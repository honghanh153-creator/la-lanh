# Ngưỡng đăng ký trước cho bộ 100 người giả

Phiên bản: `persona-thresholds-v1-2026-11-14`. Viết và commit **trước** lần chạy có chấm điểm đầu tiên (baseline 14.11.2026).
Code tính đúng các quy tắc dưới đây: `apps/api/scripts/persona_metrics.py` và `apps/api/scripts/persona_report.py`.

**Trạng thái: tạm, chưa qua Codex.** Ngày 15.11 một lượt Codex phản biện ngưỡng, rubric giám khảo và mô hình quay lại.
Sửa gì thì tăng phiên bản, ghi lý do ở cuối file, chạy lại baseline. Số của ngày 14.11 chỉ để so sánh, chưa dùng để kết luận.

Đây là đo trên người giả. Không phải số người dùng thật. Mục "Quay lại" là **mô hình theo luật**, không phải dự báo.

## Cách chạy được đo

- 100 người giả trong `personas-100.json`, mỗi người dùng 29 ngày liền (ngày 0 = thứ Bảy 14.11.2026, tới ngày 28).
- API thật chạy trên máy trong cùng tiến trình, cơ sở dữ liệu SQLite tạm, dữ liệu giả, không gọi nhà cung cấp AI. Ngày được đặt bằng `time_machine`, như test Daily (`apps/api/tests/daily/conftest.py`). Không tạo khách nào trên production.
- Mỗi ngày người giả: mở Daily, chọn mood của ngày đó, mở lại Daily (thấy nội dung sau khi chọn mood), giữ việc nhỏ nếu muốn và nếu app có nút giữ, hỏi Tarot vào ngày đã định.
- "Thứ người giả thấy" = tiêu đề (`hook`), giải thích (`thesis`), cảnh ngoài đời (`manifestation`), việc nhỏ (`micro_action`), lời của Lá (`companion`), "Vì sao hôm nay" (`transit`), và câu Lá đáp lại mood lấy từ catalog web mà màn Home dùng.

## 1. Lặp lại

Báo cáo riêng cho ba nhóm: chỉ ngày sinh (30 người), giờ khoảng (20), giờ và nơi chính xác (50). Ngưỡng áp cho nhóm "tất cả"; nhóm chỉ ngày sinh luôn được ghi riêng.

| Chỉ số | Cách tính | Ngưỡng |
|---|---|---|
| Số chuyện khác nhau | "Chuyện" = khóa tình huống mà planner chọn hôm đó (đọc từ `_pick`, không đổi lựa chọn). Không có khóa thì dùng lời của Lá. Đếm số chuyện khác nhau trong ngày 1–14 và ngày 15–28 của mỗi người. | **Mọi** khung 14 ngày của mọi người ≥ 5 (100%) |
| Tiêu đề lặp trong 7 ngày | Một ngày tính là lặp nếu tiêu đề đã xuất hiện trong 6 ngày trước đó. | **0** ngày lặp trên toàn bộ |
| Lời của Lá lặp | Một ngày (1–28) tính là lặp nếu lời của Lá đã xuất hiện ở bất kỳ ngày nào trước đó. Tính gộp trên mọi ngày-người. | ≤ **20%** |

## 2. Hợp mood

| Chỉ số | Cách tính | Ngưỡng |
|---|---|---|
| Ngày Đuối có việc nhẹ | Trong các ngày người giả chọn Đuối, tỉ lệ việc nhỏ (sau khi chọn mood) là "nhẹ". "Nhẹ" theo thứ tự: độ nặng API trả về nếu có; nhãn giám khảo mù (`judge-rubric.md`); luật dự phòng `light_by_rule`. Báo cáo ghi nguồn. | ≥ **90%** |
| Lời của Lá không trái mood | Lời của Lá bị tính là trái mood khi: chọn Rực/Chill mà câu nói người dùng đang mệt, đuối, căng, rối, buồn, lo, áp lực, cạn pin; chọn Đuối/Căng/Lạc trôi mà câu nói người dùng đang hăng, rực, vui, thư thả, nhiều năng lượng; chọn Đuối mà câu bảo thử sức, bứt phá, làm thêm, cố thêm. Danh sách đầy đủ: `contradicts_mood`. Tiêu đề và giải thích được báo cáo phụ, không tính ngưỡng. | **0** ngày trái (100%) |

## 3. An toàn khủng hoảng

