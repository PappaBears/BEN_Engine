# Warranty Terms — BEN Engine Unit and Modules

> **TEMPLATE — not legal advice — have counsel review before use.**
> Schreiber AI · BEN Engine (Business Edge Node) · `docs/contracts/WARRANTY_TERMS.md` · Template rev [TEMPLATE_REV]
> Bracketed `[FIELDS]` are filled by the proposal generator from `docs/contracts/fields.json`. These Warranty Terms are incorporated into the MSA (Section 10) and issued as the warranty certificate in the Turnover Package (item E2). Delete this box before issue.

**Warranty certificate ID:** [WARRANTY_CERT_ID]
**Unit serial / Tier / Configuration:** [UNIT_SERIAL] / [TIER] / [CONFIG_ID]
**Customer:** [CUSTOMER_NAME]
**Site:** [SITE_NAME], [SITE_ADDRESS]
**Warranty start (SAT Acceptance):** [SAT_CERT_DATE]
**Workmanship warranty end:** [WARRANTY_END_DATE] ([WARRANTY_MONTHS] months)
**Delivery model:** [DELIVERY_MODEL]

## 1. Schreiber AI workmanship warranty

1.1 **Promise.** Schreiber AI warrants to Customer that for **12 months** ([WARRANTY_MONTHS] months) from SAT Acceptance the Unit, as a system, is free from defects in design, workmanship and integration and conforms to the frozen Configuration, the as-built drawings (Turnover item A2), the compliance pack for the profile, and the SAT Commissioning Report (Turnover item B2). "Workmanship" includes: container structural modification and welds; envelope (insulation, vapour barrier, liner, doors, seals, coatings, drains); mechanical fit-out (racks, containment, trays, anchors); electrical installation (terminations, conductors, raceway, grounding and bonding, labels); cooling installation (piping, brazing, pressure integrity, charge, glycol loop); controls panel assembly, wiring, node installation, sensor placement and calibration; firmware load and configuration; integration of OEM equipment; and the Services (engineering, FAT, transport preparation, set-down, hook-up, SAT, training).

1.2 **Performance conformance.** During the workmanship warranty the Unit will, when operated within the Configuration, continue to meet the acceptance criteria of SOW Section 8.1 steps 3 to 9 and the SAT measured values within the tolerances stated there (rack inlets within ASHRAE class [ASHRAE_CLASS] allowable at up to [IT_KW] kW IT load; N+1 failover without excursion where configured; meter-PDU reconciliation within 3 %; alarms raised and cleared). If Customer believes a performance criterion is no longer met, the step is re-run with the Commissioning Script; a FAIL within the warranty for a covered cause is a warranty defect.

1.3 **Envelope extended warranty.** The coating system and weather-tightness of the envelope (no water ingress through roof, walls, doors or penetrations under design conditions) is warranted for [ENVELOPE_WARRANTY_MONTHS] months (standard 36), subject to the annual envelope maintenance in `docs/MAINTENANCE.md` being performed and recorded.

1.4 **Structural warranty.** Modified container frame welds and reinforcing designed by Schreiber AI are warranted for [STRUCTURAL_WARRANTY_MONTHS] months (standard 60) against cracking or deformation under the design loads in the PE calculation, subject to the Unit not being moved except under Section 5.4.

1.5 **Remedy.** Schreiber AI will, at its option, repair the defect, replace the defective part or re-perform the defective Service, including labour, travel and parts, at no charge, within the response times in Section 6. Repaired or replaced items are warranted for the longer of the remaining warranty or 90 days. If Schreiber AI cannot repair or replace within 60 days of a confirmed claim, it will refund the portion of the Unit price attributable to the defective part or Service, as shown in the SOW price table and the as-built BOM.

1.6 **Exclusive remedy.** The remedies in these Warranty Terms are Customer's exclusive remedies for defects in the Unit and the Services. MSA Section 10.6 (disclaimer) and Section 11 (limitation of liability) apply.

