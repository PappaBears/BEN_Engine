# Northwind Partners — BEN Engine proposal SAI-BEN2000-20261108-351AA57D

*BEN 2000 · AI training pod · Northwind Partners for Meridian Compute · Tucson, AZ · 2026-11-08 · valid until 2027-01-07*

## 1. Cover

| Item | Value |
|---|---|
| Proposal | BEN Engine BEN 2000 for Northwind Partners for Meridian Compute |
| Prepared by | Northwind Partners (engineering by Schreiber AI) |
| Customer | Northwind Partners for Meridian Compute |
| Site | Tucson, AZ |
| Tier | BEN 2000 — Prefabricated wide-body modular hall (3 site-joined 12.2 m modules) + power module + plant yard, IP66 envelope |
| Mission profile | AI training pod (ai_training) |
| Climate package | Hot / arid |
| Purchase option | White-label |
| Date | 2026-11-08 |
| Valid until | 2027-01-07 (60 days) |
| Proposal ID | SAI-BEN2000-20261108-351AA57D |
| Configuration | 1600 kW IT in 27 rack(s), Direct liquid cooling + CDU + dry cooler, N+1, 10 min UPS, generator |

AI infrastructure that arrives finished. This proposal is generated from configuration version c88b7c34; every number in it comes from the same model that produces the drawings, bill of materials, digital twin and commissioning script.

## 2. Executive summary

Northwind Partners for Meridian Compute needs 1600 kW of IT capacity for a AI training pod workload at Tucson, AZ. We propose one BEN 2000: a Prefabricated wide-body modular hall (3 site-joined 12.2 m modules) + power module + plant yard, IP66 envelope fitted out as a complete data center with 27 rack(s), Direct liquid cooling + CDU + dry cooler with N+1 redundancy, a 2 x 1937 kVA UPS giving 10 minutes of ride-through, a standby generator, clean-agent fire protection and the BEN Controls layer (sensors, firmware, digital twin, dashboard).

The unit arrives finished and factory-tested. It needs a pad, a 3000 A 12.47 kV MV service → 480 V 3ph feeder, fiber and a grounding electrode at the site; everything inside the enclosure is built, wired, tested and documented before it ships.

Price for the white-label option: $55,225,268 capital ($34,516 per kW IT) plus $112,500 per year (White-label licence under the Northwind Partners brand). 73 % of the underlying cost is at confirmed vendor prices, 0 % at manufacturer list price and 27 % is engineering estimate; the price is firm at engineering release, when the configuration is frozen.

Order to in-service: about 80 weeks, set by the longest-lead item (52 weeks) and the permit cycle. Risks are disclosed in section 10 before the price is accepted; the site requirements in section 11 are signed before anything is built for this site.

## 3. Mission profile and what it means

| Item | Value |
|---|---|
| Profile | AI training pod (ai_training) |
| ASHRAE class | A1: 15–32 °C inlet, 20–80 % RH allowable (recommended 18–27 °C); the tightest class, for sensitive or mission-critical IT |
| Redundancy | N+1: one spare cooling unit and one spare UPS module; any single unit can fail or be serviced with no loss of capacity |
| Design rack density | 59.26 kW per rack (profile default 60 kW) |
| Climate package | Hot / arid: design outdoor 46 °C / minimum -5 °C, solar 1000 W/m², corrosion class ISO 9223 C2, basic wind 47 m/s (ASCE 7) |
| Cooling derate at design day | 1.000 -> 300.0 kW per unit; 7 units installed for 6 required |
| Generator | included (profile default) |

What this means for you: the environmental class sets the alarm limits your IT will be held to; the redundancy level sets what happens when a component fails; the climate package sets the coatings, anchorage, condensation control and cooling capacity margins built into the unit. All three are fixed at engineering release and verified at the factory and site acceptance tests.

## 4. The unit: sizing

