# Statement of Work (SOW) — BEN Engine Unit

> **TEMPLATE — not legal advice — have counsel review before use.**
> Schreiber AI · BEN Engine (Business Edge Node) · `docs/contracts/SOW_TEMPLATE.md` · Template rev [TEMPLATE_REV]
> Bracketed `[FIELDS]` are filled by the proposal generator from `docs/contracts/fields.json`. The configuration block in Section 2 is pasted verbatim from the frozen `config.json`. Delete this box before signature.

**SOW ID:** [SOW_ID]
**Under MSA:** [MSA_ID] dated [EFFECTIVE_DATE] between [SCHREIBER_ENTITY_NAME] ("Schreiber AI") and [CUSTOMER_NAME] ("Customer")
**Proposal:** [PROPOSAL_ID] dated [PROPOSAL_DATE]
**Unit serial (assigned at H4):** [UNIT_SERIAL]
**Site:** [SITE_NAME], [SITE_ADDRESS]
**SOW date:** [SOW_DATE]

This SOW orders one BEN Engine Unit and the Services for it under the MSA. Capitalised terms have the meanings in the MSA. If this SOW conflicts with the MSA, this SOW governs only where it names the MSA section it overrides (MSA Section 2.2).

## 1. Delivery model and modules

| Item | Selection |
| --- | --- |
| Tier | [TIER] (BEN Micro / BEN 10 / BEN 20 / BEN 40) |
| Delivery model | [DELIVERY_MODEL] (hardware only / hardware + BEN Controls / white-label / managed) |
| Modules ordered | [SUBSYSTEMS] (any of: power, cooling, compute, controls) |
| White-label | [WHITE_LABEL] (yes / no); brand to apply: [BRAND_NAME] |
| Managed Services | [MANAGED_SERVICES] (yes / no); if yes, SLA `docs/contracts/MANAGED_SERVICES_SLA.md` rev [DOC_REV_SLA] attached, term [SLA_TERM_MONTHS] months |
| Turnkey site works by Schreiber AI | [TURNKEY_SITE_WORKS] (yes / no / partial, list: [TURNKEY_SITE_WORKS_LIST]) |
| Factory | [FACTORY_NAME], [FACTORY_ADDRESS] (Schreiber AI facility or Contract Manufacturer under `docs/contracts/CONTRACT_MANUFACTURING_AGREEMENT.md`) |
| Schreiber AI project manager | [SCHREIBER_PM_NAME], [SCHREIBER_PM_EMAIL], [SCHREIBER_PM_PHONE] |
| Customer project manager | [CUSTOMER_PM_NAME], [CUSTOMER_PM_EMAIL], [CUSTOMER_PM_PHONE] |
| Customer site contact | [CUSTOMER_SITE_CONTACT_NAME], [CUSTOMER_SITE_CONTACT_PHONE] |

## 2. Configuration

2.1 **Frozen configuration.** The Configuration below is identified as [CONFIG_ID] and conforms to `spec/ben-config.schema.json`. It is frozen at Hold Point H4. Before H4 the values are the Proposal values and may be adjusted by agreement without a Change Order; after H4 every change is a Change Order.

```json
[CONFIG_JSON]
```

2.2 **Configuration summary (generated from the JSON by `software/ben_engine/config.py`).**

| Field | Value |
| --- | --- |
| `tier` | [TIER] |
| `profile` (mission profile) | [PROFILE] (ai_inference / ai_training / private_cloud / disaster_recovery / industrial_ot / healthcare / public_sector / off_grid) |
| `it_kw` (design IT load) | [IT_KW] kW |
| `racks` | [RACKS] |
| `cooling` | [COOLING] (cabinet_dx / inrow_dx / inrow_dx_300 / rdhx_drycooler / dlc_cdu) |
| `redundancy` | [REDUNDANCY] (N / N+1 / 2N) |
| `climate` | [CLIMATE] (temperate / hot_arid / hot_humid / cold / coastal / high_altitude) |
| `ups_minutes` | [UPS_MINUTES] min |
| `generator` | [GENERATOR] |
| ASHRAE class (from profile) | [ASHRAE_CLASS] |
| Service voltage / feeder breaker | [SERVICE_VOLTAGE] / [SERVICE_BREAKER_A] A |
| Total electrical demand | [TOTAL_KVA] kVA |
| UPS | [UPS_MODULES] x [UPS_KVA_EACH] kVA; battery [BATTERY_KWH] kWh (NFPA 855 package: [NFPA855_PACKAGE]) |
| Cooling units | [COOLING_UNITS_TOTAL] (including redundancy) |
| BEN Nodes | [NODE_COUNT] plus spares per `docs/MAINTENANCE.md` Section 7 |
| Estimated PUE (model, to be measured at SAT) | [PUE_ESTIMATE] |
| Gross shipped mass (to be weighed at Q-11) | [GROSS_MASS_KG] kg |
| Design wind speed / exposure / seismic category / snow load | [WIND_SPEED] / [EXPOSURE_CATEGORY] / [SEISMIC_CATEGORY] / [SNOW_LOAD] |
| Corrosivity class (ISO 9223) | [CORROSIVITY_CLASS] |

