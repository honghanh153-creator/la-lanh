# Nhìn lại vòng tự động Claude ⇄ Codex: 30–31.10.2026

Tác giả: Claude. Người review: Codex, qua chính vòng tự động. Thiết kế đang chạy: `docs/operations/collab-auto-loop-plan.md`.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

## 1. Kết quả

**9 PR merge vào `collab/integration`** qua vòng mới, chị không phải chuyển lời giữa hai agent:

| PR | Nhóm | Mở → merge | Vòng tự động | Ghi chú |
|---|---|---|---|---|
| #130 xây vòng tự động | ops | 30/10 21:11 → 21:47 | 2 (2 P1 + 4 P2 → APPROVE) | Lần chạy Codex thật đầu tiên |
| #132 tick không import vòng | ops | 21:50 → 22:03 | 1 | |
| #135 ops đi trước | ops | 22:34 → 23:08 | 1 (P3) | |
| #115 Tarot plain summary | content | chạy 23:08 → 23:16 | 0 (APPROVE @ head có sẵn) | PR con #120 tự đổi base |
| #118 Hợp gu dễ đọc | content | chạy 31/10 09:44 → 09:55 | 1 (2 P2 → fix-forward #138) | |
| #137 tick tự check, chặn PR người ngoài | ops | 09:46 → 11:55 | 3 (P0 bảo mật, P1×3) | owner cho vòng 3 |
| #120 Tarot đợt 2 | content | chạy 12:21 → 12:32 | 0 (APPROVE @ head có sẵn) | |
| #141 cách làm hằng ngày, PATH, D1, D3 | ops | 11:58 → 12:42 | 2 | |
| #142 kiểm tra "máy bận" | ops | 12:44 → 14:29 | 2 | **tick tự làm trọn vòng, không có tay Claude** |

- Khi máy rảnh, một PR đi trọn vòng trong **8–13 phút**. Codex review mất 1–3 phút. Phần tốn thời gian nhất là author check (`pnpm check`): 8–15 phút khi chạy riêng, tới 36 phút khi máy có việc khác.
- Codex bắt được lỗi thật ở mọi PR quy trình lớn. Đáng kể nhất là P0 ở #137: không có bản sửa thì tick sẽ chạy Makefile/test của PR fork trên máy owner trước khi ai review.
- Còn mở cuối ngày: #144 Jyotish 503, #145 bảng trạng thái + checklist, #146 footer kỹ thuật, #139 và #147 chờ owner duyệt copy. Bốn PR privacy (#112, #113, #116, #117) chưa tới lượt.

## 2. Chỗ kẹt và lỗi

