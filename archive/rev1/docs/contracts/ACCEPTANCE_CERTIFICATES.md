# Acceptance Certificates — FAT, SAT and Turnover

> **TEMPLATE — not legal advice — have counsel review before use.**
> Schreiber AI · BEN Engine (Business Edge Node) · `docs/contracts/ACCEPTANCE_CERTIFICATES.md` · Template rev [TEMPLATE_REV]
> Bracketed `[FIELDS]` are filled by the proposal generator and by the Commissioning Script output. Each certificate is issued as a separate signed PDF and filed in the Turnover Package (items B1, B2, H3). Delete this box before signature.

Three certificates are used for every Unit, in this order:

| Certificate | Hold point | Process stage | Effect under the MSA |
| --- | --- | --- | --- |
| A. Factory Acceptance Test (FAT) Certificate | H13 | 13 | FAT Acceptance; milestone 3 due; title passes on payment; Unit may ship |
| B. Site Acceptance Test (SAT) Certificate | H19 | 19 | SAT Acceptance; warranty clock starts; risk of defects in Schreiber AI's site work passes; Managed Services term starts |
| C. Turnover Certificate (certificate of substantial completion) | W20 | 20 | Turnover complete; milestone 4 due less credits and holdback; Punch List governs remaining items |

Deemed acceptance (MSA 8.4) applies to A and B if Customer neither signs nor delivers a written list of failed criteria within 10 Business Days ([DEEMED_ACCEPTANCE_DAYS]) of receiving the Commissioning Report and the proposed certificate.

---

## A. Factory Acceptance Test (FAT) Certificate

**Certificate ID:** [FAT_CERT_ID]

| Field | Value |
| --- | --- |
| SOW / MSA | [SOW_ID] / [MSA_ID] |
| Customer | [CUSTOMER_NAME] |
| Unit serial | [UNIT_SERIAL] |
| Tier / Configuration ID | [TIER] / [CONFIG_ID] |
| Factory | [FACTORY_NAME], [FACTORY_ADDRESS] |
| Contract Manufacturer (if any) | [CM_NAME] |
| FAT start / end | [FAT_START_DATETIME] / [FAT_END_DATETIME] |
| Burn-in duration | [FAT_BURNIN_HOURS] hours (minimum 24) |
| Commissioning Script version | `ben_engine` [BEN_ENGINE_VERSION], mode `factory` |
| Operator (signature block in report) | [COMMISSIONING_OPERATOR] |

### A.1 Commissioning Report integrity

| Artefact | Filename | SHA-256 |
| --- | --- | --- |
| Commissioning Report (Markdown/PDF) | [FAT_REPORT_FILENAME] | [FAT_REPORT_SHA256] |
| Telemetry CSV data file | [FAT_CSV_FILENAME] | [FAT_CSV_SHA256] |
| Sweep CSVs (load step, failover, ride-through) | [FAT_SWEEP_FILENAMES] | [FAT_SWEEP_SHA256_LIST] |
| Thermography image set | [FAT_IR_FILENAME] | [FAT_IR_SHA256] |

The CSV hash printed inside the Commissioning Report must equal the CSV SHA-256 above. Both Parties verified it with `sha256sum` at signing: [FAT_HASH_VERIFIED] (yes / no).

### A.2 Step results

