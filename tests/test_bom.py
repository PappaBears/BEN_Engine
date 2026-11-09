"""BOM generator tests. Run from repo root: PYTHONPATH=software pytest tests/test_bom.py"""
import csv
import math
import re
from pathlib import Path

import pytest

from ben_engine.config import Config, TIER_GEOMETRY, TIERS_BY_LINEUP
from ben_engine.bom import (load_catalog, generate_bom, totals, eval_qty_rule, rule_variables,
                            QtyRuleError, to_csv, to_markdown, subsystem_of, STATUSES, CATALOG_PATH)

TIERS = list(TIERS_BY_LINEUP["rev1"])   # Rev 1 lineup (frozen artifacts); Rev 2 tiers: tests/test_rev2_lineup.py


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


def test_catalog_loads_and_has_required_fields(catalog):
    assert CATALOG_PATH.exists()
    assert len(catalog) > 50
    for p in catalog:
        assert p["code"].split("-")[0] in ("STR", "ENV", "PWR", "CLG", "CMP", "CTL", "FS", "SITE", "SVC"), p["code"]
        assert p["price_status"] in STATUSES
        assert p["unit_price_usd"] > 0
        assert set(p["applies_to_tiers"]) <= set(TIER_GEOMETRY)  # empty = catalogued alternate, not in any preset
        if p["price_status"] == "confirmed":
            assert p["price_checked"] in ("2026-11-07", "2026-11-08", "2026-11-09"), p["code"]   # 2026-11-09: Rev 2 lines
            assert p["vendor_url"].startswith("http"), f"{p['code']} confirmed price needs the URL it was seen on"
        elif p["price_status"] == "list":
            # audit F-05: list lines carry the date the manufacturer price was seen (or None if never checked)
            assert p["price_checked"] in (None, "2026-11-07", "2026-11-08", "2026-11-09"), p["code"]
            assert p["price_source_note"], f"{p['code']} list needs a basis note"
        else:
            assert p["price_checked"] is None, p["code"]
            assert p["price_source_note"], f"{p['code']} estimate needs a basis note"


def test_every_code_unique(catalog):
    codes = [p["code"] for p in catalog]
    assert len(codes) == len(set(codes))


@pytest.mark.parametrize("tier", TIERS)
def test_every_qty_rule_evaluates_for_preset(catalog, tier):
    cfg = Config.preset(tier)
    v = rule_variables(cfg)
    for p in catalog:
        q = eval_qty_rule(p["qty_rule"], v)
        assert q >= 0 and math.isfinite(q), (p["code"], tier)


def test_every_qty_rule_evaluates_with_generator(catalog):
    for tier in TIERS:
        cfg = Config.preset(tier)
        cfg.generator = True
        rows = generate_bom(cfg, catalog)
        gens = [r for r in rows if r["code"].startswith("PWR-GEN") or r["code"].startswith("PWR-ATS")]
        assert gens, tier
        # without generator none of these appear
        cfg.generator = False
        rows = generate_bom(cfg, catalog)
        assert not [r for r in rows if r["code"].startswith("PWR-GEN")]


def test_safe_evaluator_rejects_arbitrary_code():
    v = {"racks": 2}
    for bad in ["__import__('os')", "racks.__class__", "open('x')", "lambda: 1", "racks ** 2", "[1,2]", "x", "racks if 1"]:
        with pytest.raises(QtyRuleError):
            eval_qty_rule(bad, v)
    assert eval_qty_rule("ceil(racks/2)+1", v) == 2
    assert eval_qty_rule("max(1, racks-5)", v) == 1
    assert eval_qty_rule("2 if racks > 1 else 1", v) == 2


@pytest.mark.parametrize("tier", TIERS)
def test_totals_positive_and_sums_add_up(catalog, tier):
    rows = generate_bom(Config.preset(tier), catalog)
    assert rows
    t = totals(rows)
    assert t["total_usd"] > 0
    assert all(r["ext_price_usd"] == pytest.approx(r["qty"] * r["unit_price_usd"], abs=0.01) for r in rows)
    assert sum(t["by_status"].values()) == pytest.approx(t["total_usd"], abs=0.05)
    assert sum(t["by_subsystem"].values()) == pytest.approx(t["total_usd"], abs=0.05)
    assert 0 <= t["confirmed_pct"] <= 100
    assert all(r["qty"] >= 1 for r in rows)


