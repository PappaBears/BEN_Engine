#!/usr/bin/env bash
# Form (once) the unit's Thread network on the OTBR and record the sealed dataset for the turnover package.
# Usage: ben-thread-form.sh <unit>       Idempotent: if a dataset exists it only prints the summary.
set -euo pipefail
unit=$1
otctl() { docker exec otbr ot-ctl "$@"; }
for i in $(seq 1 30); do otctl state >/dev/null 2>&1 && break; sleep 2; done
if otctl dataset active >/dev/null 2>&1 && otctl dataset active | grep -q "Network Key"; then
    echo "Thread network already formed: $(otctl state) / $(otctl networkname)"
else
    otctl dataset init new >/dev/null
    otctl dataset networkname "BEN-${unit}" >/dev/null
    otctl dataset channel 25 >/dev/null                 # 2.4 GHz ch 25 avoids Wi-Fi 1/6/11 overlap; survey at commissioning
    otctl dataset meshlocalprefix fd00:ben:0:0::/64 >/dev/null
    otctl dataset commit active >/dev/null
    otctl ifconfig up >/dev/null; otctl thread start >/dev/null
    sleep 8
    otctl prefix add fd00:ben::/64 paros >/dev/null     # OMR prefix: Pods get fd00:ben::xxxx, broker is fd00:ben::1 on the host
    otctl netdata register >/dev/null
    ip -6 addr add fd00:ben::1/64 dev wpan0 2>/dev/null || true
    echo "Thread network BEN-${unit} formed on channel 25"
fi
out=/root/ben-thread-dataset-${unit}.txt
{ echo "# BEN ${unit} Thread operational dataset — SEAL in the turnover package. Date $(date -Is)"; otctl dataset active; } > "$out"
chmod 0600 "$out"
echo "dataset recorded in $out (network key inside — treat as a secret)"
otctl commissioner start >/dev/null 2>&1 || true
