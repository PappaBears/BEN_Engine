#!/usr/bin/env python3
"""Generate BEN Engine Rev 2 livery, data plate bands, QR plates and equipment nameplates.

    python3 brand/v2/livery/gen_livery.py            # SVG production files
    python3 brand/v2/livery/gen_livery.py --png      # + PNG previews (headless Chromium via playwright)

Reads tier data from software/ben_engine/config.py (TIER_GEOMETRY, read-only import). Tiers the
lineup has not landed yet (BEN 1, BEN 300, BEN 1000) fall back to docs/REV2_DECISION.md §2 values,
and every fallback is listed in livery/MANIFEST.json so nobody mistakes it for model output.

Decision defaults (docs/REV2_DECISION.md §1, §4.3): outdoor tiers get a Shop White body with the Night
Navy data plate band; BEN 1 (indoor mini rack) gets a Night Navy body with an S2 band.
All type in the artwork is outlined (fontTools); logo masters are placed from brand/v2/ unchanged.
"""
from __future__ import annotations

import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from brandlib import (C, REPO, Outliner, band, embed, master_aspect, plate_fields, qr_group,  # noqa: E402
                      svg_doc, _esc)

sys.path.insert(0, str(REPO / "software"))
try:
    from ben_engine import config as _cfg  # noqa: E402
    GEOM = dict(getattr(_cfg, "TIER_GEOMETRY", {}))
except Exception as e:  # pragma: no cover - the lineup agent may be mid-edit
    print(f"warning: could not import software/ben_engine/config.py ({e}); using decision-table fallbacks", file=sys.stderr)
    GEOM = {}

OUT = HERE
PREV = HERE / "previews"
ISO_W = 2438.0
ISO_H = 2896.0

# Fallbacks from docs/REV2_DECISION.md §2 (used only when config.py does not carry the tier yet).
FALLBACK = {
    "ben1": {"label": "BEN 1", "it_kw_max": 1.5, "voltage": "120 V 1ph", "ip": "IP20", "kind": "mini_rack"},
    "ben300": {"label": "BEN 300", "it_kw_max": 300, "voltage": "480 V 3ph", "ip": "IP66", "kind": "module", "ext_l_m": 6.058, "ext_w_m": 2.438, "ext_h_m": 2.896},
    "ben1000": {"label": "BEN 1000", "it_kw_max": 1000, "voltage": "480 V 3ph", "ip": "IP66", "kind": "module", "ext_l_m": 12.192, "ext_w_m": 2.438, "ext_h_m": 2.896},
}
# Tier product lines (the line under the tier designation; replaces the Rev 1 "Business Edge Node" strap).
# Same strings as dashboard/static/tooltip.js PRODUCT_LINE and the web product page.
PRODUCT_LINE = {
    "ben1": "Mini rack", "ben5": "Outdoor cabinet", "ben30": "10 ft module", "ben150": "20 ft module",
    "ben300": "Dense liquid · 20 ft", "ben500": "40 ft module", "ben700": "Dense liquid · 40 ft",
    "ben1000": "Dense liquid · 40 ft", "ben2000": "Prefabricated hall",
}


def product_line(key: str) -> str:
    return PRODUCT_LINE.get(key, "")


# Which tiers get which drawings (module length class from the decision table).
def _plan() -> list:
    """Every non-hall tier the configuration model carries, in IT-power order; decision-table fallbacks only for
    new tiers the model does not carry yet (BEN 1000 is skipped once the model renames it, e.g. to BEN 700)."""
    kinds = {"minirack": "mini_rack", "mini_rack": "mini_rack", "cabinet": "cabinet", "module": "module"}
    plan = [(k, kinds[g.get("kind")]) for k, g in GEOM.items() if g.get("kind") in kinds]
    aliases = getattr(_cfg, "TIER_ALIASES", {}) if GEOM else {}
    for k, fb in FALLBACK.items():
        if k not in GEOM and aliases.get(k) not in GEOM:
            plan.append((k, fb["kind"] if fb["kind"] != "mini_rack" else "mini_rack"))
    order = lambda kv: float((GEOM.get(kv[0]) or FALLBACK.get(kv[0], {})).get("it_kw_max") or 0)
    return sorted(plan, key=order)


PLAN = _plan()

WEEK = _dt.date(2026, 11, 9).isocalendar()


def sample_serial(label: str) -> str:
    """Proposed serial format <TIER>-<YYWW>-<NNNN> (open question for the operator); sample unit 0001."""
    return f"{label.replace(' ', '')}-{WEEK[0] % 100:02d}{WEEK[1]:02d}-0001"


def plate_url(serial: str) -> str:
    return f"https://schreiberai.com/ben/{serial}?src=plate"


def volt(v: str) -> str:
    """'120 V 1ph 15/20 A plug-in' -> '120 V 1φ'; '480 V 3ph' -> '480 V 3φ'."""
    import re
    m = re.match(r"^\s*([\d/.,]+\s*k?V(?:\s*\dph)?)", v)
    return (m.group(1) if m else v).replace("3ph", "3φ").replace("1ph", "1φ")


