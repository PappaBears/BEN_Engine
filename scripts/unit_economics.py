"""Regenerate the unit-economics table in docs/investors/VC_PROPOSITION.md from the BOM generator.

Margin assumptions are explicit inputs here, not hidden in a spreadsheet.

    python scripts/unit_economics.py                 # Rev 1 (frozen lineup): VC_PROPOSITION.md table + web/assets/pricing.json
    python scripts/unit_economics.py --lineup rev2   # Rev 2: docs/rev2/UNIT_ECONOMICS.md + web/assets/pricing-rev2.json (VC doc untouched)
"""
import sys, os, re, json, argparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.config import Config, TIER_GEOMETRY, TIERS_BY_LINEUP
try:
    from ben_engine.bom import generate_bom, totals
except ImportError as e:
    print("bom module not available:", e); sys.exit(1)

from ben_engine.commercial import PROJECT_MARGIN  # noqa: E402
MARGIN_HW = PROJECT_MARGIN  # 35 % gross margin on the whole capital price (software/ben_engine/commercial.py)
CONTROLS_LICENCE_PER_UNIT_YR = {"ben5": 1200, "ben30": 4800, "ben150": 12000, "ben500": 30000, "ben2000": 90000}
MANAGED_PER_KW_MONTH = 45  # USD; below retail colocation (110–220) because the customer owns the asset

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--lineup", default="rev1", choices=["rev1", "rev2"])
ARGS = ap.parse_args()
if ARGS.lineup == "rev2":
    from ben_engine.proposal import CONTROLS_LICENCE_PER_UNIT_YR   # one table for Rev 2 tiers (proposal.py)

rows = []
pricing = {}
for tier in TIERS_BY_LINEUP[ARGS.lineup]:  # rev1: five tiers ben5 ... ben2000; rev2: eight tiers ben1 ... ben2000
    cfg = Config.preset(tier, lineup=ARGS.lineup)
    bom = generate_bom(cfg)
    t = totals(bom)
    cost = t["total_usd"]
    price = cost / (1 - MARGIN_HW)
    conf_pct = 100 * t["by_status"].get("confirmed", 0) / max(cost, 1)
    list_pct = 100 * t["by_status"].get("list", 0) / max(cost, 1)
    est_pct = 100 * t["by_status"].get("estimate", 0) / max(cost, 1)
    managed_yr = MANAGED_PER_KW_MONTH * cfg.it_kw * 12
    infra_cost = sum(r["ext_price_usd"] for r in bom if r["subsystem"] != "compute")
    rows.append((cfg.derived()["tier_label"], cfg.it_kw, cost, price, price - cost, conf_pct, list_pct, est_pct, CONTROLS_LICENCE_PER_UNIT_YR[tier], managed_yr, price / cfg.it_kw, infra_cost / (1 - MARGIN_HW)))
    by_sub = {}
    BASE = ("str", "env", "fs", "site", "svc")
    for s in ("power", "cooling", "compute", "controls", "base"):
        sub = [r for r in bom if (r["subsystem"] in BASE if s == "base" else r["subsystem"] == s)]
        by_sub[s] = {"total": sum(r["ext_price_usd"] for r in sub) / (1 - MARGIN_HW),
                     "confirmed": sum(r["ext_price_usd"] for r in sub if r["price_status"] == "confirmed") / (1 - MARGIN_HW),
                     "list": sum(r["ext_price_usd"] for r in sub if r["price_status"] == "list") / (1 - MARGIN_HW),
                     "estimate": sum(r["ext_price_usd"] for r in sub if r["price_status"] == "estimate") / (1 - MARGIN_HW)}
    pricing[tier] = {"preset_it_kw": cfg.it_kw, "preset_cooling_units": cfg.derived()["cooling_units_total"], "by_subsystem": by_sub, "priced_on": "2026-11-11", "margin": MARGIN_HW}
    if ARGS.lineup == "rev2":
        pricing[tier].update({"priced_on": "2026-11-09", "lineup": "rev2", "form": cfg.form or None, "racks": cfg.racks})
        if cfg.is_cluster():   # Rev 2 BEN 2000: three BEN 700 modules + shared yard (docs/REV2_DECISION.md §2b)
            d = cfg.derived()
            pricing[tier].update({"kind": "cluster", "modules": d["modules"], "module_tier": d["module_tier"], "module_it_kw": d["module_it_kw"],
                                  "yard_cost_usd": round(cost - d["modules"] * totals(generate_bom(cfg.module_config()))["total_usd"], 2),
                                  "status": "layout-checked (I-K yard checks, 2 STUDY items for the AHJ / utility), priced from catalog estimates; not a quote"})

