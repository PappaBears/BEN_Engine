# BEN Engine — Engineering Brief (the request, rewritten so it can be built)

**Owner:** Ben Schreiber, Schreiber AI. **Status:** Product mode. **Repo:** PappaBears/BEN_Engine.

This file is the operator's original request rewritten into a brief that a team can build from.
The original wording is preserved at the bottom so later sessions can check for drift.

## 1. One sentence

Schreiber AI designs, builds, commissions and operates **BEN Engine** (Business Edge Node): a family of
all-in-one modular data centers, power, cooling, compute and controls in one sealed enclosure, built from an
outdoor cabinet (BEN 5, a single rack for a small business) and 10, 20 and 40 ft ISO-frame modules (BEN 30, BEN 150
and the liquid-cooled BEN 500 AI pod), element-proof by default (NEMA 4X / IP66) and hardened on request, and
scaling, when a customer needs it, to a single 2 MW center (BEN 2000, a prefabricated modular hall from the same model), with Schreiber AI's control layer
(firmware, digital twin, dashboard, calibration and commissioning tooling) that customers can run
white-label, with their own software, or as a full managed solution.

## 2. Who operates it

| Role | What they need from BEN Engine |
| --- | --- |
| Small/medium business owner | A box that arrives, connects to power, fiber and a pad, and runs their AI and IT with no data-center staff. Clear upfront risks and a price. |
| Schreiber AI field tech / integrator | Assembly instructions a new hire can follow, a commissioning script that proves the build, and a maintenance schedule. |
| Schreiber AI operations | One dashboard for every deployed unit, live data, automated sweeps, alarms, CSV export, and a model that predicts what the box will do before it does it. |
| White-label partner | The hardware plus the controls layer under their brand, or just one subsystem (power only, cooling only, compute only). |
| Investor | A defensible, capital-efficient proposition with a real build, real parts, real prices and a verified demo. |

## 3. The product family (the "base model" and the selector)

The base model is one **configuration schema** (`spec/ben-config.schema.json`) and one set of
sizing rules (`software/ben_engine/config.py`). The selector produces a configuration; everything
else (bill of materials, drawings, digital twin, dashboard 3D scene, commissioning checklist,
compliance matrix) is generated from that configuration. Changing a value in the selector changes
every downstream deliverable consistently.

Names follow the nominal maximum IT kW (`docs/TIER_AND_ENCLOSURE_DECISION.md`); the enclosure is described by its size. The core product is the all-in-one box, BEN 5 through BEN 500 (`positioning: core` in `TIER_GEOMETRY`); BEN 2000 is the capability example (`positioning: capability`): the same system scaled to a 2 MW hall, kept fully engineered but not the lead. Generation-1 keys (`micro`, `ben10`, `ben20`, `ben40`) still load through the alias map in `config.py`.

| Tier | Enclosure (off the shelf, sealed to NEMA 4X / IP66) | IT load | Racks | Cooling | Power | Controls (default) |
| --- | --- | --- | --- | --- | --- | --- |
| **BEN 5** | NEMA 4X / IP66 outdoor 24U cabinet with integral air conditioner, on a skid | 2–5 kW | 1 | Cabinet DX air conditioner | 208/240 V 1φ, 30–50 A; 3–6 kVA UPS | BEN Controls Lite: Revolution Pi RevPi Connect 4 + 3 BEN Pods |
| **BEN 30** | 10 ft high-cube ISO-frame module | 10–30 kW | 1–2 | In-row DX, hot-aisle containment, economizer | 208 V 3φ 100 A; 20–30 kVA UPS | Lite (Pro selectable; Pro default for healthcare, public sector, AI training) |
| **BEN 150** | 20 ft high-cube ISO-frame module | 50–150 kW | 4–6 | In-row DX or rear-door heat exchangers + dry cooler; DLC option | 480 V 3φ 400 A; 150 kVA modular UPS | BEN Controls Pro: PLCnext AXC F 2152 + Axioline I/O in a UL 508A panel, OnLogic Karbon 400 edge computer, 2 Pods per rack + 2 |
| **BEN 500** | 40 ft high-cube ISO-frame module | 150–500 kW | 8–12 | Direct liquid cooling with CDU + external dry cooler; RDHx | 480 V 3φ 800–1200 A; modular UPS, generator ready | BEN Controls Pro |
| **BEN 2000** | Prefabricated wide-body modular hall: 3 site-joined 12.2 × 3.66 × 4.2 m steel modules (36.6 × 11.0 m hall) + power module + plant yard | 800–2,000 kW | up to 48 (4 rows of 12) | Direct liquid cooling, N+1 CDU row, fan-wall residual air; adiabatic dry coolers in the plant yard (dry mode available) | 12.47 / 13.8 kV MV service → 2 × 2,500 kVA pad-mount transformers (2N) → 480 V UL 1558 switchgear; 2N UPS (2 × 2,000 kW strings), NFPA 855 battery rooms; N+1 generators 3 × 1,250 kW, 48 h fuel | BEN Controls Pro: redundant edge computers, one PLC per module + plant PLC, BEN Mesh with multiple border routers |

