# BEN Engine — Site Requirements (the customer signs this before we ship)

**Owner:** Schreiber AI engineering. **Purpose:** this is hold point **H3** in `docs/PROCESS_FLOW.md`. Nothing is built for a specific site until this document is filled in and signed by the customer and by Schreiber AI. It is written as a form: every line is either a value we need from the customer, a value we provide from the configuration, or a tick box.

Numbers marked *(config)* come from `software/ben_engine/config.py` for the tier's default preset (`Config.preset(tier)`); the unit-specific values are printed from the frozen configuration at engineering release and replace them.

## 1. Unit summary (filled from the configuration)

| Item | BEN 5 | BEN 30 | BEN 150 | BEN 500 | BEN 2000 |
| --- | --- | --- | --- | --- | --- |
| Enclosure (all NEMA 4X / IP66 at hardening H1) | Outdoor 24U cabinet on skid | 10 ft high-cube ISO-frame module | 20 ft high-cube ISO-frame module | 40 ft high-cube ISO-frame module | Prefabricated hall: 3 joined wide-body modules + power module + plant yard |
| External L × W × H (m) | 1.20 × 1.00 × 1.80 | 2.991 × 2.438 × 2.896 | 6.058 × 2.438 × 2.896 | 12.192 × 2.438 × 2.896 | Hall 36.6 × 11.0 × 4.2; each module 12.2 × 3.66 × 4.2; power module 12.2 × 3.66 × 4.2 |
| Gross shipped mass, default preset *(config)* | 2.2 t | 4.6 t | 9.0 t | 14.7 t | 109 t total (≈ 25–30 t per module as shipped) |
| Gross mass, maximum configuration *(config)* | 2.2 t | 4.6 t | 10.5 t | 17.3 t | ≈ 125 t total |
| Service voltage *(config)* | 208/240 V 1φ | 208 V 3φ (208Y/120) | 480 V 3φ (480Y/277) | 480 V 3φ (480Y/277) | **12.47 kV (or 13.8 kV) MV service** → 2 × 2,500 kVA pad-mount transformers (2N) → 480Y/277 V |
| Customer disconnect / feeder breaker, default preset *(config)* | 50 A | 150 A | 225 A | 400 A | Utility primary metering; MV loop-feed switch; 3,000 A per 480 V main (4,000 A bus) |
| Feeder breaker, maximum configuration *(config)* | 50 A | 150 A | 400 A | 1000 A | 2 × 3,000 A mains (2N) |
| Total electrical demand, default preset *(config)* | 9.4 kVA | 42.6 kVA | 135 kVA | 224 kVA | 1,766 kW at 1,600 kW IT (≈ 1,960 kVA); 2,250 kVA at 2,000 kW IT |
| Heat rejected outdoors (≈ total kW) | 9 kW | 41 kW | 128 kW | 212 kW | 1,770–2,200 kW via adiabatic dry coolers |
| Outdoor noise sources | Cabinet AC condenser | In-row condensers (2–3) | In-row condensers (3–6) or dry cooler | Dry cooler bank, CDU pumps, generator | Adiabatic dry cooler bank (8–12 fans), 3 × 1,250 kW generators (test runs), transformers (hum) |

## 2. Pad and foundation

