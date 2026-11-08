# PROJECT_STATE — BEN Engine

**Brief:** `docs/BRIEF.md` (rewritten from the operator's request; original in `docs/ORIGINAL_REQUEST.md`).
**Mode:** Product. **Branch:** `main`. **Repo:** github.com/PappaBears/BEN_Engine.

## Agreed scope
The full acceptance list in `docs/BRIEF.md` §5 (18 deliverables). Nothing has been dropped.

## Current reality (updated at milestones)
| Milestone | Concrete result | Proof | Status |
| --- | --- | --- | --- |
| Idea understood | Brief, acceptance list, gaps added | `docs/BRIEF.md` | done |
| Design validated | Config model + twin run for 4 tiers with faults | `python -m ben_engine.config`, twin smoke run (see VALIDATION) | done |
| First workflow | Config → twin → state → alarms | twin smoke run | done |
| Full behaviour | CFD, calibration, sweeps, commissioning, dashboard, firmware, drawings, BOM, docs, web, VC | in progress (parallel build) | in progress |
| Quality confirmed | pytest + Playwright e2e + simulated end-to-end | pending | pending |
| Handoff complete | README, VALIDATION, manifest, push | pending | pending |

## Constraints
No hardware here; ESP32 toolchain download blocked (network policy); vendor sites not reachable by curl, only through web search/fetch. No money spent; no emails sent (drafts only).

## Latest checkpoint
None yet (first commit pending).

## Blockers
None blocking. Items that stay unverified without hardware are listed in `docs/VALIDATION.md`.

## Next exact action
Integrate agent outputs, run full test suite, inspect dashboard screenshots, write VALIDATION, commit and push.
