# Hết Cứu % — PRD

> Phiên bản: 0.1 (nháp) · Cập nhật: 26/10/2026 · Trạng thái: **chờ chủ sản phẩm duyệt**. Chưa được duyệt để dựng.
> Thuộc dòng game của thương hiệu phụ (đề xuất **Lá Úp**, D1). Giai đoạn hiện tại chỉ làm tài liệu và playtest giấy, không viết code
> (`docs/plans/2026-10-23-privacy-content-game-plan.md`, giai đoạn 3).
> Tài liệu đi cùng: [SRS](het-cuu-phan-tram-srs.md) · user story [G10](../../user-stories/game/G10-tao-nhom-va-moi.md),
> [G11](../../user-stories/game/G11-tu-khai-phan-tram-va-dat-la.md), [G12](../../user-stories/game/G12-tin-nong-giua-tuan.md),
> [G13](../../user-stories/game/G13-man-lat-thu-sau.md), [G14](../../user-stories/game/G14-tong-ket-mua.md),
> [G15](../../user-stories/game/G15-quyen-rieng-tu-cua-toi.md), [G16](../../user-stories/game/G16-nhan-vat-chinh-tu-nguyen.md).
> Tài liệu chung của cả dòng game (người khác viết): `shared-room-platform-srs.md`, DPIA `docs/legal/2026-10-26-game-line-dpia.md`,
> bản nháp store/chính sách `docs/legal/2026-10-26-game-line-store-privacy-and-policy-draft.md`, playtest `docs/playtests/2026-11-game-line/`.

---

## 0. Tóm tắt một đoạn

Mỗi thứ Hai, một nhóm bạn kín (4–12 người, từ 18 tuổi) nhận một **sự kiện bựa hư cấu**, ví dụ "kẹt thang máy 2 tiếng cùng sếp tổng",
với ba mức hành động leo thang: bình thường → bựa → hết cứu. Đến hết thứ Năm, mỗi người **tự khai kín** mình có bao nhiêu phần trăm
sẽ làm từng mức, chọn một thẻ "lời khai" soạn sẵn, rồi đoán xem ai trong nhóm khai cao nhất ở mỗi mức và đặt "lá" theo độ tự tin.
Tối thứ Sáu là **màn lật**: từng mức hiện ai khai cao nhất, ai lừa được cả hội, ai đọc vị giỏi. Nếu tuần đó có **Nhân Vật Chính**
tự nguyện, màn lật có ba nhịp: "Bạn tự khai 5%… cả hội đoán 92%… lệch 87, HẾT CỨU". 72 giờ sau màn lật, mọi con số thô bị xoá.
Không có tiền, không quy đổi, không streak, không bảng xếp hạng người.

## 1. Bối cảnh và bằng chứng

Nguồn chính: báo cáo "Chốt năm trò, giữ trọn chữ Lành" (26/10/2026, phần "Hết Cứu %") và ghi chú nghiên cứu
`research_notes/Chốt trò chơi nhóm Lá Lành/most_likely_percentage_games.md`. Các điểm dưới đây chép lại để PRD tự đứng được.

| Bằng chứng | Ý nghĩa cho thiết kế | Độ tin |
|---|---|---|
| Chưa có trò lớn nào ghép "tự khai %" với "đoán ai khai cao nhất". Trò nằm giữa Wavelength (đoán trên thang; nhà phát hành tuyên bố >150.000 bộ, >5 triệu lượt tải), Wits & Wagers (cược vào câu trả lời của người khác), Psych!/Fibbage (ghi điểm khi lừa được bạn), tbh/Gas (khảo sát soạn sẵn về bạn bè) | Vay cơ chế đã kiểm chứng, không phát minh lại | Tuyên bố của công ty / thứ cấp |
| Guesspionage (Jackbox Party Pack 3) cho đoán % về người lạ và bị chê "nhanh chán, khó gây cười" (KeenGamer) | % phải nói về **người trong phòng** | Thứ cấp |
| Hiệu ứng "tôi hơn trung bình": tổng hợp >950.000 người, hiệu ứng mạnh, ổn định (Zell et al. 2020) | Người ta tự khai thấp hành vi "xấu hổ" → có khoảng lệch để cười | Sơ cấp |
| Bạn thân đoán hành vi nhìn thấy được chính xác ngang bản thân (Vazire & Mehl 2008; APS Observer) | Đề chỉ nói về hành vi nhìn thấy được, vô hại | Sơ cấp |
| Lý thuyết vi phạm lành tính (McGraw & Warren): buồn cười khi sai lệch nhưng an toàn | Leo thang ba mức trong tình huống giả định; tránh đề đạo đức/năng lực | Sơ cấp (phòng thí nghiệm) |
| Wordle: một lượt mỗi ngày tạo khan hiếm. BeReal: lịch hằng ngày thành gánh nặng, DAU rơi ~15 triệu → ~6 triệu (nguồn mâu thuẫn) | Chọn **nhịp tuần**, cửa sổ 72 giờ, có tuần nghỉ, mùa 8 tuần | Thứ cấp |
| Sarahah bị gỡ khỏi hai chợ ứng dụng năm 2018 sau tin nhắn ẩn danh xúi tự tử; tbh đóng sau 9 tháng, Gas đóng chưa tới 1 năm sau khi bị mua; Gas bán "ai đã chọn bạn" thành tính năng trả phí | Không chữ tự do, không lộ ai đoán ai, không thu phí tò mò, nhóm kín 18+ | Thứ cấp |
| Apple 1.2: app chủ yếu dùng cho chat ẩn danh, chấm điểm người thật kiểu "hot-or-not", bắt nạt có thể bị gỡ không báo trước; 1.1.1: nội dung nhằm làm nhục một người cụ thể bị cấm, dán nhãn "để giải trí" không giúp thoát (đối chiếu trang Apple ngày 26/10/2026) | Người chơi **tự khai về chính mình** trước tình huống hư cấu; không ai chấm điểm ai | Sơ cấp |
| Meme "giỡn mà thật" của Gen Z Việt (RMIT 2025–2026); meme/trang nhại là nhóm tài khoản được theo dõi nhiều thứ hai (28,7%) | Giọng tự trào, phóng đại đời thường; tách gói trường và gói văn phòng | Học thuật–tổ chức |
| Nhãn "hết cứu" (FPT Shop) | Cần kiểm tra chữ với 5–10 người thật | **Yếu** |

