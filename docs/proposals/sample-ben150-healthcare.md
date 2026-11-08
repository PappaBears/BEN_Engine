# Schreiber AI — BEN Engine proposal SAI-BEN150-20261108-4842D366

*BEN 150 · Healthcare (HIPAA) · Acme Clinic · Austin, TX · 2026-11-08 · valid until 2027-01-07*

## 1. Cover

| Item | Value |
|---|---|
| Proposal | BEN Engine BEN 150 for Acme Clinic |
| Prepared by | Schreiber AI |
| Customer | Acme Clinic |
| Site | Austin, TX |
| Tier | BEN 150 — 20 ft high-cube ISO container |
| Mission profile | Healthcare (HIPAA) (healthcare) |
| Climate package | Hot / humid |
| Purchase option | Managed service |
| Date | 2026-11-08 |
| Valid until | 2027-01-07 (60 days) |
| Proposal ID | SAI-BEN150-20261108-4842D366 |
| Configuration | 50 kW IT in 5 rack(s), Rear-door heat exchanger + dry cooler, 2N, 10 min UPS, generator |

AI infrastructure that arrives finished. This proposal is generated from configuration version 7caf6cac; every number in it comes from the same model that produces the drawings, bill of materials, digital twin and commissioning script.

## 2. Executive summary

Acme Clinic needs 50 kW of IT capacity for a Healthcare (HIPAA) workload at Austin, TX. We propose one BEN 150: a 20 ft high-cube ISO container fitted out as a complete data center with 5 rack(s), Rear-door heat exchanger + dry cooler with 2N redundancy, a 2 x 61 kVA UPS giving 10 minutes of ride-through, a standby generator, clean-agent fire protection and the BEN Controls layer (sensors, firmware, digital twin, dashboard).

The unit arrives finished and factory-tested. It needs a pad, a 100 A 480 V 3ph feeder, fiber and a grounding electrode at the site; everything inside the enclosure is built, wired, tested and documented before it ships.

Price for the managed service option: $1,807,449 capital ($36,149 per kW IT) plus $27,000 per year (Managed service at $45/kW-month x 50 kW IT). 64 % of the underlying cost is at confirmed vendor prices, 0 % at manufacturer list price and 36 % is engineering estimate; the price is firm at engineering release, when the configuration is frozen.

Order to in-service: about 34 weeks, set by the longest-lead item (20 weeks) and the permit cycle. Risks are disclosed in section 10 before the price is accepted; the site requirements in section 11 are signed before anything is built for this site.

## 3. Mission profile and what it means

| Item | Value |
|---|---|
| Profile | Healthcare (HIPAA) (healthcare) |
| ASHRAE class | A1: 15–32 °C inlet, 20–80 % RH allowable (recommended 18–27 °C); the tightest class, for sensitive or mission-critical IT |
| Redundancy | 2N: two complete, independent cooling and UPS paths; either path alone carries the full load |
| Design rack density | 10.0 kW per rack (profile default 10 kW) |
| Climate package | Hot / humid: design outdoor 38 °C / minimum 0 °C, solar 900 W/m², corrosion class ISO 9223 C4, basic wind 58 m/s (ASCE 7) |
| Cooling derate at design day | 0.955 -> 33.4 kW per unit; 4 units installed for 2 required |
| Generator | included (profile default) |

What this means for you: the environmental class sets the alarm limits your IT will be held to; the redundancy level sets what happens when a component fails; the climate package sets the coatings, anchorage, condensation control and cooling capacity margins built into the unit. All three are fixed at engineering release and verified at the factory and site acceptance tests.

## 4. The unit: sizing

