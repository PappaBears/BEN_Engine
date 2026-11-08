<p align="center"><img src="web/kit/wordmark-ben-engine.svg" alt="BEN Engine, Business Edge Node, by Schreiber AI" width="420"></p>

# BEN Engine — modular data centers you can run before they exist

**For** small and mid-size businesses, integrators and public-sector sites that want AI and IT on their own pad.
**The problem:** cloud bills that scale with success, colocation priced for hyperscalers, server closets nobody commissioned.
**The outcome:** a family of modular data centers (BEN 5 2–5 kW cabinet, BEN 30/150/500 sealed ISO-frame modules to 500 kW, and the 2 MW BEN 2000 prefabricated hall; every unit NEMA 4X / IP66 with H1/H2/H3 hardening) built from off-the-shelf enclosures, with Schreiber AI's controls layer, digital twin, commissioning script and a complete, generated deal package. Every drawing, part, price, alarm threshold and proposal comes from one configuration model.

![BEN Engine dashboard guided tour: the 3-D twin of a BEN 150 with cutaway, racks, rear-door heat exchangers and roof dry coolers](docs/media/demo.gif)

<sub>Static poster: [docs/media/demo-poster.png](docs/media/demo-poster.png). Real capture of the dashboard in simulation mode.</sub>

## What is here, and how verified it is

| Capability | Where | Status |
| --- | --- | --- |
| Configuration model: tiers, profiles, climates, sizing, validation (rows that do not fit are rejected) | `software/ben_engine/config.py`, `spec/` | verified (tests, 5 tiers × 8 profiles × climates × 3 hardening levels; BEN 2000 downstream generators pending, see VALIDATION §4a) |
| Digital twin: thermal + power chain, 7 faults, ASHRAE-class alarms | `software/ben_engine/twin.py` | verified in simulation |
| 2-D thermal lattice-Boltzmann CFD per tier, recirculation profile into the twin | `software/ben_engine/cfd.py` | verified (runs, converges); relative tool only |
| Calibration (GUM budgets, tares, placement effects) and analysis (parameter fit, 95 % prediction intervals, ride-through) | `calibration.py`, `analysis.py` | verified on synthetic data |
| Automated sweeps with pass/fail and CSV | `sweeps.py` | verified (6/6 pass on BEN 150) |
| Commissioning script, FAT/SAT, signed report with SHA-256 | `commissioning.py` | verified in simulation (10/10 steps) |
| Dashboard: 3-D twin, walkthrough, guided tour, sweeps, fault injection, I/O test, calibration, CFD, export, **proposal** | `dashboard/`, `api.py` | verified (26 API tests, Playwright e2e with screenshots) |
| Proposal generator: selector → 16-section customer proposal, md/html/json, contract pre-fill | `proposal.py`, `docs/proposals/` | verified (16 tests; rendered and inspected) |
| Deal package assembler: customer package + partner package as zips | `package.py` | verified (tests; sample built) |
| Firmware: BEN Pod core (calibration, telemetry, commands, ring buffer, failsafe) on Silicon Labs MGM240P / Thread | `firmware/ben-pod` | verified on host (37 unit tests); **EFR32MG24 cross-build and Secure Vault attestation unverified** |
| BEN Controller: industrial edge computer image (OnLogic Karbon 400, TPM: broker, OTBR, services, firewall, backups) + PLCnext PLC project (interlocks, watchdog); Revolution Pi image for BEN Controls Lite | `firmware/ben-edge` | implemented, unverified on hardware |
| Controls hardware platform: BEN Controls Pro (PLCnext AXC F 2152 + Axioline I/O in a UL 508A panel) and BEN Controls Lite (RevPi Connect 4), BEN Pods on BEN Mesh, priced in the catalog, selected by `Config.controls_tier` | `docs/CONTROLS_HARDWARE_DECISION.md`, `purchasing/parts_catalog.json` | decided and costed; hardware not yet built |
| IFC drawing set (7 sheets × 4 tiers) with CTQ/CTP tables, interference checks | `design/drawings/` | verified (generated, inspected) |
| Concept assembly renders and ASD-STE100 assembly instructions, QC forms, CTQ cards | `design/renders/`, `design/assembly/` | verified (generated; STE rules checked by script) |
| Supplier Quality Assurance Manual generated from the CTQ register | `docs/SQAM.md` | verified (generated) |
| Bill of materials with price confidence (confirmed / list / estimate) and 16 queued RFQ emails | `purchasing/`, `docs/BOM.md` | verified (21 tests); prices are listings, not quotes |
| Compliance matrix, risk register, process flow (third-party manufacturing), site requirements, turnover, maintenance, build & wiring, test guide, cybersecurity | `docs/` | written; edition years checked where possible |
| Two-sided paperwork: MSA, SOW, change order, acceptance, licence, SLA, warranty, NDA, integrator, contract manufacturing, supplier terms | `docs/contracts/` | templates for counsel review |
| Product page with mission profile picker, risks before price, configurator | `web/` | verified (rendered desktop + 390 px) |
| Investor proposition and decks with speaker notes | `docs/investors/`, `docs/presentation/` | written; numbers from the BOM |