| Step | Name | Result | Key values | Deviation / Punch List ref |
| --- | --- | --- | --- | --- |
| 1 | Pre-power visual checklist | [FAT_STEP1_RESULT] | items confirmed [FAT_STEP1_ITEMS] | |
| 2 | Pod discovery, attestation and firmware versions | [FAT_STEP2_RESULT] | Pods attested [FAT_STEP2_NODES] / expected [POD_COUNT] (node ids [NODE_COUNT]); firmware [FIRMWARE_VERSION] | |
| 3 | Sensor sanity at idle | [FAT_STEP3_RESULT] | inlet spread [FAT_STEP3_SPREAD_K] K; RH [FAT_STEP3_RH] %; dP after tare [FAT_STEP3_DP] Pa | |
| 4 | I/O point-to-point | [FAT_STEP4_RESULT] | points [FAT_STEP4_POINTS]; failed [FAT_STEP4_FAILED] | |
| 5 | Power chain: meter vs PDU sum | [FAT_STEP5_RESULT] | disagreement [FAT_STEP5_DISAGREEMENT_PCT] %; PUE [FAT_STEP5_PUE] | |
| 6 | Cooling sequential start and failover | [FAT_STEP6_RESULT] | max inlet during failover [FAT_STEP6_MAX_INLET_C] °C vs allowable [ASHRAE_MAX_C] °C | |
| 7 | Load step to 100 % and steady state | [FAT_STEP7_RESULT] | max inlet [FAT_STEP7_MAX_INLET_C] °C; ΔT at full load [FAT_STEP7_DELTA_T] K | |
| 8 | Utility loss ride-through | [FAT_STEP8_RESULT] | UPS runtime [FAT_STEP8_UPS_MIN] min; minutes to ASHRAE max [FAT_STEP8_MINUTES_TO_MAX] | |
| 9 | Alarm verification | [FAT_STEP9_RESULT] | alarm paths passed [FAT_STEP9_PASSED] / 5; residual alarms [FAT_STEP9_RESIDUAL] | |
| 10 | Export CSV and signed report | [FAT_STEP10_RESULT] | rows [FAT_STEP10_ROWS] | |
| — | Experiment E7 filter clog (FAT only) | [FAT_E7_RESULT] | dP alarm threshold [FAT_E7_DP_THRESHOLD] Pa | |
| — | Experiment E11 burn-in 24 h | [FAT_E11_RESULT] | critical alarms [FAT_E11_CRITICAL_ALARMS] | |
| — | Experiment E12 cyber scan | [FAT_E12_RESULT] | open services beyond allow-list [FAT_E12_EXTRA_SERVICES]; default credentials found [FAT_E12_DEFAULT_CREDS] | |
| — | Door fan (enclosure integrity) test | [FAT_DOORFAN_RESULT] | hold time [FAT_DOORFAN_HOLD_MIN] min | |
| — | Agent system contractor acceptance | [FAT_AGENT_RESULT] | contractor [FIRE_CONTRACTOR_NAME] | |

### A.3 QC forms closed

| Form | Title | Closed | Signatory |
| --- | --- | --- | --- |
| Q-01 | Receiving inspection | [Q01_CLOSED] | [Q01_SIGNATORY] |
| Q-02 | Container structure and modification (H7, CWI) | [Q02_CLOSED] | [Q02_SIGNATORY] |
| Q-03 | Envelope: insulation, liner, seals (W8) | [Q03_CLOSED] | [Q03_SIGNATORY] |
| Q-04 | Floor channels, anchors and torque record | [Q04_CLOSED] | [Q04_SIGNATORY] |
| Q-05 | Racks, hold-downs and containment | [Q05_CLOSED] | [Q05_SIGNATORY] |
| Q-06 | Cooling: piping, pressure test, charge (H11) | [Q06_CLOSED] | [Q06_SIGNATORY] |
| Q-07 | Electrical installation and tests (H10a/b) | [Q07_CLOSED] | [Q07_SIGNATORY] |
| Q-08 | BEN Pods, sensors and calibration (W12) | [Q08_CLOSED] | [Q08_SIGNATORY] |
| Q-09 | Fire detection and suppression | [Q09_CLOSED] | [Q09_SIGNATORY] |
| Q-10 | Final QC and pre-ship test | [Q10_CLOSED] | [Q10_SIGNATORY] |

### A.4 Firmware and calibration record

