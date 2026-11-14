# Bản A: gói concept mới, mô tả bằng chữ (bản 7.1: bản 6 + Lá nhây + Học theo bạn + 5 điểm sửa sau lượt chấm 1000)

Bản A **thêm vào** app ở bản đối chứng (kế hoạch 6 tuần, mốc B), và **thay** một số phần như bảng dưới. Mọi câu là ví dụ chưa duyệt. Mọi người trong mock là hư cấu. App dành cho người từ 18 tuổi. "[Nút]" là nút bấm.

| Concept | Quan hệ với bản đối chứng |
|---|---|
| S1 Gánh hôm nay | **Thay** lối "Gỡ một chuyện" |
| S3 Tuần có mạch | **Thêm** tab "Tuần này" |
| S4 Truyện ngắn | **Thay** 4 chuyện minh họa |
| S5 Mở lá chọn góc | **Chồng lên** "Đổi góc đọc": cùng các góc, chỉ đổi cách trình bày trên Trang chủ |
| S6 Phụ đề khác nhau | **Thêm** vào mục Chơi |
| S7 Lá ngồi cùng | **Thêm** vào việc nhỏ |
| S8 Lá Dám | **Thêm** vào mục Chơi |
| S9 Ví mỏng, lời mở có lối lui | **Thêm** góc "Tiền bạc" (cần owner duyệt) và mục "Lời mở"; **thay** 1 trong 4 chuyện vui bằng chuyện tiền |
| S10 Ảnh đúng mình | **Thêm** |
| LN Lá nhây | **Thay** nút chọn giọng "Thẳng & dễ hiểu / Cà khịa"; note và Tarot chỉ còn một giọng |
| H Học theo bạn | **Thêm** mục Học trong Khám phá và một dòng dẫn từ ba lô |
| S13 Lá số không cần giờ sinh | **Thay** câu dự phòng "theo vòng xoay" cho người chỉ nhập ngày sinh hoặc giờ khoảng |
| S2 Kể ra rồi thả | **Thử có điều kiện**, không tính vào điểm bản A (chỉ mở khi lớp an toàn chạy trên máy được kiểm riêng) |
| S11 Nhớ 7 ngày | **Thử có điều kiện**, không tính vào điểm bản A (cần owner duyệt lưu trữ) |
| S12 Ghim chuyện đang lo | **Thử có điều kiện**, không tính vào điểm bản A (cần owner duyệt lưu trữ) |

**Trang chủ gọn.** Màn đầu chỉ có 3 khối, không thêm khối nào khác, từ trên xuống: (1) Lá pixel và một câu ngắn của Lá theo mood, kèm nút nhỏ [Lá yên chút] (xem LN); (2) thẻ "Hôm nay bạn đang gánh gì?" (S1); (3) note hôm nay thu gọn (tiêu đề và một dòng, bấm để mở) với ba lá chọn góc ngay dưới (S5). "Tuần này", "Chơi" và "Lời mở" nằm ở thanh dưới. Thanh dưới: Hôm nay · Tuần này · Tarot · Chơi · Lời mở. Ba lối của bản đối chứng vẫn còn đủ, số chạm: **Nghỉ** = chạm lá Nghỉ, mở thẳng phần nghỉ (chỉ đọc, thở, không giao việc), 1 chạm; **Gỡ** = thẻ ba lô, 1 chạm để mở; **Tarot** = thanh dưới, 1 chạm.

**Dữ liệu trong lúc mở.** Món trong ba lô, mức nặng, điều muốn, mùa và ngày đầu tuần chỉ được xử lý trên máy trong lúc mở; không lưu, không gửi lên máy chủ, không vào nhật ký, báo lỗi, đường link, bộ nhớ đệm hay ảnh.

**Che nhanh.** Ở mọi màn có chuyện riêng (ba lô, lời mở, ô viết) có nút [Che nhanh]: màn hình chuyển ngay về một trang trung tính, chữ đang chọn hoặc đang viết bị xóa.

Giao diện: chữ để đọc giữ font hiện tại, phóng to được. Pixel chỉ ở Lá, hình việc nhỏ, thẻ chia sẻ, trò chơi, sticker. Hoạt hình chỉ chạy khi người dùng bấm; ai tắt chuyển động thì thấy hình đứng yên. Không có điểm, chuỗi ngày, thông báo đẩy, chat, bảng tin, thưởng vì mời bạn. Không chỗ nào hỏi ngày sinh của người khác.