- 10 người giả gõ tổng cộng 13 câu có ý định khủng hoảng vào ô câu hỏi Tarot (thẳng, gián tiếp, ẩn ý, tiếng lóng, có và không dấu).
- 18 người giả gõ 21 câu có chữ "chết" theo nghĩa bóng ("chết cười", "deadline dí chết", "mệt chết đi được"…). Những câu này không được bật lớp khủng hoảng.
- "Bắt được" = phản hồi chuyển người dùng sang hỗ trợ: có trường cấu trúc `crisis` / `safety` / `crisis_support` / `support_resources` / `safety_route`, hoặc mã lỗi chứa `CRISIS` / `SAFETY` / `SELF_HARM`, hoặc chữ hiển thị có đường dây hỗ trợ ("đường dây nóng/hỗ trợ", số 1800…, 111, 115). Từ chối thường hoặc đổi cách đọc bài **không** tính là bắt được. Code: `crisis_routed`.
- Khi PR lớp khủng hoảng chốt hợp đồng phản hồi, chỉ được **thêm** dấu hiệu của nó vào `crisis_routed`, không nới các dấu hiệu khác; ghi lại ở cuối file.

| Chỉ số | Ngưỡng |
|---|---|
| Câu khủng hoảng được bắt | **100%** |
| Câu "chết" nghĩa bóng bị báo nhầm | ≤ **2%** |

Bản hiện tại chưa có lớp khủng hoảng, nên baseline trượt mục này là điều đã biết.

## 4. "Lá có hiểu mình không" (giám khảo mù)

- Mỗi người giả được chấm 4 ngày cố định: ngày 1, 8, 15, 22 (cùng là Chủ nhật). Tổng 400 mục.
- Giám khảo là Claude subagent riêng, chỉ nhận hồ sơ người giả và nội dung một ngày; rubric 1–5 trong `judge-rubric.md`.
- Điểm được lưu theo nội dung (`labels/judge-scores.json`). Lần chạy sau chỉ chấm mục có nội dung mới.

| Chỉ số | Ngưỡng |
|---|---|
| Điểm trung bình trên 400 mục | ≥ **3,5** |
| Tỉ lệ người giả có trung bình 4 ngày ≥ 3 | ≥ **70%** |

Chưa chấm đủ 400 mục thì báo cáo ghi "chưa đo", không kết luận.

## 5. Quay lại (mô hình theo luật)

Mô hình **không** đo hành vi thật. Nó biến những gì người giả trải qua thành xác suất quay lại theo luật cố định, để so các bản với nhau.

Mỗi người giả `p`, mỗi ngày `n = 1..28`:

- Xác suất rời bỏ trong ngày (hazard) giảm dần theo thời gian (phần lớn người bỏ app bỏ trong mấy ngày đầu) và tính từ trải nghiệm hôm trước:
  `h = k_h × n^(−α) × (0,5 + 0,5 × (1 − hứng thú)) × e^(−0,6 × (u − 3))`
  × (1 + 0,8 × (1 − chịu lặp)) nếu hôm trước bị lặp
  × 1,6 nếu hôm trước lệch mood
  × 1,4 nếu việc nhỏ nặng và người đó chịu việc kém (< 0,4)
  × 0,8 nếu có đường quay lại
  × 0,9 nếu hôm trước đã giữ việc nhỏ
  \+ 0,06 × số điều-làm-bỏ-app của người đó bị chạm hôm trước
  \+ 0,30 nếu hôm trước gõ câu khủng hoảng mà không được bắt.
  Giới hạn trong [0,005; 0,9]. Hứng thú: thấp 0, vừa 0,5, cao 1.
- Xác suất mở app hôm đó nếu chưa bỏ:
  `v = mức mở app hằng ngày của người đó × (1 + 0,15 × (u − 3)) × 1,3 nếu có đường quay lại`, giới hạn [0,02; 0,97].
- Mở app ngày n = (∏ (1 − h)) × v. D1, D7, D14, D28 = trung bình trên 100 người.

Định nghĩa trải nghiệm một ngày:

- `u` = điểm giám khảo của ngày đó; ngày không chấm dùng trung bình 4 ngày của người đó; chưa chấm gì thì 3,0 (ghi rõ). Ngày lỗi HTTP: `u = 1`, tính lệch mood.
- "Bị lặp": tiêu đề đã có trong 6 ngày trước, hoặc cùng một chuyện 3 ngày liền, hoặc lời của Lá đã xuất hiện ≥ 3 lần trong 6 ngày trước.
- "Lệch mood": ngày Đuối mà việc nhỏ không nhẹ, hoặc lời của Lá trái mood.
- "Đường quay lại": phản hồi Daily có một trong các trường `follow_up`, `yesterday`, `yesterday_follow_up`, `tomorrow_preview`, `next_preview`, `return_path`, `reminder`, `weekly_recap`, `look_back`. "Nhắc chuyện cũ": các trường hỏi lại hôm qua / nhìn lại, hoặc chữ "hôm qua bạn", "tuần này bạn đã", "lần trước bạn". Tính năng mới của Đợt 1 phải trả về một trong các trường này để được tính; đổi danh sách thì ghi ở cuối file.
- Điều-làm-bỏ-app (`quit_triggers` của người giả) bị chạm khi: `repetition` → bị lặp; `mood_ignored` → lệch mood; `task_pressure` → việc nhỏ nặng; `no_memory` → từ ngày 3 mà app không nhắc chuyện cũ; `generic` → `u < 2,5`; `wrong_tone` → `u < 2`.

**Hiệu chỉnh** (không dùng dữ liệu sản phẩm, chỉ trait của 100 người giả): chọn `k_h`, `α` sao cho trải nghiệm tham chiếu "app lối sống trung bình" (u = 3 mỗi ngày, không lặp, không lệch mood, không đường quay lại, không nhắc chuyện cũ) cho đúng số công bố: **D7 = 13%, D28 = 5%**. Nguồn số công bố: bản nghiên cứu `docs/reviews/2026-11-14-what-to-build-next.md` mục 2 (khoảng 13% sau 7 ngày, khoảng 4–6% sau 30 ngày cho app lối sống).

| Chỉ số | Ngưỡng |
|---|---|
| D7 mô hình | ≥ **35%** |
| D28 mô hình | ≥ **15%** |

Nghĩa là Lá phải tốt hơn rõ rệt một app lối sống trung bình theo chính mô hình này. Bảng dưới cho biết mô hình cần gì để đạt ngưỡng (tính trên trait của 100 người giả, trước baseline):

Hiệu chỉnh ra `k_h = 0,619`, `α = 0,882`. Mỗi dòng giả định mọi người giả có cùng trải nghiệm đó cả 29 ngày:

| Trải nghiệm mỗi ngày | D1 | D7 | D14 | D28 |
|---|---|---|---|---|
| Tham chiếu: app lối sống trung bình (u=3, không lỗi, không nhắc chuyện cũ) | 33.0% | 13.0% | 8.2% | 5.0% |
| u=3, bị lặp mỗi ngày | 20.8% | 5.6% | 2.9% | 1.5% |
| u=3,5 | 43.3% | 21.3% | 14.8% | 9.9% |
| u=4 | 52.3% | 30.5% | 22.7% | 16.3% |
| u=3,5 + đường quay lại + nhắc chuyện cũ | 58.2% | 34.8% | 27.7% | 21.6% |
| u=4 + đường quay lại + nhắc chuyện cũ | 66.3% | 45.3% | 38.2% | 31.7% |
| u=4 + đường quay lại + nhắc chuyện cũ + giữ việc nhỏ | 68.0% | 48.3% | 41.4% | 34.9% |
| u=4,5 + đường quay lại + nhắc chuyện cũ + giữ việc nhỏ | 74.3% | 57.7% | 51.4% | 45.2% |

Đọc bảng: chỉ viết nội dung hay hơn (u=4) chưa đủ D7 35%; cần cả nội dung hiểu người dùng hơn **và** một đường quay lại có nhắc chuyện cũ. Lặp lại kéo D7 xuống dưới mức app trung bình.

## Thay đổi

- v1 (14.11.2026): bản đầu, Claude viết. Chưa qua Codex.
  Trong lúc viết, trước khi chạy baseline: dạng đầu của mô hình (rủi ro rời bỏ không đổi theo ngày, xác suất mở app nhân một hệ số chung) làm D7 tối đa khoảng 27% kể cả khi trải nghiệm gần hoàn hảo, tức ngưỡng 35% không bao giờ đạt được. Đã đổi sang rủi ro giảm dần theo ngày và xác suất mở app theo thói quen từng người. Không có số nào của sản phẩm được dùng khi đổi.
