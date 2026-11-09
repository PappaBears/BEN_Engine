# BEN 1 (rack10) — drawing set Rev 2.A (ISSUED FOR REVIEW)

Generated 2026-11-09 by `design/drawings/gen_drawings_rev2.py --lineup rev2` from `Config.preset('ben1', lineup='rev2', form='rack10')`; revision from `design/rev2/REVISION.json`. Brand v2 title block (brand/v2/titleblock-spec.md). The Rev 1 set of this tier, where one exists, stays in `design/drawings/ben1/` (frozen).
Configuration: ben1 rack10 | ai_inference | 0.6 kW IT | 120 V 1ph 15/20 A plug-in | APC SMTL1000RM2UC | temperate | lineup rev2
Enclosure: 10-inch 8U desk / shelf mini rack (open or semi-enclosed) (DeskPi RackMate T1 (10-inch 8U) class) — UL 62368-1 listed parts, IP20 indoor, NEMA 12 option for dusty closets (Indoor (no hardening levels)).

| Sheet | Title | Files |
|---|---|---|
| A-001 | General arrangement — rack / cabinet, dimensions and clearances (sheet 1/4) | [A-001.svg](A-001.svg), [A-001.png](A-001.png) |
| E-001 | Plug-in one-line — UPS and outlet circuit (sheet 2/4) | [E-001.svg](E-001.svg), [E-001.png](E-001.png) |
| C-001 | Controls — BEN Pod placement (sheet 3/4) | [C-001.svg](C-001.svg), [C-001.png](C-001.png) |
| I-001 | Installation — closet / office requirements (sheet 4/4) | [I-001.svg](I-001.svg), [I-001.png](I-001.png) |

Status: **ISSUED FOR REVIEW — not for construction until checked** — Rev 2.A, 2026-11-09. Drawn: BEN Engine generator; Checked: blank (the operator signs; the set is not for construction until a checker is named in design/rev2/REVISION.json).

| Rev | Date | Description | Checked |
|---|---|---|---|
| 2.A | 2026-11-09 | Rev 2.A: first issue of the BEN Engine Rev 2 design set (docs/REV2_DECISION.md) for review — Rev 2 lineup BEN 1 (both forms), BEN 5, BEN 30, BEN 150, BEN 300, BEN 500, BEN 700 and BEN 2000; brand v2 title blocks with the data plate band; liquid-first dense tiers BEN 300 and BEN 700; non-conductive liner on the wall opposite live parts per EN-001. | not checked |

## Interference checks for this tier (design/layout.py)

| Tier | ID | Sheet | Check | Numbers | Limit | Result | Resolution |
|---|---|---|---|---|---|---|---|
| BEN 1 | I-B1 | A-002 | Rack units used (pdu10 + switch + spark + spark + edge) vs 8U | 7U vs 8U | <= 8 | **OK** |  |
| BEN 1 | I-B2 | A-002 | Deepest device vs usable depth (200 mm) | 150 vs 200 | <= 200 | **OK** |  |
| BEN 1 | I-B3 | E-001 | IT load vs rack10 rating | 0.6 vs 0.6 kW | <= 0.6 | **OK** |  |
| BEN 1 | I-B4 | E-001 | Outlet current at 120 V vs 80 % of the 15 A circuit (NEC 210.19 / 210.20 continuous load) | 5.7 A vs 12 A | <= 12 | **OK** |  |
| BEN 1 | I-B5 | E-001 | UPS real power (800 W) vs IT x 1.25 headroom | 800 vs 750 | >= 750 | **OK** |  |
| BEN 1 | I-B7 | A-001 | Estimated noise at 1 m vs the 50 dBA target | 45.2 vs 50.0 | <= 50 | **OK** |  |
