#!/usr/bin/env bash
# BEN Engine — BEN Controls Lite installer — KUNBUS Revolution Pi RevPi Connect 4 / Connect S (Schreiber AI)
# Target: the KUNBUS RevPi image (Debian 12 "bookworm" based, 64-bit), RevPi DIO / AIO modules on PiBridge.
# Status: implemented, syntax-checked, unverified on hardware. For BEN Controls Pro use ../install.sh.
#
#   sudo UNIT=benmicro-0003 PODS=4 ./install.sh
#   options as in ../install.sh (ENABLE_WAN, SUPPORT_VPN, BACKUP_DEV|NAS, RCP_DEVS); CTRL_IF default eth0, MGMT_IF default eth1
#
# What is different from Pro:
#   * no PLC: the interlock state machine (ben_engine.interlocks) runs here as ben-interlocks.service and
#     serves the same Modbus TCP register map on 127.0.0.1:502 (and 10.20.0.1:502 for a customer BMS);
#   * field I/O is RevPi DIO (cooling cmd/run/fault, leak zones, valves, doors, EPO/fire aux, ATS/gen contacts)
#     and RevPi AIO (Pt1000, 4-20 mA transmitters) through /dev/piControl0 (process image, PiCtory config);
#   * a hardware WATCHDOG RELAY: the RevPi hardware watchdog (/dev/watchdog, 60 s) is petted only by the
#     interlock service; if it stops, the RevPi reboots AND the watchdog's relay output (DIO O_14, wired
#     as the cooling-enable chain contact) drops -> every cooling unit reverts to its own controller;
#   * no TPM 2.0 on the RevPi: the data volume is LUKS with the key on the RevPi's secure element where the
#     image supports it, else a passphrase file on the eMMC with the recovery copy in the turnover package.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
: "${UNIT:?set UNIT=<unit id>, e.g. benmicro-0003}"
: "${PODS:=4}"; : "${ENABLE_WAN:=0}"; : "${SUPPORT_VPN:=0}"; : "${BACKUP_DEV:=}"; : "${NAS:=}"
: "${CTRL_IF:=eth0}"; : "${MGMT_IF:=eth1}"; : "${RCP_DEVS:=/dev/ttyACM0}"
HERE=$(cd "$(dirname "$0")" && pwd)
PRO=$(cd "$HERE/.." && pwd)
REPO=$(cd "$HERE/../../.." && pwd)
[ -e /dev/piControl0 ] || echo "WARNING: /dev/piControl0 not present — piControl driver missing or not a RevPi"

echo "== [1/8] packages (RevPi image is Debian based; same package names as Pro minus TPM/docker)"
apt-get update
apt-get install -y mosquitto mosquitto-clients chrony nftables sqlite3 python3-venv python3-pip \
    dnsmasq logrotate wireguard-tools openssl unattended-upgrades cifs-utils cryptsetup radvd \
    watchdog otbr-agent 2>/dev/null || apt-get install -y mosquitto mosquitto-clients chrony nftables sqlite3 \
    python3-venv python3-pip dnsmasq logrotate wireguard-tools openssl unattended-upgrades cifs-utils cryptsetup radvd watchdog
# OTBR: the RevPi image may not have Docker; use the native ot-br-posix build (KUNBUS/Debian package `otbr-agent`
# if available, otherwise build from source per otbr/README). RCP = MGM240P on USB, same as Pro.

echo "== [2/8] user, directories, python"
id ben >/dev/null 2>&1 || useradd -r -s /usr/sbin/nologin -d /var/lib/ben ben
mkdir -p /var/lib/ben/reports /var/log/ben /etc/ben /etc/ben/pki /mnt/ben-backup /opt
chown -R ben:ben /var/lib/ben /var/log/ben
[ -e /opt/ben_engine ] || ln -s "$REPO" /opt/ben_engine
python3 -m venv /opt/ben_engine/.venv
/opt/ben_engine/.venv/bin/pip install -q --upgrade pip
/opt/ben_engine/.venv/bin/pip install -q -e "$REPO" uvicorn fastapi paho-mqtt pymodbus pysnmp cryptography revpimodio2
API_PASS=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)
if [ ! -f /etc/ben/ben.env ]; then
    sed -e "s/^BEN_UNIT=.*/BEN_UNIT=$UNIT/" -e "s/^BEN_TIER=.*/BEN_TIER=lite/" -e "s/^BEN_MQTT_PASS=.*/BEN_MQTT_PASS=$API_PASS/" \
        -e "s/^BEN_PLC_IP=.*/BEN_PLC_IP=127.0.0.1/" "$PRO/ben.env.example" > /etc/ben/ben.env
    chown root:ben /etc/ben/ben.env; chmod 0640 /etc/ben/ben.env
fi
install -m 0644 "$REPO/firmware/ben-plc/modbus_map.csv" /etc/ben/modbus_map.csv
install -m 0644 "$HERE/revpi_io_map.json" /etc/ben/revpi_io_map.json
usermod -aG dialout ben   # piControl device access group on the RevPi image

