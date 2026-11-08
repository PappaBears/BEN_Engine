# Channel and White-Label Integrator Agreement — BEN Engine

> **TEMPLATE — not legal advice — have counsel review before use.**
> Schreiber AI · BEN Engine (Business Edge Node) · `docs/contracts/INTEGRATOR_AGREEMENT.md` · Template rev [TEMPLATE_REV]
> Bracketed `[FIELDS]` are filled by the proposal generator from `docs/contracts/fields.json`. Used when an MEP firm, systems integrator or regional partner sells, installs and supports BEN Engine Units under its own brand or Schreiber AI's. Delete this box before signature.

**Agreement ID:** [INTEGRATOR_AGREEMENT_ID]
**Effective Date:** [EFFECTIVE_DATE]

This Channel and White-Label Integrator Agreement ("**Agreement**") is between **[SCHREIBER_ENTITY_NAME]**, a [SCHREIBER_ENTITY_TYPE] at [SCHREIBER_ADDRESS] ("**Schreiber AI**"), and **[INTEGRATOR_NAME]**, a [INTEGRATOR_ENTITY_TYPE] at [INTEGRATOR_ADDRESS] ("**Integrator**").

## 1. Definitions

1.1 "**End Customer**" means a person or entity that buys a Unit or Managed Services from Integrator for its own use.

1.2 "**Integrator Brand**" means Integrator's trademarks and the Brand File (in the format of `web/kit/brand.json`) approved under Section 8.

1.3 "**Integrator Order**" means Integrator's order to Schreiber AI for a Unit, in the form of `docs/contracts/SOW_TEMPLATE.md` adapted as Annex 1 says, with Integrator as the ordering party and the End Customer and Site identified.

1.4 "**Certified Personnel**" means Integrator employees who hold current Schreiber AI certification under Section 4.

1.5 "**Controls Kit**" means the UL 508A controls panel, gateway, BEN Nodes, sensors, firmware and licences supplied by Schreiber AI for a Unit.

1.6 "**Territory**" means [TERRITORY].

1.7 "**Delivery Model**" means one of: (a) **Resale** — Schreiber AI builds and commissions the Unit, Integrator sells it and provides L1 support; (b) **Install Partner** — Schreiber AI builds the Unit to FAT, Integrator performs site works, set-down, hook-up and, with Schreiber AI, SAT; (c) **Licensed Builder** — Integrator builds Units at its own or a Contract Manufacturer's facility to Schreiber AI's drawings and STE instructions using Schreiber AI Controls Kits, under the quality plan in Section 5. The Delivery Models granted to Integrator are: [INTEGRATOR_DELIVERY_MODELS].

1.8 Other capitalised terms (Unit, Tier, Configuration, Hold Point, Witness Point, FAT, SAT, Commissioning Script, Commissioning Report, Turnover Package, Customer Data, BEN Controls, Signed Image) have the meanings in `docs/contracts/MSA.md`.

## 2. Appointment

2.1 **Non-exclusive appointment.** Schreiber AI appoints Integrator as a non-exclusive integrator for BEN Engine Units in the Territory for the Delivery Models in Section 1.7 and the Tiers [INTEGRATOR_TIERS]. Schreiber AI may appoint other integrators and sell directly in the Territory. [EXCLUSIVITY_TERMS] (standard: none; optional: exclusivity for [EXCLUSIVITY_SEGMENT] subject to the minimum commitment in Section 2.4).

2.2 **Brand modes.** Integrator may sell Units (a) under the Schreiber AI brand as "BEN Engine by Schreiber AI, installed by [INTEGRATOR_NAME]", or (b) under the Integrator Brand as a white-label product under Section 8 and the Software Licence Type C. The mode is stated on each Integrator Order.

2.3 **Independent contractor.** Integrator buys and resells in its own name and for its own account, sets its own resale prices, and is not Schreiber AI's agent, franchisee or employee. Integrator may not make commitments for Schreiber AI.

2.4 **Minimum commitment.** Integrator will order at least [MIN_UNITS_PER_YEAR] Units (or [MIN_REVENUE_PER_YEAR] in Unit purchases) per contract year. If the minimum is missed, Schreiber AI may revoke any exclusivity and move Integrator to the base discount tier; it may not terminate for that reason alone in the first contract year.