def test_subsystem_filter_power_only(catalog):
    cfg = Config.preset("ben150")
    cfg.subsystems = ["power"]
    rows = generate_bom(cfg, catalog)
    prefixes = {r["code"].split("-")[0] for r in rows}
    assert "PWR" in prefixes
    assert "CLG" not in prefixes and "CMP" not in prefixes and "CTL" not in prefixes
    # enclosure, fire/safety, site and services always ride along
    assert {"STR", "ENV", "FS", "SITE", "SVC"} <= prefixes
    assert all(subsystem_of(r["code"]) in ("power", "str", "env", "fs", "site", "svc") for r in rows)


def test_no_subsystems_gives_empty_bom(catalog):
    cfg = Config.preset("ben150")
    cfg.subsystems = []
    assert generate_bom(cfg, catalog) == []


def test_cooling_type_filter(catalog):
    cfg = Config.preset("ben150")
    cfg.cooling = "inrow_dx_300"; cfg.racks = 4; cfg.it_kw = 72.0
    assert not cfg.validate()
    codes = {r["code"] for r in generate_bom(cfg, catalog)}
    assert "CLG-INROW" in codes and "CLG-RDHX" not in codes and "CLG-CDU" not in codes
    cfg.cooling = "rdhx_drycooler"
    codes = {r["code"] for r in generate_bom(cfg, catalog)}
    assert "CLG-RDHX" in codes and "CLG-DRYCOOLER" in codes and "CLG-INROW" not in codes


def test_ben5_has_fs_but_no_clean_agent(catalog):
    codes = {r["code"] for r in generate_bom(Config.preset("ben5"), catalog)}
    assert "FS-AEROSOL" in codes and "FS-CLEAN-AGENT" not in codes
    codes40 = {r["code"] for r in generate_bom(Config.preset("ben500"), catalog)}
    assert "FS-CLEAN-AGENT" in codes40


def test_controls_pod_count_rule(catalog):
    """BEN Pods: two per rack (cold and hot face) + room + outdoor on container tiers, 3 on BEN 5."""
    for tier in TIERS:
        cfg = Config.preset(tier, lineup="rev1")   # Rev 1 lineup: BEN 2000 is the hall (Rev 2 cluster: tests/test_cluster.py)
        rows = {r["code"]: r for r in generate_bom(cfg, catalog)}
        expected = 3 if tier == "ben5" else cfg.racks * 2 + 2 * cfg.derived()["modules"]
        assert rows["CTL-POD"]["qty"] == expected
        assert rows["CTL-POD-ENCL"]["qty"] == expected
        modules = cfg.derived()["modules"]
        assert rows["CTL-RCP"]["qty"] == (modules + 1 if modules > 1 else (2 if cfg.racks >= 3 else 1))
        pdu = "PWR-PDU-HD" if tier == "ben2000" else "PWR-PDU"   # BEN 2000 rows use 415 V 60 A PDUs
        assert rows[pdu]["qty"] == cfg.racks * 2
        # no hobby-grade controls hardware in any preset
        assert not {"CTL-GW-PI5", "CTL-NODE-MCU", "CTL-DS18B20", "CTL-SHT45", "CTL-ADS1115", "CTL-POE-SW"} & set(rows)


