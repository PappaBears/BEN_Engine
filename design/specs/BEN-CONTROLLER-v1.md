# BEN Gateway v1 — specification sheet

**Schreiber AI · BEN Engine controls module · IFC Rev A · 2026-11-07**
One per BEN unit. Runs the broker, the time source, the `ben_engine` API with digital twin and history, and the dashboard. Status: software package written (`firmware/ben-gateway`), **unverified on hardware**.

| | |
| --- | --- |
| **Part number** | BEN-GW-V1 |
| **Compute** | Raspberry Pi 5, 8 GB, active cooler, in DIN-rail metal case; official 27 W USB-C PSU **or** industrial 24 VDC → 5 V/5 A DIN converter (preferred: fed from the controls UPS circuit) |
| **Storage** | 256 GB NVMe via M.2 HAT (industrial grade, pSLC) for OS + SQLite; USB-A 32 GB industrial stick for nightly backups (or NAS) |
| **Network** | on-board 1 GbE → controls switch trunk (VLAN 20 untagged = controls, VLAN 30 tagged = management). Optional USB 3 GbE adapter = WAN uplink (off by default) |
| **Serial** | USB RS-485 isolated adapter (Modbus RTU to power meters / UPS when they lack Ethernet); USB console cable for node provisioning |
| **Time** | chrony; sources: upstream NTP (if WAN/VPN), optional GPS/PPS HAT (`refclock` lines ready), else orphan stratum 10 — unit always has one agreed clock |
| **OS** | Raspberry Pi OS Lite 64-bit (Debian 12), unattended security updates only when WAN is enabled |
| **Software** | Mosquitto 2.x (3 listeners: 1883 plain on controls VLAN, 8883 TLS + 9001 WSS on management), `ben_engine.api` (FastAPI/uvicorn) as systemd service, SQLite history with 400-day retention, nightly consistent backup, nftables default-drop firewall, optional outbound-only WireGuard support tunnel |
| **Protocols polled** | Modbus TCP (meters, UPS, cooling, CDU), Modbus RTU over RS-485, SNMP v2c/v3 (rack PDUs, UPS network cards); normalised to `ben/<unit>/equip/<id>/telemetry` |
| **Capacity** | sized for 16 nodes at 1 Hz + 20 equipment pollers at 0.1–1 Hz ≈ 25 msg/s, ~2 GB/yr SQLite at full channel count; Pi 5 idles ≈ 8 % CPU in that load (**estimate**) |
| **Power** | 6–12 W typical, 27 W max |
| **Environment** | 0…+45 °C ambient at the mechanical panel (Pi 5 throttles above 80 °C SoC); 5–95 %RH non-condensing; IP20 in panel |
| **Enclosure** | DIN-rail aluminium case 115 × 95 × 40 mm plus HAT; mounted in the controls section of the mechanical panel beside the PoE switch |
| **Zones** | controls VLAN (nodes, equipment) · management VLAN (dashboard, laptop) · customer IT: **no interface** · WAN: nothing inbound, ever |
| **Backup/restore** | `.backup` + integrity check + sha256 nightly 02:17 to USB/NAS, 30 copies kept; restore = copy file, restart service. Code recovered from git separately. |
| **Security** | per-node MQTT credentials + ACL (a node can only write its own topics), local CA for TLS listeners, SSH keys only, nothing listens on WAN, VPN is customer-switched with 48 h auto-off, SQLite + reports on encrypted NVMe (LUKS, key in TPM-less Pi → key on USB at boot or passphrase at commissioning; **decision recorded as reversible in PROJECT_NOTES**) |
| **Reliability** | COTS Pi 5 MTBF not published; design assumes **single gateway, no automatic failover**: nodes buffer 1 h and keep cooling on local control; a cold-spare gateway image (SD/NVMe clone) ships with every BEN 20/40, restore time < 30 min with the nightly backup |
| **Physical I/O** | none — the gateway has no field I/O on purpose; everything goes through nodes or equipment protocols |
| **Indicators** | Pi power/activity LEDs; dashboard "unit heartbeat" banner; status topic for each node retained |
