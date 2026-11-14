#!/usr/bin/env bash
# Operator step, run as root on the VPS from the staging source copy that up.sh uses
# (/opt/la-lanh/staging/source): installs the daily staging DB TLS renewal timer and the shared
# failure marker unit, then runs one check.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="${SCRIPT_DIR}/../systemd"
SYSTEMD_DIR="/etc/systemd/system"
EXPECTED="/opt/la-lanh/staging/source/infra/hetzner/staging"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer as root on the VPS." >&2
  exit 1
fi
[[ "$(readlink -f "$SCRIPT_DIR")" == "$(readlink -f "$EXPECTED")" ]] || {
  echo "Run from ${EXPECTED}, the copy the timer executes." >&2
  exit 2
}

for unit in la-lanh-staging-db-tls.service la-lanh-staging-db-tls.timer la-lanh-alert@.service; do
  install -m 0644 "${UNIT_DIR}/${unit}" "${SYSTEMD_DIR}/${unit}"
done

systemctl daemon-reload
systemctl enable --now la-lanh-staging-db-tls.timer
systemctl start la-lanh-staging-db-tls.service
systemctl is-active --quiet la-lanh-staging-db-tls.timer
echo "Staging DB TLS renewal timer is active."
