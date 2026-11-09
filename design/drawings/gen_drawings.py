"""BEN Engine — drawing set generator (revision and status from design/REVISION.json).

Reads the configuration for each tier preset through design/layout.py and writes, per tier:
    design/drawings/<tier>/A-001 ... C-001 as .svg and .png, plus INDEX.md
and design/drawings/INTERFERENCE_CHECKS.md (all tiers) which DESIGN_BASIS.md embeds.
Tiers: ben5 (NEMA 4X / IP66 cabinet), ben30 / ben150 / ben500 (ISO-frame modules sealed to IP66) and ben2000 (the hall:
A-000 site plan, per-module A-001-Mn / A-002-Mn sheets, MV one-line; generators in gen_hall.py). Every A-003 carries the
IP66 penetration detail and the hardening add-ons (H1/H2/H3, docs/TIER_AND_ENCLOSURE_DECISION.md §3).

Run:  python design/drawings/gen_drawings.py [--tier ben150] [--dpi 110]
"""
from __future__ import annotations

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import layout as L  # noqa: E402
import ctq as C  # noqa: E402
import gen_hall as GH  # noqa: E402
from revision import REV  # noqa: E402
from drawkit import (Sheet, View, INK, MUTED, LIGHT, PAPER, CTQ_C, CTP_C, RED, GREEN, PURPLE, FILL, EDGE,  # noqa: E402
                     sym_box, sym_valve, sym_pump, sym_instr, sym_hx, sym_tank, sym_breaker)

DATE = REV["issue_date"]          # from design/REVISION.json — do not hard-code
SHEETS = [("A-001", "General arrangement"), ("A-002", "Interior layout plan"), ("A-003", "Envelope section and hardening"),
          ("S-001", "Floor framing and anchoring"), ("E-001", "Power one-line"), ("M-001", "Cooling P&ID"),
          ("C-001", "Controls layout")]


FORWARD_SHEETS = [("E-001", "Power one-line — 800 VDC bus (forward study)"), ("M-001", "Cooling P&ID — high-density liquid W45 loop (forward study)")]
# Set by main(--forward): the forward prototype set is a study, generated for review beside the Rev C tier sets (change register DC-002)
STATUS_OVERRIDE = None
FORWARD_DIR = "forward-ben150"


def sheets_for(lay):
    if lay.notes.get("forward"):
        return FORWARD_SHEETS
    return GH.hall_sheets(lay) if lay.is_hall else SHEETS
RX = 500.0          # right column x
RW = 326.0          # right column width
TOP = 578.0
STD_BRK = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 600, 700, 800, 1000, 1200]


def std(a):
    return next((b for b in STD_BRK if b >= a), 1200)


def pick_scale(*constraints):
    """constraints: (length_mm, avail_sheet_mm). Return smallest standard scale satisfying all."""
    for s in (5, 10, 15, 20, 25, 30, 40, 50, 75, 100):
        if all(l / s <= a for l, a in constraints):
            return s
    return 100


def config_line(lay):
    cfg, d = lay.cfg, lay.d
    pw = f" | {cfg.power_architecture} {cfg.dc_convention}" if cfg.power_architecture == "dc800" else ""
    return f"{cfg.tier} | {cfg.profile} | {cfg.it_kw:.0f} kW IT | {cfg.racks} racks | cooling {lay.notes.get('cooling_resolved', cfg.cooling)}{pw} | {cfg.redundancy} | {cfg.climate} | {cfg.hardening}"


def new_sheet(lay, no, title, scale_text, n):
    return Sheet(no, title, lay.d["tier_label"], scale_text, n, len(sheets_for(lay)), config_line(lay), DATE)


def _refrigerant_note(lay):
    """Refrigerant / charge note for M-001 on DX tiers, from the catalog lines' `refrigerant` / `gwp` attributes
    (purchasing/parts_catalog.json; COMPLIANCE.md §0 findings 1 and 2: A1 refrigerant, GWP < 700)."""
    import json
    cat_path = os.path.join(os.path.dirname(os.path.dirname(HERE)), "purchasing", "parts_catalog.json")
    with open(cat_path, encoding="utf-8") as f:
        cat = {p["code"]: p for p in json.load(f)}
    codes = ["CLG-CABAC"] if not lay.is_container else ["CLG-INROW", "CLG-COND", "CLG-REFRIG"]
    parts = [cat[c] for c in codes if c in cat and c in cat and "gwp" in cat[c]]
    vol = lay.L * lay.W * lay.H / 1e9
    if not parts:
        return ("Refrigerant: per unit nameplate — catalog line carries no `refrigerant` attribute; add it before purchase.", f"Room volume {vol:.1f} m3.")
    p = parts[0]
    gwp = p["gwp"]
    ok = "meets" if gwp < 700 else "DOES NOT MEET"
    name = p['refrigerant'].split(' — ')[0].split(' (')[0].strip()
    line1 = (f"Refrigerant: {name} (catalog {', '.join(codes)}), GWP {gwp} — {ok} the AIM Act < 700 GWP limit for data-center cooling from 2027-01-01 (COMPLIANCE §0 finding 2).")
    if lay.is_container:
        line2 = (f"A1 (non-flammable) refrigerant, so UL 60335-2-40 / ASHRAE 15 A2L charge limits do not apply; room volume {vol:.1f} m3; charge per unit nameplate, "
                 "record the charge per circuit on form Q-06 (CTP-M1 HOLD). No A2L unit may be substituted without a new charge-vs-volume check.")
    else:
        line2 = (f"Cabinet volume {vol:.2f} m3, sealed and not for human occupancy. " + ("Factory-sealed unit, no field charge." if gwp < 700 else
                 "RFQ NOTE: the 5.8 kW rating is the R-134a variant (GWP 1430); purchasing must quote the R-513A variant (5.5 kW, GWP 631) or an R-1234yf / R-516A unit before release."))
    return (line1, line2)


def deviation_note(sh, lay, x, y):
    if not lay.deviations:
        return y
    sh.text(x, y, "CONFIGURATION DEVIATIONS APPLIED ON THIS SET", h=2.8, bold=True, c=RED)
    yy = y - 4.5
    for dv in lay.deviations:
        for ln in _wrap(dv, 150):
            sh.text(x, yy, ln, h=2.0, c=RED); yy -= 3.0
        yy -= 1.0
    return yy - 2


def _wrap(s, n):
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


def right_column(sh, lay, sheet_no, extra=None):
    """CTQ table at top of right column, then optional extra callable(sh, x, y) -> y, then deviations."""
    items = C.for_sheet(C.register(lay), sheet_no)
    y = sh.ctq_table(items, RX, TOP - 6, w=RW)
    y -= 8
    if extra:
        y = extra(sh, RX, y)
    y -= 4
    deviation_note(sh, lay, RX, y)


# ====================================================================== A-001
def sheet_a001(lay: L.Layout, out):
    s = pick_scale((lay.ext_l + 2600, 470), (lay.ext_w + 2 * lay.ext_h + 1300, 500))
    sh = new_sheet(lay, "A-001", "General arrangement", f"1:{s}", 1)
    el, ew, eh = lay.ext_l, lay.ext_w, lay.ext_h
    wall = (ew - lay.W) / 2 if lay.is_container else (ew - lay.W) / 2
    endw = (el - lay.L) / 2
    ox = 30.0
    # ----- roof plan (top)
    y_plan_top = TOP - 14
    oy = y_plan_top - ew / s - 10
    v = View(sh, s, ox, oy)
    sh.view_title(ox, y_plan_top + 6, "ROOF PLAN", f"1:{s}")
    v.rect(0, 0, el, ew, lw=1.0)
    if lay.is_container:
        v.corrugation(0, el, 0, ew, pitch=310, vertical=False)   # roof bows (schematic)
        for (X, Y) in ((0, 0), (el - 178, 0), (0, ew - 162), (el - 178, ew - 162)):
            v.rect(X, Y, X + 178, Y + 162, fc="#E8EDF3", lw=0.8)
        # roof penetrations: one line-set curb per condenser; dry cooler pipes through end wall
        for it in lay.items:
            if it.mount == "roof":
                X0 = it.x0 + endw; Y0 = it.y0 + wall
                v.rect(X0, Y0, X0 + it.w, Y0 + it.d, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6, ls="--")
                v.text((X0 + X0 + it.w) / 2, Y0 + it.d / 2, it.tag, h=2.0, ha="center", va="center", bold=True)
                cx, cy = X0 + it.w / 2, Y0 - 150 + 300  # curb 300 inboard of rail
                v.rect(cx - 150, wall + 300 - 100, cx + 150, wall + 300 + 100, fc=PAPER, ec=RED, lw=0.8)
                v.text(cx, wall + 300 + 110, "RP", h=1.7, ha="center", va="bottom", c=RED)
        # cable / power entry on end wall (shown in END VIEW); roof penetration for antenna/GPS
        v.text(el / 2, ew + 60, "DOOR END  <----", h=2.2, ha="right", c=MUTED)
        v.text(el - 10, ew + 60, "BLIND END (service section exterior)", h=2.2, ha="right", c=MUTED)
        v.text(10, ew + 60, "DOOR END", h=2.2, ha="left", c=MUTED)
    else:
        v.rect(0, 0, el, ew, fc="#F4F7FB", lw=0.8)
        v.text(el / 2, ew / 2, "CABINET ROOF (sloped 3 deg, drip edge)", h=2.0, ha="center", va="center", c=MUTED)
        for it in lay.items:
            if it.mount == "ext" and it.kind == "cooling":
                X0 = it.x0 + endw; Y0 = it.y0 + wall
                v.rect(X0, Y0, X0 + it.w, Y0 + it.d, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6)
                v.text(X0 + it.w / 2, Y0 + it.d / 2, it.tag, h=1.8, ha="center", va="center", bold=True)
    v.dim_h(0, el, ew, 16 + (6 if lay.is_container else 0), label=f"{el:.0f}")
    v.dim_v(0, ew, 0, -8, label=f"{ew:.0f}")
    rp_items = [i for i in lay.items if i.mount == "roof"]
    if rp_items:
        v.dim_v(wall, wall + 300, el, 8, label="300 (to curb)", side="right")
        v.bubble(rp_items[0].x0 + endw + 150, wall + 300, 20, 14, "CTP-A1", "CTP")
    # ----- end view (door end), right of plan
    ox_end = ox + el / s + 40
    ve = View(sh, s, ox_end, oy - (eh - ew) / s)
    sh.view_title(ox_end, y_plan_top + 6, "END VIEW — DOOR END", f"1:{s}")
    ve.rect(0, 0, ew, eh, lw=1.0)
    if lay.is_container:
        ve.rect(0, 0, 178, 118, fc="#E8EDF3", lw=0.6); ve.rect(ew - 178, 0, ew, 118, fc="#E8EDF3", lw=0.6)
        ve.rect(0, eh - 118, 178, eh, fc="#E8EDF3", lw=0.6); ve.rect(ew - 178, eh - 118, ew, eh, fc="#E8EDF3", lw=0.6)
        ve.line(ew / 2, 160, ew / 2, eh - 160, lw=0.6)   # door split
        for X in (ew * 0.3, ew * 0.42, ew * 0.58, ew * 0.7):   # lock bars
            ve.line(X, 250, X, eh - 250, c=MUTED, lw=0.8)
        ve.text(ew / 2, eh + 60, "CARGO DOORS 2 LEAF, 270 deg, GASKETED", h=1.8, ha="center", va="bottom", c=MUTED)
        ve.rect(ew * 0.75, 1200, ew * 0.75 + 150, 1350, fc=FILL["fire"], ec=RED, lw=0.6)
        ve.text(ew * 0.75 + 170, 1270, "EPO (ext)", h=1.6, va="center", c=RED)
    else:
        ve.rect(60, 150, ew - 60, eh - 100, lw=0.6); ve.text(ew / 2, eh / 2, "DOOR\nNEMA 4X / IP66\ncompression gasket\n3-point latch", h=1.8, ha="center", va="center", c=MUTED)
    ve.dim_v(0, eh, ew, 8, label=f"{eh:.0f}", side="right")
    ve.dim_h(0, ew, 0, -8, label=f"{ew:.0f}")
    # ----- side elevation A (rack-wall side)
    y_elevA_top = oy - 24
    oyA = y_elevA_top - eh / s - (800 / s if rp_items else 0)
    va = View(sh, s, ox, oyA)
    sh.view_title(ox, y_elevA_top + 2, "ELEVATION A — RACK-WALL SIDE", f"1:{s}")
    va.rect(0, 0, el, eh, lw=1.0)
    if lay.is_container:
        va.corrugation(0, el, 0, eh, pitch=280, vertical=True)
        for X in (0, el - 178):
            va.rect(X, 0, X + 178, 118, fc="#E8EDF3", lw=0.6); va.rect(X, eh - 118, X + 178, eh, fc="#E8EDF3", lw=0.6)
        for it in rp_items:
            X0 = it.x0 + endw
            va.rect(X0, eh, X0 + it.w, eh + 700, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6)
            va.text(X0 + it.w / 2, eh + 350, it.tag, h=1.8, ha="center", va="center", bold=True)
            va.rect(X0 + it.w / 2 - 150, eh, X0 + it.w / 2 + 150, eh + 120, fc=PAPER, ec=RED, lw=0.6)
        if rp_items:
            va.dim_v(eh, eh + 700, el, 8, label="700", side="right")
        if lay.find("DC1"):
            for k, zz in enumerate((2100, 2300)):
                va.circle(el - 500, zz, 60, fc=PAPER, ec=EDGE["cooling"], lw=0.7)
            va.leader(el - 500, 2300, -14, 10, "2 x DN65 sleeved pipe penetrations to dry cooler (end wall, CTP-A1)", h=1.8)
        svc = lay.find("SVC")
        if svc:
            va.rect(el, svc.z0, el + 400, svc.z1, fc=FILL["power"], ec=EDGE["power"], lw=0.6)
            va.text(el + 200, (svc.z0 + svc.z1) / 2, "SVC", h=1.8, ha="center", va="center", bold=True, rot=90)
            va.leader(el + 400, svc.z1 - 100, 6, 6, f"Service section NEMA 4X, {lay.d['service_breaker_a']} A", h=1.9)
    else:
        for it in lay.items:
            if it.mount == "ext" and it.kind == "cooling" and it.y0 < 0:
                X0 = it.x0 + endw
                va.rect(X0, it.z0, X0 + it.w, it.z1, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6)
                va.text(X0 + it.w / 2, (it.z0 + it.z1) / 2, it.tag, h=2.0, ha="center", va="center", bold=True)
        va.rect(0, -150, el, 0, fc="#E8EDF3", lw=0.8); va.text(el / 2, -75, "SKID", h=1.8, ha="center", va="center")
    va.dim_h(0, el, 0, -8, label=f"{el:.0f}")
    va.dim_v(0, eh, 0, -8, label=f"{eh:.0f}")
    va.text(0, -14 / s * s - 0 - (16 if True else 0) * 0 - 300, "", h=1)
    # ----- side elevation B (aisle side) with brand panel
    y_elevB_top = oyA - 22
    oyB = y_elevB_top - eh / s
    vb = View(sh, s, ox, oyB)
    sh.view_title(ox, y_elevB_top + 2, "ELEVATION B — AISLE SIDE (BRAND PANEL)", f"1:{s}")
    vb.rect(0, 0, el, eh, lw=1.0)
    if lay.is_container:
        vb.corrugation(0, el, 0, eh, pitch=280, vertical=True)
        for X in (0, el - 178):
            vb.rect(X, 0, X + 178, 118, fc="#E8EDF3", lw=0.6); vb.rect(X, eh - 118, X + 178, eh, fc="#E8EDF3", lw=0.6)
        pw = min(el * 0.45, 3000)
        vb.rect(el / 2 - pw / 2, eh * 0.35, el / 2 + pw / 2, eh * 0.65, fc="#0B1018", ec="#0B1018")
        vb.text(el / 2, eh * 0.5, f"SCHREIBER AI  |  {lay.d['tier_label'].upper()}", h=min(3.4, 7000 / s / 10), ha="center", va="center", c="#66E3FF", bold=True)
        vb.text(el / 2, eh * 0.3, "Brand panel: 1.5 mm aluminium composite, bonded + riveted; no penetration", h=1.7, ha="center", va="top", c=MUTED)
    else:
        for it in lay.items:
            if it.mount == "ext" and it.kind == "cooling" and it.y0 > 0:
                X0 = it.x0 + endw
                vb.rect(X0, it.z0, X0 + it.w, it.z1, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6)
                vb.text(X0 + it.w / 2, (it.z0 + it.z1) / 2, it.tag, h=2.0, ha="center", va="center", bold=True)
        vb.rect(el * 0.1, eh * 0.75, el * 0.9, eh * 0.9, fc="#0B1018", ec="#0B1018")
        vb.text(el / 2, eh * 0.825, f"SCHREIBER AI | {lay.d['tier_label'].upper()}", h=2.4, ha="center", va="center", c="#66E3FF", bold=True)
    vb.dim_h(0, el, 0, -8, label=f"{el:.0f}")
    sh.north_arrow(ox_end + ew / s / 2, oy - (eh - ew) / s - 30)
    sh.text(ox_end - 10, oy - (eh - ew) / s - 50, "Dimensions in mm. Ext dims per ISO 668 (containers).", h=2.0, c=MUTED)

    def extra(sh, x, y):
        d = lay.d
        masses = [(i.label, i.kg) for i in lay.items if i.kg]
        tot = sum(m for _, m in masses)
        cgx = sum(i.kg * (i.cx + endw) for i in lay.items if i.kg and i.mount != "ext" or i.mount == "roof") / max(1, sum(i.kg for i in lay.items if i.kg and (i.mount != "ext" or i.mount == "roof")))
        rows = [["Enclosure tare (ISO / cabinet)", f"{d['geometry']['tare_kg']}"],
                ["Payload (config rule)", f"{d['payload_kg']}"],
                ["Payload (layout item sum, incl. exterior)", f"{tot:.0f}"],
                ["GROSS (config)", f"{d['gross_kg']}"],
                ["Per corner post (gross / 4, static)", f"{d['gross_kg'] / 4:.0f}"],
                ["Longitudinal CoG from door end (layout)", f"{cgx:.0f} mm  ({cgx / el * 100:.0f} % of L)"],
                ["Max gross ISO 668 (module) / forklift (BEN 5)", "30480" if lay.is_container else "2500"]]
        y = sh.table(x, y, ["WEIGHT TABLE", "kg"], rows, [RW * 0.72, RW * 0.28], title="WEIGHTS")
        y -= 8
        y = sh.revision_table(x, y, RW)
        y -= 8
        notes = [
            "All dimensions in millimetres unless noted. Do not scale from this drawing; use figured dimensions.",
            "Enclosure: " + d["enclosure"] + f". Envelope {d['hardening_rating']}; coating {d['hardening_coating']} (site class {d['climate']['corrosion']}, ISO 9223). Hardening {d['hardening_label']}: add-ons on A-003.",
            "Every penetration is a gasketed transit frame or a sleeved and gasketed entry, hose-tested per UL 50E type 4X (CTQ-A4 WITNESS); doors have compression gaskets and three-point latches (CTQ-C3); interior at +10 Pa.",
            "Every cutout in the container shell is reinforced with a welded 50x50x5 frame (CTP-A1, HOLD POINT, certified welder). Cutouts within 300 mm of a corner post are not permitted.",
            "After modification the container is re-inspected and re-plated (CSC, CTP-A2) before road or sea transport.",
            "Roof penetrations (RP) are line-set curbs 300x200, 300 mm inboard of the top side rail, sealed with EPDM boot and butyl; see A-003 detail.",
            "Brand panel is bonded + riveted to corrugation crests; no through-fastener into the insulated zone.",
            "Weight table: payload from the configuration rule (software/ben_engine/config.py); the layout item sum is a cross-check. The larger governs rigging.",
            "CoG is longitudinal only; transverse CoG is offset toward the rack wall by the row — crane rigging uses 4-leg slings with adjustable legs.",
        ]
        y = sh.notes(x, y, "GENERAL NOTES", notes, h=2.0, lead=3.1)
        return y
    right_column(sh, lay, "A-001", extra)
    sh.title_block(status=STATUS_OVERRIDE)
    sh.save(os.path.join(out, "A-001"))