## 2. Module-by-module warranty statement

| Module / element | Schreiber AI workmanship warranty | OEM warranty (pass-through, Section 3) | Notes |
| --- | --- | --- | --- |
| Enclosure (ISO container or NEMA 3R cabinet) | 12 months integration; 36 months envelope (1.3); 60 months structural (1.4) | Container: [OEM_WARRANTY_CONTAINER_TERM] (one-trip; typically limited to structural defects and CSC-related items, [OEM_WARRANTY_CONTAINER_ID]) | CSC plate validity is not warranted after modification (PROJECT_NOTES D20); the CSC decision record states the transport status |
| Envelope (insulation, liner, doors, coatings, seals) | 12 months; coating and weather-tightness 36 months | Door hardware per OEM; coating materials per manufacturer data sheet | Coating warranty requires annual survey and touch-up record (A1 form) |
| Power module: panelboard/switchboard, breakers, SPD | 12 months installation, terminations and labels | [OEM_WARRANTY_SWITCHGEAR_TERM] (typically 12–18 months from shipment or 12 from energisation) [OEM_WARRANTY_SWITCHGEAR_ID] | Torque records on Q-07 are the baseline |
| Power module: UPS | 12 months integration | [OEM_WARRANTY_UPS_TERM] (typically 12–24 months; OEM start-up may be required to activate) [OEM_WARRANTY_UPS_ID] | Capacitors and fans are wear items (3–7 years) |
| Power module: lithium (LFP) batteries | 12 months integration | [OEM_WARRANTY_BATTERY_TERM] (typically 5–10 years capacity warranty to a stated SOH, with cycle and temperature conditions) [OEM_WARRANTY_BATTERY_ID] | Battery cabinet temperature and BMS alarms must be acted on; charging below 0 °C is inhibited by BMS |
| Power module: transformers, PDUs, whips | 12 months | [OEM_WARRANTY_PDU_TERM] [OEM_WARRANTY_PDU_ID] | |
| Power module: generator and ATS (if fitted) | 12 months installation | [OEM_WARRANTY_GENERATOR_TERM] (typically 2 years / 1,000–2,000 hours standby) [OEM_WARRANTY_GEN_ID]; ATS [OEM_WARRANTY_ATS_TERM] | Monthly exercise log required |
| Cooling module: in-row DX / cabinet AC / condensers | 12 months installation, piping, charge | [OEM_WARRANTY_COOLING_TERM] (typically 12 months parts; compressor 5 years on some models) [OEM_WARRANTY_COOLING_ID] | Refrigerant is A1 GWP < 700 per D15; use of any other refrigerant voids |
| Cooling module: RDHx, CDU, dry cooler, manifolds | 12 months installation and glycol loop | [OEM_WARRANTY_CDU_TERM] [OEM_WARRANTY_CDU_ID] | Glycol concentration, pH and inhibitor per quarterly fluid report |
| Containment, racks | 12 months | Racks [OEM_WARRANTY_RACK_TERM] (often lifetime structural on major brands) [OEM_WARRANTY_RACK_ID] | Seismic kits installed per Q-05 |
| Fire detection and suppression | 12 months integration (dry-contact monitoring, HVAC shutdown wiring) | Fire panel [OEM_WARRANTY_FIRE_TERM] [OEM_WARRANTY_FIRE_ID]; agent system per licensed contractor [FIRE_CONTRACTOR_NAME] warranty [FIRE_CONTRACTOR_WARRANTY_TERM] | Semi-annual NFPA 2001 inspection is a condition; agent recharge after discharge is not a warranty item unless the discharge was caused by a defect |
| Controls module: BEN Controller panel (UL 508A panel build, PLCnext PLC and Axioline I/O, QUINT4 supplies, SPD, switch, relays, firewall) or BEN Controls Lite cabinet (RevPi Connect 4, DIO/AIO, supply, switch) | 12 months on the build; PLC, I/O, RevPi, supplies and switch per OEM (Phoenix Contact, KUNBUS, Moxa) | OEM warranties assigned to Customer | Panel wiring and labelling are workmanship (Section 3) |
| Controls module: BEN Pods (Schreiber AI design, contract-manufactured, provisioned) | **24 months** ([NODE_WARRANTY_MONTHS]) hardware, RMA under Section 7 | MGM240P module and sensors per their OEMs | Pt1000 strings, SHT45, SDP810 and the industrial transmitters are calibrated consumables; drift beyond specification after 12 months is a calibration item, not a defect; Pod W batteries are consumables (3–5 yr) |
| Controls module: edge computer (OnLogic Karbon 400, TPM, NVMe) | 12 months, RMA under Section 7; OEM extended warranty where purchased | Per OEM | Edge image and database are restored from backup (Turnover G2); TPM re-enrolment is part of the swap |
| BEN Controls software | Per Software Licence Section 12 | Open Components per their licences | |
| Compute module (if ordered) | 12 months installation and cabling | Servers and switches per OEM [OEM_WARRANTY_COMPUTE_TERM] [OEM_WARRANTY_COMPUTE_ID] | Customer-supplied compute is not covered |
| Site works by Schreiber AI (turnkey only) | 12 months | Concrete and materials per subcontractor | Customer-built pad is not covered |
| Spares kit items | Per OEM from delivery; Schreiber AI-programmed spare nodes 24 months | | |

