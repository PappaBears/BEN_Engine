"""The website selector (JS) must produce the same sizing as config.py. Runs node if available."""
import json, shutil, subprocess, sys, os, pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.config import Config

@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
@pytest.mark.parametrize("tier,profile,climate", [("micro","private_cloud","hot_arid"),("ben10","ai_inference","temperate"),("ben20","healthcare","hot_humid"),("ben40","ai_training","cold")])
def test_parity(tier, profile, climate):
    cfg = Config.preset(tier, profile, climate)
    py = cfg.derived()
    script = f"""
    import {{derived, preset}} from '{ROOT}/web/assets/selector.js';
    import fs from 'fs';
    const cat = JSON.parse(fs.readFileSync('{ROOT}/web/assets/catalog.json'));
    const cfg = preset('{tier}','{profile}','{climate}', cat);
    console.log(JSON.stringify({{cfg, d: derived(cfg, cat)}}));
    """
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout
    js = json.loads(out)
    assert js["cfg"]["it_kw"] == cfg.it_kw and js["cfg"]["racks"] == cfg.racks and js["cfg"]["cooling"] == cfg.cooling
    for k in ("cooling_units_total","service_breaker_a","ups_kva_each","ups_modules","gross_kg","airflow_cfm","controls_tier_resolved","pods"):
        assert js["d"][k] == py[k], (k, js["d"][k], py[k])
    assert abs(js["d"]["pue_estimate"] - py["pue_estimate"]) < 1e-6


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_controls_tier_override_parity():
    for tier, ct in (("ben10", "pro"), ("ben10", "lite"), ("micro", "lite")):
        cfg = Config.preset(tier); cfg.controls_tier = ct
        assert not cfg.validate()
        assert cfg.derived()["controls_tier_resolved"] == ct
        script = f"""
        import {{derived, preset, validate}} from '{ROOT}/web/assets/selector.js';
        import fs from 'fs';
        const cat = JSON.parse(fs.readFileSync('{ROOT}/web/assets/catalog.json'));
        const cfg = preset('{tier}','ai_inference','temperate', cat); cfg.controls_tier = '{ct}';
        console.log(JSON.stringify({{errs: validate(cfg, cat), ct: derived(cfg, cat).controls_tier_resolved}}));
        """
        js = json.loads(subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout)
        assert js["errs"] == [] and js["ct"] == ct
    cfg = Config.preset("ben40"); cfg.controls_tier = "lite"
    assert cfg.validate()