| Item | Value | Basis |
|---|---|---|
| Enclosure | Prefabricated wide-body modular hall (3 site-joined 12.2 m modules) + power module + plant yard, IP66 envelope | External 36.6 x 11.0 x 4.2 m; interior 35.8 x 10.4 x 3.6 m; 3 site-joined modules |
| IT load | 1600 kW in 27 rack(s) of 48 U | 59.26 kW per rack; tier range 800–2000 kW |
| Cooling | 7 x Direct liquid cooling + CDU + dry cooler | 6 required at 300.0 kW each (derate 1.0), N+1 |
| Row fit | fits | 4 row(s) of 7 racks, 5900 mm per row vs interior 35800 mm |
| Cooling electrical | 133.33 kW | COP 12.0 at design point |
| Total electrical demand | 1765.8 kW / 1858.8 kVA | IT + cooling + 2 % house + 0.5 kW controls, pf 0.95 |
| Controls tier | BEN Controls Pro | PLCnext AXC F 2152 + Axioline I/O in a UL 508A BEN Controller panel, OnLogic Karbon 400 edge computer (TPM 2.0); 60 BEN Pods on the BEN Mesh (Thread, Secure Vault); selectable with controls_tier (docs/CONTROLS_HARDWARE_DECISION.md 2a) |
| Service | 12.47 kV MV service → 480 V 3ph, 3000 A breaker | calculated 2795 A at 80 % continuous, rounded to the next frame; medium-voltage utility service to pad-mount transformers |
| Transformers | 2 x 2,500 kVA pad-mount (MV to 480 V) | N+1: 2N transformer pairs when 2N or N+1; 90 % loading at 1858.8 kVA |
| Generators | 3 x 1,250 kW | N+1 standby with 48 h fuel; SPCC plan for the fuel yard |
| Hardening | H2 Severe environment: NEMA 4X / IP66 + flood plinth 600 mm | coating ISO 12944 C5-M; recommended for this profile/climate: H2; envelope 802.4 m² |
| UPS | 2 x 1937 kVA | IT only with 15 % headroom, N+1 |
| Battery | 296.3 kWh lithium (LFP) | 10 min at IT load, 90 % depth of discharge |
| NFPA 855 scope | YES - battery >= 20 kWh: UL 9540A data, gas detection and venting, AHJ review | energy storage threshold |
| Airflow | 64,000 cfm | 125 cfm/kW air-cooled at 12 K rise; 40 cfm/kW liquid/water |
| Envelope gain at design day | 35.7 kW | 100 mm PIR, R 3.5 m²K/W, solar on roof |
| Mass | payload 34,985 kg; gross 94,985 kg | tare 60,000 kg; crane and pad sized for the gross mass |
| PUE estimate | 1.134 | design-point calculation incl. 0.03 UPS loss; measured at SAT |

## 5. Scope of supply

| Module | Status | BOM lines | Sell price |
|---|---|---|---|
| Power module | included | 18 lines | $7,400,615 |
| Cooling module | included | 6 lines | $3,178,222 |
| Compute module | included | 5 lines | $39,128,950 |
| Controls module | included | 30 lines | $82,821 |
| Structure (container / cabinet) | included | 12 lines | $2,849,754 |
| Envelope (insulation, liner, coatings) | included | 9 lines | $73,274 |
| Fire detection and suppression | included | 8 lines | $963,514 |
| Site kit (anchors, embeds, signage) | included | 7 lines | $958,972 |
| Build labour, FAT, logistics | included | 8 lines | $589,146 |

Top 15 lines of the 103-line bill of materials for this option (sell price at 28% gross margin; the full priced BOM with vendors, part numbers and price confirmation dates is delivered at engineering release):