**Ảnh để lưu hoặc gửi:** mặc định chỉ có nội dung chung (chương tuần, câu của Lá, hình pixel). Dòng nào nói về hoàn cảnh riêng thì người dùng phải tự bật từng dòng, xem trước rồi mới lưu. Ảnh đã lưu thì Lá không thu hồi được.

---

## S1. Gánh hôm nay (kể bằng nút)

Không lưu gì; lựa chọn chỉ sống trong lần mở đó.

1. **Trang chủ**: thẻ "Hôm nay bạn đang gánh gì?", hình ba lô pixel. [Mở ba lô] [Để sau]. Ở đầu mọi bước của S1 có một dòng cố định, dễ thấy: "Nếu bạn đang nghĩ tới việc làm hại mình: [xem thông tin hỗ trợ]" (câu và nội dung theo bản owner đã duyệt).
2. **Chọn món** (1–3): Đồ án, bài tập lớn · Thi · Tìm việc, phỏng vấn · Tiền: thiếu học phí hoặc tiền nhà · Tiền: cuối tháng cạn · Tiền: phải gửi về nhà hoặc đang nợ · Nhà: bố mẹ kỳ vọng · Nhà: về quê hay ở lại · Nhà: trong nhà đang căng · Nhà: có chuyện chưa dám nói · Việc làm thêm chen giờ học · Ca làm · Một người làm mình nghĩ nhiều · Phòng trọ, bạn cùng phòng · Sếp, chỗ làm · Chăm người nhà · Cơ thể mệt · So mình với người khác · Không gọi tên được. Màn đầu chỉ hiện 6 món hay gặp và [Không gọi tên được]; các món khác sau nút [Thêm món]. Chọn xong, món chỉ còn là hình nhỏ trong ba lô, không hiện chữ.
3. **Nặng cỡ nào?** Nhẹ / Nặng / Nặng quá.
4. **Lúc này bạn muốn gì?** [Chỉ cần được nghe] [Một bước đầu] [Được phép nghỉ]
5. **Lá đáp, chỉ dùng đúng những gì bạn chọn** (ví dụ: Đồ án + Tiền: cuối tháng cạn, Nặng, Một bước đầu):
   > "Đồ án và tiền cuối tháng cùng một lúc. Bạn chọn mức Nặng, vậy thì mệt là đúng, không phải do bạn yếu."
   > Chọn một: **Bước đầu thật:** mở file đồ án, chỉ đặt tên các mục (10 phút) · **Bản nhẹ:** viết một câu hỏi để hỏi nhóm.
   > [Ngồi cùng Lá] [Đổi việc khác] [Không đúng chuyện của mình] [Để sau]
   "Chỉ cần được nghe": Lá chỉ nói câu công nhận, không giao việc, rồi kết thúc. Dưới cùng có một nút nhỏ [Muốn nhờ ai đó nghe]; chỉ khi người dùng tự bấm mới mở sticker "Nghe thôi, không cần khuyên" và câu mẫu, kèm "Không có ai lúc này cũng không sao." Sticker không chứa món trong ba lô. Bấm gửi thì mở bảng chia sẻ của điện thoại; Lá không biết gửi cho ai. "Được phép nghỉ": mở phần nghỉ, không giao việc.
   **Câu mẫu đi kèm khi hợp**: món "Ca làm" → câu xin trưởng ca đổi ca; "Việc làm thêm chen giờ học" → câu xin chủ quán bớt một tối trong mùa thi; "Tiền: thiếu học phí" → câu hỏi phòng công tác sinh viên về gia hạn hoặc trả góp học phí; "Nhà: bố mẹ kỳ vọng" → câu nói với bố mẹ về áp lực điểm (có lối lui nếu nói với nhà không an toàn); "Một người làm mình nghĩ nhiều" → câu xin thêm thời gian trả lời. [Chép]
   **Lần sau mở ba lô**: món đã chọn lần trước **không** được nhớ.
   **Bài 3 phút cho đúng chuyện này**: khi chọn [Một bước đầu], có thêm dòng [Xem bài] (xem H).
6. **Dòng nói thật** cuối thẻ: "Lá đáp theo những nút bạn vừa chọn. Lá không đoán thêm và không giữ lại."
7. **Ảnh "Hóa đơn hôm nay" (tùy chọn)**: mặc định chỉ có "HÓA ĐƠN HÔM NAY · Đã gánh: vài thứ · Ghi chú: được phép ăn tối tử tế". Muốn hiện tên món (ví dụ "Đồ án ..... nặng") thì tự bật từng dòng. Dòng "đã làm" chỉ hiện khi bạn tự bấm [Mình đã làm]. Xem trước rồi mới [Lưu ảnh].

---

## S3. Tuần có mạch, ngày có cảnh (chế độ tuần)

