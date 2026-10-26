# Bộ playtest giấy cho dòng game Lá Úp và Tri Kỷ (11–12/2026)

> Trạng thái: **nháp v0.1, ngày 26/10/2026.** Toàn bộ ngân hàng nội dung trong bộ này (sự kiện, lời khai, thông điệp, vụ án, lời thoại con ma, câu đố) là **nháp, chờ owner duyệt văn phong**. Không chạy buổi nào trước khi owner duyệt.
>
> Nguồn luật chơi: báo cáo "Chốt năm trò, giữ trọn chữ Lành" (26/10/2026). Luật ở đây giữ đúng báo cáo. Chỗ nào bản giấy phải làm khác, hoặc phải chọn một cách khi báo cáo chưa nói rõ, đều ghi ở mục "Quyết định riêng của bản giấy".

## Bộ này để làm gì

Giai đoạn 3 (game) chưa bắt đầu và chưa có dòng code nào. Theo thứ tự owner chốt ngày 23/10 (riêng tư → nội dung → game), việc làm được bây giờ là kiểm luật bằng giấy với người thật. Mỗi buổi playtest trả lời một câu hỏi mà chỉ người thật trả lời được:

| Trò | Câu hỏi chính của playtest |
|---|---|
| Hết Cứu % | Sau 3 tuần, nhóm còn tự khai không, và có ai thấy bị nhắm vào không? |
| Tam Sao Thất Bản | Chọn đáp án có làm câu trôi đủ để cười không? Bản chat 24 giờ có đủ chuỗi hoàn tất không? |
| Phiên Tòa Tủ Lạnh | Một buổi tất niên văn phòng có cười to được mà không ai thấy bị kết án thật không? |
| Sĩ Số +1 | Lớp 30 người có thấy "sao nó biết" mà không ai sợ thật hoặc thấy bị nhắm vào không? |
| Tri Kỷ | Người đọc có hiểu "Tri Kỷ" là tình bạn, không phải yêu đương, và có nhãn nào nghe như bị từ chối không? |

Kết quả playtest là đầu vào cho PRD/SRS của từng trò (thư mục `docs/foundation/game-line/`), cho DPIA (`docs/legal/2026-10-26-game-line-dpia.md`) và cho các quyết định chờ owner D1–D8. Kết quả không tự biến thành quyết định.

## Thứ tự và lịch

Thứ tự ưu tiên giữ đúng báo cáo: rẻ và ít dữ liệu đi trước, rủi ro "bị nhắm vào" cao đi sau.

| # | Trò | Hình thức | Người chơi | Lịch đề xuất |
|---|---|---|---|---|
| 0 | Chuẩn bị chung | Owner duyệt văn phong mọi ngân hàng; in; tìm nhóm; tập kịch bản | — | 27/10 – 06/11/2026 |
| 1 | **Hết Cứu %** | 3 tuần qua tin nhắn, 2–3 nhóm kín (một nhóm bạn đại học, một phòng ban) | 4–12 mỗi nhóm | Tuần 1: thứ Hai 09/11 → thứ Sáu 13/11. Tuần 2: 16/11 → 20/11 (bật Nhân Vật Chính tự nguyện). Tuần 3: 23/11 → 27/11. Xoá dữ liệu thô chậm nhất thứ Hai 30/11 lúc 20:00 |
| 2a | **Tam Sao Thất Bản** – buổi trực tiếp | Một bàn, phong bì chuỗi, host đọc màn lật | 8–12 | Thứ Bảy 14/11/2026, khoảng 60 phút |
| 2b | **Tam Sao Thất Bản** – buổi chat 24 giờ | Một nhóm Zalo thật, host gửi riêng từng lượt | 5–6 | Thứ Ba 24/11 21:00 → thứ Tư 25/11 21:00 (lật). Xoá chậm nhất thứ Sáu 27/11 21:00 |
| 3 | **Phiên Tòa Tủ Lạnh** | Buổi tất niên văn phòng thật | 16–24 | Cửa sổ 07/12 – 18/12/2026 (ưu tiên tối thứ Sáu 11/12 hoặc 18/12). Dự phòng: tuần đầu 01/2027 |
| 4 | **Sĩ Số +1** | Một lớp đại học | khoảng 30 | Cửa sổ 14/12 – 23/12/2026 (buổi học cuối trước thi). Dự phòng: 04/01 – 15/01/2027 |
| 5 | **Tri Kỷ** – kiểm tra chữ | Phỏng vấn ngắn từng người hoặc từng cặp | 5–10 | 16/11 – 18/12/2026. Chạy song song được vì không phải trò chơi và không thu dữ liệu sinh |
| — | Tổng hợp | Điền mẫu kết quả, gửi owner | — | 28/12 – 31/12/2026 |

