"""BEN Engine — assembly stage renders (concept renders generated from the configuration).

Eight isometric stage renders per tier, Schreiber AI dark style, built with matplotlib
Poly3DCollection from the same layout engine the IFC drawings use (design/layout.py).

Run:  python design/renders/gen_renders.py [--tier ben20]
Output: design/renders/<tier>/stage-N.png (1600 px wide) and contact-sheet.png
"""
from __future__ import annotations

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import layout as L  # noqa: E402

BRAND = {"graphite": "#0B1018", "slate": "#152234", "panel": "#1B2B42", "text": "#EDF4FF", "muted": "#9FB3CC",
         "cyan": "#66E3FF", "amber": "#FFC66D", "red": "#FF707D", "green": "#6EE7A8", "purple": "#C7A6FF"}
KIND_COLOR = {"rack": BRAND["cyan"], "cooling": BRAND["green"], "power": BRAND["amber"], "controls": BRAND["purple"],
              "fire": BRAND["red"], "structure": BRAND["muted"], "tray": "#DCE6F2", "envelope": "#5C7391"}
STAGES = [
    (1, "Empty container", "Receiving inspection, shell survey, cutouts marked"),
    (2, "Insulation and liner", "100 mm PIR, vapour-tight liner, door seals"),
    (3, "Floor channel and cable tray", "C100 channels under the row, overhead trays, leak rope"),
    (4, "Racks", "Racks on channels, hold-downs torqued, rails plumb"),
    (5, "Containment and cooling units", "Hot-aisle containment, in-row / RDHx / CDU, condensers"),
    (6, "Power cabinets", "UPS, batteries, panels, service section (HOLD: electrician)"),
    (7, "Controls and sensors", "Nodes, gateway, probes at 0.4 / 1.2 / 1.8 m, dP, leak, door"),
    (8, "Complete unit", "Roof closed, brand panel, ready for pre-ship test"),
]


def cuboid(x0, y0, z0, x1, y1, z1):
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])
    faces = [[v[0], v[1], v[2], v[3]], [v[4], v[5], v[6], v[7]], [v[0], v[1], v[5], v[4]], [v[2], v[3], v[7], v[6]], [v[1], v[2], v[6], v[5]], [v[0], v[3], v[7], v[4]]]
    return faces


def add_box(ax, x0, y0, z0, x1, y1, z1, color, alpha=0.9, edge=None, lw=0.5, shade=True, zs=0):
    faces = cuboid(x0, y0, z0, x1, y1, z1)
    rgb = np.array(matplotlib.colors.to_rgb(color))
    cols = []
    for k in range(6):
        f = 1.0 if not shade else (0.55, 1.0, 0.75, 0.85, 0.95, 0.65)[k]
        cols.append((*np.clip(rgb * f, 0, 1), alpha))
    pc = Poly3DCollection(faces, facecolors=cols, edgecolors=edge or (0, 0, 0, 0), linewidths=lw)
    pc.set_sort_zpos(zs)
    ax.add_collection3d(pc)
    return pc


def add_lines(ax, segs, color, lw=0.6, alpha=1.0, ls="-"):
    lc = Line3DCollection(segs, colors=color, linewidths=lw, alpha=alpha, linestyles=ls)
    ax.add_collection3d(lc)


def stage_items(lay: L.Layout, n: int):
    """Items first appearing at stage n."""
    out = []
    for it in lay.items:
        k, m, t = it.kind, it.mount, it.tag
        s = None
        if t == "SKID":
            s = 1
        elif t in ("FC", "TR-D", "TR-P", "LEAK"):
            s = 3
        elif k == "rack":
            s = 4
        elif k == "cooling":
            s = 5
        elif k == "power":
            s = 6
        elif k == "controls" or k == "fire":
            s = 7
        if s is not None and s == n:
            out.append(it)
    return out


