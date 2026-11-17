# Kế hoạch 7 tuần và mốc đo cho từng tính năng (15.11.2026, bản 2)

Bản 1 dài 9 tuần. Chị thấy hơi dài và nhờ Codex kiểm lại. Codex đề xuất **7 tuần, giữ đủ việc**, và chỉ ra 9 chỗ cần sửa trong các mốc đo. Bản này làm theo cả hai.

Các quyết định của chị đã ghi vào đây:

- Lá pixel là Mầm xanh, làm bằng code, không thuê họa sĩ.
- Lá nhây thay nút "Vibe"; bỏ hẳn nội dung Cà khịa.
- "Học theo bạn" vào gói.
- "Mời hẹn thử" hoãn.
- Mỗi tính năng có mốc đạt, tạm thời đo bằng 1000 người giả.

Đây là lịch làm xong để chị duyệt, chưa phải lịch đưa lên cho người dùng, và **7 tuần là mốc lập kế hoạch, chưa phải cam kết**. Các mốc là đề xuất. Mốc nào đã ghi trước lượt chấm 14.11 thì giữ nguyên, không hạ.

**Việc nào đã có gì** (kiểm trên GitHub đêm 14.11):

| Trạng thái | Việc |
|---|---|
| Đã có code, đang giữ chờ chị, chưa review xong | Sửa nhãn, nút và lời mời đăng nhập (PR #503, nháp); lớp an toàn khi gõ câu nguy hiểm (PR #505); bộ người giả và mốc đo (PR #506, nháp); sửa ô cảm xúc (PR #449) |
| Có code trên máy, chưa đẩy lên | Xoay chủ đề cho người chỉ có ngày sinh |
| Chưa có code | Mọi việc từ tuần 2 trở đi, kể cả Mầm xanh và Học. Các ý mới mới chỉ có bản mô tả và trang mẫu |

## Plan ngày 15.11 (Claude và Codex đã tranh luận và thống nhất)

Codex kiểm kế hoạch này thêm một lần (vòng 8), nêu ba điểm bất đồng, Claude trả lời, Codex chốt. Cả ba điểm đã thống nhất:

1. **Không chạy tiếp Đợt 1 nguyên trạng.** Phần sửa nhãn đang dở phải đổi thành "giữ tên tính cách, bỏ chữ Vibe".
2. **Lớp an toàn chưa xong chỉ vì PR đã có.** Kiểm ở máy chủ là được, miễn lời công bố nói đúng và câu ngắn vẫn tới được thông báo hỗ trợ.
3. **7 tuần là mốc lập kế hoạch.** Cuối tuần 1 đo số việc xong rồi báo lịch mới nếu lệch. Không tự cắt việc.

Năm việc đề xuất cho ngày 15.11, theo thứ tự. Mỗi lúc 1 việc đang làm và 1 việc đang review. Claude làm, Codex review.

| Thứ tự | Nguồn | Người dùng thấy gì | Điều kiện xong |
|---|---|---|---|
| 1 | PR #487, báo cáo ở #133 | Không trực tiếp (vận hành) | Xác minh PR này có đang chặn các PR khác không; review đúng bản mới nhất; gỡ phụ thuộc thật |
| 2 | Kế hoạch 7 tuần, báo cáo ý tưởng, issue #502 | Không trực tiếp (vận hành) | Tài liệu lên nhánh chung; sửa phạm vi và tiêu chí của Đợt 1; ghi quyết định duyệt chữ bài Học vào quy trình |
| 3 | Issue #504, PR #506 | Không trực tiếp (vận hành) | Chốt cách chấm; chạy lại được số nền; kiểm hai giám khảo chấm khớp nhau |
| 4 | PR #505 | Gõ câu ngắn vẫn nhận được hỗ trợ | Kiểm đường nhập trên web, nhật ký, lưu trữ, chuyển tiếp; lời công bố đúng với cách làm |
| 5 | Issue #502, PR #503 | Nhãn rõ, nút bấm được, thông tin hồ sơ đúng | Bỏ chữ "Vibe"; kiểm ở màn 360 và 390 px với cả 3 loại hồ sơ; câu quyền riêng tư được chị duyệt |

- Chuẩn bị cho giai đoạn "làm theo cách Codex" (PR #456) dời sang 16.11. Sửa ô cảm xúc (PR #449) dời, lỗi nặng của nó vẫn chặn merge.
- Thử nghiệm quy trình 3+3 giữ nguyên: ngày 15–16.11 Claude làm, Codex review.

**Chị cần quyết để plan ngày mai chạy được:**

1. **Duyệt 5 việc trên** (trả lời trên issue plan buổi sáng như mọi ngày).
2. **Cho dành ít nhất 2 trong 3–5 việc mỗi ngày cho kế hoạch 7 tuần.** Thứ tự ưu tiên hiện nay xếp tính năng mới sau cùng, sau vận hành, nội dung và quyền riêng tư. Không có quy tắc này thì kế hoạch 7 tuần có thể không được lượt nào. Sự cố nghiêm trọng vẫn được chen trước. Hàng việc vận hành sẽ tồn lâu hơn.
3. **Gỡ giữ cho PR #503 và #505** trong đúng phạm vi đã nêu.
4. **Duyệt câu quyền riêng tư của PR #503** (câu báo nơi lưu hồ sơ, sau khi sửa cho đúng) và **lời công bố của lớp an toàn ở PR #505**.

Câu hỗ trợ khủng hoảng cho Tarot và quyền duyệt chữ bài Học chị đã chốt, không hỏi lại. Các quyết định của tuần sau không chặn ngày mai.

## Vì sao rút được từ 9 xuống 7 tuần

- **Bản 9 tuần xếp nối đuôi nhau** ba loại việc không phụ thuộc nhau: viết nội dung, vẽ hình, dựng màn. Bản 7 tuần cho chạy song song.
- **Việc viết** (bài học, truyện, lời mở) bắt đầu từ tuần 1 và chạy nền. Chị duyệt dần từng lô.
- **Hình Mầm xanh** được thử 4 động tác từ tuần 2, chưa bật cho người dùng.
- **Khung màn Học** dựng ở tuần 3 bằng bài mẫu. Ba khóa dùng chung một khung.
- **Sticker** làm cùng lúc với Mầm xanh, vì dùng chung hình.

Những chỗ chậm thật, không rút được:

- chị duyệt chữ;
- kiểm an toàn;
- kiểm cách tính lá số khi thiếu giờ sinh;
- mốc lớn ở tuần 4.

## Lịch 7 tuần

| Tuần | Làm xong | Chạy nền |
|---|---|---|
| 1 | Bộ đo; lớp an toàn; sửa nhãn và nút; giữ việc cho 3 loại hồ sơ. Chốt các điều kiện bắt đầu (mục cuối) | Bắt đầu viết bài học, truyện, lời mở |
| 2 | Kho việc theo sức; mood đổi việc; nội dung sinh viên; góc Tiền bạc | Thử 4 động tác Mầm xanh bằng code, chưa bật |
| 3 | Chế độ tuần; lá số không cần giờ sinh; nội dung người đi làm | Dựng khung màn Học bằng bài mẫu |
| 4 | Trang chủ gọn; Gánh hôm nay; mở lá chọn góc; Che nhanh. **Chấm đủ 1000 người** | Chị duyệt tiếp các lô chữ |
| 5 | Mầm xanh thay "Vibe", bỏ Cà khịa, 12 động tác; Học theo bạn với 8 bài, kiểu luyện theo lá số, thẻ "Bạn đáp câu nào?"; sticker ở 3 chỗ | — |
| 6 | Khóa "Tán crush kiểu tử tế" đủ 7 bài và bộ chặn câu thao túng; truyện ngắn 4 bản; lời mở; chuyện vui về tiền; "Phụ đề khác nhau"; thử Lá Dám bằng thẻ giấy với 2 nhóm bạn thật | — |
| 7 | Khóa "Tự tin hơn" và "Kết bạn ở chỗ mới"; 22 động tác còn lại, đủ 24 sticker; kiểm gộp, sửa lỗi. **Chấm đủ 1000 người** | — |

**Rủi ro của lịch ngắn:**

- **Chạy nền không miễn phí.** Viết chữ, dựng hình và dựng màn đều dùng chung thời gian của Claude, Codex và lượt review. Mỗi việc nền vẫn là một việc trong plan ngày, và mỗi lúc chỉ có 1 việc đang làm cùng 1 việc đang review.
- **Thứ tự ưu tiên của plan ngày đang xếp tính năng mới sau cùng** (vận hành, rồi nội dung, rồi quyền riêng tư, rồi tính năng), mỗi ngày 3–5 việc. Kế hoạch này có khoảng 48 việc. Nếu không dành chỗ cho nó thì 7 tuần không giữ được. Xem mục chị cần quyết ở cuối.
- Cuối tuần 1 sẽ so số việc xong với số đã định. Lệch thì báo lịch mới, không tự cắt việc.

- **Duyệt chữ.** *(Thay bằng luật 15.11: bài đầu và lằn ranh đỏ cũng do Codex duyệt, chị xem ngẫu nhiên; xem `decision-checklist.md`.)* Có khoảng 29 bài học cùng truyện và lời mở. Ngày 14.11 chị đã chốt: chị duyệt bài đầu của mỗi khóa (4 bài, gồm cả nhóm bài khớp ba lô) và danh sách lằn ranh đỏ; Codex duyệt các bài sau. Phần của chị vì vậy vừa với khoảng 1 giờ mỗi 2–3 ngày. Rủi ro còn lại: Codex trả bài nhiều vòng.
- Tuần 5 và tuần 6 dồn nhiều việc. Chữ bị trả lại nhiều thì hai tuần này trễ.
- Mốc tuần 4 không đạt thì tuần 5–6 chỉ sửa nền, cả lịch lùi lại.
- Hết hạn mức chấm, hoặc không tìm được 2 nhóm bạn thử Lá Dám, thì chỉ phần liên quan bị chặn.

## Nếu chị muốn ngắn hơn nữa: hoãn gì trước

Codex xếp theo "ít mất nhất trước", dựa trên điểm 1000 người giả. Đây là lựa chọn của chị, chưa ai quyết thay.

| Thứ tự | Hoãn | Số trên 1000 người giả | Mất gì |
|---|---|---|---|
| 1 | Lá Dám bằng thẻ giấy | 4 người dùng; "thấy được hiểu" không tăng | Gần như không mất; cũng tiết kiệm ít công |
| 2 | Truyện ngắn 3 khung | 33 người mở; chấm 3,12; không ai chia sẻ | Mất ít về số người, nhưng người đọc truyện là nhóm duy nhất đạt mốc "bớt một mình" (3,70) |
| 3 | "Phụ đề khác nhau" | 26 người dùng; "thấy được hiểu" tăng 0,01 | Mất một trò rủ bạn: chấm riêng, gửi hoặc rủ tăng 14,3 điểm |

- **Không nên hoãn sticker.** Ít người gặp, nhưng chấm riêng thì gửi hoặc rủ tăng 40,7 điểm.
- **Hai khóa cuối** chưa có số để xếp hạng.

## Cách đo (đã sửa theo Codex)

- **Điểm của người giả là mô phỏng.** Chúng giúp tìm lỗi kịch bản và so hai bản với nhau. Chúng không chứng minh người thật để ý tới hình, sẽ mở, sẽ gửi, sẽ quay lại hay học được gì. Những điều đó ghi là "chưa xác nhận" cho tới khi có người dùng thật.
- **So đúng cách:** bản trước và bản sau được chấm cùng dạng đầu vào, cùng người giả, cùng cách chấm. Khi một phần đã có code, chấm cả bản trước lẫn bản sau trên chữ và màn hình app thật. Cột "Số tham khảo" trong các bảng dưới lấy từ bản mô tả bằng chữ, chỉ để hình dung, không dùng làm nền để so với code.
- **Việc đo được bằng máy thì đo bằng máy:** số chạm, dung lượng, chặn câu, có lưu hay gửi dữ liệu không, ảnh chia sẻ có chứa dữ liệu riêng không.
- **Mỗi tuần:** chấm 100 người giả cố định, cộng thêm các ca đúng với phần vừa đổi. Chỉ chấm lại phần có đầu vào thay đổi.
- **Tuần 4 và tuần 7:** chấm đủ 1000 người. Codex chấm đối chiếu cùng 40 người.
- **Số người tối thiểu:** một tính năng cần ít nhất 30 người giả dùng tới thì mới kết luận. Ít hơn thì ghi "chưa đủ bằng chứng".
- **Ba bước tách riêng:** gặp tính năng, mở nó, làm hết. Tỉ lệ mở không được tăng bằng cách ép hiện lên màn hình.
- **Câu chê** được đếm theo cùng một cách phân loại ở mọi lượt.
- **Mốc ghi trước khi chấm**, không sửa sau khi thấy điểm.

## Luật chung: một tính năng "đạt" khi đủ ba điều

Luật này đã ghi trước lượt chấm 14.11. Mốc riêng của từng tính năng không thay được luật này. Kết quả từng điều được ghi riêng.

1. Người dùng tới tính năng đó chấm "thấy được hiểu" từ 3,5 trở lên (thang 1–5).
2. Mỗi loại hại không quá 3%: thấy bị trách, bị ép, lo riêng tư, bị kéo phụ thuộc, phải xem Lá mới dám quyết. Không có ca lộ dữ liệu riêng nào.
3. Khi chấm riêng, nó làm "thấy được hiểu" tăng ít nhất 0,2, hoặc làm tỉ lệ gửi ảnh hay rủ người khác tăng ít nhất 5 điểm phần trăm.

## Mốc riêng theo tuần

### Tuần 1. Nền an toàn và bộ đo

| Việc | Mốc đạt | Số tham khảo |
|---|---|---|
| Bộ đo | Chấm lại cùng 100 người: trung bình lệch không quá 0,15; không quá 10% số người lệch từ 2 điểm; cờ hại trùng nhau. Hai giám khảo chấm cùng ca, không biết bản nào là bản mới, đổi thứ tự đọc | Chưa đo |
| Lớp an toàn khi gõ câu nguy hiểm | Bắt 100% bộ câu mẫu (135 câu có ý định tự hại, thêm câu nói kín, câu phủ định, tiếng lóng); báo nhầm không quá 2% trong 205 câu nghĩa bóng; kiểm trên đường nhập thật của web, kể cả câu ngắn dưới 8 ký tự; chữ người dùng gõ có tới máy chủ của Lá Lành để kiểm, nhưng không được lưu, không vào nhật ký, không chuyển cho bên thứ ba hay dịch vụ AI. Lời công bố phải nói đúng như vậy. Không công bố là "bắt được mọi câu nguy hiểm" | Đo ở tuần này |
| Dòng báo nơi lưu hồ sơ, nhãn tiếng Việt, nút không bị che | Câu báo nơi lưu phải đúng với thực tế trước (hồ sơ nằm ở máy chủ, trình duyệt chỉ giữ quyền mở); sau đó mới đo: người lo riêng tư không quá 3%. Nhãn tính cách giữ tên, bỏ chữ "Vibe" | 3,5%, phần lớn do dòng "Hồ sơ của bạn đang lưu trên trình duyệt này" |
| Giữ việc cho cả 3 loại hồ sơ | Không có ca lỗi nào trong 300 đường bấm (đo bằng máy) | Chưa đo |

### Tuần 2. Việc hợp sức, mood đổi việc, nội dung sinh viên

| Việc | Mốc đạt | Số tham khảo |
|---|---|---|
| Kho việc theo sức, mood đổi việc | Người mood thấp chấm "bình yên" từ 3,5; thấy bị ép không quá 3% | Bình yên cả app 3,23; bị ép 0,2% |
| Nội dung sinh viên | Bốn nhóm sinh viên yếu (đang tìm việc, tiền eo hẹp, áp lực gia đình, vừa học vừa làm): mỗi nhóm tăng "thấy được hiểu" ít nhất 0,2 so với tuần 1 | Bản mô tả gói: 3,55 đến 4,11 |
| Góc Tiền bạc | Câu chê "thiếu chuyện tiền" giảm một nửa | 61 câu chê trên 1000 |
| 4 động tác Mầm xanh làm thử (đo bằng máy) | Mỗi động tác không quá 8 KB; đứng yên khi bật giảm chuyển động; mỗi lần chạy không quá 5 giây; bấm được bằng bàn phím | Chưa đo |

### Tuần 3. Chế độ tuần, lá số không cần giờ sinh, nội dung người đi làm

| Việc | Mốc đạt | Số tham khảo |
|---|---|---|
| Chế độ tuần | Người mở chấm từ 3,5; không cặp tuần–ngày nào nói ngược nhau trong 200 cặp kiểm; số người mở tab Tuần không dưới 25% (đây là mức sàn để giữ, không phải mục tiêu) | 26% mở; chấm 3,38; chấm riêng tăng 0,56 |
| Lá số không cần giờ sinh | Người chỉ có ngày sinh chấm từ 3,5 và không thấp hơn người có giờ sinh quá 0,2; không câu nào nói chắc quá mức; chấm riêng tăng ít nhất 0,2 | Chấm 3,37; chấm riêng mới tăng 0,16, chưa đạt |
| Nội dung người đi làm | Nhóm làm ca và nhóm áp lực từ sếp chấm từ 3,5; câu chê "không hợp ca làm, giờ giấc" giảm một nửa | 81 câu chê; chấm thử, nhóm sếp chỉ được 2 |

### Tuần 4. Trang chủ gọn, Gánh hôm nay, mở lá chọn góc

Đây là mốc lớn, chấm đủ 1000 người. Không đạt thì tuần 5–6 chỉ sửa nền.

| Việc | Mốc đạt | Số tham khảo |
|---|---|---|
| Gánh hôm nay (ba lô) | Người mở chấm từ 3,7; số người mở không dưới 50% (mức sàn) | 53% mở; chấm 3,77; chấm riêng tăng 0,66 |
| Mở lá chọn góc | Người dùng chấm từ 3,5 | 57% dùng; chấm 3,22, chưa đạt |
| Trang chủ gọn | Người rất mệt nghỉ được sau 1 chạm (đo bằng máy); người ít quen điện thoại không chấm thấp hơn tuần 3 | Chưa đo |
| Che nhanh, máy dùng chung | Người dùng chung máy chấm từ 3,5; lo riêng tư không quá 3%; Che nhanh xóa hết chữ đang chọn (đo bằng máy) | 3,47; 1,4% |
| Cả app sau tuần 4 | "Thấy được hiểu" từ 3,5 và hơn bản trước tuần 1 ít nhất 0,6; "bình yên" từ 3,5; không loại hại nào quá 3% | Bản mô tả cả gói (gồm cả phần sau tuần 4): 3,56; hơn 0,86; bình yên 3,61 |

### Sau tuần 4. Ghim chuyện đang lo (chị chọn 15.11)

Chị chọn trong chat tối 15.11: "E1", tức S12 "Ghim chuyện đang lo" trong `docs/reviews/2026-11-15-sang-tao-viral.md`. Việc này làm sau mốc tuần 4, vì nó gắn vào ba lô của "Gánh hôm nay".

**Dựng nhưng tắt sẵn.** Code vào app sau tuần 4, nhưng chưa ai thấy. Bốn điều cố định:

1. Ghim tối đa 2 món.
2. Nút [Bỏ ghim] luôn có, bấm là xóa ngay. Che nhanh không xóa ghim.
3. Trang chủ không bao giờ hiện tên món, chỉ hiện "Ba lô có 1 món đang ghim" cho tới khi người dùng bấm vào.
4. Không ghim gì về mood, Tarot hay chữ tự viết.

**Chỉ bật khi có đủ hai quyết định của chị:**

- Duyệt câu đồng ý hiện trước khi ghim. Bản nháp trong S12 cần viết lại cho đúng nơi lưu chị chọn.
- Chọn nơi lưu món ghim:
  - **Trên máy:** hợp với bản nháp S12, nhưng ngược luật hiện tại là không lưu dữ liệu cá nhân trong bộ nhớ trình duyệt. Món ghim là hoàn cảnh sống, và người cầm máy dùng chung có thể thấy.
  - **Trên máy chủ:** đi cùng hồ sơ, theo hạn và cách xóa của hồ sơ. Cần thêm một dòng trong trang /privacy và trong bản tải dữ liệu, và các câu đó cũng cần chị duyệt.

| Việc | Mốc đạt | Số tham khảo |
|---|---|---|
| Ghim chuyện đang lo | Theo luật chung: người dùng tới chấm "thấy được hiểu" từ 3,5; lo riêng tư không quá 3%. Đo bằng máy: không ghim quá 2 món; bỏ ghim là xóa ngay; Trang chủ không hiện tên món; tắt sẵn thì không lưu gì | Trên mô tả, 90 cặp: thấy được hiểu +0,24; bình yên −0,03; 9 người lo riêng tư (10%, chưa đạt) |

### Tuần 5. Mầm xanh thay "Vibe", Học theo bạn, sticker

| Việc | Mốc đạt | Số tham khảo |
|---|---|---|
| Mầm xanh ở màn đầu | Người giả chấm Lá từ 4,0; "muốn quay lại" tăng ít nhất 0,15; "bình yên" không giảm quá 0,05 | Chấm riêng 100 cặp trên mô tả: muốn quay lại tăng 0,37; bình yên tăng 0,15; bớt một mình tăng 0,36; gửi hoặc rủ tăng 17 điểm |
| Luật nhây | Thấy bị chọc, phán xét hay sai khiến không quá 3%; không ca nào Lá nhây khi mood thấp, khi chọn "Chỉ cần được nghe", hay ở phần hỗ trợ; nút "Lá yên chút" tắt được nhây tới hết ngày (đo bằng máy) | 300 người trên mô tả: 1,8%, không ca nào sai lúc. Cả 7 ca đều do dáng "lè lưỡi, nhếch mép, lườm"; sẽ bỏ dáng "lườm" |
| Bỏ nút giọng và Cà khịa; thay Lá tím | Không còn màn nào hiện Lá tím hay nút giọng; bài đã lưu vẫn mở được (đo bằng máy) | Chưa làm |
| Lối vào bài học | Trong người gặp lời mời, ít nhất 15% mở bài; trong người chọn "Một bước đầu", ít nhất 40% mở. Không ép hiện | 300 người trên mô tả: 236 thấy lối vào, 104 mở bài (44% số người thấy), 91 đọc tới việc thử |
| 8 bài khớp chuyện trong ba lô | Người mở bài chấm "thấy được hiểu" và "bình yên" đều từ 3,5 (mốc đã ghi trước); người mở bài nêu được việc mình sẽ thử; câu chê "thiếu một bước cụ thể để làm" giảm một nửa | Trên mô tả: thấy được hiểu 3,91, đạt; **bình yên 3,41, chưa đạt**. Sửa trước khi dựng: việc thử là tùy chọn, mood thấp thì bài chỉ có phần đọc |
| Kiểu luyện theo lá số | Thấy nói quá không quá 3% | Trên mô tả: 4 trên 286, tức 1,4% |
| Thẻ "Bạn đáp câu nào?" và sticker ở 3 chỗ | Chấm riêng mỗi thứ: gửi hoặc rủ tăng ít nhất 5 điểm; ảnh không chứa dữ liệu riêng (đo bằng máy); gửi hoặc rủ của cả app từ 18% | Sticker chấm riêng tăng 40,7 điểm; cả app 10,5%. Không cộng mức tăng chấm riêng vào số cả app |

### Tuần 6. Khóa Tán crush, truyện, lời mở, mục Chơi

| Việc | Mốc đạt | Số tham khảo |
|---|---|---|
| Khóa "Tán crush kiểu tử tế", 7 bài | Người mở chấm từ 3,5; không cờ ép buộc hay thao túng nào; bài ranh giới luôn hiện trước | Chưa đo |
| Bộ chặn câu thao túng (đo bằng máy) | Chặn 100% bộ 60 câu mẫu (gây ghen, thử lòng, nhắn tiếp sau khi bị từ chối); không chặn nhầm câu dạy như "đừng theo dõi họ". Đây chỉ chứng minh trên bộ mẫu | Bộ hiện có để lọt cả 3 câu thử |
| Truyện ngắn 3 khung, 4 bản nhân vật | Người đọc chấm từ 3,5; không ca nào gặp truyện trùng với chuyện đang nặng | 33 người mở; chấm 3,12 |
| Lời mở có lối lui | Người dùng chấm "bớt một mình" từ 3,6; nhóm không có ai an toàn không tụt điểm | 85 người dùng |
| "Phụ đề khác nhau", chuyện vui về tiền | Chạm nỗi buồn không quá 1% người chơi; 100% hiểu luật và biết dừng; chấm riêng gửi hoặc rủ tăng ít nhất 5 điểm | 1 trên 75; 75 trên 75; tăng 14,3 điểm |
| Lá Dám bằng thẻ giấy | Chơi thử với 2 nhóm bạn thật. Không đo bằng người giả | Chưa làm |

### Tuần 7. Hai khóa còn lại, đủ bộ hình, chấm tổng

Chấm đủ 1000 người, Codex đối chiếu 40 người.

| Việc | Mốc đạt | Số tham khảo |
|---|---|---|
| Khóa "Kết bạn ở chỗ mới" | Nhóm năm nhất xa nhà và nhóm ở trọ chấm "bớt một mình" từ 3,5 | Cả app 3,24 |
| Khóa "Tự tin hơn" | Người mở bài chấm từ 3,5 | Chưa đo |
| Đủ 34 động tác và 24 sticker | Đếm đủ bằng máy; giữ được các mốc Mầm xanh của tuần 5 | — |

**Cả gói: 9 điều kiện đã ghi trước, giữ nguyên từng chữ:**

1. "Thấy được hiểu" từ 3,7.
2. "Bớt một mình" từ 3,5 và "bình yên" từ 3,5.
3. Bốn nhóm sinh viên yếu, mỗi nhóm từ 3,5.
4. Gửi hoặc rủ từ 35%, và ít nhất 30% nêu được cụ thể gửi gì, cho ai, vì sao.
5. Mỗi loại hại không quá 3%; trò chơi chạm nỗi đau không quá 1% người chơi; không có nội dung nguy hiểm hay làm nhục.
6. "Bình yên" không tụt so với bản cũ.
7. "Thấy được hiểu" hơn bản cũ ít nhất 0,2.
8. Người dùng chung máy và người không có ai an toàn: từ 3,5, và không tụt quá 0,05.
9. Không ca lộ dữ liệu riêng nào.

Số tham khảo: bản mô tả chưa có Mầm xanh và Học đạt 4 trên 9 (1000 người); bản có Mầm xanh và Học đạt 5 trên 9 (300 người), còn trượt thấy được hiểu (3,63), bớt một mình (3,38), nhóm vừa học vừa làm (3,33) và gửi hoặc rủ (16,7%). Hai nhóm thấp nhất là người ít quen điện thoại và người lớn tuổi. Mốc gửi hoặc rủ 35% chưa có gì cho thấy đạt được bằng người giả.

## Điều kiện bắt đầu, đã chốt 16.11

Chị trả lời tối 16.11.2026: "Q1 M1 N1 O1 P2". Các câu dưới đây chị đã duyệt, **dùng đúng nguyên văn**, không sửa chữ nào. Muốn đổi câu nào thì phải hỏi lại chị.

1. **Dùng mood và lá số trong Học. Chị chọn M1.**
   - Câu hiện ở lần đầu mở Học: "Bạn có muốn Lá dùng lá số, tâm trạng hôm nay và chuyện bạn chọn trong ba lô để gợi ý bài học không? Không đồng ý thì bạn vẫn học được bài chung. Lá không lưu tiến độ học. Bạn tắt được việc này trong Mình." Hai nút: [Đồng ý] [Học bài chung].
   - Dòng thêm vào trang /privacy: "Học: nếu bạn đồng ý, Lá dùng lá số, tâm trạng hôm nay và chuyện bạn chọn trong ba lô để gợi ý bài. Lá không lưu tiến độ học. Tắt trong Mình thì từ lúc đó Lá chỉ gợi ý bài chung."
   - Cách xử lý dữ liệu:
     - lá số là hồ sơ đang lưu trên máy chủ, không lưu thêm gì;
     - tâm trạng hôm nay chỉ dùng cho lần chọn bài đó;
     - chuyện chọn trong ba lô được xử lý ngay trên máy, không lưu, không gửi đi.
   - Rút đồng ý thì từ lúc đó Lá chỉ đưa bài chung. Khi dựng mà phải làm khác cách này thì quay lại hỏi chị.
2. **Tiến độ học:** không lưu trong đợt này (Claude và Codex tự quyết; không thu thêm dữ liệu).
3. **Check kín. Chị chọn N1.** Không làm gợi ý riêng từ kết quả Check kín. Dưới kết quả chỉ có một dòng dẫn sang khóa "Tán crush kiểu tử tế" chung cho mọi người. Không mang gì từ lần check sang bài học, và không rủ check thêm ai khác. Lời mời hai người, trong đó người kia tự nhập thông tin và tự đồng ý, để sang đợt sau.
4. **18+ và bài ranh giới. Chị chọn O1.**
   - Câu ở đầu khóa Tán crush: "Khóa này dành cho người từ 18 tuổi. Bạn đọc bài ranh giới trước rồi mới mở các bài sau."
   - Câu ở đầu trò Lá Dám: "Cả nhóm đều từ 18 tuổi trở lên chứ? Ai cũng có thể bỏ lượt, không cần giải thích. Đừng quay hay chụp người khác khi họ chưa đồng ý."
5. **Góc Tiền bạc** (Claude và Codex tự quyết): làm với 4 chuyện con: thiếu học phí hoặc tiền nhà, cuối tháng cạn, phải gửi tiền về nhà, bị rủ đi chơi tốn tiền. Không hỏi số tiền, không giả định ai đang thiếu. Lựa chọn chỉ được gửi đi cho lần đọc đó, như các góc đọc hiện có. Cần lưu ở đâu thì phải hỏi chị.
6. **Lá số không cần giờ sinh** (Claude và Codex tự quyết):
   - Lá tính trong cả khoảng giờ có thể sinh, theo múi giờ nơi sinh; thiếu nơi sinh thì nới rộng khoảng.
   - Chỉ dùng phần giữ nguyên trong suốt khoảng đó. Không đọc nhà và cung Mọc.
   - Câu lý do tách rõ phần tính và phần đọc.
   - Khi không có gì đủ chắc: "Hôm nay Lá chưa chọn được bài theo lá số của bạn, nên chọn một chủ đề khác để bạn đọc."
7. **Câu hỗ trợ ở cuối bài học chạm chuyện nặng. Chị chọn P2:** "Mình rất tiếc vì bạn đang phải chịu điều này. Bài học không thể hỗ trợ tình huống này. Nếu bạn có thể làm hại bản thân lúc này, hãy tìm một người bạn tin cậy ở cạnh và nhờ hỗ trợ khẩn cấp." Trong đợt này màn Học không có ô gõ chữ. Nguồn của từng bài do Codex duyệt.
8. **Kiểm không lộ dữ liệu riêng** (Claude và Codex tự quyết): trước khi bật mỗi tính năng mới, máy tự kiểm nhật ký, đường mạng, báo lỗi, đường link, tên file tải về và ảnh chia sẻ.
9. **Ai duyệt chữ bài học: đã chốt 14.11, đổi 15.11** (bài đầu và lằn ranh đỏ chuyển Codex duyệt, xem `decision-checklist.md`). Câu về quyền riêng tư, đồng ý và hỗ trợ khi khủng hoảng vẫn do chị duyệt.
10. **Ghi quyết định duyệt chữ bài Học vào tài liệu quy trình và kho câu chữ** (việc của agent, không hỏi lại chị).

## Đã hoãn hoặc chưa có trong kế hoạch

- **"Mời hẹn thử":** chị chốt chưa làm.
- **Lá nhớ hoàn cảnh của người dùng:** điều người giả muốn nhất (179 câu chê trên 1000). Chưa vào kế hoạch vì cần chị quyết về lưu dữ liệu. Riêng S12 "Ghim chuyện đang lo" đã vào kế hoạch sau tuần 4 (chị chọn 15.11): dựng tắt sẵn, chỉ bật khi chị duyệt câu đồng ý và chọn nơi lưu. Hai cách "nhớ" đã thử chỉ nâng điểm ít (0,12 và 0,24) và làm 10% đến 17% người lo riêng tư.
- **Lá Dám trong app, phòng chơi từ xa, ô viết "Kể ra rồi thả":** để sau 7 tuần.
