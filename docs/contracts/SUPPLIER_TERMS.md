# Purchase Order Terms and Conditions, with Supplier Quality Requirements — BEN Engine

> **TEMPLATE — not legal advice — have counsel review before use.**
> Schreiber AI · BEN Engine (Business Edge Node) · `docs/contracts/SUPPLIER_TERMS.md` · Template rev [TEMPLATE_REV]
> Bracketed `[FIELDS]` are filled by the proposal generator and the purchasing system from `docs/contracts/fields.json`. Part 1 is referenced on every Schreiber AI purchase order ("These Terms apply: docs/contracts/SUPPLIER_TERMS.md rev [TEMPLATE_REV]"). Part 2 is the Supplier Quality Requirements appendix. Contract Manufacturers buying Purchased Materials under `docs/contracts/CONTRACT_MANUFACTURING_AGREEMENT.md` use these Terms or terms at least as protective. Delete this box before issue.

# Part 1 — Purchase Order Terms and Conditions

## 1. Application and precedence

1.1 These Terms apply to every purchase order ("**PO**") issued by [SCHREIBER_ENTITY_NAME] ("**Buyer**" or "**Schreiber AI**") to the supplier named on the PO ("**Supplier**") for goods ("**Goods**") and related services. A PO is accepted by written acknowledgement, by shipment, or by starting work, whichever is first.

1.2 Order of precedence: a signed supply agreement between Buyer and Supplier (if any) > the PO face (part number, quantity, price, delivery date, ship-to) > these Terms > Part 2 Supplier Quality Requirements > Supplier's quotation (for description only). Supplier's standard terms, acknowledgement terms, invoice terms and click-through terms do not apply even if Buyer does not object to them.

1.3 **Catalog reference.** Goods are identified by Schreiber AI part code (from `purchasing/parts_catalog.json`), manufacturer and manufacturer part number as the PO states. An approved alternate is acceptable only if the PO or Buyer's written approval names it.

## 2. Price, price hold and tariffs

2.1 **Firm price.** The PO price is firm and includes packaging, standard documentation under Part 2, and, unless the PO states otherwise, delivery to the ship-to address under Section 5.

2.2 **Quotation price hold — 90 days.** A Supplier quotation is held firm for **90 days** ([PRICE_HOLD_DAYS] days) from its date for POs placed within that period, regardless of intervening list price changes. Supplier will state any shorter hold on the quotation face in bold; otherwise 90 days applies. For a Unit's long-lead items Buyer may request a price hold extension to [PRICE_HOLD_EXTENDED_DAYS] days against a deposit of [PRICE_HOLD_DEPOSIT_PCT] %.