def tier_info(key: str) -> dict:
    g = GEOM.get(key) or {}
    fb = FALLBACK.get(key, {})
    src = "config.py" if g else "REV2_DECISION.md §2 (fallback)"
    label = g.get("label") or fb.get("label") or key.upper()
    enc = g.get("enclosure", "")
    ip = fb.get("ip") or ("IP66" if "IP66" in enc or g.get("kind") in ("cabinet", "module") else "IP20")
    if g.get("ip_rating"):
        ip = g["ip_rating"]
    info = {
        "key": key, "label": label, "source": src,
        "it_kw_max": g.get("it_kw_max", fb.get("it_kw_max")),
        "voltage": volt(g.get("voltage", fb.get("voltage", "480 V 3ph"))),
        "ip": ip, "kind": g.get("kind", fb.get("kind")),
        "L": 1000 * float(g.get("ext_l_m", fb.get("ext_l_m", 0)) or 0),
        "W": 1000 * float(g.get("ext_w_m", fb.get("ext_w_m", 0)) or 0),
        "H": 1000 * float(g.get("ext_h_m", fb.get("ext_h_m", 0)) or 0),
        "fallback_fields": sorted(k for k in ("label", "it_kw_max", "voltage") if k not in g),
    }
    info["serial"] = sample_serial(label)
    return info


def kw(v) -> str:
    if v is None:
        return "?"
    v = float(v)
    return f"{v:,.0f}" if v >= 10 or v == int(v) else f"{v:g}"


XB = Outliner("xbold125")
BL = Outliner("black125")
MONO = Outliner("mono_med")


def note_block(x: float, y: float, w: float, lines, size: float) -> str:
    """Spec notes under the artwork: live text (not cut), Plex Mono."""
    out = [f'<g data-role="spec-notes" font-family="IBM Plex Mono, Consolas, monospace" font-size="{size:.2f}" fill="{C["slate"]}">']
    out.append(f'<rect x="{x:.2f}" y="{y - size * 1.6:.2f}" width="{w:.2f}" height="{size * 0.12:.2f}" fill="{C["border"]}"/>')
    import textwrap
    per = max(int(w / (0.61 * size)), 30)
    i = 0
    for n, ln in enumerate(lines):
        weight = ' font-weight="600" fill="#0B1A31"' if n == 0 else ""
        for part in textwrap.wrap(ln, per):
            out.append(f'<text x="{x:.2f}" y="{y + i * size * 1.55:.2f}"{weight}>{_esc(part)}</text>')
            i += 1
    out.append("</g>")
    return "".join(out)


def frame(art_w: float, art_h: float, art: str, notes, title: str, desc: str, ground: str = "#FFFFFF") -> str:
    m = 0.06 * max(art_w, art_h)
    ns = max(0.016 * max(art_w, art_h), 2.2)
    import textwrap
    per = max(int(art_w / (0.61 * ns)), 30)
    notes_h = ns * 1.55 * (sum(len(textwrap.wrap(n, per)) for n in notes) + 1.2)
    W, H = art_w + 2 * m, art_h + 2 * m + notes_h
    body = [f'<rect width="{W:.2f}" height="{H:.2f}" fill="{ground}"/>',
            f'<g id="artwork" transform="translate({m:.2f} {m:.2f})">{art}</g>',
            note_block(m, art_h + m * 1.6 + ns, art_w, notes, ns)]
    return svg_doc(W, H, body, unit="mm", title=title, desc=desc)


# --------------------------------------------------------------------------- outdoor modules (Shop White body)
def product_block(x0: float, y0: float, M: float, prefix: str, master: str = "lockup-deep", ink: str = C["ink"]) -> str:
    """Horizontal lockup (mark height M) + 'BEN ENGINE' product line set like the wordmark:
    Archivo ExtraBold wdth 125, +2 % tracking, cap height 0.38 M, 0.30 M below the wordmark, aligned to it."""
    s = [embed(master, x0, y0, M, prefix)]
    size = 0.05539 * 1000 / 100 * M  # wordmark em = 55.39 units per 100-unit mark
    base = y0 + 0.69 * M + 0.30 * M + 0.38 * M
    s.append(XB.svg("BEN ENGINE", size, x0 + 1.27213 * M, base, ink, tracking=0.02, label="BEN Engine"))
    return "".join(s)


