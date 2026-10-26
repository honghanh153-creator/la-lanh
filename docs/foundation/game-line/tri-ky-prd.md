# Lá Lành — PRD "Tri Kỷ" (lá đôi đồng ý hai chiều + trò đố "Hiểu Nhau Không?")

> Phiên bản: 0.1 (nháp) · Viết: 26/10/2026 · Trạng thái: **chờ chủ sản phẩm duyệt**, chưa được duyệt để triển khai.
> Giai đoạn: chỉ tài liệu. Theo kế hoạch 23/10/2026 (`docs/plans/2026-10-23-privacy-content-game-plan.md`), thứ tự là riêng tư → nội dung → game. Tri Kỷ dùng dữ liệu sinh của hai người nên **đi theo lịch của giai đoạn riêng tư**, không chờ giai đoạn game, nhưng **không viết code** cho tới khi tiêu chí thoát giai đoạn 1 đạt và owner duyệt PRD/SRS này.
> Tài liệu đi kèm: SRS [`tri-ky-srs.md`](tri-ky-srs.md); user story [`G50`–`G55`](../../user-stories/game/). Nguồn thiết kế: báo cáo "Chốt năm trò, giữ trọn chữ Lành" (26/10/2026, mục Tri Kỷ) và ghi chú `research_notes/Chốt trò chơi nhóm Lá Lành/tri_ky_friendship_ranking.md` (ngoài git, trên máy chủ sản phẩm).
> PRD này **không** thay đổi AC của US-01 đến US-22. Những chỗ cần sửa ở tài liệu khác được liệt kê ở §13 để làm bằng PR riêng.

---

## 0. Tóm tắt một đoạn

A mở **Tri Kỷ** trong Lá Lành và gửi một lời mời riêng cho đúng một người qua bảng chia sẻ của điện thoại. B mở link, thấy ai mời và hai bên sẽ thấy gì, rồi **tự dùng hồ sơ Lá Lành của chính mình** (hoặc tự tạo hồ sơ) và tick một ô đồng ý riêng. Chỉ khi cả hai đã đồng ý, hệ thống mới dựng **lá đôi**: "Điều hai bạn chung", "Cách hai bạn bù nhau", "Một việc nhỏ để thử" và một **nhãn kiểu đồng điệu** (không có phần trăm, không có điểm). Lá chỉ hai người thấy. Muốn chia sẻ ảnh lá ra ngoài thì cả hai phải cùng bấm đồng ý. Bất kỳ ai cũng giải tán lá được một cách im lặng: lá biến mất, dữ liệu cặp bị xoá, người kia không nhận thông báo. Sau MVP, cặp có thể chơi **Hiểu Nhau Không?**: 7 câu vô hại, mỗi người trả lời cho mình và đoán câu của người kia, kết quả "x/7" chỉ hai người thấy, và cặp chỉ thi với **kỷ lục của chính mình**.

### 0.1. Thước đo (bản chất Lá Lành, chủ sản phẩm 22/10/2026)

> Lá Lành là nơi tìm được những giây phút thư giãn bình yên, vui vẻ, những khoảnh khắc giúp bạn cảm giác được hiểu.

"Tri kỷ" nghĩa gốc là **người hiểu mình**. Tính năng phục vụ phần "cảm giác được hiểu" bằng một khoảnh khắc chung của hai người, và phục vụ phần "vui vẻ" bằng trò đố tự thi với chính cặp mình. Nó không được đổi phần "bình yên" lấy tăng trưởng: không xếp hạng người, không "ai chọn bạn", không nhắc quay lại.

## 1. Bối cảnh và bằng chứng

### 1.1. Vì sao không làm "Crush leaderboard" dưới bất kỳ tên nào

Ideation 28/09/2026 đã loại "Crush leaderboard". Báo cáo 26/10/2026 xác nhận lý do không nằm ở chữ "crush" mà ở **bảng xếp hạng người**:

| Ca | Chuyện gì xảy ra | Bài học cho Tri Kỷ |
|---|---|---|
| Snapchat Best Friends (2015) | Bỏ danh sách công khai, sau đó chỉ người dùng tự thấy | Kết quả về quan hệ chỉ người trong cuộc thấy |
| Snapchat+ Friend Solar System (tắt mặc định 05/04/2024) | Thiếu niên đau lòng khi biết mình "kém thân" hơn mình tưởng; Snap thừa nhận biết mình không thân bằng mong muốn có thể gây buồn (TechCrunch 05/04/2024; Axios 06/04/2024) | Cái gây hại là **bất đối xứng** (A thấy B xếp mình thấp) và **bị nhìn thấy** (người thứ ba thấy). Không xếp hạng, không so cặp này với cặp khác |
| Gas / tbh (2017–2023) | Bình chọn về bạn cùng lớp tăng rất nhanh rồi chết nhanh; Discord đóng Gas 07/11/2023 | Không xây tăng trưởng trên bình chọn về người thật; không đề cử ẩn danh |
| NGL (FTC 2024) | 5 triệu USD; bán gói "xem ai gửi" không có thật; gửi tin giả như từ bạn bè; cấm nhắn ẩn danh cho người dưới 18 | Không "ai đã chọn bạn", không thu phí để biết, không tin nhắn giả, không ẩn danh |
| Nesi & Prinstein (n=619, thiếu niên) | So sánh xã hội và tìm phản hồi qua công nghệ dự báo triệu chứng trầm cảm một năm sau | Không biến tình bạn thành con số để so |

Bằng chứng chủ yếu về thiếu niên. Chưa tìm được nghiên cứu cho người trưởng thành. Ở lớp đại học và văn phòng còn thêm thứ bậc (ai xếp sếp ở đâu, ai bị bỏ ra ngoài), nên Tri Kỷ ra mắt cho 18+ vẫn giữ nguyên các lằn ranh trên.

### 1.2. Mô hình an toàn đã có tiền lệ

- **Spotify Blend**: A mời B, chỉ khi B chấp nhận mới tạo playlist chung; phần lật cốt lõi miễn phí. Blend có hiện "taste match %". **Tri Kỷ cố ý không theo điểm này** (§4, D5).
- **Co-Star**: chỉ xem độ hợp giữa hai người đã kết bạn với nhau.
- Snapchat sau 2015 và 2024: chỉ mình thấy, tự bật.

