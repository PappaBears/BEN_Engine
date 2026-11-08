# Schreiber AI — BEN Engine proposal SAI-MICRO-20261108-C6D4D2A1

*BEN Micro · Private cloud / ERP · Riverside Dental Group · Boise, ID · 2026-11-08 · valid until 2027-01-07*

## 1. Cover

| Item | Value |
|---|---|
| Proposal | BEN Engine BEN Micro for Riverside Dental Group |
| Prepared by | Schreiber AI |
| Customer | Riverside Dental Group |
| Site | Boise, ID |
| Tier | BEN Micro — Outdoor 24U NEMA 3R cabinet on skid |
| Mission profile | Private cloud / ERP (private_cloud) |
| Climate package | Temperate |
| Purchase option | Hardware only |
| Date | 2026-11-08 |
| Valid until | 2027-01-07 (60 days) |
| Proposal ID | SAI-MICRO-20261108-C6D4D2A1 |
| Configuration | 5 kW IT in 1 rack(s), Cabinet DX air conditioner, N+1, 10 min UPS |

AI infrastructure that arrives finished. This proposal is generated from configuration version 13c7ed1f; every number in it comes from the same model that produces the drawings, bill of materials, digital twin and commissioning script.

## 2. Executive summary

Riverside Dental Group needs 5 kW of IT capacity for a Private cloud / ERP workload at Boise, ID. We propose one BEN Micro: a Outdoor 24U NEMA 3R cabinet on skid fitted out as a complete data center with 1 rack(s), Cabinet DX air conditioner with N+1 redundancy, a 2 x 6 kVA UPS giving 10 minutes of ride-through, clean-agent fire protection and the BEN Controls layer (sensors, firmware, digital twin, dashboard).

The unit arrives finished and factory-tested. It needs a pad, a 50 A 208/240 V 1ph feeder, fiber and a grounding electrode at the site; everything inside the enclosure is built, wired, tested and documented before it ships.

Price for the hardware only option: $183,483 capital ($36,697 per kW IT). 68 % of the underlying cost is at confirmed vendor prices, 0 % at manufacturer list price and 32 % is engineering estimate; the price is firm at engineering release, when the configuration is frozen.

Order to in-service: about 16 weeks, set by the longest-lead item (8 weeks) and the permit cycle. Risks are disclosed in section 10 before the price is accepted; the site requirements in section 11 are signed before anything is built for this site.

## 3. Mission profile and what it means

| Item | Value |
|---|---|
| Profile | Private cloud / ERP (private_cloud) |
| ASHRAE class | A2: 10–35 °C inlet allowable; standard enterprise IT |
| Redundancy | N+1: one spare cooling unit and one spare UPS module; any single unit can fail or be serviced with no loss of capacity |
| Design rack density | 5.0 kW per rack (profile default 10 kW) |
| Climate package | Temperate: design outdoor 35 °C / minimum -15 °C, solar 800 W/m², corrosion class ISO 9223 C3, basic wind 47 m/s (ASCE 7) |
| Cooling derate at design day | 1.000 -> 5.8 kW per unit; 2 units installed for 1 required |
| Generator | not included (option) |

What this means for you: the environmental class sets the alarm limits your IT will be held to; the redundancy level sets what happens when a component fails; the climate package sets the coatings, anchorage, condensation control and cooling capacity margins built into the unit. All three are fixed at engineering release and verified at the factory and site acceptance tests.

## 4. The unit: sizing

| Item | Value | Basis |
|---|---|---|
| Enclosure | Outdoor 24U NEMA 3R cabinet on skid | External 1.2 x 1.0 x 1.8 m; interior 1.0 x 0.8 x 1.4 m |
| IT load | 5 kW in 1 rack(s) of 24 U | 5.0 kW per rack; tier range 2–5 kW |
| Cooling | 2 x Cabinet DX air conditioner | 1 required at 5.8 kW each (derate 1.0), N+1 |
| Row fit | fits | single row 1900 mm vs interior 1000 mm |
| Cooling electrical | 1.92 kW | COP 2.6 at design point |
| Total electrical demand | 7.5 kW / 7.9 kVA | IT + cooling + 2 % house + 0.5 kW controls, pf 0.95 |
| Service | 208/240 V 1ph, 50 A breaker | calculated 41 A at 80 % continuous, rounded to the next frame |
| UPS | 2 x 6 kVA | IT only with 15 % headroom, N+1 |
| Battery | 0.9 kWh lithium (LFP) | 10 min at IT load, 90 % depth of discharge |
| NFPA 855 scope | no - battery below 20 kWh | energy storage threshold |
| Airflow | 625 cfm | 125 cfm/kW air-cooled at 12 K rise; 40 cfm/kW liquid/water |
| Envelope gain at design day | 0.11 kW | 100 mm PIR, R 3.5 m²K/W, solar on roof |
| Mass | payload 767 kg; gross 1,087 kg | tare 320 kg; crane and pad sized for the gross mass |
| PUE estimate | 1.535 | design-point calculation incl. 0.03 UPS loss; measured at SAT |