| Item | Value | Basis |
|---|---|---|
| Enclosure | 20 ft high-cube ISO container | External 6.058 x 2.438 x 2.896 m; interior 5.75 x 2.2 x 2.49 m |
| IT load | 50 kW in 5 rack(s) of 42 U | 10.0 kW per rack; tier range 50–150 kW |
| Cooling | 4 x Rear-door heat exchanger + dry cooler | 2 required at 33.4 kW each (derate 0.955), 2N |
| Row fit | fits | single row 3500 mm vs interior 5750 mm |
| Cooling electrical | 6.25 kW | COP 8.0 at design point |
| Total electrical demand | 57.8 kW / 60.8 kVA | IT + cooling + 2 % house + 0.5 kW controls, pf 0.95 |
| Controls tier | BEN Controls Pro | PLCnext AXC F 2152 + Axioline I/O in a UL 508A BEN Controller panel, OnLogic Karbon 400 edge computer (TPM 2.0); 12 BEN Pods on the BEN Mesh (Thread, Secure Vault); selectable with controls_tier (docs/CONTROLS_HARDWARE_DECISION.md 2a) |
| Service | 480 V 3ph, 100 A breaker | calculated 91 A at 80 % continuous, rounded to the next frame |
| UPS | 2 x 61 kVA | IT only with 15 % headroom, 2N |
| Battery | 9.3 kWh lithium (LFP) | 10 min at IT load, 90 % depth of discharge |
| NFPA 855 scope | no - battery below 20 kWh | energy storage threshold |
| Airflow | 2,000 cfm | 125 cfm/kW air-cooled at 12 K rise; 40 cfm/kW liquid/water |
| Envelope gain at design day | 1.29 kW | 100 mm PIR, R 3.5 m²K/W, solar on roof |
| Mass | payload 5,874 kg; gross 8,274 kg | tare 2,400 kg; crane and pad sized for the gross mass |
| PUE estimate | 1.185 | design-point calculation incl. 0.03 UPS loss; measured at SAT |

## 5. Scope of supply

| Module | Status | BOM lines | Sell price |
|---|---|---|---|
| Power module | included | 16 lines | $271,134 |
| Cooling module | included | 5 lines | $272,472 |
| Compute module | included | 5 lines | $1,072,379 |
| Controls module | included | 29 lines | $22,903 |
| Structure (container / cabinet) | included | 12 lines | $36,521 |
| Envelope (insulation, liner, coatings) | included | 12 lines | $9,035 |
| Fire detection and suppression | included | 7 lines | $38,339 |
| Site kit (anchors, embeds, signage) | included | 9 lines | $34,028 |
| Build labour, FAT, logistics | included | 8 lines | $50,639 |

Top 15 lines of the 103-line bill of materials for this option (sell price at 28% gross margin; the full priced BOM with vendors, part numbers and price confirmation dates is delivered at engineering release):

