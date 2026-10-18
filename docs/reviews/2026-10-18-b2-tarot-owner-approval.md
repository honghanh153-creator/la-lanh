# Owner approval — Tarot B2 (US-20), 2026-10-18

Owner (Pham Hanh) approved in the Claude session on 2026-10-18, after Codex APPROVE of PR #27 @
`a1155914dc09995e774b4dba3b42fb6ea79929c5`. Approval was given in conversation, not by filling the workbook; the
workbook's owner columns are therefore empty and this file is the record.

## Approved

| Item | Scope | Decision |
|---|---|---|
| A1–A7 copy | `docs/reviews/2026-10-18-b2-tarot-copy-review.xlsx`: 120 role frames, 30 leads, 48 headline frames, 8 stance conclusions, 20 conjunctions, B2-1/B2-3 phrases, 81 lean labels | Approved as written in the workbook, no edits |
| AC14 | 12 sample readings, sheet "Checklist AC14" | Passed |

## Product decisions

| # | Decision |
|---|---|
| C1 | Accept the structural exception to "at most one negative idea per reading" for the five-card **loop** map (habit + cost: 2) and **choice** map (cost of A, cost of B, trade-off: 3). Recorded in the content standard. No code change. |
| C2 | Keep: readings with Roast frames carry no per-position Roast tails. |
| C3 | Keep: Roast in energy and self-care uses the direct frames with the gentle opener and tails. |
| C4 | Backlog: an editorial pass over example scenes with advice words (3,096 / 28,416 scene slots in the bank audit; mostly narrative "thử"). |
| C5 | Backlog: an editorial pass so step actions carry a "khi…" trigger (876 / 7,104 today). |
| C6 | Deferred: 2–3 scenes per card × topic. No paid API call; any AI drafting (phase E) needs a separate owner cost approval. |
| C7 | Confirm the closed-action-label limit: 11 / 48 bank choice questions split into two options; the rest answer "what to clarify before choosing". |

## Follow-up done on approval

- The fallback approval scope now pins the framed renderer: `question_frame`, `roles`, `stance` and `variants`
  tables and versions (`tarot-renderer-v7`, `tarot-knowledge-v5`, `tarot-gates-v5`, rules v2, roles v2, stance v1,
  variants v1, variant catalog v1). `docs/operations/fallback-approval.json` refreshed with this file as evidence.

## Not decided here (still release prerequisites)

- Merge of the PR chain into `collab/integration`: owner chose **not yet** (after the approval PR is reviewed).
- PostgreSQL rehearsal of migration `20261018_0037` / cursor / RLS with the real backend role.
- Luna prompt update before any Luna activation; Luna stays off.
- `main` / `release` / deploy remain the owner's decision. `approved_release` in the approval file is set to the
  release commit when B2 ships.