## 5. Scope of supply

| Module | Status | BOM lines | Sell price |
|---|---|---|---|
| Power module | included | 10 lines | $39,707 |
| Cooling module | included | 1 lines | $25,618 |
| Compute module | included | 3 lines | $51,803 |
| Controls module | not in this option | - | - |
| Structure (container / cabinet) | included | 3 lines | $20,435 |
| Envelope (insulation, liner, coatings) | included | 5 lines | $1,021 |
| Fire detection and suppression | included | 5 lines | $2,524 |
| Site kit (anchors, embeds, signage) | included | 8 lines | $19,014 |
| Build labour, FAT, logistics | included | 6 lines | $23,361 |

Top 15 lines of the 41-line bill of materials for this option (sell price at 28% gross margin; the full priced BOM with vendors, part numbers and price confirmation dates is delivered at engineering release):

| Code | Item | Manufacturer / MPN | Qty | Sell price | Price basis | Lead (wk) |
|---|---|---|---|---|---|---|
| CMP-CPU | PowerEdge R760 2U rack server (management / storage node) | Dell Technologies R760 | 2 ea | $49,997 | confirmed | 3 |
| PWR-UPS-SRT6K | Smart-UPS SRT 6 kVA RM 208 V online double-conversion | APC by Schneider Electric SRT6KRMXLT | 2 ea | $26,900 | confirmed | 2 |
| CLG-CABAC | Blue e+ wall-mounted enclosure cooling unit 5.8 kW, 400/480 V 3-ph | Rittal SK 3189.940 | 2 ea | $25,618 | confirmed | 8 |
| STR-CAB24U | Outdoor NEMA 4 24U cabinet, 12 in plinth, integral 2200 BTU AC (shell for BEN Micro) | Great Lakes Data Racks GL24-NEMA4-AC2200 | 1 ea | $18,351 | confirmed | 6 |
| SVC-ELECTRICIAN | Licensed electrician (commercial journeyman, billed) | local electrical contractor ELEC-HR | 53 h | $8,097 | estimate | 1 |
| PWR-UPS-SRT6K-XBP | Smart-UPS SRT 192 V external battery pack (for 10 min at 6 kW) | APC by Schneider Electric SRT192RMBP | 2 ea | $6,667 | estimate | 2 |
| SITE-FIBER | Fiber drop, handhole, 24-strand SM to demarc | local ISP / contractor FIBER-DROP | 1 lot | $6,250 | estimate | 8 |
| SVC-PE | PE-stamped site electrical one-line and structural anchorage letter | licensed PE PE-STAMP | 1 lot | $5,556 | estimate | 3 |
| SITE-PERMIT | Building/electrical/fire permits, plan review, inspections | AHJ PERMITS | 1 lot | $3,472 | estimate | 6 |
| SITE-ELEC | Utility service interconnect: meter base, trench, conduit, utility fees, per ampere | local electrical contractor / utility SVC-INTERCONNECT | 50 A | $3,125 | estimate | 6 |
| PWR-PDU | NetShelter metered rack PDU 0U 5.0 kW 208 V 30 A, L6-30P, (36) C13 (6) C19 | APC by Schneider Electric AP8841 | 2 ea | $3,111 | confirmed | 1 |
| SVC-HVAC | HVAC / refrigeration technician (EPA 608), billed | local mechanical contractor HVAC-HR | 17 h | $2,951 | estimate | 1 |
| SVC-COMMISSION | Schreiber AI commissioning & I/O test labour (internal) | Schreiber AI COMM-HR | 20 h | $2,639 | estimate | 1 |
| SITE-GROUND | Grounding electrode system: 3 rods, #2 Cu ring, exothermic welds, test | local electrical contractor GES-3ROD | 1 lot | $2,500 | estimate | 1 |
| SVC-FREIGHT-EQ | Inbound freight on racks, UPS, cooling, batteries (per pallet-equivalent) | LTL carriers LTL-PALLET | 5 pallet | $2,431 | estimate | 1 |

