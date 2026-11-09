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
from ben_engine.config import TIER_GEOMETRY, TIERS_BY_LINEUP, Config  # noqa: E402

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
    # world extents: x from the MV yard (-17) to the vestibule (L + 3), y from the generators (-5.5) to the dry coolers (yard_y + 3)
    xmin, xmax, ymin, ymax = -17.0, L + 3.0, -5.5, yard_y + 3.0
    scale = min(8.0, (W - 40) / ((xmax - xmin + ymax - ymin) * COS30))
    # screen x spans (xmin - ymax) .. (xmax - ymin); centre it, and centre the vertical extent too
    sx_min, sx_max = (xmin - ymax) * COS30 * scale, (xmax - ymin) * COS30 * scale
    sy_min, sy_max = (xmin + ymin) * SIN30 * scale - Hh * scale, (xmax + ymax) * SIN30 * scale
    c = Canvas(scale=scale, ox=W / 2 - (sx_min + sx_max) / 2, oy=H / 2 - (sy_min + sy_max) / 2 + 24)
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
        c.box(gx, -2.0 - 2.4, 0, 6.0, 2.4, 3.0, side="#3b4656", end="#2d3745", top="#4a5667", sw=0.8)
        c.box(gx + 4.6, -2.0 - 2.3, 0.4, 1.4, 2.2, 1.2, side="#5b6878", end="#4a5667", top="#6b7a90", sw=0.6)
        cx, cy = c.P(gx + 1.2, -2.0 - 1.2, 3.0)
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
    c.out.append(c.brand(1.0, Wd, Hh * 0.7, 20, g["label"], f"SCHREIBER AI · {g['label']} · {modules} MODULES"))
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


# ====================================================================== Rev 2 heroes (web/assets/rev2/hero-<tier>.svg), brand v2 livery
# Rev 1 palette -> brand v2 livery (Shop White body, Night Navy ground and band, Signal Blue accents; thermal ramp for heat only).
V2_MAP = {
    BG0: "#0B1A31", BG1: "#06101F", PAD: "#0F2342", "#16213a": "#0F2342", STROKE: "#8EA7C8",
    SIDE: "#F4F7FB", END: "#DCE4EF", TOP: "#E8EEF6", RIB: "#C8D3E2",
    SIDE_L: "#B9C6D8", END_L: "#9FB0C8", TOP_L: "#CBD6E4",
    "#243a5a": "#E6ECF4", "#1b2f4c": "#D3DCE8", "#2f4a6e": "#EEF2F8",
    "#7f8ea3": "#F4F7FB", "#6b7a90": "#DCE4EF", "#98a7bc": "#E8EEF6", "#5f6f86": "#C8D3E2",
    "#3a4a60": "#6B7F99", "#2a3850": "#58708E", "#4a5c74": "#8EA7C8",
    "#3b4656": "#5D6B7E", "#2d3745": "#4A5668", "#4a5667": "#738196", "#5b6878": "#7C8BA0", "#222b37": "#3E495A",
    CYAN: "#4C9DFF", AMBER: "#4C9DFF", MUTED: "#B2C1D8", TEXT: "#EEF4FC", "#6EE7A8": "#2BB673",
    "#3fc0e0": "#5CD6FF", "#e0a44a": "#FF8A3D",
}
THERMAL = ("#5CD6FF", "#7FE3D2", "#C9E89A", "#FFB86B", "#FF8A3D")


def _recolor(svg: str) -> str:
    import re as _re
    keys = sorted(V2_MAP, key=len, reverse=True)
    pat = _re.compile("|".join(_re.escape(k) for k in keys), _re.I)
    low = {k.lower(): v for k, v in V2_MAP.items()}
    return pat.sub(lambda m: low[m.group(0).lower()], svg)


def _brandlib():
    sys.path.insert(0, os.path.join(ROOT, "brand", "v2"))
    import brandlib
    return brandlib


