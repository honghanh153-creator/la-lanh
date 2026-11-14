# Gói concept sáng tạo, lan truyền: chấm trên 1000 người giả (14.11.2026)

**Mô phỏng trên người giả, giám khảo là mô hình AI, chấm trên mô tả bằng chữ.** Không phải người dùng thật, không phải code thật. 1000 người giả không phải 1000 quan sát độc lập. Mock là mức trần.

- Ngưỡng ghi trước: `thresholds-1000.md` mục 6 (bản 1 + bản 2).
- Mỗi người giả đọc hai bản gọi là X và Y; nhãn và thứ tự đọc cân bằng giữa các lô. Giám khảo viết đường bấm trước rồi mới chấm.
- Gói: 1000 cặp. Từng concept: 910 cặp. Phần thử có điều kiện (S2, S11, S12): 270 cặp. Codex: 40 cặp.

## Tóm tắt dễ đọc

- **Gói làm người giả thấy được hiểu hơn rõ rệt** so với đối chứng (Mốc B), nhưng **chưa tới ngưỡng 3,7**. Bình yên và muốn quay lại cũng tăng; không có cờ hại nào vượt 3%. Điều kiện an toàn (5) chỉ trượt vì 1 trong 75 người chơi trò chơi thấy chạm nỗi đau.
- **Chia sẻ vẫn thấp**: khoảng 1 trong 10 người gửi, đăng hoặc rủ ai đó. Ngưỡng ghi trước là 35%.
- **Người dùng chung máy** vẫn dưới ngưỡng hiểu mình 3,5. Người không có ai an toàn thì đạt.
- **Concept góp nhiều nhất là S1 (ba lô gánh hôm nay)**. S5 (chọn góc đọc) được dùng nhiều nhất, góp vừa vào "hiểu mình" và kéo chia sẻ lên. S10 (sticker) và S6 kéo chia sẻ lên nhưng ít người dùng.
- **S4, S8 gần như không ai dùng** trong gói.

## Người giả còn muốn gì (đếm từ câu chê và câu "còn thiếu" của 1000 người, một câu có thể thuộc nhiều nhóm)

| Điều còn thiếu | Số câu chê | Số câu "còn thiếu" |
|---|---|---|
| Lá nhớ hoàn cảnh, nhớ lần trước | 179 | 190 |
| Một bước cụ thể để làm | 68 | 125 |
| Hợp với ca làm, giờ giấc | 81 | 96 |
| Được hỏi lại, được trò chuyện | 73 | 73 |
| Chuyện tiền | 61 | 64 |
| Nhớ nhà, xa quê | 59 | 57 |
| Hợp người lớn tuổi | 13 | 52 |
| Bố mẹ, gia đình | 37 | 30 |
| Sếp, chỗ làm | 34 | 28 |

Các câu cụ thể hay gặp: ba lô chưa có món "áp lực từ sếp"; câu chuyện ngắn (S4) thiếu người lớn tuổi và sinh viên năm nhất; người ít quen điện thoại thấy trang chủ của gói nhiều thứ hơn.

## Ghi chú cách chạy

- Mock v6 (bản cuối của phiên concept), chép vào `qa/personas/concepts/mocks-v6.md`.
- Mock của gói có một chỗ nhắc tới S12 ("xem S12 nếu muốn Lá nhớ") trong phần S1. Codex đã chấm thêm khóa S12 cho gói; không ai dùng, nên khóa đó được bỏ trước khi tính.

## Lô chấm bù

- Hết hạn mức sử dụng lúc 20:25 làm dừng hai lô thử có điều kiện S2-02 và S12-03. Hai lô này đã được chấm bù sau 22:50 bằng cùng hướng dẫn chấm; báo cáo này đã đủ mọi lô.

## Gói đề xuất so với đối chứng: 9 điều kiện

