# BEN 5 — drawing set Rev 2.A (ISSUED FOR REVIEW)

Generated 2026-11-09 by `design/drawings/gen_drawings_rev2.py --lineup rev2` from `Config.preset('ben5', lineup='rev2')`; revision from `design/rev2/REVISION.json`. Brand v2 title block (brand/v2/titleblock-spec.md). The Rev 1 set of this tier, where one exists, stays in `design/drawings/ben5/` (frozen).
Configuration: ben5 | ai_inference | 5 kW IT | 1 racks | cooling cabinet_dx | N+1 | temperate | H1 | lineup rev2
Enclosure: Outdoor 24U NEMA 4X / IP66 cabinet on skid — NEMA 4X / IP66 (H1 Standard).

| Sheet | Title | Files |
|---|---|---|
| A-001 | General arrangement (sheet 1/7) | [A-001.svg](A-001.svg), [A-001.png](A-001.png) |
| A-002 | Interior layout plan (sheet 2/7) | [A-002.svg](A-002.svg), [A-002.png](A-002.png) |
| A-003 | Envelope section and hardening (sheet 3/7) | [A-003.svg](A-003.svg), [A-003.png](A-003.png) |
| S-001 | Floor framing and anchoring (sheet 4/7) | [S-001.svg](S-001.svg), [S-001.png](S-001.png) |
| E-001 | Power one-line (sheet 5/7) | [E-001.svg](E-001.svg), [E-001.png](E-001.png) |
| M-001 | Cooling P&ID (sheet 6/7) | [M-001.svg](M-001.svg), [M-001.png](M-001.png) |
| C-001 | Controls layout (sheet 7/7) | [C-001.svg](C-001.svg), [C-001.png](C-001.png) |

Status: **ISSUED FOR REVIEW — not for construction until checked** — Rev 2.A, 2026-11-09. Drawn: BEN Engine generator; Checked: blank (the operator signs; the set is not for construction until a checker is named in design/rev2/REVISION.json).

| Rev | Date | Description | Checked |
|---|---|---|---|
| 2.A | 2026-11-09 | Rev 2.A: first issue of the BEN Engine Rev 2 design set (docs/REV2_DECISION.md) for review — Rev 2 lineup BEN 1 (both forms), BEN 5, BEN 30, BEN 150, BEN 300, BEN 500, BEN 700 and BEN 2000; brand v2 title blocks with the data plate band; liquid-first dense tiers BEN 300 and BEN 700; non-conductive liner on the wall opposite live parts per EN-001. | not checked |

## Interference checks for this tier (design/layout.py)

| Tier | ID | Sheet | Check | Numbers | Limit | Result | Resolution |
|---|---|---|---|---|---|---|---|
| BEN 5 | I-M1 | A-002 | Rack units available for IT after UPS (2 x 4U), battery packs (2 x 3U) and controls shelf (1U) | 24U - 15U | >= 6 | **OK*** | 9U for IT at 5 kW: 2 x 2U servers + 1U switch + 1U patch fits; was 12U rule |
| BEN 5 | I-M2 | A-001 | Cabinet DX units fit on cabinet exterior long face | 1 x 400 + 2 x 100 gap vs ext 1200 | <= 1200 | **OK** |  |
| BEN 5 | I-M3 | A-003 | Rack depth + front/rear air gap vs cabinet interior width | 600 + 100 + 100 vs 800 | <= 800 | **OK** |  |
| BEN 5 | I-M4 | S-001 | Skid + cabinet gross mass vs 2.5 t forklift / tail-lift | gross 1087 kg | <= 2500 | **OK** |  |
