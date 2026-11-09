# Schreiber AI — BEN Engine proposal SAI-BEN1-20261109-ADA95012

*BEN 1 · AI inference edge · Harbor Street Accounting · Portland, ME · 2026-11-09 · valid until 2027-01-08*

## 1. Cover

| Item | Value |
|---|---|
| Proposal | BEN Engine BEN 1 for Harbor Street Accounting |
| Prepared by | Schreiber AI |
| Customer | Harbor Street Accounting |
| Site | Portland, ME |
| Tier | BEN 1 — 10-inch 8U desk / shelf mini rack (open or semi-enclosed) (DeskPi RackMate T1 (10-inch 8U) class) |
| Mission profile | AI inference edge (ai_inference) |
| Climate package | Temperate |
| Purchase option | Hardware + BEN Controls |
| Date | 2026-11-09 |
| Valid until | 2027-01-08 (60 days) |
| Proposal ID | SAI-BEN1-20261109-ADA95012 |
| Configuration | 1 kW IT in 1 rack(s), Office air: filtered, sound-damped extraction path (no refrigerant), N, 10 min UPS |

AI infrastructure that arrives finished. This proposal is generated from configuration version a70260a2; every number in it comes from the same model that produces the drawings, bill of materials, digital twin and commissioning script.

## 2. Executive summary

Harbor Street Accounting needs 1 kW of IT capacity for a AI inference edge workload at Portland, ME. We propose one BEN 1: a 10-inch 8U desk / shelf mini rack (open or semi-enclosed) (DeskPi RackMate T1 (10-inch 8U) class) fitted out as a complete data center with 1 rack(s), Office air: filtered, sound-damped extraction path (no refrigerant) with N redundancy, a 1 x 1.0 kVA UPS giving 10 minutes of ride-through, clean-agent fire protection and the BEN Controls layer (sensors, firmware, digital twin, dashboard).

BEN 1 arrives assembled and burnt in by Schreiber AI. It needs a NEMA 5-15R on a dedicated 15 A, 120 V circuit (12 A continuous at 80 %), a network port and a room that can take 649 W (2,213 BTU/h) of heat; estimated noise 45.2 dBA at 1 m (target 50).

Price for the hardware + ben controls option: $19,746 capital ($32,910 per kW IT) plus $480 per year (BEN Controls licence). 9 % of the underlying cost is at confirmed vendor prices, 66 % at manufacturer list price and 25 % is engineering estimate; the price is firm at engineering release, when the configuration is frozen.

Order to in-service: about 3 weeks: Schreiber AI assembles BEN 1 from stock kits, burns it in, ships it and sets it up (compute bought by us can add its own lead time, see section 7). No permits are needed for a plug-in unit; risks are disclosed in section 10.

## 3. Mission profile and what it means

