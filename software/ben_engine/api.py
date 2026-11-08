"""BEN Engine dashboard API (FastAPI).

Implements the dashboard contract in spec/INTERFACES.md.

Simulation mode by default: a background asyncio task steps one :class:`ben_engine.twin.Twin`
once per real second (``POST /api/sim/speed`` runs 1–60 simulated seconds per real second) and
pushes the state to every WebSocket client on ``/ws/state``.  Every simulated step is appended to
a telemetry ring buffer that feeds ``/api/export.csv``.

Modules written by other parts of the team (cfd, calibration, analysis, sweeps, sim_nodes,
export, commissioning, bom) are imported lazily inside the endpoints.  When a module is not yet
present the endpoint answers ``503 {"detail": "<module> module not yet available"}`` so the
server and the dashboard run before they land.  Sweeps and telemetry export have a built-in
fallback implementation so the automated sweep sequence and CSV export always work.

Run:  ``PYTHONPATH=software uvicorn ben_engine.api:app --host 0.0.0.0 --port 8080``
"""
from __future__ import annotations

import asyncio
import csv
import dataclasses
import datetime as _dt
import importlib
import io
import json
import math
import threading
import time
import traceback
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import (CLIMATE_DESIGN, COOLING_LIBRARY, PROFILE_DEFAULTS, TIER_GEOMETRY, Config)
from .twin import Twin, TwinParams

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = REPO_ROOT / "dashboard" / "static"
REPORT_DIR = REPO_ROOT / "docs" / "reports"
MEDIA_DIR = REPO_ROOT / "docs" / "media"

OPTIONAL_MODULES = ("cfd", "calibration", "analysis", "sweeps", "sim_nodes", "export", "commissioning", "bom")
RING_BUFFER_ROWS = 6 * 3600  # 6 h at 1 s


# ----------------------------------------------------------------------------- helpers
def _optional(name: str):
    """Import ``ben_engine.<name>`` lazily; return the module or None."""
    try:
        return importlib.import_module(f"ben_engine.{name}")
    except ImportError:
        return None


def _require(name: str):
    mod = _optional(name)
    if mod is None:
        raise HTTPException(status_code=503, detail=f"{name} module not yet available")
    return mod


def _call_first(mod, names: List[str], *args, **kw):
    """Call the first attribute of *mod* that exists in *names*.  Used to tolerate small
    interface differences between concurrently written modules."""
    for n in names:
        fn = getattr(mod, n, None)
        if callable(fn):
            return fn(*args, **kw)
    raise HTTPException(status_code=503, detail=f"{mod.__name__} has none of {names}; interface mismatch")


def _jsonable(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return _jsonable(dataclasses.asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return _jsonable(obj.to_dict())
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        return _jsonable({k: v for k, v in vars(obj).items() if not k.startswith("_")})
    try:
        import numpy as np  # noqa
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except Exception:
        pass
    return obj


def flatten_state(state: Dict[str, Any], ts: float) -> Dict[str, Any]:
    """Flatten a Twin.state() dict into one CSV row."""
    row: Dict[str, Any] = {"ts": round(ts, 3), "ts_iso": _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).isoformat(timespec="seconds")}

    def put(prefix: str, v: Any):
        if isinstance(v, dict):
            for k, vv in v.items():
                put(f"{prefix}_{k}" if prefix else k, vv)
        elif isinstance(v, list):
            if all(not isinstance(x, (dict, list)) for x in v):
                for i, x in enumerate(v):
                    row[f"{prefix}_{i + 1}"] = x
            else:
                for i, x in enumerate(v):
                    put(f"{prefix}_{i + 1}", x)
        else:
            row[prefix] = v

    for k, v in state.items():
        if k == "alarms":
            row["alarms_active"] = len(v)
            row["alarms"] = ";".join(a["id"] for a in v)
        elif k == "faults":
            row["faults"] = ";".join(v)
        else:
            put(k, v)
    return row


def rows_to_csv(rows: List[Dict[str, Any]]) -> str:
    header: List[str] = []
    seen = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                header.append(k)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=header, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return buf.getvalue()


def _parse_time(v: Optional[str], default: float) -> float:
    if v in (None, ""):
        return default
    try:
        return float(v)
    except ValueError:
        pass
    try:
        d = _dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=_dt.timezone.utc)
        return d.timestamp()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"bad time {v!r}; use unix seconds or ISO 8601")


# ----------------------------------------------------------------------------- telemetry buffer
class TelemetryBuffer:
    """Ring buffer of flattened states keyed by wall-clock time.

    Uses ``ben_engine.export.flatten_state`` / ``columns_for`` when that module is importable so
    the dashboard CSV and the offline export tools agree on columns; otherwise a builtin flattener.
    """

    def __init__(self, maxlen: int = RING_BUFFER_ROWS):
        self.rows: deque = deque(maxlen=maxlen)
        self._ext = _optional("export")
        self.source = "ben_engine.export" if self._ext is not None and hasattr(self._ext, "flatten_state") else "builtin"

    def append(self, state: Dict[str, Any], ts: float):
        if self.source == "ben_engine.export":
            try:
                row = {"ts": round(ts, 3), "ts_iso": _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).isoformat(timespec="seconds")}
                row.update(self._ext.flatten_state(state))
                self.rows.append(row)
                return
            except Exception:
                self.source = "builtin"
        self.rows.append(flatten_state(state, ts))

    def __len__(self):
        return len(self.rows)

    def select(self, t_from: float, t_to: float) -> List[Dict[str, Any]]:
        return [r for r in self.rows if t_from <= r["ts"] <= t_to]

    def to_csv(self, rows: List[Dict[str, Any]]) -> str:
        if self.source == "ben_engine.export" and hasattr(self._ext, "columns_for"):
            try:
                cols = self._ext.columns_for(rows)
                if rows and "ts" in rows[0]:
                    cols = ["ts", "ts_iso"] + [c for c in cols if c not in ("ts", "ts_iso")]
                buf = io.StringIO()
                w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
                w.writeheader()
                for r in rows:
                    w.writerow({k: ("" if v is None else v) for k, v in r.items()})
                return buf.getvalue()
            except Exception:
                pass
        return rows_to_csv(rows)


