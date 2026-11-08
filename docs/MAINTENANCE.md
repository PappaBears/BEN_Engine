# BEN Engine — Maintenance Schedule (outdoor units)

**Owner:** Schreiber AI operations. **Applies to:** BEN 5, BEN 30, BEN 150, BEN 500 in all climates. **Principle:** the box lives outdoors for 15 years; the equipment inside lives 10. Most failures start at the envelope (water, corrosion, seals) or in consumables (filters, batteries, capacitors). Remote checks catch trends; hands-on visits fix them.

Who does what — **R** remote by Schreiber AI operations (dashboard, analysis tools); **L** local technician (customer's or Schreiber AI field tech, trained to `TURNOVER.md` T3/T5); **S** certified subcontractor (licensed electrician, EPA 608 HVAC tech, fire suppression contractor, generator vendor, battery vendor); **C** customer IT. Where "S" appears a record from the sub is mandatory.

Intervals are the default for `temperate`. Climate add-ons (section 5) shorten some intervals.

## 1. Weekly (remote, 15 minutes) — R

| Subsystem | Check | Pass | If not |
| --- | --- | --- | --- |
| Controls | All Pods online and attested, `status` heartbeat < 60 s old, no Pod `errors[]`; mesh health: every Pod W has ≥ 2 router neighbours, link quality ≥ 2, no Pod on battery < 20 % | 100 % online and attested | Dispatch L to check Pod power / placement within 48 h; a Pod that stops attesting is replaced, not re-flashed |
| Thermal | Rack inlet max over the week vs ASHRAE class recommended limit; supply/return ΔT trend; `dP_aisle` within band | Inlet max < class recommended; dP within ±20 % of commissioning value | Investigate filter/containment; raise ticket |
| Cooling | Each unit's run hours balanced (N+1 rotation working); no repeated short-cycling; fan % at similar load unchanged | Run hours within 10 % | Check rotation logic; check unit alarms |
| Power | UPS SOC 100 %, no battery alarms, input/output voltages, PDU sum vs meter within 3 % (E9 check automated) | No alarms | Open ticket; schedule S if battery |
| Leak / door | No leak events; door events match the access log | Match | Investigate unmatched door opening (security) |
| Fire | Fire panel supervisory contact normal; detector trouble = 0 | Normal | Fire contractor call within 24 h |
| Drift | `analysis.py` drift report: redundant sensor pairs within 0.5 °C, dP tare offset drift < 1 Pa | Within | Trigger recalibration visit (see 6) |
| Security | Firmware hashes unchanged, no failed logins > threshold, backup job succeeded, patch status | Clean | Follow `CYBERSECURITY.md` incident steps |
| Weather | Forecast check for storms, heat, freeze events against site climate | — | Pre-storm checklist (section 5) |

## 2. Monthly — L (1–2 hours on site) with R review

| Subsystem | Task | Record |
| --- | --- | --- |
| Envelope | Walk-around: roof standing water, debris, coating damage, rust streaks, sealant cracks at penetrations, door gaskets, hinge/lock operation, drain outlets clear, skirt/pad gap for animals | Monthly form M1 with photos |
| Structure | Visual on anchor bolts/twist-locks, corner castings, cracked paint at welds (sign of movement) | M1 |
| Cooling | Inspect filters (replace if dP > 2× clean, or visibly loaded), condenser/dry-cooler coil face for debris and fin damage, condensate drain flow (pour test), refrigerant detector self-test | M1; filter change log |
| Power | Listen/smell at panels and UPS, UPS display event log review, battery cabinet temperature, PDU breaker positions vs directory, emergency light test button (30 s) | M1 |
| Generator (if fitted) | Exercise run 30 min at ≥ 30 % load (or per NFPA 110 8.4: monthly, ≥ 30 min), check fuel level, leaks, battery charger, block heater, oil/coolant level, transfer test if site allows | Generator log |
| Fire | Visual on agent cylinder pressure gauge, releasing panel normal, abort/EPO station unobstructed, detectors uncovered, signage intact | M1 |
| Controls | Visual on controls cabinet (door seal, heater/fan, indicator LEDs), cable glands tight, dP tubing undamaged | M1 |
| Housekeeping | No storage in the electrical vestibule or aisles; blanking panels present; cable brush grommets closed | M1 |

## 3. Quarterly — L + S

| Subsystem | Task | Who | Record |
| --- | --- | --- | --- |
| Cooling | Clean condenser/dry-cooler coils (soft brush and low-pressure fresh water, with fins direction), check fan blade balance/noise, belt/vibration where applicable, confirm each unit's standalone controller matches the PLC setpoints | L | Q1 form |
| Cooling (liquid) | CDU/RDHx: fluid sample for glycol %, pH (8–10 target), inhibitor level, visual for particulates; filter/strainer dP; check quick disconnects; pump seal weep | S (fluid lab) + L | Fluid report |
| Power | Battery (lithium) BMS report download: cell voltage spread, temperature spread, SOH; UPS self-test; ATS exercise under load if not covered by generator test | L (BMS), S if anomalies | Q1 |
| Envelope | Door gasket conditioning, lubricate hinges/locks, check roof sealant and coping screws, confirm roof drains/scuppers free | L | Q1 |
| Controls | Sensor spot-check with a calibrated handheld at two inlet points and the reference (`T_ref`) — within 0.5 °C; door and leak sensor functional test; relay outputs test via dashboard I/O test | L with R | Q1; I/O test CSV |
| Security | Rotate shared service credentials; review user list; test backup restore to a spare edge computer (annually full, quarterly file-level) | R + C | Q1 |

## 4. Semi-annual, annual, 3-year, 5-year

| Interval | Subsystem | Task | Who | Record |
| --- | --- | --- | --- | --- |
| **Semi-annual** | Fire | **NFPA 2001 Ch. 8 semi-annual inspection**: agent quantity/pressure, cylinder and actuator condition, nozzles unobstructed, hoses, enclosure integrity changes (new penetrations?), detection functional test | S (licensed fire contractor) | Contractor report |
| Semi-annual | Cooling | Refrigerant leak check (electronic detector at all joints and the ITE space detector calibration/bump); verify charge by superheat/subcool; AIM Act leak-rate record for appliances ≥ 15 lb | S (EPA 608) | Leak check form with technician cert number |
| Semi-annual | Power | Thermography of all panels, UPS, PDU and transformer terminations at ≥ 40 % load; capacitor bank visual (bulging/leak) | S (electrician with IR camera) | IR report |
| Semi-annual | Generator | Fuel polishing/sampling (diesel), coolant test, load test ≥ 30 min at ≥ 30 % | S | Report |
| **Annual** | Controls | **Sensor calibration (12 months, or earlier on drift trigger)**: all temperature channels against a traceable reference bath/dry block at 3 points, RH at 2 salt points or chamber, dP at zero and span against a micromanometer, 4–20 mA loop at 4/12/20 mA; new `cal_id` issued; uncertainty budget updated (`calibration.py`) | R + L (Schreiber AI field tech) | Calibration certificates |
| Annual | Controls | Pod firmware update (signed, OTA over Thread), edge computer OS patch roll-up (if not continuous) and TPM PCR baseline re-record, PLC firmware advisory review, full edge image backup, database backup verify, certificate expiry review; **mesh health review** (topology map, router Pod count, retry rate, channel interference scan) | R | Change record; hashes; mesh report |
| Annual | Controls | **BEN Controller panel thermography** at ≥ 40 % load (PSU terminals, relay bank, SPD, feeder landing) with the power IR survey; PLC battery / real-time-clock backup check (PLCnext buffer: replace per vendor, typically 3–5 yr); RevPi RTC cell on Lite | S (IR) + R | IR report; record |
| Annual | Power | Torque check of all feeder/bus terminations to the torque table (`BUILD_AND_WIRING.md`); breaker mechanical exercise; trip-unit settings vs study; SPD status; ground electrode resistance test; UPS battery capacity/runtime test (discharge to 50 %) | S | Torque log; test report |
| Annual | Fire | NFPA 72 annual test of detection (sensitivity test per 72 Table 14.4.3.2 method, VEWFD transport time), notification, supervision, monitoring path; enclosure integrity (door fan) test if any penetration changed | S | Record of inspection |
| Annual | Envelope | Coating survey (ISO 4628 rust grade), touch-up; sealant renewal where cracked; insulation check for condensation stains at liner joints; door hardware adjustment; roof walk | L, S (coatings) for C4/C5 | Annual form A1 with photos |
| Annual | Structure | Anchor bolt torque check; twist-lock condition; level check at corners (±6 mm); corner casting cracks | L | A1 |
| Annual | Cooling | Full performance check at load (repeat E3 reduced or compare to commissioning sweep); fan motor current; EC fan bearings; condensate pump test; dry cooler pad/adiabatic system descaling | S | Report |
| Annual | Compliance | Review compliance pack against code changes (AIM Act, NFPA 855, local adoption); update arc-flash labels if the utility changed anything; SPCC plan review | Compliance (R) | Review note |
| **3-year** | Power | Full UPS service: fans, DC capacitors inspection (replace per vendor, typically 5–7 yr), firmware; ATS contact inspection; generator battery replacement; coordination study review if site changed | S | Report |
| 3-year | Cooling | Replace EC fan units showing bearing noise; refrigerant filter-driers on service; glycol replacement or re-inhibit per lab; CDU pump seals | S | Report |
| 3-year | Controls | **Pod W battery replacement** (2 × AA LiFeS2; 3–5 yr depending on report rate and temperature; the dashboard predicts the date from the measured drain); replace Pt1000 strings showing drift > 0.3 °C after calibration; replace dP tubing; PLC backup battery; spare Pod rotation | R + L | Record |
| 3-year | Fire | Clean agent cylinder hydrostatic test schedule check (5 yr container, 12 yr DOT for most); detector replacement per vendor life | S | Report |
| **5-year** | Power | UPS capacitor and fan replacement (if not done); lithium battery SOH review — replace modules < 80 % SOH or per vendor; thermography baseline reset | S | Report |
| 5-year | Envelope | Full recoat of exposed steel in C4/C5 climates (C3: spot repair); roof membrane/coating renewal; replace door gaskets and all penetration sealant; insulation core sample at one hidden location if condensation signs | S (coatings) | Report |
| 5-year | Structure | PE inspection of modified frame welds and anchorage (visual + MT on reinforced openings); re-level | PE / CWI | PE letter |
| 5-year | Cooling | Dry cooler coil replacement assessment (C5 coastal), DX compressor condition (run hours, oil analysis for larger units) | S | Report |
| 5-year | Fire | Clean agent cylinder hydrostatic test / requalification; full discharge test is **not** performed (door fan test substitutes) | S | Report |
| 5-year | Controls / IT | Edge computer refresh assessment (industrial PC: 7–10 yr, OnLogic longevity programme) with TPM re-enrolment and database migration; Pod W second battery change; Pod certificate re-issue (5-year validity); PLC I/O module assessment | R + L | Record |

## 5. Climate add-ons

| Climate | Add-on tasks | Interval change |
| --- | --- | --- |
| **hot_arid** (sand/dust) | Blow out or replace pre-filters; inspect condenser fins for sand erosion; clean intake hoods and sand traps; check door seals for grit; check roof coating SRI (dust film lowers reflectivity — rinse) | Filters monthly → **bi-weekly in dust season**; coil clean quarterly → **monthly** |
| **hot_humid** | Check dew-point alarm history; inspect liner joints and door thresholds for condensation; test door-sweep heaters; check vapour barrier at any new penetration; mould inspection; condensate line flush with biocide tablet | Envelope monthly items done with extra attention; condensate flush **monthly** |
| **cold** | Freeze protection: heat trace continuity and thermostat test before first frost; glycol % verified ≥ design before winter; crankcase heaters confirmed; snow removal from roof when > design load (post the load in kg/m² on the door), clear dry cooler and louvres of snow and ice, door seal de-icing (silicone), battery heater function (lithium charging below 0 °C is inhibited by BMS — verify alarms); economizer damper not frozen | **Pre-winter checklist (October)** and **post-storm checks**; glycol sample semi-annual |
| **coastal** (C5, salt fog) | Fresh-water rinse of condenser/dry cooler coils and exposed steel; inspect 316 fasteners for crevice corrosion; check coating edges and cut-outs; sacrificial anodes on any buried steel; louvre and hinge lubrication with marine grease | Coil rinse **monthly**; coating survey **semi-annual**; full recoat assessment 3-year |
| **high_altitude** | UV inspection of gaskets, cable jackets and coatings; fan performance vs altitude-corrected curve; generator derate check; lightning protection system continuity (NFPA 780 annual) | UV items annual; LPS test annual |
| All, **pre-storm (hurricane/high wind)** | Close and latch louvre storm covers, secure dry cooler, verify door tie-backs, top up fuel, confirm UPS SOC 100 %, pre-stage spares, verify flood barriers, photograph site | Event-driven |

## 6. Calibration interval rule (sensors)

- Default interval **12 months** for every channel.
- **Trigger-based early recalibration** when the weekly drift report shows: (a) redundant pair disagreement > 0.5 °C (Pt1000 strings on neighbouring Pods vs each other, or vs `T_ref`) for 3 consecutive weeks; (b) dP tare drift > 1 Pa or zero not reproducible at fan-off (E2 repeat); (c) RH disagreement > 3 %RH vs the calculated value from a second sensor; (d) a 4–20 mA loop reading outside 3.8–20.5 mA; (e) after any Pod replacement, firmware change affecting the RTD front end, or physical disturbance of a sensor.
- Interval may be **extended to 18 months** for a channel after two consecutive annual calibrations show drift < half the channel uncertainty (`PROTOCOL.md` k=2 values), by documented decision.

## 7. Spare parts list (on-site kit per unit)

| Item | Qty M / 10 / 20 / 40 | Why on site |
| --- | --- | --- |
| BEN Pod W, provisioned and calibrated as "spare, unassigned" (joins the mesh with its own certificate) | 1 / 1 / 2 / 3 | Pod failure = blind rack face; swap is 5 minutes, no wiring |
| BEN Pod E (room / outdoor variant) | 0 / 1 / 1 / 1 | Wired RS-485 path and Thread router |
| Pod W battery set (2 × AA LiFeS2) | 1 per Pod W | Replace at the predicted date |
| Edge computer (OnLogic Karbon 400, imaged, TPM enrolled) — Pro; RevPi Connect 4 imaged — Lite | 0 / 1 / 1 / 1 | Single point of monitoring; PLC keeps the interlocks meanwhile |
| MGM240P border router RCP (xG24 Explorer Kit) | 1 / 1 / 1 / 1 | Second radio already fitted on BEN 150/40 |
| Axioline F I/O module of each type (Pro) / RevPi DIO (Lite) | 1 each | PLC I/O failure |
| Pt1000 probe string, SDP810 sensor, Setra 264 (Pro), rope leak sensor 5 m, door reed | 1 each | Consumable sensors |
| QUINT4 24 VDC supply, interface relays, Class 2 fuses, panel fuses | 1 set | |
| Air filters (full set for all units) | 2 sets | Monthly change in dust |
| Condensate pump | 1 | Common failure |
| Fan unit (EC fan for in-row or dry cooler) | 0 / 1 / 1 / 2 | Lead time weeks |
| Refrigerant (service cylinder of the A1 refrigerant used) | 0 / 1 / 1 / 0 | Held by S, not on site, in most jurisdictions |
| Glycol concentrate (propylene) 20 L, test strips | 0 / 0 / 1 / 2 | |
| CDU strainer, pump seal kit, quick-disconnect caps | 0 / 0 / 1 / 1 | |
| UPS fan kit; spare breaker of each PDU size; fuses for SPD | 1 set | |
| Lithium battery module | 0 / 0 / 0 / 1 (vendor-held) | |
| Door gasket 10 m, sealant (polyurethane, UV stable), touch-up paint matched to coating system | 1 set | Envelope |
| Twist-lock / anchor hardware set | 0 / 1 / 1 / 1 | Relocation |
| Emergency light batteries, exit sign lamps | 1 set | |
| Smoke detector heads (spot and VEWFD filter) | 0 / 1 / 2 / 2 | |
| Laminated procedures, log forms, cable labels | 1 set | |

## 8. Record forms

All forms exist as PDF in the turnover package and as dashboard checklists (completing the dashboard checklist writes a signed record to the edge computer database and, for managed service, to Schreiber AI).

| Form | Content |
| --- | --- |
| **M1 Monthly envelope and systems walk** | Date, technician, weather; each monthly line with OK / note / photo reference; filter dP before/after; condensate test; emergency light test; generator run data (start time, load, duration, fuel) |
| **Q1 Quarterly** | Coil cleaning record; fluid sample ID and lab result; BMS export filename; sensor spot-check table (channel, handheld reading, Pod reading, difference); I/O test CSV reference |
| **A1 Annual** | Coating survey grid (one row per face), sealant map, anchor torque table, level readings, photos |
| **Calibration certificate** (per channel) | Channel, sensor serial, reference instrument and certificate number, points (reference, as-found, as-left), gain/offset, uncertainty budget, `cal_id`, technician, date, next due |
| **Refrigerant service record** | Appliance ID, refrigerant type and GWP, charge, technician EPA 608 cert #, leak check method and result, refrigerant added/recovered (kg), leak rate %/yr |
| **Fire system inspection** (contractor's NFPA 2001/72 form) | Attached as PDF; our form records receipt and open items |
| **Electrical maintenance record** | Torque checks (lug ID, specified, applied), IR images with ΔT, ground resistance, breaker exercise, UPS test |
| **Incident report** | Alarm ID, time, cause, action, time to normal, preventive action |
| **Entry log** | Who, when, purpose (dashboard logs badge events; paper form for badge failure) |

## 9. Entry procedure (non-permit space, written practice)

1. Check dashboard or door panel: no active fire, refrigerant, gas or leak alarm. If any — do not enter; call the alarm owner.
2. Open door fully and latch it; let purge ventilation run 2 minutes if the refrigerant detector showed any reading in the last 24 h.
3. Know the EPO, abort switch, exits and extinguisher locations.
4. Hearing protection inside the hot aisle above 85 dBA (signed). Arc-rated PPE per label when any panel cover is removed.
5. Nobody works alone on energised equipment. Lone entry for inspection is allowed with a check-in call before and after.
6. Leave with no tools, no storage in the vestibule, door latched, entry logged.
