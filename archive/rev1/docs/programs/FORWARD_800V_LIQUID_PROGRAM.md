# Forward Architecture Program — 800 VDC power and high-density liquid cooling

**Sponsor:** Ben Schreiber, Schreiber AI · **Budget:** funded from the umbrella R&D program (`RD_PROGRAM_2027.md`: USD 2.2 M core case, USD 3.6 M full case; the detailed table below is the full-scope costing that the umbrella trims at gates) · **Duration:** 18 months from funding · **Decision basis:** `docs/FORWARD_ARCHITECTURE_DECISION.md` · **Evidence basis:** `docs/research/STATE_OF_THE_ART_2026.md`

## 1. Objective

Make BEN Engine the first sealed, relocatable 150–500 kW module that integrators can buy **DC-ready (800 VDC) and liquid-first (W45 direct-to-chip)** with open, local-first controls, and prove it on a test cell and a prototype, not on slides. Everything this program claims is measured on hardware we own or quoted with a source.

## 2. Workstreams, deliverables and gates

| WS | Workstream | Deliverables | Gate (go / no-go evidence) |
| --- | --- | --- | --- |
| A | **800 VDC power architecture** | Design basis for DC distribution in a module covering **both** conventions (OCP Diablo 400 ±400 VDC bipolar with midpoint ground; NVIDIA/OCP 800 VDC unipolar) with a voltage-programmable front end; AC/DC front end selection (SiC rectifier vs solid-state transformer); DC busway, protection, insulation monitoring and arc detection; battery-on-bus; grounding and arc-flash method; drawings E-001-DC | G1 (M4): paper design reviewed by an outside PE; G3 (M9): 150 kW test-cell bus energised, ground-fault and arc tests passed, efficiency measured |
| B | **High-density liquid cooling** | Row CDU selection, manifold and quick-disconnect standard, W45 loop design, leak-to-isolation design, dry-cooler and heat-reuse interface, M-001-HD drawings; immersion and two-phase as a written study | G2 (M6): 200 kW loop running on the test cell at W45 with measured ΔT, flow and leak-to-isolation time |
| C | **Controls, twin and BEN Care for DC and liquid** | DC-bus twin (voltage, IMD, arc events), loop twin (flow, ΔT, pump failover), new sweeps and commissioning steps, Pod channels, dashboard objects, calibration budgets for flow and ΔT | G2/G3: twin predictions within stated intervals against test-cell data |
| D | **Standards, listings and partnerships** | NEC 2026 DC article mapping with an AHJ, UL 508A panel for DC, field-evaluation plan for DC gear, OCP participation, two component partners (power, cooling) under NDA/MSA, insurer review | G4 (M12): written path to a listed/field-evaluated DC distribution in a BEN 150; partner agreements signed |
| E | **Forward prototype BEN 150 (dc800 + dlc_hd)** | One unit built with a contract manufacturer, FAT with the commissioning script (new steps included), 30-day burn-in at 150 kW with load banks and a liquid test load, SAT on Schreiber AI's pad | G5 (M15): prototype passes FAT/SAT; data published in VALIDATION; sellable option at M18 |

## 3. Budget (USD 5,000,000)

| Line | Amount | Basis |
| --- | --- | --- |
| Engineering team (18 months): power electronics engineer, thermal/fluids engineer, controls/firmware engineer, test engineer, half-time PE/compliance lead, program manager | 1,650,000 | 5.5 FTE × 18 months, loaded |
| Test cell: 800 VDC bench (AC/DC front end 150 kW, DC busway, protection, IMD, DC load bank, battery string), liquid loop (200 kW CDU, manifolds, liquid test load, dry cooler, instrumentation), data acquisition, safety (DC-rated PPE, interlocks, arc-rated enclosure) | 1,200,000 | Vendor estimates in `purchasing/` once quoted; this is the ceiling |
| Forward prototype BEN 150 (module, DC power train, 2 racks at 75 kW liquid, CM build, FAT/SAT, 30-day burn-in energy) | 1,050,000 | Forward BOM `docs/BOM-ben150-forward.md` plus CM labour and test energy |
| Standards, listings, field evaluation, PE stamps, insurer review, OCP membership, lab fees | 350,000 | UL 508A DC panel, NRTL field evaluation, arc-flash study, third-party test witness |
| Partnerships and component NRE (quick-disconnect tooling, manifold design, rectifier integration kits) | 250,000 | Two component partners |
| Contingency (10 %) | 500,000 | Released by the sponsor at gates |
| **Total** | **5,000,000** | |

