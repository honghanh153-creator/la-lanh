#!/usr/bin/env bash
set -euo pipefail

job="${1:?Usage: run-retention-job.sh guests|expired}"
compose_file="/opt/la-lanh/current/infra/hetzner/compose.yaml"
image_ref="$(docker inspect --format '{{.Config.Image}}' la-lanh-app-1)"

case "${image_ref}" in
  la-lanh:*) release_id="${image_ref#la-lanh:}" ;;
  *)
    echo "Unexpected production app image: ${image_ref}" >&2
    exit 2
    ;;
esac

export APP_HOSTNAME="la-lanh.2-28-136-44.sslip.io"
export LA_LANH_RELEASE_ID="${release_id}"
export LA_LANH_SECRETS_DIR="/opt/la-lanh/secrets"

case "${job}" in
  guests)
    module="scripts.cleanup_guests"
    ;;
  expired)
    module="scripts.cleanup_expired"
    ;;
  *)
    echo "Unknown retention job: ${job}" >&2
    exit 2
    ;;
esac

exec docker compose --project-name la-lanh -f "${compose_file}" \
  run --rm --no-deps app python -m "${module}" --batch-size 500
