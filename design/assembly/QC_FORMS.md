# BEN Engine — QC forms Q-01 to Q-12

Issue C, 2026-11-08 (matches drawing set Rev C, `design/REVISION.json`; the set is ISSUED FOR REVIEW until a named checker signs). One set of forms per unit. The unit serial number, the tier and the configuration hash go on every page.
A **HOLD** line needs the signature of the named qualified person before the next task starts. A **WITNESS** line needs the QC inspector present.
Every measured value is written as a number, never as a tick. "N/A" needs a reason. The CTQ/CTP references are defined in `design/ctq.py` and shown on the drawings.

Header on every form:

| Unit serial | Tier | Config (tier / kW / racks / cooling / redundancy / climate) | Drawing set issue | Form issue |
|---|---|---|---|---|
| __________ | ______ | ______________________________________ | Rev C 2026-11-08 (IFR) | C |

---

## Q-01 Receiving inspection

| # | Item | Required | Measured / result | By | Date |
|---|---|---|---|---|---|
| 1 | Delivery note matches purchase order | Yes | | | |
| 2 | Enclosure serial / CSC plate (containers): owner code, serial, last inspection date | Recorded, CSC valid | | | |
| 3 | Corner castings (4 top, 4 bottom) free of cracks and weld repairs [CTQ-A2] | 8 / 8 OK | | | |
| 4 | External defects marked and photographed | Photo IDs | | | |
| 5 | Light test from inside (no light through walls or roof) | None | | | |
| 6 | Water marks inside | None | | | |
| 7 | Parts count against parts list (attach list with counts) | 100 % | | | |
| 8 | Transport damage on parts | None / listed | | | |
| 9 | Batteries and electrical parts in locked store | Yes | | | |
| 10 | Non-conformance report raised (if any) | NCR no. | | | |

Inspector: ____________________ Date: ________

## Q-02 Container structure and modification

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | External length [CTQ-A1] | drawing value +0/-6 mm | | | |
| 2 | External width [CTQ-A1] | drawing value +0/-6 mm | | | |
| 3 | External height [CTQ-A1] | drawing value +0/-6 mm | | | |
| 4 | Floor diagonals, difference [CTQ-A1] | <= 10 mm | / | | |
| 5 | Each cutout position vs A-001 / A-003 (list each) | +/-5 mm | | | |
| 6 | No cutout within 300 mm of a corner post | Yes | | | |
| 7 | **HOLD** Welder licence (AWS D1.1 / ISO 9606-1) number and expiry [CTP-A1] | On file | | | |
| 8 | Reinforcement frame welded, visual test: no cracks, undercut <= 0.5 mm, no porosity [CTP-A1] | Each frame OK | | | |
| 9 | Primer applied within 4 h of welding; topcoat applied | Yes | | | |
| 10 | Tray bosses and seismic bosses welded at S-001 positions | Yes / N/A | | | |
| 11 | Photos of every frame (IDs) | | | | |

Welder (HOLD): ____________________ Licence: ________ Date: ________
Inspector: ____________________ Date: ________

## Q-03 Envelope: insulation, liner, seals

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | PIR thickness at 10 random points [CTQ-C1] | 100 +5/-0 mm (40 mm cabinet) | 1__ 2__ 3__ 4__ 5__ 6__ 7__ 8__ 9__ 10__ | | |
| 2 | Board joints: max gap, taped, staggered [CTQ-C1] | <= 3 mm, 100 % taped | | | |
| 3 | Closed-cell foam on corner posts, door frame, cross-member ends [CTQ-C4] | 100 % | | | |
| 4 | Liner overlaps with continuous sealant bead [CTQ-C2] | 100 % | | | |
| 5 | Smoke-pencil test at 10 joints [CTQ-C2] | No movement at 10 / 10 | | | |
| 6 | Roof boots clamped and sealed (each) | Yes | | | |
| 7 | Door seal paper-strip test, 8 points per door [CTQ-C3] | Held at 8 / 8 | Door 1: Door 2: | | |
| 8 | Light test with doors closed | No light | | | |
| 9 | Floor drain fall and 1 L water test [CTP-C1] | >= 1:100; clears < 60 s | | | |
| 10 | Anti-static vinyl seams welded; skirting fitted | Yes | | | |