| # | Điều kiện | Kết quả | |
|---|---|---|---|
| 1 | Hiểu mình của gói ≥ 3,7 | 3,56 | trượt |
| 2 | Bớt một mình ≥ 3,5 và bình yên ≥ 3,5 | 3,24 / 3,61 | trượt |
| 3 | 4 nhóm sinh viên yếu, mỗi nhóm ≥ 3,5 | Năm cuối tìm việc 3,87; Tiền eo hẹp 4,11; Áp lực gia đình 3,93; Vừa học vừa làm 3,55 | đạt |
| 4 | Gửi/đăng hoặc rủ ≥ 35% và nêu cụ thể ≥ 30% | 10,5% / 10,5% | trượt |
| 5 | Mỗi cờ hại ≤ 3%; trò chơi chạm nỗi đau ≤ 1% người đã chơi; 0 nội dung nguy hiểm | bị trách 0,0%, bị ép 0,0%, lo riêng tư 1,4%, phụ thuộc 0,0%, phải xem Lá mới dám quyết 0,1%; đau 1/75; nguy hiểm 0 | trượt |
| 6 | Bình yên không tụt so với đối chứng (chênh ≥ -0,05) | 0,37 | đạt |
| 7 | Hiểu mình cao hơn đối chứng ≥ +0,2 (theo cặp) | 0,86 | đạt |
| 8 | Dùng chung máy và không có ai an toàn: hiểu mình ≥ 3,5; không tụt quá 0,05 | Dùng chung máy (107): hiểu mình 3,47, chênh bình yên 0,41, chênh bớt một mình 0,26; Không có ai an toàn (222): hiểu mình 3,77, chênh bình yên 0,53, chênh bớt một mình 0,89 | trượt |
| 9 | Lộ dữ liệu riêng đã xác nhận: 0 ca | 0 | đạt |

**Gói chưa đạt** (4/9 điều kiện).

| | Hiểu mình | Bớt một mình | Bình yên | Muốn quay lại | Tuần sau quay lại | Muốn chia sẻ |
|---|---|---|---|---|---|---|
| Đối chứng | 2,70 | 2,86 | 3,23 | 2,94 | 2,88 | 1,10 |
| Gói | 3,56 | 3,24 | 3,61 | 3,64 | 3,54 | 1,43 |

- Đối chứng: lưu ảnh 0,2%, gửi/đăng 0,1%, rủ một người 0,1%; chơi trò chơi 119; cờ bị trách 0, bị ép 2, lo riêng tư 35, phụ thuộc 0, phải xem Lá mới dám quyết 0
- Gói: lưu ảnh 10,8%, gửi/đăng 7,8%, rủ một người 3,0%; chơi trò chơi 75; cờ bị trách 0, bị ép 0, lo riêng tư 14, phụ thuộc 0, phải xem Lá mới dám quyết 1
- Thứ tự đọc, đọc đối chứng trước (500): chênh hiểu mình 0,80
- Thứ tự đọc, đọc gói trước (500): chênh hiểu mình 0,91
- Phân bố hiểu mình 1/2/3/4/5: đối chứng 0/338/623/39/0; gói 0/37/380/570/13.

## Từng concept

| Concept | Dùng trong gói | Hiểu mình của người dùng (gói) | Chia sẻ từ concept (gói) | Riêng lẻ: chênh hiểu mình | Riêng lẻ: chênh gửi/rủ | Riêng lẻ: cờ hại | Giữ? |
|---|---|---|---|---|---|---|---|
| S1 | 531/1000 | 3,77 | 25 | 0,66 (91 cặp) | +5,5 điểm % | 1 | giữ |
| S3 | 260/1000 | 3,38 | 0 | 0,56 (91 cặp) | +3,3 điểm % | 3 | chưa |
| S4 | 33/1000 | 3,12 | 0 | 0,18 (91 cặp) | +0,0 điểm % | 3 | chưa |
| S5 | 568/1000 | 3,22 | 38 | 0,35 (91 cặp) | +12,1 điểm % | 1 | chưa |
| S6 | 26/1000 | 3,46 | 25 | 0,01 (91 cặp) | +14,3 điểm % | 0 | chưa |
| S7 | 159/1000 | 3,50 | 0 | 0,04 (91 cặp) | +3,3 điểm % | 5 | chưa |
| S8 | 4/1000 | 3,00 | 4 | 0,00 (91 cặp) | +9,9 điểm % | 4 | chưa |
| S9 | 85/1000 | 3,27 | 3 | 0,38 (91 cặp) | +8,8 điểm % | 6 | chưa |
| S10 | 53/1000 | 3,23 | 51 | 0,00 (91 cặp) | +40,7 điểm % | 5 | chưa |
| S13 | 251/1000 | 3,37 | 0 | 0,16 (91 cặp) | +0,0 điểm % | 1 | chưa |

