# Kế hoạch gộp 6 tuần qua 100 người giả (14.11.2026)

**Đây là đánh giá của mô hình AI trên mô tả bằng chữ.** Không phải người dùng thật, không phải code thật. Kế hoạch chưa được làm; đây là thử trước xem trải nghiệm kế hoạch hứa có đủ để đạt mốc hay không.

- Kế hoạch: `docs/reviews/2026-11-14-ke-hoach-trien-khai-gop.md` (bản 3).
- Mock hai mốc và biến thể hỏi lại: [merged-plan/mocks.md](merged-plan/mocks.md). Câu hỏi chấm: [merged-plan/judge-instructions.md](merged-plan/judge-instructions.md).
- 100 người giả hư cấu. Tình huống hôm nay giữ như lần chấm 8 ý (25 người mỗi loại: rất mệt, quay lại sau 2 tuần, điện thoại dùng chung, không có ai an toàn). Loại hồ sơ theo người giả: 30 chỉ ngày sinh, 20 giờ khoảng, 50 giờ và nơi chính xác.
- Giám khảo: 7 Claude subagent riêng, mù với ngưỡng và số nền, chấm 300 mục. Codex chấm độc lập 60 mục (20 người chọn đều theo nhóm, cùng mẫu lần trước).

## Đọc nhanh

- **Mốc tuần 4: đạt một nửa.** 65/100 người giả chấm "hiểu mình" từ 3 trở lên (cần ≥ 50), nhưng điểm trung bình 2,77 chưa tới 3,0. Gần như mọi điểm là 2, 3 hoặc 4; chỉ 12/100 người chấm 4, không ai chấm 5.
- **Đích tuần 6: đạt một nửa.** 76/100 người từ 3 trở lên (cần ≥ 70), trung bình 2,95 (cần 3,5). "Thấy bình yên" 3,49 và "bớt thấy một mình" 3,06, chưa tới 3,5.
- So với nền (2,23 và 11/100), mọi nhóm đều lên. Nhưng nền chấm trên nội dung thật, còn lần này chấm trên mock viết sẵn ví dụ tốt, nên mức tăng là **trần**, không phải số đo trước và sau.
- **4 nhóm sinh viên yếu:** chỉ nhóm vừa học vừa làm đạt 3 ở tuần 4 (3,38). Tiền eo hẹp đứng yên ở 2,67 cả hai mốc. Không nhóm nào tới 3,5 ở tuần 6.

## Điều kế hoạch làm được (trên mock)

- Tìm được chỗ chọn mood và đổi góc đọc 92/100; câu trái mood được sửa 100/100.
- Ai cũng thấy dừng được. 25/25 người quay lại sau 2 tuần không thấy bị trách, không thấy việc tồn.
- Chuyện minh họa: 100/100 hiểu là minh họa, 0 thấy bị hứa suông. Trò chơi: 100/100 hiểu cách chơi.
- 0 ca "phải xem Lá mới dám quyết", 0 ca phụ thuộc.

## Điều chưa đạt và vì sao

1. **Thấy việc nhỏ hợp sau khi đổi: 82/100 (cần 85).** Codex vẫn 11/20, đúng như lần trước (cần ≥ 17/20). Nhóm thiếu: nhóm khác 12/19, năm cuối / việc đầu 10/14, áp lực học 15/19, không có ai an toàn 14/25. Lời chê chung: "viết tên việc ra giấy" quá nhỏ so với việc họ đang gánh (đồ án, học phí, phỏng vấn).
2. **Không có góc đọc về tiền.** Năm góc đọc hiện có trong app là người thân, nói chuyện, việc học/làm, sức lực, chăm mình. PR 8 gắn nội dung vào các góc có sẵn, nên chuyện tiền không có chỗ. Nhóm tiền eo hẹp chê đúng điểm này.
3. **Tìm đúng đường: 79/100 (cần 90; Codex 14/20).** Người không có ai để tâm sự muốn **kể**, mà ba lối không có chỗ kể. Câu ví dụ trong mock "Đây không phải chỗ để kể chuyện hay trò chuyện" làm họ hụt hẫng thêm. Câu này do người viết mock đặt, kế hoạch chỉ ghi "nói rõ phần này giúp tới đâu".
4. **Phân biệt lý do với phần diễn giải: 84/100 (cần 90; Codex 9/20).** Câu dự phòng trung thực "theo vòng xoay, không dựa trên lá số" làm người tin chiêm tinh mà chỉ nhập ngày sinh thấy hụt ("vậy phần chiêm tinh để làm gì").
5. **Trò chơi chạm nỗi đau: 7/100 (cần 0).** Chuyện "cả nhà hẹn đi ăn" làm người xa nhà, nhà đang khó khăn tiền bạc, hoặc gia đình căng thấy chạnh. Chuyện này cũng do người viết mock đặt; bài học là cảnh gia đình vui không an toàn cho mọi người.
6. **Hỏi lại việc đã giữ: 15/100 thấy bị kiểm tra (cần ≤ 5; Codex 12/20).** Theo đúng kế hoạch, phần này **chưa xây trong đợt này**. Lời chê: "như bố mẹ kiểm tra bài", "giống sếp hỏi tiến độ".
7. **Riêng tư:** 7 người dùng chung máy lo vì câu thông báo hồ sơ hiện trên Trang chủ cho người cầm máy thấy là có hồ sơ.

