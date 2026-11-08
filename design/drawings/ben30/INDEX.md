# BEN 30 — drawing set, Rev C (ISSUED FOR REVIEW)

Generated 2026-11-08 by `design/drawings/gen_drawings.py` from `Config.preset('ben30')`; revision from `design/REVISION.json`.
Configuration: ben30 | ai_inference | 30 kW IT | 2 racks | cooling inrow_dx_300 | N+1 | temperate | H1
Enclosure: 10 ft high-cube ISO-frame module, sealed to IP66 — NEMA 4X / IP66 (H1 Standard).

| Sheet | Title | Scale | Files |
|---|---|---|---|
| A-001 | General arrangement (sheet 1/7) | see sheet | [A-001.svg](A-001.svg), [A-001.png](A-001.png) |
| A-002 | Interior layout plan (sheet 2/7) | see sheet | [A-002.svg](A-002.svg), [A-002.png](A-002.png) |
| A-003 | Envelope section and hardening (sheet 3/7) | see sheet / 1:2 | [A-003.svg](A-003.svg), [A-003.png](A-003.png) |
| S-001 | Floor framing and anchoring (sheet 4/7) | see sheet / 1:5 | [S-001.svg](S-001.svg), [S-001.png](S-001.png) |
| E-001 | Power one-line (sheet 5/7) | NTS | [E-001.svg](E-001.svg), [E-001.png](E-001.png) |
| M-001 | Cooling P&ID (sheet 6/7) | NTS | [M-001.svg](M-001.svg), [M-001.png](M-001.png) |
| C-001 | Controls layout (sheet 7/7) | see sheet | [C-001.svg](C-001.svg), [C-001.png](C-001.png) |

Status: **ISSUED FOR REVIEW — not for construction until checked** — Rev C, 2026-11-08. Drawn: BEN Engine generator; Checked: blank (requires a checker before the set is re-issued for construction).

| Rev | Date | Description | Checked |
|---|---|---|---|
| C | 2026-11-08 | Rev C: design change DC-001 — BEN 5 cabinet air conditioner changed from the R-134a 5.8 kW variant (GWP 1430) to the R-513A 5.5 kW variant (GWP 631) to meet the AIM Act 700-GWP limit; cooling capacity rule updated (unit 5.5 kW, N+1 = 2 units); M-001 BEN 5 refrigerant note and schedule updated. | not checked |

## Interference checks for this tier

| Tier | ID | Sheet | Check | Numbers | Limit | Result | Resolution |
|---|---|---|---|---|---|---|---|
| BEN 30 | I-C0 | A-003 | Config interior height vs envelope build-up (2698 shipped - 100 floor - 110 roof), 10 mm tolerance | config 2490 vs computed 2488 | <= 2498 | **OK** |  |
| BEN 30 | I-C1 | A-002 | Config row_length_mm (racks + cooling units + 500 end zone) vs interior length, config rule | 2600 vs 2700 | <= 2700 | **OK** |  |
| BEN 30 | I-C2 | A-002 | Row length with layout footprints (inrow_dx_300: 2 racks, 3 cooling units, power cabinets) vs usable length | 2100 vs 2200 | <= 2200 | **OK** |  |
| BEN 30 | I-C21 | A-002 | Row length with catalog UPS (0 x 93PM 50 kW tower @495 in the row; 3 x PWR-UPS-RM20 rack-mount alternative) vs usable length | 2100 vs 2200 | <= 2200 | **OK** |  |
| BEN 30 | I-C4 | A-002 | Cold aisle / egress width (int W - plenum - row depth) vs 900 egress | 2200 - 200 - 1070 = 930 | >= 900 | **OK** |  |
| BEN 30 | I-C22 | A-002 | Aisle width with the catalog rack (STR-RACK42: 600 x 1070 deep) vs 900 egress / 914 NEC | 2200 - 200 - 1070 = 930 | >= 914 | **OK** |  |
| BEN 30 | I-C5 | A-002 | Working space depth in front of row, NEC 110.26 condition 1 (insulated wall opposite) | 930 vs 914 | >= 914 | **OK** |  |
| BEN 30 | I-C6 | A-002 | Working space depth NEC 110.26 condition 2 (grounded parts opposite) - informative | 930 vs 1067 | >= 1067 | **FAIL** | Not required: liner wall opposite the row is insulated and non-grounded-surface; condition 1 applies |
| BEN 30 | I-C7 | A-002 | Door zone (free length between door and first row item) vs 0 | 2700 - 500 - 2100 = 100 | >= 0 | **OK** |  |
| BEN 30 | I-C8 | A-002 | Two-row layout (2 x rack depth + 1000 cold aisle) vs interior width | 3140 vs 2200 | <= 2200 | **FAIL** | Not used; single row chosen |
| BEN 30 | I-C9 | A-002 | Rack 1070 + aisle 1000 + cooling unit 1070 across the width vs interior width | 3140 vs 2200 | <= 2200 | **FAIL** | Not used; cooling units are in-row, not across the width |
| BEN 30 | I-C10 | A-002 | Rack working space width (762 min) vs rack width | 762 vs 600 rack + aisle continuous | >= 762 | **OK*** | Aisle is continuous along the row; width requirement met by the open aisle |
| BEN 30 | I-C11 | A-003 | Overhead tray underside (over the aisle) vs rack top, cables drop to rack top entry | 2250 - 2000 = 250 | >= 0 | **OK*** | Trays run over the aisle, not over racks; head clearance under tray 2250 >= 2100 |
| BEN 30 | I-C12 | A-003 | Tray top vs ceiling liner (clearance >= 100 for installation) | 2490 - 2350 = 140 | >= 100 | **OK** |  |
| BEN 30 | I-C13 | A-002 | Door swing: ISO cargo doors swing outward; interior door zone needed | 0 vs 0 | >= 0 | **OK*** | Cargo doors open outward 270 deg; no interior swing |
| BEN 30 | I-C14 | A-003 | Rack height vs interior height (>= 300 for top cable entry and lights over the row) | 2490 - 2000 = 490 | >= 300 | **OK** |  |
| BEN 30 | I-C15 | S-001 | Gross mass vs ISO 668 max gross for the container size (30480 kg) | 4384 vs 30480 | <= 30480 | **OK** |  |
| BEN 30 | I-C16 | S-001 | Row strip floor load (payload over row footprint) vs ISO 1496-1 uniform payload rating (~20 kN/m2) | 8.8 kN/m2 vs 20 | <= 20 | **OK*** | Rack feet are point loads: C100 floor channels on cross-members spread them; verify in structural calc |
| BEN 30 | I-C17 | A-002 | Rack 1 U available for IT after 3 rack-mount UPS (10U each) + battery (6U) | 42 - 36 | >= 6 | **OK*** | IT in rack 1 limited to 6U; rack 2 carries the balance. Alternative: BEN 30 preset at 20 kW (2 modules) |
| BEN 30 | I-C20 | A-001 | Roof penetrations min 300 mm from side top rail | line-set curbs at y=300 interior = 419 from ext side face | >= 300 | **OK*** | Line-set roof curbs 300 mm inboard of top side rail, between corrugation roof bows; see A-001 |
