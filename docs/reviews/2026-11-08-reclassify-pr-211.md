# PR #211 reclassified S → M (fix-forward #226)

PR #211 (`70354512`) declared **S**. Two Radar section headings in the expanded ("more") layer
changed text, so users see a difference. Under `product-development-process.md` §0 that is **M**.

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
- G6: `apps/web/src/features/radar/RadarReadableView.test.tsx` asserts the new titles; `apps/api/tests/radar/test_reading.py` covers the sections.
- G7/G8: no session, permission, personal data or log change.
