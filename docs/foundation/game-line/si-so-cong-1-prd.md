# Sĩ Số +1 — PRD

> Phiên bản: 0.1 (nháp) · Cập nhật: 26/10/2026 · Trạng thái: **chờ owner duyệt, chưa được duyệt để triển khai.**
> Giai đoạn 3 (game) chưa bắt đầu; bây giờ chỉ làm tài liệu và chơi thử bằng giấy (kế hoạch owner 23/10/2026).
> Owner chốt ngày 26/10/2026: **Sĩ Số +1 và Phiên Tòa Tủ Lạnh là hai trò riêng**, dùng chung hạ tầng phòng.
> Tài liệu liên quan: [SRS](si-so-cong-1-srs.md) · [hạ tầng phòng](shared-room-platform-srs.md) · user story G41–G47 và G01–G09
> trong [`docs/user-stories/game/`](../../user-stories/game/) · [README dòng game](README.md).
> Nền nghiên cứu: báo cáo "Chốt năm trò, giữ trọn chữ Lành" (26/10/2026), mục "Sĩ Số +1: rợn nhẹ, 'sao nó biết', và người thứ 31 là
> chính cả lớp"; `research_notes/Chốt trò chơi nhóm Lá Lành/comedy_courtroom_formats.md` §1, §5;
> `research_notes/Trò chơi viral thần bí cho nhóm/risks_privacy_policy.md` §1, §5.

> **"Lớp bạn có 30 người. Điểm danh ra 31."**

## 0. Tóm tắt một đoạn

