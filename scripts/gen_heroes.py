"""Generate the product-page hero illustrations web/assets/hero-<tier>.svg from config.TIER_GEOMETRY.

One isometric SVG per tier (640 x 420), drawn from the real external dimensions so the five tiers read at the
right relative scale: the BEN 5 cabinet on a skid, the 10/20/40 ft ISO-frame modules, and the BEN 2000 hall as
three site-joined wide-body modules plus a power module block, pad-mount transformers, generators and adiabatic
dry coolers in a plant yard. Run after any geometry change: ``python scripts/gen_heroes.py``.
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "software"))
from ben_engine.config import TIER_GEOMETRY, Config  # noqa: E402

W, H = 640, 420
BG0, BG1 = "#152234", "#0B1018"
STROKE = "#27405f"
PAD = "#1B2B42"
SIDE, END, TOP = "#20334e", "#182a42", "#2a4060"
SIDE_L, END_L, TOP_L = "#33507a", "#2b4466", "#3d5f8f"
RIB = "#2f4a6e"
CYAN, AMBER, TEXT, MUTED = "#66E3FF", "#FFC66D", "#EDF4FF", "#9FB3CC"

COS30, SIN30 = math.cos(math.radians(30)), 0.5


def iso(x: float, y: float, z: float, scale: float, ox: float, oy: float):
    """World (x along length, y across width, z up) -> screen. Isometric, x to the right-down, y to the left-down."""
    sx = ox + (x - y) * COS30 * scale
    sy = oy + (x + y) * SIN30 * scale - z * scale
    return sx, sy


def poly(pts, fill, stroke=STROKE, sw=1.2, opacity=1.0, extra=""):
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}" {extra}/>'


class Canvas:
    def __init__(self, scale: float, ox: float, oy: float):
        self.scale, self.ox, self.oy = scale, ox, oy
        self.out: list[str] = []

    def P(self, x, y, z):
        return iso(x, y, z, self.scale, self.ox, self.oy)

    def box(self, x0, y0, z0, lx, ly, lz, side=SIDE, end=END, top=TOP, ribs=0.0, rib_color=RIB, sw=1.2):
        """Axis-aligned box: visible faces are the +y side (front-left), the +x end (front-right) and the top."""
        P = self.P
        # front-left face: y = y0 + ly (faces the viewer at lower-left)
        self.out.append(poly([P(x0, y0 + ly, z0), P(x0 + lx, y0 + ly, z0), P(x0 + lx, y0 + ly, z0 + lz), P(x0, y0 + ly, z0 + lz)], side, sw=sw))
        # front-right face: x = x0 + lx
        self.out.append(poly([P(x0 + lx, y0, z0), P(x0 + lx, y0 + ly, z0), P(x0 + lx, y0 + ly, z0 + lz), P(x0 + lx, y0, z0 + lz)], end, sw=sw))
        # top
        self.out.append(poly([P(x0, y0, z0 + lz), P(x0 + lx, y0, z0 + lz), P(x0 + lx, y0 + ly, z0 + lz), P(x0, y0 + ly, z0 + lz)], top, sw=sw))
        if ribs > 0:
            n = int(lx / ribs)
            for i in range(1, n):
                x = x0 + i * ribs
                a, b = P(x, y0 + ly, z0 + 0.05 * lz), P(x, y0 + ly, z0 + 0.95 * lz)
                self.out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{rib_color}" stroke-width="1"/>')

    def slab(self, x0, y0, lx, ly, fill=PAD, opacity=1.0):
        P = self.P
        self.out.append(poly([P(x0, y0, 0), P(x0 + lx, y0, 0), P(x0 + lx, y0 + ly, 0), P(x0, y0 + ly, 0)], fill, opacity=opacity))

    def ring(self, x, y, z, r, color=CYAN, sw=1.5):
        cx, cy = self.P(x, y, z)
        self.out.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r * self.scale:.1f}" ry="{r * self.scale * 0.58:.1f}" fill="none" stroke="{color}" stroke-width="{sw}"/>')

    def door(self, x, y0, ly, z0, lz, color=END_L):
        """Door leaves on the +x end face."""
        P = self.P
        half = ly / 2
        for k in (0, 1):
            ya = y0 + k * half
            self.out.append(poly([P(x, ya + 0.04, z0 + 0.05), P(x, ya + half - 0.04, z0 + 0.05), P(x, ya + half - 0.04, z0 + lz - 0.1), P(x, ya + 0.04, z0 + lz - 0.1)], color, sw=1))
        a, b = P(x, y0 + half, z0 + 0.3), P(x, y0 + half, z0 + lz - 0.3)
        self.out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{AMBER}" stroke-width="1.5"/>')

    def brand(self, x, y, z, size, label, sub):
        """Brand text skewed onto the +y face (front-left) at world point (x, y, z)."""
        sx, sy = self.P(x, y, z)
        return (f'<g transform="translate({sx:.1f},{sy:.1f}) skewY(30) scale(1,0.866)">'
                f'<text x="0" y="0" font-family="Inter,Segoe UI,system-ui,sans-serif" font-weight="800" font-size="{size}" fill="{TEXT}" letter-spacing="2">BEN <tspan fill="{CYAN}" font-weight="300">Engine</tspan></text>'
                f'<text x="0" y="{size * 0.9:.0f}" font-family="Inter,Segoe UI,system-ui,sans-serif" font-size="{max(7, size * 0.43):.0f}" fill="{MUTED}" letter-spacing="3">{sub}</text></g>')


def draw_module(c: Canvas, x0, y0, L, Wd, Hh, label, brand_size, dry_coolers=0, door=True, ribs=0.25):
    c.slab(x0 - 0.5, y0 - 0.5, L + 1.0, Wd + 1.0)
    c.box(x0, y0, 0, L, Wd, Hh, ribs=ribs)
    # corner castings and roof rail
    for cx in (x0, x0 + L - 0.18):
        for cy in (y0, y0 + Wd - 0.16):
            c.box(cx, cy, Hh - 0.12, 0.18, 0.16, 0.12, side="#3a4a60", end="#2a3850", top="#4a5c74", sw=0.6)
    if door:
        c.door(x0 + L, y0, Wd, 0, Hh)
    for i in range(dry_coolers):
        bx = x0 + 0.4 + i * (min(2.2, (L - 0.6) / max(1, dry_coolers) - 0.2) + 0.2)
        bw = min(2.2, (L - 0.6) / max(1, dry_coolers) - 0.2)
        c.box(bx, y0 + 0.3, Hh, bw, Wd - 0.6, 0.75, side=SIDE_L, end=END_L, top=TOP_L)
        nf = max(1, round(bw / 0.9))
        for f in range(nf):
            c.ring(bx + (f + 0.5) * bw / nf, y0 + Wd / 2, Hh + 0.78, min(0.38, (Wd - 0.6) / 2 - 0.1))
    c.out.append(c.brand(x0 + 0.3, y0 + Wd, Hh * 0.62, brand_size, label, f"SCHREIBER AI · {label}"))


def hero_cabinet(g):
    c = Canvas(scale=95, ox=300, oy=215)
    L, Wd, Hh = g["ext_l_m"], g["ext_w_m"], g["ext_h_m"]
    c.slab(-0.9, -0.9, L + 1.8, Wd + 1.8)
    # skid rails
    for ry in (0.0, Wd - 0.12):
        c.box(-0.15, ry, 0, L + 0.3, 0.12, 0.1, side="#3a4a60", end="#2a3850", top="#4a5c74", sw=0.6)
    c.box(0, 0, 0.1, L, Wd, Hh - 0.1, side="#7f8ea3", end="#6b7a90", top="#98a7bc", ribs=0)
    # side DX unit on the +y face
    c.box(0.15, Wd, 0.35, 0.42, 0.26, Hh * 0.6, side=SIDE_L, end=END_L, top=TOP_L, sw=0.8)
    c.ring(0.36, Wd + 0.27, 0.35 + Hh * 0.45, 0.13)
    # door with handle on +x end
    c.door(L, 0, Wd, 0.1, Hh - 0.1, color="#5f6f86")
    # status lamp
    cx, cy = c.P(L, Wd * 0.5, Hh - 0.25)
    c.out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="#6EE7A8"/>')
    c.out.append(c.brand(0.1, Wd, Hh * 0.9, 13, g["label"], f"SCHREIBER AI · {g['label']}"))
    return c


def hero_module(g):
    L, Wd, Hh = g["ext_l_m"], g["ext_w_m"], g["ext_h_m"]
    scale = min(28.0, 520 / ((L + Wd + 2) * COS30))
    c = Canvas(scale=scale, ox=W / 2 - (L - Wd) * COS30 * scale / 2 + 20, oy=H / 2 + 40 - ((L + Wd) * SIN30 * scale) / 2)
    n_dc = 0 if g["default_cooling"].startswith("inrow") or g["default_cooling"] == "cabinet_dx" else (2 if L < 8 else 3)
    draw_module(c, 0, 0, L, Wd, Hh, g["label"], 28 if L > 5 else 18, dry_coolers=n_dc)
    if g["default_cooling"].startswith("inrow"):
        # roof condensers for the DX tiers
        for i in range(2 if L > 4 else 1):
            bx = 0.5 + i * 1.4
            c.box(bx, 0.6, Hh, 1.0, Wd - 1.2, 0.5, side=SIDE_L, end=END_L, top=TOP_L)
            c.ring(bx + 0.5, Wd / 2, Hh + 0.52, 0.32)
    # utility pedestal
    c.box(-1.4, Wd - 0.6, 0, 0.5, 0.5, 1.1, side="#3b4656", end="#2d3745", top="#4a5667", sw=0.8)
    return c


def hero_hall(g, d):
    """BEN 2000: three joined wide-body modules (hall), a power module block, MV transformers, generators and dry coolers in a yard."""
    L, Wd, Hh = g["ext_l_m"], g["ext_w_m"], g["ext_h_m"]
    modules = g["modules"]
    yard_y = Wd + 4.0
    total_x, total_y = L + 22, yard_y + 3.5
    scale = min(9.0, 600 / ((total_x + total_y) * COS30))
    c = Canvas(scale=scale, ox=W / 2 + 60, oy=H / 2 + 20 - ((total_x + total_y) * SIN30 * scale) / 2 + 40)
    # slab-on-grade for everything
    c.slab(-17, -3.0, L + 20, yard_y + 6.5, fill="#16213a")
    # plant yard fence (north yard: generators), MV yard west
    # hall: three modules with visible seams
    mod_l = L / modules
    for m in range(modules):
        c.box(m * mod_l, 0, 0, mod_l, Wd, Hh, ribs=0.6)
    for m in range(1, modules):
        x = m * mod_l
        a, b = c.P(x, Wd, 0), c.P(x, Wd, Hh)
        c.out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#101a2a" stroke-width="2.4"/>')
        a, b = c.P(x, 0, Hh), c.P(x, Wd, Hh)
        c.out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#101a2a" stroke-width="2.4"/>')
    # roof parapet
    c.box(-0.05, -0.05, Hh, L + 0.1, 0.12, 0.1, side="#3a4a60", end="#2a3850", top="#4a5c74", sw=0.5)
    c.box(-0.05, Wd - 0.07, Hh, L + 0.1, 0.12, 0.1, side="#3a4a60", end="#2a3850", top="#4a5c74", sw=0.5)
    # service vestibule + doors at the +x end
    c.box(L, Wd * 0.3, 0, 2.4, 3.0, 3.0, side=SIDE_L, end=END_L, top=TOP_L)
    c.door(L + 2.4, Wd * 0.3, 3.0, 0, 3.0)
    # power module block west of the hall (long axis along y)
    pm_x0, pm_l, pm_w = -2.6 - 3.66, 3.66, 12.2
    c.box(pm_x0, (Wd - pm_w) / 2, 0, pm_l, pm_w, Hh, side="#243a5a", end="#1b2f4c", top="#2f4a6e", ribs=0.6)
    # transformers (2N pad-mounts) in the fenced MV yard
    n_x = max(2, d["transformers_total"])
    for t in range(n_x):
        ty = (Wd - pm_w) / 2 + 1.5 + t * (pm_w - 4.0) / max(1, n_x - 1)
        c.box(pm_x0 - 5.2, ty, 0, 2.4, 2.2, 2.0, side="#3b4656", end="#2d3745", top="#4a5667", sw=0.8)
        c.box(pm_x0 - 5.8, ty + 0.1, 0.2, 0.5, 2.0, 1.6, side="#2d3745", end="#222b37", top="#3b4656", sw=0.6)
    # fence around the MV yard
    fx0, fy0, fl, fw = pm_x0 - 6.4, (Wd - pm_w) / 2 - 0.6, 5.5, pm_w + 1.2
    for (ax, ay, bx, by) in ((fx0, fy0, fx0 + fl, fy0), (fx0, fy0 + fw, fx0 + fl, fy0 + fw), (fx0, fy0, fx0, fy0 + fw)):
        a, b = c.P(ax, ay, 0), c.P(bx, by, 0)
        c.out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#5a6a80" stroke-width="1" stroke-dasharray="3 3"/>')
        a2, b2 = c.P(ax, ay, 2.4), c.P(bx, by, 2.4)
        c.out.append(f'<line x1="{a2[0]:.1f}" y1="{a2[1]:.1f}" x2="{b2[0]:.1f}" y2="{b2[1]:.1f}" stroke="#5a6a80" stroke-width="1" stroke-dasharray="3 3"/>')
    # generators (N+1) in the north yard (negative y is "behind" the hall in this projection, so put them at -y)
    for k in range(d["generators_total"]):
        gx = 3.0 + k * 7.5
        c.box(gx, -3.0 - 2.4, 0, 6.0, 2.4, 3.0, side="#3b4656", end="#2d3745", top="#4a5667", sw=0.8)
        c.box(gx + 4.6, -3.0 - 2.3, 0.4, 1.4, 2.2, 1.2, side="#5b6878", end="#4a5667", top="#6b7a90", sw=0.6)
        cx, cy = c.P(gx + 1.2, -3.0 - 1.2, 3.0)
        c.out.append(f'<rect x="{cx - 2:.1f}" y="{cy - 12:.1f}" width="4" height="12" fill="#3a4a60"/>')
    # adiabatic dry coolers in the south plant yard (+y side), on grade
    n_dc = d["cooling_units_total"]
    for i in range(n_dc):
        dx0 = 1.0 + i * (6.0 + 0.8) * (L - 2.0) / max(1.0, n_dc * 6.8)
        dl = min(6.0, (L - 2.0) / n_dc - 0.8)
        c.box(dx0, yard_y, 0.1, dl, 2.4, 2.4, side=SIDE_L, end=END_L, top=TOP_L, sw=0.8)
        # wetted pads
        c.out.append(poly([c.P(dx0 + 0.2, yard_y + 2.4, 0.5), c.P(dx0 + dl - 0.2, yard_y + 2.4, 0.5), c.P(dx0 + dl - 0.2, yard_y + 2.4, 2.1), c.P(dx0 + 0.2, yard_y + 2.4, 2.1)], CYAN, stroke="none", opacity=0.22))
        for f in range(4):
            c.ring(dx0 + (f + 0.5) * dl / 4, yard_y + 1.2, 2.55, 0.5, sw=1.2)
    # glycol headers between yard and hall
    for off, col in ((0.0, "#3fc0e0"), (0.5, "#e0a44a")):
        a, b = c.P(L + 0.6 + off, Wd, 0.35), c.P(L + 0.6 + off, yard_y + 1.0, 0.35)
        c.out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col}" stroke-width="2"/>')
    # brand on the hall's south face
    c.out.append(c.brand(1.0, Wd, Hh * 0.68, 30, g["label"], f"SCHREIBER AI · {g['label']} · {modules} MODULES · POWER MODULE · PLANT YARD"))
    return c


def render(tier: str) -> str:
    g = TIER_GEOMETRY[tier]
    d = Config.preset(tier).derived()
    if g["kind"] == "cabinet":
        c = hero_cabinet(g)
    elif g["kind"] == "hall":
        c = hero_hall(g, d)
    else:
        c = hero_module(g)
    rng = f"{g['it_kw_min']:,}–{g['it_kw_max']:,} kW IT"
    body = "\n".join(c.out)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{g["label"]} isometric illustration">\n'
            f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient></defs>\n'
            f'<rect width="{W}" height="{H}" fill="url(#bg)"/>\n{body}\n'
            f'<circle cx="600" cy="40" r="6" fill="{AMBER}"/><text x="590" y="44" text-anchor="end" font-family="Inter,system-ui,sans-serif" font-size="12" fill="{MUTED}">{g["label"]} · {rng}</text>\n'
            f'<text x="590" y="60" text-anchor="end" font-family="Inter,system-ui,sans-serif" font-size="10" fill="{MUTED}">{g["enclosure"][:70]}</text>\n</svg>\n')


def main(argv=None) -> int:
    out_dir = os.path.join(ROOT, "web", "assets")
    for tier in TIER_GEOMETRY:
        path = os.path.join(out_dir, f"hero-{tier}.svg")
        with open(path, "w") as f:
            f.write(render(tier))
        print(f"wrote {os.path.relpath(path, ROOT)} ({os.path.getsize(path)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
