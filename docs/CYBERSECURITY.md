# BEN Engine — Cybersecurity for the Controls Layer

**Owner:** Schreiber AI engineering. **Scope:** the BEN controls layer (BEN Pods on BEN Mesh, the PLC or RevPi, the edge computer, controls LAN, dashboard, remote support). The customer's IT inside the racks is out of scope — it is theirs — except for the network boundary we give it. **Standard basis:** IEC 62443-3-3 (system), 62443-4-2 (components), 62443-2-4 (integrator practices), NIST SP 800-82 as informative; the PLCnext platform carries an IEC 62443-4-1 certified development process and the Pod silicon is PSA Certified Level 3 (Secure Vault High); target **Security Level 2** (protection against intentional, low-resource attacks) for the controls zones.

## 1. Zones and conduits

| Zone | What is in it | Trust | Conduits (allowed traffic) |
| --- | --- | --- | --- |
| **Z0 Life safety (hardwired)** | Fire releasing panel, detectors, HVAC shutdown relay, EPO | Highest; not networked | None. The PLC (or RevPi) and the room Pod read dry contacts only (`PROTOCOL.md` safety rules). No network path can disable fire protection or EPO |
| **Z1a PLC (control)** | PLCnext AXC F 2152 + Axioline F I/O (Pro) or RevPi Connect 4 + DIO/AIO (Lite); interlocks, failover, watchdog relay; wired transmitters | Highest networked zone | PLC ↔ edge computer: Modbus TCP / OPC UA on the panel switch only; PLC web UI disabled or HTTPS with certificate; no route beyond the panel switch |
| **Z1b Edge computer** | OnLogic Karbon 400 (TPM 2.0, measured boot, LUKS) or the RevPi on Lite: Mosquitto, `ben_engine`, SQLite, OpenThread Border Router with MGM240P RCPs | High | Pod ↔ broker: MQTT over TLS (8883) with per-Pod client certificates over Thread/IPv6; edge → equipment: Modbus TCP (502) / SNMP v3 (161) initiated by the edge computer only |
| **Z1c BEN Mesh (Thread network)** | BEN Pods W and E (MGM240P, Secure Vault High), border router RCPs | High | Thread network key held in Secure Vault; join only through commissioner with per-device credentials (DTLS); a device without a valid Schreiber AI certificate and attestation token is rejected at join and logged; Pod E RS-485 Modbus RTU to the PLC is point to point |
| **Z1d Vendor equipment VLAN** | Managed switch (FL SWITCH 2008 / Moxa), cooling unit controllers, UPS and PDU management ports, power meter, door controller | Medium-high | VLAN per device class with ACLs on the switch; polled by the edge computer only |
| **Z2 Management / dashboard** | Dashboard served by the edge computer (HTTPS 443), operator laptops when plugged into the controls panel port | Medium | Browser → edge computer HTTPS only; operator accounts with roles (view / operate / admin); no direct access from Z2 to Z1 devices |
| **Z3 Customer IT / enterprise** | Customer's servers, their LAN, their monitoring (SNMP/syslog receivers) | Customer-controlled | Only **outbound from the edge computer**: alarm forwarding (SNMP trap/syslog/webhook) to customer systems; optional read-only API (HTTPS) for customer dashboards. Firewall between Z1/Z2 and Z3 is a hard requirement — Schreiber AI supplies it in the controls panel; the customer may substitute their own |
| **Z4 Remote support (Schreiber AI)** | Schreiber AI operations centre | External | **Outbound-only** from the edge computer: WireGuard tunnel to Schreiber AI, initiated by the edge computer, certificate-pinned; can be disabled by a physical key switch on the controls panel and in software (air-gap mode). No inbound ports anywhere |

Everything the unit needs to run — control logic, alarms, twin, dashboard, data storage — lives on the PLC and the edge computer inside the container. **There is no cloud dependency.** If every external link is cut, the unit runs, alarms locally (horn/strobe and dashboard), and buffers data.

## 2. Component requirements (62443-4-2 mapped to our hardware)

