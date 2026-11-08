# Architecture

## The one idea
A **configuration** (`spec/ben-config.schema.json`, produced by the selector) is the root of everything. Every deliverable is a function of it.

```mermaid
flowchart LR
  SEL[Selector<br/>web/ · dashboard · CLI] --> CFG[(Config<br/>config.py)]
  CFG --> BOM[BOM + prices<br/>bom.py + parts_catalog.json]
  CFG --> DRW[IFC drawings + renders<br/>design/drawings, design/renders]
  CFG --> TWIN[Digital twin<br/>twin.py]
  CFG --> CFD[2-D LBM CFD<br/>cfd.py]
  CFD -->|recirculation profile| TWIN
  TWIN --> SWP[Automated sweeps<br/>sweeps.py]
  TWIN --> API[FastAPI + WebSocket<br/>api.py]
  API --> DASH[Dashboard + 3-D scene<br/>dashboard/static]
  SWP --> COM[Commissioning script<br/>commissioning.py]
  COM --> REP[Signed report + CSV]
  TEL[Measured telemetry<br/>BEN Pods + PLC I/O + Modbus/SNMP] --> ANA[Calibration + analysis<br/>calibration.py, analysis.py]
  ANA -->|fitted TwinParams| TWIN
  CFG --> COMP[Compliance pack + risk list<br/>docs/COMPLIANCE.md, web/assets/risks.json]
  CFG --> STE[STE assembly instructions<br/>design/assembly]
```

## Runtime inside a deployed unit
```mermaid
flowchart TB
  subgraph BEN Controller panel (UL 508A · IEC 62443 zone 1)
    PLC[PLC · Phoenix Contact PLCnext AXC F 2152<br/>Axioline F I/O: DI/DO, RTD, 4–20 mA<br/>interlocks, failover, watchdog relay]
    EDGE[Edge computer · OnLogic Karbon 400, TPM 2.0<br/>Mosquitto · ben_engine.api · SQLite · OTBR · chrony]
    SW[Managed switch · FL SWITCH 2008]
    PLC <-->|Modbus TCP / OPC UA| EDGE
    PLC --- SW
    EDGE --- SW
  end
  subgraph BEN Mesh (Thread / IPv6, 2.4 GHz)
    RCP[MGM240P border router RCPs ×2 on USB]
    PW[BEN Pod W · rack cold/hot faces<br/>4 × Pt1000, SHT45, attested]
    PE[BEN Pod E · room + outdoor<br/>RS-485 to PLC, Thread router]
    PW & PE -->|MQTT/JSON over DTLS/TLS 1 Hz| RCP
    RCP --> EDGE
    PE -.Modbus RTU.-> PLC
  end
  subgraph Wired transmitters on the PLC
    TX[Pt1000 supply/return · Setra 264 dP<br/>Vaisala HMW90 RH · RLE LD2100 leak]
    TX --> PLC
  end
  subgraph Vendor equipment (zone 1 VLAN)
    PM[Power meter · Modbus RTU]
    UPS[UPS · Modbus TCP/SNMP]
    CU[Cooling units · Modbus]
    PDU[Rack PDUs · SNMP]
    PM & UPS & CU & PDU -->|poll| EDGE
    CU -.enable / status.- PLC
  end
  subgraph Life safety (hardwired, no network)
    SD[Smoke detection] --> REL[Clean-agent release panel]
    EPO[EPO buttons] --> SHUNT[Shunt-trip breakers]
    REL -.dry contact.-> PLC
    EPO -.dry contact.-> PLC
  end
  subgraph Customer IT (zone 2, isolated)
    SRV[Racks / servers / GPUs]
  end
  OPS[Operator browser<br/>local or VPN] -->|HTTPS/WS| EDGE
  EDGE -. outbound-only support tunnel (optional) .-> SAI[Schreiber AI ops]
```