2.3 **Tariff pass-through rules.** (a) The PO price includes all duties, tariffs and trade measures in force on the quotation date for the country of origin stated on the quotation. (b) If a new or increased duty, tariff, antidumping or countervailing measure, or Section 232/301 action takes effect **after the PO date** and before shipment and applies to the Goods as stated, Supplier may pass through the **documented incremental amount only** (customs entry showing the duty paid, or the manufacturer's tariff surcharge notice), with no markup, by notice within 10 Business Days of the measure taking effect and before shipment; Buyer may then accept, substitute an approved alternate, or cancel the affected line without charge if the Goods have not shipped. (c) Reductions in duty after the PO date are passed to Buyer the same way. (d) A change in Supplier's country of origin or sourcing is not a basis for a tariff surcharge. (e) No tariff pass-through applies to Goods already in Supplier's or the manufacturer's inventory in the destination country on the PO date; Supplier will state this on the quotation.

2.4 **Price increase notice.** Supplier gives at least [SUPPLIER_PRICE_INCREASE_NOTICE_DAYS] days' notice of list price increases on catalog items Buyer has bought in the prior 12 months, so that Buyer can give its customers notice under its own contracts.

2.5 **Most favoured pricing on repeat items.** For items Buyer has bought at least [MFN_REPEAT_COUNT] times, Supplier will not charge Buyer more than it charges similarly situated customers for the same quantity.

## 3. Delivery, lead-time notification and allocation

3.1 **Delivery date.** The PO delivery date is the date Goods are due at the ship-to address (the "**Delivery Date**"). Time is of the essence. Supplier acknowledges the Delivery Date within 3 Business Days of the PO or proposes an alternative with the manufacturer's evidence; silence is acceptance.

3.2 **Lead-time notification.** Supplier will notify Buyer in writing within **2 Business Days** of learning of: any change to the quoted or acknowledged lead time; the manufacturer placing the item on allocation; a production hold, recall or quality stop; discontinuance or end-of-life notice; change of listing (UL/ETL/CSA) or certification status; change of country of origin; a model or firmware revision that changes form, fit, function, refrigerant, GWP, communication protocol or register map; or any event likely to delay delivery. The notice states the cause, the new expected date and the manufacturer's written confirmation.

3.3 **Allocation clause.** If the Goods are placed on allocation by the manufacturer or Supplier: (a) Supplier will give Buyer not less than a pro-rata share of Supplier's available supply, calculated on Buyer's open POs and prior 12 months' purchases, and will not favour customers who order later or pay more; (b) Supplier will tell Buyer the allocation quantity and dates within 2 Business Days; (c) Supplier will identify and quote the manufacturer's recommended substitute and any approved alternate in Buyer's PO; (d) Buyer may cancel the unallocated balance without charge; (e) allocation is an excusable delay for Supplier only if Supplier complied with (a) to (c) and placed its own order with the manufacturer within [PO_PLACEMENT_DAYS] Business Days of Buyer's PO.

3.4 **Liquidated damages for late delivery.** If Goods are delivered later than the Delivery Date plus [SUPPLIER_LD_GRACE_DAYS] calendar days for a cause not excused under Section 3.3(e) or Section 12, Supplier will pay Buyer liquidated damages of **[SUPPLIER_LD_RATE_PCT_PER_WEEK] % of the PO value of the late line(s) per full week** (standard 0.5 %), up to **[SUPPLIER_LD_CAP_PCT] % of that value** (standard 10 %). The Parties agree this is a reasonable pre-estimate of Buyer's loss, including Buyer's own delay exposure to its customers for Units whose schedule depends on the Goods (`docs/contracts/MSA.md` Section 7.7) and standing behind the Contract Manufacturer's schedule (`docs/contracts/CONTRACT_MANUFACTURING_AGREEMENT.md` Section 9), and is not a penalty. Buyer may deduct liquidated damages from any payment due to Supplier.

3.5 **Expedite at Supplier's cost.** Where Supplier's cause threatens the Delivery Date, Supplier will at its cost use premium freight, split shipments, substitution with Buyer's approval, and manufacturer expedite fees to meet the Delivery Date, and will reimburse Buyer's documented expediting costs (premium inbound freight, re-sequencing charges at the Factory) up to the liquidated damages cap in addition to liquidated damages.

3.6 **Right to cover.** If delivery is or will be more than [SUPPLIER_COVER_TRIGGER_WEEKS] weeks late for Supplier's cause, Buyer may cancel the late line(s) and buy equivalent goods elsewhere, and Supplier will pay the difference between the cover price (including expedite and freight) and the PO price, in addition to liquidated damages accrued to the date of cover.

3.7 **Early and partial delivery.** Buyer may refuse or store at Supplier's cost deliveries more than [EARLY_DELIVERY_DAYS] days early or partial deliveries not agreed in writing. Payment terms run from the Delivery Date or actual delivery, whichever is later.

3.8 **Long-lead items.** For items the PO marks "long-lead" (UPS, switchgear, in-row and cabinet cooling units, CDU, dry cooler, transformers, generators, battery cabinets, containers), Supplier provides a written production and shipping schedule with the acknowledgement and a status update every 2 weeks.

## 4. Shipping, packaging and risk

4.1 Delivery term: **DAP [SHIP_TO_ADDRESS] (Incoterms 2020)** unless the PO states otherwise. Risk of loss passes on delivery at the ship-to address; title passes on the earlier of delivery or payment.

4.2 Packaging suitable for the mode of transport and for outdoor-rated Goods, with shock and tilt indicators on UPS, battery cabinets, cooling units and CDUs. Lithium batteries ship as UN 3480 / UN 3481 with the required documentation, state of charge and labels. Refrigerant-charged equipment ships with charge declared on the packing list.

4.3 Each shipment carries a packing list with PO number, Schreiber AI part code, manufacturer part number, quantity, serial numbers, country of origin, lot or date code, and the documents in Part 2 Section Q2.

## 5. Inspection and acceptance

5.1 Buyer may inspect Goods at Supplier's or the manufacturer's premises before shipment on reasonable notice, and at the ship-to address within [RECEIVING_INSPECTION_DAYS] days of delivery. Payment is not acceptance.

5.2 Nonconforming Goods (wrong item, damaged, missing listing mark, missing documentation, failing receiving inspection, or defective) may be rejected and returned at Supplier's cost for credit, replacement or repair at Buyer's election; replacement Goods ship expedited at Supplier's cost. Latent defects may be rejected when discovered.

5.3 Buyer may back-charge Supplier the reasonable cost of inspection, sorting, rework and re-test caused by nonconforming Goods, including repeated FAT steps at the Factory where the nonconformance caused the failure.

## 6. Warranty

6.1 Supplier warrants that Goods: (a) are new (not refurbished, used, counterfeit or grey-market), of the manufacturer and part number on the PO, in current production unless the PO says otherwise; (b) conform to the PO, the manufacturer's published specifications and the documents in Part 2; (c) carry the listing or certification the PO and Part 2 require; (d) are free from defects in materials and workmanship for the longer of **[SUPPLIER_WARRANTY_MONTHS] months from delivery** (standard 18, so that it covers Buyer's 12-month warranty to its customer plus up to 6 months of build and storage) or the manufacturer's standard warranty; (e) are free of liens; (f) do not infringe third-party intellectual property; (g) comply with law, including RoHS, REACH, TSCA, Proposition 65 labelling, AIM Act GWP rules, EPA Section 608, DOT/IATA for batteries and refrigerants, FCC Part 15 for electronics, and export control.