Bối cảnh sản phẩm: Lá Lành là "nơi tìm được những giây phút thư giãn bình yên, vui vẻ, những khoảnh khắc giúp bạn cảm giác được hiểu".
Hết Cứu % là **trò hằng tuần** của dòng game và là trò rẻ nhất để playtest và dựng (không cần thời gian thực, đề soạn sẵn,
dữ liệu ít).

## 2. Mục tiêu, phi mục tiêu và nguyên tắc

### 2.1. Mục tiêu

- **G1.** Một nhóm bạn có một cuộc hẹn vui mỗi tuần (màn lật thứ Sáu) mà không thấy bị ép quay lại.
- **G2.** Mỗi màn lật có ít nhất một khoảnh khắc cười to: khoảng lệch giữa tự khai và cái nhìn của cả hội.
- **G3.** Không ai thấy mình bị nhắm vào. Số báo cáo "bị nhắm vào" mục tiêu bằng 0.
- **G4.** Dữ liệu ít và ngắn hạn: không tài khoản, chỉ biệt danh, số thô xoá sau 72 giờ.

### 2.2. Phi mục tiêu

- Không bảng xếp hạng người, không điểm cộng dồn qua tuần, không "ai đã đoán bạn", không "ai chọn bạn".
- Không tiền thật, không vật phẩm mua bán, không quy đổi "lá" ra bất cứ thứ gì, không cửa hàng, không quảng cáo.
- Không streak, không đếm tuần đã bỏ lỡ, không thông báo kiểu "bạn chưa khai".
- Không chữ tự do ngoài biệt danh; không chat, không bình luận, không nhắn riêng.
- Không đề do người dùng viết ở MVP.
- Không ngày sinh, giờ sinh, nơi sinh, không chú thích chiêm tinh cá nhân trong Lá Úp (khác báo cáo, xem §8 và HC-D1).
- Không AI/LLM ở MVP.
- Không bản cho người dưới 18 tuổi; không trang khám phá nhóm công khai.

### 2.3. Nguyên tắc

1. **Tự khai về mình, đoán về con số.** Không có câu hỏi "ai là người…"; chỉ có "bạn có bao nhiêu % sẽ…" và "ai đã khai cao nhất".
2. **Chọc tình huống, không chọc người.** Danh hiệu là "siêu năng lực", không phải lỗi.
3. **Lá chỉ sống trong một sự kiện.** Hết sự kiện là hết lá, hết điểm (D3).
4. **Có lối thoát mọi lúc:** "ẩn % của tôi", "tuần này đừng đoán tôi", rời nhóm, xoá dữ liệu của tôi, nghỉ tuần.
5. **Đóng hồ sơ sau màn lật.** Con số thô xoá sau 72 giờ; nhóm chỉ giữ danh hiệu và khoảnh khắc.

## 3. Người dùng và bối cảnh dùng

| Persona | Mô tả | Cần gì | Lo gì |
|---|---|---|---|
| **Minh, 20 tuổi, sinh viên năm 2** | Có nhóm Zalo lớp và nhóm bạn thân 6 người; hay gửi meme | Một trò để cả nhóm có chuyện nói mỗi tuần, cười chung tối thứ Sáu | Bị cả lớp "bóc"; trò bắt tải app, đăng ký |
| **Chị Thảo, 27 tuổi, nhân viên văn phòng** | Nhóm phòng ban 9 người, có sếp trực tiếp trong nhóm | Trò nhẹ cho phòng ban, không đụng chuyện lương, sếp, đời tư | Bị hiểu sai trước sếp; dữ liệu nằm lại lâu |
| **Host (người tạo nhóm)** | Thường là người hay rủ rê trong nhóm | Tạo nhóm trong một phút, gửi link vào nhóm chat, kick người lạ | Phải quản lý quá nhiều; link bị lan ra ngoài |

Tất cả người chơi từ 18 tuổi trở lên (tự xác nhận). Không có tài khoản: mỗi người là một **phiên thiết bị** cộng biệt danh.

## 4. Luật chơi chốt

### 4.1. Nhịp tuần (giờ Việt Nam, Asia/Ho_Chi_Minh)

