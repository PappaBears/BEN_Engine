# VALIDATION — what was run, what was observed, what was not

Environment: Linux cloud container, Python 3.13.18, Node 22.23, Chromium via Playwright (software WebGL), no hardware, no ESP32 toolchain (download blocked by network policy), vendor websites reachable only through web search/fetch. Dates: 2026-11-07 to 2026-11-08.

Labels: **verified** = run here and observed · **implemented, unverified** = code exists, needs device/credential/service · **simulated** = explicitly fake · **blocked** · **deferred**.

## 1. Automated checks

| Check | Command | Observed |
| --- | --- | --- |
| Python suite | `PYTHONPATH=software python -m pytest tests -q --ignore=tests/e2e` | **113 passed** in 8.7 s (twin, cfd, calibration, analysis, sweeps, sim_nodes, commissioning, bom, selector parity, api, proposal, package, export) |
| Firmware host tests | `cd firmware/ben-node && make test` | **37 tests, 0 failures** (g++ -std=c++17 -Wall -Wextra, zero warnings); `make sim` runs a 10 s online/offline/replay simulation and exits 0 |
| Build contract | `build_control.py run` (skill helper) | python-suite, selector-parity, firmware-host-tests, commissioning-sim-e2e, sweeps-ben40 all **pass** (report under `.schreiber-ai/`, git-ignored) |
| Dashboard e2e | `bash tests/e2e/run_e2e.sh` | see §3 |
| Product page render | `node scripts/shoot_web.mjs` | desktop and 390 px render, selector interactions work, validation error path shown, no horizontal overflow after fix; 404s only for screenshots not yet produced at that time |

## 2. Simulated end-to-end (config → twin → sweeps → commissioning → CSV)

`PYTHONPATH=software python -m ben_engine.commissioning --sim --tier ben20 --yes --out /tmp/r.md`, both normal and `--fast`: **all 10 steps PASS**. Key observed values (BEN 20 preset, 96 kW, 5 racks, rear-door heat exchangers, N+1): 10 inlet probes within 0.5–0.7 K at idle; 38 I/O points, 0 failed; meter vs PDU reconciliation 0.5 %; each of 4 cooling units failed in turn, worst peak inlet 25.5 °C (limit 35 °C); load step hottest inlet 23.7–23.9 °C, rack ΔT 12.9–13.2 K, PUE 1.17; utility loss with cooling off reaches ASHRAE A2 limit after 3.9 min, UPS empty at 11.8 min (thermal is the binding limit); 5/5 alarm paths raised and cleared; CSV 1077–1431 rows with SHA-256 in the report.

`python -m ben_engine.sweeps --tier ben20` and `--tier ben40`: all 6 sweeps PASS.

`python -m ben_engine.cfd --tier ben20`: grid 232 × 90 at 25 mm, flow converged in 2750 steps, 14.6 s; design case recirculation ≈ 0 with containment closed and supply > demand; fan turn-down to 0.9 or one failed unit gives 30–40 % recirculation at the end racks and max inlet 31–32 °C. Lattice Reynolds ≈ 70 vs ≈ 1e5 real: relative tool.

`python -m ben_engine.analysis --tier ben20 --load 1.0 --outdoor 35`: fitter recovers synthetic truth (recirculation 0.12, bypass 0.15 well determined; envelope UA and rack mass weakly identifiable, flagged); prediction "rack 5 inlet 22.3 ± 0.2 °C at 100 % on a 35 °C day; 2.0 min ride-through".

Calibration budgets computed (k = 2): DS18B20 ±0.17 K, SHT45 T ±0.14 K, SHT45 RH ±1.71 %RH (protocol claim 1.5 not met), SDP810 ±0.46 Pa at 12 Pa (claim 0.4 not met), 4–20 mA loop ±0.025 mA (claim 0.02 not met unless loop-calibrated), power class 0.5 ±0.9 % of reading. Left as findings.

## 3. Dashboard (Playwright, Chromium, software WebGL)

