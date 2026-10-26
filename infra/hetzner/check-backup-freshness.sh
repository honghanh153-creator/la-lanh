#!/usr/bin/env bash
# Fail (non-zero) unless the newest Lá Lành backup is recent, non-empty and matches its checksum.
# Reads only file names, ages, sizes and checksums; never opens the dump contents.
set -euo pipefail

BACKUP_DIR="${LA_LANH_BACKUP_DIR:-/opt/la-lanh/backups}"
MAX_AGE_HOURS="${LA_LANH_BACKUP_MAX_AGE_HOURS:-26}"

[[ "$MAX_AGE_HOURS" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid LA_LANH_BACKUP_MAX_AGE_HOURS" >&2; exit 2; }
[[ -d "$BACKUP_DIR" ]] || { echo "Backup directory missing: $BACKUP_DIR" >&2; exit 1; }

newest="$(ls -1t "$BACKUP_DIR"/la-lanh-*.dump 2>/dev/null | head -n 1 || true)"
[[ -n "$newest" ]] || { echo "No backup found in $BACKUP_DIR" >&2; exit 1; }
[[ -s "$newest" ]] || { echo "Newest backup is empty: $(basename "$newest")" >&2; exit 1; }
[[ -s "${newest}.sha256" ]] || { echo "Checksum file missing: $(basename "$newest").sha256" >&2; exit 1; }

if [[ -z "$(find "$newest" -maxdepth 0 -mmin "-$((MAX_AGE_HOURS * 60))")" ]]; then
  echo "Newest backup is older than ${MAX_AGE_HOURS}h: $(basename "$newest")" >&2
  exit 1
fi

(cd "$BACKUP_DIR" && sha256sum --check --status "$(basename "$newest").sha256") || {
  echo "Backup checksum mismatch: $(basename "$newest")" >&2
  exit 1
}

echo "Backup OK: $(basename "$newest") (under ${MAX_AGE_HOURS}h, checksum verified)"