Ghi chú lịch:

- Tết Đinh Mùi rơi vào đầu tháng 2/2027. Không hứa mốc Tết cho sản phẩm; lịch này chỉ là lịch playtest.
- Nếu buổi tất niên rơi sau buổi lớp học, vẫn chạy được. Thứ tự ở bảng là thứ tự ưu tiên, không bắt buộc ngày nào trước ngày nào ngoài Hết Cứu % đi đầu.
- Mỗi buổi cần owner duyệt văn phong của đúng bộ in sẽ dùng (cổng 0 trong checklist).

## Cấu trúc thư mục

Mỗi trò có một thư mục, cùng sáu tệp:

| Tệp | Nội dung |
|---|---|
| `01-luat-choi.md` | Luật một trang cho người chơi, in phát tay |
| `02-kich-ban-host.md` | Kịch bản host theo từng phút, có câu đọc nguyên văn |
| `03-bo-in.md` | Thẻ, phiếu, bảng để in và cắt (nháp, chờ owner duyệt văn phong) |
| `04-phieu-diem.md` | Phiếu tính điểm hoặc sổ ghi ván của host |
| `05-khao-sat-an-danh.md` | Phiếu khảo sát 3 câu (Phiên Tòa thêm câu 4), không ghi tên |
| `06-mau-ket-qua.md` | Mẫu ghi kết quả, chỉ số liệu tổng hợp |

Thư mục:

- [`het-cuu-phan-tram/`](het-cuu-phan-tram/)
- [`tam-sao-that-ban/`](tam-sao-that-ban/)
- [`phien-toa-tu-lanh/`](phien-toa-tu-lanh/)
- [`si-so-cong-1/`](si-so-cong-1/)
- [`tri-ky/`](tri-ky/)

## Ngưỡng thành công từng trò

Ngưỡng lấy từ phần chỉ số của báo cáo. Ngưỡng nào báo cáo chưa cho số, bộ này ghi **"đề xuất — chờ owner"**. Một buổi chỉ "đạt" khi qua mọi ngưỡng bắt buộc, kể cả ngưỡng an toàn.

| Trò | Ngưỡng bắt buộc (từ báo cáo) | Ngưỡng phụ (đề xuất — chờ owner) | Dừng ngay nếu |
|---|---|---|---|
| Hết Cứu % | Ít nhất **2/3 thành viên vẫn tự khai ở tuần 3**; **0 báo cáo khó chịu / bị nhắm vào** | Ít nhất 2/3 số nhóm đi tới màn lật cả 3 tuần; lượt dùng "ẩn %" + "đừng đoán tôi" không tăng qua từng tuần | Có 1 người báo bị nhắm vào: host dừng nhóm đó, hỏi riêng cách sửa, không chạy tuần tiếp theo cho tới khi sửa xong |
| Tam Sao Thất Bản (trực tiếp) | Không có ngưỡng số trong báo cáo; đo "độ thất bản" | Ít nhất **1/2 số chuỗi** có độ thất bản 2–3 (đoán sai câu gốc hoặc đổi ý); thời gian trung vị từ gieo tới lật ≤ 20 phút; ít nhất 1/2 bàn xin chơi ván hai | Có người bị trêu vì cách đọc to: host bỏ bước đọc to |
| Tam Sao Thất Bản (chat 24 giờ) | **Ít nhất 70% chuỗi đạt đủ 4 lượt trước giờ lật** VÀ **nhóm tự xin chơi lại** (cả hai mới cho bản chat vào MVP, quyết định D4) | Host phải làm Bot Sao Thủy ≤ 1 lần mỗi chuỗi | — |
| Phiên Tòa Tủ Lạnh | **0 báo cáo khó chịu / bị nhắm vào**; từ lúc nhận phiếu tới lúc hành động đầu tiên **dưới 60 giây** (bản giấy: điền câu đầu tiên) | Ít nhất 60% người có lên tiếng ít nhất một lần; ít nhất 3 tràng cười to cả phòng; ít nhất 1 người hỏi "làm host thế nào" | Có người thấy bản án nhắm vào chuyện có thật: dừng vụ, đổi sang vụ con vịt cao su |
| Sĩ Số +1 | **0 báo cáo khó chịu, bị nhắm vào hoặc sợ thật** | Ít nhất 3 lần cả phòng thốt "sao nó biết"; ít nhất 50% người lên tiếng trong phần thảo luận; người tổ chức lớp muốn đặt buổi thứ hai | Có người sợ thật hoặc xin dừng: chuyển ngay sang chế độ bật đèn hoặc kết thúc, giải thích cơ chế |
| Tri Kỷ (kiểm tra chữ) | Báo cáo không cho số | Ít nhất **80%** người đọc hiểu "Tri Kỷ" kèm dòng chặn là tình bạn; **không quá 1** người thấy một nhãn bậc nghe như bị từ chối; không ai ngại gửi lời mời vì sợ bị hiểu là tỏ tình sau khi đọc dòng chặn | — |