2.5 **Outside the Territory.** Integrator will not actively market outside the Territory but may accept unsolicited orders, and will coordinate with Schreiber AI where another integrator has exclusivity.

## 3. Ordering, pricing and discounts

3.1 **Integrator Orders.** Each Unit is ordered by an Integrator Order. Integrator remains responsible to Schreiber AI for payment whether or not the End Customer pays Integrator. `docs/contracts/MSA.md` Sections 3 (Ordering), 6 (Change Orders), 7 (Schedule, delivery, title, risk), 8 (Acceptance), 9 (Payment), 10 (Warranty) and 17 (Force Majeure) apply to each Integrator Order as between Schreiber AI and Integrator, with Integrator in the place of Customer, and with the changes in Annex 1.

3.2 **Price list and discounts.** Integrator buys at Schreiber AI's then-current list price per Tier and module, less the discount in the schedule below. The list price is firm for an Integrator Order at the price in effect when the Integrator Order is signed. Schreiber AI will give 60 days' notice of list price changes except for changes under `docs/contracts/MSA.md` Section 6.6 (tariff and allocation).

| Discount tier | Annual Units ordered | Discount on hardware and build (enclosure, power, cooling, compute module) | Discount on Controls Kit and engineering services | Controls licence per Unit per year (Type C) |
| --- | --- | --- | --- | --- |
| Base | 1–[DISCOUNT_TIER_1_MAX_UNITS] | [DISCOUNT_TIER_1_HW_PCT] % | [DISCOUNT_TIER_1_CTL_PCT] % | BEN Micro [LICENSE_MICRO_ANNUAL]; BEN 10 [LICENSE_BEN10_ANNUAL]; BEN 20 [LICENSE_BEN20_ANNUAL]; BEN 40 [LICENSE_BEN40_ANNUAL] |
| Silver | [DISCOUNT_TIER_2_MIN_UNITS]–[DISCOUNT_TIER_2_MAX_UNITS] | [DISCOUNT_TIER_2_HW_PCT] % | [DISCOUNT_TIER_2_CTL_PCT] % | less [LICENSE_DISCOUNT_TIER_2_PCT] % |
| Gold | [DISCOUNT_TIER_3_MIN_UNITS] and above | [DISCOUNT_TIER_3_HW_PCT] % | [DISCOUNT_TIER_3_CTL_PCT] % | less [LICENSE_DISCOUNT_TIER_3_PCT] % |

Reference values for the controls licence in `docs/investors/VC_PROPOSITION.md` are $1,200 / $4,800 / $12,000 / $30,000 per year by tier; Managed Services reference $45 per kW-month.

3.3 **Licensed Builder pricing.** For Units Integrator builds itself, Integrator pays Schreiber AI: the engineering release fee per Unit [LICENSED_BUILDER_ENGINEERING_FEE] (Configuration, IFC drawings, BOM, calcs, compliance pack, FAT/SAT procedure); the Controls Kit at [CONTROLS_KIT_PRICE_BY_TIER]; the per-Unit platform royalty [PLATFORM_ROYALTY_PCT] % of the Unit's resale price or [PLATFORM_ROYALTY_MIN] per Unit, whichever is greater; the controls licence per Section 3.2; and Schreiber AI witness and FAT attendance at the rates in Annex 2.

3.4 **Managed Services resale.** Integrator may resell Managed Services under `docs/contracts/MANAGED_SERVICES_SLA.md` at a wholesale rate of [SLA_WHOLESALE_RATE_PER_KW_MONTH] per kW-month, with Integrator providing L1 and Schreiber AI providing L2/L3 and the remote monitoring, or Integrator may provide its own managed service using the Dashboard under Software Licence Type C with Schreiber AI L2/L3 support at [L2L3_SUPPORT_FEE_PER_UNIT_MONTH] per Unit per month.

3.5 **Payment.** Milestones per `docs/contracts/MSA.md` Section 9.1 (30 / 40 / 25 / 5) unless Annex 1 states otherwise. Payment terms [PAYMENT_TERMS_DAYS] days. Credit limit [INTEGRATOR_CREDIT_LIMIT]; orders above the limit require a deposit or letter of credit.

3.6 **Price protection on End Customer quotes.** Integrator may request a price hold of up to [PRICE_HOLD_DAYS] days for a named End Customer opportunity registered under Section 3.7; Schreiber AI will honour the list price in effect at registration for an Integrator Order signed within the hold.

