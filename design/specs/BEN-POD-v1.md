# BEN Pod v1 — specification sheet

**Schreiber AI · BEN Engine sensing module · IFC Rev B · 2026-11-08** · replaces the BEN Node v1 sheet (hobby carrier) per `docs/CONTROLS_HARDWARE_DECISION.md`.
Wireless/wired sensing node on the **BEN Mesh** (Thread, IEEE 802.15.4, 2.4 GHz) for every BEN tier and both controls tiers (Lite and Pro). Two per rack plus two per unit (mechanical panel, outdoor equipment); three on a BEN 5. Status: design complete, firmware core unit-tested on host (37/37), EFR32 build and PCB **not built yet** (`firmware/README.md`).

| | |
| --- | --- |
| **Part numbers** | **BEN-POD-E-V1** (wired/PoE/RS-485 variant) · **BEN-POD-W-V1** (wireless variant) · **BEN-POD-W-V1-X** (IP65 outdoor) |
| **Module** | **Silicon Labs MGM240PB32VNA** (EFR32MG24, Arm Cortex-M33 78 MHz, 1.5 MB flash, 256 kB RAM, +10 dBm / +20 dBm variant for outdoor, integrated antenna; U.FL variant for the IP65 enclosure) |
| **Security silicon** | **Secure Vault High — PSA Certified Level 3**: hardware root of trust, secure boot with anti-rollback, secure key storage (key wrapping, PUF), tamper detection, TRNG, secure debug lock, DPA countermeasures |
| **Firmware** | `firmware/ben-pod` 1.0.0: Simplicity SDK + OpenThread, MQTT 3.1.1 over TLS 1.2 (mutual X.509, PSA opaque key), SNTP over Thread, NVM3, Gecko Bootloader signed OTA; core = `lib/bencore` |
| **Radio** | Thread 1.3 (OpenThread), IEEE 802.15.4 2.4 GHz, 250 kbit/s, 16 channels; Pod E and 24 V Pod W = Full Thread Device / router-eligible; battery Pod W = Sleepy End Device (1 s poll) |
| **Radio approval** | MGM240P **modular approval**: FCC ID, IC and CE/RED **per module datasheet** (Silicon Labs MGM240P data sheet, "Certifications" section); the Pod inherits it and needs only FCC Part 15 B unintentional-radiator testing (Class A) plus the module's integration conditions (antenna keep-out, label "Contains FCC ID …" / "Contains IC …") |
| **Protocol** | `spec/PROTOCOL.md` v1.1: node topics unchanged; status adds `cert_id`, `attested`, `parent`, `lqi`, `rssi`, `path`; `attest` challenge at join and every 24 h |

## Variants

| | **Pod E** (wired) | **Pod W** (wireless) |
| --- | --- | --- |
| Where | mechanical panel, CDU, PDU zone, anywhere with a switch port or 24 V | rack rails (2 per rack), door frames, outdoor equipment, BEN 5 cabinet |
| Power | **PoE IEEE 802.3af class 0** (Si3402 PD, isolated) **or** 24 VDC (18–30 V) terminal, 1 A fuse, reverse-protected | **2 × AA LiFeS2 (Energizer L91)** 3.0 V **or** 24 VDC terminal (then router-eligible) |
| Consumption | 1.1 W typ / 3.6 W max (relays + Ethernet) — **calculated, not measured** | battery: 1 Hz sample, 1 s poll, telemetry 1 Hz → ≈ 2.9 mA avg → **≈ 1.4 y**; at 0.2 Hz telemetry **≈ 4 y** (calculated at 20 °C; derate 30 % at −20 °C) |
| Network paths | Thread (primary) · **Ethernet 10/100 (W5500 SPI MAC+PHY)** as backup for telemetry · **RS-485 Modbus RTU slave** to the PLC/RevPi for interlock use | Thread only |
| Inputs | 4 × Pt1000 3-wire · SHT45 T/RH · SDP810 ΔP · 2 × dry contact · 1 × leak rope · 2 × 4–20 mA isolated (165 Ω) · S0 pulse | 4 × Pt1000 3-wire · SHT45 · SDP810 · 2 × dry contact · 1 × leak rope (4–20 mA inputs **not** fitted on battery build) |
| Outputs | **2 × relay 10 A** SPDT (relay1 failsafe) | none |
| Enclosure | DIN-rail polycarbonate 6 M, 106 × 90 × 58 mm, IP40 | rack-rail clip-on 95 × 60 × 28 mm IP40 **or** IP65 ABS 115 × 90 × 55 mm with U.FL external antenna (outdoor variant) |
| Mass | ≈ 230 g | ≈ 110 g (rail) / 260 g (IP65) |

