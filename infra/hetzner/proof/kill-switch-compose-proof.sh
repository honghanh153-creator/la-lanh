#!/usr/bin/env bash
# Real Docker Compose proof for the deploy kill switch (PR #40, audit O01). Run on a DISPOSABLE
# Docker host only: it refuses a Lá Lành server. It uses busybox images tagged as two fake
# releases and its own compose project, then removes everything it created.
#
# It checks the Compose behaviour deploy.sh relies on, which the fake-docker tests only model:
#   1. a running profiled worker survives `up -d --remove-orphans` without its profile (the bug);
#   2. `--profile generation rm -sf rewrite-worker` removes it and exits 0;
#   3. the same command with no worker is a successful no-op;
#   4. `LA_LANH_RELEASE_ID=<old> docker compose run` uses the old release image (preflight).
# Prints PASS/FAIL per check and exits non-zero on any FAIL.
set -euo pipefail

if [[ -e /opt/la-lanh ]]; then
  echo "Refusing: /opt/la-lanh exists. Run this on a disposable Docker host, never on a server." >&2
  exit 2
fi
command -v docker >/dev/null && docker compose version >/dev/null

PROJECT="la-lanh-killswitch-proof-$$"
WORK="$(mktemp -d)"
IMAGE="la-lanh-proof"
failures=0
cleanup() {
  docker compose -p "$PROJECT" -f "$WORK/compose.yaml" --profile generation down -v --remove-orphans \
    >/dev/null 2>&1 || true
  docker image rm "$IMAGE:old" "$IMAGE:new" >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

cat > "$WORK/compose.yaml" <<'YAML'
services:
  app:
    image: la-lanh-proof:${LA_LANH_RELEASE_ID:?}
    command: ["sleep", "3600"]
  rewrite-worker:
    profiles: ["generation"]
    image: la-lanh-proof:${LA_LANH_RELEASE_ID:?}
    command: ["sleep", "3600"]
YAML

docker pull -q busybox:1.36 >/dev/null
docker tag busybox:1.36 "$IMAGE:old"
docker tag busybox:1.36 "$IMAGE:new"
compose() { docker compose -p "$PROJECT" -f "$WORK/compose.yaml" "$@"; }
worker_running() { [[ -n "$(compose --profile generation ps -q rewrite-worker 2>/dev/null)" ]]; }
check() {
  if "$@"; then echo "PASS: $label"; else echo "FAIL: $label"; failures=$((failures + 1)); fi
}

export LA_LANH_RELEASE_ID=old
COMPOSE_PROFILES=generation compose up -d >/dev/null
label="setup: worker running with the generation profile"; check worker_running

COMPOSE_PROFILES= compose up -d --remove-orphans >/dev/null
label="1. profiled worker survives up --remove-orphans without its profile"; check worker_running

label="2. rm -sf rewrite-worker removes it and exits 0"
check bash -c "docker compose -p '$PROJECT' -f '$WORK/compose.yaml' --profile generation rm -sf rewrite-worker >/dev/null"
label="2b. no worker container remains"; check bash -c "! docker compose -p '$PROJECT' -f '$WORK/compose.yaml' --profile generation ps -q rewrite-worker | grep -q ."

label="3. rm -sf with no worker is a successful no-op"
check bash -c "docker compose -p '$PROJECT' -f '$WORK/compose.yaml' --profile generation rm -sf rewrite-worker >/dev/null"

export LA_LANH_RELEASE_ID=new
probe="$PROJECT-preflight"
LA_LANH_RELEASE_ID=old compose run -d --no-deps --name "$probe" app sleep 30 >/dev/null
used="$(docker inspect --format '{{.Config.Image}}' "$probe")"
docker rm -f "$probe" >/dev/null
label="4. LA_LANH_RELEASE_ID=old compose run uses $IMAGE:old (got $used)"
check test "$used" = "$IMAGE:old"

echo "Docker: $(docker version --format '{{.Server.Version}}'); Compose: $(docker compose version --short)"
if [[ "$failures" -ne 0 ]]; then
  echo "$failures check(s) failed" >&2
  exit 1
fi
echo "All kill-switch Compose checks passed."