| Code | Item | Manufacturer / MPN | Qty | Sell price | Price basis | Lead (wk) |
|---|---|---|---|---|---|---|
| CMP-GPU-L40S | GPU SuperServer 4U, 2x Xeon, 8x NVIDIA L40S (~4 kW), configured | Supermicro SYS-421GE-TNRT | 8 ea | $914,767 | confirmed | 6 |
| CLG-RDHX | Active rear-door heat exchanger, 42/48U, up to 40 kW | nVent Schroff / ColdLogik / Motivair RackChiller RDC active | 5 ea | $125,000 | estimate | 12 |
| CLG-CDU-RDHX | Row CDU 70-100 kW liquid-to-liquid for RDHx loop | Vertiv / CoolIT XDU070 / CHx80 | 2 ea | $125,000 | estimate | 14 |
| CMP-CPU | PowerEdge R760 2U rack server (management / storage node) | Dell Technologies R760 | 5 ea | $124,993 | confirmed | 3 |
| PWR-GEN-150 | SD150 150 kW diesel standby generator, L2 enclosure, sub-base tank | Generac Industrial SD0150 | 1 ea | $104,167 | estimate | 20 |
| PWR-UPS-GVS150 | Galaxy VS UPS 150 kW 480 V single frame, N+1 internal power modules, internal lithium battery modules up to 20 kWh (BEN 150) or external cabinets (BEN 500) | Schneider Electric GVSUPS150KHS (configure-to-order) | 1 ea | $94,444 | estimate | 14 |
| CMP-SW100G | Spectrum SN2700 32x100GbE QSFP28 switch, Cumulus Linux | NVIDIA Mellanox MSN2700-CS2RC | 2 ea | $29,425 | confirmed | 2 |
| PWR-XFMR | Dry-type step-down transformer 480 D - 208Y/120 V, 150 kVA (ben150) / 300 kVA (ben500), for rack PDUs | Square D / Eaton EX150T3H / EX300T3H | 2 ea | $26,389 | estimate | 8 |
| FS-CLEAN-AGENT | Pre-engineered FK-5-1-12 (Novec 1230) clean agent system, installed: cylinder, nozzles, releasing panel, detection, design & AHJ submittal | Fike / Kidde (via licensed fire contractor) ECS-500 / Fike CA | 34 m3 protected | $25,972 | estimate | 8 |
| STR-RACK42 | NetShelter SX 42U 600x1070 mm enclosure with sides | APC by Schneider Electric AR3100 | 5 ea | $16,111 | confirmed | 1 |
| PWR-PDU | NetShelter metered rack PDU 0U 5.0 kW 208 V 30 A, L6-30P, (36) C13 (6) C19 | APC by Schneider Electric AP8841 | 10 ea | $15,555 | confirmed | 1 |
| PWR-ATS-400 | Series 300 ATS 400 A 3P 480 V, service-entrance rated, NEMA 4X / IP66 | ASCO (Schneider) J03ATSB30400N5X | 1 ea | $15,361 | confirmed | 8 |
| SVC-ELECTRICIAN | Licensed electrician (commercial journeyman, billed) | local electrical contractor ELEC-HR | 90 h | $13,750 | estimate | 1 |
| CLG-PIPING | Glycol loop piping, valves, pumps skid, expansion tank, strainers (per m container length) | Victaulic / Grundfos FCW-LOOP | 7 per m | $11,667 | estimate | 6 |
| FS-VESDA | VESDA-E VEU aspirating smoke detector, UL | Xtralis (Honeywell) VEU-A00-UL | 1 ea | $9,381 | confirmed | 4 |

Explicitly excluded:

- Site civil works: pad, piers, anchors set in concrete, drainage, fencing, lighting, equipment yard (PE-stamped drawings are supplied by us)
- Utility service: feeder from the customer's switchgear to the disconnect at the unit, utility fees, metering, interconnection
- Permits and fees pulled by the customer (zoning, building, utility, generator air permit); we supply the engineering documents
- Fiber / ISP circuits, customer network equipment above the controls LAN, customer software licences
- Taxes, duties, freight insurance beyond the quoted domestic delivery, crane standby beyond one day

## 6. Price

| Option | Capital price | Per kW IT | Recurring / year | Term | Total over term | Confirmed / list / estimate | BOM lines | Status |
|---|---|---|---|---|---|---|---|---|
| Hardware only | $1,784,546 | $35,691 | - | 1 yr | $1,784,546 | 64 / 0 / 36 % | 74 | alternative |
| Hardware + BEN Controls | $1,807,449 | $36,149 | $12,000 | 1 yr | $1,819,449 | 64 / 0 / 36 % | 103 | alternative |
| White-label | $1,807,449 | $36,149 | $15,000 | 1 yr | $1,822,449 | 64 / 0 / 36 % | 103 | alternative |
| Managed service | $1,807,449 | $36,149 | $27,000 | 3 yr | $1,888,449 | 64 / 0 / 36 % | 103 | PROPOSED |

Confirmed = price seen on a vendor or distributor listing on the date in the BOM; list = manufacturer published price; estimate = engineering estimate with its basis stated in the BOM note. Capital prices carry a 28% gross margin on purchased hardware and build labour. Recurring items: Hardware + BEN Controls: BEN Controls licence (dashboard, twin, firmware updates, remote support hooks); White-label: White-label licence under the Schreiber AI brand (controls licence x 1.25, partner branding, source escrow); Managed service: Managed service at $45/kW-month x 50 kW IT (includes the BEN Controls licence, remote operations and the maintenance schedule).

| Managed service term | Capital | Service fees | Total |
|---|---|---|---|
| 1 year | $1,807,449 | $27,000 | $1,834,449 |
| 3 years | $1,807,449 | $81,000 | $1,888,449 |
| 5 years | $1,807,449 | $135,000 | $1,942,449 |

Payment milestones for the proposed option (Managed service, capital $1,807,449):

