# Schreiber AI — BEN Engine proposal SAI-BEN30-20261108-B4E851A1

*BEN 30 · Industrial OT analytics · Lakeshore Foundry · Duluth, MN · 2026-11-08 · valid until 2027-01-07*

## 1. Cover

| Item | Value |
|---|---|
| Proposal | BEN Engine BEN 30 for Lakeshore Foundry |
| Prepared by | Schreiber AI |
| Customer | Lakeshore Foundry |
| Site | Duluth, MN |
| Tier | BEN 30 — 10 ft high-cube ISO-frame module, sealed to IP66 |
| Mission profile | Industrial OT analytics (industrial_ot) |
| Climate package | Cold |
| Purchase option | Hardware + BEN Controls |
| Date | 2026-11-08 |
| Valid until | 2027-01-07 (60 days) |
| Proposal ID | SAI-BEN30-20261108-B4E851A1 |
| Configuration | 13 kW IT in 2 rack(s), In-row DX cooling unit (300 mm, 20 kW), N+1, 10 min UPS |

AI infrastructure that arrives finished. This proposal is generated from configuration version 0b0ffd59; every number in it comes from the same model that produces the drawings, bill of materials, digital twin and commissioning script.

## 2. Executive summary

Lakeshore Foundry needs 13 kW of IT capacity for a Industrial OT analytics workload at Duluth, MN. We propose one BEN 30: a 10 ft high-cube ISO-frame module, sealed to IP66 fitted out as a complete data center with 2 rack(s), In-row DX cooling unit (300 mm, 20 kW) with N+1 redundancy, a 2 x 16 kVA UPS giving 10 minutes of ride-through, clean-agent fire protection and the BEN Controls layer (sensors, firmware, digital twin, dashboard).

The unit arrives finished and factory-tested. It needs a pad, a 100 A 208 V 3ph feeder, fiber and a grounding electrode at the site; everything inside the enclosure is built, wired, tested and documented before it ships.

Price for the hardware + ben controls option: $551,270 capital ($42,405 per kW IT) plus $4,800 per year (BEN Controls licence). 68 % of the underlying cost is at confirmed vendor prices, 0 % at manufacturer list price and 32 % is engineering estimate; the price is firm at engineering release, when the configuration is frozen.

Order to in-service: about 21 weeks, set by the longest-lead item (10 weeks) and the permit cycle. Risks are disclosed in section 10 before the price is accepted; the site requirements in section 11 are signed before anything is built for this site.

## 3. Mission profile and what it means

| Item | Value |
|---|---|
| Profile | Industrial OT analytics (industrial_ot) |
| ASHRAE class | A3: 5–40 °C inlet allowable; hardened IT and wider economizer hours |
| Redundancy | N+1: one spare cooling unit and one spare UPS module; any single unit can fail or be serviced with no loss of capacity |
| Design rack density | 6.5 kW per rack (profile default 8 kW) |
| Climate package | Cold: design outdoor 30 °C / minimum -40 °C, solar 700 W/m², corrosion class ISO 9223 C3, basic wind 47 m/s (ASCE 7) |
| Cooling derate at design day | 1.000 -> 20.0 kW per unit; 2 units installed for 1 required |
| Generator | not included (option) |

What this means for you: the environmental class sets the alarm limits your IT will be held to; the redundancy level sets what happens when a component fails; the climate package sets the coatings, anchorage, condensation control and cooling capacity margins built into the unit. All three are fixed at engineering release and verified at the factory and site acceptance tests.

## 4. The unit: sizing

