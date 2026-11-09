# BEN Engine Rev 2 revamp program — USD 5 M, 18 months

**Sponsor:** Ben Schreiber, Schreiber AI · **Budget:** USD 5,000,000 · **Duration:** 18 months from funding, six quarterly gates · **Decision basis:** `docs/REV2_DECISION.md` §3 · **Issued:** 2026-11-09 (Rev 2) · **Supersedes for budgeting:** `RD_PROGRAM_2027.md` and `FORWARD_800V_LIQUID_PROGRAM.md` (both kept, with a "Superseded" header, as history and as workstream detail).

Operator's words (2026-11-09): "the base is good, we just need a once-over … the budget to do the once-over is a 5 million revamp … especially the liquid cooling, and I want to make sure we are as dense as we can be. Rev 2 of the Schreiber AI BEN Engine has the cutting edge and density people are looking for, along with the very low side for tiny business, where we do mini racks."

## 1. What is already done, and what the money buys

**Done in the repository now, at no cost to this budget.** The engineering, brand application and documentation revision is Rev 2 itself: the lineup with BEN 1, BEN 300 and BEN 700 (planned as BEN 1000, renamed by fit, `docs/REV2_DECISION.md` §2a) in the configuration model, liquid-first defaults on the dense tiers, density metrics, versioned Rev 2 drawings, BOMs and proposals, brand package v2 applied to the website, dashboard, decks, contracts and drawing title blocks, the revision policy, and this document set. What changed is listed in `docs/rev2/RELEASE_NOTES.md`.

**What a repository cannot do, and the USD 5 M buys.** Hardware that exists, measurements on that hardware, listings from third parties, printed and applied brand pieces, and the people to run it:

1. **BEN 1 lighthouse**: ten mini racks built in-house by Schreiber AI and placed with pilot customers (tiny businesses).
2. **BEN 300 lighthouse**: one 20 ft liquid-first module built at a contract manufacturer, with FAT, SAT and a 30-day burn-in.
3. **Liquid W45 test cell**, with the **800 VDC cell as a gated option** (scoped down from the forward program: the liquid cell is built first; the DC cell is released only if its gate is met).
4. **BEN Pod v1 production and FCC**.
5. **UL 508A listing of the BEN Controller panels** (Pro and Lite).
6. **Brand production**: data plates, nameplates, livery vinyl, print collateral and the brand package's eight touchpoints applied to BEN Engine.
7. **Team, listings and contingency.**

What the money does **not** buy: a BEN 700 build (BEN 700 stays engineered and quotable; the first unit is customer-funded after the BEN 300 burn-in proves the liquid-first design), a BEN 2000 build, a greenfield factory, immersion or two-phase hardware, or any number on a product page before it is measured.

## 2. Allocation

Every amount is a ceiling. A line is released only when its gate passes; money not released at a gate stays in the program and returns to contingency. "Basis" says where the number comes from; unit costs are from the Rev 2 BOMs written by the lineup work (`docs/rev2/BOM.md`, filled 2026-11-09), and the line is re-baselined at the first gate where it is spent.

