# Kế hoạch tiếp theo: data privacy → nội dung → game (23/10/2026)

Owner quyết định 23/10/2026:

1. Thứ tự làm: **(1) data privacy → (2) nội dung, toàn bộ → (3) game.** Không bắt đầu giai đoạn sau khi giai đoạn trước chưa
   đạt tiêu chí thoát, trừ việc chuẩn bị tài liệu không đụng runtime.
2. **Nơi bình yên hoãn toàn bộ.** Không viết code, không review, không merge thêm. PRD đã merge (#44) giữ nguyên làm tài
   liệu lưu trữ; #68 (PRD v0.7) để mở, không review và không merge cho tới khi owner mở lại.
3. **Tarot Luna được đưa vào giai đoạn nội dung** (trước đây hoãn theo quyết định C6 ngày 18/10).

Cách phối hợp (không đổi): Claude làm, Codex review theo đúng SHA. Mỗi bước là một PR nhỏ có regression đỏ trên base →
xanh trên head. Chỉ merge khi có `Review verdict: APPROVE @ <full SHA>` khớp head. Merge vào `main`, deploy, chạm server/DB
thật, đổi IAM/secret/budget hay bật provider chỉ làm khi owner ra lệnh, theo runbook. Operator làm các bước cần quyền máy
chủ; counsel trả lời câu hỏi pháp lý. Ngân sách Luna giữ trên server, không ghi vào git.

## Vì sao Tarot Luna chưa làm tới giờ

- Code đã có: `apps/api/app/domains/tarot/rewrite.py`, `meaning_brief.py`, chain `tarot-renderer → tarot-meaning-brief-v1
  → gpt-6-luna-tarot-v3 → tarot-rewrite-gates/v3` (runbook Luna). Nhưng `CHART_FREE_REWRITE_SURFACES = {"daily_home"}`
  (`apps/api/app/config.py:18`) chặn mọi surface khác, nên Tarot không bao giờ được gửi đi.
- Quyết định owner 18/10 (C6/T06): thêm cảnh và AI cho Tarot cần duyệt chi phí riêng. Audit v2 giữ Tarot Luna tắt sau
  các cổng: brief bám đúng câu được hỏi (T01), prompt/provenance/canary mới, chiến lược cho stance, và đánh giá với
  người đọc thật.
- Các cổng privacy chung chưa xong: DPA chưa ký, roster pilot (RC-05, #61) chưa deploy, câu hỏi Tarot là văn bản tự do
  nhạy cảm và không được rời máy chủ ở dạng thô.

## Giai đoạn 0: đưa hàng đợi hiện tại lên (đang làm)

| Bước | Ai | Việc |
|---|---|---|
| 0.1 | Codex | Review lại 6 head: #45 `4e02c46`, #47 `de6f666`, #48 `2d5636b`, #54 `aab05a1` (chỉ giải conflict), #60 `3de5ac4`, #64 `84e3677` |
| 0.2 | Codex (khi owner cho phép) | Merge **#66 trước** (sửa `pnpm check` đỏ trên `7ca22cb`), rồi #49 trước #48 (cùng sửa data map, giữ cả hai đoạn), rồi các PR đã APPROVE; chạy `pnpm check` trên `collab/integration` |
| 0.3 | Operator | Real Compose proof cho kill switch (#40) trên máy dùng một lần; đếm tổng hợp consent viết lại Radar/Matching trước khi deploy #61 |
| 0.4 | Codex/operator (khi owner ra lệnh) | `collab/integration` → `main`, backup, deploy theo runbook, smoke; receipt release |

Tiêu chí thoát: release mới chạy trên production, có receipt; kill switch đã kiểm trên Compose thật.

## Giai đoạn 1: data privacy

| ID | Việc | Ai | PR/artifact | Tiêu chí thoát |
|---|---|---|---|---|
| P07 | Sổ ghi xoá có khoá (phương án A) + chạy lại retention (C) sau restore; cài backup timer, alert, restore thử, receipt Supabase backup/PITR | Claude (code), operator (cài/chạy) | PR journal A + receipt operator | Restore thử trên bản sao không làm sống lại dữ liệu đã xoá; B (không restore vào service) chỉ bỏ khi PR A được duyệt |
| P06 | Số đếm tổng hợp dữ liệu cũ chưa mã hoá (staging rồi production, kênh riêng); backfill/purge theo cột "Preferred" | Operator (đếm), Claude (tool), owner (xác nhận) | `check_legacy_plaintext` + PR backfill | Số đếm về 0; PR gỡ reader tương thích cũ |
| P09 D2 | Kênh yêu cầu quyền thủ công cho B: xác minh bằng link mời/receipt hoặc A xoá hộ, không thu lại ngày sinh | Claude | PR + quy trình vận hành | Có đường xem/xuất/xoá cho B khi không còn receipt; log không chứa dữ liệu B |
| P09 D3/D4, P10 | Cơ sở pháp lý cho private check, thông báo cho B, DPA, xuyên biên giới (Đức), DPIA, App Privacy/Data Safety | Counsel, owner | Dossier #52 | Có câu trả lời của counsel; copy/consent/data map cập nhật nếu cần (PR riêng, owner duyệt copy) |
| P08 | Canary log ingress/Docker trên host; app native ký thật kiểm theo MASVS (cookie, storage, backup, crash, deep link, xoá) | Operator, thiết bị | Receipt | Không có câu hỏi/ngày sinh/token trong log thật; checklist MASVS đạt |
| P03 RC-23–27 | Bằng chứng đường dẫn ephemeris thực tế (`SE_EPHE_PATH`, mount, file phụ, nguồn image) | Operator | Receipt theo checklist #59 | Năm điều trong checklist đều có bằng chứng |
| P11 | Roster pilot (#61) đã deploy; DPA ký trước khi mở thêm surface Luna nào | Owner, operator | Receipt | Điều kiện bắt buộc cho Tarot Luna ở giai đoạn 2 |
| P12 | Google sign-in: xoay secret qua kênh bảo vệ, kiểm thử chấp nhận trên staging | Operator, owner | Receipt | Chỉ bật khi owner cho phép |

Tiêu chí thoát giai đoạn 1: P06/P07/P08/RC-23–27 có receipt, D2 chạy được, counsel đã trả lời D3/D4 và DPA. Không ghi
"đã xong privacy" khi còn mục nào chỉ có tài liệu.

## Giai đoạn 2: nội dung (toàn bộ)

Bắt đầu bằng việc owner duyệt copy (làm song song được với giai đoạn 1 vì chỉ là đọc workbook), sau đó mới wiring.

| ID | Việc | Ai | Phụ thuộc |
|---|---|---|---|
| T01 còn sót | Luật "tín hiệu dài nhất" và goal theo từ khoá đè lên hành động được hỏi | Claude, PR nhỏ có regression | #45 đã merge |
| T02/T03 | Owner duyệt workbook #67 → wiring cảnh/bước theo hành động, bump version, giữ bài đã lưu, fallback approval có evidence | Owner duyệt, Claude làm | T01 |
| T04 | Kiểm screen reader và tên dài trên thiết bị; owner chốt thứ tự Anh · Việt | Thiết bị, owner | #63 |
| T05 | Rubric hiểu nghĩa/đáp đúng câu hỏi + gate đo trên bank | Claude, owner duyệt rubric | T02/T03 |
| **T06 Tarot Luna** | (a) brief v2 chỉ gửi mã nhãn đóng của hành động/chủ đề/vai và nội dung đã duyệt, **không bao giờ gửi câu hỏi thô**; (b) prompt `gpt-6-luna-tarot-v4` + gate + canary + provenance; (c) corpus tổng hợp + đánh giá người đọc; (d) owner duyệt chi phí (ghi trên server), consent/data map/store disclosure; (e) thêm `tarot` vào allowlist bằng PR riêng, pilot ≤ N phiên opt-in | Claude (a–c, e), owner (d), Codex review từng bước | Giai đoạn 1 xong (DPA, RC-05 deploy), T01–T05 |
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
- Giai đoạn 1: ký DPA (hoặc quyết không ký), chuyển câu hỏi cho counsel.
- Giai đoạn 2: duyệt #67, #65 (chọn giọng), #64, copy #62/#63; mức chi phí cho Tarot Luna (gửi riêng, không ghi git).
- Giai đoạn 3: chọn hướng game.