### 1.3. Nền chính sách (đã kiểm ngày 26/10/2026)

- **Apple App Review Guidelines** (trang hiện hành, đọc trực tiếp 26/10/2026; trang không ghi ngày sửa):
  - 5.1.1(viii): không cho phép app tổng hợp thông tin cá nhân không lấy trực tiếp từ người dùng hoặc không có đồng ý rõ ràng của họ. Một lá tính cho người chưa tham gia vi phạm đúng điều này. Đây là lý do **chặn lối "Check kín" của US-12 cho Tri Kỷ**.
  - 1.2: app có nội dung do người dùng tạo phải có lọc, báo cáo, chặn và thông tin liên hệ công khai; app dùng chủ yếu cho chat ngẫu nhiên/ẩn danh, "objectification of real people (such as 'hot-or-not' voting)" hoặc bắt nạt có thể bị gỡ không báo trước. Tri Kỷ chỉ có một trường chữ do người dùng tạo (tên hiển thị) nhưng vẫn có báo cáo và chặn.
  - 5.1.2(v): chỉ liên hệ người trong danh bạ khi người dùng chủ động, từng người một, không "Chọn tất cả", và phải cho thấy tin nhắn sẽ hiện thế nào với người nhận.
  - 1.1.6: ghi "để giải trí" không giúp vượt quy định về thông tin sai.
- **Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15** (hiệu lực 01/01/2026) và **Nghị định 356/2025/NĐ-CP** (hiệu lực 01/01/2026, thay Nghị định 13/2023). Danh mục dữ liệu nhạy cảm có "Thông tin về đời sống riêng tư, bí mật cá nhân, bí mật gia đình" và "Dữ liệu tiết lộ đời sống tình dục, xu hướng tình dục", kèm mục mở "dữ liệu cá nhân khác được pháp luật quy định cần giữ bí mật…" (đối chiếu trang phổ biến pháp luật của Sở Tư pháp Cần Thơ, pbgdpl.cantho.gov.vn, 26/10/2026; chưa đọc bản .doc gốc trên vbpl.moj.gov.vn). Văn bản **không nói rõ** dữ liệu suy luận có thuộc nhóm nhạy cảm không, nên PRD **mặc định coi lá đôi là dữ liệu nhạy cảm (đời sống riêng tư)** cho tới khi luật sư trả lời (§12, Q-L1).
  - Ghi chú nghiên cứu nêu: im lặng không phải đồng ý, đồng ý phải tách theo từng mục đích, cấm ô tick sẵn và giao diện làm mờ ranh giới đồng ý/từ chối. Đây là kết luận qua nguồn thứ cấp; luật sư xác nhận nguyên văn.
- **Hosting**: Hetzner (Đức) và Supabase (Frankfurt) như hiện tại; hồ sơ chuyển dữ liệu ra nước ngoài thuộc dossier #52 (`docs/legal/2026-10-22-privacy-counsel-dossier.md`). Tri Kỷ không thêm nhà cung cấp nào.

### 1.4. Repo đã có hai đường ray đúng mô hình này

| Đường ray | Tài liệu | Trạng thái runtime 26/10/2026 | Tri Kỷ dùng gì |
|---|---|---|---|
| Lời mời Lá Chứng | US-08, US-09 | Hợp đồng đầy đủ; code tạo mới đang **tắt** (`la_chung_accepting_new_activity=False`) | **Hợp đồng** capability link: token ngẫu nhiên, lưu hash, bản mã hoá tạm để gửi lại, hạn 7 ngày, thu hồi, idempotency, bảng chia sẻ hệ điều hành từng người, không tải danh bạ, không suy ra "đã gửi" |
| Radar Hợp gu ngữ cảnh `friend`, mode `consented_invite` | US-13, `la-lanh-radar-hop-gu-spec.md` | Đang chạy | **Mẫu runtime**: B dùng hồ sơ của chính mình, đồng ý riêng theo mục đích, server tính hai chart từ hồ sơ mã hoá, lưu kết quả rút gọn đã mã hoá, header công khai an toàn, quyền của B theo phiên (P09 D2), `scalar_score_eligible=false` |

Chi tiết cái gì dùng lại, cái gì mới nằm ở SRS §3.

## 2. Mục tiêu, phi mục tiêu và nguyên tắc

### 2.1. Mục tiêu

1. Cho hai người đã quen nhau một khoảnh khắc "được hiểu" chung, dựa trên lá số của cả hai, mà **cả hai cùng đồng ý trực tiếp** bằng hồ sơ của chính mình.
2. Giữ cái vui của "so sánh" mà không xếp hạng người: so với **kỷ lục của chính cặp mình** (Hiểu Nhau Không?, sau MVP).
3. Là đường giới thiệu 1:1 có ý định cao nhất vào Lá Lành: B tạo hồ sơ vì một người bạn thật mời, không vì quảng cáo.
4. Là ví dụ chuẩn cho cách Lá Lành xử lý **dữ liệu suy luận về hai người**: đồng ý từng người, từng mục đích, xoá đối xứng, không lọt vào analytics, thông báo hay xem trước link.

### 2.2. Phi mục tiêu (không làm ở bất kỳ phiên bản nào)

- Danh sách "top tri kỷ", thứ tự tri kỷ, đếm "bạn có bao nhiêu tri kỷ" hiển thị cho người khác.
- Tính năng "ai đã chọn bạn", đề cử ẩn danh, thu phí để xem ai chọn mình.
- Phần trăm hợp, điểm tổng, ba chỉ báo 0–100 của Radar, thang xếp hạng nhãn.
- Khung lãng mạn: "crush", "nửa kia", "soulmate", "người yêu", hẹn hò, rung động, thả thính, định mệnh.
- Tính lá cho người chưa đồng ý; A nhập thông tin sinh của B; lối "Check kín" (US-12) cho Tri Kỷ.
- Bản đồ cặp công khai, đồ thị quan hệ của lớp/nhóm ("Class compatibility map" đã bị loại ở ideation).
- Gợi ý người để mời, tải danh bạ, tự mời, mời hàng loạt, server tự gửi SMS/email.
- Chat, tin nhắn tự do, nhắn ẩn danh, ảnh, giọng nói.
- Streak, coin/XP, đếm ngày, nhắc quay lại, đếm ngược (nguyên tắc có test: `apps/web/src/shared/ui/companion/growth.test.ts`).
- Gửi dữ liệu Tri Kỷ cho nhà cung cấp AI (Luna) ở MVP.
- Phiên bản cho người dưới 18 tuổi.