Inspector: ____________________ Date: ________

## Q-04 Floor channels, anchors and torque record

Torque wrench ID: ________ Calibration due: ________ (must be within 12 months)

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | Channel centre lines vs S-001 | +/-3 mm | Ch 1: Ch 2: | | |
| 2 | Channels parallel | <= 2 mm | | | |
| 3 | Channel level over full length (laser) [CTQ-S1] | <= 3 mm | | | |
| 4 | Shims: steel only | Yes | | | |
| 5 | **WITNESS** Through-bolts M12 torqued [CTP-S1] | 85 N·m +/-10 %, every bolt paint-marked | Count: ____ / ____ | | |
| 6 | **WITNESS** Rack hold-down bolts M12 [CTP-S2] | 85 N·m, 4 per rack | Count: ____ / ____ | | |
| 7 | Equipment skid bolts (UPS, battery, CDU, cooling units) M12 [CTP-S3] | 85 N·m, 4 per cabinet | Count: ____ / ____ | | |
| 8 | BEN 5: skid anchors M16 [CTP-S1 micro] | 210 N·m, 4 | | | |
| 9 | Tray underside height | 2250 +/-10 mm | | | |
| 10 | Tray ground bonding at every joint | <= 0.1 ohm | | | |

Attach the bolt map (S-001 marked up) with every bolt numbered.
Inspector (WITNESS): ____________________ Date: ________

## Q-05 Racks, hold-downs and containment

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | Rack x-positions vs A-002 (list each tag) [CTQ-B1] | +/-10 mm | | | |
| 2 | Rack rails plumb, both axes, each rack [CTQ-B3] | <= 2 mm over 2 m | R1: R2: R3: ... | | |
| 3 | Rack-to-rack gap [CTQ-B4] | <= 3 mm | | | |
| 4 | Rack fronts on a straight line [CTQ-B4] | <= 3 mm | | | |
| 5 | **WITNESS** Clear aisle / working space width at 3 points [CTQ-B2] | >= 914 mm | 1__ 2__ 3__ | | |
| 6 | Blanking panels in every open U | 100 % | | | |
| 7 | Rack ground bond to tray bar, each rack | <= 0.1 ohm | | | |
| 8 | Containment panels sealed to liner; brush strips at cable openings | Yes | | | |
| 9 | Containment dP at full fan speed, all doors closed [CTQ-B5] | >= 5 Pa | | | |
| 10 | RDHx doors fitted and hoses capped (BEN 150) | Yes / N/A | | | |

Inspector (WITNESS item 5): ____________________ Date: ________

## Q-06 Cooling: piping, pressure test, charge

HVAC technician licence (EPA 608 / F-gas) number: ________ Expiry: ________

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | Units positioned vs A-002 and bolted (list tags) | +/-10 mm | | | |
| 2 | Condensers on curbs with vibration mounts | Yes | | | |
| 3 | **HOLD** Brazing with nitrogen purge [CTP-M1] | Yes | | | |
| 4 | **WITNESS** Refrigerant pressure test: pressure, duration, drop [CTQ-M1] | 1.1 x design, 24 h, <= 1 % | ____ bar, ____ h, ____ % | | |
| 5 | **HOLD** Vacuum: micron reading and hold time [CTP-M1] | <= 500 micron, 30 min | | | |
| 6 | Charge per nameplate, per circuit | kg | CU1: CU2: ... | | |
| 7 | A2L detector in plenum, fan interlock tested | Yes | | | |
| 8 | **WITNESS** Water loop hydrostatic test: pressure, duration, drop [CTQ-M1] | 1.5 x working, 2 h, 0 | | | |
| 9 | Glycol concentration (refractometer) [CTQ-M4] | 30 % +/-2 % | | | |
| 10 | Flow per rack / per RDHx vs design [CTQ-M4] | +/-10 % | | | |
| 11 | Drain / drip tray 1 L water test, each tray [CTQ-M2] | < 60 s, no pooling | | | |
| 12 | Air vents at high points open and closed; no air | Yes | | | |