3.7 **Deal registration.** Integrator registers each opportunity (End Customer, Site, Tier, expected IT kW, expected date) in Schreiber AI's portal. A registered opportunity is protected against Schreiber AI's direct sales effort and against other integrators' registration for [DEAL_REGISTRATION_DAYS] days, renewable while the opportunity is active.

## 4. Certification and training

4.1 **Required before first Unit.** Before Integrator sells (Resale), installs (Install Partner) or builds (Licensed Builder) a Unit, it will have the Certified Personnel in the table below, trained by Schreiber AI at the fees in Annex 2 (first cohort of [FREE_TRAINING_SEATS] seats free).

| Role | Minimum number | Training modules | Renewal |
| --- | --- | --- | --- |
| Sales engineer | 1 | Selector and mission profiles; risk register disclosure before pricing; Site Requirements form; proposal generator | Annual refresher |
| Site / project manager | 1 | `docs/PROCESS_FLOW.md` stages 1–22, hold and witness points, Change Order discipline, SITE_REQUIREMENTS H3 and H16, permit matrix | Annual |
| Field technician (Install Partner, Licensed Builder) | 2 | STE assembly instructions for the licensed Tiers (`design/assembly/ASSEMBLY-<tier>.md`, `STE_STYLE.md`); QC forms Q-01 to Q-12; Controls Kit installation; Commissioning Script training (factory and site mode); calibration spot-checks; entry procedure; T1–T5, T7 | Every 2 years and on each major firmware release |
| Commissioning lead (Install Partner, Licensed Builder) | 1 | Full Commissioning Script, `docs/TEST_GUIDE.md` E1–E12, report integrity (SHA-256), Punch List classification, Turnover Package assembly, credential handover | Annual |
| Support engineer (L1) | 1 | Dashboard, alarm severities, RMA procedure, escalation to Schreiber AI L2 | Annual |

4.2 **Certification record.** Schreiber AI issues a certificate per person with an expiry date. Integrator keeps the roster current in the portal and does not deploy uncertified staff on hold-point or commissioning work.

4.3 **Hold points Integrator may not self-perform.** Regardless of certification, the following may be performed only by the licensed or certified trade stated, engaged by Integrator under written subcontract with the insurance in Section 11, and recorded on the QC form:

| Hold point | Work | Required trade | Form |
| --- | --- | --- | --- |
| H7 | Structural modification of the container; weld inspection | AWS D1.1 (or ISO 9606-1) certified welder; Certified Welding Inspector for inspection; PE letter | Q-02 |
| H10a, H10b | Electrical rough-in, terminations, torque, insulation resistance, energisation | Licensed electrical contractor; electrical permit | Q-07 |
| H11 | Refrigerant brazing, pressure test, evacuation, charge; glycol loop fill | Licensed HVAC contractor with EPA 608 Type II/Universal technicians | Q-06 |
| — | Fire detection and clean agent system installation, acceptance and door fan test | State-licensed fire protection contractor; fire marshal plan review | Q-09 |
| — | UL 508A controls panel assembly (Licensed Builder) | UL 508A listed panel shop (Schreiber AI's or a listed shop; Integrator may not build the panel unless it is itself a listed shop) | Q-08 |
| H18 | Site hook-up, pre-energisation checks | Licensed electrician; licensed HVAC; AHJ inspection | Q-12 |
| H22 | Refrigerant recovery, battery removal (UN 3480), data sanitisation on relocation or decommission | EPA 608 technician; hazmat-trained shipper; NIST 800-88 certificate | Decommission report |

Integrator's general labour may perform the mechanical work in the STE instructions (mounting, cable pulling, labelled connector plug-in, panel installation, rack installation) once the named trade has signed the preceding hold point, exactly as the STE instructions state.

4.4 **Commissioning Script.** Only a certified commissioning lead runs the Commissioning Script for FAT or SAT. The operator name is recorded in the report signature block (never "unsigned"). Integrator may not alter the script, its pass criteria or the report.

## 5. Quality

5.1 **Quality plan.** For every Unit Integrator installs or builds, Integrator follows `docs/PROCESS_FLOW.md`, the STE assembly instructions, the IFC drawings with their CTQ/CTP tables, and the QC forms **Q-01 to Q-12** of `design/assembly/QC_FORMS.md`, completing each form in full with the named signatory and uploading it to the Schreiber AI portal within 2 Business Days of completion.

5.2 **Schreiber AI witness points.** Integrator will give Schreiber AI at least 5 Business Days' notice of, and allow Schreiber AI to attend (in person or by live video), every hold point and witness point, and in particular: W6 container receiving; H7 weld inspection; W8 insulation and vapour barrier before the liner is closed; H10b torque and megger before energisation; H11 pressure test; W12 controls I/O point-to-point; **H13 FAT (Schreiber AI attendance mandatory for Integrator's first [FIRST_UNITS_MANDATORY_WITNESS] Units of each Tier and for every BEN 40)**; H18 pre-energisation; **H19 SAT (Schreiber AI signs the SAT Certificate for every Unit)**. Where Schreiber AI declines in writing, the form records it and work continues.

