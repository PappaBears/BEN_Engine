# BEN Controls protocol (v1.1 — industrial platform)

**Supersedes v1 (hobby gateway/nodes). Topics and JSON payloads are unchanged; this revision changes
what sits at each end of the wire and adds identity, attestation, the Thread join procedure and the
PLC ↔ edge register map.** Binding decision: `docs/CONTROLS_HARDWARE_DECISION.md`.

## Two controls tiers, one protocol

Controls scale with the box. Both tiers run the **same topics, the same JSON, the same `ben_engine`
edge software and the same BEN Pods on the BEN Mesh**; they differ in what executes the interlocks.

| Tier | Fitted to | Controller | Interlocks run in | I/O |
| --- | --- | --- | --- | --- |
| **BEN Controls Lite** | BEN 5; optional on BEN 30 | **KUNBUS Revolution Pi RevPi Connect 4** (or Connect S), industrial DIN-rail, UL/CE, running `ben_engine` edge software **and** the software interlock controller (`ben_engine/interlocks.py`) with a **hardware watchdog relay** (RevPi watchdog → relay in the cooling-enable chain) | software, on the RevPi (`firmware/ben-edge/lite`) | RevPi DIO / AIO modules via piControl; transmitters and SeaHawk contacts on DIO/AIO; no PLC |
| **BEN Controls Pro** | BEN 150 / BEN 500 / BEN 2000; optional on BEN 30 | **Phoenix Contact PLCnext AXC F 2152** PLC + **Axioline F** I/O for control; **OnLogic Karbon 400** edge computer for data/twin/broker/border router | IEC 61131-3 on the PLC (`firmware/ben-plc`), executable reference = the same Python class | Axioline F modules |

In **Lite** the "PLC register map" below is **served by the RevPi software controller** itself (a Modbus
TCP server on the RevPi, same addresses, same meanings; `ben/<unit>/plc/interlocks` is published from the
same state). A dashboard, a commissioning script or a customer BMS therefore cannot tell the tiers apart on
the wire; only `PLC_MODE` bit 8 (`LITE`) says which one is running.

The rest of this document describes the Pro platform and notes where Lite differs.

Every BEN unit has one **BEN Controller** and N sensing points:

| Element | Hardware | Role on this protocol |
| --- | --- | --- |
| **BEN Controller — control** | PLC **Phoenix Contact PLCnext AXC F 2152** + **Axioline F** remote I/O in a UL 508A panel (`design/specs/BEN-CONTROLLER-v1.md`) | Deterministic interlocks and sequencing: cooling N+1 start/stop and failover, leak isolation valves, door/EPO monitoring, generator/ATS supervision. Normalises the **wired industrial transmitters** (Pt1000 RTD strings, Setra 264 / Dwyer MS2 ΔP, Vaisala HMD humidity, RLE SeaHawk leak controller) and exposes them plus the interlock states to the edge computer over **Modbus TCP** (OPC UA optional). Program: `firmware/ben-plc`. |
| **BEN Controller — data** | Industrial edge computer **OnLogic Karbon 400** (alternate Siemens IPC227G), Ubuntu/Debian LTS, TPM 2.0 (`firmware/ben-edge`) | Runs `ben_engine` (API, twin, history, sweeps, commissioning), the **Mosquitto** broker (mTLS), chrony, the **OpenThread Border Router** (OTBR) with MGM240P RCP(s), and the Modbus TCP / SNMP pollers for third-party equipment (UPS, cooling units, CDU, power meters, rack PDUs). |
| **BEN Pod** (wireless sensing) | Our PCB on the **Silicon Labs MGM240P** module (EFR32MG24, Secure Vault High). **Pod E**: 24 VDC or PoE 802.3af, Ethernet + RS-485 Modbus RTU to the PLC as the wired path, Thread as backup, 2 relays. **Pod W**: Thread only, 2 × AA LiFeS2 or 24 VDC (`design/specs/BEN-POD-v1.md`, `firmware/ben-pod`) | Publishes the node topics below over **MQTT/TLS on IPv6 end to end** (Thread 6LoWPAN → border router → broker). No gateway translation: the Pod is an IPv6 MQTT client. |
| **PLC-connected transmitters** | 4–20 mA, Pt1000 and dry-contact devices on Axioline I/O | Appear on the same node topics, published by the edge computer's `plc_bridge` under node ids `plc1..plcN` from the Modbus register map (§ PLC ↔ edge). |