## Checklist cho host

### Trước buổi

- [ ] **Cổng 0:** owner đã duyệt văn phong bộ in của trò này (ghi ngày duyệt vào mẫu kết quả).
- [ ] Cả nhóm chơi đều từ 18 tuổi. Lớp đại học: chọn lớp từ năm thứ hai trở lên. Sinh viên năm nhất khoá 2026 có thể sinh cuối năm 2008, nên trong tháng 12/2026 vẫn có người chưa đủ 18.
- [ ] Văn phòng: người tổ chức tiệc (HR hoặc trưởng nhóm) đồng ý cho chạy trò, biết trò không có ảnh, không có tên thật, không có tiền.
- [ ] Có host phụ cho các buổi trực tiếp trên 12 người (Phiên Tòa, Sĩ Số +1).
- [ ] In đủ bộ `03-bo-in.md`, phiếu khảo sát, thêm 20% dự phòng. Cắt sẵn thẻ.
- [ ] Bút, phong bì, hộp kín đựng phiếu khảo sát, đồng hồ bấm giờ, kéo hoặc máy huỷ giấy.
- [ ] Đọc to kịch bản ít nhất một lần, bấm giờ.
- [ ] Đã chuẩn bị câu đồng ý nói miệng (mục dưới) và biết cách trả lời "dữ liệu đi đâu".
- [ ] Không chuẩn bị Google Form, Zalo bình chọn hay bảng tính có cột tên. Zalo bình chọn trong nhóm thường cho thấy ai chọn gì, nên không dùng cho khảo sát.

### Trong buổi

- [ ] Đọc câu đồng ý trước khi phát bất kỳ phiếu nào.
- [ ] Ai nói "chỉ xem" thì không nhận phiếu, không nhận vai, vẫn được ngồi xem và bỏ phiếu khảo sát.
- [ ] Không chụp ảnh, không quay, không ghi âm, trừ khi mọi người trong khung hình đã đồng ý rõ ràng. Không bao giờ chụp phiếu.
- [ ] Ghi số liệu ngay trên phiếu điểm, theo số thứ tự. Không viết tên thật lên bất kỳ giấy nào.
- [ ] Nếu có người khó chịu: dừng, hỏi riêng, cho người đó rời mà không cần giải thích.

### Sau buổi

- [ ] Phát phiếu khảo sát 3 câu, người chơi tự bỏ vào hộp kín.
- [ ] Huỷ phiếu khai báo, phiếu đoán, thẻ vai có chữ viết ngay tại chỗ, trước mặt người chơi.
- [ ] Hết Cứu % và Tam Sao bản chat: xoá tin nhắn riêng và bảng tính tay theo đúng hạn ở mục "Bảo vệ dữ liệu".
- [ ] Điền `06-mau-ket-qua.md` trong 24 giờ: chỉ số đếm, không tên, không biệt danh, không số thứ tự gắn với câu trả lời.
- [ ] Huỷ luôn phiếu điểm có số thứ tự sau khi đã chép số tổng hợp sang mẫu kết quả.

