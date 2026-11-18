# 8 ý tưởng qua 100 người giả (14.11.2026)

**Đây là đánh giá của mô hình AI trên mô tả bằng chữ.** Không phải người dùng thật, không phải app thật.

- Mỗi ý được mô tả 3-6 màn bằng chữ: [top8/mocks.md](top8/mocks.md).
- 100 người giả hư cấu. Mỗi người có một tình huống hôm nay cố định, 25 người mỗi loại: rất mệt, vừa quay lại sau hai tuần, điện thoại dùng chung, không có ai an toàn. Mức tin chiêm tinh lấy theo hồ sơ.
- Giám khảo: 7 Claude subagent riêng chấm 800 cặp (100 người x 8 ý). Codex chấm độc lập 160 cặp (20 người chọn đều theo nhóm x 8 ý).
- Câu hỏi chấm: [top8/judge-instructions.md](top8/judge-instructions.md). Ngưỡng: bảng TOP 8 trong `docs/reviews/2026-11-14-ket-qua-tranh-luan.md`.

## Đọc nhanh

- **Được chấm cao nhất là ý 3 (chọn nghỉ / gỡ / chơi, quay lại không phải giải thích) và ý 2 (mood đổi việc nhỏ ngay).** Đây là hai ý duy nhất có điểm "giúp mình" trên 3,5 ở giám khảo Claude.
- **Ý 3 trượt ngưỡng ở Claude nhưng đạt ở Codex.** Claude: 23/100 người không tìm được đúng đường, vì họ muốn kể chuyện hoặc vào Tarot, mà "Gỡ một chuyện" chỉ dẫn tới note có sẵn. Codex: 19/20 tìm được. Không ai thấy bị trách vì vắng lâu.
- **Ý 2 là chỗ hai giám khảo lệch nhau nhiều nhất.** Claude: 96/100 thấy việc nhỏ mới hợp. Codex: chỉ 11/20; nhiều người muốn được nghe một câu hiểu tâm trạng hơn là nhận việc mới. Người lớn tuổi và người ít quen điện thoại thấy nhiều nút và chữ "Chill", "Lạc trôi" khó hiểu.
- **Ý 1 và ý 5 hợp sinh viên, không hợp người khác.** Năm nhất xa nhà và nhóm áp lực học chấm khoảng 2,9–3,6. Người đi làm và nhóm khác chấm dưới 2: "chuyện học nhóm sinh viên chẳng dính gì tới mình".
- **Ý 4 (hỏi lại việc đã giữ):** không ai thấy bị phạt, nhưng 11/100 người (Codex: 10/20) thấy câu "Thử được chưa?" giống sếp kiểm tra bài.
- **Ý 7:** cả 25 người dùng chung điện thoại lo người khác thấy danh sách "Điều từng giúp mình". Ý này trượt vì 2 người ít quen điện thoại không biết cách bỏ dấu.
- **Ý 8:** 4 người thấy chuyện "bạn trong nhóm không làm bài" chạm vào chuyện thật của mình: nhớ nhóm cũ, đang thức khuya làm bài thật, nhân vật trùng tên người hay bị trêu.
- **Ý 6:** ít người muốn gửi (giúp 2,65). Người mệt hoặc không có ai để gửi thấy vô ích. Ý này trượt chỉ vì 1 người lớn tuổi không chắc người nhận có phải cài app không.
- Người không tin chiêm tinh chấm thấp hơn ở hầu hết các ý. Người chỉ nhập ngày sinh chấm gần như mọi người, vì các ý này không dựa vào lá số.

## Gợi ý chỉnh trước khi làm (suy ra từ lời chê, chưa thử lại)

1. Ý 3: thêm lối "kể ra" và lối vào Tarot ngay ở màn chọn, nói rõ "Gỡ một chuyện" dẫn tới đâu.
2. Ý 2: sau khi đổi mood, hiện một câu cho thấy Lá hiểu tâm trạng, không chỉ đổi việc nhỏ. Bớt nút cho người ít quen điện thoại.
3. Ý 7: có cách ẩn hoặc khóa danh sách khi máy dùng chung.
4. Ý 4: đổi "Thử được chưa?" sang câu không giống kiểm tra.
5. Ý 8: tránh chuyện về người không làm phần việc của mình.
6. Ý 1 và ý 5: thêm bản cho người đi làm và người lớn tuổi.

## Bảng tổng