| Item | Value | Basis |
|---|---|---|
| Enclosure | 10 ft high-cube ISO-frame module, sealed to IP66 | External 2.991 x 2.438 x 2.896 m; interior 2.7 x 2.2 x 2.49 m |
| IT load | 13 kW in 2 rack(s) of 42 U | 6.5 kW per rack; tier range 10–30 kW |
| Cooling | 2 x In-row DX cooling unit (300 mm, 20 kW) | 1 required at 20.0 kW each (derate 1.0), N+1 |
| Row fit | fits | 1 row(s) of 2 racks, 2300 mm per row vs interior 2700 mm |
| Cooling electrical | 4.19 kW | COP 3.1 at design point |
| Total electrical demand | 18.0 kW / 18.9 kVA | IT + cooling + 2 % house + 0.5 kW controls, pf 0.95 |
| Controls tier | BEN Controls Lite | Revolution Pi RevPi Connect 4 + DIO/AIO (DIN rail, listed), software interlocks behind a hardware watchdog relay; 6 BEN Pods on the BEN Mesh (Thread, Secure Vault); selectable with controls_tier (docs/CONTROLS_HARDWARE_DECISION.md 2a) |
| Service | 208 V 3ph, 100 A breaker | calculated 66 A at 80 % continuous, rounded to the next frame |
| Generator | not included (option) | total demand x 1.25, rounded to 10 kW |
| Hardening | H2 Severe environment: NEMA 4X / IP66 + flood plinth 600 mm | coating ISO 12944 C5-M; recommended for this profile/climate: H2; envelope 38.7 m² |
| UPS | 2 x 16 kVA | IT only with 15 % headroom, N+1 |
| Battery | 2.4 kWh lithium (LFP) | 10 min at IT load, 90 % depth of discharge |
| NFPA 855 scope | no - battery below 20 kWh | energy storage threshold |
| Airflow | 1,625 cfm | 125 cfm/kW air-cooled at 12 K rise; 40 cfm/kW liquid/water |
| Envelope gain at design day | 0.47 kW | 100 mm PIR, R 3.5 m²K/W, solar on roof |
| Mass | payload 3,112 kg; gross 4,412 kg | tare 1,300 kg; crane and pad sized for the gross mass |
| PUE estimate | 1.411 | design-point calculation incl. 0.03 UPS loss; measured at SAT |

## 5. Scope of supply

| Module | Status | BOM lines | Sell price |
|---|---|---|---|
| Power module | included | 12 lines | $47,363 |
| Cooling module | included | 4 lines | $66,724 |
| Compute module | included | 5 lines | $294,679 |
| Controls module | included | 22 lines | $10,520 |
| Structure (container / cabinet) | included | 17 lines | $36,483 |
| Envelope (insulation, liner, coatings) | included | 18 lines | $17,254 |
| Fire detection and suppression | included | 6 lines | $15,795 |
| Site kit (anchors, embeds, signage) | included | 8 lines | $26,806 |
| Build labour, FAT, logistics | included | 9 lines | $35,646 |

Top 15 lines of the 101-line bill of materials for this option (sell price at 28% gross margin; the full priced BOM with vendors, part numbers and price confirmation dates is delivered at engineering release):

| Code | Item | Manufacturer / MPN | Qty | Sell price | Price basis | Lead (wk) |
|---|---|---|---|---|---|---|
| CMP-GPU-L40S | GPU SuperServer 4U, 2x Xeon, 8x NVIDIA L40S (~4 kW), configured | Supermicro SYS-421GE-TNRT | 2 ea | $228,692 | confirmed | 6 |
| CMP-CPU | PowerEdge R760 2U rack server (management / storage node) | Dell Technologies R760 | 2 ea | $49,997 | confirmed | 3 |
| CLG-INROW | InRow DX 300 mm 30 kW air-cooled in-row unit (indoor section) (ACRD301S is the 300 mm, ~20 kW class unit = config inrow_dx_300; 600 mm/30 kW class ACRD600 series to be quoted for inrow_dx) | APC by Schneider Electric ACRD301S | 2 ea | $45,835 | confirmed | 10 |
| PWR-UPS-RM20 | Rack/tower online UPS 20 kVA 208 V, 10U, parallel-capable (BEN 30 R1, 3 x in parallel for N+1; 93PM tower does not fit the row) | Vertiv GXT5-20KMVRT11UXLN | 2 ea | $26,389 | estimate | 6 |
| CLG-COND | Outdoor air-cooled condensing unit for ACRD301S (30 kW), 460 V | APC by Schneider Electric ACCD75208 | 2 ea | $18,056 | estimate | 10 |
| CMP-SW100G | Spectrum SN2700 32x100GbE QSFP28 switch, Cumulus Linux | NVIDIA Mellanox MSN2700-CS2RC | 1 ea | $14,712 | confirmed | 2 |
| FS-CLEAN-AGENT | Pre-engineered FK-5-1-12 (Novec 1230) clean agent system, installed: cylinder, nozzles, releasing panel, detection, design & AHJ submittal | Fike / Kidde (via licensed fire contractor) ECS-500 / Fike CA | 17 m3 protected | $12,986 | estimate | 8 |
| SVC-ELECTRICIAN | Licensed electrician (commercial journeyman, billed) | local electrical contractor ELEC-HR | 66 h | $10,083 | estimate | 1 |
| STR-CONT10 | 10 ft high-cube ISO container, one-trip (new) | CIMC/various 10HC-1TRIP | 1 ea | $6,806 | confirmed | 3 |
| STR-RACK42 | NetShelter SX 42U 600x1070 mm enclosure with sides | APC by Schneider Electric AR3100 | 2 ea | $6,444 | confirmed | 1 |
| STR-FLOOD-PLINTH | Flood plinth 600 mm: hot-dip galvanised steel frame with cross-bracing, grating step and sealed service risers, per m of enclosure perimeter (H2 severe environment) | local steel fabricator PLINTH-600 | 11 m | $6,417 | estimate | 8 |
| SITE-ELEC | Utility service interconnect: meter base, trench, conduit, utility fees, per ampere | local electrical contractor / utility SVC-INTERCONNECT | 100 A | $6,250 | estimate | 6 |
| SITE-FIBER | Fiber drop, handhole, 24-strand SM to demarc | local ISP / contractor FIBER-DROP | 1 lot | $6,250 | estimate | 8 |
| SVC-MODS-MAT | Container modification materials per opening (frame steel, flashing, louvers, primer) | local steel supplier MOD-OPENING | 5 opening | $6,250 | estimate | 1 |
| PWR-PDU | NetShelter metered rack PDU 0U 5.0 kW 208 V 30 A, L6-30P, (36) C13 (6) C19 | APC by Schneider Electric AP8841 | 4 ea | $6,222 | confirmed | 1 |

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
| Hardware only | $540,750 | $41,596 | - | 1 yr | $540,750 | 69 / 0 / 31 % | 79 | alternative |
| Hardware + BEN Controls | $551,270 | $42,405 | $4,800 | 1 yr | $556,070 | 68 / 0 / 32 % | 101 | PROPOSED |
| White-label | $551,270 | $42,405 | $6,000 | 1 yr | $557,270 | 68 / 0 / 32 % | 101 | alternative |
| Managed service | $551,270 | $42,405 | $7,020 | 3 yr | $572,330 | 68 / 0 / 32 % | 101 | alternative |

