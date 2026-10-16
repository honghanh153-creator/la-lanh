# Cá nhân hoá và đa dạng nội dung: Tarot (B2), Astro (B3), Hợp gu (B4)

Kế hoạch 16/10/2026. Người thực hiện: Claude. Người review: Codex. Owner yêu cầu: "mở rộng mức độ cá
nhân, đa dạng của cả tarot, astro, và phần hợp gu". Nguồn: Issue #6, audit 11/10
(`docs/research/2026-10-11-content-engine-audit.md`), review Tarot 08/10, code tại `main` 8362222
(số dòng bên dưới lấy từ commit đó).

**Owner đã chốt (16/10/2026):** chọn đúng các đề xuất ở mục 8: chiến lược bậc thang S1 → S3 → S2,
Astro A2 (làm phần A1 sớm), Tarot T2, Hợp gu R2, thứ tự Tarot → Astro → Hợp gu, tín hiệu cá nhân để
chặng 2 và người dùng tự bật, checklist tâm lý vào chuẩn nội dung. Các phương án đã cân nhắc nằm ở mục
10, phần tâm lý người dùng ở mục 11, đối chiếu user flow ở mục 12. Bản phân tích trình bày cho owner (có
bảng chấm điểm) được giữ riêng; nội dung quyết định đã chép đầy đủ vào file này.

## 0. Định nghĩa đo được

Hai chữ "cá nhân" và "đa dạng" được quy thành chỉ số. Mỗi chỉ số là một floor trong
`content-matrix-baseline.json` để không thể lùi lại.

| Chỉ số | Ý nghĩa | Đo bằng |
|---|---|---|
| **Cá nhân** | Hai người khác nhau hỏi/xem cùng lúc thì nhận nội dung khác nhau, và khác vì dữ liệu của chính họ | Tỷ lệ thẻ giống hệt nhau giữa các cặp profile cùng ngày; số tín hiệu thực sự đổi nội dung |
| **Đa dạng theo thời gian** | Một người dùng lâu không gặp lại cùng câu sớm | Số tình huống khác nhau trong 30/60 ngày; khoảng cách ngắn nhất giữa hai lần lặp của cảnh/hành động/tiêu đề |
| **Đa dạng trong một bài** | Các phần của một bản đọc không lặp ý nhau | Trùng ý giữa các mục (đã có cho Daily, mở rộng cho Tarot/Radar) |
| **Đúng và an toàn** | Đa dạng không được đổi nghĩa, dự đoán hay đoán ý người khác | Các gate hiện có + gate mới theo từng mảng |

Đo trên dữ liệu tổng hợp: 50 profile (cả có giờ và chỉ ngày) × 60 ngày; ngân hàng câu hỏi Tarot
khoảng 290 câu; 50 cặp Radar. Không dùng dữ liệu người dùng thật.

## 1. Hiện trạng đã đo

### Astro (note ngày)

- **Chọn biến thể chỉ theo ngày, không có salt người dùng** (`application.py:134`,
  `interpretive_lenses.py:393-411`):
  - Hai người cùng tình huống trong cùng một ngày nhận thẻ **giống hệt**.
  - Cảnh giữ nguyên **6 ngày liền**, hành động giữ nguyên **48 ngày**.
  - Pool có 2 tình huống thì mỗi tình huống chỉ gặp tiêu đề chẵn hoặc lẻ.
- **Người chỉ nhập ngày sinh: một tình huống cố định theo cung, cả năm** (`daily_personalization.py:27`;
  test khẳng định 1 nghĩa trong 365 ngày).
- **Transit hiếm khi thắng:** cặp natal (rank 3) luôn thắng transit (rank 2), nên note ít đổi theo ngày.
- **Kho nội dung:** 15 tình huống × 6 tiêu đề × 8 cảnh × 8 hành động. "Vì sao hôm nay?" là một khung cố
  định. Baseline vẫn ghi 10 họ tình huống, đã cũ.
- **Tín hiệu chỉ được lưu, chưa dùng:** mood, phản hồi trúng/chưa trúng, note đã lưu. Gate doc ghi rõ
  muốn dùng phản hồi để xếp hạng lại thì cần consent riêng (`content-matrix-release-gate.md:127`).
- Chưa có chỉ số đếm số tình huống khác nhau mà một người gặp, hay độ trùng giữa các người dùng.

