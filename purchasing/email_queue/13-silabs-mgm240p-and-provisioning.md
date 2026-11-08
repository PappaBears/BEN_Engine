To: Ben@SchreiberAI.com
Subject: RFQ: Silicon Labs MGM240P modules (1,000 pcs), xG24 RCP boards, Custom Part Manufacturing Service for certificate injection, Secure Vault documentation
Supplier: silabs mgm240p and provisioning (Silicon Labs authorised distributor: Mouser / DigiKey / Arrow / Symmetry)
Status: QUEUED — not sent (operator forwards)
Prepared: 2026-11-08

---

Hello,

I am writing from Schreiber AI. We design and build BEN Engine, a family of modular edge data centers (an outdoor 24U cabinet unit and 10 ft / 20 ft / 40 ft high-cube ISO container units from 6 kW to 500 kW IT). The controls layer is an industrial platform: a PLC or Revolution Pi controller, an industrial edge computer, and our own secure sensing mesh (BEN Mesh) built on Silicon Labs MGM240P Thread modules. We are finalising the bill of materials for a first production run of 10 units and would like to qualify you as a supplier.

**What we need**
The BEN Pod (our sensor/IO board, two load options: Pod W wireless and Pod E wired RS-485/Ethernet) uses the MGM240PB32VNA3R Thread/802.15.4 module (EFR32MG24, Secure Vault High, PCB antenna, FCC/IC/CE modular approval). Our border router uses the same radio as an RCP on USB. Each Pod receives a per-device X.509 certificate from Schreiber AI's PKI at provisioning and attests at network join; keys never leave the chip. Distributor prices seen 2026-11-08: Mouser $9.86 (T&R, 2,099 in stock), DigiKey $5.65 at 1,000 (cut tape, 12-week lead on EU sites), Symmetry $11.03.

**Quantities**
- 1,000 pcs MGM240PB32VNA3R for the first Pod production run (10 units x up to 22 Pods + fleet spares + engineering); 5,000 pcs annual forecast
- 20 pcs xG24-EK2703A Explorer Kits (RCP / development) now; production RCP sticks later on our own PCB
- 4 pcs WSTK / Pro Kit with MGM240P radio boards for the firmware team

**Questions**
1. Price at 1,000 and 5,000 pcs, stock position and factory lead time for MGM240PB32VNA3R; is the -PA (external antenna) variant on the same lead time?
2. Silicon Labs Custom Part Manufacturing Service (CPMS): can modules be delivered with our secure boot public key, our certificate chain and the Secure Vault configuration (secure debug lock, anti-rollback, tamper settings) pre-programmed at the factory? Minimum order, NRE, lead time, and what we must supply (keys via HSM, PSA attestation requirements).
3. Secure Vault High documentation set: PSA Certified Level 3 report, secure boot / secure key storage application notes (AN1218, AN1222, AN1247 or current), attestation token format, and the Vault "device identity certificate" provisioning flow.
4. Modular approval documents: FCC grant, ISED certificate, CE RED declaration, and the antenna / host integration conditions we must respect for the Pod enclosure (plastic, metal rack rail nearby) to keep the modular approval.
5. Thread certification: current Thread Group certification of the OpenThread stack on the EFR32MG24 / Gecko SDK version you recommend for production (Simplicity SDK release), and OpenThread Border Router RCP firmware support.
6. Longevity: the published 10-year longevity statement for the MGM240P, and the EFR32MG24 roadmap (MG26 migration path).
7. Industrial temperature: confirm -40 to +85 C grade, and reflow profile / MSL for our contract manufacturer.
8. Price breaks on the xG24-EK2703A Explorer Kits at 20 and 50 pcs, and any volume programme for RCP use.
9. Design support: Silicon Labs FAE review of our Pod RF layout and the PoE PD / RS-485 section for coexistence, and access to the hardware design review service.
10. Freight terms (Incoterms / FOB point), reels per box, and whether you can drop-ship directly to our contract manufacturer in one consolidated shipment per Pod build.

Please reply with a formal quotation valid for 90 days. If you need an NDA or our drawings we can provide them.

Thank you,
Ben Schreiber
Schreiber AI
Ben@SchreiberAI.com
