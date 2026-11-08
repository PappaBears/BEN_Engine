"""BEN Engine bill-of-materials generator.

Reads ``purchasing/parts_catalog.json`` and a :class:`ben_engine.config.Config`, evaluates each
part's ``qty_rule`` with a tiny whitelisted expression evaluator (no ``eval``), filters by tier,
cooling type and selected subsystems, and returns priced rows plus totals by subsystem and by
price confidence (confirmed / list / estimate).

Subsystem membership is by code prefix:
    PWR -> power, CLG -> cooling, CMP -> compute, CTL -> controls.
STR / ENV / FS / SITE / SVC lines are always included when at least one subsystem is selected
(they are the enclosure, site and labour that every delivered unit needs). A part may also carry
``applies_to_cooling`` (list of cooling keys) so DX, RDHx and DLC lines do not all appear at once.

Decision (recorded here and in purchasing/SOURCING_NOTES.md): FS lines are *not* excluded for
BEN Micro. Instead the catalog carries Micro-specific FS parts (aerosol unit, E-stop) and the
clean-agent system applies to container tiers only via ``applies_to_tiers``.

CLI::

    python -m ben_engine.bom --tier ben20 --csv purchasing/bom-ben20.csv --md docs/BOM-ben20.md
    python -m ben_engine.bom --all          # writes all four presets + docs/BOM.md summary
"""
from __future__ import annotations

import ast
import csv
import json
import math
import operator
from pathlib import Path
from typing import Any, Dict, List

from .config import Config, TIER_GEOMETRY

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "purchasing" / "parts_catalog.json"

PREFIX_TO_SUBSYSTEM = {"PWR": "power", "CLG": "cooling", "CMP": "compute", "CTL": "controls"}
ALWAYS_PREFIXES = ("STR", "ENV", "FS", "SITE", "SVC")
STATUSES = ("confirmed", "list", "estimate")

# ----------------------------------------------------------------------------- safe evaluator
_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_CMP = {ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
        ast.Eq: operator.eq, ast.NotEq: operator.ne}
_FUNCS = {"ceil": math.ceil, "floor": math.floor, "min": min, "max": max, "round": round, "int": int, "abs": abs}


class QtyRuleError(ValueError):
    pass


