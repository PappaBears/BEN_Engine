# BEN Engine — Controls architecture specification

**Schreiber AI · IFC Rev B · 2026-11-08** · Companion to `spec/PROTOCOL.md` (wire format), `BEN-POD-v1.md`, `BEN-CONTROLLER-v1.md`, `firmware/ben-plc/README.md` (interlocks), and the one-line diagrams in `wiring/`. Industrial platform per `docs/CONTROLS_HARDWARE_DECISION.md`; two controls tiers (Lite: RevPi software controller; Pro: PLCnext + edge computer) with identical zones, protocol and acceptance.

## 1. Rules that do not change

1. **Life-safety is hardwired.** Smoke detection, clean-agent release, EPO and door interlocks for release are relay-and-wire circuits per NFPA 72 / NFPA 2001 / NFPA 70 Art. 645, supervised by a listed releasing panel. The controls layer (MQTT, Modbus, SNMP, Thread) carries **monitoring only**: the controller's DI and Pod DI read the panel's dry aux contacts. No message on any network, and no output of the PLC or RevPi program, can start, stop or inhibit a release or an EPO. See `wiring/05_life_safety_one_line.svg`.
2. **No cloud dependency.** A unit with no WAN runs forever: broker, time, history, dashboard, twin and interlocks are all inside the BEN Controller. Remote support is an outbound-only VPN the customer switches on.
3. **Local-first data.** Every record is written to the edge computer's SQLite (LUKS, TPM-sealed on Pro) first; export and sync are copies.
4. **Signed firmware, attested devices.** Pods accept only images with a matching SHA-256 **and** a valid ECDSA P-256 signature with non-decreasing version (Gecko Bootloader); every Pod attests at join and daily; the edge computer measures its boot with the TPM; the PLC project CRC is checked against the commissioned value. Procedures in `firmware/README.md`.
5. **Fail to the equipment's own controller.** If the controls layer dies, cooling units, CDU, UPS and PDUs continue on their own local setpoints. The **cooling-enable chain** (a hardware relay contact in series with every unit's remote-enable input) is driven by the PLC output (Pro) or the watchdog relay (Lite) and opens on any controller stop.
6. **Deterministic interlocks live in the controller, not in the data layer.** The edge computer advises (setpoint trim, test request); it never commands a valve or a unit. Loss of the edge changes nothing in the interlocks.

## 2. Zones and conduits (IEC 62443-3-2)

| Zone | Members | Security level target | Conduits in / out |
| --- | --- | --- | --- |
| **Z1 Control** (VLAN 20, 10.20.0.0/24 + fd00:ben:1::/64) | **PLC** (Pro) with Axioline I/O and wired transmitters · managed switch · Modbus-TCP meter gateway / meters · cooling unit controllers · CDU · UPS NMC · rack PDUs (SNMP) · **Pod E** Ethernet path · edge computer's controls NIC | SL-T 2 (PLC per IEC 62443-4-1 certified process) | PLC ↔ edge: Modbus TCP 502 / OPC UA 4840 initiated by the edge only; edge polls equipment; nothing in Z1 reaches Z1.5 except through the edge host's own listeners (8883 mTLS, 123) |
| **Z1T Thread mesh** (fd00:ben::/64) | **BEN Pods**, border router RCP(s) | SL-T 2 (Secure Vault High / PSA L3 components) | DTLS/J-PAKE join via the Commissioner on the edge; mTLS MQTT to `fd00:ben::1:8883` only; SNTP 123; CoAP 5683 (OTA, attestation); the border router is a **stub**: no route from Thread to Z1 or Z2 |
| **Z1.5 Data** (the edge computer host) | Mosquitto, `ben_engine.api`, SQLite, OTBR, chrony, PLC bridge (Pro: Karbon 400; Lite: the same RevPi that runs the interlocks, in separate systemd units) | SL-T 2 | Z1 and Z1T terminate on its listeners; Z2 reaches API/MQTT over TLS; never forwards packets between zones (`forward` policy drop) |
| **Z2 Management** (VLAN 30, 10.30.0.0/24) | edge management NIC (API :8000, MQTT TLS :8884, WSS :9001, SSH), panel HMI / dashboard screen, engineering laptop | SL-T 2 | authenticated TLS to the edge only; no path into Z1/Z1T except through the API |
| **Z3 Customer IT** | the customer's servers, switches, their own firewall and WAN | customer's | **none**. Separate switch or VLANs the controls switch never trunks. No controller interface here. Shared only: mains power and the room. |
| **Z4 Remote support** (wg0) | Schreiber AI support concentrator | SL-T 2 | outbound-only WireGuard from the edge; inbound SSH/API on wg0 only; customer-switched, 48 h auto-off; disabled by default |
| **Z0 Life safety** | releasing panel, detectors, EPO stations, agent cylinders | n/a (not networked) | dry contacts into Z1 DI (and Pod DI2), monitor only |

