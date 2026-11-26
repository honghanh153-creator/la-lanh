# Nhìn lại vòng tự động Claude ⇄ Codex: 25.11.2026

Tác giả: Claude (lượt retro tự động 25.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Báo số việc thật, không chia cho chỉ tiêu nào. Không còn ngày nào thiếu bản nhìn lại.

## 1. Số chính thức (bản chụp, chép nguyên)

- Đã gộp vào integration hôm nay: 5 PR (số PR, không phải số việc).
- Việc đạt tiêu chí: 0/3 việc đã chọn đạt đủ tiêu chí; 3 PR chưa gắn việc (#894, #826, #929), không tính.
- Việc kế hoạch 7 tuần: đã chọn 2 (tối thiểu 2 khi có việc sẵn sàng), đạt 0.
- PR đang mở: 41 (chờ owner: #906, #904, #903, #902, #901, #900, #899, #894, #734).
- Sự cố đang mở: #917 [ops-alert] Claude dùng nhanh hơn nhịp tuần (từ 24/11 10:54); #782 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-20 (từ 20/11 10:22); #511 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-14 (từ 14/11 18:29); #470 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-13 (từ 13/11 17:22); #408 [ops-alert] staging-ready failed 2026-11-10 15:29 UTC (từ 10/11 22:29); #370 [ops-alert] collab loop 2026-11-09 (từ 09/11 17:08); #368 [ops-alert] collab loop 2026-11-09 (từ 09/11 14:06); #352 [ops-alert] ssh failed 2026-11-08 15:29 UTC (từ 08/11 22:40); #334 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 20:51); #322 [ops-alert] collab loop 2026-11-08 (từ 08/11 17:09); #321 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 16:18); #318 [ops-alert] collab loop 2026-11-08 (từ 08/11 13:25); #317 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 13:25); #313 [ops-alert] collab loop 2026-11-08 (từ 08/11 10:51); #312 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-08 (từ 08/11 10:21); #311 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-08 (từ 08/11 05:07); #310 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-07 (từ 08/11 00:14); #309 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 23:24); #308 [ops-alert] collab loop 2026-11-07 (từ 07/11 22:53); #305 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 19:21); #304 [ops-alert] collab loop 2026-11-07 (từ 07/11 18:51); #303 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 17:20); #289 [ops-alert] collab loop 2026-11-07 (từ 07/11 13:21); #287 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-07 (từ 07/11 11:20); #285 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 10:29); #277 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-06 (từ 07/11 06:03); #276 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-07 (từ 07/11 06:03); #266 [ops-alert] collab loop 2026-11-06 (từ 06/11 13:54); #261 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-05 (từ 06/11 11:32); #260 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-06 (từ 06/11 11:32); #259 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-06 (từ 06/11 11:32); #244 [ops-alert] collab loop 2026-11-05 (từ 05/11 22:56); #231 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #230 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #205 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 04:46); #204 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 23:44); #196 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 20:33); #193 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 14:42).
- Lượt Codex hôm nay: 32/80; lỗi liên tiếp: 4.
- Lời hứa sửa quy trình: 63/68 đã chạy thật (đã merge, Codex duyệt), 2 đang làm, 1 chờ owner, 2 owner quyết không làm, rủi ro vẫn còn (L17, L24), **2 quá hạn** (L18, L20).

Nguồn: bản chụp 2026-11-25 khung retro, lấy lúc 23:36, integration d3818f5 · snapshot c342f88cc8f4

Các số ở những mục dưới lấy từ: `logs/tick-2026-11-25.log`, `state/2026-11-25.json`, `collab-turn --report` (23:38), `gh pr list` (PR gộp trong ngày), 20 kết luận tự động của Codex trên 9 PR trong ngày, `queue.md` của autopilot, `git log origin/main`.

## 2. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| PR người dùng thấy được (vào integration) | **2 PR** | #787 Hợp gu nói tiếng Việt dễ hiểu, hai ô xem lại đủ 44 px; #848 Daily thêm chủ đề "tự so mình / sửa mãi chưa gửi" (câu chờ duyệt). Hôm qua 7 |
| Việc đã lên bản chạy thật | **0** | `main` không có commit mới trong ngày |
| Việc kế hoạch 7 tuần | 0 đạt tiêu chí (số máy) | Máy chọn #714 và #715, chưa có PR nào cho hai việc này. Codex tự làm #704 (PR #933, 12 câu Daily cho học sinh, sinh viên đi làm thêm) và #709 (PR #932, thiết kế góc tiền bạc); cả hai được Codex đồng ý lúc 22:42–23:05, chưa gộp vì GitHub lỗi |
| PR còn lại | 3 trong 5 | Tài liệu, quy trình: #826, #929 (retro 24.11), #785 |
| Lượt tick | 77 lượt có việc, 39 lượt ngoài giờ, 5 lượt lỗi | Cả 5 lượt lỗi do GitHub trả 502/503 hoặc hết giờ kết nối (06:05, 06:56, 22:42, 23:04, 23:18) |
| Hàng chờ trống | 27 phút | |
| Từ mở PR tới gộp | 0 PR mở và gộp trong ngày. 5 PR gộp đều cũ: 14 giờ (#929) tới 125 giờ (#787) | Hôm qua 5 PR mở và gộp trong ngày |
| Việc đang làm / trần | kế hoạch 0/1, chờ review 0/1; Daily 6/1 và 0/1; quy trình **20/1** và 2/1 | `collab-turn --report`. Hôm qua quy trình 22/1 |
| PR xung đột chờ Claude sửa | **14** | 5 câu Daily (#849, #851, #859, #861, #862), 8 PR Hợp gu (#793, #800, #802, #804, #807, #811, #825, #830), #840 Tarot. #787 gộp lúc 17:05 làm lộ xung đột ở chuỗi Hợp gu |
| PR quá cỡ chờ tách | 4 (#795, #796, #797, #799, chuỗi "Hỏi về tháng này") | Không đổi |
| Issue sửa sau đang mở | **201** | Hôm qua 198. Hôm nay mở 4 (#930, #931, #936, #937), đóng 0 |
| Mức dùng Claude trong tuần | 87% đầu ngày, 90% lúc 22:49 | Chế độ tiết kiệm cả ngày: chỉ sự cố, an toàn và gộp PR đã duyệt |

Codex: 20 kết luận tự động trên 9 PR, 6 đồng ý, 14 yêu cầu sửa. Không có P0. 10 lượt Codex tự viết plan và code cho #704, #709. 2 lượt còn lại là soát đêm và chấm người giả.

## 3. Mất thời gian ở đâu

| Chuyện | Bao lâu | Vì sao | Đã sửa chưa |
|---|---|---|---|
| Codex soát lại khi không có gì mới | **9 trong 14** lượt yêu cầu sửa: #894 ×3 (10:33, 14:33, 18:04), #899 ×3 (11:20, 15:20, 18:51), #858 ×3 (12:07, 16:07, 19:59) | Máy đồng bộ nhánh với integration sau mỗi lần gộp rồi gọi Codex lại; Codex tự ghi "delta rỗng" và lặp lại đúng lỗi cũ | Chưa. Đây là S61, **ngày thứ ba liên tiếp**; hôm qua 3 lượt, hôm nay 9. Không mở được PR sửa vì làn quy trình 20/1 và Claude ở chế độ tiết kiệm |
| Ba PR quy trình chiếm đầu hàng | Từ 07:18 tới khoảng 21:30 máy xoay vòng #894 → #899 → #858, mỗi vòng: đồng bộ, chờ CI khoảng 35 phút, Codex soát | Thứ tự hàng đưa sự cố (#894) lên trước; #894 chưa qua nên mỗi vòng đều lặp | Chưa. #894 và #899 có bản sửa thật lúc 20:01 và vẫn bị yêu cầu sửa (lượt 8), nay mang nhãn chờ owner |
| Máy chờ CI | 141 lần kiểm trả "chưa xong", 20 lần "đạt", 17 lần đồng bộ nhánh, 5 lần gộp | Như hôm qua (402 lần); ít hơn vì ít PR được gộp | Chưa. S38 |
| GitHub lỗi cuối ngày | 22:42 tới lúc viết bản này: 3 lượt tick lỗi, soát đêm 2 lần không đăng được kết quả | GitHub trả 502 và lỗi GraphQL. #932, #933 đã được đồng ý nhưng chưa gộp | Máy tự thử lại ở lượt sau. Chưa có thử lại ngay trong lượt (S63 mới) |
| Autopilot không sửa PR nào | Cả ngày | Claude 87–90% mức dùng tuần; luật tiết kiệm không cho mở việc mới. `queue.md` không có ghi chú lượt nào của ngày 25.11 | Theo luật có sẵn. Codex làm thay 2 việc kế hoạch (#704, #709) |
| #874 (lô câu Codex chấm 22.11) trượt kiểm của tác giả | Từ 17:15, còn mở | CI đỏ ở bước kiểm; chưa ai xem | Chưa. Việc cho lượt autopilot kế |

## 4. PR cần từ 3 vòng review

| PR | Vòng | Nguyên nhân gốc |
|---|---|---|
| #858 (biên nhận cho tick, soát đêm, người giả) | lượt soát 10, 11, 12 hôm nay, cả ba delta rỗng; còn mở | Không có bản sửa nào trong ngày. Lỗi còn lại như 24.11: chạy lại cùng ngày xoá kết quả hỏng. Bảng mọi đường hỏng (S54) vẫn chưa viết |
| #894 (Codex sửa thay khi Claude hết mức) | lượt 4 tới 8; còn mở, chờ owner | Lượt 4: 4 lỗi chặn về chạy mã của nhánh trên máy. Lượt 5–7 rỗng. Bản sửa 20:01 đóng 2 trong 4; còn 2 lỗi về cách ly quyền đọc. Vẫn là thiếu mô hình mối nguy viết trước khi code (nhận định 23.11) |
| #899 (chuyển việc sớm ở 75/85/95%) | lượt 4 tới 8; còn mở, chờ owner | Chồng trên #894 nên mang cùng lỗi hộp cát. Lượt 5–7 rỗng. S60 (giữ PR chồng tới khi PR gốc qua) chưa làm |

Sáu PR được đồng ý hôm nay (#848, #929, #785, #787, #933, #932) đều qua ngay ở lượt soát trong ngày.

## 5. Điều tốt, có bằng chứng

- Khi Claude hết mức, việc kế hoạch vẫn đi: Codex viết plan, code và tự sửa theo review cho #704 và #709 trong khoảng một giờ (20:21–21:20), cả hai PR được đồng ý ngay lượt soát đầu.
- #787 gộp sau 5 ngày chờ; đây là PR đứng đầu chuỗi Hợp gu.
- #848 gộp, gỡ nút cho 15 PR câu Daily từng đứng sau nó.
- PR mở giảm từ 43 xuống 41; làn quy trình từ 22 xuống 20.
- Không lượt tick nào lỗi do mã của mình; cả 5 lượt lỗi đều từ phía GitHub.
- Chế độ tiết kiệm chạy đúng luật: không phiên nào mở việc mới khi Claude ở 87–90%.

## 6. Điều chưa tốt

- Chỉ 2 PR người dùng thấy được, 0 việc lên bản chạy thật, máy ghi 0/3 việc đạt.
- 9 lượt Codex bỏ phí cho soát rỗng, gấp ba hôm qua. S61 nằm trong hàng đợi ba ngày.
- 14 PR xung đột chờ Claude sửa (hôm qua 5) trong lúc Claude không được mở việc mới.
- Nợ sửa sau 201, ngày thứ tư không đóng issue nào.
- L18 (hạn 23.11) và L20 (hạn 21.11) vẫn quá hạn. Hạn giữ nguyên; chỉ owner được đổi hạn bài học.
- Không có issue plan riêng cho ngày; máy tự chọn việc. Hai việc kế hoạch máy chọn (#714, #715) không ai bắt đầu.
- Câu hỏi "vì sao máy ghi 0 việc đạt dù #703 đã gộp đủ ba phần" (đặt ra 24.11) chưa ai xem.

## 7. Học từ GitHub và nguồn gốc (kiểm 25.11.2026)

| Vấn đề | Cách làm học được | Nguồn | Mình áp dụng thế nào |
|---|---|---|---|
| GitHub trả 502/503, lượt tick bỏ dở (5 lượt) | Không bỏ qua lỗi 4xx/5xx lặp lại. Có `retry-after` thì chờ đúng số giây đó; bị giới hạn phụ thì chờ lâu dần giữa các lần thử và dừng sau một số lần nhất định. Hỏi định kỳ thì dùng yêu cầu có điều kiện (ETag), trả 304 không tính vào hạn mức | [GitHub Docs — Best practices for using the REST API](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api) (đọc 25.11) | Trang không có hướng dẫn riêng cho lỗi 5xx. Mình áp dụng phần "chờ lâu dần, có trần số lần" cho bước ghi comment và gộp: thử lại tối đa 3 lần trong cùng lượt (S63). Không thử lại vô hạn |
| Máy hỏi CI 141 lần "chưa xong" | Cùng trang: nên dùng webhook thay vì hỏi định kỳ; nếu phải hỏi thì dùng yêu cầu có điều kiện | như trên | Webhook cần máy chủ nhận, tức dịch vụ mới, thuộc quyền owner; không đề xuất. Yêu cầu có điều kiện ghi thêm vào S38 |
| Codex soát lại khi nhánh chỉ đồng bộ (ngày thứ ba) | Như 23.11: lời yêu cầu sửa còn nguyên tới khi có bản sửa | [GitHub Docs — About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) (đọc 23.11, hôm nay không mở lại) | S61, không đổi |

## 8. Chống AI bị "rotten" — cập nhật 25.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6 và các bản 08.11–24.11. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Lãng phí đã biết tăng lên khi không ai sửa | Soát rỗng: 3 lượt (24.11) → 9 lượt (25.11), cùng một nguyên nhân |
| Bản sửa quy trình bị chính quy trình chặn | S61 cần PR quy trình; làn quy trình 20/1 và chế độ tiết kiệm đều cấm mở |

**Điều học thêm:** một bản sửa giúp tiết kiệm lượt Codex và mức dùng Claude nên được xếp như sự cố, vì càng để lâu càng tốn đúng thứ đang thiếu. Xếp lại như vậy là đổi thứ tự hàng trong luật có sẵn (sự cố đi trước), không phải luật mới; ghi cho lượt autopilot kế.

## 9. Cần owner

Không có mục mới từ retro. Bản chụp ghi 9 PR mang nhãn chờ owner; #894, #899 và #906 mới thêm hôm nay do Codex gắn trong kết luận, sáu PR còn lại có từ trước. Retro không hỏi lại.

## 10. Giải pháp, xếp theo tác động

Hôm nay **không mở PR quy trình mới**: làn quy trình 20/1, Claude ở 90% mức dùng tuần (chế độ tiết kiệm), và lượt retro bắt đầu sau 23:35 (R9). Các việc AUTO nằm trong hàng đợi autopilot theo thứ tự dưới đây.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S61 | Không gọi Codex soát lại khi kết luận gần nhất là yêu cầu sửa và từ đó chỉ có commit đồng bộ | GitHub Docs (duyệt cũ) | cả 5 "không" | AUTO | **Ưu tiên 1, xếp như sự cố.** 9 lượt phí hôm nay. Trễ ngày thứ ba |
| S60 | Giữ PR chứa trọn commit của một PR mở khác tới khi PR gốc được đồng ý | luật giữ xếp chồng có sẵn | cả 5 "không" | AUTO | Chưa làm. Hôm nay #899 tốn 5 lượt vì lỗi của #894 |
| — | Gỡ xung đột: 8 PR Hợp gu theo thứ tự chuỗi (bắt đầu #793), rồi 5 câu Daily, rồi #840; xem CI đỏ của #874 và #836 | R7 | cả 5 "không" | AUTO | Khi Claude có mức dùng, hoặc Codex làm thay |
| S63 | Bước ghi comment và gộp thử lại tối đa 3 lần, chờ lâu dần, khi GitHub trả 5xx | GitHub Docs (REST best practices) | cả 5 "không" | AUTO | Mới |
| S54 | #858: bảng mọi đường hỏng của biên nhận người giả, mỗi dòng một test chạy thật | retro 21.11 | cả 5 "không" | AUTO | Chưa làm |
| — | Xem vì sao máy ghi 0 việc đạt dù #703 đã gộp đủ ba phần | số bản chụp | cả 5 "không" | AUTO | Chưa làm (từ 24.11) |
| S62 | Tick tự nhả quyền sửa PR khi phiên giữ đã ghi "xong" hoặc quá 2 giờ không có nhịp | chuyện #915 hôm 24.11 | cả 5 "không" | AUTO | Chưa làm |
| S30 + S49 | Lệnh mở PR từ chối khi làn chạm trần | Dependabot | cả 5 "không" | AUTO | **Trễ lần mười** |
| L18, L20 | Người lập plan đổi theo tuần; kiểm chính Codex tuần này | lời hứa L18, L20 | cả 5 "không"; L20 dùng 1 lượt Codex | AUTO | Quá hạn; hạn giữ nguyên |
| S29 phần mở rộng, S59, S58, S38 (thêm yêu cầu có điều kiện), S41, S50, S53, S55, S56 | Như retro 23.11 | retro 17.11–23.11 | cả 5 "không" | AUTO | Chưa làm |
| S36, S37, S43, S27+, S51, S45, S33, S34, S42 | Như retro 20.11 | retro 14.11–19.11 | cả 5 "không" | AUTO | Chưa làm. Nợ sửa sau hôm nay: 201 |

## 11. Bước bị chặn

Không có tới lúc viết file này.