| Requirement | BEN 5 | BEN 30 | BEN 150 | BEN 500 | BEN 2000 | Who provides |
| --- | --- | --- | --- | --- | --- | --- |
| Pad plan size (unit + 1.0 m apron all round, + equipment yard) | 2.5 × 2.5 m | 5.0 × 4.5 m + condenser yard 3 × 3 m | 8.0 × 4.5 m + condenser/dry cooler yard 6 × 3 m | 14.5 × 4.5 m + dry cooler yard 12 × 4 m + generator pad per vendor | **Hall slab 40 × 14 m**; power module slab 14 × 6 m; MV pad 8 × 6 m with oil containment; generator pad 20 × 8 m with containment and fuel tanks; plant yard 30 × 10 m for adiabatic coolers and water treatment; total fenced site ≈ 70 × 45 m | Customer civil (or Schreiber AI turnkey) |
| Pad type and thickness | 150 mm reinforced slab, or 4 precast piers | 200 mm reinforced slab on 150 mm compacted base, **or** 4 reinforced concrete piers 600 × 600 mm at corner castings to frost depth | 200 mm slab or 4 piers (6 piers if mid-anchors required by wind calc) | 250 mm slab or 6–8 piers; check bearing: corner loads up to 45 kN each | 250–300 mm slab-on-grade with grade beams under module rails (line load ≈ 25 kN/m), designed from the geotechnical report; frost-protected shallow foundation in `cold` | PE-stamped drawing supplied by Schreiber AI per site soil (allowable bearing ≥ 100 kPa assumed; geotech required for BEN 2000) |
| Level tolerance | ±6 mm across pad | ±6 mm between corner castings (containers twist; doors will not seal if out of level) | ±6 mm | ±6 mm | ±5 mm along module rails (joints will not seal if out of level) | Surveyed at H16 |
| Anchor points | 4 × M16 chemical anchors into slab | 4 × cast-in twist-lock bases or weld plates at corner castings (ISO 1161 pattern) | 4 (+2 mid) twist-lock bases / weld plates | 6–8 twist-lock bases / weld plates | Cast-in embed plates at 3 m centres under each module rail; welded hold-downs per seismic category | Embeds supplied by Schreiber AI; set by civil contractor to ±10 mm |
| Elevation | Pad top ≥ 150 mm above grade; ≥ 300 mm above base flood elevation | same | same | same | same; H2/H3 adds a 600 mm plinth on every tier | Customer |
| Drainage | Grade away 2 %; condensate/CDU drain to a trapped drain or dry well | same | same + glycol drip tray drain | same | Hall floor drains to trapped sumps with leak detection; cooler bleed to sanitary sewer (not storm); transformer and generator containment per SPCC | Customer |
| Frost | Piers to local frost depth in `cold` climate | same | same | same | Grade beams to frost depth or insulated slab edge | Customer |

## 3. Setbacks and clearances

| Item | Requirement | Reason |
| --- | --- | --- |
| Door side | 2.5 m clear for door swing, egress and equipment movement | OSHA egress, rack delivery |
| Condenser / dry cooler side | ≥ 1.5 m from container wall and ≥ 2.0 m from any wall or fence; no recirculation from another unit's discharge; nothing above the fan discharge | Capacity: recirculated hot air is the most common cause of lost capacity |
| Property line | Distance such that predicted sound level meets the local ordinance (see section 9); typical ≥ 15 m residential, ≥ 5 m industrial; BEN 2000 ≥ 50 m residential (≥ 25 m with barrier) | Noise |
| BEN 2000 hall | Fire separation ≥ 10 m to other buildings or 2-hour rated wall; 6 m fire lane on two sides; MV pad ≥ 3 m from the hall with utility clearances (typically 3 m front, 1 m sides); generators ≥ 6 m from hall air intakes; fuel tanks per NFPA 30 Table 22.4.1.1 | Fire code, utility rules, exhaust |
| Buildings / combustibles | ≥ 3 m to other structures or per local fire code; ≥ 6 m to fire apparatus lane on one long side | Fire code, access |
| Generator | Per manufacturer: typically ≥ 1.5 m from the container, ≥ 1.5 m from openings, exhaust away from doors and air intakes; fuel tank per NFPA 30/37 and local code | Exhaust, fire |
| Overhead | No power lines within 3 m horizontally of crane path; nothing above the unit (snow slide, roof drip) | Crane safety, roof |

## 4. Crane and delivery access

