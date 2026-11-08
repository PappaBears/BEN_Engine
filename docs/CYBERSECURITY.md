# BEN Engine — Cybersecurity for the Controls Layer

**Owner:** Schreiber AI engineering. **Scope:** the BEN controls layer (nodes, gateway, controls LAN, dashboard, remote support). The customer's IT inside the racks is out of scope — it is theirs — except for the network boundary we give it. **Standard basis:** IEC 62443-3-3 (system), 62443-4-2 (components), 62443-2-4 (integrator practices), NIST SP 800-82 as informative; target **Security Level 2** (protection against intentional, low-resource attacks) for the controls zones.

## 1. Zones and conduits

| Zone | What is in it | Trust | Conduits (allowed traffic) |
| --- | --- | --- | --- |
| **Z0 Life safety (hardwired)** | Fire releasing panel, detectors, HVAC shutdown relay, EPO | Highest; not networked | None. The node reads dry contacts only (`PROTOCOL.md` safety rules). No network path can disable fire protection or EPO |
| **Z1 Controls LAN** | BEN Nodes (ESP32-S3), gateway (Raspberry Pi 5), managed PoE switch, cooling unit controllers, UPS and PDU management ports, power meter, door controller | High | Node ↔ gateway: MQTT over TLS (8883) with per-node client certificates. Gateway → equipment: Modbus TCP (502) / SNMP v3 (161) initiated by the gateway only. VLAN per device class (nodes, vendor equipment) with ACLs on the switch |
| **Z2 Management / dashboard** | Dashboard served by the gateway (HTTPS 443), operator laptops when plugged into the controls panel port | Medium | Browser → gateway HTTPS only; operator accounts with roles (view / operate / admin); no direct access from Z2 to Z1 devices |
| **Z3 Customer IT / enterprise** | Customer's servers, their LAN, their monitoring (SNMP/syslog receivers) | Customer-controlled | Only **outbound from the gateway**: alarm forwarding (SNMP trap/syslog/webhook) to customer systems; optional read-only API (HTTPS) for customer dashboards. Firewall between Z1/Z2 and Z3 is a hard requirement — Schreiber AI supplies it in the controls panel; the customer may substitute their own |
| **Z4 Remote support (Schreiber AI)** | Schreiber AI operations centre | External | **Outbound-only** from the gateway: WireGuard tunnel to Schreiber AI, initiated by the gateway, certificate-pinned; can be disabled by a physical key switch on the controls panel and in software (air-gap mode). No inbound ports anywhere |

Everything the unit needs to run — control logic, alarms, twin, dashboard, data storage — lives on the gateway inside the container. **There is no cloud dependency.** If every external link is cut, the unit runs, alarms locally (horn/strobe and dashboard), and buffers data.

## 2. Component requirements (62443-4-2 mapped to our hardware)

| Requirement | Node (ESP32-S3) | Gateway (Pi 5) | Vendor devices (UPS, cooling, PDU, meter) |
| --- | --- | --- | --- |
| Identification & authentication | Per-node X.509 client certificate in NVS, issued at factory; MQTT username = node_id | OS accounts with SSH keys only; dashboard accounts with password + TOTP for admin | Default credentials changed at FAT (E12); SNMP v3 or disabled; vendor web UIs HTTPS or disabled |
| Use control | Nodes accept `cmd` only from the gateway's certificate; `ota`, `set_cal`, `reboot` require admin role at the gateway | Role-based: view / operate (acknowledge, I/O test) / admin (setpoints, calibration, firmware) | Write access via Modbus restricted to the gateway's IP by switch ACL; read-only where the vendor allows |
| System integrity | **Signed firmware**: images signed with Schreiber AI's Ed25519 key; bootloader verifies before flashing; secure boot and flash encryption enabled on production ESP32-S3; `ota` requires `sha256` and signature; unsigned image rejected and logged (E12) | Read-only root filesystem with A/B images; signed OS updates; dm-verity; measured in the weekly hash check | Firmware updates only through the vendor's signed process, applied by Schreiber AI during maintenance windows |
| Data confidentiality | TLS 1.2+ on MQTT; no plaintext | TLS on all services; database encrypted at rest (LUKS on SSD) | Modbus is plaintext by design → confined to its VLAN; SNMP v3 authPriv |
| Restricted data flow | Node talks only to the broker | Firewall (nftables) default-deny; documented allow-list | ACLs on the managed switch |
| Timely response to events | `status` every 10 s; `errors[]` reported | Security log (auth failures, firmware checks, config changes) to local store and, if enabled, to customer SIEM; weekly review in `MAINTENANCE.md` | Alarms polled and normalised |
| Resource availability | 1 h ring buffer on gateway loss; outputs to last state or `failsafe` | Watchdog; A/B boot; nightly database backup to customer storage if provided and to the local SSD; restore tested at SAT | Equipment runs standalone on its own controller if the gateway is lost (cooling never depends on the gateway to stay on) |

## 3. Allowed services (the list E12 scans against)

