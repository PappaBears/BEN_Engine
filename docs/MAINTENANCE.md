# BEN Engine — Maintenance Schedule (outdoor units)

**Owner:** Schreiber AI operations. **Applies to:** BEN 5, BEN 30, BEN 150, BEN 500 in all climates, plus the hall and plant items for BEN 2000 (section 4a) and the hardening add-ons for H2/H3 units (section 5a). **Principle:** the box lives outdoors for 15 years; the equipment inside lives 10. Most failures start at the envelope (water, corrosion, seals) or in consumables (filters, batteries, capacitors). Remote checks catch trends; hands-on visits fix them.

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
| **Semi-annual** | Envelope | **Gasket and seal inspection (every tier, every hardening level)**: door compression gaskets (no set > 30 %, no cracks), penetration gaskets and glands, drip edges, roof seams; positive-pressure fan ΔP within band; repair and re-test locally with a hose on any repaired seam | L | Semi-annual envelope form; photos |
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
| **3-year** | Envelope | **Hose test E14 repeat** (UL 50E type 4X method, `TEST_GUIDE.md`): whole envelope every 3 years and after any relocation or new penetration; pass = no water inside | L + SAI-Q witness | E14 record; warranty evidence (`WARRANTY_TERMS.md`) |
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

## 4a. BEN 2000 hall and plant items (in addition to sections 1–4, applied per module)

| Interval | Subsystem | Task | Who | Record |
| --- | --- | --- | --- | --- |
| Weekly (R) | Plant | Adiabatic cooler mode history (dry/wet hours), make-up water volume vs model, bleed conductivity, water treatment chemical level; generator fuel level and polishing status; transformer temperature and oil level alarms; UPS string load balance (2N: each string < 50 %); battery room gas detection normal; edge computer A/B replication healthy | R | Weekly plant report |
| Monthly (L) | Cooling plant | **Adiabatic cooler water treatment**: biocide dosing check, conductivity controller calibration, pad condition, sump cleanliness, drift eliminators, drain-down valve test (dry mode); make-up strainer | L + water treatment S | Water log (part of the ASHRAE 188 water management plan) |
| Monthly (L) | Generators | Exercise each of the 3 × 1,250 kW sets 30 min at ≥ 30 % load with a transfer (NFPA 110 8.4.2); fuel level, leaks, charger, block heater; fuel tank interstitial monitor | L | Generator log per set |
| Monthly (L) | Envelope | **Module joint seal inspection** from inside and roof: cover strips, sealant, drained cavity outlets clear, leak rope under joints dry, humidity Pods either side within 5 %RH of each other | L | M1 hall supplement with photos |
| Quarterly | Cooling plant | **Legionella control per ASHRAE 188 / Guideline 12**: Legionella culture sampling at the cooler sumps and make-up (action level ≥ 100 CFU/mL per CDC toolkit, disinfect and re-sample), heterotrophic plate count, water treatment vendor report; adjust programme | S (water treatment) | Sampling certificates in the water management plan |
| Quarterly | Power | Battery room: gas detection sensor bump test, ventilation interlock test, deflagration vent inspection, BMS export per cabinet, thermal imaging of string connections | L + S | Q1 power module |
| Semi-annual | Power | UPS string transfer: shift load to one string and back (maintenance bypass procedure, E16 reduced); switchgear tie-breaker exercise; ATS logic test with a simulated utility loss (generators start, no load transfer) | S (electrical) + R | E16 record |
| Annual | Generators | **Load bank test**: each set 2 h at 100 % rated (NFPA 110 8.4.2.3 where monthly runs did not reach 30 %; we do it regardless), plus one full-system test: utility open, all three sets start, N+1 proven with one set inhibited | S (generator vendor) | Load bank report; fuel consumed |
| Annual | Plant | Adiabatic cooler: descale and disinfect pads or replace (typically 2–3 yr life), coil cleaning, EC fan bearings, controls calibration of wet-bulb sensors; water management plan review and sign-off | S | Report |
| Annual | Envelope | Joint seal hose test (E15) on 1 of 3 joints by rotation (so every joint is tested every 3 years) and after any seismic event or module movement alarm | L + SAI-Q | E15 record |
| Annual | Power | MV: visual and thermography of pad-mount transformers and switch at load; transformer oil sample (DGA, moisture, dielectric) | S (NETA) | Report |
| **3-year** | Power | **MV gear maintenance** (NETA MTS): de-energise one transformer at a time (2N allows it), switch contact inspection and lubrication, cable terminations and elbows, insulation resistance, relay calibration, transformer TTR and power factor; switchgear breaker drawout and secondary injection test | S (NETA-accredited) | NETA report |
| 3-year | Envelope | Full E15 on all joints and E14 on each module; re-seal cover strips | L + SAI-Q | Records |
| 5-year | Power | UPS string capacitor/fan replacement by string (2N allows it live); battery SOH review per room | S | Report |
| 5-year | Plant | Generator major service (injectors, coolant system, exhaust bellows); fuel tank interior inspection (STI SP001) | S | Report |

