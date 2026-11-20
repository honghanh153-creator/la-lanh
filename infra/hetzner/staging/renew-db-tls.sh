#!/usr/bin/env bash
# Keep the staging database's own TLS pair from expiring (incident 2026-11-10: the 30-day pair from
# make-db-tls.sh expired and staging was down for about 44 hours with no warning).
#
# Daily, from la-lanh-staging-db-tls.timer:
# - if the server certificate and the CA are both valid for more than RENEW_DAYS, print the
#   expiry and exit 0;
# - otherwise make a new pair, keep one copy of the previous pair, stage the complete new pair as
#   tls.staged, write the new files in place, update the app's CA copy, restart the staging
#   database, app and (when running) the generation worker, and wait until each is healthy;
# - if an earlier run stopped anywhere after staging (while writing the files or before every
#   restart was healthy), write every file again from tls.staged and finish the restarts first.
# Any failure exits non-zero, so OnFailure= records an alert marker that la-lanh-ops-watch reports.
#
# Reads certificate dates only. Never prints keys, passwords or certificate contents.
# Staging only: production verifies Supabase's CA and has no pair of its own.
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SECRETS="${LA_LANH_STAGING_SECRETS_DIR:-/opt/la-lanh/staging/secrets}"
RENEW_DAYS="${LA_LANH_STAGING_TLS_RENEW_DAYS:-10}"
MAKE_TLS="${LA_LANH_MAKE_DB_TLS:-$HERE/../make-db-tls.sh}"
DB_CONTAINER="${LA_LANH_STAGING_DB_CONTAINER:-la-lanh-staging-db-1}"
APP_CONTAINER="${LA_LANH_STAGING_APP_CONTAINER:-la-lanh-staging-staging-app-1}"
WORKER_CONTAINER="${LA_LANH_STAGING_WORKER_CONTAINER:-la-lanh-staging-staging-rewrite-worker-1}"
HEALTH_TIMEOUT="${LA_LANH_STAGING_HEALTH_TIMEOUT_SECONDS:-180}"
TLS="$SECRETS/tls"
STAGED="$SECRETS/tls.staged"
APPLIED="$SECRETS/tls.applied"

[[ "$RENEW_DAYS" =~ ^[1-9][0-9]?$ && "$RENEW_DAYS" -lt 30 ]] \
  || { echo "LA_LANH_STAGING_TLS_RENEW_DAYS must be 1-29" >&2; exit 2; }
[[ "$HEALTH_TIMEOUT" =~ ^[1-9][0-9]*$ ]] \
  || { echo "Invalid LA_LANH_STAGING_HEALTH_TIMEOUT_SECONDS" >&2; exit 2; }
umask 077

window=$((RENEW_DAYS * 86400))
valid_beyond() { openssl x509 -checkend "$2" -noout -in "$1" >/dev/null 2>&1; }
not_after() { openssl x509 -enddate -noout -in "$1" | cut -d= -f2; }
# A complete pair: three regular non-empty files, the certificate signed by the CA and made for
# the key next to it. Compares public keys only; nothing is printed.
complete_pair() {
  local f
  for f in server.crt server.key ca.pem; do
    [[ -s "$1/$f" && ! -L "$1/$f" ]] || return 1
  done
  openssl verify -CAfile "$1/ca.pem" "$1/server.crt" >/dev/null 2>&1 || return 1
  [[ "$(openssl x509 -pubkey -noout -in "$1/server.crt" 2>/dev/null)" \
    == "$(openssl pkey -pubout -in "$1/server.key" 2>/dev/null)" ]]
}

health() { docker inspect --format '{{.State.Health.Status}}' "$1" 2>/dev/null || echo missing; }
wait_healthy() {
  local deadline=$((SECONDS + HEALTH_TIMEOUT))
  while (( SECONDS < deadline )); do
    [[ "$(health "$1")" == "healthy" ]] && return 0
    sleep 3
  done
  echo "$1 is not healthy ${HEALTH_TIMEOUT}s after the restart (status: $(health "$1"))" >&2
  return 1
}

