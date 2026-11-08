# Statement of Work (SOW) — BEN Engine Unit

> **TEMPLATE — not legal advice — have counsel review before use.**
> Schreiber AI · BEN Engine (Business Edge Node) · `docs/contracts/SOW_TEMPLATE.md` · Template rev da41cc2
> Bracketed `[FIELDS]` are filled by the proposal generator from `docs/contracts/fields.json`. The configuration block in Section 2 is pasted verbatim from the frozen `config.json`. Delete this box before signature.

**SOW ID:** SOW-BEN20-20261108-4842D366
**Under MSA:** MSA-ACMECLINIC-2026 dated [EFFECTIVE_DATE] between Schreiber AI ("Schreiber AI") and Acme Clinic ("Customer")
**Proposal:** SAI-BEN20-20261108-4842D366 dated 2026-11-08
**Unit serial (assigned at H4):** BEN-BEN20-4842D366
**Site:** Austin, TX, Austin, TX
**SOW date:** 2026-11-08

This SOW orders one BEN Engine Unit and the Services for it under the MSA. Capitalised terms have the meanings in the MSA. If this SOW conflicts with the MSA, this SOW governs only where it names the MSA section it overrides (MSA Section 2.2).

## 1. Delivery model and modules

| Item | Selection |
| --- | --- |
| Tier | ben20 (BEN Micro / BEN 10 / BEN 20 / BEN 40) |
| Delivery model | Managed service (hardware only / hardware + BEN Controls / white-label / managed) |
| Modules ordered | power, cooling, compute, controls (any of: power, cooling, compute, controls) |
| White-label | false (yes / no); brand to apply: Schreiber AI |
| Managed Services | true (yes / no); if yes, SLA `docs/contracts/MANAGED_SERVICES_SLA.md` rev da41cc2 attached, term 36 months |
| Turnkey site works by Schreiber AI | no (yes / no / partial, list: [TURNKEY_SITE_WORKS_LIST]) |
| Factory | [FACTORY_NAME], [FACTORY_ADDRESS] (Schreiber AI facility or Contract Manufacturer under `docs/contracts/CONTRACT_MANUFACTURING_AGREEMENT.md`) |
| Schreiber AI project manager | [SCHREIBER_PM_NAME], [SCHREIBER_PM_EMAIL], [SCHREIBER_PM_PHONE] |
| Customer project manager | [CUSTOMER_PM_NAME], [CUSTOMER_PM_EMAIL], [CUSTOMER_PM_PHONE] |
| Customer site contact | [CUSTOMER_SITE_CONTACT_NAME], [CUSTOMER_SITE_CONTACT_PHONE] |

## 2. Configuration

2.1 **Frozen configuration.** The Configuration below is identified as SAI-BEN20-20261108-4842D366-cfg-v1.0 and conforms to `spec/ben-config.schema.json`. It is frozen at Hold Point H4. Before H4 the values are the Proposal values and may be adjusted by agreement without a Change Order; after H4 every change is a Change Order.

```json
{
  "tier": "ben20",
  "profile": "healthcare",
  "it_kw": 50.0,
  "racks": 5,
  "cooling": "rdhx_drycooler",
  "redundancy": "2N",
  "climate": "hot_humid",
  "subsystems": [
    "power",
    "cooling",
    "compute",
    "controls"
  ],
  "white_label": false,
  "brand": "Schreiber AI",
  "ups_minutes": 10,
  "generator": true,
  "site_name": "Austin, TX",
  "controls_tier": "auto"
}
```

2.2 **Configuration summary (generated from the JSON by `software/ben_engine/config.py`).**

