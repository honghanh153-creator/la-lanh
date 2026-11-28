# Bộ đo có ổn định không: chấm lại cùng 100 người giả

Rubric: `app-judge-v4-2026-11-21` (qa/personas/judge-rubric-app.md). Code được chấm: `d8cc2fe2e5ed`, 100 người giả, nội dung do API thật sinh ra trên máy với dữ liệu giả.
Mốc lấy từ kế hoạch 7 tuần (tuần 1, việc "Bộ đo"), ghi trước khi chấm.

**Kết luận chấm lại: CHƯA ĐẠT.**

| Mốc | Kết quả |  |
| --- | --- | --- |
| Chấm đủ mọi người ở cả hai lượt | 100/100 người | ĐẠT |
| Trung bình mỗi điểm lệch không quá 0,15 | lệch nhiều nhất 0,18 ở "Thấy bình yên" | TRƯỢT |
| Không quá 10% số người có điểm lệch từ 2 | 11,0% (11 người) | TRƯỢT |
| Cờ hại trùng nhau ở mọi người | 2 người có cờ khác nhau | TRƯỢT |

## Đọc kết quả (rubric v4, 21.11.2026)

- **Rubric v4 vẫn chưa đạt mốc, nhưng trượt sát mốc ở cả ba chỗ.** "Thấy bình yên" lệch 0,18 (mốc 0,15). 11 người có điểm lệch từ 2 (mốc 10). Cờ "bị ép" khác nhau ở 2 người. Mốc không đổi, không chấm lại để lấy số đẹp hơn.
- **So với v3:** "Muốn quay lại" lệch 0,04 (v3: 0,30) và trùng điểm 93% (v3: 72%). Số người lệch từ 2: 11 (v3: 14). Kappa lượt 1 với lượt 2 từ 0,74 đến 1,00. Điểm v4 tính theo cách khác nên chỉ so được độ lặp lại, không so được mức điểm.
- **Hai giám khảo khác loại còn lệch nhiều ở "Thấy bình yên":** 0,36 điểm, 16 người lệch từ 2. Một giám khảo (giám khảo 2, gói 4) chấm cao hơn lượt kia 1,15 điểm. Chỗ lệch là ngày tốt: 53 ngày một bên ghi tốt, bên kia không tính.

## Ba điều bảng phân bố cho thấy

- **"Bớt thấy một mình" gần như không đo gì.** 95 trên 100 người ra điểm 3 ở cả ba lượt, không ngày nào được ghi tốt. Hai lượt trùng 100% là vì vậy, không phải vì chấm giỏi. Hoặc Daily hiện không có câu nào đúng điều kiện "tốt" của câu hỏi này, hoặc điều kiện viết quá hẹp. Chưa mở từng bài để biết là bên nào.
- **"Muốn quay lại": 62 đến 64 người ra điểm 1.** 63 người có từ hai ngày xấu. Phần lớn đến từ luật mới cho ý "chung chung": hồ sơ ghi "lời đọc không dính gì tới mình" và ngày đó không ô nào nói tới chuyện của họ. Đây là điều kiện kiểm được nên hai lượt khớp nhau, nhưng điểm dồn về đáy thì khó thấy khác biệt giữa hai bản app. Cần quyết ở bước sau: giữ luật này (và coi đây là số nền thật: Daily ít khi nói tới chuyện riêng của từng người), hay chỉ tính nó một lần cho cả 4 ngày.
- **"Hiểu mình": 77 đến 79 người ra điểm 3, không ai ra điểm 4.** Ít ngày được ghi tốt.

## Chỗ còn lệch (đọc từ dấu từng ngày)

- "Thấy bình yên", lượt 1 và lượt 2: 14 ngày một lượt ghi tốt, lượt kia không tính; 3 ngày xấu ở lượt này mà tốt ở lượt kia. Ý "việc nhỏ bớt đi một việc" còn để giám khảo tự hiểu.
- "Muốn quay lại": 15 ngày một lượt ghi xấu, lượt kia không tính; 3 ngày xấu và tốt ngược nhau, ở 2 người.
- "Hiểu mình": 13 ngày một lượt ghi xấu, lượt kia không tính.

## Cờ "bị ép"

- Dòng mới (hạn trong câu mẫu vẫn tính) có tác dụng: câu "Nói: Để mình xem lịch rồi báo bạn trong hôm nay." gây lệch ở v3, lần này cả ba lượt đều gắn cờ.
- Hai người còn khác nhau giữa lượt 1 và lượt 2 là do hai câu khác: "Nói bạn sẽ trả lời sau khi xem lịch tối nay." (tối nay là lúc xem lịch hay là hạn trả lời) và "Nói: Mình làm được thứ Bảy, hôm nay thì không tiện." (hôm nay ở đây không phải hạn). Giám khảo 2 còn gắn cờ cho "Hỏi ngay chỗ đó: …" ("ngay" chỉ chỗ, không chỉ lúc) và "…muốn nhờ giúp hôm nay".
- Số người bị cờ tăng từ 4 (v3) lên 7 đến 9 vì dòng mới. Bảy câu việc nhỏ của app có chữ chỉ hạn trong ngày; danh sách nằm trong các tệp điểm. Đây là phát hiện về nội dung, chưa mở issue.
- Ca cài sẵn: bắt đủ 10 trên 10 ở cả ba lượt. Không cờ nào bị bỏ vì thiếu câu trích.