Firewall (edge `nftables.conf`): input/forward/output **policy drop**; forward chain empty. Z1 DHCP hands out no default route; radvd advertises no default router.
Equipment in Z1 with a web UI (UPS NMC, PDU, cooling controller, PLC web HMI) keeps its own credentials, changed at commissioning and recorded in the turnover package; those UIs are reachable only from the edge host (`ssh -L` from Z2).

Pod identity: certificate CN = MQTT username; ACL per Pod; a Pod with `attested:false` is alarmed and its acks ignored. Thread network key is per unit, sealed in the turnover package.

## 3. Data flow

```
Pt1000/ΔP/RH/leak transmitters ─4–20 mA / RTD / contacts─► PLC (Pro) or RevPi DIO/AIO (Lite): scale, interlocks, failsafe chain
PLC / software controller ─Modbus TCP 502 (1 Hz poll by edge)─► ben-plc-bridge ─► ben/<unit>/plc/interlocks, ben/<unit>/node/plcN/*
rack/door/outdoor sensors ─► BEN Pod (calibrate, 1 Hz JSON, 1 h buffer) ─Thread/IPv6, mTLS 8883─► Mosquitto on the edge
meters/UPS/cooling/PDU ─Modbus TCP/RTU, SNMP─► ben_engine.api pollers ─► normalised equip topics
Mosquitto ─► ben_engine.api: alarm engine, twin, SQLite history ─► ben/<unit>/alarm, ben/<unit>/twin/state
ben_engine.api ─HTTPS/WSS (Z2)─► dashboard (live, 3D twin, mesh health, sweeps, CSV export, I/O test)
ben_engine.api ─cmd topic─► Pods (set_output, cal, tare, identify, reboot, ota, attest) ─► ack
ben-plc-bridge ─3 registers (EDGE_WATCHDOG, SUPPLY_TRIM_x10, TEST_REQUEST)─► controller   (the only edge→control write path)
nightly ─► SQLite .backup ─► USB / NAS
```

Rates: Pod telemetry 1 Hz (0.2–10 Hz), Pod status 10 s retained, PLC poll 1 Hz, equipment 1–10 s, alarms on change, twin 1 Hz. Every message has `ts` and `seq`; the edge flags gaps and `replay:true` back-fills.

## 4. Time synchronisation

- The edge runs **chrony** and serves 10.20.0.1, 10.30.0.1 and `fd00:ben::1`. Sources: upstream NTP when WAN/VPN exists, optional GNSS on COM1, otherwise `local stratum 10 orphan`.
- Pods SNTP over Thread to `fd00:ben::1` (OpenThread SNTP client); Pod E and the PLC to 10.20.0.1. Until the first fix a Pod sends `ts=0`, `clock_valid=false`; the edge re-times those records from `uptime_s`.
- The PLC's own clock is synced by NTP from the edge; register timestamps are edge receive time (the PLC image carries no `ts`).
- SQLite stores edge receive time and device `ts` separately so both can be audited.

## 5. Retention

