# BEN Engine Rev 2 — release notes

**Product revision:** Rev 2 · **Date:** 2026-11-09 · **Decision record:** `docs/REV2_DECISION.md` · **Revision rules:** `docs/REVISION_POLICY.md` · **Previous revision:** Rev 1, frozen (`releases/REV1.md`, branch `release/rev1`) · **Drawing set starts at:** Rev 2.A

Rev 2 is a once-over of a base that works, in the operator's words: "the base is good, we just need a once-over". It applies the Schreiber AI brand package v2, adds the low end (BEN 1 mini racks for tiny businesses) and the dense end (BEN 300 and BEN 700, liquid-first), and funds the hardware proof with a USD 5 M revamp program. Nothing from Rev 1 was deleted.

## 1. What changed from Rev 1

| Area | Rev 1 | Rev 2 | Where |
| --- | --- | --- | --- |
| **Brand** | Brand kit v1.1 (amber used for accents and status) | **Brand package v2 applied**: "BEN Engine, by Schreiber AI"; Night Navy ground, Signal Blue mark and links, Safety Amber on the primary button only, separate status colours; Archivo + IBM Plex; the **data plate band** on the hardware, drawings, proposals, slides, dashboard footer and data sheets; thermal ramp for heat maps | `brand/v2/`, `web/`, `dashboard/`, `docs/contracts/`, both decks |
| **Lineup, low end** | BEN 5 (2–5 kW outdoor cabinet) was the smallest | **BEN 1** (new): indoor mini rack, rack10 (10-inch 8U, ≤ 0.6 kW) or cab12 (19-inch 12U sound-damped, ≤ 1.5 kW), 120 V plug-in, office air, built in-house | `software/ben_engine/config.py`; `docs/COMPLIANCE.md` §18; `docs/SITE_REQUIREMENTS.md` §15; `docs/PROCESS_FLOW.md` §6; `docs/MANUFACTURING_STRATEGY.md` §12 |
| **Lineup, dense end** | BEN 150 (20 ft, 50–150 kW, rear-door) and BEN 500 (40 ft, 150–500 kW, DLC) | **BEN 300** (new, 20 ft, 150–300 kW, 2 racks) and **BEN 700** (new, 40 ft, 400–700 kW, 5 racks; named BEN 1000 at decision and renamed by fit, `docs/REV2_DECISION.md` §2a; key `ben1000` loads as `ben700`), liquid-first; BEN 150 and BEN 500 carried unchanged for existing quotes | `config.py`; `docs/COMPLIANCE.md` §19; `docs/DENSITY.md` |
| **Cooling defaults** | `dlc_hd` (W45 high-density liquid) was a forward study option | **Liquid-first default on the dense tiers**: `dlc_hd` is the default cooling on BEN 300 and BEN 700 (W45 secondary loop, row CDUs N+1, ≤ 10 % air residual, heat-reuse port); E18–E20 are mandatory on every dense unit | `config.py`; `docs/TEST_GUIDE.md`; `docs/MAINTENANCE.md` §11 |
| **800 VDC** | `dc800` study option | Unchanged: **still a study option**, now behind the revamp program's gated DC test cell | `docs/FORWARD_ARCHITECTURE_DECISION.md`; `docs/programs/REV2_REVAMP_PROGRAM.md` line 4 |
| **BEN 2000 (amendment 2026-11-09, `docs/REV2_DECISION.md` §2b)** | Prefabricated hall, 48 racks × 33 kW, `dlc_cdu`, 3.97 kW/m² of hall footprint | **Three BEN 700 modules on a shared yard**: preset 2,000 kW in 15 racks (3 × 5 × 133.3 kW, `dlc_hd`, N+1 inside every module; verified maximum 3 × 705 = 2,115 kW), 22.43 kW/m² of module footprint, 3.36 kW/m² of fenced yard, 2.35 kW/m² of site with the two 6.1 m lanes; 12.47 kV service, 15 kV 4-way switchgear, one 1,000 kVA pad-mount transformer and one heat-rejection skid per module; yard checks I-K1..I-K24 (2 STUDY: I-K6 fire separation if the AHJ classes the modules as buildings, I-K11 utility clearance at pad-mount doors). Priced from catalog estimates: $98,184,892 with the reference GB300-class compute, $8,128,721 infrastructure only (28 % margin). The Rev 1 hall stays for `lineup: rev1` unchanged; the Rev 2.A hall sheets are kept in `design/drawings/rev2/ben2000/superseded-hall-2.A/` | `config.py` (`REV2_GEOMETRY`, `cluster_yard`, `Config._derived_cluster`); `design/layout.py` (`_resolve_cluster`); `design/drawings/rev2/ben2000/` (A-000, A-001, E-001; change register R2-05); `docs/DENSITY.md`; `docs/rev2/BOM-ben2000.md` |
| **Density metrics** | Not reported | kW per rack, kW per m² of footprint, kW per m³, kW per tonne for every tier, against the sourced competitor table | `docs/DENSITY.md` |
| **Controls** | BEN Controls Lite (RevPi) and Pro (PLCnext + edge computer) | **BEN Controls Mini** added for BEN 1: the BEN Care software stack on the unit's own small controller with one BEN Pod; Lite and Pro unchanged | `config.py`; `docs/CONTROLS_HARDWARE_DECISION.md` |
| **Versioned artifacts** | Single locations | Rev 2 writes to versioned locations; Rev 1 locations frozen: drawings `design/drawings/rev2/<tier>/`, renders `design/renders/rev2/<tier>/`, assembly `design/assembly/rev2/`, BOMs `purchasing/rev2/` and `docs/rev2/BOM-*.md`, sample proposals `docs/proposals/rev2/` | `docs/REVISION_POLICY.md` rule 2 |
| **Revision policy** | Not written | "We don't delete, we only save the updated revs": two levels (product Rev N, document Rev N.letter), supersede-don't-overwrite, release records with hashes, audit check that every released file still exists | `docs/REVISION_POLICY.md` |
| **Budget** | R&D Program 2027–2028, USD 5 M core / 10 M full, 24 months | **USD 5 M revamp program, 18 months, six gates**; the R&D and forward programs are superseded for budgeting and kept as workstream detail | `docs/programs/REV2_REVAMP_PROGRAM.md` |
| **Risks** | R01–R40 | R41–R52 added (BEN 1 plain-language risks; dense-tier risks); `web/assets/risks.json` gains a `tiers` array on every risk | `docs/RISK_REGISTER.md` |
| **Tests and acceptance** | E1–E20 | E21–E24 (BEN 1 bench and handover), E25 (single-rack isolation on dense tiers) | `docs/TEST_GUIDE.md` |
| **Investor and product material** | Rev 1 lineup, R&D program as use of funds | Rev 2 lineup slide, Density slide, "Mini racks: AI for tiny businesses" slide, USD 5 M revamp as use of funds | `docs/investors/`, `docs/presentation/` |