## 4b. Forward architecture items (units with the 800 VDC option or the high-density liquid loop; study)

These rows apply only when `power_architecture: dc800` or `cooling: dlc_hd` is configured (`docs/FORWARD_ARCHITECTURE_DECISION.md`); intervals are the program's starting point and are revised from the test cell.

| Interval | Subsystem | Task | Who | Record |
| --- | --- | --- | --- | --- |
| Weekly (R) | DC bus | `IMD_kohm` trend (warn < 500 kΩ), `V_bus_pos` / `V_bus_neg` symmetry (bipolar) or return-to-earth voltage (unipolar), bus voltage inside the window, rectifier module alarms and load share, battery string SoC / SoH and cell spread | R | Weekly report |
| Weekly (R) | Liquid loop | Loop flow vs design, ΔT vs IT load (E20 reconciliation within 5 %), supply ≤ 45 °C, CDU pump hours balanced, make-up water volume, leak-sensor health, heat-reuse kWh | R | Weekly report |
| Monthly (L) | DC bus | **IMD test button** and alarm path to the controller; rectifier module filters; thermography of the bus joints, tap-offs and battery terminations at ≥ 40 % load (DC joints loosen like AC ones); battery string disconnect exercise | L + S (IR) | M1 forward supplement |
| Monthly (L) | Liquid loop | **CDU pump failover proof** (stop the duty pump, standby starts; E18 reduced); strainer / filter ΔP; drip trays dry; UQD connectors visual (weep); isolation-valve position feedback test without closing | L | M1 forward supplement |
| Quarterly | Liquid loop | **Leak-to-isolation test E19** on one rack by rotation (every rack within a year); water analysis (pH, conductivity, inhibitor, biocide, bacteria count per OCP coolant spec v1.3 / PG25); side-stream filter change | L + water treatment S | E19 record; water log |
| Quarterly | DC bus | DC arc-fault detector self-test; verify the convention label at every tap-off matches the configuration (`dc_convention`); torque spot-check 10 % of tap-off terminations | S (electrician) | Q forward supplement |
| Semi-annual | DC bus | Ground-fault injection E17 on both poles with a test resistor (IMD alarm, location, no trip); battery string capacity check (discharge to 50 % on the bus) and BMS export | S + R | E17 record |
| Annual | Liquid loop | Plate HX ΔP and approach check on the CDU and the heat-reuse HX; chemical clean or flush where ΔP > 1.3 × commissioning; dry-cooler coil clean; cold-plate inlet flow balance at the rack valves (±10 %); BTU meter calibration | S | Report |
| Annual | DC bus | Full torque check of bus, tap-offs, rectifier and battery terminations; DC MCCB mechanical exercise and secondary injection on the main; IMD calibration check against a reference resistor; arc-flash labels against the study | S (NETA) | Torque log; report |
| 3-year | DC bus / loop | Rectifier module capacitor / fan assessment per vendor; battery string SoH review (replace modules < 80 %); UQD connector seal replacement per vendor life; isolation-valve actuator spring test | S | Report |

## 5a. Hardening add-ons (H2 and H3 units)

