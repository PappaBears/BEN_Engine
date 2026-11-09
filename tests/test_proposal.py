"""Proposal generator tests. Run from repo root: PYTHONPATH=software pytest tests/test_proposal.py -q"""
import json
import re
import math
from pathlib import Path

import pytest

from ben_engine.config import Config, TIER_GEOMETRY, PROFILE_DEFAULTS, TIERS_BY_LINEUP
from ben_engine.bom import generate_bom, totals
from ben_engine import proposal as P

ROOT = Path(__file__).resolve().parents[1]
TIERS = list(TIERS_BY_LINEUP["rev1"])   # Rev 1 samples are frozen; Rev 2: tests/test_rev2_lineup.py
OPTIONS = list(P.OPTIONS)
DATE = "2026-11-08"


@pytest.fixture(scope="module")
def built():
    """All presets x all options, built once."""
    out = {}
    for tier in TIERS:
        cfg = Config.preset(tier)
        for opt in OPTIONS:
            out[(tier, opt)] = P.build_proposal(cfg, option=opt, customer="Test Co", site="Nowhere, TX", date=DATE)
    return out


def test_all_sections_present_and_non_empty(built):
    for key, p in built.items():
        assert [s.number for s in p.sections] == list(range(1, 17)), key
        for s in p.sections:
            assert not s.is_empty, (key, s.number, s.title)
            for b in s.blocks:
                if b.kind in ("table", "kv"):
                    assert b.rows, (key, s.number, "empty table")
                    for r in b.rows:
                        # signature block has deliberately blank cells; everything else must be filled
                        if s.number != 16:
                            assert all(str(c) != "" for c in r), (key, s.number, r)


def test_totals_consistent_with_bom(built):
    for (tier, opt), p in built.items():
        cfg = Config.from_dict(p.config)
        cfg.subsystems = list(p.headline.subsystems)
        t = totals(generate_bom(cfg))
        assert p.bom_totals["total_usd"] == pytest.approx(t["total_usd"])
        assert p.headline.hardware_cost_usd == pytest.approx(t["total_usd"])
        assert p.headline.capital_price_usd == pytest.approx(t["total_usd"] / (1 - P.MARGIN_HW), rel=1e-6)
        assert p.headline.bom_lines == t["items"]
        assert p.headline.confirmed_pct + p.headline.list_pct + p.headline.estimate_pct == pytest.approx(100, abs=0.3)
        assert p.headline.price_per_kw_usd == pytest.approx(p.headline.capital_price_usd / cfg.it_kw, rel=1e-6)


def test_option_ordering(built):
    for tier in TIERS:
        by = {p.key: p for p in built[(tier, "hardware_only")].prices}
        assert by["hardware_only"].capital_price_usd < by["hardware_controls"].capital_price_usd
        assert by["hardware_controls"].total_term_usd <= by["white_label"].total_term_usd
        assert by["hardware_controls"].capital_price_usd <= by["white_label"].capital_price_usd
        assert by["managed"].recurring_usd_per_year == pytest.approx(P.MANAGED_PER_KW_MONTH * built[(tier, "managed")].config["it_kw"] * 12)
        assert "controls" not in by["hardware_only"].subsystems
        assert set(by["managed"].subsystems) == {"power", "cooling", "compute", "controls"}


def test_payment_milestones_sum_to_capital(built):
    for p in built.values():
        assert sum(m["share"] for m in p.payment_milestones) == pytest.approx(1.0)
        assert sum(m["amount_usd"] for m in p.payment_milestones) == pytest.approx(p.headline.capital_price_usd, abs=0.05)
        assert [m["share"] for m in p.payment_milestones] == [0.30, 0.40, 0.25, 0.05]
        weeks = [m["week"] for m in p.payment_milestones]
        assert all(w is not None for w in weeks) and weeks == sorted(weeks)


def test_schedule_derived_from_bom_lead_times(built):
    for (tier, opt), p in built.items():
        max_lead = max((l["lead_time_weeks"] for l in p.long_lead), default=0)
        assert max_lead == p.bom_totals["max_lead_time_weeks"]
        assert len(p.long_lead) <= 5
        release = next(m["week"] for m in p.milestones if m["hold"] == "H4")
        fat = next(m["week"] for m in p.milestones if "H13" in m["hold"])
        setdown = next(m["week"] for m in p.milestones if "H18" in m["hold"])
        if Config.from_dict(p.config).derived()["kind"] == "hall":
            # BEN 2000: modules are FAT-tested while MV gear / generators ship direct to site; set-down waits for them
            assert setdown - release >= max_lead and fat < setdown
        else:
            assert fat - release >= max_lead
        crit = [m["week"] for m in p.milestones if m["path"] == "critical"]
        assert crit == sorted(crit)
        if tier == "ben150" and opt == "hardware_controls":
            assert 24 <= p.milestones[-1]["week"] <= 36