def module_side(t: dict) -> str:
    L, H = t["L"], t["H"] or ISO_H
    post, rail_t, rail_b = 160.0, 110.0, 160.0
    a = [f'<rect width="{L:.1f}" height="{H:.1f}" fill="{C["shop"]}"/>']
    pitch = 278.0
    x = post + 40
    while x + 160 < L - post:
        a.append(f'<rect x="{x:.1f}" y="{rail_t:.1f}" width="150" height="{H - rail_t - rail_b:.1f}" fill="#E8EDF4"/>')
        x += pitch
    for px in (0, L - post):
        a.append(f'<rect x="{px:.1f}" y="0" width="{post}" height="{H:.1f}" fill="#E4EAF2" stroke="#B9C6D6" stroke-width="4"/>')
    a.append(f'<rect x="0" y="0" width="{L:.1f}" height="{rail_t}" fill="#E4EAF2" stroke="#B9C6D6" stroke-width="4"/>')
    a.append(f'<rect x="0" y="{H - rail_b:.1f}" width="{L:.1f}" height="{rail_b}" fill="#E4EAF2" stroke="#B9C6D6" stroke-width="4"/>')
    for cx, cy in ((0, 0), (L - 178, 0), (0, H - 118), (L - 178, H - 118)):
        a.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="178" height="118" fill="#C3CEDB"/>')
    # data plate band (Night Navy) along the bottom of the side, above the bottom rail
    bh = round(0.066 * H)
    by = H - rail_b - bh
    fields = plate_fields(t["label"], t["serial"], kw(t["it_kw_max"]), t["voltage"], t["ip"])
    a.append(band(post, by, L - 2 * post, bh, fields, ground=C["night"], text=C["fog"], lead=C["signal"], rule=C["border"],
                  rivet_ring=C["steel"], rivet_fill=C["night"], qr_url=plate_url(t["serial"]), qr_code_w=100.0,
                  rows=1 if L > 5000 else 2))
    # lockup + product line, top left
    inset = 0.06 * H
    M = min(0.165 * H, 0.80 * (L - 2 * post - 2 * inset) / master_aspect("lockup-deep"))
    a.append(product_block(post + inset, rail_t + 0.10 * H, M, "s_"))
    # tier designation, right, above the band
    cap = 0.62 * M
    tier_base = by - 0.085 * H - 0.30 * M
    a.append(BL.svg(t["label"].upper(), BL.size_for_cap(cap), L - post - inset, tier_base, C["ink"], tracking=0.01, anchor="end", label=t["label"]))
    pl = product_line(t["key"])
    if pl:   # tier product line, Plex Mono Medium caps +8 %, Slate, cap 0.16 x mark, right-aligned under the tier
        a.append(MONO.svg(pl.upper(), MONO.size_for_cap(0.16 * M), L - post - inset, by - 0.045 * H, C["slate"], tracking=0.08, anchor="end", label=pl))
    a.append(f'<rect x="0" y="0" width="{L:.1f}" height="{H:.1f}" fill="none" stroke="{C["steel"]}" stroke-width="6"/>')
    return "".join(a), M, bh


def module_door(t: dict) -> str:
    W, H = t["W"] or ISO_W, t["H"] or ISO_H
    post, rail_t, sill = 160.0, 110.0, 160.0
    a = [f'<rect width="{W:.1f}" height="{H:.1f}" fill="{C["shop"]}"/>']
    leaf = (W - 2 * post) / 2
    for i in range(2):
        lx = post + i * leaf
        a.append(f'<rect x="{lx + 6:.1f}" y="{rail_t + 6:.1f}" width="{leaf - 12:.1f}" height="{H - rail_t - sill - 12:.1f}" fill="{C["shop"]}" stroke="#B9C6D6" stroke-width="5"/>')
        x = lx + 70
        while x + 120 < lx + leaf - 40:
            a.append(f'<rect x="{x:.1f}" y="{rail_t + 30:.1f}" width="120" height="{H - rail_t - sill - 60:.1f}" fill="#E8EDF4"/>')
            x += 260
    for px in (0, W - post):
        a.append(f'<rect x="{px:.1f}" y="0" width="{post}" height="{H:.1f}" fill="#E4EAF2" stroke="#B9C6D6" stroke-width="4"/>')
    a.append(f'<rect x="0" y="0" width="{W:.1f}" height="{rail_t}" fill="#E4EAF2" stroke="#B9C6D6" stroke-width="4"/>')
    a.append(f'<rect x="0" y="{H - sill:.1f}" width="{W:.1f}" height="{sill}" fill="#E4EAF2" stroke="#B9C6D6" stroke-width="4"/>')
    # artwork
    bh = round(0.07 * H)
    by = H - sill - bh
    fields = plate_fields(t["label"], t["serial"], kw(t["it_kw_max"]), t["voltage"], t["ip"])
    art = []
    stack_h = min(0.22 * H, 0.66 * (W - 2 * post) / master_aspect("stack-deep"))
    M = stack_h / 1.65
    sx = (W - stack_h * master_aspect("stack-deep")) / 2
    sy = rail_t + 0.14 * H
    art.append(embed("stack-deep", sx, sy, stack_h, "d_"))
    size = 0.5539 * M
    base = sy + stack_h + 0.30 * M + 0.38 * M
    art.append(XB.svg("BEN ENGINE", size, W / 2, base, C["ink"], tracking=0.02, anchor="middle", label="BEN Engine"))
    art.append(BL.svg(t["label"].upper(), BL.size_for_cap(0.62 * M), W / 2, base + 0.30 * M + 0.62 * M + 0.15 * M, C["ink"], tracking=0.01, anchor="middle", label=t["label"]))
    pl = product_line(t["key"])
    if pl:
        art.append(MONO.svg(pl.upper(), MONO.size_for_cap(0.16 * M), W / 2, base + 0.30 * M + 0.62 * M + 0.15 * M + 0.42 * M, C["slate"], tracking=0.08, anchor="middle", label=pl))
    a += art
    a.append(band(post, by, W - 2 * post, bh, fields, ground=C["night"], text=C["fog"], lead=C["signal"], rule=C["border"],
                  rivet_ring=C["steel"], rivet_fill=C["night"], qr_url=plate_url(t["serial"]), qr_code_w=100.0, rows=2))
    # lock rods and cam keepers sit in front of the vinyl: cut around them
    for i in range(2):
        lx = post + i * leaf
        for f in (0.24, 0.76):
            rx = lx + f * leaf
            a.append(f'<rect x="{rx - 19:.1f}" y="{rail_t - 40:.1f}" width="38" height="{H - rail_t - sill + 80:.1f}" fill="none" stroke="#8EA7C8" stroke-width="4" stroke-dasharray="24 14"/>')
            a.append(f'<rect x="{rx - 45:.1f}" y="{H * 0.80:.1f}" width="90" height="150" rx="10" fill="none" stroke="#8EA7C8" stroke-width="4"/>')
    # equipment nameplate position (regulatory plate, 4 x 2 in), right leaf
    npx, npy = W - post - leaf + 0.40 * leaf, by - 0.12 * H
    a.append(f'<rect x="{npx:.1f}" y="{npy:.1f}" width="101.6" height="50.8" fill="{C["night"]}" stroke="{C["deep"]}" stroke-width="2"/>')
    a.append(f'<rect x="0" y="0" width="{W:.1f}" height="{H:.1f}" fill="none" stroke="{C["steel"]}" stroke-width="6"/>')
    return "".join(a), M, bh, (npx, npy)