## 2. What did not change

- **The configuration model is the base model.** One schema and one set of sizing rules still drive drawings, BOM, twin, CFD, commissioning, proposal and the website.
- **BEN 5, BEN 30, BEN 150 and BEN 500** keep their Rev 1 sizing, presets, prices and drawings (Rev C, issued for review; Rev B IFC for the non-BEN 5 tiers). They are carried, not redesigned. **BEN 2000** keeps its Rev 1 hall for `lineup: rev1` (sizing, presets, prices and drawings unchanged, pinned by `tests/test_rev1_frozen.py`); in `lineup: rev2` it is the BEN 700 cluster (§2b, row above). A configuration saved with `lineup: rev2` for the hall (48 racks, `dlc_cdu`) no longer validates: load it as `rev1`.
- **Hardening H1/H2/H3**, NEMA 4X / IP66 on every outdoor tier.
- **Third-party manufacturing first** for every tier except BEN 1.
- **The commissioning script, twin, BEN Care, BEN Pod and BEN Mesh**: same protocol, same steps; Rev 2 adds steps and experiments, removes none.
- **Honesty rules**: every number is measured, sourced or labelled as an estimate; no "up to" numbers; 800 VDC and every density figure for the new tiers stay "design value" until the lighthouse units measure them.
- **The contracts** keep their clauses; Rev 2 changes headers, footers and the revision field.

## 3. Compatibility

| Case | Behaviour |
| --- | --- |
| A saved Rev 1 configuration (JSON without a `lineup` field, or `lineup: "rev1"`) | Loads as **`rev1`** and computes exactly the numbers it computed when it was quoted (`docs/REVISION_POLICY.md` rule 3); tests pin the Rev 1 preset numbers (`tests/fixtures/rev1_presets.json`) |
| Generation-1 keys (`micro`, `ben10`, `ben20`, `ben40`) | Still load through the alias map, as in Rev 1 |
| A new configuration | Defaults to `lineup: "rev2"`; BEN 1, BEN 300 and BEN 700 are only selectable in `rev2` |
| A configuration saved with the working key `ben1000` | Loads as `ben700` through the alias map |
| Rev 1 drawings, renders, assembly instructions, BOMs and sample proposals | Unchanged at their Rev 1 paths; Rev 2 versions are written beside them |
| Rev 1 customer-facing documents that Rev 2 rewrote | Copied first to `archive/rev1/` (README, FAQ, VC proposition, both decks with speaker notes, compliance, risk register, site requirements, maintenance, test guide, process flow, manufacturing strategy, both programs, the Rev 1 website) |
| Any Rev 1 file exactly as released | `git show origin/release/rev1:<path>` |

