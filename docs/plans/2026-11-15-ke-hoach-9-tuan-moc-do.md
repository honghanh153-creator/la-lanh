# Kế hoạch 9 tuần và mốc đo cho từng tính năng (15.11.2026)

Bản này trình bày lại kế hoạch theo từng tuần, sau các quyết định của chị đêm 14.11:

- Lá pixel là Mầm xanh, làm bằng code, không thuê họa sĩ.
- Lá nhây thay nút "Vibe"; bỏ hẳn nội dung Cà khịa.
- "Học theo bạn" vào gói.
- "Mời hẹn thử" hoãn.

Mỗi tính năng có mốc đạt, tạm thời đo bằng 1000 người giả. Nguồn số "hiện tại": lượt chấm 1000 người giả trên bản mô tả (14.11) và lượt Codex chấm thử 20 người. Chi tiết ở `docs/reviews/2026-11-15-sang-tao-viral.md`.

**Chưa có code nào được viết.** Các mốc dưới đây là đề xuất để chị duyệt. Mốc nào đã được ghi trước lượt chấm 14.11 thì giữ nguyên, không hạ.

## Cách đo

- **Cuối mỗi tuần:** chấm trên 300 người giả chọn đều theo nhóm, so app sau tuần đó với app trước tuần đó.
- **Tuần 4 và tuần 9:** chấm đủ 1000 người, và Codex chấm đối chiếu 40 người.
- **Chấm trên cái gì:** phần đã có code thì chấm trên chữ và màn hình app thật tạo ra. Phần chưa có code thì chấm trên mô tả, và báo cáo ghi rõ là mô tả.
- **Mốc ghi trước khi chấm**, không sửa sau khi thấy điểm.
- **Không đạt thì** sửa ở tuần kế tiếp, và chưa làm phần phụ thuộc vào nó.

## Luật chung: một tính năng "đạt" khi đủ ba điều

Luật này đã ghi trước lượt chấm 14.11.

1. Người dùng tới tính năng đó chấm "thấy được hiểu" từ 3,5 trở lên (thang 1–5).
2. Mỗi loại hại không quá 3%: thấy bị trách, bị ép, lo riêng tư, bị kéo phụ thuộc, phải xem Lá mới dám quyết. Không có ca lộ dữ liệu riêng nào.
3. Khi chấm riêng, nó làm "thấy được hiểu" tăng ít nhất 0,2, hoặc làm tỉ lệ gửi ảnh hay rủ người khác tăng ít nhất 5 điểm phần trăm.

Các bảng dưới ghi thêm mốc riêng của từng tính năng.

## Tuần 1. Nền an toàn và bộ đo

| Việc | Mốc đạt | Hiện tại |
|---|---|---|
| Bộ đo trên 1000 người giả | Chấm lại cùng 100 người, điểm trung bình lệch không quá 0,15 | Chưa đo |
| Lớp an toàn khi người dùng gõ câu nguy hiểm | Bắt 100% trong 135 câu có ý định tự hại; báo nhầm không quá 2% trong 205 câu nói theo nghĩa bóng | Đo ở tuần này |
| Dòng báo nơi lưu hồ sơ, nhãn tiếng Việt, nút không bị che | Người lo riêng tư không quá 3% | 3,5% ở kế hoạch hiện tại, phần lớn do dòng "Hồ sơ của bạn đang lưu trên trình duyệt này" |
| Giữ việc cho cả 3 loại hồ sơ (chỉ ngày sinh, giờ khoảng, giờ chính xác) | Không có ca lỗi nào trong 300 đường bấm | Chưa đo |

## Tuần 2. Việc hợp sức, mood đổi việc, nội dung sinh viên

| Việc | Mốc đạt | Hiện tại |
|---|---|---|
| Kho việc theo sức, mood đổi việc | Người mood thấp chấm "bình yên" từ 3,5; thấy bị ép không quá 3% | Bình yên cả app 3,23; bị ép 0,2% |
| Nội dung sinh viên | Bốn nhóm sinh viên yếu (đang tìm việc, tiền eo hẹp, áp lực gia đình, vừa học vừa làm): mỗi nhóm tăng "thấy được hiểu" ít nhất 0,2 so với tuần 1 | Bản mô tả gói: 3,55 đến 4,11 |
| Góc Tiền bạc (4 chuyện con) | Câu chê "thiếu chuyện tiền" giảm một nửa | 61 câu trên 1000 |

## Tuần 3. Tuần có mạch, lá số không cần giờ sinh, nội dung người đi làm