HVAC technician (HOLD): ____________________ Date: ________ Inspector (WITNESS): ____________________ Date: ________

## Q-07 Electrical installation and tests

Electrician licence number: ________ Expiry: ________ Insulation tester ID / cal due: ________ Earth tester ID / cal due: ________

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | **HOLD** All conductors landed by the licensed electrician [CTP-E1] | Signed | | | |
| 2 | **WITNESS** Termination torque record (attach list: device, lug, value) [CTP-E2] | Every lug | | | |
| 3 | Insulation resistance, each feeder, 1000 V, phase-phase and phase-ground [CTQ-E1] | >= 100 Mohm | | | |
| 4 | Insulation resistance, branch circuits [CTQ-E1] | >= 1 Mohm | | | |
| 5 | **WITNESS** Grounding electrode resistance (fall of potential) [CTQ-E2] | <= 25 ohm (target 5) | | | |
| 6 | **WITNESS** Bond resistance: container frame, trays, racks, cabinets [CTQ-E2] | <= 0.1 ohm each | | | |
| 7 | Phase rotation at every panel [CTQ-E4] | A-B-C | | | |
| 8 | Voltage at every panel, all phases [CTQ-E4] | nominal +/-5 % | | | |
| 9 | UPS started per manufacturer procedure; alarms clear | Yes | | | |
| 10 | Battery disconnect, E-stop, UL 9540A data on file | Yes | | | |
| 11 | Labels on every breaker, cable end, receptacle | 100 % | | | |
| 12 | Power and data trays separated 300 mm; crossings at 90 degrees | Yes | | | |

Electrician (HOLD): ____________________ Date: ________ Inspector (WITNESS): ____________________ Date: ________

## Q-08 Controls nodes, sensors and calibration

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | Nodes mounted at C-001 positions; all online in `ben_engine` | 100 % | | | |
| 2 | Inlet probe heights, each rack (3 per rack) [CTQ-K1] | 400 / 1200 / 1800 +/-20 mm (micro 300 / 700 / 1100) | | | |
| 3 | Probe stand-off from rack face [CTQ-K1] | 50 +/-10 mm | | | |
| 4 | Sensor labels match C-001 schedule and PROTOCOL.md at sensor and at node [CTQ-K2] | 100 % | | | |
| 5 | **WITNESS** Temperature calibration: ice point and 40 C, error after correction [CTQ-K3] | <= +/-0.25 C | | | |
| 6 | cal_id stored in each node (list) | | | | |
| 7 | dP tare with containment open; reading after tare [CTQ-K4] | 0 +/-0.4 Pa | | | |
| 8 | Door contact response [CTQ-K4] | <= 2 s | | | |
| 9 | Leak rope wet-finger test every 1 m [CTQ-M3] | leak = 1 within 10 s at every point | | | |
| 10 | Modbus: UPS, cooling units, PDUs, meter all reporting | Yes | | | |
| 11 | Fire and EPO dry contacts show on node as monitor only | Yes | | | |

Controls technician: ____________________ Inspector (WITNESS item 5): ____________________ Date: ________

## Q-09 Fire detection and suppression

