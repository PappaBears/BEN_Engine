# BEN Engine — Controls architecture specification

**Schreiber AI · IFC Rev A · 2026-11-07** · Companion to `spec/PROTOCOL.md` (wire format), `BEN-NODE-v1.md`, `BEN-GATEWAY-v1.md`, and the one-line diagrams in `wiring/`.

## 1. Rules that do not change

1. **Life-safety is hardwired.** Smoke detection, clean-agent release, EPO and door interlocks for release are relay-and-wire circuits per NFPA 72 / NFPA 2001 / NFPA 70 Art. 645, supervised by a listed releasing panel. The controls bus (MQTT, Modbus, SNMP) carries **monitoring only**: nodes read the panel's dry aux contacts. No message on any network can start, stop or inhibit a release or an EPO. See `wiring/05_life_safety_one_line.svg`.
2. **No cloud dependency.** A unit with no WAN runs forever: broker, time, history, dashboard and twin are all on the gateway. Remote support is an outbound-only VPN the customer switches on.
3. **Local-first data.** Every record is written to the gateway's SQLite first; export and sync are copies.
4. **Signed firmware.** Nodes accept only images with a matching SHA-256 and (production units) a Secure Boot v2 signature. Procedure in `firmware/README.md`.
5. **Fail to the equipment's own controller.** If the controls layer dies, cooling units, UPS and PDUs continue on their own local setpoints. The node's `relay1` ("cooling enable") is failsafe and releases to local control.

## 2. Zones and conduits (IEC 62443-3-2)

| Zone | Members | Security level target | Conduits in / out |
| --- | --- | --- | --- |
| **Z1 Controls** (VLAN 20, 10.20.0.0/24) | BEN nodes, PoE switch, Modbus-TCP meter gateway / meters, cooling unit controllers, CDU, UPS NMC, rack PDUs (SNMP), **gateway eth0** | SL-T 2 | only to Z2 via the gateway host itself (no routing); gateway initiates all polls; nodes publish only to the gateway |
| **Z2 Management** (VLAN 30, 10.30.0.0/24) | gateway eth0.30 (API :8000, MQTT TLS :8883, WSS :9001, SSH), dashboard screen / engineering laptop | SL-T 2 | authenticated TLS to gateway only; no path into Z1 except through the API |
| **Z3 Customer IT** | the customer's servers, switches, their own firewall and WAN | customer's | **none**. Physically separate switch or VLANs the controls switch never trunks. The gateway has no interface here. Shared only: mains power and the room. |
| **Z4 Remote support** (wg0) | Schreiber AI support concentrator | SL-T 2 | outbound-only WireGuard from the gateway; inbound SSH/API on wg0 only; customer-switched, 48 h auto-off; disabled by default |
| **Z0 Life safety** | releasing panel, detectors, EPO stations, agent cylinders | n/a (not networked) | dry contacts into Z1 nodes, monitor only |

Firewall (gateway `nftables.conf`): input/forward/output **policy drop**; forward chain empty (the gateway never routes). Nodes get DHCP from the gateway **without a default route**.

Equipment in Z1 that has a web UI (UPS NMC, PDU, cooling controller) keeps its own credentials, changed at commissioning and recorded in the turnover package; those UIs are reachable only from the gateway host (`ssh -L` from Z2).

## 3. Data flow

```
sensors ─► BEN node (calibrate, 1 Hz JSON, 1 h buffer) ─MQTT 1883─► Mosquitto on gateway
meters/UPS/cooling/PDU ─Modbus TCP/RTU, SNMP─► ben_engine.api pollers ─► normalised equip topics
Mosquitto ─► ben_engine.api: alarm engine, twin, SQLite history ─► ben/<unit>/alarm, ben/<unit>/twin/state
ben_engine.api ─HTTPS/WSS (Z2)─► dashboard (live, 3D twin, sweeps, CSV export, I/O test)
ben_engine.api ─cmd topic─► nodes (set_output, cal, tare, identify, reboot, ota)  ─► ack
nightly ─► SQLite .backup ─► USB / NAS
```

Rates: node telemetry 1 Hz (0.2–10 Hz), node status 10 s retained, equipment 1–10 s, alarms on change, twin 1 Hz.
Every message has `ts` (gateway-synced unix seconds) and `seq`; the gateway flags gaps and `replay:true` back-fills.

## 4. Time synchronisation

- The gateway runs **chrony** and serves both VLANs. Sources: upstream NTP when WAN/VPN exists, optional GPS/PPS HAT, otherwise `local stratum 10 orphan` — the unit always shares one clock even if it is wrong in absolute terms.
- Nodes SNTP to 10.20.0.1 (DHCP option 42). Until the first fix a node sends `ts=0`, `clock_valid=false`; the gateway re-times those records from the node's `uptime_s` once the first valid status arrives.
- Steps > 2 s are counted (`steps` diagnostic) and reported; a node with no sync for 24 h raises `"clock not synced"` in status.
- SQLite stores gateway receive time and node `ts` separately so both can be audited.

