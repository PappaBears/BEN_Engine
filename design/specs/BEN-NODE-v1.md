# BEN Node v1 — specification sheet

**Schreiber AI · BEN Engine controls module · IFC Rev A · 2026-11-07**
Sensor / I/O node for every BEN tier. One node per 1–2 racks plus one per mechanical panel; the gateway polls third-party equipment itself.
Status: design complete, firmware core unit-tested on host, **no node built yet** (see firmware/README.md).

| | |
| --- | --- |
| **Part number** | BEN-NODE-V1 (carrier: Olimex ESP32-POE-ISO + Schreiber AI I/O board BEN-IOB-1) |
| **Processor** | ESP32-WROOM-32 (Xtensa LX6 dual-core 240 MHz, 520 kB SRAM, 4 MB flash) on the Olimex carrier; v1.1 custom carrier moves to ESP32-S3 + 8 MB PSRAM |
| **Firmware** | `firmware/ben-node` 1.0.0, PlatformIO/Arduino, MQTT v3.1.1 over IPv4, SNTP; Secure Boot v2 + flash encryption procedure documented |
| **Network** | 10/100BASE-TX, LAN8720 PHY, RJ45 with magnetics, **galvanically isolated** PoE section (Olimex ISO variant, 3 kV) |

## Electrical

| Item | Value | Note |
| --- | --- | --- |
| Power, primary | **PoE IEEE 802.3af class 0** (≤ 12.95 W at PD), 37–57 V on the data pairs or spare pairs | isolated DC-DC on carrier |
| Power, alternate | **12–24 VDC** (10–28 VDC absolute) on pluggable terminal block, reverse-polarity protected, 1 A fuse | for cabinets without a PoE switch (BEN Micro) |
| Consumption | 2.1 W typical, 4.8 W max (all 4 relays energised, Ethernet active) | **calculated from datasheets, not measured** |
| Relay outputs | 4 × SPDT, 10 A @ 250 VAC / 10 A @ 30 VDC contact rating, coil 5 V driven by ULN2003; used ≤ 5 A pilot duty | relay1 = cooling enable (failsafe), relay2 lights, relay3 fan boost, relay4 spare |
| Relay protection | flyback diode on coil (in ULN2003); **RC snubber 100 Ω / 0.1 µF X2 across AC loads; MOV 275 VAC for inductive loads** | fitted on BEN-IOB-1 |
| Analog inputs | 4 × 4–20 mA, ADS1115 16-bit, 165 Ω 0.1 % 25 ppm shunt (0.66–3.30 V), loop-powered from node 24 V or externally powered | input impedance 165 Ω; over-range to 24 mA safe |
| 1-Wire | 1 bus, up to 8 DS18B20, 4.7 kΩ pull-up, max string 20 m with CAT5 | parasitic power not used |
| I²C | 1 bus, 100 kHz, 3.3 V: SHT45 (0x44), SDP810-125Pa (0x25), ADS1115 (0x48) | bus length ≤ 0.5 m; sensors on the I/O board or short pigtails |
| Digital inputs | leak rope (3.3 V excitation, divider), door reed (dry contact), S0 meter pulse (opto, 5–27 V), EPO/fire aux contact (dry, **monitor only**) | all input-only ESP32 pins; 100 Hz max pulse |
| Isolation | Ethernet/PoE 3 kV; S0 pulse 2.5 kV opto; relays 4 kV coil-contact; analog/1-Wire/I²C **not** isolated (same 0 V as node) | |
| Surge | PoE: integrated on carrier; terminal inputs: TVS 5.0SMDJ bidirectional on each analog/DI line | class 2 wiring only |

## Sensor channels (from spec/PROTOCOL.md)

| Channel | Sensor | Interface | Range | Node uncertainty (k=2) after calibration |
| --- | --- | --- | --- | --- |
| `T_in_1..4`, `T_out_1..4` | DS18B20 rack inlet/outlet strings | 1-Wire | −10…85 °C | ±0.25 °C |
| `T_ref` | SHT45 | I²C | −40…125 °C | ±0.15 °C |
| `RH` | SHT45 | I²C | 0…100 %RH | ±1.5 %RH |
| `dP_aisle` | SDP810-125Pa | I²C | ±125 Pa | ±0.4 Pa after tare |
| `leak` | conductive rope | GPIO + divider | 0/1 | — |
| `door` | magnetic reed | GPIO | 0/1 | — |
| `ai0..3_mA` | ADS1115 + 165 Ω shunt | I²C | 4–20 mA | ±0.02 mA |
| `relay1..4` | 10 A relay | GPIO | out | — |
| `pulse_kwh` | meter S0 pulse | GPIO IRQ | counter | — |

