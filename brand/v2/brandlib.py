"""Shared helpers for Schreiber AI brand v2 production files (BEN Engine Rev 2).

* ``Outliner``  — set text in the brand TTFs and return it as outlined SVG paths (sign shops,
  engravers and vinyl cutters must never depend on installed fonts).
* ``embed``     — place a logo master from brand/v2/ (never redrawn) with its ids prefixed so
  several masters can live in one file.
* ``qr_group``  — real QR code (segno, error correction M, square modules, 4-module quiet zone).
* ``band``      — the data plate band: rivet · fields with dividers · rivet, optional QR plate.

Requires: fontTools (+ brotli only if reading WOFF2), segno (``pip install segno``).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

BRAND = Path(__file__).resolve().parent
REPO = BRAND.parent.parent
TOK = json.loads((BRAND / "tokens.json").read_text(encoding="utf-8"))
TTF = BRAND / "fonts" / "ttf"


def tok(path: str) -> str:
    node = TOK
    for k in path.split("."):
        node = node[k]
    return node["value"] if isinstance(node, dict) else node


C = {
    "night": tok("color.surface.s0"), "s1": tok("color.surface.s1"), "s2": tok("color.surface.s2"),
    "s3": tok("color.surface.s3"), "border": tok("color.surface.border"),
    "signal": tok("color.signal.400"), "deep": tok("color.signal.700"), "cobalt": tok("color.signal.600"),
    "amber": tok("color.amber.base"), "shop": tok("color.light.shop_white"), "paper": tok("color.light.paper"),
    "ink": tok("color.text.ink"), "slate": tok("color.text.slate"), "fog": tok("color.text.fog"), "steel": tok("color.text.steel"),
    "run": tok("color.status.run"), "hold": tok("color.status.hold"), "stop": tok("color.status.stop"),
    "stop_light": tok("color.status.stop_light"), "info": tok("color.status.info"),
}

FONT_FILES = {
    "black125": "Archivo-Black-Expanded125.ttf",      # Display: Archivo 900 wdth 125
    "xbold125": "Archivo-ExtraBold-Expanded125.ttf",  # H1 / wordmark style: Archivo 800 wdth 125
    "bold": "Archivo-Bold.ttf",                       # H2: Archivo 700 wdth 100
    "xbold": "Archivo-ExtraBold.ttf",
    "sans": "IBMPlexSans-Regular.ttf", "sans_med": "IBMPlexSans-Medium.ttf",
    "sans_semi": "IBMPlexSans-SemiBold.ttf", "sans_bold": "IBMPlexSans-Bold.ttf",
    "mono": "IBMPlexMono-Regular.ttf", "mono_med": "IBMPlexMono-Medium.ttf", "mono_semi": "IBMPlexMono-SemiBold.ttf",
}
GREEK = {"regular": "IBMPlexSans-Greek-Regular.ttf", "semi": "IBMPlexSans-Greek-SemiBold.ttf"}


@lru_cache(maxsize=None)
def _font(fname: str):
    f = TTFont(str(TTF / fname))
    return f, f.getGlyphSet(), f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm


class Outliner:
    """Outlined text in a brand face. Sizes are the em size in the caller's units (mm, px ...)."""

    def __init__(self, face: str):
        self.face = face
        self.main = _font(FONT_FILES[face])
        greek = GREEK["semi"] if face in ("mono_semi", "sans_semi", "sans_bold", "black125", "xbold125", "bold", "xbold") else GREEK["regular"]
        self.fallback = _font(greek)

    def cap_height(self, size: float) -> float:
        f = self.main[0]
        return f["OS/2"].sCapHeight / self.main[4] * size

    def size_for_cap(self, cap: float) -> float:
        f = self.main[0]
        return cap * self.main[4] / f["OS/2"].sCapHeight

    def _glyph(self, ch: str):
        for font in (self.main, self.fallback):
            name = font[2].get(ord(ch))
            if name:
                return font, name
        font = self.main
        return font, font[2].get(ord("?"))

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        w = 0.0
        for i, ch in enumerate(text):
            font, name = self._glyph(ch)
            w += font[3][name][0] / font[4] * size
            if i < len(text) - 1:
                w += tracking * size
        return w

    def path(self, text: str, size: float, x: float, y: float, tracking: float = 0.0, anchor: str = "start") -> Tuple[str, float]:
        """Return (svg path d, advance width) with the baseline at y."""
        w = self.width(text, size, tracking)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        ds: List[str] = []
        pen_x = x
        for ch in text:
            font, name = self._glyph(ch)
            s = size / font[4]
            if ch != " ":
                sp = SVGPathPen(font[1], ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
                tp = TransformPen(sp, (s, 0, 0, -s, pen_x, y))
                font[1][name].draw(tp)
                d = sp.getCommands()
                if d:
                    ds.append(d)
            pen_x += font[3][name][0] * s + tracking * size
        return " ".join(ds), w

    def svg(self, text: str, size: float, x: float, y: float, fill: str, tracking: float = 0.0, anchor: str = "start", label: Optional[str] = None) -> str:
        d, _ = self.path(text, size, x, y, tracking, anchor)
        aria = f' aria-label="{_esc(label or text)}"'
        return f'<path{aria} fill="{fill}" d="{d}"/>'


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# --------------------------------------------------------------------------- logo masters
@lru_cache(maxsize=None)
def _master(name: str) -> Tuple[Tuple[float, float, float, float], str]:
    s = (BRAND / f"{name}.svg").read_text(encoding="utf-8")
    vb = tuple(float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).split())
    inner = re.sub(r"^\s*<svg[^>]*>", "", s, count=1, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
    return vb, inner  # type: ignore[return-value]


def master_aspect(name: str) -> float:
    vb, _ = _master(name)
    return vb[2] / vb[3]


def embed(name: str, x: float, y: float, height: float, prefix: str, extra_style: str = "") -> str:
    """Place a brand/v2 master (e.g. 'lockup-deep', 'stack-white', 'mark-signal') with its top-left at x,y."""
    vb, inner = _master(name)
    ids = set(re.findall(r'id="([^"]+)"', inner))
    for i in sorted(ids, key=len, reverse=True):
        inner = re.sub(rf'id="{re.escape(i)}"', f'id="{prefix}{i}"', inner)
        inner = re.sub(rf'(href|xlink:href)="#{re.escape(i)}"', rf'\1="#{prefix}{i}"', inner)
        inner = inner.replace(f"url(#{i})", f"url(#{prefix}{i})")
    s = height / vb[3]
    return (f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.5f}) translate({-vb[0]} {-vb[1]})" '
            f'data-master="brand/v2/{name}.svg"{extra_style}>{inner}</g>')


