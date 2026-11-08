# BEN 5 — Issue-for-construction drawing set

Generated 2026-11-08 by `design/drawings/gen_drawings.py` from `Config.preset('ben5')`.
Configuration: ben5 | ai_inference | 5 kW IT | 1 racks | cooling cabinet_dx | N+1 | temperate | H1
Enclosure: Outdoor 24U NEMA 4X / IP66 cabinet on skid — NEMA 4X / IP66 (H1 Standard).

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
| BEN 5 | I-M1 | A-002 | Rack units available for IT after UPS (2 x 4U), battery packs (2 x 3U) and controls shelf (1U) | 24U - 15U | >= 6 | **OK*** | 9U for IT at 5 kW: 2 x 2U servers + 1U switch + 1U patch fits; was 12U rule |
| BEN 5 | I-M2 | A-001 | Cabinet DX units fit on cabinet exterior long face | 1 x 400 + 2 x 100 gap vs ext 1200 | <= 1200 | **OK** |  |
| BEN 5 | I-M3 | A-003 | Rack depth + front/rear air gap vs cabinet interior width | 600 + 100 + 100 vs 800 | <= 800 | **OK** |  |
| BEN 5 | I-M4 | S-001 | Skid + cabinet gross mass vs 2.5 t forklift / tail-lift | gross 1087 kg | <= 2500 | **OK** |  |
