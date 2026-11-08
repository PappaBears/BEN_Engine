"""Minimal 2-D drafting kit on top of matplotlib for BEN Engine IFC sheets.

Sheet coordinates are millimetres on an A1 landscape sheet (841 x 594). A `View` maps
model millimetres at a given scale to a region of the sheet. Output is SVG (vector)
and PNG from the same figure.
"""
from __future__ import annotations

import math
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, FancyArrowPatch, PathPatch
from matplotlib.path import Path
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from revision import REV  # noqa: E402  (design/REVISION.json — one revision for the whole set)

# Deterministic SVG output (audit F-21): fixed hash salt for clip-path ids, no <dc:date> in the metadata.
plt.rcParams["svg.hashsalt"] = "ben-engine"

SHEET_W, SHEET_H = 841.0, 594.0
MARGIN = 10.0

INK = "#0B1018"
MUTED = "#5C7391"
LIGHT = "#9FB3CC"
PAPER = "#FFFFFF"
CTQ_C = "#0B8FA8"     # teal for CTQ bubbles (brand cyan darkened for print)
CTP_C = "#B8860B"     # amber darkened
RED = "#C8102E"
GREEN = "#1E8E5A"
PURPLE = "#6B4FBB"
FILL = {
    "rack": "#D6F5FC", "cooling": "#DDF7EA", "power": "#FFF0D1", "controls": "#EDE4FF",
    "fire": "#FFE1E4", "structure": "#E8EDF3", "envelope": "#E3E8EF", "tray": "#F4F7FB",
}
EDGE = {
    "rack": "#0B8FA8", "cooling": "#1E8E5A", "power": "#B8860B", "controls": "#6B4FBB",
    "fire": "#C8102E", "structure": "#5C7391", "envelope": "#5C7391", "tray": "#5C7391",
}
FONT = "DejaVu Sans"
MONO = "DejaVu Sans Mono"


def pt(mm):  # text height in mm -> font size in points (sheet is 1 mm = 1 unit, 1 pt = 0.3528 mm)
    return mm / 0.3528