Confirmed = price seen on a vendor or distributor listing on the date in the BOM; list = manufacturer published price; estimate = engineering estimate with its basis stated in the BOM note. Capital prices carry a 28% gross margin on purchased hardware and build labour. Recurring items: Hardware + BEN Controls: BEN Controls licence (dashboard, twin, firmware updates, remote support hooks); White-label: White-label licence under the Schreiber AI brand (controls licence x 1.25, partner branding, source escrow); Managed service: Managed service at $45/kW-month x 13 kW IT (includes the BEN Controls licence, remote operations and the maintenance schedule).

| Managed service term | Capital | Service fees | Total |
|---|---|---|---|
| 1 year | $551,270 | $7,020 | $558,290 |
| 3 years | $551,270 | $21,060 | $572,330 |
| 5 years | $551,270 | $35,100 | $586,370 |

Payment milestones for the proposed option (Hardware + BEN Controls, capital $551,270):

| Milestone | Share | Amount | Week from order |
|---|---|---|---|
| Engineering release (H4) | 30 % | $165,381 | 4 |
| Factory acceptance test (H13) | 40 % | $220,508 | 17 |
| Site acceptance test (H19) | 25 % | $137,817 | 20 |
| Turnover (W20) | 5 % | $27,564 | 21 |

Recurring fees are invoiced annually in advance from turnover. Prices are in USD, exclude taxes, and are valid to the date on the cover; the capital price becomes firm at engineering release.

## 7. Schedule

Milestones in weeks from order, derived from the stage durations in docs/PROCESS_FLOW.md for the BEN 30 (reference order-to-service about 20 weeks) and the longest lead time in this bill of materials (10 weeks). Critical path: engineering release -> long-lead procurement -> fit-out -> FAT -> SAT. Site civil and permits run in parallel.

