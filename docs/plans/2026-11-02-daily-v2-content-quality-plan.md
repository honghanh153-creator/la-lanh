# Daily v2 và cổng chất lượng nội dung — plan

Ngày: 2026-11-02 · Mức: **L** · Phase: nội dung (theo thứ tự ưu tiên: nội dung → quyền riêng tư → tính năng mới)
Nghiên cứu và chẩn đoán: `docs/research/2026-11-01-content-clarity-gate.md`

## 1. Quyết định của chủ sản phẩm (2026-11-02)

1. **Note ngày dùng hành tinh nhanh.** Mỗi ngày chọn 3 yếu tố, mỗi yếu tố chạm một điểm gốc khác
   nhau. Hành tinh chậm chỉ hiện thành tag **"Xu hướng hiện tại"** kèm khoảng ngày.
2. **12 nhà là nguồn lĩnh vực.** Kết hợp nhà, cung ở đầu nhà và **chủ tinh hệ hiện đại** (Diêm
   Vương, Thiên Vương, Hải Vương cho Bọ Cạp, Bảo Bình, Song Ngư). Chủ tinh truyền thống chỉ xuất hiện
   trong lớp "Vì sao Lá đọc vậy?".
3. **Trang chủ chỉ tóm tắt; muốn đọc kỹ thì vào trang chi tiết.**
4. **Thân bài chỉ viết verdict.** Không nhắc nhà, cung, chủ tinh, tên góc hay sai số. Engine dùng các
   lớp này để chọn và viết; dữ kiện chỉ nằm trong lớp "Vì sao".
5. **Không rõ giờ sinh thì không dùng nhà, cung đầu nhà, chủ tinh.** Khi đó lĩnh vực lấy theo hành
   tinh gốc.
6. **Cổng chất lượng tự động là chính.** Người không duyệt từng câu. **Đã chốt 03.11.2026** (owner giao
   Claude chốt): luật Q2 với bản đọc là "duyệt bộ chuẩn một lần, chỉ xem câu bị gắn cờ và báo cáo
   điểm" (`docs/operations/decision-checklist.md`).
7. **Đủ 12 lĩnh vực, không gộp; mở rộng bằng khía cạnh con** (owner, 03.11.2026). Bảng ở mục 1.1.

### 1.1 Mười hai lĩnh vực (chốt 03.11.2026)

Mỗi nhà một lĩnh vực riêng.
- **Chip** là nhãn ngắn trên trang chủ.
- **Tên đầy đủ** dùng ở trang chi tiết.
- **Khía cạnh con** là các việc cụ thể mà một thẻ có thể gọi tên ("Nhắn tin · 17h30"). Mỗi nhà có 4 khía cạnh.

| Nhà | Chip | Tên đầy đủ | Khía cạnh con |
|---|---|---|---|
| 1 | Bản thân | Bản thân và cách mình xuất hiện | năng lượng cơ thể; vẻ ngoài; cách mở đầu việc mới; cảm giác là chính mình |
| 2 | Tiền bạc | Tiền bạc và những gì mình có | thu nhập; chi tiêu; đồ đạc mình giữ; giá trị bản thân |
| 3 | Giao tiếp | Giao tiếp và học hỏi | nhắn tin, nói chuyện; học điều mới; anh chị em, hàng xóm; đi lại gần |
| 4 | Gia đình | Gia đình và tổ ấm | nhà cửa; cha mẹ; nơi thấy an toàn; ký ức, gốc rễ |
| 5 | Hẹn hò | Hẹn hò và niềm vui | tình cảm mới; vui chơi; sáng tạo; con cái |
| 6 | Việc hằng ngày | Việc hằng ngày và nếp sống | nếp sinh hoạt; đồng nghiệp; việc vặt; chăm sóc cơ thể (không phán đoán bệnh, luật S1) |
| 7 | Đối tác | Người yêu và đối tác | người yêu, vợ chồng; hợp tác một-một; người đối diện; lời hứa đôi bên |
| 8 | Gắn bó sâu | Gắn bó sâu và tin tưởng | thân mật; niềm tin; tiền chung, nợ nần (không khuyên đầu tư, luật S3); buông bỏ, thay đổi lớn |
| 9 | Đi xa và học | Đi xa, học sâu và niềm tin | chuyến đi xa; học sâu, thi cử; quan điểm sống; người ở nơi khác |
| 10 | Sự nghiệp | Sự nghiệp và vị trí | việc chính; cấp trên; mục tiêu dài; danh tiếng |
| 11 | Bạn bè | Bạn bè và cộng đồng | nhóm bạn; cộng đồng; mạng lưới quen biết; mong ước chung |
| 12 | Nghỉ ngơi | Nghỉ ngơi và thế giới bên trong | giấc ngủ; thời gian một mình; chuyện chưa nói ra; hồi phục |