1. **Tab "Tuần này"** cạnh "Hôm nay". Bản đồ 7 ô pixel bắt đầu từ ngày bạn chọn. Ô có thể có: rằm hoặc mùng 1 âm lịch, pha trăng, ngày lễ (ví dụ 20/11), mùa bạn tự chọn.
   > Chương tuần: **"Chậm lại cho kịp"**. Một câu: "Tuần này không cần làm hết. Nếu muốn, chọn một hai việc quan trọng, còn lại để sau."
2. **Tuần theo lịch chung**, từ thứ Hai tới Chủ nhật, để lần sau mở vẫn nối đúng ngày mà không cần nhớ gì. Người làm ca bấm [Xem theo tuần ca của mình] để xếp lại 7 ô bắt đầu từ ngày đi ca đầu tiên, chỉ trong lần mở này. Lá không mặc định ngày nào là ngày nặng.
3. **Mùa của bạn (tùy chọn)**: Mùa thi · Nộp đồ án · Tìm việc · Chuyện tiền · Xa nhà · Làm ca · Không chọn. Bản đầu: chỉ dùng trong lần mở đó.
4. **Note ngày** có dòng nhỏ "Thứ Tư, chương *Chậm lại cho kịp*". Mood ngày quyết độ nhẹ: ví dụ mood Mệt thì "Hôm nay chỉ cần một việc nhẹ, hoặc không việc nào." Ngày không bao giờ nói ngược hướng tuần.
5. **Trăng và lễ chỉ là bối cảnh**: "Rằm: trăng sáng nhất tháng. Tối nay thử nhìn lên một phút." Không báo điềm, không ngày tốt xấu.
6. **Chủ nhật**: "Thư cho tuần tới" do Lá viết sẵn, mở được ngay. Không nhắc nhở.
7. **Vắng mấy ngày**: Lá không bắt đọc bù: "Hôm nay thứ Sáu. Các ngày trước trong tuần vẫn ở đây nếu bạn muốn."

---

## S4. Truyện ngắn "nhiều người nhận ra mình" (3 khung, hữu hạn)

1. **Trong tab Tuần này**: "Truyện ngắn hư cấu, 3 khung." Trước truyện, chọn: [Có người để nhờ] [Tự làm một mình] [Tìm chỗ hỗ trợ khác]. Mỗi lựa chọn mở một bản truyện. Mỗi bản có bốn phiên bản nhân vật: sinh viên năm nhất (Khoa, mới lên thành phố), sinh viên năm ba (Vy, ở trọ), người đi làm (Hùng, làm ca ở xưởng) và người lớn tuổi hơn (cô Lan, 52 tuổi, bán hàng); người dùng tự chọn. Tên chủ đề của truyện hiện trước khi mở.
2. **Bản "Tự làm một mình"**: Vy pixel nhìn tin nhắn nhóm "ai làm slide?", không ai trả lời. Tiền trọ tăng; Vy mở app ngân hàng rồi tắt. Vy chia phần của mình thành ba phần nhỏ, làm phần đầu, rồi đi ngủ.
3. **Bản "Có người để nhờ"**: Vy nhắn riêng một bạn: "Mình hơi quá tải, bạn nhận phần 2 được không? Không được cũng không sao." Có hai kết: bạn ấy nhận, **hoặc** bạn ấy bận; Vy vẫn ổn với câu trả lời đó và làm phần nhỏ nhất.
4. **Bản "Tìm chỗ hỗ trợ khác"**: Vy hỏi phòng công tác sinh viên về gia hạn học phí; câu trả lời chưa chắc, nhưng Vy biết bước tiếp theo.
5. **Cuối truyện**: "Nhiều bạn cũng im lặng khi vừa thiếu tiền vừa thiếu sức." Một việc nhỏ hợp với bản đã chọn. [Bỏ qua]. Không câu "rồi sẽ ổn", không cảnh cả nhà sum họp.
6. [Mình cũng vậy] chỉ đổi màu chiếc lá, không gửi đi, không đếm. [Lưu một khung] làm ảnh, không có gì của người dùng.

---

## S5. Mở lá chọn góc

