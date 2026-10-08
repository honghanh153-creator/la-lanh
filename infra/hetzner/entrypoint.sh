#!/bin/sh
set -eu

read_secret() {
  variable_name="$1"
  file_variable_name="${variable_name}_FILE"
  eval "secret_file=\${$file_variable_name:-}"
  if [ -z "$secret_file" ] || [ ! -r "$secret_file" ]; then
    echo "Missing readable secret file for ${variable_name}" >&2
    exit 1
  fi
  secret_value="$(cat "$secret_file")"
  if [ -z "$secret_value" ]; then
    echo "Secret file for ${variable_name} is empty" >&2
    exit 1
  fi
  export "${variable_name}=${secret_value}"
  unset secret_value secret_file
}

read_secret LA_LANH_DATABASE_URL
[ -z "${LA_LANH_GUEST_HASH_KEY_FILE:-}" ] || read_secret LA_LANH_GUEST_HASH_KEY
read_secret LA_LANH_GUEST_ENCRYPTION_KEY
[ -z "${LA_LANH_GENERATION_OPENAI_API_KEY_FILE:-}" ] || \
  read_secret LA_LANH_GENERATION_OPENAI_API_KEY

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec uvicorn app.cloud_run:app \
  --host 0.0.0.0 \
  --port 8080 \
  --proxy-headers \
  --forwarded-allow-ips='*' \
  --no-access-log