# ----------------------------------------------------------------------------- built-in sweeps
def _ashrae_max(tw: Twin) -> float:
    return {"A1": 27.0, "A2": 35.0, "A3": 40.0, "A4": 45.0}[tw.d["ashrae_class"]]


def _builtin_sweep(name: str, cfg: Config, progress: Callable[[float], None]) -> Dict[str, Any]:
    """Short deterministic scenario sweeps against a fresh Twin.  Each returns rows (one per 10 s
    of simulated time) and pass/fail criteria."""
    spec = BUILTIN_SWEEPS[name]
    tw = Twin(cfg, seed=7)
    tw.set_it_load(0.8)
    total = spec["seconds"]
    rows: List[Dict[str, Any]] = []
    t0 = time.time()
    a_max = _ashrae_max(tw)
    events: List[str] = []
    for s in range(1, total + 1):
        spec["script"](tw, s, events)
        tw.step(1.0)
        if s % 10 == 0 or s == total:
            st = tw.state()
            rows.append({
                "t_s": s, "it_kw": st["it_kw"], "outdoor_c": st["outdoor_c"],
                "inlet_max_c": max(st["rack_inlet_c"]), "inlet_mean_c": round(sum(st["rack_inlet_c"]) / len(st["rack_inlet_c"]), 2),
                "supply_c": st["supply_c"], "return_c": st["return_c"], "aisle_dp_pa": st["aisle_dp_pa"],
                "cooling_on": sum(1 for u in st["cooling_units"] if u["on"]), "fan_pct_max": max(u["fan_pct"] for u in st["cooling_units"]),
                "utility_kw": st["power"]["utility_kw"], "ups_soc_pct": st["power"]["ups_soc_pct"], "ups_runtime_min": st["power"]["ups_runtime_min"],
                "generator_on": st["power"]["generator_on"], "pue": st["pue"],
                "alarms": ";".join(a["id"] for a in st["alarms"]),
            })
        if s % 50 == 0:
            progress(s / total)
    criteria = spec["criteria"](tw, rows, a_max, events)
    passed = all(c["pass"] for c in criteria)
    return {"rows": rows, "criteria": criteria, "passed": passed, "events": events,
            "duration_s": round(time.time() - t0, 3), "sim_seconds": total}


def _crit(name: str, value: Any, limit: str, ok: bool, unit: str = "") -> Dict[str, Any]:
    return {"name": name, "value": value, "limit": limit, "pass": bool(ok), "unit": unit}


def _sc_load_step(tw: Twin, s: int, ev: List[str]):
    if s == 1:
        tw.set_it_load(0.3)
    if s == 300:
        tw.set_it_load(1.0)
        ev.append("t=300 s: IT load step 30 % -> 100 %")


def _cr_load_step(tw, rows, a_max, ev):
    peak = max(r["inlet_max_c"] for r in rows)
    tail = [r["inlet_max_c"] for r in rows[-6:]]
    settle = max(tail) - min(tail)
    return [
        _crit("max rack inlet after load step", round(peak, 2), f"< {a_max - 2:.0f}", peak < a_max - 2, "C"),
        _crit("inlet settles (last 60 s span)", round(settle, 2), "< 0.6", settle < 0.6, "K"),
        _crit("PUE at full load", rows[-1]["pue"], "< 1.6", (rows[-1]["pue"] or 9) < 1.6),
    ]


def _sc_cool_fail(tw: Twin, s: int, ev: List[str]):
    if s == 240:
        tw.inject("cooling_unit_fail", unit=0)
        ev.append("t=240 s: cooling unit 1 failed")


def _cr_cool_fail(tw, rows, a_max, ev):
    peak = max(r["inlet_max_c"] for r in rows)
    on_after = [r["cooling_on"] for r in rows if r["t_s"] >= 260]
    need = tw.d["cooling_units_n"]
    standby = (min(on_after) >= need) if tw.cfg.redundancy != "N" else True
    return [
        _crit("max rack inlet during unit failure", round(peak, 2), f"<= {a_max:.0f}", peak <= a_max, "C"),
        _crit("standby unit started (units on >= N)", min(on_after) if on_after else 0, f">= {need}" if tw.cfg.redundancy != "N" else "n/a (N)", standby),
        _crit("cooling-failed alarm raised", any("cool1_fail" in r["alarms"] for r in rows), "true", any("cool1_fail" in r["alarms"] for r in rows)),
    ]


def _sc_utility(tw: Twin, s: int, ev: List[str]):
    if s == 60:
        tw.inject("utility_loss")
        ev.append("t=60 s: utility lost")
    if s == 420:
        tw.clear("utility_loss")
        ev.append("t=420 s: utility restored")


def _cr_utility(tw, rows, a_max, ev):
    on_batt = [r for r in rows if 60 <= r["t_s"] < 420]
    soc_min = min(r["ups_soc_pct"] for r in on_batt) if on_batt else 100
    rt0 = on_batt[0]["ups_runtime_min"] if on_batt else 0
    gen = any(r["generator_on"] for r in on_batt) if tw.cfg.generator else True
    peak = max(r["inlet_max_c"] for r in rows)
    out = [
        _crit("UPS SoC after 6 min on battery", round(soc_min, 1), "> 20", soc_min > 20, "%"),
        _crit("UPS runtime estimate at loss", rt0, f">= {tw.cfg.ups_minutes * 0.8:.0f}", rt0 >= tw.cfg.ups_minutes * 0.8, "min"),
        _crit("utility_loss alarm raised", any("utility_loss" in r["alarms"] for r in on_batt), "true", any("utility_loss" in r["alarms"] for r in on_batt)),
    ]
    if tw.cfg.generator:
        out.append(_crit("generator started", gen, "true", gen))
    out.append(_crit("max inlet during outage (cooling may be off)", round(peak, 2), "< 45 (A4)", peak < 45, "C"))
    return out


