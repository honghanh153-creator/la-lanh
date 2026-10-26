# Tam Sao Thất Bản — PRD

> Phiên bản: 0.1 (nháp) · Cập nhật: 26/10/2026 · Trạng thái: **chờ chủ sản phẩm duyệt**. Chưa được duyệt để dựng.
> Mã nội bộ: **Mercury Relay**. Thuộc thương hiệu phụ (đề xuất **Lá Úp**, D1). Giai đoạn hiện tại chỉ làm tài liệu và playtest giấy
> (`docs/plans/2026-10-23-privacy-content-game-plan.md`, giai đoạn 3).
> Tài liệu đi cùng: [SRS](tam-sao-that-ban-srs.md) · user story [G20](../../user-stories/game/G20-phong-truc-tiep-chuoi-song-song.md),
> [G21](../../user-stories/game/G21-nhom-chat-nhan-luot.md), [G22](../../user-stories/game/G22-man-lat-va-phat-lai.md),
> [G23](../../user-stories/game/G23-ngan-hang-de-va-phuong-an-gan-dung.md), [G24](../../user-stories/game/G24-quyen-host-va-nguoi-choi.md),
> [G25](../../user-stories/game/G25-xoa-du-lieu-va-tieu-huy-ho-so.md).
> Hạ tầng phòng chung (QR, mã phòng, màn hình chung, phiên host/người chơi, màn tiêu huỷ hồ sơ) do `shared-room-platform-srs.md` và story G01–G09
> định nghĩa; PRD này chỉ nói phần riêng của Tam Sao Thất Bản.

---

## 0. Tóm tắt một đoạn

"Chuyền một câu qua năm người, xem nó thất bản thành cái gì." Mỗi người gieo một câu nhắn đời thường ("Mai cho tớ mượn sạc dự phòng nhé"),
rồi câu đó đi qua bốn người khác, mỗi người chỉ thấy **một mảnh** và chỉ **chọn trong 4 phương án soạn sẵn**: người thứ hai chỉ biết ý định
và sắc thái, chọn một câu viết theo "giọng cô hàng xóm nhắn Zalo"; người thứ ba đoán mood; người thứ tư viết lại theo "giọng sếp gửi mail"; người cuối đoán
câu gốc. Cuối ván, màn hình chung phát lại cả chuỗi cạnh câu gốc, kèm dấu đỏ "THẤT BẢN". Không ai bị chấm đúng sai; cả phòng bầu chuỗi thất bản
đẹp nhất. Bản chính là **phòng trực tiếp**; bản phụ là **nhóm chat không đồng bộ** (chỉ vào MVP nếu playtest đạt, D4).

## 1. Bối cảnh và bằng chứng

Nguồn chính: báo cáo "Chốt năm trò, giữ trọn chữ Lành" (26/10/2026, phần Tam Sao Thất Bản) và ghi chú
`research_notes/Chốt trò chơi nhóm Lá Lành/relay_games_chat_vs_live.md`. Ý tưởng gốc Mercury Relay ở
`docs/ideation/2026-09-28-astro-tarot-campus-referral-games-ideation.html`.

| Bằng chứng | Ý nghĩa cho thiết kế | Độ tin |
|---|---|---|
| Trò bịt tai buồn cười nhờ ba thứ: mặt vật lộn, khoảng cách giữa câu khán giả biết và câu đoán sai, tiếng hét tự tin mà sai. Lên chat chỉ còn thứ hai | Màn lật đặt câu gốc cạnh câu cuối phải gánh toàn bộ tiếng cười | Suy luận từ cách định dạng vận hành |
| Whisper Challenge (The Tonight Show) lan thành định dạng video gia đình; bản Việt trên Kenh14: "Cáo già đeo nơ" trôi thành "Kéo ra, kéo vào" | Có sẵn văn hoá trò này ở Việt Nam; người xem thích cảnh trôi | Thứ cấp |
| Gartic Phone: mọi người viết cùng lúc theo đồng hồ, đổi luân phiên chữ và hình, phát lại cuối ván, không thắng thua, khuyến khích chơi kèm gọi thoại | Chuỗi song song, đổi dạng thông tin mỗi lượt, không chấm điểm người | Thứ cấp |
| Broken Picture Telephone (2007): chuỗi mở hàng giờ–ngày, mỗi người một lượt ≤ 10 phút, giấu chuỗi tới khi xong; chữ tự do + ẩn danh sinh trolling khi đông | Bản chat dùng "nhận lượt tự do", giấu chuỗi; **không chữ tự do** | Thứ cấp |
| Draw Something: đỉnh ~14,6 triệu DAU (4/2012) → ~3 triệu (8/2012); "phần lớn lượt chơi là ngồi chờ" | Bản chat không chạy chuỗi nối tiếp cứng | Thứ cấp (tracker) |
| Meta đưa Instant Games ra khỏi khung chat Messenger năm 2019 | Khung chat chỉ mang lời mời và thẻ kết quả; phần chơi ở trang web | Thứ cấp |
| Chờ có hẹn thành háo hức, chờ vô định thành bực (Aalto, CHI PLAY 2024) | Giờ lật cố định "Kết quả lúc 21:00" | Tổng quan tài liệu (WIP) |
| Jackbox cho người thừa làm khán giả bỏ phiếu | Người vào muộn và người "chỉ xem" bỏ phiếu chuỗi | Thứ cấp |
| **Chưa có dữ liệu** nào cho thấy trò truyền tin dạng trắc nghiệm vẫn buồn cười như vẽ hay viết tự do | Rủi ro lớn nhất; phương án gần đúng phải được thiết kế có chủ đích và playtest | — |