Sĩ Số +1 là trò ẩn vai rợn nhẹ kiểu Ma Sói cho 15–50 người trong một phòng, chơi bằng màn chiếu và điện thoại, dài 25–30 phút. Mở
màn, bộ đếm sĩ số chạy tới đúng số người đang có rồi nhảy thêm một: **N+1**. Một cái tên mờ hiện trong danh sách. Mỗi người trả lời 5
câu vô hại về mình. Vài người là **Kẻ Bị Nhập**: mỗi đêm họ chọn một người trong 3 ứng viên ngẫu nhiên và "thì thầm" cho con ma một
câu trả lời của người đó. Sáng ra, **Người thứ N+1** nói trên màn chiếu một chi tiết thật ("Sáng nay có người ăn bánh mì trứng. Người
đó đang mặc áo xanh dương.") và người đó thành **Hồn** — vẫn chơi tiếp, gửi chữ cái giúp Người Sống. Ban ngày cả phòng bỏ phiếu trục
xuất. Vòng 3 có **khoảnh khắc Akinator**: con ma đoán đúng biệt danh người cả phòng đang nghĩ tới bằng vài câu có/không. Cuối buổi,
màn hình kể lại từng lời thì thầm (mặc định chỉ nêu "một Kẻ Bị Nhập đã thì thầm" — SS-D10), rồi lật: **Người thứ N+1 là bản sao ghép từ câu trả lời của cả lớp**, chỉ bằng số đếm.
Rồi hồ sơ bị xoá ngay trên màn hình. Văn phòng mặc định chơi chế độ **"bật đèn"**: Người thứ N+1 là nhân viên mới không ai nhớ đã
tuyển (D6, chờ owner).

## 1. Bối cảnh và bằng chứng

- **Khung Ma Sói đã được kiểm chứng** và là trò "bí mật" quen thuộc nhất với giới trẻ Việt (báo cáo, dẫn báo cáo đầu tiên).
- **Một khoảnh khắc cả phòng cùng thấy** — bộ đếm nhảy lên N+1 — đúng loại khoảnh khắc mà các hiện tượng 2025–2026 dựa vào (báo
  cáo, dẫn báo cáo thứ hai). Đây cũng là cảnh dễ quay clip nhất trong danh mục (báo cáo, bảng bảy trò).
- **"Sao nó biết?" không cần AI.** Con ma chỉ đọc lại câu trả lời thật mà Kẻ Bị Nhập đã chọn. Vòng Akinator dựa trên một sản phẩm từng
  có hơn 100 triệu lượt cài (báo cáo, dẫn AppBrain), chạy bằng cây quyết định dựng từ 5 câu trả lời.
- **Quy mô lớn cần nhóm song song.** Mọi trò ẩn vai quá khoảng 10 người đều tách nhóm (Ultimate Werewolf tới ba làng) hoặc dùng khán
  giả bỏ phiếu (Jackbox); Blood on the Clocktower chậm dần khi đông, đêm gần 10 phút ở ván lớn (research note §1, §5). Vì vậy lớp 25–50
  chia **dãy bàn** thảo luận song song và pha đêm chỉ 60 giây.
- **Chủ đề ma có thể gây hoảng loạn đạo đức dù không có bằng chứng tác hại.** Momo và Blue Whale là "hoảng loạn đạo đức kinh điển";
  cảnh sát Bắc Ireland từng ra cảnh báo Momo khi chưa nhận khiếu nại nào (research note risks §1; báo cáo dẫn The Conversation). Vì
  vậy: không tin nhắn dây chuyền, không thử thách ngoài đời, **luôn giải thích cơ chế ở cuối**.

Suy luận: cú lật "bản sao ghép từ cả lớp" biến quy tắc an toàn "giải thích con ma biết bằng cách nào" thành cao trào (báo cáo, kết luận).

## 2. Mục tiêu, phi mục tiêu và nguyên tắc

### 2.1. Mục tiêu

| ID | Mục tiêu | Cách biết đã đạt |
|---|---|---|
| SS-G1 | Khoảnh khắc "sao nó biết" | ≥ 2 lần mỗi buổi cả phòng thốt lên hoặc có người rút điện thoại quay (quan sát chơi thử) |
| SS-G2 | Lớp đông vẫn có tiếng nói | Tỷ lệ người từng lên tiếng trong thảo luận (quan sát), so giữa lớp 15–24 và 25–50 |
| SS-G3 | Rợn nhẹ, không sợ thật | Câu khảo sát "Có lúc nào bạn thấy bị nhắm vào hoặc sợ thật không?": mục tiêu 0 "Có"; 0 báo cáo "Tôi thấy bị nhắm vào" |
| SS-G4 | Ai cũng hiểu con ma biết bằng cách nào | 100% buổi chạy tới màn giải thích (trừ khi host kết thúc sớm — khi đó màn kết thúc vẫn có câu giải thích ngắn) |
| SS-G5 | Host muốn tổ chức lần nữa | Số lần bấm "Chơi lại" và "Tôi muốn tự làm host" ở màn kết thúc |
| SS-G6 | Không rủi ro riêng tư mới | Xoá khi kết thúc, chậm nhất 2 giờ sau khi bắt đầu; không SDK bên thứ ba |

### 2.2. Phi mục tiêu

- Không máu me, không cái chết, không tự hại, không lời nguyền, không "chia sẻ cho 10 người nếu không sẽ…", không thử thách ngoài đời.
- Không nghi lễ hay hình ảnh tôn giáo thật; "Thầy Pháp" và "bị nhập" là vai trò hư cấu kiểu truyện ma học trò.
- Không tin nhắn, thông báo hay "tập sau" gửi tới người chơi sau buổi (mạch dài để sau, xem §8).
- Không AI (D7). Không giọng nói chạy quanh phòng ở MVP.
- Không loại người khỏi cuộc chơi: người bị bắt thành Hồn, người bị trục xuất ra "hành lang", ai cũng còn việc.
- Không streak, coin, XP, điểm mang sang buổi sau.
- Không bản cho người dưới 18 tuổi (lớp phổ thông để sau, khi giáo viên là host và học sinh không tài khoản — báo cáo).

### 2.3. Nguyên tắc thiết kế

1. **Con ma chỉ nói điều người chơi tự khai và đồng ý cho hiện.** Không đoán, không suy ra gì mới.
2. **Luôn giải thích cơ chế ở cuối.** Cú lật cuối chính là lời giải thích.
3. **Không ai bị nhắm liên tục.** Kẻ Bị Nhập chỉ chọn trong 3 ứng viên ngẫu nhiên, ưu tiên người ít được đưa vào danh sách; không ai bị
   bắt hai lần.
4. **Bị bắt vẫn có quyền.** Hồn gửi chữ cái, tham gia Akinator và màn lật.
5. **Rợn vừa đủ, có công tắc.** Chế độ bật đèn cho văn phòng và nhóm ngại ma; ai cũng có thể chỉ xem.
6. **Đêm ngắn.** 60 giây; mọi điện thoại đều có một việc giống nhau để không ai đoán được ai đang hành động.

## 3. Người dùng và bối cảnh chơi

Chỉ người từ 18 tuổi.

| Persona | Mô tả | Cần gì |
|---|---|---|
| **Host lớp đại học** — Khoa, 21, bí thư chi đoàn | Sinh hoạt lớp 30–40 người, muốn một cảnh quay "viral" | Mở nhanh, chia dãy bàn, tự chạy |
| **Người thích kinh dị** — Vy, 19 | Mê truyện ma học đường | Không khí, cú lật, chế độ ma đầy đủ |
| **Người sợ ma** — Hùng, 22 | Không thích yếu tố rợn | Biết trước nội dung, chọn chỉ xem hoặc phòng chơi bật đèn |
| **Host văn phòng** — chị Lan, 31, team lead | Team building 20 người | Bật đèn mặc định, không làm ai sợ thật, không xấu hổ |

## 4. Luật chốt

### 4.1. Dòng chảy một buổi (4 vòng mặc định, 25–30 phút)

| Hồi | Bước | Thời lượng |
|---|---|---|
| Mở màn | QR (G01, G02). Bộ đếm chạy *…N−2… N−1… N* rồi nhảy tiếp **N+1** (N = số người chơi có vai). Một cái tên mờ hiện trong danh sách. Màn hình tối, từng chữ hiện: *"Cảm ơn lớp đã cho tôi vào."* | 2 phút |
| Khai báo | 5 câu vô hại chung (G03). Điện thoại báo vai (G04, G42); lớp đông chọn dãy bàn | 3 phút |
| Đêm | Ai cũng làm một việc giả trên điện thoại. Kẻ Bị Nhập nhận **3 ứng viên ngẫu nhiên**, chọn một người và chọn một câu trả lời để thì thầm. Thầy Pháp soi một người. Hồn chọn một chữ cái để gửi | 60 giây |
| Sáng | Người thứ N+1 nói một chi tiết thật + một chi tiết thứ hai, rồi biệt danh người đó hiện: "… giờ là Hồn." Chữ của Hồn hiện lên bảng thư. Thầy Pháp nhận kết quả riêng | 40–75 giây |
| Ngày | Thảo luận; lớp 25–50 chia 2–3 **dãy bàn** thảo luận song song, mỗi dãy một người tình nguyện nói 30 giây. Cả phòng bỏ phiếu cùng lúc để trục xuất một người | 2–3,5 phút |
| Vòng 3 | **Khoảnh khắc Akinator** chen trước phần ngày: *"Hãy cùng nghĩ về một người trong phòng. Tôi sẽ nói tên người đó."* | 2 phút |
| Lật mặt | Từng lời thì thầm: *"Con ma biết chuyện bánh mì trứng vì… một Kẻ Bị Nhập đã thì thầm."* Báo cáo gốc nêu biệt danh ("vì… Lan đã thì thầm"); mặc định của tài liệu này chỉ nêu biệt danh khi chính Kẻ Bị Nhập đó tự bật lúc lật (SS-D10, theo đề xuất DP-1 của DPIA). Lời giải thích cơ chế. Danh sách vai cuối vẫn nêu ai là Kẻ Bị Nhập. Cú lật cuối: Người thứ N+1 là bản ghép từ câu trả lời của cả phòng (chỉ số đếm). **Xoá sổ điểm danh** (tiêu huỷ hồ sơ — G07) | 3–4 phút |

### 4.2. Thắng thua (đề xuất, chờ chơi thử — SS-D2)

- **Người Sống thắng ngay** khi đã trục xuất hết Kẻ Bị Nhập.
- **Con ma thắng ngay** khi số Hồn ≥ một nửa số người chơi có vai lúc bắt đầu (báo cáo: "bắt được một nửa phòng"), hoặc khi số Kẻ Bị Nhập
  còn lại ≥ số Người Sống và Thầy Pháp còn lại.
- **Hết vòng cuối** mà chưa ai thắng ngay: Người Sống thắng nếu đã trục xuất ít nhất một nửa số Kẻ Bị Nhập (làm tròn lên); nếu không, con
  ma thắng.
- Ghi chú: với bảng §5.2 và 4–5 vòng, hai mốc "thắng ngay" của con ma **không đạt được** ở mọi quy mô (ví dụ lớp 30: tối đa 8–10
  người bị bắt, cần 15). Luật hết vòng là luật quyết định; hai mốc kia giữ lại để luật vẫn đúng khi owner đổi tham số. Báo cáo nêu
  "4–5 vòng"; tài liệu chọn 4 làm mặc định để vừa 25–30 phút, host chọn 5 trước khi bắt đầu (SS-FR-05). Bộ chơi thử giấy
  (`docs/playtests/2026-11-game-line/si-so-cong-1/`, quyết định P10) dùng đúng bộ luật này để đo cân bằng.

### 4.3. Hai chế độ

| Khái niệm | **Lớp ma** (lớp đại học, nhóm bạn) | **Bật đèn** (mặc định văn phòng và nhóm ngại ma — D6) |
|---|---|---|
| Nhân vật hệ thống | Người thứ N+1 | Nhân viên mới không ai nhớ đã tuyển |
| Mở màn | Sĩ số 30… 31 | Bảng chấm công 30… 31 |
| Người Sống | Người Sống | Đồng Nghiệp |
| Kẻ Bị Nhập | Kẻ Bị Nhập | Người Được Nhờ (bị nhân viên mới nhờ "chỉ việc") |
| Thầy Pháp | Thầy Pháp | Bên Nhân Sự |
| Hồn | Hồn | Người Đi Họp |
| Bị bắt | "Tôi đã đến tìm người đó" | "Em mời người đó đi họp gấp" |
| Bị trục xuất | Ra đứng ngoài hành lang | Đi công tác |
| Đêm / Sáng | Màn tối / buổi sáng | Giờ nghỉ trưa (màn sáng) / đầu giờ chiều |
| Âm thanh, hiệu ứng | Nhiễu nhẹ, chữ hiện dần (qua kiểm nhấp nháy) | Không nhiễu, giao diện sáng |
| Lá cuối | The Moon (Mặt Trăng), hình tĩnh | The Moon, hình tĩnh |

Hai chế độ cùng luật, chỉ khác chữ và hiệu ứng. Không chế độ nào yêu cầu tắt đèn phòng; hướng dẫn host luôn giữ lối đi sáng.

## 5. Vai

### 5.1. Danh sách vai

| Vai | Số lượng | Việc |
|---|---|---|
| **Người Sống** | Đa số | Tìm và trục xuất Kẻ Bị Nhập |
| **Kẻ Bị Nhập** | 3–5 | Biết đồng bọn. Mỗi đêm, người được giao lượt chọn một người trong 3 ứng viên và chọn một câu trả lời vô hại của người đó để thì thầm |
| **Thầy Pháp** | 1 | Mỗi đêm soi một người: "bị nhập" hay "không" (chỉ mình biết) |
| **Hồn** | Người bị bắt | Không rời cuộc chơi. Được con ma "cho biết" biệt danh một Kẻ Bị Nhập (ngẫu nhiên, không nhất thiết là người đã chọn mình). Mỗi đêm gửi một chữ cái trong biệt danh đó lên bảng thư. Không bỏ phiếu trục xuất; theo luật chơi, Hồn chỉ "nói" bằng chữ |
| **Ngoài Hành Lang** | Người bị trục xuất | Vai được lật. Không bỏ phiếu trục xuất; vẫn làm việc giả ban đêm, đoán (không tính) mỗi ngày, chơi Akinator và xem màn lật |
| **Người thứ N+1** | Hệ thống | Nói trên màn chiếu |

### 5.2. Bảng số vai và nhịp theo quy mô (đề xuất, chờ chơi thử — SS-D2)

| Người chơi | Kẻ Bị Nhập | Thầy Pháp | Người bị bắt mỗi đêm (tối đa, không quá số Kẻ Bị Nhập còn lại) | Dãy bàn |
|---|---|---|---|---|
| 15–19 | 3 | 1 | 1 | Không chia |
| 20–24 | 3 | 1 | 1 | Không chia |
| 25–29 | 3 | 1 | 2 | 2 |
| 30–39 | 4 | 1 | 2 | 2 |
| 40–50 | 5 | 1 | 3 | 3 |
| Trên 50 | Người vào sau làm khán giả (không vai) | | | |

Nguồn: báo cáo (Kẻ Bị Nhập 3–5, Thầy Pháp 1, dãy bàn 2–3 cho lớp 25–50); số người bị bắt mỗi đêm là đề xuất của tài liệu này.

## 6. Ngân hàng nội dung

> **Nháp, chờ owner duyệt văn phong.** Không máu, không chết, không tự hại, không lời nguyền, không tôn giáo thật, không chạm sức khoẻ,
> ngoại hình cơ thể, tình cảm, tiền, gia đình, vùng miền. Con ma "đến tìm", "rủ đi cùng", "mời đi họp" — không bao giờ "làm hại". Mọi
> câu chỉ dùng câu trả lời người chơi đã đồng ý cho hiện.

### 6.1. Cụm từ theo phương án (để ghép câu tự nhiên)

| Câu | Slot | Cụm cho từng phương án |
|---|---|---|
| Bữa sáng | `{cum_bua_sang}` | ăn bánh mì trứng · ăn bánh mì thịt · ăn xôi · ăn phở hoặc bún · ăn cơm tấm · ăn mì gói · ăn bánh bao · ăn cháo · uống sữa với ngũ cốc · chưa ăn gì |
| Loại nhạc | `{cum_loai_nhac}` | nghe nhạc Việt pop · nghe ballad · nghe rap · nghe bolero · nghe K-pop · nghe nhạc Âu Mỹ · nghe nhạc phim · nghe nhạc không lời · nghe EDM · chưa nghe bài nào |
| Chỗ ngồi | `{cum_cho_ngoi}` | ngồi gần cửa sổ · ngồi gần cửa ra vào · ngồi giữa phòng · đang đứng |
| Màu áo | `{cum_mau_ao}` | mặc áo đen · mặc áo trắng · mặc áo xám · mặc áo xanh dương · mặc áo xanh lá · mặc áo đỏ · mặc áo vàng · mặc áo hồng · mặc áo nâu · mặc áo nhiều màu |
| Món trong túi | `{mon_trong_tui}` | sạc dự phòng · tai nghe · bút · chìa khoá · khăn giấy · bình nước · kẹo · ô · sổ tay · son dưỡng |

"Không muốn nói" không có cụm; câu đó không bao giờ được dùng.

### 6.2. Lời buổi sáng — Lớp ma (30 câu chi tiết + 6 câu kết)

Một lời buổi sáng = **câu chi tiết** (bảng dưới) từ câu được thì thầm + **câu nối** từ một câu khác của cùng người + **câu kết**, rồi
dòng biệt danh. Ví dụ: "Sáng nay có người ăn bánh mì trứng. Tôi đứng ngay sau người đó. Người đó đang mặc áo xanh dương. Tôi đã đến
tìm người đó." … "Lan giờ là Hồn."

| ID | Câu | Câu chi tiết |
|---|---|---|
| SS-S01 | Bữa sáng | "Sáng nay có người `{cum_bua_sang}`. Tôi đứng ngay sau người đó." |
| SS-S02 | Bữa sáng | "Tôi nhớ có người `{cum_bua_sang}` lúc trời còn sớm." |
| SS-S03 | Bữa sáng | "Một người ở đây `{cum_bua_sang}`. Tôi đã ngồi cùng bàn." |
| SS-S04 | Bữa sáng | "Có ai đó `{cum_bua_sang}` rất vội. Người đó không thấy tôi." |
| SS-S05 | Bữa sáng | "Sáng nay, một người trong phòng `{cum_bua_sang}`. Tôi nhớ hết." |
| SS-S06 | Bữa sáng | "Tôi hỏi người `{cum_bua_sang}` có ngon không. Người đó không nghe thấy." |
| SS-S07 | Loại nhạc | "Tối qua có người `{cum_loai_nhac}`. Tôi nghe qua bức tường." |
| SS-S08 | Loại nhạc | "Có một người ở đây vừa `{cum_loai_nhac}`. Tôi thuộc luôn giai điệu." |
| SS-S09 | Loại nhạc | "Tôi đã ngồi cạnh người `{cum_loai_nhac}`, nghe ké một bên tai." |
| SS-S10 | Loại nhạc | "Người `{cum_loai_nhac}` ơi, bài đó tôi cũng thích." |
| SS-S11 | Loại nhạc | "Tôi đi theo tiếng nhạc. Có người `{cum_loai_nhac}`." |
| SS-S12 | Loại nhạc | "Có người `{cum_loai_nhac}` trên đường tới đây. Tôi đi cùng mà không ai biết." |
| SS-S13 | Chỗ ngồi | "Người đó đang `{cum_cho_ngoi}`. Tôi đứng gần đó từ đầu buổi." |
| SS-S14 | Chỗ ngồi | "Tôi đếm từng ghế. Có người `{cum_cho_ngoi}` mà không biết tôi ở gần." |
| SS-S15 | Chỗ ngồi | "Gió vừa đổi hướng chỗ người `{cum_cho_ngoi}`. Là tôi đó." |
| SS-S16 | Chỗ ngồi | "Có người `{cum_cho_ngoi}`. Tôi đã chọn chỗ ngay bên cạnh." |
| SS-S17 | Chỗ ngồi | "Người `{cum_cho_ngoi}` có thấy lạnh gáy không? Xin lỗi, tôi đứng hơi gần." |
| SS-S18 | Chỗ ngồi | "Tôi thích chỗ của người `{cum_cho_ngoi}`. Tôi mượn một lát." |
| SS-S19 | Màu áo | "Người đó đang `{cum_mau_ao}`. Tôi nhận ra từ xa." |
| SS-S20 | Màu áo | "Trong phòng có người `{cum_mau_ao}`. Tôi đã đi theo màu áo đó." |
| SS-S21 | Màu áo | "Tôi chọn người `{cum_mau_ao}`. Màu đó dễ tìm trong bóng tối." |
| SS-S22 | Màu áo | "Có người `{cum_mau_ao}`. Mai tôi cũng định mặc giống vậy." |
| SS-S23 | Màu áo | "Tôi chỉ nhớ một màu: người đó `{cum_mau_ao}`." |
| SS-S24 | Màu áo | "Người `{cum_mau_ao}` ơi, tôi ngồi sau bạn nãy giờ." |
| SS-S25 | Món trong túi | "Trong túi một người có `{mon_trong_tui}`. Tôi đã ngó qua." |
| SS-S26 | Món trong túi | "Tôi mượn `{mon_trong_tui}` của một người. Người đó chưa biết." |
| SS-S27 | Món trong túi | "Có người mang theo `{mon_trong_tui}`. Tôi nghe nó khẽ động." |
| SS-S28 | Món trong túi | "Người có `{mon_trong_tui}` trong túi ơi, cho tôi mượn một chút." |
| SS-S29 | Món trong túi | "Tôi biết trong túi ai có `{mon_trong_tui}`." |
| SS-S30 | Món trong túi | "Một người ở đây giữ `{mon_trong_tui}` rất kỹ. Tôi vẫn thấy." |

| ID | Câu kết |
|---|---|
| SS-K01 | "Tôi đã đến tìm người đó." |
| SS-K02 | "Tôi đã rủ người đó đi cùng." |
| SS-K03 | "Người đó giờ đi với tôi một lát." |
| SS-K04 | "Tôi đã gọi tên người đó, rất khẽ." |
| SS-K05 | "Người đó đã nghe thấy tôi." |
| SS-K06 | "Cảm ơn người đó đã cho tôi ngồi cùng." |

| ID | Câu nối (chi tiết thứ hai) — Lớp ma | Bật đèn |
|---|---|---|
| SS-N01 | "Người đó `{cum_bua_sang}` sáng nay." | "Anh chị đó `{cum_bua_sang}` sáng nay." |
| SS-N02 | "Người đó vừa `{cum_loai_nhac}`." | "Anh chị đó vừa `{cum_loai_nhac}`." |
| SS-N03 | "Người đó đang `{cum_cho_ngoi}`." | "Anh chị đó đang `{cum_cho_ngoi}`." |
| SS-N04 | "Người đó đang `{cum_mau_ao}`." | "Anh chị đó đang `{cum_mau_ao}`." |
| SS-N05 | "Trong túi người đó có `{mon_trong_tui}`." | "Trong túi anh chị đó có `{mon_trong_tui}`." |

Dòng biệt danh: "`{biet_danh}` giờ là Hồn."

### 6.3. Lời buổi sáng — Bật đèn (10 câu chi tiết + 5 câu kết)

| ID | Câu |
|---|---|
| SS-B01 | "Sáng nay em thấy một anh chị `{cum_bua_sang}`. Em ghi vào sổ tay rồi." |
| SS-B02 | "Em hỏi thăm được có người `{cum_loai_nhac}` lúc đi làm." |
| SS-B03 | "Người `{cum_cho_ngoi}` ơi, em là nhân viên mới ngồi gần đây ạ." |
| SS-B04 | "Em nhận ra người `{cum_mau_ao}` đầu tiên trong phòng." |
| SS-B05 | "Em mượn tạm `{mon_trong_tui}` của một anh chị, chiều em trả." |
| SS-B06 | "Em đang học tên cả phòng. Có người `{cum_bua_sang}`, em nhớ rồi." |
| SS-B07 | "Người `{cum_cho_ngoi}` chỉ việc cho em nhiệt tình lắm." |
| SS-B08 | "Em thấy người `{cum_mau_ao}` đi lấy nước lúc 9 giờ." |
| SS-B09 | "Có anh chị `{cum_loai_nhac}` cả buổi sáng, em nghe ké." |
| SS-B10 | "Trong túi một anh chị có `{mon_trong_tui}`, em để ý vì em cũng cần." |
| SS-BK1 | "Em xin phép mời người đó đi họp gấp với em." |
| SS-BK2 | "Người đó vừa được mời đi họp. Chắc lâu mới về." |
| SS-BK3 | "Em đã nhờ người đó dẫn đi một vòng công ty." |
| SS-BK4 | "Người đó đang bận hướng dẫn em, tạm vắng nhé." |
| SS-BK5 | "Người đó đi họp với em rồi ạ." |

Dòng biệt danh: "`{biet_danh}` đang đi họp."

### 6.4. Các câu khác của Người thứ N+1 (nháp)

| ID | Nhịp | Lớp ma | Bật đèn |
|---|---|---|---|
| SS-M01 | Mở màn | "Cảm ơn lớp đã cho tôi vào." | "Chào cả nhà, em là nhân viên mới. Hình như chưa ai nhớ đã tuyển em." |
| SS-M02 | Mở màn | "Sĩ số hôm nay: `{n_cong_1}`. Đủ rồi." | "Bảng chấm công hôm nay: `{n_cong_1}` người. Có em nữa." |
| SS-M03 | Đêm | "Đêm xuống. Ai cũng nhìn vào điện thoại của mình." | "Giờ nghỉ trưa. Ai cũng nhìn vào điện thoại của mình." |
| SS-M04 | Sáng không ai bị bắt | "Đêm qua tôi chỉ đi dạo. Không ai bị tìm." | "Trưa nay em ăn một mình. Không ai đi họp." |
| SS-M05 | Ngày | "Ai trong phòng đang giúp tôi? Các bạn có 90 giây." | "Ai đang chỉ việc cho em? Cả phòng có 90 giây." |
| SS-M06 | Trục xuất — Kẻ Bị Nhập | "`{biet_danh}` ra hành lang. Vai: Kẻ Bị Nhập. Tôi mất một người giúp." | "`{biet_danh}` đi công tác. Vai: Người Được Nhờ. Em mất một người chỉ việc." |
| SS-M07 | Trục xuất — không phải | "`{biet_danh}` ra hành lang. Vai: `{vai}`. Tôi cảm ơn lớp." | "`{biet_danh}` đi công tác. Vai: `{vai}`. Em cảm ơn cả phòng." |
| SS-M08 | Không trục xuất | "Lớp chưa thống nhất. Tôi ở lại thêm một đêm." | "Cả phòng chưa thống nhất. Em ở lại thêm một ngày." |
| SS-M09 | Bảng thư | "Có thư từ Hồn `{biet_danh}`: chữ `{chu}`." | "Người Đi Họp `{biet_danh}` nhắn về một chữ: `{chu}`." |
| SS-M10 | Akinator mở | "Hãy cùng nghĩ về một người trong phòng. Tôi sẽ nói tên người đó." | "Cả phòng nghĩ về một người nhé. Em đoán tên được." |
| SS-M11 | Akinator đúng | "Người các bạn đang nghĩ tới là… `{biet_danh}`." | "Người cả phòng đang nghĩ là… `{biet_danh}` đúng không ạ?" |
| SS-M12 | Akinator 2–3 người | "Tôi thấy `{so}` người: `{danh_sach}`. Một trong số đó đang trốn tôi." | "Em thấy `{so}` người: `{danh_sach}`. Em chưa chắc ạ." |
| SS-M13 | Akinator không khớp | "Không ai khớp cả. Lần này tôi chịu thua." | "Không ai khớp. Em xin thua ván này." |
| SS-M14 | Lật — thì thầm (mặc định) | "Tôi biết chuyện `{cum}` vì… một Kẻ Bị Nhập đã thì thầm." | "Em biết chuyện `{cum}` vì… một Người Được Nhờ đã kể cho em." |
| SS-M14b | Lật — thì thầm (người đó tự bật hiện tên) | "Tôi biết chuyện `{cum}` vì… `{biet_danh}` đã thì thầm." | "Em biết chuyện `{cum}` vì… `{biet_danh}` đã kể cho em." |
| SS-M15 | Lật — giải thích (bắt buộc) | "Không có con ma nào. Mọi điều tôi nói đều từ 5 câu các bạn tự trả lời lúc đầu. Kẻ Bị Nhập chọn câu nào để kể. Vòng đoán tên là một chuỗi câu hỏi có/không trên chính những câu trả lời đó." | "Không có nhân viên mới nào. Mọi điều em nói đều từ 5 câu cả phòng tự trả lời lúc đầu. Người Được Nhờ chọn câu nào để kể. Vòng đoán tên là một chuỗi câu hỏi có/không trên chính những câu trả lời đó." |
| SS-M16 | Lật — bản sao | "Còn tôi là ai? Tôi là cả lớp ghép lại." | "Còn em là ai? Em là cả phòng ghép lại." |
| SS-M17 | Người Sống thắng | "Lớp đã tìm ra hết người giúp tôi. Tôi xin phép ra về." | "Cả phòng tìm ra hết người chỉ việc cho em. Em xin nghỉ việc." |
| SS-M18 | Con ma thắng | "Tôi ở lại lớp này thêm một thời gian nữa." | "Em được nhận chính thức rồi ạ." |
| SS-M19 | Xoá sổ | "Xoá sổ điểm danh. Câu trả lời của mọi người được xoá ngay bây giờ." | "Xoá bảng chấm công. Câu trả lời của mọi người được xoá ngay bây giờ." |

## 7. Chỉ số

Chỉ số trong sản phẩm là số đếm tổng hợp theo ngày (hạ tầng phòng §6.3).

| Chỉ số | Cách đo | Mục tiêu |
|---|---|---|
| "Sao nó biết" / rút điện thoại quay | Quan sát chơi thử | ≥ 2 lần mỗi buổi |
| Người từng lên tiếng trong thảo luận | Quan sát chơi thử, tách theo quy mô | Theo dõi điểm nghẽn ở lớp đông |
| Tỷ lệ phòng tới màn giải thích | Số đếm | ≥ 90% |
| Host đặt buổi thứ hai / muốn làm host | Đếm lần bấm ở màn kết thúc | Theo dõi |
| Tỷ lệ chọn chế độ bật đèn | Số đếm theo bối cảnh | Theo dõi |
| Tỷ lệ chỉ xem | Số khán giả / tổng người vào | Cao bất thường = trò đáng sợ hoặc khó hiểu |
| Báo cáo khó chịu; câu khảo sát "bị nhắm vào hoặc sợ thật" | Số đếm | 0 |
| Akinator đoán đúng | Số lần ra 1 người khớp / số lần chơi | Theo dõi (không đo đúng/sai thật vì hệ thống không biết người được nghĩ tới) |

## 8. Phạm vi MVP và sau MVP

| MVP (khi giai đoạn 3 mở) | Sau MVP |
|---|---|
| Màn hình host, chia vai, pha đêm và ngày, khoảng 60 câu thoại theo mẫu (bản nháp ở §6 có 51 câu buổi sáng + 19 câu khác), Akinator bằng cây quyết định, Hồn gửi chữ, màn lật, chế độ bật đèn, xoá sổ điểm danh | Giọng nói chạy vòng quanh phòng (đồng bộ âm thanh giữa máy rất khó — báo cáo) |
| Dãy bàn cho lớp 25–50 | Cốt truyện nhiều tập "Người thứ 31 là ai?" — mỗi buổi mở một mảnh; cần thiết kế riêng để không thành "tin nhắn dây chuyền" và không lưu dữ liệu người chơi qua buổi |
| Câu khảo sát cuối buổi | "Lớp bên cạnh cũng điểm danh ra +1" (lây sang lớp khác) — rủi ro hoảng loạn đạo đức cao nhất; chỉ xem xét sau khi có dữ liệu an toàn |
| | Cầu nối lá The Moon về Lá Lành (link thường, đồng ý riêng, không mang dữ liệu game) |
| | Bản lớp phổ thông (giáo viên host, học sinh không tài khoản) |

Trước MVP: **chơi thử giấy** với một lớp đại học khoảng 30 người. Host đóng vai con ma, đọc lời thoại từ slide; Kẻ Bị Nhập nhắn riêng cho
host; phiếu khai báo chỉ ghi số thứ tự, xé tại chỗ cuối buổi; khảo sát ba câu có câu "có lúc nào bạn thấy bị nhắm vào hoặc sợ thật
không" (báo cáo; Writer F lo bộ chơi thử).

## 9. Rủi ro và giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| **Hoảng loạn đạo đức** (kiểu Momo): báo chí, nhà trường, phụ huynh coi trò ma là nguy hiểm dù không có tác hại | Cao | Không tin nhắn dây chuyền, không thử thách ngoài đời, không thông báo sau buổi, không "tập sau" ở MVP; luôn giải thích cơ chế; ra mắt 18+; không đề cập tự hại hay cái chết; câu chữ được owner duyệt |
| **Sợ thật** (người sợ ma, người từng trải qua mất mát) | Trung bình–cao | Cảnh báo nội dung ở màn vào phòng của chế độ Lớp ma; chỉ xem luôn có; chế độ bật đèn; không jump scare, không âm thanh đột ngột lớn, không nhấp nháy (WCAG 2.3.1); không tắt đèn phòng |
| **Bị nhắm vào** (một người bị bắt hay bị nghi liên tục) | Trung bình | 3 ứng viên ngẫu nhiên ưu tiên người ít được đưa vào; không ai bị bắt hai lần; Hồn còn quyền; trục xuất chỉ lật vai |
| **Tín ngưỡng dân gian** ("bị nhập", "thầy pháp") chạm nhóm chủ đề tôn giáo | Trung bình | Không nghi lễ, biểu tượng hay tên gọi của tôn giáo thật; chế độ bật đèn đổi hết tên; cần kiểm Nghị định 147/2024 về nội dung mê tín (chưa kiểm — research note risks §3 Gaps) |
| **Clip màn chiếu lan truyền** kèm biệt danh và câu trả lời | Trung bình | Lời đồng ý nói rõ; câu trả lời vô hại; không thẻ chia sẻ ở MVP |
| Hồn nói thẳng tên Kẻ Bị Nhập | Thấp (luật chơi) | Luật "Hồn chỉ nói bằng chữ" hiện trên thẻ Hồn; host nhắc; cân bằng qua chơi thử (SS-D4) |
| Văn phòng: nhân viên thấy bị ép chơi trò ma | Trung bình | Bật đèn mặc định; chuyển sang Lớp ma cần host xác nhận cả phòng đồng ý (SS-D9) |
| Người dưới 18 lọt vào (lớp đại học năm nhất 17 tuổi) | Thấp–trung bình | Xác nhận 18+ (tự khai); host được hướng dẫn chỉ tổ chức cho 18+; không thu dữ liệu tuổi |
| Giấy phép G1 (Nghị định 147/2024) | Chưa rõ | Counsel |
| Cân bằng thắng thua lệch | Trung bình | Bảng tham số SS-D2; chơi thử |

## 10. Dữ liệu và quyền riêng tư (tóm tắt; chi tiết ở SRS §7)

Theo hợp đồng dữ liệu chung: biệt danh, định danh phiên gắn thiết bị, 5 câu trả lời chọn sẵn, cờ đồng ý "câu trả lời có thể hiện trên
màn hình chung" (không tick sẵn), vai và dãy bàn, phiếu (gồm lượt chọn bí mật của Kẻ Bị Nhập, Thầy Pháp, Hồn), **lời thì thầm** (Kẻ Bị
Nhập nào chọn câu trả lời nào của ai), dấu thời gian. Xoá khi buổi kết thúc, chậm nhất 2 giờ sau khi bắt đầu. Bản sao ghép chỉ dùng số
đếm. Việc giả ban đêm không được lưu. Không ngày sinh, không dữ liệu chiêm tinh; lá The Moon là hình tĩnh.

