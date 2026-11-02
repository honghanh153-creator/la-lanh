# Cổng chặn nội dung "đọc là hiểu" — chẩn đoán và đặc tả

Ngày: 2026-11-01 · Trạng thái: **đề xuất, chờ chủ sản phẩm duyệt ngưỡng** · Phạm vi: Tarot (Lá Hỏi),
Khám phá (/insights), Radar hợp gu, Daily.

Tài liệu này trả lời hai câu: vì sao nội dung hiện tại khó hiểu dù đã qua mọi cổng, và cổng mới
phải đo gì, đo bằng cách nào, ngưỡng nào thì chặn phát hành.

## 1. Vì sao nội dung đang tệ

### 1.1 Đo trên engine thật

> **Đính chính 2026-11-02.** Lần đo đầu chạy trên một nhánh cũ (`feat/luna-content-rewrite-runtime`).
> Ở đó Radar và Tarot còn nhiều câu meta và thuật ngữ. Trên `collab/integration`, Radar đã được viết
> lại dễ đọc hơn và Tarot đã bỏ các tiền tố "Ý chính của lá:", "Ví dụ:". Bảng dưới là số đo trên
> `collab/integration`, đúng với baseline của C1 (#179). Đơn vị là tổng số lần vi phạm.

| Luật | Daily (64) | Tarot (240) | Radar (96) | Khám phá (88) |
|---|---|---|---|---|
| A1 thuật ngữ đứng trơ | 0 | 0 | 0 | 1663 |
| A3 ẩn dụ máy (vượt 2/bài) | 0 | 1 | 130 | 1320 |
| A4 nói về bài/app | 0 | 0 | 0 | 396 |
| A5 cặp câu gần trùng | 0 | 712 | 254 | 6050 |
| A7 rào đón (vượt 0.3/câu) | 36 | 373 | 288 | 495 |
| A8 câu > 25 âm tiết | 33 | 24 | 124 | 775 |
| A10 tiếng Anh | 2 | 0 | 91 | 332 |
| A11 placeholder | 0 | 0 | 0 | 132 |
| A14 khẳng định việc đã xảy ra | 5 | 5 | 0 | 0 |

Kết luận theo màn:
- **Khám phá** nặng nhất. Ô hành tinh × cung × nhà được ghép độc lập nên lặp câu trong cùng trang;
  có "Nhà N", tên góc chiếu, tên hành tinh tiếng Anh; câu "X không nói bạn là gì" có ở mọi ô; ô
  Jyotish còn câu tạm "Phần giải nghĩa riêng chưa sẵn sàng".
- **Tarot** không còn thuật ngữ, nhưng trung bình khoảng 3 cặp câu gần trùng mỗi bài, headline chung
  chung (ví dụ "Lúc này, điều đáng nhìn rõ trong chuyện này."), và có cảnh không liên quan tới câu hỏi.
- **Radar** đã dễ đọc hơn nhiều; còn câu dài, rào đón và lặp ý.
- **Daily**: chữ khá sạch, nhưng **không bám theo ngày** (mục 1.4).

### 1.2 Vì sao cổng hiện tại không chặn

1. **Không phủ hết các màn người dùng thấy.** `pnpm content:review` chỉ duyệt Daily, Natal detail và
   Tarot: 10 persona, tổng 30 bài. Radar và các ô Khám phá **không được duyệt**. Chạy chính
   `ContentReviewAgent` lên các ô Khám phá thì trượt ngay (73 câu lặp, 20 cảnh không quan sát được).
2. **Duyệt sai giọng.** Script review render Tarot bằng `STRAIGHT_WARM`, nhưng route production luôn
   dùng `PLAYFUL_GROUNDED` (hoặc `ROAST`). Cổng đang kiểm một giọng không người dùng nào thấy.
3. **Danh sách cấm đóng.** `BANNED_CORE_FRAGMENTS` / `OPAQUE_CORE_FRAGMENTS` là danh sách câu đã từng
   bị chê. Cách diễn đạt mới cùng kiểu vẫn lọt qua. Hiện chưa có từ điển thuật ngữ, mẫu câu meta,
   ngưỡng rào đón hay luật về tiếng Anh.
4. **Chỉ bắt câu trùng y hệt.** Hai câu cùng ý khác vài chữ là thoát (ví dụ ở nhánh cũ: "Tám Kiếm:
   …" và "Ý chính của lá: …"); trên integration Tarot vẫn còn 712 cặp câu gần trùng. Với Tarot,
   lặp giữa các phần còn chỉ là mức `medium`, không chặn.
5. **Kiểm hình thức, không kiểm nghĩa.** Một "cảnh" chỉ cần chứa "khi " hoặc "người "; một "hành
   động" chỉ cần chứa "nói " hoặc "làm ". Không cổng nào hỏi: bài có trả lời câu hỏi không, cảnh
   có phải về người đọc không, các phần có nối với nhau không.
6. **`tarot/quality.py` chỉ kiểm an toàn.** Chính docstring của file ghi: "not a semantic quality
   guarantee". Audit Radar chỉ có 10 từ cấm cộng kiểm cấu trúc và evidence.

### 1.3 Vì sao kiểu chữ này làm người đọc mệt (nghiên cứu)

- **Thuật ngữ làm bài đọc "nặng" kể cả khi người đọc vẫn hiểu được nghĩa.** Thí nghiệm N=650: thuật
  ngữ làm độ trôi chảy khi đọc giảm từ 5.27 xuống 4.57 (η²=.11). Tác giả viết rằng thuật ngữ cản trở
  "in addition to and separate of comprehension". Hiệu ứng này rõ với chủ đề ít khẩn cấp, như
  Tarot hay chiêm tinh.
  [Bullock et al. 2019](https://comm.osu.edu/sites/comm.osu.edu/files/PUS%202019-%20Bullock%20et%20al..pdf),
  [Shulman & Bullock 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7540871).
  Đây là lý do bài "đúng" vẫn bị thấy tệ.
- **Định nghĩa kèm theo không gỡ được gánh nặng đó** (cùng nghiên cứu: định nghĩa không có tác dụng,
  p=.54). Vì vậy nhãn tự đặt như "Bắt sóng", "Lực cấn", "góc chiếu" phải **thay bằng từ đời thường**,
  không phải giải thích thêm.
- **Chữ cụ thể dễ nhớ hơn chữ trừu tượng.**
  [Sadoski et al. 1995](https://www.bohrium.com/paper-details/concreteness-effects-in-text-recall-dual-coding-or-context-availability/812099592496611328-7455).
  Câu dịch máy móc chức năng hành tinh, kiểu "cách bạn chủ động chạm vào cách người kia nhận sự quan
  tâm", là dạng trừu tượng điển hình.
- **Tiếng Việt:** tỷ lệ từ Hán-Việt và từ vay mượn tương quan khoảng 0.8 với độ khó của văn bản
  [(Luong et al. 2020)](https://ftp.saiconference.com/Downloads/Volume11No8/Paper_14-Assessing_Vietnamese_Text_Readability.pdf).
  Tuy vậy **chưa có công thức độ dễ đọc tiếng Việt nào đã được kiểm chứng**, và công thức không bắt
  được lỗi meta, rào đón hay lặp
  [(CDC)](https://Cdc.gov/ccindex/pdf/clear-communication-user-guide.pdf). Không dùng điểm công thức
  làm tiêu chí đạt/trượt.
- **Có sẵn mô hình cổng chấm điểm:**
  - CDC Clear Communication Index: các mục chấm 0/1, đạt từ 90/100, dùng *trước khi phát hành*.
    Mục 7 yêu cầu thuật ngữ không tránh được phải giải thích ngay trong câu đó hoặc câu kế tiếp.
  - [PEMAT-P](https://www.ahrq.gov/health-literacy/patient-education/pemat-p.html): mục 2 (không
    có nội dung làm phân tâm), mục 3 (từ đời thường), mục 4 (thuật ngữ được định nghĩa), mục 5 (câu
    chủ động).

### 1.4 So sánh với một bài đọc chủ sản phẩm thấy "khớp hôm nay" (bổ sung 2026-11-02)

Chủ sản phẩm đưa một chart thật cùng bảng transit Astrodienst ngày 2/11/2026, kèm một bài đọc do
một AI chat viết, và thấy bài đó khớp hơn hẳn Daily Note và Khám phá. Mình chạy engine của Lá Lành
cho đúng chart và ngày đó. Dữ liệu sinh và các vị trí suy ra từ chart chỉ xử lý cục bộ. Repo công
khai nên tài liệu này chỉ ghi số đếm và dạng lỗi, không ghi vị trí hay góc của chart đó.

**Daily Note của Lá Lành không bám theo ngày:**
- Trên `collab/integration`: 11/14 ngày liên tiếp dùng cùng một transit của hành tinh chậm (kéo
  dài khoảng 3 tháng), mà câu vẫn mở bằng "Hôm nay…". Ở nhánh cũ là 13/14 ngày.
  Planner chọn transit theo độ chính xác của góc và trọng số hành tinh gốc,
  không tính tốc độ hành tinh.
- Headline thay đổi theo `editorial_seed`, không theo bầu trời: 14 ngày chỉ có 9 headline khác nhau,
  một câu lặp 3 lần. Cả loạt headline xoay quanh một chủ đề hẹp (bản nháp, xin góp ý).
- Transit thật sự chỉ có trong hôm đó (một góc của Mặt Trăng, chính xác trong ngày) không được
  dùng.
- Headline khẳng định một việc như đã xảy ra: *"Tin nhắn vừa gửi chưa đúng cách bạn muốn nói."*
  Hôm đó không gửi tin thì người đọc thấy ngay là "không đúng".
- Cả bài chỉ một cảnh, một lĩnh vực, không có câu nào nối bầu trời với nội dung. Còn có câu cụt:
  *"Ví dụ với người kia."*

**Bài của AI chat "khớp" vì hình thức, không vì đúng:**
- **Sai hoặc lỏng 3/6 dữ kiện kiểm được** (đối chiếu với chính bảng Astrodienst, engine Lá Lành
  khớp tới vài phút cung):
  - một góc đối đỉnh ghi "sai số 8°" thực tế lệch khoảng 22°; góc 8° là với một điểm gốc khác (AI
    chat nhầm hàng);
  - một góc ghi "đang tiến gần" thực tế đã qua 17° và đang rời xa;
  - một góc ghi "gần" thực tế cách 11.6°, ngoài mọi sai số thường dùng.
- **Đúng:** 3 dữ kiện còn lại (một góc lục hợp 0.5°, vị trí nhà của hai hành tinh transit).
- **Bỏ sót các góc chặt nhất hôm đó,** gồm một góc gần như chính xác (0.01°) và góc duy nhất chỉ có
  trong ngày (của Mặt Trăng).
- Khung giờ "17h–19h" tự bịa, chính bài cũng thừa nhận điều đó.

**Hình thức mà Lá Lành nên học:**
1. **Chuỗi lý do lộ ra:** dữ kiện → nghĩa thường gặp → với bạn hôm nay. Thuật ngữ được chấp nhận
   vì câu ngay sau nói nó có hệ quả gì (đúng mục 7 của CDC). Thuật ngữ của Lá Lành thì đứng trơ
   hoặc đi kèm ẩn dụ, ví dụ "tạo thêm một điểm kéo-ngược cần điều tiết".
2. **Chia theo lĩnh vực đời sống** (công việc, tiền, tình cảm, tâm trạng, giao tiếp), để người đọc
   tự tìm chỗ của mình.
3. **Nói theo điều kiện:** "Nếu hôm nay có cuộc trao đổi với cấp trên…". Không khẳng định một sự
   việc đã xảy ra.
4. **Chọn và tổng hợp:** mục "Điều mình muốn nhấn mạnh" gom 2 yếu tố thành một câu hỏi.
5. **Kết hợp yếu tố nhanh** (Mặt Trăng hôm nay) **với yếu tố chậm,** và nói rõ yếu tố nào là gì.
6. **Mời đi sâu:** hỏi người đọc muốn xem kỹ lĩnh vực nào.
7. **Rào đón đặt một lần ở đầu mục,** không lặp ở mọi câu.

Bài học: cảm giác "khớp" đến từ hình thức (hiệu ứng Barnum cộng với vẻ chuyên môn), kể cả khi dữ
kiện sai. Lá Lành học **hình thức**, giữ **độ đúng**. Cổng phải chặn cả hai lỗi: đúng mà vô hồn,
và hay mà sai.

Giới hạn: phần lớn bằng chứng là tiếng Anh, lĩnh vực y tế/khoa học, và đo cảm nhận chứ không đo
hiểu. Không có nguồn nào cho ngưỡng số bằng tiếng Việt. **Mọi ngưỡng số dưới đây là tạm thời**,
phải hiệu chỉnh bằng bộ mẫu vàng (mục 4).

## 2. Nguyên tắc của cổng mới

1. **Phủ mọi màn người dùng thấy, bằng đúng giọng production:** Tarot (`playful_grounded` và
   `roast`), Radar (4 ngữ cảnh), Khám phá (ô tổng quan và bản tổng hợp), Daily.
2. **Lỗi đo được bằng máy thì máy chặn; lỗi về nghĩa thì giám khảo chấm theo mục 0/1 và phải
   trích nguyên văn câu lỗi;** người thật kiểm trước mỗi thay đổi lớn về renderer.
3. **Thuật ngữ chỉ được xuất hiện khi mang theo hệ quả.** Một thuật ngữ chiêm tinh trong thân bài
   phải đi cùng nghĩa đời thường và tác động lên người đọc, ngay trong câu đó hoặc câu sau. Thuật
   ngữ không giải thích, ẩn dụ của engine và nhãn tự đặt thì bị chặn. Chi tiết kỹ thuật như orb,
   độ, nhà, mã nằm trong lớp "Vì sao Lá đọc vậy?".
4. **Ngắn ở màn đầu, sâu khi người đọc muốn.** Người dùng muốn nhiều nội dung, nhưng phải chia
   theo lĩnh vực và mở dần, không phải một khối chữ dài.
5. **Siết dần (ratchet):** bật chế độ báo cáo, lấy baseline, chặn ngay mọi bản làm số lỗi tăng,
   rồi kéo về 0 theo từng màn.

## 3. Đặc tả tiêu chí

### Lớp A — tự động, chặn phát hành

| ID | Tiêu chí | Cách đo | Ngưỡng chặn (tạm) | Ví dụ trượt hiện tại |
|---|---|---|---|---|
| A1 | Không có thuật ngữ đứng trơ | Từ điển: góc chiếu, đồng cung, đối đỉnh, lục hợp, tam hợp, vuông góc, nghịch hành, "Nhà N", composite, synastry, overlay, nakshatra, pada, drishti, điểm thế hệ, tropical/sidereal. Mỗi lần xuất hiện, câu đó hoặc câu sau phải có "bạn" kèm một động từ hành vi. Orb, độ và mã chỉ được nằm trong lớp evidence | 0 thuật ngữ đứng trơ; 0 orb/độ ngoài evidence | "Góc đối đỉnh gần nhất với Saturn tạo thêm một điểm kéo-ngược" (không có hệ quả) |
| A2 | Không nhãn tự đặt trong thân bài | Bắt sóng, Lực cấn, Dễ phối hợp, lớp kỹ thuật, Trạm Bắt Sóng, Bản đồ Lá… (nhãn UI tạm giữ cho tới khi qua kiểm thử kể lại) | 0 trong thân bài | "Độ hai nhịp có sẵn đường để nói…" |
| A3 | Ít ẩn dụ máy | nhịp, tín hiệu, chạm vào, lớp, vùng, kích hoạt, lực kéo, sóng, năng lượng, đường phối hợp, điều tiết | ≤ 2 lần mỗi bài | Radar trung bình 17 lần "nhịp" mỗi bài |
| A4 | Không nói về bài, app hay phương pháp | Mẫu: phần dưới, mở phần, Radar giữ, đây không phải tín hiệu, góc (nghĩa góc chiếu), Ý chính của lá, "Ví dụ:", không nói bạn là gì, suy từ chart | 0 | "Phần dưới chỉ ra lúc nó…; mở phần dưới để xem…" |
| A5 | Không lặp câu trong bài | Câu ≥ 6 âm tiết; trùng cặp âm tiết liền nhau (bigram) ≥ 50% với câu khác | 0 cặp | Tóm tắt Tarot chép lại đoạn nghĩa |
| A6 | Không lặp câu giữa các bài | Một câu không phải disclaimer xuất hiện ở > 20% số bài của cùng màn | 0 câu | "X không nói bạn là gì; nó mô tả…" có trong mọi ô |
| A7 | Ít rào đón | có thể, dễ, chưa chắc, không phải, đôi lúc, có lẽ | ≤ 0.3 mỗi câu; 0 câu kiểu disclaimer trong thân bài | Radar 0.92 mỗi câu |
| A8 | Câu ngắn | Âm tiết mỗi câu | Không câu nào > 25 | 100% bài Radar và Khám phá |
| A9 | Màn đầu vừa sức đọc trên điện thoại | Chỉ đếm âm tiết ở lớp đầu, trước khi người dùng bấm mở thêm. Lớp sâu không giới hạn tổng độ dài, nhưng từng đoạn vẫn phải qua A1–A8 | Tarot 1/3/5 lá: 120/250/400; Radar lớp đầu ≤ 400; Khám phá màn đầu ≤ 300; Daily màn đầu ≤ 150 | Khám phá ~1150 âm tiết mỗi trang (đo trên nhánh cũ; cần đo lại khi có A9) |
| A10 | Không tiếng Anh trong thân bài | Từ có f/j/w/z hoặc thuộc danh sách vay mượn; allowlist: Vibe, tên sản phẩm | 0 | chart, mood, flirt, Saturn |
| A11 | Không câu chờ hay placeholder | "chưa sẵn sàng", "đang cập nhật", TODO | 0 | Ô nakshatra: "Phần giải nghĩa riêng chưa sẵn sàng." |
| A12 | Phủ đủ và đúng giọng | Số mẫu: Tarot ≥ 200 (mọi giọng production), Radar ≥ 80, Khám phá ≥ 80, Daily ≥ 60 | Thiếu là trượt | Hiện 30 mẫu, sai giọng, thiếu Radar và Khám phá |
| A13 | Daily bám đúng ngày | Render 30 ngày liên tiếp cho mỗi persona có giờ sinh. Đếm: (a) ngày có ít nhất một yếu tố nhanh (transit của Mặt Trăng, Mặt Trời, Sao Thủy, Sao Kim, Sao Hỏa, hoặc cung/nhà của Mặt Trăng); (b) số lý do khác nhau; (c) headline lặp | (a) 100% số ngày; (b) không có lý do nào chiếm > 3 ngày trong 7; (c) 0 headline lặp trong 30 ngày | 11/14 ngày cùng một lý do (transit chậm); 9 headline cho 14 ngày |
| A14 | Không khẳng định sự việc đã xảy ra | Headline/cảnh có hành động của người đọc ở thể đã xong ("vừa gửi", "đã gửi", "rồi mới thấy", "vừa nói") mà không có "nếu/khi/lúc" | 0 | "Tin nhắn vừa gửi chưa đúng cách bạn muốn nói." |
| A15 | Dữ kiện trong câu chữ khớp engine | Bóc mọi cặp hành tinh + góc/cung/nhà được nhắc trong thân bài, đối chiếu với contacts/positions của engine (gồm pha tiến gần/rời xa) | 0 sai lệch | (Lá Lành chưa thấy lỗi này; bài AI chat sai 3/6.) Cần trước khi bật Luna viết lại tự do hơn |

Soft warning, không chặn: tỷ lệ từ Hán-Việt, tỷ lệ từ ngoài 3.000 từ thông dụng. Theo dõi theo xu
hướng; nghiên cứu cho thấy chỉ đúng khoảng 80% nên không đủ để chặn.

### Lớp B — giám khảo chấm theo mục (LLM hoặc người), chặn phát hành khi đã hiệu chỉnh

Mỗi mục chấm 0/1, giám khảo **bắt buộc trích nguyên văn** câu làm trượt. Điểm = số mục đạt chia
số mục áp dụng, nhân 100. **Đạt khi ≥ 90 và mọi mục ★ đều đạt** (theo cách của CDC).

| ID | Mục | Câu giám khảo trả lời | Nguồn |
|---|---|---|---|
| B1 ★ | Trả lời thẳng | Hai câu đầu có trả lời đúng câu hỏi hoặc mục đích không? Tarot: trả lời câu hỏi người dùng. Radar: điều nổi bật nhất của cặp này. Khám phá: nét riêng nhất của chart | Chuẩn nội dung Lá Lành, bước 1 |
| B2 ★ | Về người đọc | Mọi cảnh có phải là chuyện của "bạn" hoặc "hai bạn" trong đời họ, không phải người lạ hay nghề lạ? | Chuẩn nội dung; lỗi "người in thống nhất kích thước" |
| B3 ★ | Không phải giải mã | Có câu nào người bình thường phải đọc lại hai lần mới hiểu không? Trích câu đó | PEMAT 3, CDC 7 |
| B4 ★ | Riêng cho dữ kiện này | Đưa giám khảo bài này và một bài mồi (lá khác hoặc cặp khác). Giám khảo có chọn đúng bài khớp với dữ kiện không? | Chống hiệu ứng Barnum (vòng 1) |
| B5 | Cảnh nhìn thấy được | Có ai làm gì, lúc nào? | Chuẩn nội dung |
| B6 | Một việc làm được | Có đúng một việc chính, làm được trong 24 giờ, không lặp ở nhiều chỗ? | PEMAT actionability |
| B7 | Các phần nối với nhau | Lá sau có dựa trên lá trước, các chương có ăn khớp, không như ba bài riêng? | Lỗi Tarot hiện tại |
| B8 | Không phân tâm | Có đoạn nào không giúp người đọc hiểu chuyện của mình không? | PEMAT 2 |
| B9 | Câu chủ động, có chủ thể | Câu có nói rõ ai làm gì? | PEMAT 5 |
| B10 | Thuật ngữ được giải thích tại chỗ | Thuật ngữ không tránh được (ví dụ tên lá) có nghĩa đời thường ở ngay câu đó hoặc câu sau không? | CDC 7 |
| B11 ★ | Chuỗi lý do lộ ra | Mỗi luận điểm chính có đủ: dữ kiện (lá, hành tinh, cặp) → nghĩa đời thường → với bạn hôm nay? | Bài AI chat chủ sản phẩm chọn (mục 1.4) |
| B12 | Nói theo điều kiện, nhiều lối vào | Cảnh có dạng "nếu/khi…" và có ít nhất 2 tình huống để người đọc tự nhận? | Mục 1.4 |
| B13 | Phủ lĩnh vực (Daily, Khám phá) | Có ít nhất 3 lĩnh vực (công việc, tiền, tình cảm, giao tiếp, tâm trạng), mỗi lĩnh vực một xu hướng và một cảnh có điều kiện, hoặc cho người đọc chọn lĩnh vực? | Mục 1.4 |
| B14 | Có chọn ưu tiên | Bài có nói rõ 1–2 điều quan trọng nhất và vì sao, thay vì liệt kê đều nhau? | Mục 1.4; CliftonStrengths (vòng 1) |

**So sánh với bài tham chiếu:** chủ sản phẩm chọn vài bài "khớp" làm mẫu, sau khi sửa lại dữ kiện
sai như bài ở mục 1.4. Giám khảo đặt bài của Lá Lành cạnh bài tham chiếu cùng chart và cùng ngày.
Lá Lành không được thua ở B1, B2, B11, B13. Mẫu tham chiếu không được chép vào corpus; nó chỉ là
thước đo.

Giám khảo chỉ được chặn phát hành sau khi đạt **≥ 85% đồng ý với người chấm ở từng mục ★** trên bộ
mẫu vàng. Trước đó, lớp B chỉ cảnh báo. Giám khảo chỉ nhận bài render từ persona tổng hợp, không có
dữ liệu người dùng thật.

### Lớp C — người thật, bắt buộc khi đổi renderer hoặc knowledge lớn

- **Kể lại:** 6–9 người, mỗi người đọc một bài rồi nói lại bằng lời mình "bài nói gì về bạn" và
  "bạn sẽ làm gì". Đạt khi ≥ 5/6 người nói đúng ý chính và đúng việc cần làm
  [(digital.gov)](https://digital.gov/guides/plain-language/test/paraphrase-testing).
- **Nhận bài của mình:** mỗi người xem bài của chính mình lẫn với 2 bài mồi. Đạt khi tỷ lệ chọn
  đúng rõ ràng cao hơn mức đoán mò (1/3).
- **Không dùng** câu "thấy đúng mình không?" làm chỉ số đạt. Văn bản chung chung vẫn được chấm
  khoảng 4.3/5 (Forer, vòng 1).

## 4. Bộ mẫu vàng và chống "học tủ"

- Chủ sản phẩm gắn nhãn khoảng 60 bài đầu, khoảng 20 bài cho mỗi màn. Mỗi bài có nhãn tốt/tệ kèm
  nhãn từng mục B. Mục tiêu dài hạn khoảng 200 bài để hiệu chỉnh giám khảo.
- Mỗi lần sửa ngưỡng ở lớp A, chạy lại trên bộ mẫu vàng: bài "tốt" không được trượt, bài "tệ"
  phải trượt.
- Giữ riêng khoảng 20% bộ mẫu không dùng để viết luật, chỉ dùng để kiểm. Thay mới mỗi quý.
- Từ điển lớp A chỉ chặn trong thân bài. Nếu đổi sang từ đồng nghĩa mà vẫn khó hiểu thì mục B3 sẽ
  bắt. Hai lớp bù nhau.

## 5. Thứ tự triển khai

1. **Phủ đúng màn, đúng giọng (A12) và lớp A ở chế độ báo cáo.** Thêm Radar và Khám phá vào
   `review_content_release`, đổi Tarot sang giọng production, thêm luật A1–A11. In baseline từng
   màn, rồi chặn mọi thay đổi làm số lỗi tăng. Chặn ngay, vì đây là lỗi thật: A11 (placeholder),
   A14 (khẳng định sự việc), A4 câu chỉ đường. Đo A13 trên 30 ngày để có baseline Daily.
   Sửa Daily tương ứng: thêm tốc độ hành tinh vào cách chọn transit, ưu tiên ít nhất một yếu tố
   nhanh mỗi ngày, bỏ xoay vòng headline theo seed khi lý do không đổi.
2. **Viết lại nội dung theo màn** cho tới khi lớp A về 0, rồi đổi màn đó sang chặn cứng. Thứ tự
   gợi ý: Tarot (ít lỗi nhất, dùng nhiều), Radar, Khám phá.
3. **Bộ mẫu vàng và lớp B ở chế độ cảnh báo.** Hiệu chỉnh tới ngưỡng đồng ý, rồi bật chặn.
4. **Lớp C** trước khi phát hành bản viết lại của từng màn.

## 6. Báo cáo theo AGENTS.md

- **Nguồn đã xem:**
  - `docs/foundation/la-lanh-plain-vietnamese-content-standard.md`, spec Tarot, spec Radar hợp gu.
  - `apps/api/app/domains/readings/review_agent.py`, `tarot/quality.py`, `scripts/review_content_release.py`, `scripts/audit_radar_experience.py`.
  - Hai vòng deep research: 43 nguồn, các kết luận được kiểm chứng chéo ba phiếu.
- **Đã sửa:** chưa sửa code. Đây là chẩn đoán và đặc tả.
- **Rủi ro còn mở:**
  - Ngưỡng số chưa có căn cứ tiếng Việt, phải hiệu chỉnh.
  - Bật lớp A ở chế độ chặn ngay lập tức sẽ chặn mọi bản phát hành, nên phải đi theo cách siết dần.
  - Giám khảo LLM gửi bài render (persona tổng hợp) cho nhà cung cấp, cần ghi vào phần riêng tư
    nếu có dùng.
- **AC/DoD chưa xong:**
  - Chưa có AC mới cho cổng này trong SRS.
  - Nhãn UI "Bắt sóng / Dễ phối hợp / Lực cấn" trong spec Radar cần quyết định sau kiểm thử kể lại.