2.3 **Repository document revisions that apply to this Unit.**

| Document | Revision |
| --- | --- |
| `docs/PROCESS_FLOW.md` | [DOC_REV_PROCESS_FLOW] |
| `docs/SITE_REQUIREMENTS.md` (signed copy attached as Annex A) | [DOC_REV_SITE_REQUIREMENTS] |
| `docs/COMPLIANCE.md` compliance pack for profile [PROFILE] | [DOC_REV_COMPLIANCE] |
| `docs/TEST_GUIDE.md` | [DOC_REV_TEST_GUIDE] |
| `docs/TURNOVER.md` | [DOC_REV_TURNOVER] |
| `docs/MAINTENANCE.md` | [DOC_REV_MAINTENANCE] |
| `docs/RISK_REGISTER.md` (risk acknowledgement signed [RISK_ACK_DATE]) | [DOC_REV_RISK_REGISTER] |
| `docs/CYBERSECURITY.md` | [DOC_REV_CYBERSECURITY] |
| `design/assembly/QC_FORMS.md` (Q-01 to Q-12) | [DOC_REV_QC_FORMS] |
| `spec/PROTOCOL.md`, `spec/INTERFACES.md` | [DOC_REV_PROTOCOL] |
| Issue-for-construction drawing set `design/drawings/[TIER_DIR]/` | issued at H4, index [DRAWING_INDEX_REV] |

## 3. Scope by module

Mark each row **Included** or **Excluded**. Excluded rows are Customer's responsibility or are not part of this Unit.

### 3.1 Enclosure, structure and envelope (always included with any module)

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| One-trip high-cube ISO container ([TIER]) or NEMA 3R outdoor cabinet on skid (BEN Micro), received and inspected (Q-01, W6) | [SCOPE_ENCLOSURE] | |
| Structural modification by AWS D1.1 certified welder to IFC drawings; CWI inspection (H7, Q-02) | [SCOPE_STRUCTURAL] | Not applicable to BEN Micro |
| Envelope: 100 mm PIR/spray-foam insulation, vapour barrier, non-combustible liner, personnel doors with panic hardware, coating system to ISO 9223 class [CORROSIVITY_CLASS], seals, drains (W8, Q-03) | [SCOPE_ENVELOPE] | |
| Electrical vestibule 1.1 m (BEN 20/40); second egress door (BEN 40 at ≥ 1000 A) | [SCOPE_VESTIBULE] | |
| Floor channels, anchor clips, torque record (Q-04) | [SCOPE_FLOOR] | |
| Lighting, emergency lighting (90-minute self-contained), signage (arc-flash, NFPA 704, refrigerant, agent, entry procedure) | [SCOPE_LIGHTING_SIGNAGE] | |
| Door access control (badge reader, camera on controls LAN) | [SCOPE_ACCESS_CONTROL] | |
| PE-stamped anchorage and foundation drawing for the Site (climate wind speed [WIND_SPEED], seismic [SEISMIC_CATEGORY]) | [SCOPE_PE_ANCHORAGE] | Drawing only; civil works per Section 3.7 |
| Transport preparation (Q-11), CSC decision record, shock loggers, weigh ticket | [SCOPE_TRANSPORT_PREP] | |