| Requirement | BEN Pod (MGM240P, Secure Vault High) | PLC (PLCnext AXC F 2152) / RevPi Connect 4 | Edge computer (Karbon 400, TPM 2.0) | Vendor devices (UPS, cooling, PDU, meter) |
| --- | --- | --- | --- | --- |
| Identification & authentication | Per-Pod X.509 device certificate issued by Schreiber AI's PKI at the factory provisioning cell and written into Secure Vault; private key generated on-chip, never exported; **attestation token** (PSA) checked at Thread join and at broker connect; MQTT username = node_id | PLCnext: user management with certificates, 62443-4-1 certified development process; RevPi: OS accounts with SSH keys only | UEFI Secure Boot with Schreiber AI keys; **TPM 2.0 measured boot** (PCRs sealed to the LUKS key: a modified image does not unlock the database); OS accounts with SSH keys only; dashboard accounts with password + TOTP for admin | Default credentials changed at FAT (E12); SNMP v3 or disabled; vendor web UIs HTTPS or disabled |
| Use control | Pods accept `cmd` only from the broker's certificate; `ota`, `set_cal`, `reboot` require admin role at the edge computer | Interlock logic changes only through a signed PLC project download under change control; PLC web UI disabled in production | Role-based: view / operate (acknowledge, I/O test) / admin (setpoints, calibration, firmware) | Write access via Modbus restricted to the edge computer's IP by switch ACL; read-only where the vendor allows |
| System integrity | **Signed firmware**: ECDSA P-256 (Secure Vault) with anti-rollback; Gecko bootloader verifies before flashing; secure debug locked; tamper detection events logged; `ota` requires `sha256` and signature; unsigned image rejected and logged (E12) | Signed PLC firmware from Phoenix Contact; project checksum recorded in the FAT report | Read-only root filesystem with A/B images; signed OS updates; dm-verity; TPM PCR baseline recorded at FAT and checked weekly | Firmware updates only through the vendor's signed process, applied by Schreiber AI during maintenance windows |
| Data confidentiality | DTLS at Thread join; TLS 1.2+ on MQTT; Thread network key in Secure Vault | Modbus TCP to the edge computer only on the panel switch | TLS on all services; database encrypted at rest (LUKS, key sealed in the TPM) | Modbus is plaintext by design → confined to its VLAN; SNMP v3 authPriv |
| Restricted data flow | Pod talks only to the broker (and Pod E to the PLC on RS-485) | No route beyond the panel switch | Firewall (nftables) default-deny; documented allow-list | ACLs on the managed switch |
| Timely response to events | `status` every 10 s with mesh health (parent, link quality, attestation state); `errors[]` reported | Watchdog relay; diagnostic log | Security log (auth failures, firmware checks, join rejections, config changes) to local store and, if enabled, to customer SIEM; weekly review in `MAINTENANCE.md` | Alarms polled and normalised |
| Resource availability | 1 h ring buffer on broker loss; outputs to last state or `failsafe`; mesh self-heals around a lost router Pod (E13) | Runs the interlocks with the edge computer down; watchdog relay drops to local control if the PLC itself stops (CTP-K2) | Watchdog; A/B boot; nightly database backup to customer storage if provided and to the local SSD; restore tested at SAT | Equipment runs standalone on its own controller if the controller is lost (cooling never depends on software to stay on) |

### 2a. Hardware root of trust and PKI

- **PKI.** Schreiber AI operates an offline root CA and a per-product issuing CA (HSM-backed). The factory provisioning cell (`CTL-PROV-FIXTURE`: J-Link over SWD, bed-of-nails fixture, HSM token) asks each Pod to generate its key pair inside Secure Vault, signs the CSR and writes the device certificate; the serial, EUI-64, certificate fingerprint and firmware hash are recorded in the as-built BOM. Edge computers get a TPM-bound certificate from the same issuing CA. Certificates are valid 5 years; revocation is a CRL on the edge computer.
- **Attestation.** At every join and every broker reconnect the Pod presents a PSA attestation token (boot state, firmware hash, Secure Vault lifecycle state). The edge computer accepts only tokens that chain to Schreiber AI's CA with a firmware hash on the release list; anything else is rejected, logged and shown on the dashboard mesh health panel. Commissioning check CTQ-K5 requires 100 % attested and a rejected rogue join.
- **Signed firmware.** Pod images are signed with ECDSA P-256 (anti-rollback counter in Secure Vault); the edge image and PLC project are signed and hashed; the TPM seals the disk key to the measured boot so a tampered image cannot read the database.
- **Lite tier.** The RevPi Connect 4 has no TPM: it uses signed A/B images with dm-verity and its hardware watchdog relay; the Pods and the PKI are identical. This is stated in the compliance row and the proposal.

## 3. Allowed services (the list E12 scans against)

