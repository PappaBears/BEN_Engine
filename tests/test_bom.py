"""BOM generator tests. Run from repo root: PYTHONPATH=software pytest tests/test_bom.py"""
import csv
import math
from pathlib import Path

import pytest

from ben_engine.config import Config, TIER_GEOMETRY
from ben_engine.bom import (load_catalog, generate_bom, totals, eval_qty_rule, rule_variables,
                            QtyRuleError, to_csv, to_markdown, subsystem_of, STATUSES, CATALOG_PATH)

TIERS = list(TIER_GEOMETRY)


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
        assert set(p["applies_to_tiers"]) <= set(TIERS)  # empty = catalogued alternate, not in any preset
        if p["price_status"] == "confirmed":
            assert p["price_checked"] in ("2026-11-07", "2026-11-08"), p["code"]
            assert p["vendor_url"].startswith("http"), f"{p['code']} confirmed price needs the URL it was seen on"
        else:
            assert p["price_checked"] is None, p["code"]
            assert p["price_source_note"], f"{p['code']} estimate/list needs a basis note"


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
    cfg = Config.preset("ben20")
    cfg.subsystems = ["power"]
    rows = generate_bom(cfg, catalog)
    prefixes = {r["code"].split("-")[0] for r in rows}
    assert "PWR" in prefixes
    assert "CLG" not in prefixes and "CMP" not in prefixes and "CTL" not in prefixes
    # enclosure, fire/safety, site and services always ride along
    assert {"STR", "ENV", "FS", "SITE", "SVC"} <= prefixes
    assert all(subsystem_of(r["code"]) in ("power", "str", "env", "fs", "site", "svc") for r in rows)


def test_no_subsystems_gives_empty_bom(catalog):
    cfg = Config.preset("ben20")
    cfg.subsystems = []
    assert generate_bom(cfg, catalog) == []


def test_cooling_type_filter(catalog):
    cfg = Config.preset("ben20")
    cfg.cooling = "inrow_dx_300"; cfg.racks = 4; cfg.it_kw = 72.0
    assert not cfg.validate()
    codes = {r["code"] for r in generate_bom(cfg, catalog)}
    assert "CLG-INROW" in codes and "CLG-RDHX" not in codes and "CLG-CDU" not in codes
    cfg.cooling = "rdhx_drycooler"
    codes = {r["code"] for r in generate_bom(cfg, catalog)}
    assert "CLG-RDHX" in codes and "CLG-DRYCOOLER" in codes and "CLG-INROW" not in codes


def test_micro_has_fs_but_no_clean_agent(catalog):
    codes = {r["code"] for r in generate_bom(Config.preset("micro"), catalog)}
    assert "FS-AEROSOL" in codes and "FS-CLEAN-AGENT" not in codes
    codes40 = {r["code"] for r in generate_bom(Config.preset("ben40"), catalog)}
    assert "FS-CLEAN-AGENT" in codes40


def test_controls_pod_count_rule(catalog):
    """BEN Pods: two per rack (cold and hot face) + room + outdoor on container tiers, 3 on BEN Micro."""
    for tier in TIERS:
        cfg = Config.preset(tier)
        rows = {r["code"]: r for r in generate_bom(cfg, catalog)}
        expected = 3 if tier == "micro" else cfg.racks * 2 + 2
        assert rows["CTL-POD"]["qty"] == expected
        assert rows["CTL-POD-ENCL"]["qty"] == expected
        assert rows["CTL-RCP"]["qty"] == (2 if cfg.racks >= 3 else 1)
        assert rows["PWR-PDU"]["qty"] == cfg.racks * 2
        # no hobby-grade controls hardware in any preset
        assert not {"CTL-GW-PI5", "CTL-NODE-MCU", "CTL-DS18B20", "CTL-SHT45", "CTL-ADS1115", "CTL-POE-SW"} & set(rows)


def test_controls_tier_filter(catalog):
    """applies_to_controls splits BEN Controls Lite (RevPi) from BEN Controls Pro (PLCnext panel + edge computer)."""
    lite = {r["code"] for r in generate_bom(Config.preset("micro"), catalog)}
    assert {"CTL-REVPI", "CTL-REVPI-DIO", "CTL-REVPI-AIO", "CTL-SWITCH-LITE", "CTL-ENCL", "CTL-POD", "CTL-PSU-QUINT"} <= lite
    assert not {"CTL-PLC", "CTL-EDGE", "CTL-PANEL", "CTL-PANEL-BUILD", "CTL-IO-DIO", "CTL-LEAK-CTRL"} & lite
    pro = {r["code"]: r for r in generate_bom(Config.preset("ben40"), catalog)}
    assert {"CTL-PLC", "CTL-IO-DIO", "CTL-IO-RTD", "CTL-IO-AI", "CTL-EDGE", "CTL-PANEL", "CTL-PANEL-BUILD", "CTL-SWITCH",
            "CTL-PSU-ORING", "CTL-SETRA264", "CTL-VAISALA-HMW90", "CTL-LEAK-CTRL", "CTL-POD"} <= set(pro)
    assert not {"CTL-REVPI", "CTL-SWITCH-LITE"} & set(pro)
    assert pro["CTL-PSU-QUINT"]["qty"] == 2
    # BEN 10 defaults to Lite for ai_inference and to Pro for healthcare; the override is honoured
    b10 = Config.preset("ben10")
    assert "CTL-REVPI" in {r["code"] for r in generate_bom(b10, catalog)}
    b10.controls_tier = "pro"
    codes = {r["code"] for r in generate_bom(b10, catalog)}
    assert "CTL-PLC" in codes and "CTL-REVPI" not in codes
    assert "CTL-PLC" in {r["code"] for r in generate_bom(Config.preset("ben10", "healthcare"), catalog)}


def test_moq_respected(catalog):
    rows = {r["code"]: r for r in generate_bom(Config.preset("micro"), catalog)}
    assert rows["CTL-RELAY"]["qty"] % 10 == 0
    assert rows["CTL-TERM"]["qty"] % 50 == 0


def test_csv_and_markdown_outputs(catalog, tmp_path):
    cfg = Config.preset("ben10")
    rows = generate_bom(cfg, catalog)
    path = to_csv(rows, tmp_path / "bom.csv")
    with open(path, newline="") as f:
        data = list(csv.DictReader(f))
    assert data[-1]["code"] == "TOTAL"
    assert len(data) == len(rows) + 1
    md = to_markdown(rows, cfg, "t")
    assert "confirmed" in md and "| Code |" in md and rows[0]["code"] in md


def test_invalid_config_rejected(catalog):
    cfg = Config.preset("ben20")
    cfg.racks = 99
    with pytest.raises(ValueError):
        generate_bom(cfg, catalog)


def test_generated_artifacts_exist():
    root = Path(__file__).resolve().parents[1]
    for tier in TIERS:
        assert (root / "purchasing" / f"bom-{tier}.csv").exists()
        assert (root / "docs" / f"BOM-{tier}.md").exists()
    assert (root / "docs" / "BOM.md").exists()
    assert (root / "purchasing" / "bom.csv").exists()