| Code | Item | Manufacturer / MPN | Qty | Sell price | Price basis | Lead (wk) |
|---|---|---|---|---|---|---|
| CMP-GPU-H100 | GPU SuperServer 8U, 2x Xeon, 8x NVIDIA HGX H100 SXM5 (~10 kW) | Supermicro SYS-821GE-TNHR | 117 ea | $38,333,750 | confirmed | 10 |
| PWR-GEN-1250 | Diesel standby generator 1,250 kW / 1,562 kVA 480 V, EPA Tier 2 stationary emergency, Level 2 sound-attenuated enclosure, 24 h sub-base tank, paralleling-ready controls (N+1 set) | Caterpillar / Cummins / Kohler CAT D1250 GC / Cummins QSK50-DQGAA | 3 ea | $2,583,333 | estimate | 52 |
| STR-MODULE-WB | Wide-body prefabricated data-hall module (one 12.2 m bay = three road sections 12.2 x 3.66 x 4.2 m, site-joined to 12.2 x 11.0 m), factory-finished steel frame, 100 mm PIR sandwich walls/roof, IP66 envelope, 3.6 m clear interior, C3 coating | modular building manufacturer (PCX / Whitley / Compass Datacenters-class, RFQ email 19) WB-12.2-DH | 3 ea | $1,750,000 | estimate | 26 |
| CLG-CDU | Row CDU 450-750 kW liquid-to-liquid (DLC) | Vertiv / CoolIT XDU450 / CHx750 | 7 ea | $1,458,333 | estimate | 16 |
| PWR-UPS-GVL500 | Galaxy VL UPS 500 kVA/kW 480 V frame, N+1 internal power modules, parallel-capable (4 frames per 2,000 kW string; 2 strings for 2N) | Schneider Electric GVL500KDS | 8 ea | $978,600 | confirmed | 20 |
| FS-CLEAN-AGENT-HALL | Pre-engineered FK-5-1-12 clean agent per module zone + power module: cylinders, nozzles, releasing panels, cross-zoned detection, design and AHJ submittal, installed, per m3 protected | Fike / Kidde (via licensed fire contractor) ECS-500 / Fike CA | 1,501 m3 protected | $875,583 | estimate | 10 |
| PWR-LV-SWGR-4000 | 480 V low-voltage switchgear 4,000 A UL 1558, drawout power circuit breakers, main-tie-main ready, 6 feeder breakers, arc-resistant option, one lineup per transformer (A / B) | Eaton Magnum / Schneider MasterPact / Vertiv Powerboard Magnum DS 4000 A | 2 ea | $861,111 | estimate | 44 |
| PWR-BATT-ROOM | Lithium (LFP) UPS battery cabinets for the 2,000 kW strings, UL 9540 / UL 9540A, in two battery rooms with 2-hour separation (NFPA 855), per kWh installed | Schneider Galaxy Li-Ion / Vertiv EnergyCore / Samsung SDI Li-ion cabinet string | 594 kWh | $742,500 | estimate | 24 |
| CMP-CPU | PowerEdge R760 2U rack server (management / storage node) | Dell Technologies R760 | 27 ea | $674,962 | confirmed | 3 |
| STR-MODULE-PWR | Power module 12.2 x 11.0 x 4.2 m (three road sections), factory-fitted: 480 V switchgear room with 1.5 m working space, UPS room, two lithium battery rooms with 2-hour fire separation (NFPA 855), HVAC, IP66 envelope | modular building manufacturer (RFQ email 19) WB-12.2-PWR | 1 ea | $638,889 | estimate | 26 |
| CLG-PIPING-HALL | Plant piping: primary glycol loop DN200 to the dry coolers, secondary DN150 headers to the CDU rows, N+1 pump skid with VFDs, expansion, air separation, chemical treatment, insulation and heat trace (lot) | mechanical contractor PIPE-LOT | 1 lot | $583,333 | estimate | 14 |
| CLG-FANWALL | Fan-wall air handler 200 kW class on the hall long wall, chilled/glycol coil, EC fan array N+1, ePM1 filters, for residual air-side heat (one per module + 1) | Vertiv CoolLoop Thermal Wall / Mitsubishi CVWALL / Carrier Thermal Wall 200 kW | 4 ea | $527,778 | estimate | 20 |
| SITE-MV-INTERCONNECT | MV utility interconnect allowance: primary metering, 12.47 kV riser/ductbank 150 m, utility contribution-in-aid, protection study and witness test | utility + MV contractor MV-IC | 1 lot | $486,111 | estimate | 52 |
| PWR-BUSWAY | Overhead track busway 800 A 480 V, 36 m run with end-feed, 12 plug-in tap-off boxes 60 A 3P (one A or B run per row) | Starline (Legrand) / Eaton Pow-R-Way T5 800 A | 8 ea | $466,667 | estimate | 12 |
| PWR-GEN-PARALLEL | Generator paralleling switchgear 480 V 4,000 A with load-share controls, utility-paralleling (closed transition) and load-shed, outdoor walk-in or in the power module | ASCO / Eaton / Russelectric ASCO 7000 series paralleling | 1 ea | $388,889 | estimate | 44 |

Explicitly excluded:

- Site civil works: pad, piers, anchors set in concrete, drainage, fencing, lighting, equipment yard (PE-stamped drawings are supplied by us)
- Utility service: feeder from the customer's switchgear to the disconnect at the unit, utility fees, metering, interconnection
- Permits and fees pulled by the customer (zoning, building, utility, generator air permit); we supply the engineering documents
- Fiber / ISP circuits, customer network equipment above the controls LAN, customer software licences
- Taxes, duties, freight insurance beyond the quoted domestic delivery, crane standby beyond one day

## 6. Price

| Option | Capital price | Per kW IT | Recurring / year | Term | Total over term | Confirmed / list / estimate | BOM lines | Status |
|---|---|---|---|---|---|---|---|---|
| Hardware only | $55,142,447 | $34,464 | - | 1 yr | $55,142,447 | 73 / 0 / 27 % | 73 | alternative |
| Hardware + BEN Controls | $55,225,268 | $34,516 | $90,000 | 1 yr | $55,315,268 | 73 / 0 / 27 % | 103 | alternative |
| White-label | $55,225,268 | $34,516 | $112,500 | 1 yr | $55,337,768 | 73 / 0 / 27 % | 103 | PROPOSED |
| Managed service | $55,225,268 | $34,516 | $864,000 | 3 yr | $57,817,268 | 73 / 0 / 27 % | 103 | alternative |

