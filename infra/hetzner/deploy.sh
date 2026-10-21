#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
source "${SCRIPT_DIR}/compose-files.sh"

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
select_compose_files "$SCRIPT_DIR"

if grep -Eq '^LA_LANH_SWISSEPH_LICENSE_MODE=development$' "${SCRIPT_DIR}/app.env"; then
  echo "Deployment blocked: approve AGPL or professional Swiss Ephemeris posture first." >&2
  exit 2
fi

cd "$REPO_ROOT"
docker compose "${COMPOSE_ARGS[@]}" config --quiet
docker compose "${COMPOSE_ARGS[@]}" build app
generation_enabled="$(
  docker compose "${COMPOSE_ARGS[@]}" run --rm --no-deps -T app \
    python -c 'from app.config import Settings; print(str(Settings().generation_enabled).lower())'
)"
case "$generation_enabled" in
  true)
    require_secret_file "${LA_LANH_SECRETS_DIR}/openai_api_key"
    export COMPOSE_PROFILES=generation
    ;;
  false)
    unset COMPOSE_PROFILES || true
    # Kill switch: a profiled worker is not an orphan, so `up --remove-orphans` would leave a
    # worker from an earlier generation=on release running with its old settings. Stop it first.
    docker compose "${COMPOSE_ARGS[@]}" --profile generation rm -sf rewrite-worker
    ;;
  *)
    echo "Deployment blocked: generation setting did not resolve to true or false." >&2
    exit 2
    ;;
esac
docker compose "${COMPOSE_ARGS[@]}" config --quiet
docker compose "${COMPOSE_ARGS[@]}" run --rm --no-deps app python -m scripts.check_database_tls
docker compose "${COMPOSE_ARGS[@]}" run --rm --no-deps app python -m scripts.review_content_release
docker compose "${COMPOSE_ARGS[@]}" run --rm --no-deps app alembic upgrade head
docker compose "${COMPOSE_ARGS[@]}" run --rm --no-deps app python -m scripts.check_database_privacy
docker compose "${COMPOSE_ARGS[@]}" up -d --remove-orphans --wait app
docker compose "${COMPOSE_ARGS[@]}" up -d --remove-orphans --wait

# Refresh the installed runner on every release, rather than leaving an old
# base-compose-only copy behind when Auth configuration changes.
if [[ "${EUID}" -eq 0 ]] && command -v systemctl >/dev/null; then
  install -m 0755 "${SCRIPT_DIR}/run-retention-job.sh" /usr/local/sbin/la-lanh-retention-job
fi

echo "Release ${LA_LANH_RELEASE_ID} is running for https://${APP_HOSTNAME}"
