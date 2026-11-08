# FAQ

**What is BEN Engine?** A family of modular data centers (BEN Micro, 10, 20, 40) built in off-the-shelf outdoor cabinets and ISO high-cube containers, with Schreiber AI's controls layer: gateway, sensor nodes, dashboard, digital twin, calibration and a commissioning script. One configuration model drives the drawings, bill of materials, compliance pack, assembly instructions, proposal and the twin.

**Can I try it without hardware?** Yes. `bash scripts/run_dashboard.sh` starts the dashboard in simulation mode with the twin, virtual nodes for I/O tests, sweeps, CFD, calibration and CSV export. Everything shown is labelled simulation.

**What runs on a real unit?** The same `ben_engine.api` on a Raspberry Pi 5 gateway, reading ESP32 nodes over MQTT and third-party equipment over Modbus/SNMP. The gateway package is in `firmware/ben-gateway` and is marked implemented, unverified on hardware.

**Which parts of the firmware are tested?** The platform-independent core (calibration, telemetry JSON, commands, ring buffer, failsafe, alarms) has 37 host unit tests that pass. The ESP32 hardware layer compiles only on the target and was not built here because the toolchain download was blocked.

**How accurate is the digital twin?** It is a lumped-parameter model with design-value thermal masses. Steady-state temperatures and the direction of every fault response are physically reasonable; the ride-through minutes are a lower bound until measured on hardware. `analysis.py` fits the parameters from a commissioning load step and reports which are well determined.

**Is the CFD real?** It is a real 2-D thermal lattice-Boltzmann solver, run per tier, useful for ranking layouts and scenario deltas (fan turn-down, failed unit, door open). It is not a 3-D absolute-temperature prediction and says so.

**Where do prices come from?** `purchasing/parts_catalog.json`, 113 parts, each with vendor, URL, price and a status: confirmed (seen on a distributor listing on 2026-11-07), list, or estimate (with basis). The BOM and the proposal show the share of each. Nothing is a quote until the queued RFQ emails are answered.

**Were any emails sent?** No. 15 RFQs were created as Gmail drafts addressed to Ben@SchreiberAI.com and as files in `purchasing/email_queue/`. Ben forwards them.

**Why rear-door heat exchangers on BEN 20 instead of in-row DX?** The drawing generator's interference check showed five racks plus 600 mm in-row units do not fit a 20 ft row at 96 kW. The configuration model now rejects rows that do not fit and the preset falls back through 300 mm in-row, rear-door, then liquid.

**Why not R-410A or R-454B?** The AIM Act 700-GWP limit for new IT-room cooling applies from 2027-01-01, and A2L refrigerant charge limits inside a 32 m³ container are below what a 20–30 kW DX unit holds. In-row DX is specified with R-513A or R-515B (A1, GWP under 700).

**What about lithium batteries?** UL 9540 listed cabinets; Micro/10/20 presets stay under the 20 kWh NFPA 855 threshold by default; BEN 40 carries the full NFPA 855 package.

**Can a customer run the commissioning themselves?** Yes. `python -m ben_engine.commissioning --sim` rehearses it; `--live --url` targets a gateway. The report carries the SHA-256 of the exported data and a signature block.

**Who builds the units?** Third-party contract manufacturers to Schreiber AI's drawings and Simplified Technical English instructions, with hold points, QC forms and our witness at FAT. See `docs/MANUFACTURING_STRATEGY.md`. A greenfield factory is a later study.

**What paperwork exists?** Customer side: MSA, SOW, change order, acceptance certificates, software licence, SLA, warranty, NDA. Partner side: integrator agreement, contract manufacturing agreement, supplier PO terms with delay liquidated damages. All in `docs/contracts/`, all templates for counsel review, all fillable from the proposal generator.

**Does it work offline?** The dashboard vendors three.js locally and needs no internet. The gateway has no WAN route by default; remote support is an outbound-only tunnel the customer switches on.

**Who owns the data?** The customer. The gateway's SQLite database is the system of record; export is one click.

**What is least accurate?** In order: thermal ride-through minutes and recovery times, envelope UA, CFD absolute temperatures, calibration placement corrections (literature values), estimate-status prices (CDU, RDHx, dry coolers, generators, site civil), and every hardware-layer behaviour until a lighthouse unit exists.

**What is the licence of this repository?** Unresolved; the owner has not chosen one. Do not assume open-source terms.