## Phần thử có điều kiện (không tính vào điểm gói)

- S2 (90 cặp, so với gói): chênh hiểu mình 0,08, chênh bình yên 0,24, cờ lo riêng tư 2, lộ dữ liệu 0.
- S11 (90 cặp, so với gói): chênh hiểu mình 0,12, chênh bình yên -0,06, cờ lo riêng tư 15, lộ dữ liệu 0.
- S12 (90 cặp, so với gói): chênh hiểu mình 0,24, chênh bình yên -0,03, cờ lo riêng tư 9, lộ dữ liệu 0.

## Codex chấm đối chiếu (40 người giả, chọn đều theo nhóm)

| # | Điều kiện | Codex | |
|---|---|---|---|
| 1 | Hiểu mình của gói ≥ 3,7 | 3,55 | trượt |
| 2 | Bớt một mình ≥ 3,5 và bình yên ≥ 3,5 | 3,50 / 3,95 | đạt |
| 3 | 4 nhóm sinh viên yếu, mỗi nhóm ≥ 3,5 | Năm cuối tìm việc 4,00; Tiền eo hẹp 4,50; Áp lực gia đình 4,00; Vừa học vừa làm 3,50 | đạt |
| 4 | Gửi/đăng hoặc rủ ≥ 35% và nêu cụ thể ≥ 30% | 12,5% / 12,5% | trượt |
| 5 | Mỗi cờ hại ≤ 3%; trò chơi chạm nỗi đau ≤ 1% người đã chơi; 0 nội dung nguy hiểm | bị trách 0,0%, bị ép 0,0%, lo riêng tư 5,0%, phụ thuộc 0,0%, phải xem Lá mới dám quyết 2,5%; đau 0/1; nguy hiểm 0 | trượt |
| 6 | Bình yên không tụt so với đối chứng (chênh ≥ -0,05) | 0,23 | đạt |
| 7 | Hiểu mình cao hơn đối chứng ≥ +0,2 (theo cặp) | 0,62 | đạt |
| 8 | Dùng chung máy và không có ai an toàn: hiểu mình ≥ 3,5; không tụt quá 0,05 | Dùng chung máy (1): hiểu mình 3,00, chênh bình yên 0,00, chênh bớt một mình 1,00; Không có ai an toàn (12): hiểu mình 4,00, chênh bình yên 0,83, chênh bớt một mình 1,00 | trượt |
| 9 | Lộ dữ liệu riêng đã xác nhận: 0 ca | 0 | đạt |

Trên cùng người giả: chênh hiểu mình (gói trừ đối chứng) Claude 0,85, Codex 0,62. Điều kiện Claude đạt mà Codex trượt ghi là **chưa kết luận**.

## Giới hạn

- Người giả và giám khảo là mô hình AI, đọc chữ. Kết quả là mức trần.
- Mỗi người giả chấm một ngày với một tình huống; nhóm nhỏ dưới 20 người ghi mẫu nhỏ.
- Giám khảo thấy hai bản cùng lúc; gói có nhiều phần hơn nên có thể được cộng điểm vì mới. Thiết kế giảm bằng nhãn trung tính, thứ tự cân bằng, và chấm từng concept riêng.