| Field | Value |
| --- | --- |
| `tier` | ben20 |
| `profile` (mission profile) | healthcare (ai_inference / ai_training / private_cloud / disaster_recovery / industrial_ot / healthcare / public_sector / off_grid) |
| `it_kw` (design IT load) | 50 kW |
| `racks` | 5 |
| `cooling` | Rear-door heat exchanger + dry cooler (cabinet_dx / inrow_dx / inrow_dx_300 / rdhx_drycooler / dlc_cdu) |
| `redundancy` | 2N (N / N+1 / 2N) |
| `climate` | hot_humid (temperate / hot_arid / hot_humid / cold / coastal / high_altitude) |
| `ups_minutes` | 10 min |
| `generator` | true |
| ASHRAE class (from profile) | A1 |
| Service voltage / feeder breaker | 480 V 3ph / 100 A |
| Total electrical demand | 60.8 kVA |
| UPS | 2 x 61 kVA; battery 9.3 kWh (NFPA 855 package: false) |
| Cooling units | 4 (including redundancy) |
| Controls tier | BEN Controls Pro |
| BEN Pods | 12 plus spares per `docs/MAINTENANCE.md` Section 7 (logical node ids: 4) |
| Estimated PUE (model, to be measured at SAT) | 1.185 |
| Gross shipped mass (to be weighed at Q-11) | 8,274 kg |
| Design wind speed / exposure / seismic category / snow load | 58 m/s (ASCE 7 basic; confirm per site) / [EXPOSURE_CATEGORY] / [SEISMIC_CATEGORY] / [SNOW_LOAD] |
| Corrosivity class (ISO 9223) | C4 |

2.3 **Repository document revisions that apply to this Unit.**

| Document | Revision |
| --- | --- |
| `docs/PROCESS_FLOW.md` | da41cc2 |
| `docs/SITE_REQUIREMENTS.md` (signed copy attached as Annex A) | da41cc2 |
| `docs/COMPLIANCE.md` compliance pack for profile healthcare | da41cc2 |
| `docs/TEST_GUIDE.md` | da41cc2 |
| `docs/TURNOVER.md` | da41cc2 |
| `docs/MAINTENANCE.md` | da41cc2 |
| `docs/RISK_REGISTER.md` (risk acknowledgement signed [RISK_ACK_DATE]) | da41cc2 |
| `docs/CYBERSECURITY.md` | da41cc2 |
| `design/assembly/QC_FORMS.md` (Q-01 to Q-12) | da41cc2 |
| `spec/PROTOCOL.md`, `spec/INTERFACES.md` | da41cc2 |
| Issue-for-construction drawing set `design/drawings/ben20/` | issued at H4, index IFC Rev A (da41cc2) |

## 3. Scope by module

Mark each row **Included** or **Excluded**. Excluded rows are Customer's responsibility or are not part of this Unit.

### 3.1 Enclosure, structure and envelope (always included with any module)

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| One-trip high-cube ISO container (ben20) or NEMA 3R outdoor cabinet on skid (BEN Micro), received and inspected (Q-01, W6) | Included | |
| Structural modification by AWS D1.1 certified welder to IFC drawings; CWI inspection (H7, Q-02) | Included | Not applicable to BEN Micro |
| Envelope: 100 mm PIR/spray-foam insulation, vapour barrier, non-combustible liner, personnel doors with panic hardware, coating system to ISO 9223 class C4, seals, drains (W8, Q-03) | Included | |
| Electrical vestibule 1.1 m (BEN 20/40); second egress door (BEN 40 at ≥ 1000 A) | Included | |
| Floor channels, anchor clips, torque record (Q-04) | Included | |
| Lighting, emergency lighting (90-minute self-contained), signage (arc-flash, NFPA 704, refrigerant, agent, entry procedure) | Included | |
| Door access control (badge reader, camera on controls LAN) | Included | |
| PE-stamped anchorage and foundation drawing for the Site (climate wind speed 58 m/s (ASCE 7 basic; confirm per site), seismic [SEISMIC_CATEGORY]) | Included | Drawing only; civil works per Section 3.7 |
| Transport preparation (Q-11), CSC decision record, shock loggers, weigh ticket | Included | |

### 3.2 Power module

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| Main panelboard/switchboard rated 100 A, SCCR 65 kA, SPD | Included | |
| UPS 2 x 61 kVA, UL 1778, with lithium (LFP) battery 9.3 kWh, UL 1973 / UL 9540 | Included | NFPA 855 package where ≥ 20 kWh: false |
| Step-down transformers 480→208Y/120 V (BEN 20/40) | Included | |
| Rack PDUs (A/B per rack, metered), whips, receptacles | Included | |
| Power meters per power path; E9 reconciliation | Included | |
| Grounding and bonding inside the Unit; two 2/0 AWG bonding lugs at diagonal corners | Included | Site electrode per Section 3.7 |
| Arc-flash and coordination study (IEEE 1584), provisional labels at FAT, final labels at SAT with utility data | Included | Requires utility fault current from Customer (Risk R03) |
| Generator 80 kW with ATS (UL 1008), sub-base tank, NFPA 110 acceptance | Included | Only if `generator` = true |
| Cooling on UPS / mechanical ride-through path | Included | Profile option (PROJECT_NOTES D7) |
| Electrical installation by licensed electrical contractor; H10a rough-in, H10b torque and megger (≥ 100 MΩ at 1 kV), bonding ≤ 0.1 Ω (Q-07) | Included | |