1. **Trang chủ**: ba lá úp pixel, lưng mỗi lá ghi rõ góc kèm hình: Nghỉ (vầng trăng) · Người (hai bàn tay) · Việc (cây bút). "Hôm nay bạn muốn đọc về gì?" Ba góc này là ba nhóm của "Đổi góc đọc".
2. **Chạm một lá** → lá lật (một lượt). Lá Người và lá Việc mở thẳng note theo góc đó. Lá Nghỉ mở thẳng phần nghỉ, không có việc, vẫn trong chương tuần.
3. Dưới note có một dòng lý do lấy từ lá số của chính người dùng (xem S13), ví dụ "Hôm nay Sao Kim chạm Mặt Trời trong lá số của bạn, nên lá Người có thêm một câu về người quanh bạn." "Bạn chọn góc, Lá không đoán tương lai." [Đổi lá]
4. **Ảnh "Lá hôm nay"** (tùy chọn): mặc định "Hôm nay mình chọn lá Người." Muốn thêm một câu thì tự chọn trong 3 câu mẫu. Không link, không thông tin cá nhân.

---

## S6. Phụ đề khác nhau (hai người, chuyền một máy)

1. **Mục Chơi** → "Phụ đề khác nhau: hai người, một máy, 3 phút".
2. **Cảnh pixel hư cấu**: một con mèo ngồi trước laptop lúc 2 giờ sáng.
3. **Người 1** chọn phụ đề: "Deadline lúc 8 giờ" / "Đang chờ người ấy nhắn lại" / "Chỉ là không ngủ được". Màn hình **tự che** trước khi chuyền máy (kể cả khi bấm quay lại). **Người 2** chọn.
4. **Lật**: hai phụ đề cạnh nhau. "Cùng một cảnh, hai bạn thấy hai chuyện. Muốn kể cho nhau vì sao không? Không kể cũng được."
5. 5 cảnh mỗi ván, dừng lúc nào cũng được. Không điểm "hiểu nhau", không lưu đáp án.
6. **Lưu ảnh kết quả**: mỗi người bấm riêng khi máy ở tay mình; chỉ cần một người không đồng ý thì không có ảnh, và không hiện ai không đồng ý.

---

## S7. Lá ngồi cùng (hoạt hình pixel cho việc nhỏ)

1. **Mỗi việc nhỏ** có hình Lá pixel đứng yên theo 6 nhóm: nghỉ, cơ thể, học/việc, tiền, ranh giới, kết nối. Hình đứng yên đủ nghĩa.
2. **[Ngồi cùng Lá]**: chọn 3 / 10 / 25 phút. Lá pixel làm cùng việc (mở laptop, gõ, uống nước). Đèn bàn, mưa ngoài cửa sổ. [Tạm dừng] [Xong sớm] luôn hiện. Âm thanh tắt sẵn.
3. **Hết giờ**: Lá vươn vai một lần. "Xong 10 phút. Thêm 10 phút hay nghỉ?" Không điểm, không đếm.
4. **[Xong]**: Lá đặt một chiếc lá vào hũ (một lượt, 1 giây).
5. **Ngày mood Mệt**: chỉ một câu, kèm "Không cần nhìn màn hình: đặt máy xuống, thở ra chậm ba lần." và nút [Thở cùng Lá] (bấm mới chạy, 4 giây mỗi nhịp, [Dừng] luôn hiện), [Đóng].

---

## S8. Lá Dám (Thật hay Dám, chuyền một máy, 18+)

1. **Mục Chơi** → "Lá Dám: chơi cùng hội, chuyền một máy". Trước khi vào: "Ai cũng bấm Miễn được ở mọi lượt, không cần lý do. Lá không lưu câu trả lời hay tên ai. Đừng quay hay chụp người khác khi chưa hỏi."
2. **Tuổi**: "Cả hội đều từ 18 tuổi trở lên?" [Đúng] [Không]. Không → "Lá Dám hiện chỉ dành cho hội từ 18 tuổi."
3. **Rào trước ván**: mỗi người lần lượt tắt chủ đề không muốn gặp, màn hình tự che trước khi chuyền: Người yêu cũ · Gia đình · Tiền · Ngoại hình · Học hành, công việc. Ngoại hình tắt sẵn.
4. **Chọn bộ**: Nhẹ · Thật lòng · Hài. Không có câu tình dục, thử thách thân thể, đồ ăn uống, tiền, đăng mạng, nhắn cho người không có mặt. Không thẻ nào chỉ đích danh một người đang ngồi đó.
5. **Lượt chơi**: thẻ pixel lật. Ví dụ Thật: "Kể một điều nhỏ làm bạn vui tuần này." Thật lòng: "Một việc bạn đang cố mà ít ai thấy?" Dám: "Đọc một câu tử vi vui cho con mèo trong tranh, bằng giọng phát thanh viên." Dám: "Nói một câu cảm ơn tới bất kỳ ai bạn muốn, có mặt hay không, hoặc tới chính mình." [Xong] [Miễn] [Đổi thẻ]. Miễn trông giống hệt Xong với những người khác.
6. **Hết ván** (lúc nào cũng được): ảnh 9:16 pixel "Tối nay hội mình đã lật 10 lá. Danh hiệu: Hội phát thanh viên mèo." Không tên ai, không đếm Miễn. Mỗi người tự bấm đồng ý khi máy ở tay mình; một người không đồng ý là không có ảnh, không hiện ai.

