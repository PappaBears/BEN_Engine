"""BEN 2000 (hall) sheet generators for design/drawings/gen_drawings.py.

The hall is three 12.2 m bays (each three road sections 12.2 x 3.66 x 4.2 m) site-joined into one IP66 envelope,
a power module and a plant yard (docs/TIER_AND_ENCLOSURE_DECISION.md §2). Sheets:
    A-000 site plan · A-001 general arrangement · A-001-M1..M3 module GA · A-002 interior plan (4 rows) ·
    A-002-M1..M3 module interior · A-003 envelope section with IP66 and hardening details · S-001 foundation ·
    E-001 MV one-line · M-001 cooling P&ID · C-001 controls layout
All geometry comes from design/layout.py (_resolve_hall) so the renders, assembly and CTQ register agree.
"""
from __future__ import annotations

import math
import os

import layout as L
import ctq as C
from drawkit import (Sheet, View, INK, MUTED, LIGHT, PAPER, CTQ_C, CTP_C, RED, GREEN, PURPLE, FILL, EDGE,
                     sym_box, sym_valve, sym_pump, sym_instr, sym_hx, sym_tank, sym_breaker)

RX, RW, TOP = 500.0, 326.0, 578.0
STD_BRK = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200, 225, 250, 300, 350, 400, 450, 500, 600, 700, 800, 1000, 1200, 1600, 2000, 2500, 3000, 4000]


def std(a):
    return next((b for b in STD_BRK if b >= a), 4000)


def hall_sheets(lay):
    """Sheet list for the hall tier (number, title)."""
    mods = [(f"A-001-M{m+1}", f"Module {m+1} general arrangement") for m in range(lay.modules)]
    mods2 = [(f"A-002-M{m+1}", f"Module {m+1} interior layout") for m in range(lay.modules)]
    return ([("A-000", "Site plan"), ("A-001", "General arrangement")] + mods + [("A-002", "Interior layout plan")] + mods2 +
            [("A-003", "Envelope section and hardening"), ("S-001", "Foundation and anchoring"), ("E-001", "Power one-line (MV service)"),
             ("M-001", "Cooling P&ID"), ("C-001", "Controls layout")])


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


class Ctx:
    """Bundle of the generic helpers passed in by gen_drawings (sheet factory, right column, details)."""
    def __init__(self, new_sheet, right_column, details):
        self.new_sheet, self.right_column, self.details = new_sheet, right_column, details


def _ext(lay):
    return (lay.ext_l - lay.L) / 2, (lay.ext_w - lay.W) / 2


def _hall_outline(v, lay, z=1, fc="#E3E8EF"):
    endw, wall = _ext(lay)
    v.rect(-endw, -wall, lay.L + endw, lay.W + wall, fc=fc, ec=INK, lw=1.0, z=z)
    v.rect(0, 0, lay.L, lay.W, fc=PAPER, ec=INK, lw=0.7, z=z)
    for jx in lay.module_x:                       # bay joints
        v.line(jx, -wall, jx, lay.W + wall, c=RED, lw=0.9, ls="--", z=z + 2)
    for k in (1, 2):                              # section seams within a bay (3 sections across the width)
        yy = -wall + k * L.HALL_SECTION_W
        v.line(-endw, yy, lay.L + endw, yy, c=MUTED, lw=0.5, ls=":", z=z + 2)


# ====================================================================== A-000 site plan
def sheet_a000(lay, out, ctx: Ctx):
    endw, wall = _ext(lay)
    ext_items = [i for i in lay.items if i.mount == "ext" and i.kind != "controls"]
    xs = [i.x0 for i in ext_items] + [i.x1 for i in ext_items] + [-endw - L.SITE_SETBACK - 2000, lay.L + endw + L.SITE_SETBACK]
    ys = [i.y0 for i in ext_items] + [i.y1 for i in ext_items] + [-wall - L.SITE_SETBACK - 6000, lay.W + wall + L.SITE_SETBACK]
    X0, X1, Y0, Y1 = min(xs) - 3000, max(xs) + 3000, min(ys) - 3000, max(ys) + 3000
    s = next(k for k in (100, 125, 150, 200, 250, 300) if (X1 - X0) / k <= 450 and (Y1 - Y0) / k <= 430)
    sh = ctx.new_sheet(lay, "A-000", "Site plan", f"1:{s}", 1)
    ox, y_top = 30.0, TOP - 14
    oy = y_top - 8 - (Y1 - Y0) / s   # sheet y of model Y0
    v = View(sh, s, ox - X0 / s, oy - Y0 / s)
    sh.view_title(ox, y_top + 6, "SITE PLAN — HALL, POWER MODULE, MV PAD, GENERATORS, PLANT YARD", f"1:{s}")
    # site boundary / graded area
    v.rect(X0 + 1500, Y0 + 1500, X1 - 1500, Y1 - 1500, fc="#F7F9FB", ec=MUTED, lw=0.6, ls="-.", z=0)
    v.text(X0 + 2500, Y1 - 3500, "SITE BOUNDARY / GRADED PAD — PER SURVEY", h=2.0, c=MUTED)
    # setback band around the hall (fire lane)
    v.rect(-endw - L.SITE_SETBACK, -wall - L.SITE_SETBACK, lay.L + endw + L.SITE_SETBACK, lay.W + wall + L.SITE_SETBACK, fc="none", ec=GREEN, lw=0.6, ls="--", z=1)
    v.text(lay.L / 2, -wall - L.SITE_SETBACK + 300, f"FIRE LANE / SETBACK {L.SITE_SETBACK / 1000:.1f} m (IFC 503)", h=1.9, ha="center", c=GREEN)
    # crane lane
    cr = lay.find("CRANE")
    if cr:
        v.hatch_rect(cr.x0, cr.y0, cr.x1, cr.y1, hatch="////", ec=LIGHT, z=0)
        v.text(cr.cx, cr.cy, "CRANE HARDSTAND + ACCESS LANE 6 m (100-130 t AT crane, module set from the south)", h=2.0, ha="center", va="center", c=MUTED, bg=PAPER)
    yard = lay.find("YARD")
    if yard:
        v.rect(yard.x0, yard.y0, yard.x1, yard.y1, fc="#F1F4F7", ec=MUTED, lw=0.5, ls=":", z=0)
        v.text(yard.x0 + 500, yard.y1 - 700, "PLANT YARD (crushed stone, pipe rack, bollards)", h=1.9, c=MUTED)
    # hall
    _hall_outline(v, lay)
    v.text(lay.L / 2, lay.W / 2 + 1500, f"IT HALL — 3 BAYS x 3 SECTIONS = {lay.ext_l / 1000:.1f} x {lay.ext_w / 1000:.1f} x {lay.ext_h / 1000:.1f} m", h=2.6, ha="center", va="center", bold=True)
    v.text(lay.L / 2, lay.W / 2 - 600, f"{lay.cfg.racks} racks in {lay.d['rows']} rows, DLC + fan wall, IP66 envelope, {lay.d['hardening_label']}", h=2.0, ha="center", va="center", c=MUTED)
    v.text(0, lay.W + wall + 400, "VESTIBULE / BAY 1", h=1.8, c=MUTED)
    # exterior items
    pm = lay.find("PM")
    for it in ext_items:
        if it.tag in ("CRANE", "YARD"):
            continue
        inside_pm = it.note == "in PM"
        v.rect(it.x0, it.y0, it.x1, it.y1, fc=FILL.get(it.kind, "none") if not inside_pm else "none", ec=EDGE.get(it.kind, INK), lw=0.9 if it.tag == "PM" else 0.6, ls="-" if not inside_pm else "--", z=3 if not inside_pm else 4)
        if it.tag == "PM":
            v.text(it.cx, it.y1 - 500, "POWER MODULE (3 sections): SWGR A/B · UPS 2N · BATTERY ROOMS A/B", h=2.0, ha="center", va="top", bold=True, bg=PAPER)
        else:
            h = 1.9 if it.w / s > 12 else 1.5
            v.text(it.cx, it.cy, it.tag, h=h, ha="center", va="center", bold=True, rot=90 if it.w / s < 9 and it.d / s > it.w / s else 0)
    # MV pad outline
    mv = lay.find("MV-SWGR"); xa = lay.find("XFMR-A"); xb = lay.find("XFMR-B") or xa
    if mv and xa:
        v.rect(mv.x0 - 1000, min(mv.y0, xa.y0) - 1000, xa.x1 + 1000, max(xb.y1, mv.y1) + 1000, fc="none", ec=EDGE["power"], lw=0.6, ls="-.", z=2)
        v.text(mv.x0 - 800, min(mv.y0, xa.y0) - 1400, "MV PAD: 15 kV SWITCHGEAR + 2 x 2,500 kVA\nPAD-MOUNTS (FR3), UTILITY PRIMARY METERING", h=1.8, c=EDGE["power"], va="top")
    # utility feed line
    if mv:
        v.line(X0 + 1500, mv.cy, mv.x0, mv.cy, c=EDGE["power"], lw=1.2, ls="-", z=3)
        v.text(X0 + 1800, mv.cy + 400, "UTILITY 12.47 kV (ductbank, utility riser pole / handhole per utility)", h=1.8, c=EDGE["power"])
        if pm:
            v.line(xa.x1, xa.cy, pm.x0, xa.cy, c=EDGE["power"], lw=1.0, z=3)
            v.line(xb.x1, xb.cy, pm.x0, xb.cy, c=EDGE["power"], lw=1.0, z=3)
            v.text((xa.x1 + pm.x0) / 2, xa.y0 - 500, "480 V 4,000 A duct banks A / B", h=1.6, ha="center", c=EDGE["power"])
    # feeders hall <-> power module, pipes hall <-> plant yard
    if pm:
        for k, xx in enumerate((lay.L * 0.55, lay.L * 0.62)):
            v.line(xx, lay.W + wall, xx, pm.y0 if xx < pm.x1 else pm.y0, c=EDGE["power"], lw=0.8, ls="--", z=3)
        v.text(lay.L * 0.58, lay.W + wall + 2500, "UPS output feeders A / B to row busways (trench / ductbank)", h=1.7, ha="center", c=EDGE["power"], bg=PAPER)
    dc1 = lay.find("DC1")
    if dc1:
        v.line(lay.L + endw, lay.W * 0.4, dc1.x0, lay.W * 0.4, c=EDGE["cooling"], lw=1.2, z=3)
        v.line(lay.L + endw, lay.W * 0.5, dc1.x0, lay.W * 0.5, c=RED, lw=1.2, z=3)
        v.text(lay.L + endw + 600, lay.W * 0.5 + 400, "Primary glycol DN200 supply / return on pipe rack", h=1.7, c=EDGE["cooling"], bg=PAPER)
    # dimensions
    v.dim_h(-endw, lay.L + endw, -wall, -10, label=f"{lay.ext_l:.0f} HALL")
    v.dim_v(-wall, lay.W + wall, lay.L + endw, 8, label=f"{lay.ext_w:.0f}", side="right")
    if pm:
        v.dim_v(lay.W + wall, pm.y0, lay.L * 0.3, -8, label=f"{pm.y0 - lay.W - wall:.0f} SETBACK")
        v.dim_h(pm.x0, pm.x1, pm.y1, 8, label=f"{pm.w:.0f} POWER MODULE")
    g1 = lay.find("GEN1")
    if g1 and pm:
        v.dim_h(pm.x1, g1.x0, g1.y0, -8, label=f"{g1.x0 - pm.x1:.0f} GEN CLEARANCE (NFPA 37)")
    if xa and pm:
        v.dim_h(xa.x1, pm.x0, xa.y0, -8, label=f"{pm.x0 - xa.x1:.0f} XFMR (FM 5-4)")
    if dc1:
        v.dim_h(lay.L + endw, dc1.x0, dc1.y0, -8, label=f"{dc1.x0 - lay.L - endw:.0f}")
    sh.north_arrow(RX - 45, TOP - 30)
    sh.text(ox, oy - 12, "Dimensions in mm. Site north, grades, utility point of connection and property lines per the site survey; this plan fixes the relative positions and clearances.", h=2.0, c=MUTED)

    def extra(sh, x, y):
        rows = []
        for it in ext_items:
            if it.tag in ("CRANE", "YARD"):
                continue
            rows.append([it.tag, it.code, it.label[:60], f"{it.x0:.0f}", f"{it.y0:.0f}", f"{it.w / 1000:.1f}x{it.d / 1000:.1f}", f"{it.kg:,.0f}"])
        y = sh.table(x, y, ["TAG", "CODE", "DESCRIPTION", "x0", "y0", "W x D m", "kg"], rows, [20, 24, RW - 20 - 24 - 16 - 16 - 22 - 16, 16, 16, 22, 16], h=1.6, rowh=3.2,
                     title="SITE EQUIPMENT SCHEDULE (mm, hall interior origin)")
        y -= 6
        notes = [f"Hall: {lay.modules} bays x 3 road sections ({L.HALL_SECTION_W} wide), joined on grade beams (S-001); power module 3 sections; all envelopes IP66 (hose test CTQ-A4).",
                 f"Fire apparatus access lane {L.SITE_SETBACK / 1000:.1f} m around the hall (IFC 503 / AHJ); crane lane doubles as the south fire lane. Hydrant coverage per AHJ.",
                 "Generators: NFPA 37 clearance >= 1.5 m to walls, 3 m drawn for radiator discharge and service; 48 h fuel in a UL 2085 tank with SPCC plan (PWR-FUEL-48H); exhaust away from intakes.",
                 "Pad-mount transformers FR3 ester (less-flammable): >= 0.9 m to a non-combustible wall (FM 5-4 / IEEE C57.12), 3 m drawn; utility primary metering on the MV pad; MV switchgear dead-front, lockable.",
                 "Adiabatic dry coolers: intakes >= 5 m from generator exhaust and from the fan-wall intake louvres; make-up water with backflow preventer; water-free mode below 25 C.",
                 "Setbacks to property lines, noise (dry coolers and generators) and stormwater per the site study; this sheet shows relative positions and minimum clearances only.",
                 f"Hardening {lay.d['hardening_label']}: H2 adds the 600 mm flood plinth under every section and C5-M coating; H3 adds the mantrap vestibule, ballistic panels and the shielded envelope (A-003)."]
        return sh.notes(x, y, "SITE NOTES", notes, h=2.0, lead=3.1)
    ctx.right_column(sh, lay, "A-000", extra)
    sh.title_block()
    sh.save(os.path.join(out, "A-000"))