### 3.3 Cooling module

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| Cooling type Rear-door heat exchanger + dry cooler: 4 units, A1 refrigerant GWP < 700 (R-513A or R-515B) for DX tiers; no A2L inside the ITE space (PROJECT_NOTES D15) | Included | |
| Condensers / dry cooler / CDU and external piping to the equipment yard | Included | |
| Hot-aisle containment, blanking panels, cable brush grommets | Excluded | |
| Glycol loop fill (propylene glycol 25 %), drip trays, rope leak detection, condensate pump with float alarm | Included | RDHx / DLC only |
| Refrigerant detector, purge ventilation, HVAC shutdown relay from fire panel | Included | |
| Installation by licensed HVAC contractor with EPA 608 technicians; H11 pressure test (1.1× design, 24 h) and evacuation (≤ 500 µm) (Q-06) | Included | |
| Economizer / free cooling | Excluded (option) | |
| Low-noise fans / acoustic barrier option | Excluded (option) | Per noise prediction vs ordinance |

### 3.4 Compute module

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| Racks 5 x 42U/48U, 1,360–1,590 kg rated, seismic kits, anchored (Q-05) | Included | Racks are included with Cooling or Power module even if Compute is excluded |
| Reference compute set: Reference GPU/CPU node set from the catalog (CMP- lines) | Included | Customer-supplied if excluded; Schreiber AI provides rack space, circuits and cooling only (MSA 4.5) |
| Network: ToR switches, structured cabling, fiber patching to the communications entry plate | Included | |
| IT burn-in load for SAT (load banks if Customer IT not available) | Included (FAT/SAT rental) | Load bank rental at cost |

### 3.5 Controls module (BEN Controls)

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| BEN Controller, tier BEN Controls Pro: Pro = UL 508A listed panel with Phoenix Contact PLCnext AXC F 2152 PLC and Axioline F I/O, OnLogic Karbon 400 edge computer (TPM 2.0), redundant QUINT4 24 V DC supplies, surge protection, managed switch, interface relays, firewall, remote-support key switch; Lite = DIN-rail cabinet with Revolution Pi RevPi Connect 4 controller and DIO/AIO modules, 24 V DC supply, switch, watchdog relay | Included | |
| BEN Pods x 12 on the BEN Mesh (Thread/IPv6, Silicon Labs MGM240P with Secure Vault, per-Pod certificate and attestation), with Pt1000 probe strings, SHT45, SDP810, rope leak, door reed, 4–20 mA inputs, pulse input per `spec/PROTOCOL.md`; wired transmitters on the PLC (Pro): Setra 264 dP, Vaisala HMW90 RH, RLE LD2100 leak controller | Included | |
| Signed firmware load, per-node certificates, `cal_id` applied, factory calibration with traceable references (Q-08, W12) | Included | |
| Modbus/SNMP integration to UPS, cooling units, PDUs, meters, fire panel dry contacts (monitor only), door controller | Excluded (option) | |
| Dashboard (live data, 3-D twin, alarms, sweeps, CSV export, I/O test, calibration), digital twin fitted from commissioning data | Included | |
| Software Licence per `docs/contracts/SOFTWARE_LICENSE_BEN_CONTROLS.md`: [LICENSE_TYPE] | Included | perpetual per-Unit / subscription / white-label |
| Remote support path (outbound WireGuard) | Included | enabled / disabled (air-gap) per consent form |
| Alarm forwarding to Customer systems (SNMP trap / syslog / webhook); read-only API | Included | |
| Backup target for the edge computer database (Customer SMB/NFS/S3 or second SSD) | Included | |

### 3.6 Fire and life safety (always included with container tiers)

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| VEWFD aspirating smoke detection plus spot detectors; UL 864 releasing panel; outdoor horn/strobe | Included | |
| Clean agent system (FK-5-1-12 class) with 10-minute hold, pre-discharge delay, abort station, door fan test (Q-09) | Included | BEN 10/20/40; BEN Micro: aerosol unit, detection and extinguisher |
| EPO at exit door; HVAC shutdown on second-stage alarm | Included | Hardwired, never on the controls bus |
| Fire marshal plan review and permit by licensed fire protection contractor | Included (submittal support; Customer pulls permit) | |
| Connection to central station / Customer monitoring | Included | Site-dependent |