# --------------------------------------------------------------------------- BEN 5 outdoor cabinet
def cabinet_view(t: dict, view: str) -> str:
    W = (t["L"] or 1200.0) if view == "side" else (t["W"] or 1000.0)
    H = t["H"] or 1800.0
    skid, hood = 100.0, 60.0
    a = [f'<rect x="0" y="{H - skid:.1f}" width="{W:.1f}" height="{skid}" fill="#8EA7C8"/>',
         f'<rect x="10" y="{hood:.1f}" width="{W - 20:.1f}" height="{H - skid - hood:.1f}" rx="14" fill="{C["shop"]}" stroke="{C["steel"]}" stroke-width="4"/>',
         f'<rect x="0" y="0" width="{W:.1f}" height="{hood + 10:.1f}" rx="10" fill="#E4EAF2" stroke="{C["steel"]}" stroke-width="4"/>']
    if view == "door":
        a.append(f'<rect x="40" y="{hood + 30:.1f}" width="{W - 80:.1f}" height="{H - skid - hood - 60:.1f}" rx="10" fill="none" stroke="#B9C6D6" stroke-width="4"/>')
        a.append(f'<rect x="{W - 95:.1f}" y="{H * 0.42:.1f}" width="34" height="200" rx="8" fill="#AEBBCB" stroke="#8EA7C8" stroke-width="3"/>')
        for hy in (0.18, 0.5, 0.82):
            a.append(f'<rect x="24" y="{hood + hy * (H - skid - hood) - 40:.1f}" width="22" height="80" rx="4" fill="#C3CEDB"/>')
    else:
        # cabinet DX condenser grille on the side
        gx, gy, gw, gh = W * 0.18, H * 0.47, W * 0.64, H * 0.20
        a.append(f'<rect x="{gx:.1f}" y="{gy:.1f}" width="{gw:.1f}" height="{gh:.1f}" rx="8" fill="#E4EAF2" stroke="#B9C6D6" stroke-width="3"/>')
        yy = gy + 18
        while yy < gy + gh - 10:
            a.append(f'<rect x="{gx + 16:.1f}" y="{yy:.1f}" width="{gw - 32:.1f}" height="7" rx="3" fill="#C3CEDB"/>')
            yy += 22
    inner_w = W - 80
    stack_h = min(0.20 * H, 0.72 * inner_w / master_aspect("stack-deep"))
    M = stack_h / 1.65
    sx = (W - stack_h * master_aspect("stack-deep")) / 2
    sy = hood + 0.07 * H
    a.append(embed("stack-deep", sx, sy, stack_h, f"c{view}_"))
    base = sy + stack_h + 0.68 * M
    a.append(XB.svg("BEN ENGINE", 0.5539 * M, W / 2, base, C["ink"], tracking=0.02, anchor="middle", label="BEN Engine"))
    a.append(BL.svg(t["label"].upper(), BL.size_for_cap(0.55 * M), W / 2, base + 0.30 * M + 0.55 * M, C["ink"], tracking=0.01, anchor="middle", label=t["label"]))
    pl = product_line(t["key"])
    if pl:
        a.append(MONO.svg(pl.upper(), MONO.size_for_cap(0.15 * M), W / 2, base + 0.30 * M + 0.55 * M + 0.40 * M, C["slate"], tracking=0.08, anchor="middle", label=pl))
    bh = 140.0
    by = H - skid - 40 - bh
    fields = plate_fields(t["label"], t["serial"], kw(t["it_kw_max"]), t["voltage"], t["ip"])
    a.append(band(10, by, W - 20, bh, fields, ground=C["night"], text=C["fog"], lead=C["signal"], rule=C["border"],
                  rivet_ring=C["steel"], rivet_fill=C["night"], qr_url=plate_url(t["serial"]), qr_code_w=64.0, rows=2))
    if view == "door":
        a.append(f'<rect x="{W * 0.5 - 50.8:.1f}" y="{by - 120:.1f}" width="101.6" height="50.8" fill="{C["night"]}" stroke="{C["deep"]}" stroke-width="2"/>')
    return "".join(a), W, H, M, bh


