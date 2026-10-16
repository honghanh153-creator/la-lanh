# Cá nhân hoá và đa dạng nội dung: Tarot (B2), Astro (B3), Hợp gu (B4)

Kế hoạch 16/10/2026. Người thực hiện: Claude. Người review: Codex. Owner yêu cầu: "mở rộng mức độ cá
nhân, đa dạng của cả tarot, astro, và phần hợp gu". Nguồn: Issue #6, audit 11/10
(`docs/research/2026-10-11-content-engine-audit.md`), review Tarot 08/10, code tại `main` 8362222
(số dòng bên dưới lấy từ commit đó).

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

**Đề xuất thứ tự:** P0 → P1 → B2 (đang có issue, phạm vi rõ) → B3-1 (lợi nhanh nhất: hết lặp 6/48 ngày,
hết một tình huống cả năm) → B4 → B3-2 → B3-3.

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

## 8. Owner cần quyết

1. **Tarot, mức hướng nghiêng:** chỉ 3 mức (thử / cân nhắc thêm / chưa rõ), không có "nghiêng về chưa
   nên"? Đề xuất: **3 mức**.
2. **Tarot, tên lá tiếng Anh:** bỏ khỏi copy, chỉ giữ trong chi tiết thu gọn? Đề xuất: **có**.
3. **Tarot, nối với note hôm nay** (opt-in): làm trong B2 hay để sau? Đề xuất: **để sau B3-1**.
4. **Astro, dùng mood và phản hồi để chỉnh note** (opt-in, mặc định tắt): đồng ý hướng này? Cần thêm
   copy consent mới.
5. **Astro, 5 tình huống mới:** owner chọn từ danh sách đề xuất ở P0.
6. **Thứ tự** như mục 6, hay ưu tiên mảng khác?

## 9. Không thuộc phạm vi

Bật Luna, lá ngược chiều, trải bài mới, đổi cách bốc lá, Lá Chung, thông báo đẩy, ghép đôi người lạ.
