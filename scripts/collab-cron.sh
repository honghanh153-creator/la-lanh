#!/bin/bash
# launchd entry point for the collab safety net (docs/operations/collab-auto-loop-plan.md).
# Runs only reviewed code: a dedicated ops clone pinned to origin/collab/integration.
set -euo pipefail

home_dir="${LA_LANH_COLLAB_HOME:-$HOME/.cache/la-lanh-collab}"
runtime="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies"
# pnpm lives in the runtime fallback dir; it goes last so /usr/bin/git wins over its own git.
export PATH="$runtime/node/bin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$runtime/bin/fallback"
ops="$home_dir/ops"
# Trial 12.11.2026 (owner): author check reads the pr-check CI result; the PR's code no longer runs here.
# Rollback: delete this line.
export LA_LANH_CHECK_SOURCE=ci
log="$home_dir/logs/tick-$(date +%Y-%m-%d).log"
mkdir -p "$home_dir/logs"
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
    /usr/bin/git -C "$ops" worktree remove --force "$d" >/dev/null 2>&1 || true
    rm -f "$runs/.$name.pid"
  done
  /usr/bin/git -C "$ops" worktree prune >/dev/null 2>&1 || true
}
unpin() {
  [ -n "$run_dir" ] || return 0
  /usr/bin/git -C "$ops" worktree remove --force "$run_dir" >/dev/null 2>&1 || true
  rm -f "$runs/.$(basename "$run_dir").pid"
}
pin() {
  /usr/bin/git -C "$ops" fetch -q origin collab/integration || return 1
  local rev
  rev="$(/usr/bin/git -C "$ops" rev-parse --verify -q 'FETCH_HEAD^{commit}')" || return 1
  sweep
  mkdir -p "$runs" || return 1
  run_dir="$runs/$1-$(date +%Y%m%d%H%M%S)-$$"
  /usr/bin/git -C "$ops" worktree add -q --detach "$run_dir" "$rev" || { run_dir=""; return 1; }
  printf '%s\n' "$$" > "$runs/.$(basename "$run_dir").pid"
  trap unpin EXIT
}

{
  if [ ! -d "$ops/.git" ]; then
    /usr/bin/git clone --quiet https://github.com/honghanh153-creator/la-lanh.git "$ops"
  fi
  # The shared ops tree stays current for the git hooks and the sub-agent gate, which read it; the tick
  # itself runs from its own pinned copy, so a report or another run can never change it mid-run.
  /usr/bin/git -C "$ops" fetch --quiet origin collab/integration
  /usr/bin/git -C "$ops" checkout --quiet --force --detach FETCH_HEAD
  /usr/bin/git -C "$ops" clean -fdxq
  pin tick
  node "$run_dir/scripts/collab-tick.mjs"
} >>"$log" 2>&1