### Tarot

- **Không trả lời câu hỏi:**
  - Intent là so khớp chuỗi con theo thứ tự cho 5 intent; mọi câu có chữ "hỏi" rơi vào giao tiếp.
  - Không nhận ra câu hỏi có/không.
  - Tiêu đề cố định theo intent (`engine.py:136-142,568-581`).
- **Nghĩa không theo vị trí:**
  - Vị trí 1 của trải 3 lá rơi vào "Ý chính của lá: …".
  - Vị trí 3 lặp lại cạm bẫy.
  - Hành động giống nhau ở mọi vị trí (`engine.py:383-436,479-484`).
- **Tóm tắt là danh sách**, do gate bắt nêu tên mọi lá (`:348-380,512`).
- **Chữ thừa:** "Ý chính của lá:", "Thử nhé:", "Ví dụ: Có lần…" dưới nhãn "Ví dụ để đối chiếu". Web
  hiện tên Anh và dòng "Engine …".
- Gate ép độn chữ (`review_agent.py:194,213,228`). Audit chỉ có 1 câu hỏi cho mỗi chủ đề.
- **Mỗi lá × chủ đề chỉ có một câu nghĩa:** hai người rút cùng lá nhận cùng câu, dù câu hỏi khác.
- Phiên đã rút đóng băng 29 ngày 18 giờ. Hiện ở renderer v6, gates v4, knowledge v4, meaning brief v2.

### Hợp gu (Radar)

- **Cấu trúc:** tiêu đề, bản đồ 3 chỉ số, 4 mục (hợp, ma sát, góc nhìn, kiểm chứng) (`radar/reading.py:359-447`).
- **Contact → 8 chủ đề; mỗi chủ đề một cảnh cố định** (`SCENE_COPY` :194). Tiêu đề và thân cố định theo
  chủ đề; chỉ có 11 cặp hành tinh được viết riêng. Phần riêng theo contact chỉ có câu nối và câu mở đầu
  về góc chiếu.
- **Ngữ cảnh** (crush/bạn/người yêu/ai đó) chỉ đổi thẻ kiểm chứng. **Giọng** (4 lựa chọn) chỉ thêm tiền tố
  vào câu hành động (:567-598).
- Kế hoạch biên tập đã nối một phần: tối đa 3 trong 15 khái niệm, chọn theo hash.
- Audit chỉ dùng **một cặp** × 4 ngữ cảnh × 4 giọng.
- Riêng tư: chart người kia tính xong rồi bỏ; nhãn và kết quả được mã hoá; giữ 30 ngày.

## 2. Nguyên tắc chung

1. **Đa dạng không đổi nghĩa.** Biến thể nằm trong cùng một "ý" đã được duyệt: cùng tình huống, cùng
   hành động gốc. Gate meaning và anti-influence chạy trên mọi biến thể.
2. **Salt riêng từng người, tất định, không cần lưu thêm.** Biến thể chọn theo
   `HMAC(khoá server, owner_scope + bề mặt + ngày/phiên)`, rồi hoán vị theo người: cùng người + cùng
   ngày thì luôn ra cùng thẻ (cache, chia sẻ, đổi giọng vẫn ổn định), nhưng hai người khác nhau thì
   khác nhau. Không tạo bảng lịch sử mới.
3. **Chống lặp bằng hoán vị, không bằng bộ nhớ.** Mỗi người có một hoán vị riêng của (tiêu đề × cảnh ×
   hành động), nên trong một chu kỳ không lặp và mọi trục đổi mỗi ngày. Không còn kiểu đổi theo hệ cơ số
   (6/48 ngày).
4. **Tín hiệu người dùng tự cung cấp chỉ dùng khi họ bật**, có công tắc, giải thích và nút xoá; mặc định
   tắt. Ngoại lệ: tín hiệu thuộc đúng mục đích của chính màn đó (câu hỏi Tarot, ngữ cảnh Radar, lens của
   note) được dùng như hiện nay.
5. **Không gửi gì mới cho Luna** ngoài các giá trị đóng (nhãn), có test chặn chữ của người dùng. Luna
   hiện vẫn tắt.
6. **Phiên bản và đóng băng:** mỗi đợt bump phiên bản. Bản đã lưu, chia sẻ hoặc đang trong phiên vẫn giữ
   nguyên, không render lại.