class Sheet:
    def __init__(self, dwg_no, title, tier_label, scale_text, sheet_n, sheet_total, config_line, date=None, rev=None):
        self.fig = plt.figure(figsize=(SHEET_W / 25.4, SHEET_H / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, SHEET_W); self.ax.set_ylim(0, SHEET_H)
        self.ax.set_aspect("equal"); self.ax.axis("off")
        self.fig.patch.set_facecolor(PAPER)
        self.dwg_no, self.title, self.tier_label = dwg_no, title, tier_label
        self.scale_text, self.sheet_n, self.sheet_total = scale_text, sheet_n, sheet_total
        self.config_line = config_line
        self.date = date or REV["issue_date"]
        self.rev = rev or REV["drawing_rev"]
        self._border()

    # ------------------------------------------------------------ primitives
    def rect(self, x, y, w, h, fc="none", ec=INK, lw=0.5, ls="-", z=2, hatch=None, alpha=1.0):
        self.ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, lw=lw, ls=ls, zorder=z, hatch=hatch, alpha=alpha))

    def line(self, x0, y0, x1, y1, c=INK, lw=0.5, ls="-", z=2, alpha=1.0):
        self.ax.add_line(Line2D([x0, x1], [y0, y1], color=c, lw=lw, ls=ls, zorder=z, alpha=alpha))

    def poly(self, pts, fc="none", ec=INK, lw=0.5, z=2, ls="-", closed=True, hatch=None, alpha=1.0):
        self.ax.add_patch(Polygon(pts, closed=closed, facecolor=fc, edgecolor=ec, lw=lw, ls=ls, zorder=z, hatch=hatch, alpha=alpha))

    def circle(self, x, y, r, fc="none", ec=INK, lw=0.5, z=3):
        self.ax.add_patch(Circle((x, y), r, facecolor=fc, edgecolor=ec, lw=lw, zorder=z))

    def text(self, x, y, s, h=2.5, c=INK, ha="left", va="baseline", rot=0, bold=False, mono=False, z=5, bg=None):
        kw = {}
        if bg:
            kw["bbox"] = dict(boxstyle="square,pad=0.15", fc=bg, ec="none")
        self.ax.text(x, y, s, fontsize=pt(h), color=c, ha=ha, va=va, rotation=rot, family=MONO if mono else FONT,
                     fontweight="bold" if bold else "normal", zorder=z, **kw)

    def arrow(self, x0, y0, x1, y1, c=INK, lw=0.6, z=4, style="-|>", ms=6):
        self.ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=ms, color=c, lw=lw, zorder=z))

    # ------------------------------------------------------------ dimensions (sheet mm, label value given)
    def dim_h(self, x0, x1, y, label, off=0, h=2.2, c=INK, ext_from=None):
        """Horizontal dimension line at sheet y; extension lines from ext_from (y of the object)."""
        if ext_from is not None:
            for x in (x0, x1):
                self.line(x, ext_from, x, y + (1.5 if y > ext_from else -1.5), c=c, lw=0.3)
        self.line(x0, y, x1, y, c=c, lw=0.4)
        for x in (x0, x1):   # oblique ticks (architectural)
            self.line(x - 1, y - 1, x + 1, y + 1, c=c, lw=0.8)
        self.text((x0 + x1) / 2, y + 1.0 + off, label, h=h, c=c, ha="center", va="bottom")

    def dim_v(self, y0, y1, x, label, off=0, h=2.2, c=INK, ext_from=None, side="left"):
        if ext_from is not None:
            for y in (y0, y1):
                self.line(ext_from, y, x + (1.5 if x > ext_from else -1.5), y, c=c, lw=0.3)
        self.line(x, y0, x, y1, c=c, lw=0.4)
        for y in (y0, y1):
            self.line(x - 1, y - 1, x + 1, y + 1, c=c, lw=0.8)
        dx = -1.0 - off if side == "left" else 1.0 + off
        self.text(x + dx, (y0 + y1) / 2, label, h=h, c=c, ha="center", va="bottom" if side == "left" else "top", rot=90)

    # ------------------------------------------------------------ annotation
    def leader(self, x0, y0, x1, y1, s, h=2.2, c=INK, ha="left", bold=False):
        self.line(x0, y0, x1, y1, c=c, lw=0.35)
        self.circle(x0, y0, 0.5, fc=c, ec=c)
        self.text(x1 + (0.8 if ha == "left" else -0.8), y1, s, h=h, c=c, ha=ha, va="center", bold=bold)

    def bubble(self, x, y, label, kind="CTQ", r=3.2):
        c = CTQ_C if kind == "CTQ" else CTP_C
        self.circle(x, y, r, fc=PAPER, ec=c, lw=0.9, z=6)
        self.text(x, y, label, h=1.9, c=c, ha="center", va="center", bold=True, z=7)

    def view_title(self, x, y, title, scale):
        self.text(x, y, title, h=4, bold=True)
        self.text(x, y - 4.5, f"SCALE {scale}", h=2.5, c=MUTED)
        self.line(x, y - 1.2, x + 4.5 * len(title) * 0.62, y - 1.2, lw=0.8)

    def north_arrow(self, x, y, label="SITE NORTH: PER SITE PLAN"):
        self.circle(x, y, 7, lw=0.5)
        self.poly([(x, y + 6), (x - 2.5, y - 3), (x, y - 1), (x + 2.5, y - 3)], fc=INK, ec=INK)
        self.text(x, y + 8, "N", h=3.5, ha="center", va="bottom", bold=True)
        self.text(x, y - 9, label, h=1.8, ha="center", va="top", c=MUTED)

    def notes(self, x, y, title, lines, w=320, h=2.3, lead=3.4):
        self.text(x, y, title, h=3, bold=True)
        yy = y - 5
        maxch = int(w / (h * 0.5))
        for i, ln in enumerate(lines):
            parts = _wrap(f"{i+1}. {ln}", maxch)
            for k, ptxt in enumerate(parts):
                self.text(x + (0 if k == 0 else 4), yy, ptxt, h=h)
                yy -= lead * 0.85 if k < len(parts) - 1 else lead
        return yy

    def table(self, x, y, cols, rows, widths, h=2.1, rowh=4.2, header_fc="#E8EDF3", title=None, wrap=None):
        """Simple grid table. widths in mm per column. Returns bottom y."""
        if title:
            self.text(x, y + 1.5, title, h=3, bold=True)
        total = sum(widths)
        yy = y
        self.rect(x, yy - rowh, total, rowh, fc=header_fc, lw=0.5)
        xx = x
        for c, w in zip(cols, widths):
            self.text(xx + 1.2, yy - rowh + 1.3, c, h=h, bold=True)
            xx += w
        yy -= rowh
        for r in rows:
            # wrap long cells
            cells = []
            maxlines = 1
            for c, w in zip(r, widths):
                s = str(c)
                maxch = max(4, int(w / (h * 0.52)))
                lines = _wrap(s, maxch)
                cells.append(lines); maxlines = max(maxlines, len(lines))
            rh = rowh * (0.55 + 0.45 * maxlines) if maxlines > 1 else rowh
            self.rect(x, yy - rh, total, rh, lw=0.4)
            xx = x
            for lines, w in zip(cells, widths):
                for k, ln in enumerate(lines):
                    self.text(xx + 1.2, yy - 1.0 - (k + 1) * h * 1.25 + h * 0.3, ln, h=h, va="baseline")
                self.line(xx, yy, xx, yy - rh, lw=0.3)
                xx += w
            yy -= rh
        return yy

    # ------------------------------------------------------------ frame
    def _border(self):
        self.rect(MARGIN, MARGIN, SHEET_W - 2 * MARGIN, SHEET_H - 2 * MARGIN, lw=1.2)
        # grid reference letters/numbers
        for i in range(8):
            x = MARGIN + (SHEET_W - 2 * MARGIN) * (i + 0.5) / 8
            self.text(x, SHEET_H - MARGIN + 1.5, str(i + 1), h=2.2, c=MUTED, ha="center")
            self.text(x, MARGIN - 4, str(i + 1), h=2.2, c=MUTED, ha="center")
        for i in range(6):
            y = MARGIN + (SHEET_H - 2 * MARGIN) * (i + 0.5) / 6
            self.text(MARGIN - 3, y, "FEDCBA"[i], h=2.2, c=MUTED, ha="center", va="center")
            self.text(SHEET_W - MARGIN + 3, y, "FEDCBA"[i], h=2.2, c=MUTED, ha="center", va="center")

    def title_block(self, status=None, rev=None):
        """Title block. Status and revision come from design/REVISION.json unless overridden:
        while REVISION.json has no checker the sheet says ISSUED FOR REVIEW; with a named checker it says ISSUE FOR CONSTRUCTION."""
        status = status or REV["status_long"]
        rev = rev or self.rev
        w, h = 260, 58
        x, y = SHEET_W - MARGIN - w, MARGIN
        self.rect(x, y, w, h, fc=PAPER, lw=1.0, z=8)
        # brand panel
        self.rect(x, y, 62, h, fc="#0B1018", ec="#0B1018", z=9)
        self.rect(x + 6, y + h - 22, 16, 16, fc="#152234", ec="#66E3FF", lw=0.8, z=10)
        self.text(x + 14, y + h - 14, "SAI", h=4, c="#66E3FF", ha="center", va="center", bold=True, z=11)
        self.text(x + 26, y + h - 10, "Schreiber AI", h=3.6, c="#EDF4FF", bold=True, z=11)
        self.text(x + 26, y + h - 16, "BEN Engine", h=3.0, c="#66E3FF", z=11)
        self.text(x + 6, y + h - 30, self.tier_label.upper(), h=4.2, c="#EDF4FF", bold=True, z=11)
        st_lines = _wrap(status, 40)[:2]
        for k, ln in enumerate(st_lines):
            self.text(x + 6, y + 14 - k * 3.2, ln, h=2.6 if k == 0 else 1.9, c="#FFC66D", bold=(k == 0), z=11)
        self.text(x + 6, y + 5.5, f"Rev {rev}   {self.date}", h=2.4, c="#9FB3CC", z=11)
        # fields
        fx = x + 62
        self.line(fx, y + h - 20, x + w, y + h - 20, lw=0.5, z=10)
        self.line(fx, y + 20, x + w, y + 20, lw=0.5, z=10)
        self.text(fx + 3, y + h - 5, "TITLE", h=1.8, c=MUTED, z=11)
        self.text(fx + 3, y + h - 15, self.title, h=4.0, bold=True, z=11)
        cols = [("DRAWING No.", self.dwg_no, 48), ("REV", rev, 16), ("SCALE", self.scale_text, 40), ("SHEET", f"{self.sheet_n} / {self.sheet_total}", 26),
                ("DATE", self.date, 34), ("STATUS", REV["status_short"], 32)]
        xx = fx
        for lab, val, cw in cols:
            self.line(xx, y + 20, xx, y + h - 20, lw=0.4, z=10)
            self.text(xx + 2, y + h - 25, lab, h=1.8, c=MUTED, z=11)
            self.text(xx + 2, y + 24, val, h=3.2 if len(val) < 14 else 2.4, bold=True, z=11)
            xx += cw
        self.text(fx + 3, y + 14, "DRAWN: BEN Engine generator (design/drawings/gen_drawings.py)", h=2.1, z=11)
        self.text(fx + 3, y + 9.5, f"CHECKED: {REV['checker_text']}   APPROVED: ____________________", h=2.1, z=11)
        self.text(fx + 3, y + 4.5, f"CONFIG: {self.config_line}", h=1.9, c=MUTED, mono=True, z=11)

    def revision_table(self, x, y, w=None):
        """Revision history (design/REVISION.json): current issue plus the superseded one. Returns bottom y."""
        w = w or 326.0
        rows = []
        sup = REV.get("supersedes")
        if sup:
            rows.append([sup["drawing_rev"], sup["issue_date"], sup["notes"], "—"])
        rows.append([REV["drawing_rev"], REV["issue_date"], f"{REV['status_title']}. {REV['notes_short']}", REV["checker"].strip() or "not checked"])
        return self.table(x, y, ["REV", "DATE", "DESCRIPTION", "CHECKED"], rows, [w * 0.07, w * 0.13, w * 0.62, w * 0.18], h=1.9, rowh=4.0,
                          title="REVISIONS (design/REVISION.json)")

    def ctq_table(self, items, x, y, w=330):
        """CTQ / CTP table at (x, y top). Returns bottom y."""
        rows = []
        for it in items:
            flag = f" [{it.point}]" if it.point else ""
            rows.append([it.id, it.kind, it.item + flag, it.method, it.criterion, it.form])
        widths = [16, 10, w * 0.30, w * 0.22, w * 0.33, 14]
        s = sum(widths); widths = [wd * w / s for wd in widths]
        return self.table(x, y, ["ID", "TYPE", "ITEM", "CHECK METHOD", "ACCEPTANCE / TOLERANCE", "FORM"], rows, widths,
                          h=1.9, rowh=4.0, title="CRITICAL TO QUALITY (CTQ) / CRITICAL TO PROCESS (CTP) — THIS SHEET")

    def legend(self, x, y, entries, h=2.2):
        self.text(x, y, "LEGEND", h=3, bold=True)
        yy = y - 5
        for kind, label in entries:
            self.rect(x, yy - 1.2, 6, 3.2, fc=FILL.get(kind, "none"), ec=EDGE.get(kind, INK), lw=0.6)
            self.text(x + 8, yy, label, h=h, va="center")
            yy -= 4.6
        return yy

    def save(self, path_base, dpi=110):
        self.fig.savefig(path_base + ".svg", format="svg", facecolor=PAPER, metadata={"Date": None})
        self.fig.savefig(path_base + ".png", format="png", dpi=dpi, facecolor=PAPER, metadata={"Software": None})
        plt.close(self.fig)