| Device | Port / protocol | Direction | Purpose |
| --- | --- | --- | --- |
| Gateway | 8883/TCP MQTT TLS | Z1 → gateway | Node telemetry/commands |
| Gateway | 443/TCP HTTPS | Z2 → gateway; Z3 → gateway (read-only API, optional) | Dashboard, API |
| Gateway | 22/TCP SSH (keys only, admin VLAN only; may be disabled) | Z2 admin → gateway | Maintenance |
| Gateway | 51820/UDP WireGuard | gateway → Z4 (outbound only) | Remote support (optional) |
| Gateway | 123/UDP SNTP | gateway → customer NTP or GPS | Time |
| Vendor devices | 502/TCP Modbus, 161/UDP SNMP v3 | gateway → device only | Polling |
| Nodes | none listening (MQTT client only; no web server, no telnet, Wi-Fi off) | — | — |
| Door controller / camera | 443/TCP to gateway only | Z1 | Access events, video to local storage |

Anything else found open is a defect.

## 4. Local-first data and customer ownership

- All telemetry, alarms, calibration records, commissioning reports and video are stored on the gateway and belong to **the customer**. Export is available at any time as CSV (`GET /api/export.csv`) and as a full database dump; the formats are documented in `spec/PROTOCOL.md` and `spec/INTERFACES.md`.
- Schreiber AI receives data only under the managed-service agreement (through the Z4 tunnel) and uses it for operating the unit and for anonymised fleet statistics (model improvement). The customer can revoke this by disabling Z4; the unit keeps working.
- Retention defaults: telemetry 1 Hz for 90 days, 1-minute aggregates for 10 years, alarms and security logs 10 years, video 30 days. All configurable.
- Data recovery is separate from code recovery: the gateway database has its own nightly backup job to a customer-supplied target (SMB/NFS/S3-compatible) or to a second SSD in the controls panel; restore is tested at SAT (`TURNOVER.md` G2).
- Decommissioning: NIST SP 800-88 purge of the gateway SSD, certificate revocation for the unit, record in the decommission report.

## 5. Patching and vulnerability handling

| Item | Practice |
| --- | --- |
| Node firmware | Released as signed images; changes logged with SHA-256; applied by OTA from the gateway during an agreed window; A/B slots with automatic rollback if the node fails to report healthy within 5 min |
| Gateway OS and `ben_engine` | Monthly security roll-up (or sooner for critical CVEs), staged: twin → Schreiber AI lab unit → customer units in waves; A/B image, automatic rollback |
| Vendor equipment firmware | Reviewed quarterly; applied during maintenance by Schreiber AI or the vendor; recorded |
| Vulnerability intake | security@schreiberai.com; coordinated disclosure within 90 days; customers notified within 72 h of a confirmed exploitable issue affecting their units |
| SBOM | Software bill of materials (SPDX) for the gateway image and firmware delivered with each release and in the turnover package |
| Certificates | Node and gateway certificates valid 5 years; expiry tracked in the dashboard with 90-day warning; re-issue procedure in the O&M manual |

## 6. Remote support path (managed service)

1. The gateway opens a WireGuard tunnel **outbound** to Schreiber AI's operations endpoint (certificate-pinned, keys rotated yearly). Nothing listens for inbound connections at the site.
2. Within the tunnel, Schreiber AI engineers reach the dashboard and SSH (key + hardware token) under named accounts; every session is logged locally and at Schreiber AI; the customer can watch sessions live in the dashboard and can revoke access at any time.
3. The physical key switch on the controls panel ("REMOTE SUPPORT ENABLED / DISABLED") breaks the tunnel; its state is shown on the dashboard and in `status`. Air-gapped sites (public_sector, some healthcare) leave it disabled; support is then by on-site visit or by the customer exporting diagnostics.
4. Firmware and OS updates in managed mode travel through the tunnel but are still signed and verified at the device — the tunnel is transport, not trust.

## 7. White-label implications

| Topic | Rule |
| --- | --- |
| Signing keys | The firmware signing key stays with Schreiber AI unless the partner takes the full source licence and operates their own signing infrastructure; then **their** key is provisioned at the factory and we cannot push firmware to their units. Mixed fleets are not allowed on one gateway |
| Branding | Dashboard theme and names come from `web/kit/brand.json`-style partner files; security logs and certificates still identify the manufacturer (Schreiber AI) for traceability |
| Remote support | Partner may run the Z4 endpoint themselves or contract Schreiber AI; the choice is recorded in the SLA and in the gateway config; a unit never has two remote endpoints |
| Vulnerability disclosure | Flows to the partner and to Schreiber AI simultaneously; the partner owns customer notification |
| Source escrow | Hardware-only and white-label customers get source escrow for the controls layer, released on defined triggers (insolvency, end of support) so the "no cloud dependency" promise survives Schreiber AI |
| Compliance packs | HIPAA, PCI, CMMC mappings are delivered as templates; the partner is responsible for their own attestation |

## 8. What we do not claim

- No certification to IEC 62443 yet; the architecture is designed to SL 2 and can be assessed on request.
- No FIPS 140-3 validation of the crypto modules by default; available as an option for public-sector units.
- No guarantee against a compromised customer network reaching Z3 services we expose on request (read-only API); the firewall rules we ship are the minimum, and customer changes to them are the customer's responsibility.
- The controls layer does not protect the customer's IT workloads; it protects the room they run in.
