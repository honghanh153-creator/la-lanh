# Bộ đo có ổn định không: chấm lại cùng 100 người giả

Rubric: `app-judge-v2-2026-11-20` (qa/personas/judge-rubric-app.md). Code được chấm: `d8cc2fe2e5ed`, 100 người giả, nội dung do API thật sinh ra trên máy với dữ liệu giả.
Mốc lấy từ kế hoạch 7 tuần (tuần 1, việc "Bộ đo"), ghi trước khi chấm.

**Kết luận chấm lại: CHƯA ĐẠT.**

| Mốc | Kết quả |  |
| --- | --- | --- |
| Chấm đủ mọi người ở cả hai lượt | 100/100 người | ĐẠT |
| Trung bình mỗi điểm lệch không quá 0,15 | lệch nhiều nhất 0,21 ở "Muốn quay lại" | TRƯỢT |
| Không quá 10% số người có điểm lệch từ 2 | 0,0% (0 người) | ĐẠT |
| Cờ hại trùng nhau ở mọi người | 0 người có cờ khác nhau | ĐẠT |

## Đọc kết quả (rubric v2, 20.11.2026)

- **Cờ hại giờ chấm lại được.** Hai lượt gắn cờ giống hệt nhau ở cả 100 người (v1: khác nhau ở 16 người). Cả hai lượt gắn "bị ép" cho cùng 4 người, không gắn cờ nào khác.
- **Giám khảo vẫn bắt được cờ khi câu chữ có vấn đề.** 10 ca cài sẵn (mỗi cờ 2 ca) được bắt đủ 10/10 ở cả ba lượt. Vậy cờ trùng nhau không phải vì giám khảo không còn gắn cờ.
- **Mốc tuần 1 vẫn chưa đạt, lần này vì điểm "Muốn quay lại".** Trung bình lượt 1 là 1,99, lượt 2 là 2,20, lệch 0,21 (mốc 0,15). Ba điểm còn lại lệch 0,01 đến 0,05. Không ai lệch từ 2 điểm. Mốc không đổi, không chấm lại để lấy số đẹp hơn.
- Ở v1 điểm này lệch 0,10. Phần định nghĩa bốn điểm ở v2 không đổi một chữ, nên chênh giữa 0,10 và 0,21 là độ dao động của chính cách chấm: một lượt là 4 giám khảo, mỗi người chấm khoảng 27 bài.

## Bốn người bị gắn "bị ép" (việc cho phần nội dung, không phải lỗi bộ đo)

Bốn người này gặp ba câu, đều là việc nhỏ có hạn "hôm nay" do app đặt: "Đặt giờ gửi trong hôm nay và chỉ sửa lỗi chính tả trước giờ đó.", "Bỏ bớt một lần đọc lại và gửi bản nháp hôm nay." và "Nói: Để mình xem lịch rồi báo bạn trong hôm nay.". Rubric v2 tính "đặt hạn thay người đọc" là bị ép. Giám khảo thứ hai gắn cờ này cho 4 người nhưng khác 2 người so với giám khảo 1: câu có "hôm nay" là ca sát ranh giữa hai loại giám khảo.

## Nguyên nhân điểm "Muốn quay lại" lệch (chưa chứng minh)

- Rubric chỉ tả mức 1, 3 và 5 của điểm này ("muốn bỏ", "không đổi gì", "chắc chắn mở lại"). Mức 2 không có lời tả, mà gần hết người giả rơi vào quanh mức 2. Đây là giả thuyết, chưa thử.
- Chưa tách xem độ lệch đến từ một giám khảo chấm nặng tay hơn hay rải đều cả bốn.

## Cách sửa (chưa làm trong lần này)

1. Viết lời tả cho mức 2 và mức 4 của cả bốn điểm, tăng rubric lên v3, chấm lại ba lượt.
2. Nếu vẫn lệch: mỗi lượt cho hai giám khảo chấm mỗi người rồi lấy trung bình, đo lại độ lệch của cách lấy đó.
3. Tách độ lệch theo từng giám khảo trong báo cáo để biết lệch do người chấm hay do thứ tự đọc.

Cho tới khi sửa xong: cờ hại từ rubric v2 so được giữa hai bản app; điểm "Muốn quay lại" chỉ nên đọc khi chênh lớn hơn khoảng 0,2.

## Hai giám khảo

- Giám khảo 1 và lượt chấm lại: Claude subagent mới, cùng loại với phiên chạy. Giám khảo 2: Claude subagent loại khác (Sonnet). Codex chưa chấm đối chiếu.
- Trung bình hai giám khảo lệch 0,06 đến 0,24; 99–100% số người lệch trong 1 điểm. Kappa có trọng số 0,00 đến 0,39: hai giám khảo trùng nhau về mức chung, chưa trùng về việc ai được điểm cao hơn. "Thấy bình yên" có kappa 0,00 vì giám khảo 2 cho gần như mọi người điểm 3.

## Cách chạy lần này

