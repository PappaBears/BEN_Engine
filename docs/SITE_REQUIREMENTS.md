# BEN Engine — Site Requirements (the customer signs this before we ship)

**Owner:** Schreiber AI engineering. **Purpose:** this is hold point **H3** in `docs/PROCESS_FLOW.md`. Nothing is built for a specific site until this document is filled in and signed by the customer and by Schreiber AI. It is written as a form: every line is either a value we need from the customer, a value we provide from the configuration, or a tick box.

Numbers marked *(config)* come from `software/ben_engine/config.py` for the tier's default preset (`Config.preset(tier)`); the unit-specific values are printed from the frozen configuration at engineering release and replace them.

## 1. Unit summary (filled from the configuration)

| Item | BEN Micro | BEN 10 | BEN 20 | BEN 40 |
| --- | --- | --- | --- | --- |
| Enclosure | Outdoor 24U NEMA 3R cabinet on skid | 10 ft high-cube ISO | 20 ft high-cube ISO | 40 ft high-cube ISO |
| External L × W × H (m) | 1.20 × 1.00 × 1.80 | 2.991 × 2.438 × 2.896 | 6.058 × 2.438 × 2.896 | 12.192 × 2.438 × 2.896 |
| Gross shipped mass, default preset *(config)* | 2.2 t | 4.6 t | 9.0 t | 14.7 t |
| Gross mass, maximum configuration *(config)* | 2.2 t | 4.6 t | 10.5 t | 17.3 t |
| Service voltage *(config)* | 208/240 V 1φ | 208 V 3φ (208Y/120) | 480 V 3φ (480Y/277) | 480 V 3φ (480Y/277) |
| Customer disconnect / feeder breaker, default preset *(config)* | 50 A | 150 A | 225 A | 400 A |
| Feeder breaker, maximum configuration *(config)* | 50 A | 150 A | 400 A | 1000 A |
| Total electrical demand, default preset *(config)* | 9.4 kVA | 42.6 kVA | 135 kVA | 224 kVA |
| Heat rejected outdoors (≈ total kW) | 9 kW | 41 kW | 128 kW | 212 kW |
| Outdoor noise sources | Cabinet AC condenser | In-row condensers (2–3) | In-row condensers (3–6) or dry cooler | Dry cooler bank, CDU pumps, generator |

## 2. Pad and foundation

| Requirement | BEN Micro | BEN 10 | BEN 20 | BEN 40 | Who provides |
| --- | --- | --- | --- | --- | --- |
| Pad plan size (unit + 1.0 m apron all round, + equipment yard) | 2.5 × 2.5 m | 5.0 × 4.5 m + condenser yard 3 × 3 m | 8.0 × 4.5 m + condenser/dry cooler yard 6 × 3 m | 14.5 × 4.5 m + dry cooler yard 12 × 4 m + generator pad per vendor | Customer civil (or Schreiber AI turnkey) |
| Pad type and thickness | 150 mm reinforced slab, or 4 precast piers | 200 mm reinforced slab on 150 mm compacted base, **or** 4 reinforced concrete piers 600 × 600 mm at corner castings to frost depth | 200 mm slab or 4 piers (6 piers if mid-anchors required by wind calc) | 250 mm slab or 6–8 piers; check bearing: corner loads up to 45 kN each | PE-stamped drawing supplied by Schreiber AI per site soil (allowable bearing ≥ 100 kPa assumed; geotech if unknown) |
| Level tolerance | ±6 mm across pad | ±6 mm between corner castings (containers twist; doors will not seal if out of level) | ±6 mm | ±6 mm | Surveyed at H16 |
| Anchor points | 4 × M16 chemical anchors into slab | 4 × cast-in twist-lock bases or weld plates at corner castings (ISO 1161 pattern) | 4 (+2 mid) twist-lock bases / weld plates | 6–8 twist-lock bases / weld plates | Embeds supplied by Schreiber AI; set by civil contractor to ±10 mm |
| Elevation | Pad top ≥ 150 mm above grade; ≥ 300 mm above base flood elevation | same | same | same | Customer |
| Drainage | Grade away 2 %; condensate/CDU drain to a trapped drain or dry well | same | same + glycol drip tray drain | same | Customer |
| Frost | Piers to local frost depth in `cold` climate | same | same | same | Customer |

## 3. Setbacks and clearances

| Item | Requirement | Reason |
| --- | --- | --- |
| Door side | 2.5 m clear for door swing, egress and equipment movement | OSHA egress, rack delivery |
| Condenser / dry cooler side | ≥ 1.5 m from container wall and ≥ 2.0 m from any wall or fence; no recirculation from another unit's discharge; nothing above the fan discharge | Capacity: recirculated hot air is the most common cause of lost capacity |
| Property line | Distance such that predicted sound level meets the local ordinance (see section 9); typical ≥ 15 m residential, ≥ 5 m industrial | Noise |
| Buildings / combustibles | ≥ 3 m to other structures or per local fire code; ≥ 6 m to fire apparatus lane on one long side | Fire code, access |
| Generator | Per manufacturer: typically ≥ 1.5 m from the container, ≥ 1.5 m from openings, exhaust away from doors and air intakes; fuel tank per NFPA 30/37 and local code | Exhaust, fire |
| Overhead | No power lines within 3 m horizontally of crane path; nothing above the unit (snow slide, roof drip) | Crane safety, roof |

