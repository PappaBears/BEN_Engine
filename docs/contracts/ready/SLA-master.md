# Managed Services Agreement and Service Level Agreement (SLA) — BEN Engine

<img src="../../../brand/v2/lockup-deep.svg" alt="Schreiber AI" height="28">

> **TEMPLATE — not legal advice — have counsel review before use.**
> BEN Engine, by Schreiber AI · Rev 2 · `docs/contracts/MANAGED_SERVICES_SLA.md` · Template rev 4d362db
> Bracketed `[FIELDS]` are filled by the proposal generator from `docs/contracts/fields.json`. This SLA is attached to a SOW as Annex E when the delivery model is "managed" or Managed Services are ordered later. Delete this box before signature.

**SLA ID:** [SLA_ID]
**Under MSA / SOW:** [MSA_ID] / [SOW_ID]
**Unit serial / Site:** [UNIT_SERIAL] / [SITE_NAME], [SITE_ADDRESS]
**Tier / IT kW / Profile / Climate:** [TIER] / [IT_KW] kW / [PROFILE] / [CLIMATE]
**Service start:** SAT Acceptance date [SAT_CERT_DATE]
**Initial term:** 36 months

## 1. Service description

1.1 Schreiber AI will monitor, maintain and support the Unit so that Customer needs no data-center staff. The service covers the Unit's enclosure, structure, envelope, power module, cooling module, controls module and fire/life-safety interfaces. It does not cover Customer's IT equipment or workloads except where Section 1.3 says so.

1.2 **Service elements.**

| Element | What Schreiber AI does | Reference |
| --- | --- | --- |
| Remote monitoring | Watches the Unit through the outbound remote support path during Monitoring Hours; triages alarms; dispatches | Section 2, 3 |
| Preventive maintenance | Performs or procures every task in `docs/MAINTENANCE.md` at its interval, including climate add-ons for [CLIMATE] | Section 4 |
| Calibration | Annual sensor calibration (or trigger-based earlier), new `cal_id`, certificates | Section 4.3 |
| Firmware and software | Signed BEN Pod firmware, edge computer image and `ben_engine` updates; vendor equipment firmware review | Section 5 |
| Corrective maintenance | Diagnoses and repairs faults; manages OEM warranty claims; installs spares | Section 3, 6 |
| Reporting | Monthly report with PUE, availability, alarms, maintenance done, calibration status, CSV | Section 7 |
| Compliance records | Keeps refrigerant, fire inspection, electrical, battery and generator records; annual compliance review | Section 4.5 |
| Spares management | Holds and replenishes the on-site spares kit | Section 6.3 |
| Security operations | Weekly hash and log review, patching, backup verification, certificate expiry management | Section 5, 9 |

1.3 **Optional elements** (selected in Section 13): Customer IT hands-and-eyes (rack and stack, reboots, media swaps); managed firewall between the Unit and Customer LAN; 24x7 Monitoring Hours; on-site technician visits beyond the maintenance schedule; generator fuel management; compliance attestation support.

## 2. Monitoring hours and contacts

| Item | Value |
| --- | --- |
| Monitoring Hours | 24x7 automated intake; human triage of Critical 24x7; others Business Days (standard: 24x7 automated alarm intake with human triage of critical alarms 24x7; human review of non-critical alarms Business Days [BUSINESS_HOURS_START]–[BUSINESS_HOURS_END] [SITE_TIMEZONE]) |
| Schreiber AI operations centre | [OPS_CENTER_PHONE], [OPS_CENTER_EMAIL], ticket portal [OPS_PORTAL_URL] |
| Escalation (Schreiber AI) | L1 operations duty engineer → L2 controls engineer [L2_CONTACT] → L3 principal engineer [L3_CONTACT] → executive Ben Schreiber |
| Customer contacts | Operations [CUSTOMER_OPS_CONTACT]; IT/security [CUSTOMER_SECURITY_CONTACT]; site access [CUSTOMER_SITE_CONTACT_NAME], [CUSTOMER_SITE_CONTACT_PHONE]; executive [CUSTOMER_EXEC_SPONSOR] |
| Local technician (L) | [LOCAL_TECH_PROVIDER] (Schreiber AI field technician / Customer-employed technician trained to T3/T5) |
| Certified subcontractors (S) | Electrical [SUB_ELECTRICAL]; HVAC (EPA 608) [SUB_HVAC]; fire protection [SUB_FIRE]; generator [SUB_GENERATOR]; battery [SUB_BATTERY] |
| Nearest spares depot and travel time to Site | [SPARES_DEPOT], [TRAVEL_TIME_HOURS] h |