| Thời điểm | Diễn biến | Người chơi làm gì | Story |
|---|---|---|---|
| Thứ Hai 9:00 | Thả **thẻ sự kiện**: tranh minh hoạ, ba mức hành động, "lá của tuần" (tarot, không dùng dữ liệu cá nhân) | Mở thẻ; host có thể gửi link vào nhóm chat | G11 |
| Thứ Hai 9:00 → thứ Năm 9:00 (72 giờ) | Cửa sổ tự khai kín | Đặt % mỗi mức (bước 5%), chọn một thẻ lời khai, đoán ai khai cao nhất mỗi mức và đặt lá; tuỳ chọn tình nguyện làm Nhân Vật Chính hoặc đoán % của Nhân Vật Chính | G11, G16 |
| Thứ Tư 12:00 (**sau MVP**) | Tin nóng giữa tuần: sự kiện có thêm một chi tiết | Được sửa **một** con số | G12 |
| Thứ Năm 9:00 → thứ Sáu 20:00 | Khoá câu trả lời, chờ lật | Không làm gì; trang hiện "Kết quả lúc 20:00 thứ Sáu" | G11 |
| Thứ Sáu 20:00 | **Màn lật** | Xem, thả cảm xúc soạn sẵn, chia sẻ thẻ danh hiệu nếu muốn | G13, G16 |
| Thứ Hai 20:00 tuần sau (lật + 72 giờ) | Xoá %, phiếu đoán, lá, điểm của sự kiện | — | G13, G15 |
| Sau sự kiện thứ 8 | **Tổng kết mùa** trong nhóm | Xem danh hiệu, khoảnh khắc; host chọn nghỉ một tuần hoặc sang mùa mới | G14 |

Lưu ý: cửa sổ khai đóng thứ Năm 9:00 theo báo cáo (72 giờ từ thứ Hai 9:00). Khoảng chờ thứ Năm → thứ Sáu là chủ ý để màn lật thành cuộc hẹn.

### 4.2. Từng bước trong một sự kiện

1. **Tự khai %.** Với mỗi mức 1, 2, 3: thanh trượt 0–100%, bước 5%. Không có giá trị mặc định được tính là đã khai; người chơi phải chạm vào thanh.
2. **Thẻ lời khai.** Chọn một thẻ soạn sẵn cho mức mình khai cao nhất (nếu hoà, mức cao hơn được chọn). Thẻ được đọc to ở màn lật nếu mình khai cao nhất ở mức đó.
3. **Đoán và đặt lá.** Với mỗi mức, chọn một thành viên mình đoán là khai cao nhất (không chọn chính mình) và đặt lá lên phiếu đó. Mỗi người có **3 lá cho cả sự kiện**. Phiếu đoán phải có ít nhất 1 lá; tổng lá đặt không quá 3. Bỏ qua một mức được.
4. **Nhân Vật Chính (tuỳ chọn, D8).** Nếu tuần này có người tình nguyện, người khác ước lượng % người đó khai ở mức 3.
5. **Nộp.** Có thể sửa cho tới khi cửa sổ đóng.

Điều kiện để sự kiện có phần đoán: ít nhất **3 thành viên có thể bị đoán** (đã tự khai và không bật "đừng đoán tôi"). Nếu không đủ, sự kiện chạy ở chế độ "chỉ tự khai": màn lật chỉ hiện thẻ lời khai và số người tham gia, không chấm điểm (SRS HC-FR-24).

### 4.3. Chấm điểm trong một sự kiện (đề xuất mặc định cho D3)

| Hành động | Điểm |
|---|---|
| Đoán đúng ai khai cao nhất ở một mức (hoà thì ai trong nhóm cao nhất cũng tính) | + số lá đã đặt vào phiếu đó |
| Đoán sai | − số lá đã đặt; điểm sự kiện không xuống dưới 0 |
| **Lừa cả hội:** mình khai cao nhất ở một mức nhưng không quá 1/3 số người đoán mức đó đoán ra mình | +3 |
| **Đọc vị:** ước lượng % mức 3 của Nhân Vật Chính lệch không quá 10 điểm | +2 |

Điểm chỉ để chọn danh hiệu của **sự kiện này**. Mỗi người chỉ thấy điểm của chính mình. Điểm xoá cùng số thô sau 72 giờ.

**Khác với báo cáo (cần owner chốt D3):** báo cáo đề xuất "mỗi đầu tháng nhận lại 10 lá" và điểm theo mùa. Cách đó tạo một nền kinh tế
lá cộng dồn và một bảng điểm mùa, trái với nguyên tắc đã có test "không coin/XP, không streak, không áp lực quay lại"
(`apps/web/src/shared/ui/companion/growth.test.ts`). Mặc định trong PRD này:

- 3 lá mỗi sự kiện, không mang sang sự kiện sau, không nạp lại, không mua, không tặng, không cửa hàng.
- Điểm reset mỗi sự kiện; không có tổng điểm mùa; tổng kết mùa chỉ có danh hiệu và khoảnh khắc.
- Bỏ một tuần không mất gì, không bị nhắc.

Phương án dự phòng nếu "đặt lá" có rủi ro bị xếp vào "mô phỏng cờ bạc": bỏ lá, chỉ đoán kèm nhãn độ chắc ("chắc chắn / hơi chắc / đoán bừa"), không cộng trừ điểm,
danh hiệu Thầy Đọc Vị tính bằng số mức đoán đúng (xem D3).

### 4.4. Danh hiệu của sự kiện

| Danh hiệu | Trao cho | Ghi chú |
|---|---|---|
| Danh hiệu mức 3 của sự kiện (ví dụ "Vua Bolero Thang Máy") | Người khai cao nhất ở mức 3 | Lấy từ ngân hàng sự kiện; không trao cho người bật "đừng đoán tôi" (họ không khai) |
| **Thánh Lừa** | Người có điểm "lừa cả hội" cao nhất | Hoà thì cùng nhận |
| **Thầy Đọc Vị** | Người có điểm sự kiện cao nhất từ đoán và đọc vị | Hoà thì cùng nhận; cần điểm > 0 |
| **Hết Cứu** | Nhân Vật Chính khi lệch ≥ 50 điểm | Chỉ khi có Nhân Vật Chính |