### 3.7 Site works and services

| Scope item | Included (Schreiber AI turnkey) / Excluded (Customer) | Notes |
| --- | --- | --- |
| Site survey, utility letter, AHJ pre-application meeting, Site Requirements (H3) | Included | |
| Engineering Release package (H4) | Included | |
| Permit services: AHJ pre-submission support (included); permits pulled by Customer | Excluded (Customer) | Per `docs/SITE_REQUIREMENTS.md` Section 10 and Annex A |
| Pad / piers, anchors and embeds to PE drawing; H16 survey | Excluded | |
| Grounding electrode system, tested ≤ 5 Ω | Excluded | |
| Utility service, customer disconnect and feeder to the Unit | Excluded | |
| Fiber conduits (2 x 50 mm) and circuits | Excluded | Order at H3; 60–120 day lead |
| Water, drain, condensate, make-up water, fuel | Excluded | |
| Fence, lighting, screening | Excluded | |
| Crane, rigger and lift plan (W17) | Included (set-down) | Booked by Schreiber AI unless excluded |
| Freight, route survey, route permits, transit insurance to Austin, TX DAP | Included | |
| Hook-up by licensed trades; H18 pre-energisation | Included | |
| SAT (H19), acoustic survey (E10), 48-hour burn-in (E11) | Included | |
| Training T1 to T7 and Turnover Package (W20) | Included | |
| Spare parts kit per `docs/MAINTENANCE.md` Section 7 | Included | |
| Field evaluation (NFPA 790/791) by NRTL field evaluation body | Excluded (option) | Option; Risk R15 |
| TIA-942 Rated-level audit or other third-party certification | Included | Option; MSA 4.6 |
| Decommissioning / relocation services (Stage 22) | Excluded unless ordered later | Priced on request |

## 4. Exclusions

Unless marked Included in Section 3, the following are excluded from the price and are Customer's responsibility:

1. Customer IT equipment, operating systems, workloads, licences and data.
2. Civil works, pad, piers, grading, drainage, fencing and lighting.
3. Utility service application, connection fees, transformer, meter, customer disconnect and feeder.
4. Fiber / ISP circuits and recurring telecom charges.
5. Permits and fees assigned to Customer in Annex A (Site Requirements Section 10), and impact fees.
6. Fuel, electricity, water and consumables after SAT Acceptance.
7. Electricity for FAT and burn-in at the Factory is included; electricity at the Site from energisation is Customer's.
8. Taxes (MSA 9.5).
9. Changes required by an AHJ beyond the compliance pack (MSA 20.2), except where Section 3.7 includes field evaluation.
10. Site security, Customer insurance after risk of loss passes, and Customer's network firewall beyond the shipped controls-panel firewall.
11. Noise barrier walls beyond the option in Section 3.3, and neighbour relations.
12. Removal of existing structures, utilities or contamination at the Site.
13. Maintenance after SAT Acceptance unless Managed Services are ordered.

## 5. Schedule and milestones

5.1 **Baseline schedule.** Durations follow `docs/PROCESS_FLOW.md` Section 3 for the Tier (typical order-to-service: BEN Micro 10–12 weeks, BEN 10 about 20 weeks, BEN 20 about 27 weeks, BEN 40 32–36 weeks). Long-lead items drive the critical path: UPS 8–16 weeks, switchgear 10–20 weeks, in-row/CDU 8–24 weeks, transformer 10–16 weeks.

