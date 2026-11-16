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

# Owner 16.11.2026 (5-fix package item 3c, Codex C2): a run never re-checks-out the shared ops tree
# that another run (the scheduled tick, a report) may be using. Each run gets its own detached worktree
# of the reviewed commit it just fetched (ops-runs/<step>-<time>-<pid>), runs there and removes it on
# exit. A leftover tree is removed only when its run's process is gone and no live process names the
# tree (or, with no pid yet, once it is older than 10 minutes), so a running copy is never pulled from
# under its run.
runs="$home_dir/ops-runs"
run_dir=""
sweep() {
  [ -d "$runs" ] || return 0
  local d name pid
  for d in "$runs"/*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    pid="$(cat "$runs/.$name.pid" 2>/dev/null || true)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then continue; fi
    # Codex r1 on #603: the wrapper may be gone while its node (or a child of it) still runs from the
    # tree; any live process whose command line names the tree keeps it.
    if /usr/bin/pgrep -f -- "$(printf '%s' "${d%/}" | sed 's/[][\\.^$*+?(){}|]/\\&/g')" >/dev/null 2>&1; then continue; fi
    if [ -z "$pid" ] && [ -n "$(find "$d" -maxdepth 0 -mmin -10 2>/dev/null)" ]; then continue; fi
    git -C "$ops" worktree remove --force "$d" >/dev/null 2>&1 || true
    rm -f "$runs/.$name.pid"
  done
  git -C "$ops" worktree prune >/dev/null 2>&1 || true
}
unpin() {
  [ -n "$run_dir" ] || return 0
  git -C "$ops" worktree remove --force "$run_dir" >/dev/null 2>&1 || true
  rm -f "$runs/.$(basename "$run_dir").pid"
}
pin() {
  git -C "$ops" fetch -q origin collab/integration || return 1
  local rev
  rev="$(git -C "$ops" rev-parse --verify -q 'FETCH_HEAD^{commit}')" || return 1
  sweep
  mkdir -p "$runs" || return 1
  run_dir="$runs/$1-$(date +%Y%m%d%H%M%S)-$$"
  git -C "$ops" worktree add -q --detach "$run_dir" "$rev" || { run_dir=""; return 1; }
  printf '%s\n' "$$" > "$runs/.$(basename "$run_dir").pid"
  trap unpin EXIT
}

step="${1:-}"
[ $# -gt 0 ] && shift
case "$step" in
  status) pin status && cd "$clone" && node "$run_dir/scripts/collab-turn.mjs" --status ;;
  report) pin report && cd "$clone" && node "$run_dir/scripts/collab-turn.mjs" --report ;;
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
  # L19: the owner report (08/14/22) and the retro read one shared source snapshot per slot.
  snapshot)
    if [[ "${1:-}" =~ ^(08|14|22|retro)$ ]]; then
      pin snapshot && cd "$clone" && node "$run_dir/scripts/collab-snapshot.mjs" --slot "$1"
    else
      echo "ops-run: snapshot needs a slot (08|14|22|retro)" >&2; exit 2
    fi ;;
  *) echo "ops-run: unknown step '$step' (status|report|busy|beat NAME start|done|preflight N|snapshot SLOT)" >&2; exit 2 ;;
esac