## 3. Alarm response

3.1 **Severity.** Alarms are classified by the edge computer (`ben/<unit>/alarm` severity) and confirmed by the duty engineer.

| Severity | Definition | Examples |
| --- | --- | --- |
| **Critical** | Immediate risk to IT availability, safety or the Unit | Rack inlet above ASHRAE allowable; both/all cooling units failed; UPS on battery with no utility and generator not running; fire panel alarm or supervisory; refrigerant or battery gas detection; leak under CDU/RDHx; door forced; edge computer unreachable and no Pod heartbeat for 10 minutes; security integrity failure (firmware hash changed) |
| **Major** | Redundancy lost or performance degraded; no immediate risk | One cooling unit failed (N+1 holding); UPS battery alarm; generator failed to start on exercise; inlet above ASHRAE recommended; Pod offline; dP outside band; backup job failed; failed logins above threshold |
| **Minor** | Maintenance or drift condition | Filter dP high; sensor pair drift > 0.5 °C; condensate pump cycling; certificate expiry < 90 days; run-hour imbalance; weather watch |
| **Informational** | Normal events | Door open with matching badge; maintenance mode; scheduled test |

3.2 **Response targets.**

| Severity | Acknowledge (human) | Remote action started | On-site arrival target | Restore / workaround target | Root-cause report |
| --- | --- | --- | --- | --- | --- |
| Critical | **15 minutes** 15 | 30 minutes | **4 hours** 4 (Site within [TRAVEL_TIME_HOURS] h travel; otherwise 8 h) | 8 hours or N+1 restored, whichever first | 5 Business Days |
| Major | 1 hour 1 | 2 hours | Next Business Day 1 | 3 Business Days (subject to OEM parts) | 10 Business Days |
| Minor | Next Business Day | Next Business Day | Next scheduled visit, or 10 Business Days | Next scheduled visit | In monthly report |
| Informational | Logged | — | — | — | — |

3.3 **Measurement.** Acknowledge time runs from the alarm timestamp (`ts`) in the edge computer to the duty engineer's acknowledgement in the dashboard, which is logged. On-site arrival time runs from acknowledgement to the technician's badge event at the Unit door. Targets are measured monthly and reported in Section 7.

3.4 **Actions Schreiber AI may take remotely without further consent**: acknowledge alarms; adjust cooling setpoints within the ASHRAE class; rotate cooling unit lead/lag; run the I/O test on non-life-safety outputs; enable fan boost; start a generator exercise; collect diagnostics; apply a security Update in an agreed maintenance window. **Actions requiring Customer consent at the time**: IT load-shed commands to Customer equipment; any change to firewall rules; emergency firmware Update outside a window; opening a PDU breaker.

3.5 **Life safety.** Fire suppression, EPO and HVAC shutdown on fire are hardwired and are never operated by Schreiber AI remotely. On a fire or gas alarm Schreiber AI calls the Customer emergency contact and, where the SOW assigns it, the central station, and dispatches the fire contractor.

## 4. Preventive maintenance and calibration

4.1 **Schedule.** Schreiber AI performs every task in `docs/MAINTENANCE.md` Sections 1 to 5 at the stated interval, as adjusted for climate [CLIMATE]:

| Interval | Performed by | Scope (summary; `docs/MAINTENANCE.md` governs) |
| --- | --- | --- |
| Weekly (remote) | R | Pod health, thermal trends, cooling rotation, UPS SOC and PDU-vs-meter check, leak/door log match, fire supervisory, drift report, security hashes and backup status, weather watch |
| Monthly (on site, 1–2 h) | L | Envelope walk-around with photos (M1), structure, filters and coils, condensate pour test, UPS log, battery cabinet temperature, generator exercise ≥ 30 min at ≥ 30 % load, fire visual, controls cabinet, housekeeping |
| Quarterly | L + S | Coil cleaning, fluid sample (glycol %, pH, inhibitor) for liquid tiers, BMS report, UPS self-test and ATS exercise, door gaskets and roof sealant, sensor spot-check within 0.5 °C, relay I/O test, credential rotation, backup restore test (file-level) |
| Semi-annual | S | NFPA 2001 Ch. 8 clean agent inspection; refrigerant leak check and AIM Act leak-rate record (EPA 608 technician); thermography of all terminations at ≥ 40 % load; generator fuel polishing and load test |
| Annual | R + L + S | Sensor calibration (Section 4.3); firmware and OS update, full edge computer image backup, certificate review; torque check of feeders, breaker exercise, trip settings vs study, SPD, ground electrode test, UPS battery runtime test; NFPA 72 annual detection test and door fan test if penetrations changed; coating survey and touch-up; anchor torque and level; cooling performance check vs commissioning sweep; compliance review (AIM Act, NFPA 855, arc-flash labels, SPCC) |
| 3-year | S / R + L | UPS service (fans, capacitors inspection), ATS contacts, generator battery; EC fan replacement where noisy, filter-driers, glycol re-inhibit, CDU seals; sensor string replacement where drift > 0.3 °C, dP tubing, spare node rotation; agent cylinder hydrostatic schedule check |
| 5-year | S / PE | UPS capacitor and fan replacement; lithium battery SOH review (< 80 % replaced); full recoat (C4/C5) or spot repair; roof coating, gaskets, sealant; PE weld and anchorage inspection; dry cooler coil assessment; agent cylinder requalification; gateway hardware refresh and database migration |
| Climate add-ons | per `docs/MAINTENANCE.md` Section 5 | [CLIMATE_ADDONS_SUMMARY] (for example hot_arid: filters bi-weekly in dust season, coil clean monthly; cold: pre-winter checklist in October; coastal: coil rinse monthly, coating survey semi-annual) |
| Pre-storm | L | Louvre storm covers, dry cooler secured, fuel topped, UPS at 100 %, spares staged, flood barriers, photographs |

4.2 **Who pays for what.** Labour, travel and consumables for scheduled maintenance (filters, gaskets, sealant, touch-up paint, glycol top-up, test strips, biocide, emergency-light batteries) are included in the fee. Replacement of major components outside warranty (UPS capacitors and fans at 3–5 years, battery modules, EC fans, compressors, agent cylinders, dry cooler coils, edge computer hardware refresh) is charged at cost plus 15 % with Customer's approval, unless Section 13 selects the "all-inclusive lifecycle" option at [LIFECYCLE_UPLIFT_PCT] % uplift.

4.3 **Calibration.** Every sensor channel is calibrated at least every **12 months** against traceable references (temperature at 3 points, RH at 2 points, dP at zero and span, 4–20 mA at 4/12/20 mA), a new `cal_id` is issued and certificates with GUM uncertainty budgets are delivered (`calibration.py`). Early recalibration is triggered by the rules in `docs/MAINTENANCE.md` Section 6 (pair disagreement > 0.5 °C for 3 weeks; dP tare drift > 1 Pa; RH disagreement > 3 %RH; loop outside 3.8–20.5 mA; after Pod replacement or ADC-affecting firmware). A channel may be extended to 18 months after two consecutive calibrations with drift under half its uncertainty, by documented decision shared with Customer.

4.4 **Records.** Every task writes a signed record to the edge computer database (dashboard checklist) and to Schreiber AI's records; forms M1, Q1, A1, calibration certificates, refrigerant service record, fire inspection, electrical maintenance record and incident report per `docs/MAINTENANCE.md` Section 8 are available in the dashboard and in the monthly report.

4.5 **Compliance records kept for Customer.** Refrigerant records with technician EPA 608 numbers; NFPA 2001 and NFPA 72 inspection reports; NFPA 110 generator logs; battery BMS and SOH reports; thermography; ground resistance; arc-flash label currency; SPCC review notes; SBOM and firmware hashes. These are Customer Data and are exported with the Unit at the end of the term.

## 5. Firmware, software and security operations

5.1 BEN Pod firmware and edge computer Updates are Signed Images applied in **maintenance windows** agreed as: second Tuesday monthly (standard: second Tuesday of each month, [MAINTENANCE_WINDOW_START]–[MAINTENANCE_WINDOW_END] [SITE_TIMEZONE]), with 5 Business Days' notice of content and A/B rollback. Critical security Updates may be applied within 72 hours on 24 hours' notice.

5.2 Vendor equipment firmware (UPS, cooling, PDU, fire panel, BMS, door controller) is reviewed quarterly and applied during maintenance visits through the vendor's signed process.

5.3 Weekly security review: firmware hashes unchanged; failed logins; backup job success; patch status; certificate expiry; remote-support session log. Findings go to the monthly report; incidents follow Section 9.

