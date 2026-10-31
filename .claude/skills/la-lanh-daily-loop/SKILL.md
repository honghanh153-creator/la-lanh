---
name: la-lanh-daily-loop
description: Use at the start of any Lá Lành work session, when resuming, and before ending a turn. The owner-approved daily method for the Claude ⇄ Codex auto loop - read the queue, never wait idle on a check, fix claude-fix PRs first, top up the plan, decide with the five-question checklist, and write the end-of-day retro.
---

# Lá Lành daily loop (owner-approved 30–31.10.2026)

Sources of truth (read them, they win over this summary):
`docs/operations/collab-auto-loop-plan.md` (§2 decisions, §3.2 daily method),
`docs/operations/decision-checklist.md`, `AGENTS.md`.

## Start or resume

1. `node scripts/collab-turn.mjs --report` (or the ops clone `~/.cache/la-lanh-collab/ops/scripts/…`):
   who has the turn on every open PR. The plan issue's status board says whether the loop runs.
2. Stop autopilot runs that show no progress for more than 30 minutes (they block later runs).
3. Owner decisions made since the last session are in the plan §2 and hub issue #2. Do not
   follow older notes that contradict them.

## While the day runs (08:50–23:30)

- **Heavy work is serial and belongs to the tick**: author check, Codex review, merge. Never run
  your own `pnpm check` loop. `node scripts/collab-check.mjs --busy` tells whether a check runs.
- **Never wait idle.** While a check runs, do light work: `claude-fix` PRs first, then open
  `fix-forward` issues, then the next task of the active priority group
  (ops → content → privacy → new features). Keep local test runs small (seconds).
- **Before ending a turn**, look for `claude-fix` items and leave a watcher if the session stays
  open, so a REQUEST_CHANGES never waits for the owner's next message.
- **Plan top-up**: when the machine has fewer than two jobs, add the next task and post
  "Bổ sung plan HH:MM: …" on the plan issue (agent marker, never the owner reply grammar).
- Before push: lint/format the touched files.

## Deciding

Run Q1–Q5 of the checklist. All "no" → decide, do, report. UX improvements that pass Q1–Q5 are
done without waiting. New user-facing copy, personal data, product direction, cost or anything
irreversible → ask once, with numbered options and a recommendation, and keep working meanwhile.

From the third automatic review round (owner, 31.10.2026), Claude decides: a PR labelled
`needs-owner` only by the two-round cap is fixed and unlabelled when the finding is critical or
user-impacting, or when Q1–Q5 are all "no"; comment "Round N: Claude decides per checklist".
Copy approval and any Q1–Q5 "yes" still wait for the owner.

## Never

Merge to `main`, release, deploy, touch production or real user data, change IAM/secrets/budget,
call paid APIs outside the Codex review script, post personal data in the public repo, or write
`Duyệt`/`Giữ`/`Bỏ` on the plan issue for the owner.

## End of day

Write `docs/reviews/YYYY-MM-DD-collab-loop-retro.md` (numbers, stalls with root causes, fixes,
proposals) and open an `area:ops` PR so Codex reviews it. Once a week, look for rot: notes, queue
items or instructions that contradict the current plan; mark them superseded or remove them.