## 4. Where each Rev 2 artifact lives

| Artifact | Path |
| --- | --- |
| Decision record | `docs/REV2_DECISION.md` |
| Revision policy | `docs/REVISION_POLICY.md` |
| These release notes | `docs/rev2/RELEASE_NOTES.md` |
| Density metrics | [`docs/DENSITY.md`](../DENSITY.md) |
| Rev 2 BOMs (per tier) | [`docs/rev2/BOM.md`](BOM.md) (summary), `docs/rev2/BOM-*.md`, `purchasing/rev2/` |
| Rev 2 unit economics | [`docs/rev2/UNIT_ECONOMICS.md`](UNIT_ECONOMICS.md) |
| Rev 2 drawings, renders, assembly | `design/drawings/rev2/<tier>/`, `design/renders/rev2/<tier>/`, `design/assembly/rev2/` |
| Rev 2 sample proposals | [`docs/proposals/rev2/README.md`](../proposals/rev2/README.md) |
| Open operator questions | [`docs/rev2/OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) |
| USD 5 M revamp program | `docs/programs/REV2_REVAMP_PROGRAM.md` |
| Compliance for new tiers | `docs/COMPLIANCE.md` §18 (BEN 1), §19 (BEN 300 / BEN 700) |
| Site requirements for new tiers | `docs/SITE_REQUIREMENTS.md` §15 |
| Maintenance for new tiers | `docs/MAINTENANCE.md` §10 (BEN 1), §11 (dense) |
| Acceptance experiments | `docs/TEST_GUIDE.md` E21–E25 |
| Process paths | `docs/PROCESS_FLOW.md` §6 (BEN 1), §7 (dense) |
| In-house BEN 1 build | `docs/MANUFACTURING_STRATEGY.md` §12 |
| Risks | `docs/RISK_REGISTER.md` R41–R52; `web/assets/risks.json` |
| Brief rows | `docs/BRIEF.md` §5 rows 27–35 and §8.1 |
| Brand masters and source | `brand/v2/` |
| Investor proposition and decks | `docs/investors/VC_PROPOSITION.md`, `docs/investors/deck/`, `docs/presentation/` |
| Rev 1 archive | `archive/rev1/`, `releases/REV1.md`, branch `release/rev1` |

## 5. Rev 2 at a glance (values from the configuration)

| Tier | Enclosure | IT kW (nominal max) | Racks | kW per rack | kW per m² of footprint | Gross mass |
| --- | --- | --- | --- | --- | --- | --- |
| BEN 1 rack10 | 10-inch 8U desk / shelf rack | 0.6 | 1 | 0.6 | 8.21 | 38 kg |
| BEN 1 cab12 | 19-inch 12U sound-damped cabinet (APC NetShelter CX Mini 12U class, ~550 mm usable depth: short-depth servers only) | 1.5 | 1 | 1.5 | 2.29 | 136 kg at the 1.1 kW preset, 176 kg at 1.5 kW |
| BEN 300 | 20 ft module, liquid-first | 300 (2 × 155 = 310 kW verified maximum) | 2 | 150 | 20.31 | 9.41 t |
| BEN 700 (renamed from BEN 1000) | 40 ft module, liquid-first, all-in-one | 700 (5 × 141 = 705 kW verified maximum) | 5 | 140 | 23.55 | 19.3 t |

Presets: profile `ai_inference` / `ai_training`, climate `temperate`, lineup `rev2` (`docs/DENSITY.md`). The 40 ft target of 1,000 kW did not fit the interference checks, so under the rule in `docs/REV2_DECISION.md` §2 the tier carries the power that fits: **BEN 700** (amendment §2a); the key `ben1000` loads as `ben700`. BEN 300 is limited by row length (5,350 of 5,400 mm usable), BEN 700 by power gear (5.0 m of the 11.5 m usable row). Profiles with 2N redundancy (healthcare, public sector) step down to **155 kW** on BEN 300 and **400 kW** on BEN 700. BEN 1 at full load: heat to room 649 W (rack10), 1,177 W (cab12 at 1.1 kW), 1,599 W (cab12 at 1.5 kW); estimated 45–47 dBA at 1 m; UPS APC SMTL1000 (rack10) / SMTL2200 (cab12); 120 V on a dedicated 15 A / 20 A circuit.

Detail: [docs/DENSITY.md](../DENSITY.md) (generated density table and interference checks) · [docs/rev2/BOM.md](BOM.md) (Rev 2 BOM summary) · [docs/rev2/UNIT_ECONOMICS.md](UNIT_ECONOMICS.md) (sell prices) · [docs/proposals/rev2/README.md](../proposals/rev2/README.md) (sample proposals) · open decisions: [docs/rev2/OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

## 6. Known limits

1. **No Rev 2 hardware exists yet.** BEN 1, BEN 300 and BEN 700 numbers are design values from the configuration model; the BEN 1 and BEN 300 lighthouse units in the revamp program measure them. BEN 700 is engineered and quotable but not built. The unverified inputs behind them (fan-coil rating, Galaxy VL masses, UL 9540A data, GB300 480Y/277 V acceptance, CX Mini and SMTL2200 ratings, the noise model, the 254 mm rack-top clearance, the GB300 rack price) are listed in `docs/VALIDATION.md` §9.
2. **800 VDC is a study**, gated behind a DC test cell that is itself an option in the program; no 150–500 kW 800 VDC distribution is listed in November 2026 (`docs/research/STATE_OF_THE_ART_2026.md` §0 fact 3).
3. **Rack powers for 2027 platforms are unpublished** (Vera Rubin NVL72 190–250 kW by analyst estimates; Kyber "600 kW" not restated); BEN 300 and BEN 700 are sized for current liquid racks (GB300 NVL72-class, 132–155 kW) and re-baselined at program gates.
4. **The research was built from search excerpts**; the primary PDFs listed in the research §6 must be read in full before any of their figures appears on a product page.
5. **BEN 1 acoustic and heat-to-room figures** are targets until E21 and E22 run on the first articles.
6. **Rev 2 drawings are issued for review**, not for construction, until a checker is named in `design/REVISION.json`.
7. **The proposal and the product page filter risks by mission profile**; until they also filter on the new `tiers` field, a proposal for one tier can list risks written for another.
8. **Operator questions still open**, each with a recommended default, in [`docs/rev2/OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) (from `docs/REV2_DECISION.md` §4, the brand work and the revamp program).
9. **BEN 300 and BEN 700 BOMs are about 97 % estimate** because the GB300 NVL72-class rack price is an analyst estimate; read the infrastructure-only price for those tiers (`docs/rev2/UNIT_ECONOMICS.md`).