5.3 **Nonconformance.** A deviation from a drawing, CTQ/CTP tolerance, STE step or QC form is a nonconformance. Integrator records it on a nonconformance report (NCR) with photos, stops work on the affected item, and asks Schreiber AI engineering for a disposition (use-as-is, rework, repair, reject) within 2 Business Days. Integrator does not close the liner, energise, charge, ship or energise a Unit with an open NCR on the affected system.

5.4 **Audit.** Schreiber AI may audit Integrator's facilities, records, subcontractor certifications and in-progress Units on 5 Business Days' notice (or without notice where a safety concern exists), up to [AUDITS_PER_YEAR] times per year plus for cause.

5.5 **Performance measures.** Schreiber AI tracks per Integrator: FAT first-pass rate; SAT first-pass rate; NCRs per Unit; Punch List items per Unit; Commissioning Report integrity failures; warranty claims per Unit in year one; End Customer alarm response under Section 9. Two consecutive quarters below [QUALITY_THRESHOLD_DESCRIPTION] (standard: FAT or SAT first-pass rate below 80 %, or any report integrity failure) place Integrator on a corrective action plan; failure to meet the plan within 90 days is a material breach.

5.6 **Recalls and safety notices.** Integrator will pass Schreiber AI safety notices and recall instructions to every affected End Customer within 72 hours and will perform the corrective work at the rates Schreiber AI states in the notice.

## 6. Site Requirements, permits and End Customer contract

6.1 Integrator will have each End Customer complete and sign `docs/SITE_REQUIREMENTS.md` (H3) before Integrator signs an Integrator Order, and will disclose the Risk Register to the End Customer **before pricing**, obtaining the risk acknowledgement (`web/kit/brand.json` rule).

6.2 Integrator's contract with each End Customer will contain, at minimum, provisions corresponding to `docs/contracts/MSA.md` Sections 5 (site readiness), 6 (Change Orders with price and schedule impact and re-baselined dates), 7.5 to 7.8 (Customer-Caused Delay, liquidated damages as sole remedy, delay charges), 8 (two-stage acceptance with deemed acceptance), 10.4 (warranty exclusions), 11 (limitation of liability at least as protective of Schreiber AI as of Integrator), 15 (data ownership with the End Customer; local-first), 16 (Schreiber AI IP) and 20 (permits and AHJ), and the Software Licence pass-through in Section 7. Schreiber AI is named as an intended third-party beneficiary of the IP, licence and data provisions.

6.3 Permits are pulled by the parties in `docs/SITE_REQUIREMENTS.md` Section 10, with Integrator's licensed subcontractors in the place of Schreiber AI's.

## 7. Software Licence pass-through

7.1 Each Unit carries a Software Licence under `docs/contracts/SOFTWARE_LICENSE_BEN_CONTROLS.md`: Type A for Units sold under the Schreiber AI brand; Type C for white-label Units; Type B where Integrator resells Schreiber AI Managed Services. Integrator signs the Software Licence as Licensee and sublicenses to the End Customer under Software Licence Section 2.3(c) and 5.7.

7.2 Integrator will not install unsigned images, will apply security Updates within the windows in Software Licence Section 5.5, and will not mix Units signed with different keys on one gateway or remote endpoint.

7.3 **Remote support endpoint.** Integrator elects per Unit whether Schreiber AI's Z4 endpoint or Integrator's own endpoint ([INTEGRATOR_OWN_Z4]) is used; a Unit never has two. If Integrator runs its own, it meets `docs/CYBERSECURITY.md` Section 6 (outbound-only WireGuard, certificate pinning, named accounts with hardware tokens, session logging visible to the End Customer, key switch honoured).