## 11. Quyết định chờ owner

| ID | Câu hỏi | Đề xuất — chờ owner |
|---|---|---|
| D6 (chung) | Văn phòng mặc định "bật đèn" | Có |
| D7 (chung) | AI làm con ma ở MVP | Không |
| SS-D1 | Số người tối thiểu | 15 |
| SS-D2 | Tham số cân bằng: số Kẻ Bị Nhập, số người bị bắt mỗi đêm, số vòng mặc định, luật hết vòng | Như §4.2 và §5.2 (SRS SS-FR-05, SS-FR-21, SS-FR-70–73; bộ chơi thử giấy P10 dùng cùng bộ); chơi thử chỉnh |
| SS-D3 | Buổi sáng có hiện biệt danh người bị bắt | Có, sau câu kết 3 giây |
| SS-D4 | Hồn gửi chữ trong biệt danh của Kẻ Bị Nhập nào | Một Kẻ Bị Nhập ngẫu nhiên còn trong cuộc (không cho Hồn biết ai đã chọn mình, để không lộ "ai chọn ai" — DPIA R10) |
| SS-D5 | Ai trả lời câu hỏi Akinator | Mọi điện thoại trong phòng (người chơi, Hồn, hành lang, khán giả), theo đa số |
| SS-D6 | Người bị trục xuất làm gì | "Ngoài Hành Lang": không bỏ phiếu trục xuất, vẫn có việc ban đêm, đoán không tính, chơi Akinator |
| SS-D7 | Kẻ Bị Nhập có biết đồng bọn | Có |
| SS-D8 | Cầu nối lá The Moon ở MVP | Sau MVP |
| SS-D10 | Màn lật có nêu biệt danh người đã thì thầm không | Mặc định không: "một Kẻ Bị Nhập đã thì thầm"; chỉ nêu khi Kẻ Bị Nhập đó tự bật "Hiện tên tôi" lúc lật (DPIA DP-1). Báo cáo gốc nêu tên |
| SS-D9 | Văn phòng chuyển sang Lớp ma được không | Được, nếu host tick "Mọi người trong phòng đã biết đây là bản rợn nhẹ và đồng ý chơi" (không tick sẵn) |

