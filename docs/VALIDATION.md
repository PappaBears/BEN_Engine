# VALIDATION — what was run, what was observed, what was not

Environment: Linux cloud container, Python 3.13.18, Node 22.23, Chromium via Playwright (software WebGL), no hardware, no EFR32 / Gecko SDK toolchain (download blocked by network policy), vendor websites reachable only through web search/fetch. Dates: 2026-11-07 to 2026-11-09 (Rev 2 checks in §9).

Labels: **verified** = run here and observed · **implemented, unverified** = code exists, needs device/credential/service · **simulated** = explicitly fake · **blocked** · **deferred**.

## 1. Automated checks

| Check | Command | Observed |
| --- | --- | --- |
| Python suite | `PYTHONPATH=software python -m pytest tests -q --ignore=tests/e2e` | **262 passed** in 41.1 s on 2026-11-09 (Rev 2; adds the Rev 1 frozen fixture and the Rev 2 lineup tests, §9). Generation 2 on 2026-11-08: 198 passed in 20.3 s (twin, cfd, calibration, analysis, sweeps, sim_nodes, commissioning, interlocks, bom, selector parity incl. aliases/hardening, api, proposal, package, export, config generation 2, forward architecture dc800 / dlc_hd incl. JS parity, BOM filters, twin faults, sweeps, commissioning steps 10–11, forward layout and drawings) |
| Firmware host tests (BEN Pod core) | `cd firmware/ben-pod && make test` | **37 tests, 0 failures** (g++ -std=c++17 -Wall -Wextra, zero warnings); `make sim` runs a 10 s online/offline/replay simulation and exits 0 |
| Build contract | `build_control.py run` (skill helper) | eight checks: python-suite, selector-parity, firmware-host-tests, commissioning-sim-e2e, sweeps-ben500, sim-e2e-pytest, links, audit-mechanical. Commands carry their own `PYTHONPATH` so they run from a clean clone (audit F-01). Latest report stored at `docs/audit/evidence/build-report.json` |
| Dashboard e2e | `bash tests/e2e/run_e2e.sh` | see §3 |
| Product page render | `node scripts/shoot_web.mjs` | desktop and 390 px render, selector interactions work, validation error path shown, no horizontal overflow after fix; 404s only for screenshots not yet produced at that time |

## 2. Simulated end-to-end (config → twin → sweeps → commissioning → CSV)

`PYTHONPATH=software python -m ben_engine.commissioning --sim --tier ben150 --yes --out /tmp/r.md`, both normal and `--fast`: **all 12 steps PASS** (steps 10 and 11, the forward-architecture steps, are skipped with the stated reason on this AC / rear-door unit; on the forward prototype configuration `dc800 + dlc_hd` they run and pass: leak-to-isolation 8.0 s, IMD alarm 5 s on both poles, bus 771–880 V on battery). Key observed values (BEN 150 preset, 96 kW, 5 racks, rear-door heat exchangers, N+1): 10 inlet probes within 0.5–0.7 K at idle; 38 I/O points, 0 failed; meter vs PDU reconciliation 0.5 %; each of 4 cooling units failed in turn, worst peak inlet 25.5 °C (limit 35 °C); load step hottest inlet 23.7–23.9 °C, rack ΔT 12.9–13.2 K, PUE 1.17; utility loss with cooling off reaches ASHRAE A2 limit after 3.9 min, UPS empty at 11.8 min (thermal is the binding limit); 5/5 alarm paths raised and cleared; CSV 1077–1431 rows with SHA-256 in the report.

`python -m ben_engine.sweeps --tier ben150` and `--tier ben500`: all 6 sweeps PASS.

`python -m ben_engine.cfd --tier ben150`: grid 232 × 90 at 25 mm, flow converged in 2500 steps, 12.5 s; design case recirculation ≈ 0 with containment closed and supply > demand; fan turn-down to 0.9 or one failed unit gives 30–40 % recirculation at the end racks and max inlet 31–32 °C. Lattice Reynolds ≈ 70 vs ≈ 1e5 real: relative tool.

