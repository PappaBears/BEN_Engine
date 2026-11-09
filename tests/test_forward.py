"""Forward architecture (docs/FORWARD_ARCHITECTURE_DECISION.md): 800 VDC option (dc800) and high-density liquid (dlc_hd).

Rules checked here: the options default off and change nothing already quoted; dc800 / dlc_hd are BEN 150+ only; the derived
sizing follows the stated assumptions; the BOM filters split the AC and DC chains; the twin, sweeps, commissioning and virtual
nodes carry the new sensors and faults; the forward prototype layout and drawings generate; the JS selector agrees with config.py.
"""
import json, math, os, shutil, subprocess, sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
sys.path.insert(0, os.path.join(ROOT, "design"))
from ben_engine.config import Config, TIER_GEOMETRY, TIERS_BY_LINEUP, PRESETS, COOLING_LIBRARY, POWER_ARCHITECTURES, DC_CONVENTIONS
from ben_engine.bom import load_catalog, generate_bom, totals, rule_variables
from ben_engine.twin import Twin
from ben_engine import sweeps as sw
from ben_engine import commissioning as cm
from ben_engine.sim_nodes import NodeFleet


def forward():
    cfg = Config.preset("ben150")
    cfg.power_architecture = "dc800"
    cfg.cooling = "dlc_hd"
    cfg.it_kw = 150.0
    cfg.racks = 2
    assert not cfg.validate()
    return cfg


# --------------------------------------------------------------------------- config
def test_options_default_off_and_presets_unchanged():
    for t in TIERS_BY_LINEUP["rev1"]:   # Rev 2 liquid-first tiers default to dlc_hd (tests/test_rev2_lineup.py)
        c = PRESETS[t]
        assert c.power_architecture == "ac480" and c.cooling != "dlc_hd" and c.dc_convention == "bipolar_400"
        d = c.derived()
        assert d["power_architecture"] == "ac480" and "dc_bus_current_a" not in d and "loop_flow_lpm" not in d
        assert d["dc_ready"] == (t in ("ben150", "ben500", "ben2000"))
    # the numbers the AC presets already quote (BEN 150 preset: 96 kW, 5 racks, RDHx)
    d = PRESETS["ben150"].derived()
    assert (d["ups_modules"], d["ups_kva_each"], d["battery_kwh"], d["service_breaker_a"]) == (2, 116, 17.8, 200)


def test_validation_rules():
    for t in ("ben5", "ben30"):
        c = Config.preset(t); c.power_architecture = "dc800"
        assert any("dc800" in e for e in c.validate()), t
        c = Config.preset(t); c.cooling = "dlc_hd"
        assert any("dlc_hd" in e for e in c.validate()), t
    c = Config.preset("ben2000"); c.cooling = "dlc_hd"
    assert not c.validate()
    c = Config.preset("ben500"); c.power_architecture = "dc800"; c.dc_convention = "unipolar_800"
    assert not c.validate() and c.derived()["dc_bus_v_pole"] == 800
    c.dc_convention = "sideways"
    assert any("dc_convention" in e for e in c.validate())
    c = Config.preset("ben150"); c.power_architecture = "dc400"
    assert any("power_architecture" in e for e in c.validate())