## Claude và Codex lệch nhau ở đâu

- Trên cùng 20 người, điểm trung bình lệch tối đa 0,35 mỗi câu chấm; không người nào lệch điểm "hiểu mình" từ 2 trở lên.
- Codex khắt khe hơn ở ba chỗ: việc nhỏ hợp sau khi đổi (Codex 11/20), phân biệt lý do với diễn giải (9/20), tìm đúng đường (14/20). Theo kế hoạch, Claude đạt mà Codex trượt thì **chưa kết luận, phải chấm thêm**.
- Codex ghi "chưa hiểu cách chơi" cho 11/20 người chỉ vì họ không vào chơi. Đây là khác cách hiểu câu hỏi, không phải người giả hiểu nhầm trò chơi.

## Gợi ý chỉnh kế hoạch (suy ra từ lời chê, chưa thử lại)

1. Thêm nội dung về tiền. Cần owner quyết vì kế hoạch đang chỉ dùng các góc đọc có sẵn.
2. Viết lại dòng giải thích của "Gỡ một chuyện": nói nó làm được gì, không nói "không phải chỗ để kể". Cân nhắc dẫn người muốn hỏi sang "Hỏi Tarot".
3. Với người chỉ nhập ngày sinh: giữ câu dự phòng trung thực, thêm một lời mời nhập giờ sinh nếu muốn note dựa trên lá số.
4. Trò chơi: tránh cảnh gia đình sum họp, giữ cảnh trung tính (bạn bè, chỗ làm, đường phố).
5. Việc nhỏ cho người đang gánh việc lớn: thêm việc "bước đầu tiên của việc thật" (mở file, ghi một dòng), không chỉ việc nghỉ.

## Mục tiêu của kế hoạch đo được bằng mock

| Chỉ số | Nền (v1) | Mốc tuần 4 | Mock mốc A | Đích tuần 6 | Mock mốc B |
| --- | --- | --- | --- | --- | --- |
| Hiểu mình (trung bình) | 2,23 | ≥ 3,0 | 2,77 (trượt) | ≥ 3,5 | 2,95 (trượt) |
| Người giả có điểm hiểu mình ≥ 3 | 11/100 | ≥ 50 | 65/100 (đạt) | ≥ 70 | 76/100 (đạt) |
| Bớt thấy một mình | chưa có (lấy ở PR 0) | — | 2,84 | ≥ 3,5 và tăng ≥ 0,5 | 3,06 (trượt); chưa so được mức tăng |
| Thấy bình yên | chưa có (lấy ở PR 0) | — | 3,34 | ≥ 3,5 và tăng ≥ 0,5 | 3,49 (trượt); chưa so được mức tăng |
| Hiểu mình: Năm cuối tìm việc (8 người) | 2,25 | ≥ 3,0 | 2,62 (trượt) | ≥ 3,5 | 2,75 (trượt) |
| Hiểu mình: Tiền eo hẹp (6 người) | 2,21 | ≥ 3,0 | 2,67 (trượt) | ≥ 3,5 | 2,67 (trượt) |
| Hiểu mình: Áp lực gia đình (6 người) | 2,04 | ≥ 3,0 | 2,83 (trượt) | ≥ 3,5 | 3,17 (trượt) |
| Hiểu mình: Vừa học vừa làm (8 người) | 2,16 | ≥ 3,0 | 3,38 (đạt) | ≥ 3,5 | 3,25 (trượt) |
| Cờ 'phải xem Lá mới dám quyết' (mốc A) | chưa đo | 0 | 0 (đạt) | 0 |  |
| Cờ 'phải xem Lá mới dám quyết' (mốc B) | chưa đo | 0 |  | 0 | 0 (đạt) |