# ====================================================================== A-002
def plan_view(sh, lay, ox, oy, s, show_items=True, dashed_wall_items=True, labels=True):
    """Interior plan with walls, returns View."""
    v = View(sh, s, ox, oy)
    wall = (lay.ext_w - lay.W) / 2
    endw = (lay.ext_l - lay.L) / 2
    # walls as thick band (exterior outline + interior outline), hatched
    v.rect(-endw, -wall, lay.L + endw, lay.W + wall, fc="#E3E8EF", ec=INK, lw=1.0, z=1)
    v.rect(0, 0, lay.L, lay.W, fc=PAPER, ec=INK, lw=0.8, z=1)
    if lay.is_container:
        # door opening at x=0
        v.rect(-endw, 150, 0, lay.W - 150, fc=PAPER, ec=PAPER, lw=0, z=2)
        v.line(-endw, 150, 0, 150, lw=0.8, z=3); v.line(-endw, lay.W - 150, 0, lay.W - 150, lw=0.8, z=3)
        # door leaves open outward (arcs schematic as lines)
        v.line(0, 150, -800, 150 - 0, c=MUTED, lw=0.5, ls="--", z=3)
        v.line(0, lay.W - 150, -800, lay.W - 150, c=MUTED, lw=0.5, ls="--", z=3)
        v.text(-endw, lay.W + wall + 60, "DOOR END (doors open outward)", h=1.9, ha="left", va="bottom", c=MUTED)
    if show_items:
        order = {"tray": 0, "structure": 1, "rack": 3, "cooling": 3, "power": 3, "controls": 4, "fire": 4}
        for it in sorted(lay.items, key=lambda i: order.get(i.kind, 2)):
            if it.mount == "ext" or it.mount == "roof" or it.mount == "rack":
                continue
            if it.tag in ("LEAK", "HAC", "FC"):
                continue
            if it.tag == "SKID":
                v.rect(it.x0, it.y0, it.x1, it.y1, fc="none", ec=MUTED, lw=0.6, ls="--", z=1)
                continue
            if it.kind == "tray":
                v.rect(it.x0, it.y0, it.x1, it.y1, fc="none", ec=MUTED, lw=0.5, ls="--", z=2)
                v.text(it.x1 - 50, it.cy, it.tag, h=1.7, ha="right", va="center", c=MUTED)
                continue
            if it.mount in ("wall", "ceiling"):
                v.rect(it.x0, it.y0, it.x1, it.y1, fc=FILL.get(it.kind), ec=EDGE.get(it.kind, INK), lw=0.6, ls="--", z=4)
                if labels:
                    wmm = it.w / s; dmm = it.d / s
                    v.text(it.cx, it.cy, it.tag, h=1.7, ha="center", va="center", bold=True, rot=90 if dmm > wmm else 0)
                continue
            v.item(it, label=labels, h=2.0 if it.w / s > 8 else 1.6)
    return v


def sheet_a002(lay: L.Layout, out):
    s = pick_scale((lay.ext_l + 600, 470))
    sh = new_sheet(lay, "A-002", "Interior layout plan", f"1:{s}", 2)
    ox = 40.0
    y_top = TOP - 14
    oy = y_top - lay.W / s - 36
    sh.view_title(ox, y_top + 6, "INTERIOR LAYOUT PLAN", f"1:{s}")
    v = plan_view(sh, lay, ox, oy, s)
    W, Lm = lay.W, lay.L
    if lay.is_container:
        rf = lay.aisle_y0
        plenum = lay.notes.get("plenum", 0)
        # containment plenum
        if plenum:
            row_end = lay.notes["row_end_x"]
            v.hatch_rect(0, 0, row_end, plenum, hatch="xxxx", ec=EDGE["cooling"], z=1)
            v.text(row_end / 2, plenum / 2, "HOT-AISLE PLENUM (contained)", h=1.7, ha="center", va="center", c=EDGE["cooling"], bg=PAPER)
        # NEC working space zone in front of row
        row_end = lay.notes["row_end_x"]
        v.rect(0, rf, row_end, rf + 914, fc="none", ec=CTQ_C, lw=0.5, ls=":", z=2)
        v.text(row_end / 2, rf + 914 - 40, "NEC 110.26 WORKING SPACE 914 (condition 1)", h=1.8, ha="center", va="top", c=CTQ_C, bg=PAPER)
        # egress path arrow along aisle to door
        ya = rf + (W - rf) / 2
        x0e, y0e = v.p(Lm - L.END_ZONE - 100, ya); x1e, y1e = v.p(-200, ya)
        sh.arrow(x0e, y0e, x1e, y1e, c=GREEN, lw=1.2, ms=9)
        v.text(Lm / 2, ya + 60, f"EGRESS PATH, clear width {W - rf:.0f} >= 900", h=2.0, ha="center", va="bottom", c=GREEN, bg=PAPER)
        # leak rope route: perimeter of floor at 100 from walls + under cooling units
        pts = [(100, 100), (Lm - 100, 100), (Lm - 100, W - 100), (100, W - 100), (100, 100)]
        v.poly(pts, fc="none", ec=RED, lw=0.6, ls=":", closed=False, z=3)
        for it in lay.items:
            if it.kind == "cooling" and it.mount == "floor":
                v.line(it.cx, 100, it.cx, it.y1 - 100, c=RED, lw=0.6, ls=":", z=3)
        v.text(Lm - L.END_ZONE - 150, W - 160, "LEAK ROPE (dotted)", h=1.6, ha="right", va="top", c=RED, bg=PAPER)
        # dimensions
        v.dim_v(0, plenum, Lm + 300 if plenum else Lm, 0, label=f"{plenum}") if plenum else None
        v.dim_v(plenum, rf, 0, -10, label=f"{rf - plenum:.0f}")
        v.dim_v(rf, W, 0, -10, label=f"{W - rf:.0f} AISLE")
        v.dim_v(0, W, 0, -22, label=f"{W:.0f} INT")
        # chain dimension along the row (x positions)
        xs = sorted(set([0] + [it.x0 for it in lay.items if it.mount == "floor" and it.kind in ("rack", "cooling", "power")] + [row_end, Lm - L.END_ZONE, Lm]))
        for a, b in zip(xs[:-1], xs[1:]):
            if b - a > 0:
                v.dim_h(a, b, 0, -10, label=f"{b - a:.0f}", h=1.7)
        v.dim_h(0, Lm, 0, -20, label=f"{Lm:.0f} INTERIOR")
        v.dim_h(row_end, Lm - L.END_ZONE, W, 10, label=f"{lay.notes['door_zone']:.0f} FREE")
        v.dim_h(Lm - L.END_ZONE, Lm, W, 10, label=f"{L.END_ZONE} END ZONE")
        # CTQ bubbles
        racks = lay.by_kind("rack")
        if racks:
            v.bubble(racks[0].cx, racks[0].y1, 0, 22, "CTQ-B3")
            v.bubble(racks[-1].x1, racks[-1].y1, 10, 22, "CTQ-B4")
        v.bubble(Lm / 2, rf + 914, 30, 14, "CTQ-B2")
        v.bubble(300, rf, -16, -16, "CTQ-B1")
    else:
        r = lay.find("R1")
        v.dim_h(0, r.x0, 0, -8, label=f"{r.x0:.0f}"); v.dim_h(r.x0, r.x1, 0, -8, label="600"); v.dim_h(r.x1, Lm, 0, -8, label=f"{Lm - r.x1:.0f}")
        v.dim_v(0, r.y0, 0, -8, label=f"{r.y0:.0f}"); v.dim_v(r.y0, r.y1, 0, -8, label=f"{r.d:.0f}"); v.dim_v(r.y1, W, 0, -8, label=f"{W - r.y1:.0f} FRONT")
        v.text(Lm / 2, W + 120, "CABINET DOOR THIS SIDE (opens 120 deg)", h=2.0, ha="center", c=MUTED)
        v.bubble(r.cx, r.y1, 0, 20, "CTQ-B3")
    sh.north_arrow(RX - 45, TOP - 30)

    # row elevation below
    y_el_top = oy - 40
    oyE = y_el_top - lay.H / s - 6
    ve = View(sh, s, ox, oyE)
    sh.view_title(ox, y_el_top + 2, "ROW ELEVATION — LOOKING AT RACK WALL FROM THE AISLE", f"1:{s}")
    ve.rect(0, 0, lay.L, lay.H, lw=0.8)
    if lay.is_container:
        for it in lay.items:
            if it.mount == "floor" and it.kind in ("rack", "cooling", "power"):
                ve.rect(it.x0, it.z0, it.x1, it.z1, fc=FILL[it.kind], ec=EDGE[it.kind], lw=0.6)
                ve.text(it.cx, it.z1 / 2, it.tag, h=1.9 if it.w / s > 8 else 1.5, ha="center", va="center", bold=True, rot=0 if it.w / s > 8 else 90)
            elif it.mount == "rack":
                ve.rect(it.x0 + 30, it.z0, it.x1 - 30, it.z1, fc=FILL[it.kind], ec=EDGE[it.kind], lw=0.5)
                ve.text(it.cx, (it.z0 + it.z1) / 2, it.tag, h=1.4, ha="center", va="center")
            elif it.mount == "wall" and it.front == "-x":
                pass
        for it in lay.items:
            if it.kind == "tray":
                ve.rect(0, it.z0, it.x1, it.z1, fc="none", ec=MUTED, lw=0.5, ls="--")
        ve.text(lay.L - L.END_ZONE / 2, lay.H / 2, "END ZONE:\nFS1 cylinder\nCP1 controller\nPNL-M aisle side", h=1.6, ha="center", va="center", c=MUTED)
        ve.dim_v(0, lay.H, 0, -8, label=f"{lay.H:.0f}")
        tr = lay.find("TR-D")
        if tr:
            ve.dim_v(0, tr.z0, lay.L, 8, label=f"{tr.z0:.0f} U/S TRAY", side="right")
        racks = lay.by_kind("rack")
        if racks:
            ve.dim_v(0, racks[-1].z1, lay.notes["row_end_x"], 6, label=f"{racks[-1].z1:.0f} RACK", side="right")
    else:
        r = lay.find("R1")
        ve.rect(r.x0, 0, r.x1, r.z1, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6)
        for it in lay.items:
            if it.mount == "rack" and it.tag != "PDU1":
                ve.rect(it.x0 + 30, it.z0, it.x1 - 30, it.z1, fc=FILL[it.kind], ec=EDGE[it.kind], lw=0.5)
                ve.text(it.cx, (it.z0 + it.z1) / 2, it.tag, h=1.6, ha="center", va="center")
        ve.text(r.cx, r.z1 * 0.75, f"IT: {lay.notes['u_it']}U free", h=1.8, ha="center", va="center", c=MUTED)
        ve.dim_v(0, lay.H, 0, -8, label=f"{lay.H:.0f}")

    def extra(sh, x, y):
        rows = []
        for it in lay.items:
            if it.mount in ("ext",) and it.kind != "power":
                continue
            rows.append([it.tag, it.code, it.label[:48], f"{it.x0:.0f}", f"{it.y0:.0f}", f"{it.w:.0f}x{it.d:.0f}", f"{it.z0:.0f}", it.mount])
        y = sh.table(x, y, ["TAG", "CODE", "DESCRIPTION", "x0", "y0", "W x D", "z0", "MOUNT"], rows,
                     [16, 20, RW - 16 - 20 - 16 - 16 - 30 - 14 - 20, 16, 16, 30, 14, 20], h=1.7, rowh=3.4,
                     title="EQUIPMENT SCHEDULE (interior mm; x from door-end liner, y from rack-wall liner, z from finished floor)")
        y -= 6
        y = sh.legend(x, y, [("rack", "IT rack"), ("cooling", "Cooling unit / RDHx / CDU"), ("power", "UPS, battery, panel"), ("controls", "Controls"), ("fire", "Fire suppression")], h=2.0)
        return y
    right_column(sh, lay, "A-002", extra)
    sh.title_block(status=STATUS_OVERRIDE)
    sh.save(os.path.join(out, "A-002"))