echo "== [3/8] network (same addressing as Pro: $CTRL_IF 10.20.0.1/24, $MGMT_IF 10.30.0.1/24, Thread fd00:ben::/64)"
cat > /etc/systemd/network/10-ctrl.network <<NET
[Match]
Name=$CTRL_IF
[Network]
Address=10.20.0.1/24
LinkLocalAddressing=ipv6
IPv6AcceptRA=no
IPForward=ipv6
NET
cat > /etc/systemd/network/20-mgmt.network <<NET
[Match]
Name=$MGMT_IF
[Network]
Address=10.30.0.1/24
LinkLocalAddressing=no
NET
cat > /etc/dnsmasq.d/ben.conf <<DNS
interface=$CTRL_IF
bind-interfaces
dhcp-range=10.20.0.100,10.20.0.199,12h
dhcp-option=option:ntp-server,10.20.0.1
dhcp-option=option:router
DNS
echo "net.ipv6.conf.all.forwarding=1" > /etc/sysctl.d/60-ben-thread.conf
systemctl disable --now dhcpcd NetworkManager 2>/dev/null || true
systemctl enable systemd-networkd dnsmasq

echo "== [4/8] PKI, broker, ACL (identical to Pro)"
cd /etc/ben/pki
if [ ! -f unit-ca.crt ]; then
    openssl ecparam -name prime256v1 -genkey -noout -out unit-ca.key
    openssl req -x509 -new -key unit-ca.key -days 3650 -subj "/CN=BEN $UNIT unit CA/O=Schreiber AI" -out unit-ca.crt
    openssl ecparam -name prime256v1 -genkey -noout -out broker.key
    openssl req -new -key broker.key -subj "/CN=broker.ben.local" -out broker.csr
    printf "subjectAltName=IP:10.30.0.1,IP:10.20.0.1,IP:fd00:ben::1,DNS:broker.ben.local\nextendedKeyUsage=serverAuth\n" > san.ext
    openssl x509 -req -in broker.csr -CA unit-ca.crt -CAkey unit-ca.key -CAcreateserial -out broker.crt -days 1825 -extfile san.ext
    openssl ecparam -name prime256v1 -genkey -noout -out benapi.key
    openssl req -new -key benapi.key -subj "/CN=benapi" -out benapi.csr
    openssl x509 -req -in benapi.csr -CA unit-ca.crt -CAkey unit-ca.key -CAcreateserial -out benapi.crt -days 1825