## Electrical

| Item | Value | Note |
| --- | --- | --- |
| RTD inputs | 4 × Pt1000 class A, **3-wire**, ADS124S08 24-bit Σ-Δ, IDAC 500 µA, 1.65 kΩ 0.05 % 10 ppm reference, ratiometric; lead resistance compensated to 20 Ω | −50…150 °C span; open/short detection |
| I²C sensors | SHT45 (0x44, ±0.1 °C / ±1 %RH), SDP810-125Pa (0x25, ±125 Pa, 60 LSB/Pa) | on the PCB; SDP810 ports to barbed 3/16 in fittings |
| 4–20 mA (Pod E) | 2 × isolated (ADuM / ISO224 front end), 165 Ω 0.1 % 25 ppm shunt, 24 V loop supply from X2 | ±0.02 mA after calibration |
| Digital inputs | 2 × dry contact (3.3 V wetting, 10 kΩ, debounced 20 ms), leak rope (resistive 2-wire, comparator at 50 kΩ threshold), S0 pulse (opto, 5–27 V, 100 Hz max) | input 2 doubles as EPO/fire **monitor** |
| Relays (Pod E) | 2 × SPDT 10 A @ 250 VAC / 30 VDC, used ≤ 5 A pilot duty; ULN2003 drivers; RC snubber 100 Ω / 0.1 µF X2 + MOV 275 V on AC loads | relay1 failsafe (drops 60 s after broker loss) |
| Isolation | Ethernet/PoE 1.5 kV (magnetics) + PD isolated DC-DC; RS-485 2.5 kV; relays 4 kV coil-contact; 4–20 mA 1 kV channel-to-ground; RTD/I²C/DI not isolated | |
| Surge | TVS 5.0SMDJ bidirectional on every terminal line; PoE integrated | Class 2 wiring only |
| Clock | 38.4 MHz radio crystal + 32.768 kHz LFXO ±20 ppm (sleepy timing) | |
| Debug | SWD on 10-pin Cortex header **locked** after provisioning (Secure Vault secure debug: unlock only with a device-specific HSM-signed challenge) | |

## Sensor channels (from spec/PROTOCOL.md)

| Channel | Sensor | Interface | Range | Pod uncertainty (k=2) after calibration |
| --- | --- | --- | --- | --- |
| `T_in_1..2`, `T_out_1..2` (4 per Pod) | Pt1000 class A probes, 2 m PTFE leads, 3-wire | RTD ADC | −50…150 °C | **±0.15 °C** |
| `T_ref` | SHT45 | I²C | −40…125 °C | ±0.15 °C |
| `RH` | SHT45 | I²C | 0…100 %RH | ±1.5 %RH |
| `dP_aisle` | SDP810-125Pa | I²C | ±125 Pa | ±0.4 Pa after tare |
| `leak` | leak rope | comparator | 0/1 | — |
| `door` | dry contact | DI | 0/1 | — |
| `ai0..1_mA` (Pod E) | isolated 165 Ω | ADC | 4–20 mA | ±0.02 mA |
| `relay1..2` (Pod E) | 10 A relay | out | — | — |
| `pulse_kwh` | S0 pulse | DI IRQ | counter | — |

Telemetry at 1 Hz (0.2–10 Hz configurable); status every 10 s (retained) with mesh health (`parent`, `lqi`, `rssi`) and identity (`cert_id`, `attested`); 1 h local buffer when the broker is lost; calibration (gain, offset, cal_id) in NVM3 and applied in the Pod, raw counts always reported.

## Connectors

