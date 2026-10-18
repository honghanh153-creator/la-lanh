#!/usr/bin/env bash
# Rehearse a release migration on a disposable copy of the latest backup.
#
# Restores the newest dump into a throwaway PostgreSQL container on a private
# Docker network (with the Supabase browser roles present so grants restore),
# runs the release image's `alembic upgrade head`, the privacy isolation check,
# the Tarot variant cursor rehearsal and a private readiness probe, then
# destroys the container and its data. Nothing touches the production
# database. Credentials stay inside containers.
#
# The app side (migrations, checks, readiness) connects as a least-privileged
# backend role, never as the container superuser: like Supabase's pooler role
# in production it owns the restored public tables but is NOSUPERUSER (and,
# stricter than production, NOBYPASSRLS / NOCREATEROLE / NOCREATEDB).
set -euo pipefail

: "${LA_LANH_RELEASE_ID:?Set LA_LANH_RELEASE_ID to the release image tag}"
BACKUP_DIR="${LA_LANH_BACKUP_DIR:-/opt/la-lanh/backups}"
SECRETS_DIR="${LA_LANH_SECRETS_DIR:-/opt/la-lanh/secrets}"
PG_IMAGE="${LA_LANH_PG_IMAGE:-postgres:17-alpine}"
IMAGE="la-lanh:${LA_LANH_RELEASE_ID}"
NAME="la-lanh-rehearsal-$$"
NET="${NAME}-net"
BACKEND_ROLE="la_lanh_rehearsal_backend"
# shellcheck source=rehearsal-lib.sh
source "$(dirname "$0")/rehearsal-lib.sh"

dump="$(ls -1t "${BACKUP_DIR}"/la-lanh-*.dump 2>/dev/null | head -n1)"
[[ -n "$dump" ]] || { echo "No backup found in ${BACKUP_DIR}" >&2; exit 2; }
sha256sum --check --status "${dump}.sha256" || { echo "Backup checksum mismatch" >&2; exit 2; }
docker image inspect "$IMAGE" >/dev/null

cleanup() {
  docker rm -f "$NAME" "${NAME}-app" >/dev/null 2>&1 || true
  docker network rm "$NET" >/dev/null 2>&1 || true
}
trap cleanup EXIT

password="$(head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9')"
tls_dir="$(mktemp -d)"
"$(dirname "$0")/make-db-tls.sh" "$tls_dir" "$NAME"
docker network create --internal "$NET" >/dev/null
docker run -d --name "$NAME" --network "$NET" --tmpfs /var/lib/postgresql/data \
  -v "${tls_dir}:/tls:ro" \
  -e POSTGRES_PASSWORD="$password" -e POSTGRES_DB=rehearsal "$PG_IMAGE" \
  -c ssl=on -c ssl_cert_file=/tls/server.crt -c ssl_key_file=/tls/server.key >/dev/null
sleep 2
docker ps --filter "name=^${NAME}$" --format '{{.Names}}' | grep -q . || { docker logs "$NAME" >&2; exit 1; }
for _ in $(seq 1 60); do
  docker exec "$NAME" pg_isready -U postgres -d rehearsal >/dev/null 2>&1 && break
  sleep 1
done

docker exec "$NAME" psql -q -U postgres -d rehearsal -v ON_ERROR_STOP=1 -c "
  CREATE ROLE anon NOLOGIN; CREATE ROLE authenticated NOLOGIN; CREATE ROLE service_role NOLOGIN;"
backend_password="$(head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9')"
# The password reaches psql on stdin only (see rehearsal-lib.sh), never a process argument.
create_backend_role "$NAME" "$BACKEND_ROLE" "$backend_password"
# Objects are created as the backend role, so it owns them as the pooler role does in production.
docker exec -i "$NAME" pg_restore -U postgres -d rehearsal --no-owner --role="$BACKEND_ROLE" \
  < "$dump" || \
  echo "pg_restore reported non-fatal warnings (missing Supabase-only objects are expected)"