Explicitly excluded:

- Site civil works: pad, piers, anchors set in concrete, drainage, fencing, lighting, equipment yard (PE-stamped drawings are supplied by us)
- Utility service: feeder from the customer's switchgear to the disconnect at the unit, utility fees, metering, interconnection
- Permits and fees pulled by the customer (zoning, building, utility, generator air permit); we supply the engineering documents
- Fiber / ISP circuits, customer network equipment above the controls LAN, customer software licences
- Taxes, duties, freight insurance beyond the quoted domestic delivery, crane standby beyond one day
- Standby generator, ATS and fuel system (available as an option)

## 6. Price

| Option | Capital price | Per kW IT | Recurring / year | Term | Total over term | Confirmed / list / estimate | BOM lines | Status |
|---|---|---|---|---|---|---|---|---|
| Hardware only | $183,483 | $36,697 | - | 1 yr | $183,483 | 68 / 0 / 32 % | 41 | PROPOSED |
| Hardware + BEN Controls | $187,614 | $37,523 | $1,200 | 1 yr | $188,814 | 69 / 0 / 31 % | 64 | alternative |
| White-label | $187,614 | $37,523 | $1,500 | 1 yr | $189,114 | 69 / 0 / 31 % | 64 | alternative |
| Managed service | $187,614 | $37,523 | $2,700 | 3 yr | $195,714 | 69 / 0 / 31 % | 64 | alternative |

Confirmed = price seen on a vendor or distributor listing on the date in the BOM; list = manufacturer published price; estimate = engineering estimate with its basis stated in the BOM note. Capital prices carry a 28% gross margin on purchased hardware and build labour. Recurring items: Hardware + BEN Controls: BEN Controls licence (dashboard, twin, firmware updates, remote support hooks); White-label: White-label licence under the Schreiber AI brand (controls licence x 1.25, partner branding, source escrow); Managed service: Managed service at $45/kW-month x 5 kW IT (includes the BEN Controls licence, remote operations and the maintenance schedule).

| Managed service term | Capital | Service fees | Total |
|---|---|---|---|
| 1 year | $187,614 | $2,700 | $190,314 |
| 3 years | $187,614 | $8,100 | $195,714 |
| 5 years | $187,614 | $13,500 | $201,114 |

Payment milestones for the proposed option (Hardware only, capital $183,483):

| Milestone | Share | Amount | Week from order |
|---|---|---|---|
| Engineering release (H4) | 30 % | $55,045 | 2 |
| Factory acceptance test (H13) | 40 % | $73,393 | 12 |
| Site acceptance test (H19) | 25 % | $45,871 | 15 |
| Turnover (W20) | 5 % | $9,174 | 16 |

Recurring fees are invoiced annually in advance from turnover. Prices are in USD, exclude taxes, and are valid to the date on the cover; the capital price becomes firm at engineering release.

## 7. Schedule

Milestones in weeks from order, derived from the stage durations in docs/PROCESS_FLOW.md for the BEN Micro (reference order-to-service 10-12 weeks) and the longest lead time in this bill of materials (8 weeks). Critical path: engineering release -> long-lead procurement -> fit-out -> FAT -> SAT. Site civil and permits run in parallel.

