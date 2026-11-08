# Item codes — reconciled with purchasing/parts_catalog.json

Generated 2026-11-08 by `design/assembly/gen_assembly.py`. Every code in the assembly instructions and on the drawings is a code from `purchasing/parts_catalog.json` (197 parts). Codes marked **new** were appended to the catalog by the design generator as `estimate` lines (basis note on each) because no catalog part covered them; purchasing confirms or replaces them.

| Catalog code | Catalog name | Status | Used in assembly docs (tiers) | On drawings (tiers) | Working code it replaced |
|---|---|---|---|---|---|
| CLG-ADIABATIC | Adiabatic dry cooler bank, V-type, EC fans, glycol, wetted pre-cooling pads with water-fre | estimate |  | ben2000 |  |
| CLG-CABAC | Blue e+ wall-mounted enclosure cooling unit 5.8 kW, 400/480 V 3-ph | confirmed | ben5, ben2000 | ben5 | CLG-001 |
| CLG-CDU | Row CDU 450-750 kW liquid-to-liquid (DLC) | estimate | ben500, ben2000 | ben2000, ben500 | CLG-020 |
| CLG-CDU-RDHX | Row CDU 70-100 kW liquid-to-liquid for RDHx loop | estimate | ben150 | ben150 | CLG-030 |
| CLG-COND | Outdoor air-cooled condensing unit for ACRD301S (30 kW), 460 V | estimate | ben30, ben500 | ben30, ben500 | CLG-015 |
| CLG-CONDPUMP | Condensate pump per DX unit | estimate | ben5, ben30, ben500 |  | CLG-017 |
| CLG-DRYCOOLER | Outdoor dry cooler (V-type, EC fans), adiabatic-ready, glycol | estimate | ben150, ben500, ben2000 | ben150, ben500 | CLG-040 |
| CLG-FANWALL | Fan-wall air handler 200 kW class on the hall long wall, chilled/glycol coil, EC fan array | estimate |  | ben2000 |  |
| CLG-GLYCOL | Propylene glycol inhibited, 25% mix (gal) | estimate | ben150, ben500, ben2000 |  | CLG-033 |
| CLG-INROW | InRow DX 300 mm 30 kW air-cooled in-row unit (indoor section) (ACRD301S is the 300 mm, ~20 | confirmed | ben30, ben500 | ben30, ben500 |  |
| CLG-MANIFOLD | Rack coolant manifold pair + QD hose kit (DLC) | estimate |  | ben2000 |  |
| CLG-PIPING | Glycol loop piping, valves, pumps skid, expansion tank, strainers (per m container length) | estimate | ben150, ben500, ben2000 |  | CLG-034 |
| CLG-PIPING-HALL | Plant piping: primary glycol loop DN200 to the dry coolers, secondary DN150 headers to the | estimate |  | ben2000 |  |
| CLG-RDHX | Active rear-door heat exchanger, 42/48U, up to 40 kW | estimate | ben150 |  | CLG-031 |
| CLG-REFRIG | Refrigerant line set, insulation, R-513A (A1, GWP ~630) charge per DX unit | estimate | ben30, ben500 |  | CLG-016 |
| CMP-BLANK | 1U tool-less blanking panels, pack of 10 (every open U, CTQ-B5) | **new** (estimate) | ben30, ben150, ben500 |  | CMP-010 |
| CTL-CAT6A | Cat6A UTP patch cable 10 ft | confirmed | ben5, ben30, ben150, ben500, ben2000 |  | CTL-009 |
| CTL-DOOR | Surface-mount magnetic door contact | confirmed | ben5, ben30, ben150, ben500, ben2000 |  | CTL-007 |
| CTL-EDGE | OnLogic Karbon 400 (K410) industrial edge computer: Atom x6425E, 16 GB, 256 GB NVMe, TPM 2 | estimate | ben150, ben500, ben2000 |  | CTL-014 |
| CTL-ENCL | CAB PC polycarbonate wall box 300x200x180 mm IP65 with DIN rail (BEN Controls Lite cabinet | confirmed | ben5, ben30 | ben30 | CTL-001 |
| CTL-IO-AI | AXL F AI4 I 1H Axioline F 4-channel 4-20 mA analog input (Setra 264 dP, Vaisala RH/T, spar | confirmed | via CTL-PANEL |  |  |
| CTL-IO-DIO | AXL F DI8/1 DO8/1 1H Axioline F 8 DI 24 VDC + 8 DO 24 VDC 0.5 A (door, EPO/fire monitor co | confirmed | via CTL-PANEL |  |  |
| CTL-IO-RTD | AXL F RTD4 1H Axioline F 4-channel RTD input (Pt1000 2/3/4-wire) for cooling unit supply/r | confirmed | via CTL-PANEL |  |  |
| CTL-LABELS | Label printer cartridges, cable labels, engraved phenolic tags (lot) | estimate | ben5, ben30, ben150, ben500, ben2000 |  | CTL-011 |
| CTL-LEAK | SeaHawk conductive-fluid leak sensing cable 50 ft, connectorised (to LD2100 on Pro; to Pod | confirmed | ben5, ben30, ben150, ben500, ben2000 | ben150, ben2000, ben30, ben500 | CTL-010 |
| CTL-LEAK-CTRL | SeaHawk LD2100 distance-read leak detection controller, web enabled, relay + Modbus to the | confirmed | ben150, ben500, ben2000 |  | CTL-016 |
| CTL-LEAK-LEADER | Leak cable leader + end-of-line terminator | estimate | via CTL-LEAK |  |  |
| CTL-MGM240P | MGM240PB32VNA3R Thread/802.15.4 module, EFR32MG24, Secure Vault High, PCB antenna, FCC/IC/ | confirmed | via CTL-POD |  |  |
| CTL-PANEL | Wall-mount enclosure Type 12/IP65, 30x24x12 in (762x610x305 mm, the 800x600x300 class), st | confirmed | ben150, ben500, ben2000 | ben150, ben2000, ben500 | CTL-001 |
| CTL-PANEL-BUILD | UL 508A panel shop: assembly, wiring, SCCR calculation and label, point-to-point drawings, | estimate | via CTL-PANEL |  |  |
| CTL-PANEL-KIT | Controls panel hardware lot: DIN rail, wire duct, 600 V MTW wire, ferrules, fuse holders + | estimate | via CTL-PANEL, CTL-ENCL |  |  |
| CTL-PLC | PLCnext AXC F 2152 controller (IEC 61131-3 + Linux, 2x Ethernet, Axioline F local bus, UL  | confirmed | ben150, ben500, ben2000 | ben2000 | CTL-012 |
| CTL-POD | BEN Pod v1 assembled and provisioned (MGM240P Thread module w/ Secure Vault High, 4x Pt100 | estimate | ben5, ben30, ben150, ben500, ben2000 | ben150, ben2000, ben30, ben5, ben500 | CTL-002 |
| CTL-POD-ENCL | BEN Pod enclosure: Phoenix Contact ICS 50 DIN-rail housing set with rack-rail clip (IP40); | estimate | via CTL-POD |  |  |
| CTL-PSU-ORING | QUINT4-S-ORING/12-24DC/1X40 redundancy (diode) module for the two QUINT4 supplies | confirmed | via CTL-PANEL |  |  |
| CTL-PSU-QUINT | QUINT4-PS/1AC/24DC/10 DIN-rail 24 VDC 10 A power supply (UL 508 listed; 2 redundant on Pro | confirmed | ben5, ben30, ben150, ben500, ben2000 |  | CTL-017 |
| CTL-PT1000 | Pt1000 class A 3-wire RTD probe string: 4 probes (3 inlet, 1 outlet), 6 mm SS tip, 3 m PTF | estimate | ben5, ben30, ben150, ben500, ben2000 |  | CTL-003 |
| CTL-RCP | xG24-EK2703A Explorer Kit (EFR32MG24/MGM240P) as OpenThread Border Router radio co-process | list | ben5, ben30, ben150, ben500, ben2000 |  | CTL-015 |
| CTL-RELAY | PLC-RSC-24DC/21 DIN interface relay 6 A SPDT (PLC/RevPi DO to cooling enable, fan boost, v | confirmed | via CTL-PANEL, CTL-ENCL |  |  |
| CTL-REVPI | RevPi Connect 4 industrial controller (CM4-based industrial controller, 8 GB eMMC, 2x Ethe | confirmed | ben5, ben30, ben2000 | ben5 | CTL-013 |
| CTL-REVPI-AIO | RevPi AIO module, 4 AI (4-20 mA / 0-10 V) + 2 AO + 2 RTD inputs (cooling unit supply/retur | list | via CTL-ENCL |  |  |
| CTL-REVPI-DIO | RevPi DIO module, 14 DI + 14 DO 24 VDC (door, EPO/fire monitor contacts, cooling status; o | list | via CTL-ENCL |  |  |
| CTL-RS485 | RS-485 cable Belden 3106A 22 AWG shielded pair, 100 ft (Pod E to PLC/RevPi Modbus RTU) | estimate | via CTL-PANEL, CTL-ENCL |  |  |
| CTL-SDP810 | SDP810-125Pa differential pressure sensor, I2C (fitted on the two room Pods: aisle dP and  | confirmed | ben5, ben30 |  | CTL-005 |
| CTL-SETRA264 | Setra 264 very low differential pressure transmitter 0-0.25 in WC, 4-20 mA (aisle dP on th | confirmed | ben150, ben500, ben2000 |  | CTL-005 |
| CTL-SPD | VAL-MS 230/3+1 Type 2 surge arrester, pluggable, for the controls panel supply | confirmed | via CTL-PANEL |  |  |
| CTL-SWITCH | FL SWITCH 2008 managed industrial Ethernet switch, 8x RJ45, RSTP, DIN rail (controls LAN:  | confirmed | ben150, ben500, ben2000 |  | CTL-008 |
| CTL-SWITCH-LITE | Moxa EDS-2008-EL compact industrial Ethernet switch, 8x RJ45, DIN rail, 9.6-60 VDC (Lite c | confirmed | ben5, ben30 |  | CTL-008 |
| CTL-TERM | UT 2,5 feed-through DIN terminal block | confirmed | via CTL-PANEL, CTL-ENCL |  |  |
| CTL-VAISALA-HMW90 | Vaisala HMW90 wall humidity and temperature transmitter, +/-1.7 %RH, 4-20 mA (room RH on t | estimate | ben150, ben500, ben2000 |  | CTL-004 |
| ENV-DOORGASKET-4X | Compression door gasket kit: EPDM sponge D-profile 20 mm on the frame, 3-point compression | estimate |  | ben2000 |  |
| ENV-DOORSEAL | EPDM bulb door seal 20 mm, self-adhesive, 10 m roll (secondary seal on cargo doors) | **new** (estimate) | ben30, ben150, ben500 |  | ENV-005 |
| ENV-DRAIN | Floor drain 50 mm with trap and exterior cap, stainless | **new** (estimate) | ben30, ben150, ben500 |  | ENV-011 |
| ENV-FLOOR | Anti-static vinyl floor tile over container plywood floor | estimate | ben30, ben150, ben500 |  | ENV-007 |
| ENV-FLOOR-PIR | Floor build-up: 80 mm PIR + 18 mm plywood, per m2 (under anti-static vinyl, A-003 Detail 2 | **new** (estimate) | ben30, ben150, ben500 |  | ENV-006 |
| ENV-HAT | Steel hat channel / furring 7/8 in x 10 ft | estimate | ben30, ben150, ben500 |  | ENV-004 |
| ENV-LED | 4 ft LED strip light 4000K, 120-277 V | confirmed |  | ben2000 |  |
| ENV-LINER | Ribbed 29-ga galvanized steel liner panel 3 ft x 8 ft | confirmed | ben30, ben150, ben500 |  | ENV-002 |
| ENV-MICRO-HEATER | Anti-condensation heater 100 W with thermostat + replacement IP55 door gasket (BEN 5 cabin | **new** (estimate) | ben5, ben2000 |  | ENV-013 |
| ENV-PIR | Polyiso (PIR) foil-faced board 2 in x 4 ft x 8 ft, R-13 (two layers = 100 mm) | confirmed | ben30, ben150, ben500 |  | ENV-001 |
| ENV-ROOFBOOT | EPDM roof boot + butyl tape + clamp band for line-set / pipe curb | **new** (estimate) | ben30, ben150, ben500 |  | ENV-008 |
| ENV-SEAL | Fire-rated sealant / low-expansion PU foam | estimate | ben30, ben150, ben500 |  | ENV-010 |
| FS-AEROSOL | Condensed aerosol fire suppression unit for BEN 5 cabinet (no piping) | estimate | ben5, ben2000 | ben5 | FS-001 |
| FS-CLEAN-AGENT | Pre-engineered FK-5-1-12 (Novec 1230) clean agent system, installed: cylinder, nozzles, re | estimate | ben30, ben150, ben500 | ben150, ben30, ben500 | FS-040 |
| FS-CLEAN-AGENT-HALL | Pre-engineered FK-5-1-12 clean agent per module zone + power module: cylinders, nozzles, r | estimate |  | ben2000 |  |
| FS-EPO | Emergency Power Off (EPO) button station | confirmed | ben5, ben30, ben150, ben500, ben2000 | ben150, ben2000, ben30, ben500 | PWR-130 |
| FS-EXT | 10 lb CO2 portable fire extinguisher | estimate | via FS-CLEAN-AGENT |  |  |
| FS-SIGNS | Arc-flash labels, warning signage, egress signage (lot) | estimate | via FS-CLEAN-AGENT |  |  |
| FS-SMOKE | Intelligent photoelectric smoke detector (replacement for SIGA-PS) | confirmed | ben30, ben150, ben500 |  | FS-030 |
| FS-VESDA | VESDA-E VEU aspirating smoke detector, UL | confirmed | via FS-CLEAN-AGENT |  |  |
| PWR-ATS-200 | Series 300 ATS 200 A 3P 208 V, NEMA 4X | estimate | via PWR-SVC-ENCL |  |  |
| PWR-ATS-400 | Series 300 ATS 400 A 3P 480 V, service-entrance rated, NEMA 4X | estimate | via PWR-SVC-ENCL |  |  |
| PWR-BATT-LI | Galaxy Lithium-ion battery cabinet UL, 16 x 2.04 kWh modules (32.6 kWh) | confirmed | ben500 | ben500 |  |
| PWR-BATT-ROOM | Lithium (LFP) UPS battery cabinets for the 2,000 kW strings, UL 9540 / UL 9540A, in two ba | estimate | ben2000 | ben2000 |  |
| PWR-BUSWAY | Overhead track busway 800 A 480 V, 36 m run with end-feed, 12 plug-in tap-off boxes 60 A 3 | estimate |  | ben2000 |  |
| PWR-EPO-RELAY | Shunt-trip / EPO interface relay and wiring to main breaker | estimate | via PWR-SVC-ENCL |  |  |
| PWR-FEEDER | Feeder cable, conduit, lugs, breaker-to-UPS-to-PDU distribution (per ampere of service bre | estimate | ben5, ben30, ben150, ben500, ben2000 |  | PWR-150 |
| PWR-FUEL-48H | Bulk diesel storage 10,000 gal (38 m3) UL 2085 protected above-ground tank, fuel polishing | estimate | ben2000 | ben2000 |  |
| PWR-GEN-1250 | Diesel standby generator 1,250 kW / 1,562 kVA 480 V, EPA Tier 2 stationary emergency, Leve | estimate | ben2000 | ben2000 |  |
| PWR-GEN-PARALLEL | Generator paralleling switchgear 480 V 4,000 A with load-share controls, utility-paralleli | estimate | ben2000 | ben2000 |  |
| PWR-GROUNDBAR | Telecom grounding busbar kit 1/4 x 4 x 12 in with insulators/brackets | confirmed | ben5, ben30, ben150, ben500, ben2000 |  | PWR-160 |
| PWR-LOADCTR | QO 100 A 20-space outdoor (NEMA 4X) load center with 50 A 2P main for BEN 5 | estimate | ben5, ben2000 | ben5 | PWR-030 |
| PWR-LV-SWGR-4000 | 480 V low-voltage switchgear 4,000 A UL 1558, drawout power circuit breakers, main-tie-mai | estimate | ben2000 | ben2000 |  |
| PWR-MAIN-BKR | PowerPact L-frame main breaker 400 A 3P 480 V, LSI electronic trip | estimate | via PWR-SVC-ENCL |  |  |
| PWR-MV-SWGR | Pad-mounted 15 kV class switchgear, 600 A, 4-way (2 source ways + 2 fault-interrupter tran | estimate | ben2000 | ben2000 |  |
| PWR-MV-XFMR-2500 | Pad-mount transformer 2,500 kVA, 12.47 kV delta (or 13.8 kV) - 480Y/277 V, FR3 natural est | estimate | ben2000 | ben2000 |  |
| PWR-PANEL-BOX | I-Line panelboard box + trim, NEMA 1, 32 in W x 73 in H | estimate | via PWR-PANEL-ILINE |  |  |
| PWR-PANEL-ILINE | I-Line panelboard interior 400 A MLO 480Y/277 V, 42 circuit (HCJ) | confirmed | ben30, ben150, ben500 | ben150, ben500 | PWR-120 |
| PWR-PANEL-NQ | NQ panelboard 225 A MLO 208Y/120 V, 42 circuit, with 150 A main breaker (ben30) | estimate | ben30 | ben30 | PWR-121 |
| PWR-PDU | NetShelter metered rack PDU 0U 5.0 kW 208 V 30 A, L6-30P, (36) C13 (6) C19 | confirmed | ben5, ben30, ben150, ben500, ben2000 | ben5 | PWR-020 |
| PWR-RCPT | Rack PDU receptacle IEC 60309 30/32 A with box and labelled pigtail (A + B per rack) | **new** (estimate) | ben5, ben30, ben150, ben500, ben2000 |  | PWR-170 |
| PWR-SPD | Surgelogic SPD 40 kA, 600Y/347 V 3-ph 4-wire, NEMA 4X | confirmed | via PWR-SVC-ENCL |  |  |
| PWR-SVC-ENCL | NEMA 4X service-section enclosure, wall-mount on blind end, houses main breaker + SPD + AT | **new** (estimate) | ben30, ben150, ben500 | ben150, ben30, ben500 | PWR-140 |
| PWR-UPS-GVL500 | Galaxy VL UPS 500 kVA/kW 480 V frame, N+1 internal power modules, parallel-capable (4 fram | confirmed | ben2000 | ben2000 |  |
| PWR-UPS-GVS100 | Galaxy VS UPS 100 kW 480 V for external batteries, start-up 5x8 | confirmed | ben150, ben500 | ben150, ben500 |  |
| PWR-UPS-RM20 | Rack/tower online UPS 20 kVA 208 V, 10U, parallel-capable (BEN 30 R1, 3 x in parallel for  | **new** (estimate) | ben5, ben30, ben2000 | ben30 | PWR-010 |
| PWR-UPS-RM20-XBP | External battery cabinet 6U for 20 kVA rack UPS (10 min at 30 kW with the parallel set) | **new** (estimate) | ben5, ben30, ben2000 | ben30 | PWR-011 |
| PWR-UPS-SRT6K | Smart-UPS SRT 6 kVA RM 208 V online double-conversion | confirmed |  | ben5 |  |
| PWR-UPS-SRT6K-XBP | Smart-UPS SRT 192 V external battery pack (for 10 min at 6 kW) | estimate |  | ben5 |  |
| PWR-XFMR | Dry-type step-down transformer 480 D - 208Y/120 V, 150 kVA (ben150) / 300 kVA (ben500), fo | estimate | ben150, ben500 |  | PWR-122 |
| SITE-CRANE | Mobile crane with operator, half day, set container on pad | estimate | ben5, ben30, ben150, ben500, ben2000 |  | SITE-005 |
| SITE-CRANE-HALL | Mobile crane 100-130 t with operator and rigging crew, 4 days: set 9 hall sections + 3 pow | estimate |  | ben2000 |  |
| SITE-FIBER | Fiber drop, handhole, 24-strand SM to demarc | estimate | ben5, ben30, ben150, ben500, ben2000 |  | SITE-004 |
| SITE-GROUND | Grounding electrode system: 3 rods, #2 Cu ring, exothermic welds, test | estimate | ben5, ben30, ben150, ben500, ben2000 |  | SITE-003 |
| SITE-PAD | Reinforced concrete pad 6 in, #4 rebar 12 in o.c., compacted base, 0.6 m margin each side | estimate | ben5, ben30, ben150, ben500, ben2000 |  | SITE-001 |
| SITE-TRANSPORT-KIT | Transport blocking and strapping kit: timber blocking, ratchet straps, rack door locks, dr | **new** (estimate) | ben5, ben30, ben150, ben500, ben2000 |  | SITE-006 |
| STR-CAB24U | Outdoor NEMA 4X / IP66 24U cabinet, aluminium (UL 50E Type 4X), 300 mm plinth, two side cu | estimate | ben5, ben2000 | ben5 | CMP-003 |
| STR-CONT-DOOR | Hot-aisle containment sliding double door kit (2-pack) | confirmed | via STR-CONT-ROOF |  |  |
| STR-CONT-FRAME | Hot-aisle containment frame end kit (SmartRack) | confirmed | via STR-CONT-ROOF |  |  |
| STR-CONT-ROOF | Hot-aisle containment roof/riser panels, clear polycarbonate on aluminium frame (made in-h | estimate | ben30, ben500 | ben2000, ben30, ben500 | CLG-050 |
| STR-FASTENERS | Fastener & hardware kit (self-drilling TEK screws, rivets, Unistrut, anchors) | estimate | ben5, ben30, ben150, ben500, ben2000 |  | STR-011, STR-022 |
| STR-FLOORCHAN | Floor channel C100x50x5 hot-dip galvanised, 3 m length (2 runs under the row, S-001) | **new** (estimate) | ben30, ben150, ben500 | ben150, ben30, ben500 | STR-001 |
| STR-MODULE-PWR | Power module 12.2 x 11.0 x 4.2 m (three road sections), factory-fitted: 480 V switchgear r | estimate | ben2000 | ben2000 |  |
| STR-PLANTYARD | Plant-yard steel: equipment skids for CDUs/pump skid, pipe rack 30 m, generator and dry-co | estimate |  | ben2000 |  |
| STR-RACK42 | NetShelter SX 42U 600x1070 mm enclosure with sides | confirmed | ben30, ben150 | ben150, ben30 |  |
| STR-RACK48 | NetShelter SX 48U 600x1070 mm enclosure with sides (1070 deep keeps the 900 mm aisle in a  | estimate | ben500 | ben2000, ben500 |  |
| STR-SEISMIC | NetShelter SX high-seismic / OSHPD bolt-down kit | confirmed | ben30, ben150, ben500 |  | STR-005 |
| STR-SKID | Steel skid base for BEN 5 cabinet (C6 channel frame, forklift pockets, 4 lifting eyes) | estimate | ben5, ben2000 | ben5 | STR-010 |
| STR-TIEDOWN | Twistlock / tie-down anchor set (4 corner castings to pad) | estimate | ben5, ben30, ben150, ben500, ben2000 |  | SITE-002 |
| STR-TRAY | Wire-mesh cable tray 300 x 100 mm, 3 m length, with ceiling hangers (data + power runs) | **new** (estimate) | ben30, ben150, ben500 | ben150, ben2000, ben30, ben500 | STR-021 |
| SVC-MODS-MAT | Container modification materials per opening (frame steel, flashing, louvers, primer) | estimate | ben5, ben30, ben150, ben500, ben2000 |  | ENV-012, STR-004 |
| SVC-WELDER | Certified (AWS D1.1) mobile welder: cutouts, frames, reinforcement, door install | estimate | via SVC-MODS-MAT |  |  |

## Catalog items the drawings assume but the catalog sizes differently

- `PWR-UPS-93PM50` (BEN 30): two 50 kW towers (495 mm wide each) do not fit the 10 ft row; the drawings and instructions use `PWR-UPS-RM20` x 3 + `PWR-UPS-RM20-XBP` (new). Purchasing decides which stays.
- `PWR-UPS-GVS100` / `PWR-BATT-LI` (BEN 150/500): qty rules `ceil(ups_kva_each/100)*ups_modules` give 4 / 6 UPS frames and 2 / 4 battery cabinets; the rows do not hold them (check I-C21). Drawings use one modular frame with N+1 modules (+ 2 battery cabinets for BEN 500). Recommend qty rule `ceil(ups_kva_each*1.0/100)+1` frames per unit, not per module.
- `STR-RACK48` is 600 x 1200 deep: the BEN 500 aisle drops to 800 mm (< 900 egress, check I-C22). Drawings use a 1070-deep 48U enclosure; change the catalog part or use 42U 1070 racks.
- `CLG-INROW` is the 300 mm / 20 kW-class unit (`inrow_dx_300`); the catalog note says the 600 mm / 30 kW unit is to be quoted separately. BEN 500 residual air also uses `CLG-INROW` (4 units) + `CLG-COND`, which the catalog currently limits to ben10/ben20 (`applies_to_tiers`).
- `FS-PANIC` (new) is required by the egress note in DESIGN_BASIS §6.