def _sc_outdoor(tw: Twin, s: int, ev: List[str]):
    clim = CLIMATE_DESIGN[tw.cfg.climate]
    start = clim["t_design_c"] - 12
    tw.set_outdoor(start + (clim["t_design_c"] - start) * min(1.0, s / 900.0))
    if s == 900:
        ev.append(f"t=900 s: outdoor reached design {clim['t_design_c']} C")


def _cr_outdoor(tw, rows, a_max, ev):
    peak = max(r["inlet_max_c"] for r in rows)
    fan = max(r["fan_pct_max"] for r in rows)
    return [
        _crit("max rack inlet at design outdoor", round(peak, 2), f"< {a_max - 2:.0f}", peak < a_max - 2, "C"),
        _crit("fan headroom", fan, "<= 100", fan <= 100, "%"),
    ]


def _sc_door(tw: Twin, s: int, ev: List[str]):
    if s == 120:
        tw.inject("door_open")
        ev.append("t=120 s: door opened")
    if s == 720:
        tw.clear("door_open")
        ev.append("t=720 s: door closed")


def _cr_door(tw, rows, a_max, ev):
    before = [r["inlet_max_c"] for r in rows if r["t_s"] <= 120]
    during = [r["inlet_max_c"] for r in rows if 120 < r["t_s"] <= 720]
    rise = (max(during) - before[-1]) if during and before else 0
    return [
        _crit("door_open alarm raised", any("door_open" in r["alarms"] for r in rows), "true", any("door_open" in r["alarms"] for r in rows)),
        _crit("inlet rise with door open", round(rise, 2), "< 3", rise < 3, "K"),
        _crit("max inlet with door open", round(max(during), 2) if during else None, f"< {a_max:.0f}", (max(during) if during else 0) < a_max, "C"),
    ]


BUILTIN_SWEEPS: Dict[str, Dict[str, Any]] = {
    "load_step": {"label": "IT load step 30 → 100 %", "seconds": 1200, "script": _sc_load_step, "criteria": _cr_load_step,
                  "description": "Steps IT load and checks rack inlets settle inside the ASHRAE class with margin."},
    "cooling_unit_fail": {"label": "Cooling unit failure", "seconds": 1200, "script": _sc_cool_fail, "criteria": _cr_cool_fail,
                          "description": "Fails cooling unit 1; redundancy must start a standby unit and inlets stay below the class maximum."},
    "utility_loss": {"label": "Utility loss / UPS ride-through", "seconds": 600, "script": _sc_utility, "criteria": _cr_utility,
                     "description": "Drops utility for 6 min; UPS must hold the IT load and generator must start if fitted."},
    "outdoor_ramp": {"label": "Outdoor ramp to design day", "seconds": 1200, "script": _sc_outdoor, "criteria": _cr_outdoor,
                     "description": "Ramps outdoor temperature to the climate design value; cooling must keep inlets in class."},
    "door_open": {"label": "Door open 10 min", "seconds": 900, "script": _sc_door, "criteria": _cr_door,
                  "description": "Opens the container door; alarm must raise and inlets must not rise more than 3 K."},
}