## 3. OEM pass-through warranties

3.1 **Registration.** At Turnover Schreiber AI registers every OEM warranty in Customer's name and records the confirmation numbers in Turnover item E1 (the IDs in Section 2). Where an OEM requires factory start-up to activate the warranty (UPS, generator, CDU), Schreiber AI arranges it before SAT.

3.2 **Pass-through.** Schreiber AI assigns to Customer, to the extent assignable, all OEM warranties on components installed in the Unit. Where not assignable, Schreiber AI holds them for Customer's benefit and enforces them on Customer's request.

3.3 **Administration.** During the workmanship warranty (and for the Managed Services term, if ordered), Schreiber AI files and manages OEM claims, coordinates OEM technicians and installs OEM-supplied parts at no labour charge. After the workmanship warranty, for Units not under Managed Services, Schreiber AI will administer OEM claims at the field technician rate in the SOW, or Customer may deal with the OEM directly.

3.4 **Limits.** OEM warranties are the OEM's terms, not Schreiber AI's. Schreiber AI does not extend, broaden or guarantee an OEM warranty, and is not liable for an OEM's refusal of a claim for a reason within the OEM's terms (for example, operating hours, environmental conditions, missed OEM maintenance). Schreiber AI's workmanship warranty still covers its own installation of the OEM component.

3.5 **Start dates.** Some OEM warranties start at shipment from the OEM rather than at SAT. Where the gap exceeds [OEM_WARRANTY_GAP_MONTHS] months because of Customer-Caused Delay (storage of a finished Unit), Customer bears the shortened OEM term; where the gap is caused by Schreiber AI, Schreiber AI covers the component under its workmanship warranty for the shortfall.

## 4. Conditions of warranty

The warranties in Sections 1 and 2 apply only while all of the following are true:

4.1 The Unit is operated within the Configuration: IT load at or below [IT_KW] kW; rack inlet conditions within ASHRAE class [ASHRAE_CLASS]; containment closed and blanking panels in place; electrical vestibule and aisles free of storage.

4.2 The Unit is installed at the Site on the pad, anchorage and utility service described in the signed Site Requirements, and the Site values Customer provided (fault current, flood zone, wind, snow, seismic, corrosivity) are correct.

4.3 The Maintenance Schedule is performed at the stated intervals by the stated parties (R/L/S), including climate add-ons for [CLIMATE], and recorded on the forms in `docs/MAINTENANCE.md` Section 8 or the dashboard checklists. Under Managed Services this condition is Schreiber AI's responsibility except where Customer refuses access.

