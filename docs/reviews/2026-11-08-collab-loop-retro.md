# Nhìn lại vòng tự động Claude ⇄ Codex: 04–08.11.2026

Tác giả: Claude (lượt retro tự động 08.11, 23:36). Người review: Codex, qua vòng tự động.
Báo cáo gộp năm ngày: lượt retro 05, 06 và 07.11 bị lỡ (ops-alert #261, #277, #310); 04.11 cũng không có file. Xem K34.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Nguồn số liệu: `~/.cache/la-lanh-collab/logs/tick-2026-11-0{4..8}.log`, `state/2026-11-0{4..8}.json`, `logs/review-*.json`, `collab-turn --report` (08.11 23:40), `gh pr list --state merged`, comment `Review verdict` của Codex trên 103 PR được review từ 03.11, `queue.md` của autopilot, danh sách issue `ops-alert`.

## 1. Kết quả theo ngày

| Ngày | PR merge vào `collab/integration` | Lượt Codex | APPROVE / REQUEST_CHANGES | P0 | P1 chặn | P2 chặn | P2/P3 không chặn |
|---|---|---|---|---|---|---|---|
| 04.11 | 11 | 20 | 11 / 9 | 0 | 13 | 2 | 21 |
| 05.11 | 13 | 25 | 13 / 12 | 0 | 13 | 0 | 8 |
| 06.11 | 18 | 24 | 18 / 6 | 0 | 9 | 0 | 24 |
| 07.11 | 18 | 20 | 18 / 2 | 0 | 3 | 0 | 7 |
| 08.11 (tới 23:36) | 19 | 28 | 19 / 8 | 0 | 5 | 5 | 15 |

Tổng 79 PR merge, 117 lượt Codex, **không có P0** trong năm ngày. Từ 06.11 mỗi ngày đạt cam kết 16–20 PR (#197). Số lượt Codex luôn dưới trần 32.

Nhóm PR đã merge (chi tiết: `gh pr list --state merged --base collab/integration`):

- **Daily v2 và nội dung:** C2b nhà theo độ tin cậy giờ sinh (#213), C2c gộp nghịch hành (#216), C2d biến thể HMAC và chống lặp 30 ngày (#210, #240), 120 ô hành tinh × nhà chờ owner duyệt (#221), cổng hard-zero C1-3 (#214), nhà nói theo bộ ý nghĩa có nguồn (#215), 4 đợt biến thể tiêu đề/cảnh/hành động gắn cờ chờ duyệt (#282–#284, #298–#301, #314–#316, #329, #330), cờ chờ duyệt cho câu mới (#256).
- **Sửa lỗi sản phẩm và privacy:** 422 chung không lặp lại dữ liệu người dùng (#200, #246), lỗi nội dung tách khỏi lỗi kết nối (#209, #342), xóa lịch sử và thu hồi thiết bị ghi nhật ký để khôi phục không làm sống lại (#199, #278), Explore theo mức dữ liệu (#207).
- **Kiểm thử:** tham chiếu độc lập cho góc và cusp (#227, #245, #267), bằng chứng 360/390 px và bàn phím (#249, #270, #272, #273).
- **Vòng tự động:** retro 03.11 S1/S2/S5 (#234, #235, #236), check tự lành (#239), hạn giờ cho mọi lệnh (#242), đệm 5 PR sẵn sàng (#251), trần 400 dòng + rà cả lớp sau 2 lần REQUEST_CHANGES (#252), báo lỡ lượt qua issue và email (#255, #264), khóa an toàn (#279), preflight lỗi giữ PR (#307), top-up tính sau merge (#337), `pr-check` khi đổi base (#338).
- **Prototype Hẹn ở Lá:** #319, #323.
- **Phân loại S/M/L bổ sung cho PR đã merge:** #325–#328, #333, #336, #340, #344.

## 2. Thời gian mất và nguyên nhân

| # | Ngày, giờ | Sự cố | Mất | Nguyên nhân gốc | Trạng thái |
|---|---|---|---|---|---|
| **K32** | 04.11 14:24 → 05.11 10:25 | #214 (cổng hard-zero C1-3) cần **13 vòng review**, vòng nào cũng có P1 | ~20 giờ, 13 lượt Codex (11% lượt của 5 ngày) | Luật nhận diện câu tiếng Việt viết bằng regex (S9 "câu điều kiện", A15 "pha của góc chiếu"). Mỗi vòng Codex đưa một câu phản ví dụ mới; bản sửa chỉ vá đúng câu đó. Không có bộ câu mẫu có nhãn để đo độ chính xác, nên "đúng hết" không có điểm dừng | #252 (06.11) bắt rà cả lớp sau 2 lần REQUEST_CHANGES và trần 400 dòng. Từ 06.11 không PR nào quá 4 vòng |
| **K33** | 08.11 10:00–14:15; 07.11 13:00–15:00 | Tick chạy nhưng không có PR nào cho máy | ~6 giờ (`collab-turn --report`: "Hàng chờ trống hôm nay: 357 phút") | Người cấp việc là autopilot, nhưng autopilot lỡ lượt 09:37 (#312) và treo (#317, #321). Báo "chạy không" (#313, #318, #322) gửi tới đúng tác vụ đang treo, nên không ai xử lý. Đệm 5 PR (#251) cũng do autopilot nạp, nên rỗng cùng lúc | **Chưa sửa** (S9) |
| **K34** | 04–07.11 | Retro hằng ngày không chạy 4 ngày; autopilot, ops-watch cũng lỡ nhiều lượt | 4 báo cáo, 4 lượt "tự giải" | Tác vụ hẹn giờ của Claude dừng chờ quyền hoặc không được mở; launchd không chạy bù được. Watchdog báo đúng (#260, #261, #276, #277, #310, #311) nhưng không có bước tự xử lý | Lặp lại K30. Cần owner (mục 8.2) |
| **K35** | 06.11 → 08.11 | **32 issue `ops-alert` đang mở, 0 issue đã đóng**. Cùng tiêu đề "tác vụ hẹn giờ bị treo 2026-11-08" mở 4 lần (#317, #321, #334, #350) | Khó thấy báo động mới; tốn ngữ cảnh mỗi lượt đọc | Mỗi lần báo tạo issue mới; không gộp theo khóa, không tự đóng khi hết lỗi | **Chưa sửa** (S8) |
| K36 | 08.11 12:24–23:25 | 29 lượt tick báo "máy đang chạy check khác" | Chậm, chưa đo được | Mỗi lượt là một tiến trình khác giữ khóa check. Chưa rõ tiến trình nào (có thể phiên Claude song song chạy check). Khóa vẫn chặn đúng, không có check chồng nhau | Theo dõi bằng `collab:metrics` khi #354 merge |
| K37 | 08.11 18:50–20:51 | Không có lượt tick nào | ~2 giờ | Chưa rõ (giống khoảng trống K31 ngày 03.11; có thể máy ngủ) | Theo dõi |

Khoảng 05.11 01:39–06:28 là ban đêm, không tính. Cổng plan buổi sáng là thiết kế, không tính.

## 3. PR cần từ 3 vòng review trở lên

| PR | Số vòng | Diễn biến | Nguyên nhân gốc |
|---|---|---|---|
| #214 cổng hard-zero C1-3 | 13 | 04.11 14:24 → APPROVE 05.11; mỗi vòng 1–2 P1 về câu điều kiện hoặc pha góc chiếu | K32: luật ngôn ngữ dạng regex không có tập mẫu có nhãn; sửa theo từng phản ví dụ |
| #258 giữ log check lỗi | 4 | 06.11 20:30 → APPROVE 22:05 | Mỗi vòng một chỗ khác trong cùng script; 2 vòng cần owner (needsOwner) |
| #319 Hẹn ở Lá | 4 | 08.11 14:34 → APPROVE 16:12 | Prototype lớn; 2 vòng cần owner |
| #314 tiêu đề đợt 3 | 4 | 08.11 12:30 → APPROVE 22:24 | Câu mới cần duyệt; 2 vòng cần owner |
| #215, #239 | 3 | 04–05.11 | Sửa theo phát hiện được nêu (trước #252) |

Sau #252 (06.11 00:32), PR nhiều vòng nhất là 4 vòng và xong trong vài giờ, so với 13 vòng/20 giờ trước đó.

## 4. Tốt và chưa tốt

**Tốt (có bằng chứng):**
- 79 PR merge trong 5 ngày; 06–08.11 mỗi ngày 18–19 PR.
- Không có P0; P1 chặn giảm từ 13/ngày (04–05.11) xuống 3–5/ngày (07–08.11).
- Ba giải pháp của retro 03.11 (S1, S2, S5) merge 05.11 (#234–#236). S1 chạy đúng: báo "chạy không" ở #289, #304, #308, #313, #318, #322.
- #252 chặn được kiểu kéo dài như #214.
- Từ 06.11 câu mới đều gắn cờ chờ duyệt (#256), không câu nào tự lên app.

**Chưa tốt:**
- Báo động có nhưng không ai xử lý: báo "chạy không" đến tay tác vụ đang treo (K33); 32 issue mở không đóng (K35).
- Retro hằng ngày lỡ 4 ngày liền (K34), dù owner yêu cầu chạy mỗi ngày.
- Việc tồn từ 31.10 vẫn chưa xử lý: 5 PR nháp (#154, #155, #157, #160, #161); S3 của retro 03.11 chưa làm; dòng K24 trong hàng đợi vẫn chưa đánh dấu xong dù #166 đã sửa từ 02.11.

## 5. Học từ GitHub và các nguồn chính

Ngày kiểm tra: 08.11.2026.

| Vấn đề | Cách làm phổ biến | Nguồn | Áp dụng ở mình |
|---|---|---|---|
| Báo động trùng, không tự đóng (K35) | Gộp báo động cùng loại thành một thông báo; tắt báo động phụ khi báo động gốc đang bật | [Prometheus Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) (grouping, inhibition) | S8: một issue mở cho mỗi khóa báo động, lần sau thêm comment |
| | Action tạo issue có tùy chọn cập nhật issue mở cùng tiêu đề thay vì tạo mới | [JasonEtco/create-an-issue](https://github.com/JasonEtco/create-an-issue) (`update_existing`, `search_existing`) | S8: bỏ ngày khỏi tiêu đề, tìm issue mở trước khi tạo |
| | "Every page should be actionable"; báo động chỉ cần phản xạ máy móc thì nên tự động hóa | [Google SRE book — Monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/) | S8 tự đóng khi tác vụ có beat `done` mới; S9 gửi báo "chạy không" tới kênh còn sống |
| Báo động gửi tới chính tác vụ đang hỏng (K33) | Inhibition: khi tác vụ gốc đang lỗi, chỉ báo lỗi gốc | Alertmanager (như trên) | S9: khi autopilot đang lỡ/treo, báo "chạy không" chỉ gộp vào issue của autopilot |
| Luật ngôn ngữ chặn cứng kéo 13 vòng (K32) | Công cụ phân tích phải giữ tỉ lệ "báo sai thực tế" thấp; có nút "NOT USEFUL", luật báo sai nhiều thì hạ xuống chạy ngoài luồng chặn | [Sadowski et al., Lessons from Building Static Analysis Tools at Google, CACM 04/2018](https://cacm.acm.org/magazines/2018/4/226371-lessons-from-building-static-analysis-tools-at-google/pdf); [Tricorder, ICSE 2015](https://www.cs.umd.edu/class/spring2019/cmsc414/papers/tricorder-building-a-program-analysis-ecosystem.pdf) | S10: tập câu mẫu có nhãn cho mỗi luật ngôn ngữ; trường hợp mơ hồ báo "cần người duyệt" thay vì chặn (cần owner, mục 8.3) |
| PR tụt sau base (S3 cũ) | Merge queue | [GitHub Docs — managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | Trang hiện không còn ghi rõ loại repo được dùng; kết luận 03.11 (repo cá nhân không có) chưa kiểm lại được bằng thử. Giữ S3 (API `update-branch`) |

## 6. Chống AI bị "rotten" — cập nhật 08.11

Nguồn và biện pháp gốc ở retro 03.11, mục 6. Hôm nay có thêm:

**Triệu chứng mới:**

| Triệu chứng | Bằng chứng |
|---|---|
| Ghi chú cũ không được dọn | Dòng K24 trong `queue.md` vẫn "[ ]" 6 ngày sau khi #166 sửa; mục "sáng 01.11 gỡ draft" còn nguyên; 5 PR nháp 31.10 vẫn mở |
| Tín hiệu bị chìm trong nhiễu | 32 issue `ops-alert` mở, nhiều cái trùng tiêu đề; agent đọc danh sách issue phải lọc qua chúng mỗi lượt |
| Luật đã có nhưng không có ai thi hành | Retro hằng ngày là lệnh của owner (02.11) nhưng lỡ 4 ngày |

**Điều học thêm:** báo động cũng là ngữ cảnh. Theo SRE book và Alertmanager, báo động phải gộp, tự đóng khi hết lỗi và mỗi cái phải có việc cần làm; nếu không, cả người và agent đều quen bỏ qua.

**Biện pháp thêm:**
1. S8: báo động gộp theo khóa, tự đóng khi khỏi.
2. Mỗi retro đánh dấu xong các dòng hàng đợi đã có PR merge (đã làm hôm nay, mục 7, S12).
3. PR nháp quá 7 ngày được đưa vào danh sách xử lý của retro (đóng nếu đã có PR khác làm thay, hoặc gỡ nháp).

## 7. Giải pháp, xếp theo tác động

Đang có PR quy trình mở của Claude (#354, phạm vi khác: hook chặn lệnh nguy hiểm, `collab:metrics`), nên theo luật WIP 1 các việc AUTO mới được ghi vào hàng đợi autopilot để làm ngay sau khi #354 merge.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S9 | Khi autopilot lỡ lượt/treo, báo "chạy không" gộp vào issue của autopilot (một lỗi gốc) và gửi email ngay lần đầu, không chờ 6 lượt | Alertmanager inhibition; SRE "actionable" | cả 5 "không" | AUTO | Hàng đợi (sau #354) |
| S8 | `ops-alert`: tiêu đề không có ngày, tìm issue mở cùng khóa trước khi tạo, lần sau chỉ thêm comment; beat `done` mới hoặc tick có việc thì tự đóng kèm comment "đã khỏi" | create-an-issue `update_existing`; Alertmanager grouping | cả 5 "không" | AUTO | Hàng đợi (sau #354) |
| S3 | PR đã APPROVE, tụt sau base, không xung đột → `update-branch` với `expected_head_sha` (từ retro 03.11) | REST update-branch | cả 5 "không" | AUTO | Vẫn trong hàng đợi |
| S11 | Xử lý 5 PR nháp từ 31.10: #160 so với #337 (cùng việc top-up) — đóng nếu đã làm thay; các PR còn lại gỡ nháp hoặc đóng có lý do | Dọn định kỳ (retro 03.11, mục 6.3) | cả 5 "không"; mở lại được | AUTO | Hàng đợi |
| S12 | Dọn `queue.md`: đánh dấu xong K24 (#166) và S1/S2/S5; ghi rõ mục còn mở | Dọn ghi chú có cấu trúc | local, không đổi luật | AUTO | **Đã làm** |
| S10 | Luật ngôn ngữ (S9, A15 của cổng clarity) có tập câu mẫu có nhãn; câu mơ hồ → "cần người duyệt" thay vì chặn cứng | Google static analysis; Tricorder | Đổi cách cổng hard-zero chặn | NEEDS OWNER | Mục 8.3 |

## 8. Cần owner

1. **32 issue `ops-alert` đang mở.** Khuyến nghị: sau khi S8 merge, cho Claude đóng một lần các issue đã khỏi (có comment), giữ mở cái còn lỗi.
2. **Tác vụ hẹn giờ vẫn lỡ/treo** (retro 04–07.11, autopilot 07–08.11, ops-watch). Lặp lại mục 2 của retro 03.11. Khuyến nghị: để app Claude mở trong giờ chạy và cho phép sẵn các lệnh chỉ đọc mà tác vụ dùng.
3. **S10: cổng hard-zero với câu mơ hồ.** Khuyến nghị: đồng ý cho câu mơ hồ chuyển sang "cần người duyệt" (owner vẫn duyệt mọi câu cuối cùng), giữ chặn cứng cho mẫu rõ ràng.

Merge queue: không đổi khuyến nghị (chưa chuyển repo sang organization).

## 9. Bước bị chặn

Không có tới lúc viết file này.
