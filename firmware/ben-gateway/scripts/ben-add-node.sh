#!/usr/bin/env bash
# Add (or rotate) a node's MQTT credential and ACL. Usage: ben-add-node.sh <unit> <nodeN> [password]
# Prints the serial provisioning line to paste into the node's USB console.
set -euo pipefail
unit=$1; node=$2; pass=${3:-$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)}
mosquitto_passwd -b /etc/mosquitto/ben_passwd "$node" "$pass"
if ! grep -q "^user $node\$" /etc/mosquitto/ben_acl; then
cat >> /etc/mosquitto/ben_acl <<ACL

user $node
topic write ben/$unit/node/$node/telemetry
topic write ben/$unit/node/$node/status
topic write ben/$unit/node/$node/ack
topic read  ben/$unit/node/$node/cmd
ACL
fi
systemctl kill -s HUP mosquitto.service || true
echo "Node credential set. Paste on the node's serial console (115200 8N1):"
echo "PROV unit=$unit node=$node broker=10.20.0.1 user=$node pass=$pass"
