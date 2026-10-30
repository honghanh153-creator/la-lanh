#!/usr/bin/env bash
# One pass of the human Tarot Sheet bridge inside the running app container (US-24 U5).
# Uses the app's own environment and secrets; prints counts and closed error codes only.
set -euo pipefail

container="la-lanh-app-1"
image_ref="$(docker inspect --format '{{.Config.Image}}' "${container}")"
case "${image_ref}" in
  la-lanh:*) ;;
  *)
    echo "Unexpected production app image: ${image_ref}" >&2
    exit 2
    ;;
esac

exec docker exec "${container}" python -m scripts.sync_human_tarot