| Item | Value |
| --- | --- |
| BEN Pod firmware version / image SHA-256 | [FIRMWARE_VERSION] / [FIRMWARE_SHA256] |
| Edge computer image version / SHA-256 | [GATEWAY_IMAGE_VERSION] / [GATEWAY_IMAGE_SHA256] |
| Signing certificate fingerprint | [SIGNING_CERT_FINGERPRINT] |
| Calibration ID applied to all channels | [CAL_ID] |
| Reference instrument certificates | [REFERENCE_CERT_IDS] |

### A.5 Punch List at FAT

| # | Item | Class (safety / performance / cosmetic) | Owner | Due | Blocks shipment? |
| --- | --- | --- | --- | --- | --- |
| [FAT_PUNCH_1_ID] | [FAT_PUNCH_1_ITEM] | [FAT_PUNCH_1_CLASS] | [FAT_PUNCH_1_OWNER] | [FAT_PUNCH_1_DUE] | [FAT_PUNCH_1_BLOCKS] |

No safety item may remain open. Deviations accepted in writing are listed here with the accepting signatory.

### A.6 Declaration

Schreiber AI declares that the Unit was tested with the Commissioning Script in factory mode, that the results above are those in the Commissioning Report whose hashes are recorded in A.1, and that every Hold Point through H13 has been signed by the named trade or inspector.

