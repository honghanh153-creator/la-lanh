# Nhìn lại vòng tự động Claude ⇄ Codex: 21.11.2026

Tác giả: Claude (lượt retro tự động 21.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Báo số việc thật, không chia cho chỉ tiêu nào. Retro 18–20.11 nằm trong PR #818, chưa gộp; bản này đi chung PR đó.

## 1. Số chính thức (bản chụp, chép nguyên)

- Đã gộp vào integration hôm nay: 16 PR (số PR, không phải số việc).
- Việc đạt tiêu chí: 0/3 việc đã chọn đạt đủ tiêu chí; 3 PR chưa gắn việc (#806, #757, #768), không tính.
- Việc kế hoạch 7 tuần: đã chọn 2 (tối thiểu 2 khi có việc sẵn sàng), đạt 0.
- PR đang mở: 50.
- Sự cố đang mở: #782 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-20 (từ 20/11 10:22); #511 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-14 (từ 14/11 18:29); #470 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-13 (từ 13/11 17:22); #408 [ops-alert] staging-ready failed 2026-11-10 15:29 UTC (từ 10/11 22:29); #370 [ops-alert] collab loop 2026-11-09 (từ 09/11 17:08); #368 [ops-alert] collab loop 2026-11-09 (từ 09/11 14:06); #352 [ops-alert] ssh failed 2026-11-08 15:29 UTC (từ 08/11 22:40); #334 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 20:51); #322 [ops-alert] collab loop 2026-11-08 (từ 08/11 17:09); #321 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 16:18); #318 [ops-alert] collab loop 2026-11-08 (từ 08/11 13:25); #317 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 13:25); #313 [ops-alert] collab loop 2026-11-08 (từ 08/11 10:51); #312 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-08 (từ 08/11 10:21); #311 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-08 (từ 08/11 05:07); #310 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-07 (từ 08/11 00:14); #309 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 23:24); #308 [ops-alert] collab loop 2026-11-07 (từ 07/11 22:53); #305 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 19:21); #304 [ops-alert] collab loop 2026-11-07 (từ 07/11 18:51); #303 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 17:20); #289 [ops-alert] collab loop 2026-11-07 (từ 07/11 13:21); #287 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-07 (từ 07/11 11:20); #285 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 10:29); #277 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-06 (từ 07/11 06:03); #276 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-07 (từ 07/11 06:03); #266 [ops-alert] collab loop 2026-11-06 (từ 06/11 13:54); #261 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-05 (từ 06/11 11:32); #260 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-06 (từ 06/11 11:32); #259 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-06 (từ 06/11 11:32); #244 [ops-alert] collab loop 2026-11-05 (từ 05/11 22:56); #231 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #230 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #205 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 04:46); #204 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 23:44); #196 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 20:33); #193 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 14:42).
- Lượt Codex hôm nay: 34/80; lỗi liên tiếp: 0.
- Lời hứa sửa quy trình: 47/54 đã chạy thật (đã merge, Codex duyệt), 4 đang làm, 1 chờ owner, 2 owner quyết không làm, rủi ro vẫn còn (L17, L24), **2 quá hạn** (L11, L13), ghi xong nhưng chưa có bằng chứng merge + Codex duyệt: L11, L13.

Nguồn: bản chụp 2026-11-21 khung retro, lấy lúc 23:36, integration 625991c · snapshot 894ec1a8709f

Các số ở những mục dưới lấy từ: `logs/tick-2026-11-21.log`, `state/2026-11-21.json`, `collab-turn --report` và `collab-metrics` (23:40), `gh pr list` (PR gộp trong ngày), 26 comment `Review verdict` của Codex trên 18 PR trong ngày, `queue.md` của autopilot, `git log origin/main`.

## 2. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| Việc người dùng thấy được (vào integration) | **4** | Câu từ biệt "đi xa mãi mãi" có thêm chữ phía sau được nhận ra và chuyển sang hỗ trợ (#808). Tiêu đề Daily không còn nói sẵn "bạn đang mệt" khi đã có câu viết lại (#788). Khám phá và Aura không lặp câu giữa các thẻ (#774). Lô câu Codex duyệt 19.11 (#757) |
| Việc đã lên bản chạy thật | **1** | #808, qua bản hotfix #824, gộp `main` lúc 12:52 (R12) |
| Việc kế hoạch 7 tuần | 0 đạt tiêu chí | Đã gộp 4 PR thuộc kế hoạch (#806, #823, #827: bộ chấm người giả, mốc chưa đạt; #768: máy kiểm lộ dữ liệu ở file tải về và ảnh chia sẻ) |
| PR còn lại | 12 trong 16 | Daily chống lặp chủ đề: plan, hàm chọn (chưa nối vào app) và tiêu chí (#841, #842, #857); 5 PR quy trình và tài liệu |
| Lượt tick báo lỗi | 0 | Một lượt CI đỏ ở #842 (20:43), sau đó xanh |
| Hàng chờ trống | 0 phút | |
| Từ mở PR tới gộp (từ 14.11, 162 PR) | trung bình 15,6 giờ | 67% qua review lần đầu; 66% có việc sửa tiếp |
| Việc đang làm / trần | kế hoạch 1/1, chờ review 0/1; Daily 9/1 và 2/1; quy trình **24/1** và 7/1 | `collab-turn --report` |
| PR bị giữ vì "cùng file" | **31** trong 50 PR mở | 18 chờ #847, 6 chờ #776, 5 chờ #820, 2 chờ #864 |
| Issue sửa sau đang mở | **169** | Hôm qua 156. Hôm nay mở 15, đóng 2 |

Codex: 26 kết luận tự động trên 18 PR, 22 đồng ý, 4 yêu cầu sửa (#768 hai lần, #808, #847), mỗi lần một lỗi chặn. Không có P0. 8 lượt còn lại là chạy tay, trong đó 3 lượt cho bản hotfix #824.

## 3. Mất thời gian ở đâu

| Chuyện | Bao lâu | Vì sao | Đã sửa chưa |
|---|---|---|---|
| Integration đỏ sau khi gộp #747 | 19:21 tới 21:19, gần 2 giờ. Mọi PR đồng bộ trong lúc đó đều đỏ theo | #747 chỉ sửa file luật nên CI xếp là "tài liệu" và không chạy test nào. Nhưng file này có code đọc: nó dài quá giới hạn của hook nên 4 test hỏng | Đã sửa file (#863). Bản sửa CI (#864) còn mở |
| 31 PR đứng sau 4 PR "cùng file" | Cả ngày. #847 mở từ sáng, tới 23:40 vẫn chờ kiểm | Luật giữ theo tên file, không theo xung đột thật. Một PR đầu hàng chậm là cả hàng đứng | Chưa. S29; bản đo thử (#850) có rồi nhưng chính nó cũng đang bị giữ |
| Làn quy trình 24 việc đang làm, trần là 1 | Hôm qua 20, hôm nay 24 | Việc sửa quy trình được viết nhanh hơn tốc độ gộp. Làn quy trình đứng cuối thứ tự R7 | Chưa. S30 trễ lần sáu |
| Vòng không chạy 07:48–10:03 | 2 giờ 15 phút | Log không có dòng nào trong khoảng này; nguyên nhân không đọc được từ log. Autopilot đã báo lúc 10:00 | Chưa rõ nguyên nhân |
| #808 chờ từ 20.11 | Mở 20.11 15:12, gộp 21.11 10:39 (19,4 giờ), 7 vòng review | Mục 4 | Đã gộp và đã lên bản chạy thật |
| PR cũ gộp rất muộn | #743 74 giờ, #747 69 giờ, #761 và #757 47,6 giờ | #743, #747, #761 mỗi PR chỉ một vòng Codex; thời gian còn lại là chờ lượt | Chưa. S47 (#843) còn mở |

Hàng đợi autopilot không có ghi chú lượt nào sau 13:48. Hôm nay không có issue báo động mới, nên chưa kết luận được là lượt bị lỡ hay chỉ không ghi.

## 4. PR cần từ 3 vòng review

| PR | Vòng | Nguyên nhân gốc |
|---|---|---|
| #808 (câu từ biệt "đi xa mãi mãi") | sửa ×6 (5 lần hôm 20.11, 1 lần 07:48), đồng ý 10:29 | Luật chữ cố nhận ra từng kiểu câu xấu; mỗi vòng Codex tìm ra một kiểu nữa. Retro 20.11 đã ghi S54 (đổi sang mặc định hỗ trợ). Phần máy của S54 (bắt nộp bảng cả loại sau 3 lần sửa) chưa thấy PR |
| #768 (máy kiểm lộ dữ liệu trong PNG) | sửa, sửa, đồng ý | Cùng một kiểu: máy kiểm đi tìm dữ liệu ở từng chỗ, từng cách viết. Vòng 1 sót tên bảng màu và chữ EXIF hai byte. Vòng 2 sót ngày viết kiểu `YYYY:MM:DD` |
| #841 (plan Daily chống lặp) | đồng ý ×3 | Không có lỗi. Đầu nhánh đổi do đồng bộ nên phải xin duyệt lại (S38) |

#808 và #768 là một bài học: liệt kê cái được phép dễ làm đúng hơn cố nhận ra mọi cái xấu (đã ghi ở retro 19.11, #411).

## 5. Điều tốt, có bằng chứng

- Lỗi an toàn #808 đi trọn đường trong nửa ngày: Codex đồng ý 10:29, gộp 10:39, hotfix lên bản chạy thật 12:52, có 3 lượt Codex soát bản hotfix và hành trình sau phát hành.
- Sự cố integration đỏ được tìm ra nguyên nhân, sửa và gộp trong 2 giờ (#863); PR sửa gốc ở CI mở cùng lúc (#864, bài học L59).
- Lời hứa sửa quy trình đã chạy thật: 47/54 (17.11 là 37/47).
- Lượt Codex 34/80, không có lượt lỗi. 22 trong 26 kết luận là đồng ý.
- Ba dòng trạng thái cũ trong bảng luật (R2, R7, R10; nêu từ retro 17.11) đã sửa trong #863.
- Thử nghiệm 3+3 đã có bản nhìn lại và quyết định (#829).

## 6. Điều chưa tốt

- 0/3 việc đã chọn đạt đủ tiêu chí; 0 việc kế hoạch 7 tuần đạt.
- 50 PR mở, 31 PR bị giữ vì "cùng file". Phần lớn tính năng Hợp gu, Hỏi về tháng này và các lô câu Daily đang nằm trong hàng này.
- Làn quy trình 24/1. Các việc S của retro trước (S29, S30, S38, S41, S47…) phần nhiều đã có PR nhưng chưa PR nào gộp, nên hạn lại trôi.
- Nợ sửa sau 156 lên 169; mở 15, đóng 2.
- Hai lời hứa quá hạn (L11, L13) vẫn nguyên.
- PR retro 18–20.11 (#818) mở từ đêm 20.11, chưa tới lượt kiểm.

## 7. Học từ GitHub và nguồn gốc (kiểm 21.11.2026)

| Vấn đề | Cách làm học được | Nguồn | Mình áp dụng thế nào |
|---|---|---|---|
| #747: PR "chỉ tài liệu" làm hỏng test | GitHub ghi rõ: workflow bị bỏ qua do lọc theo đường dẫn thì check bắt buộc đứng ở "Pending" và chặn gộp. Tức là lọc theo đường dẫn phải do chính workflow quyết bên trong, và danh sách "file nào là tài liệu" là một phần của cổng | [GitHub Docs — Workflow syntax, paths](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#onpushpull_requestpull_request_targetpathspaths-ignore) | `pr-check` đã quyết bên trong (bước `scope`), nên không bị kẹt "Pending". Thiếu sót là coi mọi `.md` là tài liệu. #864 sửa đúng chỗ: file tài liệu nào có script nêu tên thì chạy test vòng. Không cần đổi cài đặt repo |
| Làn quy trình 24/1; luật WIP chỉ là chữ | Bot mở PR có trần cứng: Dependabot dừng mở PR mới khi số PR đang mở chạm `open-pull-requests-limit` (mặc định 5) cho tới khi có PR được gộp hoặc đóng. Renovate có `prConcurrentLimit` và `prHourlyLimit` (giá trị mặc định chưa đọc được nguyên văn, không ghi ở đây) | [GitHub Docs — Dependabot options](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference); [Renovate — Configuration options](https://docs.renovatebot.com/configuration-options/) | S30: lệnh mở PR đếm PR đang mở của làn và từ chối khi chạm trần, giống hai bot này. Trần là số trong luật R7, không đổi luật |
| 31 PR bị giữ vì "cùng file" | Không tra nguồn mới. Dùng lại `git merge-tree --write-tree` (retro 20.11) | [git-merge-tree](https://git-scm.com/docs/git-merge-tree) | S29, ưu tiên 1. #850 (đo thử mỗi giờ) nên được kiểm trước các PR quy trình khác |
| #768: máy kiểm metadata PNG sót từng kiểu | Định tra danh sách loại khối trong chuẩn PNG của W3C; trang trả lỗi 403 nên **chưa kiểm được nguồn** | (chưa có) | S57 chỉ dựa trên bài học nội bộ #411: kiểm ảnh chia sẻ theo danh sách khối được phép, khối lạ là đỏ. Trước khi làm phải đọc được chuẩn PNG từ nguồn chính |
| Đồng bộ nhánh, xin duyệt lại | Merge queue | [GitHub Docs — Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | Trang hôm nay vẫn không ghi loại tài khoản nào dùng được. Giữ kết luận retro 16.11 |

## 8. Chống AI bị "rotten" — cập nhật 21.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6 và các bản 08.11–20.11. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| File chỉ dẫn lớn dần tới lúc bị cắt mà không ai thấy | #747 thêm một luật làm file luật dài 9.153 ký tự, quá giới hạn 9.000 của hook. Hook lặng lẽ chỉ gửi bản rút gọn cho mọi phiên; chỉ có test báo |
| Viết cách sửa nhanh hơn đưa được vào chạy | 24 PR quy trình đang mở. Retro nào cũng thêm việc S mới trong khi việc S cũ chưa gộp |

**Điều học thêm:** tài liệu mà code đọc thì là code: phải qua cùng test. Và một bản retro thêm việc mới khi hàng cũ chưa gộp chỉ làm hàng dài hơn; hôm nay retro chỉ thêm một việc mới (S57) và xếp lại thứ tự gộp.

**Biện pháp đã vào code hôm nay:** file luật về dưới giới hạn (#863). Đang chờ: #864.

## 9. Cần owner

Không có mục mới. Không có PR nào mang nhãn chờ owner trong bản chụp hôm nay.

## 10. Giải pháp, xếp theo tác động

Làn quy trình đang 24 việc làm và 7 chờ review, trần là 1 và 1. Vì vậy hôm nay **không mở PR quy trình mới**; bản retro này đi chung PR #818. Lượt retro bắt đầu 23:36, sau giờ không mở việc mới (R9). Việc cần làm trước là **gộp cái đã viết**, theo thứ tự dưới đây.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S29 | Giữ PR "cùng file" chỉ khi gộp thử báo xung đột thật. Đưa #850 lên đầu hàng quy trình | git-merge-tree | cả 5 "không" | AUTO | Hạn 22.11. 31 PR đang bị giữ |
| L59 | Tài liệu có script đọc thì chạy test vòng (#864) | GitHub Docs, paths | cả 5 "không" | AUTO | PR đã mở, chờ kiểm |
| S47 | Tick làm theo làn đúng thứ tự R7 (#843) | R7 | cả 5 "không" | AUTO | PR đã mở, chờ #864 |
| S30 + S49 | Lệnh mở PR từ chối khi làn chạm trần; gỡ quá tải làn quy trình đi trước | Dependabot, Renovate | cả 5 "không" | AUTO | **Trễ lần sáu**, hạn mới 22.11. Không viết thêm việc quy trình mới cho tới khi làn về dưới 5 |
| S54 (phần máy) | PR bị yêu cầu sửa 3 lần cùng loại lỗi thì lượt sửa kế phải nộp bảng cả loại | retro 19.11, 20.11 | cả 5 "không" | AUTO | Trễ hạn 21.11, hạn mới 23.11 |
| S57 | Máy kiểm ảnh chia sẻ theo danh sách khối PNG được phép; khối lạ là đỏ | bài học #411; nguồn PNG chưa kiểm được | cả 5 "không"; bảo vệ dữ liệu người dùng | AUTO | Mới, hạn 24.11, thuộc làn kế hoạch (#691) |
| S38, S41, S46+, S50, S53, S55, S56 | Như retro 20.11 | retro 17.11–20.11 | cả 5 "không" | AUTO | Trễ hạn 21.11, hạn mới 23.11. Ba dòng R2, R7, R10 của S46 đã xong ở #863 |
| S36, S37, S43, S27+, S51, S45, S33, S34, S42 | Như retro 20.11 | retro 14.11–19.11 | cả 5 "không" | AUTO | Hạn 22.11 giữ nguyên. Nợ sửa sau hôm nay: 169 |

## 11. Bước bị chặn

Không có tới lúc viết file này.
