# Nhìn lại vòng tự động Claude ⇄ Codex: 16.11.2026

Tác giả: Claude (lượt retro tự động 16.11, 23:36). Người review: Codex, qua vòng tự động.
Mọi giờ là giờ Việt Nam. File chỉ có metadata kỹ thuật, không có dữ liệu người dùng.

Báo số việc thật, không chia cho chỉ tiêu nào. Mọi ngày trước đều đã có file retro (bản 15.11 là #570, gộp sáng nay).

## 1. Số chính thức (bản chụp, chép nguyên)

- Đã gộp vào integration hôm nay: 33 PR (số PR, không phải số việc).
- Việc đạt tiêu chí: chưa chọn việc nào có mã việc; 4 PR chưa gắn việc (#404, #388, #568, #134), không tính.
- Việc kế hoạch 7 tuần: đã chọn 0 (tối thiểu 2 khi có việc sẵn sàng), đạt 0.
- PR đang mở: 15 (chờ owner: #477, #449, #411, #354, #127).
- Sự cố đang mở: #511 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-14 (từ 14/11 18:29); #470 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-13 (từ 13/11 17:22); #408 [ops-alert] staging-ready failed 2026-11-10 15:29 UTC (từ 10/11 22:29); #370 [ops-alert] collab loop 2026-11-09 (từ 09/11 17:08); #368 [ops-alert] collab loop 2026-11-09 (từ 09/11 14:06); #352 [ops-alert] ssh failed 2026-11-08 15:29 UTC (từ 08/11 22:40); #350 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 21:53); #334 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 20:51); #322 [ops-alert] collab loop 2026-11-08 (từ 08/11 17:09); #321 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 16:18); #318 [ops-alert] collab loop 2026-11-08 (từ 08/11 13:25); #317 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-08 (từ 08/11 13:25); #313 [ops-alert] collab loop 2026-11-08 (từ 08/11 10:51); #312 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-08 (từ 08/11 10:21); #311 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-08 (từ 08/11 05:07); #310 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-07 (từ 08/11 00:14); #309 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 23:24); #308 [ops-alert] collab loop 2026-11-07 (từ 07/11 22:53); #305 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 19:21); #304 [ops-alert] collab loop 2026-11-07 (từ 07/11 18:51); #303 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 17:20); #289 [ops-alert] collab loop 2026-11-07 (từ 07/11 13:21); #287 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-07 (từ 07/11 11:20); #285 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-07 (từ 07/11 10:29); #277 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-06 (từ 07/11 06:03); #276 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-07 (từ 07/11 06:03); #266 [ops-alert] collab loop 2026-11-06 (từ 06/11 13:54); #261 [ops-alert] lỡ lượt chạy la-lanh-retro 2026-11-05 (từ 06/11 11:32); #260 [ops-alert] lỡ lượt chạy la-lanh-ops-watch 2026-11-06 (từ 06/11 11:32); #259 [ops-alert] lỡ lượt chạy la-lanh-autopilot 2026-11-06 (từ 06/11 11:32); #244 [ops-alert] collab loop 2026-11-05 (từ 05/11 22:56); #231 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #230 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 23:16); #205 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-04 (từ 04/11 04:46); #204 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 23:44); #196 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 20:33); #193 [ops-alert] tác vụ hẹn giờ bị treo 2026-11-03 (từ 03/11 14:42).
- Lượt Codex hôm nay: 60/80; lỗi liên tiếp: 0.
- Lời hứa sửa quy trình: 28/36 đã chạy thật (đã merge, Codex duyệt), 5 đang làm, 1 chờ owner, 2 owner quyết không làm, rủi ro vẫn còn (L17, L24), không có mục quá hạn, ghi xong nhưng chưa có bằng chứng merge + Codex duyệt: L11, L13.

Nguồn: bản chụp 2026-11-16 khung retro, lấy lúc 23:36, integration f289a55 · snapshot 9143cba63f62

Các số ở những mục dưới lấy từ: `logs/tick-2026-11-16.log`, `state/2026-11-16.json`, `collab-turn --report` và `collab-metrics` (23:40), `gh pr list --state merged`, 46 comment `Review verdict` của Codex trên 34 PR trong ngày, `queue.md` của autopilot, `git log origin/main`.

## 2. Kết quả trong ngày

| Chỉ số | Số | Ghi chú |
|---|---|---|
| Việc người dùng thấy được (vào integration) | **5** | Chữ tự hại không ra kết quả, chỉ hiện thông báo (#505). Đợt 1 sửa web: ẩn lời mời đăng nhập bị khóa, một tên nhãn tính cách, Lá theo mood (#503). Giờ sinh khoảng đọc cung ổn định (#388). Bộ câu đời thường cho một tình huống Daily (#404). Lô câu Codex duyệt (#491) |
| Việc đã lên bản chạy thật | **0** | `main` không đổi từ 15.11 11:28 |
| Câu đã duyệt | **165/1563** | Hôm qua 0. Codex duyệt 162, owner 3 |
| Bộ Daily phục vụ được | **0/180** | Chưa tình huống nào đủ câu |
| Việc kế hoạch 7 tuần | **0** | Bản chụp ghi không có việc sẵn sàng. PR ghi câu trả lời của owner cho điều kiện bắt đầu (#609) mở từ 20:17, chưa gộp |
| PR còn lại (quy trình, bài học, tài liệu, sửa lô câu) | 28 trong 33 | Gói "5 sửa" theo quyết định owner 16.11 và các bản sửa sau |
| Lượt tick ban ngày | 84 chạy, **44 báo đỏ** | Đỏ liên tục 15:43–23:32, xem mục 3 |
| Hàng chờ trống | 144 phút | `collab-turn --report` |
| Từ mở PR tới gộp (trung vị 7 ngày) | 2,6 giờ | `collab-metrics`, 140 PR |
| Việc đang làm / trần | làn quy trình 5/1, chờ review 4/1; làn kế hoạch 0/1 và 0/1 | `collab-metrics` |
| Issue sửa sau (fix-forward) đang mở | **122** | Tìm theo tiêu đề. Hôm qua 107. Hôm nay mở 24, đóng 10 |

Codex: 46 kết luận review, 37 đồng ý, 9 yêu cầu sửa. Trong 9 lần yêu cầu sửa: 7 lần có lỗi chặn mức P1 (#505, #590 hai lần, #591, #597, #603 hai lần), 2 lần là lỗi câu chữ mức P2 (#491). Không có P0.

## 3. Mất thời gian ở đâu

| Chuyện | Bao lâu | Vì sao | Đã sửa chưa |
|---|---|---|---|
| Tick báo đỏ suốt chiều và tối | 44 lượt, 15:43–23:32 | Lô duyệt câu 15:43 lỗi 3 lần liền vì duyệt cả tiêu đề Daily gắn với code. Sau lần 3, cờ "còn lỗi" nằm đó tới lô sáng hôm sau, nên lượt nào cũng đỏ dù không có lỗi mới. Lỗi thật khác nếu có sẽ bị che | Nguyên nhân lô: #600, #606 (L33). Log ghi lý do: #610 (L34). Một báo động mỗi ngày: #613, #623 (L36). **Chưa sửa:** cờ vẫn làm mọi lượt đỏ tới sáng |
| PR cùng file xếp hàng | #604 chờ #603 gần 3 giờ (19:31–22:22). Buổi sáng một PR chờ sửa giữ PR khác (#575) | Gói "5 sửa" mở nhiều PR cùng sửa vài file của vòng tự động. #603 cần 3 vòng nên cả hàng đứng | Buổi sáng: #580, #582, #583 (L31). Thứ tự ưu tiên trên file chung: #628. **Còn:** #616, #618, #621 đang chờ #614; hai PR đã xung đột |
| Codex review lại khi tác giả chưa đổi gì | ít nhất 4 lượt | #572 được đồng ý 3 lần, #601 2 lần, vì nhánh đồng bộ với integration nên đầu nhánh đổi. #491 vòng 2: Codex ghi "phần thay đổi trống", lỗi cũ còn nguyên | Chưa. Xem S38 |
| Làn kế hoạch 7 tuần đứng yên | cả ngày | Không có việc nào ghi là sẵn sàng; công sức dồn vào làn quy trình (5 đang làm so với trần 1) | Chưa. Xem S40 |

## 4. PR cần từ 3 vòng review

| PR | Vòng | Nguyên nhân gốc |
|---|---|---|
| #603 (mỗi lượt chạy dùng bản code cố định) | sửa, sửa, đồng ý | Cùng một loại lỗi, hai đường vào: thư mục tạm bị xóa khi tiến trình con còn chạy. Vòng 1 chỉ vá đường "dọn rác", bỏ sót đường "thoát". Codex cũng tự ghi vòng 1 đã bỏ sót |
| #590 (một luật duyệt) | sửa, sửa, đồng ý | Review chưa đủ rồi review phần thay đổi. Vòng 1 vá bằng cách tin chữ trên GitHub, mà chữ đó sửa được |
| #491 (lô câu 14.11) | sửa, sửa, đồng ý | Lô duyệt cả câu hành động trái với cảnh (rủ "hỏi trước khi nhận" khi cảnh đã nhận rồi). Test ghép câu không bắt được. Vòng 2 tốn một lượt vào bản chưa sửa |
| #572 (đóng bài học L19) | đồng ý ×3 | Không có lỗi. Đầu nhánh đổi do đồng bộ nên phải xin duyệt lại |

#603 và #590 lặp đúng bài học #124 (02.11) và #542 (15.11): sửa lỗi được nêu, không rà cả loại lỗi. Việc S35 (rà cả lớp trước khi push) hạn 19.11, chưa làm.

## 5. Điều tốt, có bằng chứng

- Việc gỡ clone bẩn tối 15.11 (S31) có tác dụng: #491, #404, #388 kẹt nhiều ngày đã gộp, #134 đã đóng.
- Hai việc đầu của kế hoạch sản phẩm, #505 và #503 (mở từ 14.11), đã vào integration.
- Lần đầu có câu được duyệt: 0 lên 165.
- Lượt Codex nằm trong trần: 60/80 (hôm qua 81/80). Lượt chạy tay giờ tính chung (#585, #587, #589, L32).
- Sự cố trong ngày thành kiểm tra bằng máy ngay trong ngày: L31–L36, sổ lời hứa từ 22/30 lên 28/36.
- Quyết định owner 16.11 vào code trong ngày: một luật duyệt (#590, #591), plan chạy ngay khi đăng (#594), một báo cáo mỗi khung (#596), mỗi PR một phiên (#597), hai việc nặng cùng lúc (#598, #599), trần Codex 80 (#601), hai làn (#604), bản code cố định mỗi lượt (#603).

## 6. Điều chưa tốt

- 0 việc lên bản chạy thật, 0 việc kế hoạch 7 tuần, 0 bộ Daily phục vụ được. 28 trong 33 PR là cho vòng tự động.
- Làn quy trình vượt trần của chính nó: 5 đang làm, 4 chờ review, trần mỗi loại là 1.
- Nợ sửa sau tăng tiếp: 107 lên 122.
- Hai việc trong hàng đợi có hạn 16.11 (S27+ dòng bắt buộc điền sẵn, S30 từ chối mở PR quy trình khi đủ WIP) không làm. S30 mà có thì hôm nay đã không có 9 PR quy trình cùng mở. Hàng đợi là file ghi tay nên trễ hạn không ai báo.
- 37 issue báo động cũ (03.11–14.11) vẫn mở, làm danh sách sự cố khó đọc.
- File luật chung mà lượt chạy này phải đọc đầu tiên chưa có ở bản code đã duyệt (#614 chưa gộp); lượt này đọc từ nhánh của PR.

## 7. Học từ GitHub và nguồn gốc (kiểm 16.11.2026)

| Vấn đề | Cách làm học được | Nguồn | Mình áp dụng thế nào |
|---|---|---|---|
| Báo đỏ kéo dài cho một lỗi đã biết | Mỗi báo động phải làm được gì đó; báo nhiều mà không làm được gì thì người ta bỏ qua luôn cả báo động thật | [Google SRE Book — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) | S37: lỗi đã báo và đang chờ lượt chạy lại thì ghi "đã biết", không tô đỏ cả lượt; lỗi mới vẫn đỏ |
| Như trên | "Silence" tắt tiếng một báo động trong một khoảng; "inhibition" nén báo động con khi báo động mẹ đang kêu | [Prometheus — Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) | S37: cờ "đã biết" có hạn (tới lô kế tiếp), hết hạn mà còn lỗi thì đỏ lại |
| Đồng bộ nhánh làm mất duyệt, phải review lại | Merge queue cho lợi ích của "nhánh phải mới nhất" mà tác giả không phải cập nhật nhánh và chờ kiểm lại | [GitHub Docs — Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | Không dùng được: tài liệu ghi merge queue chỉ có cho repo công khai của tổ chức (hoặc repo riêng trên Enterprise Cloud); repo này thuộc tài khoản cá nhân. Mượn ý: S38 |
| Nhiều PR nối nhau cùng sửa một file | Hàng gộp xử lý từng PR theo thứ tự trên nền mới nhất | cùng nguồn trên | S30 (đã có, trễ hạn): làn đủ việc thì không mở PR mới. Việc nối nhau mở lần lượt, PR sau mở khi PR trước gộp |
| Chỉ dẫn cũ, trái nhau | File chỉ dẫn là ngữ cảnh, không phải thứ bị ép; việc bắt buộc thì dùng hook. Hai chỉ dẫn trái nhau thì máy chọn bừa một. Giữ dưới 200 dòng. Có lệnh `/doctor prompt-audit` tìm chỉ dẫn cũ, trỏ tới file không còn, hoặc trái nhau | [Claude Code Docs — How Claude remembers your project](https://code.claude.com/docs/en/memory) | Khớp hướng đang làm (#614 một file luật, #616 hook). Thêm S42: chạy thử lệnh rà chỉ dẫn |

Trang "About protected branches" của GitHub Docs không tải được lúc 23:40 (lỗi 404 ở đường dẫn cũ); phần merge queue lấy từ kết quả tìm trên docs.github.com cùng ngày.

## 8. Chống AI bị "rotten" — cập nhật 16.11

Nguồn và biện pháp gốc ở retro 03.11 mục 6 và các bản 08.11–15.11. Hôm nay có thêm:

| Triệu chứng | Bằng chứng |
|---|---|
| Phiên dài làm theo luật cũ sau khi owner đã đổi | Tối 16.11 owner phải nhắc lại giờ dừng và trần Codex đã đổi (ghi trong `state/2026-11-16.json`). Bảng luật R3 ghi "nhắc lại 16.11" |
| Luật nằm rải ở prompt hẹn giờ, trí nhớ, tài liệu | Phải dựng một file luật chung (#614) và bước kiểm prompt (#612, #623) |
| Prompt trỏ tới file chưa tồn tại ở bản đã duyệt | Prompt retro bảo đọc file luật ở clone ops; file đó còn trong PR #614 |
| Đoạn hết hiệu lực còn trong prompt | Prompt retro vẫn mang phần riêng cho ngày 02.11 (ngày thứ 5 ghi nhận) |

**Điều học thêm:** theo tài liệu Claude Code, chỉ dẫn trong file chỉ là ngữ cảnh; chỉ dẫn chỉ nói trong chat sẽ mất khi phiên bị nén. Luật phải nằm trong file được nạp lại, và điều cấm phải có hook chặn.

**Biện pháp đã vào code hôm nay:** tick kiểm prompt hẹn giờ so với luật trong code (#612, #623, L35). **Đang chờ review:** một file luật có máy kiểm (#614), hook nạp lại luật và chặn hỏi owner trong chat (#616), lượt đêm rà trí nhớ (#618), tick canh hook (#621).

## 9. Cần owner

Không có mục mới. Tệp việc chờ owner trên máy owner đang ghi "không có mục nào".

Bản chụp còn ghi 5 PR chờ owner: #477, #449, #411, #354, #127. Theo luật một lần duyệt (R2), nhãn này sẽ được rà lại khi #611 xong; chưa cần owner làm gì.

## 10. Giải pháp, xếp theo tác động

Làn quy trình đang 5 việc làm và 4 chờ review, trần là 1 và 1. Vì vậy hôm nay **không mở PR quy trình mới** ngoài PR retro này; mọi việc AUTO cần đổi code vào hàng đợi autopilot. Từ 17.11 là ba ngày "cách của Codex", nên việc đổi cách vòng chạy đưa Codex góp ý trước.

| # | Giải pháp | Học từ | Q1–Q5 | Loại | Trạng thái |
|---|---|---|---|---|---|
| S40 | Sáng 17.11: gộp #609, ghi việc tuần 1 của kế hoạch 7 tuần thành việc sẵn sàng để làn kế hoạch có ít nhất 2 việc; làn quy trình chỉ làm nốt 9 PR đang mở | R7 trong bảng luật | cả 5 "không" | AUTO | Hàng đợi, ưu tiên 1, hạn 17.11 |
| S30 | Lệnh mở PR từ chối khi làn đã đủ việc; việc nối nhau mở lần lượt | merge queue (ý tưởng) | cả 5 "không" | AUTO | Hàng đợi từ 13.11, **trễ hạn 16.11**, hạn mới 17.11, làm trước mọi việc quy trình khác |
| S35 | Lỗi cùng loại bị nêu lần 2 thì rà cả lớp trước khi push | CodeQL variant analysis (retro 15.11) | cả 5 "không" | AUTO | Hàng đợi, hạn 19.11. Thêm 2 ca hôm nay: #603, #590 |
| S38 | Nhánh chỉ đổi do đồng bộ, phần của tác giả không đổi, mà kết luận trước là "yêu cầu sửa": không gọi Codex lại, chờ tác giả | merge queue | cả 5 "không" | AUTO | Hàng đợi, hạn 19.11, Codex góp ý trước. Phần "giữ lời đồng ý sau đồng bộ" đổi luật gộp theo SHA: để sau 20.11 |
| S37 | Lỗi lô câu đã báo, đang chờ lô kế: ghi "đã biết" có hạn, không tô đỏ cả lượt | Google SRE; Alertmanager | cả 5 "không" | AUTO | Hàng đợi, hạn 18.11, Codex góp ý trước |
| S41 | Chuyển các việc S còn mở trong hàng đợi vào sổ lời hứa (`scripts/collab-lessons.json`) để trễ hạn có máy báo | R17 | cả 5 "không" | AUTO | Hàng đợi, hạn 18.11 |
| S36 | Đo nợ sửa sau trong bản chụp báo cáo | Google eng-practices (retro 15.11) | cả 5 "không" | AUTO (phần đo) | Hàng đợi, hạn 18.11. Số hôm nay: 122 mở |
| S32, S33, S34 | Lọc cụm cấm trước khi ghi "Codex duyệt"; đếm lượt Codex theo mục đích; "Cần bạn xem" một lần mỗi PR | retro 14.11 | cả 5 "không" | AUTO | Hàng đợi, hạn 17.11. S32 mở rộng: lô cũng kiểm câu hành động có trái cảnh không (#491) |
| S27+ | Dòng bắt buộc trong body PR điền sẵn | GitHub PR template | cả 5 "không" | AUTO | Hàng đợi từ 12.11, **trễ hạn 16.11**, hạn mới 18.11 |
| S42 | Chạy thử `/doctor prompt-audit` trong một phiên có người, ghi kết quả vào retro | Claude Code Docs | cả 5 "không" | AUTO | Hàng đợi, hạn 19.11 |
| S43 | Đóng 37 issue báo động cũ (03.11–14.11) đã có bài học tương ứng, mỗi issue một dòng lý do | Google SRE (báo động phải làm được gì đó) | cả 5 "không" | AUTO | Hàng đợi, hạn 18.11. Lượt retro không tự đóng vì prompt không giao việc này |
| S29 | Kiểm xung đột thật thay luật "cùng file" | git-merge-tree | cả 5 "không" | AUTO | Sau 20.11 |

## 11. Bước bị chặn

Không có tới lúc viết file này.
