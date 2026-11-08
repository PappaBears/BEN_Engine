# Roadmap (deferred by decision; separate from what is done)

| Item | Value | Depends on |
| --- | --- | --- |
| Lighthouse build BEN Micro + BEN 20 | Converts simulation-verified claims to hardware-verified | Funding, site |
| ESP32 cross-build in CI with cached toolchain | Firmware verified on target | Network access to Espressif registry or vendored toolchain |
| 3-D CFD (OpenFOAM) for BEN 40 liquid + air hybrid | Absolute temperatures, not relative | Compute, validation data from lighthouse |
| Modbus TCP server / SNMP agent on the gateway for customer BMS | Integration with existing facilities | Register map decision |
| UL 508A listing of controls panel; FCC Part 15 for node carrier | Sellable in most US jurisdictions without exception | Prototype hardware |
| Mechanical UPS sizing tool (cooling ride-through) in selector | Lets customers price the ride-through option explicitly | Vendor data for fan/pump inrush |
| Solar + battery sizing for off-grid profile | Completes the off-grid promise | Irradiance data source |
| Managed-service SOC 2 program | Enterprise and healthcare sales | Ops team |
| Paperclip agent tree per unit (monitor, draft maintenance tickets) | Zero relay work for the operator | Paperclip endpoint |
| Atlas memory of fitted parameters across the fleet | Fleet learning: each commissioning improves the next twin | Atlas endpoint |