def _wrap(s, maxch):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > maxch and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines or [""]


class View:
    """Maps model mm (X right, Y up) to sheet mm at 1:scale, origin at (ox, oy) on the sheet."""

    def __init__(self, sheet: Sheet, scale: float, ox: float, oy: float):
        self.s, self.k, self.ox, self.oy = sheet, scale, ox, oy

    def p(self, X, Y):
        return self.ox + X / self.k, self.oy + Y / self.k

    def rect(self, X0, Y0, X1, Y1, **kw):
        x0, y0 = self.p(min(X0, X1), min(Y0, Y1)); x1, y1 = self.p(max(X0, X1), max(Y0, Y1))
        self.s.rect(x0, y0, x1 - x0, y1 - y0, **kw)

    def line(self, X0, Y0, X1, Y1, **kw):
        x0, y0 = self.p(X0, Y0); x1, y1 = self.p(X1, Y1)
        self.s.line(x0, y0, x1, y1, **kw)

    def poly(self, pts, **kw):
        self.s.poly([self.p(*q) for q in pts], **kw)

    def circle(self, X, Y, R, **kw):
        x, y = self.p(X, Y); self.s.circle(x, y, R / self.k, **kw)

    def text(self, X, Y, s, **kw):
        x, y = self.p(X, Y); self.s.text(x, y, s, **kw)

    def item(self, it, label=True, h=1.9, dashed=False, show_front=True, alpha=1.0, tag_only=False):
        """Draw a layout Item in plan."""
        kw = dict(fc=FILL.get(it.kind, "none"), ec=EDGE.get(it.kind, INK), lw=0.6, alpha=alpha)
        if dashed:
            kw["ls"] = "--"; kw["fc"] = "none"
        self.rect(it.x0, it.y0, it.x1, it.y1, **kw)
        if show_front and it.mount == "floor" and it.kind in ("rack", "cooling", "power"):
            # service face tick
            if it.front == "+y":
                self.line(it.x0 + 40, it.y1 - 60, it.x1 - 40, it.y1 - 60, c=EDGE.get(it.kind, INK), lw=1.2)
            elif it.front == "+x":
                self.line(it.x1 - 60, it.y0 + 40, it.x1 - 60, it.y1 - 40, c=EDGE.get(it.kind, INK), lw=1.2)
            elif it.front == "-x":
                self.line(it.x0 + 60, it.y0 + 40, it.x0 + 60, it.y1 - 40, c=EDGE.get(it.kind, INK), lw=1.2)
        if label:
            wmm = (it.x1 - it.x0) / self.k
            rot = 90 if wmm < 9 and (it.y1 - it.y0) / self.k > wmm else 0
            self.text(it.cx, it.cy, it.tag, h=h, ha="center", va="center", bold=True, rot=rot)

    def dim_h(self, X0, X1, Yobj, offset_mm, label=None, **kw):
        x0, yo = self.p(X0, Yobj); x1, _ = self.p(X1, Yobj)
        y = yo + offset_mm
        self.s.dim_h(x0, x1, y, label if label is not None else f"{abs(X1 - X0):.0f}", ext_from=yo, **kw)

    def dim_v(self, Y0, Y1, Xobj, offset_mm, label=None, side="left", **kw):
        xo, y0 = self.p(Xobj, Y0); _, y1 = self.p(Xobj, Y1)
        x = xo + offset_mm
        self.s.dim_v(y0, y1, x, label if label is not None else f"{abs(Y1 - Y0):.0f}", ext_from=xo, side=side, **kw)

    def leader(self, X, Y, dx_mm, dy_mm, s, **kw):
        x, y = self.p(X, Y)
        self.s.leader(x, y, x + dx_mm, y + dy_mm, s, ha="left" if dx_mm >= 0 else "right", **kw)

    def bubble(self, X, Y, dx_mm, dy_mm, label, kind="CTQ"):
        x, y = self.p(X, Y)
        self.s.line(x, y, x + dx_mm, y + dy_mm, c=CTQ_C if kind == "CTQ" else CTP_C, lw=0.4)
        self.s.bubble(x + dx_mm, y + dy_mm, label, kind)

    def corrugation(self, X0, X1, Y0, Y1, pitch=280, vertical=True, c=LIGHT):
        if vertical:
            X = X0 + pitch / 2
            while X < X1:
                self.line(X, Y0, X, Y1, c=c, lw=0.25); X += pitch
        else:
            Y = Y0 + pitch / 2
            while Y < Y1:
                self.line(X0, Y, X1, Y, c=c, lw=0.25); Y += pitch

    def hatch_rect(self, X0, Y0, X1, Y1, hatch="////", ec=MUTED, fc="none", lw=0.0, z=1, alpha=1.0):
        self.rect(X0, Y0, X1, Y1, fc=fc, ec=ec, lw=lw, hatch=hatch, z=z, alpha=alpha)


