# Paperwork ready set — generated 2026-11-08 (template rev 9fed473)

Schreiber AI's side and every policy number are filled; counterparty identity, addresses, dates and counsel choices stay as `[FIELD]` until known. Templates are not legal advice; counsel reviews before signature (`docs/contracts/README.md` §7). Regenerate with `python scripts/prepare_paperwork.py` after editing `purchasing/counterparties.json`.

## Signing sequence

1. **NDA first**, before any drawing, BOM or configuration leaves Schreiber AI (send with the RFQ reply, not the RFQ).
2. **Suppliers**: Purchase Order Terms (`SUPPLIER-TERMS-master.md`) referenced on every PO; delivery liquidated damages 0.5 %/week, cap 10 %, grace 5 days.
3. **Contract manufacturer**: `CMA-master.md` after the site audit and before the first-article build order; LDs 0.5 %/week, cap 10 %, grace 7 days.
4. **Integrators / white-label**: `INTEGRATOR-master.md` plus the software licence.
5. **Customers**: `MSA-master.md` once, then one SOW per unit from the proposal generator; change orders; acceptance certificates; SLA for managed units.
6. Every counterparty NDA/agreement ID is logged in `docs/contracts/ready/INDEX.md` (this file) and the customer deal in the proposal package MANIFEST.

## Counterparties

| Counterparty | Role | RFQ | NDA file | Agreements to follow | Fields still open |
| --- | --- | --- | --- | --- | --- |
| Container dealers: Cascade Containers / ContainerOne / Midstate | supplier | 01 | `NDA-container-dealers-cascade-containers-containeron.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Great Lakes Case & Cabinet / DDB Unlimited | supplier | 02 | `NDA-great-lakes-case-cabinet-ddb-unlimited.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Rittal North America / Pfannenberg USA | supplier | 03 | `NDA-rittal-north-america-pfannenberg-usa.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Schneider Electric (APC) partner | supplier | 04 | `NDA-schneider-electric-apc-partner.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Vertiv | supplier | 05 | `NDA-vertiv.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| CoolIT Systems / Motivair | supplier | 06 | `NDA-coolit-systems-motivair.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Güntner US / Alfa Laval | supplier | 07 | `NDA-g-ntner-us-alfa-laval.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Eaton | supplier | 08 | `NDA-eaton.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Schneider Electric (Galaxy VS, lithium) | supplier | 09 | `NDA-schneider-electric-galaxy-vs-lithium.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| ASCO Power / Generac Industrial dealer | supplier | 10 | `NDA-asco-power-generac-industrial-dealer.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Fike / Kidde Fire Systems distributor | supplier | 11 | `NDA-fike-kidde-fire-systems-distributor.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Supermicro authorised reseller | supplier | 12 | `NDA-supermicro-authorised-reseller.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Silicon Labs / authorised distributor | supplier | 13 | `NDA-silicon-labs-authorised-distributor.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| JLCPCB / PCBWay or contract electronics manufacturer | supplier | 14 | `NDA-jlcpcb-pcbway-or-contract-electronics-manufactur.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Local site civil and electrical contractor | site contractor | 15 | `NDA-local-site-civil-and-electrical-contractor.md` | SUPPLIER-TERMS (PO terms), site subcontract (counsel) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Contract manufacturer (container modification / skid builder) | contract manufacturer | 16 | `NDA-contract-manufacturer-container-modification-ski.md` | CMA, SUPPLIER-TERMS (quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Phoenix Contact USA and UL 508A panel shop | supplier | 17 | `NDA-phoenix-contact-usa-and-ul-508a-panel-shop.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| OnLogic | supplier | 18 | `NDA-onlogic.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Modular building manufacturer (BEN 2000) | contract manufacturer (modular building) | 19 | `NDA-modular-building-manufacturer-ben-2000.md` | CMA, SUPPLIER-TERMS (quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| MV / critical power package vendor (Eaton, Schneider, ABB, Vertiv, Generac, Caterpillar dealer) | supplier | 20 | `NDA-mv-critical-power-package-vendor-eaton-schneider.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| Hardening vendors (ballistic, forced-entry, HEMP shielding, coatings) | supplier | 21 | `NDA-hardening-vendors-ballistic-forced-entry-hemp-sh.md` | SUPPLIER-TERMS (PO terms + quality requirements) | 14: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME, COUNTERPARTY_SIGNATORY_TITLE… |
| [Integrator / white-label partner] | integrator |  | `NDA-integrator-white-label-partner.md` | INTEGRATOR, SOFTWARE-LICENSE, SLA (wholesale) | 15: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NAME, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME… |
| [Customer] | customer |  | `NDA-customer.md` | MSA, SOW per unit, SOFTWARE-LICENSE, WARRANTY, SLA (managed) | 15: COUNTERPARTY_ADDRESS, COUNTERPARTY_ENTITY_TYPE, COUNTERPARTY_NAME, COUNTERPARTY_NOTICE_EMAIL, COUNTERPARTY_NOTICE_NAME, COUNTERPARTY_SIGNATORY_NAME… |

## Masters (Schreiber AI side filled)

| File | Source template | Fields still open |
| --- | --- | --- |
| `MSA-master.md` | `MSA.md` | 51 |
| `INTEGRATOR-master.md` | `INTEGRATOR_AGREEMENT.md` | 56 |
| `CMA-master.md` | `CONTRACT_MANUFACTURING_AGREEMENT.md` | 74 |
| `SUPPLIER-TERMS-master.md` | `SUPPLIER_TERMS.md` | 19 |
| `SLA-master.md` | `MANAGED_SERVICES_SLA.md` | 57 |
| `SOFTWARE-LICENSE-master.md` | `SOFTWARE_LICENSE_BEN_CONTROLS.md` | 25 |
| `WARRANTY-master.md` | `WARRANTY_TERMS.md` | 51 |
