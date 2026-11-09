# Schreiber AI R&D Program 2027–2028 — refresh the BEN Engine lineup

**Sponsor:** Ben Schreiber · **Budget envelope:** USD 5,000,000 core case, USD 10,000,000 full case · **Duration:** 24 months · **Governance:** quarterly gates release money; every claim measured or sourced (`docs/VALIDATION.md` standard).

This is the umbrella plan. The 800 VDC and liquid-cooling workstream has its own detailed plan (`FORWARD_800V_LIQUID_PROGRAM.md`) and is funded from this envelope; its earlier stand-alone USD 5 M figure is superseded by the allocations below.

## 1. What the lineup becomes

| Today (generation 2, Rev C) | Generation 3 (end of program) | Core (5 M) | Full (10 M) |
| --- | --- | --- | --- |
| BEN 5 — 2–5 kW NEMA 4X cabinet, cabinet DX, Controls Lite | **BEN 5** productised: R-513A cooling, battery module, Controls Lite on RevPi with TPM enrolment, sealed Pod W sensors, lighthouse unit built and commissioned | yes | yes |
| BEN 30 — 10 ft module, in-row DX | **BEN 30** carried forward on air with the gen-3 controls kit; liquid option study only | yes | yes |
| BEN 150 — 20 ft module, rear-door + dry cooler, Controls Pro | **BEN 150 AI**: 800 VDC-ready (both conventions) and W45 direct liquid at 75 kW per rack, lighthouse unit built, FAT/SAT, 30-day burn-in; AC/rear-door variant retained for private-cloud buyers | yes (prototype) | yes (prototype + sellable option) |
| BEN 500 — 40 ft module, DLC + CDU | **BEN 500 AI**: liquid-first, DC-ready, two 132–155 kW racks per 10 ft of row, heat-reuse port | design only | prototype built |
| BEN 2000 — capability example | **BEN 2000** engineering release (site plan, power module, plant yard) ready to quote with a modular-building manufacturer | no | yes |
| Modules sold separately (power, cooling, compute, controls) | Two new stand-alone products: **BEN Power 800** (DC sidecar: AC/DC front end + DC busway + battery on bus for other people's racks) and **BEN Cool 600** (row CDU skid with loop twin and leak-to-isolation) | design only | prototypes |
| BEN Controls Lite/Pro, BEN Pod (design), BEN Mesh, BEN Care (software) | **BEN Pod v1 in production** (PCBA, FCC Part 15 modular, provisioning cell), **BEN Controller panel UL 508A listed**, **BEN Care Managed** with fleet learning, DC-bus and loop care, monthly proof of redundancy, SOC 2 Type 1 | Pod + panel listing + Care features | plus SOC 2 and fleet learning in production |

## 2. Workstreams and what each buys

| WS | Workstream | Core (USD) | Full (USD) | Deliverables added by Full |
| --- | --- | --- | --- | --- |
| 1 | **Forward power and liquid** (test cell, 800 VDC both conventions, W45 loop, leak-to-isolation benchmark, BEN 150 AI prototype) | 2,200,000 | 3,600,000 | BEN 500 AI prototype; heat-reuse demonstration; two-phase and immersion evaluation on the cell |
| 2 | **Lighthouse units** (BEN 5 and BEN 150 built at a contract manufacturer, FAT/SAT, 30-day burn-in, commissioning data that calibrates the twin) | 1,000,000 | 1,600,000 | BEN 5 second unit in a severe-climate (H2) site; relocation drill of a unit |
| 3 | **Controls hardware productisation** (BEN Pod v1 PCBA runs, enclosures, provisioning cell with HSM, FCC Part 15 modular testing, BEN Controller UL 508A panel listing on Pro and Lite, EFR32 firmware on target, PLCnext project validated, RevPi TPM enrolment) | 650,000 | 1,000,000 | Pod v1.1 (10BASE-T1S wired variant), second-source radio module, EMC pre-compliance lab |
| 4 | **BEN Care and software** (twin fitted from lighthouse data, DC-bus and loop care, monthly proof of redundancy as a service, live risk scorecard, dashboard HTTPS and roles, security event log, A/B images with dm-verity, full SBOM, edge-side attestation) | 600,000 | 1,100,000 | Fleet learning through Atlas in production; customer BMS integration (Modbus TCP server, SNMP); white-label partner portal |
| 5 | **Standards, listings, compliance** (UL 508A, FCC, NRTL field-evaluation path for DC, PE stamps in three states, arc-flash study, AHJ pre-submissions, OCP membership) | 300,000 | 550,000 | SOC 2 Type 1 for Care Managed; UL 9540 pathway for the battery-on-bus string; CMMC Level 2 readiness for H3 units |
| 6 | **Manufacturing and supply chain** (qualify two contract manufacturers, first-article inspections, SQAM audits, supplier quality agreements, long-lead framework agreements) | 150,000 | 450,000 | Modular-building manufacturer qualified for BEN 2000; consigned-kit logistics cell |
| 7 | **Program management, quality and contingency** | 100,000 + 0 | 300,000 + 1,400,000 | Contingency 14 % released at gates (core case carries no contingency: scope is cut at gates instead) |
| | **Total** | **5,000,000** | **10,000,000** | |

## 3. Team

| Role | Core | Full |
| --- | --- | --- |
| Program lead (Ben Schreiber, design authority) | existing | existing |
| Power electronics engineer | 1 | 1 |
| Thermal / fluids engineer | 1 | 1 |
| Controls and firmware engineer | 1 | 2 |
| Software engineer (twin, Care, dashboard) | 1 | 2 |
| Test and commissioning engineer | 1 | 1 |
| Compliance / quality lead (half-time PE support contracted) | 0.5 | 1 |
| Sourcing and supplier quality | 0.5 | 1 |
| **Total FTE** | **6** | **9** |

## 4. Schedule and gates (24 months)

| Quarter | Gate | Evidence required to release the next tranche |
| --- | --- | --- |
| Q1 | G0 funding; hires; test-cell long-lead orders; primary specifications read (OCP Diablo 400, OCP LVDC SST, NVIDIA 800 VDC, OCP UQD v2, Leak Detection & Intervention); contract manufacturer RFI closed | Signed CM shortlist; design bases drafted |
| Q2 | **G1** BEN 5 lighthouse FAT; BEN Pod v1 first article and FCC pre-scan; 800 VDC design basis reviewed by an outside PE; AHJ and NRTL pre-meetings | FAT report with data hash; PE review memo; NRTL field-evaluation path letter |
| Q3 | **G2** liquid loop running at W45 on the cell with leak-to-isolation measured; BEN 150 (AC) lighthouse FAT; BEN Controller UL 508A listing submitted | Cell data; FAT report; listing application |
| Q4 | **G3** DC bus energised at 150 kW with ground-fault, arc and efficiency tests; BEN 150 lighthouse SAT and 30-day burn-in; twin refitted from lighthouse data; BEN Care Managed live on two units | Measured efficiency table; VALIDATION updated with hardware rows |
| Q5 | **G4** BEN 150 AI prototype engineering release and CM build order; Pod v1 production run; SOC 2 Type 1 audit (full case) | Rev D drawings IFC with named checker; PCBA yield report |
| Q6 | **G5** BEN 150 AI FAT at the CM; BEN 500 AI design freeze (full: build order) | FAT with 12-step commissioning |
| Q7 | **G6** BEN 150 AI SAT and burn-in; BEN Power 800 and BEN Cool 600 prototypes (full) | SAT report; sellable option pricing from measured BOM |
| Q8 | **G7** program close-out: generation-3 lineup released in the selector with measured numbers, BEN 2000 engineering release (full), roadmap for 2029 | Close-out report; audit by the internal auditor against `docs/audit/AUDIT_CHECKLIST.md` |

## 5. Success metrics (measured)

| Metric | Target |
| --- | --- |
| Lighthouse units | Two units (BEN 5, BEN 150) pass FAT and SAT and run 30 days at ≥ 80 % load with zero critical alarms |
| Twin accuracy after refit | Rack inlet, loop ΔT and ride-through predictions inside their stated 95 % intervals on live data |
| Forward architecture | End-to-end efficiency measured against the AC baseline on the same cell; DC ground fault detected ≤ 1 s and isolated; leak-to-isolation ≤ 10 s |
| Controls | Pod v1 passes FCC Part 15; BEN Controller UL 508A listed; firmware runs on target with the 37 host tests ported |
| Care | Monthly proof of redundancy delivered automatically on every managed unit; security roadmap items of MSA 15.5 closed or re-dated by gate |
| Cost | Generation-3 BEN 150 infrastructure price per kW within 10 % of generation 2 |
| Quality | Internal audit at close-out: zero major nonconformities |

## 6. What the money does not do

No greenfield factory (contract manufacturing stays, `docs/MANUFACTURING_STRATEGY.md`), no immersion hardware beyond cell evaluation, no claims before data. Scope beyond the tables goes to `docs/ROADMAP.md`.

## 7. Decision asked of the sponsor

Choose the case. **Core (5 M)** proves the lineup on two lighthouse units and one forward prototype and productises the controls. **Full (10 M)** adds the BEN 500 AI and the two stand-alone products, the BEN 2000 engineering release, SOC 2, a second contract manufacturer and a real contingency. Either case starts with the same first quarter.