| Item | Value |
|---|---|
| Profile | AI inference edge (ai_inference) |
| ASHRAE class | A2: 10–35 °C inlet allowable; standard enterprise IT |
| Redundancy | N: no redundant cooling or UPS module; a failure of one unit means a planned shutdown (accepted for this profile by the customer's recovery-time decision) |
| Design rack density | 0.6 kW per rack (profile default 20 kW) |
| Climate package | Temperate: design outdoor 35 °C / minimum -15 °C, solar 800 W/m², corrosion class ISO 9223 C3, basic wind 47 m/s (ASCE 7) |
| Cooling derate at design day | 1.000 -> 1.6 kW per unit; 1 units installed for 1 required |
| Generator | not included (option) |

What this means for you: the environmental class sets the alarm limits your IT will be held to; the redundancy level sets what happens when a component fails; the climate package sets the coatings, anchorage, condensation control and cooling capacity margins built into the unit. All three are fixed at engineering release and verified at the factory and site acceptance tests.

## 4. The unit: sizing

| Item | Value | Basis |
|---|---|---|
| Enclosure | 10-inch 8U desk / shelf mini rack (open or semi-enclosed) (DeskPi RackMate T1 (10-inch 8U) class) | External 0.281 x 0.26 x 0.451 m; interior 0.222 x 0.2 x 0.356 m |
| IT load | 1 kW in 1 rack(s) of 8 U | 0.6 kW per rack; tier range 0.2–1.5 kW |
| Cooling | 1 x Office air: filtered, sound-damped extraction path (no refrigerant) | 1 required at 1.6 kW each (derate 1.0), N |
| Row fit | fits | 1 row(s) of 1 racks, 281 mm per row vs interior 222 mm |
| Cooling electrical | 0.015 kW | COP 40.0 at design point |
| Total electrical demand | 0.649 kW / 0.683 kVA | IT + cooling + 2 % house + 0.5 kW controls, pf 0.95 |
| Controls tier | BEN Controls Mini | Revolution Pi RevPi Connect 4 + DIO/AIO (DIN rail, listed), software interlocks behind a hardware watchdog relay; 2 BEN Pods on the BEN Mesh (Thread, Secure Vault); selectable with controls_tier (docs/CONTROLS_HARDWARE_DECISION.md 2a) |
| Service | 120 V 1ph 15/20 A plug-in, 15 A breaker | calculated 7 A at 80 % continuous, rounded to the next frame |
| Generator | not included (option) | total demand x 1.25, rounded to 10 kW |
| Hardening | Indoor (no hardening levels): UL 62368-1 listed parts, IP20 indoor, NEMA 12 option for dusty closets | coating powder coat, indoor; recommended for this profile/climate: IND; envelope 0.56 m² |
| UPS | 1 x 1.0 kVA | IT only with 15 % headroom, N |
| Battery | 0.111 kWh lithium (LFP) | 10 min at IT load, 90 % depth of discharge |
| NFPA 855 scope | no - battery below 20 kWh | energy storage threshold |
| Airflow | 107 cfm | 125 cfm/kW air-cooled at 12 K rise; 40 cfm/kW liquid/water |
| Envelope gain at design day | 0.0 kW | 100 mm PIR, R 3.5 m²K/W, solar on roof |
| Mass | payload 34 kg; gross 38 kg | tare 4 kg; crane and pad sized for the gross mass |
| PUE estimate | 1.081 | design-point calculation incl. 0.03 UPS loss; measured at SAT |

## 5. Scope of supply

| Module | Status | BOM lines | Sell price |
|---|---|---|---|
| Power module | included | 2 lines | $2,311 |
| Cooling module | not in this option | - | - |
| Compute module | included | 3 lines | $13,700 |
| Controls module | included | 6 lines | $1,929 |
| Structure (container / cabinet) | included | 2 lines | $271 |
| Envelope (insulation, liner, coatings) | included | 1 lines | $49 |
| Site kit (anchors, embeds, signage) | included | 1 lines | $167 |
| Build labour, FAT, logistics | included | 2 lines | $1,319 |

Top 15 lines of the 17-line bill of materials for this option (sell price at 28% gross margin; the full priced BOM with vendors, part numbers and price confirmation dates is delivered at engineering release):

| Code | Item | Manufacturer / MPN | Qty | Sell price | Price basis | Lead (wk) |
|---|---|---|---|---|---|---|
| CMP-AI-DGXSPARK | Desktop AI computer NVIDIA DGX Spark (GB10 Grace Blackwell, 128 GB unified memory, 240 W supply) — customer-selectable | NVIDIA DGX Spark | 2 ea | $13,053 | list | 4 |
| PWR-UPS-MINI-1000 | Smart-UPS Li-ion short depth 1000 VA / 800 W 120 V, 2U rack/tower, line-interactive, SmartConnect (NEMA 5-15P) | APC by Schneider Electric SMTL1000RM2UC | 1 ea | $2,153 | estimate | 2 |
| CTL-EDGE-MINI | Fanless edge computer for the BEN Care agent (OnLogic BlastShield CL210, dual LAN) — omit when BEN Care runs on the customer's own box | OnLogic CL210 (BlastShield) | 1 ea | $1,285 | confirmed | 3 |
| SVC-MINI-ASSEMBLY | Schreiber AI assembly, imaging, 24 h burn-in and test of BEN 1 (hours) | Schreiber AI SVC-MINI | 6 h | $792 | estimate | 1 |
| SVC-MINI-SETUP | Setup and handover at the customer (or remote): placement, outlet check, network, BEN Care enrolment, room-heat check (hours) | Schreiber AI SVC-MINI-SETUP | 4 h | $528 | estimate | 1 |
| CMP-NAS-DS224 | Synology DiskStation DS224+ 2-bay desktop NAS beside the 10-inch rack (diskless) — customer-selectable | Synology DS224+ | 1 ea | $458 | estimate | 2 |
| CTL-POD | BEN Pod v1 assembled and provisioned (MGM240P Thread module w/ Secure Vault High, 4x Pt1000 3-wire 24-bit front end, SHT45, 2x dry contact, leak-rope input, 2x isolated 4-20 mA; Pod E adds Ethernet/PoE PD, RS-485, 2x relay) - make item, per unit | Schreiber AI (contract electronics manufacturer) BEN-POD-v1 | 2 ea | $244 | estimate | 8 |
| CMP-SW-MINI | UniFi Switch Lite 8 PoE, 8 x GbE, 4 x PoE+ (52 W), managed | Ubiquiti USW-Lite-8-PoE | 1 ea | $189 | confirmed | 1 |
| CTL-LABELS | Label printer cartridges, cable labels, engraved phenolic tags (lot) | Brady / Brother M211 + B-427 | 1 lot | $167 | estimate | 1 |
| SITE-MINI-PARCEL | Parcel freight, insured, BEN 1 10-inch rack | Carrier PARCEL | 1 ea | $167 | estimate | 1 |
| STR-MINIRACK-10 | 10-inch 8U desk / shelf mini rack, aluminium + acrylic (DeskPi RackMate T1), 281 W x 200 D x 451 H mm | DeskPi (GeeekPi) RackMate T1 | 1 ea | $167 | confirmed | 2 |
| PWR-PDU-10IN | 10-inch 1U PDU, 4 x NEMA 5-15R, 15 A, surge protected | Generic 10-inch 10IN-1U-4OUT | 1 ea | $158 | estimate | 2 |
| CTL-CAT6A | Cat6A UTP patch cable 10 ft | Fiber Cables Direct C6A-UTP-10 | 10 ea | $135 | confirmed | 1 |
| STR-MINI-SHELF10 | 10-inch 2U vented shelf (one desktop AI box or mini PC per shelf) | DeskPi (GeeekPi) 10in-2U-shelf | 3 ea | $104 | estimate | 2 |
| CTL-RCP | xG24-EK2703A Explorer Kit (EFR32MG24/MGM240P) as OpenThread Border Router radio co-processor on USB; 2 for redundancy on BEN 150/500 | Silicon Labs XG24-EK2703A | 1 ea | $54 | list | 1 |

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
| Hardware only | $17,817 | $29,694 | - | 1 yr | $17,817 | 2 / 73 / 25 % | 11 | alternative |
| Hardware + BEN Controls | $19,746 | $32,910 | $480 | 1 yr | $20,226 | 9 / 66 / 25 % | 17 | PROPOSED |
| White-label | $19,746 | $32,910 | $600 | 1 yr | $20,346 | 9 / 66 / 25 % | 17 | alternative |
| Managed service | $19,746 | $32,910 | $324 | 3 yr | $20,718 | 9 / 66 / 25 % | 17 | alternative |

Confirmed listing (shown as 'confirmed') = a price seen on the vendor's or distributor's own product page on the date in the BOM, read from a search-result snippet, not a quote, re-verified before purchase order; list = manufacturer published price; estimate = engineering estimate with its basis stated in the BOM note. Capital prices carry a 28% gross margin on purchased hardware and build labour. Recurring items: Hardware + BEN Controls: BEN Controls licence (dashboard, twin, firmware updates, remote support hooks); White-label: White-label licence under the Schreiber AI brand (controls licence x 1.25, partner branding, source escrow); Managed service: Managed service at $45/kW-month x 1 kW IT (includes the BEN Controls licence, remote operations and the maintenance schedule).

| Managed service term | Capital | Service fees | Total |
|---|---|---|---|
| 1 year | $19,746 | $324 | $20,070 |
| 3 years | $19,746 | $972 | $20,718 |
| 5 years | $19,746 | $1,620 | $21,366 |

Payment milestones for the proposed option (Hardware + BEN Controls, capital $19,746):

| Milestone | Share | Amount | Week from order |
|---|---|---|---|
| Order confirmation (H4) | 50 % | $9,873 | 0 |
| Bench test passed and shipped (H13) | 40 % | $7,898 | 2 |
| Setup and handover (H19) | 10 % | $1,975 | 3 |

Recurring fees are invoiced annually in advance from turnover. Prices are in USD, exclude taxes, and are valid to the date on the cover; the capital price becomes firm at engineering release.

## 7. Schedule

BEN 1 is assembled and shipped by Schreiber AI in 2-3 weeks with customer-furnished or in-stock compute: no contract manufacturer, no pad and no site acceptance test; the last milestone is setup and handover. Weeks from order:

| Week | Milestone | Owner | Hold / witness point | Path |
|---|---|---|---|---|
| 0 | Order confirmation: form (10-inch rack or 12U cabinet), compute (customer-furnished or bought by us), outlet and room checked against section 11 | Customer + Schreiber AI | H4 | critical |
| 1 | Kit pulled from Schreiber AI stock (restock lead 8 weeks); non-kit parts on the bench (longest 1 weeks) | Schreiber AI | - | critical |
| 2 | Assembled, imaged and 24 h burn-in test passed (commissioning script in factory mode) | Schreiber AI; customer may witness remotely | H13 | critical |
| 2 | Shipped (parcel for the 10-inch rack, LTL with liftgate for the 12U cabinet) | Schreiber AI | - | critical |
| 3 | Setup and handover at the customer (or remote): placement, outlet check, network, BEN Care enrolment, room-heat check; in service | Schreiber AI + customer | H19, W20 | critical |
| 6 | NOTE: compute bought by Schreiber AI has a 4-week lead time; with customer-furnished compute the dates above hold | Customer | - | risk |

Long-lead items (ordered at engineering release):

| Code | Item | Vendor | Qty | Lead time (weeks) |
|---|---|---|---|---|
| CTL-POD | BEN Pod v1 assembled and provisioned (MGM240P Thread module w/ Secure Vault High, 4x Pt1000 3-wire 24-bit front end, SHT45, 2x dry contact, leak-rope input, 2x isolated 4-20 mA; Pod E adds Ethernet/PoE PD, RS-485, 2x relay) - make item, per unit | contract electronics manufacturer (RFQ 14) | 2 ea | 8 |
| CTL-POD-ENCL | BEN Pod enclosure: Phoenix Contact ICS 50 DIN-rail housing set with rack-rail clip (IP40); IP65 outdoor variant for the outdoor Pod | onlinecomponents / DigiKey | 2 ea | 5 |
| CMP-AI-DGXSPARK | Desktop AI computer NVIDIA DGX Spark (GB10 Grace Blackwell, 128 GB unified memory, 240 W supply) — customer-selectable | NVIDIA / partners | 2 ea | 4 |
| CTL-EDGE-MINI | Fanless edge computer for the BEN Care agent (OnLogic BlastShield CL210, dual LAN) — omit when BEN Care runs on the customer's own box | CDW | 1 ea | 3 |
| PWR-UPS-MINI-1000 | Smart-UPS Li-ion short depth 1000 VA / 800 W 120 V, 2U rack/tower, line-interactive, SmartConnect (NEMA 5-15P) | Reseller listings | 1 ea | 2 |

## 8. Drawings and documents delivered

Issue-for-construction drawing set for the BEN 1, regenerated from the frozen configuration at engineering release and re-issued as built after SAT. Rev 2.A set generated from the configuration at order confirmation (design/layout.py BEN 1 resolver, checks I-B1..I-B7)

| Sheet | Title | Scale |
|---|---|---|
| A-001 | Mini rack general arrangement, U stack and desk / closet footprint | 1:5 |
| E-001 | Power: outlet circuit, UPS, PDU one-line | NTS |
| C-001 | BEN Pods, network and BEN Care enrolment | NTS |

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
| Profile | ai_inference (A2, N+1) |
| ASHRAE class / redundancy (from config) | A2 / N |
| Emphasis | Baseline |
| Standards emphasised | NEC, NFPA 75/2001/72, UL 508A, ASHRAE TC 9.9 A2, AIM Act |
| Extra documents in the pack | Rated-2 design-basis statement; PUE calc |
| Typical AHJ / third-party questions | Noise at property line; refrigerant type |

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
| UL 508A | BEN Controls Lite: DIN-rail cabinet of UL-listed components (RevPi, QUINT4, switch); no 508A panel label | Component listing marks (CTQ-K6) |
| ASHRAE TC 9.9 | Class A2 alarm limits in the controls | Load step test E3/E7 at FAT and SAT |
| AIM Act / EPA 608 | GWP < 700 A1 refrigerant or water loops; certified technicians | Charge record per circuit |
| ISO 668 / 1496 / CSC | One-trip high-cube container, PE-checked modifications, CSC decision at transport | Weld inspection H7, weigh ticket |

## 10. Risks disclosed up front

These are the risks that apply to the ai inference edge profile on a BEN 1, from the product risk register (docs/RISK_REGISTER.md, web/assets/risks.json). Each line says what the design covers and what remains the customer's decision or duty. Please read them before accepting the price.

| ID | Risk | Severity | What can happen | Covered by the design | Customer owns |
|---|---|---|---|---|---|
| R01 | Utility power loss | high | The grid fails for seconds to days. IT shuts down when the battery runs out and cooling stops at once unless it is on UPS or generator. | UPS ride-through (default 10 min), generator option with ATS, measured cooling ride-through (test E5), N+1/2N per profile. | Whether to buy the generator and fuel, the utility contract, and whether cooling is put on UPS. |
| R41 | Heat goes into your closet (BEN 1) | high | Every watt the AI box uses becomes heat in the room: a full cab12 is about 5,600 BTU/h, like a small space heater running all day. A closed closet with no air path heats up within hours and the AI box slows down or shuts off. | Heat-to-room figure on the quote and the data plate, site check before shipping (room cooling or a vent path sized for the unit), BEN Pod intake-temperature alarm before the IT throttles, heat to room measured at handover (E22). | Keep the vent path or door grille open, do not block the intake, tell us if the room changes. |
| R14 | Sensor drift gives false comfort | medium | A drifted sensor can make the dashboard look fine while the room is not. | Redundant sensors, idle cross-check (test E1), drift detection, 12-month or trigger-based recalibration. | Allow calibration visits, do not move sensors. |
| R42 | Circuit overload trips the breaker (BEN 1) | medium | A cab12 at full load uses most of a 20 A circuit. A heater, printer or coffee machine on the same circuit trips the breaker; the UPS carries the IT for a few minutes and then shuts it down. | Dedicated circuit required (15 A rack10, 20 A cab12), load limited to 80 % of the circuit in the configuration, clean shutdown on UPS input loss, input current measured at handover (E22). | Have the dedicated circuit installed and keep other loads and power strips off it. |
| R44 | Someone walks off with it (BEN 1) | medium | A mini rack is small enough to carry and it holds your data. | Lockable cabinet (cab12) or cable-lock point (rack10), disk encryption on by default with the key held off the box, door-contact alarm through the BEN Pod, remote wipe of controller credentials. | Keep it in a lockable room, keep the recovery key safe, insure the equipment. |
| R45 | Consumer-grade gear creeps in (BEN 1) | medium | Someone adds a gaming PC, a cheap switch or an unlisted power strip because it fits. The unit runs hotter, louder and less reliably and may hold a part nobody can support. | Shipped full and labelled, additions by change order with a fit, heat and power check, only UL 62368-1 listed parts on the BEN 1 catalog, BEN Care flags unknown devices. | Ask before adding equipment; no extra power strips. |
| R46 | Backups not tested, restore fails (BEN 1) | medium | Small sites often have a backup job that has silently stopped. When a disk fails or ransomware hits, the restore does not work. | Backup to a second target set up at handover, BEN Care reports every failed backup, quarterly restore test on the maintenance list and checked remotely. | Keep the second backup target and do the quarterly restore test (or let BEN Care do it). |
| R47 | UPS battery wears out (BEN 1) | medium | Lithium UPS batteries last about 3 to 5 years. An old battery holds the IT for seconds, so a short power blip becomes a hard shutdown. | Quarterly UPS self-test reported by BEN Care, battery-health alarm, replacement pack shipped before end of life with a prepaid recycling return, runtime measured at handover (E23). | Swap the battery when it arrives (about 10 minutes) or book the visit. |
| R19 | Component discontinued or listing changes | low | A specified part may be discontinued or lose its listing before or after build. | Approved alternates in the BOM, configuration freeze per unit, FAT repeats affected tests. | None. |
| R43 | Noisier than expected (BEN 1) | low | Fans speed up when the AI box works hard, which can annoy a small office and lead to the unit being moved somewhere worse. | Sound-damped cabinet (cab12), low-speed fans, target 45 dBA or less at 1 m at full load, measured at handover (E21). | Place it away from desks where possible and keep the cabinet door closed. |

## 11. Site requirements summary

The full form (docs/SITE_REQUIREMENTS.md) is signed by the customer and by us at hold point H3 before anything is built for this site. Summary for this unit:

| Item | Value |
|---|---|
| Placement | 10-inch 8U desk / shelf mini rack (open or semi-enclosed): 281 W x 260 D x 451 H mm on a desk, shelf or floor; 300 mm clear at the front and back |
| Mass | 38 kg loaded |
| Power | NEMA 5-15R on a dedicated 15 A, 120 V circuit (12 A continuous at 80 %); draw 5.7 A at 120 V (NEMA 5-15P on the UPS). 230 V 1ph 10/16 A (IEC C14 / C20 inlet) option for export; same UPS family in the 230 V (I) variant |
| Room heat | All 649 W (2213 BTU/h) of BEN 1 goes into the room; the room's air conditioning must remove it. In an open office with central HVAC that is one or two people's worth of heat. In a closed closet it is not: give the closet a transfer fan or door grille moving at least 232 cfm (holds the closet within 5 K of the office), or a dedicated 0.5 ton split unit. Keep the inlet side 300 mm clear of walls. |
| Noise | estimated 45.2 dBA at 1 m (target 50); IT sound pressure at 1 m 45.2 dBA (desktop gear, +15 dB per decade of power) less 0.0 dB cabinet insertion loss, + 28 dBA extraction fans |
| Network | one uplink port (1 GbE) to the customer's router or firewall; BEN Care reaches out over HTTPS only |
| Environment | office air 23 °C design, 30 °C maximum; IT held to ASHRAE A2; UL 62368-1 listed parts, IP20 indoor, NEMA 12 option for dusty closets |
| Permits | none for a plug-in unit; the building's own fire and electrical rules apply |

## 12. Acceptance: burn-in test and handover

Acceptance is by the commissioning script (software/ben_engine/commissioning.py) in factory mode before shipping (24 h burn-in, hold point H13) and a short setup check at handover (H19). Steps that need hardware BEN 1 does not have (generator, liquid loop, DC bus; door and fans on the 10-inch rack) are skipped with the reason stated in the report.

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

Pass criteria specific to this configuration: rack inlets within ASHRAE A2 at 1 kW; N failover with no inlet excursion; UPS ride-through >= 10 minutes at IT load; meter vs PDU reconciliation within 3 %; PUE at full load reported against the 1.081 estimate. Deviations are closed or accepted in writing before the milestone is invoiced.

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

Sensor calibration every 12 months (or on drift trigger) with GUM uncertainty budgets; a spare parts kit per unit is delivered at turnover (MAINTENANCE.md section 7). Climate add-ons for this unit: baseline intervals.

## 14. Commercial terms summary

The governing documents are the Master Services Agreement (docs/contracts/MSA.md), the Statement of Work for this unit (docs/contracts/SOW_TEMPLATE.md, pre-filled from this proposal), the change order form (docs/contracts/CHANGE_ORDER.md), the acceptance certificates, and for the controls layer the software licence (docs/contracts/SOFTWARE_LICENCE.md) and, for the managed option, the service level agreement (docs/contracts/SLA.md). This section summarises them; the contracts prevail.

| Term | Summary |
|---|---|
| Payment | 50 % at Order confirmation / 40 % at Bench test passed and shipped / 10 % at Setup and handover; net 30 from invoice; recurring fees annually in advance |
| Price validity | 60 days from the proposal date; capital price firm at engineering release (configuration frozen, hold point H4) |
| Scope changes | Every change after engineering release is a change order; each change order carries its price impact and its schedule impact and is signed before the work is done |
| Customer-caused delay | A delay caused by the customer or its contractors (site not ready, permits, utility, late information or approvals) extends the schedule day for day and suspends Schreiber AI's liquidated-damages exposure for that period |
| Delivery liquidated damages | 0.5 % of the capital price per week of Schreiber AI-caused delay to FAT, capped at 5.0 %; sole remedy for delay |
| Storage of a finished unit | If the unit passes FAT and cannot ship because the site, permits or utility are not ready, storage and preservation are charged at $10 per day after 14 days, and the FAT milestone is payable |
| Supplier and contract-manufacturer delay | Delivery liquidated damages in our supplier purchase orders and contract-manufacturing agreements flow back-to-back with the customer terms, so a late UPS or switchgear supplier bears its share of any delay damages |
| Title and risk | Title passes at payment of the FAT milestone; risk of loss passes at set-down; freight insured to full replacement value |
| Warranty | 24 months workmanship; vendor warranties passed through (section 13) |
| Acceptance | FAT and SAT by the commissioning script; deviations closed or accepted in writing; acceptance deemed 10 business days after a passing SAT report if not signed |
| Data and software | Customer owns its data; controls software is licensed, not sold; firmware is signed; no cloud dependency |
| Governing law | [GOVERNING_STATE] (set in the MSA) |

## 15. Assumptions and what is not included

- Configuration as on the cover: 1 kW IT, 1 rack(s), Office air: filtered, sound-damped extraction path (no refrigerant), N, climate Temperate; any change is priced as a change order
- Prices from purchasing/parts_catalog.json priced on the dates in the BOM; 9 % confirmed, 66 % list, 25 % estimate for this option; the estimate share is re-priced at engineering release
- Gross margin 28% on hardware and build labour; controls licence $480/yr for this tier; white-label uplift x1.25; managed service $45/kW-month
- Domestic delivery within one day's haul of the integration shop; export, over-dimension permits beyond the carrier's standard, and crane standby beyond one day are extra
- Utility fault current <= 65 kA and voltage within +/-10 % at the disconnect; otherwise current-limiting fuses are added by change order
- Soil bearing >= 100 kPa; otherwise a geotechnical report and revised foundation are the customer's cost
- Permit fees, utility fees, taxes and duties are excluded; AHJ edition of each code applies (docs/COMPLIANCE.md section 16 lists editions not verified on the proposal date)
- Compute hardware prices are reseller listings on the BOM date; GPU server availability can move lead times
- Not included: site civil, utility service, permits, fiber circuits, customer IT software, generator fuel, insurance after set-down, spare parts beyond the turnover kit, decommissioning (quoted separately)

## 16. Signature block

By signing, the customer accepts this proposal (SAI-BEN1-20261109-ADA95012) and the risk disclosure in section 10, and authorises Schreiber AI to start the site survey and engineering release; the site requirements form is signed separately at hold point H3.

| Role | Name | Signature | Date |
|---|---|---|---|
| Customer authorised representative, Harbor Street Accounting |  |  |  |
| Schreiber AI — sales |  |  |  |
| Schreiber AI — engineering |  |  |  |
| Schreiber AI — compliance |  |  |  |

---
*Schreiber AI — proposal SAI-BEN1-20261109-ADA95012. Generated by ben_engine.proposal from the configuration model; numbers are not hand-edited.*