Two controls tiers run this architecture (`docs/CONTROLS_HARDWARE_DECISION.md` §2a, `Config.controls_tier`): **BEN Controls Pro** (BEN 150/500, selectable on BEN 30) is the diagram above. **BEN Controls Lite** (BEN 5, default on BEN 30) replaces the PLC + edge computer pair with one DIN-rail **Revolution Pi RevPi Connect 4** with RevPi DIO/AIO modules: it runs `ben_engine`, the broker, the border router and the interlock logic in software behind a hardware watchdog relay. Same Pods, same mesh, same protocol, same dashboard; life safety is hardwired in both.

## BEN 2000: the same architecture, multiplied by module
BEN 2000 (`TIER_GEOMETRY["ben2000"]`, `kind: "hall"`, `modules: 3`) is a prefabricated hall of three site-joined wide-body modules, a separate power module and a plant yard (`docs/TIER_AND_ENCLOSURE_DECISION.md` §2). Nothing in the controls architecture changes shape; it is instanced per module and given redundancy at the top.

```mermaid
flowchart TB
  subgraph Hall (3 joined modules, IP66 envelope)
    M1[Module 1 · PLC 1 + Axioline I/O<br/>16 racks, CDU pair, fan wall, VESDA, clean agent]
    M2[Module 2 · PLC 2 + Axioline I/O]
    M3[Module 3 · PLC 3 + Axioline I/O]
    BR1[Border router A · 2 RCPs]
    BR2[Border router B · 2 RCPs]
    BR3[Border router C · 2 RCPs]
    M1 --- BR1
    M2 --- BR2
    M3 --- BR3
  end
  subgraph Power module (separate fire area)
    PPLC[Plant PLC · switchgear, ATS logic supervision,<br/>generator and transformer status, battery-room gas detection, fuel level]
    EA[Edge computer A · OnLogic Karbon 400]
    EB[Edge computer B · OnLogic Karbon 400<br/>active standby, replicated SQLite + broker bridge]
    SWA[Managed switch A] --- SWB[Managed switch B]
  end
  subgraph Plant yard
    MV[MV switch · 2 × 2,500 kVA transformers]
    GEN[3 × 1,250 kW generators · 48 h fuel]
    ADC[Adiabatic dry coolers · water treatment skid]
  end
  M1 & M2 & M3 -->|Modbus TCP / OPC UA, ring| SWA
  PPLC --> SWA
  SWA & SWB --> EA & EB
  BR1 & BR2 & BR3 -->|IPv6| SWA
  MV & GEN & ADC -.hardwired I/O + Modbus.-> PPLC
```

