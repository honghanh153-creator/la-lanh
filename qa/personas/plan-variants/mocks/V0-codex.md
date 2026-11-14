# Trải nghiệm Lá, mô tả bằng chữ

**Chấm trải nghiệm ở Mốc B** (gồm mọi thứ ở Mốc A cộng phần thêm của Mốc B).

Mô tả trung lập những gì một người dùng thấy và làm ở hai thời điểm. Chỉ có chữ, không phải thiết kế cuối, không có code.
Nguồn: `docs/reviews/2026-11-14-ke-hoach-trien-khai-gop.md` (bản 3, Codex APPROVE).

- Câu đặt trong ngoặc kép có ghi **[nguyên văn kế hoạch]** là câu kế hoạch đã chốt.
- Mọi câu khác là **ví dụ** do người viết mock đặt, để giám khảo có chữ mà đọc. Nhãn mood, nhãn góc đọc và nội dung note chưa được chốt trong kế hoạch.

## Mốc A. Cuối tuần 4 (đã có PR 1–12)

**A1. Mở app.** Không có lời mời đăng nhập nào ở bất kỳ màn nào. Ở chỗ trước đây có lời mời, giờ là một dòng nhỏ:
"Hồ sơ của bạn đang lưu trên trình duyệt này. Đổi máy, xoá dữ liệu trình duyệt hoặc không mở Lá trong 30 ngày thì hồ sơ sẽ mất." **[nguyên văn kế hoạch]**

**A2. Trang chủ.** Từ trên xuống:
- Hàng ba lối nhỏ: "Nghỉ một chút", "Gỡ một chuyện", "Hỏi Tarot" **[nguyên văn kế hoạch]**. Đây là một hàng nút trên Trang chủ, không phải màn chặn trước note. Không có lối "Chơi".
- Hàng chọn mood bằng tiếng Việt dễ hiểu (ví dụ): "Vui, có sức", "Bình thường", "Mệt", "Căng thẳng", "Rối, không rõ mình muốn gì".
- Note hôm nay: một tiêu đề, một cảnh ngoài đời, một việc nhỏ, một câu của Lá. Có nút "Giữ việc này" và nút đóng, đủ lớn để bấm trên điện thoại nhỏ.
- Dưới note: "Đổi góc đọc" và "Không giống mình".

Nếu người dùng chưa cho Lá biết gì về hoàn cảnh, note là **note nền**, viết cho người chưa rõ đang học hay đi làm. Lá không đoán nghề hay tuổi từ ngày sinh. Ví dụ note nền:
- Tiêu đề: "Một việc nhỏ bị treo từ mấy hôm trước."
- Cảnh: "Có một việc không lớn, nhưng cứ mở điện thoại là nhớ tới, rồi lại để đó."
- Việc nhỏ: "Viết tên việc đó ra giấy. Chỉ viết tên, chưa cần làm."
- Lời của Lá: "Việc treo lâu thường nặng hơn khi nghĩ tới so với khi làm."
- Note không trách, không bảo phải nhắn cho ai, không nói kiểu "bạn lại trễ".

**A3. Chọn mood.** Người dùng bấm "Mệt" (1 thao tác). Ngay trên note, không chuyển màn:
- Câu của Lá đổi (ví dụ): "Hôm nay sức bạn có hạn. Không cần làm thêm gì để được nghỉ."
- Việc nhỏ đổi sang việc rất nhẹ (ví dụ): "Uống một cốc nước. Vậy là đủ cho hôm nay."
- Một dòng nhỏ: "Lá đổi việc nhẹ hơn vì bạn chọn Mệt."
- Nếu note trước đó có câu không hợp mood (ví dụ "Hôm nay bạn đang có sức, thử thêm một việc"), câu đó cũng đổi theo. Tiêu đề, cảnh, việc và lời của Lá không câu nào nói ngược mood vừa chọn.
- Từ lúc mở app tới lúc thấy việc nhỏ mới: tối đa 2 thao tác, dưới 70 chữ phải đọc.

Mỗi mood có nhiều câu khác nhau (khoảng 36 câu mỗi mood), nên chọn cùng một mood nhiều ngày liền không gặp lại cùng một câu.

**A4. "Đổi góc đọc".** Mở ra năm lựa chọn (nhãn ví dụ): "Người thân, bạn bè", "Nói chuyện với người khác", "Việc học, việc làm", "Sức khỏe, sức lực", "Chăm sóc bản thân". Chọn một thì cảnh và việc nhỏ đổi theo góc đó ngay. Lựa chọn này chỉ dùng cho lần đọc đó; máy chủ không lưu lại.
- Có note riêng cho sinh viên, cho người đi làm và cho người lớn tuổi. Note sinh viên chỉ hiện khi người dùng tự chọn góc đọc, hoặc được ghi rõ "Ví dụ: chuyện của một bạn sinh viên".
- Ví dụ note sinh viên (góc "Việc học, việc làm"): "Phần bài nhóm của bạn còn dang dở. Việc nhỏ: mở file, viết một dòng tiêu đề cho phần của mình."
- Ví dụ note người đi làm: "Cuối ca còn một việc chưa xong. Việc nhỏ: ghi lại việc đó vào điện thoại để mai làm tiếp, khỏi phải nhớ."
- Ví dụ note người lớn tuổi: "Con cháu bận, nhà yên hơn thường lệ. Việc nhỏ: pha một ấm trà và ngồi ở chỗ có nắng mười phút."

**A5. "Không giống mình".** Chọn lý do: "Không phải chuyện của mình", "Việc nặng quá", "Giọng không hợp". Việc nhỏ và câu của Lá đổi ngay. Không cần viết gì. Lựa chọn chỉ có tác dụng trong lần đó.