## 2. Mục tiêu, phi mục tiêu và nguyên tắc

### 2.1. Mục tiêu

- **G1.** Một ván phòng trực tiếp ~15 phút làm cả phòng cười ở màn lật.
- **G2.** Không ai thấy mình bị chê sai: chỉ có "độ thất bản" của cả chuỗi.
- **G3.** Thẻ lật đủ hay để người chơi tự gửi vào nhóm chat, và không mang dữ liệu nào ngoài biệt danh đã đồng ý và chữ của ngân hàng đề.
- **G4.** Dữ liệu sống ngắn: phòng trực tiếp xoá khi kết thúc; bản chat xoá 48 giờ sau màn lật.

### 2.2. Phi mục tiêu

- Không chữ tự do (ngoài biệt danh), không chat, không nhắn riêng, không ảnh, không ghi âm, không giọng đọc máy ở MVP.
- Không chấm đúng sai từng người, không bảng xếp hạng, không coin/XP, không streak.
- Không chạy bên trong Zalo/Messenger; không bot gửi tin vào nhóm chat.
- Không AI/LLM ở MVP (D7). "Bot Sao Thủy" là lựa chọn ngẫu nhiên có nhãn, không phải AI.
- Không chú thích chiêm tinh cá nhân trong Lá Úp (không dữ liệu sinh); chỉ có "Sao Thủy chú thích" dạng kiến thức chung (TS-D6).
- Không phòng công khai, không tìm phòng; chỉ 18+.

### 2.3. Nguyên tắc

1. **Mỗi lượt là một kiểu lựa chọn khác:** câu → ý định + sắc thái → câu theo giọng → mood → câu theo giọng khác → đoán gốc.
2. **Trôi có chủ đích:** mỗi lượt 3–4 phương án, luôn có phương án gần đúng (đổi dấu thanh, từ gần âm, đổi chi tiết, đổi sắc thái, hiểu nghĩa đen).
3. **Không ai có lỗi:** điểm chỉ thuộc về chuỗi; Sao Thủy chú thích nói về cách nghe, không nói ai sai.
4. **Giấu tới phút chót, lật một lần:** mỗi người chỉ thấy mảnh trước mặt mình.
5. **Không ai phải chờ:** chuỗi song song; bản chat nhận lượt tự do, có hạn chót, có Bot Sao Thủy điền thay.

## 3. Người dùng và bối cảnh dùng

| Persona | Bối cảnh | Cần gì | Lo gì |
|---|---|---|---|
| **Lan, 21 tuổi, lớp trưởng** | Sinh hoạt lớp 25 người, có máy chiếu | Trò mở màn 15 phút, ai cũng chơi được bằng điện thoại | Phải tải app; người ngại bị gọi lên |
| **Anh Khoa, 30 tuổi, trưởng nhóm** | Họp đầu tuần 8 người, chiếu lên TV phòng họp | Trò phá băng không đụng chuyện nhạy cảm | Nội dung lố trước sếp; dữ liệu nằm lại |
| **Nhóm bạn 6 người ở ba thành phố** | Nhóm Zalo, không gặp được nhau | Chơi rải rác trong ngày, tối xem kết quả | Một người im là cả trò đứng |
| **Người "chỉ xem"** | Vào muộn hoặc không muốn chơi | Vẫn được bỏ phiếu, cười cùng | Bị ép chơi |

Không tài khoản: host và người chơi là **phiên thiết bị** + biệt danh (theo hạ tầng phòng chung).

## 4. Luật chơi chốt

### 4.1. Phòng trực tiếp (bản chính) — G20, G22

| Bước | Người chơi thấy | Người chơi làm | Thời lượng |
|---|---|---|---|
| 0. Vào phòng | QR và mã phòng trên màn hình chung | Nhập biệt danh, đồng ý (luồng vào phòng chung + hai ô riêng của Tam Sao), chọn bàn nếu phòng > 12 (máy chủ cân lại để mỗi bàn 4–6 người) | ≤ 60 giây |
| 1. Gieo | 3 thông điệp gốc rút ngẫu nhiên, mỗi cái một ý định khác nhau | Chọn 1. N người → N chuỗi chạy cùng lúc | 10 giây |
| 2. Diễn đạt | Chỉ chip **ý định + sắc thái** (ví dụ "Nhờ vả · hơi ngại") và một **giọng** được giao ngẫu nhiên | Chọn 1 trong 4 câu viết theo giọng đó | 20 giây |
| 3. Bắt mood | Chỉ câu ở bước 2. Nếu host bật "đọc to", người làm bước 2 đọc câu đó bằng giọng được giao (tuỳ chọn, bỏ qua được, không ghi âm) | Chọn mood trên vòng 8 emoji và độ mạnh 1–3 | 15 giây |
| 4. Nói lại | Chỉ mood và độ mạnh | Chọn 1 trong 4 câu viết theo một giọng khác bước 2 | 20 giây |
| 5. Đoán gốc | Chỉ câu ở bước 4 | Chọn câu gốc trong 4 phương án | 15 giây |
| 6. Lật | Màn hình chung phát lại từng chuỗi: Gốc → Ý → Câu → Mood → Câu mới → Đoán, dấu "THẤT BẢN" theo độ thất bản | Bỏ phiếu "chuỗi thất bản đẹp nhất" | 5–8 phút |