| Data | Where | Retention |
| --- | --- | --- |
| 1 Hz Pod telemetry, PLC image, equipment telemetry | SQLite `/var/lib/ben/ben.sqlite` (LUKS) | 400 days raw, then 1-min aggregates kept indefinitely |
| Alarms, acks, commands, interlock events (`COOL_FAILOVER_CNT` transitions, leak latches, mode changes) | SQLite, append-only | indefinitely (audit trail; feeds BEN Care proof-of-redundancy) |
| Pod calibration records, certificate issue/renewal, attestation results | SQLite + `/var/lib/ben/reports` | indefinitely |
| Commissioning and sweep reports | `/var/lib/ben/reports` | indefinitely |
| Broker/API/bridge logs | `/var/log/ben`, `/var/log/mosquitto` | 30 days / 8 weeks |
| Nightly backup | USB / NAS `/mnt/ben-backup/<unit>/` | 30 copies |
| Pod ring buffer | Pod RAM | 1 h at 1 Hz, lost on Pod power loss |
| Thread dataset, LUKS recovery passphrase, PLC project | turnover package (sealed) + OTBR volume / PLC SD | life of unit |

## 6. Loss behaviour

### 6a. A Pod loses the broker (edge down, RCP down, or mesh partition)

| Time since last broker contact | Pod behaviour |
| --- | --- |
| 0 s (TLS/MQTT session drops) | Keeps measuring; every record goes into the 1 h ring buffer with original `ts`/`seq`. Reconnect attempts every 5 s (re-attach to another parent/border router if the mesh offers one). **Failsafe outputs drop at once** on session loss. |
| 60 s silent session | Failsafe relays drop; non-failsafe hold. IDENT LED 1 Hz. Status carries `"gateway lost: failsafe active"`. |
| up to 1 h | Buffer fills; local alarm table keeps evaluating for the LED / Pod E relay2 beacon. |
| > 1 h | Oldest records overwritten (`dropped` counter on reconnect). |
| reconnect | Oldest-first replay 20/s, `replay:true`, live queued behind; commanded outputs applied; re-attestation. |
| power loss | Buffer lost; identity, certificate, calibration, Thread dataset survive in NVM3/Secure Vault; outputs come up off. |

### 6b. Gateway-loss behaviour, split by controller tier

| Event | Pro (PLC + edge) | Lite (RevPi) |
| --- | --- | --- |
| **Edge computer lost** (Karbon off / API dead / Lite: `ben-api` or broker crashed) | PLC: `EDGE_LOST` after 30 s; interlocks, sequencing, leak isolation, enable chain **unchanged**; trim → 0; tests refused. Pods buffer; dashboard dark; history gap back-filled on restore. No field alarm (beacon off). | Interlock service is a separate unit and continues; `EDGE_LOST` set the same way; Pods buffer; dashboard dark until restart (systemd restarts the API within 3 s). |
| **Controller lost** (PLC STOP / power; Lite: interlock service stalled) | Enable-chain relay drops (DOR output de-energised) → every cooling unit on its own controller; valves hold; CDU own leak logic; edge raises `critical` "controller comms lost"; `plcN` stale; Pods and history continue. | `WatchdogSec` restart in 10 s; if the loop is truly dead, hardware watchdog reboots the RevPi in 60 s and piControl zeroes outputs → KW1 opens → units on local control. History pauses during the reboot (Pods buffer). |
| **Both lost** | Units on local control; Pods buffer 1 h; life safety unaffected (hardwired). | Same (single box). |
| **Border router RCP lost** | BEN 150/500: Pods re-attach via RCP2 within 60 s; BEN 30: Pods buffer until the RCP is back; Pod E falls to Ethernet (`path:"eth"`) or RS-485 to the PLC. | Pods buffer; Pod E falls to Ethernet/RS-485. |
| **Switch lost** | PLC and edge keep running; edge loses meters/UPS/PDU polls (equipment "stale"); Pods unaffected (Thread); PLC keeps RTU devices. | Same. |
| **24 VDC PSU 1 lost** | Redundancy module → `PSU_REDUNDANCY_OK` = 0, alarm, no functional change. | Supercap ride-through 30 s then orderly shutdown; alarm. |

The edge side mirrors this: a Pod silent for 30 s raises `warn`, 5 min `alarm`; a PLC heartbeat frozen 3 s raises `critical`; the twin falls back to model-predicted values and marks them "estimated".

## 7. Failsafe table — split by executor

### 7a. Controller outputs (PLC on Pro; RevPi DIO behind KW1 on Lite) — authoritative, see `firmware/ben-plc/README.md`