# --------------------------------------------------------------------------- QR
def qr_matrix(data: str) -> List[List[bool]]:
    import segno  # pure python; pip install segno
    q = segno.make(data, error="m", micro=False, boost_error=False)
    return [[bool(v) for v in row] for row in q.matrix]


def qr_group(data: str, x: float, y: float, code_w: float, dark: str, light: Optional[str] = None, quiet: int = 4) -> Tuple[str, float]:
    """QR with square modules; code_w is the width of the code WITHOUT the quiet zone.
    Returns (svg, total width including the quiet zone). The quiet zone is painted ``light`` if given."""
    m = qr_matrix(data)
    n = len(m)
    mod = code_w / n
    total = code_w + 2 * quiet * mod
    parts = []
    if light:
        parts.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{total:.3f}" height="{total:.3f}" fill="{light}"/>')
    d = []
    ox, oy = x + quiet * mod, y + quiet * mod
    for r, row in enumerate(m):
        c = 0
        while c < n:
            if row[c]:
                start = c
                while c < n and row[c]:
                    c += 1
                d.append(f"M{ox + start * mod:.3f} {oy + r * mod:.3f}h{(c - start) * mod:.3f}v{mod:.3f}h{-(c - start) * mod:.3f}z")
            else:
                c += 1
    parts.append(f'<path fill="{dark}" shape-rendering="crispEdges" d="{"".join(d)}"/>')
    return f'<g data-qr="{_esc(data)}" data-ec="M" data-quiet-zone="{quiet}">' + "".join(parts) + "</g>", total


# --------------------------------------------------------------------------- data plate band
def caps_keep_units(s: str) -> str:
    """Upper-case for the band, but keep SI unit case (kW, kV, kVA) readable and correct."""
    out = s.upper()
    for u in ("KW", "KVA", "KV"):
        out = re.sub(rf"(?<=\d )({u})\b", {"KW": "kW", "KVA": "kVA", "KV": "kV"}[u], out)
    return out.replace("Φ", "φ")


