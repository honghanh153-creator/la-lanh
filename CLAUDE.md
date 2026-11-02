# Lá Lành shared task workflow

@AGENTS.md
@docs/operations/codex-claude-collaboration.md

Run `node scripts/collaboration-inbox.mjs` at the start/resume of a task.
You may implement any module. Coordinate overlapping edits in the task Issue.
Update the task Issue with a handoff before stopping. Another agent must be able
to continue using the task's branch, commit and test receipt, without this chat.
Merge into collab/integration only with a matching `Review verdict: APPROVE @ <SHA>` and
`Author check: PASS @ <SHA>`. Use the auto loop in `docs/operations/collab-auto-loop-plan.md`:
`collab-check.mjs` → `codex-review.mjs` → `collab-merge.mjs`; `collab-turn.mjs --report` shows the queue.
These instructions are guidance, not a technical permission boundary.
