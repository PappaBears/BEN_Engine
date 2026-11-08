# Controls hardware decision — industrial platform, BEN Mesh, and BEN Care

**Status:** decided 2026-11-08 by the lead after the operator rejected the hobby-grade gateway. Supersedes D5 in `docs/PROJECT_NOTES.md`. Every document, BOM line, drawing, spec sheet, firmware target and contract clause that said "Raspberry Pi", "Olimex" or "ESP32" is changed to this.

## 1. The mistake and the correction

The first pass used a Raspberry Pi 5 gateway and ESP32 hobby boards as sensor nodes. They are cheap and they work on a bench. They are not what a plant director, an insurer, a UL 508A panel shop or an AHJ expects inside a container that carries 500 kW. BEN Engine is a true industrial solution, so the controls are built the way a data center BMS and an industrial control panel are built, and the part we make ourselves is the part that nobody else offers: a secure sensing mesh with a hardware root of trust, and the digital care layer on top of it.

## 2. Architecture (three layers)

| Layer | What it does | Hardware | Standards |
| --- | --- | --- | --- |
| **Control** (deterministic, interlocks, sequencing) | Cooling unit start/stop and failover, leak isolation valves, door and EPO monitoring, generator/ATS supervision, mechanical panel I/O | **PLC: Phoenix Contact PLCnext AXC F 2152** (alternates: Beckhoff CX9240, WAGO PFC200) with **Axioline F remote I/O** in a UL 508A listed panel | IEC 61131-3, IEC 62443-4-1 (PLCnext development process certified), UL 508 listed controller, UL 508A panel |
| **Data and digital twin** (history, twin, dashboard, proposal, analytics) | Runs `ben_engine` (API, twin, sweeps, commissioning, export), MQTT broker, time series store, border router for the mesh | **Industrial edge computer: OnLogic Karbon 400 series** (Intel Atom x6425E, −40…70 °C, TPM 2.0, DIN rail, dual LAN, UL 62368-1, optional Class I Div 2); alternate **Siemens SIMATIC IPC227G** | UL 62368-1, IEC 62443-3-3 zone host, TPM 2.0 measured boot, full-disk encryption |
| **Sensing** (dense, placement-flexible, secure) | Rack inlet/outlet temperature at three heights, humidity, differential pressure, leak, door, vibration, outdoor equipment, Micro cabinets, fleet | **Wired:** industrial transmitters on the PLC I/O (Pt1000 RTD strings, Setra 264 / Dwyer MS2 ΔP transmitters, Vaisala HMD humidity, RLE SeaHawk leak controller). **Wireless: BEN Pod** on the **BEN Mesh** (our own design, below) | UL 61010-1 for transmitters, FCC Part 15 modular approval for the Pod radio |

Life safety (smoke detection, clean-agent release, EPO) stays hardwired and is only *monitored* by the PLC through dry contacts. That rule does not change.

## 3. BEN Mesh and BEN Pod (what we build ourselves)

**Why a mesh at all.** Wiring 6 probes per rack × 12 racks plus outdoor equipment is 80+ runs of shielded cable, terminations and labels; it is the most error-prone, least repeatable part of a controls install, and it is the part that cannot move when the container moves. A secure, self-healing, IP-native mesh removes it, and it is the same hardware for the Micro cabinet, the dry cooler on the roof, the generator on the pad and the fleet.

**Radio and silicon: Thread (IEEE 802.15.4, 2.4 GHz) on Silicon Labs EFR32MG24, as the pre-certified MGM240P module.**
- Thread is IPv6 end to end (6LoWPAN), so the BEN protocol (`spec/PROTOCOL.md`: MQTT/JSON, mutual TLS) runs unchanged from Pod to broker. No proprietary gateway translation, no cloud.
- Self-healing mesh, router-eligible nodes, 250 kbit/s, sleepy end devices for battery pods (years on a cell), deterministic join with DTLS and per-device credentials.
- EFR32MG24 has **Secure Vault High** (PSA Certified Level 3): hardware root of trust, secure boot with anti-rollback, secure key storage, tamper detection, true RNG, secure debug. Industrial temperature silicon, published 10-year longevity.
- The MGM240P module carries FCC/IC/CE modular radio approval, so the Pod needs FCC Part 15 unintentional-radiator testing only, not full intentional-radiator certification.
- Alternatives considered: Wi-SUN FAN (sub-GHz, utility-grade, longer range, heavier stack and modules, overkill inside a container; kept as the option for large campuses), LoRaWAN (not a mesh, too slow for 1 Hz telemetry), Zigbee (not IP), Wi-Fi mesh (power and interference), wired-only (rejected for the reasons above; a wired ring remains for the PLC I/O).