## 3. Tarot B2: trả lời đúng câu hỏi và riêng cho từng câu

Giữ nguyên 8 tiêu chí của Issue #6. Thiết kế:

- **Hiểu câu hỏi** (`QuestionFrame`, tất định, trên server):
  - **form:** có/không, chọn A/B, làm sao, vì sao, khi nào → đổi thành "điều cần sẵn sàng", mở.
  - **topic:** chấm điểm nhiều tín hiệu thay cho so khớp đầu tiên.
  - **action:** nhóm hành động đóng, khoảng 30 nhãn.
  - **Không trích nguyên văn câu hỏi vào bản đọc**, vì bản đọc nằm trong payload Luna.
  - Các bộ lọc an toàn hiện có chạy trước.
- **Vị trí quyết định nghĩa:** mỗi vị trí có một vai (đang rõ / dễ bỏ qua / bước tiếp / các vai trải 5
  lá), chọn trường dữ liệu và khung câu riêng. Bỏ nhánh chung chung. Hành động chỉ ở vai bước tiếp.
- **Hướng nghiêng** cho có/không và A/B:
  - Thêm nhãn `lean ∈ {mở, giữ, hai mặt}` cho mỗi lá × chủ đề (≤ 468 nhãn: mặc định theo lá, chủ đề
    chỉ ghi đè khi khác), có trọng số theo vai.
  - Ba mức: **"nghiêng về thử {action}" / "cân nhắc thêm trước khi {action}" / "chưa rõ"**, kèm 1–2 lý
    do trỏ tới vai và lá. Không phán, không dự đoán.
- **Tóm tắt dạng câu chuyện:** nối các vai bằng liên từ. Tiêu đề dựng từ form + hướng nghiêng + lá trọng
  tâm.
- **Đa dạng (mới theo yêu cầu owner):**
  - Mỗi vai có **3 khung câu** cho mỗi giọng; chọn theo salt phiên, nên cùng lá với hai câu hỏi khác nhau
    ra câu khác nhau.
  - Ví dụ đời thường có **2–3 cảnh** cho mỗi lá × chủ đề (hiện là 1). Ưu tiên các lá rút nhiều nhất theo
    audit.
  - Câu hỏi tự soi theo vai × form, không còn một câu chung.
- **Cá nhân (tuỳ chọn, cần owner duyệt):** nếu người dùng đã có chart và bật "nối Tarot với lá số", thêm
  một câu ngắn nối lá trọng tâm với **tình huống note hôm nay** của họ. Chỉ dùng nhãn tình huống, không
  dùng chi tiết chart. Mặc định tắt.
- **Gate và audit:**
  - Thay gate "nêu tên mọi lá" bằng gate liên kết giữa các vai.
  - Thêm gate: hướng nghiêng nhất quán; không quyết định thay hay dự đoán; câu đúng vai.
  - Bỏ mức tối thiểu số chữ cho Tarot.
  - Ngân hàng câu hỏi ≥ 8 câu cho mỗi chủ đề × form, chạy với 4 giọng.
- **Giao diện:** khối "Hướng nghiêng"; bỏ tên Anh và dòng "Engine"; một nhãn "Ví dụ" duy nhất; trường
  mới đều tuỳ chọn để phiên cũ vẫn hiển thị.
- **Phiên bản:** renderer v7, gates v5 (thành hằng số), knowledge v5, meaning brief v3. Sửa default cũ
  và tài liệu cũ.

## 4. Astro B3: note ngày riêng cho từng người và đổi mỗi ngày

- **Salt người dùng + hoán vị** (nguyên tắc 2–3):
  - Thay `daily_mixed_radix_slots` bằng hoán vị theo người.
  - Trong một ngày, tình huống chọn từ top-K của người đó (K = 3–4 theo điểm), có luân phiên. Tình
    huống mạnh nhất chiếm ≤ 50% số ngày, không còn kiểu chỉ một cặp natal áp đảo.
- **Người chỉ có ngày sinh:** thay "một tình huống mỗi cung cả năm" bằng một pool 4–6 tình huống từ:
  - cung, nguyên tố, tính chất (modality) của Mặt Trời;
  - **transit tới Mặt Trời natal**, tính được chỉ từ ngày sinh;
  - lens đang chọn.

  Vẫn ghi rõ là "bản tóm tắt từ ngày sinh".
