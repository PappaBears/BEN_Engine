# EN-001 — Engineering notice: NEC 110.26 working space and the aisle-wall liner

| | |
| --- | --- |
| Notice | EN-001 |
| Date | 2026-11-09 |
| Raised by | Lineup engineer (Rev 2 lineup work), confirmed by the design authority |
| Against | Rev 1 drawing set (`design/REVISION.json`): Rev B issued for construction (BEN 30, BEN 150, BEN 500, BEN 2000), Rev C issued for review (BEN 5) |
| Resolved in | Rev 2 drawing set Rev 2.A (`design/rev2/REVISION.json`, change R2-04) |
| Status | **Open against Rev 1** (hold on BEN 150 and BEN 500); **resolved by design in Rev 2**, pending the checker's signature and AHJ acceptance |

## 1. Issue

NEC 110.26(A)(1) sets the depth of the working space in front of electrical equipment that may be examined, adjusted, serviced or maintained while energised. Table 110.26(A)(1) gives three conditions:

| Nominal voltage to ground | Condition 1 | Condition 2 | Condition 3 |
| --- | --- | --- | --- |
| 0–150 V | 914 mm (3 ft) | 914 mm (3 ft) | 914 mm (3 ft) |
| 151–600 V | 914 mm (3 ft) | 1,067 mm (3.5 ft) | 1,219 mm (4 ft) |

Condition 1 means exposed live parts on one side and **no live or grounded parts on the other side** of the working space (or both sides guarded by insulating material). Condition 2 means live parts on one side and **grounded parts** on the other; the code states that concrete, brick or tile walls count as grounded.

The Rev 1 module drawings draw a single row against the rack wall with a 930 mm aisle in front of it, and claim condition 1 (914 mm) because the wall opposite the row is "insulated, non-grounded". The Rev 1 interference table says the same (check I-C5 "condition 1 (insulated wall opposite)", I-C6 "Not required: liner wall opposite the row is insulated and non-grounded-surface"). But the Rev 1 catalog liner is **ENV-LINER — ribbed 29-ga galvanised steel panel**, fixed with steel hat channel to a steel container shell and bonded with it. A bonded steel liner is a grounded surface. Condition 1 is therefore not justified; the module is a condition 2 situation, and at 151–600 V the working space must be 1,067 mm. The drawn aisle (930 mm) is 137 mm short.

## 2. Re-examination of every tier

| Tier (Rev 1) | Service | Voltage to ground in the working space | Aisle drawn | Required with a steel liner | Finding |
| --- | --- | --- | --- | --- | --- |
| BEN 5 | 208/240 V 1φ | 120 V | outdoor cabinet, open site in front of the door | 914 mm | **Not affected.** 0–150 V: 914 mm under every condition. |
| BEN 30 | 208 V 3φ (208Y/120) | 120 V | 930 mm | 914 mm | **Not affected in substance.** 0–150 V: 914 mm under every condition, so the steel liner does not change the requirement. The drawing's wording ("condition 1") is wrong but the clearance complies. Wording corrected in Rev 2. |
| BEN 150 | 480 V 3φ (480Y/277) | 277 V | 930 mm | 1,067 mm | **Non-compliant as drawn.** UPS frame, transformer and 415/240 V rack PDUs in the row; steel liner opposite. |
| BEN 500 | 480 V 3φ (480Y/277) | 277 V | 930 mm | 1,067 mm | **Non-compliant as drawn.** Same layout and liner. |
| BEN 2000 | 12.47 kV → 480 V | 277 V | cold aisles 1,100 mm; switchgear 1,500 mm | 1,067 / 1,219 mm | **Not affected by the liner.** The hall was designed to condition 2 (cold aisles, I-H4) and condition 3 (4,000 A switchgear, I-H7, drawn 1,500 ≥ 1,219). Two open items in §5. |
| Forward study `forward-ben150` | 480 V / 800 VDC | — | — | — | Study only, nothing issued; superseded by the Rev 2 dense tiers. |

A re-layout of BEN 150 / BEN 500 to condition 2 inside the module is not possible: interior width 2,200 mm − 200 mm plenum − 1,070 mm rack depth = 930 mm; condition 2 needs 1,067 mm, which would require racks no deeper than 933 mm (no current 42U/48U AI rack) or removing the hot-aisle plenum (which breaks the air path). The only practical Rev 1 fix is the liner.