# ----------------------------------------------------------------------------- runtime
class Runtime:
    """Everything mutable the API serves: twin, buffer, jobs, WS clients."""

    def __init__(self):
        self.cfg: Config = Config.preset("ben20")
        self.twin: Twin = Twin(self.cfg, seed=1)
        self.twin.set_it_load(0.75)
        self.buffer = TelemetryBuffer()
        self.speed: int = 1
        self.mode: str = "sim"
        self.gateway_url: str = ""
        self.started_wall = time.time()
        self.last_step_wall: float = 0.0
        self.task: Optional[asyncio.Task] = None
        self.clients: List[WebSocket] = []
        self.sweeps: Dict[str, Dict[str, Any]] = {}
        self.sweep_order: List[str] = []
        self.cfd_jobs: Dict[str, Dict[str, Any]] = {}
        self.commission_job: Optional[Dict[str, Any]] = None
        self.io_fleet = None
        self.io_log: deque = deque(maxlen=200)
        self.calibrations: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self._step_now()

    # -- twin
    def rebuild(self, cfg: Config):
        with self.lock:
            old_load = self.twin.it_fraction
            old_outdoor = self.twin.outdoor_c if cfg.climate == self.cfg.climate else None
            self.cfg = cfg
            self.twin = Twin(cfg, seed=1, outdoor_c=old_outdoor)
            self.twin.set_it_load(old_load)
            self.io_fleet = None
            self._step_now()

    def _step_now(self):
        self.twin.step(1.0)
        self.last_step_wall = time.time()
        self.buffer.append(self.twin.state(), self.last_step_wall)

    def tick(self):
        with self.lock:
            for _ in range(self.speed):
                self._step_now()

    def snapshot(self) -> Dict[str, Any]:
        st = self.twin.state()
        st["wall_ts"] = self.last_step_wall
        st["sim_speed"] = self.speed
        st["mode"] = self.mode
        return st

    def config_payload(self) -> Dict[str, Any]:
        return {"config": self.cfg.to_dict(), "derived": _jsonable(self.cfg.derived()), "errors": [],
                "sensors": self.sensors_payload()}

    def sensors_payload(self) -> List[Dict[str, Any]]:
        return [{"id": s.id, "kind": s.kind, "location_m": list(s.location_m), "unit": s.unit, "u95": s.u95, "node": s.node}
                for s in self.twin.sensors()]

    def modules(self) -> Dict[str, bool]:
        return {m: _optional(m) is not None for m in OPTIONAL_MODULES}

    # -- sweeps
    def sweep_catalog(self) -> Dict[str, Any]:
        """Sweeps from ben_engine.sweeps.SWEEPS when importable, else the builtin set."""
        mod = _optional("sweeps")
        if mod is not None and isinstance(getattr(mod, "SWEEPS", None), dict):
            items = []
            for name, fn in mod.SWEEPS.items():
                doc = (fn.__doc__ or "").strip().splitlines()
                items.append({"name": name, "label": name.replace("_", " "), "description": doc[0] if doc else ""})
            return {"source": "ben_engine.sweeps", "sweeps": items, "all": [i["name"] for i in items]}
        items = [{"name": k, "label": v["label"], "description": v["description"]} for k, v in BUILTIN_SWEEPS.items()]
        return {"source": "builtin", "sweeps": items, "all": [i["name"] for i in items]}

    def _run_one_sweep(self, name: str, cfg: Config, progress: Callable[[float], None]) -> Dict[str, Any]:
        mod = _optional("sweeps")
        if mod is not None and isinstance(getattr(mod, "SWEEPS", None), dict) and name in mod.SWEEPS:
            t0 = time.time()
            res = mod.run_sweep(name, cfg, seed=7)
            r = res.to_dict() if hasattr(res, "to_dict") else _jsonable(res)
            criteria = [{"name": c.get("name"), "value": c.get("value"), "limit": c.get("limit"), "pass": bool(c.get("passed", c.get("pass", False))),
                         "unit": "", "note": c.get("note", "")} for c in r.get("criteria", [])]
            progress(1.0)
            return {"rows": _jsonable(r.get("rows", [])), "criteria": criteria, "passed": bool(r.get("passed", all(c["pass"] for c in criteria))),
                    "events": [r["summary"]] if r.get("summary") else [], "summary": r.get("summary", ""), "started": r.get("started"),
                    "extra": _jsonable(r.get("extra", {})), "duration_s": round(time.time() - t0, 3), "source": "ben_engine.sweeps"}
        if name not in BUILTIN_SWEEPS:
            raise KeyError(name)
        res = _builtin_sweep(name, cfg, progress)
        res["source"] = "builtin"
        return res

    def start_sweep(self, name: str) -> Dict[str, Any]:
        cat = self.sweep_catalog()
        names = cat["all"] if name == "all" else [name]
        for n in names:
            if n not in cat["all"]:
                raise HTTPException(status_code=404, detail=f"unknown sweep {n}; available: {cat['all']} or 'all'")
        sid = uuid.uuid4().hex[:10]
        job = {"id": sid, "name": name, "sweeps": names, "status": "queued", "progress": 0.0,
               "started": time.time(), "finished": None, "config": self.cfg.to_dict(), "results": [], "error": None,
               "passed": None}
        self.sweeps[sid] = job
        self.sweep_order.append(sid)
        cfg = Config.from_dict(self.cfg.to_dict())

        def work():
            job["status"] = "running"
            try:
                for i, n in enumerate(names):
                    def prog(p, i=i):
                        job["progress"] = round((i + p) / len(names), 3)
                    res = self._run_one_sweep(n, cfg, prog)
                    res["name"] = n
                    job["results"].append(res)
                    job["progress"] = round((i + 1) / len(names), 3)
                job["passed"] = all(r["passed"] for r in job["results"])
                job["status"] = "done"
            except Exception as e:
                job["status"] = "failed"
                job["error"] = f"{type(e).__name__}: {e}"
                job["trace"] = traceback.format_exc()
            job["finished"] = time.time()

        threading.Thread(target=work, name=f"sweep-{sid}", daemon=True).start()
        return self.sweep_summary(job)

    @staticmethod
    def sweep_summary(job: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in job.items() if k != "results"} | {
            "results": [{"name": r["name"], "passed": r["passed"], "criteria": r["criteria"], "events": r.get("events", []),
                         "rows_n": len(r["rows"]), "source": r.get("source")} for r in job["results"]]}

    def sweep_csv(self, job: Dict[str, Any]) -> str:
        if len(job["results"]) == 1 and job["results"][0].get("csv"):
            return job["results"][0]["csv"]
        rows: List[Dict[str, Any]] = []
        for r in job["results"]:
            for row in r["rows"]:
                rows.append({"sweep": r["name"], **row})
        crit_rows = [{"sweep": r["name"], "criterion": c.get("name"), "value": c.get("value"), "limit": c.get("limit"), "pass": c.get("pass")}
                     for r in job["results"] for c in r["criteria"]]
        out = rows_to_csv(rows)
        if crit_rows:
            out += "\n# criteria\n" + rows_to_csv(crit_rows)
        return out

    # -- websocket
    async def broadcast(self, msg: Dict[str, Any]):
        if not self.clients:
            return
        data = json.dumps(_jsonable(msg))
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.clients:
                self.clients.remove(ws)


RT = Runtime()


async def _sim_loop():
    """Step the twin `speed` times per real second and push state at 1 Hz."""
    while True:
        t0 = time.monotonic()
        try:
            RT.tick()
            await RT.broadcast({"type": "state", "state": RT.snapshot()})
        except Exception:  # keep the loop alive
            traceback.print_exc()
        await asyncio.sleep(max(0.05, 1.0 - (time.monotonic() - t0)))


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    RT.task = asyncio.create_task(_sim_loop())
    try:
        yield
    finally:
        if RT.task:
            RT.task.cancel()
            try:
                await RT.task
            except (asyncio.CancelledError, Exception):
                pass


app = FastAPI(title="BEN Engine API", version="0.1.0", lifespan=lifespan,
              description="Schreiber AI BEN Engine digital-twin dashboard API (simulation mode).")


# ----------------------------------------------------------------------------- health / sim
@app.get("/api/health")
async def health():
    age = time.time() - RT.last_step_wall if RT.last_step_wall else None
    running = RT.task is not None and not RT.task.done()
    ok = running and age is not None and age < 5.0
    return {"ok": ok, "mode": RT.mode, "twin_running": running, "last_step_age_s": round(age, 3) if age is not None else None,
            "sim_speed": RT.speed, "sim_t": RT.twin.t, "uptime_s": round(time.time() - RT.started_wall, 1),
            "ws_clients": len(RT.clients), "buffer_rows": len(RT.buffer), "buffer_source": RT.buffer.source,
            "modules": RT.modules(), "tier": RT.cfg.tier, "version": app.version}


@app.get("/api/sim")
async def sim_get():
    return {"speed": RT.speed, "mode": RT.mode, "gateway_url": RT.gateway_url, "t": RT.twin.t, "outdoor_c": RT.twin.outdoor_c,
            "it_fraction": RT.twin.it_fraction}