Không có danh hiệu tiêu cực, không có "người khai thấp nhất", không có "người đoán tệ nhất".

### 4.5. Mùa

- Một mùa = 8 sự kiện. Host có thể cho nhóm **nghỉ một tuần** bất kỳ lúc nào trước thứ Hai 9:00; tuần nghỉ không tính vào 8.
- Tổng kết mùa: danh hiệu từng tuần, "khoảnh khắc hết cứu nhất" (chỉ khi Nhân Vật Chính đồng ý giữ, G16), và chiếu lại một sự kiện cũ thành sự kiện mới của mùa sau.
- **Khác báo cáo:** câu "Tuần 3 bạn khai 10%, giờ thì sao?" cần giữ số thô quá 72 giờ, trái với thời hạn lưu. Mặc định: chiếu lại chỉ so với khoảnh khắc đã được giữ có đồng ý, không so với số thô (G14).

## 5. Nội dung

Mọi nội dung dưới đây là **nháp, chờ owner duyệt văn phong**. Áp dụng `docs/foundation/la-lanh-plain-vietnamese-content-standard.md`
(giọng Cà khịa: chọc hành vi, không chọc người, không chửi thề, không định mệnh) và danh sách chủ đề cấm ở §5.5.

### 5.1. Ngân hàng 20 sự kiện mẫu (19 từ báo cáo, #20 viết mới; MVP cần 24 sự kiện, còn thiếu 4)

Mọi sự kiện đều hư cấu. "Sếp" luôn là sếp chung chung.

| # | Gói | Sự kiện | Mức 1: bình thường | Mức 2: bựa | Mức 3: hết cứu |
|---|---|---|---|---|---|
| 1 | Văn phòng | Kẹt thang máy 2 tiếng cùng sếp tổng | Bắt chuyện thời tiết suốt 2 tiếng | Rủ sếp song ca bolero | Mở "Đêm nhạc Thang Máy", phát vé mời cho cả toà nhà |
| 2 | Văn phòng | Filter củ khoai tây tự bật đúng lúc bạn báo cáo quý trên Zoom | Giả vờ mạng lag | Báo cáo tiếp tới hết slide bằng giọng nghiêm túc nhất đời | Đề xuất cả phòng bật filter khoai tây "cho đồng bộ nhận diện" |
| 3 | Văn phòng | Máy in tự in 200 trang chữ "CỨU TÔI" | Rút phích, coi như không thấy | In lại một trang "ĐANG TỚI" để trấn an máy | Đặt tên máy in, lập fanpage, nhận nuôi chính thức |
| 4 | Văn phòng | Bạn gửi nhầm voice 4 phút hát karaoke vào nhóm chat toàn công ty | Thu hồi rồi im lặng | Gửi thêm bản remix "cho đủ bộ" | Mở series "Thứ Sáu hát cho cả công ty nghe" |
| 5 | Văn phòng | Team building đổi thành flashmob trước toà nhà lúc 7h sáng | Đứng hàng cuối, nhảy 30% công suất | Lên hàng đầu, nhảy 100% | Tự phong biên đạo, bắt cả phòng tập thêm 3 buổi |
| 6 | Văn phòng | Wifi sập cả ngày, chỉ góc pantry cạnh nồi cơm còn sóng | Dời laptop ra pantry | Họp online đội nồi cơm "cho tăng sóng" | Treo biển "Chi nhánh Pantry", tự nhận trưởng chi nhánh |
| 7 | Văn phòng | Bốc thăm tất niên trúng danh hiệu "Sếp Nhí 1 ngày" | Từ chối khéo | Nhận, in danh thiếp "Sếp Nhí" | Ban hành nội quy đầu tiên: thứ Hai mặc đồ ngủ đi làm |
| 8 | Văn phòng | Robot hút bụi công ty "nổi loạn", đi theo bạn cả ngày | Đi đường vòng để né | Đặt tên, dắt robot đi họp | Làm đơn xin cấp thẻ nhân viên cho robot |
| 9 | Văn phòng | Kẹt trong phòng họp kính, cả tầng nhìn thấy nhưng không ai nghe thấy | Gõ cửa kính lịch sự | Viết chữ ngược lên bảng trắng cầu cứu | Diễn kịch câm 20 phút kể lại cả cuộc đời |
| 10 | Trường | Giảng viên điểm danh bằng cách đọc lái tên cả lớp | Giơ tay nhầm một lần | Đổi luôn tên Zalo theo kiểu lái | Đề nghị cả lớp xưng hô bằng tên lái tới hết kỳ |
| 11 | Trường | Một con mèo ngủ trên bàn giảng viên đúng giờ bạn thuyết trình | Thuyết trình nhỏ giọng cho mèo ngủ | Ghi tên mèo làm đồng tác giả trên slide | Xin thầy cho mèo điểm cộng chuyên cần |
| 12 | Trường | Căn tin chỉ còn một ổ bánh mì, 30 người đang xếp hàng | Nhường | Đề xuất chia 30 phần bằng thước kẻ | Tổ chức "đấu giá bằng hát" để quyết định |
| 13 | Trường | Ký túc xá cúp điện cả đêm, điện thoại còn 20% pin | Đi ngủ sớm | Rủ cả phòng kể chuyện ma bằng đèn pin | Mở "đêm nhạc acoustic hành lang", mời cả tầng |
| 14 | Trường | Bị thêm nhầm vào nhóm Zalo "CLB đờn ca tài tử phường" | Rời nhóm ngay | Ở lại nghe 3 ngày cho biết | Nhận lời biểu diễn ở buổi sinh hoạt tháng sau |
| 15 | Trường | Xe buýt trường đi nhầm tuyến, chở cả lớp ra tới Vũng Tàu | Xin xuống bắt xe về | Mở bản đồ dẫn đường cho tài xế | Biến luôn thành "dã ngoại bất đắc dĩ", lập lịch trình 2 ngày |
| 16 | Trường | Giảng viên lỡ bật giọng chipmunk suốt buổi học online | Tắt cam để cười | Xin ghi âm làm nhạc chuông | Đặt câu hỏi bằng giọng chipmunk "cho đồng bộ" |
| 17 | Trường | Group project 5 người, tới 23:58 chỉ có mình bạn online | Tự làm nốt, im lặng nộp | Gửi voice 7 phút "diễn văn đêm khuya" | Nộp bài kèm "Phụ lục: Nhật ký một mình" dài 20 trang |
| 18 | Chung | Sáng dậy bạn hiểu được tiếng chim bồ câu, chỉ trong 24 giờ | Giữ bí mật | Phỏng vấn đàn bồ câu ở công viên | Nhận làm phiên dịch cho "Hội nghị Bồ câu toàn quốc" |
| 19 | Chung | Shipper giao tới 47 hộp sữa chua đã thanh toán sẵn, không rõ ai đặt | Gửi lại shipper | Nhận và chia cả tầng | Mở "Lễ hội Sữa chua" có ban tổ chức và áo đồng phục |
| 20 | Văn phòng | Cổng quẹt thẻ ở sảnh nhận nhầm bạn là khách VIP, mỗi lần bạn đi qua lại bật nhạc chào mừng | Đi cổng phụ cho đỡ ngại | Đi qua thật chậm, vẫy tay chào cả sảnh | Trải thảm đỏ từ cổng tới thang máy, nhờ lễ tân đọc lời giới thiệu mỗi sáng |