| Item | Requirement |
| --- | --- |
| Delivery vehicle | Flatbed or step-deck; high-cube overall height on a standard trailer ≈ 4.4 m — the route must clear 4.5 m. Customer confirms gate width ≥ 3.5 m, turning radius for a 16 m (BEN 30/150) or 21 m (BEN 500) tractor-trailer, surface for 40 t axle loads. **BEN 2000:** four over-width loads (3.66 m wide, 4.2 m high on a lowboy ≈ 4.9 m overall), escorts and state permits; gate ≥ 5 m; yard for a 100 t crane to set all modules from one or two positions |
| Crane | Mobile crane sized for the gross mass at the required radius (BEN 150 at 9 t and 12 m radius ≈ 60–80 t crane; BEN 500 at 15–17 t ≈ 100–130 t crane). Firm, level outrigger ground; outrigger mats. Lift by all four top corner castings with spreader bar only |
| Alternative | BEN 5 and BEN 30 can be set with a telehandler/forklift of adequate capacity using the forklift pockets (BEN 30) or skid (BEN 5) |
| BEN 2000 crane | **100 t all-terrain crane** (module ≈ 30 t at up to 15 m radius), engineered lifting lugs and a four-leg spreader frame supplied with the modules; 3-day set for three hall modules and the power module; crane pad bearing ≥ 200 kPa on mats |
| Who | Customer provides access and permission; Schreiber AI logistics books the crane unless the customer prefers their own rigger (then the lift plan is still reviewed by us, W17) |

## 5. Utility service

| Item | BEN 5 | BEN 30 | BEN 150 | BEN 500 | BEN 2000 |
| --- | --- | --- | --- | --- | --- |
| Voltage / phases | 208 or 240 V, 1φ, 3-wire + ground | 208Y/120 V, 3φ, 4-wire + ground | 480Y/277 V, 3φ, 4-wire + ground | 480Y/277 V, 3φ, 4-wire + ground | **Medium voltage 12.47 kV (or 13.8 kV) 3φ** from the utility with primary metering; customer-owned 15 kV class loop-feed pad-mount switch, 2 × 2,500 kVA pad-mount transformers (2N) to 480Y/277 V |
| Customer-provided disconnect within sight of the unit, rated *(config `service_breaker_a`)* | 50 A | 150 A | 225 A (default) to 400 A (max) | 400 A (default) to 1000 A (max) | MV switch with fused ways; 480 V mains 2 × 3,000 A in the power module (we supply) |
| Feeder conductors (customer side, NEC 310.16 75 °C Cu) | 8 AWG | 1/0 AWG | 4/0 AWG (225 A) / 600 kcmil or 2 × 3/0 (400 A) | 600 kcmil (400 A) / 3 × 400 kcmil (1000 A) | MV: 15 kV 1/0 Al or Cu EPR cable in concrete-encased duct bank (utility spec); LV: bus duct 3,000 A per transformer to switchgear, ≤ 15 m |
| Available fault current at the disconnect | Required from utility before shipping; our SCCR is 65 kA at 480 V, 65 kA at 208/240 V; higher values need current-limiting fuses — tell us early |  |  |  |
| Metering | Utility meter at customer switchgear (normal) or at the unit (tell us; changes to NEC Art. 230 service rules) |  |  |  |
| Generator (if selected) | n/a | n/a | 150–250 kW diesel/natural gas, customer gas service or diesel tank | 250–750 kW, sub-base tank; SPCC applies ≥ 1,320 gal | Standard: **3 × 1,250 kW N+1, 48 h fuel** (≈ 10,500 US gal diesel in UL 142 double-wall sub-base or bulk tank); PE-certified SPCC plan; fuel delivery access for a 30 t tanker |
| Power quality | Voltage within ±10 %, frequency ±1 Hz; harmonics per IEEE 519 at PCC (we provide active-front-end UPS; report THD at SAT) |  |  |  |
| Who | Customer's electrical contractor installs the disconnect and feeder; Schreiber AI's licensed sub terminates at the unit |  |  |  |

## 6. Grounding electrode system

