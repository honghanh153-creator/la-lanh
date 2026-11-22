# Nhìn lại vòng tự động Claude ⇄ Codex: 20.11.2026

Tác giả: Claude (lượt retro tự động 20.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Báo số việc thật, không chia cho chỉ tiêu nào. Retro 18.11 và 19.11 (trước ở #748, #764, không ai review) được gộp vào cùng PR này ngày 21.11 để chỉ cần một lượt review.

## 1. Số chính thức (bản chụp, chép nguyên)

- Đã gộp vào integration hôm nay: 11 PR (số PR, không phải số việc).
- Việc đạt tiêu chí: 0/1 việc đã chọn đạt đủ tiêu chí; 4 PR chưa gắn việc (#411, #757, #740, #756), không tính.
- Việc kế hoạch 7 tuần: đã chọn 2 (tối thiểu 2 khi có việc sẵn sàng), đạt 0.
- PR đang mở: 36 (chờ owner: #127).
- Sự cố đang mở: #782 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-20 (từ 20/11 10:22); #511 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-14 (từ 14/11 18:29); #470 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-13 (từ 13/11 17:22); #408 [ops-alert] staging-ready failed 2026-11-10 15:29 UTC (từ 10/11 22:29); #370 [ops-alert] collab loop 2026-11-09 (từ 09/11 17:08); #368 [ops-alert] collab loop 2026-11-09 (từ 09/11 14:06); #352 [ops-alert] ssh failed 2026-11-08 15:29 UTC (từ 08/11 22:40); #334 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 20:51); #322 [ops-alert] collab loop 2026-11-08 (từ 08/11 17:09); #321 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 16:18); #318 [ops-alert] collab loop 2026-11-08 (từ 08/11 13:25); #317 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 13:25); #313 [ops-alert] collab loop 2026-11-08 (từ 08/11 10:51); #312 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-08 (từ 08/11 10:21); #311 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-08 (từ 08/11 05:07); #310 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-07 (từ 08/11 00:14); #309 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 23:24); #308 [ops-alert] collab loop 2026-11-07 (từ 07/11 22:53); #305 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 19:21); #304 [ops-alert] collab loop 2026-11-07 (từ 07/11 18:51); #303 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 17:20); #289 [ops-alert] collab loop 2026-11-07 (từ 07/11 13:21); #287 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-07 (từ 07/11 11:20); #285 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 10:29); #277 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-06 (từ 07/11 06:03); #276 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-07 (từ 07/11 06:03); #266 [ops-alert] collab loop 2026-11-06 (từ 06/11 13:54); #261 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-05 (từ 06/11 11:32); #260 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-06 (từ 06/11 11:32); #259 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-06 (từ 06/11 11:32); #244 [ops-alert] collab loop 2026-11-05 (từ 05/11 22:56); #231 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #230 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #205 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 04:46); #204 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 23:44); #196 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 20:33); #193 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 14:42).
- Lượt Codex hôm nay: 48/80; lỗi liên tiếp: 0.
- Lời hứa sửa quy trình: 46/53 đã chạy thật (đã merge, Codex duyệt), 4 đang làm, 1 chờ owner, 2 owner quyết không làm, rủi ro vẫn còn (L17, L24), **1 quá hạn** (L13), ghi xong nhưng chưa có bằng chứng merge + Codex duyệt: L11, L13.

Nguồn: bản chụp 2026-11-20 khung retro, lấy lúc 23:36, integration 8b2c29f · snapshot 23a2feefb114

Các số ở những mục dưới lấy từ: `logs/tick-2026-11-20.log`, `state/2026-11-20.json`, `collab-turn --report` và `collab-metrics` (23:37), `gh pr list` (PR gộp trong ngày), 44 comment `Review verdict` của Codex trên 19 PR trong ngày, `queue.md` của autopilot, `git log origin/main`. Mức lỗi P0/P1/P2 đếm theo chữ xuất hiện trong comment của Codex, không đọc từng lỗi.

## 2. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| Việc người dùng thấy được (vào integration) | **3** | Hồ sơ chỉ có ngày sinh hoặc giờ khoảng cũng giữ được việc của Note hôm nay (#740). Home hiện và đổi được việc đang giữ, mất mạng thì nói đúng là chưa đổi (#756). Người chỉ có ngày sinh có thêm chủ đề Daily và câu xoay theo lần gặp (#778) |
| Câu mới còn chờ duyệt, người dùng chưa thấy | 2 PR | Câu Khám phá theo hành tinh × cung (#775); thêm 3 cặp lời Lá mỗi chủ đề Daily (#779) |
| Bảo vệ người dùng | 1 | Kho câu chặn link, thông tin liên lạc và chỗ điền dở (#411, mở từ 10.11) |
| Việc đã lên bản chạy thật | **1 bản phát hành tuần** | #769 gộp vào `main` lúc 09:26, lấy integration tới 22:31 ngày 19.11. Lần đầu `main` đổi kể từ 15.11. 11 PR gộp hôm nay chưa lên; 90 commit ở integration chưa lên `main` |
| Câu đã duyệt | **258/1870** | 17.11: 251/1605. Codex duyệt 254, owner 4 |
| Bộ Daily phục vụ được | **9/180** | Không đổi từ 17.11 |
| Việc kế hoạch 7 tuần | chọn 2, **đạt 0** | #740 và #756 đã gộp nhưng bản chụp chưa tính là đạt tiêu chí |
| PR còn lại | 5 trong 11 | 2 PR bộ mô phỏng người dùng (#781, #783), 3 PR cho vòng tự động (#780, #805, #814) |
| Lượt tick | 84 chạy, 40 nghỉ, **1 lỗi** | Lỗi lúc 21:40: lệnh đọc danh sách PR bị GitHub ngắt giữa chừng, lượt sau chạy lại bình thường |
| Hàng chờ trống | 0 phút | |
| Từ mở PR tới gộp (trung vị 7 ngày) | 3,3 giờ | 146 PR |
| Việc đang làm / trần | làn quy trình 20/1, chờ review 9/1; kế hoạch 0/1 và 2/1; Daily 2/1 và 0/1 | `collab-metrics` |
| Issue sửa sau (fix-forward) đang mở | **156** | 17.11: 127; 19.11: 144. Hôm nay mở 13, đóng 1 |

Codex: 44 kết luận review trên 19 PR, 30 đồng ý, 14 yêu cầu sửa. Trong 14 lần yêu cầu sửa: 11 lần có P1, 3 lần chỉ có P2 (#779 hai lần, #411). Không có P0.

## 3. Mất thời gian ở đâu

| Chuyện | Bao lâu | Vì sao | Đã sửa chưa |
|---|---|---|---|
| Lớp chặn câu từ biệt "đi xa mãi mãi" (#808) bị yêu cầu sửa 5 lần, chưa gộp | Mở 15:12; yêu cầu sửa lúc 16:38, 18:11, 19:44, 20:45, 23:07. 12 lần tự đồng bộ nhánh | Xem mục 4 | Chưa. S54 |
| 15 PR đứng chờ sau một PR | Cả ngày. Bảng lượt ghi "chờ PR #757 cùng file" cho 15 PR, gồm cả chuỗi "Hỏi về tháng này" và Hợp gu | #757 (lô duyệt câu 19.11) bị yêu cầu sửa lúc 10:11, sau đó xung đột với integration, tới lượt 22:48 mới gỡ xong. Luật giữ PR "cùng file" không kiểm có xung đột thật hay không | Chưa. S29 (đã hẹn "sau 20.11") |
| Một bài kiểm thử giao diện chập chờn (#763) làm đỏ 3 PR | #806 đỏ từ 15:50; #774 và #776 đỏ cả chiều và tối | Bài "giữ việc" hết giờ trên một trình duyệt giả lập. Bản sửa #814 gộp 19:07, nhưng tick không tự đồng bộ PR đang ở trạng thái "cần sửa", nên #774 và #776 cuối ngày vẫn đỏ vì lỗi đã hết | Sửa gốc xong (#814). Phần đồng bộ lại: S55 |
| Autopilot lỡ lượt 09:37 | Một lượt; các lượt chiều và tối chạy đủ | Tác vụ hẹn giờ không chạy xong; máy canh đã mở #782 | Issue #782 còn mở dù các lượt sau đã chạy |
| Thông báo điện thoại không gửi được | 2 lần (18:48, 19:48) | Ghi chú autopilot: push không gửi được, đã chuyển sang comment trên #133 | Chưa rõ nguyên nhân. S56 |
| Codex đồng ý nhiều lần trên cùng PR | #778: 5 lần, #781: 5 lần, #788: 4 lần | Chưa kiểm từng lần; nhiều khả năng do đầu nhánh đổi sau đồng bộ (đúng ca của S38) | Chưa. S38 trễ hạn |
| #780 trượt kiểm đầu vào một lần | 10:22, một lượt | Mô tả PR thiếu câu trả lời mục bảo mật | Đã gộp 14:55. S27+ (điền sẵn dòng bắt buộc) chưa làm |

## 4. PR cần từ 3 vòng review

| PR | Vòng | Nguyên nhân gốc |
|---|---|---|
| #808 (an toàn: bắt câu "đi xa mãi mãi" khi có chữ phía sau) | sửa ×5, chưa gộp | Dùng luật chữ để phân biệt lời từ biệt của người viết với câu kể về người thân đã mất. Mỗi vòng Codex đưa một kiểu câu mới lọt hoặc bị bắt nhầm (người thân ở đầu câu; cha mẹ tự xưng trong thư; "mẹ của con"; dấu hiệu thư quét cả tin nhắn), mỗi vòng thêm một luật. Ghi chú autopilot ở vòng 4 đã đề nghị đổi cách nếu vòng 5 còn lỗi cùng kiểu; vòng 5 vẫn còn |
| #783 (đo bộ chấm người giả) | sửa, sửa, đồng ý | Hai vòng đều có P1; đã gộp 13:58 |
| #779 (thêm lời Lá cho Daily) | sửa, sửa, đồng ý | Cả hai vòng chỉ có P2 về câu chữ; P2 loại câu cho người dùng chặn gộp theo luật hiện có |
| #411 (kho câu chặn link) | gộp sau 10 ngày | Hôm nay 1 lần yêu cầu sửa (P2) rồi đồng ý. Tổng cộng hơn 10 lần yêu cầu sửa từ 10.11 |

#808 lặp bài học của #640 (17.11) và #411 (19.11): vá từng ca được nêu thay vì đổi cách cho cả loại. Bảng lượt của máy giờ đã in nhắc "đã 5 lần REQUEST_CHANGES: rà cùng loại lỗi", nhưng đó mới là lời nhắc, chưa chặn.

## 5. Điều tốt, có bằng chứng

- Bản phát hành tuần đã lên bản chạy thật (#769, 09:26), lần đầu từ 15.11.
- Ba việc người dùng thấy được vào integration, hai trong đó thuộc kế hoạch 7 tuần. Lần đầu làn kế hoạch có việc được chọn (17.11: chọn 0).
- #411 gộp sau 10 ngày mở.
- Hàng chờ trống 0 phút. Lượt Codex 48/80, trong trần.
- Lời hứa sửa quy trình: 46/53 đã chạy thật (17.11: 37/47).
- Bài kiểm chập chờn #763 được sửa gốc trong một ngày (#814), không tắt bài.
- Các lượt sửa #808 đều thêm bài kiểm đỏ trước rồi mới sửa (ghi chú autopilot 19:48, 20:48).

## 6. Điều chưa tốt

- Làn quy trình 20 đang làm và 9 chờ review, trần là 1 và 1. 36 PR mở (17.11: 11).
- Nợ sửa sau lên 156; hôm nay mở 13, đóng 1.
- Bản chụp: 0/1 việc đã chọn đạt tiêu chí; 4 PR đã chọn không gắn việc.
- Bản sửa an toàn #808 chưa vào integration sau 8 giờ.
- Trong 11 PR gộp hôm nay không có PR nào cho các việc đã hẹn hạn 20.11: S47, S32, S30 + S49, S35 + S44, S38, S41, S46+, S50, S36, S37, S43, S27+. S30 trễ lần năm, S32 lần bốn.
- Hai retro 18.11 và 19.11 nằm trong PR này (gộp 21.11). Các issue báo động cũ (03.11–14.11) vẫn mở.
- Bộ Daily phục vụ được đứng ở 9/180 từ 17.11.

## 7. Học từ GitHub và nguồn gốc (kiểm 20.11.2026)

| Vấn đề | Cách làm học được | Nguồn | Mình áp dụng thế nào |
|---|---|---|---|
| 15 PR bị giữ vì "cùng file" với #757 | `git merge-tree --write-tree` gộp thử mà không đọc hay ghi thư mục làm việc và index; mã thoát 0 là gộp sạch, 1 là có xung đột | [git-merge-tree](https://git-scm.com/docs/git-merge-tree) | S29: chỉ giữ PR khi gộp thử với PR đi trước báo xung đột thật. Chạy trên máy, miễn phí, không đổi cài đặt repo |
| Bài kiểm chập chờn làm đỏ PR không liên quan | Playwright xếp bài trượt lần đầu rồi đậu khi chạy lại vào nhóm "flaky", tách khỏi "failed" | [Playwright — Retries](https://playwright.dev/docs/test-retries) | S55: khi một bài đã có issue "chập chờn" và bản sửa đã gộp, tick đồng bộ lại các PR chỉ đỏ vì bài đó. Không bật chạy lại hàng loạt để che lỗi; trang này không nêu tùy chọn làm đỏ lượt khi có bài "flaky" nên chưa dựa vào tùy chọn đó |
| Đồng bộ nhánh liên tục (#808: 12 lần) | Merge queue | [GitHub Docs — Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | Trang hôm nay vẫn không ghi điều kiện dùng. Giữ kết luận của retro 16.11 (không dùng được cho repo này) và chỉ mượn ý: đồng bộ PR sắp tới lượt gộp (S45) |
| #808: luật chữ cho câu nguy cơ, vá mãi không hết | Không tra nguồn mới hôm nay. Dùng lại bài học #411 (retro 19.11): liệt kê cái được phép thay vì cố nhận ra mọi cái xấu | retro 19.11 mục 7 | S54: mọi câu "đã đi xa mãi mãi" đều chuyển sang hỗ trợ, trừ khi câu ghi rõ người mất là người khác theo một danh sách mẫu hẹp. Nghiêng về an toàn; bắt nhầm một câu tang nhẹ hơn bỏ sót một lời từ biệt |

## 8. Chống AI bị "rotten" — cập nhật 20.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6 và các bản 08.11–19.11. Hôm nay có thêm một điều:

| Triệu chứng | Bằng chứng |
|---|---|
| Lời nhắc có sẵn nhưng không đổi hành vi | Ghi chú autopilot vòng 4 của #808 tự viết "nếu vòng 5 lại ra P1 cùng kiểu thì đổi cách". Bảng lượt cũng in nhắc rà cả loại lỗi. Lượt sau vẫn vá tiếp theo cách cũ |
| Hàng việc hẹn hạn trôi mỗi ngày | S30 trễ lần năm, S32 lần bốn; mỗi retro chỉ ghi hạn mới. S41 (đưa việc S vào sổ lời hứa để máy báo trễ) chính nó cũng trễ |

**Điều học thêm:** lời nhắc viết bằng chữ, kể cả do chính phiên trước viết, không đủ để phiên sau đổi cách. Điểm "đổi cách" phải là một bước máy chặn (S54 phần máy).

## 9. Cần owner

Không có mục mới. Bản chụp còn 1 PR chờ owner (#127, đã có từ trước).

## 10. Giải pháp, xếp theo tác động

Làn quy trình đang 20 việc làm và 9 chờ review, trần là 1 và 1. Vì vậy hôm nay **không mở PR quy trình mới** ngoài PR retro này; mọi việc AUTO cần đổi code vào hàng đợi autopilot. Lượt retro bắt đầu 23:36, sau giờ không mở việc mới (R9).

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S54 | #808: đổi cách, mặc định chuyển sang hỗ trợ, chỉ miễn cho danh sách mẫu hẹp "người khác đã mất"; kèm bảng cả loại câu và bài kiểm từng dòng. Phần máy: PR đã bị yêu cầu sửa 3 lần vì cùng loại lỗi thì lượt sửa kế phải nộp bảng cả loại, thiếu thì kiểm đầu vào báo đỏ | retro 19.11 (#411); S35 + S44 | cả 5 "không"; không đổi câu cho người dùng | AUTO | Mới, ưu tiên 1, làm ở lượt sửa #808 kế tiếp, hạn 21.11 |
| S29 | Giữ PR "cùng file" chỉ khi gộp thử báo xung đột thật | git-merge-tree | cả 5 "không" | AUTO | Đến hạn (hẹn "sau 20.11"), hạn 22.11. Ca hôm nay: 15 PR chờ #757. Codex góp ý trước |
| S55 | Sau khi bản sửa một bài chập chờn đã gộp, tick đồng bộ lại các PR "cần sửa" chỉ đỏ vì bài đó | Playwright | cả 5 "không" | AUTO | Mới, hạn 22.11. Trước mắt: lượt autopilot kế đồng bộ tay #774, #776 |
| S47 | Hàng kiểm và gộp xếp đúng thứ tự R7 | R7 | cả 5 "không" | AUTO | **Trễ hạn 20.11**, hạn mới 21.11 |
| S32 + S52 | Lô câu tự kiểm trước khi mở PR; câu "việc nên làm" phải khớp mọi cảnh | retro 14.11, 19.11 | cả 5 "không" | AUTO | S32 **trễ lần bốn**, hạn mới 21.11. #757 vẫn chưa gộp |
| S30 + S49 | Lệnh mở PR từ chối khi làn đủ việc; việc gỡ quá tải của làn quy trình đi trước | merge queue (ý tưởng) | cả 5 "không"; S49 đi bằng PR sửa bảng luật | AUTO | S30 **trễ lần năm**, hạn mới 21.11. Làn hôm nay 20/1 |
| S38 | Không gọi Codex lại khi phần của tác giả không đổi | GitHub protected branches (retro 17.11) | cả 5 "không" | AUTO | **Trễ hạn 20.11**, hạn mới 21.11. Hôm nay #778, #781, #788 có 4–5 lần đồng ý |
| S41, S46+, S50, S53 | Việc S vào sổ lời hứa; sửa dòng trạng thái cũ trong bảng luật và máy báo; chặn lệnh "sửa comment cuối" | R17 | cả 5 "không" | AUTO | S41 **trễ lần ba**; hạn mới 21.11 |
| S36, S37, S43, S27+ | Đo nợ sửa sau; lỗi đã biết không tô đỏ cả lượt; đóng issue báo động cũ (thêm #782); dòng bắt buộc điền sẵn | retro 15.11, 16.11 | cả 5 "không" | AUTO | **Trễ hạn 20.11**, hạn mới 22.11. Nợ hôm nay: 156 mở |
| S56 | Tìm vì sao thông báo điện thoại không gửi được (2 lần hôm nay) và thêm kiểm bằng máy | R5, R17 | cả 5 "không" nếu chỉ đọc log và sửa trên máy; đụng cài đặt dịch vụ thì chuyển owner | AUTO (phần tìm nguyên nhân) | Mới, hạn 21.11 |
| S51, S45, S33, S34, S42 | PR tài liệu đi thẳng tới review; đo đồng bộ và CI mỗi PR; đếm lượt Codex theo mục đích; "Cần bạn xem" một lần mỗi PR; chạy thử lệnh rà chỉ dẫn | retro 14.11–19.11 | cả 5 "không" | AUTO | Hạn 21.11, giữ nguyên |

## 11. Bước bị chặn

Không có tới lúc viết file này.
