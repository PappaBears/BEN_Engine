# BEN Engine Rev 2 — release notes

**Product revision:** Rev 2 · **Date:** 2026-11-09 · **Decision record:** `docs/REV2_DECISION.md` · **Revision rules:** `docs/REVISION_POLICY.md` · **Previous revision:** Rev 1, frozen (`releases/REV1.md`, branch `release/rev1`) · **Drawing set starts at:** Rev 2.A

Rev 2 is a once-over of a base that works, in the operator's words: "the base is good, we just need a once-over". It applies the Schreiber AI brand package v2, adds the low end (BEN 1 mini racks for tiny businesses) and the dense end (BEN 300 and BEN 1000, liquid-first), and funds the hardware proof with a USD 5 M revamp program. Nothing from Rev 1 was deleted.

## 1. What changed from Rev 1

| Area | Rev 1 | Rev 2 | Where |
| --- | --- | --- | --- |
| **Brand** | Brand kit v1.1 (amber used for accents and status) | **Brand package v2 applied**: "BEN Engine, by Schreiber AI"; Night Navy ground, Signal Blue mark and links, Safety Amber on the primary button only, separate status colours; Archivo + IBM Plex; the **data plate band** on the hardware, drawings, proposals, slides, dashboard footer and data sheets; thermal ramp for heat maps | `brand/v2/`, `web/`, `dashboard/`, `docs/contracts/`, both decks |
| **Lineup, low end** | BEN 5 (2–5 kW outdoor cabinet) was the smallest | **BEN 1** (new): indoor mini rack, rack10 (10-inch 8U, ≤ 0.6 kW) or cab12 (19-inch 12U sound-damped, ≤ 1.5 kW), 120 V plug-in, office air, built in-house | `software/ben_engine/config.py`; `docs/COMPLIANCE.md` §18; `docs/SITE_REQUIREMENTS.md` §15; `docs/PROCESS_FLOW.md` §6; `docs/MANUFACTURING_STRATEGY.md` §12 |
| **Lineup, dense end** | BEN 150 (20 ft, 50–150 kW, rear-door) and BEN 500 (40 ft, 150–500 kW, DLC) | **BEN 300** (new, 20 ft, 150–300 kW) and **BEN 1000** (new, 40 ft, 500–1,000 kW), liquid-first; BEN 150 and BEN 500 carried unchanged for existing quotes | `config.py`; `docs/COMPLIANCE.md` §19; `docs/DENSITY.md` |
| **Cooling defaults** | `dlc_hd` (W45 high-density liquid) was a forward study option | **Liquid-first default on the dense tiers**: `dlc_hd` is the default cooling on BEN 300 and BEN 1000 (W45 secondary loop, row CDUs N+1, ≤ 10 % air residual, heat-reuse port); E18–E20 are mandatory on every dense unit | `config.py`; `docs/TEST_GUIDE.md`; `docs/MAINTENANCE.md` §11 |
| **800 VDC** | `dc800` study option | Unchanged: **still a study option**, now behind the revamp program's gated DC test cell | `docs/FORWARD_ARCHITECTURE_DECISION.md`; `docs/programs/REV2_REVAMP_PROGRAM.md` line 4 |
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
- **BEN 5, BEN 30, BEN 150, BEN 500 and BEN 2000** keep their Rev 1 sizing, presets, prices and drawings (Rev C, issued for review; Rev B IFC for the non-BEN 5 tiers). They are carried, not redesigned.
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
| A new configuration | Defaults to `lineup: "rev2"`; BEN 1, BEN 300 and BEN 1000 are only selectable in `rev2` |
| Rev 1 drawings, renders, assembly instructions, BOMs and sample proposals | Unchanged at their Rev 1 paths; Rev 2 versions are written beside them |
| Rev 1 customer-facing documents that Rev 2 rewrote | Copied first to `archive/rev1/` (README, FAQ, VC proposition, both decks with speaker notes, compliance, risk register, site requirements, maintenance, test guide, process flow, manufacturing strategy, both programs, the Rev 1 website) |
| Any Rev 1 file exactly as released | `git show origin/release/rev1:<path>` |