Transport between Pods/edge is **MQTT 3.1.1 over TLS 1.2/1.3 with mutual X.509 authentication** on the
unit's isolated controls network (Thread mesh + controls VLAN; no internet dependency). Payloads are
JSON. Every message carries `ts` (unix seconds, synced to the edge computer via SNTP/Thread network
time) and `seq`.

## Topics (unchanged from v1)

| Topic | Direction | Rate | Payload |
| --- | --- | --- | --- |
| `ben/<unit>/node/<node_id>/telemetry` | Pod/PLC-bridge → edge | 1 Hz (configurable 0.2–10 Hz) | `{"ts":…, "seq":…, "ch":{"T_in_1":21.4,"T_in_2":21.9,"T_out_1":33.0,"RH":41.2,"dP_aisle":12.3,"leak":0,"door":0,"ai0_mA":12.01}, "raw":{…ADC counts…}, "cal_id":"c-2026-11-07-01"}` |
| `ben/<unit>/node/<node_id>/status` | Pod/PLC-bridge → edge | 10 s + on change | `{"fw":"1.0.0","uptime_s":…,"rssi":…,"ip":…,"heap":…,"errors":[], "cert_id":"…","attested":true,"parent":"…","lqi":…,"buffered":…,"clock_valid":true}` (retained) — see identity fields below |
| `ben/<unit>/node/<node_id>/cmd` | edge → Pod | on demand | `{"id":"uuid","op":"set_output","out":"relay1","value":1}` / `{"op":"get_cal"}` / `{"op":"set_cal","ch":"T_in_1","gain":1.002,"offset":-0.13,"cal_id":"…"}` / `{"op":"tare","ch":"dP_aisle"}` / `{"op":"identify"}` / `{"op":"reboot"}` / `{"op":"ota","url":"…","sha256":"…"}` |
| `ben/<unit>/node/<node_id>/ack` | Pod → edge | reply | `{"id":"uuid","ok":true,"result":{…}}` |
| `ben/<unit>/equip/<equip_id>/telemetry` | edge internal | 1–10 s | normalised third-party values: `{"kw":…, "kva":…, "v_ab":…, "i_a":…, "supply_c":…, "return_c":…, "fan_pct":…, "soc_pct":…, "runtime_min":…, "alarm":[]}` |
| `ben/<unit>/plc/interlocks` | edge internal (from PLC) | 1 s + on change | mirror of the interlock register block (§ PLC ↔ edge) as JSON: `{"ts":…, "cooling":[{"unit":1,"cmd":1,"run":1,"fault":0,"lead":1}], "leak_zone":[0,0,0,0], "iso_valve":[0,0,0,0], "door":[0,0], "epo_ok":1, "ats_source":"utility", "gen_run":0, "plc_mode":"auto", "edge_wd_ok":1}` (retained) |
| `ben/<unit>/alarm` | edge → all | on change | `{"id":…, "sev":"warn|alarm|critical", "src":"pod3/T_in_1", "msg":"Rack 3 inlet 27.8 C > 27 C (ASHRAE A1 max)", "active":true}` |
| `ben/<unit>/twin/state` | edge → dashboard | 1 Hz | full twin state (see INTERFACES.md) |

`ben/<unit>/plc/interlocks` is the only new topic; it is additive and optional for dashboards that only
read node/equip/alarm/twin.

### Identity and attestation fields in `status` (new in v1.1, additive)