def test_controls_tier_filter(catalog):
    """applies_to_controls splits BEN Controls Lite (RevPi) from BEN Controls Pro (PLCnext panel + edge computer)."""
    lite = {r["code"] for r in generate_bom(Config.preset("ben5"), catalog)}
    assert {"CTL-REVPI", "CTL-REVPI-DIO", "CTL-REVPI-AIO", "CTL-SWITCH-LITE", "CTL-ENCL", "CTL-POD", "CTL-PSU-QUINT"} <= lite
    assert not {"CTL-PLC", "CTL-EDGE", "CTL-PANEL", "CTL-PANEL-BUILD", "CTL-IO-DIO", "CTL-LEAK-CTRL"} & lite
    pro = {r["code"]: r for r in generate_bom(Config.preset("ben500"), catalog)}
    assert {"CTL-PLC", "CTL-IO-DIO", "CTL-IO-RTD", "CTL-IO-AI", "CTL-EDGE", "CTL-PANEL", "CTL-PANEL-BUILD", "CTL-SWITCH",
            "CTL-PSU-ORING", "CTL-SETRA264", "CTL-VAISALA-HMW90", "CTL-LEAK-CTRL", "CTL-POD"} <= set(pro)
    assert not {"CTL-REVPI", "CTL-SWITCH-LITE"} & set(pro)
    assert pro["CTL-PSU-QUINT"]["qty"] == 2
    # BEN 30 defaults to Lite for ai_inference and to Pro for healthcare; the override is honoured
    b10 = Config.preset("ben30")
    assert "CTL-REVPI" in {r["code"] for r in generate_bom(b10, catalog)}
    b10.controls_tier = "pro"
    codes = {r["code"] for r in generate_bom(b10, catalog)}
    assert "CTL-PLC" in codes and "CTL-REVPI" not in codes
    assert "CTL-PLC" in {r["code"] for r in generate_bom(Config.preset("ben30", "healthcare"), catalog)}


def test_moq_respected(catalog):
    rows = {r["code"]: r for r in generate_bom(Config.preset("ben5"), catalog)}
    assert rows["CTL-RELAY"]["qty"] % 10 == 0
    assert rows["CTL-TERM"]["qty"] % 50 == 0


def test_csv_and_markdown_outputs(catalog, tmp_path):
    cfg = Config.preset("ben30")
    rows = generate_bom(cfg, catalog)
    path = to_csv(rows, tmp_path / "bom.csv")
    with open(path, newline="") as f:
        data = list(csv.DictReader(f))
    assert data[-1]["code"] == "TOTAL"
    assert len(data) == len(rows) + 1
    md = to_markdown(rows, cfg, "t")
    assert "confirmed" in md and "| Code |" in md and rows[0]["code"] in md


def test_invalid_config_rejected(catalog):
    cfg = Config.preset("ben150")
    cfg.racks = 99
    with pytest.raises(ValueError):
        generate_bom(cfg, catalog)


# ----------------------------------------------------------------------------- generation 2 (docs/TIER_AND_ENCLOSURE_DECISION.md)
def test_catalog_file_uses_only_new_tier_keys():
    """The catalog itself carries the power-based keys; the loader alias is a fallback, not the storage format."""
    import json
    raw = json.load(open(CATALOG_PATH, encoding="utf-8"))
    for p in raw:
        assert not set(p["applies_to_tiers"]) & {"micro", "ben10", "ben20", "ben40"}, p["code"]
        assert not re.search(r"BEN (Micro|10|20|40)\b", p["name"]), p["code"]
        assert "NEMA 3R" not in p["name"], p["code"]   # NEMA 3R dropped everywhere


def test_ben5_cabinet_is_nema_4x_and_ip66_sealing_lines_everywhere(catalog):
    cab = next(p for p in catalog if p["code"] == "STR-CAB24U")
    assert "NEMA 4X" in cab["name"] and "IP66" in cab["name"] and cab["applies_to_tiers"] == ["ben5"]
    for tier in TIERS:
        codes = {r["code"] for r in generate_bom(Config.preset(tier), catalog)}
        assert {"ENV-SEAL-KIT", "ENV-DOORGASKET-4X", "SVC-HOSE-TEST"} <= codes, tier


def test_rule_variables_expose_generation2_terms():
    v = rule_variables(Config.preset("ben2000", lineup="rev1"))
    for k in ("transformers_total", "generators_total", "modules", "rows", "hardening_H2", "hardening_H3", "envelope_area_m2", "mv_service"):
        assert k in v, k
    assert v["modules"] == 3 and v["rows"] == 4 and v["mv_service"] == 1 and v["hardening_H2"] == 0 and v["hardening_H3"] == 0
    assert eval_qty_rule("transformers_total * 2 + modules", v) == v["transformers_total"] * 2 + 3


