# Purchasing email queue — BEN Engine

One file per supplier question. Each is addressed **To: Ben@SchreiberAI.com** so Ben can review and forward to the supplier; nothing has been sent. Bodies introduce Schreiber AI, state the need and quantities (per unit x 10-unit first run), and ask for price breaks, lead time, availability, UL/CE documents, STEP/2D drawings, Modbus/SNMP maps where relevant, warranty and freight terms. Prepared 2026-11-07.

| # | File | Supplier | Subject | Why it is queued |
|---|---|---|---|---|
| 1 | [01-container-dealer-cascade-containerone.md](email_queue/01-container-dealer-cascade-containerone.md) | container dealer cascade containerone | RFQ: one-trip 10/20/40 ft high-cube ISO containers, 10-unit run (BEN Engine) | Containers are the structural base; 40 ft HC showed backordered; 10 ft HC is rare. |
| 2 | [02-great-lakes-ddb-outdoor-cabinet.md](email_queue/02-great-lakes-ddb-outdoor-cabinet.md) | great lakes ddb outdoor cabinet | RFQ: outdoor NEMA 4 24U cabinet, ~6 kW IT heat load, 10 units (BEN Micro) | Micro enclosure: placeholder cabinet's integral AC is undersized; needs configured quote. |
| 3 | [03-rittal-pfannenberg-cabinet-ac.md](email_queue/03-rittal-pfannenberg-cabinet-ac.md) | rittal pfannenberg cabinet ac | RFQ: 5.8 kW enclosure cooling units (Blue e+ SK 3189.940 / DTS 6x2E), 30 units | 5.8 kW cabinet coolers have 1-2 pcs distributor stock; mounting on a 24U cabinet unproven. |
| 4 | [04-schneider-apc-inrow-and-racks.md](email_queue/04-schneider-apc-inrow-and-racks.md) | schneider apc inrow and racks | RFQ: InRow DX ACRD301S + condensers, NetShelter SX racks, AP8841 PDUs, EPO (BEN 10 / BEN 20) | Largest BEN10/20 cooling + rack spend; condenser part and price unknown. |
| 5 | [05-vertiv-thermal-crv-rdhx-xdu.md](email_queue/05-vertiv-thermal-crv-rdhx-xdu.md) | vertiv thermal crv rdhx xdu | RFQ: Liebert CRV in-row (alternate), CoolLoop RDHx, XDU450 CDU (BEN 20 / BEN 40) | No public pricing for CRV / RDHx / XDU450 (BOM estimates). |
| 6 | [06-coolit-motivair-cdu-manifolds.md](email_queue/06-coolit-motivair-cdu-manifolds.md) | coolit motivair cdu manifolds | RFQ: CHx750 row CDU, rack manifolds and QD hose kits for 48U GPU racks (BEN 40) | CDU and manifolds are the largest BEN 40 estimate ($345k). |
| 7 | [07-guntner-alfa-laval-dry-cooler.md](email_queue/07-guntner-alfa-laval-dry-cooler.md) | guntner alfa laval dry cooler | RFQ: outdoor dry coolers 120 kW and 230 kW, glycol, EC fans, adiabatic-ready (BEN 20 / BEN 40) | Dry cooler is estimate only ($110/kW). |
| 8 | [08-eaton-93pm-ups.md](email_queue/08-eaton-93pm-ups.md) | eaton 93pm ups | RFQ: 93PM 50 kW UPS, 208 V, internal batteries, N+1 pair (BEN 10) | BEN 10 UPS is ~16% of its BOM; AVENDOR stock at 0 on several SKUs. |
| 9 | [09-schneider-galaxy-vs-lithium.md](email_queue/09-schneider-galaxy-vs-lithium.md) | schneider galaxy vs lithium | RFQ: Galaxy VS 100 kW 480 V UPS + Galaxy Lithium-ion battery cabinets (BEN 20 / BEN 40) | Galaxy VS + Li-ion cabinets are ~$190k-470k per unit; right-sizing needed. |
| 10 | [10-asco-generac-ats-generator.md](email_queue/10-asco-generac-ats-generator.md) | asco generac ats generator | RFQ: Series 300 ATS (200 A / 400 A, NEMA 3R, SE-rated) and SD150 / SD250 diesel gensets (generator option) | Generator option is dealer-quote only. |
| 11 | [11-fike-kidde-clean-agent.md](email_queue/11-fike-kidde-clean-agent.md) | fike kidde clean agent | RFQ: pre-engineered FK-5-1-12 (Novec 1230) clean agent systems for 10/20/40 ft containers (design-build) | Fire suppression is quote-only and AHJ-dependent. |
| 12 | [12-supermicro-reseller-gpu-servers.md](email_queue/12-supermicro-reseller-gpu-servers.md) | supermicro reseller gpu servers | RFQ: SYS-821GE-TNHR (8x H100) and SYS-421GE-TNRT (8x L40S) reference compute, 100GbE switching | Compute dominates BOM value; allocation and liquid-cooled variants. |
| 13 | [13-olimex-esp32-poe-iso.md](email_queue/13-olimex-esp32-poe-iso.md) | olimex esp32 poe iso | RFQ: ESP32-POE-ISO-EA (industrial temp) boards, 100 pcs, for BEN Node controls carrier | Node MCU: spotty stock; -IND variant 12 wk lead. |
| 14 | [14-jlcpcb-node-carrier-pcb.md](email_queue/14-jlcpcb-node-carrier-pcb.md) | jlcpcb node carrier pcb | RFQ: BEN Node carrier PCB fabrication + SMT assembly, 100 pcs | Make item: carrier PCB price is an estimate. |
| 15 | [15-local-site-civil-electrical.md](email_queue/15-local-site-civil-electrical.md) | local site civil electrical | RFQ: site civil & electrical package per BEN unit (pad, service, grounding, fiber), regional pricing | SITE- lines are regional estimates; utility lead time is the critical path. |

Gmail drafts: all 16 created on 2026-11-07/08 in the schreibears@gmail.com account, addressed to Ben@SchreiberAI.com, nothing sent. Each draft carries a header line naming the supplier to forward to and the source file.

| 16 | Contract manufacturer RFI (shortlist in docs/MANUFACTURING_STRATEGY.md §3.1) | `16-contract-manufacturer-rfi.md` | queued |