7.4 **Full source licence.** Available to Integrator under Software Licence Section 9.6 for [FULL_SOURCE_LICENSE_FEE], with Integrator's own signing key provisioned at the factory for its Units and Integrator assuming the update and vulnerability obligations for them.

## 8. Branding

8.1 **White-label rights.** For white-label Units Integrator may apply the Integrator Brand to: the container exterior livery (within the coating specification), the dashboard theme and names via the Brand File, the Turnover Package covers, marketing materials and the product page, and the About screen as Software Licence Section 5.3 requires. Integrator may name the product and tiers with its own names.

8.2 **What stays unchanged.** Safety labels, arc-flash labels, NFPA 704 placards, refrigerant and agent notices, entry procedure placards, equipment nameplates, the UL 508A panel label, the manufacturer identification inside the controls cabinet and in security logs and certificates, and all warning and alarm texts remain as Schreiber AI issues them. Integrator may add its own support contact label beside them.

8.3 **Brand File approval.** Integrator submits its Brand File and livery drawing for Schreiber AI approval before first use; Schreiber AI approves or comments within 10 Business Days and may refuse only for safety, legibility (contrast of alarm colours), legal or quality reasons.

8.4 **Schreiber AI marks.** Where Units are sold under the Schreiber AI brand, Integrator follows `web/kit/brand.json` and `web/kit/BRAND_GUIDE.md`: the SAI monogram in cyan on graphite or graphite on light and never on photographs; "BEN Engine" and the tier names "BEN Micro", "BEN 10", "BEN 20", "BEN 40" written exactly; numbers only from the configuration model or measured evidence; risks shown before prices; prospect samples watermarked "Schreiber AI". Integrator receives a limited, non-exclusive, non-transferable licence to use the marks for this purpose during the term.

8.5 **No invented metrics.** Integrator will not publish PUE, availability, ride-through, capacity or Tier-certification claims that are not produced by the configuration model, a Commissioning Report or a signed SLA, and will not describe any Unit as Uptime Tier certified or IEC 62443 certified.

## 9. Support tiers and End Customer service

9.1 **L1 — Integrator.** First point of contact for End Customers; alarm triage using the Dashboard; dispatch of Integrator technicians and licensed subcontractors; spares kit management; monthly and quarterly maintenance per `docs/MAINTENANCE.md` where Integrator provides the managed service; RMA requests; Turnover Package custody. Target: acknowledge Critical alarms within 15 minutes, on-site within 4 hours where Integrator sells a managed SLA, or as Integrator's own SLA states.

9.2 **L2 — Schreiber AI controls and commissioning engineering.** Remote diagnosis through the remote support path (where enabled) or from Integrator-exported diagnostics; firmware and gateway issues; twin and calibration questions; Commissioning Script failures; Change Order engineering. Response: Critical 1 hour, Major 4 business hours, Minor 2 Business Days, 24x7 for Critical.

9.3 **L3 — Schreiber AI principal engineering.** Design defects, PE and compliance questions, OEM escalations, root-cause analysis, safety notices. Response: 1 Business Day to engage; root-cause report within 10 Business Days.

9.4 **Escalation.** Integrator L1 → Schreiber AI L2 [L2_CONTACT] → L3 [L3_CONTACT] → executive [SCHREIBER_EXEC_SPONSOR]. Integrator's escalation contact: [INTEGRATOR_ESCALATION_CONTACT].

9.5 **Support fee.** L2/L3 support for Integrator is included for Units under Schreiber AI Managed Services; for others it is [L2L3_SUPPORT_FEE_PER_UNIT_MONTH] per Unit per month or at the rates in Annex 2 per case, as Integrator elects per Unit.

## 10. Data ownership and security

10.1 **End Customer owns the data.** All telemetry, alarms, calibration records, Commissioning Reports, video and logs generated by a Unit belong to the End Customer (`docs/CYBERSECURITY.md` Section 4). Neither Integrator nor Schreiber AI acquires ownership. Integrator's contract with the End Customer will say so and will not grant Integrator rights beyond those needed to provide the agreed services.

10.2 **Access.** Integrator accesses Unit data only to provide services the End Customer has contracted, under named accounts, with sessions logged in the Dashboard. Integrator will not aggregate End Customer data across customers except under an opt-in equivalent to Software Licence Section 4.3, and will share anonymised fleet statistics with Schreiber AI where the End Customer has opted in.

