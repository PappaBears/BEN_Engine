# BEN Engine — Turnover Package and Turnover Meeting

**Owner:** Schreiber AI operations. **When:** stage 20 in `docs/PROCESS_FLOW.md`, after SAT sign-off (H19). **Format:** one indexed binder (PDF) plus the same files on an encrypted USB left in the controls cabinet document pocket, plus a copy in the gateway's `/srv/ben/turnover/` share. Every document carries the unit serial, configuration version and date.

## 1. Turnover package checklist

Tick every line. "N/A" must be justified in the notes column (e.g. "no generator in this configuration").

| # | Document | Produced by | Format | Required for tier | ✓ | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **A. Configuration and design** | | | | | | |
| A1 | Frozen configuration (`config.json`, v1.x) with derived sizing printout | ENG | JSON + PDF | All | | |
| A2 | As-built drawing set (IFC set red-lined at FAT and SAT, re-issued "as built") | ENG | PDF + native | All | | |
| A3 | Single-line diagram (as built) with breaker settings and ATS sequence | ENG | PDF | All | | |
| A4 | Controls wiring and one-line diagrams; network diagram with IP plan | ENG | PDF | All | | |
| A5 | Bill of materials as built (serials of UPS, cooling units, CDU, batteries, panel) | CM (verified by Schreiber AI quality) | CSV + PDF | All | | |
| A6 | PE-stamped anchorage/foundation drawing and calc; structural modification calc and weld inspection report | PE / CWI | PDF | 10/20/40 | | |
| A7 | Arc-flash and coordination study, final (with utility data) and label schedule | PE | PDF | 10/20/40 | | |
| A8 | Refrigerant charge vs. room volume calc; refrigerant and GWP declaration per circuit | ENG / HVAC sub | PDF | M/10/20 | | |
| A9 | Compliance pack for the profile (subset of `COMPLIANCE.md`) and code summary sheet | Compliance | PDF | All | | |
| **B. Test and inspection reports** | | | | | | |
| B1 | FAT commissioning report (signed JSON + PDF) with all experiment data and CSVs | ENG | PDF + CSV | All | | |
| B2 | SAT commissioning report (signed) | ENG | PDF + CSV | All | | |
| B3 | Electrical tests: torque log, insulation resistance, bonding continuity, ground electrode resistance, phase rotation, thermography images | CM licensed electrician (witnessed by Schreiber AI quality) | PDF | All | | |
| B4 | Cooling tests: pressure test chart, evacuation log, charge weights, superheat/subcool, glycol concentration and pH, flow and dP readings | HVAC sub | PDF | All | | |
| B5 | Fire alarm record of completion (NFPA 72), suppression acceptance test, door fan (enclosure integrity) test report, agent concentration calc | Fire contractor | PDF | 10/20/40 | | |
| B6 | Battery: UL 9540A report (≥ 20 kWh), BMS commissioning report, capacity/runtime test | Battery vendor / ENG | PDF | All | | |
| B7 | Generator: NFPA 110 installation acceptance test, load bank report, fuel system test | Generator vendor | PDF | option | | |
| B8 | Acoustic survey at property line (E10) | ENG | PDF | All | | |
| B9 | Envelope: coating DFT record, insulation photos, blower-door/leak test, water spray test | CM (countersigned by Schreiber AI quality) | PDF | All | | |
| B10 | Transport record: shock logger data, weigh ticket, set-down inspection | LOG | PDF | 10/20/40 | | |
| **C. Calibration** | | | | | | |
| C1 | Calibration certificates for every sensor channel (gain/offset, `cal_id`, reference instrument and its traceability, uncertainty budget per GUM) | ENG (`calibration.py`) | PDF + JSON | All | | |
| C2 | Reference instrument certificates (traceable to NIST or national lab) | Cal lab | PDF | All | | |
| C3 | Power meter and PDU meter verification (E9 reconciliation) | ENG | PDF | All | | |
| C4 | Next calibration due dates and the drift-trigger rule | ENG | PDF | All | | |
| **D. Operations and maintenance** | | | | | | |
| D1 | O&M manual for the unit (operating modes, alarm list with response actions, setpoints, failsafe behaviour) | ENG | PDF | All | | |
| D2 | Vendor O&M manuals (UPS, cooling, CDU, fire panel, generator, batteries, PDU, door controller) | Vendors | PDF | All | | |
| D3 | Maintenance schedule for this unit and climate (`MAINTENANCE.md` extract) with the first 12 months pre-populated | Operations | PDF + ICS | All | | |
| D4 | Record forms (blank) | Operations | PDF | All | | |
| D5 | Entry procedure, LOTO procedure, emergency procedures (fire, leak, battery alarm, power loss, heat) | Compliance | PDF (laminated copy at the door) | All | | |
| D6 | SDS binder (refrigerant, clean agent, glycol, battery electrolyte, coatings) | Compliance | PDF + paper | All | | |
| **E. Warranty and support** | | | | | | |
| E1 | Warranty registrations completed (UPS, cooling, CDU, batteries, generator, fire panel) with confirmation numbers | Schreiber AI operations | PDF | All | | |
| E2 | Schreiber AI warranty certificate and service-level agreement (managed, white-label or hardware-only) | Sales / Ops | PDF | All | | |
| E3 | Support contacts, escalation path, remote support consent form (signed or declined) | Ops | PDF | All | | |
| **F. Spare parts** | | | | | | |
| F1 | Spare parts list with part numbers and quantities delivered (see `MAINTENANCE.md` §7) | Schreiber AI operations | CSV | All | | |
| F2 | Recommended stock for years 2–5 with lead times | Ops | PDF | All | | |
| **G. Software, firmware and security** | | | | | | |
| G1 | Firmware versions and SHA-256 hashes for every node and the gateway image; signing certificate fingerprint | ENG | PDF + JSON | All | | |
| G2 | Gateway backup (full image) and database backup, with restore procedure tested at SAT | ENG | USB + PDF | All | | |
| G3 | Network and security configuration (zones, firewall rules, accounts, certificates and expiry dates) | ENG | PDF | All | | |
| G4 | **Password and credential handover record** (see §3) | ENG + CUST | PDF, signed | All | | |
| G5 | Data ownership and retention statement; export procedure (CSV) | Compliance | PDF | All | | |
| **H. Training and acceptance** | | | | | | |
| H1 | Training attendance and competency sign-off per module (§4) | ENG + CUST | PDF, signed | All | | |
| H2 | Open items list (punch list) with owner and date for each item | ENG + CUST | PDF | All | | |
| H3 | Certificate of substantial completion / acceptance | CUST | PDF, signed | All | | |
| H4 | AHJ certificates (electrical final, mechanical final, fire final, certificate of occupancy or equivalent) | AHJ via sub | PDF | 10/20/40 | | |