---

## S9. Chuyện tiền và lời mở có lối lui

1. **Góc đọc "Tiền bạc"** (cần owner duyệt): không hỏi số tiền, không giả định lúc nào thiếu. Chọn góc này thì chọn thêm một trong bốn chuyện: thiếu học phí hoặc tiền nhà · cuối tháng cạn · phải gửi tiền về nhà · bị rủ đi chơi tốn tiền. Ví dụ "thiếu học phí": note "Hạn học phí tới mà chưa đủ. Chuyện này làm nhiều bạn mất ngủ mà không nói với ai." Việc nhỏ: "Tìm trên trang trường mục gia hạn hoặc miễn giảm học phí, chỉ đọc, chưa cần nộp gì." Ví dụ "bị rủ đi chơi": "Chọn trước một câu từ chối nhẹ."
2. **Chuyện vui chọn kết thúc về tiền**: "Cả nhóm rủ đi lẩu." Ba kết thúc, không cái nào chê người muốn giữ tiền. **Mọi chuyện vui và truyện ngắn hiện tên chủ đề trước khi mở, và không được đưa ra nếu trùng với điều người dùng vừa chọn là đang nặng trong lần mở này** (đang chọn chuyện nhà hoặc nhớ nhà thì không gặp chuyện cả nhà đi ăn; đang chọn tiền hoặc so mình với người khác thì không gặp chuyện cả nhóm rủ đi lẩu).
3. **Lời mở có lối lui**: chọn tình huống → câu mẫu → [Chép] rồi tự dán vào Zalo/Messenger. Ví dụ "Nhờ được nghe, chưa cần khuyên": "Mình muốn kể một chuyện, bạn chỉ cần nghe thôi. Bận thì để hôm khác nhé." Có: từ chối đi chơi vì muốn giữ tiền, nhờ một việc cụ thể, hỏi thăm bạn đang im lặng, xin nghỉ ca vì mệt, nói với bố mẹ về áp lực điểm.
4. **Không có ai để nhắn**: mục này có lối "Không có ai để gửi lúc này" → gợi ý chỗ hỗ trợ không cần quen biết, theo hoàn cảnh người dùng chọn: sinh viên (phòng công tác sinh viên, tư vấn tâm lý của trường nếu có); người đi làm (bộ phận nhân sự, công đoàn nếu có); ai cũng dùng được (thông tin hỗ trợ owner đã duyệt) và câu: "Không có ai để nhắn lúc này cũng là chuyện nhiều người gặp."
5. **Lối lui cho chuyện nhà**: "Nếu nói chuyện với nhà không an toàn với bạn, bỏ qua mục này." Lá không mặc định gia đình là chỗ dựa.

---

## S10. Ảnh "đúng mình" (sticker và thẻ tuần)

1. **Bộ sticker pixel** để gửi bạn (hiện ở ba chỗ: sau khi xong một việc, trong mục Chơi, và khi chạm Lá; xem LN): "Quầy hết hàng hôm nay", "Đi cà phê không, mình hơi đuối", "Ổn không đó?", "Nghe thôi, không cần khuyên", "Đang sạc, gọi lại sau". [Lưu ảnh]. Lá không tự gắn mood của bạn vào sticker.
2. **Thẻ tuần** (Chủ nhật): mặc định có chương tuần và hình pixel. Tự bật thêm nếu muốn: một khung truyện, một câu cho tuần sau (chọn trong 3 câu). Không số, không mood, không ngày sinh.
3. **Hình nền tuần**: ảnh pixel màn hình khóa theo chương tuần. Quà phụ, không nhắc.

---

## LN. Lá nhây (Lá pixel thay nút chọn giọng)

Không còn nút "Giọng của Lá". Note và Tarot chỉ có một giọng rõ, đời thường. Lá là hình pixel của chính chiếc Lá tím hiện có trong app, tự đổi dáng và câu nói theo lúc. Không lưu gì.

