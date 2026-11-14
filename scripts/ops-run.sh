#!/bin/bash
# Fixed entry point for the la-lanh scheduled tasks (owner 08.11; moved into the repo 13.11, lesson L10).
# One allowlisted path instead of compound shell lines. Only the steps below; anything else is refused.
# Installed to ~/.cache/la-lanh-collab/ops-run.sh from the ops clone (reviewed collab/integration code)
# by `node scripts/collab-ops-wrapper.mjs --install`; the tick warns when the installed copy differs.
# Was zsh-only before (`(start|done)`, `<->`, unquoted paths), so `report` failed under bash.
set -uo pipefail
runtime="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies"
# /usr/bin/git first: the runtime fallback dir ships its own git.
export PATH="$runtime/node/bin:$HOME/.local/bin:/usr/bin:/bin:$PATH:$runtime/bin/fallback"
home_dir="${LA_LANH_COLLAB_HOME:-$HOME/.cache/la-lanh-collab}"
ops="$home_dir/ops"
clone="${LA_LANH_CLAUDE_CLONE:-$HOME/Documents/New project/la-lanh-claude}"

refresh() {
  git -C "$ops" fetch -q origin collab/integration && git -C "$ops" checkout -q --force --detach FETCH_HEAD
}

step="${1:-}"
[ $# -gt 0 ] && shift
case "$step" in
  status) refresh && cd "$clone" && node "$ops/scripts/collab-turn.mjs" --status ;;
  report) refresh && cd "$clone" && node "$ops/scripts/collab-turn.mjs" --report ;;
  busy) node "$ops/scripts/collab-check.mjs" --busy ;;
  beat)
    if [[ "${1:-}" == la-lanh-* && ( "${2:-}" == start || "${2:-}" == done ) ]]; then
      node "$ops/scripts/collab-watchdog.mjs" --beat "$1" "$2"
    else
      echo "ops-run: beat needs NAME (la-lanh-*) and start|done" >&2; exit 2
    fi ;;
  preflight)
    if [[ "${1:-}" =~ ^[1-9][0-9]*$ ]]; then
      cd "$clone" && node "$ops/scripts/collab-preflight.mjs" --pr "$1"
    else
      echo "ops-run: preflight needs a positive PR number" >&2; exit 2
    fi ;;
  *) echo "ops-run: unknown step '$step' (status|report|busy|beat NAME start|done|preflight N)" >&2; exit 2 ;;
esac
