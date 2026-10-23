#!/usr/bin/env bash
# Hourly host-side copy of the deletion journal (audit P07, option A). Dumps exclude the journal's
# rows, and a restore or provider PITR rewinds the database, so this file is what carries the
# erasures made after the last backup. It holds keyed digests, kinds, scopes and times only.
set -euo pipefail

BACKUP_DIR="${LA_LANH_BACKUP_DIR:-/opt/la-lanh/backups}"
JOURNAL_DIR="${BACKUP_DIR}/erasure-journal"
KEEP_DAYS="${LA_LANH_JOURNAL_EXPORT_KEEP_DAYS:-2}"
infra="/opt/la-lanh/current/infra/hetzner"
source "$infra/compose-files.sh"

image_ref="$(docker inspect --format '{{.Config.Image}}' la-lanh-app-1)"
case "${image_ref}" in
  la-lanh:*) release_id="${image_ref#la-lanh:}" ;;
  *) echo "Unexpected production app image: ${image_ref}" >&2; exit 2 ;;
esac
export APP_HOSTNAME="la-lanh.2-28-136-44.sslip.io"
export LA_LANH_RELEASE_ID="${release_id}"
export LA_LANH_SECRETS_DIR="/opt/la-lanh/secrets"
select_compose_files "$infra"

install -d -m 0700 "$JOURNAL_DIR"
umask 077
out="${JOURNAL_DIR}/journal-$(date -u +%Y%m%dT%H%M%SZ).jsonl"
run() {
  docker compose --project-name la-lanh "${COMPOSE_ARGS[@]}" \
    run --rm --no-deps -T app python -m scripts.erasure_journal "$@"
}
run export > "${out}.partial"
mv "${out}.partial" "$out"
chmod 0600 "$out"
echo "Journal exported: $(wc -l < "$out" | tr -d ' ') entr(y/ies) to ${out}"

# Entries older than the oldest restorable backup are no longer needed (setting
# LA_LANH_ERASURE_JOURNAL_RETENTION_DAYS, at least 15). Each export holds every live entry, so
# older export files only guard against a damaged newest file; keep a short window of them.
run purge
find "$JOURNAL_DIR" -maxdepth 1 -name 'journal-*.jsonl' -mtime +"$KEEP_DAYS" ! -samefile "$out" -delete
