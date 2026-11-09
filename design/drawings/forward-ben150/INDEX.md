# BEN 150 forward prototype (800 VDC + high-density liquid) — drawing set, Rev C (ISSUED FOR REVIEW — forward architecture study)

Generated 2026-11-08 by `design/drawings/gen_drawings.py --forward` from `layout.forward_prototype_config()` (BEN 150, 150 kW in 2 racks, dc800 bipolar_400, dlc_hd); revision from `design/REVISION.json`, change register **DC-002**. Study sheets for review beside the Rev C tier sets; nothing here is issued for construction. Decision: `docs/FORWARD_ARCHITECTURE_DECISION.md`; BOM: `docs/BOM-ben150-forward.md`; research: `docs/research/STATE_OF_THE_ART_2026.md`.
Configuration: ben150 | ai_inference | 150 kW IT | 2 racks | cooling dlc_hd | dc800 bipolar_400 | N+1 | temperate | H1
Enclosure: 20 ft high-cube ISO-frame module, sealed to IP66 — NEMA 4X / IP66 (H1 Standard).

| Sheet | Title | Scale | Files |
|---|---|---|---|
| E-001 | Power one-line — 800 VDC bus (forward study) (sheet 1/2) | NTS | [E-001.svg](E-001.svg), [E-001.png](E-001.png) |
| M-001 | Cooling P&ID — high-density liquid W45 loop (forward study) (sheet 2/2) | NTS | [M-001.svg](M-001.svg), [M-001.png](M-001.png) |

Status: **ISSUED FOR REVIEW — forward architecture study, not for construction** — Rev C, 2026-11-08. Drawn: BEN Engine generator; Checked: blank (requires a checker before the set is re-issued for construction).

| Rev | Date | Description | Checked |
|---|---|---|---|
| C | 2026-11-08 | Rev C: design change DC-001 — BEN 5 cabinet air conditioner changed from the R-134a 5.8 kW variant (GWP 1430) to the R-513A 5.5 kW variant (GWP 631) to meet the AIM Act 700-GWP limit; cooling capacity rule updated (unit 5.5 kW, N+1 = 2 units); M-001 BEN 5 refrigerant note and schedule updated. | not checked |

## Interference checks for this tier

| Tier | ID | Sheet | Check | Numbers | Limit | Result | Resolution |
|---|---|---|---|---|---|---|---|
| BEN 150 | I-C0 | A-003 | Config interior height vs envelope build-up (2698 shipped - 100 floor - 110 roof), 10 mm tolerance | config 2490 vs computed 2488 | <= 2498 | **OK** |  |
| BEN 150 | I-C1 | A-002 | Config row_length_mm (racks + cooling units + 500 end zone) vs interior length, config rule | 2900 vs 5750 | <= 5750 | **OK** |  |
| BEN 150 | I-C2 | A-002 | Row length with layout footprints (dlc_hd: 2 racks, 2 cooling units, power cabinets) vs usable length | 4500 vs 5250 | <= 5250 | **OK** |  |
| BEN 150 | I-C21 | A-002 | Row length with catalog 800 VDC power quantities (1 x rectifier cabinet @600 + 1 x 800 V battery cabinet @600 for 28 kWh) vs usable length | 4500 vs 5250 | <= 5250 | **OK** |  |
| BEN 150 | I-C4 | A-002 | Cold aisle / egress width (int W - plenum - row depth) vs 900 egress | 2200 - 200 - 1070 = 930 | >= 900 | **OK** |  |
| BEN 150 | I-C22 | A-002 | Aisle width with the catalog rack (STR-RACK42: 600 x 1070 deep) vs 900 egress / 914 NEC | 2200 - 200 - 1070 = 930 | >= 914 | **OK** |  |
| BEN 150 | I-C5 | A-002 | Working space depth in front of row, NEC 110.26 condition 1 (insulated wall opposite) | 930 vs 914 | >= 914 | **OK** |  |
| BEN 150 | I-C6 | A-002 | Working space depth NEC 110.26 condition 2 (grounded parts opposite) - informative | 930 vs 1067 | >= 1067 | **FAIL** | Not required: liner wall opposite the row is insulated and non-grounded-surface; condition 1 applies |
| BEN 150 | I-C7 | A-002 | Door zone (free length between door and first row item) vs 0 | 5750 - 500 - 4500 = 750 | >= 0 | **OK** |  |
| BEN 150 | I-C8 | A-002 | Two-row layout (2 x rack depth + 1000 cold aisle) vs interior width | 3140 vs 2200 | <= 2200 | **FAIL** | Not used; single row chosen |
| BEN 150 | I-C9 | A-002 | Rack 1070 + aisle 1000 + cooling unit 1070 across the width vs interior width | 3140 vs 2200 | <= 2200 | **FAIL** | Not used; cooling units are in-row, not across the width |
| BEN 150 | I-C10 | A-002 | Rack working space width (762 min) vs rack width | 762 vs 600 rack + aisle continuous | >= 762 | **OK*** | Aisle is continuous along the row; width requirement met by the open aisle |
| BEN 150 | I-C11 | A-003 | Overhead tray underside (over the aisle) vs rack top, cables drop to rack top entry | 2250 - 2000 = 250 | >= 0 | **OK*** | Trays run over the aisle, not over racks; head clearance under tray 2250 >= 2100 |
| BEN 150 | I-C12 | A-003 | Tray top vs ceiling liner (clearance >= 100 for installation) | 2490 - 2350 = 140 | >= 100 | **OK** |  |
| BEN 150 | I-C13 | A-002 | Door swing: ISO cargo doors swing outward; interior door zone needed | 0 vs 0 | >= 0 | **OK*** | Cargo doors open outward 270 deg; no interior swing |
| BEN 150 | I-C14 | A-003 | Rack height vs interior height (>= 300 for top cable entry and lights over the row) | 2490 - 2000 = 490 | >= 300 | **OK** |  |
| BEN 150 | I-C15 | S-001 | Gross mass vs ISO 668 max gross for the container size (30480 kg) | 5822 vs 30480 | <= 30480 | **OK** |  |
| BEN 150 | I-C16 | S-001 | Row strip floor load (payload over row footprint) vs ISO 1496-1 uniform payload rating (~20 kN/m2) | 4.6 kN/m2 vs 20 | <= 20 | **OK*** | Rack feet are point loads: C100 floor channels on cross-members spread them; verify in structural calc |
| BEN 150 | I-C23 | M-001 | Residual air load (10% IT, stated library value) vs W45 in-row fan coils x (units - 1) | 15.8 kW vs 2 x 12 kW | >= 15.75 | **OK** |  |
| BEN 150 | I-C24 | M-001 | Row CDU capacity (N units) vs liquid heat x 1.05 | 600 vs 142 | >= 141.75 | **OK** |  |
| BEN 150 | I-C25 | E-001 | DC busway frame vs bus current with 25 % headroom (±400 VDC bipolar) | 400 A vs 238 A | >= 238 | **OK** |  |
| BEN 150 | I-C26 | E-001 | Rectifier modules (N, 100 kW) vs AC/DC front-end load | 200 vs 165.8 | >= 165.8 | **OK** |  |
| BEN 150 | I-C20 | A-001 | Roof penetrations min 300 mm from side top rail | line-set curbs at y=300 interior = 419 from ext side face | >= 300 | **OK*** | Line-set roof curbs 300 mm inboard of top side rail, between corrugation roof bows; see A-001 |