| Tiêu chí PR | Cần | Mốc A | Mốc B |
| --- | --- | --- | --- |
| PR 3: tìm đúng chỗ chọn mood và đổi góc đọc | ≥ 90% | 92/100 (đạt) | 93/100 (đạt) |
| PR 7: thấy việc nhỏ hợp sau khi đổi | ≥ 85% | 82/100 (trượt) | 81/100 (trượt) |
| PR 7: ca mâu thuẫn được sửa | 100% | 100/100 (đạt) | 100/100 (đạt) |
| PR 10: phân biệt lý do với phần diễn giải | ≥ 90% | 84/100 (trượt) | 84/100 (trượt) |
| PR 12: tìm đúng đường | ≥ 90% | 79/100 (trượt) | 82/100 (trượt) |
| PR 12: dừng được | 100% | 100/100 (đạt) | 100/100 (đạt) |
| PR 13: hiểu là chuyện minh họa | 100% | — | 100/100 (đạt) |
| PR 13: không thấy bị phủ nhận nỗi khó | 100% | — | 99/100 (trượt) |
| PR 13: không thấy bị hứa suông | 100% | — | 100/100 (đạt) |
| PR 14: hiểu cách chơi | ≥ 90% | — | 100/100 (đạt) |
| PR 14: dừng chơi được | 100% | — | 100/100 (đạt) |
| PR 14: không thấy bị chạm nỗi đau | 100% | — | 93/100 (trượt) |
| PR 12: quay lại sau 2 tuần không bị trách, không việc tồn (mốc A) | 100% | bị trách 0/25, việc tồn 0/25 (đạt) |  |
| PR 12: quay lại sau 2 tuần không bị trách, không việc tồn (mốc B) | 100% | bị trách 0/25, việc tồn 0/25 (đạt) |  |
| PR 7: mỗi nhóm ≥ 80% thấy hợp (mốc A) | mỗi nhóm | trượt: Nhóm khác 12/19, Năm cuối / việc đầu tiên 10/14, Áp lực học 15/19, Không có ai an toàn (tình huống) 14/25 |  |

### Biến thể hỏi lại việc đã giữ (chỉ xây nếu qua)

- Thấy bị kiểm tra: **15/100** (cần ≤ 5). Thấy bị ép: 0/100. Lo riêng tư: 9/100. Phụ thuộc: 0/100.
- Giúp mình 2,74, muốn quay lại 3,13.
- Sẽ bấm: useful 39, not_yet 28, skip 17, not_fit 12, none 4.
- Kết luận theo ngưỡng phần mock: **không qua**. Kế hoạch còn cần owner xác nhận mục đích lưu câu trả lời.
- Câu bị chỉ ra: 'Hôm qua bạn định thử Đi ngủ trước 12 giờ.' (3).

### Chỉ đo được bằng code

- Chống lặp 4 điều kiện qua 42 ngày, với cả 3 loại hồ sơ (PR 9): chỉ đo được bằng code.
- Lời của Lá lặp ≤ 20%, có ca một mood giữ suốt 42 ngày: chỉ đo được bằng code.
- Ngày 'Đuối' được việc nhẹ ≥ 90% (giám khảo độc lập chấm 48 việc rất nhẹ): chỉ đo được bằng code.
- Không câu nào trái mood qua mọi ngày (mock chỉ có một ca): chỉ đo được bằng code.
- Lớp khủng hoảng: bắt / báo nhầm / không bài đọc / không lưu / không log / đúng câu: chỉ đo được bằng code.
- Database: không bảng, cột hay bản ghi mới sau khi chọn góc đọc hoặc lối vào (PR 7, 8, 12): chỉ đo được bằng code.
- PR 2: 0 lời mời đăng nhập ở mọi màn; câu thông báo đúng nguyên văn (mã băm): chỉ đo được bằng code.
- PR 4: nút 'Giữ' và nút đóng bấm trọn ở khổ 390 px và nhỏ hơn: chỉ đo được bằng code.
- PR 7: ≤ 2 thao tác và ≤ 70 chữ trước khi thấy việc nhỏ (mock được viết để đạt, phải đo trên giao diện): chỉ đo được bằng code.
- PR 12: lượt mở 30 giây không bị chặn: chỉ đo được bằng code.
- Quay lại sau 7 / 28 ngày (mô hình, chỉ tham khảo): chỉ đo được bằng code.

