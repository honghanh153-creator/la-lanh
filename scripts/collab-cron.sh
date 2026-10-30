#!/bin/bash
# launchd entry point for the collab safety net (docs/operations/collab-auto-loop-plan.md).
# Runs only reviewed code: a dedicated ops clone pinned to origin/collab/integration.
set -euo pipefail

home_dir="${LA_LANH_COLLAB_HOME:-$HOME/.cache/la-lanh-collab}"
runtime="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies"
export PATH="$runtime/node/bin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
ops="$home_dir/ops"
log="$home_dir/logs/tick-$(date +%Y-%m-%d).log"
mkdir -p "$home_dir/logs"

{
  if [ ! -d "$ops/.git" ]; then
    /usr/bin/git clone --quiet https://github.com/honghanh153-creator/la-lanh.git "$ops"
  fi
  /usr/bin/git -C "$ops" fetch --quiet origin collab/integration
  /usr/bin/git -C "$ops" checkout --quiet --force --detach FETCH_HEAD
  /usr/bin/git -C "$ops" clean -fdxq
  node "$ops/scripts/collab-tick.mjs"
} >>"$log" 2>&1
