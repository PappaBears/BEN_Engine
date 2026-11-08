# Roadmap (deferred by decision; separate from what is done)

| Item | Value | Depends on |
| --- | --- | --- |
| Lighthouse build BEN 5 + BEN 150 | Converts simulation-verified claims to hardware-verified | Funding, site |
| EFR32MG24 / Gecko SDK cross-build in CI with a vendored toolchain; OpenThread integration test on two xG24 kits | BEN Pod firmware verified on target | Vendored Simplicity SDK; two Explorer Kits |
| Secure provisioning cell: PKI issuing CA, J-Link fixture, Secure Vault certificate injection, attestation check in the commissioning script (CTQ-K5) | Every Pod attests; rogue join rejected (E12) | First Pod PCBAs (email 14), HSM token |
| PLCnext project for the AXC F 2152 (interlocks, failover, watchdog relay) and the RevPi equivalent for BEN Controls Lite; OPC UA / Modbus map to the edge computer | PLC watchdog proven (CTP-K2) | One PLC starter kit, one RevPi Connect 4 |
| Dashboard mesh health panel (topology, parent, link quality, attestation, battery) and E13 heal-time report | Mesh resilience visible and testable | Pod firmware status fields |
| 3-D CFD (OpenFOAM) for BEN 500 liquid + air hybrid | Absolute temperatures, not relative | Compute, validation data from lighthouse |
| Modbus TCP server / SNMP agent on the edge computer for customer BMS | Integration with existing facilities | Register map decision |
| UL 508A listing of the BEN Controller panel through the panel partner (email 17); FCC Part 15 B SDoC for the assembled Pod (modular approval covers the radio) | Sellable in most US jurisdictions without exception | Prototype hardware; panel partner |
| Mechanical UPS sizing tool (cooling ride-through) in selector | Lets customers price the ride-through option explicitly | Vendor data for fan/pump inrush |
| Solar + battery sizing for off-grid profile | Completes the off-grid promise | Irradiance data source |
| Managed-service SOC 2 program | Enterprise and healthcare sales | Ops team |
| Paperclip agent tree per unit (monitor, draft maintenance tickets) | Zero relay work for the operator | Paperclip endpoint |
| Atlas memory of fitted parameters across the fleet | Fleet learning: each commissioning improves the next twin | Atlas endpoint |