### 3.2 Power module

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| Main panelboard/switchboard rated [SERVICE_BREAKER_A] A, SCCR 65 kA, SPD | [SCOPE_PWR_MAIN] | |
| UPS [UPS_MODULES] x [UPS_KVA_EACH] kVA, UL 1778, with lithium (LFP) battery [BATTERY_KWH] kWh, UL 1973 / UL 9540 | [SCOPE_PWR_UPS] | NFPA 855 package where ≥ 20 kWh: [NFPA855_PACKAGE] |
| Step-down transformers 480→208Y/120 V (BEN 20/40) | [SCOPE_PWR_TRANSFORMERS] | |
| Rack PDUs (A/B per rack, metered), whips, receptacles | [SCOPE_PWR_PDU] | |
| Power meters per power path; E9 reconciliation | [SCOPE_PWR_METERS] | |
| Grounding and bonding inside the Unit; two 2/0 AWG bonding lugs at diagonal corners | [SCOPE_PWR_BONDING] | Site electrode per Section 3.7 |
| Arc-flash and coordination study (IEEE 1584), provisional labels at FAT, final labels at SAT with utility data | [SCOPE_PWR_ARCFLASH] | Requires utility fault current from Customer (Risk R03) |
| Generator [GENERATOR_KW] kW with ATS (UL 1008), sub-base tank, NFPA 110 acceptance | [SCOPE_PWR_GENERATOR] | Only if `generator` = true |
| Cooling on UPS / mechanical ride-through path | [SCOPE_PWR_COOLING_ON_UPS] | Profile option (PROJECT_NOTES D7) |
| Electrical installation by licensed electrical contractor; H10a rough-in, H10b torque and megger (≥ 100 MΩ at 1 kV), bonding ≤ 0.1 Ω (Q-07) | [SCOPE_PWR_INSTALL] | |

### 3.3 Cooling module

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| Cooling type [COOLING]: [COOLING_UNITS_TOTAL] units, A1 refrigerant GWP < 700 (R-513A or R-515B) for DX tiers; no A2L inside the ITE space (PROJECT_NOTES D15) | [SCOPE_CLG_UNITS] | |
| Condensers / dry cooler / CDU and external piping to the equipment yard | [SCOPE_CLG_OUTDOOR] | |
| Hot-aisle containment, blanking panels, cable brush grommets | [SCOPE_CLG_CONTAINMENT] | |
| Glycol loop fill (propylene glycol [GLYCOL_PCT] %), drip trays, rope leak detection, condensate pump with float alarm | [SCOPE_CLG_FLUIDS] | RDHx / DLC only |
| Refrigerant detector, purge ventilation, HVAC shutdown relay from fire panel | [SCOPE_CLG_SAFETY] | |
| Installation by licensed HVAC contractor with EPA 608 technicians; H11 pressure test (1.1× design, 24 h) and evacuation (≤ 500 µm) (Q-06) | [SCOPE_CLG_INSTALL] | |
| Economizer / free cooling | [SCOPE_CLG_ECONOMIZER] | |
| Low-noise fans / acoustic barrier option | [SCOPE_CLG_ACOUSTIC] | Per noise prediction vs ordinance |

### 3.4 Compute module

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| Racks [RACKS] x 42U/48U, 1,360–1,590 kg rated, seismic kits, anchored (Q-05) | [SCOPE_CMP_RACKS] | Racks are included with Cooling or Power module even if Compute is excluded |
| Reference compute set: [COMPUTE_DESCRIPTION] | [SCOPE_CMP_SERVERS] | Customer-supplied if excluded; Schreiber AI provides rack space, circuits and cooling only (MSA 4.5) |
| Network: ToR switches, structured cabling, fiber patching to the communications entry plate | [SCOPE_CMP_NETWORK] | |
| IT burn-in load for SAT (load banks if Customer IT not available) | [SCOPE_CMP_LOADBANKS] | Load bank rental [LOADBANK_RENTAL_BASIS] |

### 3.5 Controls module (BEN Controls)

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| UL 508A controls panel: gateway (Raspberry Pi 5), managed PoE switch, 24 V DC supply, relays, firewall, remote-support key switch | [SCOPE_CTL_PANEL] | |
| BEN Nodes (ESP32-S3 on Olimex ESP32-POE-ISO) x [NODE_COUNT], sensors per `spec/PROTOCOL.md` (DS18B20 strings, SHT45, SDP810, rope leak, door reed, 4–20 mA inputs, pulse input) | [SCOPE_CTL_NODES] | |
| Signed firmware load, per-node certificates, `cal_id` applied, factory calibration with traceable references (Q-08, W12) | [SCOPE_CTL_FIRMWARE_CAL] | |
| Modbus/SNMP integration to UPS, cooling units, PDUs, meters, fire panel dry contacts (monitor only), door controller | [SCOPE_CTL_INTEGRATION] | |
| Dashboard (live data, 3-D twin, alarms, sweeps, CSV export, I/O test, calibration), digital twin fitted from commissioning data | [SCOPE_CTL_DASHBOARD] | |
| Software Licence per `docs/contracts/SOFTWARE_LICENSE_BEN_CONTROLS.md`: [LICENSE_TYPE] | [SCOPE_CTL_LICENSE] | perpetual per-Unit / subscription / white-label |
| Remote support path (outbound WireGuard) | [SCOPE_CTL_REMOTE] | enabled / disabled (air-gap) per consent form |
| Alarm forwarding to Customer systems (SNMP trap / syslog / webhook); read-only API | [SCOPE_CTL_FORWARDING] | |
| Backup target for gateway database (Customer SMB/NFS/S3 or second SSD) | [SCOPE_CTL_BACKUP] | |

