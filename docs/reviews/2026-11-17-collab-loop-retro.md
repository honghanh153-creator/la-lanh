# Nhìn lại vòng tự động Claude ⇄ Codex: 17.11.2026

Tác giả: Claude (lượt retro tự động 17.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Báo số việc thật, không chia cho chỉ tiêu nào. Mọi ngày trước đều đã có file retro (bản 16.11 là #633, gộp sáng nay). Hôm nay là ngày đầu của ba ngày thử "cách của Codex" (17–19.11).

## 1. Số chính thức (bản chụp, chép nguyên)

- Đã gộp vào integration hôm nay: 30 PR (số PR, không phải số việc).
- Việc đạt tiêu chí: chưa chọn việc nào có mã việc; 3 PR chưa gắn việc (#609, #614, #624), không tính.
- Việc kế hoạch 7 tuần: đã chọn 0 (tối thiểu 2 khi có việc sẵn sàng), đạt 0.
- PR đang mở: 11 (chờ owner: #127).
- Sự cố đang mở: #511 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-14 (từ 14/11 18:29); #470 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-13 (từ 13/11 17:22); #408 [ops-alert] staging-ready failed 2026-11-10 15:29 UTC (từ 10/11 22:29); #370 [ops-alert] collab loop 2026-11-09 (từ 09/11 17:08); #368 [ops-alert] collab loop 2026-11-09 (từ 09/11 14:06); #352 [ops-alert] ssh failed 2026-11-08 15:29 UTC (từ 08/11 22:40); #350 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 21:53); #334 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 20:51); #322 [ops-alert] collab loop 2026-11-08 (từ 08/11 17:09); #321 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 16:18); #318 [ops-alert] collab loop 2026-11-08 (từ 08/11 13:25); #317 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 13:25); #313 [ops-alert] collab loop 2026-11-08 (từ 08/11 10:51); #312 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-08 (từ 08/11 10:21); #311 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-08 (từ 08/11 05:07); #310 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-07 (từ 08/11 00:14); #309 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 23:24); #308 [ops-alert] collab loop 2026-11-07 (từ 07/11 22:53); #305 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 19:21); #304 [ops-alert] collab loop 2026-11-07 (từ 07/11 18:51); #303 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 17:20); #289 [ops-alert] collab loop 2026-11-07 (từ 07/11 13:21); #287 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-07 (từ 07/11 11:20); #285 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 10:29); #277 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-06 (từ 07/11 06:03); #276 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-07 (từ 07/11 06:03); #266 [ops-alert] collab loop 2026-11-06 (từ 06/11 13:54); #261 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-05 (từ 06/11 11:32); #260 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-06 (từ 06/11 11:32); #259 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-06 (từ 06/11 11:32); #244 [ops-alert] collab loop 2026-11-05 (từ 05/11 22:56); #231 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #230 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #205 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 04:46); #204 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 23:44); #196 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 20:33); #193 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 14:42).
- Lượt Codex hôm nay: 68/80; lỗi liên tiếp: 0.
- Lời hứa sửa quy trình: 37/47 đã chạy thật (đã merge, Codex duyệt), 7 đang làm, 1 chờ owner, 2 owner quyết không làm, rủi ro vẫn còn (L17, L24), **1 quá hạn** (L13), ghi xong nhưng chưa có bằng chứng merge + Codex duyệt: L11, L13.

Nguồn: bản chụp 2026-11-17 khung retro, lấy lúc 23:36, integration ac3ff94 · snapshot 11d51df1df5b

Các số ở những mục dưới lấy từ: `logs/tick-2026-11-17.log`, `state/2026-11-17.json`, `collab-turn --report` và `collab-metrics` (23:40), `gh pr list` (PR đổi trong ngày), 54 comment `Review verdict` của Codex trên 33 PR trong ngày, `queue.md` của autopilot, `git log origin/main`.

## 2. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| Việc người dùng thấy được (vào integration) | **4** | Ngày Đuối có việc nhẹ hơn, có nút về việc ban đầu (#634, #640, #670: một việc, ba PR). Giờ sinh khoảng vẫn có Daily (#660, #666). Kho câu của Lá cho từng vấn đề Daily, phần lưu; phần chọn câu còn tắt (#657). Lô câu Codex duyệt 16.11 (#635) |
| Việc đã lên bản chạy thật | **0** | `main` không đổi từ 15.11 11:28. 701 commit ở integration chưa lên `main` |
| Câu đã duyệt | **251/1605** | Hôm qua 165/1563. Codex duyệt 248, owner 3 |
| Bộ Daily phục vụ được | **9/180** | Hôm qua 0. Lần đầu có bộ đủ câu |
| Việc kế hoạch 7 tuần | **0** | Câu trả lời của owner cho điều kiện bắt đầu đã gộp 13:51 (#609), nhưng chưa việc tuần 1 nào được ghi là sẵn sàng |
| PR còn lại (quy trình, bài học, tài liệu) | 23 trong 30 | 17 PR cho vòng tự động, 1 PR cho bộ mô phỏng người dùng, 5 PR tài liệu |
| Lượt tick báo lỗi | **0** | Hôm qua 44 lượt đỏ |
| Hàng chờ trống | 10 phút | Hôm qua 144 phút |
| Từ mở PR tới gộp (trung vị 7 ngày) | 3,2 giờ | Hôm qua 2,6 giờ. 153 PR |
| Việc đang làm / trần | làn quy trình 2/1, chờ review 6/1; làn kế hoạch 0/1 và 0/1; làn Daily 0/1 và 0/1 | `collab-metrics` |
| Issue sửa sau (fix-forward) đang mở | **127** | Hôm qua 122. Hôm nay mở 20, đóng 10 (8 trong 20 issue mới đóng ngay trong ngày) |

Codex: 54 kết luận review trên 33 PR, 35 đồng ý, 19 yêu cầu sửa. Trong 19 lần yêu cầu sửa: 17 lần có lỗi chặn mức P1, 2 lần chỉ có lỗi P2 (#618 vòng 2, #635). Không có P0.

## 3. Mất thời gian ở đâu

| Chuyện | Bao lâu | Vì sao | Đã sửa chưa |
|---|---|---|---|
| Màn "ngày Đuối" (#640) cần 8 vòng review | Mở 09:59, gộp 17:56. Review từ 13:14 tới 17:56, 7 lần yêu cầu sửa, lần nào cũng có P1 | Xem mục 4 | Đã gộp. Bài học chưa thành kiểm tra bằng máy: S44 |
| Nhánh phải đồng bộ lại sau mỗi lần có PR khác gộp | 52 lần tự đồng bộ trong ngày. #635: 9 lần, #640: 5 lần, #666 và #652: 4 lần. Mỗi lần là một đầu nhánh mới và một lượt CI mới (72 kết quả author check trong ngày) | Ngày có 30 PR gộp; PR nào đang chờ cũng phải chứa integration mới nhất trước khi kiểm | Chưa. Mới đo được hôm nay: S45 |
| Lô câu 16.11 (#635) đỏ CI hai lần | Mở 08:10, gộp 15:43 | Lô duyệt cả những câu không qua cổng nội dung khi đưa ra dùng (1 cụm đã bị loại, rồi 5 test đỏ; trả 17 câu về "chờ"). Sau đó Codex yêu cầu trả thêm 2 câu giả định một cảnh cụ thể. Đây là đúng ca #491 hôm 16.11 | Chưa. S32 (lô tự kiểm trước khi mở PR) hạn 17.11, **trễ hạn** |
| Codex review lại khi tác giả không đổi gì | 3 lượt: #609 hai lần, #633 một lần. Codex ghi "phần thay đổi trống" | Đầu nhánh đổi do đồng bộ nên phải xin duyệt lại | Chưa. S38 hạn 19.11 |
| Làn kế hoạch 7 tuần đứng yên | Cả ngày, ngày thứ hai liền | Không có việc nào ghi là sẵn sàng; S40 mới làm được nửa đầu (#609 gộp) | Chưa. S40 phần còn lại chuyển 18.11 |
| 4 PR quy trình mở tối 16.11 chờ qua đêm (#614, #616, #618, #621) | Mở 22:20–22:35 ngày 16.11, gộp 10:29–12:27 ngày 17.11 | Làn quy trình vượt trần từ hôm qua; các PR nối nhau cùng file | Đã gộp hết. Cuối ngày làn vẫn 2 đang làm, 6 chờ review (trần 1 và 1). S30 **trễ hạn lần hai** |

## 4. PR cần từ 3 vòng review

| PR | Vòng | Nguyên nhân gốc |
|---|---|---|
| #640 (web: ngày Đuối hiện việc nhẹ hơn) | sửa ×7, đồng ý | Một loại lỗi, bảy đường vào: thứ tự giữa lựa chọn vừa bấm, bản lưu trên máy chủ, bản nhớ tạm, tab khác và phản hồi về trễ. Vòng 1–5 mỗi lần vá một tình huống. Vòng 6 phiên điều phối mới yêu cầu "sửa cả lớp lỗi bằng một luật thứ tự". Vòng 7 lộ ra luật đó dựa vào giờ do máy chủ ghi trước khi khóa, nên hai lần lưu có thể đảo thứ tự; test giả ghi giờ theo thứ tự lưu nên không thấy. Cuối cùng phần "hiện ngay khi mất mạng" bị tách ra thành việc sau |
| #657 (kho câu của Lá) | sửa, sửa, đồng ý | Chọn câu theo ngày lịch nên một vấn đề lặp lại cách ngày luôn ra cùng một câu. Vòng 2 vẫn lỗi cũ dưới dạng khác. Cách xong: tắt phần chọn câu, chỉ giữ phần lưu |
| #666 (giờ sinh khoảng, bằng chứng không đổi theo góc nhìn) | sửa, sửa, đồng ý | Vòng 1: đổi nội dung mà không đổi số phiên bản, bản cũ mở lại sẽ khác. Vòng 2: bản vá làm chuỗi phiên bản dài 75 ký tự, cột chỉ chứa 64 |
| #637 (câu trả lời owner gỡ nhãn chờ) | sửa, sửa, đồng ý | Tin bản ghi cũ thay vì đọc lại comment hiện tại. Vòng 2 cùng lỗi ở chỗ gọi thứ hai (comment đọc trước lượt Codex 30 phút) |
| #618 (lượt đêm rà trí nhớ) | sửa, sửa, đồng ý | Vòng 1: đường dẫn `..` có thể xóa chính thư mục nguồn. Vòng 2 chỉ còn P2 |
| #609 (câu trả lời owner cho kế hoạch) | đồng ý ×3 (tính cả 16.11) | Không có lỗi. Đầu nhánh đổi do đồng bộ |

#640, #657 và #637 lặp bài học #124 (02.11), #542 (15.11), #603 và #590 (16.11): sửa tình huống được nêu, không rà cả loại lỗi. Việc S35 (rà cả lớp trước khi push) hạn 19.11, chưa làm; ở #640 phải tới vòng 6 mới có người yêu cầu làm đúng việc đó.

## 5. Điều tốt, có bằng chứng

- Lần đầu có bộ Daily phục vụ được: 0 lên 9. Câu đã duyệt 165 lên 251.
- Ba việc sản phẩm mới vào integration trong một ngày, đều thuộc Daily (#627, #626).
- Không còn lượt tick đỏ (hôm qua 44). Hàng chờ trống 10 phút (hôm qua 144).
- Bảng luật chung đã ở bản code đã duyệt (#614) và hook nạp lại luật đã chạy (#616, #621): lượt retro này nhận bảng luật ngay lúc mở phiên, không phải đọc từ nhánh PR như hôm qua.
- Nhãn "chờ owner" cũ đã gỡ được bằng máy (#637, #675, #679): bản chụp còn 1 PR chờ owner (#127), hôm qua 5.
- 8 trong 20 issue sửa sau mở hôm nay được đóng ngay trong ngày, kèm PR (#662, #671, #663, #655…).
- Lượt Codex trong trần: 68/80.
- Quyết định owner 17.11 (thêm một làn Daily, thử 18–19.11) vào code trong ngày (#676).

## 6. Điều chưa tốt

- 0 việc lên bản chạy thật, ngày thứ hai. 0 việc kế hoạch 7 tuần, ngày thứ hai.
- 17 trong 30 PR vẫn là cho vòng tự động.
- Làn quy trình cuối ngày 2 đang làm, 6 chờ review; trần là 1 và 1.
- Nợ sửa sau tăng tiếp: 122 lên 127.
- Việc trong hàng đợi có hạn 17.11 không thấy PR nào: S30 (trễ lần hai), S32, S33, S34. Hậu quả của S32 thấy ngay hôm nay ở #635.
- Bản chụp báo 1 lời hứa quá hạn (L13) và 2 mục ghi xong nhưng chưa có bằng chứng (L11, L13).
- 37 issue báo động cũ (03.11–14.11) vẫn mở.

## 7. Học từ GitHub và nguồn gốc (kiểm 17.11.2026)

| Vấn đề | Cách làm học được | Nguồn | Mình áp dụng thế nào |
|---|---|---|---|
| #640: lựa chọn vừa bấm, bản lưu và bản nhớ tạm giẫm nhau | Trước khi hiện trước kết quả: hủy các lượt đọc đang bay để chúng không ghi đè; khi lỗi thì trả về bản cũ; xong (lỗi hay thành công) luôn đọc lại từ máy chủ. Nếu chỉ một chỗ hiện kết quả thì dùng luôn giá trị đang gửi, không sửa bản nhớ tạm | [TanStack Query — Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates) | S44: màn nào có "hiện trước khi lưu xong" thì trước khi viết code phải có bảng tình huống thứ tự (bấm, lưu chậm, lưu lỗi, đọc về trễ, tab khác, qua ngày) và dùng đúng mẫu của thư viện, không tự dựng |
| #640 vòng 7: thứ tự hai lần lưu dựa vào giờ máy chủ | Máy chủ cấp một mã phiên bản cho mỗi bản lưu; bên gửi kèm mã đã thấy, lệch thì máy chủ từ chối (412), bên gửi đọc lại rồi mới ghi | [MDN — If-Match](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Match) | Bản đã gộp dùng giờ tăng dần trong khóa. Ghi vào S44: thứ tự phải do máy chủ cấp trong khóa; test phải chạy với đúng cách máy chủ thật ghi, không dùng bản giả |
| Đồng bộ nhánh liên tục, CI chạy lại | Merge queue cho lợi ích của "nhánh phải mới nhất" mà tác giả không phải cập nhật nhánh | [GitHub Docs — Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | Không dùng được (retro 16.11 đã kiểm: không có cho repo tài khoản cá nhân; trang hôm nay không ghi điều kiện). Mượn ý: chỉ đồng bộ PR sắp tới lượt gộp. S45 đo trước, đổi sau 20.11 |
| Review lại khi phần của tác giả không đổi | GitHub chỉ bỏ lời duyệt cũ khi commit mới làm đổi phần thay đổi của PR. Có lựa chọn khác: chỉ cần lần đẩy gần nhất được người khác duyệt | [GitHub Docs — About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) | Khớp S38: so phần thay đổi của tác giả trước và sau đồng bộ; không đổi thì không gọi Codex. Không đổi cài đặt repo |

## 8. Chống AI bị "rotten" — cập nhật 17.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6 và các bản 08.11–16.11. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Bảng luật mới gộp một ngày đã có cột trạng thái cũ | R2 ghi "tới khi xong #611" (#611 đóng 13:52 hôm nay); R7 ghi "tới khi #604 merge" và R10 ghi "chờ #603" (cả hai gộp 16.11) |
| Prompt hẹn giờ trỏ tới thư mục làm việc đã cũ | Prompt retro bảo làm trong một worktree đang ở nhánh retro 11.11, sau integration 83 commit và có 4 file sửa dở của việc khác. Lượt này dùng một worktree sạch riêng, không đụng 4 file đó |
| Prompt ghi cứng thông tin đã đổi | Dòng chữ ký commit trong prompt retro ghi một tên model khác với model đang chạy lượt này |
| Đoạn hết hiệu lực còn trong prompt | Prompt retro vẫn mang phần riêng cho ngày 02.11 (ngày thứ 6 ghi nhận) |
| Phiên làm việc quên bước bắt buộc | Ghi chú autopilot 19:10: mấy lượt sửa #640 trước đó trong ngày không giữ chỗ PR trước khi sửa (R10) |

**Điều học thêm:** một file luật chung giải quyết chuyện luật nằm rải rác, nhưng cột "trạng thái" trong chính file đó là thông tin sống theo PR, cũ đi trong vài giờ. Thứ gì máy tự biết (PR đã gộp chưa) thì để máy điền, không ghi tay.

**Biện pháp đã vào code hôm nay:** bảng luật có máy kiểm (#614, #656), hook nạp lại luật và chặn hỏi owner trong chat (#616), tick canh hook (#621), lượt đêm rà trí nhớ (#618, #644).

## 9. Cần owner

Không có mục mới. Tệp việc chờ owner trên máy owner đang ghi "không có mục nào". Bản chụp còn 1 PR chờ owner (#127, đã có từ trước).

Ba điểm trong prompt hẹn giờ ở mục 8 (thư mục làm việc, dòng chữ ký, đoạn 02.11) là sửa prompt trên máy owner; lượt retro không được giao sửa prompt của chính nó, nên đã gửi phiên điều phối.

## 10. Giải pháp, xếp theo tác động

Làn quy trình đang 2 việc làm và 6 chờ review, trần là 1 và 1. Vì vậy hôm nay **không mở PR quy trình mới** ngoài PR retro này; mọi việc AUTO cần đổi code vào hàng đợi autopilot. Đang là ba ngày "cách của Codex", việc đổi cách vòng chạy đưa Codex góp ý trước.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S40 | Ghi việc tuần 1 của kế hoạch 7 tuần thành việc sẵn sàng (phần #609 đã xong) | R7 | cả 5 "không" | AUTO | Hàng đợi, ưu tiên 1, hạn 18.11 |
| S35 + S44 | Lỗi cùng loại bị nêu lần 2 thì dừng vá, viết bảng "cả lớp lỗi" kèm test từng dòng rồi mới push. Riêng màn có "hiện trước khi lưu xong": bảng tình huống thứ tự có trước khi viết code; thứ tự do máy chủ cấp trong khóa; test theo cách máy chủ thật ghi | TanStack Query; MDN If-Match; CodeQL variant analysis (retro 15.11) | cả 5 "không" | AUTO | Hàng đợi, hạn 19.11. Thêm 3 ca hôm nay: #640, #657, #637 |
| S32 | Lô câu tự chạy cổng nội dung và test đọc trước khi mở PR; câu trượt thì để "chờ" | retro 14.11 | cả 5 "không" | AUTO | **Trễ hạn 17.11**, hạn mới 18.11, làm trước lô 08:00 nếu kịp. Ca hôm nay: #635 |
| S30 | Lệnh mở PR từ chối khi làn đã đủ việc; việc nối nhau mở lần lượt | merge queue (ý tưởng) | cả 5 "không" | AUTO | **Trễ hạn lần hai**, hạn mới 18.11 |
| S38 | Nhánh chỉ đổi do đồng bộ, phần của tác giả không đổi: không gọi Codex lại | GitHub protected branches | cả 5 "không" | AUTO | Hàng đợi, hạn 19.11. Hôm nay tốn 3 lượt |
| S45 | Đo số lần đồng bộ và số lượt CI cho mỗi PR trong `collab-metrics`; đề xuất "chỉ đồng bộ PR sắp gộp" đưa Codex góp ý | merge queue | cả 5 "không" | AUTO (phần đo) | Mới. Đo hạn 19.11; đổi cách chạy sau 20.11 |
| S46 | Cột trạng thái của bảng luật: máy báo khi PR được nhắc tới đã gộp hoặc issue đã đóng; sửa 3 dòng R2, R7, R10 | Claude Code Docs (retro 16.11) | cả 5 "không"; không đổi luật nào | AUTO | Mới, hạn 19.11 |
| S41 | Chuyển các việc S còn mở vào sổ lời hứa để trễ hạn có máy báo | R17 | cả 5 "không" | AUTO | Hàng đợi, hạn 18.11. Hôm nay lại có 4 việc trễ mà không máy nào báo |
| S36, S37, S43, S27+ | Đo nợ sửa sau; lỗi đã biết không tô đỏ cả lượt; đóng 37 issue báo động cũ; dòng bắt buộc điền sẵn | retro 15.11, 16.11 | cả 5 "không" | AUTO | Hàng đợi, hạn 18.11. Số nợ hôm nay: 127 mở |
| S33, S34 | Đếm lượt Codex theo mục đích; "Cần bạn xem" một lần mỗi PR | retro 14.11 | cả 5 "không" | AUTO | **Trễ hạn 17.11**, hạn mới 19.11 |
| S42 | Chạy thử `/doctor prompt-audit` trong phiên có người | Claude Code Docs | cả 5 "không" | AUTO | Hàng đợi, hạn 19.11 |
| S29 | Kiểm xung đột thật thay luật "cùng file" | git-merge-tree | cả 5 "không" | AUTO | Sau 20.11 |

## 11. Bước bị chặn

Không có tới lúc viết file này.