## Theo nhóm người giả

| Nhóm | Người | Hiểu mình: nền | A | B | Bớt một mình B | Bình yên B | Muốn quay lại B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Người đi làm trẻ | 19 | 2,16 | 2,95 | 2,95 | 2,95 | 3,58 | 3,26 |
| Nhóm khác | 19 | 2,16 | 2,42 | 2,53 | 3,00 | 3,53 | 3,21 |
| Năm cuối / việc đầu tiên | 14 | 2,30 | 2,79 | 3,00 | 3,07 | 3,43 | 3,21 |
| Năm nhất xa nhà | 15 | 2,28 | 2,67 | 3,27 | 3,33 | 3,33 | 3,53 |
| Vừa học vừa làm | 14 | 2,18 | 3,07 | 3,00 | 3,07 | 3,57 | 3,43 |
| Áp lực học | 19 | 2,29 | 2,79 | 3,05 | 3,00 | 3,47 | 3,26 |
| Không có ai an toàn (tình huống) | 25 | 2,16 | 2,40 | 2,64 | 2,88 | 3,40 | 3,08 |

## Theo hoàn cảnh chi tiết

| Nhóm | Người | Hiểu mình: nền | A | B | Bớt một mình B | Bình yên B | Muốn quay lại B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Cha mẹ có con nhỏ | 5 | 2,30 | 3,00 | 3,00 | 3,00 | 3,80 | 3,60 |
| Công việc đầu tiên | 6 | 2,38 | 3,00 | 3,33 | 3,33 | 3,67 | 3,50 |
| Deadline dày | 7 | 2,29 | 2,71 | 2,71 | 3,00 | 3,71 | 3,29 |
| Làm theo ca | 6 | 2,00 | 3,17 | 3,17 | 2,83 | 3,67 | 3,33 |
| Người LGBTQ+ | 5 | 2,20 | 2,40 | 2,60 | 3,00 | 3,80 | 3,20 |
| Người lớn tuổi | 5 | 2,00 | 2,20 | 2,40 | 3,00 | 3,20 | 3,20 |
| Năm cuối, đang tìm việc | 8 | 2,25 | 2,62 | 2,75 | 2,88 | 3,25 | 3,00 |
| Sinh viên năm nhất xa nhà | 8 | 2,38 | 2,62 | 3,25 | 3,50 | 3,38 | 3,50 |
| So sánh trên mạng xã hội | 5 | 2,55 | 2,80 | 3,20 | 3,00 | 3,60 | 3,20 |
| Tiền eo hẹp | 6 | 2,21 | 2,67 | 2,67 | 3,00 | 3,17 | 3,00 |
| Vừa học vừa làm thêm | 8 | 2,16 | 3,38 | 3,25 | 3,12 | 3,88 | 3,75 |
| Áp lực gia đình | 6 | 2,04 | 2,83 | 3,17 | 3,00 | 3,17 | 3,00 |
| Áp lực từ sếp | 6 | 2,17 | 3,00 | 3,00 | 3,00 | 3,33 | 3,17 |
| Ít quen dùng điện thoại | 4 | 2,12 | 2,00 | 2,00 | 3,00 | 3,25 | 2,75 |
| Đang mùa thi | 8 | 2,31 | 2,75 | 2,88 | 3,00 | 3,62 | 3,50 |
| Ở ký túc xá / phòng trọ | 7 | 2,18 | 2,71 | 3,29 | 3,14 | 3,29 | 3,57 |

## Theo loại hồ sơ