| Stage | Hold / Witness | Owner | Baseline date | Re-baselined date (latest Change Order) |
| --- | --- | --- | --- | --- |
| SOW signed; milestone 1 invoiced | — | Both | 2026-11-08 | |
| Site Requirements signed | H3 | Customer + Schreiber AI ENG | 2026-11-29 | [DATE_H3_CURRENT] |
| Engineering Release; Configuration frozen; milestone 2 invoiced | H4 | Schreiber AI ENG | 2026-12-20 | [DATE_H4_CURRENT] |
| Long-lead orders placed | — | Schreiber AI | 2027-05-09 | |
| Permits applied for (Customer-assigned permits) | — | Customer | 2026-12-27 | |
| Container receiving | W6 | Factory | 2027-01-10 | |
| Structural weld inspection | H7 | CWI + ENG | 2027-01-10 | |
| Envelope insulation / vapour barrier | W8 | Factory QC | 2027-01-17 | |
| Electrical rough-in / pre-energisation | H10a / H10b, W10 | Licensed electrician + QC | 2027-05-09 | |
| Cooling pressure test and evacuation | H11 | HVAC sub + QC | 2027-05-30 | |
| Controls I/O point-to-point | W12 | ENG | 2027-06-06 | |
| **FAT complete; milestone 3 invoiced** | **H13** | ENG + Customer | **2027-06-06** | [DATE_FAT_CURRENT] |
| Pad, anchors, grounding, utility ready | H16 | Customer site contractor + ENG | 2027-03-28 | [DATE_H16_CURRENT] |
| Shipment from Factory | — | Logistics | 2027-06-13 | [DATE_SHIP_CURRENT] |
| Set-down | W17 | Logistics + crane | 2027-06-20 | |
| Hook-up and pre-energisation; AHJ releases power | H18 | Licensed trades + AHJ | 2027-06-20 | |
| **SAT complete** | **H19** | ENG + Customer + fire marshal | **2027-06-27** | [DATE_SAT_CURRENT] |
| Training and Turnover; milestone 4 invoiced | W20 | ENG + Customer | 2027-07-04 | [DATE_TURNOVER_CURRENT] |

5.2 **Customer-dependent dates.** H3, Customer permits, H16, utility ready-to-connect letter (2027-03-28) and fiber ready (2027-03-28) are Customer-owned. A slip in any of them is a Customer-Caused Delay under MSA 7.5, moves every later date day for day plus re-sequencing time, suspends Schreiber AI's liquidated damages, and triggers the delay charges in Section 7.4 of this SOW.

5.3 **Working hours and access.** Site access for Schreiber AI and subcontractors: [SITE_ACCESS_HOURS]. Factory witness visits: by appointment with 5 Business Days' notice.

## 6. Hold points and witness points for this Unit

| Point | Stage | Who signs / may attend | Form | Customer attendance |
| --- | --- | --- | --- | --- |
| H3 | Site Requirements | Customer + Schreiber AI ENG + Compliance | `docs/SITE_REQUIREMENTS.md` Section 14 | Signs |
| H4 | Engineering Release | ENG lead, Compliance, Factory manager | Release note | Receives copy |
| W6 | Container receiving | Factory QC | Q-01 | May attend |
| H7 | Structural welds | CWI + ENG | Q-02 | Receives report |
| W8 | Insulation and vapour barrier before liner | Factory QC | Q-03 | May attend; photos filed |
| — | Floor channels, anchors | Factory QC | Q-04 | |
| — | Racks and containment | Factory QC | Q-05 | |
| H11 | Cooling pressure test / evacuation / charge | Factory QC + HVAC sub | Q-06 | Receives chart |
| H10a / H10b, W10 | Electrical rough-in; torque and megger; energisation | Licensed electrician + Factory QC; AHJ-of-record may witness | Q-07 | May attend W10 |
| W12 | Controls I/O point-to-point, calibration | ENG | Q-08 | May attend |
| — | Fire detection and suppression | Licensed fire contractor | Q-09 | |
| **H13** | **FAT** | ENG + Customer (or written waiver) | Q-10, Commissioning Report (factory mode), FAT Certificate | **Invited; 10 Business Days' notice; may send 3 people** |
| — | Transport preparation | Factory + Logistics | Q-11 | |
| H16 | Pad and utilities | Customer site contractor + ENG | Pad survey, ground test | Customer provides |
| W17 | Set-down, lift plan | Logistics + crane | Q-12 | May attend |
| H18 | Pre-energisation at Site | Licensed electrician + AHJ | Q-12 | May attend |
| **H19** | **SAT** | ENG + Customer + fire marshal | Commissioning Report (site mode), SAT Certificate | **Attends; 10 Business Days' notice** |
| W20 | Turnover meeting | ENG + Customer | `docs/TURNOVER.md`, Turnover Certificate | Attends |

Hold points H7, H10a, H10b, H11, H18 and the fire system commissioning may only be performed by the licensed or certified trade named; neither Party may waive them.

## 7. Price and payment

7.1 **Price.**