6.2 **Warranty pass-through.** Supplier assigns to Buyer, and Buyer may assign onward to its Contract Manufacturer, Integrator and end customer, the full manufacturer warranty, and will provide the registration procedure, serial-based warranty start date and claim contact with the Goods. Where the manufacturer's warranty starts at the manufacturer's shipment, Supplier states the start date on the packing list so Buyer can manage storage under `docs/contracts/WARRANTY_TERMS.md` Section 3.5. Supplier will register the warranty in Buyer's (or its customer's) name on request.

6.3 **Remedy.** Repair, replacement or refund at Buyer's election, with Supplier paying freight both ways and reasonable removal and reinstallation labour at the Factory or Site at Buyer's rates (`docs/contracts/SOW_TEMPLATE.md` Section 7.5). Replaced Goods are warranted for the longer of the remaining period or 12 months.

6.4 **Epidemic failure.** If the same failure mode occurs in [EPIDEMIC_FAILURE_PCT] % or more of a lot or of Goods delivered in any 12 months, Supplier will at its cost investigate (8D), replace or retrofit all affected Goods including those in deployed Units, and reimburse Buyer's field labour and travel.

## 7. Payment

7.1 Payment terms: net [PAYMENT_TERMS_DAYS] days from the later of invoice receipt, delivery and receipt of the Part 2 documentation. Early payment discount: [EARLY_PAYMENT_DISCOUNT]. Deposits for long-lead items as stated on the PO, secured by the manufacturer's order acknowledgement in Buyer's name where available.

7.2 Invoices reference the PO number and line, Schreiber AI part code, serial numbers and the tariff pass-through evidence if any. Buyer may set off liquidated damages, back-charges and credits.

## 8. Changes and cancellation

8.1 Buyer may change quantities, delivery dates and ship-to address by written change before shipment; Supplier gives the price and schedule impact within 3 Business Days; reasonable documented costs of changes are reimbursed.

8.2 Buyer may cancel for convenience before shipment, paying Supplier's documented non-recoverable costs and the manufacturer's cancellation or restocking charge stated on the quotation (which Supplier must disclose on the quotation; otherwise no charge applies), not exceeding the PO price. Standard catalog items are cancellable without charge until shipment.

8.3 Supplier may not change the manufacturer, part number, revision, country of origin, firmware version, refrigerant, or any document in Part 2 without Buyer's prior written approval.

## 9. Intellectual property and confidentiality

9.1 Specifications, drawings, register-map requirements, wiring diagrams, BOMs and quantities Buyer provides are Buyer's Confidential Information and property; Supplier uses them only to fulfil the PO and does not disclose Buyer's purchase volumes, unit configurations or customer identities.

