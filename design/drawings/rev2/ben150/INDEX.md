# BEN 150 — drawing set Rev 2.A (ISSUED FOR REVIEW)

Generated 2026-11-09 by `design/drawings/gen_drawings_rev2.py --lineup rev2` from `Config.preset('ben150', lineup='rev2')`; revision from `design/rev2/REVISION.json`. Brand v2 title block (brand/v2/titleblock-spec.md). The Rev 1 set of this tier, where one exists, stays in `design/drawings/ben150/` (frozen).
Configuration: ben150 | ai_inference | 96 kW IT | 5 racks | cooling rdhx_drycooler | N+1 | temperate | H1 | lineup rev2
Enclosure: 20 ft high-cube ISO-frame module, sealed to IP66 — NEMA 4X / IP66 (H1 Standard).

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

## EN-001 working space (docs/audit/EN-001_working_space_liner.md)

277 V to ground. Condition 1 (914 mm) is justified by ENV-LINER-NC on the aisle wall and no grounded device on that wall (checks I-C5, I-C27); 480 V gear at condition 2 where drawn. Resolved in Rev 2.

## Interference checks for this tier (design/layout.py)

| Tier | ID | Sheet | Check | Numbers | Limit | Result | Resolution |
|---|---|---|---|---|---|---|---|
| BEN 150 | I-C0 | A-003 | Config interior height vs envelope build-up (2698 shipped - 100 floor - 110 roof), 10 mm tolerance | config 2490 vs computed 2488 | <= 2498 | **OK** |  |
| BEN 150 | I-C1 | A-002 | Config row_length_mm (racks + cooling units + 500 end zone) vs interior length, config rule | 3500 vs 5750 | <= 5750 | **OK** |  |
| BEN 150 | I-C2 | A-002 | Row length with layout footprints (rdhx_drycooler: 5 racks, 4 cooling units, power cabinets) vs usable length | 4800 vs 5250 | <= 5250 | **OK** |  |
| BEN 150 | I-C21 | A-002 | Row length with catalog UPS/battery quantities (0 x Galaxy VS 100 kW @521 + 0 x Li cab @600, catalog qty rules) vs usable length | 4200 vs 5250 | <= 5250 | **OK** |  |
| BEN 150 | I-C4 | A-002 | Cold aisle / egress width (int W - plenum - row depth) vs 900 egress | 2200 - 0 - 1270 = 930 | >= 900 | **OK** |  |
| BEN 150 | I-C22 | A-002 | Aisle width with the catalog rack (STR-RACK42: 600 x 1070 deep + RDHx) vs 900 egress / 914 NEC | 2200 - 0 - 1070 = 930 | >= 914 | **OK** |  |
| BEN 150 | I-C5 | A-002 | Working space depth in front of the row, NEC 110.26 condition 1 at 277 V to ground: non-conductive Class A liner ENV-LINER-NC opposite (EN-001); liner build-up 15 mm <= 19 mm steel rib it replaces | 930 vs 914 | >= 914 | **OK*** | ENV-LINER-NC on the aisle wall; AHJ accepts the FRP liner over insulation as not grounded |
| BEN 150 | I-C6 | A-002 | Working space depth NEC 110.26 condition 2 (grounded parts opposite) - informative, the depth a steel liner would need | 930 vs 1067 | >= 1067 | **FAIL** | Not required with ENV-LINER-NC; a galvanised steel liner here would make the module non-compliant (EN-001) |
| BEN 150 | I-C27 | A-002 | Grounded or live devices on the aisle wall opposite the row inside its working space (EN-001) | 0 (none) | <= 0 | **OK** |  |
| BEN 150 | I-C7 | A-002 | Door zone (free length between door and first row item) vs 0 | 5750 - 500 - 4800 = 450 | >= 0 | **OK** |  |
| BEN 150 | I-C8 | A-002 | Two-row layout (2 x rack depth + 1000 cold aisle) vs interior width | 3140 vs 2200 | <= 2200 | **FAIL** | Not used; single row chosen |
| BEN 150 | I-C9 | A-002 | Rack 1070 + aisle 1000 + cooling unit 1070 across the width vs interior width | 3140 vs 2200 | <= 2200 | **FAIL** | Not used; cooling units are in-row, not across the width |
| BEN 150 | I-C10 | A-002 | Rack working space width (762 min) vs rack width | 762 vs 600 rack + aisle continuous | >= 762 | **OK*** | Aisle is continuous along the row; width requirement met by the open aisle |
| BEN 150 | I-C11 | A-003 | Overhead tray underside (over the aisle) vs rack top, cables drop to rack top entry | 2250 - 2000 = 250 | >= 0 | **OK*** | Trays run over the aisle, not over racks; head clearance under tray 2250 >= 2100 |
| BEN 150 | I-C12 | A-003 | Tray top vs ceiling liner (clearance >= 100 for installation) | 2490 - 2350 = 140 | >= 100 | **OK** |  |
| BEN 150 | I-C13 | A-002 | Door swing: ISO cargo doors swing outward; interior door zone needed | 0 vs 0 | >= 0 | **OK*** | Cargo doors open outward 270 deg; no interior swing |
| BEN 150 | I-C14 | A-003 | Rack height vs interior height (>= 300 for top cable entry and lights over the row) | 2490 - 2000 = 490 | >= 300 | **OK** |  |
| BEN 150 | I-C15 | S-001 | Gross mass vs ISO 668 max gross for the container size (30480 kg) | 8342 vs 30480 | <= 30480 | **OK** |  |
| BEN 150 | I-C16 | S-001 | Row strip floor load (payload over row footprint) vs ISO 1496-1 uniform payload rating (~20 kN/m2) | 6.9 kN/m2 vs 20 | <= 20 | **OK*** | Rack feet are point loads: C100 floor channels on cross-members spread them; verify in structural calc |
| BEN 150 | I-C18 | M-001 | RDHx doors per rack vs config cooling_units_total | 5 doors vs 4 config units | >= 4 | **OK*** | RDHx is one door per rack (catalog CLG-RDHX qty = racks); config counts 35 kW units for capacity only |
| BEN 150 | I-C20 | A-001 | Roof penetrations min 300 mm from side top rail | line-set curbs at y=300 interior = 419 from ext side face | >= 300 | **OK*** | Line-set roof curbs 300 mm inboard of top side rail, between corrugation roof bows; see A-001 |