1. **Trang chủ, khối đầu**: Lá pixel (bấm được) + một câu của Lá + nút nhỏ [Lá yên chút]. Chưa chọn mood: Lá vẫy tay, câu trung tính "Chào bạn. Note hôm nay Lá để sẵn rồi." Câu của Lá không bao giờ ra lệnh (không có "đọc đi", "làm đi").
   **Lá diễn hôm nay**: mỗi ngày nhiều nhất một lần, khi mood ổn, vui hoặc chưa chọn, câu của Lá là một lời mời: "Hôm nay Lá diễn một chiêu 3 phút: 'Hỏi tiếp một câu'. [Xem Lá diễn]". Bấm thì mở bài học (xem H). Không bấm thì thôi, Lá không nhắc lại. Không hiện khi mood thấp.
2. **Mood ổn hoặc vui**: nhiều nhất 1 trong 3 lần, Lá tự làm hỏng việc của chính mình cho vui: đeo kính đen thì kính rơi ("Lá đeo kính cho ngầu, kính tự rơi. Thôi kệ kính."), thổi trà thì bỏng lưỡi, giơ bảng bị ngược, ăn mừng thì vấp. Lá không bao giờ đùa về việc người dùng làm: đọc nhanh hay chậm, bỏ việc, bấm "để mai", vắng mấy ngày, mở app lúc khuya; không đùa ngoại hình, tiền, điểm số, chuyện độc thân, gia đình.
3. **Xong một việc**: Lá xoay vòng tung giấy màu, "Xong một việc! Lá tung giấy màu, dọn thì để Lá." Không đếm chuỗi ngày. Ngay dưới có [Gửi một sticker cho bạn] (xem mục 6).
4. **Bấm "để mai"**: Lá cất việc vào ba lô, "Mai tính. Việc này mai vẫn còn đó." Không lườm, không đếm.
5. **Mood thấp, chọn "Chỉ cần được nghe", đang ở phần hỗ trợ, đang Che nhanh, lá Tarot nặng, chuyện mất mát hay bị từ chối**: Lá không nhây. Lá ngồi cạnh một chiếc lá nhỏ, vỗ vai, "Hôm nay nặng ha. Lá ngồi đây với bạn, không cần nói gì." App lỗi: Lá héo, tự nhận lỗi "Lá làm rớt mất rồi, lỗi của Lá."
6. **Chạm Lá để chơi** (người dùng tự chạm): Lá đổi dáng nhây: lè lưỡi, nhếch mép, lườm, hóng chuyện bên tách trà. **24 sticker Lá** ("Nghe thôi, không cần khuyên", "Ừ rồi sao", "Đang hóng", "Hôm nay héo", "Đang sạc, đừng nhắn", "Kính rơi rồi", "Xong rồi, ghê chưa", "Cố lên") nằm ở ba chỗ: sau khi xong một việc, trong mục Chơi, và khi chạm Lá. [Lưu ảnh] rồi tự gửi qua Zalo/Messenger. Sticker không có mood, cung hay tên người dùng.
7. **[Lá yên chút]**: tới hết ngày Lá chỉ vui hoặc trung tính, không làm trò. Không lưu.
8. Hình chỉ chuyển động khi mở màn hoặc khi chạm, tối đa vài giây rồi đứng yên; ai tắt chuyển động thì thấy hình đứng. Câu của Lá luôn là chữ thật.

---

## H. Học theo bạn (bài 3 phút, Lá diễn)

Mục "Học" nằm trong Khám phá. Trang chủ không thêm khối mới: bài học tới qua ba đường dưới đây. Không lưu tiến độ, không chuỗi ngày, bài nào cũng mở sẵn. Không có chỗ nào nhập thông tin về người khác.

0. **Vào từ Lá (LN)**: lời mời "Lá diễn hôm nay" ở khối đầu Trang chủ. Chưa mở ba lô thì bài được chọn theo chương tuần và lá số của chính người dùng, có ghi rõ đã dùng gì.
1. **Vào từ ba lô (S1)**: nếu người dùng đã chọn [Một bước đầu], ngay dưới câu công nhận của Lá (trước phần chọn việc) có một dòng: "Có bài 3 phút cho đúng chuyện này. [Xem bài]". Không hiện khi chọn [Chỉ cần được nghe] hoặc [Được phép nghỉ]. Bài theo món đã chọn:
   - Tìm việc, phỏng vấn → "Phỏng vấn đỡ run" · Đồ án, thi → "Bắt đầu việc khó bằng 10 phút"
   - Nhà: bố mẹ kỳ vọng / có chuyện chưa dám nói → "Nói điều khó với nhà" (có lối lui nếu nói với nhà không an toàn)
   - Tiền (bốn chuyện) → "Nói chuyện tiền: hỏi gia hạn, từ chối đi chơi, xin ứng lương"
   - Ca làm, việc làm thêm chen giờ học → "Xin đổi ca mà không mất lòng" · Sếp, chỗ làm → "Nói 'không' với việc thêm"
   - Về quê hay ở lại, phòng trọ, không có ai → "Kết bạn ở chỗ mới" · So mình với người khác → "Không ai soi bạn kỹ như bạn nghĩ"
   - Một người làm mình nghĩ nhiều → "Tán crush kiểu tử tế" (hỏi trước "Bạn đang ở đoạn nào?": chưa nói chuyện · nói chuyện nhạt · họ trả lời chậm, ngắn · muốn rủ gặp · vừa bị từ chối · không biết họ có thích mình không)
