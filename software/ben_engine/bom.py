"""BEN Engine bill-of-materials generator.

Reads ``purchasing/parts_catalog.json`` and a :class:`ben_engine.config.Config`, evaluates each
part's ``qty_rule`` with a tiny whitelisted expression evaluator (no ``eval``), filters by tier,
cooling type and selected subsystems, and returns priced rows plus totals by subsystem and by
price confidence (confirmed / list / estimate).

Subsystem membership is by code prefix:
    PWR -> power, CLG -> cooling, CMP -> compute, CTL -> controls.
STR / ENV / FS / SITE / SVC lines are always included when at least one subsystem is selected
(they are the enclosure, site and labour that every delivered unit needs). A part may also carry
``applies_to_cooling`` (list of cooling keys) so DX, RDHx and DLC lines do not all appear at once, and a CTL part
carries ``applies_to_controls`` (``["lite"]``, ``["pro"]`` or both) so the BEN Controls Lite (Revolution Pi + Pods)
and BEN Controls Pro (PLCnext + UL 508A panel + edge computer + Pods) lines follow ``Config.controls_tier_resolved()``
(docs/CONTROLS_HARDWARE_DECISION.md §2a). A part may carry ``applies_to_hardening`` (``["H2"]``, ``["H3"]``,
``["H2", "H3"]``) so the severe-environment and hardened/government add-ons follow ``Config.hardening``
(docs/TIER_AND_ENCLOSURE_DECISION.md §3); lines without it apply at every level (H1 baseline is IP66 everywhere).
A part may carry ``applies_to_power`` (``["ac480"]`` or ``["dc800"]``) so the AC UPS / PDU / transformer chain and the 800 VDC chain
(rectifier front end, DC busway, DC breakers, insulation monitoring, battery on the bus; docs/FORWARD_ARCHITECTURE_DECISION.md) do not
appear together; lines without it apply to both architectures.

Decision (recorded here and in purchasing/SOURCING_NOTES.md): FS lines are *not* excluded for
BEN 5. Instead the catalog carries BEN 5-specific FS parts (aerosol unit, E-stop) and the
clean-agent system applies to module and hall tiers only via ``applies_to_tiers``.

Tier keys are the generation-2 power-based keys (ben5/ben30/ben150/ben500/ben2000); ``load_catalog`` canonicalises
generation-1 keys (micro/ben10/ben20/ben40) through ``config.canonical_tier`` for catalogs that still carry them.

CLI::

    python -m ben_engine.bom --tier ben150 --csv purchasing/bom-ben150.csv --md docs/BOM-ben150.md
    python -m ben_engine.bom --all          # writes all five presets + docs/BOM.md summary
"""
from __future__ import annotations

import ast
import csv
import json
import math
import operator
from pathlib import Path
from typing import Any, Dict, List

from .config import canonical_tier, Config, TIER_GEOMETRY, TIER_ALIASES, HARDENING, TIERS_BY_LINEUP, LINEUPS

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "purchasing" / "parts_catalog.json"

PREFIX_TO_SUBSYSTEM = {"PWR": "power", "CLG": "cooling", "CMP": "compute", "CTL": "controls"}
ALWAYS_PREFIXES = ("STR", "ENV", "FS", "SITE", "SVC")
STATUSES = ("confirmed", "list", "estimate")

# Hosts that are marketplaces, aggregators or storefront platforms rather than the vendor's own product page.
# A "confirmed" price must be seen on the vendor's or distributor's own page (audit F-05, scripts/audit.py A6d).
# amazon.com is treated as not allowed because a seller cannot be told apart from the marketplace in a URL.
MARKETPLACE_HOSTS = (
    "alibaba.com", "aliexpress.com", "reach.dog", "findchips.com", "octopart.com", "ebay.com", "ebay.de",
    "amazon.com", "amazon.co.uk", "amazon.de", "craigslist.org", "pages.dev",
)
MARKETPLACE_HOST_PREFIXES = ("marketplace-admin.",)
MARKETPLACE_PATH_FRAGMENTS = ("/videos/",)