`bash tests/e2e/run_e2e.sh` (2026-11-08): **22/22 checks passed, exit 0**, about 13 minutes under software WebGL. Checks: server up with modules; WebSocket live; BEN 20 scene 5 racks / 27 sensors; selector to BEN 40 rebuilds twin and scene (10 racks); invalid configuration shows inline error and disables Apply; BEN Micro renders one cabinet; walkthrough eye height 1.70 m stays inside; cooling fault via UI raises alarm, click selects the unit in 3-D, clear via UI; sweep run and CSV download (105 lines); every panel renders; calibration demo points give gain/offset/U95; guided tour 24 frames with captions; **proposal panel generates a proposal from the current configuration and the HTML is served**; 390 px layout stacks with no horizontal scroll; 0 uncaught page errors.

Screenshots inspected by eye: `docs/media/screens/desktop-exterior-iso.png`, `interior-walkthrough.png`, `alarms.png`, `sweeps.png`, `selector-micro.png`, `selector-ben40.png`, `narrow-390.png`, `live-hot-aisle.png`, `proposal-panel.png`, `web-hero.png`, `web-configure.png`, `web-narrow.png`, `proposal-1.png`, `proposal-2.png`. Fixes made from looking are listed in `docs/PROJECT_NOTES.md`.

Not verified: pointer-lock mouse look (needs a real user gesture), a live gateway connection (no hardware), GPU rendering performance (software WebGL here).

## 4. Generated deliverables

| Deliverable | Command | Observed |
| --- | --- | --- |
| Drawings | `python design/drawings/gen_drawings.py` | 28 sheets (SVG+PNG), 4 INDEX.md, INTERFERENCE_CHECKS.md; red deviation notes: none after the configuration changes; remaining FAILs are informative (NEC 110.26 condition 2 not required, two-row layouts rejected by design) plus BEN 40 rack-top clearance 290 vs 300 mm (resolution printed on sheet) |
| Renders | `python design/renders/gen_renders.py` | 32 stage PNGs + 4 contact sheets; labelled concept renders |
| Assembly | `python design/assembly/gen_assembly.py` | 4 STE documents; 0 instructions over 20 words; banned-word check passes; all item codes reconciled with the catalog |
| SQAM | `python design/gen_sqam.py` | 405 lines; CTQ/CTP register per tier (Micro 27, BEN 10 38, BEN 20 38, BEN 40 39 items) |
| BOM | `python -m ben_engine.bom --all` | Micro 64 lines $135 k (69 % confirmed); BEN 10 90 lines $660 k (81 %); BEN 20 94 lines $1.87 M (79 %); BEN 40 95 lines $4.43 M (83 %). "Confirmed" = distributor listing seen in search results on 2026-11-07, not a quote |
| Proposals | `python -m ben_engine.proposal …` | 4 samples in `docs/proposals/`; BEN 20 healthcare managed: $1.89 M capital, $27 k/yr, 34 weeks to in-service |
| Packages | `python -m ben_engine.package …` | customer and partner zips built; MANIFEST lists missing sources explicitly |
| Decks | `build_presentation.py` | 12 + 12 slides with notes; visual review of the HTML decks **not performed** |
| Demo GIF | `make_demo_gif.py` | 24 real tour frames, 6 s, 4.5 MB |

## 5. Implemented, unverified

- ESP32 HAL and `main.cpp` against real Arduino/ESP-IDF library APIs (never compiled; toolchain download blocked). First `pio run -e olimex_esp32_poe_iso` will need fixes.
- Gateway package on a Raspberry Pi 5 (package names, VLAN config, nftables rules).
- Modbus/SNMP adapters for third-party equipment (interfaces described, not coded).
- Any physical behaviour: thermal time constants, ride-through, fan curves, pressure, acoustics.
- Contract templates (counsel review), compliance edition years listed as unconfirmed in `docs/COMPLIANCE.md` §13.

## 6. Blocked / deferred

- ESP32 cross-build: blocked (network). Greenfield factory study: deferred by decision. 3-D CFD: deferred. UL 508A / FCC listings: need hardware.

## 7. Least accurate, in order

1. Thermal ride-through minutes and recovery times (design-value thermal masses; treat as lower bounds).
2. Envelope UA (not identifiable from indoor data).
3. CFD absolute temperatures and recirculation fractions (2-D, low lattice Reynolds).
4. Calibration placement corrections (literature magnitudes until a traverse is done).
5. Estimate-status prices: CDU, rear-door heat exchangers, dry coolers, generators, 150 kW UPS frame, site civil, labour rates.
6. Assembly time estimates (scaled, not from a labour study) and MTBF (parts-count prediction).
7. Market sizes (vendor research with 2–4× spread; ranges quoted).
