To: Ben@SchreiberAI.com
Subject: RFQ: BEN Pod PCB fabrication + SMT assembly (MGM240P, 4-layer, RTD front end, PoE PD, RS-485), 500 pcs
Supplier: jlcpcb / pcbway or the contract manufacturer (BEN Pod PCBA)
Status: QUEUED — not sent (operator forwards)
Prepared: 2026-11-08

---

Hello,

I am writing from Schreiber AI. We design and build BEN Engine, a family of modular edge data centers (a 5 kW outdoor cabinet, 30 / 150 / 500 kW relocatable modules and a 2 MW prefabricated center). The controls layer is an industrial platform: a PLC or Revolution Pi controller, an industrial edge computer, and our own secure sensing mesh (BEN Mesh) built on Silicon Labs MGM240P Thread modules. We are finalising the bill of materials for a first production run of 10 units and would like to qualify you as a supplier.

**What we need**
4-layer PCB (~90 x 60 mm, ENIG, 1.6 mm, controlled impedance for the RF keep-out and the Ethernet pair) for the BEN Pod v1, with SMT assembly: Silicon Labs MGM240PB32VNA3R module (consigned or sourced), 24-bit RTD front end for 4 x Pt1000 3-wire (ADS124S08 class), SHT45, SDP810 footprint on the room variant, 2 x isolated 4-20 mA inputs (165 ohm 0.1 % shunts), 2 x dry-contact inputs, leak-rope input, pluggable terminal blocks and M12 footprints; the Pod E load option adds LAN8742 Ethernet PHY + magnetics, 802.3af PoE PD controller, isolated RS-485 transceiver and 2 x 10 A relays. We supply Gerbers, BOM and CPL. Secure provisioning (certificate injection into Secure Vault) is done in our own fixture, not at the assembler; we only need the SWD test points exposed and a bed-of-nails-friendly layout.

**Quantities**
- 50 pcs first article / pilot; 500 pcs first production run (two load options, roughly 20 % Pod E); 2,000 pcs annual

**Questions**
1. Price for 50, 500 and 2,000 pcs fab + SMT assembly, Pod W and Pod E load options separately, with the MGM240P consigned and with the MGM240P sourced by you.
2. Conformal coating (silicone, IPC-CC-830) and IPC-A-610 class 2 inspection; AOI and X-ray on the module and QFN parts; functional test fixture support (we supply the test firmware).
3. Impedance control (50 ohm RF trace from module to keep-out, 100 ohm differential Ethernet) and your stack-up for a 4-layer 1.6 mm board.
4. Lead time door-to-door to the US, HS code / tariff handling and whether partial shipments are possible.
5. Price breaks and MOQ for the pluggable terminal blocks, the relays and the PoE magnetics from your parts library versus our approved vendor list.
6. Serial-number / 2D barcode labelling per board (we map board serial to the device certificate at provisioning).
7. Certification support: UL 94 V-0 laminate certificate, RoHS / REACH declarations, and a CE / FCC Part 15 B pre-compliance test report option for the assembled Pod.
8. Drawings: 2D PDF and 3D STEP of the assembled board for enclosure fit; DFM report before the first article.
9. Warranty terms on workmanship and what voids them in an outdoor installation (-40 to +70 C, IP65 outdoor enclosure variant).
10. Freight terms (Incoterms / FOB point), ESD packaging, and consolidated shipment to our provisioning cell per build.

Please reply with a formal quotation valid for 90 days. If you need an NDA or our drawings we can provide them.

Thank you,
Ben Schreiber
Schreiber AI
Ben@SchreiberAI.com
