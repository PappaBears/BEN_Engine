"""Digital twin: determinism, physics sanity, faults and the CFD recirculation hook."""
import math

from ben_engine.config import Config, TIER_GEOMETRY
from ben_engine.twin import Twin, TwinParams, run_profile


def _settle(tw, s=1800, load=1.0):
    tw.set_it_load(load)
    for _ in range(s):
        tw.step(1.0)
    return tw.state()


def test_deterministic_same_seed():
    a = run_profile(Config.preset("ben150"), seconds=120, seed=3)
    b = run_profile(Config.preset("ben150"), seconds=120, seed=3)
    assert a[-1] == b[-1]


def test_all_tiers_build_and_step():
    for t in TIER_GEOMETRY:
        tw = Twin(Config.preset(t), seed=1)
        s = _settle(tw, 300, 0.8)
        assert len(s["rack_inlet_c"]) == tw.cfg.racks
        assert all(math.isfinite(x) for x in s["rack_inlet_c"])
        assert s["pue"] is not None and 1.0 < s["pue"] < 2.5


def test_energy_balance_rack_delta_t():
    """Rack ΔT at full load must be close to the design 12 K scaled by flow (it is ~14 K in the twin)."""
    tw = Twin(Config.preset("ben150"), seed=0)
    s = _settle(tw)
    dT = sum(s["rack_outlet_c"]) / len(s["rack_outlet_c"]) - sum(s["rack_inlet_c"]) / len(s["rack_inlet_c"])
    assert 8.0 < dT < 20.0


def test_utility_loss_drains_ups_and_heats_racks():
    tw = Twin(Config.preset("ben150"), seed=0)
    s0 = _settle(tw)
    tw.inject("utility_loss")
    for _ in range(600):
        tw.step(1.0)
    s = tw.state()
    assert s["power"]["ups_on_battery"] is True
    assert s["power"]["ups_soc_pct"] < s0["power"]["ups_soc_pct"]
    assert max(s["rack_inlet_c"]) > max(s0["rack_inlet_c"]) + 5.0
    assert any(a["id"] == "utility_loss" for a in s["alarms"])


def test_cooling_unit_failover_starts_standby():
    tw = Twin(Config.preset("ben150"), seed=0)
    _settle(tw, 600)
    n_needed = tw.d["cooling_units_n"]
    tw.inject("cooling_unit_fail", unit=0)
    for _ in range(120):
        tw.step(1.0)
    s = tw.state()
    assert sum(1 for u in s["cooling_units"] if u["on"] and u["ok"]) >= n_needed
    assert s["cooling_units"][0]["ok"] is False


def test_recirculation_profile_hook_changes_inlets():
    """TwinParams.recirculation_profile (CFD output) overrides the scalar + position bias."""
    cfg = Config.preset("ben150")
    base = _settle(Twin(cfg, params=TwinParams(), seed=0))
    prof = TwinParams(recirculation_profile=[0.4, 0.0, 0.0, 0.0, 0.0])
    s = _settle(Twin(cfg, params=prof, seed=0))
    assert s["rack_inlet_c"][0] > base["rack_inlet_c"][0] + 2.0
    assert abs(s["rack_inlet_c"][1] - s["supply_c"]) < 0.5


def test_sensor_specs_cover_nodes():
    tw = Twin(Config.preset("ben150"))
    ids = [s.id for s in tw.sensors()]
    assert "dP_aisle" in ids and "T_supply" in ids and len(ids) > 4 * tw.cfg.racks


def test_ben2000_twin_rows_and_sensors():
    """BEN 2000 hall: 40-48 racks placed in `rows` rows across the interior width, nodes per two racks, room sensors per module."""
    cfg = Config.preset("ben2000", "ai_inference")
    d = cfg.derived()
    tw = Twin(cfg, seed=0)
    assert cfg.racks == 48 and d["rows"] == 4
    pos = tw.rack_positions()
    ys = sorted({round(y, 3) for _, y in pos})
    assert len(ys) == 4 and all(abs(y) < d["geometry"]["int_w_m"] / 2 for y in ys)
    xs = [x for x, _ in pos]
    assert 0 < min(xs) and max(xs) < d["geometry"]["int_l_m"]
    sens = tw.sensors()
    ids = {s.id for s in sens}
    assert len([s for s in sens if s.id.startswith("T_in_r")]) == 3 * cfg.racks
    assert {"RH_room_m1", "RH_room_m2", "RH_room_m3", "leak_floor_m3", "dP_aisle_m2"} <= ids
    nodes = {s.node for s in sens if s.kind == "temperature" and s.id.startswith("T_")} - {"node1"}
    assert len(nodes) >= cfg.racks // 2 - 1
    states = run_profile(cfg, seconds=300, seed=1)
    st = states[-1]
    assert len(st["rack_inlet_c"]) == cfg.racks and len(st["power"]["pdu_kw"]) == cfg.racks
    assert max(st["rack_inlet_c"]) < 35
    assert st["pue"] is not None and 1.05 < st["pue"] < 1.4


def test_filter_clog_on_liquid_cooling_only_derates_the_air_side():
    cfg = Config.preset("ben2000")
    tw = Twin(cfg, seed=0); tw.set_it_load(1.0)
    for _ in range(300): tw.step(5.0)
    tw.inject("filter_clog")
    for _ in range(600): tw.step(5.0)
    st = tw.state()
    assert max(st["rack_inlet_c"]) < 35, st["rack_inlet_c"][:4]