def _face_group(c: "Canvas", x, y, z, inner: str, clip=None) -> str:
    """Group skewed onto the +y face (front-left) at world point (x, y, z): local u along +x, v downward.

    One metre along x is c.scale * COS30 local u units (skewY(30) keeps u as the screen x offset), one metre
    up is c.scale / COS30 local v units (the 0.866 vertical scale). ``clip`` = (u0, v0, u1, v1) in local units
    keeps everything inside the face, so no lettering can ever run past the box edge.
    """
    sx, sy = c.P(x, y, z)
    if clip:
        _face_group.n += 1
        cid = f"fc{_face_group.n}"
        u0, v0, u1, v1 = clip
        inner = (f'<clipPath id="{cid}"><rect x="{u0:.1f}" y="{v0:.1f}" width="{u1 - u0:.1f}" height="{v1 - v0:.1f}"/></clipPath>'
                 f'<g clip-path="url(#{cid})">{inner}</g>')
    return f'<g transform="translate({sx:.1f},{sy:.1f}) skewY(30) scale(1,0.866)">{inner}</g>'


_face_group.n = 0
MONO_EM = 0.62      # IBM Plex Mono advance (0.6 em) plus a margin for the monospace fallback
CAPS_EM = 0.78      # Archivo / Inter heavy caps, widest of the fallbacks


def _mono_w(text: str, fs: float, ls: float) -> float:
    return len(text) * (fs * MONO_EM + ls)


def _fit_band(fields, avail, fs_max, fs_min=3.6, drop=(3, 1)):
    """Font size and the fields that fit ``avail`` local units: shrink first, then drop the optional fields
    (rated, then BEN ENGINE) like the .opt cells of the web data plate band. Returns (fs, ls, gap, fields)."""
    fields = list(fields)
    order = list(drop)
    while True:
        fs = fs_max
        while fs >= fs_min:
            ls, gap = fs * 0.16, fs * 1.6
            need = sum(_mono_w(f, fs, ls) for f in fields) + gap * (len(fields) - 1) + fs * 2.4
            if need <= avail:
                return fs, ls, gap, fields
            fs -= 0.2
        if not order:
            return fs_min, fs_min * 0.16, fs_min * 1.6, fields[:1]
        i = order.pop(0)
        fields = [f for j, f in enumerate(fields) if j != i] if i < len(fields) else fields
        order = [j - (1 if j > i else 0) for j in order]


def _band_parts(fields, u0, avail, bh, fs_max, ground, lead="#4C9DFF", text="#B2C1D8"):
    fs, ls, gap, fields = _fit_band(fields, avail, fs_max)
    parts = [f'<rect x="{u0:.1f}" y="{-bh:.1f}" width="{avail:.1f}" height="{bh:.1f}" fill="{ground}" stroke="#24406B" stroke-width="0.6"/>']
    ux = u0 + fs * 1.2
    for i, f in enumerate(fields):
        parts.append(f'<text x="{ux:.1f}" y="{-bh / 2 + fs * 0.36:.1f}" font-family="IBM Plex Mono,monospace" font-weight="600" font-size="{fs:.1f}" letter-spacing="{ls:.2f}" fill="{lead if i == 0 else text}">{f}</text>')
        ux += _mono_w(f, fs, ls) + gap
    return parts


