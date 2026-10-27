# T02/T03 — Tarot copy keyed by the asked action (draft for owner review), 2026-10-22

**Status: decided under owner delegation (26/10/2026); wired in the T02/T03 wiring PR (27/10/2026, renderer v8), not released.** Was: DRAFT, awaiting owner approval. Nothing in the workbook is live. It is not wired into the engine,
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


## Wiring (27/10/2026, Claude; awaiting Codex review, not released)

`apps/api/app/domains/tarot/action_copy.py` holds the decided rows: 130 scenes (three dropped rows
fall back to the action's `general` row) and 142 steps, plus one table of topic openings. A framed
reading whose QuestionFrame carries an action shows, **at the spread's one step role only**, the
action's scene for the frame's topic and the action's step for that role; the other positions keep
the card × topic scene. A frame without an action, and an action without a row (the eight solo
actions have no opening), render as before. Renderer `tarot-renderer-v8`, knowledge
`tarot-knowledge-v6`, `tarot-action-copy-v1`; readings stored under v7 keep their text (a test
reopens a drawn session after the copy changes). The fallback approval pins the module.

**Claude review of the Codex polish:** the four lines are kept as written. The scene is observable
and carries no advice; the three openings are sample lines that do not assume a job, a date or a
dispute.

**Wiring condition 1 (openings for every topic).** 19 topic openings were added where the action's
opening did not read naturally for one of its topics (new copy, for Codex review):

| Action × topic | Opening |
|---|---|
| nhan_lai × relationships | Mở lời: “Hôm qua đi chơi với bạn vui lắm, cảm ơn bạn nhé.” |
| nhan_lai × communication | Mở lời: “Hình như mình nói chưa rõ, ý mình là…” |
| cho_them × relationships | Mở lời: “Mình cần chút thời gian để nghĩ, vài hôm nữa mình nhắn bạn nhé.” |
| bat_dau × relationships | Mở lời: “Hôm trước nói chuyện với bạn vui ghê, cuối tuần này mình đi cà phê nhé?” |
| bat_dau × self_care | Mở lời: “Mỗi sáng mình giữ mười phút cho riêng mình, lúc đó mình chưa trả lời tin nhắn nhé.” |
| xin_gop_y × relationships | Mở lời: “Mình muốn nghe bạn nghĩ thật về chuyện tình cảm của mình, bạn nói thẳng giúp mình nhé.” |
| gui_di × relationships | Mở lời: “Mình có món quà nhỏ muốn gửi bạn, bạn nhận giúp mình nhé.” |
| xin_loi × general, work | Mở lời: “Mình xin lỗi về chuyện hôm trước, phần đó là lỗi của mình. Mình muốn nghe bạn nói.” |
| dat_ranh_gioi × work | Mở lời: “Ngoài giờ làm mình ít xem tin nhắn, việc gấp thì bạn gọi mình nhé.” |
| dat_ranh_gioi × energy | Mở lời: “Tuần này mình chỉ gặp được một buổi, mình hẹn bạn hôm khác nhé.” |
| dat_ranh_gioi × self_care | Mở lời: “Dạo này mình cần giữ khoảng cách một chút, mình nói trước để bạn biết.” |
| thu_lai × general, work, self_care | Mở lời: “Mình định thử lại chuyện này lần nữa, bạn nhắc mình giữ lời nhé?” |
| thu_lai × relationships | Mở lời: “Lâu rồi mình chưa hỏi thăm bạn, dạo này bạn thế nào?” |
| sap_xep_lai × energy | Mở lời: “Từ tuần này mình ngủ sớm hơn, sau mười giờ mình trả lời bạn vào sáng hôm sau nhé.” |
| sap_xep_lai × self_care | Mở lời: “Cuối tuần này mình dọn lại phòng, bạn giúp mình một tay được không?” |
| de_xuat × relationships | Mở lời: “Mình có một cách chia việc khác, bạn nghe mình nói hai phút nhé?” |

**One edited step.** `T03-dung_lai-criterion` lost "rõ ràng" and now ends "… lên một mẩu giấy dán
cạnh bàn": with the Roast lead-in the old line had 29 words in one sentence, and it ended like
`tap_trung/next`.

**Wiring condition 2 (variety).** Measured on the chosen drafts: no repeated line; "gõ … xóa" in 2
scenes, "đọc lại" in 3, "ghi lại … thấy thế nào" in 2 steps. A test keeps these caps. Action scenes
still do not depend on the card: two readings with the same action and topic show the same step-role
scene; the card's meaning differs.

**Review gate.** The plain-language review's observability and testability checks are word lists. 58
decided lines (concrete times, places, objects and verbs such as "gửi", "dời", "nằm") were missing
from them. Tarot-only marker lists were added (`TAROT_SCENE_MARKERS`, `TAROT_ACTION_MARKERS`); Daily
and natal keep the old lists, and the existing negative cases still fail.

**Luna provenance.** The step role's scene and step trace to closed codes `act.<action>.<topic>`
(new optional `scene` code; the action code pattern widened), so Tarot Luna can still rebuild every
text. No new data reaches a provider: the action label was already in the brief's stance labels.

Still open: framer longest-signal collisions (finding 1), T05 comprehension check, release.