| # | Sự cố | Mất | Nguyên nhân gốc | Đã sửa |
|---|---|---|---|---|
| K1 | Autopilot không chạy lượt nào 22:48 → 11:47 | ~13 giờ | Lượt chạy kẹt ở lệnh Bash đầu tiên (chờ quyền); lượt treo chặn mọi lượt theo lịch | Dừng lượt treo; author check chuyển sang tick (#137), autopilot chỉ còn việc sửa |
| K2 | Plan 08:50 không được đăng | ~50 phút | Mac ngủ; launchd không chạy khi máy ngủ | Plan ghi khoảng ngủ (D3, #141); owner chạy `pmset repeat` |
| K3 | Hai `pnpm check` chạy cùng lúc | 1 check bị hủy | Session cũ chạy `checkshas.sh` song song, không có khóa | `check.lock` + từ chối khi máy bận (#137); `checkshas.sh` thay bằng tick (§7.1) |
| K4 | Tick có việc nhưng không làm được gì | cả buổi sáng | Chỉ Claude được chạy author check | #137 |
| K5 | Claude ngồi chờ #137 | ~1 giờ | Chạy nối tiếp, không tách việc nặng/nhẹ | Cách làm hằng ngày §3.2 (#141) |
| K6 | Tick chỉ chạy một lần mỗi giờ | tối đa 1 PR/giờ | Cổng `lastRunHour` | D1 (#141) |
| K7 | Session cũ vẫn mở PR registry (#136) | 1 PR thừa | Quyết định mới chưa tới session đang chạy | Đóng #136; §3.2 mục 5 |
| K8 | Author check FAIL giả (`sha256sum`, `pnpm` không có trên PATH) | 1 receipt sai | PATH của script/launchd thiếu `/sbin` và thư mục `pnpm` | #141; tick kiểm công cụ trước khi chạy |
| K9 | Claude kết luận "FAIL giả" cho #139 trước khi đọc log | 1 ghi chú phải đính chính | Gộp hai FAIL cùng thời lượng thành một nguyên nhân | Luôn đọc log từng PR |
| K10 | Kiểm tra "máy bận" bằng `pgrep -f` báo bận nhầm | tick từ chối #112 | `pgrep -f` khớp cả shell có nhắc tới mẫu | #142 |
| K11 | Author check của tick mất 36 phút | ~25 phút | Claude chạy `pytest` lớn song song | Việc nhẹ chỉ là đọc/viết code và test nhỏ |
| K12 | Vòng đứng yên 15:54 → 17:06 | ~1 giờ | PR ops chờ Claude sửa vẫn chặn mọi nhóm; Claude kết thúc lượt mà không xử lý | #145: nhóm hoạt động là nhóm còn việc cho máy |
| K13 | Claude báo nhầm "PR privacy vừa nhận REQUEST_CHANGES" | 1 thông tin sai cho owner | Đọc giờ UTC ngày 30/10 thành chiều 31/10 | Đính chính; đọc ngày đầy đủ |
| K14 | #144 FAIL vì định dạng code | 1 vòng check | Không chạy `ruff format` trước khi push | Checklist: lint/format phần vừa sửa trước khi push |

## 3. Phát hiện ngoài vòng tự động

- **Khám phá với giờ sinh khoảng** (owner báo, #143): bản đọc rỗng với copy vô nghĩa (E1), Jyotish 503 (E2), thẻ hành tinh lặp câu (E3), footer kỹ thuật lộ ra (E4). E2/E3/E4 đã có PR; E1 đang làm (cần sửa precision công khai và evidence của Jyotish trước khi mở PR).
- **Ảnh chụp của owner không phải lá số của owner:** các cung khớp hồ sơ tổng hợp của bộ test (sinh 1997-09-20, không có giờ chính xác). Owner đang kiểm tra tab Mình. Nếu đúng là hồ sơ test thì không có sự cố hiện nhầm dữ liệu.

## 4. Cách làm đã đổi hôm nay

1. Việc nặng nối tiếp và đi qua tick; Claude làm việc nhẹ song song, không ngồi chờ (§3.2).
2. Checklist quyết định 5 câu hỏi (`decision-checklist.md`, #145). Cải thiện trải nghiệm người dùng mà không vướng Q1–Q5 thì làm luôn.
3. Bảng trạng thái trên issue plan, cập nhật mỗi tick và trước mỗi việc nặng (#145).
4. Mỗi PR sửa vòng tự động chạy thử trong đúng môi trường launchd (`env -i` + PATH của cron) trước khi merge.

## 5. Đề xuất cho Codex review

| # | Đề xuất | Lợi ích | Rủi ro |
|---|---|---|---|
| D2 | Tick báo `ops-alert` khi có lượt autopilot không tiến triển quá 30 phút | K1 không kéo dài qua đêm | Chỉ báo, không tự dừng session |
| D4 | Đánh giá lại phần khóa việc nặng của #134 (owner tạm dừng) so với `check.lock` | Một cơ chế khóa cho mọi session | Trùng chức năng |
| D6 | Author check chỉ chạy phần liên quan cho PR chỉ đổi docs | Giảm 8–15 phút mỗi PR docs | Phải chứng minh tập kiểm tra rút gọn đủ an toàn |
| D7 | Claude kiểm hàng đợi `claude-fix` trước khi kết thúc mỗi lượt trả lời | Tránh K12 | Không |

## 5b. Liên hệ: "hệ thống AI tự thối rữa" (video owner gửi 31.10)

Nguồn: reel "AIOS — Agentic Operating System" của kênh AI 5 Phút (Facebook). Claude chỉ đọc được phần mô tả bằng chữ, không nghe/xem nội dung video. Ý chính: xây hệ thống agent theo lớp, từ "danh tính" (CLAUDE.md: ai, làm gì, không bao giờ làm gì) tới công cụ; mỗi lớp có nhịp bảo trì riêng; nếu không bảo trì, hệ thống "thối" dần (quy tắc cũ chồng quy tắc mới, AI làm sai, phải nhắc lại).

Áp vào Lá Lành. Rà ngay hôm nay tìm ra 5 chỗ "thối", đã dọn:

| Chỗ thối | Hậu quả nếu để | Đã sửa |
|---|---|---|
| Memory "luôn đưa owner prompt dán cho Codex" | Claude tiếp tục bắt owner chuyển lời dù script đã tự gọi Codex | Đánh dấu SUPERSEDED |
| Memory autopilot nhắc `codex-prompt.md` gộp | Autopilot viết file không ai dùng | Cập nhật theo vòng mới |
| Memory "gom việc lớn rồi mới giao Codex" | PR to, review lâu, trái vòng tự động | Chỉnh: ngày làm nhiều việc, PR nhỏ |
| Hàng đợi autopilot: "Merge any approved PR (owner order)" | Mâu thuẫn quy tắc merge tự động vào integration | Sửa: chỉ `main`/release/deploy cần lệnh owner |
| Hàng đợi autopilot: việc "bấm Run now" đã xong | Nhắc owner việc đã làm | Xoá |

Các lớp của mình hiện nay và nhịp bảo trì đề xuất:

| Lớp | Ở đâu | Nhịp |
|---|---|---|
| Danh tính, luật cứng | `CLAUDE.md`, `AGENTS.md`, danh sách cấm (checklist §2) | khi owner đổi quyết định |
| Quyết định | `decision-checklist.md`, plan §2 | ghi ngay khi có quyết định mới |
| Trí nhớ | memory của Claude, `queue.md` | **rà mỗi tuần** (dễ thối nhất) |
| Quy trình | lịch autopilot (SKILL), script vòng tự động | qua PR + Codex review |
| Công cụ | launchd, `collab-*.mjs`, hook | test + chạy thử đúng môi trường |

Đề xuất thêm cho Codex đánh giá:

| # | Đề xuất | Lợi ích | Rủi ro |
|---|---|---|---|
| D8 | Rà "thối" mỗi tuần (Chủ nhật): Claude so memory, `queue.md`, SKILL autopilot với plan và checklist hiện hành; đánh dấu SUPERSEDED, xoá việc đã xong; báo owner một dòng | Ngăn quy tắc cũ quay lại | Tốn 1 lượt Claude mỗi tuần |
| D9 | Hook trước khi push: lint/format đúng phần đã sửa (K14) — tách phần này khỏi #134 | Không còn FAIL vì định dạng | Hook chạy trên máy agent, cần owner bật |
| D10 | Đóng gói cách làm hằng ngày (check → sửa → bổ sung plan → báo cáo cuối ngày) thành một skill Claude Code dùng chung cho mọi session | Session mới (kể cả session cũ như 09b7c769) làm đúng quy trình mà không cần nhắc | Phải giữ skill đồng bộ với plan (lớp "quy trình") |

## 6. Việc ngày mai

1. E1 (#143) đến PR.
2. Theo dõi #144/#145/#146 qua tick; privacy #112–#117 theo thứ tự.
3. Owner: duyệt copy #139, #147; xác nhận ngày sinh trong tab Mình; chạy `sudo pmset repeat wakeorpoweron MTWRFSU 08:45:00`.

Nguồn: log `~/.cache/la-lanh-collab/logs`, comment `Author check`/`Review verdict` trên các PR, `collab-turn --report`, issue #143.
