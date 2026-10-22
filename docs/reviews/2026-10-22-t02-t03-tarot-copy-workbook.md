# T02/T03 — Tarot copy keyed by the asked action (draft for owner review), 2026-10-22

**Status: DRAFT, awaiting owner approval.** Nothing in the workbook is live. It is not wired into the engine,
`examples.py`, `roles.py`, `meaning_brief.py` or the fallback approval scope (`docs/operations/fallback-approval.json`).

Workbook: `docs/reviews/2026-10-22-t02-t03-tarot-copy-workbook.xlsx`

## Problem

Readings now carry one closed action label per question (`TarotAction`, US-20 decision A6), but the everyday scene
comes from card × topic and the small step from the card's resource (or one of eight keyword goals). The scene and
step can therefore miss the question. Example: "Mình có nên xin lỗi sau lần nói chuyện vừa rồi không?" (Quan hệ,
The Fool) renders the dating scene "Có lần bạn muốn rủ người mới quen đi chơi…".

## What the workbook contains

| Sheet | Rows | Maps to |
|---|---|---|
| Hướng dẫn | purpose, the C4/C5 rules in Vietnamese, the bug example, how to review, known risks | — |
| Cảnh theo hành động | 133 rows (action × plausible topic), drafts A and B each = 266 scenes; 47 implausible combos skipped with a reason on the action's `general` row | T02 / decision C4 |
| Bước nhỏ theo hành động | 142 rows (30 actions × step roles `focus`, `next`, `alternative`, `criterion`; 22 actions × `opening`), drafts A and B each = 284 steps; 8 solo actions have no `opening` row, reason given | T03 / decision C5 |
| Đối chiếu hiện tại | 16 synthetic cases rendered by `TarotReadingEngine` on `collab/integration` @ `7ca22cb` (direct voice, variant 0) next to the proposed scene and step | before/after |

Every topic skipped for an action falls back to that action's `general` row. All 30 actions have a `general` row.
Owner columns: "Owner decision" (Duyệt / Sửa / Bỏ, drop-down) and "Owner note".

## Self-review done before saving

- Every example question was run through the real question framer (`assess_question` + `frame_question`): all 133 are
  accepted and map to the row's action and topic.
- Scenes: no "nên / hãy / thử / đừng / có thể", no "sẽ / chắc chắn / định mệnh / số phận / vũ trụ", no
  mind-reading phrases, no medical/legal/financial terms, contain "bạn", 12–28 words. Observability reviewed by hand.
- Steps: no "phải / nhất định / bắt buộc / chắc chắn", no outcome promises, no "cân nhắc thêm / suy nghĩ thêm"
  (self-care actions always do the action), ≤ 28 words; every `opening` step is a sample line starting "Mở lời:".
- Shared banned phrases from the content standard (pattern, vận hành, giữ nhịp, …) absent.
- Synthetic questions only; no personal data; no paid API call.

## Findings outside this workbook

1. The bug question frames as `noi_ra`, not `xin_loi`, on `collab/integration`: `match_action` prefers the longest
   signal, and "nói chuyện" (10 chars) beats "xin lỗi" (7). Similar collisions: "thêm thời gian" (→ `cho_them`),
   "chia tay" (→ `ket_thuc`), "thói quen" (→ `doi_thoi_quen`) win over the action the sentence asks about. Example
   questions in the workbook were rephrased to avoid them; the framer rule itself needs a separate fix.
2. Keyword goals in `meaning_brief.py` can override the action: "Mình có nên ghi lại những việc làm mình mệt trong
   tuần không?" (`viet_ra`) gets the rest step "Giữ khoảng nghỉ đã chọn…" because "mệt" matches goal `rest`.
3. Some current scenes break C4, e.g. "Bạn có thể nhờ nhóm đọc thử…" (Ba Cốc, work) and "…chọn ít việc hơn có thể
   hợp lý lúc này" (Tiết Chế).

## After approval (separate PR, not this one)

Wire approved rows by action label (fallback: action `general` row, then today's card × topic scene when the
question has no label), bump the variant/catalog and knowledge versions, refresh the fallback approval scope, keep
every stored reading frozen (US-20 AC15/AC17), re-measure AC16 variety (action scenes do not depend on the card),
and run `pnpm tarot:audit` and `pnpm content:review`.

## Open items (AC/DoD)

- Owner approval of every row (US-20 AC14/AC19 copy approval; DoD "owner duyệt nội dung mới"): not started.
- Wiring, versioning, audits and Codex review: not started, by design.
- Framer longest-signal collisions (finding 1) and goal override (finding 2): not fixed here.
