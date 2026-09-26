#!/usr/bin/env bash
set -euo pipefail

PROJECT_REF="${1:?Usage: configure-database.sh PROJECT_REF POOLER_HOST}"
POOLER_HOST="${2:?Usage: configure-database.sh PROJECT_REF POOLER_HOST}"
SECRETS_DIR="${LA_LANH_SECRETS_DIR:-/opt/la-lanh/secrets}"

if [[ ! "$PROJECT_REF" =~ ^[a-z0-9]{20}$ ]]; then
  echo "Invalid Supabase project reference." >&2
  exit 1
fi
if [[ ! "$POOLER_HOST" =~ ^[a-z0-9.-]+\.pooler\.supabase\.com$ ]]; then
  echo "Invalid Supabase pooler host." >&2
  exit 1
fi

read -r -s -p "Supabase database password (input hidden): " database_password
echo
if [[ -z "$database_password" ]]; then
  echo "Password cannot be empty." >&2
  exit 1
fi

encoded_password="$(printf '%s' "$database_password" | python3 -c \
  'import sys, urllib.parse; print(urllib.parse.quote(sys.stdin.read(), safe=""))')"
unset database_password

install -d -m 0700 "$SECRETS_DIR"
umask 077
printf '%s\n' \
  "postgresql+asyncpg://postgres.${PROJECT_REF}:${encoded_password}@${POOLER_HOST}:5432/postgres?ssl=require" \
  > "${SECRETS_DIR}/database_url"
unset encoded_password
chmod 0600 "${SECRETS_DIR}/database_url"
chown 65532:65532 "${SECRETS_DIR}/database_url"

echo "Database URL stored securely at ${SECRETS_DIR}/database_url"
