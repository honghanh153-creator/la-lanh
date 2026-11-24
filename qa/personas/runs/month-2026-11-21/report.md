# Hỏi về tháng này: 1000 người giả, câu hỏi làm sẵn (21.11.2026)

**Đây là mô phỏng trên máy**, không phải người dùng thật: 1000 người giả (`qa/personas/personas-1000.json`), app chạy trên máy với SQLite riêng mỗi tiến trình, không gọi dịch vụ ngoài. Riêng lượt này, câu chữ `month.*` được coi là đã duyệt trong bộ nhớ để chạy được mọi đường. Owner chọn AS1 ngày 21.11: không có ô gõ câu hỏi. Lệnh: `uv run --directory apps/api python -m scripts.persona_month_check --out ../../qa/personas/runs/month-2026-11-21`. Số liệu: `summary.json`.

| Kiểm | Kết quả |
|---|---|
| Câu trả lời theo mảng (6 mảng × 1000 người, hỏi 2 lần) | 6000/6000 giống nhau cả hai lần, đủ 3 phần, có "Dựa vào", không ngày |
| Câu hỏi làm sẵn (18 câu × 1000 người) | 18000/18000 trả lời đúng câu hỏi, có "Với câu này", phần tháng giống câu trả lời theo mảng, không câu nào mở đầu kiểu có/không, không ngày |
| Chữ tự do (câu hỏi Tarot và câu khủng hoảng của người giả gửi kèm) | 1100/1100 bị từ chối ở bước kiểm tra dữ liệu, không câu nào bị lặp lại |
| Khoảng ngày dễ hơn | từ hôm nay, tối đa 3 ngày, ở mọi người |
| Lưu | mỗi người lưu một câu theo mảng và một câu làm sẵn; danh sách đúng hai câu đó, câu làm sẵn giữ câu hỏi |
| Lẫn dữ liệu giữa người | 0: người sau không thấy, không xóa được câu đã lưu của người trước; không câu trả lời nào chứa chữ của người khác |

## Câu làm sẵn có đúng điều người giả muốn hỏi không

Đếm thô bằng từ khóa trên 4023 câu hỏi Tarot của người giả (chỉ để báo cáo, không phải kiểm đạt/trượt): 1034 câu (26%) khớp tình huống của ít nhất một câu làm sẵn. Số người giả có ít nhất một câu khớp:

| Câu làm sẵn | Người |
|---|---|
| Thức khuya hoài, làm sao ngủ sớm hơn? | 160 |
| Tăng ca, đổi ca liên tục, giữ sức thế nào? | 123 |
| Mấy hôm nay nặng lòng, làm gì cho nhẹ? | 101 |
| Cuối tháng hết tiền, xoay sao cho đỡ? | 83 |
| Nhiều môn thi dồn, chia ôn thế nào? | 79 |
| Đồ án chưa có ý, bắt đầu từ đâu? | 75 |
| Việc dồn nhiều quá, nên làm việc nào trước? | 69 |
| Bố mẹ hỏi chuyện điểm, việc làm, trả lời sao? | 56 |
| Nhớ nhà quá, làm gì cho đỡ? | 55 |
| Nói với bố mẹ về con đường mình chọn thế nào? | 54 |
| Mùa thi mệt quá, giữ sức thế nào? | 53 |
| Làm sao nói chuyện khó với sếp? | 50 |
| Nhắc người khác trả tiền sao cho khỏi mất lòng? | 35 |
| Người thương ở xa, ít nhắn, mình nên nói gì? | 35 |
| Bố mẹ hay so mình với người khác, nói sao? | 26 |
| Bạn rủ đi ăn mà mình đang kẹt tiền, từ chối sao? | 23 |
| Làm sao để hai người gần nhau hơn? | 21 |
| Nói với người thương là mình mệt sao cho khỏi cãi? | 12 |

Từ khóa thô nên số thật có thể cao hơn (nhiều câu hỏi nói cùng chuyện bằng chữ khác). Ba câu ít người nhất đều ở mảng Tình cảm, mảng người giả ít hỏi nhất; nếu cần thay câu, đó là chỗ nên xem trước.
