# BEN Engine — Build and Wiring Guide

**Owner:** Schreiber AI engineering. **Companion to:** the Simplified Technical English assembly instructions in `design/assembly/` (step-by-step) and the IFC drawings in `design/drawings/`. This guide gives the *rules and numbers* those steps rely on, so an electrician, a controls tech or an inspector can check any step against a reason.

Everything electrical is done by a licensed electrician to the AHJ's adopted NEC edition. Everything here that says "NEC" refers to NFPA 70-2026 unless the AHJ has adopted an earlier edition (2020/2023 are common; the tables below do not change between them).

## 1. Sizing basis

All loads come from `software/ben_engine/config.py` → `Config.derived()`:

- `total_kva` = (IT kW + cooling electrical kW + 0.5 kW + 2 % of IT) / 0.95 pf.
- `service_amps_calc` = total_kva / (√3 × V_LL) / 0.8 (the 0.8 applies the 125 % continuous-load rule of NEC 210.19/215.2 to the whole load, conservatively).
- `service_breaker_a` = next standard frame ≥ `service_amps_calc` (NEC 240.6 standard ratings).
- UPS feeder = `ups_kva_each` / (√3 × V_LL) × 1.25.
- Rack whip = `per_rack_kw` / (√3 × V) × 1.25 at the PDU voltage (208Y/120 or 415Y/240 from the PDU transformer; BEN Micro at 208/240 V 1φ).

Conductors: copper, 90 °C insulation (THHN/THWN-2 or XHHW-2), **ampacity taken from NEC 310.16 at the 75 °C column** because terminations on breakers and lugs are rated 75 °C (110.14(C)). Ambient correction (310.15(B)) applies for conductors run through the hot aisle: at 40 °C ambient the 75 °C column is multiplied by 0.88 — the table below already selects a size that still passes after that correction where the run is in the hot aisle (marked †).

### 1.1 Feeder and breaker table (default presets; the frozen configuration reprints this)

| Tier / circuit | Load basis (config) | Calculated A | Breaker frame (A) | Conductor (Cu, 75 °C col.) | 310.16 ampacity | EGC (250.122) | Neutral |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **BEN Micro** service feeder, 240 V 1φ | 9.4 kVA | 49 | 50 | 8 AWG | 50 | 10 AWG | 8 AWG (full, 1φ) |
| BEN Micro UPS input/output, 240 V 1φ | 7 kVA | 29 → ×1.25 = 36 | 50 (to match feeder) | 8 AWG | 50 | 10 AWG | 8 AWG |
| BEN Micro rack whip, 240 V 1φ | 6 kW | 25 → 31 | 30 | 10 AWG | 35 | 10 AWG | 10 AWG |
| **BEN 10** service feeder, 208Y/120 V | 42.6 kVA | 148 | 150 | 1/0 AWG | 150 | 6 AWG | 1/0 AWG |
| BEN 10 UPS input, 208 V | 36 kVA | 100 → 125 | 150 | 1/0 AWG | 150 | 6 AWG | 1/0 |
| BEN 10 UPS output to PDU | 36 kVA | 100 → 125 | 125 | 1 AWG | 130 | 6 AWG | 1 AWG |
| BEN 10 rack whip, 208Y/120 V 3φ | 15 kW | 42 → 52 | 60 | 6 AWG† | 65 | 10 AWG | 6 AWG |
| **BEN 20** service feeder, 480Y/277 V | 135.2 kVA | 203 | 225 | 4/0 AWG | 230 | 4 AWG | 4/0 (full; non-linear loads) |
| BEN 20 UPS input, 480 V | 116 kVA | 140 → 175 | 200 | 3/0 AWG | 200 | 6 AWG | 3/0 |
| BEN 20 UPS output to PDU transformer primary, 480 V | 116 kVA | 140 → 175 | 200 | 3/0 AWG | 200 | 6 AWG | — (3-wire delta primary) |
| BEN 20 PDU transformer secondary 208Y/120 V (two 75 kVA) | 75 kVA each | 208 → 260 | 250 | 250 kcmil | 255 | 4 AWG (per 250.30 SBJ 2 AWG) | 250 kcmil |
| BEN 20 rack whip, 208Y/120 V 3φ | 19.2 kW | 53 → 67 | 70 | 4 AWG† | 85 | 8 AWG | 4 AWG |
| BEN 20 rack whip, 415Y/240 V 3φ (option) | 19.2 kW | 27 → 33 | 40 | 8 AWG† | 50 | 10 AWG | 8 AWG |
| BEN 20 in-row DX unit, 480 V 3φ (each ≈ 9.4 kW) | 30 kW/3.2 COP | 11 → 14 (MCA per nameplate governs) | 20 | 12 AWG | 25 | 12 AWG | — |
| **BEN 20 max** (150 kW, DLC) service feeder | 210.9 kVA | 317 | 400 | 600 kcmil or 2 × 3/0 parallel | 420 / 400 | 3 AWG | 600 kcmil |
| **BEN 40** service feeder (default 192 kW), 480Y/277 V | 223.5 kVA | 336 | 400 | 600 kcmil (or 2 × 3/0) | 420 | 3 AWG | 600 kcmil |
| BEN 40 UPS input, 480 V | 232 kVA | 279 → 349 | 400 | 600 kcmil | 420 | 3 AWG | 600 kcmil |
| BEN 40 CDU, 480 V 3φ | 16 kW elec. | 19 → 24 | 30 | 10 AWG | 35 | 10 AWG | — |
| BEN 40 dry cooler fan bank, 480 V 3φ | per vendor MCA | — | per MCA/MOCP | — | — | — | — |
| **BEN 40 max** (500 kW) service feeder | 581 kVA | 874 | 1000 | 3 × 400 kcmil per phase, parallel | 1005 | 2/0 AWG (per raceway if parallel: 2/0 in each) | 3 × 400 kcmil |
| BEN 40 max UPS input | 605 kVA | 728 → 910 | 1000 | 3 × 400 kcmil | 1005 | 2/0 | 3 × 400 kcmil |

