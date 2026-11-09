"""BEN Engine site commissioning script.

Run by a Schreiber AI field technician or by the customer. In ``--sim`` mode it runs against
the digital twin and the virtual nodes, end to end, and produces the same signed report that a
live run would. In ``--live`` mode it connects to the unit's gateway API (see
spec/INTERFACES.md); the live adapter is a placeholder that checks the gateway answers and then
stops, because the live I/O and load-bank steps need a person on site.

    python -m ben_engine.commissioning --sim --tier ben150 --out /path/report.md [--yes] [--csv /path/data.csv]
    python -m ben_engine.commissioning --live --url http://ben-edge.local:8000 --out /path/report.md

Steps (each records values and PASS/FAIL):
 1  pre-power visual checklist (operator answers y/n; ``--yes`` auto-accepts in sim)
 2  node discovery and firmware versions
 3  sensor sanity at idle (inlet temperatures within 2 K of each other, RH plausible, ΔP tare)
 4  I/O point-to-point (toggle each relay and read it back; read each contact, including a
    forced door-open and leak)
 5  power chain: utility meter against the PDU sum within 3 % after subtracting metered
    cooling, house and UPS losses
 6  cooling unit sequential start and failover (sweeps.cooling_unit_failover); on dlc_hd also the row CDU pumps
    (sweeps.cdu_pump_failover)
 7  load step 20→100 % and thermal steady state within the ASHRAE class (sweeps.load_step);
    in real life the IT load is a resistive load bank
 8  utility loss ride-through (sweeps.utility_loss_ride_through); on dc800 also the DC bus voltage drift with
    state of charge (battery on the bus) against the 760–920 V window
 9  alarm verification (inlet high via sensor drift, leak, door, cooling fail, utility loss; all clear)
10  liquid loop: leak-to-isolation time (dlc_hd; skipped with the reason stated otherwise)
11  DC bus: insulation monitoring and ground-fault alarm (dc800; skipped with the reason stated otherwise)
12  export CSV + signed markdown report with SHA-256 of the data file and a signature block
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import platform
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional

from . import __version__
from .config import Config, PROFILE_DEFAULTS, CLIMATE_DESIGN
from .twin import Twin, TwinParams
from .sim_nodes import NodeFleet, RELAYS, FW_VERSION
from .export import TelemetryBuffer, flatten_state, write_csv
from . import sweeps as _sweeps
from .sweeps import ASHRAE_MAX, SweepResult

CHECKLIST = [
    "Container level on pad, tie-downs installed, CSC plate legible",
    "Grounding electrode conductor landed and tested (< 5 Ω)",
    "Utility feeder terminated, torque marks present, breaker open and locked",
    "No shipping damage to cooling units, condensate drains connected",
    "Fire suppression / EPO hardwired and tagged (not on controls bus)",
    "Racks anchored, blanking panels fitted, containment doors close and latch",
    "Controls LAN isolated: no route to the internet from the gateway",
    "Fiber and copper uplinks labelled at both ends",
]


@dataclass
class StepResult:
    num: int
    name: str
    passed: bool
    values: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    started_t: float = 0.0
    ended_t: float = 0.0

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass
class CommissioningReport:
    cfg: Config
    mode: str
    started: str
    steps: List[StepResult] = field(default_factory=list)
    sweep_results: Dict[str, SweepResult] = field(default_factory=dict)
    csv_path: Optional[str] = None
    csv_sha256: Optional[str] = None
    report_path: Optional[str] = None
    operator: str = "unsigned"
    organisation: str = "Schreiber AI"
    seed: int = 0

    @property
    def passed(self) -> bool:
        return all(s.passed for s in self.steps)


class Commissioning:
    """Drives the twelve commissioning steps on a twin (sim) or a gateway (live placeholder)."""

    def __init__(self, cfg: Config, sim: bool = True, yes: bool = False, seed: int = 0, operator: str = "unsigned",
                 ask: Optional[Callable[[str], str]] = None, log: Optional[Callable[[str], None]] = None,
                 params: Optional[TwinParams] = None, clock: Optional[str] = None, fast: bool = False):
        self.cfg = cfg
        self.sim = sim
        self.yes = yes
        self.seed = seed
        self.ask = ask or (lambda q: "y" if yes else input(q))
        self.log = log or (lambda m: print(m))
        self.fast = fast
        self.clock = clock
        self.twin = Twin(cfg, params=params, seed=seed)
        self.fleet = NodeFleet(cfg, seed=seed)
        self.buffer = TelemetryBuffer(hours=48, rate_hz=1.0)
        self.report = CommissioningReport(cfg, "sim" if sim else "live", clock or _now(), operator=operator, seed=seed)
        self._phase = "setup"

    # ------------------------------------------------------------ helpers
    def _run(self, seconds: float, dt: float = 1.0, record_every: float = 5.0):
        """Advance the twin, recording into the telemetry buffer."""
        n = int(seconds / dt)
        for k in range(n):
            self.twin.step(dt)
            if (k * dt) % record_every < dt - 1e-9:
                st = self.twin.state()
                st["phase"] = self._phase
                self.buffer.append(st)
        return self.twin.state()

    def _step(self, num: int, name: str, fn: Callable[[StepResult], None]) -> StepResult:
        self._phase = f"step{num}"
        sr = StepResult(num, name, True, started_t=self.twin.t)
        self.log(f"--- Step {num}: {name}")
        try:
            fn(sr)
        except Exception as e:  # a crashing step is a failed step, with the reason in the report
            sr.passed = False
            sr.notes.append(f"exception: {type(e).__name__}: {e}")
        sr.ended_t = self.twin.t
        self.log(f"    {sr.status}" + (f" — {'; '.join(sr.notes)}" if sr.notes else ""))
        self.report.steps.append(sr)
        return sr

    # ------------------------------------------------------------ steps
    def step1_checklist(self, sr: StepResult):
        answers = {}
        for item in CHECKLIST:
            a = self.ask(f"    [{item}] done? (y/n) ").strip().lower()
            answers[item] = a
            if a not in ("y", "yes"):
                sr.passed = False
                sr.notes.append(f"not confirmed: {item}")
        sr.values["answers"] = answers
        sr.values["auto_accepted"] = self.yes

    def step2_discovery(self, sr: StepResult):
        self._run(5.0)
        nodes = self.fleet.discover()
        expected = NodeFleet.expected_nodes(self.cfg)
        sr.values["nodes"] = [{"node_id": n["node_id"], "fw": n["fw"], "ip": n["ip"], "kind": n["kind"], "racks": n["racks"]} for n in nodes]
        sr.values["expected_nodes"] = expected
        fws = {n["fw"] for n in nodes}
        if len(nodes) != expected:
            sr.passed = False
            sr.notes.append(f"found {len(nodes)} nodes, expected {expected}")
        if len(fws) != 1:
            sr.passed = False
            sr.notes.append(f"mixed firmware versions {sorted(fws)}")
        sr.notes.append(f"{len(nodes)} nodes, firmware {sorted(fws)}")

    def step3_sensor_sanity(self, sr: StepResult):
        self.twin.set_it_load(0.2)
        self._run(300.0 if not self.fast else 120.0)
        st = self.twin.state()
        tele = {t: p for t, p in self.fleet.poll_all(st)}
        inlets = [v for t, p in tele.items() for k, v in p["ch"].items() if k.startswith("T_in_")]
        spread = max(inlets) - min(inlets)
        room = tele[self.fleet.nodes[0].topic("telemetry")]["ch"]
        rh = room["RH"]
        # ΔP tare: in real life both ports open; in sim we tare the live reading and check the ack and post-tare value
        ack_t, ack = self.fleet.handle(self.fleet.nodes[0].topic("cmd"), {"id": "tare-1", "op": "tare", "ch": "dP_aisle"})
        post = {t: p for t, p in self.fleet.poll_all(st)}[self.fleet.nodes[0].topic("telemetry")]["ch"]["dP_aisle"]
        sr.values.update({"inlet_spread_k": round(spread, 3), "inlet_min_c": min(inlets), "inlet_max_c": max(inlets), "rh_pct": rh,
                          "tare_ack": ack, "dp_after_tare_pa": post, "n_inlet_probes": len(inlets)})
        if spread > 2.0:
            sr.passed = False
            sr.notes.append(f"inlet probes spread {spread:.2f} K > 2 K at idle")
        if not (20.0 <= rh <= 80.0):
            sr.passed = False
            sr.notes.append(f"RH {rh} % implausible")
        if not ack.get("ok") or abs(post) > 0.5:
            sr.passed = False
            sr.notes.append(f"ΔP tare failed or residual {post} Pa")
        sr.notes.append(f"{len(inlets)} inlet probes within {spread:.2f} K; RH {rh:.0f} %; ΔP after tare {post:+.2f} Pa")

    def step4_io(self, sr: StepResult):
        results = []
        ok = True
        for node in self.fleet.nodes:
            for r in RELAYS:
                for val in (1, 0):
                    _, ack = self.fleet.handle(node.topic("cmd"), {"id": f"io-{node.node_id}-{r}-{val}", "op": "set_output", "out": r, "value": val})
                    _, rb = self.fleet.handle(node.topic("cmd"), {"id": "rb", "op": "get_output"})
                    good = ack.get("ok") and rb["result"]["outputs"][r] == val
                    ok &= bool(good)
                    results.append({"node": node.node_id, "point": r, "set": val, "read": rb["result"]["outputs"][r], "ok": bool(good)})
        # contacts: door and leak must read 0, then 1 when forced, then 0
        room = self.fleet.nodes[0]
        for fault, ch in (("door_open", "door"), ("leak", "leak")):
            seq = []
            for forced in (False, True, False):
                if forced:
                    self.twin.inject(fault)
                else:
                    self.twin.clear(fault)
                st = self._run(3.0)
                v = room.poll(st)["ch"][ch]
                seq.append(v)
                good = v == (1 if forced else 0)
                ok &= good
                results.append({"node": room.node_id, "point": ch, "set": int(forced), "read": v, "ok": good})
        sr.values["points"] = results
        sr.values["n_points"] = len(results)
        sr.values["n_failed"] = sum(1 for p in results if not p["ok"])
        sr.passed = ok
        sr.notes.append(f"{len(results)} point checks, {sr.values['n_failed']} failed")

    def step5_power_chain(self, sr: StepResult):
        self.twin.set_it_load(0.6)
        st = self._run(300.0 if not self.fast else 60.0)
        p = self.twin.p
        meter = st["power"]["utility_kw"]
        pdu_sum = sum(st["power"]["pdu_kw"])
        house = 0.5 + 0.02 * self.cfg.it_kw
        cooling = st["cooling_kw_elec"]
        ups_loss = st["power"]["ups_kw"] * (1 - p.ups_eff) / p.ups_eff if p.ups_eff else 0.0
        # the UPS output meter should see pdu_sum / pdu_eff; main meter = IT + losses + cooling + house
        expected_it = meter - cooling - house - (st["power"]["ups_kw"] - pdu_sum)
        err_pct = abs(expected_it - pdu_sum) / max(pdu_sum, 1e-6) * 100.0
        sr.values.update({"utility_meter_kw": meter, "pdu_sum_kw": round(pdu_sum, 2), "cooling_kw": cooling, "house_kw": round(house, 2),
                          "ups_input_kw": st["power"]["ups_kw"], "reconciled_it_kw": round(expected_it, 2), "disagreement_pct": round(err_pct, 2),
                          "limit_pct": 3.0, "pue": st["pue"]})
        if err_pct > 3.0:
            sr.passed = False
            sr.notes.append(f"meter vs PDU sum disagree by {err_pct:.1f} % (> 3 %)")
        sr.notes.append(f"meter {meter:.1f} kW, PDUs {pdu_sum:.1f} kW, reconciled within {err_pct:.2f} %")

    def step6_cooling(self, sr: StepResult):
        # sequential start: every healthy unit must report running when asked (standby included)
        start_log = []
        for i, u in enumerate(self.twin.cooling_units):
            u["on"] = True
            st = self._run(60.0 if not self.fast else 20.0)
            cu = st["cooling_units"][i]
            start_log.append({"unit": i + 1, "on": cu["on"], "ok": cu["ok"], "kw": cu["kw"], "fan_pct": cu["fan_pct"]})
            if not (cu["on"] and cu["ok"] and cu["kw"] > 0):
                sr.passed = False
                sr.notes.append(f"unit {i+1} did not start")
        sr.values["sequential_start"] = start_log
        res = _sweeps.cooling_unit_failover(self.twin, load=1.0, fail_s=600.0 if not self.fast else 200.0,
                                            recover_s=300.0 if not self.fast else 100.0, clock=self.clock)
        self._absorb(res)
        sr.values["failover"] = {"summary": res.summary, "criteria": [asdict(c) for c in res.criteria], "units": res.extra.get("units")}
        if not res.passed:
            sr.passed = False
            sr.notes.extend(c.name for c in res.criteria if not c.passed)
        sr.notes.append(res.summary)
        if self.twin.hd:
            # high-density liquid: every row CDU pump must run when asked, then each fails in turn with the standby taking over
            pump_log = []
            for i, u in enumerate(self.twin.cdu_pumps):
                u["on"] = True
                st = self._run(30.0 if not self.fast else 10.0)
                pp = st["loop"]["pumps"][i]
                pump_log.append({"pump": i + 1, "on": pp["on"], "ok": pp["ok"], "pct": pp["pct"]})
                if not (pp["on"] and pp["ok"] and pp["pct"] > 0):
                    sr.passed = False
                    sr.notes.append(f"CDU pump {i+1} did not start")
            sr.values["cdu_pump_start"] = pump_log
            res2 = _sweeps.cdu_pump_failover(self.twin, load=1.0, fail_s=200.0 if not self.fast else 60.0, recover_s=120.0 if not self.fast else 40.0, clock=self.clock)
            self._absorb(res2)
            sr.values["cdu_pump_failover"] = {"summary": res2.summary, "criteria": [asdict(c) for c in res2.criteria], "pumps": res2.extra.get("pumps")}
            if not res2.passed:
                sr.passed = False
                sr.notes.extend(c.name for c in res2.criteria if not c.passed)
            sr.notes.append(res2.summary)

    def step7_load_step(self, sr: StepResult):
        self.twin.set_it_load(0.2)
        self._run(120.0)
        res = _sweeps.load_step(self.twin, hold_s=900.0, clock=self.clock)
        self._absorb(res)
        cls = self.twin.d["ashrae_class"]
        sr.values.update({"summary": res.summary, "criteria": [asdict(c) for c in res.criteria], "levels": res.extra.get("levels"),
                          "ashrae_class": cls, "ashrae_max_c": ASHRAE_MAX[cls]})
        core = [c for c in res.criteria if c.name in ("max_rack_inlet_within_ashrae", "steady_state_reached_each_level", "rack_delta_t_in_band_at_full_load")]
        if not all(c.passed for c in core):
            sr.passed = False
            sr.notes.extend(c.name for c in core if not c.passed)
        rec = next((c for c in res.criteria if c.name == "max_rack_inlet_within_recommended"), None)
        if rec is not None and not rec.passed:
            sr.notes.append(f"inside allowable but outside the ASHRAE recommended 27 C envelope ({rec.value} C)")
        sr.notes.append(res.summary)
        sr.notes.append("In the field the IT load is a resistive load bank in each rack (or the customer's servers at a burn-in load); "
                        "record the load-bank serial numbers and kW settings here.")

    def step8_ride_through(self, sr: StepResult):
        res = _sweeps.utility_loss_ride_through(self.twin, load=1.0, clock=self.clock)
        self._absorb(res)
        sr.values.update({"summary": res.summary, "criteria": [asdict(c) for c in res.criteria], **res.extra})
        if not res.passed:
            sr.passed = False
            sr.notes.extend(c.name for c in res.criteria if not c.passed)
        sr.notes.append(res.summary)
        if self.twin.dc800:
            # battery on the bus: the bus voltage must stay inside the 760-920 V window while the battery carries the load
            vs = [r["dc_v_bus"] for r in res.rows if r.get("phase") == "utility_loss" and r.get("dc_v_bus") is not None and r.get("power_ups_soc_pct", 0) > 5]
            lo, hi = self.twin.d["dc_bus_v_min"], self.twin.d["dc_bus_v_max"]
            vmin, vmax = (min(vs), max(vs)) if vs else (None, None)
            ok = bool(vs) and lo <= vmin and vmax <= hi
            sr.values.update({"dc_bus_v_min_on_battery": vmin, "dc_bus_v_max_on_battery": vmax, "dc_bus_window_v": [lo, hi], "dc_bus_in_window": ok})
            if not ok:
                sr.passed = False
                sr.notes.append(f"DC bus left the {lo}-{hi} V window on battery ({vmin}-{vmax} V)")
            sr.notes.append(f"800 VDC bus on battery: {vmin}-{vmax} V while SoC > 5 % (window {lo}-{hi} V); battery on the bus, no UPS double conversion")

    def step9_alarms(self, sr: StepResult):
        checks = []
        self.twin.set_it_load(0.8)
        cls = self.twin.d["ashrae_class"]
        a_max = ASHRAE_MAX[cls]
        # recover from the ride-through test: wait until the hottest inlet is back under the warning
        # threshold (up to 30 min) and record how long that took; the UPS recharges over hours
        t0 = self.twin.t
        st = self.twin.state()
        while max(st["rack_inlet_c"]) > a_max - 2.5 and self.twin.t - t0 < 1800.0:
            st = self._run(30.0)
        st = self._run(120.0)
        recovery_min = round((self.twin.t - t0) / 60.0, 1)
        pre_existing = sorted(a["id"] for a in st["alarms"])
        sr.values["recovery_after_ride_through_min"] = recovery_min
        sr.notes.append(f"inlets back under {a_max - 2.5:.1f} C {recovery_min} min after cooling was restored")
        if pre_existing:
            sr.notes.append(f"alarms already active before the test (carried over from step 8, not counted): {pre_existing}")

        def expect(alarm_prefix: str, inject: str, clear_kw: Dict[str, Any], wait_s: float = 30.0, **kw):
            self.twin.inject(inject, **kw)
            st = self._run(wait_s)
            raised = [a["id"] for a in st["alarms"] if a["id"].startswith(alarm_prefix) and a["id"] not in pre_existing]
            self.twin.clear(inject, **clear_kw)
            st2 = self._run(wait_s)
            still = [a["id"] for a in st2["alarms"] if a["id"].startswith(alarm_prefix) and a["id"] not in pre_existing]
            ok = bool(raised) and not still
            checks.append({"alarm": alarm_prefix, "via": inject, "raised": raised[:3], "cleared": not still, "ok": ok})
            return ok

        # inlet high: drift the inlet sensors up past the class limit
        st = self.twin.state()
        delta = a_max - min(st["rack_inlet_c"]) + 1.0
        ok = expect("rack", "sensor_drift", {}, delta_c=delta)
        ok &= expect("leak", "leak", {})
        ok &= expect("door_open", "door_open", {})
        ok &= expect("cool1_fail", "cooling_unit_fail", {"unit": 0}, unit=0)
        ok &= expect("utility_loss", "utility_loss", {}, wait_s=10.0)
        st = self._run(300.0)
        residual = [a["id"] for a in st["alarms"] if a["id"] not in pre_existing]
        sr.values.update({"checks": checks, "residual_alarms": residual, "pre_existing_alarms": pre_existing})
        if residual:
            ok = False
            sr.notes.append(f"alarms still active after clearing: {residual}")
        sr.passed = ok
        sr.notes.append(f"{sum(c['ok'] for c in checks)}/{len(checks)} alarm paths raised and cleared")

    def step10_leak_isolation(self, sr: StepResult):
        """dlc_hd: inject a leak at the rack manifold; the detection + isolation valve must close within 15 s and the loop must
        be reported isolated. Skipped with the reason when the unit has no high-density liquid loop."""
        if not self.twin.hd:
            sr.values["skipped"] = True
            sr.notes.append(f"skipped: not applicable — cooling is {self.cfg.cooling}, the leak-to-isolation step needs the high-density liquid loop (dlc_hd)")
            return
        self.twin.set_it_load(0.6)
        self._run(60.0 if not self.fast else 20.0)
        self.twin.inject("leak")
        t0 = self.twin.t
        st = self._run(1.0)
        while st["loop"]["leak_to_isolation_s"] is None and self.twin.t - t0 < 60.0:
            st = self._run(1.0)
        t_iso = st["loop"]["leak_to_isolation_s"]
        alarm = any(a["id"] == "loop_isolated" for a in st["alarms"])
        flow_after = self._run(30.0)["loop"]["flow_lpm"]
        self.twin.clear("leak")
        self._run(60.0 if not self.fast else 20.0)
        limit_s = 15.0
        sr.values.update({"leak_to_isolation_s": t_iso, "limit_s": limit_s, "isolated_alarm": alarm, "flow_after_isolation_lpm": flow_after})
        if t_iso is None or t_iso > limit_s or not alarm or flow_after > 0.05 * self.twin.d["loop_flow_lpm"]:
            sr.passed = False
            sr.notes.append(f"leak to valve closed {t_iso} s (limit {limit_s:.0f} s), alarm {alarm}, flow after {flow_after} L/min")
        sr.notes.append(f"leak injected at the rack manifold: isolation valves closed after {t_iso} s (limit {limit_s:.0f} s), loop flow {flow_after} L/min after isolation, alarm raised; "
                        "in the field the leak is a wet-finger test on the drip-tray sensor with the valve position switch timed (E19)")

    def step11_dc_bus_imd(self, sr: StepResult):
        """dc800: insulation monitoring reads healthy, a ground fault on each pole drops it and raises the critical alarm within
        10 s without tripping the IT load, and the alarm clears. Skipped with the reason on an AC unit."""
        if not self.twin.dc800:
            sr.values["skipped"] = True
            sr.notes.append(f"skipped: not applicable — power architecture is {self.cfg.power_architecture}; the DC bus insulation step needs the 800 VDC option (dc800)")
            return
        healthy = self.twin.state()["dc"]["imd_kohm"]
        res = _sweeps.dc_ground_fault_response(self.twin, load=0.8, hold_s=60.0 if not self.fast else 30.0, clock=self.clock)
        self._absorb(res)
        sr.values.update({"imd_healthy_kohm": healthy, "summary": res.summary, "criteria": [asdict(c) for c in res.criteria], **res.extra})
        if healthy < 500.0:
            sr.passed = False
            sr.notes.append(f"insulation resistance {healthy} kΩ before the test is below 500 kΩ")
        if not res.passed:
            sr.passed = False
            sr.notes.extend(c.name for c in res.criteria if not c.passed)
        sr.notes.append(res.summary)
        sr.notes.append("In the field the ground fault is a listed test resistor from each pole to the ground bar with the IMD test button; the location function is checked on the faulted tap-off (E17).")

    def step12_export(self, sr: StepResult, csv_path: str, report_path: str):
        self._phase = "export"
        rows = self.buffer.to_rows()
        write_csv(rows, csv_path)
        sha = _sha256(csv_path)
        self.report.csv_path = csv_path
        self.report.csv_sha256 = sha
        self.report.report_path = report_path
        sr.values.update({"csv": csv_path, "rows": len(rows), "sha256": sha})
        sr.notes.append(f"{len(rows)} rows → {csv_path} (sha256 {sha[:16]}…)")

    def _absorb(self, res: SweepResult):
        """Keep sweep rows in the telemetry buffer so the exported CSV holds everything."""
        self.report.sweep_results[res.name] = res
        for r in res.rows:
            self.buffer.append(_unflatten_min(r))

    # ------------------------------------------------------------ driver
    def run(self, out_path: str, csv_path: Optional[str] = None) -> CommissioningReport:
        if not self.sim:
            raise RuntimeError("live mode is driven by run_live(); use --sim for the simulator")
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        csv_path = csv_path or os.path.splitext(out_path)[0] + "_data.csv"
        self._step(1, "Pre-power visual checklist", self.step1_checklist)
        self._step(2, "Node discovery and firmware versions", self.step2_discovery)
        self._step(3, "Sensor sanity at idle", self.step3_sensor_sanity)
        self._step(4, "I/O point-to-point test", self.step4_io)
        self._step(5, "Power chain: meter vs PDU sum", self.step5_power_chain)
        self._step(6, "Cooling unit sequential start and failover", self.step6_cooling)
        self._step(7, "Load step to 100 % and thermal steady state", self.step7_load_step)
        self._step(8, "Utility loss ride-through", self.step8_ride_through)
        self._step(9, "Alarm verification", self.step9_alarms)
        self._step(10, "Liquid loop: leak-to-isolation time", self.step10_leak_isolation)
        self._step(11, "DC bus: insulation monitoring and ground-fault alarm", self.step11_dc_bus_imd)
        self._step(12, "Export CSV and signed report", lambda sr: self.step12_export(sr, csv_path, out_path))
        md = render_markdown(self.report)
        with open(out_path, "w") as fh:
            fh.write(md)
        self.log(f"report → {out_path}  ({'PASS' if self.report.passed else 'FAIL'})")
        return self.report


# ------------------------------------------------------------------ live placeholder
def run_live(url: str, cfg: Optional[Config], out_path: str, log=print) -> CommissioningReport:
    """Placeholder live adapter: confirms the gateway answers, pulls its config and latest state,
    writes a report that says what remains to be done by hand. The full live sequence (relay
    toggling with a second person at the panel, load bank, breaker operation) is executed step by
    step from the dashboard's commissioning page; this CLI entry only proves connectivity."""
    import urllib.request
    rep = CommissioningReport(cfg or Config(), "live", _now())
    sr = StepResult(0, f"Gateway connectivity {url}", True)
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/api/config", timeout=5) as r:
            cfg_json = json.loads(r.read().decode())
        with urllib.request.urlopen(url.rstrip("/") + "/api/state", timeout=5) as r:
            state = json.loads(r.read().decode())
        rep.cfg = Config.from_dict(cfg_json.get("config", cfg_json))
        sr.values = {"config": rep.cfg.to_dict(), "state_t": state.get("t"), "alarms": state.get("alarms")}
        sr.notes.append("gateway reachable; live steps 1–12 must be run from the dashboard commissioning page with a person on site")
    except Exception as e:
        sr.passed = False
        sr.notes.append(f"gateway not reachable: {e}")
    rep.steps.append(sr)
    with open(out_path, "w") as fh:
        fh.write(render_markdown(rep))
    log(f"report → {out_path}")
    return rep