### 3.6 Fire and life safety (always included with container tiers)

| Scope item | Included / Excluded | Notes |
| --- | --- | --- |
| VEWFD aspirating smoke detection plus spot detectors; UL 864 releasing panel; outdoor horn/strobe | [SCOPE_FS_DETECTION] | |
| Clean agent system (FK-5-1-12 class) with 10-minute hold, pre-discharge delay, abort station, door fan test (Q-09) | [SCOPE_FS_SUPPRESSION] | BEN 10/20/40; BEN Micro: aerosol unit, detection and extinguisher |
| EPO at exit door; HVAC shutdown on second-stage alarm | [SCOPE_FS_EPO] | Hardwired, never on the controls bus |
| Fire marshal plan review and permit by licensed fire protection contractor | [SCOPE_FS_PERMIT] | |
| Connection to central station / Customer monitoring | [SCOPE_FS_MONITORING] | Site-dependent |

### 3.7 Site works and services

| Scope item | Included (Schreiber AI turnkey) / Excluded (Customer) | Notes |
| --- | --- | --- |
| Site survey, utility letter, AHJ pre-application meeting, Site Requirements (H3) | Included | |
| Engineering Release package (H4) | Included | |
| Permit services: [PERMIT_SERVICES_LIST] | [SCOPE_SITE_PERMITS] | Per `docs/SITE_REQUIREMENTS.md` Section 10 and Annex A |
| Pad / piers, anchors and embeds to PE drawing; H16 survey | [SCOPE_SITE_CIVIL] | |
| Grounding electrode system, tested ≤ [GROUND_RESISTANCE_TARGET] Ω | [SCOPE_SITE_GROUNDING] | |
| Utility service, customer disconnect and feeder to the Unit | [SCOPE_SITE_UTILITY] | |
| Fiber conduits (2 x 50 mm) and circuits | [SCOPE_SITE_FIBER] | Order at H3; 60–120 day lead |
| Water, drain, condensate, make-up water, fuel | [SCOPE_SITE_WATER] | |
| Fence, lighting, screening | [SCOPE_SITE_FENCE] | |
| Crane, rigger and lift plan (W17) | [SCOPE_SITE_CRANE] | Booked by Schreiber AI unless excluded |
| Freight, route survey, route permits, transit insurance to [SITE_ADDRESS] DAP | Included | |
| Hook-up by licensed trades; H18 pre-energisation | Included | |
| SAT (H19), acoustic survey (E10), 48-hour burn-in (E11) | Included | |
| Training T1 to T7 and Turnover Package (W20) | Included | |
| Spare parts kit per `docs/MAINTENANCE.md` Section 7 | [SCOPE_SPARES] | |
| Field evaluation (NFPA 790/791) by NRTL field evaluation body | [SCOPE_FIELD_EVAL] | Option; Risk R15 |
| TIA-942 Rated-level audit or other third-party certification | [SCOPE_CERTIFICATION] | Option; MSA 4.6 |
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
| SOW signed; milestone 1 invoiced | — | Both | [DATE_ORDER] | |
| Site Requirements signed | H3 | Customer + Schreiber AI ENG | [DATE_H3_BASELINE] | [DATE_H3_CURRENT] |
| Engineering Release; Configuration frozen; milestone 2 invoiced | H4 | Schreiber AI ENG | [DATE_H4_BASELINE] | [DATE_H4_CURRENT] |
| Long-lead orders placed | — | Schreiber AI | [DATE_LONGLEAD_BASELINE] | |
| Permits applied for (Customer-assigned permits) | — | Customer | [DATE_PERMITS_APPLIED_BASELINE] | |
| Container receiving | W6 | Factory | [DATE_W6_BASELINE] | |
| Structural weld inspection | H7 | CWI + ENG | [DATE_H7_BASELINE] | |
| Envelope insulation / vapour barrier | W8 | Factory QC | [DATE_W8_BASELINE] | |
| Electrical rough-in / pre-energisation | H10a / H10b, W10 | Licensed electrician + QC | [DATE_H10_BASELINE] | |
| Cooling pressure test and evacuation | H11 | HVAC sub + QC | [DATE_H11_BASELINE] | |
| Controls I/O point-to-point | W12 | ENG | [DATE_W12_BASELINE] | |
| **FAT complete; milestone 3 invoiced** | **H13** | ENG + Customer | **[DATE_FAT_BASELINE]** | [DATE_FAT_CURRENT] |
| Pad, anchors, grounding, utility ready | H16 | Customer site contractor + ENG | [DATE_H16_BASELINE] | [DATE_H16_CURRENT] |
| Shipment from Factory | — | Logistics | [DATE_SHIP_BASELINE] | [DATE_SHIP_CURRENT] |
| Set-down | W17 | Logistics + crane | [DATE_SETDOWN_BASELINE] | |
| Hook-up and pre-energisation; AHJ releases power | H18 | Licensed trades + AHJ | [DATE_H18_BASELINE] | |
| **SAT complete** | **H19** | ENG + Customer + fire marshal | **[DATE_SAT_BASELINE]** | [DATE_SAT_CURRENT] |
| Training and Turnover; milestone 4 invoiced | W20 | ENG + Customer | [DATE_TURNOVER_BASELINE] | [DATE_TURNOVER_CURRENT] |