Quy tắc dùng:
- Lĩnh vực của thẻ lấy theo nhà mà hành tinh đang đi qua đứng trong lá số gốc.
- Khi transit chạm chủ tinh của một nhà thì thêm nhà đó. Chỉ áp dụng khi nhãn nhà không đổi trong khoảng sai số của giờ sinh (C2b).
- Khía cạnh con chọn theo tính chất hành tinh đang đi. Ví dụ: Sao Thủy chọn khía cạnh về lời nói, Sao Kim về tình cảm và tiền, Sao Hỏa về hành động.
- Mỗi lĩnh vực chỉ một chip mỗi ngày.
- Không rõ giờ sinh thì lĩnh vực lấy theo hành tinh gốc, dùng cùng 12 chip:
  - Mặt Trời → Bản thân;
  - Mặt Trăng → Gia đình;
  - Sao Thủy → Giao tiếp;
  - Sao Kim → Hẹn hò hoặc Đối tác;
  - Sao Hỏa → Việc hằng ngày.
- Mở rộng thêm khía cạnh qua PR, không gộp lĩnh vực.

## 2. Số liệu nền

Đo bằng engine ngày 2026-11-01/02. Dữ liệu sinh thật chỉ xử lý cục bộ.

| Chỉ số | Hiện tại | Daily v2 (mô phỏng 20 chart × 30 ngày) |
|---|---|---|
| Lý do chiêm tinh trùng hôm qua | 79% (11/14 ngày cùng một transit chậm, đo trên `collab/integration`) | 7% |
| Bộ 3 yếu tố trùng hôm qua (Jaccard, trung vị) | — | 0.20 |
| Ngày không đủ 3 yếu tố nhanh | — | 0% khi chạm mọi điểm gốc |
| Headline lặp | 9 headline cho 14 ngày, xoay theo seed, không theo bầu trời | Mục tiêu: 0 lặp trong 30 ngày |
| Giờ tính | Sky Chapter tính lúc 12:00 UTC (19h giờ VN) | Theo ngày giờ VN, lấy mẫu mỗi 30 phút |

## 3. Hợp đồng note ngày mới

**Trang chủ: chỉ tóm tắt** (≤ 60 âm tiết, quyết định chủ sản phẩm 2026-11-02):
- Một câu chính, rút từ yếu tố mạnh nhất hôm nay.
- Một gợi ý "hôm nay thử", lấy từ thẻ quan trọng nhất.
- Ba chip lĩnh vực có giờ, ví dụ "Hẹn hò · 17h30", "Sự nghiệp · hôm nay", "Bạn bè · mấy ngày này".
- Bấm vào note hoặc vào một chip thì mở trang chi tiết, tới đúng thẻ đó.
- Trang chủ không có tag xu hướng, lớp "Vì sao" hay các thẻ đầy đủ.
- **Trang chủ là cái móc, không phải bản tóm tắt khô.** Phản hồi của chủ sản phẩm 2026-11-02:
  "nghe chán". Luật viết:
  - Mở bằng **khoảnh khắc riêng của ngày** (một giờ cụ thể) hoặc **hai mặt tương phản** của ngày.
  - Có ít nhất một hình ảnh cụ thể ("đầu nhiều ý", "tim dễ rung"). Không dùng động từ chung chung
    như "làm mới", "cân bằng", "kết nối".
  - Gợi ý viết như lời bạn bè, một vế, không như bài tập.
  - Chip là một móc nhỏ, ví dụ "17h30 · tim dễ rung", không phải nhãn khô "Hẹn hò".
  - Vẫn nói theo điều kiện, không đoán suy nghĩ người khác, không dọa.
  - Đo bằng tỷ lệ bấm vào trang chi tiết và tỷ lệ quay lại hôm sau. Thử A/B các giọng bằng domain
    `experiments` có sẵn.
