# BEN Controller v1 — specification sheet (UL 508A controls panel)

**Schreiber AI · BEN Engine controls module · IFC Rev B · 2026-11-08** · replaces the BEN Gateway v1 sheet per `docs/CONTROLS_HARDWARE_DECISION.md`.
One per BEN unit. **BEN Controls Pro** (§ A) for BEN 20/40 and optional on BEN 10; **BEN Controls Lite** (§ B) for BEN Micro and standard on BEN 10. Both run the same `ben_engine` software and the same BEN Pods; both are built as a listed industrial control panel. Status: specified, software written (`firmware/ben-edge`, `firmware/ben-plc`), **no panel built yet**.

---

## A. BEN Controls Pro panel — BEN-CTRL-PRO-V1

| | |
| --- | --- |
| **Listing** | **UL 508A** industrial control panel, built and labelled by a UL 508A panel shop (Schreiber AI's contract panel builder); NEMA 12 / IP54 enclosure; cUL for Canada |
| **Function** | Control (PLC + I/O: interlocks, sequencing, transmitters) and data (edge computer: broker, twin, API, border router) halves in one panel, separated by a divider; 24 VDC control power with redundancy; Thread border router RCPs on the panel face |
| **Enclosure** | **Rittal AX 1380 / Hoffman equivalent**, wall-mount steel, **800 W × 1000 H × 300 D mm**, NEMA 12, with 3-point latch, document pocket, gland plate (bottom), **external RCP antennas** via N-type bulkhead (2) on the top (or a polycarbonate window section for internal antennas) |
| **Mounting** | on the mechanical section wall inside the container, door swings toward the aisle; clearances per NEC 110.26 (914 mm front) |
| **Environment** | 0…+50 °C inside the mechanical section (panel heater option for −40 °C sites; filter fan 100 m³/h on the data half); heat load below |

### Bill of panel components (Pro)

| Qty | Item | Make / model (alternate) | Role |
| --- | --- | --- | --- |
| 1 | **PLC** | **Phoenix Contact PLCnext AXC F 2152** (Beckhoff CX9240 · WAGO PFC200 750-8212) | interlocks, sequencing, Modbus RTU master, Modbus TCP / OPC UA server; IEC 62443-4-1 certified development; UL 508 listed |
| 1 | Bus base + end bracket | AXL F BK bus connectors, AXL F … end plate | Axioline F local bus |
| 2–4 | Digital input 16 | **AXL F DI16/1 1F** | cooling run/fault contacts, SeaHawk zones, valve limit switches, doors, EPO/fire aux (monitor), ATS/gen/UPS contacts, PSU redundancy OK |
| 1–2 | Relay output 4 / DO 8 | **AXL F DOR LC/1** (relay, enable chain) + **AXL F DO8/1 1F** | cooling unit remote enables, isolation valves, CDU pump stop, beacon, **enable-chain relay** |
| 2–8 | RTD input 4 | **AXL F RTD4 1H** (Pt1000, 2/3/4-wire) | supply/return/outdoor Pt1000; rack strings on Pro-wired units (up to 32) |
| 1–4 | Analog input 4 (current) | **AXL F AI4 I 1H** | Setra 264 / Dwyer MS2 ΔP, Vaisala HMD/HMW RH, IT kW transducer, CDU pressures (4–20 mA) |
| 1 | Serial | **AXL F RS UNI 1H** | RS-485 Modbus RTU to cooling units / meters / UPS (and Pod E slaves) |
| 1 | **Edge computer** | **OnLogic Karbon 400** (K401 config: Atom x6425E, 16 GB, 256 GB NVMe industrial, TPM 2.0, 2 × GbE, 2 × COM, DIN-rail kit) (Siemens SIMATIC IPC227G) | `ben_engine` API/twin/history, Mosquitto mTLS, OTBR, chrony, PLC bridge, backups; UL 62368-1 |
| 2 | **Border router RCP** | **MGM240P dev module on USB** (Silicon Labs BRD4186C-based RCP or Schreiber AI BEN-RCP-1 USB stick) | OpenThread RCP, one per OTBR; redundant pair on BEN 20/40 (1 on BEN 10) |
| 1 | **Managed Ethernet switch** | **Phoenix Contact FL SWITCH 2008 / 2016 PN** (Moxa EDS-2010-ML / EDS-408A) | VLAN 20 (controls) + VLAN 30 (management) + PoE ports for Pod E where fitted (FL SWITCH 2008 PoE variant or Moxa EDS-P506E); IGMP snooping; port security |
| 1 | **24 VDC PSU, primary** | **Phoenix Contact QUINT4-PS/1AC/24DC/10** (10 A) | control power; UL 508 listed, SEMI F47 |
| 1 | **24 VDC PSU, secondary** | QUINT4-PS/1AC/24DC/10 | fed from the other controls circuit (UPS-backed) |
| 1 | **Redundancy module** | **QUINT4-ORING/12-24DC/2X10/1X20** (diode-less ORing, OK contact) | N+1 24 V with monitoring contact → PLC DI (`PSU_REDUNDANCY_OK`) |
| 1 | 24 V buffer / UPS | **QUINT4-UPS/24DC/24DC/10** + UPS-BAT/VRLA/24DC/3.4AH (or supercap UPS-CAP) | rides through ATS transfer; `UPS_ON_BATTERY` contact |
| 1 | **Surge protection, 120/230 VAC** | **Phoenix Contact PLT-SEC-T3-230-FM** (Type 3 / Class III) at panel entry + fused disconnect | mains feed from the controls circuit |
| 6+ | Surge protection, signal | **TERMITRAB complete** TTC-6P-… for RS-485, 4–20 mA field loops, Pt1000 strings leaving the container; **DT-LAN-CAT.6+** for Ethernet to outdoor | field wiring protection |
| 1 | Ethernet surge for RCP coax | N-type coaxial arrestor (CN-UB-280DC-BB) | antennas on the roof option |
| — | **Terminal blocks** | Phoenix Contact **PT 2,5** push-in (field), PT 2,5-TWIN for 24 V distribution, **PT 2,5-PE** ground, knife-disconnect PT 2,5-MT for every field input, fuse terminals UT 4-HESI for loop power | labelled per `wiring/02` sheet |
| 1 | Marshalling | 4 × PTCB circuit breakers 24 V (electronic, 2 A/4 A) for PLC, edge, switch, field loops | selective 24 V protection |
| 1 | Panel HMI | 7 in PLCnext-compatible HMI (**Phoenix AX WEB PANEL 7** or BTP 2070W) + 3-position selector OFF/AUTO/MANUAL + RESET pushbuttons (latched faults, leak) + beacon (red, steady) | local operation; the edge cannot change mode |
| 1 | Panel accessories | thermostat + 100 m³/h filter fan, panel light, 230 V service receptacle (GFCI), document pocket, panel temperature Pt1000 → PLC (`PANEL_TEMP_C_x10`) | |

### Panel electrical data (Pro)

| Item | Value |
| --- | --- |
| Supply | **120 VAC 20 A** (or 230 VAC 10 A) from the **controls circuit** (UPS-backed, breaker labelled CONTROLS) + second feed from the house circuit for PSU 2 |
| 24 VDC load | PLC + I/O ≈ 1.2 A · edge computer ≈ 1.5 A (36 W) · switch ≈ 0.6 A (+ PoE budget 60 W if Pod E on PoE) · HMI 0.4 A · field loops 0.5 A · relays 0.3 A → **≈ 4.5 A typ, 7 A max**, on 2 × 10 A redundant |
| **Heat load** | **≈ 110 W typical, 180 W max** (PSUs 92 % eff.: 16 W; edge 36 W; PLC + I/O 30 W; switch 15 W; HMI 10 W; PoE losses up to 15 W) — filter fan sized at 100 m³/h for ΔT ≤ 10 K at 50 °C ambient |
| **SCCR** | **UL 508A SB4: 10 kA at 120/240 VAC** (QUINT4 PSUs 10 kA when protected by the specified CB; terminal blocks/CBs rated accordingly). Fed from a 20 A branch breaker in the IT distribution panel: upstream available fault current must be ≤ 10 kA at the panel terminals or a current-limiting fuse (Class CC, 20 A) is added at the feed. The EOR confirms the available fault current at the controls circuit on the stamped set. |
| Control voltage | 24 VDC Class 2 (every field circuit); 120 VAC confined to the PSU/receptacle section behind a finger-safe barrier |
| Wiring | UL 1015 / MTW, 18 AWG field signal, 16 AWG 24 V distribution, 12 AWG mains; ferrules; wire numbers per `wiring/02` |
| Grounding | PE bar bonded to enclosure and container bonding grid; shield bar for field cable shields (landed at the panel end only); functional earth for the PLC |
| Dimensions / mass | 800 × 1000 × 300 mm, ≈ 85 kg loaded |

### Networks on the Pro panel

```
controls VLAN 20 (10.20.0.0/24)   PLC 10.20.0.10 · edge 10.20.0.1 · meters/UPS/cooling/CDU/PDUs · Pod E
Thread mesh fd00:ben::/64         RCP1 (wpan0) + RCP2 (wpan1) on the edge computer USB · Pods
management VLAN 30 (10.30.0.0/24) edge 10.30.0.1 · HMI/dashboard · engineering laptop
customer IT                       NO port on the controls switch is in the customer VLAN; no cable
```

### Pro reliability and failure behaviour

PLCnext AXC F 2152 published MTBF ≈ 700 000 h (vendor); Karbon 400 MTBF ≈ 300 000 h (vendor); QUINT4 PSU > 1 000 000 h. Design assumptions: **PLC alone keeps the interlocks running** without the edge; **the edge alone keeps history and dashboard** without the PLC (telemetry from Pods continues; `plcN` goes stale, dashboard shows "controller comms lost"); **both lost** → enable chain opens, every cooling unit on local control, Pods buffer 1 h. A cold-spare edge image (NVMe clone + LUKS recovery) and a spare PLC with the project on SD ship with every BEN 20/40; restore < 30 min.

---

## B. BEN Controls Lite panel — BEN-CTRL-LITE-V1

For **BEN Micro** (standard) and **BEN 10** (standard; Pro selectable). Same software, same Pods, same acceptance tests; no PLC — the interlocks run on the RevPi behind a hardware watchdog relay (`firmware/ben-edge/lite`, `firmware/ben-plc/README.md`).

| | |
| --- | --- |
| **Listing** | **UL 508A** panel (smaller shop build) or, for BEN Micro, a UL 508A-listed pre-assembled enclosure kit; NEMA 12 / IP54 |
| **Enclosure** | **Rittal AX 1050 / Hoffman equivalent**, **500 W × 500 H × 210 D mm**, wall-mount; antenna bulkhead (1) |
| **Controller + edge** | **KUNBUS Revolution Pi RevPi Connect 4** (8 GB RAM, 32 GB eMMC, 2 × GbE, RTC, hardware watchdog, UL/CE, −25…+55 °C) — alternate RevPi Connect S; runs `ben_engine`, Mosquitto, OTBR (native agent), interlock service |
| **I/O** | **RevPi DIO** (16 DI / 16 DO 24 V, PiBridge) × 1 (× 2 on BEN 10) · **RevPi AIO** (4 AI 4–20 mA, 2 AO, 2 RTD) × 1 |
| **Watchdog relay** | **KW1**: Phoenix Contact PLC-RSC-24DC/21 (DIN relay module) driven by DIO O_14; NO contact in series in the cooling-enable chain; NC contact → beacon |
| **Border router RCP** | 1 × MGM240P RCP on USB |
| **Switch** | **Phoenix Contact FL SWITCH 2005 / Moxa EDS-2005-EL** (5-port, unmanaged VLAN-less → two physical segments: the RevPi's two NICs separate controls and management; PoE injector for a Pod E if fitted) |
| **PSU** | **QUINT4-PS/1AC/24DC/5** (5 A) × 1 + **UPS-CAP** supercap buffer 24 V (ride-through 30 s); redundancy module optional |
| **Surge** | PLT-SEC-T3-230-FM at mains entry; TERMITRAB on field loops leaving the cabinet |
| **Terminal blocks** | PT 2,5 push-in with knife disconnects on field inputs; PE and shield bars |
| **HMI** | OFF/AUTO/MANUAL selector, RESET button, beacon; dashboard on the customer's screen via VLAN 30 (no panel HMI) |
| **24 VDC load / heat** | ≈ 1.8 A typ, 3 A max; **≈ 45 W typical, 70 W max** heat; passive ventilation, louvres with filters |
| **SCCR** | **5 kA at 120/240 VAC** (UL 508A SB4, 15 A branch, Class CC fuse at feed if upstream exceeds) |
| **Dimensions / mass** | 500 × 500 × 210 mm, ≈ 25 kg |
| **Failure behaviour** | interlock service stalls → systemd restart (10 s) → hardware watchdog reboot (60 s) → outputs zero → KW1 opens → units on local control; RevPi dead → same; edge functions and interlocks share the box, so a dead RevPi also stops history until the cold spare (eMMC image) is swapped (< 20 min) |

---

## Common: what the Controller does NOT do (both tiers)

- It never routes between the controls, Thread, management and customer networks (host firewall default-drop, no forwarding).
- It never commands fire suppression, EPO or door release; it reads the releasing panel's and EPO loop's aux contacts only (`wiring/05`).
- The edge software never writes an output: three advisory registers (watchdog, trim, test request) are the whole edge→controller write path.
- It never depends on the internet; remote support is an outbound-only, customer-switched VPN.
