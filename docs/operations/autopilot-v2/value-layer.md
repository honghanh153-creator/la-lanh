# Tầng giá trị (bổ sung vào thiết kế v2)

## Câu hỏi của owner
- "Việc luôn tạo ra giá trị" nằm ở đâu trong thiết kế?
- Những giá trị chưa đo được bây giờ thì làm sao?
- Ví dụ: "nội dung tốt hơn, hấp dẫn hơn".

## Chỗ hở trong bản v2
- `decide()` chỉ ưu tiên theo chỉ số. Giá trị chưa đo được bị bỏ đói, vì máy chỉ nhìn chỗ có đèn: niềm tin, giọng văn, sự bình yên, độ chăm chút, an toàn, việc học được.
- "Rảnh có chủ đích" không bảo đảm luôn có việc có giá trị trong hàng chờ.

## Thiết kế

### 1. Mỗi việc phải khai loại giá trị (critic chặn nếu thiếu)
- **A.** Kết quả người dùng **đo được**: gắn hợp đồng chỉ số.
- **B.** Kết quả người dùng **chưa đo được**: là một **cược giá trị**. Phải đăng ký trước:
  - giả thuyết;
  - bậc bằng chứng nào sẽ xác nhận, và khi nào;
  - khẩu phần thời gian;
  - ngày xét lại.
- **C.** Giảm rủi ro (an toàn, riêng tư, độ tin cậy): đo bằng rủi ro đã đóng.
- **D.** Nền móng: phải trỏ tới mục tiêu hoặc giá trị mà nó mở khoá.
- **E.** Học hỏi: câu hỏi cần trả lời và cách biết đã trả lời xong.

Việc không thuộc loại nào thì bị bác. Lúc đó rảnh còn tốt hơn làm việc vô giá trị.

### 2. Danh mục giá trị (owner đặt tỷ lệ trong policy)
- Ví dụ tỷ lệ: A 40%, B 20%, C 20%, D 10%, E 10%.
- `decide()` cân theo tỷ lệ này ở nhánh 7–9, để chỉ số không nuốt hết sức chứa.

### 3. Thang bằng chứng (giá trị leo dần lên khi có dữ liệu)
1. **Ràng buộc cứng.** Không bao giờ vi phạm, là luật chứ không phải để tối đa hoá:
   - không dự đoán sự kiện đời;
   - câu chữ dễ hiểu, không giải thích kỹ thuật, không giọng gắt;
   - riêng tư.

   Đã có các cổng: clarity gate, cổng trải nghiệm.
2. **Gu của owner, đo bằng so sánh cặp A/B.** So cặp là cách đo gu đáng tin nhất. Mỗi phiên 10 cặp, khoảng 5 phút. Kết quả xếp hạng kiểu Elo theo từng phong cách hay biến thể.
3. **Giám khảo khác model**, được hiệu chỉnh theo các cặp owner đã chọn. Độ khớp đo trên bộ cặp giữ kín. Đủ ngưỡng thì được chấm thay owner, kèm 5% mẫu.
4. **Tester:**
   - nói lại được note nói gì (thấy được hiểu);
   - so cặp trong app;
   - "hợp" 1 chạm;
   - đọc hết.
5. **Hành vi người dùng:** lưu, chia sẻ, quay lại D1/D7; "nếu mất app bạn có tiếc không".

Mỗi cược giá trị ghi rõ đang ở bậc nào. Không được dùng bậc thấp để kết luận điều chỉ bậc cao mới trả lời được. Ví dụ: không kết luận được về giữ chân người dùng khi chưa có người dùng.

### 4. Thẻ giá trị hằng tuần (trong phiên owner, 5 phút)
- "Tuần này tạo ra giá trị gì", kèm bằng chứng: cặp trước/sau, ảnh, lời tester.
- Owner chấm 1–5. Điểm này **tự nó là một chỉ số**, nên giá trị chưa đo được vẫn có tín hiệu theo thời gian.

### 5. Tránh hàng chờ rỗng
- Mỗi điều phối mục tiêu, vòng ngoài và agent nghiên cứu nuôi một **hàng cược giá trị** đã đăng ký trước.
- "Rảnh" chỉ xảy ra khi hàng này rỗng thật. Khi đó máy báo trong thẻ: "hết cược giá trị, đề xuất 3 cược mới".

## Ví dụ: "Nội dung hấp dẫn hơn"

**1. Dịch.** Chưa có người dùng, nên chỉ số chính tạm thời là **tỷ lệ thắng so cặp của owner**: bản mới so với bản cũ, cùng tình huống. Đối trọng:
- 0 vi phạm ràng buộc cứng;
- độ đa dạng giữa các ngày (đo theo `la-lanh-variety-measurement-spec.md`);
- tỷ lệ owner bác.

**2. Bảng chấm "hấp dẫn"** bám north star (bình yên, vui, thấy được hiểu). Mỗi tiêu chí có ví dụ tốt/xấu lấy từ chính các lần owner sửa:
- **Thấy được hiểu:** có cảnh đời thường cụ thể.
- **Móc câu:** tiêu đề khiến muốn đọc tiếp.
- **Bình yên:** không ép, không doạ.
- **Một chút vui:** bất ngờ nhẹ.
- **Việc nhỏ làm được trong hôm nay.**
- **Không lặp** với các ngày gần đó.

**3. Leo đồi:**
1. Sinh 3 biến thể cho mỗi tình huống.
2. Lọc qua ràng buộc cứng.
3. Giám khảo xếp hạng.
4. Owner so cặp top 2 trong phiên (5 phút).
5. Bản thắng thành ví dụ gu, codemod áp kiểu sửa đó cho cả kho.
6. Chấm lại trên bộ giữ kín: giữ hoặc quay lui.

**4. Khi có tester:** thêm "nói lại được", "hợp" 1 chạm, đọc hết, so cặp trong app.
**5. Khi có người dùng:** lưu, chia sẻ, D1/D7. Tiêu chí nào không dự báo được hành vi thì bị bỏ khỏi bảng chấm.

**Owner bỏ ra:** khoảng 5 phút so cặp mỗi phiên. Giám khảo khớp đủ thì giảm xuống còn mẫu 5%.
