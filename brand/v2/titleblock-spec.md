# Drawing title block: brand v2 specification (Rev 2.A drawing set)

For the design generators (`design/drawings/drawkit.py` → `Sheet.title_block()`, `design/gen_sqam.py`, `design/specs/wiring/gen_wiring.py`). The brand agent did not edit them; this is the spec the lead applies when Rev 2.A starts. Drawings print on white, so every color here is the **light-ground** set.

## 1. Colors for print on white

| Role | Rev 1 value in `drawkit.py` | Rev 2 value | Token |
| --- | --- | --- | --- |
| Line work, text (`INK`) | `#0B1018` | `#0B1A31` | Ink |
| Secondary text, labels (`MUTED`) | `#5C7391` | `#4A5D7A` | Slate |
| Light rules (`LIGHT`) | `#9FB3CC` | `#B2C1D8` | Fog |
| The mark, accent rules | `#66E3FF` cyan | `#1E40AF` | Deep Cobalt (the mark on white) |
| Title block brand panel ground | `#0B1018` | `#06101F` | Night Navy (print: rich black C60 M40 Y20 K100, see BRAND_GUIDE) |
| Status line ("ISSUED FOR REVIEW") | `#FFC66D` amber | `#F2C94C` on the navy panel | Hold. Amber is the button color only |
| CTQ bubbles (`CTQ_C`) | `#0B8FA8` | `#1E40AF` | Deep Cobalt |
| CTP bubbles (`CTP_C`) | `#B8860B` | `#8A6A00` (Hold darkened for print, 5.0:1 on white) | — |
| Red / stop (`RED`) | `#C8102E` | `#C8323A` | Stop (light ground) |
| Green / run (`GREEN`) | `#1E8E5A` | `#1B7F50` (Run darkened for print, 5.0:1 on white) | — |
| Hot / cold on plans and CFD | cyan / amber | thermal ramp `#5CD6FF` → `#FF8A3D`, always with a legend | Thermal |

The equipment fill tints (`FILL`) may stay; they are not brand colors.

## 2. Fonts (matplotlib)

Register the brand TTFs once at import, then use the families below. All files are in `brand/v2/fonts/ttf/` (SIL OFL, see `brand/v2/fonts/LICENSES.md`).

```python
from matplotlib import font_manager as fm
TTF = REPO / "brand/v2/fonts/ttf"
for f in TTF.glob("*.ttf"):
    fm.fontManager.addfont(str(f))
DISPLAY = fm.FontProperties(fname=TTF / "Archivo-ExtraBold-Expanded125.ttf")   # titles, tier label
H2      = fm.FontProperties(fname=TTF / "Archivo-Bold.ttf")                    # sheet section heads
BODY    = "IBM Plex Sans"        # notes, table text  (fallback: DejaVu Sans)
MONO    = "IBM Plex Mono"        # drawing No., rev, dates, config line, dimensions (fallback: DejaVu Sans Mono)
plt.rcParams["font.family"] = [BODY, "DejaVu Sans"]
plt.rcParams["svg.fonttype"] = "path"   # outline text in the SVG so the sheet never depends on installed fonts
```

`svg.fonttype = "path"` changes the SVG bytes; re-baseline any hash check (audit F-21) when switching. Text heights: keep the Rev 1 heights (title 4.0 mm, fields 3.2 mm, labels 1.8 mm, minimum 1.8 mm on A1, which stays ≥ 1.3 mm when printed at A3).

## 3. Layout of the 260 × 58 mm title block (A1 sheet, bottom right)

```
┌──────────── 62 ────────────┬───────────────────────── 198 ─────────────────────────┐
│ [lockup-white, mark 9 mm]  │ TITLE (label 1.8 Plex Mono caps, Slate)                │
│                            │ Sheet title  (Archivo Bold 4.0 mm, Ink)                │
│ BEN ENGINE (Archivo XB 125,├──────┬───┬────────┬──────┬────────┬──────────────────┤
│   3.4 mm cap, Paper)       │DWG No│REV│ SCALE  │SHEET │ DATE   │ STATUS           │
│ BEN 300 (Archivo Black 125,│ mono │   │        │      │        │                  │
│   5.0 mm cap, Paper)       ├──────┴───┴────────┴──────┴────────┴──────────────────┤
│ ISSUED FOR REVIEW (Hold)   │ DRAWN / CHECKED / APPROVED (Plex Sans 2.1)            │
│ Rev 2.A · 2026-mm-dd (Fog) │ CONFIG: … (Plex Mono 1.9, Slate)                       │
├────────────────────────────┴───────────────────────────────────────────────────────┤
│ ● SCHREIBER AI │ BEN ENGINE │ BEN 300 │ DWG M-001 │ REV 2.A │ RATED 300 kW IT │ SHEET 3 / 12 ● │  ← data plate band, 6 mm
└────────────────────────────────────────────────────────────────────────────────────┘
```

