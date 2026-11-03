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
7. **Đủ 12 nhà, không gộp** (owner, 03.11.2026). Mỗi nhà là một chùm nghĩa có cột nguồn; câu nhiều
   cửa để người đọc tự nhận ra; không nhãn cố định (mục 1.1, chốt sau nghiên cứu ba nguồn).

### 1.1 Mười hai nhà và cách chọn nghĩa (chốt 03.11.2026)

**Lịch sử.**
- Bản 927811b gán mỗi nhà một chip cố định (nhà 5 = "Hẹn hò"). Owner bác vì một nhà có nhiều nghĩa: Sao Mộc qua nhà 5 có thể là có con.
- Bản 9423dae chuyển sang "nhà là chùm nghĩa".
- Bản này chốt cách làm sau khi đối chiếu ba nguồn nền (`docs/research/2026-11-03-sach-chiem-tinh-nha-va-transit.md`):
  - Lilly, *Christian Astrology* (1647);
  - BPHS (bản Santhanam) cùng Phaladeepika;
  - Hand, *Planets in Transit*, cùng Sasportas, *The Twelve Houses*.
- Owner giao Claude chốt. Chọn **phương án B** (tâm lý hiện đại, câu nhiều cửa) làm nền, cộng **ba luật an toàn** lấy từ phương án A (cổ điển).

**Ba điều cả ba nguồn cùng đồng ý, nên là luật cứng:**
1. Một nhà là một chùm nghĩa. Nghĩa nào hiện ra phải qua nhiều lớp mới quyết.
2. Hai trường phái cổ điển (Lilly tr.53, BPHS 11.6) đặt **con cái lên đầu nhà 5** và **tình yêu ở nhà 7** (Lilly tr.54, Phaladeepika 1.13). Chỉ trường phái hiện đại thêm tình yêu vào nhà 5.
3. **Không nguồn nào để một transit đơn lẻ đoán có bầu hay cưới.**
   - Lilly coi transit là đồng hồ của vài ngày (ch. CLXXIV, tr.741) và canh hôn nhân bằng kỹ thuật khác (tr.589).
   - Phaladeepika đặt chu kỳ dasha trước transit (12.25).
   - Hand coi transit là năng lượng để làm việc cùng, không phải lời báo trước.

**Luật chọn nghĩa và viết:**

