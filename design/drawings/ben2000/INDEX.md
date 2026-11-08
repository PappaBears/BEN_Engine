# BEN 2000 — Issue-for-construction drawing set

Generated 2026-11-08 by `design/drawings/gen_drawings.py` from `Config.preset('ben2000')`.
Configuration: ben2000 | ai_inference | 1600 kW IT | 48 racks | cooling dlc_cdu | N+1 | temperate | H1
Enclosure: Prefabricated wide-body modular hall (3 site-joined 12.2 m modules) + power module + plant yard, IP66 envelope — NEMA 4X / IP66 (H1 Standard).

| Sheet | Title | Scale | Files |
|---|---|---|---|
| A-000 | Site plan (sheet 1/14) | see sheet | [A-000.svg](A-000.svg), [A-000.png](A-000.png) |
| A-001 | General arrangement (sheet 2/14) | see sheet | [A-001.svg](A-001.svg), [A-001.png](A-001.png) |
| A-001-M1 | Module 1 general arrangement (sheet 3/14) | 1:50 | [A-001-M1.svg](A-001-M1.svg), [A-001-M1.png](A-001-M1.png) |
| A-001-M2 | Module 2 general arrangement (sheet 4/14) | 1:50 | [A-001-M2.svg](A-001-M2.svg), [A-001-M2.png](A-001-M2.png) |
| A-001-M3 | Module 3 general arrangement (sheet 5/14) | 1:50 | [A-001-M3.svg](A-001-M3.svg), [A-001-M3.png](A-001-M3.png) |
| A-002 | Interior layout plan (sheet 6/14) | see sheet | [A-002.svg](A-002.svg), [A-002.png](A-002.png) |
| A-002-M1 | Module 1 interior layout (sheet 7/14) | 1:50 | [A-002-M1.svg](A-002-M1.svg), [A-002-M1.png](A-002-M1.png) |
| A-002-M2 | Module 2 interior layout (sheet 8/14) | 1:50 | [A-002-M2.svg](A-002-M2.svg), [A-002-M2.png](A-002-M2.png) |
| A-002-M3 | Module 3 interior layout (sheet 9/14) | 1:50 | [A-002-M3.svg](A-002-M3.svg), [A-002-M3.png](A-002-M3.png) |
| A-003 | Envelope section and hardening (sheet 10/14) | see sheet / 1:2 | [A-003.svg](A-003.svg), [A-003.png](A-003.png) |
| S-001 | Foundation and anchoring (sheet 11/14) | see sheet / 1:5 | [S-001.svg](S-001.svg), [S-001.png](S-001.png) |
| E-001 | Power one-line (MV service) (sheet 12/14) | NTS | [E-001.svg](E-001.svg), [E-001.png](E-001.png) |
| M-001 | Cooling P&ID (sheet 13/14) | NTS | [M-001.svg](M-001.svg), [M-001.png](M-001.png) |
| C-001 | Controls layout (sheet 14/14) | see sheet | [C-001.svg](C-001.svg), [C-001.png](C-001.png) |

Status: **ISSUE FOR CONSTRUCTION Rev A** — Drawn: BEN Engine generator; Checked: blank (requires a checker before release).

## Interference checks for this tier