Confirmed = price seen on a vendor or distributor listing on the date in the BOM; list = manufacturer published price; estimate = engineering estimate with its basis stated in the BOM note. Capital prices carry a 28% gross margin on purchased hardware and build labour. Recurring items: Hardware + BEN Controls: BEN Controls licence (dashboard, twin, firmware updates, remote support hooks); White-label: White-label licence under the Northwind Partners brand (controls licence x 1.25, partner branding, source escrow); Managed service: Managed service at $45/kW-month x 1600 kW IT (includes the BEN Controls licence, remote operations and the maintenance schedule).

| Managed service term | Capital | Service fees | Total |
|---|---|---|---|
| 1 year | $55,225,268 | $864,000 | $56,089,268 |
| 3 years | $55,225,268 | $2,592,000 | $57,817,268 |
| 5 years | $55,225,268 | $4,320,000 | $59,545,268 |

Payment milestones for the proposed option (White-label, capital $55,225,268):

| Milestone | Share | Amount | Week from order |
|---|---|---|---|
| Engineering release (H4) | 30 % | $16,567,580 | 12 |
| Factory acceptance test (H13) | 40 % | $22,090,107 | 70 |
| Site acceptance test (H19) | 25 % | $13,806,317 | 79 |
| Turnover (W20) | 5 % | $2,761,263 | 80 |

Recurring fees are invoiced annually in advance from turnover. Prices are in USD, exclude taxes, and are valid to the date on the cover; the capital price becomes firm at engineering release.

## 7. Schedule

Milestones in weeks from order, derived from the stage durations in docs/PROCESS_FLOW.md for the BEN 2000 (reference order-to-service about 52 weeks) and the longest lead time in this bill of materials (52 weeks). Critical path: engineering release -> long-lead procurement -> fit-out -> FAT -> SAT. Site civil and permits run in parallel.

| Week | Milestone | Owner | Hold / witness point | Path |
|---|---|---|---|---|
| 0 | Order and risk acknowledgement signed | Customer + Schreiber AI | - | critical |
| 4 | Site survey and site requirements sign-off | Customer + ENG | H3 | critical |
| 12 | Engineering release: configuration frozen, IFC drawings, BOM; long-lead purchase orders placed | ENG | H4 | critical |
| 24 | Container / cabinet received and inspected; structural and envelope work starts | FAC | W6, H7, W8 | critical |
| 24 | Permits issued (building, electrical, mechanical, fire plan review) | Customer / AHJ | - | parallel |
| 44 | Site pad, grounding and utility feeder complete and surveyed | Customer civil | H16 | parallel |
| 64 | Longest-lead item on the floor (52 weeks from release); mechanical and electrical fit-out complete | FAC + SUB | H10 | critical |
| 70 | Cooling, controls and firmware complete; factory acceptance test incl. 24 h burn-in | FAC + ENG; customer witness | H11, W12, H13 | critical |
| 73 | Transport prep and shipping | LOG | - | critical |
| 77 | Set-down, hook-up and pre-energisation check | LOG + SUB + AHJ | W17, H18 | critical |
| 79 | Site acceptance test and fire marshal acceptance | ENG + customer + AHJ | H19 | critical |
| 80 | Training and turnover; unit in service | ENG + customer | W20 | critical |

Long-lead items (ordered at engineering release):

| Code | Item | Vendor | Qty | Lead time (weeks) |
|---|---|---|---|---|
| PWR-GEN-1250 | Diesel standby generator 1,250 kW / 1,562 kVA 480 V, EPA Tier 2 stationary emergency, Level 2 sound-attenuated enclosure, 24 h sub-base tank, paralleling-ready controls (N+1 set) | Cat / Cummins dealer (RFQ email 20) | 3 ea | 52 |
| SITE-MV-INTERCONNECT | MV utility interconnect allowance: primary metering, 12.47 kV riser/ductbank 150 m, utility contribution-in-aid, protection study and witness test | utility / MV contractor (RFQ email 15/20) | 1 lot | 52 |
| PWR-MV-XFMR-2500 | Pad-mount transformer 2,500 kVA, 12.47 kV delta (or 13.8 kV) - 480Y/277 V, FR3 natural ester, dead-front loop feed, bayonet fuses, taps (2N pair) | transformer distributor (RFQ email 20) | 2 ea | 48 |
| PWR-LV-SWGR-4000 | 480 V low-voltage switchgear 4,000 A UL 1558, drawout power circuit breakers, main-tie-main ready, 6 feeder breakers, arc-resistant option, one lineup per transformer (A / B) | switchgear manufacturer (RFQ email 20) | 2 ea | 44 |
| PWR-GEN-PARALLEL | Generator paralleling switchgear 480 V 4,000 A with load-share controls, utility-paralleling (closed transition) and load-shed, outdoor walk-in or in the power module | ASCO dealer (RFQ email 20) | 1 ea | 44 |