| Week | Milestone | Owner | Hold / witness point | Path |
|---|---|---|---|---|
| 0 | Order and risk acknowledgement signed | Customer + Schreiber AI | - | critical |
| 2 | Site survey and site requirements sign-off | Customer + ENG | H3 | critical |
| 4 | Engineering release: configuration frozen, IFC drawings, BOM; long-lead purchase orders placed | ENG | H4 | critical |
| 7 | Container / cabinet received and inspected; structural and envelope work starts | FAC | W6, H7, W8 | critical |
| 12 | Permits issued (building, electrical, mechanical, fire plan review) | Customer / AHJ | - | parallel |
| 14 | Longest-lead item on the floor (10 weeks from release); mechanical and electrical fit-out complete | FAC + SUB | H10 | critical |
| 16 | Site pad, grounding and utility feeder complete and surveyed | Customer civil | H16 | parallel |
| 17 | Cooling, controls and firmware complete; factory acceptance test incl. 24 h burn-in | FAC + ENG; customer witness | H11, W12, H13 | critical |
| 18 | Transport prep and shipping | LOG | - | critical |
| 19 | Set-down, hook-up and pre-energisation check | LOG + SUB + AHJ | W17, H18 | critical |
| 20 | Site acceptance test and fire marshal acceptance | ENG + customer + AHJ | H19 | critical |
| 21 | Training and turnover; unit in service | ENG + customer | W20 | critical |

Long-lead items (ordered at engineering release):

| Code | Item | Vendor | Qty | Lead time (weeks) |
|---|---|---|---|---|
| CLG-INROW | InRow DX 300 mm 30 kW air-cooled in-row unit (indoor section) (ACRD301S is the 300 mm, ~20 kW class unit = config inrow_dx_300; 600 mm/30 kW class ACRD600 series to be quoted for inrow_dx) | CDW | 2 ea | 10 |
| CLG-COND | Outdoor air-cooled condensing unit for ACRD301S (30 kW), 460 V | CDW / Schneider | 2 ea | 10 |
| FS-CLEAN-AGENT | Pre-engineered FK-5-1-12 (Novec 1230) clean agent system, installed: cylinder, nozzles, releasing panel, detection, design & AHJ submittal | licensed fire contractor | 17 m3 protected | 8 |
| STR-FLOOD-PLINTH | Flood plinth 600 mm: hot-dip galvanised steel frame with cross-bracing, grating step and sealed service risers, per m of enclosure perimeter (H2 severe environment) | steel fabricator | 11 m | 8 |
| SITE-FIBER | Fiber drop, handhole, 24-strand SM to demarc | local | 1 lot | 8 |

## 8. Drawings and documents delivered

Issue-for-construction drawing set for the BEN 30, regenerated from the frozen configuration at engineering release and re-issued as built after SAT. Issue for construction set regenerated from the frozen configuration at engineering release (index not readable at proposal time)

| Sheet | Title | Scale |
|---|---|---|
| A-001 | General arrangement | see sheet |
| A-002 | Interior layout plan | see sheet |
| A-003 | Envelope section | 1:10 / 1:2 |
| S-001 | Floor framing and anchoring | see sheet / 1:5 |
| E-001 | Power one-line | NTS |
| M-001 | Cooling P&ID | NTS |
| C-001 | Controls layout | see sheet |

Document set (indexed binder, encrypted USB in the BEN Controller panel pocket, and the edge computer share, per docs/TURNOVER.md):

- At order: this proposal, risk acknowledgement, site requirements form (docs/SITE_REQUIREMENTS.md) for signature
- At engineering release (H4): frozen configuration JSON with derived sizing, IFC drawing set with CTQ/CTP callouts, priced bill of materials with confirmation status, arc-flash and coordination study, PE anchorage calculation, compliance pack, FAT/SAT procedure
- At FAT (H13): signed commissioning report (JSON + PDF) with sweep CSVs, thermography, door-fan test, electrical and cooling test records
- At SAT (H19): site commissioning report, acoustic survey, final arc-flash labels, AHJ certificates
- At turnover (W20): as-built drawings, as-built BOM with serials, O&M manual, maintenance schedule with the first 12 months pre-populated, calibration certificates per channel, firmware hashes, Pod certificate register, edge computer backup, password handover record, training sign-off, warranty certificates

## 9. Compliance pack for this profile

Compliance is central to the design, not an appendix: docs/COMPLIANCE.md maps every applicable code to a design feature and a verification. The pack delivered with this unit is the subset for the profile and climate below.

| Item | Value |
|---|---|
| Profile | industrial_ot (A3, N+1) |
| ASHRAE class / redundancy (from config) | A3 / N+1 |
| Emphasis | OT analytics on plant |
| Standards emphasised | IEC 62443 zones aligned to plant Purdue model; NFPA 70E for plant electricians; NEMA 4/4X dust option |
| Extra documents in the pack | Zone/conduit drawing joined to plant network drawing; dust/vibration add-on |
| Typical AHJ / third-party questions | Who owns the firewall between plant and BEN controls |

