# Nhìn lại vòng tự động Claude ⇄ Codex: 19.11.2026

Tác giả: Claude (lượt retro tự động 19.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Báo số việc thật, không chia cho chỉ tiêu nào. Mọi ngày trước đều đã có file retro (bản 18.11 là #748, còn mở, chờ lượt kiểm từ đêm 18.11).

## 1. Số chính thức (bản chụp, chép nguyên)

- Đã gộp vào integration hôm nay: 8 PR (số PR, không phải số việc).
- Việc đạt tiêu chí: 0/1 việc đã chọn đạt đủ tiêu chí; 4 PR chưa gắn việc (#740, #742, #411, #729), không tính.
- Việc kế hoạch 7 tuần: đã chọn 3 (tối thiểu 2 khi có việc sẵn sàng), đạt 0.
- PR đang mở: 15 (chờ owner: #127).
- Sự cố đang mở: #511 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-14 (từ 14/11 18:29); #470 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-13 (từ 13/11 17:22); #408 [ops-alert] staging-ready failed 2026-11-10 15:29 UTC (từ 10/11 22:29); #370 [ops-alert] collab loop 2026-11-09 (từ 09/11 17:08); #368 [ops-alert] collab loop 2026-11-09 (từ 09/11 14:06); #352 [ops-alert] ssh failed 2026-11-08 15:29 UTC (từ 08/11 22:40); #350 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 21:53); #334 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 20:51); #322 [ops-alert] collab loop 2026-11-08 (từ 08/11 17:09); #321 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 16:18); #318 [ops-alert] collab loop 2026-11-08 (từ 08/11 13:25); #317 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 13:25); #313 [ops-alert] collab loop 2026-11-08 (từ 08/11 10:51); #312 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-08 (từ 08/11 10:21); #311 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-08 (từ 08/11 05:07); #310 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-07 (từ 08/11 00:14); #309 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 23:24); #308 [ops-alert] collab loop 2026-11-07 (từ 07/11 22:53); #305 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 19:21); #304 [ops-alert] collab loop 2026-11-07 (từ 07/11 18:51); #303 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 17:20); #289 [ops-alert] collab loop 2026-11-07 (từ 07/11 13:21); #287 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-07 (từ 07/11 11:20); #285 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 10:29); #277 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-06 (từ 07/11 06:03); #276 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-07 (từ 07/11 06:03); #266 [ops-alert] collab loop 2026-11-06 (từ 06/11 13:54); #261 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-05 (từ 06/11 11:32); #260 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-06 (từ 06/11 11:32); #259 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-06 (từ 06/11 11:32); #244 [ops-alert] collab loop 2026-11-05 (từ 05/11 22:56); #231 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #230 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #205 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 04:46); #204 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 23:44); #196 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 20:33); #193 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 14:42).
- Lượt Codex hôm nay: 34/120; lỗi liên tiếp: 0.
- Lời hứa sửa quy trình: 45/52 đã chạy thật (đã merge, Codex duyệt), 4 đang làm, 1 chờ owner, 2 owner quyết không làm, rủi ro vẫn còn (L17, L24), **1 quá hạn** (L13), ghi xong nhưng chưa có bằng chứng merge + Codex duyệt: L11, L13.

Nguồn: bản chụp 2026-11-19 khung retro, lấy lúc 23:36, integration 059d3c3 · snapshot 88bdc7cde72b

Các số ở những mục dưới lấy từ: `logs/tick-2026-11-19.log`, `state/2026-11-19.json`, `collab-turn --report` và `collab-metrics` (23:40), `gh pr list` (PR gộp và PR mở trong ngày), 19 comment `Review verdict` của Codex trên 11 PR trong ngày, `queue.md` của autopilot, comment trong ngày trên #133, `git log origin/main`.

Trần Codex 120 là mức thử hai ngày 18–19.11 owner cho (ghi trong `state`, mục Z1); bảng luật R8 vẫn ghi 80. Từ 20.11 mức thử hết hạn.

## 2. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| Việc người dùng thấy được (vào integration) | **1, mới một phần** | Việc nhẹ viết riêng cho từng vấn đề Daily (#749): code đã gộp, 30 câu mới còn chờ duyệt nên người dùng chưa thấy. Lô câu 18.11 (#685) gộp, thêm 6 câu đã duyệt |
| Việc đã lên bản chạy thật | **0** | `main` không đổi từ 15.11 11:28, ngày thứ tư. 868 commit ở integration chưa lên `main` |
| Câu đã duyệt | **258/1636** | Hôm qua 252/1606. Lô câu hôm nay (#757) chưa gộp |
| Bộ Daily phục vụ được | **9/180** | Như hôm qua |
| Việc kế hoạch 7 tuần | bản chụp ghi chọn 3, đạt **0** | Đã gộp 4 PR của làn này: kiểm giữ việc ở màn 360 và 390 px (#742), máy kiểm bắt nút bị che (#751), việc nhẹ theo vấn đề (#749), máy kiểm không lộ dữ liệu (#753). Việc chính "hồ sơ chỉ ngày sinh và giờ khoảng cũng giữ được việc" (#740) còn 1 lỗi chặn và CI đỏ lúc 21:21. Home hiện việc đang giữ (#756) mở 14:07, chưa tới lượt kiểm |
| PR còn lại | 3 trong 8 | 1 PR cho vòng tự động (#738), 1 PR kiểm thử màn Home (#729), 1 PR tài liệu (#682) |
| Lượt tick báo lỗi | **0** | Ngày thứ ba |
| Hàng chờ trống | 0 phút | Như hôm qua |
| Từ mở PR tới gộp (trung vị 7 ngày) | 3,0 giờ | Hôm qua 3,6 giờ. 148 PR |
| Việc đang làm / trần | kế hoạch 1/1 và 1/1; Daily 1/1 và 1/1; quy trình 4/1 và 4/1 | `collab-metrics`. Hai làn đầu về đúng trần; làn quy trình quá trần ngày thứ tư |
| Số lần tự đồng bộ nhánh | 36 | Hôm qua 18 |
| Issue sửa sau (fix-forward) đang mở | **144** | Hôm qua 136. Hôm nay mở 7, đóng 0 |

Codex: 19 kết luận review trên 11 PR, 9 đồng ý, 10 yêu cầu sửa. Trong 10 lần yêu cầu sửa: 4 lần có lỗi chặn mức P1 (#740, #734, #757 hai lần), 6 lần chỉ có P2 nhưng vẫn chặn (#411 ba lần, #753 hai lần, #685 một lần). Không có P0. 34 lượt Codex gồm 19 lượt review, 1 lô câu, soát đêm và các lượt chạy tay; nguồn hôm nay không tách được phần còn lại theo mục đích (S33 chưa làm).

Lượt soát đêm (tạm tính 23:06) ghi 4 câu báo cáo sai nguồn trong 27 báo cáo. Bản chốt có sau nửa đêm.

## 3. Mất thời gian ở đâu

| Chuyện | Bao lâu | Vì sao | Đã sửa chưa |
|---|---|---|---|
| PR tài liệu và PR quy trình nhỏ chờ lượt kiểm hơn một ngày | #743 từ 16:46 ngày 18.11; #747 từ 22:14 ngày 18.11; #748 từ 23:41 ngày 18.11; #761 từ 20:21 hôm nay. CI của cả bốn đã xanh | Hàng kiểm xếp theo nhóm cũ: quy trình, nội dung, riêng tư, tính năng (`areaOrder` trong `scripts/collab-trust.mjs`). PR tên `docs(...)` và `fix(collab)` bị xếp vào nhóm "tính năng", nhóm cuối. Nhóm nội dung có #411 và #757 quay lại liên tục nên nhóm cuối không tới lượt | Chưa. Autopilot báo kẹt 2 lần (08:53, 09:54). Xem S47 |
| Việc kế hoạch 7 tuần đứng sau PR nội dung | #756 mở 14:07, tới 23:36 chưa được kiểm. Trong lúc đó #411 giữ đầu hàng 5 lần, #757 giữ 3 lần | Cùng nguyên nhân: code chưa xếp theo thứ tự R7 (sự cố, kế hoạch 7 tuần, Daily, quy trình). Comment plan sáng nay vẫn in thứ tự cũ "quy trình → content → privacy → tính năng mới" | Chưa. Bảng luật ghi R7 chờ #604, nhưng #604 đã gộp từ 16.11 và chỉ làm phần đếm việc theo làn, không đổi thứ tự hàng |
| #411 giữ đầu hàng rồi lại bị yêu cầu sửa | Khoảng 5 giờ giữ đầu hàng trong ngày (5 lượt: 08:37, 13:17, 15:11, 16:54, 18:30) | 3 lần yêu cầu sửa trong ngày, tổng 10 lần. Mỗi lần Codex đưa một kiểu chuỗi mới lọt qua bộ lọc. Xem mục 4 | Một phần: sáng nay đã bỏ cách liệt kê đuôi tên miền (S48). Chưa đủ |
| Lô câu hôm nay (#757) đỏ CI vì đúng câu cũ | CI đỏ 3 lần (15:21, 17:47, 18:19). Mở 15:00, chưa gộp | Lô duyệt lại câu `daily.action.defend-old-choice.09`, câu chứa cụm đã bị loại. **Lần thứ tư** cùng lỗi (#491, #635, #685, #757), lần thứ ba đúng câu đó | Chưa. S32 **trễ hạn lần ba** |
| Codex review lại khi tác giả chưa sửa gì | 1 lượt Codex (#757, 23:08) | Kết luận lần 2 ghi rõ phần thay đổi so với lần 1 là rỗng, lỗi chặn cũ còn nguyên | Chưa. S38 trễ hạn |
| Một test chập chờn làm đỏ CI của PR không liên quan | #411 đỏ lúc 09:09 vì test màn giữ việc, không phải code của nó; đứng hơn 2 giờ | Test chờ trang tải lại trước khi yêu cầu xong | Đã sửa 12:52 (#751) |
| Giữ chỗ hết hạn thì không xin lại được | #685 bị từ chối 3 lần (10:26–10:47) | PR đã dùng hết lượt giữ ở bản đó, dù integration đã đổi | Đã sửa 21:55 (#738) |

Khoảng không gộp được PR nào: 14:47 tới 19:02 và 19:02 tới 21:55.

## 4. PR cần từ 3 vòng review

| PR | Vòng | Nguyên nhân gốc |
|---|---|---|
| #411 (chặn link, số liên lạc, chỗ trống chưa điền trong kho câu) | tổng 10 lần yêu cầu sửa, hôm nay 3; chưa gộp | Bộ lọc cố nhận ra **mọi dạng xấu**: mọi tên miền hợp lệ theo chuẩn quốc tế, mọi dạng chỗ trống kiểu `%s`. Hôm nay Codex tìm thêm tên miền có dấu ghép, có ký hiệu, và `%.s`. Kiểu liệt kê cái xấu thì không hết. Cả 3 lần chỉ có lỗi P2; loại `user_copy` mức P2 chặn gộp theo luật sẵn có (`blockingP2` trong `scripts/collab-trust.mjs`). Trong khi đó kho câu hiện chưa có bộ lọc nào, và cả 1636 câu thật đều qua |
| #753 (máy kiểm không lộ dữ liệu) | sửa 2 lần rồi đồng ý; đã gộp | Che giờ trong dòng nhật ký để khỏi báo nhầm, nhưng che luôn cả giờ sinh. Lần 1 vá cho đường link và dữ liệu, lần 2 mới vá cho giờ đứng đầu dòng. Cùng một loại lỗi, vá hai lần |

#757 mới 2 vòng nhưng lỗi P1 của nó (7 câu "việc nên làm" không khớp với cảnh đi kèm) cùng loại với lỗi của lô hôm qua (#685): lô duyệt từng câu riêng, chưa kiểm câu ghép với cảnh nào.

#411 và #753 lặp bài học của #726, #449 hôm qua: vá ca được nêu, không rà cả loại lỗi. S35 (rà cả lớp trước khi push) trễ hạn.

## 5. Điều tốt, có bằng chứng

- Làn kế hoạch 7 tuần gộp 4 PR, trong đó có máy kiểm không lộ dữ liệu (#753): bảo vệ dữ liệu người dùng bằng kiểm tra tự động trên nhật ký, đường mạng, báo lỗi và đường link.
- Làn kế hoạch và làn Daily về đúng trần 1 đang làm và 1 chờ review.
- Autopilot lượt 21:48 tự chọn việc theo R7: sửa #753 (kế hoạch 7 tuần) trước #411 và #757.
- 0 lượt tick lỗi, 0 phút hàng trống, ngày thứ ba.
- Lượt Codex xa trần: 34/120.
- Hai lỗi của vòng thành bản sửa ngay trong ngày: test chập chờn (#751), giữ chỗ hết hạn (#738). Sổ lời hứa 45/52 (hôm qua 42/50).
- Hai PR chờ lâu đã gộp: retro 17.11 (#682) và lô câu 18.11 (#685).

## 6. Điều chưa tốt

- 0 việc lên bản chạy thật, ngày thứ tư. Việc người dùng thấy được vào integration mới một phần.
- Bản chụp ghi 0/3 việc kế hoạch đạt tiêu chí.
- Gộp 8 PR, hôm qua 14.
- Thứ tự hàng trong code vẫn là thứ tự cũ, khác R7. Đây là ngày thứ hai việc kế hoạch chờ sau PR nội dung.
- Lô câu trượt cùng một câu lần thứ tư.
- Làn quy trình 4 đang làm, 4 chờ review, ngày thứ tư. Vì vậy mọi lượt autopilot lại ghi "làn quy trình quá trần, không mở PR", và không việc S nào có hạn 19.11 được làm, trừ một phần S48.
- Nợ sửa sau tăng tiếp: 136 lên 144; cả ngày không đóng issue nào.
- Bản chụp vẫn báo L13 quá hạn và L11, L13 chưa có bằng chứng.
- 37 issue báo động cũ (03.11–14.11) vẫn mở.

## 7. Học từ GitHub và nguồn gốc (kiểm 19.11.2026)

| Vấn đề | Cách làm học được | Nguồn | Mình áp dụng thế nào |
|---|---|---|---|
| #411: 10 vòng vì cố liệt kê mọi dạng xấu | Định nghĩa cái được nhận và từ chối mọi thứ còn lại; đừng cố nhận ra mọi chuỗi xấu. Với văn bản tự do vẫn dùng được cách này: cho phép dải chữ rộng, giới hạn độ dài | [OWASP — Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) | S48 đổi hướng: câu cho người dùng chỉ được chứa chữ, số, khoảng trắng và một danh sách ngắn dấu câu; dấu chấm phải đứng trước khoảng trắng hoặc hết câu; không có ký tự `%`, `{`, `}`, `@`, `/`. Câu nào ra ngoài thì từ chối. Không còn phải hiểu tên miền hay `%s` |
| Một PR trượt kiểm quay lại đầu hàng; PR tài liệu chờ hơn một ngày | Trong merge queue của GitHub, PR trượt kiểm bị đưa ra khỏi hàng, các PR sau được dựng lại không có nó và đi tiếp | [GitHub Docs — Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | Không bật được (repo tài khoản cá nhân, đã kiểm 16.11; trang hôm nay vẫn không ghi điều kiện gói). Mượn ý cho S47, như hôm qua |
| PR chỉ có tài liệu vẫn xếp hàng chờ lượt kiểm đầy đủ | Bước kiểm bị bỏ qua bằng điều kiện thì báo "đạt" và không chặn gộp; đừng bắt buộc một bước kiểm có thể bị bỏ qua theo đường dẫn file | [GitHub Docs — Troubleshooting required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks) | CI của mình đã làm đúng: PR chỉ có tài liệu được xếp mức `docs` và xanh nhanh. Chỗ thiếu nằm ở vòng: PR mức `docs` vẫn chờ lượt giữ đầu hàng. S51: PR mức `docs` có CI xanh thì đi thẳng tới review, không cần giữ chỗ |
| #753, #757: cùng loại lỗi, vá từng ca | Như retro 15.11 và 17.11 | đã kiểm các ngày trước, hôm nay không kiểm lại | S35, thêm 2 ca |

## 8. Chống AI bị "rotten" — cập nhật 19.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6 và các bản 08.11–18.11. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Bảng luật ghi "chờ PR X" trong khi PR X đã gộp và không làm việc đó | R7 ghi code chạy thứ tự cũ "tới khi #604 merge". #604 gộp 16.11, thứ tự hàng vẫn cũ. Không ai kiểm lại dòng trạng thái sau khi PR gộp |
| Câu hỏi "vì sao" để mở qua hai ngày dù trả lời mất vài phút | "Vì sao lỗi P2 vẫn chặn #411" ghi là việc dở từ 18.11. Câu trả lời nằm ở một dòng code (`blockingP2`) |
| Việc trễ hạn chỉ được chép sang ngày mới | S32 trễ lần ba, S30 lần bốn, S41 lần hai. Retro ghi lại, autopilot ghi "quá trần", không có gì khác đi |
| Prompt hẹn giờ còn đoạn hết hiệu lực | Prompt retro vẫn mang phần riêng cho ngày 02.11 (ngày thứ 8 ghi nhận) |

**Điều học thêm:** khi một dòng trạng thái ghi "chờ PR số N", lúc PR đó gộp phải có máy kiểm lại dòng ấy. Nếu không, dòng ấy thành lời hứa không ai giữ.

## 9. Cần owner

Không có mục mới. Bản chụp còn 1 PR chờ owner (#127, có từ trước). Mức thử 120 lượt Codex hết hạn sau hôm nay; việc xem lại ngày 20.11 owner đã hẹn sẵn (mục Z1), không cần hỏi thêm.

## 10. Giải pháp, xếp theo tác động

Làn quy trình đang 4 việc làm và 4 chờ review, trần là 1 và 1. Vì vậy hôm nay **không mở PR quy trình mới** ngoài PR retro này; mọi việc AUTO cần đổi code vào hàng đợi autopilot. Hôm nay là ngày cuối của ba ngày "cách của Codex"; việc đổi cách vòng chạy đưa Codex góp ý trước và làm sau buổi xem lại 20.11.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S47 | Hàng kiểm và gộp xếp đúng thứ tự R7: sự cố, kế hoạch 7 tuần, Daily, quy trình. Chỗ sửa đã rõ: `areaOrder` và `sortByPriority` trong `scripts/collab-trust.mjs`. PR bị yêu cầu sửa xuống cuối hàng của làn nó. Sửa luôn dòng in thứ tự cũ trong comment plan và dòng trạng thái R7 | GitHub merge queue | cả 5 "không"; làm đúng R7, không đổi luật | AUTO | **Trễ hạn 19.11**, hạn mới 20.11, ưu tiên 1. Codex góp ý trước |
| S32 | Lô câu bỏ qua câu chứa cụm đã loại trước khi gửi Codex; câu trượt để "chờ". Viết lại câu `.09` | retro 14.11 | cả 5 "không"; câu viết lại đi qua cờ chờ duyệt | AUTO | **Trễ hạn lần ba**, hạn mới 20.11, làm trước lô câu kế tiếp |
| S48 | #411: bỏ cách nhận ra cái xấu, đổi sang chỉ nhận cái được phép (xem mục 7). Câu hỏi còn dở đã có trả lời: P2 loại `user_copy` chặn gộp theo `blockingP2` | OWASP | cả 5 "không" | AUTO | Làm ở lượt sửa #411 kế tiếp, hạn 20.11 |
| S52 | Lô câu chỉ duyệt câu "việc nên làm" khi đã kiểm nó khớp với mọi cảnh có thể ghép; chưa kiểm được thì để "chờ" | retro 15.11 (rà cả lớp) | cả 5 "không" | AUTO | Mới, hạn 21.11. Hai lô liền (#685, #757) bị chặn vì lỗi này |
| S51 | PR mức `docs` có CI xanh đi thẳng tới review, không giữ chỗ đầu hàng | GitHub Docs (required checks) | cả 5 "không" | AUTO | Mới, hạn 21.11. Codex góp ý trước |
| S30 + S49 | Lệnh mở PR từ chối khi làn đủ việc (S30). Việc gỡ nguyên nhân quá tải của chính làn quy trình được đi trước, một việc mỗi lần (S49) | merge queue (ý tưởng) | cả 5 "không"; S49 đổi câu chữ R7 nên đi bằng PR sửa bảng luật, Codex duyệt | AUTO | S30 **trễ hạn lần bốn**. Hạn mới 20.11, đưa vào buổi xem lại 20.11 |
| S53 | Máy kiểm bảng luật: dòng trạng thái ghi "chờ #N" mà #N đã gộp thì báo đỏ | R17 | cả 5 "không" | AUTO | Mới, hạn 21.11. Thêm vào `collab-rules.mjs` |
| S35 + S44 | Lỗi cùng loại bị nêu lần 2 thì dừng vá, viết bảng "cả lớp lỗi" kèm test từng dòng | retro 15.11, 17.11 | cả 5 "không" | AUTO | **Trễ hạn 19.11**, hạn mới 20.11. Thêm 2 ca: #753, #411 |
| S38 | Không gọi Codex lại khi phần thay đổi so với lần review trước là rỗng | retro 14.11–17.11 | cả 5 "không" | AUTO | **Trễ hạn 19.11**, hạn mới 20.11. Ca mới: #757 lần 2 |
| S41, S46+, S50 | Chuyển việc S còn mở vào sổ lời hứa; R8 ghi mức thử; chặn lệnh "sửa comment cuối" | R17 | cả 5 "không" | AUTO | S41 **trễ hạn lần hai**; S46+ trễ hạn 19.11. Hạn mới 20.11 |
| S36, S37, S43, S27+ | Đo nợ sửa sau; lỗi đã biết không tô đỏ cả lượt; đóng 37 issue báo động cũ; dòng bắt buộc điền sẵn | retro 15.11, 16.11 | cả 5 "không" | AUTO | Hạn 20.11. Nợ hôm nay: 144 mở |
| S45, S33, S34, S42 | Đo đồng bộ và CI mỗi PR; đếm lượt Codex theo mục đích; "Cần bạn xem" một lần mỗi PR; chạy thử lệnh rà chỉ dẫn | retro 14.11–17.11 | cả 5 "không" | AUTO | **Trễ hạn 19.11**, hạn mới 21.11. S34: hôm nay #734 nhận 3 comment "Cần bạn xem" |
| S29 | Kiểm xung đột thật thay luật "cùng file" | git-merge-tree | cả 5 "không" | AUTO | Sau 20.11 |

## 11. Bước bị chặn

Không có tới lúc viết file này.