| Nhóm | Người | Hiểu mình: nền | A | B | Bớt một mình B | Bình yên B | Muốn quay lại B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chỉ ngày sinh | 30 | 2,32 | 2,60 | 2,93 | 3,07 | 3,47 | 3,20 |
| Giờ khoảng | 20 | 2,08 | 2,80 | 3,00 | 3,05 | 3,40 | 3,20 |
| Giờ và nơi chính xác | 50 | 2,23 | 2,86 | 2,94 | 3,06 | 3,54 | 3,42 |

## Theo tình huống hôm nay

| Nhóm | Người | Hiểu mình: nền | A | B | Bớt một mình B | Bình yên B | Muốn quay lại B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Rất mệt | 25 | 2,38 | 3,36 | 3,36 | 3,00 | 3,88 | 3,52 |
| Quay lại sau 2 tuần | 25 | 2,25 | 2,52 | 2,88 | 3,24 | 3,36 | 3,28 |
| Điện thoại dùng chung | 25 | 2,11 | 2,80 | 2,92 | 3,12 | 3,32 | 3,36 |
| Không có ai an toàn | 25 | 2,16 | 2,40 | 2,64 | 2,88 | 3,40 | 3,08 |

Lượt nền không có tình huống hôm nay; cột nền ở bảng này và dòng 'Không có ai an toàn' là điểm nền của chính những người giả đó.

## Theo mức tin chiêm tinh

| Nhóm | Người | Hiểu mình: nền | A | B | Bớt một mình B | Bình yên B | Muốn quay lại B |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Tin chiêm tinh | 27 | 2,19 | 2,67 | 2,85 | 3,04 | 3,44 | 3,37 |
| Nửa tin | 45 | 2,26 | 2,96 | 3,16 | 3,16 | 3,64 | 3,56 |
| Không tin | 28 | 2,21 | 2,57 | 2,71 | 2,93 | 3,29 | 2,86 |

## 3 nhóm vẫn thấp nhất ở mốc B (theo hiểu mình)

**Ít quen dùng điện thoại** (4 người): hiểu mình 2,00 (nền 2,12), bớt một mình 3,00, bình yên 3,25, muốn quay lại 2,75.

- "Chuyện ông về hưu ngồi không, còn bà thì ngày nào cũng ra vườn, chẳng giống mình."
- "Thêm chuyện với trò chơi, tôi chỉ cần một câu ngắn chữ to."
- "Lá không nhớ chuyện tôi kể, nói ai cũng như ai."

**Người lớn tuổi** (5 người): hiểu mình 2,40 (nền 2,00), bớt một mình 3,00, bình yên 3,20, muốn quay lại 3,20.

- "Chuyện ngắn với note không có gì về người còn làm tiệm, đọc thấy không phải chuyện của mình."
- "Chuyện ngắn kể bác về hưu nhà vắng, còn cô thì trông cháu cả ngày."
- "Không có xem ngày tốt xấu, cũng không ai hỏi han chuyện của tôi."

**Người LGBTQ+** (5 người): hiểu mình 2,60 (nền 2,20), bớt một mình 3,00, bình yên 3,80, muốn quay lại 3,20.

- "Không có chỗ nào ghi lại tâm trạng của mình, chỉ bấm mood rồi thôi."
- "Đọc thì nhẹ nhưng đổi tên ai cũng hợp, app không nhớ gì về mình."
- "Không có ai để kể mà app nói rõ không phải chỗ để kể chuyện hay trò chuyện."

## Cờ và câu bị chỉ ra

- Mốc A: bị trách 0, bị ép 2, lo riêng tư 8, phụ thuộc 0, phải xem Lá mới dám quyết 0.
  - bị ép: 'Viết tên việc đó ra giấy. Chỉ viết tên, chưa cần làm.' (2)
  - lo riêng tư: 'Hồ sơ của bạn đang lưu trên trình duyệt này.' (7); 'Giữ thì việc hiện lại trên Trang chủ trong ngày đó.' (1)
- Mốc B: bị trách 0, bị ép 4, lo riêng tư 8, phụ thuộc 0, phải xem Lá mới dám quyết 0.
  - bị ép: 'Hôm nay bạn đang có sức, thử thêm một việc' (2); 'Viết tên việc đó ra giấy. Chỉ viết tên, chưa cần làm.' (1)
  - lo riêng tư: 'Hồ sơ của bạn đang lưu trên trình duyệt này.' (7); 'Giữ thì việc hiện lại trên Trang chủ trong ngày đó.' (1)