`python -m ben_engine.analysis --tier ben150 --load 1.0 --outdoor 35`: fitter recovers synthetic truth (recirculation 0.12, bypass 0.15 well determined; envelope UA and rack mass weakly identifiable, flagged); prediction "rack 5 inlet 24.4 ± 0.2 °C at 100 % on a 35 °C day; 4.5 min ride-through (rear-door cooling preset; the earlier 22.3 °C / 2.0 min figure was for the retired in-row preset)".

Calibration budgets computed (k = 2): DS18B20 ±0.17 K, SHT45 T ±0.14 K, SHT45 RH ±1.71 %RH (protocol claim 1.5 not met), SDP810 ±0.46 Pa at 12 Pa (claim 0.4 not met), 4–20 mA loop ±0.025 mA (claim 0.02 not met unless loop-calibrated), power class 0.5 ±0.9 % of reading. Left as findings.

## 3. Dashboard (Playwright, Chromium, software WebGL)

`bash tests/e2e/run_e2e.sh` (2026-11-08, generation 2): **25/25 checks passed, exit 0**. Checks include five presets with the hardening select, BEN 500 switch, BEN 5 cabinet, BEN 2000 hall (48 racks in 4 rows, 2 transformers, 3 generators, 7 dry coolers, 8 fan walls, H3 plinth and vestibule), cooling fault and alarm, sweep CSV download, every panel, calibration, guided tour frames, hover tooltips with BOM part and live values, proposal generation, 390 px layout, 0 uncaught errors.

Screenshots inspected by eye: `docs/media/screens/desktop-exterior-iso.png`, `interior-walkthrough.png`, `alarms.png`, `sweeps.png`, `selector-ben5.png`, `selector-ben500.png`, `narrow-390.png`, `live-hot-aisle.png`, `proposal-panel.png`, `web-hero.png`, `web-configure.png`, `web-narrow.png`, `proposal-1.png`, `proposal-2.png`. Fixes made from looking are listed in `docs/PROJECT_NOTES.md`.

Not verified: pointer-lock mouse look (needs a real user gesture), a live BEN Controller connection (no hardware), GPU rendering performance (software WebGL here).

## 4. Generated deliverables

| Deliverable | Command | Observed |
| --- | --- | --- |
| Drawings | `python design/drawings/gen_drawings.py` | Rev C issued for review on 2026-11-08 (design change DC-001: BEN 5 cabinet air conditioner to the R-513A 5.5 kW variant); Rev B was checked by Ben Schreiber and issued for construction the same day and is unchanged for BEN 30/150/500/2000. Rev C becomes IFC when the checker signs in `design/REVISION.json`; 5 tiers; BEN 2000 adds A-000 site plan and per-module A-001/A-002 sheets (42 sheets total, SVG+PNG), INDEX.md per tier, INTERFERENCE_CHECKS.md (BEN 2000 rows: no FAIL); red deviation notes: none after the configuration changes; remaining FAILs are informative (NEC 110.26 condition 2 not required, two-row layouts rejected by design) plus BEN 500 rack-top clearance 290 vs 300 mm (resolution printed on sheet) |
| Renders | `python design/renders/gen_renders.py` | 40 stage PNGs + 5 contact sheets (8 stages × 5 tiers); labelled concept renders |
| Assembly | `python design/assembly/gen_assembly.py` | 5 STE documents (one per tier) with CTQ cards and QC forms; the generator's built-in check reports 0 banned-word hits and 0 step sentences over 20 words across 654 numbered steps and fails generation otherwise (audit F-10); all item codes reconciled with the catalog |
| SQAM | `python design/gen_sqam.py` | 472 lines; CTQ/CTP register per tier (BEN 5 32, BEN 30 42, BEN 150 42, BEN 500 43, BEN 2000 44 items) |
| BOM | `python -m ben_engine.bom --all` | BEN 5 65 lines $132 k (60 % confirmed); BEN 30 92 lines $666 k (80 %); BEN 150 104 lines $1.89 M (79 %); BEN 500 105 lines $4.45 M (83 %); BEN 2000 94 lines $40.4 M (73 %). "Confirmed" = distributor listing seen in search results on 2026-11-07/08, not a quote |
| Proposals | `python -m ben_engine.proposal …` | 5 samples in `docs/proposals/` (one per tier); BEN 150 healthcare managed: $1.89 M capital, $27 k/yr, 34 weeks to in-service |
| Packages | `python -m ben_engine.package …` | customer package 22 files, partner package 21 files, 0 missing after the BEN-POD spec path fix (audit F-04c); zips built; MANIFEST lists per-document unfilled fields |
| Contract pre-fill | `proposal.known_fields_report` | of the 911 vocabulary fields filled from a proposal (BEN 150 healthcare sample); remaining fields belong to later stages (commissioning report 128, turnover 63, CRM 62, change order 59, QC forms 24, counsel 8). MSA draft has 15 fields left (customer identity, arbitration venue); SOW draft 47 |
| Decks | `build_presentation.py` then `scripts/brand_deck.py` | Rev 2 (2026-11-09): 16 (product) + 16 (investor) slides with notes, brand v2 theme; slide 1 and the Density slide of each deck rendered with Playwright at 1280 × 720 and inspected (§9). Rev 1: 14 + 13 slides, inspected 2026-11-08 (`docs/media/screens/deck-*.png`) |
| Demo GIF | `make_demo_gif.py` | 24 real tour frames, 6 s, 4.5 MB |