A second, related defect was found during the re-examination: in Rev 1 the fire releasing panel (FRP, metal enclosure, 100 mm deep) and the EPO station (60 mm) are mounted on the aisle wall at x = 150–600 mm, directly opposite the first row items (UPS frame on BEN 150 / BEN 500). They are grounded parts inside the working space and they reduce the clear depth to 830 mm at that point, so even a non-conductive liner alone would not make that zone condition 1.

## 3. Affected Rev 1 sheets and their status

| Sheet / document | Content affected | Rev 1 status |
| --- | --- | --- |
| `design/drawings/ben150/A-002` | Working-space zone labelled "condition 1"; FRP and EPO on the aisle wall | Rev B **IFC** (checked 2026-11-08) |
| `design/drawings/ben500/A-002` | Same | Rev B **IFC** |
| `design/drawings/ben150/A-003`, `ben500/A-003` | Liner ENV-LINER (steel) on all walls | Rev B **IFC** |
| `design/drawings/ben150/E-001`, `ben500/E-001` | EPO station location "by door, aisle wall" | Rev B **IFC** |
| `design/drawings/ben30/A-002` | Wording "condition 1" only (clearance complies at 120 V to ground) | Rev B IFC — no hold |
| `design/drawings/{ben30,ben150,ben500}/INDEX.md`, `design/drawings/INTERFERENCE_CHECKS.md`, `design/DESIGN_BASIS.md` | I-C5 / I-C6 text | Rev B / Rev C record |
| `design/assembly/ASSEMBLY-ben150.md`, `ASSEMBLY-ben500.md` | Task 03 liner on all walls; FRP / EPO on the aisle wall | Issue B / C |

## 4. Safety significance

Working space exists so that a qualified person working on energised equipment can move back, is not pressed against a grounded surface while touching a live part, and can escape. With a grounded steel wall 930 mm behind the worker instead of the 1,067 mm the code requires at 277 V to ground, the risk of a phase-to-ground contact through the worker's body and of a restricted escape from an arc flash is higher than the code accepts. The defect is not a hazard in normal operation (doors closed, nobody in the aisle) and does not affect a unit that is de-energised for service, but the BEN Engine operating model (BEN Care service visits, UPS and PDU maintenance) includes energised examination. An AHJ inspection would be expected to reject the module as drawn. Classification: **major — safety / code compliance**; no unit has been built from the Rev B set, so there is no field exposure.

## 5. Disposition

**Rev 1 (frozen).** Drawing set Rev B IFC for **BEN 150 and BEN 500 is placed ON HOLD — do not build from it** — pending either (a) a liner change to a non-conductive liner on the aisle wall together with relocating the FRP and EPO off that wall, issued as a Rev 1 change with a new check, or (b) building those tiers from the Rev 2 set instead. A re-layout to condition 2 / 3 clearances inside the 2.2 m module is not feasible (§2). BEN 30, BEN 5 and BEN 2000 are not placed on hold; the BEN 30 wording is corrected in Rev 2. Rev 1 drawings are **not** regenerated (`docs/REVISION_POLICY.md`); the hold is recorded in `releases/REV1.md` ("Notices against Rev 1") and in the `notices` list of `design/REVISION.json`.

**Rev 2 (resolved by design, change R2-04).**

1. Catalog lines **ENV-LINER-NC** (FRP liner panel 0.09 in × 4 × 8 ft, ASTM E84 **Class A** required — Crane Composites Fire-X Glasbord class or Kemlite Class A FRP; standard Glasbord / Sequentia panels are Class C and are not acceptable) and **ENV-LINER-NC-SUB** (fire-retardant-treated plywood substrate, Class A) are added with `applies_to_lineups: ["rev2"]` for BEN 150, BEN 500, BEN 300 and BEN 700 (no Rev 1 BOM changes). Price: estimate USD 135 per FRP sheet (no published Fire-X price found; Class C Sequentia 4 × 8 seen at USD 69.99–99.99) and USD 75 per FRT plywood sheet.
2. The aisle wall opposite the row is lined with ENV-LINER-NC on FRT plywood on the furring, fixed with FRP adhesive and nylon rivets, PVC/FRP trims only; it is **not bonded**. Build-up 15 mm, less than the 19 mm rib depth of the steel liner it replaces, so the aisle does not shrink.
3. Nothing grounded or live is mounted on that wall in the row's working space: the fire releasing panel moves to a NEMA 4X box outside beside the cargo door; the EPO station is recessed in the door-end frame at the exit (x < 0) with a second station on the exterior service section. New checks I-C27 (carried module tiers) and I-D20 (dense tiers) count devices on that wall: 0 on every tier.
4. 480 V gear (UPS frames, battery cabinets, switchboard) on BEN 300 / BEN 700 keeps the condition 2 depth (1,067 mm, drawn 1,200 / 1,590 mm, check I-D5) conservatively. A related clearance found while drawing BEN 300: the end-wall panelboard PNL-D's 900 mm-wide working space overlapped the last fan coil by 50 mm; the panel moves 70 mm toward the aisle-wall liner (check I-D19, intrusion 0).
5. Rev 2 checks per tier:

| Rev 2 tier | Volts to ground | Aisle (mm) | Condition used | Liner | Result |
| --- | --- | --- | --- | --- | --- |
| BEN 1 | 120 V | office | 914 front clearance (sheet I-001) | n/a | not affected |
| BEN 5 | 120 V | outdoor | 914 | n/a | not affected |
| BEN 30 | 120 V | 930 | any (914) | steel ENV-LINER kept | OK (I-C5, I-C6, I-C27) |
| BEN 150 | 277 V | 930 | condition 1 | ENV-LINER-NC | OK* (I-C5), I-C27 0 devices |
| BEN 300 | 277 V | 932 racks / 1,000 CDUs / 1,200 gear | condition 1 racks and CDUs, condition 2 gear | ENV-LINER-NC | OK (I-D4, I-D5, I-D6, I-D19, I-D20) |
| BEN 500 | 277 V | 930 | condition 1 | ENV-LINER-NC | OK* (I-C5), I-C27 0 devices |
| BEN 700 | 277 V | 932 racks / 1,000 CDUs / 1,590 switchboard / 1,200 gear | condition 1 racks and CDUs, condition 2 gear | ENV-LINER-NC | OK (I-D4, I-D5, I-D6, I-D20) |
| BEN 2000 | 277 V | 1,100 cold / 900 hot | condition 2 / 3 | not relied on | OK; open items below |

No Rev 2 tier needs a condition 2 / 3 re-layout because of grounded rack frames opposite: in every module the row is single-sided, so the only surface opposite the racks is the aisle wall.

**Open items (not holds).**

- **AHJ acceptance.** Condition 1 relies on the AHJ accepting a Class A FRP liner over insulation over the steel shell as "no grounded parts" on that side. Raise it at the first plan review; if refused, BEN 150 / BEN 500 / BEN 300 / BEN 700 rack zones need 1,067 mm, which the 2.2 m module cannot give (the tiers would move to a wider enclosure or to a two-module layout).
- **BEN 2000 hot aisle.** The 900 mm contained hot aisle is drawn as egress. If rack-rear PDU breakers (415/240 V) are to be examined or reset energised from the hot aisle, condition 2 (1,067 mm) applies there. Rev 2 keeps the hall unchanged; the operating procedure must say rack-rear PDUs are serviced from the cold aisle or de-energised, or the hot aisle is widened at the next hall revision.
- **Layout constant.** `NEC_WS_COND3_LV` in `design/layout.py` is 1,200 mm; the code value is 1,219 mm (4 ft). The drawn switchgear space (1,500 mm) complies; the constant is left unchanged so Rev 1 output stays reproducible, and the check text is to be corrected with the next hall revision.
- **BOM over-count.** The Rev 1 catalog line ENV-LINER (steel) still counts the aisle wall in its quantity rule for the Rev 2 tiers; existing catalog lines are not edited. Purchasing buys about 10 % fewer steel sheets for Rev 2 BEN 150 / 500 / 300 / 700, or the line is superseded by a Rev 2 line at the next catalog revision.

## 6. Verification

- `python design/layout.py --rev2` — I-C5 / I-C6 / I-C27 and I-D4 / I-D5 / I-D6 / I-D19 / I-D20 as tabled above.
- Rev 2 sheets A-002 / A-003 / E-001 of the module tiers carry the EN-001 note; `design/drawings/rev2/<tier>/INDEX.md` carries the EN-001 status line.
- CTQ-E10 (WITNESS, form Q-03): Class A report for the delivered lot, liner face open-circuit to ground at 10 points, clear depth ≥ 914 mm (racks) and ≥ 1,067 mm (480 V gear).
- `design/assembly/rev2/ASSEMBLY-ben150.md` (and 300 / 500 / 700) Task 03 liner steps; FRP and EPO relocated in the fire and electrical tasks.