foreign_owned="$(docker exec "$NAME" psql -tA -U postgres -d rehearsal -c \
  "select count(*) from pg_tables where schemaname = 'public' and tableowner <> '${BACKEND_ROLE}'")"
[[ "$foreign_owned" == "0" ]] || { echo "Restored tables not owned by the backend role" >&2; exit 1; }
echo "Restored rows: guest_sessions=$(docker exec "$NAME" psql -tA -U postgres -d rehearsal -c 'select count(*) from guest_sessions')"
echo "Head before: $(docker exec "$NAME" psql -tA -U postgres -d rehearsal -c 'select version_num from alembic_version')"

secret_dir="$(mktemp -d)"
chmod 0700 "$secret_dir"
printf 'postgresql+asyncpg://%s:%s@%s:5432/rehearsal?sslrootcert=/run/secrets/db_ca.pem' \
  "$BACKEND_ROLE" "$backend_password" "$NAME" > "${secret_dir}/database_url"
cp "${SECRETS_DIR}/guest_hash_key" "${SECRETS_DIR}/guest_encryption_key" "$secret_dir/"
cp "${tls_dir}/ca.pem" "${secret_dir}/db_ca.pem"
chown -R 65532:65532 "$secret_dir"
chmod 0600 "$secret_dir"/*
trap 'rm -rf "$secret_dir" "$tls_dir"; cleanup' EXIT

run_app() {
  docker run --rm --network "$NET" --env-file "$(dirname "$0")/app.env" \
    -e LA_LANH_DATABASE_URL_FILE=/run/secrets/database_url \
    -e LA_LANH_GUEST_HASH_KEY_FILE=/run/secrets/guest_hash_key \
    -e LA_LANH_GUEST_ENCRYPTION_KEY_FILE=/run/secrets/guest_encryption_key \
    -e LA_LANH_AUTH_ENABLED=false -e LA_LANH_GENERATION_ENABLED=false \
    -v "${secret_dir}:/run/secrets:ro" \
    -v "$(dirname "$0")/entrypoint.sh:/usr/local/bin/la-lanh-entrypoint:ro" \
    --entrypoint /usr/local/bin/la-lanh-entrypoint "$IMAGE" "$@"
}

run_app alembic upgrade head
echo "Head after: $(docker exec "$NAME" psql -tA -U postgres -d rehearsal -c 'select version_num from alembic_version')"
run_app python -m scripts.check_database_privacy
echo "Rows after: guest_sessions=$(docker exec "$NAME" psql -tA -U postgres -d rehearsal -c 'select count(*) from guest_sessions')"
# Tarot B2 (US-20): backend role is not a superuser, cursor table isolated, concurrent starts get
# distinct positions, deletion/cleanup keep the cursor, guest deletion removes it. Synthetic data;
# its far-future cleanup also purges the copy's Tarot sessions, so it runs after the row counts.
run_app python -m scripts.rehearse_tarot_cursor

docker run -d --name "${NAME}-app" --network "$NET" --env-file "$(dirname "$0")/app.env" \
  -e LA_LANH_DATABASE_URL_FILE=/run/secrets/database_url \
  -e LA_LANH_GUEST_HASH_KEY_FILE=/run/secrets/guest_hash_key \
  -e LA_LANH_GUEST_ENCRYPTION_KEY_FILE=/run/secrets/guest_encryption_key \
  -e LA_LANH_AUTH_ENABLED=false -e LA_LANH_GENERATION_ENABLED=false \
  -v "${secret_dir}:/run/secrets:ro" \
  -v "$(dirname "$0")/entrypoint.sh:/usr/local/bin/la-lanh-entrypoint:ro" \
  --entrypoint /usr/local/bin/la-lanh-entrypoint "$IMAGE" >/dev/null
for _ in $(seq 1 60); do
  if docker exec "${NAME}-app" python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8080/v1/ready',timeout=4).read().decode())" 2>/dev/null; then
    echo "Rehearsal readiness OK"
    exit 0
  fi
  sleep 2
done
echo "Rehearsal app never became ready" >&2
docker logs --tail 40 "${NAME}-app" >&2
exit 1