# ====================================================================== A-001 general arrangement (hall)
def sheet_a001(lay, out, ctx: Ctx, n):
    endw, wall = _ext(lay)
    el, ew, eh = lay.ext_l, lay.ext_w, lay.ext_h
    s = 125
    sh = ctx.new_sheet(lay, "A-001", "General arrangement", f"1:{s}", n)
    ox = 30.0
    y_plan_top = TOP - 14
    oy = y_plan_top - ew / s - 10
    v = View(sh, s, ox + endw / s, oy + wall / s)
    sh.view_title(ox, y_plan_top + 6, "ROOF PLAN — BAYS, SECTION SEAMS, PENETRATIONS", f"1:{s}")
    _hall_outline(v, lay)
    for m in range(lay.modules):
        xm = m * el / lay.modules - endw + el / lay.modules / 2
        v.text(xm, lay.W / 2, f"BAY {m+1}", h=3.0, ha="center", va="center", c=MUTED, bold=True)
    # fan-wall intake louvres on the long wall (y = W side), roof penetrations for manifold/pipe entries at the blind end
    for it in lay.items:
        if it.tag.startswith("FW"):
            v.rect(it.x0, lay.W + wall - 100, it.x1, lay.W + wall + 250, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6)
            v.text(it.cx, lay.W + wall + 600, it.tag + " LOUVRE", h=1.6, ha="center", c=EDGE["cooling"])
    for k, yy in enumerate((lay.W * 0.4, lay.W * 0.5)):
        v.circle(lay.L - 600, yy, 150, fc=PAPER, ec=RED, lw=0.7)
    v.leader(lay.L - 600, lay.W * 0.5, 8, 10, "2 x DN200 sleeved pipe penetrations (end wall, gasketed frame, hose test CTQ-A4)", h=1.8, c=RED)
    v.rect(lay.L * 0.55 - 300, -wall - 200, lay.L * 0.62 + 300, -wall + 150, fc=FILL["power"], ec=EDGE["power"], lw=0.6)
    v.leader(lay.L * 0.58, -wall - 200, 10, -8, "Busway / feeder entries A and B through gasketed transit frames (ENV-SEAL-KIT)", h=1.8)
    v.text(-endw, -wall - 2600, "DOOR END — VESTIBULE", h=2.0, c=MUTED, va="top")
    v.text(lay.L + endw, -wall - 2600, "BLIND END — PLANT PENETRATIONS", h=2.0, ha="right", c=MUTED, va="top")
    v.dim_h(-endw, el - endw, -wall, -10, label=f"{el:.0f} = 3 x {el / 3:.0f}")
    v.dim_v(-wall, ew - wall, -endw, -10, label=f"{ew:.0f} = 3 x {L.HALL_SECTION_W}")
    v.bubble(lay.module_x[0], lay.W * 0.8, 14, 12, "CTP-J1", "CTP")
    # end view (door end)
    ox_end = ox + el / s + 30
    ve = View(sh, s, ox_end, oy + wall / s - (eh - ew) / s)
    sh.view_title(ox_end, y_plan_top + 6, "END VIEW — DOOR END", f"1:{s}")
    ve.rect(0, 0, ew, eh, lw=1.0)
    for k in (1, 2):
        ve.line(k * L.HALL_SECTION_W, 0, k * L.HALL_SECTION_W, eh, c=MUTED, lw=0.5, ls=":")
    ve.rect(ew / 2 - 1500, 0, ew / 2 + 1500, 2400, fc=PAPER, ec=INK, lw=0.7)
    ve.text(ew / 2, 1200, "VESTIBULE DOORS\nIP66 compression gasket\n3-point latch", h=1.6, ha="center", va="center")
    ve.rect(ew / 2 + 1700, 1200, ew / 2 + 1850, 1350, fc=FILL["fire"], ec=RED, lw=0.6); ve.text(ew / 2 + 1950, 1270, "EPO (ext)", h=1.5, va="center", c=RED)
    if lay.cfg.hardening in ("H2", "H3"):
        ve.rect(-200, -600, ew + 200, 0, fc="#D9E1EA", ec=INK, lw=0.6); ve.text(ew / 2, -300, "FLOOD PLINTH 600 (H2/H3)", h=1.6, ha="center", va="center")
    ve.dim_v(0, eh, ew, 8, label=f"{eh:.0f}", side="right")
    ve.dim_h(0, ew, 0, -8, label=f"{ew:.0f}")
    # elevations
    y_elevA_top = oy - 22
    oyA = y_elevA_top - eh / s
    va = View(sh, s, ox, oyA)
    sh.view_title(ox, y_elevA_top + 2, "ELEVATION A — LONG WALL (y = 0 SIDE), BRAND PANEL", f"1:{s}")
    va.rect(0, 0, el, eh, lw=1.0)
    for jx in lay.module_x:
        va.line(jx + endw, 0, jx + endw, eh, c=RED, lw=0.8, ls="--")
    va.corrugation(0, el, 0, eh, pitch=1000, vertical=True)   # sandwich panel joints
    pw = 6000
    va.rect(el / 2 - pw / 2, eh * 0.4, el / 2 + pw / 2, eh * 0.7, fc="#0B1018", ec="#0B1018")
    va.text(el / 2, eh * 0.55, f"SCHREIBER AI  |  {lay.d['tier_label'].upper()}", h=3.0, ha="center", va="center", c="#66E3FF", bold=True)
    va.text(el / 2, eh * 0.3, "Brand panel 1.5 mm aluminium composite, bonded + riveted to panel ribs; no penetration", h=1.6, ha="center", va="top", c=MUTED)
    va.dim_h(0, el, 0, -8, label=f"{el:.0f}")
    va.dim_v(0, eh, 0, -8, label=f"{eh:.0f}")
    y_elevB_top = oyA - 20
    oyB = y_elevB_top - eh / s
    vb = View(sh, s, ox, oyB)
    sh.view_title(ox, y_elevB_top + 2, "ELEVATION B — FAN-WALL SIDE (y = W): INTAKE LOUVRES, SERVICE DOORS", f"1:{s}")
    vb.rect(0, 0, el, eh, lw=1.0)
    for jx in lay.module_x:
        vb.line(jx + endw, 0, jx + endw, eh, c=RED, lw=0.8, ls="--")
    for it in lay.items:
        if it.tag.startswith("FW"):
            X0 = el - (it.x1 + endw)   # mirrored view
            vb.rect(X0, 600, X0 + it.w, 600 + 2400, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6)
            vb.text(X0 + it.w / 2, 1800, f"{it.tag} LOUVRE\nePM1 filter (H2)\nweather hood", h=1.5, ha="center", va="center")
    for m in range(lay.modules):
        X = m * el / lay.modules + 800
        vb.rect(X, 0, X + 1000, 2200, fc=PAPER, ec=INK, lw=0.6); vb.text(X + 500, 2400, f"DOOR M{lay.modules - m}", h=1.4, ha="center")
    vb.dim_h(0, el, 0, -8, label=f"{el:.0f}")
    sh.north_arrow(ox_end + ew / s / 2, oyA + 8)
    sh.text(ox, oyB - 10, "Dimensions in mm. Section seams dotted, bay joints dashed red (CTP-J1 HOLD). All penetrations through gasketed frames; hose test on every one (CTQ-A4 WITNESS).", h=2.0, c=MUTED)

    def extra(sh, x, y):
        d = lay.d
        rows = [["Tare: 3 bays x 3 sections + power module", f"{d['geometry']['tare_kg']:,}"],
                ["Payload (config rule, racks + CDUs + UPS + batteries)", f"{d['payload_kg']:,}"],
                ["GROSS (config)", f"{d['gross_kg']:,}"],
                ["Per road section (tare / 12 + fit-out share)", f"{d['geometry']['tare_kg'] / 12 + 800:,.0f}"],
                ["Slab + grade beam design mass", "1,200,000"],
                ["Hardening envelope adder", f"{d['envelope_area_m2']} m2 x {lay.hardening['mass_kg_m2']} kg/m2 = {d['envelope_area_m2'] * lay.hardening['mass_kg_m2']:,.0f}"]]
        y = sh.table(x, y, ["WEIGHT TABLE", "kg"], rows, [RW * 0.72, RW * 0.28], title="WEIGHTS")
        y -= 8
        notes = ["All dimensions in millimetres unless noted. Do not scale from this drawing; use figured dimensions.",
                 "Enclosure: " + d["enclosure"] + f". Hardening {d['hardening_label']}: {d['hardening_rating']}; coating {d['hardening_coating']}.",
                 "Each bay arrives as three factory-finished road sections (12.2 x 3.66 x 4.2 m); sections are set on grade beams, aligned, bolted at the splice plates and sealed with the two-stage gasket (CTP-J1 HOLD).",
                 "Every penetration is a gasketed transit frame or a sleeved and gasketed pipe entry; every door has a compression gasket and a three-point latch; the interior is held at +10 Pa by the make-up fan (ENV-PRESSURE-FAN).",
                 "Weight table: payload from the configuration rule (software/ben_engine/config.py); section lift masses on S-001; the larger governs rigging.",
                 "Occupancy: IBC Group B / F-1 to be agreed with the AHJ; lights-out operation with a service vestibule; two exits from the hall (vestibule and blind-end door M3)."]
        y = sh.notes(x, y, "GENERAL NOTES", notes, h=2.0, lead=3.1)
        return y
    ctx.right_column(sh, lay, "A-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "A-001"))


# ====================================================================== per-module sheets
def _bay_bounds(lay, m):
    endw, wall = _ext(lay)
    bay = lay.ext_l / lay.modules
    return m * bay - endw, (m + 1) * bay - endw   # interior x range (ext at the ends)


def sheet_a001_module(lay, out, ctx: Ctx, m, n):
    endw, wall = _ext(lay)
    bx0, bx1 = _bay_bounds(lay, m)
    s = 50
    no = f"A-001-M{m+1}"
    sh = ctx.new_sheet(lay, no, f"Module {m+1} general arrangement", f"1:{s}", n)
    ox, y_top = 40.0, TOP - 14
    oy = y_top - (lay.W + 2 * wall) / s - 14
    v = View(sh, s, ox - bx0 / s + endw / s, oy + wall / s)
    sh.view_title(ox, y_top + 6, f"BAY {m+1} ROOF PLAN — THREE ROAD SECTIONS, LIFTING POINTS, JOINTS", f"1:{s}")
    x_lo = bx0 if m else -endw
    x_hi = bx1 if m < lay.modules - 1 else lay.L + endw
    v.rect(x_lo, -wall, x_hi, lay.W + wall, fc="#E3E8EF", ec=INK, lw=1.0, z=1)
    for k in range(3):
        y0 = -wall + k * L.HALL_SECTION_W
        v.rect(x_lo, y0, x_hi, y0 + L.HALL_SECTION_W, fc=PAPER if k % 2 == 0 else "#F4F7FB", ec=INK, lw=0.7, z=2)
        v.text((x_lo + x_hi) / 2, y0 + L.HALL_SECTION_W / 2, f"SECTION {m+1}.{k+1}  12.2 x 3.66 x 4.2 m  tare ~{lay.d['geometry']['tare_kg'] / 12:,.0f} kg", h=2.2, ha="center", va="center", c=MUTED)
        for X in (x_lo + 1500, (x_lo + x_hi) / 2, x_hi - 1500):
            for Y in (y0 + 400, y0 + L.HALL_SECTION_W - 400):
                v.circle(X, Y, 120, fc=PAPER, ec=CTP_C, lw=0.8, z=4)
    v.leader(x_lo + 1500, -wall + 400, -10, -8, "Lifting points 6 per section, spreader frame only (CTP-S4 HOLD)", h=1.8, c=CTP_C)
    for k in (1, 2):
        v.line(x_lo, -wall + k * L.HALL_SECTION_W, x_hi, -wall + k * L.HALL_SECTION_W, c=RED, lw=0.9, ls="--", z=3)
    v.leader((x_lo + x_hi) / 2 + 2000, -wall + L.HALL_SECTION_W, 12, 10, "Longitudinal section seam: splice plates M20 @ 600, two-stage gasket, roof cover flashing (CTP-J1)", h=1.8, c=RED)
    if m:
        v.line(bx0, -wall - 300, bx0, lay.W + wall + 300, c=RED, lw=1.0, ls="--", z=3)
        v.text(bx0, lay.W + wall + 500, f"JOINT TO BAY {m}", h=1.7, ha="center", c=RED)
    if m < lay.modules - 1:
        v.line(bx1, -wall - 300, bx1, lay.W + wall + 300, c=RED, lw=1.0, ls="--", z=3)
        v.text(bx1, lay.W + wall + 500, f"JOINT TO BAY {m+2}", h=1.7, ha="center", c=RED)
    for it in lay.items:
        if it.tag.startswith("FW") and x_lo <= it.cx <= x_hi:
            v.rect(it.x0, lay.W + wall - 100, it.x1, lay.W + wall + 250, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6, z=4)
            v.text(it.cx, lay.W + wall + 700, it.tag + " LOUVRE", h=1.6, ha="center", c=EDGE["cooling"])
    v.dim_h(x_lo, x_hi, -wall, -10, label=f"{x_hi - x_lo:.0f}")
    v.dim_v(-wall, lay.W + wall, x_lo, -10, label=f"{lay.ext_w:.0f}")
    v.dim_v(-wall, -wall + L.HALL_SECTION_W, x_hi, 8, label=f"{L.HALL_SECTION_W} SECTION", side="right")
    # elevation of the bay (long wall)
    y_el = oy - 26
    oyE = y_el - lay.ext_h / s
    ve = View(sh, s, ox, oyE)
    sh.view_title(ox, y_el + 2, f"BAY {m+1} ELEVATION — LONG WALL, PANEL RIBS AND PLINTH", f"1:{s}")
    ve.rect(0, 0, x_hi - x_lo, lay.ext_h, lw=1.0)
    ve.corrugation(0, x_hi - x_lo, 0, lay.ext_h, pitch=1000, vertical=True)
    ve.rect(0, lay.ext_h - 300, x_hi - x_lo, lay.ext_h, fc="#E8EDF3", ec=INK, lw=0.5)
    ve.text((x_hi - x_lo) / 2, lay.ext_h - 150, "ROOF: 100 mm PIR SANDWICH, 1:50 FALL TO THE FAN-WALL SIDE, DRIP EDGE", h=1.6, ha="center", va="center", c=MUTED)
    if lay.cfg.hardening in ("H2", "H3"):
        ve.rect(-200, -600, x_hi - x_lo + 200, 0, fc="#D9E1EA", ec=INK, lw=0.6)
        ve.text((x_hi - x_lo) / 2, -300, "FLOOD PLINTH 600 — GALVANISED FRAME (H2/H3, STR-FLOOD-PLINTH)", h=1.6, ha="center", va="center")
    else:
        ve.rect(-200, -250, x_hi - x_lo + 200, 0, fc="#D9E1EA", ec=INK, lw=0.6)
        ve.text((x_hi - x_lo) / 2, -125, "GRADE BEAMS UNDER SECTION RAILS (S-001)", h=1.5, ha="center", va="center")
    ve.dim_v(0, lay.ext_h, 0, -8, label=f"{lay.ext_h:.0f}")
    ve.dim_h(0, x_hi - x_lo, 0, -16, label=f"{x_hi - x_lo:.0f}")

    def extra(sh, x, y):
        notes = [f"Bay {m+1} of {lay.modules}: " + ("vestibule, BEN Controller, fire releasing and staging zone" if m == 0 else "IT rows (see A-002 and A-002-M%d), fan-wall units FW on the long wall" % (m + 1)) + ".",
                 "Road sections are factory-finished (panels, liner, lighting, cable tray brackets, leak rope clips, IP66 penetration frames) and factory hose-tested; the site joins them (CTP-J1) and re-tests every joint and penetration (CTQ-A4).",
                 "Section transport: 3.66 m wide x 4.2 m high x 12.2 m long on a drop-deck/lowboy trailer, travel height 4.8 m (check I-H13), escorts and route survey; lift with a spreader frame on the six lifting points only.",
                 "Set sequence: south section first on the grade beams, middle, north; align within 10 mm; compress the gasket with the splice bolts in three passes; fit the roof cover flashing; bond across every joint (<= 0.1 ohm).",
                 f"Hardening {lay.d['hardening_label']}: see A-003 details (flood plinth, C5-M, ballistic panels, shielded penetrations as applicable)."]
        return sh.notes(x, y, f"BAY {m+1} NOTES", notes, h=2.0, lead=3.1)
    ctx.right_column(sh, lay, "A-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, no))


def _plan_items(v, lay, s, x_lo=None, x_hi=None, labels=True):
    order = {"tray": 0, "structure": 1, "rack": 3, "cooling": 3, "power": 3, "controls": 4, "fire": 4}
    for it in sorted(lay.items, key=lambda i: order.get(i.kind, 2)):
        if it.mount in ("ext", "roof", "rack") or it.tag in ("LEAK",) or it.tag.startswith("HAC"):
            continue
        if x_lo is not None and (it.x1 <= x_lo or it.x0 >= x_hi):
            continue
        X0, X1 = (max(it.x0, x_lo), min(it.x1, x_hi)) if x_lo is not None else (it.x0, it.x1)
        if it.tag == "STG":
            v.rect(X0, it.y0, X1, it.y1, fc="none", ec=MUTED, lw=0.5, ls=":", z=1)
            v.text((X0 + X1) / 2, it.cy, "STAGING / UNLOADING ZONE", h=2.0, ha="center", va="center", c=MUTED)
            continue
        if it.kind == "tray" or it.mount == "ceiling":
            v.rect(X0, it.y0, X1, it.y1, fc="none", ec=EDGE.get(it.kind, MUTED), lw=0.5, ls="--", z=2)
            if labels and (X1 - X0) / s > 20:
                v.text(X1 - 100, it.cy, it.tag, h=1.5, ha="right", va="center", c=EDGE.get(it.kind, MUTED))
            continue
        if it.mount == "wall":
            v.rect(X0, it.y0, X1, it.y1, fc=FILL.get(it.kind), ec=EDGE.get(it.kind, INK), lw=0.6, ls="--", z=4)
            if labels:
                v.text((X0 + X1) / 2, it.cy, it.tag, h=1.6, ha="center", va="center", bold=True, rot=90 if (it.y1 - it.y0) / s > (X1 - X0) / s else 0)
            continue
        kw = dict(fc=FILL.get(it.kind, "none"), ec=EDGE.get(it.kind, INK), lw=0.6)
        v.rect(X0, it.y0, X1, it.y1, **kw)
        if it.kind in ("rack", "cooling") and it.mount == "floor":
            if it.front == "-y":
                v.line(X0 + 40, it.y0 + 60, X1 - 40, it.y0 + 60, c=EDGE[it.kind], lw=1.0)
            elif it.front == "+y":
                v.line(X0 + 40, it.y1 - 60, X1 - 40, it.y1 - 60, c=EDGE[it.kind], lw=1.0)
        if labels:
            wmm = (X1 - X0) / s
            h = 1.9 if wmm > 8 else (1.3 if wmm > 4 else 1.0)
            if it.kind == "rack" and wmm < 4:
                continue
            v.text((X0 + X1) / 2, it.cy, it.tag, h=h, ha="center", va="center", bold=True, rot=90 if wmm < 9 and (it.y1 - it.y0) / s > wmm else 0)


def _aisle_labels(v, lay, x0, x1, h=1.8):
    for kind, y0, y1 in lay.notes["aisles"]:
        lab = "COLD AISLE" if kind == "cold" else "HOT AISLE (CONTAINED)"
        col = CTQ_C if kind == "cold" else RED
        v.text((x0 + x1) / 2, (y0 + y1) / 2, f"{lab} {y1 - y0:.0f}", h=h, ha="center", va="center", c=col, bg=PAPER)


def sheet_a002(lay, out, ctx: Ctx, n):
    endw, wall = _ext(lay)
    s = 100
    sh = ctx.new_sheet(lay, "A-002", "Interior layout plan", f"1:{s} / 1:60", n)
    ox, y_top = 40.0, TOP - 14
    oy = y_top - (lay.W + 2 * wall) / s - 30
    v = View(sh, s, ox + endw / s, oy + wall / s)
    sh.view_title(ox, y_top + 6, "INTERIOR LAYOUT PLAN — WHOLE HALL", f"1:{s}")
    _hall_outline(v, lay)
    v.rect(-endw, lay.W / 2 - 1500, 0, lay.W / 2 + 1500, fc=PAPER, ec=PAPER, lw=0, z=2)
    _plan_items(v, lay, s, labels=False)
    for it in lay.items:
        if it.kind == "cooling" and it.tag.startswith(("CDU", "FW")):
            v.text(it.cx, it.cy, it.tag, h=1.3, ha="center", va="center", bold=True, rot=90)
    for r, y0, y1, front in lay.notes["rows_y"]:
        v.text(lay.notes["row_x0"] - 900, (y0 + y1) / 2, f"ROW {r}", h=1.8, ha="right", va="center", bold=True, c=EDGE["rack"])
    _aisle_labels(v, lay, lay.notes["row_x1"] + 500, lay.L - 600, h=1.5)
    for m in range(lay.modules):
        xm = m * lay.ext_l / lay.modules - endw + lay.ext_l / lay.modules / 2
        v.text(xm, lay.W + wall + 500, f"BAY {m+1}", h=2.2, ha="center", c=MUTED, bold=True)
    # egress arrows: hot-aisle doors -> cold aisles -> vestibule and blind-end door
    ya = lay.notes["aisles"][0][2] / 2
    x0e, y0e = v.p(lay.notes["row_x0"], ya); x1e, y1e = v.p(300, ya)
    sh.arrow(x0e, y0e, x1e, y1e, c=GREEN, lw=1.0, ms=8)
    v.text(lay.notes["row_x0"] / 2, ya + 300, "EGRESS to vestibule", h=1.6, ha="center", c=GREEN, bg=PAPER)
    x0e, y0e = v.p(lay.notes["row_x1"], ya); x1e, y1e = v.p(lay.L - 300, ya)
    sh.arrow(x0e, y0e, x1e, y1e, c=GREEN, lw=1.0, ms=8)
    v.text((lay.notes["row_x1"] + lay.L) / 2, ya + 300, "EGRESS to door M3", h=1.6, ha="center", c=GREEN, bg=PAPER)
    v.rect(lay.L - 1200, lay.W / 2 - 600, lay.L, lay.W / 2 + 600, fc=PAPER, ec=INK, lw=0.6, z=3); v.text(lay.L - 600, lay.W / 2, "DOOR M3", h=1.3, ha="center", va="center", rot=90)
    v.dim_h(0, lay.notes["row_x0"], 0, -10, label=f"{lay.notes['row_x0']:.0f}")
    v.dim_h(lay.notes["row_x0"], lay.notes["row_x1"], 0, -10, label=f"{lay.notes['row_len']:.0f} ROW")
    v.dim_h(lay.notes["row_x1"], lay.L, 0, -10, label=f"{lay.L - lay.notes['row_x1']:.0f}")
    v.dim_h(0, lay.L, 0, -20, label=f"{lay.L:.0f} INTERIOR")
    v.dim_v(0, lay.W, 0, -12, label=f"{lay.W:.0f} INT")
    v.bubble(lay.notes["row_x0"] + 300, lay.notes["rows_y"][0][1], -14, -12, "CTQ-B1")
    sh.north_arrow(RX - 45, TOP - 30)
    # zoomed IT-zone plan 1:60
    s2 = 60
    x_lo, x_hi = lay.notes["row_x0"] - 1500, lay.notes["row_x1"] + 1500
    y_z = oy - 30
    oyZ = y_z - lay.W / s2 - 8
    vz = View(sh, s2, ox - x_lo / s2, oyZ)
    sh.view_title(ox, y_z + 2, "IT ZONE PLAN — FOUR ROWS, CDU ROW ENDS, FAN WALL (zoomed)", f"1:{s2}")
    vz.rect(x_lo, 0, x_hi, lay.W, fc=PAPER, ec=INK, lw=0.8, z=1)
    vz.line(x_lo, lay.W, x_hi, lay.W, c=INK, lw=2.0, z=1); vz.text(x_lo + 200, lay.W + 150, "LONG WALL y = W (FAN-WALL SIDE)", h=1.5, c=MUTED)
    vz.line(x_lo, 0, x_hi, 0, c=INK, lw=2.0, z=1); vz.text(x_lo + 200, -400, "LONG WALL y = 0", h=1.5, c=MUTED)
    for jx in lay.module_x:
        if x_lo < jx < x_hi:
            vz.line(jx, 0, jx, lay.W, c=RED, lw=0.8, ls="--", z=3); vz.text(jx, lay.W + 150, "BAY JOINT", h=1.4, ha="center", c=RED)
    _plan_items(vz, lay, s2, x_lo, x_hi, labels=True)
    for kind, y0, y1 in lay.notes["aisles"]:
        if kind == "hot":
            vz.hatch_rect(lay.notes["row_x0"], y0, lay.notes["row_x1"], y1, hatch="xxx", ec=EDGE["cooling"], z=1)
    _aisle_labels(vz, lay, x_lo + 300, lay.notes["row_x0"] - 300, h=1.4)
    for r, y0, y1, front in lay.notes["rows_y"]:
        vz.text(lay.notes["row_x1"] + 300, (y0 + y1) / 2, f"ROW {r} ({'faces -y' if front == '-y' else 'faces +y'})", h=1.4, va="center", c=EDGE["rack"])
    # NEC working space in cold aisles
    cold = [a for a in lay.notes["aisles"] if a[0] == "cold"]
    for kind, y0, y1 in cold:
        vz.rect(lay.notes["row_x0"], y0, lay.notes["row_x1"], y1, fc="none", ec=CTQ_C, lw=0.5, ls=":", z=2)
    vz.text(lay.notes["row_x0"] + 200, cold[1][1] + 150, "NEC 110.26 cond. 2 >= 1067 (equipment both sides)", h=1.3, c=CTQ_C, bg=PAPER)
    # dims across the width
    y_prev = 0
    for kind, y0, y1 in lay.notes["aisles"]:
        vz.dim_v(y0, y1, x_lo, -8, label=f"{y1 - y0:.0f}", h=1.6)
    for r, y0, y1, front in lay.notes["rows_y"]:
        vz.dim_v(y0, y1, x_lo, -8, label=f"{y1 - y0:.0f}", h=1.6)
    fw = [i for i in lay.items if i.tag.startswith("FW")]
    if fw:
        vz.dim_v(fw[0].y0, fw[0].y1, x_lo, -8, label=f"{fw[0].d:.0f} FW", h=1.6)
    vz.dim_v(0, lay.W, x_lo, -18, label=f"{lay.W:.0f} INT", h=1.8)
    vz.dim_h(lay.notes["row_x0"], lay.notes["row_x0"] + 600, 0, -8, label="600 CDU", h=1.5)
    vz.dim_h(lay.notes["row_x0"] + 600, lay.notes["row_x1"] - 600, 0, -8, label=f"{lay.d['racks_per_row']} x 600", h=1.5)
    vz.bubble(lay.notes["row_x0"] + 3000, cold[0][2], 0, -14, "CTQ-B2")
    vz.bubble(lay.notes["row_x1"] - 1500, lay.notes["rows_y"][1][2], 14, 10, "CTQ-B5")
    vz.bubble(lay.notes["row_x0"] + 1800, lay.notes["rows_y"][0][2], -14, 6, "CTQ-B3")
    # row elevation (row 1 from the cold aisle)
    y_el_top = oyZ - 22
    oyE = y_el_top - lay.H / s2 - 6
    ve = View(sh, s2, ox - x_lo / s2, oyE)
    sh.view_title(ox, y_el_top + 2, "ROW 1 ELEVATION — FROM COLD AISLE 1, OVERHEAD MANIFOLD AND BUSWAY", f"1:{s2}")
    ve.rect(x_lo, 0, x_hi, lay.H, lw=0.8)
    for it in lay.items:
        if it.note == "row1" or (it.tag in ("CDU1", "CDU2")):
            ve.rect(it.x0, it.z0, it.x1, it.z1, fc=FILL[it.kind], ec=EDGE[it.kind], lw=0.5)
            ve.text(it.cx, it.z1 / 2, it.tag, h=1.2, ha="center", va="center", rot=90)
    for tag, lab in (("MAN-1", "DLC MANIFOLDS S/R"), ("BUS-1A", "BUSWAY A / B 800 A")):
        it = lay.find(tag)
        if it:
            ve.rect(it.x0, it.z0, it.x1, it.z1, fc=FILL[it.kind], ec=EDGE[it.kind], lw=0.5, ls="--")
            ve.text(it.x1 + 200, (it.z0 + it.z1) / 2, lab, h=1.4, va="center", c=EDGE[it.kind])
    ve.dim_v(0, lay.H, x_lo, -8, label=f"{lay.H:.0f} INT")
    ve.dim_v(0, L.HALL_RACK_H, x_hi, 6, label=f"{L.HALL_RACK_H} RACK", side="right")
    ve.dim_v(0, L.HALL_MANIFOLD_Z, x_hi, 14, label=f"{L.HALL_MANIFOLD_Z} U/S MANIFOLD", side="right")
    ve.dim_v(0, L.HALL_BUSWAY_Z, x_hi, 22, label=f"{L.HALL_BUSWAY_Z} U/S BUSWAY", side="right")

    def extra(sh, x, y):
        rows = []
        seen = set()
        for it in lay.items:
            if it.mount in ("ext", "rack") or it.kind == "controls" and it.code == "CTL-POD":
                continue
            key = (it.code, it.label[:30])
            if it.kind == "rack":
                if "rack" in seen:
                    continue
                seen.add("rack")
                rows.append(["R1..R%d" % lay.cfg.racks, it.code, f"{lay.cfg.racks} racks, 4 rows x {lay.d['racks_per_row']}, 48U 600x1070", f"{lay.notes['row_x0'] + 600:.0f}", "rows", "600x1070", "0", "floor"])
                continue
            rows.append([it.tag, it.code, it.label[:46], f"{it.x0:.0f}", f"{it.y0:.0f}", f"{it.w:.0f}x{it.d:.0f}", f"{it.z0:.0f}", it.mount])
        y = sh.table(x, y, ["TAG", "CODE", "DESCRIPTION", "x0", "y0", "W x D", "z0", "MOUNT"], rows[:34],
                     [20, 22, RW - 20 - 22 - 16 - 16 - 28 - 14 - 18, 16, 16, 28, 14, 18], h=1.5, rowh=3.0,
                     title="EQUIPMENT SCHEDULE (interior mm; x from vestibule end wall, y from long wall y = 0, z from slab)")
        y -= 5
        y = sh.legend(x, y, [("rack", "IT rack (DLC)"), ("cooling", "CDU / fan wall / manifold"), ("power", "Busway, EPO"), ("controls", "Controls"), ("fire", "Fire suppression")], h=1.9)
        return y
    ctx.right_column(sh, lay, "A-002", extra)
    sh.title_block()
    sh.save(os.path.join(out, "A-002"))


def sheet_a002_module(lay, out, ctx: Ctx, m, n):
    endw, wall = _ext(lay)
    bx0, bx1 = _bay_bounds(lay, m)
    x_lo = bx0 if m else 0
    x_hi = bx1 if m < lay.modules - 1 else lay.L
    s = 50
    no = f"A-002-M{m+1}"
    sh = ctx.new_sheet(lay, no, f"Module {m+1} interior layout", f"1:{s}", n)
    ox, y_top = 40.0, TOP - 14
    oy = y_top - lay.W / s - 30
    v = View(sh, s, ox - x_lo / s, oy)
    sh.view_title(ox, y_top + 6, f"BAY {m+1} INTERIOR PLAN (x {x_lo:.0f} to {x_hi:.0f})", f"1:{s}")
    v.rect(x_lo, 0, x_hi, lay.W, fc=PAPER, ec=INK, lw=1.0, z=1)
    if m == 0:
        v.rect(-endw, lay.W / 2 - 1500, 0, lay.W / 2 + 1500, fc=PAPER, ec=INK, lw=0.6, z=2)
        v.text(-endw + 200, lay.W / 2 + 1700, "VESTIBULE DOORS (outward, IP66)", h=1.5, c=MUTED)
    for jx in lay.module_x:
        if x_lo <= jx <= x_hi:
            v.line(jx, 0, jx, lay.W, c=RED, lw=1.0, ls="--", z=3); v.text(jx, lay.W + 200, "BAY JOINT (CTP-J1)", h=1.5, ha="center", c=RED)
    for k in (1, 2):
        v.line(x_lo, -wall + k * L.HALL_SECTION_W, x_hi, -wall + k * L.HALL_SECTION_W, c=MUTED, lw=0.5, ls=":", z=2)
    _plan_items(v, lay, s, x_lo, x_hi, labels=True)
    for kind, y0, y1 in lay.notes["aisles"]:
        if kind == "hot" and x_hi > lay.notes["row_x0"] and x_lo < lay.notes["row_x1"]:
            v.hatch_rect(max(x_lo, lay.notes["row_x0"]), y0, min(x_hi, lay.notes["row_x1"]), y1, hatch="xxx", ec=EDGE["cooling"], z=1)
    if m == 0:
        _aisle_labels(v, lay, x_lo + 4500, x_hi, h=1.5)
    else:
        _aisle_labels(v, lay, x_lo, x_lo + min(1500, max(300, lay.notes["row_x0"] - x_lo)), h=1.3)
    # leak rope route
    v.poly([(x_lo + 100, 100), (x_hi - 100, 100), (x_hi - 100, lay.W - 100), (x_lo + 100, lay.W - 100)], fc="none", ec=RED, lw=0.5, ls=":", closed=(m == 1), z=3)
    v.dim_h(x_lo, x_hi, 0, -10, label=f"{x_hi - x_lo:.0f}")
    v.dim_v(0, lay.W, x_lo, -10, label=f"{lay.W:.0f} INT")
    for kind, y0, y1 in lay.notes["aisles"]:
        v.dim_v(y0, y1, x_hi, 6, label=f"{y1 - y0:.0f}", side="right", h=1.5)
    for r, y0, y1, front in lay.notes["rows_y"]:
        v.dim_v(y0, y1, x_hi, 6, label=f"R{r} {y1 - y0:.0f}", side="right", h=1.5)
    sh.north_arrow(RX - 45, TOP - 30)
    # ceiling plan strip: manifolds, busways, tray, lights
    y_c = oy - 26
    oyC = y_c - lay.W / s - 8
    vc = View(sh, s, ox - x_lo / s, oyC)
    sh.view_title(ox, y_c + 2, f"BAY {m+1} REFLECTED CEILING — MANIFOLDS, BUSWAYS, TRAY, LIGHTS, NOZZLES", f"1:{s}")
    vc.rect(x_lo, 0, x_hi, lay.W, fc=PAPER, ec=INK, lw=0.8, z=1)
    for it in lay.items:
        if it.mount == "ceiling" and it.x1 > x_lo and it.x0 < x_hi:
            X0, X1 = max(it.x0, x_lo), min(it.x1, x_hi)
            vc.rect(X0, it.y0, X1, it.y1, fc=FILL.get(it.kind, "none"), ec=EDGE.get(it.kind, INK), lw=0.6)
            vc.text(X0 + 300, it.cy, f"{it.tag} z {it.z0:.0f}", h=1.3, va="center")
    nx = max(1, int((x_hi - x_lo) / 3000))
    for i in range(nx):
        for yy in (lay.W * 0.25, lay.W * 0.75):
            X = x_lo + (i + 0.5) * (x_hi - x_lo) / nx
            vc.rect(X - 600, yy - 60, X + 600, yy + 60, fc="#FFFBE6", ec=MUTED, lw=0.4)
            vc.circle(X, yy + 700, 90, fc=PAPER, ec=RED, lw=0.5)
    vc.text(x_lo + 300, lay.W - 400, "LED luminaires 4000 K over the cold aisles (500 lx); clean-agent nozzles (red) per zone; VESDA pipe along the ceiling", h=1.5, c=MUTED)
    vc.dim_h(x_lo, x_hi, 0, -8, label=f"{x_hi - x_lo:.0f}")

    def extra(sh, x, y):
        rows = []
        for it in lay.items:
            if it.mount in ("ext", "rack") or it.kind == "tray" or it.x1 <= x_lo or it.x0 >= x_hi or it.tag.startswith("P") and it.code == "CTL-POD":
                continue
            if it.kind == "rack":
                continue
            rows.append([it.tag, it.code, it.label[:44], f"{max(it.x0, x_lo):.0f}", f"{it.y0:.0f}", f"{it.z0:.0f}", it.mount])
        racks = [i for i in lay.by_kind("rack") if x_lo <= i.cx <= x_hi]
        if racks:
            rows.insert(0, [f"{racks[0].tag}..{racks[-1].tag}", "STR-RACK48", f"{len(racks)} racks in this bay", f"{racks[0].x0:.0f}", "rows", "0", "floor"])
        y = sh.table(x, y, ["TAG", "CODE", "DESCRIPTION", "x0", "y0", "z0", "MOUNT"], rows[:30], [22, 24, RW - 22 - 24 - 16 - 16 - 14 - 18, 16, 16, 14, 18], h=1.5, rowh=3.0,
                     title=f"BAY {m+1} EQUIPMENT (interior mm)")
        y -= 5
        notes = ["Items that cross a bay joint are set after the joint is sealed and bonded (CTP-J1); racks never straddle a joint (rows snapped to the joint grid).",
                 "Leak rope around the bay perimeter, under every CDU and in every manifold drip tray; ends at the module PLC panel.",
                 "Hot aisles contained with roof panels and end doors (CTQ-B5); cold aisles are the egress and working space (CTQ-B2)."]
        return sh.notes(x, y, "BAY NOTES", notes, h=2.0, lead=3.1)
    ctx.right_column(sh, lay, "A-002", extra)
    sh.title_block()
    sh.save(os.path.join(out, no))


# ====================================================================== A-003 envelope section (hall)
def sheet_a003(lay, out, ctx: Ctx, n):
    endw, wall = _ext(lay)
    s = 25
    sh = ctx.new_sheet(lay, "A-003", "Envelope section and hardening", f"1:{s} / details", n)
    ox, y_top = 40.0, TOP - 14
    ew, eh, W, H = lay.ext_w, lay.ext_h, lay.W, lay.H
    oy = y_top - eh / s - 24
    v = View(sh, s, ox, oy)
    sh.view_title(ox, y_top + 6, "CROSS SECTION THROUGH THE ROWS (looking toward the blind end)", f"1:{s}")
    slab = 200
    v.rect(-600, -slab, ew + 600, 0, fc="#D9E1EA", ec=INK, lw=0.6, hatch="//")
    v.text(ew / 2, -slab / 2, "SLAB ON GRADE 200 + GRADE BEAMS UNDER SECTION RAILS (S-001)", h=1.6, ha="center", va="center", bg=PAPER)
    plinth = 600 if lay.cfg.hardening in ("H2", "H3") else 0
    if plinth:
        v.rect(-200, 0, ew + 200, plinth, fc="#C9D3E0", ec=INK, lw=0.6)
        v.text(ew / 2, plinth / 2, "FLOOD PLINTH 600 — GALVANISED FRAME, GRATING STEP (H2/H3)", h=1.6, ha="center", va="center")
    z0 = plinth
    v.rect(0, z0, ew, z0 + eh, lw=1.0)
    for k in (1, 2):
        v.line(k * L.HALL_SECTION_W, z0, k * L.HALL_SECTION_W, z0 + eh, c=RED, lw=0.9, ls="--")
        v.text(k * L.HALL_SECTION_W, z0 + eh + 150, "SECTION SEAM (CTP-J1)", h=1.4, ha="center", c=RED)
    # walls 300 (100 PIR sandwich + frame), roof 300, floor 300
    for X0, X1 in ((0, wall), (ew - wall, ew)):
        v.rect(X0, z0, X1, z0 + eh, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
    v.rect(wall, z0 + eh - (eh - H - 300), ew - wall, z0 + eh, fc="#FFF4D6", ec=MUTED, lw=0.3, hatch="...")
    v.rect(wall, z0, ew - wall, z0 + 300, fc="#E9D8B0", ec=MUTED, lw=0.4)
    v.text(ew / 2, z0 + 150, "SECTION FLOOR: STEEL FRAME + 18 mm CEMENT BOARD + ANTI-STATIC VINYL (no raised floor)", h=1.5, ha="center", va="center", c=MUTED)
    zf = z0 + 300   # finished floor
    # rows and aisles
    for kind, y0, y1 in lay.notes["aisles"]:
        col = CTQ_C if kind == "cold" else RED
        v.text(wall + (y0 + y1) / 2, zf + 1000, "COLD" if kind == "cold" else "HOT", h=1.6, ha="center", va="center", rot=90, c=col)
        if kind == "hot":
            v.hatch_rect(wall + y0, zf, wall + y1, zf + L.HALL_RACK_H + 200, hatch="xxx", ec=EDGE["cooling"])
            v.rect(wall + y0, zf + L.HALL_RACK_H, wall + y1, zf + L.HALL_RACK_H + 200, fc="none", ec=EDGE["cooling"], lw=0.6, ls="--")
    for r, y0, y1, front in lay.notes["rows_y"]:
        v.rect(wall + y0, zf, wall + y1, zf + L.HALL_RACK_H, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6)
        v.text(wall + (y0 + y1) / 2, zf + L.HALL_RACK_H / 2, f"ROW {r}", h=1.8, ha="center", va="center", rot=90, bold=True)
        v.rect(wall + y0 + 350, zf + L.HALL_MANIFOLD_Z, wall + y1 - 350, zf + L.HALL_MANIFOLD_Z + 200, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.5)
        for yy in (y0 + 50, y1 - 250):
            v.rect(wall + yy, zf + L.HALL_BUSWAY_Z, wall + yy + 200, zf + L.HALL_BUSWAY_Z + 150, fc=FILL["power"], ec=EDGE["power"], lw=0.5)
    fw = [i for i in lay.items if i.tag.startswith("FW")]
    if fw:
        f = fw[0]
        v.rect(wall + f.y0, zf, wall + f.y1, zf + f.z1, fc=FILL["cooling"], ec=EDGE["cooling"], lw=0.6)
        v.text(wall + f.cy, zf + f.z1 / 2, "FAN WALL", h=1.6, ha="center", va="center", rot=90)
        v.rect(ew - wall - 100, zf + 600, ew + 250, zf + 3000, fc="none", ec=EDGE["cooling"], lw=0.6, ls="--")
        v.text(ew + 400, zf + 1800, "INTAKE LOUVRE + ePM1 (H2) + HOOD", h=1.4, va="center", rot=90, c=EDGE["cooling"])
    v.rect(wall + W / 2 - 600, zf + H - 60, wall + W / 2 + 600, zf + H, fc="#FFFBE6", ec=MUTED, lw=0.5)
    v.text(wall + W / 2, zf + H - 200, "LED 4000 K", h=1.3, ha="center", c=MUTED)
    # hardening overlays on the wall
    if lay.cfg.hardening == "H3":
        v.rect(wall, zf, wall + 12, zf + H, fc="#8B5A2B", ec="#8B5A2B")
        v.rect(ew - wall - 12, zf, ew - wall, zf + H, fc="#8B5A2B", ec="#8B5A2B")
        v.leader(wall + 6, zf + H - 400, -16, 8, "Ballistic panel UL 752 (H3), battened to the liner (CTQ-H2)", h=1.7, c=CTP_C)
        v.rect(wall + 12, zf, wall + 14, zf + H, fc=INK, ec=INK)
        v.leader(wall + 13, zf + 600, -16, -8, "HEMP shield liner 2 mm steel, welded (H3 option, CTQ-H3)", h=1.7)
    v.dim_v(-slab, 0, ew, 8, label="200 SLAB", side="right")
    if plinth:
        v.dim_v(0, plinth, ew, 8, label="600 PLINTH", side="right")
    v.dim_v(z0, zf, ew, 8, label="300 FLOOR", side="right")
    v.dim_v(zf, zf + H, ew, 8, label=f"{H:.0f} INT", side="right")
    v.dim_v(zf + H, z0 + eh, ew, 8, label=f"{eh - H - 300:.0f} ROOF", side="right")
    v.dim_v(z0, z0 + eh, ew, 24, label=f"{eh:.0f}", side="right")
    v.dim_h(0, ew, -slab, -8, label=f"{ew:.0f}")
    v.dim_h(0, L.HALL_SECTION_W, z0 + eh, 6, label=f"{L.HALL_SECTION_W} SECTION")
    v.bubble(wall / 2, zf + 1500, -12, 6, "CTQ-C1"); v.bubble(ew - wall / 2, zf + 2500, 14, 8, "CTQ-C3"); v.bubble(L.HALL_SECTION_W, z0 + eh - 300, 16, 10, "CTQ-A4")
    # details row
    dy = oy - 30
    ctx.details["panel_joint"](sh, ox, dy)
    ctx.details["ip66"](sh, ox + 125, dy)
    ctx.details["hardening"](sh, ox + 262, dy, lay)

    def extra(sh, x, y):
        clim = lay.d["climate"]
        R = 0.100 / 0.022; U = 1 / (R + 0.17)
        rows = [["Wall / roof", "100 mm PIR sandwich panel (steel skins), lambda 0.022, R %.1f m2K/W, U %.2f; factory-sealed joints, site seams two-stage gasket" % (R, U)],
                ["Floor", "Steel section frame on grade beams, 18 mm cement board, 2 mm anti-static vinyl; no raised floor (overhead busway + manifolds)"],
                ["Envelope rating", f"{lay.d['hardening_rating']}; every penetration a gasketed frame (ENV-SEAL-KIT), hose test UL 50E 4X (CTQ-A4); +10 Pa make-up fan"],
                ["Corrosion", f"{lay.d['hardening_coating']} (site {clim['corrosion']}); stainless fasteners and anodes at H2/H3"],
                ["Design conditions", f"Outdoor {clim['t_design_c']} / {clim['t_min_c']} C ({clim['label']}); indoor 22 C 50 % RH (dew point 11.1 C); envelope gain {lay.d['envelope_gain_kw']} kW"],
                ["Hardening", f"{lay.d['hardening_label']}: " + "; ".join(lay.hardening["features"][:4])]]
        y = sh.table(x, y, ["THERMAL ENVELOPE", "VALUE / NOTE"], rows, [RW * 0.26, RW * 0.74], title="ENVELOPE AND HARDENING SCHEDULE", h=1.8)
        y -= 6
        notes = ["H1 baseline (every tier): NEMA 4X / IP66 envelope, gasketed and hose-tested penetrations, compression-gasket doors with three-point latches, drip edges, positive pressure.",
                 "H2 severe environment adds: 600 mm flood plinth (STR-FLOOD-PLINTH), C5-M coating (ENV-C5M-COATING), ePM1 intake filters and hoods, hurricane door hardware, snow guards, stainless fasteners, anodes, intrusion detection.",
                 "H3 hardened/government adds: UL 752 ballistic panels on every wall (certification record CTQ-H2, HOLD), ASTM F3038 forced-entry doors, IK10 hatches, HEMP shield option MIL-STD-188-125-1 with filtered penetrations and an 80 dB shield integrity test (CTQ-H3, HOLD), mantrap vestibule, two-factor access.",
                 "Module joints: splice plates + two-stage EPDM/butyl gasket + cover flashing + bonding jumper; seal and continuity checked at every joint (CTP-J1 HOLD) before the hose test.",
                 "Fire: PIR class B-s2,d0 (EN 13501-1) or FM 4880 panels; one clean-agent zone per bay + power module with VESDA (CTP-F1); pre-action option per AHJ."]
        return sh.notes(x, y, "ENVELOPE NOTES", notes, h=1.9, lead=3.0)
    ctx.right_column(sh, lay, "A-003", extra)
    sh.title_block()
    sh.save(os.path.join(out, "A-003"))


# ====================================================================== S-001 foundation (hall)
def sheet_s001(lay, out, ctx: Ctx, n):
    endw, wall = _ext(lay)
    s = 100
    sh = ctx.new_sheet(lay, "S-001", "Foundation and anchoring", f"1:{s} / 1:10 / 1:5", n)
    ox, y_top = 40.0, TOP - 14
    oy = y_top - (lay.W + 2 * wall + 2000) / s - 30
    v = View(sh, s, ox + (endw + 1000) / s, oy + (wall + 1000) / s)
    sh.view_title(ox, y_top + 6, "FOUNDATION PLAN — SLAB ON GRADE, GRADE BEAMS UNDER SECTION RAILS, ANCHORS", f"1:{s}")
    v.rect(-endw - 1000, -wall - 1000, lay.L + endw + 1000, lay.W + wall + 1000, fc="#F1F4F7", ec=INK, lw=0.8, hatch="//", z=0)
    v.text(lay.L / 2, lay.W + wall + 500, "SLAB 200 mm, 35 MPa, DOUBLE MAT #4 @ 300, 1 m APRON ALL ROUND (SITE-SLAB)", h=1.6, ha="center", c=MUTED, bg=PAPER)
    v.rect(-endw, -wall, lay.L + endw, lay.W + wall, fc="none", ec=INK, lw=1.0, z=2)
    # grade beams: under the 4 longitudinal section rail lines and the transverse joints / ends
    for k in range(4):
        yy = -wall + k * L.HALL_SECTION_W
        v.rect(-endw - 300, yy - 300, lay.L + endw + 300, yy + 300, fc="#C9D3E0", ec=INK, lw=0.6, z=3)
    for xx in [-endw] + lay.module_x + [lay.L + endw]:
        v.rect(xx - 300, -wall - 300, xx + 300, lay.W + wall + 300, fc="#C9D3E0", ec=INK, lw=0.6, z=3)
    v.text(lay.L * 0.25, -wall - 750, "GRADE BEAMS 600 x 600 UNDER EVERY SECTION RAIL AND EVERY BAY JOINT (6 longitudinal / 4 transverse)", h=1.6, c=INK, bg=PAPER)
    # anchors at rail brackets every 2 m
    for k in range(4):
        yy = -wall + k * L.HALL_SECTION_W
        X = -endw + 600
        while X < lay.L + endw:
            v.circle(X, yy, 60, fc=INK, ec=INK, z=4); X += 2000
    v.leader(-endw + 600, -wall, -8, -10, "M20 adhesive anchors at rail brackets @ 2,000 (CTP-S1)", h=1.7, c=CTP_C)
    # rack anchors
    for it in lay.items:
        if it.mount == "floor" and it.kind in ("rack", "cooling"):
            v.rect(it.x0, it.y0, it.x1, it.y1, fc="none", ec=EDGE[it.kind], lw=0.3, ls="--", z=3)
    r1 = lay.by_kind("rack")[0]
    v.leader(r1.x0, r1.y0, -10, 12, "Rack base: 4 x M12 adhesive anchors per rack to the slab (CTP-S2); CDU / fan wall per manufacturer seismic detail (CTP-S3)", h=1.7, c=CTP_C)
    v.dim_h(-endw, lay.L + endw, -wall - 1000, -10, label=f"{lay.ext_l:.0f}")
    v.dim_v(-wall, -wall + L.HALL_SECTION_W, -endw - 1000, -10, label=f"{L.HALL_SECTION_W}")
    v.dim_v(-wall, lay.W + wall, lay.L + endw + 1000, 8, label=f"{lay.ext_w:.0f}", side="right")
    v.bubble(lay.L * 0.6, -wall, 0, -16, "CTP-S1", "CTP"); v.bubble(r1.cx, r1.y1, 12, 14, "CTP-S2", "CTP"); v.bubble(lay.L * 0.4, lay.W / 2, 0, 14, "CTQ-S1")
    # details
    dy = oy - 34
    sh.view_title(ox, dy, "DETAIL A — SECTION RAIL ON GRADE BEAM", "1:10")
    vd = View(sh, 10, ox + 125, dy - 100)
    vd.rect(-400, -600, 400, 0, fc="#D9E1EA", ec=INK, lw=0.6, hatch="//"); vd.text(0, -300, "GRADE BEAM 600x600", h=1.6, ha="center", va="center", bg=PAPER)
    vd.rect(-1200, -200, -400, 0, fc="#F1F4F7", ec=INK, lw=0.5, hatch="//"); vd.rect(400, -200, 1200, 0, fc="#F1F4F7", ec=INK, lw=0.5, hatch="//")
    vd.rect(-300, 0, 300, 20, fc="#A8B4C4", ec=INK, lw=0.5)
    vd.rect(-250, 20, 250, 320, fc="#C9D3E0", ec=INK, lw=0.6); vd.text(0, 170, "SECTION RAIL 300x250 RHS", h=1.4, ha="center", va="center")
    vd.rect(-250, 320, 250, 600, fc="#E9D8B0", ec=MUTED, lw=0.4); vd.text(0, 460, "FLOOR", h=1.4, ha="center", va="center", c=MUTED)
    vd.rect(-12, -250, 12, 60, fc=INK, ec=INK); vd.rect(-40, 20, 40, 32, fc=INK, ec=INK)
    vd.rect(-320, 20, -250, 120, fc="#A8B4C4", ec=INK, lw=0.5)
    vd.leader(0, -200, 20, -8, "M20 adhesive anchor, 200 embed, 410 N·m (CTP-S1)", h=1.7, c=CTP_C)
    vd.leader(-300, 10, -14, 10, "10 mm neoprene + 20 mm shim/grout bed (level within 3 mm, CTQ-S1)", h=1.7)
    vd.leader(250, 500, 16, 6, "Floor build-up 300 (cement board + vinyl)", h=1.7)
    sx = ox + 270
    sh.view_title(sx, dy, "DETAIL B — RACK BASE TO SLAB", "1:5")
    vb = View(sh, 5, sx, dy - 100)
    vb.rect(0, -200, 700, 0, fc="#F1F4F7", ec=INK, lw=0.6, hatch="//"); vb.text(350, -100, "SLAB 200", h=1.5, ha="center", va="center", bg=PAPER)
    vb.rect(0, 0, 700, 2, fc=INK, ec=INK)
    vb.rect(50, 2, 650, 14, fc="#A8B4C4", ec=INK, lw=0.6)
    vb.rect(50, 14, 70, 350, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6); vb.rect(630, 14, 650, 350, fc=FILL["rack"], ec=EDGE["rack"], lw=0.6)
    vb.text(350, 200, "RACK FRAME", h=1.6, ha="center", va="center", c=EDGE["rack"])
    for X in (140, 560):
        vb.rect(X - 6, -120, X + 6, 30, fc=INK, ec=INK); vb.rect(X - 15, 14, X + 15, 26, fc=INK, ec=INK)
    vb.leader(560, -100, 18, -8, "M12 adhesive anchor 110 embed, 85 N·m, 4 per rack (CTP-S2)", h=1.7, c=CTP_C)
    vb.leader(350, 8, 18, 12, "Rack base plate on 2 mm anti-static vinyl; grout where > 3 mm", h=1.7)
    sx2 = ox
    dy_c = dy - 118
    sh.view_title(sx2, dy_c, "DETAIL C — SEISMIC: EQUIPMENT ANCHOR SCHEDULE", "NTS")
    rows = [["Rack 48U (1,000 kg)", "4 x M12 adhesive", "110", "85"], ["CDU 300 kW", "4 x M16 adhesive", "150", "210"], ["Fan wall", "6 x M16 adhesive", "150", "210"],
            ["UPS frame / battery cabinet", "4 x M16 per mfr", "150", "210"], ["Switchgear section", "per mfr seismic cert", "-", "-"], ["Section rail bracket", "M20 adhesive @ 2 m", "200", "410"]]
    sh.table(sx2, dy_c - 8, ["ITEM", "ANCHOR", "EMBED mm", "N·m"], rows, [52, 48, 22, 16], h=1.7, rowh=3.6)

    def extra(sh, x, y):
        d = lay.d
        rows = [["Dead load (gross, config)", f"{d['gross_kg']:,} kg = {d['gross_kg'] * 9.81 / 1000:,.0f} kN"],
                ["Rack footprint load", next((f"{c.value} kN/m2 vs {c.limit:g} — {c.result}" for c in lay.checks if c.id == "I-H18"), "n/a")],
                ["Section lift mass", next((f"{c.value:,.0f} kg vs {c.limit:,.0f} — {c.result}" for c in lay.checks if c.id == "I-H19"), "n/a")],
                ["Wind (ASCE 7 basic)", f"{d['climate']['wind_ms']} m/s (H2/H3 package {lay.hardening['wind_ms_min']} m/s) -> qz ~ {0.613 * d['climate']['wind_ms'] ** 2 / 1000:.2f} kPa; uplift resisted by rail anchors"],
                ["Seismic", "Site SDS from geotech; ASCE 7 Ch. 13 Ip = 1.5 for racks/CDUs; SDC D at H2/H3"],
                ["Snow (roof)", "3 kPa design at H2/H3 (snow guards); 1.5 kPa H1 temperate"],
                ["Soil", "Allowable bearing >= 100 kPa assumed (assumption); geotech report required before the slab design is released"],
                ["Bolt torque (class 8.8, dry)", "M12 85 / M16 210 / M20 410 N·m, +/-10 %, calibrated wrench"]]
        y = sh.table(x, y, ["LOAD / ITEM", "VALUE"], rows, [RW * 0.34, RW * 0.66], title="STRUCTURAL DATA", h=1.8)
        y -= 6
        notes = ["Slab and grade beams by the engineer of record (SVC-AE-HALL) from the geotech report; this sheet fixes the rail lines, anchor positions and loads.",
                 "Grade beams carry the section rails continuously; the slab between beams carries the racks (point loads spread by the base plates).",
                 "Section set tolerance: rails level within 3 mm over 12.2 m before joining; joint gap 10 +/-3 mm (CTP-A2 WITNESS); anchors torqued after joining (CTP-S1).",
                 "Flood plinth (H2/H3) sits between the grade beams and the section rails: 600 mm galvanised frame, anchors through the plinth feet.",
                 "Every torqued anchor gets a paint stripe after the witness check (Q-04); 5 % of adhesive anchors pull-tested to 25 kN."]
        return sh.notes(x, y, "STRUCTURAL NOTES", notes, h=1.9, lead=3.0)
    ctx.right_column(sh, lay, "S-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "S-001"))


# ====================================================================== E-001 MV one-line (hall)
def sheet_e001(lay, out, ctx: Ctx, n):
    sh = ctx.new_sheet(lay, "E-001", "Power one-line (MV service)", "NTS", n)
    d, cfg = lay.d, lay.cfg
    xf_a = d["transformer_kva"] * 1000 / (math.sqrt(3) * 480)
    n_frames = d["ups_modules"] * math.ceil(d["ups_kva_each"] / 500)
    sh.view_title(30, TOP - 8, "POWER ONE-LINE — 12.47 kV SERVICE, 2N TRANSFORMERS AND SWITCHGEAR, 2N UPS, N+1 GENERATORS", "NTS")
    y = TOP - 30
    xa, xb = 120.0, 330.0
    # utility + MV switchgear
    sh.text(xa + 60, y, "UTILITY 12.47 kV (or 13.8 kV), 3 ph, primary metering", h=2.8, bold=True, ha="center")
    sh.line(xa + 60, y - 4, xa + 60, y - 14, lw=1.2)
    sh.circle(xa + 60, y - 18, 4, lw=0.8); sh.text(xa + 60, y - 18, "kWh", h=1.6, ha="center", va="center")
    sh.text(xa + 68, y - 18, "Utility primary meter + P_utility pulse (meter1)", h=1.8, va="center", c=MUTED)
    sh.line(xa + 60, y - 22, xa + 60, y - 30, lw=1.2)
    sym_box(sh, xa - 20, y - 66, 160, 36, "MV-SWGR — 15 kV PAD-MOUNTED SWITCHGEAR (S&C Vista class)", ["2 source ways (utility + spare), 2 fault-interrupter ways", "600 A, 25 kA, dead-front, SF6-free; relays 50/51, 51N", "MV pad; lockable; utility witness test (CTP-E3 HOLD)"], kind="power")
    sh.line(xa + 20, y - 66, xa + 20, y - 80, lw=1.0); sh.line(xa + 100, y - 66, xa + 100, y - 80, lw=1.0)
    for k, (x, lab) in enumerate(((xa + 20, "A"), (xa + 100, "B"))):
        sym_breaker(sh, x, y - 86, f"FI-{lab}", "600 A FI")
        sh.line(x, y - 92, x, y - 100, lw=1.0)
        sym_box(sh, x - 26, y - 124, 52, 24, f"XFMR-{lab}", [f"{d['transformer_kva']:,} kVA, 12.47 kV D - 480Y/277 V", "FR3 ester, Z 5.75 %, pad-mount", f"FLA {xf_a:,.0f} A at 480 V"], kind="power")
        sh.line(x, y - 124, x, y - 136, lw=1.4)
    # LV switchgear A and B
    yb = y - 140
    for k, (x, lab) in enumerate(((xa + 20, "A"), (xa + 100, "B"))):
        xs = x - 10
        sym_breaker(sh, x, yb - 6, f"MAIN-{lab}", "4000 A LSIG")
        sh.line(x, yb - 12, x, yb - 20, lw=1.4)
    sh.line(xa - 20, yb - 20, xa + 140, yb - 20, lw=2.2)
    sh.text(xa - 20, yb - 25, f"SWGR-A  480 V 4,000 A BUS (UL 1558)", h=2.0, bold=True)
    sh.text(xa + 140, yb - 25, "SWGR-B  480 V 4,000 A BUS", h=2.0, bold=True, ha="right")
    sh.line(xa + 60, yb - 16, xa + 60, yb - 24, lw=0.1, c=PAPER)
    sym_breaker(sh, xa + 60, yb - 20, "TIE", "4000 A N.O.", vertical=False) if False else None
    sh.rect(xa + 52, yb - 23, 16, 6, fc=PAPER, ec=INK, lw=0.8); sh.text(xa + 60, yb - 20, "TIE N.O.", h=1.5, ha="center", va="center")
    sh.text(xa - 20, yb - 29, "Working space 1,500 (NEC 110.26 cond. 3 >= 1,200), two exits (110.26(C)(2)); arc-flash study before energisation", h=1.7, c=MUTED)
    # generators into a paralleling bus feeding both switchgears via gen mains
    xg = xb + 20
    sh.text(xg + 60, y, f"GENERATORS N+1: {d['generators_total']} x {d['generator_kw_each']:,} kW", h=2.8, bold=True, ha="center")
    for k in range(d["generators_total"]):
        gx = xg + k * 44
        sym_box(sh, gx, y - 30, 38, 20, f"GEN{k+1}", [f"{d['generator_kw_each']:,} kW / 1,562 kVA", "480 V, Tier 2 emergency", "48 h fuel (PWR-FUEL-48H)"], kind="power", title_h=2.2)
        sh.line(gx + 19, y - 30, gx + 19, y - 40, lw=1.0)
        sym_breaker(sh, gx + 19, y - 46, "", "2500 A")
        sh.line(gx + 19, y - 52, gx + 19, y - 60, lw=1.0)
    sh.line(xg, y - 60, xg + d["generators_total"] * 44 - 6, y - 60, lw=2.2)
    sh.text(xg, y - 65, "GEN-SWGR — PARALLELING BUS 480 V 4,000 A (ASCO 7000 class): load share, closed-transition utility paralleling, load shed", h=1.8, bold=True)
    for k, (x, lab) in enumerate(((xa + 20, "A"), (xa + 100, "B"))):
        sh.line(xg + 20 + k * 40, y - 60, xg + 20 + k * 40, yb - 8, lw=1.0, ls="--")
        sym_breaker(sh, xg + 20 + k * 40, yb - 2, f"GM-{lab}", "4000 A")
        sh.line(xg + 20 + k * 40, yb - 8, xg + 20 + k * 40, yb - 20, lw=1.0, ls="--")
        sh.line(xg + 20 + k * 40, yb - 20, (xa + 140 if lab == "B" else xa - 20), yb - 20, lw=1.0, ls="--")
    sh.text(xg + 100, yb - 14, "Generator mains to SWGR-A / SWGR-B (interlocked with MAIN-A / MAIN-B)", h=1.7, c=MUTED)
    # UPS strings
    yu = yb - 40
    for k, (x, lab) in enumerate(((xa + 20, "A"), (xa + 100, "B"))):
        sh.line(x, yb - 20, x, yu + 6, lw=1.0)
        sym_breaker(sh, x, yu, f"CB-UPS-{lab}", "3000 A")
        sh.line(x, yu - 6, x, yu - 14, lw=1.0)
        sym_box(sh, x - 30, yu - 50, 60, 36, f"UPS STRING {lab} — {n_frames // 2} x 500 kW", [f"Galaxy VL 500 kW frames in parallel = {n_frames // 2 * 500:,} kW", f"Battery room {lab}: {d['battery_kwh']} kWh LFP, {cfg.ups_minutes} min", "Parallel cabinet + system bypass (PWR-UPS-PARALLEL)", "Modbus TCP to BEN Controller"], kind="power")
        sh.line(x, yu - 50, x, yu - 60, lw=1.0)
        sym_box(sh, x - 30, yu - 84, 60, 24, f"UPS OUTPUT SWGR {lab}", ["480 V 3,000 A, feeder breakers per row busway", f"{d['rows']} x CB 1,000 A to BUS-n{lab} via 300 kVA 480-415 V K-13 transformers"], kind="power")
        sh.line(x, yu - 84, x, yu - 94, lw=1.0)
    sh.text(xa - 32, yu - 56, "EPO: shunt-trip UPS output (CTQ-E3)", h=1.8, c=RED)
    # row busways
    yr = yu - 96
    sh.line(xa - 30, yr, xa + 150, yr, lw=1.4)
    for r in range(d["rows"]):
        xr = xa - 20 + r * 42
        sh.line(xr, yr, xr, yr - 8, lw=0.8); sh.line(xr + 20, yr, xr + 20, yr - 8, lw=0.8)
        sym_box(sh, xr - 6, yr - 30, 36, 22, f"ROW {r+1}", [f"BUS-{r+1}A / BUS-{r+1}B 800 A 415 V", f"{d['racks_per_row']} racks x 2 PDU 60 A", f"{d['per_rack_kw']} kW/rack"], kind="rack", title_h=2.2)
    sh.text(xa - 30, yr - 36, f"Rack PDUs: 2 per rack (A/B), 415 V 60 A metered by outlet (PWR-PDU-HD); row transformers PWR-XFMR-ROW; busway tap-offs 60 A 3P", h=1.8, c=MUTED)
    # mechanical loads
    xm = xb + 40
    ym = yu
    sh.line(xa + 140, yb - 20, xm + 60, yb - 20, lw=0.1, c=PAPER)
    sh.text(xm, ym + 8, "MECHANICAL (non-UPS, from SWGR-A and SWGR-B, auto-transfer)", h=2.4, bold=True)
    loads = [(f"CDU x{d['cooling_units_total']}", f"{std(15 * 1000 / (math.sqrt(3) * 480 * 0.95) * 1.25)} A ea"), (f"FW x{lay.notes.get('n_fanwall', 4)}", f"{std(35 * 1000 / (math.sqrt(3) * 480 * 0.95) * 1.25)} A ea"),
             (f"DC x{lay.notes.get('n_drycooler', 5)}", f"{std(30 * 1000 / (math.sqrt(3) * 480 * 0.95) * 1.25)} A ea"), ("PUMP skid", "150 A"), ("PM HVAC", "60 A"), ("LTG/RCPT", "100 A"), ("CTL", "30 A")]
    for i, (tag, a) in enumerate(loads):
        xl = xm + i * 26
        sh.line(xl, ym, xl, ym - 8, lw=0.8)
        sym_breaker(sh, xl, ym - 12, "", a)
        sh.line(xl, ym - 16, xl, ym - 22, lw=0.8)
        sh.rect(xl - 10, ym - 34, 20, 12, fc=FILL["cooling" if tag[:2] in ("CD", "FW", "DC", "PU") else "controls"], ec=EDGE["cooling" if tag[:2] in ("CD", "FW", "DC", "PU") else "controls"], lw=0.6)
        sh.text(xl, ym - 28, tag, h=1.6, ha="center", va="center", bold=True)
    sh.line(xm - 6, ym, xm + len(loads) * 26, ym, lw=1.4)
    sh.text(xm, ym - 40, f"Mechanical connected load ~{d['cooling_elec_kw'] + 60:.0f} kW; cooling may ride the generators without UPS (DLC loop thermal inertia > 60 s; CDU pumps on UPS-backed controls power)", h=1.7, c=MUTED)
    # grounding
    yg = 92
    sh.text(30, yg + 26, "GROUNDING ELECTRODE SYSTEM (NEC 250, IEEE 80 at the MV pad)", h=3, bold=True)
    sh.line(40, yg + 14, 330, yg + 14, lw=2.0); sh.text(332, yg + 14, "Ground ring #4/0 Cu around hall, power module and MV pad; TMGB in the power module", h=2.0, va="center")
    for i, lab in enumerate(["Ground rods 3 m Cu-clad, every 15 m on the ring", "MV pad grid: step/touch per IEEE 80", "Pad rebar (Ufer) bonds", "Section frames bonded at every joint (CTP-J1)", "Rack / busway / tray bonds, 6 AWG per rack", "UPS, switchgear, CDU, generator frames; SPD at each service"]):
        xg2 = 50 + i * 48
        sh.line(xg2, yg + 14, xg2, yg + 4, lw=0.8)
        if i < 3:
            sh.line(xg2, yg + 4, xg2, yg - 4, lw=1.0); sh.line(xg2 - 4, yg - 4, xg2 + 4, yg - 4, lw=1.0); sh.line(xg2 - 2.5, yg - 6, xg2 + 2.5, yg - 6, lw=0.8); sh.line(xg2 - 1, yg - 8, xg2 + 1, yg - 8, lw=0.6)
        else:
            sh.rect(xg2 - 5, yg - 4, 10, 8, fc=FILL["structure"], lw=0.5)
        for k, ln in enumerate(_wrap(lab, 24)):
            sh.text(xg2, yg - 12 - k * 2.8, ln, h=1.7, ha="center")
    sh.text(30, yg - 24, "Resistance targets: grid <= 5 ohm (MV pad per IEEE 80 study), every bond <= 0.1 ohm (CTQ-E2, WITNESS). Lightning protection per NFPA 780 risk assessment (plant yard masts).", h=1.9, c=MUTED)

    def extra(sh, x, y):
        rows = [["Service", f"{d['voltage']}; 2N pad-mounts {d['transformers_total']} x {d['transformer_kva']:,} kVA; service {d['service_amps_calc']:,} A calc at 480 V"],
                ["Total connected", f"{d['total_kw']:,} kW / {d['total_kva']:,} kVA (IT {cfg.it_kw:.0f} kW + cooling {d['cooling_elec_kw']} kW + aux); PUE est. {d['pue_estimate']}"],
                ["480 V switchgear", "2 lineups 4,000 A UL 1558, drawout, main-tie-main (tie N.O.), gen mains; arc-resistant option"],
                ["UPS", f"2N: {d['ups_modules']} strings x {n_frames // 2} x 500 kW Galaxy VL = {n_frames // 2 * 500:,} kW each; {d['battery_kwh']} kWh LFP per string, {cfg.ups_minutes} min; two battery rooms, 2-hour separation (NFPA 855)"],
                ["Generators", f"{d['generators_total']} x {d['generator_kw_each']:,} kW N+1, paralleling switchgear 4,000 A, 48 h fuel 10,000 gal UL 2085, SPCC"],
                ["IT distribution", f"{d['rows']} rows x busway A/B 800 A 415 V; {cfg.racks} racks x 2 PDU 60 A; {d['per_rack_kw']} kW/rack"],
                ["EPO", "Vestibule and power module: shunt-trip UPS output + CDU pumps hold (thermal inertia); hard-wired, monitored by PLC DI"],
                ["Studies", "Short-circuit, coordination, arc-flash (NEC 110.9/110.10, NFPA 70E), IEEE 80 grid, utility interconnect protection review"]]
        y = sh.table(x, y, ["ITEM", "VALUE"], rows, [RW * 0.24, RW * 0.76], title="ELECTRICAL SCHEDULE (preliminary)", h=1.8)
        y -= 6
        notes = ["ALL RATINGS PRELIMINARY: the engineer of record (SVC-AE-HALL) issues the MV/LV design, protection and arc-flash study before any energisation; NETA acceptance tests on every MV/LV item (CTP-E3 HOLD).",
                 "Only the utility and a licensed MV contractor work on the 12.47 kV side; only a licensed electrician lands 480 V conductors (CTP-E1 HOLD).",
                 "Battery rooms: UL 9540 / UL 9540A data on file; <= 600 kWh per room (check I-H14); deflagration venting and 2-hour separation per NFPA 855; disconnects outside each room.",
                 "Generator paralleling: closed-transition utility paralleling only with utility approval; otherwise open transition at GM-A/GM-B.",
                 "Separation: UPS feeders A and B in separate duct banks to the hall; busway A and B on opposite sides of each row.",
                 "Labelling: every breaker, busway tap-off, cable end and receptacle carries the tag on this sheet (CTQ-B6)."]
        return sh.notes(x, y, "ELECTRICAL NOTES", notes, h=1.9, lead=3.0)
    ctx.right_column(sh, lay, "E-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "E-001"))


# ====================================================================== M-001 cooling P&ID (hall)
def sheet_m001(lay, out, ctx: Ctx, n):
    sh = ctx.new_sheet(lay, "M-001", "Cooling P&ID", "NTS", n)
    d, cfg = lay.d, lay.cfg
    sh.view_title(30, TOP - 8, "COOLING P&ID — DLC: ADIABATIC DRY COOLERS, PRIMARY LOOP, CDU RING HEADER, ROW MANIFOLDS, FAN WALLS", "NTS")
    xleft, y0 = 40, TOP - 40
    n_dc = lay.notes.get("n_drycooler", 5)
    # dry cooler bank
    sh.text(xleft, y0 + 4, f"PLANT YARD — {n_dc} x ADIABATIC DRY COOLERS 400 kW (water-free mode < 25 C), EC FANS", h=2.8, bold=True)
    for k in range(n_dc):
        x = xleft + k * 46
        sym_hx(sh, x, y0 - 34, 40, 24, f"DC{k+1} adiabatic")
        sh.text(x + 20, y0 - 17, "pads + EC fans", h=1.4, ha="center", c=MUTED)
        sh.line(x + 10, y0 - 34, x + 10, y0 - 46, lw=1.2, c=CTQ_C); sh.line(x + 30, y0 - 34, x + 30, y0 - 46, lw=1.2, c=RED)
        sym_valve(sh, x + 10, y0 - 40, size=2.0, vertical=True); sym_valve(sh, x + 30, y0 - 40, size=2.0, vertical=True)
    xh1 = xleft + (n_dc - 1) * 46 + 40
    sh.line(xleft + 10, y0 - 46, xh1, y0 - 46, lw=1.6, c=CTQ_C); sh.line(xleft + 30, y0 - 50, xh1, y0 - 50, lw=1.6, c=RED)
    sh.text(xh1 + 2, y0 - 46, "PRIMARY SUPPLY DN200 (30 % PG), 32 C", h=1.8, va="center", c=CTQ_C)
    sh.text(xh1 + 2, y0 - 50, "PRIMARY RETURN DN200, 42 C", h=1.8, va="center", c=RED)
    sh.text(xleft, y0 - 56, "Make-up water: RPZ backflow preventer, softener/treatment, meter with leak alarm; drain to site; winter: pads drained, dry mode", h=1.7, c=MUTED)
    # pump skid
    yp = y0 - 78
    sym_box(sh, xleft, yp - 20, 70, 20, "PUMP SKID N+1 (CLG-PIPING-HALL)", ["2 x 75 kW VFD pumps", "air separator, expansion, PRV 6 bar", "FM-101 / PI-103 / TI-102"], kind="cooling", title_h=2.2)
    sym_pump(sh, xleft + 80, yp - 10); sym_pump(sh, xleft + 92, yp - 10); sh.text(xleft + 86, yp - 16.5, "P1 / P2", h=1.5, ha="center")
    sh.line(xleft + 40, y0 - 46, xleft + 40, yp, lw=1.4, c=CTQ_C); sh.line(xleft + 46, y0 - 50, xleft + 46, yp, lw=1.4, c=RED)
    sym_instr(sh, xleft + 110, yp - 4, "FM-101"); sym_instr(sh, xleft + 110, yp - 16, "TI-102"); sym_instr(sh, xleft + 124, yp - 10, "PI-103")
    sh.line(xleft + 132, yp - 6, xleft + 180, yp - 6, lw=1.4, c=CTQ_C); sh.line(xleft + 132, yp - 14, xleft + 180, yp - 14, lw=1.4, c=RED)
    sh.text(xleft + 140, yp - 2, "HALL END-WALL PENETRATIONS 2 x DN200 (sleeved, gasketed, hose-tested CTQ-A4)", h=1.6, c=MUTED)
    sh.line(xleft + 176, yp + 2, xleft + 176, yp - 22, c=MUTED, lw=0.4, ls="--")
    # CDUs on a common header (ring)
    yc = yp - 40
    sh.text(xleft, yc + 8, f"HALL — {d['cooling_units_total']} x CDU 300 kW (N+1 SYSTEM-WIDE) ON A PRIMARY HEADER AND A SECONDARY RING MAIN DN150 (check I-H10)", h=2.6, bold=True)
    xc0 = xleft + 10
    pitch = min(60, 420 / d["cooling_units_total"])
    for k in range(d["cooling_units_total"]):
        x = xc0 + k * pitch
        sym_hx(sh, x, yc - 30, pitch - 8, 24, f"CDU{k+1}")
        sh.text(x + (pitch - 8) / 2, yc - 13, "plate HX, N+1 pumps", h=1.3, ha="center", c=MUTED)
        sh.text(x + (pitch - 8) / 2, yc - 16.5, "VFD, 2-way CV, tray", h=1.3, ha="center", c=MUTED)
        sh.line(x + 4, yc - 6, x + 4, yc, lw=1.0, c=CTQ_C); sh.line(x + pitch - 12, yc - 6, x + pitch - 12, yc + 3, lw=1.0, c=RED)
        sh.line(x + 4, yc - 30, x + 4, yc - 40, lw=1.0, c=CTQ_C); sh.line(x + pitch - 12, yc - 30, x + pitch - 12, yc - 44, lw=1.0, c=RED)
        sym_valve(sh, x + 4, yc - 35, size=1.6, vertical=True); sym_valve(sh, x + pitch - 12, yc - 37, size=1.6, vertical=True)
    xc1 = xc0 + d["cooling_units_total"] * pitch
    sh.line(xc0, yc, xc1, yc, lw=1.6, c=CTQ_C); sh.line(xc0, yc + 3, xc1, yc + 3, lw=1.6, c=RED)
    sh.text(xc1 + 2, yc + 1.5, "PRIMARY HEADER (from pump skid)", h=1.6, va="center", c=MUTED)
    sh.line(xc0, yc - 40, xc1, yc - 40, lw=1.8, c=CTQ_C); sh.line(xc0, yc - 44, xc1, yc - 44, lw=1.8, c=RED)
    sh.text(xc1 + 2, yc - 40, "SECONDARY SUPPLY RING DN150, 30 C (TCS, deionised + inhibitor)", h=1.6, va="center", c=CTQ_C)
    sh.text(xc1 + 2, yc - 44, "SECONDARY RETURN RING DN150, 40 C", h=1.6, va="center", c=RED)
    sym_instr(sh, xc0 + 6, yc - 52, "TI-201"); sym_instr(sh, xc0 + 20, yc - 52, "PI-203"); sym_instr(sh, xc0 + 34, yc - 52, "FM-204")
    # row manifolds
    ym = yc - 66
    for r in range(d["rows"]):
        x = xc0 + 50 + r * 100
        sh.line(x, yc - 40, x, ym, lw=1.2, c=CTQ_C); sh.line(x + 6, yc - 44, x + 6, ym - 3, lw=1.2, c=RED)
        sym_valve(sh, x, yc - 50, size=1.8, vertical=True); sym_valve(sh, x + 6, yc - 52, size=1.8, vertical=True)
        sh.line(x, ym, x + 80, ym, lw=1.4, c=CTQ_C); sh.line(x + 6, ym - 3, x + 80, ym - 3, lw=1.4, c=RED)
        sh.text(x + 40, ym + 1.5, f"MAN-{r+1} supply/return DN80 over row {r+1} ({d['racks_per_row']} racks)", h=1.5, ha="center", va="bottom", c=MUTED)
        for i in range(min(d["racks_per_row"], 6)):
            xr = x + 10 + i * 12
            sh.line(xr, ym, xr, ym - 12, lw=0.6, c=CTQ_C); sh.line(xr + 3, ym - 3, xr + 3, ym - 12, lw=0.6, c=RED)
            sh.rect(xr - 3, ym - 22, 9, 10, fc=FILL["rack"], ec=EDGE["rack"], lw=0.5)
            sh.text(xr + 1.5, ym - 17, "R", h=1.2, ha="center", va="center")
        sh.text(x + 74, ym - 17, f"... x{d['racks_per_row']}", h=1.3, c=MUTED)
        sh.text(x + 40, ym - 26, "QD hoses, drip tray, leak rope (CTQ-M3); rack manifold CLG-MANIFOLD", h=1.3, ha="center", c=MUTED)
    # fan walls on the chilled glycol loop (residual air)
    yf = ym - 44
    sh.text(xleft, yf + 4, f"AIR SIDE — {lay.notes.get('n_fanwall', 4)} x FAN WALL 200 kW (N+1) ON THE PRIMARY LOOP, RESIDUAL 25 % OF IT = {0.25 * cfg.it_kw:.0f} kW (check I-H11)", h=2.4, bold=True)
    for k in range(lay.notes.get("n_fanwall", 4)):
        x = xleft + 10 + k * 62
        sym_hx(sh, x, yf - 28, 50, 20, f"FW{k+1} fan wall")
        sh.text(x + 25, yf - 13, "coil, EC fan array, ePM1", h=1.3, ha="center", c=MUTED)
        sh.line(x + 8, yf - 28, x + 8, yf - 36, lw=1.0, c=CTQ_C); sh.line(x + 42, yf - 28, x + 42, yf - 36, lw=1.0, c=RED)
        sym_valve(sh, x + 8, yf - 32, size=1.6, vertical=True)
    xf1 = xleft + 10 + lay.notes.get("n_fanwall", 4) * 62
    sh.line(xleft + 18, yf - 36, xf1, yf - 36, lw=1.2, c=CTQ_C); sh.line(xleft + 52, yf - 39, xf1, yf - 39, lw=1.2, c=RED)
    sh.text(xf1 + 2, yf - 37.5, "Branch from primary header (CDU-independent), supply 32 C -> room 24 C", h=1.5, va="center", c=MUTED)
    sh.text(xleft, yf - 46, "Coolant: primary 30 % propylene glycol (CTQ-M4); secondary TCS per CDU/rack OEM fluid spec; pressure test 1.5 x working pressure 2 h (CTQ-M1 WITNESS); flush < 5 NTU; vents at high points; heat trace outdoors where t_min < 0 C.", h=1.7, c=MUTED)
    # legend
    lx, ly = 30, 80
    sh.text(lx, ly + 16, "SYMBOLS", h=2.6, bold=True)
    sym_valve(sh, lx + 4, ly + 10); sh.text(lx + 10, ly + 10, "Isolation valve", h=1.8, va="center")
    sym_pump(sh, lx + 4, ly + 3, r=2.5); sh.text(lx + 10, ly + 3, "Pump", h=1.8, va="center")
    sym_instr(sh, lx + 54, ly + 10, "TI-xx", r=2.8); sh.text(lx + 60, ly + 10, "Instrument (TI temp, PI pressure, FM flow)", h=1.8, va="center")
    sh.line(lx + 52, ly + 3, lx + 58, ly + 3, lw=1.4, c=CTQ_C); sh.text(lx + 60, ly + 3, "Supply", h=1.8, va="center")
    sh.line(lx + 142, ly + 10, lx + 148, ly + 10, lw=1.4, c=RED); sh.text(lx + 150, ly + 10, "Return", h=1.8, va="center")

    def extra(sh, x, y):
        rows = [["IT load / per rack", f"{cfg.it_kw:.0f} kW / {d['per_rack_kw']} kW"],
                ["Architecture", f"{d['cooling_label']}; DLC removes 75 % at the cold plate (assumption), fan walls take the residual air"],
                ["CDUs (config N / total)", f"{d['cooling_units_n']} / {d['cooling_units_total']} x 300 kW on a ring header; placement {lay.notes.get('cdu_per_row')} per row end"],
                ["Fan walls", f"{lay.notes.get('n_fanwall')} x 200 kW (N+1) on the long wall"],
                ["Heat rejection", f"{lay.notes.get('n_drycooler')} x 400 kW adiabatic dry coolers >= {d['total_kw'] * 1.1:,.0f} kW; chilled-water option above 40 C design"],
                ["Cooling electrical", f"{d['cooling_elec_kw']} kW (COP {L.COOLING_LIBRARY[cfg.cooling]['cop']}); airflow {d['airflow_cfm']:,} cfm residual"],
                ["Setpoints", f"ASHRAE {d['ashrae_class']}; TCS supply 30 C; room 24 C; inlet alarm > 27 C; RH 20-70 %"],
                ["Water", "Adiabatic make-up ~0.5-1.5 L/kWh rejected in wet hours; water-free below 25 C; treatment and RPZ"]]
        y = sh.table(x, y, ["ITEM", "VALUE"], rows, [RW * 0.3, RW * 0.7], title="COOLING SCHEDULE", h=1.8)
        y -= 6
        notes = ["Plant piping, flushing, fill and water treatment by a licensed mechanical contractor (CTP-M1 HOLD); CDU and rack manifold connections per the OEM manuals.",
                 "Secondary ring main lets any CDU serve any row; per-row isolation valves and flow meters; N+1 is system-wide (check I-H10).",
                 "Fan walls draw outside air through ePM1 filters (H2) and weather hoods; intakes >= 5 m from generator exhaust (A-000).",
                 "Leak rope under every CDU, along manifold drip trays and at the end-wall penetrations (CTQ-M3); drains water-tested (CTQ-M2).",
                 "Controls: CDU and fan-wall setpoints from the plant PLC; local control on loss of comms; watchdog relay (CTP-K2); PROTOCOL.md safety rules."]
        return sh.notes(x, y, "COOLING NOTES", notes, h=1.9, lead=3.0)
    ctx.right_column(sh, lay, "M-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "M-001"))


# ====================================================================== C-001 controls (hall)
def sheet_c001(lay, out, ctx: Ctx, n):
    endw, wall = _ext(lay)
    s = 100
    sh = ctx.new_sheet(lay, "C-001", "Controls layout", f"1:{s} / 1:60", n)
    ox, y_top = 40.0, TOP - 14
    oy = y_top - (lay.W + 2 * wall) / s - 24
    v = View(sh, s, ox + endw / s, oy + wall / s)
    sh.view_title(ox, y_top + 6, "SENSOR AND BEN POD PLAN — WHOLE HALL", f"1:{s}")
    _hall_outline(v, lay)
    _plan_items(v, lay, s, labels=False)
    ax = sh.ax
    marker = {"T": ("^", CTQ_C), "RH": ("D", PURPLE), "dP": ("s", GREEN), "leak": ("o", RED), "door": ("P", INK), "kWh": ("h", CTP_C)}
    for sn in lay.sensors:
        x, y = v.p(sn.x, sn.y)
        m, c = marker[sn.kind]
        ax.plot([x], [y], marker=m, ms=3.2 if sn.kind != "T" else 2.2, mfc=PAPER if sn.id.startswith("T_in") else c, mec=c, mew=0.5, zorder=8)
    for it in lay.items:
        if it.kind == "controls" and it.code != "CTL-POD" and it.tag != "LEAK":
            v.rect(it.x0, it.y0, it.x1, it.y1, fc=FILL["controls"], ec=PURPLE, lw=0.7, z=7)
            v.text(it.cx, it.y1 + 150, it.tag, h=1.5, ha="center", va="bottom", c=PURPLE, bold=True)
    for sn in lay.sensors:
        if sn.id.startswith(("RH_room", "dP_aisle", "door_main", "P_utility", "leak_floor")):
            v.leader(sn.x, sn.y, 6, 8 if not sn.id.startswith("leak") else -8, f"{sn.id} ({sn.channel})", h=1.4)
    tr = lay.find("TR-D")
    if tr:
        v.line(tr.x0, tr.cy, tr.x1, tr.cy, c=PURPLE, lw=0.9, ls="-.", z=3)
        v.text(tr.x0 + 300, tr.cy + 250, "Controls LAN on TR-D: fibre ring CP1 -> PLC1..3; RS-485 + 24 VDC to Pod E per module; Modbus TCP to CDUs, fan walls, UPS, PDUs; BEN Mesh (Thread) for Pod W", h=1.4, c=PURPLE, bg=PAPER)
    sh.north_arrow(RX - 45, TOP - 30)
    # zoomed IT zone with pods
    s2 = 60
    x_lo, x_hi = lay.notes["row_x0"] - 1500, lay.notes["row_x1"] + 1500
    y_z = oy - 28
    oyZ = y_z - lay.W / s2 - 8
    vz = View(sh, s2, ox - x_lo / s2, oyZ)
    sh.view_title(ox, y_z + 2, "IT ZONE — PODS (W cold/hot face per rack), INLET PROBES, dP, LEAK ROPE", f"1:{s2}")
    vz.rect(x_lo, 0, x_hi, lay.W, fc=PAPER, ec=INK, lw=0.8, z=1)
    _plan_items(vz, lay, s2, x_lo, x_hi, labels=False)
    for it in lay.items:
        if it.mount == "floor" and it.kind in ("rack", "cooling") and x_lo <= it.cx <= x_hi:
            vz.text(it.cx, it.cy, it.tag, h=1.1, ha="center", va="center", c=MUTED, rot=90)
    for sn in lay.sensors:
        if x_lo <= sn.x <= x_hi:
            x, y = vz.p(sn.x, sn.y)
            m, c = marker[sn.kind]
            ax.plot([x], [y], marker=m, ms=3.4 if sn.kind != "T" else 2.6, mfc=PAPER if sn.id.startswith("T_in") else c, mec=c, mew=0.6, zorder=8)
    for it in lay.items:
        if it.code == "CTL-POD" and it.mount == "rack" and x_lo <= it.cx <= x_hi:
            vz.rect(it.x0, it.y0, it.x1, it.y1, fc=FILL["controls"], ec=PURPLE, lw=0.5, z=7)
    for r, y0, y1, front in lay.notes["rows_y"]:
        cy = y0 - 300 if front == "-y" else y1 + 300
        vz.text(lay.notes["row_x0"] - 200, cy, f"T_in_r{(r-1)*lay.d['racks_per_row']+1}..r{r*lay.d['racks_per_row']} (cold face row {r})", h=1.3, ha="right", va="center", c=CTQ_C)
    for it in lay.items:
        if it.kind == "cooling" and it.mount == "floor" and x_lo <= it.cx <= x_hi:
            vz.line(it.cx, it.y0, it.cx, it.y1, c=RED, lw=0.5, ls=":", z=3)
    vz.poly([(x_lo + 100, 100), (x_hi - 100, 100), (x_hi - 100, lay.W - 100), (x_lo + 100, lay.W - 100), (x_lo + 100, 100)], fc="none", ec=RED, lw=0.5, ls=":", closed=False, z=3)
    vz.bubble(lay.notes["row_x0"] + 2000, lay.notes["rows_y"][0][1] - 50, -14, -10, "CTQ-K1"); vz.bubble(lay.notes["row_x1"] - 2000, lay.notes["rows_y"][3][2] + 50, 14, 10, "CTQ-K2")
    # network diagram
    nx, ny = 30, 122
    sh.text(nx, ny + 22, "BEN CONTROLS PRO — PLANT PLC + ONE PLC PER MODULE, REDUNDANT EDGE COMPUTERS, BEN MESH WITH MULTIPLE BORDER ROUTERS (isolated controls LAN, no internet dependency)", h=2.6, bold=True)
    sym_box(sh, nx, ny - 6, 58, 24, "CP1 BEN CONTROLLER (UL 508A)", ["Plant PLC AXC F 2152 + Axioline F I/O", "2 x Karbon 400 edge (redundant): ben_engine, MQTT, OTBR", "2 x QUINT4 24 VDC, SPD, TPM 2.0"], kind="controls")
    sym_box(sh, nx + 68, ny - 6, 40, 24, "SWITCH RING", ["2 x FL SWITCH 2008 (managed)", "fibre ring to module panels", "VLAN: controls only"], kind="controls")
    sh.line(nx + 58, ny + 6, nx + 68, ny + 6, lw=1.0, c=PURPLE)
    for m in range(lay.modules):
        xk = nx + 118 + m * 50
        sh.line(nx + 108, ny + 6, xk, ny + 6, lw=0.9, c=PURPLE)
        sym_box(sh, xk, ny - 6, 44, 24, f"PLC{m+1} MODULE {m+1}", ["AXC F 2152 + I/O: CDUs, fan wall,", "leak controller, door, fire monitor", f"RCP border router #{m+1}; Pod E (RS-485)"], kind="controls", title_h=2.2)
    xm = nx + 118 + lay.modules * 50 + 6
    sym_box(sh, xm, ny - 6, 52, 24, "MODBUS / SNMP", ["CDUs, fan walls, dry coolers, pump skid", "UPS strings, switchgear meters, gensets", "PDUs (96), meter1 (P_utility)"], kind="power")
    sh.line(nx + 58, ny - 2, nx + 62, ny - 2, lw=0.8, c=CTP_C); sh.line(nx + 62, ny - 2, nx + 62, ny - 14, lw=0.8, c=CTP_C); sh.line(nx + 62, ny - 14, xm, ny - 14, lw=0.8, c=CTP_C); sh.line(xm, ny - 14, xm, ny - 6, lw=0.8, c=CTP_C)
    sh.text(nx, ny - 20, f"Life-safety (fire releasing panels FRP per zone, EPO) is HARD-WIRED; PLCs only monitor dry contacts (CTP-K1 HOLD). {lay.notes.get('n_pods', 102)} BEN Pods: 2 per rack (W) + room and outdoor Pod E per module; Thread mesh with {lay.modules} border routers.", h=1.9, c=RED)
    sh.text(nx, ny - 24, "Pod telemetry 1 Hz over Thread/IPv6 (mutual TLS); channel names per spec/PROTOCOL.md; calibration in Pod Secure Vault NVM (CTQ-K3); attestation at join (CTQ-K5); edge failover < 30 s (CTP-K2).", h=1.9, c=MUTED)
    lx, ly = xm + 62, ny + 14
    for k, (kind, lab) in enumerate([("T", "Pt1000 inlet (3 heights) / outlet per rack on Pods"), ("RH", "RH: HMW90 per module + Pod"), ("dP", "dP cold/hot: Setra 264 per row"), ("leak", "Leak rope (dotted)"), ("door", "Door contact"), ("kWh", "Meter pulse")]):
        m, c = marker[kind]
        ax.plot([lx], [ly - k * 4.0], marker=m, ms=4.2, mfc=PAPER if kind == "T" else c, mec=c, mew=0.7, zorder=8)
        sh.text(lx + 4, ly - k * 4.0, lab, h=1.8, va="center")

    def extra(sh, x, y):
        rows = [[f"T_in_r1..r{lay.cfg.racks}_{{0.4,1.2,1.8}}", "T_in_1..3", f"node1..{lay.notes.get('n_nodes', 24)}", "rack cx", "cold face +/-50", "400/1200/1800", "Pt1000 A ±0.25 C"],
                [f"T_out_r1..r{lay.cfg.racks}", "T_out_1", "node1..24", "rack cx", "hot face", "1200", "Pt1000 A"]]
        for sn in lay.sensors:
            if not sn.id.startswith(("T_in", "T_out")):
                rows.append([sn.id, sn.channel, sn.node, f"{sn.x:.0f}", f"{sn.y:.0f}", f"{sn.z:.0f}", {"T": "Pt1000 A", "RH": "HMW90 ±1.5 %RH", "dP": "264 ±0.4 Pa", "leak": "rope 0/1", "door": "reed 0/1", "kWh": "S0 pulse"}[sn.kind]])
        y = sh.table(x, y, ["SENSOR ID", "CHANNEL", "NODE ID", "x", "y", "z", "TYPE / u95"], rows,
                     [RW * 0.28, RW * 0.13, RW * 0.12, RW * 0.1, RW * 0.11, RW * 0.11, RW * 0.15], h=1.6, rowh=3.2, title="SENSOR SCHEDULE (interior mm; matches twin.sensors() and PROTOCOL.md)")
        return y
    ctx.right_column(sh, lay, "C-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "C-001"))
