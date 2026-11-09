# BEN Engine — drawing set generator

Drawing sets for every tier are generated from the configuration model. Nothing in `design/drawings/<tier>/`
is hand-drawn; change the configuration or the generator and regenerate.

**Current issue:** see `design/REVISION.json` (Rev B, 2026-11-08, ISSUED FOR REVIEW — no checker named yet). The set
is not an issue-for-construction (IFC) set until a named checker is written into that file and the set is regenerated.

## Revision procedure (document control)

One file, `design/REVISION.json`, holds the revision of the whole design set: drawings (42 sheets + INDEX.md files),
renders, STE assembly instructions, QC forms reference, SQAM, DESIGN_BASIS.md, the wiring one-lines and the
`DRAWING_INDEX_REV` field of generated proposals / SOW drafts. No generator carries a hard-coded revision or date.

1. Edit `design/REVISION.json`: bump `drawing_rev` (A → B → C …), set `issue_date`, write what changed in `notes`.
   Leave `checker` empty while the set is for review. The generators then print
   "ISSUED FOR REVIEW — not for construction until checked" in every title block and INDEX.
2. When a named person has checked the set, write their name in `checker` (`status` may then read
   "ISSUE FOR CONSTRUCTION"). The title blocks switch to IFC and the checker's name appears in the CHECKED field.
3. Regenerate everything, in this order:
   ```bash
   python design/drawings/gen_drawings.py && python design/gen_design_basis.py
   python design/renders/gen_renders.py
   python design/assembly/gen_assembly.py        # fails on an STE violation
   python design/gen_sqam.py
   python design/specs/wiring/gen_wiring.py
   (cd software && python -m ben_engine.bom --all)   # if catalog attributes changed
   ```
   then regenerate the sample proposals (`docs/proposals/README.md` "Regenerate") so the SOW cites the new revision.
4. Confirm nothing cites the old issue: `grep -rn "<old date>" design docs/SQAM.md docs/proposals | grep -i "rev\|issue"` must return nothing;
   `python scripts/audit.py` A13 must show one date for drawings, SQAM, QC forms and assembly.
5. The lead re-issues: commit the regenerated set in one commit titled "Drawing set Rev <X> (<date>)".
   Generation is deterministic (fixed `svg.hashsalt`, no `<dc:date>`), so a regeneration with no design change gives no diff.

Sheet A-001 of every tier carries the revision table (Rev / date / description / checked) from the same file.
`design/assembly/QC_FORMS.md` is hand-written; update its issue line and the Rev column in the header table by hand in the same change.

## Regenerate

```bash
cd /home/user/ben_engine
python design/drawings/gen_drawings.py                 # all tiers, all sheets, + INTERFERENCE_CHECKS.md
python design/drawings/gen_drawings.py --tier ben150   # one tier
python design/drawings/gen_drawings.py --tier ben500 --sheet E-001 --sheet M-001
python design/drawings/gen_drawings.py --dpi 150       # larger PNGs (default 110 dpi on an A1 sheet = 3642 px wide)
python design/drawings/gen_drawings.py --forward       # forward prototype study set only: forward-ben150/E-001 (800 VDC) + M-001 (W45 liquid)
```

**Forward architecture study set.** `design/drawings/forward-ben150/` holds E-001 (800 VDC one-line: AC/DC front end, DC busway ±400 V or 800 V unipolar, DC tap-offs, 800 V → 50 V rack shelves, battery on the bus, IMD, grounding / midpoint) and M-001 (W45 high-density liquid P&ID: row CDUs, manifolds, dry coolers, isolation valves, leak detection, heat-reuse HX) for the BEN 150 forward prototype (`layout.forward_prototype_config()`: 150 kW, 2 racks, dc800, dlc_hd). Title block status reads "ISSUED FOR REVIEW — forward architecture study"; the set is recorded as change DC-002 in `design/REVISION.json` and is not part of the Rev C tier sets. It is regenerated with `--forward` and checked with the next revision; nothing in it is issued for construction.

Requirements: Python 3.13, numpy, matplotlib, pillow (no other dependencies). Runtime about 10 s per tier.

Companion generators that use the same layout engine:

```bash
python design/renders/gen_renders.py                   # assembly stage renders + contact sheets
python design/assembly/gen_assembly.py                 # STE assembly instructions + ITEM_CODES_USED.md
python design/gen_design_basis.py                      # DESIGN_BASIS.md (run after gen_drawings.py)
python design/gen_sqam.py                              # docs/SQAM.md + design/assembly/CTQ-CARD-<tier>.md from ctq.py
python design/specs/wiring/gen_wiring.py               # one-line wiring diagrams (03_power_one_line_<tier>.svg for ben5/ben30/ben150/ben500)
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
| A-002 | Interior layout plan | Row with pitch, hot plenum / RDHx, cold aisle and egress (>= 900), NEC 110.26 working space (914 / 1067), containment, power cabinets, panels, BEN Controller panel, trays, leak rope, cylinder, row elevation, equipment schedule |
| A-003 | Envelope section | Cross section, wall / floor / door-seal / roof-curb details at 1:2 and 1:2.5, R-value, condensation check, thermal-bridge notes |
| S-001 | Floor framing and anchoring | Cross members, floor channels, through-bolt and hold-down pattern, equipment skid bolts, lifting and tie-down, seismic option, structural data and torques |
| E-001 | Power one-line | Utility → meter → service section (main CB, SPD) → ATS / generator → UPS (+ transformer) → IT distribution → rack PDUs; mechanical panel; EPO; grounding electrode system |
| M-001 | Cooling P&ID | DX air section (in-row / cabinet units, roof condensers, line sets, condensate), liquid section (dry cooler, pumping unit / CDUs, manifolds, RDHx or cold plates, instruments, make-up, leak rope) |
| C-001 | Controls layout | Sensor and Pod plan, probe heights, sensor schedule with PROTOCOL.md channel names and twin coordinates, controls network |

Every sheet carries the title block (Schreiber AI · BEN Engine · tier · drawing no. · status, Rev and date from `design/REVISION.json` · scale · sheet n/N · Drawn: BEN Engine generator · Checked: the `checker` field, blank while ISSUED FOR REVIEW) and a CTQ / CTP table for that sheet. A-001 also carries the revision table.

## Conventions

- Interior coordinates: x along the length from the door-end liner, y across the width from the rack-wall liner, z from the finished floor; millimetres.
- Sheet is A1 landscape (841 x 594 mm). Text 1.7–4 mm on the sheet. Scales are picked per tier so the longest view fits 470 mm.
- Colours on the sheets are print-safe darkened versions of the brand palette (racks teal, cooling green, power amber, controls purple, fire red). The title block uses the brand graphite / cyan.
- "OK*" in an interference table means the check passes only with the resolution written next to it. "FAIL" with a resolution means the drawn solution deviates from the configuration or from the first-choice design; the deviation is also printed in red on every sheet of that tier.

## Known limits

- The generator is a drafting aid, not a CAD model: there are no hidden-line views and no 3D-derived sections. Details are schematic and dimensioned by rule, not by part drawings.
- Breaker sizes, conductor sizes, refrigerant line sizes and the cylinder size are preliminary and say so on the sheets; a licensed engineer / technician completes them.
- "Checked" is blank while `design/REVISION.json` has no `checker`. A person checks the set, their name goes into that file, and the set is regenerated as IFC before it is used for construction.

## Rev 2 drawing set (Rev 2.A)

Record: `design/rev2/REVISION.json` (product revision 2, drawing set Rev 2.A, change register R2-01..R2-04). `design/revision.py` loads it when a generator runs with `--lineup rev2`; without the flag every generator reads `design/REVISION.json` exactly as before, so Rev 1 regenerates byte-identically.

```bash
python design/drawings/gen_drawings_rev2.py --lineup rev2     # design/drawings/rev2/<tier>/ (BEN 1: rev2/ben1/rack10|cab12/, A-001 E-001 C-001 I-001)
PYTHONPATH=software python design/gen_design_basis.py --lineup rev2   # design/rev2/DESIGN_BASIS.md (run after the drawings)
python design/renders/gen_renders.py --lineup rev2           # design/renders/rev2/<tier>/
python design/assembly/gen_assembly.py --lineup rev2         # design/assembly/rev2/ASSEMBLY-<tier>.md (fails on an STE violation)
python design/gen_sqam.py --lineup rev2                      # docs/rev2/SQAM.md + design/assembly/rev2/CTQ-CARD-<tier>.md
python design/specs/wiring/gen_wiring.py --lineup rev2       # design/specs/wiring/rev2/
PYTHONPATH=software python -m ben_engine.bom --all --lineup rev2      # purchasing/rev2/, docs/rev2/BOM*.md
```

Title blocks follow `brand/v2/titleblock-spec.md` (lockup-deep master embedded as vector on white, Archivo / IBM Plex TTFs, data plate band inside the 260 x 58 mm envelope so no Rev 1 layout moves, legal line under the frame). Index of the set: `design/drawings/rev2/INDEX.md`; engineering notice EN-001 (working space / aisle-wall liner): `docs/audit/EN-001_working_space_liner.md`.