Telemetry at 1 Hz (0.2–10 Hz configurable); status every 10 s (retained); 1 h local buffer when the gateway is lost; calibration (gain, offset, cal_id) stored in NVS and applied in the node, raw counts always reported.

## I/O counts and connectors

| Connector | Type | Pins | Carries |
| --- | --- | --- | --- |
| X1 | RJ45 shielded | 8 | Ethernet + PoE in |
| X2 | pluggable terminal block 5.08 mm, 2-pos | 2 | 12–24 VDC alt. power |
| X3 | pluggable terminal block 3.5 mm, 3-pos | 3 | 1-Wire (3V3, DATA, 0V) — DS18B20 string |
| X4 | pluggable terminal block 3.5 mm, 4-pos | 4 | SDP810 remote header / spare I²C (3V3, SDA, SCL, 0V) |
| X5 | pluggable terminal block 3.5 mm, 8-pos | 8 | AI0..AI3 (+, −) 4–20 mA |
| X6 | pluggable terminal block 3.5 mm, 8-pos | 8 | leak (EXC, SENSE), door (C, NO), pulse (+, −), EPO monitor (C, NO) |
| X7 | pluggable terminal block 5.08 mm, 12-pos | 12 | relay1..4 (COM, NO, NC each) |
| P1, P2 | barbed 3/16 in | 2 | SDP810 + / − pressure tubing to aisle taps |
| USB-C | | | serial console for provisioning (115200 8N1) and flashing |

LEDs (front): **PWR** green steady; **LINK** amber (Ethernet activity); **IDENT** blue — solid = identify command active, **1 Hz blink = gateway lost (failsafe active)**, 50 ms blip every 2 s = normal; **RLY1..4** red when the relay is energised.

## Environmental and mechanical

| Item | Value |
| --- | --- |
| Operating temperature | −20…+60 °C (ESP32 and relays −40…+85 °C; SDP810 −40…+85 °C; limited by electrolytic capacitors) |
| Humidity | 5–95 %RH non-condensing |
| Ingress | IP20 (inside the container / cabinet mechanical panel); IP55 option = in its own DIN enclosure |
| Enclosure | **DIN-rail (EN 60715 TH35), polycarbonate, 6 modules, 106 × 90 × 58 mm (W × H × D)**, UL 94 V-0 |
| Mass | ≈ 240 g with relays |
| Vibration | transport per ISTA 3A in the container; no fan, no moving parts |
| Compliance targets | EN 61326-1 (EMC, industrial), EN 62368-1 (safety, PoE PD), FCC Part 15 B (Class A); RoHS; relay circuits ≤ 250 VAC Class 1 wiring in a separate conduit |

## Reliability

**MTBF method:** parts-count prediction per **Telcordia SR-332 Issue 4**, ground benign, 40 °C, with manufacturer FIT for the ESP32 module (Espressif reliability report), relays at 10 % of rated contact load, electrolytics derated 50 %. Predicted **MTBF ≈ 310 000 h (35 years) for the electronics, dominated by the relays and the 24 V DC-DC**; the DS18B20 strings and the leak rope are field-replaceable consumables (expected 7–10 years). This is a prediction, not a demonstrated value; the commissioning burn-in (72 h at 40 °C) is the first evidence. Mission-critical actions do not depend on a node: a lost node only removes visibility, the cooling unit's own controller keeps running (relay1 failsafe releases "enable" to local control).

## What the node does NOT do (by design)

- It never controls fire suppression, EPO, or door interlocks; it only monitors their aux contacts.
- It never routes or bridges networks; one Ethernet port, one VLAN.
- It never accepts a firmware image without a matching SHA-256 and (when eFuses are burnt) a valid signature.