5.2 **Customer-dependent dates.** H3, Customer permits, H16, utility ready-to-connect letter ([DATE_UTILITY_READY_BASELINE]) and fiber ready ([DATE_FIBER_READY_BASELINE]) are Customer-owned. A slip in any of them is a Customer-Caused Delay under MSA 7.5, moves every later date day for day plus re-sequencing time, suspends Schreiber AI's liquidated damages, and triggers the delay charges in Section 7.4 of this SOW.

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
| **H13** | **FAT** | ENG + Customer (or written waiver) | Q-10, Commissioning Report (factory mode), FAT Certificate | **Invited; [FAT_NOTICE_DAYS] Business Days' notice; may send [WITNESS_ATTENDEES] people** |
| — | Transport preparation | Factory + Logistics | Q-11 | |
| H16 | Pad and utilities | Customer site contractor + ENG | Pad survey, ground test | Customer provides |
| W17 | Set-down, lift plan | Logistics + crane | Q-12 | May attend |
| H18 | Pre-energisation at Site | Licensed electrician + AHJ | Q-12 | May attend |
| **H19** | **SAT** | ENG + Customer + fire marshal | Commissioning Report (site mode), SAT Certificate | **Attends; [SAT_NOTICE_DAYS] Business Days' notice** |
| W20 | Turnover meeting | ENG + Customer | `docs/TURNOVER.md`, Turnover Certificate | Attends |

Hold points H7, H10a, H10b, H11, H18 and the fire system commissioning may only be performed by the licensed or certified trade named; neither Party may waive them.

## 7. Price and payment

7.1 **Price.**

| Line | Amount ([CURRENCY]) | Basis |
| --- | --- | --- |
| Enclosure, structure, envelope, fire and life safety | [PRICE_ENCLOSURE] | Firm |
| Power module | [PRICE_POWER] | Firm |
| Cooling module | [PRICE_COOLING] | Firm |
| Compute module | [PRICE_COMPUTE] | Firm (or Customer-supplied: 0) |
| Controls module (hardware and integration) | [PRICE_CONTROLS] | Firm |
| Engineering, FAT, transport, set-down, hook-up, SAT, training, turnover | [PRICE_SERVICES] | Firm |
| **Unit price (basis for milestones and liquidated damages)** | **[PRICE_TOTAL]** | |
| Software Licence (perpetual per-Unit fee, or first-year subscription) | [LICENSE_FEE] | Per Software Licence |
| Turnkey site works | [PRICE_SITE_WORKS] | Allowance; reconciled to actual with [SITE_WORKS_MARKUP_PCT] % markup |
| Permit services | [PRICE_PERMIT_SERVICES] | Time and materials at Section 7.5 rates; fees at cost |
| Options selected: [OPTIONS_LIST] | [PRICE_OPTIONS] | Firm |
| Managed Services | [SLA_RATE_PER_KW_MONTH] per kW-month x [IT_KW] kW = [SLA_MONTHLY_FEE] per month | Per SLA, from SAT Acceptance |
| **Total contract value at signature** | **[CONTRACT_VALUE_TOTAL]** | Excludes taxes |