### 2.3. Nguyên tắc thiết kế

| # | Nguyên tắc | Kiểm thế nào |
|---|---|---|
| N1 | **Một cặp, một lá.** Không danh sách xếp hạng; danh sách cặp chỉ sắp theo thời gian tạo | Test thứ tự danh sách; không có trường nhãn/điểm trong danh sách |
| N2 | **Hai người cùng đồng ý trực tiếp.** Mỗi người dùng hồ sơ của mình, tick ô đồng ý riêng không tick sẵn | API từ chối mọi payload có trường sinh của người khác; ô đồng ý mặc định trống |
| N3 | **Không con số dự đoán.** Nhãn là kiểu, không phải bậc. Con số duy nhất là "x/7" của trò đố, vì đó là đếm câu đoán đúng, không phải tiên đoán (D5) | Test schema: projection lá đôi không có trường số |
| N4 | **Chỉ hai người thấy.** Không analytics nội dung, không nội dung trong thông báo đẩy, không link chia sẻ có xem trước | Canary log/analytics; test nội dung push cố định |
| N5 | **Rời đi im lặng và đối xứng.** Ai cũng giải tán được, không ai bị báo "bạn đã bị xoá", không lộ ai giải tán | Màn trạng thái cuối giống hệt nhau cho mọi nguyên nhân |
| N6 | **Không áp lực quay lại.** Không nhắc, không đếm ngày, không "đã lâu rồi" | Rà copy + test không có bộ đếm |
| N7 | **Thân, không yêu đương.** Ngữ cảnh cố định `friend`; gate chặn từ vựng lãng mạn; bỏ chủ đề `attraction` của Radar | Gate từ vựng và test projection |

## 3. Người dùng, lối vào và phạm vi

### 3.1. Persona (18+)

| Persona | Bối cảnh | Muốn gì | Rủi ro cần chặn |
|---|---|---|---|
| **Linh, 21**, sinh viên năm 3 ở TP.HCM, đã dùng Note hôm nay | Có một cạ cứng từ cấp 3, hai đứa hay gửi nhau trắc nghiệm vui | Một thứ để gửi cho riêng bạn ấy, đọc xong thấy "đúng hai đứa mình" | Lá bị hiểu là chuyện yêu đương; bạn ấy chưa có Lá Lành và phải khai ngày sinh |
| **Minh, 27**, nhân viên văn phòng ở Hà Nội | Thân với một đồng nghiệp cùng nhóm | Một lời mời nhẹ, không ai khác trong nhóm thấy | Bị dùng để so ai thân với sếp hơn; ảnh chia sẻ lộ trong nhóm chat công ty |
| **B (người được mời)**, 18+, có thể chưa có Lá Lành | Nhận link từ một người quen | Biết rõ mình phải đưa gì, ai thấy gì, rút ra thế nào | Bị ép đồng ý; link bị chuyển tiếp tới nhầm người |

Người dưới 18 tuổi không dùng được Tri Kỷ (cả người mời và người nhận). Kiểm theo ngày sinh trong hồ sơ của chính người đó; đây không phải xác minh tuổi mạnh (xem rủi ro R7).

### 3.2. Lối vào

- Tab/khu Hợp gu: thẻ "Tri Kỷ" cạnh Radar, tách biệt rõ với "Check kín".
- Không có lối vào từ thông báo đẩy, không có thẻ "mời thêm người" chen vào Home.
- B vào từ link mời (universal/app link; web companion nếu chưa cài app).

### 3.3. Phạm vi theo phiên bản

| Hạng mục | MVP (sau giai đoạn riêng tư) | Sau MVP | Không bao giờ |
|---|---|---|---|
| Lời mời từng người qua bảng chia sẻ, thu hồi, gửi lại, hết hạn | Có (G50) | | Mời hàng loạt, danh bạ |
| B nhận bằng hồ sơ của mình + đồng ý riêng; chặn/báo cáo người mời | Có (G51) | | Check kín |
| Lá đôi: ba khối nội dung + nhãn kiểu đồng điệu | Có (G52) | Đổi "việc nhỏ để thử" theo tuần (không nhắc) | % hoặc điểm |
| Lá tarot của hai đứa | | Có, sau khi owner duyệt copy | |
| Chia sẻ ảnh khi cả hai đồng ý | Có (G53) | | Link công khai có xem trước |
| Giải tán im lặng, xoá cứng | Có (G54) | | Thông báo "bạn đã bị xoá" |
| Hiểu Nhau Không? (x/7, kỷ lục của cặp) | | Có (G55), sau khi copy và ngân hàng câu được duyệt | So với cặp khác |
| Giọng Cà khịa | | Có, sau khi owner duyệt câu mới | |
| Bản tóm tắt riêng "Tháng này bạn đã đọc vía cùng 3 người" | | Cân nhắc, không thứ tự | Thứ tự người |
| Con số chung của hội trong sự kiện phòng ("68%") | | **Không** trong Tri Kỷ; nếu làm ở Lá Úp phải qua D5 vì đó là một phần trăm | |
| Luna viết lại lá đôi | | Chỉ khi có mục đích, đồng ý và gate riêng | |

## 4. Luật chốt

Bảng dưới là luật sản phẩm. Phần kỹ thuật ở SRS.