5.4 Nightly database backup to [BACKUP_TARGET]; file-level restore test quarterly; full restore to a spare edge computer annually.

## 6. Corrective maintenance, parts and spares

6.1 **Included.** Diagnosis, remote and on-site labour, travel within [TRAVEL_TIME_HOURS] h, and installation of spares for any fault in the Unit's covered scope.

6.2 **Parts.** During the workmanship warranty and OEM warranties Schreiber AI manages the claim and the Customer pays nothing for covered parts. Outside warranty, parts are charged per Section 4.2.

6.3 **Spares kit.** Schreiber AI keeps the on-site spares kit (`docs/MAINTENANCE.md` Section 7) at the listed quantities for [TIER], replenishing used items within 10 Business Days; refrigerant cylinders are held by the HVAC subcontractor where local rules require.

6.4 **BEN Pod and edge computer swaps** follow the RMA procedure in `docs/contracts/WARRANTY_TERMS.md` Section 7; a spare Pod is swapped within the on-site target for the alarm severity and recalibrated or given its stored `cal_id`.

## 7. Reporting

7.1 **Monthly report**, delivered by the 10th of the following month as PDF and CSV, containing:

| Section | Content |
| --- | --- |
| Availability | Availability percentage per Section 8 with every exclusion listed and justified |
| PUE | Monthly average PUE from the E9-reconciled meters (utility kWh / IT kWh), daily PUE trend, comparison with the Proposal estimate [PUE_ESTIMATE] and the SAT measurement [SAT_STEP5_PUE] |
| Thermal | Max and 95th-percentile rack inlet per rack vs ASHRAE class [ASHRAE_CLASS]; hours above recommended; dP trend |
| Power | IT kW profile, peak, UPS events and runtime, generator runs, PDU-vs-meter disagreement, THD at PCC if metered |
| Alarms | Count by severity; each Critical and Major with timestamps, acknowledge and restore times vs targets, root cause |
| Maintenance | Tasks completed with form references; tasks deferred and why; next 60 days' plan |
| Calibration | Channels due, drift report summary, any triggered recalibration |
| Security | Hash integrity, patch status, backup success, remote-support sessions (who, when, duration), certificate expiries |
| Spares | Kit inventory and replenishment |
| Service credits | Calculation per Section 8.5 |
| Data | CSV extract of 1-minute aggregates for the month, and alarm log CSV |

7.2 **Quarterly review meeting** (remote, 1 hour) and **annual review** (on site, with the annual maintenance visit) to review trends, twin fit, capacity headroom and recommendations.

7.3 **Real-time access.** Customer keeps full dashboard access at all times; Managed Services do not reduce Customer's visibility or export rights.

## 8. Availability

8.1 **Definition.** "**Infrastructure Availability**" for a month is:

Infrastructure Availability (%) = (Total Minutes − Infrastructure Downtime Minutes + Excluded Minutes) / Total Minutes × 100

where "**Infrastructure Downtime**" is any period in which the Unit fails to deliver to Customer's IT equipment **both** (a) conditioned power at any rack PDU rated for the Configuration and (b) rack inlet conditions within the ASHRAE class [ASHRAE_CLASS] **allowable** envelope, as recorded by the gateway, for a cause within the Unit's covered scope.

8.2 **Target.** [AVAILABILITY_TARGET_PCT] % per month (standard: N profiles 99.5 %; N+1 profiles 99.9 %; 2N profiles 99.99 %), consistent with the design basis in `docs/COMPLIANCE.md` Section 5 (TIA-942 Rated-2/Rated-3 concepts, not Uptime Tier certification).

8.3 **Excluded Minutes** (not counted as downtime):

1. Utility power outage, under-voltage or frequency excursion outside `docs/SITE_REQUIREMENTS.md` Section 5 power quality limits, beyond the UPS runtime and generator capability stated in the Configuration (10 min; generator False).
2. Customer IT equipment faults, misconfiguration, IT load above [IT_KW] kW, blocked containment or removed blanking panels.
3. Customer network, fiber or ISP outages, and Customer firewall changes.
4. Scheduled maintenance windows (Section 5.1) and scheduled maintenance visits announced 5 Business Days ahead, up to 8 hours per month.
5. Customer-requested shutdowns, tests or load-shed.
6. Denial or delay of Site access, or unsafe Site conditions preventing entry under `docs/MAINTENANCE.md` Section 9.
7. Force Majeure under MSA Section 17, including weather beyond the design values in the Configuration (wind, snow, flood, outdoor temperature above the climate design temperature [CLIMATE_DESIGN_TEMP_C] °C).
8. Fire, battery or refrigerant events initiated by Customer equipment or by Customer's violation of the entry procedure, and the AHJ-mandated downtime after any discharge.
9. Failures of Customer-supplied site works (grounding, pad, drainage, fencing) and Customer-side utility equipment (disconnect, feeder, transformer).
10. Customer refusal of a recommended Update, repair or part replacement after written notice of the availability risk.
11. Periods in which the remote support path is disabled by Customer and the fault could have been detected or corrected remotely, for the time until Schreiber AI is notified.