# ------------------------------------------------------------------ report
def render_markdown(rep: CommissioningReport) -> str:
    cfg = rep.cfg
    d = cfg.derived()
    L = []
    L.append(f"# BEN Engine commissioning report — {d['tier_label']} — {cfg.site_name}")
    L.append("")
    L.append(f"Schreiber AI · BEN Engine `ben_engine {__version__}` · mode **{rep.mode}** · started {rep.started} · "
             f"overall **{'PASS' if rep.passed else 'FAIL'}**")
    L.append("")
    L.append("## Unit")
    L.append("")
    L.append("| Item | Value |")
    L.append("| --- | --- |")
    for k, v in (("Tier", d["tier_label"]), ("Enclosure", d["enclosure"]), ("Mission profile", PROFILE_DEFAULTS[cfg.profile]["label"]),
                 ("IT load", f"{cfg.it_kw} kW in {cfg.racks} racks ({d['per_rack_kw']} kW/rack)"), ("Cooling", f"{d['cooling_label']}, {d['cooling_units_total']} units ({cfg.redundancy})"),
                 ("Power", (f"{d['voltage']} service, {d['service_breaker_a']} A; 800 VDC bus (±{d['dc_bus_v_pole']} V, {d['dc_bus_v_min']}–{d['dc_bus_v_max']} V window), AC/DC front end {d['ac_dc_front_end_kw']} kW "
                            f"({d['rectifier_modules']} × {d['rectifier_module_kw']} kW), busway {d['dc_busway_a']} A, battery on bus {d['battery_on_bus_kwh']} kWh for {cfg.ups_minutes} min — forward architecture study")
                           if cfg.power_architecture == "dc800" else
                           f"{d['voltage']}, {d['service_breaker_a']} A service, UPS {d['ups_modules']} × {d['ups_kva_each']} kVA, battery {d['battery_kwh']} kWh for {cfg.ups_minutes} min"),
                 ("Climate", f"{CLIMATE_DESIGN[cfg.climate]['label']}, design {CLIMATE_DESIGN[cfg.climate]['t_design_c']} C"), ("ASHRAE class", d["ashrae_class"]),
                 *([("Liquid loop", f"{d['loop_water_class']} warm water, {d['loop_supply_design_c']:.0f}/{d['loop_return_design_c']:.0f} C, {d['loop_flow_lpm']} L/min at ΔT {d['loop_dt_design_k']:.0f} K, heat reuse {d['heat_reuse_kw_available']} kW available")] if cfg.cooling == "dlc_hd" else []),
                 ("Twin seed", rep.seed)):
        L.append(f"| {k} | {v} |")
    L.append("")
    L.append("## Steps")
    L.append("")
    L.append("| # | Step | Result | Key values |")
    L.append("| --- | --- | --- | --- |")
    for s in rep.steps:
        L.append(f"| {s.num} | {s.name} | **{s.status}** | {_key_values(s)} |")
    L.append("")
    for s in rep.steps:
        L.append(f"### Step {s.num}: {s.name} — {s.status}")
        L.append("")
        for n in s.notes:
            L.append(f"- {n}")
        detail = _detail_table(s)
        if detail:
            L.append("")
            L.extend(detail)
        L.append("")
    if rep.sweep_results:
        L.append("## Sweep criteria")
        L.append("")
        L.append(_sweeps.report_markdown(list(rep.sweep_results.values())))
    L.append("## Data")
    L.append("")
    if rep.csv_path:
        L.append(f"- Telemetry CSV: `{os.path.basename(rep.csv_path)}`")
        L.append(f"- SHA-256: `{rep.csv_sha256}`")
        L.append("- Verify with `sha256sum <file>`; the report is valid only with a data file whose hash matches.")
    else:
        L.append("- no data file")
    L.append("")
    L.append("## Notes and limits")
    L.append("")
    L.append("- Simulation mode exercises the control logic, protocol, sweeps and report path against the digital twin; it does not prove "
             "the hardware. Live commissioning repeats every step on the real unit with a resistive load bank.")
    L.append("- Temperatures are read from calibrated DS18B20 strings (U95 ±0.25 K per spec/PROTOCOL.md); pass/fail margins smaller than that are not meaningful.")
    L.append("- The ride-through result is the time to the ASHRAE allowable limit with cooling off; battery minutes are the UPS runtime at the tested load.")
    L.append("- Steps 10 and 11 belong to the forward architecture (docs/FORWARD_ARCHITECTURE_DECISION.md); on a unit without the high-density liquid loop or the 800 VDC bus "
             "they are recorded as skipped with the reason and count as passed.")
    L.append("")
    L.append("## Signature")
    L.append("")
    L.append("| Role | Name | Organisation | Date | Signature |")
    L.append("| --- | --- | --- | --- | --- |")
    L.append(f"| Commissioning engineer | {rep.operator} | {rep.organisation} | {rep.started[:10]} | |")
    L.append("| Customer witness | | | | |")
    L.append("")
    L.append(f"Report generated by `ben_engine.commissioning` on {platform.node() or 'host'}; mode {rep.mode}; "
             f"data hash {rep.csv_sha256 or 'n/a'}.")
    return "\n".join(L)