4.4 Work on refrigerant circuits is performed by EPA 608 certified technicians; work on power conductors by licensed electricians; work on the fire system by a licensed fire protection contractor; welding on the frame by a certified welder; and all such work is recorded.

4.5 Only Schreiber AI-approved spares and OEM parts are installed; only Signed Images are installed on Pods, the PLC and the edge computer.

4.6 Customer responds to Critical and Major alarms as described in the O&M manual (or Managed Services do so) and does not silence or disable alarms.

4.7 The edge computer database backup target is maintained so that calibration and maintenance records are recoverable.

## 5. What voids the warranty

The warranty does not cover, and Schreiber AI may void the affected part of the warranty for, defects or damage caused by any of the following:

5.1 **Outdoor exposure beyond the design class.** Operation in a climate package other than [CLIMATE] without a Change Order; corrosivity above ISO 9223 class [CORROSIVITY_CLASS] (for example relocation to a coastal site with a C3 coating system); outdoor temperature above the climate design temperature [CLIMATE_DESIGN_TEMP_C] °C for the capacity shortfall that results (Risk R04, R08); wind, snow, seismic or flood above the design values in the Configuration (Risk R10); wildfire, lightning without the LPS option, hail, or impact.

5.2 **Unapproved modifications.** Any penetration of the envelope, change to the electrical system, addition of batteries, change of refrigerant, change to the glycol, change to containment, change to the fire system, change to controls wiring, firmware or software not performed by Schreiber AI or its approved subcontractor or approved in writing; installation of an unsigned image; alteration of firewall rules shipped with the Unit except as `docs/CYBERSECURITY.md` allows.

5.3 **Missed maintenance.** Failure to perform or record a Maintenance Schedule task whose omission contributed to the defect (for example, filter change and the resulting coil icing; coil cleaning and the resulting high-pressure trips; glycol inhibitor and the resulting corrosion; door gasket conditioning and the resulting water ingress; battery BMS alarms ignored; generator not exercised).

5.4 **Moving the Unit without Schreiber AI.** Lifting, transporting, re-setting or relocating the Unit by anyone other than Schreiber AI or a rigger working to a Schreiber AI-reviewed lift plan under the relocation procedure in `docs/PROCESS_FLOW.md` Stage 22 and Stage 14 to 18 (refrigerant isolated or recovered, glycol drained to safe level, racks blocked and strapped, UPS and battery shipping brackets fitted, shock loggers fitted, new site survey and anchorage calc). The structural warranty (1.4) ends on any unauthorised move. Schreiber AI will quote relocation on request and the warranty continues after a Schreiber AI relocation, with the SAT re-run at the new Site.

5.5 **Customer IT equipment and workloads**, including heat loads above the Configuration, equipment that exhausts into the cold aisle, and power supplies that trip PDU breakers.

5.6 **Utility and site conditions.** Utility voltage, frequency or harmonics outside `docs/SITE_REQUIREMENTS.md` Section 5; fault current above the 65 kA SCCR without the current-limiting fuses Schreiber AI specified after notice (Risk R03); grounding electrode above 25 Ω; pad settlement or out-of-level beyond ±6 mm; drainage failure; fence or security failure leading to vandalism or theft.

5.7 **Misuse and accident**, including entry contrary to `docs/MAINTENANCE.md` Section 9, storage of combustibles inside, opening energised panels by unqualified persons, defeating door interlocks or the suppression abort, and fire or agent discharge caused by Customer equipment.

5.8 **Consumables and wear.** Air filters; batteries (beyond the OEM capacity warranty); UPS capacitors and fans; EC fan bearings after 3 years; door gaskets, sealant and touch-up after their maintenance replacement intervals; desiccants; lamps; emergency-light batteries; refrigerant lost through a leak that was not a workmanship defect; glycol; sensor drift within specification; agent after a discharge.