8.4 **Not excluded.** Failure of a Schreiber AI-maintained component within its service life; a maintenance task Schreiber AI missed; a sensor drift Schreiber AI failed to detect under Section 4.3; a firmware Update that fails and does not roll back.

8.5 **Service credits.** If Infrastructure Availability in a month falls below the target, Customer receives a credit against the next invoice:

| Infrastructure Availability in the month | Credit (percentage of that month's Managed Services fee) |
| --- | --- |
| Below target but ≥ target − 0.1 percentage points | 10 % (standard 10 %) |
| Below target − 0.1 but ≥ target − 0.5 percentage points | 25 % (standard 25 %) |
| Below target − 0.5 but ≥ target − 1.0 percentage points | 50 % (standard 50 %) |
| Below target − 1.0 percentage points | 100 % (standard 100 %) |

Response-time credits: for each Critical alarm acknowledged later than 15 minutes or with on-site arrival later than the target, a credit of 5 % of the monthly fee per miss, up to 25 % per month.

Credits are capped at 100 % of the monthly fee in total, are Customer's sole remedy for missed availability and response targets, and count toward the MSA liability cap. Customer must claim a credit within 60 days of the report that shows the shortfall; Schreiber AI will compute credits proactively in the report.

8.6 **Chronic failure.** If Infrastructure Availability falls below target − 1.0 percentage points in any 3 months of a rolling 12-month period for causes not excluded, Customer may terminate this SLA on 30 days' notice without the termination charge in Section 11.3.

## 9. Security incidents and remote support rules

9.1 The remote support path is as described in `docs/CYBERSECURITY.md` Section 6: outbound-only WireGuard from the edge computer to Schreiber AI's operations endpoint, certificate-pinned, keys rotated yearly, no inbound ports at the Site.

9.2 **Rules of use.** Every session is under a named Schreiber AI account with key plus hardware token; every session is logged locally and at Schreiber AI; Customer can watch sessions live in the dashboard and can revoke access at any time by the key switch or in software; Schreiber AI accesses only the Unit's controls zones (Z1, Z2) and never Customer's IT equipment or enterprise network (Z3) unless the optional IT hands-and-eyes service is selected and the specific access is agreed in writing; no Customer Data is copied off the edge computer except diagnostics needed for a case and the reporting aggregates in Section 7; session logs are included in the monthly report.

9.3 **Key switch disabled.** If Customer disables the remote support path, Schreiber AI's response targets run from the time Customer notifies the operations centre of an alarm, and Section 8.3 item 11 applies. Air-gapped Sites receive the on-site-only service variant at the fee in Section 12.

9.4 **Incident handling.** Schreiber AI notifies Customer within 72 hours of confirming a security incident affecting the Unit's controls layer, follows the incident steps in `docs/CYBERSECURITY.md`, preserves logs, and delivers a report within 10 Business Days. Customer notifies Schreiber AI within 72 hours of an incident on Customer's network that may reach the Unit.

9.5 **Vulnerabilities.** Confirmed exploitable vulnerabilities affecting the Unit are notified within 72 hours and patched per Section 5.1.

## 10. Customer obligations

10.1 **Access.** Give Schreiber AI, the local technician and certified subcontractors Site access within [SITE_ACCESS_RESPONSE_HOURS] hours for Critical alarms and by appointment for scheduled visits; keep the badge list current; provide a safe route and lighting; keep the equipment yard clear.

10.2 **Network.** Keep the edge computer's outbound path (Customer internet or the Schreiber AI LTE/5G modem) available; keep the firewall between the Unit and the Customer LAN in place; provide an NTP source or allow GPS time; do not change the shipped controls-panel firewall rules without notice.

10.3 **Operate within the Configuration.** IT load ≤ [IT_KW] kW; containment closed and blanking panels fitted; no storage in the vestibule or aisles; no unapproved batteries or refrigerant equipment; follow the entry procedure in `docs/MAINTENANCE.md` Section 9 and the arc-flash labels.

10.4 **Approvals.** Approve or decline recommended out-of-warranty parts within 10 Business Days; approve maintenance window changes within 5 Business Days.

10.5 **Utilities and consumables.** Provide electricity, water, generator fuel (unless fuel management is selected), telecom circuits and waste disposal.

10.6 **Alarm receipt.** Keep the Customer emergency contact reachable 24x7 and acknowledge Schreiber AI's calls for fire, gas, leak and door-forced alarms.

10.7 **Backup target.** Provide and maintain the backup target [BACKUP_TARGET] with 500 GB capacity, or accept the second-SSD option.

## 11. Term, renewal and termination

11.1 **Term.** From SAT Acceptance for 36 months, renewing for successive 12-month periods unless either Party gives 90 days' notice.

11.2 **Price adjustment at renewal.** The fee may be adjusted at each renewal by the change in CPI-U over the prior 12 months, capped at 5 %.

11.3 **Termination for convenience by Customer.** On 90 days' notice at any time after the first 12 months, paying a termination charge of 3 months' fees, except under Section 8.6.

11.4 **Termination for breach.** MSA Section 18.2 applies.

11.5 **Transition.** On expiry or termination Schreiber AI will, for up to 90 days: hand over all maintenance and compliance records and the calibration certificates; deliver the first-12-months maintenance calendar for self-operation; rotate all credentials to Customer and delete the Schreiber AI remote-support account in front of Customer; convert the Software Licence to Type A under the Software Licence Section 2.2; train Customer's technician (T3, T5, T7 refresh) at the rates in the SOW; and return or destroy Customer Data held by Schreiber AI with a certificate.

## 12. Pricing

| Item | Rate | Basis |
| --- | --- | --- |
| **Managed Services fee** | **USD 45 per kW-month x [IT_KW] kW = [SLA_MONTHLY_FEE] per month** | Design IT kW in the Configuration, not metered load; standard rate basis in `docs/investors/VC_PROPOSITION.md` ($45/kW-month reference) |
| Minimum monthly fee | [SLA_MINIMUM_MONTHLY_FEE] | BEN 5 and small BEN 30 Units |
| 24x7 human triage of all severities (option) | + [OPTION_24X7_UPLIFT_PCT] % | |
| All-inclusive lifecycle parts (option) | + [LIFECYCLE_UPLIFT_PCT] % | Covers Section 4.2 major components |
| IT hands-and-eyes (option) | [OPTION_HANDS_EYES_FEE] per month plus [RATE_FIELD_TECH] per hour | |
| Managed firewall (option) | [OPTION_FIREWALL_FEE] per month | |
| Generator fuel management (option) | [OPTION_FUEL_FEE] per month plus fuel at cost | |
| Air-gapped (on-site-only) variant | [SLA_AIRGAP_RATE_PER_KW_MONTH] per kW-month | Monthly on-site visit replaces remote weekly checks |
| Out-of-scope work | SOW Section 7.5 rates | |
| Invoicing | Monthly in advance; payment 30 days | Credits applied to the next invoice |

## 13. Options selected for this Unit

| Option | Selected |
| --- | --- |
| 24x7 human triage of all severities | False |
| All-inclusive lifecycle parts | False |
| IT hands-and-eyes | False |
| Managed firewall | False |
| Generator fuel management | False |
| Air-gapped variant | False |
| Compliance attestation support (HIPAA / PCI / CMMC templates) | False |
| Additional scheduled visits per year | False |

## 14. Signatures

| | Schreiber AI | Customer |
| --- | --- | --- |
| Entity | Schreiber AI | [CUSTOMER_NAME] |
| Signature | ______________________ | ______________________ |
| Name | Ben Schreiber | [CUSTOMER_SIGNATORY_NAME] |
| Title | Founder | [CUSTOMER_SIGNATORY_TITLE] |
| Date | [SIGNATURE_DATE_SCHREIBER] | [SIGNATURE_DATE_CUSTOMER] |

---
BEN Engine, by Schreiber AI · Rev 2 · Ben@SchreiberAI.com · Template maintained at `docs/contracts/MANAGED_SERVICES_SLA.md` · TEMPLATE — not legal advice — have counsel review before use. Schreiber AI is a Schreiber Holding LLC company.