fi
[ -f device-ca-chain.crt ] || cp "$PRO/otbr/device-ca-chain.example.crt" device-ca-chain.crt
cat unit-ca.crt device-ca-chain.crt > trusted-clients.crt
chown -R mosquitto:mosquitto /etc/ben/pki; chmod 0600 /etc/ben/pki/*.key; cd "$HERE"
install -m 0644 "$PRO/mosquitto/ben.conf" /etc/mosquitto/conf.d/ben.conf
sed "s/__UNIT__/$UNIT/g" "$PRO/mosquitto/ben_acl.template" > /etc/mosquitto/ben_acl
touch /etc/mosquitto/ben_passwd
mosquitto_passwd -b /etc/mosquitto/ben_passwd benapi "$(grep ^BEN_MQTT_PASS= /etc/ben/ben.env | cut -d= -f2)"
mosquitto_passwd -b /etc/mosquitto/ben_passwd dashboard "$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)"
chown mosquitto:mosquitto /etc/mosquitto/ben_passwd /etc/mosquitto/ben_acl; chmod 0600 /etc/mosquitto/ben_passwd

echo "== [5/8] OTBR (native otbr-agent), chrony, firewall"
mkdir -p /etc/default
cat > /etc/default/otbr-agent <<OT
OTBR_AGENT_OPTS="-I wpan0 -B $CTRL_IF spinel+hdlc+uart://${RCP_DEVS%% *}?uart-baudrate=460800 trel://$CTRL_IF"
OT
install -m 0644 "$PRO/otbr/radvd.conf" /etc/radvd.conf; sed -i "s/interface enp1s0/interface $CTRL_IF/" /etc/radvd.conf
install -m 0755 "$PRO/otbr/ben-thread-form.sh" /usr/local/sbin/ben-thread-form.sh
sed -i 's#otctl() { docker exec otbr ot-ctl "$@"; }#otctl() { ot-ctl "$@"; }#' /usr/local/sbin/ben-thread-form.sh
install -m 0644 "$PRO/chrony.conf" /etc/chrony/chrony.conf
install -m 0644 "$PRO/nftables.conf" /etc/ben/nftables.conf
sed -i "s/define CTRL   = \"enp1s0\"/define CTRL   = \"$CTRL_IF\"/; s/define MGMT   = \"enp2s0\"/define MGMT   = \"$MGMT_IF\"/" /etc/ben/nftables.conf
# Lite: the software controller serves Modbus TCP 502 on the controls VLAN for a customer BMS (read-only ACL in the service)
sed -i "s#iifname \$CTRL ip saddr @plc tcp dport 8883 accept.*#iifname \$CTRL ip saddr @ctrl_hosts tcp dport 502 accept      # Lite: BMS reads the software controller's register map#" /etc/ben/nftables.conf
[ "$ENABLE_WAN" = 1 ] && sed -i 's/ ct mark 0x5a//' /etc/ben/nftables.conf
systemctl disable --now nftables 2>/dev/null || true
systemctl enable radvd otbr-agent 2>/dev/null || true

echo "== [6/8] hardware watchdog relay"
# RevPi hardware watchdog: /dev/watchdog, 60 s. ONLY ben-interlocks.service pets it (WatchdogSec in its unit +
# the service writes the keepalive). The `watchdog` daemon is disabled so nothing else can mask a dead interlock loop.
systemctl disable --now watchdog 2>/dev/null || true
cat > /etc/ben/watchdog-relay.md <<MD
Watchdog relay (Lite): RevPi DIO output O_14 drives relay KW1 (24 VDC, DIN rail). KW1 NO contact is wired IN
SERIES in the cooling-enable chain (same chain the Pro PLC's enable output closes). ben-interlocks.service sets
O_14 only while its loop runs and the state machine says cooling_enable_relay=TRUE; the RevPi hardware watchdog
reboots the CPU if the service stalls 60 s, and piControl resets all outputs to 0 on reboot -> chain opens ->
units run on their own controllers. KW1 NC contact lights the panel 'controls fault' beacon.
MD

echo "== [7/8] VPN (optional), backup target"
if [ "$SUPPORT_VPN" = 1 ]; then
    if [ ! -f /etc/wireguard/wg0.conf ]; then
        wg genkey | tee /etc/wireguard/gw.key | wg pubkey > /etc/wireguard/gw.pub
        cat > /etc/wireguard/wg0.conf <<WG
[Interface]
PrivateKey = $(cat /etc/wireguard/gw.key)
Address = 10.99.$((RANDOM % 250 + 1)).2/32
[Peer]
PublicKey = REPLACE_WITH_SCHREIBER_AI_SUPPORT_PUBKEY
Endpoint = support.schreiberai.com:51820
AllowedIPs = 10.99.0.1/32
PersistentKeepalive = 25
WG
        chmod 0600 /etc/wireguard/wg0.conf /etc/wireguard/gw.key
        echo "Edge WireGuard public key (send to Schreiber AI support): $(cat /etc/wireguard/gw.pub)"
    fi
fi
install -m 0755 "$PRO/scripts/ben-vpn-support.sh" /usr/local/sbin/ben-vpn-support.sh
install -m 0755 "$PRO/scripts/ben-add-pod.sh" /usr/local/sbin/ben-add-pod.sh
if [ -n "$BACKUP_DEV" ]; then
    uuid=$(blkid -s UUID -o value "$BACKUP_DEV")
    grep -q "$uuid" /etc/fstab || echo "UUID=$uuid /mnt/ben-backup auto defaults,nofail,noatime,x-systemd.device-timeout=10 0 2" >> /etc/fstab
elif [ -n "$NAS" ]; then
    grep -q "$NAS" /etc/fstab || echo "$NAS /mnt/ben-backup cifs credentials=/etc/ben/nas.cred,nofail,_netdev,uid=ben,gid=ben 0 0" >> /etc/fstab
    [ -f /etc/ben/nas.cred ] || { printf "username=ben\npassword=CHANGE_ME\n" > /etc/ben/nas.cred; chmod 0600 /etc/ben/nas.cred; }
fi
mount -a || true

echo "== [8/8] services"
chmod 0755 "$PRO/scripts/ben-backup.sh"
install -m 0644 "$PRO/logrotate.conf" /etc/logrotate.d/ben
install -m 0644 "$PRO"/systemd/ben-api.service "$PRO"/systemd/ben-backup.service "$PRO"/systemd/ben-backup.timer "$PRO"/systemd/ben-firewall.service "$PRO"/systemd/ben-plc-bridge.service /etc/systemd/system/
install -m 0644 "$HERE"/systemd/ben-interlocks.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now ben-firewall.service chrony mosquitto ben-interlocks.service ben-api.service ben-plc-bridge.service ben-backup.timer
systemctl restart mosquitto
/usr/local/sbin/ben-thread-form.sh "$UNIT" || echo "Thread network not formed yet (RCP not attached?) — rerun ben-thread-form.sh $UNIT"
: > /root/ben-pod-provisioning.txt
for i in $(seq 1 "$PODS"); do "$PRO/scripts/ben-add-pod.sh" "$UNIT" "pod$i" | tee -a /root/ben-pod-provisioning.txt; done
chmod 0600 /root/ben-pod-provisioning.txt

echo
echo "BEN Controls Lite installed for unit $UNIT on RevPi with $PODS Pod ACL entries."
echo "  interlocks: systemctl status ben-interlocks ; register map on 127.0.0.1:502 and 10.20.0.1:502 (read-only for BMS)"
echo "  verify watchdog: systemctl stop ben-interlocks -> O_14 drops within 1 s, RevPi reboots within 60 s, beacon lights"
