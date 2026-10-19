#!/usr/bin/env bash
# Helpers for rehearse-migration.sh (sourced, not executed).

# create_backend_role CONTAINER ROLE PASSWORD
# Creates the least-privileged backend login role in the disposable rehearsal database.
# The password never reaches a process argument list: it is written to psql's stdin as a
# `\set` meta-command by bash builtins (printf is a builtin, so no child process carries it),
# and `PASSWORD :'pw'` makes psql quote it as an SQL literal.
create_backend_role() {
  local container="$1" role="$2" password="$3"
  [[ "$role" =~ ^[a-z_][a-z0-9_]{0,62}$ ]] || { echo "Invalid backend role name" >&2; return 1; }
  [[ "$password" =~ ^[A-Za-z0-9]{16,}$ ]] || { echo "Invalid backend password" >&2; return 1; }
  {
    printf '\\set role %s\n' "$role"
    printf "\\\\set pw '%s'\n" "$password"
    cat <<'SQL'
CREATE ROLE :"role" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
  PASSWORD :'pw';
ALTER SCHEMA public OWNER TO :"role";
GRANT CONNECT, TEMPORARY ON DATABASE rehearsal TO :"role";
SQL
  } | docker exec -i "$container" psql -q -U postgres -d rehearsal -v ON_ERROR_STOP=1
}