@app.post("/api/sim/speed")
async def sim_speed(body: Dict[str, Any]):
    try:
        x = int(round(float(body.get("x", body.get("speed", 1)))))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="x must be a number 1..60")
    if not 1 <= x <= 60:
        raise HTTPException(status_code=400, detail="x must be between 1 and 60")
    RT.speed = x
    return {"speed": RT.speed}


@app.post("/api/sim/mode")
async def sim_mode(body: Dict[str, Any]):
    mode = body.get("mode", "sim")
    if mode not in ("sim", "live"):
        raise HTTPException(status_code=400, detail="mode must be 'sim' or 'live'")
    RT.mode = mode
    RT.gateway_url = str(body.get("gateway_url", RT.gateway_url) or "")
    note = None
    if mode == "live":
        note = "Live mode records the gateway URL only; this build has no gateway adapter connected, so the twin keeps simulating."
    return {"mode": RT.mode, "gateway_url": RT.gateway_url, "note": note}


@app.post("/api/sim/reset")
async def sim_reset():
    RT.rebuild(Config.from_dict(RT.cfg.to_dict()))
    return {"ok": True, "t": RT.twin.t}


@app.post("/api/outdoor")
async def set_outdoor(body: Dict[str, Any]):
    try:
        c = float(body["c"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="body {c: <deg C>}")
    if not -50 <= c <= 60:
        raise HTTPException(status_code=400, detail="outdoor_c must be within -50..60")
    RT.twin.set_outdoor(c)
    return {"outdoor_c": c}


# ----------------------------------------------------------------------------- config
@app.get("/api/config")
async def get_config():
    return RT.config_payload()


@app.post("/api/config")
async def post_config(body: Dict[str, Any]):
    merged = RT.cfg.to_dict()
    merged.update({k: v for k, v in (body or {}).items() if k in Config.__dataclass_fields__})
    try:
        if "it_kw" in merged:
            merged["it_kw"] = float(merged["it_kw"])
        if "racks" in merged:
            merged["racks"] = int(merged["racks"])
        if "ups_minutes" in merged:
            merged["ups_minutes"] = int(merged["ups_minutes"])
        cfg = Config.from_dict(merged)
    except (TypeError, ValueError) as e:
        return JSONResponse(status_code=400, content={"errors": [f"bad value: {e}"], "config": merged})
    errs = cfg.validate()
    if errs:
        return JSONResponse(status_code=400, content={"errors": errs, "config": cfg.to_dict()})
    RT.rebuild(cfg)
    payload = RT.config_payload()
    await RT.broadcast({"type": "config", **payload})
    return payload


@app.post("/api/config/validate")
async def validate_config(body: Dict[str, Any]):
    merged = RT.cfg.to_dict()
    merged.update({k: v for k, v in (body or {}).items() if k in Config.__dataclass_fields__})
    try:
        cfg = Config.from_dict(merged)
        errs = cfg.validate()
    except (TypeError, ValueError) as e:
        return {"errors": [str(e)], "derived": None}
    return {"errors": errs, "derived": _jsonable(cfg.derived()) if not errs else None, "config": cfg.to_dict()}


@app.get("/api/presets")
async def presets():
    out = {}
    for t in TIER_GEOMETRY:
        cfg = Config.preset(t)
        out[t] = {"config": cfg.to_dict(), "derived": {k: v for k, v in _jsonable(cfg.derived()).items() if k not in ("geometry", "climate")}}
    return out


@app.get("/api/catalog")
async def catalog():
    return {"tiers": TIER_GEOMETRY, "profiles": PROFILE_DEFAULTS, "cooling": COOLING_LIBRARY, "climates": CLIMATE_DESIGN,
            "redundancy": ["N", "N+1", "2N"], "subsystems": ["power", "cooling", "compute", "controls"], "faults": list(Twin.FAULTS)}


@app.get("/api/sensors")
async def sensors():
    return RT.sensors_payload()


# ----------------------------------------------------------------------------- state
@app.get("/api/state")
async def state():
    return _jsonable(RT.snapshot())


@app.websocket("/ws/state")
async def ws_state(ws: WebSocket):
    await ws.accept()
    RT.clients.append(ws)
    try:
        await ws.send_text(json.dumps(_jsonable({"type": "config", **RT.config_payload()})))
        await ws.send_text(json.dumps(_jsonable({"type": "state", "state": RT.snapshot()})))
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text(json.dumps({"type": "pong", "ts": time.time()}))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if ws in RT.clients:
            RT.clients.remove(ws)


# ----------------------------------------------------------------------------- faults / load
@app.post("/api/fault")
async def inject_fault(body: Dict[str, Any]):
    name = body.get("name")
    params = body.get("params") or {}
    if name not in Twin.FAULTS:
        raise HTTPException(status_code=400, detail=f"unknown fault {name}; valid: {list(Twin.FAULTS)}")
    try:
        RT.twin.inject(name, **params)
    except (TypeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    RT.twin._update_alarms()
    return {"faults": sorted(RT.twin.faults.keys()), "alarms": _jsonable(RT.twin.state()["alarms"])}


@app.delete("/api/fault/{name}")
async def clear_fault(name: str, request: Request):
    if name not in Twin.FAULTS:
        raise HTTPException(status_code=400, detail=f"unknown fault {name}")
    params = {k: v for k, v in request.query_params.items()}
    if not params and name == "cooling_unit_fail":
        params = dict(RT.twin.faults.get(name, {}))
    RT.twin.clear(name, **params)
    RT.twin._update_alarms()
    return {"faults": sorted(RT.twin.faults.keys())}


@app.delete("/api/faults")
async def clear_all_faults():
    for name, params in list(RT.twin.faults.items()):
        RT.twin.clear(name, **params)
    RT.twin._update_alarms()
    return {"faults": []}


@app.post("/api/load")
async def set_load(body: Dict[str, Any]):
    try:
        f = float(body["fraction"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="body {fraction: 0..1.2}")
    if not 0.0 <= f <= 1.2:
        raise HTTPException(status_code=400, detail="fraction must be 0..1.2")
    RT.twin.set_it_load(f)
    return {"fraction": RT.twin.it_fraction}


# ----------------------------------------------------------------------------- sweeps
@app.get("/api/sweeps/catalog")
async def sweeps_catalog():
    return RT.sweep_catalog()


@app.post("/api/sweep")
async def sweep_start(body: Dict[str, Any]):
    name = (body or {}).get("name")
    if not name:
        raise HTTPException(status_code=400, detail="body {name: <sweep> | 'all'}")
    return RT.start_sweep(name)


@app.get("/api/sweeps")
async def sweeps_list():
    return [RT.sweep_summary(RT.sweeps[s]) for s in RT.sweep_order]


@app.get("/api/sweeps/{sid}.csv")
async def sweep_csv(sid: str):
    job = RT.sweeps.get(sid)
    if job is None:
        raise HTTPException(status_code=404, detail="unknown sweep id")
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail=f"sweep is {job['status']}")
    text = RT.sweep_csv(job)
    fname = f"ben_sweep_{job['name']}_{sid}.csv"
    return Response(text, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@app.get("/api/sweeps/{sid}")
async def sweep_get(sid: str):
    job = RT.sweeps.get(sid)
    if job is None:
        raise HTTPException(status_code=404, detail="unknown sweep id")
    return _jsonable(job)


# ----------------------------------------------------------------------------- export
def _export_rows(t_from: Optional[str], t_to: Optional[str], last: Optional[float]) -> List[Dict[str, Any]]:
    now = time.time()
    if last:
        f, t = now - float(last), now + 1
    else:
        f = _parse_time(t_from, 0.0)
        t = _parse_time(t_to, now + 1)
    return RT.buffer.select(f, t)


@app.get("/api/export.csv")
async def export_csv(request: Request, last: Optional[float] = None):
    rows = _export_rows(request.query_params.get("from"), request.query_params.get("to"), last)
    text = RT.buffer.to_csv(rows)
    fname = f"ben_{RT.cfg.tier}_telemetry_{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
    return Response(text, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{fname}"',
                                                          "X-Row-Count": str(len(rows))})


@app.get("/api/export.json")
async def export_json(request: Request, last: Optional[float] = None):
    rows = _export_rows(request.query_params.get("from"), request.query_params.get("to"), last)
    fname = f"ben_{RT.cfg.tier}_telemetry_{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    return Response(json.dumps({"config": RT.cfg.to_dict(), "rows": rows}), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"', "X-Row-Count": str(len(rows))})


@app.get("/api/export/range")
async def export_range():
    rows = RT.buffer.rows
    return {"rows": len(rows), "from": rows[0]["ts"] if rows else None, "to": rows[-1]["ts"] if rows else None}


# ----------------------------------------------------------------------------- I/O test (sim_nodes)
CHANNEL_UNITS = {"T_": "C", "RH": "%RH", "dP": "Pa", "ai": "mA", "leak": "bool", "door": "bool", "pulse": "Wh", "relay": "out"}


def _chan_unit(name: str) -> str:
    for k, u in CHANNEL_UNITS.items():
        if name.startswith(k):
            return u
    return ""


def _io_fleet():
    """One ben_engine.sim_nodes.NodeFleet per twin build (virtual BEN nodes on an in-process bus)."""
    mod = _require("sim_nodes")
    if RT.io_fleet is None:
        fleet_cls = getattr(mod, "NodeFleet", None)
        if fleet_cls is None:
            raise HTTPException(status_code=503, detail="sim_nodes present but exposes no NodeFleet; interface mismatch")

        def on_output(node_id, out, val):
            RT.io_log.appendleft({"ts": time.time(), "node": node_id, "channel": out, "value": val, "op": "output_changed",
                                  "ack": {"ok": True, "result": {"function": mod.RELAY_FUNCTIONS.get(out, out)}}, "latency_ms": 0.0})
        RT.io_fleet = fleet_cls(RT.cfg, unit=f"ben-{RT.cfg.tier}", seed=1, on_output=on_output)
    return RT.io_fleet


@app.get("/api/io/status")
async def io_status():
    fleet = _io_fleet()
    st = RT.twin.state()
    nodes = []
    try:
        for node in fleet.nodes:
            tel = node.poll(st)
            status = node.status()
            channels = [{"id": k, "value": v, "raw": tel["raw"].get(k), "unit": _chan_unit(k), "cal": node.cal.get(k)}
                        for k, v in tel["ch"].items() if not k.startswith("relay")]
            outputs = [{"id": r, "value": node.outputs[r], "function": mod_fn(r)} for r in node.outputs]
            nodes.append({"id": node.node_id, "kind": node.kind, "racks": list(status.get("racks", [])), "ip": status.get("ip"),
                          "status": status, "cal_id": tel.get("cal_id"), "seq": tel.get("seq"), "ts": tel.get("ts"),
                          "topic": node.topic("telemetry"), "channels": channels, "outputs": outputs, "online": True,
                          "identify": node.identify_until_s > node.uptime_s})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"sim_nodes status failed: {type(e).__name__}: {e}")
    return {"source": "ben_engine.sim_nodes", "unit": fleet.unit, "nodes": nodes, "log": list(RT.io_log)}


def mod_fn(relay: str) -> str:
    mod = _optional("sim_nodes")
    return getattr(mod, "RELAY_FUNCTIONS", {}).get(relay, relay) if mod else relay


@app.post("/api/io/test")
async def io_test(body: Dict[str, Any]):
    """Send a PROTOCOL.md cmd to a virtual node: {node, channel, value} sets a relay;
    {node, op: identify|get_cal|tare|reboot|set_cal, channel?, gain?, offset?} sends that op."""
    fleet = _io_fleet()
    node_id = body.get("node")
    channel = body.get("channel")
    value = body.get("value")
    op = body.get("op")
    node = fleet.by_id.get(node_id) if node_id else None
    if node is None:
        raise HTTPException(status_code=404, detail=f"unknown node {node_id}; nodes: {list(fleet.by_id)}")
    cmd: Dict[str, Any] = {"id": uuid.uuid4().hex[:8]}
    if op:
        cmd["op"] = op
        if channel:
            cmd["ch"] = channel
        for k in ("gain", "offset", "cal_id", "value", "out"):
            if k in body and body[k] is not None:
                cmd[k] = body[k]
    else:
        if not channel:
            raise HTTPException(status_code=400, detail="body {node, channel, value} or {node, op}")
        cmd.update({"op": "set_output", "out": channel, "value": value})
    t0 = time.perf_counter()
    # make sure the node has a reading (tare needs one)
    node.poll(RT.twin.state())
    ack = node.command(cmd)
    latency_ms = round((time.perf_counter() - t0) * 1000, 3)
    entry = {"ts": time.time(), "node": node_id, "channel": channel or cmd.get("out"), "value": value, "op": cmd["op"], "cmd": cmd,
             "ack": ack, "latency_ms": latency_ms, "topic": node.topic("cmd")}
    RT.io_log.appendleft(entry)
    return entry


# ----------------------------------------------------------------------------- calibration
CAL_CHANNEL_TYPE = {"temperature": "DS18B20", "humidity": "SHT45_RH", "pressure": "SDP810", "power": "POWER_CLASS05", "current": "ADS1115_4_20MA"}


@app.post("/api/calibrate")
async def calibrate(body: Dict[str, Any]):
    """Least-squares gain/offset for a channel from reference/reading pairs plus a GUM budget."""
    mod = _require("calibration")
    channel = body.get("channel")
    pts = body.get("reference_points") or body.get("points") or []
    if not channel or len(pts) < 2:
        raise HTTPException(status_code=400, detail="body {channel, reference_points: [{reference, reading}, ...] (>= 2)}")
    try:
        ref = [float(p["reference"] if isinstance(p, dict) else p[0]) for p in pts]
        rd = [float(p["reading"] if isinstance(p, dict) else p[1]) for p in pts]
        fit = mod.linear_fit(ref, rd)
    except (KeyError, TypeError, ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"calibration failed: {e}")
    spec = next((s for s in RT.twin.sensors() if s.id == channel), None)
    kind = spec.kind if spec else ("temperature" if channel.startswith("T_") else "temperature")
    ch_type = body.get("channel_type") or CAL_CHANNEL_TYPE.get(kind, "DS18B20")
    out: Dict[str, Any] = {"channel": channel, "channel_type": ch_type, **fit.to_dict(), "residual_rms": fit.residual_std,
                           "reference": fit.reference, "reading": fit.reading, "residuals": fit.residuals,
                           "cal_id": f"c-{_dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:4]}"}
    try:
        budget = mod.default_budget(ch_type, reading=fit.x_mean, cal=fit)
        bd = budget.to_dict()
        out["u95"] = bd["U95"]
        out["budget"] = [{"source": src["name"], "type": src["type"], "distribution": src["distribution"], "value": src["value"], "u": src["u"], "note": src.get("note", "")} for src in bd["sources"]]
        out["budget_summary"] = {k: bd[k] for k in ("u_c", "nu_eff", "k", "U95", "dominant", "unit")}
    except Exception as e:  # budget is informative; the fit still stands
        out["u95"] = fit.u95_at(fit.x_mean)
        out["budget"] = []
        out["budget_error"] = f"{type(e).__name__}: {e}"
    out = _jsonable(out)
    RT.calibrations[channel] = out
    return out


@app.get("/api/calibrations")
async def calibrations():
    return RT.calibrations


@app.post("/api/calibrate/apply")
async def calibrate_apply(body: Dict[str, Any]):
    """Apply a calibration's offset to the twin's reported channel (sensor_drift correction)."""
    channel = body.get("channel")
    cal = RT.calibrations.get(channel)
    if cal is None:
        raise HTTPException(status_code=404, detail="no calibration for that channel; POST /api/calibrate first")
    offset = cal.get("offset", 0.0)
    gain = cal.get("gain", 1.0)
    applied = False
    if isinstance(channel, str) and channel.startswith("T_in"):
        try:
            # the node now reports gain*raw + offset; the twin's reported drift moves by the correction at ~22 C
            RT.twin.drift_c = round(RT.twin.drift_c + float(offset) + (float(gain) - 1.0) * 22.0, 3)
            applied = True
        except (TypeError, ValueError):
            pass
    return {"channel": channel, "gain": gain, "offset": offset, "applied_to_twin": applied, "twin_drift_c": RT.twin.drift_c}


# ----------------------------------------------------------------------------- CFD
def _cfd_run(tier: str, job: Dict[str, Any]):
    mod = _optional("cfd")
    try:
        if mod is None:
            raise RuntimeError("cfd module not yet available")
        cfg = Config.from_dict(RT.cfg.to_dict()) if tier == RT.cfg.tier else Config.preset(tier)
        MEDIA_DIR.joinpath("cfd").mkdir(parents=True, exist_ok=True)
        png = MEDIA_DIR / "cfd" / f"cfd_{tier}.png"
        met = mod.run_cfd(cfg, out_png=str(png))
        job["png"] = str(png) if png.exists() else None
        job["metrics_full"] = met
        job["metrics"] = _jsonable({k: v for k, v in met.items() if k not in ("fields", "solver", "png")})
        job["metrics"]["recirculation"] = float(sum(met["recirculation_index"]) / max(1, len(met["recirculation_index"])))
        job["status"] = "done"
    except Exception as e:
        job["status"] = "failed"
        job["error"] = f"{type(e).__name__}: {e}"
        job["trace"] = traceback.format_exc()
    job["finished"] = time.time()


@app.post("/api/cfd/run")
async def cfd_run(tier: Optional[str] = None):
    _require("cfd")
    tier = tier or RT.cfg.tier
    if tier not in TIER_GEOMETRY:
        raise HTTPException(status_code=400, detail="unknown tier")
    job = {"tier": tier, "status": "running", "started": time.time(), "finished": None, "png": None, "metrics": None, "error": None}
    RT.cfd_jobs[tier] = job
    threading.Thread(target=_cfd_run, args=(tier, job), daemon=True).start()
    return job


@app.get("/api/cfd/metrics")
async def cfd_metrics(tier: Optional[str] = None):
    _require("cfd")
    tier = tier or RT.cfg.tier
    job = RT.cfd_jobs.get(tier)
    if job is None:
        return {"tier": tier, "status": "idle", "metrics": None}
    return _jsonable({k: v for k, v in job.items() if k != "metrics_full"})


@app.get("/api/cfd")
async def cfd_png(tier: Optional[str] = None):
    _require("cfd")
    tier = tier or RT.cfg.tier
    job = RT.cfd_jobs.get(tier)
    if job is None or job["status"] != "done" or not job.get("png"):
        raise HTTPException(status_code=404, detail="no CFD result for that tier yet; POST /api/cfd/run")
    return FileResponse(job["png"], media_type="image/png")


@app.post("/api/cfd/apply")
async def cfd_apply(tier: Optional[str] = None):
    """Copy the CFD per-rack recirculation profile into the running twin's parameters."""
    tier = tier or RT.cfg.tier
    job = RT.cfd_jobs.get(tier)
    if job is None or job["status"] != "done":
        raise HTTPException(status_code=409, detail="run CFD first")
    met = job.get("metrics_full") or job.get("metrics") or {}
    mod = _optional("cfd")
    prof = list(met.get("recirculation_index") or [])
    if not prof:
        raise HTTPException(status_code=422, detail="CFD metrics carry no recirculation_index to apply")
    if mod is not None and hasattr(mod, "apply_to_params"):
        mod.apply_to_params(met, RT.twin.p)
    else:
        RT.twin.p.recirculation = float(sum(prof) / len(prof))
    if len(prof) != RT.cfg.racks:
        RT.twin.p.recirculation_profile = None  # profile is for a different rack count; mean still applies
    return {"applied": True, "recirculation": RT.twin.p.recirculation, "profile": getattr(RT.twin.p, "recirculation_profile", None), "tier": tier}


# ----------------------------------------------------------------------------- commissioning
def _step_view(sr) -> Dict[str, Any]:
    """Compact view of a commissioning StepResult for the dashboard table."""
    vals = getattr(sr, "values", {}) or {}
    nums = []
    for k, v in vals.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            nums.append(f"{k}={round(v, 2)}")
        elif isinstance(v, str) and len(v) < 24:
            nums.append(f"{k}={v}")
        if len(nums) >= 3:
            break
    return {"id": sr.num, "name": sr.name, "pass": bool(sr.passed), "measured": "; ".join(nums), "criterion": "; ".join(sr.notes or []),
            "values": _jsonable(vals), "notes": list(sr.notes or []), "started_t": sr.started_t, "ended_t": sr.ended_t}


@app.post("/api/commission/run")
async def commission_run():
    """Run ben_engine.commissioning.Commissioning (10 steps) against a fresh twin in a thread."""
    mod = _require("commissioning")
    if RT.commission_job and RT.commission_job["status"] == "running":
        return {k: v for k, v in RT.commission_job.items() if k != "_cx"}
    job: Dict[str, Any] = {"id": uuid.uuid4().hex[:8], "status": "running", "started": time.time(), "finished": None,
                           "steps": [], "log": [], "report_path": None, "report_url": None, "csv_path": None, "error": None, "passed": None,
                           "config": RT.cfg.to_dict()}
    RT.commission_job = job
    cfg = Config.from_dict(RT.cfg.to_dict())

    def log(msg: str):
        job["log"].append(str(msg))
        if len(job["log"]) > 400:
            del job["log"][:100]
        # mirror completed steps as they finish (the report's step list grows step by step)
        cx = job.get("_cx")
        if cx is not None:
            job["steps"] = [_step_view(sr) for sr in cx.report.steps]

    def work():
        try:
            REPORT_DIR.mkdir(parents=True, exist_ok=True)
            stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            out = REPORT_DIR / f"commissioning_{cfg.tier}_{stamp}.md"
            cx = mod.Commissioning(cfg, sim=True, yes=True, seed=1, operator="dashboard (sim)", log=log, fast=True)
            job["_cx"] = cx
            rep = cx.run(str(out))
            job["steps"] = [_step_view(sr) for sr in rep.steps]
            job["passed"] = bool(rep.passed)
            job["report_path"] = str(out)
            job["report_url"] = "/api/commission/report"
            job["csv_path"] = rep.csv_path
            job["csv_sha256"] = rep.csv_sha256
            job["status"] = "done"
        except Exception as e:
            job["status"] = "failed"
            job["error"] = f"{type(e).__name__}: {e}"
            job["trace"] = traceback.format_exc()
        job["finished"] = time.time()
        job.pop("_cx", None)

    threading.Thread(target=work, daemon=True).start()
    return {k: v for k, v in job.items() if k != "_cx"}


@app.get("/api/commission/status")
async def commission_status():
    if RT.commission_job is None:
        return {"status": "idle", "steps": [], "module": _optional("commissioning") is not None}
    return {k: v for k, v in RT.commission_job.items() if k != "_cx"}


@app.get("/api/commission/report")
async def commission_report():
    job = RT.commission_job
    if not job or not job.get("report_path"):
        raise HTTPException(status_code=404, detail="no report yet")
    p = Path(job["report_path"])
    media = "text/markdown" if p.suffix == ".md" else ("application/json" if p.suffix == ".json" else "application/octet-stream")
    if p.suffix == ".html":
        media = "text/html"
    return FileResponse(str(p), media_type=media, filename=p.name)


# ----------------------------------------------------------------------------- BOM
@app.get("/api/bom")
async def bom():
    mod = _require("bom")
    try:
        rows = mod.generate_bom(RT.cfg)
        tot = mod.totals(rows) if hasattr(mod, "totals") else None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"bom failed: {type(e).__name__}: {e}")
    return _jsonable({"config": RT.cfg.to_dict(), "lines": rows, "totals": tot, "n": len(rows)})


# ----------------------------------------------------------------------------- static dashboard
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="dashboard")
else:  # pragma: no cover
    @app.get("/")
    async def _no_dashboard():
        return PlainTextResponse("dashboard/static not found", status_code=404)
