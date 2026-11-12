#!/usr/bin/env bash
# Owner/operator only, after the US-24 launch choices and the Google grant (never run by an agent).
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="${SCRIPT_DIR}/systemd"
SYSTEMD_DIR="/etc/systemd/system"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer as root on the VPS." >&2
  exit 1
fi

for unit in la-lanh-human-tarot-sync.service la-lanh-human-tarot-sync.timer; do
  install -m 0644 "${UNIT_DIR}/${unit}" "${SYSTEMD_DIR}/${unit}"
done
install -m 0755 "${SCRIPT_DIR}/run-human-tarot-sync.sh" /usr/local/sbin/la-lanh-human-tarot-sync

systemctl daemon-reload
systemctl enable --now la-lanh-human-tarot-sync.timer
systemctl is-active --quiet la-lanh-human-tarot-sync.timer
echo "Lá Lành human Tarot sync timer is active."