Notes: (1) Neutral is full-size on all IT circuits because IT loads are non-linear (NEC 310.15(E), neutral counts as a current-carrying conductor). (2) Parallel sets per 310.10(G): same length, material, size, insulation, termination; each raceway carries one of each phase + neutral + EGC. (3) Voltage drop: keep feeders ≤ 3 %; at these lengths (< 15 m inside the container) it is never limiting. (4) Cooling unit circuits are sized from the nameplate **MCA/MOCP**, not from the config COP estimate; the config number is the budget check. (5) Where the AHJ's edition differs, re-check 310.16 — the table has not changed in substance since 2017.

### 1.2 Standard conductor reference (NEC 310.16, 75 °C column, Cu)

| Size | A | Size | A | Size | A |
| --- | --- | --- | --- | --- | --- |
| 14 AWG | 20 | 1 AWG | 130 | 300 kcmil | 285 |
| 12 AWG | 25 | 1/0 | 150 | 350 kcmil | 310 |
| 10 AWG | 35 | 2/0 | 175 | 400 kcmil | 335 |
| 8 AWG | 50 | 3/0 | 200 | 500 kcmil | 380 |
| 6 AWG | 65 | 4/0 | 230 | 600 kcmil | 420 |
| 4 AWG | 85 | 250 kcmil | 255 | 750 kcmil | 475 |
| 3 AWG | 100 | | | | |
| 2 AWG | 115 | | | | |

### 1.3 Equipment grounding conductor (NEC 250.122, Cu)

| Breaker (A) | EGC | Breaker (A) | EGC |
| --- | --- | --- | --- |
| 15 | 14 AWG | 400 | 3 AWG |
| 20 | 12 AWG | 500 | 2 AWG |
| 30–60 | 10 AWG | 600 | 1 AWG |
| 100 | 8 AWG | 800 | 1/0 |
| 200 | 6 AWG | 1000 | 2/0 |
| 300 | 4 AWG | 1200 | 3/0 |

## 2. Colour codes

| System | A | B | C | Neutral | Ground | High leg |
| --- | --- | --- | --- | --- | --- | --- |
| 208Y/120 V and 240 V 1φ | Black | Red | Blue | White | Green (or bare) | Orange (not used — no delta high-leg systems in BEN) |
| 480Y/277 V | Brown | Orange | Yellow | Grey | Green with yellow stripe | — |
| 415Y/240 V (PDU option) | Brown | Orange | Yellow | Grey | Green | — |
| DC (battery, PV) | Red (+) | — | — | Black (−) or white if grounded | Green | — |
| 24 V DC controls | Blue (+), Blue/white (0 V) | | | | | |
| 120 V AC controls (avoid; use 24 V DC) | Red | | | White | Green | |
| Intrinsically safe / life safety hardwired (fire panel contacts) | Light blue (IS convention) or per fire contractor, and labelled "FIRE — NOT ON BUS" | | | | | |