def _key_values(s: StepResult) -> str:
    v = s.values
    keep = {}
    for k in ("inlet_spread_k", "rh_pct", "dp_after_tare_pa", "n_points", "n_failed", "disagreement_pct", "utility_meter_kw", "pdu_sum_kw",
              "minutes_to_ashrae_max", "minutes_to_ups_empty", "rows", "expected_nodes", "ashrae_max_c", "skipped", "leak_to_isolation_s",
              "imd_healthy_kohm", "dc_bus_v_min_on_battery", "dc_bus_v_max_on_battery"):
        if k in v:
            keep[k] = v[k]
    if "nodes" in v:
        keep["nodes"] = len(v["nodes"])
    if "levels" in v and v["levels"]:
        keep["max_inlet_c_at_100"] = v["levels"][-1]["max_inlet_c"]
    if "checks" in v:
        keep["alarm_paths_ok"] = f"{sum(c['ok'] for c in v['checks'])}/{len(v['checks'])}"
    if "sha256" in v:
        keep["sha256"] = v["sha256"][:12] + "…"
    return ", ".join(f"{k}={val}" for k, val in keep.items()) or "—"


def _detail_table(s: StepResult) -> List[str]:
    v = s.values
    out: List[str] = []
    if "answers" in v:
        out += [f"Checklist {'auto-accepted (simulation)' if v.get('auto_accepted') else 'answered by operator'}:", "",
                "| Item | Answer |", "| --- | --- |"] + [f"| {k} | {a} |" for k, a in v["answers"].items()]
    if "nodes" in v:
        out += ["| Node | Kind | Racks | Firmware | IP |", "| --- | --- | --- | --- | --- |"]
        out += [f"| {n['node_id']} | {n['kind']} | {n['racks']} | {n['fw']} | {n['ip']} |" for n in v["nodes"]]
    if "points" in v:
        failed = [p for p in v["points"] if not p["ok"]]
        out += [f"{v['n_points']} point checks; failed: {len(failed)}"]
        if failed:
            out += ["", "| Node | Point | Set | Read |", "| --- | --- | --- | --- |"] + [f"| {p['node']} | {p['point']} | {p['set']} | {p['read']} |" for p in failed]
    if "levels" in v and v["levels"]:
        out += ["| Load | Max inlet C | Mean ΔT K | PUE | Settle s | Steady |", "| --- | --- | --- | --- | --- | --- |"]
        out += [f"| {int(l['load']*100)} % | {l['max_inlet_c']} | {l['mean_delta_t_k']} | {l['pue']} | {l['settle_s']} | {'yes' if l['steady'] else 'no'} |" for l in v["levels"]]
    if "failover" in v and v["failover"].get("units"):
        out += ["| Unit failed | Peak inlet C | Units running after | Standby start s | Alarm |", "| --- | --- | --- | --- | --- |"]
        out += [f"| {u['unit']} | {u['peak_inlet_c']} | {u['running_after_fail']} | {u['standby_started_after_s']} | {'yes' if u['alarm_raised'] else 'no'} |" for u in v["failover"]["units"]]
    if "checks" in v:
        out += ["| Alarm | Forced via | Raised | Cleared |", "| --- | --- | --- | --- |"]
        out += [f"| {c['alarm']} | {c['via']} | {', '.join(c['raised']) or 'NO'} | {'yes' if c['cleared'] else 'NO'} |" for c in v["checks"]]
    if "utility_meter_kw" in v:
        out += ["| Utility meter kW | PDU sum kW | Cooling kW | House kW | UPS input kW | Reconciled IT kW | Disagreement % |", "| --- | --- | --- | --- | --- | --- | --- |",
                f"| {v['utility_meter_kw']} | {v['pdu_sum_kw']} | {v['cooling_kw']} | {v['house_kw']} | {v['ups_input_kw']} | {v['reconciled_it_kw']} | {v['disagreement_pct']} |"]
    if "sequential_start" in v:
        out += ["| Unit | On | OK | kW | Fan % |", "| --- | --- | --- | --- | --- |"]
        out += [f"| {u['unit']} | {u['on']} | {u['ok']} | {u['kw']} | {u['fan_pct']} |" for u in v["sequential_start"]]
    if "cdu_pump_failover" in v and v["cdu_pump_failover"].get("pumps"):
        out += ["", "| CDU pump failed | Standby start s | Min flow % | Max ΔT K | Alarm |", "| --- | --- | --- | --- | --- |"]
        out += [f"| {u['pump']} | {u['standby_started_after_s']} | {u['min_flow_pct']} | {u['max_dt_k']} | {'yes' if u['alarm_raised'] else 'no'} |" for u in v["cdu_pump_failover"]["pumps"]]
    if "poles" in v:
        out += ["| Pole | Alarm after s | IMD kΩ at fault | V+ | V− | IT kW held | Cleared |", "| --- | --- | --- | --- | --- | --- | --- |"]
        out += [f"| {p['pole']} | {p['alarm_after_s']} | {p['imd_kohm_at_fault']} | {p['v_pos']} | {p['v_neg']} | {p['it_kw_min_during_fault']} | {'yes' if p['alarm_cleared'] else 'NO'} |" for p in v["poles"]]
    return out


