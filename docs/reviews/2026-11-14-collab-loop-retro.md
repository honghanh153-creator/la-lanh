# Nhìn lại vòng tự động Claude ⇄ Codex: 14.11.2026

Tác giả: Claude (lượt retro tự động 14.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Nguồn số liệu: `~/.cache/la-lanh-collab/logs/tick-2026-11-14.log`, `state/2026-11-14.json`, `collab-turn --report` và `collab-metrics` (14.11 23:45), `gh pr list --state merged`, 14 comment `Review verdict` của Codex trên 12 PR được review hôm nay, `queue.md` của autopilot, comment trên issue plan #133, issue #511. Mọi ngày trước đều đã có file retro (#488 của 13.11 merge hôm nay).

Báo theo Autopilot v2 (owner duyệt 12.11): số việc thật, không chia cho 20.

## 1. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| PR merge vào integration | 9 | #478 (10:50) tới #513 (23:18) |
| PR merge vào `main` | 0 | `git log origin/main` không có commit mới trong ngày |
| Việc thật mới merge (người dùng thấy được) | **0** | cả 9 PR là công cụ vòng hoặc tài liệu |
| Việc đã lên bản chạy thật | không đổi so với 13.11 | integration cách `main` 81 commit (hôm qua 20) |
| Bộ Daily phục vụ được | **0/168** | câu đã duyệt 0/1524 (`collab-metrics`) |
| Lượt Codex của vòng | 39, lỗi 0 | trong đó 14 lượt review PR. Trần 32 tới 22:37, sau đó 60 (#514, lệnh owner) |
| Lượt tick | 76 ran, 0 lỗi | ngoài 52 lượt "closed" ban đêm và 6 lượt chờ plan |
| Hàng chờ trống | 84 phút | 16:34–16:44 và 17:38–18:39 |
| PR mở của agent đang làm | **17, trần là 1** | `collab-turn --report` |

PR đã merge: #478 (dùng thử sau phát hành), #480 (lô duyệt câu lỗi thì thử lại), #481 (sổ lời hứa), #482 (hook trước push), #484 (script qua symlink), #486 (soát đêm), #488 (retro 13.11), #514 (giờ chạy 08:00–23:59), #513 (kế hoạch 7 tuần).

Plan trong `state` chọn 3 PR (#477, #480, #488): 2 đã merge, #477 dừng chờ owner sau 2 vòng.

## 2. Phát hiện của Codex theo mức

| Mức | Số | Ở đâu |
|---|---|---|
| P0 | 0 | — |
| P1 | 5 | #477 (gia hạn TLS: cài chứng chỉ dở dang không được khôi phục, vòng 2 nên dừng chờ owner); #482 (đường dẫn hook có `~` bị hiểu sai, đã sửa, APPROVE vòng 2); #486 (soát đêm nhận biên bản review mà không đọc kết quả, đã sửa, APPROVE vòng 2); #493 ×2 (ghi L22 xong khi test chưa chứng minh; đếm M3 thiếu nguồn, chưa sửa) |
| P2 | 17 | #478 ×4, #480, #481 ×2, #482 ×2, #486 ×2, #487, #488, #493 ×2, #513, #514 |
| P3 | 1 | #488 |

7/9 PR đã merge được APPROVE ở vòng đầu; #482 và #486 ở vòng 2.

Codex bắt hai lỗi trong chính retro 13.11 (#488): retro ghi sự cố lô duyệt câu "hết lúc 20:08" theo giờ merge bản sửa, không theo một lô chạy thành công; và số PR APPROVE vòng đầu cộng lại không khớp.

## 3. Thời gian mất và nguyên nhân

| Mất | Bao lâu | Nguyên nhân | Bằng chứng |
|---|---|---|---|
| Hết lượt Codex | 19:09 → 22:53 (3 giờ 44 phút không có review nào) | Trần 32 lượt hết khi mới dùng 11 lượt cho review PR. Phần còn lại đi vào lô duyệt câu và các lượt chấm khác; `state` không ghi tách theo mục đích nên không biết chính xác. Vòng chạy lại khi #514 nâng trần lên 60 | log tick 19:20–22:34 không làm gì; comment báo kẹt #133 lúc 21:49 |
| 14 PR xếp hàng sau #487 | cả buổi tối, chưa gỡ | Luật "chờ PR cùng file": 12 PR chờ trực tiếp #487, 2 PR chờ tiếp sau đó. #487 trượt preflight 17:27, qua check 19:09, bị REQUEST_CHANGES 22:53, sửa xong 22:54, cuối ngày còn chờ CI | `collab-turn --report` 23:45 |
| Lô duyệt câu 14.11 (#491) đỏ | 13:19 → hết ngày | Một câu được duyệt chứa cụm bị cấm nên author check trượt. Autopilot biết cách sửa nhưng dừng vì bản clone làm việc còn 3 file sửa dở của #477 từ 13.11 21:50 | `queue.md` 10:50, 13:55, 22:50; comment #133 lúc 15:49 |
| PR trượt preflight vì body thiếu dòng | #481 khoảng 50 phút, #487 khoảng 80 phút, #513 khoảng 50 phút | Thiếu câu trả lời G7 trong body. Mỗi lần phải chờ lượt autopilot kế tiếp sửa tay. Ngày thứ 3 gặp loại lỗi này (S27 chưa làm) | log 11:00, 17:27, 22:03 |
| Lỡ một lượt autopilot | lượt 17:37 | Tác vụ hẹn giờ không chạy xong; watchdog mở #511. Ngày thứ 2 liên tiếp (hôm qua #470) | issue #511 |
| Owner bị báo lặp | #354 ít nhất 4 lần, #505 2 lần | Khóa chống trùng của "Cần bạn xem" gắn theo commit đầu nhánh. Mỗi lần nhánh được đồng bộ là thành khóa mới | comment #133 lúc 14:23, 14:56, 17:28, 22:44 |
| PR bị đồng bộ lại | 8 lượt (hôm qua 52) | Giảm vì ít merge hơn và nhiều PR đang bị giữ, không phải vì đã sửa (#495 còn chờ) | log tick |

## 4. PR từ 3 vòng review trở lên

Không có. Cao nhất là 2 vòng (#477, #482, #486).

## 5. Tốt và chưa tốt

**Tốt**
- 0 P0, 0 lượt Codex lỗi, 0 tick lỗi.
- Sổ lời hứa (#481) đã chạy: 6/24 mục xong có PR đã merge, không mục nào quá hạn.
- Lệnh owner đổi giờ chạy và trần Codex (#514) từ mở tới merge mất 24 phút.
- Báo kẹt tới owner đúng lúc: #491 lúc 15:49, hết lượt Codex lúc 21:49.

**Chưa tốt**
- Không có việc nào người dùng thấy được. Chưa câu Daily nào tới người dùng: 0/1524 câu được duyệt, lô hôm nay đỏ cả ngày.
- 17 PR quy trình đang mở, trần là 1. Hôm qua là 10. S30 (máy từ chối mở thêm) chưa làm.
- Một bản clone bẩn chặn hai việc (#491, #477) suốt 26 giờ.
- Hết lượt Codex giữa buổi tối mà không có phần dành riêng cho review PR.
- Dòng "/ 20" trong file tác vụ retro vẫn còn (ngày thứ 3).

## 6. Học từ GitHub và các nguồn chính

Ngày kiểm tra: 14.11.2026.

| Vấn đề | Cách làm phổ biến | Nguồn | Áp dụng ở mình |
|---|---|---|---|
| Thư mục làm việc bẩn chặn việc gấp | Không đụng vào thư mục đang dở; tạo một worktree tạm cho việc gấp, xong thì xóa | [git-scm — git-worktree, mục Examples](https://git-scm.com/docs/git-worktree) | S31: autopilot gặp clone bẩn thì làm trong worktree tạm, không dừng và không hỏi owner |
| Việc phụ dùng hết hạn mức của việc chính | Chia nhóm theo mục đích, mỗi nhóm có giới hạn riêng; việc mới của một nhóm không đẩy nhóm khác ra | [GitHub Docs — Control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) | S33: `state` đếm lượt Codex theo mục đích; việc không phải review PR dừng sớm để chừa lượt cho review. Không dùng nguyên GitHub Actions concurrency vì Codex chạy trên máy owner, chỉ mượn ý chia nhóm |
| Báo lặp cho cùng một việc | Thông báo gom theo cuộc trao đổi; người nhận giảm ồn bằng cách bỏ theo dõi từng cuộc | [GitHub Docs — About notifications](https://docs.github.com/en/account-and-profile/managing-subscriptions-and-notifications-on-github/setting-up-notifications/about-notifications) | S34: khóa "Cần bạn xem" theo số PR, mỗi PR báo một lần cho tới khi trạng thái đổi |
| Giữ PR chỉ vì cùng sửa một file | `git merge-tree --write-tree` kiểm xung đột thật | [git-scm — git-merge-tree](https://git-scm.com/docs/git-merge-tree) (kiểm 13.11) | S29 giữ nguyên ý. Theo góp ý của Codex ngày 14.11, không đổi luật giữ PR trước buổi xem lại thử nghiệm 20.11; trước đó chỉ đo |

Merge queue của GitHub: đã kiểm 12.11, không có cho repo của tài khoản cá nhân; không kiểm lại hôm nay.

## 7. Chống AI bị "rotten" — cập nhật 14.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6, 08.11 mục 6, 09.11–13.11 mục 7. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Báo "đã hết sự cố" theo giờ merge bản sửa, không theo kết quả chạy thật | Codex P2 trên #488. Hôm nay lô duyệt câu có chạy nhưng PR của nó đỏ, số câu được duyệt vẫn là 0 |
| Luật WIP ngày càng xa thực tế | 10 PR (13.11) → 17 PR (14.11), trần 1 |
| Trạng thái dở nằm lại trong chỗ làm chung | 3 file sửa dở trong clone từ 13.11 21:50 chặn mọi lượt autopilot sau đó |

**Điều học thêm:** "xong" trong báo cáo phải là kết quả quan sát được (lô chạy ra câu được duyệt), không phải "bản sửa đã merge". Chỗ làm chung phải sạch khi một lượt kết thúc; việc dở thì commit vào nhánh của nó.

**Biện pháp:** S31 (worktree tạm khi clone bẩn); retro từ nay ghi sự cố là "còn mở" cho tới khi có một lần chạy thành công sau bản sửa. Theo đó sự cố lô duyệt câu từ 13.11 **còn mở**.

## 8. Cần owner

Không hỏi lại mục đã chốt. Mục còn mở:

1. **Ba file sửa dở của #477 trong clone làm việc**: giữ hay bỏ. Khuyến nghị: giữ, Claude hoàn thiện rồi commit vào #477. Đã lưu bản sao phần sửa dở ở máy owner (`~/.cache/la-lanh-collab/backups/`), nên chọn cách nào cũng không mất.
2. **Sửa file tác vụ retro**: thay dòng "Báo %: … / 20" bằng "báo số việc thật theo Autopilot v2". Khuyến nghị: đồng ý.
3. **PR chờ owner duyệt câu hoặc quyết định**: #505 (thông báo khi người dùng gõ chữ tự hại), #503, #449, #404, #388, #411, #134, #354, #477. Nhóm lỗi nội dung (L05) chưa có trả lời.
4. **Việc owner của Autopilot v2** (từ 12.11): để Mac thức khi cắm điện; bật "Include your own updates"; chọn 5 người thử.

## 9. Giải pháp, xếp theo tác động

PR quy trình mở của Claude là 17, vượt WIP, nên mọi việc AUTO hôm nay vào hàng đợi autopilot có hạn ngày, không mở PR mới. Việc đổi cách vòng chạy (S33, S34, S29) cần Codex góp ý trước khi làm, theo luật thử nghiệm 14–19.11. Khi WIP cho phép, các mục này được ghi vào sổ lời hứa `scripts/collab-lessons.json`.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S31 | Sửa #491 trong worktree tạm (đưa câu có cụm cấm về chờ duyệt); autopilot gặp clone bẩn thì dùng worktree tạm | git-worktree | cả 5 "không" | AUTO | Hàng đợi, ưu tiên 1, hạn 15.11. Đã làm ngay: lưu bản sao phần sửa dở |
| S32 | Lô duyệt câu lọc cụm cấm trước khi ghi "Codex duyệt", để PR của lô không đỏ vì lý do này | bài học #491 | cả 5 "không" | AUTO | Hàng đợi, hạn 17.11 |
| S33 | Đếm lượt Codex theo mục đích; chừa lượt cho review PR | chia nhóm giới hạn | cả 5 "không" | AUTO | Hàng đợi, hạn 17.11 cho phần đếm; phần chừa lượt sau 20.11 |
| S34 | "Cần bạn xem" báo một lần cho mỗi PR | GitHub notifications | cả 5 "không" | AUTO | Hàng đợi, hạn 17.11 |
| S27+ | Dòng bắt buộc trong body PR được điền sẵn hoặc tự bổ sung | GitHub PR template | cả 5 "không" | AUTO | Hàng đợi từ 12.11, hạn 16.11 |
| S30 | Lệnh mở PR quy trình từ chối khi đã đủ WIP | quyết định 12.11 | cả 5 "không" | AUTO | Hàng đợi từ 13.11, hạn 16.11 |
| S25 | Chỉ đồng bộ PR đứng đầu hàng | GitHub merge queue | cả 5 "không" | AUTO | Đã có PR #495, chờ #487 |
| S29 | Kiểm xung đột thật thay luật "cùng file" | git-merge-tree | cả 5 "không" | AUTO | Dời sau 20.11 theo góp ý Codex 14.11 (hạn cũ 15.11) |

## 10. Bước bị chặn

Không có tới lúc viết file này.