def livery_side(c: "Canvas", x0, y0, L, Wd, Hh, label, rated, mark="mark-deep", band_frac=0.066, outdoor=True):
    """Data plate band along the bottom of the +y face, v2 mark, product line and tier number (brand/v2/livery side art)."""
    bl = _brandlib()
    ku = c.scale * COS30          # local u units per metre along x on the skewed face
    kv = c.scale / COS30          # local v units per metre up the face
    u_len, v_len = L * ku, Hh * kv
    clip = (0.0, -v_len, u_len, 0.0)        # the whole face, origin at the bottom-left corner
    bh = max(Hh * band_frac * kv, 7.0)
    band_ground = "#06101F" if outdoor else "#0F2342"
    z_band = 0.18 if outdoor else 0.02
    fields = ["SCHREIBER AI", "BEN ENGINE", label.upper(), rated, "REV 2"]
    parts = _band_parts(fields, 0.04 * u_len, 0.92 * u_len, bh, max(4.2, min(7.0, bh * 0.52)), band_ground)
    vb = z_band * kv
    face = [f'<g transform="translate(0,{-vb:.1f})">{"".join(parts)}</g>']
    ink = "#0B1A31" if outdoor else "#EEF4FC"
    sub = "#4A5D7A" if outdoor else "#B2C1D8"
    # lockup top-left: mark + SCHREIBER AI / BEN ENGINE, no wider than 46 % of the face
    lock_em = 1.28 + len("SCHREIBER AI") * 0.36 * CAPS_EM + 0.36 * 0.6 / 34 * 12
    mh = min(Hh * 0.30 * kv, 34, 0.46 * u_len / lock_em)
    vl = 0.93 * v_len - mh       # baseline of the lockup row: its top sits 7 % below the roof edge
    face.append(f'<g transform="translate({0.06 * u_len:.1f},{-vl:.1f})">' + bl.embed(mark, 0, -mh, mh, prefix=f"hm{abs(hash(label)) % 997}_") +
                f'<text x="{mh * 1.28:.1f}" y="{-mh * 0.52:.1f}" font-family="Archivo,Inter,system-ui,sans-serif" font-weight="800" font-size="{mh * 0.36:.1f}" letter-spacing="0.6" fill="{ink}">SCHREIBER AI</text>'
                f'<text x="{mh * 1.28:.1f}" y="{-mh * 0.08:.1f}" font-family="Archivo,Inter,system-ui,sans-serif" font-weight="700" font-size="{mh * 0.24:.1f}" letter-spacing="1.2" fill="{sub}">BEN ENGINE</text></g>')
    # tier number right-aligned on the face, no wider than 40 % of it
    tsize = min(Hh * 0.22 * kv, 30, 0.40 * u_len / (len(label) * CAPS_EM))
    face.append(f'<text x="{0.94 * u_len:.1f}" y="{-Hh * 0.42 * kv:.1f}" text-anchor="end" font-family="Archivo,Inter,system-ui,sans-serif" font-weight="900" font-size="{tsize:.1f}" fill="{ink}">{label.upper()}</text>')
    return _face_group(c, x0, y0 + Wd, 0.0, "".join(face), clip=clip)


def heat_plume(c: "Canvas", x, y, z, h=1.6, w=0.5):
    """Warm-air cue above a fan: thermal ramp, never amber."""
    gid = f"th{int(x * 100)}{int(y * 100)}"
    a, b = c.P(x, y, z), c.P(x, y, z + h)
    return (f'<defs><linearGradient id="{gid}" x1="0" y1="1" x2="0" y2="0">' + "".join(f'<stop offset="{i / 4:.2f}" stop-color="{col}" stop-opacity="{0.55 - i * 0.1:.2f}"/>' for i, col in enumerate(THERMAL)) +
            f'</linearGradient></defs><path d="M{a[0] - w * c.scale:.1f},{a[1]:.1f} Q{a[0]:.1f},{(a[1] + b[1]) / 2:.1f} {a[0] - w * c.scale * 0.3:.1f},{b[1]:.1f} L{a[0] + w * c.scale * 0.3:.1f},{b[1]:.1f} Q{a[0]:.1f},{(a[1] + b[1]) / 2:.1f} {a[0] + w * c.scale:.1f},{a[1]:.1f} Z" fill="url(#{gid})"/>')