## 12. Bàn giao cho user story

| Story | Nội dung | Dựa vào hạ tầng |
|---|---|---|
| [G41](../../user-stories/game/G41-mo-man-diem-danh-n-cong-1.md) | Chọn bối cảnh và chế độ, cảnh báo nội dung, mở màn N+1 | G01, G02 |
| [G42](../../user-stories/game/G42-nhan-vai-va-pha-dem.md) | Chia vai, dãy bàn, pha đêm (việc giả, 3 ứng viên, thì thầm, Thầy Pháp, Hồn chọn chữ) | G03, G04, G05 |
| [G43](../../user-stories/game/G43-buoi-sang-nguoi-thu-n-cong-1-noi.md) | Lời buổi sáng, Hồn, kết quả Thầy Pháp | — |
| [G44](../../user-stories/game/G44-ban-ngay-day-ban-va-truc-xuat.md) | Thảo luận, dãy bàn, bỏ phiếu trục xuất, thắng thua | G05 |
| [G45](../../user-stories/game/G45-hon-gui-chu-cai.md) | Hồn và bảng thư | G05 |
| [G46](../../user-stories/game/G46-vong-akinator.md) | Khoảnh khắc Akinator bằng cây quyết định | G05 |
| [G47](../../user-stories/game/G47-lat-mat-ban-sao-ghep-va-xoa-so.md) | Lật mặt, giải thích cơ chế, bản sao ghép, xoá sổ | G07, G08 |

