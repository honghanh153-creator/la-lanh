#!/usr/bin/env bash
# Start or update the staging stack with an already-built release image.
# Creates staging-only secrets on first run (never shared with production).
set -euo pipefail

: "${LA_LANH_RELEASE_ID:?Set LA_LANH_RELEASE_ID}"
: "${STAGING_HOSTNAME:?Set STAGING_HOSTNAME, e.g. staging.la-lanh.2-28-136-44.sslip.io}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SECRETS="${LA_LANH_STAGING_SECRETS_DIR:-/opt/la-lanh/staging/secrets}"
export LA_LANH_STAGING_SECRETS_DIR="$SECRETS"

install -d -m 0700 "$SECRETS"
umask 077
new_secret() { [[ -s "$SECRETS/$1" ]] || head -c 32 /dev/urandom | base64 | tr '+/' '-_' | tr -d '=\n' > "$SECRETS/$1"; }
new_secret guest_hash_key
new_secret guest_encryption_key
if [[ ! -s "$SECRETS/db_password" ]]; then
  head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' > "$SECRETS/db_password"
fi
[[ -s "$SECRETS/tls/server.crt" ]] || "$HERE/../make-db-tls.sh" "$SECRETS/tls" db
cp "$SECRETS/tls/ca.pem" "$SECRETS/db_ca.pem"
printf 'postgresql+asyncpg://lalanh:%s@db:5432/lalanh?sslrootcert=/run/secrets/db_ca.pem' "$(cat "$SECRETS/db_password")" > "$SECRETS/database_url"
chown 65532:65532 "$SECRETS"/guest_hash_key "$SECRETS"/guest_encryption_key "$SECRETS"/database_url "$SECRETS"/db_ca.pem
chown 70:70 "$SECRETS/db_password"   # postgres user in the alpine image
chmod 0600 "$SECRETS"/guest_hash_key "$SECRETS"/guest_encryption_key "$SECRETS"/database_url "$SECRETS"/db_ca.pem "$SECRETS"/db_password

sed -e "s#https://la-lanh.2-28-136-44.sslip.io#https://${STAGING_HOSTNAME}#" "$HERE/../app.env" > "$HERE/app.env"
grep -q '^LA_LANH_AUTH_ENABLED=true' "$HERE/app.env" && { echo "Staging keeps auth disabled" >&2; exit 2; }
chmod 0600 "$HERE/app.env"

cd "$HERE"
docker compose -f compose.staging.yaml up -d --wait db
docker compose -f compose.staging.yaml run --rm --no-deps app alembic upgrade head
docker compose -f compose.staging.yaml up -d --wait app
echo "Staging ${LA_LANH_RELEASE_ID} is running behind https://${STAGING_HOSTNAME}"