def draw_shell(ax, lay: L.Layout, stage: int):
    Lm, W, H = lay.L, lay.W, lay.H
    wall = (lay.ext_w - W) / 2
    endw = (lay.ext_l - Lm) / 2
    roof_t = lay.ext_h - H - 198 - 100 if lay.is_container else 60
    fl = 198 + 100 if lay.is_container else 60   # floor structure below finished floor
    shell = "#243752"
    # floor slab (structure)
    add_box(ax, -endw, -wall, -fl, Lm + endw, W + wall, 0, shell, alpha=0.95, edge="#3A5070", lw=0.4, zs=-10)
    # rack wall (y=0 side) and blind end wall (x=L) - always drawn (back of the scene)
    add_box(ax, -endw, -wall, 0, Lm + endw, 0, H, shell, alpha=0.85, edge="#3A5070", lw=0.4, zs=-9)
    add_box(ax, Lm, -wall, 0, Lm + endw, W + wall, H, shell, alpha=0.85, edge="#3A5070", lw=0.4, zs=-9)
    # corrugation lines on the rack wall
    segs = []
    pitch = 280 if lay.is_container else 150
    x = pitch / 2
    while x < Lm:
        segs.append([(x, -wall / 2, 0), (x, -wall / 2, H)]); x += pitch
    add_lines(ax, segs, "#3F5878", lw=0.5, alpha=0.8)
    if stage == 1 or stage == 8:
        # roof and front wall translucent, door-end wall with doors
        add_box(ax, -endw, -wall, H, Lm + endw, W + wall, H + roof_t, shell, alpha=0.35 if stage == 1 else 0.9, edge="#3A5070", lw=0.4, zs=20)
        add_box(ax, -endw, W, 0, Lm + endw, W + wall, H, shell, alpha=0.25 if stage == 1 else 0.9, edge="#3A5070", lw=0.4, zs=19)
        add_box(ax, -endw, -wall, 0, 0, W + wall, H, "#2E4461", alpha=0.6 if stage == 1 else 0.95, edge="#3A5070", lw=0.4, zs=19)
        if lay.is_container:
            # door split and lock bars on the door end
            add_lines(ax, [[(-endw - 1, W / 2, 100), (-endw - 1, W / 2, H - 100)]], BRAND["muted"], lw=1.0)
            for yy in (W * 0.3, W * 0.42, W * 0.58, W * 0.7):
                add_lines(ax, [[(-endw - 1, yy, 250), (-endw - 1, yy, H - 250)]], BRAND["muted"], lw=0.8)
    else:
        # roof as wireframe so the interior reads
        segs = [[(-endw, -wall, H + roof_t), (Lm + endw, -wall, H + roof_t)], [(-endw, W + wall, H + roof_t), (Lm + endw, W + wall, H + roof_t)],
                [(-endw, -wall, H + roof_t), (-endw, W + wall, H + roof_t)], [(Lm + endw, -wall, H + roof_t), (Lm + endw, W + wall, H + roof_t)],
                [(-endw, W + wall, 0), (-endw, W + wall, H + roof_t)], [(Lm + endw, W + wall, 0), (Lm + endw, W + wall, H + roof_t)],
                [(-endw, -wall, 0), (-endw, -wall, H + roof_t)]]
        add_lines(ax, segs, "#4A6487", lw=0.8, ls="--")
    # corner castings
    if lay.is_container:
        for (cx, cy) in ((-endw, -wall), (Lm + endw - 178, -wall), (-endw, W + wall - 162), (Lm + endw - 178, W + wall - 162)):
            add_box(ax, cx, cy, -fl, cx + 178, cy + 162, -fl + 118, "#8DA2BF", alpha=1, zs=-8)
            if stage in (1, 8):
                add_box(ax, cx, cy, H + roof_t - 118, cx + 178, cy + 162, H + roof_t, "#8DA2BF", alpha=1, zs=21)


def draw_envelope(ax, lay: L.Layout, highlight: bool):
    Lm, W, H = lay.L, lay.W, lay.H
    a = 0.95 if highlight else 0.5
    pir = "#D9B86A" if highlight else "#8A7A52"
    liner = "#D6E2F0" if highlight else "#6E7F96"
    t = 100 if lay.is_container else 40
    # PIR on rack wall and end wall (behind liner), liner shown on half the wall to reveal the build-up
    add_box(ax, 0, -t - 1, 0, Lm, -1, H, pir, alpha=a, zs=-5)
    add_box(ax, Lm + 1, 0, 0, Lm + t + 1, W, H, pir, alpha=a, zs=-5)
    add_box(ax, Lm * 0.45, -1, 0, Lm, 0, H, liner, alpha=a, edge="#9FB3CC", lw=0.4, zs=-4)
    add_box(ax, Lm, 0, 0, Lm + 1, W, H, liner, alpha=a, edge="#9FB3CC", lw=0.4, zs=-4)
    # floor build-up
    add_box(ax, 0, 0, -1, Lm, W, 0, liner if highlight else "#52627A", alpha=a, edge="#9FB3CC", lw=0.3, zs=-6)
    # ceiling liner (thin frame)
    add_lines(ax, [[(0, 0, H), (Lm, 0, H)], [(0, W, H), (Lm, W, H)], [(0, 0, H), (0, W, H)], [(Lm, 0, H), (Lm, W, H)]], liner, lw=0.8)


