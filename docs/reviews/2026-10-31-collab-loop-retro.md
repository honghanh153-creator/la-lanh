# Nhìn lại vòng tự động Claude ⇄ Codex: 30–31.10.2026

Tác giả: Claude. Người review: Codex (qua chính vòng tự động). Thiết kế đang chạy: `docs/operations/collab-auto-loop-plan.md`.
Mọi giờ là giờ Việt Nam. Chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

## 1. Kết quả theo số liệu

| PR | Nhóm | Mở → merge | Vòng tự động | Ghi chú |
|---|---|---|---|---|
| #130 xây vòng tự động | ops | 21:12 → 21:47 (35 phút) | 2 (RC: 2 P1 + 4 P2 → APPROVE) | Lần chạy Codex thật đầu tiên |
| #132 tick không import vòng | ops | 21:50 → 22:03 (13 phút) | 1, không phát hiện | Sửa lỗi tick treo |
| #135 ops đi trước | ops | 22:34 → 23:08 (34 phút) | 1, 1 P3 | Chờ máy rảnh ~25 phút |
| #115 Tarot plain summary | content | chạy 23:08 → 23:16 (8 phút) | 0 (APPROVE thủ công có sẵn @ head) | PR con #120 tự đổi base |
| #118 Hợp gu dễ đọc | content | chạy 09:44 → 09:55 (11 phút) | 1, 2 P2 → fix-forward #138 | #138 sửa ngay trong ngày (#139) |
| #137 tick tự chạy author check | ops | 09:46 → (đang chạy vòng 3) | 2 RC → `needs-owner`, owner cho vòng 3 lúc 11:46 | Codex bắt 1 P0 bảo mật thật |

So với 11–30.10 (trung vị mở PR → merge 22 giờ, vòng review chờ owner chuyển lời): khi máy rảnh, một PR đi trọn vòng trong **8–13 phút**. Codex review mất 1–3 phút. Phần tốn thời gian nhất là author check (`pnpm check`, 7–15 phút).

Chất lượng review: Codex tìm ra lỗi thật ở mọi PR quy trình lớn. Đáng kể nhất là P0 ở #137: nếu không có bản sửa, tick sẽ chạy Makefile/test của PR fork trên máy owner trước khi ai review.

## 2. Chỗ bị kẹt hôm nay

| # | Sự cố | Mất bao lâu | Nguyên nhân gốc |
|---|---|---|---|
| K1 | Autopilot không chạy lượt nào từ 22:48 tối 30/10 tới 11:47 sáng 31/10 | ~13 giờ | Lượt 22:48 kẹt ở lệnh Bash đầu tiên (chờ quyền); lượt treo chặn mọi lượt theo lịch sau đó. Lượt 27/10 cũng treo tương tự. |
| K2 | Plan 08:50 không được đăng, đăng tay lúc 09:41 | ~50 phút | Mac ngủ; launchd không chạy job khi máy ngủ. |
| K3 | Hai `pnpm check` chạy cùng lúc (22:25, 23:16) | phải hủy 1 lần check | Session cũ chạy `checkshas.sh` song song trong `la-lanh-claude`, không có khóa. |
| K4 | Tick có việc nhưng không làm được gì cả buổi sáng | cả buổi sáng | Mọi PR đang ở bước "cần author check", mà trước #137 chỉ Claude được chạy check. |
| K5 | Claude ngồi chờ #137 thay vì làm việc khác | ~1 giờ | Cách làm: chạy nối tiếp từng PR, không tách việc nặng và việc nhẹ. |
| K6 | Tick chỉ chạy một lần mỗi giờ | tối đa 1 PR/giờ | Cổng `lastRunHour` trong `tick()`. |
| K7 | Session cũ vẫn mở PR registry (#136) sau khi owner đã dừng | 1 PR thừa | Quyết định mới chưa tới được session đang chạy. |

## 3. Đã sửa hôm nay

- K3, K4: #137 (tick tự chạy author check trong clone riêng, `check.lock`, từ chối khi máy đang có check, `CI=1`). Vòng `checkshas.sh` được đánh giá (plan §7.1) và thay bằng cơ chế này.
- Bảo mật: #137 chỉ chạy/review/merge PR của tài khoản owner từ nhánh trong repo.
- K1: dừng 3 lượt autopilot treo; sửa mẫu kiểm tra "máy bận" của autopilot (`contracts:check|vitest|pytest|playwright|codex exec`).
- K5: cách làm mới ở mục 4, ghi vào thiết kế.
- K7: đóng #136; owner xác nhận ngừng registry.

## 4. Cách làm đã tối ưu (đề xuất ghi vào thiết kế)

1. **Tách việc nặng và việc nhẹ.** Việc nặng (`pnpm check`) chạy nối tiếp, mỗi lúc một việc trên cả máy. Trong lúc đó Claude làm việc nhẹ: sửa fix-forward, viết code, viết test, viết docs. Claude không ngồi chờ việc nặng.
2. **Việc nặng thuộc về tick.** Author check, review, merge đi qua tick hoặc các script của vòng tự động. Không session nào tự chạy `pnpm check` bằng script riêng.
3. **Fix-forward là việc kế tiếp.** Issue `fix-forward` mới thuộc cùng nhóm ưu tiên với PR gốc và được làm ngay trong ngày.
4. **Đầu ngày:** Mac tự thức lúc 08:45 (`pmset repeat`). Claude đọc `collab-turn --report` và dọn lượt autopilot treo.
5. **Cuối ngày:** nhìn lại quy trình và viết report vào `docs/reviews/` (như file này) để Codex review qua vòng tự động.

## 5. Đề xuất tiếp theo (cần review, chưa làm)

| # | Đề xuất | Lợi ích | Rủi ro |
|---|---|---|---|
| D1 | **Làm trong PR này:** bỏ cổng "một lần mỗi giờ" (K6); tick làm việc mỗi lần chạy khi máy rảnh, khóa bảo đảm chạy nối tiếp | 1 PR/giờ → khoảng 4 PR/giờ | Tốn hạn mức Codex nhanh hơn (trần 12/ngày vẫn giữ) |
| D2 | Tick phát hiện lượt autopilot treo (không có tiến triển > 30 phút) và mở `ops-alert` | K1 không kéo dài qua đêm | Chỉ báo, không tự dừng session |
| D3 | **Làm trong PR này:** plan 08:50 kèm dòng "máy không chạy tick từ … tới …" khi heartbeat cũ hơn 30 phút | Owner thấy K2 ngay | Không |
| D4 | Tách phần khóa việc nặng của #134 (owner tạm dừng) thành PR riêng nếu vẫn cần sau #137 | Một cơ chế khóa cho mọi session | Trùng với `check.lock` của #137; cần so sánh trước |

## 6. Còn mở

- #137 vòng 3 (owner duyệt chạy lúc 11:46).
- #139 (#138) chờ author check.
- Hàng content: #120; privacy: #112, #113, #116, #117 (US-23 #122–124 chờ #113).
- Owner: chạy `sudo pmset repeat wakeorpoweron MTWRFSU 08:45:00`; bấm "Always allow" cho autopilot.

Nguồn: log `~/.cache/la-lanh-collab/logs`, comment verdict/author check trên các PR, `collab-turn --report`.
