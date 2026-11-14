# 100 người giả để đo "Lá có hiểu mình không, có muốn quay lại không"

Owner chọn đo bằng người giả có ngưỡng cụ thể thay cho số liệu người dùng thật và thay cho đợt dùng thử thật, trong lúc này (14.11.2026).
Mọi người trong `personas-100.json` là **hư cấu**: không phải người thật, không dùng dữ liệu của owner hay của người dùng. Ngày, giờ, nơi sinh được sinh ngẫu nhiên có hạt giống cố định.

## Chạy

```bash
pnpm personas:run
```

Một lệnh: kiểm bộ người giả, cho 100 người dùng app 29 ngày trên API chạy ở máy (SQLite tạm, dữ liệu giả, không mạng, không production), rồi chấm theo `thresholds.md`.
Kết quả ở `qa/personas/runs/<ngày>-<sha>/report.md`. Đặt tên khác: `pnpm personas:run -- --name sau-dot1`. Cần build thư viện lá số một lần: `pnpm astro:build-native`.
Mất khoảng 3–5 phút với 7 tiến trình.

Điểm "hiểu mình" và nhãn "việc nhẹ" do giám khảo mù chấm, lưu theo nội dung trong `labels/`. Nội dung không đổi thì dùng lại điểm cũ.
Nội dung mới sinh ra `judge-packets.jsonl` / `label-packets.jsonl` trong thư mục lần chạy; cách chấm ở `judge-prompt.md`, rồi `pnpm personas:merge-scores -- <tệp>` và `pnpm personas:report -- --run <thư mục>`.
Chưa chấm đủ thì báo cáo ghi "chưa đo" cho mục đó, không đoán.

## Bộ người giả được dựng thế nào

1. `build_skeleton.py` (hạt giống `20261114`) chia đúng tỉ lệ và gán phần cần chính xác:
   - 56 sinh viên: năm nhất xa nhà 8, ký túc xá/phòng trọ 7, mùa thi 8, năm cuối tìm việc 8, làm thêm 8, tiền eo hẹp 6, áp lực gia đình 6, so sánh trên mạng 5; 18 ngành; Bắc 34 / Trung 33 / Nam 33 người trên toàn bộ;
   - 25 người đi làm trẻ: việc đầu tiên 6, làm ca 6, deadline dày 7, áp lực từ sếp 6;
   - 19 người khác: lớn tuổi 5, cha mẹ con nhỏ 5, LGBTQ+ 5, ít quen điện thoại 4;
   - dữ liệu đã nhập vào app: 30 chỉ ngày sinh, 20 giờ khoảng (một khung giờ trong ngày) + nơi sinh, 50 giờ + nơi chính xác;
   - mẫu mood 29 ngày theo hoàn cảnh (mùa thi căng dần rồi đuối, làm ca lên xuống, nhớ nhà cuối tuần, cuối tháng hết tiền…) cộng nhiễu ngẫu nhiên;
   - các con số mô hình quay lại đọc: mức mở app mỗi ngày, hứng thú với chiêm tinh/Tarot, chịu lặp, chịu bị giao việc, tỉ lệ giữ việc nhỏ;
   - câu thử an toàn: 10 người gõ 13 câu có ý định khủng hoảng (thẳng, gián tiếp, ẩn ý, tiếng lóng, có và không dấu); 18 người gõ 21 câu "chết" theo nghĩa bóng.
2. Bốn Claude subagent, mỗi bên 25 người, viết phần đời sống trên khung đó: hoàn cảnh, áp lực, tính cách, nhịp ngày, thói quen điện thoại, muốn gì ở app, điều làm họ bỏ app (và nhãn tương ứng), mức chịu lặp/chịu việc, giải thích mẫu mood, loại việc nhỏ họ hay giữ, 3–6 câu hỏi Tarot bằng giọng của họ. Câu hỏi Tarot thường không được chứa chữ "chết" hay ý định khủng hoảng, để hai bộ câu thử an toàn sạch.
3. `pnpm personas:check` kiểm tỉ lệ, độ đủ trường, tuổi khớp ngày sinh, nhãn hợp lệ, và tách bạch câu thử an toàn.

## Giới hạn

- Người giả là giả. Mô hình quay lại là luật tự đặt, đã hiệu chỉnh theo số công bố của app lối sống, chỉ để so các bản với nhau.
- Giám khảo là một mô hình AI, không phải người dùng. Điểm của nó thiên về đọc chữ, không thấy giao diện, tốc độ hay thông báo.
- Lớp web chỉ được lấy phần câu Lá đáp lại mood từ catalog web; giao diện không được chạy trong trình duyệt cho 2.900 ngày-người.
- Mood được chọn sau khi mở note, rồi mở lại note; nếu app cần làm mới theo cách khác thì bộ chạy phải sửa theo.
