import os, sys, zipfile, pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.config import Config
from ben_engine.package import build_package

@pytest.mark.parametrize("tier,option", [("ben5", "hardware_only"), ("ben150", "managed")])
def test_package_builds(tmp_path, tier, option):
    cfg = Config.preset(tier, "healthcare" if tier == "ben150" else "private_cloud")
    res = build_package(cfg, option, "Test Customer", "Test Site", tmp_path, "both", {"GOVERNING_STATE": "Texas"}, include_drawings=False)
    for k in ("customer", "partner"):
        assert (res[k] / "MANIFEST.md").exists()
        m = (res[k] / "MANIFEST.md").read_text()
        assert "Proposal SAI-" in m
    assert (res["customer"] / "proposal" / "PROPOSAL.html").exists()
    assert (res["customer"] / "risk" / "RISK_DISCLOSURE.md").exists()
    if option == "managed":
        assert "MANAGED_SERVICES_SLA" in (res["customer"] / "MANIFEST.md").read_text()
    with zipfile.ZipFile(res["customer_zip"]) as z:
        names = z.namelist()
        assert any(n.endswith("PROPOSAL.md") for n in names)

def test_missing_sources_are_listed_not_hidden(tmp_path, monkeypatch):
    import ben_engine.package as pk
    monkeypatch.setattr(pk, "CUSTOMER_DOCS", pk.CUSTOMER_DOCS + [("docs/DOES_NOT_EXIST.md", "x/y.md", False)])
    res = build_package(Config.preset("ben30"), "hardware_controls", "C", "S", tmp_path, "customer", include_drawings=False, zip_it=False)
    assert "MISSING" in (res["customer"] / "MANIFEST.md").read_text()