## 8. Drawings and documents delivered

Issue-for-construction drawing set for the BEN 2000, regenerated from the frozen configuration at engineering release and re-issued as built after SAT. Issue for construction set regenerated from the frozen configuration at engineering release (index not readable at proposal time)

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
| Profile | ai_training (A1, N+1, 60 kW/rack, DLC) |
| ASHRAE class / redundancy (from config) | A1 / N+1 |
| Emphasis | High density, liquid |
| Standards emphasised | NFPA 75-2024 liquid/immersion clauses; ASHRAE W-class; glycol handling; UL 9540/NFPA 855 (battery > 20 kWh likely) |
| Extra documents in the pack | CDU fluid spec and leak response; battery HMA; 400–1000 A arc-flash study |
| Typical AHJ / third-party questions | Battery fire protection; leak detection; weight on pad |

Climate add-ons:

| Item | Value |
|---|---|
| Climate | hot_arid |
| Config values | 46 °C / −5 °C, 1000 W/m², C2, 47 m/s |
| Compliance / design add-ons | DX derate 0.835 → one extra cooling unit (config adds it automatically); condenser/dry-cooler rated to 50 °C ambient (verify vendor curve); sand/dust: MERV 13 pre-filters with hoods, NEMA 4X / IP66 louvres with sand traps; solar: white cool-roof coating (SRI ≥ 80), optional shade canopy (reduces envelope_gain_kw ~1.5 kW on BEN 150) |
| Verification | E8 outdoor derate test; filter dP trend |

Baseline matrix lines that apply to every unit:

| Code / standard | Design feature | Verification |
|---|---|---|
| NFPA 70 (NEC) | Listed dead-front gear, SCCR 65 kA, selective coordination, arc-flash labels | Electrical inspection H10, AHJ at H18 |
| NFPA 75 / 2001 / 72 | Non-combustible liner, VEWFD, clean agent with 10-min hold, EPO, HVAC shutdown | Door-fan test, NFPA 72 record of completion at SAT |
| UL 508A | BEN Controller panel (PLCnext PLC, I/O, edge computer) built and labelled by a UL 508A shop | Panel label and schedule (CTQ-K6) |
| ASHRAE TC 9.9 | Class A1 alarm limits in the controls | Load step test E3/E7 at FAT and SAT |
| AIM Act / EPA 608 | GWP < 700 A1 refrigerant or water loops; certified technicians | Charge record per circuit |
| ISO 668 / 1496 / CSC | One-trip high-cube container, PE-checked modifications, CSC decision at transport | Weld inspection H7, weigh ticket |
| NFPA 855 / UL 9540 / 9540A | 296.3 kWh LFP battery: listed cabinets, gas detection, venting, separation | UL 9540A data in the pack; AHJ review |
| NFPA 110 / NFPA 37 / 30 | Standby generator with ATS, fuel system, exhaust setbacks | Installation acceptance test, load bank |

## 10. Risks disclosed up front

These are the risks that apply to the ai training pod profile, from the product risk register (docs/RISK_REGISTER.md, web/assets/risks.json). Each line says what the design covers and what remains the customer's decision or duty. Please read them before accepting the price.

