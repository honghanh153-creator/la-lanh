# Giám khảo mù: "Lá có hiểu mình không?" và nhãn "việc nhẹ"

Phiên bản: `judge-rubric-v1-2026-11-14`. Viết trước lần chấm đầu tiên. Đổi rubric thì đổi phiên bản và chấm lại toàn bộ.

Giám khảo là một Claude subagent riêng. Nó chỉ nhận:

- hồ sơ người giả (tên, tuổi, hoàn cảnh, áp lực, tính cách, nhịp ngày, muốn gì ở app, điều làm họ bỏ app, họ đã nhập gì vào app);
- nội dung của **một ngày**: mood họ chọn, tiêu đề, giải thích, cảnh ngoài đời, việc nhỏ, lời của Lá, "Vì sao hôm nay" nếu có, câu Lá đáp lại mood.

Giám khảo **không** biết bản code nào, lần chạy nào, ngưỡng nào, người giả khác ra sao, hay đây là ngày thứ mấy. Các mục được xáo trộn giữa nhiều người giả; mỗi mục chấm độc lập.

## Câu hỏi chấm

"Nếu là người này, đọc nội dung hôm nay, mình có thấy Lá hiểu mình không?"

| Điểm | Nghĩa |
|---|---|
| 1 | Sai người hoặc sai lúc: nói chuyện không dính tới đời họ, trái với mood họ vừa chọn, giọng làm họ khó chịu, hoặc giao việc họ sẽ bực. |
| 2 | Chung chung: ai đọc cũng được; có thể đúng nhưng họ không thấy mình trong đó. Hoặc có một chỗ lệch rõ (việc nhỏ quá nặng cho mood đó, cảnh không hợp hoàn cảnh). |
| 3 | Tạm được: có một phần chạm tới hoàn cảnh hoặc cảm giác của họ, phần còn lại chung chung. Họ đọc xong không khó chịu. |
| 4 | Hợp: cảnh và việc nhỏ khớp với một áp lực thật của họ, giọng hợp, việc nhỏ làm được trong ngày với mood đó. |
| 5 | Trúng: họ sẽ nghĩ "đúng là mình hôm nay"; nội dung nối với mood và với điều họ đang lo, việc nhỏ vừa sức và đáng làm. |

Quy tắc:

- Chấm từ góc nhìn người giả, không phải góc nhìn người viết nội dung. Không cộng điểm vì câu hay.
- Không đoán phần hồ sơ không có. Không trừ điểm vì Lá không biết điều người dùng chưa nhập.
- Câu trái mood vừa chọn → tối đa 2. Việc nhỏ nặng (phải nói chuyện với người khác, bắt đầu việc lớn, quyết định) vào ngày Đuối → tối đa 3.
- Ghi một câu lý do ngắn, tiếng Việt thường, không lặp lại hồ sơ.

Đầu ra mỗi mục: `{"item_id": "...", "score": 1-5, "reason": "..."}`.

## Nhãn "việc nhẹ" (cho chỉ số mood)

Một giám khảo mù khác chỉ nhận danh sách câu việc nhỏ (không biết người, mood hay ngày). Mỗi câu gắn một nhãn:

- `light`: một người đang mệt có thể làm **một mình, trong 5 phút**, không cần liên lạc, hỏi, nói hay gửi gì cho ai, không phải bắt đầu hay hoàn thành một phần việc học/làm, không phải đưa ra quyết định hay đánh giá.
- `not_light`: còn lại.

Nhãn được lưu theo nội dung câu trong `labels/action-weight.json`. Câu mới chưa có nhãn thì báo cáo dùng luật dự phòng trong `apps/api/scripts/persona_metrics.py` (`light_by_rule`) và ghi rõ nguồn "rule". Nếu API sau này trả về độ nặng của việc nhỏ (`weight` / `action_weight`), báo cáo dùng giá trị đó trước và ghi nguồn "api".

## Cách chạy giám khảo (lặp lại được)

1. `pnpm personas:run` ghi `judge-packets.jsonl` và `label-packets.jsonl` vào thư mục lần chạy: chỉ gồm mục **chưa có điểm** trong bộ nhớ đệm.
2. Giao mỗi tệp cho một Claude subagent mới, kèm file này, với lời dặn trong `judge-prompt.md`. Subagent ghi điểm vào tệp JSON.
3. `pnpm personas:merge-scores -- <tệp điểm>` gộp vào `labels/judge-scores.json` hoặc `labels/action-weight.json`.
4. `pnpm personas:report -- --run <thư mục>` chấm lại. Mục có nội dung giống hệt lần trước dùng lại điểm cũ, nên lần chạy sau chỉ cần chấm phần nội dung mới.
