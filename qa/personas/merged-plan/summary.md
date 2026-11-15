## Đọc nhanh

- **Mốc tuần 4: đạt một nửa.** 65/100 người giả chấm "hiểu mình" từ 3 trở lên (cần ≥ 50), nhưng điểm trung bình 2,77 chưa tới 3,0. Gần như mọi điểm là 2, 3 hoặc 4; chỉ 12/100 người chấm 4, không ai chấm 5.
- **Đích tuần 6: đạt một nửa.** 76/100 người từ 3 trở lên (cần ≥ 70), trung bình 2,95 (cần 3,5). "Thấy bình yên" 3,49 và "bớt thấy một mình" 3,06, chưa tới 3,5.
- So với nền (2,23 và 11/100), mọi nhóm đều lên. Nhưng nền chấm trên nội dung thật, còn lần này chấm trên mock viết sẵn ví dụ tốt, nên mức tăng là **trần**, không phải số đo trước và sau.
- **4 nhóm sinh viên yếu:** chỉ nhóm vừa học vừa làm đạt 3 ở tuần 4 (3,38). Tiền eo hẹp đứng yên ở 2,67 cả hai mốc. Không nhóm nào tới 3,5 ở tuần 6.

## Điều kế hoạch làm được (trên mock)

- Tìm được chỗ chọn mood và đổi góc đọc 92/100; câu trái mood được sửa 100/100.
- Ai cũng thấy dừng được. 25/25 người quay lại sau 2 tuần không thấy bị trách, không thấy việc tồn.
- Chuyện minh họa: 100/100 hiểu là minh họa, 0 thấy bị hứa suông. Trò chơi: 67/67 người đã vào chơi hiểu cách chơi và dừng được (33 người không vào chơi: không áp dụng).
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
- Bản đầu, Codex ghi "chưa hiểu cách chơi" và "không dừng được" cho 11/20 người chỉ vì họ không vào chơi. Theo cách chấm v2, hai câu này chỉ tính cho người đã vào chơi: Codex 9/9 đạt cả hai, Claude 67/67 đạt cả hai. Hết lệch.
- **Codex chấm lại riêng phần trò chơi theo cách chấm v2** (1 lượt owner cấp thêm, cùng 20 người; câu hỏi: [judge-game-v2.md](merged-plan/judge-game-v2.md), kết quả: `merged-plan/judged/out-codex-game-v2.json`). Lần này Codex tự quyết ai vào chơi: 8/20 vào chơi. Cả 8 hiểu cách chơi và dừng được, nên PR 14 đạt hai tiêu chí này. Nhưng **3/8 thấy bị chạm nỗi đau**, cả ba chỉ đúng câu "Cả nhà hẹn tối nay đi ăn.": một sinh viên ở ký túc xá xa nhà, một bạn năm nhất có bố mẹ làm ca nên cuối tuần ít gặp, một người LGBTQ+ mà gia đình chưa biết chuyện của mình. Kết quả này củng cố điểm 5 ở trên. Giám khảo Claude chỉ gắn cờ này cho 1 trong 20 người đó.
- Ai vào chơi là chuyện phán đoán: lượt chấm lại của Codex khớp lượt đầu của Codex ở 13/20 người, khớp Claude ở 11/20. Vì vậy hai câu về trò chơi phải tính trên người đã vào chơi, không tính trên cả 100 người.
- **Một cờ "bị trách" của Codex** (người giả P027, cả hai mốc, cùng một câu): "Việc treo lâu thường nặng hơn khi nghĩ tới so với khi làm." Người này là sinh viên năm cuối đang làm khóa luận và đi phỏng vấn, không có ai để tâm sự. Đọc câu đó, họ hiểu là Lá cho rằng việc chỉ nặng vì mình nghĩ nhiều, trong khi việc của họ khó thật. Lời chê: "Khóa luận với bài tuyển dụng khó thật, nói như mình chỉ nghĩ nhiều nên thấy nặng thì khó chịu." Giám khảo Claude không gắn cờ này cho P027. Câu này là ví dụ trong mock, không phải câu kế hoạch đã chốt. Bài học cho kho câu: lời của Lá không ngụ ý nỗi khó là do người dùng tự nghĩ ra.

## Gợi ý chỉnh kế hoạch (suy ra từ lời chê, chưa thử lại)

1. Thêm nội dung về tiền. Cần owner quyết vì kế hoạch đang chỉ dùng các góc đọc có sẵn.
2. Viết lại dòng giải thích của "Gỡ một chuyện": nói nó làm được gì, không nói "không phải chỗ để kể". Cân nhắc dẫn người muốn hỏi sang "Hỏi Tarot".
3. Với người chỉ nhập ngày sinh: giữ câu dự phòng trung thực, thêm một lời mời nhập giờ sinh nếu muốn note dựa trên lá số.
4. Trò chơi: tránh cảnh gia đình sum họp, giữ cảnh trung tính (bạn bè, chỗ làm, đường phố).
5. Việc nhỏ cho người đang gánh việc lớn: thêm việc "bước đầu tiên của việc thật" (mở file, ghi một dòng), không chỉ việc nghỉ.