- **Transit có chỗ đứng:**
  - Cân lại rank để transit trong orb chặt (≤ 2°, hoặc trạm/đổi chiều) được vào top-K.
  - "Vì sao hôm nay?" có 3–4 khung câu theo loại transit (đang tới gần / chính xác / tách dần) và chống
    lặp cùng một transit quá 3 ngày liền.
  - Giữ hợp đồng evidence binding.
- **Mở rộng kho nội dung:**
  - Thêm **5 tình huống mới**, 15 → 20 (danh sách đề xuất ở bước B3-0, owner duyệt), cùng chuẩn 6 × 8
    × 8.
  - Mỗi tình huống thêm hành động theo lens (công việc, giao tiếp, năng lượng), không chỉ quan hệ.
- **Tín hiệu người dùng (opt-in, mặc định tắt):**
  - **Mood hôm nay → nhịp của hành động:** Đuối/Căng thì chọn hành động nhẹ, Rực thì chọn hành động chủ
    động, trong cùng tình huống. Chỉ dùng mood của chính ngày đó, không suy ra hồ sơ cảm xúc.
  - **Phản hồi trúng/chưa trúng → xếp hạng lại tình huống:**
    - chỉ cộng/trừ điểm cho họ tình huống, lưu tổng hợp ở mức họ, giữ 30 ngày;
    - xem và đặt lại được trong Mình;
    - đúng điều kiện consent mà gate doc đã ghi.
  - Copy consent, data map, Apple App Privacy và Google Data Safety cập nhật cùng lúc. **Kiểm lại Luật
    91/2025 và NĐ 356/2025 từ nguồn chính thức trước khi code**, vì đây là dữ liệu suy ra về cảm xúc.
- **Cà khịa:** câu mới cần ánh xạ Cà khịa và owner duyệt (file Excel như lần 16/10).

## 5. Hợp gu B4: bản đọc cặp riêng cho từng cặp

- **Cảnh theo chủ đề × ngữ cảnh:** 8 chủ đề × 4 ngữ cảnh × 2–3 biến thể thay cho 8 cảnh cố định. Chọn
  theo salt của kết quả, nên ổn định khi mở lại.
- **Câu theo contact:**
  - Viết câu riêng cho các cặp hành tinh × họ góc chiếu (hài hoà / căng / hợp) hay gặp nhất, ưu tiên theo
    tần suất trong 50 cặp tổng hợp.
  - Thêm câu về **cân bằng nguyên tố/tính chất của hai người**, như "một người nhanh, một người chậm",
    lấy từ hai chart.
  - Giữ ràng buộc không đoán ý người kia.
- **Ngữ cảnh đổi cả mục "hợp" và "ma sát"**, không chỉ thẻ kiểm chứng: cùng một contact, với crush và
  với đồng nghiệp sẽ nói khác.
- **Giọng đổi cả câu**, không chỉ tiền tố: 4 giọng có khung riêng cho tiêu đề, thân và hành động; Cà khịa
  cần owner duyệt.
- **Kế hoạch biên tập:** nối khái niệm vào các chương hiển thị, mở rộng 15 → khoảng 30 khái niệm có thể
  xuất bản. Sửa ghi chú cũ trong gate doc.
- **Audit:** 50 cặp tổng hợp (có giờ và không rõ giờ) × 4 ngữ cảnh × 4 giọng; đo độ trùng câu giữa các
  cặp và số câu riêng theo contact.
- Không lưu thêm dữ liệu của người kia. Salt chỉ dùng mã kết quả đã có.

## 6. Thứ tự làm (mỗi bước một PR, Codex review @ SHA)