| # | Line | USD | Basis | Gate that releases it | Measured deliverable |
| --- | --- | --- | --- | --- | --- |
| 1 | **BEN 1 lighthouse** — 10 units built in-house (mix of rack10 and cab12), light assembly bench with ESD control, burn-in shelf, sound meter, power analyser, field setup and handover at 10 pilot sites | 300,000 | 10 × unit BOM (`docs/rev2/BOM-ben1*.md`, rack10 USD 14,217 and cab12 USD 42,080 with reference compute, USD 4,353 and USD 9,144 without; at reference compute ten units exceed the line, so the line assumes pilot customers bring or pay for their own compute — open question Q-P3 in `docs/rev2/OPEN_QUESTIONS.md`) + bench and test equipment about USD 60 k + setup travel about USD 40 k | **G0** (bench, first 2 units); **G1** (units 3–10) | Ten units pass BEN 1 acceptance (E21–E24, `docs/TEST_GUIDE.md`) and run 90 days at pilot sites; noise at 1 m, heat to room, UPS runtime and uptime reported per unit |
| 2 | **BEN 300 lighthouse** at a contract manufacturer — infrastructure (module, 480 V power train, UPS and battery, row CDUs N+1, dry coolers, controls kit, fire), CM labour, liquid load banks, FAT, transport, SAT on a pad, 30-day burn-in energy | 1,450,000 | Infrastructure cost from `docs/rev2/BOM-ben300.md` (USD 925,804 excluding compute, of which 24.6 % confirmed listings and the rest estimates; no customer compute: liquid load banks stand in) + CM labour per `docs/MANUFACTURING_STRATEGY.md` §7 + burn-in energy (300 kW × 720 h ≈ 216 MWh) | **G2** (engineering release Rev 2.A IFC, CM build order); **G3** (FAT) | FAT and SAT with the commissioning script; 30 days at ≥ 80 % load with zero critical alarms; measured kW per m², PUE, loop ΔT, CDU failover (E18) and leak-to-isolation (E19) published in `docs/VALIDATION.md`. The unit is kept as a demonstrator or sold to the first BEN 300 customer after burn-in |
| 3 | **Liquid W45 test cell** — 300 kW-class CDU with N+1 pumps, manifolds with OCP UQD v2 connectors, liquid test load, dry cooler, flow and temperature instrumentation, leak-injection rig, data acquisition | 400,000 | Scoped down from `FORWARD_800V_LIQUID_PROGRAM.md` §3 (test-cell line USD 1.2 M covered DC and liquid); vendor classes in `docs/research/STATE_OF_THE_ART_2026.md` §2.2 | **G0** (long-lead orders) | Loop at W45 with measured ΔT and flow against the vendor table (177 LPM per GB300-class rack at 45 °C); leak-to-isolation ≤ 15 s (E19); pump failover (E18); heat balance within 5 % (E20). These numbers de-risk BEN 300 before its build order |
| 4 | **800 VDC test cell (gated option)** — AC/DC front end about 150 kW, DC busway section, DC breakers, insulation monitoring, DC load bank, arc-rated enclosure | 350,000 | Remainder of the forward program's DC bench, cut to one bus section | **G3**, only if (a) an NRTL has accepted a written field-evaluation path, (b) a front-end partner supplies hardware under NDA, and (c) the liquid cell has met its G2 numbers. Otherwise the line returns to contingency | E17 ground-fault injection on both poles; measured efficiency against the AC baseline on the same load bank; `dc800` stays a study option in the selector until this data exists |
| 5 | **BEN Pod v1 production and FCC** — PCBA runs, enclosures, provisioning cell with HSM, FCC Part 15 Subpart B SDoC testing (radio covered by the MGM240P modular grant), firmware on target | 250,000 | `RD_PROGRAM_2027.md` WS3 core (USD 650 k) less the UL 508A share and the PLC work already done in the repository | **G1** (first article, FCC pre-scan); **G3** (production run) | Pod v1 passes FCC Part 15 B; production yield report; 37 host tests ported and passing on target; Pods shipped in BEN 1 (one per unit) and BEN 300 |
| 6 | **UL 508A listing of the BEN Controller panels** (Controls Pro and Controls Lite) through the panel partner's file; labels and listing records | 120,000 | NRTL fees, partner engineering, two panel builds for evaluation | **G1** (submission) | Listing mark on both panel types; file number on every panel label checked at FAT (BEN 300 lighthouse carries the first listed Pro panel) |
| 7 | **Brand production** — data plate band and nameplates (UL 969-rated labels, PMS 2767 C proofs), livery vinyl for module sides and doors, print collateral, and the brand package's eight touchpoints for BEN Engine: business card, one-page sales sheet, proposal title and scope pages, case-study and LinkedIn set, video lower-third and end card, event table throw, vehicle door decal, welcome kit with thank-you and review card | 150,000 | Brand package v2 (`brand/v2/source/`) touchpoint list; print and vinyl quotes once the artwork is final | **G0** (proofs and touchpoints); **G3** (plates and livery on the BEN 300 lighthouse) | Approved colour proofs; data plates on all 10 BEN 1 units and the BEN 300 lighthouse; QR scans per touchpoint tracked from the landing page |
| 8 | **Team** (18 months, loaded): thermal/fluids engineer, power and controls engineer, test and commissioning engineer, BEN 1 assembly and support technician, software engineer (twin, BEN Care), half-time compliance/quality lead, half-time sourcing | 1,350,000 | 6 FTE × 18 months at about USD 12.5 k per FTE-month loaded; program lead (Ben Schreiber) not charged | **G0** (hires) then each gate for the next two quarters | Staffed plan; every gate report signed by the named engineer |
| 9 | **Listings and compliance (other)** — NRTL field evaluation of the BEN 300 lighthouse, arc-flash and coordination study (incl. the 1,200 A frame on the BEN 700 drawings), PE stamps in three states, AHJ pre-submissions, insurer review, OCP membership | 230,000 | `RD_PROGRAM_2027.md` WS5 core (USD 300 k) less the UL 508A line above | **G1** (AHJ pre-meetings), **G3** (field evaluation) | Field-evaluation label on the BEN 300 lighthouse; PE-signed arc-flash study and labels; AHJ minutes on file |
| 10 | **Contingency** (8 %) | 400,000 | Released by the sponsor at a gate, against a written variance | Any gate | Variance log in the gate report |
| | **Total** | **5,000,000** | | | |

Cash timing (ceiling): about 35 % in quarters 1–2 (team, liquid cell, BEN 1 build, brand proofs), 45 % in quarters 3–4 (BEN 300 build and FAT, Pod production, listings), 20 % in quarters 5–6 (SAT, burn-in, close-out).