| Field | Type | Meaning |
| --- | --- | --- |
| `cert_id` | string | Serial number (hex) of the Pod's device certificate issued by the Schreiber AI PKI. The broker ACL maps the TLS client certificate CN (`pod-<unit>-<node_id>`) to the topics the Pod may use; `cert_id` lets the edge audit which certificate instance is on the air after a rotation. |
| `attested` | bool | `true` when the Pod's last **attestation** passed: at every (re)join the Pod signs a challenge from the edge with its Secure Vault device key and reports the running firmware's signature verification result from the Gecko Bootloader. `false` → edge raises `alarm` "pod not attested" and ignores `set_output` acks from it. |
| `parent` | string | Thread parent router's RLOC16 (hex, e.g. `"0x5400"`), or `"leader"`/`"router"` when the Pod is itself a router. Mesh-health panel item. |
| `lqi` | int 0–255 | Link quality indicator to the parent (Thread MAC). |
| `rssi` | int dBm | RSSI to the parent (already in v1; `0` for Pod E on Ethernet). |
| `ip` | string | Pod's Thread mesh-local or OMR global IPv6 address (was IPv4 in v1). |
| `path` | string | Pod E only: `"eth"`, `"thread"` or `"rs485"` — which path is currently carrying telemetry. |

The PLC bridge publishes `status` for `plc1..N` with `cert_id` of the edge computer's own client
certificate, `attested:true` when the PLC's project checksum matches the commissioned one, and no mesh fields.

## Node channel map (BEN Pod v1 and PLC I/O)

| Channel | Pod sensor | PLC-connected equivalent | Interface | Range | Uncertainty (k=2) after calibration |
| --- | --- | --- | --- | --- | --- |
| `T_in_1..4`, `T_out_1..4` | Pt1000 class A, 3-wire, 24-bit RTD ADC (rack inlet/outlet strings) | Pt1000 on Axioline AXL F RTD4 | RTD | −50…150 °C | ±0.15 °C |
| `T_ref` | SHT45 | Vaisala HMD60 (T) | I²C / 4–20 mA | −40…125 °C | ±0.15 °C |
| `RH` | SHT45 | Vaisala HMD60 (RH) | I²C / 4–20 mA | 0…100 %RH | ±1.5 %RH |
| `dP_aisle` | SDP810-125Pa | Setra 264 ±125 Pa or Dwyer MS2 | I²C / 4–20 mA | ±125 Pa | ±0.4 Pa after tare (Pod); ±1 % FS (transmitter) |
| `leak` | leak-rope input (resistive, 2-wire) | RLE SeaHawk LD2100 / SeaHawk zone contacts | analog comparator / DI | 0/1 | — |
| `door` | dry contact | door switch on Axioline DI | DI | 0/1 | — |
| `ai0..1_mA` (Pod) / `ai0..3_mA` (PLC) | 165 Ω, isolated | Axioline AXL F AI4 I 1H | 4–20 mA | 4–20 mA | ±0.02 mA |
| `relay1..2` (Pod E only) | 10 A relay | Axioline DO relay | out | — | — |
| `pulse_kwh` | meter S0 pulse | Axioline counter input | DI IRQ | counter | — |

### Forward architecture channels (additive, v1.1; present only when the unit has the option)

Units built with the 800 VDC option (`power_architecture: dc800`) or the high-density liquid loop (`cooling: dlc_hd`, `docs/FORWARD_ARCHITECTURE_DECISION.md`) add these channels on the room Pod / PLC (`node1`); a unit without the option omits the keys. Twin state carries the same values under `state.dc` and `state.loop`; `sim_nodes.py` emits them with raw = engineering value × 10.

