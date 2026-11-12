# Phiên duyệt 1 — thứ Sáu 13.11.2026 (60 phút)

Thuộc kế hoạch thử nghiệm 4 tuần (báo cáo DevCon bản 3.1). Hết 60 phút thì dừng. Mục chưa xong chuyển sang phiên sau và không bị tính là lỗi.

Mỗi mục gồm: việc gì, bạn cần quyết gì, đề xuất của Claude. Bạn chỉ cần trả lời **đồng ý / không / để sau**. Đồng hồ ghi phút bắt đầu khi bạn mở file này.

| # | Mục | Phút | Đề xuất của Claude |
|---|---|---|---|
| 1 | #354 hook chặn lệnh nguy hiểm | 12 | Tách đôi |
| 2 | #411 + #404 câu chữ Daily | 12 | Cho Claude sửa tiếp, bạn không cần đọc câu |
| 3 | #388 nghiệm thu thử | 10 | Bạn thử 1 lượt với dữ liệu giả |
| 4 | #134 kiểm trước author check | 5 | Đóng, vì đã có bản khác |
| 5 | #127 cầu nối Google Sheet | 5 | Giữ đóng băng |
| 6 | #68 PRD Nơi bình yên | 2 | Đóng, mở lại khi cần |
| — | Ghi sổ phút | 4 | |
| — | Dự phòng | 10 | |

## 1. #354 — hook chặn lệnh nguy hiểm (12')

**Hiện trạng.** PR gộp ba việc: hook chặn lệnh có thể làm mất code, đo thời gian từng PR, và nhãn trạng thái. Codex còn tìm ra 2 cách lách hook (P1). Hook trên máy đã chạy được: hôm nay nó chặn đúng một lệnh force-push.

**Vì sao không vá tiếp.** Một bộ lọc lệnh thì luôn còn cách lách. Ranh giới cứng phải là sandbox và quyền của token (xem spec 1b).

**Đề xuất.**
- (a) Tách phần đo thời gian và nhãn thành PR riêng, chạy vòng review bình thường.
- (b) Giữ hook ở vai trò "lớp cảnh báo". Ghi rõ điều này trong PR, không hứa chặn được mọi lệnh. Merge sau khi Codex đồng ý với cách ghi.

**Bạn quyết:** đồng ý tách đôi theo (a) + (b)?

## 2. #411 + #404 — câu chữ Daily (12')

**#411** thêm luật chặn link, email, số điện thoại và chỗ trống mẫu trong câu hiện cho người dùng. Không đổi câu nào. Codex chặn vì luật đang bỏ sót tên miền có đuôi lạ (ví dụ `vi-du.ai`).
→ **Đề xuất:** Claude sửa luật để bắt mọi dạng `chữ.chữ` giống tên miền, rồi Codex xem lại. Bạn không cần đọc câu nào.

**#404** viết lại câu Daily cho tình huống "nhận lời giúp khi chưa xem lịch". 68 câu vẫn ở trạng thái chờ duyệt nên người dùng chưa thấy. Codex chặn vì các mảnh câu được ghép ngẫu nhiên: tiêu đề nói về "bạn thân" có thể bị ghép với cảnh "báo cáo cho sếp".
→ **Đề xuất:** câu dùng chung không nhắc tới người cụ thể. Chỉ câu riêng của mỗi cảnh mới nhắc sếp, mẹ hay bạn.

**Bạn quyết:** đồng ý hai hướng sửa này? Bạn sẽ duyệt câu khi gom đủ một đợt cuối, như đã chốt.

## 3. #388 — nghiệm thu thử (10')

**Việc gì.** Khi người dùng chỉ nhớ giờ sinh khoảng (ví dụ "buổi sáng") và chọn hệ Ấn Độ, app đang hiện trang rút gọn. PR này cho họ đọc được những vị trí không đổi trong khoảng giờ đó, giống hệ Tây phương.

**Bạn làm.** Claude gửi link bản xem thử đúng SHA kèm dữ liệu giả. Bạn trả lời 4 câu:
1. Hiểu ngay đang đọc gì?
2. Thấy nhẹ, dễ chịu?
3. Có câu nào khẳng định quá mức so với giờ khoảng?
4. Còn lỗi nhìn thấy? (đạt khi trả lời "không")

Mục này cũng để đo xem một lần nghiệm thu thật tốn bao nhiêu phút.

## 4. #134 — kiểm nhanh trước author check (5')

PR mở từ 30.10. Phần kiểm nhanh và khoá việc nặng đã vào integration qua các PR sau (`collab-preflight`, `collab-lock`).
→ **Đề xuất:** đóng PR và ghi chú "đã thay bằng bản khác".

## 5. #127 — cầu nối Google Sheet (5')

PR gần 3.000 dòng, chưa bật, cần tài khoản dịch vụ Google. Thứ tự ưu tiên hiện tại là nội dung → bảo mật/riêng tư → tính năng.
→ **Đề xuất:** giữ đóng băng, đổi nhãn sang "hoãn" để không còn nằm trong hàng chờ bạn. Mở lại khi tới phần tính năng.

## 6. #68 — PRD Nơi bình yên (2')

Bạn đã hoãn toàn bộ Nơi bình yên từ 23.10.
→ **Đề xuất:** đóng. Nhánh vẫn còn, mở lại được bất cứ lúc nào.

## Sau phiên

Claude làm theo quyết định, ghi phút vào `docs/reviews/so-phut-duyet.csv`, và báo lại trong 1–2 dòng.
