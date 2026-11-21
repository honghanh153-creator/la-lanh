# Bộ đo có ổn định không: chấm lại cùng 100 người giả

Rubric: `app-judge-v3-2026-11-21` (qa/personas/judge-rubric-app.md). Code được chấm: `d8cc2fe2e5ed`, 100 người giả, nội dung do API thật sinh ra trên máy với dữ liệu giả.
Mốc lấy từ kế hoạch 7 tuần (tuần 1, việc "Bộ đo"), ghi trước khi chấm.

**Kết luận chấm lại: CHƯA ĐẠT.**

| Mốc | Kết quả |  |
| --- | --- | --- |
| Chấm đủ mọi người ở cả hai lượt | 100/100 người | ĐẠT |
| Trung bình mỗi điểm lệch không quá 0,15 | lệch nhiều nhất 0,30 ở "Muốn quay lại" | TRƯỢT |
| Không quá 10% số người có điểm lệch từ 2 | 14,0% (14 người) | TRƯỢT |
| Cờ hại trùng nhau ở mọi người | 2 người có cờ khác nhau | TRƯỢT |

## Đọc kết quả (rubric v3, 21.11.2026)

- **Rubric v3 không đạt mốc và tệ hơn v2 ở ba mốc.** "Muốn quay lại" lệch 0,30 (v2: 0,21). 14 người có điểm lệch từ 2 (v2: 0). Cờ hại khác nhau ở 2 người (v2: 0). Mốc không đổi, không chấm lại để lấy số đẹp hơn.
- **Hai điểm tốt lên, hai điểm xấu đi.** "Hiểu mình" và "Bớt thấy một mình": trùng điểm 89% và 96% (v2: 77% và 87%), không ai lệch từ 2. "Thấy bình yên" và "Muốn quay lại": trùng điểm 74% và 72%, có 6 và 8 người lệch từ 2.
- **Giám khảo tra bảng đúng, chỗ lệch là lúc đếm ngày.** Không bài nào có điểm khác bảng tra ở cả ba lượt. Vậy điểm lệch vì hai giám khảo đếm số ngày xấu, ngày tốt khác nhau cho cùng một người.
- **Bảng tra làm chỗ lệch to ra.** Ở bảng A, một ngày bị đếm là xấu kéo điểm từ 4 xuống 2. Ở v2 hai lượt chỉ lệch nhau 1 điểm; ở v3 cùng một bất đồng thành lệch 2 đến 4 điểm.

## Vì sao đếm ngày lại khác nhau (đọc từ số đếm giám khảo ghi)

Các số dưới đây tính trên 110 bài mỗi lượt (100 người và 10 ca cài sẵn).

- "Muốn quay lại": lượt 1 và lượt 2 ghi số ngày xấu khác nhau ở 21 bài, số ngày tốt khác nhau ở 26 bài. Có bài một lượt ghi 4 ngày xấu, lượt kia ghi 4 ngày tốt. Điều kiện dựa vào hai ô hồ sơ `would_quit_if` và `wants_from_app`. Cách đọc của mình, chưa chứng minh: hai ô này viết bằng lời chung, và ngày nào Daily cũng có một việc nhỏ, nên cùng một bài có giám khảo xếp vào điều làm người đó bỏ app, có giám khảo xếp vào thứ người đó muốn. Chưa mở từng bài để kiểm.
- Từng giám khảo đếm theo một thói quen riêng. Ở lượt 1, gói 1 ghi 4 ngày xấu cho 16 trên 28 bài và không ghi ngày tốt nào; gói 2 ghi 4 ngày xấu cho 2 trên 27 bài. Ở lượt 2, gói 2 chấm "Muốn quay lại" cao hơn lượt kia 0,83 điểm và "Thấy bình yên" cao hơn 0,50 trên cùng những người đó.
- "Thấy bình yên": số ngày tốt khác nhau ở 23 bài, số ngày xấu ở 7 bài. Điều kiện "việc nhỏ làm được trong nhịp ngày và nhắm vào một chuyện trong hồ sơ" còn rộng: một giám khảo (lượt 2, gói 2) ghi ngày tốt cho 15 trên 28 bài, bảy giám khảo còn lại của hai lượt ghi cho 0 đến 7 bài.
- "Hiểu mình" và "Bớt thấy một mình" đếm ổn hơn vì điều kiện so chữ của bài với chuyện ghi trong hồ sơ, ít phải đoán ý.

## Cờ "bị ép" khác nhau ở 2 người