| Mã | Luật | Nguồn |
|---|---|---|
| N-1 | **Bảng chùm nghĩa 12 nhà có cột nguồn.** Mỗi nghĩa ghi "cổ điển", "hiện đại" hoặc "cả hai". Nhà 5 gồm: con cái ⚠ (cổ điển, đứng đầu); sáng tạo, tự thể hiện (hiện đại); niềm vui, giải trí, tiệc (cả hai); tình yêu, rung động (hiện đại); thể thao, chơi (hiện đại); may rủi ⚠ (cả hai); học, trí tuệ (Ấn). Bỏ "học trò" vì không có nguồn. Bảng đủ 12 nhà ở mục "Nhà 5 là nhà con cái trước" của báo cáo nghiên cứu. | Lilly tr.50–56; BPHS 11.2–11.13; Sasportas (chưa đối chiếu) |
| N-2 | **Ô hành tinh × nhà là năng lượng × vùng đời sống, viết như lời mời.** Có 120 ô (10 hành tinh × 12 nhà). Mỗi ô gồm: một câu chủ đề, 3–4 cách thường hiện ra, và một gợi ý "nếu… thì…". Không câu nào báo trước một chuyện sẽ xảy ra. | Hand (theo tóm tắt, chưa đối chiếu) |
| N-3 | **Câu nhiều cửa.** Câu về chủ đề đời người nêu ít nhất ba cách hiện ra. Mục ⚠ không bao giờ đứng một mình, không đứng đầu, không lên chip trang chủ. Đọc nguyên câu phải đúng với cả bốn persona (mục "Persona" bên dưới). | Luật riêng của Lá Lành |
| N-4 | **Góc với sao gốc chỉ đổi thứ tự trong dải nghĩa.** Sao chậm chạm Sao Kim gốc: tình cảm lên trước. Chạm Mặt Trăng gốc: gia đình, chăm sóc lên trước. Chạm Sao Thủy gốc: việc học lên trước. Không thêm nghĩa mới. Mục ⚠ vẫn không lên đầu. **Luật nguồn đứng trên N-4:** N-4 chỉ đổi thứ tự giữa các nghĩa được phép đứng đầu (nguồn "cổ điển" hoặc "cả hai", không ⚠). Ví dụ Sao Mộc ở nhà 5 chạm Sao Kim gốc: tình yêu ở nhà 5 chỉ có nguồn hiện đại nên không lên đầu; câu mở bằng niềm vui, giải trí, tình yêu chỉ là một cửa phía sau. Chủ tinh của nhà **không** dùng để chọn nghĩa; theo quyết định 1.2 nó chỉ dùng để thêm nhà (C2b). | Sasportas (chưa đối chiếu) |
| N-5 | **Thời gian thật của mỗi hành tinh.** Mặt Trăng: khoảng 2–2,5 ngày một nhà, góc chính xác vài giờ. Mặt Trời, Sao Thủy, Sao Kim: vài tuần, lâu hơn khi nghịch hành. Sao Hỏa: vài tuần đến vài tháng. Sao Mộc: khoảng 1 năm. Sao Thổ: khoảng 2,5 năm. Hành tinh nhanh chỉ nói tâm trạng và việc nhỏ. Chủ đề đời người (con cái, cam kết, nhà cửa, đổi việc) chỉ đến từ Sao Mộc trở ra, và chỉ trong tag "Xu hướng hiện tại". | Số thiên văn; Lilly tr.741 |
| N-6 | **Giới hạn tần suất mục ⚠.** Một người thấy mục ⚠ trong tag xu hướng nhiều nhất một lần mỗi tuần. Xoay vòng bằng HMAC theo người, không lưu lịch sử (khớp C2d). | Bảo vệ persona đang mong con |
| N-7 | **Không hỏi hoàn cảnh.** App không hỏi, không suy ra, không lưu tình trạng hôn nhân, chuyện có con hay ý định có con. Mang thai và khả năng có con là dữ liệu sức khỏe nhạy cảm. | Luật 91/2025/QH15 (cần kiểm lại văn bản chính thức khi làm C3a) |
| A-6 | **Sao Thổ hay Sao Hỏa ở nhà 5 không nhắc con cái** trong thân bài, vì sách cổ đọc hai sao này ở đây rất nặng nề. Chỉ nói nhịp và kỷ luật của niềm vui, hoặc sự sôi nổi. | Lilly tr.53, tr.603–604; thư Lilly gửi người học |
| A-7 | ~~Sàn 18 tuổi.~~ **Owner bỏ ngày 03.11.2026, không làm.** Chặn tuổi lúc nhập ngày sinh giữ nguyên. | (từng suy từ BPHS 16.18–20) |
| A-8 | **Jyotish tính riêng.** Bản đọc ngày Jyotish vẫn chỉ dùng lá số gốc như hiện nay (`planner.py`). Khi mở transit Jyotish (gochara): đếm từ Mặt Trăng gốc sidereal; dùng bảng ô tốt, điểm chặn (vedha) và bảng điểm Ashtakavarga. Không dùng lại bảng Tây. | Phaladeepika 26.1, 26.2, 26.7, 26.41 |
| N-8 | **Lớp "Vì sao Lá đọc vậy?" nói thật về luật của Lá.** Viết "Lá chọn không đoán chuyện này", không viết "chiêm tinh cổ không đoán", vì sách cổ vẫn đoán sự kiện. | Báo cáo nghiên cứu, mục đạo đức |

Dấu ⚠: chủ đề nhạy cảm, chỉ nói ở dạng rộng theo N-3 và N-6. Các chủ đề sau **không bao giờ vào bản đọc theo ngày**: cái chết, mất người thân, bệnh tật, bệnh viện, tù tội, kiện tụng.

**Persona** (bộ thử của cổng lớp C). Mỗi câu phải đúng và không làm đau bốn người:
- độc thân, chưa có con;
- có gia đình và con;
- đang mong con hoặc hiếm muộn;
- lớn tuổi, con đã lớn.

**Ví dụ nhà 5 sau khi chốt.**