Customer (or, if Customer did not attend after notice, Schreiber AI on Customer's behalf under MSA 8.2) accepts the Unit at FAT, subject to the Punch List in A.5. Milestone 3 is due under SOW Section 7.2. The Unit may be prepared for transport (Q-11).

| | Schreiber AI engineering | Schreiber AI factory / CM QC | Customer witness |
| --- | --- | --- | --- |
| Signature | ______________________ | ______________________ | ______________________ |
| Name | [SCHREIBER_ENG_SIGNATORY] | [FACTORY_QC_SIGNATORY] | [CUSTOMER_FAT_WITNESS] |
| Title | | | |
| Date | [FAT_CERT_DATE] | [FAT_CERT_DATE] | [FAT_CERT_DATE] |

Customer waiver of attendance (if applicable): "Customer waives attendance at FAT and accepts the Commissioning Report as the record of the test." Signed [CUSTOMER_FAT_WAIVER_SIGNATORY], [CUSTOMER_FAT_WAIVER_DATE].

---

## B. Site Acceptance Test (SAT) Certificate

**Certificate ID:** [SAT_CERT_ID]

| Field | Value |
| --- | --- |
| SOW / MSA | [SOW_ID] / [MSA_ID] |
| Customer | [CUSTOMER_NAME] |
| Unit serial | [UNIT_SERIAL] |
| Tier / Configuration ID (after Change Orders) | [TIER] / [CONFIG_ID] |
| Site | [SITE_NAME], [SITE_ADDRESS] |
| FAT Certificate reference | [FAT_CERT_ID] |
| Set-down date (W17) / Hook-up complete (H18) | [SETDOWN_DATE] / [H18_DATE] |
| AHJ power release | [AHJ_POWER_RELEASE_DATE], inspector [AHJ_ELECTRICAL_INSPECTOR] |
| SAT start / end | [SAT_START_DATETIME] / [SAT_END_DATETIME] |
| Burn-in duration | [SAT_BURNIN_HOURS] hours (minimum 48) |
| Load source | [SAT_LOAD_SOURCE] (load banks, serials [LOADBANK_SERIALS] / Customer IT at [SAT_LOAD_KW] kW) |
| Commissioning Script version | `ben_engine` [BEN_ENGINE_VERSION], mode `site` |
| Operator | [COMMISSIONING_OPERATOR] |

### B.1 Commissioning Report integrity

| Artefact | Filename | SHA-256 |
| --- | --- | --- |
| Commissioning Report (site mode) | [SAT_REPORT_FILENAME] | [SAT_REPORT_SHA256] |
| Telemetry CSV data file | [SAT_CSV_FILENAME] | [SAT_CSV_SHA256] |
| Sweep CSVs | [SAT_SWEEP_FILENAMES] | [SAT_SWEEP_SHA256_LIST] |
| Acoustic survey report (E10) | [SAT_ACOUSTIC_FILENAME] | [SAT_ACOUSTIC_SHA256] |
| E12 cyber report | [SAT_E12_FILENAME] | [SAT_E12_SHA256] |

Hash verified with `sha256sum` by both Parties at signing: [SAT_HASH_VERIFIED] (yes / no).

### B.2 Step results

| Step | Name | Result | Key values | Deviation / Punch List ref |
| --- | --- | --- | --- | --- |
| 1 | Pre-power visual checklist | [SAT_STEP1_RESULT] | | |
| 2 | Pod discovery, attestation and firmware versions | [SAT_STEP2_RESULT] | Pods attested [SAT_STEP2_NODES] / [POD_COUNT]; firmware [FIRMWARE_VERSION] | |
| 3 | Sensor sanity at idle | [SAT_STEP3_RESULT] | spread [SAT_STEP3_SPREAD_K] K; RH [SAT_STEP3_RH] %; dP [SAT_STEP3_DP] Pa | |
| 4 | I/O point-to-point | [SAT_STEP4_RESULT] | points [SAT_STEP4_POINTS]; failed [SAT_STEP4_FAILED] | |
| 5 | Power chain: meter vs PDU sum | [SAT_STEP5_RESULT] | disagreement [SAT_STEP5_DISAGREEMENT_PCT] %; **measured PUE [SAT_STEP5_PUE]** (Proposal estimate [PUE_ESTIMATE]) | |
| 6 | Cooling sequential start and failover | [SAT_STEP6_RESULT] | max inlet during failover [SAT_STEP6_MAX_INLET_C] °C | |
| 7 | Load step (reduced per E3) and steady state | [SAT_STEP7_RESULT] | max inlet [SAT_STEP7_MAX_INLET_C] °C; outdoor temperature during test [SAT_OUTDOOR_TEMP_C] °C | |
| 8 | Utility loss ride-through | [SAT_STEP8_RESULT] | **measured minutes to ASHRAE max with cooling off [SAT_STEP8_MINUTES_TO_MAX]**; UPS runtime [SAT_STEP8_UPS_MIN] min; generator start [SAT_STEP8_GEN_START_S] s | |
| 9 | Alarm verification | [SAT_STEP9_RESULT] | paths passed [SAT_STEP9_PASSED] / 5; residual [SAT_STEP9_RESIDUAL] | |
| 10 | Export CSV and signed report | [SAT_STEP10_RESULT] | rows [SAT_STEP10_ROWS] | |

### B.3 Additional SAT items (SOW Section 8.2)

| Item | Result | Value / certificate | Deviation / Punch List ref |
| --- | --- | --- | --- |
| Fire alarm record of completion (NFPA 72 Ch. 14) | [SAT_FIRE_ALARM_RESULT] | [FIRE_ALARM_RECORD_ID] | |
| Clean agent acceptance and door fan test | [SAT_SUPPRESSION_RESULT] | hold [SAT_DOORFAN_HOLD_MIN] min; AHJ fire acceptance [AHJ_FIRE_ACCEPTANCE_ID] | |
| Acoustic survey (E10) | [SAT_E10_RESULT] | measured [SAT_E10_MEASURED_DBA] dBA vs limit [NOISE_LIMIT_NIGHT] dBA | |
| Burn-in 48 h (E11) | [SAT_E11_RESULT] | critical alarms [SAT_E11_CRITICAL_ALARMS] | |
| Cyber (E12) | [SAT_E12_RESULT] | extra services [SAT_E12_EXTRA_SERVICES]; default credentials [SAT_E12_DEFAULT_CREDS]; unsigned image rejected [SAT_E12_UNSIGNED_REJECTED] | |
| Ground electrode resistance | [SAT_GROUND_RESULT] | [SAT_GROUND_OHMS] Ω (≤ 25 Ω; target ≤ 5 Ω) | |
| Bonding continuity / insulation resistance / phase rotation | [SAT_ELECTRICAL_RESULT] | [SAT_BONDING_OHMS] Ω / [SAT_IR_MOHM] MΩ / [SAT_PHASE_ROTATION] | |
| Emergency lighting 90-minute test | [SAT_EMERGENCY_LIGHT_RESULT] | | |
| Final arc-flash labels with utility data | [SAT_ARCFLASH_RESULT] | utility fault current [UTILITY_FAULT_CURRENT_KA] kA | |
| Cooling: superheat/subcool, leak check, glycol | [SAT_COOLING_RESULT] | [SAT_COOLING_VALUES] | |
| Generator NFPA 110 acceptance (if fitted) | [SAT_GENERATOR_RESULT] | [GENERATOR_ACCEPTANCE_ID] | |
| Battery BMS commissioning / UL 9540A report on file (≥ 20 kWh) | [SAT_BATTERY_RESULT] | [BATTERY_9540A_REPORT_ID] | |
| Edge computer backup restored to spare edge computer (Turnover G2) | [SAT_BACKUP_RESTORE_RESULT] | | |
| Default-credential scan; factory credentials replaced | [SAT_CREDENTIAL_SCAN_RESULT] | | |

### B.4 Site QC form

| Form | Title | Closed | Signatory |
| --- | --- | --- | --- |
| Q-11 | Transport preparation (shock logger IDs [SHOCK_LOGGER_IDS]; max event [SHOCK_MAX_G] g) | [Q11_CLOSED] | [Q11_SIGNATORY] |
| Q-12 | Site set-down and hook-up (anchor torque, level ±6 mm, H18) | [Q12_CLOSED] | [Q12_SIGNATORY] |

### B.5 Punch List at SAT

| # | Item | Class | Owner | Due | Holdback estimate |
| --- | --- | --- | --- | --- | --- |
| [SAT_PUNCH_1_ID] | [SAT_PUNCH_1_ITEM] | [SAT_PUNCH_1_CLASS] | [SAT_PUNCH_1_OWNER] | [SAT_PUNCH_1_DUE] | [SAT_PUNCH_1_HOLDBACK] |

Total holdback (150 % of Schreiber AI's estimate, MSA 8.5): [SAT_PUNCH_HOLDBACK_TOTAL]. No safety item is open.

### B.6 Declaration

Schreiber AI declares that the Unit was tested with the Commissioning Script in site mode on utility power at the Site, that the results above are those in the Commissioning Report whose hashes are recorded in B.1, that the AHJ has released power and accepted the fire systems, and that every Hold Point through H19 has been signed.

Customer accepts the Unit at SAT, subject to the Punch List in B.5. The **warranty period of [WARRANTY_MONTHS] months starts on [SAT_CERT_DATE]**. Managed Services (if ordered) start on the same date.

| | Schreiber AI engineering | Customer authorised representative | Fire marshal / AHJ (acknowledgement of acceptance) |
| --- | --- | --- | --- |
| Signature | ______________________ | ______________________ | ______________________ |
| Name | [SCHREIBER_ENG_SIGNATORY] | [CUSTOMER_SIGNATORY_NAME] | [AHJ_FIRE_MARSHAL] |
| Title | | [CUSTOMER_SIGNATORY_TITLE] | |
| Date | [SAT_CERT_DATE] | [SAT_CERT_DATE] | [AHJ_FIRE_ACCEPTANCE_DATE] |

---

## C. Turnover Certificate (certificate of substantial completion)

**Certificate ID:** [TURNOVER_CERT_ID]

| Field | Value |
| --- | --- |
| SOW / MSA | [SOW_ID] / [MSA_ID] |
| Customer | [CUSTOMER_NAME] |
| Unit serial | [UNIT_SERIAL] |
| Site | [SITE_NAME], [SITE_ADDRESS] |
| SAT Certificate reference / date | [SAT_CERT_ID] / [SAT_CERT_DATE] |
| Turnover meeting date (W20) | [TURNOVER_DATE] |
| Delivery model | [DELIVERY_MODEL] |

### C.1 Turnover Package checklist (`docs/TURNOVER.md` Section 1)

| Section | Items | Delivered | N/A justified | Notes |
| --- | --- | --- | --- | --- |
| A. Configuration and design | A1–A9 | [TO_A_DELIVERED] / 9 | [TO_A_NA] | |
| B. Test and inspection reports | B1–B10 | [TO_B_DELIVERED] / 10 | [TO_B_NA] | |
| C. Calibration | C1–C4 | [TO_C_DELIVERED] / 4 | [TO_C_NA] | |
| D. Operations and maintenance | D1–D6 | [TO_D_DELIVERED] / 6 | [TO_D_NA] | |
| E. Warranty and support | E1–E3 | [TO_E_DELIVERED] / 3 | [TO_E_NA] | |
| F. Spare parts | F1–F2 | [TO_F_DELIVERED] / 2 | [TO_F_NA] | |
| G. Software, firmware and security | G1–G5 | [TO_G_DELIVERED] / 5 | [TO_G_NA] | |
| H. Training and acceptance | H1–H4 | [TO_H_DELIVERED] / 4 | [TO_H_NA] | |

Binder delivered as: PDF binder [TO_BINDER_SHA256]; encrypted USB in controls cabinet pocket [TO_USB_ID]; edge computer share `/srv/ben/turnover/`.

### C.2 Report hashes carried forward

| Report | SHA-256 |
| --- | --- |
| FAT Commissioning Report / CSV | [FAT_REPORT_SHA256] / [FAT_CSV_SHA256] |
| SAT Commissioning Report / CSV | [SAT_REPORT_SHA256] / [SAT_CSV_SHA256] |
| BEN Pod firmware image | [FIRMWARE_SHA256] |
| Edge computer image | [GATEWAY_IMAGE_SHA256] |
| Edge computer backup image (G2) | [GATEWAY_BACKUP_SHA256] |
| Database backup (G2) | [DATABASE_BACKUP_SHA256] |
| SBOM (SPDX) | [SBOM_SHA256] |

### C.3 Credential handover (`docs/TURNOVER.md` Section 3)

| Item | Status |
| --- | --- |
| All factory and default credentials replaced | [TO_CREDS_REPLACED] |
| Credentials delivered in sealed envelope and encrypted file to [CUSTOMER_SECURITY_CONTACT] | [TO_CREDS_DELIVERED] |
| Customer changed every password during the meeting | [TO_CREDS_CHANGED] |
| Schreiber AI remote-support account | [REMOTE_SUPPORT_STATE] (enabled with signed consent [REMOTE_CONSENT_ID] / deleted in front of Customer) |
| Schreiber AI destroyed its copies of Customer-owned credentials | [TO_CREDS_DESTROYED] |
| Handover record signed (G4) | [TO_G4_SIGNED] |

### C.4 Training (`docs/TURNOVER.md` Section 4)

| Module | Attendees | Competency check passed | Trainer |
| --- | --- | --- | --- |
| T1 Safe entry and emergency response | [T1_ATTENDEES] | [T1_PASSED] | [T1_TRAINER] |
| T2 Dashboard and alarms | [T2_ATTENDEES] | [T2_PASSED] | [T2_TRAINER] |
| T3 Daily/weekly checks | [T3_ATTENDEES] | [T3_PASSED] | [T3_TRAINER] |
| T4 Power system operation | [T4_ATTENDEES] | [T4_PASSED] | [T4_TRAINER] |
| T5 Cooling system operation | [T5_ATTENDEES] | [T5_PASSED] | [T5_TRAINER] |
| T6 IT handover (Customer confirms PDU circuit map and rack labels) | [T6_ATTENDEES] | [T6_PASSED] | — |
| T7 Security and remote support | [T7_ATTENDEES] | [T7_PASSED] | [T7_TRAINER] |

### C.5 Monitoring and alarms live

| Item | Status |
| --- | --- |
| Managed Services: Schreiber AI monitoring live through remote support path | [TO_MONITORING_LIVE] |
| Self-operated: Customer confirmed receipt of a test alarm by [ALARM_FORWARDING] | [TO_ALARM_RECEIPT_CONFIRMED] |
| First 12 months of maintenance calendar delivered (D3) | [TO_MAINTENANCE_CALENDAR] |
| Spares kit delivered and counted (F1) | [TO_SPARES_DELIVERED] |
| OEM warranties registered in Customer's name (E1): UPS [OEM_WARRANTY_UPS_ID]; cooling [OEM_WARRANTY_COOLING_ID]; batteries [OEM_WARRANTY_BATTERY_ID]; fire panel [OEM_WARRANTY_FIRE_ID]; generator [OEM_WARRANTY_GEN_ID]; container [OEM_WARRANTY_CONTAINER_ID] | [TO_OEM_REGISTERED] |
| AHJ certificates in binder (H4): electrical final, mechanical final, fire final, certificate of occupancy or equivalent | [TO_AHJ_CERTS] |

### C.6 Open items (Punch List H2)

| # | Item | Class | Owner | Due | Status |
| --- | --- | --- | --- | --- | --- |
| [TO_PUNCH_1_ID] | [TO_PUNCH_1_ITEM] | [TO_PUNCH_1_CLASS] | [TO_PUNCH_1_OWNER] | [TO_PUNCH_1_DUE] | [TO_PUNCH_1_STATUS] |

No safety item is open. Holdback carried: [TO_HOLDBACK_TOTAL].

### C.7 Financial close-out

| Item | Amount ([CURRENCY]) |
| --- | --- |
| Milestone 4 ([MILESTONE_4_PCT] % of Unit price [PRICE_TOTAL] as amended) | [MILESTONE_4_AMOUNT] |
| Less liquidated damages credit (MSA 7.7): [LD_WEEKS_LATE] weeks x [CUSTOMER_LD_RATE_PCT_PER_WEEK] %, capped at [CUSTOMER_LD_CAP_PCT] % | ([LD_CREDIT_AMOUNT]) |
| Less Punch List holdback (released on closure) | ([TO_HOLDBACK_TOTAL]) |
| Plus Customer delay charges invoiced and unpaid (MSA 7.8) | [DELAY_CHARGES_OUTSTANDING] |
| Plus Change Orders invoiced on signature and unpaid | [CO_OUTSTANDING] |
| **Net due with this certificate** | **[TURNOVER_NET_DUE]** |

### C.8 Declaration

Both Parties confirm that `docs/TURNOVER.md` Section 5 is met: every Turnover Package line is delivered or justified; the credential handover record is signed; training modules are signed; no safety Punch List item is open; monitoring is live or alarm receipt is confirmed; AHJ certificates are in the binder. Turnover is complete on [TURNOVER_DATE]. The warranty runs from the SAT Certificate date [SAT_CERT_DATE] to [WARRANTY_END_DATE].

| | Schreiber AI | Customer |
| --- | --- | --- |
| Signature | ______________________ | ______________________ |
| Name | [SCHREIBER_ENG_SIGNATORY] | [CUSTOMER_SIGNATORY_NAME] |
| Title | | [CUSTOMER_SIGNATORY_TITLE] |
| Date | [TURNOVER_DATE] | [TURNOVER_DATE] |

---
Schreiber AI · BEN Engine (Business Edge Node) · Ben@SchreiberAI.com · Template maintained at `docs/contracts/ACCEPTANCE_CERTIFICATES.md` · TEMPLATE — not legal advice — have counsel review before use.