def draw_item(ax, it: L.Item, lay: L.Layout, highlight: bool):
    col = KIND_COLOR.get(it.kind, BRAND["muted"])
    a = 0.95 if highlight else 0.55
    edge = BRAND["text"] if highlight else (1, 1, 1, 0.15)
    if it.tag == "LEAK":
        Lm, W = lay.L, lay.W
        pts = [(100, 100, 15), (Lm - 100, 100, 15), (Lm - 100, W - 100, 15), (100, W - 100, 15), (100, 100, 15)]
        add_lines(ax, [list(zip(pts[:-1], pts[1:]))[i] for i in range(4)], BRAND["red"], lw=1.6 if highlight else 0.8, alpha=1 if highlight else 0.5)
        return
    if it.tag == "HAC":
        # containment: top panels over the plenum+rack top, from rack top to ceiling, translucent
        racks = lay.by_kind("rack")
        if racks:
            ztop = racks[0].z1
            add_box(ax, it.x0, 0, ztop, it.x1, lay.aisle_y0, lay.H, BRAND["green"], alpha=0.25 if highlight else 0.12, edge=BRAND["green"] if highlight else (0, 0, 0, 0), lw=0.5, zs=5)
            add_box(ax, it.x1, 0, 0, it.x1 + 10, lay.aisle_y0, lay.H, BRAND["green"], alpha=0.25 if highlight else 0.12, zs=5)
        return
    if it.kind == "tray":
        # hollow tray: two side rails + bottom
        add_box(ax, it.x0, it.y0, it.z0, it.x1, it.y0 + 15, it.z1, col, alpha=a, zs=8)
        add_box(ax, it.x0, it.y1 - 15, it.z0, it.x1, it.y1, it.z1, col, alpha=a, zs=8)
        add_box(ax, it.x0, it.y0, it.z0, it.x1, it.y1, it.z0 + 10, col, alpha=a * 0.8, zs=8)
        return
    if it.tag == "FC":
        racks = lay.by_kind("rack")
        r = racks[0]
        feet = (r.y0 + 100, r.y1 - 100) if lay.notes.get("plenum", 0) else (r.y0 + 300, r.y1 - 100)
        for yf in feet:
            add_box(ax, it.x0, yf - 50, 0, it.x1, yf + 50, 100 if False else 2, "#B8C6D8", alpha=a, edge=edge, lw=0.4, zs=-3)
            add_box(ax, it.x0, yf - 50, -2, it.x1, yf + 50, 0, "#B8C6D8", alpha=a, zs=-3)
        return
    if it.mount == "rack":
        add_box(ax, it.x0 + 40, it.y0 + 40, it.z0, it.x1 - 40, it.y1 - 40, it.z1, col, alpha=a, edge=edge, lw=0.4, zs=3)
        return
    zs = 2 if it.mount == "floor" else 6
    add_box(ax, it.x0, it.y0, it.z0, it.x1, it.y1, it.z1, col, alpha=a, edge=edge, lw=0.5 if highlight else 0.3, zs=zs)
    if it.kind == "rack" and lay.is_container:
        # door perforation hint: darker front panel
        add_box(ax, it.x0 + 20, it.y1 - 12, 60, it.x1 - 20, it.y1 + 2, it.z1 - 60, "#0B1018", alpha=0.35 if highlight else 0.2, zs=4)
        if lay.notes.get("cooling_resolved") == "rdhx_drycooler":
            add_box(ax, it.x0, it.y0, 0, it.x1, it.y0 + 200, it.z1, BRAND["green"], alpha=a * 0.8, zs=3)
    if highlight and it.mount in ("floor", "wall", "roof"):
        # install guide: vertical drop line above the item
        cx, cy = it.cx, it.cy
        add_lines(ax, [[(cx, cy, it.z1 + 150), (cx, cy, it.z1 + 650)]], BRAND["cyan"], lw=1.0, ls=":")
        ax.scatter([cx], [cy], [it.z1 + 650], color=BRAND["cyan"], s=12, depthshade=False)


