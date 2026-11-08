#!/usr/bin/env bash
# BEN Engine edge computer installer — BEN Controls Pro (Schreiber AI)
# Target: OnLogic Karbon 400 (Intel Atom x6425E, TPM 2.0) or Siemens IPC227G, x86-64,
#         Ubuntu Server 22.04/24.04 LTS or Debian 12. Status: implemented, syntax-checked, unverified on hardware.
# For BEN Controls Lite (RevPi) use lite/install.sh instead.
#
#   sudo UNIT=ben20-0007 PODS=12 PLC_IP=10.20.0.10 ./install.sh
#   options: ENABLE_WAN=0|1 (default 0)  SUPPORT_VPN=0|1 (default 0)  BACKUP_DEV=/dev/sdb1 or NAS=//nas/ben
#            CTRL_IF=enp1s0 (controls VLAN trunk)  MGMT_IF=enp2s0 (management, separate NIC on the Karbon)
#            RCP_DEVS="/dev/ttyACM0 /dev/ttyACM1" (MGM240P radio co-processors; two on BEN 150/500)
#            LUKS=1 (default 1: enrol the TPM 2.0 for unattended unlock of the data volume)
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }
: "${UNIT:?set UNIT=<unit id>, e.g. ben20-0007}"
: "${PODS:=8}"; : "${PLC_IP:=10.20.0.10}"; : "${ENABLE_WAN:=0}"; : "${SUPPORT_VPN:=0}"; : "${BACKUP_DEV:=}"; : "${NAS:=}"
: "${CTRL_IF:=enp1s0}"; : "${MGMT_IF:=enp2s0}"; : "${RCP_DEVS:=/dev/ttyACM0}"; : "${LUKS:=1}"
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
. /etc/os-release
case "$ID" in ubuntu|debian) ;; *) echo "unsupported OS $ID (Ubuntu LTS or Debian 12 expected)"; exit 1;; esac

echo "== [1/11] packages"
apt-get update
apt-get install -y mosquitto mosquitto-clients chrony nftables sqlite3 python3-venv python3-pip \
    dnsmasq logrotate wireguard-tools openssl unattended-upgrades cifs-utils \
    tpm2-tools clevis clevis-luks clevis-tpm2 cryptsetup \
    docker.io docker-compose-plugin \
    radvd avahi-daemon

echo "== [2/11] user, directories"
id ben >/dev/null 2>&1 || useradd -r -s /usr/sbin/nologin -d /var/lib/ben ben
mkdir -p /var/lib/ben/reports /var/log/ben /etc/ben /etc/ben/pki /mnt/ben-backup /opt
chown -R ben:ben /var/lib/ben /var/log/ben
[ -e /opt/ben_engine ] || ln -s "$REPO" /opt/ben_engine

echo "== [3/11] TPM 2.0 measured boot + LUKS data volume"
if [ "$LUKS" = 1 ]; then
    if ! tpm2_getcap properties-fixed >/dev/null 2>&1; then echo "no TPM 2.0 visible — enable fTPM/dTPM in BIOS"; exit 1; fi
    DATA_DEV=$(blkid -L BEN_DATA -o device 2>/dev/null || true)
    if [ -n "$DATA_DEV" ] && cryptsetup isLuks "$DATA_DEV"; then
        # bind to PCR 7 (Secure Boot state) + PCR 0,2 (firmware). A firmware change or Secure Boot off -> passphrase prompt.
        clevis luks list -d "$DATA_DEV" | grep -q tpm2 || clevis luks bind -d "$DATA_DEV" tpm2 '{"pcr_bank":"sha256","pcr_ids":"0,2,7"}'
        grep -q ben_data /etc/crypttab || echo "ben_data $DATA_DEV none luks,_netdev,initramfs" >> /etc/crypttab
        grep -q /var/lib/ben /etc/fstab || echo "/dev/mapper/ben_data /var/lib/ben ext4 defaults,nofail 0 2" >> /etc/fstab
        update-initramfs -u
        echo "LUKS volume bound to TPM 2.0 (PCR 0,2,7). Recovery passphrase goes in the turnover package."
    else
        echo "WARNING: no LUKS volume labelled BEN_DATA found. Create it at imaging time:"
        echo "  cryptsetup luksFormat /dev/nvme0n1p3 && cryptsetup open /dev/nvme0n1p3 ben_data && mkfs.ext4 -L BEN_DATA /dev/mapper/ben_data"
    fi
