#!/usr/bin/env bash
# BEN Engine edge computer — nightly consistent SQLite backup to USB stick or NAS mount.
# Data recovery is separate from code recovery (BRIEF.md §7.9): this file IS the unit's history.
# Status: implemented, unverified on hardware.
set -euo pipefail
: "${BEN_DB:=/var/lib/ben/ben.sqlite}"
: "${BEN_BACKUP_TARGET:=/mnt/ben-backup}"
: "${BEN_BACKUP_KEEP:=30}"
: "${BEN_UNIT:=unit0}"

ts=$(date +%Y%m%d-%H%M%S)
if ! mountpoint -q "$BEN_BACKUP_TARGET"; then
    echo "$ts BACKUP SKIPPED: $BEN_BACKUP_TARGET is not mounted (USB removed or NAS offline)"; exit 1
fi
dest="$BEN_BACKUP_TARGET/$BEN_UNIT"
mkdir -p "$dest"
tmp="$dest/ben-$ts.sqlite.tmp"
# Online, consistent copy even while the API is writing (uses the SQLite backup API).
sqlite3 "$BEN_DB" ".backup '$tmp'"
sqlite3 "$tmp" "PRAGMA integrity_check;" | grep -q '^ok$'
gzip -f "$tmp" && mv "$tmp.gz" "$dest/ben-$ts.sqlite.gz"
sha256sum "$dest/ben-$ts.sqlite.gz" > "$dest/ben-$ts.sqlite.gz.sha256"
# Also keep the calibration certificates / commissioning reports with the data.
if [ -d /var/lib/ben/reports ]; then tar czf "$dest/reports-$ts.tgz" -C /var/lib/ben reports; fi
# Prune beyond BEN_BACKUP_KEEP newest copies
ls -1t "$dest"/ben-*.sqlite.gz 2>/dev/null | tail -n +$((BEN_BACKUP_KEEP + 1)) | while read -r f; do rm -f "$f" "$f.sha256"; done
sync
echo "$ts BACKUP OK: $dest/ben-$ts.sqlite.gz ($(du -h "$dest/ben-$ts.sqlite.gz" | cut -f1))"