## 3. Quarterly gates (18 months)

| Quarter | Gate at quarter end | Work in the quarter | Evidence required to release the next tranche |
| --- | --- | --- | --- |
| Q1 (months 1–3) | **G0 → G1** | Funding and hires; BEN 1 bench set up (ESD, burn-in shelf); first two BEN 1 units built and burned in; liquid-cell long-lead orders; contract manufacturer RFI for BEN 300; brand proofs and the eight touchpoints; Pod v1 first article and FCC pre-scan; UL 508A submission; AHJ pre-meetings | BEN 1 first articles pass E21–E24; CM shortlist signed; Pod pre-scan report; UL 508A application number |
| Q2 (months 4–6) | **G2** | BEN 1 units 3–10 built and handed over at pilot sites (2–3 weeks each, `docs/PROCESS_FLOW.md` §6); liquid cell running at W45; BEN 300 engineering release Rev 2.A IFC with a named checker; CM qualification audit | Liquid-cell data: E18, E19 ≤ 15 s, E20 within 5 %; ten BEN 1 units in service; BEN 300 IFC drawings and CM build order |
| Q3 (months 7–9) | **G3** | BEN 300 build at the CM (witness points per `PROCESS_FLOW.md`); Pod v1 production run and FCC SDoC; DC-cell decision; brand plates and livery ordered for BEN 300 | Decision memo on the 800 VDC option (release or return to contingency); Pod yield report; CM hold points signed |
| Q4 (months 10–12) | **G4** | BEN 300 FAT at the CM with the commissioning script and liquid load banks; UL 508A listing received; NRTL field-evaluation visit booked; BEN 1 90-day pilot review | FAT report with data hash; listing mark; BEN 1 pilot report (noise, heat to room, runtime, support calls, uptime) |
| Q5 (months 13–15) | **G5** | BEN 300 shipped, set on a pad, SAT; 30-day burn-in at ≥ 80 % load; field evaluation; DC cell E17 (if released) | SAT report; burn-in log with zero critical alarms; field-evaluation label |
| Q6 (months 16–18) | **G6 close-out** | Measured numbers replace estimates in the selector and in `docs/DENSITY.md`; twin refitted from BEN 300 data; BEN 700 go/no-go for a customer-funded first unit; Rev 2 drawing set Rev 2.B issued from lighthouse findings | Close-out report; `docs/VALIDATION.md` updated with hardware rows; internal audit against `docs/audit/AUDIT_CHECKLIST.md` with zero major nonconformities |

## 4. Success metrics (measured, not claimed)

| Metric | Target | How measured |
| --- | --- | --- |
| BEN 1 in the field | 10 units in service; noise and heat-to-room inside the published limits at every site; zero unplanned outages caused by the BEN 1 infrastructure (power, UPS, airflow) over 90 days | E21–E24 at handover; BEN Care records |
| BEN 300 lighthouse | FAT and SAT passed; 30 days at ≥ 80 % load, zero critical alarms; measured kW per m² of module footprint reported against the design value 20.31 kW per m² (300 kW on 14.77 m²) | Commissioning script; `docs/DENSITY.md` |
| Liquid loop | W45 supply held; leak-to-isolation ≤ 15 s on every rack; CDU pump failover with no throttle flag | E18–E20 on the cell and on BEN 300 |
| Listings | BEN Controller Pro and Lite UL 508A listed; Pod v1 FCC Part 15 B; BEN 300 field-evaluation label | Listing letters in the turnover package |
| Brand | Every unit shipped in the program carries the Rev 2 data plate band; eight touchpoints printed and tracked | Shipping photos; landing-page source tags |
| Budget | Within USD 5 M with the DC option either executed or returned | Gate reports |

## 5. Where the detail lives

| Workstream | Detail (kept, superseded for budgeting) |
| --- | --- |
| Liquid cell, DC cell, standards for DC | `FORWARD_800V_LIQUID_PROGRAM.md` (workstreams A–D; its BEN 150 forward prototype is replaced here by the BEN 300 lighthouse) |
| Controls productisation, BEN Care, manufacturing qualification | `RD_PROGRAM_2027.md` (workstreams 3–6) |
| BEN 1 build, handover and support | `docs/MANUFACTURING_STRATEGY.md` §12, `docs/PROCESS_FLOW.md` §6, `docs/MAINTENANCE.md` §10 |
| Risks of the new tiers | `docs/RISK_REGISTER.md` R41–R52 |

## 6. Decision asked of the sponsor

Open points that follow from this allocation (approval, BEN 300 lighthouse sell-or-keep, BEN 1 pilot customers, BEN 700 customer-funded first unit, 8 % contingency) are listed with recommended defaults in `docs/rev2/OPEN_QUESTIONS.md`.

Approve the allocation and release G0: the hires, the liquid-cell long-lead orders, the BEN 1 bench and the brand proofs. Everything after G0 is released by evidence at the gate.