## 4a. Generation 2 (power-based tiers, BEN 2000, hardening) — observed 2026-11-08
- Configuration model: aliases micro/ben10/ben20/ben40 resolve; all 5 tiers × 8 profiles × 4 climates produce valid presets (test_config_gen2, 20 tests).
- BEN 2000 preset (ai_training, hot_arid, 1,600 kW, 27 racks, N+1, H2): 12.47 kV service, 2 × 2,500 kVA transformers, 2 × 1,937 kVA UPS strings, 296 kWh LFP, 3 × 1,250 kW generators, 7 CDUs, PUE 1.134, gross mass about 95 t. Twin, sweeps (6/6), commissioning (10/10, 102 Pods) and CFD (3.7 s) run for the hall.
- Hardening: H1/H2/H3 selectable in the website and dashboard; H2/H3 catalog lines (9/19) priced as estimates; envelope mass adder applied; compliance and maintenance rows written.
- Unit economics (28 % margin): BEN 2000 sell price about $56.1 M all modules, $16.4 M infrastructure-only (about $10,200 per kW IT), against $10,000–13,000 per kW for a traditional 1–5 MW build (cited).
- Not verified: any BEN 2000 physical value (module mass, water use, utility lead time, noise), prefabricated-module pricing, MV equipment lead times (48–52 weeks carried; proposal shows ~71 weeks to turnover versus the 52-week target), hardening vendor pricing, ballistic/shielding integration with the IP66 envelope.

## 5. Implemented, unverified

