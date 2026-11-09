# BEN Engine — Investment proposition

**BEN Engine, by Schreiber AI · Rev 2 · prepared 2026-11-07, updated for Rev 2 on 2026-11-09 · contact Ben@SchreiberAI.com**
*The Rev 1 edition of this document is kept unchanged in `archive/rev1/docs/investors/VC_PROPOSITION.md`.*
*This document is generated alongside a working build. Every technical number in it is produced by the code in this repository; every market number is cited in `MARKET_SOURCES.md`; every price carries a confidence label from the bill of materials.*

## 1. The one-paragraph case

Small and mid-size businesses are adopting AI faster than their infrastructure can follow. Their choices today are a cloud bill that scales with success, a colocation contract priced for hyperscalers (about USD 196 per kW-month wholesale in 2025), or a server closet nobody commissioned. BEN Engine is a family of all-in-one modular data centers named by IT power: power, cooling, compute and controls in one sealed enclosure, from a 0.6–1.5 kW indoor mini rack for a tiny business (BEN 1, new in Rev 2) and a 5 kW outdoor cabinet (BEN 5) through liquid-first 20 ft and 40 ft modules at 300 kW and 1 MW (BEN 300 and BEN 1000, new in Rev 2), built from off-the-shelf enclosures and listed equipment, element-proof (NEMA 4X / IP66) by default and hardened on request, and sold with a controls layer that makes the box observable, testable and brandable. The same system scales to a single 2 MW prefabricated center (BEN 2000), which we hold as demonstrated capability and an upsell path rather than the near-term go-to-market. Schreiber AI's edge is not the steel: it is the **configuration-driven engineering system** that turns a mission profile into drawings, bill of materials, compliance pack, assembly instructions, digital twin and commissioning report, in the same afternoon, with the same numbers. That system is working software in this repository, not a roadmap item.

### Rev 2 (2026-11-09)

Rev 2 is a once-over of a base that works. In the operator's words: "the base is good, we just need a once-over … especially the liquid cooling, and I want to make sure we are as dense as we can be … along with the very low side for tiny business, where we do mini racks." Three things changed. **The brand:** the Schreiber AI brand package v2 is applied to every module, document and screen, with a data plate band on the hardware that carries the tier, serial, rating and revision. **The ends of the lineup:** BEN 1 mini racks at the low end, built in-house and plugged into a wall outlet, and BEN 300 and BEN 1000 at the dense end, liquid-first by default (W45 warm-water direct liquid, row CDUs N+1). **The budget:** a USD 5 M revamp program funds the lighthouse hardware, the liquid test cell, the listings and the brand production that a repository cannot produce. Rev 1 is frozen and every Rev 1 quote reproduces exactly; what changed is listed in `docs/rev2/RELEASE_NOTES.md`.

## 2. Problem

1. **Cloud economics invert for steady AI workloads.** Inference that runs all day on owned GPUs is cheaper than renting them after roughly one to two years; most SMBs cannot capture that because they cannot operate a facility.
2. **Traditional builds are priced for megawatts.** USD 10–13 M per MW and 18–30 months. Nobody builds a 100 kW facility that way.
3. **Modular vendors sell to hyperscalers and telcos.** Their minimum viable deal, engineering cycle and support model do not fit a 40-person manufacturer or a regional clinic.
4. **Data sovereignty and latency.** Healthcare, public sector, industrial OT and anyone with a customer-data promise want the model where the data is.

## 3. Product

**Focus and sequencing.** The core product is the all-in-one box, BEN 1 through BEN 1000 in Rev 2 (BEN 5 through BEN 500 in Rev 1): one enclosure, one delivery, one commissioning script. These are what the lighthouse units, the integrator channel and the first three years of sales are built on. BEN 2000 stays in the family as the capability example and upsell path: fully sized, drawn, priced and documented from the same model, offered when a regional customer outgrows a BEN 500, and not part of the near-term go-to-market.