# ====================================================================== A-003
def sheet_a003(lay: L.Layout, out):
    sh = new_sheet(lay, "A-003", "Envelope section and hardening", "1:15 / 1:2" if lay.is_container else "1:5 / 1:2", 3)
    ew, eh, W, H = lay.ext_w, lay.ext_h, lay.W, lay.H
    s = 15 if lay.is_container else 5
    ox, y_top = (40.0 if lay.is_container else 100.0), TOP - 14
    oy = y_top - eh / s - 14
    v = View(sh, s, ox, oy)
    sh.view_title(40.0, y_top + 6, "CROSS SECTION THROUGH ROW (looking toward blind end)", f"1:{s}")
    wall = (ew - W) / 2
    if lay.is_container:
        floor_struct = 198; floor_bu = 100; roof_bu = eh - floor_struct - floor_bu - H
        z0 = floor_struct + floor_bu  # finished floor from ext bottom
        # outer shell
        v.rect(0, 0, ew, eh, lw=1.0)
        # corrugated side walls (zig-zag)
        for side in (0, 1):
            X = 0 if side == 0 else ew
            dirn = 1 if side == 0 else -1
            pts = []
            Y = floor_struct
            while Y < eh - 120:
                pts += [(X, Y), (X + dirn * 36, Y + 40), (X + dirn * 36, Y + 100), (X, Y + 140)]
                Y += 140
            v.poly(pts, fc="none", ec=INK, lw=0.5, closed=False)
        # PIR + liner each side
        for side in (0, 1):
            if side == 0:
                v.rect(36, z0, 36 + 100, eh - 120 - 100, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
                v.rect(136, z0, 136 + 1, eh - 120 - 100, fc=INK, ec=INK, lw=0.6)
            else:
                v.rect(ew - 136, z0, ew - 36, eh - 120 - 100, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
                v.rect(ew - 137, z0, ew - 136, eh - 120 - 100, fc=INK, ec=INK, lw=0.6)
        # roof: corrugated + 100 PIR + liner
        v.rect(0, eh - 120, ew, eh, fc="#E8EDF3", lw=0.6)
        v.rect(136, eh - 120 - 100, ew - 136, eh - 120, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
        v.line(136, eh - 220, ew - 136, eh - 220, lw=0.8)
        # floor: cross members + plywood + build-up
        v.rect(0, 0, ew, 118, fc="#E8EDF3", lw=0.6)  # bottom side rails zone (schematic)
        v.rect(118, 0, ew - 118, floor_struct - 28, fc="none", ec=MUTED, lw=0.4)
        v.text(ew / 2, (floor_struct - 28) / 2, "FLOOR CROSS MEMBERS 122 x 45 @ 300 (section through)", h=1.6, ha="center", va="center", c=MUTED)
        v.rect(118, floor_struct - 28, ew - 118, floor_struct, fc="#E9D8B0", ec=MUTED, lw=0.4)
        v.rect(136, floor_struct, ew - 136, floor_struct + 80, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
        v.rect(136, floor_struct + 80, ew - 136, floor_struct + 98, fc="#E9D8B0", ec=MUTED, lw=0.4)
        v.rect(136, floor_struct + 98, ew - 136, z0, fc=INK, ec=INK, lw=0.4)
        # equipment in section: plenum, rack, aisle, tray
        rf = lay.aisle_y0; pl = lay.notes.get("plenum", 0)
        r = lay.by_kind("rack")[0]
        yoff = wall  # interior y=0 at ext wall + wall thickness
        v.rect(yoff + r.y0, z0, yoff + r.y1, z0 + r.z1, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6)
        v.text(yoff + (r.y0 + r.y1) / 2, z0 + r.z1 / 2, "RACK", h=2.2, ha="center", va="center", rot=90, bold=True)
        if pl:
            v.hatch_rect(yoff, z0, yoff + pl, z0 + H, hatch="xxx", ec=EDGE["cooling"])
            v.text(yoff + pl / 2, z0 + H - 300, "HOT PLENUM", h=1.5, ha="center", va="center", rot=90, c=EDGE["cooling"], bg=PAPER)
            v.rect(yoff + pl, z0 + r.z1, yoff + r.y1, z0 + H, fc="none", ec=EDGE["cooling"], lw=0.6, ls="--")
            v.text(yoff + (pl + r.y1) / 2, z0 + (r.z1 + H) / 2, "CONTAINMENT TOP PANEL", h=1.5, ha="center", va="center", c=EDGE["cooling"])
        else:
            v.rect(yoff, z0, yoff + 200, z0 + r.z1, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6)
            v.text(yoff + 100, z0 + r.z1 / 2, "RDHx", h=1.6, ha="center", va="center", rot=90, c=EDGE["cooling"])
        for it in lay.items:
            if it.kind == "tray":
                v.rect(yoff + it.y0, z0 + it.z0, yoff + it.y1, z0 + it.z1, fc=FILL["tray"], ec=MUTED, lw=0.5)
                v.text(yoff + it.cy, z0 + it.z1 + 60, it.tag, h=1.5, ha="center", c=MUTED)
        v.text(yoff + rf + (W - rf) / 2, z0 + 1000, "COLD AISLE / EGRESS", h=2.0, ha="center", va="center", rot=90, c=GREEN)
        # LED luminaire over aisle
        v.rect(yoff + rf + (W - rf) / 2 - 300, z0 + H - 60, yoff + rf + (W - rf) / 2 + 300, z0 + H, fc="#FFFBE6", ec=MUTED, lw=0.5)
        v.text(yoff + rf + (W - rf) / 2, z0 + H - 140, "LED 4000 K, 500 lx at 1 m", h=1.4, ha="center", c=MUTED)
        # floor drain + condensate
        v.circle(yoff + rf + 150, z0 - 30, 40, fc=PAPER, ec=RED, lw=0.6)
        v.leader(yoff + rf + 150, z0 - 30, 20, -12, "Floor drain 50 mm with trap, fall 1:100 (CTP-C1)", h=1.8, c=RED)
        # dims
        v.dim_v(0, floor_struct, ew, 8, label=f"{floor_struct} STRUCT", side="right")
        v.dim_v(floor_struct, z0, ew, 8, label=f"{floor_bu} FLOOR B/U", side="right")
        v.dim_v(z0, z0 + H, ew, 8, label=f"{H:.0f} INT", side="right")
        v.dim_v(z0 + H, eh, ew, 8, label=f"{roof_bu:.0f} ROOF", side="right")
        v.dim_v(0, eh, ew, 24, label=f"{eh:.0f}", side="right")
        v.dim_h(0, wall, 0, -8, label=f"{wall:.0f}")
        v.dim_h(wall, ew - wall, 0, -8, label=f"{W:.0f} INT")
        v.dim_h(ew - wall, ew, 0, -8, label=f"{wall:.0f}")
        v.dim_h(0, ew, 0, -18, label=f"{ew:.0f}")
        v.bubble(60, z0 + 1500, -14, 6, "CTQ-C1"); v.bubble(136, z0 + 2000, -14, 10, "CTQ-C2"); v.bubble(ew - 60, z0 + 300, 14, -8, "CTQ-C4")
        # details in two rows below the section
        dy = oy - 30
        detail_wall(sh, ox, dy, lay)
        detail_floor(sh, ox + 95, dy, lay, k=2.5)
        detail_door_seal(sh, ox + 240, dy)
        detail_curb(sh, ox + 335, dy, k=2.5)
        dy2 = dy - 118
        detail_ip66(sh, ox, dy2)
        detail_hardening(sh, ox + 150, dy2, lay)
    else:
        # cabinet: double skin with 40 PIR, rack inside, cabinet AC on side
        v.rect(0, 0, ew, eh, lw=1.0)
        v.rect(100, 150, ew - 100, eh - 100, fc=PAPER, lw=0.6)
        for X0, X1 in ((2, 98), (ew - 98, ew - 2)):
            v.rect(X0 + 20, 150, X1 - 20, eh - 100, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
        r = lay.find("R1")
        v.rect(wall + r.y0, 150 + 100, wall + r.y1, 150 + 100 + r.z1, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6)
        v.text(wall + r.cy, 150 + 100 + r.z1 / 2, "24U RAILS", h=2.0, ha="center", va="center", rot=90, bold=True)
        cu = lay.find("CU1")
        v.rect(-250, cu.z0, 0, cu.z1, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6)
        v.text(-125, (cu.z0 + cu.z1) / 2, "CABINET DX", h=1.8, ha="center", va="center", rot=90)
        v.rect(-50, -150, ew + 50, 0, fc="#E8EDF3", lw=0.6); v.text(ew / 2, -75, "SKID (fork pockets)", h=1.8, ha="center", va="center")
        v.dim_v(0, eh, ew, 8, label=f"{eh:.0f}", side="right"); v.dim_h(0, ew, 0, -8, label=f"{ew:.0f}")
        v.dim_h(100, ew - 100, eh, 8, label=f"{ew - 200:.0f} INT (config {W:.0f})")
        v.leader(60, eh / 2, -14, 10, "Double skin + 40 PIR, NEMA 4X / IP66 compression gasket", h=1.8)
        v.bubble(ew - 100, eh / 2, 14, 8, "CTQ-C1"); v.bubble(ew - 60, eh * 0.75, 14, 6, "CTQ-C3")
        if lay.cfg.hardening in ("H2", "H3"):
            v.rect(-100, -750, ew + 100, -150, fc="#C9D3E0", ec=INK, lw=0.6); v.text(ew / 2, -450, "FLOOD PLINTH 600 (H2/H3) UNDER THE SKID", h=1.6, ha="center", va="center")
        detail_wall(sh, ox + ew / s + 70, TOP - 20, lay)
        detail_door_seal(sh, ox + ew / s + 180, TOP - 20)
        detail_ip66(sh, ox + ew / s + 70, TOP - 160)
        detail_hardening(sh, ox + ew / s + 70, TOP - 300, lay)

    def extra(sh, x, y):
        clim = lay.d["climate"]
        if lay.is_container:
            R = 0.100 / 0.022; U = 1 / (R + 0.17)
            tin, rh = 22, 50
            tdp = 11.1
            tsi = tin - U * 0.13 * (tin - clim["t_min_c"])
            rows = [["Envelope rating", f"{lay.d['hardening_rating']}; coating {lay.d['hardening_coating']}"],
                    ["Wall / roof insulation", "100 mm PIR, lambda 0.022 W/mK, foil faced, joints taped"],
                    ["R-value (centre of panel)", f"{R:.1f} m2K/W; U = {U:.2f} W/m2K (config uses effective R 3.5 incl. bridging)"],
                    ["Floor build-up", "80 mm PIR + 18 mm plywood + 2 mm anti-static vinyl = 100 mm; C100 channels under row"],
                    ["Design conditions", f"Outdoor {clim['t_design_c']} C / {clim['t_min_c']} C ({clim['label']}); indoor 22 C, 50 % RH, dew point {tdp} C"],
                    ["Liner surface temp at t_min", f"{tsi:.1f} C > dew point {tdp} C: no condensation on liner (centre of panel)"],
                    ["Thermal bridges", "Corner posts, door frame, floor cross members: local surface can reach ~5 C at t_min. 20 mm closed-cell foam on all exposed steel inside; heated door gasket for 'cold' climate"],
                    ["Vapour control", "Liner (0.7 mm steel, sealed joints) is the warm-side vapour barrier. All penetrations sealed with butyl + EPDM boots"],
                    ["Envelope gain at design", f"{lay.d['envelope_gain_kw']} kW (config rule)"]]
        else:
            rows = [["Cabinet wall", "Double-skin aluminium / steel, 40 mm PIR, NEMA 4X / IP66 compression gasket, 3-point latch (STR-CAB24U)"],
                    ["Design conditions", f"Outdoor {clim['t_design_c']} C / {clim['t_min_c']} C; indoor 18-27 C"],
                    ["Condensation", "Cabinet DX runs in dehumidify mode below 15 C dew point; heater strip 100 W for t_min < 0 C"]]
        y = sh.table(x, y, ["THERMAL ENVELOPE", "VALUE / NOTE"], rows, [RW * 0.3, RW * 0.7], title="THERMAL AND MOISTURE NOTES", h=1.9)
        y -= 6
        notes = ["Insulation is fixed with adhesive and 4 mechanical pins/m2; no gap > 3 mm, joints staggered and taped.",
                 "Liner panels overlap 25 mm with sealant bead; interior finish white (reflectance >= 0.8) for lighting.",
                 "Floor drain and condensate drains fall 1:100 to the exterior trap; trap primed before shipping.",
                 "Doors: original ISO door gaskets retained; add the compression gasket kit (ENV-DOORGASKET-4X: 20 mm EPDM sponge D-seal, three-point compression latch, drip edge); 25 mm PIR + liner on door inner faces; compression check CTQ-C3.",
                 "IP66 (UL 50E type 4X): every penetration through a gasketed transit frame (ENV-SEAL-KIT) or a sleeved pipe entry with EPDM boot; hose test on every one (CTQ-A4 WITNESS, Detail 5); make-up fan holds +10 Pa (ENV-PRESSURE-FAN).",
                 f"Hardening {lay.d['hardening_label']} (Detail 6): H2 adds flood plinth 600, C5-M coating, ePM1 intake filters + hoods, hurricane door hardware, snow guards, stainless fasteners, anodes; H3 adds UL 752 ballistic panels (CTQ-H2), ASTM F3038 doors, IK10 hatches, HEMP shield option with filtered penetrations (CTQ-H3), mantrap, two-factor access.",
                 "Fire: PIR class B-s2,d0 minimum (EN 13501-1) or FM 4880 approved; liner joints sealed to maintain the clean-agent hold time (CTP-F1)."]
        return sh.notes(x, y, "ENVELOPE NOTES", notes, h=2.0, lead=3.1)
    right_column(sh, lay, "A-003", extra)
    sh.title_block(status=STATUS_OVERRIDE)
    sh.save(os.path.join(out, "A-003"))


def detail_wall(sh, x, ytop, lay):
    sh.view_title(x, ytop, "DETAIL 1 — WALL BUILD-UP", "1:2")
    v = View(sh, 2, x + 10, ytop - 112)
    # corrugation (outer), 100 PIR, liner
    pts = [(0, 0), (36, 40), (36, 100), (0, 140), (36, 180), (36, 200)]
    v.poly(pts, fc="none", ec=INK, lw=0.7, closed=False)
    v.rect(36, 0, 136, 200, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
    v.rect(136, 0, 137, 200, fc=INK, ec=INK)
    v.line(36, 100, 136, 100, c=MUTED, lw=0.3)
    v.leader(18, 70, -10, -14, "Corrugated shell 1.6-2.0 mm Corten", h=1.8)
    v.leader(86, 150, 36, 6, "100 mm PIR, foil faced, pinned + glued", h=1.8)
    v.leader(136, 50, 10, -10, "Liner 0.7 mm galv. steel, white, sealed laps", h=1.8)
    v.dim_h(36, 136, 0, -8, label="100")
    v.dim_h(0, 137, 200, 6, label="137")


def detail_floor(sh, x, ytop, lay, k=2):
    sh.view_title(x, ytop, "DETAIL 2 — FLOOR BUILD-UP AT CHANNEL", f"1:{k:g}")
    v = View(sh, k, x, ytop - 12 - 250 / k)
    v.rect(0, 0, 300, 122, fc="none", ec=INK, lw=0.6)          # cross member (I-section schematic)
    v.line(0, 61, 300, 61, c=MUTED, lw=0.3)
    v.rect(0, 122, 300, 150, fc="#E9D8B0", ec=MUTED, lw=0.4)  # 28 plywood
    v.rect(0, 150, 100, 230, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")   # PIR 80
    v.rect(200, 150, 300, 230, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
    v.rect(0, 230, 100, 248, fc="#E9D8B0", ec=MUTED, lw=0.4); v.rect(200, 230, 300, 248, fc="#E9D8B0", ec=MUTED, lw=0.4)
    v.rect(0, 248, 100, 250, fc=INK, ec=INK); v.rect(200, 248, 300, 250, fc=INK, ec=INK)
    # C100x50x5 channel between, open side down? draw as C opening up
    v.poly([(100, 150), (100, 250), (105, 250), (105, 155), (195, 155), (195, 250), (200, 250), (200, 150)], fc="#C9D3E0", ec=INK, lw=0.6)
    # M12 bolt through channel web, plywood and cross member flange
    v.rect(145, 100, 155, 165, fc=INK, ec=INK); v.rect(135, 155, 165, 165, fc=INK, ec=INK)
    v.leader(150, 110, 16, -14, "M12 8.8 through-bolt + nyloc, 85 N·m (CTP-S1)", h=1.8, c=CTP_C)
    v.leader(150, 230, 16, 10, "Rack foot / hold-down angle, M12 to channel (CTP-S2)", h=1.8, c=CTP_C)
    v.leader(50, 190, 6, 22, "80 PIR + 18 ply + 2 anti-static vinyl", h=1.8)
    v.leader(250, 136, 12, -8, "Original 28 mm plywood on cross members", h=1.8)
    v.dim_v(150, 250, 300, 10, label="100", side="right")
    v.dim_h(100, 200, 250, 6, label="100 CHANNEL")


def detail_door_seal(sh, x, ytop):
    sh.view_title(x, ytop, "DETAIL 3 — DOOR SEAL", "1:2")
    v = View(sh, 2, x + 10, ytop - 95)
    v.rect(0, 0, 60, 160, fc="#E8EDF3", ec=INK, lw=0.6)         # door frame post
    v.rect(70, 20, 110, 160, fc="#E8EDF3", ec=INK, lw=0.6)      # door leaf edge
    v.rect(110, 20, 135, 160, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")  # 25 PIR on door
    v.rect(135, 20, 136, 160, fc=INK, ec=INK)
    v.circle(65, 60, 10, fc="#C9D3E0", ec=INK, lw=0.6)          # bulb seal
    v.poly([(60, 110), (70, 100), (70, 130), (60, 120)], fc="#C9D3E0", ec=INK, lw=0.5)   # original gasket
    v.leader(65, 60, 40, -14, "Secondary 20 mm EPDM bulb seal (CTQ-C3)", h=1.8, c=CTQ_C)
    v.leader(65, 115, 20, 20, "Original ISO door gasket", h=1.8)
    v.leader(122, 90, 16, 0, "25 mm PIR + liner on door", h=1.8)


def detail_curb(sh, x, ytop, k=2):
    sh.view_title(x, ytop, "DETAIL 4 — ROOF LINE-SET CURB", f"1:{k:g}")
    v = View(sh, k, x, ytop - 12 - 125 / k)
    v.rect(0, 0, 300, 20, fc="#E8EDF3", ec=INK, lw=0.6)         # roof sheet
    v.rect(0, -100, 300, 0, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")   # PIR under
    v.rect(0, -101, 300, -100, fc=INK, ec=INK)
    v.rect(100, -100, 105, 120, fc="#C9D3E0", ec=INK, lw=0.6); v.rect(195, -100, 200, 120, fc="#C9D3E0", ec=INK, lw=0.6)  # curb frame 50x50x5 as uprights
    v.rect(100, 120, 200, 125, fc="#C9D3E0", ec=INK, lw=0.6)
    v.poly([(95, 120), (205, 120), (215, 20), (85, 20)], fc="none", ec=INK, lw=0.6, ls="--")   # EPDM boot
    v.circle(130, 60, 10, fc=PAPER, ec=INK, lw=0.6); v.circle(170, 60, 6, fc=PAPER, ec=INK, lw=0.6)
    v.text(130, 60, "S", h=1.5, ha="center", va="center"); v.text(170, 60, "L", h=1.5, ha="center", va="center")
    v.leader(150, 122, 16, 12, "Welded curb 50x50x5, 150 high (CTP-A1 HOLD)", h=1.8, c=CTP_C)
    v.leader(210, 70, 14, 0, "EPDM boot + butyl, clamp band", h=1.8)
    v.leader(130, 60, -20, -20, "S suction / L liquid, insulated", h=1.8)


def detail_ip66(sh, x, ytop):
    """Detail 5: gasketed cable transit frame in the wall + hose-test note (UL 50E type 4X / IEC 60529 IPX6)."""
    sh.view_title(x, ytop, "DETAIL 5 — IP66 PENETRATION + HOSE TEST", "1:2")
    v = View(sh, 2, x + 10, ytop - 108)
    v.rect(0, 0, 36, 200, fc="#E8EDF3", ec=INK, lw=0.7)                 # outer skin
    v.rect(36, 0, 136, 200, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")  # PIR
    v.rect(136, 0, 137, 200, fc=INK, ec=INK)                             # liner
    v.rect(-6, 60, 160, 66, fc="#C9D3E0", ec=INK, lw=0.6); v.rect(-6, 134, 160, 140, fc="#C9D3E0", ec=INK, lw=0.6)   # frame flanges
    v.rect(-6, 60, 0, 140, fc="#C9D3E0", ec=INK, lw=0.6); v.rect(154, 60, 160, 140, fc="#C9D3E0", ec=INK, lw=0.6)
    for k in range(3):                                                    # compression modules around cables
        y0 = 70 + k * 22
        v.rect(0, y0, 154, y0 + 18, fc="#8FA3BA", ec=INK, lw=0.4)
        v.circle(77, y0 + 9, 6, fc=PAPER, ec=INK, lw=0.4)
    v.rect(0, 136, 154, 140, fc=INK, ec=INK)                              # compression wedge
    v.rect(-12, 54, -6, 146, fc="#2E4461", ec=INK, lw=0.5)                # exterior gasket
    v.leader(-9, 100, -6, 14, "EPDM gasket 4 mm under the flange,\nstainless bolts @ 100", h=1.6)
    v.leader(77, 79, 24, -12, "Compression modules (Roxtec CF /\nComSeal class) IP66/67, UL 50E 4X\n(ENV-SEAL-KIT)", h=1.6)
    v.leader(77, 138, 24, 14, "Wedge compressed to the mark;\nspare modules for future cables", h=1.6)
    v.leader(136, 30, 14, -6, "Liner sealed to the frame (PU bead)", h=1.6)
    v.text(-12, -14, "HOSE TEST (CTQ-A4 WITNESS): 25 mm nozzle, 240 L/min at 3-3.5 m,", h=1.6, c=CTQ_C)
    v.text(-12, -22, "every penetration and door seam; no water inside.", h=1.6, c=CTQ_C)


def detail_hardening(sh, x, ytop, lay):
    """Detail 6: hardening add-ons per level — H2 flood plinth and C5-M coating, H3 ballistic panel and shielded penetration."""
    hz = lay.cfg.hardening
    sh.view_title(x, ytop, f"DETAIL 6 — HARDENING ADD-ONS H2 / H3 (this unit: {hz})", "1:10 / 1:2")
    # H2: flood plinth under the skid / module rail, 1:10
    v = View(sh, 10, x + 8, ytop - 94)
    v.rect(0, -150, 700, 0, fc="#D9E1EA", ec=INK, lw=0.6, hatch="//"); v.text(350, -75, "PAD / SLAB", h=1.4, ha="center", va="center", bg=PAPER)
    v.rect(60, 0, 140, 600, fc="#C9D3E0", ec=INK, lw=0.6); v.rect(560, 0, 640, 600, fc="#C9D3E0", ec=INK, lw=0.6)
    v.line(60, 0, 640, 600, c=INK, lw=0.5); v.line(60, 600, 640, 0, c=INK, lw=0.5)
    v.rect(0, 600, 700, 660, fc="#A8B4C4", ec=INK, lw=0.6)
    v.rect(0, 660, 700, 850, fc="#E8EDF3", ec=INK, lw=0.7); v.text(350, 755, "SKID / MODULE RAIL", h=1.4, ha="center", va="center", c=MUTED)
    v.rect(90, -120, 110, 40, fc=INK, ec=INK); v.rect(590, -120, 610, 40, fc=INK, ec=INK)
    v.dim_v(0, 600, 700, 6, label="600", side="right", h=1.6)
    v.leader(350, 630, 8, 14, "H2: flood plinth 600, HDG frame + bracing,\nanodes (STR-FLOOD-PLINTH, STR-ANODES)", h=1.5, c=CTP_C)
    v.leader(100, -100, 10, -8, "M16 anchors through plinth feet;\nstainless A4 fasteners (H2)", h=1.5)
    sh.text(x, ytop - 112, "H2 also: C5-M coating 320 um, ePM1 intake filters + hoods, hurricane hardware, snow guards, intrusion detection.", h=1.5, c=MUTED)
    sh.text(x, ytop - 115.5, "H3 also: ASTM F3038 doors, IK10 hatches, tamper seals, mantrap, two-factor access, shield test by test house.", h=1.5, c=MUTED)
    # H3: ballistic panel + shielded penetration, 1:2
    vb = View(sh, 2, x + 128, ytop - 108)
    vb.rect(0, 0, 36, 200, fc="#E8EDF3", ec=INK, lw=0.7); vb.rect(36, 0, 136, 200, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
    vb.rect(136, 0, 137, 200, fc=INK, ec=INK)
    vb.rect(137, 0, 139, 200, fc="#4A4A4A", ec="#4A4A4A")                 # 2 mm steel shield liner
    vb.rect(139, 0, 151, 200, fc="#8B5A2B", ec=INK, lw=0.4)               # 12 mm ballistic panel
    vb.rect(151, 0, 153, 200, fc="#C9D3E0", ec=INK, lw=0.3)               # batten / finish
    vb.rect(-10, 80, 170, 86, fc="#C9D3E0", ec=INK, lw=0.5); vb.rect(-10, 114, 170, 120, fc="#C9D3E0", ec=INK, lw=0.5)
    vb.rect(0, 86, 150, 114, fc="#8FA3BA", ec=INK, lw=0.4)
    vb.rect(137, 70, 175, 80, fc="#4A4A4A", ec="#4A4A4A"); vb.rect(137, 120, 175, 130, fc="#4A4A4A", ec="#4A4A4A")
    vb.rect(160, 86, 175, 114, fc="#2E4461", ec=INK, lw=0.5)
    vb.leader(145, 40, 16, -8, "H3: UL 752 ballistic panel 12 mm\n(Level 3; 4-8 selectable), battened,\nseams lapped 50 (CTQ-H2 HOLD)", h=1.5, c=CTP_C)
    vb.leader(138, 175, 16, 6, "H3 option: HEMP shield liner 2 mm steel,\nwelded, 80 dB (ENV-HEMP-SHIELD, CTQ-H3)", h=1.5)
    vb.leader(167, 100, 12, 8, "Filtered penetration: HEMP power-line\nfilter / waveguide-below-cutoff for pipes,\nfibre-only data (ENV-HEMP-PENETRATIONS)", h=1.5)
    vb.leader(75, 100, -10, -12, "IP66 frame as Detail 5,\ninside the shield boundary", h=1.5)
    if hz == "H1":
        sh.text(x, ytop - 119.5, "This unit is H1 Standard: Detail 6 shows the add-ons available at H2 / H3; none are fitted.", h=1.6, c=RED)


def detail_panel_joint(sh, x, ytop):
    """Hall: section seam — splice plates, two-stage gasket, cover flashing, bonding jumper (CTP-J1)."""
    sh.view_title(x, ytop, "DETAIL 7 — SECTION SEAM", "1:3")
    v = View(sh, 3, x + 6, ytop - 90)
    for X0 in (0, 170):                                                   # two panel edges (100 PIR sandwich with steel skins)
        v.rect(X0, 0, X0 + 130, 200, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
        v.rect(X0, 0, X0 + 130, 2, fc=INK, ec=INK); v.rect(X0, 198, X0 + 130, 200, fc=INK, ec=INK)
        v.rect(X0 + (120 if X0 == 0 else 0), 0, X0 + (130 if X0 == 0 else 10), 200, fc="#C9D3E0", ec=INK, lw=0.6)   # edge frames
    v.rect(130, 60, 170, 140, fc="#2E4461", ec=INK, lw=0.5)               # primary EPDM gasket (compressed)
    v.rect(130, 20, 170, 40, fc="#5C7391", ec=INK, lw=0.4)                # secondary butyl
    v.rect(110, 90, 190, 110, fc=INK, ec=INK)                             # splice plate + bolt
    v.rect(-10, 198, 310, 206, fc="#A8B4C4", ec=INK, lw=0.6)              # exterior cover flashing
    v.line(125, 10, 175, 10, c=GREEN, lw=1.2)                             # bonding jumper
    v.leader(150, 100, 20, -24, "Splice plate 10 mm, M20 8.8 @ 600, 410 N·m (CTP-J1)", h=1.6, c=CTP_C)
    v.leader(150, 130, 24, 10, "Primary EPDM gasket 40 mm, compressed 30-50 %", h=1.6)
    v.leader(150, 30, 24, -8, "Secondary butyl tape; interior liner trim sealed", h=1.6)
    v.leader(150, 202, 24, 14, "Exterior cover flashing, riveted @ 300, sealant both edges; roof seam flashing lapped 150", h=1.6)
    v.leader(150, 10, -20, -12, "Bonding jumper 16 mm2 at every joint, <= 0.1 ohm", h=1.6, c=GREEN)
    v.dim_h(130, 170, 0, -8, label="40 GAP")


DETAILS = {"wall": detail_wall, "floor": detail_floor, "door_seal": detail_door_seal, "curb": detail_curb, "ip66": detail_ip66,
           "hardening": detail_hardening, "panel_joint": detail_panel_joint}
HALL_CTX = GH.Ctx(new_sheet, right_column, DETAILS)


# ====================================================================== S-001
def sheet_s001(lay: L.Layout, out):
    s = pick_scale((lay.ext_l + 600, 470))
    sh = new_sheet(lay, "S-001", "Floor framing and anchoring", f"1:{s} / 1:5", 4)
    ox, y_top = 40.0, TOP - 14
    oy = y_top - lay.W / s - 30
    v = View(sh, s, ox, oy)
    Lm, W = lay.L, lay.W
    if lay.is_container:
        sh.view_title(ox, y_top + 6, "FLOOR FRAMING PLAN — VIEW FROM ABOVE, FLOOR BUILD-UP REMOVED", f"1:{s}")
        wall = (lay.ext_w - W) / 2; endw = (lay.ext_l - Lm) / 2
        v.rect(-endw, -wall, Lm + endw, W + wall, fc="#E3E8EF", lw=1.0, z=1)
        v.rect(0, 0, Lm, W, fc=PAPER, lw=0.8, z=1)
        # cross members @ 300
        n = int(Lm // 300)
        pitch = Lm / n
        for i in range(n + 1):
            X = i * pitch
            v.rect(X - 22, 0, X + 22, W, fc="#D9E1EA", ec=MUTED, lw=0.3, z=1)
        v.text(Lm / 2, W - 120, f"FLOOR CROSS MEMBERS 122x45 C-SECTION @ ~{pitch:.0f} ({n + 1} off) — EXISTING", h=1.8, ha="center", c=MUTED, bg=PAPER)
        # floor channels under row: 2 runs at rack feet lines
        racks = lay.by_kind("rack")
        r = racks[0]
        row_end = lay.notes["row_end_x"]
        feet = (r.y0 + 100, r.y1 - 100) if lay.notes.get("plenum", 0) else (r.y0 + 300, r.y1 - 100)
        for yf in feet:
            v.rect(0, yf - 50, row_end, yf + 50, fc="#C9D3E0", ec=INK, lw=0.7, z=3)
            for i in range(n + 1):   # through-bolt at each cross member
                X = i * pitch
                if X <= row_end:
                    v.circle(X, yf, 25, fc=INK, ec=INK, z=4)
        v.text(row_end / 2, feet[0] - 120, "FLOOR CHANNEL C100x50x5 (2 runs), M12 THROUGH-BOLT AT EVERY CROSS MEMBER (CTP-S1)", h=1.7, ha="center", va="top", c=INK, bg=PAPER)
        # rack hold-down bolts (4 per rack) and equipment skid bolts
        for it in lay.items:
            if it.mount != "floor" or it.kind not in ("rack", "cooling", "power"):
                continue
            v.rect(it.x0, it.y0, it.x1, it.y1, fc="none", ec=EDGE[it.kind], lw=0.5, ls="--", z=3)
            v.text(it.cx, it.cy, it.tag, h=1.6, ha="center", va="center", c=EDGE[it.kind], rot=90 if it.w / s < 8 else 0)
            if it.kind == "rack":
                for X in (it.x0 + 60, it.x1 - 60):
                    for Y in feet:
                        v.circle(X, Y, 30, fc=PAPER, ec=RED, lw=0.7, z=5)
            else:
                for X in (it.x0 + 50, it.x1 - 50):
                    for Y in (it.y0 + 50, it.y1 - 50):
                        v.circle(X, Y, 30, fc=PAPER, ec=CTP_C, lw=0.7, z=5)
        # corner castings: lifting / tie-down
        for (X, Y) in ((-endw, -wall), (Lm + endw - 178, -wall), (-endw, W + wall - 162), (Lm + endw - 178, W + wall - 162)):
            v.rect(X, Y, X + 178, Y + 162, fc="#9FB3CC", ec=INK, lw=0.8, z=4)
        v.text(-endw + 90, -wall - 120, "TIE-DOWN: bottom castings, twist-locks on pad (4)", h=1.7, ha="left", va="top", c=MUTED)
        v.text(Lm + endw - 90, W + wall + 120, "LIFT: top castings, 4-leg spreader (CTP-S4 HOLD)", h=1.7, ha="right", va="bottom", c=MUTED)
        # dims
        v.dim_v(feet[0], feet[1], 0, -10, label=f"{feet[1] - feet[0]:.0f} CHANNEL C/C")
        v.dim_v(0, feet[0], 0, -10, label=f"{feet[0]:.0f}")
        v.dim_h(0, row_end, 0, -10, label=f"{row_end:.0f} CHANNEL LENGTH")
        v.dim_h(0, pitch, W, 8, label=f"{pitch:.0f} TYP")
        v.bubble(row_end / 2, feet[1], 0, 24, "CTP-S1", "CTP")
        v.bubble(racks[0].x0 + 60, feet[1], -14, 20, "CTP-S2", "CTP")
        v.bubble(row_end / 2, feet[0], 30, -22, "CTQ-S1")
        # detail: rack hold-down section 1:5
        dx = ox; dy = oy - 40
        sh.view_title(dx, dy, "DETAIL A — RACK HOLD-DOWN TO FLOOR CHANNEL", "1:5")
        vd = View(sh, 5, dx, dy - 95)
        vd.rect(0, 0, 600, 122, fc="none", ec=INK, lw=0.6); vd.text(300, 61, "CROSS MEMBER", h=1.5, ha="center", va="center", c=MUTED)
        vd.rect(0, 122, 600, 150, fc="#E9D8B0", ec=MUTED, lw=0.4)
        vd.poly([(200, 150), (200, 250), (205, 250), (205, 155), (395, 155), (395, 250), (400, 250), (400, 150)], fc="#C9D3E0", ec=INK, lw=0.6)
        vd.rect(0, 150, 200, 250, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="..."); vd.rect(400, 150, 600, 250, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
        vd.rect(150, 250, 450, 262, fc="#A8B4C4", ec=INK, lw=0.6)   # rack base angle/plate
        vd.rect(150, 262, 170, 600, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6); vd.rect(430, 262, 450, 600, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6)
        vd.text(300, 450, "RACK FRAME", h=1.8, ha="center", va="center", c=EDGE["rack"])
        for X in (240, 360):
            vd.rect(X - 6, 155, X + 6, 290, fc=INK, ec=INK); vd.rect(X - 15, 262, X + 15, 275, fc=INK, ec=INK)
        vd.rect(294, 100, 306, 165, fc=INK, ec=INK); vd.rect(285, 155, 315, 165, fc=INK, ec=INK)
        vd.leader(360, 280, 20, 12, "M12 8.8 hold-down bolts, 2 per foot, 85 N·m, paint-mark (CTP-S2)", h=1.8, c=CTP_C)
        vd.leader(300, 110, 24, -10, "M12 through-bolt to cross member flange, 85 N·m (CTP-S1)", h=1.8, c=CTP_C)
        vd.leader(100, 200, -10, 12, "Floor build-up between channels", h=1.8)
        vd.dim_h(200, 400, 250, 8, label="100")
        # seismic option
        sx = dx + 180
        sh.view_title(sx, dy, "DETAIL B — SEISMIC BRACING OPTION (SDS >= 0.5 g)", "1:20")
        vs = View(sh, 20, sx, dy - 132)
        vs.rect(0, 0, 600, 2000, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6); vs.text(300, 1000, "RACK", h=1.8, ha="center", va="center")
        vs.rect(-200, 0, -190, 2400, fc=INK, ec=INK)   # wall liner
        vs.line(-190, 2300, 300, 2000, c=RED, lw=1.0); vs.line(-190, 2300, 300, 2000, c=RED, lw=1.0)
        vs.rect(-190, 2250, 0, 2350, fc="#C9D3E0", ec=INK, lw=0.5)
        vs.leader(60, 2150, 16, 10, "45 deg strut, P1000 channel + fittings, M12 to top side rail boss (welded, CTP-A1)", h=1.7, c=RED)
        vs.leader(300, 1990, 16, -14, "Rack top: 2 struts per rack at rack-to-rack joint, bolted through frame", h=1.7)
        vs.text(300, -250, "Option for seismic design category D+ : add 2 struts per rack and 4 anchors per equipment skid; engineer of record to confirm (ASCE 7 Ch.13)", h=1.6, ha="center", c=MUTED)
    else:
        sh.view_title(ox, y_top + 6, "SKID PLAN — ANCHOR AND FORK POCKET LAYOUT", f"1:{s}")
        sk = lay.find("SKID")
        v.rect(sk.x0, sk.y0, sk.x1, sk.y1, fc="#E8EDF3", lw=0.8)
        v.rect(0, 0, Lm, W, fc=PAPER, lw=0.6, ls="--")
        for X in (sk.x0 + 100, sk.x1 - 100):
            for Y in (sk.y0 + 100, sk.y1 - 100):
                v.circle(X, Y, 20, fc=PAPER, ec=CTP_C, lw=0.8)
        for Y in (sk.cy - 250, sk.cy + 250):
            v.rect(sk.x0, Y - 60, sk.x1, Y + 60, fc="none", ec=MUTED, lw=0.5, ls=":")
        v.text(Lm / 2, W / 2, "CABINET FOOTPRINT", h=2.0, ha="center", va="center", c=MUTED)
        v.text(sk.cx, sk.cy - 250, "FORK POCKET 180x60", h=1.5, ha="center", va="center", c=MUTED, bg=PAPER)
        v.dim_h(sk.x0, sk.x1, sk.y0, -8, label=f"{sk.w:.0f}"); v.dim_v(sk.y0, sk.y1, sk.x0, -8, label=f"{sk.d:.0f}")
        v.dim_h(sk.x0 + 100, sk.x1 - 100, sk.y1, 8, label=f"{sk.w - 200:.0f} ANCHOR C/C")
        v.bubble(sk.x0 + 100, sk.y1 - 100, -12, 12, "CTP-S1", "CTP")
        dy = oy - 40
        sh.view_title(ox, dy, "DETAIL A — SKID ANCHOR TO PAD", "1:5")
        vd = View(sh, 5, ox, dy - 90)
        vd.rect(0, 0, 500, 150, fc="#D9E1EA", ec=INK, lw=0.6, hatch="//"); vd.text(250, 75, "CONCRETE PAD 150 min, 25 MPa", h=1.6, ha="center", va="center", bg=PAPER)
        vd.rect(0, 150, 500, 160, fc="#A8B4C4", ec=INK, lw=0.6)
        vd.rect(150, 160, 350, 260, fc="#E8EDF3", ec=INK, lw=0.6); vd.text(250, 210, "SKID 100x50 RHS", h=1.5, ha="center", va="center")
        vd.rect(242, 40, 258, 280, fc=INK, ec=INK); vd.rect(225, 260, 275, 275, fc=INK, ec=INK)
        vd.leader(250, 270, 20, 10, "M16 wedge anchor, 110 embed, 210 N·m (CTP-S1)", h=1.8, c=CTP_C)
        vd.leader(100, 155, -10, 14, "10 mm neoprene bearing pad", h=1.8)

    def extra(sh, x, y):
        d = lay.d
        g = 9.81
        racks = lay.by_kind("rack")
        rows = [["Dead load (gross)", f"{d['gross_kg']} kg = {d['gross_kg'] * g / 1000:.0f} kN"],
                ["Rack point load (900-1000 kg, 4 feet)", f"{(racks[0].kg if racks else 400) * g / 4 / 1000:.2f} kN per foot"],
                ["Floor UDL check (row strip)", next((f"{c.value} kN/m2 vs {c.limit:g} — {c.result}" for c in lay.checks if c.id == "I-C16"), "n/a")],
                ["Wind (ASCE 7 basic)", f"{d['climate']['wind_ms']} m/s -> qz ~ {0.613 * d['climate']['wind_ms'] ** 2 / 1000:.2f} kPa; overturning resisted by 4 twist-locks"],
                ["Seismic", "Site SDS from geotech; Detail B option when SDS >= 0.5 g"],
                ["Snow (roof)", "Container roof rated 300 kg/m2 (ISO 1496 roof test ~ 300 kg on 600x300); condensers on curbs clear of snow line 300 mm"],
                ["Bolt torque (class 8.8, dry)", "M8 25 / M10 50 / M12 85 / M16 210 N·m, +/-10 %, calibrated wrench"]]
        y = sh.table(x, y, ["LOAD / ITEM", "VALUE"], rows, [RW * 0.36, RW * 0.64], title="STRUCTURAL DATA", h=1.9)
        y -= 6
        notes = ["Floor channels bear directly on the original plywood over cross members; never on insulation alone.",
                 "Shim channels with steel shims only; level within 3 mm over the row before torquing (CTQ-S1).",
                 "Every torqued bolt gets a paint stripe across nut and base after the witness check (Q-04).",
                 "Container corner posts carry 86.4 t each (ISO 1496 stacking test, 9-high); no load is applied to the posts by this design other than lifting and tie-down.",
                 "Cutouts weaken the corrugated shell shear panel: keep the sum of cutout widths in any 1 m of wall below 400 mm, or add a diagonal stiffener (engineer of record).",
                 "BEN 5: skid has 4 anchors to pad and fork pockets both directions; lift with forks only from the long side with the cabinet empty of IT. H2/H3: 600 mm flood plinth between pad and skid / module rails (A-003 Detail 6).",
                 ]
        return sh.notes(x, y, "STRUCTURAL NOTES", notes, h=2.0, lead=3.1)
    right_column(sh, lay, "S-001", extra)
    sh.title_block(status=STATUS_OVERRIDE)
    sh.save(os.path.join(out, "S-001"))


# ====================================================================== E-001
def sheet_e001(lay: L.Layout, out):
    if lay.cfg.power_architecture == "dc800":
        return sheet_e001_dc(lay, out)
    sh = new_sheet(lay, "E-001", "Power one-line", "NTS", 5)
    d, cfg = lay.d, lay.cfg
    V = 480 if d["voltage"].startswith("480") else (208 if d["voltage"].startswith("208 V 3") else 240)
    three = V != 240
    def amps(kw, v=V, pf=0.95):
        return kw * 1000 / (math.sqrt(3) * v * pf) if (three and v != 240) else kw * 1000 / (v * pf)
    ups_kva = d["ups_kva_each"]; nups = d["ups_modules"]
    ups_in_a = std(ups_kva * 1000 / (math.sqrt(3) * V) * 1.25) if three else std(ups_kva * 1000 / V * 1.25)
    v_pdu = 415 if V == 480 else V
    pdu_a = std(d["per_rack_kw"] * 1000 / (math.sqrt(3) * v_pdu * 0.95) * 1.25) if three else std(d["per_rack_kw"] * 1000 / (v_pdu * 0.95) * 1.25)
    cool_key = lay.notes.get("air_key", "inrow300")
    cool_unit_kw = L.LIB[cool_key]["kw"] / L.COOLING_LIBRARY["inrow_dx"]["cop"] if lay.is_container else L.COOLING_LIBRARY["cabinet_dx"]["unit_kw"] / L.COOLING_LIBRARY["cabinet_dx"]["cop"]
    cool_a = std(amps(cool_unit_kw) * 1.25)
    cus = [i for i in lay.items if i.tag.startswith("CU")]
    pumps = [i for i in lay.items if i.tag.startswith("PU") or i.tag.startswith("CDU")]
    dc = lay.find("DC1")
    pnlm_load_kw = len(cus) * cool_unit_kw + len(pumps) * 5 + (12 if dc else 0) + 1.5
    pnlm_a = std(amps(pnlm_load_kw) * 1.25)
    gen_kva = math.ceil(d["total_kw"] * 1.25 / 0.8 / 10) * 10

    sh.view_title(30, TOP - 8, "POWER ONE-LINE DIAGRAM", "NTS")
    x_main = 70.0
    y = TOP - 30
    # utility
    sh.text(x_main, y, "UTILITY", h=3, bold=True, ha="center")
    sh.text(x_main, y - 4, f"{d['voltage']}, {'3 ph 4 W' if three else '1 ph 3 W'}, {d['service_amps_calc']} A calc", h=2.0, ha="center", c=MUTED)
    sh.line(x_main, y - 6, x_main, y - 14, lw=1.0)
    sh.circle(x_main, y - 18, 4, lw=0.8); sh.text(x_main, y - 18, "kWh", h=1.6, ha="center", va="center")
    sh.text(x_main + 6, y - 18, "Utility meter + P_utility pulse (meter1)", h=1.9, va="center", c=MUTED)
    sh.line(x_main, y - 22, x_main, y - 30, lw=1.0)
    # service section
    sym_box(sh, x_main - 28, y - 70, 56, 40, "SVC — SERVICE SECTION", [f"Main CB {d['service_breaker_a']} A, {V} V", "NEMA 4X, exterior end wall", "Type 1 SPD 100 kA", "Ground bar / GES bond"], kind="power")
    sh.text(x_main + 32, y - 44, f"CTP-E1 HOLD: licensed electrician", h=1.8, c=CTP_C)
    sh.line(x_main, y - 70, x_main, y - 84, lw=1.0)
    # ATS
    if lay.is_container:
        sym_box(sh, x_main - 28, y - 112, 56, 28, "ATS" + ("" if cfg.generator else " (optional)"), [f"{d['service_breaker_a']} A, 4 pole, open transition", "Generator-ready; EPO interlock"], kind="power")
        sym_box(sh, x_main + 50, y - 112, 56, 28, "GENERATOR" + ("" if cfg.generator else " (optional)"), [f"{gen_kva} kVA diesel, {V} V", "Site item, 2 h fuel min"], kind="power")
        sh.line(x_main + 28, y - 98, x_main + 50, y - 98, lw=1.0, ls="-" if cfg.generator else "--")
        sh.line(x_main, y - 112, x_main, y - 126, lw=1.0)
        y_bus = y - 128
    else:
        sh.text(x_main + 6, y - 78, "Generator inlet 50 A + manual transfer (optional)", h=1.8, c=MUTED)
        y_bus = y - 86
    # main bus
    sh.line(x_main - 30, y_bus, x_main + 300, y_bus, lw=2.0)
    sh.text(x_main + 302, y_bus, f"MAIN BUS {V} V", h=2.2, va="center", bold=True)
    # branch: UPS chain
    xu = x_main
    sh.line(xu, y_bus, xu, y_bus - 10, lw=1.0)
    sym_breaker(sh, xu, y_bus - 15, "CB-UPS", f"{ups_in_a} A x {nups}")
    sh.line(xu, y_bus - 20, xu, y_bus - 30, lw=1.0)
    ups_lbl = f"UPS x{nups} ({cfg.redundancy})"
    ups_lines = [f"{ups_kva} kVA each, {'rack-mount' if lay.notes.get('rack_ups') or not lay.is_container else 'modular frame'}",
                 f"Battery {d['battery_kwh']} kWh Li-ion, {cfg.ups_minutes} min", "Internal static + maintenance bypass", "Modbus TCP to BEN Controller"]
    sym_box(sh, xu - 32, y_bus - 72, 64, 42, ups_lbl, ups_lines, kind="power")
    sh.text(xu + 34, y_bus - 40, "EPO: shunt-trip UPS output (CTQ-E3)", h=1.8, c=RED)
    sh.line(xu, y_bus - 72, xu, y_bus - 84, lw=1.0)
    yy = y_bus - 84
    if V == 480:
        sym_box(sh, xu - 28, yy - 26, 56, 26, "ISOLATION TRANSFORMER", [f"{math.ceil(ups_kva * nups / 1.0 / 25) * 25 if nups == 1 else ups_kva} kVA, 480 - 415/240 V", "K-13, Cu, shielded"], kind="power")
        sh.line(xu, yy - 26, xu, yy - 38, lw=1.0); yy -= 38
    pnl_name = "PNL-IT" if (lay.notes.get("rack_ups") or not lay.is_container) else "UPS OUTPUT DISTRIBUTION"
    sym_box(sh, xu - 32, yy - 26, 64, 26, pnl_name, [f"{v_pdu} V, {std(amps(cfg.it_kw, v_pdu) * 1.25)} A main", f"{2 * cfg.racks} x {pdu_a} A 3P branch (A + B per rack)" if three else f"{2 * cfg.racks} x {pdu_a} A 2P branch"], kind="power")
    sh.line(xu, yy - 26, xu, yy - 36, lw=1.0)
    yb = yy - 36
    sh.line(xu - 30, yb, xu + 150, yb, lw=1.4)
    racks = lay.by_kind("rack")
    nshow = min(len(racks), 6)
    for i in range(nshow):
        xr = xu - 24 + i * 30
        sh.line(xr, yb, xr, yb - 8, lw=0.8)
        sym_breaker(sh, xr, yb - 12, "", f"{pdu_a} A")
        sh.line(xr, yb - 16, xr, yb - 24, lw=0.8)
        sym_box(sh, xr - 11, yb - 44, 22, 20, f"R{i+1}", ["PDU A", "PDU B", f"{pdu_a} A"], kind="rack", title_h=2.2)
    if len(racks) > nshow:
        sh.text(xu - 24 + nshow * 30, yb - 34, f"... to R{len(racks)}", h=2.0, c=MUTED)
    sh.text(xu - 30, yb - 50, f"Rack PDUs: 2 per rack (A/B), {pdu_a} A, {v_pdu} V, metered per outlet group; {d['per_rack_kw']} kW/rack design", h=1.9, c=MUTED)
    # branch: mechanical panel
    xm = x_main + 200
    sh.line(xm, y_bus, xm, y_bus - 10, lw=1.0)
    sym_breaker(sh, xm, y_bus - 15, "CB-M", f"{pnlm_a} A")
    sh.line(xm, y_bus - 20, xm, y_bus - 30, lw=1.0)
    sym_box(sh, xm - 32, y_bus - 60, 64, 30, "PNL-M — MECHANICAL", [f"{V} V, {pnlm_a} A main, {pnlm_load_kw:.1f} kW connected", "Not on UPS; EPO shunt-trips cooling", "Surge: Type 2 SPD"], kind="power")
    sh.line(xm, y_bus - 60, xm, y_bus - 70, lw=1.0)
    ym = y_bus - 70
    sh.line(xm - 30, ym, xm + 120, ym, lw=1.4)
    loads = [(c.tag, f"{cool_a} A") for c in cus] + [(p.tag, f"{std(amps(5) * 1.25)} A") for p in pumps]
    if dc:
        loads.append(("DC1", f"{std(amps(12) * 1.25)} A"))
    loads += [("LTG", "20 A"), ("RCPT", "20 A"), ("CTL", "15 A")]
    for i, (tag, a) in enumerate(loads[:8]):
        xl = xm - 26 + i * 20
        sh.line(xl, ym, xl, ym - 8, lw=0.8)
        sym_breaker(sh, xl, ym - 12, "", a)
        sh.line(xl, ym - 16, xl, ym - 22, lw=0.8)
        sh.rect(xl - 8, ym - 34, 16, 12, fc=FILL["cooling" if tag[:2] in ("CU", "PU", "CD", "DC") else "controls"], ec=EDGE["cooling" if tag[:2] in ("CU", "PU", "CD", "DC") else "controls"], lw=0.6)
        sh.text(xl, ym - 28, tag, h=1.8, ha="center", va="center", bold=True)
    if len(loads) > 8:
        sh.text(xm - 26 + 8 * 20, ym - 28, f"+{len(loads) - 8} more", h=1.8, c=MUTED)
    # grounding electrode system
    yg = 95
    sh.text(30, yg + 26, "GROUNDING ELECTRODE SYSTEM (NEC 250)", h=3, bold=True)
    sh.line(40, yg + 14, 300, yg + 14, lw=2.0); sh.text(302, yg + 14, "TMGB 25x6 Cu bar in SVC", h=2.0, va="center")
    for i, lab in enumerate(["Ground rod 1 (3 m Cu-clad)", "Ground rod 2 (>= 1.8 m apart)", "Pad rebar (Ufer) where available", "Container frame bond (2 places, exothermic)", "Rack / tray ground bus, 6 AWG per rack", "UPS, panels, CDU, condenser frames"]):
        xg = 50 + i * 46
        sh.line(xg, yg + 14, xg, yg + 4, lw=0.8)
        if i < 3:
            sh.line(xg, yg + 4, xg, yg - 4, lw=1.0); sh.line(xg - 4, yg - 4, xg + 4, yg - 4, lw=1.0); sh.line(xg - 2.5, yg - 6, xg + 2.5, yg - 6, lw=0.8); sh.line(xg - 1, yg - 8, xg + 1, yg - 8, lw=0.6)
        else:
            sh.rect(xg - 5, yg - 4, 10, 8, fc=FILL["structure"], lw=0.5)
        for k, ln in enumerate(_wrap(lab, 22)):
            sh.text(xg, yg - 12 - k * 2.8, ln, h=1.8, ha="center")
    sh.text(30, yg - 24, "Resistance targets: electrode <= 25 ohm (<= 5 ohm target), every bond <= 0.1 ohm (CTQ-E2, WITNESS). Signal reference: racks bonded to tray and TMGB; no isolated grounds.", h=1.9, c=MUTED)

    def extra(sh, x, y):
        rows = [["Service", f"{d['voltage']}, main {d['service_breaker_a']} A (calc {d['service_amps_calc']} A at 80 %)"],
                ["Total connected", f"{d['total_kw']} kW / {d['total_kva']} kVA (IT {cfg.it_kw:.0f} kW + cooling {d['cooling_elec_kw']} kW + aux)"],
                ["UPS", f"{nups} x {ups_kva} kVA ({cfg.redundancy}); input CB {ups_in_a} A; battery {d['battery_kwh']} kWh / {cfg.ups_minutes} min"],
                ["IT distribution", f"{v_pdu} V; {cfg.racks} racks x 2 PDU x {pdu_a} A; {d['per_rack_kw']} kW/rack"],
                ["Mechanical panel", f"{pnlm_a} A main; {len(cus)} x cooling unit {cool_a} A" + (f"; {len(pumps)} x pump/CDU" if pumps else "") + ("; dry cooler" if dc else "")],
                ["Generator (optional)", f"{gen_kva} kVA, ATS {d['service_breaker_a']} A 4P"],
                ["EPO", "Mushroom button at door (int) and on SVC (ext, NEMA 4X): shunt-trip UPS output + PNL-M main; hard-wired, monitored by a controller dry-contact input"],
                ["PUE estimate", f"{d['pue_estimate']}"]]
        y = sh.table(x, y, ["ITEM", "VALUE"], rows, [RW * 0.26, RW * 0.74], title="ELECTRICAL SCHEDULE (preliminary)", h=1.9)
        y -= 6
        notes = ["ALL BREAKER AND CONDUCTOR SIZES ARE PRELIMINARY. A licensed electrical engineer performs the short-circuit, coordination and arc-flash study (NEC 110.9, 110.10, 240.12, NFPA 70E) before the set is released for energisation.",
                 "Workers mount enclosures, trays and conduits and pull labelled cables. Only a licensed electrician lands conductors and energises (CTP-E1 HOLD).",
                 "Rack PDUs plug into labelled receptacles under the IT distribution; plug-in connections may be made by trained workers after the electrician's sign-off.",
                 "Battery: UL 9540A test data on file; disconnect and E-stop per UL 9540; ventilation per IFC 1207.",
                 "Separation: power and data in separate trays (TR-P, TR-D), 300 mm apart; crossings at 90 deg.",
                 "Labelling: every breaker, cable end and receptacle carries the tag on this sheet (CTQ-B6)."]
        return sh.notes(x, y, "ELECTRICAL NOTES", notes, h=2.0, lead=3.1)
    right_column(sh, lay, "E-001", extra)
    sh.title_block(status=STATUS_OVERRIDE)
    sh.save(os.path.join(out, "E-001"))


# ====================================================================== E-001 (dc800 variant, forward architecture study)
def sheet_e001_dc(lay: L.Layout, out):
    """Utility -> service section -> ATS -> 480 V bus -> AC/DC front end (SiC rectifier / SST modules N+1) -> 800 VDC busway
    (bipolar ±400 V with high-resistance midpoint, or unipolar 800 V with isolated return) -> DC tap-off breakers -> racks with
    800 V -> 50 V shelves; battery string on the bus; insulation monitoring; mechanical panel stays AC. docs/FORWARD_ARCHITECTURE_DECISION.md."""
    n_sheet = 1 if lay.notes.get("forward") else 5
    sh = new_sheet(lay, "E-001", "Power one-line — 800 VDC bus", "NTS", n_sheet)
    d, cfg = lay.d, lay.cfg
    V = 480
    conv = d["dc_convention"]
    bip = conv == "bipolar_400"
    def amps(kw, v=V, pf=0.95):
        return kw * 1000 / (math.sqrt(3) * v * pf)
    rect_in_a = std(amps(d["ac_dc_front_end_kw"]) * 1.25)
    tap_a = std(d["dc_bus_kw"] / cfg.racks * 1000 / d["dc_bus_v_nominal"] * 1.25)
    batt_a = std(d["battery_on_bus_kwh"] / (cfg.ups_minutes / 60) * 1000 / d["dc_bus_v_nominal"] * 1.25)
    cool_key = lay.notes.get("air_key", "inrow300")
    cool_unit_kw = L.LIB[cool_key]["kw"] / (L.COOLING_LIBRARY["dlc_hd"]["cop"] if cool_key == "inrow_cw300" else L.COOLING_LIBRARY["inrow_dx"]["cop"])
    cool_a = std(amps(cool_unit_kw) * 1.25)
    cus = [i for i in lay.items if i.tag.startswith("CU")]
    pumps = [i for i in lay.items if i.tag.startswith("PU") or i.tag.startswith("CDU")]
    dc = lay.find("DC1")
    pnlm_load_kw = len(cus) * cool_unit_kw + len(pumps) * 8 + (12 if dc else 0) + 1.5
    pnlm_a = std(amps(pnlm_load_kw) * 1.25)
    gen_kva = math.ceil(d["total_kw"] * 1.25 / 0.8 / 10) * 10

    sh.view_title(30, TOP - 8, f"POWER ONE-LINE DIAGRAM — 800 VDC BUS ({'±400 V BIPOLAR, HR MIDPOINT' if bip else '800 V UNIPOLAR, ISOLATED RETURN'})", "NTS")
    sh.text(30, TOP - 13, "FORWARD ARCHITECTURE STUDY (docs/FORWARD_ARCHITECTURE_DECISION.md, docs/research/STATE_OF_THE_ART_2026.md) — NOT FOR CONSTRUCTION; vendor efficiencies are claims; the bus window is a working assumption", h=2.0, c=RED, bold=True)
    x_main = 70.0
    y = TOP - 30
    sh.text(x_main, y, "UTILITY", h=3, bold=True, ha="center")
    sh.text(x_main, y - 4, f"{d['voltage']}, 3 ph 4 W, {d['service_amps_calc']} A calc", h=2.0, ha="center", c=MUTED)
    sh.line(x_main, y - 6, x_main, y - 14, lw=1.0)
    sh.circle(x_main, y - 18, 4, lw=0.8); sh.text(x_main, y - 18, "kWh", h=1.6, ha="center", va="center")
    sh.text(x_main + 6, y - 18, "Utility meter + P_utility pulse (meter1)", h=1.9, va="center", c=MUTED)
    sh.line(x_main, y - 22, x_main, y - 30, lw=1.0)
    sym_box(sh, x_main - 28, y - 70, 56, 40, "SVC — SERVICE SECTION", [f"Main CB {d['service_breaker_a']} A, {V} V", "NEMA 4X, exterior end wall", "Type 1 SPD 100 kA", "Ground bar / GES bond"], kind="power")
    sh.text(x_main + 32, y - 44, "CTP-E1 HOLD: licensed electrician", h=1.8, c=CTP_C)
    sh.line(x_main, y - 70, x_main, y - 84, lw=1.0)
    sym_box(sh, x_main - 28, y - 112, 56, 28, "ATS" + ("" if cfg.generator else " (optional)"), [f"{d['service_breaker_a']} A, 4 pole, open transition", "Generator-ready; EPO interlock"], kind="power")
    sym_box(sh, x_main + 50, y - 112, 56, 28, "GENERATOR" + ("" if cfg.generator else " (optional)"), [f"{gen_kva} kVA diesel, {V} V", "Site item, 2 h fuel min"], kind="power")
    sh.line(x_main + 28, y - 98, x_main + 50, y - 98, lw=1.0, ls="-" if cfg.generator else "--")
    sh.line(x_main, y - 112, x_main, y - 126, lw=1.0)
    y_bus = y - 128
    sh.line(x_main - 30, y_bus, x_main + 360, y_bus, lw=2.0)
    sh.text(x_main + 362, y_bus, f"AC BUS {V} V", h=2.2, va="center", bold=True)
    # ---- AC/DC front end
    xu = x_main
    sh.line(xu, y_bus, xu, y_bus - 10, lw=1.0)
    sym_breaker(sh, xu, y_bus - 15, "CB-FE", f"{rect_in_a} A")
    sh.line(xu, y_bus - 20, xu, y_bus - 30, lw=1.0)
    sym_box(sh, xu - 36, y_bus - 76, 72, 46, f"AC/DC FRONT END ({cfg.redundancy})",
            [f"{d['rectifier_modules']} x {d['rectifier_module_kw']} kW SiC rectifier / SST modules in {d['rectifier_cabinets']} cabinet(s)", f"{d['ac_dc_front_end_kw']} kW at {d['rectifier_eff']*100:.1f} % (VENDOR CLAIM)",
             "480 V AC -> 800 VDC, pre-charge, hot-swap", "Modbus TCP to BEN Controller", "Delta / Vertiv / Eaton / ABB class, sampling 2026"], kind="power")
    sh.text(xu + 38, y_bus - 40, "EPO: shunt-trip CB-FE + open the battery disconnect (CTQ-E3)", h=1.8, c=RED)
    sh.line(xu, y_bus - 76, xu, y_bus - 90, lw=1.0)
    # ---- DC bus
    yb = y_bus - 92
    sh.line(xu - 30, yb, xu + 190, yb, lw=2.2, c=CTQ_C)
    sh.line(xu - 30, yb - 3, xu + 190, yb - 3, lw=2.2, c=RED)
    pole_lbl = "+400 V / −400 V to ground (midpoint HRG)" if bip else "+800 V / isolated return (IT system)"
    sh.text(xu + 192, yb + 4, f"DC BUSWAY {d['dc_busway_a']} A, 800 VDC nominal", h=2.2, va="center", bold=True)
    sh.text(xu + 192, yb - 1, pole_lbl, h=1.9, va="center", bold=True)
    sh.text(xu + 192, yb - 6, f"bus {d['dc_bus_current_a']} A incl. 25 % headroom", h=1.7, va="center", c=MUTED)
    # midpoint / grounding reference + IMD
    xg = xu - 22
    if bip:
        sh.line(xg, yb - 1.5, xg, yb - 14, lw=0.8); sh.rect(xg - 3, yb - 22, 6, 8, fc=PAPER, lw=0.6); sh.text(xg + 5, yb - 18, "HRG resistor, midpoint", h=1.6, va="center")
        sh.line(xg, yb - 22, xg, yb - 28, lw=0.8); sh.line(xg - 4, yb - 28, xg + 4, yb - 28, lw=1.0); sh.line(xg - 2.5, yb - 30, xg + 2.5, yb - 30, lw=0.8); sh.line(xg - 1, yb - 32, xg + 1, yb - 32, lw=0.6)
    else:
        sh.text(xg - 6, yb - 12, "Return isolated from PE (two-wire IT system)", h=1.6, va="center")
    sym_instr(sh, xu + 8, yb - 14, "IMD")
    sh.text(xu + 14, yb - 14, f"{d['imd_count']} x insulation monitor (Bender iso685 class): {d['dc_imd_arrangement']}", h=1.6, va="center", c=MUTED)
    sym_instr(sh, xu + 8, yb - 24, "AFD"); sh.text(xu + 14, yb - 24, "DC arc-fault detection per section and per tap-off (method caveat: UL 1699B is a PV standard)", h=1.6, va="center", c=MUTED)
    sym_instr(sh, xu + 8, yb - 34, "V/I"); sh.text(xu + 14, yb - 34, "V_bus_pos, V_bus_neg, I_bus, IMD_kohm to the controller (PROTOCOL.md)", h=1.6, va="center", c=MUTED)
    # battery on the bus
    xb = xu + 150
    sh.line(xb, yb - 3, xb, yb - 12, lw=1.0, c=RED)
    sym_breaker(sh, xb, yb - 17, "SW-BAT", f"{batt_a} A DC")
    sh.line(xb, yb - 22, xb, yb - 30, lw=1.0, c=RED)
    sym_box(sh, xb - 26, yb - 62, 52, 32, "BATTERY ON BUS", [f"{d['battery_on_bus_kwh']} kWh LFP, {d['battery_string_v']}", f"{cfg.ups_minutes} min at IT load; no UPS, no DC/DC", "pre-charge, fuses, BMS Modbus", "UL 9540 / 9540A data on file"], kind="power")
    # racks
    racks = lay.by_kind("rack")
    nshow = min(len(racks), 6)
    yr = yb - 44
    for i in range(nshow):
        xr = xu - 24 + i * 24
        sh.line(xr, yb - 3, xr, yr + 6, lw=0.8, c=RED)
        sym_breaker(sh, xr, yr + 2, "", f"{tap_a} A DC")
        sh.line(xr, yr - 2, xr, yr - 10, lw=0.8)
        sym_box(sh, xr - 10, yr - 40, 20, 30, f"R{i+1}", ["DC tap-off", f"{d['rack_shelves_per_rack']} x {d['rack_shelf_kw']} kW", "800->50 V shelf", "or MGX rack"], kind="rack", title_h=2.2)
    if len(racks) > nshow:
        sh.text(xu - 24 + nshow * 24, yr - 24, f"... to R{len(racks)}", h=2.0, c=MUTED)
    sh.text(xu - 30, yr - 46, f"Rack interface: {d['rack_interface']}; shelf efficiency {d['rack_shelf_eff']*100:.1f} % is a VENDOR CLAIM ({d['dc_bus_kw']} kW on the bus for {cfg.it_kw:.0f} kW IT)", h=1.8, c=MUTED)
    sh.text(xu - 30, yr - 50, f"Bus window {d['dc_window_v'][0]}–{d['dc_window_v'][1]} V = WORKING ASSUMPTION ({d['dc_window_basis']}); Diablo 400 states ±400 V ±0.5 % regulation only.", h=1.8, c=RED)
    # ---- mechanical panel (AC)
    xm = x_main + 330
    sh.line(xm, y_bus, xm, y_bus - 10, lw=1.0)
    sym_breaker(sh, xm, y_bus - 15, "CB-M", f"{pnlm_a} A")
    sh.line(xm, y_bus - 20, xm, y_bus - 30, lw=1.0)
    sym_box(sh, xm - 32, y_bus - 60, 64, 30, "PNL-M — MECHANICAL (AC)", [f"{V} V, {pnlm_a} A main, {pnlm_load_kw:.1f} kW connected", "Not on the DC bus; EPO shunt-trips cooling", "Surge: Type 2 SPD"], kind="power")
    sh.line(xm, y_bus - 60, xm, y_bus - 70, lw=1.0)
    ym = y_bus - 70
    sh.line(xm - 30, ym, xm + 70, ym, lw=1.4)
    loads = [(c.tag, f"{cool_a} A") for c in cus] + [(p.tag, f"{std(amps(8) * 1.25)} A") for p in pumps]
    if dc:
        loads.append(("DC1", f"{std(amps(12) * 1.25)} A"))
    loads += [("LTG", "20 A"), ("RCPT", "20 A"), ("CTL", "15 A")]
    for i, (tag, a) in enumerate(loads[:5]):
        xl = xm - 26 + i * 20
        sh.line(xl, ym, xl, ym - 8, lw=0.8)
        sym_breaker(sh, xl, ym - 12, "", a)
        sh.line(xl, ym - 16, xl, ym - 22, lw=0.8)
        sh.rect(xl - 8, ym - 34, 16, 12, fc=FILL["cooling" if tag[:2] in ("CU", "PU", "CD", "DC") else "controls"], ec=EDGE["cooling" if tag[:2] in ("CU", "PU", "CD", "DC") else "controls"], lw=0.6)
        sh.text(xl, ym - 28, tag, h=1.8, ha="center", va="center", bold=True)
    if len(loads) > 5:
        sh.text(xm - 26, ym - 40, f"+{len(loads) - 5} more: " + ", ".join(t for t, _ in loads[5:]), h=1.8, c=MUTED)
    # grounding electrode system + DC grounding note
    yg = 80
    sh.text(30, yg + 26, "GROUNDING ELECTRODE SYSTEM (NEC 250) AND DC GROUNDING / MIDPOINT", h=3, bold=True)
    sh.line(40, yg + 14, 300, yg + 14, lw=2.0); sh.text(302, yg + 14, "TMGB 25x6 Cu bar in SVC", h=2.0, va="center")
    for i, lab in enumerate(["Ground rod 1 (3 m Cu-clad)", "Ground rod 2 (>= 1.8 m apart)", "Pad rebar (Ufer) where available", "Container frame bond (2 places, exothermic)", "Rack / busway / shelf chassis, 6 AWG per rack", "DC midpoint HRG resistor" if bip else "IMD reference (no bonded pole)"]):
        xg2 = 50 + i * 46
        sh.line(xg2, yg + 14, xg2, yg + 4, lw=0.8)
        if i < 3:
            sh.line(xg2, yg + 4, xg2, yg - 4, lw=1.0); sh.line(xg2 - 4, yg - 4, xg2 + 4, yg - 4, lw=1.0); sh.line(xg2 - 2.5, yg - 6, xg2 + 2.5, yg - 6, lw=0.8); sh.line(xg2 - 1, yg - 8, xg2 + 1, yg - 8, lw=0.6)
        else:
            sh.rect(xg2 - 5, yg - 4, 10, 8, fc=FILL["structure"], lw=0.5)
        for k, ln in enumerate(_wrap(lab, 22)):
            sh.text(xg2, yg - 12 - k * 2.8, ln, h=1.8, ha="center")
    sh.text(30, yg - 24, f"DC grounding: {d['dc_grounding']}.", h=1.9, c=MUTED)
    sh.text(30, yg - 28, f"Convention: {d['dc_convention_spec']}. Both conventions must be servable; this sheet is drawn for {d['dc_convention']}.", h=1.9, c=MUTED)

    def extra(sh, x, y):
        rows = [["Service (AC)", f"{d['voltage']}, main {d['service_breaker_a']} A (calc {d['service_amps_calc']} A at 80 %)"],
                ["Total connected", f"{d['total_kw']} kW / {d['total_kva']} kVA (IT {cfg.it_kw:.0f} kW + cooling {d['cooling_elec_kw']} kW + aux)"],
                ["AC/DC front end", f"{d['rectifier_modules']} x {d['rectifier_module_kw']} kW ({cfg.redundancy}); {d['ac_dc_front_end_kw']} kW; CB-FE {rect_in_a} A; eff {d['rectifier_eff']*100:.1f} % vendor claim"],
                ["DC bus", f"800 VDC, {d['dc_convention_label']}; {d['dc_bus_current_a']} A -> busway {d['dc_busway_a']} A; {d['dc_bus_v_pole']} V to ground"],
                ["Bus window", f"{d['dc_window_v'][0]}-{d['dc_window_v'][1]} V: {d['dc_window_basis']}"],
                ["Rack interface", f"{cfg.racks} racks x {d['rack_shelves_per_rack']} x {d['rack_shelf_kw']} kW 800->50 V shelves, tap-off {tap_a} A DC each; {d['per_rack_kw']} kW/rack"],
                ["Battery on bus", f"{d['battery_on_bus_kwh']} kWh / {cfg.ups_minutes} min; disconnect {batt_a} A DC; no UPS modules"],
                ["Protection / monitoring", f"{d['imd_count']} x IMD, DC AFD per section, DC MCCB 1000 V class at bus, battery and tap-offs"],
                ["Mechanical panel (AC)", f"{pnlm_a} A main; {len(cus)} x in-row {cool_a} A" + (f"; {len(pumps)} x CDU" if pumps else "") + ("; dry cooler" if dc else "")],
                ["Stated savings (assumption)", f"-{d['dc_loss_saving_kw']} kW distribution loss ({d['dc_loss_saving_frac']*100:.0f} %); copper {d['copper_kg_dc_bus']} vs {d['copper_kg_ac_feeders']} kg (-{d['copper_saving_pct']} %, area-ratio method)"],
                ["PUE estimate", f"{d['pue_estimate']} (rectifier + shelf losses from vendor claims)"]]
        y = sh.table(x, y, ["ITEM", "VALUE"], rows, [RW * 0.28, RW * 0.72], title="ELECTRICAL SCHEDULE (study, preliminary)", h=1.8)
        y -= 6
        notes = ["STUDY SHEET: not for construction. Listings for 800 VDC busway, DC breakers and the front end are to be confirmed in the program (COMPLIANCE.md forward section); a field evaluation path is assumed.",
                 "DC arc-flash: no settled IEEE 1584 method for DC; the study uses the NFPA 70E Annex D.5 (Doan) method with the equipment-specific data from the vendor; labels are preliminary.",
                 "The 760-920 V bus window is a working assumption pending OCP Diablo 400 section 9.3.1 / NVIDIA MGX power rack spec; efficiencies of the front end and the rack shelves are vendor claims to be measured on the test cell.",
                 "Both DC conventions (±400 V HR midpoint; 800 V unipolar isolated return) must be servable: bus insulation 1000 VDC class, IMD selectable, tap-offs labelled per convention.",
                 "First ground fault on the IT bus alarms and locates; it does not trip (E17). A second fault is pole-to-pole: the tap-off DC breaker clears it.",
                 "Battery: UL 9540A test data on file; string disconnect with pre-charge; ventilation per IFC 1207; the battery is sized so the bus never leaves the window above the string cutoff.",
                 "Only a licensed electrician lands conductors and energises (CTP-E1 HOLD); DC polarity verified at every tap-off before load (CTQ-E8)."]
        return sh.notes(x, y, "ELECTRICAL NOTES (800 VDC)", notes, h=1.9, lead=3.0)
    right_column(sh, lay, "E-001", extra)
    sh.title_block(status=STATUS_OVERRIDE)
    sh.save(os.path.join(out, "E-001"))


# ====================================================================== M-001 (dlc_hd variant, forward architecture study)
def sheet_m001_hd(lay: L.Layout, out):
    """High-density DLC: row CDUs (N+1 pumps) on a W45 warm-water secondary loop (40/50 C design), DN80 manifolds with UQD drops
    to the cold plates of every rack, in-row fan coils on the same loop for the residual air, leak detection per rack with row
    isolation valves (leak-to-isolation time E19), W45 dry coolers on the primary and a heat-reuse plate heat exchanger (option)."""
    n_sheet = 2 if lay.notes.get("forward") else 6
    sh = new_sheet(lay, "M-001", "Cooling P&ID — high-density liquid (W45)", "NTS", n_sheet)
    d, cfg = lay.d, lay.cfg
    sh.view_title(30, TOP - 8, "COOLING P&ID — HIGH-DENSITY DIRECT LIQUID COOLING, W45 WARM-WATER LOOP, ROW CDU N+1", "NTS")
    sh.text(30, TOP - 13, "FORWARD ARCHITECTURE STUDY (docs/FORWARD_ARCHITECTURE_DECISION.md) — NOT FOR CONSTRUCTION; CDU, UQD and dry-cooler selections are vendor classes, not quotes", h=2.0, c=RED, bold=True)
    xleft = 40
    yb = TOP - 90
    # primary: W45 dry cooler bank + heat reuse HX
    sym_hx(sh, xleft, yb, 50, 34, f"DC1 W45 DRY COOLER BANK ({math.ceil(d['liquid_heat_kw'] * 1.15)} kW)")
    sh.text(xleft + 25, yb + 26, "EC fans, no chiller, no adiabatic", h=1.6, ha="center", c=MUTED)
    sh.text(xleft + 25, yb + 22, f"{d['climate']['t_design_c']} C design; approach 8 K", h=1.6, ha="center", c=MUTED)
    sym_hx(sh, xleft, yb - 46, 50, 30, f"HRX HEAT-REUSE PHE (option), {d['heat_reuse_kw_available']} kW")
    sh.text(xleft + 25, yb - 24, "3-way diverting valve, BTU meter (E20)", h=1.6, ha="center", c=MUTED)
    sh.text(xleft + 25, yb - 28, "customer loop 45/55 C by others", h=1.6, ha="center", c=MUTED)
    xs0 = xleft + 50
    xp = xleft + 120
    sh.line(xs0, yb + 8, xp, yb + 8, lw=1.2, c=CTQ_C); sh.line(xp, yb + 26, xs0, yb + 26, lw=1.2, c=RED)
    sh.line(xs0 + 20, yb + 26, xs0 + 20, yb - 38, lw=1.0, c=RED); sh.line(xs0 + 20, yb - 38, xs0, yb - 38, lw=1.0, c=RED)
    sh.line(xs0, yb - 24, xs0 + 26, yb - 24, lw=1.0, c=CTQ_C); sh.line(xs0 + 26, yb - 24, xs0 + 26, yb + 8, lw=1.0, c=CTQ_C)
    sym_valve(sh, xs0 + 20, yb - 6, vertical=True); sh.text(xs0 + 23, yb - 6, "3-way CV (reuse / reject)", h=1.4, va="center", c=MUTED)
    sym_valve(sh, xs0 + 10, yb + 8); sym_valve(sh, xs0 + 10, yb + 26); sh.text(xs0 + 10, yb + 2, "ISO", h=1.4, ha="center", c=MUTED)
    sym_pump(sh, xs0 + 40, yb + 8); sh.text(xs0 + 40, yb + 1.5, "P1/P2 N+1 (primary)", h=1.5, ha="center")
    sh.rect(xs0 + 50, yb + 6, 6, 4, fc=PAPER, lw=0.5); sh.text(xs0 + 53, yb + 1.5, "STR", h=1.4, ha="center")
    sym_instr(sh, xs0 + 62, yb + 14, "FM-101"); sym_instr(sh, xs0 + 62, yb + 32, "TI-102"); sym_instr(sh, xs0 + 50, yb + 32, "PI-103")
    sh.line(xs0 + 46, yb - 2, xs0 + 46, yb + 40, c=MUTED, lw=0.4, ls="--"); sh.text(xs0 + 30, yb + 36, "WALL PENETRATION (end wall, sleeved + sealed)", h=1.5, c=MUTED)
    sym_tank(sh, xs0 + 54, yb - 12, 10, 8, "EXP"); sh.line(xs0 + 59, yb - 4, xs0 + 59, yb + 8, lw=0.5)
    sh.text(xs0 + 66, yb - 8, "Expansion, air separator, PRV, make-up with RPZ + meter; treated water (25 % PG where t_min < 0 C)", h=1.6, c=MUTED)
    # row CDUs
    units = [i for i in lay.items if i.tag.startswith("CDU")]
    xc = xp
    for k, u in enumerate(units):
        yc = yb - k * 46
        sym_hx(sh, xc, yc, 44, 34, f"{u.tag} ROW CDU 600 kW ({cfg.redundancy})")
        sh.text(xc + 22, yc + 26, "plate HX, pumps N+1 (E18)", h=1.6, ha="center", c=MUTED)
        sh.text(xc + 22, yc + 22, "VFD, filter 50 um, leak tray", h=1.6, ha="center", c=MUTED)
        sh.text(xc + 22, yc + 18, "Modbus TCP -> controller", h=1.6, ha="center", c=MUTED)
        if k > 0:
            sh.line(xp, yb + 8, xp, yc + 8, lw=1.2, c=CTQ_C); sh.line(xp - 4, yb + 26, xp - 4, yc + 26, lw=1.2, c=RED); sh.line(xp - 4, yc + 26, xc, yc + 26, lw=1.2, c=RED)
        sh.line(xc + 44, yc + 8, xc + 70, yc + 8, lw=1.2, c=CTQ_C); sh.line(xc + 70, yc + 26, xc + 44, yc + 26, lw=1.2, c=RED)
        sym_valve(sh, xc + 52, yc + 8); sym_valve(sh, xc + 52, yc + 26)
    # secondary manifolds, row isolation valves, racks, fan coils
    xm0 = xc + 70
    xm1 = min(xm0 + 300, 440)
    ysup, yret = yb + 8, yb + 26
    sym_valve(sh, xm0 + 8, ysup, size=3.5); sym_valve(sh, xm0 + 8, yret, size=3.5)
    sh.text(xm0 + 8, ysup - 7, "ISO1 row isolation (motorised, spring-return, closes on leak <= 15 s, CTQ-M6)", h=1.6, ha="left", c=RED)
    sh.line(xm0, ysup, xm1, ysup, lw=1.6, c=CTQ_C); sh.line(xm0, yret, xm1, yret, lw=1.6, c=RED)
    sh.text(xm0 + 50, ysup + 1.2, f"SUPPLY MANIFOLD DN80, {d['loop_supply_design_c']:.0f} C, {d['loop_flow_lpm']} L/min design", h=1.9, va="bottom", c=CTQ_C, bg=PAPER)
    sh.text(xm0 + 50, yret + 1.2, f"RETURN MANIFOLD DN80, {d['loop_return_design_c']:.0f} C (ΔT {d['loop_dt_design_k']:.0f} K)", h=1.9, va="bottom", c=RED, bg=PAPER)
    sym_instr(sh, xm0 + 24, ysup - 10, "TI-201"); sym_instr(sh, xm0 + 24, yret + 10, "TI-202"); sym_instr(sh, xm0 + 38, yret + 10, "FM-203"); sym_instr(sh, xm0 + 52, yret + 10, "PI-204")
    racks = lay.by_kind("rack")
    cus = [i for i in lay.items if i.tag.startswith("CU")]
    nshow = min(len(racks), 10)
    pitch = (xm1 - xm0 - 60) / max(1, nshow + 1)
    for i in range(nshow):
        xr = xm0 + 60 + i * pitch
        sh.line(xr, ysup, xr, ysup - 18, lw=0.8, c=CTQ_C); sh.line(xr + 6, yret, xr + 6, ysup - 18, lw=0.8, c=RED)
        sym_valve(sh, xr, ysup - 6, size=1.8, vertical=True); sym_valve(sh, xr + 6, yret - 14, size=1.8, vertical=True)
        sh.rect(xr - 6, ysup - 36, 18, 18, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6)
        sh.text(xr + 3, ysup - 23, f"R{i+1} manifold", h=1.5, ha="center", va="center")
        sh.text(xr + 3, ysup - 27, "UQD04 x cold plates", h=1.3, ha="center", va="center", c=MUTED)
        sh.text(xr + 3, ysup - 30.5, f"{d['per_rack_kw']} kW, drip tray", h=1.3, ha="center", va="center", c=MUTED)
        sh.text(xr + 3, ysup - 34, "leak sensor", h=1.3, ha="center", va="center", c=RED)
    xf = xm0 + 60 + nshow * pitch
    sh.line(xf, ysup, xf, ysup - 18, lw=0.8, c=CTQ_C); sh.line(xf + 6, yret, xf + 6, ysup - 18, lw=0.8, c=RED)
    sh.rect(xf - 6, ysup - 36, 18, 18, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6)
    sh.text(xf + 3, ysup - 23, f"CU1..{len(cus)}", h=1.5, ha="center", va="center"); sh.text(xf + 3, ysup - 27, "in-row fan coils", h=1.3, ha="center", va="center", c=MUTED)
    sh.text(xf + 3, ysup - 30.5, f"residual air {d['air_residual']:.0%}", h=1.3, ha="center", va="center", c=MUTED); sh.text(xf + 3, ysup - 34, "12 kW each at W45", h=1.3, ha="center", va="center", c=MUTED)
    sh.line(xm0 + 30, ysup - 40, xm1, ysup - 40, c=RED, lw=0.6, ls=":")
    sh.text(xm0 + 30, ysup - 43, "Leak detection: rope along manifolds + spot sensor in every rack drip tray -> leak controller -> ISO1 close + alarm (CTQ-M3, CTQ-M6, E19)", h=1.8, va="top", c=RED)
    ynote = yb - 60 - (len(units) - 1) * 46
    for k, ln in enumerate([
        f"Loop: {d['loop_water_class']} class warm water (ASHRAE W45: facility supply up to 45 C), design {d['loop_supply_design_c']:.0f}/{d['loop_return_design_c']:.0f} C, {d['loop_flow_lpm']} L/min for {d['liquid_heat_kw']} kW to liquid ({1 - d['air_residual']:.0%} of IT); no chiller.",
        "Coolant per OCP water-based cold-plate coolant spec v1.3 (or PG25 where freeze protection is needed); flush and fill through the CDU filter; pressure test 1.5 x working pressure 2 h (CTQ-M1 WITNESS); air vents at every high point.",
        "Heat reuse (E20): the return side of HRX offers the full liquid heat at ~50 C to a customer loop; the 3-way valve diverts to the dry coolers when no heat sink is present; BTU meter is the accounting reference.",
        "Residual air: in-row fan coils on the same W45 loop (sensible only, derated to 12 kW at a 40 C supply), N+1; rack inlet class per the configuration; no refrigerant inside the module.",
        "Redundancy proof: CDU pump failover (E18) and leak-to-isolation (E19) are commissioning steps 6 and 10 (software/ben_engine/commissioning.py) and monthly BEN Care proofs."]):
        sh.text(xleft, ynote - k * 3.6, ln, h=1.9, c=MUTED)
    lx, ly = 30, 70
    sh.text(lx, ly + 20, "SYMBOLS", h=2.6, bold=True)
    sym_valve(sh, lx + 4, ly + 14); sh.text(lx + 10, ly + 14, "Isolation valve (motorised at ISO1)", h=1.8, va="center")
    sym_pump(sh, lx + 4, ly + 6, r=2.5); sh.text(lx + 10, ly + 6, "Pump", h=1.8, va="center")
    sym_instr(sh, lx + 74, ly + 14, "TI-xx", r=2.8); sh.text(lx + 80, ly + 14, "Instrument (TI temp, PI pressure, FM flow)", h=1.8, va="center")
    sh.line(lx + 72, ly + 6, lx + 78, ly + 6, lw=1.4, c=CTQ_C); sh.text(lx + 80, ly + 6, "Supply line", h=1.8, va="center")
    sh.line(lx + 162, ly + 14, lx + 168, ly + 14, lw=1.4, c=RED); sh.text(lx + 170, ly + 14, "Return line", h=1.8, va="center")
    sh.line(lx + 162, ly + 6, lx + 168, ly + 6, lw=0.6, c=RED, ls=":"); sh.text(lx + 170, ly + 6, "Leak rope", h=1.8, va="center")

    def extra(sh, x, y):
        rows = [["IT load / per rack", f"{cfg.it_kw:.0f} kW / {d['per_rack_kw']} kW (dlc_hd limit 250 kW/rack)"],
                ["Cooling architecture", d["cooling_label"]],
                ["Row CDUs (N / total)", f"{d['cooling_units_n']} / {d['cooling_units_total']} x {d['cooling_unit_kw_derated']} kW, pumps N+1 each"],
                ["Loop", f"{d['loop_water_class']}; {d['loop_supply_design_c']:.0f}/{d['loop_return_design_c']:.0f} C; {d['loop_flow_lpm']} L/min; {d['liquid_heat_kw']} kW to liquid"],
                ["Heat reuse available", f"{d['heat_reuse_kw_available']} kW at ~{d['loop_return_design_c']:.0f} C (option HRX)"],
                ["Dry coolers", f"{math.ceil(d['liquid_heat_kw'] * 1.15)} kW rejection at {d['climate']['t_design_c']} C, W45 class, no water"],
                ["Residual air", f"{d['air_residual']:.0%} of IT = {d['air_residual'] * cfg.it_kw:.1f} kW; {lay.notes.get('n_air', 0)} x in-row fan coils 12 kW; {d['airflow_cfm']} cfm"],
                ["Isolation / leak", f"{d['rows']} row valve pair(s); leak sensor per rack; leak-to-isolation <= 15 s (E19)"],
                ["Cooling electrical", f"{d['cooling_elec_kw']} kW (COP {L.COOLING_LIBRARY['dlc_hd']['cop']}, stated)"],
                ["ASHRAE class", f"{d['ashrae_class']} air; W45 liquid; inlet alarm > 27 C"]]
        y = sh.table(x, y, ["ITEM", "VALUE"], rows, [RW * 0.32, RW * 0.68], title="COOLING SCHEDULE (study)", h=1.9)
        y -= 6
        notes = ["STUDY SHEET: not for construction. Row CDU, UQD, isolation valve and dry cooler are vendor classes (Vertiv XDU / CoolIT CHx / Motivair; Staubli / Parker UQD04; Belimo; Guntner / Alfa Laval) to be quoted in the program.",
                 "Piping, welding, flushing and fill by a licensed mechanical contractor (CTP-M1 HOLD); no refrigerant work inside the module.",
                 "Every drain and drip tray is water-tested before the floor is closed (CTQ-M2); leak rope and spot sensors tested wet (CTQ-M3).",
                 "Controls: CDU pumps, ISO1 and the 3-way valve follow the BEN Controller; CDU defaults to local control on loss of comms; watchdog relay (CTP-K2); loop channels T_loop_sup, T_loop_ret, F_loop, cdu_pumpN, loop_iso (PROTOCOL.md).",
                 "Fouling and water quality on a warm loop are a maintenance item (MAINTENANCE.md forward rows): quarterly water analysis, side-stream filter, annual HX ΔP check."]
        return sh.notes(x, y, "COOLING NOTES (W45 LIQUID)", notes, h=2.0, lead=3.1)
    right_column(sh, lay, "M-001", extra)
    sh.title_block(status=STATUS_OVERRIDE)
    sh.save(os.path.join(out, "M-001"))


# ====================================================================== M-001
def sheet_m001(lay: L.Layout, out):
    if lay.cfg.cooling == "dlc_hd":
        return sheet_m001_hd(lay, out)
    sh = new_sheet(lay, "M-001", "Cooling P&ID", "NTS", 6)
    d, cfg = lay.d, lay.cfg
    mode = lay.notes.get("cooling_resolved", cfg.cooling)
    sh.view_title(30, TOP - 8, f"COOLING P&ID — {d['cooling_label'].upper() if mode == cfg.cooling else L.COOLING_LIBRARY[mode]['label'].upper()}", "NTS")
    cus = [i for i in lay.items if i.tag.startswith("CU")]
    y0 = TOP - 40
    xleft = 40
    # ---------------- DX air section (micro, ben10, ben40 residual)
    if cus:
        sh.text(xleft, y0 + 4, "DX AIR SECTION" + (" (residual air load with DLC)" if mode == "dlc_cdu" else ""), h=3, bold=True)
        n = len(cus)
        pitch = min(70, 440 / n)
        for i, cu in enumerate(cus):
            x = xleft + 10 + i * pitch
            # condenser (roof / exterior)
            sym_hx(sh, x, y0 - 24, 34, 16, f"CND{i+1} condenser, roof" if lay.is_container else f"{cu.tag} condenser section (ext)")
            sh.text(x + 17, y0 - 20, "fan, EC", h=1.6, ha="center", c=MUTED)
            # evaporator in-row
            sym_hx(sh, x, y0 - 100, 34, 28, f"{cu.tag} evaporator" if lay.is_container else f"{cu.tag} evaporator (int)")
            sh.text(x + 17, y0 - 90, "EC fans", h=1.6, ha="center", c=MUTED)
            # lines: liquid (thin) and suction (thick)
            xl, xs = x + 10, x + 24
            sh.line(xl, y0 - 24, xl, y0 - 72, lw=0.6); sh.line(xs, y0 - 24, xs, y0 - 72, lw=1.4)
            sym_valve(sh, xl, y0 - 40, size=2.2, vertical=True); sym_valve(sh, xs, y0 - 40, size=2.2, vertical=True)
            sh.rect(xl - 2, y0 - 52, 4, 5, fc=PAPER, lw=0.5); sh.text(xl - 3, y0 - 49.5, "FD", h=1.4, ha="right", va="center")
            sh.circle(xl, y0 - 60, 1.6, lw=0.5); sh.text(xl - 3, y0 - 60, "SG", h=1.4, ha="right", va="center")
            sh.text(xs + 2, y0 - 50, "S", h=1.6, va="center"); sh.text(xs + 2, y0 - 58, 'HP/LP', h=1.4, va="center", c=MUTED)
            if i == 0:
                sh.text(x - 2, y0 - 62, "L", h=1.6, ha="right", va="center")
            # condensate drain
            sh.line(x + 17, y0 - 100, x + 17, y0 - 112, c=CTQ_C, lw=0.6)
            sh.poly([(x + 17, y0 - 112), (x + 20, y0 - 116), (x + 23, y0 - 112)], fc="none", ec=CTQ_C, lw=0.6, closed=False)  # trap
            # wall penetration marker (roof curb)
            sh.line(x - 2, y0 - 34, x + 36, y0 - 34, c=MUTED, lw=0.4, ls="--")
            if i == 0:
                sh.text(x - 4, y0 - 34, "ROOF / SHELL", h=1.5, ha="right", va="center", c=MUTED)
        # drain header
        xh0, xh1 = xleft + 10, xleft + 10 + (n - 1) * pitch + 40
        sh.line(xh0, y0 - 116, xh1, y0 - 116, c=CTQ_C, lw=0.8)
        sh.text(min(xh1 + 2, 300), y0 - 116, "Condensate header 32 mm PVC, fall 1:100 -> exterior drain / pump (CTQ-M2)", h=1.8, va="center", c=CTQ_C, bg=PAPER)
        # leak rope
        sh.line(xh0, y0 - 122, xh1, y0 - 122, c=RED, lw=0.6, ls=":")
        sh.text(min(xh1 + 2, 300), y0 - 122, "Leak rope under every unit -> leak controller / Pod E (CTQ-M3)", h=1.8, va="center", c=RED, bg=PAPER)
        notes_y = y0 - 130
        refr = _refrigerant_note(lay)
        sh.text(xleft, notes_y, refr[0], h=1.9, c=MUTED)
        sh.text(xleft, notes_y - 3.5, refr[1], h=1.9, c=MUTED)
        sh.text(xleft, notes_y - 7, f"Each unit: {L.LIB.get(lay.notes.get('air_key', 'inrow300'), {}).get('kw', 5.8) if lay.is_container else 5.8} kW sensible; EC fans modulate on supply temp 18-22 C and dP_aisle setpoint; "
                "line sizes PLACEHOLDER L 3/8\" / S 7/8\" for <= 15 m equivalent — HVAC technician sizes per manufacturer table (CTP-M1 HOLD).", h=1.9, c=MUTED)
        y_water = notes_y - 17
    else:
        y_water = y0
    # ---------------- water / liquid section (ben20 RDHx, ben40 DLC)
    if mode in ("rdhx_drycooler", "dlc_cdu"):
        sh.text(xleft, y_water + 4, "LIQUID SECTION — " + ("REAR-DOOR HEAT EXCHANGERS + DRY COOLER" if mode == "rdhx_drycooler" else "DIRECT LIQUID COOLING: CDU (N+1) + DRY COOLER"), h=3, bold=True)
        yb = y_water - 60
        # dry cooler
        sym_hx(sh, xleft, yb, 50, 34, "DC1 DRY COOLER (site pad)")
        sh.text(xleft + 25, yb + 26, "EC fans, adiabatic pads opt.", h=1.6, ha="center", c=MUTED)
        sh.text(xleft + 25, yb + 22, f"{d['climate']['t_design_c']} C design, 30 % PG", h=1.6, ha="center", c=MUTED)
        # primary loop: supply low, return high
        xs0 = xleft + 50
        xp = xleft + 110
        sh.line(xs0, yb + 8, xp, yb + 8, lw=1.2, c=CTQ_C)      # supply to building
        sh.line(xp, yb + 26, xs0, yb + 26, lw=1.2, c=RED)      # return
        sym_valve(sh, xs0 + 10, yb + 8); sym_valve(sh, xs0 + 10, yb + 26)
        sh.text(xs0 + 10, yb + 2, "ISO", h=1.4, ha="center", c=MUTED)
        sym_pump(sh, xs0 + 28, yb + 8); sh.text(xs0 + 28, yb + 1.5, "P1/P2 N+1", h=1.5, ha="center")
        sh.rect(xs0 + 40, yb + 6, 6, 4, fc=PAPER, lw=0.5); sh.text(xs0 + 43, yb + 1.5, "STR", h=1.4, ha="center")
        sym_instr(sh, xs0 + 52, yb + 14, "FM-101"); sym_instr(sh, xs0 + 52, yb + 32, "TI-102")
        sym_instr(sh, xs0 + 40, yb + 32, "PI-103")
        sh.text(xs0 + 20, yb + 36, "WALL PENETRATION (end wall, sleeved + sealed)", h=1.5, c=MUTED)
        sh.line(xs0 + 36, yb - 2, xs0 + 36, yb + 40, c=MUTED, lw=0.4, ls="--")
        sym_tank(sh, xs0 + 44, yb - 12, 10, 8, "EXP")
        sh.line(xs0 + 49, yb - 4, xs0 + 49, yb + 8, lw=0.5)
        sh.text(xs0 + 56, yb - 8, "Expansion tank, air separator, PRV 6 bar, make-up with RPZ backflow preventer + meter (make-up alarm)", h=1.6, c=MUTED)
        # pumping unit / CDUs
        units = [i for i in lay.items if i.tag.startswith("PU") or i.tag.startswith("CDU")]
        xc = xp
        for k, u in enumerate(units):
            yc = yb + 0 - k * 46
            sym_hx(sh, xc, yc, 44, 34, f"{u.tag} {'PUMPING UNIT' if u.tag.startswith('PU') else 'CDU'} ({cfg.redundancy})")
            sh.text(xc + 22, yc + 26, "plate HX, pumps N+1", h=1.6, ha="center", c=MUTED)
            sh.text(xc + 22, yc + 22, "VFD, 2-way CV, leak tray", h=1.6, ha="center", c=MUTED)
            sh.text(xc + 22, yc + 18, "Modbus TCP -> controller", h=1.6, ha="center", c=MUTED)
            if k > 0:
                sh.line(xp, yb + 8, xp, yc + 8, lw=1.2, c=CTQ_C); sh.line(xp - 4, yb + 26, xp - 4, yc + 26, lw=1.2, c=RED)
                sh.line(xp - 4, yc + 26, xc, yc + 26, lw=1.2, c=RED)
            # secondary side
            sh.line(xc + 44, yc + 8, xc + 70, yc + 8, lw=1.2, c=CTQ_C); sh.line(xc + 70, yc + 26, xc + 44, yc + 26, lw=1.2, c=RED)
            sym_valve(sh, xc + 52, yc + 8); sym_valve(sh, xc + 52, yc + 26)
        # secondary manifolds along the row
        xm0 = xc + 70
        xm1 = min(xm0 + 300, 440)
        ysup, yret = yb + 8, yb + 26
        sh.line(xm0, ysup, xm1, ysup, lw=1.6, c=CTQ_C); sh.line(xm0, yret, xm1, yret, lw=1.6, c=RED)
        dn = "DN50" if mode == "rdhx_drycooler" else "DN65"
        sh.text(xm0 + 40, ysup + 1.2, f"SUPPLY MANIFOLD {dn}, {'18' if mode == 'rdhx_drycooler' else '30'} C", h=1.9, va="bottom", c=CTQ_C, bg=PAPER)
        sh.text(xm0 + 40, yret + 1.2, f"RETURN MANIFOLD {dn}, {'26' if mode == 'rdhx_drycooler' else '40'} C", h=1.9, va="bottom", c=RED, bg=PAPER)
        sym_instr(sh, xm0 + 10, ysup - 10, "TI-201"); sym_instr(sh, xm0 + 10, yret + 10, "TI-202"); sym_instr(sh, xm0 + 24, yret + 10, "PI-203")
        racks = lay.by_kind("rack")
        nshow = min(len(racks), 10)
        pitch = (xm1 - xm0 - 40) / max(1, nshow)
        for i in range(nshow):
            xr = xm0 + 40 + i * pitch
            sh.line(xr, ysup, xr, ysup - 18, lw=0.8, c=CTQ_C); sh.line(xr + 6, yret, xr + 6, ysup - 18, lw=0.8, c=RED)
            sym_valve(sh, xr, ysup - 6, size=1.8, vertical=True); sym_valve(sh, xr + 6, yret - 6 - 8, size=1.8, vertical=True)
            lbl = f"R{i+1} RDHx" if mode == "rdhx_drycooler" else f"R{i+1} manifold"
            sh.rect(xr - 6, ysup - 34, 18, 16, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6)
            sh.text(xr + 3, ysup - 23, lbl, h=1.5, ha="center", va="center")
            sh.text(xr + 3, ysup - 29, "flex hoses" if mode == "rdhx_drycooler" else "cold plates", h=1.3, ha="center", va="center", c=MUTED)
            sh.text(xr + 3, ysup - 32, "drip tray", h=1.3, ha="center", va="center", c=MUTED)
        sh.line(xm0 + 30, ysup - 38, xm1, ysup - 38, c=RED, lw=0.6, ls=":")
        sh.text(xm0 + 30, ysup - 41, "Leak rope along manifolds and under each rack (CTQ-M3)", h=1.8, va="top", c=RED)
        sh.text(xleft, yb - 60 - (len(units) - 1) * 46, "Coolant: 30 % propylene glycol (CTQ-M4); pressure test 1.5 x working pressure 2 h (CTQ-M1 WITNESS); flush and fill through the CDU strainer; air vents at every high point.", h=1.9, c=MUTED)
        sh.text(xleft, yb - 64 - (len(units) - 1) * 46, "Secondary (TCS) loop stays inside the container; primary (FWS) runs to the dry cooler through two sleeved end-wall penetrations, insulated 25 mm and heat-traced where t_min < 0 C.", h=1.9, c=MUTED)
    # legend
    lx, ly = 30, 80
    sh.text(lx, ly + 20, "SYMBOLS", h=2.6, bold=True)
    sym_valve(sh, lx + 4, ly + 14); sh.text(lx + 10, ly + 14, "Isolation valve", h=1.8, va="center")
    sym_pump(sh, lx + 4, ly + 6, r=2.5); sh.text(lx + 10, ly + 6, "Pump", h=1.8, va="center")
    sym_instr(sh, lx + 44, ly + 14, "TI-xx", r=2.8); sh.text(lx + 50, ly + 14, "Instrument (TI temp, PI pressure, FM flow)", h=1.8, va="center")
    sh.line(lx + 42, ly + 6, lx + 48, ly + 6, lw=1.4, c=CTQ_C); sh.text(lx + 50, ly + 6, "Supply / liquid line", h=1.8, va="center")
    sh.line(lx + 132, ly + 14, lx + 138, ly + 14, lw=1.4, c=RED); sh.text(lx + 140, ly + 14, "Return / suction line", h=1.8, va="center")
    sh.line(lx + 132, ly + 6, lx + 138, ly + 6, lw=0.6, c=RED, ls=":"); sh.text(lx + 140, ly + 6, "Leak rope", h=1.8, va="center")

    def extra(sh, x, y):
        rows = [["IT load / per rack", f"{cfg.it_kw:.0f} kW / {d['per_rack_kw']} kW"],
                ["Cooling architecture (config)", d["cooling_label"]],
                ["Cooling architecture (drawn)", L.COOLING_LIBRARY[mode]["label"] + ("" if mode == cfg.cooling else "  ** DEVIATION, see note **")],
                ["Units (config N / total)", f"{d['cooling_units_n']} / {d['cooling_units_total']} x {d['cooling_unit_kw_derated']} kW (derate {d['cooling_derate']})"],
                ["Units drawn", (f"{len(cus)} x in-row DX 300 mm 20 kW class" if cus else "") + (f"; {lay.notes.get('n_rdhx', 0)} x RDHx + {lay.notes.get('n_pu', 1)} x row CDU" if mode == "rdhx_drycooler" else "") + (f"; {lay.notes.get('n_cdu', 0)} x CDU" if mode == "dlc_cdu" else "")],
                ["Airflow", f"{d['airflow_cfm']} cfm ({d['airflow_cfm'] * 0.000472:.2f} m3/s)"],
                ["Cooling electrical", f"{d['cooling_elec_kw']} kW (COP {L.COOLING_LIBRARY[cfg.cooling]['cop']})"],
                ["Envelope gain at design", f"{d['envelope_gain_kw']} kW at {d['climate']['t_design_c']} C"],
                ["ASHRAE class / setpoints", f"{d['ashrae_class']}; supply 18-22 C; inlet alarm > 27 C; RH 20-70 %"]]
        y = sh.table(x, y, ["ITEM", "VALUE"], rows, [RW * 0.32, RW * 0.68], title="COOLING SCHEDULE", h=1.9)
        y -= 6
        notes = ["Refrigerant work (brazing, pressure test, evacuation, charging) only by a licensed HVAC technician (EPA 608 / F-gas). HOLD POINT CTP-M1.",
                 "Workers set units in position, bolt them down, run condensate drains, mount roof condensers on curbs and pull (do not braze) pre-insulated line sets.",
                 "Line sizes on this sheet are placeholders; final sizes, traps and oil return per the unit manufacturer's installation manual for the measured equivalent length.",
                 "Refrigerant is A1 (R-513A, GWP 631, catalog CLG-INROW / CLG-COND / CLG-REFRIG; BEN 5 cabinet AC see DX note): no A2L charge limit applies. If an A2L unit is ever substituted: detector in the hot plenum, fan interlock, no ignition sources, UL 60335-2-40 charge-vs-volume check before release.",
                 "Every drain and drip tray is water-tested before the floor is closed (CTQ-M2).",
                 "Controls: unit supply temperature setpoint and fan speed follow the gateway; units default to local control on loss of comms; PLC / RevPi watchdog relay (CTP-K2); PROTOCOL.md safety rules."]
        return sh.notes(x, y, "COOLING NOTES", notes, h=2.0, lead=3.1)
    right_column(sh, lay, "M-001", extra)
    sh.title_block(status=STATUS_OVERRIDE)
    sh.save(os.path.join(out, "M-001"))


# ====================================================================== C-001
def sheet_c001(lay: L.Layout, out):
    s = pick_scale((lay.ext_l + 600, 470))
    sh = new_sheet(lay, "C-001", "Controls layout", f"1:{s}", 7)
    ox, y_top = 40.0, TOP - 14
    oy = y_top - lay.W / s - 24
    sh.view_title(ox, y_top + 6, "SENSOR AND BEN POD PLAN", f"1:{s}")
    v = plan_view(sh, lay, ox, oy, s, labels=False)
    # racks labelled lightly
    for it in lay.items:
        if it.mount == "floor" and it.kind in ("rack", "cooling", "power"):
            v.text(it.cx, it.cy, it.tag, h=1.6, ha="center", va="center", c=MUTED, rot=90 if it.w / s < 8 else 0)
    marker = {"T": ("^", CTQ_C), "RH": ("D", PURPLE), "dP": ("s", GREEN), "leak": ("o", RED), "door": ("P", INK), "kWh": ("h", CTP_C)}
    ax = sh.ax
    for sn in lay.sensors:
        x, y = v.p(sn.x, sn.y)
        m, c = marker[sn.kind]
        ax.plot([x], [y], marker=m, ms=4.5 if sn.kind != "T" else 3.6, mfc=PAPER if sn.id.startswith("T_in") else c, mec=c, mew=0.7, zorder=8)
    # label clusters per rack (inlet 3 heights)
    racks = lay.by_kind("rack")
    rf = lay.aisle_y0
    for i, r in enumerate(racks):
        v.text(r.cx, rf + 170, f"T_in_r{i+1}", h=1.4, ha="center", va="bottom", c=CTQ_C, rot=90)
        if lay.notes.get("plenum", 0):
            v.text(r.cx, r.y0 - 60, f"T_out_r{i+1}", h=1.3, ha="center", va="top", c=CTQ_C, rot=90)
    for sn in lay.sensors:
        if sn.id in ("RH_room", "dP_aisle", "door_main", "P_utility", "T_supply", "T_return", "leak_floor"):
            v.leader(sn.x, sn.y, 6 if sn.id != "door_main" else -8, 8 if sn.id not in ("T_return", "leak_floor") else -8, f"{sn.id} ({sn.channel})", h=1.6)
    # nodes and gateway
    for it in lay.items:
        if it.kind == "controls" and it.tag != "LEAK":
            v.rect(it.x0, it.y0, it.x1, it.y1, fc=FILL["controls"], ec=PURPLE, lw=0.7, z=7)
            v.text(it.cx, it.y1 + 60, it.tag, h=1.7, ha="center", va="bottom", c=PURPLE, bold=True)
    # leak rope route
    Lm, W = lay.L, lay.W
    pts = [(100, 100), (Lm - 100, 100), (Lm - 100, W - 100), (100, W - 100), (100, 100)]
    v.poly(pts, fc="none", ec=RED, lw=0.6, ls=":", closed=False, z=3)
    for it in lay.items:
        if it.kind == "cooling" and it.mount == "floor":
            v.line(it.cx, 100, it.cx, it.y1 - 100, c=RED, lw=0.6, ls=":", z=3)
    # PoE / controls LAN route on data tray
    tr = lay.find("TR-D")
    if tr:
        v.line(tr.x0, tr.cy, tr.x1, tr.cy, c=PURPLE, lw=0.9, ls="-.", z=3)
        v.text(tr.x1 - 100, tr.cy + 60, "Controls LAN on TR-D: RS-485 + 24 VDC to Pod E; Modbus TCP to UPS/cooling; fibre uplink to CP1. Pod W on BEN Mesh (Thread)", h=1.5, ha="right", va="bottom", c=PURPLE, bg=PAPER)
    if racks:
        v.bubble(racks[0].cx, rf + 50, -14, 18, "CTQ-K1"); v.bubble(racks[-1].cx, rf + 50, 14, 18, "CTQ-K2")
    sh.north_arrow(RX - 45, TOP - 30)
    # elevation with sensor heights
    y_el_top = oy - 36
    oyE = y_el_top - lay.H / s - 6
    ve = View(sh, s, ox, oyE)
    sh.view_title(ox, y_el_top + 2, "ROW ELEVATION — SENSOR HEIGHTS (probe 50 mm in front of rack face)", f"1:{s}")
    ve.rect(0, 0, Lm, lay.H, lw=0.8)
    for it in lay.items:
        if it.mount == "floor" and it.kind in ("rack", "cooling", "power"):
            ve.rect(it.x0, 0, it.x1, it.z1, fc=FILL[it.kind], ec=EDGE[it.kind], lw=0.5, alpha=0.6)
    for i, r in enumerate(racks):
        for z in lay.notes["probe_heights"]:
            x, y = ve.p(r.cx, z)
            ax.plot([x], [y], marker="^", ms=3.6, mfc=PAPER, mec=CTQ_C, mew=0.7, zorder=8)
    if racks:
        r = racks[0]
        for k, z in enumerate(lay.notes["probe_heights"]):
            ve.dim_v(0, z, 0, -8 - 7 * k, label=f"{z}", side="left", h=1.8)
    for it in lay.items:
        if it.kind == "controls" and it.code == "CTL-POD" and it.mount != "ext":
            ve.rect(it.x0, it.z0, it.x1, it.z1, fc=FILL["controls"], ec=PURPLE, lw=0.7)
            ve.text(it.cx, it.z1 + 60, it.tag, h=1.6, ha="center", c=PURPLE, bold=True)
    gw = lay.find("CP1")
    if gw and lay.is_container:
        ve.rect(Lm - 350, gw.z0, Lm - 50, gw.z1, fc=FILL["controls"], ec=PURPLE, lw=0.7, ls="--")
        ve.text(Lm - 200, (gw.z0 + gw.z1) / 2, "CP1\n(end wall)", h=1.4, ha="center", va="center", c=PURPLE)
    # network diagram, bottom-left
    nx, ny = 30, 125
    pro = lay.notes.get("controls_tier", "pro") == "pro"
    sh.text(nx, ny + 22, ("BEN CONTROLS PRO" if pro else "BEN CONTROLS LITE") + " — CONTROLS NETWORK (isolated controls LAN + BEN Mesh, no internet dependency)", h=2.8, bold=True)
    if pro:
        sym_box(sh, nx, ny - 6, 54, 24, "CP1 BEN CONTROLLER (UL 508A)", ["PLCnext AXC F 2152 + Axioline F I/O", "Karbon 400 edge: ben_engine, MQTT, OTBR", "2 x QUINT4 24 VDC, SPD, TPM 2.0"], kind="controls")
    else:
        sym_box(sh, nx, ny - 6, 54, 24, "CP1 BEN CONTROLS LITE", ["RevPi Connect 4 + DIO/AIO", "ben_engine, MQTT, OTBR on the RevPi", "QUINT4 24 VDC, watchdog relay"], kind="controls")
    sym_box(sh, nx + 66, ny - 6, 44, 24, "SWITCH", ["FL SWITCH 2008 (managed)" if pro else "Moxa EDS-2008-EL", "VLAN: controls only"], kind="controls")
    sh.line(nx + 54, ny + 6, nx + 66, ny + 6, lw=1.0, c=PURPLE)
    nn = min(lay.notes.get("n_pods", 3), 5)
    for k in range(nn):
        xk = nx + 122 + k * 26
        sh.line(nx + 110, ny + 6, xk, ny + 6, lw=0.8, c=PURPLE, ls="--" if k < nn - 1 else "-")
        sym_box(sh, xk - 10, ny - 2, 20, 16, f"P{k+1}" if k < nn - 1 else "Pod E", ["MGM240P", "Thread" if k < nn - 1 else "RS-485"], kind="controls", title_h=2.2)
    xm = nx + 122 + nn * 26 + 10
    sym_box(sh, xm, ny - 6, 50, 24, "MODBUS / SNMP", ["UPS, cooling units, CDU", "meter1 (P_utility), PDUs"], kind="power")
    sh.line(nx + 54, ny - 2, nx + 60, ny - 2, lw=0.8, c=CTP_C); sh.line(nx + 60, ny - 2, nx + 60, ny - 14, lw=0.8, c=CTP_C); sh.line(nx + 60, ny - 14, xm, ny - 14, lw=0.8, c=CTP_C); sh.line(xm, ny - 14, xm, ny - 6, lw=0.8, c=CTP_C)
    sh.text(nx, ny - 20, f"Life-safety (fire releasing panel FRP, EPO) is HARD-WIRED; the controller only monitors dry contacts (CTP-K1 HOLD). Controller outputs via interface relays: cooling enable, lights, fan boost, spare. {lay.notes.get('n_pods', 3)} BEN Pods (dashed = Thread mesh, solid = Pod E wired RS-485 + 24 VDC).", h=1.9, c=RED)
    sh.text(nx, ny - 24, "Pod telemetry 1 Hz on ben/<unit>/node/<id>/telemetry over Thread/IPv6 (mutual TLS); channel names per spec/PROTOCOL.md; calibration (gain, offset, cal_id) in the Pod Secure Vault NVM (CTQ-K3); attestation at join (CTQ-K5).", h=1.9, c=MUTED)
    # legend
    lx, ly = xm + 60, ny + 14
    for k, (kind, lab) in enumerate([("T", "Temperature Pt1000 class A on Pods (inlet 3 heights / outlet); supply / return on panel RTD"), ("RH", "RH: Vaisala HMW90 (Pro) + Pod SHT45"), ("dP", "dP taps cold vs hot: Setra 264 (Pro) / Pod SDP810"), ("leak", "Leak rope (route dotted)"), ("door", "Door contact"), ("kWh", "Meter pulse S0")]):
        m, c = marker[kind]
        ax.plot([lx], [ly - k * 4.2], marker=m, ms=4.5, mfc=PAPER if kind == "T" else c, mec=c, mew=0.7, zorder=8)
        sh.text(lx + 4, ly - k * 4.2, lab, h=1.9, va="center")

    def extra(sh, x, y):
        rows = []
        for sn in lay.sensors:
            rows.append([sn.id, sn.channel, sn.node, f"{sn.x:.0f}", f"{sn.y:.0f}", f"{sn.z:.0f}", {"T": "Pt1000 A ±0.25 C", "RH": "HMW90/SHT45 ±1.5 %RH", "dP": "264/SDP810 ±0.4 Pa", "leak": "rope 0/1", "door": "reed 0/1", "kWh": "S0 pulse"}[sn.kind]])
        # cap rows to fit: group inlet sensors
        if len(rows) > 40:
            grouped = [r for r in rows if not r[0].startswith("T_in_r")]
            n = len(racks)
            grouped.insert(0, [f"T_in_r1..r{n}_{{0.4,1.2,1.8}}", "T_in_1..3", f"node1..{lay.notes.get('n_nodes', 1)}", "rack cx", f"{rf + 50:.0f}", "400/1200/1800", "Pt1000 A ±0.25 C"])
            rows = grouped
        y = sh.table(x, y, ["SENSOR ID", "CHANNEL", "NODE ID", "x", "y", "z", "TYPE / u95"], rows,
                     [RW * 0.26, RW * 0.14, RW * 0.11, RW * 0.1, RW * 0.1, RW * 0.11, RW * 0.18], h=1.7, rowh=3.3,
                     title="SENSOR SCHEDULE (interior mm; matches twin.sensors() and PROTOCOL.md)")
        return y
    right_column(sh, lay, "C-001", extra)
    sh.title_block(status=STATUS_OVERRIDE)
    sh.save(os.path.join(out, "C-001"))


# ====================================================================== driver
GENERATORS = {"A-001": sheet_a001, "A-002": sheet_a002, "A-003": sheet_a003, "S-001": sheet_s001,
              "E-001": sheet_e001, "M-001": sheet_m001, "C-001": sheet_c001}


def write_index(lay, out):
    sheets = sheets_for(lay)
    fwd = lay.notes.get("forward")
    lines = [f"# {lay.d['tier_label']}{' forward prototype (800 VDC + high-density liquid)' if fwd else ''} — drawing set, Rev {REV['drawing_rev']} ({REV['status_title']}{' — forward architecture study' if fwd else ''})", "",
             (f"Generated {DATE} by `design/drawings/gen_drawings.py --forward` from `layout.forward_prototype_config()` (BEN 150, 150 kW in 2 racks, dc800 {lay.cfg.dc_convention}, dlc_hd); "
              f"revision from `design/REVISION.json`, change register **DC-002**. Study sheets for review beside the Rev C tier sets; nothing here is issued for construction. "
              f"Decision: `docs/FORWARD_ARCHITECTURE_DECISION.md`; BOM: `docs/BOM-ben150-forward.md`; research: `docs/research/STATE_OF_THE_ART_2026.md`.")
             if fwd else f"Generated {DATE} by `design/drawings/gen_drawings.py` from `Config.preset('{lay.tier}')`; revision from `design/REVISION.json`.",
             f"Configuration: {config_line(lay)}", f"Enclosure: {lay.d['enclosure']} — {lay.d['hardening_rating']} ({lay.d['hardening_label']}).", "",
             "| Sheet | Title | Scale | Files |", "|---|---|---|---|"]
    scales = {"A-000": "see sheet", "A-001": "see sheet", "A-002": "see sheet", "A-003": "see sheet / 1:2", "S-001": "see sheet / 1:5", "E-001": "NTS", "M-001": "NTS", "C-001": "see sheet"}
    for i, (no, title) in enumerate(sheets, 1):
        lines.append(f"| {no} | {title} (sheet {i}/{len(sheets)}) | {scales.get(no, '1:50')} | [{no}.svg]({no}.svg), [{no}.png]({no}.png) |")
    checked = f"Checked: {REV['checker']}" if REV["checked"] else "Checked: blank (requires a checker before the set is re-issued for construction)"
    lines += ["", f"Status: **{STATUS_OVERRIDE or REV['status_long']}** — Rev {REV['drawing_rev']}, {REV['issue_date']}. Drawn: BEN Engine generator; {checked}.", "",
              "| Rev | Date | Description | Checked |", "|---|---|---|---|"]
    if REV.get("supersedes"):
        sp = REV["supersedes"]
        lines.append(f"| {sp['drawing_rev']} | {sp['issue_date']} | {sp['notes']} | — |")
    lines += [f"| {REV['drawing_rev']} | {REV['issue_date']} | {REV['notes_short']} | {REV['checker'] or 'not checked'} |", ""]
    if lay.deviations:
        lines += ["## Configuration deviations applied on this set", ""] + [f"- {dv}" for dv in lay.deviations] + [""]
    lines += ["## Interference checks for this tier", "", L.checks_table([lay]), ""]
    with open(os.path.join(out, "INDEX.md"), "w") as f:
        f.write("\n".join(lines))


def hall_generators(lay):
    """Sheet number -> callable(lay, out) for the hall, numbered in sheets_for order."""
    gens = {}
    for n, (no, _title) in enumerate(sheets_for(lay), 1):
        if no == "A-000":
            gens[no] = lambda lay, out: GH.sheet_a000(lay, out, HALL_CTX)
        elif no == "A-001":
            gens[no] = lambda lay, out, n=n: GH.sheet_a001(lay, out, HALL_CTX, n)
        elif no.startswith("A-001-M"):
            gens[no] = lambda lay, out, n=n, m=int(no[-1]) - 1: GH.sheet_a001_module(lay, out, HALL_CTX, m, n)
        elif no == "A-002":
            gens[no] = lambda lay, out, n=n: GH.sheet_a002(lay, out, HALL_CTX, n)
        elif no.startswith("A-002-M"):
            gens[no] = lambda lay, out, n=n, m=int(no[-1]) - 1: GH.sheet_a002_module(lay, out, HALL_CTX, m, n)
        else:
            fn = {"A-003": GH.sheet_a003, "S-001": GH.sheet_s001, "E-001": GH.sheet_e001, "M-001": GH.sheet_m001, "C-001": GH.sheet_c001}[no]
            gens[no] = lambda lay, out, n=n, fn=fn: fn(lay, out, HALL_CTX, n)
    return gens


ALL_SHEET_NOS = list(GENERATORS) + ["A-000"] + [f"A-001-M{k}" for k in (1, 2, 3)] + [f"A-002-M{k}" for k in (1, 2, 3)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=list(L.TIER_GEOMETRY) + list(L.TIER_ALIASES), action="append")
    ap.add_argument("--sheet", choices=ALL_SHEET_NOS, action="append")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--forward", action="store_true", help=f"generate the forward prototype study set (E-001 dc800, M-001 dlc_hd) into {FORWARD_DIR}/ only")
    a = ap.parse_args(argv)
    if a.forward:
        return main_forward(a)
    tiers = [L.canonical_tier(t) for t in a.tier] if a.tier else list(L.TIERS_BY_LINEUP["rev1"])   # Rev 2 drawings go to design/drawings/rev2/ (not generated yet)
    lays = []
    for t in tiers:
        lay = L.resolve(t)
        lays.append(lay)
        out = os.path.join(HERE, t)
        os.makedirs(out, exist_ok=True)
        gens = hall_generators(lay) if lay.is_hall else GENERATORS
        sheets = [s_ for s_ in (a.sheet or list(gens)) if s_ in gens]
        for no in sheets:
            gens[no](lay, out)
            print(f"  wrote {out}/{no}.svg/.png")
        write_index(lay, out)
    if not a.tier:
        with open(os.path.join(HERE, "INTERFERENCE_CHECKS.md"), "w") as f:
            f.write("# Interference checks (generated by gen_drawings.py)\n\n")
            f.write("Result key: OK = passes; OK* = passes after the documented resolution; FAIL = does not pass as given, resolution column says what changes.\n\n")
            f.write(L.checks_table(lays) + "\n\n## Deviations applied\n\n" + L.deviations_md(lays) + "\n")
        print("  wrote INTERFERENCE_CHECKS.md")
    return 0


def main_forward(a):
    """Forward prototype study set: design/drawings/forward-ben150/ (E-001 800 VDC one-line, M-001 W45 P&ID, INDEX.md), title block
    status 'ISSUED FOR REVIEW — forward architecture study'. Not part of the Rev C tier sets; change register DC-002."""
    global STATUS_OVERRIDE
    STATUS_OVERRIDE = "ISSUED FOR REVIEW — forward architecture study, not for construction"
    cfg = L.forward_prototype_config()
    lay = L.resolve_config(cfg)
    lay.notes["forward"] = True
    out = os.path.join(HERE, FORWARD_DIR)
    os.makedirs(out, exist_ok=True)
    for no, _title in FORWARD_SHEETS:
        {"E-001": sheet_e001, "M-001": sheet_m001}[no](lay, out)
        print(f"  wrote {out}/{no}.svg/.png")
    write_index(lay, out)
    STATUS_OVERRIDE = None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