## 13. Bàn giao theo AGENTS.md

**Nguồn đã kiểm tra:** báo cáo "Chốt năm trò, giữ trọn chữ Lành" (toàn văn, nhất là mục Sĩ Số +1); research note
`comedy_courtroom_formats.md` §1, §5; `risks_privacy_policy.md` §1–§5; brief chung 26/10/2026; `AGENTS.md`; chuẩn nội dung tiếng Việt dễ
hiểu; kế hoạch 23/10/2026. Apple App Review Guidelines 1.1.1 và 1.2 đọc lại 26/10/2026. Luật 91/2025, Nghị định 356/2025, Nghị định
147/2024 (kể cả quy định về nội dung mê tín) **chưa** được đối chiếu nguyên văn trong lượt này.

**Phát hiện đã xử lý:** con ma chỉ dùng câu đã đồng ý, không dùng "Không muốn nói"; bản sao ghép chỉ số đếm và ẩn phương án có dưới 3
người (SRS, DPIA KS-04); màn lật mặc định không nêu ai đã thì thầm (SS-D10); Hồn không được biết ai đã chọn mình (SS-D4); việc giả ban đêm không lưu; Hồn và người bị trục xuất đều còn việc; không yêu cầu tắt đèn phòng; mạch dài và "lây sang lớp
khác" bị giữ ngoài MVP vì gần nhất với kiểu tin nhắn dây chuyền; tên vai đổi hết ở chế độ bật đèn để bớt màu tín ngưỡng.

**Rủi ro chưa giải quyết:** cân bằng (SS-D2) chưa chơi thử; Nghị định 147/2024 về nội dung mê tín; G1; Hồn tự nói tên; tâm lý người từng
mất mát với chủ đề ma (chỉ giảm bằng cảnh báo và chỉ xem).

**AC/DoD chưa hoàn tất:** toàn bộ. Chưa chơi thử giấy; ngân hàng câu chưa được owner duyệt; chưa có DPIA duyệt, nhãn cửa hàng, chính sách
quyền riêng tư, ý kiến counsel.
