# Nhìn lại vòng tự động Claude ⇄ Codex: 11.11.2026

Tác giả: Claude (lượt retro tự động 11.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Nguồn số liệu: `~/.cache/la-lanh-collab/logs/tick-2026-11-11.log`, `state/2026-11-11.json`, `collab-turn --report` (11.11 23:40), `gh pr list --state merged`, comment `Review verdict` của Codex trên 20 PR được động tới hôm nay, log check cục bộ của #410 và #428, `queue.md` của autopilot. Các ngày 04–07.11 không có file retro riêng đã được gộp trong retro 08.11.

## 1. Kết quả trong ngày

Hôm nay là ngày đầu đếm theo "việc" (luật owner duyệt 10.11).

| Chỉ số | Số | Ghi chú |
|---|---|---|
| PR merge vào integration | 13 | #413 (12:01) tới #424 (23:00) |
| Việc thật đã merge | **9 / 20** | xem bảng dưới |
| Việc đã lên bản chạy thật | **0** việc của máy | `main` chỉ nhận hotfix #427 do owner tự làm và merge (21:34). Integration chưa lên `main` (cách 740 commit) |
| PR không tính | 4 | #409 (retro), #419 và #421 (chỉ test), #424 (cùng việc với #406) |
| Lượt Codex review | 19, lỗi 0 | `state/2026-11-11.json` |
| PR sẵn sàng cuối ngày | 5 / 5 | `collab-turn --report` |
| Hàng chờ trống | 318 phút (~5,3 giờ) | hôm qua 410 phút |

| Việc | PR |
|---|---|
| Daily `changed-plan` viết lại thành bộ câu khớp nhau | #406, #424 (tính 1) |
| Daily ghép tiêu đề, cảnh, hành động thành một bộ mỗi ngày | #407 |
| Xóa lịch sử xóa luôn ghi chú Daily lưu trên máy | #410 |
| Trang mời Radar công khai không còn hiện nhãn riêng | #413 |
| Daily `comparison-loop` thành bộ | #416 |
| Daily `decision-fatigue` thành bộ | #417 |
| Daily `defend-old-choice` thành bộ | #418 |
| Daily `missing-context` thành bộ | #422 |
| Daily `too-many-open-loops` thành bộ | #423 |

## 2. Phát hiện của Codex theo mức

| Mức | Số | Ở đâu |
|---|---|---|
| P0 | 0 | — |
| P1 | 3 | #410: 2 (xóa lịch sử nhưng dữ liệu ban đầu của màn hình vẫn được dựng lại từ bản lưu); #412: 1 (bản app cũ đọc tâm trạng đã mã hóa thành lỗi khi hai bản chạy song song) |
| P2 trên PR bị chặn | 6 | #411 (1 rồi 2), #410 (1), #423 (1), #424 (1) |
| P2 trên PR đã APPROVE | 6 | #407 (2), #413 (2), #409 (1), #419 (1); không chặn |

13/13 PR merge đều được APPROVE; 9 ở vòng đầu, 4 ở vòng 2 (#406, #407 từ hôm qua; #410, #423, #424).

## 3. Thời gian mất và nguyên nhân

| Mất | Bao lâu | Nguyên nhân | Bằng chứng |
|---|---|---|---|
| Không có việc cho máy | 318 phút | Sáng 08:57–10:07 chỉ có plan, chưa có PR; tối 20:15–23:20 nhiều quãng, hàng chỉ còn PR chờ owner, PR đang sửa hoặc PR chờ PR khác cùng file | log `collab-tick: []` 31 lượt; `collab-turn --report` |
| Check phải chờ nhau | 40 lượt tick check + 3 lượt review bỏ qua | Check chạy từng cái; tick gặp máy bận thì bỏ lượt (S13 vẫn trong hàng đợi) | log `"check":{"status":"busy"…}` |
| #410 trượt author check 3 lần | khoảng 4 giờ | 2 lần không do code PR: Playwright không mở được web server trong 60 giây vì máy quá tải; một test tốc độ đo 0,256 giây với ngưỡng 0,25 giây. Lần 3 là lỗi lint thật | `queue.md` 12:55, 13:50, 16:50; log `check-410-*` |
| Lỗi merge giả lặp lại | 1 lượt tick | 21:05 GitHub trả "Merge already in progress" cho #423 rồi merge xong 21:05:59. Lần thứ hai (10.11 ở #380). S18 chưa làm | log 14:05:52Z |
| Comment check nói "bước lỗi: không xác định" | 2 lần ở #428 | Log ghi rõ `Clarity ratchet failed` (câu Jyotish mới vi phạm cổng rõ nghĩa) nhưng comment không nêu, nên người sửa phải mở log trên máy owner | `check-428-07dec6065a6b.log` dòng 243 |
| PR port thiếu cổng | #431 preflight FAIL | PR port hotfix của owner (#430) mở thiếu cổng G1–G10 và mức S/M/L | log 16:27Z |

## 4. PR từ 3 vòng review trở lên

Không có. #411 đã 2 vòng REQUEST_CHANGES (vòng 2: tên miền có dấu vẫn lọt luật chặn link) và đang chờ owner. #410 chỉ 2 vòng review nhưng 3 lần trượt check, 2 lần do máy, xem mục 3.

## 5. Tốt và chưa tốt

**Tốt**
- 9 việc thật, có 2 việc bảo vệ dữ liệu người dùng (#410, #413).
- 0 lỗi chạy Codex, 0 P0. P1 của #410 được sửa trong ngày.
- Không còn hai phiên làm trùng một việc như #406 hôm qua.
- PR nội dung theo bộ xung đột cùng file (#423, #424) được dựng lại file sạch, diff chỉ +216 dòng.

**Chưa tốt**
- 0 việc của máy lên bản chạy thật.
- 9/20, thiếu 11 việc. Hàng chờ trống 5,3 giờ là nguyên nhân lớn nhất: 4 PR nội dung theo bộ đều sửa chung `copy_registry.json` nên phải chờ nhau (#429 chờ #426).
- Lỗi đã biết từ hôm qua (S13, S18) lặp lại vì việc quy trình bị giữ sau #354 đã ba ngày (luật WIP 1).
- #412 (mã hóa tâm trạng) có P1 chưa ai nhận sửa.

## 6. Học từ GitHub và các nguồn chính

Ngày kiểm tra: 11.11.2026.

| Vấn đề | Cách làm phổ biến | Nguồn | Áp dụng ở mình |
|---|---|---|---|
| Comment check không nêu bước lỗi | Mỗi bước ghi tóm tắt Markdown vào job summary, gộp lên trang chạy, để người xem biết ngay bước nào hỏng mà không cần mở log | [GitHub Blog — Supercharging GitHub Actions with Job Summaries (09.05.2022)](https://github.blog/news-insights/product-news/supercharging-github-actions-with-job-summaries/) | S19: author check tìm dòng lỗi cuối (`... failed`, `FAILED`, `✖`) trong log và dán 5 dòng quanh đó vào comment |
| Test tốc độ trượt khi máy bận | Google có bài riêng về cách giảm test chập chờn trong CI. Cách làm phổ biến: test nên kiểm điều kiện, không kiểm thời gian đồng hồ, hoặc đo bằng thời gian CPU với ngưỡng rộng (nguồn chỉ nêu chung; phần "đồng hồ" là cách làm phổ biến, chưa có trích dẫn chính thức) | [Google Testing Blog — Flaky Tests at Google and How We Mitigate Them (27.05.2016)](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html) | Đã sửa trong #410 (đo `process_time`, ngưỡng 1,0 giây). S20: rà các test còn đo thời gian đồng hồ |
| Lỗi "Merge already in progress" | API merge trả lỗi khi một merge khác đang chờ, tức merge đang chạy | [GitHub REST — Merge a pull request](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request) (đã kiểm 10.11) | S18 giữ nguyên |
| Check bận thì bỏ lượt | `concurrency` cho lần chạy mới chờ ở trạng thái pending | [GitHub Docs — concurrency](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs) (đã kiểm 09.11) | S13 giữ nguyên |

## 7. Chống AI bị "rotten" — cập nhật 11.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6, 08.11 mục 6, 09.11 mục 7, 10.11 mục 7. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Công cụ biết nhiều hơn điều nó nói | Log #428 có dòng `Clarity ratchet failed` nhưng comment ghi "không xác định"; phiên sửa sau đó phải tự đoán |
| Luật giữ chính việc sửa luật | WIP 1 bị #354 (chờ owner) giữ từ 09.11, nên S13, S17, S18 nằm hàng đợi ba ngày và S18 đã lặp lại |

**Điều học thêm:** thông tin cho phiên sau phải nằm sẵn trong chỗ chung (comment PR), không nằm trong log riêng; hàng đợi việc quy trình cần hạn tối đa, nếu không ghi chú sẽ cũ đi trong khi lỗi vẫn lặp.

**Biện pháp:** S19 (comment nêu bước lỗi); đề nghị owner cho PR đang chờ owner không chiếm chỗ WIP 1 (mục 8).

## 8. Cần owner

Không hỏi lại mục đã chốt. Mục còn mở:

1. **Đưa integration lên `main` và go-live** (740 commit). Khuyến nghị: duyệt khi owner sẵn sàng; đây là cách duy nhất để 9 việc hôm nay tới tay người dùng.
2. **WIP 1 cho PR quy trình:** PR đang chờ owner (#354, #134) không tính vào WIP 1. Khuyến nghị: đồng ý, để S13/S17/S18/S19 chạy được ngay.
3. **#404, #388, #411** gắn `needs-owner` vì có câu mới hoặc luật copy. Khuyến nghị: duyệt cùng lượt duyệt copy cuối.
4. **#354**: chuyển phần chặn cứng sang deny rules, hook chỉ cảnh báo (như 09.11).
5. **#430** (hotfix của owner, base `main`): chỉ owner merge được.

## 9. Giải pháp, xếp theo tác động

PR quy trình mở của Claude là #354 và #134 (chờ owner), nên theo WIP 1 các việc AUTO quy trình được ghi vào hàng đợi autopilot.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S21 | Hàng chờ thiếu PR: ưu tiên việc không đụng `copy_registry.json` (sửa lỗi, P1 #412, quyền riêng tư) để không phải chờ nhau cùng file | retro 09.11 S15 | cả 5 "không" | AUTO | Hàng đợi autopilot (không phải PR quy trình) |
| S19 | Comment author check nêu bước lỗi và vài dòng log quanh đó | GitHub Blog — Job Summaries | cả 5 "không" | AUTO | Hàng đợi (sau WIP 1) |
| S18 | Tick coi "Merge already in progress" là đang merge | GitHub REST merge | cả 5 "không" | AUTO | Hàng đợi (từ 10.11) |
| S13 | Check bận thì xếp hàng, không bỏ lượt | GitHub Actions concurrency | cả 5 "không" | AUTO | Hàng đợi (từ 09.11) |
| S20 | Rà test còn đo thời gian đồng hồ, đổi sang thời gian CPU hoặc kiểm điều kiện | Google Testing Blog | cả 5 "không" | AUTO | Hàng đợi |
| S22 | PR port hotfix dùng template PR có sẵn cổng G1–G10 và mức S/M/L | preflight #431 | cả 5 "không" | AUTO | Hàng đợi autopilot (sửa body #431) |
| S17, S2b | Như retro 10.11 | — | — | AUTO | Hàng đợi |

## 10. Bước bị chặn

Không có tới lúc viết file này.