10.3 **Local-first.** Integrator will not introduce a cloud dependency into any Unit's operation and will keep the shipped firewall rules and zone model.

10.4 **Credential handover.** Integrator follows `docs/TURNOVER.md` Section 3 at every Turnover: new credentials, sealed envelope and encrypted file, End Customer changes passwords in the meeting, Integrator and Schreiber AI destroy their copies, record signed.

10.5 **Incidents.** Integrator notifies Schreiber AI and the affected End Customer within 72 hours of confirming a security incident or exploitable vulnerability affecting a Unit; Schreiber AI does the same toward Integrator.

## 11. Insurance and licences

11.1 Integrator carries, and requires its subcontractors to carry: commercial general liability [INTEGRATOR_INSURANCE_CGL] per occurrence including products/completed operations; professional liability [INTEGRATOR_INSURANCE_PROFESSIONAL] (Install Partner, Licensed Builder); cyber liability [INTEGRATOR_INSURANCE_CYBER] where it provides managed services or runs a remote endpoint; automobile [INTEGRATOR_INSURANCE_AUTO]; workers' compensation statutory; builder's risk or installation floater for Units in its custody; and names Schreiber AI as additional insured with waiver of subrogation. Certificates before the first Unit and annually.

11.2 Integrator holds and keeps current every contractor licence the Territory requires for the work it performs, and uses only licensed trades for Section 4.3 work.

## 12. Warranty flow

12.1 **Schreiber AI to Integrator.** Schreiber AI gives Integrator the warranties in `docs/contracts/WARRANTY_TERMS.md` for the scope Schreiber AI performs: for Resale, the whole Unit; for Install Partner, the Unit as shipped from FAT plus Schreiber AI's SAT participation; for Licensed Builder, the engineering release, the Controls Kit (BEN Nodes 24 months, gateway 12 months, RMA procedure) and BEN Controls under the Software Licence.

12.2 **Integrator to End Customer.** Integrator gives the End Customer at least the warranty in `docs/contracts/WARRANTY_TERMS.md` for the whole Unit, including Integrator's own site works and, for Licensed Builder, its own build. Integrator may offer more; the excess is Integrator's.

12.3 **Claims.** The End Customer claims to Integrator (L1). Integrator triages, performs or procures the repair, and claims back-to-back to Schreiber AI within 10 Business Days for defects in Schreiber AI's scope, with the incident report and gateway data. Schreiber AI reimburses parts and, for Schreiber AI-scope defects, Integrator labour at [WARRANTY_LABOUR_REIMBURSEMENT_RATE] per hour up to the hours Schreiber AI approves. OEM warranties are registered in the End Customer's name and administered by Integrator during year one, with Schreiber AI's help.

12.4 **Exclusions.** `docs/contracts/WARRANTY_TERMS.md` Sections 4 and 5 apply. Integrator-caused defects (STE steps not followed, QC forms incomplete, uncertified trades, unapproved parts, unsigned firmware, moving a Unit without the relocation procedure) are Integrator's responsibility toward the End Customer and toward Schreiber AI.

## 13. Delivery, delay and liquidated damages (back-to-back)

13.1 **Schreiber AI late to Integrator.** For Resale and Install Partner Units, if FAT is later than the baseline FAT date in the Integrator Order (as re-baselined) plus [LD_GRACE_DAYS] days for a cause within Schreiber AI's control, Schreiber AI credits Integrator liquidated damages of [LD_RATE_PCT_PER_WEEK] % of the Unit price per full week, capped at [LD_CAP_PCT] %, as sole remedy for delay (`docs/contracts/MSA.md` Section 7.7). For Licensed Builder Units, the same applies to late delivery of the engineering release package and the Controls Kit, on the engineering fee and Controls Kit price respectively.

13.2 **Integrator's End Customer contract.** Integrator will not promise an End Customer delay liquidated damages at a rate or cap higher than Section 13.1 for Schreiber AI's scope, or a FAT or SAT date earlier than the Integrator Order baseline, without bearing the difference itself. Integrator will include in its End Customer contract the Customer-Caused Delay, storage, crane re-mobilisation, standby and re-commissioning provisions of `docs/contracts/MSA.md` Sections 7.5 and 7.8 so that End Customer-caused delays do not fall on Integrator or Schreiber AI.

