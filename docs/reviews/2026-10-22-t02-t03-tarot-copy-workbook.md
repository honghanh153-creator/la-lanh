# T02/T03 — Tarot copy keyed by the asked action (draft for owner review), 2026-10-22

**Status: decided under owner delegation (26/10/2026); wired in the T02/T03 wiring PR (27/10/2026, renderer v8) with the Codex r47 fixes (28/10/2026), not released.** Nothing in the workbook is live until release. Was (22/10): DRAFT awaiting owner
approval, not wired into the engine or the fallback approval scope; the wiring now lives in
`tarot/action_copy.py`, which the fallback approval pins (`docs/operations/fallback-approval.json`).

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

## Codex r47 fixes (28/10/2026, Claude; awaiting Codex review, not released)

Codex r47 ([PR #110 comment](https://github.com/honghanh153-creator/la-lanh/pull/110#issuecomment-6458291780))
found two whole-output defects that passed every gate. Both are fixed from closed labels (the frame,
the stance and a closed partner word list), not from a question or card whitelist, and no gate was
loosened. Versions stay `tarot-renderer-v8` / `tarot-knowledge-v6` / `tarot-action-copy-v1`:
nothing has been released or stored under them.

**1. The step agrees with the stance** (`action_copy.plan_step`). The stance is decided from the drawn
cards before any prose, then the step role shows:

| Reading | Step | Scene |
|---|---|---|
| yes/no leaning "thử" (LEAN_TRY), or how / why / open | the action's own step (as wired 27/10) | the action's scene |
| yes/no "cân nhắc thêm" (CONSIDER) or "kéo về hai phía" (UNCLEAR), or "khi nào" (timing) | the action's **preparation step** (below) | the action's scene |
| the same, for a self-care or boundary action (`stance.SELF_CARE_ACTIONS`) | the action's own step (owner decision 2026-10-19: never discourage rest or a boundary) | the action's scene |
| a choice the cards settle | the chosen option's step | the chosen option's scene |
| a choice the cards do not settle | the **choice step** (names neither option) | the card's scene |

In Roast, a reading whose cards ask for care uses only the two existing lead-ins that do not urge
acting now ("Bài tập nhỏ, khỏi gồng:", "Một nước đi gọn gàng:"); "Thôi nào, làm liền:", "Chốt kèo
nhỏ này nha:" and "Làm thử cho biết nè:" stay for readings that lean toward trying. No new lead-in.

New copy for Codex review, 24 preparation steps and 1 choice step (`PREP_STEPS`):

| Key | Step |
|---|---|
| nhan_loi | Trước khi trả lời lời mời, mở lịch và ghi ra một việc bị lùi lại nếu bạn nhận lời. |
| noi_ra | Viết điều bạn muốn nói thành một câu, để qua một đêm và sáng mai đọc lại xem còn đúng ý không. |
| nhan_lai | Gõ tin bạn định gửi vào ghi chú, ba mươi phút sau đọc lại rồi mới chọn gửi hay sửa. |
| hoi_lai | Ghi ra đúng một chỗ bạn chưa hiểu, kèm điều bạn đang đoán về chỗ đó, trước khi nhắn hỏi. |
| cho_them | Ghi vào lịch một ngày để xem lại chuyện này, và đến ngày đó mới chốt chờ tiếp hay thôi. |
| bat_dau | Ghi ra một thứ cần có sẵn để bắt đầu, như giờ rảnh hay dụng cụ, và kiểm xem đã có chưa. |
| doi_viec | Trong mười phút, ghi ra hai điều bạn muốn giữ ở công việc hiện tại và hai điều bạn muốn đổi. |
| xin_gop_y | Đánh dấu đúng một phần bạn muốn được góp ý, và viết một câu hỏi cụ thể cho phần đó. |
| gui_di | Đọc lại bản này một lượt và ghi ra một điều bạn muốn người nhận hiểu đúng nhất. |
| xin_loi | Viết câu xin lỗi vào ghi chú, đọc to một lần, rồi gạch bớt những chữ đang biện minh. |
| hen_gap | Mở lịch và khoanh hai khung giờ bạn thật sự rảnh, chưa cần nhắn rủ ngay. |
| chia_se | Viết ra một câu bạn muốn kể và một phần bạn muốn giữ riêng, trước khi kể với ai. |
| ket_thuc | Viết hai cột, điều chuyện này còn cho bạn và điều nó không còn đáp ứng, rồi để đó một ngày. |
| thu_lai | Ghi ra điều khiến lần trước chưa ổn và một chi tiết bạn đổi được ở lần này. |
| hoc_them | Ghi ra bạn muốn học để làm gì trong một câu, rồi xem bài đầu mà chưa đăng ký khóa nào. |
| tap_trung | Ghi ra ba việc đang kéo sự chú ý của bạn, và khoanh việc nào xong thì các việc kia nhẹ đi. |
| sap_xep_lai | Mở lịch tuần này và đánh dấu những ngày đang dồn việc, chưa cần dời việc nào. |
| gop_y | Viết góp ý bạn định nói ra giấy, giữ ý về việc làm và gạch những ý nói về con người. |
| de_xuat | Viết đề xuất thành ba dòng, vấn đề, cách làm, bước đầu, rồi đọc lại xem dòng nào còn thiếu. |
| don_dep | Đi một vòng và ghi ra góc bạn muốn dùng lại trước tiên, chưa cần dọn ngay. |
| ra_ngoai | Ghi ra bạn muốn ra ngoài để làm gì, gặp người hay đổi không khí, rồi chọn một chỗ gần nhà. |
| o_nha | Ghi ra điều bạn cần nhất tối nay, nghỉ hay gặp người, trước khi trả lời lời rủ. |
| doi_thoi_quen | Ghi ra lúc thói quen cũ hay bắt đầu và việc bạn thường làm ngay trước đó. |
| viet_ra | Ghi một dòng về điều đang chiếm đầu bạn nhất, chưa cần viết hết mọi thứ. |
| choice | Viết hai lựa chọn thành hai cột, dưới mỗi cột ghi điều bạn được và điều bạn lo nhất. |

**2. No presumed partner or event.** Ten of the 19 topic openings presumed something the closed
labels do not establish; they now read event-neutral:

| Action × topic | 27/10 | Now | Why |
|---|---|---|---|
| nhan_lai × relationships | Mở lời: “Hôm qua đi chơi với bạn vui lắm, cảm ơn bạn nhé.” | Mở lời: “Mình đọc tin rồi, giờ mình nhắn lại đây.” | invented an outing (Codex r47) |
| nhan_lai × communication | Mở lời: “Hình như mình nói chưa rõ, ý mình là…” | Mở lời: “Mình nhắn lại về chuyện lúc trước, mình muốn nói thêm một chút.” | assumed the reader had been unclear |
| bat_dau × relationships | Mở lời: “Hôm trước nói chuyện với bạn vui ghê, cuối tuần này mình đi cà phê nhé?” | Mở lời: “Mình muốn cùng bạn bắt đầu một việc nhỏ, bạn nghe mình kể nhé?” | assumed an earlier talk and a café date |
| xin_gop_y × relationships | Mở lời: “Mình muốn nghe bạn nghĩ thật về chuyện tình cảm của mình, bạn nói thẳng giúp mình nhé.” | Mở lời: “Mình muốn nghe bạn nghĩ thật về chuyện này, bạn nói thẳng giúp mình nhé.” | assumed a romance ("chuyện tình cảm") |
| gui_di × relationships | Mở lời: “Mình có món quà nhỏ muốn gửi bạn, bạn nhận giúp mình nhé.” | Mở lời: “Mình có cái này muốn gửi bạn, bạn xem khi tiện nhé.” | assumed a gift |
| xin_loi × general, work | Mở lời: “Mình xin lỗi về chuyện hôm trước, phần đó là lỗi của mình. Mình muốn nghe bạn nói.” | Mở lời: “Mình xin lỗi về chuyện vừa rồi, phần đó là lỗi của mình. Mình muốn nghe bạn nói.” | "hôm trước" assumed when it happened (work row too) |
| dat_ranh_gioi × energy | Mở lời: “Tuần này mình chỉ gặp được một buổi, mình hẹn bạn hôm khác nhé.” | Mở lời: “Dạo này mình cần nghỉ nhiều hơn, tuần này mình chỉ nhận một buổi gặp thôi nhé.” | assumed plans already made |
| thu_lai × relationships | Mở lời: “Lâu rồi mình chưa hỏi thăm bạn, dạo này bạn thế nào?” | Mở lời: “Mình muốn thử nói chuyện lại một lần nữa, bạn cho mình vài phút nhé?” | assumed a long silence |
| sap_xep_lai × self_care | Mở lời: “Cuối tuần này mình dọn lại phòng, bạn giúp mình một tay được không?” | Mở lời: “Mình đang xếp lại lịch tuần này cho đỡ dồn, mình dời việc này sang hôm khác được không?” | assumed tidying a room |
| de_xuat × relationships | Mở lời: “Mình có một cách chia việc khác, bạn nghe mình nói hai phút nhé?” | Mở lời: “Mình có một ý muốn đề xuất, bạn nghe mình nói hai phút nhé?” | assumed shared chores |

The other nine openings were reread and kept (they propose a future behaviour; none presumes a
past event or a partner).

Relationships also covers family and friends. Sixteen decided relationships scenes presume a
romantic partner or a date (bat_dau, chia_se, doi_thoi_quen, dung_lai, gop_y, hen_gap, hoi_lai, ket_thuc, nhan_lai, nhan_loi, nho_giup, noi_ra, o_nha, sap_xep_lai, thu_lai, tu_choi); they now show only when the question names a partner
(`question_frame.PARTNER_SIGNALS`: người yêu, người ấy, người cũ, crush, bạn trai, bạn gái, vợ, chồng,
ny, nửa kia, hẹn hò, buổi hẹn, tỏ tình). Otherwise the action's `general` scene stands in, as for the
dropped rows. A test keeps that list equal to the rows with a partner word, with two hand-reviewed
exceptions each way. Limitation: the `general` scene is a different everyday vignette (for "nhắn lại
cho mẹ" it shows a friend's unanswered message); family-specific scenes would be new copy.

**Luna provenance.** Preparation and choice steps trace to closed codes `prep.<key>`; the general
fallback scene traces to `act.<action>.general`. The partner word is read only at render time and
never leaves the engine; the provider sees only which closed code was chosen.

**Frozen readings.** A literal reading persisted under renderer v7 (rendered at `010b27e`, the root
bug: the dating scene) is a test fixture; the service returns it byte for byte.

