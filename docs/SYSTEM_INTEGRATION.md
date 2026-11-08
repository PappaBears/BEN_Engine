# System integration

BEN Engine is self-contained per unit. Integration with Schreiber AI's larger system is through configurable, documented interfaces; nothing is hard-coded.

| System | Role | Interface | Configuration | State today |
| --- | --- | --- | --- | --- |
| **Atlas** (tiered memory) | Long-term memory of corrections: fitted twin parameters, calibration history, maintenance findings per unit | The edge computer posts `fitted_params` and `cal_record` JSON to an Atlas endpoint when `ATLAS_URL` is set; otherwise stores locally in SQLite | env `ATLAS_URL`, `ATLAS_TOKEN` (never in repo) | interface defined, not connected (no endpoint in this session) |
| **Jev** (fast routing) | Routes alarms to the right human/agent | The edge computer publishes `ben/<unit>/alarm` to an MQTT bridge or webhook when `ALARM_WEBHOOK` is set | env `ALARM_WEBHOOK` | interface defined, not connected |
| **Paperclip** (agent orchestration) | One sub-agent tree per customer unit for monitoring, maintenance scheduling and report drafting | Reads the dashboard API (`/api/state`, `/api/sweeps`, `/api/export.csv`) read-only; writes nothing without an operator action | API URL + read-only token | interface available (the API exists); orchestration not deployed |
| **HomeBase** | Not applicable to data center units; BEN Micro can expose the same MQTT topics for a site that also runs HomeBase | shared MQTT topic namespace `ben/<unit>/…` | broker bridge | documented only |
| **OMI wearable** | Voice query of unit status ("what's rack 3 inlet?") via Jev → API | `/api/state` | — | documented only |
| Customer BMS / SCADA | Read unit status | Modbus TCP server map and SNMP (roadmap) | — | roadmap |
| Customer white-label | Their brand in dashboard and on the box | `Config.brand`, `white_label` | config | implemented in selector and 3-D scene |

## Triggers and automation that exist in the repo
- Dashboard background task steps the twin at 1 Hz (simulation) — real worker, starts with the API.
- Edge computer `systemd` units (firmware/ben-edge: OnLogic Karbon 400 or Revolution Pi on BEN Controls Lite) run the API, broker, OpenThread Border Router, nightly backup — implemented, unverified on hardware. The PLC (PLCnext) owns the interlocks and is polled by the edge computer.
- CI (`.github/workflows/ci.yml`) runs the Python suite and firmware native tests on push.

## Shared state and ownership
Per-unit SQLite on the edge computer is the system of record. Schreiber AI's copy (if the customer opts in) is a replica. Customer owns the data; export is one click (`/api/export.csv`).
