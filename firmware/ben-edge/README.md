# BEN Gateway — Raspberry Pi 5 software package

**Status: implemented, unverified on hardware.** Every file in this directory was written against
Raspberry Pi OS Lite (Debian 12, 64-bit) package names and syntax-checked (`bash -n`), but no
gateway has been built and run yet. Treat the first install as a commissioning step with the
`CONTROLS_SPEC.md` acceptance checks.

The gateway is not ESP code. It is the Pi that runs the unit: the MQTT broker the nodes talk to,
the time source they sync to, the `ben_engine.api` service (FastAPI + twin + SQLite history),
the firewall that keeps the controls VLAN closed, and the nightly backup of the unit's data.

## Files

| File | Installs to | Purpose |
| --- | --- | --- |
| `install.sh` | — | One-shot installer: packages, user, VLANs, broker, certs, chrony, firewall, services, backup target |
| `mosquitto/ben.conf` | `/etc/mosquitto/conf.d/ben.conf` | Three listeners: 1883 plain on controls VLAN (nodes), 8883 TLS and 9001 WSS on management VLAN |
| `mosquitto/ben_acl.template` | `/etc/mosquitto/ben_acl` | Per-node ACL: a node writes only its own `telemetry/status/ack`, reads only its own `cmd` |
| `chrony.conf` | `/etc/chrony/chrony.conf` | Gateway serves time to both VLANs; `local stratum 10 orphan` keeps the unit on one clock without WAN |
| `nftables.conf` | `/etc/ben/nftables.conf` | Default-drop in/out/forward; controls VLAN only; no WAN by default; VPN inbound SSH/API only |
| `systemd/ben-api.service` | `/etc/systemd/system/` | `uvicorn ben_engine.api:app` on 10.30.0.1:8000, hardened, restart=always |
| `systemd/ben-backup.{service,timer}` | `/etc/systemd/system/` | Nightly 02:17 consistent SQLite `.backup` + integrity check + sha256 to USB/NAS |
| `systemd/ben-firewall.service` | `/etc/systemd/system/` | Loads the nftables ruleset before networking services |
| `logrotate.conf` | `/etc/logrotate.d/ben` | 30 days of API/backup logs, 8 weeks of broker log |
| `ben.env.example` | `/etc/ben/ben.env` | Unit id, broker credentials, DB path, retention, backup target |
| `scripts/ben-add-node.sh` | `/usr/local/sbin/` | Creates a node's broker credential + ACL block and prints the serial `PROV` line |
| `scripts/ben-backup.sh` | (run by timer) | The backup itself; skips loudly if the USB/NAS is not mounted |
| `scripts/ben-vpn-support.sh` | `/usr/local/sbin/` | Customer-controlled `up`/`down` for the outbound-only WireGuard support tunnel (auto-off 48 h) |

## Install

```bash
sudo apt-get install -y git
git clone <repo> /home/pi/ben_engine && cd /home/pi/ben_engine/firmware/ben-gateway
sudo UNIT=ben20-0007 NODES=4 BACKUP_DEV=/dev/sda1 ./install.sh
# options: ENABLE_WAN=1 (apt/OTA fetch outbound only), SUPPORT_VPN=1 (installs wg0, stays down), NAS=//nas/ben
```

The installer prints one `PROV unit=… node=… broker=10.20.0.1 user=… pass=…` line per node into
`/root/ben-node-provisioning.txt`. Paste each on the matching node's USB serial console (see
`firmware/README.md` → Provisioning).

## Network layout the installer assumes

```
eth0            10.20.0.1/24   controls VLAN 20 (untagged): nodes, Modbus-TCP meter gateway, PDUs (SNMP), cooling, UPS
eth0.30         10.30.0.1/24   management VLAN 30 (tagged):  dashboard, engineering laptop, API :8000, MQTT TLS :8883
(customer IT)   —              separate VLAN/switch; the gateway has NO interface on it
wan0 / wg0      optional       outbound only; nothing listens on WAN. VPN is customer-switched.
```

The gateway never forwards between zones (`forward` chain policy drop). DHCP for nodes hands out no
default route — the controls VLAN has no exit.

## Data retention and recovery

- SQLite at `/var/lib/ben/ben.sqlite`; `BEN_RETENTION_DAYS=400` (13 months, covers a seasonal cycle).
- Nightly `.backup` (online, consistent) → gzip → sha256 → `/mnt/ben-backup/<unit>/`, keep 30.
- Commissioning reports and calibration records under `/var/lib/ben/reports` go in the same backup.
- Restore: `gunzip -c ben-<ts>.sqlite.gz > /var/lib/ben/ben.sqlite && chown ben:ben … && systemctl restart ben-api`.
- The repo (code) is recovered from git; the data is recovered from this backup. They are separate on purpose.

## Verification checklist (do this on the first real gateway)

1. `systemctl status ben-firewall mosquitto chrony ben-api ben-backup.timer` — all active.
2. `nft list ruleset` shows policy drop on input/forward/output; from the customer IT VLAN, `nmap 10.20.0.1` finds nothing.
3. `chronyc sources` and `chronyc clients` — every node appears as an SNTP client within 2 min of boot.
4. `mosquitto_sub -h 10.20.0.1 -u benapi -P … -t 'ben/+/node/+/status' -v` — one retained status per node.
5. `mosquitto_pub` as `node1` to `ben/<unit>/node/node2/telemetry` is **denied** (ACL).
6. Pull the USB stick, trigger `systemctl start ben-backup` — log says `BACKUP SKIPPED`; replace it, run again — `BACKUP OK`.
7. Pull the gateway's Ethernet for 90 s: node LEDs blink 1 Hz; relay1 (cooling enable) drops; on reconnect the
   dashboard shows the gap back-filled with `replay:true` records.
