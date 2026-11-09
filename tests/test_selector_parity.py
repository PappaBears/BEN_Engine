"""The website selector (JS) must produce the same sizing as config.py. Runs node if available."""
import json, shutil, subprocess, sys, os, pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.config import Config

PARITY_KEYS = ("cooling_units_total", "service_breaker_a", "service_amps_calc", "ups_kva_each", "ups_modules", "gross_kg", "payload_kg",
               "airflow_cfm", "controls_tier_resolved", "pods", "rows", "racks_per_row", "row_length_mm", "row_fits", "mv_service",
               "transformers_total", "transformer_kva", "generators_total", "generator_kw_each", "modules", "kind",
               "hardening", "hardening_recommended", "hardening_label", "envelope_area_m2", "battery_kwh", "total_kva")

def _node(script):
    return json.loads(subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout)

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

@needs_node
@pytest.mark.parametrize("tier,profile,climate,hardening", [
    ("ben5", "private_cloud", "hot_arid", None), ("ben30", "ai_inference", "temperate", None), ("ben150", "healthcare", "hot_humid", None),
    ("ben500", "ai_training", "cold", None), ("ben2000", "ai_training", "hot_arid", None), ("ben2000", "public_sector", "coastal", None),
    ("ben2000", "healthcare", "temperate", "H3"), ("ben150", "ai_inference", "temperate", "H3"), ("ben500", "private_cloud", "coastal", "H2"),
    # generation-1 alias keys still load and size identically
    ("ben20", "healthcare", "hot_humid", None), ("micro", "private_cloud", "temperate", None),
])
def test_parity(tier, profile, climate, hardening):
    cfg = Config.preset(tier, profile, climate, hardening)
    assert not cfg.validate()
    py = cfg.derived()
    hz = "null" if hardening is None else f"'{hardening}'"
    js = _node(f"""
    import {{derived, preset, validate}} from '{ROOT}/web/assets/selector.js';
    import fs from 'fs';
    const cat = JSON.parse(fs.readFileSync('{ROOT}/web/assets/catalog.json'));
    const cfg = preset('{tier}','{profile}','{climate}', cat, {hz});
    console.log(JSON.stringify({{cfg, d: derived(cfg, cat), errs: validate(cfg, cat)}}));
    """)
    assert js["errs"] == []
    assert js["cfg"]["tier"] == cfg.tier
    assert js["cfg"]["it_kw"] == cfg.it_kw and js["cfg"]["racks"] == cfg.racks and js["cfg"]["cooling"] == cfg.cooling
    assert js["cfg"]["hardening"] == cfg.hardening and js["cfg"]["generator"] == cfg.generator
    for k in PARITY_KEYS:
        assert js["d"][k] == py[k], (k, js["d"][k], py[k])
    assert abs(js["d"]["pue_estimate"] - py["pue_estimate"]) < 1e-6


# Rev 2: the JS port must size BEN 1 (both forms), the liquid-first BEN 300 / BEN 700 and the lineup exactly as config.py does
REV2_KEYS = PARITY_KEYS + ("lineup", "kw_per_rack", "kw_per_m2_footprint", "kw_per_m3_volume", "footprint_m2", "volume_m3", "pue_estimate")
MINI_KEYS = ("form", "noise_dba_est", "noise_dba_target", "noise_ok", "outlet_circuit", "outlet_circuit_a", "outlet_amps", "ups_va", "ups_w", "ups_model",
             "ups_runtime_min_est", "ups_battery_packs", "heat_to_room_w", "heat_to_room_btu_h", "closet_vent_cfm", "cooling_elec_kw", "ashrae_class", "total_kw")
DENSE_KEYS = ("row_items", "ups_frames", "ups_frames_n", "fancoils_total", "battery_cabinets", "battery_kwh_installed", "battery_minutes_installed",
              "swbd_sections", "panelboard_wall", "trim_loop_kw", "row_budget_mm", "nfpa_855_scope", "liquid_load")