| Week | Milestone | Owner | Hold / witness point | Path |
|---|---|---|---|---|
| 0 | Order and risk acknowledgement signed | Customer + Schreiber AI | - | critical |
| 1 | Site survey and site requirements sign-off | Customer + ENG | H3 | critical |
| 2 | Engineering release: configuration frozen, IFC drawings, BOM; long-lead purchase orders placed | ENG | H4 | critical |
| 4 | Container / cabinet received and inspected; structural and envelope work starts | FAC | W6, H7, W8 | critical |
| 6 | Permits issued (building, electrical, mechanical, fire plan review) | Customer / AHJ | - | parallel |
| 8 | Site pad, grounding and utility feeder complete and surveyed | Customer civil | H16 | parallel |
| 10 | Longest-lead item on the floor (8 weeks from release); mechanical and electrical fit-out complete | FAC + SUB | H10 | critical |
| 12 | Cooling, controls and firmware complete; factory acceptance test incl. 24 h burn-in | FAC + ENG; customer witness | H11, W12, H13 | critical |
| 13 | Transport prep and shipping | LOG | - | critical |
| 14 | Set-down, hook-up and pre-energisation check | LOG + SUB + AHJ | W17, H18 | critical |
| 15 | Site acceptance test and fire marshal acceptance | ENG + customer + AHJ | H19 | critical |
| 16 | Training and turnover; unit in service | ENG + customer | W20 | critical |

Long-lead items (ordered at engineering release):

| Code | Item | Vendor | Qty | Lead time (weeks) |
|---|---|---|---|---|
| CLG-CABAC | Blue e+ wall-mounted enclosure cooling unit 5.8 kW, 400/480 V 3-ph | DigiKey (UK listing) | 2 ea | 8 |
| SITE-FIBER | Fiber drop, handhole, 24-strand SM to demarc | local | 1 lot | 8 |
| STR-CAB24U | Outdoor NEMA 4 24U cabinet, 12 in plinth, integral 2200 BTU AC (shell for BEN Micro) | CDW | 1 ea | 6 |
| SITE-PERMIT | Building/electrical/fire permits, plan review, inspections | local | 1 lot | 6 |
| SITE-ELEC | Utility service interconnect: meter base, trench, conduit, utility fees, per ampere | local | 50 A | 6 |

## 8. Drawings and documents delivered

Issue-for-construction drawing set for the BEN Micro, regenerated from the frozen configuration at engineering release and re-issued as built after SAT. ISSUE FOR CONSTRUCTION Rev A — Drawn: BEN Engine generator; Checked: blank (requires a checker before release).

| Sheet | Title | Scale |
|---|---|---|
| A-001 | General arrangement (sheet 1/7) | see sheet |
| A-002 | Interior layout plan (sheet 2/7) | see sheet |
| A-003 | Envelope section (sheet 3/7) | 1:10 / 1:2 |
| S-001 | Floor framing and anchoring (sheet 4/7) | see sheet / 1:5 |
| E-001 | Power one-line (sheet 5/7) | NTS |
| M-001 | Cooling P&ID (sheet 6/7) | NTS |
| C-001 | Controls layout (sheet 7/7) | see sheet |

Document set (indexed binder, encrypted USB in the controls cabinet, and the gateway share, per docs/TURNOVER.md):

- At order: this proposal, risk acknowledgement, site requirements form (docs/SITE_REQUIREMENTS.md) for signature
- At engineering release (H4): frozen configuration JSON with derived sizing, IFC drawing set with CTQ/CTP callouts, priced bill of materials with confirmation status, arc-flash and coordination study, PE anchorage calculation, compliance pack, FAT/SAT procedure
- At FAT (H13): signed commissioning report (JSON + PDF) with sweep CSVs, thermography, door-fan test, electrical and cooling test records
- At SAT (H19): site commissioning report, acoustic survey, final arc-flash labels, AHJ certificates
- At turnover (W20): as-built drawings, as-built BOM with serials, O&M manual, maintenance schedule with the first 12 months pre-populated, calibration certificates per channel, firmware hashes, gateway backup, password handover record, training sign-off, warranty certificates

## 9. Compliance pack for this profile

Compliance is central to the design, not an appendix: docs/COMPLIANCE.md maps every applicable code to a design feature and a verification. The pack delivered with this unit is the subset for the profile and climate below.

| Item | Value |
|---|---|
| Profile | private_cloud (A2, N+1) |
| ASHRAE class / redundancy (from config) | A2 / N+1 |
| Emphasis | ERP / finance workloads |
| Standards emphasised | PCI DSS v4.0.1 Req. 9; SOC 2 mapping; ISO 27001 |
| Extra documents in the pack | Physical access control matrix; camera retention policy |
| Typical AHJ / third-party questions | Segmentation of controls LAN from CDE |

Climate add-ons:

| Item | Value |
|---|---|
| Climate | temperate |
| Config values | 35 °C / −15 °C, C3, 47 m/s |
| Compliance / design add-ons | Baseline package |
| Verification | — |