Ghi chú rà soát chủ đề (đề xuất, owner quyết):

- #13 "kể chuyện ma": ma ở đây là chuyện kể vui, không phải chủ đề kinh dị chính; giữ.
- #19 "đã thanh toán sẵn": nhắc tới thanh toán nhưng không phải tiền của người chơi; giữ, theo dõi khi kiểm tra chữ.
- #20 viết mới (26/10/2026), thay sự kiện "mẹ gọi video lúc thuyết trình" của báo cáo, vì nhân vật "mẹ" chạm chủ đề gia đình nằm trong danh sách cấm ở §5.5 và brief. Cổng quẹt thẻ là máy, không nhắm ai; không chạm ngoại hình hay tiền. Kiểm tra chữ cùng các đề khác.
- #7 "mặc đồ ngủ đi làm": không chạm ngoại hình hay cơ thể; giữ.

### 5.2. Lớp nội dung đi kèm từng sự kiện (nháp mới, ngoài báo cáo)

| # | Danh hiệu mức 3 | Lá của tuần (tarot, chỉ là gia vị) | Tin nóng giữa tuần (sau MVP, G12) |
|---|---|---|---|
| 1 | Vua Bolero Thang Máy | The Fool | Cập nhật: sếp vừa hỏi bạn có biết bài "Duyên phận" không. *(từ báo cáo)* |
| 2 | Khoai Tây Trưởng Phòng | The Magician | Cập nhật: khách hàng cũng vừa bật filter củ cà rốt. |
| 3 | Bảo Mẫu Máy In | The Hermit | Cập nhật: máy in vừa in thêm một trang "CẢM ƠN". |
| 4 | Ca Sĩ Nội Bộ | The Star | Cập nhật: phòng nhân sự vừa thả tim voice của bạn. |
| 5 | Biên Đạo 7 Giờ Sáng | Strength | Cập nhật: bảo vệ toà nhà xin nhảy cùng. |
| 6 | Trưởng Chi Nhánh Pantry | The Emperor | Cập nhật: nồi cơm vừa bật chế độ hâm nóng, sóng mạnh thêm một vạch. |
| 7 | Sếp Nhí Ban Hành | The Chariot | Cập nhật: sếp thật xin được làm trợ lý cho Sếp Nhí. |
| 8 | Bạn Thân Robot | The Lovers *(đề xuất đổi: Wheel of Fortune, tránh gợi tình cảm)* | Cập nhật: robot vừa học được cách mở cửa phòng họp. |
| 9 | Diễn Viên Kính | The Hanged Man | Cập nhật: cả tầng bắt đầu giơ bảng chấm điểm diễn xuất. |
| 10 | Thủ Lĩnh Tên Lái | Judgement | Cập nhật: thầy vừa đọc lái luôn tên môn học. |
| 11 | Đồng Tác Giả Của Mèo | The High Priestess | Cập nhật: mèo vừa thức dậy và nhìn thẳng vào slide của bạn. |
| 12 | Trọng Tài Bánh Mì | Justice | Cập nhật: cô căn tin tìm thấy thêm nửa ổ. |
| 13 | DJ Hành Lang | The Moon | Cập nhật: phòng bên cạnh mang tới một cây đàn ukulele. |
| 14 | Nghệ Sĩ Phường Nhận Nuôi | Temperance | Cập nhật: chủ nhiệm CLB vừa gửi bạn bản nhạc để tập. |
| 15 | Hướng Dẫn Viên Bất Đắc Dĩ | The World | Cập nhật: tài xế nói còn đủ xăng ra tới Phan Thiết. *(từ báo cáo)* |
| 16 | Chipmunk Danh Dự | The Sun | Cập nhật: thầy hỏi cả lớp có nghe rõ không, bằng giọng chipmunk. |
| 17 | Người Gánh Cả Team | The Tower | Cập nhật: một bạn trong nhóm vừa online lúc 23:59 và thả một chữ "ok". |
| 18 | Phiên Dịch Bồ Câu | The Empress | Cập nhật: đàn bồ câu vừa nhờ bạn chuyển lời tới đàn quạ. |
| 19 | Trưởng Ban Sữa Chua | Ace of Cups | Cập nhật: shipper quay lại với thêm 12 hộp. |
| 20 | Khách VIP Cổng Quẹt Thẻ | Four of Wands | Cập nhật: cổng vừa đổi sang bài nhạc thứ hai, dài gấp đôi. |