| Output | Function | Energised = | Controller alive, edge lost | Controller stopped / watchdog | Why |
| --- | --- | --- | --- | --- | --- |
| Cooling unit remote enables (N) | unit may run under BEN sequencing | run | sequencer continues on base setpoint | **de-energised** → units on local control (enable chain open) | losing controls must never stop cooling |
| Enable-chain relay | hardware permission for the above | chain closed | held | **drops** | single hardware point of failsafe |
| Isolation valves (per leak zone) | close on hardwired leak | closed | unchanged | hold (spring-return option closes) | leak logic needs no edge |
| CDU pump stop | valve fault + zone wet | stop | unchanged | released → CDU protection governs | |
| Beacon | controls fault | lit | lit for any non-edge alarm | lit by NC contact | visible local indication |
| — | Fire release, EPO, door release | — | **not connected** | — | hardwired per §1 |

### 7b. Edge-layer outputs (advisory; `ben_engine.api`, `ben-plc-bridge`)

| Output | Path | On edge loss | On controller loss |
| --- | --- | --- | --- |
| `SUPPLY_TRIM_x10` | Modbus write, clamped ±2 K | controller ignores after 30 s | n/a |
| `TEST_REQUEST` | Modbus write | refused (needs edge present) | n/a |
| `EDGE_WATCHDOG` | Modbus write 1 Hz | stops → `EDGE_LOST` | n/a |
| Pod `set_output` (relay1/relay2 on Pod E: beacon, lights, fan boost) | MQTT cmd | relay1 drops after 60 s (failsafe), relay2 holds | unchanged |
| UPS self-test request, PDU outlet cycle | SNMP (allow-listed OIDs) | none | none |

Alarm inhibit, UPS shutdown, breaker trip and generator start are **not** controls outputs; they belong to the ATS controller, the UPS and the releasing panel respectively.

## 8. Commissioning acceptance for the controls layer (both tiers unless noted)

1. Every Pod shows a retained status within 2 min of power-up with `attested:true`, `parent` and `lqi` populated; `clock_valid:true` within 5 min.
2. A Pod certificate from a foreign CA is refused at the TLS handshake; `pod3` publishing on `pod4`'s topic is denied; anonymous connect is denied; the management listener presents the unit CA.
3. From the customer IT VLAN, no controller port answers; from the controls VLAN only 8883/123/67 (edge) and 502/4840 (PLC, Pro) answer; from a Pod address only 8883/123/5683.
4. **Controller stop test:** PLC STOP (Pro) / `systemctl stop ben-interlocks` (Lite): enable chain opens within 1 s, every cooling unit keeps running on local control; dashboard shows "controller comms lost" within 5 s.
5. **Edge stop test:** stop `ben-plc-bridge` 35 s: `EDGE_LOST` = 1, sequencing unchanged, trim ignored; on restart `EDGE_LOST` = 0.
6. **Failover sweep:** `TEST_REQUEST` = 1 in AUTO: lead unit stops, standby starts within the start window, `COOL_FAILOVER_CNT` increments, report signed and stored.
7. **Leak test:** short a SeaHawk zone: isolation valve closes (limit switch within 30 s), `LEAK_ISOLATION_ACTIVE`, latched until HMI RESET; block the valve: `ISO_VALVE_FAULT` and `CDU_PUMP_STOP`.
8. Press the EPO test station with the panel in test mode: controller `EPO_LOOP_OK` = 0 and Pod DI2 report within 1 s; **nothing on the bus changed the EPO state** (by construction).
9. Pull RCP1 (BEN 150/500): Pods re-attach via RCP2 within 60 s; `seq` has no gaps after replay.
10. Calibration: `set_cal` on each analog channel, `tare` on `dP_aisle`; `get_cal` echoes `cal_id`; power-cycle the Pod; `get_cal` still echoes it. PLC-side: RTD channel against a reference bath at two points, recorded in `GVL_Cal`.
11. Nightly backup produces a file with a valid sha256 and passes `PRAGMA integrity_check`; Pro: `clevis luks list` shows the TPM pin and a reboot unlocks unattended.
12. Lite only: `kill -STOP` the interlock service: restart within 10 s, O_14/KW1 state logged; hardware watchdog reboot test with units on local control throughout.