- **Chạy song song hai kiểu để thử** (chủ sản phẩm chốt 2026-11-02):
  - **A, "Khoảnh khắc trong ngày":** mở bằng giờ rõ nhất của ngày.
  - **C, "Nói như bạn thân":** giọng vui, gợi ý một vế.
  - Mỗi người dùng được gán cố định vào một nhánh. Nhánh nào ít bị chạm "khó hiểu", nhiều lượt bấm
    vào chi tiết và nhiều lượt quay lại hôm sau thì thắng.
- **Trang chi tiết cũng viết lại theo cùng kiểu với nhánh** (chủ sản phẩm 2026-11-02):
  - Mỗi thẻ mở bằng một câu móc theo giọng của nhánh A hoặc C, rồi tới verdict, rồi gợi ý "nếu…
    thì…".
  - Tag xu hướng cũng viết theo giọng của nhánh.
  - Chỉ lớp "Vì sao" giữ giọng trung tính, dạng dữ kiện.
  - Không người dùng nào thấy trang chủ một giọng mà trang chi tiết một giọng khác.

**Trang chi tiết note** (Note Detail, ≤ 150 âm tiết cho phần nhìn thấy trước khi cuộn):
- Một câu chính.
- Ba thẻ. Mỗi thẻ gồm:
  - **nhãn lĩnh vực đời thường**: lấy từ nhà khi có giờ sinh chính xác, nếu không thì từ hành tinh
    gốc;
  - **khung giờ thật** (yếu tố của Mặt Trăng) hoặc "mấy ngày này" (Mặt Trời, Sao Thủy, Sao Kim,
    Sao Hỏa);
  - **một câu verdict** và **một gợi ý "nếu… thì…"**.
- Tag "Xu hướng hiện tại": 1–2 yếu tố chậm, kèm khoảng ngày và ngày rõ nhất. Chỉ ghi verdict, không
  ghi tên góc.

**Lớp "Vì sao Lá đọc vậy?"** (mở khi người đọc muốn): hành tinh, góc, sai số, giờ chính xác, nhà,
cung đầu nhà, chủ tinh hiện đại và truyền thống.

**Cuối note:** một lời mời đi sâu vào một lĩnh vực.

## 4. Các PR

Mỗi PR nhỏ, chạy qua vòng review tự động. Cột "Cổng" ghi các cổng cần có bằng chứng: docs, UX,
copy, BE, FE, QC, security, privacy, release, cost.

