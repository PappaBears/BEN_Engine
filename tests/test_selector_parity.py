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