Baseline matrix lines that apply to every unit:

| Code / standard | Design feature | Verification |
|---|---|---|
| NFPA 70 (NEC) | Listed dead-front gear, SCCR 65 kA, selective coordination, arc-flash labels | Electrical inspection H10, AHJ at H18 |
| NFPA 75 / 2001 / 72 | Non-combustible liner, VEWFD, clean agent with 10-min hold, EPO, HVAC shutdown | Door-fan test, NFPA 72 record of completion at SAT |
| UL 508A | Controls panel built in a UL 508A shop | Panel label and schedule |
| ASHRAE TC 9.9 | Class A2 alarm limits in the controls | Load step test E3/E7 at FAT and SAT |
| AIM Act / EPA 608 | GWP < 700 A1 refrigerant or water loops; certified technicians | Charge record per circuit |
| ISO 668 / 1496 / CSC | One-trip high-cube container, PE-checked modifications, CSC decision at transport | Weld inspection H7, weigh ticket |

## 10. Risks disclosed up front

These are the risks that apply to the private cloud / erp profile, from the product risk register (docs/RISK_REGISTER.md, web/assets/risks.json). Each line says what the design covers and what remains the customer's decision or duty. Please read them before accepting the price.

| ID | Risk | Severity | What can happen | Covered by the design | Customer owns |
|---|---|---|---|---|---|
| R01 | Utility power loss | high | The grid fails for seconds to days. IT shuts down when the battery runs out and cooling stops at once unless it is on UPS or generator. | UPS ride-through (default 10 min), generator option with ATS, measured cooling ride-through (test E5), N+1/2N per profile. | Whether to buy the generator and fuel, the utility contract, and whether cooling is put on UPS. |
| R15 | Permit delay or unexpected AHJ requirement | high | The local authority may classify the container as a building, ask for a field evaluation or more fire protection, and take longer than the build. | Pre-application package, code summary, field-evaluation budget line, site requirements signed before build, parallel permit path in the schedule. | Pulling permits (or authorising us), zoning, neighbour relations. |
| R18 | Long-lead parts slip | high | UPS, switchgear, cooling units and transformers can take months and slip. | Long-lead orders at engineering release, approved alternates, stocked controls hardware. | Early deposit and configuration freeze; no late changes. |
| R02 | Arc flash or electrical fault | medium | A fault while a panel is open or a component failure can injure someone and damage equipment. | Arc-flash study and labels, selective coordination, listed dead-front gear, lockout points, NFPA 70E training at turnover. | Only qualified electricians work on it and the labels are followed. |
| R06 | Fire inside the container | medium | A cable, battery or power supply fire would mean loss of IT, an agent discharge and downtime. | Very-early smoke detection, clean agent with 10-minute hold, HVAC shutdown, EPO, non-combustible liner, battery separation. | Fire marshal relationship, agent recharge contract, no combustible storage inside, insurance. |
| R08 | Water or coolant leak | medium | Roof, door seals, condensate or a liquid-cooling loop can leak and damage IT. | Rope leak sensors, condensate float alarm, drip trays, CDU auto pump stop on leak, propylene glycol only, seal inspection schedule. | Keep drains clear, respond to alarms, pad drainage. |
| R11 | Intrusion into the controls network | medium | An attacker who reaches the controls LAN could change setpoints or stop cooling. | IEC 62443 zones, isolated controls LAN, signed firmware, no inbound ports, outbound-only remote support that can be disabled, hardwired life safety. | The firewall between BEN controls and the customer LAN (unless managed), password handover, patch windows. |
| R14 | Sensor drift gives false comfort | medium | A drifted sensor can make the dashboard look fine while the room is not. | Redundant sensors, idle cross-check (test E1), drift detection, 12-month or trigger-based recalibration. | Allow calibration visits, do not move sensors. |
| R17 | Noise complaints | medium | Dry coolers and condensers can exceed night-time limits at the property line. | Sound prediction at quote, low-noise fans and night setback, acoustic survey at SAT (test E10), barrier option. | Site selection, setbacks, local ordinance. |
| R20 | Site costs above quote | medium | Civil works, permits and utility connection can cost more than the allowance. | Firm box price after engineering release; site works quoted after survey; utility costs identified at survey. | Utility fees, civil works, permits, taxes, and changes after freeze. |
| R21 | Energy cost higher than expected | medium | Cooling energy rises in hot climates and with high utilisation. | Honest PUE estimate from the configuration, measured at SAT (test E9), economizer and variable-speed fans. | Electricity tariff and IT utilisation. |
| R03 | Site fault current differs from assumption | low | Until the utility gives its fault current and voltage, arc-flash labels and some ratings are provisional. | Labels marked provisional until SAT; study updated with utility data; panel SCCR at least 65 kA. | Provide utility fault current and voltage before the unit ships. |
| R09 | Transport or lifting damage | low | A bad lift or rough transport can twist the frame or crack a weld. | Corner-casting lifts with spreader, PE-checked frame, shock loggers, set-down inspection, freight insurance. | Crane access, competent rigger, route survey for the high-cube height. |
| R12 | Vendor cloud dependence | low | If a supplier disappears or changes terms, a cloud-dependent box loses its dashboard. | Local-first design: everything runs on the gateway in the container; dashboard works with no internet; source escrow for white-label; CSV export any time. | Keep local backups (we automate to customer storage if provided). |
| R16 | Refrigerant rules change | low | GWP limits and flammable-refrigerant rules are changing; a unit model can become unavailable for new installs. | Non-flammable refrigerant under 700 GWP chosen now, or water loops; EPA 608 technicians; small charges. | Normal service contracts. |
| R19 | Component discontinued or listing changes | low | A specified part may be discontinued or lose its listing before or after build. | Approved alternates in the BOM, configuration freeze per unit, FAT repeats affected tests. | None. |
| R23 | Person inside during agent discharge or refrigerant leak | low | Clean agent or a refrigerant leak can disorient or expose a technician inside. | Pre-discharge alarm with delay, abort switch, door interlock, refrigerant detector, purge ventilation, written entry procedure, non-flammable refrigerants. | Follow the entry procedure, keep training current. |
| R25 | No Uptime Tier certification is claimed | low | We design with TIA-942 Rated-2/3 concepts but do not hold a Tier certificate; an insurer or auditor may ask. | Design-basis statement, FAT/SAT evidence, optional third-party audit at cost. | Deciding if a certification is required and paying for it. |