- Quy mô MVP: 4–30 người. Mỗi người làm đúng một bước của mỗi chuỗi mình chạm vào, không làm hai bước trong cùng một chuỗi.
- Xoay vòng: ở vòng r (0–4), người thứ i làm chuỗi (i − r) mod N trong bàn của mình.
- **Bàn 4 người** (phòng 4 người, hoặc bàn còn 4 vì có người rời): bước 4 do Bot Sao Thủy điền, có nhãn; bốn người làm bước 1, 2, 3, 5 (TS-D3).
- Hết giờ mà chưa chọn, hoặc mất kết nối: Bot Sao Thủy chọn ngẫu nhiên một phương án, có nhãn "Sao Thủy điền giúp".
- Phòng > 12 người: chia bàn 4–6 người, chuỗi xoay trong bàn; mỗi bàn bầu một chuỗi trên điện thoại, chuỗi cao phiếu nhất của từng bàn lên màn hình chung;
  cả phòng bầu chuỗi đẹp nhất. Người vào sau khi ván bắt đầu và người chọn "chỉ xem" là khán giả bỏ phiếu.
- Cả ván khoảng 15 phút.

### 4.2. Nhóm chat không đồng bộ (bản phụ) — G21, G22 · **D4: chỉ vào MVP nếu playtest đạt**

| Quy tắc | Chi tiết |
|---|---|
| Nơi chơi | Trang web mở từ link. Khung chat (Zalo, Messenger…) chỉ mang lời mời, tối đa một câu nhắc host tự gửi cho mỗi lượt, và thẻ lật |
| Quy mô | 4–8 người, host chọn 3 hoặc 4 chuỗi song song |
| Nhận lượt tự do | Ai mở link cũng nhận được một lượt đang chờ. Nhận xong có 10 phút để chọn, quá thì lượt trả về hàng chờ. Mỗi người tối đa một lượt trong mỗi chuỗi |
| Hạn chót mỗi lượt | Mặc định 3 giờ kể từ khi lượt sẵn sàng. Quá hạn thì Bot Sao Thủy điền, có nhãn. Không còn ai đủ điều kiện làm lượt đó thì Bot điền ngay |
| Chuỗi tối thiểu | Chuỗi được tính "hoàn tất" khi có ≥ 4 lượt do người làm. Tới giờ lật, lượt còn thiếu do Bot điền |
| Giờ lật | Host chọn khi tạo, trong khoảng 2–48 giờ (mặc định 21:00 gần nhất cách ít nhất 6 giờ); hoặc lật ngay khi mọi chuỗi xong |
| Nhắc | Tối đa một câu nhắc cho mỗi lượt đang chờ, host bấm "Sao chép câu nhắc" rồi tự gửi vào nhóm chat. **Không có thông báo đẩy** ở bản chat (tối thiểu hoá: không lưu địa chỉ nhận thông báo); giờ lật được ghi rõ trên trang và trong lời mời |
| Thẻ lật | Ảnh dọc: câu gốc và câu cuối chữ to, đường đi ở giữa. Chỉ người đã tick "cho biệt danh của tôi nằm trên thẻ lật" hiện tên, người khác hiện "Người chơi A, B…" |
| Link | Không lập chỉ mục, không cache, token không vào log hay Referer, hết hạn 48 giờ sau màn lật, host thu hồi được |

Quy tắc chốt (D4): bản chat vào MVP nếu ở playtest giấy **≥ 70% chuỗi có ≥ 4 lượt người làm trước giờ lật** và nhóm tự xin chơi lại.
Ngưỡng 70% là đề xuất, chưa có chuẩn ngành.

### 4.3. Độ thất bản (của chuỗi, không của người)

Mỗi chuỗi cộng 1 điểm cho mỗi chỗ trôi: bước 2 chọn phương án không phải "đúng ý"; bước 3 chọn mood khác mood gốc; bước 4 chọn câu thuộc ý định khác;
bước 5 đoán sai. Tổng 0–4:

| Điểm | Nhãn trên màn lật |
|---|---|
| 0 | "Truyền tin chuẩn chỉnh" |
| 1 | "Hơi lệch" |
| 2 | "THẤT BẢN" |
| 3 | "THẤT BẢN nặng" |
| 4 | "THẤT BẢN toàn tập" |

Lượt do Bot điền vẫn tính trôi như lượt người, có nhãn riêng. Không có điểm cho từng người. Phiếu bầu "chuỗi thất bản đẹp nhất" chỉ hiện chuỗi thắng.

### 4.4. Sao Thủy chú thích (chung, không dữ liệu cá nhân)

Mỗi chuỗi có một dòng chọn theo chỗ trôi lớn nhất, ví dụ:

- Trôi ở giọng: "Cùng một lời nhờ, qua giọng sếp gửi mail nghe thành mệnh lệnh."
- Trôi ở mood: "Câu chữ giữ nguyên, nhưng người nghe bắt sai cảm xúc. Chuyện này xảy ra cả ngoài đời."
- Trôi ở chữ: "Một dấu thanh đổi, cục sạc thành cái sạp."
- Không trôi: "Chuỗi này giữ được ý. Hiếm đấy."

Dòng chú thích nói về cách nghe, không nói ai sai, không dự đoán.

## 5. Nội dung: ngân hàng đề khởi đầu