| Connector | Type | Pins | Carries |
| --- | --- | --- | --- |
| X1 (Pod E) | RJ45 shielded, magnetics, PoE | 8 | Ethernet + PoE in |
| X2 | pluggable 5.08 mm, 2-pos | 2 | 24 VDC alt. power (Pod E) / 24 VDC option (Pod W) |
| X3 | pluggable 3.5 mm, 12-pos | 12 | RTD1..4 (3 wires each) |
| X4 | pluggable 3.5 mm, 6-pos | 6 | DI1 (C, NO), DI2/EPO-mon (C, NO), LEAK (A, B) |
| X5 (Pod E) | pluggable 3.5 mm, 4-pos | 4 | AI0 (+,−), AI1 (+,−) 4–20 mA |
| X6 (Pod E) | pluggable 5.08 mm, 6-pos | 6 | relay1, relay2 (COM, NO, NC) |
| X7 (Pod E) | pluggable 3.5 mm, 3-pos | 3 | RS-485 A, B, shield/common (120 Ω jumper) |
| X8 | pluggable 3.5 mm, 2-pos | 2 | S0 pulse (+, −) |
| P1, P2 | barbed 3/16 in | 2 | SDP810 + / − tubing |
| J1 | 10-pin Cortex SWD (locked) | 10 | factory provisioning only |
| BT1 (Pod W) | 2 × AA holder | — | LiFeS2 cells |

**LEDs (front):** **PWR** green (Pod E only; Pod W blips on battery check); **IDENT** blue — solid = identify, **1 Hz blink = broker lost (failsafe active)**, 50 ms blip every 2 s = normal; **LINK** amber — on = Thread attached and MQTT connected, blink = joining; **RLY1/2** red (Pod E).

## Environmental and mechanical

| Item | Value |
| --- | --- |
| Operating temperature | **−40…+70 °C** (MGM240P −40…+105 °C; SHT45/SDP810 −40…+85 °C; relays −40…+85 °C; LiFeS2 cells −40…+60 °C; all capacitors polymer/ceramic — no electrolytics) |
| Humidity | 5–95 %RH non-condensing (IP65 variant: condensing allowed, conformal coating) |
| Ingress | IP40 indoor; **IP65** outdoor variant (dry cooler, generator pad, BEN 5 outdoors) |
| Vibration | ISTA 3A transport in the container; no moving parts |
| Enclosures | DIN EN 60715 TH35 (Pod E), rack-rail clip (Pod W), wall/pole IP65 (Pod W-X); UL 94 V-0 |
| Compliance targets | FCC Part 15 B Class A (unintentional) with MGM240P modular approval (intentional); ISED ICES-003; EN 61326-1 (EMC industrial); UL 61010-1 / EN 61010-1 (measurement equipment safety); UL 62368-1 for the PoE PD section; RoHS/REACH; relay circuits ≤ 250 VAC Class 1 wiring in separate conduit |
| Cybersecurity | PSA Certified Level 3 silicon; per-device X.509 from the Schreiber AI PKI in Secure Vault; signed firmware (ECDSA P-256, anti-rollback); DTLS join; mTLS MQTT; attestation; IEC 62443-4-2 component requirements mapped in `CONTROLS_SPEC.md` |

## Reliability

**MTBF method:** parts-count prediction per **Telcordia SR-332 Issue 4**, ground benign, 40 °C, with the MGM240P FIT from the Silicon Labs reliability report (industrial grade, 10-year longevity program), relays at 10 % of rated contact load, no electrolytic capacitors. Predicted **MTBF ≈ 520 000 h (59 y) for Pod W, ≈ 340 000 h (39 y) for Pod E** (relays and PoE DC-DC dominate). Pt1000 probes and leak rope are field-replaceable; LiFeS2 cells are a maintenance item (replace at the `battery_pct` < 20 % alarm, ≈ every 1.5–4 y). These are predictions, not demonstrated values; the 72 h / 40 °C commissioning burn-in is the first evidence. A lost Pod only removes visibility: interlocks live in the PLC/RevPi, and cooling units keep their own controllers.

## What the Pod does NOT do (by design)

- It never controls fire suppression, EPO or door interlocks; it only monitors their aux contacts.
- It never routes IP between networks: Thread end device/router inside one mesh; Pod E Ethernet is a second path for its *own* telemetry only.
- It never accepts firmware without a matching SHA-256 **and** a valid ECDSA signature with a non-decreasing version.
- It never holds a key that can leave the chip; it never joins a mesh without the Commissioner's PSKd entry for its EUI-64.
- Its relays are not in the cooling-enable chain (that is the controller's hardware chain).
