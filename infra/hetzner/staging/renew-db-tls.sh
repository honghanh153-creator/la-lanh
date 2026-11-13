#!/usr/bin/env bash
# Keep the staging database's own TLS pair from expiring (incident 2026-11-10: the 30-day pair from
# make-db-tls.sh expired and staging was down for about 44 hours with no warning).
#
# Daily, from la-lanh-staging-db-tls.timer:
# - if the server certificate and the CA are both valid for more than RENEW_DAYS, print the
#   expiry and exit 0;
# - otherwise make a new pair, keep one copy of the previous pair, write the new files in place,
#   update the app's CA copy, restart the staging database, app and (when running) the generation
#   worker, and wait until each is healthy;
# - if an earlier run stopped before every restart was healthy, finish those restarts first.
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
PENDING="$SECRETS/tls.pending-restart"

[[ "$RENEW_DAYS" =~ ^[1-9][0-9]?$ && "$RENEW_DAYS" -lt 30 ]] \
  || { echo "LA_LANH_STAGING_TLS_RENEW_DAYS must be 1-29" >&2; exit 2; }
[[ "$HEALTH_TIMEOUT" =~ ^[1-9][0-9]*$ ]] \
  || { echo "Invalid LA_LANH_STAGING_HEALTH_TIMEOUT_SECONDS" >&2; exit 2; }
for f in server.crt server.key ca.pem; do
  [[ -s "$TLS/$f" && ! -L "$TLS/$f" ]] || { echo "Staging TLS file missing: tls/$f" >&2; exit 1; }
done
[[ -s "$SECRETS/db_ca.pem" && ! -L "$SECRETS/db_ca.pem" ]] \
  || { echo "Staging app CA copy missing: db_ca.pem" >&2; exit 1; }

window=$((RENEW_DAYS * 86400))
valid_beyond() { openssl x509 -checkend "$2" -noout -in "$1" >/dev/null 2>&1; }
not_after() { openssl x509 -enddate -noout -in "$1" | cut -d= -f2; }

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

# Every process that loaded the old CA or pair must restart. The marker is written before the new
# files go in and removed only after every restart is healthy, so a run that stopped half-way is
# finished by the next run instead of reporting fresh files on disk as success.
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
  rm -f "$PENDING"
}

if [[ -e "$PENDING" ]]; then
  echo "Staging DB TLS: an earlier renewal did not finish its restarts; restarting now"
  activate
  echo "Staging DB TLS restarts finished: certificate valid until $(not_after "$TLS/server.crt")"
  exit 0
fi

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
openssl verify -CAfile "$new/ca.pem" "$new/server.crt" >/dev/null 2>&1 \
  || { echo "New certificate does not verify against its CA; the current pair is unchanged" >&2; exit 1; }
valid_beyond "$new/server.crt" "$window" \
  || { echo "New certificate is not valid beyond ${RENEW_DAYS} days; the current pair is unchanged" >&2; exit 1; }

# One previous pair only (it holds a private key): enough to diagnose, nothing more.
umask 077
find "$SECRETS" -maxdepth 1 -name 'tls.prev-*' -type d -exec rm -rf {} +
cp -Rp "$TLS" "$SECRETS/tls.prev-$stamp"

: > "$PENDING"
# Write in place so the directory and file inodes the containers mount stay the same;
# cp -p keeps the postgres owner (uid 70) and 0600 on the key when run as root.
for f in ca.pem server.crt server.key; do
  cp -p "$new/$f" "$TLS/$f"
done
# The app's CA copy keeps its own owner (65532) and 0600: overwrite the content only.
cat "$TLS/ca.pem" > "$SECRETS/db_ca.pem"

activate

echo "Staging DB TLS renewed: certificate valid until $(not_after "$TLS/server.crt"); previous pair kept as tls.prev-$stamp"