| Tier | ID | Sheet | Check | Numbers | Limit | Result | Resolution |
|---|---|---|---|---|---|---|---|
| BEN 2000 | I-H0 | A-001 | Hall external width vs 3 road sections of 3,660 mm joined side by side | 3 x 3660 = 10980 vs ext 11000 | <= 11000 | **OK** |  |
| BEN 2000 | I-H1 | A-002 | Width stack (4 rows, cold 1100 / hot 900 aisles, racks 1070 deep, fan wall 1000) vs interior width | 10380 vs 10400 | <= 10400 | **OK** |  |
| BEN 2000 | I-H2 | A-002 | Config row_length_mm (racks + CDUs + 500 end zone) vs interior length, config rule | 8900 vs 35800 | <= 35800 | **OK** |  |
| BEN 2000 | I-H3 | A-002 | Row footprint (12 racks x 600 + 2 CDU ends) vs IT-zone length (bays 2-3) | 8400 vs 22800 | <= 22800 | **OK*** | Rows centred; 14400 mm spare split to the two row-end service zones (staging, spares). Hall holds 48 racks at up to 80 kW DLC = 3,840 kW; preset 1600 kW |
| BEN 2000 | I-H4 | A-002 | Cold aisle width vs NEC 110.26 condition 2 (1067, equipment on both sides) and 900 egress | 1100 vs 1067 | >= 1067 | **OK** |  |
| BEN 2000 | I-H5 | A-002 | Contained hot aisle width vs 900 egress (doors at both ends) | 900 vs 900 | >= 900 | **OK** |  |
| BEN 2000 | I-H6 | A-002 | Fan-wall discharge aisle (cold aisle 3 in front of the fan wall) vs 1067 | 1100 vs 1067 | >= 1067 | **OK** |  |
| BEN 2000 | I-H7 | E-001 | 480 V switchgear 4,000 A working space, NEC 110.26(A)(1) condition 3 (grounded/live both sides) at 480 V: drawn 1500 vs 1,200 min; two entrances >= 610 x 2,000 (110.26(C)(2), >= 1,200 A and > 1.8 m wide) | 1500 vs 1200 | >= 1200 | **OK*** | 1,500 drawn: 1,200 cond. 3 minimum + 300 for drawout breaker lift truck; rear access 1,000; two exits from the switchgear room |
| BEN 2000 | I-H8 | A-000 | Power module depth stack (switchgear + working space + UPS row + 1,200 aisle + battery rooms) vs 3 sections (11.0 m) | 9400 vs 10980 | <= 10980 | **OK** |  |
| BEN 2000 | I-H9 | A-000 | Two 4,000 A lineups side by side + 1,200 between + ends vs power module length | 11600 vs 12200 | <= 12200 | **OK** |  |
| BEN 2000 | I-H10 | M-001 | CDU capacity on the common secondary header vs IT x 1.05 + one 300 kW spare (row 4 alone has 1 CDU = 300 kW < row load 400 kW, so per-row CDUs would not carry N) | 7 x 300 = 2100 vs 1980 | >= 1980 | **OK*** | CDUs feed one ring-main secondary header so N+1 is system-wide ([2, 2, 2, 1] per row); per-row isolation valves, header sized DN150 |
| BEN 2000 | I-H11 | M-001 | Residual air (25 % of IT) vs fan-wall units N (one per module) | 420 vs 600 | >= 420 | **OK** |  |
| BEN 2000 | I-H12 | A-003 | Overhead stack: rack 2,200 + manifold + busway (top) vs interior height - 300 for lights and sprinkler/clean-agent nozzles | 2950 vs 3300 | <= 3300 | **OK** |  |
| BEN 2000 | I-H13 | A-003 | Road section travel height (4,200 + 600 lowboy deck) vs 4,880 (16 ft) permit route limit | 4200 + 600 = 4800 vs 4880 | <= 4880 | **OK*** | Lowboy / drop-deck trailer, route survey and superload permits (SITE-FREIGHT-WB); 3.66 m width needs escorts |
| BEN 2000 | I-H14 | E-001 | Lithium battery energy per room vs NFPA 855 600 kWh group limit (UL 9540A large-scale test above it), 2-hour separation between rooms | 296 kWh per room vs 600 | <= 600 | **OK** |  |
| BEN 2000 | I-H15 | A-000 | Generator enclosure to hall / power module clearance vs 3,000 (NFPA 37 1.5 m min to combustible walls; 3 m for service and radiator discharge) | 3000 vs 3000 | >= 3000 | **OK** |  |
| BEN 2000 | I-H16 | A-000 | FR3 ester pad-mount transformer to power module clearance vs 900 (FM 5-4 / IEEE C57.12 less-flammable liquid, non-combustible wall) | 3000 vs 900 | >= 900 | **OK** |  |
| BEN 2000 | I-H17 | A-000 | Setback / fire lane around the hall vs 6,000 (IFC 503 fire apparatus access 6.1 m) | 6100 vs 6100 | >= 6100 | **OK*** | Fire lane is the 6 m crane lane on the south side plus the 6 m yard; AHJ confirms the access route |
| BEN 2000 | I-H18 | S-001 | Rack footprint load (1,000 kg on 0.6 x 1.07 m) vs 200 mm slab-on-grade design 20 kN/m2 | 15.3 kN/m2 vs 20 | <= 20 | **OK** |  |
| BEN 2000 | I-H19 | S-001 | Road section lift mass (tare per section + 800 kg fit-out) vs 100 t AT crane at 20 m radius (~25 t) | 7467 vs 25000 | <= 25000 | **OK** |  |
| BEN 2000 | I-H20 | A-001 | Hall gross mass (config) vs slab + grade beams design 1,200 t | 109070 vs 1200000 | <= 1.2e+06 | **OK** |  |
