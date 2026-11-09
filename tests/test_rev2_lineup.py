"""Rev 2 lineup (docs/REV2_DECISION.md §2): BEN 1 mini rack, liquid-first BEN 300 / BEN 700, lineup loading, density, BOM,
twin / sweeps / CFD / commissioning / proposal on the new tiers."""
import json
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))
sys.path.insert(0, str(ROOT / "design"))
sys.path.insert(0, str(ROOT / "scripts"))

from ben_engine.config import (CLUSTER_TIERS, Config, TIER_GEOMETRY, TIERS_BY_LINEUP, PROFILE_DEFAULTS, CLIMATE_DESIGN, PRESETS, PRESETS_REV1,  # noqa: E402
                               canonical_tier, DENSE_FOOTPRINTS, MINIRACK)
from ben_engine.bom import generate_bom, load_catalog, totals, rule_variables, eval_qty_rule  # noqa: E402
from ben_engine.twin import Twin  # noqa: E402
from ben_engine import sweeps as sw  # noqa: E402

REV2 = TIERS_BY_LINEUP["rev2"]
NEW = ("ben1", "ben300", "ben700")


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


# --------------------------------------------------------------------------- lineup and presets
def test_lineups_and_tier_lists():
    assert TIERS_BY_LINEUP["rev1"] == ["ben5", "ben30", "ben150", "ben500", "ben2000"]
    assert TIERS_BY_LINEUP["rev2"] == ["ben1", "ben5", "ben30", "ben150", "ben300", "ben500", "ben700", "ben2000"]
    assert list(PRESETS) == REV2 and list(PRESETS_REV1) == TIERS_BY_LINEUP["rev1"]
    assert all(c.lineup == "rev2" for c in PRESETS.values())


@pytest.mark.parametrize("tier", REV2)
def test_every_rev2_preset_is_valid_for_every_profile_and_climate(tier):
    for p in PROFILE_DEFAULTS:
        for c in CLIMATE_DESIGN:
            cfg = Config.preset(tier, p, c)
            assert not cfg.validate(), (tier, p, c, cfg.validate())
            d = cfg.derived()
            assert d["lineup"] == "rev2" and d["kw_per_rack"] > 0 and d["kw_per_m2_footprint"] > 0 and d["kw_per_m3_volume"] > 0


def test_alias_and_lineup_loading():
    assert canonical_tier("ben1000") == "ben700"
    assert Config.preset("ben1000").tier == "ben700"
    assert Config.from_dict({"tier": "ben1000", "it_kw": 700.0, "racks": 5, "cooling": "dlc_hd"}).tier == "ben700"
    # a saved dict without lineup: Rev 1 tier -> rev1, Rev 2-only tier -> rev2
    assert Config.from_dict({"tier": "ben150"}).lineup == "rev1"
    assert Config.from_dict({"tier": "ben1", "it_kw": 0.5, "racks": 1, "cooling": "office_air"}).lineup == "rev2"
    assert Config.from_dict(Config.preset("ben300").to_dict()).lineup == "rev2"
    assert Config().lineup == "rev2"
    for t in NEW:
        with pytest.raises(ValueError):
            Config.preset(t, lineup="rev1")
    # Rev 1 tiers in both lineups: same configuration, density keys only in rev2 (except BEN 2000: Rev 2 is the BEN 700 cluster, §2b)
    for t in [x for x in TIERS_BY_LINEUP["rev1"] if x not in CLUSTER_TIERS]:
        a, b = Config.preset(t, lineup="rev1"), Config.preset(t, lineup="rev2")
        da, db = a.derived(), b.derived()
        assert {k: v for k, v in db.items() if k in da} == da and "lineup" not in da and db["lineup"] == "rev2"