| Hành tinh (thời gian) | Thân bài | Lớp "Vì sao Lá đọc vậy?" |
|---|---|---|
| Sao Mộc (khoảng 1 năm, chỉ trong tag xu hướng) | "Mấy tháng này, điều bạn yêu dễ lớn thêm: một sở thích, thứ bạn tự tay làm ra, một mối tình cảm, hay chuyện con cái. Nếu có một niềm vui bạn đã gác lại, đây là lúc mở nó ra." | "Sao Mộc đi qua nhà 5. Nhà 5 là con cái, niềm vui, sáng tạo; sách hiện đại thêm tình yêu. Sao Mộc làm mọi thứ rộng ra. Lá không đoán chuyện gì sẽ xảy ra, chỉ gợi những hướng hay gặp." |
| Sao Thổ (khoảng 2,5 năm, chỉ trong tag) | "Giai đoạn này, điều bạn yêu muốn bạn nghiêm túc hơn: một dự án cần kỷ luật, một niềm vui cần giờ cố định, hay một lời hứa cần rõ hơn. Nếu thấy chơi mà mệt, thử ít mà đều." (không nhắc con cái, A-6) | "Sao Thổ đi qua nhà 5. Sao Thổ đòi cam kết và kiên nhẫn." |
| Sao Kim (vài tuần) | "Mấy tuần này mắt dễ thấy đẹp và lòng dễ vui: một bữa ngon, một buổi đi chơi, một lời khen. Nếu muốn, tặng mình một thứ nhỏ." | "Sao Kim đi qua nhà 5, nơi Lilly gọi là niềm vui của Sao Kim." |
| Mặt Trăng (khoảng 2 ngày; giờ rõ nhất khi chạm sao gốc) | "Hôm nay lòng muốn chơi: vẽ vời, hát, nấu món mới, hay đùa với người thân." | "Mặt Trăng đi qua nhà 5: tâm trạng hợp với vui chơi và làm bằng tay." |

**Chip.** Không có chip cố định theo nhà. Chip gồm giờ và một câu móc ngắn rút từ câu chủ đề, ví dụ "17h30 · lòng muốn chơi" (luật móc ở mục 3). Mục ⚠ không lên chip.

**Không rõ giờ sinh.** Không dùng nhà. Chủ đề lấy theo chùm nghĩa của hành tinh gốc bị chạm, viết theo N-2 và N-3. Ví dụ Sao Kim gốc gồm tình cảm, cái đẹp, tiền và sự dễ chịu.

**Điều kiện để C3a xong:**
1. **Hand và Sasportas: owner chốt không mua sách (03.11.2026).** Vì vậy:
   - nghĩa có nguồn "cổ điển" hoặc "cả hai" dùng bình thường;
   - nghĩa chỉ có nguồn "hiện đại" (ví dụ tình yêu ở nhà 5) chỉ được là một trong các cửa của N-3, không bao giờ đứng đầu câu và không lên chip;
   - không trích lời hay số trang của Hand và Sasportas ở bất cứ đâu trong app.
2. **Đối chiếu số câu Phaladeepika với bản in** trước khi đưa vào lớp "Vì sao".
3. **Thêm luật đo câu chung chung vào cổng lớp C** (câu đúng với ai cũng được), vì đây là điểm yếu tự nhiên của câu nhiều cửa.

**Xét lại sau.** Khi C5 có số liệu, nếu người dùng chấm nhiều thẻ xu hướng là "không giống mình", lớp nên thêm đầu tiên là kiểm độ mạnh của nhà trong lá số gốc (phương án A-3). Lớp này chỉ làm câu nhẹ đi, không bao giờ tính điểm "khả năng có con".

**Mở rộng.** Thêm nghĩa hoặc thêm ô qua PR, kèm cột nguồn. Không gộp nhà, không rút chùm nghĩa thành một nhãn.

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
- Ba chip có giờ và câu móc, ví dụ "17h30 · lòng muốn chơi", "hôm nay · việc chính dễ trôi", "mấy ngày này · bạn bè gọi". Không có nhãn cố định theo nhà (mục 1.1).
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
- **Chốt mục 1.1 sau nghiên cứu ba nguồn (03.11.2026).** Phương án B (câu nhiều cửa, bảng nghĩa có
  cột nguồn) cộng ba luật của A: không nhắc con cái khi Sao Thổ/Sao Hỏa ở nhà 5, sàn 18 tuổi, Jyotish
  tính từ Mặt Trăng. Sửa sáu chỗ lệch sách của bản trước: tình yêu ở nhà 5 chỉ có nguồn hiện đại; bỏ
  "học trò"; thời gian Mặt Trăng và Sao Kim; chủ tinh không dùng để chọn nghĩa; bỏ câu mặc định có
  con; C3a chờ đối chiếu Hand và Sasportas.

## 9. Lộ trình tổng thể (triển khai lại 03.11.2026)

Owner yêu cầu triển khai lại kế hoạch sau khi chốt mục 1.1. Thứ tự theo ưu tiên của owner: nội dung →
quyền riêng tư → tính năng mới. Mỗi PR nhỏ, đi qua vòng tự động (author check → Codex → merge vào
`collab/integration`); main, release và deploy vẫn do owner.