Where phase colours are used, they are applied at every termination point and at every accessible location (NEC 210.5(C), 215.12(C)) and a colour legend is posted in each panel.

## 3. Labelling scheme

Format: **UNIT – PANEL – CIRCUIT [– DEVICE]**

| Field | Example | Rule |
| --- | --- | --- |
| UNIT | `B20-0007` | Tier code (BM, B10, B20, B40) and four-digit serial; printed on every label so a photo is traceable |
| PANEL | `MDP`, `UPS1`, `UPS2`, `PDU-A`, `PDU-B`, `CP` (controls panel), `FP` (fire panel), `ATS`, `GEN` | Two to five characters |
| CIRCUIT | `PDU-A-07` | Breaker position number, two digits |
| DEVICE | `R03-L` (rack 3, left PDU), `CRAC-2`, `CDU-1`, `N03` (node 3) | What the circuit feeds |

Example full label on a rack whip: `B20-0007 PDU-A-07 → R03-L`. The same string is the `equip_id` in `spec/PROTOCOL.md` topics for metered circuits, so the dashboard and the panel agree.

Rules: engraved or thermal-transfer laminated labels (not hand-written); at both ends of every feeder and whip; circuit directories printed and placed in the panel door pocket and in the turnover package; arc-flash labels per NEC 110.16 with the study values; "FIRE — HARDWIRED — NOT ON CONTROLS BUS" on every fire-panel conductor; controls cable labels at both ends with node and channel, e.g. `N03 T_in_1`.

## 4. Torque table (typical; the device label governs — NEC 110.14(D) requires the manufacturer's value)

| Termination | Typical torque | Tool |
| --- | --- | --- |
| Breaker lugs 14–10 AWG (slotted) | 2.0–2.5 N·m (18–22 lb-in) | Torque screwdriver |
| Breaker lugs 8–6 AWG | 4.0–4.5 N·m (35–40 lb-in) | Torque screwdriver |
| Breaker lugs 4–1/0 AWG (hex) | 5.6–6.2 N·m (50–55 lb-in) | Torque wrench, hex bit |
| Lugs 2/0–4/0 AWG | 12–14 N·m (110–120 lb-in) | Torque wrench |
| Lugs 250–600 kcmil | 28–42 N·m (250–375 lb-in) | Torque wrench |
| Mechanical lug on ground bar, 2/0 | 14 N·m (120 lb-in) | |
| Bus bolts, 3/8-16 Grade 5 | 27 N·m (20 lb-ft) | |
| Bus bolts, 1/2-13 Grade 5 | 68 N·m (50 lb-ft) | |
| Compression lugs on bus, M10 | 30 N·m | |
| Terminal blocks, controls (screw clamp) | 0.5–0.6 N·m | Torque screwdriver |
| Terminal blocks, push-in | n/a; pull test 20 N | |
| Container anchor / twist-lock bolts M20 Grade 8.8 | 400 N·m | Calibrated torque wrench, record |
| Rack anchors M12 | 50 N·m | |

Every torqued termination is marked with torque-seal paint after tightening and logged (lug ID, specified, applied, date, initials). Re-torque is **not** done at the annual check unless the mark is broken or thermography shows a hot spot — repeated re-torquing damages terminations; verify with IR instead.

## 5. Controls wiring rules

