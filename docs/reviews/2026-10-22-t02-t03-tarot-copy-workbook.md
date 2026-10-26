# T02/T03 — Tarot copy keyed by the asked action (draft for owner review), 2026-10-22

**Status: decided under owner delegation (26/10/2026), not yet wired.** Was: DRAFT, awaiting owner approval. Nothing in the workbook is live. It is not wired into the engine,
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

- Copy decisions are recorded under owner delegation for all 275 rows; four rewritten lines are polished by Codex below. Claude review of this polish remains open. This does not close wiring or T05.
- Wiring, versioning, audits and Codex review: not started, by design.
- Framer longest-signal collisions (finding 1) and goal override (finding 2): not fixed here.


## Delegated decision (26/10/2026)

The owner delegated copy decisions to Claude on 26/10/2026. Claude had a first-pass reviewer read every row against the
rules above, then checked samples and every uncertain row itself. The "Owner decision" / "Owner note" columns now carry
each decision ("Uỷ quyền 26/10: …"). This is one careful reading, not a comprehension test with real readers.

| Sheet | Approve A | Approve B | Rewrite | Drop (use the action's general row) |
|---|---|---|---|---|
| Scenes (T02, 133) | 96 | 33 | 1 | 3 |
| Steps (T03, 142) | 90 | 49 | 3 | 0 |

- **Rewrites (Codex to polish before wiring):** `T02-chia_se-self_care` (A ended alone in a dark room; B was writing, not
  sharing); `T03-nhan_loi-opening`, `T03-hen_gap-opening`, `T03-gop_y-opening` (both drafts fitted one topic only).
- **Dropped for now:** `T02-dat_ranh_gioi-relationships` (a partner monitoring messages is control-adjacent; it waits for
  a safety layer); `T02-tap_trung-self_care` and `T02-sap_xep_lai-self_care` (their example questions belong to another
  action: "tập trung vào bản thân", tidying a room). Both are T01 framer follow-ups.
- **Switched to B** where A ran longer than one small step: `T03-nghi_ngoi-next`, `T03-o_nha-next`, `T03-hen_gap-next`.

Conditions for the wiring PR (not done here):
1. Steps are keyed by action × role but render for every topic. Every `opening` line must read naturally for all topics
   of its action; any that cannot is split by topic in the wiring PR.
2. Add a variety check (AC16): scenes repeat images (typing then deleting, rereading, an unopened chat) and many steps
   end "…và ghi lại bạn thấy thế nào". Vary these before readers see them across readings.
3. Keep frozen readings: wiring bumps the content version, and stored readings keep their old text.
4. A human comprehension check stays open (T05). This decision does not replace it.


## Codex wording pass (26/10/2026)

Read the four requested rewrites against the C4/C5 rules and the topic-neutral opening requirement. The final proposed
text is in each row's Owner note; drafts A/B remain unchanged as provenance. Claude must review this authored polish.

| ID | Proposed text after polish |
|---|---|
| T02-chia_se-self_care | Cả tuần bạn trả lời “mình ổn” mỗi khi được hỏi thăm, rồi chuyển sang chuyện khác. |
| T03-nhan_loi-opening | Mở lời: “Mình nhận lời nhé, mình thống nhất thời gian cụ thể với bạn được không?” |
| T03-hen_gap-opening | Mở lời: “Bạn rảnh lúc nào để mình hẹn gặp và nói chuyện một chút?” |
| T03-gop_y-opening | Mở lời: “Bạn có muốn nghe một góp ý của mình về chuyện này không?” |

The scene is observable and carries no advice. The three openings do not assume a job, a date, a prior meeting or
an existing disagreement. All four are at most 28 whitespace-delimited Vietnamese syllables. No runtime, catalog,
versions, fallback approval, stored reading or provider payload changes. The wiring conditions and T05 stay open.
