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

# Production generation settings never leak into staging: they are stripped and
# staging's own values come only from staging/generation.env when explicitly on.
sed -e "s#https://la-lanh.2-28-136-44.sslip.io#https://${STAGING_HOSTNAME}#" "$HERE/../app.env" \
  | { grep -v '^LA_LANH_GENERATION_' || true; } > "$HERE/app.env"
grep -q '^LA_LANH_AUTH_ENABLED=true' "$HERE/app.env" && { echo "Staging keeps auth disabled" >&2; exit 2; }
case "${STAGING_GENERATION:-off}" in
  off)
    echo "LA_LANH_GENERATION_ENABLED=false" >> "$HERE/app.env"
    unset COMPOSE_PROFILES || true
    ;;
  on)
    GEN_ENV="$HERE/generation.env"
    [[ -s "$GEN_ENV" ]] || { echo "STAGING_GENERATION=on needs $GEN_ENV" >&2; exit 2; }
    # Only plain LA_LANH_GENERATION_* settings; never the key, never the worker switch.
    if grep -Ev '^(LA_LANH_GENERATION_[A-Z0-9_]+=.*|#.*|)$' "$GEN_ENV" >/dev/null \
      || grep -Eq '^LA_LANH_GENERATION_(OPENAI_API_KEY|OPENAI_API_KEY_FILE|WORKER_ENABLED)=' "$GEN_ENV"; then
      echo "$GEN_ENV may only hold LA_LANH_GENERATION_* settings without key or worker switch" >&2
      exit 2
    fi
    KEY="$SECRETS/openai_api_key"
    [[ -s "$KEY" && ! -L "$KEY" ]] || { echo "Missing staging provider key file $KEY" >&2; exit 2; }
    [[ "$(stat -c '%u:%a' "$KEY")" == "65532:600" ]] \
      || { echo "$KEY must be owned by 65532 with mode 0600" >&2; exit 2; }
    cat "$GEN_ENV" >> "$HERE/app.env"
    export COMPOSE_PROFILES=generation
    ;;
  *) echo "STAGING_GENERATION must be on or off" >&2; exit 2 ;;
esac
chmod 0600 "$HERE/app.env"

cd "$HERE"
docker compose -f compose.staging.yaml up -d --wait db
# Migrations revoke browser access from Supabase's Data API roles; create them
# so a plain PostgreSQL matches production's grant model.
docker compose -f compose.staging.yaml exec -T db psql -q -U lalanh -d lalanh -v ON_ERROR_STOP=1 -c "
  DO \$\$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN CREATE ROLE anon NOLOGIN; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN CREATE ROLE service_role NOLOGIN; END IF;
  END \$\$;"
docker compose -f compose.staging.yaml run --rm --no-deps staging-app alembic upgrade head
docker compose -f compose.staging.yaml run --rm --no-deps staging-app python -m scripts.check_database_privacy
docker compose -f compose.staging.yaml up -d --wait staging-app
if [[ "${COMPOSE_PROFILES:-}" == "generation" ]]; then
  docker compose -f compose.staging.yaml up -d --wait staging-rewrite-worker
  # The provider key must exist only inside the worker.
  if docker compose -f compose.staging.yaml exec -T staging-app \
    python -c "import os, sys; sys.exit(0 if os.path.exists('/run/secrets/openai_api_key') else 1)"; then
    echo "staging-app must not mount the provider key; stopping the worker" >&2
    docker compose -f compose.staging.yaml stop staging-rewrite-worker
    exit 2
  fi
else
  # Kill switch: a worker left over from an earlier opt-in is removed.
  docker compose -f compose.staging.yaml --profile generation rm -sf staging-rewrite-worker >/dev/null 2>&1 || true
fi
# Guard: from Caddy's point of view, "app" must resolve to exactly one
# container (production). Anything else would split production traffic.
app_ips="$(docker exec la-lanh-caddy-1 nslookup app 127.0.0.11 2>/dev/null | awk '/^Name:/{n=1;next} n&&/^Address/{c++} END{print c+0}')"
if [[ "$app_ips" != "1" ]]; then
  echo "Production alias 'app' resolves to ${app_ips} containers; disconnecting staging" >&2
  docker network disconnect la-lanh_default la-lanh-staging-staging-app-1 || true
  exit 2
fi
echo "Staging ${LA_LANH_RELEASE_ID} is running behind https://${STAGING_HOSTNAME}"
