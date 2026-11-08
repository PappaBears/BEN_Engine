# TASKS

| ID | Outcome | Owner | Status | Acceptance / evidence |
| --- | --- | --- | --- | --- |
| T1 | Brief, config model, skeleton | lead | done | `docs/BRIEF.md`, `software/ben_engine/config.py` sizing runs for 5 tiers |
| T2 | Twin, CFD, calibration, analysis, sweeps, commissioning | agent A | done | `pytest tests` |
| T3 | Firmware: BEN Pod + BEN Controller (edge, PLC) + specs + wiring one-lines | agent B | done | `make test` (firmware/ben-pod) |
| T4 | Dashboard + API + 3D + e2e | agent C | done | `tests/test_api.py`, `tests/e2e/run_e2e.sh`, screenshots |
| T5 | IFC drawings, renders, STE assembly, QC forms, design basis | agent D | done | files under `design/` |
| T6 | Parts catalog, BOM generator, pricing confirmation, email queue | agent E | done | `tests/test_bom.py`, `docs/BOM.md` |
| T7 | Compliance, risk register, process flow, site reqs, turnover, maintenance, build/wiring, test guide, cyber | agent F | done | files under `docs/` |
| T8 | Product page, brand kit, marketing, VC proposition, decks | lead | done | `web/`, `docs/investors/` |
| T9 | Verify, VALIDATION, manifest, commit, push | lead | done | `docs/VALIDATION.md`, git log |
| T10 | Proposal generator + contract pre-fill | agent H | done | `tests/test_proposal.py` 16 passed, `docs/proposals/` |
| T11 | Two-sided contracts set with LD flow-down and fields.json | agent I | done | `docs/contracts/` |
| T12 | SQAM generated from CTQ register, CTQ cards | agent D | done | `docs/SQAM.md`, `design/assembly/CTQ-CARD-*.md` |
| T13 | Manufacturing strategy (third-party first), revised process flow, CM RFI | agent F | done | `docs/MANUFACTURING_STRATEGY.md` |
| T14 | Deal package assembler + dashboard Proposal panel + API | lead | done | `tests/test_package.py`, `tests/test_api.py` |