def test_forward_sizing_numbers():
    d = forward().derived()
    pa = POWER_ARCHITECTURES["dc800"]
    assert d["ups_modules"] == 0 and d["ups_kva_each"] == 0
    assert d["dc_bus_v_nominal"] == 800 and d["dc_window_v"] == [760, 920] and "assumption" in d["dc_window_basis"]
    assert d["dc_bus_v_pole"] == 400 and d["dc_convention"] == "bipolar_400" and "midpoint" in d["dc_grounding"]
    bus_kw = 150 / pa["rack_shelf_eff"]
    assert d["dc_bus_current_a"] == round(bus_kw * 1000 / 800 * 1.25) == 238
    assert d["dc_busway_a"] == 400
    assert d["ac_dc_front_end_kw"] == round((d["total_kw"] + bus_kw - 150) / pa["rectifier_eff"], 1)
    assert d["rectifier_modules_n"] == 2 and d["rectifier_modules"] == 3 and d["imd_count"] == 3 and d["rectifier_cabinets"] == 1
    assert d["rack_shelves_per_rack"] == 2 and d["rack_shelves_total"] == 4
    assert d["battery_on_bus_kwh"] == d["battery_kwh"] == 27.8 and d["battery_string_v"] == "800 V class"
    assert d["dc_loss_saving_kw"] == 4.5
    assert 40 < d["copper_saving_pct"] < 45 and d["copper_kg_dc_bus"] < d["copper_kg_ac_feeders"]
    assert d["pue_estimate"] == round(d["total_kw"] / 150 + d["dc_pue_loss_adder"], 3)
    # liquid loop: 90 % of 150 kW at ΔT 10 K
    assert d["liquid_heat_kw"] == 135.0 and d["heat_reuse_kw_available"] == 135.0
    assert d["loop_flow_lpm"] == round(135 / (4.18 * 10) * 60, 1) == 193.8
    assert d["loop_water_class"] == "W45" and d["cooling_units_total"] == 2 and d["row_fits"]
    assert d["airflow_cfm"] == 150 * 125 * 0.10
    # redundancy drives rectifier count
    c = forward(); c.redundancy = "2N"
    assert c.derived()["rectifier_modules"] == 4
    c.redundancy = "N"
    assert c.derived()["rectifier_modules"] == 2 and c.derived()["rack_shelves_per_rack"] == 1