# --------------------------------------------------------------------------- BEN 1 mini racks (Night Navy body)
def ben1_bezel(t: dict) -> str:
    W, H = 254.0, 8 * 44.45
    ear = 16.0
    a = [f'<rect width="{W}" height="{H:.2f}" rx="3" fill="{C["night"]}"/>']
    for ex in (0, W - ear):
        a.append(f'<rect x="{ex}" y="0" width="{ear}" height="{H:.2f}" fill="{C["s1"]}"/>')
        for u in range(8):
            for k in (6.35, 22.225, 38.1):
                a.append(f'<rect x="{ex + ear / 2 - 2.6:.2f}" y="{u * 44.45 + k - 2.6:.2f}" width="5.2" height="5.2" rx="0.8" fill="{C["border"]}"/>')
    iw = W - 2 * ear
    M = 0.62 * iw / master_aspect("lockup-signal") * 1.0
    x0 = ear + (iw - M * master_aspect("lockup-signal")) / 2
    y0 = 18.0
    a.append(embed("lockup-signal", x0, y0, M, "b_"))
    base = y0 + M + 0.30 * M + 0.38 * M
    a.append(XB.svg("BEN ENGINE", 0.5539 * M, x0 + 1.27213 * M, base, C["fog"], tracking=0.02, label="BEN Engine"))
    # sound-damped intake: perforated field
    py0, py1 = base + 14, H - 112
    yy = py0
    row = 0
    while yy < py1:
        xx = ear + 14 + (3.0 if row % 2 else 0)
        while xx < W - ear - 14:
            a.append(f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="1.5" fill="{C["s2"]}"/>')
            xx += 6.0
        yy += 5.2
        row += 1
    a.append(BL.svg(t["label"].upper(), BL.size_for_cap(22), W - ear - 12, H - 66, C["paper"], tracking=0.01, anchor="end", label=t["label"]))
    a.append(MONO.svg(f"{product_line('ben1').upper()} · 10-INCH 8U", 4.2, ear + 12, H - 66, C["steel"], tracking=0.08))
    bh = 40.0
    fields = plate_fields(t["label"], t["serial"], "0.6", t["voltage"], t["ip"])
    a.append(band(ear, H - 8 - bh, iw, bh, fields, ground=C["s2"], text=C["fog"], lead=C["signal"], rule=C["border"],
                  rivet_ring=C["steel"], rivet_fill=C["night"], qr_url=plate_url(t["serial"]), qr_code_w=20.32, rows=2))
    return "".join(a), W, H, M, bh


def ben1_door(t: dict) -> str:
    FW, FH = 600.0, 720.0
    a = [f'<rect width="{FW}" height="{FH}" rx="8" fill="{C["s1"]}"/>']
    dx, dy, DW, DH = 20.0, 30.0, 560.0, 650.0
    a.append(f'<rect x="{dx}" y="{dy}" width="{DW}" height="{DH}" rx="6" fill="{C["night"]}" stroke="{C["border"]}" stroke-width="2"/>')
    for sy in (dy + 14, dy + DH - 34):
        x = dx + 40
        while x < dx + DW - 60:
            a.append(f'<rect x="{x:.1f}" y="{sy:.1f}" width="14" height="20" rx="3" fill="{C["s2"]}"/>')
            x += 22
    a.append(f'<rect x="{dx + DW - 34:.1f}" y="{dy + DH * 0.40:.1f}" width="14" height="120" rx="6" fill="{C["s3"]}" stroke="{C["border"]}" stroke-width="1.5"/>')
    stack_h = min(0.26 * DH, 0.66 * DW / master_aspect("stack-signal"))
    M = stack_h / 1.65
    sx = dx + (DW - stack_h * master_aspect("stack-signal")) / 2
    sy = dy + 70
    a.append(embed("stack-signal", sx, sy, stack_h, "bd_"))
    base = sy + stack_h + 0.68 * M
    a.append(XB.svg("BEN ENGINE", 0.5539 * M, dx + DW / 2, base, C["fog"], tracking=0.02, anchor="middle", label="BEN Engine"))
    a.append(BL.svg(t["label"].upper(), BL.size_for_cap(0.62 * M), dx + DW / 2, base + 0.30 * M + 0.62 * M, C["paper"], tracking=0.01, anchor="middle", label=t["label"]))
    a.append(MONO.svg(f"{product_line('ben1').upper()} · 19-INCH 12U · SOUND-DAMPED", 8.0, dx + DW / 2, base + 0.30 * M + 0.62 * M + 34, C["steel"], tracking=0.08, anchor="middle"))
    bh = 52.0
    by = dy + DH - 48 - bh
    fields = plate_fields(t["label"], t["serial"], kw(t["it_kw_max"]), t["voltage"], t["ip"])
    a.append(band(dx, by, DW, bh, fields, ground=C["s2"], text=C["fog"], lead=C["signal"], rule=C["border"],
                  rivet_ring=C["steel"], rivet_fill=C["night"], qr_url=plate_url(t["serial"]), qr_code_w=25.4, rows=2))
    return "".join(a), FW, FH, M, bh


# --------------------------------------------------------------------------- equipment nameplate (regulatory)
def nameplate(t: dict | None) -> str:
    """4 x 2 in two-ply engraving laminate: Night Navy cap over white core (engraved = white).
    Static brand elements are outlined; field values are live text placeholders for the engraver."""
    W, H = 101.6, 50.8
    white = "#FFFFFF"
    a = [f'<rect width="{W}" height="{H}" rx="2.5" fill="{C["night"]}"/>',
         f'<rect x="1.2" y="1.2" width="{W - 2.4}" height="{H - 2.4}" rx="1.6" fill="none" stroke="{white}" stroke-width="0.3"/>']
    for cx, cy in ((4.2, 4.2), (W - 4.2, 4.2), (4.2, H - 4.2), (W - 4.2, H - 4.2)):
        a.append(f'<circle cx="{cx}" cy="{cy}" r="1.6" fill="none" stroke="{white}" stroke-width="0.3"/>')  # 3.2 mm mounting holes
    a.append(embed("lockup-white", 8.0, 3.2, 6.6, "np_"))
    lab = Outliner("mono_semi")
    a.append(lab.svg("INDUSTRIAL CONTROL PANEL", 2.05, W - 8.0, 6.3, white, tracking=0.06, anchor="end"))
    a.append(lab.svg("BEN ENGINE · REV 2", 2.05, W - 8.0, 9.4, white, tracking=0.06, anchor="end", label="BEN Engine · Rev 2"))
    a.append(f'<rect x="3" y="11.6" width="{W - 6}" height="0.35" fill="{white}"/>')
    if t:
        ph = "3" if "3φ" in t["voltage"] else ("1" if "1φ" in t["voltage"] else "{{PHASE}}")
        vv = t["voltage"].split(" V")[0] + " V AC" if " V" in t["voltage"] else "{{VOLTAGE}}"
        enc = "UL 50E Type 4X" if t["ip"] == "IP66" else "{{ENCLOSURE_TYPE}}"
        model = t["label"]
    else:
        ph, vv, enc, model = "{{PHASE}}", "{{VOLTAGE}}", "{{ENCLOSURE_TYPE}}", "{{MODEL}}"
    fields = [("MODEL", model), ("SERIAL NO.", "{{SERIAL}}"),
              ("SUPPLY VOLTAGE", vv), ("PHASE", ph),
              ("FREQUENCY", "60 Hz"), ("FULL-LOAD AMPS", "{{FLA}} A"),
              ("LARGEST MOTOR FLA", "{{MOTOR_FLA}} A"), ("SCCR", "{{SCCR}} kA rms sym, {{SCCR_V}} V"),
              ("ENCLOSURE", enc), ("WIRING DIAGRAM", "{{DWG_NO}}"),
              ("MFG DATE", "{{YYYY-MM}}"), ("MANUFACTURER", "Schreiber AI")]
    col_x = (4.6, 52.6)
    y0, dy = 15.3, 4.92
    for i, (k, v) in enumerate(fields):
        cx = col_x[i % 2]
        y = y0 + (i // 2) * dy
        a.append(Outliner("mono_med").svg(k, 1.55, cx, y, white, tracking=0.06))
        a.append(f'<text x="{cx}" y="{y + 2.55:.2f}" font-family="IBM Plex Mono, Consolas, monospace" font-weight="600" font-size="2.15" fill="{white}" data-field="{_esc(k)}">{_esc(v)}</text>')
    a.append(f'<rect x="7.5" y="{H - 6.2:.2f}" width="{W - 15}" height="0.3" fill="{white}"/>')
    a.append(Outliner("mono_med").svg("SCHREIBER AI · SCHREIBERAI.COM", 1.55, 7.6, H - 2.55, white, tracking=0.06,
                                      label="Schreiber AI · schreiberai.com"))
    a.append(f'<rect x="{W - 22.5:.2f}" y="{H - 5.3:.2f}" width="15" height="3.9" rx="0.6" fill="none" stroke="{white}" stroke-width="0.25" stroke-dasharray="0.8 0.6"/>')
    a.append(Outliner("mono_med").svg("LISTING MARK", 1.0, W - 15.0, H - 2.75, white, tracking=0.04, anchor="middle"))
    return "".join(a), W, H


# --------------------------------------------------------------------------- write everything
def write(name: str, svg: str, manifest: list, meta: dict) -> Path:
    p = OUT / name
    p.write_text(svg, encoding="utf-8")
    manifest.append({"file": f"brand/v2/livery/{name}", **meta})
    return p


def main(png: bool) -> None:
    PREV.mkdir(exist_ok=True)
    manifest: list = []
    written = []
    common = ["Spec · Schreiber AI brand v2 · BEN Engine Rev 2 · scale 1:1, units mm · all type outlined, masters from brand/v2 (do not redraw)"]
    pms = "Night Navy #06101F ≈ PMS 2767 C (proof) · Deep Cobalt #1E40AF ≈ PMS 2728 C · Signal Blue #4C9DFF ≈ PMS 2727 C · Shop White #F4F7FB (proof vs paint fan deck)"
    for key, kind in PLAN:
        t = tier_info(key)
        meta = {"tier": key, "label": t["label"], "data_source": t["source"], "fallback_fields": t["fallback_fields"], "serial_sample": t["serial"],
                "qr_url": plate_url(t["serial"])}
        if kind == "module":
            art, M, bh = module_side(t)
            length_class = {2991: "10 ft", 6058: "20 ft", 12192: "40 ft"}.get(round(t["L"]), f"{t['L']:.0f} mm")
            notes = common + [f"{t['label']} · {length_class} high-cube module · side · body Shop White, data plate band Night Navy (decision default, REV2_DECISION §4.3)",
                              f"Lockup: lockup-deep, mark height {M:.0f} mm · tier product line “{product_line(key)}” Plex Mono Medium caps, Slate · product line BEN ENGINE Archivo ExtraBold wdth 125 +2 %, cap {0.38 * M:.0f} mm (0.38 × mark) · tier Archivo Black wdth 125",
                              f"Band: {bh:.0f} mm, Plex Mono SemiBold caps +16 %, lead Signal Blue, fields Fog #B2C1D8, rivets Steel ring · QR EC M, square modules, 4-module quiet zone, code 100 mm (≥ 2.5 in) on Shop White plate → {plate_url(t['serial'])}",
                              pms, "Vinyl: expand strokes before cutting; cut around castings and posts. Serial shown is a sample; regenerate per unit."]
            written.append(write(f"{key}-side.svg", frame(t["L"], t["H"], art, notes, f"{t['label']} side livery", "Schreiber AI · BEN Engine Rev 2 livery"), manifest, {**meta, "view": "side"}))
            art, M, bh, np = module_door(t)
            notes = common + [f"{t['label']} · module end doors · body Shop White, band Night Navy · stacked lockup stack-deep, mark height {M:.0f} mm",
                              f"Band {bh:.0f} mm across both leaves, 2 rows · QR code 100 mm (≥ 2.5 in) → {plate_url(t['serial'])}",
                              "Lock rods, cam keepers and hinges sit in front of the vinyl: cut around them. Navy 4 × 2 in box = equipment nameplate (nameplate.svg) position, confirm against the electrical drawings.",
                              pms]
            written.append(write(f"{key}-door.svg", frame(t["W"] or ISO_W, t["H"] or ISO_H, art, notes, f"{t['label']} door livery", "Schreiber AI · BEN Engine Rev 2 livery"), manifest, {**meta, "view": "door"}))
        elif kind == "cabinet":
            for view in ("side", "door"):
                art, W, H, M, bh = cabinet_view(t, view)
                notes = common + [f"{t['label']} · outdoor NEMA 4X / IP66 cabinet · {view} · body Shop White, band Night Navy · stack-deep, mark height {M:.0f} mm",
                                  f"Band {bh:.0f} mm, 2 rows · QR code 64 mm (≥ 2.5 in) → {plate_url(t['serial'])}" + (" · navy 4 × 2 in box = equipment nameplate" if view == "door" else ""),
                                  pms]
                written.append(write(f"{key}-{view}.svg", frame(W, H, art, notes, f"{t['label']} {view} livery", "Schreiber AI · BEN Engine Rev 2 livery"), manifest, {**meta, "view": view}))
        elif kind == "mini_rack":
            art, W, H, M, bh = ben1_bezel(t)
            notes = common + [f"{t['label']} · 10-inch 8U desk/shelf mini rack · front bezel · Night Navy body (indoor default), S2 band",
                              f"lockup-signal, mark height {M:.1f} mm · band {bh:.0f} mm, 2 rows, rated 0.6 kW (10-inch variant) · QR code 20.3 mm (0.8 in) → {plate_url(t['serial'])}",
                              "Print: UV-print or screen on powder-coated Night Navy steel; QR on a Shop White plate, never reversed."]
            written.append(write(f"{key}-bezel-10in.svg", frame(W, H, art, notes, f"{t['label']} 10-inch bezel livery", "Schreiber AI · BEN Engine Rev 2 livery", ground=C["shop"]), manifest, {**meta, "view": "bezel-10in"}))
            art, W, H, M, bh = ben1_door(t)
            notes = common + [f"{t['label']} · 19-inch 12U sound-damped office cabinet · door · Night Navy body, S2 band · stack-signal, mark height {M:.0f} mm",
                              f"Band {bh:.0f} mm, 2 rows, rated {kw(t['it_kw_max'])} kW · QR code 25.4 mm (1.0 in, ≥ 0.8 in) → {plate_url(t['serial'])}"]
            written.append(write(f"{key}-door-12u.svg", frame(W, H, art, notes, f"{t['label']} 12U cabinet door livery", "Schreiber AI · BEN Engine Rev 2 livery", ground=C["shop"]), manifest, {**meta, "view": "door-12u"}))
        # standalone data plate band + QR plate for the sign shop (door width for modules, item width otherwise)
        bw = {"module": 2118.0, "cabinet": 980.0, "mini_rack": 222.0}[kind]
        bh = {"module": 202.0, "cabinet": 140.0, "mini_rack": 40.0}[kind]
        qw = {"module": 100.0, "cabinet": 64.0, "mini_rack": 20.32}[kind]
        rated = "0.6" if kind == "mini_rack" else kw(t["it_kw_max"])
        g = C["s2"] if kind == "mini_rack" else C["night"]
        fields = plate_fields(t["label"], t["serial"], rated, t["voltage"], t["ip"])
        art = band(0, 0, bw, bh, fields, ground=g, text=C["fog"], lead=C["signal"], rule=C["border"], rivet_ring=C["steel"],
                   rivet_fill=C["night"], qr_url=plate_url(t["serial"]), qr_code_w=qw, rows=2)
        notes = [f"Data plate band · {t['label']} · {bw:.0f} × {bh:.0f} mm · fields: " + " · ".join(fields),
                 f"QR EC M, square modules, 4-module quiet zone, code {qw:g} mm → {plate_url(t['serial'])}"]
        written.append(write(f"{key}-band.svg", frame(bw, bh, art, notes, f"{t['label']} data plate band", "Schreiber AI data plate band"), manifest, {**meta, "view": "band"}))
        qsvg, total = qr_group(plate_url(t["serial"]), 0, 0, qw, C["night"], C["shop"])
        (OUT / f"{key}-qr.svg").write_text(svg_doc(total, total, [qsvg], unit="mm", title=f"{t['label']} plate QR", desc=plate_url(t["serial"])), encoding="utf-8")
        manifest.append({"file": f"brand/v2/livery/{key}-qr.svg", **meta, "view": "qr", "code_mm": qw, "total_mm": round(total, 2)})
        art, W, H = nameplate(t)
        notes = [f"Equipment nameplate · {t['label']} · 4 × 2 in (101.6 × 50.8 mm) · 2-ply engraving laminate, Night Navy cap / white core",
                 "{{FIELDS}} are filled by engineering from the UL 508A panel calc and the unit record; never ship a plate with a placeholder.",
                 "Listing mark area stays blank until the panel is listed."]
        written.append(write(f"{key}-nameplate.svg", frame(W, H, art, notes, f"{t['label']} equipment nameplate", "Regulatory nameplate"), manifest, {**meta, "view": "nameplate"}))
    art, W, H = nameplate(None)
    notes = ["Equipment nameplate template · 4 × 2 in (101.6 × 50.8 mm) · 2-ply engraving laminate, Night Navy cap / white core · 3.2 mm holes at 4.2 mm from edges",
             "UL 508A / NEC 409.110 marking: manufacturer, supply voltage, phase, frequency, full-load current, largest motor FLA, SCCR, enclosure type, wiring diagram no.",
             "Brand: lockup-white 6.6 mm mark; labels Plex Mono Medium 1.55 mm caps; values Plex Mono SemiBold 2.15 mm (min. 1.5 mm cap height engraved)."]
    written.append(write("nameplate-template.svg", frame(W, H, art, notes, "Equipment nameplate template", "Regulatory nameplate template"), manifest, {"view": "nameplate-template"}))
    (OUT / "MANIFEST.json").write_text(json.dumps({"generated_by": "brand/v2/livery/gen_livery.py", "revision": "Rev 2",
                                                   "tiers_from_config": sorted(GEOM.keys()), "files": manifest}, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(written)} drawings + QR files + MANIFEST.json to {OUT.relative_to(REPO)}")
    if png:
        args = []
        for p in written:
            args += [str(p), str(PREV / (p.stem + ".png")), "1600"]
        subprocess.run(["node", str(HERE.parent / "render_png.mjs"), *args], check=True)


if __name__ == "__main__":
    main("--png" in sys.argv)