# Reader-facing label for the JSON status key "confirmed" (audit F-14): the key stays "confirmed" for the
# tests and the CSVs; the label and this definition are what BOM.md, SOURCING_NOTES and the proposal print.
CONFIRMED_LABEL = "confirmed listing"
CONFIRMED_DEFINITION = ("A confirmed listing is a price seen on the vendor's or distributor's own product page on the date shown "
                        "(read from a search-result snippet, not a quote); re-verify before purchase order.")


def _url_host(url: str) -> str:
    from urllib.parse import urlparse
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def is_marketplace_url(url: str) -> bool:
    """True if ``url`` is on a marketplace/aggregator host or a non-product path (video pages)."""
    host = _url_host(url)
    if not host:
        return True
    if any(host == h or host.endswith("." + h) for h in MARKETPLACE_HOSTS):
        return True
    if any(host.startswith(pre) for pre in MARKETPLACE_HOST_PREFIXES):
        return True
    path = url.split(host, 1)[-1].lower()
    return any(frag in path for frag in MARKETPLACE_PATH_FRAGMENTS)


def validate_price_evidence(part: Dict[str, Any]) -> None:
    """Raise ValueError if the price_status of ``part`` is not backed by the evidence its definition promises."""
    code, st = part.get("code"), part.get("price_status")
    url = (part.get("vendor_url") or "").strip()
    note = (part.get("price_source_note") or "").strip()
    if st == "confirmed":
        if not url.startswith("http"):
            raise ValueError(f"{code}: confirmed price needs the vendor_url it was seen on")
        if is_marketplace_url(url):
            raise ValueError(f"{code}: confirmed price must be on the vendor's own product page, not a marketplace/aggregator/video page ({url})")
        if not part.get("price_checked"):
            raise ValueError(f"{code}: confirmed price needs price_checked (date seen)")
    elif st == "list":
        if not url.startswith("http") and not note.startswith("MSRP"):
            raise ValueError(f"{code}: list price needs a vendor_url or a price_source_note starting 'MSRP'")

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
        validate_price_evidence(p)
    for p in cat:
        p["applies_to_tiers"] = sorted({canonical_tier(t) for t in p.get("applies_to_tiers", [])})
        if "applies_to_controls" in p and not p["applies_to_controls"]:
            del p["applies_to_controls"]
        if "applies_to_hardening" in p and not p["applies_to_hardening"]:
            del p["applies_to_hardening"]
        if "applies_to_power" in p and not p["applies_to_power"]:
            del p["applies_to_power"]
    return cat


def subsystem_of(code: str) -> str:
    prefix = code.split("-", 1)[0]
    return PREFIX_TO_SUBSYSTEM.get(prefix, prefix.lower())


