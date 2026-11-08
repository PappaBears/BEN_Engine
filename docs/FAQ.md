# FAQ

**What is BEN Engine?** A family of all-in-one modular data centers named by IT power: power, cooling, compute and controls in one sealed enclosure, built in an off-the-shelf outdoor cabinet (BEN 5) and 10, 20 and 40 ft ISO-frame high-cube modules (BEN 30, BEN 150, BEN 500). That all-in-one box is the core product. The same system scales to a single 2 MW center (BEN 2000, a prefabricated modular hall), which we keep in the family as the capability example. All of it runs Schreiber AI's controls layer: a BEN Controller (PLC + industrial edge computer, or a Revolution Pi on the Lite tier), BEN Pods on the BEN Mesh, dashboard, digital twin, calibration, a commissioning script and the BEN Care digital care layer. One configuration model drives the drawings, bill of materials, compliance pack, assembly instructions, proposal and the twin.

**Why did the names change from BEN 10/20/40 to BEN 30/150/500?** The old number was the container length in feet; the new number is the nominal maximum IT kW, which is what a buyer sizes against. BEN Micro became BEN 5. The old keys (`micro`, `ben10`, `ben20`, `ben40`) still load through an alias map in `config.py` (D33 in `docs/PROJECT_NOTES.md`).

**What is BEN 2000?** The capability example at the top of the family, not the lead product: the single 2 MW center, not a container but a prefabricated, relocatable data hall of three factory-built wide-body steel modules (12.2 × 3.66 × 4.2 m each) joined on site into one sealed envelope, plus a separate power module and a plant yard. 800–2,000 kW IT in up to 48 liquid-cooled racks; 12.47 kV medium-voltage service to two 2,500 kVA pad-mount transformers (2N), 2N UPS strings with NFPA 855 battery rooms, three 1,250 kW generators (N+1) with 48 h fuel, adiabatic dry coolers. It is a building to the AHJ (IBC Group B or F-1) and the utility service is the critical path: about 52 weeks from order to in service (`docs/PROCESS_FLOW.md` §5). `python -m ben_engine.config --tier ben2000` prints the sizing.

**Is it weatherproof? What are H1, H2 and H3?** Every tier is element-proof by default: NEMA 4X / IP66 envelope, hose-tested per UL 50E type 4X (test E14), corrosion class C3. **H2 Severe environment** adds a 600 mm flood plinth, C5-M marine coating, sand/dust filtration, 67 m/s wind hardware and anodes for coastal, desert, arctic and hurricane sites. **H3 Hardened / government** adds UL 752 ballistic panels, ASTM F3038 forced-entry doors, IK10, a mantrap, two-factor access, tamper detection and an optional HEMP shield (MIL-STD-188-125-1) with TEMPEST-ready separation. The old rain-only 3R rating is no longer used anywhere. The configurator has a Hardening select; the config recommends H2 for severe climates and offers H3 for public-sector profiles.

**Can I try it without hardware?** Yes. `bash scripts/run_dashboard.sh` starts the dashboard in simulation mode with the twin, virtual Pods for I/O tests, sweeps, CFD, calibration and CSV export; hover any rack, cooling unit or Pod in the 3-D scene for its BOM part and live values. Everything shown is labelled simulation.

**What runs on a real unit?** The same `ben_engine.api` on an industrial edge computer (OnLogic Karbon 400 with TPM 2.0; on BEN Controls Lite, a Revolution Pi RevPi Connect 4) reading BEN Pods over MQTT on a Thread/IPv6 mesh, a Phoenix Contact PLCnext PLC over Modbus TCP/OPC UA for the interlocks, and third-party equipment over Modbus/SNMP. The edge image is in `firmware/ben-edge` and is marked implemented, unverified on hardware. Two controls tiers, Lite and Pro, are described in `docs/CONTROLS_HARDWARE_DECISION.md` §2a.

**What is a BEN Pod and why a mesh?** Our own sensor board: a Silicon Labs MGM240P Thread module with Secure Vault High (hardware root of trust), four Pt1000 inputs, humidity, pressure, contacts and a leak-rope input, in a rack-rail enclosure. Two Pods per rack plus a room and an outdoor Pod; no sensor cabling to pull, the mesh heals itself, every Pod attests with its own certificate, and the same Pod serves a BEN 5 cabinet, a dry cooler on the roof and a generator on the pad.