def hero_v2_module(g, d, cfg):
    L, Wd, Hh = g["ext_l_m"], g["ext_w_m"], g["ext_h_m"]
    dense = bool(g.get("liquid_first"))
    skid_l = (2.6 if cfg.it_kw <= 300 else 5.0) if dense else 0.0
    span = L + (skid_l + 1.2 if dense else 0)
    scale = min(28.0, 520 / ((span + Wd + 2) * COS30))
    while True:                  # fit between the header (y 72) and the bottom edge, roof to skid pad
        c = Canvas(scale=scale, ox=W / 2 - (span - Wd) * COS30 * scale / 2 + 20, oy=H / 2 + 40 - ((span + Wd) * SIN30 * scale) / 2)
        top = min(c.P(0, 0, Hh)[1], c.P(0, Wd, Hh)[1])
        if top < 72:
            c.oy += 72 - top
        bottom = c.P(span + 0.5, Wd + 0.6, 0)[1]
        if bottom <= H - 10:
            break
        scale *= 0.96
    n_dc = 0 if (dense or g["default_cooling"].startswith("inrow") or g["default_cooling"] == "cabinet_dx") else (2 if L < 8 else 3)
    Canvas.brand = lambda self, *a, **k: ""
    draw_module(c, 0, 0, L, Wd, Hh, g["label"], 0, dry_coolers=n_dc)
    if g["default_cooling"].startswith("inrow"):
        for i in range(2 if L > 4 else 1):
            bx = 0.5 + i * 1.4
            c.box(bx, 0.6, Hh, 1.0, Wd - 1.2, 0.5, side=SIDE_L, end=END_L, top=TOP_L)
            c.ring(bx + 0.5, Wd / 2, Hh + 0.52, 0.32)
    extra = []
    if dense:
        # adjacent heat-rejection skid at the blind end: W45 dry coolers + 18 C trim chiller, pipes to the end wall
        sx0 = L + 1.2
        c.slab(sx0 - 0.3, -0.5, skid_l + 0.6, Wd + 1.0)
        c.box(sx0, 0, 0, skid_l, Wd, 0.25, side="#6B7F99", end="#58708E", top="#8EA7C8", sw=0.6)
        n_fan = max(2, round(skid_l / 1.2))
        c.box(sx0, 0.1, 0.25, skid_l, Wd - 0.2, 1.7, side=SIDE_L, end=END_L, top=TOP_L, sw=0.8)
        for f in range(n_fan):
            fx = sx0 + (f + 0.5) * skid_l / n_fan
            c.ring(fx, Wd * 0.33, 1.97, min(0.42, skid_l / n_fan / 2 - 0.08))
            c.ring(fx, Wd * 0.72, 1.97, min(0.42, skid_l / n_fan / 2 - 0.08))
        c.box(sx0 + skid_l - 1.1, Wd - 0.05, 0.25, 1.0, 0.7, 1.1, side="#CBD6E4", end="#B9C6D8", top="#DCE4EF", sw=0.8)
        for k2, col in enumerate(("#5CD6FF", "#FF8A3D")):
            a, b = c.P(L, Wd * (0.35 + 0.15 * k2), 0.5), c.P(sx0, Wd * (0.35 + 0.15 * k2), 0.5)
            c.out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{col}" stroke-width="2.4"/>')
        for f in range(n_fan):
            extra.append(heat_plume(c, sx0 + (f + 0.5) * skid_l / n_fan, Wd * 0.5, 2.05, h=1.4, w=0.35))
    else:
        for i in range(n_dc):
            bw = min(2.2, (L - 0.6) / max(1, n_dc) - 0.2)
            bx = 0.4 + i * (bw + 0.2)
            extra.append(heat_plume(c, bx + bw / 2, Wd / 2, Hh + 0.8, h=1.3, w=0.4))
    c.box(-1.4, Wd - 0.6, 0, 0.5, 0.5, 1.1, side="#3b4656", end="#2d3745", top="#4a5667", sw=0.8)
    svg_body = _recolor("\n".join(c.out)) + "\n" + "\n".join(extra)
    svg_body += "\n" + livery_side(c, 0, 0, L, Wd, Hh, g["label"], f"RATED {cfg.it_kw:g} kW IT")
    return svg_body


def hero_v2_cabinet(g, d, cfg):
    Canvas.brand = lambda self, *a, **k: ""
    c = hero_cabinet(g)
    L, Wd, Hh = g["ext_l_m"], g["ext_w_m"], g["ext_h_m"]
    body = _recolor("\n".join(c.out))
    return body + "\n" + livery_side(c, 0, 0, L, Wd, Hh, g["label"], f"RATED {cfg.it_kw:g} kW IT", band_frac=0.08)


def hero_v2_hall(g, d, cfg):
    Canvas.brand = lambda self, *a, **k: ""
    c = hero_hall(g, d)
    L, Wd, Hh = g["ext_l_m"], g["ext_w_m"], g["ext_h_m"]
    body = _recolor("\n".join(c.out))
    plumes = [heat_plume(c, 1.0 + i * (L - 2.0) / max(1, d["cooling_units_total"]) + 2.0, Wd + 5.2, 2.6, h=3.0, w=1.2) for i in range(d["cooling_units_total"])]
    return body + "\n" + "\n".join(plumes) + "\n" + livery_side(c, 0, 0, L, Wd, Hh, g["label"], f"RATED {cfg.it_kw:g} kW IT")