| ID | Risk | Severity | What can happen | Covered by the design | Customer owns |
|---|---|---|---|---|---|
| R01 | Utility power loss | high | The grid fails for seconds to days. IT shuts down when the battery runs out and cooling stops at once unless it is on UPS or generator. | UPS ride-through (default 10 min), generator option with ATS, measured cooling ride-through (test E5), N+1/2N per profile. | Whether to buy the generator and fuel, the utility contract, and whether cooling is put on UPS. |
| R05 | Cooling stops when power is lost | high | If cooling is not on UPS, inlet temperature in a small container rises several degrees per minute at full load. | Ride-through measured in test E5 and published; option to put fans and pumps on UPS; generator start in 10 s; load-shed hooks. | Choose: accept a few minutes, add cooling to UPS, or add a generator. |
| R15 | Permit delay or unexpected AHJ requirement | high | The local authority may classify the container as a building, ask for a field evaluation or more fire protection, and take longer than the build. | Pre-application package, code summary, field-evaluation budget line, site requirements signed before build, parallel permit path in the schedule. | Pulling permits (or authorising us), zoning, neighbour relations. |
| R18 | Long-lead parts slip | high | UPS, switchgear, cooling units and transformers can take months and slip. | Long-lead orders at engineering release, approved alternates, stocked controls hardware. | Early deposit and configuration freeze; no late changes. |
| R27 | Medium-voltage utility service lead time (BEN 2000) | high | A new 12.47 kV service with primary metering and two pad-mount transformers is utility work on the utility's schedule, typically 26 to 52 weeks. | Interconnection application filed at order, utility window carried on the critical path, load letter and single-line ready at kick-off, temporary 480 V service for commissioning where allowed. | The utility contract and fees, land for utility equipment, easements. |
| R30 | Construction permit for a building (BEN 2000) | high | The hall is a building (IBC Group B or F-1), not an equipment enclosure: plan review, state modular approval and inspections take 8 to 16 weeks before civil works can start. | Stamped permit set from the engineering release, state modular label on each module, pre-application meeting, civil package starts after permit, both occupancy classifications budgeted. | Zoning, land use, easements, neighbour notice, permit fees. |
| R02 | Arc flash or electrical fault | medium | A fault while a panel is open or a component failure can injure someone and damage equipment. | Arc-flash study and labels, selective coordination, listed dead-front gear, lockout points, NFPA 70E training at turnover. | Only qualified electricians work on it and the labels are followed. |
| R04 | Rack inlets run hot | medium | Hot days, a failed cooling unit or more load than planned push inlet temperatures up; IT throttles or trips. | N+1 cooling, climate derate built into sizing, inlet sensors at three heights per rack with ASHRAE alarms, load-step and failover tests. | Keep IT load inside the configured kW, keep filters and coils clean, do not block containment. |
| R06 | Fire inside the container | medium | A cable, battery or power supply fire would mean loss of IT, an agent discharge and downtime. | Very-early smoke detection, clean agent with 10-minute hold, HVAC shutdown, EPO, non-combustible liner, battery separation. | Fire marshal relationship, agent recharge contract, no combustible storage inside, insurance. |
| R07 | Lithium battery thermal runaway | medium | A battery cell failure can release flammable gas and start a fire that spreads if not contained. | LFP chemistry, UL 1973/9540 listed cabinets with UL 9540A data, BMS alarms, gas detection and venting above 20 kWh, capped battery size on smaller tiers; BEN 2000 battery rooms with 2-hour separation and gas detection. | No unapproved batteries, keep BMS firmware updated, respond to BMS alarms. |
| R08 | Water or coolant leak | medium | Roof, door seals, condensate or a liquid-cooling loop can leak and damage IT. | Rope leak sensors, condensate float alarm, drip trays, CDU auto pump stop on leak, propylene glycol only, seal inspection schedule. | Keep drains clear, respond to alarms, pad drainage. |
| R14 | Sensor drift gives false comfort | medium | A drifted sensor can make the dashboard look fine while the room is not. | Redundant sensors, idle cross-check (test E1), drift detection, 12-month or trigger-based recalibration. | Allow calibration visits, do not move sensors. |
| R17 | Noise complaints | medium | Dry coolers and condensers can exceed night-time limits at the property line. | Sound prediction at quote, low-noise fans and night setback, acoustic survey at SAT (test E10), barrier option. | Site selection, setbacks, local ordinance. |
| R20 | Site costs above quote | medium | Civil works, permits and utility connection can cost more than the allowance. | Firm box price after engineering release; site works quoted after survey; utility costs identified at survey. | Utility fees, civil works, permits, taxes, and changes after freeze. |
| R21 | Energy cost higher than expected | medium | Cooling energy rises in hot climates and with high utilisation. | Honest PUE estimate from the configuration, measured at SAT (test E9), economizer and variable-speed fans. | Electricity tariff and IT utilisation. |
| R24 | Heat and noise in the hot aisle | medium | Technicians can face heat stress and noise above 85 dBA behind high-density racks. | Work limits in the O&M manual, hearing protection signage, cold-aisle work position for most tasks. | Work-rest cycles and PPE. |
| R28 | Water availability for adiabatic cooling (BEN 2000) | medium | Hot-day make-up water is 2 to 8 cubic metres a day per 1,000 kW; drought rules or a weak supply can force the coolers to run dry and lose capacity on the hottest days. | Dry mode below 28 C, chilled-water option for hot climates, water quantity and drain confirmed at site survey, storage tank option, water management plan per ASHRAE 188. | Water supply contract, drought-rule compliance, sewer discharge permit for bleed water. |
| R29 | Module joint leakage (BEN 2000) | medium | The three hall modules are sealed on site; the seams are the one part of the IP66 envelope not finished in the factory. | Factory compression gaskets and field EPDM cover strips with a drained cavity, joint seal hose test E15 at SAT and after any relocation, leak rope under each joint, semi-annual seal inspection. | Keep the roof clear of debris and snow beyond design, respond to alarms. |
| R03 | Site fault current differs from assumption | low | Until the utility gives its fault current and voltage, arc-flash labels and some ratings are provisional. | Labels marked provisional until SAT; study updated with utility data; panel SCCR at least 65 kA. | Provide utility fault current and voltage before the unit ships. |
| R09 | Transport or lifting damage | low | A bad lift or rough transport can twist the frame or crack a weld. | Corner-casting lifts with spreader, PE-checked frame, shock loggers, set-down inspection, freight insurance; BEN 2000 modules lifted on engineered lugs with a 100 t crane and a certified lift plan. | Crane access, competent rigger, route survey for the high-cube height. |
| R19 | Component discontinued or listing changes | low | A specified part may be discontinued or lose its listing before or after build. | Approved alternates in the BOM, configuration freeze per unit, FAT repeats affected tests. | None. |
| R23 | Person inside during agent discharge or refrigerant leak | low | Clean agent or a refrigerant leak can disorient or expose a technician inside. | Pre-discharge alarm with delay, abort switch, door interlock, refrigerant detector, purge ventilation, written entry procedure, non-flammable refrigerants. | Follow the entry procedure, keep training current. |