| Device | Port / protocol | Direction | Purpose |
| --- | --- | --- | --- |
| Edge computer | 8883/TCP MQTT TLS | Z1c (Pods via OTBR) → edge | Pod telemetry/commands |
| Edge computer | 443/TCP HTTPS | Z2 → edge; Z3 → edge (read-only API, optional) | Dashboard, API |
| Edge computer | 22/TCP SSH (keys only, admin VLAN only; may be disabled) | Z2 admin → edge | Maintenance |
| Edge computer | 51820/UDP WireGuard | edge → Z4 (outbound only) | Remote support (optional) |
| Edge computer | 123/UDP SNTP | edge → customer NTP or GPS | Time |
| Edge computer | 5683/UDP CoAP (OTBR, Thread-side only) | Z1c | Border router services, not routable from the LAN |
| PLC | 502/TCP Modbus TCP, 4840/TCP OPC UA | edge → PLC only (panel switch) | Setpoints read, interlock status |
| Vendor devices | 502/TCP Modbus, 161/UDP SNMP v3 | edge → device only | Polling |
| Pods | none listening on the LAN (MQTT client over Thread; no web server, no telnet; Pod E RS-485 is not IP) | — | — |
| Door controller / camera | 443/TCP to edge only | Z1d | Access events, video to local storage |

Anything else found open is a defect.

## 4. Local-first data and customer ownership

- All telemetry, alarms, calibration records, commissioning reports and video are stored on the edge computer and belong to **the customer**. Export is available at any time as CSV (`GET /api/export.csv`) and as a full database dump; the formats are documented in `spec/PROTOCOL.md` and `spec/INTERFACES.md`.
- Schreiber AI receives data only under the managed-service agreement (through the Z4 tunnel) and uses it for operating the unit and for anonymised fleet statistics (model improvement). The customer can revoke this by disabling Z4; the unit keeps working.
- Retention defaults: telemetry 1 Hz for 90 days, 1-minute aggregates for 10 years, alarms and security logs 10 years, video 30 days. All configurable.
- Data recovery is separate from code recovery: the edge computer database has its own nightly backup job to a customer-supplied target (SMB/NFS/S3-compatible) or to a second SSD in the controls panel; restore is tested at SAT (`TURNOVER.md` G2).
- Decommissioning: NIST SP 800-88 purge of the edge computer SSD (TPM clear), Secure Vault lifecycle advance to decommissioned on every Pod, certificate revocation for the unit, record in the decommission report.

## 5. Patching and vulnerability handling

| Item | Practice |
| --- | --- |
| Pod firmware | Released as signed images (ECDSA P-256, anti-rollback); changes logged with SHA-256; applied by OTA over Thread from the edge computer during an agreed window; A/B slots with automatic rollback if the Pod fails to report healthy within 5 min |
| PLC firmware and project | Phoenix Contact security advisories reviewed monthly (PSIRT); project changes under change control with checksum in the record |
| Edge computer OS and `ben_engine` | Monthly security roll-up (or sooner for critical CVEs), staged: twin → Schreiber AI lab unit → customer units in waves; A/B image, automatic rollback |
| Vendor equipment firmware | Reviewed quarterly; applied during maintenance by Schreiber AI or the vendor; recorded |
| Vulnerability intake | security@schreiberai.com; coordinated disclosure within 90 days; customers notified within 72 h of a confirmed exploitable issue affecting their units |
| SBOM | Software bill of materials (SPDX) for the edge image, the Pod firmware and the PLC project delivered with each release and in the turnover package |
| Certificates | Pod and edge computer certificates valid 5 years; expiry tracked in the dashboard with 90-day warning; re-issue procedure in the O&M manual |

## 6. Remote support path (managed service)

1. The edge computer opens a WireGuard tunnel **outbound** to Schreiber AI's operations endpoint (certificate-pinned, keys rotated yearly). Nothing listens for inbound connections at the site.
2. Within the tunnel, Schreiber AI engineers reach the dashboard and SSH (key + hardware token) under named accounts; every session is logged locally and at Schreiber AI; the customer can watch sessions live in the dashboard and can revoke access at any time.
3. The physical key switch on the controls panel ("REMOTE SUPPORT ENABLED / DISABLED") breaks the tunnel; its state is shown on the dashboard and in `status`. Air-gapped sites (public_sector, some healthcare) leave it disabled; support is then by on-site visit or by the customer exporting diagnostics.
4. Firmware and OS updates in managed mode travel through the tunnel but are still signed and verified at the device — the tunnel is transport, not trust.

## 7. White-label implications

