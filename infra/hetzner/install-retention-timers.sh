#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="${SCRIPT_DIR}/systemd"
SYSTEMD_DIR="/etc/systemd/system"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer as root on the VPS." >&2
  exit 1
fi

for unit in \
  la-lanh-guest-cleanup.service \
  la-lanh-guest-cleanup.timer \
  la-lanh-expired-cleanup.service \
  la-lanh-expired-cleanup.timer; do
  install -m 0644 "${UNIT_DIR}/${unit}" "${SYSTEMD_DIR}/${unit}"
done

install -m 0755 "${SCRIPT_DIR}/run-retention-job.sh" \
  /usr/local/sbin/la-lanh-retention-job

systemctl daemon-reload
systemctl enable --now la-lanh-guest-cleanup.timer la-lanh-expired-cleanup.timer
systemctl start la-lanh-guest-cleanup.service la-lanh-expired-cleanup.service

systemctl is-active --quiet la-lanh-guest-cleanup.timer
systemctl is-active --quiet la-lanh-expired-cleanup.timer
echo "Lá Lành retention timers are active."
