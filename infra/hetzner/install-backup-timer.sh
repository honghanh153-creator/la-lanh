#!/usr/bin/env bash
# Operator step, run as root on the VPS from the active release: installs the daily backup timer,
# the six-hourly freshness check, the hourly deletion-journal copy and the failure marker unit,
# then runs one backup, one check and one journal copy.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="${SCRIPT_DIR}/systemd"
SYSTEMD_DIR="/etc/systemd/system"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer as root on the VPS." >&2
  exit 1
fi
[[ "$(readlink -f /opt/la-lanh/current)" == "$(readlink -f "${SCRIPT_DIR}/../..")" ]] || {
  echo "Run from the release that /opt/la-lanh/current points at." >&2
  exit 2
}

for unit in \
  la-lanh-backup.service \
  la-lanh-backup.timer \
  la-lanh-backup-check.service \
  la-lanh-backup-check.timer \
  la-lanh-erasure-journal.service \
  la-lanh-erasure-journal.timer \
  la-lanh-alert@.service; do
  install -m 0644 "${UNIT_DIR}/${unit}" "${SYSTEMD_DIR}/${unit}"
done
install -d -m 0700 /opt/la-lanh/backups

systemctl daemon-reload
systemctl enable --now la-lanh-backup.timer la-lanh-backup-check.timer la-lanh-erasure-journal.timer
systemctl start la-lanh-backup.service
systemctl start la-lanh-backup-check.service
systemctl start la-lanh-erasure-journal.service

systemctl is-active --quiet la-lanh-backup.timer
systemctl is-active --quiet la-lanh-backup-check.timer
systemctl is-active --quiet la-lanh-erasure-journal.timer
echo "Lá Lành backup, freshness check and deletion-journal copy timers are active."
