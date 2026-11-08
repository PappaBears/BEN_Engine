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