Quy tắc cho "lá của tuần": chỉ nói lá này là lá gì và gắn với tình huống thế nào. **Không** viết "lá đã báo trước" hay bất kỳ câu dự đoán nào
(sửa so với báo cáo, theo chuẩn nội dung "không dự đoán"). Mẫu: "Lá của tuần: The Fool, lá của người dám bước vào chuyện lạ."

### 5.3. Thẻ lời khai (nháp, 10 thẻ)

1. "Tôi chỉ làm theo vũ trụ." *(báo cáo)*
2. "Lúc đó tôi đói." *(báo cáo)*
3. "Đây là chiến lược dài hạn." *(báo cáo)*
4. "Tôi tưởng đây là buổi tập."
5. "Không ai cản tôi cả."
6. "Tôi làm vì tập thể."
7. "Tôi chỉ đi ngang qua thôi."
8. "Cơ hội chỉ đến một lần."
9. "Tôi đã suy nghĩ rất kỹ trong 3 giây."
10. "Vì đồng đội."

### 5.4. Chữ trên màn lật (nháp)

- Mức: "Mức 3 · hết cứu: người khai cao nhất là **{biệt danh}** với **{%}**." Nếu người đó bật "ẩn %": "… với mức **cao**."
- Lừa cả hội: "**{biệt danh}** khai cao nhất mà chỉ {k}/{n} người đoán ra. Thánh Lừa tuần này."
- Nhân Vật Chính: "{biệt danh} tự khai **{a}%**… cả hội đoán **{b}%**… lệch **{|a−b|}**." Nhãn: lệch ≥ 50 "HẾT CỨU"; 20–49 "Cứu được chút"; < 20 "Tự biết mình ghê".
- Chế độ chỉ tự khai: "Tuần này chưa đủ người để đoán. Đây là các thẻ lời khai của nhóm."

### 5.5. Chủ đề cấm trong mọi sự kiện, thẻ và danh hiệu

Ngoại hình và cơ thể; tình dục và giới; sức khoẻ (thể chất, tinh thần, mang thai, khuyết tật); phạm pháp; ngoại tình, người yêu cũ,
quan hệ tình cảm thật; tiền và lương; gia đình nhạy cảm; tôn giáo; vùng miền; dân tộc; chính trị; sếp hay đồng nghiệp có tên thật;
người thật có tên; tự hại; thử thách có rượu bia; thử thách ngoài đời thật. Không đoán sức khoẻ tinh thần, xu hướng tính dục, sang chấn,
ngoại tình, danh tính crush, kết quả thi hay "ai toxic".

## 6. Chỉ số

Chỉ dùng số đếm tổng hợp ở máy chủ, không SDK phân tích bên thứ ba, không gắn với biệt danh hay phiên.

| Chỉ số | Cách đo | Ngưỡng quan sát (đề xuất) |
|---|---|---|
| Tỷ lệ thành viên tự khai mỗi tuần | số người đã nộp / số thành viên đầu sự kiện, theo nhóm, rồi lấy trung vị | ≥ 2/3 ở tuần 3 (quy tắc chốt playtest) |
| Tỷ lệ nhóm đi tới màn lật | số sự kiện có màn lật / số sự kiện đã thả | — |
| Tỷ lệ nhóm còn chơi ở tuần 2, 4, 8 | đếm nhóm có ≥ 3 người nộp ở sự kiện thứ k | — |
| Lượt dùng "ẩn %" và "đừng đoán tôi" | số đếm theo sự kiện | Chỉ báo khó chịu; tăng đột biến thì rà đề |
| Thành viên mới được mời vào nhóm | số lần tham gia qua link | — |
| Báo cáo "bị nhắm vào" | số báo cáo | **Mục tiêu 0**; ≥ 1 thì rà lại đề tuần đó |
| Số lần chia sẻ thẻ danh hiệu | đếm lần bấm chia sẻ (không ghi đích) | — |

Không đo: thời gian xem từng người, ai đoán ai, tỷ lệ trúng của từng người.

## 7. Phạm vi MVP và sau MVP

