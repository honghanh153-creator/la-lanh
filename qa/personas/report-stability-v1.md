# Bộ đo có ổn định không: chấm lại cùng 100 người giả

Rubric: `app-judge-v1-2026-11-20` (qa/personas/judge-rubric-app.md). Code được chấm: `d8cc2fe2e5ed`, 100 người giả, nội dung do API thật sinh ra trên máy với dữ liệu giả.
Mốc lấy từ kế hoạch 7 tuần (tuần 1, việc "Bộ đo"), ghi trước khi chấm.

**Kết luận chấm lại: CHƯA ĐẠT.**

| Mốc | Kết quả |  |
| --- | --- | --- |
| Chấm đủ mọi người ở cả hai lượt | 100/100 người | ĐẠT |
| Trung bình mỗi điểm lệch không quá 0,15 | lệch nhiều nhất 0,10 ở "Muốn quay lại" | ĐẠT |
| Không quá 10% số người có điểm lệch từ 2 | 0,0% (0 người) | ĐẠT |
| Cờ hại trùng nhau ở mọi người | 16 người có cờ khác nhau | TRƯỢT |

## Đọc kết quả (20.11.2026)

- **Bốn điểm 1–5 chấm lại được.** Trung bình lệch nhiều nhất 0,10 (mốc 0,15) và không người nào lệch từ 2 điểm.
- **Cờ hại chưa chấm lại được.** 16 trong 100 người có cờ khác nhau giữa hai lượt. Gần hết nằm ở cờ "bị ép": lượt 1 gắn 15 người, lượt 2 gắn 6 người, 11 người khác nhau. Cờ "bị trách" khác ở 5 người. Ba cờ còn lại không ai gắn ở cả ba lượt.
- Vì vậy mốc tuần 1 của bộ đo **chưa đạt**. Mốc không đổi.

## Nguyên nhân (đọc từ các câu trích của giám khảo)

- Ngày nào Daily cũng đưa một việc nhỏ. Rubric v1 chỉ ghi "thấy bị ép làm gì", không nói khi nào một việc nhỏ bình thường thành "bị ép". Có giám khảo gắn cờ cho mọi người ghét bị giao việc, có giám khảo chỉ gắn khi câu chữ ra lệnh.
- Cờ "bị trách" cũng vậy: cùng một tiêu đề tả thói quen ("Việc mới đến, bạn bỏ dở việc đang làm.") có lượt coi là trách, có lượt không.
- Đây là lỗi của cách chấm, chưa nói được gì về việc app có ép người dùng hay không.

## Cách sửa (chưa làm trong lần này)

1. Viết lại định nghĩa từng cờ thành điều kiện kiểm được trên câu chữ, kèm ví dụ gắn cờ và ví dụ không gắn cờ. Ví dụ với "bị ép": chỉ gắn khi câu trích không cho lối từ chối, hoặc việc nhỏ trái với mood người đó vừa chọn.
2. Tăng phiên bản rubric lên v2 và chấm lại cả ba lượt trên cùng 100 người.
3. Nếu v2 vẫn không trùng, đổi cách lấy cờ: ba giám khảo, cờ chỉ tính khi ít nhất hai người gắn, rồi đo lại độ trùng của cách lấy đó.

Cho tới khi sửa xong, số cờ hại lấy từ một lượt chấm đơn lẻ (kể cả các lượt 14–15.11) nên đọc là "khoảng", không so được với mốc 3%.

## Hai giám khảo

- Giám khảo 1 và lượt chấm lại: Claude subagent mới, cùng loại với phiên chạy. Giám khảo 2: Claude subagent loại khác (Sonnet). Codex chưa chấm đối chiếu.
- Trung bình hai giám khảo gần nhau (lệch 0,01 đến 0,22), 98–100% số người lệch trong 1 điểm. Nhưng kappa thấp (0,10–0,38): gần hết điểm dồn vào 2 và 3, nên hai giám khảo trùng nhau về mức chung mà chưa trùng về việc **ai** được điểm cao hơn. So trung bình của một nhóm lớn thì dùng được; xếp hạng từng người hay nhóm nhỏ thì chưa.
- "Bớt thấy một mình" lệch 0,22 giữa hai giám khảo: khi so hai bản app bằng điểm này, phải dùng cùng một loại giám khảo cho cả hai bản.