| # | PR | Cỡ | Nội dung | Điều kiện xong |
|---|---|---|---|---|
| C1 | Cổng lớp A | M | `content:review` phủ Radar, Khám phá, Daily, đúng giọng production. Luật A1–A15 chạy ở chế độ báo cáo, có baseline; PR nào làm số lỗi tăng thì chặn. Chặn cứng ngay: câu tạm, khẳng định việc đã xảy ra, câu chỉ đường | Baseline được commit; CI chặn regression |
| C2a | Engine: cửa sổ ngày và 3 tầng thời gian | M | Ngày giờ VN, lấy mẫu mỗi 30 phút; chia tầng hôm nay / mấy ngày này / xu hướng; chọn top 3 đa dạng; pha của góc; dự phòng bằng điểm gốc khác và vị trí Mặt Trăng | Test 30 ngày: top-1 trùng ≤ 10%; ngày nào cũng ≥ 3 yếu tố |
| C2b | Engine: nhà, cung đầu nhà, chủ tinh | M | Cung ở đầu mỗi nhà, cung bị chặn, chủ tinh hiện đại (truyền thống chỉ làm metadata), các nhà mỗi hành tinh cai quản; tăng ưu tiên khi transit chạm chủ tinh của chart hoặc của nhà. Tắt cả lớp này khi giờ sinh không chính xác | Khớp astro.com trên chart mẫu; có test cho trường hợp không rõ giờ |
| C2c | Engine: khoảng ngày của xu hướng | S | Ngày bắt đầu, ngày rõ nhất (kể cả các lần đi qua do nghịch hành), ngày kết thúc của transit chậm | Khớp phép tính quét theo ngày |
| C2d | Chống lặp | S | Lưu mã các mảnh đã hiện trong 30 ngày cho mỗi người. Chỉ lưu mã, thời hạn giữ và đường xóa giống Daily Note | 0 mảnh lặp trong 30 ngày; được đưa vào kho dữ liệu cá nhân của Mình → Xóa |
| C3a | Bộ chuẩn | S | Tiêu chí A1–A16 và B1–B14, từ điển thuật ngữ, ~10 ví dụ đúng và ~10 ví dụ sai. Bộ mẫu vàng dựng từ các quyết định chủ sản phẩm đã có | Chủ sản phẩm duyệt một lần |
| C3b | Nhà máy nội dung Daily | L | Viết hai bộ giọng A và C cho cả trang chủ lẫn trang chi tiết. Mỗi giọng khoảng 550 mảnh: verdict và cảnh theo nhà × góc thuận/căng × hành tinh nhanh × pha (~360); chân dung nhà × cung đầu nhà (144); nghĩa hành tinh gốc (~50). Quy trình: viết → lớp A cho 100% → tự sửa tối đa 3 vòng → giám khảo Codex theo lô cho nhóm rủi ro cao và mẫu ngẫu nhiên → người đọc giả lập | Lớp A = 0; mẫu 100 câu không có lỗi nghiêm trọng (tỷ lệ lỗi < 3% với độ tin cậy 95%) |
| C4 | API, giao diện, A/B | M | Gán người dùng vào nhánh A hoặc C bằng `experiments`, cố định theo người. Thêm trường mới, không phá trường cũ: câu chính, gợi ý, chip, thẻ, tag xu hướng, lớp "Vì sao". Trang chủ chỉ hiện tóm tắt và chip; Note Detail hiện thẻ đầy đủ, xu hướng và lớp "Vì sao"; chip mở đúng thẻ | Test web/API; ảnh chụp mobile cả trang chủ và trang chi tiết |
| C5 | Tín hiệu "câu khó hiểu" | M | Người đọc chạm vào câu khó hiểu; app chỉ gửi mã mảnh. Mảnh bị chạm nhiều thì tự rút khỏi kho | Có review quyền riêng tư; cập nhật lời giải thích quyền riêng tư |

Sau Daily, dùng cùng nhà máy và cổng cho Tarot, Radar và Khám phá, mỗi màn một plan con.

## 5. Luật mới cho cổng (bổ sung vào đặc tả)

- **A16:** Thân bài Daily không chứa tên nhà, tên cung đầu nhà, chủ tinh, tên góc hay sai số. Tất
  cả phải nằm trong lớp "Vì sao".
- **A15 (mở rộng):** nhà, cung đầu nhà, chủ tinh, khoảng ngày và giờ trong lớp "Vì sao" phải khớp
  với engine.
- **Không rõ giờ sinh:** 0 lần nhắc tới nhà, cung đầu nhà hay chủ tinh.

