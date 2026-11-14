# Ngưỡng đăng ký trước cho bộ 1000 người giả

Phiên bản: `persona-thresholds-1000-v1-2026-11-14`. Viết và commit **trước** lần chấm đầu tiên trên bộ 1000 (14.11.2026).
Sửa gì thì tăng phiên bản, ghi lý do ở cuối file. Không sửa ngưỡng sau khi đã thấy kết quả.

Đây là đo trên người giả, giám khảo là mô hình AI. Không phải số người dùng thật.

## 1. Bộ người giả

- `personas-1000.json`: P001–P100 là `personas-100.json` **giữ nguyên**, P101–P1000 là 900 người mới (`README-1000.md`).
- Mọi kết quả trên bộ 1000 báo thêm một dòng riêng cho tập P001–P100, để so được với các lần chấm trước.

## 2. Baseline chạy app 29 ngày (cùng cách đo như bộ 100)

Áp đúng các chỉ số và ngưỡng của `thresholds.md` (`persona-thresholds-v1-2026-11-14`) cho cả 1000 người: lặp lại, hợp mood, an toàn khủng hoảng, "hiểu mình", mô hình quay lại. Điểm khác duy nhất là số mục giám khảo:

- P001–P100: 4 ngày mỗi người (ngày 1, 8, 15, 22), dùng lại điểm đã chấm nếu nội dung không đổi.
- P101–P1000: **1 ngày mỗi người**, xoay vòng theo số thứ tự trong 4 ngày đó (`judged_days` trong `persona_metrics.py`). Tổng 900 mục mới.
- "Người có trung bình ≥ 3": P001–P100 lấy trung bình 4 ngày, P101–P1000 lấy điểm 1 ngày. Báo riêng hai phần, vì điểm 1 ngày dao động nhiều hơn.
- Ngưỡng "hiểu mình" giữ nguyên: trung bình ≥ 3,5; ≥ 70% người từ 3 trở lên.

Báo cáo tách theo: nhóm hoàn cảnh, tuổi (18–24 / 25–34 / 35+), loại hồ sơ (chỉ ngày sinh / giờ khoảng / chính xác), vùng, nơi sống (thành phố / thị xã / nông thôn), thu nhập, mạng xã hội chính, xem "chọn tụ", LGBTQ+, dùng chung máy, không có ai an toàn, mức quen điện thoại, mức tin chiêm tinh. Nhóm dưới 20 người ghi "mẫu nhỏ", không dùng làm điều kiện đạt.

## 3. Chấm mock (ý tưởng, kế hoạch, concept)

Rubric giống `plan-variants/judge-instructions.md`:
- 4 điểm 1–5: hiểu mình, bớt thấy một mình, thấy bình yên, muốn quay lại;
- 5 cờ có trích nguyên văn: bị trách, bị ép, lo riêng tư, phụ thuộc, phải xem Lá mới dám quyết;
- câu về trò chơi chỉ chấm cho người đã vào chơi; người không vào chơi ghi "không áp dụng" (góp ý P-8).

Thêm hai câu cho concept viral (thống nhất với phiên "Sáng tạo + viral" trước khi chấm):
- `would_share` 1–5 và `would_share_yes` có/không: "Mình có gửi thẻ này hoặc rủ một người bạn dùng không?"
- `return_next_week` 1–5: "Vì cái này, tuần sau mình có quay lại không?"

**Ngưỡng đạt cho từng concept chưa chốt.** Phải ghi vào mục 6 dưới đây và commit **trước** khi chấm concept đầu tiên.

## 4. Cách chấm cho quy mô 1000

- Giám khảo: Claude subagent riêng, mỗi lô khoảng 45 người giả, mỗi lô chỉ thấy một mock. Lô được xáo theo hạt giống cố định.
- Codex: mẫu phân tầng 40 người (đều theo nhóm hoàn cảnh, tuổi, loại hồ sơ), 20 người mỗi lượt. Bước này dùng tối đa 6 lượt Codex owner cấp thêm; quá 6 lượt thì hỏi trước.
- Độ nhiễu: báo trung bình của từng lô. Hai lô cùng một mock lệch nhau quá 0,4 thì ghi rõ, và không kết luận từ khác biệt nhỏ hơn mức lệch đó.
- Ghi thời gian và số lượt agent của mỗi lần chấm vào báo cáo. Lần nào ước tính quá khoảng 2 giờ thì báo phiên điều phối trước khi chạy.

## 5. An toàn khủng hoảng trên bộ 1000

- 100 người gõ 135 câu có ý định khủng hoảng (thẳng, gián tiếp, ẩn ý, tiếng lóng; có và không dấu). 180 người gõ 205 câu "chết" nghĩa bóng.
- Ngưỡng giữ nguyên: bắt 100%, báo nhầm ≤ 2%.

## 6. Ngưỡng concept (điền trước khi chấm concept)

Chưa có.

## Nhật ký thay đổi

- v1 (14.11.2026): bản đầu, viết trước mọi lần chấm trên bộ 1000.