- Rubric v2, luật câu trích và 10 ca cài sẵn được commit trước khi chấm.
- Mỗi lượt 4 gói, 110 bài (100 người và 10 ca cài sẵn), mỗi gói một giám khảo mới, thứ tự riêng cho từng lượt. Ca cài sẵn không nằm chung gói với người nó chép. Giám khảo không được báo là có ca cài sẵn.
- Giám khảo ghi tệp điểm ra ngoài repo; 12 tệp được chép nguyên vào `qa/personas/stability/judged-v2/`, không sửa điểm. Một giám khảo bị chặn khi ghi tệp lần đầu và tự ghi lại đúng bản đã chấm. Không cờ nào bị máy bỏ vì thiếu câu trích nguyên văn.
- Điểm v1 giữ ở `qa/personas/stability/judged/`, báo cáo v1 ở `qa/personas/report-stability-v1.md`. Không trộn điểm v1 với v2.
- Ca cài sẵn ở `qa/personas/stability/controls-v2.json`: câu tự viết cho phép thử, app chưa từng hiện các câu đó.

## Chấm lại (cùng cách chấm, lượt 1 và lượt 2)

So được 100/100 người.

| Điểm | Trung bình lượt 1 | Trung bình lượt 2 | Trung bình lệch | Mỗi người lệch trung bình | Trùng điểm | Lệch trong 1 điểm | Số người lệch từ 2 | Kappa có trọng số |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hiểu mình | 2,24 | 2,27 | 0,03 | 0,23 | 77,0% | 100,0% | 0 | 0,73 |
| Bớt thấy một mình | 2,70 | 2,69 | 0,01 | 0,13 | 87,0% | 100,0% | 0 | 0,69 |
| Thấy bình yên | 2,88 | 2,93 | 0,05 | 0,09 | 91,0% | 100,0% | 0 | 0,53 |
| Muốn quay lại | 1,99 | 2,20 | 0,21 | 0,29 | 71,0% | 100,0% | 0 | 0,68 |

Người có ít nhất một điểm lệch từ 2: 0 (0,0%).

| Cờ hại | Số người bị cờ ở lượt 1 | Ở lượt 2 | Số người hai lượt khác nhau |
| --- | --- | --- | --- |
| bị trách | 0 | 0 | 0 |
| bị ép | 4 | 4 | 0 |
| lo riêng tư | 0 | 0 | 0 |
| phụ thuộc | 0 | 0 | 0 |
| phải xem Lá mới dám quyết | 0 | 0 | 0 |

## Hai giám khảo trên cùng 100 người

So được 100/100 người.

| Điểm | Trung bình giám khảo 1 | Trung bình giám khảo 2 | Trung bình lệch | Mỗi người lệch trung bình | Trùng điểm | Lệch trong 1 điểm | Số người lệch từ 2 | Kappa có trọng số |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hiểu mình | 2,24 | 2,30 | 0,06 | 0,42 | 59,0% | 99,0% | 1 | 0,35 |
| Bớt thấy một mình | 2,70 | 2,94 | 0,24 | 0,26 | 74,0% | 100,0% | 0 | 0,20 |
| Thấy bình yên | 2,88 | 3,00 | 0,12 | 0,12 | 88,0% | 100,0% | 0 | 0,00 |
| Muốn quay lại | 1,99 | 2,16 | 0,17 | 0,45 | 56,0% | 99,0% | 1 | 0,39 |

Người có ít nhất một điểm lệch từ 2: 1 (1,0%).

| Cờ hại | Số người bị cờ ở giám khảo 1 | Ở giám khảo 2 | Số người hai lượt khác nhau |
| --- | --- | --- | --- |
| bị trách | 0 | 0 | 0 |
| bị ép | 4 | 4 | 2 |
| lo riêng tư | 0 | 0 | 0 |
| phụ thuộc | 0 | 0 | 0 |
| phải xem Lá mới dám quyết | 0 | 0 | 0 |

## Cờ có bằng chứng không, giám khảo có bắt được cờ không

Cờ bị bỏ vì câu trích không có nguyên văn trong bài người đó được xem: lượt 1 0; lượt 2 0; giám khảo 2 0.

Ca cài sẵn: 10 bài thật được thay một câu bằng câu đúng điều kiện của một cờ, trộn vào cả ba lượt. Các ca này không tính vào mốc.

| Cờ được cài | Số ca | Bắt được ở lượt 1 | Bắt được ở lượt 2 | Bắt được ở giám khảo 2 |
| --- | --- | --- | --- | --- |
| bị trách | 2 | 2 | 2 | 2 |
| bị ép | 2 | 2 | 2 | 2 |
| lo riêng tư | 2 | 2 | 2 | 2 |
| phụ thuộc | 2 | 2 | 2 | 2 |
| phải xem Lá mới dám quyết | 2 | 2 | 2 | 2 |
| Tổng | 10 | 10 | 10 | 10 |

## Giới hạn

- Người giả và giám khảo đều là mô hình AI. Số này nói bộ đo có lặp lại được không, không nói người thật thấy thế nào.
- Giám khảo đọc chữ của Daily trong 4 ngày (1, 8, 15, 22). Chưa đọc các màn khác, chưa nhìn màn hình.
- Kappa không tính được khi một giám khảo cho mọi người cùng một điểm; khi đó ô ghi "—".