## 6. Quyền riêng tư và bảo mật

- **Dữ liệu mới được lưu:** lịch sử mã mảnh (C2d), suy ra từ chart, nên coi là dữ liệu cá nhân suy
  diễn. Mã hóa giống Daily Note, cùng thời hạn giữ, xóa khi người dùng xóa.
- **Nhà máy nội dung:** chỉ chạy trên persona tổng hợp. Giám khảo Codex không nhận dữ liệu người
  dùng.
- **Lúc chạy app:** không gọi LLM.
- **C5:** chỉ gửi mã mảnh, không gửi câu chữ hay dữ liệu sinh. Cần cập nhật lời giải thích quyền
  riêng tư trong app, phần khai báo dữ liệu cho App Store / Google Play và chính sách quyền riêng tư
  nếu C5 làm phát sinh mục dữ liệu mới.

## 7. Còn mở

- Q2 và 12 lĩnh vực: đã chốt 03.11.2026 (mục 1.6, 1.7, 1.1).
- Ngưỡng số của cổng là tạm thời, hiệu chỉnh bằng bộ mẫu vàng.

## 8. Thay đổi sau rà soát toàn diện (2026-11-03)

Chi tiết: `docs/plans/2026-11-03-daily-v2-gap-register.md`. Các thay đổi:

- **Số liệu nền, mục 2.** "11/14 ngày cùng một transit chậm" là lựa chọn của planner. Theo đường
  production, phần transit chỉ hiện khoảng 1/10 ngày (258/2.700 note giả lập), vì gate hay từ chối và
  lùi về bản chỉ dựa trên lá số gốc. Daily hiện tại vì vậy còn ít bám theo ngày hơn số liệu ban đầu.
- **C2a mở rộng:**
  - nhánh cho người có giờ gần đúng hoặc chỉ có ngày sinh (`orb_bounds`);
  - tông nền của ngày;
  - xếp hạng theo trọng số và độ hiếm;
  - giới hạn số lựa chọn Mặt Trăng;
  - gộp một sự kiện bị tách thành hai thẻ;
  - khung giờ thật;
  - đặt tầng theo độ dài thật;
  - sự kiện bầu trời: trạm, trăng non/tròn, thực, đổi cung, nghịch hành, sinh nhật.

  Có thể tách thành C2a-2 để #178 giữ nhỏ.
- **C2b:** thêm góc với cung Mọc/Thiên Đỉnh. Chỉ dùng nhãn nhà khi nhãn không đổi trong khoảng sai số
  của giờ sinh.
- **C2c:** nối các lần đi qua do nghịch hành.
- **C2d:** không lưu lịch sử. Chọn biến thể bằng HMAC theo người, theo góc và theo chu kỳ trăng, để
  giữ thời hạn 24 giờ của Daily.
- **C4a (mới):**
  - gán nhánh A/B bằng HMAC, không lưu;
  - chỉ dùng bộ đếm tổng hợp;
  - chọn A hay C chủ yếu bằng phép thử người đọc (note thật cùng note mồi); A/B live chỉ làm rào
    chắn.
- **C5 làm trước A/B,** dùng lại tính năng cảm nhận (hit/miss) đang có.
- **C3a thêm luật an toàn hạng A** và dòng hỗ trợ tĩnh, chỉ dùng số đã xác minh.
- **C3b:**
  - giám khảo chấm 100% mảnh;
  - giám khảo khác họ model với người viết;
  - nghiệm thu trên note đã ghép;
  - kho mảnh không tự merge.
- **C1 sửa tiếp:** chặn cứng thật; baseline so với nhánh đích; ratchet theo từng câu; corpus phủ toàn
  bộ chuỗi nguồn.
- **Sửa ngay trên production, ngoài v2:**
  - múi giờ của người sinh ở miền Bắc 1960–1975;
  - 2/30 lá số Jyotish bị từ chối mỗi ngày;
  - `/metrics` mở công khai.