| Item | Requirement |
| --- | --- |
| Electrode | Ground ring (≥ 6 m of 2 AWG bare copper, 750 mm deep around the pad) **or** two 3 m rods ≥ 1.8 m apart, bonded to the building electrode system if one exists (NEC 250.50) |
| Target resistance | ≤ 25 Ω code minimum; **≤ 5 Ω recommended** for IT and lightning performance; tested by fall-of-potential before set-down (H16) |
| Connection to unit | Two 2/0 AWG bonding conductors to the unit's main bonding bar (we provide the lugs at diagonally opposite corners) |
| Lightning | Site NFPA 780 risk assessment where the climate or exposure indicates (high_altitude, open sites); air terminals are an option |
| Who | Customer's electrical contractor; Schreiber AI verifies |

## 7. Fiber / ISP and controls connectivity

| Item | Requirement |
| --- | --- |
| Conduit | Two 50 mm conduits (one spare) from the customer's demarcation to the unit's communications entry plate, with pull strings, sealed against water and rodents |
| Service | Customer orders the circuit(s); single-mode fiber preferred; diverse routes for 2N profiles. Lead time 60–120 days — order at H3 |
| Remote support (optional) | One outbound-only internet path for the edge computer (can be LTE/5G on our modem); no inbound ports required. Can be disabled for air-gapped sites |
| Time | The edge computer uses SNTP; GPS time source option for air-gapped sites |
| Who | Customer |

## 8. Water, drain and fluids (liquid-cooled or RDHx options; condensate for all DX)

| Item | Requirement |
| --- | --- |
| Condensate (DX units) | Gravity to a trapped drain or dry well; ≥ 25 mm line; heat-traced in `cold` climate. Volume at design humidity: up to 20 L/day (BEN 150, hot_humid) |
| Make-up water (dry cooler with adiabatic pad, option) | Potable or softened water, 15–20 L/min at 2 bar during peak; backflow preventer per local plumbing code |
| **BEN 2000 adiabatic coolers** | Make-up water **2–8 m³/day per 1,000 kW on hot days, zero in dry mode** (below ≈ 28 °C dry bulb); peak flow 60–100 L/min at 2–3 bar; water quality: hardness < 200 mg/L CaCO₃ or softener supplied; 3-day storage tank option where supply is uncertain; bleed/blow-down 20–30 % of make-up to **sanitary** sewer; backflow preventer; water treatment skid and ASHRAE 188 water management plan (`MAINTENANCE.md`) |
| Glycol loop fill | Closed loop filled by Schreiber AI (propylene glycol 30–50 % by climate); no site water connection needed; drain containment 200 L drip tray |
| Drain | Floor drain or dry well sized for a full-loop dump (BEN 500 CDU loop ≈ 400–600 L; BEN 2000 CDU and cooler loops ≈ 6,000–8,000 L, drained to a holding tank) |
| Who | Customer plumbing contractor |

## 9. Noise

| Item | Requirement |
| --- | --- |
| Customer provides | The local ordinance limits (day/night, dBA at property line) and the distance from the equipment yard to the nearest property line and nearest dwelling |
| Schreiber AI provides | A predicted level at the property line from the selected equipment's sound power, with the barrier/low-noise options if the prediction is within 3 dB of the limit. BEN 2000: generators in Level 2 (≤ 75 dBA at 7 m) enclosures, adiabatic coolers with EC fans ≈ 65 dBA at 10 m per bank, night set-back; expect ≥ 50 m to a residential property line without a barrier wall, ≥ 25 m with one |
| Verified by | Acoustic survey at SAT (E10) |

## 10. Permits and who pulls them

