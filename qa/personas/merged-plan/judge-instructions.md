# Giám khảo mù: kế hoạch gộp, hai mốc

Phiên bản `merged-plan-judge-v1-2026-11-14`. Giám khảo chỉ đọc file này, `mocks.md` và gói người giả của mình.

Mỗi người giả là một người hư cấu: hoàn cảnh, mức tin chiêm tinh, dữ liệu đã nhập vào app, **tình huống hôm nay** (rất mệt / vừa quay lại sau hai tuần / điện thoại dùng chung / không có ai an toàn để tâm sự) và **mood hôm nay**.

Với mỗi người giả, đọc mock và đặt mình vào vị trí người đó, trong tình huống và mood hôm nay. Tự quyết người đó sẽ bấm gì (lối nào, góc đọc nào, có bỏ qua không), đúng với tính cách và thói quen điện thoại của họ. Chấm ba mục riêng:

- `moment` = `"A"`: trải nghiệm ở **Mốc A** (cuối tuần 4).
- `moment` = `"B"`: trải nghiệm ở **Mốc B** (cuối tuần 6, gồm mọi thứ của mốc A cộng chuyện minh họa và chuyện vui). Chấm toàn bộ trải nghiệm, không chỉ phần mới.
- `moment` = `"ask"`: chỉ phần **Biến thể hỏi lại việc đã giữ**, giả sử hôm qua người này đã giữ một việc.

Chấm từ góc nhìn người giả, không chấm độ hay của câu chữ. Không đoán phần hồ sơ không có. Người không tin chiêm tinh chấm như người không tin.

## Mục A và B: trả lời

- Bốn điểm 1–5:
  - `understood` "Lá có hiểu mình không?" 1 = sai người hoặc sai lúc; 2 = chung chung, ai đọc cũng được; 3 = có một phần chạm tới mình; 4 = hợp với một áp lực thật của mình; 5 = "đúng là mình hôm nay".
  - `less_alone` "Đọc xong mình có bớt thấy một mình không?" 1 = thấy một mình hơn; 3 = không đổi; 5 = rõ ràng bớt.
  - `peaceful` "Đọc xong mình có thấy bình yên hơn không?" 1 = bứt rứt hơn; 3 = không đổi; 5 = rõ ràng yên hơn.
  - `want_return` "Mình có muốn mở lại app ngày mai không?" 1 = muốn bỏ; 3 = không đổi gì; 5 = chắc chắn mở lại.
- Năm cờ true/false, mỗi cờ true phải kèm **nguyên văn** cụm chữ trong mock gây ra cảm giác đó (`quotes`, khóa trùng tên cờ):
  - `blame`: thấy bị trách.
  - `pressure`: thấy bị ép làm gì.
  - `privacy`: lo lộ chuyện riêng, kể cả với người dùng chung máy.
  - `dependence`: thấy bị kéo phụ thuộc vào app.
  - `must_check_la`: thấy như phải xem Lá rồi mới dám quyết chuyện của mình.
- `path_chosen`: một câu ngắn, người này đã bấm gì.
- `complaint`: một câu ngắn tiếng Việt thường, điều người này chê nhất (không có thì "").
- `checks` (true/false, từ góc nhìn người này):

| Khóa | Câu hỏi | Mốc |
|---|---|---|
| `found_mood_and_angle` | Tìm và hiểu được chỗ chọn mood và "Đổi góc đọc". | A, B |
| `fits_after_change` | Sau khi chọn mood, đổi góc đọc hoặc bấm "Không giống mình", việc nhỏ mới hợp với mình hôm nay. | A, B |
| `contradiction_fixed` | Không còn câu nào nói ngược mood mình vừa chọn. | A, B |
| `reason_vs_interpretation_clear` | Phân biệt được đâu là lý do chọn note, đâu là phần diễn giải. | A, B |
| `found_right_path` | Trong ba lối (và "Chơi một chút" ở mốc B), tìm được đúng đường cho điều mình muốn hôm nay. | A, B |
| `could_stop` | Thấy rõ mình dừng hoặc đóng được bất cứ lúc nào. | A, B |
| `felt_blamed_for_absence` | Thấy bị trách vì vắng (chỉ trả lời nếu hôm nay là ngày quay lại sau hai tuần, còn lại để false). | A, B |
| `leftover_after_absence` | Thấy còn việc cũ tồn lại sau khi vắng (như trên). | A, B |
| `profile_notice_clear` | Hiểu câu thông báo hồ sơ: lưu ở đâu, khi nào mất. | A, B |
| `story_understood_as_illustration` | Hiểu chuyện ngắn là chuyện minh họa, không phải lời kể của người thật. | B |
| `story_denied_difficulty` | Thấy chuyện ngắn coi nhẹ nỗi khó của mình. | B |
| `story_false_promise` | Thấy chuyện ngắn hứa suông kiểu "rồi sẽ ổn". | B |
| `game_understood` | Hiểu cách chơi chuyện vui ngay. | B |
| `game_could_stop` | Thấy dừng chơi được bất cứ lúc nào. | B |
| `game_hurt` | Có chỗ trong chuyện vui chạm vào nỗi đau của mình. | B |

## Mục ask: trả lời

- `help` 1–5 "Thẻ này có giúp mình không?", `want_return` 1–5 như trên.
- `felt_checked`: thấy như bị kiểm tra bài hoặc bị theo dõi.
- `pressure`, `privacy`, `dependence` true/false, kèm `quotes` nguyên văn như trên.
- `would_answer`: sẽ bấm "Có ích", "Chưa thử", "Không hợp", "Bỏ qua" hay không bấm (ghi đúng một trong năm: `useful`, `not_yet`, `not_fit`, `skip`, `none`).
- `complaint`: một câu ngắn.

## Đầu ra

Một mảng JSON, đủ 3 phần tử cho mỗi người giả trong gói, đúng tên khóa:

```json
[
 {"persona": "P001", "moment": "A", "understood": 3, "less_alone": 3, "peaceful": 3, "want_return": 3,
  "blame": false, "pressure": false, "privacy": false, "dependence": false, "must_check_la": false,
  "quotes": {}, "path_chosen": "…", "complaint": "…",
  "checks": {"found_mood_and_angle": true, "fits_after_change": true, "contradiction_fixed": true,
   "reason_vs_interpretation_clear": true, "found_right_path": true, "could_stop": true,
   "felt_blamed_for_absence": false, "leftover_after_absence": false, "profile_notice_clear": true}},
 {"persona": "P001", "moment": "B", "…": "như A, thêm 6 khóa của mốc B trong checks"},
 {"persona": "P001", "moment": "ask", "help": 3, "want_return": 3, "felt_checked": false,
  "pressure": false, "privacy": false, "dependence": false, "quotes": {}, "would_answer": "skip", "complaint": ""}
]
```
