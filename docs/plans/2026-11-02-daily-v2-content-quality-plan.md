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
7. **Đủ 12 nhà, không gộp** (owner, 03.11.2026). Mỗi nhà là một chùm nghĩa; nghĩa nào nổi lên do cặp
   hành tinh × nhà, lá số gốc và độ dài transit quyết định, không có nhãn cố định (mục 1.1).

### 1.1 Mười hai nhà: mỗi nhà là một chùm nghĩa, không phải một nhãn (sửa 03.11.2026)

**Sửa bản 927811b.** Bản đó gán cho mỗi nhà một chip cố định, ví dụ nhà 5 là "Hẹn hò". Cách này sai:
- Một nhà có nhiều nghĩa. Nghĩa nào hiện ra còn tùy hành tinh đang đi qua, lá số gốc và đời sống của người đọc.
- Ví dụ của owner: Sao Mộc đi qua nhà 5 có thể là có con, hoặc có bầu rồi cưới. Đó không phải "hẹn hò mở rộng".
- Sách cổ coi nhà 5 trước hết là nhà con cái. Lilly (1647) xếp con cái và phụ nữ mang thai lên đầu, trước vui chơi. Chiêm tinh Ấn Độ gọi nhà 5 là *putra bhava* (nhà con cái) và coi Sao Mộc là sao chủ về con cái (*putrakaraka*).

**Code hiện tại mắc cùng lỗi** (sửa ở C2b/C3a, xem sổ lỗ hổng mục HM):
- `readings/knowledge.py`, `HOUSES[5]` viết "niềm vui, sáng tạo và hẹn hò", không có con cái.
- `_short_arena` gộp nhà 6 và 10 thành "công việc", nhà 4 và 12 thành "đời sống riêng", nhà 7 và 11 thành "quan hệ".
- `readings/daily_personalization.py`, `HOUSE_ARENAS` dồn 12 nhà vào 4 nhóm, chẳng hạn nhà 5 thành SELF_CARE và nhà 9 thành WORK.

Vẫn đủ 12 nhà, không gộp. Engine chọn chủ đề qua **bốn tầng**:

**Tầng 1: chùm nghĩa của nhà.** Đây là bảng tra nội bộ, không hiện ra như một nhãn. Các nghĩa không xếp theo thứ tự ưu tiên.
- Dấu ⚠ là chủ đề nhạy cảm, chỉ được nhắc ở dạng rộng (luật viết bên dưới).
- Dấu ⛔ là chủ đề chỉ được giải thích khi người dùng tự tra lá số, không bao giờ đưa vào bản đọc theo ngày.

| Nhà | Chùm nghĩa |
|---|---|
| 1 | thân thể, sức sống; vẻ ngoài; tính khí; cách mở đầu việc mới; hướng đi của chính mình |
| 2 | tiền kiếm được; tài sản, đồ đạc; giá trị bản thân; khả năng tự lo cho mình; tài năng có thể ra tiền |
| 3 | anh chị em, họ hàng gần; hàng xóm; nhắn tin, giấy tờ, ký kết nhỏ; học điều cơ bản; đi lại gần, xe cộ |
| 4 | cha mẹ; nhà cửa, đất đai; chuyển nhà; quê, gốc rễ, ký ức; đời sống riêng; giai đoạn khép lại một việc |
| 5 | con cái ⚠ (mang thai, sinh nở, nuôi dạy); tình yêu, hẹn hò; niềm vui, giải trí, sở thích; sáng tạo, biểu diễn; may rủi, đầu cơ ⚠; học trò |
| 6 | việc hằng ngày; đồng nghiệp, người làm cùng; nếp sinh hoạt và chăm cơ thể ⚠; vật nuôi; phục vụ người khác; việc vặt |
| 7 | vợ chồng, người yêu lâu dài; cưới hỏi ⚠; đối tác, hợp đồng; khách hàng; người đối diện, kể cả đối thủ công khai |
| 8 | thân mật, tình dục ⚠; tiền chung, nợ, thừa kế, bảo hiểm, thuế ⚠; thay đổi lớn, buông bỏ; mất mát ⛔; tâm lý sâu |
| 9 | đi xa, nước ngoài; học cao, thi cử; luật, tôn giáo, triết lý; thầy, người dẫn đường; xuất bản; gia đình bên vợ hoặc chồng |
| 10 | sự nghiệp, vị trí; danh tiếng; cấp trên, người có quyền; mục tiêu dài; người cha hoặc mẹ dẫn dắt mình |
| 11 | bạn bè; nhóm, cộng đồng; mạng lưới quen biết; mong ước, kế hoạch tương lai; lợi lộc từ công việc |
| 12 | nghỉ ngơi, giấc ngủ; thời gian một mình; chuyện thầm kín; chi tiêu khó thấy; tâm linh, buông bỏ; bệnh viện, nơi cách ly ⛔ |

**Tầng 2: cặp hành tinh × nhà quyết định mặt nào nổi.** Bảng có 10 hành tinh × 12 nhà = 120 ô. Mỗi ô gồm:
- một câu chủ đề đủ rộng, để mọi người ở hoàn cảnh nào cũng thấy mình trong đó;
- 2–3 cách chủ đề thường hiện ra, xếp theo mức hay gặp.

Ví dụ với nhà 5:

| Hành tinh | Câu chủ đề | Cách thường hiện ra |
|---|---|---|
| Sao Mộc (xu hướng, nhiều tháng) | điều mình yêu thương lớn thêm | chuyện con cái hoặc gia đình có thêm người; một niềm vui hay sở thích mở rộng; thứ mình tạo ra được đón nhận; tình cảm ấm thêm |
| Sao Thổ (xu hướng) | trách nhiệm với điều mình yêu | con cái cần nhiều thời gian hơn; tình cảm đi tới cam kết nghiêm túc; sáng tạo cần kỷ luật; ít thời gian chơi |
| Sao Kim (vài ngày) | dễ thấy vui, dễ rung động | một buổi hẹn hay lời khen; làm đẹp, nghệ thuật; thời gian dễ chịu với con hoặc người thương |
| Sao Hỏa (vài tuần) | muốn chơi hết mình | thể thao, thi đấu; tranh cãi vì cái tôi; nhiệt hơn trong tình cảm; con cái hiếu động |
| Mặt Trăng (vài giờ) | cần một chút vui cho riêng mình | chơi với con; gặp một người mình thích; làm một việc bằng tay |

Bảng đủ 120 ô được làm ở C3a:
- dựa trên ít nhất hai nguồn độc lập (một sách cổ điển và một sách hiện đại);
- Codex review;
- phải qua cổng lớp A, B và C.

**Tầng 3: lá số gốc dịch trọng tâm.** Ví dụ:
- transit chạm chủ tinh nhà 5, hoặc đi qua Sao Mộc gốc, thì nghiêng về con cái;
- transit chạm Sao Kim gốc thì nghiêng về tình cảm.

Tầng này chỉ dùng khi nhãn nhà không đổi trong khoảng sai số của giờ sinh (C2b).

**Tầng 4: độ dài transit quyết định cỡ chuyện.**
- Hành tinh nhanh (Mặt Trăng, Sao Thủy, Sao Kim, Mặt Trời, Sao Hỏa) chỉ nói về khoảnh khắc, tâm trạng, việc nhỏ trong ngày.
- Chủ đề đời người (con cái, cam kết, nhà cửa, đổi việc) chỉ đến từ hành tinh chậm, nằm trong tag "Xu hướng hiện tại", và luôn ở dạng khả năng.

**Luật viết** (thêm vào bộ chuẩn C3a và lint C1):
- **Không đoán sự kiện đời người**, như mang thai, cưới, chia tay, ly hôn, mất việc, bệnh hay mất người thân. Chỉ nói chủ đề và vài cách nó có thể hiện ra, để người đọc tự nhận ra mình. Ví dụ: "Chuyện con cái, một niềm vui riêng hay thứ bạn đang tạo ra có thể lớn thêm trong mấy tháng này."
- **Không giả định hoàn cảnh.** Không giả định tình trạng hôn nhân, có con hay không, giới tính hay nghề nghiệp. Mỗi câu phải đúng với bốn người đọc mẫu, dùng làm bộ persona cho cổng lớp C:
  - độc thân, chưa có con;
  - đã có gia đình và con;
  - đang mong con hoặc hiếm muộn;
  - lớn tuổi, con đã lớn.
- **Mang thai, sinh nở và khả năng có con là dữ liệu sức khỏe**, thuộc dữ liệu nhạy cảm theo Luật 91/2025/QH15. App không suy ra, không lưu, không hỏi. Chỉ nói "chuyện con cái" ở dạng khả năng, giọng tích cực, không bao giờ nói khó có con hay mất con.
- **Chủ đề ⛔ không vào bản đọc theo ngày.**

**Chip.** Không còn chip cố định theo nhà:
- Chip gồm giờ và một câu móc ngắn, rút từ câu chủ đề của ô hành tinh × nhà, ví dụ "17h30 · dễ thấy vui" (đúng luật móc ở mục 3).
- Tên nhà và chùm nghĩa chỉ nằm trong lớp "Vì sao Lá đọc vậy?", ví dụ "Nhà 5: con cái, tình yêu, niềm vui, sáng tạo".

**Không rõ giờ sinh.** Không dùng nhà. Chủ đề lấy theo chùm nghĩa của hành tinh gốc bị chạm, cũng nói rộng như trên. Ví dụ Sao Kim gốc gồm tình cảm, cái đẹp, tiền và sự dễ chịu, chứ không gán "Hẹn hò" hay "Đối tác".

**Mở rộng.** Thêm nghĩa hoặc thêm ô qua PR. Không gộp nhà, không rút chùm nghĩa thành một nhãn.

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
- Ba chip có giờ và câu móc, ví dụ "17h30 · dễ thấy vui", "hôm nay · việc chính dễ trôi", "mấy ngày này · bạn bè gọi". Không có nhãn cố định theo nhà (mục 1.1).
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

- Q2 và 12 nhà: đã chốt 03.11.2026 (mục 1.6, 1.7, 1.1). Bản nhãn cố định đã bỏ cùng ngày theo phản hồi owner.
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
- **Nghĩa của nhà (phản hồi owner 03.11.2026).** Bỏ bảng chip cố định theo nhà. Nhà là chùm nghĩa,
  chủ đề do cặp hành tinh × nhà, lá số gốc và độ dài transit chọn. Thêm luật không đoán sự kiện đời
  người, không giả định hoàn cảnh, và bốn persona cho cổng lớp C (mục 1.1; sổ lỗ hổng HM-1…HM-7).
