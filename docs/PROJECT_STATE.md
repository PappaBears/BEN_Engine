# PROJECT_STATE — BEN Engine

**Brief:** `docs/BRIEF.md` (rewritten from the operator's request; original in `docs/ORIGINAL_REQUEST.md`).
**Mode:** Product. **Branch:** `main`. **Repo:** github.com/PappaBears/BEN_Engine.

## Agreed scope
The full acceptance list in `docs/BRIEF.md` §5 (22 deliverables after the mid-session additions: proposal generator, two-sided paperwork, third-party manufacturing strategy, deal package assembler, SQAM). Nothing has been dropped.

## Current reality (updated at milestones)
| Milestone | Concrete result | Proof | Status |
| --- | --- | --- | --- |
| Idea understood | Brief, acceptance list, gaps added | `docs/BRIEF.md` | done |
| Design validated | Config model + twin run for 4 tiers with faults | `python -m ben_engine.config`, twin smoke run (see VALIDATION) | done |
| First workflow | Config → twin → state → alarms | twin smoke run | done |
| Full behaviour | CFD, calibration, sweeps, commissioning, dashboard, firmware, drawings, BOM, docs, web, VC, proposal generator, deal packages, SQAM, contracts, manufacturing strategy | pytest 113 passed; firmware 37 passed; generators run | done |
| Quality confirmed | pytest + Playwright e2e + simulated end-to-end | `docs/VALIDATION.md` | done (hardware checks remain unverified) |
| Handoff complete | README, VALIDATION, manifest, push | README.md, docs/launch-manifest.json, git log | done |

## Constraints
No hardware here; EFR32 / Gecko SDK toolchain not available (network policy); vendor sites not reachable by curl, only through web search/fetch. No money spent; no emails sent (drafts only).

## Latest checkpoint
`main` on github.com/PappaBears/BEN_Engine; see `git log`. Restore: clone the tag/commit and run the Quickstart commands in README.md.

## Blockers
None blocking. Items that stay unverified without hardware are listed in `docs/VALIDATION.md`.

## Next exact action
Operator decisions: (1) forward the 16 RFQ Gmail drafts, (2) choose the first contract manufacturer from `docs/MANUFACTURING_STRATEGY.md` §3.1 and send the RFI, (3) counsel review of `docs/contracts/`, (4) fund the two lighthouse units. Engineering next: controls platform is now PLCnext + OnLogic Karbon 400 + BEN Pods (MGM240P) with a Revolution Pi Lite tier (`docs/CONTROLS_HARDWARE_DECISION.md`, 2026-11-08): forward RFQs 13, 14, 17, 18; build the first Pod PCBAs and compile the firmware on an xG24 kit; fix the HAL against the real Gecko SDK / OpenThread APIs; stand up the provisioning cell.