## Bảo vệ dữ liệu trong playtest

Playtest giấy vẫn xử lý dữ liệu cá nhân: câu trả lời khai báo (bữa sáng, màu áo, chỗ ngồi…) gắn với người đang ngồi trong phòng, phần trăm tự khai trong Hết Cứu %, và tin nhắn riêng gửi host. Vì vậy mọi buổi theo đúng các quy tắc dưới đây. Quy tắc này mô phỏng hợp đồng dữ liệu của sản phẩm (tối thiểu, có hạn xoá, chỉ số tổng hợp) để playtest cũng thử luôn màn "tiêu huỷ hồ sơ".

### 1. Chỉ người từ 18 tuổi

- Host hỏi miệng khi mời và nhắc lại ở câu đồng ý. Không xem giấy tờ, không ghi năm sinh.
- Nếu trong phòng có người dưới 18: người đó không nhận phiếu, không nhận vai. Với Sĩ Số +1 thì chuyển sang chế độ bật đèn hoặc hoãn buổi.

### 2. Câu đồng ý nói miệng

Host đọc nguyên văn trước khi phát phiếu (bản riêng cho từng trò nằm trong `02-kich-ban-host.md`, cùng ý):

> "Trước khi chơi, mình nói rõ ba điều.
>
> Một: đây là buổi thử luật cho một trò chơi đang làm của nhóm Lá Lành. Chỉ người từ 18 tuổi trở lên tham gia. Nếu bạn chưa đủ 18, bạn ngồi xem cùng mọi người nhé.
>
> Hai: trên phiếu không có tên. Mỗi người một số. Câu trả lời của bạn có thể được đọc to trong phòng như một manh mối. Ai không muốn câu trả lời của mình được đọc thì để trống ô đồng ý trên phiếu, hoặc chọn 'chỉ xem'. Không cần giải thích.
>
> Ba: hết buổi, mình xé toàn bộ phiếu ngay tại đây. Không chụp ảnh, không quay, không ghi âm. Mình chỉ giữ lại con số đếm, ví dụ 'có 18 người chơi, 3 người chỉ xem'.
>
> Bạn có thể dừng hoặc rời đi bất cứ lúc nào. Ai đồng ý chơi thì giơ tay nhé."

Host ghi vào phiếu điểm: số người đồng ý, số người chỉ xem. Không ghi ai. Im lặng không tính là đồng ý: ai không giơ tay thì mặc định chỉ xem.

### 3. Không có tên trên giấy

- Mỗi người rút một phiếu số ngẫu nhiên (1, 2, 3…). Phiếu khai báo, phiếu đoán, thẻ vai chỉ ghi số.
- Biệt danh chơi (nếu trò cần) do người chơi tự đặt, 2–20 ký tự, không dùng tên thật đầy đủ. Host có quyền đổi biệt danh xúc phạm.
- Host không viết bảng "số → tên thật" ở bất kỳ đâu.

### 4. Không dùng Google Form gắn tên

- Không dùng Google Form, Zalo bình chọn, Microsoft Forms hay bảng tính có cột tên, email hoặc số điện thoại.
- Khảo sát dùng giấy và hộp kín. Riêng Hết Cứu % và Tam Sao bản chat chạy từ xa: host gửi ảnh phiếu khảo sát 3 câu, người chơi nhắn riêng ba ký tự trả lời (ví dụ "4-K-C"). Host chép vào bảng đếm rồi xoá tin nhắn ngay. Nếu muốn dùng biểu mẫu trực tuyến thì phải tắt thu email, không bắt đăng nhập, không có ô chữ tự do, và phải ghi lại cấu hình đó vào mẫu kết quả.

### 5. Ảnh và ghi hình

- Mặc định không chụp, không quay, không ghi âm.
- Chỉ chụp hoặc quay khi **mọi người trong khung hình** đã đồng ý rõ ràng, từng người. Không quay phiếu, màn lật có câu trả lời, hay bảng điểm.
- Chỉ số "có người rút điện thoại quay" chỉ đếm số lần. Host nhắc ngay từ đầu: "Muốn quay thì hỏi người trong khung hình trước."

