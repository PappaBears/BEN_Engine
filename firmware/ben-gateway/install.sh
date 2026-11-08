#!/usr/bin/env bash
# BEN Engine gateway installer — Raspberry Pi 5, Raspberry Pi OS Lite (Debian 12, 64-bit)
# Schreiber AI. Status: implemented, unverified on hardware (written against Debian 12 packages).
#
#   sudo UNIT=ben20-0007 NODES=4 ./install.sh
#   options: ENABLE_WAN=0|1 (default 0)  SUPPORT_VPN=0|1 (default 0)  BACKUP_DEV=/dev/sda1 or NAS=//nas/ben
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
: "${UNIT:?set UNIT=<unit id>, e.g. ben20-0007}"
: "${NODES:=4}"; : "${ENABLE_WAN:=0}"; : "${SUPPORT_VPN:=0}"; : "${BACKUP_DEV:=}"; : "${NAS:=}"
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)

echo "== [1/9] packages"
apt-get update
apt-get install -y mosquitto mosquitto-clients chrony nftables sqlite3 python3-venv python3-pip \
    dnsmasq logrotate wireguard-tools openssl unattended-upgrades cifs-utils

echo "== [2/9] user, directories"
id ben >/dev/null 2>&1 || useradd -r -s /usr/sbin/nologin -d /var/lib/ben ben
mkdir -p /var/lib/ben/reports /var/log/ben /etc/ben /mnt/ben-backup /opt
chown -R ben:ben /var/lib/ben /var/log/ben
[ -e /opt/ben_engine ] || ln -s "$REPO" /opt/ben_engine

echo "== [3/9] python service (ben_engine.api)"
python3 -m venv /opt/ben_engine/.venv
/opt/ben_engine/.venv/bin/pip install -q --upgrade pip
/opt/ben_engine/.venv/bin/pip install -q -e "$REPO/software" uvicorn fastapi paho-mqtt pymodbus pysnmp
API_PASS=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)
if [ ! -f /etc/ben/ben.env ]; then
    sed -e "s/^BEN_UNIT=.*/BEN_UNIT=$UNIT/" -e "s/^BEN_MQTT_PASS=.*/BEN_MQTT_PASS=$API_PASS/" "$HERE/ben.env.example" > /etc/ben/ben.env
    chown root:ben /etc/ben/ben.env; chmod 0640 /etc/ben/ben.env
fi

echo "== [4/9] network: controls VLAN 10.20.0.1/24 on eth0, management VLAN 30 tagged"
cat > /etc/systemd/network/10-ctrl.network <<NET
[Match]
Name=eth0
[Network]
Address=10.20.0.1/24
VLAN=eth0.30
LinkLocalAddressing=no
IPv6AcceptRA=no
NET
cat > /etc/systemd/network/20-mgmt.netdev <<NET
[NetDev]
Name=eth0.30
Kind=vlan
[VLAN]
Id=30
NET
cat > /etc/systemd/network/20-mgmt.network <<NET
[Match]
Name=eth0.30
[Network]
Address=10.30.0.1/24
NET
cat > /etc/dnsmasq.d/ben.conf <<DNS
interface=eth0
bind-interfaces
dhcp-range=10.20.0.100,10.20.0.199,12h
dhcp-option=option:ntp-server,10.20.0.1
dhcp-option=option:router      # no default route handed to nodes: the controls VLAN has no exit
DNS
systemctl enable systemd-networkd dnsmasq

echo "== [5/9] mosquitto: per-node auth, ACL, TLS certs"
install -m 0644 "$HERE/mosquitto/ben.conf" /etc/mosquitto/conf.d/ben.conf
sed "s/__UNIT__/$UNIT/g" "$HERE/mosquitto/ben_acl.template" > /etc/mosquitto/ben_acl
touch /etc/mosquitto/ben_passwd
mosquitto_passwd -b /etc/mosquitto/ben_passwd benapi "$(grep ^BEN_MQTT_PASS= /etc/ben/ben.env | cut -d= -f2)"
mosquitto_passwd -b /etc/mosquitto/ben_passwd dashboard "$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)"
for i in $(seq 1 "$NODES"); do UNIT=$UNIT "$HERE/scripts/ben-add-node.sh" "$UNIT" "node$i" | tee -a /root/ben-node-provisioning.txt; done
chmod 0600 /root/ben-node-provisioning.txt
if [ ! -f /etc/mosquitto/certs/ben-ca.crt ]; then
    mkdir -p /etc/mosquitto/certs && cd /etc/mosquitto/certs
    openssl req -x509 -newkey rsa:3072 -nodes -days 3650 -subj "/CN=BEN $UNIT local CA/O=Schreiber AI" -keyout ben-ca.key -out ben-ca.crt
    openssl req -newkey rsa:2048 -nodes -subj "/CN=10.30.0.1" -keyout gateway.key -out gateway.csr
    printf "subjectAltName=IP:10.30.0.1,IP:10.20.0.1,DNS:gateway.ben.local\n" > san.ext
    openssl x509 -req -in gateway.csr -CA ben-ca.crt -CAkey ben-ca.key -CAcreateserial -out gateway.crt -days 1825 -extfile san.ext
    chown mosquitto:mosquitto gateway.key; chmod 0600 gateway.key ben-ca.key; cd "$HERE"