Cash timing: 35 % in months 1–6 (team, test-cell orders), 40 % in months 7–12 (prototype build, listings), 25 % in months 13–18 (SAT, burn-in, productisation).

## 4. Schedule and gates

| Month | Milestone |
| --- | --- |
| 0 | Funding; hires; test-cell long-lead orders (front end, CDU, DC breakers, IMD) placed |
| 1 | Primary specifications read in full (OCP Diablo 400, OCP LVDC SST v0.3, NVIDIA 800 VDC white paper, Schneider WP219/WP220, Lenovo GB300 liquid guide, OCP UQD v2.0.0 and Leak Detection & Intervention); research baseline corrected and frozen |
| 2 | Design basis drafts for WS A and B; AHJ and NRTL pre-meetings booked (field-evaluation route per NFPA 791 assumed until NEC 2029) |
| 4 | **G1** external PE review of the 800 VDC design basis; AHJ pre-meeting held |
| 6 | **G2** liquid loop running at W45 on the test cell; leak-to-isolation time measured |
| 9 | **G3** DC bus energised at 150 kW; ground-fault, arc and efficiency tests passed; twin validated against the cell |
| 10 | Forward prototype engineering release (Rev D drawings, forward BOM frozen); CM build order |
| 12 | **G4** listing/field-evaluation path written and accepted by the NRTL and the insurer; partner MSAs signed |
| 15 | **G5** prototype FAT at the CM, SAT on our pad, 30-day burn-in starts |
| 18 | Sellable options `power_architecture=dc800` and `cooling=dlc_hd` in the selector with measured numbers; program close-out report |

## 5. Success metrics (measured, not claimed)

| Metric | Target | How measured |
| --- | --- | --- |
| End-to-end electrical efficiency, utility to rack input, at 50–100 % load | ≥ 2 points better than the AC baseline module | Test-cell power analysers both sides, same load bank |
| DC ground-fault detection and isolation | Detected ≤ 1 s, isolated per design basis, no nuisance trips in 30-day burn-in | Injected faults on the cell (E17) |
| Liquid loop | 75 kW per rack at W45 supply with rack ΔT in the design band and pumps sized for W45 flow (about 3× the 25 °C flow per vendor tables); leak-to-isolation ≤ 10 s, published as a benchmark because none exists | E18–E20 |
| Twin accuracy | Bus voltage, loop ΔT and ride-through predictions inside their stated 95 % intervals | Commissioning data vs `analysis.py` |
| Cost | Forward BEN 150 infrastructure price per kW within 10 % of the AC BEN 150 | BOM at prototype close-out |
| Safety | Zero recordable incidents; arc-flash labels and procedures signed by a PE | Program safety log |

## 6. Risks specific to this program

| Risk | Mitigation |
| --- | --- |
| Listed 800 VDC distribution gear not available at 150 kW scale in time | Field evaluation path (NFPA 791) with the NRTL agreed at G1; design the bus so AC fallback racks remain possible |
| Two DC conventions (±400 V bipolar vs 800 V unipolar) and unpublished 2027 rack power/water figures | Front end and grounding designed for both conventions; module sized for one or two current liquid racks; re-baseline at G1 when primary specs are read |
| DC arc-flash methods immature | Conservative PPE and remote racking; third-party arc-flash study; test-cell energisation behind barriers only |
| Liquid in a sealed module | Leak-to-isolation designed and measured; drip trays and sump; coolant chosen for non-conductive residual (study immersion only as a paper option) |
| Program scope creep | Gates release money; anything not on the deliverable list goes to the roadmap |

## 7. What the program does not do

It does not build BEN 2000, does not pursue immersion hardware, and does not claim efficiency or density numbers before G3/G5 data exists.
