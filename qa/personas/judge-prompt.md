# Lời giao việc cho giám khảo mù

Dùng nguyên văn khi giao một tệp packet cho một Claude subagent **mới** (không dùng subagent đã thấy code, ngưỡng hay lần chạy khác).
Thay `<PACKETS>` và `<OUT>` bằng đường dẫn thật. Mỗi subagent nhận tối đa khoảng 100 mục.

## A. Chấm "Lá có hiểu mình không"

> Bạn là giám khảo mù. Đọc rubric ở `qa/personas/judge-rubric.md` (chỉ phần "Câu hỏi chấm" và "Quy tắc").
> Tệp `<PACKETS>` có mỗi dòng một mục JSON: `profile` là một người hư cấu, `today` là nội dung app cho họ xem trong một ngày.
> Chấm từng mục độc lập, từ góc nhìn người đó, theo thang 1–5 của rubric. Không đọc file nào khác trong repo.
> Ghi `<OUT>` là một mảng JSON `[{"item_id": "...", "score": 1-5, "reason": "một câu tiếng Việt ngắn"}]`, đủ mọi mục, đúng `item_id`.
> Kiểm tra tệp parse được và số mục bằng số dòng đầu vào. Trả lời một dòng: đường dẫn và số mục.

## B. Gắn nhãn "việc nhẹ"

> Bạn là người gắn nhãn mù. Đọc phần "Nhãn việc nhẹ" trong `qa/personas/judge-rubric.md`.
> Tệp `<PACKETS>` có mỗi dòng `{"action": "..."}`. Gắn `light` hoặc `not_light` cho từng câu, độc lập, không đoán người dùng là ai.
> Ghi `<OUT>` là mảng JSON `[{"action": "<giữ nguyên chuỗi>", "label": "light" | "not_light"}]`, đủ mọi câu. Trả lời một dòng: đường dẫn và số mục.

Sau đó: `pnpm personas:merge-scores -- <OUT>` rồi `pnpm personas:report -- --run qa/personas/runs/<tên>`.