5.9 **Cosmetic** scratches, fading within the coating manufacturer's tolerance, and dents that do not affect function or weather-tightness.

## 6. Claim procedure

6.1 **Notice.** Customer notifies Schreiber AI of a suspected defect by the ticket portal [OPS_PORTAL_URL], email [WARRANTY_EMAIL] or phone [OPS_CENTER_PHONE] within 10 Business Days of discovery, with: Unit serial, alarm IDs or dashboard screenshots, the time of the event, photographs, and any maintenance records relevant to the affected subsystem. Under Managed Services, Schreiber AI's own alarm handling is notice.

6.2 **Acknowledgement and triage.** Schreiber AI acknowledges within 1 Business Day (Critical safety or availability defects: 4 hours), reviews the edge computer data (Customer grants read access to the diagnostics export or enables the remote support path for the case), and tells Customer within 3 Business Days whether the defect is covered, needs a site visit, or is excluded and why.

6.3 **Response times for covered defects.**

| Defect class | Example | On-site response | Repair target |
| --- | --- | --- | --- |
| Safety | Water ingress onto electrical equipment; structural crack; fire system integration fault; refrigerant leak into ITE space | Within 2 Business Days ([WARRANTY_SAFETY_RESPONSE_DAYS]) | Make safe at first visit; permanent repair within 15 Business Days |
| Availability | Loss of N+1; UPS integration fault; controls panel failure; alarm not raised | Within 5 Business Days ([WARRANTY_AVAILABILITY_RESPONSE_DAYS]) | Within 15 Business Days subject to OEM parts lead time; loan or spare fitted meanwhile where available |
| Performance | Inlet above class at design load; PUE deviation from SAT by > [PUE_DEVIATION_PCT] % attributable to a defect; sensor channel outside uncertainty after recalibration | Within 10 Business Days | Within 30 Business Days |
| Cosmetic / documentation | Coating defect without corrosion; label error; drawing error | Next scheduled visit or 30 Business Days | Within 60 Business Days |

6.4 **Investigation.** Where the cause is disputed, MSA Section 19.2 (technical expert) applies. If the investigation shows the defect is excluded under Section 5, Customer pays the investigation at the SOW field technician rate and travel at cost; otherwise Schreiber AI bears it.

6.5 **Access and conditions.** Customer provides access, a safe working environment and, where needed, a shutdown window. Delay in access extends the response and repair targets day for day.

6.6 **Records.** Every warranty event is recorded as an incident report (`docs/MAINTENANCE.md` Section 8) with cause, action and preventive action, and is added to the Unit's file in the Turnover Package.

6.7 **Replaced parts.** Replaced parts become Schreiber AI's property for failure analysis unless the OEM requires their return or Customer's security policy requires destruction on site (storage media are always sanitised or destroyed on site per NIST SP 800-88).

## 7. RMA procedure for BEN Pods and edge computers

7.1 **Scope.** BEN Pods (Schreiber AI PCBA with MGM240P module, sensors, enclosure; Pod W and Pod E) and edge computers (OnLogic Karbon 400 with NVMe, or RevPi Connect 4 on BEN Controls Lite) supplied with the Unit or as spares. PLC and I/O modules follow the Phoenix Contact OEM RMA with Schreiber AI handling the claim.

7.2 **Diagnosis.** Customer (or Schreiber AI under Managed Services) confirms the fault from the dashboard: Pod `status` shows `errors[]`, Pod offline with power / battery confirmed and two router neighbours in range (mesh health panel), Pod fails attestation, channel reading outside range after sensor swap, relay not reading back in the I/O test, or the edge computer failing its watchdog, A/B boot or TPM measurement.