Price confidence: the bill of materials behind this price carries a confirmed / list / estimate split of [BOM_CONFIDENCE_SPLIT] as of [BOM_DATE]; items marked "estimate" are firm to Customer once this SOW is signed, and the risk of their variance is Schreiber AI's except under MSA 6.6 and 17.2.

7.2 **Milestones (MSA 9.1).**

| # | Trigger | Share | Amount | Baseline invoice date |
| --- | --- | --- | --- | --- |
| 1 | SOW signature | [MILESTONE_1_PCT] % | [MILESTONE_1_AMOUNT] | [DATE_ORDER] |
| 2 | H4 Engineering Release | [MILESTONE_2_PCT] % | [MILESTONE_2_AMOUNT] | [DATE_H4_BASELINE] |
| 3 | H13 FAT Acceptance (title passes; Unit ships on receipt) | [MILESTONE_3_PCT] % | [MILESTONE_3_AMOUNT] | [DATE_FAT_BASELINE] |
| 4 | H19 SAT Acceptance and Turnover, less LD credits and Punch List holdback | [MILESTONE_4_PCT] % | [MILESTONE_4_AMOUNT] | [DATE_TURNOVER_BASELINE] |

Payment terms [PAYMENT_TERMS_DAYS] days. Milestones delayed by Customer-Caused Delay are invoiced on the baseline date (MSA 9.3).

7.3 **Liquidated damages owed by Schreiber AI (MSA 7.7).** Rate [CUSTOMER_LD_RATE_PCT_PER_WEEK] % of the Unit price per full week that FAT passes later than [DATE_FAT_BASELINE] as re-baselined, after a grace period of [LD_GRACE_DAYS] days; cap [CUSTOMER_LD_CAP_PCT] % of the Unit price; sole remedy for delay; credited against milestone 4.

7.4 **Delay charges owed by Customer (MSA 7.8).**

| Charge | Rate | When |
| --- | --- | --- |
| Storage of FAT-passed Unit | [STORAGE_FEE_PER_DAY] per day after [FREE_STORAGE_DAYS] free days | Unit cannot ship on [DATE_SHIP_BASELINE] for a Customer-owned reason |
| Crane / rigger re-mobilisation | [CRANE_REMOB_FEE] plus rigger cancellation at cost | Lift cancelled or moved with < [CRANE_NOTICE_DAYS] Business Days' notice |
| Personnel standby | [STANDBY_RATE_PER_DAY] per person per day | Crew kept waiting at Site |
| Re-commissioning | [RECOMMISSIONING_FEE] per repeat plus load-bank rental at cost | SAT repeated for a Customer-side cause |
| Re-engineering for changed utility data | Section 7.5 rates | Utility data differs from Annex A |
| OEM storage / warranty-start / re-certification charges | At cost | As incurred |

7.5 **Rates for Change Orders and time-and-materials work.**

| Role | Rate ([CURRENCY] per hour) |
| --- | --- |
| Principal engineer / PE review | [RATE_PRINCIPAL_ENGINEER] |
| Controls / commissioning engineer | [RATE_CONTROLS_ENGINEER] |
| Field technician | [RATE_FIELD_TECH] |
| Licensed electrician (subcontract) | [RATE_ELECTRICIAN] |
| Licensed HVAC technician EPA 608 (subcontract) | [RATE_HVAC] |
| Certified welder (subcontract) | [RATE_WELDER] |
| Project management | [RATE_PM] |
| Travel and living | At cost plus [TRAVEL_MARKUP_PCT] % |
| Materials on Change Orders | At cost plus [MATERIAL_MARKUP_PCT] % |

## 8. Acceptance criteria

8.1 **FAT and SAT acceptance table.** The Commissioning Script (`software/ben_engine/commissioning.py`) runs these ten steps. FAT uses factory mode with load banks and shop power; SAT uses site mode on utility power with load banks or Customer IT at burn-in load. A step passes when every criterion in its row is met; otherwise it fails and MSA 8.5 and 8.6 apply. Sensor uncertainties are those in `spec/PROTOCOL.md` (k=2). Mapping to `docs/TEST_GUIDE.md` experiments is shown.

