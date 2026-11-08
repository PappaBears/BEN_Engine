# BEN Engine — Internal Audit Report

| | |
| --- | --- |
| Report | AUD-BEN-2026-11-08 |
| Auditee | BEN Engine project (Schreiber AI), repository `PappaBears/BEN_Engine`, branch `main`, commit `5c0e57e` ("Finishing pass … 178 tests") |
| Audit type | Internal, independent (ISO 19011 style), pre-release: before supplier RFQs leave and before investor review |
| Audit dates | 2026-11-08 (single session, 03:50–04:40 UTC, Linux cloud container, Python 3.13, Node 22, Playwright Chromium) |
| Auditor | Independent internal auditor (this session), no part in building the deliverables |
| Audit client | Operator (Ben Schreiber, Schreiber AI) |
| Distribution | Operator; project lead; whoever owns the CAPA items |
| Reusable checklist | `docs/audit/AUDIT_CHECKLIST.md`; automated checks `scripts/audit.py` (output in Appendix A) |

## 1. Scope

The whole repository as the product that is about to be shown to contract manufacturers, component suppliers and investors: the 24 deliverables of `docs/BRIEF.md` §5, the evidence that supports their claimed status, the configuration-management and document-control practice around generated files, the purchasing catalog and its price-status claims, the compliance matrix, the safety-critical design statements, cybersecurity claims, the two-sided contract set, website and deck claims, data and secrets hygiene, test quality, and the honest-limits statements. Hardware was not available; nothing physical was audited.

Out of scope: legal adequacy of the contracts (counsel review is already a stated condition), the correctness of engineering values that need a lighthouse unit to verify (these are checked only for whether their status is stated honestly), and the external websites behind catalog URLs (not reachable from the audit environment; URLs were inspected for form and provenance only).

## 2. Criteria

1. **The brief's acceptance list**: `docs/BRIEF.md` §5 rows 1–24, column "Done when".
2. **Schreiber AI evidence standard** (`docs/VALIDATION.md` line 5): every capability labelled *verified* (run here and observed), *implemented, unverified*, *simulated*, *blocked* or *deferred*; a *verified* claim must be reproducible from the repository.
3. **House standards in the repository**: `design/assembly/STE_STYLE.md` (ASD-STE100 rules), `docs/contracts/README.md` §4 and §6 (LD flow-down, field vocabulary rule), `docs/COMPLIANCE.md` §0 decisions, `design/specs/CONTROLS_SPEC.md` §1 "rules that do not change", `purchasing/SOURCING_NOTES.md` and the catalog's `price_status` vocabulary, `docs/build-contract.json` and `docs/launch-manifest.json`.
4. **Basic software quality**: tests pass from a clean checkout with the documented commands; tests assert behaviour; CI runs what the documentation says is the gate; no secrets; JSON well-formed; links resolve.
5. **Document control**: a document that changes gets a new revision or issue date; generated documents are regenerated, not hand-edited; revision marks are consistent across documents that cite each other; issue-for-construction documents carry a checker.

Classification used: **Major nonconformity** (a stated claim is false or an item a supplier, customer or investor will rely on is inconsistent in a way that misleads or affects safety or contract), **Minor nonconformity** (a requirement of the criteria is not met but the exposure is contained or the gap is disclosed), **Observation** (a weakness that is not yet a nonconformity), **OFI** (opportunity for improvement).

## 3. Method

Documents read in full: `docs/BRIEF.md`, `docs/VALIDATION.md`, `docs/PROJECT_STATE.md`, `docs/PROJECT_NOTES.md`, `docs/launch-manifest.json`, `docs/build-contract.json`, `docs/COMPLIANCE.md`, `docs/contracts/README.md`, `purchasing/SOURCING_NOTES.md` (sampled), `README.md`, `design/specs/CONTROLS_SPEC.md` §1 and §7, `firmware/ben-plc/README.md`, `software/ben_engine/interlocks.py` (failsafe table), `design/assembly/STE_STYLE.md`, `docs/CYBERSECURITY.md` (sampled), `docs/TASKS.md`, `docs/ROADMAP.md`, `docs/BEN_CARE.md` §Honest limits, `docs/FAQ.md`, `docs/proposals/README.md`, `.github/workflows/ci.yml`, `scripts/prepare_paperwork.py`, `software/ben_engine/package.py` (document list), `tests/test_package.py`, `tests/test_twin.py`, `tests/test_cfd.py` (assertions). Sampled: `docs/SQAM.md`, `docs/PROCESS_FLOW.md`, `docs/MAINTENANCE.md`, `docs/TURNOVER.md`, `docs/RISK_REGISTER.md`, `docs/TEST_GUIDE.md`, `docs/investors/*`, `web/index.html`, `firmware/ben-edge/*`, `design/drawings/*/INDEX.md`, `design/specs/wiring/gen_wiring.py`, `design/assembly/ASSEMBLY-*.md`.

Commands run (all from `/home/user/ben_engine`, results in §5 and Appendix A):

```
PYTHONPATH=software python -m pytest tests -q --ignore=tests/e2e [-rs]      # 178 passed, 0 skipped, 17.97 s
PYTHONPATH=software python -m pytest tests --collect-only -q --ignore=tests/e2e
cd firmware/ben-pod && make test                                             # 37 tests, 0 failures
python scripts/check_links.py                                                # 148 md files, 0 broken
python <skill>/schreiber-ai/scripts/build_control.py run --repo .            # verified: false (2 of 5 fail)
PYTHONPATH=software python -m ben_engine.bom --all                           # VALIDATION §4 reproduction
PYTHONPATH=software python -m ben_engine.cfd --tier ben150                   # VALIDATION §2 reproduction
PYTHONPATH=software python -m ben_engine.analysis --tier ben150 --load 1.0 --outdoor 35
PYTHONPATH=software python -m ben_engine.commissioning --sim --tier ben150 --yes --fast --out <scratch>
PYTHONPATH=software python scripts/unit_economics.py
python design/gen_sqam.py; python design/assembly/gen_assembly.py; python design/gen_design_basis.py
python scripts/gen_catalog.py; python design/specs/wiring/gen_wiring.py; python design/drawings/gen_drawings.py
git status --short; git diff --stat; git checkout -- design/drawings          # hand-edit check, then restore
bash tests/e2e/run_e2e.sh                                                    # Playwright, 25/25 (Appendix C)
python scripts/audit.py; python scripts/audit.py --run                       # Appendix A
```

Ad-hoc scripts (reproduced in Appendix B): token comparison `fields.json` vs templates; LD-clause cross-check; STE word-length and banned-word scan; AST scan for tests without assertions; catalog URL/domain survey; stale-reference grep; secrets/e-mail grep; numeric-claim extraction from `web/index.html` and `slides.json`.

Sampling: 15 "confirmed" catalog lines (all 57 were listed; the 15 named in F-05 were examined in detail); 3 VALIDATION claims reproduced plus 2 incidental; 5 of 11 contract templates read at the cited LD clauses; all 5 STE assembly documents scanned; all 42 drawing SVGs grepped; 2 of 5 drawing INDEX files read.

Working-tree hygiene: every generator run during the audit was followed by `git status`; drawings and `docs/media` were restored with `git checkout --`. The only files added by the audit are `docs/audit/AUDIT_REPORT_2026-11-08.md`, `docs/audit/AUDIT_CHECKLIST.md` and `scripts/audit.py`. Nothing was committed.

## 4. Summary of results

| Classification | Count | Findings |
| --- | --- | --- |
| Major nonconformity | 4 | F-01, F-02, F-03, F-04 |
| Minor nonconformity | 9 | F-05, F-06, F-07, F-08, F-09, F-10, F-11, F-12, F-13 |
| Observation | 6 | F-14, F-15, F-16, F-17, F-18, F-19 |
| Opportunity for improvement | 3 | F-20, F-21, F-22 |
| **Total** | **22** | |

What is in good order (conformities worth recording): the Python suite (178), firmware host tests (37, zero warnings) and link check all pass as documented; BOM totals, unit economics and the commissioning simulation reproduce exactly; the generators for SQAM, STE assembly, design basis, catalog/schema and wiring one-lines regenerate byte-identical output (no hand edits); the life-safety hardwired rule is present in the protocol, controls spec, SQAM (CTP-K1), SOW §3.6, SLA 3.5, CMA hold-point table, drawing E-001 and sheet 05; the three failsafe tables agree row for row; every LD clause cited in the flow-down matrix exists and carries the named fields; `fields.json` covers every template token; no secrets; all JSON parses; risk list on the product page precedes the price; deck numbers trace to `unit_economics.py` and `MARKET_SOURCES.md`; the honest-limits list exists in four places and is ordered consistently.