## 4. Where each Rev 2 artifact lives

| Artifact | Path |
| --- | --- |
| Decision record | `docs/REV2_DECISION.md` |
| Revision policy | `docs/REVISION_POLICY.md` |
| These release notes | `docs/rev2/RELEASE_NOTES.md` |
| Density metrics | `docs/DENSITY.md` |
| Rev 2 BOMs (per tier) | `docs/rev2/BOM-*.md`, `purchasing/rev2/` |
| Rev 2 unit economics | `docs/rev2/UNIT_ECONOMICS.md` |
| Rev 2 drawings, renders, assembly | `design/drawings/rev2/<tier>/`, `design/renders/rev2/<tier>/`, `design/assembly/rev2/` |
| Rev 2 sample proposals | `docs/proposals/rev2/` |
| USD 5 M revamp program | `docs/programs/REV2_REVAMP_PROGRAM.md` |
| Compliance for new tiers | `docs/COMPLIANCE.md` §18 (BEN 1), §19 (BEN 300 / BEN 1000) |
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
| BEN 1 rack10 | 10-inch 8U desk / shelf rack | 0.6 | 1 | 0.6 | {{BEN1_RACK10_KW_PER_M2}} | {{BEN1_RACK10_MASS_KG}} kg |
| BEN 1 cab12 | 19-inch 12U sound-damped cabinet | 1.5 | 1 | 1.5 | {{BEN1_CAB12_KW_PER_M2}} | {{BEN1_CAB12_MASS_KG}} kg |
| BEN 300 | 20 ft module, liquid-first | {{BEN300_IT_KW}} | {{BEN300_RACKS}} | {{BEN300_KW_PER_RACK}} | {{BEN300_KW_PER_M2}} | {{BEN300_MASS_T}} t |
| BEN 1000 | 40 ft module, liquid-first | {{BEN1000_IT_KW}} | {{BEN1000_RACKS}} | {{BEN1000_KW_PER_RACK}} | {{BEN1000_KW_PER_M2}} | {{BEN1000_MASS_T}} t |

If a density target did not fit the interference checks, the tier carries the name of the power that fits (`docs/REV2_DECISION.md` §2); the lead replaces the names above with the final ones.

## 6. Known limits

1. **No Rev 2 hardware exists yet.** BEN 1, BEN 300 and BEN 1000 numbers are design values from the configuration model; the BEN 1 and BEN 300 lighthouse units in the revamp program measure them. BEN 1000 is engineered and quotable but not built.
2. **800 VDC is a study**, gated behind a DC test cell that is itself an option in the program; no 150–500 kW 800 VDC distribution is listed in November 2026 (`docs/research/STATE_OF_THE_ART_2026.md` §0 fact 3).
3. **Rack powers for 2027 platforms are unpublished** (Vera Rubin NVL72 190–250 kW by analyst estimates; Kyber "600 kW" not restated); BEN 300 and BEN 1000 are sized for current liquid racks (GB300 NVL72-class, 132–155 kW) and re-baselined at program gates.
4. **The research was built from search excerpts**; the primary PDFs listed in the research §6 must be read in full before any of their figures appears on a product page.
5. **BEN 1 acoustic and heat-to-room figures** are targets until E21 and E22 run on the first articles.
6. **Rev 2 drawings are issued for review**, not for construction, until a checker is named in `design/REVISION.json`.
7. **The proposal and the product page filter risks by mission profile**; until they also filter on the new `tiers` field, a proposal for one tier can list risks written for another.
8. **Operator questions still open** (`docs/REV2_DECISION.md` §4): BEN Care vs "Atlas, by Schreiber AI" sign-in name; phone number, starting prices and pilot results for the brand package's proof slots; module paint (default chosen: Shop White body with Night Navy band outdoors, Night Navy for BEN 1).

## 7. Placeholders for the lead to fill

Values in `{{…}}` are produced by the lineup work (`docs/DENSITY.md`, `docs/rev2/BOM-*.md`, `docs/rev2/UNIT_ECONOMICS.md`) and are left open in the documents below. Replace each with the final figure (and the tier name if a tier was renamed).