## 7. Placeholders — filled 2026-11-09

The Rev 2 documents were first written with open placeholders for the values the lineup work had not yet produced. All were filled on 2026-11-09 from `docs/DENSITY.md`, `docs/rev2/BOM*.md`, `docs/rev2/UNIT_ECONOMICS.md` and `python -m ben_engine.config --tier <t> --json` (lineup `rev2`); the tier renamed by fit is BEN 700 (was BEN 1000). The table is kept as the record of what was filled and with which value.

| Placeholder | Meaning | Source | Used in | Value filled |
| --- | --- | --- | --- | --- |
| `BEN1_RACK10_KW_PER_M2`, `BEN1_CAB12_KW_PER_M2` | kW IT per m² of footprint | `docs/DENSITY.md` | this file §5 | 8.21 (rack10, 0.6 kW on 0.073 m²); 2.29 (cab12 at 1.5 kW on 0.655 m²) |
| `BEN1_RACK10_MASS_KG`, `BEN1_CAB12_MASS_KG` | Loaded mass | `docs/DENSITY.md` / BOM | this file §5; `docs/SITE_REQUIREMENTS.md` §15 | 38 kg (rack10); 136 kg at the 1.1 kW preset to 176 kg at 1.5 kW (cab12) |
| `BEN1_CAB12_BOM_USD` | cab12 unit cost with reference compute | `docs/rev2/BOM-ben1*.md` | `docs/programs/REV2_REVAMP_PROGRAM.md` line 1 | USD 42,080 at the `ai_inference` preset (1.0 kW), of which USD 32,936 is the reference 2U GPU server; USD 9,144 without compute (`python -m ben_engine.bom --tier ben1 --form cab12 --lineup rev2`; not in the generated `BOM-ben1.md`, which is rack10) |
| `BEN1_UPS_MINUTES` | UPS minutes in the BEN 1 preset | `config.py` | `docs/TEST_GUIDE.md` E23 | 10 min configured (`ups_minutes`); vendor-curve estimate 10.4 min rack10 / 11.5 min cab12 |
| `BEN300_IT_KW`, `BEN1000_IT_KW` | Final nominal IT kW (the tier name if renamed) | `docs/DENSITY.md` | this file §5 | 300 kW (310 max); BEN 700: 700 kW (705 max), renamed from BEN 1000 |
| `BEN300_RACKS`, `BEN1000_RACKS` | Racks in the preset | `docs/DENSITY.md` | this file §5 | 2; 5 |
| `BEN300_KW_PER_RACK`, `BEN1000_KW_PER_RACK` | kW per rack | `docs/DENSITY.md` | this file §5 | 150; 140 |
| `BEN300_KW_PER_M2`, `BEN1000_KW_PER_M2` | kW IT per m² of module footprint | `docs/DENSITY.md` | this file §5; program §4; decks | 20.31; 23.55 |
| `BEN300_MASS_T`, `BEN1000_MASS_T` | Gross shipped mass | `docs/DENSITY.md` / config | this file §5; `SITE_REQUIREMENTS.md` §15 | 9.41 t; 19.3 t |
| `BEN300_INFRA_BOM_USD` | BEN 300 infrastructure cost without compute | `docs/rev2/BOM-ben300.md` | program line 2 | USD 925,804 (excl. compute, `docs/rev2/BOM.md`) |
| `BEN300_FEEDER_A`, `BEN1000_FEEDER_A` | Customer disconnect rating | config `service_breaker_a` | `SITE_REQUIREMENTS.md` §15 | 600 A (509 A calculated); 1,200 A (1,186 A calculated) |
| `BEN300_DEMAND_KVA`, `BEN1000_DEMAND_KVA` | Total electrical demand | config | `SITE_REQUIREMENTS.md` §15 | 338.4 kVA; 788.9 kVA |
| `BEN300_HEAT_REJECT_KW`, `BEN1000_HEAT_REJECT_KW` | Heat rejected outdoors | config | `SITE_REQUIREMENTS.md` §15 | about 322 kW; about 750 kW (total electrical demand, all of which becomes heat; liquid loop 270 / 630 kW plus trim loop 33 / 77 kW at the coils) |
| `BEN300_SKID_FOOTPRINT_M`, `BEN1000_SKID_FOOTPRINT_M` | Heat-rejection yard size | drawings / config | `SITE_REQUIREMENTS.md` §15 | skid 2.4 × 2.6 m; 4.8 × 2.6 m, each 1.5 m off the blind end (site 25.89 m²; 48.08 m²) |
| `BEN300_LOOP_VOLUME_L`, `BEN1000_LOOP_VOLUME_L` | Liquid loop volume | config | `SITE_REQUIREMENTS.md` §15 | **not computed**: the configuration has no loop-volume output; depends on the CDU secondary hold-up (vendor data), the DN80 rear-plenum header and rack drops, and the skid piping run; stated on the FAT fill record |
| `BEN1_CAB12_SELL_USD`, `BEN300_INFRA_SELL_USD`, `BEN1000_INFRA_SELL_USD` | Sell price (BEN 1 cab12 with reference compute; dense tiers infrastructure-only) | `docs/rev2/UNIT_ECONOMICS.md` | `docs/investors/deck/slides.json` (business-model slide) | cab12 USD 58,445 with reference compute (USD 12,701 without; BOM ÷ 0.72); BEN 300 USD 1,285,839; BEN 700 USD 2,267,400 infrastructure-only |
| Density figures on the decks | `BEN300_*` / `BEN1000_*` kW per rack, kW per m², racks | `docs/DENSITY.md` | `docs/investors/deck/slides.json`, `docs/presentation/slides.json` (Density slide); `docs/FAQ.md` (BEN 700 answer). Rebuild both decks after filling | as above; decks rebuilt 2026-11-09 |

A search of `docs/` and `README.md` for the placeholder braces returns nothing in prose after this pass (2026-11-09). The generated sample `docs/proposals/rev2/sample-ben300-ai_training.*` still quotes three placeholders it copied from `SITE_REQUIREMENTS.md` §15 before that section was filled; it is fixed by regenerating the sample (command in `docs/proposals/rev2/README.md`), not by hand.