| Milestone | Share | Amount | Week from order |
|---|---|---|---|
| Engineering release (H4) | 30 % | $542,235 | 6 |
| Factory acceptance test (H13) | 40 % | $722,980 | 30 |
| Site acceptance test (H19) | 25 % | $451,862 | 33 |
| Turnover (W20) | 5 % | $90,372 | 34 |

Recurring fees are invoiced annually in advance from turnover. Prices are in USD, exclude taxes, and are valid to the date on the cover; the capital price becomes firm at engineering release.

## 7. Schedule

Milestones in weeks from order, derived from the stage durations in docs/PROCESS_FLOW.md for the BEN 150 (reference order-to-service about 27 weeks) and the longest lead time in this bill of materials (20 weeks). Critical path: engineering release -> long-lead procurement -> fit-out -> FAT -> SAT. Site civil and permits run in parallel.

| Week | Milestone | Owner | Hold / witness point | Path |
|---|---|---|---|---|
| 0 | Order and risk acknowledgement signed | Customer + Schreiber AI | - | critical |
| 3 | Site survey and site requirements sign-off | Customer + ENG | H3 | critical |
| 6 | Engineering release: configuration frozen, IFC drawings, BOM; long-lead purchase orders placed | ENG | H4 | critical |
| 9 | Container / cabinet received and inspected; structural and envelope work starts | FAC | W6, H7, W8 | critical |
| 14 | Permits issued (building, electrical, mechanical, fire plan review) | Customer / AHJ | - | parallel |
| 20 | Site pad, grounding and utility feeder complete and surveyed | Customer civil | H16 | parallel |
| 26 | Longest-lead item on the floor (20 weeks from release); mechanical and electrical fit-out complete | FAC + SUB | H10 | critical |
| 30 | Cooling, controls and firmware complete; factory acceptance test incl. 24 h burn-in | FAC + ENG; customer witness | H11, W12, H13 | critical |
| 31 | Transport prep and shipping | LOG | - | critical |
| 32 | Set-down, hook-up and pre-energisation check | LOG + SUB + AHJ | W17, H18 | critical |
| 33 | Site acceptance test and fire marshal acceptance | ENG + customer + AHJ | H19 | critical |
| 34 | Training and turnover; unit in service | ENG + customer | W20 | critical |

Long-lead items (ordered at engineering release):

| Code | Item | Vendor | Qty | Lead time (weeks) |
|---|---|---|---|---|
| PWR-GEN-150 | SD150 150 kW diesel standby generator, L2 enclosure, sub-base tank | Generac industrial dealer | 1 ea | 20 |
| CLG-CDU-RDHX | Row CDU 70-100 kW liquid-to-liquid for RDHx loop | Vertiv / CoolIT sales | 2 ea | 14 |
| PWR-UPS-GVS150 | Galaxy VS UPS 150 kW 480 V single frame, N+1 internal power modules, internal lithium battery modules up to 20 kWh (BEN 150) or external cabinets (BEN 500) | AVENDOR | 1 ea | 14 |
| CLG-DRYCOOLER | Outdoor dry cooler (V-type, EC fans), adiabatic-ready, glycol | Guntner / Alfa Laval rep | 58 kW | 14 |
| CLG-RDHX | Active rear-door heat exchanger, 42/48U, up to 40 kW | nVent / Legrand distributor | 5 ea | 12 |

## 8. Drawings and documents delivered

Issue-for-construction drawing set for the BEN 150, regenerated from the frozen configuration at engineering release and re-issued as built after SAT. ISSUE FOR CONSTRUCTION Rev A — Drawn: BEN Engine generator; Checked: blank (requires a checker before release).

