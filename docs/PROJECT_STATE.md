# PROJECT_STATE — BEN Engine

**Brief:** `docs/BRIEF.md` (rewritten from the operator's request; original in `docs/ORIGINAL_REQUEST.md`).
**Mode:** Product. **Branch:** `main`. **Repo:** github.com/PappaBears/BEN_Engine.

## Agreed scope
The full acceptance list in `docs/BRIEF.md` §5 (24 deliverables after the mid-session additions: proposal generator, two-sided paperwork, third-party manufacturing strategy, deal package assembler, SQAM, BEN 2000 and enclosure hardening). Nothing has been dropped.

## Current reality (updated at milestones)
| Milestone | Concrete result | Proof | Status |
| --- | --- | --- | --- |
| Idea understood | Brief, acceptance list, gaps added | `docs/BRIEF.md` | done |
| Design validated | Config model + twin run for 5 tiers (BEN 5/30/150/500 and the 2 MW BEN 2000) with faults; hardening H1–H3 in the config | `python -m ben_engine.config`, twin smoke run (see VALIDATION) | done |
| First workflow | Config → twin → state → alarms | twin smoke run | done |
| Full behaviour | CFD, calibration, sweeps, commissioning, dashboard, firmware, drawings, BOM, docs, web, VC, proposal generator, deal packages, SQAM, contracts, manufacturing strategy | pytest 198 passed at Generation 2; **263 passed** at Rev 2 (2026-11-09); firmware 37 passed; generators run | done |
| Quality confirmed | pytest + Playwright e2e + simulated end-to-end | `docs/VALIDATION.md` | done (hardware checks remain unverified) |
| Handoff complete | README, VALIDATION, manifest, push | README.md, docs/launch-manifest.json, git log | done |
| Generation-2 refactor (2026-11-08) | Power-based names (BEN 5/30/150/500), BEN 2000 prefabricated hall, NEMA 4X / IP66 baseline with H1/H2/H3 hardening, across config, docs, contracts, decks, product page | `docs/TIER_AND_ENCLOSURE_DECISION.md`, `python -m ben_engine.config --tier ben2000`, `docs/VALIDATION.md` | done: drawings (A-000 + per-module sheets), BOM-ben2000, twin/CFD/sweeps/commissioning run for the hall (VALIDATION §4a) |

## Constraints
No hardware here; EFR32 / Gecko SDK toolchain not available (network policy); vendor sites not reachable by curl, only through web search/fetch. No money spent; no emails sent (drafts only).

## Generation 2 (2026-11-08)
Tiers renamed by IT power (BEN 5/30/150/500) with aliases; BEN 2000 prefabricated 2 MW center added as the capability example (positioning per D36: the all-in-one boxes BEN 5–500 are the core product and lead every document; BEN 2000 is kept fully engineered as the upsell path); enclosures IP66 with hardening H1–H3; controls on an industrial platform (BEN Controls Lite/Pro, BEN Pod on BEN Mesh). 185 Python tests, 25/25 browser checks, 21 RFQ drafts queued.

## Audit (2026-11-08)
Independent internal audit: 22 findings (4 major). All corrective actions worked; re-audit 17 PASS / 3 WARN / 0 FAIL. Drawing set Rev B checked by Ben Schreiber and issued for construction on 2026-11-08; Rev C (design change DC-001, BEN 5 cabinet AC to R-513A 5.5 kW) issued for review the same day and awaits the checker's signature. MSA 15.5 and the software licence now state SAT deliverables versus security-roadmap items exactly as the cybersecurity status table does. Open with suppliers: Rittal part number and price for the R-513A variant (RFQ 03). Paperwork ready set in `docs/contracts/ready/`.

## Forward architecture (2026-11-09)
800 VDC power (both OCP conventions) and high-density W45 liquid cooling are selectable options from BEN 150 up, with sizing, twin, sweeps, commissioning steps, BOM, study drawings, compliance and risk rows; existing presets unchanged. Research with 235 sources in `docs/research/`; R&D Program 2027–2028 (USD 5 M core / 10 M full) in `docs/programs/RD_PROGRAM_2027.md` with the 800 VDC and liquid workstream detailed in `FORWARD_800V_LIQUID_PROGRAM.md`. All forward efficiencies and prices are vendor claims or estimates until the test cell measures them.

## Rev 2 (2026-11-09)
Product revision Rev 2 (`docs/REV2_DECISION.md`, `docs/rev2/RELEASE_NOTES.md`): brand package v2 applied; BEN 1 mini racks (rack10 0.6 kW, cab12 1.5 kW); dense liquid-first BEN 300 (2 × 150 kW) and BEN 700 (5 × 140 kW; planned as BEN 1000, renamed by fit, §2a); USD 5 M revamp program. Python suite **263 tests, 263 passed**; Rev 1 frozen by a fixture test of 267 configurations; Rev 2 checks in `docs/VALIDATION.md` §9. Open operator decisions: `docs/rev2/OPEN_QUESTIONS.md`.

## Latest checkpoint
`main` on github.com/PappaBears/BEN_Engine; see `git log`. Restore: clone the tag/commit and run the Quickstart commands in README.md.

## Blockers
None blocking. Items that stay unverified without hardware are listed in `docs/VALIDATION.md`.

## Next exact action
Operator decisions: (1) forward the 21 RFQ Gmail drafts, (2) choose the first contract manufacturer from `docs/MANUFACTURING_STRATEGY.md` §3.1 and send the RFI, (3) counsel review of `docs/contracts/`, (4) fund the two lighthouse units, (5) pick the reference site and utility for the first BEN 2000 engineering release. Engineering next: controls platform is now PLCnext + OnLogic Karbon 400 + BEN Pods (MGM240P) with a Revolution Pi Lite tier (`docs/CONTROLS_HARDWARE_DECISION.md`, 2026-11-08): forward RFQs 13, 14, 17, 18; build the first Pod PCBAs and compile the firmware on an xG24 kit; fix the HAL against the real Gecko SDK / OpenThread APIs; stand up the provisioning cell.