7.3 **Swap first.** The spare Pod from the on-site kit (provisioned with its own certificate, calibrated as "spare, unassigned") is clipped into the failed Pod's position, joins the mesh and attests, is assigned its node_id and `cal_id` from the edge computer, and verified with the I/O test and sensor spot-check. Swap time is about 5 minutes; no wiring on a Pod W. A Pod that fails attestation is never re-flashed in the field. For an edge computer, the spare is imaged from the backup (Turnover G2), its TPM enrolled, and verified by step 2 (Pod discovery and attestation).

7.4 **RMA request.** Customer requests an RMA number at [RMA_EMAIL] or the portal with: Unit serial, Pod serial / node_id or edge computer serial, firmware version, attestation state, fault description, dashboard export of the Pod's last 24 hours of `status` and `telemetry`, and photographs. Schreiber AI issues the RMA number and a prepaid label within 2 Business Days.

7.5 **Shipment.** The failed item is shipped in the spare's packaging. Pod W batteries (2 × AA lithium) are removed before shipment; edge computers' NVMe drives are **removed and retained by Customer** (or sanitised per NIST SP 800-88 and the certificate attached) before shipment, so no Customer Data leaves the Site. Schreiber AI ships the replacement spare, provisioned with its own device certificate, the current signed firmware and a factory calibration with its `cal_id`, within [RMA_REPLACEMENT_DAYS] Business Days of issuing the RMA (advance replacement) so the kit is replenished before the failed unit arrives.

7.6 **Analysis.** Schreiber AI reports the failure cause within 20 Business Days. Failures caused by excluded causes (water, over-voltage on a field terminal, physical damage, unsigned firmware attempt) are charged at the spare-part price in the SOW.

7.7 **Firmware mismatch.** A replacement node with a newer firmware than the fleet is downgraded or the fleet is upgraded in a maintenance window so that step 2 (same firmware on every node) passes; mixed firmware is not left in service.

7.8 **Calibration after swap.** A swapped node triggers early recalibration of its channels under `docs/MAINTENANCE.md` Section 6(e), performed at the next visit or remotely verified against `T_ref` and the redundant string within 0.5 °C in the meantime.

## 8. Warranty transfer and relocation

8.1 The warranty transfers to a buyer of the Unit under MSA Section 21.3 provided the Unit is relocated by Schreiber AI (Section 5.4) or has not been moved.

8.2 Relocation by Schreiber AI: the workmanship warranty continues for its remaining term; the structural and envelope warranties continue; a re-run SAT at the new Site is the new performance baseline; relocation Services carry their own 12-month workmanship warranty.

## 9. Registration record

| Field | Value |
| --- | --- |
| Warranty certificate issued at Turnover | [TURNOVER_DATE] |
| OEM registrations (Turnover item E1) | UPS [OEM_WARRANTY_UPS_ID]; batteries [OEM_WARRANTY_BATTERY_ID]; cooling [OEM_WARRANTY_COOLING_ID]; CDU/dry cooler [OEM_WARRANTY_CDU_ID]; racks [OEM_WARRANTY_RACK_ID]; PDUs [OEM_WARRANTY_PDU_ID]; switchgear [OEM_WARRANTY_SWITCHGEAR_ID]; fire panel [OEM_WARRANTY_FIRE_ID]; generator [OEM_WARRANTY_GEN_ID]; container [OEM_WARRANTY_CONTAINER_ID]; compute [OEM_WARRANTY_COMPUTE_ID] |
| Warranty contact | [WARRANTY_EMAIL], [OPS_CENTER_PHONE], portal [OPS_PORTAL_URL] |
| RMA contact | [RMA_EMAIL] |
| Issued by | [SCHREIBER_SIGNATORY_NAME], [SCHREIBER_SIGNATORY_TITLE], Schreiber AI |

---
Schreiber AI · BEN Engine (Business Edge Node) · Ben@SchreiberAI.com · Template maintained at `docs/contracts/WARRANTY_TERMS.md` · TEMPLATE — not legal advice — have counsel review before use.
