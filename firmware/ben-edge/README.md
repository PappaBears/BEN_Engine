# BEN Edge — industrial edge computer software package

**Status: implemented, syntax-checked (`bash -n`), unverified on hardware.** Written for **Ubuntu Server
22.04/24.04 LTS or Debian 12 on x86-64** — the **OnLogic Karbon 400** (Intel Atom x6425E, TPM 2.0, −40…70 °C,
DIN rail, dual LAN; alternate Siemens SIMATIC IPC227G). Treat the first install as a commissioning step with
the `CONTROLS_SPEC.md` acceptance checks. **BEN Controls Lite** (RevPi, BEN Micro / BEN 10) uses the
same files through `lite/install.sh` — see `lite/README.md`.

The edge computer is the *data* half of the **BEN Controller**: the MQTT broker the Pods talk to (mutual
TLS), the Thread border router, the time source, the `ben_engine.api` service (FastAPI + twin + SQLite
history), the PLC bridge (Modbus TCP ↔ MQTT), the firewall that keeps the controls zone closed, and the
nightly backup of the unit's data. The *control* half (interlocks) is the PLCnext PLC (`firmware/ben-plc`)
on Pro, or `lite/ben_interlocks_service.py` on Lite. The edge never commands a valve or a cooling unit; it
writes exactly three advisory registers.

## Files

| File | Installs to | Purpose |
| --- | --- | --- |
| `install.sh` | — | Pro installer: packages, user, **TPM 2.0 + LUKS (clevis, PCR 0,2,7)**, venv, VLANs + IPv6 prefix, PKI, broker, OTBR, chrony, firewall, VPN, services, backup target, Pod ACL entries |
| `lite/install.sh` | — | Lite installer for the RevPi (no TPM/docker; native `otbr-agent`; interlock service; watchdog relay) |
| `mosquitto/ben.conf` | `/etc/mosquitto/conf.d/ben.conf` | Four listeners: **8883 mTLS on `fd00:ben::1` (Pods over Thread)**, 8883 mTLS on 10.20.0.1 (Pod E / bridge), 8884 TLS+password on 10.30.0.1 (API, laptop), 9001 WSS |
| `mosquitto/ben_acl.template` | `/etc/mosquitto/ben_acl` | Per-Pod ACL keyed on the **certificate CN** `pod-<unit>-<podN>`: write own `telemetry/status/ack`, read own `cmd` |
| `otbr/docker-compose.yml`, `otbr/otbr.env` | `/etc/ben/` | OpenThread Border Router container(s); one per MGM240P RCP on USB (`/dev/ttyACM0`, `/dev/ttyACM1` for the redundant RCP on BEN 20/40) |
| `otbr/ben-thread-form.sh` | `/usr/local/sbin/` | Forms the unit's Thread network once (channel 25, OMR prefix `fd00:ben::/64`), records the sealed dataset, starts the Commissioner |
| `otbr/radvd.conf` | `/etc/radvd.conf` | Advertises the Pod E prefix and the mesh route on the controls VLAN, **no default route** |
| `otbr/device-ca-chain.example.crt` | `/etc/ben/pki/device-ca-chain.crt` | Placeholder for the Schreiber AI Device CA chain (real one exported from the provisioning HSM) |
| `chrony.conf` | `/etc/chrony/chrony.conf` | Serves time on 10.20.0.1, 10.30.0.1 and `fd00:ben::1`; `local stratum 10 orphan` keeps the unit on one clock without WAN |
| `nftables.conf` | `/etc/ben/nftables.conf` | Default-drop in/out/forward; Thread, controls, management as separate zones; PLC reachable only on 502/4840 from the edge; no WAN by default |
| `systemd/ben-api.service` | `/etc/systemd/system/` | `uvicorn ben_engine.api:app` on 10.30.0.1:8000, hardened, restart=always |
| `systemd/ben-plc-bridge.service` | `/etc/systemd/system/` | 1 Hz Modbus TCP poll of the PLC (or Lite software controller) → `ben/<unit>/plc/interlocks`, `node/plcN/*`; writes `EDGE_WATCHDOG`, `SUPPLY_TRIM_x10`, `TEST_REQUEST` only |
| `systemd/ben-otbr.service` | `/etc/systemd/system/` | Brings the OTBR compose stack up after the firewall |
| `systemd/ben-backup.{service,timer}` | `/etc/systemd/system/` | Nightly 02:17 consistent SQLite `.backup` + integrity check + sha256 to USB/NAS |
| `systemd/ben-firewall.service` | `/etc/systemd/system/` | Loads the nftables ruleset before networking services |
| `logrotate.conf` | `/etc/logrotate.d/ben` | 30 days of API/bridge/backup logs, 8 weeks of broker log |
| `ben.env.example` | `/etc/ben/ben.env` | Unit id, tier, broker credentials/certs, PLC address + map, DB path, retention, backup target |
| `scripts/ben-add-pod.sh` | `/usr/local/sbin/` | Pod lifecycle: ACL entry by CN, Thread joiner entry (EUI-64 + PSKd, 10 min window), `--renew` (CSR → cert), `--revoke` |
| `scripts/ben-backup.sh` | (run by timer) | The backup itself; skips loudly if the USB/NAS is not mounted |
| `scripts/ben-vpn-support.sh` | `/usr/local/sbin/` | Customer-controlled `up`/`down` for the outbound-only WireGuard support tunnel (auto-off 48 h) |