| Level | Interval | Task | Who | Record |
| --- | --- | --- | --- | --- |
| H1–H3 | Semi-annual | **Gasket inspection** (section 4, first row) — mandatory for the envelope warranty | L | Form |
| H1–H3 | 3-year and after relocation | **Hose test E14** — mandatory for the envelope warranty | L + SAI-Q | E14 record |
| H2, H3 | Annual | **Sacrificial anode inspection**; **replace at 50 % consumed** (typically 2–4 years coastal, 5+ inland) on skids, plinth steel and any buried steel; check bonding of anodes | L | A1 supplement |
| H2, H3 | Semi-annual | C5-M coating survey (ISO 4628) with touch-up; stainless fastener crevice check; weather hood and sand-trap louvre cleaning; ePM1 filter change on ΔP | L | A1 |
| H2, H3 | Annual | Flood plinth: sealed penetrations, drain valve, flood sensor test; hurricane door hardware operation; snow guard anchorage | L | A1 |
| H3 | Semi-annual | **Ballistic panel inspection**: no impacts, delamination, water staining or corrosion at panel edges; fasteners present; vision panel clarity; any panel struck is replaced, never repaired; lot certificate retained | L | H3 form with photos |
| H3 | Annual | Forced-entry door assemblies: hinge pins, multi-point locks, strike wear, closer force; IK10 door skins for dents; mantrap interlock and two-factor reader test; tamper switches and PLC tamper alarm test; audit trail export from BEN Care | L + R | H3 form |
| H3 (shielded option) | Annual | **Shield integrity test**: shielding effectiveness per IEEE 299 at 3 frequencies (10 kHz H-field, 100 MHz, 1 GHz plane wave) at every door, vent and penetration group; pass ≥ 80 dB (or the value on the FAT certificate); door finger-stock contact check, waveguide vent inspection, filter insulation resistance | S (shielding vendor or EMC lab) | Shield test certificate |
| H3 | Quarterly | Tamper-evident seal audit on panels, conduit bodies and the controls cabinet against the seal register | L | Seal register |

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

| Item | Qty BEN 5 / 30 / 150 / 500 (BEN 2000: per module as BEN 500, plus plant spares below) | Why on site |
| --- | --- | --- |
| BEN Pod W, provisioned and calibrated as "spare, unassigned" (joins the mesh with its own certificate) | 1 / 1 / 2 / 3 | Pod failure = blind rack face; swap is 5 minutes, no wiring |
| BEN Pod E (room / outdoor variant) | 0 / 1 / 1 / 1 | Wired RS-485 path and Thread router |
| Pod W battery set (2 × AA LiFeS2) | 1 per Pod W | Replace at the predicted date |
| Edge computer (OnLogic Karbon 400, imaged, TPM enrolled) — Pro; RevPi Connect 4 imaged — Lite | 0 / 1 / 1 / 1 | Single point of monitoring; PLC keeps the interlocks meanwhile |
| MGM240P border router RCP (xG24 Explorer Kit) | 1 / 1 / 1 / 1 | Second radio already fitted on BEN 150/500 |
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
| BEN 2000 plant spares: cooler EC fan 2, adiabatic pad set 1, water treatment pump and probes 1 set, generator starting battery set 1, fuel filter kits 3, switchgear trip unit 1, MV fuses 1 set, UPS power module 1 per string, battery-room gas sensor 1, joint cover strip 12 m and sealant, edge computer 1 (third unit) | — | Plant items with lead times of weeks |
| H2/H3 spares: sacrificial anodes 1 set, ePM1 filters 2 sets, door gasket (hardened door profile) 10 m, finger-stock 5 m and shielded door gasket (H3 shielded), tamper seals 100, ballistic vision panel 1 | — | Hardening items are long lead |

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

## 10. BEN 1 mini rack — a schedule a tiny business can do (added 2026-11-09, Rev 2)

BEN 1 is indoors and has no envelope, refrigerant, generator or fire system, so sections 1–9 do not apply except the security checks in section 1. The owner or an office manager does the **L** tasks below in minutes, with no tools beyond a screwdriver; BEN Care (**R**) does the rest remotely and tells the owner by email when something needs a hand. Under a BEN Care plan Schreiber AI can do every task instead.