| Step | Name | What is done | Pass criteria | FAT | SAT | Experiment |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Pre-power visual checklist | Operator confirms each checklist item: unit level and tied down, CSC plate legible; grounding electrode conductor landed and tested; feeder terminated with torque marks, breaker open and locked; no shipping damage to cooling units, condensate drains connected; fire suppression and EPO hardwired and tagged, not on controls bus; racks anchored, blanking panels fitted, containment doors latch; controls LAN has no route to the internet; uplinks labelled both ends | Every item confirmed "yes" by the operator and the Customer witness; any "no" fails the step | Yes (factory equivalents for pad and feeder) | Yes | — |
| 2 | Node discovery and firmware versions | Gateway discovers all BEN Nodes | Node count equals 1 + ceil(racks / 2) = [NODE_COUNT]; every node reports the same signed firmware version [FIRMWARE_VERSION]; every node `status` heartbeat < 60 s old | Yes | Yes | E12 (part) |
| 3 | Sensor sanity at idle | 20 % load for 5 minutes; read all inlet probes, RH, tare dP | All rack inlet probes within 2.0 K of each other; RH between 20 % and 80 %; dP tare acknowledged and residual ≤ 0.5 Pa | Yes | Yes | E1, E2 |
| 4 | I/O point-to-point | Each relay on each node set 1 then 0 and read back; door and leak contacts read 0, forced 1, released 0 | 100 % of points read back as set; 0 failed points | Yes | Yes | — |
| 5 | Power chain: meter vs PDU sum | 60 % load for 5 minutes; utility meter reconciled to PDU sum after subtracting metered cooling, house load and UPS losses | Disagreement ≤ 3.0 %; PUE recorded | Yes | Yes | E9 |
| 6 | Cooling unit sequential start and failover | Each cooling unit started in sequence; then one unit failed at 100 % load for 10 minutes and recovered | Every unit starts and reports running with kW > 0; during failover max rack inlet stays within ASHRAE Class [ASHRAE_CLASS] allowable ([ASHRAE_MAX_C] °C) and the standby unit picks up load; all failover criteria in `sweeps.cooling_unit_failover` pass | Yes | Yes | E4 |
| 7 | Load step to 100 % and thermal steady state | Load stepped 20 → 100 % in levels, each held 15 minutes | Max rack inlet within ASHRAE Class [ASHRAE_CLASS] allowable at every level; steady state reached at each level; rack ΔT within band at full load. Inlet above the 27 °C recommended envelope but within allowable is recorded as a note, not a failure | Yes (full) | Yes (reduced per `docs/TEST_GUIDE.md` E3) | E3, E8 |
| 8 | Utility loss ride-through | Utility removed at 100 % load; UPS carries IT; cooling behaviour per Configuration | UPS carries IT for ≥ [UPS_MINUTES] minutes; if cooling is on UPS or generator, inlets stay within allowable; if not, the measured minutes-to-ASHRAE-max is recorded and matches the Proposal within [RIDE_THROUGH_TOLERANCE_PCT] %; generator (if fitted) starts and accepts load within 10 s; all criteria in `sweeps.utility_loss_ride_through` pass | Yes | Yes | E5 |
| 9 | Alarm verification | Alarms injected: rack inlet high (sensor drift), leak, door open, cooling unit fail, utility loss; each then cleared | Every injected alarm is raised within 30 s (10 s for utility loss) and clears when the cause is removed; no residual alarms after 5 minutes; recovery time after step 8 recorded | Yes | Yes | E6 (door), E7 (filter clog at FAT) |
| 10 | Export CSV and signed report | Telemetry buffer exported; report rendered with SHA-256 of CSV and signature block | CSV written; SHA-256 printed in the report matches `sha256sum` of the file; operator name recorded (not "unsigned"); report marked PASS overall | Yes | Yes | — |

8.2 **Additional SAT criteria (MSA 8.3).**

| Item | Pass criterion | Record |
| --- | --- | --- |
| Fire alarm and suppression acceptance | NFPA 72 Chapter 14 record of completion issued; door fan test shows ≥ 10-minute hold at design concentration; AHJ fire acceptance | Fire contractor report; AHJ certificate |
| Acoustic survey (E10) | Measured level at the property line ≤ ordinance limit in Annex A Section 9 ([NOISE_LIMIT_DAY] dBA day / [NOISE_LIMIT_NIGHT] dBA night) | Survey report |
| Burn-in (E11) | 48 hours at SAT (24 hours at FAT) with no critical alarm and no component replacement | Commissioning CSV |
| Cyber (E12) | Port scan finds only the services in `docs/CYBERSECURITY.md` Section 3; default credentials none; unsigned firmware image rejected and logged; gateway loss leaves nodes buffering and failsafe outputs correct | E12 report |
| Electrical | Ground electrode ≤ 25 Ω (target ≤ 5 Ω); bonding ≤ 0.1 Ω; insulation resistance ≥ 100 MΩ at 1 kV; phase rotation correct; emergency lights pass 90-minute test; final arc-flash labels installed with utility data | Q-07, Q-12 |
| Cooling | Superheat/subcool in range; no leak at 24 h sniff; glycol concentration and pH in range | Q-06 |
| Backup and restore | Gateway database restored to a spare gateway from the backup target | Turnover item G2 |

