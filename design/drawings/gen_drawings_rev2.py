"""BEN Engine Rev 2 — drawing set Rev 2.A generator (brand v2 title blocks, Rev 2 lineup).

Record: design/rev2/REVISION.json (loaded through design/revision.py with ``--lineup rev2``).
Output: design/drawings/rev2/<tier>/ (A-001 ... C-001 .svg/.png + INDEX.md), BEN 1 in design/drawings/rev2/ben1/<form>/
(reduced set A-001, E-001, C-001, I-001), design/drawings/rev2/INTERFERENCE_CHECKS.md and design/drawings/rev2/INDEX.md.
Rev 1 sheets in design/drawings/<tier>/ are frozen and never written by this script.

Reuses the Rev 1 sheet generators (gen_drawings.py, gen_hall.py) for the carried tiers and the module sheets that do not
change, with the brand v2 palette, fonts and title block applied in this process only; adds the dense-tier E-001 / M-001
(BEN 300, BEN 700) and the BEN 1 sheets.

Run:  python design/drawings/gen_drawings_rev2.py --lineup rev2 [--tier ben700] [--sheet E-001] [--dpi 110]
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sys

if "--lineup" not in sys.argv:                     # the record is chosen from the command line by design/revision.py
    sys.argv[1:1] = ["--lineup", "rev2"]

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
REPO = os.path.dirname(DESIGN)
sys.path.insert(0, DESIGN)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "brand", "v2"))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

import revision  # noqa: E402
from revision import REV  # noqa: E402
assert REV["lineup"] == "rev2", "gen_drawings_rev2.py must load design/rev2/REVISION.json"

import drawkit as DK  # noqa: E402
import layout as L  # noqa: E402
import ctq as C  # noqa: E402
import gen_drawings as G  # noqa: E402
import gen_hall as GH  # noqa: E402

OUT_ROOT = os.path.join(HERE, "rev2")
TTF = os.path.join(REPO, "brand", "v2", "fonts", "ttf")

# ====================================================================== brand v2 (brand/v2/titleblock-spec.md §1-§2)
V2 = {"ink": "#0B1A31", "slate": "#4A5D7A", "fog": "#B2C1D8", "steel": "#8EA7C8", "deep": "#1E40AF", "signal": "#4C9DFF",
      "night": "#06101F", "border": "#24406B", "paper": "#EEF4FC", "hold": "#F2C94C", "ctp": "#8A6A00", "stop": "#C8323A",
      "run": "#1B7F50", "thermal_cool": "#5CD6FF", "thermal_warm": "#FF8A3D"}
FONTS_OK = False
MONO_SEMI = ["IBM Plex Mono SemiBold", "DejaVu Sans Mono"]   # the SemiBold TTF registers as its own family
P_DISPLAY = P_TIER = P_H2 = None


def apply_brand_v2():
    """Fonts, print palette and the v2 title block, for this process only (Rev 1 generators are untouched)."""
    global FONTS_OK, P_DISPLAY, P_TIER, P_H2
    files = [f for f in ("IBMPlexSans-Regular.ttf", "IBMPlexSans-Medium.ttf", "IBMPlexSans-SemiBold.ttf", "IBMPlexSans-Bold.ttf",
                         "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "IBMPlexMono-SemiBold.ttf",
                         "Archivo-Bold.ttf", "Archivo-ExtraBold-Expanded125.ttf", "Archivo-Black-Expanded125.ttf")
             if os.path.exists(os.path.join(TTF, f))]
    for f in files:
        fm.fontManager.addfont(os.path.join(TTF, f))
    FONTS_OK = len(files) == 10
    if FONTS_OK:
        DK.FONT = ["IBM Plex Sans", "DejaVu Sans"]          # per-glyph fallback (φ, Δ) to DejaVu
        DK.MONO = ["IBM Plex Mono", "DejaVu Sans Mono"]
        P_DISPLAY = fm.FontProperties(fname=os.path.join(TTF, "Archivo-ExtraBold-Expanded125.ttf"))
        P_TIER = fm.FontProperties(fname=os.path.join(TTF, "Archivo-Black-Expanded125.ttf"))
        P_H2 = fm.FontProperties(fname=os.path.join(TTF, "Archivo-Bold.ttf"))
    plt.rcParams["font.family"] = DK.FONT if FONTS_OK else ["DejaVu Sans"]
    plt.rcParams["svg.fonttype"] = "path"
    plt.rcParams["svg.hashsalt"] = "ben-engine"
    pal = {"INK": V2["ink"], "MUTED": V2["slate"], "LIGHT": V2["fog"], "CTQ_C": V2["deep"], "CTP_C": V2["ctp"], "RED": V2["stop"], "GREEN": V2["run"]}
    for mod in (DK, G, GH):
        for k, v in pal.items():
            if hasattr(mod, k):
                setattr(mod, k, v)
    DK.EDGE.update({"rack": V2["deep"], "cooling": V2["run"], "power": V2["ctp"], "fire": V2["stop"], "structure": V2["slate"], "envelope": V2["slate"], "tray": V2["slate"]})
    DK.FILL.update({"rack": "#E3ECFB"})
    G.Sheet = SheetV2
    DK.Sheet = SheetV2
    G.brand_panel_side = brand_panel_side_v2
    G.brand_panel_cabinet = brand_panel_cabinet_v2
    GH.brand_panel_hall = brand_panel_hall_v2


def _fp(p, h):
    """FontProperties copy with the size set (sheet mm -> pt)."""
    if p is None:
        return None
    q = p.copy()
    q.set_size(DK.pt(h))
    return q


class SheetV2(DK.Sheet):
    """A1 sheet with the brand v2 title block (Deep Cobalt lockup master on white), data plate band and legal line."""

    def _border(self):
        super()._border()
        self.text(DK.SHEET_W - DK.MARGIN, 2.6, "Schreiber AI is a Schreiber Holding LLC company.", h=1.8, c=V2["slate"], ha="right")
        self.text(DK.MARGIN, 2.6, f"BEN Engine, by Schreiber AI · drawing set Rev {REV['drawing_rev']} · record {REV['path']}", h=1.8, c=V2["slate"])

    def title_block(self, status=None, rev=None):
        status = status or REV["status_long"]
        rev = rev or self.rev
        w, h, band_h = 260.0, 58.0, 6.0
        x, y = DK.SHEET_W - DK.MARGIN - w, DK.MARGIN
        yb = y + band_h                                   # block sits on the band; band + block = 58 mm (Rev 1 envelope kept)
        hb = h - band_h
        self.rect(x, y, w, h, fc=DK.PAPER, ec=V2["ink"], lw=1.0, z=8)
        # ---- brand panel (white paper, Deep Cobalt lockup master)
        pw = 62.0
        self.line(x + pw, yb, x + pw, y + h, c=V2["deep"], lw=0.9, z=10)
        lock_h = 7.0
        lock_w = lock_h * 6.527
        self.add_master("lockup-deep", x + 5, y + h - 4 - lock_h, lock_h)
        ty = y + h - 4 - lock_h - 5.2
        self._t(x + 5, ty, "BEN ENGINE", 3.0, V2["ink"], P_DISPLAY, bold=True)
        self._t(x + 5, ty - 8.6, self.tier_label.upper(), 5.0, V2["ink"], P_TIER, bold=True)
        st = REV["status_title"]
        cw = 3.3 + len(st) * 1.75
        self.rect(x + 5, ty - 15.6, min(cw, pw - 8), 4.6, fc=V2["hold"], ec="none", z=10)       # Hold chip (status only)
        self.text(x + 6.2, ty - 14.4, st, h=2.4, c=V2["night"], bold=True, z=11)
        self.text(x + 5, ty - 19.6, "not for construction until checked" if not REV["checked"] else "checked: " + REV["checker"], h=1.8, c=V2["slate"], z=11)
        self.text(x + 5, yb + 2.4, f"Rev {rev} · {self.date}", h=2.3, c=V2["slate"], mono=True, z=11)
        # ---- fields
        fx = x + pw
        self.line(fx, y + h - 19, x + w, y + h - 19, c=V2["ink"], lw=0.5, z=10)
        self.line(fx, yb + 17, x + w, yb + 17, c=V2["ink"], lw=0.5, z=10)
        self.text(fx + 3, y + h - 4.5, "TITLE", h=1.8, c=V2["slate"], mono=True, z=11)
        self._t(fx + 3, y + h - 13.5, self.title, 4.0 if len(self.title) < 52 else 3.2, V2["ink"], P_H2, bold=True)
        cols = [("DRAWING No.", self.dwg_no, 44), ("REV", rev, 18), ("SCALE", self.scale_text, 40), ("SHEET", f"{self.sheet_n} / {self.sheet_total}", 26),
                ("DATE", self.date, 36), ("STATUS", REV["status_short"], 34)]
        xx = fx
        for lab, val, cwid in cols:
            self.line(xx, yb + 17, xx, y + h - 19, c=V2["ink"], lw=0.4, z=10)
            self.text(xx + 2, y + h - 23.5, lab, h=1.8, c=V2["slate"], mono=True, z=11)
            self.text(xx + 2, yb + 20.5, val, h=3.2 if len(val) < 14 else 2.4, bold=True, mono=True, c=V2["ink"], z=11)
            xx += cwid
        self.text(fx + 3, yb + 12.2, "DRAWN: BEN Engine generator (design/drawings/gen_drawings_rev2.py)", h=2.1, c=V2["ink"], z=11)
        self.text(fx + 3, yb + 7.6, f"CHECKED: {REV['checker_text']}   APPROVED: ____________________", h=2.1, c=V2["ink"], z=11)
        self.text(fx + 3, yb + 2.6, f"CONFIG: {self.config_line}"[:150], h=1.9, c=V2["slate"], mono=True, z=11)
        # ---- data plate band (Night Navy, prints as rich black; Signal lead, Fog fields, rivets, Border dividers)
        self.rect(x, y, w, band_h, fc=V2["night"], ec=V2["border"], lw=0.5, z=10)
        for rx in (x + 3, x + w - 3):
            self.circle(rx, y + band_h / 2, 1.0, fc=V2["night"], ec=V2["steel"], lw=0.5)
            self.ax.patches[-1].set_zorder(11)
        fields = ["SCHREIBER AI", "BEN ENGINE", self.tier_label.upper(), f"DRAWING SET REV {REV['drawing_rev']}", REV["status_title"], self.date,
                  f"DWG {self.dwg_no}", f"SHEET {self.sheet_n} / {self.sheet_total}"]
        avail = w - 12
        widths = [len(f) + 3 for f in fields]
        k = avail / sum(widths)
        xx = x + 6
        for i, (f, wd) in enumerate(zip(fields, widths)):
            self.text(xx + 1.0, y + band_h / 2, f, h=1.9, c=V2["signal"] if i == 0 else V2["fog"], mono=True, bold=True, va="center", z=12)
            xx += wd * k
            if i < len(fields) - 1:
                self.line(xx - 0.8, y + 1.6, xx - 0.8, y + band_h - 1.6, c=V2["border"], lw=0.5, z=12)

    def text(self, x, y, s, h=2.5, c=None, ha="left", va="baseline", rot=0, bold=False, mono=False, z=5, bg=None):
        kw = {"bbox": dict(boxstyle="square,pad=0.15", fc=bg, ec="none")} if bg else {}
        fam = (MONO_SEMI if (bold and FONTS_OK) else DK.MONO) if mono else DK.FONT
        self.ax.text(x, y, s, fontsize=DK.pt(h), color=c or DK.INK, ha=ha, va=va, rotation=rot, family=fam,
                     fontweight="bold" if (bold and not (mono and FONTS_OK)) else "normal", zorder=z, **kw)

    def _t(self, x, y, s, h, c, fp, bold=False):
        if fp is not None:
            self.ax.text(x, y, s, fontproperties=_fp(fp, h), color=c, zorder=11)
        else:
            self.text(x, y, s, h=h, c=c, bold=bold, z=11)

    def revision_table(self, x, y, w=None):
        w = w or 326.0
        rows = [[REV["drawing_rev"], REV["issue_date"], f"{REV['status_title']}. {REV['notes_short']} Change register: " + ", ".join(c["id"] for c in REV.get("change_register", [])),
                 REV["checker"].strip() or "not checked"]]
        rows.append(["1 (C)", "2026-11-08", "Predecessor: Rev 1 drawing set (design/REVISION.json, frozen). EN-001 hold on Rev B IFC for BEN 150 / BEN 500.", "—"])
        return self.table(x, y, ["REV", "DATE", "DESCRIPTION", "CHECKED"], rows, [w * 0.08, w * 0.13, w * 0.61, w * 0.18], h=1.9, rowh=4.0,
                          title=f"REVISIONS ({REV['path']})")

    def add_master(self, name, x, y, h):
        """Reserve a slot (sheet mm, bottom-left x, y, height h) for a brand/v2 master; placed as vector in the SVG, raster in the PNG."""
        slots = self.__dict__.setdefault("slots", [])
        w = h * _aspect(name)
        gid = f"bv2-slot-{len(slots)}"
        self.ax.add_patch(Rectangle((x, y), w, h, fill=False, lw=0, gid=gid, zorder=11))
        slots.append((gid, name, x, y, w, h))
        return w

    def save(self, path_base, dpi=110):
        svg = path_base + ".svg"
        self.fig.savefig(svg, format="svg", facecolor=DK.PAPER, metadata={"Date": None})
        slots = getattr(self, "slots", [])
        if slots:
            _embed_masters(svg, slots)
            for gid, name, x, y, w, h in slots:
                png = os.path.join(REPO, "brand", "v2", "png", PNG_MASTER.get(name, name + ".png"))
                if os.path.exists(png):
                    self.ax.imshow(plt.imread(png), extent=(x, x + w, y, y + h), zorder=12, interpolation="antialiased")
            self.ax.set_xlim(0, DK.SHEET_W); self.ax.set_ylim(0, DK.SHEET_H)
        self.fig.savefig(path_base + ".png", format="png", dpi=dpi, facecolor=DK.PAPER, metadata={"Software": None})
        plt.close(self.fig)


PNG_MASTER = {"lockup-deep": "lockup-deep-2000.png", "lockup-signal": "lockup-signal-2000.png", "lockup-white": "lockup-white-2000.png",
              "mark-deep": "mark-deep-512.png", "mark-signal": "mark-signal-512.png", "stack-deep": "stack-deep-1600.png"}


def _aspect(name):
    import brandlib
    return brandlib.master_aspect(name)


def _embed_masters(svg_path, slots):
    """Route 1 of titleblock-spec §4: replace each placeholder with the vector master from brand/v2/ (never redrawn)."""
    import brandlib
    k = 72.0 / 25.4
    t = open(svg_path, encoding="utf-8").read()
    for i, (gid, name, x, y, w, h) in enumerate(slots):
        g = brandlib.embed(name, x * k, (DK.SHEET_H - y - h) * k, h * k, prefix=f"m{i}_")
        t, n = re.subn(rf'<g id="{gid}">.*?</g>', lambda m: g, t, count=1, flags=re.S)
        if n != 1:
            raise RuntimeError(f"{gid} not found in {svg_path}")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(t)


def _serial(tier):
    import json as _j
    try:
        m = _j.load(open(os.path.join(REPO, "brand", "v2", "livery", "MANIFEST.json")))
        for e in m["files"]:
            if e["tier"] == tier and e.get("serial_sample"):
                return e["serial_sample"]
    except Exception:
        pass
    return f"{tier.upper()}-2646-0001"


# ====================================================================== helpers
RX, RW, TOP = G.RX, G.RW, G.TOP
std = G.std
_wrap = G._wrap


def config_line(lay):
    if lay.is_minirack:
        cfg, d = lay.cfg, lay.d
        return f"ben1 {cfg.form} | {cfg.profile} | {cfg.it_kw:g} kW IT | {d['voltage']} | {d['ups_model'].split(' (')[0]} | {cfg.climate} | lineup rev2"
    return G.config_line(lay) + " | lineup rev2"


def sheet(lay, no, title, scale, n, total):
    return SheetV2(no, title, lay.d["tier_label"], scale, n, total, config_line(lay), REV["issue_date"])


def en001_note(sh, lay, x, y):
    """EN-001 note printed on A-002 / A-003 / E-001 of the module tiers."""
    if not lay.is_container:
        return y
    vg = L.volts_to_ground(lay)
    if lay.notes.get("nc_liner"):
        txt = (f"EN-001 (working space): {vg:.0f} V to ground. The aisle wall opposite the row carries ENV-LINER-NC (non-conductive FRP, ASTM E84 Class A, on FRT plywood, "
               "nylon fasteners, no metal trim) so NEC 110.26 condition 1 (914 mm) applies in front of the racks and CDUs; 480 V gear keeps 1,067 mm (condition 2, conservative). "
               "Fire releasing panel outside beside the door, EPO recessed in the door-end frame: nothing grounded on the aisle wall (checks I-C27 / I-D20). Do not substitute a steel liner (CTQ-E10).")
    else:
        txt = (f"EN-001 (working space): {vg:.0f} V to ground — NEC Table 110.26(A)(1) gives 914 mm under conditions 1, 2 and 3, so the liner material does not set the "
               "working space for this tier; the drawn aisle meets it. Wall devices are kept off the aisle wall (check I-C27).")
    sh.text(x, y, "ENGINEERING NOTICE EN-001", h=2.6, bold=True, c=V2["deep"])
    yy = y - 4.2
    for ln in _wrap(txt, 165):
        sh.text(x, yy, ln, h=1.9, c=V2["ink"]); yy -= 2.9
    return yy - 2


def _patch_right_column():
    orig = G.deviation_note

    def deviation_note(sh, lay, x, y):
        y = orig(sh, lay, x, y)
        if getattr(sh, "dwg_no", "") in ("A-002", "A-003", "E-001") and lay.is_container:
            y = en001_note(sh, lay, x, y - 2)
        return y
    G.deviation_note = deviation_note


# ====================================================================== brand v2 livery on the elevations (brand/v2/livery, BRAND_GUIDE §7)
def _livery(v, lay, x0, x1, z0, z1, rail=118.0, lockup_frac=0.165):
    """Shop White body, lockup-deep placement box, tier number, Night Navy data plate band above the bottom rail."""
    el, eh = x1 - x0, z1 - z0
    v.rect(x0, z0, x1, z1, fc="#F4F7FB", ec="none", z=0.5)
    bh = max(eh * 0.066, 140)
    bx0, bx1 = x0 + (178 if lay.is_container or lay.is_hall else 60), x1 - (178 if lay.is_container or lay.is_hall else 60)
    v.rect(bx0, z0 + rail + 40, bx1, z0 + rail + 40 + bh, fc=V2["night"], ec=V2["border"], lw=0.5, z=3)
    d = lay.d
    rated = f"RATED {lay.cfg.it_kw:g} kW IT"
    fields = ["SCHREIBER AI", "BEN ENGINE", d["tier_label"].upper(), "S/N " + _serial(lay.tier), rated, d["voltage"].split(" →")[-1].replace("3ph", "3PH").replace("1ph", "1PH").upper(), "IP66", "REV 2"]
    k = (bx1 - bx0) / sum(len(f) + 4 for f in fields)
    xx = bx0 + 60
    for i, f in enumerate(fields):
        v.text(xx, z0 + rail + 40 + bh / 2, f, h=min(1.8, bh / v.k * 0.55), c=V2["signal"] if i == 0 else V2["fog"], va="center", mono=True, bold=True, z=4)
        xx += (len(f) + 4) * k
    # lockup-deep master: mark height = min(16.5 % of the side height, fit) per brand/v2/livery (MANIFEST / gen_livery.py)
    asp = _aspect("lockup-deep")
    lh = min(eh * lockup_frac, el * 0.42 / asp)
    lw_ = lh * asp
    lx = x0 + (el - lw_) / 2 if not (lay.is_container or lay.is_hall) else x0 + el * 0.08
    lz = z1 - eh * 0.14 - lh
    sx, sy = v.p(lx, lz)
    v.s.add_master("lockup-deep", sx, sy, lh / v.k)
    # product line "BEN ENGINE": cap height 0.38 x mark, 0.30 x mark below the wordmark baseline, left-aligned to the wordmark
    wx = lx + lh * 1.30
    cap = 0.38 * lh
    tx, ty = v.p(wx, lz - 0.30 * lh - cap)
    v.s.ax.text(tx, ty, "BEN ENGINE", fontproperties=_fp(P_DISPLAY, cap / v.k / 0.72) if P_DISPLAY else None, color=V2["ink"], zorder=6,
                **({} if P_DISPLAY else {"fontsize": DK.pt(cap / v.k / 0.72), "fontweight": "bold"}))
    v.leader(lx + lw_ + lh * 0.25, lz + lh / 2, 14, 6, f"Artwork: brand/v2/livery/{lay.tier}-side.svg (production file)", h=1.6)
    v.text(x1 - (el * 0.06 if el > 3000 else 80), z0 + rail + 60 + bh + eh * 0.05, d["tier_label"].upper(), h=min(4.0, eh / v.k * 0.12), ha="right", c=V2["ink"], bold=True, z=4)
    v.text(x0 + el / 2, z0 - 60, f"Livery: Shop White #F4F7FB body, Night Navy data plate band with QR; production art brand/v2/livery/{lay.tier}-side.svg (masters never redrawn)",
           h=1.6, ha="center", va="top", c=V2["slate"], z=4)


def brand_panel_side_v2(vb, lay, el, eh, s):
    _livery(vb, lay, 0, el, 0, eh)


def brand_panel_cabinet_v2(vb, lay, el, eh, s):
    _livery(vb, lay, 0, el, 0, eh, rail=40, lockup_frac=0.08)


def brand_panel_hall_v2(va, lay, el, eh):
    _livery(va, lay, 0, el, 0, eh, rail=150, lockup_frac=0.12)


# ====================================================================== BEN 300 / BEN 700: E-001 power one-line (real frames)
def sheet_e001_dense(lay: L.Layout, out, n=5, total=7):
    sh = sheet(lay, "E-001", "Power one-line — 480 V, UPS frames, battery groups", "NTS", n, total)
    d, cfg = lay.d, lay.cfg
    V = 480.0

    def amps(kw, pf=0.95):
        return kw * 1000 / (math.sqrt(3) * V * pf)
    ups = [i for i in lay.items if i.tag.startswith("UPS")]
    bats = [i for i in lay.items if i.tag.startswith("BAT")]
    cdus = [i for i in lay.items if i.tag.startswith("CDU")]
    fcs = [i for i in lay.items if i.tag.startswith("FC") and i.kind == "cooling"]
    racks = lay.by_kind("rack")
    swbd = lay.find("SWBD1")
    rack_kw = cfg.it_kw / len(racks)
    rack_a = std(amps(rack_kw) / 2 * 1.25)               # A + B feeds per rack, each sized for half the rack at 125 %
    cdu_kw = 7.5
    fc_kw = 1.5
    skid_kw = round(d["trim_loop_kw"] / 3.0 + d["liquid_heat_kw"] * 0.02, 1)   # trim chiller (COP 3) + dry-cooler EC fans (~2 % of rejection)
    ups_kva = 500 if ups else 0
    ups_in_a = std(ups_kva * 1000 / (math.sqrt(3) * V) * 1.25) if ups else 0
    crit_kw = cfg.it_kw + len(cdus) * cdu_kw + 1.5
    mech_kw = len(fcs) * fc_kw + skid_kw + 3.0
    sh.view_title(30, TOP - 8, "POWER ONE-LINE DIAGRAM — LIQUID-FIRST MODULE", "NTS")
    xm = 60.0
    y = TOP - 28
    sh.text(xm, y, "UTILITY 480Y/277 V 3φ 4W", h=2.8, bold=True, ha="center")
    sh.text(xm, y - 4, f"{d['service_amps_calc']} A calculated (80 % rule), {d['total_kw']} kW / {d['total_kva']} kVA", h=1.9, ha="center", c=DK.MUTED)
    sh.line(xm, y - 6, xm, y - 12, lw=1.0)
    sh.circle(xm, y - 16, 4, lw=0.8); sh.text(xm, y - 16, "kWh", h=1.6, ha="center", va="center")
    sh.line(xm, y - 20, xm, y - 26, lw=1.0)
    DK.sym_box(sh, xm - 30, y - 62, 60, 36, "SVC — SERVICE SECTION", [f"Main CB {d['service_breaker_a']} A, 480 V", "NEMA 4X, exterior blind end", "Type 1 SPD; GES bond", "Generator inlet / ATS (option)"], kind="power")
    sh.text(xm + 32, y - 34, "CTP-E1 HOLD: licensed electrician", h=1.8, c=DK.CTP_C)
    sh.line(xm, y - 62, xm, y - 72, lw=1.2)
    yb = y - 74
    main_lbl = (f"SWBD1 — 480 V SWITCHBOARD SECTION {d['service_breaker_a']} A (main + maintenance bypass), 915 W x 610 D" if swbd
                else f"PNL-D — 480 V DISTRIBUTION PANELBOARD {d['service_breaker_a']} A MAIN (end wall)")
    sh.line(xm - 30, yb, 470, yb, lw=2.2)
    sh.text(xm + 4, yb + 2.2, main_lbl, h=2.1, bold=True)
    # ---- UPS frames with battery groups
    ux0 = 80.0
    pitch = 70.0 if len(ups) > 1 else 0
    bats_per = max(1, len(bats) // max(1, len(ups)))
    for k, u in enumerate(ups):
        xu = ux0 + k * pitch
        sh.line(xu, yb, xu, yb - 8, lw=1.0)
        DK.sym_breaker(sh, xu, yb - 12, f"CB-{u.tag}", f"{ups_in_a} A 3P")
        sh.line(xu, yb - 17, xu, yb - 26, lw=1.0)
        DK.sym_box(sh, xu - 26, yb - 62, 52, 36, f"{u.tag} GALAXY VL", [f"frame 500 kVA, 850 x 925", f"{d['ups_kva_each']} kVA load share", "internal N+1 modules", "static + maint. bypass"], kind="power", title_h=2.3)
        for j in range(bats_per):
            bi = k * bats_per + j
            if bi >= len(bats):
                break
            bx = xu - 26 + j * 27
            sh.rect(bx, yb - 84, 25, 14, fc=DK.FILL["power"], ec=DK.EDGE["power"], lw=0.7)
            sh.text(bx + 12.5, yb - 75, bats[bi].tag, h=2.0, ha="center", bold=True)
            sh.text(bx + 12.5, yb - 79.5, "32.6 kWh Li", h=1.6, ha="center", c=DK.MUTED)
            sh.text(bx + 12.5, yb - 82.5, f"group {bi + 1}", h=1.6, ha="center", c=DK.MUTED)
            sh.line(bx + 12.5, yb - 70, bx + 12.5, yb - 62, lw=0.6, ls="--")
        sh.line(xu, yb - 62, xu, yb - 66, lw=1.0)
    if ups:
        sh.text(ux0 + (len(ups) - 1) * pitch + 34, yb - 76, f"Battery: {d['battery_cabinets']} cabinets x 32.6 kWh = {d['battery_kwh_installed']} kWh, {d['battery_minutes_installed']} min at IT load; one cabinet per NFPA 855 group (CTQ-E9 HOLD)", h=1.8, c=DK.MUTED)
    # ---- critical bus (UPS output)
    yc = yb - 104
    sh.line(30, yc, 470, yc, lw=1.8)
    sh.text(ux0 + (len(ups) - 1) * pitch + 6, yc + 2.2, f"CRITICAL BUS 480 V (UPS output, {crit_kw:.0f} kW): racks + CDU pumps ride through on the UPS", h=2.0, bold=True)
    for k, u in enumerate(ups):
        sh.line(ux0 + k * pitch, yb - 66, ux0 + k * pitch, yc, lw=1.0)
    loads = [(r.tag, f"2 x {rack_a} A", "rack", f"{rack_kw:.0f} kW") for r in racks] + [(c.tag, f"{std(amps(cdu_kw) * 1.25)} A", "cooling", f"{cdu_kw} kW") for c in cdus] + [("CP1", "20 A", "controls", "1.5 kW")]
    pitch_l = min(30.0, 430.0 / len(loads))
    for i, (tag, a, kind, kw) in enumerate(loads):
        xl = 40 + i * pitch_l
        sh.line(xl, yc, xl, yc - 7, lw=0.8)
        DK.sym_breaker(sh, xl, yc - 11, "", "")
        sh.text(xl, yc - 18, a, h=1.6, ha="center", c=DK.MUTED)
        sh.line(xl, yc - 15, xl, yc - 21, lw=0.8)
        bw = min(22.0, pitch_l - 3)
        sh.rect(xl - bw / 2, yc - 37, bw, 16, fc=DK.FILL[kind], ec=DK.EDGE[kind], lw=0.6)
        sh.text(xl, yc - 26.5, tag, h=2.0, ha="center", bold=True)
        sh.text(xl, yc - 31, kw, h=1.6, ha="center", c=DK.MUTED)
        sh.text(xl, yc - 35, "A+B" if kind == "rack" else ("pumps" if kind == "cooling" else "UPS"), h=1.5, ha="center", c=DK.MUTED)
    sh.text(30, yc - 43, f"Rack feeds: 480Y/277 V direct to the rack power shelves (no transformer), two feeds per rack (A from {ups[0].tag if ups else 'UPS'}, B from "
            f"{ups[-1].tag if ups else 'UPS'}), {rack_a} A 3P each, sized for half the rack at 125 %; tap boxes on TR-P over the aisle.", h=1.8, c=DK.MUTED)
    # ---- mechanical bus (not on UPS)
    xmch = 400.0
    sh.line(xmch, yb, xmch, yb - 8, lw=1.0)
    DK.sym_breaker(sh, xmch, yb - 12, "CB-M", f"{std(amps(mech_kw) * 1.25)} A")
    sh.line(xmch, yb - 17, xmch, yb - 26, lw=1.0)
    DK.sym_box(sh, xmch - 40, yb - 58, 80, 32, "MECHANICAL (not on UPS)", [f"{len(fcs)} fan coils x {fc_kw} kW", f"Skid: dry coolers + trim chiller {skid_kw} kW", "Lights, receptacles 3 kW", "EPO sheds this bus"], kind="cooling", title_h=2.2)
    # EPO and grounding
    ye = yc - 62
    sh.text(30, ye, "EPO", h=3, bold=True, c=DK.RED)
    sh.text(30, ye - 5, "Recessed in the door-end frame (interior, at the exit) + exterior station on SVC: shunt-trips UPS output breakers and the mechanical main; "
            "CDU pumps stop only after the leak / isolation logic (M-001). Hard-wired, monitored by a controller DI (CTQ-E3, CTP-K1).", h=1.9)
    yg = ye - 26
    sh.text(30, yg, "GROUNDING AND BONDING (NEC 250)", h=3, bold=True)
    for i, lab in enumerate(["2 ground rods + pad Ufer (GES), TMGB in SVC", "Module frame bonded at 2 corners (exothermic)", "Rack / tray ground bus, 6 AWG per rack",
                             "CDU, manifold and dry-cooler skid bonded", "Battery cabinets bonded per UL 9540", "Aisle-wall liner ENV-LINER-NC: NOT bonded (non-conductive, EN-001)"]):
        sh.text(34, yg - 5 - i * 3.2, "• " + lab, h=1.9)
    sh.text(30, yg - 28, f"Interference / code checks for this sheet: I-D5 (gear working space 1,067), I-D7 (second entrance), I-D12 (UPS), I-D13 (battery power), I-D14 (NFPA 855 groups), I-D19 (PNL-D working space).", h=1.8, c=DK.MUTED)

    def extra(sh, x, y):
        rows = [["Service", f"{d['voltage']}, main {d['service_breaker_a']} A (calc {d['service_amps_calc']} A)"],
                ["Main distribution", ("SWBD1 switchboard section 1,200 A (915 x 610), main + maintenance bypass" if swbd else f"PNL-D panelboard {d['service_breaker_a']} A, end wall")],
                ["UPS", f"{len(ups)} x Galaxy VL 500 kVA frame (N+1 modules inside), {cfg.redundancy}; input CB {ups_in_a} A"],
                ["Battery", f"{d['battery_cabinets']} x 32.6 kWh Li-ion = {d['battery_kwh_installed']} kWh, {d['battery_minutes_installed']} min; one cabinet per group"],
                ["Racks", f"{len(racks)} x {rack_kw:.0f} kW, 2 feeds x {rack_a} A 3P at 480Y/277 V"],
                ["CDUs (on UPS)", f"{len(cdus)} x ~{cdu_kw} kW pump drives"],
                ["Mechanical (not on UPS)", f"{mech_kw:.0f} kW: fan coils, skid (trim chiller {d['trim_loop_kw']} kW cooling), lights"],
                ["Working space", "Gear 1,067 mm (cond. 2, I-D5); racks / CDUs 914 mm with ENV-LINER-NC (I-D4, I-D6); PNL-D clear (I-D19)"],
                ["PUE estimate", f"{d['pue_estimate']}"]]
        y = sh.table(x, y, ["ITEM", "VALUE"], rows, [RW * 0.26, RW * 0.74], title="ELECTRICAL SCHEDULE (preliminary)", h=1.9)
        y -= 6
        notes = ["ALL BREAKER AND CONDUCTOR SIZES ARE PRELIMINARY: short-circuit, coordination and arc-flash study by a licensed engineer before energisation (NEC 110.9/110.10/240.87, NFPA 70E).",
                 "Galaxy VL frames are 850 W x 925 D (brochure); masses assumed 900 kg, to be read from the IOM before S-001 is checked.",
                 "Lithium: UL 9540 system listing and UL 9540A report on file before the reduced group spacing is used (I-D14); otherwise 914 mm between groups does not fit the row.",
                 "Only a licensed electrician lands conductors and energises (CTP-E1 HOLD)."]
        return sh.notes(x, y, "ELECTRICAL NOTES", notes, h=2.0, lead=3.1)
    G.right_column(sh, lay, "E-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "E-001"))


# ====================================================================== BEN 300 / BEN 700: M-001 P&ID (W45 loop + 18 C trim loop)
def sheet_m001_dense(lay: L.Layout, out, n=6, total=7):
    sh = sheet(lay, "M-001", "Cooling P&ID — W45 direct liquid + 18 °C trim loop", "NTS", n, total)
    d, cfg = lay.d, lay.cfg
    cdus = [i for i in lay.items if i.tag.startswith("CDU")]
    fcs = [i for i in lay.items if i.tag.startswith("FC") and i.kind == "cooling"]
    racks = lay.by_kind("rack")
    SUP, RET, TRIM = V2["thermal_cool"], V2["thermal_warm"], "#2F7FF0"
    sh.view_title(30, TOP - 8, "COOLING P&ID — W45 LOOP, ROW CDUs N+1, 18 °C TRIM LOOP", "NTS")
    # skid (exterior)
    sx, sy = 30.0, 330.0
    sh.rect(sx - 4, sy - 6, 120, 210, fc="none", ec=DK.MUTED, lw=0.6, ls="--")
    sh.text(sx - 2, sy + 199, "ADJACENT SKID (exterior)", h=2.2, bold=True, c=DK.MUTED)
    DK.sym_hx(sh, sx, sy + 130, 52, 40, f"DC1 W45 DRY COOLERS {math.ceil(d['liquid_heat_kw'] * 1.15)} kW")
    sh.text(sx + 26, sy + 125, f"design ambient {d['climate']['t_design_c']} C + 8 K -> {d['climate']['t_design_c'] + 8:.0f} C", h=1.7, ha="center", c=DK.MUTED)
    DK.sym_pump(sh, sx + 66, sy + 160); sh.text(sx + 66, sy + 164.5, "P-F1/F2 N+1", h=1.7, ha="center")
    DK.sym_hx(sh, sx, sy + 40, 52, 34, f"CH1 TRIM CHILLER {d['trim_loop_kw']} kW")
    sh.text(sx + 26, sy + 35, "factory-sealed, A1/A2L per COMPLIANCE", h=1.6, ha="center", c=DK.MUTED)
    DK.sym_pump(sh, sx + 60, sy + 20); sh.text(sx + 71, sy + 20, "P-T1/T2 N+1", h=1.7, va="center")
    DK.sym_hx(sh, sx + 62, sy + 88, 40, 24, "HRX heat reuse (opt.)")
    # facility W45 headers to CDUs
    cx0 = 190.0
    yF_s, yF_r = sy + 160, sy + 140
    sh.line(sx + 52, yF_s, cx0 + 20 + 62 * (len(cdus) - 1) + 40, yF_s, c=SUP, lw=1.6)
    sh.line(sx + 52, yF_r, cx0 + 20 + 62 * (len(cdus) - 1) + 40, yF_r, c=RET, lw=1.6)
    sh.text(cx0, yF_s + 2, f"FACILITY W45 SUPPLY {d['loop_supply_design_c']:.0f} C (primary)", h=1.8, c=DK.INK)
    sh.text(cx0, yF_r - 4.5, "FACILITY RETURN", h=1.8, c=DK.INK)
    sh.line(sx + 82, yF_r, sx + 82, sy + 112, c=RET, lw=0.8, ls="--")
    # CDUs
    for k, c in enumerate(cdus):
        x = cx0 + k * 62
        sh.line(x + 10, yF_s, x + 10, sy + 110, c=SUP, lw=1.0); sh.line(x + 30, yF_r, x + 30, sy + 110, c=RET, lw=1.0)
        DK.sym_box(sh, x, sy + 70, 40, 40, f"{c.tag} 600 kW", ["plate HX + pumps N+1", "50 um strainer", "Modbus TCP"], kind="cooling", title_h=2.2)
        sh.line(x + 10, sy + 70, x + 10, sy + 50, c=SUP, lw=1.0); sh.line(x + 30, sy + 70, x + 30, sy + 56, c=RET, lw=1.0)
    sh.text(cx0, sy + 114, f"{len(cdus)} CDUs: N = {d['cooling_units_n']}, +1 standby (I-D11); common secondary header", h=1.8, c=DK.MUTED)
    # secondary headers (rear plenum)
    x_end = 470.0
    ysS, ysR = sy + 50, sy + 56
    sh.line(cx0 + 10, ysS, x_end, ysS, c=SUP, lw=1.8)
    sh.line(cx0 + 30, ysR, x_end, ysR, c=RET, lw=1.8)
    sh.text(cx0 + 50, ysR + 2, f"W45 SECONDARY RETURN {d['loop_return_design_c']:.0f} C, DN80 rear-plenum header", h=1.8)
    sh.text(cx0 + 50, ysS - 4.5, f"W45 SECONDARY SUPPLY {d['loop_supply_design_c']:.0f} C, {d['loop_flow_lpm']} L/min, ΔT {d['loop_dt_design_k']:.0f} K", h=1.8)
    # isolation valves
    xi = cx0 + 52 + 62 * (len(cdus) - 1) + 8
    DK.sym_valve(sh, xi, ysS, c=DK.RED); DK.sym_valve(sh, xi, ysR, c=DK.RED)
    sh.text(xi - 6, ysS - 9, "ISO1 S/R spring-return, close on leak <= 15 s (CTQ-M6)", h=1.7, c=DK.RED)
    # racks with UQD drops
    rx0 = xi + 12
    pitch = (x_end - rx0) / max(1, len(racks))
    for k, r in enumerate(racks):
        x = rx0 + k * pitch + 3
        bw = min(26.0, pitch - 4)
        sh.line(x + 5, ysS, x + 5, sy - 6, c=SUP, lw=0.8); sh.line(x + bw - 5, ysR, x + bw - 5, sy - 6, c=RET, lw=0.8)
        sh.rect(x, sy - 36, bw, 30, fc=DK.FILL["rack"], ec=DK.EDGE["rack"], lw=0.7)
        sh.text(x + bw / 2, sy - 15, r.tag, h=2.2, ha="center", bold=True)
        sh.text(x + bw / 2, sy - 20, "cold plates", h=1.5, ha="center", c=DK.MUTED)
        sh.text(x + bw / 2, sy - 24, f"{cfg.it_kw / len(racks) * 0.9:.0f} kW liq.", h=1.5, ha="center", c=DK.MUTED)
        sh.text(x + bw / 2, sy - 28.5, "UQD x2", h=1.5, ha="center", c=DK.MUTED)
        sh.rect(x - 1, sy - 40, bw + 2, 3, fc="none", ec=DK.RED, lw=0.6)
        sh.text(x + bw / 2, sy - 44, f"LS-{k + 1}", h=1.6, ha="center", c=DK.RED)
    sh.text(rx0, sy - 50, "Drip tray + spot leak sensor under every rack drop, leak rope under every CDU and along the header drip tray", h=1.7, c=DK.RED)
    # trim loop to fan coils
    yT_s, yT_r = sy - 70, sy - 76
    sh.line(sx + 52, sy + 60, sx + 60, sy + 60, c=TRIM, lw=1.2)
    sh.line(sx + 60, sy + 60, sx + 60, yT_s, c=TRIM, lw=1.2); sh.line(sx + 52, sy + 46, sx + 68, sy + 46, c=TRIM, lw=1.2, ls="--"); sh.line(sx + 68, sy + 46, sx + 68, yT_r, c=TRIM, lw=1.2, ls="--")
    sh.line(sx + 60, yT_s, x_end, yT_s, c=TRIM, lw=1.4)
    sh.line(sx + 68, yT_r, x_end, yT_r, c=TRIM, lw=1.2, ls="--")
    sh.text(sx + 72, yT_s + 2, f"TRIM LOOP SUPPLY {d['trim_loop_c']:.0f} C (chilled water, separate from W45)", h=1.8, c=TRIM)
    sh.text(sx + 72, yT_r - 4.5, "TRIM LOOP RETURN ~24 C", h=1.8, c=TRIM)
    fpitch = (x_end - 150) / max(1, len(fcs))
    for k, fc in enumerate(fcs):
        x = 150 + k * fpitch + 4
        bw = min(26.0, fpitch - 6)
        sh.line(x + 5, yT_s, x + 5, yT_s - 12, c=TRIM, lw=0.8); sh.line(x + bw - 5, yT_r, x + bw - 5, yT_s - 12, c=TRIM, lw=0.8, ls="--")
        sh.rect(x, yT_s - 32, bw, 20, fc=DK.FILL["cooling"], ec=DK.EDGE["cooling"], lw=0.7)
        sh.text(x + bw / 2, yT_s - 20, fc.tag, h=2.0, ha="center", bold=True)
        sh.text(x + bw / 2, yT_s - 25, "20 kW @18 C", h=1.5, ha="center", c=DK.MUTED)
        sh.text(x + bw / 2, yT_s - 29, "EC fans", h=1.5, ha="center", c=DK.MUTED)
    sh.text(150, yT_s - 38, f"Residual air {d['air_residual']:.0%} of IT = {cfg.it_kw * d['air_residual'] * 1.05:.0f} kW incl. 5 %: {d['fancoils_n']} x 20 kW (N) + 1 (I-D10). "
            "W45 water (40-50 C) cannot cool 27 C room air: the fan coils never connect to the W45 loop (CAPA observation, Rev 1 line CLG-AIR-RESID-HD not used).", h=1.8, c=DK.INK)
    # instruments and logic
    for k, (tag, xx) in enumerate((("TT-101", cx0 - 12), ("PT-101", cx0 - 4), ("FT-101", x_end - 30), ("TT-102", x_end - 20), ("TT-201", 150))):
        DK.sym_instr(sh, xx, (ysS + 20 if k < 4 else yT_s + 12), tag)
    yl = 150.0
    sh.text(30, yl, "LEAK-TO-ISOLATION LOGIC (BEN Controller, hard-wired dry contacts)", h=2.6, bold=True, c=DK.RED)
    for i, ln in enumerate(["Any LS-n or leak rope = 1  ->  alarm + ISO1 supply and return close (spring return, position switches)  ->  isolation confirmed <= 15 s (CTQ-M6 WITNESS).",
                            "CDU pumps ramp to minimum on the isolated header; loop flow to the row 0 within 30 s; racks throttle on their own coolant-temperature protection.",
                            "Leak on the facility side (skid): skid pumps stop, CDUs alarm on approach; dry coolers drain-down per skid manual.",
                            "Failsafe: loss of controller -> ISO1 holds position (spring-return only on leak relay); watchdog alarm (CTP-K2)."]):
        sh.text(32, yl - 5 - i * 3.4, ln, h=1.85)
    sh.rect(30, 96, 160, 7, fc="none", ec=DK.MUTED, lw=0.4)
    for i in range(20):
        t = i / 19
        c0 = matplotlib.colors.to_rgb(V2["thermal_cool"]); c1 = matplotlib.colors.to_rgb(V2["thermal_warm"])
        sh.rect(30 + i * 8, 96, 8, 7, fc=tuple(a + (b - a) * t for a, b in zip(c0, c1)), ec="none")
    sh.text(30, 92, "Thermal ramp legend: supply (cool, 18-40 C) to return (warm, 50 C). Trim loop in Cobalt.", h=1.8, c=DK.MUTED)

    def extra(sh, x, y):
        rows = [["IT load / racks", f"{cfg.it_kw:.0f} kW in {len(racks)} racks, {cfg.it_kw / len(racks):.0f} kW each"],
                ["Liquid heat (90 %)", f"{d['liquid_heat_kw']} kW on W45, {d['loop_flow_lpm']} L/min at ΔT {d['loop_dt_design_k']:.0f} K"],
                ["Row CDUs", f"{len(cdus)} x 600 kW (N = {d['cooling_units_n']}), 600 x 1200 x 2000, back to the wall"],
                ["Residual air (10 %)", f"{len(fcs)} fan coils x 20 kW on the {d['trim_loop_c']:.0f} C trim loop ({d['trim_loop_kw']} kW chiller)"],
                ["Heat rejection", lay.notes.get("heat_rejection", "")],
                ["Heat reuse (option)", f"{d['heat_reuse_kw_available']} kW at the W45 return via HRX"],
                ["Isolation / leak", "ISO1 S+R, LS per rack, rope under CDUs and header; isolation <= 15 s"],
                ["Fluid", "Treated water (25 % PG where t_min < 0 C), CTQ-M4 / CTQ-M9"]]
        y = sh.table(x, y, ["ITEM", "VALUE"], rows, [RW * 0.26, RW * 0.74], title="COOLING SCHEDULE (W45 liquid-first)", h=1.9)
        y -= 6
        notes = ["Vendor classes, not quotes: CDU (Vertiv CoolChip CDU 600 class), UQD (Staubli / Parker class), isolation valves (Belimo class), dry coolers (Guentner / Alfa Laval class), trim chiller (packaged air-cooled).",
                 "Pressure test 1.5 x working pressure 2 h on every loop before the racks are connected (CTQ-M1, CTQ-M8); flush and water analysis before fill (CTQ-M9 HOLD).",
                 "Fan-coil supply stays >= room dew point + 2 K (CTQ-M10); condensate trays piped to the floor drain.",
                 "Piping, flushing and fill by a licensed mechanical contractor (CTP-M1 HOLD)."]
        return sh.notes(x, y, "COOLING NOTES", notes, h=2.0, lead=3.1)
    G.right_column(sh, lay, "M-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "M-001"))


# ====================================================================== BEN 1 (mini rack) reduced set
BEN1_SHEETS = [("A-001", "General arrangement — rack / cabinet, dimensions and clearances"), ("E-001", "Plug-in one-line — UPS and outlet circuit"),
               ("C-001", "Controls — BEN Pod placement"), ("I-001", "Installation — closet / office requirements")]


def _ben1_front(sh, lay, ox, oy, s, labels=True):
    """Front elevation of the mini rack with the U stack. Model coords: x across (mm), z up (mm)."""
    v = DK.View(sh, s, ox, oy)
    body = V2["night"]
    v.rect(0, 0, lay.ext_l, lay.ext_h, fc=body, ec=V2["ink"], lw=0.8)
    x0, x1 = (lay.ext_l - lay.L) / 2, (lay.ext_l + lay.L) / 2
    v.rect(x0, 40, x1, lay.ext_h - 40, fc="#16305A", ec=V2["border"], lw=0.4)
    for it in [i for i in lay.items if i.mount == "rack" and i.tag not in ("P1", "P2")]:
        kind = it.kind
        v.rect(x0 + 8, it.z0, x1 - 8, it.z1, fc=DK.FILL.get(kind, "#FFFFFF"), ec=DK.EDGE.get(kind, V2["ink"]), lw=0.5)
        if labels:
            v.text((x0 + x1) / 2, (it.z0 + it.z1) / 2, f"{it.tag}  {it.label.split(' (')[0][:40]}", h=1.6, ha="center", va="center")
    # data plate band along the bottom of the bezel / door (S2 ground indoors), with the livery sample serial
    bh = max(18.0, lay.ext_h * 0.06)
    v.rect(0, 4, lay.ext_l, 4 + bh, fc="#0F2342", ec=V2["border"], lw=0.4)
    v.text(lay.ext_l * 0.03, 4 + bh / 2, f"SCHREIBER AI · BEN ENGINE · BEN 1 · S/N {_serial('ben1')} · 120 V · REV 2", h=min(1.5, bh / v.k * 0.6), c=V2["fog"], va="center", mono=True, z=6)
    # lockup-signal master (indoor Night Navy body) in the top margin of the bezel / door
    mh = min(30.0, (lay.ext_h - lay.L * 0 - (lay.ext_h - 40)) * 0.8) if False else 26.0
    lw_ = mh * _aspect("lockup-signal")
    if lw_ > lay.ext_l * 0.9:
        mh = lay.ext_l * 0.9 / _aspect("lockup-signal"); lw_ = lay.ext_l * 0.9
    sx, sy = v.p((lay.ext_l - lw_) / 2, lay.ext_h - 8 - mh)
    sh.add_master("lockup-signal", sx, sy, mh / v.k)
    sh.text(v.ox, v.oy - 23, f"Artwork: brand/v2/livery/ben1-{'bezel-10in' if lay.cfg.form == 'rack10' else 'door-12u'}.svg (production file); lockup-signal master on the Night Navy bezel / door", h=1.7, c=V2["slate"])
    return v


def ben1_a001(lay, out, n, total):
    d, cfg = lay.d, lay.cfg
    s = 2 if cfg.form == "rack10" else 5
    sh = sheet(lay, "A-001", BEN1_SHEETS[0][1], f"1:{s}", n, total)
    sh.view_title(30, TOP - 8, f"FRONT ELEVATION — {d['form_label'].upper()}", f"1:{s}")
    oy = TOP - 30 - lay.ext_h / s
    v = _ben1_front(sh, lay, 40, oy, s)
    v.dim_h(0, lay.ext_l, 0, -8, f"{lay.ext_l:.0f}")
    v.dim_v(0, lay.ext_h, 0, -8, f"{lay.ext_h:.0f}")
    sh.text(40, oy - 18, f"U stack ({lay.notes['u_used']}U of {lay.notes['u_total']}U, check I-B1); data plate band on the bezel / door (brand/v2/livery/ben1-*.svg)", h=1.9, c=DK.MUTED)
    # side elevation
    sx = 40 + lay.ext_l / s + 60
    sh.text(sx, TOP - 8, "SIDE ELEVATION", h=4, bold=True)
    vs = DK.View(sh, s, sx, oy)
    vs.rect(0, 0, lay.ext_w, lay.ext_h, fc="#E8EDF3", ec=V2["ink"], lw=0.8)
    deep = max(L.MINI_DEVICES[k][1] for k in lay.notes["stack"])
    vs.rect((lay.ext_w - deep) / 2, 60, (lay.ext_w + deep) / 2, lay.ext_h - 60, fc="none", ec=DK.EDGE["rack"], lw=0.5, ls="--")
    vs.dim_h(0, lay.ext_w, 0, -8, f"{lay.ext_w:.0f}")
    vs.text(lay.ext_w / 2, lay.ext_h / 2, f"deepest device {deep} mm\nusable {L.TIER_GEOMETRY['ben1']['forms'][cfg.form]['usable_depth_mm']} mm (I-B2)", h=1.7, ha="center", va="center")
    sh.text(sx, oy - 18, "Air: front intake -> rear exhaust" + (" (two extraction fans N+1 in the rear door)" if cfg.form == "cab12" else " (open rack, device fans)"), h=1.9, c=DK.MUTED)
    # plan with clearances
    ps = 20
    py = min(250.0, oy - 85)
    sh.view_title(30, py + 50, "PLAN — SERVICE AND AIR CLEARANCES", f"1:{ps}")
    vp = DK.View(sh, ps, 80, py - 60)
    fp_l = lay.notes["desk_footprint_mm"][0]
    vp.rect(-300, -300, fp_l + 300, lay.ext_w + 914, fc="none", ec=DK.CTQ_C, lw=0.5, ls=":")
    vp.rect(0, 0, lay.ext_l, lay.ext_w, fc=DK.FILL["rack"], ec=DK.EDGE["rack"], lw=0.8)
    vp.text(lay.ext_l / 2, lay.ext_w / 2, "BEN 1", h=2.0, ha="center", va="center", bold=True)
    if cfg.form == "rack10":
        u = lay.find("UPS1")
        if u and u.mount == "floor":
            vp.rect(u.x0, u.y0, u.x1, u.y1, fc=DK.FILL["power"], ec=DK.EDGE["power"], lw=0.6)
            vp.text(u.cx, u.cy, "UPS", h=1.6, ha="center", va="center", rot=90)
    vp.dim_h(0, lay.ext_l, lay.ext_w + 914, 4, f"{lay.ext_l:.0f}")
    vp.dim_v(lay.ext_w, lay.ext_w + 914, -300, -4, "914")
    vp.dim_v(-300, 0, -300, -4, "300")
    vp.text(lay.ext_l / 2, -150, "REAR: 300 mm clear (exhaust)", h=1.7, ha="center", va="center", c=DK.CTQ_C)
    vp.dim_h(-300, 0, -300, -4, "300")
    vp.text(lay.ext_l / 2, lay.ext_w + 914 - 120, "FRONT: keep 914 mm clear for service while energised", h=1.7, ha="center", c=DK.CTQ_C)
    # tables
    def extra(sh, x, y):
        rows = [["Form", f"{cfg.form}: {d['form_label']}"], ["Reference model", d["geometry"]["reference"]],
                ["Outside (W x D x H)", f"{lay.ext_l:.0f} x {lay.ext_w:.0f} x {lay.ext_h:.0f} mm; {lay.notes['u_total']}U"],
                ["IT load", f"{cfg.it_kw:g} kW (form max {L.TIER_GEOMETRY['ben1']['forms'][cfg.form]['it_kw_max']} kW, I-B3)"],
                ["Mass", f"tare {d['geometry']['tare_kg']} kg, gross {d['gross_kg']} kg"],
                ["Noise at 1 m", f"{d['noise_dba_est']} dBA est. vs {d['noise_dba_target']:.0f} dBA target (I-B7)"],
                ["Body / livery", "Night Navy body, S2 data plate band with QR (brand/v2/livery/ben1-*)"]]
        y = sh.table(x, y, ["ITEM", "VALUE"], rows, [RW * 0.28, RW * 0.72], title="UNIT DATA", h=1.9)
        y -= 6
        rows = [[it.tag, it.code, it.label[:70]] for it in lay.items if it.mount in ("rack", "floor") and it.tag != "R1"]
        y = sh.table(x, y, ["TAG", "CODE", "DEVICE"], rows, [RW * 0.12, RW * 0.26, RW * 0.62], title="U STACK AND DEVICES (bottom up)", h=1.8, rowh=3.8)
        y -= 6
        y = sh.revision_table(x, y, RW)
        return y
    G.right_column(sh, lay, "A-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "A-001"))


def ben1_e001(lay, out, n, total):
    sh = sheet(lay, "E-001", BEN1_SHEETS[1][1], "NTS", n, total)
    d, cfg = lay.d, lay.cfg
    sh.view_title(30, TOP - 8, "PLUG-IN ONE-LINE (120 V)", "NTS")
    x = 80.0; y = TOP - 34
    DK.sym_box(sh, x - 40, y - 26, 80, 26, "CUSTOMER BRANCH CIRCUIT", [d["outlet_circuit"][:52], f"{d['outlet_circuit_a']} A breaker in the office panel", "dedicated: nothing else on it"], kind="structure", title_h=2.2)
    sh.line(x, y - 26, x, y - 36, lw=1.0)
    sh.text(x + 4, y - 32, f"Receptacle NEMA {'5-15R' if d['ups_plug'].endswith('5-15P') else '5-20R'}  <-  UPS cord {d['ups_plug']} (no extension cord, no power strip)", h=1.9)
    DK.sym_box(sh, x - 40, y - 76, 80, 40, "UPS1 LINE-INTERACTIVE LITHIUM", [d["ups_model"][:50], f"{d['ups_va']} VA / {d['ups_w']} W, ~{d['ups_runtime_min_est']} min", "AVR, USB + network card", "graceful shutdown to hosts"], kind="power", title_h=2.2)
    sh.line(x, y - 76, x, y - 86, lw=1.0)
    sh.text(x + 4, y - 82, "UPS outlets (battery-backed)", h=1.9, c=DK.MUTED)
    yb = y - 88
    devices = [it for it in lay.items if it.mount == "rack" and it.tag not in ("UPS1", "BAT1", "PDU1", "P1", "P2")]
    pdu = lay.find("PDU1")
    if pdu:
        DK.sym_box(sh, x - 30, yb - 24, 60, 22, "PDU1 10-inch 1U", ["4 x NEMA 5-15R, surge", "fed from one UPS outlet"], kind="power", title_h=2.0)
        sh.line(x, yb, x, yb - 2, lw=1.0)
        sh.line(x, yb - 24, x, yb - 30, lw=1.0)
        yb -= 30
    sh.line(30, yb, 470, yb, lw=1.4)
    pitch = min(60.0, 430.0 / max(1, len(devices) + 2))
    loads = devices + [None, None]
    for i, it in enumerate(loads):
        xl = 30 + pitch / 2 + i * pitch
        sh.line(xl, yb, xl, yb - 10, lw=0.8)
        bw = pitch - 6
        if it is None:
            lab, sub, kind = ("P1 / P2", "BEN Pod W x2, 5 V", "controls") if i == len(devices) else ("SPARE", "outlet", "structure")
        else:
            lab, sub, kind = it.tag, it.label.split(" (")[0][:26], it.kind
        sh.rect(xl - bw / 2, yb - 30, bw, 20, fc=DK.FILL.get(kind, "#FFFFFF"), ec=DK.EDGE.get(kind, V2["ink"]), lw=0.6)
        sh.text(xl, yb - 16, lab, h=2.0, ha="center", bold=True)
        for k, ln in enumerate(_wrap(sub, int(bw / 1.0))[:2]):
            sh.text(xl, yb - 21 - k * 3, ln, h=1.5, ha="center", c=DK.MUTED)
    sh.text(30, yb - 40, f"Load at the outlet: {d['outlet_amps']} A at 120 V vs {0.8 * d['outlet_circuit_a']:.0f} A continuous (80 % of {d['outlet_circuit_a']} A, I-B4). "
            f"UPS real power {d['ups_w']} W vs IT x 1.25 = {cfg.it_kw * 1250:.0f} W (I-B5).", h=1.9)
    sh.text(30, yb - 45, f"Export option: {d['voltage_option']}.", h=1.9, c=DK.MUTED)
    sh.text(30, yb - 55, "GROUNDING", h=2.6, bold=True)
    for i, ln in enumerate(["Equipment ground through the UPS cord to the building receptacle ground; no separate electrode.",
                            "Rack / cabinet frame bonded to the UPS chassis ground (bond <= 0.1 ohm, CTQ-E1).",
                            "Every device is listed and cord-connected: no field wiring inside BEN 1 (CTP-E1)."]):
        sh.text(32, yb - 60 - i * 3.4, "• " + ln, h=1.9)

    def extra(sh, x, y):
        rows = [["Supply", d["voltage"]], ["Circuit", d["outlet_circuit"]], ["UPS", d["ups_model"]],
                ["Runtime", f"~{d['ups_runtime_min_est']} min at {cfg.it_kw:g} kW"], ["Battery energy", f"{d['battery_kwh']} kWh (NFPA 855 not in scope)"],
                ["Heat to room", f"{d['heat_to_room_w']} W / {d['heat_to_room_btu_h']} BTU/h (I-001)"]]
        y = sh.table(x, y, ["ITEM", "VALUE"], rows, [RW * 0.24, RW * 0.76], title="ELECTRICAL DATA", h=1.9)
        return y - 4
    G.right_column(sh, lay, "E-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "E-001"))


def ben1_c001(lay, out, n, total):
    d, cfg = lay.d, lay.cfg
    s = 2 if cfg.form == "rack10" else 5
    sh = sheet(lay, "C-001", BEN1_SHEETS[2][1], f"1:{s}", n, total)
    sh.view_title(30, TOP - 8, "POD PLACEMENT — FRONT AND SIDE", f"1:{s}")
    oy = TOP - 30 - lay.ext_h / s
    v = _ben1_front(sh, lay, 40, oy, s, labels=False)
    p1, p2 = lay.find("P1"), lay.find("P2")
    v.rect(p1.x0, p1.z0, p1.x1, p1.z1, fc=DK.FILL["controls"], ec=DK.EDGE["controls"], lw=0.8)
    v.leader(p1.cx, p1.z1, 30, 10, f"P1 Pod W inlet, front rail, z {p1.z0:.0f} mm", h=1.9)
    vs = DK.View(sh, s, 40 + lay.ext_l / s + 60, oy)
    vs.rect(0, 0, lay.ext_w, lay.ext_h, fc="#E8EDF3", ec=V2["ink"], lw=0.8)
    vs.rect(lay.ext_w - 40, p1.z0, lay.ext_w, p1.z1, fc=DK.FILL["controls"], ec=DK.EDGE["controls"], lw=0.8)
    vs.rect(0, p2.z0, 40, p2.z1, fc=DK.FILL["controls"], ec=DK.EDGE["controls"], lw=0.8)
    vs.text(lay.ext_w - 20, p1.z1 + 30, "P1", h=1.9, ha="center", bold=True)
    vs.text(20, p2.z1 + 30, "P2", h=1.9, ha="center", bold=True)
    vs.text(lay.ext_w / 2, -60, "front ->", h=1.8, ha="center", c=DK.MUTED)
    # network
    yn = 250.0
    sh.text(30, yn, "CONTROLS NETWORK — BEN CONTROLS MINI", h=3, bold=True)
    boxes = [("P1 / P2", "BEN Pod W, Thread"), ("EDGE", "fanless edge, BEN Care agent"), ("SWITCH", "8-port managed"), ("CUSTOMER ROUTER", "outbound TLS only"), ("BEN CARE", "cloud dashboard")]
    for i, (a, b) in enumerate(boxes):
        bx = 30 + i * 90
        DK.sym_box(sh, bx, yn - 36, 74, 26, a, [b], kind="controls" if i < 3 else "structure", title_h=2.2)
        if i:
            sh.arrow(bx - 16, yn - 23, bx - 1, yn - 23, c=DK.EDGE["controls"])
    sh.text(30, yn - 46, "UPS network card -> EDGE (SNMP/Modbus TCP): on-battery and low-battery events trigger the graceful shutdown of the hosts.", h=1.9)
    sh.text(30, yn - 51, "No life-safety function in BEN 1: smoke detection and suppression are the building's; the Pods report only temperature, RH and door / leak inputs.", h=1.9, c=DK.MUTED)

    def extra(sh, x, y):
        rows = [[sn.id, sn.kind, f"{sn.x:.0f}/{sn.y:.0f}/{sn.z:.0f}", sn.channel] for sn in lay.sensors[:10]]
        y = sh.table(x, y, ["SENSOR", "KIND", "x/y/z mm", "CHANNEL"], rows, [RW * 0.34, RW * 0.12, RW * 0.28, RW * 0.26], title="SENSOR SCHEDULE (PROTOCOL.md names)", h=1.8, rowh=3.8)
        return y - 4
    G.right_column(sh, lay, "C-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "C-001"))


def ben1_i001(lay, out, n, total):
    sh = sheet(lay, "I-001", BEN1_SHEETS[3][1], "NTS", n, total)
    d, cfg = lay.d, lay.cfg
    sh.view_title(30, TOP - 8, "INSTALLATION — CLOSET / OFFICE REQUIREMENTS", "NTS")
    # closet plan schematic (sheet mm)
    cx, cy, cw, ch = 40.0, 330.0, 200.0, 170.0
    sh.rect(cx, cy, cw, ch, fc="none", ec=V2["ink"], lw=1.6)
    sh.text(cx + 3, cy + ch - 5, "CLOSET (or office corner)", h=2.2, bold=True)
    sh.rect(cx + cw - 2, cy + 30, 4, 40, fc=DK.PAPER, ec=DK.PAPER, lw=0)
    sh.text(cx + cw + 4, cy + 50, "door with grille\nor undercut", h=1.8, va="center")
    uw, ud = 46.0, 40.0
    ux, uy = cx + 40, cy + 70
    sh.rect(ux, uy, uw, ud, fc=V2["night"], ec=V2["ink"], lw=0.8)
    sh.text(ux + uw / 2, uy + ud / 2, "BEN 1", h=2.4, ha="center", va="center", c=V2["paper"], bold=True)
    sh.rect(ux - 14, uy - 14, uw + 28, ud + 14 + 30, fc="none", ec=DK.CTQ_C, lw=0.5, ls=":")
    sh.text(ux + uw / 2, uy + ud + 34, "914 mm service clearance in front", h=1.7, ha="center", c=DK.CTQ_C)
    sh.text(ux + uw / 2, uy - 19, "300 mm rear (exhaust)", h=1.7, ha="center", c=DK.CTQ_C)
    sh.arrow(ux + uw / 2, uy + ud + 22, ux + uw / 2, uy + ud + 2, c=V2["thermal_cool"], lw=1.4)
    sh.arrow(ux + uw / 2, uy - 2, ux + uw / 2, uy - 12, c=V2["thermal_warm"], lw=1.4)
    sh.rect(cx + cw - 50, cy + ch - 18, 30, 10, fc=DK.FILL["cooling"], ec=DK.EDGE["cooling"], lw=0.6)
    sh.text(cx + cw - 35, cy + ch - 13, "TRANSFER FAN", h=1.6, ha="center", va="center")
    sh.text(cx + cw - 35, cy + ch - 22, f">= {d['closet_vent_cfm']} cfm", h=1.8, ha="center", bold=True)
    sh.rect(cx + 4, cy + 4, 18, 12, fc=DK.FILL["power"], ec=DK.EDGE["power"], lw=0.6)
    sh.text(cx + 13, cy + 10, f"{d['outlet_circuit_a']} A", h=1.7, ha="center", va="center")
    sh.text(cx + 26, cy + 8, "dedicated 120 V receptacle within cord reach (1.8 m)", h=1.7)
    # requirements table (left, below)
    rows = [["Heat to room", f"{d['heat_to_room_w']} W = {d['heat_to_room_btu_h']} BTU/h, continuous, 24 h/day"],
            ["Closet ventilation", f">= {d['closet_vent_cfm']} cfm transfer fan or door grille pair (holds the closet within 5 K of the office), or a dedicated 0.5 ton split unit"],
            ["Room temperature", f"office design {d['office_design_c']:.0f} C, max {d['office_max_c']:.0f} C at the BEN 1 inlet (ASHRAE {d['ashrae_class']})"],
            ["Electrical circuit", f"{d['outlet_circuit']}; {d['outlet_amps']} A at full load"],
            ["Clearances", "914 mm in front for service; 300 mm behind and at the air inlet; nothing on top of the unit"],
            ["Noise", f"{d['noise_dba_est']} dBA at 1 m est. (target {d['noise_dba_target']:.0f} dBA); quiet up to {d['noise_quiet_up_to_kw']} kW. Not beside a desk above 50 dBA."],
            ["Floor / shelf", f"{d['gross_kg']} kg; shelf or floor rated for 2 x this mass; level within 3 mm"],
            ["Network", "1 x Ethernet to the customer router; outbound TLS (443) for BEN Care"],
            ["Not allowed", "No water pipes above, no sprinkler-only cupboard without the vent, no extension cords, no daisy-chained strips"]]
    sh.table(30, 300, ["REQUIREMENT", "VALUE"], rows, [90, 370], title="SITE REQUIREMENTS (from Config.preset('ben1', form='%s'))" % cfg.form, h=2.0, rowh=4.4)
    sh.text(30, 236, "ROOM NOTE (from the configuration model)", h=2.6, bold=True)
    for i, ln in enumerate(_wrap(d["room_cooling_note"], 200)):
        sh.text(30, 231 - i * 3.2, ln, h=1.9)
    # key numbers
    tiles = [("HEAT TO ROOM", f"{d['heat_to_room_w']} W", f"{d['heat_to_room_btu_h']} BTU/h, 24 h/day"),
             ("CLOSET VENT", f">= {d['closet_vent_cfm']} cfm", "or a 0.5 ton split unit"),
             ("CIRCUIT", f"{d['outlet_circuit_a']} A, 120 V", f"dedicated; {d['outlet_amps']} A at full load"),
             ("CLEARANCES", "914 / 300 mm", "front service / rear and inlet"),
             ("NOISE AT 1 m", f"{d['noise_dba_est']} dBA", f"target {d['noise_dba_target']:.0f} dBA")]
    for i, (a, b, c) in enumerate(tiles):
        tx, ty = 270 + (i % 2) * 110, 470 - (i // 2) * 48
        sh.rect(tx, ty, 100, 40, fc="#F4F7FB", ec=V2["deep"], lw=0.8)
        sh.text(tx + 4, ty + 33, a, h=2.0, c=V2["slate"], mono=True)
        sh.text(tx + 4, ty + 18, b, h=6.0, c=V2["ink"], bold=True)
        sh.text(tx + 4, ty + 7, c, h=1.9, c=V2["slate"])

    def extra(sh, x, y):
        rows = [["1", "Customer confirms the dedicated circuit and receptacle type"], ["2", "Clearances measured: front 914, rear 300"], ["3", "Vent / split unit in place if closed closet"],
                ["4", "Network drop and outbound 443 open"], ["5", "Unit set level; burn-in record (CTQ-T1) handed over"], ["6", "Customer signs CTQ-I1 on form Q-12"]]
        y = sh.table(x, y, ["#", "SITE CHECKLIST"], rows, [RW * 0.08, RW * 0.92], title="SITE CHECKLIST (installer + customer)", h=1.9)
        return y - 4
    G.right_column(sh, lay, "I-001", extra)
    sh.title_block()
    sh.save(os.path.join(out, "I-001"))


BEN1_GENS = {"A-001": ben1_a001, "E-001": ben1_e001, "C-001": ben1_c001, "I-001": ben1_i001}


# ====================================================================== INDEX and driver
def _sheet_list(lay):
    if lay.is_minirack:
        return BEN1_SHEETS
    return G.sheets_for(lay)


def write_index(lay, out, rel):
    sheets = _sheet_list(lay)
    form = f" ({lay.cfg.form})" if lay.is_minirack else ""
    lines = [f"# {lay.d['tier_label']}{form} — drawing set Rev {REV['drawing_rev']} ({REV['status_title']})", "",
             f"Generated {REV['issue_date']} by `design/drawings/gen_drawings_rev2.py --lineup rev2` from `Config.preset('{lay.tier}', lineup='rev2'"
             + (f", form='{lay.cfg.form}'" if lay.is_minirack else "") + f")`; revision from `{REV['path']}`. Brand v2 title block (brand/v2/titleblock-spec.md). "
             f"The Rev 1 set of this tier, where one exists, stays in `design/drawings/{lay.tier}/` (frozen).",
             f"Configuration: {config_line(lay)}", f"Enclosure: {lay.d['enclosure']} — {lay.d['hardening_rating']} ({lay.d['hardening_label']}).", "",
             "| Sheet | Title | Files |", "|---|---|---|"]
    for i, (no, title) in enumerate(sheets, 1):
        lines.append(f"| {no} | {title} (sheet {i}/{len(sheets)}) | [{no}.svg]({no}.svg), [{no}.png]({no}.png) |")
    checked = f"Checked: {REV['checker']}" if REV["checked"] else "Checked: blank (the operator signs; the set is not for construction until a checker is named in design/rev2/REVISION.json)"
    lines += ["", f"Status: **{REV['status_long']}** — Rev {REV['drawing_rev']}, {REV['issue_date']}. Drawn: BEN Engine generator; {checked}.", "",
              "| Rev | Date | Description | Checked |", "|---|---|---|---|",
              f"| {REV['drawing_rev']} | {REV['issue_date']} | {REV['notes_short']} | {REV['checker'] or 'not checked'} |", ""]
    if lay.is_container or lay.is_hall:
        lines += ["## EN-001 working space (docs/audit/EN-001_working_space_liner.md)", "", en001_status(lay), ""]
    if lay.deviations:
        lines += ["## Configuration deviations applied on this set", ""] + [f"- {dv}" for dv in lay.deviations] + [""]
    lines += ["## Interference checks for this tier (design/layout.py)", "", L.checks_table([lay]), ""]
    with open(os.path.join(out, "INDEX.md"), "w") as f:
        f.write("\n".join(lines))


def en001_status(lay):
    if lay.is_hall:
        return ("BEN 2000 hall: cold aisles are designed to condition 2 (1,100 >= 1,067, I-H4) and the 4,000 A switchgear to condition 3 (I-H7); the liner does not set "
                "the working space. Open item: the 900 mm contained hot aisle is egress only; if rack-rear PDU breakers are to be serviced energised, condition 2 (1,067) applies there — "
                "see EN-001 §5.")
    vg = L.volts_to_ground(lay)
    if lay.notes.get("nc_liner"):
        return (f"{vg:.0f} V to ground. Condition 1 (914 mm) is justified by ENV-LINER-NC on the aisle wall and no grounded device on that wall (checks "
                + ("I-D4, I-D6, I-D20" if lay.notes.get("dense") else "I-C5, I-C27") + "); 480 V gear at condition 2 where drawn. Resolved in Rev 2.")
    if lay.is_container:
        return f"{vg:.0f} V to ground: 914 mm under every condition (I-C5); not affected. Wall devices kept off the aisle wall (I-C27)."
    return "Not affected."


def generate(lay, out, sheets_only=None, dpi=110):
    os.makedirs(out, exist_ok=True)
    if lay.is_minirack:
        gens = {no: (lambda lay, out, fn=fn, n=i: fn(lay, out, n, len(BEN1_SHEETS))) for i, (no, fn) in enumerate(BEN1_GENS.items(), 1)}
    elif lay.is_hall:
        gens = G.hall_generators(lay)
    else:
        gens = dict(G.GENERATORS)
        if lay.is_dense:
            gens["E-001"] = sheet_e001_dense
            gens["M-001"] = sheet_m001_dense
    for no in [s_ for s_ in (sheets_only or list(gens)) if s_ in gens]:
        gens[no](lay, out)
        print(f"  wrote {os.path.relpath(out, REPO)}/{no}.svg/.png")


def layouts():
    out = []
    for t in L.TIERS_BY_LINEUP["rev2"]:
        if t == "ben1":
            for form in ("rack10", "cab12"):
                out.append((t, form, L.resolve_rev2(t, form=form)))
        else:
            out.append((t, None, L.resolve_rev2(t)))
    return out


def prepare(lay):
    if lay.is_container:
        vg = L.volts_to_ground(lay)
        lay.notes["ws_label"] = (f"NEC 110.26 WORKING SPACE 914 (condition 1, {vg:.0f} V to ground; ENV-LINER-NC opposite, EN-001)" if lay.notes.get("nc_liner")
                                 else f"NEC 110.26 WORKING SPACE 914 ({vg:.0f} V to ground: all conditions)")
    return lay


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lineup", default="rev2", choices=["rev2"])
    ap.add_argument("--tier", action="append")
    ap.add_argument("--sheet", action="append")
    ap.add_argument("--dpi", type=int, default=110)
    a = ap.parse_args(argv)
    apply_brand_v2()
    _patch_right_column()
    all_lays = layouts()
    sel = [x for x in all_lays if not a.tier or x[0] in a.tier]
    for t, form, lay in sel:
        prepare(lay)
        out = os.path.join(OUT_ROOT, t, form) if form else os.path.join(OUT_ROOT, t)
        generate(lay, out, a.sheet, a.dpi)
        write_index(lay, out, os.path.relpath(out, HERE))
    if not a.tier:
        lays = [x[2] for x in all_lays]
        with open(os.path.join(OUT_ROOT, "INTERFERENCE_CHECKS.md"), "w") as f:
            f.write(f"# Interference checks — Rev 2 lineup, drawing set Rev {REV['drawing_rev']} (generated by gen_drawings_rev2.py)\n\n")
            f.write("Result key: OK = passes; OK* = passes after the documented resolution; FAIL = does not pass as given (informative checks say 'Not used' / 'Not required').\n\n")
            f.write(L.checks_table(lays) + "\n\n## Deviations applied\n\n" + L.deviations_md(lays) + "\n")
        idx = [f"# BEN Engine Rev 2 — drawing set Rev {REV['drawing_rev']} ({REV['status_title']}, {REV['issue_date']})", "",
               f"Record: `{REV['path']}` (change register R2-01..R2-04). Generator: `python design/drawings/gen_drawings_rev2.py --lineup rev2`. "
               "Rev 1 sets in `design/drawings/<tier>/` are frozen (docs/REVISION_POLICY.md).", "",
               "| Tier | Folder | Sheets | EN-001 |", "|---|---|---|---|"]
        for t, form, lay in all_lays:
            folder = f"{t}/{form}" if form else t
            nsh = len(_sheet_list(lay))
            idx.append(f"| {lay.d['tier_label']}{' ' + form if form else ''} | [{folder}/]({folder}/INDEX.md) | {nsh} | {en001_status(lay).split('.')[0]} |")
        idx += ["", "All interference checks: [INTERFERENCE_CHECKS.md](INTERFERENCE_CHECKS.md).", ""]
        with open(os.path.join(OUT_ROOT, "INDEX.md"), "w") as f:
            f.write("\n".join(idx))
        print("  wrote design/drawings/rev2/INDEX.md, INTERFERENCE_CHECKS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
