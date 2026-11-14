# Nhìn lại vòng tự động Claude ⇄ Codex: 13.11.2026

Tác giả: Claude (lượt retro tự động 13.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Nguồn số liệu: `~/.cache/la-lanh-collab/logs/tick-2026-11-13.log`, `state/2026-11-13.json`, `collab-turn --report` (13.11 23:40), `gh pr list --state merged`, 20 comment `Review verdict` của Codex trên PR được động tới hôm nay, `queue.md` của autopilot, issue #470 và #479. Mọi ngày trước đều đã có file retro (#432 của 11.11 và #455 của 12.11 merge hôm nay).

Báo theo Autopilot v2 (owner duyệt 12.11): số việc thật, không chia cho 20.

## 1. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| PR merge vào integration | 13 | #451 (10:34) tới #483 (22:31) |
| PR merge vào `main` (owner ra lệnh phát hành) | 2 | #464 R1 (12:16), #472 R2 (18:13) |
| Việc thật mới merge | **2** | #448, #450 |
| Việc đã lên bản chạy thật | **toàn bộ integration tới R2** | gồm 11 việc của 12.11 và #448, #450. Kiểm bằng `git merge-base --is-ancestor`: #412, #438, #442, #448, #450 đều có trên `main`. Integration còn cách `main` 20 commit (hôm qua 797) |
| PR không tính | 11 | công cụ vòng (#451, #462), test (#460, #467), phát hành và đồng bộ (#463, #474), tài liệu (#432, #454, #455, #473, #483) |
| Lượt Codex chạy | 26, lỗi 0 | `state/2026-11-13.json` |
| Lượt tick | 73 (72 ran, 1 ran-with-errors) | ngoài 53 lượt "closed" ban đêm |
| Hàng chờ trống | **1 phút** | hôm qua 5 phút |
| PR mở ở hàng chờ cuối ngày | 22 | 10 PR sẵn sàng, trần là 5 |

| Việc | Loại | PR |
|---|---|---|
| Vùng bấm 44px ở phần ghi chú tín hiệu | Sửa giao diện | #448 |
| Radar hỏi giờ sinh trước khi điền form, không đợi lỗi 409 | Sửa lỗi | #450 |

Các bộ Daily vẫn ở trạng thái chờ duyệt câu nên người dùng chưa thấy, dù đã lên production.

## 2. Phát hiện của Codex theo mức

| Mức | Số | Ở đâu |
|---|---|---|
| P0 | 0 | — |
| P1 | 7 | #450 (chế độ mời bị mất khi qua bước giờ sinh, đã sửa, APPROVE vòng 2); #449 (chọn cảm xúc offline bị lựa chọn cũ ghi đè, đã sửa, chờ owner duyệt nhãn mới); #463 (thiếu kê khai dữ liệu G8 khi Jyotish lưu bản diễn giải mới, đã sửa, APPROVE vòng 2); #456 (biên nhận có thể bị dùng lại, đã sửa, APPROVE vòng 2); #477 ×2 (gia hạn TLS staging: báo xong khi chưa khởi động lại hết; worker chưa nạp CA mới, đã sửa, chờ check); #480 (nhánh thử lại lô câu chữ đặt tên theo ngày cũ, chờ sửa) |
| P2 | khoảng 18 | đếm theo dòng P2 trong comment; 13 trên PR đã APPROVE (không chặn, đã thành issue fix-forward #461, #466, #468, #469, #471, #476, #485) |

12/13 PR merge vào integration được APPROVE ở vòng đầu; #450 và #463 ở vòng 2.

## 3. Thời gian mất và nguyên nhân

| Mất | Bao lâu | Nguyên nhân | Bằng chứng |
|---|---|---|---|
| 7 PR xếp hàng sau một file chung | từ chiều tới hết ngày | Luật "chờ PR cùng file" coi mọi PR sửa `package.json` là đụng nhau. #478 chờ #477; #456, #457, #481, #482, #484, #486 chờ #478; #465 chờ #484. #456 đã APPROVE lúc 21:14 nhưng chưa merge được | `collab-turn --report` 23:40 |
| PR bị đồng bộ lại | 52 lượt "đã đồng bộ, check lại ở tick sau" (hôm qua 22) | S25 chưa làm: mỗi lần integration nhận merge, mọi PR chờ đều bị merge integration vào rồi chờ CI lại | log tick |
| Preflight trượt vì luật mới áp cho PR cũ | 5 PR, tới 18:50 mới hết | #451 (10:34) thêm dòng bắt buộc "Người dùng thấy gì:". #428, #431, #354, #432, #455 mở từ trước nên trượt; autopilot sửa body từng PR qua nhiều lượt | log 12:05, 12:49, 16:26; `queue.md` 13:50, 18:50 |
| Lô duyệt câu chữ của Codex lỗi | 10:44 → 20:08 | Lệnh commit trên máy vận hành thiếu tên tác giả git. #462 sửa và merge 20:08. #480 thêm thử lại và báo owner, đang REQUEST_CHANGES | log 03:44Z; `state.copyBatch.status = error` |
| Preflight trượt vì PR quá 400 dòng | #456 | 438 dòng; đã ghi `Size-exception` lúc 20:50 | log 19:58 |
| Lỡ một lượt autopilot | lượt 16:37 | Tác vụ hẹn giờ không chạy xong, watchdog mở #470 | issue #470 |

## 4. PR từ 3 vòng review trở lên

Không có. Cao nhất là 2 vòng (#450, #456, #463).

## 5. Tốt và chưa tốt

**Tốt**
- Phát hành production hai bước (R1 0038a, R2 0042) theo lệnh owner. Mọi việc đã merge tới R2 đã lên bản chạy thật; khoảng cách integration → `main` từ 797 xuống 20 commit. Biên nhận #473.
- Lượt dùng thử sau phát hành chạy ngay trong ngày và đã thành danh sách sửa #479 (1 P1, 10 P2, 3 P3).
- 0 P0, 0 lỗi chạy Codex. Mọi P1 của PR đã merge được sửa trong 1–2 giờ.
- Hàng chờ trống chỉ 1 phút.

**Chưa tốt**
- Chỉ 2 việc mới có giá trị cho người dùng; phần lớn sức trong ngày dành cho phát hành và công cụ vòng.
- PR quy trình mở của Claude: 8 ở nhóm ops (#477, #478, #480–#482, #484, #486, #487) và 2 ở nhóm feature (#456, #457), dù luật là WIP 1+1. 10 PR sẵn sàng so với trần 5.
- Luật mới trong preflight làm trượt PR cũ; lại phải sửa tay từng body.
- S25–S28 của hôm qua vẫn nằm trong hàng đợi; số lượt đồng bộ lại tăng gấp đôi.
- Dòng "/ 20" trong file tác vụ retro vẫn còn (ngày thứ 2).

## 6. Học từ GitHub và các nguồn chính

Ngày kiểm tra: 13.11.2026.

| Vấn đề | Cách làm phổ biến | Nguồn | Áp dụng ở mình |
|---|---|---|---|
| Giữ PR chỉ vì cùng sửa một file | Kiểm thử merge thật mà không đụng thư mục làm việc: `git merge-tree --write-tree A B` trả 0 khi merge sạch, 1 khi xung đột | [git-scm — git-merge-tree](https://git-scm.com/docs/git-merge-tree) | S29: thay luật "cùng file" bằng kiểm `merge-tree` giữa PR và integration sau merge trước; chỉ giữ khi có xung đột thật. `package.json` thêm dòng script ở chỗ khác nhau thường merge sạch |
| Đồng bộ lại mọi PR mỗi lần base đổi | Merge queue kiểm PR với base mới nhất ngay trước khi merge | [GitHub Docs — Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) (kiểm 12.11) | Giữ S25: chỉ đồng bộ PR đứng đầu hàng |
| Luật mới làm trượt PR cũ | Template chỉ điền sẵn khi tạo PR; công cụ dòng lệnh phải tự dựng body từ template | [GitHub Docs — Creating a pull request template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository) (kiểm 09.11) | Mở rộng S27: khi preflight thêm dòng bắt buộc, cùng PR đó phải có bước tự thêm dòng còn thiếu (giá trị mặc định "chưa ghi") vào body các PR đang mở, thay vì để autopilot sửa tay |

## 7. Chống AI bị "rotten" — cập nhật 13.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6, 08.11 mục 6, 09.11–12.11 mục 7. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Luật WIP có trên giấy nhưng không ai chặn | WIP 1+1 duyệt 12.11, cuối ngày 13.11 có 10 PR quy trình của Claude đang mở |
| Hàng đợi giải pháp chỉ dài thêm | S25–S28 vào hàng đợi 12.11, không cái nào làm; hôm nay thêm S29 |

**Điều học thêm:** luật giới hạn số việc cần một chỗ chặn bằng máy lúc mở PR, không chỉ lúc báo cáo. Giải pháp xếp hàng cần hạn ngày, giống sổ lời hứa ở #481.

**Biện pháp:** S30 (lệnh mở PR quy trình từ chối khi đã đủ WIP); S25–S29 ghi hạn ngày trong `queue.md`.

## 8. Cần owner

Không hỏi lại mục đã chốt (integration → `main` đã làm hôm nay). Mục còn mở:

1. **Sửa file tác vụ retro**: thay dòng "Báo %: … / 20" bằng "báo số việc thật theo Autopilot v2". Khuyến nghị: đồng ý.
2. **#479 câu chữ quyền riêng tư** (lời mời đăng nhập khi Google chưa bật, xác nhận "Đã xóa", đoạn thời hạn lưu): cần owner duyệt câu. Khuyến nghị: duyệt khi đọc lượt câu tiếp theo.
3. **#449** chờ owner duyệt nhãn mới cho phản hồi cảm xúc. **#404, #388, #411** chờ duyệt câu. **#134, #354** chờ owner.
4. **Việc owner của Autopilot v2** (từ 12.11): để Mac thức khi cắm điện; bật "Include your own updates"; chọn 5 người thử.

## 9. Giải pháp, xếp theo tác động

PR quy trình mở của Claude đã vượt WIP (mục 5), nên mọi việc AUTO quy trình hôm nay vào hàng đợi autopilot, không mở PR mới.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S29 | Thay "chờ PR cùng file" bằng kiểm xung đột thật `git merge-tree --write-tree` | git-merge-tree | cả 5 "không" | AUTO | Hàng đợi, ưu tiên 1 (gỡ 7 PR đang chờ) |
| S25 | Chỉ đồng bộ PR đứng đầu hàng của nhóm | GitHub merge queue | cả 5 "không" | AUTO | Hàng đợi |
| S27+ | Mở PR luôn dựng body từ template; luật preflight mới tự bổ sung dòng thiếu vào PR đang mở | GitHub PR template | cả 5 "không" | AUTO | Hàng đợi |
| S30 | Lệnh mở PR quy trình từ chối khi đã đủ WIP 1+1 | quyết định 12.11 | cả 5 "không" | AUTO | Hàng đợi |
| S26, S28 | Như retro 12.11 | — | — | AUTO | Hàng đợi |

## 10. Bước bị chặn

Không có tới lúc viết file này.
