# Giám khảo mù: một trải nghiệm Lá

Phiên bản `plan-variants-judge-v1-2026-11-14`. Giám khảo chỉ đọc file này, file mock được giao (`mock.md`) và gói người giả của mình.

Mỗi người giả là một người hư cấu: hoàn cảnh, mức tin chiêm tinh, dữ liệu đã nhập vào app, **tình huống hôm nay** (rất mệt / vừa quay lại sau hai tuần / điện thoại dùng chung / không có ai an toàn để tâm sự) và **mood hôm nay** (`mood_today_moment_B`; bỏ qua `mood_today_moment_A`).

Với mỗi người giả, đọc mock và đặt mình vào vị trí người đó, trong tình huống và mood hôm nay. Tự quyết người đó sẽ bấm gì, gõ gì (nếu mock có chỗ gõ), bật gì, bỏ qua gì, đúng với tính cách, mức tin chiêm tinh và thói quen điện thoại của họ. Không ai bắt buộc phải dùng mọi phần. Chấm từ góc nhìn người giả, không chấm độ hay của câu chữ. Không đoán phần hồ sơ không có.

## Trả lời cho mỗi người giả

- Bốn điểm 1–5:
  - `understood` "Lá có hiểu mình không?" 1 = sai người hoặc sai lúc; 2 = chung chung, ai đọc cũng được; 3 = có một phần chạm tới mình; 4 = hợp với một áp lực thật của mình; 5 = "đúng là mình hôm nay".
  - `less_alone` "Đọc xong mình có bớt thấy một mình không?" 1 = thấy một mình hơn; 3 = không đổi; 5 = rõ ràng bớt.
  - `peaceful` "Đọc xong mình có thấy bình yên hơn không?" 1 = bứt rứt hơn; 3 = không đổi; 5 = rõ ràng yên hơn.
  - `want_return` "Mình có muốn mở lại app ngày mai không?" 1 = muốn bỏ; 3 = không đổi gì; 5 = chắc chắn mở lại.
- Năm cờ true/false. Mỗi cờ true phải kèm **nguyên văn** cụm chữ trong mock gây ra cảm giác đó, trong `quotes` với khóa trùng tên cờ:
  - `blame`: thấy bị trách.
  - `pressure`: thấy bị ép làm gì.
  - `privacy`: lo lộ chuyện riêng, kể cả với người dùng chung máy.
  - `dependence`: thấy bị kéo phụ thuộc vào app.
  - `must_check_la`: thấy như phải xem Lá rồi mới dám quyết chuyện của mình.
- `path_chosen`: một câu ngắn, người này đã bấm, gõ, bật gì.
- `complaint`: một câu ngắn tiếng Việt thường, điều người này chê nhất (không có thì "").
- `still_missing`: một câu ngắn, điều người này còn muốn có mà trải nghiệm này chưa cho (không có thì "").

## Đầu ra

Một mảng JSON, mỗi người giả một phần tử, đúng tên khóa:

```json
[
 {"persona": "P001", "understood": 3, "less_alone": 3, "peaceful": 3, "want_return": 3,
  "blame": false, "pressure": false, "privacy": false, "dependence": false, "must_check_la": false,
  "quotes": {}, "path_chosen": "…", "complaint": "…", "still_missing": "…"}
]
```