def test_ben2000_bom_has_mv_service_generators_and_modules(catalog):
    cfg = Config.preset("ben2000", lineup="rev1")   # the Rev 1 hall
    d = cfg.derived()
    rows = {r["code"]: r for r in generate_bom(cfg, catalog)}
    t = totals(list(rows.values()))
    assert t["total_usd"] > 0 and t["items"] > 60
    # medium-voltage service chain
    assert {"PWR-MV-SWGR", "PWR-MV-XFMR-2500", "PWR-LV-SWGR-4000", "PWR-UPS-GVL500", "PWR-BATT-ROOM"} <= set(rows)
    assert rows["PWR-MV-XFMR-2500"]["qty"] == d["transformers_total"] == 2
    assert rows["PWR-LV-SWGR-4000"]["qty"] == d["transformers_total"]
    assert rows["PWR-UPS-GVL500"]["qty"] == d["ups_modules"] * math.ceil(d["ups_kva_each"] / 500)
    # N+1 generators follow the derived count, and the preset always carries them
    assert cfg.generator and rows["PWR-GEN-1250"]["qty"] == d["generators_total"] == 3
    # modules, CDU rows, controls
    assert rows["STR-MODULE-WB"]["qty"] == d["modules"] == 3 and rows["STR-MODULE-PWR"]["qty"] == 1
    assert rows["STR-MODULE-JOINT"]["qty"] == d["modules"] * 2 + (d["modules"] - 1) + 2   # bay seams, bay-to-bay joints, power module
    assert rows["CLG-CDU"]["qty"] == d["cooling_units_total"] and rows["CLG-MANIFOLD"]["qty"] == cfg.racks
    assert rows["CTL-PLC"]["qty"] == d["modules"] + 1 and rows["CTL-PANEL"]["qty"] == 1
    assert rows["CTL-POD"]["qty"] == d["pods"]
    assert rows["FS-VESDA-HALL"]["qty"] == d["modules"] + 1 and "FS-CLEAN-AGENT-HALL" in rows and "FS-CLEAN-AGENT" not in rows
    assert "SITE-SLAB" in rows and "SITE-MV-INTERCONNECT" in rows
    # container-only lines stay out of the hall
    assert not {"STR-CONT40", "SVC-CSC", "STR-TIEDOWN", "PWR-ATS-400"} & set(rows)
    # every line has a real vendor and a basis
    for r in rows.values():
        assert r["manufacturer"] and r["vendor"], r["code"]
        if r["price_status"] != "confirmed":
            assert r["price_source_note"], r["code"]


def test_hardening_filter(catalog):
    hard_codes = {p["code"] for p in catalog if p.get("applies_to_hardening")}
    assert hard_codes, "catalog needs applies_to_hardening lines"
    for tier in TIERS:
        base = Config.preset(tier); base.hardening = "H1"
        h1 = {r["code"] for r in generate_bom(base, catalog)}
        assert not h1 & hard_codes, (tier, h1 & hard_codes)       # H1 carries no H2/H3 add-ons
        base.hardening = "H2"
        h2 = {r["code"] for r in generate_bom(base, catalog)}
        assert {"STR-FLOOD-PLINTH", "ENV-C5M-COATING", "ENV-EPM1-FILTER", "STR-HURRICANE-HW"} <= h2, tier
        assert not {c for c in h2 if c.startswith("STR-BALLISTIC") or c.startswith("ENV-HEMP")}, tier
        base.hardening = "H3"
        h3 = {r["code"] for r in generate_bom(base, catalog)}
        assert "STR-BALLISTIC-UL752" in h3 and "STR-DOOR-FE" in h3 and "ENV-HEMP-SHIELD" in h3 and "CTL-2FA-ACCESS" in h3, tier
        assert {"STR-FLOOD-PLINTH", "ENV-C5M-COATING"} <= h3     # H3 is "as H2 plus"
        assert h1 < h2 < h3
        t1, t3 = totals(generate_bom(Config.preset(tier), catalog)), totals(generate_bom(base, catalog))
        assert t3["total_usd"] > t1["total_usd"]
    # the ballistic line scales with wall area and the shield with envelope area
    cfg = Config.preset("ben500"); cfg.hardening = "H3"
    rows = {r["code"]: r for r in generate_bom(cfg, catalog)}
    v = rule_variables(cfg)
    assert rows["STR-BALLISTIC-UL752"]["qty"] == math.ceil(v["wall_area_m2"])
    assert rows["ENV-HEMP-SHIELD"]["qty"] == math.ceil(v["envelope_area_m2"])
    # public_sector presets default to H3 and coastal to H2 (decision §3)
    assert Config.preset("ben150", "public_sector").hardening == "H3"
    assert Config.preset("ben150", "ai_inference", "coastal").hardening == "H2"