| Ý | Ngưỡng phần người giả | Giúp mình (1-5) | Muốn quay lại (1-5) | Có cờ trách / ép / lo riêng tư / phụ thuộc | Codex: giúp / quay lại |
| --- | --- | --- | --- | --- | --- |
| 1. Note sát chuyện sinh viên, xoay chủ đề, nói thật vì sao có note này | ĐẠT (phần 42 ngày chưa thử) | 2.48 | 2.62 | 10/100 | 2.15 / 2.2 |
| 2. Mood, góc đọc, nút 'không giống mình' đổi việc nhỏ ngay | ĐẠT | 3.64 | 3.39 | 2/100 | 3.55 / 3.2 |
| 3. Mở app chọn nghỉ / gỡ / chơi; quay lại sau thời gian vắng không phải giải thích | TRƯỢT | 3.74 | 3.57 | 0/100 | 4.4 / 4.25 |
| 4. Hỏi lại việc đã giữ, một lần, bỏ qua được | ĐẠT | 3.0 | 3.06 | 14/100 | 2.4 / 2.3 |
| 5. Chuyện ngắn minh họa về cảm giác lạc lõng | ĐẠT | 2.52 | 2.58 | 0/100 | 3.15 / 2.95 |
| 6. Gửi một lá cho người quen, kèm mẫu câu mở lời | TRƯỢT | 2.65 | 2.82 | 0/100 | 2.55 / 2.7 |
| 7. 'Điều từng giúp mình': tự đánh dấu, tự bỏ dấu | TRƯỢT | 3.02 | 3.04 | 25/100 | 3.2 / 3.0 |
| 8. Trò chơi chọn kết thúc chuyện vui đời sinh viên | TRƯỢT | 2.64 | 2.75 | 1/100 | 2.5 / 2.5 |

## Ý 1. Note sát chuyện sinh viên, xoay chủ đề, nói thật vì sao có note này

Kết luận theo ngưỡng phần người giả: **ĐẠT (phần 42 ngày chưa thử)**.

- `reason_vs_interpretation_clear` = true: 97/100 (cần ≥ 90%) → đạt
- Chưa thử được bằng mock: Phần mô phỏng 42 ngày (4 nhóm tình huống mỗi 7 ngày, 5 tình huống mỗi 14 ngày, không lặp tiêu đề 7 ngày, không lặp nguyên note 14 ngày) cần code; baseline hiện tại trượt (trung vị 1 tình huống mỗi 14 ngày).

| Nhóm | Người | Giúp | Quay lại |
| --- | --- | --- | --- |
| Người đi làm trẻ | 19 | 1.95 | 2.11 |
| Nhóm khác | 19 | 1.89 | 2.26 |
| Năm cuối / việc đầu tiên | 14 | 2.43 | 2.43 |
| Năm nhất xa nhà | 15 | 3.0 | 3.07 |
| Vừa học vừa làm | 14 | 2.93 | 3.07 |
| Áp lực học | 19 | 2.89 | 2.95 |
| Không có ai an toàn (tình huống) | 25 | 2.68 | 2.8 |
| (tin chiêm tinh) | 27 | 2.52 | 2.67 |
| (nửa tin) | 45 | 2.58 | 2.73 |
| (không tin) | 28 | 2.29 | 2.39 |
| (chỉ nhập ngày sinh) | 30 | 2.5 | 2.77 |

Cờ: bị trách 2, bị ép 8, lo riêng tư 0, phụ thuộc 0.
Câu trong mock bị chỉ ra nhiều nhất: 'Nhắn một câu cho nhóm' (6); 'Bạn chưa dám nhắn nhóm là phần của mình bị trễ.' (2); 'Nhắn một câu cho nhóm: 'Phần mình trễ tới tối nay, mình gửi trước 9 giờ.'' (1)

Lời chê ở các cặp điểm thấp nhất:

- Chuyện học nhóm sinh viên chẳng dính gì tới mình, lại còn giao việc.
- Mình đi làm ca rồi, note toàn chuyện sinh viên.
- Mệt rã người mà note lại nói chuyện học nhóm sinh viên.

Codex so với Claude trên cùng 20 người giả: giúp 2.15 so với 2.65, quay lại 2.2 so với 2.7. Lệch trung bình: giúp 0.5, quay lại 0.6.
- Người giả lệch điểm giúp từ 2 trở lên: P037.
- Câu kiểm trả lời ngược nhau: P017/feels_relevant, P022/feels_relevant, P037/feels_relevant, P038/feels_relevant, P080/feels_relevant.
- Một lời chê của Codex: Nhóm mình có người không làm, chứ không phải mình đang nộp trễ.