# Rev 2 BEN 2000 cluster of BEN 700 modules (config.Config._derived_cluster, cluster_yard)
CLUSTER_KEYS = ("module_it_kw", "module_racks", "module_service_breaker_a", "module_total_kva", "module_gross_kg", "transformer_kva", "transformers_total",
                "transformer_loading_pct", "mv_service_amps", "mv_switchgear_ways", "site_area_m2", "yard_area_m2", "yard_pad_sqft", "yard_surface_m2",
                "lane_area_m2", "mv_feeder_m", "kw_per_m2_site", "kw_per_m2_yard", "kw_per_m2_module", "skids", "skid_rejection_kw_each", "water", "leak",
                "controls", "liquid_heat_kw", "loop_flow_lpm", "verified_max_kw", "module", "yard")


@needs_node
@pytest.mark.parametrize("tier,profile,climate,form,lineup", [
    ("ben1", "ai_inference", "temperate", "rack10", "rev2"), ("ben1", "ai_training", "temperate", "cab12", "rev2"),
    ("ben1", "healthcare", "hot_humid", None, "rev2"), ("ben1", "off_grid", "cold", None, "rev2"), ("ben1", "private_cloud", "temperate", "cab12", "rev2"),
    ("ben300", "ai_training", "temperate", None, "rev2"), ("ben300", "healthcare", "hot_humid", None, "rev2"), ("ben300", "public_sector", "coastal", None, "rev2"),
    ("ben700", "ai_training", "hot_arid", None, "rev2"), ("ben700", "private_cloud", "temperate", None, "rev2"), ("ben1000", "healthcare", "temperate", None, "rev2"),
    # carried tiers under both lineups (Rev 1 numbers are frozen; rev2 adds the density keys)
    ("ben150", "healthcare", "hot_humid", None, "rev1"), ("ben500", "ai_training", "cold", None, "rev2"), ("ben5", "private_cloud", "temperate", None, "rev1"),
    # BEN 2000: Rev 2 cluster of three BEN 700 modules (§2b), Rev 1 hall unchanged
    ("ben2000", "ai_training", "temperate", None, "rev2"), ("ben2000", "healthcare", "hot_arid", None, "rev2"), ("ben2000", "private_cloud", "coastal", None, "rev2"),
    ("ben2000", "off_grid", "cold", None, "rev2"), ("ben2000", "ai_training", "hot_arid", None, "rev1"), ("ben2000", "healthcare", "temperate", None, "rev1"),
])
def test_parity_rev2(tier, profile, climate, form, lineup):
    cfg = Config.preset(tier, profile, climate, lineup=lineup, form=form)
    assert not cfg.validate(), cfg.validate()
    py = json.loads(json.dumps(cfg.derived(), default=str))
    fm = "null" if form is None else f"'{form}'"
    js = _node(f"""
    import {{derived, preset, validate}} from '{ROOT}/web/assets/selector.js';
    import fs from 'fs';
    const cat = JSON.parse(fs.readFileSync('{ROOT}/web/assets/catalog.json'));
    const cfg = preset('{tier}','{profile}','{climate}', cat, null, '{lineup}', {fm});
    console.log(JSON.stringify({{cfg, d: derived(cfg, cat), errs: validate(cfg, cat)}}));
    """)
    assert js["errs"] == []
    for k in ("tier", "it_kw", "racks", "cooling", "redundancy", "hardening", "generator", "ups_minutes", "lineup", "form"):
        assert js["cfg"][k] == getattr(cfg, k), (k, js["cfg"][k], getattr(cfg, k))
    keys = REV2_KEYS if lineup == "rev2" else PARITY_KEYS
    keys = keys + (MINI_KEYS if py["kind"] == "minirack" else ()) + (DENSE_KEYS if py.get("liquid_first") else ()) + (CLUSTER_KEYS if py["kind"] == "cluster" else ())
    for k in keys:
        if k == "liquid_load":
            continue
        if k == "pue_estimate":
            assert abs(js["d"][k] - py[k]) < 1e-6
            continue
        assert js["d"].get(k) == py.get(k), (k, js["d"].get(k), py.get(k))
    if lineup == "rev1":
        assert "lineup" not in js["d"] and "lineup" not in py