def rule_variables(cfg: Config) -> Dict[str, float]:
    d = cfg.derived()
    g = cfg.geometry()
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
        # BEN Pods: two per rack (cold face, hot face) + room + outdoor per module; BEN 5 has 3. "nodes" kept as an alias.
        "pods": d["pods"],
        "nodes": d["pods"],
        "controls_pro": 1 if d["controls_tier_resolved"] == "pro" else 0,
        "tier_len_m": g["ext_l_m"],
        "generator": 1 if cfg.generator else 0,
        # generation 2 (docs/TIER_AND_ENCLOSURE_DECISION.md): MV service, modules, rows and hardening
        "transformers_total": d["transformers_total"],
        "transformer_kva": d["transformer_kva"],
        "generators_total": d["generators_total"],
        "generator_kw_each": d["generator_kw_each"],
        "modules": d["modules"],
        "rows": d["rows"],
        "racks_per_row": d["racks_per_row"],
        "mv_service": 1 if d["mv_service"] else 0,
        "hardening_H2": 1 if cfg.hardening == "H2" else 0,
        "hardening_H3": 1 if cfg.hardening == "H3" else 0,
        "hardening_H2_plus": 1 if cfg.hardening in ("H2", "H3") else 0,
        "envelope_area_m2": d["envelope_area_m2"],
        "wall_area_m2": round(2 * (g["ext_l_m"] * g["ext_h_m"] + g["ext_w_m"] * g["ext_h_m"]), 1),
        "footprint_m2": round(g["ext_l_m"] * g["ext_w_m"], 1),
        "int_volume_m3": round(g["int_l_m"] * g["int_w_m"] * g["int_h_m"], 1),
        # forward architecture (docs/FORWARD_ARCHITECTURE_DECISION.md): 800 VDC chain and the high-density liquid loop; zero when not selected
        "dc800": 1 if cfg.power_architecture == "dc800" else 0,
        "rectifier_modules": d.get("rectifier_modules", 0),
        "rectifier_cabinets": d.get("rectifier_cabinets", 0),
        "dc_busway_a": d.get("dc_busway_a", 0),
        "dc_bus_current_a": d.get("dc_bus_current_a", 0),
        "imd_count": d.get("imd_count", 0),
        "battery_on_bus_kwh": d.get("battery_on_bus_kwh", 0),
        "rack_shelves_total": d.get("rack_shelves_total", 0),
        "dlc_hd": 1 if cfg.cooling == "dlc_hd" else 0,
        "liquid_heat_kw": d.get("liquid_heat_kw", 0),
        "loop_flow_lpm": d.get("loop_flow_lpm", 0),
        "heat_reuse_kw": d.get("heat_reuse_kw_available", 0),
        # Rev 2 (docs/REV2_DECISION.md §2): liquid-first dense tiers and the BEN 1 mini rack; zero on every Rev 1 tier
        "liquid_first": 1 if d.get("liquid_first") else 0,
        "fancoils_total": d.get("fancoils_total", 0),
        "battery_cabinets": d.get("battery_cabinets", 0),
        "swbd_sections": d.get("swbd_sections", 0),
        "ups_frames": d.get("ups_frames", 0),
        "trim_loop_kw": d.get("trim_loop_kw", 0),
        "minirack": 1 if d["kind"] == "minirack" else 0,
        "form_rack10": 1 if (d["kind"] == "minirack" and cfg.form == "rack10") else 0,
        "form_cab12": 1 if (d["kind"] == "minirack" and cfg.form == "cab12") else 0,
        "ups_va": d.get("ups_va", 0),
        "ups_battery_packs": d.get("ups_battery_packs", 0),
        "controls_mini": 1 if d["controls_tier_resolved"] == "mini" else 0,
        "profile_ai": 1 if cfg.profile in ("ai_training", "ai_inference") else 0,
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
    controls_tier = cfg.controls_tier_resolved()
    rows: List[Dict[str, Any]] = []
    for p in catalog:
        if cfg.tier not in p["applies_to_tiers"]:
            continue
        cooling_filter = p.get("applies_to_cooling")
        if cooling_filter and cfg.cooling not in cooling_filter:
            continue
        controls_filter = p.get("applies_to_controls")
        if controls_filter and controls_tier not in controls_filter:
            continue
        hardening_filter = p.get("applies_to_hardening")
        if hardening_filter and cfg.hardening not in hardening_filter:
            continue
        power_filter = p.get("applies_to_power")
        if power_filter and cfg.power_architecture not in power_filter:
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
            # refrigerant-charged lines carry the refrigerant and its GWP (AIM Act < 700 from 2027-01-01, COMPLIANCE.md §0 finding 2)
            "refrigerant": p.get("refrigerant", ""), "gwp": p.get("gwp"),
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
              "availability_note", "price_source_note", "qty_rule", "refrigerant", "gwp"]
GWP_LIMIT = 700   # AIM Act Technology Transitions: data-center / IT-room cooling installed from 2027-01-01


