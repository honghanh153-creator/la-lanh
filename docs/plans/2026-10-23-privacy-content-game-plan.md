# Kế hoạch tiếp theo: data privacy → nội dung → game (23/10/2026)

Owner quyết định 23/10/2026:

1. Thứ tự làm: **(1) data privacy → (2) nội dung, toàn bộ → (3) game.** Không bắt đầu giai đoạn sau khi giai đoạn trước chưa
   đạt tiêu chí thoát, trừ việc chuẩn bị tài liệu không đụng runtime.
2. **Nơi bình yên hoãn toàn bộ.** Không viết code, không review, không merge thêm. PRD đã merge (#44) giữ nguyên làm tài
   liệu lưu trữ; #68 (PRD v0.7) để mở, không review và không merge cho tới khi owner mở lại.
3. **Tarot Luna được đưa vào giai đoạn nội dung** (trước đây hoãn theo quyết định C6 ngày 18/10).
4. **DPA không phải điều kiện deploy hay mở Luna.** Owner ký khi thuận tiện (quyết định 21/10 và 23/10); việc ký là
   một mục theo dõi riêng của owner, không chặn bước nào trong plan.

Cách phối hợp (không đổi): Claude làm, Codex review theo đúng SHA. Mỗi bước là một PR nhỏ có regression đỏ trên base →
xanh trên head. Chỉ merge khi có `Review verdict: APPROVE @ <full SHA>` khớp head. Merge vào `main`, deploy, chạm server/DB
thật, đổi IAM/secret/budget hay bật provider chỉ làm khi owner ra lệnh, theo runbook. Operator làm các bước cần quyền máy
chủ; counsel trả lời câu hỏi pháp lý. **Ngân sách Luna đã được owner duyệt: một mức tổng chung cho mọi surface Luna**
(Note ngày, Tarot, Hợp gu…), con số giữ trên server, không ghi vào git. Mở thêm surface không cần duyệt chi phí lại; chỉ
cần nằm trong mức chung đó.

## Vì sao Tarot Luna chưa làm tới giờ

- Code đã có trên `collab/integration` `7ca22cb` (đã làm, không cần làm lại):
  - Bài **framed** (rules version hiện hành): `tarot-meaning-brief-v3` có provenance theo catalog
    (`tarot/provenance.py:54`, `framed_brief`; `rewrite.py:_brief`), renderer `gpt-6-luna-tarot-v4` (`rewrite.py:50`),
    gate `tarot-rewrite-gates/v4`, schema `tarot-rewrite/v1` (`content_rewrite/registry.py:133`).
  - Bài **legacy** (rules version cũ): `tarot-meaning-brief-v2` (`meaning_brief.py:11`), cùng renderer và gate v4.
  - Không gửi câu hỏi thô: reducer gửi `focus_sentence` cố định; Roast không tạo request.
  - Nhưng `CHART_FREE_REWRITE_SURFACES = {"daily_home"}` (`apps/api/app/config.py:18`) chặn mọi surface khác, nên Tarot
    không bao giờ được gửi đi. #73 (S4) thêm `tarot` vào allowlist; allowlist **không** phải bật.
- Quyết định owner 18/10 (C6/T06) để AI cho Tarot chờ duyệt chi phí; sau đó owner đã chốt một ngân sách tổng chung cho mọi
  surface Luna, nên phần chi phí đã xong. Audit v2 vẫn giữ Tarot Luna tắt sau
  các cổng còn lại: brief bám đúng câu được hỏi (T01, #45), chiến lược cho stance, và đánh giá với người đọc thật.
  Prompt v4, provenance brief v3 và canary đã có trong code.
- Các cổng privacy chung chưa xong: roster pilot (RC-05, #61) chưa deploy, câu hỏi Tarot là văn bản tự do
  nhạy cảm và không được rời máy chủ ở dạng thô.

## Giai đoạn 0: đưa hàng đợi hiện tại lên (đang làm)

| Bước | Ai | Việc |
|---|---|---|
| 0.1 | Codex | Review lại 6 head: #45 `4e02c46`, #47 `de6f666`, #48 `2d5636b`, #54 `aab05a1` (chỉ giải conflict), #60 `3de5ac4`, #64 `84e3677` |
| 0.2 | Codex (khi owner cho phép) | Merge **#66 trước** (sửa `pnpm check` đỏ trên `7ca22cb`), rồi #49 trước #48 (cùng sửa data map, giữ cả hai đoạn), rồi các PR đã APPROVE; chạy `pnpm check` trên `collab/integration` |
| 0.3 | Operator | Real Compose proof cho kill switch (#40) trên máy dùng một lần; đếm tổng hợp consent viết lại Radar/Matching trước khi deploy #61 |
| 0.4 | Codex/operator (khi owner ra lệnh) | `collab/integration` → `main`, backup, deploy theo runbook, smoke; receipt release |

Tiêu chí thoát: release mới chạy trên production, có receipt; kill switch đã kiểm trên Compose thật.

## Sprint Luna (23/10/2026): làm cơ chế viết lại tối ưu cho Tarot và Hợp gu

Kết quả rà ngày 23/10: content engine dựng bản mask → Luna viết lại → gate → merge; gate từ chối thì giữ bản của engine.
Tarot đã đủ code (mask chỉ mã nhãn đóng và nội dung đã duyệt, không gửi câu hỏi thô; merge có gate chặt), chỉ chưa có
trong allowlist. Hợp gu có code nhưng payload còn nhãn kỹ thuật và gate merge yếu. Surface tắt **không** lưu job
(`ContentRewriteService.enqueue` từ chối khi rollout tắt), nhưng service Tarot/Hợp gu vẫn dựng payload rồi ghi log enqueue
bị từ chối, một việc thừa.

| Bước | Việc | Thuộc giai đoạn | Tiêu chí xong |
|---|---|---|---|
| S1 (#70, APPROVE @ `4c08e3c`) | Service Tarot/Hợp gu chỉ dựng payload và gọi enqueue khi surface đó đang bật; tránh dựng payload và log enqueue không cần thiết khi chỉ Note ngày bật | 1 (tối thiểu hoá dữ liệu) | Test: rollout chỉ `daily_home` ⇒ Tarot/Radar không gọi enqueue; Daily vẫn gọi |
| S2 (#71, APPROVE @ `58192de`) | Payload Hợp gu bỏ nhãn kỹ thuật (hành tinh, góc chiếu, nhà), chỉ gửi nghĩa đã dựng và mức độ | 1 | Test chứng minh payload Radar không chứa tên hành tinh/góc/nhà; prompt và gate vẫn chạy |
| S3 (#72, đang review) | Gate merge Hợp gu ngang Tarot: gate nghĩa và chống thao túng, giữ ngữ cảnh, giữ nguyên câu theo cặp hành tinh (R03) | 2 | Test từ chối output đổi ngữ cảnh, xoá câu theo contact, hoặc trái nghĩa. **Còn mở:** gate giữ giọng bằng máy |
| S4 (#73, APPROVE @ `46059af`, chỉ phần allowlist) | Thêm `tarot` vào allowlist kèm test payload không có dữ kiện lá số | 2 | Code: xong khi #73 merge (sau #45, #61, #66). **Chưa làm:** bật rollout, pilot trong giới hạn người hiện có, receipt pilot và canary trên môi trường thật — cần lệnh owner/operator |
| S5 | Bật Hợp gu Luna | 2 | Sau khi R03 được duyệt và wiring xong, S2/S3 đã merge |

Mỗi bước một PR nhỏ có regression đỏ → xanh; xong bước nào gửi prompt review cho Codex ngay. Full API trên `7ca22cb` còn
1 lỗi pin `approved_release` (`tests/grammar/test_grammar.py:367`) mà #66 sửa; chưa ghi là hoàn toàn xanh cho tới khi #66 vào.

## Giai đoạn 1: data privacy

| ID | Việc | Ai | PR/artifact | Tiêu chí thoát |
|---|---|---|---|---|
| P07 | Sổ ghi xoá có khoá (phương án A) + chạy lại retention (C) sau restore; cài backup timer, alert, restore thử, receipt Supabase backup/PITR | Claude (code), operator (cài/chạy) | PR journal A + receipt operator | Restore thử trên bản sao không làm sống lại dữ liệu đã xoá; B (không restore vào service) chỉ bỏ khi PR A được duyệt |
| P06 | Số đếm tổng hợp dữ liệu cũ chưa mã hoá (staging rồi production, kênh riêng); backfill/purge theo cột "Preferred" | Operator (đếm), Claude (tool), owner (xác nhận) | `check_legacy_plaintext` + PR backfill | Số đếm về 0; PR gỡ reader tương thích cũ |
| P09 D2 | Kênh yêu cầu quyền thủ công cho B: xác minh bằng link mời/receipt hoặc A xoá hộ, không thu lại ngày sinh | Claude | PR + quy trình vận hành | Có đường xem/xuất/xoá cho B khi không còn receipt; log không chứa dữ liệu B |
| P09 D3/D4, P10 | Cơ sở pháp lý cho private check, thông báo cho B, xuyên biên giới (Đức), DPIA, App Privacy/Data Safety; DPA owner ký khi thuận tiện (không chặn) | Counsel, owner | Dossier #52 | Có câu trả lời của counsel; copy/consent/data map cập nhật nếu cần (PR riêng, owner duyệt copy) |
| P08 | Canary log ingress/Docker trên host; app native ký thật kiểm theo MASVS (cookie, storage, backup, crash, deep link, xoá) | Operator, thiết bị | Receipt | Không có câu hỏi/ngày sinh/token trong log thật; checklist MASVS đạt |
| P03 RC-23–27 | Bằng chứng đường dẫn ephemeris thực tế (`SE_EPHE_PATH`, mount, file phụ, nguồn image) | Operator | Receipt theo checklist #59 | Năm điều trong checklist đều có bằng chứng |
| P11 | Roster pilot (#61) đã deploy, có số đếm consent trước deploy | Operator | Receipt | Điều kiện cho Tarot Luna ở giai đoạn 2 |
| P12 | Google sign-in: xoay secret qua kênh bảo vệ, kiểm thử chấp nhận trên staging | Operator, owner | Receipt | Chỉ bật khi owner cho phép |

Tiêu chí thoát giai đoạn 1: P06/P07/P08/RC-23–27 có receipt, D2 chạy được, counsel đã trả lời D3/D4. DPA không thuộc tiêu chí thoát. Không ghi
"đã xong privacy" khi còn mục nào chỉ có tài liệu.

## Giai đoạn 2: nội dung (toàn bộ)

Bắt đầu bằng việc owner duyệt copy (làm song song được với giai đoạn 1 vì chỉ là đọc workbook), sau đó mới wiring.

| ID | Việc | Ai | Phụ thuộc |
|---|---|---|---|
| T01 còn sót | Luật "tín hiệu dài nhất" và goal theo từ khoá đè lên hành động được hỏi | Claude, PR nhỏ có regression | #45 đã merge |
| T02/T03 | Owner duyệt workbook #67 → wiring cảnh/bước theo hành động, bump version, giữ bài đã lưu, fallback approval có evidence | Owner duyệt, Claude làm | T01 |
| T04 | Kiểm screen reader và tên dài trên thiết bị; owner chốt thứ tự Anh · Việt | Thiết bị, owner | #63 |
| T05 | Rubric hiểu nghĩa/đáp đúng câu hỏi + gate đo trên bank | Claude, owner duyệt rubric | T02/T03 |
| **T06 Tarot Luna** | **Đã có trong code** (không làm lại, không hạ version): brief v3 framed có provenance / brief v2 legacy, chỉ mã nhãn đóng và nội dung đã duyệt, không gửi câu hỏi thô; renderer `gpt-6-luna-tarot-v4`, gate `tarot-rewrite-gates/v4`, canary; allowlist (#73, chờ merge). **Còn lại:** (c) corpus tổng hợp + đánh giá người đọc; (d) consent/data map/store disclosure, dùng chung ngân sách Luna đã duyệt (cap trên server); (e) owner/operator bật rollout, pilot ≤ N phiên opt-in, receipt và canary trên môi trường thật | Claude (c–d), owner duyệt copy consent, operator (e), Codex review từng bước | Giai đoạn 1 xong (RC-05 #61 đã deploy), #45, #66, T01–T05 |
| R03 | Owner duyệt workbook #65 (chọn `deep_dive` hay `roast`) → catalog `radar/contact_copy.py` + wiring thay câu chung, variant theo seed để đạt AC02/AC03; bỏ strict xfail khi gate #47 xanh thật | Owner, Claude | #47 |
| R04 | Owner quyết spec #64 → API/UI khoảng điểm, adapter cho bài cũ | Owner, Claude | R03 |
| R05 | Freeze variant lúc tạo + grammar manifest trên output thật | Claude | R03 |
| R07 | Copy consent nhập tay/Roast theo câu trả lời D3 | Owner, counsel, Claude | Giai đoạn 1 |
| Daily M1 | Review pilot Luna Daily ngày 04/11/2026 (≤ 20 opt-in, gate 670 chưa đạt theo ngoại lệ owner, không EvaluationRecord giả); quyết mở rộng hay giữ | Owner, Codex, Claude | — |

Tiêu chí thoát giai đoạn 2: mọi gate nội dung (Tarot audit, US-22 AC01–AC03, T05) xanh trên output thật; copy mới đều có
owner duyệt; Tarot Luna pilot có số liệu đánh giá, không chỉ test máy.

## Giai đoạn 3: game

1. **Chốt phạm vi trước (owner):** repo chưa có tính năng game, chỉ có ý tưởng trong `docs/ideation`:
   `2026-09-28-astro-tarot-campus-referral-games-ideation.html` (game nhóm "Vũ Trụ Leak") và
   `2026-09-08-short-game-reveal-onboarding-ideation.html` (game reveal lúc onboarding). Owner chọn một hướng.
2. PRD → user story/AC → privacy review (dữ liệu nhóm, chia sẻ, trẻ vị thành niên) → build theo từng PR.
3. Giữ nguyên tắc sản phẩm đã có test: không streak, không coin/XP, không gây áp lực quay lại
   (`apps/web/src/shared/ui/companion/growth.test.ts`).

## Owner cần trả lời

- Giai đoạn 0: cho phép merge và deploy khi Codex APPROVE.
- Giai đoạn 1: chuyển câu hỏi cho counsel. DPA ký khi thuận tiện, không chặn deploy.
- Giai đoạn 2: duyệt #67, #65 (chọn giọng), #64, copy #62/#63. Chi phí Luna đã chốt (ngân sách chung), không cần quyết lại.
- Giai đoạn 3: chọn hướng game.
