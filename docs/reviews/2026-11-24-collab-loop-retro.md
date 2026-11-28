# Nhìn lại vòng tự động Claude ⇄ Codex: 24.11.2026

Tác giả: Claude (lượt retro tự động 24.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Báo số việc thật, không chia cho chỉ tiêu nào. Không còn ngày nào thiếu bản nhìn lại.

## 1. Số chính thức (bản chụp, chép nguyên)

- Đã gộp vào integration hôm nay: 10 PR (số PR, không phải số việc).
- Việc đạt tiêu chí: 0/2 việc đã chọn đạt đủ tiêu chí; 3 PR chưa gắn việc (#770, #858, #905), không tính.
- Việc kế hoạch 7 tuần: đã chọn 2 (tối thiểu 2 khi có việc sẵn sàng), đạt 0.
- PR đang mở: 43 (chờ owner: #904, #903, #902, #901, #900, #734).
- Sự cố đang mở: #917 [ops-alert] Claude dùng nhanh hơn nhịp tuần (từ 24/11 10:54); #782 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-20 (từ 20/11 10:22); #511 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-14 (từ 14/11 18:29); #470 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-13 (từ 13/11 17:22); #408 [ops-alert] staging-ready failed 2026-11-10 15:29 UTC (từ 10/11 22:29); #370 [ops-alert] collab loop 2026-11-09 (từ 09/11 17:08); #368 [ops-alert] collab loop 2026-11-09 (từ 09/11 14:06); #352 [ops-alert] ssh failed 2026-11-08 15:29 UTC (từ 08/11 22:40); #334 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 20:51); #322 [ops-alert] collab loop 2026-11-08 (từ 08/11 17:09); #321 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 16:18); #318 [ops-alert] collab loop 2026-11-08 (từ 08/11 13:25); #317 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 13:25); #313 [ops-alert] collab loop 2026-11-08 (từ 08/11 10:51); #312 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-08 (từ 08/11 10:21); #311 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-08 (từ 08/11 05:07); #310 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-07 (từ 08/11 00:14); #309 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 23:24); #308 [ops-alert] collab loop 2026-11-07 (từ 07/11 22:53); #305 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 19:21); #304 [ops-alert] collab loop 2026-11-07 (từ 07/11 18:51); #303 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 17:20); #289 [ops-alert] collab loop 2026-11-07 (từ 07/11 13:21); #287 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-07 (từ 07/11 11:20); #285 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 10:29); #277 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-06 (từ 07/11 06:03); #276 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-07 (từ 07/11 06:03); #266 [ops-alert] collab loop 2026-11-06 (từ 06/11 13:54); #261 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-05 (từ 06/11 11:32); #260 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-06 (từ 06/11 11:32); #259 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-06 (từ 06/11 11:32); #244 [ops-alert] collab loop 2026-11-05 (từ 05/11 22:56); #231 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #230 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #205 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 04:46); #204 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 23:44); #196 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 20:33); #193 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 14:42).
- Lượt Codex hôm nay: 25/80; lỗi liên tiếp: 0.
- Lời hứa sửa quy trình: 63/68 đã chạy thật (đã merge, Codex duyệt), 2 đang làm, 1 chờ owner, 2 owner quyết không làm, rủi ro vẫn còn (L17, L24), **2 quá hạn** (L18, L20).

Nguồn: bản chụp 2026-11-24 khung retro, lấy lúc 23:36, integration 49bd0e9 · snapshot bdae11ba4ac7

Các số ở những mục dưới lấy từ: `logs/tick-2026-11-24.log`, `state/2026-11-24.json`, `collab-turn --report` (23:40), `gh pr list` (PR gộp trong ngày), 22 comment `Review verdict` của Codex trên 16 PR trong ngày, `queue.md` của autopilot, `git log origin/main`.

## 2. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| PR người dùng thấy được (vào integration) | **7 PR** | #915, #924, #926: việc làm một mình và dòng "nhiều bạn cũng vậy" (#703, đủ ba phần: kho câu, API, màn hình); #919 cỡ và nhóm hình cho việc thường của Daily (#699 phần 2); #855 Daily tránh chủ đề đã gặp trong tuần (đang tắt, bật theo ngày); #847 thêm chủ đề "nói rõ mình cần gì" (câu chờ duyệt); #921 máy kiểm ảnh chia sẻ chỉ chứa phần được phép (#691). Máy vẫn ghi 0/2 việc đạt đủ tiêu chí |
| Việc đã lên bản chạy thật | **0** | `main` không có commit mới trong ngày |
| Việc kế hoạch 7 tuần | 0 đạt tiêu chí (số máy) | 5 PR thuộc kế hoạch đã gộp: #915, #919, #921, #924, #926 |
| PR còn lại | 3 trong 10 | Quy trình: #905 (retro 22–23.11), #837, #770 |
| Lượt tick báo lỗi | 0 | 81 lượt chạy; khoảng nghỉ dài nhất 31 phút (14:51) |
| Hàng chờ trống | 0 phút | |
| Từ mở PR tới gộp | 5 PR mở và gộp trong ngày: nhanh nhất 1 giờ (#924), chậm nhất 9 giờ (#915). 5 PR cũ: 26 giờ (#905) tới 101 giờ (#770) | Hôm qua không PR nào gộp trong ngày nó được mở |
| Việc đang làm / trần | kế hoạch 0/1, chờ review 0/1; Daily 6/1 và 1/1; quy trình **22/1** và 4/1 | `collab-turn --report`. Hôm qua Daily 9/1, quy trình 23/1 |
| PR bị giữ vì "cùng file" | **25** trong 43 PR mở | 15 chờ #848, 3 chờ #851, 3 chờ #894, 2 chờ #849, 1 chờ #787, 1 chờ #793. Hôm qua 21 |
| PR xung đột chờ Claude sửa | **5** câu Daily (#849, #851, #859, #861, #862) | Hôm qua 8. Hôm nay gỡ #847 (đã gộp), #848 (chờ kiểm), #855 (đã gộp) |
| Issue sửa sau đang mở | **198** | Hôm qua 190. Hôm nay mở 8, đóng 0 |
| Mức dùng Claude trong tuần | 80% lúc 10:54, 86% lúc 22:49 | Máy báo #917 (dùng nhanh hơn nhịp) và chuyển sang chế độ tiết kiệm từ 85% |

Codex: 22 kết luận tự động trên 16 PR, 13 đồng ý, 9 yêu cầu sửa. Không có P0. 3 lượt còn lại trong 25 là lập plan, soát đêm và chấm người giả.

## 3. Mất thời gian ở đâu

| Chuyện | Bao lâu | Vì sao | Đã sửa chưa |
|---|---|---|---|
| Codex soát lại #858 khi không có gì mới | 3 trong 5 lượt của #858 hôm nay (07:11, 08:57 và 22:18) | Nhánh chỉ được máy đồng bộ với integration; Codex tự ghi "empty review delta" và lặp lại đúng lỗi cũ | Chưa. Đây là S61, ngày thứ hai liên tiếp thấy đúng lỗi này. Không mở được PR sửa vì làn quy trình 22/1 |
| #915 bị một phiên buổi sáng giữ | 06:02 tới khoảng 15:00 (gộp 15:23) | Phiên chuẩn bị buổi sáng giữ quyền sửa PR rồi không nhả; tick báo "chờ CI" suốt, nhiều PR cùng file phải chờ | Tự hết khi #915 gộp. Chưa có máy tự nhả quyền khi phiên giữ đã ghi "xong" (S62 mới) |
| Máy chờ CI | 402 lần kiểm trả "chưa xong", 44 lần "đạt", 34 lần đồng bộ nhánh, 20 lần gộp | Mỗi lần gộp là các PR sau phải đồng bộ rồi chờ CI lại | Chưa. S38 |
| Chuỗi PR "Codex sửa thay" | 4 lượt Codex (#894, #899, #903, #904), tất cả yêu cầu sửa | Các PR chồng lên #894; #894 vẫn chưa qua về bảo mật | Chưa. S60. #900–#904 đang chờ owner |
| #919 trượt kiểm của tác giả | 2 lần CI đỏ, gộp sau 3,5 giờ | Lỗi thật trong PR, sửa xong thì qua | Đã sửa trong ngày |
| Claude vào chế độ tiết kiệm | Từ khoảng 22:49 | Mức dùng tuần 86% | Theo luật có sẵn. Lượt retro này không mở việc mới |

## 4. PR cần từ 3 vòng review

| PR | Vòng | Nguyên nhân gốc |
|---|---|---|
| #858 (biên nhận cho tick, soát đêm, người giả) | tới lượt soát thứ 9, hôm nay yêu cầu sửa ×5; còn mở | Hai nguyên nhân. (1) Mỗi lần sửa chỉ đóng một đường hỏng, Codex tìm ra đường kế: lượt hỏng vẫn ghi "xong" → điểm Codex rỗng vẫn ghi "xong" → chạy lại cùng ngày xoá mất kết quả hỏng. Bảng liệt kê mọi đường hỏng (S54) chưa được viết trước khi sửa. (2) 3 trong 5 lượt là soát lại khi chỉ có commit đồng bộ. Ngoài ra PR đổi mức từ S sang M sau khi có code nên thiếu bước Codex chấm plan; lỗi này lặp lại ở cả 3 kết luận gần nhất |
| #894 (Codex sửa thay khi Claude hết mức) | yêu cầu sửa lần 3 trong 3 ngày; còn mở | Vẫn là thiếu mô hình mối nguy cho việc chạy mã của nhánh trên máy. Như nhận định 23.11 |

Các PR người dùng thấy được hôm nay đều qua trong 1 lượt Codex.

## 5. Điều tốt, có bằng chứng

- 7 PR người dùng thấy được, nhiều nhất từ 20.11. Việc #703 đi trọn ba phần trong một ngày (#915 06:02 → #926 23:19).
- 5 PR mở và gộp trong cùng ngày; hôm qua là 0. Chia việc thành PR nhỏ theo lớp (kho câu → API → màn hình) giúp mỗi PR qua Codex ngay lượt đầu.
- Autopilot chạy lại sau một ngày im: 4 lượt sửa có ghi chú (#858, #847, #848, S57 → #921).
- S57 từ hàng đợi retro đã thành code và gộp (#921): máy kiểm ảnh chia sẻ theo danh sách phần PNG được phép.
- Daily: PR đang làm giảm từ 9 xuống 6; PR xung đột giảm từ 8 xuống 5.
- Tick chạy cả ngày không lượt lỗi; Codex không bị nhà cung cấp từ chối lượt nào (hôm qua 14 lần).
- Số PR mở giảm từ 48 xuống 43.

## 6. Điều chưa tốt

- 0 việc lên bản chạy thật; máy ghi 0/2 việc đạt đủ tiêu chí dù #703 đã gộp đủ ba phần. Cần xem vì sao máy chưa tính (có thể thiếu dòng tiêu chí đạt trong issue) — việc cho lượt autopilot kế.
- #858 tốn 5 lượt Codex trong ngày, 3 lượt không có gì mới để soát.
- S61 và S60 được đề ra hôm qua, hôm nay chưa làm, và lỗi chúng nhắm tới lặp lại y nguyên.
- Làn quy trình 22/1: không mở được PR sửa quy trình nào, kể cả bản sửa giúp giảm lãng phí. Phần lớn 22 PR này đang bị giữ hoặc chờ owner.
- Nợ sửa sau 198, ngày thứ ba không đóng issue nào.
- L18 (hạn 23.11) và L20 (hạn 21.11) quá hạn. Hạn giữ nguyên; chỉ owner được đổi hạn bài học.
- 25 PR bị giữ vì cùng file (hôm qua 21), trong đó 15 đứng sau #848; #848 đã được Codex đồng ý nhưng phải kiểm lại sau mỗi lần integration đổi.
- Không có issue plan riêng cho ngày; file trạng thái ghi "máy chọn theo cùng luật".

## 7. Học từ GitHub và nguồn gốc (kiểm 24.11.2026)

| Vấn đề | Cách làm học được | Nguồn | Mình áp dụng thế nào |
|---|---|---|---|
| PR sau phải đồng bộ rồi chờ CI lại mỗi lần có PR gộp (402 lần "chưa xong") | Merge queue: GitHub tạo nhánh tạm `merge_group` gồm nền mới nhất cộng các PR xếp trước, chạy kiểm bắt buộc trên nhánh đó; tác giả không phải tự đồng bộ nhánh | [GitHub Docs — Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) (đọc 24.11) | Trang này hôm nay **không ghi** loại tài khoản nào được dùng, nên chưa xác nhận được repo cá nhân có bật được không (retro 15.11 ghi là không). Bật là đổi cài đặt repo, thuộc quyền owner; không đề xuất lại. Mình học ý tưởng: kiểm trên bản gộp thử thay vì đồng bộ từng nhánh (S38, S29) |
| Codex soát lại khi nhánh chỉ đồng bộ (#858, ngày thứ hai) | Như 23.11: lời đồng ý cũ khi diff đổi; lời yêu cầu sửa thì vẫn còn nguyên tới khi có bản sửa | [GitHub Docs — About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) (đọc 23.11, hôm nay không mở lại) | S61, không đổi |
| Mỗi vòng review lộ thêm một đường hỏng (#858) | Không có nguồn ngoài mới. Cách của mình từ retro 21.11 (S54): liệt kê mọi đường hỏng thành bảng trước khi sửa, mỗi dòng một test chạy thật | retro 21.11 | Lượt sửa #858 kế phải nộp bảng này trong mô tả PR; Codex soát bảng một lần thay vì tìm từng đường |

## 8. Chống AI bị "rotten" — cập nhật 24.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6 và các bản 08.11–23.11. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Giải pháp nằm trong hàng đợi trong khi lỗi nó nhắm tới lặp lại | S61 ghi 23.11; hôm nay #858 lại tốn 3 lượt soát rỗng |
| Trần việc đang làm chặn luôn bản sửa giúp gỡ trần | Làn quy trình 22/1 suốt 3 ngày; S30+S49 trễ lần chín |

**Điều học thêm:** PR nhỏ theo lớp (#703: ba PR, mỗi PR một lượt Codex) đi nhanh hơn hẳn PR to sửa nhiều vòng (#858: chín lượt). Việc quy trình cũng nên chia như vậy.

## 9. Cần owner

Không có mục mới từ retro. Bản chụp ghi 6 PR mang nhãn chờ owner (#900, #901, #902, #903, #904, #734); đều đã có từ trước. Retro không hỏi lại.

## 10. Giải pháp, xếp theo tác động

Hôm nay **không mở PR quy trình mới**: làn quy trình 22/1 (luật mỗi lúc một PR quy trình), Claude ở 86% mức dùng tuần (chế độ tiết kiệm), và lượt retro bắt đầu sau 23:35 (R9). Các việc AUTO nằm trong hàng đợi autopilot, xếp lại theo thứ tự dưới đây.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S61 | Không gọi Codex soát lại khi kết luận gần nhất là yêu cầu sửa và từ đó chỉ có commit đồng bộ | GitHub Docs (duyệt cũ) | cả 5 "không" | AUTO | **Ưu tiên 1 của làn quy trình.** Lỗi lặp lại hôm nay. Đưa vào PR quy trình đầu tiên được mở |
| S54 | #858: bảng mọi đường hỏng của biên nhận người giả (hỏng, điểm rỗng, chạy lại cùng ngày, hỏng giữa chừng), mỗi dòng một test chạy thật; xin Codex chấm plan mức M | retro 21.11 | cả 5 "không" | AUTO | Lượt sửa #858 kế |
| — | Gỡ 5 PR câu Daily còn xung đột (#849, #851, #859, #861, #862), mỗi lượt một PR | R7 | cả 5 "không" | AUTO | Đang làm dần (hôm nay xong 2) |
| — | Xem vì sao máy ghi 0/2 việc đạt dù #703 đã gộp đủ ba phần | số bản chụp | cả 5 "không" | AUTO | Mới, lượt autopilot kế |
| S62 | Tick tự nhả quyền sửa PR khi phiên giữ đã ghi "xong" hoặc quá 2 giờ không có nhịp | chuyện #915 hôm nay | cả 5 "không" | AUTO | Mới, sau S61 |
| S60 | Giữ PR chứa trọn commit của một PR mở khác tới khi PR gốc được đồng ý | luật giữ xếp chồng có sẵn | cả 5 "không" | AUTO | Chưa làm |
| S30 + S49 | Lệnh mở PR từ chối khi làn chạm trần | Dependabot | cả 5 "không" | AUTO | **Trễ lần chín** |
| L18, L20 | Người lập plan đổi theo tuần; kiểm chính Codex tuần này | lời hứa L18, L20 | cả 5 "không"; L20 dùng 1 lượt Codex | AUTO | Quá hạn; hạn giữ nguyên |
| S57 | Máy kiểm ảnh chia sẻ theo danh sách phần PNG | retro 22.11 | — | AUTO | **Xong**, #921 đã gộp |
| S29 phần mở rộng, S59, S58, S38, S41, S50, S53, S55, S56 | Như retro 23.11 | retro 17.11–23.11 | cả 5 "không" | AUTO | Chưa làm |
| S36, S37, S43, S27+, S51, S45, S33, S34, S42 | Như retro 20.11 | retro 14.11–19.11 | cả 5 "không" | AUTO | Chưa làm. Nợ sửa sau hôm nay: 198 |

## 11. Bước bị chặn

Không có tới lúc viết file này.
