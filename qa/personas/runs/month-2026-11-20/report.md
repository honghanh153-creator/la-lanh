# Hỏi về tháng này: 1000 người giả (20.11.2026)

**Đây là mô phỏng trên máy**, không phải người dùng thật: 1000 người giả (`qa/personas/personas-1000.json`), app chạy trên máy với SQLite riêng mỗi tiến trình, không gọi dịch vụ ngoài. Riêng lượt này, câu chữ `month.*` và hai câu nháp của owner được coi là đã duyệt trong bộ nhớ, và cờ câu gõ được bật, để chạy được mọi đường. Lệnh: `uv run --directory apps/api python -m scripts.persona_month_check --out ../../qa/personas/runs/month-2026-11-20`. Số liệu: `summary.json`.

| Kiểm | Kết quả |
|---|---|
| Câu khủng hoảng được chuyển sang thông báo an toàn | 135/135 (không lọt câu nào) |
| Báo nhầm khủng hoảng | 0/205 câu nói quá ("chết cười"…) và 0/4023 câu hỏi thường |
| Câu trả lời theo mảng (6 mảng × 1000 người, hỏi 2 lần) | 6000/6000 giống nhau cả hai lần, đủ 3 phần, có "Dựa vào", không ngày |
| Khoảng ngày dễ hơn | từ hôm nay, tối đa 3 ngày, ở mọi người |
| Câu gõ (4023 câu hỏi Tarot của người giả) | 3234 trả lời, 789 nhờ chọn mảng, 1682 có câu mở đầu "Lá không …" (câu hỏi kết quả, thời điểm, "có nên", ý người khác); không câu nào bị lặp lại trong câu trả lời |
| Lẫn dữ liệu giữa người | 0: người sau không thấy, không xóa được câu đã lưu của người trước; không câu trả lời nào chứa câu hỏi của người khác |
| Lưu | mỗi người lưu một câu, danh sách chỉ có đúng câu đó |

Lượt đầu bắt được 71 câu trả lời có một phần mở đầu bằng "Có …" (2 câu mẫu trong mảng Tình cảm). Đã viết lại hai câu và thêm test chặn (#795). Lượt trên là lượt sau khi sửa.