**Nháp, chờ owner duyệt văn phong.** MVP cần khoảng 60 thông điệp gốc × 5 giọng; dưới đây là bộ khởi đầu **16 ý định**, mỗi ý định có: thông điệp gốc,
sắc thái, mood gốc, 4 phương án bước 2 (một giọng mẫu) gắn nhãn kiểu trôi, một câu bước 4 (giọng khác) và 3 phương án nhiễu cho bước 5.
Quy tắc soạn và rà ở G23 và SRS §3.4.

**Giọng (5):** V1 Cô hàng xóm nhắn Zalo · V2 Sếp gửi mail · V3 MC đám cưới · V4 Gen Z viết tắt · V5 Thơ lục bát.
**Vòng mood (8):** 😄 Vui · 🤩 Hào hứng · 😅 Ngại · 😌 Bình thản · 😤 Bực · 🥺 Năn nỉ · 😏 Tinh nghịch · 😬 Lo lo. Độ mạnh 1–3.
Mood ở đây là cảm xúc của **câu nhắn**, không phải tâm trạng của người chơi.
**Nhãn kiểu trôi:** [đúng ý] · [dấu] đổi dấu thanh · [âm] từ gần âm · [chi tiết] đổi chi tiết · [sắc thái] đổi sắc thái · [nghĩa đen] hiểu nghĩa đen.