- EFR32MG24 HAL (`hal_efr32`) and `main.cpp` against the real Gecko SDK / OpenThread APIs (never compiled; toolchain not available). The first build for the MGM240P will need fixes; Secure Vault provisioning and attestation have not run on silicon.
- Edge computer image on an OnLogic Karbon 400 (TPM measured boot, LUKS sealing, OTBR with two RCPs, package names, VLAN config, nftables rules) and the Revolution Pi image for BEN Controls Lite.
- Cybersecurity controls split by status in `docs/CYBERSECURITY.md` (Status column, 2026-11-08): implemented in code or config — nftables default-deny, four-listener Mosquitto with mTLS and per-Pod ACL, unit PKI, TPM 2.0 + LUKS (Pro), outbound-only WireGuard, nightly backup, Pod `attest` op and signed-OTA path in `hal_efr32`, PLC project CRC in the register map, Python-side SPDX SBOM (`scripts/sbom.py`), installers that refuse placeholder credentials; **documented only** — dashboard roles/TOTP/HTTPS, edge-side attestation verification, security log/SIEM, switch ACLs, SNMP v3, PCR baseline check; **roadmap** — signed A/B images with dm-verity (edge and Lite), RevPi TPM enrolment, Pod-firmware and PLC SBOMs. Nothing in that file is hardware-verified.
- PLCnext project (interlocks, watchdog relay) on an AXC F 2152; UL 508A panel build; FCC Part 15 B test of the assembled Pod.
- Modbus/SNMP adapters for third-party equipment (interfaces described, not coded).
- Any physical behaviour: thermal time constants, ride-through, fan curves, pressure, acoustics.
- Contract templates (counsel review), compliance edition years listed as unconfirmed in `docs/COMPLIANCE.md` §16; UL 752 / ASTM F3038 / MIL-STD-188-125-1 / ASHRAE 188 editions from memory.
- BEN 2000 physical design values (module mass, slab, water use 2–8 m³/day per 1,000 kW, noise distances, utility lead time 26–52 weeks) are engineering estimates from public rules of thumb, not vendor data.

## 6. Blocked / deferred

- EFR32 build: blocked (toolchain). Controls hardware (PLC, edge computer, Pods) priced, not purchased. Greenfield factory study: deferred by decision. 3-D CFD: deferred. UL 508A / FCC listings: need hardware.

## 7. Least accurate, in order

1. Thermal ride-through minutes and recovery times (design-value thermal masses; treat as lower bounds).
2. Envelope UA (not identifiable from indoor data).
3. CFD absolute temperatures and recirculation fractions (2-D, low lattice Reynolds).
4. Calibration placement corrections (literature magnitudes until a traverse is done).
5. Estimate-status prices: CDU, rear-door heat exchangers, dry coolers, generators, 150 kW UPS frame, site civil, labour rates.
6. Assembly time estimates (scaled, not from a labour study) and MTBF (parts-count prediction).
7. Market sizes (vendor research with 2–4× spread; ranges quoted).

## 8. Audit trail
An independent internal audit (`docs/audit/AUDIT_REPORT_2026-11-08.md`, 22 findings, 4 major) was run against this ledger on 2026-11-08. Corrective actions and their closure status are recorded in `docs/audit/CAPA_LOG.md`; the mechanical checks are rerun by `python scripts/audit.py` (also in CI) and the evidence of the latest run is stored under `docs/audit/evidence/`.

## 9. Rev 2 (2026-11-09) — what was run for the new lineup

Rev 2 adds BEN 1 (rack10, cab12), BEN 300 and BEN 700 (planned as BEN 1000, renamed by fit, `docs/REV2_DECISION.md` §2a). Everything below is simulation or generated output; **no Rev 2 hardware exists**. Rows for the Rev 2.A drawing set are added by the design work.