Every tier ships at hardening level **H1** (watertight, corrosion class C3). **H2 Severe environment** (flood plinth, C5-M, 67 m/s wind, dust filtration) and **H3 Hardened / government** (UL 752 ballistic panels, ASTM F3038 forced-entry doors, IK10, HEMP shielding option, TEMPEST-ready separation, mantrap) are selectable per unit.

Controls hardware is the industrial platform in `docs/CONTROLS_HARDWARE_DECISION.md`: both tiers run the same software, the same BEN Pods on the BEN Mesh (Thread, Silicon Labs MGM240P with Secure Vault High) and the same protocol; life safety is hardwired in both.

Subsystems are selectable separately: **Power module**, **Cooling module**, **Compute module**,
**Controls module**. A customer can buy any one of them or all of them.

## 4. Mission profiles

AI inference edge · AI training pod · Private cloud / ERP · Disaster recovery · Industrial OT
analytics · Healthcare (HIPAA) · Public sector / tactical · Remote / off-grid. A profile sets the
ASHRAE environmental class, redundancy (N, N+1, 2N), climate package, compliance set and the risk
list that must be disclosed on the product page before purchase.

## 5. What must be delivered (acceptance list)

| # | Deliverable | Where | Done when |
| --- | --- | --- | --- |
| 1 | Issue-for-construction drawing set per tier with CTQ/CTP callouts | `design/drawings/` | Drawings generated from the config; every CTQ has a check method and tolerance; BEN 2000 adds a site plan (A-000) and per-module sheets |
| 2 | Assembly renders + Simplified Technical English assembly instructions | `design/renders/`, `design/assembly/` | A worker with no data-center experience can follow numbered steps with one action per step |
| 3 | Manufacturing process flow, design to field deployed | `docs/PROCESS_FLOW.md` | Every stage has an owner, inputs, outputs, hold points and records |
| 4 | Firmware for the BEN Pods (MGM240P / OpenThread) and the BEN Controller (edge image, PLC project), with spec sheets and one-line wiring diagrams | `firmware/`, `design/specs/` | Compiles; unit tests pass on host; protocol documented; EFR32 build and attestation status stated honestly |
| 5 | Commissioning script usable by Schreiber AI or the customer | `software/ben_engine/commissioning.py` | Runs against the simulator end to end and produces a signed report |
| 6 | Turnover package and maintenance schedule (outdoor) | `docs/TURNOVER.md`, `docs/MAINTENANCE.md` | Intervals, tasks, parts, and records for every subsystem and the envelope |
| 7 | Compliance matrix | `docs/COMPLIANCE.md` | Each applicable code or standard mapped to a design feature and a verification |
| 8 | Web dashboard: live data, 3D twin, walkthrough, sweeps, CSV export, I/O test | `dashboard/` | Runs with no hardware in simulation mode; Playwright test passes; screenshots recorded |
| 9 | Calibration and analysis tools | `software/ben_engine/calibration.py`, `analysis.py` | GUM uncertainty budgets; model fit from commissioning sweep; predictions with intervals |
| 10 | CFD | `software/ben_engine/cfd.py` | 2D thermal lattice-Boltzmann airflow solver runs per tier; results feed the twin |
| 11 | Parts list with real parts, real prices, confirmation status, quantities | `purchasing/bom.csv`, `docs/BOM.md` | Every line has a vendor, a price, and `confirmed` / `list price` / `estimate` |
| 12 | Purchasing questions queued as emails to Ben@SchreiberAI.com | `purchasing/email_queue/` + Gmail drafts | One email per supplier question; nothing sent |
| 13 | Build, wiring and test guide with experiments | `docs/BUILD_AND_WIRING.md`, `docs/TEST_GUIDE.md` | Experiments have hypothesis, setup, measurement, pass criterion |
| 14 | Product page for SchreiberAI.com with mission profile picker and upfront risks | `web/` | Static page; picker drives configuration; risks shown before pricing |
| 15 | Marketing kit and Schreiber AI branding | `web/kit/` | Logo, palette, type, one-pagers, copy blocks |
| 16 | Venture capital proposition and deck | `docs/investors/` | Problem, solution, market, business model, unit economics from the BOM, ask, use of funds |
| 17 | Simulated end-to-end test | `tests/test_e2e.py` (pytest, runs the commissioning script in simulation and checks report, CSV and hash) and `tests/e2e/` (browser) | Config → twin → commissioning → sweep → CSV; the pytest gate runs in CI, the browser suite on demand |
| 18 | Honest final report | `docs/VALIDATION.md` | Verified / unverified / least accurate stated per capability |
| 19 | Proposal generator: selector → complete customer proposal | `software/ben_engine/proposal.py`, `docs/proposals/` | One command produces scope, price by purchase option, schedule, drawings list, compliance pack, risks, site requirements, acceptance, terms |
| 20 | Paperwork set, two-sided | `docs/contracts/` | Customer: MSA, SOW, change order, acceptance certificates, software licence, SLA, warranty, NDA. Partner/supply: integrator agreement, contract manufacturing agreement, supplier PO terms with delivery liquidated damages flowing back-to-back; customer scope-change and delay clauses |
| 21 | Manufacturing strategy: third-party first | `docs/MANUFACTURING_STRATEGY.md`, revised `docs/PROCESS_FLOW.md` | Contract manufacturers and integrators build; Schreiber AI is design authority, controls, commissioning and operations; greenfield factory is a later study |
| 25 | Forward architecture options: 800 VDC power and high-density liquid | `software/ben_engine/config.py`, `docs/FORWARD_ARCHITECTURE_DECISION.md`, `docs/research/` | Options selectable with sizing, BOM, drawings for review, twin and commissioning steps; existing presets unchanged |
| 26 | R&D Program 2027–2028, USD 5 M core / 10 M full, lineup refresh | `docs/programs/RD_PROGRAM_2027.md`, `docs/programs/FORWARD_800V_LIQUID_PROGRAM.md` | Lineup table, workstream budgets for both cases, team, quarterly gates, measured success metrics |
| 22 | Deal package assembler | `software/ben_engine/package.py` | One command assembles the customer deal package and the partner onboarding package for a configuration |
| 23 | BEN 2000 single 2 MW center | `config.py` (`ben2000`), `docs/COMPLIANCE.md` §14, `PROCESS_FLOW.md`, `SITE_REQUIREMENTS.md`, `MAINTENANCE.md`, `BUILD_AND_WIRING.md` | Sizing (MV service, transformers, UPS strings, generators, CDUs per module) generated from the config; building-permit, MV-service, NFPA 855 battery-room, NFPA 110 Level 1, SPCC and ASHRAE 188 rows in the compliance pack; ~52-week order-to-service plan with the utility lead time on the critical path |
| 24 | Enclosure hardening H1/H2/H3 | `config.py` (`hardening`), `COMPLIANCE.md` §15, `TEST_GUIDE.md` E14, contracts | Every unit IP66 and hose-tested; H2/H3 packages priced from catalog lines, their tests (UL 752, ASTM F3038, IEEE 299 shielding) in the compliance pack, maintenance add-ons and warranty terms tied to the hose test |