def band(x: float, y: float, w: float, h: float, fields: Sequence[str], *, ground: str, text: str, lead: str,
         rule: str, rivet_ring: str, rivet_fill: str, qr_url: Optional[str] = None, qr_code_w: float = 0.0,
         rows: int = 1, max_font: Optional[float] = None, tracking: float = 0.16, face: str = "mono_semi",
         plate_color: Optional[str] = None, qr_dark: Optional[str] = None) -> str:
    """Data plate band. fields[0] is the lead (set in ``lead`` color). ``rows`` = 1 or 2 (small items)."""
    o = Outliner(face)
    parts = [f'<g data-role="data-plate-band"><rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{ground}"/>',
             f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h * 0.012 + 0.2:.2f}" fill="{rule}"/>',
             f'<rect x="{x:.2f}" y="{y + h - (h * 0.012 + 0.2):.2f}" width="{w:.2f}" height="{h * 0.012 + 0.2:.2f}" fill="{rule}"/>']
    fs = max_font or (h / 2.6 if rows == 1 else h / 4.4)
    pad = fs * 1.2
    rv = fs * 0.7
    # QR plate at the right end
    right = x + w - pad
    if qr_url:
        qsvg, total = qr_group(qr_url, 0, 0, qr_code_w, qr_dark or C["night"], plate_color or C["shop"])
        qy = y + (h - total) / 2
        qx = right - total
        parts.append(f'<g transform="translate({qx:.3f} {qy:.3f})">{qsvg}</g>')
        right = qx - pad
    # rivets
    cyc = y + h / 2
    parts.append(f'<circle cx="{x + pad + rv / 2:.2f}" cy="{cyc:.2f}" r="{rv / 2:.2f}" fill="{rivet_fill}" stroke="{rivet_ring}" stroke-width="{max(rv * 0.14, 0.15):.2f}"/>')
    parts.append(f'<circle cx="{right - rv / 2:.2f}" cy="{cyc:.2f}" r="{rv / 2:.2f}" fill="{rivet_fill}" stroke="{rivet_ring}" stroke-width="{max(rv * 0.14, 0.15):.2f}"/>')
    tx0, tx1 = x + pad + rv + fs * 1.0, right - rv - fs * 1.0
    avail = tx1 - tx0
    fields = [caps_keep_units(f) for f in fields]
    gap = 1.6  # em between field and divider (package: gap 1.6em)
    rows_f: List[List[str]] = [list(fields)] if rows == 1 else [list(fields[: (len(fields) + 1) // 2]), list(fields[(len(fields) + 1) // 2:])]

    def row_w(r: List[str], size: float) -> float:
        return sum(o.width(f, size, tracking) for f in r) + (len(r) - 1) * (2 * gap * size)

    need = max(row_w(r, 1.0) for r in rows_f)
    size = min(fs, avail / need)
    line_h = h / rows
    for ri, r in enumerate(rows_f):
        base = y + line_h * ri + line_h / 2 + o.cap_height(size) / 2
        # spread the row across the available width: fixed gaps, last field right-aligned like .grow
        cx = tx0
        extra = (avail - row_w(r, size)) if len(r) > 1 else 0
        for i, f in enumerate(r):
            color = lead if (ri == 0 and i == 0) else text
            d, wf = o.path(f, size, cx, base, tracking)
            parts.append(f'<path aria-label="{_esc(f)}" fill="{color}" d="{d}"/>')
            cx += wf
            if i < len(r) - 1:
                stretch = extra / (len(r) - 1)
                mid = cx + gap * size + stretch / 2
                parts.append(f'<rect x="{mid - max(size * 0.03, 0.12):.2f}" y="{base - size * 0.78:.2f}" width="{max(size * 0.06, 0.25):.2f}" height="{size * 0.95:.2f}" fill="{rule}"/>')
                cx += 2 * gap * size + stretch
    parts.append("</g>")
    return "".join(parts)


def plate_fields(tier_label: str, serial: str, rated_kw: str, voltage: str, ip: str, rev: str = "Rev 2") -> List[str]:
    return ["Schreiber AI", "BEN Engine", tier_label, f"S/N {serial}", f"Rated {rated_kw} kW IT", voltage, ip, rev]


def svg_doc(w: float, h: float, body: Iterable[str], unit: str = "mm", title: str = "", desc: str = "", scale_px: Optional[float] = None) -> str:
    wa = f"{w:.2f}{unit}" if unit else f"{w * (scale_px or 1):.0f}"
    ha = f"{h:.2f}{unit}" if unit else f"{h * (scale_px or 1):.0f}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{wa}" height="{ha}" '
            f'viewBox="0 0 {w:.2f} {h:.2f}" role="img" aria-label="{_esc(title)}">'
            f"<title>{_esc(title)}</title><desc>{_esc(desc)}</desc>" + "".join(body) + "</svg>\n")
