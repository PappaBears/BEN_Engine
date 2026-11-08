#!/usr/bin/env bash
# Register a BEN Pod on this unit: broker ACL entry keyed on its certificate CN, and (with --serial) the
# Thread Commissioner joiner entry for its EUI-64 + PSKd. Also issues/renews a device certificate when
# the unit runs the Device CA locally (--renew: CSR from the Pod, key stays in its Secure Vault).
#
#   ben-add-pod.sh <unit> <podN>                               # ACL only (install time)
#   ben-add-pod.sh <unit> <podN> --serial <serial> --eui64 <hex16> --pskd <PSKd from label>
#   ben-add-pod.sh <unit> <podN> --renew <csr.pem>             # emits a new cert via the Device CA (if present)
#   ben-add-pod.sh <unit> <podN> --revoke                      # removes ACL + joiner; Pod's next TLS handshake fails
set -euo pipefail
unit=$1; pod=$2; shift 2
serial=""; eui=""; pskd=""; csr=""; revoke=0
while [ $# -gt 0 ]; do case "$1" in
  --serial) serial=$2; shift 2;; --eui64) eui=$2; shift 2;; --pskd) pskd=$2; shift 2;;
  --renew) csr=$2; shift 2;; --revoke) revoke=1; shift;; *) echo "unknown option $1"; exit 2;; esac; done
cn="pod-$unit-$pod"
acl=/etc/mosquitto/ben_acl
otctl() { docker exec otbr ot-ctl "$@" 2>/dev/null || /usr/local/bin/ot-ctl "$@"; }

if [ "$revoke" = 1 ]; then
    sed -i "/^user $cn\$/,/^topic read .*\/$pod\/cmd\$/d" "$acl"
    [ -n "$eui" ] && otctl commissioner joiner remove "$eui" || true
    systemctl kill -s HUP mosquitto.service || true
    echo "revoked $cn"; exit 0
fi

if ! grep -q "^user $cn\$" "$acl"; then
cat >> "$acl" <<ACL

user $cn
topic write ben/$unit/node/$pod/telemetry
topic write ben/$unit/node/$pod/status
topic write ben/$unit/node/$pod/ack
topic read  ben/$unit/node/$pod/cmd
ACL
fi
systemctl kill -s HUP mosquitto.service || true

if [ -n "$pskd" ]; then
    [ -n "$eui" ] || { echo "--eui64 required with --pskd"; exit 2; }
    otctl commissioner start >/dev/null || true
    otctl commissioner joiner add "$eui" "$pskd" 600 >/dev/null        # 10 min join window
    echo "joiner window open 600 s for EUI-64 $eui"
fi

if [ -n "$csr" ]; then
    ca=/etc/ben/pki/device-ca.crt; key=/etc/ben/pki/device-ca.key
    [ -f "$key" ] || { echo "Device CA key is not on this unit (it lives in the HSM). Send the CSR to the provisioning cell."; exit 3; }
    out="/var/lib/ben/reports/${cn}-$(date +%Y%m%d).crt"
    openssl x509 -req -in "$csr" -CA "$ca" -CAkey "$key" -CAcreateserial -days 1825 -out "$out" \
        -extfile <(printf "subjectAltName=DNS:%s\nextendedKeyUsage=clientAuth\n" "$cn")
    echo "renewed certificate: $out (serial $(openssl x509 -in "$out" -noout -serial | cut -d= -f2))"
fi

echo "POD unit=$unit node=$pod cn=$cn serial=${serial:-?} eui64=${eui:-?} broker=[fd00:ben::1]:8883"
