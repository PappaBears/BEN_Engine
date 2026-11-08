# BEN Engine — Product and engineering briefing: speaker notes

## 1. BEN Engine, Business Edge Node

A family of modular data centers named by IT power, from a sealed outdoor cabinet to a single 2 MW prefabricated center, with Schreiber AI's controls, twin and commissioning layer.

Audience: engineers, integrators, facilities leads. Names changed on 2026-11-08: the number is now the IT kW, not the container length (docs/TIER_AND_ENCLOSURE_DECISION.md); old keys still load. Set expectations: every number on these slides comes from code in the repository and the evidence file is docs/VALIDATION.md.

## 2. A concrete scenario

A regional clinic wants inference on patient data on-site: healthcare profile, 2N power, A1 class, generator standard.

Walk the selector live on the product page (web/index.html) or the dashboard. Show the validation error path by setting racks to 1 at 150 kW.

## 3. BEN 2000: the single 2 MW center

Not a container: a prefabricated, relocatable data hall of three site-joined wide-body modules, a power module and a plant yard.

python -m ben_engine.config --tier ben2000 prints these numbers. Twin, CFD per module, drawings (site plan A-000 + per-module sheets) and BOM for BEN 2000 are marked pending in docs/VALIDATION.md until the core and catalog work lands; do not claim them verified. Built by modular-building manufacturers (MANUFACTURING_STRATEGY.md section 3.2).

## 4. Element-proof and hardened

Every BEN starts watertight (NEMA 4X / IP66, hose-tested per UL 50E); two hardening packages sit on top.

Config.hardening drives the envelope mass adder, catalog cost lines, compliance pack rows (COMPLIANCE.md section 15), maintenance add-ons and the warranty conditions. Say plainly: TEMPEST-ready, not TEMPEST-certified; HEMP shielding is a vendor-certified enclosure plus our IEEE 299 test. The rain-only 3R rating is retired everywhere.

## 5. One configuration drives everything

config.py is the base model: sizing rules, validation, presets. Downstream generators consume it.

Mention the parity test: tests/test_selector_parity.py runs node against the Python model so the website cannot drift from engineering.

## 6. The digital twin

Lumped thermal and power-chain model with faults, alarms and sensor specs; fit-able from commissioning data.

Caveat: thermal masses are design values until measured. The fitter flags envelope UA as weakly identifiable from indoor data; say so.

## 7. CFD for layout, not for absolute numbers

2-D lattice-Boltzmann airflow with heat and tracer transport runs per tier in seconds.

Reynolds number in the lattice is ~70 versus ~1e5 real; it is a relative tool for ranking layouts and scenario deltas. The 3-D CFD is on the roadmap after lighthouse data exists.

## 8. Measurement plan and calibration

Sensors chosen for the quantities we predict, with uncertainty budgets, tares and placement effects.

Two budget claims in PROTOCOL.md were not met by the computed budgets (RH and dP); they are left as findings in docs/ANALYSIS_AND_CALIBRATION.md rather than quietly edited.

## 9. Controls: industrial platform, BEN Mesh, hardwired life safety

BEN Controls Pro: Phoenix Contact PLCnext PLC in a UL 508A panel + OnLogic edge computer (TPM). BEN Controls Lite: Revolution Pi for the BEN 5. Both: our BEN Pods on a secure Thread mesh.

Be precise: the EFR32/OpenThread HAL has never been compiled against the real SDK and attestation has not run on silicon. The PLC, edge computer and Pods are priced in the BOM (controls +0.3 to +0.9 % of a unit) and not yet bought. Everything platform-independent is tested. Decision record: docs/CONTROLS_HARDWARE_DECISION.md.

## 10. Build it with workers who have minimal experience

Assembly instructions in ASD-STE100 with hold points for licensed trades, QC forms and CTQ/CTP references.

Renders are labelled concept renders. The interference checks table in design/drawings/INTERFERENCE_CHECKS.md is worth showing to engineers: it is what changed the cooling defaults.

## 11. Commissioning: the same script in the factory and on site

Ten steps, pass/fail per step, CSV with SHA-256, signature block; the customer can run it.

Run it live: PYTHONPATH=software python -m ben_engine.commissioning --sim --tier ben150 --yes --out /tmp/r.md. Show the report.

## 12. Compliance findings that changed the design

A2L refrigerant charge limits, NFPA 855 at 20 kWh, NEC 110.26 vestibule, container as Group U structure.

docs/COMPLIANCE.md section 0 lists these with the calculation basis and what could not be verified (NFPA 76 edition, ASHRAE 15/34 2025).

## 13. Validation summary

Verified in simulation and on host; unverified on hardware; least accurate items named.

Read docs/VALIDATION.md before presenting; update numbers to the latest run.

## 14. Get started

Clone, install, test, run the dashboard, generate a proposal.

Next decision for an integrator: which tier to pilot and which site. Next decision for Schreiber AI: lighthouse funding.
