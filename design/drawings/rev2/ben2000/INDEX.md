# BEN 2000 — drawing set Rev 2.A (ISSUED FOR REVIEW)

Generated 2026-11-09 by `design/drawings/gen_drawings_rev2.py --lineup rev2` from `Config.preset('ben2000', lineup='rev2')`; revision from `design/rev2/REVISION.json`. Brand v2 title block (brand/v2/titleblock-spec.md). The Rev 1 set of this tier, where one exists, stays in `design/drawings/ben2000/` (frozen).
Configuration: ben2000 | ai_inference | 2000 kW IT | 15 racks | cooling dlc_hd | N+1 | temperate | H1 | lineup rev2
Enclosure: Three BEN 700 liquid-first 40 ft modules (all-in-one, sealed to IP66) on a shared yard: 12.47 kV switchgear, one pad-mount transformer and one heat-rejection skid per module — NEMA 4X / IP66 (H1 Standard).

| Sheet | Title | Files |
|---|---|---|
| A-000 | Site plan — three BEN 700 modules and the shared yard (sheet 1/3) | [A-000.svg](A-000.svg), [A-000.png](A-000.png) |
| A-001 | Cluster arrangement — elevations and BEN 700 module sheet reference (sheet 2/3) | [A-001.svg](A-001.svg), [A-001.png](A-001.png) |
| E-001 | Power one-line — 12.47 kV service to three BEN 700 modules (sheet 3/3) | [E-001.svg](E-001.svg), [E-001.png](E-001.png) |

Status: **ISSUED FOR REVIEW — not for construction until checked** — Rev 2.A, 2026-11-09. Drawn: BEN Engine generator; Checked: blank (the operator signs; the set is not for construction until a checker is named in design/rev2/REVISION.json).

| Rev | Date | Description | Checked |
|---|---|---|---|
| 2.A | 2026-11-09 | Rev 2.A: first issue of the BEN Engine Rev 2 design set (docs/REV2_DECISION.md) for review — Rev 2 lineup BEN 1 (both forms), BEN 5, BEN 30, BEN 150, BEN 300, BEN 500, BEN 700 and BEN 2000; brand v2 title blocks with the data plate band; liquid-first dense tiers BEN 300 and BEN 700; non-conductive liner on the wall opposite live parts per EN-001. | not checked |

## EN-001 working space (docs/audit/EN-001_working_space_liner.md)

BEN 2000 cluster: each module as BEN 700 (277 V to ground, ENV-LINER-NC, checks I-D4, I-D6, I-D20 per module through I-K1); yard MV working space NFPA 70 Table 110.34(A) (I-K12) and utility clearance in front of pad-mount doors (I-K11, STUDY)

## Cluster (docs/REV2_DECISION.md §2b, change register R2-05)

Three BEN 700 modules built to the module set [../ben700/](../ben700/INDEX.md) unchanged (the module sheets are not duplicated here), on a shared yard: 12.47 kV service, 15 kV pad-mounted switchgear (1 source + 3 transformer ways), one 1,000 kVA pad-mount transformer and one heat-rejection skid per module. 3 x 666.67 kW = 2000 kW in 15 racks (133.33 kW/rack); 22.43 kW/m² of module footprint, 3.36 kW/m² of fenced yard (594.6 m²), 2.35 kW/m² of site including the two 6.1 m lanes (849.9 m²). STUDY checks need the AHJ's or the utility's value before this set can be checked for construction. The superseded Rev 2.A sheets of the hall (drawn before §2b) are kept in [superseded-hall-2.A/](superseded-hall-2.A/INDEX.md).

## Configuration deviations applied on this set

- DEV-K1: pad-mount transformer footprint 2100 x 2100 mm and mass 4300 kg are estimates (estimate: typical three-phase 1,000 kVA dead-front pad-mount footprint and mass, not read from a datasheet); the yard keeps 1500 mm behind and 3000 mm in front, so a larger unit fits by moving the service lane.
- Every module: DEV-D1: GB300 NVL72 racks are drawn 600 x 1068 (NVIDIA MGX / Supermicro / Cisco datasheet). The Vertiv SmartIT enclosure is 1,200 deep with its rear extension: W 2200 - 200 plenum - 1,200 = 800 mm aisle, below the 900 mm egress, so it is not used in a 2.2 m module.

