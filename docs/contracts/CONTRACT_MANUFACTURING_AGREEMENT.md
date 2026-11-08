# Contract Manufacturing Agreement — BEN Engine Build Shop

> **TEMPLATE — not legal advice — have counsel review before use.**
> Schreiber AI · BEN Engine (Business Edge Node) · `docs/contracts/CONTRACT_MANUFACTURING_AGREEMENT.md` · Template rev [TEMPLATE_REV]
> Bracketed `[FIELDS]` are filled by the proposal generator from `docs/contracts/fields.json`. Used with the third-party container modification shop, electrical integrator or UL 508A panel shop that builds Units for Schreiber AI (the operator's decision to manufacture with third parties first). Delete this box before signature.

**Agreement ID:** [CM_AGREEMENT_ID]
**Effective Date:** [EFFECTIVE_DATE]

This Contract Manufacturing Agreement ("**Agreement**") is between **[SCHREIBER_ENTITY_NAME]**, a [SCHREIBER_ENTITY_TYPE] at [SCHREIBER_ADDRESS] ("**Schreiber AI**"), and **[CM_NAME]**, a [CM_ENTITY_TYPE] at [CM_ADDRESS], with its build facility at [CM_FACILITY_ADDRESS] (the "**Facility**") ("**Manufacturer**").

## 1. Definitions

1.1 "**Build Order**" means Schreiber AI's purchase order to Manufacturer for one Unit or a batch of Units, referencing this Agreement, the Configuration ID, the IFC drawing index, the STE assembly instruction issue, the BOM revision, the delivery date and the price.

1.2 "**Build Package**" means, for a Unit: the frozen `config.json` ([CONFIG_ID]); the issue-for-construction drawing set with CTQ/CTP tables (`design/drawings/<tier>/`, index [DRAWING_INDEX_REV]); the STE assembly instructions (`design/assembly/ASSEMBLY-<tier>.md`, issue [ASSEMBLY_ISSUE]) and `STE_STYLE.md`; the QC forms (`design/assembly/QC_FORMS.md` Q-01 to Q-12); the BOM for the Unit (`purchasing/bom-<tier>.csv` revision [BOM_REV]) with the consigned/purchased split; the wire sizing and torque tables (`docs/BUILD_AND_WIRING.md`); the compliance pack extract; the PE structural calculation; the FAT procedure (`docs/TEST_GUIDE.md`, factory-mode steps).

1.3 "**Consigned Materials**" means materials Schreiber AI supplies to Manufacturer at no charge for incorporation into Units, listed in Annex B.

1.4 "**Controls Kit**" means the Consigned **BEN Controller** (BEN Controls Pro: the UL 508A listed panel with the Phoenix Contact PLCnext AXC F 2152 controller, Axioline F I/O, QUINT4 24 VDC supplies, SPD, FL SWITCH 2008 and the OnLogic Karbon 400 edge computer, imaged and TPM-enrolled, or the panel built by Manufacturer if Manufacturer is the listed panel shop under Section 8.3; BEN Controls Lite: the DIN-rail cabinet with the Revolution Pi RevPi Connect 4, DIO/AIO, supply and switch), the **BEN Pods** (provisioned with their device certificates at Schreiber AI's provisioning cell, calibrated, with probe strings and enclosures), the border router radios, the industrial transmitters (Pt1000, Setra 264, Vaisala HMW90, RLE LD2100 and leak cable), the RS-485 / 24 VDC cabling kit, signed firmware and the PLC project on media, calibration references and the Pod certificate register.

1.5 "**Purchased Materials**" means materials Manufacturer buys for Units under Section 4.

1.6 "**Nonconformance**" means any departure of a Unit, part or process from the Build Package, including a CTQ or CTP outside tolerance, a skipped or unsigned hold point, or an incomplete QC form.

1.7 "**Tooling**" means jigs, fixtures, templates, lifting frames, test harnesses and load-bank adapters made or bought for BEN Engine production, listed in Annex C.

1.8 "**Licensed Trades**" means the certified or licensed persons required by `docs/PROCESS_FLOW.md` and the STE instructions: AWS D1.1 (or ISO 9606-1) certified welders and a Certified Welding Inspector; licensed electrical contractor; licensed HVAC/refrigeration contractor with EPA Section 608 Type II or Universal technicians; state-licensed fire protection contractor; UL 508A listed panel shop.

1.9 Other capitalised terms (Unit, Tier, Configuration, Hold Point, Witness Point, FAT, Commissioning Script, Commissioning Report) have the meanings in `docs/contracts/MSA.md`.

## 2. Scope

2.1 **What Manufacturer does.** For each Build Order Manufacturer will build the Unit at the Facility strictly to the Build Package, performing Process Stages 6 to 14 of `docs/PROCESS_FLOW.md` as allocated below, and deliver it FAT-passed and transport-prepared.

| Stage | Work | Allocation |
| --- | --- | --- |
| 6 | Container (or cabinet) receiving and inspection, Q-01, W6 | Manufacturer |
| 7 | Structural modification by certified welder; CWI inspection (visual 100 %, MT 10 %); H7; Q-02 | Manufacturer with Licensed Trade |
| 8 | Envelope: insulation, vapour barrier, liner, doors, coatings, seals, drains; W8; blower-door test; Q-03 | Manufacturer |
| 9 | Mechanical fit-out: floor channels, racks, containment, trays, lighting, leak detection rope; Q-04, Q-05 | Manufacturer |
| 10 | Electrical installation by licensed electrical contractor; H10a, H10b; W10; Q-07 | Manufacturer with Licensed Trade |
| 11 | Cooling installation by licensed HVAC contractor; H11 pressure test and evacuation; charge; glycol fill; Q-06 | Manufacturer with Licensed Trade |
| 12 | Controls Kit installation, node addressing, sensor placement, cable labelling; firmware already loaded and signed by Schreiber AI; I/O point-to-point W12; Q-08 | Manufacturer installs; Schreiber AI commissions firmware and calibration |
| — | Fire detection and suppression by licensed fire contractor; door fan test; Q-09 | Manufacturer with Licensed Trade (or Schreiber AI's contractor, per Build Order) |
| 13 | FAT with the Commissioning Script in factory mode; 24-hour burn-in; H13; Q-10 | Manufacturer provides Unit, shop power, load banks and labour; Schreiber AI commissioning lead runs the script and signs |
| 14 | Transport preparation, weigh ticket, shock loggers, CSC decision record; Q-11 | Manufacturer |

2.2 **What Schreiber AI does.** Supplies the Build Package and Consigned Materials; answers technical queries within 2 Business Days; attends hold and witness points; performs firmware commissioning, calibration and FAT; arranges transport from the Facility; manages the End Customer.

2.3 **Tiers and capacity.** This Agreement covers Tiers [CM_TIERS]. Manufacturer reserves capacity for [CM_CAPACITY_UNITS_PER_QUARTER] Units per quarter on [CM_FORECAST_NOTICE_WEEKS] weeks' rolling forecast; forecasts are non-binding except for the first [CM_FIRM_WINDOW_WEEKS] weeks, which Schreiber AI will cover by Build Orders.

2.4 **No design authority.** Manufacturer builds to the Build Package. Manufacturer will not change a dimension, material, component, wiring method, refrigerant, fastener, coating or sequence without a written disposition from Schreiber AI engineering under Section 7 or a change under Section 12. Where the Build Package is ambiguous or appears wrong, Manufacturer stops the affected work and raises a technical query.

## 3. First article and qualification

3.1 **Qualification audit.** Before the first Build Order Schreiber AI audits the Facility: welding procedure specifications and welder qualifications; electrical contractor licence; HVAC licence and EPA 608 certificates; fire contractor licence; UL 508A listing if applicable; calibration of torque wrenches, megger, micrometer, manometer, scales and refrigerant scales; lifting equipment certifications; shop power capacity for FAT ([SHOP_POWER_KVA] kVA at [SHOP_VOLTAGE]); load banks; insurance; and the quality system (ISO 9001 or equivalent, [CM_QUALITY_SYSTEM]).

3.2 **First article.** The first Unit of each Tier is a First Article. Schreiber AI attends every hold and witness point of the First Article in person. First Article inspection covers every CTQ and CTP in the drawing tables with measured values recorded, a full dimensional report against the drawings, and a complete Q-01 to Q-11 set. First Article approval is a condition for further Build Orders of that Tier.

3.3 **PPAP-lite documentation.** With the First Article Manufacturer delivers: process flow diagram for the Facility; control plan mapping each CTQ/CTP to the inspection method, frequency, gauge and reaction; gauge list with calibration certificates; welder, electrician, HVAC and fire contractor certifications; welding procedure specifications and procedure qualification records; coating system data sheets and DFT records; material certifications for structural steel and insulation; the dimensional report; and a sample of every QC form filled in. This set is updated when a process, supplier or trade changes.

## 4. Materials: consigned and purchased

4.1 **Consigned Materials (Annex B).** Schreiber AI supplies at no charge, delivered DAP Facility: the Controls Kit; BEN Node spares for the Unit's kit; signed firmware media; calibration references; Schreiber AI-specific labels, placards and the Turnover document pocket; and any long-lead OEM equipment Schreiber AI chooses to buy directly (UPS, battery cabinets, in-row units, CDU, dry cooler, switchgear, generator, as the Build Order states). Title to Consigned Materials stays with Schreiber AI at all times. Manufacturer holds them as bailee, stores them indoors, segregated and labelled "Property of Schreiber AI", insures them under Section 13, uses them only for Build Orders, and returns unused items on request.

4.2 **Purchased Materials.** Manufacturer buys the remaining BOM lines (container or cabinet, structural steel, insulation, liner, doors, coatings, racks, containment kits, trays, lighting, wire and raceway, panelboards and breakers unless consigned, PDUs, transformers, cooling units unless consigned, piping, refrigerant, glycol, fire system components unless by Schreiber AI's contractor) **from the manufacturers and part numbers in the BOM or the approved alternates column**, under `docs/contracts/SUPPLIER_TERMS.md` or terms at least as protective, with certificates of conformance and UL listings as that document's Appendix requires. Substitution without written approval is a Nonconformance.

4.3 **Receiving.** All materials are receiving-inspected (Q-01 for the enclosure; receiving log for others) against the packing list, the BOM part number, the listing mark and visible damage. Serial numbers of UPS, batteries, cooling units, CDU, PDUs, fire panel, BEN Controller panel, PLC, edge computer and every BEN Pod (serial, EUI-64, certificate fingerprint) are recorded in the as-built BOM.

4.4 **Pass-through of OEM warranties.** Manufacturer assigns to Schreiber AI (for onward assignment to the End Customer) all OEM warranties on Purchased Materials and provides the registration data at FAT.

4.5 **Title to Purchased Materials and work in progress.** Title passes to Schreiber AI progressively as Schreiber AI pays milestone invoices under Section 11, and in any event on FAT Acceptance. Manufacturer keeps Units and materials free of liens and provides lien waivers with each invoice.

4.6 **Surplus and scrap.** Surplus Purchased Materials bought for a Build Order are offered to Schreiber AI at cost; scrap is Manufacturer's unless it contains Schreiber AI Confidential Information (drawings, labels, nodes), which is destroyed and certified.

## 5. Quality plan

5.1 **Governing documents.** `docs/PROCESS_FLOW.md` (stages, owners, hold points, witness points, records); the STE assembly instructions (task order, personnel, tools, warnings, steps, checks); the drawings' CTQ/CTP tables; `design/assembly/QC_FORMS.md`.

5.2 **Hold points.** Work stops at each hold point until the named person signs the form. Manufacturer will not: close the liner before W8 photos are filed; energise before H10b; charge a refrigerant circuit before H11; connect life-safety wiring to anything but dry-contact monitoring (CTP-K1); ship before H13 and the CSC decision record (CTP-A2).

| Hold point | Signatory | Form | Schreiber AI attendance |
| --- | --- | --- | --- |
| H7 weld inspection | CWI; Schreiber AI ENG countersigns | Q-02 | First Article in person; thereafter report review within 2 Business Days, attendance at Schreiber AI's option |
| H10a rough-in | Licensed electrician + Manufacturer QC | Q-07 | At option |
| H10b torque and megger before energisation | Licensed electrician + Manufacturer QC | Q-07 | First Article in person; thereafter at option (video acceptable) |
| H11 pressure test and evacuation | Licensed HVAC + Manufacturer QC | Q-06 | First Article in person; thereafter 24-hour chart and evacuation log reviewed before charge |
| Fire system commissioning | Licensed fire contractor | Q-09 | Report review |
| H13 FAT | Schreiber AI commissioning lead + End Customer witness | Q-10, Commissioning Report, FAT Certificate | **Always in person** |

5.3 **Witness points.** Manufacturer gives Schreiber AI 5 Business Days' notice of W6, W8, W10, W12 and of the FAT start date, and of any CTQ measurement Schreiber AI lists as "witness" in the control plan. End Customers may attend W6, W8, W10, W12 and H13 under the MSA; Manufacturer will accommodate up to [WITNESS_ATTENDEES] visitors with PPE and a safety briefing.

5.4 **QC forms.** Every Q-form is completed in full, legibly, with measured values (not ticks alone where a value is specified), signatory name, certification number where applicable, date and photographs where the form asks, and uploaded to the Schreiber AI portal within 2 Business Days of completion. The forms become part of the Turnover Package (items A5, A6, B3, B4, B5, B9, B10).

5.5 **Critical-to-quality measurements.** The following are measured and recorded on every Unit, and are not sampled:

| CTQ / CTP | Requirement (from drawings) | Form |
| --- | --- | --- |
| CTQ-S1 squareness and flatness after welding | Within drawing tolerance; corner-casting diagonals | Q-02 |
| CTP-A1 frame welds | Fully welded, undercut ≤ 0.5 mm, primed within 4 h | Q-02 |
| CTQ-E2 envelope leakage | Blower-door result ≤ target; smoke pencil at 10 joints | Q-03 |
| Coating DFT | Per coating system for ISO 9223 class; readings per face | Q-03 |
| CTP-S1 / CTP-S2 anchor and hold-down torque | 85 N·m ±10 %, paint-striped, every bolt | Q-04, Q-05 |
| Rack positions | ±5 mm to drawing; aisle width ≥ drawing | Q-05 |
| CTP-M1 brazing and evacuation | Nitrogen purge; ≤ 500 micron held 30 min (24 h hold per PROCESS_FLOW for the circuit); charge per nameplate by weight | Q-06 |
| CTQ-M1 pressure test | Refrigerant 1.1× design 24 h drop ≤ 1 %; water 1.5× working 2 h no drop | Q-06 |
| CTP-E1 energisation gate | No energisation before sign-off | Q-07 |
| CTP-E2 termination torque | Every lug to device label value, recorded | Q-07 |
| Insulation resistance | ≥ 100 MΩ at 1 kV | Q-07 |
| CTQ-E2 bonding | Every bond ≤ 0.1 Ω | Q-07 |
| CTQ-E1 working space | NEC 110.26 clearances; vestibule 1.1 m (BEN 150/40) | Q-07 |
| CTQ-K3 sensor placement and calibration check | Within ±0.25 °C after correction; `cal_id` stored | Q-08 |
| CTP-K1 life-safety isolation | Dry contacts only to node; releasing circuit independent | Q-09 |
| CTP-F1 hold time | ≥ 10 min at design concentration; certificate | Q-09 |
| CTQ-E3 EPO | All IT power off < 1 s | Q-10 |
| CTQ-A3 gross mass | Drawing value + 10 % max; weigh ticket | Q-11 |
| CTP-A2 CSC | New CSC plate or ACEP record, or "cargo, plate covered" decision record, before transport | Q-11 |

5.6 **Shop calibration.** Torque wrenches, insulation testers, low-resistance ohmmeters, manometers, vacuum gauges, refrigerant scales, DFT gauges, tape measures over 5 m and the weigh scale are calibrated to traceable standards at intervals not exceeding 12 months, with certificates available at audit.

5.7 **Audit rights.** Schreiber AI and, with notice, its End Customer or the AHJ-of-record may audit the Facility, records, subcontractors and in-progress Units on 3 Business Days' notice during working hours, and without notice where a safety or integrity concern exists. Manufacturer gives Schreiber AI read access to its production schedule for BEN Engine Units.

5.8 **Traceability.** Each Unit carries its serial [UNIT_SERIAL] on the frame, the controls panel and every QC form; each form references the drawing revision and STE issue used.

## 6. Factory acceptance test

6.1 **Readiness.** Manufacturer declares FAT readiness when Q-01 to Q-09 are closed with no open Nonconformance, the Unit is energised from shop power at the Configuration voltage, load banks totalling [IT_KW] kW are connected in the racks, condensers or dry cooler are operating, and the Controls Kit reports every node online. Readiness is declared at least 5 Business Days before the FAT date to allow End Customer notice under the MSA.

6.2 **Execution.** Schreiber AI's commissioning lead runs `commissioning.py --mode factory` through the ten steps (pre-power checklist; node discovery and firmware; sensor sanity at idle; I/O point-to-point; power chain meter vs PDU sum within 3 %; cooling sequential start and failover; load step 20 → 100 % within the ASHRAE class; utility loss ride-through; alarm verification; CSV export with SHA-256 and signed report), plus E7 filter clog, E11 24-hour burn-in and E12 cyber scan, the door fan test and the fire contractor's acceptance. Manufacturer provides labour, shop power, load banks, thermography camera access, a manometer and a safe test area for the duration, including the 24-hour burn-in.

6.3 **Result.** A step FAIL for a Manufacturer cause is a Nonconformance under Section 7; Manufacturer corrects it and the step is re-run at Manufacturer's cost (including Schreiber AI's re-attendance at [COMMISSIONING_DAY_RATE] per day plus travel if the re-run cannot be done during the same visit). A FAIL for a Schreiber AI cause (firmware, calibration references, Consigned Material defect, drawing error) is Schreiber AI's cost. A FAIL for an OEM component defect is handled under the OEM warranty, with Manufacturer performing the swap at Schreiber AI's cost unless Manufacturer's handling caused it.

6.4 **FAT Acceptance.** FAT is accepted when the FAT Certificate (`docs/contracts/ACCEPTANCE_CERTIFICATES.md` Part A) is signed by Schreiber AI and Manufacturer's QC, with the End Customer's signature or waiver. The Commissioning Report and CSV hashes are recorded on the certificate. FAT Acceptance is the Build Order delivery event for Section 10.

6.5 **Shop power and load banks.** Manufacturer's shop supply must deliver the Configuration's service voltage and at least [TOTAL_KVA] kVA; load banks of [IT_KW] kW with rack-mount form factor and PDU plug compatibility are [LOADBANK_PROVIDER]'s (Manufacturer / Schreiber AI / rented at Schreiber AI's cost).

## 7. Nonconformance and rework

7.1 **Reporting.** Manufacturer records every Nonconformance on a nonconformance report (NCR) with Unit serial, drawing and STE reference, description, photographs, measured values and containment action, within 1 Business Day of discovery, and stops work on the affected system.

7.2 **Disposition.** Schreiber AI engineering dispositions each NCR within 2 Business Days as: use-as-is (with technical justification recorded, and End Customer consent where the deviation is visible in the acceptance criteria); rework to drawing; repair to an approved repair procedure; or reject and replace. Manufacturer may not self-disposition a Nonconformance on a CTQ, CTP or hold-point item.

7.3 **Cost.** Rework, repair and replacement for Manufacturer-caused Nonconformance (including subcontracted Licensed Trades) is at Manufacturer's cost, including materials, labour, re-test, re-inspection and Schreiber AI re-attendance. Nonconformance caused by a Build Package error or a Consigned Material defect is at Schreiber AI's cost through a change under Section 12.

7.4 **Repeat Nonconformance.** The same Nonconformance on two Units triggers a root-cause analysis (8D or equivalent) within 10 Business Days and a control plan update. Three Units trigger a Schreiber AI audit at Manufacturer's cost.

7.5 **Escapes.** A Nonconformance discovered after FAT (at set-down, SAT or in the warranty period) that is traceable to Manufacturer's work is corrected by Manufacturer at the Site at its cost, or by Schreiber AI with back-charge at the rates in Annex D, within the response times in `docs/contracts/WARRANTY_TERMS.md` Section 6.3.

## 8. Safety, licensed trades and listings

8.1 **Licensed Trades.** Manufacturer will employ or subcontract Licensed Trades for all work `docs/PROCESS_FLOW.md` and the STE instructions reserve to them, and will keep on file and upload to the portal: welder qualification records (AWS D1.1 or ISO 9606-1) and WPS/PQR; CWI certificate; electrical contractor licence [CM_ELECTRICAL_LICENSE] and the responsible master electrician; HVAC contractor licence [CM_HVAC_LICENSE] and EPA Section 608 certificates (Type II or Universal) of every technician who handles refrigerant; fire protection contractor licence [CM_FIRE_LICENSE] (or Schreiber AI's contractor); forklift and crane operator certifications; confined-space and LOTO training records. No person without the stated certification performs the stated work, even under supervision.

8.2 **Safety.** Manufacturer complies with OSHA and applicable state rules at the Facility; provides PPE per the STE instructions (T-15); maintains LOTO for energised work; manages refrigerant and glycol per SDS; stores lithium batteries per the OEM and NFPA 855 storage guidance, charged to the OEM's storage SOC, with fire separation; and reports any recordable injury or near-miss on a BEN Engine Unit to Schreiber AI within 24 hours.

8.3 **UL 508A controls panel.** The BEN controls panel must be built and labelled by a UL 508A listed panel shop with SCCR marking per Supplement SB. If Manufacturer is a listed shop ([CM_UL508A_FILE_NUMBER]), it builds the panel to Schreiber AI's panel drawings as Purchased work; otherwise Schreiber AI consigns the panel. Manufacturer may not open or modify a listed panel's internal wiring beyond landing the field terminals shown on the drawings.

8.4 **Listed equipment.** Manufacturer installs listed equipment per its listing and instructions (NEC 110.3(B)) and does not field-modify listed equipment beyond listed accessories. Any field evaluation required by an AHJ because of a Manufacturer modification is at Manufacturer's cost.

8.5 **Refrigerant.** Only the A1 refrigerant specified in the Build Package (R-513A or R-515B, GWP < 700) is charged; charge by weight per circuit is recorded with the technician's EPA 608 number on the refrigerant service record. Recovery on rework follows 40 CFR 82 Subpart F.

8.6 **Environmental.** Manufacturer handles coatings, solvents, refrigerant, glycol, batteries and waste per law and provides SDS for the Turnover binder (item D6).

## 9. Schedule, delivery and liquidated damages

9.1 **Delivery date.** Each Build Order states the FAT-ready date and the FAT Acceptance date (the "**Delivery Date**"), set from `docs/PROCESS_FLOW.md` Section 3 durations for the Tier (Stages 6 to 13 typically 10 to 13 weeks for a BEN 150 once the container and long-lead items are at the Facility). Manufacturer confirms the Delivery Date within 5 Business Days of the Build Order or proposes an alternative with reasons; silence is acceptance.

9.2 **Progress reporting.** Weekly written progress report per Unit: stage, QC forms closed, open NCRs, material shortages, forecast FAT-ready date, photographs. Manufacturer gives notice within 2 Business Days of any event that threatens the Delivery Date.

9.3 **Schreiber AI-caused and excusable delay.** The Delivery Date moves day for day for: late Consigned Materials (beyond the date in Annex B); late Build Package or technical query answers (beyond 2 Business Days); Schreiber AI changes under Section 12; Schreiber AI's unavailability for a hold point or FAT after proper notice; and Force Majeure under Section 15, including supplier allocation of a Purchased Material where Manufacturer ordered within [PO_PLACEMENT_DAYS] Business Days of the Build Order, gave notice within 2 Business Days of learning of the allocation, and pursued the approved alternate.

9.4 **Liquidated damages (Manufacturer to Schreiber AI).** If FAT Acceptance is later than the Delivery Date plus [CM_LD_GRACE_DAYS] calendar days for a cause not excused under Section 9.3, Manufacturer pays Schreiber AI liquidated damages of **[CM_LD_RATE_PCT_PER_WEEK] % of the Build Order price per full week** (standard 0.5 %), up to **[CM_LD_CAP_PCT] % of the Build Order price** (standard 10 %), as a reasonable pre-estimate of Schreiber AI's loss including its own liquidated damages exposure to the End Customer under `docs/contracts/MSA.md` Section 7.7. Liquidated damages may be set off against any invoice.

9.5 **Expediting at Manufacturer's cost.** Where Manufacturer's cause threatens the Delivery Date, Manufacturer will at its cost add shifts, expedite Purchased Materials and freight, and pay Schreiber AI's documented expediting costs (premium freight on Consigned Materials re-routed, Schreiber AI staff overtime and travel changes).

9.6 **Right to cover.** If the delay exceeds [CM_COVER_TRIGGER_WEEKS] weeks beyond the Delivery Date for Manufacturer's cause, or Manufacturer notifies that it cannot meet a Delivery Date by more than that, Schreiber AI may, in addition to liquidated damages up to the cap: (a) remove the Unit and all materials and Tooling from the Facility (paying for conforming work performed and not yet paid) and complete it elsewhere, charging Manufacturer the reasonable excess cost of completion; and/or (b) cancel the Build Order without cancellation charge.

9.7 **Back-to-back intent.** The Parties acknowledge that Section 9.4 to 9.6 stand behind Schreiber AI's delivery obligations and liquidated damages to End Customers (`docs/contracts/MSA.md` Section 7.7) and that Manufacturer's supplier terms (`docs/contracts/SUPPLIER_TERMS.md` or equivalent) carry allocation notice, liquidated damages and cover rights that stand behind Section 9.4.

9.8 **Early delivery and storage.** Schreiber AI may accept early FAT. If Schreiber AI cannot take a FAT-passed Unit on the Delivery Date (End Customer site not ready), Manufacturer stores it at the Facility, insured, with weekly battery charge maintenance and inspection, for [CM_FREE_STORAGE_DAYS] free days and then at [CM_STORAGE_FEE_PER_DAY] per day; Schreiber AI passes this cost to the End Customer under `docs/contracts/MSA.md` Section 7.8.

9.9 **Delivery term.** Delivery is EXW Facility (Incoterms 2020) loaded onto the carrier's vehicle by Manufacturer's crane or forklift using the lift points and spreader bar, after FAT Acceptance and Q-11. Risk of loss passes when the Unit is secured on the carrier's vehicle. Manufacturer provides the weigh ticket, packing list, shock logger IDs and CSC decision record.

## 10. Title, risk and insurance of work in progress

10.1 Title to the Unit passes to Schreiber AI progressively with milestone payments (Section 11) and in full at FAT Acceptance; Manufacturer warrants good title free of liens and provides conditional lien waivers with each invoice and unconditional waivers on payment.

10.2 Risk of loss of the Unit, Purchased Materials and Consigned Materials at the Facility remains with Manufacturer until loaded on the carrier under Section 9.9. Manufacturer insures them under Section 13.

## 11. Pricing and payment

11.1 **Price per Unit by Tier (build labour, Facility, Purchased Materials handling and Licensed Trades; excludes Consigned Materials).**

| Tier | Build price per Unit | Purchased Materials | Notes |
| --- | --- | --- | --- |
| BEN 5 | [CM_PRICE_MICRO] | At cost plus [CM_MATERIAL_MARKUP_PCT] % handling | Skid, cabinet fit-out, no structural stage |
| BEN 30 | [CM_PRICE_BEN30] | At cost plus [CM_MATERIAL_MARKUP_PCT] % | |
| BEN 150 | [CM_PRICE_BEN150] | At cost plus [CM_MATERIAL_MARKUP_PCT] % | Includes vestibule, 2 x welding frames |
| BEN 500 | [CM_PRICE_BEN500] | At cost plus [CM_MATERIAL_MARKUP_PCT] % | Includes battery compartment partition, second egress door, DLC manifolds |
| Options | [CM_OPTION_PRICES] | | Cooling-on-UPS path, generator integration, RDHx in place of DX, C5 coating system, acoustic package |

Prices are firm for Build Orders placed in the first [CM_PRICE_FIRM_MONTHS] months and then adjusted annually by [PRICE_INDEX], capped at [CM_PRICE_ESCALATION_CAP_PCT] %. Volume rebate: [CM_VOLUME_REBATE_SCHEDULE].

11.2 **Milestones per Build Order.**

| # | Trigger | Share |
| --- | --- | --- |
| 1 | Build Order acceptance and container received (Q-01) | [CM_MILESTONE_1_PCT] % |
| 2 | H7 and W8 closed (structure and envelope) | [CM_MILESTONE_2_PCT] % |
| 3 | H10b and H11 closed (electrical energised, cooling charged) | [CM_MILESTONE_3_PCT] % |
| 4 | FAT Acceptance (H13) and Q-11 | [CM_MILESTONE_4_PCT] % less liquidated damages and back-charges |

Purchased Materials are invoiced at cost plus handling on receipt at the Facility with supplier invoices attached, or Schreiber AI may pay suppliers directly. Payment terms [PAYMENT_TERMS_DAYS] days. Schreiber AI may withhold amounts in dispute and 150 % of the estimated cost of open Nonconformance at FAT.

11.3 **Open book.** Manufacturer keeps records of labour hours by stage and Purchased Materials by Unit for 3 years and allows Schreiber AI to audit them for price review and for Change pricing.

## 12. Change control

12.1 Schreiber AI may change the Build Package for a Unit before the affected stage starts by a written Build Change Notice (BCN) stating the drawing, STE or BOM revision change. Manufacturer responds within 3 Business Days with price and schedule impact at Annex D rates; Schreiber AI confirms in writing before the change is built. Changes after a stage is complete are priced as rework.

12.2 Manufacturer may propose changes (producibility, cost, safety) by engineering change request; Schreiber AI decides. A Manufacturer proposal adopted into the Build Package is licensed to Schreiber AI under Section 14.3.

12.3 Revision control: Manufacturer builds only to the revision in the Build Order and the BCNs; superseded drawings are marked and removed from the shop floor within 1 Business Day of a BCN.

## 13. Insurance

Manufacturer carries and provides certificates for: commercial general liability [CM_INSURANCE_CGL] per occurrence including products/completed operations; property / builder's risk covering Units, Purchased Materials and Consigned Materials at the Facility for replacement value (not less than [CM_INSURANCE_PROPERTY]); workers' compensation statutory and employer's liability [CM_INSURANCE_EL]; commercial auto [CM_INSURANCE_AUTO]; pollution liability [CM_INSURANCE_POLLUTION] (refrigerant, glycol, coatings); umbrella [CM_INSURANCE_UMBRELLA]; and requires its Licensed Trade subcontractors to carry CGL and workers' compensation appropriate to their work. Schreiber AI is additional insured with waiver of subrogation on CGL, property and auto. Claims-made policies maintain a [INSURANCE_TAIL_YEARS]-year tail.

## 14. Intellectual property, tooling and confidentiality

14.1 **Build Package is Schreiber AI's.** All drawings, STE instructions, QC forms, BOMs, panel drawings, firmware, software, the configuration model and any derivative, including as-built red-lines and the dimensional reports, are Schreiber AI's property and Confidential Information. Manufacturer receives a limited licence to use them only to build Units under Build Orders. Manufacturer will not: reuse any part of the Build Package to build any other product; disclose it to anyone but employees and Licensed Trade subcontractors under written confidentiality; keep copies after the last Build Order is complete except one archival set for warranty defence; or reverse engineer the Controls Kit or firmware.

14.2 **No competing units.** During the term and for [CM_NON_COMPETE_MONTHS] months after, Manufacturer will not build modular data center units for third parties that use or are derived from the Build Package, and will tell Schreiber AI before accepting work on modular data center containers for a competitor so that Schreiber AI can verify that no Build Package information is used.

14.3 **Improvements.** Process improvements and producibility changes Manufacturer proposes and Schreiber AI adopts are assigned to Schreiber AI to the extent they relate to the Build Package, with Manufacturer keeping a royalty-free licence for its general shop practice that does not disclose Schreiber AI Confidential Information.

14.4 **Tooling (Annex C).** Tooling bought or made for BEN Engine production and paid for by Schreiber AI (directly or through a Tooling line in a Build Order) is Schreiber AI's property, marked "Property of Schreiber AI", maintained by Manufacturer, insured under Section 13, used only for Build Orders, and returned in working order within 10 Business Days of request or termination. Tooling Manufacturer funds itself remains Manufacturer's but is offered to Schreiber AI at depreciated cost on termination. Jig and fixture drawings derived from the Build Package are Schreiber AI's regardless of who paid.

14.5 **Marks and labels.** Manufacturer applies only the labels and nameplates in the Build Package. Manufacturer may not mark the Unit with its own name except where the Build Order permits a "Built by [CM_NAME] for Schreiber AI" plate inside the controls cabinet. Manufacturer may not publicise the relationship without Schreiber AI's written consent.

14.6 **Confidentiality.** `docs/contracts/MSA.md` Section 14 applies between the Parties, with the Build Package, pricing, End Customer identities and Sites as Schreiber AI's Confidential Information and Manufacturer's costs and processes as its own. `docs/contracts/NDA_MUTUAL.md` is superseded for information disclosed after the Effective Date.

## 15. Force majeure and allocation

15.1 `docs/contracts/MSA.md` Section 17.1 applies. Supplier allocation of a Purchased Material counts as Force Majeure for Manufacturer only under the conditions in Section 9.3 (prompt ordering, notice within 2 Business Days, pursuit of the approved alternate).

15.2 Manufacturer will tell Schreiber AI within 2 Business Days when any supplier notifies allocation, extended lead time, discontinuance, listing change, price increase above [SUPPLIER_PRICE_INCREASE_NOTICE_PCT] % or tariff change affecting a BOM line, and will forward the supplier's notice, so that Schreiber AI can give the End Customer notice under `docs/contracts/MSA.md` Sections 6.6 and 17.2.

15.3 Prolonged Force Majeure beyond [FM_TERMINATION_DAYS] days allows either Party to cancel the affected Build Order, with Schreiber AI paying for conforming work performed and taking the Unit and materials.

## 16. Warranty by Manufacturer

16.1 Manufacturer warrants each Unit's workmanship (structural modification, envelope, fit-out, electrical and cooling installation, controls installation, transport preparation) for **[CM_WARRANTY_MONTHS] months** (standard 18, so that it covers Schreiber AI's 12-month warranty to the End Customer plus up to 6 months of storage and site works) from FAT Acceptance, to the Build Package and good trade practice, and that Purchased Materials are new, as specified, and listed as the BOM requires.

16.2 Remedy: repair at the Site or the Facility at Manufacturer's cost, including Licensed Trades, within the response times of `docs/contracts/WARRANTY_TERMS.md` Section 6.3, or reimbursement of Schreiber AI's cost of doing so at Annex D rates. Envelope weather-tightness and coating workmanship: [CM_ENVELOPE_WARRANTY_MONTHS] months (standard 36). Structural welds: [CM_STRUCTURAL_WARRANTY_MONTHS] months (standard 60).

16.3 Exclusions: Schreiber AI design errors; Consigned Material defects; OEM component defects (OEM warranty applies); End Customer misuse or missed maintenance under `docs/contracts/WARRANTY_TERMS.md` Section 5; damage after risk of loss passed, other than latent Manufacturer defects.

## 17. Liability and indemnity

17.1 Each Party's liability under a Build Order is capped at [CM_LIABILITY_CAP_MULTIPLIER] times the Build Order price, excluding: indemnities; death, bodily injury or property damage from negligence; breach of Section 14; liquidated damages (which count toward the cap); and fraud. Neither Party is liable for consequential damages except as liquidated damages and cover costs under Section 9 state.

17.2 Manufacturer indemnifies Schreiber AI and its End Customers against third-party claims for injury or property damage from Manufacturer's or its subcontractors' negligence, against liens, and against violations of law at the Facility. Schreiber AI indemnifies Manufacturer against third-party IP claims about the Build Package and Controls Kit as `docs/contracts/MSA.md` Section 12.1(b).

## 18. Term, termination, exit and transition assistance

18.1 **Term.** [TERM_YEARS] years, renewing annually unless either Party gives 180 days' notice.

18.2 **Termination for breach.** 30 days' cure (10 days for non-payment); immediate for a safety or integrity breach (skipped hold point, unlicensed trade on reserved work, falsified QC record, unauthorised use of the Build Package).

18.3 **Termination for convenience by Schreiber AI.** On 90 days' notice. Build Orders in progress are completed or cancelled at Schreiber AI's election, with Schreiber AI paying for conforming work performed, Purchased Materials ordered and non-cancellable, and reasonable demobilisation.

18.4 **Exit and transition assistance.** On expiry or termination for any reason Manufacturer will, for up to [TRANSITION_DAYS] days at the Annex D rates (free where termination is for Manufacturer's breach): complete or hand over in-progress Units at Schreiber AI's election; release all Units, Consigned Materials, Purchased Materials paid for, Tooling and the Build Package copies to Schreiber AI's carrier; deliver all QC forms, NCRs, dimensional reports, PPAP-lite documents, supplier records, serial-number lists and as-built red-lines; make its Licensed Trade subcontractors available to a successor manufacturer; allow the successor to observe the last Unit built; and certify destruction of remaining Build Package copies. Schreiber AI pays undisputed invoices and returns Manufacturer's confidential process information.

18.5 **Survival.** Sections 4.1 (consigned title), 7.5, 9.4–9.7 (for Build Orders in progress), 10, 14, 16, 17, 18.4 and 19 survive.

## 19. General

19.1 Governing law: State of [GOVERNING_STATE]. Disputes: `docs/contracts/MSA.md` Section 19 (escalation, technical expert for CTQ/CTP and FAT disputes, mediation, arbitration at [ARBITRATION_BODY], [ARBITRATION_CITY]); Schreiber AI may seek injunctive relief and replevin of Units, materials and Tooling in court.

19.2 Notices: Schreiber AI [SCHREIBER_NOTICE_NAME], [SCHREIBER_NOTICE_EMAIL]; Manufacturer [CM_NOTICE_NAME], [CM_NOTICE_EMAIL].

19.3 No assignment or subcontracting of whole Units without consent (Licensed Trade subcontracting under Section 8.1 is permitted); independent contractors; compliance with law including export control, anti-corruption and OSHA; entire agreement; amendment in writing; severability; counterparts; electronic signature; order of precedence: this Agreement > Build Order > Build Package (and within the Build Package: drawings > STE instructions > BOM) > Manufacturer quotations.

## Annex A — Build Order form

| Field | Value |
| --- | --- |
| Build Order number | [BUILD_ORDER_ID] |
| Unit serial(s) / Tier / Configuration ID | [UNIT_SERIAL] / [TIER] / [CONFIG_ID] |
| End Customer SOW reference (for witness and FAT notice only) | [SOW_ID] |
| Drawing index revision / STE issue / BOM revision / QC forms revision | [DRAWING_INDEX_REV] / [ASSEMBLY_ISSUE] / [BOM_REV] / [DOC_REV_QC_FORMS] |
| Consigned Materials and delivery dates to Facility | per Annex B, [CONSIGNED_DELIVERY_DATES] |
| Purchased Materials: lines Manufacturer buys | per BOM column "purchased_by" = CM |
| FAT-ready date / Delivery Date (FAT Acceptance) | [CM_FAT_READY_DATE] / [CM_DELIVERY_DATE] |
| Build price / Purchased Materials estimate / Options | [CM_BUILD_PRICE] / [CM_PURCHASED_ESTIMATE] / [CM_OPTION_PRICES] |
| Liquidated damages | [CM_LD_RATE_PCT_PER_WEEK] % per week after [CM_LD_GRACE_DAYS] days, cap [CM_LD_CAP_PCT] % |
| Fire contractor | [FIRE_CONTRACTOR_NAME] (Manufacturer's / Schreiber AI's) |
| Load banks | [LOADBANK_PROVIDER] |
| Shipping carrier (arranged by Schreiber AI) and planned pick-up | [CARRIER_NAME], [DATE_SHIP_BASELINE] |

## Annex B — Consigned Materials

| Item | Quantity per Unit | Delivered to Facility by | Storage requirement |
| --- | --- | --- | --- |
| UL 508A controls panel (if not built by Manufacturer) | 1 | [CONSIGNED_DATE_PANEL] | Indoor, dry |
| BEN Controller: UL 508A panel with PLC, I/O, supplies, switch and edge computer (imaged, TPM-enrolled, sealed) — or Lite cabinet with RevPi | 1 + 1 spare edge computer | [CONSIGNED_DATE_GATEWAY] | Indoor, ESD |
| BEN Pods provisioned with device certificates, signed firmware and factory `cal_id`, with probe strings, enclosures and border router radios | [POD_COUNT] + spares per `docs/MAINTENANCE.md` Section 7 | [CONSIGNED_DATE_NODES] | Indoor, ESD; Pod W batteries fitted at FAT |
| Sensor kit (Pt1000 probe strings, SDP810, Setra 264 / Vaisala HMW90 / RLE LD2100 on Pro, rope leak, door reed) | per Unit | with Pods | Indoor |
| Calibration references (for Schreiber AI's use at W12/FAT) | 1 set | with commissioning lead | Returned after FAT |
| Labels, placards, arc-flash provisional labels, document pocket, laminated procedures | 1 set | [CONSIGNED_DATE_LABELS] | Indoor |
| Long-lead OEM equipment bought by Schreiber AI (as Build Order states): UPS, battery cabinets, in-row units, CDU, dry cooler, switchgear, generator | per Configuration | [CONSIGNED_DATE_OEM] | Per OEM; batteries per NFPA 855 storage guidance |

## Annex C — Tooling register

| Tooling item | Owner | Paid by | Location | Maintenance |
| --- | --- | --- | --- | --- |
| Welding frames for door and louvre openings ([TIER]) | Schreiber AI | Schreiber AI | Facility | Manufacturer |
| Floor channel drilling template | Schreiber AI | Schreiber AI | Facility | Manufacturer |
| Rack anchor template | Schreiber AI | Schreiber AI | Facility | Manufacturer |
| Spreader bar and lifting rig (CSC-rated) | [TOOLING_OWNER_SPREADER] | [TOOLING_PAYER_SPREADER] | Facility | Manufacturer, annual certification |
| Load-bank rack adapters and PDU plug sets | Schreiber AI | Schreiber AI | Facility | Manufacturer |
| FAT test harness (dP manometer, thermography camera, megger, micro-ohmmeter) | [TOOLING_OWNER_TEST] | [TOOLING_PAYER_TEST] | Facility | Calibrated annually |
| Blower-door kit | [TOOLING_OWNER_BLOWER] | [TOOLING_PAYER_BLOWER] | Facility | Calibrated annually |

## Annex D — Rates

| Item | Rate |
| --- | --- |
| Manufacturer general labour | [CM_RATE_LABOUR] per hour |
| Manufacturer QC inspector | [CM_RATE_QC] per hour |
| Certified welder (subcontract) | [RATE_WELDER] per hour |
| Licensed electrician (subcontract) | [RATE_ELECTRICIAN] per hour |
| Licensed HVAC technician EPA 608 (subcontract) | [RATE_HVAC] per hour |
| Facility storage after free days | [CM_STORAGE_FEE_PER_DAY] per Unit per day |
| Schreiber AI commissioning lead re-attendance (back-charge) | [COMMISSIONING_DAY_RATE] per day plus travel |
| Schreiber AI engineering (back-charge for Manufacturer-caused NCR engineering) | [RATE_PRINCIPAL_ENGINEER] per hour |
| Purchased Materials handling | [CM_MATERIAL_MARKUP_PCT] % |

## Signatures

| | Schreiber AI | Manufacturer |
| --- | --- | --- |
| Entity | [SCHREIBER_ENTITY_NAME] | [CM_NAME] |
| Signature | ______________________ | ______________________ |
| Name | [SCHREIBER_SIGNATORY_NAME] | [CM_SIGNATORY_NAME] |
| Title | [SCHREIBER_SIGNATORY_TITLE] | [CM_SIGNATORY_TITLE] |
| Date | [SIGNATURE_DATE_SCHREIBER] | [SIGNATURE_DATE_CM] |

---
Schreiber AI · BEN Engine (Business Edge Node) · Ben@SchreiberAI.com · Template maintained at `docs/contracts/CONTRACT_MANUFACTURING_AGREEMENT.md` · TEMPLATE — not legal advice — have counsel review before use.