| Channel | Source | PLC-connected equivalent | Range | Uncertainty (k=2) | Alarm |
| --- | --- | --- | --- | --- | --- |
| `V_bus_pos`, `V_bus_neg` | DC bus pole voltage to ground (IMD / divider, isolated) | Axioline AI, 0–10 V from a 1,000 V class divider | ±1,000 V | ±2 V | `dc_bus_voltage` when the bus leaves the window (760–920 V, working assumption); a faulted pole reads toward 0 V |
| `I_bus` | DC bus shunt / Hall sensor | Axioline AI 4–20 mA | 0–3,200 A | ±0.5 % | — |
| `IMD_kohm` | Insulation monitoring device (Bender iso685 class), Modbus TCP | — | 1–10,000 kΩ | per device | `dc_insulation_low` < 500 kΩ (warn), `dc_ground_fault` < 100 kΩ (critical, first fault alarms, does not trip) |
| `dc_gf` | IMD relay contact | Axioline DI | 0/1 | — | mirrors `dc_ground_fault` |
| `T_loop_sup`, `T_loop_ret` | Pt1000 in the W45 supply / return manifold | Axioline RTD | 0–80 °C | ±0.15 °C | `loop_supply_high` > 45 °C (warn) |
| `F_loop` | Loop flow meter (magnetic / ultrasonic), 4–20 mA | Axioline AI | 0–2 × design L/min | ±2 % | `loop_flow_low` < 20 % of design (critical) |
| `cdu_pump1..N` | CDU pump running status | Axioline DI / CDU Modbus | 0/1 | — | `cdu_pumpN_fail` (alarm) with standby status |
| `loop_iso` | Row isolation valve closed (position switch) | Axioline DI | 0/1 | — | `loop_isolated` (critical) with the measured leak-to-isolation time |

Channel names and JSON keys are identical to v1 so `lib/bencore` and the edge parsers are unchanged.
A Pod that lacks a sensor omits the key. `relay3..4` exist only on PLC-connected I/O (`plcN`).

Calibration coefficients (`gain`, `offset`) are applied in the Pod and stored in **NVM3** with a
`cal_id`; the Pod always also reports `raw` so the edge can re-process. For PLC-connected channels the
coefficients are applied in the PLC (`GVL_Cal` in `firmware/ben-plc`) and `cal_id` is the PLC project's
calibration record id.

## Thread network join and credentials

1. **Pre-provisioned identity.** Each Pod leaves the provisioning cell with (a) a per-device ECDSA P-256
   key pair generated **inside** Secure Vault (non-exportable, wrapped to the chip), (b) a device X.509
   certificate `CN=pod-<serial>` signed by the **Schreiber AI Device CA** (intermediate, HSM-held), (c) the
   Schreiber AI root and the unit-independent Device CA chain, and (d) a Thread **PSKd** (pre-shared key for
   device) derived from the serial and printed as the QR/label code. Firmware is signed; the Gecko
   Bootloader refuses anything else (see `firmware/README.md`).
2. **Commissioning (MeshCoP).** The edge computer is the Thread **Commissioner** (OTBR). `ben-add-pod.sh
   <unit> <node_id> <serial>` reads the PSKd from the label, adds a joiner entry (EUI-64 + PSKd, 10 min window),
   and registers the certificate CN to the unit's broker ACL. The Pod runs the **Thread Joiner** role:
   DTLS handshake (J-PAKE with the PSKd) with the Commissioner, receives the network credentials (network
   key, PAN ID, channel, mesh-local prefix) and stores them in NVM3 **wrapped by Secure Vault**.
3. **Attach.** The Pod attaches as a **Router-Eligible End Device** (Pod E, 24 V Pod W) or **Sleepy End
   Device** (battery Pod W, poll period 1 s). It obtains an OMR IPv6 address from the border router and
   SNTP time from the edge computer (`fd00:ben::1`).
4. **Application TLS.** The Pod opens **MQTT over TLS 1.2 (mbedTLS, PSA Crypto)** to the broker at
   `fd00:ben::1:8883`, presenting its device certificate; the broker requires a client certificate
   signed by the Device CA and uses the CN as the MQTT username (`use_identity_as_username true`). Cipher
   suite `TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256`. The TLS private key never leaves Secure Vault; mbedTLS
   uses it through a PSA opaque key handle.
5. **Attestation.** The edge publishes `{"op":"attest","nonce":"<32 hex>"}` on the Pod's `cmd` topic after the
   first `status`. The Pod acks with `{"ok":true,"result":{"sig":"<DER ECDSA over nonce||fw_hash>","fw_hash":"…","boot":"verified","cert_id":"…"}}`.
   The edge verifies against the certificate and the release manifest; `attested` becomes `true` in the
   Pod's next status. Re-attestation happens at every rejoin and every 24 h.