| Việc | Mốc đạt | Hiện tại |
|---|---|---|
| Chế độ tuần (tuần là chương, ngày là cảnh) | Ít nhất 25% mở tab Tuần; người mở chấm từ 3,5; không có cặp tuần–ngày nào nói ngược nhau trong 200 cặp kiểm | 26% mở; 3,38; chấm riêng tăng 0,56 |
| Lá số không cần giờ sinh | Người chỉ có ngày sinh chấm từ 3,5 và không thấp hơn người có giờ sinh quá 0,2; không có câu nào nói chắc quá mức | Người dùng tới chấm 3,37; chấm riêng tăng 0,16 |
| Nội dung người đi làm | Nhóm làm ca và nhóm áp lực từ sếp chấm từ 3,3; câu chê "không hợp ca làm, giờ giấc" giảm một nửa | 81 câu trên 1000; chấm thử, nhóm sếp chỉ được 2 |

## Tuần 4. Trang chủ gọn, Gánh hôm nay, mở lá chọn góc

Đây là mốc lớn, chấm đủ 1000 người. Không đạt thì tuần 5–6 chỉ sửa nền.

| Việc | Mốc đạt | Hiện tại |
|---|---|---|
| Gánh hôm nay (ba lô) | Ít nhất 50% mở ba lô; người mở chấm từ 3,7 | 53%; 3,77; chấm riêng tăng 0,66 |
| Mở lá chọn góc | Ít nhất 50% dùng; người dùng chấm từ 3,5 | 57%; 3,22 (chưa đạt) |
| Trang chủ gọn, 3 khối | Người rất mệt nghỉ được sau 1 chạm ở ít nhất 90% đường bấm; người ít quen điện thoại không chấm thấp hơn tuần 3 | Chưa đo |
| Che nhanh, máy dùng chung | Người dùng chung máy chấm từ 3,5; lo riêng tư không quá 3% | 3,47; 1,4% |
| Cả app sau tuần 4 | "Thấy được hiểu" từ 3,5 và hơn kế hoạch cũ ít nhất 0,6; "bình yên" từ 3,5; không loại hại nào quá 3% | Bản mô tả gói: 3,56; hơn 0,86; bình yên 3,61 |

## Tuần 5. Lá nhây (Mầm xanh) thay "Vibe"

Làm bằng code. Làm thật 4 động tác trước để đo, rồi làm tiếp tới 12 động tác.

| Việc | Mốc đạt | Hiện tại |
|---|---|---|
| Mầm xanh pixel ở màn đầu | Ít nhất 90% người giả để ý tới Lá; chấm Lá từ 4,0 | Chấm thử 20 người: 100%; 4,1 |
| Luật nhây | Thấy bị chọc, phán xét hay sai khiến không quá 5%; không có ca nào Lá nhây khi mood thấp, khi chọn "Chỉ cần được nghe", hay ở phần hỗ trợ | Chấm thử: 1 trên 20, đã bỏ câu gây ra |
| Bỏ nút giọng và nội dung Cà khịa | "Muốn quay lại" tăng ít nhất 0,15; "bình yên" không giảm quá 0,05 | Chấm thử: tăng 0,20; bình yên giảm 0,10, cần theo dõi |
| 4 động tác làm thật (đo trên máy, không dùng người giả) | Mỗi động tác không quá 8 KB; đứng yên khi máy bật giảm chuyển động; mỗi lần chạy không quá 5 giây; bấm được bằng bàn phím | Chưa đo |
| Thay Lá tím bằng Mầm xanh | Không còn màn nào hiện Lá tím | Chưa làm |

## Tuần 6. Học theo bạn, bản đầu

Gồm: 8 bài khớp với các món hay gặp trong ba lô; lời mời "Lá diễn hôm nay"; kiểu luyện chọn sẵn theo lá số của chính người dùng; thẻ "Bạn đáp câu nào?". Chị duyệt chữ từng bài.

| Việc | Mốc đạt | Hiện tại |
|---|---|---|
| Lối vào bài học ("Lá diễn hôm nay", dòng [Xem bài] trong ba lô) | Ít nhất 15% người giả mở một bài; riêng người chọn "Một bước đầu": ít nhất 40% | Chấm thử: 1 trên 20, trước khi sửa lối vào |
| 8 bài khớp chuyện trong ba lô | Người mở bài chấm từ 3,5 (mốc đã ghi trước); câu "thiếu một bước cụ thể để làm" giảm một nửa | Người duy nhất mở bài chấm 5; 125 câu trên 1000 |
| Kiểu luyện theo lá số | Thấy nói quá không quá 3%; ít nhất một phần ba người mở bài thấy đúng mình hơn | Chưa đủ số để nói |
| Thẻ "Bạn đáp câu nào?" | Chấm riêng: gửi hoặc rủ tăng ít nhất 5 điểm phần trăm | Chưa đo |
| An toàn nội dung | Không có nội dung ép buộc hay thao túng | Chưa đo |