| Permit | Typical need | Who pulls | Notes |
| --- | --- | --- | --- |
| Zoning / land use | Yes for 30/150/500 (accessory structure); often no for BEN 5; **BEN 2000: principal structure, site plan approval** | Customer | Setbacks, height, screening |
| Building permit (structure, foundation, anchorage) | Yes for 30/150/500; **BEN 2000: full building permit (IBC Group B or F-1) plus state modular-building approval** | Customer's contractor or Schreiber AI as agent (we provide PE drawings) | AHJ decides Group U vs other occupancy; see `COMPLIANCE.md` §6 and §14; BEN 2000 plan review 8–16 weeks |
| Electrical permit | Yes | Licensed electrical sub (ours for the unit, customer's for the feeder) | Two permits are common: one for the site feeder, one for the unit hook-up |
| Mechanical / refrigeration permit | Yes where DX or glycol piping is installed on site | Licensed HVAC sub | Refrigerant quantity declared |
| Fire alarm / suppression permit and plan review | Yes for 30/150/500 | Licensed fire protection contractor | Fire marshal plan review 4–8 weeks |
| Generator: air permit / registration, fuel tank permit | If generator selected | Customer (we provide engine certification and tank data) | Emergency-engine rules; SPCC ≥ 1,320 gal |
| Utility interconnection (solar/export only) | off_grid with PV paralleling | Customer with our documents | Art. 705 |
| **MV service application** (BEN 2000) | Always | Customer, with our load letter and single-line | Filed at order; 26–52 weeks utility lead time; easement for utility equipment |
| Stormwater construction permit (NPDES CGP) | BEN 2000 (disturbance > 0.4 ha) | Customer civil | SWPPP before mobilisation |
| Water supply and sewer discharge (BEN 2000) | Always | Customer | Make-up water tap size, bleed discharge permit |
| Stormwater / grading | Site dependent | Customer civil | |

## 11. Security fencing and lighting

| Item | Requirement |
| --- | --- |
| Fence | 2.4 m chain-link or better with locked gate around the unit and equipment yard; healthcare/public_sector: anti-climb and camera coverage per their security plan |
| Lighting | ≥ 50 lux at the door and equipment yard, on a photocell; dark-sky compliant where required |
| Access control | Our door has a badge reader and camera on the controls LAN; customer decides who holds badges |
| Signage | Hazard placard (NFPA 704), "authorised personnel only", arc-flash, refrigerant/agent notices — supplied with the unit |

## 12. Environmental and climate checks (customer confirms, we design to)

| Check | Value needed | Where it goes |
| --- | --- | --- |
| Climate package selected | one of temperate / hot_arid / hot_humid / cold / coastal / high_altitude | `Config.climate` |
| FEMA flood zone | Zone letter and base flood elevation | Pad elevation |
| Design wind speed (ASCE 7 site-specific) and exposure category | m/s or mph, B/C/D | Anchorage calc (config default by climate: 47–67 m/s) |
| Ground snow load | kPa or psf | Roof and dry-cooler structure |
| Seismic design category | A–F | Anchorage and rack bracing |
| Site altitude | m above sea level | Fan and generator derate (high_altitude) |
| Wildfire interface | yes/no | Ember-resistant louvres, defensible space |
| Corrosivity confirmation | distance to salt water, industrial emissions | ISO 9223 class (C2–C5) coating system |
| Hardening level | H1 standard / H2 severe environment / H3 hardened (`Config.hardening`); the config recommends H2 for coastal, hot_arid, hot_humid, cold and high_altitude and offers H3 for public_sector | Envelope package, flood plinth, ballistic/forced-entry/shielding options; the hose test E14 is run at every level |
| Water availability (BEN 2000) | supply capacity L/min, hardness, drought restrictions, sewer discharge rules | Adiabatic vs dry vs chilled-water selection |

## 13. Delivery route

| Item | Requirement |
| --- | --- |
| Route survey | Customer confirms bridges ≥ 4.5 m, no weight-restricted bridges below 40 t, gate and yard turning space; Schreiber AI logistics performs a desktop route survey and, for BEN 500, a physical survey |
| Permits | Over-height/over-dimension permits are obtained by the carrier; pilot cars where required |
| Timing | Delivery window agreed 2 weeks ahead; crane and rigger booked by us; customer provides site contact and access |

## 14. Sign-off

| Role | Name | Signature | Date |
| --- | --- | --- | --- |
| Customer authorised representative | | | |
| Customer's electrical contractor (sections 5, 6) | | | |
| Schreiber AI engineering | | | |
| Schreiber AI compliance | | | |

By signing, the customer confirms the values provided are correct and that permits will be pulled by the parties named in section 10. Changes after signature are handled as change orders and may move the delivery date.

## 15. Rev 2 tiers: BEN 1, BEN 300 and BEN 700 (added 2026-11-09)

*(amended 2026-11-09: the 40 ft dense tier was renamed BEN 1000 → BEN 700 after the layout check, `docs/REV2_DECISION.md` §2a)*

This section is signed with section 14. For **BEN 1** it replaces sections 2–6, 8, 10–13: a mini rack is plugged in indoors and needs no pad, crane, utility service, grounding electrode or permit. For **BEN 300** and **BEN 700** sections 2–14 apply as for BEN 150 and BEN 500, with the values below. Values are printed from the Rev 2 configuration presets (`python -m ben_engine.config --tier <t> --json`, `docs/DENSITY.md`, 2026-11-09) and are re-confirmed from the frozen configuration at engineering release.

| Item | BEN 1 | BEN 300 | BEN 700 |
| --- | --- | --- | --- |
| Enclosure | Indoor mini rack: rack10 = 10-inch 8U desk or shelf rack (≤ 0.6 kW IT); cab12 = 19-inch 12U sound-damped office cabinet (≤ 1.5 kW IT) | 20 ft high-cube ISO-frame module, liquid-first, NEMA 4X / IP66 | 40 ft high-cube ISO-frame module, liquid-first, NEMA 4X / IP66, heat-rejection skid alongside |
| Location | Office, closet, back room or shelf; indoors, dry, 15–30 °C room air, not in a bathroom, kitchen or unheated space | Outdoor pad | Outdoor pad plus a heat-rejection skid yard |
| Pad plan size (unit + apron + yard) | n/a — floor or shelf space: rack10 about 0.30 × 0.35 m on a shelf or desk; cab12 about 0.60 × 0.80 m floor space plus 0.6 m clear in front | 8.0 × 4.5 m + dry-cooler / heat-rejection skid 2.4 × 2.6 m set 1.5 m off the blind end (unit + gap + skid about 10.0 × 2.6 m = 25.9 m², `docs/DENSITY.md`) | 14.5 × 4.5 m + heat-rejection skid 4.8 × 2.6 m set 1.5 m off the blind end (unit + gap + skid about 18.5 × 2.6 m = 48.1 m², `docs/DENSITY.md`) + battery enclosure pad where the NFPA 855 spacing requires it (`COMPLIANCE.md` §19) |
| Pad type and thickness | n/a — floor or shelf load: rack10 loaded about 38 kg (a sturdy shelf rated ≥ 2 × that mass); cab12 loaded about 136 kg (1.1 kW preset) to 176 kg (1.5 kW) on four feet (ordinary office floor; tell us if it is a raised floor or a mezzanine) | 200 mm slab or 4–6 piers; corner loads from the gross mass 9.4 t (9,410 kg preset); PE-stamped per site soil | 250 mm slab or 6–8 piers; corner loads from the gross mass 19.3 t (19,300 kg preset); PE-stamped per site soil |
| Anchor points | Anti-tip wall bracket (cab12) or shelf strap (rack10), supplied | 4 (+2 mid) twist-lock bases / weld plates | 6–8 twist-lock bases / weld plates |
| Voltage / phases | 120 V, 1φ, NEMA 5-15R (rack10) or NEMA 5-20R (cab12) receptacle within 1.5 m of the unit | 480Y/277 V, 3φ, 4-wire + ground | 480Y/277 V, 3φ, 4-wire + ground (MV service and a customer transformer are common at this size: tell us at survey) |
| Customer-provided disconnect | n/a — a **dedicated** 120 V branch circuit: **15 A for rack10, 20 A for cab12**, nothing else on it (NEC 210.23(A) 80 % rule, `COMPLIANCE.md` §18) | Rated 600 A from the configuration (509 A calculated at 300 kW) | Rated 1,200 A from the configuration (1,186 A calculated at 700 kW; ground-fault protection and arc-energy reduction apply at this rating, `COMPLIANCE.md` §19) |
| Feeder conductors | n/a — the existing building wiring for a 15 A or 20 A circuit (14 AWG / 12 AWG Cu) | Per NEC 310.16 75 °C Cu for the breaker rating; parallel sets above 400 A | Per NEC 310.16 75 °C Cu for the breaker rating, parallel sets or bus duct |
| Generator (if selected) | n/a | 300–500 kW class, sub-base tank; SPCC applies ≥ 1,320 gal | 750–1,000 kW class; SPCC; fuel delivery access |
| Total electrical demand, default preset | rack10 about 0.68 kVA; cab12 about 1.24 kVA at the 1.1 kW preset, 1.68 kVA at 1.5 kW (IT + UPS losses and charging + fans) | 338 kVA (321.5 kW) | 789 kVA (749.5 kW) |
| **Heat released to the room / rejected outdoors** | **To the room**, at full IT load including UPS and fan losses: rack10 about **2,210 BTU/h** (649 W at 0.6 kW IT); cab12 about **4,020 BTU/h** (1,177 W at the 1.1 kW preset) and **5,460 BTU/h** (1,599 W at 1.5 kW) | Outdoors through the skid, about 322 kW at full load (liquid loop 270 kW + trim loop 33 kW at the coils, plus pump, chiller and UPS losses); W45 dry-cooler bank sized 311 kW + 33 kW trim chiller | Outdoors through the skid, about 750 kW at full load (liquid loop 630 kW + trim loop 77 kW at the coils, plus losses); W45 dry-cooler bank sized 725 kW + 77 kW trim chiller |
| Room heat removal (BEN 1) | Either (a) the room's air conditioning has spare capacity ≥ the heat figure above, **or** (b) a vent path to a conditioned space: a door or wall grille plus a quiet exhaust fan moving ≥ 120 CFM (rack10) or ≥ 300 CFM (cab12), sized for a 10 K rise. A closed closet with neither is **not acceptable** (risk R41) | n/a | n/a |
| Ventilation clearance (BEN 1) | Intake (front) and exhaust (rear or top) unobstructed: ≥ 0.15 m behind and above the cabinet, nothing stored against the vents; 0.6 m in front for the door and service | n/a (sections 3, 9) | n/a (sections 3, 9) |
| Water and fluids | None. Any liquid cooling is sealed inside the AI box by its maker | Closed W45 loop filled by Schreiber AI (volume not yet computed: set by the CDU secondary hold-up, the rear-plenum header and the skid piping; stated on the FAT fill record; design flow 388 L/min); drain or holding tank for a full-loop dump; no site water for dry-cooler-only rejection | Closed W45 loop (volume not yet computed, as for BEN 300; design flow 904 L/min); drain or holding tank; heat-reuse port connection if the customer has an offtaker; make-up water only if an adiabatic option is chosen |
| Internet and network | Business broadband (any ISP), one Ethernet drop to the cabinet; static IP optional; an outbound-only path for BEN Care remote support (can be disabled) | Section 7 | Section 7; diverse fibre routes recommended at this size |
| Delivery and access | Ships by parcel or freight on a pallet; doorways ≥ 0.8 m; cab12 needs two people or a hand truck; no crane | Section 4 (BEN 150 values; heavier rack set-in at site if R51 applies) | Section 4 (BEN 500 values; heavier; racks may be set in at site) |
| Permits | **None for a plug-in unit.** A new dedicated circuit, if needed, is ordinary electrical work by the customer's electrician under local rules | Section 10 (as BEN 150) | Section 10 (as BEN 500), plus the NFPA 855 battery review and the utility's review of a 1,200 A service |
| Noise | Estimated 45–47 dBA at 1 m (cab12 door closed: 45 dBA up to about 1.17 kW IT, 46.7 dBA at 1.5 kW; rack10 about 45 dBA at 0.6 kW, its own gear's noise); a source-level model, measured at handover (E21) | Section 9; dry-cooler prediction at quote | Section 9; skid prediction at quote |
| Who | Customer provides the circuit, the room, the vent path and the network drop; Schreiber AI ships, sets up and hands over (`PROCESS_FLOW.md` §6) | As sections 2–14 | As sections 2–14 |