def _gwp_cell(r: Dict[str, Any]) -> str:
    """Markdown cell for the GWP column: 'R-513A / 631' or 'R-134a / 1430 (> 700!)'; '—' for lines with no refrigerant."""
    if r.get("gwp") is None:
        return "—"
    name = str(r.get("refrigerant", "")).split(" — ")[0].split(" (")[0].strip() or "?"
    flag = "" if r["gwp"] < GWP_LIMIT else f" (> {GWP_LIMIT}!)"
    return f"{name} / {r['gwp']}{flag}"


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
        if cfg.power_architecture == "dc800":
            power_txt = (f"{d['voltage']} service · {d['service_breaker_a']} A · **800 VDC bus**, {d['dc_convention_label']} ({d['dc_bus_v_min']}–{d['dc_bus_v_max']} V window: {d['dc_window_basis']}): "
                         f"AC/DC front end {d['ac_dc_front_end_kw']} kW, {d['rectifier_modules']} × {d['rectifier_module_kw']} kW rectifier modules ({cfg.redundancy}), "
                         f"bus {d['dc_bus_current_a']} A → {d['dc_busway_a']} A busway, {d['imd_count']} insulation monitors · {d['rack_shelves_total']} × {d['rack_shelf_kw']} kW 800 V → 50 V rack shelves "
                         f"(efficiencies are vendor claims) · battery on bus {d['battery_on_bus_kwh']} kWh (800 V class, no UPS)")
        else:
            power_txt = f"{d['voltage']} · {d['service_breaker_a']} A service · UPS {d['ups_modules']} × {d['ups_kva_each']} kVA · battery {d['battery_kwh']} kWh"
        loop_txt = (f" · W45 loop {d['loop_flow_lpm']} L/min at ΔT {d['loop_dt_design_k']:.0f} K, heat reuse {d['heat_reuse_kw_available']} kW available"
                    if cfg.cooling == "dlc_hd" else "")
        out.append(f"**Configuration:** {d['tier_label']} · {cfg.profile} · {d['hardening_label']} · {cfg.it_kw:.0f} kW IT in {cfg.racks} rack(s) · "
                   f"{d['cooling_label']} ({d['cooling_units_total']} units, {cfg.redundancy}){loop_txt} · {power_txt} · generator {'yes' if cfg.generator else 'no'} · controls: {d['controls_label']} "
                   f"({d['pods']} BEN Pods) · subsystems: {', '.join(cfg.subsystems)}\n")
    out.append(f"**Total: ${t['total_usd']:,.2f}** across {t['items']} lines — "
               f"${t['by_status']['confirmed']:,.0f} {CONFIRMED_LABEL} ({t['confirmed_pct']}%), "
               f"${t['by_status']['list']:,.0f} list price, ${t['by_status']['estimate']:,.0f} estimate. "
               f"Confirmed-listing share excluding compute servers: {t['confirmed_pct_ex_compute']}%. "
               f"Longest lead time in BOM: {t['max_lead_time_weeks']} weeks.\n")
    out.append(f"Price status key: **{CONFIRMED_LABEL}** (JSON key `confirmed`) — {CONFIRMED_DEFINITION} "
               "Direct vendor pages were not reachable from the build environment. **list** = manufacturer published price (URL or MSRP note); "
               "**estimate** = engineering estimate with basis in the note.\n")
    out.append("| Subsystem | Extended USD |\n|---|---:|")
    for k, v in t["by_subsystem"].items():
        out.append(f"| {k} | {v:,.2f} |")
    out.append("")
    has_gwp = any(r.get("gwp") is not None for r in rows)   # GWP column present when the BOM holds a refrigerant-charged line
    gwp_h = " Refrigerant / GWP |" if has_gwp else ""
    out.append(f"| Code | Item | Mfr / MPN | Vendor | Qty | Unit | Unit USD | Ext USD | Status | Checked | Lead wk |{gwp_h} Note |")
    out.append("|---|---|---|---|---:|---|---:|---:|---|---|---:|" + ("---|" if has_gwp else "") + "---|")
    for r in rows:
        vendor = f"[{_md_escape(r['vendor'])}]({r['vendor_url']})" if r.get("vendor_url") else _md_escape(r["vendor"])
        cells = [
            r["code"], _md_escape(r["name"]), _md_escape(f"{r['manufacturer']} {r['mpn']}".strip()), vendor,
            f"{r['qty']:,}", _md_escape(r["unit"]), f"{r['unit_price_usd']:,.2f}", f"{r['ext_price_usd']:,.2f}",
            r["price_status"], r["price_checked"] or "—", str(r["lead_time_weeks"] if r["lead_time_weeks"] is not None else "—"),
        ]
        if has_gwp:
            cells.append(_gwp_cell(r))
        cells.append(_md_escape(r["price_source_note"] + (" " + r["availability_note"] if r["availability_note"] else "")))
        out.append("| " + " | ".join(cells) + " |")
    if has_gwp:
        bad = [r for r in rows if r.get("gwp") is not None and r["gwp"] >= GWP_LIMIT]
        out.append("")
        out.append(f"Refrigerant / GWP column: every refrigerant-charged line carries `refrigerant` and `gwp` from the catalog; the AIM Act limit for "
                   f"data-center cooling installed from 2027-01-01 is GWP < {GWP_LIMIT} (`docs/COMPLIANCE.md` §0 finding 2). "
                   + (f"**{len(bad)} line(s) exceed the limit: " + ", ".join(f"{r['code']} ({r['gwp']})" for r in bad) + " — see the RFQ note on the catalog line.**"
                      if bad else "All lines are below the limit."))
    out.append("")
    return "\n".join(out)