## 5. Retention

| Data | Where | Retention |
| --- | --- | --- |
| 1 Hz node telemetry, equipment telemetry | SQLite `/var/lib/ben/ben.sqlite` | 400 days raw (covers a full seasonal cycle), then 1-min aggregates kept indefinitely |
| Alarms, acks, commands (who/what/when) | SQLite, append-only table | indefinitely (audit trail) |
| Node calibration records (`cal_id`, coefficients, reference, uncertainty) | SQLite + `/var/lib/ben/reports` | indefinitely |
| Commissioning and sweep reports | `/var/lib/ben/reports` | indefinitely |
| Broker/API logs | `/var/log/ben`, `/var/log/mosquitto` | 30 days / 8 weeks, compressed |
| Nightly backup | USB / NAS `/mnt/ben-backup/<unit>/` | 30 copies (≈ 1 month) + customer may mirror |
| Node ring buffer | node RAM | 1 h at 1 Hz, lost on node power loss |

## 6. What a node does when it loses the gateway

| Time since last gateway contact | Node behaviour |
| --- | --- |
| 0 s (TCP/MQTT session drops) | Keeps measuring at the same rate; every record goes into the 1 h ring buffer with original `ts`/`seq`. Reconnect attempts every 5 s. **Failsafe outputs drop at once** on link loss (the broker lives on the gateway: no session = no gateway). |
| 60 s without any contact (session up but silent, e.g. broker alive, API dead) | Failsafe outputs drop (`relay1` cooling enable → cooling unit runs on its own controller). Non-failsafe outputs hold their last state. IDENT LED blinks 1 Hz. Status carries `"gateway lost: failsafe active"`. |
| up to 1 h | Buffer fills; local alarm table (ASHRAE A1, leak, door, dP) keeps evaluating so the LED and, where wired, `relay4` can signal locally. |
| > 1 h | Oldest records are overwritten (`dropped` counter reported on reconnect). |
| on reconnect | Buffered records are replayed oldest-first, 20 per second, marked `"replay":true` with empty `raw`; live samples queue behind them so `seq` stays monotonic. Commanded output states received during the loss are applied once contact is restored. Failsafe clears immediately. |
| on power loss | Buffer is lost (RAM). Calibration, identity, output *configuration* survive in NVS; outputs come up **off** and wait for the gateway's first `set_output`. |

The gateway side mirrors this: a node silent for 30 s raises a `warn` alarm, 5 min an `alarm`; the twin falls back to model-predicted values for that rack and marks them "estimated" on the dashboard.

## 7. Failsafe outputs table

| Output | Function | Energised = | Failsafe? | State on gateway loss | State on node power-up | Why |
| --- | --- | --- | --- | --- | --- | --- |
| relay1 | Cooling unit remote enable (in series with the unit's own enable input) | enable follows BEN | **yes** | drops → unit reverts to its local controller / default "run" | off (unit runs on local control until commanded) | losing controls must never stop cooling |
| relay2 | Container lights | lights on | no | holds | off | comfort only |
| relay3 | Fan boost (economizer / RDHx fan override) | boost | no | holds (unit's own thermostat still limits) | off | holding boost is safe; dropping it mid-event is not |
| relay4 | Spare (default assignment: local beacon "controls fault") | beacon on | no | holds (app sets it when the gateway is lost) | off | visible local indication |
| — | Fire release, EPO, door release | — | **not connected** | — | — | hardwired per §1 |

Alarm inhibit, UPS shutdown, breaker trip and generator start are **not** node outputs; they belong to the ATS controller, the UPS and the releasing panel respectively. The gateway may *request* a UPS test over SNMP; it cannot shut a UPS down.

## 8. Commissioning acceptance for the controls layer

1. Every node shows a retained status within 2 min of power-up; `clock_valid:true` within 5 min.
2. `mosquitto_pub` as `nodeA` to `nodeB`'s topic is denied; anonymous connect is denied; TLS listener presents the unit CA.
3. From the customer IT VLAN, no gateway port answers; from the controls VLAN, only 1883/123/67 answer.
4. Pull the gateway Ethernet for 90 s: relay1 drops within 2 s of link loss; dashboard back-fills with `replay:true`; `seq` has no gaps.
5. Press the EPO test station with the panel in test mode: node reports `"EPO/fire loop open"` within 1 s; **nothing on the bus changed the EPO state** (by construction).
6. Calibration: `set_cal` for each analog channel, `tare` on `dP_aisle` with both taps open to the same room; `get_cal` echoes `cal_id`; power-cycle the node; `get_cal` still echoes it.
7. Nightly backup produces a file with a valid sha256 and passes `PRAGMA integrity_check` when opened on a laptop.