9.2 Supplier grants Buyer and its customers a perpetual, royalty-free licence to use, copy and distribute with the Unit the documentation, firmware, register maps, STEP files and software delivered with the Goods to install, operate, integrate, maintain and relocate the Goods.

9.3 Supplier indemnifies Buyer and its customers against third-party IP claims arising from the Goods as delivered.

## 10. Compliance and conduct

10.1 Supplier complies with applicable law, including anti-corruption, export control (and provides ECCN/HTS codes on request), sanctions, conflict minerals reporting, modern slavery and environmental law, and Buyer's supplier code of conduct if provided.

10.2 Supplier provides Safety Data Sheets for refrigerants, glycols, coatings, agents and batteries with the first shipment and on each revision.

10.3 **Counterfeit prevention.** Supplier buys only from the manufacturer or its authorised distribution, maintains traceability to the manufacturer, and notifies Buyer immediately of any suspected counterfeit. Counterfeit Goods are rejected, retained by Buyer for reporting, and Supplier reimburses all costs.

## 11. Insurance, indemnity and liability

11.1 Supplier carries commercial general liability including products/completed operations of at least [SUPPLIER_INSURANCE_CGL] per occurrence, workers' compensation as required, and, for Goods installed or serviced at Buyer's Factory or Site, automobile liability [SUPPLIER_INSURANCE_AUTO]; certificates on request.

11.2 Supplier indemnifies Buyer, its Contract Manufacturers, Integrators and customers against third-party claims for injury, death or property damage caused by defective Goods or Supplier's negligence, and against product recall costs attributable to the Goods.

11.3 Neither Party is liable for consequential damages, except that liquidated damages, cover costs, back-charges, epidemic failure costs and indemnified amounts are recoverable as stated. Supplier's liability for defects is not capped below the greater of the PO value and the insurance in 11.1.

## 12. Force majeure

Neither Party is liable for delay caused by events beyond its reasonable control that it could not avoid by reasonable precautions (natural disaster, epidemic, war, government action, embargo, labour dispute not limited to its own workforce, carrier or port closure), provided it gives notice within 2 Business Days and mitigates. Manufacturer allocation is covered only by Section 3.3(e). Supplier's inability to buy at the price it expected is not force majeure. If force majeure exceeds [FM_TERMINATION_DAYS] days Buyer may cancel without charge.

## 13. General

Governing law: State of [GOVERNING_STATE]; venue [VENUE_COUNTY], [GOVERNING_STATE]; the UN Convention on Contracts for the International Sale of Goods does not apply. No assignment or subcontracting of the PO without consent. Independent contractors. Waivers in writing. Severability. Electronic documents are originals. Sections 6, 9, 10, 11 and Part 2 record-retention survive.

# Part 2 — Supplier Quality Requirements (Appendix)

These requirements apply to every PO by category. Non-delivery of a required document is a nonconformance under Section 5 and stops the payment clock.

## Q1. Category matrix

