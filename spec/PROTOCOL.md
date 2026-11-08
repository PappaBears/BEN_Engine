# BEN Controls protocol (v1)

Every BEN unit has one **gateway** (Raspberry Pi 5, runs `ben_engine` server) and N **nodes**
(ESP32-S3 sensor/IO nodes, Olimex ESP32-POE-ISO carrier). Third-party equipment (UPS, cooling
units, power meters, rack PDUs) is polled by the gateway over Modbus TCP/RTU or SNMP and
normalised onto the same topics. Transport between nodes and gateway is **MQTT over the
unit's isolated controls LAN** (no internet dependency). Payloads are JSON. Every message
carries `ts` (unix seconds, gateway-synced via SNTP) and `seq`.

## Topics

| Topic | Direction | Rate | Payload |
| --- | --- | --- | --- |
| `ben/<unit>/node/<node_id>/telemetry` | node → gw | 1 Hz (configurable 0.2–10 Hz) | `{"ts":…, "seq":…, "ch":{"T_in_1":21.4,"T_in_2":21.9,"T_out_1":33.0,"RH":41.2,"dP_aisle":12.3,"leak":0,"door":0,"ai0_mA":12.01}, "raw":{…ADC counts…}, "cal_id":"c-2026-11-07-01"}` |
| `ben/<unit>/node/<node_id>/status` | node → gw | 10 s + on change | `{"fw":"1.0.0","uptime_s":…,"rssi":…,"ip":…,"heap":…,"errors":[]}` (retained) |
| `ben/<unit>/node/<node_id>/cmd` | gw → node | on demand | `{"id":"uuid","op":"set_output","out":"relay1","value":1}` / `{"op":"get_cal"}` / `{"op":"set_cal","ch":"T_in_1","gain":1.002,"offset":-0.13,"cal_id":"…"}` / `{"op":"tare","ch":"dP_aisle"}` / `{"op":"identify"}` / `{"op":"reboot"}` / `{"op":"ota","url":"…","sha256":"…"}` |
| `ben/<unit>/node/<node_id>/ack` | node → gw | reply | `{"id":"uuid","ok":true,"result":{…}}` |
| `ben/<unit>/equip/<equip_id>/telemetry` | gw internal | 1–10 s | normalised third-party values: `{"kw":…, "kva":…, "v_ab":…, "i_a":…, "supply_c":…, "return_c":…, "fan_pct":…, "soc_pct":…, "runtime_min":…, "alarm":[]}` |
| `ben/<unit>/alarm` | gw → all | on change | `{"id":…, "sev":"warn|alarm|critical", "src":"node3/T_in_1", "msg":"Rack 3 inlet 27.8 C > 27 C (ASHRAE A1 max)", "active":true}` |
| `ben/<unit>/twin/state` | gw → dashboard | 1 Hz | full twin state (see INTERFACES.md) |

## Node channel map (BEN Node v1)

| Channel | Sensor | Interface | Range | Node uncertainty (k=2) after calibration |
| --- | --- | --- | --- | --- |
| `T_in_1..4`, `T_out_1..4` | DS18B20 (rack inlet/outlet strings) | 1-Wire | −10…85 °C | ±0.25 °C |
| `T_ref` | SHT45 | I²C | −40…125 °C | ±0.15 °C |
| `RH` | SHT45 | I²C | 0…100 %RH | ±1.5 %RH |
| `dP_aisle` | SDP810-125Pa | I²C | ±125 Pa | ±0.4 Pa after tare |
| `leak` | Conductive rope sensor | GPIO + divider | 0/1 | — |
| `door` | Magnetic reed | GPIO | 0/1 | — |
| `ai0..3_mA` | ADS1115 + 165 Ω shunt | I²C | 4–20 mA | ±0.02 mA |
| `relay1..4` | 10 A relay (cooling enable, lights, fan boost, spare) | GPIO | out | — |
| `pulse_kwh` | Meter S0 pulse | GPIO IRQ | counter | — |

Calibration coefficients (`gain`, `offset`) are applied in the node and stored in NVS with a
`cal_id`; the node always also reports `raw` so the gateway can re-process.

## Safety rules
- A node that loses the gateway for 60 s keeps measuring and buffering (ring buffer 1 h) and leaves outputs in their last state unless the output is configured `failsafe` (then it drops).
- Life-safety (fire suppression, EPO) is **never** on this bus. It is hardwired; the node only monitors dry contacts.
