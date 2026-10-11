#!/usr/bin/env bash
# Back up the application schema (public) to a root-only custom-format dump.
# The connection string is read inside the client container from the mounted
# secret file and is never printed, logged or passed as a host argument.
set -euo pipefail

SECRETS_DIR="${LA_LANH_SECRETS_DIR:-/opt/la-lanh/secrets}"
BACKUP_DIR="${LA_LANH_BACKUP_DIR:-/opt/la-lanh/backups}"
RETENTION_DAYS="${LA_LANH_BACKUP_RETENTION_DAYS:-14}"
PG_IMAGE="${LA_LANH_PG_CLIENT_IMAGE:-postgres:17-alpine}"

[[ -s "${SECRETS_DIR}/database_url" ]] || { echo "Missing database_url secret" >&2; exit 2; }
install -d -m 0700 "$BACKUP_DIR"
umask 077

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="${BACKUP_DIR}/la-lanh-${stamp}.dump"

docker run --rm --network host \
  -v "${SECRETS_DIR}/database_url:/run/secrets/database_url:ro" \
  "$PG_IMAGE" sh -ec '
    url="$(sed -e "s#^postgresql+asyncpg://#postgresql://#" -e "s#\([?&]\)ssl=#\1sslmode=#" /run/secrets/database_url)"
    exec pg_dump --format=custom --no-owner --schema=public --dbname="$url"
  ' > "${out}.partial"

mv "${out}.partial" "$out"
chmod 0600 "$out"
sha256sum "$out" > "${out}.sha256"
chmod 0600 "${out}.sha256"
echo "Backup written: ${out} ($(du -h "$out" | cut -f1))"

# Bounded retention: backups hold personal data and must not live forever.
find "$BACKUP_DIR" -maxdepth 1 -name 'la-lanh-*.dump*' -mtime +"$RETENTION_DAYS" -delete