## Bước sau (chưa làm trong lần này)

1. "Thấy bình yên": viết ngày tốt thành danh sách chữ kiểm được, bỏ ý "bớt đi một việc".
2. Cờ "bị ép": thêm ba ví dụ không gắn cho chữ "hôm nay", "tối nay", "ngay" khi chúng không phải hạn của việc nhỏ.
3. Quyết cách tính ý "chung chung" ở "Muốn quay lại" và xem lại điều kiện tốt của "Bớt thấy một mình", vì hai điểm này đang dồn về một mức.
4. Nếu sau đó vẫn trượt: mỗi người hai giám khảo mỗi lượt (cách B trong Plan trên #689).

Cho tới khi đạt mốc: không dùng điểm v4 để so hai bản app. #692 chờ tiếp.

## Cách chạy lần này

- Rubric v4, công thức và test được commit trước khi chấm. Plan và phần đính chính viết trên #689 trước khi sửa code.
- Cùng lần chạy app với v1 đến v3 (`stability-2026-11-20`), cùng 10 ca cài sẵn. Mỗi lượt 4 gói, 110 bài, mỗi gói một giám khảo mới.
- Giám khảo 1 và lượt chấm lại: Claude subagent cùng loại với phiên chạy. Giám khảo 2: Claude subagent loại khác (Sonnet). Codex chưa chấm đối chiếu.
- Giám khảo chỉ đọc phần rubric dành cho giám khảo và tệp gói, ghi tệp điểm ra ngoài repo. 12 tệp được chép nguyên vào `qa/personas/stability/judged-v4/`, không sửa. Không giám khảo nào phải ghi lại.
- Điểm v3 giữ ở `qa/personas/stability/judged-v3/`, báo cáo v3 ở `qa/personas/report-stability-v3.md`. Lệnh `report` của bản code này không đọc được tệp điểm v1 đến v3 (không có dấu từng ngày).

## Chấm lại (cùng cách chấm, lượt 1 và lượt 2)

So được 100/100 người.

| Điểm | Trung bình lượt 1 | Trung bình lượt 2 | Trung bình lệch | Mỗi người lệch trung bình | Trùng điểm | Lệch trong 1 điểm | Số người lệch từ 2 | Kappa có trọng số |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hiểu mình | 2,79 | 2,77 | 0,02 | 0,12 | 91,0% | 97,0% | 3 | 0,74 |
| Bớt thấy một mình | 2,95 | 2,95 | 0,00 | 0,00 | 100,0% | 100,0% | 0 | 1,00 |
| Thấy bình yên | 2,73 | 2,91 | 0,18 | 0,20 | 84,0% | 96,0% | 4 | 0,92 |
| Muốn quay lại | 1,79 | 1,75 | 0,04 | 0,12 | 93,0% | 95,0% | 5 | 0,91 |

Người có ít nhất một điểm lệch từ 2: 11 (11,0%).

| Cờ hại | Số người bị cờ ở lượt 1 | Ở lượt 2 | Số người hai lượt khác nhau |
| --- | --- | --- | --- |
| bị trách | 0 | 0 | 0 |
| bị ép | 7 | 7 | 2 |
| lo riêng tư | 0 | 0 | 0 |
| phụ thuộc | 0 | 0 | 0 |
| phải xem Lá mới dám quyết | 0 | 0 | 0 |

## Hai giám khảo trên cùng 100 người

So được 100/100 người.

| Điểm | Trung bình giám khảo 1 | Trung bình giám khảo 2 | Trung bình lệch | Mỗi người lệch trung bình | Trùng điểm | Lệch trong 1 điểm | Số người lệch từ 2 | Kappa có trọng số |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hiểu mình | 2,79 | 2,87 | 0,08 | 0,12 | 89,0% | 99,0% | 1 | 0,81 |
| Bớt thấy một mình | 2,95 | 2,99 | 0,04 | 0,04 | 96,0% | 100,0% | 0 | 0,60 |
| Thấy bình yên | 2,73 | 3,09 | 0,36 | 0,56 | 65,0% | 84,0% | 16 | 0,74 |
| Muốn quay lại | 1,79 | 1,76 | 0,03 | 0,23 | 89,0% | 90,0% | 10 | 0,78 |

Người có ít nhất một điểm lệch từ 2: 23 (23,0%).

| Cờ hại | Số người bị cờ ở giám khảo 1 | Ở giám khảo 2 | Số người hai lượt khác nhau |
| --- | --- | --- | --- |
| bị trách | 0 | 0 | 0 |
| bị ép | 7 | 9 | 4 |
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

## Điểm phân bố thế nào

Số người nhận từng điểm ở mỗi lượt. Khi gần như ai cũng cùng một điểm thì hai lượt trùng nhau không nói được là bộ đo ổn định.

| Điểm | Lượt | 1 điểm | 2 điểm | 3 điểm | 4 điểm | 5 điểm |
| --- | --- | --- | --- | --- | --- | --- |
| Hiểu mình | lượt 1 | 4 | 17 | 77 | 0 | 2 |
| Hiểu mình | lượt 2 | 5 | 15 | 79 | 0 | 1 |
| Hiểu mình | giám khảo 2 | 3 | 14 | 78 | 3 | 2 |
| Bớt thấy một mình | lượt 1 | 0 | 5 | 95 | 0 | 0 |
| Bớt thấy một mình | lượt 2 | 0 | 5 | 95 | 0 | 0 |
| Bớt thấy một mình | giám khảo 2 | 0 | 3 | 95 | 2 | 0 |
| Thấy bình yên | lượt 1 | 24 | 17 | 33 | 14 | 12 |
| Thấy bình yên | lượt 2 | 20 | 15 | 35 | 14 | 16 |
| Thấy bình yên | giám khảo 2 | 23 | 13 | 25 | 10 | 29 |
| Muốn quay lại | lượt 1 | 62 | 5 | 29 | 0 | 4 |
| Muốn quay lại | lượt 2 | 64 | 6 | 25 | 1 | 4 |
| Muốn quay lại | giám khảo 2 | 63 | 6 | 27 | 0 | 4 |

## Hai lượt ghi ngày khác nhau ở đâu

Giám khảo ghi từng ngày là xấu, tốt hay không tính; máy tính điểm. Bảng đếm số ngày hai lượt ghi khác nhau. Một ngày xấu ở lượt này mà tốt ở lượt kia làm điểm lệch 2; hai kiểu còn lại lệch 1.

Lượt 1 và lượt 2:

| Điểm | Số ngày so được | Xấu và không tính | Tốt và không tính | Xấu và tốt | Số người có ngày khác nhau |
| --- | --- | --- | --- | --- | --- |
| Hiểu mình | 400 | 13 | 2 | 0 | 9 |
| Bớt thấy một mình | 400 | 0 | 0 | 0 | 0 |
| Thấy bình yên | 400 | 1 | 14 | 3 | 17 |
| Muốn quay lại | 400 | 15 | 6 | 3 | 11 |

Giám khảo 1 và giám khảo 2:

| Điểm | Số ngày so được | Xấu và không tính | Tốt và không tính | Xấu và tốt | Số người có ngày khác nhau |
| --- | --- | --- | --- | --- | --- |
| Hiểu mình | 400 | 9 | 3 | 0 | 11 |
| Bớt thấy một mình | 400 | 2 | 2 | 0 | 4 |
| Thấy bình yên | 400 | 6 | 53 | 4 | 38 |
| Muốn quay lại | 400 | 19 | 23 | 4 | 16 |

## Từng giám khảo so với lượt kia

Mỗi dòng là một tệp điểm (một giám khảo). Số là trung bình điểm của giám khảo đó trừ trung bình lượt kia cho đúng những người đó. Dấu trừ là chấm thấp hơn lượt kia.

| Giám khảo | Số người | Hiểu mình | Bớt thấy một mình | Thấy bình yên | Muốn quay lại |
| --- | --- | --- | --- | --- | --- |
| lượt 1, gói 1 | 24 | +0,00 | +0,00 | -0,12 | +0,08 |
| lượt 1, gói 2 | 25 | +0,00 | +0,00 | -0,04 | +0,00 |
| lượt 1, gói 3 | 26 | -0,04 | +0,00 | -0,38 | +0,00 |
| lượt 1, gói 4 | 25 | +0,12 | +0,00 | -0,16 | +0,08 |
| lượt 2, gói 1 | 26 | -0,15 | +0,00 | +0,12 | +0,04 |
| lượt 2, gói 2 | 24 | +0,00 | +0,00 | +0,29 | -0,17 |
| lượt 2, gói 3 | 25 | +0,00 | +0,00 | +0,12 | +0,00 |
| lượt 2, gói 4 | 25 | +0,08 | +0,00 | +0,20 | -0,04 |
| giám khảo 2, gói 1 | 26 | -0,08 | +0,00 | -0,08 | +0,08 |
| giám khảo 2, gói 2 | 23 | +0,00 | +0,00 | -0,04 | -0,26 |
| giám khảo 2, gói 3 | 25 | +0,20 | +0,12 | +0,36 | -0,04 |
| giám khảo 2, gói 4 | 26 | +0,19 | +0,04 | +1,15 | +0,08 |

## Giới hạn

- Người giả và giám khảo đều là mô hình AI. Số này nói bộ đo có lặp lại được không, không nói người thật thấy thế nào.
- Giám khảo đọc chữ của Daily trong 4 ngày (1, 8, 15, 22). Chưa đọc các màn khác, chưa nhìn màn hình.
- Kappa không tính được khi một giám khảo cho mọi người cùng một điểm; khi đó ô ghi "—".