## Tuần 7. Truyện ngắn, lời mở, sticker

| Việc | Mốc đạt | Hiện tại |
|---|---|---|
| Sticker Mầm xanh ở 3 chỗ | Ít nhất 20% người giả gặp sticker; gửi hoặc rủ của cả app từ 18% | 5,3% gặp; cả app 10,5%; chấm riêng tăng 40,7 điểm |
| Truyện ngắn 3 khung, 4 bản nhân vật | Ít nhất 10% mở; người đọc chấm từ 3,5; không có ca nào gặp truyện trùng với chuyện đang nặng | 3,3% mở; 3,12 |
| Lời mở có lối lui | Ít nhất 15% dùng; người dùng chấm "bớt một mình" từ 3,6; nhóm không có ai an toàn không tụt điểm | 8,5% dùng |

## Tuần 8. Khóa "Tán crush kiểu tử tế", mục Chơi

| Việc | Mốc đạt | Hiện tại |
|---|---|---|
| Khóa Tán crush, 7 bài | Trong nhóm đang nghĩ nhiều về một người: ít nhất 30% mở; chấm từ 3,5; không có cờ ép buộc hay thao túng | Chưa đo |
| Bộ chặn câu thao túng (đo trên máy) | Chặn 100% trong 60 câu mẫu (gây ghen, thử lòng, nhắn tiếp sau khi bị từ chối); không chặn nhầm câu dạy như "đừng theo dõi họ" | Bộ hiện có để lọt cả 3 câu thử |
| "Phụ đề khác nhau" và chuyện vui về tiền | Chạm nỗi buồn không quá 1% người chơi; 100% hiểu luật và biết dừng; chấm riêng gửi hoặc rủ tăng ít nhất 5 điểm | 1 trên 75; 75 trên 75; tăng 14,3 điểm |
| Lá Dám bằng thẻ giấy | Chơi thử với 2 nhóm bạn thật. Phần này không đo bằng người giả | Chưa làm |

## Tuần 9. Hai khóa còn lại, đủ bộ động tác, chấm tổng

Chấm đủ 1000 người, Codex đối chiếu.

| Việc | Mốc đạt | Hiện tại |
|---|---|---|
| Khóa "Kết bạn ở chỗ mới" | Nhóm năm nhất xa nhà và nhóm ở trọ chấm "bớt một mình" từ 3,5 | Cả app 3,24 |
| Khóa "Tự tin hơn" | Người mở bài chấm từ 3,5 | Chưa đo |
| 22 động tác còn lại, đủ 24 sticker | Giữ được các mốc Lá nhây của tuần 5 | — |
| Cả gói: 9 điều kiện đã ghi trước, giữ nguyên | Thấy được hiểu từ 3,7; bớt một mình và bình yên từ 3,5; bốn nhóm sinh viên yếu từ 3,5; gửi hoặc rủ từ 35%; mỗi loại hại không quá 3%; bình yên không tụt; hơn kế hoạch cũ ít nhất 0,2; người dùng chung máy và người không có ai an toàn từ 3,5; không ca lộ dữ liệu | Đạt 4 trên 9 (bản mô tả, chưa có Lá nhây và Học) |

## Đã hoãn hoặc chưa có trong kế hoạch

- **"Mời hẹn thử":** chị chốt chưa làm. Thiết kế giữ trong báo cáo.
- **Lá nhớ hoàn cảnh của người dùng:** đây là điều người giả muốn nhất (179 câu chê trên 1000). Chưa vào kế hoạch vì cần chị quyết về lưu dữ liệu. Hai cách "nhớ" đã thử gần như không nâng điểm và làm nhiều người lo riêng tư.
- **Lá Dám trong app, phòng chơi từ xa, ô viết "Kể ra rồi thả":** để sau 9 tuần.

## Điều người giả không đo được

- Người giả và giám khảo đều là AI đọc chữ. Chúng giúp tìm lỗi kịch bản và so hai bản với nhau.
- Chúng không chứng minh người thật thấy vui, sẽ chia sẻ hay sẽ quay lại. Mốc gửi hoặc rủ 35% đặc biệt khó tin nếu chỉ dựa vào người giả.
- Khi có người dùng thật, nên thay dần các mốc này bằng số đo thật.

## Chị cần duyệt

1. Các mốc đề xuất trong bản này. Chị muốn nâng hay hạ mốc nào thì sửa trước khi bắt đầu tuần đó.
2. Chấm 300 người mỗi tuần và đủ 1000 người ở tuần 4 và tuần 9. Mỗi lượt 1000 người mất hơn 2 giờ và tốn nhiều hạn mức sử dụng của tài khoản.
3. Câu đồng ý và chính sách quyền riêng tư cho việc dùng lá số trong Học, trước tuần 6.
