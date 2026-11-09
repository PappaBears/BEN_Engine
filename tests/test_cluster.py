"""Rev 2 BEN 2000 = three BEN 700 modules on a shared yard (docs/REV2_DECISION.md §2b).

The Rev 1 BEN 2000 hall stays exactly as built for lineup "rev1" (tests/test_rev1_frozen.py pins its numbers); lineup "rev2" loads the cluster:
every module is a stand-alone BEN 700 (same sizing, same layout resolver, same BOM lines) and the yard adds the 12.47 kV service, one pad-mount
transformer and one heat-rejection skid per module, checked by design/layout.py I-K1..I-K24.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))
sys.path.insert(0, str(ROOT / "design"))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))

from ben_engine.config import Config, CLUSTER_TIERS, CLUSTER_YARD, PROFILE_DEFAULTS, CLIMATE_DESIGN, TIERS_BY_LINEUP, TIER_GEOMETRY  # noqa: E402
from ben_engine.bom import generate_bom, load_catalog, totals, rule_variables, eval_qty_rule  # noqa: E402
from ben_engine import proposal as P  # noqa: E402
import layout as L  # noqa: E402

FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "rev1_presets.json").read_text())


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


def test_rev2_ben2000_preset_is_three_ben700_modules():
    c = Config.preset("ben2000")
    assert not c.validate() and c.lineup == "rev2" and c.is_cluster() and CLUSTER_TIERS == ("ben2000",)
    assert (c.it_kw, c.racks, c.cooling, c.redundancy, c.generator) == (2000.0, 15, "dlc_hd", "N+1", False)
    d = c.derived()
    assert d["kind"] == "cluster" and d["modules"] == 3 and d["module_tier"] == "ben700" and d["rows"] == 3 and d["racks_per_row"] == 5
    assert d["module_racks"] == 5 and d["module_it_kw"] == pytest.approx(666.67) and d["kw_per_rack"] == pytest.approx(133.33)
    assert 132 <= d["kw_per_rack"] <= TIER_GEOMETRY["ben700"]["max_rack_kw"]          # GB300 NVL72-class band
    m = c.module_config()
    assert m.tier == "ben700" and not m.validate() and m.it_kw <= TIER_GEOMETRY["ben700"]["it_kw_max"]
    md = m.derived()
    # sums over the modules, per-module keys unchanged
    assert d["cooling_units_total"] == 3 * md["cooling_units_total"] == 9 and d["ups_frames"] == 3 * md["ups_frames"] == 6
    assert d["battery_cabinets"] == 12 and d["pods"] == c.racks * 2 + 2 * 3 and d["gross_kg"] == 3 * md["gross_kg"]
    assert d["row_items"] == md["row_items"] and d["row_fits"] and d["service_breaker_a"] == md["service_breaker_a"] == 1200
    # yard: MV service, one transformer per module, 4-way switchgear, one skid per module
    assert d["mv_service"] and d["mv_kv"] == 12.47 and d["transformers_total"] == 3 and d["transformer_kva"] == 1000
    assert d["module_total_kva"] <= CLUSTER_YARD["xfmr_loading_max"] * d["transformer_kva"] and d["skids"] == 3
    assert d["mv_switchgear_ways"] >= 1 + d["modules"] and d["mv_service_amps"] < d["mv_switchgear_a"]
    assert d["verified_max_kw"] == 3 * 705 and c.it_kw <= d["verified_max_kw"]
    assert {"water", "leak", "controls", "yard"} <= set(d) and "supervisory" in d["controls"]


def test_cluster_density_module_and_site():
    d = Config.preset("ben2000", "ai_training").derived()
    hall = Config.preset("ben2000", "ai_training", lineup="rev1").derived()
    b700 = Config.preset("ben700", "ai_training").derived()
    assert d["kw_per_m2_footprint"] == pytest.approx(2000 / (3 * 12.192 * 2.438), abs=0.01)
    assert d["kw_per_m2_footprint"] > 5 * 3.97                                  # the Rev 1 hall preset is 3.97 kW/m2 of hall footprint
    assert d["kw_per_m2_footprint"] == d["kw_per_m2_module"] and d["kw_per_m2_footprint"] < b700["kw_per_m2_footprint"]   # 666.7 kW < 700 kW per module
    assert d["footprint_m2"] < d["yard_area_m2"] < d["site_area_m2"]
    assert d["kw_per_m2_footprint"] > d["kw_per_m2_yard"] > d["kw_per_m2_site"] > 0
    assert hall["kind"] == "hall" and "kw_per_m2_site" not in hall


@pytest.mark.parametrize("profile", list(PROFILE_DEFAULTS))
def test_cluster_presets_valid_for_every_profile(profile):
    c = Config.preset("ben2000", profile)
    assert not c.validate(), c.validate()
    assert c.racks % 3 == 0 and TIER_GEOMETRY["ben700"]["it_kw_min"] * 3 <= c.it_kw <= 2000
    if PROFILE_DEFAULTS[profile]["redundancy"] == "2N":
        assert c.it_kw < 1600 and c.generator


def test_every_module_passes_the_dense_checks_and_the_yard_has_no_fail():
    lay = L.resolve_rev2("ben2000")
    assert lay.is_cluster and len(lay.notes["module_layouts"]) == 3
    ids = {c.id for c in lay.checks}
    assert {"I-K1.1", "I-K1.2", "I-K1.3", "I-K2", "I-K3", "I-K7", "I-K11", "I-K12", "I-K13", "I-K14", "I-K17", "I-K18", "I-K20"} <= ids
    assert not [c for c in lay.checks if c.failed], [(c.id, c.formula) for c in lay.checks if c.failed]
    assert {c.id for c in lay.checks if c.result == "STUDY"} == {"I-K6", "I-K11"}
    for ml in lay.notes["module_layouts"]:
        assert ml.is_dense and all(c.passed for c in ml.checks) and {"I-D2", "I-D3", "I-D4", "I-D5", "I-D20"} <= {c.id for c in ml.checks}
    # yard items in site coordinates: three modules, three transformers, switchgear; module contents carried with a module prefix
    tags = {i.tag for i in lay.items}
    assert {"M1", "M2", "M3", "T1", "T2", "T3", "SWGR", "LANE-W", "LANE-E", "FENCE", "M1-R1", "M3-R5", "M2-DC1"} <= tags
    assert len([i for i in lay.items if i.kind == "rack"]) == 15


@pytest.mark.parametrize("profile,climate", [("healthcare", "hot_arid"), ("off_grid", "cold"), ("public_sector", "coastal"), ("private_cloud", "temperate")])
def test_yard_checks_hold_across_profiles_and_climates(profile, climate):
    lay = L.resolve_rev2("ben2000", profile=profile, climate=climate)
    assert not [c for c in lay.checks if c.failed], [(c.id, c.formula) for c in lay.checks if c.failed]
    if lay.cfg.generator:
        assert "I-K24" in {c.id for c in lay.checks} and {"G1", "G2", "G3"} <= {i.tag for i in lay.items}


def test_cluster_validation_rules():
    for k, v in (("racks", 14), ("cooling", "dlc_cdu"), ("it_kw", 1000.0), ("it_kw", 2400.0), ("controls_tier", "lite")):
        c = Config.preset("ben2000"); setattr(c, k, v)
        assert c.validate(), (k, v)
    c = Config.preset("ben2000"); c.racks, c.it_kw = 12, 2000.0                # 166.7 kW per rack: above the GB300-class 155 kW
    assert any("GB300" in e for e in c.validate())
    # a Rev 1 hall configuration only loads as the hall under lineup rev1
    hall = Config.preset("ben2000", lineup="rev1").to_dict()
    assert not Config.from_dict(hall).validate()
    assert Config.from_dict({**hall, "lineup": "rev2"}).validate()


def test_rev1_ben2000_hall_unchanged():
    for key in ("ben2000|ai_inference|temperate", "ben2000|ai_training|hot_arid", "ben2000|healthcare|temperate"):
        t, p, cl = key.split("|")
        c = Config.preset(t, p, cl, lineup="rev1")
        assert json.loads(json.dumps(c.derived(), sort_keys=True, default=str)) == FIXTURE["derived"][key], key
        assert round(totals(generate_bom(c))["total_usd"], 2) == FIXTURE["bom"][key]["total_usd"], key
    saved = dict(FIXTURE["config"]["ben2000|ai_inference|temperate"])
    c = Config.from_dict(saved)
    assert c.lineup == "rev1" and not c.is_cluster() and c.derived()["kind"] == "hall" and c.geometry() is TIER_GEOMETRY["ben2000"]
    lay = L.resolve("ben2000")
    assert lay.is_hall and {"I-H0", "I-H20"} <= {x.id for x in lay.checks} and all(x.passed for x in lay.checks)
    assert TIERS_BY_LINEUP["rev1"][-1] == "ben2000" and "kind" in TIER_GEOMETRY["ben2000"] and TIER_GEOMETRY["ben2000"]["kind"] == "hall"


def test_cluster_bom_is_three_modules_plus_yard(catalog):
    c = Config.preset("ben2000")
    rows = {r["code"]: r for r in generate_bom(c, catalog)}
    mod = {r["code"]: r for r in generate_bom(c.module_config(), catalog)}
    for code, r in mod.items():
        assert rows[code]["qty"] >= 3 * r["qty"], code
    assert rows["CMP-GB300-NVL72"]["qty"] == rows["STR-RACK-MGX"]["qty"] == 15 and rows["CLG-CDU-HD"]["qty"] == 9 and rows["PWR-UPS-GVL500"]["qty"] == 6
    assert rows["PWR-MV-XFMR-1000"]["qty"] == 3 and rows["PWR-MV-SWGR-3FI"]["qty"] == 1 and rows["SITE-MV-INTERCONNECT"]["qty"] == 1
    assert rows["PWR-MV-FEEDER"]["qty"] == pytest.approx(c.derived()["mv_feeder_m"], abs=1) and rows["CTL-PLC"]["qty"] == 3 * mod["CTL-PLC"]["qty"] + 1
    # none of the Rev 1 hall lines
    assert not {"STR-MODULE-WB", "STR-MODULE-PWR", "PWR-MV-XFMR-2500", "PWR-LV-SWGR-4000", "CLG-FANWALL", "PWR-GEN-1250", "PWR-BATT-ROOM", "CLG-CDU"} & set(rows)
    t, tm = totals(list(rows.values())), totals(list(mod.values()))
    yard = t["total_usd"] - 3 * tm["total_usd"]
    assert 0 < yard < 0.05 * t["total_usd"]
    assert {r["scope"] for r in rows.values()} and all(r.get("scope") for r in rows.values())
    # every yard-only line is an estimate with its basis; every qty rule evaluates on every configuration
    for p in catalog:
        if p.get("applies_to_lineups") == ["rev2"] and "ben2000" in p["applies_to_tiers"]:
            assert p["price_status"] == "estimate" and p["price_source_note"] and p.get("lead_time_weeks"), p["code"]
    for cfg in (c, Config.preset("ben2000", lineup="rev1"), Config.preset("ben700")):
        v = rule_variables(cfg)
        for p in catalog:
            assert eval_qty_rule(p["qty_rule"], v) >= 0
            if "cluster_qty_rule" in p:
                assert eval_qty_rule(p["cluster_qty_rule"], v) >= 0


def test_pricing_page_agrees_with_the_bom_and_the_proposals():
    """web/assets/pricing-rev2.json (scripts/unit_economics.py --lineup rev2) is the BOM / margin source the proposals use: the page price of
    every Rev 2 preset equals the proposal capital price of that preset, and the Rev 2 sample proposals are current."""
    pr = json.loads((ROOT / "web" / "assets" / "pricing-rev2.json").read_text())
    assert set(pr) == set(TIERS_BY_LINEUP["rev2"])
    for t in TIERS_BY_LINEUP["rev2"]:
        cfg = Config.preset(t, lineup="rev2")
        page = sum(s["total"] for s in pr[t]["by_subsystem"].values())
        prop = P.build_proposal(cfg, option="hardware_controls", customer="Test Co", site="Nowhere", date="2026-11-09").headline.capital_price_usd
        assert page == pytest.approx(prop, abs=0.5), (t, page, prop)
        assert pr[t]["preset_it_kw"] == cfg.it_kw and pr[t]["racks"] == cfg.racks
    assert pr["ben2000"]["kind"] == "cluster" and pr["ben2000"]["modules"] == 3 and pr["ben2000"]["yard_cost_usd"] > 0
    for f in sorted((ROOT / "docs" / "proposals" / "rev2").glob("sample-*.json")):
        p = json.loads(f.read_text())
        cfg = Config.from_dict(p["config"]); cfg.subsystems = p["headline"]["subsystems"]
        cap = round(totals(generate_bom(cfg))["total_usd"] / (1 - P.MARGIN_HW), 2)
        assert cap == p["headline"]["capital_price_usd"], f.name
        pre = Config.preset(cfg.tier, lineup="rev2", form=cfg.form or None)
        same = all(getattr(cfg, k) == getattr(pre, k) for k in ("it_kw", "racks", "cooling", "redundancy", "climate", "hardening", "generator", "ups_minutes", "form"))
        if same and p["headline"]["key"] == "hardware_controls":
            assert round(sum(s["total"] for s in pr[cfg.tier]["by_subsystem"].values())) == round(p["headline"]["capital_price_usd"]), f.name


def test_cluster_proposal_builds_with_the_site_schedule():
    p = P.build_proposal(Config.preset("ben2000"), option="hardware_controls", customer="Test Co", site="Nowhere", date="2026-11-09")
    setdown = next(m for m in p.milestones if "H18" in m["hold"])
    assert "pad-mount transformers" in setdown["milestone"] and p.headline.capital_price_usd > 0