# --------------------------------------------------------------------------- BEN 1
def test_ben1_forms_and_sizing():
    r = Config.preset("ben1", "ai_inference")
    c = Config.preset("ben1", "ai_training")
    assert r.form == "rack10" and c.form == "cab12"
    dr, dc = r.derived(), c.derived()
    assert dr["kind"] == dc["kind"] == "minirack" and dr["controls_tier_resolved"] == "mini" and dr["pods"] == 2
    assert dr["hardening"] == "IND" and "UL 62368-1" in dr["hardening_rating"] and "IP20" in dr["hardening_rating"]
    assert dr["outlet_circuit_a"] == 15 and dr["ups_va"] == 1000 and dr["cooling_units_total"] == 1
    assert dc["ups_va"] == 2200 and dc["cooling_units_total"] == 2 and dc["noise_dba_est"] <= 45.0 and dc["noise_ok"]
    assert abs(dr["heat_to_room_btu_h"] - dr["heat_to_room_w"] * 3.412) <= 2   # both rounded from the same watts
    assert "room" in dr["room_cooling_note"]
    # form limits: 0.6 kW rack10, 1.5 kW cab12 on a 20 A circuit (16 A continuous)
    full = Config.preset("ben1", "ai_training"); full.it_kw = 1.5
    d = full.derived()
    assert not full.validate() and d["outlet_circuit_a"] == 20 and d["outlet_amps"] <= 16.0 and d["ups_w"] >= 1500 * 1.25
    assert not d["noise_ok"] and d["noise_quiet_up_to_kw"] < 1.5          # 1.5 kW is above the 45 dBA target: stated, not hidden
    bad = Config.preset("ben1", "ai_inference"); bad.it_kw = 0.8
    assert any("rack10" in e for e in bad.validate())
    over = Config.preset("ben1", "ai_training"); over.it_kw = 1.6
    assert over.validate()
    for k, v in (("cooling", "dlc_hd"), ("power_architecture", "dc800"), ("hardening", "H1"), ("generator", True), ("redundancy", "2N"), ("controls_tier", "pro")):
        x = Config.preset("ben1"); setattr(x, k, v)
        assert x.validate(), (k, v)
    assert Config.preset("ben1").geometry()["ext_l_m"] == TIER_GEOMETRY["ben1"]["forms"]["rack10"]["ext_l_m"]


def test_ben1_is_not_offered_elsewhere():
    for k, v in (("cooling", "office_air"), ("hardening", "IND"), ("controls_tier", "mini")):
        x = Config.preset("ben150"); setattr(x, k, v)
        assert x.validate(), (k, v)


# --------------------------------------------------------------------------- dense tiers and density
def test_dense_tiers_fit_with_real_footprints_and_names_follow_power():
    import layout as L
    for t, racks, kw in (("ben300", 2, 300), ("ben700", 5, 700)):
        cfg = Config.preset(t, "ai_training")
        assert cfg.racks == racks and cfg.it_kw == kw and cfg.cooling == "dlc_hd"
        d = cfg.derived()
        assert d["row_fits"] and d["row_length_mm"] <= TIER_GEOMETRY[t]["int_l_m"] * 1000
        lay = L.resolve(t, cfg=cfg)
        assert all(c.passed for c in lay.checks), [(c.id, c.formula) for c in lay.checks if not c.passed]
        assert {"I-D2", "I-D3", "I-D4", "I-D5", "I-D8"} <= {c.id for c in lay.checks}
    # the BEN 1000 target (7 racks, 1,000 kW) does not fit; 6 racks never beat 5
    t = Config(tier="ben700", profile="ai_training", it_kw=1000.0, racks=7, cooling="dlc_hd", ups_minutes=5)
    assert not t.derived()["row_fits"]
    from gen_density import max_fit
    assert max_fit("ben300", 2)[0] == 310 and max_fit("ben300", 3)[0] < 310
    assert max_fit("ben700", 5)[0] == 705 and max_fit("ben700", 6)[0] < 705 and max_fit("ben700", 7)[0] < 705


def test_density_monotonic_sanity():
    d = {t: Config.preset(t, "ai_training").derived() for t in REV2}
    assert d["ben300"]["kw_per_m2_footprint"] > d["ben150"]["kw_per_m2_footprint"]          # same 20 ft box, liquid-first
    assert d["ben700"]["kw_per_m2_footprint"] > d["ben500"]["kw_per_m2_footprint"]          # same 40 ft box
    assert d["ben700"]["kw_per_rack"] >= d["ben300"]["kw_per_rack"] * 0.9 > d["ben150"]["kw_per_rack"]
    assert d["ben700"]["kw_per_m3_volume"] > d["ben300"]["kw_per_m3_volume"] > d["ben30"]["kw_per_m3_volume"]
    assert d["ben300"]["kw_per_rack"] <= DENSE_FOOTPRINTS["rack"]["kw_max"]


def test_dense_validation_rules():
    c = Config.preset("ben300"); c.cooling = "dlc_cdu"
    assert any("liquid-first" in e for e in c.validate())
    c = Config.preset("ben300"); c.racks = 1
    assert any("GB300" in e for e in c.validate())
    c = Config.preset("ben700"); c.controls_tier = "lite"
    assert c.validate()
    c = Config.preset("ben700"); c.power_architecture = "dc800"
    assert not c.validate() and c.derived()["ups_frames"] == 0          # dc800 stays a study option, sized and fits