| Check | Command | Observed |
| --- | --- | --- |
| Python suite | `PYTHONPATH=software python -m pytest tests -q --ignore=tests/e2e` | **262 collected, 262 passed** in 41.1 s |
| Rev 1 frozen | `tests/test_rev1_frozen.py` against `tests/fixtures/rev1_presets.json` | **267 Rev 1 configurations** (config, derived values byte-identical and BOM totals identical) recompute exactly under the Rev 2 code; Rev 1 sample-proposal configs reproduce; the `rev1` lineup rejects Rev 2 tiers; `lineup` missing or `rev1` loads as Rev 1 (`docs/REVISION_POLICY.md` rule 3) |
| Rev 2 lineup | `tests/test_rev2_lineup.py` (18 test functions, parametrised) | every Rev 2 preset valid for every profile and climate; `ben1000` → `ben700` alias and lineup loading; BEN 1 forms and sizing; dense tiers fit with real footprints and names follow power; dense validation rules; Rev 2 BOM totals and lines; `docs/DENSITY.md` current; sweeps, twin faults, CFD within 60 s, commissioning and proposals on the new tiers. 2N step-down observed by CLI: BEN 300 155 kW, BEN 700 400 kW |
| Sweeps | `python -m ben_engine.sweeps --tier ben1` / `ben300` / `ben700` | BEN 1 3/3 PASS (load step, utility-loss ride-through 12.5 min vs 10 min configured, outdoor sweep); BEN 300 7/7 PASS; BEN 700 7/7 PASS (incl. CDU pump failover: standby within 6 s, loop ΔT peak 10.1 K vs 10 K design) |
| Commissioning (simulation) | `python -m ben_engine.commissioning --sim --tier <t> --yes --fast` | **12/12 steps PASS** on BEN 1, BEN 300 and BEN 700. BEN 1: steps 10–11 skipped with the reason (office air, AC). BEN 300 / BEN 700: leak-to-isolation 8.0 s (limit 15 s), 5/5 alarm paths, UPS empty at 13.0 / 11.3 min; step 11 (DC bus) skipped on AC |
| CFD | `python -m ben_engine.cfd --tier <t>` | BEN 1 grid 13 × 12, 0.64 s; BEN 300 grid 232 × 90, 10.4 s; BEN 700 grid 239 × 46, 4.6 s; all converged; recirculation index ≤ 0.035 (BEN 1, open containment) and ≤ 0.005 (dense, closed). Relative tool, as in §2 |
| Selector (browser) | product-page / dashboard selector checks for the Rev 2 tiers (UI work) | **13/13** reported by the lineup work; screenshots `docs/media/screens/selector-ben1-rack10.png`, `selector-ben1-cab12.png`, `selector-ben700.png`. Not re-run in this documentation pass |
| Decks | `build_presentation.py` + `scripts/brand_deck.py` | Both decks rebuilt; slide 1 and the Density slide of each rendered and looked at |

**Honest limits of the Rev 2 numbers** (from the lineup engineer; each stays an estimate until a datasheet, a quote or the lighthouse replaces it):

1. **Fan coil 20 kW per 300 mm on the 18 °C trim loop** is a design value, not a datasheet figure (checks I-D10 depend on it).
2. **Galaxy VL UPS masses** (900 kg assumed) and **200 kW per Galaxy lithium battery cabinet** are inferred, not read from the manual.
3. **UL 9540A large-scale fire test data** for the Galaxy lithium cabinets was not obtained; without it the cabinets cannot stand side by side (I-D14) and the battery moves to an external enclosure.
4. **GB300 NVL72 acceptance of 480Y/277 V** at the rack power shelves is unverified.
5. **APC NetShelter CX Mini 12U 1.6 kW** extraction rating (cab12, I-B6) is unverified.
6. **SMTL2200 runtime** (cab12, 11.5 min estimated) is unverified; SMTL1000 runtime is from reseller listings.
7. **BEN 1 noise** (45–47 dBA at 1 m) is a source-level estimate (+15 dB per decade of power, cabinet insertion loss), not a measurement; E21 replaces it.
8. **Rack-top clearance 254 mm** against the 250 mm rule (I-D8) is marginal: a taller rack or a top-entry fitting breaks it.
9. **GB300 rack price is an analyst estimate**, so the BEN 300 and BEN 700 all-modules BOMs are about 97–98 % estimate (`docs/rev2/UNIT_ECONOMICS.md`); the infrastructure-only figures (24.6 % / 26.4 % confirmed listings excluding compute, `docs/rev2/BOM.md`) are the ones to quote.
10. **Liquid loop volume** is not computed by the configuration (`docs/SITE_REQUIREMENTS.md` §15).

Sources: [`docs/DENSITY.md`](DENSITY.md), [`docs/rev2/BOM.md`](rev2/BOM.md), [`docs/rev2/UNIT_ECONOMICS.md`](rev2/UNIT_ECONOMICS.md), [`docs/proposals/rev2/README.md`](proposals/rev2/README.md).