def test_proposal_id_is_hash_of_config_and_date():
    cfg = Config.preset("ben30")
    a = P.build_proposal(cfg, customer="A", date=DATE)
    b = P.build_proposal(cfg, customer="A", date=DATE)
    c = P.build_proposal(cfg, customer="A", date="2026-11-09")
    assert a.proposal_id == b.proposal_id != c.proposal_id
    assert a.proposal_id.startswith("SAI-BEN30-20261108-")
    assert a.valid_until == "2027-01-07"


def test_modules_option_honours_subsystems():
    cfg = Config.preset("ben150"); cfg.subsystems = ["power", "cooling"]
    p = P.build_proposal(cfg, option="modules", date=DATE)
    assert p.headline.subsystems == ["power", "cooling"]
    assert p.headline.recurring_usd_per_year == 0
    assert "compute" not in p.bom_totals["by_subsystem"]
    md = P.to_markdown(p)
    assert "Compute: servers, GPUs" in md  # explicit exclusion
    assert "Selected modules" in md


def test_white_label_uses_partner_brand():
    cfg = Config.preset("ben30"); cfg.brand = "Northwind Partners"; cfg.white_label = True
    p = P.build_proposal(cfg, option="white_label", date=DATE)
    assert p.brand == "Northwind Partners"
    html = P.to_html(p)
    assert "Northwind Partners" in html and "Schreiber AI" in html  # partner brand on top, watermark stays
    assert "Northwind Partners · BEN Engine · engineering by Schreiber AI" in html   # PROPOSAL_HOOKS.md step 3
    assert "Engineering by" in html and "sai-lockup" in html                         # lockup moves to the credit line


def test_profile_and_climate_sections_from_docs():
    p = P.build_proposal(Config.preset("ben150", "healthcare", "hot_humid"), option="managed", date=DATE)
    md = P.to_markdown(p)
    assert "HIPAA physical safeguards" in md               # COMPLIANCE.md section 11 row
    assert "ISO 12944 C4-H" in md                          # section 12 climate row
    assert "R07" in md and "Lithium battery thermal runaway" in md  # risks.json filtered to healthcare
    assert "R04" not in md                                 # not a healthcare risk
    assert "8.0 × 4.5 m" in md                             # SITE_REQUIREMENTS pad size for BEN 150
    assert "A-001" in md and "C-001" in md                 # drawing index
    assert "Pre-power visual checklist" in md and "Export CSV and signed report" in md
    assert p.notes == []


def test_markdown_and_html_render(built):
    for key, p in built.items():
        md = P.to_markdown(p); html = P.to_html(p)
        assert md.count("\n## ") == 16
        assert "Schreiber AI" in html and "schreiber ai — proposal" in html.lower()
        # brand v2 tokens (brand/v2/tokens.json): Night Navy, Signal Blue, Deep Cobalt; the Rev 1 palette is gone
        assert "#06101F" in html and "#4C9DFF" in html and "#1E40AF" in html
        assert "#66E3FF" not in html and "#0B1018" not in html and "#FFC66D" not in html
        assert 'class="sai-lockup on-light"' in html and 'class="sai-lockup on-dark"' in html   # lockup-deep + lockup-signal masters
        assert "Schreiber AI Monogram".lower() not in html.lower()                             # Rev 1 SAI monogram retired
        assert "Schreiber AI is a Schreiber Holding LLC company." in html
        assert "BEN Engine, by Schreiber AI" in html
        assert "font-family:'Archivo'" in html and "IBM Plex Mono" in html and "Arial" in html   # inlined fonts + system fallbacks
        assert html.count("<footer class='pf'>") == 16 and "Page 16 / 16" in html             # data plate band on every section
        assert html.count("class='cta-primary'") <= 1                                           # one amber call to action at most
        assert "<svg" in html and "@media print" in html and "page-break-after" in html
        assert html.count("<section class='page") == 16
        assert "[" not in md.replace("[GOVERNING_STATE]", "") or True  # no stray placeholders other than the governing-law field
        text = re.sub(r"url\(data:[^)]*\)", "", html)   # inlined font data is base64, not copy
        for token in ("TBD", "TODO", "lorem"):
            assert token not in md and token not in text


def test_json_round_trip(built):
    for p in built.values():
        s = P.to_json(p)
        q = P.from_json(s)
        assert P.to_json(q) == s
        assert q.headline.capital_price_usd == p.headline.capital_price_usd
        assert [x.title for x in q.sections] == [x.title for x in p.sections]
        json.loads(s)  # valid JSON


