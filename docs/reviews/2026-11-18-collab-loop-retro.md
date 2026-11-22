# Nhìn lại vòng tự động Claude ⇄ Codex: 18.11.2026

Tác giả: Claude (lượt retro tự động 18.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Báo số việc thật, không chia cho chỉ tiêu nào. Mọi ngày trước đều đã có file retro (bản 17.11 là #682, còn mở, chưa tới lượt kiểm).

## 1. Số chính thức (bản chụp, chép nguyên)

- Đã gộp vào integration hôm nay: 14 PR (số PR, không phải số việc).
- Việc đạt tiêu chí: chưa chọn việc nào có mã việc; 5 PR chưa gắn việc (#354, #477, #411, #673, #449), không tính.
- Việc kế hoạch 7 tuần: đã chọn 0 (tối thiểu 2 khi có việc sẵn sàng), đạt 0.
- PR đang mở: 16 (chờ owner: #127).
- Sự cố đang mở: #511 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-14 (từ 14/11 18:29); #470 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-13 (từ 13/11 17:22); #408 [ops-alert] staging-ready failed 2026-11-10 15:29 UTC (từ 10/11 22:29); #370 [ops-alert] collab loop 2026-11-09 (từ 09/11 17:08); #368 [ops-alert] collab loop 2026-11-09 (từ 09/11 14:06); #352 [ops-alert] ssh failed 2026-11-08 15:29 UTC (từ 08/11 22:40); #350 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 21:53); #334 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 20:51); #322 [ops-alert] collab loop 2026-11-08 (từ 08/11 17:09); #321 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 16:18); #318 [ops-alert] collab loop 2026-11-08 (từ 08/11 13:25); #317 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 13:25); #313 [ops-alert] collab loop 2026-11-08 (từ 08/11 10:51); #312 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-08 (từ 08/11 10:21); #311 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-08 (từ 08/11 05:07); #310 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-07 (từ 08/11 00:14); #309 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 23:24); #308 [ops-alert] collab loop 2026-11-07 (từ 07/11 22:53); #305 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 19:21); #304 [ops-alert] collab loop 2026-11-07 (từ 07/11 18:51); #303 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 17:20); #289 [ops-alert] collab loop 2026-11-07 (từ 07/11 13:21); #287 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-07 (từ 07/11 11:20); #285 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 10:29); #277 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-06 (từ 07/11 06:03); #276 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-07 (từ 07/11 06:03); #266 [ops-alert] collab loop 2026-11-06 (từ 06/11 13:54); #261 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-05 (từ 06/11 11:32); #260 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-06 (từ 06/11 11:32); #259 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-06 (từ 06/11 11:32); #244 [ops-alert] collab loop 2026-11-05 (từ 05/11 22:56); #231 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #230 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #205 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 04:46); #204 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 23:44); #196 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 20:33); #193 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 14:42).
- Lượt Codex hôm nay: 41/120; lỗi liên tiếp: 0.
- Lời hứa sửa quy trình: 42/50 đã chạy thật (đã merge, Codex duyệt), 5 đang làm, 1 chờ owner, 2 owner quyết không làm, rủi ro vẫn còn (L17, L24), **1 quá hạn** (L13), ghi xong nhưng chưa có bằng chứng merge + Codex duyệt: L11, L13.

Nguồn: bản chụp 2026-11-18 khung retro, lấy lúc 23:36, integration 328073b · snapshot 85251b8a1d3e

Các số ở những mục dưới lấy từ: `logs/tick-2026-11-18.log`, `state/2026-11-18.json`, `collab-turn --report` và `collab-metrics` (23:38), `gh pr list` (PR đổi trong ngày), 27 comment `Review verdict` của Codex trên 17 PR trong ngày, `queue.md` của autopilot, comment trong ngày trên #133, `git log origin/main`.

Trần Codex 120 là mức thử hai ngày 18–19.11 owner cho (ghi trong `state`, mục Z1); bảng luật R8 vẫn ghi 80.

## 2. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| Việc người dùng thấy được (vào integration) | **2** | Người chỉ có ngày sinh nay đổi giữa hai tình huống Daily (#684). Ô chọn cảm xúc nằm dưới Note, có câu hỏi, tự gửi lại khi có mạng (#449, mở từ 12.11) |
| Việc đã lên bản chạy thật | **0** | `main` không đổi từ 15.11 11:28, ngày thứ ba. 823 commit ở integration chưa lên `main` |
| Câu đã duyệt | **252/1606** | Hôm qua 251/1605. Lô câu hôm nay (#685) chưa gộp |
| Bộ Daily phục vụ được | **9/180** | Như hôm qua |
| Việc kế hoạch 7 tuần | bản chụp ghi **0** | Plan sáng do máy chọn 5 PR cũ, không có việc kế hoạch. Trong ngày làn kế hoạch có thêm 4 PR: bộ đo 300 đường bấm giữ việc (#717, đã gộp; kết quả 100/300 đường giữ được việc), kiểm bề rộng trang đồng ý và trang riêng tư (#720, đã gộp), mở giữ việc cho hồ sơ chỉ ngày sinh và giờ khoảng (#740) và kiểm trên web (#742), hai PR sau chưa tới lượt kiểm |
| PR còn lại | 12 trong 14 | 7 PR cho vòng tự động, 3 PR kiểm thử và bước chưa bật (#717, #720, #724), 1 PR hạ tầng staging (#477), 1 PR tài liệu (#673) |
| Lượt tick báo lỗi | **0** | Như hôm qua |
| Hàng chờ trống | 0 phút | Hôm qua 10 phút |
| Từ mở PR tới gộp (trung vị 7 ngày) | 3,6 giờ | Hôm qua 3,2 giờ. 155 PR |
| PR gộp sau 19:10 | **0** | 6 PR chờ bước kiểm của tác giả tới cuối ngày, xem mục 3 |
| Việc đang làm / trần | kế hoạch 0/1 và 2/1; Daily 2/1 và 0/1; quy trình 5/1 và 4/1 | `collab-metrics` |
| Số lần tự đồng bộ nhánh | 18 | Hôm qua 52 |
| Issue sửa sau (fix-forward) đang mở | **136** | Hôm qua 127. Hôm nay mở 9, đóng 1 |

Codex: 27 kết luận review trên 17 PR, 16 đồng ý, 11 yêu cầu sửa. Trong 11 lần yêu cầu sửa: 7 lần có lỗi chặn mức P1 (#477, #684, #736, #449, #726 ba lần), 4 lần trên #411 (ba lần cuối chỉ có P2). Không có P0. 41 lượt Codex gồm 10 lượt chạy tay (6 lượt soát quy trình mỗi giờ, 3 lượt góp ý thiết kế, 1 lượt owner yêu cầu).

Lượt soát đêm (tạm tính 23:07) ghi 7 lỗi lọt sau khi Codex duyệt, 0 lần gộp thiếu biên nhận, 0 câu báo cáo sai nguồn trong 28 báo cáo.

## 3. Mất thời gian ở đâu

| Chuyện | Bao lâu | Vì sao | Đã sửa chưa |
|---|---|---|---|
| Hàng một lối: PR đầu hàng giữ cả hàng | Từ 19:10 tới cuối ngày không gộp được PR nào. Chờ bước kiểm của tác giả: #685 từ 08:05, #729 từ 10:53, #740 từ 15:00, #742 từ 15:56, #747 từ 22:14, #682 từ đêm 17.11. Log có 97 dòng "đồng bộ khi tới lượt đầu hàng" | Từ 14:35 (#736) vòng chỉ đồng bộ và kiểm PR đầu hàng. Đầu hàng là #411, bị yêu cầu sửa 4 lần trong ngày; mỗi vòng sửa, chạy CI, review mất khoảng 1,5 giờ rồi #411 lại về đầu hàng. Hai PR kế hoạch 7 tuần (#740, #742) đứng sau một PR nội dung chỉ còn lỗi P2, trái thứ tự R7 | Chưa. Autopilot đã báo kẹt 4 lần trên #133 (17:50, 18:49, 21:09 và trước đó 11:50). Xem S47 |
| PR cần CI đầy đủ bị PR nhanh chen | #673 (tài liệu) ở trong vòng từ 08:00 tới 19:10; #684 từ 09:00 tới 15:42 | Mỗi lần có PR khác gộp, PR đang kiểm phải đồng bộ và chạy lại CI khoảng 32 phút | Đã sửa 14:35: PR đầu hàng giữ chỗ (#736, L50). Bản sửa này sinh ra chuyện ở dòng trên. Còn mở: #738 |
| Đổi nhãn làm hủy lượt CI đang chạy | Buổi sáng, #684, #717, #477 bị hủy sau 8–9 phút | Vòng tự đổi nhãn trạng thái, CI coi đó là thay đổi mới | Đã sửa 12:21 (#722, L48) |
| Lô câu hôm nay (#685) đỏ CI vì đúng câu cũ | Mở 08:05, chưa gộp | Lô duyệt lại một câu chứa cụm đã bị loại. Lần thứ ba cùng lỗi (#491, #635, #685), lần thứ hai đúng câu đó | Chưa. S32 **trễ hạn lần hai** |
| Nhãn "chờ owner" gắn sai | Cả buổi sáng danh sách PR báo chờ owner cho PR chỉ chờ PR khác hoặc đang nháp | Nhãn dùng chung cho mọi lý do giữ | Một nửa: #727 gộp 12:48 (L49); #743 cho PR nháp còn mở (L52). Cuối ngày #726, #104, #68 vẫn mang nhãn "chờ owner" dù chỉ là nháp |

## 4. PR cần từ 3 vòng review

| PR | Vòng | Nguyên nhân gốc |
|---|---|---|
| #411 (chặn link, số liên lạc trong kho câu) | tổng 7 lần yêu cầu sửa, hôm nay 4; chưa gộp | Tự viết luật nhận ra tên miền bằng cách liệt kê đuôi. Mỗi vòng Codex đưa một kiểu đuôi mới lọt qua: chữ hoa lẫn chữ thường, đuôi viết hoa chữ đầu, đuôi không phải chữ Latin. Liệt kê thì không bao giờ hết |
| #726 (Daily giờ gần đúng dùng vị trí hành tinh theo khung) | sửa ×3 trong một buổi tối; về nháp | Một yêu cầu (đổi góc nhìn không được đổi bằng chứng của ngày), ba đường vào: chỗ chọn tình huống, bộ chặn lặp, lượt tính riêng cho mỗi góc nhìn. Mỗi vòng vá một đường. Còn một đường đã biết chưa đóng (hai góc nhìn mở cùng lúc) |
| #449 (ô chọn cảm xúc) | sửa lần 3 hôm nay, rồi đồng ý | Chọn lại cảm xúc lúc mất mạng rồi tải lại trang thì mất lựa chọn. Cùng loại với #640 hôm qua: thứ tự giữa lựa chọn vừa bấm, hàng chờ gửi và bản đã lưu |
| #477 (staging tự gia hạn chứng chỉ) | sửa lần 3 hôm nay, rồi đồng ý | Ghi dấu "xong" trước khi ghi đủ file; lượt chạy lại sau lỗi giữa chừng tưởng đã xong |

#411 và #726 lặp bài học #124, #542, #603, #590, #640: vá tình huống được nêu, không rà cả loại lỗi. S35 (rà cả lớp trước khi push) hạn 19.11, chưa làm. #449 là ca thứ hai của S44.

## 5. Điều tốt, có bằng chứng

- Làn kế hoạch 7 tuần hết đứng yên sau hai ngày: 4 PR, 2 đã gộp. Bộ đo #717 cho ra con số thật (100/300 đường giữ được việc) và từ đó có việc sửa #740.
- Ba sự cố quy trình trong ngày thành kiểm tra bằng máy ngay trong ngày: hủy CI do nhãn (#722, L48), nhãn chờ sai (#727, L49), PR bị bỏ đói (#736, L50). Sổ lời hứa 42/50.
- 0 lượt tick lỗi, 0 phút hàng trống, ngày thứ hai.
- Lượt Codex xa trần: 41/120 (hôm qua 68/80).
- Số lần tự đồng bộ nhánh giảm từ 52 xuống 18.
- Hai PR mở lâu đã gộp: #354 (từ 08.11) và #449 (từ 12.11).
- Autopilot tự thấy một lỗi của chính nó (sửa nhầm một comment cũ trên #133 bằng lệnh "sửa comment cuối"), khôi phục nguyên văn từ lịch sử sửa và ghi lại.

## 6. Điều chưa tốt

- 0 việc lên bản chạy thật, ngày thứ ba. Chỉ 2 việc người dùng thấy được vào integration.
- Từ 19:10 không gộp thêm PR nào; 6 PR chờ kiểm qua đêm, trong đó có 2 PR kế hoạch.
- Bản sửa chống bỏ đói (#736) đổi cách chạy của hàng giữa ba ngày thử và tạo ra điểm nghẽn mới ngay trong buổi chiều.
- Làn quy trình vẫn 5 đang làm, 4 chờ review; trần là 1 và 1. Ngày thứ ba.
- Nợ sửa sau tăng tiếp: 127 lên 136; cả ngày chỉ đóng 1.
- Việc trong hàng đợi có hạn 18.11 không thấy PR nào: S30 (trễ lần ba), S32 (trễ lần hai), S36, S37, S41, S43, S27+. Lý do autopilot ghi: làn quy trình quá trần nên không mở PR. Kết quả là việc chặn đúng nguyên nhân (S30, S32) không bao giờ tới lượt.
- Bản chụp vẫn báo L13 quá hạn và L11, L13 chưa có bằng chứng.
- 37 issue báo động cũ (03.11–14.11) vẫn mở.

## 7. Học từ GitHub và nguồn gốc (kiểm 18.11.2026)

| Vấn đề | Cách làm học được | Nguồn | Mình áp dụng thế nào |
|---|---|---|---|
| PR đầu hàng trượt kiểm mà vẫn giữ đầu hàng | Trong merge queue của GitHub, PR trượt kiểm hoặc quá giờ chờ CI thì bị đưa ra khỏi hàng; các PR sau được dựng lại không có nó và đi tiếp. Có sẵn mức "thời gian chờ CI tối đa" và "số lượt kiểm chạy cùng lúc" | [GitHub Docs — Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | Không bật được (repo tài khoản cá nhân, đã kiểm 16.11; trang hôm nay không ghi điều kiện gói). Mượn ý cho S47: PR bị yêu cầu sửa thì xuống cuối hàng của làn nó, không quay lại đầu; giữ chỗ có hạn; đầu hàng chọn theo thứ tự R7 |
| #411: review đòi sửa mãi các lỗi nhỏ | Người review nên duyệt khi thay đổi chắc chắn làm code tốt hơn hiện tại, dù chưa hoàn hảo; điểm không bắt buộc thì ghi rõ là tùy chọn | [Google eng-practices — The Standard of Code Review](https://google.github.io/eng-practices/review/reviewer/standard.html) | Kho câu hiện không chặn link nào; #411 ở vòng 4 đã tốt hơn hẳn. Luật sẵn có: lỗi P2 thì gộp và mở issue sửa sau. S48: xem vì sao P2 ở #411 vẫn chặn gộp |
| #411: tự liệt kê đuôi tên miền | Không có cách tính ra đuôi tên miền hợp lệ; chỉ có danh sách, và danh sách đổi liên tục. Trang này cũng dặn không dùng danh sách để kiểm tên miền | [Public Suffix List — Learn more](https://publicsuffix.org/learn/) | S48: bỏ liệt kê đuôi. Câu cho người dùng không cần chứa "chữ.chữ" liền nhau; chặn mọi mẫu đó, trừ một danh sách ngắn các trường hợp được phép có test |
| #726, #449: cùng loại lỗi, nhiều đường vào | Như retro 15.11 và 17.11 (CodeQL variant analysis; TanStack Query — Optimistic Updates) | đã kiểm các ngày trước, hôm nay không kiểm lại | S35 + S44, thêm 3 ca |

## 8. Chống AI bị "rotten" — cập nhật 18.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6 và các bản 08.11–17.11. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Luật "quá trần thì không mở PR quy trình" khóa luôn việc sửa nguyên nhân | S30 và S32 trễ hạn ba và hai lần; mỗi lượt autopilot ghi cùng một câu "làn quy trình quá trần, không mở PR" |
| Bảng luật và máy lệch nhau | R8 ghi trần 80, bản chụp ghi 41/120 (mức thử owner cho, chỉ nằm trong file trạng thái) |
| Lệnh tiện tay sửa nhầm dữ liệu cũ | Lệnh "sửa comment cuối" sửa nhầm một comment ngày 14.11 trên #133; đã khôi phục |
| Prompt hẹn giờ còn đoạn hết hiệu lực | Prompt retro vẫn mang phần riêng cho ngày 02.11 (ngày thứ 7 ghi nhận). Hai điểm kia của hôm qua (thư mục làm việc, dòng chữ ký) đã được sửa trong prompt |

**Điều học thêm:** một luật giới hạn việc đang làm cần lối ưu tiên cho việc gỡ đúng nguyên nhân gây quá tải, nếu không nó tự giữ mình ở trạng thái quá tải.

## 9. Cần owner

Không có mục mới. Bản chụp còn 1 PR chờ owner (#127, có từ trước). PR lịch phát hành thứ Sáu (#747) ghi lại quyết định owner đã cho hôm nay, đang chờ kiểm, không cần owner làm thêm.

## 10. Giải pháp, xếp theo tác động

Làn quy trình đang 5 việc làm và 4 chờ review, trần là 1 và 1. Vì vậy hôm nay **không mở PR quy trình mới** ngoài PR retro này; mọi việc AUTO cần đổi code vào hàng đợi autopilot. Đang là ba ngày "cách của Codex", việc đổi cách vòng chạy đưa Codex góp ý trước.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S47 | Hàng không đứng vì một PR: PR bị yêu cầu sửa xuống cuối hàng của làn nó; đầu hàng chọn theo R7 (sự cố, kế hoạch 7 tuần, Daily, quy trình); giữ chỗ hết hạn thì nhường | GitHub merge queue | cả 5 "không"; làm đúng R7, không đổi luật | AUTO | Mới, ưu tiên 1, hạn 19.11. Là sửa hỏng hóc của #736, làm trong #738 nếu cùng phạm vi. Codex góp ý trước |
| S48 | #411: bỏ liệt kê đuôi tên miền, chặn mọi mẫu "chữ.chữ" trừ danh sách được phép; tìm vì sao lỗi chỉ P2 vẫn chặn gộp ở PR này | Google eng-practices; Public Suffix List | cả 5 "không" | AUTO | Mới, hạn 19.11, làm ở lượt sửa #411 kế tiếp |
| S32 | Lô câu tự chạy cổng nội dung trước khi mở PR; câu trượt để "chờ". Viết lại câu bị duyệt nhầm hai lần | retro 14.11 | cả 5 "không" | AUTO | **Trễ hạn lần hai**, hạn mới 19.11, làm trước lô 08:00 |
| S30 + S49 | Lệnh mở PR từ chối khi làn đủ việc (S30). Thêm S49: việc gỡ nguyên nhân quá tải của chính làn đó được đi trước, một việc mỗi lần, thay chỗ một PR quy trình đang mở | merge queue (ý tưởng) | cả 5 "không" | AUTO | S30 **trễ hạn lần ba**. Hạn mới 19.11. Codex góp ý S49 trước |
| S35 + S44 | Lỗi cùng loại bị nêu lần 2 thì dừng vá, viết bảng "cả lớp lỗi" kèm test từng dòng | retro 15.11, 17.11 | cả 5 "không" | AUTO | Hạn 19.11. Thêm 3 ca: #726, #411, #449 |
| S50 | Chặn bằng máy lệnh "sửa comment cuối" trên GitHub; sửa comment phải theo mã comment | R17 | cả 5 "không" | AUTO | Mới, hạn 20.11 |
| S46+ | Bảng luật R8 ghi thêm mức thử 120 của 18–19.11 theo đúng lời owner trong file trạng thái; sửa 3 dòng trạng thái cũ (R2, R7, R10) | retro 17.11 | cả 5 "không"; không đổi luật nào | AUTO | Hạn 19.11 |
| S41 | Chuyển các việc S còn mở vào sổ lời hứa để trễ hạn có máy báo | R17 | cả 5 "không" | AUTO | **Trễ hạn 18.11**, hạn mới 19.11. Hôm nay 7 việc trễ mà không máy nào báo |
| S36, S37, S43, S27+ | Đo nợ sửa sau; lỗi đã biết không tô đỏ cả lượt; đóng 37 issue báo động cũ; dòng bắt buộc điền sẵn | retro 15.11, 16.11 | cả 5 "không" | AUTO | **Trễ hạn 18.11**, hạn mới 20.11. Nợ hôm nay: 136 mở |
| S38, S45, S33, S34, S42 | Không gọi Codex lại khi tác giả không đổi gì; đo đồng bộ và CI mỗi PR; đếm lượt Codex theo mục đích; "Cần bạn xem" một lần mỗi PR; chạy thử lệnh rà chỉ dẫn | retro 14.11–17.11 | cả 5 "không" | AUTO | Hàng đợi, hạn 19.11 |
| S29 | Kiểm xung đột thật thay luật "cùng file" | git-merge-tree | cả 5 "không" | AUTO | Sau 20.11 |

## 11. Bước bị chặn

Không có tới lúc viết file này.
