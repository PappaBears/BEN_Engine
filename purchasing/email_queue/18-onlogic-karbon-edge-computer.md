To: Ben@SchreiberAI.com
Subject: RFQ: OnLogic Karbon 400 (K410) edge computers with TPM 2.0, 10 + 2 units; Karbon 300 option for BEN Controls Lite
Supplier: onlogic karbon edge computer (OnLogic, South Burlington VT)
Status: QUEUED — not sent (operator forwards)
Prepared: 2026-11-08

---

Hello,

I am writing from Schreiber AI. We design and build BEN Engine, a family of modular edge data centers (an outdoor 24U cabinet unit and 10 ft / 20 ft / 40 ft high-cube ISO container units from 6 kW to 500 kW IT). The controls layer is an industrial platform: a PLC or Revolution Pi controller, an industrial edge computer, and our own secure sensing mesh (BEN Mesh) built on Silicon Labs MGM240P Thread modules. We are finalising the bill of materials for a first production run of 10 units and would like to qualify you as a supplier.

**What we need**
One Karbon 400 series (K410) per BEN 20 / BEN 40 unit (and per BEN 10 on the Pro controls tier) as the edge computer inside our UL 508A BEN Controller panel: Intel Atom x6425E, 16 GB, 256 GB NVMe (industrial grade), TPM 2.0 enabled, 2 x LAN, 1 x RS-485/232, DIN-rail mount, -40 to +70 C, 24 VDC input, Ubuntu LTS pre-installed (or bare). It runs ben_engine (API, digital twin, commissioning, local database), the MQTT broker and the OpenThread Border Router with one or two MGM240P RCP radios on USB. We could find no public list price for the K410 (your store is configure-to-order); please quote.

**Quantities**
- 10 + 2 spare K410 for the first run; 50 annual forecast
- Option: Karbon 300 (K300) class as the compact edge computer for the BEN Controls Lite tier if the Revolution Pi route is not adopted — 10 units, same accessories

**Questions**
1. Configured price at 12 and 50 units for the K410 above, with and without the pre-installed OS; lead time and your build-to-order schedule.
2. TPM 2.0: discrete TPM part number and firmware version, measured boot / UEFI Secure Boot support with our own keys (custom PK/KEK/db enrolment), and whether OnLogic can enrol our keys at the factory.
3. Industrial storage: NVMe options with power-loss protection and endurance (TBW) ratings; SSD encryption with the TPM.
4. Certifications: UL 62368-1 listing, CE, FCC Part 15 B; Class I Division 2 option; vibration/shock (MIL-STD-810) data; the certificates we can attach to our compliance file.
5. Environmental: fanless operation at 24 VDC inside a NEMA 12 panel at up to 50 C internal; derating curves; DIN-rail kit part number.
6. Longevity: product life commitment for the K410 (Elkhart Lake) and the migration path (Karbon 420 / 520) with the same mounting and I/O.
7. Imaging and OEM services: pre-loading our disk image, asset tags / serial reporting (we map serial to the TPM EK certificate), and OEM branding options for white-label units.
8. Price breaks at 12 / 25 / 50 units, and extended warranty (3 / 5 years) and advance-replacement terms.
9. Drawings: 2D PDF and 3D STEP for the panel layout.
10. Freight terms (Incoterms / FOB point), and whether units can ship directly to our UL 508A panel shop in one kit per panel.

Please reply with a formal quotation valid for 90 days. If you need an NDA or our drawings we can provide them.

Thank you,
Ben Schreiber
Schreiber AI
Ben@SchreiberAI.com