## Ý 2. Mood, góc đọc, nút 'không giống mình' đổi việc nhỏ ngay

Kết luận theo ngưỡng phần người giả: **ĐẠT**.

- `fits_after_change` = true: 96/100 (cần ≥ 85%) → đạt
- `contradiction_fixed` = true: 100/100 (cần ≥ 100%) → đạt
- Mỗi nhóm ≥ 80% thấy hợp: đạt
- Chưa thử được bằng mock: Mock chỉ có một ca mâu thuẫn (câu 'đang hăng' khi chọn Đuối); mọi ca phải thử bằng code.

| Nhóm | Người | Giúp | Quay lại |
| --- | --- | --- | --- |
| Người đi làm trẻ | 19 | 3.84 | 3.58 |
| Nhóm khác | 19 | 2.89 | 2.79 |
| Năm cuối / việc đầu tiên | 14 | 3.57 | 3.29 |
| Năm nhất xa nhà | 15 | 3.73 | 3.33 |
| Vừa học vừa làm | 14 | 3.93 | 3.57 |
| Áp lực học | 19 | 3.95 | 3.79 |
| Không có ai an toàn (tình huống) | 25 | 3.44 | 3.24 |
| (tin chiêm tinh) | 27 | 3.52 | 3.37 |
| (nửa tin) | 45 | 3.87 | 3.6 |
| (không tin) | 28 | 3.39 | 3.07 |
| (chỉ nhập ngày sinh) | 30 | 3.73 | 3.4 |

Cờ: bị trách 0, bị ép 0, lo riêng tư 2, phụ thuộc 0.
Câu trong mock bị chỉ ra nhiều nhất: 'Lá đổi việc nhẹ hơn vì bạn chọn Đuối.' (2)

Lời chê ở các cặp điểm thấp nhất:

- Bấm qua bấm lại mất thời gian, mình chỉ muốn đọc 30 giây.
- Chữ Chill tiếng Anh với nhiều nút bấm, tôi sợ bấm nhầm.
- Mấy chữ Chill, Lạc trôi đọc không hiểu, bấm nhiều nút quá.

Codex so với Claude trên cùng 20 người giả: giúp 3.55 so với 3.5, quay lại 3.2 so với 3.25. Lệch trung bình: giúp 0.35, quay lại 0.75.
- Người giả lệch điểm giúp từ 2 trở lên: không có.
- Câu kiểm trả lời ngược nhau: P015/fits_after_change, P017/fits_after_change, P022/fits_after_change, P024/fits_after_change, P027/fits_after_change, P033/fits_after_change, P050/fits_after_change, P095/fits_after_change.
- Một lời chê của Codex: Mình vẫn muốn được nghe một câu hiểu tâm trạng hơn là nhận việc để làm.

## Ý 3. Mở app chọn nghỉ / gỡ / chơi; quay lại sau thời gian vắng không phải giải thích

Kết luận theo ngưỡng phần người giả: **TRƯỢT**.

- `found_right_path` = true: 77/100 (cần ≥ 90%) → trượt
- `could_stop` = true: 100/100 (cần ≥ 100%) → đạt
- `felt_blamed_for_absence` = false: 100/100 (cần ≥ 100%) → đạt

| Nhóm | Người | Giúp | Quay lại |
| --- | --- | --- | --- |
| Người đi làm trẻ | 19 | 3.79 | 3.53 |
| Nhóm khác | 19 | 3.37 | 3.21 |
| Năm cuối / việc đầu tiên | 14 | 3.71 | 3.5 |
| Năm nhất xa nhà | 15 | 3.73 | 3.87 |
| Vừa học vừa làm | 14 | 3.93 | 3.64 |
| Áp lực học | 19 | 3.95 | 3.74 |
| Không có ai an toàn (tình huống) | 25 | 3.32 | 3.24 |
| (tin chiêm tinh) | 27 | 3.26 | 3.41 |
| (nửa tin) | 45 | 4.07 | 3.78 |
| (không tin) | 28 | 3.68 | 3.39 |
| (chỉ nhập ngày sinh) | 30 | 3.77 | 3.67 |

Cờ: bị trách 0, bị ép 0, lo riêng tư 0, phụ thuộc 0.

Lời chê ở các cặp điểm thấp nhất:

- Không có lối vào Tarot chuyện yêu xa.
- Thêm một màn hỏi nữa, mình chỉ mở vài giây.
- Không có lối vào Tarot ngay từ màn đầu.

Codex so với Claude trên cùng 20 người giả: giúp 4.4 so với 3.7, quay lại 4.25 so với 3.55. Lệch trung bình: giúp 0.7, quay lại 0.7.
- Người giả lệch điểm giúp từ 2 trở lên: P065, P080.
- Câu kiểm trả lời ngược nhau: P027/found_right_path, P050/found_right_path, P061/found_right_path, P065/found_right_path, P080/found_right_path, P082/found_right_path, P083/found_right_path.
- Một lời chê của Codex: Phần gỡ chuyện vẫn chưa cho mình biết sẽ giúp chuyện gia đình tới đâu.

## Ý 4. Hỏi lại việc đã giữ, một lần, bỏ qua được

Kết luận theo ngưỡng phần người giả: **ĐẠT**.

- `asked_once_no_penalty` = true: 100/100 (cần ≥ 100%) → đạt
- `answer_changes_next` = true: 100/100 (cần ≥ 100%) → đạt
- Chưa thử được bằng mock: 'Câu trả lời làm đổi gợi ý lần sau' chỉ kiểm thật được khi có code.

| Nhóm | Người | Giúp | Quay lại |
| --- | --- | --- | --- |
| Người đi làm trẻ | 19 | 2.95 | 3.0 |
| Nhóm khác | 19 | 3.0 | 3.0 |
| Năm cuối / việc đầu tiên | 14 | 3.07 | 3.21 |
| Năm nhất xa nhà | 15 | 3.2 | 3.27 |
| Vừa học vừa làm | 14 | 2.93 | 3.0 |
| Áp lực học | 19 | 2.89 | 2.95 |
| Không có ai an toàn (tình huống) | 25 | 3.16 | 3.12 |
| (tin chiêm tinh) | 27 | 3.11 | 3.11 |
| (nửa tin) | 45 | 2.96 | 3.0 |
| (không tin) | 28 | 2.96 | 3.11 |
| (chỉ nhập ngày sinh) | 30 | 2.9 | 3.0 |

Cờ: bị trách 1, bị ép 11, lo riêng tư 2, phụ thuộc 0.
Câu trong mock bị chỉ ra nhiều nhất: 'Thử được chưa?' (10); 'Hôm qua bạn giữ việc: Đi ngủ trước 12 giờ. Thử được chưa?' (3); 'Lần sau Lá gợi việc nhỏ hơn một chút.' (1)

Lời chê ở các cặp điểm thấp nhất:

- Hỏi đã làm chưa nghe y như quản lý hỏi chỉ tiêu.
- Mùa thi bị hỏi lại việc đã giữ thấy như bị giục.
- Hỏi lại chuyện hôm qua thấy chán, mình muốn cái mới.

Codex so với Claude trên cùng 20 người giả: giúp 2.4 so với 2.7, quay lại 2.3 so với 2.8. Lệch trung bình: giúp 0.4, quay lại 0.5.
- Người giả lệch điểm giúp từ 2 trở lên: không có.
- Câu kiểm trả lời ngược nhau: không có.
- Một lời chê của Codex: Đi làm về muộn thì việc nhỏ hơn cũng chưa chắc giải quyết được chuyện ngủ.

## Ý 5. Chuyện ngắn minh họa về cảm giác lạc lõng

Kết luận theo ngưỡng phần người giả: **ĐẠT**.

- `mistook_for_real_testimony` = false: 100/100 (cần ≥ 100%) → đạt
- `felt_difficulty_denied` = false: 100/100 (cần ≥ 100%) → đạt
- `felt_false_promise` = false: 100/100 (cần ≥ 100%) → đạt

| Nhóm | Người | Giúp | Quay lại |
| --- | --- | --- | --- |
| Người đi làm trẻ | 19 | 1.95 | 2.11 |
| Nhóm khác | 19 | 1.63 | 2.11 |
| Năm cuối / việc đầu tiên | 14 | 2.64 | 2.5 |
| Năm nhất xa nhà | 15 | 3.6 | 3.33 |
| Vừa học vừa làm | 14 | 2.5 | 2.71 |
| Áp lực học | 19 | 3.05 | 2.89 |
| Không có ai an toàn (tình huống) | 25 | 2.8 | 2.76 |
| (tin chiêm tinh) | 27 | 2.41 | 2.48 |
| (nửa tin) | 45 | 2.73 | 2.73 |
| (không tin) | 28 | 2.29 | 2.43 |
| (chỉ nhập ngày sinh) | 30 | 2.63 | 2.67 |