# --------------------------------------------------------------------------- BOM
@pytest.mark.parametrize("tier,form", [("ben1", "rack10"), ("ben1", "cab12"), ("ben300", None), ("ben700", None)])
def test_rev2_bom_totals_positive(catalog, tier, form):
    for p in PROFILE_DEFAULTS:
        cfg = Config.preset(tier, p, form=form)
        rows = generate_bom(cfg, catalog)
        t = totals(rows)
        assert t["total_usd"] > 0 and t["items"] >= 10, (tier, p)
        assert abs(sum(t["by_status"].values()) - t["total_usd"]) < 0.05
        v = rule_variables(cfg)
        for line in catalog:
            assert eval_qty_rule(line["qty_rule"], v) >= 0


def test_rev2_bom_lines_follow_the_design(catalog):
    rows = {r["code"]: r for r in generate_bom(Config.preset("ben700", "ai_training"), catalog)}
    d = Config.preset("ben700", "ai_training").derived()
    assert rows["CLG-CDU-HD"]["qty"] == d["cooling_units_total"] == 3
    assert rows["CLG-FANCOIL-CW20"]["qty"] == d["fancoils_total"]
    assert rows["PWR-UPS-GVL500"]["qty"] == d["ups_frames"] == 2
    assert rows["PWR-BATT-LI"]["qty"] == d["battery_cabinets"] == 4
    assert rows["PWR-SWBD-SECTION"]["qty"] == d["swbd_sections"] == 1
    assert rows["CMP-GB300-NVL72"]["qty"] == rows["STR-RACK-MGX"]["qty"] == 5
    assert "PWR-PDU" not in rows and "CLG-AIR-RESID-HD" not in rows and "STR-RACK48" not in rows
    mini = {r["code"] for r in generate_bom(Config.preset("ben1", "ai_inference"), catalog)}
    assert {"STR-MINIRACK-10", "PWR-UPS-MINI-1000", "CMP-AI-DGXSPARK", "CTL-POD", "CTL-EDGE-MINI"} <= mini
    assert not {"STR-MINICAB-12", "FS-CLEAN-AGENT", "SITE-PAD", "STR-CONT20"} & mini
    cab = {r["code"] for r in generate_bom(Config.preset("ben1", "ai_training"), catalog)}
    assert {"STR-MINICAB-12", "PWR-UPS-MINI-2200", "CMP-AI-2U-RTXPRO", "CMP-NAS-RS422", "CTL-DOOR-MINI"} <= cab


def test_rev2_outputs_written():
    for t in REV2:
        assert (ROOT / "purchasing" / "rev2" / f"bom-{t}.csv").exists(), t
        assert (ROOT / "docs" / "rev2" / f"BOM-{t}.md").exists(), t
    for f in ("docs/rev2/BOM.md", "docs/rev2/UNIT_ECONOMICS.md", "web/assets/pricing-rev2.json", "docs/DENSITY.md"):
        assert (ROOT / f).exists(), f
    pr = json.loads((ROOT / "web/assets/pricing-rev2.json").read_text())
    assert set(pr) == set(REV2)
    for t in NEW:
        assert list((ROOT / "docs/proposals/rev2").glob(f"sample-{t}-*.md")), t
    assert (ROOT / "docs/proposals/rev2/sample-ben150-healthcare.md").exists()


def test_density_doc_is_current():
    import gen_density
    assert (ROOT / "docs" / "DENSITY.md").read_text(encoding="utf-8") == gen_density.build()


# --------------------------------------------------------------------------- twin, sweeps, CFD, commissioning, proposal
@pytest.mark.parametrize("tier,profile,form", [("ben1", "ai_inference", "rack10"), ("ben1", "ai_training", "cab12"), ("ben1", "healthcare", "cab12"),
                                               ("ben300", "ai_training", None), ("ben300", "healthcare", None), ("ben700", "ai_training", None),
                                               ("ben700", "public_sector", None)])