**A6. "Vì sao hôm nay có note này?"** Ngày nào cũng có. Bấm vào thấy hai phần tách riêng:
- **Lý do chọn.** Với người có giờ và nơi sinh (ví dụ): "Hôm nay Mặt Trăng đi qua cung liên quan tới việc hằng ngày trong lá số của bạn." Với người chỉ nhập ngày sinh hoặc giờ khoảng, câu dự phòng trung thực: "Hôm nay Lá chọn chuyện này theo vòng xoay, không dựa trên lá số" **[nguyên văn kế hoạch, ví dụ câu dự phòng]**.
- **Phần diễn giải** (ví dụ): "Theo chiêm tinh, đây hay được đọc là ngày hợp với việc nhỏ, làm từng chút. Đây là một cách nhìn, không phải nguyên nhân của chuyện gì."

**A7. Ba lối trên Trang chủ.**
- "Nghỉ một chút": mở phần chỉ để đọc (ví dụ: vài dòng ngắn về việc được phép nghỉ). Không giao việc nào. Có nút đóng.
- "Gỡ một chuyện": dẫn tới "Đổi góc đọc" ở A4, kèm một dòng nói rõ phần này giúp tới đâu (ví dụ): "Chọn chuyện đang làm bạn vướng, Lá đưa một góc nhìn và một việc nhỏ. Lá không thay bạn quyết định." Đây không phải chỗ để kể chuyện hay trò chuyện.
- "Hỏi Tarot": vào thẳng Tarot. Bài đọc Tarot không quyết thay người hỏi, không đoán người khác nghĩ gì. Nếu câu hỏi cho thấy người hỏi đang nghĩ tới việc làm hại bản thân, Lá không rút bài mà hiện thông tin hỗ trợ (câu chữ theo PR lớp khủng hoảng, không chép ở đây).
- Lựa chọn lối vào không được lưu.

**A8. Quay lại sau hai tuần không mở app.** Trang chủ như thường, note của hôm nay. Không có số ngày vắng, không có chuỗi ngày bị mất, không có việc cũ còn tồn, không hỏi vì sao vắng. Việc đã giữ từ hai tuần trước không còn hiện.

**A9. Giữ việc nhỏ.** Nút "Giữ việc này" có cho cả người chỉ nhập ngày sinh, người nhập giờ khoảng và người nhập giờ chính xác. Giữ thì việc hiện lại trên Trang chủ trong ngày đó. Ngày mai note đổi chủ đề, không lặp tiêu đề hôm qua.

## Mốc B. Cuối tuần 6 (thêm PR 13–14)

Mọi thứ ở mốc A vẫn còn. Thêm:

**B1. Chuyện minh họa ngắn.** Thỉnh thoảng Trang chủ có thẻ "Một chuyện ngắn". Trên đầu ghi: "Chuyện minh họa, không phải lời kể của người thật." Có nút "Bỏ qua". Có 4 chuyện; Lá chọn bản hợp với góc đọc người dùng đã chọn, chưa chọn thì là bản chung. Ví dụ:
- Bản sinh viên: "Một bạn năm nhất ăn trưa một mình ở căng tin. Nhóm bàn bên cười to chuyện gì đó bạn không hiểu. Tối về phòng trọ, bạn nghĩ chắc ai cũng có nhóm rồi." Cuối chuyện: "Cảm giác không thuộc về nhóm nào là có thật. Nhiều bạn năm nhất cũng thấy vậy trong vài tháng đầu. Một việc nhỏ có ích: hỏi người ngồi cạnh trong lớp một câu về bài tập, chỉ một câu."
- Bản người đi làm: "Một người mới vào công ty ba tuần. Giờ nghỉ trưa, cả phòng ra ngoài ăn theo nhóm quen. Chị ăn cơm hộp ở bàn và lướt điện thoại." Cuối chuyện: "Ở chỗ làm mới, cảm giác đứng ngoài thường kéo dài vài tuần. Một việc nhỏ có ích: hỏi một đồng nghiệp chỗ mua đồ ăn trưa gần đây."
- Bản người lớn tuổi: "Một bác về hưu được nửa năm. Sáng dậy vẫn quen giờ đi làm, nhưng không còn chỗ phải tới. Con cái gọi điện cuối tuần, nói vài câu rồi bận." Cuối chuyện: "Thấy trống sau khi nghỉ hưu là chuyện nhiều người gặp. Một việc nhỏ có ích: ra công viên đầu ngõ vào giờ mọi người tập buổi sáng, chỉ đứng xem cũng được."
- Không có câu "rồi sẽ ổn thôi", không có nút chia sẻ cảm xúc.

**B2. Chuyện vui chọn kết thúc.** Trên Trang chủ có thêm lối "Chơi một chút". Màn đầu: "Đọc chuyện, chọn một kết thúc. Mỗi lần khoảng 1 phút." Có 4 chuyện, bối cảnh hợp cả sinh viên lẫn người đi làm, không có chữ tiếng Anh. Ví dụ:
- Chuyện: "Cả nhà hẹn tối nay đi ăn. Hỏi ăn gì, ai cũng nói: 'Gì cũng được.'"
- Ba kết thúc: "Bàn 40 phút, cuối cùng vẫn ra quán quen đầu ngõ." / "Mỗi người viết một món ra giấy rồi bốc thăm, trúng đúng món không ai viết." / "Gọi đồ về nhà, ăn xong mới nhận ra là chưa ai đói."
- Chọn xong thấy một dòng vui ngắn. Không chấm điểm, không xếp hạng, không lưu đáp án hay lịch sử chơi. Nút "Chuyện khác" và "Dừng" luôn hiện. Không có chuỗi ngày chơi.