**Overall conclusion: release-ready for supplier RFQs and investor review — YES, WITH CONDITIONS.** The RFQ e-mails (price inquiries that send no drawings) and the investor conversation can proceed once the four Major findings are closed, because each of them is a statement the recipient would rely on that is currently not true or not consistent: the acceptance gate does not run as written (F-01); the issue-for-construction drawing set is Rev A for two different designs and has no checker (F-02); the controls specification cites a code article the compliance matrix says is not invoked, in the one rule that "does not change" (F-03); and the honest-ledger `docs/VALIDATION.md` contains stale or unsupported statements (F-04). None of these needs hardware to fix; all are a day's work. The build package (drawings, STE instructions, SQAM) must **not** go to a contract manufacturer until F-02, F-03, F-10 and F-12 are closed.

## 5. Results by audit area

### 5.1 (a) Traceability brief → deliverable → evidence

| § 5 row | Deliverable | Artifact exists | Status claimed (where) | Test / inspection record | Audit view |
| --- | --- | --- | --- | --- | --- |
| 1 | IFC drawing set with CTQ/CTP | `design/drawings/<tier>/` 42 SVG+PNG, `INTERFERENCE_CHECKS.md` | verified (generated, inspected) — README:29 | generator rerun (41 s), `INDEX.md`, interference table | Artifact OK; **status overstated**: no checker, Rev A reused (F-02) |
| 2 | Renders + STE assembly | `design/renders/`, `design/assembly/ASSEMBLY-*.md`, CTQ cards, QC forms | verified (STE rules checked by script) — README:30 | none in repo for the STE rules | **No script exists**; STE violations found (F-04b, F-10) |
| 3 | Process flow | `docs/PROCESS_FLOW.md` 30 stage rows with owner/inputs/outputs/hold points/records | written | inspection | Conforms |
| 4 | Firmware + specs + one-lines | `firmware/ben-pod`, `ben-edge`, `ben-plc`, `design/specs/*.md`, `wiring/*.svg` | host verified; cross-build blocked; edge/PLC implemented-unverified | `make test` 37/37 rerun | Status honest; one-line file names and revs stale (F-02, F-06) |
| 5 | Commissioning script | `software/ben_engine/commissioning.py` | verified in simulation | rerun 10/10 PASS, SHA-256 in report | Conforms; build-contract wrapper fails (F-01) |
| 6 | Turnover + maintenance | `docs/TURNOVER.md`, `docs/MAINTENANCE.md` (§4a hall, §5a hardening) | written | inspection | Conforms |
| 7 | Compliance matrix | `docs/COMPLIANCE.md` §0–§15 | written; editions checked where possible (§13) | inspection | Stale tier codes, section order, 645 contradiction (F-03, F-07) |
| 8 | Dashboard | `dashboard/`, `api.py`, screenshots | verified (26 API tests, e2e 25/25) | `test_api.py` 26 collected; e2e rerun this audit 25/25 (Appendix C) | Conforms |
| 9 | Calibration + analysis | `calibration.py`, `analysis.py` | verified on synthetic data | rerun; numbers differ from VALIDATION (F-04a) | Artifact OK, record stale |
| 10 | CFD | `cfd.py` | verified, relative tool | rerun 232×90 converged | Conforms (step/time text stale, F-04d) |
| 11 | Parts list | `purchasing/bom.csv`, `docs/BOM.md`, `parts_catalog.json` 204 lines | verified (30 tests); prices are listings | `test_bom.py` 30 collected; `bom --all` reproduces | Conforms; "confirmed" basis weak (F-05, F-14) |
| 12 | Purchasing e-mails | `purchasing/email_queue/01–21`, `EMAIL_QUEUE.md` | drafts, nothing sent | inspection | Conforms; personal Gmail noted (F-13) |
| 13 | Build/wiring + test guide | `docs/BUILD_AND_WIRING.md`, `docs/TEST_GUIDE.md` (16 experiments, each with hypothesis) | written | inspection | Conforms |
| 14 | Product page | `web/index.html`, `web/assets/` | verified (rendered) | `shoot_web.mjs` screenshots; `test_selector_parity.py` 13 | Conforms; risks section (line 57) precedes price (line 103) |
| 15 | Marketing kit | `web/kit/` brand.json, guide, kit, logo, wordmark | written | inspection | Conforms |
| 16 | VC proposition + deck | `docs/investors/` | written; numbers from BOM | `unit_economics.py` reproduces table byte-identical | Conforms |
| 17 | Simulated end-to-end test | **`tests/test_e2e.py` does not exist** (brief:80); real artifacts are `commissioning-sim-e2e` in the build contract and `tests/e2e/dashboard.spec.mjs` | "passes in CI" | CI runs only pytest + firmware; build contract fails as written | **Gap** (F-08, F-01) |
| 18 | Honest final report | `docs/VALIDATION.md` | — | reproduction of 5 claims | 3 reproduce, 2 stale/unsupported (F-04) |
| 19 | Proposal generator | `proposal.py`, 5 samples | verified (16 tests) | 16 collected; sample numbers consistent with BOM | Conforms; "891 fields" stale (F-09) |
| 20 | Two-sided paperwork | `docs/contracts/` 11 templates + fields.json + ready/ | templates for counsel review | LD clause cross-check (App. B) | Conforms; stale "node" term (F-06) |
| 21 | Manufacturing strategy | `docs/MANUFACTURING_STRATEGY.md` §1–§11 | written | inspection | Conforms |
| 22 | Deal package assembler | `package.py` | verified (tests; 0 missing) | current code produces 1 MISSING in partner package | **Record stale** (F-04c) |
| 23 | BEN 2000 | `config.py ben2000`, COMPLIANCE §14, PROCESS_FLOW, SITE, MAINT, BUILD | done; physical values unverified | `config --tier ben2000`; proposal 71 weeks vs 52-week target disclosed in VALIDATION §4a | Conforms with disclosure (F-19) |
| 24 | Hardening H1–H3 | `config.py hardening`, COMPLIANCE §15, TEST_GUIDE E14, WARRANTY 1.3, RISK R31–R33, MAINT §5a | done; vendor pricing unverified | catalog 19 `applies_to_hardening` lines | Conforms |

### 5.2 (b) Evidence integrity

| Claim (`docs/VALIDATION.md`) | Reproduced | Result |
| --- | --- | --- |
| line 11: 178 passed | yes | 178 passed in 17.97 s; 0 skipped (`-rs`) |
| line 12: firmware 37 tests, 0 failures, zero warnings | yes | 37/37, no `warning:` in `make test` output |
| line 13: build contract, all five checks pass | yes | **`"verified": false`**: `commissioning-sim-e2e` and `sweeps-ben500` exit 1 in 15 ms with `ModuleNotFoundError: No module named 'ben_engine'` (report `.schreiber-ai/runs/72cbb193…/report.json`) |
| line 44: BOM totals and confirmed % per tier | yes | identical to the cent: 65/$132,118/60.3 %, 92/$666,095/80.0 %, 104/$1,890,335/78.5 %, 105/$4,446,283/82.7 %, 94/$40,414,106/72.7 % |
| line 23: CFD BEN 150 grid 232×90, converged in 2750 steps, 14.6 s | yes | grid 232×90, **2500** steps, 12.66 s, converged (text stale, numbers of the same kind) |
| line 25: analysis "rack 5 inlet 22.3 ± 0.2 °C … 2.0 min ride-through" | yes | **24.4 ± 0.2 °C and 4.5 min** (recirculation 0.12 / bypass 0.15 recovered as stated) |
| line 17: commissioning 10/10, 10 probes within 0.5–0.7 K, 38 I/O points, 0.5 % reconciliation, worst inlet 25.5 °C | yes (`--fast`) | 10/10 PASS; 0.50 K; 38 points; 0.52 %; 25.5 °C; ASHRAE limit at 4.9 min (VALIDATION 3.9), PUE 1.192 (1.17), 871 rows (1077–1431): the `--fast` path differs, acceptable |
| line 43: assembly "0 instructions over 20 words; banned-word check passes" | yes (own script) | **29 instruction sentences over 20 words; 21 banned-word uses**; no checking code exists in `gen_assembly.py` |
| line 47: packages "0 missing" | yes (dist and code) | `package.py:57` lists `design/specs/BEN-NODE-v1.md`, which does not exist; latest partner MANIFEST (`dist/packages/SAI-BEN150-20261108-2F67AC17/partner-package/MANIFEST.md:24`) shows `MISSING` |
| line 31: e2e 25/25 | yes | 25/25 passed, exit 0, 0 console errors (Appendix C) |

### 5.3 (c) Configuration and document control