def draw_sensors(ax, lay: L.Layout, highlight: bool):
    xs, ys, zs, cs = [], [], [], []
    for sn in lay.sensors:
        xs.append(sn.x); ys.append(sn.y); zs.append(sn.z)
        cs.append({"T": BRAND["cyan"], "RH": BRAND["purple"], "dP": BRAND["green"], "leak": BRAND["red"], "door": BRAND["text"], "kWh": BRAND["amber"]}[sn.kind])
    ax.scatter(xs, ys, zs, c=cs, s=14 if highlight else 6, depthshade=False, alpha=1 if highlight else 0.5, marker="^")


def render_stage(lay: L.Layout, n: int, out_png: str):
    Lm, W, H = lay.L, lay.W, lay.H
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor(BRAND["graphite"])
    ax = fig.add_axes([0.02, 0.0, 0.76, 1.0], projection="3d")
    ax.set_facecolor(BRAND["graphite"])
    ax.set_axis_off()
    draw_shell(ax, lay, n)
    if n >= 2:
        draw_envelope(ax, lay, highlight=(n == 2))
    for k in range(3, 8):
        if n >= k:
            for it in stage_items(lay, k):
                if n == 8 and it.mount in ("ext", "roof"):
                    draw_item(ax, it, lay, highlight=False)
                elif it.mount == "ext" and n < 8 and it.kind != "power":
                    continue   # dry cooler and exterior AC only in the complete view
                else:
                    draw_item(ax, it, lay, highlight=(n == k))
    if n >= 7:
        draw_sensors(ax, lay, highlight=(n == 7))
    if n == 8:
        # brand panel on the aisle-side wall (exterior) and door-end detail
        wall = (lay.ext_w - W) / 2
        pw = min(Lm * 0.45, 3000)
        add_box(ax, Lm / 2 - pw / 2, W + wall, H * 0.35, Lm / 2 + pw / 2, W + wall + 15, H * 0.65, "#0B1018", alpha=1, edge=BRAND["cyan"], lw=1.0, zs=30)
        ax.text(Lm / 2, W + wall + 40, H * 0.5, f"SCHREIBER AI  |  {lay.d['tier_label'].upper()}", color=BRAND["cyan"], fontsize=9 if lay.is_container else 6,
                ha="center", va="center", zdir="x", fontweight="bold")
    # camera & aspect
    ext = max(Lm + 1500, W + 2500, H + 1500)
    pad_x = 600 if lay.is_container else 300
    ax.set_xlim(-pad_x, Lm + pad_x * (3 if n == 8 and lay.find("DC1") else 1))
    ax.set_ylim(-800, W + 1200)
    ax.set_zlim(-300, H + 1000)
    xr = ax.get_xlim(); yr = ax.get_ylim(); zr = ax.get_zlim()
    ax.set_box_aspect((xr[1] - xr[0], yr[1] - yr[0], (zr[1] - zr[0]) * 1.0))
    ax.view_init(elev=24, azim=-128)
    ax.dist = 7.5 if hasattr(ax, "dist") else None
    # side panel text
    stage_no, title, sub = STAGES[n - 1]
    if not lay.is_container:
        sub = sub.replace("0.4 / 1.2 / 1.8 m", "0.3 / 0.7 / 1.1 m").replace("100 mm PIR", "40 mm PIR").replace("C100 channels under the row, overhead trays, leak rope", "Skid, rails, leak rope")
    fig.text(0.80, 0.90, "BEN Engine", color=BRAND["cyan"], fontsize=13, fontweight="bold")
    fig.text(0.80, 0.865, lay.d["tier_label"] + "  —  assembly sequence", color=BRAND["text"], fontsize=11)
    fig.text(0.80, 0.80, f"STAGE {stage_no} / 8", color=BRAND["amber"], fontsize=10, fontweight="bold")
    fig.text(0.80, 0.765, title, color=BRAND["text"], fontsize=15, fontweight="bold")
    import textwrap
    for i, ln in enumerate(textwrap.wrap(sub, 48)):
        fig.text(0.80, 0.735 - i * 0.025, ln, color=BRAND["muted"], fontsize=9)
    items = stage_items(lay, n) if n not in (1, 2, 8) else []
    y = 0.66
    fig.text(0.80, y, "Items in this stage", color=BRAND["muted"], fontsize=8); y -= 0.025
    seen = {}
    for it in items:
        key = it.label
        seen[key] = seen.get(key, 0) + 1
    if n == 1:
        seen = {lay.d["enclosure"]: 1, "Corner castings / CSC plate check": 1}
    if n == 2:
        seen = {"PIR insulation 100 mm (40 mm cabinet)": 1, "Steel liner, sealed joints": 1, "Floor build-up 100 mm": 1, "Door seals": 1}
    if n == 8:
        seen = {"Roof closed, penetrations sealed": 1, "Brand panel bonded + riveted": 1, "Exterior: service section, condensers / dry cooler": 1}
    for lab, cnt in list(seen.items())[:14]:
        fig.text(0.80, y, f"{cnt} x  {lab[:52]}", color=BRAND["text"], fontsize=8); y -= 0.022
    d = lay.d
    fig.text(0.80, 0.26, "Configuration", color=BRAND["muted"], fontsize=8)
    cfg_lines = [f"{lay.cfg.it_kw:.0f} kW IT in {lay.cfg.racks} racks ({d['per_rack_kw']} kW/rack)",
                 f"Cooling: {L.COOLING_LIBRARY[lay.notes.get('cooling_resolved', lay.cfg.cooling)]['label']}",
                 f"Power: {d['voltage']}, {d['service_breaker_a']} A, UPS {d['ups_modules']} x {d['ups_kva_each']} kVA",
                 f"Interior {Lm:.0f} x {W:.0f} x {H:.0f} mm, gross {d['gross_kg']} kg"]
    for i, ln in enumerate(cfg_lines):
        fig.text(0.80, 0.235 - i * 0.022, ln, color=BRAND["text"], fontsize=8)
    fig.text(0.80, 0.12, "Concept render — generated from configuration", color=BRAND["amber"], fontsize=8.5, fontweight="bold")
    fig.text(0.80, 0.095, "design/renders/gen_renders.py · not to scale · see IFC set A-001…C-001", color=BRAND["muted"], fontsize=7.5)
    fig.text(0.80, 0.05, "Schreiber AI", color=BRAND["cyan"], fontsize=9, fontweight="bold")
    fig.text(0.80, 0.03, "AI infrastructure that arrives finished.", color=BRAND["muted"], fontsize=7.5)
    # legend
    lx = 0.03
    for i, (k, lab) in enumerate([("rack", "Racks"), ("cooling", "Cooling"), ("power", "Power"), ("controls", "Controls"), ("fire", "Fire"), ("tray", "Tray / channel")]):
        fig.patches.append(plt.Rectangle((lx + i * 0.075, 0.035), 0.012, 0.02, transform=fig.transFigure, color=KIND_COLOR[k]))
        fig.text(lx + i * 0.075 + 0.016, 0.038, lab, color=BRAND["muted"], fontsize=8)
    fig.savefig(out_png, dpi=100, facecolor=BRAND["graphite"])
    plt.close(fig)


