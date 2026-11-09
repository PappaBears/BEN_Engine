# BEN 1 (cab12) — drawing set Rev 2.A (ISSUED FOR REVIEW)

Generated 2026-11-09 by `design/drawings/gen_drawings_rev2.py --lineup rev2` from `Config.preset('ben1', lineup='rev2', form='cab12')`; revision from `design/rev2/REVISION.json`. Brand v2 title block (brand/v2/titleblock-spec.md). The Rev 1 set of this tier, where one exists, stays in `design/drawings/ben1/` (frozen).
Configuration: ben1 cab12 | ai_inference | 1 kW IT | 120 V 1ph 15/20 A plug-in | APC SMTL2200RM2UC | temperate | lineup rev2
Enclosure: 19-inch 12U sound-damped office cabinet (APC NetShelter CX Mini 12U (AR4000MVX431) class) — UL 62368-1 listed parts, IP20 indoor, NEMA 12 option for dusty closets (Indoor (no hardening levels)).

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
| BEN 1 | I-B1 | A-002 | Rack units used (ups2u + switch + nas1u + gpu2u + edge + patch) vs 12U | 8U vs 12U | <= 12 | **OK** |  |
| BEN 1 | I-B2 | A-002 | Deepest device vs usable depth (550 mm) | 472 vs 550 | <= 550 | **OK*** | 2U short-depth edge servers only (472 mm class); standard 2U GPU servers (700-800 mm) do not fit |
| BEN 1 | I-B3 | E-001 | IT load vs cab12 rating | 1.0 vs 1.5 kW | <= 1.5 | **OK** |  |
| BEN 1 | I-B4 | E-001 | Outlet current at 120 V vs 80 % of the 15 A circuit (NEC 210.19 / 210.20 continuous load) | 9.4 A vs 12 A | <= 12 | **OK** |  |
| BEN 1 | I-B5 | E-001 | UPS real power (1920 W) vs IT x 1.25 headroom | 1920 vs 1250 | >= 1250 | **OK** |  |
| BEN 1 | I-B6 | M-001 | Cabinet extraction (one fan of the N+1 pair at 100 %, 1.6 kW at 10 K) vs IT x 1.05 | 1.6 vs 1.05 kW | >= 1.05 | **OK** |  |
| BEN 1 | I-B7 | A-001 | Estimated noise at 1 m vs the 45 dBA target | 44.1 vs 45.0 | <= 45 | **OK** |  |