def hero_v2_ben1(g, d, cfg):
    """BEN 1: the 12U sound-damped office cabinet (Night Navy, S2 band) on a desk, with a small screen for scale."""
    fm = g["forms"]["cab12"]
    L, Wd, Hh = fm["ext_l_m"], fm["ext_w_m"], fm["ext_h_m"]
    desk_l, desk_w, desk_h = 1.6, 1.0, 0.74
    c = Canvas(scale=128, ox=W / 2 - 30, oy=172)
    bl = _brandlib()
    # floor
    c.slab(-0.4, -0.3, desk_l + 0.9, desk_w + 0.7, fill="#0F2342")
    # desk legs + top
    for (lx, ly) in ((0.05, 0.05), (desk_l - 0.1, 0.05), (0.05, desk_w - 0.1), (desk_l - 0.1, desk_w - 0.1)):
        c.box(lx, ly, 0, 0.05, 0.05, desk_h - 0.04, side="#8EA7C8", end="#6B7F99", top="#B2C1D8", sw=0.5)
    c.box(0, 0, desk_h - 0.04, desk_l, desk_w, 0.04, side="#B2C1D8", end="#8EA7C8", top="#DCE4EF", sw=0.6)
    z0 = desk_h
    # monitor and keyboard for scale (left part of the desk)
    c.box(0.15, 0.15, z0, 0.55, 0.02, 0.34, side="#16305A", end="#0F2342", top="#24406B", sw=0.5)
    c.box(0.2, 0.55, z0, 0.42, 0.14, 0.015, side="#24406B", end="#16305A", top="#4A5D7A", sw=0.4)
    # the cabinet (Night Navy), door on the +y face (front-left)
    cx0, cy0 = desk_l - L - 0.05, desk_w - Wd * 0.62 - 0.02
    sc = 0.62   # the 952 mm deep cabinet is drawn on a deep credenza; depth shown reduced so it reads on a desk
    c.box(cx0, cy0, z0, L, Wd * sc, Hh, side="#0F2342", end="#0B1A31", top="#16305A", sw=1.0)
    P = c.P
    yf = cy0 + Wd * sc
    c.out.append(poly([P(cx0 + 0.03, yf, z0 + 0.05), P(cx0 + L - 0.03, yf, z0 + 0.05), P(cx0 + L - 0.03, yf, z0 + Hh - 0.04), P(cx0 + 0.03, yf, z0 + Hh - 0.04)], "#06101F", stroke="#24406B", sw=1))
    for i in range(7):   # door perforation / sound-damped intake slots
        zz = z0 + 0.18 + i * 0.05
        a, b = P(cx0 + 0.12, yf, zz), P(cx0 + L - 0.12, yf, zz)
        c.out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#16305A" stroke-width="2"/>')
    # band (S2) and the signal mark on the door
    ku, kv = c.scale * COS30, c.scale / COS30
    u_len, v_len = L * ku, Hh * kv
    bh = 0.07 * kv
    fields = ["SCHREIBER AI", "BEN ENGINE", "BEN 1", "120 V", "REV 2"]
    door = [f'<g transform="translate(0,{-0.06 * kv:.1f})">' + "".join(_band_parts(fields, 0.02 * u_len, 0.96 * u_len, bh, 5.4, "#0F2342", text="#B2C1D8")) + '</g>']
    lock_em = 1.25 + len("SCHREIBER AI") * 0.3 * CAPS_EM
    mh = min(0.16 * kv, 0.84 * u_len / lock_em)
    door.append(f'<g transform="translate({0.08 * u_len:.1f},{-(Hh - 0.08) * kv:.1f})">' + bl.embed("mark-signal", 0, 0, mh, prefix="b1m_") +
                f'<text x="{mh * 1.25:.1f}" y="{mh * 0.45:.1f}" font-family="Archivo,Inter,system-ui,sans-serif" font-weight="800" font-size="{mh * 0.3:.1f}" fill="#EEF4FC">SCHREIBER AI</text>'
                f'<text x="{mh * 1.25:.1f}" y="{mh * 0.82:.1f}" font-family="Archivo,Inter,system-ui,sans-serif" font-weight="700" font-size="{mh * 0.2:.1f}" fill="#B2C1D8" letter-spacing="1">BEN ENGINE</text></g>')
    tsize = min(0.1 * kv, 0.6 * u_len / (5 * CAPS_EM))
    door.append(f'<text x="{0.08 * u_len:.1f}" y="{-Hh * 0.42 * kv:.1f}" font-family="Archivo,Inter,system-ui,sans-serif" font-weight="900" font-size="{tsize:.1f}" fill="#EEF4FC">BEN 1</text>')
    c.out.append(_face_group(c, cx0, yf, z0, "".join(door), clip=(0.0, -v_len, u_len, 0.0)))
    # status lamp (Run) and a warm exhaust cue at the rear top
    sx, sy = P(cx0 + L - 0.06, yf, z0 + Hh - 0.07)
    c.out.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3" fill="#2BB673"/>')
    c.out.append(heat_plume(c, cx0 + L * 0.5, cy0, z0 + Hh, h=0.35, w=0.12))
    # wall outlet + cord
    a = P(desk_l + 0.25, 0.02, 0.35)
    c.out.append(f'<rect x="{a[0] - 5:.1f}" y="{a[1] - 7:.1f}" width="10" height="14" rx="2" fill="#B2C1D8" stroke="#8EA7C8"/>')
    return "\n".join(c.out)


