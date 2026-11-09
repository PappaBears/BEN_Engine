# BEN 700 — drawing set Rev 2.A (ISSUED FOR REVIEW)

Generated 2026-11-09 by `design/drawings/gen_drawings_rev2.py --lineup rev2` from `Config.preset('ben700', lineup='rev2')`; revision from `design/rev2/REVISION.json`. Brand v2 title block (brand/v2/titleblock-spec.md). The Rev 1 set of this tier, where one exists, stays in `design/drawings/ben700/` (frozen).
Configuration: ben700 | ai_inference | 700 kW IT | 5 racks | cooling dlc_hd | N+1 | temperate | H1 | lineup rev2
Enclosure: 40 ft high-cube ISO-frame module, liquid-first, all-in-one, sealed to IP66 — NEMA 4X / IP66 (H1 Standard).

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

277 V to ground. Condition 1 (914 mm) is justified by ENV-LINER-NC on the aisle wall and no grounded device on that wall (checks I-D4, I-D6, I-D20); 480 V gear at condition 2 where drawn. Resolved in Rev 2.

## Configuration deviations applied on this set

- DEV-D1: GB300 NVL72 racks are drawn 600 x 1068 (NVIDIA MGX / Supermicro / Cisco datasheet). The Vertiv SmartIT enclosure is 1,200 deep with its rear extension: W 2200 - 200 plenum - 1,200 = 800 mm aisle, below the 900 mm egress, so it is not used in a 2.2 m module.

## Interference checks for this tier (design/layout.py)

| Tier | ID | Sheet | Check | Numbers | Limit | Result | Resolution |
|---|---|---|---|---|---|---|---|
| BEN 700 | I-C0 | A-003 | Config interior height vs envelope build-up (2698 shipped - 100 floor - 110 roof), 10 mm tolerance | config 2490 vs computed 2488 | <= 2498 | **OK** |  |
| BEN 700 | I-D1 | A-002 | Config row_length_mm (dense rule: row items + 350 end zone) vs interior length | 11665 vs 11850 | <= 11850 | **OK** |  |
| BEN 700 | I-D2 | A-002 | Row length with real footprints (5 racks 600, 3 CDU 600, 5 fan coil 300, 2 UPS 850, 4 battery 600, 1 switchboard 915) vs usable length (interior - 350 end zone) | 11315 vs 11500 | <= 11500 | **OK** |  |
| BEN 700 | I-D3 | A-002 | Aisle in the rack zone (W - 200 plenum - 1068 rack) vs 900 egress | 2200 - 200 - 1068 = 932 | >= 900 | **OK** |  |
| BEN 700 | I-D4 | A-002 | NEC 110.26 working space in front of the racks (480Y/277 V power shelves), condition 1: non-conductive Class A FRP liner ENV-LINER-NC opposite (EN-001), no grounded device on that wall | 932 vs 914 | >= 914 | **OK** |  |
| BEN 700 | I-D5 | E-001 | NEC 110.26 condition 2 in front of the 480 V gear (switchboard, UPS, battery DC breakers), applied conservatively although the liner opposite is non-conductive (bonded door-end frame within reach): gear backs onto the wall | 2200 - 1000 = 1200 vs 1067 | >= 1067 | **OK** |  |
| BEN 700 | I-D20 | A-002 | Grounded or live devices on the aisle wall opposite the row inside its working space (EN-001) | 0 (none) | <= 0 | **OK** |  |
| BEN 700 | I-D6 | A-002 | Aisle in front of the row CDUs (1200 deep, back to the wall) vs 914 (condition 1, 480 V pump drives behind closed covers) | 2200 - 1200 = 1000 | >= 914 | **OK** |  |
| BEN 700 | I-D7 | E-001 | NEC 110.26(C)(2): a second entrance to the working space is needed for equipment >= 1,200 A AND over 1.8 m wide; switchboard 1200 A, 915 mm wide | 915 vs 1800 | <= 1800 | **OK*** | 1,200 A main but 915 mm wide: one entrance (the aisle) is permitted; the cargo doors give a second |
| BEN 700 | I-D8 | A-003 | Rack-top clearance (2236 mm MGX rack) vs 250 (top power entry; lights over the aisle; liquid enters low from the plenum) | 2490 - 2236 = 254 | >= 250 | **OK** |  |
| BEN 700 | I-D9 | A-003 | Overhead tray top vs ceiling liner (>= 100 for installation); trays run over the aisle, not the racks | 2490 - 2350 = 140 | >= 100 | **OK** |  |
| BEN 700 | I-D10 | M-001 | Residual air (10% of IT x 1.05) vs fan coils x (N) at 20 kW (18 C trim loop) | 4 x 20 vs 73.5 | >= 73.5 | **OK** |  |
| BEN 700 | I-D11 | M-001 | Row CDU capacity (N units x 600 kW) vs liquid heat x 1.05 | 2 x 600 vs 662 | >= 661.5 | **OK** |  |
| BEN 700 | I-D12 | E-001 | UPS frames (N x 500 kVA) vs IT / 0.95 x 1.15 | 2 x 500 vs 847 | >= 847.368 | **OK** |  |
| BEN 700 | I-D13 | E-001 | Battery cabinet discharge power (4 x 200 kW per path) vs IT load | 800 vs 700 | >= 700 | **OK** |  |
| BEN 700 | I-D14 | E-001 | NFPA 855 group energy: one lithium cabinet per group vs 50 kWh; groups adjacent in the row | 32.6 kWh vs 50 | <= 50 | **OK*** | Adjacent groups need UL 9540A large-scale fire test data for reduced spacing (Galaxy Li-ion is listed as a UL 9540 ESS with Galaxy VL; the 9540A report is to be obtained); otherwise 914 mm between groups, which does not fit the row |
| BEN 700 | I-D15 | S-001 | Gross mass vs ISO 668 max gross (30,480 kg) | 19300 vs 30480 | <= 30480 | **OK** |  |
| BEN 700 | I-D16 | S-001 | Rack floor load: 1500 kg GB300-class rack on a 600 x 1,600 mm load-spreading frame (on its own 0.6 x 1.068 m footprint it is 23.0 kN/m2) vs 20 kN/m2 | 15.3 vs 20 | <= 20 | **OK*** | STR-LOADFRAME under every rack, bearing on the C100 floor channels; structural calc confirms |
| BEN 700 | I-D17 | A-002 | Door zone (free length between the row end and the blind-end zone) vs 0 | 11850 - 350 - 11315 = 185 | >= 0 | **OK** |  |
