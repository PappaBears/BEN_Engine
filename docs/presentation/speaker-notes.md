# BEN Engine — Product and engineering briefing: speaker notes

## 1. BEN Engine, Business Edge Node

All-in-one modular data centers named by IT power, from a mini rack on a shelf to a 1 MW liquid-first 40 ft module, with Schreiber AI's controls, twin and commissioning layer. The same system scales to a 2 MW center.

Audience: engineers, integrators, facilities leads. Names changed on 2026-11-08: the number is now the IT kW, not the container length (docs/TIER_AND_ENCLOSURE_DECISION.md); old keys still load. Set expectations: every number on these slides comes from code in the repository and the evidence file is docs/VALIDATION.md. Rev 2 (2026-11-09) adds BEN 1, BEN 300 and BEN 1000; Rev 1 configurations load as rev1 and reproduce (docs/rev2/RELEASE_NOTES.md).

## 2. Density

As dense as a sealed, relocatable box allows, with every figure generated from the configuration and checked against real footprints, not taken from a brochure.

Fill the placeholders from docs/DENSITY.md before presenting; never present a slide with braces on it. Peer figures come from docs/research/STATE_OF_THE_ART_2026.md section 3 and are vendor statements, so say 'as published'. The honest positioning: every DC-ready offer is MW-class and every sub-MW container is AC; none publishes leak-to-isolation or redundancy-proof numbers. For engineers: kW per m² is IT kW over the module's outside footprint; the interference checks (single row, 900 mm egress, NEC 110.26 at 480 V) must pass first. Our density is a design value until the lighthouse.

## 3. Mini racks: AI for tiny businesses

A tiny business can run private AI on a shelf: one or two AI boxes, a NAS and a firewall, plugged into the wall, set up and watched by Schreiber AI.

The buyer is the owner of a studio, a trades business or a small office who wants AI on their own data without hiring IT. What they get is the same discipline as the big units: a site check, a burn-in, measured noise and heat, a handover, BEN Care watching it and a four-line owner maintenance list. Do not quote a market number for this segment; MARKET_SOURCES.md says none was found. Prices come from docs/rev2/UNIT_ECONOMICS.md. Engineering detail: COMPLIANCE.md section 18 (UL 62368-1 parts, NEC 210.23 80 % rule), SITE_REQUIREMENTS.md section 15, TEST_GUIDE.md E21–E24.

## 4. A concrete scenario

A regional clinic wants inference on patient data on-site: healthcare profile, 2N power, A1 class, generator standard.

Walk the selector live on the product page (web/index.html) or the dashboard. Show the validation error path by setting racks to 1 at 150 kW.

## 5. BEN 2000: the single 2 MW center

The capability example, not the lead product. Not a container: a prefabricated, relocatable data hall of three site-joined wide-body modules, a power module and a plant yard.

python -m ben_engine.config --tier ben2000 prints these numbers. Twin, CFD per module, drawings (site plan A-000 + per-module sheets) and BOM-ben2000 are generated and run in simulation (docs/VALIDATION.md section 4a); every physical value (module mass, water use, utility lead time, module pricing) is unverified, so say sized and documented, not proven. Built by modular-building manufacturers (MANUFACTURING_STRATEGY.md section 3.2).

## 6. Element-proof and hardened

Every BEN starts watertight (NEMA 4X / IP66, hose-tested per UL 50E); two hardening packages sit on top.

Config.hardening drives the envelope mass adder, catalog cost lines, compliance pack rows (COMPLIANCE.md section 15), maintenance add-ons and the warranty conditions. Say plainly: TEMPEST-ready, not TEMPEST-certified; HEMP shielding is a vendor-certified enclosure plus our IEEE 299 test. The rain-only 3R rating is retired everywhere.

## 7. One configuration drives everything

config.py is the base model: sizing rules, validation, presets. Downstream generators consume it.

Mention the parity test: tests/test_selector_parity.py runs node against the Python model so the website cannot drift from engineering.

## 8. The digital twin

Lumped thermal and power-chain model with faults, alarms and sensor specs; fit-able from commissioning data.

Caveat: thermal masses are design values until measured. The fitter flags envelope UA as weakly identifiable from indoor data; say so.

## 9. CFD for layout, not for absolute numbers

2-D lattice-Boltzmann airflow with heat and tracer transport runs per tier in seconds.

Reynolds number in the lattice is ~70 versus ~1e5 real; it is a relative tool for ranking layouts and scenario deltas. The 3-D CFD is on the roadmap after lighthouse data exists.

## 10. Measurement plan and calibration

Sensors chosen for the quantities we predict, with uncertainty budgets, tares and placement effects.

Two budget claims in PROTOCOL.md were not met by the computed budgets (RH and dP); they are left as findings in docs/ANALYSIS_AND_CALIBRATION.md rather than quietly edited.

## 11. Controls: industrial platform, BEN Mesh, hardwired life safety

BEN Controls Pro: Phoenix Contact PLCnext PLC in a UL 508A panel + OnLogic edge computer (TPM). BEN Controls Lite: Revolution Pi for the BEN 5. Both: our BEN Pods on a secure Thread mesh.

Be precise: the EFR32/OpenThread HAL has never been compiled against the real SDK and attestation has not run on silicon. The PLC, edge computer and Pods are priced in the BOM (controls +0.3 to +0.9 % of a unit) and not yet bought. Everything platform-independent is tested. Decision record: docs/CONTROLS_HARDWARE_DECISION.md.

## 12. Build it with workers who have minimal experience

Assembly instructions in ASD-STE100 with hold points for licensed trades, QC forms and CTQ/CTP references.

Renders are labelled concept renders. The interference checks table in design/drawings/INTERFERENCE_CHECKS.md is worth showing to engineers: it is what changed the cooling defaults.

## 13. Commissioning: the same script in the factory and on site

Twelve steps, pass/fail per step, CSV with SHA-256, signature block; the customer can run it.

Run it live: PYTHONPATH=software python -m ben_engine.commissioning --sim --tier ben150 --yes --out /tmp/r.md. Show the report.

## 14. Compliance findings that changed the design

A2L refrigerant charge limits, NFPA 855 at 20 kWh, NEC 110.26 vestibule, container as Group U structure.

docs/COMPLIANCE.md section 0 lists these with the calculation basis and what could not be verified (NFPA 76 edition, ASHRAE 15/34 2025).

## 15. Validation summary

Verified in simulation and on host; unverified on hardware; least accurate items named.

Read docs/VALIDATION.md before presenting; update numbers to the latest run.

## 16. Get started

Clone, install, test, run the dashboard, generate a proposal.

Next decision for an integrator: which tier to pilot and which site. Next decision for Schreiber AI: release gate G0 of the USD 5 M revamp (docs/programs/REV2_REVAMP_PROGRAM.md) and pick the BEN 1 pilot customers.