**Đợt 1 — đang review (gói #180):**

| PR | Việc | Trạng thái 03.11 chiều |
|---|---|---|
| #177 | Plan, sổ lỗ hổng | Đã merge (bản 927811b); phần sửa mục 1.1 sau đó đi PR mới |
| #178 | C2a: chọn yếu tố trong ngày | Codex đòi sửa (pha không chắc chắn, múi giờ nơi sinh, góc vào orb lúc gần nửa đêm), đang sửa |
| #179 | C1: cổng ngôn ngữ dễ hiểu | Codex chặn vì một hằng số gắn ngày sinh thật của owner; đã xóa khỏi toàn bộ lịch sử nhánh. Đang sửa thêm hai P2 |
| #181, #182 | `/metrics` đóng; Jyotish không còn bị từ chối | Đã merge |
| #183 | Múi giờ miền Bắc 1960–1975 | Codex đòi báo "giờ chưa chắc" trên Radar và xóa nhà/góc khi chưa chắc, đang sửa |
| #184 | Sự kiện bầu trời | Codex đã duyệt, chờ merge |
| #185 | Khung "Rạng sáng 00–06h" | Chờ review |
| mới | Ngày mẫu trong test: dùng các ngày giả lập khác nhau | Đang làm |

**Đợt 2 — nền nội dung theo mục 1.1 (04–05.11):**
1. **C1-3, luật chặn cứng mới.** Chặn câu đoán sự kiện đời người (mang thai, cưới, chia tay, mất
   việc, bệnh, mất người thân) và câu giả định hoàn cảnh (độc thân, có con, giới tính) — HM-4. Đưa
   GT-1 về chặn cứng; thêm A9, A13, A15.
2. **C3a-1, bảng chùm nghĩa 12 nhà có cột nguồn** (N-1) dạng dữ liệu, kèm test: mỗi nghĩa có nguồn,
   mục ⚠ được đánh dấu, không có nghĩa thiếu nguồn. Bốn persona thành fixture cho cổng lớp C.
3. **HM-2/HM-3, sửa Daily và bản đọc đang chạy.** `knowledge.py` `HOUSES` lấy từ bảng mới (nhà 5 có
   con cái ở dạng rộng); `_short_arena` không gộp nhà; `HOUSE_ARENAS` không dồn 12 nhà vào 4 nhóm.
4. **C2b, nhà theo độ tin cậy của giờ sinh** và góc với cung Mọc/Thiên Đỉnh. (A-7 owner bỏ ngày
   03.11.2026.)

**Đợt 3 — bảng ô và nhà máy (05–07.11):**
5. **C3a-2, bảng 120 ô hành tinh × nhà** theo N-2…N-5 và A-6; luật đo câu chung chung (HM-10).
6. **C2c** nối các lần đi qua do nghịch hành; **C2d** chọn biến thể bằng HMAC, không lưu; N-6 (mục ⚠
   tối đa một lần mỗi tuần).
7. **C3b, nhà máy nội dung:** giám khảo chấm 100% mảnh, khác họ model; nghiệm thu trên note đã ghép;
   kho mảnh không tự merge.

**Đợt 4 — đưa tới người dùng (08–11.11):**
8. **C4:** API và giao diện Daily v2; trường mới trong envelope mã hóa; tính một lần mỗi ngày.
9. **C5 trước A/B:** dùng lại tính năng cảm nhận đúng/sai. Nếu thẻ xu hướng bị chấm "không giống mình"
   nhiều, xét thêm lớp độ mạnh nhà (A-3).
10. **C4a:** A/B giọng A và C bằng HMAC, chỉ bộ đếm tổng hợp.

**Chặn, cùng PR (PV-18, PV-20):** PR C4 hoặc C5 nào thêm dữ liệu mới phải cập nhật ngay trong chính PR đó
lời giải thích quyền riêng tư trong app, khai báo App Store / Google Play, bản đồ dữ liệu và chính sách.
Thiếu phần này thì PR không merge và tính năng không bật.

**Song song, không chặn:** Jyotish gochara theo A-8 (sau đợt 3); đối chiếu số câu Phaladeepika với
bản in.

**Cách đo xong.** Mỗi đợt xong khi các PR của đợt đã merge vào `collab/integration` với Codex APPROVE ở
đúng head, và các chỉ số ở mục 2 được đo lại trên engine mới.
