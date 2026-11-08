# BEN Care — the digital care layer

**What it is.** BEN Care is the service that runs on every BEN Engine unit: the fitted physics twin, the monthly proof of redundancy, drift-triggered calibration, the live risk scorecard, fleet learning, and a hardware root of trust in every sensor. It is what turns a monitored box into a cared-for one. It runs on the BEN Controller (industrial edge computer + PLC) and the BEN Mesh of BEN Pods described in `docs/CONTROLS_HARDWARE_DECISION.md`.

## What nobody else does

| Everyone else | BEN Care |
| --- | --- |
| A threshold alarm: "inlet 31 °C". | **Minutes-to-limit with a confidence interval**: "rack 5 reaches the A2 limit in 6.4 ± 1.1 min if cooling unit 2 stays down; standby unit 4 is starting". The number comes from a twin fitted to this unit's own commissioning data and refitted as it runs. |
| Failover is tested at commissioning, if at all, and never again. | **Proof of redundancy every month.** The same sweeps that passed FAT run automatically at low load, are hash-signed and attached to the SLA report. The warranty and the availability credit depend on them. |
| Calibrate on a calendar, or never. | **Calibrate when the data says so.** Pods cross-check each other and the twin; when a channel's uncertainty grows past its budget, BEN Care asks for a calibration and attaches the GUM budget to the record. |
| A risk register in the proposal appendix. | **A live risk scorecard.** Every risk the customer saw before the price shows the evidence that it is covered right now: last failover pass, filter ΔP trend, battery state of health, door events, mesh health, attestation state. |
| Each site learns alone. | **Fleet learning.** Fitted parameters and failure precursors from every unit improve the priors for the next commissioning and sharpen every prediction, through Schreiber AI's memory layer. Customer data never leaves the unit unless the customer opts in. |
| Sensors are anonymous devices on a flat network. | **Every Pod attests.** Per-device certificate in a hardware secure element (Secure Vault High, PSA Level 3), signed firmware with anti-rollback, DTLS join, TPM-measured boot on the edge computer, no route to the internet from the controls zone. |
| Cloud dashboards that stop when the subscription does. | **Local-first and open.** The dashboard, twin and data live in the box; the customer owns them; white-label partners put their brand on it; the safety identity stays. |
| A commissioning report that is filed and forgotten. | **One script for the whole life.** FAT, SAT, monthly check and warranty baseline are the same signed script with the same pass criteria. |

## Care plans

| Plan | Who watches | What is included | Price basis |
| --- | --- | --- | --- |
| **Care Essential** (included with BEN Controls Lite and Pro; the hardware tier changes the controller, not the care layer) | Customer | Twin, alarms with minutes-to-limit, sweeps on demand, calibration tools, CSV/JSON export, local dashboard, software updates for the update period | Controls licence per tier per year |
| **Care Managed** | Schreiber AI operations centre | Everything in Essential plus 24 × 7 monitoring, monthly proof-of-redundancy run and signed report, drift-triggered calibration visits, maintenance scheduling and execution per `docs/MAINTENANCE.md`, firmware and security patching, monthly PUE/availability report, outbound-only support tunnel the customer switches on | USD per kW-month on design IT load (`docs/contracts/MANAGED_SERVICES_SLA.md`) |
| **Care Partner** (white-label) | Integrator L1, Schreiber AI L2/L3 | Care Managed delivered under the partner's brand with Schreiber AI behind it; fleet view for the partner | Wholesale rate per kW-month + licence |

## Evidence behind each claim (in this repository)

| Claim | Code | Verified |
| --- | --- | --- |
| Minutes-to-limit with uncertainty | `software/ben_engine/analysis.py` (`thermal_margin`, `predict` Monte Carlo) | simulation |
| Monthly proof of redundancy | `software/ben_engine/sweeps.py` (`cooling_unit_failover`, `utility_loss_ride_through`), `commissioning.py` signed report | simulation |
| Drift-triggered calibration | `software/ben_engine/calibration.py` (`predictability_score`, budgets), twin `sensor_drift` fault raises the alarm path | simulation |
| Live risk scorecard | `web/assets/risks.json` + dashboard alarms/evidence inspector (scorecard view is on the roadmap) | partial |
| Fleet learning | `docs/SYSTEM_INTEGRATION.md` Atlas interface | interface only |
| Attestation and signed firmware | `firmware/ben-pod` (Secure Vault / Gecko bootloader procedure), `docs/CYBERSECURITY.md` | documented, not run on hardware |
| Local-first, white-label | `dashboard/`, `Config.brand`, licence terms | verified in simulation |

## Honest limits
The twin's thermal time constants are design values until the first lighthouse unit is commissioned; minutes-to-limit is a lower bound until then. Fleet learning needs more than one unit. The Pod hardware has not been built. These are the reasons the lighthouse units come first.