| Sheet | Title | Scale |
|---|---|---|
| A-001 | General arrangement (sheet 1/7) | see sheet |
| A-002 | Interior layout plan (sheet 2/7) | see sheet |
| A-003 | Envelope section (sheet 3/7) | 1:10 / 1:2 |
| S-001 | Floor framing and anchoring (sheet 4/7) | see sheet / 1:5 |
| E-001 | Power one-line (sheet 5/7) | NTS |
| M-001 | Cooling P&ID (sheet 6/7) | NTS |
| C-001 | Controls layout (sheet 7/7) | see sheet |

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
| Profile | healthcare (A1, 2N, generator) |
| ASHRAE class / redundancy (from config) | A1 / 2N |
| Emphasis | HIPAA |
| Standards emphasised | HIPAA physical safeguards; NFPA 99 and NFPA 110 only if the AHJ deems the load essential (then Art. 700/701); 2N coordination |
| Extra documents in the pack | BAA template; facility security plan; 2N single-line; emergency power classification letter |
| Typical AHJ / third-party questions | Whether the load is "essential electrical system" |

Climate add-ons:

| Item | Value |
|---|---|
| Climate | hot_humid |
| Config values | 38 °C / 0 °C, C4, 58 m/s |
| Compliance / design add-ons | Condensation control: vapour barrier on warm side of PIR, dew-point alarm, door-sweep heaters; corrosion C4 coating (ISO 12944 C4-H system); wind 58 m/s (130 mph) anchorage; hurricane-rated louvres and door tie-backs; IEEE/FEMA flood elevation |
| Verification | Coating DFT inspection; anchor calc |

Baseline matrix lines that apply to every unit:

| Code / standard | Design feature | Verification |
|---|---|---|
| NFPA 70 (NEC) | Listed dead-front gear, SCCR 65 kA, selective coordination, arc-flash labels | Electrical inspection H10, AHJ at H18 |
| NFPA 75 / 2001 / 72 | Non-combustible liner, VEWFD, clean agent with 10-min hold, EPO, HVAC shutdown | Door-fan test, NFPA 72 record of completion at SAT |
| UL 508A | BEN Controller panel (PLCnext PLC, I/O, edge computer) built and labelled by a UL 508A shop | Panel label and schedule (CTQ-K6) |
| ASHRAE TC 9.9 | Class A1 alarm limits in the controls | Load step test E3/E7 at FAT and SAT |
| AIM Act / EPA 608 | GWP < 700 A1 refrigerant or water loops; certified technicians | Charge record per circuit |
| ISO 668 / 1496 / CSC | One-trip high-cube container, PE-checked modifications, CSC decision at transport | Weld inspection H7, weigh ticket |
| NFPA 110 / NFPA 37 / 30 | Standby generator with ATS, fuel system, exhaust setbacks | Installation acceptance test, load bank |

## 10. Risks disclosed up front

These are the risks that apply to the healthcare (hipaa) profile, from the product risk register (docs/RISK_REGISTER.md, web/assets/risks.json). Each line says what the design covers and what remains the customer's decision or duty. Please read them before accepting the price.