`ben_engine.plc_bridge` (the Python module the bridge service runs) is **not yet written**; the service file,
the environment and the register map it will load (`/etc/ben/modbus_map.csv`) are in place.

## Install (Pro, Karbon 400)

```bash
# Image the Karbon: Ubuntu 24.04 LTS, Secure Boot ON, partition 3 = LUKS2 labelled BEN_DATA (see install.sh step 3)
sudo apt-get install -y git
git clone <repo> /opt/src/ben_engine && cd /opt/src/ben_engine/firmware/ben-edge
sudo UNIT=ben20-0007 PODS=12 PLC_IP=10.20.0.10 CTRL_IF=enp1s0 MGMT_IF=enp2s0 \
     RCP_DEVS="/dev/ttyACM0 /dev/ttyACM1" BACKUP_DEV=/dev/sdb1 ./install.sh
# options: ENABLE_WAN=1 (apt/OTA fetch outbound only), SUPPORT_VPN=1 (installs wg0, stays down), NAS=//nas/ben, LUKS=0
```

Then per Pod, from its label: `ben-add-pod.sh ben20-0007 pod3 --serial SAI-P-000123 --eui64 b43a31fffe12ab34 --pskd J01NME`
opens a 10 min joiner window; the Pod joins (DTLS/J-PAKE), attaches, connects to the broker with its
device certificate and appears as a retained `status` with `attested:true` after the edge's challenge.

## Network layout the installer assumes

```
enp1s0          10.20.0.1/24 + fd00:ben:1::1/64   controls VLAN 20: PLC 10.20.0.10, Pod E, Modbus-TCP meters, PDUs (SNMP), cooling, UPS
wpan0 (RCP)     fd00:ben::1/64                    Thread mesh: BEN Pods (own zone; DTLS join, mTLS MQTT). wpan1 = second RCP (BEN 20/40)
enp2s0          10.30.0.1/24                      management VLAN 30: dashboard, engineering laptop, API :8000, MQTT TLS :8884, WSS :9001
(customer IT)   —                                 separate VLAN/switch; the edge computer has NO interface on it
wan0 / wg0      optional                          outbound only; nothing listens on WAN. VPN is customer-switched.
```

The edge never forwards between zones (`forward` chain policy drop; Thread is a stub network terminating on
the host's own broker). DHCP for Pod E / meters hands out no default route.

## TPM 2.0 and disk encryption

The data volume (`/var/lib/ben`: SQLite, reports, calibration records, Thread dataset copies) is **LUKS2**,
unlocked at boot by **clevis/tpm2** sealed to PCR 0, 2, 7 (firmware, option ROMs, Secure Boot policy). A
changed BIOS, a disabled Secure Boot or a moved disk falls back to the recovery passphrase, which lives in the
unit's turnover package (sealed envelope) — never on the unit. The OS partition is unencrypted and holds no
unit data; `/etc/ben` (certs, env) is on the data volume via bind mount in production images.

## Data retention and recovery

- SQLite at `/var/lib/ben/ben.sqlite`; `BEN_RETENTION_DAYS=400` (13 months, covers a seasonal cycle).
- Nightly `.backup` (online, consistent) → gzip → sha256 → `/mnt/ben-backup/<unit>/`, keep 30.
- Commissioning reports, calibration records and Pod certificate renewals under `/var/lib/ben/reports` go in the same backup.
- Restore: `gunzip -c ben-<ts>.sqlite.gz > /var/lib/ben/ben.sqlite && chown ben:ben … && systemctl restart ben-api`.
- The repo (code) is recovered from git; the data is recovered from this backup; the Thread dataset and the
  recovery passphrase from the turnover package. They are separate on purpose.

## Verification checklist (do this on the first real edge computer)

1. `systemctl status ben-firewall mosquitto chrony ben-otbr ben-api ben-plc-bridge ben-backup.timer` — all active.
2. `docker exec otbr ot-ctl state` → `leader`; `ot-ctl netdata show` lists `fd00:ben::/64`; `ip -6 addr show wpan0` has `fd00:ben::1`.
3. `nft list ruleset` shows policy drop on input/forward/output; from the customer IT VLAN, `nmap 10.20.0.1` finds nothing; from the controls VLAN only 8883/123/67 answer; `nmap -6 fd00:ben::1` from a Pod address finds 8883/123/5683 only.
4. `chronyc sources` and `chronyc clients` — every Pod and the PLC appear as SNTP clients within 2 min of boot.
5. `mosquitto_sub -h 10.30.0.1 -p 8884 --cafile /etc/ben/pki/unit-ca.crt -u benapi -P … -t 'ben/+/node/+/status' -v` — one retained status per Pod with `attested:true`, `parent`, `lqi`, `cert_id`.
6. A Pod certificate signed by a *different* CA is refused at the TLS handshake; a valid Pod publishing on another Pod's topic is **denied** (ACL).
7. `clevis luks list -d /dev/nvme0n1p3` shows the tpm2 pin; reboot unlocks without a prompt; `tpm2_pcrread sha256:7` recorded in the turnover package.
8. Pull the USB stick, trigger `systemctl start ben-backup` — log says `BACKUP SKIPPED`; replace it, run again — `BACKUP OK`.
9. Stop `ben-plc-bridge` for 35 s: PLC register `EDGE_LOST` (40005) goes 1, cooling keeps sequencing on the PLC, dashboard shows "edge advisory lost"; restart → 0.
10. Power the primary RCP off (BEN 20/40): Pods re-attach through the second border router within 60 s; no telemetry gap beyond the ring-buffer replay (`replay:true`).