| Line | Amount (USD) | Basis |
| --- | --- | --- |
| Enclosure, structure, envelope, fire and life safety | 83,894.53 | Firm |
| Power module | 271,133.68 | Firm |
| Cooling module | 272,472.22 | Firm |
| Compute module | 1,072,379.14 | Firm (or Customer-supplied: 0) |
| Controls module (hardware and integration) | 22,902.65 | Firm |
| Engineering, FAT, transport, set-down, hook-up, SAT, training, turnover | 50,638.89 | Firm |
| **Unit price (basis for milestones and liquidated damages)** | **1,807,448.89** | |
| Software Licence (perpetual per-Unit fee, or first-year subscription) | 12,000.00 | Per Software Licence |
| Turnkey site works | 34,027.78 | Allowance; reconciled to actual with 10 % markup |
| Permit services | 0.00 | Time and materials at Section 7.5 rates; fees at cost |
| Options selected: none | 0.00 | Firm |
| Managed Services | USD 45 per kW-month x 50 kW = 2,250.00 per month | Per SLA, from SAT Acceptance |
| **Total contract value at signature** | **1,834,448.89** | Excludes taxes |

Price confidence: the bill of materials behind this price carries a confirmed / list / estimate split of 64 % confirmed / 0 % list / 36 % estimate as of 2026-11-08; items marked "estimate" are firm to Customer once this SOW is signed, and the risk of their variance is Schreiber AI's except under MSA 6.6 and 17.2.

7.2 **Milestones (MSA 9.1).**

| # | Trigger | Share | Amount | Baseline invoice date |
| --- | --- | --- | --- | --- |
| 1 | SOW signature | 30 % | 542,234.67 | 2026-11-08 |
| 2 | H4 Engineering Release | 40 % | 722,979.56 | 2026-12-20 |
| 3 | H13 FAT Acceptance (title passes; Unit ships on receipt) | 25 % | 451,862.22 | 2027-06-06 |
| 4 | H19 SAT Acceptance and Turnover, less LD credits and Punch List holdback | 5 % | 90,372.44 | 2027-07-04 |

Payment terms 30 days. Milestones delayed by Customer-Caused Delay are invoiced on the baseline date (MSA 9.3).

7.3 **Liquidated damages owed by Schreiber AI (MSA 7.7).** Rate 0.5 % of the Unit price per full week that FAT passes later than 2027-06-06 as re-baselined, after a grace period of 14 days; cap 10 % of the Unit price; sole remedy for delay; credited against milestone 4.

7.4 **Delay charges owed by Customer (MSA 7.8).**

| Charge | Rate | When |
| --- | --- | --- |
| Storage of FAT-passed Unit | 300 per day after 14 free days | Unit cannot ship on 2027-06-13 for a Customer-owned reason |
| Crane / rigger re-mobilisation | 4,500.00 plus rigger cancellation at cost | Lift cancelled or moved with < 5 Business Days' notice |
| Personnel standby | 1,200.00 per person per day | Crew kept waiting at Site |
| Re-commissioning | 7,500.00 per repeat plus load-bank rental at cost | SAT repeated for a Customer-side cause |
| Re-engineering for changed utility data | Section 7.5 rates | Utility data differs from Annex A |
| OEM storage / warranty-start / re-certification charges | At cost | As incurred |

7.5 **Rates for Change Orders and time-and-materials work.**

| Role | Rate (USD per hour) |
| --- | --- |
| Principal engineer / PE review | 225.00 |
| Controls / commissioning engineer | 175.00 |
| Field technician | 125.00 |
| Licensed electrician (subcontract) | 110.00 |
| Licensed HVAC technician EPA 608 (subcontract) | 125.00 |
| Certified welder (subcontract) | 135.00 |
| Project management | 165.00 |
| Travel and living | At cost plus 10 % |
| Materials on Change Orders | At cost plus 15 % |

## 8. Acceptance criteria

8.1 **FAT and SAT acceptance table.** The Commissioning Script (`software/ben_engine/commissioning.py`) runs these ten steps. FAT uses factory mode with load banks and shop power; SAT uses site mode on utility power with load banks or Customer IT at burn-in load. A step passes when every criterion in its row is met; otherwise it fails and MSA 8.5 and 8.6 apply. Sensor uncertainties are those in `spec/PROTOCOL.md` (k=2). Mapping to `docs/TEST_GUIDE.md` experiments is shown.

