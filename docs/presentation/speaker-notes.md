# BEN Engine — Product and engineering briefing: speaker notes

## 1. BEN Engine, Business Edge Node

A family of modular data centers built in off-the-shelf containers and cabinets, with Schreiber AI's controls, twin and commissioning layer.

Audience: engineers, integrators, facilities leads. Set expectations: every number on these slides comes from code in the repository and the evidence file is docs/VALIDATION.md.

## 2. A concrete scenario

A regional clinic wants inference on patient data on-site: healthcare profile, 2N power, A1 class, generator standard.

Walk the selector live on the product page (web/index.html) or the dashboard. Show the validation error path by setting racks to 1 at 150 kW.

## 3. One configuration drives everything

config.py is the base model: sizing rules, validation, presets. Downstream generators consume it.

Mention the parity test: tests/test_selector_parity.py runs node against the Python model so the website cannot drift from engineering.

## 4. The digital twin

Lumped thermal and power-chain model with faults, alarms and sensor specs; fit-able from commissioning data.

Caveat: thermal masses are design values until measured. The fitter flags envelope UA as weakly identifiable from indoor data; say so.

## 5. CFD for layout, not for absolute numbers

2-D lattice-Boltzmann airflow with heat and tracer transport runs per tier in seconds.

Reynolds number in the lattice is ~70 versus ~1e5 real; it is a relative tool for ranking layouts and scenario deltas. The 3-D CFD is on the roadmap after lighthouse data exists.

## 6. Measurement plan and calibration

Sensors chosen for the quantities we predict, with uncertainty budgets, tares and placement effects.

Two budget claims in PROTOCOL.md were not met by the computed budgets (RH and dP); they are left as findings in docs/ANALYSIS_AND_CALIBRATION.md rather than quietly edited.

## 7. Controls: open, local-first, hardwired life safety

Raspberry Pi 5 gateway, ESP32 PoE nodes, MQTT/JSON, Modbus/SNMP to third-party gear.

Be precise: the ESP32 HAL has never been compiled against the real libraries. First pio run on hardware will need fixes. Everything platform-independent is tested.

## 8. Build it with workers who have minimal experience

Assembly instructions in ASD-STE100 with hold points for licensed trades, QC forms and CTQ/CTP references.

Renders are labelled concept renders. The interference checks table in design/drawings/INTERFERENCE_CHECKS.md is worth showing to engineers: it is what changed the cooling defaults.

## 9. Commissioning: the same script in the factory and on site

Ten steps, pass/fail per step, CSV with SHA-256, signature block; the customer can run it.

Run it live: PYTHONPATH=software python -m ben_engine.commissioning --sim --tier ben20 --yes --out /tmp/r.md. Show the report.

## 10. Compliance findings that changed the design

A2L refrigerant charge limits, NFPA 855 at 20 kWh, NEC 110.26 vestibule, container as Group U structure.

docs/COMPLIANCE.md section 0 lists these with the calculation basis and what could not be verified (NFPA 76 edition, ASHRAE 15/34 2025).

## 11. Validation summary

Verified in simulation and on host; unverified on hardware; least accurate items named.

Read docs/VALIDATION.md before presenting; update numbers to the latest run.

## 12. Get started

Clone, install, test, run the dashboard, generate a proposal.

Next decision for an integrator: which tier to pilot and which site. Next decision for Schreiber AI: lighthouse funding.
