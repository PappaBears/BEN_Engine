# Tier naming, the 2 MW center, and enclosure protection — decision

**Status:** decided 2026-11-08 from operator steering. Binding for the generation-2 refactor of `software/ben_engine/config.py` and everything generated from it.

## 1. Names follow IT power, not container length

| New key | New name | IT load | Enclosure | Old key |
| --- | --- | --- | --- | --- |
| `ben5` | **BEN 5** | 2–5 kW | Outdoor NEMA 4X / IP66 24U cabinet on a skid | `micro` |
| `ben30` | **BEN 30** | 10–30 kW | 10 ft high-cube ISO-frame module, sealed to IP66 | `ben10` |
| `ben150` | **BEN 150** | 50–150 kW | 20 ft high-cube ISO-frame module, sealed to IP66 | `ben20` |
| `ben500` | **BEN 500** | 150–500 kW | 40 ft high-cube ISO-frame module, sealed to IP66 | `ben40` |
| `ben2000` | **BEN 2000** | 800–2,000 kW | Single center: prefabricated wide-body modular hall, 3 site-joined 12.2 m modules plus a separate power module and plant yard | new |

The number is the nominal maximum IT kW. Marketing, drawings folders, CLI arguments, catalog `applies_to_tiers`, JSON schema, website selector and tests all use the new keys. A compatibility alias map (`micro→ben5`, `ben10→ben30`, `ben20→ben150`, `ben40→ben500`) is kept in `config.py` so saved configurations and URLs still load, and `Config.from_dict` normalises them.

## 2. BEN 2000 — the single 2 MW center

Not a container. A **prefabricated, relocatable data hall** built from factory-finished wide-body steel modules (each 12.2 m × 3.66 m × 4.2 m external, road-transportable on a flatbed with permits), site-joined into one sealed envelope, plus a **power module** and a **plant yard**.

| Item | Design value |
| --- | --- |
| IT load | 800–2,000 kW, up to 48 racks at 40 kW average (DLC), 4 rows of 12 |
| Hall | 3 modules joined: 36.6 m × 11.0 m × 4.2 m external; interior 35.8 × 10.4 × 3.6 m; raised-floor-free, overhead busway and DLC manifolds |
| Cooling | Direct liquid cooling (CDU row, N+1) with air-side residual by in-row/fan-wall units; heat rejection by **adiabatic dry coolers** in the plant yard (water-free mode available); chilled-water option for climates above 40 °C design |
| Power | Medium-voltage service (12.47 or 13.8 kV) to pad-mount transformers 2 × 2,500 kVA (2N), 480 V switchgear in the power module, modular UPS 2N (2 × 2,000 kW strings), lithium battery rooms per NFPA 855 with 2-hour separation, N+1 generators (3 × 1,250 kW) with 48 h fuel |
| Fire | Clean agent per module with VESDA, pre-action option for the hall, hydrant coverage per AHJ |
| Structure | Pre-engineered steel modules on a slab-on-grade with grade beams; wind, snow, seismic per climate package; IBC Group B/F-1 occupancy classification to be agreed with the AHJ (this one is a building) |
| Controls | BEN Controls Pro, redundant edge computers, one PLC per module plus a plant PLC, BEN Mesh with multiple border routers |
| Staffing | Designed for lights-out operation with a service vestibule, NOC-less under BEN Care Managed |

Sizing rules in `config.py` extend naturally: cooling units per module, UPS strings per 1,000 kW, service in kVA at medium voltage with transformer count, gross mass per module, PUE estimate with adiabatic rejection. Drawings are generated per module plus a site plan.

## 3. Enclosure protection: element-proof by default, hardening levels on top

NEMA 3R is dropped everywhere. The baseline for every tier is **watertight and corrosion-resistant**:

| Level | Name | Enclosure rating | Corrosion | Structural | Security | Intended for |
| --- | --- | --- | --- | --- | --- | --- |
| **H1** | Standard | NEMA 4X / IP66 envelope; all penetrations gasketed and tested (hose test per UL 50E); doors with compression gaskets and three-point latches; drip edges; positive-pressure interior | ISO 12944 C3 coating system | Wind and snow per climate package; seismic per ASCE 7 site class | Keyed access, door contacts, camera-ready | Most commercial sites |
| **H2** | Severe environment | NEMA 4X / IP66 plus flood plinth 600 mm, sand/dust filtration (ISO 16890 ePM1 + weather hoods), hurricane-rated door hardware, roof snow guards | ISO 12944 C5-M (marine), stainless fasteners, sacrificial anodes on skids | Wind 67 m/s, snow 3 kPa, seismic SDC D | As H1 plus intrusion detection and lighting | Coastal, desert, arctic, hurricane zones |
| **H3** | Hardened / government | As H2 plus ballistic wall panels (UL 752 Level 3–8 selectable), IK10 impact doors, forced-entry rated doors (ASTM F3038), EMI/EMP shielding option (MIL-STD-188-125-1 HEMP, 80 dB shielded enclosure with filtered penetrations), TEMPEST-ready separation, tamper-evident seals, secure vestibule with mantrap, hardened conduit | ISO 12944 C5-M | As H2 | Two-factor access, intrusion and tamper detection on the PLC, audit trail in BEN Care, CMMC/NIST 800-171 controls pack | Public sector, defence, utilities, critical infrastructure |

`Config.hardening: "H1"|"H2"|"H3"` (default by profile: public_sector → H3 option offered, coastal/hot_arid/cold climates → H2 default, else H1). Derived outputs: envelope mass adder, cost adders via catalog lines with `applies_to_hardening`, compliance pack rows (UL 50E type 4X test, UL 752, ASTM F3038, MIL-STD-188-125), risk register entries, maintenance add-ons (gasket inspection, anode replacement, shield integrity test).

## 4. What this changes in the repository

- `config.py`: new keys and labels, alias map, `ben2000` geometry and sizing rules, `hardening` field, BEN 5 cabinet rated NEMA 4X.
- `parts_catalog.json`: `applies_to_tiers` migrated to new keys; new lines for the 2 MW center (MV gear, transformers, 2 MW UPS strings, generators, CDU rows, adiabatic dry coolers, wide-body modules, slab allowances) and for hardening levels (ballistic panels, shielding, forced-entry doors, flood plinth, C5-M coating).
- Drawings, renders, assembly, SQAM, wiring: regenerated per tier; BEN 2000 gets a site plan sheet (A-000) and per-module sheets.
- Twin, CFD, sweeps: BEN 2000 handled as modules; CFD per module.
- Website, dashboard, proposal, contracts field vocabulary (`TIER` enum), decks, README, FAQ, VC, process flow durations (BEN 2000 ~ 40–52 weeks), compliance (building occupancy, MV service, SPCC for generator fuel).