| Category (Schreiber AI code prefix) | Examples | Required documents and attributes |
| --- | --- | --- |
| STR Enclosure | One-trip high-cube ISO containers 10/20/40 ft; NEMA 3R / IP55 outdoor cabinets | CSC safety approval plate legible and photographed; manufacturer's certificate of conformance to ISO 1496-1 and ISO 668; one-trip condition statement (no dents > 20 mm, floor sound, doors seal); corner casting conformance to ISO 1161; steel mill certificates on request; for cabinets: UL 50 / UL 50E listing, NEMA type, integral AC listing (UL 1995 or UL 60335-2-40) and refrigerant/GWP declaration |
| PWR Switchgear and panelboards | UL 891 switchboards, UL 67 panelboards, breakers, SPDs (UL 1449), ATS (UL 1008) | UL listing file numbers and labels; SCCR ≥ 65 kA at the rated voltage; time-current curves and trip-unit data (for coordination and arc-flash studies); Modbus or SNMP register map where metering or communication is fitted; dimensional drawings in STEP; torque values on device labels |
| PWR UPS | Modular and monolithic UPS 208 V and 480 V | UL 1778 listing; efficiency curve; input THD and power factor data; battery compatibility list; Modbus/SNMP register map and MIB; STEP model; start-up requirement for warranty activation stated; firmware version on the packing list |
| PWR Batteries | Lithium (LFP) battery cabinets and modules | UL 1973 listing of modules; **UL 9540 system listing and a current UL 9540A test report (unit-level, showing no cell-to-cell propagation) for any shipment that will be installed in a configuration ≥ 20 kWh**; BMS communication protocol and register map; storage SOC and temperature requirements; UN 38.3 test summary; UN 3480 shipping documents; SDS; capacity warranty terms with SOH threshold |
| PWR Transformers and PDUs | Dry-type 480→208Y/120 transformers; rack PDUs | UL 1561 / UL 5085 (transformers); UL 60950-1 or UL 62368-1 (PDUs); PDU SNMP MIB and Modbus map; outlet metering accuracy class; STEP models |
| PWR Generators | Diesel or natural gas standby, sub-base tanks | EPA engine certification (emergency stationary engine); UL 2200 listing; NFPA 110 Level 2 Type 10 capability statement; UL 142 tank listing; sound power data; Modbus register map for the controller; STEP model |
| CLG DX cooling | In-row DX, cabinet air conditioners, condensing units | UL 1995 or UL 60335-2-40 listing; **refrigerant designation and GWP on the quotation and packing list; A1 class and GWP < 700 (R-513A, R-515B or equivalent) for units shipped for Buyer's container tiers; any A2L unit requires Buyer's prior written approval and the listed charge-limit and mitigation data**; charge per circuit by weight; capacity tables at Buyer's design outdoor temperatures (35 °C temperate and up to [CLIMATE_DESIGN_TEMP_C] °C); sound power data; Modbus/SNMP register map; STEP model; AIM Act Technology Transitions compliance statement for data-center use |
| CLG Liquid cooling | RDHx, CDU, dry coolers, manifolds, quick disconnects | Pressure rating and test certificate; materials of construction and wetted-material compatibility with propylene glycol; filtration requirements; pump curves; approach and capacity tables; leak-detection interface; Modbus register map; STEP models; UL or CE/ETL listing of electrical components |
| CLG Containment and airflow | Hot-aisle containment doors and frames, blanking panels, EC fans | Flame spread / smoke developed rating for panels (UL 723 / ASTM E84 Class A); EC fan motor data and Modbus interface where fitted |
| FS Fire detection and suppression | VEWFD aspirating detectors, spot detectors, UL 864 releasing panels, clean agent cylinders and nozzles, horn/strobes | UL listings; FM approval where applicable; agent designation (FK-5-1-12 class), NOAEL/LOAEL and design concentration data; hydrostatic test date of cylinders; installation only by a licensed contractor (Buyer's or Manufacturer's) |
| CTL Controls hardware | Raspberry Pi 5, SSD, PSU; managed PoE switches; Olimex ESP32-POE-ISO boards; SHT45, SDP810, DS18B20, ADS1115, relays, terminals; enclosures | FCC Part 15 / CE declarations; UL/IEC 62368-1 for PSUs and switches; UL 508 recognition for relays, terminals and supplies used in the UL 508A panel; manufacturer datasheets with revision; date/lot codes on the packing list; RoHS and REACH declarations; for sensors: manufacturer accuracy specification and, where offered, calibration certificate |
| CMP Compute | Servers, GPUs, switches, cabling | UL 62368-1 listing; manufacturer warranty registration; Redfish/IPMI and SNMP documentation; power supply input range 200–240 V; rack rail kits; STEP or dimension drawings |
| ENV Envelope materials | PIR / spray foam insulation, liner panels, coatings, sealants, doors | Insulation thermal resistance and ASTM E84 Class A flame spread; coating system data sheet for ISO 9223 class C2–C5 with DFT specification; sealant UV stability; door panic hardware listing (UL 305) |
| SITE / SVC Services | Civil, crane, electrical, HVAC, fire, welding subcontracts | Licences and certifications per `docs/contracts/CONTRACT_MANUFACTURING_AGREEMENT.md` Section 8.1; insurance per Section 11 |

## Q2. Documents with every shipment