## Interference checks for this tier (design/layout.py)

| Tier | ID | Sheet | Check | Numbers | Limit | Result | Resolution |
|---|---|---|---|---|---|---|---|
| BEN 2000 | I-K1.1 | A-000 | Module 1 (BEN 700 at 666.7 kW in 5 racks, N+1) passes the stand-alone dense resolver unchanged (_resolve_dense, I-D1..I-D20) | 19/19 module checks pass | <= 0 | **OK** |  |
| BEN 2000 | I-K1.2 | A-000 | Module 2 (BEN 700 at 666.7 kW in 5 racks, N+1) passes the stand-alone dense resolver unchanged (_resolve_dense, I-D1..I-D20) | 19/19 module checks pass | <= 0 | **OK** |  |
| BEN 2000 | I-K1.3 | A-000 | Module 3 (BEN 700 at 666.7 kW in 5 racks, N+1) passes the stand-alone dense resolver unchanged (_resolve_dense, I-D1..I-D20) | 19/19 module checks pass | <= 0 | **OK** |  |
| BEN 2000 | I-K2 | A-000 | Heat-rejection skid of every module where the module layout puts it (item DC1 of _resolve_dense) vs the yard rule (config.CLUSTER_YARD skid_*) | max deviation 0 mm | <= 1 | **OK** |  |
| BEN 2000 | I-K3 | A-000 | Clear distance between adjacent modules (each holds a 130.4 kWh lithium ESS, NFPA 855 scope) vs 3,048 (10 ft): IFC 2021 1207.8.3 / NFPA 855 outdoor ESS clearance to exposures | 3048 vs 3048 | >= 3048 | **OK*** | 10 ft is used without the reduction to 3 ft that UL 9540A large-scale fire test data accepted by the AHJ would allow; the edition adopted locally governs |
| BEN 2000 | I-K4 | A-000 | Exterior path between modules with both cargo leaves folded back (150 mm each) vs 1,118 (44 in, IBC 1020.2 corridor width used conservatively) | 3048 - 2 x 150 = 2748 vs 1118 | >= 1118 | **OK** |  |
| BEN 2000 | I-K5 | A-000 | Door swing: cargo leaf (1219 mm) swings inside the door-end apron, clear of the fire lane | 1219 vs apron 1500 | <= 1500 | **OK** |  |
| BEN 2000 | I-K6 | A-000 | Fire separation between modules if the AHJ classifies each module as a building: fire separation distance to the imaginary line between them vs 914 (IBC Table 705.8: no openings below 3 ft) | 1524 vs 914 | >= 914 | **STUDY** | STUDY: at 1,524 mm (5 ft) IBC Table 705.8 limits openings on the facing long sides (protected openings 15 %) and Table 602 can require 1-hour exterior walls by construction type and occupancy; the steel ISO modules are non-combustible but unrated. If the AHJ treats the modules as listed equipment (NFPA 855 / NFPA 75 enclosures), I-K3 governs. Options: AHJ ruling, or widen the gap to 6,096 (FSD 10 ft). The openings on the long sides (personnel door, louvres) are to be confirmed on the module drawings |
| BEN 2000 | I-K7 | A-000 | Pad-mount transformer (FR3 listed less-flammable liquid) to the nearest module wall or wall-mounted exterior item vs 900 (NFPA 70 450.23, FM DS 5-4; as I-H16) | 7240 vs 900 | >= 900 | **OK** |  |
| BEN 2000 | I-K8 | A-000 | Pad-mount transformer to its heat-rejection skid (non-combustible steel equipment) vs 900 (same rule) | 1500 vs 900 | >= 900 | **OK** |  |
| BEN 2000 | I-K9 | A-000 | Transformer to transformer side clearance vs 900 (FM DS 5-4 less-flammable liquid; utility side clearance for cabinet access) | 3386 vs 900 | >= 900 | **OK** |  |
| BEN 2000 | I-K10 | A-000 | Switchgear to transformer 1 clearance vs 900 (same rule) | 3000 vs 900 | >= 900 | **OK** |  |
| BEN 2000 | I-K11 | A-000 | Working and hot-stick clearance in front of the transformer and switchgear compartment doors | 3000 vs 3000 | >= 3000 | **STUDY** | STUDY: 3,000 mm (10 ft) is the common US utility requirement for pad-mount equipment doors; the serving utility's standard sets the value (and side / back clearances) |
| BEN 2000 | I-K12 | E-001 | 15 kV switchgear working space, NFPA 70 Table 110.34(A): 2,501-9,000 V to ground (12.47Y/7.2 kV), condition 2 = 1,500 | 3200 vs 1500 | >= 1500 | **OK** |  |
| BEN 2000 | I-K13 | E-001 | Transformer size: module total kVA vs 90 % of 1,000 kVA (config loading rule; smallest standard size that passes) | 751.4 vs 900 | <= 900 | **OK** |  |
| BEN 2000 | I-K14 | E-001 | Module main breaker (1200 A) as transformer secondary protection vs 125 % of secondary full-load current (NFPA 70 Table 450.3(A), primary over 1,000 V, secondary <= 1,000 V) | 1200 vs 1.25 x 1203 = 1504 | <= 1503.52 | **OK** |  |
| BEN 2000 | I-K15 | E-001 | Switchgear ways: 1 source + 3 transformer ways vs the 4-way frame | 4 vs 4 | <= 4 | **OK** |  |
| BEN 2000 | I-K16 | E-001 | 12.47 kV service current (total 2254.2 kVA) vs switchgear continuous rating 600 A | 104.4 vs 600 | <= 600 | **OK** |  |
| BEN 2000 | I-K17 | M-001 | Clear gap between adjacent heat-rejection skids vs skid height (2400 mm): side-by-side V-type dry coolers spaced at least one unit height to limit warm-air recirculation | 2886 vs 2400 | >= 2400 | **OK*** | rule of thumb from dry-cooler installation guidance (estimate); confirm with the selected unit's installation manual, or a CFD of the yard |
| BEN 2000 | I-K18 | A-000 | Fire apparatus access road width vs 6,096 (IFC 503.2.1, 20 ft) | 6100 vs 6096 | >= 6096 | **OK** |  |
| BEN 2000 | I-K19 | A-000 | Hose-lay distance from the door-end lane to the farthest exterior wall of a module (along the path between modules) vs 45,720 (IFC 503.1.1, 150 ft) | 15911 vs 45720 | <= 45720 | **OK*** | the service lane on the yard end also reaches the skids and transformers; the AHJ approves the route |
| BEN 2000 | I-K20 | A-000 | Crane access: module set from the door-end lane (crane at mid-lane opposite module 2), radius to the farthest module centre vs 20000 (planning value of I-H19) | 12873 vs 20000 | <= 20000 | **OK** |  |
| BEN 2000 | I-K21 | S-001 | Module pick mass (gross 19300 kg, racks fitted) vs 25000 kg at 20 m (100 t AT crane planning value, as I-H19) | 19300 vs 25000 | <= 25000 | **OK*** | lift plan and load chart from the crane contractor; racks can be set after the module to cut the pick to the module tare + fit-out |
| BEN 2000 | I-K22 | A-000 | Transformer delivery from the service lane: radius to the transformer centre vs 20000 (boom truck or the module crane; transformer mass 4300 kg, estimate) | 8100 vs 20000 | <= 20000 | **OK** |  |
| BEN 2000 | I-K23 | A-000 | Cluster IT load vs 3 x the BEN 700 verified maximum (705 kW in 5 racks, docs/DENSITY.md); module load vs the BEN 700 rating | 2000 vs 2115 (module 666.7 vs 700) | <= 1 | **OK** |  |