### 6. Tiêu huỷ

| Trò | Thứ phải huỷ | Hạn |
|---|---|---|
| Phiên Tòa, Sĩ Số +1, Tam Sao trực tiếp, Tri Kỷ | Phiếu khai báo, phiếu đoán, thẻ vai có chữ viết, phong bì manh mối đã điền, sổ ghi ván có số thứ tự | Xé hoặc huỷ ngay cuối buổi, trước mặt người chơi |
| Hết Cứu % | Tin nhắn riêng chứa % và phiếu đoán (ở máy host), bảng tính tay theo số | Chậm nhất **72 giờ sau màn lật thứ Sáu** của từng tuần. Danh hiệu theo tuần giữ tới hết playtest + 30 ngày rồi xoá |
| Tam Sao bản chat | Tin nhắn riêng chứa lựa chọn từng lượt, sổ chuỗi | Chậm nhất **48 giờ sau giờ lật** |

Zalo là dịch vụ của bên thứ ba. Host xoá được đoạn chat ở máy mình, nhưng không kiểm soát bản lưu trên máy người khác hay máy chủ của dịch vụ. Vì vậy tin nhắn playtest chỉ chứa mã lựa chọn và con số, không chứa chuyện riêng. Host nhắc người chơi tự xoá đoạn chat với host ở máy họ nếu muốn.

### 7. Khảo sát ẩn danh 3 câu

Câu chung cho mọi trò (bản từng trò ở `05-khao-sat-an-danh.md`):

1. Bạn thấy trò này vui tới đâu? (1 = chán, 5 = rất vui)
2. **Có lúc nào bạn thấy bị nhắm vào không?** (Sĩ Số +1: "…bị nhắm vào hoặc sợ thật không?") — Có / Không / Không chắc
3. Nếu có buổi sau, bạn muốn chơi lại không? — Có / Có thể / Không

Riêng Phiên Tòa Tủ Lạnh thêm câu 4: **"Có lúc nào bạn thấy bị ép phải nói không?"** — Có / Không / Không chắc (điều kiện G34-AC10). Một phiếu "Có" ở câu này cũng là không đạt ngưỡng an toàn.

Không có ô chữ tự do, để người viết không vô tình kể chuyện về một người khác. Ý kiến thêm thì nói miệng với host lúc tổng kết. Host ghi theo chủ đề, không ghi ai nói.

### 8. Cách ghi kết quả không có dữ liệu cá nhân

- Chỉ ghi con số đếm và tỷ lệ: số người, số chuỗi, số lần cười, số phiếu "Có" ở câu 2.
- Không ghi biệt danh, số thứ tự, màu áo hay bất kỳ câu trả lời nào gắn với một người.
- Số đếm dưới 3 trong một nhóm nhỏ có thể lộ người. Với các câu trả lời khai báo, chỉ ghi giá trị phổ biến nhất và chỉ khi có từ 3 người trở lên chọn.
- Trích ý kiến thì viết lại bằng lời của host, bỏ mọi chi tiết nhận ra người nói.
- Mẫu kết quả được commit vào repo, nên phải đọc lại một lần với câu hỏi: "Người trong phòng đọc tệp này có nhận ra ai không?" Nếu có thì sửa trước khi commit.

### 9. Lằn ranh nội dung (mọi trò)

Ngân hàng nội dung không chạm: ngoại hình và cơ thể, tình dục và giới, sức khoẻ (cả tinh thần), tội phạm thật (chỉ có vụ hộp xôi hư cấu), quan hệ tình cảm thật, tiền thật và lương, gia đình nhạy cảm, tôn giáo, vùng miền, chính trị, người thật có tên, tự hại, thử thách có rượu bia. Phán quyết và bản án nhắm vào vai do game chia, không nhắm vào con người. Mọi bản án tượng trưng đều có "Miễn án". Không bao giờ đoán sức khoẻ tinh thần, xu hướng tính dục, sang chấn, ngoại tình, danh tính crush, kết quả thi hay "ai toxic".

## Quyết định riêng của bản giấy