| Document | Requirement |
| --- | --- |
| Certificate of conformance (CoC) | Signed statement that the Goods conform to the PO, the manufacturer's specification and the listings stated, with PO number, part numbers, quantities, serials or lot numbers, and manufacturer |
| Listing evidence | UL/ETL/CSA listing mark visible on the Goods and the file or certificate number on the CoC; where a listing is required by Q1 and is missing, the Goods are rejected |
| Traceability | Serial numbers for every UPS, battery module and cabinet, cooling unit, CDU, dry cooler, PDU, transformer, generator, fire panel, agent cylinder, gateway, PoE switch and BEN Node board; lot/date code for sensors, relays and supplies; retained by Supplier for 10 years and by Buyer in the as-built BOM |
| Country of origin and HTS code | On the packing list and commercial invoice |
| Test reports | Factory test reports for UPS, switchgear (including SCCR and trip-unit settings as shipped), cooling units (run test), CDU (pressure test), generators (load test), batteries (capacity and BMS), per the manufacturer's standard |
| Register maps and MIBs | **Modbus register maps (address, type, scaling, units, function codes) and SNMP MIBs for every device with a communication port**, in machine-readable form (CSV or the manufacturer's PDF plus CSV), matching the shipped firmware version; required for the gateway's pollers (`spec/PROTOCOL.md` equipment topics) |
| STEP files | **3-D STEP (AP214 or AP242) models and 2-D dimensional drawings for every enclosure-scale item** (UPS, battery cabinet, cooling unit, condenser, dry cooler, CDU, racks, panelboards, transformers, generator, fire cylinders) for Buyer's drawing generator and digital twin; delivered with the quotation or within 10 Business Days of PO |
| Installation, operation and maintenance manuals | Current revision, electronic; included in the Turnover Package (item D2) |
| Warranty statement and registration procedure | With start-date rule and claim contact |
| SDS | For refrigerants, glycol, agents, coatings, sealants, batteries |
| Firmware version and release notes | For every device with firmware; manufacturer's signed-update procedure described |
| SBOM or declaration | For devices with network interfaces (UPS, PDU, cooling controllers, switches): software bill of materials or a manufacturer cybersecurity statement, default-credential change procedure, and the list of open network services |

## Q3. Specific requirements

### Q3.1 Refrigerant-charged equipment and refrigerant

- Refrigerant designation (ASHRAE 34), safety class and GWP (AR4) on the quotation, CoC and packing list.
- For Buyer's container tiers (BEN 10, BEN 20): **A1 class, GWP < 700**. A2L (R-454B, R-32) is not accepted for equipment installed inside the ITE space without Buyer's prior written approval and the listed charge-limit, leak-detection and mitigation data under UL 60335-2-40 and ASHRAE 15.
- Compliance statement with the AIM Act Technology Transitions rule for new data-center / IT-room cooling installed on or after 1 January 2027 (GWP < 700). R-410A equipment is not accepted for new builds.
- Any field charging, recovery or repair performed by Supplier is by **EPA Section 608 Type II or Universal certified technicians**, with certificate numbers on the service record, and with refrigerant quantities recorded per appliance.
- Refrigerant cylinders: DOT-compliant, labelled, with CoC of refrigerant purity (AHRI 700).

### Q3.2 Batteries (lithium) — UL 9540 / UL 9540A

- Modules UL 1973 listed; system (cabinet with BMS) **UL 9540 listed**; **UL 9540A test report at unit level** with the current edition, dated within [UL9540A_REPORT_MAX_AGE_MONTHS] months, delivered with the quotation for any configuration that will exceed 20 kWh total lithium in a Unit (BEN 20 optional package; BEN 40 always).
- Report must show cell-to-cell and module-to-module propagation results, gas composition and volume data sufficient for NFPA 69 deflagration venting sizing, and the spacing basis.
- BMS alarm and telemetry interface (Modbus or CAN with documented map) available to Buyer's gateway.
- Storage, transport SOC, charging temperature limits (charging below 0 °C inhibited) and shelf-life stated.
- Chemistry: LFP unless Buyer approves otherwise in writing.

### Q3.3 Electrical equipment and the UL 508A panel

- All electrical Goods NRTL listed for the application (NEC 110.3(B)); components for the controls panel must be on the UL 508A recognised-component list or listed, with SCCR data for SCCR marking under Supplement SB.
- SCCR ≥ 65 kA for panelboards and switchgear at 208/240 V and 480 V unless the PO states a series rating.
- Trip-unit and relay settings as shipped documented for the coordination study.

### Q3.4 Environmental compliance

- **RoHS** (EU 2011/65/EU as amended) and **REACH** SVHC declarations for all electronics, sensors, cables, PCBs, enclosures and coatings where relevant; TSCA PFAS reporting cooperation where applicable; California Proposition 65 labels as required.
- Conflict minerals (3TG) reasonable country-of-origin inquiry on request.
- Packaging recyclable and marked; wood packaging ISPM 15 for export.

### Q3.5 Traceability and records

Supplier retains CoCs, test reports, serial-number records and calibration records for 10 years and provides them within 5 Business Days of request, including for warranty, recall, AHJ or incident investigation.

### Q3.6 Change notification (PCN/EOL)

Supplier gives at least [PCN_NOTICE_DAYS] days' notice of any product change notice (PCN) affecting form, fit, function, firmware, refrigerant, listing or register map, and at least [EOL_NOTICE_DAYS] days' notice of end-of-life with a last-time-buy opportunity and a recommended replacement, so that Buyer can update the approved-alternates column of its BOM and repeat affected FAT tests (`docs/RISK_REGISTER.md` R19).

### Q3.7 First article and sample approval

For a new part number, a new manufacturer, or a changed revision, Buyer may require a first-article sample with the Q2 documents before releasing the production PO; approval is in writing and references the revision approved.

### Q3.8 Corrective action

Supplier responds to a Supplier Corrective Action Request within 10 Business Days with containment, root cause and corrective action (8D format acceptable), and implements it by the agreed date. Two open overdue SCARs suspend new POs until closed.

### Q3.9 Site and Factory conduct

Supplier personnel at Buyer's Factory, a Contract Manufacturer's Facility or a Site follow its safety rules, the entry procedure in `docs/MAINTENANCE.md` Section 9 where applicable, LOTO, and PPE requirements, sign in and out, and do not photograph without consent.

### Q3.10 Supplier performance

Buyer tracks on-time delivery, documentation completeness, receiving rejects, SCAR responsiveness and warranty claims per Supplier and reviews them with Supplier [SUPPLIER_REVIEW_FREQUENCY]. Performance below [SUPPLIER_OTD_THRESHOLD_PCT] % on-time or [SUPPLIER_REJECT_THRESHOLD_PCT] % receiving rejects over two quarters moves Supplier to probation and may remove it from the approved-supplier list.

## Q4. PO face fields (filled by the purchasing system)

| Field | Value |
| --- | --- |
| PO number | [PO_NUMBER] |
| Supplier | [SUPPLIER_NAME], [SUPPLIER_ADDRESS], [SUPPLIER_CONTACT] |
| Ship-to | [SHIP_TO_ADDRESS] (Schreiber AI Factory / Contract Manufacturer Facility / Site) |
| For Unit / Build Order | [UNIT_SERIAL] / [BUILD_ORDER_ID] |
| Lines: Schreiber AI part code, manufacturer, manufacturer part number, approved alternate(s), quantity, unit price, extended price, category, long-lead flag | [PO_LINES] |
| PO value | [PO_VALUE] [CURRENCY] |
| Quotation reference and date (price hold 90 days) | [SUPPLIER_QUOTE_REF], [SUPPLIER_QUOTE_DATE] |
| Delivery Date | [PO_DELIVERY_DATE] |
| Liquidated damages | [SUPPLIER_LD_RATE_PCT_PER_WEEK] % per week after [SUPPLIER_LD_GRACE_DAYS] days, cap [SUPPLIER_LD_CAP_PCT] % |
| Payment terms | Net [PAYMENT_TERMS_DAYS] |
| Required documents (Q1 category rows and Q2) | [PO_REQUIRED_DOCS] |
| Buyer contact | [BUYER_CONTACT_NAME], [BUYER_CONTACT_EMAIL] |
| Terms | `docs/contracts/SUPPLIER_TERMS.md` rev [TEMPLATE_REV] |

---
Schreiber AI · BEN Engine (Business Edge Node) · Ben@SchreiberAI.com · Template maintained at `docs/contracts/SUPPLIER_TERMS.md` · TEMPLATE — not legal advice — have counsel review before use.