Chữ của năm cờ không đổi so với v2. Hai lượt đều gắn cờ cho 4 người, nhưng khác nhau ở 2 người, và cả hai lần đều do cùng một câu: "Nói: Để mình xem lịch rồi báo bạn trong hôm nay." Một lượt coi "trong hôm nay" là hạn app đặt thay người đọc, lượt kia coi đó là lời người đọc tự nói. Báo cáo v2 đã ghi câu này là ca sát ranh giữa hai loại giám khảo; lần này nó lệch ngay giữa hai lượt cùng loại. Vậy kết quả "0 người khác nhau" của v2 có phần may. Ca cài sẵn vẫn bắt đủ 10/10 ở cả ba lượt.

## Cách sửa (chưa làm trong lần này)

1. Không dùng bảng tra có bậc nhảy 2 điểm. Hoặc quay lại bốn điểm của v2 cho "Thấy bình yên" và "Muốn quay lại", giữ cách đếm cho "Hiểu mình" và "Bớt thấy một mình"; hoặc đổi bảng để mỗi ngày chỉ làm điểm đổi 1.
2. Cho mỗi người hai giám khảo mỗi lượt rồi lấy trung bình (cách B trong Plan trên #689). Bảng "Từng giám khảo so với lượt kia" cho thấy lệch đến từ thói quen của từng giám khảo, nên lấy trung bình hai người là cách chữa đúng chỗ.
3. Thêm vào rubric một dòng cho cờ "bị ép": hạn nằm trong câu mẫu để người đọc tự nói ra thì tính hay không. Chọn một, ghi ví dụ.
4. Bắt giám khảo ghi ngày nào là xấu, ngày nào là tốt (không chỉ số đếm), để lần sau chỉ ra đúng câu gây bất đồng.

Cho tới khi sửa xong: không dùng điểm v3 của "Thấy bình yên" và "Muốn quay lại" để so hai bản app. Cờ hại so được, trừ câu có hạn "hôm nay" nằm trong lời mẫu. #692 nên chờ bước sửa tiếp, hoặc ghi rõ đang dùng rubric nào.

## Hai giám khảo

- Giám khảo 1 và lượt chấm lại: Claude subagent mới, cùng loại với phiên chạy. Giám khảo 2: Claude subagent loại khác (Sonnet). Codex chưa chấm đối chiếu.
- "Muốn quay lại": trung bình lệch 0,27, 14 người lệch từ 2, kappa 0,45. Ba điểm còn lại: trung bình lệch 0,00 đến 0,07, kappa 0,59 đến 0,66 (v2: 0,00 đến 0,39). Hai giám khảo khớp nhau hơn v2 ở ba điểm đó.

## Cách chạy lần này

- Rubric v3, hai bảng đọc nguyên nhân và luật "có ca cài sẵn thì từ 2 gói" được commit trước khi chấm. Plan viết trên #689 trước khi sửa code.
- Cùng lần chạy app với v1 và v2 (`stability-2026-11-20`), cùng 10 ca cài sẵn. Mỗi lượt 4 gói, 110 bài, mỗi gói một giám khảo mới. Thứ tự và cách chia gói khác v2 vì hạt xáo lấy từ tên phiên bản rubric.
- Giám khảo chỉ đọc phần rubric dành cho giám khảo và tệp gói, ghi tệp điểm ra ngoài repo. 12 tệp được chép nguyên vào `qa/personas/stability/judged-v3/`, không sửa điểm. Không giám khảo nào phải ghi lại.
- Điểm v2 giữ ở `qa/personas/stability/judged-v2/`, báo cáo v2 ở `qa/personas/report-stability-v2.md`. Không trộn điểm giữa các phiên bản.

## Chấm lại (cùng cách chấm, lượt 1 và lượt 2)

So được 100/100 người.

| Điểm | Trung bình lượt 1 | Trung bình lượt 2 | Trung bình lệch | Mỗi người lệch trung bình | Trùng điểm | Lệch trong 1 điểm | Số người lệch từ 2 | Kappa có trọng số |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hiểu mình | 1,90 | 1,89 | 0,01 | 0,11 | 89,0% | 100,0% | 0 | 0,84 |
| Bớt thấy một mình | 2,96 | 2,98 | 0,02 | 0,04 | 96,0% | 100,0% | 0 | 0,66 |
| Thấy bình yên | 2,96 | 3,00 | 0,04 | 0,32 | 74,0% | 94,0% | 6 | 0,50 |
| Muốn quay lại | 1,68 | 1,98 | 0,30 | 0,42 | 72,0% | 92,0% | 8 | 0,72 |

Người có ít nhất một điểm lệch từ 2: 14 (14,0%).

| Cờ hại | Số người bị cờ ở lượt 1 | Ở lượt 2 | Số người hai lượt khác nhau |
| --- | --- | --- | --- |
| bị trách | 0 | 0 | 0 |
| bị ép | 4 | 4 | 2 |
| lo riêng tư | 0 | 0 | 0 |
| phụ thuộc | 0 | 0 | 0 |
| phải xem Lá mới dám quyết | 0 | 0 | 0 |

## Hai giám khảo trên cùng 100 người

So được 100/100 người.

| Điểm | Trung bình giám khảo 1 | Trung bình giám khảo 2 | Trung bình lệch | Mỗi người lệch trung bình | Trùng điểm | Lệch trong 1 điểm | Số người lệch từ 2 | Kappa có trọng số |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hiểu mình | 1,90 | 1,95 | 0,05 | 0,19 | 83,0% | 98,0% | 2 | 0,59 |
| Bớt thấy một mình | 2,96 | 2,96 | 0,00 | 0,04 | 96,0% | 100,0% | 0 | 0,66 |
| Thấy bình yên | 2,96 | 2,89 | 0,07 | 0,21 | 81,0% | 98,0% | 2 | 0,60 |
| Muốn quay lại | 1,68 | 1,95 | 0,27 | 0,65 | 59,0% | 86,0% | 14 | 0,45 |

Người có ít nhất một điểm lệch từ 2: 16 (16,0%).

| Cờ hại | Số người bị cờ ở giám khảo 1 | Ở giám khảo 2 | Số người hai lượt khác nhau |
| --- | --- | --- | --- |
| bị trách | 0 | 0 | 0 |
| bị ép | 4 | 5 | 3 |
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

## Điểm có khớp số đếm không

Số bài có điểm khác với điểm bảng tra cho ra từ số ngày xấu và ngày tốt giám khảo tự ghi (bài thiếu số đếm cũng tính). Máy chỉ đếm, không sửa điểm. Có tính cả ca cài sẵn.

| Điểm | Lượt 1 | Lượt 2 | Giám khảo 2 |
| --- | --- | --- | --- |
| Hiểu mình | 0 | 0 | 0 |
| Bớt thấy một mình | 0 | 0 | 0 |
| Thấy bình yên | 0 | 0 | 0 |
| Muốn quay lại | 0 | 0 | 0 |

## Từng giám khảo so với lượt kia

Mỗi dòng là một tệp điểm (một giám khảo). Số là trung bình điểm của giám khảo đó trừ trung bình lượt kia cho đúng những người đó. Dấu trừ là chấm thấp hơn lượt kia.

| Giám khảo | Số người | Hiểu mình | Bớt thấy một mình | Thấy bình yên | Muốn quay lại |
| --- | --- | --- | --- | --- | --- |
| lượt 1, gói 1 | 27 | +0,07 | +0,00 | +0,19 | -0,33 |
| lượt 1, gói 2 | 25 | +0,08 | +0,00 | -0,12 | -0,20 |
| lượt 1, gói 3 | 23 | -0,09 | -0,04 | +0,00 | -0,13 |
| lượt 1, gói 4 | 25 | -0,04 | -0,04 | -0,24 | -0,52 |
| lượt 2, gói 1 | 26 | -0,04 | +0,00 | -0,27 | +0,15 |
| lượt 2, gói 2 | 24 | -0,04 | -0,04 | +0,50 | +0,83 |
| lượt 2, gói 3 | 23 | +0,04 | +0,04 | -0,04 | -0,04 |
| lượt 2, gói 4 | 27 | +0,00 | +0,07 | +0,00 | +0,26 |
| giám khảo 2, gói 1 | 24 | -0,04 | -0,04 | -0,08 | +0,12 |
| giám khảo 2, gói 2 | 26 | +0,04 | -0,04 | -0,12 | +0,31 |
| giám khảo 2, gói 3 | 24 | +0,17 | +0,08 | +0,04 | +0,50 |
| giám khảo 2, gói 4 | 26 | +0,04 | +0,00 | -0,12 | +0,15 |

## Giới hạn

- Người giả và giám khảo đều là mô hình AI. Số này nói bộ đo có lặp lại được không, không nói người thật thấy thế nào.
- Giám khảo đọc chữ của Daily trong 4 ngày (1, 8, 15, 22). Chưa đọc các màn khác, chưa nhìn màn hình.
- Kappa không tính được khi một giám khảo cho mọi người cùng một điểm; khi đó ô ghi "—".