| Interval | Task | Who | Pass | If not |
| --- | --- | --- | --- | --- |
| Weekly (automatic) | BEN Care report: intake temperature trend, fan speed, UPS status and battery health, backup job result, firmware and patch status, unknown devices on the network | R | Green report email | Follow the one action named in the email |
| **Monthly** | **Filter look**: open the cabinet door (cab12) or look at the intake (rack10); if the filter is grey, rinse or replace it (spare in the kit). Check that nothing is stacked against the vents and the room vent or grille is open | L (5 min) | Filter light in colour; vents clear | Replace the filter; BEN Pod intake alarm (filter-clog, E24) is the backstop |
| Monthly | Look at the cords: UPS plugged straight into its dedicated wall receptacle, no extra power strips, nothing new added (R42, R45) | L (2 min) | As shipped | Remove the addition; call us for a change order |
| **Quarterly** | **UPS self-test**: press the test button (or BEN Care triggers it); the UPS switches to battery for about 10 s and back | L or R | Self-test passed; runtime estimate ≥ 80 % of the handover value (E23) | Battery replacement shipped (R47) |
| **Quarterly** | **Backup restore test**: restore one folder and one model file from the backup to a scratch location and open them | L or R (15 min) | Files open | Fix the backup job before anything else (R46) |
| Quarterly | **Firmware and software updates**: approve the update window BEN Care proposes for the firewall, NAS, AI box OS and BEN Controls Mini; updates are signed and staged, never forced during work hours | L approves, R runs | All parts on the supported version | Update at the next window; critical security updates within 7 days |
| Annual | Dust out the cabinet with the unit shut down (compressed air outdoors or a vacuum with a brush), check fan noise against the handover figure (E21), re-seat the cable strain relief, check the anti-tip bracket | L or Schreiber AI visit | Noise within 3 dB of handover | Fan replacement (spare in the kit) |
| 3–5 years | **UPS battery replacement** when the battery-health alarm or the quarterly runtime says so; old pack returned for recycling with the prepaid label | L (10 min) or visit | New pack passes the self-test | — |
| 3–5 years | IT refresh review: AI box and NAS against the workload; drives wiped (NIST SP 800-88) on return | Schreiber AI + owner | Plan agreed | — |

Spare kit shipped with every BEN 1: two intake filters, one fan (cab12), a printed one-page "what the lights mean" card and the battery return label.

## 11. Dense liquid-first tiers BEN 300 and BEN 1000 (added 2026-11-09, Rev 2)

BEN 300 and BEN 1000 follow sections 1–9 (as BEN 150 and BEN 500) and the liquid-loop rows of section 4b, which **apply to every unit** because liquid is the default on these tiers (no longer "study"). The rows below are added or tightened for the higher loop flows (about 177 LPM per GB300-class rack at a 45 °C supply, `docs/research/STATE_OF_THE_ART_2026.md` §2.3) and the larger number of CDUs and pumps.

| Interval | Subsystem | Task | Who | Record |
| --- | --- | --- | --- | --- |
| Weekly (R) | Liquid loop | Per-rack flow at the rack valves vs commissioning (±10 %), loop ΔT vs IT load (E20 reconciliation within 5 %), CDU pump run hours balanced, side-stream filter ΔP trend, make-up volume (any make-up on a closed loop is a leak until proven otherwise) | R | Weekly report |
| Monthly (L) | CDU pumps | **Pump rotation**: change the duty pump on each CDU so run hours stay within 10 %; **CDU failover proof** on one CDU by rotation (E18 reduced); listen and check for seal weep | L | M1 dense supplement |
| Monthly (L) | Filters | Strainer and side-stream filter ΔP; change the side-stream filter element at 1.5 × clean ΔP or every 3 months, whichever is first | L | M1 dense supplement |
| **Quarterly** | Coolant | **Coolant sampling**: pH, conductivity, inhibitor level, glycol % (PG25), biocide residual, bacteria count, iron and copper (corrosion indicators) per OCP water-based coolant v1.3 / PG25 limits; result trended against commissioning (R50) | L + water treatment S | Water log |
| Quarterly | Leak isolation | E19 leak-to-isolation on one rack by rotation (every rack within a year on BEN 300; within 18 months on BEN 1000) | L | E19 record |
| Semi-annual | CDU | CDU strainer clean; pump coupling and bearing check; VFD fan and filter; dead-head protection test with one row closed | S | Report |
| Annual | Loop and heat rejection | Plate HX ΔP and approach on every CDU and the heat-reuse HX; flush or chemical clean at ΔP > 1.3 × commissioning; dry-cooler or skid coil clean; BTU-meter calibration; UQD connector inspection and seal replacement per vendor cycles | S | Report |
| Annual | Power (≥ 1,200 A frames) | Ground-fault protection performance test on the main (NEC 230.95(C)); arc-energy reduction switch function test; IR scan of the main and busway at ≥ 40 % load; labels checked against the arc-flash study | S (NETA) | Report |
| 3-year | CDU | Pump seal and bearing replacement per vendor hours; isolation-valve actuator test; coolant change if the quarterly trend calls for it | S | Report |