| Hạng mục | MVP | Sau MVP |
|---|---|---|
| Nhóm kín 4–12, link mời thu hồi được, host kick | ✓ | |
| Một sự kiện mỗi tuần, ngân hàng 24 sự kiện (đủ 3 tháng), tách gói văn phòng/trường/chung | ✓ | |
| Tự khai, thẻ lời khai, đoán, đặt lá (theo D3), lừa cả hội | ✓ | |
| Màn lật, danh hiệu, thẻ danh hiệu chia sẻ | ✓ | |
| Nhân Vật Chính tự nguyện (D8) | ✓ (báo cáo: đưa vào từ tuần 2 playtest) | |
| Tổng kết mùa (danh hiệu, khoảnh khắc đã đồng ý giữ) | ✓ | |
| "Ẩn %", "đừng đoán tôi", rời nhóm, xoá dữ liệu của tôi, báo cáo | ✓ | |
| Thông báo đẩy tuỳ chọn (≤ 1/tuần mỗi nhóm, câu cố định không tên, không số) | ✓ | |
| Tin nóng giữa tuần | | ✓ (G12) |
| Đề tự tạo theo khuôn, qua hàng chờ kiểm duyệt | | ✓ |
| Bản chạy trực tiếp như một vòng trong sự kiện phòng | | ✓ |
| Chú thích chiêm tinh cá nhân cho Nhân Vật Chính | | Không làm trong Lá Úp (HC-D1) |

## 8. Ranh giới thương hiệu và cầu nối về Lá Lành

- Chạy trên web (PWA/trình duyệt), tách khỏi app Lá Lành, ghi "một sản phẩm của Lá Lành".
- Đúng một cầu nối tự nguyện: **"lá của tuần"** có link "Xem lá này trong Lá Lành". Link không mang mã nhóm, mã phiên, biệt danh,
  sự kiện hay bất kỳ dữ liệu game nào; mở với `Referrer-Policy: no-referrer`. Nếu người chơi dùng Lá Lành, họ đi qua bước đồng ý riêng của
  Lá Lành. Không có dữ liệu game nào chuyển sang Lá Lành.
- Báo cáo có nhắc "chú thích chiêm tinh cá nhân cho Nhân Vật Chính, tắt mặc định". PRD này **không** đưa vào, vì brief của dòng game
  chốt "Lá Úp không bao giờ nhận dữ liệu sinh". Ghi thành HC-D1 để owner xác nhận.

## 9. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Khoảng lệch bị đọc thành lời buộc tội | Cao | Đề chỉ về hành vi nhìn thấy được, vô hại; danh hiệu "siêu năng lực"; "đừng đoán tôi"; báo cáo; rà đề khi có báo cáo |
| "Đặt lá" bị chợ ứng dụng hoặc người dùng hiểu là cá cược | Trung bình | Không tiền, không quy đổi, lá chỉ sống trong một sự kiện; tránh chữ "cược", "kèo"; phương án dự phòng không lá (D3); hỏi luật sư trước khi gói vào app store |
| Nhóm văn phòng có sếp: người ngại bị hiểu sai | Trung bình | Gói văn phòng không đụng năng lực, đạo đức; "ẩn %"; không lộ ai đoán ai |
| Nhóm tắt sau vài tuần (như tbh/Gas) | Trung bình | Nhịp tuần, mùa 8 tuần, tuần nghỉ; không ép quay lại; chấp nhận đây là trò theo mùa |
| Mất phiên thiết bị (xoá dữ liệu trình duyệt, đổi máy) | Trung bình | Vào lại bằng link mời thành thành viên mới; host gỡ thành viên cũ; nói rõ trước khi vào (SRS §5) |
| Link mời bị lan ra ngoài nhóm | Trung bình | Link thu hồi được, có hạn, giới hạn 12 người, host duyệt khi nhóm đã đủ hoặc kick |
| Chữ "hết cứu" không hợp người dùng | Thấp–trung bình | Kiểm tra chữ với 5–10 người (D2) |
| Đề tuần đó chạm chủ đề nhạy cảm của một nhóm cụ thể | Thấp | Owner duyệt từng đề; host được đổi đề trước thứ Hai 9:00 (chọn 1 trong 2 đề) hoặc cho nghỉ tuần |

## 10. Quyết định chờ owner

Các mục dưới đây là **"Đề xuất — chờ owner"**, chưa phải quyết định.

| # | Câu hỏi | Đề xuất mặc định |
|---|---|---|
| D1 | Tên thương hiệu phụ | Lá Úp (thay Lá Đêm) |
| D2 | Tên trò | Hết Cứu %; bỏ "Kèo Bựa" vì gợi cá cược. Kiểm tra chữ với 5–10 người |
| **D3** | Cơ chế lá và điểm | **3 lá mỗi sự kiện, không mang sang, không nạp lại, không cửa hàng; điểm reset mỗi sự kiện; tổng kết mùa chỉ có danh hiệu và khoảnh khắc; không bảng xếp hạng người cộng dồn.** Mâu thuẫn với báo cáo (10 lá nạp lại mỗi tháng, điểm mùa) được giải theo nguyên tắc "không coin/XP, không streak, không áp lực quay lại". Trước khi gói vào app store: hỏi luật sư và đối chiếu câu hỏi "Simulated Gambling" trong bảng xếp hạng tuổi của Apple và chính sách cờ bạc của Google Play. Dự phòng: bỏ lá, chỉ nhãn độ chắc |
| D8 | Nhân Vật Chính | Chỉ người tự nguyện, mỗi tuần tối đa một người, không ai bị chỉ định, không ai làm hai tuần liền nếu còn người khác tình nguyện |
| HC-D1 | Chú thích chiêm tinh cá nhân cho Nhân Vật Chính (báo cáo) | Không làm trong Lá Úp; chỉ giữ "lá của tuần" không dùng dữ liệu cá nhân |
| HC-D2 | Số thông báo mỗi tuần | Tối đa 1 cho mỗi nhóm, tự bật, câu cố định không biệt danh, không con số (HC-FR-53–56; báo cáo đề xuất 3: thả đề, nhắc, lật). Người chơi chọn nhận lúc thả đề (thứ Hai) hoặc lúc lật (thứ Sáu); không có thông báo nhắc |
| HC-D3 | Màn lật hiện những số nào | Chỉ % của người khai cao nhất từng mức (hoặc dải nếu họ ẩn) và số đếm "k/n người đoán đúng". Không hiện % của người khác |
| HC-D4 | Thời gian sống của nhóm khi không còn chơi | Nhóm và danh sách thành viên xoá khi mùa kết thúc + 30 ngày mà không có mùa mới; nhóm không có ai nộp trong 4 sự kiện liền thì tự tạm dừng thả đề. Cần DPIA ghi nhận |
| HC-D5 | Tin nóng giữa tuần | Sau MVP, đúng như báo cáo |