fi

echo "== [4/11] python service (ben_engine.api + plc bridge)"
python3 -m venv /opt/ben_engine/.venv
/opt/ben_engine/.venv/bin/pip install -q --upgrade pip
/opt/ben_engine/.venv/bin/pip install -q -e "$REPO" uvicorn fastapi paho-mqtt pymodbus pysnmp cryptography
API_PASS=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)
if [ ! -f /etc/ben/ben.env ]; then
    sed -e "s/^BEN_UNIT=.*/BEN_UNIT=$UNIT/" -e "s/^BEN_MQTT_PASS=.*/BEN_MQTT_PASS=$API_PASS/" -e "s/^BEN_PLC_IP=.*/BEN_PLC_IP=$PLC_IP/" "$HERE/ben.env.example" > /etc/ben/ben.env
    chown root:ben /etc/ben/ben.env; chmod 0640 /etc/ben/ben.env
fi
install -m 0644 "$REPO/firmware/ben-plc/modbus_map.csv" /etc/ben/modbus_map.csv

echo "== [5/11] network: controls VLAN 10.20.0.1/24 on $CTRL_IF, management 10.30.0.1/24 on $MGMT_IF, Thread prefix fd00:ben::/64"
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
IPv6AcceptRA=no
NET
cat > /etc/dnsmasq.d/ben.conf <<DNS
interface=$CTRL_IF
bind-interfaces
dhcp-range=10.20.0.100,10.20.0.199,12h
dhcp-option=option:ntp-server,10.20.0.1
dhcp-option=option:router      # no default route: the controls VLAN has no exit
DNS
sysctl -w net.ipv6.conf.all.forwarding=1 >/dev/null
echo "net.ipv6.conf.all.forwarding=1" > /etc/sysctl.d/60-ben-thread.conf
systemctl enable systemd-networkd dnsmasq