def eval_qty_rule(expr: str, variables: Dict[str, float]) -> float:
    """Evaluate a qty_rule using only arithmetic, comparisons, ``x if c else y`` and the
    whitelisted functions above. Any other syntax raises :class:`QtyRuleError`."""
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as e:
        raise QtyRuleError(f"bad qty_rule {expr!r}: {e}") from None

    def ev(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            raise QtyRuleError(f"unknown variable {node.id!r} in {expr!r}")
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            return _BIN[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](ev(node.operand))
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _CMP:
            return _CMP[type(node.ops[0])](ev(node.left), ev(node.comparators[0]))
        if isinstance(node, ast.IfExp):
            return ev(node.body) if ev(node.test) else ev(node.orelse)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS and not node.keywords:
            return _FUNCS[node.func.id](*[ev(a) for a in node.args])
        raise QtyRuleError(f"disallowed syntax {type(node).__name__} in {expr!r}")

    val = ev(tree)
    if isinstance(val, bool):
        val = int(val)
    if not isinstance(val, (int, float)) or val < 0 or math.isnan(val) or math.isinf(val):
        raise QtyRuleError(f"qty_rule {expr!r} gave {val!r}")
    return val


# ----------------------------------------------------------------------------- catalog
def load_catalog(path: Path | str = CATALOG_PATH) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        cat = json.load(f)
    if not isinstance(cat, list):
        raise ValueError("catalog must be a JSON array")
    seen = set()
    for p in cat:
        for k in ("code", "name", "unit", "unit_price_usd", "price_status", "applies_to_tiers", "qty_rule"):
            if k not in p:
                raise ValueError(f"part {p.get('code')} missing {k}")
        if p["code"] in seen:
            raise ValueError(f"duplicate code {p['code']}")
        seen.add(p["code"])
        if p["price_status"] not in STATUSES:
            raise ValueError(f"{p['code']}: bad price_status {p['price_status']}")
    return cat


def subsystem_of(code: str) -> str:
    prefix = code.split("-", 1)[0]
    return PREFIX_TO_SUBSYSTEM.get(prefix, prefix.lower())


def rule_variables(cfg: Config) -> Dict[str, float]:
    d = cfg.derived()
    g = TIER_GEOMETRY[cfg.tier]
    return {
        "racks": cfg.racks,
        "it_kw": cfg.it_kw,
        "cooling_units_total": d["cooling_units_total"],
        "ups_modules": d["ups_modules"],
        "ups_kva_each": d["ups_kva_each"],
        "battery_kwh": d["battery_kwh"],
        "service_breaker_a": d["service_breaker_a"],
        "total_kw": d["total_kw"],
        "total_kva": d["total_kva"],
        "nodes": math.ceil(cfg.racks / 2) + 1,
        "tier_len_m": g["ext_l_m"],
        "generator": 1 if cfg.generator else 0,
    }


# ----------------------------------------------------------------------------- generation
def generate_bom(cfg: Config, catalog: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    """Return priced BOM rows for ``cfg``. Rows whose quantity evaluates to zero are dropped."""
    errs = cfg.validate()
    if errs:
        raise ValueError("invalid config: " + "; ".join(errs))
    catalog = catalog if catalog is not None else load_catalog()
    subs = set(cfg.subsystems)
    if not subs:
        return []
    variables = rule_variables(cfg)
    rows: List[Dict[str, Any]] = []
    for p in catalog:
        if cfg.tier not in p["applies_to_tiers"]:
            continue
        cooling_filter = p.get("applies_to_cooling")
        if cooling_filter and cfg.cooling not in cooling_filter:
            continue
        prefix = p["code"].split("-", 1)[0]
        sub = subsystem_of(p["code"])
        if prefix not in ALWAYS_PREFIXES and sub not in subs:
            continue
        qty = eval_qty_rule(p["qty_rule"], variables)
        qty = math.ceil(qty - 1e-9) if not float(qty).is_integer() else int(qty)
        moq = int(p.get("moq") or 1)
        if qty > 0 and moq > 1:
            qty = max(qty, moq)
            qty = int(math.ceil(qty / moq) * moq)
        if qty <= 0:
            continue
        unit_price = float(p["unit_price_usd"])
        rows.append({
            "code": p["code"], "subsystem": sub, "name": p["name"],
            "manufacturer": p.get("manufacturer", ""), "mpn": p.get("mpn", ""),
            "vendor": p.get("vendor", ""), "vendor_url": p.get("vendor_url", ""),
            "unit": p["unit"], "qty": qty, "unit_price_usd": round(unit_price, 2),
            "ext_price_usd": round(qty * unit_price, 2),
            "price_status": p["price_status"], "price_checked": p.get("price_checked"),
            "price_source_note": p.get("price_source_note", ""),
            "lead_time_weeks": p.get("lead_time_weeks"), "availability_note": p.get("availability_note", ""),
            "qty_rule": p["qty_rule"],
        })
    return rows


def totals(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_sub: Dict[str, float] = {}
    by_status = {s: 0.0 for s in STATUSES}
    for r in rows:
        by_sub[r["subsystem"]] = by_sub.get(r["subsystem"], 0.0) + r["ext_price_usd"]
        by_status[r["price_status"]] += r["ext_price_usd"]
    total = sum(r["ext_price_usd"] for r in rows)
    return {
        "total_usd": round(total, 2),
        "by_subsystem": {k: round(v, 2) for k, v in sorted(by_sub.items())},
        "by_status": {k: round(v, 2) for k, v in by_status.items()},
        "confirmed_pct": round(100 * by_status["confirmed"] / total, 1) if total else 0.0,
        "items": len(rows),
        "max_lead_time_weeks": max((r["lead_time_weeks"] or 0) for r in rows) if rows else 0,
        "confirmed_pct_ex_compute": _confirmed_pct_ex_compute(rows),
    }


def _confirmed_pct_ex_compute(rows: List[Dict[str, Any]]) -> float:
    """Compute servers dominate the totals and are all 'confirmed' reseller listings, which flatters the
    headline confidence. This gives the confirmed share of everything that is not CMP-."""
    rest = [r for r in rows if r["subsystem"] != "compute"]
    tot = sum(r["ext_price_usd"] for r in rest)
    conf = sum(r["ext_price_usd"] for r in rest if r["price_status"] == "confirmed")
    return round(100 * conf / tot, 1) if tot else 0.0



# ----------------------------------------------------------------------------- output
CSV_FIELDS = ["code", "subsystem", "name", "manufacturer", "mpn", "vendor", "vendor_url", "unit", "qty",
              "unit_price_usd", "ext_price_usd", "price_status", "price_checked", "lead_time_weeks",
              "availability_note", "price_source_note", "qty_rule"]


def to_csv(rows: List[Dict[str, Any]], path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
        t = totals(rows)
        w.writerow({"code": "TOTAL", "name": f"{t['items']} lines", "ext_price_usd": t["total_usd"],
                    "price_status": f"confirmed {t['by_status']['confirmed']:.2f} / list {t['by_status']['list']:.2f} / estimate {t['by_status']['estimate']:.2f}"})
    return path


def _md_escape(s: Any) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def to_markdown(rows: List[Dict[str, Any]], cfg: Config | None = None, title: str | None = None) -> str:
    t = totals(rows)
    out: List[str] = []
    if title:
        out.append(f"# {title}\n")
    if cfg is not None:
        d = cfg.derived()
        out.append(f"**Configuration:** {d['tier_label']} · {cfg.profile} · {cfg.it_kw:.0f} kW IT in {cfg.racks} rack(s) · "
                   f"{d['cooling_label']} ({d['cooling_units_total']} units, {cfg.redundancy}) · {d['voltage']} · "
                   f"{d['service_breaker_a']} A service · UPS {d['ups_modules']} × {d['ups_kva_each']} kVA · "
                   f"battery {d['battery_kwh']} kWh · generator {'yes' if cfg.generator else 'no'} · subsystems: {', '.join(cfg.subsystems)}\n")
    out.append(f"**Total: ${t['total_usd']:,.2f}** across {t['items']} lines — "
               f"${t['by_status']['confirmed']:,.0f} confirmed ({t['confirmed_pct']}%), "
               f"${t['by_status']['list']:,.0f} list price, ${t['by_status']['estimate']:,.0f} estimate. "
               f"Confirmed share excluding compute servers: {t['confirmed_pct_ex_compute']}%. "
               f"Longest lead time in BOM: {t['max_lead_time_weeks']} weeks.\n")
    out.append("Price status key: **confirmed** = price seen on a vendor/distributor listing on the date shown (via search-result "
               "snippet; direct vendor pages were not reachable from the build environment); **list** = manufacturer published price; "
               "**estimate** = engineering estimate with basis in the note.\n")
    out.append("| Subsystem | Extended USD |\n|---|---:|")
    for k, v in t["by_subsystem"].items():
        out.append(f"| {k} | {v:,.2f} |")
    out.append("")
    out.append("| Code | Item | Mfr / MPN | Vendor | Qty | Unit | Unit USD | Ext USD | Status | Checked | Lead wk | Note |")
    out.append("|---|---|---|---|---:|---|---:|---:|---|---|---:|---|")
    for r in rows:
        vendor = f"[{_md_escape(r['vendor'])}]({r['vendor_url']})" if r.get("vendor_url") else _md_escape(r["vendor"])
        out.append("| " + " | ".join([
            r["code"], _md_escape(r["name"]), _md_escape(f"{r['manufacturer']} {r['mpn']}".strip()), vendor,
            f"{r['qty']:,}", _md_escape(r["unit"]), f"{r['unit_price_usd']:,.2f}", f"{r['ext_price_usd']:,.2f}",
            r["price_status"], r["price_checked"] or "—", str(r["lead_time_weeks"] if r["lead_time_weeks"] is not None else "—"),
            _md_escape(r["price_source_note"] + (" " + r["availability_note"] if r["availability_note"] else "")),
        ]) + " |")
    out.append("")
    return "\n".join(out)


def summary_markdown(presets: Dict[str, Config], boms: Dict[str, List[Dict[str, Any]]]) -> str:
    out = ["# BEN Engine — BOM summary (all presets)\n",
           "Generated by `python -m ben_engine.bom --all` from `purchasing/parts_catalog.json` and `ben_engine.config` presets "
           "(profile `ai_inference`, climate `temperate`, all four subsystems, no generator). Per-tier detail: "
           + ", ".join(f"[{t}](BOM-{t}.md)" for t in boms) + ". CSVs in `purchasing/bom-<tier>.csv`.\n",
           "| Tier | IT kW | Racks | Lines | Total USD | Confirmed USD | Confirmed % | Confirmed % excl. compute | List USD | Estimate USD | Max lead (wk) |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for tier, rows in boms.items():
        t = totals(rows)
        cfg = presets[tier]
        out.append(f"| {tier} | {cfg.it_kw:.0f} | {cfg.racks} | {t['items']} | {t['total_usd']:,.0f} | {t['by_status']['confirmed']:,.0f} | "
                   f"{t['confirmed_pct']} | {t['confirmed_pct_ex_compute']} | {t['by_status']['list']:,.0f} | {t['by_status']['estimate']:,.0f} | {t['max_lead_time_weeks']} |")
    out.append("")
    for tier, rows in boms.items():
        t = totals(rows)
        out.append(f"## {tier}\n")
        out.append(f"Total ${t['total_usd']:,.0f}: ${t['by_status']['confirmed']:,.0f} confirmed, ${t['by_status']['list']:,.0f} list, "
                   f"${t['by_status']['estimate']:,.0f} estimate. By subsystem: " +
                   ", ".join(f"{k} ${v:,.0f}" for k, v in t["by_subsystem"].items()) + ".\n")
        drivers = sorted(rows, key=lambda r: -r["ext_price_usd"])[:5]
        out.append("**Biggest 5 cost drivers**\n")
        for r in drivers:
            out.append(f"- {r['code']} {r['name']} — {r['qty']} × ${r['unit_price_usd']:,.0f} = **${r['ext_price_usd']:,.0f}** ({r['price_status']})")
        unc = sorted([r for r in rows if r["price_status"] != "confirmed"], key=lambda r: -r["ext_price_usd"])[:5]
        out.append("\n**Biggest 5 uncertainties (non-confirmed lines by extended value)**\n")
        for r in unc:
            out.append(f"- {r['code']} {r['name']} — **${r['ext_price_usd']:,.0f}** {r['price_status']}: {r['price_source_note']}")
        out.append("")
    return "\n".join(out)


# ----------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    import argparse
    from .config import PROFILE_DEFAULTS, CLIMATE_DESIGN

    ap = argparse.ArgumentParser(description="BEN Engine BOM generator")
    ap.add_argument("--tier", default="ben20", choices=list(TIER_GEOMETRY))
    ap.add_argument("--profile", default="ai_inference", choices=list(PROFILE_DEFAULTS))
    ap.add_argument("--climate", default="temperate", choices=list(CLIMATE_DESIGN))
    ap.add_argument("--subsystems", default="power,cooling,compute,controls", help="comma list")
    ap.add_argument("--generator", action="store_true")
    ap.add_argument("--csv", help="write CSV to this path")
    ap.add_argument("--md", help="write Markdown to this path")
    ap.add_argument("--json", action="store_true", help="print rows + totals as JSON")
    ap.add_argument("--all", action="store_true", help="write purchasing/bom-<tier>.csv, docs/BOM-<tier>.md for all presets and docs/BOM.md")
    a = ap.parse_args(argv)

    catalog = load_catalog()
    if a.all:
        presets, boms = {}, {}
        for tier in TIER_GEOMETRY:
            cfg = Config.preset(tier, a.profile, a.climate)
            if a.generator:
                cfg.generator = True
            rows = generate_bom(cfg, catalog)
            presets[tier], boms[tier] = cfg, rows
            to_csv(rows, REPO_ROOT / "purchasing" / f"bom-{tier}.csv")
            md = REPO_ROOT / "docs" / f"BOM-{tier}.md"
            md.write_text(to_markdown(rows, cfg, f"BEN Engine BOM — {cfg.derived()['tier_label']}"), encoding="utf-8")
            t = totals(rows)
            print(f"{tier:6s} {t['items']:3d} lines  ${t['total_usd']:>12,.0f}  confirmed {t['confirmed_pct']:5.1f}%")
        (REPO_ROOT / "docs" / "BOM.md").write_text(summary_markdown(presets, boms), encoding="utf-8")
        # purchasing/bom.csv = default preset (ben20) for the acceptance list
        to_csv(boms["ben20"], REPO_ROOT / "purchasing" / "bom.csv")
        return 0

    cfg = Config.preset(a.tier, a.profile, a.climate)
    cfg.subsystems = [s.strip() for s in a.subsystems.split(",") if s.strip()]
    if a.generator:
        cfg.generator = True
    rows = generate_bom(cfg, catalog)
    t = totals(rows)
    if a.csv:
        to_csv(rows, a.csv)
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(to_markdown(rows, cfg, f"BEN Engine BOM — {cfg.derived()['tier_label']}"), encoding="utf-8")
    if a.json:
        print(json.dumps({"rows": rows, "totals": t}, indent=2))
    else:
        print(f"{cfg.derived()['tier_label']}: {t['items']} lines, total ${t['total_usd']:,.2f} — "
              f"${t['by_status']['confirmed']:,.0f} confirmed ({t['confirmed_pct']}%), ${t['by_status']['list']:,.0f} list, "
              f"${t['by_status']['estimate']:,.0f} estimate")
        for k, v in t["by_subsystem"].items():
            print(f"  {k:10s} ${v:>12,.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
