#!/usr/bin/env bash
# Optional outbound-only WireGuard tunnel for Schreiber AI remote support.
# The edge computer initiates; nothing listens on WAN. Customer enables/disables it: `ben-vpn-support.sh up|down`.
# Status: implemented, unverified on hardware.
set -euo pipefail
case "${1:-}" in
  up)
    [ -f /etc/wireguard/wg0.conf ] || { echo "no /etc/wireguard/wg0.conf — run install.sh with SUPPORT_VPN=1"; exit 1; }
    systemctl start wg-quick@wg0; echo "support tunnel up (outbound only, 48 h auto-off)"
    systemd-run --on-active=48h --unit=ben-vpn-autooff /usr/bin/systemctl stop wg-quick@wg0 >/dev/null 2>&1 || true ;;
  down) systemctl stop wg-quick@wg0; systemctl stop ben-vpn-autooff.timer 2>/dev/null || true; echo "support tunnel down" ;;
  *) echo "usage: $0 up|down"; exit 2 ;;
esac