def test_sweeps_pass_on_rev2_presets(tier, profile, form):
    cfg = Config.preset(tier, profile, form=form)
    res = sw.run_all(cfg, clock="2026-11-09T00:00:00+00:00")
    assert res and all(r.passed for r in res), [(r.name, [c.name for c in r.criteria if not c.passed]) for r in res if not r.passed]
    names = {r.name for r in res}
    if form == "rack10":
        assert not {"door_open", "cooling_unit_failover", "filter_clog"} & names
    if tier != "ben1":
        assert "cdu_pump_failover" in names


def test_ben1_twin_faults_and_alarms():
    tw = Twin(Config.preset("ben1", "ai_inference"))
    assert set(tw.applicable_faults()) == {"utility_loss", "sensor_drift"}
    with pytest.raises(ValueError, match="no door"):
        tw.inject("door_open")
    tc = Twin(Config.preset("ben1", "ai_training"))
    assert {"door_open", "cooling_unit_fail", "filter_clog"} <= set(tc.applicable_faults()) and "leak" not in tc.applicable_faults()
    tc.set_it_load(1.0); tc.p.office_room_ua_w_k = 40.0         # a closed closet: the room cannot take the heat
    for _ in range(3600):
        tc.step(1.0)
    st = tc.state()
    assert "mini" in st and {"room_hot"} <= {a["id"] for a in st["alarms"]}
    loud = Config.preset("ben1", "ai_training"); loud.it_kw = 1.5
    tl = Twin(loud); tl.inject("door_open"); tl.set_it_load(1.0)
    for _ in range(120):
        tl.step(1.0)
    assert "noise_high" in {a["id"] for a in tl.state()["alarms"]}


@pytest.mark.parametrize("tier,form", [("ben1", "rack10"), ("ben1", "cab12"), ("ben300", None), ("ben700", None)])
def test_cfd_runs_within_60_s(tier, form):
    from ben_engine.cfd import run_cfd
    t0 = time.perf_counter()
    m = run_cfd(Config.preset(tier, "ai_training", form=form))
    assert time.perf_counter() - t0 < 60 and m["max_rack_inlet_c"] > 0


@pytest.mark.parametrize("tier,form", [("ben1", "rack10"), ("ben1", "cab12"), ("ben700", None)])
def test_commissioning_sim_passes_and_skips_with_reasons(tmp_path, tier, form):
    from ben_engine.commissioning import Commissioning
    cfg = Config.preset(tier, "ai_training", form=form)
    rep = Commissioning(cfg, sim=True, yes=True, fast=True, log=lambda m: None, clock="2026-11-09T00:00:00+00:00").run(str(tmp_path / "r.md"))
    assert rep.passed, [(s.num, s.notes) for s in rep.steps if not s.passed]
    text = (tmp_path / "r.md").read_text()
    if tier == "ben1":
        assert "not applicable" in text and "liquid loop" in text
    if form == "rack10":
        assert "no door" in text and "no extraction fans" in text


def test_proposals_for_new_tiers():
    from ben_engine.proposal import build_proposal, to_markdown, CONTROLS_LICENCE_PER_UNIT_YR, STORAGE_FEE_PER_DAY
    for t in REV2:
        assert t in CONTROLS_LICENCE_PER_UNIT_YR and t in STORAGE_FEE_PER_DAY
    p = build_proposal(Config.preset("ben1", "ai_inference"), date="2026-11-09")
    crit = [m for m in p.milestones if m["path"] == "critical"]
    assert crit[-1]["week"] <= 3 and "handover" in crit[-1]["milestone"].lower()
    md = to_markdown(p)
    assert "Site acceptance test" not in md.split("## 12")[1].split("## 13")[0] or "burn-in" in md
    assert abs(sum(x["share"] for x in p.payment_milestones) - 1.0) < 1e-9 and all(x["week"] is not None for x in p.payment_milestones)
    for t in ("ben300", "ben700"):
        q = build_proposal(Config.preset(t, "ai_training"), date="2026-11-09")
        assert q.milestones[-1]["week"] >= 26 and q.headline.capital_price_usd > 0


def test_catalog_json_carries_rev2_for_the_selector():
    cat = json.loads((ROOT / "web/assets/catalog.json").read_text())
    assert cat["tiers_by_lineup"]["rev2"] == REV2 and "office_air" in cat["cooling"] and "mini" in cat["controls_tiers"]
    assert set(cat["tiers"]["ben1"]["forms"]) == {"rack10", "cab12"} and cat["tier_aliases"]["ben1000"] == "ben700"
    assert cat["dense_footprints"]["rack"]["d"] == 1068 and cat["minirack"]["ups_models"] == MINIRACK["ups_models"]
