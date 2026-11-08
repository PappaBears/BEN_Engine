# PROJECT_NOTES — decisions and rationale

All decisions are reversible unless marked. The operator asked for no questions, so choices were made on risk and feasibility and recorded here.

| # | Decision | Why | Alternative considered |
| --- | --- | --- | --- |
| D1 | Product name **BEN Engine = Business Edge Node**; tiers BEN Micro / 10 / 20 / 40 | Matches repo name, reads as a product family, tier number = container length | "Schreiber Pod" |
| D2 | One configuration model (`config.py`) drives BOM, drawings, twin, dashboard, website | Prevents drift between deliverables; it *is* the "base model" the operator asked for | Separate spreadsheets per deliverable |
| D3 | Off-the-shelf enclosures only: one-trip ISO high-cube containers (10/20/40) and a NEMA 3R 24U outdoor cabinet for Micro | Lowest cost, known structure (ISO 1496), worldwide transport; cabinet gives SMBs a true micro deployable | Custom welded enclosure (more parts, certification burden) |
| D4 | Air cooling (in-row DX) up to ~30 kW/rack; rear-door HX + dry cooler mid; direct liquid (DLC+CDU) for BEN 40 / training pods | Density and PUE; DX is the only feasible option at Micro/10 scale | Chilled-water CRAH (needs chiller plant) |
| D5 | Controls: Raspberry Pi 5 gateway + ESP32-S3 (Olimex ESP32-POE-ISO) nodes, MQTT/JSON, Modbus/SNMP to third-party gear; life-safety hardwired and never on the bus | Cheap, PoE powered, isolated, open; same firmware for all tiers; keeps liability boundary clear | PLC (cost, closed), cloud IoT (lock-in) |
| D6 | Digital twin is a lumped RC thermal + power chain model; CFD is a 2-D lattice-Boltzmann used for *relative* placement and recirculation, not absolute | Runs in seconds on a laptop, fit-able from commissioning data; 3-D CFD would not be verifiable here | OpenFOAM (not installed, not verifiable in session) |
| D7 | Cooling on a mechanical UPS/ride-through path is a **profile option**, default off for N, on for N+1/2N | Twin shows a 100 kW room passes ASHRAE max within ~3–5 min of cooling loss; healthcare/public sector need it | Always on (cost) |
| D8 | Lithium (LFP) battery cabinets with UL 9540 listing required in BOM | Footprint and weight inside a container; VRLA too heavy for 40 ft payload with DLC | VRLA |
| D9 | Firmware compiled and unit-tested on host (`native`); ESP32 cross-build defined but not run here | Toolchain download blocked; HAL keeps the application code identical | Skip firmware (would violate brief) |
| D10 | Assembly instructions in ASD-STE100 | Operator opened the session with STE; it is the right tool for low-experience assemblers | Plain English |
| D11 | Purchasing emails are **drafts** (files in `purchasing/email_queue/` + Gmail drafts to Ben@SchreiberAI.com) | Outbound action needs the operator's send | Sending directly |
| D12 | Website is static HTML in `web/` using the same selector logic (ported to JS from `config.py`) | Deployable on any host, no backend needed for the product page; demo links to the dashboard | React build |
| D13 | Risks shown before pricing on the product page | Operator requirement; also reduces sales-cycle surprises | Risk page in footer |
| D14 | VC proposition built from BOM-derived unit economics with the confidence split (confirmed/list/estimate) shown | Honesty is the pitch; investors can audit the number | Top-down TAM only |

## Observations during build
- Twin smoke run: BEN 20 at 90 % load settles to 21.3–21.4 °C rack inlets; one in-row unit failure is covered by the N+1 unit within minutes; utility loss with no mechanical ride-through drives inlets to ~49 °C within 5 min. That is the physical basis for D7.
- BEN Micro at 6 kW IT needs two 5.8 kW cabinet AC units for N+1; that drives the cabinet choice (dual-AC-ready outdoor cabinet).

## Compliance decisions (from `docs/COMPLIANCE.md` §0, 2026-11-07)