## 11. Site requirements summary

The full form (docs/SITE_REQUIREMENTS.md) is signed by the customer and by us at hold point H3 before anything is built for this site. Summary for this unit:

| Item | Value |
|---|---|
| Pad plan size | Hall slab 40 × 14 m; power module slab 14 × 6 m; MV pad 8 × 6 m with oil containment; generator pad 20 × 8 m with containment and fuel tanks; plant yard 30 × 10 m for adiabatic coolers and water treatment; total fenced site ≈ 70 × 45 m |
| Pad type | 250–300 mm slab-on-grade with grade beams under module rails (line load ≈ 25 kN/m), designed from the geotechnical report; frost-protected shallow foundation in cold |
| Anchor points | Cast-in embed plates at 3 m centres under each module rail; welded hold-downs per seismic category |
| Gross mass to set | 94,985 kg (crane sized for this mass at the required radius) |
| Utility service | Medium voltage 12.47 kV (or 13.8 kV) 3φ from the utility with primary metering; customer-owned 15 kV class loop-feed pad-mount switch, 2 × 2,500 kVA pad-mount transformers (2N) to 480Y/277 V; customer disconnect rated 3000 A for this configuration (tier range: MV switch with fused ways; 480 V mains 2 × 3,000 A in the power module (we supply)) |
| Feeder conductors (customer side) | MV: 15 kV 1/0 Al or Cu EPR cable in concrete-encased duct bank (utility spec); LV: bus duct 3,000 A per transformer to switchgear, ≤ 15 m |
| Fault current | utility available fault current and voltage required before shipping; unit SCCR 65 kA |
| Generator | Standard: 3 × 1,250 kW N+1, 48 h fuel (≈ 10,500 US gal diesel in UL 142 double-wall sub-base or bulk tank); PE-certified SPCC plan; fuel delivery access for a 30 t tanker |
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

Pass criteria specific to this configuration: rack inlets within ASHRAE A1 at 1600 kW; N+1 failover with no inlet excursion; UPS ride-through >= 10 minutes at IT load; meter vs PDU reconciliation within 3 %; PUE at full load reported against the 1.134 estimate. Deviations are closed or accepted in writing before the milestone is invoiced.

## 13. Warranty, maintenance and support

| Item | Value |
|---|---|
| Workmanship warranty | 24 months from SAT on the integration, wiring, piping, envelope and controls build |
| Equipment warranty | Vendor warranties (UPS, cooling, CDU, batteries, fire panel, generator, servers) registered in the customer's name at turnover and passed through; minimum 12 months, longer where the vendor offers it |
| Controls software | Signed Pod firmware, PLC project and edge computer updates for the licence term; security fixes for the life of the licence |
| Support level in this option | Second-line engineering support to Northwind Partners; partner delivers first-line support under its own brand |

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