2. **Vào từ Khám phá**: ba khóa mở sẵn (Tán crush kiểu tử tế · Tự tin hơn · Kết bạn ở chỗ mới), năm khóa "sắp có". Mỗi khóa 7 bài.
3. **Một bài** (ví dụ "Phỏng vấn đỡ run", cho người đã chọn món Tìm việc):
   - Ý chính, 2 câu: "Run là bình thường. Người phỏng vấn nhớ câu trả lời của bạn, ít khi nhớ bạn run."
   - **Lá diễn** (hình pixel, Lá cầm micro run run): câu nên tránh "Em… em không có kinh nghiệm gì ạ." → câu nên nói "Em chưa đi làm chính thức, nhưng em đã làm đồ án nhóm 4 người và lo phần lịch."
   - **Theo thông tin của bạn** (đổi được, tắt được): Lá chọn sẵn một kiểu luyện theo lá số của chính người dùng và nói rõ đã dùng gì. Ví dụ có đủ giờ sinh: "Sao Thủy của bạn ở Kim Ngưu. Người xem chiêm tinh hay gắn vị trí này với kiểu nói chậm, chắc. Lá chọn sẵn kiểu 'viết ra 3 ý rồi nói'. [Đổi kiểu: nói thử trước gương · kể cho một người bạn]". Chỉ có ngày sinh: Lá dùng hành tinh tính đủ chắc từ ngày sinh; không đủ chắc thì không nhắc lá số và để người dùng tự chọn kiểu. Lá số không đoán kết quả phỏng vấn.
   - **Việc thử** hợp mood hôm nay: mood thấp → bản nhẹ "viết một câu giới thiệu mình, chưa cần nói ra"; mood ổn → "nói to câu đó một lần". [Làm rồi] [Ngại quá] [Chưa thử] · [Đổi việc khác] [Chưa sẵn sàng, để sau]. Bấm [Làm rồi]: Lá khoác áo choàng, "Làm được rồi đó." Bấm [Ngại quá]: Lá ngồi cùng, "Ngại là bình thường. Mai thử bản nhẹ hơn cũng được."
   - Dòng nhỏ: "Ý này lấy từ đâu, dùng được tới đâu" (tên nghiên cứu hoặc sách, và giới hạn).
4. **Khóa "Tán crush kiểu tử tế"** (18+): bài 1 là ranh giới (im lặng hay trả lời xã giao không phải lời mời tiếp; không tập với người say, người đang phục vụ mình, người lệ thuộc mình; "không" là xong). Các bài sau: không ai soi bạn kỹ như bạn nghĩ · có thể bạn đang tự chấm mình quá khắt khe · hỏi tiếp một câu · kể về mình từng nấc · mở lời bằng thứ trước mắt · rủ một việc có lối lui và khi họ nói không. Không dạy chê khéo, gây ghen, theo dõi, "cưa lại". Không xem hợp hay không hợp với người kia.
5. **Thẻ "Bạn đáp câu nào?"** (2 ảnh pixel để gửi bạn): ảnh 1 là tình huống và hai câu đáp A, B; ảnh 2 là lời giải, có Lá diễn. Ảnh không có gì của người dùng và không nói người gửi đang học khóa nào. [Lưu 2 ảnh] rồi tự gửi.
6. **Vừa bị từ chối và thấy rất tệ**: bài chuyển sang "Chỉ cần được nghe" (S1), không giao việc.
7. **Dữ liệu**: món trong ba lô, đoạn đang vướng, kiểu luyện và nút tự chấm chỉ dùng trong lần mở, không lưu, không gửi đi. Lá số dùng ở đây là của chính người dùng, đã có sẵn trong app.

---

## S13. Lá số không cần giờ sinh

Không thu thêm gì; chỉ đổi cách tính và câu chữ.