| # | Ý định · sắc thái · mood gốc | Thông điệp gốc | Bước 2 (giọng mẫu): 4 phương án | Bước 4 (giọng khác) | Bước 5: 3 phương án nhiễu |
|---|---|---|---|---|---|
| 1 | Nhờ vả · hơi ngại · 😅2 | Mai cho tớ mượn sạc dự phòng nhé. *(báo cáo)* | V1: [đúng ý] "Cháu ơi mai cho cô mượn cục sạc dự phòng nha, cô ngại hỏi quá." · [dấu] "Cháu ơi mai cho cô mượn cục sặc dự phòng nha." · [âm] "Cháu ơi mai cho cô mượn cái sạp dự phòng nha." · [sắc thái] "Mai mang sạc dự phòng qua cho cô. Không bàn cãi." | V2: "Kính gửi anh/chị, nếu không phiền, em xin phép mượn thiết bị sạc vào ngày mai." | "Mai cho tớ mượn sách dự thi nhé." · "Mai tớ trả cậu cục sạc nhé." · "Mai cho tớ mượn sân dự phòng nhé." |
| 2 | Rủ đi ăn · hào hứng · 🤩3 | Tối nay đi ăn lẩu không, tớ thèm quá! | V3: [đúng ý] "Xin trân trọng kính mời quý bạn tối nay cùng thưởng thức một nồi lẩu thật nóng!" · [âm] "Kính mời quý bạn tối nay cùng lên lầu ngắm trăng!" · [chi tiết] "Kính mời quý bạn trưa mai cùng thưởng thức một nồi lẩu!" · [sắc thái] "Kính mời quý bạn tối nay… rảnh thì đi, không thì thôi." | V4: "tối nay lẩu ko, đói xỉu r 🤤" | "Tối nay đi hát karaoke không, tớ thèm quá!" · "Tối nay lên lầu không, ngắm trăng đẹp lắm!" · "Trưa mai đi ăn lẩu không, tớ đói quá!" |
| 3 | Nhắc khéo trả đồ · tinh nghịch · 😏2 | Cái ô tớ cho mượn hôm trước chắc nhớ nhà rồi đấy. | V2: [đúng ý] "Kính gửi bạn, chiếc ô được cho mượn hôm trước có vẻ đang nhớ chủ cũ. Mong sớm đoàn tụ." · [nghĩa đen] "Kính gửi bạn, chiếc ô của tôi đã gửi đơn xin về quê." · [âm] "Kính gửi bạn, cái ổ bánh mì tôi cho hôm trước có vẻ đang nhớ nhà." · [sắc thái] "Yêu cầu hoàn trả ô trước 17:00 hôm nay." | V1: "Cháu ơi cái ô của cô đi lâu quá chưa về, cô lo." | "Cái ổ bánh mì tớ cho hôm trước chắc nguội rồi đấy." · "Cái ô tớ cho mượn hôm trước chắc hỏng rồi đấy." · "Cái áo tớ cho mượn hôm trước chắc nhớ nhà rồi đấy." |
| 4 | Khoe · hào hứng · 🤩2 | Tớ vừa nấu thành công nồi cơm không bị khê! | V5: [đúng ý] "Hôm nay cơm chín thơm lừng / Nồi không khê cháy, tớ mừng rưng rưng." · [âm] "Hôm nay cơm chín thơm lừng / Nồi không khế cháy, tớ mừng rưng rưng." · [chi tiết] "Hôm nay canh chín thơm lừng / Nồi không trào nước, tớ mừng rưng rưng." · [sắc thái] "Nồi cơm chín, chuyện thường thôi / Có gì đâu mà phải ngồi khoe khoang." | V4: "ê t nấu cơm k khê nha, đỉnh nóc kịch trần 😎" | "Tớ vừa nấu thành công nồi canh khế!" · "Tớ vừa nấu nồi cơm bị khê rồi!" · "Tớ vừa mua thành công nồi cơm điện!" |
| 5 | Xin lỗi vì trễ · ngại · 😅2 | Tớ xin lỗi, kẹt xe nên tới trễ 10 phút. | V3: [đúng ý] "Xin quý vị thứ lỗi, do kẹt xe, nhân vật chính sẽ xuất hiện trễ 10 phút!" · [dấu] "Xin quý vị thứ lỗi, do kẹt xe, nhân vật chính sẽ trẻ ra 10 phút!" · [chi tiết] "Xin quý vị thứ lỗi, do kẹt thang máy, nhân vật chính sẽ tới trễ 10 phút!" · [sắc thái] "Xin quý vị kiên nhẫn, người quan trọng luôn đến sau cùng!" | V2: "Kính gửi anh/chị, em thành thật xin lỗi vì sự chậm trễ ngoài ý muốn." | "Tớ xin lỗi, kẹt xe nên tới sớm 10 phút." · "Tớ xin lỗi, kẹt thang máy nên tới trễ 10 phút." · "Tớ xin lỗi, quên xe nên tới trễ 10 phút." |
| 6 | Từ chối khéo · ngại · 😅1 | Tuần này tớ bận rồi, hẹn cậu tuần sau nhé. | V4: [đúng ý] "tuần này t bận r, tuần sau nha 🙏" · [dấu] "tuần này t bẩn r, tuần sau nha" · [chi tiết] "tuần sau t bận r, tuần này nha" · [sắc thái] "k đi đâu, đừng rủ 😑" | V1: "Cháu ơi tuần này cô kín lịch rồi, để tuần sau cô cháu mình đi nha." | "Tuần này tớ bẩn rồi, hẹn cậu tuần sau nhé." · "Tuần sau tớ bận rồi, hẹn cậu tuần này nhé." · "Tuần này tớ bận rồi, hẹn cậu năm sau nhé." |
| 7 | Cảm ơn · vui · 😄2 | Cảm ơn cậu đã giữ chỗ cho tớ trong căn tin! | V2: [đúng ý] "Kính gửi bạn, xin chân thành cảm ơn bạn đã giữ chỗ cho tôi tại căn tin." · [âm] "Kính gửi bạn, xin chân thành cảm ơn bạn đã giữ chó cho tôi tại căn tin." · [chi tiết] "Kính gửi bạn, xin cảm ơn bạn đã giữ chỗ cho tôi tại phòng họp." · [sắc thái] "Ghi nhận việc giữ chỗ. Lần sau đề nghị giữ gần cửa sổ." | V3: "Xin một tràng pháo tay cảm ơn người bạn đã giữ cho tôi một chỗ ngồi!" | "Cảm ơn cậu đã giữ chó cho tớ trong căn tin!" · "Cảm ơn cậu đã giữ chỗ cho tớ trong thư viện!" · "Cảm ơn cậu đã gửi đồ cho tớ trong căn tin!" |
| 8 | Hỏi thăm · bình thản · 😌1 | Hôm nay deadline sao rồi, có cần tớ đỡ một tay không? | V1: [đúng ý] "Cháu ơi việc hôm nay sao rồi, cần cô phụ gì không cháu?" · [nghĩa đen] "Cháu ơi đưa tay đây cô đỡ cho, tay cháu mỏi không?" · [âm] "Cháu ơi cái 'đét lai' hôm nay ăn chưa cháu?" · [sắc thái] "Việc của cháu thì cháu tự lo đi nhé." | V4: "dl sao r, cần t gánh k 💪" | "Hôm nay deadline sao rồi, có cần tớ đỡ một chân không?" · "Hôm nay ăn trưa chưa, có cần tớ mua giùm không?" · "Hôm nay deadline lùi rồi, có cần tớ báo một tiếng không?" |
| 9 | Báo tin vui nhỏ · hào hứng · 🤩2 | Quán trà sữa đầu ngõ vừa mở lại rồi! | V5: [đúng ý] "Đầu ngõ có quán quen xưa / Hôm nay mở lại, trà sữa ngọt ngào." · [âm] "Đầu ngõ có quán quen xưa / Hôm nay mở lại, trà sứa ngọt ngào." · [chi tiết] "Cuối phố có quán quen xưa / Hôm nay đóng cửa, trà sữa ngọt ngào." · [sắc thái] "Quán xưa mở lại thì sao / Uống hay không uống, chẳng nao lòng mình." | V2: "Thông báo: cơ sở cung cấp đồ uống đầu ngõ đã hoạt động trở lại." | "Quán trà sứa đầu ngõ vừa mở lại rồi!" · "Quán trà sữa cuối ngõ vừa đóng cửa rồi!" · "Quán cà phê đầu ngõ vừa mở lại rồi!" |
| 10 | Đổi lịch · ngại · 😅1 | Họp nhóm dời sang 3 giờ chiều được không? | V3: [đúng ý] "Xin thông báo, buổi họp nhóm xin phép dời sang 3 giờ chiều, mong quý vị thông cảm!" · [chi tiết] "Xin thông báo, buổi họp nhóm dời sang 3 giờ sáng!" · [dấu] "Xin thông báo, buổi hớp nhóm, mỗi người một ngụm, dời sang 3 giờ chiều!" · [sắc thái] "Xin thông báo, buổi họp nhóm dời sang 3 giờ chiều, ai không tới tự chịu!" | V4: "họp dời 3h chiều đc k mn 🥲" | "Họp nhóm dời sang 3 giờ sáng được không?" · "Hớp nhóm dời sang 3 giờ chiều được không?" · "Họp lớp dời sang 3 giờ chiều được không?" |
| 11 | Xin ý kiến · bình thản · 😌1 | Slide này nên để nền xanh hay nền trắng? | V1: [đúng ý] "Cháu ơi cái slide này để nền xanh hay nền trắng thì đẹp hả cháu?" · [nghĩa đen] "Cháu ơi lát nền nhà màu xanh hay màu trắng hả cháu?" · [chi tiết] "Cháu ơi cái slide này để nền đỏ hay nền vàng?" · [sắc thái] "Để nền gì cũng được, cháu hỏi làm gì." | V2: "Kính gửi team, xin ý kiến về phương án màu nền cho bài trình bày." | "Sàn nhà này nên lát gạch xanh hay gạch trắng?" · "Slide này nên để chữ xanh hay chữ trắng?" · "Slide này nên bỏ nền xanh hay giữ nền trắng?" |
| 12 | Chúc mừng · vui · 😄2 | Chúc mừng cậu vừa nuôi sống được chậu cây đầu tiên! | V3: [đúng ý] "Xin chúc mừng người bạn của chúng ta đã nuôi sống thành công chậu cây đầu tiên!" · [âm] "Xin chúc mừng người bạn của chúng ta đã nuôi thành công chậu ớt cay đầu tiên!" · [chi tiết] "Xin chúc mừng người bạn của chúng ta đã nuôi sống chú cá đầu tiên!" · [sắc thái] "Xin chúc mừng… một chậu cây thôi mà, cũng không có gì to tát." | V1: "Cháu giỏi quá, cây của cháu xanh tốt rồi kìa!" | "Chúc mừng cậu vừa trồng được chậu ớt cay đầu tiên!" · "Chúc mừng cậu vừa nuôi sống được chú cá đầu tiên!" · "Chúc mừng cậu vừa mua được chậu cây đầu tiên!" |
| 13 | Mời · hào hứng · 🤩2 | Thứ Bảy này qua nhà tớ xem phim nhé! | V2: [đúng ý] "Kính mời bạn tham dự buổi chiếu phim tại tư gia vào thứ Bảy này." · [âm] "Kính mời bạn tham dự buổi pha phin tại tư gia vào thứ Bảy này." · [chi tiết] "Kính mời bạn tham dự buổi họp tại tư gia vào thứ Bảy này." · [sắc thái] "Thứ Bảy này yêu cầu có mặt tại nhà tôi lúc 19:00." | V4: "t7 qua nhà t cày phim k 🍿" | "Thứ Bảy này qua nhà tớ pha phin nhé!" · "Thứ Bảy này qua nhà tớ họp nhóm nhé!" · "Chủ Nhật này qua nhà tớ xem phim nhé!" |
| 14 | Than nhẹ · bực · 😤1 | Máy lạnh phòng mình lại kêu rè rè rồi. | V5: [đúng ý] "Phòng mình máy lạnh lại rè / Kêu như ve sầu mùa hè giữa trưa." · [âm] "Phòng mình máy lạnh lại rề / Chạy chầm chậm như kéo lê cả chiều." · [chi tiết] "Phòng mình quạt trần lại rè / Kêu như ve sầu mùa hè giữa trưa." · [sắc thái] "Máy kêu thì kệ máy kêu / Mình nghe như nhạc, càng nhiều càng vui." | V3: "Xin mời quý vị lắng nghe màn trình diễn rè rè đặc sắc của chiếc máy lạnh!" | "Quạt trần phòng mình lại kêu rè rè rồi." · "Máy lạnh phòng mình lại chạy rề rề rồi." · "Máy lạnh phòng mình lại lạnh quá rồi." |
| 15 | Nhắc hạn nộp · hơi gấp · 😬2 | Nhắc nhẹ: 5 giờ chiều nay nộp báo cáo nha. | V1: [đúng ý] "Cháu ơi 5 giờ chiều nay nộp báo cáo nha cháu, cô nhắc trước đó." · [âm] "Cháu ơi 5 giờ chiều nay nộp bao gạo nha cháu." · [chi tiết] "Cháu ơi 5 giờ sáng mai nộp báo cáo nha cháu." · [sắc thái] "Nộp hay không tuỳ cháu, cô nói rồi đó." | V2: "Kính gửi anh/chị, xin lưu ý hạn nộp báo cáo là 17:00 hôm nay." | "Nhắc nhẹ: 5 giờ chiều nay nộp bao gạo nha." · "Nhắc nhẹ: 5 giờ sáng mai nộp báo cáo nha." · "Nhắc nhẹ: 5 giờ chiều nay họp báo cáo nha." |
| 16 | Hỏi đường · bình thản · 😌1 | Từ cổng trường tới thư viện đi lối nào vậy? | V3: [đúng ý] "Xin quý vị chỉ giúp, từ cổng trường tới thư viện đi lối nào ạ?" · [dấu] "Xin quý vị chỉ giúp, từ cổng trường tới thư viện phải lội qua đâu ạ?" · [chi tiết] "Xin quý vị chỉ giúp, từ cổng trường tới căn tin đi lối nào ạ?" · [sắc thái] "Xin quý vị tránh đường, tôi tự tìm thư viện!" | V4: "đg nào ra thư viện v mn 🧭" | "Từ cổng trường tới thư viện lội qua đâu vậy?" · "Từ cổng trường tới căn tin đi lối nào vậy?" · "Từ thư viện tới cổng trường đi lối nào vậy?" |