# ------------------------------------------------------------ schematic symbols (sheet mm)
def sym_breaker(s: Sheet, x, y, label, rating, w=10, vertical=True):
    """Draw a circuit breaker symbol centred at x,y with label text to the right."""
    if vertical:
        s.line(x, y - w / 2, x, y - w / 6, lw=0.8)
        s.line(x, y - w / 6, x + 2.2, y + w / 3, lw=0.8)
        s.line(x, y + w / 2, x, y + w / 4, lw=0.8)
        s.text(x + 3, y + 1, label, h=2.2, bold=True)
        s.text(x + 3, y - 2.2, rating, h=2.0, c=MUTED)
    return y


def sym_box(s: Sheet, x, y, w, h, title, lines=(), kind="power", title_h=2.6):
    s.rect(x, y, w, h, fc=FILL.get(kind, "#F4F7FB"), ec=EDGE.get(kind, INK), lw=0.8, z=3)
    s.text(x + w / 2, y + h - 4.2, title, h=title_h, ha="center", bold=True, z=5)
    yy = y + h - 8
    for ln in lines:
        s.text(x + w / 2, yy, ln, h=2.0, ha="center", c=MUTED, z=5)
        yy -= 3.2


def sym_valve(s: Sheet, x, y, size=3, c=INK, vertical=False):
    if vertical:
        s.poly([(x - size / 2, y - size), (x + size / 2, y - size), (x, y)], ec=c, fc=PAPER)
        s.poly([(x - size / 2, y + size), (x + size / 2, y + size), (x, y)], ec=c, fc=PAPER)
    else:
        s.poly([(x - size, y - size / 2), (x - size, y + size / 2), (x, y)], ec=c, fc=PAPER)
        s.poly([(x + size, y - size / 2), (x + size, y + size / 2), (x, y)], ec=c, fc=PAPER)