## Cách chạy lần này

- Mỗi lượt 4 gói, mỗi gói 25 người, mỗi gói một giám khảo mới. Thứ tự người trong ba lượt khác nhau.
- Giám khảo ghi tệp điểm ra ngoài repo; các tệp được chép nguyên vào `qa/personas/stability/judged/`, không sửa điểm. Hai giám khảo lúc đầu báo đã ghi tệp trong khi chưa ghi được; đã phát hiện vì tệp không có trên đĩa và họ ghi lại đúng bản đã chấm.
- Gói chấm tạo lại được bằng `pnpm personas:stability -- packets` từ `transcript.jsonl.gz` của lần chạy.

## Chấm lại (cùng cách chấm, lượt 1 và lượt 2)

So được 100/100 người.

| Điểm | Trung bình lượt 1 | Trung bình lượt 2 | Trung bình lệch | Mỗi người lệch trung bình | Trùng điểm | Lệch trong 1 điểm | Số người lệch từ 2 | Kappa có trọng số |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hiểu mình | 2,27 | 2,30 | 0,03 | 0,27 | 73,0% | 100,0% | 0 | 0,69 |
| Bớt thấy một mình | 2,59 | 2,52 | 0,07 | 0,33 | 67,0% | 100,0% | 0 | 0,34 |
| Thấy bình yên | 2,89 | 2,89 | 0,00 | 0,10 | 90,0% | 100,0% | 0 | 0,54 |
| Muốn quay lại | 2,13 | 2,03 | 0,10 | 0,24 | 76,0% | 100,0% | 0 | 0,70 |

Người có ít nhất một điểm lệch từ 2: 0 (0,0%).

| Cờ hại | Số người bị cờ ở lượt 1 | Ở lượt 2 | Số người hai lượt khác nhau |
| --- | --- | --- | --- |
| bị trách | 5 | 4 | 5 |
| bị ép | 15 | 6 | 11 |
| lo riêng tư | 0 | 0 | 0 |
| phụ thuộc | 0 | 0 | 0 |
| phải xem Lá mới dám quyết | 0 | 0 | 0 |

## Hai giám khảo trên cùng 100 người

So được 100/100 người.

| Điểm | Trung bình giám khảo 1 | Trung bình giám khảo 2 | Trung bình lệch | Mỗi người lệch trung bình | Trùng điểm | Lệch trong 1 điểm | Số người lệch từ 2 | Kappa có trọng số |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hiểu mình | 2,27 | 2,26 | 0,01 | 0,49 | 52,0% | 99,0% | 1 | 0,26 |
| Bớt thấy một mình | 2,59 | 2,81 | 0,22 | 0,40 | 60,0% | 100,0% | 0 | 0,10 |
| Thấy bình yên | 2,89 | 2,99 | 0,10 | 0,12 | 88,0% | 100,0% | 0 | 0,13 |
| Muốn quay lại | 2,13 | 2,19 | 0,06 | 0,40 | 62,0% | 98,0% | 2 | 0,38 |

Người có ít nhất một điểm lệch từ 2: 2 (2,0%).

| Cờ hại | Số người bị cờ ở giám khảo 1 | Ở giám khảo 2 | Số người hai lượt khác nhau |
| --- | --- | --- | --- |
| bị trách | 5 | 1 | 6 |
| bị ép | 15 | 6 | 9 |
| lo riêng tư | 0 | 0 | 0 |
| phụ thuộc | 0 | 0 | 0 |
| phải xem Lá mới dám quyết | 0 | 0 | 0 |

## Giới hạn

- Người giả và giám khảo đều là mô hình AI. Số này nói bộ đo có lặp lại được không, không nói người thật thấy thế nào.
- Giám khảo đọc chữ của Daily trong 4 ngày (1, 8, 15, 22). Chưa đọc các màn khác, chưa nhìn màn hình.
- Kappa không tính được khi một giám khảo cho mọi người cùng một điểm; khi đó ô ghi "—".
