#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:?Usage: smoke.sh https://your-hostname}"
BASE_URL="${BASE_URL%/}"

check_200() {
  local path="$1"
  curl --fail --silent --show-error --location --retry 4 --retry-all-errors \
    --retry-delay 2 -H 'Accept: text/html' "${BASE_URL}${path}" >/dev/null
}

check_200 /v1/health
check_200 /v1/ready
check_200 /welcome
check_200 /home
check_200 /radar

headers="$(curl --fail --silent --show-error --head \
  -H 'Accept: text/html' "${BASE_URL}/radar")"
grep -Eiq '^strict-transport-security:.*max-age=' <<<"$headers"
grep -Eiq '^referrer-policy:[[:space:]]*no-referrer' <<<"$headers"
grep -Eiq '^x-robots-tag:.*noindex' <<<"$headers"
grep -Eiq '^cache-control:.*no-store' <<<"$headers"

echo "Public smoke checks passed for ${BASE_URL}"
