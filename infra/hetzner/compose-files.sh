#!/usr/bin/env bash

require_secret_file() {
  local path="$1"
  [[ -r "$path" && -s "$path" ]] || {
    echo "Missing nonempty readable secret file: $path" >&2
    return 2
  }
  [[ "$(stat -c '%a' "$path")" == "600" && "$(stat -c '%u:%g' "$path")" == "65532:65532" ]] || {
    echo "Secret file must use mode 0600 and owner 65532:65532: $path" >&2
    return 2
  }
}

select_compose_files() {
  local infra="$1"
  local secret="${LA_LANH_SECRETS_DIR:?}/supabase_admin_key"
  [[ -r "$infra/app.env" ]] || return 2
  COMPOSE_ARGS=(-f "$infra/compose.yaml")
  # Keep erasure available even when new sign-in has been disabled. Only the
  # app/cleanup process mounts the admin credential; the rewrite worker does not.
  if [[ -e "$secret" ]]; then
    require_secret_file "$secret" || return 2
    COMPOSE_ARGS+=(-f "$infra/compose.auth.yaml")
  elif grep -Eq '^LA_LANH_AUTH_ENABLED=true$' "$infra/app.env"; then
    echo "Auth requires a protected Supabase admin credential for identity erasure." >&2
    return 2
  fi
}
