"""Automated sweeps: determinism, criteria, flattening and CSV."""
import csv

from ben_engine.config import Config
from ben_engine.twin import Twin
from ben_engine import sweeps as sw
from ben_engine.export import flatten_state


def test_flatten_state_rules():
    st = {"t": 1.0, "rack_inlet_c": [20.0, 21.0], "power": {"ups_soc_pct": 99.0, "pdu_kw": [1.0]},
          "cooling_units": [{"on": True, "kw": 2.0}], "alarms": [{"id": "x", "sev": "warn"}], "faults": ["door_open"]}
    f = flatten_state(st)
    assert f["rack_inlet_c_1"] == 20.0 and f["rack_inlet_c_2"] == 21.0
    assert f["power_ups_soc_pct"] == 99.0 and f["power_pdu_kw_1"] == 1.0
    assert f["cooling_units_1_on"] is True and f["cooling_units_1_kw"] == 2.0
    assert f["alarm_count"] == 1 and f["alarm_ids"] == "x" and f["alarm_max_sev"] == "warn"
    assert f["faults"] == "door_open"
    assert not any(isinstance(v, (list, dict)) for v in f.values())


def test_load_step_passes_and_is_deterministic():
    cfg = Config.preset("ben20")
    r1 = sw.load_step(Twin(cfg, seed=1), hold_s=300.0, clock="2026-01-01T00:00:00+00:00")
    r2 = sw.load_step(Twin(cfg, seed=1), hold_s=300.0, clock="2026-01-01T00:00:00+00:00")
    assert r1.to_dict() == r2.to_dict()
    assert r1.passed, [c for c in r1.criteria if not c.passed]
    assert {row["phase"] for row in r1.rows} >= {"load_20", "load_100"}
    assert r1.extra["levels"][-1]["load"] == 1.0


def test_failover_and_ride_through():
    cfg = Config.preset("ben20")
    f = sw.cooling_unit_failover(Twin(cfg, seed=0), fail_s=200.0, recover_s=100.0)
    assert f.passed and len(f.extra["units"]) == cfg.derived()["cooling_units_total"]
    r = sw.utility_loss_ride_through(Twin(cfg, seed=0))
    assert r.extra["minutes_to_ups_empty"] is not None
    assert r.extra["minutes_to_ashrae_max"] is not None
    assert "binding limit" in r.summary


def test_door_outdoor_filter():
    cfg = Config.preset("ben10")
    d = sw.door_open(Twin(cfg, seed=0), open_s=300.0)
    assert any(c.name == "door_alarm_raised" and c.passed for c in d.criteria)
    o = sw.outdoor_temperature_sweep(Twin(cfg, seed=0), hold_s=200.0, step_k=10.0)
    assert o.extra["points"][-1]["outdoor_c"] == 35
    fc = sw.filter_clog(Twin(cfg, seed=0), max_s=8000.0)
    assert fc.extra["alarm_after_s"] is not None


def test_run_sweep_and_csv(tmp_path):
    cfg = Config.preset("ben10")
    r = sw.run_sweep("door_open", cfg, open_s=120.0)
    p = tmp_path / "door.csv"
    sw.to_csv(r, str(p))
    with open(p) as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(r.rows) and "rack_inlet_c_1" in rows[0] and "phase" in rows[0]
    md = sw.report_markdown([r])
    assert "door_open" in md
    try:
        sw.run_sweep("nope", cfg)
        assert False
    except ValueError:
        pass