| Tier | Enclosure | IT load | Who buys it |
| --- | --- | --- | --- |
| **BEN 1** (new, Rev 2) | Indoor mini rack: 10-inch 8U desk or shelf rack (rack10, ≤ 0.6 kW) or 19-inch 12U sound-damped office cabinet (cab12, ≤ 1.5 kW); 120 V plug-in, office air | 0.2–1.5 kW | Tiny businesses that want private AI: one or two desktop-class AI boxes, a NAS and a firewall in a closet or on a shelf |
| BEN 5 | NEMA 4X / IP66 outdoor 24U cabinet | 2–5 kW | Clinics, retailers, farms, branch offices, "AI for everyone" |
| BEN 30 | 10 ft high-cube ISO-frame module, IP66 | 10–30 kW | SMB private cloud + inference |
| BEN 150 | 20 ft high-cube module, IP66 | 50–150 kW | Mid-market, industrial sites, regional AI |
| **BEN 300** (new, Rev 2, dense) | 20 ft high-cube module, liquid-first (W45 direct liquid, row CDUs N+1, ≤ 10 % air) | 150–300 kW | One or two current liquid AI racks (GB300 NVL72-class, 132–155 kW) at a regional site or a factory |
| BEN 500 | 40 ft high-cube module, direct liquid cooling | 150–500 kW | Training pods, white-label partners, public sector (Rev 1 configuration, kept for existing quotes) |
| **BEN 1000** (new, Rev 2, flagship dense) | 40 ft high-cube module, liquid-first, all-in-one: power, UPS and battery, CDUs and controls in one sealed box; heat rejection on an adjacent skid; heat-reuse port | 500–1,000 kW | Up to six or seven current liquid racks for an AI training or inference pod without building a hall |
| BEN 2000 | Prefabricated modular hall (3 joined wide-body modules) + power module + plant yard; MV service, 2N power, N+1 generators | 800–2,000 kW | Regional enterprises, hospital systems, universities, municipalities, colocation-edge operators, defence |

**BEN 2000 (capability example, later): who buys a single 2 MW center.** Below the hyperscale campus and above the container there is a buyer nobody serves well: the regional enterprise consolidating its server rooms, the hospital system that must keep imaging and records on campus, the university research cluster, the municipality or utility building a resilient operations center, the colocation-edge operator planting a 2 MW node in a secondary market, and defence or public-sector programmes that need a hardened, relocatable facility. Their alternative is a traditional build at USD 10–13 M per MW over 18–30 months, with a design team hired per project. BEN 2000 is the same configuration-driven system scaled to a hall: three factory-finished modules, a power module and a plant yard, about 52 weeks from order to in service with the utility on the critical path, and the same twin, commissioning script and BEN Care on top. The BOM-based price per MW comes from `docs/BOM-ben2000.md` (**BEN 2000 BOM-based sell price about $35,000 per kW IT all-in and about $10,200 per kW for the infrastructure without compute, against $10,000–13,000 per kW ($10–13 M per MW) for a traditional 1–5 MW build (`docs/BOM-ben2000.md`, `scripts/unit_economics.py`)**).

**Density, Rev 2.** The dense tiers exist because the buyers we talk to ask first how much IT fits per box. BEN 300 and BEN 1000 are sized from the configuration model against real footprints: they must pass the same interference checks as every other tier (single row, 900 mm egress, NEC 110.26 working space at 480 V), or they are renamed to the power that fits. Design values per tier (kW per rack, kW per m² of footprint, kW per m³, kW per tonne) are in `docs/DENSITY.md`; they are design values until the BEN 300 lighthouse measures them. Positioning against what competitors publish (`docs/research/STATE_OF_THE_ART_2026.md` §3, vendor statements with their dates): Delta's 20 ft containerized AI data center is up to 60 kW per rack on AC; ZTE's prefabricated container is 40 kW per liquid rack; Huawei's reference design is 50 kW per rack in 16-rack modules; HPE's AI Mod POD reaches up to 1.5 MW in 6 m and 12 m containers on AC; Vertiv's MegaMod HDX compact is 13 racks and 1.25 MW. Every DC-ready modular offer found (Delta's 800 VDC modular data center, Flex Axiom, Eaton–Flexnode) is MW-class, every sub-MW container found is AC, and none publishes leak-to-isolation or proof-of-redundancy figures. BEN 300 and BEN 1000 compete on density in a sealed, relocatable, all-in-one box with open, local-first controls and published commissioning numbers; we do not claim to beat a purpose-built hall on kW per m².