| Rule | Why |
| --- | --- |
| **RS-485 (Modbus RTU) on shielded twisted pair**, 120 Ω characteristic impedance, 22–24 AWG (Belden 3106A class), daisy-chain only — no stars or stubs > 0.3 m | A bus with stubs reflects; reflections corrupt bits at 9.6–115 kbps over the 10–40 m runs in a container |
| **Terminate both ends** with 120 Ω; bias resistors at one end only (usually the gateway converter) | Matches the line impedance; bias keeps the idle state defined |
| **Ground the shield at one end only** (the controls-panel end) with a short pigtail; insulate the far end | Grounding both ends makes a loop; stray currents in the loop induce noise. One end drains static and capacitive pickup |
| **Signal common** (third conductor) is carried with the pair and connected at every device | RS-485 is differential but needs a common-mode reference within ±7 V |
| **Separate controls from power**: ≥ 300 mm from power conductors in parallel runs, cross at 90°, separate raceway or barriered tray (NEC 725.136 for Class 2) | Magnetic coupling from feeders induces 60 Hz and switching noise; Class 2 wiring must not share raceways with power circuits |
| **Ethernet (PoE to nodes)**: Cat 6A shielded, grounded at the switch end, ≤ 90 m, never through the hot aisle unbundled with power | Same reasons; shielded protects the 1 Hz telemetry from VFD/EC-fan noise |
| **1-Wire DS18B20 strings**: 3-wire (power, data, ground), ≤ 20 m per string, ≤ 8 sensors per bus, 2.2–4.7 kΩ pull-up at the node, strong pull-up where > 10 m | 1-Wire is a single-ended bus; long strings and many devices slow the edges and cause CRC errors |
| **I²C sensors (SHT45, SDP810, ADS1115)**: on the node board or ≤ 1 m shielded; never run I²C across the container — use a node per location | I²C is a board-level bus; capacitance kills it beyond a metre |
| **4–20 mA loops**: twisted pair, shield at the panel, 165 Ω shunt at the node (ADS1115), loop power 24 V from the Class 2 supply, fuse each loop at 100 mA | Current loops are noise-immune and detect open wires (0 mA) and shorts (> 21 mA) |
| **Relay outputs** (cooling enable, lights, fan boost, spare): 10 A relays drive **interposing contactors** for anything over 2 A or any inductive load; a flyback diode or RC snubber across coils | Protects node relays and avoids resetting the ESP32 from inductive kicks |
| **Failsafe wiring**: cooling enable is wired so **loss of node power or gateway = cooling ON** (normally-closed contact opens the "disable" input) | A dead controller must never stop cooling (`PROTOCOL.md` safety rules) |
| **Life safety is hardwired**: fire panel releasing, HVAC shutdown on detection, EPO — on their own supervised circuits from the UL 864 panel; the node only reads dry contacts | Never on MQTT; a software fault must not disable fire protection |
| **Surge**: Type 2 SPD at the MDP, Type 3 at the controls panel; data-line SPDs on any RS-485/Ethernet leaving the container (to dry cooler, generator) | Outdoor runs pick up induced surges |
| **Controls panel (UL 508A)**: SCCR marked; 24 V Class 2 supply; separate terminal strips for field wiring; wire duct; every wire ferruled and numbered to the drawing | Panel-shop listing requires it; makes troubleshooting fast |

## 6. Sensor placement rules and the physics behind them