tbl = [f"| Tier (preset) | IT kW | BOM cost (all modules) | Sell price ({MARGIN_HW:.0%} GM) | Infrastructure-only sell price (no compute) | Gross profit | Confirmed / list / estimate share of cost | Controls licence /yr | Managed service /yr | Price per kW IT |",
       "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
for r in rows:
    tbl.append(f"| {r[0]} | {r[1]:g} | ${r[2]:,.0f} | ${r[3]:,.0f} | ${r[11]:,.0f} | ${r[4]:,.0f} | {r[5]:.0f} % / {r[6]:.0f} % / {r[7]:.0f} % | ${r[8]:,.0f} | ${r[9]:,.0f} | ${r[10]:,.0f} |")
tbl.append("")
tbl.append(f"Assumptions: gross margin {MARGIN_HW:.0%} on the whole capital price; managed service ${MANAGED_PER_KW_MONTH}/kW-month; controls licence per tier as shown. BOM cost excludes site civil and utility service (SITE- lines are shown separately in `docs/BOM.md`). Compute is the reference GPU/CPU node set from the catalog and dominates the all-modules price (one 8-GPU server is ~$82–236 k); most SMB customers will size their own compute or start with the infrastructure-only price and grow.")
table = "\n".join(tbl)

if ARGS.lineup == "rev2":
    out = os.path.join(ROOT, "docs/rev2/UNIT_ECONOMICS.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    head = ("# BEN Engine Rev 2 — unit economics\n\n"
            "Generated by `python scripts/unit_economics.py --lineup rev2` from the Rev 2 presets (profile `ai_inference`, climate `temperate`) and "
            "`purchasing/parts_catalog.json`. This table is also written above the frozen Rev 1 table in `docs/investors/VC_PROPOSITION.md`. "
            "BEN 1 rows are the 10-inch rack preset (two desktop AI boxes); BEN 300 / BEN 700 carry GB300 NVL72-class compute at an analyst estimate "
            "(customer-selectable), so the infrastructure-only column is the number to read for those tiers. BEN 2000 is the Rev 2 cluster "
            "(docs/REV2_DECISION.md §2b): three BEN 700 modules at 666.7 kW (the stand-alone BEN 700 BOM × 3) plus the shared yard "
            "(12.47 kV switchgear, one pad-mount transformer per module, MV feeders, MV interconnect, yard surfacing and lanes, site controls); "
            "the yard lines are estimates (`docs/rev2/BOM-ben2000.md`, Scope column). The Rev 1 BEN 2000 hall row stays in `docs/investors/VC_PROPOSITION.md`.\n\n")
    open(out, "w").write(head + table.replace("BOM cost excludes site civil and utility service (SITE- lines are shown separately in `docs/BOM.md`)",
                                              "BOM cost includes the catalog SITE- and SVC- lines (`docs/rev2/BOM.md`)") + "\n")
    json.dump(pricing, open(os.path.join(ROOT, "web/assets/pricing-rev2.json"), "w"), indent=1)
    # the investor proposition carries the current Rev 2 table above its frozen Rev 1 record
    vp = os.path.join(ROOT, "docs/investors/VC_PROPOSITION.md")
    vs = open(vp).read()
    vs = re.sub(r"<!-- UNIT_ECONOMICS_TABLE_REV2 -->.*?<!-- /UNIT_ECONOMICS_TABLE_REV2 -->",
                lambda _m: "<!-- UNIT_ECONOMICS_TABLE_REV2 -->\n" + table + "\n<!-- /UNIT_ECONOMICS_TABLE_REV2 -->", vs, flags=re.S)
    open(vp, "w").write(vs)
    print(table)
    sys.exit(0)

p = os.path.join(ROOT, "docs/investors/VC_PROPOSITION.md")
s = open(p).read()
s = re.sub(r"<!-- UNIT_ECONOMICS_TABLE -->.*?(?=\n\nRevenue lines:)", "<!-- UNIT_ECONOMICS_TABLE -->\n" + table, s, flags=re.S)
open(p, "w").write(s)
json.dump(pricing, open(os.path.join(ROOT, "web/assets/pricing.json"), "w"), indent=1)
print(table)