Installer certificate number: ________ Expiry: ________

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | Cylinder size vs room volume calculation (attach) | Per installer design | | | |
| 2 | Cylinder bracket, pipe supports every 1.5 m, nozzles | Yes | | | |
| 3 | Detectors: 2 per zone, zones correct | Yes | | | |
| 4 | **HOLD** Releasing circuit, abort, EPO interlock, cooling shutdown wired and tested by installer [CTP-F1] | Signed | | | |
| 5 | **HOLD** Life-safety hard-wired; nodes monitor dry contacts only [CTP-K1] | Yes | | | |
| 6 | Room integrity (door fan) test: hold time [CTP-F1] | >= 10 min | | | |
| 7 | Functional test with solenoid disconnected; actuator fitted last | Yes | | | |
| 8 | BEN 5: aerosol unit mounted, actuator independent, label on door | Yes / N/A | | | |

Installer (HOLD): ____________________ Date: ________

## Q-10 Final QC and pre-ship test

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | Label walk-down against A-002 and C-001 [CTQ-B6] | 100 % | | | |
| 2 | Aisle width at 3 points | >= 914 mm | | | |
| 3 | Load bank 50 % IT for 1 h: all inlets [CTQ-M5] | 18-27 C | min: max: | | |
| 4 | Load bank 100 % IT for 2 h: all inlets [CTQ-M5] | 18-27 C | min: max: | | |
| 5 | Cooling unit load share [CTQ-M5] | within 15 % | | | |
| 6 | UPS on battery at 100 % IT: runtime | >= design minutes | | | |
| 7 | **WITNESS** EPO test: time to all IT and cooling off [CTQ-E3] | < 1 s | | | |
| 8 | Energy meter reading start / end | kWh | | | |
| 9 | Pre-ship report from `ben_engine.commissioning --stage pre-ship` attached | Report ID | | | |
| 10 | Open items list (punch list) attached | | | | |

Inspector (WITNESS): ____________________ Date: ________

## Q-11 Transport preparation

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | Battery state of charge; battery disconnect open; UPS transport lock | 30-50 %; open; fitted | | | |
| 2 | Servers removed or strapped (list) | | | | |
| 3 | Transport blocking fitted; containment doors locked; drains capped | Yes | | | |
| 4 | **WITNESS** Gross mass (weigh-bridge / crane scale) [CTQ-A3] | design +10 % max | ____ kg | | |
| 5 | **HOLD** CSC re-inspection: new plate or ACEP record no. [CTP-A2] | On unit | | | |
| 6 | **HOLD** Rigging check: 4-leg sling on top castings, angle >= 60 degrees [CTP-S4] | Signed | | | |
| 7 | Door seal number / key number | Recorded | | | |
| 8 | Dangerous goods documents for batteries | Attached | | | |
| 9 | Transport documents in document box | Yes | | | |

Surveyor (HOLD): ____________________ Rigger (HOLD): ____________________ Inspector (WITNESS): ____________________ Date: ________

## Q-12 Site set-down and hook-up

| # | Item | Required | Measured | By | Date |
|---|---|---|---|---|---|
| 1 | Pad level at 4 foundation points | difference <= 6 mm | | | |
| 2 | Twist-locks locked (containers) / anchors M16 torqued 210 N·m (micro) [CTP-S1 micro] | 4 / 4 | | | |
| 3 | Transport blocking and straps removed | Yes | | | |
| 4 | Ground rods driven, exothermic connections, pad rebar bonded | Yes | | | |
| 5 | **WITNESS** Ground resistance [CTQ-E2] | <= 25 ohm (target 5) | | | |
| 6 | **HOLD** Service conductors connected by licensed electrician; phase rotation [CTQ-E4] | A-B-C | | | |
| 7 | **HOLD** Dry cooler connected, primary loop filled, vented and pressure tested by HVAC technician | Yes / N/A | | | |
| 8 | Fibre terminated on ODF; link up to gateway | Yes | | | |
| 9 | Servers fitted; each on PDU A and PDU B | Yes | | | |
| 10 | Commissioning script `--stage site` report ID (handover point) | Signed report | | | |