Ghi chú rà soát (đề xuất): #8 dùng chữ "deadline" (trộn tiếng Anh nhẹ, hợp văn phòng); #12 đổi từ ý "chúc mừng qua môn" sang "nuôi sống chậu cây" để tránh chủ đề kết quả thi;
#2 câu "thèm" là đồ ăn, không gợi nghĩa khác; giọng V1 đổi từ "mẹ nhắn Zalo" (báo cáo) sang "cô hàng xóm nhắn Zalo" (26/10/2026) để ngân hàng không chạm chủ đề gia đình, vẫn giữ kiểu viết thân mật của người lớn tuổi. Cần kiểm tra với 5–10 người xem các phương án [dấu] và [âm]
có đủ gần để người chơi chọn nhầm không.

**Cách ghép phương án lúc chơi** (chi tiết ở SRS §3.4):

- Bước 4 luôn có 4 câu cùng mood (± 1 độ mạnh) và cùng giọng V' ≠ giọng bước 2: một câu thuộc ý định gốc của chuỗi (nếu ngân hàng có), ba câu thuộc ý định khác.
- Bước 5 có 4 câu: câu gốc thật, một phương án nhiễu của câu gốc, câu gốc của ý định mà câu bước 4 thuộc về (nếu khác ý định gốc), và một phương án nhiễu của câu đó.
  Nếu bước 4 đúng ý định gốc, dùng câu gốc thật + 3 phương án nhiễu của nó.