The honest ledger, including what is least accurate, is `docs/VALIDATION.md`.

## Quickstart

```bash
pip install -r requirements.txt
PYTHONPATH=software python -m pytest tests -q --ignore=tests/e2e
bash scripts/run_dashboard.sh        # open http://localhost:8080
```

First success: the dashboard opens on a BEN 150 in simulation. Change the tier to BEN 500 in the Selector, press Apply, inject a cooling-unit failure under Sweeps, watch the standby unit start and the alarm clear, then open the Proposal panel and generate a proposal for that configuration.

More commands:

```bash
PYTHONPATH=software python -m ben_engine.config --tier ben150 --profile healthcare --climate hot_humid
PYTHONPATH=software python -m ben_engine.config --tier ben2000
PYTHONPATH=software python -m ben_engine.config --tier ben150 --hardening H3
PYTHONPATH=software python -m ben_engine.sweeps --tier ben500
PYTHONPATH=software python -m ben_engine.commissioning --sim --tier ben150 --yes --out /tmp/report.md
PYTHONPATH=software python -m ben_engine.cfd --tier ben150 --png /tmp/cfd.png
PYTHONPATH=software python -m ben_engine.proposal --tier ben150 --profile healthcare --option managed --customer "Acme Clinic" --site "Austin, TX" --out /tmp/p.md --html /tmp/p.html
PYTHONPATH=software python -m ben_engine.package --tier ben150 --profile healthcare --option managed --customer "Acme Clinic" --site "Austin, TX"
PYTHONPATH=software python -m ben_engine.bom --all
cd firmware/ben-pod && make test
```

## The product family

| Tier | Enclosure | IT load | Cooling (preset) | Power |
| --- | --- | --- | --- | --- |
| BEN 5 | NEMA 4X / IP66 24U outdoor cabinet on a skid | 2–5 kW | 2 × 5.8 kW cabinet DX (N+1) | 208/240 V 1φ |
| BEN 30 | 10 ft high-cube ISO-frame module, IP66 | 10–30 kW | 300 mm in-row DX, R-513A | 208 V 3φ |
| BEN 150 | 20 ft high-cube module, IP66 | 50–150 kW | Rear-door heat exchangers + dry cooler | 480 V 3φ |
| BEN 500 | 40 ft high-cube module, IP66 | 150–500 kW | Direct liquid cooling, CDU + dry cooler | 480 V 3φ |
| BEN 2000 | Prefabricated wide-body modular hall (3 joined 12.2 m modules) + power module + plant yard | 800–2,000 kW | Direct liquid cooling, N+1 CDU row, adiabatic dry coolers | 12.47 kV MV → 2 × 2,500 kVA (2N), 2N UPS, 3 × 1,250 kW generators |