| ID | Risk | Severity | What can happen | Covered by the design | Customer owns |
|---|---|---|---|---|---|
| R01 | Utility power loss | high | The grid fails for seconds to days. IT shuts down when the battery runs out and cooling stops at once unless it is on UPS or generator. | UPS ride-through (default 10 min), generator option with ATS, measured cooling ride-through (test E5), N+1/2N per profile. | Whether to buy the generator and fuel, the utility contract, and whether cooling is put on UPS. |
| R15 | Permit delay or unexpected AHJ requirement | high | The local authority may classify the container as a building, ask for a field evaluation or more fire protection, and take longer than the build. | Pre-application package, code summary, field-evaluation budget line, site requirements signed before build, parallel permit path in the schedule. | Pulling permits (or authorising us), zoning, neighbour relations. |
| R18 | Long-lead parts slip | high | UPS, switchgear, cooling units and transformers can take months and slip. | Long-lead orders at engineering release, approved alternates, stocked controls hardware. | Early deposit and configuration freeze; no late changes. |
| R02 | Arc flash or electrical fault | medium | A fault while a panel is open or a component failure can injure someone and damage equipment. | Arc-flash study and labels, selective coordination, listed dead-front gear, lockout points, NFPA 70E training at turnover. | Only qualified electricians work on it and the labels are followed. |
| R06 | Fire inside the container | medium | A cable, battery or power supply fire would mean loss of IT, an agent discharge and downtime. | Very-early smoke detection, clean agent with 10-minute hold, HVAC shutdown, EPO, non-combustible liner, battery separation. | Fire marshal relationship, agent recharge contract, no combustible storage inside, insurance. |
| R07 | Lithium battery thermal runaway | medium | A battery cell failure can release flammable gas and start a fire that spreads if not contained. | LFP chemistry, UL 1973/9540 listed cabinets with UL 9540A data, BMS alarms, gas detection and venting above 20 kWh, capped battery size on smaller tiers. | No unapproved batteries, keep BMS firmware updated, respond to BMS alarms. |
| R11 | Intrusion into the controls network | medium | An attacker who reaches the controls LAN could change setpoints or stop cooling. | IEC 62443 zones, isolated controls LAN, signed firmware, no inbound ports, outbound-only remote support that can be disabled, hardwired life safety. | The firewall between BEN controls and the customer LAN (unless managed), password handover, patch windows. |
| R14 | Sensor drift gives false comfort | medium | A drifted sensor can make the dashboard look fine while the room is not. | Redundant sensors, idle cross-check (test E1), drift detection, 12-month or trigger-based recalibration. | Allow calibration visits, do not move sensors. |
| R20 | Site costs above quote | medium | Civil works, permits and utility connection can cost more than the allowance. | Firm box price after engineering release; site works quoted after survey; utility costs identified at survey. | Utility fees, civil works, permits, taxes, and changes after freeze. |
| R03 | Site fault current differs from assumption | low | Until the utility gives its fault current and voltage, arc-flash labels and some ratings are provisional. | Labels marked provisional until SAT; study updated with utility data; panel SCCR at least 65 kA. | Provide utility fault current and voltage before the unit ships. |
| R09 | Transport or lifting damage | low | A bad lift or rough transport can twist the frame or crack a weld. | Corner-casting lifts with spreader, PE-checked frame, shock loggers, set-down inspection, freight insurance. | Crane access, competent rigger, route survey for the high-cube height. |
| R19 | Component discontinued or listing changes | low | A specified part may be discontinued or lose its listing before or after build. | Approved alternates in the BOM, configuration freeze per unit, FAT repeats affected tests. | None. |
| R22 | Fuel or glycol spill | low | A generator tank or coolant loop leak to ground brings clean-up cost and fines. | Double-wall UL 142 tank, overfill alarm, SPCC plan where required, propylene glycol, drip trays. | Fuel deliveries, SPCC plan ownership, stormwater rules. |
| R23 | Person inside during agent discharge or refrigerant leak | low | Clean agent or a refrigerant leak can disorient or expose a technician inside. | Pre-discharge alarm with delay, abort switch, door interlock, refrigerant detector, purge ventilation, written entry procedure, non-flammable refrigerants. | Follow the entry procedure, keep training current. |
| R25 | No Uptime Tier certification is claimed | low | We design with TIA-942 Rated-2/3 concepts but do not hold a Tier certificate; an insurer or auditor may ask. | Design-basis statement, FAT/SAT evidence, optional third-party audit at cost. | Deciding if a certification is required and paying for it. |

## 11. Site requirements summary

The full form (docs/SITE_REQUIREMENTS.md) is signed by the customer and by us at hold point H3 before anything is built for this site. Summary for this unit:

| Item | Value |
|---|---|
| Pad plan size | 8.0 × 4.5 m + condenser/dry cooler yard 6 × 3 m |
| Pad type | 200 mm slab or 4 piers (6 piers if mid-anchors required by wind calc) |
| Anchor points | 4 (+2 mid) twist-lock bases / weld plates |
| Gross mass to set | 8,274 kg (crane sized for this mass at the required radius) |
| Utility service | 480Y/277 V, 3φ, 4-wire + ground; customer disconnect rated 100 A for this configuration (tier range: 225 A (default) to 400 A (max)) |
| Feeder conductors (customer side) | 4/0 AWG (225 A) / 600 kcmil or 2 × 3/0 (400 A) |
| Fault current | utility available fault current and voltage required before shipping; unit SCCR 65 kA |
| Generator | 150–250 kW diesel/natural gas, customer gas service or diesel tank |
| Grounding electrode | Ground ring (≥ 6 m of 2 AWG bare copper, 750 mm deep around the pad) or two 3 m rods ≥ 1.8 m apart, bonded to the building electrode system if one exists (NEC 250.50) |
| Ground resistance | ≤ 25 Ω code minimum; ≤ 5 Ω recommended for IT and lightning performance; tested by fall-of-potential before set-down (H16) |
| Fiber conduit | Two 50 mm conduits (one spare) from the customer's demarcation to the unit's communications entry plate, with pull strings, sealed against water and rodents |
| Fiber service | Customer orders the circuit(s); single-mode fiber preferred; diverse routes for 2N profiles. Lead time 60–120 days — order at H3 |
| Clearances | 2.5 m clear on the door side; >= 1.5 m at condensers / dry cooler with no recirculation; >= 3 m to other structures; fire lane on one long side |
| Climate inputs the customer confirms | flood zone and base flood elevation, site wind speed and exposure, ground snow load, seismic category, altitude, corrosivity |

Permits and who pulls them:

| Permit | Typical need | Who pulls |
|---|---|---|
| Zoning / land use | Yes for 30/150/500 (accessory structure); often no for BEN 5 | Customer |
| Building permit (structure, foundation, anchorage) | Yes for 30/150/500 | Customer's contractor or Schreiber AI as agent (we provide PE drawings) |
| Electrical permit | Yes | Licensed electrical sub (ours for the unit, customer's for the feeder) |
| Mechanical / refrigeration permit | Yes where DX or glycol piping is installed on site | Licensed HVAC sub |
| Fire alarm / suppression permit and plan review | Yes for 30/150/500 | Licensed fire protection contractor |
| Generator: air permit / registration, fuel tank permit | If generator selected | Customer (we provide engine certification and tank data) |
| Utility interconnection (solar/export only) | off_grid with PV paralleling | Customer with our documents |
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

Pass criteria specific to this configuration: rack inlets within ASHRAE A1 at 50 kW; 2N failover with no inlet excursion; UPS ride-through >= 10 minutes at IT load; meter vs PDU reconciliation within 3 %; PUE at full load reported against the 1.185 estimate. Deviations are closed or accepted in writing before the milestone is invoiced.

## 13. Warranty, maintenance and support

| Item | Value |
|---|---|
| Workmanship warranty | 24 months from SAT on the integration, wiring, piping, envelope and controls build |
| Equipment warranty | Vendor warranties (UPS, cooling, CDU, batteries, fire panel, generator, servers) registered in the customer's name at turnover and passed through; minimum 12 months, longer where the vendor offers it |
| Controls software | Signed Pod firmware, PLC project and edge computer updates for the licence term; security fixes for the life of the licence |
| Support level in this option | 24 x 7 remote monitoring by Schreiber AI operations, weekly remote checks, scheduled local and subcontractor visits per the maintenance schedule, alarm response and monthly report; the maintenance schedule below is included |

Maintenance schedule (docs/MAINTENANCE.md; intervals for temperate climate, climate add-ons shorten some intervals; task counts per interval):

| Interval | Who | Tasks |
|---|---|---|
| Weekly (remote, 15 minutes) — R | Remote, Schreiber AI operations (R) | 9 |
| Monthly — L (1–2 hours on site) with R review | Local technician (L) with remote review | 8 |
| Quarterly — L + S | Local technician + certified subcontractor (L + S) | 6 |
| Semi-annual | Certified subcontractor (S) with record; remote (R) for controls | 4 |
| Annual | Certified subcontractor (S) with record; remote (R) for controls | 9 |
| 3-year | Certified subcontractor (S) with record; remote (R) for controls | 4 |
| 5-year | Certified subcontractor (S) with record; remote (R) for controls | 6 |

Sensor calibration every 12 months (or on drift trigger) with GUM uncertainty budgets; a spare parts kit per unit is delivered at turnover (MAINTENANCE.md section 7). Climate add-ons for this unit: dew-point and condensation check monthly, coating inspection annually (C4).

## 14. Commercial terms summary

The governing documents are the Master Services Agreement (docs/contracts/MSA.md), the Statement of Work for this unit (docs/contracts/SOW_TEMPLATE.md, pre-filled from this proposal), the change order form (docs/contracts/CHANGE_ORDER.md), the acceptance certificates, and for the controls layer the software licence (docs/contracts/SOFTWARE_LICENCE.md) and, for the managed option, the service level agreement (docs/contracts/SLA.md). This section summarises them; the contracts prevail.

| Term | Summary |
|---|---|
| Payment | 30 % at Engineering release / 40 % at Factory acceptance test / 25 % at Site acceptance test / 5 % at Turnover; net 30 from invoice; recurring fees annually in advance |
| Price validity | 60 days from the proposal date; capital price firm at engineering release (configuration frozen, hold point H4) |
| Scope changes | Every change after engineering release is a change order; each change order carries its price impact and its schedule impact and is signed before the work is done |
| Customer-caused delay | A delay caused by the customer or its contractors (site not ready, permits, utility, late information or approvals) extends the schedule day for day and suspends Schreiber AI's liquidated-damages exposure for that period |
| Delivery liquidated damages | 0.5 % of the capital price per week of Schreiber AI-caused delay to FAT, capped at 5.0 %; sole remedy for delay |
| Storage of a finished unit | If the unit passes FAT and cannot ship because the site, permits or utility are not ready, storage and preservation are charged at $300 per day after 14 days, and the FAT milestone is payable |
| Supplier and contract-manufacturer delay | Delivery liquidated damages in our supplier purchase orders and contract-manufacturing agreements flow back-to-back with the customer terms, so a late UPS or switchgear supplier bears its share of any delay damages |
| Title and risk | Title passes at payment of the FAT milestone; risk of loss passes at set-down; freight insured to full replacement value |
| Warranty | 24 months workmanship; vendor warranties passed through (section 13) |
| Acceptance | FAT and SAT by the commissioning script; deviations closed or accepted in writing; acceptance deemed 10 business days after a passing SAT report if not signed |
| Data and software | Customer owns its data; controls software is licensed, not sold; firmware is signed; no cloud dependency |
| Governing law | [GOVERNING_STATE] (set in the MSA) |

## 15. Assumptions and what is not included

- Configuration as on the cover: 50 kW IT, 5 rack(s), Rear-door heat exchanger + dry cooler, 2N, climate Hot / humid; any change is priced as a change order
- Prices from purchasing/parts_catalog.json priced on the dates in the BOM; 64 % confirmed, 0 % list, 36 % estimate for this option; the estimate share is re-priced at engineering release
- Gross margin 28% on hardware and build labour; controls licence $12,000/yr for this tier; white-label uplift x1.25; managed service $45/kW-month
- Domestic delivery within one day's haul of the integration shop; export, over-dimension permits beyond the carrier's standard, and crane standby beyond one day are extra
- Utility fault current <= 65 kA and voltage within +/-10 % at the disconnect; otherwise current-limiting fuses are added by change order
- Soil bearing >= 100 kPa; otherwise a geotechnical report and revised foundation are the customer's cost
- Permit fees, utility fees, taxes and duties are excluded; AHJ edition of each code applies (docs/COMPLIANCE.md section 13 lists editions not verified on the proposal date)
- Compute hardware prices are reseller listings on the BOM date; GPU server availability can move lead times
- Not included: site civil, utility service, permits, fiber circuits, customer IT software, generator fuel, insurance after set-down, spare parts beyond the turnover kit, decommissioning (quoted separately)

## 16. Signature block

By signing, the customer accepts this proposal (SAI-BEN150-20261108-4842D366) and the risk disclosure in section 10, and authorises Schreiber AI to start the site survey and engineering release; the site requirements form is signed separately at hold point H3.

| Role | Name | Signature | Date |
|---|---|---|---|
| Customer authorised representative, Acme Clinic |  |  |  |
| Schreiber AI — sales |  |  |  |
| Schreiber AI — engineering |  |  |  |
| Schreiber AI — compliance |  |  |  |

---
*Schreiber AI — proposal SAI-BEN150-20261108-4842D366. Generated by ben_engine.proposal from the configuration model; numbers are not hand-edited.*