def _wrap(text: str, width: int) -> list:
    """Word-wrap the caption so it stays right of the header lockup (x >= 300 at 10 px) and is never cut."""
    lines, cur = [], ""
    for w_ in text.split():
        if cur and len(cur) + 1 + len(w_) > width:
            lines.append(cur)
            cur = w_
        else:
            cur = f"{cur} {w_}".strip()
    return lines + ([cur] if cur else [])


def render_v2(tier: str) -> str:
    g = TIER_GEOMETRY[tier]
    cfg = Config.preset(tier, lineup="rev2")
    d = cfg.derived()
    if g["kind"] == "minirack":
        body = hero_v2_ben1(g, d, cfg)
    elif g["kind"] == "cabinet":
        body = hero_v2_cabinet(g, d, cfg)
    elif g["kind"] == "hall":
        body = hero_v2_hall(g, d, cfg)
    else:
        body = hero_v2_module(g, d, cfg)
    bl = _brandlib()
    rng = f"{g['it_kw_min']:,}–{g['it_kw_max']:,} kW IT".replace(".0", "")
    sub_lines = _wrap(g["enclosure"], 52)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{g["label"]} — BEN Engine, by Schreiber AI, Rev 2 illustration">\n'
            f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0B1A31"/><stop offset="1" stop-color="#06101F"/></linearGradient></defs>\n'
            f'<rect width="{W}" height="{H}" fill="url(#bg)"/>\n{body}\n'
            + bl.embed("mark-signal", 24, 22, 26, prefix="hdr_") +
            f'\n<text x="58" y="34" font-family="IBM Plex Mono,monospace" font-weight="600" font-size="10" letter-spacing="1.6" fill="#4C9DFF">SCHREIBER AI</text>'
            f'<text x="58" y="47" font-family="IBM Plex Mono,monospace" font-size="9" letter-spacing="1.4" fill="#B2C1D8">BEN ENGINE · REV 2</text>\n'
            f'<text x="616" y="34" text-anchor="end" font-family="IBM Plex Sans,Inter,system-ui,sans-serif" font-weight="600" font-size="13" fill="#EEF4FC">{g["label"]} · {rng}</text>\n'
            + "".join(f'<text x="616" y="{50 + 13 * i}" text-anchor="end" font-family="IBM Plex Sans,Inter,system-ui,sans-serif" font-size="10" fill="#B2C1D8">{ln}</text>\n' for i, ln in enumerate(sub_lines))
            + '</svg>\n')


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--lineup" in argv and argv[argv.index("--lineup") + 1] == "rev2":
        out_dir = os.path.join(ROOT, "web", "assets", "rev2")
        os.makedirs(out_dir, exist_ok=True)
        for tier in TIERS_BY_LINEUP["rev2"]:
            path = os.path.join(out_dir, f"hero-{tier}.svg")
            with open(path, "w") as f:
                f.write(render_v2(tier))
            print(f"wrote {os.path.relpath(path, ROOT)} ({os.path.getsize(path)} bytes)")
        return 0
    out_dir = os.path.join(ROOT, "web", "assets")
    for tier in TIERS_BY_LINEUP["rev1"]:
        path = os.path.join(out_dir, f"hero-{tier}.svg")
        with open(path, "w") as f:
            f.write(render(tier))
        print(f"wrote {os.path.relpath(path, ROOT)} ({os.path.getsize(path)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