| Bước | Nội dung |
|---|---|
| **P0** (docs) | Kế hoạch này; US-20 (Tarot) và AC cho B3/B4; ngân hàng câu hỏi; danh sách 5 tình huống mới; quyết định owner (mục 8) |
| **P1** (đo) | Thêm chỉ số đa dạng/cá nhân vào audit (Daily 50 profile × 60 ngày, Tarot ngân hàng câu hỏi, Radar 50 cặp); ghi baseline hiện tại. Chưa đổi nội dung |
| **B2-1…4** | Tarot: hiểu câu hỏi → nghĩa theo vai và dọn chữ thừa → hướng nghiêng, tóm tắt, khung câu đa dạng → Cà khịa, phiên bản, Luna |
| **B3-1** | Astro: salt và hoán vị theo người, top-K luân phiên, pool cho người chỉ có ngày sinh, cân lại transit |
| **B3-2** | Astro: 5 tình huống mới, hành động theo lens, khung "Vì sao hôm nay?" |
| **B3-3** (sau consent) | Astro: mood và phản hồi opt-in, copy riêng tư, khai báo store |
| **B4-1…2** | Hợp gu: cảnh × ngữ cảnh, câu theo contact và nguyên tố → giọng đổi cả câu, kế hoạch biên tập |
| Release | Theo từng mảng, đúng runbook. Mỗi đợt có file Excel để owner duyệt nội dung mới |

**Thứ tự đã chốt (bậc thang, 3 chặng):**

- **Chặng 1 (S1, không dữ liệu mới, không chi phí AI):**
  1. P0 → P1.
  2. **B3-1a, phần A1:** salt + hoán vị theo người, top-K luân phiên. Bước nhỏ, tác động rộng; làm ngay
     sau P1, song song với B2-1.
  3. **B2-1…4:** Tarot T2.
  4. **B3-1b + B3-2, phần còn lại của A2:** pool cho người chỉ có ngày sinh, cân lại transit, khung "Vì
     sao hôm nay?", 5 tình huống mới, hành động theo lens.
  5. **B4-1…2:** Hợp gu R2.
- **Chặng 2 (S3 nhẹ, người dùng tự bật):** chỉ sau khi rà Luật 91/2025 + NĐ 356/2025 từ nguồn chính thức
  và có copy consent mới.
  - B3-3 (A3): mood và phản hồi.
  - Gợi ý cách hỏi Tarot: phần đầu của T3, mở rộng câu gợi hỏi lại hiện có thành gợi ý theo chủ đề.
  - Thẻ câu hỏi Hợp gu: phần đầu của R3.
  - Nối Tarot với tình huống note hôm nay.
- **Chặng 3 (S2):** bật Luna cho note và Tarot; nhật ký Tarot; nhắc lại Hợp gu. Chỉ làm khi đủ điều kiện
  của Issue #7 (chấm mẫu, DPA, governance, khai báo).

**Khối lượng nội dung cần viết:**

| Mảng | Nội dung |
|---|---|
| Tarot | ≤ 468 nhãn lean; khoảng 3 khung × 8 vai × 4 giọng; 1–2 cảnh thêm cho các lá rút nhiều |
| Astro | 5 tình huống × (6 + 8 + 8) câu; hành động theo lens |
| Hợp gu | khoảng 64–96 cảnh; câu theo contact hay gặp; khung 4 giọng |

Tất cả đi qua gate và Excel duyệt.

## 7. Quality gates (AGENTS.md)

- **Hợp đồng:**
  - Viết US-20 (Tarot) và AC cho B3/B4. Ánh xạ từng thay đổi tới AC.
  - Cập nhật tarot engine spec, content standard, content-matrix-release-gate, baseline, contract API
    (trường mới tuỳ chọn) và web types.
- **Bảo mật:**
  - Không thêm endpoint public.
  - Khoá HMAC salt là secret server, không phải khoá mã hoá dữ liệu.
  - Bộ phân loại câu hỏi chỉ tách token (≤ 280 ký tự), không dùng regex lồng nhau.
  - Công tắc opt-in đi qua CSRF và quyền sở hữu phiên như các cài đặt khác.
- **Riêng tư:**
  - `QuestionFrame` và điểm phản hồi theo họ là dữ liệu suy ra: mã hoá trong payload phiên/hồ sơ, không
    log, xoá cùng hồ sơ.
  - Mood và phản hồi chỉ dùng khi bật, giữ 30 ngày, có nút đặt lại.
  - Payload Luna chỉ có nhãn đóng.
  - Cập nhật `store-privacy-data-map.md`, privacy copy trong app, Apple/Google declarations.
  - Kiểm lại luật Việt Nam hiện hành trước B3-3.

## 8. Quyết định của owner (16/10/2026)