def test_old_key_catalog_is_canonicalised(tmp_path):
    import json
    part = {"code": "X-1", "name": "x", "unit": "ea", "unit_price_usd": 1.0, "price_status": "estimate", "applies_to_tiers": ["micro", "ben40"], "qty_rule": "1",
            "price_source_note": "n", "price_checked": None}
    f = tmp_path / "cat.json"; f.write_text(json.dumps([part]))
    assert load_catalog(f)[0]["applies_to_tiers"] == ["ben5", "ben500"]


def test_generated_artifacts_exist():
    root = Path(__file__).resolve().parents[1]
    for tier in TIERS:
        assert (root / "purchasing" / f"bom-{tier}.csv").exists()
        assert (root / "docs" / f"BOM-{tier}.md").exists()
    assert (root / "docs" / "BOM.md").exists()
    assert (root / "purchasing" / "bom.csv").exists()


def test_price_status_evidence_rule():
    """Audit F-05: a confirmed price must sit on the vendor's own page with a date; a list price needs a URL or an MSRP note."""
    from ben_engine.bom import validate_price_evidence, is_marketplace_url
    base = {"code": "X-1", "name": "x", "unit": "ea", "unit_price_usd": 1.0, "applies_to_tiers": [], "qty_rule": "1",
            "price_source_note": "seen", "price_checked": "2026-11-08"}
    ok = dict(base, price_status="confirmed", vendor_url="https://www.cdw.com/product/x/123")
    validate_price_evidence(ok)
    for bad_url in ("https://www.alibaba.com/product-detail/x.html", "https://reach.dog/shop/dealer/products/x",
                    "https://www.findchips.com/detail/x", "https://marketplace-admin.example.com/x.html",
                    "https://www.digikey.co.uk/en/videos/r/rittal/x", "https://www.amazon.com/dp/B000", ""):
        assert is_marketplace_url(bad_url) or bad_url == ""
        with pytest.raises(ValueError):
            validate_price_evidence(dict(base, price_status="confirmed", vendor_url=bad_url))
    with pytest.raises(ValueError):
        validate_price_evidence(dict(ok, price_checked=None))
    validate_price_evidence(dict(base, price_status="list", vendor_url="", price_source_note="MSRP $39 on the product page"))
    validate_price_evidence(dict(base, price_status="list", vendor_url="https://vendor.example.com/p/1", price_source_note="x"))
    with pytest.raises(ValueError):
        validate_price_evidence(dict(base, price_status="list", vendor_url="", price_source_note="no url, no msrp"))
    validate_price_evidence(dict(base, price_status="estimate", vendor_url="", price_checked=None))


def test_catalog_confirmed_lines_sit_on_vendor_pages(catalog):
    from ben_engine.bom import is_marketplace_url
    for p in catalog:
        if p["price_status"] == "confirmed":
            assert not is_marketplace_url(p["vendor_url"]), p["code"]
            assert p["price_checked"], p["code"]
        if p["price_status"] == "list":
            assert p["vendor_url"].startswith("http") or p["price_source_note"].startswith("MSRP"), p["code"]
        assert not p["name"].startswith("[WITHDRAWN]"), f"{p['code']}: withdrawn lines live in parts_catalog_withdrawn.json"
