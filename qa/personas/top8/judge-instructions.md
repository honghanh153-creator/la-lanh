# Giám khảo mù: 8 ý tưởng

Phiên bản `top8-judge-v1-2026-11-14`. Giám khảo chỉ đọc file này, `mocks.md` và gói người giả của mình.

Mỗi người giả là một người hư cấu, có hoàn cảnh, mức tin chiêm tinh, dữ liệu đã nhập vào app, và **tình huống hôm nay** (rất mệt / vừa quay lại sau hai tuần / điện thoại dùng chung / không có ai an toàn để tâm sự).
Với **mỗi người giả × mỗi ý (1–8)**, đọc mock của ý đó và đặt mình vào vị trí người đó, trong tình huống hôm nay của họ. Chấm độc lập từng cặp. Không chấm theo độ hay của câu chữ.

## Trả lời cho mỗi cặp

- `help` 1–5: "Cái này có giúp mình không?" 1 = vô ích hoặc làm mình khó chịu, 3 = tạm, 5 = đúng thứ mình cần.
- `return` 1–5: "Cái này có làm mình muốn mở lại app không?" 1 = làm mình muốn bỏ, 3 = không đổi gì, 5 = chắc chắn mở lại.
- `blame`, `pressure`, `privacy`, `dependence` (true/false): có chỗ nào làm người này thấy bị trách, bị ép, lo lộ chuyện riêng (kể cả với người dùng chung máy), hoặc thấy bị kéo phụ thuộc vào app không.
- `quote`: nếu có cờ nào true, chép **nguyên văn** cụm chữ trong mock gây ra cảm giác đó; không có thì "".
- `complaint`: một câu ngắn tiếng Việt thường, điều người này chê nhất ở ý này (không có thì "").
- `checks`: trả lời đúng các câu của ý đó (true/false), từ góc nhìn người này:

| Ý | Câu kiểm |
|---|---|
| 1 | `reason_vs_interpretation_clear`: phân biệt được đâu là lý do chọn note, đâu là phần diễn giải. `feels_relevant`: chủ đề có dính tới đời mình. |
| 2 | `fits_after_change`: sau khi đổi mood/góc/"không giống mình", việc nhỏ mới hợp với mình hôm nay. `contradiction_fixed`: câu trái với mood vừa chọn đã được sửa. |
| 3 | `found_right_path`: tìm được đúng đường cho điều mình muốn hôm nay. `could_stop`: thấy rõ mình dừng được bất cứ lúc nào. `felt_blamed_for_absence`: thấy bị trách vì vắng. |
| 4 | `asked_once_no_penalty`: thấy chỉ bị hỏi một lần, không bị phạt. `answer_changes_next`: hiểu câu trả lời sẽ đổi gợi ý lần sau. |
| 5 | `mistook_for_real_testimony`: tưởng đây là lời kể của người thật. `felt_difficulty_denied`: thấy nỗi khó bị coi nhẹ. `felt_false_promise`: thấy bị hứa suông kiểu "rồi sẽ ổn". |
| 6 | `saw_preview`: biết trước người nhận sẽ thấy gì. `worried_private_info_attached`: lo bị kèm mood/ngày sinh/câu hỏi. `recipient_needs_account`: nghĩ người nhận phải tạo tài khoản. `would_send`: sẽ thử gửi. |
| 7 | `could_find_again`: biết tìm lại điều đã đánh dấu. `could_remove`: biết bỏ dấu/xóa. `worried_auto_saved`: lo app tự lưu mood hay câu hỏi Tarot. |
| 8 | `understood_how_to_play`: hiểu cách chơi ngay. `joke_hurt`: có câu đùa chạm nỗi đau của mình. `could_stop`: thấy dừng được bất cứ lúc nào. |

## Đầu ra

Một mảng JSON, mỗi phần tử:

```json
{"persona": "P001", "idea": 1, "help": 3, "return": 2, "blame": false, "pressure": false, "privacy": false, "dependence": false, "quote": "", "complaint": "…", "checks": {"reason_vs_interpretation_clear": true, "feels_relevant": false}}
```

Đủ 8 phần tử cho mỗi người giả trong gói, đúng tên khóa ở bảng trên.