| # | Câu hỏi | Đã chọn |
|---|---|---|
| 1 | Chiến lược chung | Bậc thang: S1 nội dung tất định mở rộng → S3 học từ phản hồi (opt-in) → S2 Luna |
| 2 | Astro | **A2** (A1 làm sớm như bước riêng) |
| 3 | Tarot | **T2**: 3 mức hướng nghiêng (thử / cân nhắc thêm / chưa rõ), không có mức "chưa nên"; bỏ tên lá tiếng Anh khỏi nội dung, chỉ giữ trong chi tiết thu gọn; câu "khi nào" đổi thành "điều cần sẵn sàng trước" |
| 4 | Hợp gu | **R2** |
| 5 | Thứ tự | Tarot → Astro → Hợp gu, A1 chen sớm |
| 6 | Mood, phản hồi, nhật ký | Chặng 2, mặc định tắt, người dùng tự bật; nối Tarot với note hôm nay cũng ở chặng 2 |
| 7 | Checklist tâm lý | Đưa vào chuẩn nội dung (`la-lanh-plain-vietnamese-content-standard.md`), áp cho mọi câu mới |

Còn chờ owner ở P0: chọn 5 tình huống Astro mới từ danh sách đề xuất, và duyệt câu Cà khịa của từng đợt
qua file Excel.

## 9. Không thuộc phạm vi

Bật Luna, lá ngược chiều, trải bài mới, đổi cách bốc lá, Lá Chung, thông báo đẩy, ghép đôi người lạ.

## 10. Phương án đã cân nhắc

Chấm 1–5 trên: giá trị cho người dùng, tốc độ ra mắt, khối lượng nội dung, riêng tư/pháp lý, chi phí vận
hành, rủi ro nội dung, khả năng đo.

| Chiến lược | Ý chính | Điểm mạnh | Điểm yếu |
|---|---|---|---|
| **S1 · Nội dung tất định mở rộng** (chọn, chặng 1) | Viết thêm nội dung đã duyệt, chọn theo người + ngày + câu hỏi | Không dữ liệu mới, chi phí gần 0, đo được | Khối lượng viết và duyệt lớn |
| S2 · Khung tất định + Luna | Engine giữ nghĩa, Luna làm mượt câu | Câu tự nhiên | Chờ chấm mẫu, DPA, consent; không sửa được cấu trúc |
| S3 · Học từ người dùng (opt-in) | Mood và phản hồi chỉnh lựa chọn | Cảm giác "app hiểu mình" rõ nhất | Dữ liệu suy ra về cảm xúc; rủi ro chỉ thấy điều mình thích |

| Mảng | Phương án 1 | Phương án 2 (chọn) | Phương án 3 |
|---|---|---|---|
| Astro | A1: xoay vòng riêng (salt, hoán vị, top-K) | **A2**: A1 + pool cho người chỉ có ngày sinh, transit có chỗ đứng, 5 tình huống mới, hành động theo lens | A3: A2 + mood/phản hồi opt-in (chặng 2) |
| Tarot | T1: sửa cấu trúc (vai, tóm tắt liền, dọn chữ thừa) | **T2**: T1 + hiểu câu hỏi, hướng nghiêng 3 mức, khung câu và ví dụ đa dạng | T3: T2 + gợi ý cách hỏi, đào sâu một lá, nhật ký (chặng 2–3) |
| Hợp gu | R1: cảnh × ngữ cảnh, giọng đổi cả câu | **R2**: R1 + câu theo góc chiếu giữa hai chart và cân bằng nguyên tố, ngữ cảnh đổi cả "hợp"/"ma sát" | R3: R2 + thẻ câu hỏi để nói chuyện, góc nhìn hai phía, nhắc lại (chặng 2–3) |

Lý do không chọn S2 trước: làm mượt câu trên nội dung đang lặp chỉ che triệu chứng. Lý do không chọn T1:
không giải quyết kỳ vọng chính, là được trả lời đúng câu hỏi. Lý do R2 thay R1: R1 vẫn để hai cặp cùng
chủ đề nhận bài gần giống nhau.

## 11. Tâm lý người dùng

### Năm tâm thế khi mở app