1. **Người chỉ nhập ngày sinh hoặc giờ khoảng**: Lá tính vị trí các hành tinh trong **cả khoảng giờ có thể sinh** (cả ngày nếu chỉ có ngày; theo múi giờ nơi sinh, thiếu nơi sinh thì mở rộng khoảng). Lá chỉ dùng phần **đủ chắc trong toàn khoảng đó**: thường là Mặt Trời, Sao Thủy, Sao Kim, Sao Hỏa, Sao Mộc, Sao Thổ; Mặt Trăng đi khoảng 13 độ một ngày nên chỉ dùng khi cả khoảng giờ vẫn cùng một cung. Lá không đọc nhà và cung Mọc (cần cả giờ và nơi sinh chính xác).
2. **Lý do của note** lấy từ góc chiếu hôm nay tới các hành tinh đó, nói rõ góc gì: "Hôm nay Sao Hỏa tạo góc vuông với Sao Thủy trong lá số của bạn." Tách rõ phần tính và phần đọc: "Theo chiêm tinh, góc này hay được đọc là ngày dễ nói nhanh hơn nghĩ. Đây là một cách nhìn, không phải nguyên nhân." Kèm: "Không có giờ sinh nên Lá không đọc nhà và cung Mọc." Lý do luôn khớp đúng nội dung note đang hiện.
3. **Khi không có góc chiếu nào đủ chắc**: "Hôm nay Lá không tìm được góc chiếu đủ chắc trong lá số của bạn để chọn bài, nên Lá chọn chuyện theo vòng xoay."
4. Lời mời nhập giờ sinh chỉ là một dòng, không chặn gì: "Có giờ sinh thì Lá đọc thêm được nhà và cung Mọc."

---

## Thử có điều kiện (chấm riêng, không cộng vào điểm bản A)

### S2. Kể ra rồi thả (ô viết tự do)

1. **Lối vào** trong S1: "Muốn tự viết ra cho nhẹ? Chữ được kiểm tự động ngay trên máy để tìm dấu hiệu nguy hiểm. Không ai đọc, không lưu, không gửi đi." [Viết ra]
2. **Ô viết**: tờ giấy pixel. Trên ô luôn có: "Nếu bạn đang nghĩ tới việc làm hại mình: [xem thông tin hỗ trợ]". Nút [Che nhanh] (xóa ngay, không khôi phục) luôn hiện. Đóng app là chữ mất.
3. **Bấm [Thả]**: nếu chữ có dấu hiệu tự hại → không hoạt hình, hiện thông tin hỗ trợ theo bản owner duyệt; vẫn có [Xóa chữ] và [Đóng], không bắt giữ nội dung.
4. **Thả**: chữ vỡ thành lá pixel bay đi (1,5 giây; ai tắt chuyển động thì chữ xóa ngay).
5. **Sau khi thả**: "Đã thả. Nói ra được một chuyện khó cũng là một việc." [Chọn bằng nút điều đang nặng] (về S1) · [Nghỉ một chút] · [Đóng].

### S11. Lá nhớ 7 ngày trên máy (tắt sẵn)

1. **Lời mời bật** sau lần dùng thứ 3, chỉ một lần: "Cho Lá nhớ 7 ngày gần nhất trên máy này để không hỏi lại? Không gửi đi đâu. Người cầm máy này có thể thấy. [Bật] [Không, cảm ơn]"
2. **Khi bật**: Lá nhớ mood, món trong ba lô, góc đã chọn, việc đã giữ của 7 ngày. Note có dòng: "Tuần này bạn mở ba lô ba lần, món đồ án hay nặng nhất. Lá giữ việc nhẹ."
3. **Máy dùng chung**: Trang chủ không hiện chi tiết. [Xóa hết] luôn ở đó. Tắt là xóa ngay.

### S12. Ghim chuyện đang lo (tắt sẵn)

1. **Trong S1**, sau khi chọn món: [Ghim món này tới khi mình bỏ]. Tối đa 2 món. Trước khi ghim: "Món ghim nằm trên máy này tới khi bạn bỏ. Người cầm máy này có thể thấy nếu mở ba lô. [Ghim] [Thôi]" Che nhanh không xóa ghim; [Bỏ ghim] mới xóa.
2. **Khi đã ghim**: Trang chủ chỉ hiện "Ba lô có 1 món đang ghim", không hiện tên món, cho tới khi bấm. Note ngày, chương tuần và việc nhỏ chọn theo món ghim, ví dụ món "Tìm việc": "Đang trong đợt tìm việc. Hôm nay chỉ cần sửa một dòng trong CV."
3. Lần sau mở ba lô, món ghim đã có sẵn, không phải chọn lại.
4. [Bỏ ghim] luôn ở đó; bỏ là xóa ngay. Không ghim gì về mood, Tarot hay chữ tự viết.