Names are the nominal maximum IT kW (`docs/TIER_AND_ENCLOSURE_DECISION.md`); old keys `micro/ben10/ben20/ben40` still load. Every enclosure is NEMA 4X / IP66 (hardening **H1**); **H2** severe-environment and **H3** hardened/government packages are selectable (`--hardening H2|H3`).

Mission profiles: AI inference, AI training, private cloud, disaster recovery, industrial OT, healthcare, public sector, off-grid. Modules (power, cooling, compute, controls) can be bought separately; white-label and managed options exist.

## Architecture

```mermaid
flowchart LR
  SEL[Selector: web · dashboard · CLI] --> CFG[(Config)]
  CFG --> BOM[BOM + price confidence]
  CFG --> DRW[IFC drawings · renders · STE assembly · SQAM]
  CFG --> TWIN[Digital twin] --> SWP[Sweeps] --> COM[Commissioning report]
  CFG --> CFD[2-D LBM CFD] --> TWIN
  TWIN --> API[FastAPI + WS] --> DASH[Dashboard 3-D]
  CFG --> PROP[Proposal] --> PKG[Customer + partner deal packages]
  CFG --> COMP[Compliance pack · risk list]
```

Full architecture, trust boundaries and failure behaviour: `docs/ARCHITECTURE.md`. Protocol between BEN Pods, the PLC and the edge computer: `spec/PROTOCOL.md`.

## Deliverable map

- **Engineering:** `design/DESIGN_BASIS.md`, `design/drawings/<tier>/`, `design/drawings/INTERFERENCE_CHECKS.md`, `design/specs/` (BEN Pod and BEN Controller spec sheets, controls spec, one-line wiring SVGs), `design/assembly/` (STE instructions, QC forms, CTQ cards)
- **Quality for third parties:** `docs/SQAM.md`, `docs/MANUFACTURING_STRATEGY.md`, `docs/PROCESS_FLOW.md`
- **Operations:** `docs/COMPLIANCE.md`, `docs/RISK_REGISTER.md`, `docs/SITE_REQUIREMENTS.md`, `docs/TURNOVER.md`, `docs/MAINTENANCE.md`, `docs/BUILD_AND_WIRING.md`, `docs/TEST_GUIDE.md`, `docs/CYBERSECURITY.md`, `docs/ANALYSIS_AND_CALIBRATION.md`
- **Commercial:** `docs/proposals/` (samples), `docs/contracts/` (templates and `fields.json`), `purchasing/` (catalog, BOMs, RFQ queue, sourcing notes), `docs/investors/` (VC proposition, market sources, deck)
- **Marketing:** `web/index.html` (product page), `web/kit/` (brand guide, marketing kit, logo, wordmark)
- **Firmware:** `firmware/README.md`, `firmware/ben-pod/`, `firmware/ben-edge/`
- **Record:** `docs/BRIEF.md`, `docs/PROJECT_STATE.md`, `docs/PROJECT_NOTES.md`, `docs/TASKS.md`, `docs/VALIDATION.md`, `docs/ROADMAP.md`, `docs/FAQ.md`

## Tests and evidence

```bash
PYTHONPATH=software python -m pytest tests -q --ignore=tests/e2e   # python suite
bash tests/e2e/run_e2e.sh                                          # Playwright, ~13 min under software WebGL
cd firmware/ben-pod && make test                                   # 37 host unit tests
```

Observed results and screenshots: `docs/VALIDATION.md`, `docs/media/screens/`.

## Operations, checkpoints, recovery

See `docs/OPERATIONS.md`. Code and generated documents are in git; a deployed unit's telemetry database lives on its edge computer with a nightly backup (`firmware/ben-edge`). Licence of this repository is unresolved; the owner has not chosen one.

## Decks

- Product and engineering briefing: `docs/presentation/index.html` (speaker notes: `docs/presentation/speaker-notes.md`)
- Investor briefing: `docs/investors/deck/index.html` (speaker notes alongside)

---
Schreiber AI · Ben@SchreiberAI.com · Everything numeric on this page is generated by the code in this repository or cited in `docs/investors/MARKET_SOURCES.md`.