## 6. Chỉ số

Chỉ số đếm tổng hợp ở máy chủ, không SDK bên thứ ba, không gắn biệt danh hay phiên.

| Chỉ số | Chế độ | Ghi chú |
|---|---|---|
| Tỷ lệ chuỗi có ≥ 4 lượt người làm trước giờ lật | Chat | Ngưỡng D4 ≥ 70% |
| Thời gian trung vị từ gieo tới lật | Cả hai | |
| Phân bố độ thất bản (0–4) | Cả hai | Đa số chuỗi 0–1 → trò nhạt, phải sửa phương án gần đúng |
| Số thẻ lật được chia sẻ mỗi ván | Cả hai | Đếm lần bấm chia sẻ, không ghi đích |
| Tỷ lệ nhóm/phòng mở ván thứ hai trong 24 giờ | Cả hai | Đếm theo phiên host, không lưu quá 24 giờ |
| Số lượt Bot Sao Thủy điền / tổng lượt | Cả hai | Cao → giờ hoặc hạn chót quá ngắn |
| Số báo cáo / ván, số lần host gỡ người | Cả hai | Chỉ báo an toàn |

## 7. Phạm vi MVP và sau MVP

| Hạng mục | MVP | Sau MVP |
|---|---|---|
| Phòng trực tiếp, 5 bước, 4–30 người, chia bàn, khán giả bỏ phiếu | ✓ | |
| Ngân hàng ~60 thông điệp gốc × 5 giọng, 8 mood | ✓ | |
| Sao Thủy chú thích dạng chung | ✓ | |
| Thẻ lật, phát lại trên màn hình chung | ✓ | |
| Lượt "đọc to" tuỳ chọn (không ghi âm) | ✓ (host bật) | |
| Bản nhóm chat không đồng bộ | Chỉ khi đạt D4 | ✓ (mặc định ở đây) |
| Chú thích Sao Thủy cá nhân | | Không làm trong Lá Úp (TS-D6) |
| Giọng theo mùa (Tết, tất niên) | | ✓ |
| Lượt "nghe" bằng giọng đọc máy | | ✓ (cần rà quyền giọng và dữ liệu) |

## 8. Ranh giới thương hiệu và cầu nối

- Web-first, tách khỏi app Lá Lành, ghi "một sản phẩm của Lá Lành".
- Một cầu nối tự nguyện: dòng "Đọc thêm về Sao Thủy trong Lá Lành" dưới Sao Thủy chú thích ở màn lật; link không mang mã phòng, biệt danh hay lựa chọn;
  mở với `noopener noreferrer`; Lá Lành có bước đồng ý riêng của nó; không dữ liệu game nào chuyển sang.
- Báo cáo có nhắc tầng chú thích cá nhân ("Sao Thủy của Lan nghiêng về nói nhẹ…") dùng hồ sơ Lá Lành. PRD này **không** đưa vào vì brief dòng game chốt Lá Úp
  không nhận dữ liệu sinh (TS-D6).

## 9. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Trắc nghiệm trôi quá ít, trò nhạt | **Cao** | Phương án gần đúng có chủ đích; đổi giọng là nguồn trôi chính; đo phân bố độ thất bản ở playtest; sửa ngân hàng trước khi dựng |
| Bản chat chuỗi đứng vì ít người | Trung bình | Nhận lượt tự do, hạn chót 3 giờ, Bot điền, chuỗi tối thiểu 4, giờ lật cố định; chỉ vào MVP nếu đạt D4 |
| Biệt danh xúc phạm | Trung bình | Bộ lọc biệt danh, host đổi tên/gỡ, báo cáo |
| Thẻ lật lan ra ngoài nhóm kèm biệt danh | Trung bình | Biệt danh trên thẻ chỉ khi đồng ý (mặc định "Người chơi A"); thẻ không có link mời hay token |
| Phương án [sắc thái] bị đọc thành chê người | Thấp | Sắc thái gắn với giọng hư cấu (cô hàng xóm, sếp, MC); không nhắm ai trong phòng |
| Giọng "Sếp gửi mail" làm người văn phòng ngại | Thấp | Sếp chung chung; có thể tắt giọng theo gói (sau MVP) |
| Lượt "đọc to" làm người ngại bị ép | Thấp | Host bật mới có; mỗi người bỏ qua được; không ghi âm |
| Bắt chước giọng nhân vật có thật / sở hữu trí tuệ | Thấp | Giọng là kiểu người chung (MC, sếp), không tên người thật, không giọng chương trình truyền hình cụ thể |