| Tâm thế | Thường gặp ở | Cần | Tránh |
|---|---|---|---|
| Nghi thức nhỏ cho mình | Note buổi sáng | Ngắn, ấm, mỗi ngày một chút mới | Lặp, dài, giáo huấn |
| Bất an trước quyết định | Tarot "có nên… không" | Hướng nghiêng có lý do, cảm giác mình nắm quyền | Phán, mơ hồ, bị dẫn dắt |
| Bận tâm về một người | Hợp gu, Tarot về crush, thường về đêm | Quay về điều mình muốn và cách mở lời | Đoán ý người khác, nuôi suy nghĩ lặp |
| Hiểu mình | Reveal, lá số | Cụ thể, có căn cứ | Câu ai đọc cũng đúng (Barnum) |
| Kết nối | Chia sẻ thẻ, Hợp gu | Thẻ khác bạn bè, an toàn khi chia sẻ | Lộ thông tin riêng |

Mối quan tâm tới chiêm tinh tăng theo mức bất an (Padgett & Jorgenson, 1982), và chiêm tinh được dùng để
khẳng định bản thân và đối phó với khủng hoảng (Lillqvist & Lindeman, 1998; đọc qua tóm tắt thứ cấp,
mẫu nhỏ). Một nghiên cứu định tính nhỏ cho thấy người dùng Tarot coi lá bài như tấm gương tự soi (Hofer,
2009). Vì vậy nội dung phải trao lại cảm giác tự chủ, không nuôi sự phụ thuộc.

### Nguyên lý → quy tắc nội dung

| Nguyên lý | Bằng chứng | Quy tắc |
|---|---|---|
| Tự chủ, năng lực, gắn kết | Ryan & Deci (2000) | Đưa lựa chọn; việc nhỏ làm được trong ngày; Lá là bạn đồng hành, không phải thầy |
| Phản kháng khi bị ra lệnh | Altendorf và cộng sự (2019); kết quả lặp lại chưa đồng nhất | Không mệnh lệnh; Tarot chỉ "nghiêng về" |
| Kế hoạch "khi… thì…" | Gollwitzer & Sheeran (2006), d ≈ 0,65 | Việc nhỏ kèm tình huống kích hoạt |
| Đỉnh và kết | Fredrickson & Kahneman (1993); phân tích gộp 2022 | Đỉnh là câu "à ra vậy"; kết bằng việc nhỏ tích cực, không kết bằng cảnh báo |
| Hiệu ứng Barnum | Forer (1949) | Mỗi câu gắn với căn cứ riêng; không khen chung chung |
| Thiên lệch tiêu cực | Baumeister và cộng sự (2001) | Tối đa một ý tiêu cực mỗi bài, luôn kèm lối ra |
| Bất định và kiểm soát | Padgett & Jorgenson (1982) | "Điều bạn quyết được hôm nay"; không định mệnh, không ép quay lại |
| Suy nghĩ lặp về đêm | Thực hành chung; app đã có nhắc nền tối sau 21:00 | Sau 21:00 câu ngắn hơn; hỏi Tarot lại cùng câu trong 24 giờ thì mở lại bài cũ |

### Persona kiểm thiết kế (tổng hợp, không phải người dùng thật)

- **Minh Anh, chỉ nhập ngày sinh, mở app 30 giây mỗi sáng:**
  - Hiện tại: một tình huống cả năm, dễ bỏ app sau khoảng 2 tuần.
  - A2 giải quyết bằng pool theo transit tới Mặt Trời và việc nhỏ có tình huống kích hoạt.
- **Huy, phân vân nhận việc, mở Tarot lúc 23:00:**
  - Hiện tại: tiêu đề cố định, không có hướng nghiêng.
  - T2 trả lời bằng "cân nhắc thêm trước khi nhận lời" kèm lý do. Hỏi lại cùng câu thì mở lại bài cũ.
- **Linh, crush chưa trả lời:**
  - Hiện tại: Hợp gu ra cảnh cố định. Tarot từ chối câu đoán ý người kia và đưa một câu hỏi lại chung,
    giống nhau cho mọi trường hợp (`engine.py:187-195`).
  - R2 + T2 nói về nhịp của hai người. Chặng 2 thêm thẻ câu hỏi để mở lời.
- **Thảo, nhập đủ giờ và nơi sinh, hay bấm trúng/chưa trúng:**
  - Hiện tại: phản hồi không làm thay đổi gì.
  - Chặng 1: Lá ghi nhận phản hồi bằng lời. Chặng 2 (tự bật): A3 chỉnh tình huống, có giải thích và nút
    đặt lại.