| Topic | Rule |
| --- | --- |
| Signing keys | The firmware signing key stays with Schreiber AI unless the partner takes the full source licence and operates their own signing infrastructure; then **their** key is provisioned at the factory and we cannot push firmware to their units. Mixed fleets are not allowed on one edge computer |
| Branding | Dashboard theme and names come from `web/kit/brand.json`-style partner files; security logs and certificates still identify the manufacturer (Schreiber AI) for traceability |
| Remote support | Partner may run the Z4 endpoint themselves or contract Schreiber AI; the choice is recorded in the SLA and in the edge computer config; a unit never has two remote endpoints |
| Vulnerability disclosure | Flows to the partner and to Schreiber AI simultaneously; the partner owns customer notification |
| Source escrow | Hardware-only and white-label customers get source escrow for the controls layer, released on defined triggers (insolvency, end of support) so the "no cloud dependency" promise survives Schreiber AI |
| Compliance packs | HIPAA, PCI, CMMC mappings are delivered as templates; the partner is responsible for their own attestation |

## 7a. Hardening level H3: TEMPEST separation and the air-gapped variant

H3 (`Config.hardening = "H3"`, `docs/TIER_AND_ENCLOSURE_DECISION.md` §3) adds physical and electromagnetic controls to the zones above. Nothing in the software changes; the conduits get narrower and the box gets quieter.

| Topic | H3 rule |
| --- | --- |
| **TEMPEST-ready separation** | Red (customer IT, Z3) and black (controls, Z1, and any external link) cabling run in separate, labelled, metallic raceways with ≥ 50 mm separation and no shared penetration; fibre only between red and black spaces; controls panel, edge computer and border routers sit in the black space; the shielded enclosure option (80 dB, MIL-STD-188-125-1) gives a single filtered power entry and waveguide-below-cutoff vents so the hall or module is itself the shielded volume. **We deliver TEMPEST-ready, not TEMPEST-certified**: the customer's certified TEMPEST authority (CTTA) assesses and certifies; we provide the drawings, the shielding test (IEEE 299) and the penetration schedule they ask for. |
| **Air-gapped variant** | Z4 removed entirely: no WireGuard endpoint, no modem, remote-support key switch deleted from the panel, the edge computer's external interface disabled in firmware and the port blanked; GPS or a local rubidium/PTP grandmaster for time (SNTP off); updates by signed offline bundle on a customer-controlled medium through a kiosk procedure (hash verified against a printed manifest, dual-person rule); fleet learning off, Care Managed delivered as **on-site visits** with an export of the signed monthly proof-of-redundancy report carried out by the customer; vulnerability notices by letter/secure email to the customer's ISSO. |
| **Physical access and tamper** | Mantrap vestibule with two-factor (badge + PIN or biometric) on the inner door; tamper switches on the controls panel, conduit bodies and the shielded door frame wired to PLC digital inputs (Z1a) so a tamper is an interlock event, not a log line; tamper-evident seal register audited quarterly (`MAINTENANCE.md` §5a); audit trail of every door, login, setpoint change and firmware event in BEN Care with hash chaining, exportable for the SSP. |
| **Controls pack** | NIST SP 800-171 Rev. 3 / CMMC Level 2 physical (PE), audit (AU), configuration management (CM) and media protection (MP) control statements pre-written for the unit; FIPS 140-3 validated crypto modules on the edge computer (option) and the PLC's certified development process cited; the controls zone has no route to the internet in any variant, and in the air-gapped variant no route to anything outside the hall. |
| **Border routers and Pods** | Thread radio stays inside the shielded volume (the shield also keeps the mesh in); the Pod radio power is limited to the minimum for the mesh; in a TEMPEST assessment the mesh is treated as a black-side emitter and the CTTA may require the wired RS-485 path (Pod E) only — the design supports both. |
| **BEN 2000 at H3** | Each module is its own shielded volume with a shielded joint (conductive gasket across the module seam, tested in E15 with a shield continuity check); the power module is outside the shield and feeds through filtered penetrations; the plant yard equipment is unshielded and treated as black-side. |

## 8. What we do not claim

- No system certification to IEC 62443 yet; the architecture is designed to SL 2 and can be assessed on request. The PLCnext controller's 62443-4-1 process certification and the MGM240P's PSA Level 3 certification are the vendors' certificates, not ours, and the attestation flow has not yet run on hardware.
- No FIPS 140-3 validation of the crypto modules by default; available as an option for public-sector units.
- No guarantee against a compromised customer network reaching Z3 services we expose on request (read-only API); the firewall rules we ship are the minimum, and customer changes to them are the customer's responsibility.
- The controls layer does not protect the customer's IT workloads; it protects the room they run in.
- No TEMPEST certification: H3 is TEMPEST-*ready*. HEMP protection to MIL-STD-188-125-1 is an option built with a shielding vendor's certified enclosure and verified by test; it is a vendor certificate plus our annual IEEE 299 test, not a government accreditation.
