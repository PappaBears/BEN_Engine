# CAPA log — corrective and preventive actions from the 2026-11-08 internal audit

Status values: **closed** (action done and evidence recorded), **in progress**, **accepted** (observation acknowledged, no action), **deferred** (roadmap).

| Finding | Class | Action | Evidence | Status |
| --- | --- | --- | --- | --- |
| F-01 build contract fails from a clean clone | Major | Commands now carry `env PYTHONPATH=software`; three checks added (sim-e2e-pytest, links, audit-mechanical); latest report stored in `docs/audit/evidence/build-report.json` by `scripts/store_evidence.py` | `docs/build-contract.json`, `docs/audit/evidence/` | closed |
| F-02 drawing set not under revision control | Major | `design/REVISION.json` drives every generator; set re-issued as Rev B 2026-11-08 with status "ISSUED FOR REVIEW" until a named checker signs; wiring files renamed to generation-2 keys; SQAM, QC forms, assembly and SOW sample cite the same revision | `design/REVISION.json`, `design/drawings/README.md` | in progress |
| F-03 NEC 645 cited as basis of life-safety circuit; 2.55 m height | Major | CONTROLS_SPEC §1 now cites NFPA 75 / 72 / 2001 and states 645 not invoked; life-safety sheet subtitle and COMPLIANCE height corrected | `design/specs/CONTROLS_SPEC.md`, `docs/COMPLIANCE.md`, wiring sheet 05 | in progress (spec done; sheet and matrix with F-02/F-07 owner) |
| F-04 stale or unsupported VALIDATION statements | Major | Analysis, CFD, package and field-count lines regenerated from fresh runs; STE claim replaced by the generator's own check result once implemented (F-10); package path fixed in `package.py` | `docs/VALIDATION.md`, `software/ben_engine/package.py` | in progress (STE line pending F-10) |
| F-05 "confirmed" prices on non-vendor pages | Minor | Eight lines re-sourced or downgraded; loader rule rejects marketplace/aggregator hosts and missing check dates; test added | `purchasing/parts_catalog.json`, `software/ben_engine/bom.py`, `tests/test_bom.py` | in progress |
| F-06 stale generation-1 terms | Minor | STE_STYLE rule 11, CMA hold-point row, TASKS, OPERATIONS, wiring strings and file names updated | grep in `scripts/audit.py` A5 | in progress (lead items closed) |
| F-07 compliance matrix stale cells, GWP not carried | Minor | Tier cells corrected, sections renumbered, `refrigerant`/`gwp` on every refrigerant-charged catalog line, GWP column in BOM output, refrigerant note on M-001 | `docs/COMPLIANCE.md`, catalog, `design/drawings/*/M-001` | in progress |
| F-08 brief row 17 artifact missing; e2e gate not in CI | Minor | `tests/test_e2e.py` added (commissioning sim for 3 tiers with CSV hash, all sweeps, CLI); CI runs it with the suite plus `check_links.py` and `audit.py`; brief row corrected | `tests/test_e2e.py`, `.github/workflows/ci.yml`, `docs/BRIEF.md` | closed |
| F-09 field-count duplicated and stale | Minor | `_meta.field_count` computed; prose no longer states the literal | `docs/contracts/fields.json`, `docs/proposals/README.md`, `docs/VALIDATION.md` | closed |
| F-10 STE rules 2 and 10 violated | Minor | Step texts fixed; word-count and banned-word check built into `gen_assembly.py` (fails generation) | `design/assembly/gen_assembly.py`, `scripts/audit.py` A10 | in progress |
| F-11 cyber controls documented only; default credential | Minor | Status column added to CYBERSECURITY; RevPi claim made consistent; installers refuse `CHANGE_ME`; A/B, dm-verity, SBOM on roadmap or implemented | `docs/CYBERSECURITY.md`, `firmware/ben-edge/*/install.sh`, `docs/ROADMAP.md` | in progress |
| F-12 SQAM scope omits BEN 2000 | Minor | Applies-to sentence generated from the tier table; drawing revision from REVISION.json | `design/gen_sqam.py`, `docs/SQAM.md` | in progress |
| F-13 personal e-mail in project document | Minor | Replaced by "the operator's mail account" | `purchasing/EMAIL_QUEUE.md` | closed |
| F-14 "confirmed" over-promises | Observation | Reader-facing label becomes "confirmed listing" with its one-sentence definition wherever shown | `docs/BOM.md`, `purchasing/SOURCING_NOTES.md`, proposal §6 note | in progress |
| F-15 evidence produced but not stored | Observation | `scripts/store_evidence.py` writes build report, audit output, pytest and firmware summaries to `docs/audit/evidence/` | `docs/audit/evidence/INDEX.md` | closed |
| F-16 failsafe table presented three ways | Observation | Accepted; `interlocks.FAILSAFE_TABLE` is the source, the two documents restate it; a consistency test is on the roadmap | — | accepted |
| F-17 test-quality weaknesses | Observation | Accepted for this release; specific tests listed in the report are on the roadmap | `docs/ROADMAP.md` | deferred |
| F-18 honest-limits lists are subsets | Observation | README and FAQ lists now state they are the short form of VALIDATION §7 | `README.md`, `docs/FAQ.md` | in progress |
| F-19 BEN 2000 schedule criterion | Observation | Disclosed in PROCESS_FLOW and the proposal (52 weeks best case, 60–72 at catalog leads) | `docs/PROCESS_FLOW.md` | accepted |
| F-20 CI and documented gates differ | OFI | CI now runs suite + links + audit; browser suite stays on demand (runtime) | `.github/workflows/ci.yml` | closed |
| F-21 drawing generation non-deterministic | OFI | Seeds/timestamps fixed in generators | `design/drawings/gen_drawings.py` | in progress |
| F-22 catalog hygiene | OFI | Items in the finding worked with F-05 | catalog | in progress |

Re-audit: run `python scripts/audit.py` (mechanical) and repeat `docs/audit/AUDIT_CHECKLIST.md` areas A–L before the next release. Close-out of this log is recorded in `docs/PROJECT_STATE.md`.