## 12. Đối chiếu user flow

| Flow | Route | Điểm nghẽn hiện tại | Giải bằng |
|---|---|---|---|
| Lần đầu | `/welcome → /birth → /reveal → /home` | Người chỉ có ngày sinh gặp một tình huống cả năm | A1, A2; nhắc nhẹ thêm giờ sinh sau 7 ngày (đã có slot "Lá nhắc") |
| Vòng hằng ngày | `/home → /note/today`, mood, trúng/chưa trúng, `/saved`, `/card` | Mood và phản hồi là ngõ cụt | Chặng 1: Lá ghi nhận bằng lời; chặng 2: A3 opt-in |
| Tarot | `/tarot → /tarot/:sessionId` | Ô nhập không hướng dẫn cách hỏi; kết quả không trả lời câu hỏi | T2; chặng 2: gợi ý cách hỏi theo chủ đề |
| Hợp gu | `/radar → /radar/start` hoặc `/radar/invite` → `/radar/result/:id` | Chọn ngữ cảnh và giọng gần như không đổi kết quả; bài dừng ở thẻ kiểm chứng | R2; chặng 2: thẻ câu hỏi |

## 13. Tham chiếu

- Sản phẩm, theo mô tả của chính hãng trên trang App Store, chưa kiểm chứng độc lập:
  - Co–Star: note ngày từ lá số và transit, https://apps.apple.com/app/id1264782561
  - CHANI: transit cá nhân là tính năng trả phí, https://apps.apple.com/us/app/-/id1532791252
  - The Pattern: "Bonds" gắn nhãn kiểu Soulmate/Challenging; Lá Lành tránh nhãn phán xét này,
    https://apps.apple.com/us/app/-/id1071085727
- Labyrinthos, câu có/không trong Tarot: đổi thành câu quyết định, trải yếu tố ủng hộ/cản,
  https://labyrinthos.co/blogs/learn-tarot-with-labyrinthos-academy/how-to-answer-yes-no-questions-with-tarot-4-yes-or-no-tarot-spreads
- Gottman Love Maps (mẫu thẻ câu hỏi cho cặp): https://www.gottman.com/app/love-maps-app/
- NN/g, Personalization vs Customization: https://www.nngroup.com/videos/personalization-customization/
- Google PAIR, Feedback + Control: https://pair.withgoogle.com/chapter/People%20+%20AI%20Guidebook%20-%20Feedback%20+%20Control.pdf
- Kaminskas & Bridge, đa dạng, độ mới và độ phủ trong gợi ý:
  https://research.ucc.ie/en/publications/diversity-serendipity-novelty-and-coverage-a-survey-and-empirical/
- Tâm lý học:
  - Forer 1949 / hiệu ứng Barnum: https://www.ebsco.com/research-starters/psychology/barnum-effect
  - Padgett & Jorgenson 1982: https://opus4.kobv.de/opus4-Fromm/frontdoor/index/index/year/2024/docId/37972
  - Hofer 2009: https://dspace.library.uvic.ca/handle/1828/1553
  - Ryan & Deci 2000 (APA): https://apa.org/research-practice/conduct-research/self-determination-theory
  - Altendorf 2019: https://pure.uva.nl/ws/files/33032229/Published_article_Altendorf_et_al_2019_.pdf
  - Implementation intentions: https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2015.00395/pdf
  - Fredrickson & Kahneman 1993: https://bear.warrington.ufl.edu/brenner/mar7588/Papers/fredr-kahneman-jpsp1993.pdf
  - Baumeister 2001: https://fbaum.unc.edu/teaching/articles/Baumeister_2001.pdf
- Pháp lý, cần đối chiếu bản gốc trên Cổng Pháp luật quốc gia trước chặng 2:
  - Luật 91/2025/QH15 (hiệu lực 01/01/2026): https://thuvienphapluat.vn/van-ban/bo-may-hanh-chinh/Luat-Bao-ve-du-lieu-ca-nhan-2025-so-91-2025-QH15-625628.aspx
  - NĐ 356/2025/NĐ-CP: https://thuvienphapluat.vn/van-ban/Quyen-dan-su/Nghi-dinh-356-2025-ND-CP-huong-dan-Luat-Bao-ve-du-lieu-ca-nhan-687428.aspx