Những chỗ báo cáo chưa nói rõ hoặc bản giấy buộc phải làm khác. Writer PRD/SRS và owner cần khớp lại.

| # | Trò | Bản giấy làm thế nào | Lý do |
|---|---|---|---|
| P1 | Hết Cứu % | **Đề xuất — chờ owner (D3):** mỗi người có **3 lá cho mỗi sự kiện**, chia tuỳ ý cho 3 phiếu đoán (một mức 0–3 lá, tổng không quá 3). Lá hết hiệu lực khi sự kiện kết thúc. Điểm về 0 mỗi tuần. Không có bảng điểm cộng dồn | Báo cáo gốc cho 10 lá nạp lại mỗi tháng, trái với nguyên tắc "không coin/XP, không streak, không áp lực quay lại" của plan 23/10. Bản giấy thử phương án mặc định của brief |
| P2 | Hết Cứu % | Người bật "tuần này đừng đoán tôi" không có tên trong danh sách đoán và không được tính vào "ai khai cao nhất". Họ vẫn tự khai và đoán người khác | Nếu vẫn tính vào ngôi đầu thì mọi phiếu đoán khác sai oan |
| P3 | Hết Cứu % | Màn lật thứ Sáu chạy qua cuộc gọi nhóm hoặc gặp mặt, host chiếu slide chứ không gửi tệp. Tin nhắn lật gửi vào nhóm chỉ có danh hiệu và người khai cao nhất mỗi mức, không gửi bảng % từng người | Tin nhắn trong nhóm Zalo nằm lại vô thời hạn, vượt hạn xoá 72 giờ |
| P4 | Hết Cứu % | Nhãn độ lệch của Nhân Vật Chính theo PRD §5.4 và HC-FR-39: dưới 20 điểm "Tự biết mình ghê", 20–49 "Cứu được chút", từ 50 "HẾT CỨU". "Ẩn %" hiện dải theo HC-FR-25: thấp (0–30), vừa (35–65), cao (70–100). **Đề xuất — chờ owner** | Một bộ nhãn cho cả PRD, SRS và bản giấy |
| P5 | Tam Sao | Bản giấy dùng 8 thông điệp gốc, mỗi thông điệp gắn sẵn hai giọng; lượt 4 có 3 câu cho mỗi nhóm mood (4 nhóm). Một thông điệp được dùng cho nhiều chuỗi | In 60 thông điệp × 5 giọng không khả thi; báo cáo cho phép 3–4 phương án mỗi lượt |
| P6 | Phiên Tòa | Năm câu khai báo chọn từ danh sách có mã. Manh mối in sẵn cho mọi giá trị, host chỉ rút thẻ đúng. Kẻ Chủ Mưu chọn manh mối nào bị đổi chữ; chữ bị đổi là chữ cái đầu của ba câu trả lời của chính Kẻ Chủ Mưu | Host chỉ có 5 phút giải lao để chuẩn bị ba vụ |
| P7 | Phiên Tòa | Người không tick ô "câu trả lời có thể được đọc to" không bao giờ là Thủ Phạm, Đồng Phạm hay Kẻ Chủ Mưu | Manh mối được dựng từ câu trả lời của các vai này |
| P8 | Sĩ Số +1 | Pha đêm dùng cách nhắm mắt của Ma Sói thay cho nhắn riêng host. Kẻ Bị Nhập chỉ tay chọn trong 3 số ứng viên host giơ lên | Không để lại tin nhắn nào, khỏi phải xoá |
| P9 | Sĩ Số +1 | Người bị trục xuất (bất kỳ vai nào) lật thẻ và ra "ngoài hành lang": vẫn ngồi lại, chơi Akinator, xem màn lật; không bầu trục xuất, không thành Hồn. Hồn cũng không bầu trục xuất. Theo PRD §5.1, SS-D6 và SRS SS-FR-42, SS-FR-44. **Đề xuất — chờ owner** | Không ai bị gạt ra khỏi phòng, và bản giấy đo đúng luật của app |
| P10 | Sĩ Số +1 | Bản giấy dùng **đúng bộ luật đề xuất của PRD §4.2, §5.2 và SRS SS-FR-05, SS-FR-21, SS-FR-70–73** (SS-D2 — đề xuất, chờ owner): lớp 30 người có 4 Kẻ Bị Nhập và 2 lượt bắt mỗi đêm; 4 vòng mặc định, host chốt 5 vòng trước buổi nếu có từ 45 phút. Hết vòng cuối mà chưa bên nào thắng ngay: Người Sống thắng nếu đã trục xuất ít nhất một nửa số Kẻ Bị Nhập (làm tròn lên); nếu không, con ma thắng. Màn lật mặc định không nêu ai đã thì thầm, chỉ nêu người tự giơ tay nhận (SS-D10, DP-1). Riêng thư của Hồn và vòng Akinator, bản giấy đơn giản hoá (mọi Hồn ghép một biệt danh; người tự nguyện tự giơ CÓ/KHÔNG) | Lớp 30 người, mỗi đêm bắt 1–2 người, thì 4–5 vòng không thể bắt đủ nửa phòng (tối đa 8–10 người, cần 15), nên luật hết vòng quyết định. Bản trước của bộ này dùng luật hết giờ riêng; nay bỏ để PRD, SRS, story G44 và bản giấy chỉ có một bộ luật |
| P11 | Sĩ Số +1 | Màn "bản sao" chỉ đọc giá trị phổ biến nhất của mỗi câu và số người chọn, chỉ khi từ 3 người trở lên | Số đếm nhỏ có thể lộ người |
| P12 | Mọi trò | Host không chơi | Host thấy toàn bộ câu trả lời |
| P13 | Tam Sao (chat) | Đồng hồ hạn chót 3 giờ tạm dừng từ 23:00 tới 8:00 | Hạn 3 giờ chạy qua đêm sẽ làm Bot Sao Thủy điền gần hết lượt đêm; nhắn lúc khuya cũng trái chất bình yên |
| P14 | Sĩ Số +1 | Người không tick đồng ý không bao giờ vào cốc ứng viên và không được tự nguyện ở vòng Akinator | Con ma đọc câu trả lời của nạn nhân và người tự nguyện |
| P15 | Sĩ Số +1 | Tên vai ở chế độ bật đèn: Nhân Viên, Nội Gián, Bảo Vệ Toà Nhà, Người Bị Điều Chuyển. **Đề xuất — chờ owner** | Báo cáo chỉ đổi Người thứ 31; giữ tên "Thầy Pháp", "Hồn" thì bản bật đèn vẫn còn sắc tâm linh. **Còn lệch:** PRD §4.3 đề xuất bộ tên khác (Đồng Nghiệp, Người Được Nhờ, Bên Nhân Sự, Người Đi Họp); owner chọn một bộ trước buổi chơi thử |
| P16 | Tri Kỷ | Điểm "Hiểu Nhau Không?" x/7 là điểm chung của cặp: một câu được tính khi **cả hai** đoán đúng câu của nhau (mặc định TK-5, SRS FR-TK-104, G55). Không tính và không đọc điểm riêng từng người. Sổ ghi thêm cách tính "ít nhất một người đúng" **chỉ để so trong playtest**, không đọc cho cặp. **Đề xuất — chờ owner (TK-5)** | Báo cáo chưa nói cách đếm; D5 chỉ quyết chuyện không có % độ hợp |
| P17 | Phiên Tòa | Bản giấy dài 35–45 phút thay vì 25–35 phút, vì có 5 phút nghỉ chuẩn bị manh mối và giải mã bằng tay | Không có điện thoại làm tay cầm |