Climate add-ons:

| Item | Value |
|---|---|
| Climate | cold |
| Config values | 30 °C / −40 °C, 47 m/s |
| Compliance / design add-ons | Low-ambient kits on DX (crankcase heaters, head-pressure control to −40 °C); glycol 50 % propylene glycol in dry cooler loops; heat trace on condensate and drains; door seal heaters; battery heating (lithium charge inhibited < 0 °C — BMS review); snow load on roof and dry cooler (site ground snow load → PE); economizer lockout logic for sub-zero humidity |
| Verification | Freeze-protection checklist; snow load calc |

Baseline matrix lines that apply to every unit:

| Code / standard | Design feature | Verification |
|---|---|---|
| NFPA 70 (NEC) | Listed dead-front gear, SCCR 65 kA, selective coordination, arc-flash labels | Electrical inspection H10, AHJ at H18 |
| NFPA 75 / 2001 / 72 | Non-combustible liner, VEWFD, clean agent with 10-min hold, EPO, HVAC shutdown | Door-fan test, NFPA 72 record of completion at SAT |
| UL 508A | BEN Controls Lite: DIN-rail cabinet of UL-listed components (RevPi, QUINT4, switch); no 508A panel label | Component listing marks (CTQ-K6) |
| ASHRAE TC 9.9 | Class A3 alarm limits in the controls | Load step test E3/E7 at FAT and SAT |
| AIM Act / EPA 608 | GWP < 700 A1 refrigerant or water loops; certified technicians | Charge record per circuit |
| ISO 668 / 1496 / CSC | One-trip high-cube container, PE-checked modifications, CSC decision at transport | Weld inspection H7, weigh ticket |

## 10. Risks disclosed up front

These are the risks that apply to the industrial ot analytics profile, from the product risk register (docs/RISK_REGISTER.md, web/assets/risks.json). Each line says what the design covers and what remains the customer's decision or duty. Please read them before accepting the price.