**BEN Pod v1 (our PCB, built by the contract electronics manufacturer):**
- MGM240P module; 24 VDC or PoE-powered variant (**Pod E**: LAN8742 Ethernet PHY + 802.3af PD, RS-485 Modbus RTU to the PLC as the wired path, Thread as backup) and battery/24 VDC variant (**Pod W**: Thread only, 2 × AA LiFeS2 or 24 VDC).
- Inputs: 4 × Pt1000 RTD (3-wire, 24-bit ADC), SHT45 temperature/humidity, SDP810 differential pressure, 2 × dry contact, 1 × leak-rope input, 2 × 4–20 mA (165 Ω, isolated), 2 × relay (10 A) on Pod E only.
- Secure provisioning in our factory cell: per-device X.509 certificate from Schreiber AI's PKI written into Secure Vault; firmware signed with ECDSA P-256; attestation at network join; keys never leave the chip.
- DIN-rail and rack-rail enclosure, IP40 indoor / IP65 outdoor variant, −40…70 °C.
- Firmware: the existing `bencore` library (calibration, telemetry JSON, commands, ring buffer, failsafe, alarms) is unchanged; the HAL targets Silicon Labs Gecko SDK / OpenThread instead of ESP-IDF. Native host tests remain the acceptance for the core.

**Border router.** OpenThread Border Router on the edge computer with an MGM240P radio co-processor (RCP) on USB/UART; two RCPs for redundancy on BEN 20/40.

## 4. BEN Care — the digital care layer, and what nobody else does

Most data center monitoring tells you a temperature. BEN Care tells you how long you have, how sure we are, and proves the box still works every month.

1. **A physics twin per unit, fitted from the unit's own commissioning data and re-fitted continuously.** Every alarm carries minutes-to-limit and a confidence interval, not a threshold crossing. (`analysis.py`)
2. **Proof of redundancy every month.** Automated failover and ride-through sweeps run at low load, are logged with a signed hash, and feed the warranty and the SLA. Almost no small facility ever tests failover; BEN units prove it on a schedule. (`sweeps.py`, `commissioning.py`)
3. **Drift-triggered calibration instead of calendar calibration.** Pods are cross-checked against each other and the twin; calibration is requested when uncertainty grows, with a GUM budget attached. (`calibration.py`)
4. **Live risk scorecard.** The risk register the customer saw before the price becomes a per-unit live scorecard: each risk shows the evidence that it is covered right now.
5. **Fleet learning.** Fitted parameters and failure precursors from every unit improve the priors for the next one (Atlas interface in `docs/SYSTEM_INTEGRATION.md`); the customer's data never leaves their unit unless they opt in.
6. **Hardware root of trust end to end.** Every Pod attests; every firmware image is signed; the edge computer measures its boot with a TPM; the controls zone has no route to the internet. Local-first, no cloud dependency, customer owns the data, white-label without losing the safety identity.
7. **One script from factory to field to lifetime.** The same commissioning script is the FAT, the SAT, the monthly check and the warranty baseline.

## 5. What changes in the repository

| Area | Change |
| --- | --- |
| `spec/PROTOCOL.md` | Gateway = edge computer + PLC; nodes = BEN Pod (Thread/IPv6) and PLC I/O; wired transmitters normalised by the PLC |
| `design/specs/` | `BEN-CONTROLLER-v1.md` (PLC + edge computer panel), `BEN-POD-v1.md` (replaces node spec), wiring one-lines regenerated |
| `firmware/` | `ben-node` → `ben-pod`: HAL target Gecko SDK/OpenThread (`hal_efr32`), `platformio.ini` env for the MGM240P, core and host tests unchanged; `ben-gateway` → `ben-edge`: install for the industrial edge computer (Debian/Ubuntu LTS or Yocto, TPM-backed disk encryption, OTBR), PLC project skeleton (PLCnext) with the interlock logic described |
| `purchasing/parts_catalog.json` | Remove Pi, Olimex, hobby relay boards; add PLC, Axioline I/O, edge computer, industrial transmitters, MGM240P, secure provisioning fixture; Pod PCB cost per unit; update emails |
| `design/` | Layout, assembly (STE), drawings, SQAM: controls panel is a UL 508A panel; Pods on rack rails; wiring tasks change |
| `docs/` | Architecture, compliance (UL 508A row now ours, FCC modular approval), cybersecurity (Secure Vault, TPM, attestation), maintenance, build & wiring, FAQ, README, VC, decks, contracts (supplier quality rows) |
| Dashboard | Labels: "BEN Pod", "controller", mesh health panel item (link quality, parent, attestation state) |