def summary_markdown(presets: Dict[str, Config], boms: Dict[str, List[Dict[str, Any]]], lineup: str = "rev1") -> str:
    if lineup == "rev2":
        return summary_markdown_rev2(presets, boms)
    out = ["# BEN Engine — BOM summary (all presets)\n",
           "Generated by `python -m ben_engine.bom --all` from `purchasing/parts_catalog.json` and `ben_engine.config` presets "
           "(profile `ai_inference`, climate `temperate`, hardening H1, all four subsystems; generator only where the preset carries one — BEN 2000 always has N+1 generators). Per-tier detail: "
           + ", ".join(f"[{t}](BOM-{t}.md)" for t in boms) + ". CSVs in `purchasing/bom-<tier>.csv`.\n",
           f"**Status labels.** *Confirmed listing* (JSON key `confirmed`): {CONFIRMED_DEFINITION} "
           "*List* = manufacturer published price. *Estimate* = engineering estimate with its basis in the line note. "
           "Nothing in this BOM is a quote.\n",
           "| Tier | IT kW | Racks | Lines | Total USD | Confirmed listing USD | Confirmed listing % | Confirmed listing % excl. compute | List USD | Estimate USD | Max lead (wk) |",
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
        out.append(f"Total ${t['total_usd']:,.0f}: ${t['by_status']['confirmed']:,.0f} {CONFIRMED_LABEL}, ${t['by_status']['list']:,.0f} list, "
                   f"${t['by_status']['estimate']:,.0f} estimate. By subsystem: " +
                   ", ".join(f"{k} ${v:,.0f}" for k, v in t["by_subsystem"].items()) + ".\n")
        drivers = sorted(rows, key=lambda r: -r["ext_price_usd"])[:5]
        out.append("**Biggest 5 cost drivers**\n")
        for r in drivers:
            out.append(f"- {r['code']} {r['name']} — {r['qty']} × ${r['unit_price_usd']:,.0f} = **${r['ext_price_usd']:,.0f}** ({r['price_status']})")
        unc = sorted([r for r in rows if r["price_status"] != "confirmed"], key=lambda r: -r["ext_price_usd"])[:5]
        out.append("\n**Biggest 5 uncertainties (lines without a confirmed listing, by extended value)**\n")
        for r in unc:
            out.append(f"- {r['code']} {r['name']} — **${r['ext_price_usd']:,.0f}** {r['price_status']}: {r['price_source_note']}")
        out.append("")
    return "\n".join(out)


def summary_markdown_rev2(presets: Dict[str, Config], boms: Dict[str, List[Dict[str, Any]]]) -> str:
    """Rev 2 summary (docs/rev2/BOM.md). The Rev 1 summary in docs/BOM.md is frozen."""
    out = ["# BEN Engine Rev 2 — BOM summary (all Rev 2 presets)\n",
           "Generated by `python -m ben_engine.bom --all --lineup rev2` from `purchasing/parts_catalog.json` and the Rev 2 presets "
           "(profile `ai_inference`, climate `temperate`, all four subsystems). Rev 1 BOMs stay in `docs/BOM.md` and `purchasing/bom-<tier>.csv` unchanged. "
           "Per-tier detail: " + ", ".join(f"[{t}](BOM-{t}.md)" for t in boms) + ". CSVs in `purchasing/rev2/bom-<tier>.csv`.\n",
           f"**Status labels.** *Confirmed listing* (JSON key `confirmed`): {CONFIRMED_DEFINITION} *List* = manufacturer published price. "
           "*Estimate* = engineering estimate with its basis in the line note. Nothing in this BOM is a quote. "
           "Compute lines (`CMP-`) on BEN 1, BEN 300 and BEN 700 are **customer-selectable**: most buyers bring their own; the column excluding compute is the BEN Engine scope.\n",
           "| Tier | IT kW | Racks | Lines | Total USD | Excl. compute USD | Confirmed USD | List USD | Estimate USD | Confirmed % excl. compute | Max lead (wk) |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for tier, rows in boms.items():
        t = totals(rows)
        cfg = presets[tier]
        ex = sum(r["ext_price_usd"] for r in rows if r["subsystem"] != "compute")
        kw = f"{cfg.it_kw:g}"
        out.append(f"| {tier}{' (' + cfg.form + ')' if cfg.form else ''} | {kw} | {cfg.racks} | {t['items']} | {t['total_usd']:,.0f} | {ex:,.0f} | {t['by_status']['confirmed']:,.0f} | "
                   f"{t['by_status']['list']:,.0f} | {t['by_status']['estimate']:,.0f} | {t['confirmed_pct_ex_compute']} | {t['max_lead_time_weeks']} |")
    out.append("")
    for tier, rows in boms.items():
        t = totals(rows)
        out.append(f"## {tier}\n")
        out.append(f"Total ${t['total_usd']:,.0f}: ${t['by_status']['confirmed']:,.0f} {CONFIRMED_LABEL}, ${t['by_status']['list']:,.0f} list, "
                   f"${t['by_status']['estimate']:,.0f} estimate. By subsystem: " + ", ".join(f"{k} ${v:,.0f}" for k, v in t["by_subsystem"].items()) + ".\n")
        out.append("**Biggest 5 cost drivers**\n")
        for r in sorted(rows, key=lambda r: -r["ext_price_usd"])[:5]:
            out.append(f"- {r['code']} {r['name']} — {r['qty']} × ${r['unit_price_usd']:,.0f} = **${r['ext_price_usd']:,.0f}** ({r['price_status']})")
        out.append("\n**Biggest 5 uncertainties (lines without a confirmed listing, by extended value)**\n")
        for r in sorted([r for r in rows if r["price_status"] != "confirmed"], key=lambda r: -r["ext_price_usd"])[:5]:
            out.append(f"- {r['code']} {r['name']} — **${r['ext_price_usd']:,.0f}** {r['price_status']}: {r['price_source_note']}")
        out.append("")
    return "\n".join(out)


def write_lineup(lineup: str, profile: str = "ai_inference", climate: str = "temperate", catalog=None, quiet: bool = False) -> Dict[str, Dict[str, Any]]:
    """Write every preset BOM of ``lineup``. rev1 -> purchasing/bom-<tier>.csv, docs/BOM-<tier>.md, docs/BOM.md (frozen Rev 1 locations);
    rev2 -> purchasing/rev2/bom-<tier>.csv, docs/rev2/BOM-<tier>.md, docs/rev2/BOM.md (docs/REVISION_POLICY.md rule 2)."""
    catalog = catalog if catalog is not None else load_catalog()
    presets, boms = {}, {}
    csv_dir = REPO_ROOT / "purchasing" if lineup == "rev1" else REPO_ROOT / "purchasing" / "rev2"
    md_dir = REPO_ROOT / "docs" if lineup == "rev1" else REPO_ROOT / "docs" / "rev2"
    md_dir.mkdir(parents=True, exist_ok=True)
    for tier in TIERS_BY_LINEUP[lineup]:
        cfg = Config.preset(tier, profile, climate, lineup=lineup)
        rows = generate_bom(cfg, catalog)
        presets[tier], boms[tier] = cfg, rows
        to_csv(rows, csv_dir / f"bom-{tier}.csv")
        title = f"BEN Engine {'Rev 2 ' if lineup == 'rev2' else ''}BOM — {cfg.derived()['tier_label']}" + (f" ({cfg.form})" if cfg.form else "")
        (md_dir / f"BOM-{tier}.md").write_text(to_markdown(rows, cfg, title), encoding="utf-8")
        t = totals(rows)
        if not quiet:
            print(f"{tier:7s} {t['items']:3d} lines  ${t['total_usd']:>14,.0f}  confirmed {t['confirmed_pct']:5.1f}%")
    (md_dir / "BOM.md").write_text(summary_markdown(presets, boms, lineup), encoding="utf-8")
    return {t: totals(r) for t, r in boms.items()}


# ----------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    import argparse
    from .config import PROFILE_DEFAULTS, CLIMATE_DESIGN, POWER_ARCHITECTURES, COOLING_LIBRARY

    ap = argparse.ArgumentParser(description="BEN Engine BOM generator")
    ap.add_argument("--tier", default="ben150", choices=list(TIER_GEOMETRY) + list(TIER_ALIASES))
    ap.add_argument("--profile", default="ai_inference", choices=list(PROFILE_DEFAULTS))
    ap.add_argument("--climate", default="temperate", choices=list(CLIMATE_DESIGN))
    ap.add_argument("--subsystems", default="power,cooling,compute,controls", help="comma list")
    ap.add_argument("--generator", action="store_true")
    ap.add_argument("--hardening", choices=list(HARDENING), help="enclosure hardening level (default: preset rule)")
    ap.add_argument("--power-architecture", dest="power_architecture", choices=list(POWER_ARCHITECTURES), help="ac480 (default) or dc800 (forward option)")
    ap.add_argument("--cooling", choices=list(COOLING_LIBRARY), help="override the preset cooling (e.g. dlc_hd)")
    ap.add_argument("--it-kw", dest="it_kw", type=float, help="override the preset IT load")
    ap.add_argument("--racks", type=int, help="override the preset rack count")
    ap.add_argument("--redundancy", choices=["N", "N+1", "2N"], help="override the preset redundancy")
    ap.add_argument("--title", help="Markdown title override (single-config mode)")
    ap.add_argument("--csv", help="write CSV to this path")
    ap.add_argument("--md", help="write Markdown to this path")
    ap.add_argument("--json", action="store_true", help="print rows + totals as JSON")
    ap.add_argument("--all", action="store_true", help="write purchasing/bom-<tier>.csv, docs/BOM-<tier>.md for all presets and docs/BOM.md")
    ap.add_argument("--lineup", default="rev1", choices=list(LINEUPS),
                    help="--all: rev1 (default) rewrites the frozen Rev 1 outputs; rev2 writes purchasing/rev2/ and docs/rev2/. Single config: preset lineup")
    ap.add_argument("--form", choices=["rack10", "cab12"], help="BEN 1 form")
    a = ap.parse_args(argv)

    catalog = load_catalog()
    if a.all and a.lineup == "rev2":
        write_lineup("rev2", a.profile, a.climate, catalog)
        return 0
    if a.all:
        presets, boms = {}, {}
        for tier in TIERS_BY_LINEUP["rev1"]:
            cfg = Config.preset(tier, a.profile, a.climate, lineup="rev1")
            if a.generator:
                cfg.generator = True
            if a.hardening:
                cfg.hardening = a.hardening
            rows = generate_bom(cfg, catalog)
            presets[tier], boms[tier] = cfg, rows
            to_csv(rows, REPO_ROOT / "purchasing" / f"bom-{tier}.csv")
            md = REPO_ROOT / "docs" / f"BOM-{tier}.md"
            md.write_text(to_markdown(rows, cfg, f"BEN Engine BOM — {cfg.derived()['tier_label']}"), encoding="utf-8")
            t = totals(rows)
            print(f"{tier:6s} {t['items']:3d} lines  ${t['total_usd']:>12,.0f}  confirmed {t['confirmed_pct']:5.1f}%")
        (REPO_ROOT / "docs" / "BOM.md").write_text(summary_markdown(presets, boms), encoding="utf-8")
        # purchasing/bom.csv = default preset (ben150) for the acceptance list
        to_csv(boms["ben150"], REPO_ROOT / "purchasing" / "bom.csv")
        return 0

    tier = canonical_tier(a.tier)
    lineup = a.lineup if tier in TIERS_BY_LINEUP[a.lineup] else "rev2"
    cfg = Config.preset(tier, a.profile, a.climate, lineup=lineup, form=a.form)
    cfg.subsystems = [s.strip() for s in a.subsystems.split(",") if s.strip()]
    if a.generator:
        cfg.generator = True
    if a.hardening:
        cfg.hardening = a.hardening
    for k in ("power_architecture", "cooling", "it_kw", "racks", "redundancy"):
        if getattr(a, k) is not None:
            setattr(cfg, k, getattr(a, k))
    rows = generate_bom(cfg, catalog)
    t = totals(rows)
    if a.csv:
        to_csv(rows, a.csv)
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(to_markdown(rows, cfg, a.title or f"BEN Engine BOM — {cfg.derived()['tier_label']}"), encoding="utf-8")
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