| ID | Risk | Severity | What can happen | Covered by the design | Customer owns |
|---|---|---|---|---|---|
| R01 | Utility power loss | high | The grid fails for seconds to days. IT shuts down when the battery runs out and cooling stops at once unless it is on UPS or generator. | UPS ride-through (default 10 min), generator option with ATS, measured cooling ride-through (test E5), N+1/2N per profile. | Whether to buy the generator and fuel, the utility contract, and whether cooling is put on UPS. |
| R15 | Permit delay or unexpected AHJ requirement | high | The local authority may classify the container as a building, ask for a field evaluation or more fire protection, and take longer than the build. | Pre-application package, code summary, field-evaluation budget line, site requirements signed before build, parallel permit path in the schedule. | Pulling permits (or authorising us), zoning, neighbour relations. |
| R18 | Long-lead parts slip | high | UPS, switchgear, cooling units and transformers can take months and slip. | Long-lead orders at engineering release, approved alternates, stocked controls hardware. | Early deposit and configuration freeze; no late changes. |
| R27 | Medium-voltage utility service lead time (BEN 2000) | high | A new 12.47 kV service with primary metering and two pad-mount transformers is utility work on the utility's schedule, typically 26 to 52 weeks. | Interconnection application filed at order, utility window carried on the critical path, load letter and single-line ready at kick-off, temporary 480 V service for commissioning where allowed. | The utility contract and fees, land for utility equipment, easements. |
| R30 | Construction permit for a building (BEN 2000) | high | The hall is a building (IBC Group B or F-1), not an equipment enclosure: plan review, state modular approval and inspections take 8 to 16 weeks before civil works can start. | Stamped permit set from the engineering release, state modular label on each module, pre-application meeting, civil package starts after permit, both occupancy classifications budgeted. | Zoning, land use, easements, neighbour notice, permit fees. |
| R02 | Arc flash or electrical fault | medium | A fault while a panel is open or a component failure can injure someone and damage equipment. | Arc-flash study and labels, selective coordination, listed dead-front gear, lockout points, NFPA 70E training at turnover. | Only qualified electricians work on it and the labels are followed. |
| R06 | Fire inside the container | medium | A cable, battery or power supply fire would mean loss of IT, an agent discharge and downtime. | Very-early smoke detection, clean agent with 10-minute hold, HVAC shutdown, EPO, non-combustible liner, battery separation. | Fire marshal relationship, agent recharge contract, no combustible storage inside, insurance. |
| R11 | Intrusion into the controls network | medium | An attacker who reaches the controls LAN could change setpoints or stop cooling. | IEC 62443 zones, isolated controls LAN, signed firmware, no inbound ports, outbound-only remote support that can be disabled, hardwired life safety. | The firewall between BEN controls and the customer LAN (unless managed), password handover, patch windows. |
| R14 | Sensor drift gives false comfort | medium | A drifted sensor can make the dashboard look fine while the room is not. | Redundant sensors, idle cross-check (test E1), drift detection, 12-month or trigger-based recalibration. | Allow calibration visits, do not move sensors. |
| R20 | Site costs above quote | medium | Civil works, permits and utility connection can cost more than the allowance. | Firm box price after engineering release; site works quoted after survey; utility costs identified at survey. | Utility fees, civil works, permits, taxes, and changes after freeze. |
| R29 | Module joint leakage (BEN 2000) | medium | The three hall modules are sealed on site; the seams are the one part of the IP66 envelope not finished in the factory. | Factory compression gaskets and field EPDM cover strips with a drained cavity, joint seal hose test E15 at SAT and after any relocation, leak rope under each joint, semi-annual seal inspection. | Keep the roof clear of debris and snow beyond design, respond to alarms. |
| R03 | Site fault current differs from assumption | low | Until the utility gives its fault current and voltage, arc-flash labels and some ratings are provisional. | Labels marked provisional until SAT; study updated with utility data; panel SCCR at least 65 kA. | Provide utility fault current and voltage before the unit ships. |
| R09 | Transport or lifting damage | low | A bad lift or rough transport can twist the frame or crack a weld. | Corner-casting lifts with spreader, PE-checked frame, shock loggers, set-down inspection, freight insurance; BEN 2000 modules lifted on engineered lugs with a 100 t crane and a certified lift plan. | Crane access, competent rigger, route survey for the high-cube height. |
| R16 | Refrigerant rules change | low | GWP limits and flammable-refrigerant rules are changing; a unit model can become unavailable for new installs. | Non-flammable refrigerant under 700 GWP chosen now, or water loops; EPA 608 technicians; small charges. | Normal service contracts. |
| R19 | Component discontinued or listing changes | low | A specified part may be discontinued or lose its listing before or after build. | Approved alternates in the BOM, configuration freeze per unit, FAT repeats affected tests. | None. |
| R23 | Person inside during agent discharge or refrigerant leak | low | Clean agent or a refrigerant leak can disorient or expose a technician inside. | Pre-discharge alarm with delay, abort switch, door interlock, refrigerant detector, purge ventilation, written entry procedure, non-flammable refrigerants. | Follow the entry procedure, keep training current. |
| R32 | Ballistic or forced-entry attack | low | Gunfire or a break-in can destroy IT, injure people or take data-bearing equipment. | H1: steel skin, keyed access, door contacts. H3: UL 752 ballistic panels (level 3 to 8), ASTM F3038 forced-entry doors, IK10, mantrap vestibule, two-factor access, tamper detection on the PLC and an audit trail in BEN Care. | Threat assessment and choice of level, guard force and response, perimeter. |

## 11. Site requirements summary

The full form (docs/SITE_REQUIREMENTS.md) is signed by the customer and by us at hold point H3 before anything is built for this site. Summary for this unit:

| Item | Value |
|---|---|
| Pad plan size | 5.0 × 4.5 m + condenser yard 3 × 3 m |
| Pad type | 200 mm reinforced slab on 150 mm compacted base, or 4 reinforced concrete piers 600 × 600 mm at corner castings to frost depth |
| Anchor points | 4 × cast-in twist-lock bases or weld plates at corner castings (ISO 1161 pattern) |
| Gross mass to set | 4,412 kg (crane sized for this mass at the required radius) |
| Utility service | 208Y/120 V, 3φ, 4-wire + ground; customer disconnect rated 100 A for this configuration (tier range: 150 A) |
| Feeder conductors (customer side) | 1/0 AWG |
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
| Zoning / land use | Yes for 30/150/500 (accessory structure); often no for BEN 5; BEN 2000: principal structure, site plan approval | Customer |
| Building permit (structure, foundation, anchorage) | Yes for 30/150/500; BEN 2000: full building permit (IBC Group B or F-1) plus state modular-building approval | Customer's contractor or Schreiber AI as agent (we provide PE drawings) |
| Electrical permit | Yes | Licensed electrical sub (ours for the unit, customer's for the feeder) |
| Mechanical / refrigeration permit | Yes where DX or glycol piping is installed on site | Licensed HVAC sub |
| Fire alarm / suppression permit and plan review | Yes for 30/150/500 | Licensed fire protection contractor |
| Generator: air permit / registration, fuel tank permit | If generator selected | Customer (we provide engine certification and tank data) |
| Utility interconnection (solar/export only) | off_grid with PV paralleling | Customer with our documents |
| MV service application (BEN 2000) | Always | Customer, with our load letter and single-line |
| Stormwater construction permit (NPDES CGP) | BEN 2000 (disturbance > 0.4 ha) | Customer civil |
| Water supply and sewer discharge (BEN 2000) | Always | Customer |
| Stormwater / grading | Site dependent | Customer civil |

## 12. Acceptance: FAT and SAT

Acceptance is by the commissioning script (software/ben_engine/commissioning.py), run twice: in factory mode on load banks before shipping (FAT, hold point H13) and in site mode on the energised unit (SAT, hold point H19). The same ten steps run both times and produce a signed report with the SHA-256 of the data file. The customer may witness both; FAT passing releases the 40 % milestone and SAT passing releases the 25 % milestone.

| Step | Test | Pass criterion |
|---|---|---|
| 1 | Pre-power visual checklist | Every checklist item answered yes by the operator; no open item |
| 2 | Pod discovery, attestation and firmware versions | All BEN Pods answer and attest; firmware versions and hashes match the release record |
| 3 | Sensor sanity at idle | Rack inlet temperatures within 2 K of each other; RH plausible; aisle dP tared |
| 4 | I/O point-to-point test | Every relay toggles and reads back; every contact (door, leak, EPO) reads correctly |
| 5 | Power chain: utility meter vs PDU sum | Meter agrees with the PDU sum within 3 % after metered cooling, house and UPS losses |
| 6 | Cooling unit sequential start and failover | Each unit starts in sequence; one unit removed and inlet stays within the ASHRAE class |
| 7 | Load step 20-100 % and thermal steady state | Inlet temperatures settle inside the ASHRAE class at 100 % load (resistive load bank on the real unit) |
| 8 | Utility loss ride-through | UPS carries IT for the configured minutes; cooling ride-through measured and published |
| 9 | Alarm verification | Inlet high, leak, door, cooling fail and utility loss each raise and clear the correct alarm |
| 10 | Export CSV and signed report | CSV of all channels exported; report carries the SHA-256 of the data and a signature block |

Pass criteria specific to this configuration: rack inlets within ASHRAE A3 at 13 kW; N+1 failover with no inlet excursion; UPS ride-through >= 10 minutes at IT load; meter vs PDU reconciliation within 3 %; PUE at full load reported against the 1.411 estimate. Deviations are closed or accepted in writing before the milestone is invoiced.

## 13. Warranty, maintenance and support

| Item | Value |
|---|---|
| Workmanship warranty | 24 months from SAT on the integration, wiring, piping, envelope and controls build |
| Equipment warranty | Vendor warranties (UPS, cooling, CDU, batteries, fire panel, generator, servers) registered in the customer's name at turnover and passed through; minimum 12 months, longer where the vendor offers it |
| Controls software | Signed Pod firmware, PLC project and edge computer updates for the licence term; security fixes for the life of the licence |
| Support level in this option | Remote dashboard access and business-hours support for the licence term; maintenance by the customer's technician with our remote review |

Maintenance schedule (docs/MAINTENANCE.md; intervals for temperate climate, climate add-ons shorten some intervals; task counts per interval):

| Interval | Who | Tasks |
|---|---|---|
| Weekly (remote, 15 minutes) — R | Remote, Schreiber AI operations (R) | 9 |
| Monthly — L (1–2 hours on site) with R review | Local technician (L) with remote review | 8 |
| Quarterly — L + S | Local technician + certified subcontractor (L + S) | 6 |
| Semi-annual | Certified subcontractor (S) with record; remote (R) for controls | 5 |
| Annual | Certified subcontractor (S) with record; remote (R) for controls | 9 |
| 3-year | Certified subcontractor (S) with record; remote (R) for controls | 5 |
| 5-year | Certified subcontractor (S) with record; remote (R) for controls | 6 |

Sensor calibration every 12 months (or on drift trigger) with GUM uncertainty budgets; a spare parts kit per unit is delivered at turnover (MAINTENANCE.md section 7). Climate add-ons for this unit: freeze-protection checklist before winter, heat-trace and door-seal heater test, snow removal plan.

## 14. Commercial terms summary

The governing documents are the Master Services Agreement (docs/contracts/MSA.md), the Statement of Work for this unit (docs/contracts/SOW_TEMPLATE.md, pre-filled from this proposal), the change order form (docs/contracts/CHANGE_ORDER.md), the acceptance certificates, and for the controls layer the software licence (docs/contracts/SOFTWARE_LICENCE.md) and, for the managed option, the service level agreement (docs/contracts/SLA.md). This section summarises them; the contracts prevail.

| Term | Summary |
|---|---|
| Payment | 30 % at Engineering release / 40 % at Factory acceptance test / 25 % at Site acceptance test / 5 % at Turnover; net 30 from invoice; recurring fees annually in advance |
| Price validity | 60 days from the proposal date; capital price firm at engineering release (configuration frozen, hold point H4) |
| Scope changes | Every change after engineering release is a change order; each change order carries its price impact and its schedule impact and is signed before the work is done |
| Customer-caused delay | A delay caused by the customer or its contractors (site not ready, permits, utility, late information or approvals) extends the schedule day for day and suspends Schreiber AI's liquidated-damages exposure for that period |
| Delivery liquidated damages | 0.5 % of the capital price per week of Schreiber AI-caused delay to FAT, capped at 5.0 %; sole remedy for delay |
| Storage of a finished unit | If the unit passes FAT and cannot ship because the site, permits or utility are not ready, storage and preservation are charged at $150 per day after 14 days, and the FAT milestone is payable |
| Supplier and contract-manufacturer delay | Delivery liquidated damages in our supplier purchase orders and contract-manufacturing agreements flow back-to-back with the customer terms, so a late UPS or switchgear supplier bears its share of any delay damages |
| Title and risk | Title passes at payment of the FAT milestone; risk of loss passes at set-down; freight insured to full replacement value |
| Warranty | 24 months workmanship; vendor warranties passed through (section 13) |
| Acceptance | FAT and SAT by the commissioning script; deviations closed or accepted in writing; acceptance deemed 10 business days after a passing SAT report if not signed |
| Data and software | Customer owns its data; controls software is licensed, not sold; firmware is signed; no cloud dependency |
| Governing law | [GOVERNING_STATE] (set in the MSA) |

## 15. Assumptions and what is not included

- Configuration as on the cover: 13 kW IT, 2 rack(s), In-row DX cooling unit (300 mm, 20 kW), N+1, climate Cold; any change is priced as a change order
- Prices from purchasing/parts_catalog.json priced on the dates in the BOM; 68 % confirmed, 0 % list, 32 % estimate for this option; the estimate share is re-priced at engineering release
- Gross margin 28% on hardware and build labour; controls licence $4,800/yr for this tier; white-label uplift x1.25; managed service $45/kW-month
- Domestic delivery within one day's haul of the integration shop; export, over-dimension permits beyond the carrier's standard, and crane standby beyond one day are extra
- Utility fault current <= 65 kA and voltage within +/-10 % at the disconnect; otherwise current-limiting fuses are added by change order
- Soil bearing >= 100 kPa; otherwise a geotechnical report and revised foundation are the customer's cost
- Permit fees, utility fees, taxes and duties are excluded; AHJ edition of each code applies (docs/COMPLIANCE.md section 13 lists editions not verified on the proposal date)
- Compute hardware prices are reseller listings on the BOM date; GPU server availability can move lead times
- Not included: site civil, utility service, permits, fiber circuits, customer IT software, generator fuel, insurance after set-down, spare parts beyond the turnover kit, decommissioning (quoted separately)

## 16. Signature block

By signing, the customer accepts this proposal (SAI-BEN30-20261108-B4E851A1) and the risk disclosure in section 10, and authorises Schreiber AI to start the site survey and engineering release; the site requirements form is signed separately at hold point H3.

| Role | Name | Signature | Date |
|---|---|---|---|
| Customer authorised representative, Lakeshore Foundry |  |  |  |
| Schreiber AI — sales |  |  |  |
| Schreiber AI — engineering |  |  |  |
| Schreiber AI — compliance |  |  |  |

---
*Schreiber AI — proposal SAI-BEN30-20261108-B4E851A1. Generated by ben_engine.proposal from the configuration model; numbers are not hand-edited.*