def _unflatten_min(row: Dict[str, Any]) -> Dict[str, Any]:
    """Sweep rows are already flat; wrap them so the buffer's flattening is a no-op."""
    return dict(row)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="BEN Engine site commissioning")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sim", action="store_true", help="run against the digital twin and virtual nodes")
    mode.add_argument("--live", action="store_true", help="connect to a gateway (placeholder: connectivity + report)")
    ap.add_argument("--url", default="http://localhost:8000", help="gateway API base URL for --live")
    ap.add_argument("--tier", default="ben150")
    ap.add_argument("--profile", default="ai_inference")
    ap.add_argument("--climate", default="temperate")
    ap.add_argument("--site", default="Demo site")
    ap.add_argument("--out", required=True, help="markdown report path")
    ap.add_argument("--csv", default=None, help="telemetry CSV path (default next to report)")
    ap.add_argument("--yes", action="store_true", help="auto-accept the visual checklist (sim)")
    ap.add_argument("--operator", default="unsigned")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fast", action="store_true", help="shorter holds (tests)")
    a = ap.parse_args(argv)
    cfg = Config.preset(a.tier, a.profile, a.climate)
    cfg.site_name = a.site
    if a.live:
        rep = run_live(a.url, cfg, a.out)
        return 0 if rep.passed else 1
    c = Commissioning(cfg, sim=True, yes=a.yes, seed=a.seed, operator=a.operator, fast=a.fast)
    rep = c.run(a.out, a.csv)
    return 0 if rep.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
