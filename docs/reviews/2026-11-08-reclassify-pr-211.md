# PR #211 reclassified S → M (fix-forward #226)

PR #211 (`70354512`) declared **S**. Two Radar section headings in the expanded ("more") layer
changed text, so users see a difference. Under `product-development-process.md` §0 that is **M**.

## Full scope of `70354512`

The commit changed more than title text (corrected by fix-forward #332):

1. **Copy:** two Radar section titles in `apps/api/app/domains/radar/reading.py` (table below).
2. **Content linter (backend tooling):** `apps/api/app/domains/readings/clarity_lint.py` adds
   `a6_sentences`; rule A6 (sentence shared by too many readings) now skips sections whose name ends
   in `_title`. Every other rule still lints titles.
3. **Corpus extraction:** `apps/api/scripts/content_clarity_corpus.py` emits a Radar scene's title as
   its own `scene_<key>_title` section instead of folding it into `scene_<key>` with the body, so A6
   can tell title from body.
4. **Approval record:** `docs/operations/fallback-approval.json` hashes refreshed.

| Section | Before | After |
|---|---|---|
| `why` | Những điểm chạm Lá đã dùng (26 ký tự) | Những điều Lá đã dựa vào (24 ký tự) |
| `perspective` | Cùng một lần gặp, mỗi người có thể để tâm chuyện khác (52) | Cùng một lần gặp, mỗi người để tâm một chuyện khác (50) |

## M gates

- G1: same sections, same order and `layer`; only `title` text. No API/schema change. Copy is listed in
  `docs/operations/fallback-approval.json` by PR #211.
- G2: headings got shorter (−2 chars each); no new element, state or style. They render in the
  existing section heading, which wraps. 360/390 px: checked by code reading only (no screenshot in
  this receipt); the longer old titles already shipped at these widths. A visual check at 360/390 px
  stays open for the next owner content/UI pass.
- G3: wording change of existing copy, in the owner's end-of-content polish (no new sentence type).
- G4 (linter/tooling, items 2–3): offline content tooling only; no API route, schema, runtime reading
  or user output changes. The A6 exemption is narrow (suffix `_title` only), so body text keeps the
  duplicate check.
- G6, what is actually covered:
  - Linter: `apps/api/tests/readings/test_clarity_lint.py:200`
    (`test_a6_skips_fixed_titles_but_other_rules_still_lint_them`) proves A6 skips a title repeated in
    10/10 synthetic readings, still flags the same sentence in a body section, and still applies other
    rules (placeholder) to titles.
  - Corpus extraction (item 3): no direct test that `scene_<key>_title` is emitted separately.
  - Titles (item 1): **not asserted.** `RadarReadableView.test.tsx:49` only uses the new `why` title as
    fixture data and never checks it; the `perspective` fixture (`:65`) uses a short placeholder title.
    `apps/api/tests/radar/test_reading.py` checks section structure, not these strings. Reverting both
    title changes would leave these tests green.
  - Gap (open): add an assertion on the two exact titles from `reading.py` and a test for the
    `scene_<key>_title` split. Recorded here; not fixed by this receipt.
- G7/G8: no session, permission, personal data or log change.
