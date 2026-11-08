# BEN Engine — Engineering Brief (the request, rewritten so it can be built)

**Owner:** Ben Schreiber, Schreiber AI. **Status:** Product mode. **Repo:** PappaBears/BEN_Engine.

This file is the operator's original request rewritten into a brief that a team can build from.
The original wording is preserved at the bottom so later sessions can check for drift.

## 1. One sentence

Schreiber AI designs, builds, commissions and operates **BEN Engine** (Business Edge Node): a family of
modular data centers built from off-the-shelf ISO containers and outdoor cabinets, sized from a single
rack for a small business up to a 40 ft liquid-cooled AI pod, with Schreiber AI's control layer
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

| Tier | Enclosure (off the shelf) | IT load | Racks | Cooling | Power | Controls (default) |
| --- | --- | --- | --- | --- | --- | --- |
| **BEN 5** | NEMA 4X / IP66 / IP55 outdoor 24U cabinet with integral air conditioner, on a skid | 3–8 kW | 1 | Cabinet DX air conditioner | 208/240 V 1φ, 30–50 A; 3–6 kVA UPS | BEN Controls Lite: Revolution Pi RevPi Connect 4 + 3 BEN Pods |
| **BEN 30** | 10 ft high-cube ISO container | 10–30 kW | 1–2 | In-row DX, hot-aisle containment, economizer | 208 V 3φ 100 A; 20–30 kVA UPS | Lite (Pro selectable; Pro default for healthcare, public sector, AI training) |
| **BEN 150** | 20 ft high-cube ISO container | 50–150 kW | 4–6 | In-row DX or rear-door heat exchangers + dry cooler; DLC option | 480 V 3φ 400 A; 150 kVA modular UPS | BEN Controls Pro: PLCnext AXC F 2152 + Axioline I/O in a UL 508A panel, OnLogic Karbon 400 edge computer, 2 Pods per rack + 2 |
| **BEN 500** | 40 ft high-cube ISO container | 150–500 kW | 8–12 | Direct liquid cooling with CDU + external dry cooler; RDHx | 480 V 3φ 800–1200 A; modular UPS, generator ready | BEN Controls Pro |

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
| 1 | Issue-for-construction drawing set per tier with CTQ/CTP callouts | `design/drawings/` | Drawings generated from the config; every CTQ has a check method and tolerance |
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
| 17 | Simulated end-to-end test | `tests/test_e2e.py` | Config → twin → commissioning → sweep → CSV; passes in CI |
| 18 | Honest final report | `docs/VALIDATION.md` | Verified / unverified / least accurate stated per capability |
| 19 | Proposal generator: selector → complete customer proposal | `software/ben_engine/proposal.py`, `docs/proposals/` | One command produces scope, price by purchase option, schedule, drawings list, compliance pack, risks, site requirements, acceptance, terms |
| 20 | Paperwork set, two-sided | `docs/contracts/` | Customer: MSA, SOW, change order, acceptance certificates, software licence, SLA, warranty, NDA. Partner/supply: integrator agreement, contract manufacturing agreement, supplier PO terms with delivery liquidated damages flowing back-to-back; customer scope-change and delay clauses |
| 21 | Manufacturing strategy: third-party first | `docs/MANUFACTURING_STRATEGY.md`, revised `docs/PROCESS_FLOW.md` | Contract manufacturers and integrators build; Schreiber AI is design authority, controls, commissioning and operations; greenfield factory is a later study |
| 22 | Deal package assembler | `software/ben_engine/package.py` | One command assembles the customer deal package and the partner onboarding package for a configuration |

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

## 8. Original request (verbatim, preserved)

> Design a complete modular data center that can be built in an ISO container or other type of modified "Off the shelf" container … [full text in `docs/ORIGINAL_REQUEST.md`]