6. **Rotation / revocation.** Device certificates are valid 5 years; the edge warns 90 days before expiry
   and `ben-add-pod.sh --renew` issues a new certificate through the Device CA (CSR generated in the Pod,
   key stays in the chip). Revocation = remove the CN from the broker ACL and the joiner from the
   Commissioner; the Pod's next TLS handshake fails and it falls back to buffering.

Thread network key, PAN ID and channel are **per unit** and recorded sealed in the unit's turnover package.
The mesh is its own IEC 62443 zone (Z1T, `design/specs/CONTROLS_SPEC.md`).

## PLC ↔ edge data path (Modbus TCP, OPC UA optional)

The edge computer polls the PLC at **1 Hz** over Modbus TCP (port 502, unit id 1) on the controls VLAN
and publishes `ben/<unit>/plc/interlocks` and `ben/<unit>/node/plcN/telemetry`. The same tags are exposed
on the PLCnext OPC UA server (`opc.tcp://10.20.0.10:4840`, namespace `BEN`) for customers who prefer it.
The PLC never depends on the edge: it reads transmitters and runs interlocks whether or not the poll
arrives. On **Lite** the poll is local (edge and controller are the same RevPi); the interlock service and the
API are separate systemd units so the interlocks keep running when the API or broker restarts, and the RevPi
hardware watchdog drops the cooling-enable relay if the interlock service itself stops. **The edge writes exactly three registers** (watchdog, setpoint trim, test request); everything
else is read-only.

### Register map (holding registers, 16-bit, big-endian; FC03 read, FC06/16 write where marked W)

