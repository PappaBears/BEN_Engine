To: Ben@SchreiberAI.com
Subject: RFQ: 12.47 kV service package for a 2 MW center: MV switchgear, 2 x 2,500 kVA pad-mount transformers, 4,000 A 480 V switchgear, 2 MW UPS strings, 3 x 1,250 kW generators
Supplier: Eaton / Schneider Electric / ABB / Vertiv / Generac Industrial / Caterpillar dealer
Status: QUEUED — not sent (operator forwards)
Prepared: 2026-11-08

---

Hello,

I am writing from Schreiber AI. We design, commission and operate BEN Engine, a family of modular edge data centers (a 5 kW outdoor cabinet, 30 / 150 / 500 kW relocatable modules and a 2 MW prefabricated center). For the 2 MW center, BEN 2000, we are sourcing the medium-voltage service and critical power package.

What we need (per center, sized by our configuration model for 1,600 to 2,000 kW IT, total about 1,770 to 2,210 kW)
- MV switchgear: 15 kV class pad-mount or metal-enclosed switchgear with utility and customer sections, two transformer feeders, relaying, for a 12.47 kV (or 13.8 kV) utility service.
- Transformers: 2 x 2,500 kVA pad-mount, 12.47 kV delta to 480Y/277 V, 2N arrangement (4 at 2 MW with 2N); loss-evaluated (DOE 2016 or better), K-factor and harmonic considerations for UPS load.
- 480 V switchgear: 4,000 A main-tie-main, UL 1558 or UL 891, with power monitoring (Modbus TCP) and arc-flash reduction.
- UPS: two 2 MW class modular UPS strings (2N) with lithium batteries for 10 minutes, UL 9540 / 9540A documentation, battery room layout with 2-hour separation per NFPA 855, Modbus TCP / SNMP monitoring.
- Generators: 3 x 1,250 kW diesel (N+1), Level 2 sound-attenuated enclosures, 48-hour sub-base or day tanks with SPCC-compliant containment, paralleling switchgear, NFPA 110 Level 1, EPA Tier 4 or stationary emergency certification.

Quantities
- First center in 2027 H2; forecast 3 to 5 centers per year

Questions
1. Budgetary price and lead time for each line; which items are allocated or over 40 weeks (our schedule model currently carries 48 to 52 weeks for transformers and generators and places them on the critical path).
2. Transformer efficiency class and loss evaluation, and whether a 3,000 kVA pair is preferable for 2 MW at 2N.
3. UPS string topology (number of 250 or 500 kW modules per string, internal N+1), efficiency at 30 to 60 percent load (our typical operating point), eco-mode availability, and battery cabinet count for 10 minutes at 2,000 kW.
4. Generator sizing check with UPS step loads and VFD cooling loads, alternator oversize recommendation, and fuel consumption at 75 percent load.
5. Arc-flash and selective coordination study scope and price for the whole chain (MV through rack PDUs).
6. Factory witness testing for switchgear and UPS, and start-up service pricing (mandatory for warranty?).
7. Monitoring: Modbus TCP / SNMP register maps and MIBs for every item so our BEN Controller can poll them; any software licence implications.
8. Certification documents: UL listings, IEEE C57 transformer test reports, UL 9540A battery reports, EPA certificates, CE where applicable.
9. Drawings: 2D PDF and 3D STEP for the pads and the power module layout; recommended working clearances at 4,000 A per NEC 110.26.
10. Commercial: price breaks at 1 / 3 / 5 centers per year, warranty terms, freight terms (Incoterms / FOB site), and whether the package can be shipped direct to site with a single commissioning crew.

Please reply with a budgetary proposal valid for 90 days.

Thank you,
Ben Schreiber
Schreiber AI
Ben@SchreiberAI.com