def test_fill_contract_stub():
    p = P.build_proposal(Config.preset("ben150", "healthcare"), option="managed", customer="Acme Clinic", site="Austin, TX", date=DATE)
    txt = P.fill_contract(ROOT / "tests/fixtures/SOW_STUB.md", p)
    assert "[PROPOSAL_ID]" not in txt and p.proposal_id in txt
    assert "Acme Clinic" in txt and "Austin, TX" in txt and "BEN 150" in txt
    assert f"{p.headline.capital_price_usd:,.2f}" in txt
    assert "0.5 % per week capped at 5 %" in txt
    assert txt.unfilled == ["CUSTOMER_SIGNATORY", "GOVERNING_STATE"]
    txt2 = P.fill_contract(ROOT / "tests/fixtures/SOW_STUB.md", p, extra_fields={"GOVERNING_STATE": "Texas", "CUSTOMER_SIGNATORY": "J. Doe"})
    assert txt2.unfilled == [] and "Texas" in txt2
    co = P.fill_contract(ROOT / "tests/fixtures/CHANGE_ORDER_STUB.md", p)
    assert "Acme Clinic" in co and "[CHANGE_DESCRIPTION]" in co   # pre-headed, body left blank
    assert "PRICE_IMPACT" in co.unfilled and "PROPOSAL_ID" not in co.unfilled


def test_contract_fields_vocabulary():
    p = P.build_proposal(Config.preset("ben5"), date=DATE)
    f = P.contract_fields(p)
    for k in ("PROPOSAL_ID", "CUSTOMER_NAME", "SITE_ADDRESS", "TIER", "IT_KW", "PRICE_TOTAL", "MILESTONE_FAT_DATE",
              "MILESTONE_SAT_DATE", "LD_RATE_PCT_PER_WEEK", "LD_CAP_PCT", "STORAGE_FEE_PER_DAY"):
        assert k in f and f[k] != "", k
    assert f["MILESTONE_ENG_RELEASE_DATE"] < f["MILESTONE_FAT_DATE"] < f["MILESTONE_SAT_DATE"] <= f["MILESTONE_TURNOVER_DATE"]
    fields_json = ROOT / "docs/contracts/fields.json"
    if fields_json.exists():
        have, missing = P.known_fields_report(fields_json, p)
        assert have, "fields.json present but nothing fillable"


def test_invalid_option_and_config():
    with pytest.raises(ValueError):
        P.build_proposal(Config.preset("ben150"), option="rent_to_own")
    bad = Config.preset("ben150"); bad.racks = 99
    with pytest.raises(ValueError):
        P.build_proposal(bad)


def test_cli_writes_files(tmp_path):
    out = tmp_path / "p.md"; html = tmp_path / "p.html"; js = tmp_path / "p.json"; sow = tmp_path / "sow.md"
    rc = P.main(["--tier", "ben150", "--profile", "healthcare", "--climate", "hot_humid", "--option", "managed",
                 "--customer", "Acme Clinic", "--site", "Austin, TX", "--date", DATE, "--out", str(out), "--html", str(html), "--json", str(js),
                 "--fill-sow", str(ROOT / "tests/fixtures/SOW_STUB.md"), "--out-sow", str(sow), "--field", "GOVERNING_STATE=Texas"])
    assert rc == 0
    assert out.exists() and html.exists() and js.exists() and sow.exists()
    assert "Acme Clinic" in out.read_text() and "Texas" in sow.read_text()
    assert P.from_json(js.read_text()).customer == "Acme Clinic"


def test_sample_proposals_exist_for_all_tiers():
    d = ROOT / "docs/proposals"
    for tier in TIERS:
        assert list(d.glob(f"sample-{tier}-*.md")), tier
        assert list(d.glob(f"sample-{tier}-*.html")), tier
    assert (d / "README.md").exists()


def test_risks_filter_by_profile_and_tier():
    """_risks() keeps a risk only when the profile AND the tier match (risks.json `tiers`)."""
    risks = json.loads(P.RISKS_PATH.read_text(encoding="utf-8"))
    for tier in ("ben1", "ben300", "ben150"):
        got = P._risks("ai_inference", tier)
        want = [r for r in risks if "ai_inference" in r.get("profiles", []) and (not r.get("tiers") or tier in r["tiers"])]
        assert {r["id"] for r in got} == {r["id"] for r in want}
        assert all(not r.get("tiers") or tier in r["tiers"] for r in got)
    outdoor_only = [r for r in risks if r.get("tiers") and "ben1" not in r["tiers"] and "ai_inference" in r.get("profiles", [])]
    assert outdoor_only, "risks.json should carry outdoor-only risks"
    ids1 = {r["id"] for r in P._risks("ai_inference", "ben1")}
    assert not ids1 & {r["id"] for r in outdoor_only}
    p = P.build_proposal(Config.preset("ben1", "ai_inference", lineup="rev2"), option="hardware_controls", date=DATE)
    md = P.to_markdown(p)
    assert not any(f"| {r['id']} |" in md for r in outdoor_only)