fi
chown mosquitto:mosquitto /etc/mosquitto/ben_passwd /etc/mosquitto/ben_acl; chmod 0600 /etc/mosquitto/ben_passwd

echo "== [6/9] chrony"
install -m 0644 "$HERE/chrony.conf" /etc/chrony/chrony.conf

echo "== [7/9] firewall (controls VLAN only, no WAN by default)"
install -m 0644 "$HERE/nftables.conf" /etc/ben/nftables.conf
if [ "$ENABLE_WAN" = 1 ]; then
    echo "WAN enabled: apt/OTA fetch allowed outbound only (TCP 80/443, UDP 123, UDP 51820)"
    sed -i 's/ ct mark 0x5a//' /etc/ben/nftables.conf
fi
systemctl disable --now nftables 2>/dev/null || true   # we manage the ruleset via ben-firewall.service

echo "== [8/9] optional outbound-only support VPN"
if [ "$SUPPORT_VPN" = 1 ]; then
    if [ ! -f /etc/wireguard/wg0.conf ]; then
        wg genkey | tee /etc/wireguard/gw.key | wg pubkey > /etc/wireguard/gw.pub
        cat > /etc/wireguard/wg0.conf <<WG
[Interface]
PrivateKey = $(cat /etc/wireguard/gw.key)
Address = 10.99.$((RANDOM % 250 + 1)).2/32
# No ListenPort: this peer only initiates.
[Peer]
# Schreiber AI support concentrator — fill in before first use
PublicKey = REPLACE_WITH_SCHREIBER_AI_SUPPORT_PUBKEY
Endpoint = support.schreiberai.com:51820
AllowedIPs = 10.99.0.1/32
PersistentKeepalive = 25
WG
        chmod 0600 /etc/wireguard/wg0.conf /etc/wireguard/gw.key
        echo "Gateway WireGuard public key (send to Schreiber AI support): $(cat /etc/wireguard/gw.pub)"
    fi
    echo "Support VPN installed but DOWN. Customer runs: ben-vpn-support.sh up"
else
    echo "Support VPN not installed (SUPPORT_VPN=0)"
fi
install -m 0755 "$HERE/scripts/ben-vpn-support.sh" /usr/local/sbin/ben-vpn-support.sh
install -m 0755 "$HERE/scripts/ben-add-node.sh" /usr/local/sbin/ben-add-node.sh

echo "== [9/9] backup target, services, log rotation"
if [ -n "$BACKUP_DEV" ]; then
    uuid=$(blkid -s UUID -o value "$BACKUP_DEV")
    grep -q "$uuid" /etc/fstab || echo "UUID=$uuid /mnt/ben-backup auto defaults,nofail,noatime,x-systemd.device-timeout=10 0 2" >> /etc/fstab
elif [ -n "$NAS" ]; then
    grep -q "$NAS" /etc/fstab || echo "$NAS /mnt/ben-backup cifs credentials=/etc/ben/nas.cred,nofail,_netdev,uid=ben,gid=ben 0 0" >> /etc/fstab
    [ -f /etc/ben/nas.cred ] || { printf "username=ben\npassword=CHANGE_ME\n" > /etc/ben/nas.cred; chmod 0600 /etc/ben/nas.cred; }
fi
mount -a || true
chmod 0755 "$HERE/scripts/ben-backup.sh"
install -m 0644 "$HERE/logrotate.conf" /etc/logrotate.d/ben
install -m 0644 "$HERE"/systemd/*.service "$HERE"/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now ben-firewall.service chrony mosquitto ben-api.service ben-backup.timer
systemctl restart mosquitto

echo
echo "BEN gateway installed for unit $UNIT with $NODES node credentials."
echo "  node provisioning lines: /root/ben-node-provisioning.txt"
echo "  dashboard/API: http://10.30.0.1:8000   MQTT TLS: 10.30.0.1:8883   CA: /etc/mosquitto/certs/ben-ca.crt"
echo "  verify: systemctl status ben-api mosquitto chrony ben-firewall ; nft list ruleset ; chronyc sources"