- Generators regenerate identically: `gen_sqam.py`, `gen_assembly.py`, `gen_design_basis.py`, `gen_catalog.py`, `gen_wiring.py`, `bom --all`, `unit_economics.py` → `git status` empty. **No hand-edited generated file found.**
- `gen_drawings.py` regenerates 46 changed files, but the diff is only `<dc:date>` and matplotlib clip-path ids (Appendix B) — content identical, output non-deterministic (F-21).
- Revision marks: drawings "Rev A 2026-11-08" (`gen_drawings.py:29`), SQAM "IFC drawing set Rev A (2026-11-07)" (`docs/SQAM.md:10, 472`), QC forms "IFC Rev A 2026-11-07" (`QC_FORMS.md:11`), STE assembly "Issue A · 2026-11-07" (hard-coded in the generator, so `ASSEMBLY-ben2000.md:3` is dated before BEN 2000 existed), wiring power/cooling/life-safety "IFC Rev A", controls one-lines and specs "IFC Rev B 2026-11-08", `STE_STYLE.md` "Issue A, 2026-11-07" (F-02).
- Duplicated numbers that drift: field count 891 (VALIDATION:48, proposals/README:35, fields.json `_meta`) vs 911 declared; interior height 2.55 m (COMPLIANCE:43) vs 2.49 m (PROJECT_NOTES D24, DESIGN_BASIS, config); analysis prediction values (F-04a); CFD step count.
- Regeneration commands are scattered (README "More commands", proposals/README, drawings/README, OPERATIONS, each generator's docstring); there is no single list (F-20).

### 5.4 (d) Purchasing

- Mechanical checks pass: 57/57 confirmed lines have `vendor_url` and `price_checked`; 144/144 estimates have a `price_source_note`; 204/204 have `lead_time_weeks`. The three `list` lines (`CTL-RCP`, `CTL-REVPI-DIO`, `CTL-REVPI-AIO`) have `price_checked: null` and `CTL-REVPI-DIO` has no URL.
- 15-line sample of "confirmed" (code → URL host → observation): STR-CONT10, STR-CONT20, STR-MANDOOR → `reach.dog` (a marketplace front for dealers, not the dealer); PWR-METER → `alibaba.com` (marketplace, $85 meter for a revenue-relevant point); CLG-CABAC → `digikey.co.uk/en/videos/…` (**a video page, not a product listing**, yet "confirmed $9,222.32 with 1 in stock"); CMP-GPU-H100 → `marketplace-admin.uvation.com` (an admin host name, unlikely to be the public product page); CTL-MGM240P, CTL-PLC → `findchips.com` (aggregator, not Mouser/TTI); ENV-PIR → `superarbor.io` reseller; CTL-PANEL → Platt product page whose slug reads "nema-3r-4-12-13" for a Type 12 Hoffman A302412LP (plausible, verify); STR-RACK42, PWR-PDU, CTL-POE-SW, FS-EPO → CDW product pages (good); PWR-UPS-SRT6K → SHI (good); PWR-PANEL-ILINE → Standard Electric Supply (good). Dates present on all. (F-05)
- Estimate bases: the 10 notes read (SITE-CRANE, SVC-PE, CTL-POD, SITE-GENPAD "Engineering estimate" only, SITE-PERMIT, CLG-RDHX, CLG-CDU, CLG-DRYCOOLER, PWR-UPS-GVS150, STR-MODULE-WB, CTL-EDGE) state a basis except SITE-GENPAD. Lead times present everywhere.
- VALIDATION line 44 defines "confirmed" as "distributor listing seen in search results on 2026-11-07/08, not a quote". That definition is honest but the word "confirmed" on an investor's or supplier's screen means more (F-14).

### 5.5 (e) Compliance matrix

- Unverified editions are flagged in §13 and inline (*verify with AHJ*). Conforms.
- A2L/GWP: COMPLIANCE §0 finding 2 says "all DX selections in the BOM carry a GWP column". The catalog has a `gwp` key on **one** line (`CLG-REFRIG`, 631); `CLG-INROW`, `CLG-CABAC`, `CLG-COND` carry none; `bom.csv` has no GWP column; no drawing mentions R-513A or GWP (A2L appears on 4 sheets). NFPA 855: `PWR-BATT-LI`, `PWR-BATT-ROOM` reference UL 9540; 5 drawings mention 9540. UL 508A: `CTL-PANEL`, `CTL-PANEL-BUILD`; 8 drawings mention 508A. (F-07)
- Stale generation-1 tier codes remain in the Tiers column: line 71 "20 (optional), 40", line 83 "Pro: 10 (option), 20, 40", line 85 "M". Sections run §12 → §14 → §15 → §13. Line 43 "interior 2.55 m" contradicts the 2.49 m used everywhere else. (F-07)

### 5.6 (f) Safety-critical design claims

- Life-safety hardwired rule: `spec/PROTOCOL.md:191`, `CONTROLS_SPEC.md:7, 24, 86, 104`, `docs/SQAM.md:120…311` (CTP-K1, five tiers), `SOW_TEMPLATE.md:160`, `MANAGED_SERVICES_SLA.md:70`, `CONTRACT_MANUFACTURING_AGREEMENT.md:114`, `design/drawings/ben150/E-001.svg:7313`, `design/specs/wiring/05_life_safety_one_line.svg`, `docs/CYBERSECURITY.md` Z0. **Present everywhere required.**
- Failsafe tables: `interlocks.py:444–451` (6 outputs × 2 columns), `firmware/ben-plc/README.md` table (7 rows, adds "PLC in MANUAL" column and "Fire/EPO not connected"), `CONTROLS_SPEC.md` §7a (6 rows) + §7b (edge outputs). Row-by-row the states agree (cooling commands → local control; enable relay → drops; valves hold / spring-return option; CDU pump stop → released; beacon → NC contact; trim → ignored). The only differences are presentational (F-16).
- Code citation: `CONTROLS_SPEC.md:7` ("relay-and-wire circuits per NFPA 72 / NFPA 2001 / **NFPA 70 Art. 645**") and `gen_wiring.py:586` ("NFPA 70 Art. 645 EPO" on the life-safety sheet title) contradict `COMPLIANCE.md:31` finding 4 and `PROJECT_NOTES.md` D17 ("NEC Article 645 not invoked"; EPO provided under NFPA 75). (F-03)
- Browser e2e rerun during this audit: **25/25 passed, exit 0** (Appendix C); `VALIDATION.md:31` confirmed.

### 5.7 (g) Cybersecurity claims vs implementation

Implemented in the repository: nftables default-deny (`firmware/ben-edge/nftables.conf`), four-listener Mosquitto with mTLS and per-Pod ACL (`mosquitto/ben.conf`, `ben_acl.template`), TPM 2.0 + LUKS via clevis PCR 0,2,7 (`install.sh:36–49`), WireGuard outbound-only support tunnel script, backup timer, PLC project CRC check (`ben.env.example:16`), Pod firmware signature/anti-rollback logic on host (`firmware/ben-pod`). Documented only (no code or artefact): signed **A/B images with dm-verity** on the Lite tier (`CYBERSECURITY.md:37`), **A/B image with automatic rollback** for the edge OS (`:70`), **SBOM (SPDX)** per release (`:73`; no SBOM file anywhere), Pod attestation challenge on the edge side, PSA attestation token verification. `VALIDATION.md` §5 labels the edge image "implemented, unverified" without naming these as not implemented. `lite/install.sh:17` says the LUKS key sits on "the RevPi's secure element" while `CYBERSECURITY.md:37` says the RevPi has no TPM; neither cites the vendor. `lite/install.sh:161` and `install.sh:170` write a default `password=CHANGE_ME` for the NAS credential. (F-11)

### 5.8 (h) Contracts

- LD flow-down matrix (`docs/contracts/README.md` §4) vs clauses: all 9 cited clause groups exist; field tokens present where cited (`MSA.md:166` 7.7 carries `LD_GRACE_DAYS`, `CUSTOMER_LD_RATE_PCT_PER_WEEK`, `CUSTOMER_LD_CAP_PCT`; `CMA:172` 9.4; `SUPPLIER_TERMS:37` 3.4; `INTEGRATOR:182` 13.1). Conforms.
- `fields.json` vs templates: 911 template tokens (excluding the templates' own words FIELD/FIELDS/FIELD_NAME), 911 declared, 0 missing either way. `_meta.field_count` says 891 (F-09).
- Stale term: `CONTRACT_MANUFACTURING_AGREEMENT.md:114` "Dry contacts only to node" (product term is Pod/controller) (F-06).
- Counsel banner present on every template; §7 assumptions list current. `scripts/prepare_paperwork.py` fills `TEMPLATE_REV` with the git short hash, so `ready/` documents carry a traceable revision. Conforms.

### 5.9 (i) Website and marketing claims

Every number extracted from `web/index.html` is descriptive (tier kW ranges, 600 mm plinth, C5-M, 67 m/s / 150 mph, 2-hour separation, NFPA 110 Level 1, 48 h fuel) and matches `config.py` / COMPLIANCE §14–15; prices on the page are computed by the ported selector (`test_selector_parity.py`, 13 tests). Investor deck numbers ($0.64 M, $2.6 M, $16.4 M, $10,200/kW, $45/kW-month, $10,000–13,000/kW traditional) match `unit_economics.py` output and `MARKET_SOURCES.md:13` (Cushman & Wakefield via Uptime). Market sizes quoted as ranges with 8 cited sources. Product deck "PUE 1.13" matches `config --tier ben2000` (1.134). No Tier or TEMPEST certification is claimed. Conforms.

### 5.10 (j) Data and secrets

No API keys, tokens or private keys (Appendix A, A11). Credentials in `firmware/ben-edge` are generated at install or read from `ben.env`; `ben.env.example` has placeholders only. E-mail addresses: `Ben@SchreiberAI.com` ×136, `security@schreiberai.com` ×3 and **`schreibears@gmail.com` ×1** (`purchasing/EMAIL_QUEUE.md:30`, the account in which the Gmail drafts were created) (F-13). Phone-like matches were SVG coordinates. No vendor URL is fabricated in form, but eight "confirmed" URLs are not vendor product pages (F-05).

### 5.11 (k) Test quality

178 tests, 0 without an assertion (AST scan), 0 skipped in this run; three conditional `pytest.skip` calls in `tests/test_api.py:252, 273, 286` would silently drop sim-node coverage if `sim_nodes` were unavailable. `tests/test_sweeps.py:37–38, 49` assert only `is not None`. `tests/test_package.py` asserts a MISSING line appears for an injected bad path but does not assert that the **real** document list has zero missing, which is how F-04c escaped. `tests/test_twin.py` and `test_cfd.py` assert physical ranges (ΔT 8–20 K, u_lattice < 0.2, rises within 0.6–1.6 × design): meaningful. e2e coverage: 25 named checks spanning presets, hardening, faults, sweeps/CSV, every panel, calibration, tour, tooltips, proposal, 390 px, uncaught errors; there is no check of the I/O test action itself (brief row 8 "I/O test") beyond the panel rendering. CI runs only pytest and firmware; not the build contract, link check or e2e (F-17, F-20).

### 5.12 (l) Honest-limits statements

`docs/VALIDATION.md` §7 (7 items, ordered), `docs/FAQ.md:45` (6 items: drops "assembly time / MTBF" and "market sizes", adds "every hardware-layer behaviour"), `docs/BEN_CARE.md` §Honest limits (3 statements: thermal time constants, fleet learning, Pod hardware), `README.md:38` points to VALIDATION, deck notes line 77 "least accurate items named". The lists are consistent in order where they overlap; the FAQ and BEN Care lists are subsets without saying so (F-18).

## 6. Findings

### F-01 — Build contract does not pass as written; VALIDATION says it does — **Major nonconformity**

- **Criterion:** evidence standard (a *verified* claim is reproducible); `docs/build-contract.json`; `docs/launch-manifest.json` `acceptance_ids`.
- **Evidence:** `build_control.py run --repo .` → `"verified": false`; `.schreiber-ai/runs/72cbb1934f3a4659affa9509bd874b4c/commissioning-sim-e2e.log`: `/usr/local/bin/python3: Error while finding module specification for 'ben_engine.commissioning' (ModuleNotFoundError: No module named 'ben_engine')`; same for `sweeps-ben500`. `docs/build-contract.json` lines 7–8 run `python3 -m ben_engine.*` with no `PYTHONPATH`; `pip show ben-engine` → not installed; `pyproject.toml` only sets `pythonpath` for pytest. `docs/VALIDATION.md:13` states all five checks **pass**; `docs/launch-manifest.json` cites `commissioning-sim-e2e` and `sweeps-ben500` as the evidence for two *verified* capabilities. Earlier run reports in `.schreiber-ai/runs/` passed, so the environment they ran in had the package importable; the repository does not.
- **Gap:** the acceptance gate that the launch manifest and VALIDATION rely on fails from a clean clone; the recorded pass is not reproducible.
- **Risk:** an investor's or partner's engineer who runs the stated gate gets a failure on the first try, which discredits the rest of the evidence ledger; the two capabilities lose their *verified* evidence.
- **Corrective action (owner: project lead / release owner):** make the contract self-sufficient (either `pip install -e .` in the contract's setup, or commands `env PYTHONPATH=software python3 -m …`, or a `scripts/` wrapper), rerun, store the passing `report.json` in the repository (not only under the git-ignored `.schreiber-ai/`), and correct VALIDATION §1. Add `scripts/audit.py --run` (A3) to the pre-release routine.

### F-02 — IFC drawing set and its dependants are not under revision control — **Major nonconformity**

- **Criterion:** document control; brief row 1 ("issue-for-construction"); `docs/SQAM.md` and SOW pin the drawing revision.
- **Evidence:** `design/drawings/gen_drawings.py:29` `DATE = "2026-11-08"`, title block "Rev A" on all 42 sheets (drawkit.py:179–199), while the set was regenerated for a materially different product (new tiers BEN 5/30/150/500, 14 new BEN 2000 sheets, IP66 envelope) after the Rev A set of 2026-11-07 that `docs/SQAM.md:10, 472`, `design/assembly/QC_FORMS.md:11` and `docs/proposals/sample-ben150-healthcare-SOW-draft.md:99` cite ("IFC Rev A (2026-11-07)"). Every `design/drawings/*/INDEX.md:17` says "Checked: blank (requires a checker before release)" under a status of **ISSUE FOR CONSTRUCTION**; `design/drawings/README.md:61–64` acknowledges it. `design/specs/wiring/gen_wiring.py:631` writes `03_power_one_line_{micro,ben10,ben20,ben40}.svg` (generation-1 keys) whose titles read "BEN 150 …"; those sheets and 04/05 say "IFC Rev A" while 01/01b/02 and the three spec sheets say "IFC Rev B · 2026-11-08". `design/assembly/gen_assembly.py` hard-codes "Issue A · 2026-11-07", so `ASSEMBLY-ben2000.md:3` is dated before BEN 2000 was decided (D34, 2026-11-08). `README.md:29` labels the set "verified (generated, inspected)".
- **Gap:** two different designs carry the same revision; documents that reference each other cite different dates for that revision; IFC status is claimed without a checker; file names do not match content.
- **Risk:** a contract manufacturer quoting or building from "Rev A" cannot tell which Rev A; the SQAM and QC forms bind to a revision that no longer exists as described; a drawing labelled IFC without a check is a liability if built from.
- **Corrective action (owner: Schreiber AI engineering, design authority):** introduce a revision scheme driven by one variable (e.g. `design/REVISION.json`) that every generator reads; bump drawings to Rev B (or re-issue Rev A dated 2026-11-08 with a revision note) and regenerate SQAM, QC forms, assembly, wiring and the SOW sample so they cite the same rev/date; rename wiring outputs to the generation-2 keys; change the drawing status to "ISSUED FOR REVIEW" until a named checker signs, then re-issue as IFC; change `README.md:29` to "generated; unchecked" until then.

### F-03 — Controls specification cites NEC Art. 645 as the basis of the hardwired life-safety circuit, which the compliance matrix says is not invoked — **Major nonconformity**

- **Criterion:** `CONTROLS_SPEC.md` §1 "rules that do not change"; `COMPLIANCE.md` §0 finding 4; `PROJECT_NOTES.md` D17; brief §6 "compliance is central".
- **Evidence:** `design/specs/CONTROLS_SPEC.md:7` "relay-and-wire circuits per NFPA 72 / NFPA 2001 / NFPA 70 Art. 645, supervised by a listed releasing panel"; `design/specs/wiring/gen_wiring.py:586` life-safety sheet subtitle "NFPA 70 Art. 645 EPO"; `docs/COMPLIANCE.md:31` "NEC Article 645 is optional and we do not invoke it by default … We still provide the NFPA 75 items the fire marshal expects: EPO/remote disconnect at the exit door"; `docs/COMPLIANCE.md:56` "Art. 645 ITE rooms — Not invoked (finding 4)". Related: `docs/COMPLIANCE.md:43` "headroom 2.0 m preserved (interior 2.55 m)" vs `PROJECT_NOTES.md` D24 and `design/DESIGN_BASIS.md` 2490 mm.
- **Gap:** the two documents a panel shop, an integrator and an AHJ will read side by side give different code bases for the same safety circuit; a dimension used in the NEC 110.26 argument is wrong by 60 mm.
- **Risk:** AHJ or insurer challenge at the first permit; a panel shop designing the EPO to a 645 reading that the project has decided not to invoke; credibility of the "compliance is central" position.
- **Corrective action (owner: Schreiber AI engineering + compliance):** change CONTROLS_SPEC §1.1 and the life-safety sheet title to cite NFPA 75 (and NFPA 72 / 2001) as the basis for the EPO/HVAC-shutdown, with 645 mentioned only as "not invoked"; correct the interior height in COMPLIANCE §1 to the config value or make the row read it from `config.py`; add a grep for "645" to the audit checklist (F-4).

### F-04 — `docs/VALIDATION.md` contains stale or unsupported statements — **Major nonconformity**

- **Criterion:** brief row 18 ("honest final report"); evidence standard.
- **Evidence:** (a) `VALIDATION.md:25` "rack 5 inlet 22.3 ± 0.2 °C … 2.0 min ride-through" — rerun gives **24.4 ± 0.2 °C and 4.5 min** (same command, same fitted parameters). (b) `VALIDATION.md:43` "0 instructions over 20 words; banned-word check passes" and `README.md:30` "STE rules checked by script" — `design/assembly/gen_assembly.py` contains no word-count or banned-word check (grep for "banned", "ensure", "split()" returns nothing but the docstring); an independent scan finds 29 instruction sentences over 20 words (e.g. `ASSEMBLY-ben150.md:327` 33 words, `:342` 41 words) and 21 uses of rule-10 banned verbs (e.g. `ASSEMBLY-ben150.md:482` "Check the phase rotation", `:443` "Follow the battery manufacturer's shipping instructions", `ASSEMBLY-ben30.md:489` "check the refrigerant pressures"). (c) `VALIDATION.md:47` "customer package 22 files, partner package 21 files, 0 missing" — `software/ben_engine/package.py:57` references `design/specs/BEN-NODE-v1.md` (renamed to `BEN-POD-v1.md` by D32); the latest package `dist/packages/SAI-BEN150-20261108-2F67AC17/partner-package/MANIFEST.md:7, 24` reads "17 present, 1 missing … MISSING source design/specs/BEN-NODE-v1.md not found". (d) `VALIDATION.md:23` "converged in 2750 steps, 14.6 s" vs 2500 steps, 12.7 s observed. (e) `VALIDATION.md:48` "369 of 891 vocabulary fields" vs 911 fields in `fields.json`.
- **Gap:** the document that is supposed to be the honest ledger carries at least two statements that were never true as written (b, c) and three that are stale after configuration changes (a, d, e).
- **Risk:** the honesty position is the pitch (D14, D21); one investor rerunning one command finds a mismatch and discounts the whole ledger.
- **Corrective action (owner: project lead / QA):** regenerate every numeric line of VALIDATION from the commands it quotes (or mark values with the commit they were observed at); implement the STE check that the text claims (the scan in `scripts/audit.py` A10 can be the start) and report its true result; fix `package.py:57`, add a test that the real `CUSTOMER_DOCS`/`PARTNER_DOCS` lists have zero MISSING, rebuild the sample packages; update the field count or make it computed.

### F-05 — "Confirmed" price status rests on non-vendor pages for 8 of 57 lines — **Minor nonconformity**

- **Criterion:** brief §6 ("what is purchased must be real, priced, and the price confirmation state stated"); brief row 11; catalog vocabulary `confirmed / list / estimate`.
- **Evidence:** `purchasing/parts_catalog.json`: `CLG-CABAC` `vendor_url` is `https://www.digikey.co.uk/en/videos/r/rittal/blue-e-cooling-units-at-a-glance` (a video page) with note "DigiKey listing $9,222.32 with 1 in stock"; `PWR-METER` → alibaba.com; `CMP-GPU-H100` → `marketplace-admin.uvation.com`; `STR-CONT10/20`, `STR-MANDOOR` → `reach.dog` marketplace; `CTL-MGM240P`, `CTL-PLC` → findchips.com although the vendor field says Mouser/TTI. `list` lines `CTL-RCP`, `CTL-REVPI-DIO`, `CTL-REVPI-AIO` have `price_checked: null`; `CTL-REVPI-DIO` has no URL ("not confirmed on a vendor page with URL") yet is not an estimate. `SITE-GENPAD` note is only "Engineering estimate". `VALIDATION.md:44` defines confirmed as "distributor listing seen in search results … not a quote".
- **Gap:** the status word promises a vendor price page; eight lines point elsewhere; three list-price lines have no check date.
- **Risk:** a supplier or investor who clicks finds a video or a marketplace and questions the 60–83 % "confirmed" shares that drive the unit economics.
- **Corrective action (owner: purchasing):** for each of the eight lines replace the URL with the distributor's own product page or downgrade to `list`/`estimate`; set `price_checked` on `list` lines; add to the catalog loader a rule that a `confirmed` URL host must not be in a marketplace/aggregator list (A6d in `scripts/audit.py`) and that `list` requires a URL and date; state a basis for every estimate (SITE-GENPAD).

### F-06 — Stale generation-1 terms and paths outside the history files — **Minor nonconformity**

- **Criterion:** `docs/CONTROLS_HARDWARE_DECISION.md` ("Every document, BOM line, drawing, spec sheet, firmware … updated"); D33–D35; document control.
- **Evidence:** `software/ben_engine/package.py:57` `design/specs/BEN-NODE-v1.md` (missing file, see F-04c); `design/assembly/STE_STYLE.md:31` rule 11 "Node, not sensor board. Gateway, not controller" while every assembly document uses "Pod" (22–25 times each) and "controller" (9–15 times) and never "node"; `docs/contracts/CONTRACT_MANUFACTURING_AGREEMENT.md:114` "Dry contacts only to node"; `design/specs/wiring/gen_wiring.py:446` "Modbus to gateway", `:631` generation-1 tier keys as file names; `docs/TASKS.md:7` T3 "Firmware node + gateway … `pio test -e native`"; `docs/OPERATIONS.md:13` `pio test -e native` (PlatformIO is not installed; the real runner is `make test`); `purchasing/parts_catalog.json:2437, 2459` `BEN-NODE-PCB-v1` / `BEN-NODE-KIT` (marked `[WITHDRAWN]`, applies to no tier — acceptable as history); `purchasing/SOURCING_NOTES.md:53` NEMA 3R price basis (explained).
- **Gap:** the house style guide tells writers to use the words the project retired, and a contract hold-point row uses them.
- **Risk:** a CM reads "node"/"gateway" in the contract and the STE guide and "Pod"/"PLC"/"edge computer" in the drawings and asks which is which.
- **Corrective action (owner: engineering documentation):** update STE_STYLE rule 11 to the generation-2 vocabulary (Pod, BEN Controller / PLC, edge computer) and re-issue it; fix CMA:114, gen_wiring strings and file names, TASKS, OPERATIONS; keep `scripts/audit.py` A5 at zero hard hits.

### F-07 — Compliance matrix carries stale tier codes, a wrong dimension, out-of-order sections and an untraced BOM claim — **Minor nonconformity**

- **Criterion:** brief row 7 ("each applicable code … mapped to a design feature and a verification"); COMPLIANCE §0 finding 2.
- **Evidence:** `docs/COMPLIANCE.md:71` Tiers "20 (optional), 40"; `:83` "Pro: 10 (option), 20, 40"; `:85` "M (and container doors…)"; the file's own key (line 18) defines only 5/30/150/500/2000. Section order lines 188 → 203 (§14) → 223 (§15) → 245 (§13). `:29` "All DX selections in the BOM carry a GWP column and must be < 700" — `purchasing/parts_catalog.json` has `gwp` on one line (`CLG-REFRIG`); `bom.csv` header has no GWP column; `CLG-INROW`, `CLG-CABAC`, `CLG-COND` carry no refrigerant/GWP attribute; no drawing carries an R-513A or GWP note (`grep -l` over 42 SVGs: 0) although `:97` says "charge vs. volume calc on each drawing". `:43` interior 2.55 m (see F-03).
- **Gap:** a design-changing finding (A2L/AIM Act) is not carried into the BOM attributes or the drawings as the matrix says it is; tier codes do not match the key.
- **Risk:** the matrix is the document a plant director "defends to their boss, their insurer and the local inspector" (line 5); an inconsistent tier column or a missing GWP attribute undermines it at the first reading.
- **Corrective action (owner: compliance + purchasing):** add `refrigerant` and `gwp` to every DX/cabinet-AC catalog line and a GWP column to `bom.csv`/`BOM.md`; add the refrigerant/charge note to M-001 for DX tiers; replace the three stale tier cells; renumber §13–§15 in order; make the matrix' tier column a generated field or add a test that its tier tokens are in the key.

### F-08 — Brief row 17 names an artifact that does not exist and CI does not run the stated end-to-end gate — **Minor nonconformity**

- **Criterion:** brief row 17 ("`tests/test_e2e.py` … passes in CI"); basic software quality.
- **Evidence:** `docs/BRIEF.md:80` "`tests/test_e2e.py`"; no such file (`scripts/audit.py` A1: 38/39). The simulated end-to-end is `commissioning-sim-e2e` in `docs/build-contract.json` (fails as written, F-01) and the browser e2e is `tests/e2e/dashboard.spec.mjs` (not run in CI). `.github/workflows/ci.yml` runs only `pytest tests -q --ignore=tests/e2e` and the firmware tests.
- **Gap:** the "Done when" of row 17 is unverifiable: the artifact is misnamed and the gate is not in CI.
- **Risk:** regressions in the config → twin → commissioning → CSV chain reach `main` unnoticed; the brief and the repo disagree on where the proof lives.
- **Corrective action (owner: project lead):** either add `tests/test_e2e.py` that runs `commissioning --sim --fast` and checks the report/CSV/SHA, or correct the brief row to the real paths; add the build contract (or `scripts/audit.py --run`) and `check_links.py` to CI; run the Playwright suite in CI on a schedule if runtime allows.

### F-09 — Field-vocabulary count duplicated in three places and stale in all — **Minor nonconformity**

- **Criterion:** document control (duplicated numbers that drift).
- **Evidence:** `docs/contracts/fields.json` `_meta.field_count: 891` vs 911 entries in `fields`; `docs/VALIDATION.md:48` "369 of 891"; `docs/proposals/README.md:35` "Of the 891 fields"; the eight hardening/BEN 2000 fields were added 2026-11-08 (`_meta.hardening_and_ben2000`) without updating the count.
- **Gap/Risk:** small, but it is the kind of number an investor's analyst checks; it also shows the generator that writes `fields.json` does not maintain its own metadata.
- **Corrective action (owner: contracts tooling owner):** compute `field_count` in the generator; remove the literal from VALIDATION/proposals README or make `known_fields_report` print it.

### F-10 — STE assembly instructions do not meet STE_STYLE rules 2 and 10 — **Minor nonconformity**

- **Criterion:** `design/assembly/STE_STYLE.md` rule 2 (instruction ≤ 20 words) and rule 10 (banned words: check as a verb, follow, …); brief row 2.
- **Evidence:** 21 banned-verb uses and 29 over-length instruction sentences across the five documents (list in Appendix B): `ASSEMBLY-ben150.md:482` / `ben2000:456` / `ben30:488` / `ben5:328` / `ben500:532` "Check the phase rotation"; `ben30:489`, `ben5:329` "check the refrigerant pressures"; `ben5:130` "check the factory charge"; `ben150:253`, `ben2000:146`, `ben500:291` "Check th…" in the glycol step; `ben150:443` et al. CAUTION "Follow the battery manufacturer's shipping instructions"; `ben150:487` et al. "Follow the script st…"; `ASSEMBLY-ben150.md:327` 33-word sentence, `:342` 41 words, `ASSEMBLY-ben5.md:204` 41 words.
- **Gap:** the documents a "worker with no data-center experience" follows break the two rules most tied to that goal; the generator has no check.
- **Risk:** low per instance, but the STE claim is a selling point to CMs and the brief's row-2 acceptance.
- **Corrective action (owner: assembly-documentation owner):** fix the step texts in `gen_assembly.py` ("Examine the phase rotation", "Obey the shipping instructions …", split long steps); add the word-count and banned-word check to the generator so it fails the build; regenerate.

### F-11 — Cybersecurity controls that exist only on paper are not labelled as such; default credential written at install — **Minor nonconformity**

- **Criterion:** evidence standard (*implemented, unverified* vs *deferred*); `docs/CYBERSECURITY.md`; MSA 15.5 promises delivery "to `docs/CYBERSECURITY.md`".
- **Evidence:** `docs/CYBERSECURITY.md:37` "signed A/B images with dm-verity" (Lite), `:70` "A/B image, automatic rollback" (edge), `:73` "SBOM (SPDX) … delivered with each release" — `grep -rn -i "dm-verity|rauc|ostree|swupdate|sbom|spdx" firmware software` returns nothing; no SBOM file in the repository. `firmware/ben-edge/lite/install.sh:17` "key on the RevPi's secure element" vs `CYBERSECURITY.md:37` "RevPi Connect 4 has no TPM". `firmware/ben-edge/lite/install.sh:161` and `install.sh:170` write `password=CHANGE_ME` to `/etc/ben/nas.cred`. `docs/VALIDATION.md` §5 lists the edge image as implemented-unverified without naming A/B, dm-verity or SBOM as not implemented.
- **Gap:** MSA 15.5 contractually promises a document whose A/B-update, dm-verity and SBOM rows have no implementation; a default credential can survive to production.
- **Risk:** a customer security review (or the IEC 62443 assessor the matrix invites) finds promised controls absent; an operator who skips the NAS step ships a known default.
- **Corrective action (owner: controls software owner):** add a column "status" (implemented / documented-only / roadmap) to CYBERSECURITY §2–§5 and mirror it in VALIDATION §5–6; move A/B + dm-verity + SBOM to ROADMAP or implement (a minimal SPDX via `pip-licenses`/`syft` is a day); make `install.sh` refuse to finish while `CHANGE_ME` is present or generate a random credential; verify the RevPi secure-element claim against KUNBUS documentation and make the two files agree.

### F-12 — SQAM scope omits BEN 2000 while its register and the manufacturing strategy include it — **Minor nonconformity**

- **Criterion:** brief row 23 (BEN 2000 in every downstream deliverable); `docs/MANUFACTURING_STRATEGY.md` §3.2 (modular-building manufacturers build BEN 2000); document control.
- **Evidence:** `docs/SQAM.md:8` "Applies to … building or supplying BEN 5, BEN 30, BEN 150 and BEN 500 units"; `:18` "It covers the five tiers"; register §5 includes a BEN 2000 table (44 items, `VALIDATION.md:43`); `docs/SQAM.md:10, 472` cite "IFC drawing set Rev A (2026-11-07)".
- **Gap:** the manual's applicability statement contradicts its own scope sentence and content, and pins a drawing issue that has since changed (F-02).
- **Risk:** a modular-building manufacturer bidding BEN 2000 reads that the SQAM does not apply to them.
- **Corrective action (owner: Schreiber AI quality):** generate the "Applies to" line from `TIER_GEOMETRY`; re-issue with the corrected drawing revision reference (after F-02).

### F-13 — Personal e-mail account recorded in a project document — **Minor nonconformity**

- **Criterion:** audit requirement (j): no personal data beyond the operator's business e-mail.
- **Evidence:** `purchasing/EMAIL_QUEUE.md:30` "Gmail drafts: created in the schreibears@gmail.com account".
- **Gap/Risk:** a personal address in a document that goes into the partner package's purchasing folder (`package.py` copies `purchasing/`); minor privacy exposure and an unprofessional signal to suppliers.
- **Corrective action (owner: operator / purchasing):** replace with "the operator's Gmail account" or the business address; check `package.py` copies do not include the line; add the gmail pattern to the secrets scan (done in `scripts/audit.py` A11 as WARN).

### F-14 — The word "confirmed" over-promises relative to its definition — **Observation**

`docs/VALIDATION.md:44` defines confirmed as "distributor listing seen in search results, not a quote"; `docs/investors/VC_PROPOSITION.md:67–76` and the deck present "confirmed / list / estimate" shares as an auditable number. Recommend a four-level vocabulary (quoted / listed / list-price / estimate) or renaming the current level to `listed`, with the definition printed in `docs/BOM.md` and the deck footnote. Owner: purchasing + investor-materials owner.

### F-15 — Evidence is produced but not stored — **Observation**

Build-control reports live under `.schreiber-ai/` (git-ignored, `.gitignore:4, 15`), the e2e log is not kept (only screenshots), `dist/` is ignored, and the commissioning sample in `docs/reports/` dates from the generation-1 design (2026-11-07). A reviewer must rerun everything to see any evidence. Recommend `docs/evidence/<date>/` with the latest build-control `report.json`, e2e log, `scripts/audit.py` output and one commissioning report per tier, refreshed by the release routine. Owner: release owner.

### F-16 — Failsafe tables agree but are presented three ways — **Observation**

`interlocks.py:444–451` (6 rows, 2 failure columns), `firmware/ben-plc/README.md` (7 rows, adds "PLC in MANUAL" and the Fire/EPO row), `CONTROLS_SPEC.md` §7a/7b (6 rows + edge table; setpoint trim moved to 7b). States match. Recommend generating the two Markdown tables from `FAILSAFE_TABLE` (and extending the Python tuple with the MANUAL column) so they cannot drift. Owner: controls software owner.

### F-17 — Test-quality weaknesses — **Observation**

`tests/test_api.py:252, 273, 286` conditional `pytest.skip` (would hide loss of sim-node coverage; none skipped today); `tests/test_sweeps.py:37–38, 49` assert only `is not None`; `tests/test_package.py` does not assert zero MISSING for the real document lists (allowed F-04c); e2e has no direct check of the I/O test action. Recommend: fail instead of skip when `sim_nodes` is expected; assert numeric ranges in sweeps; add the zero-missing assertion; add an e2e check that drives the I/O test. Owner: test owner.

### F-18 — Honest-limits lists are subsets without saying so — **Observation**

`docs/FAQ.md:45` (6 items) and `docs/BEN_CARE.md` §Honest limits (3 items) are shorter than `docs/VALIDATION.md` §7 (7 items) and do not say they are abridged or point to the full list. Order is consistent where items overlap. Recommend one sentence in each: "Full list, in order, in `docs/VALIDATION.md` §7." Owner: documentation owner.

### F-19 — BEN 2000 schedule acceptance criterion not met as written, but disclosed — **Observation**

Brief row 23 "~52-week order-to-service plan"; `docs/proposals/sample-ben2000-ai_training.md` and `VALIDATION.md:57` show about 71 weeks to turnover with the 48–52-week MV-service lead time; VALIDATION discloses the gap. Recommend either changing the brief row to "utility lead time on the critical path; 52 weeks when the utility delivers in ≤ 26 weeks" or showing both cases in the proposal. Owner: project lead.

### F-20 — CI and the documented gates are not the same thing — **OFI**

`.github/workflows/ci.yml` runs pytest and firmware only; the build contract, `check_links.py`, `scripts/audit.py` and the e2e suite are documented gates not run anywhere automatically; regeneration commands are scattered over five documents. Recommend a `make release-check` (or `scripts/release_check.sh`) that runs the contract, links, audit and generators-with-diff, called from CI. Owner: release owner.

### F-21 — Drawing generation is non-deterministic — **OFI**

Regenerating the 42 sheets changes 46 files although content is identical (`<dc:date>` and matplotlib clip-path ids, Appendix B). Set `metadata={"Date": None}` and `svg.hashsalt` (matplotlib rcParam) so a regeneration with no design change produces no diff; then "regenerate and diff" becomes a usable audit check (C-1). Owner: drawings owner.

### F-22 — Catalog hygiene — **OFI**

Withdrawn generation-1 lines (`CTL-POE-SW`, `CTL-SHT45`, `CTL-ADS1115`, `CTL-DS18B20`, `CTL-PSU24`, `CTL-PCB`, `CTL-MISC`, marked `[WITHDRAWN]`, `applies_to_tiers: []`) remain in `purchasing/parts_catalog.json`; `dist/` and `.schreiber-ai/` hold stale `SAI-BEN20-*` packages and `commissioning-ben20.md`. Move withdrawn lines to a `withdrawn` array or a history file and clean the local build outputs. Owner: purchasing.

## 7. Conclusion

| Question | Answer |
| --- | --- |
| Release-ready for supplier RFQs (price inquiries, e-mails 01–21)? | **Yes, with conditions**: close F-05 (URL/status hygiene) and F-13 before the queue is forwarded; the e-mails themselves are honest and send no drawings. |
| Release-ready to send the build package (drawings, STE, SQAM, QC forms) to a contract manufacturer or integrator? | **No** until F-02, F-03, F-06, F-10 and F-12 are closed and a named checker has signed the drawing set. |
| Release-ready for investor review? | **Yes, with conditions**: close F-01 and F-04 first (the gate must run and the ledger must be true), state F-14's definition where the confirmed share is shown, and add the status column of F-11 so no documented-only control reads as implemented. |

The engineering substance is in better shape than the paperwork around it: the model, twin, commissioning, BOM and economics reproduce exactly; the safety rule is everywhere it should be; the contract chain is internally consistent. The nonconformities are about control of documents and about the ledger keeping pace with a fast refactor (generation 1 → 2 in one day). All Majors are closable without hardware.

## 8. CAPA list

| # | Finding | Action | Owner (role) | Due | Verification |
| --- | --- | --- | --- | --- | --- |
| C-1 | F-01 | Make build-contract commands importable from a clean clone; rerun; store report in repo; fix VALIDATION §1 | Release owner | before investor review | `scripts/audit.py --run` A3 PASS; `report.json` `verified: true` committed |
| C-2 | F-02 | Single revision source for all generators; bump/re-date drawings; regenerate SQAM, QC forms, assembly, wiring, SOW sample; rename wiring files; status "FOR REVIEW" until a checker signs | Design authority (engineering) | before any build package leaves | A13a/A13b PASS; checker name on every INDEX |
| C-3 | F-03 | Correct Art. 645 citations in CONTROLS_SPEC §1 and sheet 05; correct interior height in COMPLIANCE §1 | Engineering + compliance | with C-2 | grep "645" shows only "not invoked"; dimensions equal config |
| C-4 | F-04 | Regenerate VALIDATION numbers; implement the STE check; fix `package.py:57` + add zero-missing test; computed field count | Project lead / QA | before investor review | three random VALIDATION claims reproduce; A10a PASS; `test_package` asserts 0 MISSING |
| C-5 | F-05, F-14 | Re-source 8 URLs or downgrade status; date the `list` lines; add marketplace rule to loader; publish the status definitions | Purchasing | before RFQs are forwarded | A6d/A6e PASS; definition in BOM.md and deck |
| C-6 | F-06 | Update STE_STYLE rule 11, CMA:114, gen_wiring strings/names, TASKS, OPERATIONS | Documentation owner | with C-2 | A5 0 hard hits |
| C-7 | F-07 | GWP/refrigerant attributes on DX lines + BOM column + M-001 note; fix tier cells; renumber sections | Compliance + purchasing | before build package | grep shows GWP on all DX lines; tier tokens in key |
| C-8 | F-08, F-20 | Add `tests/test_e2e.py` or correct the brief; CI runs contract + links + audit | Project lead | next sprint | CI green with new jobs |
| C-9 | F-09 | Computed `field_count`; remove literals | Contracts tooling owner | with C-4 | A7 PASS |
| C-10 | F-10 | Fix step texts; generator fails on rule 2/10 violations; regenerate | Assembly-documentation owner | before build package | A10a PASS, A10b 0 |
| C-11 | F-11 | Status column in CYBERSECURITY; roadmap or implement A/B, dm-verity, SBOM; no default credential | Controls software owner | before first customer security review | grep shows no CHANGE_ME path without enforcement; CYBERSECURITY rows labelled |
| C-12 | F-12 | Generate SQAM "Applies to" from TIER_GEOMETRY; cite corrected drawing rev | Quality | with C-2 | SQAM:8 lists five tiers |
| C-13 | F-13 | Remove personal address | Operator | immediately | A11 PASS |
| C-14 | F-15, F-21, F-22 | Evidence folder; deterministic SVG; catalog cleanup | Release owner / drawings / purchasing | next release | C-1 checklist item passes with empty diff |
| C-15 | F-16, F-17, F-18, F-19 | Generate failsafe tables from code; tighten tests; cross-reference honest-limits lists; align brief row 23 | Respective owners | next release | re-audit |

---

## Appendix A — `scripts/audit.py` output (commit 5c0e57e, 2026-11-08)

```
BEN Engine audit — /home/user/ben_engine
FAIL A1    Brief §5 artifact paths exist (38/39)                                                  | row 17: tests/test_e2e.py
PASS A2    Launch manifest paths exist (24/24)                                                  
PASS A2b   Manifest acceptance_ids exist in build-contract.json                                 
FAIL A3    Build-contract checks runnable as written (static)                                     | commissioning-sim-e2e, sweeps-ben500 call `python3 -m ben_engine.*` with no PYTHONPATH and the package is not installed (pip install -e . or PYTHONPATH=software missing); these checks fail as written
PASS A4    Relative link check                                                                    | 148 markdown files, 131 relative targets checked, 0 broken
FAIL A5    Stale generation-1 references outside history files (5 hard, 15 explained)             | purchasing/parts_catalog.json:2437 [BEN-NODE]; purchasing/parts_catalog.json:2459 [BEN-NODE]; purchasing/SOURCING_NOTES.md:53 [NEMA 3R]; purchasing/email_queue/10-asco-generac-ats-generator.md:14 [NEMA 3R]; software/ben_engine/package.py:57 [BEN-NODE]
PASS A6a   Catalog: confirmed lines carry vendor_url + price_checked (57/57)                    
PASS A6b   Catalog: estimate lines carry a price_source_note (144/144)                          
PASS A6c   Catalog: every line has lead_time_weeks (204/204)                                    
WARN A6d   Catalog: confirmed URLs on marketplaces / aggregators / non-product pages (8)          | STR-CONT10 (reach.dog); STR-CONT20 (reach.dog); STR-MANDOOR (reach.dog); PWR-METER (www.alibaba.com); CLG-CABAC (www.digikey.co.uk); CMP-GPU-H100 (marketplace-admin.uvation.com); CTL-MGM240P (www.findchips.com); CTL-PLC (www.findchips.com)
WARN A6e   Catalog: 'list' lines without vendor_url or price_checked (3)                          | CTL-RCP; CTL-REVPI-DIO; CTL-REVPI-AIO
WARN A7    fields.json covers every template [FIELD] token                                        | tokens in templates 911, fields declared 911, _meta.field_count 891; _meta.field_count is stale (891 vs 911 declared)
PASS A8    Test count in docs matches collected (178)                                             | 178 collected; README/VALIDATION/PROJECT_STATE quote it
PASS A9    Drawing SVG title blocks carry 'ISSUE FOR CONSTRUCTION' and 'Rev A' (42/42)          
WARN A13a  Drawing INDEX 'Checked' field filled (0/5)                                             | IFC status with no checker: design/drawings/ben2000/INDEX.md; design/drawings/ben500/INDEX.md; design/drawings/ben150/INDEX.md; design/drawings/ben30/INDEX.md; design/drawings/ben5/INDEX.md
WARN A13b  Rev A issue dates agree across drawings, SQAM, QC forms, assembly                      | {'design/drawings/gen_drawings.py': '2026-11-08', 'docs/SQAM.md': '2026-11-07', 'design/assembly/QC_FORMS.md': '2026-11-07', 'design/assembly/ASSEMBLY-ben150.md': '2026-11-07'}
FAIL A10a  STE banned words in ASSEMBLY-*.md (21 hits; list from STE_STYLE.md rule 10: 12 words)  | design/assembly/ASSEMBLY-ben150.md:253 'check'; design/assembly/ASSEMBLY-ben150.md:443 'follow'; design/assembly/ASSEMBLY-ben150.md:482 'check'; design/assembly/ASSEMBLY-ben150.md:487 'follow'; design/assembly/ASSEMBLY-ben2000.md:146 'check'; design/assembly/ASSEMBLY-ben2000.md:421 'follow'; design/assembly/ASSEMBLY-ben2000.md:456 'check'; design/assembly/ASSEMBLY-ben2000.md:461 'follow'; design/assembly/ASSEMBLY-ben30.md:449 'follow'; design/assembly/ASSEMBLY-ben30.md:488 'check'; design/assembly/ASSEMBLY-ben30.md:489 'check'; design/assembly/ASSEMBLY-ben30.md:493 'follow'; design/assembly/ASSEMBLY-ben5.md:130 'check'; design/assembly/ASSEMBLY-ben5.md:293 'follow'; design/assembly/ASSEMBLY-ben5.md:328 'check'
WARN A10b  STE instruction sentences over 20 words (29)                                           | design/assembly/ASSEMBLY-ben150.md:327 (21 w); design/assembly/ASSEMBLY-ben150.md:327 (33 w); design/assembly/ASSEMBLY-ben150.md:328 (24 w); design/assembly/ASSEMBLY-ben150.md:329 (24 w); design/assembly/ASSEMBLY-ben150.md:342 (41 w); design/assembly/ASSEMBLY-ben150.md:345 (22 w); design/assembly/ASSEMBLY-ben150.md:345 (22 w); design/assembly/ASSEMBLY-ben2000.md:227 (24 w); design/assembly/ASSEMBLY-ben2000.md:228 (24 w); design/assembly/ASSEMBLY-ben2000.md:229 (24 w); design/assembly/ASSEMBLY-ben2000.md:332 (41 w); design/assembly/ASSEMBLY-ben30.md:339 (22 w) …
WARN A11   Secrets / personal-data scan (1 hits)                                                  | purchasing/EMAIL_QUEUE.md:30 personal gmail address
PASS A12   JSON files parse (18/18)                                                             

Summary: 9 PASS, 7 WARN, 4 FAIL
EXIT=1
```

`python scripts/audit.py --run` (A3 executed; other lines identical):

```
FAIL A3    Build-contract checks runnable as written (executed)  | commissioning-sim-e2e: exit 1: /usr/local/bin/python3: Error while finding module specification for 'ben_engine.commissioning' (ModuleNotFoundError: No module named 'ben_engine'); sweeps-ben500: exit 1: /usr/local/bin/python3: Error while finding module specification for 'ben_engine.sweeps' (ModuleNotFoundError: No module named 'ben_engine'); commissioning-sim-e2e, sweeps-ben500 call `python3 -m ben_engine.*` with no PYTHONPATH and the package is not installed (pip install -e . or PYTHONPATH=software missing); these checks fail as written
Summary: 9 PASS, 7 WARN, 4 FAIL
EXIT=1
```

## Appendix B — Ad-hoc checks and raw observations

**B.1 Build-control run** (`build_control.py run --repo /home/user/ben_engine`): `python-suite` pass, `selector-parity` pass, `firmware-host-tests` pass, `commissioning-sim-e2e` **fail** (exit 1, 15 ms), `sweeps-ben500` **fail** (exit 1, 16 ms); `"verified": false`; run id `72cbb1934f3a4659affa9509bd874b4c`. Earlier run ids in `.schreiber-ai/runs/` (`0e8e0265`, `3fbae4b8`, `623a7490`, `b5f30d32`) all show pass, confirming the earlier environment differed from the repository state.

**B.2 Reproductions**: `bom --all` output identical to `docs/BOM.md`; `unit_economics.py` output identical to `VC_PROPOSITION.md:70–78`; `cfd --tier ben150`: "grid 232x90 @ 0.025 m, 2500 flow steps, runtime 12.66 s, flow_converged=True, Re lattice 69.6 vs real ~53529"; `analysis`: "rack 5 inlet will be 24.4 ± 0.2 °C … 4.5 minutes before the hottest inlet passes 35 °C … UPS 11.8 minutes … recirculation = 0.12 ± 0.00034, envelope_ua_w_k = 49.2 ± 49 (poorly determined), rack_mass_kg = 79.3 ± 0.74, bypass = 0.152 ± 0.0056"; `commissioning --sim --fast`: overall PASS, 10/10 steps, 871 rows, sha256 e80515c2….

**B.3 Generator regeneration**: `gen_sqam.py`, `gen_assembly.py`, `gen_design_basis.py`, `gen_catalog.py`, `gen_wiring.py`, `bom --all`, `unit_economics.py` → `git status --short` empty. `gen_drawings.py` (41 s) → 46 files changed, 16424 insertions, 16640 deletions; `git diff` line classes after masking numbers: only `<dc:date>` and `clip-path="url(#p…)"` ids. Restored with `git checkout -- design/drawings`.

**B.4 fields.json vs templates** (script): 911 distinct `[A-Z0-9_]` tokens in the 11 templates (README excluded; the words FIELD, FIELDS, FIELD_NAME are explanatory text); 911 names in `fields.json`; 0 missing in either direction; `_meta.field_count` = 891.

**B.5 LD clause cross-check** (script): every clause number cited in README §4 found as a paragraph in its file; token counts: MSA {CUSTOMER_LD_RATE_PCT_PER_WEEK 1, LD_GRACE_DAYS 1, CUSTOMER_LD_CAP_PCT 1, LD_CAP_CURE_DAYS 1}; CMA {CM_LD_RATE_PCT_PER_WEEK 2, CM_LD_GRACE_DAYS 2, CM_LD_CAP_PCT 2, CM_COVER_TRIGGER_WEEKS 1}; SUPPLIER_TERMS {SUPPLIER_LD_RATE_PCT_PER_WEEK 2, SUPPLIER_LD_GRACE_DAYS 2, SUPPLIER_LD_CAP_PCT 2, SUPPLIER_COVER_TRIGGER_WEEKS 1}; INTEGRATOR {LD_RATE_PCT_PER_WEEK 1, LD_GRACE_DAYS 1, LD_CAP_PCT 1}; SOW {CUSTOMER_LD_RATE_PCT_PER_WEEK 1, LD_GRACE_DAYS 1, CUSTOMER_LD_CAP_PCT 1}.

**B.6 STE scan** (banned words from STE_STYLE rule 10; "Check:" headings, part lists and "Secure Vault" excluded): 21 hits — ben150:253 check, 443 follow, 482 check, 487 follow; ben2000:146 check, 421 follow, 456 check, 461 follow; ben30:449 follow, 488 check, 489 check, 493 follow; ben5:130 check, 293 follow, 328 check, 329 check, 333 follow; ben500:291 check, 493 follow, 532 check, 537 follow. Instruction sentences > 20 words: 29 (ben150 7, ben2000 4, ben30 7, ben5 4, ben500 7).

**B.7 Tests**: `pytest --collect-only`: analysis 5, api 26, bom 30, calibration 8, cfd 12, commissioning 3, config_gen2 20, interlocks 16, package 3, plc_bridge 6, proposal 16, selector_parity 13, sim_nodes 6, sweeps 5, twin 9 = 178. AST scan: 0 test functions without `assert`/`raises`. `-rs`: 0 skipped.

**B.8 Catalog survey**: 204 lines; status counts estimate 144, confirmed 57, list 3; 104 lines have an empty `vendor_url` (all estimates/list); hosts of confirmed URLs: cdw.com 9, rspsupply.com 8, avendor.com 4, reach.dog 3, zoro.com 2, findchips.com 2, digikey.co.uk 2 (one a video page), others 1 each incl. alibaba.com, marketplace-admin.uvation.com, superarbor.io.

**B.9 Secrets / personal data**: no key/token/private-key patterns; e-mail addresses Ben@SchreiberAI.com ×136, security@schreiberai.com ×3, schreibears@gmail.com ×1 (`purchasing/EMAIL_QUEUE.md:30`); `CHANGE_ME` default in `firmware/ben-edge/install.sh:170`, `lite/install.sh:161`.

**B.10 Stale-reference grep** (patterns ben-node|ben-gateway|Raspberry|Olimex|ESP32|NEMA 3R|BEN Micro|BEN 10/20/40, outside history files): hard hits `software/ben_engine/package.py:57`, `purchasing/parts_catalog.json:2437, 2459`, `purchasing/SOURCING_NOTES.md:53`, `purchasing/email_queue/10-asco-generac-ats-generator.md:14`; 15 further hits in explanatory context (BOM notes "Rating changed from NEMA 3R to NEMA 4X", FAQ rename answer, firmware README history).

## Appendix C — Browser e2e rerun

`bash tests/e2e/run_e2e.sh` rerun 2026-11-08 04:14–04:3x UTC (node playwright 1.63, Chromium 1243, software WebGL): **25/25 checks passed, exit 0**, 0 console errors (log head: `PASS server up — port 35073, modules cfd,calibration,analysis,sweeps,sim_nodes,export,commissioning,bom`; tail: `PASS no uncaught page errors — 0 console errors` / `25/25 checks passed`). The run rewrote `docs/media/screens` and `docs/media/frames`; they were restored with `git checkout -- docs/media` so the committed screenshots are unchanged. This confirms `docs/VALIDATION.md:31`.