* **Brand panel (left, 62 mm, Night Navy).** Replace the Rev 1 "SAI" box and live "Schreiber AI" text with the **white horizontal lockup** `brand/v2/lockup-white.svg`, mark height 9 mm (lockup 58.7 × 9 mm would overflow: use the **mark** `brand/v2/mark-white.svg` 12 mm at top left plus the product line, or the lockup at mark height 7.6 mm = 49.6 mm wide, inset 6 mm). Below it: `BEN ENGINE` (Archivo ExtraBold wdth 125, +2 % tracking, Paper `#EEF4FC`), then the tier in Archivo Black wdth 125, then status in Hold `#F2C94C`, then `Rev 2.A · date` in Fog.
* **Fields (right, 198 mm).** Unchanged structure; label text Plex Mono caps Slate, values Plex Mono SemiBold Ink. Drawing No., Rev and dates are always mono.
* **Data plate band (new, full 260 mm width, 6 mm tall, directly under the block; block grows to 64 mm).** Night Navy ground, Border `#24406B` rules top and bottom, Plex Mono SemiBold 2.0 mm caps +16 % tracking in Fog, lead "SCHREIBER AI" in Signal Blue `#4C9DFF`, rivets 2 mm Night Navy circles with a Steel ring at each end, 1-unit dividers in Border. Fields: `Schreiber AI · BEN Engine · <tier> · DWG <no> · Rev <rev> · Rated <kW> kW IT · Sheet n / N`. Note: on white paper the navy band prints as rich black; that is intended.
* **Legal line** in the bottom margin under the frame, right-aligned, Plex Sans 1.8 mm Slate: `Schreiber AI is a Schreiber Holding LLC company.`

## 4. Placing the logo master in matplotlib (never redraw it)

matplotlib cannot read SVG. Two supported routes:

1. **Vector (preferred for the SVG sheets).** Draw a placeholder with an id, then post-process the saved SVG:
   ```python
   self.ax.add_patch(Rectangle((x, y), w, h, fill=False, lw=0, gid="bv2-lockup-slot"))
   # after savefig(...svg): replace <g id="bv2-lockup-slot">…</g> with
   #   brandlib.embed("lockup-white", x_px, y_px, h_px, prefix="tb_")   (brand/v2/brandlib.py)
   ```
   Convert sheet mm to the SVG's pt user units (matplotlib writes 72 pt/in, y flipped).
2. **Raster (the PNG sheets).** `self.ax.imshow(plt.imread("brand/v2/png/lockup-white-2000.png"), extent=(x, x + w, y, y + h), zorder=11)`. The PNG masters in `brand/v2/png/` (transparent, 2000 px wide lockups, 1600 px stacks, 512 px marks) are rendered from the SVG masters by `brand/v2/render_png.mjs`.

## 5. Other generated graphics

* `design/specs/wiring/gen_wiring.py` reads its palette from constants commented "web/kit/brand.json": switch to `brand/v2/tokens.json` (`color.surface.*`, `color.signal.400`, `color.status.*`), replace the SAI monogram (lines 43–45) with `mark-signal` via route 1, and use Hold `#F2C94C` for the "power" accent that was amber.
* `design/gen_sqam.py` document headers: lockup-deep on white, legal line in the footer, data plate band as in §3.
* `scripts/gen_heroes.py` (web hero isometrics, still Rev 1 livery): body Shop White `#F4F7FB` with the Night Navy band for outdoor tiers, BEN 1 Night Navy; side artwork follows `brand/v2/livery/<tier>-side.svg`.