**Hardening as a margin lever.** Every tier is NEMA 4X / IP66 (H1) at the base price. **H2 Severe environment** (flood plinth, C5-M coating, dust filtration, hurricane hardware) and **H3 Hardened / government** (UL 752 ballistic panels, ASTM F3038 doors, mantrap, HEMP shielding option, CMMC controls pack) are priced from catalog lines with `applies_to_hardening` and sold to buyers whose alternative is a bespoke engineering project; they carry hardware margin above the 28 % base because the value is the certified, tested envelope and the compliance pack, not the steel. H2 is recommended automatically for coastal, desert, arctic and high-altitude climates, which is a large share of the sites that cannot use a conventional building.

Four ways to buy: **hardware only**, **hardware + BEN Controls**, **white-label** (partner's brand on the box and dashboard), **managed** (Schreiber AI watches and maintains). Modules (power, cooling, compute, controls) can be bought separately.

## 4. Why we win: the engineering system

| Capability | What it does | Status in this repo |
| --- | --- | --- |
| Configuration model | One schema sizes power, cooling, structure, mass, PUE | `software/ben_engine/config.py` — verified for all tiers |
| Generated drawings | Issue-for-construction set with CTQ/CTP tables per tier | `design/drawings/` |
| Generated BOM with price confidence | Real parts, confirmed/list/estimate split | `purchasing/`, `docs/BOM.md` |
| Digital twin | Thermal + power model with faults; fits itself from commissioning data | `software/ben_engine/twin.py`, `analysis.py` |
| CFD | 2-D lattice-Boltzmann airflow for layout and recirculation | `software/ben_engine/cfd.py` |
| Commissioning script | FAT/SAT with signed report; customer or Schreiber AI can run it | `software/ben_engine/commissioning.py` |
| Dashboard | 3-D twin, walkthrough, sweeps, I/O test, CSV, calibration | `dashboard/` |
| Controls platform | **BEN Controls Pro**: Phoenix Contact PLCnext PLC + Axioline I/O in a UL 508A panel, OnLogic industrial edge computer with TPM; **BEN Controls Lite**: Revolution Pi for the BEN 5; both with **BEN Pods on BEN Mesh** (our own Thread/IPv6 sensor Pod on Silicon Labs MGM240P with Secure Vault High), MQTT/Modbus, signed firmware, attestation | `docs/CONTROLS_HARDWARE_DECISION.md`, `firmware/`, `purchasing/` |
| STE assembly instructions | Workers with minimal experience build it; licensed trades at hold points | `design/assembly/` |
| Compliance pack per profile | NEC, NFPA, UL 9540, ASHRAE, A2L refrigerant limits, IEC 62443, HIPAA, CMMC | `docs/COMPLIANCE.md` |

A competitor can buy the same container and the same UPS. They cannot buy the system that makes every unit identical, documented and testable, and that is what lets a small company ship many units with few engineers.

### BEN Care and BEN Mesh: what nobody else does

Most data center monitoring tells you a temperature. **BEN Care** tells you how long you have, how sure we are, and proves the box still works every month: every alarm carries minutes-to-limit with a confidence interval from a physics twin fitted to that unit's own commissioning data; failover and ride-through sweeps run automatically at low load, are hash-signed and feed the warranty and the SLA; calibration is requested when uncertainty grows, not by calendar; the risk register the customer saw before the price becomes a live scorecard with the evidence behind each line; fitted parameters from every unit improve the priors for the next. Underneath it, **BEN Mesh** removes the most error-prone part of a controls install, 80-plus shielded sensor runs, with our own **BEN Pod**: a Thread/IPv6 sensor node on Silicon Labs' MGM240P with a hardware root of trust (Secure Vault High, PSA Level 3), a per-device certificate injected in our factory cell, signed firmware and attestation at every join, on a self-healing mesh that moves with the container and serves the BEN 5 cabinet, the dry cooler and the generator with the same part. The control layer stays conservative and listed (PLCnext in a UL 508A panel, hardwired life safety); the part we build is the part a plant director, an insurer and an AHJ cannot buy from anyone else. Costed in the BOM at about +0.3 to +0.9 % of a unit; the same commissioning script is the FAT, the SAT, the monthly check and the warranty baseline.

## 5. Market

Ranges, not point estimates (sources in `MARKET_SOURCES.md`):
- Modular data centers: USD 36–39 B in 2025 growing to USD 63–85 B by 2030 (10–19 % CAGR). A conservative house puts 2030 at USD 37 B.
- Edge data centers: USD 13–16 B in 2025 by most firms; US alone about USD 5.7 B.
- SMB AI adoption: between 28 % and 65 % of US small businesses report using or piloting AI in 2025 depending on survey; 68 % among 10–100 employee firms in one survey.

**The low end (BEN 1): tiny businesses that want private AI.** The buyer is the owner of a studio, a trades business, a clinic front office or a ten-person firm who wants AI on their own data without a cloud bill or an IT department. Desktop- and deskside-class AI systems now make that possible on a shelf (for example, Dell's and NVIDIA's 21 Oct 2026 announcement is framed "from the deskside to data center", cited in `docs/research/STATE_OF_THE_ART_2026.md` §3); what the owner lacks is the setup, the power and heat check, the backup discipline and someone watching it. BEN 1 sells exactly that. Sourced numbers: US small-business AI adoption is reported between 28 % and 65 % in 2025 depending on the survey, 68 % among firms of 10–100 employees in one survey (`MARKET_SOURCES.md`). **No statistic for on-premises or private AI deployment by tiny businesses was found; we do not claim a market size for BEN 1.** The ten BEN 1 lighthouse units in the revamp program are the first evidence of demand, price and support load.

Our serviceable segment is the owner-operated all-in-one deployment from under 1 kW to 1 MW: tiny businesses (BEN 1), SMBs, regional healthcare, industrial sites, municipalities, AI pods for mid-market buyers (BEN 300, BEN 1000), and integrators who want a white-label platform. The **mid-market / regional 2 MW segment** (BEN 2000: enterprises, hospital systems, universities, municipalities, colocation-edge operators and defence buyers whose only alternative is a traditional build at USD 10–13 M per MW and 18–30 months) is a later phase that the same system already demonstrates; it is not in the near-term plan. We do not compete for hyperscale campuses.

## 6. Business model and unit economics

**Rev 2 tiers (BEN 1, BEN 300, BEN 1000):** unit economics from the Rev 2 BOMs are in `docs/rev2/UNIT_ECONOMICS.md`; the table below is the Rev 1 lineup, carried unchanged into Rev 2.

Unit economics are derived from the bill of materials in `docs/BOM.md`. The table below is regenerated by `scripts/unit_economics.py` and shows the price-confidence split so an investor can audit the margin.

<!-- UNIT_ECONOMICS_TABLE -->
| Tier (preset) | IT kW | BOM cost (all modules) | Sell price (28 % GM) | Infrastructure-only sell price (no compute) | Gross profit | Confirmed / list / estimate share of cost | Controls licence /yr | Managed service /yr | Price per kW IT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BEN 5 | 5 | $132,082 | $183,447 | $131,645 | $51,365 | 46 % / 0 % / 53 % | $1,200 | $2,700 | $36,689 |
| BEN 30 | 30 | $666,059 | $925,082 | $287,365 | $259,023 | 79 % / 0 % / 21 % | $4,800 | $16,200 | $30,836 |
| BEN 150 | 96 | $1,889,829 | $2,624,763 | $637,617 | $734,934 | 78 % / 0 % / 22 % | $12,000 | $51,840 | $27,341 |
| BEN 500 | 192 | $4,935,406 | $6,854,731 | $1,302,432 | $1,919,325 | 84 % / 0 % / 16 % | $30,000 | $103,680 | $35,702 |
| BEN 2000 | 1600 | $44,502,455 | $61,808,966 | $16,388,936 | $17,306,510 | 75 % / 0 % / 25 % | $90,000 | $864,000 | $38,631 |

Assumptions: hardware gross margin 28%; managed service $45/kW-month; controls licence per tier as shown. BOM cost excludes site civil and utility service (SITE- lines are shown separately in `docs/BOM.md`). Compute is the reference GPU/CPU node set from the catalog and dominates the all-modules price (one 8-GPU server is ~$82–236 k); most SMB customers will size their own compute or start with the infrastructure-only price and grow.

Revenue lines:
1. **Unit sales** (hardware + build + commissioning), target gross margin 25–35 % on hardware, higher on the controls module.
2. **BEN Controls licence** per unit per year (white-label partners) or included in managed service.
3. **Managed service** per kW-month: remote monitoring, maintenance scheduling, calibration, compliance records. Priced below colocation retail rates because the customer owns the asset.
4. **Engineering services**: site survey, permits support, AHJ submissions.

## 6b. Asset-light manufacturing

Units are built by qualified third-party contract manufacturers (container modification shops, modular electrical skid builders, UL 508A panel shops) to Schreiber AI's issue-for-construction drawings, Simplified Technical English instructions and QC forms, with Schreiber AI supplying the controls kit, witnessing hold points and running the factory acceptance test. Integrators sell and install under their brand or ours. Schreiber AI keeps the design authority, the controls layer, commissioning and operations. Capital goes into engineering, certification and controls hardware, not into a building. A greenfield factory is a later phase with explicit transition criteria (`docs/MANUFACTURING_STRATEGY.md`). Delivery risk is managed contractually: supplier and contract-manufacturer delay liquidated damages flow back-to-back with customer commitments, and customer scope changes re-baseline price and schedule (`docs/contracts/`).

## 7. Go-to-market

1. **Lighthouse units.** Rev 2: ten BEN 1 mini racks with pilot customers (built in-house) and one BEN 300 built at a contract manufacturer with FAT, SAT and a 30-day burn-in; every one produces the commissioning data that proves the twin. (Rev 1 planned a BEN 5 and a BEN 150; those stay the first outdoor-cabinet and air-module builds when a customer orders them.)
2. **Integrators and MEP firms** as white-label channel: they bring sites and licensed trades, we bring the system.
3. **Profile-led marketing**: the product page leads with mission profiles and risks, which qualifies buyers before a sales call.

## 7b. The Rev 2 revamp program (USD 5 M, 18 months)

The engineering, brand application and documentation revision is done in this repository now; that is Rev 2. The USD 5 M revamp buys what a repository cannot ([`docs/programs/REV2_REVAMP_PROGRAM.md`](../programs/REV2_REVAMP_PROGRAM.md)): the BEN 1 lighthouse (ten units built in-house for pilot customers), the BEN 300 lighthouse at a contract manufacturer with FAT, SAT and a 30-day burn-in, a liquid W45 test cell (with an 800 VDC cell only as a gated option), BEN Pod v1 production and FCC, UL 508A listing of the BEN Controller panels, brand production, the team, other listings and a contingency. Six quarterly gates release the money against measured evidence. The industry context is unchanged from Rev 1: GPU-vendor roadmaps move AI racks to 800 VDC distribution from 2027 and direct liquid cooling is mandatory above about 100 kW per rack; in November 2026 no 800 VDC distribution at 150–500 kW is listed, so Rev 2 leads with liquid and keeps DC as a study behind its gate. The earlier R&D Program 2027–2028 (USD 5 M core / 10 M full, 24 months) is superseded for budgeting and kept as workstream detail (`docs/programs/RD_PROGRAM_2027.md`).

## 8. What the money is for: the USD 5 M revamp

| Line | USD | What it delivers (measured) |
| --- | --- | --- |
| BEN 300 lighthouse at a contract manufacturer (infrastructure, CM labour, liquid load banks, FAT, transport, SAT, 30-day burn-in energy) | 1,450,000 | FAT and SAT passed; 30 days at ≥ 80 % load with zero critical alarms; measured kW per m², PUE, CDU failover and leak-to-isolation |
| Team: 6 FTE for 18 months (thermal/fluids, power and controls, test and commissioning, BEN 1 technician, software, half-time compliance and sourcing) | 1,350,000 | Staffed plan; every gate report signed by the named engineer |
| Liquid W45 test cell | 400,000 | W45 loop with measured ΔT and flow; leak-to-isolation ≤ 15 s; pump failover; heat balance within 5 % |
| 800 VDC test cell (gated option; returns to contingency if its gate is not met) | 350,000 | DC ground-fault injection on both poles; efficiency measured against the AC baseline |
| BEN 1 lighthouse: ten units built in-house, bench and test equipment, field setup | 300,000 | Ten units in service for 90 days; noise, heat to room, UPS runtime and uptime per unit |
| BEN Pod v1 production and FCC Part 15 | 250,000 | FCC SDoC; production yield report; firmware on target |
| Other listings and compliance (field evaluation, arc-flash study, PE stamps, AHJ pre-submissions, insurer review) | 230,000 | Field-evaluation label on the BEN 300 lighthouse; PE-signed arc-flash study |
| Brand production (data plates, nameplates, livery vinyl, print, the brand package's eight touchpoints) | 150,000 | Data plates on every program unit; touchpoints printed and tracked |
| UL 508A listing of the BEN Controller panels (Pro and Lite) | 120,000 | Listing mark on both panel types |
| Contingency (8 %) | 400,000 | Released at a gate against a written variance |
| **Total** | **5,000,000** | |

The basis of each line and the gate that releases it are in the program document. What the money does not buy: a BEN 1000 or BEN 2000 build (both engineered and quotable; the first BEN 1000 is customer-funded after the BEN 300 burn-in), a factory, immersion hardware, or any product-page number before it is measured. The ask and terms are set with the lead investor; this document fixes the shape and the ceiling of the plan so they can be audited against the build. The Rev 1 use-of-funds table is kept in `archive/rev1/docs/investors/VC_PROPOSITION.md`.

## 9. Risks we tell investors (same list we tell customers)

See `docs/RISK_REGISTER.md`. The three that matter most for the investment case: (1) **regulatory variance** across jurisdictions (container as building, battery storage, A2L refrigerants) lengthens first sales cycles; (2) **supply chain** on UPS, cooling and GPUs, mitigated by the catalog of qualified alternates; (3) **the twin's accuracy is proven in simulation, not yet on hardware**, and the Rev 2 tiers (BEN 1, BEN 300, BEN 1000) are design values until the lighthouse units measure them. We say so on every page. The lighthouse builds exist to retire that risk. Rev 2 adds the tier-specific risks R41–R52 (for BEN 1 in plain words for a tiny business: heat in the closet, circuit overload, noise, theft, untested backups, UPS battery age).

## 10. What you can verify today

Clone the repository, run `pip install -r requirements.txt`, `PYTHONPATH=software pytest tests -q`, then `bash scripts/run_dashboard.sh` and open the dashboard. Everything in this document that is marked verified is reproducible from that command line. `docs/VALIDATION.md` lists what is not.