## 11. Bàn giao

- **Cho SRS và dev (giai đoạn 3):** SRS định nghĩa yêu cầu chức năng, mô hình dữ liệu khớp hợp đồng dữ liệu chung, job xoá và test hook.
- **Cho DPIA (Writer D) và store/chính sách (Writer E):** danh mục dữ liệu ở SRS §6 và bản nháp màn đồng ý ở SRS §8. HC-D2, HC-D4 và
  việc xoá thuê bao đẩy khi rời nhóm là các điểm cần ghi vào DPIA.
- **Cho playtest (Writer F):** 3 tuần, 2–3 nhóm thật (một nhóm bạn đại học, một phòng ban). Host gửi thẻ sự kiện vào nhóm; mỗi người nhắn
  riêng % và phiếu đoán cho host bằng **số thứ tự**, không bằng tên; host lật bằng một slide tối thứ Sáu và xoá tin nhắn sau buổi. Tuần
  thứ hai bật Nhân Vật Chính tự nguyện. Quy tắc chốt: tiếp tục nếu ≥ 2/3 thành viên vẫn tự khai ở tuần 3 và không có báo cáo khó chịu.
  Playtest giấy nên thử cả hai biến thể D3 (có lá / không lá).
- **Cho owner:** duyệt văn phong §5, chốt D1–D3, D8 và HC-D1–HC-D5 (mã HC- là quyết định riêng của trò này, không trùng dãy D chung).

## 12. Bàn giao theo AGENTS.md

**Nguồn đã kiểm tra:** báo cáo "Chốt năm trò, giữ trọn chữ Lành" (phần Hết Cứu %, quyết định chờ chủ, bàn giao); ghi chú
`most_likely_percentage_games.md`; `AGENTS.md`; `docs/plans/2026-10-23-privacy-content-game-plan.md`;
`apps/web/src/shared/ui/companion/growth.test.ts`; `docs/foundation/la-lanh-plain-vietnamese-content-standard.md`;
`docs/legal/privacy-security-flow-notes.md`; `docs/legal/2026-10-22-privacy-counsel-dossier.md`; trang Apple App Review Guidelines
(đọc lại 26/10/2026: 1.1.1, 1.2, 4.7, 5.3; trang không có mục "simulated gambling", câu hỏi này nằm ở bảng xếp hạng tuổi, chưa đọc).
Kết quả tìm kiếm thứ cấp về chính sách "simulated gambling" của Google Play (chưa đọc được trang chính sách gốc).

**Phát hiện đã sửa trong thiết kế:** (1) nền kinh tế lá nạp lại hằng tháng và điểm mùa → lá chỉ trong một sự kiện (D3); (2) 3 thông
báo/tuần → tối đa 1 (HC-D2); (3) chiếu lại "Tuần 3 bạn khai 10%" cần giữ số thô → chỉ so với khoảnh khắc đã đồng ý giữ; (4) "Lá tuần này
đã báo trước" → bỏ câu dự đoán; (5) chú thích chiêm tinh cá nhân → loại khỏi Lá Úp (HC-D1); (6) "đừng đoán tôi" không thu % của người đó
(tối thiểu hoá); (7) "The Lovers" cho sự kiện robot đề xuất đổi để tránh gợi tình cảm.

**Rủi ro chưa giải quyết:** phân loại "mô phỏng cờ bạc" của cơ chế lá (chưa có nguồn chính thức, chưa có ý kiến luật sư); phân loại
G1 theo Nghị định 147/2024/NĐ-CP (chưa đối chiếu nguyên văn); chữ "hết cứu" chưa kiểm tra với người dùng; thời gian sống của nhóm (HC-D4)
chưa có trong hợp đồng dữ liệu chung; web push trên iOS chỉ chạy khi web app được thêm vào Màn hình chính (WebKit, iOS 16.4+), nên
nhiều người iPhone sẽ không nhận được thông báo.

**AC/DoD còn thiếu:** owner chưa duyệt nội dung và D-codes; ngân hàng còn thiếu 4/24 sự kiện; chưa playtest giấy; DPIA, nhãn store
và chính sách quyền riêng tư chưa cập nhật cho trò này; chưa có ý kiến luật sư về G1 và mô phỏng cờ bạc.