def sym_pump(s: Sheet, x, y, r=3.5, c=INK):
    s.circle(x, y, r, fc=PAPER, ec=c, lw=0.7)
    s.poly([(x - r * 0.6, y - r * 0.6), (x + r * 0.9, y), (x - r * 0.6, y + r * 0.6)], fc=c, ec=c)


def sym_instr(s: Sheet, x, y, tag, r=3.6, c=INK):
    s.circle(x, y, r, fc=PAPER, ec=c, lw=0.6)
    s.line(x - r, y, x + r, y, c=c, lw=0.4)
    top, bot = tag.split("-") if "-" in tag else (tag, "")
    s.text(x, y + 0.6, top, h=1.9, ha="center", va="bottom", c=c, bold=True)
    s.text(x, y - 0.6, bot, h=1.7, ha="center", va="top", c=c)


def sym_hx(s: Sheet, x, y, w, h, label, kind="cooling"):
    s.rect(x, y, w, h, fc=FILL[kind], ec=EDGE[kind], lw=0.8)
    s.line(x, y, x + w, y + h, c=EDGE[kind], lw=0.5)
    s.text(x + w / 2, y + h + 1.2, label, h=2.1, ha="center", bold=True)


def sym_tank(s: Sheet, x, y, w, h, label):
    s.rect(x, y, w, h, fc=PAPER, ec=INK, lw=0.6)
    s.text(x + w / 2, y + h / 2, label, h=1.8, ha="center", va="center")
