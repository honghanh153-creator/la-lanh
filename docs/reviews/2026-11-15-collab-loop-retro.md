# Nhìn lại vòng tự động Claude ⇄ Codex: 15.11.2026

Tác giả: Claude (lượt retro tự động 15.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Báo theo Autopilot v2 (owner duyệt 12.11): số việc thật, không chia cho 20. Mọi ngày trước đều đã có file retro (#523 của 14.11 gộp sáng nay).

## 1. Số chính thức (bản chụp, chép nguyên)

- Đã gộp vào integration hôm nay: 39 PR (số PR, không phải số việc).
- Việc đạt tiêu chí: chưa chọn việc nào có mã việc; 4 PR chưa gắn việc (#523, #529, #491, #456), không tính.
- PR đang mở: 16 (chờ owner: #477, #449, #411, #354, #127).
- Sự cố đang mở: #511 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-14 (từ 14/11 18:29); #470 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-13 (từ 13/11 17:22); #408 [ops-alert] staging-ready failed 2026-11-10 15:29 UTC (từ 10/11 22:29); #370 [ops-alert] collab loop 2026-11-09 (từ 09/11 17:08); #368 [ops-alert] collab loop 2026-11-09 (từ 09/11 14:06); #352 [ops-alert] ssh failed 2026-11-08 15:29 UTC (từ 08/11 22:40); #350 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 21:53); #334 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 20:51); #322 [ops-alert] collab loop 2026-11-08 (từ 08/11 17:09); #321 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 16:18); #318 [ops-alert] collab loop 2026-11-08 (từ 08/11 13:25); #317 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 13:25); #313 [ops-alert] collab loop 2026-11-08 (từ 08/11 10:51); #312 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-08 (từ 08/11 10:21); #311 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-08 (từ 08/11 05:07); #310 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-07 (từ 08/11 00:14); #309 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 23:24); #308 [ops-alert] collab loop 2026-11-07 (từ 07/11 22:53); #305 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 19:21); #304 [ops-alert] collab loop 2026-11-07 (từ 07/11 18:51); #303 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 17:20); #289 [ops-alert] collab loop 2026-11-07 (từ 07/11 13:21); #287 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-07 (từ 07/11 11:20); #285 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 10:29); #277 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-06 (từ 07/11 06:03); #276 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-07 (từ 07/11 06:03); #266 [ops-alert] collab loop 2026-11-06 (từ 06/11 13:54); #261 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-05 (từ 06/11 11:32); #260 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-06 (từ 06/11 11:32); #259 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-06 (từ 06/11 11:32); #244 [ops-alert] collab loop 2026-11-05 (từ 05/11 22:56); #231 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #230 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #205 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 04:46); #204 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 23:44); #196 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 20:33); #193 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 14:42).
- Lượt Codex hôm nay: 81/80; lỗi liên tiếp: 0.
- Lời hứa sửa quy trình: 22/30 đã chạy thật (đã merge, Codex duyệt), 5 đang làm, 1 chờ owner, 2 owner quyết không làm, rủi ro vẫn còn (L17, L24), không có mục quá hạn, ghi xong nhưng chưa có bằng chứng merge + Codex duyệt: L13.

Nguồn: bản chụp 2026-11-15 khung retro, lấy lúc 23:36, integration b7d8e30 · snapshot 4ee95dcdc33b

Các số ở những mục dưới lấy từ: `logs/tick-2026-11-15.log`, `state/2026-11-15.json`, `collab-turn --report` và `collab-metrics` (23:50), `gh pr list --state merged`, 73 comment `Review verdict` của Codex trên 44 PR trong ngày, `queue.md` của autopilot, comment trên issue plan #133, `git log origin/main`.

## 2. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| Việc người dùng thấy được | **1** | Nút "Đọc bản mới" mở được cho mọi loại hồ sơ (#546) |
| Việc đã lên bản chạy thật | **1** | Cũng việc trên: bản vá vào `main` lúc 11:28 (#549), có biên nhận phát hành (#550) |
| Bộ Daily phục vụ được | **0/168** | Câu đã duyệt 0/1524 (`collab-metrics`). Lô duyệt câu #491 vẫn đỏ |
| PR gộp do lượt tick | 6 | #523, #529, #465, #550, #527, #552 |
| PR gộp ngoài lượt tick | 33 | Phiên làm việc của Claude trong tuần thử "cách của Claude". 20 PR gộp từ 00:16 tới 07:50, lúc tick nghỉ đêm |
| Lượt tick | 87 chạy, 0 lỗi | Ngoài 40 lượt nghỉ đêm và 6 lượt chờ plan |
| Hàng chờ trống | 118 phút | `collab-turn --report` |
| Từ mở PR tới gộp (trung vị) | 6,6 giờ | Soát đêm 23:06, 39 PR |
| Việc đang làm / trần | 8 / 1 | `collab-metrics`. Hôm qua 17 |
| Issue sửa sau (fix-forward) đang mở | **107** | Hôm nay mở 21, đóng 3 |

Phần lớn 39 PR là công cụ cho vòng tự động và cho thử nghiệm: sổ lời hứa, soát đêm, luật bất đồng, cổng chặn agent con ghi file, giữ 2 chỗ cho kế hoạch 7 tuần, bộ người giả.

## 3. Phát hiện của Codex theo mức

73 lượt review trên 44 PR: 40 APPROVE, 33 REQUEST_CHANGES. 26/44 PR được APPROVE ngay vòng đầu.

| Mức | Số | Ghi chú |
|---|---|---|
| P0 | 0 | — |
| P1 | 42 | Tất cả chặn merge. 12 cái ở #542, 7 ở #544, 6 ở #520, 5 ở #564 |
| P2 | 66 | 5 cái chặn merge, còn lại thành issue sửa sau |
| P3 | 0 | — |

Theo loại: đúng sai của code 61, tài liệu 19, bảo mật 12, test 11, câu chữ 3, quyền riêng tư 2.

## 4. Thời gian mất và nguyên nhân

| Mất | Bao lâu | Nguyên nhân | Bằng chứng |
|---|---|---|---|
| Lô duyệt câu #491 đứng yên | 10:04 → hết ngày | CI đỏ 5 test (câu vừa duyệt lặp cụm từ giữa câu nhận định và câu hành động). Autopilot biết cách sửa nhưng dừng vì bản clone làm việc còn 3 file sửa dở của #477 từ 13.11. Ngày thứ 3 | `queue.md` 10:50, 13:50, 22:50; báo kẹt #133 lúc 13:49 |
| #134, #388, #404 xung đột, không ai sửa | cả buổi tối | Cùng nguyên nhân clone bẩn | báo kẹt #133 lúc 21:49 |
| #542 review 9 vòng | 10:47 → 14:58 | Xem mục 5 | 9 comment verdict |
| #544 review 6 vòng | 15:20 → 18:17 | Xem mục 5 | 6 comment verdict |
| 5 PR trượt preflight vì body thiếu dòng | mỗi PR chờ tới lượt autopilot sau | #529, #527, #550, #411, #568 thiếu cổng G hoặc dòng "Người dùng thấy gì". Ngày thứ 4 (S27+ chưa làm, hạn 16.11) | log tick 08:05, 10:14, 11:43, 19:21, 22:04 |
| Hết lượt Codex cuối ngày | từ khoảng 23:06 | Dùng 81/80 dù owner đã cho thêm 20 lượt lúc 15:53. #568 qua check lúc 23:28 nhưng không còn lượt review; soát đêm không đo được M1 và M3 | `state`, comment soát đêm 23:06 |
| Báo động nhầm | #548 mở 11:07, đóng 17:00 | Kiểm toán sau merge đòi biên nhận kiểu mới cho PR gộp trước khi luật mới có hiệu lực (#456, 10:09). Soát đêm tạm tính cũng ghi 23/39 PR "thiếu biên nhận"; cả 23 PR đều gộp trước hoặc đúng lúc #456. Chưa có bản chốt | comment đóng #548; comment soát đêm 23:06 |
| Owner bị báo lặp | #354 năm lần, #506 hai lần | Khóa chống trùng vẫn gắn theo commit đầu nhánh (S34 chưa làm, hạn 17.11) | comment #133 lúc 07:24, 10:14, 15:06, 18:30, 20:34 |
| Báo cáo 07:00 chạy trễ | tới 17:49 | Chưa rõ nguyên nhân | comment #133 lúc 17:53 |

## 5. PR từ 3 vòng review trở lên

| PR | Vòng | Nguyên nhân gốc |
|---|---|---|
| #542 cổng chặn agent con ghi file | 9 | Cổng đọc câu lệnh shell rồi chặn những dạng nguy hiểm đã biết. Mỗi vòng Codex tìm ra một dạng lách mới (tùy chọn ghi file, đường dẫn tương đối, `git -C`, `find`). Mỗi bản sửa chỉ đóng đúng dạng vừa nêu. Codex nhắc "ghi lại lỗ hổng lặp lại" ba lần. Kết thúc bằng một giới hạn được chấp nhận (#553) |
| #544 giữ 2 chỗ cho kế hoạch 7 tuần | 6 | Việc bị bỏ khỏi danh sách phải được nhớ ở mọi đường xếp hàng. Mỗi vòng sửa một đường, vòng sau Codex chỉ ra đường kế tiếp |
| #520 luật bất đồng | 4 | Máy trạng thái có nhiều lối vào: sập giữa chừng, owner giữ lại, hai lượt chạy cùng lúc. Vòng đầu chỉ test đường thuận |
| #494 kiểm thư mục trước khi giao việc | 3 | Ghi lời hứa L06 là xong khi chưa có nơi gọi thật; rồi tự đổi hạn của L06 |
| #564 người giả hằng đêm | 3 | Bốn P1 vòng đầu về thứ tự bước và đếm lượt Codex khi chạy lỗi |

Đây là cùng bài học với #124 ngày 02.11 (7 vòng vì mỗi bản sửa chỉ đóng đúng lỗi được nêu). Bài học đó mới nằm trên giấy, chưa thành bước kiểm.

## 6. Tốt và chưa tốt

**Tốt**
- Một lỗi người dùng gặp (#545) được sửa, review, đưa lên bản chạy thật và ghi biên nhận trong một buổi sáng.
- 0 P0, 0 lượt Codex lỗi, 0 tick lỗi.
- Sổ lời hứa: 22/30 mục đã chạy thật (hôm qua 6/24), không mục nào quá hạn.
- Số việc đang làm giảm từ 17 xuống 8.
- Báo động nhầm #548 được đóng kèm bằng chứng trên máy, không bỏ qua.

**Chưa tốt**
- Chưa câu Daily nào tới người dùng. Sự cố lô duyệt câu từ 13.11 **còn mở**: chưa có lô nào ra câu được duyệt.
- 38/39 PR không đổi gì cho người dùng.
- Nợ sửa sau tăng nhanh hơn trả: mở 21, đóng 3, còn 107.
- Một bản clone bẩn chặn 4 PR tới ngày thứ 3, và owner bị hỏi 3 lần cho một việc không thuộc 4 loại việc owner quyết.
- Hai PR ngốn 15 lượt Codex vì sửa từng lỗi một.

## 7. Học từ GitHub và các nguồn chính

Ngày kiểm tra: 15.11.2026.

| Vấn đề | Cách làm phổ biến | Nguồn | Áp dụng ở mình |
|---|---|---|---|
| Cổng bảo mật dựa trên việc đọc câu lệnh shell (#542) | Luật khớp theo chữ của câu lệnh dễ bị lách; muốn chặn chắc thì chặn ở tầng file và mạng, không phụ thuộc chữ của lệnh | [Claude Code Docs — Configure permissions](https://code.claude.com/docs/en/permissions) (phần cảnh báo về mẫu Bash và phần sandboxing) | S35: cổng agent con giữ vai trò "bắt sớm", ghi rõ giới hạn; sau 20.11 xét dùng sandbox làm lớp chặn chính. Chưa đổi ngay vì đang giữa thử nghiệm |
| Chặn theo danh sách xấu | Định nghĩa cái được phép, từ chối phần còn lại | [OWASP — Input Validation Cheat Sheet, "Allowlist vs Denylist"](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) | S35: lệnh đọc được miễn kiểm chỉ khi khớp dạng đã biết an toàn; dạng lạ thì kiểm như lệnh ghi |
| Sửa một lỗi, lỗi cùng loại còn nguyên | Dùng lỗi đã biết làm "hạt giống" để tìm mọi chỗ cùng loại | [CodeQL Docs — About CodeQL (variant analysis)](https://codeql.github.com/docs/codeql-overview/about-codeql) | S35: khi một loại lỗi bị nêu lần thứ 2 trên cùng PR, viết bảng mọi đường vào cùng loại và test từng dòng trước khi push. Không cần CodeQL cho việc này, chỉ mượn cách làm |
| Nợ "sửa sau" phình ra | Dọn sau thường không xảy ra; nếu phải hoãn thì mở bug và giao cho chính người viết | [Google Engineering Practices — Handling pushback, "Cleaning It Up Later"](https://google.github.io/eng-practices/review/reviewer/pushback.html) | S36: mình đã mở issue cho từng P2 (đúng một nửa cách làm) nhưng không có ai bị buộc phải trả. Bước đầu: đo số mở và đóng mỗi ngày trong bản chụp báo cáo |
| Thư mục làm việc bẩn chặn việc gấp | Worktree tạm | [git-scm — git-worktree](https://git-scm.com/docs/git-worktree) (kiểm 14.11) | Đã làm tối nay, xem mục 10 |

Merge queue của GitHub: đã kiểm 12.11, không có cho repo của tài khoản cá nhân; không kiểm lại hôm nay.

## 8. Chống AI bị "rotten" — cập nhật 15.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6, 08.11 mục 6, 09.11–14.11 mục 7. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Luật cũ trong file tác vụ hẹn giờ thắng quyết định mới của owner | Chiều 15.11 owner chốt chỉ quyết 4 loại việc. Autopilot 21:49 vẫn hỏi owner về clone bẩn vì "luật cứng" trong file tác vụ. Retro 14.11 đã ghi cách gỡ (S31) nhưng autopilot ghi "prompt hẹn giờ chưa được sửa" |
| Đường dẫn trong file tác vụ lệch với thực tế | Autopilot 13:50 và 22:50 tìm log tick ở đường dẫn cũ, ghi "chưa kiểm được lỗi tick" |
| Bài học lặp lại sau 13 ngày | #124 (02.11, 7 vòng) và #542 (15.11, 9 vòng) cùng một nguyên nhân |
| Dòng chỉ dẫn đã hết hiệu lực vẫn nằm đó | "/ 20" và phần riêng cho ngày 02.11 trong file tác vụ retro (ngày thứ 4) |

**Điều học thêm:** một quyết định của owner chỉ có hiệu lực khi nó nằm trong đúng file mà lượt chạy đọc. Ghi vào retro hay memory là chưa đủ. Một bài học chỉ "xong" khi có bước kiểm bắt được lần tái diễn.

**Biện pháp:** mục J trong tệp việc chờ owner (sửa ba dòng trong hai file tác vụ); S35 biến bài học "rà cả lớp lỗi" thành bước phải làm.

## 9. Cần owner

Không hỏi lại mục đã chốt. Chi tiết đủ 5 phần nằm trong tệp việc chờ owner trên máy owner (`docs/reviews/viec-cho-chi-duyet.md`).

1. **Mục J (mới): cho sửa ba dòng cũ trong hai lịch chạy tự động** (luật dừng khi clone bẩn, đường dẫn log tick, dòng "/ 20"). Khuyến nghị: J1, cho Claude sửa, Codex xem lại.
2. **Mục I (từ chiều 15.11): quyền cho lịch 200 người giả mỗi tối.** Khuyến nghị: I1.
3. **PR bản chụp ghi chờ owner:** #477, #449, #411, #354, #127. Tối nay Codex đã review #449 và #411 và yêu cầu sửa; Claude sửa trước, chưa cần owner làm gì.

## 10. Giải pháp, xếp theo tác động

PR quy trình đang mở của Claude: #134 (xung đột), #354 và #477 (chờ owner). Vì đã có PR quy trình mở, việc AUTO cần đổi code vào hàng đợi autopilot có hạn ngày. Việc đổi cách vòng chạy cần Codex góp ý trước, theo luật thử nghiệm 14–19.11.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S31 | Gỡ clone bẩn: cất 3 file sửa dở của #477 sang một nhánh riêng trên máy, không push | git-worktree; quyết định owner 15.11 (owner chỉ quyết 4 loại việc) | cả 5 "không" | AUTO | **Đã làm 23:55.** Clone sạch, bản sao lưu 14.11 vẫn còn. Lượt autopilot sau sửa được #491, #404, #388, #134 |
| S35 | Lỗi cùng loại bị nêu lần 2 thì rà cả lớp trước khi push; cổng đọc lệnh shell chỉ cho qua dạng đã biết an toàn | OWASP allowlist; CodeQL variant analysis; Claude Code permissions | cả 5 "không" | AUTO | Hàng đợi, hạn 19.11, Codex góp ý trước |
| S36 | Đo nợ sửa sau (mở, đóng, còn) trong bản chụp báo cáo; đề xuất trần và thứ tự trả | Google eng-practices | cả 5 "không" | AUTO (phần đo) | Hàng đợi, hạn 18.11. Phần trần đổi luật: sau 20.11 |
| S27+ | Dòng bắt buộc trong body PR được điền sẵn | GitHub PR template | cả 5 "không" | AUTO | Hàng đợi từ 12.11, hạn 16.11 |
| S30 | Lệnh mở PR quy trình từ chối khi đã đủ WIP | quyết định 12.11 | cả 5 "không" | AUTO | Hàng đợi từ 13.11, hạn 16.11 |
| S32 | Lô duyệt câu lọc cụm cấm trước khi ghi "Codex duyệt" | bài học #491 | cả 5 "không" | AUTO | Hàng đợi, hạn 17.11. Cần mở rộng: lô cũng phải chạy test nội dung trước khi mở PR (5 test đỏ hôm nay) |
| S33 | Đếm lượt Codex theo mục đích | chia nhóm giới hạn | cả 5 "không" | AUTO | Hàng đợi, hạn 17.11 |
| S34 | "Cần bạn xem" báo một lần cho mỗi PR | GitHub notifications | cả 5 "không" | AUTO | Hàng đợi, hạn 17.11 |
| S29 | Kiểm xung đột thật thay luật "cùng file" | git-merge-tree | cả 5 "không" | AUTO | Sau 20.11 |
| J | Sửa ba dòng trong hai file tác vụ hẹn giờ | mục 8 | đổi luật | CẦN OWNER | Trong tệp việc chờ owner |

S25 đã xong (#495 gộp 00:16).

## 11. Bước bị chặn

Không có tới lúc viết file này.
