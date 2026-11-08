# Change Order — BEN Engine SOW

> **TEMPLATE — not legal advice — have counsel review before use.**
> Schreiber AI · BEN Engine (Business Edge Node) · `docs/contracts/CHANGE_ORDER.md` · Template rev 7906fcc
> Bracketed `[FIELDS]` are filled by the proposal generator from `docs/contracts/fields.json`. One form per change. Delete this box before signature.

| Field | Value |
| --- | --- |
| Change Order number | 001 (sequential per SOW) |
| SOW | SOW-BEN20-20261108-508EC188 under MSA MSA-ACMECLINIC-2026 |
| Unit serial | BEN-BEN20-508EC188 |
| Tier / Configuration | ben20 / SAI-BEN20-20261108-508EC188-cfg-v1.0 |
| Customer | Acme Clinic |
| Requested by | [CO_REQUESTED_BY] (Customer / Schreiber AI / AHJ requirement / supplier allocation or tariff under MSA 6.6) |
| Request date | [CO_REQUEST_DATE] |
| Proposal delivered | [CO_PROPOSAL_DATE] (due within 10 Business Days of request, MSA 6.3) |
| Emergency work performed before signature (MSA 6.5) | [CO_EMERGENCY] (yes / no) |

## 1. Description of the change

[CO_DESCRIPTION]

Reason for the change: [CO_REASON]

Documents affected (drawings, config.json fields, Site Requirements sections, compliance pack items, SOW sections): [CO_DOCUMENTS_AFFECTED]

## 2. Configuration impact

| Field in `config.json` | Before | After |
| --- | --- | --- |
| [CO_CONFIG_FIELD_1] | [CO_CONFIG_BEFORE_1] | [CO_CONFIG_AFTER_1] |
| [CO_CONFIG_FIELD_2] | [CO_CONFIG_BEFORE_2] | [CO_CONFIG_AFTER_2] |

New Configuration ID after this Change Order: [CO_NEW_CONFIG_ID]. Derived sizing re-run: [CO_DERIVED_SIZING_CHANGED] (yes / no). If any of feeder breaker, UPS size, battery kWh, cooling unit count, gross mass or ASHRAE class changes, the PE anchorage, arc-flash study, refrigerant calc, NFPA 855 status and Site Requirements are re-checked and listed in Section 1.

## 3. Price impact

| Element | Amount (USD) | Basis |
| --- | --- | --- |
| Re-engineering and document re-issue | [CO_PRICE_ENGINEERING] | Rates in SOW Section 7.5 |
| Materials added / removed (net) | [CO_PRICE_MATERIALS] | Cost plus 15 % / credit at cost less restocking |
| OEM and supplier cancellation or restocking charges | [CO_PRICE_CANCELLATION] | At cost, evidence attached |
| Factory / Contract Manufacturer rework | [CO_PRICE_REWORK] | Quotation attached |
| Repeated tests (FAT / SAT steps re-run) | [CO_PRICE_RETEST] | SOW Section 7.4 and 7.5 |
| Permit re-submission fees | [CO_PRICE_PERMITS] | At cost |
| Storage, standby, crane re-mobilisation caused by the change | [CO_PRICE_DELAY_CHARGES] | SOW Section 7.4 |
| Tariff / allocation cost difference (MSA 6.6, 17.2) | [CO_PRICE_TARIFF] | Supplier evidence attached |
| **Net price change** | **[CO_PRICE_DELTA]** | |
| Unit price before | [CO_PRICE_BEFORE] | |
| **Unit price after** | **[CO_PRICE_AFTER]** | New basis for milestones and liquidated damages |

Milestone adjustment: [CO_MILESTONE_ADJUSTMENT] (for example, "net change added to milestone 3" or "invoiced on signature of this Change Order").

## 4. Schedule impact and re-baselined dates