8.3 **Deemed acceptance.** 10 Business Days ([DEEMED_ACCEPTANCE_DAYS]) per MSA 8.4.

8.4 **Punch List closure.** Performance items within [PUNCH_PERFORMANCE_DAYS] days; cosmetic items within [PUNCH_COSMETIC_DAYS] days; no safety item open at SAT Acceptance.

## 9. Site Requirements sign-off reference

The signed `docs/SITE_REQUIREMENTS.md` for this Unit is attached as **Annex A**, signed on [DATE_H3_ACTUAL] by [CUSTOMER_SITE_SIGNATORY] (Customer), [CUSTOMER_ELECTRICAL_CONTRACTOR] (Customer's electrical contractor), [SCHREIBER_ENG_SIGNATORY] (Schreiber AI engineering) and [SCHREIBER_COMPLIANCE_SIGNATORY] (Schreiber AI compliance). Values Customer provided there (utility fault current [UTILITY_FAULT_CURRENT_KA] kA, voltage, flood zone [FLOOD_ZONE], wind, snow, seismic, altitude, corrosivity, noise limits) are the design basis. A change to any of them after H4 is a Change Order.

## 10. Data, security and licence selections for this Unit

| Item | Selection |
| --- | --- |
| Remote support path at Turnover | [REMOTE_SUPPORT_STATE] (enabled with consent form / disabled, air-gap) |
| Telemetry sharing opt-in for anonymised fleet statistics | [TELEMETRY_OPT_IN] (yes / no) |
| Backup target | [BACKUP_TARGET] |
| Alarm forwarding to Customer | [ALARM_FORWARDING] |
| Software Licence type | [LICENSE_TYPE] |
| Source escrow | [ESCROW_SELECTED] (yes / no); agent [ESCROW_AGENT] |
| Regulated-data addendum (BAA or similar) | [REGULATED_DATA_ADDENDUM] |
| White-label brand file | [BRAND_FILE_REF] (partner `brand.json` equivalent) |

## 11. Change Order log

| CO number | Date signed | Description | Price impact | Schedule impact (days) | New FAT date | New SAT date | New Turnover date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [CO_NUMBER] | | | | | | | |
| | | | | | | | |
| | | | | | | | |

Running totals: price [CO_PRICE_TOTAL_DELTA]; schedule [CO_SCHEDULE_TOTAL_DELTA_DAYS] days.

## 12. Annexes

| Annex | Content |
| --- | --- |
| A | Signed Site Requirements (`docs/SITE_REQUIREMENTS.md`) |
| B | Proposal [PROPOSAL_ID] with risk register extract and signed risk acknowledgement |
| C | Frozen `config.json` ([CONFIG_ID]) and derived sizing printout |
| D | Issue-for-construction drawing index (issued at H4) |
| E | Managed Services SLA with Unit-specific values (if ordered) |
| F | Software Licence order form (licence type, fees, escrow election) |
| G | Remote support consent form |
| H | Regulated-data addendum (if any) |

## 13. Signatures

| | Schreiber AI | Customer |
| --- | --- | --- |
| Entity | [SCHREIBER_ENTITY_NAME] | [CUSTOMER_NAME] |
| Signature | ______________________ | ______________________ |
| Name | [SCHREIBER_SIGNATORY_NAME] | [CUSTOMER_SIGNATORY_NAME] |
| Title | [SCHREIBER_SIGNATORY_TITLE] | [CUSTOMER_SIGNATORY_TITLE] |
| Date | [SIGNATURE_DATE_SCHREIBER] | [SIGNATURE_DATE_CUSTOMER] |

---
Schreiber AI · BEN Engine (Business Edge Node) · Ben@SchreiberAI.com · Template maintained at `docs/contracts/SOW_TEMPLATE.md` · TEMPLATE — not legal advice — have counsel review before use.
