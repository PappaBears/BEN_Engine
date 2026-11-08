# BEN 500 — Issue-for-construction drawing set

Generated 2026-11-08 by `design/drawings/gen_drawings.py` from `Config.preset('ben500')`.
Configuration: ben500 | ai_inference | 192 kW IT | 10 racks | cooling dlc_cdu | N+1 | temperate | H1
Enclosure: 40 ft high-cube ISO-frame module, sealed to IP66 — NEMA 4X / IP66 (H1 Standard).

| Sheet | Title | Scale | Files |
|---|---|---|---|
| A-001 | General arrangement (sheet 1/7) | see sheet | [A-001.svg](A-001.svg), [A-001.png](A-001.png) |
| A-002 | Interior layout plan (sheet 2/7) | see sheet | [A-002.svg](A-002.svg), [A-002.png](A-002.png) |
| A-003 | Envelope section and hardening (sheet 3/7) | see sheet / 1:2 | [A-003.svg](A-003.svg), [A-003.png](A-003.png) |
| S-001 | Floor framing and anchoring (sheet 4/7) | see sheet / 1:5 | [S-001.svg](S-001.svg), [S-001.png](S-001.png) |
| E-001 | Power one-line (sheet 5/7) | NTS | [E-001.svg](E-001.svg), [E-001.png](E-001.png) |
| M-001 | Cooling P&ID (sheet 6/7) | NTS | [M-001.svg](M-001.svg), [M-001.png](M-001.png) |
| C-001 | Controls layout (sheet 7/7) | see sheet | [C-001.svg](C-001.svg), [C-001.png](C-001.png) |

Status: **ISSUE FOR CONSTRUCTION Rev A** — Drawn: BEN Engine generator; Checked: blank (requires a checker before release).

## Interference checks for this tier

| Tier | ID | Sheet | Check | Numbers | Limit | Result | Resolution |
|---|---|---|---|---|---|---|---|
| BEN 500 | I-C0 | A-003 | Config interior height vs envelope build-up (2698 shipped - 100 floor - 110 roof), 10 mm tolerance | config 2490 vs computed 2488 | <= 2498 | **OK** |  |
| BEN 500 | I-C1 | A-002 | Config row_length_mm (racks + cooling units + 500 end zone) vs interior length, config rule | 7700 vs 11850 | <= 11850 | **OK** |  |
| BEN 500 | I-C2 | A-002 | Row length with layout footprints (dlc_cdu: 10 racks, 2 cooling units, power cabinets) vs usable length | 10400 vs 11350 | <= 11350 | **OK** |  |
| BEN 500 | I-C21 | A-002 | Row length with catalog UPS/battery quantities (0 x Galaxy VS 100 kW @521 + 2 x Li cab @600, catalog qty rules) vs usable length | 9600 vs 11350 | <= 11350 | **OK** |  |
| BEN 500 | I-C4 | A-002 | Cold aisle / egress width (int W - plenum - row depth) vs 900 egress | 2200 - 200 - 1070 = 930 | >= 900 | **OK** |  |
| BEN 500 | I-C22 | A-002 | Aisle width with the catalog rack (STR-RACK48: 600 x 1070 deep) vs 900 egress / 914 NEC | 2200 - 200 - 1070 = 930 | >= 914 | **OK** |  |
| BEN 500 | I-C5 | A-002 | Working space depth in front of row, NEC 110.26 condition 1 (insulated wall opposite) | 930 vs 914 | >= 914 | **OK** |  |
| BEN 500 | I-C6 | A-002 | Working space depth NEC 110.26 condition 2 (grounded parts opposite) - informative | 930 vs 1067 | >= 1067 | **FAIL** | Not required: liner wall opposite the row is insulated and non-grounded-surface; condition 1 applies |
| BEN 500 | I-C7 | A-002 | Door zone (free length between door and first row item) vs 0 | 11850 - 500 - 10400 = 950 | >= 0 | **OK** |  |
| BEN 500 | I-C8 | A-002 | Two-row layout (2 x rack depth + 1000 cold aisle) vs interior width | 3140 vs 2200 | <= 2200 | **FAIL** | Not used; single row chosen |
| BEN 500 | I-C9 | A-002 | Rack 1070 + aisle 1000 + cooling unit 1070 across the width vs interior width | 3140 vs 2200 | <= 2200 | **FAIL** | Not used; cooling units are in-row, not across the width |
| BEN 500 | I-C10 | A-002 | Rack working space width (762 min) vs rack width | 762 vs 600 rack + aisle continuous | >= 762 | **OK*** | Aisle is continuous along the row; width requirement met by the open aisle |
| BEN 500 | I-C11 | A-003 | Overhead tray underside (over the aisle) vs rack top, cables drop to rack top entry | 2250 - 2200 = 50 | >= 0 | **OK*** | Trays run over the aisle, not over racks; head clearance under tray 2250 >= 2100 |
| BEN 500 | I-C12 | A-003 | Tray top vs ceiling liner (clearance >= 100 for installation) | 2490 - 2350 = 140 | >= 100 | **OK** |  |
| BEN 500 | I-C13 | A-002 | Door swing: ISO cargo doors swing outward; interior door zone needed | 0 vs 0 | >= 0 | **OK*** | Cargo doors open outward 270 deg; no interior swing |
| BEN 500 | I-C14 | A-003 | Rack height vs interior height (>= 300 for top cable entry and lights over the row) | 2490 - 2200 = 290 | >= 300 | **FAIL** | Short by 10 mm: lights move over the aisle; top cable entry needs >= 250. Alternative: 47U racks (2150) |
| BEN 500 | I-C15 | S-001 | Gross mass vs ISO 668 max gross for the container size (30480 kg) | 14684 vs 30480 | <= 30480 | **OK** |  |
| BEN 500 | I-C16 | S-001 | Row strip floor load (payload over row footprint) vs ISO 1496-1 uniform payload rating (~20 kN/m2) | 7.0 kN/m2 vs 20 | <= 20 | **OK*** | Rack feet are point loads: C100 floor channels on cross-members spread them; verify in structural calc |
| BEN 500 | I-C19 | M-001 | Residual air load (25 % IT) vs in-row 300 capacity x units (N) | 50.4 kW vs 4 x 20 kW | >= 50.4 | **OK** |  |
| BEN 500 | I-C20 | A-001 | Roof penetrations min 300 mm from side top rail | line-set curbs at y=300 interior = 419 from ext side face | >= 300 | **OK*** | Line-set roof curbs 300 mm inboard of top side rail, between corrugation roof bows; see A-001 |