@needs_node
def test_validate_rules_parity_rev2():
    """BEN 1 and liquid-first rules: the JS validator rejects what config.py rejects, rule for rule."""
    cases = [
        ("ben1", dict(form="rack10", it_kw=1.0)), ("ben1", dict(cooling="dlc_hd")), ("ben1", dict(hardening="H2")), ("ben1", dict(generator=True)),
        ("ben1", dict(redundancy="2N")), ("ben1", dict(controls_tier="pro")), ("ben1", dict(power_architecture="dc800")), ("ben1", dict(form="rack19")),
        ("ben300", dict(cooling="dlc_cdu")), ("ben300", dict(racks=1)), ("ben300", dict(controls_tier="lite")), ("ben700", dict(racks=7, it_kw=700.0)),
        ("ben700", dict(lineup="rev1")), ("ben150", dict(hardening="IND")), ("ben150", dict(controls_tier="mini")), ("ben30", dict(cooling="office_air")),
        # Rev 2 BEN 2000 cluster
        ("ben2000", dict(racks=14)), ("ben2000", dict(cooling="dlc_cdu")), ("ben2000", dict(it_kw=1000.0)), ("ben2000", dict(it_kw=2400.0, racks=15)),
        ("ben2000", dict(racks=12, it_kw=2000.0)), ("ben2000", dict(controls_tier="lite")), ("ben2000", dict(racks=48, cooling="dlc_cdu", it_kw=1600.0)),
    ]
    for tier, ch in cases:
        cfg = Config.preset(tier)
        for k, v in ch.items():
            setattr(cfg, k, v)
        py_errs = cfg.validate()
        assert py_errs, (tier, ch)
        js = _node(f"""
        import {{validate}} from '{ROOT}/web/assets/selector.js';
        import fs from 'fs';
        const cat = JSON.parse(fs.readFileSync('{ROOT}/web/assets/catalog.json'));
        console.log(JSON.stringify(validate({json.dumps(cfg.to_dict())}, cat)));
        """)
        assert len(js) == len(py_errs), (tier, ch, js, py_errs)


@needs_node
def test_controls_tier_override_parity():
    for tier, ct in (("ben30", "pro"), ("ben30", "lite"), ("ben5", "lite"), ("ben2000", "pro")):
        cfg = Config.preset(tier); cfg.controls_tier = ct
        assert not cfg.validate()
        assert cfg.derived()["controls_tier_resolved"] == ct
        js = _node(f"""
        import {{derived, preset, validate}} from '{ROOT}/web/assets/selector.js';
        import fs from 'fs';
        const cat = JSON.parse(fs.readFileSync('{ROOT}/web/assets/catalog.json'));
        const cfg = preset('{tier}','ai_inference','temperate', cat); cfg.controls_tier = '{ct}';
        console.log(JSON.stringify({{errs: validate(cfg, cat), ct: derived(cfg, cat).controls_tier_resolved}}));
        """)
        assert js["errs"] == [] and js["ct"] == ct
    cfg = Config.preset("ben500"); cfg.controls_tier = "lite"
    assert cfg.validate()


@needs_node
def test_validate_rules_parity():
    """Rule-for-rule: the JS validator rejects what config.py rejects (BEN 5 cooling, BEN 2000 DLC-only, hardening, Lite on big tiers)."""
    cases = [
        dict(tier="ben5", cooling="inrow_dx_300"), dict(tier="ben2000", cooling="rdhx_drycooler"), dict(tier="ben150", hardening="H9"),
        dict(tier="ben2000", controls_tier="lite"), dict(tier="ben30", cooling="cabinet_dx"), dict(tier="ben2000", racks=60),
    ]
    for c in cases:
        cfg = Config.preset(c["tier"])
        for k, v in c.items():
            setattr(cfg, k, v)
        py_errs = cfg.validate()
        assert py_errs, c
        js = _node(f"""
        import {{validate}} from '{ROOT}/web/assets/selector.js';
        import fs from 'fs';
        const cat = JSON.parse(fs.readFileSync('{ROOT}/web/assets/catalog.json'));
        console.log(JSON.stringify(validate({json.dumps(cfg.to_dict())}, cat)));
        """)
        assert len(js) == len(py_errs), (c, js, py_errs)