| Bước | Diễn biến | Luật |
|---|---|---|
| 1 | A mở Tri Kỷ. Màn giới thiệu: người hiểu mình, không yêu đương, không xếp hạng, chỉ hai người thấy, rời đi lúc nào cũng được | Không danh sách gợi ý người. A cần hồ sơ ngày sinh (Level 1 trở lên, đề xuất TK-1) và đăng nhập khi tạo link (đề xuất TK-2) |
| 2 | A chọn tên hiển thị B sẽ thấy, đọc trước đúng màn B sẽ thấy, đọc câu báo dữ liệu nhạy cảm ngay trên ô, tick ô đồng ý của mình (`tri-ky-pair-v1`) rồi tạo link | A cũng là chủ thể dữ liệu của lá đôi nên A cũng phải đồng ý. Ô không tick sẵn. Câu "dữ liệu nhạy cảm" nằm ngay trên ô, không chỉ trong chính sách |
| 3 | A gửi link qua bảng chia sẻ hệ điều hành, mỗi lần một người | Link hạn 7 ngày, dùng một lần, thu hồi được, không chứa định danh hay dữ liệu sinh. Không ghi "đã gửi/đã đọc" |
| 4 | B mở link: thấy tên A chọn, hai bên sẽ thấy gì, mình phải đưa gì, rút ra thế nào | Xem trước không tạo sự kiện theo dõi. B không phải đăng nhập để xem |
| 5 | B dùng hồ sơ Lá Lành của mình, hoặc tự tạo hồ sơ (US-01/US-02 với đồng ý hồ sơ riêng), đọc câu báo dữ liệu nhạy cảm ngay trên ô, rồi tick ô đồng ý riêng: "Dùng hồ sơ sinh của tôi để dựng lá Tri Kỷ với [tên A]" và chọn tên hiển thị của mình | Không ai nhập hộ ai. B phải 18+. Câu "dữ liệu nhạy cảm" nằm ngay trên ô của B như ở màn của A. B có nút "Không nhận", "Báo cáo", "Không nhận lời mời Tri Kỷ từ người này nữa" |
| 6 | Hệ thống dựng lá đôi và hiện cho cả hai: ba khối nội dung + nhãn kiểu đồng điệu | Không %, không điểm, không chỉ báo 0–100. Nhãn là một trong ba **kiểu** ngang hàng, không phải bậc. Lá đóng băng nội dung lúc dựng |
| 7 | Chia sẻ ảnh lá chỉ khi cả hai cùng bấm đồng ý cho đúng ảnh đó | Ảnh có tên hiển thị, nhãn kiểu và một câu chung; không ngày sinh, không cung, không nguyên tố. Không tạo link công khai. Người kia không bấm thì yêu cầu tự hết hạn, không có thông báo "bị từ chối". Yêu cầu chia sẻ (hàng vận hành) xoá 7 ngày sau khi kết thúc; mỗi lần đồng ý để lại một bằng chứng tối thiểu (ai, lúc nào, bản câu chữ, bản ảnh; không có ảnh), giữ khi lá còn, xoá khi giải tán (SRS FR-TK-067). Có phải giữ bằng chứng lâu hơn không: chờ counsel (Q-L7) |
| 8 | Ai cũng giải tán lá được, im lặng | Xoá cứng lá, yêu cầu chia sẻ, bằng chứng đồng ý chia sẻ, dữ liệu trò đố. Người kia chỉ thấy lá không còn, giống mọi trường hợp lá không còn khác |
| 9 (sau MVP) | Hiểu Nhau Không?: 7 câu vô hại, mỗi người trả lời cho mình và đoán câu của người kia, khi nào rảnh thì chơi | Đồng ý riêng `tri-ky-quiz-v1`. Kết quả là điểm chung của cặp "x/7", chỉ hai người thấy, không có điểm riêng từng người. Câu trả lời gắn với cặp nên được xử lý như **dữ liệu nhạy cảm**; bị xoá ngay khi cả hai đã xem kết quả, muộn nhất 7 ngày sau khi lượt xong. Sau đó chỉ còn kỷ lục x/7 (và tháng) của cặp, giữ khi cặp còn; giải tán xoá hết |

**Ba kiểu đồng điệu (đề xuất, chờ owner duyệt và kiểm chữ):**

| Mã | Nhãn | Khi nào | Giải thích một dòng |
|---|---|---|---|
| `deep` | Đồng điệu sâu | Bằng chứng trùng hướng chiếm ưu thế | Hai bạn hay nhìn một chuyện từ cùng một phía. |
| `complementary` | Đồng điệu kiểu bù trừ | Bằng chứng khác hướng nhưng bổ sung chiếm ưu thế | Hai bạn khác nhau ở đúng chỗ người kia cần. |
| `opening` | Đồng điệu đang mở | Ít bằng chứng đủ rõ (gồm cả trường hợp chỉ có ngày sinh) | Lá chưa thấy nhiều, phần còn lại để hai bạn tự khám phá. |

Ba nhãn có cùng trọng lượng hình ảnh, không màu "tốt/xấu", không sắp thành thang. Kiểm chữ với 5–10 người phải xác nhận không nhãn nào nghe như bị từ chối; nhãn nào trượt thì đổi trước khi build (R2).

**Cách nói sự bù trừ:** theo dải mềm, không bao giờ bằng con số. Ví dụ (nháp): "Lửa và Khí: một người hay mở đầu, một người giúp việc đi tới cùng." Báo cáo gốc viết "một người giữ nhịp", nhưng "giữ nhịp" nằm trong danh sách cụm từ không dùng của chuẩn nội dung, nên đã đổi.

## 5. Copy nháp (tất cả **chờ owner duyệt**)

Giọng direct theo `la-lanh-plain-vietnamese-content-standard.md`. Có thể dùng "cạ cứng", "đồng điệu" cho câu phụ; không dùng "crush", "nửa kia", "soulmate". Hạn chế tiếng Anh; "bestie" không dùng ở MVP. Mọi câu dưới đây là nháp để owner duyệt qua file Excel như các đợt trước, chưa được đưa cho người dùng thật.