| Address | Name | Type | R/W | Meaning |
| --- | --- | --- | --- | --- |
| 40001 | `PLC_HEARTBEAT` | uint16 | R | increments every 100 ms PLC cycle; edge alarms if frozen 3 s |
| 40002 | `PLC_MODE` | enum + flags | R | low byte: 0 off, 1 auto, 2 manual (HMI), 3 test, 4 fault; bit 8 = `LITE` (register map served by the RevPi software controller) |
| 40003 | `PLC_PROJECT_CRC` | uint16 | R | CRC-16 of the loaded project; edge compares with the commissioned value (`attested`) |
| 40004 | `EDGE_WATCHDOG` | uint16 | **W** | edge writes a rising counter every 1 s; PLC sets `EDGE_LOST` when unchanged 30 s |
| 40005 | `EDGE_LOST` | bool | R | 1 = PLC runs on its own setpoints (edge trim ignored, failsafe table "PLC alone") |
| 40006 | `SUPPLY_TRIM_x10` | int16 | **W** | edge-requested supply setpoint trim, −20…+20 (×0.1 K); clamped and ignored when `EDGE_LOST` |
| 40007 | `TEST_REQUEST` | enum | **W** | 0 none, 1 failover sweep, 2 UPS ride-through, 3 generator exercise; PLC accepts only in mode 1 with no active alarm and clears the register |
| 40010 | `COOL_CMD` | bitfield | R | bit n = cooling unit n+1 commanded run (n = 0..7) |
| 40011 | `COOL_RUN` | bitfield | R | bit n = unit n+1 run feedback (aux contact / Modbus RTU status) |
| 40012 | `COOL_FAULT` | bitfield | R | bit n = unit n+1 fault (contact or comms loss) |
| 40013 | `COOL_LEAD` | uint16 | R | index (1..N) of the current lead unit (weekly rotation) |
| 40014 | `COOL_N_REQUIRED` | uint16 | R | units required for current load (from `IT_KW_x10`), N of N+1 |
| 40015 | `COOL_FAILOVER_CNT` | uint16 | R | failovers since power-up (audit) |
| 40016 | `COOL_LAST_FAILOVER_S` | uint16 | R | seconds since last failover (saturates at 65535) |
| 40020 | `LEAK_ZONE` | bitfield | R | bit n = leak zone n+1 wet (SeaHawk zone contacts + Pod `leak` via edge is **not** used for isolation; PLC only acts on hardwired zones) |
| 40021 | `ISO_VALVE_CMD` | bitfield | R | bit n = isolation valve n+1 commanded closed |
| 40022 | `ISO_VALVE_CLOSED` | bitfield | R | bit n = valve n+1 closed limit switch |
| 40023 | `ISO_VALVE_FAULT` | bitfield | R | bit n = valve did not reach limit within 30 s |
| 40024 | `CDU_PUMP_STOP` | bool | R | 1 = PLC has stopped the CDU pumps (leak in a zone whose valve failed) |
| 40030 | `DOOR_STATE` | bitfield | R | bit n = door n+1 open |
| 40031 | `DOOR_OPEN_S` | uint16 | R | seconds the longest-open door has been open |
| 40032 | `EPO_LOOP_OK` | bool | R | 1 = EPO loop closed (**monitor only**: PLC reads the releasing panel/EPO aux contact; cannot act on the loop) |
| 40033 | `FIRE_PANEL` | bitfield | R | bit 0 alarm, bit 1 trouble, bit 2 released, bit 3 supervisory — aux contacts, monitor only |
| 40040 | `ATS_SOURCE` | enum | R | 0 none, 1 utility, 2 generator, 3 in transfer |
| 40041 | `GEN_STATE` | enum | R | 0 off, 1 starting, 2 running, 3 cooldown, 4 fault, 5 not ready |
| 40042 | `GEN_RUN_S` | uint16 | R | seconds in current run |
| 40043 | `UPS_ON_BATTERY` | bool | R | from UPS dry contact (redundant with SNMP) |
| 40044 | `UTILITY_OK` | bool | R | from ATS utility-available contact |
| 40050 | `IT_KW_x10` | uint16 | R | IT load from branch meter pulse/Modbus RTU, ×0.1 kW |
| 40051 | `SUPPLY_C_x10` | int16 | R | cooling supply air/water temperature, ×0.1 °C (lead unit) |
| 40052 | `RETURN_C_x10` | int16 | R | return temperature ×0.1 °C |
| 40053 | `OUTDOOR_C_x10` | int16 | R | outdoor Pt1000 ×0.1 °C |
| 40054 | `AISLE_DP_x10` | int16 | R | Setra 264 ΔP ×0.1 Pa |
| 40055 | `RH_x10` | uint16 | R | Vaisala HMD RH ×0.1 % |
| 40060–40091 | `RTD_01_x100 … RTD_32_x100` | int16 | R | Pt1000 strings on Axioline RTD modules, ×0.01 °C; mapped to `plcN` `T_in_*`/`T_out_*` by `firmware/ben-edge` config |
| 40100–40115 | `AI_01_uA … AI_16_uA` | uint16 | R | 4–20 mA inputs in µA (4000–20000) → `aiN_mA` |
| 40120 | `ALARM_WORD` | bitfield | R | PLC-generated alarms: bit 0 cooling capacity lost, 1 all units faulted, 2 leak isolation active, 3 valve fault, 4 door > 5 min, 5 EPO loop open, 6 fire alarm, 7 generator fault, 8 ATS on generator, 9 edge lost, 10 PSU redundancy lost, 11 24 V UPS on battery |
| 40121 | `PSU_REDUNDANCY_OK` | bool | R | 24 VDC redundancy module OK contact |
| 40122 | `PANEL_TEMP_C_x10` | int16 | R | panel internal temperature |

Bits above 15 are not used; N > 8 cooling units take a second word at +1 (reserved 40017, 40018). Unused
registers read 0. The PLC program publishes the same list as `firmware/ben-plc/modbus_map.csv`; the edge
loads that CSV, so the two cannot drift.

## Safety rules
- A Pod that loses the broker for 60 s keeps measuring and buffering (ring buffer 1 h) and leaves outputs
  in their last state unless the output is configured `failsafe` (then it drops). Pod E relays are
  **not** used for cooling enable any more: cooling enable/failover is a PLC output, so Pod relays are
  for lights, beacons and fan boost only.
- Interlocks (cooling failover, leak isolation, door/EPO monitoring, generator/ATS supervision) live in
  the PLC and run with the edge computer absent. The edge **advises** (setpoint trim, test requests);
  it never commands a valve or a cooling unit directly.
- Life-safety (fire suppression, EPO) is **never** on this bus. It is hardwired; the PLC and Pods only
  monitor dry contacts. **This rule is unchanged from v1.**