| Milestone | Current baseline | Change (days) | **Re-baselined date** |
| --- | --- | --- | --- |
| H4 Engineering Release | [DATE_H4_CURRENT] | [CO_SCHEDULE_DELTA_DAYS] | [CO_NEW_DATE_H4] |
| H13 FAT | [DATE_FAT_CURRENT] | [CO_SCHEDULE_DELTA_DAYS] | [CO_NEW_DATE_FAT] |
| Shipment | [DATE_SHIP_CURRENT] | [CO_SCHEDULE_DELTA_DAYS] | [CO_NEW_DATE_SHIP] |
| H16 Pad and utilities ready (Customer) | [DATE_H16_CURRENT] | [CO_SCHEDULE_DELTA_DAYS_H16] | [CO_NEW_DATE_H16] |
| H19 SAT | [DATE_SAT_CURRENT] | [CO_SCHEDULE_DELTA_DAYS] | [CO_NEW_DATE_SAT] |
| W20 Turnover | [DATE_TURNOVER_CURRENT] | [CO_SCHEDULE_DELTA_DAYS] | [CO_NEW_DATE_TURNOVER] |

Schedule basis: [CO_SCHEDULE_BASIS] (for example, re-procurement lead time of the changed cooling unit; re-sequencing of Factory slot; crane re-booking window).

Classification of this change for delay purposes (MSA 7.5 to 7.8): [CO_DELAY_CLASSIFICATION]
- **Customer-requested or Customer-Caused Delay**: Schreiber AI's liquidated damages exposure is suspended for [CO_SCHEDULE_DELTA_DAYS] days and the re-baselined FAT date becomes the new liquidated damages reference date; Customer delay charges in Section 3 apply.
- **Schreiber AI-caused**: the FAT date for liquidated damages does not move; price impact is nil to Customer.
- **Excusable (AHJ requirement beyond compliance pack, Force Majeure, allocation or tariff under MSA 17.2)**: dates re-baselined; no liquidated damages or delay charges for the excusable period; cost treated as stated in Section 3.

## 5. Acceptance criteria impact

| Acceptance step or SAT item | Before | After |
| --- | --- | --- |
| [CO_ACCEPTANCE_ITEM] | [CO_ACCEPTANCE_BEFORE] | [CO_ACCEPTANCE_AFTER] |

If none: "No change to the acceptance criteria in SOW Section 8."

## 6. Other impacts

| Topic | Impact |
| --- | --- |
| Site Requirements (Annex A) sections affected | [CO_SITE_REQ_SECTIONS] |
| Permits affected / re-submission needed | [CO_PERMITS_AFFECTED] |
| Risk Register items newly relevant | [CO_RISKS_AFFECTED] |
| Warranty (for example, OEM warranty start date moves with storage) | [CO_WARRANTY_IMPACT] |
| Software Licence / Managed Services fee (if IT kW or delivery model changes) | [CO_LICENSE_SLA_IMPACT] |
| Spares kit | [CO_SPARES_IMPACT] |
| Training / Turnover Package items | [CO_TURNOVER_IMPACT] |

## 7. Terms

7.1 This Change Order amends SOW SOW-BEN20-20261108-508EC188 as stated above and in no other respect. The MSA, the SOW as amended, and prior Change Orders remain in force.

7.2 The price and schedule in this Change Order are firm once signed by both Parties and are not subject to further adjustment except by another Change Order.

7.3 Work on this change starts only after both signatures, except emergency work under MSA 6.5 as declared above.

7.4 This Change Order is entered in the SOW Change Order log (SOW Section 11) with its running totals.

## 8. Signatures

| | Schreiber AI | Customer |
| --- | --- | --- |
| Signature | ______________________ | ______________________ |
| Name | [SCHREIBER_PM_NAME] or Ben Schreiber | [CUSTOMER_PM_NAME] or [CUSTOMER_SIGNATORY_NAME] |
| Title | Founder | [CUSTOMER_SIGNATORY_TITLE] |
| Date | [CO_SIGNATURE_DATE_SCHREIBER] | [CO_SIGNATURE_DATE_CUSTOMER] |

Signature authority: Change Orders up to [CO_PM_AUTHORITY_LIMIT] may be signed by the project managers named in the SOW; above that amount, by the signatories of the SOW.

---
Schreiber AI · BEN Engine (Business Edge Node) · Ben@SchreiberAI.com · Template maintained at `docs/contracts/CHANGE_ORDER.md` · TEMPLATE — not legal advice — have counsel review before use.
