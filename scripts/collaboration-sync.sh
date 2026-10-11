#!/usr/bin/env bash
set -euo pipefail

# Run from an isolated agent checkout, not the directory containing this script.
integration='collab/integration'
mode="${1:---check}"
if [[ $# -gt 1 || ( "$mode" != '--check' && "$mode" != '--apply' ) ]]; then
  echo 'Usage: bash scripts/collaboration-sync.sh [--check|--apply]' >&2
  exit 2
fi
root=$(git rev-parse --show-toplevel) || exit 2
cd "$root"
branch=$(git symbolic-ref --quiet --short HEAD) || {
  echo 'Stop: detached HEAD. Use an agent branch.' >&2
  exit 2
}
case "$branch" in
  agent/codex|agent/codex/*|agent/claude|agent/claude/*) ;;
  *) echo "Stop: '$branch' is not an agent branch. No fetch or merge performed." >&2; exit 2 ;;
esac

preflight() {
  if [[ -n "$(git status --porcelain=v1 --untracked-files=normal)" ]]; then
    echo 'Stop: uncommitted or untracked files. Commit your own work first; nothing was stashed or deleted.' >&2
    exit 2
  fi
  for state in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD rebase-merge rebase-apply; do
    if [[ -e "$(git rev-parse --git-path "$state")" ]]; then
      echo "Stop: unfinished Git operation ($state). Resolve it first." >&2
      exit 2
    fi
  done
}
preflight
lock="$(git rev-parse --git-path collaboration-sync.lock)"
if ! mkdir "$lock" 2>/dev/null; then
  echo 'Stop: another sync is running, or a previous sync left its lock. Inspect before removing the lock.' >&2
  exit 2
fi
trap 'rmdir "$lock"' EXIT
git fetch --no-tags origin "refs/heads/$integration:refs/remotes/origin/$integration"
target=$(git rev-parse "refs/remotes/origin/$integration^{commit}")
if ! git merge-base HEAD "$target" >/dev/null; then
  echo 'Stop: unrelated history. No merge performed.' >&2
  exit 2
fi
echo "Agent: $branch"
echo "Integration: $integration @ $target"
if git merge-base --is-ancestor "$target" HEAD; then
  echo 'Already contains the reviewed integration commits. Nothing to merge.'
  exit 0
fi
git log --oneline "HEAD..$target"
if [[ "$mode" == '--check' ]]; then
  echo 'Check only: branch and working files unchanged. Use --apply after reviewing the commits.'
  exit 0
fi
# Agents must be paused during --apply. This catches edits arriving after fetch,
# but cannot lock an unrelated editor or another agent editing the same checkout.
preflight
if ! git merge --no-edit "$target"; then
  echo 'Merge stopped. Do not push. Review conflicts, or run git merge --abort to undo this sync.' >&2
  exit 1
fi
echo 'Merged into the local agent branch. Run relevant tests, then push without --force.'