## Codex so với Claude trên cùng 20 người giả

| Mục | Claude | Codex | Lệch TB / người |
| --- | --- | --- | --- |
| Hiểu mình (mốc A) | 2,45 | 2,75 | 0,50 |
| Bớt thấy một mình (mốc A) | 2,90 | 3,00 | 0,10 |
| Thấy bình yên (mốc A) | 3,20 | 3,50 | 0,50 |
| Muốn quay lại (mốc A) | 2,95 | 2,65 | 0,30 |
| Hiểu mình (mốc B) | 2,80 | 2,70 | 0,50 |
| Bớt thấy một mình (mốc B) | 3,05 | 3,20 | 0,25 |
| Thấy bình yên (mốc B) | 3,25 | 3,45 | 0,50 |
| Muốn quay lại (mốc B) | 3,10 | 2,75 | 0,35 |

- Codex: thấy việc nhỏ hợp sau khi đổi (mốc A) **11/20**. Kế hoạch cần từ 11/20 lên ≥ 17/20.
- Codex, biến thể hỏi lại: thấy bị kiểm tra 12/20, giúp 1,50.
- Mốc A: câu kiểm trả lời ngược nhau: `found_right_path` 8, `reason_vs_interpretation_clear` 5, `fits_after_change` 4, `found_mood_and_angle` 3, `profile_notice_clear` 2. Lệch điểm hiểu mình từ 2 trở lên: không có.
  - Cờ trên 20 người: Codex bị trách 1, bị ép 0, lo riêng tư 2, phụ thuộc 0, phải xem Lá mới dám quyết 0; Claude bị trách 0, bị ép 1, lo riêng tư 2, phụ thuộc 0, phải xem Lá mới dám quyết 0.
- Mốc B: câu kiểm trả lời ngược nhau: `game_understood` 11, `game_could_stop` 11, `fits_after_change` 7, `found_right_path` 7, `reason_vs_interpretation_clear` 5, `game_hurt` 2, `found_mood_and_angle` 2, `profile_notice_clear` 2, `story_denied_difficulty` 1. Lệch điểm hiểu mình từ 2 trở lên: không có.
  - Cờ trên 20 người: Codex bị trách 1, bị ép 1, lo riêng tư 2, phụ thuộc 0, phải xem Lá mới dám quyết 0; Claude bị trách 0, bị ép 3, lo riêng tư 2, phụ thuộc 0, phải xem Lá mới dám quyết 0.
- Vài lời chê của Codex (mốc B):
  - "Mình năm ba rồi, chuyện mới vào trường chỉ giống mỗi đoạn ngồi một mình."
  - "Hôm nay thêm chuyện để đọc cũng chỉ làm mình ngại đọc hơn."
  - "Mình đang rối vì chuyện nhà mà vẫn chỉ chọn được một nhóm chuyện rộng quá."

## Giới hạn

- Người giả và giám khảo đều là mô hình AI. Giám khảo đọc mô tả bằng chữ, không dùng app thật và không có code thật. Điểm cho biết hướng, không chứng minh người thật thấy được hiểu hay quay lại.
- Số nền 2,23 được chấm trên **nội dung thật từng ngày** do app sinh ra. Điểm mới chấm trên **mock**, nơi người viết mock chọn ví dụ tốt. Hai con số khác công cụ đo, nên mức tăng là giới hạn trên của điều kế hoạch có thể mang lại, không phải số đo trước-sau.
- Nhãn mood, nhãn góc đọc và nội dung note trong mock là ví dụ; kế hoạch chưa chốt chúng. Kết quả phụ thuộc nhiều vào chất lượng câu thật sau này.
- 'Bớt thấy một mình' và 'thấy bình yên' chưa có số nền (kế hoạch lấy nền ở PR 0), nên chỉ so được với mức 3,5, chưa so được điều kiện tăng ≥ 0,5.
- Mỗi người giả chỉ chấm một tình huống hôm nay. Nhóm người lớn tuổi chỉ có 5 người.
- Giám khảo có thể chấm dễ hơn khi thấy mock viết cẩn thận. Codex chấm đối chiếu 20 người để bắt chỗ này.
