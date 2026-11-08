"""API tests for the BEN Engine dashboard server (ben_engine.api) using FastAPI's TestClient.

Run:  PYTHONPATH=software pytest tests/test_api.py -q
"""
from __future__ import annotations

import csv
import io
import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from ben_engine.api import app, RT, BUILTIN_SWEEPS  # noqa: E402
from ben_engine.config import Config, TIER_GEOMETRY  # noqa: E402
from ben_engine.twin import Twin  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_config(client):
    """Every test starts from the BEN 20 preset at 1x speed."""
    client.post("/api/config", json=Config.preset("ben20").to_dict())
    client.post("/api/sim/speed", json={"x": 1})
    client.delete("/api/faults")
    yield


# --------------------------------------------------------------------------- health
def test_health_reports_running_twin(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    h = r.json()
    assert h["twin_running"] is True
    assert h["mode"] == "sim"
    assert h["last_step_age_s"] is not None and h["last_step_age_s"] < 5
    assert isinstance(h["modules"], dict) and set(h["modules"]) >= {"sweeps", "sim_nodes", "export", "cfd"}
    assert h["ok"] is True


def test_dashboard_static_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "BEN Engine" in r.text
    assert client.get("/vendor/three/three.module.js").status_code == 200


# --------------------------------------------------------------------------- presets / catalog / config
def test_presets_cover_all_tiers(client):
    p = client.get("/api/presets").json()
    assert set(p) == set(TIER_GEOMETRY)
    for tier, item in p.items():
        assert item["config"]["tier"] == tier
        assert item["derived"]["service_breaker_a"] > 0
        assert Config.from_dict(item["config"]).validate() == []


def test_catalog_shape(client):
    c = client.get("/api/catalog").json()
    assert set(c["tiers"]) == set(TIER_GEOMETRY)
    assert "ai_inference" in c["profiles"] and "inrow_dx" in c["cooling"] and "temperate" in c["climates"]
    assert set(c["faults"]) == set(Twin.FAULTS)


def test_config_get_has_config_derived_sensors(client):
    r = client.get("/api/config").json()
    assert r["config"]["tier"] == "ben20"
    assert r["derived"]["tier_label"] == "BEN 20"
    assert r["errors"] == []
    assert len(r["sensors"]) == len(Twin(Config.preset("ben20")).sensors())
    assert {"id", "kind", "location_m", "unit", "u95", "node"} <= set(r["sensors"][0])


def test_config_post_valid_rebuilds_twin(client):
    r = client.post("/api/config", json={"tier": "ben40", "it_kw": 300, "racks": 8, "cooling": "dlc_cdu", "redundancy": "N+1"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["config"]["tier"] == "ben40" and body["config"]["racks"] == 8
    assert body["derived"]["tier_label"] == "BEN 40"
    st = client.get("/api/state").json()
    assert st["tier"] == "ben40" and len(st["rack_inlet_c"]) == 8
    assert len(client.get("/api/sensors").json()) == len(body["sensors"])


def test_config_post_invalid_returns_400_with_errors(client):
    r = client.post("/api/config", json={"it_kw": 9999})
    assert r.status_code == 400
    errs = r.json()["errors"]
    assert errs and any("kW" in e for e in errs)
    # the running twin is untouched
    assert client.get("/api/state").json()["tier"] == "ben20"
    r = client.post("/api/config", json={"tier": "micro", "cooling": "inrow_dx", "it_kw": 4, "racks": 1})
    assert r.status_code == 400 and any("Micro" in e for e in r.json()["errors"])


def test_config_validate_endpoint_does_not_apply(client):
    r = client.post("/api/config/validate", json={"racks": 99}).json()
    assert r["errors"] and r["derived"] is None
    assert client.get("/api/config").json()["config"]["racks"] == 5


# --------------------------------------------------------------------------- state
def test_state_shape(client):
    st = client.get("/api/state").json()
    for k in ("t", "outdoor_c", "it_kw", "it_fraction", "rack_inlet_c", "rack_outlet_c", "supply_c", "return_c",
              "aisle_dp_pa", "rh_pct", "cooling_units", "cooling_kw_elec", "power", "pue", "alarms", "faults", "door_open", "leak",
              "wall_ts", "sim_speed", "mode"):
        assert k in st, k
    assert isinstance(st["rack_inlet_c"], list) and len(st["rack_inlet_c"]) == 5
    assert {"on", "kw", "fan_pct", "ok"} <= set(st["cooling_units"][0])
    assert {"utility_ok", "utility_kw", "ups_kw", "ups_soc_pct", "ups_runtime_min", "ups_on_battery", "generator_on", "pdu_kw"} <= set(st["power"])
    assert len(st["power"]["pdu_kw"]) == 5


def test_websocket_pushes_config_then_state(client):
    with client.websocket_connect("/ws/state") as ws:
        m1 = ws.receive_json()
        assert m1["type"] == "config" and m1["config"]["tier"] == "ben20"
        m2 = ws.receive_json()
        assert m2["type"] == "state" and "rack_inlet_c" in m2["state"]


# --------------------------------------------------------------------------- faults / load / outdoor
def test_fault_inject_and_clear(client):
    r = client.post("/api/fault", json={"name": "cooling_unit_fail", "params": {"unit": 0}})
    assert r.status_code == 200
    assert "cooling_unit_fail" in r.json()["faults"]
    assert any(a["id"] == "cool1_fail" for a in r.json()["alarms"])
    st = client.get("/api/state").json()
    assert st["cooling_units"][0]["ok"] is False
    r = client.delete("/api/fault/cooling_unit_fail")
    assert r.status_code == 200 and r.json()["faults"] == []
    assert client.get("/api/state").json()["cooling_units"][0]["ok"] is True


def test_fault_unknown_rejected(client):
    assert client.post("/api/fault", json={"name": "meteor"}).status_code == 400
    assert client.delete("/api/fault/meteor").status_code == 400


def test_door_open_raises_warning_alarm(client):
    client.post("/api/fault", json={"name": "door_open"})
    st = client.get("/api/state").json()
    assert st["door_open"] is True
    assert any(a["id"] == "door_open" and a["sev"] == "warn" for a in st["alarms"])
    client.delete("/api/fault/door_open")


def test_load_and_outdoor(client):
    assert client.post("/api/load", json={"fraction": 0.5}).json()["fraction"] == 0.5
    assert client.post("/api/load", json={"fraction": 5}).status_code == 400
    assert client.post("/api/outdoor", json={"c": 40}).json()["outdoor_c"] == 40
    assert client.get("/api/sim").json()["outdoor_c"] == 40
    assert client.post("/api/outdoor", json={"c": 99}).status_code == 400


# --------------------------------------------------------------------------- sim speed
def test_sim_speed(client):
    assert client.post("/api/sim/speed", json={"x": 30}).json()["speed"] == 30
    assert client.get("/api/health").json()["sim_speed"] == 30
    assert client.post("/api/sim/speed", json={"x": 0}).status_code == 400
    assert client.post("/api/sim/speed", json={"x": 61}).status_code == 400
    assert client.post("/api/sim/speed", json={"x": "fast"}).status_code == 400
    t0 = client.get("/api/state").json()["t"]
    RT.tick()  # one scheduler tick advances `speed` simulated seconds
    assert client.get("/api/state").json()["t"] - t0 == 30
    client.post("/api/sim/speed", json={"x": 1})


def test_sim_mode_live_records_url_only(client):
    r = client.post("/api/sim/mode", json={"mode": "live", "gateway_url": "http://10.77.0.1:8080"}).json()
    assert r["mode"] == "live" and r["gateway_url"].startswith("http://10.77") and r["note"]
    assert client.get("/api/state").json()["mode"] == "live"
    assert client.post("/api/sim/mode", json={"mode": "sim"}).json()["mode"] == "sim"
    assert client.post("/api/sim/mode", json={"mode": "hybrid"}).status_code == 400


# --------------------------------------------------------------------------- export
def test_export_csv_has_header_and_rows(client):
    for _ in range(3):
        RT.tick()
    r = client.get("/api/export.csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in r.headers["content-disposition"] and r.headers["content-disposition"].endswith('.csv"')
    rows = list(csv.DictReader(io.StringIO(r.text)))
    assert len(rows) >= 3
    assert int(r.headers["X-Row-Count"]) == len(rows)
    hdr = set(rows[0])
    assert {"ts", "ts_iso", "t", "supply_c", "return_c", "rack_inlet_c_1", "power_utility_kw", "power_ups_soc_pct"} <= hdr
    assert float(rows[-1]["t"]) > float(rows[0]["t"])


def test_export_range_filters_and_json(client):
    now = time.time()
    r = client.get(f"/api/export.csv?from={now + 3600}")
    assert int(r.headers["X-Row-Count"]) == 0
    assert r.text.strip() == "" or len(r.text.splitlines()) == 1  # header only (or empty when no columns known)
    r = client.get("/api/export.json?last=600")
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/json")
    body = r.json()
    assert body["config"]["tier"] == "ben20" and isinstance(body["rows"], list) and body["rows"]
    assert client.get("/api/export.csv?from=not-a-time").status_code == 400
    rng = client.get("/api/export/range").json()
    assert rng["rows"] > 0 and rng["from"] <= rng["to"]


# --------------------------------------------------------------------------- sweeps
def test_sweep_catalog_and_run(client):
    cat = client.get("/api/sweeps/catalog").json()
    assert cat["sweeps"] and cat["source"] in ("builtin", "ben_engine.sweeps")
    name = cat["all"][0]
    r = client.post("/api/sweep", json={"name": name})
    assert r.status_code == 200
    sid = r.json()["id"]
    for _ in range(600):
        job = next(j for j in client.get("/api/sweeps").json() if j["id"] == sid)
        if job["status"] in ("done", "failed"):
            break
        time.sleep(0.05)
    assert job["status"] == "done", job.get("error")
    assert job["results"][0]["criteria"], "sweep must report criteria"
    assert all({"name", "pass"} <= set(c) for c in job["results"][0]["criteria"])
    assert isinstance(job["passed"], bool)
    r = client.get(f"/api/sweeps/{sid}.csv")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    assert len(r.text.splitlines()) > 2
    assert client.get(f"/api/sweeps/{sid}").json()["id"] == sid
    assert client.post("/api/sweep", json={"name": "does_not_exist"}).status_code == 404
    assert client.get("/api/sweeps/nope.csv").status_code == 404


def test_builtin_sweeps_run_for_every_tier():
    for tier in TIER_GEOMETRY:
        cfg = Config.preset(tier)
        for name in BUILTIN_SWEEPS:
            res = __import__("ben_engine.api", fromlist=["_builtin_sweep"])._builtin_sweep(name, cfg, lambda p: None)
            assert res["rows"] and res["criteria"]


# --------------------------------------------------------------------------- I/O (virtual nodes)
def test_io_status_and_test(client):
    r = client.get("/api/io/status")
    if r.status_code == 503:
        pytest.skip(f"sim_nodes not available: {r.json()['detail']}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["nodes"], "at least one virtual node"
    n0 = body["nodes"][0]
    assert {"id", "channels", "outputs", "status"} <= set(n0)
    assert n0["channels"] and {"id", "value", "raw"} <= set(n0["channels"][0])
    relay = n0["outputs"][0]["id"]
    t = client.post("/api/io/test", json={"node": n0["id"], "channel": relay, "value": 1}).json()
    assert t["ack"]["ok"] is True and t["latency_ms"] >= 0
    t = client.post("/api/io/test", json={"node": n0["id"], "op": "identify"}).json()
    assert t["ack"]["ok"] is True
    assert client.post("/api/io/test", json={"node": "node99", "op": "identify"}).status_code == 404
    assert client.get("/api/io/status").json()["log"]


# --------------------------------------------------------------------------- optional modules degrade gracefully
def test_calibrate_endpoint(client):
    pts = [{"reference": r, "reading": r * 1.002 - 0.2} for r in (15, 20, 25, 30, 35)]
    r = client.post("/api/calibrate", json={"channel": "T_in_r1_1.2", "reference_points": pts})
    if r.status_code == 503:
        pytest.skip(r.json()["detail"])
    assert r.status_code == 200, r.text
    b = r.json()
    assert abs(b["gain"] - 1 / 1.002) < 1e-3 and abs(b["offset"] - 0.2 / 1.002) < 1e-2
    assert "u95" in b
    assert client.post("/api/calibrate", json={"channel": "x", "reference_points": []}).status_code == 400
    a = client.post("/api/calibrate/apply", json={"channel": "T_in_r1_1.2"}).json()
    assert a["applied_to_twin"] is True


def test_bom_endpoint(client):
    r = client.get("/api/bom")
    if r.status_code == 503:
        pytest.skip(r.json()["detail"])
    assert r.status_code == 200
    assert r.json()["lines"]


def test_cfd_metrics_idle_or_503(client):
    r = client.get("/api/cfd/metrics")
    assert r.status_code in (200, 503)
    if r.status_code == 503:
        assert "not yet available" in r.json()["detail"]
    r = client.get("/api/cfd")
    assert r.status_code in (404, 503)


def test_commission_status_idle_or_module_flag(client):
    r = client.get("/api/commission/status")
    assert r.status_code == 200
    assert r.json()["status"] in ("idle", "running", "done", "failed")


def test_proposal_and_package_endpoints(client):
    r = client.get("/api/proposal/options")
    assert r.status_code == 200 and "managed" in r.json()["options"]
    r = client.post("/api/proposal", json={"option": "managed", "customer": "Test Co", "site": "Test Site"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["proposal_id"].startswith("SAI-")
    h = client.get(j["html_url"])
    assert h.status_code == 200 and "Schreiber AI" in h.text
    r = client.post("/api/package", json={"option": "hardware_controls", "customer": "Test Co", "site": "Test Site", "drawings": False})
    assert r.status_code == 200, r.text
    z = client.get(r.json()["customer"]["zip_url"])
    assert z.status_code == 200 and z.headers["content-type"].startswith("application/zip")