## 11. Site requirements summary

The full form (docs/SITE_REQUIREMENTS.md) is signed by the customer and by us at hold point H3 before anything is built for this site. Summary for this unit:

| Item | Value |
|---|---|
| Pad plan size | 2.5 × 2.5 m |
| Pad type | 150 mm reinforced slab, or 4 precast piers |
| Anchor points | 4 × M16 chemical anchors into slab |
| Gross mass to set | 1,087 kg (crane sized for this mass at the required radius) |
| Utility service | 208 or 240 V, 1φ, 3-wire + ground; customer disconnect rated 50 A for this configuration (tier range: 50 A) |
| Feeder conductors (customer side) | 8 AWG |
| Fault current | utility available fault current and voltage required before shipping; unit SCCR 65 kA |
| Generator | not in this configuration |
| Grounding electrode | Ground ring (≥ 6 m of 2 AWG bare copper, 750 mm deep around the pad) or two 3 m rods ≥ 1.8 m apart, bonded to the building electrode system if one exists (NEC 250.50) |
| Ground resistance | ≤ 25 Ω code minimum; ≤ 5 Ω recommended for IT and lightning performance; tested by fall-of-potential before set-down (H16) |
| Fiber conduit | Two 50 mm conduits (one spare) from the customer's demarcation to the unit's communications entry plate, with pull strings, sealed against water and rodents |
| Fiber service | Customer orders the circuit(s); single-mode fiber preferred; diverse routes for 2N profiles. Lead time 60–120 days — order at H3 |
| Clearances | 2.5 m clear on the door side; >= 1.5 m at condensers / dry cooler with no recirculation; >= 3 m to other structures; fire lane on one long side |
| Climate inputs the customer confirms | flood zone and base flood elevation, site wind speed and exposure, ground snow load, seismic category, altitude, corrosivity |

Permits and who pulls them:

| Permit | Typical need | Who pulls |
|---|---|---|
| Zoning / land use | Yes for 10/20/40 (accessory structure); often no for Micro | Customer |
| Building permit (structure, foundation, anchorage) | Yes for 10/20/40 | Customer's contractor or Schreiber AI as agent (we provide PE drawings) |
| Electrical permit | Yes | Licensed electrical sub (ours for the unit, customer's for the feeder) |
| Mechanical / refrigeration permit | Yes where DX or glycol piping is installed on site | Licensed HVAC sub |
| Fire alarm / suppression permit and plan review | Yes for 10/20/40 | Licensed fire protection contractor |
| Generator: air permit / registration, fuel tank permit | If generator selected | Customer (we provide engine certification and tank data) |
| Utility interconnection (solar/export only) | off_grid with PV paralleling | Customer with our documents |
| Stormwater / grading | Site dependent | Customer civil |

## 12. Acceptance: FAT and SAT

Acceptance is by the commissioning script (software/ben_engine/commissioning.py), run twice: in factory mode on load banks before shipping (FAT, hold point H13) and in site mode on the energised unit (SAT, hold point H19). The same ten steps run both times and produce a signed report with the SHA-256 of the data file. The customer may witness both; FAT passing releases the 40 % milestone and SAT passing releases the 25 % milestone.

| Step | Test | Pass criterion |
|---|---|---|
| 1 | Pre-power visual checklist | Every checklist item answered yes by the operator; no open item |
| 2 | Node discovery and firmware versions | All nodes answer; firmware versions and hashes match the release record |
| 3 | Sensor sanity at idle | Rack inlet temperatures within 2 K of each other; RH plausible; aisle dP tared |
| 4 | I/O point-to-point test | Every relay toggles and reads back; every contact (door, leak, EPO) reads correctly |
| 5 | Power chain: utility meter vs PDU sum | Meter agrees with the PDU sum within 3 % after metered cooling, house and UPS losses |
| 6 | Cooling unit sequential start and failover | Each unit starts in sequence; one unit removed and inlet stays within the ASHRAE class |
| 7 | Load step 20-100 % and thermal steady state | Inlet temperatures settle inside the ASHRAE class at 100 % load (resistive load bank on the real unit) |
| 8 | Utility loss ride-through | UPS carries IT for the configured minutes; cooling ride-through measured and published |
| 9 | Alarm verification | Inlet high, leak, door, cooling fail and utility loss each raise and clear the correct alarm |
| 10 | Export CSV and signed report | CSV of all channels exported; report carries the SHA-256 of the data and a signature block |

Pass criteria specific to this configuration: rack inlets within ASHRAE A2 at 5 kW; N+1 failover with no inlet excursion; UPS ride-through >= 10 minutes at IT load; meter vs PDU reconciliation within 3 %; PUE at full load reported against the 1.535 estimate. Deviations are closed or accepted in writing before the milestone is invoiced.

## 13. Warranty, maintenance and support

| Item | Value |
|---|---|
| Workmanship warranty | 24 months from SAT on the integration, wiring, piping, envelope and controls build |
| Equipment warranty | Vendor warranties (UPS, cooling, CDU, batteries, fire panel, generator, servers) registered in the customer's name at turnover and passed through; minimum 12 months, longer where the vendor offers it |
| Controls software | Signed firmware and gateway updates for the licence term; security fixes for the life of the licence |
| Support level in this option | Remote email support during business hours for the warranty period; maintenance by the customer or a certified subcontractor per the schedule |

Maintenance schedule (docs/MAINTENANCE.md; intervals for temperate climate, climate add-ons shorten some intervals; task counts per interval):

| Interval | Who | Tasks |
|---|---|---|
| Weekly (remote, 15 minutes) — R | Remote, Schreiber AI operations (R) | 9 |
| Monthly — L (1–2 hours on site) with R review | Local technician (L) with remote review | 8 |
| Quarterly — L + S | Local technician + certified subcontractor (L + S) | 6 |
| Semi-annual | Certified subcontractor (S) with record; remote (R) for controls | 4 |
| Annual | Certified subcontractor (S) with record; remote (R) for controls | 8 |
| 3-year | Certified subcontractor (S) with record; remote (R) for controls | 4 |
| 5-year | Certified subcontractor (S) with record; remote (R) for controls | 6 |

Sensor calibration every 12 months (or on drift trigger) with GUM uncertainty budgets; a spare parts kit per unit is delivered at turnover (MAINTENANCE.md section 7). Climate add-ons for this unit: baseline intervals.

## 14. Commercial terms summary

The governing documents are the Master Services Agreement (docs/contracts/MSA.md), the Statement of Work for this unit (docs/contracts/SOW_TEMPLATE.md, pre-filled from this proposal), the change order form (docs/contracts/CHANGE_ORDER.md), the acceptance certificates, and for the controls layer the software licence (docs/contracts/SOFTWARE_LICENCE.md) and, for the managed option, the service level agreement (docs/contracts/SLA.md). This section summarises them; the contracts prevail.

| Term | Summary |
|---|---|
| Payment | 30 % at Engineering release / 40 % at Factory acceptance test / 25 % at Site acceptance test / 5 % at Turnover; net 30 from invoice; recurring fees annually in advance |
| Price validity | 60 days from the proposal date; capital price firm at engineering release (configuration frozen, hold point H4) |
| Scope changes | Every change after engineering release is a change order; each change order carries its price impact and its schedule impact and is signed before the work is done |
| Customer-caused delay | A delay caused by the customer or its contractors (site not ready, permits, utility, late information or approvals) extends the schedule day for day and suspends Schreiber AI's liquidated-damages exposure for that period |
| Delivery liquidated damages | 0.5 % of the capital price per week of Schreiber AI-caused delay to FAT, capped at 5.0 %; sole remedy for delay |
| Storage of a finished unit | If the unit passes FAT and cannot ship because the site, permits or utility are not ready, storage and preservation are charged at $60 per day after 14 days, and the FAT milestone is payable |
| Supplier and contract-manufacturer delay | Delivery liquidated damages in our supplier purchase orders and contract-manufacturing agreements flow back-to-back with the customer terms, so a late UPS or switchgear supplier bears its share of any delay damages |
| Title and risk | Title passes at payment of the FAT milestone; risk of loss passes at set-down; freight insured to full replacement value |
| Warranty | 24 months workmanship; vendor warranties passed through (section 13) |
| Acceptance | FAT and SAT by the commissioning script; deviations closed or accepted in writing; acceptance deemed 10 business days after a passing SAT report if not signed |
| Data and software | Customer owns its data; controls software is licensed, not sold; firmware is signed; no cloud dependency |
| Governing law | [GOVERNING_STATE] (set in the MSA) |

## 15. Assumptions and what is not included

- Configuration as on the cover: 5 kW IT, 1 rack(s), Cabinet DX air conditioner, N+1, climate Temperate; any change is priced as a change order
- Prices from purchasing/parts_catalog.json priced on the dates in the BOM; 68 % confirmed, 0 % list, 32 % estimate for this option; the estimate share is re-priced at engineering release
- Gross margin 28% on hardware and build labour; controls licence $1,200/yr for this tier; white-label uplift x1.25; managed service $45/kW-month
- Domestic delivery within one day's haul of the integration shop; export, over-dimension permits beyond the carrier's standard, and crane standby beyond one day are extra
- Utility fault current <= 65 kA and voltage within +/-10 % at the disconnect; otherwise current-limiting fuses are added by change order
- Soil bearing >= 100 kPa; otherwise a geotechnical report and revised foundation are the customer's cost
- Permit fees, utility fees, taxes and duties are excluded; AHJ edition of each code applies (docs/COMPLIANCE.md section 13 lists editions not verified on the proposal date)
- Compute hardware prices are reseller listings on the BOM date; GPU server availability can move lead times
- Not included: site civil, utility service, permits, fiber circuits, customer IT software, generator fuel, insurance after set-down, spare parts beyond the turnover kit, decommissioning (quoted separately)

## 16. Signature block

By signing, the customer accepts this proposal (SAI-MICRO-20261108-C6D4D2A1) and the risk disclosure in section 10, and authorises Schreiber AI to start the site survey and engineering release; the site requirements form is signed separately at hold point H3.

| Role | Name | Signature | Date |
|---|---|---|---|
| Customer authorised representative, Riverside Dental Group |  |  |  |
| Schreiber AI — sales |  |  |  |
| Schreiber AI — engineering |  |  |  |
| Schreiber AI — compliance |  |  |  |

---
*Schreiber AI — proposal SAI-MICRO-20261108-C6D4D2A1. Generated by ben_engine.proposal from the configuration model; numbers are not hand-edited.*