| Step | Name | What is done | Pass criteria | FAT | SAT | Experiment |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Pre-power visual checklist | Operator confirms each checklist item: unit level and tied down, CSC plate legible; grounding electrode conductor landed and tested; feeder terminated with torque marks, breaker open and locked; no shipping damage to cooling units, condensate drains connected; fire suppression and EPO hardwired and tagged, not on controls bus; racks anchored, blanking panels fitted, containment doors latch; controls LAN has no route to the internet; uplinks labelled both ends | Every item confirmed "yes" by the operator and the Customer witness; any "no" fails the step | Yes (factory equivalents for pad and feeder) | Yes | — |
| 2 | Pod discovery, attestation and firmware versions | The BEN Controller discovers all BEN Pods on the mesh | Pod count equals 12 (two per rack + room + outdoor; Micro 3); every Pod attested; every Pod reports the same signed firmware version [FIRMWARE_VERSION]; every Pod `status` heartbeat < 60 s old; logical node ids 4 | Yes | Yes | E12 (part) |
| 3 | Sensor sanity at idle | 20 % load for 5 minutes; read all inlet probes, RH, tare dP | All rack inlet probes within 2.0 K of each other; RH between 20 % and 80 %; dP tare acknowledged and residual ≤ 0.5 Pa | Yes | Yes | E1, E2 |
| 4 | I/O point-to-point | Each relay on each node set 1 then 0 and read back; door and leak contacts read 0, forced 1, released 0 | 100 % of points read back as set; 0 failed points | Yes | Yes | — |
| 5 | Power chain: meter vs PDU sum | 60 % load for 5 minutes; utility meter reconciled to PDU sum after subtracting metered cooling, house load and UPS losses | Disagreement ≤ 3.0 %; PUE recorded | Yes | Yes | E9 |
| 6 | Cooling unit sequential start and failover | Each cooling unit started in sequence; then one unit failed at 100 % load for 10 minutes and recovered | Every unit starts and reports running with kW > 0; during failover max rack inlet stays within ASHRAE Class A1 allowable (27 °C) and the standby unit picks up load; all failover criteria in `sweeps.cooling_unit_failover` pass | Yes | Yes | E4 |
| 7 | Load step to 100 % and thermal steady state | Load stepped 20 → 100 % in levels, each held 15 minutes | Max rack inlet within ASHRAE Class A1 allowable at every level; steady state reached at each level; rack ΔT within band at full load. Inlet above the 27 °C recommended envelope but within allowable is recorded as a note, not a failure | Yes (full) | Yes (reduced per `docs/TEST_GUIDE.md` E3) | E3, E8 |
| 8 | Utility loss ride-through | Utility removed at 100 % load; UPS carries IT; cooling behaviour per Configuration | UPS carries IT for ≥ 10 minutes; if cooling is on UPS or generator, inlets stay within allowable; if not, the measured minutes-to-ASHRAE-max is recorded and matches the Proposal within 20 %; generator (if fitted) starts and accepts load within 10 s; all criteria in `sweeps.utility_loss_ride_through` pass | Yes | Yes | E5 |
| 9 | Alarm verification | Alarms injected: rack inlet high (sensor drift), leak, door open, cooling unit fail, utility loss; each then cleared | Every injected alarm is raised within 30 s (10 s for utility loss) and clears when the cause is removed; no residual alarms after 5 minutes; recovery time after step 8 recorded | Yes | Yes | E6 (door), E7 (filter clog at FAT) |
| 10 | Export CSV and signed report | Telemetry buffer exported; report rendered with SHA-256 of CSV and signature block | CSV written; SHA-256 printed in the report matches `sha256sum` of the file; operator name recorded (not "unsigned"); report marked PASS overall | Yes | Yes | — |

8.2 **Additional SAT criteria (MSA 8.3).**

