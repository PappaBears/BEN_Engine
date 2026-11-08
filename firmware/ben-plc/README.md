# BEN PLC — PLCnext project skeleton (BEN Controls Pro) and the Lite equivalent

**Controller:** Phoenix Contact **PLCnext AXC F 2152** (alternates Beckhoff CX9240, WAGO PFC200) with
**Axioline F** I/O in the UL 508A BEN Controller panel (`design/specs/BEN-CONTROLLER-v1.md`). Tooling:
PLCnext Engineer 2024.x. **Status: structured text written, NOT compiled** (no PLCnext Engineer on the
build host); the I/O names, task configuration and Modbus server are described here and must be created in
the Engineer project at first build.

**On BEN Controls Lite (BEN Micro / BEN 10 option) there is no PLC.** The *same* interlock state machine
runs as a Python service on the RevPi: `software/ben_engine/interlocks.py` (class `Interlocks`) driven by
`firmware/ben-edge/lite/ben_interlocks_service.py`, with a hardware watchdog relay in the cooling-enable
chain. That Python class is the **executable reference** for `BenInterlocks.st`: the unit tests in
`tests/test_interlocks.py` (16 tests: N+1 sizing, lead rotation, failover on fault contact and on missing run
feedback, retry-then-latch, leak isolation latch and valve-fault pump stop, edge loss advisory-only, trim
clamp, door/EPO monitor-only, generator start failure, failover sweep request gating, mode OFF, register
image, failsafe table) are the acceptance for both. Change the Python first, run the tests, then mirror the
change in the ST.

## Files

| File | Purpose |
| --- | --- |
| `BenInterlocks.st` | IEC 61131-3 ST program: cooling N+1 sequencing and failover, leak isolation, door/EPO monitoring, ATS/generator supervision, edge watchdog, test requests, failsafe enable chain, Modbus image |
| `modbus_map.csv` | The register map the edge computer reads (identical to `spec/PROTOCOL.md`); `ben-plc-bridge` loads this file, so the two cannot drift |
| (to create in PLCnext Engineer) | `FB_AxiolineScale` (RTD4/AI4 scaling into `MB.aiRtd_x100`, `MB.awAi_uA`), `FB_CoolingModbus` (Modbus RTU master to the cooling units: run/fault/setpoint), `FB_Crc16` (project CRC into `GVL_Plant.wProjectCrc`), HMI pages |

## IEC 61131-3 program structure

| Task | Cycle | POUs | Notes |
| --- | --- | --- | --- |
| `BenInterlocks` (cyclic, priority 1) | 100 ms | `BenInterlocks` | everything safety-adjacent; no Modbus TCP client in this task |
| `BenIo` (cyclic, priority 2) | 100 ms | `FB_AxiolineScale` | scales Pt1000 (RTD4, 4-wire/3-wire) to ×0.01 °C, 4–20 mA (AI4 I 1H) to µA, writes `rSupplyC`, `rReturnC`, `rOutdoorC`, `rAisleDp`, `rRh`, `rItKw` |
| `BenComms` (cyclic, priority 5) | 500 ms | `FB_CoolingModbus`, `FB_Crc16` | Modbus RTU (RS-485, AXL F RS UNI) to cooling unit controllers: read run/fault/supply temp, write supply setpoint = `rSetpointC + trim`; a comms loss on a unit sets `abCoolFaultIn[i]` after 3 missed polls |
| Modbus TCP server | — | PLCnext "Modbus TCP Server" app (or OPC UA server, native) | serves `MB` struct at 40001.. per `modbus_map.csv`, unit id 1, port 502; only 40004/40006/40007 writable (server ACL) |

### Function by function (all in `BenInterlocks.st`, mirrored from `interlocks.py`)