| Chỗ | Nháp |
|---|---|
| Tên tính năng | Tri Kỷ |
| Câu giới thiệu | Tri kỷ là người hiểu mình. Xem hai bạn đồng điệu ở đâu, chỉ hai bạn thấy. |
| Dòng chặn hiểu sai (luôn hiện ở màn giới thiệu và trên lá) | Tri Kỷ nói về tình bạn, không phải chuyện yêu đương. Không có bảng xếp hạng. |
| Ba bước | Bạn gửi lời mời cho một người → người ấy dùng hồ sơ Lá Lành của họ và đồng ý → hai bạn cùng mở lá đôi. |
| Riêng tư (trước nút tạo link) | Lá đôi chỉ hai bạn thấy. Không ai nhập ngày sinh hộ ai. Ai cũng giải tán được, lúc nào cũng được. |
| Câu báo dữ liệu nhạy cảm (đặt **ngay trên** ô đồng ý của A và ô đồng ý của B, không xen nội dung khác) | Lá đôi là dữ liệu nhạy cảm vì nó nói về đời sống riêng tư của hai bạn. Lá Lành chỉ tạo khi cả hai cùng đồng ý, và chỉ hai bạn xem được. *(nháp, chờ owner duyệt; counsel xem có đủ cho Nghị định 356 Điều 6 khoản 4 không, Q-L1)* |
| Ô đồng ý của A | Dùng hồ sơ sinh của tôi để dựng lá Tri Kỷ với người nhận lời mời này. Tôi hiểu lá đôi là thông tin riêng tư về hai chúng tôi và chỉ hai người thấy. |
| Nút | Tạo link riêng |
| Sau khi tạo | Link đã sẵn sàng. Link dùng được một lần, trong 7 ngày. |
| Cảnh báo sao chép | Ai có link này đều mở được lời mời. Chỉ gửi cho người bạn muốn mời. |
| Màn của B (link hợp lệ) | [Tên A] mời bạn mở một lá Tri Kỷ. |
| B sẽ đưa gì | Bạn dùng hồ sơ Lá Lành của chính bạn. Chưa có thì bạn tự tạo, khoảng 1 phút. [Tên A] không thấy ngày sinh của bạn. |
| Hai bên thấy gì | Hai bạn cùng thấy một lá đôi: điều chung, cách bù nhau và một việc nhỏ để thử. Không có phần trăm hay điểm số. |
| Ô đồng ý của B | Dùng hồ sơ sinh của tôi để dựng lá Tri Kỷ với [tên A]. Tôi hiểu lá đôi là thông tin riêng tư về hai chúng tôi và chỉ hai người thấy. |
| Nút của B | Đồng ý và mở lá · Không nhận |
| Lối an toàn của B | Báo cáo lời mời · Không nhận lời mời Tri Kỷ từ người này nữa |
| Link chuyển tiếp | Chỉ nhận nếu lời mời này dành cho bạn. |
| Link hết hạn / thu hồi / đã dùng / sai | Lời mời này không còn mở được. Nếu cần, nhờ người gửi tạo link mới. |
| Ba khối | Điều hai bạn chung · Cách hai bạn bù nhau · Một việc nhỏ để thử |
| Disclaimer (ngoài nội dung chính) | Lá đọc từ lá số của hai bạn để gợi chuyện. Lá không đo tình bạn và không nói thay ai. |
| Giải tán | Giải tán lá này? Lá và mọi thứ của hai bạn trong Tri Kỷ sẽ bị xoá. [Tên kia] không nhận thông báo. Ảnh đã chia sẻ ra ngoài thì Lá Lành không thu lại được. |
| Nút giải tán | Giải tán · Giữ lá |
| Lá không còn (mọi nguyên nhân) | Lá này không còn. |
| Yêu cầu chia sẻ (người xin) | Bạn muốn chia sẻ ảnh này? [Tên kia] cần đồng ý trước. |
| Yêu cầu chia sẻ (người được hỏi) | [Tên kia] muốn chia sẻ ảnh lá đôi này. Bạn đồng ý không? · Đồng ý chia sẻ · Không chia sẻ |
| Chưa chia sẻ được (hết 72 giờ, không nói lý do) | Ảnh này chưa chia sẻ được. |
| Hiểu Nhau Không? giới thiệu | 7 câu vui. Bạn trả lời cho mình và đoán câu của [tên kia]. Hai bạn chỉ so với kỷ lục của chính mình. |
| Câu ngay trên ô đồng ý trò đố | Câu trả lời gắn với hai bạn nên Lá Lành xử lý như dữ liệu nhạy cảm. |
| Ô đồng ý trò đố | Lưu câu trả lời của tôi cho lượt chơi này. Câu trả lời bị xoá khi cả hai bạn đã xem kết quả, muộn nhất 7 ngày sau khi lượt xong; chỉ giữ kỷ lục của hai bạn. |
| Kết quả | Lần này hai bạn hiểu nhau 5/7 câu. Kỷ lục của hai bạn: 6/7. |
| Kết quả bằng hoặc thấp hơn kỷ lục | Kỷ lục vẫn là 6/7. Lượt sau có câu mới. |
| Push khi có người nhận lời (nếu có push, chỉ câu cố định) | Có cập nhật mới trong Lá Lành. |

Không dùng ở bất kỳ đâu: "bạn đã bị xoá", "ai đó đã chọn bạn", "thân nhất", "top", "hơn [cặp khác]", "đã lâu không gặp", "quay lại phá kỷ lục", "mỗi tháng".

## 6. Chỉ số

**Không theo dõi từng người, không phân tích nội dung.** Chỉ dùng **bộ đếm tổng hợp theo ngày phía server**: không ID người, không ID cặp, không nhãn, không nội dung, không SDK bên thứ ba. Danh sách trường, mục đích, ngưỡng ô nhỏ (ẩn mọi ô < 3 theo KS-04; báo cáo Tri Kỷ chỉ hiện ô ≥ 10) và thời hạn (DPIA X7, chờ owner) nằm ở SRS §10 và là bản chuẩn; bảng dưới chỉ định nghĩa chỉ số tính từ các bộ đếm đó.

| Chỉ số | Định nghĩa | Vai trò |
|---|---|---|
| Tỷ lệ lời mời được nhận | invite chuyển `accepted` / invite tạo ra | Chính |
| Tỷ lệ hoàn tất | lá đôi dựng xong / invite tạo ra | Chính |
| Tỷ lệ B tạo hồ sơ mới | accept mà hồ sơ B được tạo trong luồng mời / accept | Tăng trưởng 1:1 |
| Tỷ lệ chia sẻ khi cả hai đồng ý | yêu cầu chia sẻ được duyệt / yêu cầu tạo ra | Phụ |
| Giải tán trong 30 ngày | số lá giải tán khi tuổi lá < 30 ngày (bucket tính lúc giải tán) / lá dựng xong | **Guardrail** |
| Báo cáo và chặn | số báo cáo lời mời, số lần chặn / invite tạo ra | **Guardrail** |
| Lỗi dựng lá | số lần dựng thất bại theo mã lỗi | Vận hành |

Đề xuất ngưỡng dừng (chờ owner): báo cáo > 1% lời mời trong một tuần, hoặc giải tán trong 30 ngày > 30%, thì tạm dừng tạo lời mời mới và rà copy/luồng. Không đặt mục tiêu "số lá trên mỗi người", vì nó đẩy về phía sưu tập người.

