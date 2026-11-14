## Đọc nhanh

- **Không bản nào đạt đủ.** Bản tốt nhất là V2 (thêm ô "Kể ra"): hiểu mình 3,10 (cần 3,7), 83/100 người từ 3 trở lên (đạt). "Bớt thấy một mình" 3,02 và "bình yên" 3,34 đều chưa tới 3,5. Hai trong bốn nhóm sinh viên yếu đạt 3,5: năm cuối tìm việc và áp lực gia đình. Hai nhóm còn lại chưa đạt: tiền eo hẹp 3,33, vừa học vừa làm 3,12.
- **Thứ tự các bản theo Codex** (cùng 20 người, cùng cách chấm): V0 2,65 → V1 2,75 → V2 2,95. Giám khảo Claude cho V1 thấp hơn V0 (2,73 so với 2,95). Lý do có thể là V0 được chấm trong lượt khác, cùng mốc A; Codex chấm lại V0 theo đúng cách mới thì không thấy tụt. Vì vậy **V1 không làm tệ đi**, nhưng cũng chỉ nhích nhẹ.
- **V3 và V4 không thêm gì.** Chỉ 8/100 người bật "Lá nhớ 7 ngày". Ai bật thì Lá cũng chỉ nhớ mood và việc đã giữ, trong khi người giả muốn Lá nhớ **chuyện họ đang lo**. Nút "Đã thử" không đổi điểm.
- **Độ nhiễu:** ba lô giám khảo chấm cùng một bản cho trung bình lệch nhau tới 0,39 (V3: 2,82 đến 3,21). Khác biệt giữa V2, V3, V4 nằm trong mức nhiễu này. Khác biệt giữa V1 và V2 (0,37 ở Claude, 0,20 ở Codex) là khác biệt duy nhất cả hai giám khảo cùng thấy.

## Vì sao chưa tới 3,7

1. **Không giám khảo nào cho điểm 5** trong 500 lượt chấm. Gần như mọi điểm là 2, 3 hoặc 4. Muốn trung bình 3,7 thì khoảng 70 người phải chấm 4, mà bản tốt nhất mới có 27 người chấm 4.
2. **Ô "Kể ra" là đòn bẩy mạnh nhất, nhưng ít người dùng.** Ở V2, 29 người có kể; nhóm này chấm hiểu mình 3,48, còn 71 người không kể chấm 2,94. Người có kể phần lớn là người không có ai an toàn (13/25 người trong tình huống này). Người rất mệt, người dùng chung máy và người vừa quay lại ít kể hơn nhiều (5–6/25 mỗi nhóm).
3. **Người giả vẫn muốn bốn điều** (tự ghi ở câu "còn thiếu gì", đếm trên V1–V4, mỗi bản khoảng 100 câu):
   - Gợi ý cụ thể cho đúng chuyện của mình (17–23 câu mỗi bản): ví dụ cách nói với trưởng phòng, nên làm bài trường hay đơn khách trước.
   - Lá nhớ hoàn cảnh đang kéo dài của mình (13–19 câu): đang tìm việc, đang thiếu tiền tháng này, đang lo cho con ở xa. Không phải nhớ mood.
   - Màn hình gọn hơn: ít nút, một câu ngắn trước, chữ to (18–22 câu).
   - Chiêm tinh dựa trên lá số của mình, nhất là người chỉ nhập ngày sinh (12–18 câu). Câu "chọn theo vòng xoay, không dựa trên lá số" vẫn làm người tin chiêm tinh hụt hẫng, kể cả khi có lời mời nhập giờ sinh.

## Dữ liệu mới, cần owner quyết

- **V2, ô "Kể ra":** Lá xử lý chữ người dùng tự gõ, **một lần**, để chọn chuyện và đáp một câu. Không lưu, không ghi nhật ký, có lớp khủng hoảng. Đây vẫn là một mục đích dùng dữ liệu mới: chữ tự do có thể chứa chuyện sức khỏe, tình cảm, tên người khác. Cần quyết định riêng, câu thông báo riêng tư được duyệt, và kiểm thật rằng không lưu.
- **V3, "Lá nhớ 7 ngày":** lưu mood và việc đã giữ 7 ngày **trên máy**. Đây là dữ liệu mới, dù chỉ ở trên máy. Người dùng chung máy có thể xem được. Bản này không tăng điểm, nên chưa đáng làm ở dạng này.
- **V4** dựa trên dữ liệu của V3.

## Điều chưa thử (suy ra từ lời người giả, cần owner quyết trước khi thử)

- **"Chuyện đang lo" ghim lại:** người dùng tự chọn một nhãn (ví dụ "Đang tìm việc", "Đang thiếu tiền", "Đang ôn thi", "Lo cho người nhà"). Lá giữ nhãn đó trên máy cho tới khi người dùng bỏ, và chọn note theo nhãn. Đây đúng là điều người giả hỏi nhiều nhất, nhưng cũng là dữ liệu mới (hoàn cảnh sống).
- **Trang chủ gọn:** một câu của Lá trước, các nút gập lại.
- Hai thay đổi này chưa được chấm. Nếu owner muốn, có thể chấm một bản V5 trên 100 người giả như các bản trên.