| Rule | BEN 2000 value | Why |
| --- | --- | --- |
| One PLC per module plus a plant PLC | 4 PLCnext AXC F 2152 | A module's interlocks (CDU isolation, leak valves, cooling failover, door/EPO) must not depend on a cable that crosses a module joint; the plant PLC supervises MV, generators, ATS logic in the switchgear, battery-room gas detection and fuel |
| Redundant edge computers | 2 × OnLogic Karbon 400, active/standby, replicated history, VRRP address for the dashboard and API | The hall is NOC-less under BEN Care Managed; the twin, sweeps and the care layer must survive one computer failing or being patched |
| Multiple border routers | 3 border routers (one per module, 2 RCPs each) forming one Thread network with 102 Pods (`derived()["pods"]`) | Thread partitions heal, but the 36.6 m hall and the steel module walls make a single border router a reach and a single-point problem |
| Controls network | Ring of managed switches (MRP/RSTP) between modules and the power module, fibre across module joints | Copper across a joint is a maintenance seam; fibre also helps the H3 shielding and TEMPEST separation |
| Life safety | Per module: VESDA + spot detection + clean agent release panel; hall pre-action option; EPO per module and whole-hall | Same rule as every tier: hardwired, PLC only observes dry contacts |
| Twin and CFD | Twin per module with a shared plant model; CFD per module (`cfd.py` runs the 2-D solver on each module's rack rows) | Keeps the solver small and the fit per module where the sensors are |
| Drawings | Site plan A-000 plus per-module sheets | A hall needs a site plan for the AHJ; a module needs the same sheets a BEN 500 has |

## Components and contracts
| Component | Owns | Interface | Persistence |
| --- | --- | --- | --- |
| `config.py` | Tiers, profiles, climates, sizing rules, validation | `Config`, `derived()` | JSON file per unit |
| `twin.py` | Physics state, faults, alarms, sensor specs | `step()`, `state()`, `inject()` | none (deterministic from config + seed) |
| `cfd.py` | Airflow/temperature fields, recirculation index | `run_cfd()`, `recirculation_profile()` | PNG + metrics JSON |
| `calibration.py` | Fits, tares, uncertainty budgets | `linear_fit()`, `budget()` | cal records (JSON) with `cal_id` |
| `analysis.py` | Parameter fitting, prediction intervals, margins | `fit_params()`, `predict()` | fitted params JSON |
| `sweeps.py` | Test sequences with pass/fail | `run(name, twin)` | CSV per sweep |
| `commissioning.py` | FAT/SAT procedure | CLI | signed Markdown report + CSV hash |
| `api.py` | HTTP/WS surface, ring buffer, background sim | see `spec/INTERFACES.md` | SQLite (edge computer / RevPi), in-memory (demo) |
| `dashboard/static` | UI, 3-D scene, panels | REST + WS | browser only |
| `firmware/ben-pod` (BEN Pod, MGM240P / OpenThread) | Measurement, calibration apply, outputs, buffering, attestation | MQTT per `spec/PROTOCOL.md` over Thread/IPv6 | Secure Vault NVM (cal, ids, device certificate) |
| `firmware/ben-edge` (edge computer / RevPi image) | Broker, OTBR, services, backups, firewall, TPM measured boot | systemd | SQLite + nightly backup |
| PLC project (PLCnext, `firmware/ben-edge/plc`) | Interlocks, cooling failover, leak isolation, watchdog relay, life-safety monitoring | Modbus TCP / OPC UA to the edge computer | PLC retentive memory |

## Trust boundaries
1. Life-safety never crosses into software. The PLC (or RevPi) and the Pods only *observe* dry contacts.
5. Hardware root of trust end to end: every Pod attests at join (Secure Vault High, per-device certificate), every firmware image is signed, the edge computer measures its boot with a TPM; the controls zone has no route to the internet.
2. Controls VLAN has no route to customer IT or to the internet by default.
3. Firmware images are signed; calibration changes carry a `cal_id` and are logged.
4. The dashboard shows a connection indicator that follows a real WebSocket heartbeat and last-step age, never a static green light.

## Failure behaviour
| Failure | Behaviour |
| --- | --- |
| Edge computer down | PLC keeps the interlocks; Pods keep measuring and buffering 1 h; outputs hold or fail safe per table in `design/specs/CONTROLS_SPEC.md`; cooling units run on their own controllers |
| PLC / RevPi down | Watchdog relay drops within 5 s: cooling units fall back to local control (cooling enable is wired fail-ON); edge computer raises the alarm; commissioning proves it (CTP-K2) |
| Pod down or mesh partition | Thread mesh self-heals around a lost router Pod (E13); twin falls back to neighbouring sensors; alarm "sensor loss"; commissioning blocks until fixed |
| Rogue device on the mesh | Join rejected (no valid certificate / attestation); event logged; E12 tests it |
| Utility loss | UPS carries IT; cooling rides through only with the mechanical-UPS option; twin predicts minutes to ASHRAE limit |
| Cooling unit fail | Standby unit starts (N+1/2N); alarm; sweep `cooling_unit_failover` is the acceptance test |
| Leak | Critical alarm; CDU isolates (liquid tiers); procedure in maintenance docs |
| One edge computer down (BEN 2000) | Standby edge computer takes the VRRP address within seconds; history replicated; PLCs unaffected |
| Border router down (BEN 2000) | Pods re-parent to a neighbouring module's border router through router-eligible Pod E units at the joints; alarm "border router loss" |
| Module joint seal failure (BEN 2000) | Leak-rope under each joint and humidity Pods either side raise the alarm; E15 seal test at SAT and after any relocation; procedure in `MAINTENANCE.md` |
| MV transformer or UPS string loss (BEN 2000) | 2N: the other transformer and string carry the full load; generators start on utility loss; E16 transfer test is the acceptance test |