Không đo: ai mời ai, nhãn phân bố theo người, thời gian đọc lá, số lần mở lá, kết quả trò đố.

## 7. Phạm vi MVP và giai đoạn sau

- **MVP:** G50, G51, G52, G53, G54. Giọng direct. Không Luna. Không tarot. Không trò đố.
- **Sau MVP:** G55 Hiểu Nhau Không?; lá tarot của hai đứa; giọng Cà khịa; đổi "việc nhỏ để thử" (không nhắc).
- **Điều kiện bắt đầu build MVP:** tiêu chí thoát giai đoạn 1 của kế hoạch 23/10 đạt (P06/P07/P08 có receipt, D2 chạy, counsel trả lời D3/D4); counsel trả lời Q-L1–Q-L4 (§12); owner duyệt PRD, SRS, copy §5; kiểm chữ "tri kỷ / cạ cứng / đồng điệu" và ba nhãn với 5–10 người (giao cho Writer F, `docs/playtests/2026-11-game-line/`); DPIA (Writer D) và bản nháp store/privacy (Writer E) phản ánh đúng dữ liệu ở SRS §6.

## 8. Rủi ro

| # | Rủi ro | Giảm thế nào | Còn lại |
|---|---|---|---|
| R1 | Lá đôi bị hiểu là chuyện yêu đương | Ngữ cảnh cố định `friend`, bỏ chủ đề `attraction`, gate từ vựng, dòng chặn hiểu sai luôn hiện | Chưa đo chữ "tri kỷ" với Gen Z; chưa xác minh phim "Soulmate" có phát hành ở VN với tên "Tri kỷ" không |
| R2 | Một nhãn kiểu nghe như bị từ chối ("đang mở") | Ba kiểu ngang hàng, không thang; kiểm chữ trước build | Có thể phải đổi nhãn |
| R3 | Bất đối xứng ở trò đố (biết mình đoán đúng còn người kia đoán sai) | Chỉ điểm chung của cặp, không điểm riêng, không "ai hiểu ai hơn" | Người chơi vẫn suy ra được từ câu của mình; chấp nhận, ghi trong copy test |
| R4 | Giải tán "im lặng" vẫn bị nhận ra vì lá biến mất | Màn "Lá này không còn" giống hệt mọi nguyên nhân (xoá tài khoản, hết hạn hồ sơ) | Không xoá được cảm giác mất; đây là đánh đổi có chủ đích |
| R5 | Link mời bị chuyển tiếp, người lạ nhận | Dùng một lần, 7 ngày, cảnh báo trên landing, A thấy tên B chọn và giải tán ngay được | Người lạ đã thấy một lá có tên A; TK-4 có phương án A xác nhận trước |
| R6 | Dùng để so ai thân với sếp/ai bị bỏ ra ngoài ở văn phòng | Không danh sách xếp hạng, không đếm công khai, ảnh chia sẻ cần cả hai đồng ý | Người dùng vẫn có thể tự khoe; ngoài tầm kiểm soát |
| R7 | Người dưới 18 khai tuổi sai | Chặn theo ngày sinh của chính người đó; Play Console Restrict Minor Access như Radar | Không phải xác minh tuổi mạnh |
| R8 | Dữ liệu suy luận có thể được coi là nhạy cảm, cần thủ tục riêng (thông báo, DPIA) | Mặc định coi là nhạy cảm; đồng ý theo mục đích; DPIA | Chờ luật sư (Q-L1) |
| R9 | Lá sống không hạn cho tới khi giải tán, trái với hạn 30 ngày của Radar | Gắn với vòng đời hồ sơ của cả hai (30 ngày không hoạt động với khách, 365 ngày với tài khoản đã liên kết); xoá theo cascade | Chờ owner (TK-7) và luật sư (Q-L3) |
| R10 | Ảnh đã chia sẻ ra ngoài không thu lại được | Ảnh tối thiểu (không ngày sinh, cung, nguyên tố); copy nói rõ trước khi đồng ý | Còn tên hiển thị và nhãn kiểu |
| R11 | Áp lực quay lại qua "phá kỷ lục" | Bỏ "mỗi tháng", không nhắc, không đếm ngược, không cooldown hiển thị | Cần rà copy khi build G55 |
| R12 | Nhiều cặp trên một người thành "bộ sưu tập" | Giới hạn số lá đang có (TK-3), danh sách theo thời gian, không đếm công khai | |

## 9. Quyết định cần chủ sản phẩm

D-số là quyết định chung của dòng game (brief 26/10/2026). TK-số là quyết định riêng của Tri Kỷ. Tất cả là **Đề xuất — chờ owner**, chưa quyết.