**What is BEN Care?** The digital care layer on top: minutes-to-limit alarms from a twin fitted to the unit's own data, proof of redundancy every month, drift-triggered calibration, a live risk scorecard, fleet learning and the same signed commissioning script from factory to lifetime (`docs/BEN_CARE.md`).

**Which parts of the firmware are tested?** The platform-independent core (calibration, telemetry JSON, commands, ring buffer, failsafe, alarms) has 37 host unit tests that pass. The EFR32MG24 / Gecko SDK hardware layer and the OpenThread integration compile only on the target and have not been built here (toolchain not available in this environment); the Secure Vault attestation flow has not run on hardware.

**How accurate is the digital twin?** It is a lumped-parameter model with design-value thermal masses. Steady-state temperatures and the direction of every fault response are physically reasonable; the ride-through minutes are a lower bound until measured on hardware. `analysis.py` fits the parameters from a commissioning load step and reports which are well determined.

**Is the CFD real?** It is a real 2-D thermal lattice-Boltzmann solver, run per tier, useful for ranking layouts and scenario deltas (fan turn-down, failed unit, door open). It is not a 3-D absolute-temperature prediction and says so.

**Where do prices come from?** `purchasing/parts_catalog.json`, 204 parts (12 of them withdrawn or factory-tooling lines), each with vendor, URL, price and a status: confirmed (seen on a distributor listing on 2026-11-07/08), list, or estimate (with basis). Totals per tier are in `docs/BOM.md` (BEN 5 $132k, BEN 30 $666k, BEN 150 $1.89 M, BEN 500 $4.45 M, BEN 2000 $40.4 M, reference compute included). The BOM and the proposal show the share of each. Nothing is a quote until the queued RFQ emails are answered.

**Were any emails sent?** No. 21 RFQs were created as Gmail drafts addressed to Ben@SchreiberAI.com and as files in `purchasing/email_queue/`. Ben forwards them.

**Why rear-door heat exchangers on BEN 150 instead of in-row DX?** The drawing generator's interference check showed five racks plus 600 mm in-row units do not fit a 20 ft row at 96 kW. The configuration model now rejects rows that do not fit and the preset falls back through 300 mm in-row, rear-door, then liquid.

**Why not R-410A or R-454B?** The AIM Act 700-GWP limit for new IT-room cooling applies from 2027-01-01, and A2L refrigerant charge limits inside a 32 m³ container are below what a 20–30 kW DX unit holds. In-row DX is specified with R-513A or R-515B (A1, GWP under 700).

**What about lithium batteries?** UL 9540 listed cabinets; BEN 5/30/150 presets stay under the 20 kWh NFPA 855 threshold by default; BEN 500 carries the full NFPA 855 package; BEN 2000 has dedicated battery rooms with 2-hour separation, gas detection and deflagration venting.

**Can a customer run the commissioning themselves?** Yes. `python -m ben_engine.commissioning --sim` rehearses it; `--live --url` targets a unit's edge computer. The report carries the SHA-256 of the exported data and a signature block.

**Who builds the units?** Third-party contract manufacturers to Schreiber AI's drawings and Simplified Technical English instructions, with hold points, QC forms and our witness at FAT. BEN 2000 modules come from prefabricated modular-building / modular data center manufacturers (named candidates in `docs/MANUFACTURING_STRATEGY.md` §3.2). A greenfield factory is a later study.

**What paperwork exists?** Customer side: MSA, SOW, change order, acceptance certificates, software licence, SLA, warranty, NDA. Partner side: integrator agreement, contract manufacturing agreement, supplier PO terms with delay liquidated damages. All in `docs/contracts/`, all templates for counsel review, all fillable from the proposal generator.

**Does it work offline?** The dashboard vendors three.js locally and needs no internet. The edge computer has no WAN route by default; remote support is an outbound-only tunnel the customer switches on.

**Who owns the data?** The customer. The edge computer's SQLite database is the system of record; export is one click.

**What is least accurate?** This is the short form of `docs/VALIDATION.md` §7, which is the complete list. In order: thermal ride-through minutes and recovery times, envelope UA, CFD absolute temperatures, calibration placement corrections (literature values), estimate-status prices (CDU, RDHx, dry coolers, generators, site civil), and every hardware-layer behaviour until a lighthouse unit exists.

**What is the licence of this repository?** Unresolved; the owner has not chosen one. Do not assume open-source terms.