def test_cli_json_exposes_dc_and_loop():
    out = subprocess.run([sys.executable, "-m", "ben_engine.config", "--tier", "ben150", "--power-architecture", "dc800", "--cooling", "dlc_hd",
                          "--it-kw", "150", "--racks", "2", "--dc-convention", "unipolar_800", "--json"], cwd=os.path.join(ROOT, "software"), capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
    j = json.loads(out.stdout)
    assert j["config"]["power_architecture"] == "dc800" and j["derived"]["dc_busway_a"] == 400 and j["derived"]["loop_flow_lpm"] == 193.8
    assert j["derived"]["dc_bus_v_pole"] == 800 and "isolated" in j["derived"]["dc_grounding"]
    cat = json.load(open(os.path.join(ROOT, "web/assets/catalog.json")))
    assert "dlc_hd" in cat["cooling"] and cat["power_architectures"]["dc800"]["tiers"][:3] == ["ben150", "ben500", "ben2000"]   # Rev 2 adds ben300, ben700
    assert set(cat["dc_conventions"]) == {"bipolar_400", "unipolar_800"}
    schema = json.load(open(os.path.join(ROOT, "spec/ben-config.schema.json")))
    assert schema["properties"]["power_architecture"]["enum"] == ["ac480", "dc800"] and "dlc_hd" in schema["properties"]["cooling"]["enum"]


# --------------------------------------------------------------------------- BOM
@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


def test_bom_power_and_cooling_filters(catalog):
    dc_codes = {p["code"] for p in catalog if p.get("applies_to_power") == ["dc800"]}
    ac_codes = {p["code"] for p in catalog if p.get("applies_to_power") == ["ac480"]}
    hd_codes = {p["code"] for p in catalog if p.get("applies_to_cooling") == ["dlc_hd"]}
    assert {"PWR-DC-RECT-100", "PWR-DC-BUSWAY", "PWR-DC-TAPOFF", "PWR-DC-IMD", "PWR-DC-AFD", "PWR-BATT-800V", "PWR-DC-RACK-BUS", "PWR-DC-SHELF-50V"} <= dc_codes
    assert {"PWR-UPS-GVS150", "PWR-BATT-LI", "PWR-XFMR", "PWR-PDU", "PWR-UPS-GVL500", "PWR-BATT-ROOM"} <= ac_codes
    assert {"CLG-CDU-HD", "CLG-MANIFOLD-HD", "CLG-DRYCOOLER-W45", "CLG-LEAK-RACK", "CLG-ISOVALVE-ROW", "CLG-HRX"} <= hd_codes
    # the AC presets never see a DC or dlc_hd line
    for t in TIERS_BY_LINEUP["rev1"]:
        codes = {r["code"] for r in generate_bom(PRESETS[t], catalog)}
        assert not codes & dc_codes and not codes & hd_codes, t
    rows = {r["code"]: r for r in generate_bom(forward(), catalog)}
    d = forward().derived()
    assert not set(rows) & ac_codes
    assert rows["PWR-DC-RECT-100"]["qty"] == d["rectifier_modules"] == 3
    assert rows["PWR-DC-IMD"]["qty"] == d["imd_count"]
    assert rows["PWR-DC-TAPOFF"]["qty"] == rows["PWR-DC-RACK-BUS"]["qty"] == rows["CLG-MANIFOLD-HD"]["qty"] == rows["CLG-LEAK-RACK"]["qty"] == 2
    assert rows["PWR-DC-SHELF-50V"]["qty"] == d["rack_shelves_total"] == 4
    assert rows["PWR-BATT-800V"]["qty"] == math.ceil(d["battery_on_bus_kwh"])
    assert rows["CLG-CDU-HD"]["qty"] == d["cooling_units_total"] == 2
    assert rows["CLG-HRX"]["qty"] == math.ceil(d["heat_reuse_kw_available"]) == 135
    assert rows["CLG-DRYCOOLER-W45"]["qty"] == math.ceil(d["liquid_heat_kw"] * 1.15)
    assert rows["CLG-AIR-RESID-HD"]["qty"] == 3
    for code in dc_codes | hd_codes:
        p = next(x for x in catalog if x["code"] == code)
        assert p["price_status"] == "estimate" and p["price_source_note"], code   # nothing in the forward chain is a quote
    t = totals(list(rows.values()))
    assert t["total_usd"] > 0 and t["by_status"]["estimate"] > 500_000
    v = rule_variables(forward())
    assert v["dc800"] == 1 and v["dlc_hd"] == 1 and v["heat_reuse_kw"] == 135.0 and v["rack_shelves_total"] == 4
    assert rule_variables(PRESETS["ben150"])["dc800"] == 0


def test_forward_bom_artifacts_exist_and_preset_bom_untouched():
    assert os.path.exists(os.path.join(ROOT, "purchasing/bom-ben150-dc800-dlchd.csv"))
    md = open(os.path.join(ROOT, "docs/BOM-ben150-forward.md"), encoding="utf-8").read()
    assert "800 VDC bus" in md and "PWR-DC-RECT-100" in md and "CLG-CDU-HD" in md and "PWR-UPS-GVS150" not in md
    preset_md = open(os.path.join(ROOT, "docs/BOM-ben150.md"), encoding="utf-8").read()
    assert "PWR-DC-" not in preset_md and "PWR-UPS-GVS150" in preset_md


# --------------------------------------------------------------------------- twin / sweeps / commissioning / nodes
def _settle(tw, s=600, load=1.0):
    tw.set_it_load(load)
    for _ in range(s):
        tw.step(1.0)
    return tw.state()


def test_twin_dc_bus_states_and_faults():
    tw = Twin(forward(), seed=0)
    st = _settle(tw)
    dc = st["dc"]
    assert 760 <= dc["v_bus"] <= 800 and abs(dc["v_bus_pos"] - dc["v_bus_neg"] - dc["v_bus"]) < 5 and abs(abs(dc["v_bus_neg"]) - dc["v_bus_pos"]) < 5
    assert dc["imd_kohm"] > 1000 and dc["ground_fault"] is False
    assert abs(dc["i_bus"] - st["it_kw"] / 0.985 / 0.995 * 1000 / dc["v_bus"]) < 3
    assert st["power"]["ups_kw"] > st["it_kw"]    # front-end input carries rectifier + shelf losses
    assert 1.0 < st["pue"] < 1.3
    tw.inject("dc_ground_fault", pole="neg")
    for _ in range(15):
        tw.step(1.0)
    st = tw.state()
    assert st["dc"]["imd_kohm"] < 100 and abs(st["dc"]["v_bus_neg"]) < 0.25 * st["dc"]["v_bus"]
    assert any(a["id"] == "dc_ground_fault" and a["sev"] == "critical" for a in st["alarms"])
    assert st["it_kw"] > 140                       # first fault alarms, does not trip
    tw.clear("dc_ground_fault")
    tw.inject("utility_loss")
    for _ in range(300):
        tw.step(1.0)
    st = tw.state()
    assert st["dc"]["on_battery"] and st["power"]["ups_soc_pct"] < 100 and 760 <= st["dc"]["v_bus"] <= 920
    tw.clear("utility_loss")
    tw.inject("dc_arc", rack=1)
    tw.step(1.0)
    st = tw.state()
    assert st["power"]["pdu_kw"][1] == 0.0 and st["dc"]["arc_tripped_rack"] == 2 and any(a["id"] == "dc_arc" for a in st["alarms"])
    tw.clear("dc_arc")
    tw.step(1.0)
    assert tw.state()["power"]["pdu_kw"][1] > 0


def test_twin_liquid_loop_pumps_and_leak_isolation():
    tw = Twin(forward(), seed=0)
    st = _settle(tw)
    lp = st["loop"]
    assert lp["water_class"] == "W45" and 38 <= lp["supply_c"] <= 45 and 8 <= lp["dt_k"] <= 12
    assert abs(lp["removed_kw"] - 135) < 2 and lp["heat_reuse_kw"] == lp["removed_kw"]
    assert len(lp["pumps"]) == 2 and sum(1 for p in lp["pumps"] if p["on"] and p["ok"]) == 1
    tw.inject("cdu_pump_fail", pump=0)
    for _ in range(30):
        tw.step(1.0)
    st = tw.state()
    assert st["loop"]["pumps"][0]["ok"] is False and st["loop"]["pumps"][1]["on"] and not st["loop"]["flow_low"]
    assert any(a["id"] == "cdu_pump1_fail" for a in st["alarms"])
    tw.clear("cdu_pump_fail", pump=0)
    tw.inject("leak")
    for _ in range(40):
        tw.step(1.0)
    st = tw.state()
    assert st["loop"]["leak_isolated"] and st["loop"]["leak_to_isolation_s"] == 8.0 and st["loop"]["flow_lpm"] < 10
    assert any(a["id"] == "loop_isolated" for a in st["alarms"])
    tw.clear("leak")
    tw.step(1.0)
    assert not tw.state()["loop"]["leak_isolated"]
    # faults that do not apply are refused
    with pytest.raises(ValueError):
        Twin(PRESETS["ben150"]).inject("dc_ground_fault")
    with pytest.raises(ValueError):
        Twin(PRESETS["ben150"]).inject("cdu_pump_fail")
    ids = {s.id for s in tw.sensors()}
    assert {"V_bus_pos", "V_bus_neg", "I_bus", "IMD_kohm", "T_loop_supply", "T_loop_return", "F_loop", "CDU_pump1", "CDU_pump2"} <= ids
    assert not {"V_bus_pos", "F_loop"} & {s.id for s in Twin(PRESETS["ben150"]).sensors()}


def test_forward_sweeps_pass_and_applicability():
    cfg = forward()
    assert sw.applicable("cdu_pump_failover", cfg) and sw.applicable("dc_ground_fault_response", cfg)
    assert not sw.applicable("cdu_pump_failover", PRESETS["ben150"]) and not sw.applicable("dc_ground_fault_response", PRESETS["ben150"])
    r = sw.run_sweep("cdu_pump_failover", cfg, fail_s=120.0, recover_s=60.0)
    assert r.passed, [c.name for c in r.criteria if not c.passed]
    assert len(r.extra["pumps"]) == 2
    r = sw.run_sweep("dc_ground_fault_response", cfg, hold_s=40.0)
    assert r.passed, [c.name for c in r.criteria if not c.passed]
    assert [p["pole"] for p in r.extra["poles"]] == ["pos", "neg"]
    with pytest.raises(ValueError):
        sw.run_sweep("dc_ground_fault_response", PRESETS["ben150"])
    names = [x.name for x in sw.run_all(PRESETS["ben30"])]
    assert "cdu_pump_failover" not in names and "dc_ground_fault_response" not in names


def test_forward_commissioning_runs_all_twelve_steps(tmp_path):
    cfg = forward()
    c = cm.Commissioning(cfg, sim=True, yes=True, seed=0, operator="QA", log=lambda m: None, fast=True, clock="2026-01-01T00:00:00+00:00")
    rep = c.run(str(tmp_path / "fwd.md"))
    assert [s.num for s in rep.steps] == list(range(1, 13))
    assert rep.passed, [(s.num, s.notes) for s in rep.steps if not s.passed]
    s6, s8, s10, s11 = rep.steps[5], rep.steps[7], rep.steps[9], rep.steps[10]
    assert "cdu_pump_failover" in s6.values and s6.values["cdu_pump_start"]
    assert s8.values["dc_bus_in_window"] and 760 <= s8.values["dc_bus_v_min_on_battery"]
    assert s10.values["leak_to_isolation_s"] == 8.0 and not s10.values.get("skipped")
    assert s11.values["imd_healthy_kohm"] > 500 and not s11.values.get("skipped")
    md = (tmp_path / "fwd.md").read_text()
    assert "800 VDC bus" in md and "W45" in md and "cdu_pump_failover" in md and "dc_ground_fault_response" in md


def test_sim_nodes_carry_dc_and_loop_channels():
    cfg = forward()
    tw = Twin(cfg, seed=1)
    _settle(tw, 30, 0.8)
    fl = NodeFleet(cfg, seed=1)
    room = fl.poll_all(tw.state())[0][1]["ch"]
    assert {"V_bus_pos", "V_bus_neg", "I_bus", "IMD_kohm", "dc_gf", "T_loop_sup", "T_loop_ret", "F_loop", "cdu_pump1", "cdu_pump2", "loop_iso"} <= set(room)
    assert room["dc_gf"] == 0 and room["loop_iso"] == 0 and room["V_bus_pos"] > 350 and room["F_loop"] > 50
    base = NodeFleet(PRESETS["ben150"], seed=1).poll_all(Twin(PRESETS["ben150"]).state())[0][1]["ch"]
    assert "V_bus_pos" not in base and "F_loop" not in base


# --------------------------------------------------------------------------- layout and drawings
def test_forward_layout_and_drawings_generate(tmp_path):
    import layout as L
    lay = L.resolve_config(L.forward_prototype_config())
    tags = [i.tag for i in lay.items]
    assert "RECT1" in tags and "BAT1" in tags and "CDU1" in tags and "CDU2" in tags and "HRX" in tags and "ISO1" in tags
    assert not any(t.startswith("UPS") for t in tags) and not any(t.startswith("CND") for t in tags)
    assert all(c.passed for c in lay.checks if c.id in ("I-C2", "I-C21", "I-C23", "I-C24", "I-C25", "I-C26")), [(c.id, c.result) for c in lay.checks]
    # the preset layouts are what they were
    for t in TIER_GEOMETRY:
        L.resolve(t)
    fwd = os.path.join(ROOT, "design/drawings/forward-ben150")
    for f in ("E-001.svg", "M-001.svg", "INDEX.md"):
        assert os.path.exists(os.path.join(fwd, f)), f
    e = open(os.path.join(fwd, "E-001.svg"), encoding="utf-8").read()
    assert "forward architecture" in e and "800 VDC" in e   # matplotlib keeps the text in XML comments; the title block wraps the status
    idx = open(os.path.join(fwd, "INDEX.md"), encoding="utf-8").read()
    assert "DC-002" in idx and "not for construction" in idx
    rev = json.load(open(os.path.join(ROOT, "design/REVISION.json")))
    assert any(e["id"] == "DC-002" for e in rev["change_register"]) and rev["drawing_rev"] == "C" and rev["checker"] == ""


# --------------------------------------------------------------------------- JS parity
@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_selector_parity_for_forward_options():
    cfg = forward()
    py = cfg.derived()
    script = f"""
    import {{derived, validate}} from '{ROOT}/web/assets/selector.js';
    import fs from 'fs';
    const cat = JSON.parse(fs.readFileSync('{ROOT}/web/assets/catalog.json'));
    const cfg = {json.dumps(cfg.to_dict())};
    const bad = {{...cfg, tier: 'ben30'}};
    console.log(JSON.stringify({{errs: validate(cfg, cat), d: derived(cfg, cat), badErrs: validate(bad, cat)}}));
    """
    js = json.loads(subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout)
    assert js["errs"] == []
    for k in ("dc_bus_current_a", "dc_busway_a", "rectifier_modules", "imd_count", "rack_shelves_total", "battery_on_bus_kwh", "ac_dc_front_end_kw",
              "dc_loss_saving_kw", "copper_saving_pct", "loop_flow_lpm", "heat_reuse_kw_available", "ups_modules", "gross_kg", "payload_kg",
              "airflow_cfm", "pue_estimate", "row_length_mm", "dc_bus_v_pole", "dc_convention", "cooling_units_total", "dc_ready"):
        assert js["d"][k] == py[k], (k, js["d"][k], py[k])
    assert len(js["badErrs"]) == len(Config.from_dict({**cfg.to_dict(), "tier": "ben30"}).validate()) >= 2
