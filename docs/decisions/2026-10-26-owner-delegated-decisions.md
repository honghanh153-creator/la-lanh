# Quyết định được owner uỷ quyền (26/10/2026)

Owner viết ngày 26/10/2026: "Các phần cần tôi chốt, bạn chốt giúp tôi đi, rồi cần thì nhờ codex viết lại cho mượt.
Những phần bạn đề xuất làm đi nhé. Cứ làm lần lượt." Claude ghi lại từng quyết định ở đây để Codex review đúng SHA và
chuốt câu chữ. Đây là quyết định uỷ quyền, không phải owner tự đọc từng câu. Nếu owner muốn đổi, quyết định của owner
thay thế mục tương ứng.

Không thuộc phạm vi uỷ quyền: merge vào `main`, deploy, chạm server/DB thật, đổi IAM/secret/budget, bật provider. Các
bước đó vẫn cần lệnh riêng của owner và operator thực hiện theo runbook.

| # | Việc | Quyết định | Ai làm tiếp |
|---|---|---|---|
| 1 | Câu chữ #76 (hạn receipt) | Footer: "Bạn có thể xem lại bản đọc trên thiết bị này trong tối đa 30 ngày." Màn mất receipt: "Bản đọc có thể đã hết hạn, bị rút hoặc xoá. Dữ liệu trình duyệt trên thiết bị này cũng có thể đã bị xoá." Không nêu quy định làm nguyên nhân; không hứa thời điểm xoá | Codex chuốt và áp vào #76, Claude review |
| 2 | #74 (CI kiểm chứng Compose) | Nhận. Merge vào `collab/integration` sau khi #82 merge và integration xanh lại | Merge theo SHA đã APPROVE, chạy `CI=1 pnpm check` |
| 3 | Copy màn hình P09 D2 | Duyệt bản nháp 25/10: mỗi dòng hiện quan hệ (ngữ cảnh của B, không bao giờ biệt danh A đặt); cửa vào ở trang Radar và trang link mời đã dùng; link từ màn mất receipt thêm sau #76 | #83 (Claude), Codex review và chuốt |
| 4 | R04 cơ chế khoảng | Duyệt khoảng thay cho số nguyên, hiển thị dạng chữ "70–95" (chưa dùng thanh khoảng) | Triển khai sau R03 |
| 5 | R04 bảng neo §4.2 | Giữ đề xuất (p97 → 90, p99,5 → 97). PR triển khai in phân vị tham chiếu thật; chỉ chỉnh neo nếu AC3 không đạt, và ghi lý do | Claude khi triển khai |
| 6 | R04 công thức độ rộng §5 | Giữ công thức hiện có (đã có phản ví dụ và test biên); không đổi sang ±10 cố định | Claude khi triển khai |
| 7 | R04 câu giải thích khoảng | "Khoảng rộng hơn khi ít tín hiệu hoặc chưa rõ giờ sinh, và không đo mức độ hợp nhau." | Codex chuốt; đưa vào workbook khi triển khai |
| 8 | Giọng thứ tư của Hợp gu (R03) | `deep_dive` ("Đọc kỹ"), như runtime đang có; không thêm `roast` cho Hợp gu. 140 câu `roast` trong workbook #65 không dùng; 140 câu `deep_dive` cần viết mới ở bước riêng. 420 câu của ba giọng còn lại được rà lần lượt | Claude rà và viết, Codex chuốt |
| 9 | Release #75 | Đồng ý release khi đủ điều kiện: #82 và #76 đã merge, #74 đã nhận, `CI=1 pnpm check` trên integration xanh (có cả lượt Codex), operator có backup mới + bật timer + chạy migration `20261023_0038`, smoke staging đạt. Việc bấm merge vào `main` và deploy vẫn cần owner ra lệnh cho operator | Owner ra lệnh; operator thực hiện |
| 10 | T02/T03 (workbook #67) | Chưa duyệt trong lượt này: cần rà từng cảnh theo hành động và kiểm hiểu nội dung, không duyệt máy | Claude rà lần lượt, Codex chuốt |

Ghi chú bằng chứng: các lượt `CI=1 pnpm check` do Claude chạy được ghi là của Claude; Codex đã chạy riêng tại
`3d34eb4` và thấy đỏ hai test phụ thuộc ngày (sửa ở #82).

Codex chuốt 26/10: mục 1 không khẳng định lưu trữ chỉ ở thiết bị, không quy việc mất dữ liệu cho một quy định chưa xác định và giữ cả lý do rút/xoá. Mục 7 nói về tín hiệu đầu vào, không ngụ ý khoảng đã được kiểm định như độ chắc thống kê. Các quyết định khác giữ nguyên; Claude review bản sửa này.