## 4. Crane and delivery access

| Item | Requirement |
| --- | --- |
| Delivery vehicle | Flatbed or step-deck; high-cube overall height on a standard trailer ≈ 4.4 m — the route must clear 4.5 m. Customer confirms gate width ≥ 3.5 m, turning radius for a 16 m (BEN 10/20) or 21 m (BEN 40) tractor-trailer, surface for 40 t axle loads |
| Crane | Mobile crane sized for the gross mass at the required radius (BEN 20 at 9 t and 12 m radius ≈ 60–80 t crane; BEN 40 at 15–17 t ≈ 100–130 t crane). Firm, level outrigger ground; outrigger mats. Lift by all four top corner castings with spreader bar only |
| Alternative | BEN Micro and BEN 10 can be set with a telehandler/forklift of adequate capacity using the forklift pockets (BEN 10) or skid (Micro) |
| Who | Customer provides access and permission; Schreiber AI logistics books the crane unless the customer prefers their own rigger (then the lift plan is still reviewed by us, W17) |

## 5. Utility service

| Item | BEN Micro | BEN 10 | BEN 20 | BEN 40 |
| --- | --- | --- | --- | --- |
| Voltage / phases | 208 or 240 V, 1φ, 3-wire + ground | 208Y/120 V, 3φ, 4-wire + ground | 480Y/277 V, 3φ, 4-wire + ground | 480Y/277 V, 3φ, 4-wire + ground |
| Customer-provided disconnect within sight of the unit, rated *(config `service_breaker_a`)* | 50 A | 150 A | 225 A (default) to 400 A (max) | 400 A (default) to 1000 A (max) |
| Feeder conductors (customer side, NEC 310.16 75 °C Cu) | 8 AWG | 1/0 AWG | 4/0 AWG (225 A) / 600 kcmil or 2 × 3/0 (400 A) | 600 kcmil (400 A) / 3 × 400 kcmil (1000 A) |
| Available fault current at the disconnect | Required from utility before shipping; our SCCR is 65 kA at 480 V, 65 kA at 208/240 V; higher values need current-limiting fuses — tell us early |  |  |  |
| Metering | Utility meter at customer switchgear (normal) or at the unit (tell us; changes to NEC Art. 230 service rules) |  |  |  |
| Generator (if selected) | n/a | n/a | 150–250 kW diesel/natural gas, customer gas service or diesel tank | 250–750 kW, sub-base tank; SPCC applies ≥ 1,320 gal |
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
| Condensate (DX units) | Gravity to a trapped drain or dry well; ≥ 25 mm line; heat-traced in `cold` climate. Volume at design humidity: up to 20 L/day (BEN 20, hot_humid) |
| Make-up water (dry cooler with adiabatic pad, option) | Potable or softened water, 15–20 L/min at 2 bar during peak; backflow preventer per local plumbing code |
| Glycol loop fill | Closed loop filled by Schreiber AI (propylene glycol 30–50 % by climate); no site water connection needed; drain containment 200 L drip tray |
| Drain | Floor drain or dry well sized for a full-loop dump (BEN 40 CDU loop ≈ 400–600 L) |
| Who | Customer plumbing contractor |

## 9. Noise

| Item | Requirement |
| --- | --- |
| Customer provides | The local ordinance limits (day/night, dBA at property line) and the distance from the equipment yard to the nearest property line and nearest dwelling |
| Schreiber AI provides | A predicted level at the property line from the selected equipment's sound power, with the barrier/low-noise options if the prediction is within 3 dB of the limit |
| Verified by | Acoustic survey at SAT (E10) |

## 10. Permits and who pulls them

| Permit | Typical need | Who pulls | Notes |
| --- | --- | --- | --- |
| Zoning / land use | Yes for 10/20/40 (accessory structure); often no for Micro | Customer | Setbacks, height, screening |
| Building permit (structure, foundation, anchorage) | Yes for 10/20/40 | Customer's contractor or Schreiber AI as agent (we provide PE drawings) | AHJ decides Group U vs other occupancy; see `COMPLIANCE.md` §6 |
| Electrical permit | Yes | Licensed electrical sub (ours for the unit, customer's for the feeder) | Two permits are common: one for the site feeder, one for the unit hook-up |
| Mechanical / refrigeration permit | Yes where DX or glycol piping is installed on site | Licensed HVAC sub | Refrigerant quantity declared |
| Fire alarm / suppression permit and plan review | Yes for 10/20/40 | Licensed fire protection contractor | Fire marshal plan review 4–8 weeks |
| Generator: air permit / registration, fuel tank permit | If generator selected | Customer (we provide engine certification and tank data) | Emergency-engine rules; SPCC ≥ 1,320 gal |
| Utility interconnection (solar/export only) | off_grid with PV paralleling | Customer with our documents | Art. 705 |
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

## 13. Delivery route

| Item | Requirement |
| --- | --- |
| Route survey | Customer confirms bridges ≥ 4.5 m, no weight-restricted bridges below 40 t, gate and yard turning space; Schreiber AI logistics performs a desktop route survey and, for BEN 40, a physical survey |
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