## 6. Constraints the operator set

- Minimize purchased parts; what is purchased must be real, priced, and the price confirmation state stated.
- Looks and feels like a premium product.
- Assembly by workers with minimal experience; instructions in Simplified Technical English.
- Compliance is central, not an appendix.
- Risks disclosed upfront on the product page.
- No questions back to the operator; decisions are recorded as reversible decisions in `docs/PROJECT_NOTES.md`.
- Finish with what was verified, what was not, and what is expected to be least accurate.

## 7. What the original request was missing (added by this brief)

1. **A shared configuration model.** Without it the BOM, drawings, twin and website drift apart.
2. **A measurement plan.** Which sensors, where, what uncertainty, how calibrated, how tared, and how wall and placement effects are handled.
3. **A power chain definition** with fault levels, selective coordination and arc-flash labeling as design items.
4. **Site requirements** (pad, grounding, utility service, fiber, setbacks, permits) as a deliverable the customer signs before the container ships.
5. **Cybersecurity** for the controls layer (IEC 62443 zones, no cloud dependency, signed firmware, local-first data).
6. **Service model and economics**: managed service, white-label and hardware-only tiers each need a margin model; the VC proposition depends on it.
7. **Transport and lifting**: CSC plate validity, tie-downs, crane/forklift pockets, weight distribution, and road permits.
8. **Decommissioning and relocation**: containers move; the design must survive a second deployment.
9. **Data recovery is separate from code recovery**: the edge computer database needs its own backup plan.
10. **An investor-grade proposition** (added at the operator's request mid-session).
11. **Proposal-level output from the selector** and the **two-sided paperwork** (customer deals; integrator, contract-manufacturer and supplier agreements) with liquidated damages and scope-change rules that flow back-to-back (added mid-session).
12. **Third-party manufacturing first**, greenfield factory later (added mid-session).
13. **Power-based names, a 2 MW center and element-proof enclosures** (operator steering 2026-11-08, `docs/TIER_AND_ENCLOSURE_DECISION.md`): the number in the name is the IT kW, not the container length; BEN 2000 is a prefabricated modular hall rather than a container; NEMA 3R is gone and every unit is NEMA 4X / IP66 with optional H2/H3 hardening.

## 8. Original request (verbatim, preserved)

> Design a complete modular data center that can be built in an ISO container or other type of modified "Off the shelf" container … [full text in `docs/ORIGINAL_REQUEST.md`]