| Item | Pass criterion | Record |
| --- | --- | --- |
| Fire alarm and suppression acceptance | NFPA 72 Chapter 14 record of completion issued; door fan test shows ≥ 10-minute hold at design concentration; AHJ fire acceptance | Fire contractor report; AHJ certificate |
| Acoustic survey (E10) | Measured level at the property line ≤ ordinance limit in Annex A Section 9 ([NOISE_LIMIT_DAY] dBA day / [NOISE_LIMIT_NIGHT] dBA night) | Survey report |
| Burn-in (E11) | 48 hours at SAT (24 hours at FAT) with no critical alarm and no component replacement | Commissioning CSV |
| Cyber (E12) | Port scan finds only the services in `docs/CYBERSECURITY.md` Section 3; default credentials none; unsigned firmware image rejected and logged; 100 % of Pods attested and a rogue Pod rejected at join; edge computer loss leaves Pods buffering and the PLC holding interlocks; PLC loss drops the watchdog relay with cooling on | E12 report |
| Mesh resilience (E13) | Removing a router Pod: children re-attach within 60 s, telemetry ≥ 99.5 % complete after buffer catch-up | E13 report |
| Electrical | Ground electrode ≤ 25 Ω (target ≤ 5 Ω); bonding ≤ 0.1 Ω; insulation resistance ≥ 100 MΩ at 1 kV; phase rotation correct; emergency lights pass 90-minute test; final arc-flash labels installed with utility data | Q-07, Q-12 |
| Cooling | Superheat/subcool in range; no leak at 24 h sniff; glycol concentration and pH in range | Q-06 |
| Backup and restore | Edge computer database restored to a spare edge computer from the backup target | Turnover item G2 |

8.3 **Deemed acceptance.** 10 Business Days (10) per MSA 8.4.

8.4 **Punch List closure.** Performance items within 30 days; cosmetic items within 60 days; no safety item open at SAT Acceptance.

## 9. Site Requirements sign-off reference

The signed `docs/SITE_REQUIREMENTS.md` for this Unit is attached as **Annex A**, signed on [DATE_H3_ACTUAL] by [CUSTOMER_SITE_SIGNATORY] (Customer), [CUSTOMER_ELECTRICAL_CONTRACTOR] (Customer's electrical contractor), [SCHREIBER_ENG_SIGNATORY] (Schreiber AI engineering) and [SCHREIBER_COMPLIANCE_SIGNATORY] (Schreiber AI compliance). Values Customer provided there (utility fault current [UTILITY_FAULT_CURRENT_KA] kA, voltage, flood zone [FLOOD_ZONE], wind, snow, seismic, altitude, corrosivity, noise limits) are the design basis. A change to any of them after H4 is a Change Order.

## 10. Data, security and licence selections for this Unit

| Item | Selection |
| --- | --- |
| Remote support path at Turnover | [REMOTE_SUPPORT_STATE] (enabled with consent form / disabled, air-gap) |
| Telemetry sharing opt-in for anonymised fleet statistics | False (yes / no) |
| Backup target | [BACKUP_TARGET] |
| Alarm forwarding to Customer | [ALARM_FORWARDING] |
| Software Licence type | [LICENSE_TYPE] |
| Source escrow | False (yes / no); agent [ESCROW_AGENT] |
| Regulated-data addendum (BAA or similar) | none |
| White-label brand file | [BRAND_FILE_REF] (partner `brand.json` equivalent) |

## 11. Change Order log

| CO number | Date signed | Description | Price impact | Schedule impact (days) | New FAT date | New SAT date | New Turnover date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 001 | | | | | | | |
| | | | | | | | |
| | | | | | | | |

Running totals: price [CO_PRICE_TOTAL_DELTA]; schedule [CO_SCHEDULE_TOTAL_DELTA_DAYS] days.

## 12. Annexes

| Annex | Content |
| --- | --- |
| A | Signed Site Requirements (`docs/SITE_REQUIREMENTS.md`) |
| B | Proposal SAI-BEN20-20261108-4842D366 with risk register extract and signed risk acknowledgement |
| C | Frozen `config.json` (SAI-BEN20-20261108-4842D366-cfg-v1.0) and derived sizing printout |
| D | Issue-for-construction drawing index (issued at H4) |
| E | Managed Services SLA with Unit-specific values (if ordered) |
| F | Software Licence order form (licence type, fees, escrow election) |
| G | Remote support consent form |
| H | Regulated-data addendum (if any) |

## 13. Signatures

| | Schreiber AI | Customer |
| --- | --- | --- |
| Entity | Schreiber AI | Acme Clinic |
| Signature | ______________________ | ______________________ |
| Name | Ben Schreiber | [CUSTOMER_SIGNATORY_NAME] |
| Title | Founder | [CUSTOMER_SIGNATORY_TITLE] |
| Date | [SIGNATURE_DATE_SCHREIBER] | [SIGNATURE_DATE_CUSTOMER] |

---
Schreiber AI · BEN Engine (Business Edge Node) · Ben@SchreiberAI.com · Template maintained at `docs/contracts/SOW_TEMPLATE.md` · TEMPLATE — not legal advice — have counsel review before use.