Sensor calibration every 12 months (or on drift trigger) with GUM uncertainty budgets; a spare parts kit per unit is delivered at turnover (MAINTENANCE.md section 7). Climate add-ons for this unit: filter inspection monthly, coil cleaning quarterly, cool-roof coating check annually.

## 14. Commercial terms summary

The governing documents are the Master Services Agreement (docs/contracts/MSA.md), the Statement of Work for this unit (docs/contracts/SOW_TEMPLATE.md, pre-filled from this proposal), the change order form (docs/contracts/CHANGE_ORDER.md), the acceptance certificates, and for the controls layer the software licence (docs/contracts/SOFTWARE_LICENCE.md) and, for the managed option, the service level agreement (docs/contracts/SLA.md). This section summarises them; the contracts prevail.

| Term | Summary |
|---|---|
| Payment | 30 % at Engineering release / 40 % at Factory acceptance test / 25 % at Site acceptance test / 5 % at Turnover; net 30 from invoice; recurring fees annually in advance |
| Price validity | 60 days from the proposal date; capital price firm at engineering release (configuration frozen, hold point H4) |
| Scope changes | Every change after engineering release is a change order; each change order carries its price impact and its schedule impact and is signed before the work is done |
| Customer-caused delay | A delay caused by the customer or its contractors (site not ready, permits, utility, late information or approvals) extends the schedule day for day and suspends Schreiber AI's liquidated-damages exposure for that period |
| Delivery liquidated damages | 0.5 % of the capital price per week of Schreiber AI-caused delay to FAT, capped at 5.0 %; sole remedy for delay |
| Storage of a finished unit | If the unit passes FAT and cannot ship because the site, permits or utility are not ready, storage and preservation are charged at $2,500 per day after 14 days, and the FAT milestone is payable |
| Supplier and contract-manufacturer delay | Delivery liquidated damages in our supplier purchase orders and contract-manufacturing agreements flow back-to-back with the customer terms, so a late UPS or switchgear supplier bears its share of any delay damages |
| Title and risk | Title passes at payment of the FAT milestone; risk of loss passes at set-down; freight insured to full replacement value |
| Warranty | 24 months workmanship; vendor warranties passed through (section 13) |
| Acceptance | FAT and SAT by the commissioning script; deviations closed or accepted in writing; acceptance deemed 10 business days after a passing SAT report if not signed |
| Data and software | Customer owns its data; controls software is licensed, not sold; firmware is signed; no cloud dependency |
| Governing law | [GOVERNING_STATE] (set in the MSA) |

## 15. Assumptions and what is not included

- Configuration as on the cover: 1600 kW IT, 27 rack(s), Direct liquid cooling + CDU + dry cooler, N+1, climate Hot / arid; any change is priced as a change order
- Prices from purchasing/parts_catalog.json priced on the dates in the BOM; 73 % confirmed, 0 % list, 27 % estimate for this option; the estimate share is re-priced at engineering release
- Gross margin 28% on hardware and build labour; controls licence $90,000/yr for this tier; white-label uplift x1.25; managed service $45/kW-month
- Domestic delivery within one day's haul of the integration shop; export, over-dimension permits beyond the carrier's standard, and crane standby beyond one day are extra
- Utility fault current <= 65 kA and voltage within +/-10 % at the disconnect; otherwise current-limiting fuses are added by change order
- Soil bearing >= 100 kPa; otherwise a geotechnical report and revised foundation are the customer's cost
- Permit fees, utility fees, taxes and duties are excluded; AHJ edition of each code applies (docs/COMPLIANCE.md section 13 lists editions not verified on the proposal date)
- Compute hardware prices are reseller listings on the BOM date; GPU server availability can move lead times
- Not included: site civil, utility service, permits, fiber circuits, customer IT software, generator fuel, insurance after set-down, spare parts beyond the turnover kit, decommissioning (quoted separately)

## 16. Signature block

By signing, the customer accepts this proposal (SAI-BEN2000-20261108-351AA57D) and the risk disclosure in section 10, and authorises Schreiber AI to start the site survey and engineering release; the site requirements form is signed separately at hold point H3.

| Role | Name | Signature | Date |
|---|---|---|---|
| Customer authorised representative, Northwind Partners for Meridian Compute |  |  |  |
| Schreiber AI — sales |  |  |  |
| Schreiber AI — engineering |  |  |  |
| Schreiber AI — compliance |  |  |  |
| Partner, Northwind Partners |  |  |  |

---
*Schreiber AI — proposal SAI-BEN2000-20261108-351AA57D. Generated by ben_engine.proposal from the configuration model; numbers are not hand-edited.*