Cờ: bị trách 0, bị ép 0, lo riêng tư 0, phụ thuộc 0.

Lời chê ở các cặp điểm thấp nhất:

- Chuyện cảm xúc dài, không có việc gì rõ để làm.
- Chuyện sinh viên năm nhất không liên quan, đọc xong không nhớ gì.
- Chuyện sinh viên năm nhất không phải chuyện của mình.

Codex so với Claude trên cùng 20 người giả: giúp 3.15 so với 2.95, quay lại 2.95 so với 2.85. Lệch trung bình: giúp 0.5, quay lại 0.3.
- Người giả lệch điểm giúp từ 2 trở lên: P027.
- Câu kiểm trả lời ngược nhau: không có.
- Một lời chê của Codex: Hôm nay mình mệt vì bài tốt nghiệp, chuyện ăn một mình chưa trúng điều đó.

## Ý 6. Gửi một lá cho người quen, kèm mẫu câu mở lời

Kết luận theo ngưỡng phần người giả: **TRƯỢT**.

- `saw_preview` = true: 100/100 (cần ≥ 100%) → đạt
- `worried_private_info_attached` = false: 100/100 (cần ≥ 100%) → đạt
- `recipient_needs_account` = false: 99/100 (cần ≥ 100%) → trượt
- Chưa thử được bằng mock: Không kèm mood/ngày sinh và người nhận không cần tài khoản phải kiểm trên app thật bằng dữ liệu giả.

| Nhóm | Người | Giúp | Quay lại |
| --- | --- | --- | --- |
| Người đi làm trẻ | 19 | 2.53 | 2.74 |
| Nhóm khác | 19 | 3.16 | 3.16 |
| Năm cuối / việc đầu tiên | 14 | 2.21 | 2.36 |
| Năm nhất xa nhà | 15 | 2.8 | 3.0 |
| Vừa học vừa làm | 14 | 2.64 | 3.0 |
| Áp lực học | 19 | 2.47 | 2.63 |
| Không có ai an toàn (tình huống) | 25 | 2.56 | 2.68 |
| (tin chiêm tinh) | 27 | 3.44 | 3.52 |
| (nửa tin) | 45 | 2.44 | 2.69 |
| (không tin) | 28 | 2.21 | 2.36 |
| (chỉ nhập ngày sinh) | 30 | 2.7 | 2.97 |

Cờ: bị trách 0, bị ép 0, lo riêng tư 0, phụ thuộc 0.

Lời chê ở các cặp điểm thấp nhất:

- Mùa thi không có lý do gì để gửi lá cho ai.
- Đang hết sức, không có sức gửi cho ai.
- Không có ai để gửi, mà gửi lá bói cũng không phải kiểu của mình.

Codex so với Claude trên cùng 20 người giả: giúp 2.55 so với 2.5, quay lại 2.7 so với 2.7. Lệch trung bình: giúp 0.45, quay lại 0.4.
- Người giả lệch điểm giúp từ 2 trở lên: P048.
- Câu kiểm trả lời ngược nhau: P022/would_send, P048/would_send, P082/would_send, P095/would_send.
- Một lời chê của Codex: Gửi một lá cho vui vẫn chưa dễ bằng nhắn thẳng chuyện mình muốn nói.

## Ý 7. 'Điều từng giúp mình': tự đánh dấu, tự bỏ dấu

Kết luận theo ngưỡng phần người giả: **TRƯỢT**.

- `could_find_again` = true: 97/100 (cần ≥ 90%) → đạt
- `could_remove` = true: 98/100 (cần ≥ 100%) → trượt
- `worried_auto_saved` = false: 100/100 (cần ≥ 100%) → đạt
- Chưa thử được bằng mock: Xóa được thật và không tự lưu mood/Tarot phải kiểm trên app thật.

| Nhóm | Người | Giúp | Quay lại |
| --- | --- | --- | --- |
| Người đi làm trẻ | 19 | 2.95 | 2.95 |
| Nhóm khác | 19 | 2.63 | 2.79 |
| Năm cuối / việc đầu tiên | 14 | 3.21 | 3.14 |
| Năm nhất xa nhà | 15 | 3.2 | 3.27 |
| Vừa học vừa làm | 14 | 3.07 | 3.07 |
| Áp lực học | 19 | 3.16 | 3.11 |
| Không có ai an toàn (tình huống) | 25 | 3.0 | 3.12 |
| (tin chiêm tinh) | 27 | 3.04 | 3.15 |
| (nửa tin) | 45 | 3.13 | 3.11 |
| (không tin) | 28 | 2.82 | 2.82 |
| (chỉ nhập ngày sinh) | 30 | 3.07 | 3.07 |