13.3 **Integrator late to Schreiber AI.** Where Integrator owns site works, H16, permits or End Customer approvals and they are late, `docs/contracts/MSA.md` Sections 7.5, 7.8 and 9.3 apply between Schreiber AI and Integrator: Schreiber AI's LD exposure is suspended, milestones are invoiced on baseline dates, and Integrator pays storage [STORAGE_FEE_PER_DAY] per day after [FREE_STORAGE_DAYS] free days, crane re-mobilisation [CRANE_REMOB_FEE], standby [STANDBY_RATE_PER_DAY] and re-commissioning [RECOMMISSIONING_FEE] as incurred.

13.4 **Licensed Builder schedule.** For Units Integrator builds, Integrator owes the End Customer the delivery schedule and bears its own delay. Schreiber AI's responsibility is limited to Section 13.1.

13.5 **Allocation and tariffs.** `docs/contracts/MSA.md` Sections 6.6 and 17.2 apply; Schreiber AI passes on allocation notices from suppliers within 10 Business Days and uses approved alternates.

## 14. Marketing

14.1 Integrator may use Schreiber AI's marketing kit (`web/kit/MARKETING_KIT.md`, one-pagers, copy blocks, renders, dashboard screenshots) for the Territory, co-branded or under the Integrator Brand as Section 8 allows.

14.2 Integrator submits new marketing materials, case studies, press releases and public claims about BEN Engine to Schreiber AI for approval; Schreiber AI responds within 10 Business Days and may refuse only for inaccuracy (Section 8.5), brand rule breach, or legal risk. Approved templates may be reused without re-approval.

14.3 Each Party may list the other as a partner. End Customer names and Sites are published only with the End Customer's written consent.

14.4 Marketing development funds: [MDF_PCT] % of Integrator's prior-quarter Unit purchases, claimable against approved activities within the following two quarters.

## 15. Non-solicitation and non-circumvention

15.1 During the term and for [NON_SOLICIT_MONTHS] months after, neither Party will solicit for employment the other's employees who were involved in this Agreement, except through general advertising not targeted at them.

15.2 During the term and for [NON_CIRCUMVENT_MONTHS] months after, Schreiber AI will not sell directly to an End Customer whose opportunity Integrator registered and actively pursued, except where the End Customer approaches Schreiber AI after terminating with Integrator or where Integrator's registration has lapsed; and Integrator will not engage a Schreiber AI Contract Manufacturer or supplier to build units competing with BEN Engine using Schreiber AI Confidential Information.

## 16. Intellectual property and confidentiality

16.1 Schreiber AI owns BEN Engine and BEN Controls as `docs/contracts/MSA.md` Section 16.1 describes. Integrator receives only the licences in this Agreement and the Software Licence. Drawings, STE instructions, QC forms, the configuration model and Controls Kits may be used only for Units ordered under this Agreement. Integrator will not build, or help anyone build, a unit from Schreiber AI drawings or instructions other than under an Integrator Order.

16.2 Improvements Integrator suggests to the drawings, instructions, firmware or process are licensed to Schreiber AI royalty-free and perpetually; Integrator keeps ownership of its own independently developed tools that do not incorporate Schreiber AI Confidential Information.

16.3 `docs/contracts/MSA.md` Section 14 (Confidentiality) applies between the Parties. `docs/contracts/NDA_MUTUAL.md` is superseded for information disclosed after the Effective Date.

## 17. Term and termination

17.1 **Term.** [TERM_YEARS] years from the Effective Date, renewing for one-year periods unless either Party gives 120 days' notice.

17.2 **Termination for breach.** Either Party may terminate for material breach uncured 30 days after notice (10 days for non-payment; immediately for a safety breach such as skipping a hold point, using unlicensed trades for Section 4.3 work, or installing unsigned firmware).

17.3 **Termination for convenience.** Either Party on 180 days' notice after the first contract year.

17.4 **Effect.** Integrator Orders signed before notice are completed under this Agreement unless the terminating Party elects otherwise for breach. Integrator stops using the Schreiber AI marks and the Integrator Brand on new Units; deployed Units keep their Software Licences (Type C survives for deployed Units, Software Licence Section 13.1) and End Customers keep operating. Integrator hands over to Schreiber AI, at Schreiber AI's request, the support of End Customers who elect to move, with Turnover Packages, records and credentials under the handover procedure, for the transition fee in Annex 2. Sections 7.2, 10, 12, 15, 16, 17.4, 18 and 19 survive.