| ID | Câu hỏi | Đề xuất mặc định | Phương án khác và hệ quả |
|---|---|---|---|
| **D5** | Tri Kỷ có hiện con số nào không | Không có độ hợp %, không chỉ báo 0–100. Chỉ có "x/7" ở Hiểu Nhau Không?, vì đó là đếm câu đoán đúng, không phải tiên đoán | Có % kiểu Spotify Blend: trái báo cáo, mời so cặp, rủi ro Apple 1.2 |
| TK-1 | Mức hồ sơ tối thiểu | Level 1 (chỉ ngày sinh) cho cả hai; nội dung tự rút gọn theo độ chính xác, ngày giáp ranh cung không dùng câu nguyên tố | Level 3 như Radar: ít chỗ sai hơn nhưng B phải khai giờ và nơi sinh ngay lần đầu, phễu giảm mạnh |
| TK-2 | Ai cần đăng nhập | A đăng nhập khi tạo link (US-19 hard trigger "gửi cho người khác"); B nhận bằng phiên khách có hồ sơ, được gợi ý liên kết nhưng không bắt buộc | Cả hai bắt buộc tài khoản: bền hơn khi đổi máy, phễu giảm |
| TK-3 | Số lá đang có tối đa mỗi người | 10 lá đang có, 5 lời mời đang chờ | Không giới hạn: dễ thành sưu tập |
| TK-4 | Link bị chuyển tiếp | Dựng lá ngay khi B đồng ý; A giải tán được ngay | A xác nhận "đúng người" trước khi dựng: an toàn hơn cho A, nhưng nếu A không xác nhận thì B nhận một tín hiệu như bị từ chối (bất đối xứng) |
| TK-5 | Cách tính "x/7" | Một câu được tính khi **cả hai** cùng đoán đúng câu của nhau | Tính khi **ít nhất một** người đoán đúng: điểm cao hơn, ít buồn hơn, nhưng kỷ lục dễ chạm 7/7 và hết vui |
| TK-6 | "Chơi lại mỗi tháng" của báo cáo | Bỏ chữ "mỗi tháng"; chơi lúc nào cũng được; không nhắc, không cooldown hiển thị; mỗi lượt rút câu mới | Nhịp hằng tháng có nhắc: trái nguyên tắc "không áp lực quay lại" |
| TK-7 | Lá có hạn tối đa không | Không hạn riêng; sống tới khi một người giải tán hoặc hồ sơ của một người hết hạn/bị xoá (theo hợp đồng dữ liệu chung) | Hỏi lại cả hai sau 12 tháng: tối thiểu hoá tốt hơn, thêm một lần làm phiền |
| TK-8 | Ảnh chia sẻ chứa gì | Tên Tri Kỷ, hai tên hiển thị, nhãn kiểu, một câu "điều chung" không nhắc cung/nguyên tố | Thêm cung/nguyên tố: hấp dẫn hơn nhưng lộ khoảng ngày sinh |
| TK-9 | Giọng | Chỉ direct ở MVP | Cà khịa ngay: cần duyệt thêm câu và gate |
| TK-10 | Luna | Tắt cho Tri Kỷ; không thêm `tri_ky` vào allowlist | Bật sau: cần mục đích, đồng ý, gate, DPA và đánh giá chuyển dữ liệu riêng |
| TK-11 | Hiểu Nhau Không? vào MVP? | Không, làm sau (đúng báo cáo) | Vào MVP: tăng vui nhưng thêm dữ liệu và copy cần duyệt |
| TK-12 | Thông báo khi B nhận lời | Chỉ mục trong hộp thư trong app; push chỉ khi người dùng đã bật và chỉ câu cố định "Có cập nhật mới trong Lá Lành" | Push có tên: vi phạm N4 |

## 10. Yêu cầu không chức năng (tóm tắt; chi tiết ở SRS §10)

Native app là đích phát hành; web là companion cho B mở link. Ultraviolet Paper, một font Be Vietnam Pro, light/dark. Control ≥ 44 px, screen reader, 200% chữ, Reduce Motion, WCAG AA. Không confetti, không đếm ngược. Lá không lưu bền trên máy. Dựng lá p95 ≤ 3 giây trên server hiện tại.

## 11. Truy vết requirement

| Requirement ở đây | Nguồn | Ghi chú |
|---|---|---|
| Không xếp hạng người, không "ai chọn bạn", không thu phí xem | Báo cáo 26/10 mục Tri Kỷ; ideation 28/09 loại Crush leaderboard | N1, §2.2 |
| Đồng ý trực tiếp của cả hai, chặn Check kín | Apple 5.1.1(viii); báo cáo; brief | N2; SRS FR-TK-020–024 |
| Không % | D5; US-13 AC04; US-22 AC04 | N3; Radar ba chỉ báo bị loại khỏi projection |
| Đường ray lời mời | US-08 §6–7; Radar spec §2, §7 | SRS §3 |
| Ngữ cảnh `friend` | Radar spec §2, `CONTEXTS` trong `radar/service.py` | Cố định, không chọn |
| Không streak/coin/XP | Kế hoạch 23/10 giai đoạn 3; `growth.test.ts` | N6 |
| Dữ liệu nhạy cảm | Luật 91/2025; Nghị định 356/2025 danh mục nhạy cảm | Q-L1 |
| Retention | Hợp đồng dữ liệu chung (brief 26/10) | SRS §8 |
| Xoá và sao lưu | Erasure journal P07 (`store-privacy-data-map.md`) | Kiểu mới `tri_ky_dissolved` |

## 12. Câu hỏi cho luật sư (bổ sung vào dossier #52 bằng PR riêng)

- **Q-L1.** Lá đôi suy ra từ ngày sinh của hai người có là dữ liệu nhạy cảm ("đời sống riêng tư") theo danh mục của Nghị định 356 không? Nếu có: thủ tục thông báo/đồng ý riêng nào bắt buộc, có cần nói rõ "đây là dữ liệu nhạy cảm" trong ô đồng ý không?
- **Q-L2.** Đồng ý `tri-ky-pair-v1` của từng người có đủ làm căn cứ xử lý không, hay cần căn cứ khác cho phần dữ liệu về người kia nằm trong lá?
- **Q-L3.** Lá sống không hạn riêng (gắn vòng đời hồ sơ) có đạt nguyên tắc giới hạn lưu trữ không, hay cần hạn tối đa/hỏi lại?
- **Q-L4.** Khi một người giải tán, xoá cả phần lá của người kia (người kia không đồng ý xoá) có vấn đề gì không? Có cần thông báo cho người kia không, hay "không thông báo" là được?
- **Q-L5.** Câu trả lời trò đố (sở thích vô hại) có cần đồng ý riêng theo mục đích hay đã nằm trong mục đích Tri Kỷ?
- **Q-L6.** Bản đánh giá tác động (DPIA) và hồ sơ chuyển dữ liệu ra nước ngoài hiện có có cần bổ sung riêng cho Tri Kỷ không?
- **Q-L7.** Bằng chứng đồng ý (đồng ý theo cặp trên hàng cặp và bằng chứng đồng ý chia sẻ `tri_ky_share_consents`) hiện bị xoá cùng lá khi giải tán. Nghị định 356 Điều 6 khoản 2 đặt trách nhiệm chứng minh đồng ý lên bên kiểm soát: có phải giữ một bản tối thiểu lâu hơn lá không, giữ bao lâu, và có mâu thuẫn với lời hứa "giải tán xoá mọi dữ liệu của cặp" không? **Chờ counsel.**

## 13. Việc phải sửa ở tài liệu khác (follow-up, **không** sửa trong PR này)