def contact_sheet(out_dir, lay):
    ims = [Image.open(os.path.join(out_dir, f"stage-{n}.png")) for n in range(1, 9)]
    w, h = ims[0].size
    cw = 1600; ch = int(cw / 4 * (h / w)) * 2 + 60
    sheet = Image.new("RGB", (cw, ch), BRAND["graphite"])
    tw = cw // 4; th = int(tw * h / w)
    for i, im in enumerate(ims):
        sheet.paste(im.resize((tw, th)), ((i % 4) * tw, 60 + (i // 4) * th))
    dr = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 22); f2 = ImageFont.truetype("DejaVuSans.ttf", 14)
    except Exception:
        f = f2 = ImageFont.load_default()
    dr.text((20, 14), f"BEN Engine — {lay.d['tier_label']} — assembly sequence contact sheet", fill=BRAND["cyan"], font=f)
    dr.text((20, 40), "Concept render — generated from configuration · Schreiber AI", fill=BRAND["muted"], font=f2)
    sheet.save(os.path.join(out_dir, "contact-sheet.png"))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=list(L.TIER_GEOMETRY), action="append")
    ap.add_argument("--stage", type=int, action="append")
    a = ap.parse_args(argv)
    for t in a.tier or list(L.TIER_GEOMETRY):
        lay = L.resolve(t)
        out = os.path.join(HERE, t)
        os.makedirs(out, exist_ok=True)
        for n in a.stage or range(1, 9):
            p = os.path.join(out, f"stage-{n}.png")
            render_stage(lay, n, p)
            print("  wrote", p)
        if not a.stage:
            contact_sheet(out, lay)
            print("  wrote", os.path.join(out, "contact-sheet.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