| Rule | Physics / reason |
| --- | --- |
| **Rack inlet temperature at three heights** (bottom ≈ U4, middle ≈ U20, top ≈ U38; `T_in_1..3`, `T_in_4` spare or top-of-rack) | Cold-aisle air stratifies: supply enters low (in-row and raised-floor designs) and warms as it rises; recirculation over the top of the rack and through gaps makes the **top U the hottest**. ASHRAE TC 9.9 specifies the measurement at the inlet of the equipment, and one point cannot represent a 2 m column. Three heights capture the gradient and prove containment works (top − bottom < 2 °C is a good containment) |
| **Sensors 50 mm off the door / rack front, centred in the perforated area, not touching metal** | A sensor touching the door reads the **door metal temperature** (conduction), not the air; metal is coupled to the room radiation field and the rack frame. 50 mm is far enough to be in the free stream drawn by the servers, close enough to be the air the servers actually ingest. Radiation error is reduced by a small sensor with low emissivity housing; conduction error by stand-off clips |
| **Outlet sensors (`T_out`) 100 mm behind the rear door at mid-height, out of the direct fan jet** | Server exhaust is a set of hot jets at different temperatures; a sensor in one jet reads that server, not the rack. Set back and mid-height gives a mixed value. ΔT across the rack is the load proxy |
| **`T_ref` (SHT45) at the cooling unit return, in the mixed stream** | The reference should see the best-mixed air; it also anchors the DS18B20 strings during the isothermal cross-check (E1) |
| **RH measured at the supply and return, not the aisle floor** | Humidity ratio is constant through the rack (sensible heat only); RH changes only with temperature. Measuring at supply shows dew-point margin for cold surfaces; return shows the true room moisture |
| **Differential pressure taps (`dP_aisle`): cold aisle to hot aisle, taps ≥ 1 m from any fan discharge or intake, flush wall taps perpendicular to the flow, 4 mm tubing ≤ 5 m, same length both sides** | A tap near a fan discharge reads **velocity pressure**, not static pressure — a 5 m/s jet adds ~15 Pa, more than the whole signal (5–15 Pa). Flush, perpendicular taps read static only (Bernoulli). Equal tube lengths cancel thermal and acoustic effects |
| **dP sensor mounted vertically, tubing without low points, and tared at fan-off (E2)** | Condensation in tubing gives a false offset; the SDP810 has ~0.1 Pa zero stability but position affects it; taring at zero flow removes the mounting offset and gives the ±0.4 Pa stated in `PROTOCOL.md` |
| **Leak rope under every liquid component, around the perimeter at the low point of the floor, 20 mm from the wall** | Water travels along the lowest line; containers are set with a 0.5 % drain fall toward the door end; the rope must be where the water goes, not where the pipe is |
| **Door reed on the hinge side top, with 10 mm gap maximum** | Doors sag at the latch side; the hinge side stays aligned over time |
| **Refrigerant / gas detectors low** (A1 refrigerants and most gases are heavier than air): 300 mm above floor, away from the door draught; **H₂ detector high** for battery compartments | Density decides where a leak collects |
| **Power meter CTs on the unit's incoming feeder, inside the MDP, with the correct polarity (arrow toward load)** | PUE denominator; wrong polarity = negative kW and a failed E9 |
| **Node placement**: one node per rack pair (BEN 20: 3 nodes + 1 environmental), nodes in the cold aisle at mid-height, PoE from the controls switch | Keeps 1-Wire strings short and I²C local |

## 7. Grounding and bonding of the container

1. Main bonding bar (copper, 6 × 50 mm) in the electrical vestibule, bonded to the MDP ground bus with 2/0 AWG (BEN 10/20) or 250 kcmil (BEN 40).
2. Container shell bonded to the bar at **two diagonally opposite corner castings** with 2/0 AWG and listed lugs on cleaned, welded bonding pads (paint removed to bright metal, anti-oxidant, pad painted after).
3. Every rack bonded to a rack grounding busbar (telecom "TGB" style, 2 AWG), racks bonded with 6 AWG jumpers; cable trays bonded every 10 m and at every splice.
4. PDU transformer secondaries are separately derived systems: system bonding jumper per 250.30, grounding electrode conductor to the main bonding bar.
5. Site electrode conductors (two × 2/0) land on the main bonding bar at the corner lugs provided; electrode resistance tested and recorded.
6. Shield drains for controls cables land on the controls-panel ground bar, which is bonded to the main bar by 6 AWG — single point.

## 8. Commissioning hand-off (what the electrician gives the commissioning engineer)

| Item | Evidence |
| --- | --- |
| Torque log, 100 % of terminations, with torque-seal marks visible | Signed log |
| Insulation resistance (megger) of every feeder at 1,000 V DC: ≥ 100 MΩ; whips at 500 V: ≥ 100 MΩ | Table per circuit |
| Bonding continuity: container shell to main bar ≤ 0.1 Ω; each rack to TGB ≤ 0.1 Ω | Table |
| Phase rotation ABC at MDP, UPS output, each PDU; confirmed matching the utility at SAT | Photo of rotation meter |
| Breaker trip-unit settings per coordination study | Settings sheet signed |
| Circuit directories complete and matching labels | Photos |
| Provisional arc-flash labels installed; "site data TBD" stickers in place | Photos |
| CT polarity and ratio set in the power meter; meter kW positive under load | Screenshot |
| All controls I/O point-to-point checked (every channel in `PROTOCOL.md` toggled or stimulated once) | I/O checklist CSV |
| Failsafe test: pull node power → cooling enable stays ON; pull gateway → nodes keep publishing to buffer; restore → buffer drains | Test record |
| Fire contractor's dry contacts verified at the node with the fire panel in test mode | Joint record |

The commissioning engineer does not start `commissioning.py` until this hand-off is complete. The script then takes over (`docs/TEST_GUIDE.md`).