# tls.staged is the whole new pair, put there by one rename before any live file changes, and it
# stays until every restart is healthy. A run that stopped half-way (between two file writes, or
# before a restart was healthy) is finished by the next run from tls.staged: every file is written
# again, so the database never starts on a certificate and key from two different pairs.
install_staged() {
  local f
  complete_pair "$STAGED" \
    || { echo "tls.staged is not a complete pair; restore tls/ from tls.prev-* by hand" >&2; exit 1; }
  # Write in place so the directory and file inodes the containers mount stay the same;
  # cp -p keeps the postgres owner (uid 70) and 0600 on the key when run as root.
  for f in ca.pem server.crt server.key; do
    cp -p "$STAGED/$f" "$TLS/$f"
  done
  # The app's CA copy keeps its own owner (65532) and 0600: overwrite the content only.
  cat "$TLS/ca.pem" > "$SECRETS/db_ca.pem"
}

# Every process that loaded the old CA or pair must restart.
activate() {
  docker restart "$DB_CONTAINER" >/dev/null
  wait_healthy "$DB_CONTAINER"
  docker restart "$APP_CONTAINER" >/dev/null
  wait_healthy "$APP_CONTAINER"
  # The optional generation worker loads db_ca.pem once at start. Restart it only when it runs;
  # never start a worker that the generation opt-in left off.
  if [[ -n "$(docker ps -q --filter "name=^/${WORKER_CONTAINER}\$")" ]]; then
    docker restart "$WORKER_CONTAINER" >/dev/null
    wait_healthy "$WORKER_CONTAINER"
  fi
  # One rename ends the renewal; a half-deleted tls.staged is never mistaken for a pending one.
  mv "$STAGED" "$APPLIED"
  rm -rf "$APPLIED"
}

rm -rf "$APPLIED"
for f in server.crt server.key ca.pem; do
  [[ -e "$TLS/$f" && ! -L "$TLS/$f" ]] || { echo "Staging TLS file missing: tls/$f" >&2; exit 1; }
done
[[ -e "$SECRETS/db_ca.pem" && ! -L "$SECRETS/db_ca.pem" ]] \
  || { echo "Staging app CA copy missing: db_ca.pem" >&2; exit 1; }

if [[ -e "$STAGED" ]]; then
  echo "Staging DB TLS: an earlier renewal did not finish; writing the staged pair again and restarting"
  install_staged
  activate
  echo "Staging DB TLS renewal finished: certificate valid until $(not_after "$TLS/server.crt")"
  exit 0
fi

# No renewal is pending, so an empty file here is damage, not a write that was cut short.
for f in server.crt server.key ca.pem; do
  [[ -s "$TLS/$f" ]] || { echo "Staging TLS file missing: tls/$f" >&2; exit 1; }
done
[[ -s "$SECRETS/db_ca.pem" ]] || { echo "Staging app CA copy missing: db_ca.pem" >&2; exit 1; }

if valid_beyond "$TLS/server.crt" "$window" && valid_beyond "$TLS/ca.pem" "$window" \
  && cmp -s "$TLS/ca.pem" "$SECRETS/db_ca.pem"; then
  echo "Staging DB TLS OK: certificate valid until $(not_after "$TLS/server.crt"); renews when under ${RENEW_DAYS} days"
  exit 0
fi

echo "Staging DB TLS renews now (certificate valid until $(not_after "$TLS/server.crt"))"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
new="$SECRETS/tls.new"
rm -rf "$new"
trap 'rm -rf "$new"' EXIT
"$MAKE_TLS" "$new" db
for f in server.crt server.key ca.pem; do
  [[ -s "$new/$f" ]] || { echo "New pair is missing $f; the current pair is unchanged" >&2; exit 1; }
done
complete_pair "$new" \
  || { echo "New certificate does not match its CA or key; the current pair is unchanged" >&2; exit 1; }
valid_beyond "$new/server.crt" "$window" \
  || { echo "New certificate is not valid beyond ${RENEW_DAYS} days; the current pair is unchanged" >&2; exit 1; }

# One previous pair only (it holds a private key): enough to diagnose, nothing more.
find "$SECRETS" -maxdepth 1 -name 'tls.prev-*' -type d -exec rm -rf {} +
cp -Rp "$TLS" "$SECRETS/tls.prev-$stamp"

# From this rename on, the next run finishes the renewal even if this one stops at any line.
mv "$new" "$STAGED"
install_staged
activate

echo "Staging DB TLS renewed: certificate valid until $(not_after "$TLS/server.crt"); previous pair kept as tls.prev-$stamp"