| Placeholder | Meaning | Source | Used in |
| --- | --- | --- | --- |
| `{{BEN1_RACK10_KW_PER_M2}}`, `{{BEN1_CAB12_KW_PER_M2}}` | kW IT per m² of footprint | `docs/DENSITY.md` | this file §5 |
| `{{BEN1_RACK10_MASS_KG}}`, `{{BEN1_CAB12_MASS_KG}}` | Loaded mass | `docs/DENSITY.md` / BOM | this file §5; `docs/SITE_REQUIREMENTS.md` §15 |
| `{{BEN1_CAB12_BOM_USD}}` | cab12 unit cost with reference compute | `docs/rev2/BOM-ben1*.md` | `docs/programs/REV2_REVAMP_PROGRAM.md` line 1 |
| `{{BEN1_UPS_MINUTES}}` | UPS minutes in the BEN 1 preset | `config.py` | `docs/TEST_GUIDE.md` E23 |
| `{{BEN300_IT_KW}}`, `{{BEN1000_IT_KW}}` | Final nominal IT kW (the tier name if renamed) | `docs/DENSITY.md` | this file §5 |
| `{{BEN300_RACKS}}`, `{{BEN1000_RACKS}}` | Racks in the preset | `docs/DENSITY.md` | this file §5 |
| `{{BEN300_KW_PER_RACK}}`, `{{BEN1000_KW_PER_RACK}}` | kW per rack | `docs/DENSITY.md` | this file §5 |
| `{{BEN300_KW_PER_M2}}`, `{{BEN1000_KW_PER_M2}}` | kW IT per m² of module footprint | `docs/DENSITY.md` | this file §5; program §4; decks |
| `{{BEN300_MASS_T}}`, `{{BEN1000_MASS_T}}` | Gross shipped mass | `docs/DENSITY.md` / config | this file §5; `SITE_REQUIREMENTS.md` §15 |
| `{{BEN300_INFRA_BOM_USD}}` | BEN 300 infrastructure cost without compute | `docs/rev2/BOM-ben300.md` | program line 2 |
| `{{BEN300_FEEDER_A}}`, `{{BEN1000_FEEDER_A}}` | Customer disconnect rating | config `service_breaker_a` | `SITE_REQUIREMENTS.md` §15 |
| `{{BEN300_DEMAND_KVA}}`, `{{BEN1000_DEMAND_KVA}}` | Total electrical demand | config | `SITE_REQUIREMENTS.md` §15 |
| `{{BEN300_HEAT_REJECT_KW}}`, `{{BEN1000_HEAT_REJECT_KW}}` | Heat rejected outdoors | config | `SITE_REQUIREMENTS.md` §15 |
| `{{BEN300_SKID_FOOTPRINT_M}}`, `{{BEN1000_SKID_FOOTPRINT_M}}` | Heat-rejection yard size | drawings / config | `SITE_REQUIREMENTS.md` §15 |
| `{{BEN300_LOOP_VOLUME_L}}`, `{{BEN1000_LOOP_VOLUME_L}}` | Liquid loop volume | config | `SITE_REQUIREMENTS.md` §15 |
| `{{BEN1_CAB12_SELL_USD}}`, `{{BEN300_INFRA_SELL_USD}}`, `{{BEN1000_INFRA_SELL_USD}}` | Sell price (BEN 1 cab12 with reference compute; dense tiers infrastructure-only) | `docs/rev2/UNIT_ECONOMICS.md` | `docs/investors/deck/slides.json` (business-model slide) |
| Density figures on the decks | `{{BEN300_*}}` / `{{BEN1000_*}}` kW per rack, kW per m², racks | `docs/DENSITY.md` | `docs/investors/deck/slides.json`, `docs/presentation/slides.json` (Density slide); `docs/FAQ.md` (BEN 1000 answer). Rebuild both decks after filling |

A line-by-line list with file and line numbers is produced by `grep -rn "{{" docs README.md`.