## Bàn giao theo AGENTS.md

**Nguồn đã kiểm tra:** báo cáo "Chốt năm trò, giữ trọn chữ Lành" (26/10/2026) cùng brief chung của đợt viết tài liệu; `AGENTS.md`; `docs/foundation/la-lanh-plain-vietnamese-content-standard.md`; `docs/plans/2026-10-23-privacy-content-game-plan.md`; ghi chú nghiên cứu `research_notes/Chốt trò chơi nhóm Lá Lành/tri_ky_friendship_ranking.md` và `research_notes/Trò chơi viral thần bí cho nhóm/risks_privacy_policy.md`. Web, 26/10/2026: xác nhận Luật 91/2025/QH15 có hiệu lực từ 01/01/2026 ([Thị trường Tài chính Tiền tệ](https://thitruongtaichinhtiente.vn/nhung-diem-chinh-can-luu-y-tai-luat-bao-ve-du-lieu-ca-nhan-chinh-thuc-co-hieu-luc-tu-ngay-1-1-2026-75881.html), [tài liệu giới thiệu của NHNN](https://sbv.gov.vn/documents/20117/1445080/Tài%20liệu%20giới%20thiệu%20Luật%20Bảo%20vệ%20dữ%20liệu%20cá%20nhân.docx.docx/1334c638-924f-58e2-f754-998f8ba38e5d)). Nguyên tắc "im lặng không phải là đồng ý" và đồng ý theo từng mục đích lấy từ báo cáo (dẫn LuatVietnam); lượt này chưa đọc lại nguyên văn Điều 9–10 ([toàn văn trên LuatVietnam](https://static3.luatvietnam.vn/uploaded/others/2025/08/21/luat-91-2025-qh15_2108094941.pdf)).

**Phát hiện đã sửa trong bộ playtest:** thay sự kiện #20 "mẹ gọi video" của Hết Cứu % bằng sự kiện văn phòng mới, khớp PRD (chủ đề gia đình nằm trong danh sách cấm); bỏ câu "lá tuần này đã báo trước" (câu dự đoán) và không đọc to điểm tuần của ai (HC-FR-30); Sĩ Số +1 dùng đúng bộ luật thắng thua, số lượt bắt và số vòng của PRD/SRS, màn lật mặc định không nêu người thì thầm (P9, P10); Phiên Tòa thêm câu khảo sát "bị ép phải nói"; tách lá của Hết Cứu % theo từng sự kiện (P1); không gửi bảng % vào nhóm chat (P3); bỏ cách nhắn riêng host ở Sĩ Số +1 (P8); không dùng Zalo bình chọn cho khảo sát vì lộ người chọn; khảo sát không có ô chữ tự do; số đếm dưới 3 không được ghi; chọn lớp từ năm hai trở lên để tránh người 17 tuổi; người không đồng ý đọc câu trả lời không nhận vai bị dựng manh mối (P7, P14); đổi cụm "giữ nhịp" trong lá đôi mẫu của Tri Kỷ vì nằm trong danh sách không dùng của chuẩn nội dung; Sĩ Số +1 luôn kết bằng giải thích cơ chế và không có lời hẹn kéo dài ra ngoài buổi (bài học Momo); bản án Phiên Tòa chỉ làm tại chỗ, không tiền, không đồ uống.

**Rủi ro chưa giải quyết:** Zalo giữ bản tin nhắn ngoài tầm xoá của host; đồng ý nói miệng không để lại bằng chứng theo từng người (Nghị định 356 đòi chứng minh được đồng ý; playtest cố ý không ghi danh tính, cần counsel xác nhận cách ghi số đếm là đủ); cân bằng thắng thua của Sĩ Số +1 chưa chơi thử (P10, SS-D2); D3 chưa chốt; chưa kiểm tra quy định quấy rối nơi làm việc (Bộ luật Lao động 2019, Nghị định 145/2020) cho bản văn phòng của Phiên Tòa; câu "chơi lại mỗi tháng để phá kỷ lục" của Tri Kỷ có thể trái nguyên tắc không gây áp lực quay lại (bộ này đo bằng câu K2); bản giấy của Tam Sao gắn sẵn giọng cho từng thông điệp nên độ trôi đo được có thể thấp hơn bản app có giọng ngẫu nhiên.

**AC/DoD còn thiếu:** owner chưa duyệt văn phong bất kỳ ngân hàng nào; chưa chạy buổi nào; luật bản giấy đã đối chiếu với PRD/SRS ngày 26/10/2026 (P4, P9, P10, P16); còn lệch có ghi rõ: tên vai bật đèn của Sĩ Số +1 (P15), cách đơn giản hoá thư của Hồn và vòng Akinator (P10), danh hiệu và lá của tuần trong bộ in Hết Cứu % khác bảng PRD §5.2 ở một số sự kiện; ngưỡng phụ "đề xuất — chờ owner" chưa được duyệt.