| Tài liệu | Cần sửa gì | Ai |
|---|---|---|
| `docs/legal/store-privacy-data-map.md` | Thêm dòng Apple App Privacy và Google Data Safety cho Tri Kỷ: tên hiển thị theo cặp, đồng ý, lá đôi (dữ liệu suy luận, linked, không tracking, App Functionality), yêu cầu chia sẻ, câu trả lời trò đố và kỷ lục, danh sách chặn, báo cáo; ghi rõ không chia sẻ cho bên thứ ba, ảnh chia sẻ do người dùng tự xuất | PR riêng, đối chiếu bản nháp của Writer E |
| `docs/user-stories/US-13-hoan-tat-full-la-ghep.md` | Ghi rằng Tri Kỷ là bề mặt riêng, không phải output Radar; AC04 (`scalar_score_eligible=false`) áp dụng và Tri Kỷ còn bỏ cả ba chỉ báo 0–100; AC10 không áp cho Tri Kỷ vì Tri Kỷ không có lối private | PR riêng |
| `docs/user-stories/US-12-tao-va-gui-la-ghep.md` | Thêm dòng: attestation `radar-authorized-input-v1` không bao giờ mở Tri Kỷ; fallback `/radar/invite` không được dẫn sang Tri Kỷ | PR riêng |
| `docs/foundation/la-lanh-radar-hop-gu-spec.md` | §2: ghi Tri Kỷ là bề mặt riêng dùng chung engine và rails, không phải mode thứ ba của Radar; §8: projection Tri Kỷ không chứa ba chỉ báo | PR riêng |
| `docs/legal/2026-10-22-privacy-counsel-dossier.md` | Thêm Q-L1–Q-L6 và dòng inventory Tri Kỷ | PR riêng, owner chuyển counsel |
| `docs/user-stories/US-19-xac-thuc-khi-can.md` | Thêm "Gửi lời mời Tri Kỷ" vào hard trigger (nếu TK-2 được duyệt) | PR riêng |
| `docs/user-stories/README.md` | Liên kết sang story map game | Coordinator |
| `docs/operations/luna-rewrite-release-runbook.md` / `apps/api/app/config.py` | Ghi rõ `tri_ky` không thuộc `CHART_FREE_REWRITE_SURFACES` | Khi build |
| `docs/operations/backup-restore-and-deletion-reconciliation.md` | Kiểu erasure journal mới `tri_ky_dissolved`, `tri_ky_quiz_cleared` | Khi build |
| Chính sách quyền riêng tư và lời giải thích trong app | Thêm mục Tri Kỷ khớp SRS §6 | PR riêng, owner duyệt copy |
| `docs/plans/2026-10-23-privacy-content-game-plan.md` | Ghi Tri Kỷ consent flow vào việc của giai đoạn 1 (theo báo cáo) | Owner/Coordinator |
| DPIA `docs/legal/2026-10-26-game-line-dpia.md` | Mirror SRS §6 và §8 | Writer D |

## 14. Bàn giao theo AGENTS.md

**Nguồn đã kiểm tra (26/10/2026):** brief dòng game; báo cáo "Chốt năm trò, giữ trọn chữ Lành" (mục Tri Kỷ, bảng quyết định, rủi ro, bàn giao); ghi chú `tri_ky_friendship_ranking.md`; `AGENTS.md`; chuẩn nội dung tiếng Việt; kế hoạch 23/10; PRD mẫu "Nơi bình yên"; US-08, US-09, US-12, US-13, US-19, US-22; `la-lanh-radar-hop-gu-spec.md`; `la-lanh-radar-r04-range-calibration-spec.md` (ba chỉ báo 0–100); `la-lanh-relationship-engine-spec.md`; `store-privacy-data-map.md`; dossier 22/10; `privacy-security-flow-notes.md`; `chart-synthesis-release-runbook.md`. Code chỉ đọc: `apps/api/app/domains/radar/service.py` (CONTEXTS, `radar-pair-v1`, TTL, yêu cầu Level 3 ở `_lock_chart_sources`), `routes/radar.py` (header công khai, token trong path rồi đổi sang cookie), `routes/la_chung.py` (tạo mới đang tắt), `radar/reading.py` (chủ đề `attraction`), `erasure_journal/journal.py`, `config.py`. Web: Apple App Review Guidelines (đọc trực tiếp 26/10/2026, 1.1.6, 1.2, 5.1.1(viii), 5.1.2(v)); danh mục dữ liệu nhạy cảm Nghị định 356 qua trang phổ biến pháp luật Cần Thơ (chưa đọc bản gốc .doc).

**Phát hiện đã sửa trong thiết kế:** bỏ ba chỉ báo 0–100 của Radar khỏi Tri Kỷ; đổi "giữ nhịp" (cụm từ cấm) trong ví dụ của báo cáo; bỏ "chơi lại mỗi tháng" vì trái nguyên tắc không áp lực quay lại; trò đố chỉ có điểm chung của cặp để tránh bất đối xứng; yêu cầu chia sẻ hết hạn im lặng thay vì "bị từ chối"; A cũng phải đồng ý theo mục đích (không chỉ B); xem trước link chỉ hiện tên A tự chọn, không hiện nhãn riêng A đặt cho B (khác runtime Radar/Lá Chứng hiện tại, xem SRS §3.3); token đặt trong fragment URL để không vào log server (SRS §9).

**Rà lại theo review Codex @ c1960a3 (26/10/2026):** thêm câu báo dữ liệu nhạy cảm ngay trên ô đồng ý của A và B (§4 bước 2, 5; §5); câu trả lời đố là dữ liệu nhạy cảm, xoá khi cả hai đã xem hoặc muộn nhất 7 ngày; tách hàng yêu cầu chia sẻ (7 ngày) với bằng chứng đồng ý (khi lá còn); §6 trỏ về danh sách chuẩn bộ đếm ở SRS §10; thêm Q-L7.

**Rủi ro chưa giải quyết:** §8 (R1–R12) và §12 (Q-L1–Q-L7). Nổi bật: chưa rõ dữ liệu suy luận có là dữ liệu nhạy cảm; lá không hạn riêng; chữ "tri kỷ" chưa đo với người dùng.

**AC/DoD còn thiếu:** toàn bộ. Chưa có quyết định D5, TK-1–TK-12; copy §5 chưa duyệt; chưa kiểm chữ; chưa có ý kiến luật sư; nhãn App Privacy, Data Safety, chính sách quyền riêng tư chưa cập nhật; DPIA chưa có; chưa có code (đúng kế hoạch).
