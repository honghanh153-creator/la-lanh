# Tarot legacy copy pinned in the fallback approval — 2026-10-18

Follow-up to Codex's non-blocking note on PR #28 (APPROVE @ `550ae446123f769beed7df40cf1fd7a04e464672`): older
copy reused by the Tarot renderers was not fingerprinted, so an edit to, for example,
`meaning_brief._GOAL_ACTIONS` or `voice.GENTLE_ACTION_FRAMES` changed served text while
`fallback_approval.current()` stayed the same.

## What is now pinned

| Module | Tables | Served as |
|---|---|---|
| `tarot/meaning_brief.py` | `_GOALS`, `_DEFAULT_GOAL`, `_GOAL_ACTIONS`, `_GOAL_FEELING_ACTION`, `_GOAL_NEED_ACTIONS`, `_GOAL_AGENCY_ACTIONS`, `_GOAL_BOUNDARY_ACTIONS`, `_STAGE_ONE_POSITIONS`, `_STAGE_TWO_POSITIONS`, `_LINKS`, `BRIEF_LIMITS`, `GOAL_KEYS` | goal reflections, goal small actions, summary lead lines, provider brief goals/links/limits |
| `tarot/voice.py` | `ROAST_HEADLINES`, `GENTLE_HEADLINES`, `SUMMARY_OPENERS`, `ROAST_MEANING_TAILS`, `GENTLE_MEANING_TAILS`, `ROAST_ACTION_FRAMES`, `GENTLE_ACTION_FRAMES`, `_MEANING_GROUPS`, `GENTLE_CONTEXTS` | Roast and gentle-register frames, tails and openers |
| `tarot/examples.py` | `CARD_EXAMPLES`, `CONTEXT_EXAMPLES`, `RELATIONSHIP_EXAMPLES` | example scenes for the "general" and "relationships" topics (the other four topics use `CONTEXT_SCENES`, already pinned) |

The three dictionaries that lived inside `goal_action` were moved to module tables (`_GOAL_*_ACTIONS`,
`_GOAL_FEELING_ACTION`, stage sets) so the approval can fingerprint them. Behaviour is unchanged: the 189
outputs (9 goals × 21 position keys) hash to `86698546666ec66f598b21ccfe2c1795d5a65d325b7413ee029092b06e3b31ce`
before and after the move (test `test_goal_action_output_is_unchanged_by_the_table_move`).

## Approval source

No copy changed. Every pinned table is **byte-identical to production release `836222282dfc`**, the release
the owner approved (`docs/reviews/production-release-2026-10-16/receipt.md`; it is the `approved_release` of
`fallback-approval.json`). Rerunnable proof, from `apps/api`:

```
uv run python -m scripts.compare_tarot_release_copy            # exports 836222282dfc with git show
uv run python -m scripts.compare_tarot_release_copy --release <hash> | --historical-dir <dir>
```

The tool exports `relationship_readings`, `examples`, `voice` and `meaning_brief` from the release, and each
historical module resolves its Tarot sibling imports to the historical files (so `examples` uses the release's
`RELATIONSHIP_EXAMPLES`, not the current one). It exits 1 on any mismatch. Hardened after Codex's P3 notes on
#29 (`f60412c`): the first helper compared the current relationship table with itself and exited 0 on
mismatch; both have negative controls in `tests/grammar/test_compare_tarot_release_copy.py`.

Result on 2026-10-18: relationship_readings, examples and voice tables identical; `meaning_brief._GOALS`,
`_DEFAULT_GOAL`, `_GOAL_ACTIONS`, `_LINKS` identical; `goal_action` identical over 9 goals × 21 positions;
`BRIEF_LIMITS` present verbatim in the release source. `ALL IDENTICAL`, exit 0.

## Regressions

`tests/grammar/test_grammar.py`: a mutation of each of 19 tables changes `current()`; Codex's example (editing
`_GOAL_ACTIONS` changes a framed reading's small action) now also changes the approval; the `goal_action`
snapshot above.

## Not covered yet (candidates for a further follow-up)

- Vietnamese literals inside function bodies are not fingerprinted by design of `module_tables`: in
  `engine.py` (`_reflection` questions, `_meaning` frames of the legacy renderer, `_boundary_rejection` /
  `_clarify` reframes, closing prompt and disclaimer in `render`) and in `stance.py` (`_role_sentence`,
  `_compact_sentence`, `_reason` summary/reason frames). Pinning them needs the same move to module tables;
  `engine.py` changes would refresh the engine fingerprints.
- Compiled regex rules (question safety, sensitive-question voice fallback, checklist patterns) are skipped by
  `canonical()`; they are rules rather than copy and are covered by tests, not by the approval.