Electrician (HOLD): ____________________ HVAC (HOLD): ____________________ Inspector: ____________________ Customer: ____________________ Date: ________

---

## NCR-01 Non-conformance report and disposition

| Field | Entry |
|---|---|
| NCR number / date raised | NCR-____ / ________ |
| Unit serial / tier / IFC rev | |
| Found at (task, stage, hold/witness point) | |
| Drawing / CTQ-CTP reference | |
| Requirement (specification and tolerance) | |
| Actual condition (measured value, instrument ID) | |
| Classification | critical / major / minor |
| Containment (other units or features affected, tag fitted) | |
| Proposed disposition | rework / use-as-is / scrap-replace |
| Schreiber AI Engineering decision (required for any CTQ; use-as-is never for critical) | Name / date / signature |
| Rework instruction and re-inspection result (100 %) | |
| CAPA required? (critical, repeated major, bypassed hold point) | yes → CAPA-____ / no |
| Closed by (supplier quality lead) / verified by (Schreiber AI Quality) | |

## FAI-01 First-article inspection report

Header: unit serial, tier, configuration line, IFC revision, supplier, dates, Schreiber AI witness name.

| Balloon | Drawing / sheet | Characteristic | Specification | Measured | Instrument ID (cal due) | Pass / fail | Witness |
|---|---|---|---|---|---|---|---|
| 1…n | A-002 equipment schedule | Every tag x, y, z | ±10 mm | | | | |
| | A-001 | External dims, diagonals | +0/−6 mm, 10 mm | | | | |
| | S-001 | Channel level, bolt torque (every bolt) | 3 mm; 85 N·m | | | | |
| | E-001 | Insulation resistance, ground, rotation, lug torque | per register | | | | |
| | M-001 | Pressure tests, charge, glycol, flow | per register | | | | |
| | C-001 | Probe positions, labels, calibration error | ±20 mm; 100 %; ±0.25 C | | | | |
| | — | Full CTQ/CTP register (attach section 5 of SQAM with values) | all | | | | |

Attachments: complete Q-01…Q-12, NCR log, FAT report + CSV hash, photos of every hold point, certificates of qualified persons.
Approval: Schreiber AI Engineering ____________ Quality ____________ Date ________ (second unit of this tier may not start before this signature).

## DR-01 Deviation request

| Field | Entry |
|---|---|
| DR number / date | |
| Unit(s) / tier / IFC rev / sheet and item | |
| Requirement as drawn | |
| Proposed deviation (what, why, how long) | |
| CTQ / CTP items affected and the supplier's assessment | |
| Interference / footprint check needed? (substituted part dims) | yes / no |
| Schreiber AI Engineering decision | approved / approved with conditions / rejected — name, date |
| Conditions and record (red-line, Q-form note) | |

## CAPA-01 Corrective and preventive action (8D-lite)

| D | Step | Entry |
|---|---|---|
| D1 | Team (names, roles) | |
| D2 | Problem statement (NCR numbers, what, where, how many) | |
| D3 | Containment (units checked, result, date) | |
| D4 | Root cause (5-why; evidence) | |
| D5 | Corrective action (what changes, owner, date) | |
| D6 | Verification (measurement showing the problem is gone, on which units) | |
| D7 | Prevention (instruction / form / fixture / training change; drawing change request if needed) | |
| D8 | Close-out (supplier quality lead; Schreiber AI Quality verification, date) | |

## COC-01 Certificate of conformance (FAT)

Unit serial ________ Tier ________ Configuration hash ________ IFC rev ________
FAT report file ________ Telemetry CSV SHA-256 ________ Date of test ________
All Q-forms complete: yes/no. Open NCRs: critical ____ major ____ minor ____ (critical and major must be 0). FAI approved (first unit): yes/no/N-A.
Schreiber AI Quality ____________ Supplier quality lead ____________ Date ________