## 18. Liability and indemnity

18.1 `docs/contracts/MSA.md` Sections 11 (cap: [LIABILITY_CAP_MULTIPLIER] times the fees under the affected Integrator Order; carve-outs as stated) and 12 (indemnities) apply between the Parties, with Integrator in the place of Customer, and with these additions: Integrator indemnifies Schreiber AI against End Customer and third-party claims arising from Integrator's installation, build, site works, support, marketing claims and use of the Integrator Brand; Schreiber AI indemnifies Integrator against third-party IP claims about BEN Controls and Schreiber AI-designed Deliverables as MSA Section 12.1(b).

## 19. General

19.1 Governing law: State of [GOVERNING_STATE]. Disputes: `docs/contracts/MSA.md` Section 19 (escalation, technical expert, mediation, arbitration at [ARBITRATION_BODY], [ARBITRATION_CITY]).

19.2 Notices: Schreiber AI [SCHREIBER_NOTICE_NAME], [SCHREIBER_NOTICE_EMAIL]; Integrator [INTEGRATOR_NOTICE_NAME], [INTEGRATOR_NOTICE_EMAIL].

19.3 Assignment only with consent, except to a successor; compliance with export control and anti-corruption laws; independent contractors; entire agreement; amendment in writing; severability; counterparts; electronic signature.

## Annex 1 — Changes to the SOW template for Integrator Orders

| SOW section | Change |
| --- | --- |
| Header | "Customer" reads "Integrator"; End Customer and Site are identified for delivery and licence purposes |
| 1 Delivery model | Adds the Integrator Delivery Model (Resale / Install Partner / Licensed Builder) and brand mode |
| 3.7 Site works | Rows owned by Integrator are marked "Integrator"; Schreiber AI's scope ends at FAT for Install Partner |
| 5 Schedule | Adds Integrator-owned dates (H16, permits, utility ready) and the Schreiber AI witness dates under Section 5.2 of this Agreement |
| 7 Price | Uses list price less the discount tier; for Licensed Builder, lists engineering fee, Controls Kit, royalty and licence |
| 7.3 / 7.4 | LD and delay charges per Section 13 of this Agreement |
| 8 Acceptance | FAT and SAT Certificates signed by Schreiber AI, Integrator and End Customer; Schreiber AI signs SAT for every Unit |
| 10 Data and licence | Licence Type C or A; End Customer as data owner; remote endpoint election |

## Annex 2 — Rates and fees

| Item | Amount |
| --- | --- |
| Training per seat (after free seats) | [TRAINING_FEE_PER_SEAT] |
| Schreiber AI witness attendance (per day plus travel at cost) | [WITNESS_DAY_RATE] |
| Schreiber AI FAT / SAT attendance (per day plus travel) | [COMMISSIONING_DAY_RATE] |
| L2/L3 per-case support (Units not on monthly support fee) | [L2L3_CASE_RATE] per hour |
| Warranty labour reimbursement to Integrator | [WARRANTY_LABOUR_REIMBURSEMENT_RATE] per hour |
| Transition fee on termination (per End Customer handed over) | [TRANSITION_FEE_PER_CUSTOMER] |
| Controls Kit price by tier | [CONTROLS_KIT_PRICE_BY_TIER] |
| Engineering release fee per Unit (Licensed Builder) | [LICENSED_BUILDER_ENGINEERING_FEE] |

## Signatures

| | Schreiber AI | Integrator |
| --- | --- | --- |
| Entity | [SCHREIBER_ENTITY_NAME] | [INTEGRATOR_NAME] |
| Signature | ______________________ | ______________________ |
| Name | [SCHREIBER_SIGNATORY_NAME] | [INTEGRATOR_SIGNATORY_NAME] |
| Title | [SCHREIBER_SIGNATORY_TITLE] | [INTEGRATOR_SIGNATORY_TITLE] |
| Date | [SIGNATURE_DATE_SCHREIBER] | [SIGNATURE_DATE_INTEGRATOR] |

---
Schreiber AI · BEN Engine (Business Edge Node) · Ben@SchreiberAI.com · Template maintained at `docs/contracts/INTEGRATOR_AGREEMENT.md` · TEMPLATE — not legal advice — have counsel review before use.
