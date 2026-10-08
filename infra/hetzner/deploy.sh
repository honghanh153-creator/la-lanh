#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/compose.yaml"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_file() {
  local path="$1"
  [[ -r "$path" ]] || {
    echo "Missing readable file: $path" >&2
    exit 1
  }
}

require_secret_file() {
  local path="$1"
  require_file "$path"
  [[ -s "$path" ]] || {
    echo "Secret file is empty: $path" >&2
    exit 1
  }
  [[ "$(stat -c '%a' "$path")" == "600" ]] || {
    echo "Secret file must use mode 0600: $path" >&2
    exit 1
  }
  [[ "$(stat -c '%u:%g' "$path")" == "65532:65532" ]] || {
    echo "Secret file must be owned by 65532:65532: $path" >&2
    exit 1
  }
}

require_command docker
require_command curl
require_command stat
docker compose version >/dev/null

export LA_LANH_RELEASE_ID="${LA_LANH_RELEASE_ID:-$(git -C "$REPO_ROOT" rev-parse --short=12 HEAD 2>/dev/null || date -u +%Y%m%d%H%M%S)}"
export APP_HOSTNAME="${APP_HOSTNAME:?Set APP_HOSTNAME to the public DNS hostname}"
export LA_LANH_SECRETS_DIR="${LA_LANH_SECRETS_DIR:-/opt/la-lanh/secrets}"

require_file "${SCRIPT_DIR}/app.env"
require_secret_file "${LA_LANH_SECRETS_DIR}/database_url"
require_secret_file "${LA_LANH_SECRETS_DIR}/guest_hash_key"
require_secret_file "${LA_LANH_SECRETS_DIR}/guest_encryption_key"

if grep -Eq '^LA_LANH_SWISSEPH_LICENSE_MODE=development$' "${SCRIPT_DIR}/app.env"; then
  echo "Deployment blocked: approve AGPL or professional Swiss Ephemeris posture first." >&2
  exit 2
fi

cd "$REPO_ROOT"
docker compose -f "$COMPOSE_FILE" config --quiet
docker compose -f "$COMPOSE_FILE" build app
generation_enabled="$(
  docker compose -f "$COMPOSE_FILE" run --rm --no-deps -T app \
    python -c 'from app.config import Settings; print(str(Settings().generation_enabled).lower())'
)"
case "$generation_enabled" in
  true)
    require_secret_file "${LA_LANH_SECRETS_DIR}/openai_api_key"
    export COMPOSE_PROFILES=generation
    ;;
  false)
    unset COMPOSE_PROFILES || true
    ;;
  *)
    echo "Deployment blocked: generation setting did not resolve to true or false." >&2
    exit 2
    ;;
esac
docker compose -f "$COMPOSE_FILE" config --quiet
docker compose -f "$COMPOSE_FILE" run --rm --no-deps app python -m scripts.check_database_tls
docker compose -f "$COMPOSE_FILE" run --rm --no-deps app python -m scripts.review_content_release
docker compose -f "$COMPOSE_FILE" run --rm --no-deps app alembic upgrade head
docker compose -f "$COMPOSE_FILE" run --rm --no-deps app python -m scripts.check_database_privacy
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans --wait app
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans --wait

echo "Release ${LA_LANH_RELEASE_ID} is running for https://${APP_HOSTNAME}"
