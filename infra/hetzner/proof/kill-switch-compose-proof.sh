#!/usr/bin/env bash
# Real Docker Compose proof for the deploy kill switch (PR #40, audit O01). Run on a DISPOSABLE
# Docker host only. It is opt-in and refuses anything it cannot verify as local and disposable.
#
# Opt in explicitly, on the disposable machine itself:
#   LA_LANH_KILL_SWITCH_PROOF=1 LA_LANH_PROOF_DOCKER_CONTEXT=<context> \
#     bash infra/hetzner/proof/kill-switch-compose-proof.sh
# where <context> is the output of `docker context show` on that machine. It refuses when
# DOCKER_HOST/DOCKER_CONTEXT are set, when the context is not the named one, when the context
# endpoint is not a local socket (a remote daemon would make the /opt/la-lanh guard meaningless),
# when the daemon is unreachable, or when Lá Lành containers exist. After the check, every Docker
# command in the run is pinned to that endpoint via DOCKER_HOST. Each run uses its own compose
# project and image tags and removes only what it created.
#
# It checks the Compose behaviour deploy.sh relies on, which the fake-docker tests only model:
#   1. a running profiled worker survives `up -d --remove-orphans` without its profile (the bug);
#   2. `--profile generation rm -sf rewrite-worker` removes it and exits 0;
#   3. the same command with no worker is a successful no-op;
#   4. `LA_LANH_RELEASE_ID=<old> docker compose run` uses the old release image (preflight).
# Prints PASS/FAIL per check and exits non-zero on any FAIL.
# Exit codes: 0 pass, 1 check failed, 2 looks like a Lá Lành server, 3 not opted in,
# 4 Docker target not verified as local/disposable, 5 Docker daemon or Compose unavailable.
set -euo pipefail

refuse() { echo "Refusing: $2" >&2; exit "$1"; }

if [[ "${LA_LANH_KILL_SWITCH_PROOF:-}" != "1" ]]; then
  echo "Skipped: set LA_LANH_KILL_SWITCH_PROOF=1 and LA_LANH_PROOF_DOCKER_CONTEXT on a disposable Docker host." >&2
  exit 3
fi
if [[ -e /opt/la-lanh ]]; then
  refuse 2 "/opt/la-lanh exists. Run this on a disposable Docker host, never on a server."
fi
command -v docker >/dev/null || refuse 5 "docker CLI not found."
[[ -z "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" ]] \
  || refuse 4 "unset DOCKER_HOST and DOCKER_CONTEXT; select the disposable context with 'docker context use'."
expected="${LA_LANH_PROOF_DOCKER_CONTEXT:-}"
[[ -n "$expected" ]] || refuse 4 "set LA_LANH_PROOF_DOCKER_CONTEXT to the disposable context name."
current="$(docker context show)"
[[ "$current" == "$expected" ]] || refuse 4 "current Docker context '$current' is not '$expected'."
endpoint="$(docker context inspect --format '{{.Endpoints.docker.Host}}' "$current")"
case "$endpoint" in
  unix://*|npipe://*) ;;
  *) refuse 4 "context '$current' points to '$endpoint', not a local Docker socket." ;;
esac
# Pin every later Docker command to the endpoint just verified: the daemon probe, the container
# inventory, the child `bash -c` checks and the cleanup trap all inherit DOCKER_HOST. A
# `docker context use` (or `docker context update`) in another terminal can no longer redirect
# this run to a daemon that was not checked.
export DOCKER_HOST="$endpoint"
docker info --format '{{.ServerVersion}}' >/dev/null 2>&1 \
  || refuse 5 "the Docker daemon for context '$current' is not reachable."
docker compose version >/dev/null 2>&1 || refuse 5 "docker compose is not available."
if docker ps -a --format '{{.Names}}' | grep '^la-lanh' | grep -vq '^la-lanh-killswitch-proof-'; then
  refuse 2 "Lá Lành containers exist on this Docker host; use a disposable one."
fi

RUN_ID="$(date +%Y%m%d%H%M%S)-$$-${RANDOM}"
PROJECT="la-lanh-killswitch-proof-$RUN_ID"
IMAGE="la-lanh-proof-$RUN_ID"
export PROOF_IMAGE="$IMAGE"
WORK="$(mktemp -d)"
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
    image: ${PROOF_IMAGE:?}:${LA_LANH_RELEASE_ID:?}
    command: ["sleep", "3600"]
  rewrite-worker:
    profiles: ["generation"]
    image: ${PROOF_IMAGE:?}:${LA_LANH_RELEASE_ID:?}
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