| # | Decision | Why | Alternative considered |
| --- | --- | --- | --- |
| D15 | **BEN 10 / BEN 20 in-row DX use A1 (non-flammable) refrigerant with GWP < 700 (R-513A or R-515B); no A2L (R-454B/R-32) inside the ITE space.** Where a vendor offers only A2L, use RDHx/chilled-water so refrigerant stays outside | UL 60335-2-40 / ASHRAE 15 allowable A2L charge in a BEN 20 (12.7 m², 32 m³) is ≈ 1.2 kg unmitigated; a 30 kW in-row unit holds 8–15 kg. AIM Act 700-GWP limit for data-center cooling from 1 Jan 2027 rules out R-410A | A2L with listed leak detection + mitigation ventilation (cost, AHJ friction, extra failure modes) |
| D16 | **Lithium battery capped at 20 kWh total on BEN Micro/10/20 by default; BEN 40 (and any BEN 20 above 20 kWh) carries the NFPA 855 package** (UL 9540 listing, UL 9540A report, separated battery compartment, gas detection, explosion control). Generator is the preferred long ride-through, not more battery | NFPA 855 scope starts at 20 kWh lithium; the package adds cost and fire-marshal review | Unlimited battery with 855 package on every tier |
| D17 | **NEC Article 645 not invoked**; wire to Chapters 1–4; NFPA 75 items (EPO, HVAC shutdown on detection, VEWFD, clean agent) provided regardless | No raised floor, so 645's relaxations buy nothing; fewer AHJ questions | Invoke 645 |
| D18 | **Containers (10/20/40) are presented to AHJs as relocatable structures, Group U, not normally occupied**, with PE-stamped anchorage and a building permit; BEN Micro is equipment on a skid. Field evaluation (NFPA 790/791) budgeted as an option | Most AHJs treat a walk-in container as a structure; pre-empting the classification question shortens the permit | Argue "equipment enclosure, no permit" (fails often) |
| D19 | **Electrical vestibule 1.1 m deep at the door end of BEN 20/40**; second egress door on BEN 40 when service ≥ 1000 A | NEC 110.26 working space at 480 V (1.07 m) and 110.26(C)(3) egress ≥ 1200 A; also OSHA egress | Panels along the side wall (steals aisle width) |
| D20 | **Domestic shipments move as cargo on a flatbed with the CSC plate covered; re-certification by a classification society only for export/rail or relocation profiles** | Cutting openings voids the CSC approval; most units never travel as containers | Re-certify every unit |
| D21 | Uptime Tier certification is **not claimed**; design basis stated as TIA-942-C Rated-2 (N+1) / Rated-3 (2N) concepts | Honesty rule in brand.json; certification is a customer option | Claim "Tier III design" |
| D22 | **Third parties first for manufacturing**: qualified contract manufacturers / integrators build the units from Schreiber AI's package and consigned controls kit; Schreiber AI = design authority + controls + FAT/SAT + operations; greenfield factory is a later phase gated by `docs/MANUFACTURING_STRATEGY.md` §10 | Operator steering 2026-11-08: capital, speed, leverage of the CM's UL 508A file, welder certs and licences | Own factory first (US$ 6–12 M capex before unit 1) |

## Decisions added during integration (2026-11-08)
| # | Decision | Why |
| --- | --- | --- |
| D23 | `inrow_dx_300` (300 mm, 20 kW) added; BEN 10 default; BEN 20 default is rear-door heat exchangers + dry cooler; `validate()` rejects rows that do not fit; presets fall back in-row → in-row 300 → RDHx → DLC | Drawing interference checks: five racks plus 600 mm in-row units do not fit a 20 ft row at 96 kW |
| D24 | Container interior height 2.49 m; BEN Micro capped at 5 kW IT with two 5.8 kW cabinet AC units | Envelope build-up and cabinet face area |
| D25 | In-row DX specified with R-513A/R-515B (A1, GWP < 700) | A2L charge limits in a container; AIM Act 2027 |
| D26 | Battery energy under 20 kWh on Micro/10/20 by default (internal to the UPS frame); BEN 40 carries the NFPA 855 package | NFPA 855 / UL 9540 threshold |
| D27 | UPS presets: BEN 10 rack-mount 20 kVA modules; BEN 20/40 single Galaxy VS 150 kW frame with internal N+1 modules; 93PM and GVS100 kept as catalogued alternates | Row length interference check I-C21 |
| D28 | 48U rack is the 1070 mm deep model (AR3107) | Keeps the 900 mm aisle on BEN 40 (I-C22) |
| D29 | Third-party contract manufacturing first; greenfield factory a later study with transition criteria | Operator steer; capital and certification leverage |
| D30 | Proposal generator is the back end of the selector; paperwork templates share one `[FIELD]` vocabulary so the proposal pre-fills them; supplier/CM delay LDs flow back-to-back; customer scope changes re-baseline price and schedule | Operator steer: "full proposal level", "the package has to cover all of it" |
| D31 | 16 RFQ/RFI emails created as Gmail drafts to Ben@SchreiberAI.com; nothing sent | Outbound action is the operator's |

## Fixes made from looking at rendered output
- Product page: fieldset overflow at 390 px (min-width 0, min(280px, 100%) grid).
- Dashboard (by the dashboard agent): exterior framing, lighting/exposure, cutaway transparency, power-bay layout, hot-aisle pipe sizing, sensor sphere and particle size, Micro presets, status strip at 390 px, sweeps panel re-render.
- Drawings (by the drawings agent): leader overlaps on A-003, north arrow collision, leak-rope item painting over C-001, step numbering, Micro node placement, M-001 label collisions, sensor dimension stacking.
- Proposal: blank "proposed" marker column became a Status column.

## D32 — Controls hardware replaced with an industrial platform (2026-11-08)
Operator rejected the Raspberry Pi gateway. Decision: PLC (Phoenix Contact PLCnext AXC F 2152 + Axioline I/O, UL 508A panel) for control and interlocks; industrial edge computer (OnLogic Karbon 400, TPM 2.0, −40…70 °C) for the twin, dashboard and history; sensing by industrial transmitters on the PLC plus **BEN Pod** on **BEN Mesh** (Thread/IPv6 on Silicon Labs EFR32MG24 / MGM240P with Secure Vault High, our PCB, our PKI). ESP32 and Olimex removed. Rationale and the BEN Care differentiators in `docs/CONTROLS_HARDWARE_DECISION.md`.