echo "== [6/11] PKI: unit CA for brokers/API, Device CA chain for Pods"
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
# Device CA chain (Schreiber AI root + Device CA intermediate). Pods present certificates from this chain.
# The Device CA private key lives in the HSM at the provisioning cell — it is NEVER on a unit.
[ -f device-ca-chain.crt ] || cp "$REPO/firmware/ben-edge/otbr/device-ca-chain.example.crt" device-ca-chain.crt
cat unit-ca.crt device-ca-chain.crt > trusted-clients.crt
chown -R mosquitto:mosquitto /etc/ben/pki; chmod 0600 /etc/ben/pki/*.key; cd "$HERE"

echo "== [7/11] mosquitto: mTLS listeners, CN-based ACL"
install -m 0644 "$HERE/mosquitto/ben.conf" /etc/mosquitto/conf.d/ben.conf
sed "s/__UNIT__/$UNIT/g" "$HERE/mosquitto/ben_acl.template" > /etc/mosquitto/ben_acl
touch /etc/mosquitto/ben_passwd
mosquitto_passwd -b /etc/mosquitto/ben_passwd benapi "$(grep ^BEN_MQTT_PASS= /etc/ben/ben.env | cut -d= -f2)"
mosquitto_passwd -b /etc/mosquitto/ben_passwd dashboard "$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)"
chown mosquitto:mosquitto /etc/mosquitto/ben_passwd /etc/mosquitto/ben_acl; chmod 0600 /etc/mosquitto/ben_passwd

echo "== [8/11] OpenThread Border Router (OTBR) with MGM240P RCP(s): $RCP_DEVS"
install -m 0644 "$HERE/otbr/otbr.env" /etc/ben/otbr.env
sed -i "s#^RCP_DEVS=.*#RCP_DEVS=\"$RCP_DEVS\"#; s#^CTRL_IF=.*#CTRL_IF=$CTRL_IF#" /etc/ben/otbr.env
install -m 0644 "$HERE/otbr/docker-compose.yml" /etc/ben/otbr-compose.yml
install -m 0644 "$HERE/otbr/radvd.conf" /etc/radvd.conf
install -m 0755 "$HERE/otbr/ben-thread-form.sh" /usr/local/sbin/ben-thread-form.sh
systemctl enable docker radvd

echo "== [9/11] chrony, firewall"
install -m 0644 "$HERE/chrony.conf" /etc/chrony/chrony.conf
install -m 0644 "$HERE/nftables.conf" /etc/ben/nftables.conf
sed -i "s/define CTRL   = \"enp1s0\"/define CTRL   = \"$CTRL_IF\"/; s/define MGMT   = \"enp2s0\"/define MGMT   = \"$MGMT_IF\"/" /etc/ben/nftables.conf
if [ "$ENABLE_WAN" = 1 ]; then
    echo "WAN enabled: apt/OTA fetch allowed outbound only (TCP 80/443, UDP 123, UDP 51820)"
    sed -i 's/ ct mark 0x5a//' /etc/ben/nftables.conf
fi
systemctl disable --now nftables 2>/dev/null || true   # we manage the ruleset via ben-firewall.service

echo "== [10/11] optional outbound-only support VPN"
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
        echo "Edge WireGuard public key (send to Schreiber AI support): $(cat /etc/wireguard/gw.pub)"
    fi
    echo "Support VPN installed but DOWN. Customer runs: ben-vpn-support.sh up"
else
    echo "Support VPN not installed (SUPPORT_VPN=0)"
fi
install -m 0755 "$HERE/scripts/ben-vpn-support.sh" /usr/local/sbin/ben-vpn-support.sh
install -m 0755 "$HERE/scripts/ben-add-pod.sh" /usr/local/sbin/ben-add-pod.sh

echo "== [11/11] backup target, services, log rotation, Pod joiner entries"
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
systemctl enable --now ben-firewall.service chrony mosquitto ben-otbr.service ben-api.service ben-plc-bridge.service ben-backup.timer
systemctl restart mosquitto
# Thread network: form once (dataset is kept in OTBR's persistent volume), then register the Pod joiners.
/usr/local/sbin/ben-thread-form.sh "$UNIT" || echo "Thread network not formed yet (RCP not attached?) — rerun ben-thread-form.sh $UNIT"
: > /root/ben-pod-provisioning.txt
for i in $(seq 1 "$PODS"); do "$HERE/scripts/ben-add-pod.sh" "$UNIT" "pod$i" | tee -a /root/ben-pod-provisioning.txt; done
chmod 0600 /root/ben-pod-provisioning.txt

echo
echo "BEN edge computer installed for unit $UNIT (Controls Pro) with $PODS Pod ACL entries."
echo "  Pod joiner/ACL records:  /root/ben-pod-provisioning.txt   (serial + PSKd are added per Pod with ben-add-pod.sh --serial)"
echo "  dashboard/API: https://10.30.0.1:8000   MQTT mTLS: [fd00:ben::1]:8883 (Pods) / 10.30.0.1:8883 (mgmt)   CA: /etc/ben/pki/unit-ca.crt"
echo "  PLC: Modbus TCP $PLC_IP:502 polled by ben-plc-bridge (map /etc/ben/modbus_map.csv)"
echo "  verify: systemctl status ben-api ben-plc-bridge ben-otbr mosquitto chrony ben-firewall ; nft list ruleset ; chronyc sources ; docker exec otbr ot-ctl state"
