"""Regenerate the unit-economics table in docs/investors/VC_PROPOSITION.md from the BOM generator.

Margin assumptions are explicit inputs here, not hidden in a spreadsheet.
"""
import sys, os, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.config import Config
try:
    from ben_engine.bom import generate_bom, totals
except ImportError as e:
    print("bom module not available:", e); sys.exit(1)

MARGIN_HW = 0.28          # target gross margin on purchased hardware + build labour
CONTROLS_LICENCE_PER_UNIT_YR = {"micro": 1200, "ben10": 4800, "ben20": 12000, "ben40": 30000}
MANAGED_PER_KW_MONTH = 45  # USD; below retail colocation (110–220) because the customer owns the asset

rows = []
pricing = {}
for tier in ("micro", "ben10", "ben20", "ben40"):
    cfg = Config.preset(tier)
    bom = generate_bom(cfg)
    t = totals(bom)
    cost = t["total"]
    price = cost / (1 - MARGIN_HW)
    conf_pct = 100 * t["by_status"].get("confirmed", 0) / max(cost, 1)
    list_pct = 100 * t["by_status"].get("list", 0) / max(cost, 1)
    est_pct = 100 * t["by_status"].get("estimate", 0) / max(cost, 1)
    managed_yr = MANAGED_PER_KW_MONTH * cfg.it_kw * 12
    rows.append((cfg.derived()["tier_label"], cfg.it_kw, cost, price, price - cost, conf_pct, list_pct, est_pct, CONTROLS_LICENCE_PER_UNIT_YR[tier], managed_yr, price / cfg.it_kw))
    by_sub = {}
    for s in ("power", "cooling", "compute", "controls", "base"):
        sub = [r for r in bom if r.get("subsystem") == s]
        by_sub[s] = {"total": sum(r["ext_price"] for r in sub) / (1 - MARGIN_HW),
                     "confirmed": sum(r["ext_price"] for r in sub if r["price_status"] == "confirmed") / (1 - MARGIN_HW),
                     "list": sum(r["ext_price"] for r in sub if r["price_status"] == "list") / (1 - MARGIN_HW),
                     "estimate": sum(r["ext_price"] for r in sub if r["price_status"] == "estimate") / (1 - MARGIN_HW)}
    pricing[tier] = {"preset_it_kw": cfg.it_kw, "preset_cooling_units": cfg.derived()["cooling_units_total"], "by_subsystem": by_sub, "priced_on": "2026-11-07", "margin": MARGIN_HW}

tbl = ["| Tier (preset) | IT kW | BOM cost | Sell price (28 % GM) | Gross profit | Confirmed / list / estimate share of cost | Controls licence /yr | Managed service /yr | Price per kW IT |",
       "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
for r in rows:
    tbl.append(f"| {r[0]} | {r[1]:.0f} | ${r[2]:,.0f} | ${r[3]:,.0f} | ${r[4]:,.0f} | {r[5]:.0f} % / {r[6]:.0f} % / {r[7]:.0f} % | ${r[8]:,.0f} | ${r[9]:,.0f} | ${r[10]:,.0f} |")
tbl.append("")
tbl.append(f"Assumptions: hardware gross margin {MARGIN_HW:.0%}; managed service ${MANAGED_PER_KW_MONTH}/kW-month; controls licence per tier as shown. BOM cost excludes site civil and utility service (SITE- lines are shown separately in `docs/BOM.md`). Compute is the reference node set from the catalog; customers often supply their own.")
table = "\n".join(tbl)

p = os.path.join(ROOT, "docs/investors/VC_PROPOSITION.md")
s = open(p).read()
s = re.sub(r"<!-- UNIT_ECONOMICS_TABLE -->.*?(?=\n\nRevenue lines:)", "<!-- UNIT_ECONOMICS_TABLE -->\n" + table, s, flags=re.S)
open(p, "w").write(s)
json.dump(pricing, open(os.path.join(ROOT, "web/assets/pricing.json"), "w"), indent=1)
print(table)