Cờ: bị trách 0, bị ép 0, lo riêng tư 25, phụ thuộc 0.
Câu trong mock bị chỉ ra nhiều nhất: 'Ai mở được app trên máy này thì cũng thấy danh sách này.' (25)

Lời chê ở các cặp điểm thấp nhất:

- Mục Mình với danh sách, tôi không biết tìm ở đâu.
- Thêm nút thêm danh sách, mắt kém không biết tìm ở đâu.
- Mình không có thói quen đánh dấu, chắc chẳng mở lại danh sách.

Codex so với Claude trên cùng 20 người giả: giúp 3.2 so với 3.05, quay lại 3.0 so với 3.05. Lệch trung bình: giúp 0.65, quay lại 0.75.
- Người giả lệch điểm giúp từ 2 trở lên: P038.
- Câu kiểm trả lời ngược nhau: không có.
- Một lời chê của Codex: Hôm trống trải mình vẫn cần câu mới hợp lúc đó.

## Ý 8. Trò chơi chọn kết thúc chuyện vui đời sinh viên

Kết luận theo ngưỡng phần người giả: **TRƯỢT**.

- `understood_how_to_play` = true: 98/100 (cần ≥ 90%) → đạt
- `joke_hurt` = false: 96/100 (cần ≥ 100%) → trượt
- `could_stop` = true: 100/100 (cần ≥ 100%) → đạt

| Nhóm | Người | Giúp | Quay lại |
| --- | --- | --- | --- |
| Người đi làm trẻ | 19 | 2.37 | 2.47 |
| Nhóm khác | 19 | 1.89 | 2.16 |
| Năm cuối / việc đầu tiên | 14 | 2.43 | 2.43 |
| Năm nhất xa nhà | 15 | 3.0 | 3.07 |
| Vừa học vừa làm | 14 | 3.21 | 3.36 |
| Áp lực học | 19 | 3.11 | 3.16 |
| Không có ai an toàn (tình huống) | 25 | 2.76 | 2.8 |
| (tin chiêm tinh) | 27 | 2.59 | 2.7 |
| (nửa tin) | 45 | 2.87 | 3.02 |
| (không tin) | 28 | 2.32 | 2.36 |
| (chỉ nhập ngày sinh) | 30 | 2.6 | 2.7 |

Cờ: bị trách 1, bị ép 0, lo riêng tư 0, phụ thuộc 0.
Câu trong mock bị chỉ ra nhiều nhất: 'bạn Tùng nhắn: 'Ủa, nộp hôm nay hả?'' (1)

Lời chê ở các cặp điểm thấp nhất:

- Nhân vật bị đem ra đùa trùng tên mình, mình vốn hay bị trêu nên đọc thấy nhột.
- Trò chơi sinh viên, không hợp với mình.
- Chuyện trà sữa với tên file tiếng Anh tôi đọc không hiểu.

Codex so với Claude trên cùng 20 người giả: giúp 2.5 so với 2.65, quay lại 2.5 so với 2.7. Lệch trung bình: giúp 0.25, quay lại 0.3.
- Người giả lệch điểm giúp từ 2 trở lên: không có.
- Câu kiểm trả lời ngược nhau: P001/joke_hurt, P033/joke_hurt.
- Một lời chê của Codex: Mang trà sữa tới chưa giải quyết được chuyện người khác phải làm thay.

## Giới hạn

- Người giả và giám khảo đều là mô hình AI, chấm mô tả bằng chữ chứ không dùng app thật. Kết quả cho biết hướng, không chứng minh người thật sẽ vui hơn hay quay lại.
- Mỗi người giả chỉ chấm một tình huống hôm nay. Ý hợp với người mệt có thể khác với ý hợp với người vắng lâu.
- Ngưỡng 'mọi ca' trong bản tranh luận là yêu cầu thiết kế; ở đây nó được đo bằng cảm nhận của từng người giả, nên một người hiểu nhầm là đủ để trượt.
- Các ngưỡng về lưu dữ liệu, xóa, thu hồi link, không ghi log phải kiểm trên app thật bằng dữ liệu giả khi có code.