1. **Cooling sequencing N+1** — `UnitsRequired()` = ⌈IT kW / (unit kW × 0.85)⌉ + redundancy (N: 0, N+1: 1, 2N: N), capped at installed units. Units start lead-first, round robin, skipping faulted/latched. Weekly lead rotation. Anti-short-cycle 5 min.
2. **Failover** — a unit is faulted by its own fault contact **or** by missing run feedback 90 s after command. The faulted unit's command drops and the sequencer brings the next healthy unit in on the same scan. One automatic retry after 10 min; a unit that never ran ≥ 5 min before faulting **latches** until an HMI reset (the edge cannot reset). `COOL_FAILOVER_CNT` / `COOL_LAST_FAILOVER_S` give the audit trail for the monthly proof-of-redundancy sweep (BEN Care).
3. **Leak isolation** — hardwired SeaHawk zone contacts only (Pod `leak` is advisory). A wet zone **latches** its isolation valve closed; if the valve's closed limit switch is not seen within 30 s → `ISO_VALVE_FAULT`; valve fault **and** zone still wet → `CDU_PUMP_STOP`. Reset from the HMI after inspection.
4. **Door / EPO monitoring** — door open > 5 min → alarm. EPO loop and fire panel aux contacts are **read into the alarm word only**; there is no output in this program that can reach the loop or the panel (CONTROLS_SPEC.md §1).
5. **Generator / ATS supervision** — the ATS starts the generator; the PLC supervises: utility lost and no run contact within 60 s → `GEN_FAULT`; run time, cooldown, ATS source enum.
6. **Watchdog with the edge computer** — the edge writes `EDGE_WATCHDOG` every second; unchanged 30 s → `EDGE_LOST`: trim ignored, tests refused, sequencing continues unchanged. Edge loss alone lights no beacon.
7. **Test requests** — `TEST_REQUEST` = 1 stops the lead unit once (failover sweep) and is accepted only in AUTO, edge present, no alarm other than `EDGE_LOST`/`ATS_ON_GEN`. Always cleared.
8. **Failsafe enable chain** — `bCoolingEnable` (relay in series with every unit's remote-enable input) is TRUE only in AUTO/TEST with at least one healthy unit. A PLC stop, power loss or watchdog trip de-energises the relay → every unit runs on its own local controller.

## Failsafe table (PLC side; the edge side is in `CONTROLS_SPEC.md` §7)

| Output | PLC alive, edge lost | PLC stopped / power lost / watchdog | PLC in MANUAL |
| --- | --- | --- | --- |
| Cooling unit commands | sequencer continues on base setpoint | de-energised → units on local control (enable chain open) | frozen; HMI forces |
| Isolation valves | unchanged (leak logic needs no edge) | hold position (spring-return option closes); CDU's own leak logic governs | frozen |
| CDU pump stop | unchanged | released | frozen |
| Cooling enable relay | held | **drops** | held if healthy |
| Supply setpoint trim | 0 (base setpoint) | n/a | 0 |
| Beacon | lit for any non-edge alarm | lit by relay NC contact | lit |
| Fire / EPO | **not connected** (monitor only) | — | — |

## Hardware watchdog (Pro vs Lite)

- **Pro:** the AXC F 2152 has a hardware watchdog on the cyclic task (task watchdog 200 ms → controller STOP → outputs de-energise). The enable chain relay is on a DOR LC/1 relay output and drops on STOP.
- **Lite:** `ben-interlocks.service` pets the RevPi `/dev/watchdog` (60 s) and systemd `WatchdogSec=10`; RevPi DIO `O_14` → relay KW1 in the enable chain. Details in `firmware/ben-edge/lite/README.md`.

## Commissioning steps specific to the PLC

1. Load the project; record `PLC_PROJECT_CRC` in `/etc/ben/ben.env` (`BEN_PLC_PROJECT_CRC`) so `plcN` status reports `attested:true`.
2. Set `GVL_Plant` (unit count, unit kW, zones, doors, redundancy, setpoint) from the unit's `ben_engine` config; the commissioning script cross-checks `COOL_N_REQUIRED` against `Config.derived()`.
3. Run `tests/test_interlocks.py` scenarios against the live PLC with the I/O simulator (force inputs, read registers): failover, leak latch, valve fault, edge loss, mode OFF. Record in the FAT/SAT report.
4. Verify the enable chain: PLC STOP → every unit's remote enable opens within 1 s and the units keep cooling on local control.
