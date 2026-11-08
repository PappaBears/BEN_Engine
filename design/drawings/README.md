# BEN Engine — drawing set generator

Issue-for-construction (IFC) drawing sets for every tier are generated from the configuration model.
Nothing in `design/drawings/<tier>/` is hand-drawn; change the configuration or the generator and regenerate.

## Regenerate

```bash
cd /home/user/ben_engine
python design/drawings/gen_drawings.py                 # all tiers, all sheets, + INTERFERENCE_CHECKS.md
python design/drawings/gen_drawings.py --tier ben20    # one tier
python design/drawings/gen_drawings.py --tier ben40 --sheet E-001 --sheet M-001
python design/drawings/gen_drawings.py --dpi 150       # larger PNGs (default 110 dpi on an A1 sheet = 3642 px wide)
```

Requirements: Python 3.13, numpy, matplotlib, pillow (no other dependencies). Runtime about 10 s per tier.

Companion generators that use the same layout engine:

```bash
python design/renders/gen_renders.py                   # assembly stage renders + contact sheets
python design/assembly/gen_assembly.py                 # STE assembly instructions + ITEM_CODES_USED.md
python design/gen_design_basis.py                      # DESIGN_BASIS.md (run after gen_drawings.py)
python design/gen_sqam.py                              # docs/SQAM.md + design/assembly/CTQ-CARD-<tier>.md from ctq.py
python design/layout.py                                # prints the resolved layout and the interference table
```

## What is where

| File | Role |
|---|---|
| `design/layout.py` | Layout engine. Reads `Config.preset(tier)`, places every item in interior millimetres, runs the interference checks, records configuration deviations. Shared by drawings, renders and assembly docs. |
| `design/ctq.py` | CTQ / CTP register (one source for the sheet tables, the assembly "Check:" lines and the QC forms). |
| `design/drawings/drawkit.py` | Small drafting kit on matplotlib: A1 sheet, scaled views, dimensions, leaders, bubbles, tables, title block, P&ID symbols. |
| `design/drawings/gen_drawings.py` | The seven sheet generators and the driver. |
| `design/drawings/<tier>/A-001 … C-001.svg/.png` | The sheets. SVG is the vector master; PNG is for review and for the web. |
| `design/drawings/<tier>/INDEX.md` | Sheet list, configuration line, deviations and the tier's interference table. |
| `design/drawings/INTERFERENCE_CHECKS.md` | All tiers' interference checks (embedded in `design/DESIGN_BASIS.md`). |

## Sheet list

| No. | Title | Content |
|---|---|---|
| A-001 | General arrangement | Roof plan, two elevations, door-end view, corner castings, roof penetrations, brand panel, weight table, general notes |
| A-002 | Interior layout plan | Row with pitch, hot plenum / RDHx, cold aisle and egress (>= 900), NEC 110.26 working space (914 / 1067), containment, power cabinets, panels, gateway, trays, leak rope, cylinder, row elevation, equipment schedule |
| A-003 | Envelope section | Cross section, wall / floor / door-seal / roof-curb details at 1:2 and 1:2.5, R-value, condensation check, thermal-bridge notes |
| S-001 | Floor framing and anchoring | Cross members, floor channels, through-bolt and hold-down pattern, equipment skid bolts, lifting and tie-down, seismic option, structural data and torques |
| E-001 | Power one-line | Utility → meter → service section (main CB, SPD) → ATS / generator → UPS (+ transformer) → IT distribution → rack PDUs; mechanical panel; EPO; grounding electrode system |
| M-001 | Cooling P&ID | DX air section (in-row / cabinet units, roof condensers, line sets, condensate), liquid section (dry cooler, pumping unit / CDUs, manifolds, RDHx or cold plates, instruments, make-up, leak rope) |
| C-001 | Controls layout | Sensor and node plan, probe heights, sensor schedule with PROTOCOL.md channel names and twin coordinates, controls network |

Every sheet carries the title block (Schreiber AI · BEN Engine · tier · drawing no. · ISSUE FOR CONSTRUCTION Rev A · 2026-11-07 · scale · sheet n/7 · Drawn: BEN Engine generator · Checked: blank) and a CTQ / CTP table for that sheet.

## Conventions

- Interior coordinates: x along the length from the door-end liner, y across the width from the rack-wall liner, z from the finished floor; millimetres.
- Sheet is A1 landscape (841 x 594 mm). Text 1.7–4 mm on the sheet. Scales are picked per tier so the longest view fits 470 mm.
- Colours on the sheets are print-safe darkened versions of the brand palette (racks teal, cooling green, power amber, controls purple, fire red). The title block uses the brand graphite / cyan.
- "OK*" in an interference table means the check passes only with the resolution written next to it. "FAIL" with a resolution means the drawn solution deviates from the configuration or from the first-choice design; the deviation is also printed in red on every sheet of that tier.

## Known limits (Rev A)

- The generator is a drafting aid, not a CAD model: there are no hidden-line views and no 3D-derived sections. Details are schematic and dimensioned by rule, not by part drawings.
- Breaker sizes, conductor sizes, refrigerant line sizes and the cylinder size are preliminary and say so on the sheets; a licensed engineer / technician completes them.
- "Checked" is blank on purpose. A person checks the set before it is used for construction.