## 10. Quyết định chờ owner

Các mục là **"Đề xuất — chờ owner"**, chưa phải quyết định. Mã TS- là quyết định riêng của trò này.

| # | Câu hỏi | Đề xuất mặc định |
|---|---|---|
| D1 | Tên thương hiệu phụ | Lá Úp |
| D4 | Bản chat có vào MVP không | Chỉ khi playtest giấy đạt ≥ 70% chuỗi có ≥ 4 lượt người làm trước giờ lật và nhóm tự xin chơi lại |
| D7 | AI ở MVP | Không. Bot Sao Thủy là chọn ngẫu nhiên có nhãn |
| TS-D1 | Màn lật hiện độ thất bản bằng gì | Nhãn chữ 5 mức (§4.3), không con số |
| TS-D2 | Biệt danh khi lật | Hai lựa chọn riêng, đều không tick sẵn: (a) hiện biệt danh khi phát lại cho người trong phòng/nhóm; (b) cho biệt danh nằm trên thẻ lật để chia sẻ ra ngoài. Không tick thì hiện "Người chơi A, B…". Đổi lại được tới khi lật |
| TS-D3 | Bàn/nhóm 4 người | Bước 4 (Nói lại) do Bot điền, có nhãn |
| TS-D4 | Thời gian bản chat | Hạn chót lượt 3 giờ, giữ lượt 10 phút, giờ lật trong 2–48 giờ, xoá 48 giờ sau lật |
| TS-D5 | Lượt "đọc to" | Tắt mặc định; host bật cho phòng; mỗi người bỏ qua được |
| TS-D6 | Chú thích Sao Thủy cá nhân | Không làm trong Lá Úp |

## 11. Bàn giao

- **SRS/dev:** SRS định nghĩa xoay vòng, ghép phương án, máy trạng thái, dữ liệu, xoá, bảo mật.
- **Hạ tầng phòng chung (Writer B):** Tam Sao cần từ nền tảng: vào phòng bằng QR/mã, phiên host/người chơi, màn hình chung, kênh thời gian thực, nút host, màn tiêu huỷ
  hồ sơ, hết hạn cứng 2 giờ. Tam Sao thêm: dòng đồng ý "biệt danh trên thẻ lật", chia bàn, Bot Sao Thủy, nhận lượt cho bản chat.
- **DPIA/store (Writer D, E):** danh mục dữ liệu SRS §6, bản nháp màn đồng ý SRS §8.2; các cột [bổ sung] cần ghi nhận.
- **Playtest (Writer F):** hai buổi. Trực tiếp: 8–12 người, thẻ in sẵn phương án, mỗi người một phong bì chuỗi, host đọc màn lật từ bảng tổng hợp. Chat: 5–6 người trong
  một nhóm Zalo thật, 24 giờ, host gửi riêng từng lượt bằng ảnh thẻ, tự làm Bot Sao Thủy khi quá hạn, gửi thẻ lật lúc 21:00. Đo: phân bố độ thất bản, tỷ lệ chuỗi đủ
  4 lượt, có xin chơi lại không. Không dùng Google Form gắn tên; phiếu ghi số thứ tự và huỷ sau buổi.
- **Owner:** duyệt văn phong §4.4 và §5, chốt D4, D7, TS-D1–TS-D6.

## 12. Bàn giao theo AGENTS.md

**Nguồn đã kiểm tra:** báo cáo "Chốt năm trò" (phần Tam Sao, bảy trò, quyết định chờ chủ, bàn giao); `relay_games_chat_vs_live.md`; `AGENTS.md`;
plan 23/10/2026; chuẩn nội dung tiếng Việt; `privacy-security-flow-notes.md`; trang Apple App Review Guidelines (đọc lại 26/10/2026, 1.1.1, 1.2, 4.7).

**Phát hiện đã sửa trong thiết kế:** (1) biệt danh khi phát lại và trên thẻ lật chuyển sang hai đồng ý riêng, mặc định ẩn (báo cáo: "chỉ có biệt danh người chơi tự đặt"); bỏ thông báo đẩy ở bản chat để không phải lưu địa chỉ nhận thông báo; (2) bàn 4 người
không đủ người cho 5 bước → Bot điền bước 4; (3) bước 5 trước đây chỉ có nhiễu của câu gốc, nên đoán sai gần như không xảy ra khi bước 4 đã lệch ý định → thêm câu gốc
của ý định bước 4 vào phương án; (4) đề "chúc mừng qua môn" đổi để tránh chủ đề kết quả thi; (5) chú thích Sao Thủy cá nhân loại khỏi Lá Úp; (6) "mood" ghi rõ là cảm
xúc của câu nhắn, không phải tâm trạng người chơi.

**Rủi ro chưa giải quyết:** độ trôi của trắc nghiệm chưa được kiểm chứng; phân loại G1 theo Nghị định 147/2024/NĐ-CP chưa có ý kiến luật sư; nút chặn người theo Apple 1.2
(khi UGC chỉ là biệt danh) chưa có kết luận; ngân hàng còn thiếu ~44 thông điệp gốc và 4 giọng còn lại cho mỗi ý định.

**AC/DoD còn thiếu:** owner chưa duyệt nội dung và D-codes; chưa playtest giấy; DPIA, chính sách quyền riêng tư và nhãn store chưa cập nhật cho trò này.
