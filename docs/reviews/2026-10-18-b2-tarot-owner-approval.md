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

## Addendum — 2026-10-19: self-care lean rule

Owner (chat, 2026-10-19): "ok sửa lỗi hướng nghiêng trước đi", after the production finding that 23 of 78
one-card readings told a tired reader "cân nhắc thêm trước khi nghỉ ngơi" while the step said to take a rest.

- Rule (`stance.SELF_CARE_ACTIONS`, `tarot-stance-v2`): for rest, stopping, saying no, setting a boundary, asking
  for help and treating oneself, a "hold" card counts as neutral, so the lean is "nghiêng về thử" or "chưa rõ",
  never "cân nhắc thêm trước khi". No new copy: the existing approved conclusions and headlines are reused.
- Same session decisions recorded for the next Tarot/Hợp gu work (not implemented here): card names shown as
  English + Vietnamese; keep the lean in a conditional form; Hợp gu keeps a number, shown as a range, with the
  calibration reviewed so the strongest pairs can reach 90–100; Luna's role is to rewrite; Hợp gu allows manual
  entry of the other person's birth data (consent basis to be confirmed, see the Hợp gu plan).
- `fallback-approval.json` refreshed for the changed stance table and version.

## Addendum — 2026-10-22: asked-clause labels (audit T01)

Owner (chat, 2026-10-22, audit v2): "sửa Tarot target-action nhất quán", after the audit found that a background
clause decided the action ("Mình có nên xin lỗi sau lần nói chuyện vừa rồi không?" was labelled "nói ra", so the
lean, goals and step answered a conversation instead of the apology).

- Rule (`question_frame.asked_text`, frame `tarot-question-frame-v2`): action, topic and goals come from the asked
  clause; "sau khi / trước khi / sau lần … / khi / vì / nếu / dù …" clauses are background. Question words stay
  asked ("khi nào", "là lúc", "vì sao", "thay vì"). A why/how/open question whose asked clause names no action reads
  the whole question (`_REFLECTIVE_FORMS`), because its "khi" clause is the situation being reflected on.
- Stored v1 frames are replayed as stored (AC17); choice options under v2 drop their own background clauses.
- No new copy. On the 296-question bank one label changes (`general.yes_no.3`: bắt đầu → dọn dẹp).
- `fallback-approval.json` refreshed for the new rule table `_REFLECTIVE_FORMS` only.