## 2. Turnover meeting agenda (half day on site, after SAT)

| Time | Item | Led by | Output |
| --- | --- | --- | --- |
| 0:00 | Safety briefing: entry procedure, arc-flash boundaries, refrigerant/agent/battery hazards, emergency stop locations | Schreiber AI compliance | Attendance |
| 0:15 | Walk the unit: every labelled component matched to the single-line and the drawings | ENG | Red-lines confirmed as-built |
| 1:00 | SAT results review: what was tested, what passed, deviations and how they were closed; the measured ride-through (E5) and acoustic (E10) numbers in plain words | ENG | Customer understands the real performance numbers |
| 1:30 | Dashboard session: live data, alarm list, how to acknowledge, CSV export, sweeps, what "failsafe" does | ENG | Operators log in with their own accounts |
| 2:00 | Maintenance schedule and who does what (remote Schreiber AI / local tech / certified sub); first-year calendar handed over | Operations | Calendar accepted |
| 2:20 | Warranty, SLA, escalation and spares | Ops / Sales | Contacts confirmed |
| 2:35 | Security and credential handover (§3), remote support consent | ENG + customer IT | Signed record |
| 2:50 | Open items and acceptance signature | Both | H2, H3 signed |
| 3:00 | Close | | |

## 3. Password and credential handover procedure

1. Before the meeting, Schreiber AI generates **new** credentials for every account the customer will own (dashboard admin, gateway OS admin, MQTT broker, Modbus/SNMP device passwords, fire panel installer code if the contractor permits, door controller, UPS and cooling web interfaces, Wi-Fi if enabled). Factory defaults are never left in place; the SAT includes a default-credential scan (E12).
2. Credentials are delivered in a sealed envelope **and** in an encrypted file (age/GPG) to the customer's named security contact; the passphrase is given verbally at the meeting. No credentials are emailed.
3. The customer changes every password during the meeting while Schreiber AI watches the dashboard confirm the change. Schreiber AI's own remote-support account is separate, uses certificate authentication, and is either enabled (managed service, consent form signed) or deleted (hardware-only / air-gap) in front of the customer.
4. The handover record lists every account, who now holds it, and the date; both parties sign. Schreiber AI destroys its copies of customer-owned credentials and records this.
5. Recovery: the customer stores a copy of the gateway backup (G2) and the admin credentials in their own vault. Schreiber AI keeps no customer passwords; recovery of a lost gateway requires the customer's backup or a factory re-image, which loses local history unless a database backup exists.

## 4. Training modules and sign-off

| Module | Audience | Duration | Competency check |
| --- | --- | --- | --- |
| T1 Safe entry and emergency response | Everyone with a badge | 45 min | Walk-through: find EPO, abort switch, extinguisher, exits, shut-off valves |
| T2 Dashboard and alarms | Operators | 60 min | Acknowledge an injected alarm, export a CSV, read the inlet temperature trend |
| T3 Daily/weekly checks | Local tech | 30 min | Complete the weekly form on the live unit |
| T4 Power system operation | Customer electrician | 60 min | Explain ATS sequence, identify breaker settings, read arc-flash label, perform LOTO on a PDU circuit |
| T5 Cooling system operation | Local tech / HVAC sub | 45 min | Change a filter, read dP, identify refrigerant detector, explain what happens on a leak alarm |
| T6 IT handover (customer's own) | Customer IT | — | Customer confirms PDU circuit map and rack labels match their asset list |
| T7 Security and remote support | Customer IT/security | 30 min | Verify remote support state, rotate a password, read the firmware hash |

Each module is signed by the trainee and the trainer and filed as H1.

## 5. What "turnover complete" means

Turnover is complete when: every line in §1 is ticked or justified; §3 record is signed; §4 modules are signed; the punch list has no safety items open; monitoring is live (managed service) or the customer has confirmed they are receiving alarms (self-operated); AHJ certificates are in the binder. The warranty clock starts on the acceptance signature (H3) date.
