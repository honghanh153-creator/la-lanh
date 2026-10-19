# Cá nhân hoá và đa dạng nội dung (bản triệt để): Tarot (B2), Astro (B3), Hợp gu (B4)

Kế hoạch 16/10/2026. Người thực hiện: Claude. Người review: Codex. Owner yêu cầu: "mở rộng mức độ cá
nhân, đa dạng của cả tarot, astro, và phần hợp gu". Nguồn: Issue #6, audit 11/10
(`docs/research/2026-10-11-content-engine-audit.md`), review Tarot 08/10, code tại `main` 8362222
(số dòng bên dưới lấy từ commit đó).

**Owner đã chốt (16/10/2026):** chọn đúng các đề xuất ở mục 8: chiến lược bậc thang S1 → S3 → S2,
Astro A2 (làm phần A1 sớm), Tarot T2, Hợp gu R2, thứ tự Tarot → Astro → Hợp gu, tín hiệu cá nhân để
chặng 2 và người dùng tự bật, checklist tâm lý vào chuẩn nội dung. Các phương án đã cân nhắc nằm ở mục
10, phần tâm lý người dùng ở mục 11, đối chiếu user flow ở mục 12. Bản phân tích trình bày cho owner (có
bảng chấm điểm) được giữ riêng; nội dung quyết định đã chép đầy đủ vào file này.

**Owner chốt bản triệt để (16/10/2026, sau review lần 2):** plan nền chỉ xoay một kho câu hữu hạn. Câu cũ
quay lại sau khoảng 6–8 ngày, và hai người khác nhau nhờ salt chứ chưa phải vì bài hiểu họ. Owner chọn
thêm **ba tầng nền tảng** (mục 14):

1. **Ngữ pháp nội dung:** câu ghép từ các ô đã duyệt, có allowlist dựng lúc build.
2. **AI lúc soạn:** sinh thêm biến thể ở bước biên tập, không gửi dữ liệu người dùng, không gọi lúc chạy.
3. **Tín hiệu để bài nói về chính người đọc:** lịch cá nhân từ lá số, mạch nhiều ngày, "điều bạn đang
   quan tâm" do người dùng tự chọn, và dùng lá số sâu hơn.

Các phần đã review (§2 seed và chu kỳ theo trục, đóng băng, T2, R2, chặng 2–3, riêng tư) giữ nguyên làm
nền. Mục 14 thay tầng nội dung bên dưới chúng.

## 0. Định nghĩa đo được

Hai chữ "cá nhân" và "đa dạng" được quy thành chỉ số. Mỗi chỉ số là một floor trong
`content-matrix-baseline.json` để không thể lùi lại.

| Chỉ số | Ý nghĩa | Đo bằng |
|---|---|---|
| **Cá nhân** | Hai người khác nhau hỏi/xem cùng lúc thì nhận nội dung khác nhau, và khác vì dữ liệu của chính họ | Tỷ lệ thẻ giống hệt nhau giữa các cặp profile cùng ngày; số tín hiệu thực sự đổi nội dung |
| **Đa dạng theo thời gian** | Một người dùng lâu không gặp lại cùng câu sớm | Số tình huống khác nhau trong 30/60 ngày; khoảng cách ngắn nhất giữa hai lần lặp của cảnh/hành động/tiêu đề |
| **Đa dạng trong một bài** | Các phần của một bản đọc không lặp ý nhau | Trùng ý giữa các mục (đã có cho Daily, mở rộng cho Tarot/Radar) |
| **Đúng và an toàn** | Đa dạng không được đổi nghĩa, dự đoán hay đoán ý người khác | Các gate hiện có + gate mới theo từng mảng |
| **Chân trời lặp câu** (bản triệt để) | Bao lâu một người gặp lại đúng một câu tiêu đề/cảnh/việc nhỏ | Số ngày ngắn nhất giữa hai lần cùng một câu, theo profile |
| **Yếu tố riêng mỗi bài** (bản triệt để) | Bài nhắc bao nhiêu điều chỉ của người này | Đếm: transit của mình, chương lịch cá nhân, mạch hôm trước, mối quan tâm đã chọn |
| **Phủ allowlist** (bản triệt để) | Câu chạy thật có được gate trước không | Tỷ lệ câu runtime nằm trong allowlist đã gate ở build (phải 100%) |

Đo trên dữ liệu tổng hợp: 50 profile (cả có giờ và chỉ ngày) × 60 ngày; ngân hàng câu hỏi Tarot
khoảng 290 câu; 50 cặp Radar. Không dùng dữ liệu người dùng thật.
Các chỉ số của bản triệt để dùng cửa sổ 200 ngày, chia nhóm và điều kiện khả thi ở §14.6.

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
  - Intent là so khớp chuỗi con theo thứ tự cho 5 intent. Ranh giới được xét trước giao tiếp
    (`engine.py:571-574`), nên câu có chữ "hỏi" mà không chạm từ khoá ranh giới sẽ rơi vào giao tiếp.
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
2. **Salt riêng từng người, tất định, không cần lưu thêm.**
   - **Seed ổn định, không chứa ngày:** `seed = HMAC(K[v], owner_scope ‖ surface ‖ catalog_version)`.
     `K[v]` là khoá server có phiên bản, chỉ dùng cho việc chọn biến thể, không phải khoá mã hoá dữ liệu.
   - **Ngày hoặc phiên chỉ chọn vị trí trong chu kỳ:**
     - Daily dùng số ngày lịch (theo múi giờ của note) tính từ một mốc cố định.
     - Tarot dùng thứ tự vai trong phiên và mã phiên. Biến thể Tarot được chọn **một lần lúc rút**,
       ghi vào payload phiên và không chọn lại.
   - Không tạo bảng lịch sử mới.
   - **Trùng giữa hai người là có thể,** vì kho hữu hạn. Không cam kết "mọi cặp người đều khác"; đo bằng
     tỷ lệ va chạm (mục 0).
3. **Chống lặp: cam kết cụ thể và cách bảo đảm.** Một hoán vị chung của cả bộ (tiêu đề × cảnh × hành
   động) **không** bảo đảm từng trục đổi mỗi ngày. Ví dụ hai bộ kề nhau `(0,0,0)` và `(1,0,0)` vẫn cùng
   cảnh và cùng hành động. Vì vậy thiết kế dùng **chu kỳ riêng cho từng trục**:
   - **Cách làm:**
     - Mỗi trục (tiêu đề 6, cảnh 8, hành động 8) có một hoán vị riêng, sinh từ `seed ‖ axis ‖ cycle_no`.
     - Vị trí trong ngày = `day_index mod n_axis`. `cycle_no = day_index div n_axis` nên mỗi chu kỳ được
       xáo lại.
     - **Ràng buộc biên:** phần tử đầu của chu kỳ mới phải khác phần tử cuối chu kỳ trước. Nếu trùng thì
       hoán đổi phần tử đầu với phần tử thứ hai, một phép tất định.
   - **Cam kết cứng, có AC:** trong cùng một tình huống, hai ngày lịch liên tiếp luôn khác nhau ở **mọi
     trục**, kể cả ở biên chu kỳ. Mỗi tiêu đề xuất hiện đúng một lần trong mỗi 6 ngày, mỗi cảnh và mỗi hành
     động đúng một lần trong mỗi 8 ngày của chu kỳ trục đó.
   - **Không cam kết bộ đầy đủ không lặp.** Chu kỳ theo trục được xáo lại, nên bộ đầy đủ (tiêu đề, cảnh,
     hành động) vẫn có thể trùng một ngày đã gặp.
     - **Mô phỏng sơ bộ** (50 seed tổng hợp, chạy bằng stdlib ngoài engine, trường hợp xấu nhất là tình
       huống đứng yên mỗi ngày): **6,7%** số ngày trùng bộ đã gặp trong 30 ngày trước, **13,6%** trong 60
       ngày. Không ngày nào trùng trục với ngày trước.
     - **So với hiện tại:** 0% trùng bộ trong 384 ngày, nhưng cảnh đứng yên 6 ngày và hành động 48 ngày.
     - **Đánh đổi có chủ đích:** ưu tiên mỗi trục đổi mỗi ngày.
     - P1 đo lại trên engine thật với top-K thật (K > 1 làm trùng bộ hiếm hơn) và đặt floor cho tỷ lệ trùng
       bộ trong 30/60 ngày.
     - Nếu owner muốn thấp hơn: thêm bước tránh trùng bộ (đổi hành động sang phần tử khác trong cùng chu
       kỳ) với điều kiện không phá cam kết cứng. AC kèm theo phải chứng minh cả hai điều kiện.
   - **Tình huống (top-K):**
     - Mỗi ngày xếp hạng pool đủ điều kiện của chính ngày đó, rồi chọn theo `day_index mod K` trên danh
       sách đã sắp xếp ổn định (thứ tự theo điểm, hoà thì theo mã tình huống).
     - Pool đổi theo transit thì tình huống có thể lặp. Guard: không quá 2 ngày liền cùng tình huống khi
       pool có ít nhất 2 phần tử.
     - Pool chỉ có 1 phần tử thì tình huống đứng yên, các trục vẫn xoay.
     - Chỉ số trục dùng `day_index` chứ không đếm số lần tình huống đã xuất hiện, nên không cần lưu lịch
       sử. Đánh đổi: một tình huống quay lại sau đúng 6 ngày có thể gặp lại cùng tiêu đề.
   - **Đóng băng và replay:**
     - Biến thể được chọn khi tạo bản đọc của ngày hoặc phiên, **trước khi** tính `plan_hash` và lưu
       revision.
     - Bản đã lưu ghi `variant_key_version` và `catalog_version`.
     - AC:
       - (a) Cache miss hoặc khởi động lại server cho ra đúng bản cũ.
       - (b) Đổi giọng chỉ đổi giọng của biến thể đã chọn (ánh xạ Cà khịa), không chọn lại.
       - (c) Thẻ đã chia sẻ hay lưu giữ nguyên snapshot.
       - (d) Đổi khoá (`K[v+1]`) chỉ áp cho ngày hoặc phiên mới; không render lại bản đã lưu.
     - Mọi thay đổi catalog cũng bump phiên bản.
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

- **Chặng 1 (S1 + bản triệt để; không gọi AI lúc chạy).** Thứ tự mảng giữ đúng quyết định 5: Tarot →
  Astro → Hợp gu. Hạ tầng ngữ pháp đi trước vì cả ba mảng cùng dùng.
  1. **P0** (docs, mở rộng): US-20, AC cho B3/B4, danh sách tình huống mới, danh sách "điều bạn đang
     quan tâm", nhà cung cấp cho AI lúc soạn, và các spec:
     - **Spec ngữ pháp:** khung, ô, tag; ô bắt buộc đổi và ô theo bucket; lịch chủ, vị trí thống nhất, tách
       từ vựng và phân vai giữa khung, trạng thái ngoại lệ; thuật toán lịch hợp lệ và giới hạn bước;
       giới hạn tổ hợp và tài nguyên CI; manifest; luật từ chối build (§14.2).
     - **Spec sự kiện G2:** miền longitude, orb dạng khoảng, pha chắc, ID lượt, cửa sổ chắc và cửa sổ có
       thể, ngày theo múi giờ của note, `event_spec_version` (§14.4).
     - **Spec đo:** cửa sổ 200 ngày, chuẩn hoá câu, nhóm, fixture, ngưỡng và cách đếm yếu tố riêng (§14.6).
     - **AC lặp giữa các màn** (§14.6b).
  2. **P1:** đo baseline, gồm các chỉ số mới ở mục 0.
  3. **B3-1a (A1):** salt + chu kỳ theo trục + top-K. Đây là nền chọn giá trị cho các ô ngữ pháp.
  4. **G0:** composer + allowlist dựng lúc build (hạ tầng chung). Chưa đổi nội dung hiển thị; kiểm trên
     một khung mẫu.
  5. **B2 (Tarot T2) trên ngữ pháp:** khung vai, lý do hướng nghiêng, liên từ tóm tắt. Đây là mảng thí
     điểm đầu tiên của ngữ pháp.
  6. **G1 (Astro trên ngữ pháp) + phần còn lại của A2:** thí điểm 2 tình huống, owner đọc 14 ngày mẫu,
     rồi mở rộng đủ 20 tình huống (gồm 5 mới). Pool cho người chỉ có ngày sinh, cân lại transit.
  7. **G2:** lịch cá nhân từ lá số và mạch nhiều ngày cho note ngày.
  8. **B4 (Hợp gu R2) trên ngữ pháp:** câu theo contact, câu về nhịp hai người.
  9. **E (AI lúc soạn):** chạy theo đợt cho từng mảng sau khi khung ổn định. Mỗi đợt owner duyệt chi phí
     trước khi gọi API trả phí.
  10. **F ("điều bạn đang quan tâm"):** chỉ sau khi rà luật (có thể làm sớm, trước chặng 2) và có copy
      consent, data map, khai báo store.
- **Chặng 2 (S3 nhẹ, người dùng tự bật):** chỉ sau khi rà Luật 91/2025 + NĐ 356/2025 từ nguồn chính thức
  và có copy consent mới.
  - B3-3 (A3): mood và phản hồi.
  - Gợi ý cách hỏi Tarot: phần đầu của T3, mở rộng câu gợi hỏi lại hiện có thành gợi ý theo chủ đề.
  - Thẻ câu hỏi Hợp gu: phần đầu của R3.
  - Nối Tarot với tình huống note hôm nay.
  - **Nhật ký Tarot (theo §8, mặc định tắt):**
    - Người dùng tự bật; chỉ ghi các bài người dùng chủ động lưu vào nhật ký, kèm ghi chú tự do nếu có.
    - **Dữ liệu và consent:** ghi chú tự do là dữ liệu cá nhân mới, có thể nhạy cảm. Nhật ký được đưa vào
      inventory dữ liệu, copy consent riêng, `store-privacy-data-map.md`, privacy copy trong app và khai
      báo Apple/Google.
    - **Lưu giữ và xoá:** mã hoá cùng cơ chế payload phiên, không log, thời hạn lưu do owner chốt ở AC
      (mặc định đề xuất theo hồ sơ, xoá khi tắt nhật ký hoặc xoá hồ sơ). Có xem, xuất và xoá từng mục hoặc
      toàn bộ.
    - **Không** tự đi vào Luna, xếp hạng hay phân tích mẫu. "Your Mirror" kiểu tìm mẫu lặp lại là một
      quyết định riêng, cần consent riêng nếu làm.
- **Chặng 3 (S2):** bật Luna cho note và Tarot; nhắc lại Hợp gu (cần cơ chế thông báo và consent riêng).
  Chỉ làm khi đủ điều kiện của Issue #7 (chấm mẫu, DPA, governance, khai báo).

**Khối lượng nội dung cần viết:**

| Mảng | Nội dung |
|---|---|
| Tarot | ≤ 468 nhãn lean; khung vai và ô theo ngữ pháp × 4 giọng; ô ví dụ đời thường |
| Astro | Khung và ô cho 20 tình huống (gồm 5 mới); ô theo lens, mối quan tâm và nhịp của chương; khung cho từng loại sự kiện lịch cá nhân |
| Hợp gu | Khung cảnh × ngữ cảnh; ô theo cặp hành tinh × họ góc chiếu; ô nhịp nguyên tố; khung 4 giọng |

Owner duyệt **giá trị ô** và **mẫu ghép** (khoảng 30 tổ hợp mỗi khung, chọn tất định và gồm cả tổ hợp
biên) qua Excel, không duyệt từng tổ hợp. Mọi tổ hợp chạy thật đều đã qua gate tự động ở build (mục
14.2).

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
- **Bản triệt để:**
  - **Allowlist:** mọi tổ hợp của ngữ pháp được liệt kê và chạy qua gate meaning, anti-influence,
    editorial, nudge checker và các mục kiểm máy được của checklist tâm lý **ở build/CI**. Runtime chỉ chọn
    trong allowlist theo `catalog_version`. Không gian quá lớn thì chia khung; không gate theo mẫu ở runtime.
  - **AI lúc soạn:**
    - Brief chỉ là nội dung biên tập (nghĩa, anchor, ví dụ đã duyệt), **không có dữ liệu người dùng**.
    - Output qua khử trùng, gate, review của agent và owner duyệt theo mẫu.
    - Catalog ghi provenance: model, phiên bản prompt, ngày, người duyệt.
    - Mỗi đợt gọi API trả phí cần owner duyệt trước, kèm ước tính chi phí.
    - Kiểm điều khoản nhà cung cấp về quyền dùng output làm nội dung.
  - **Lịch cá nhân và mạch:** tính tất định từ lá số và lịch thiên văn, không lưu lịch sử. Bản đã tạo vẫn
    đóng băng như §2.
  - **"Điều bạn đang quan tâm":**
    - Dữ liệu cá nhân mới do người dùng tự đặt; mặc định chưa chọn; đổi hoặc xoá trong Mình.
    - Tránh nhãn nhạy cảm (sức khoẻ, tình trạng hôn nhân cụ thể).
    - Chỉ dùng để chọn tag cảnh và đối tượng. Không gửi Luna, không suy luận thêm, không log.
    - Xoá cùng hồ sơ. Cập nhật data map, privacy copy, khai báo Apple/Google. Rà luật trước khi bật.

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
| 8 | Kiến trúc nội dung | **Bản triệt để** (mục 14): ngữ pháp nội dung + AI lúc soạn + tín hiệu cá nhân. Giữ các phần đã review làm nền. Thứ tự mảng theo quyết định 5 giữ nguyên; hạ tầng ngữ pháp (G0) đi trước |

**P0 (bản nháp đã viết, chờ review và owner chốt):**

- US-20 (Tarot), US-21 (note ngày), US-22 (Hợp gu)
- `docs/foundation/la-lanh-content-grammar-spec.md` (ngữ pháp, lịch chủ, build, manifest, ngoại lệ, G-AC1…9)
- `docs/foundation/la-lanh-personal-sky-events-spec.md` (G2)
- `docs/foundation/la-lanh-variety-measurement-spec.md` (đo và fixture)
- `docs/fixtures/tarot-question-bank-v1.json`
- `docs/plans/2026-10-16-p0-owner-decisions.md` (các điểm owner cần chốt)

Bước triển khai nào phụ thuộc mục chưa chốt thì chưa bắt đầu. Approval của kế hoạch này không phải
approval code hay release.

Còn chờ owner ở P0:

- chọn 5 tình huống Astro mới;
- chốt danh sách "điều bạn đang quan tâm";
- chọn nhà cung cấp cho AI lúc soạn;
- xác nhận các ngưỡng ở mục 14.6;
- duyệt giá trị ô và mẫu ghép của từng đợt (gồm Cà khịa) qua file Excel.

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
| Tarot | T1: sửa cấu trúc (vai, tóm tắt liền, dọn chữ thừa) | **T2**: T1 + hiểu câu hỏi, hướng nghiêng 3 mức, khung câu và ví dụ đa dạng | T3: T2 + gợi ý cách hỏi, đào sâu một lá, nhật ký opt-in (chặng 2) |
| Hợp gu | R1: cảnh × ngữ cảnh, giọng đổi cả câu | **R2**: R1 + câu theo góc chiếu giữa hai chart và cân bằng nguyên tố, ngữ cảnh đổi cả "hợp"/"ma sát" | R3: R2 + thẻ câu hỏi và góc nhìn hai phía (chặng 2); nhắc lại (chặng 3) |

| Kiến trúc nội dung | Ý chính | Kết quả với người dùng hằng ngày |
|---|---|---|
| Kho câu viết sẵn (plan nền) | 6/8/8 câu mỗi tình huống, xoay theo chu kỳ | Gặp lại đúng câu cũ sau khoảng 6–8 ngày |
| **Ngữ pháp + AI lúc soạn + tín hiệu (chọn)** | Câu ghép từ ô đã duyệt, ô được nhân lên bằng AI ở bước biên tập, chọn theo lá số, lịch, mạch và mối quan tâm | Mục tiêu: không gặp lại cùng câu trong ≥ 90 ngày; bài nhắc ≥ 3 yếu tố riêng |
| Luna viết lúc chạy (chặng 3) | Mô hình viết cho từng người | Câu tự nhiên nhất nhưng vướng riêng tư, chi phí, governance; không sửa được tín hiệu nghèo |

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

**Phạm vi bằng chứng:**

- **Padgett & Jorgenson (1982):** nghiên cứu lưu trữ, tìm thấy tương quan ở mức xã hội và lịch sử giữa
  chỉ số khó khăn kinh tế và số bài viết về chiêm tinh, mê tín ở Đức 1918–1940. Nghiên cứu không đo sự bất
  an của từng người.
- **Lillqvist & Lindeman (1998):** đọc qua tóm tắt thứ cấp, mẫu nhỏ. Các nguồn tóm tắt mô tả kết quả
  về khủng hoảng không thống nhất.
- **Hofer (2009):** luận văn định tính phỏng vấn bốn phụ nữ dùng Tarot thường xuyên. Không chứng minh
  cải thiện sức khoẻ hay chất lượng quyết định.
- **Không nguồn nào ở đây là bằng chứng hiệu quả cho Lá Lành.** Việc áp các nguồn này vào persona và tâm
  thế bên dưới là **giả thuyết sản phẩm**, cần kiểm bằng tín hiệu tổng hợp sau khi ra mắt.

Hướng chung rút ra, ở mức giả thuyết: nội dung nên trao lại cảm giác tự chủ, không nuôi sự phụ thuộc.

### Nguyên lý → quy tắc nội dung

| Nguyên lý | Bằng chứng | Quy tắc |
|---|---|---|
| Tự chủ, năng lực, gắn kết | Ryan & Deci (2000) | Đưa lựa chọn; việc nhỏ làm được trong ngày; Lá là bạn đồng hành, không phải thầy |
| Phản kháng khi bị ra lệnh | Altendorf và cộng sự (2019); kết quả lặp lại chưa đồng nhất | Không mệnh lệnh; Tarot chỉ "nghiêng về" |
| Kế hoạch "khi… thì…" | Gollwitzer & Sheeran (2006), d ≈ 0,65 trong phân tích gộp; không phải effect size cho app | Phần advice có tình huống kích hoạt |
| Đỉnh và kết | Fredrickson & Kahneman (1993); phân tích gộp 2022 (bối cảnh lý thuyết) | Đỉnh là câu "à ra vậy"; bài kết ở phần advice, không kết bằng cảnh báo |
| Hiệu ứng Barnum | Forer (1949) | Mỗi câu gắn với căn cứ riêng; không khen chung chung |
| Thiên lệch tiêu cực | Baumeister và cộng sự (2001) (bối cảnh lý thuyết) | Tối đa một ý tiêu cực mỗi bài, luôn kèm lối ra. Ngưỡng "một" là lựa chọn sản phẩm, không do nghiên cứu xác định |
| Bất định và kiểm soát | Padgett & Jorgenson (1982), tương quan mức xã hội; áp cho người dùng là giả thuyết | "Điều bạn quyết được hôm nay"; không định mệnh, không ép quay lại |
| Suy nghĩ lặp về đêm | Giả thuyết sản phẩm; app đã có nhắc nền tối sau 21:00 | Sau 21:00 chỉ đổi **cách trình bày** (thu gọn mục phụ mặc định), không đổi nội dung bản đọc (mục 11, "Quy tắc ban đêm") |

### Quy tắc ban đêm (không đổi nội dung đã đóng băng)

- **Phương án chọn:** chỉ rút gọn **cách trình bày** sau 21:00 theo giờ thiết bị, ví dụ thu gọn mặc định
  các mục phụ của Note Detail và câu dài của Lá. Nội dung bản đọc không đổi theo giờ mở. Bản đã tạo, lưu,
  chia sẻ hoặc đang trong phiên hiển thị cùng một nội dung bất kể mở lúc nào.
- **Không làm:** render lại hay chọn biến thể khác theo giờ mở. Nếu sau này muốn biến thể "ban đêm" thì
  phải chọn **lúc tạo** rồi đóng băng như mọi biến thể khác. Việc đó cần quyết riêng.
- **Ý tưởng Tarot "hỏi lại cùng câu trong 24 giờ thì mở lại bài cũ":** để P0 quyết, vì cần so câu hỏi.
  Nếu làm thì so bằng hash có khoá trên câu đã chuẩn hoá, nằm trong payload phiên đã mã hoá, không thêm
  bảng mới và không gửi ra ngoài.

### Persona kiểm thiết kế (tổng hợp, không phải người dùng thật)

- **Minh Anh, chỉ nhập ngày sinh, mở app 30 giây mỗi sáng:**
  - Hiện tại: một tình huống cả năm. Giả thuyết cần đo: người dùng nhóm này bỏ app sớm hơn.
  - A2 giải quyết bằng pool theo transit tới Mặt Trời và việc nhỏ có tình huống kích hoạt.
- **Huy, phân vân nhận việc, mở Tarot lúc 23:00:**
  - Hiện tại: tiêu đề cố định, không có hướng nghiêng.
  - T2 trả lời bằng "cân nhắc thêm trước khi nhận lời" kèm lý do. Việc mở lại bài cũ khi hỏi lại cùng câu là ý tưởng cần quyết ở P0 (xem quy tắc ban đêm).
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

## 14. Bản triệt để: ba tầng thay đổi nền tảng

### 14.1 Vì sao cần

Plan nền (§2–§5) chọn câu từ một kho viết sẵn nhỏ. Kể cả khi xoay vòng tốt, một tình huống ổn định vẫn
cho người dùng hằng ngày gặp lại đúng câu sau khoảng 6–8 ngày. Hai người khác nhau vì salt, chưa phải vì
bài nói về chính họ. Bản triệt để đổi **cách tạo câu** và **tín hiệu dùng để chọn câu**.

### 14.2 Tầng 1: Ngữ pháp nội dung

- **Khung và ô:** mỗi phần của bài là một khung gồm nhiều ô; mỗi ô có danh sách giá trị đã duyệt. Ví dụ
  việc nhỏ của tình huống `missing-context` có dạng `[tình huống kích hoạt] [động từ] [đối tượng]`:
  - tình huống kích hoạt: "Khi mở tin nhắn tiếp theo,", "Trước khi trả lời,", "Lúc đọc lại đoạn chat,", …
  - động từ: "hỏi lại", "hỏi thẳng", …
  - đối tượng: "một chữ chưa rõ", "đúng chỗ bạn đang đoán", …

  Cảnh có dạng `[người] [kênh] [khoảnh khắc] [dấu hiệu quan sát được]`. Tiêu đề là khung kèm danh từ của
  tình huống.
- **Metadata của mỗi giá trị:**
  - khoá nghĩa (phải khớp anchor của tình huống) và giọng (direct/roast);
  - tag theo lens, mối quan tâm và nhịp của chương;
  - độ dài;
  - ràng buộc đi cùng hoặc loại trừ (ví dụ kênh "tin nhắn" chỉ đi với giao tiếp);
  - đặc điểm ngữ pháp tiếng Việt (loại từ, trợ từ cuối câu).
- **Chọn trong allowlist bằng lịch hợp lệ dựng lúc build.** Chu kỳ độc lập của §2 vẫn dùng cho kho
  không có ràng buộc. Với tầng ngữ pháp, chạy chu kỳ từng ô rồi lọc **không** giữ được cam kết. Phản ví
  dụ: allowlist `{(0,0,0), (0,1,1), (1,0,1)}` không có hai tổ hợp nào khác nhau ở mọi ô. Vì vậy:
  - **Ô bắt buộc đổi và ô được lặp:** mỗi khung khai báo ô nào bắt buộc đổi giữa hai ngày liên tiếp (ví
    dụ tình huống kích hoạt, động từ, đối tượng của việc nhỏ) và ô nào được phép lặp (ví dụ danh từ của
    tình huống).
  - **Ô theo bucket:** mỗi tổ hợp tag/context đủ điều kiện (lens × mối quan tâm × nhịp chương) là một
    bucket. Bucket **chỉ** được điền các ô khai báo là "ô theo bucket" (ví dụ cụm danh từ cụ thể hợp với
    mối quan tâm). Các ô bắt buộc đổi **không phụ thuộc bucket**. Số bucket mỗi khung có giới hạn trong spec.
  - **Lịch chủ:** với mỗi khung, build dựng **một lịch chủ** trên tổ hợp của các ô bắt buộc đổi (không phụ
    thuộc bucket):
    - Lịch là một chu trình khép kín dài L, hai phần tử kề nhau (kể cả cuối → đầu) khác nhau ở mọi ô bắt
      buộc đổi.
    - Mỗi tổ hợp chủ chỉ xuất hiện một lần trong lịch. L ≥ 90 theo điều kiện khả thi ở §14.6.
    - Mọi bucket dùng **chung** lịch chủ và chỉ điền thêm ô theo bucket. Đổi bucket giữa hai ngày vì vậy
      không làm đổi lịch.
  - **Vị trí thống nhất:** vị trí của ngày là `p = (day_index + offset) mod L`.
    - Mọi khung trong một bài dùng cùng `p` và cùng L (khung có nhiều tổ hợp hơn chỉ dùng L tổ hợp mỗi
      biến thể lịch).
    - Seed của người dùng (§2) chọn một trong M biến thể lịch chủ đã chứng minh, cùng với `offset`.
    - Tarot dùng vị trí theo phiên, chọn một lần lúc rút.
    - **Không có bước chọn lại lúc chạy:** bỏ hẳn cơ chế "lùi tối đa 3 vị trí" của bản trước. Ngày sau
      luôn đi tới phần tử kế tiếp trên cùng lịch chủ, nên cam kết của lịch là cam kết của output thật.
  - **Quy tắc giữa các khung phải nằm trong cấu trúc, không tìm kiếm lúc chạy.** Cách đo stdlib cho thấy
    dựng lịch riêng từng khung rồi tìm độ lệch ghép **không** tìm được ghép hợp lệ khi quy tắc giữa khung
    dày. Vì vậy:
    - Quy tắc trùng ý giữa khung thành **tách từ vựng**. Ví dụ tiêu đề và cảnh không dùng động từ hành
      động của việc nhỏ, đúng với chuẩn "tiêu đề và cảnh không chứa lời khuyên". Build kiểm tách từ vựng
      giữa các khung của một bài.
    - Ngân sách ý tiêu cực thành **phân vai**: chỉ một khung được chứa giá trị mang ý tiêu cực (ví dụ ô "dễ
      bỏ qua"), nên cả bài không thể vượt ngưỡng.
    - Quy tắc nào không đưa được vào cấu trúc thì build dựng lịch ghép chung cho các khung đó và kiểm đủ
      L ngày. Không dựng được thì build thất bại.
  - **Cam kết trên output thật được phục vụ** (thay cho "mỗi giá trị đúng một lần mỗi chu kỳ" của §2):
    - **(a)** Hai lần phục vụ liên tiếp của cùng khung, cả hai **không** ở trạng thái ngoại lệ, khác nhau ở
      mọi ô bắt buộc đổi. Áp cả khi đổi bucket và ở biên lịch.
    - **(b)** Cùng một câu ghép không được phục vụ lại trong L ngày, vì tổ hợp chủ là duy nhất trong mỗi L
      ngày.
    - **(c)** Mỗi giá trị của ô bắt buộc đổi xuất hiện ít nhất một lần trong mỗi lịch chủ.
    - Ô theo bucket **được phép trùng** khi đổi bucket, và không tính vào (a). Khoảng cách giữa hai lần dùng
      cùng một giá trị ô không được bảo đảm, trừ khi khung khai báo thêm ràng buộc và build chứng minh được.
  - **Trạng thái ngoại lệ** (đo được, không báo như vẫn có bảo đảm):
    - Gate toàn bài lúc chạy chỉ còn là lưới an toàn; theo cấu trúc trên nó không được phép từ chối. Nếu
      vẫn từ chối, hoặc manifest hỏng, thì ngày đó phục vụ kho nền (plan nền §2).
    - Provenance của bản đọc ghi `variety_exception` (lý do và phiên bản, không có dữ liệu cá nhân). Có
      counter tổng hợp theo khung và phiên bản.
    - Ngày sau quay lại vị trí danh nghĩa `p`, không dịch vị trí.
    - Cặp ngày có ngoại lệ bị loại khỏi (a) và (b) và **báo riêng** số lượt cùng tỷ lệ ngoại lệ. Mục tiêu
      trong đo tổng hợp: 0 ngoại lệ do gate.
  - **Phép thử sơ bộ** (stdlib, dữ liệu tổng hợp, không chạy sản phẩm):
    - Phản ví dụ ở trên không dựng được lịch nên build từ chối.
    - Một khung 6 × 5 × 8 bỏ khoảng 15% tổ hợp (198 tổ hợp) dựng được lịch khép vòng 189.
    - **Phản ví dụ của Codex** (gate từ chối ngày D, lùi sang vị trí 1, ngày D+1 lặp lại) tái hiện được với
      cơ chế lùi, nên cơ chế lùi đã bị bỏ.
    - Cách "lịch riêng từng khung + tìm độ lệch ghép" và "bucket dựng lịch riêng" đều thất bại trong mô
      phỏng: không tìm được ghép, và có 7 vi phạm (a) khi đổi bucket.
    - **Lịch chủ** (6 × 5 × 4, L = 90), bucket đổi ngẫu nhiên mỗi ngày, 400 ngày, 3 ngày ép lỗi lúc chạy:
      output phục vụ có **0** vi phạm (a), **0** câu lặp trong L ngày; 3 ngày ngoại lệ đều được đánh dấu.
    - Đây là bằng chứng hướng thiết kế, không phải chứng nhận triển khai.
  - **Không khả thi thì build thất bại (CI đỏ).** Ngoại lệ duy nhất là khung khai báo rõ một ngoại lệ đã
    review (ví dụ hạ một ô từ "bắt buộc đổi" thành "được lặp"), ghi trong manifest. Không chọn ngẫu nhiên,
    không thử lại vô hạn, không âm thầm phá cam kết lúc chạy.
- **Allowlist và manifest:**
  - CI liệt kê **mọi** tổ hợp của từng khung, chạy gate meaning, anti-influence, editorial, nudge checker và
    các mục kiểm máy được của checklist tâm lý, rồi khử trùng câu sau chuẩn hoá.
  - Giới hạn số tổ hợp mỗi khung và tài nguyên CI ghi trong spec P0; vượt giới hạn thì build thất bại, phải
    tách khung.
  - Manifest gắn `catalog_version`, `composer_version`, `gate_version` và hash của allowlist cùng các lịch.
  - Runtime chỉ phục vụ khung có manifest hợp lệ. Manifest hỏng hoặc thiếu thì dùng kho nền (plan nền §2),
    không ghép tự do.
  - "100% trong allowlist" chỉ chứng minh độ phủ của kiểm tra máy, **không** chứng minh câu tự nhiên hay
    đúng nghĩa. Owner vẫn đọc mẫu.
- **Gate toàn bài:** chạy `evaluate_candidate` như lưới an toàn trên bài đã ghép. Không có bước chọn lại;
  nếu gate từ chối thì vào trạng thái ngoại lệ ở trên. Mọi lựa chọn xong **trước** khi tính `plan_hash` và
  lưu (§2).
- **AC cho các đường chọn** (P0 viết, G0/G1 kiểm). Mọi chỉ số §14.6 tính trên **output cuối cùng được phục
  vụ**, không tính trên lịch build:
  1. Ngày D: ép gate toàn bài từ chối (như phản ví dụ). Kỳ vọng: D là ngoại lệ (kho nền, có cờ); D+1 ở vị
     trí danh nghĩa; không có câu nào phục vụ hai lần trong L ngày.
  2. Đổi bucket giữa hai ngày ở mọi vị trí `p` của lịch, với mọi cặp bucket có thể kề nhau trong fixture.
     Kỳ vọng: (a) và (b) giữ.
  3. Biên lịch: ngày ở vị trí L−1 rồi 0.
  4. Build có cấu hình vi phạm tách từ vựng hoặc ngân sách tiêu cực: CI phải đỏ.
  5. Manifest hỏng hoặc thiếu: phục vụ kho nền, có cờ ngoại lệ và counter.
  6. Đổi giọng, replay sau cache miss hoặc restart, chia sẻ: cùng mã tổ hợp, không chạy lại lịch.
  7. Báo cáo gồm số lượt và tỷ lệ ngoại lệ, tỷ lệ vi phạm (a)/(b) trên output thật, theo nhóm của §14.6.
- **Đổi giọng:** mỗi tổ hợp direct có ánh xạ Cà khịa theo mã tổ hợp, và bản Cà khịa cũng phải nằm trong
  allowlist. Build kiểm đủ ánh xạ, thiếu thì thất bại. Đổi giọng chỉ tra ánh xạ, không chạy lại lịch.
- **Cà khịa:** giá trị ô có bản Cà khịa riêng; ghép Cà khịa là khung riêng, ít ô hơn. Quy tắc "không nửa
  thẻ" giữ nguyên.
- **Duyệt:** owner duyệt giá trị ô và mẫu ghép, không duyệt từng tổ hợp (§6).
- **Quy mô mục tiêu,** đo thật ở G1: mỗi tình huống khoảng 240 việc nhỏ hợp lệ, 120 cảnh, và **≥ 90
  tổ hợp tiêu đề** (con số 30 trước đây không đủ cho mục tiêu 90 ngày khi pool chỉ có một tình huống, xem
  §14.6).
- **Rủi ro câu ghép kém tự nhiên:** giữ khung ngắn, ít ô; gate độ dài; owner đọc 14 ngày mẫu trước khi mở
  rộng.

### 14.3 Tầng 2: AI lúc soạn

- **Quy trình:**
  1. Brief biên tập của khung: nghĩa, anchor, contrary, giọng, giá trị đã duyệt.
  2. Mô hình sinh giá trị ô ứng viên.
  3. Khử trùng (trùng chữ, gần nghĩa).
  4. Gate tự động.
  5. Review của agent.
  6. Owner duyệt theo mẫu.
  7. Vào catalog, có provenance.
- **Không dữ liệu người dùng, không gọi lúc chạy.** Chi phí là một lần cho mỗi đợt; mỗi đợt owner duyệt
  trước.
- Duyệt và lưu qua Content Studio (`apps/api/app/domains/content/`) nếu phù hợp; nếu không thì dùng
  catalog trong repo cộng file Excel.
- Mục tiêu: 5–10 lần số giá trị mỗi ô so với bản viết tay.

### 14.4 Tầng 3: Tín hiệu để bài nói về chính người đọc

- **Lịch cá nhân từ lá số** (tất định, không dữ liệu mới):
  - Các sự kiện: sinh nhật (Mặt Trời trở về), Sao Mộc và Sao Thổ trở về, transit chậm vào orb với hành tinh
    cá nhân, Sao Thuỷ nghịch hành chạm Sao Thuỷ natal, …
  - Mỗi sự kiện là một **chương**, có tình huống và khung riêng.
  - Người chỉ có ngày sinh dùng các sự kiện tính được từ Mặt Trời và ngày sinh.
- **Mạch nhiều ngày:**
  - Engine đã có `TransitPhase` (đang tới gần / chính xác / tách dần).
  - Một chương N ngày chia ba nhịp **nhận ra → thử → nhìn lại**. Ô "nhịp" chọn theo ngày thứ mấy của
    chương, ví dụ "Ngày 2 của đợt Sao Hoả chạm Mặt Trời của bạn".
  - Tính lại được từ lịch thiên văn, không cần lưu lịch sử.
  - Nhiều chương trùng nhau thì ưu tiên theo độ chặt orb và mức cá nhân; tối đa một chương nổi trên Home.
- **"Điều bạn đang quan tâm":**
  - Người dùng tự chọn một mục từ danh sách khoảng 8. Đề xuất: học tập, công việc mới, tình cảm, gia đình,
    bạn bè, chăm mình, tiền bạc, một thay đổi lớn. Owner chốt ở P0.
  - Đổi cảnh và đối tượng của bài. Ràng buộc riêng tư ở §7.
- **Lá số sâu hơn:** thêm luật về cặp, nhà, góc chiếu và orb vào chấm điểm tình huống và "Vì sao hôm nay?".
  Giữ evidence binding.
- **Người chỉ có ngày sinh: dùng gần đủ lá số, nhưng mang theo miền bất định tới tận câu chữ.**
  - Hiện `calculate_date_only_sun` (`astro/engine.py:583-606`) chỉ trả tập cung của Mặt Trời từ các mẫu
    cách 6 giờ trên khoảng ngày dân sự (UTC+14 tới UTC−12, khoảng 50 giờ). Nó không trả miền longitude, orb
    hay pha.
  - **Cùng cung chưa đủ.** Probe của Codex (dữ liệu tổng hợp 1990-03-15) cho Sao Thuỷ 349,16° và 353,14°
    ở hai đầu khoảng sinh, vẫn cùng cung Song Ngư. Transit lúc 2026-02-21 12:00 UTC cho orb 1,56° và 2,42°,
    cả hai trong ngưỡng, nhưng `_transit_phase` trả **separating** cho một đầu và **approaching** cho đầu
    kia. Chọn một longitude đại diện sẽ nói sai pha với một giờ sinh vẫn hợp lệ.
  - **Contract mới (spec ở P0, làm ở G2):**
    1. **Miền longitude:** với mỗi hành tinh trừ Mặt Trăng, tính khoảng `[λmin, λmax]` trên toàn khoảng sinh.
       Gồm hai đầu khoảng, mọi điểm đứng (tốc độ đổi dấu) bên trong, và xử lý vòng 0°/360°. Dung sai và cách
       phát hiện điểm đổi cung/điểm cực trị phải nêu rõ, không phụ thuộc mẫu cách 6 giờ.
    2. **Orb:** orb của transit với natal là một khoảng. **Chắc chắn trong orb** khi orb lớn nhất ≤ ngưỡng.
       **Có thể** khi chỉ orb nhỏ nhất ≤ ngưỡng.
    3. **Pha:** chỉ phát biểu khi pha giống nhau trên toàn miền (cả hai đầu và các điểm cực trị bên trong).
       Không thì không nói pha.
    4. **Chương** = một lượt đi qua (pass) có ID ổn định: (hành tinh transit, điểm natal, góc chiếu, thứ tự
       lượt theo thời gian). Có nhiều lượt khi nghịch hành.
       - **Cửa sổ chắc:** trong orb với mọi điểm của miền.
       - **Cửa sổ có thể:** trong orb với ít nhất một điểm.
       - Biên tìm bằng tìm nghiệm trên ephemeris, có dung sai.
       - Ngày tính theo ngày dân sự ở múi giờ của note. Spec có phiên bản `event_spec_version`.
    5. **Chữ hiển thị:**
       - "Ngày N của đợt…" chỉ dùng khi đang trong cửa sổ chắc, và N đếm từ biên chắc.
       - Đang ở cửa sổ có thể thì nói "đợt này" không kèm số ngày, hoặc bỏ chi tiết.
       - Không bịa "Ngày 2".
  - **Vẫn không dùng** Mặt Trăng, cung mọc, nhà và các kết luận phụ thuộc giờ. Bài ghi rõ là bản đọc từ
    ngày sinh.
  - **Test bắt buộc:** cùng cung nhưng khác orb/pha (như ví dụ trên); ngày đổi cung; vòng 0°/360°; điểm
    đứng nằm trong khoảng sinh; nhiều lượt do nghịch hành.
- **`TransitPhase` hiện tại** là phân loại tại một thời điểm (exact khi orb ≤ 0,2°, so với vị trí sau một
  giờ, `engine.py:609-619`). Nó không có khoảng sự kiện hay số ngày của chương, nên G2 phải thêm phần tìm
  biên và lượt cho cả người có giờ sinh. Tính lại được từ ephemeris, không lưu lịch sử, vẫn đóng băng trước
  `plan_hash` như §2.
- **Nhịp "nhìn lại"** chỉ mời người đọc tự soi. Không khẳng định họ đã đọc hay đã làm gì hôm trước.
- Hình học thiên văn là căn cứ để chọn nội dung, **không** phải bằng chứng rằng hành tinh gây ra trải nghiệm
  của người dùng.

### 14.5 Áp cho Tarot và Hợp gu

- **Tarot:**
  - Khung vai, lý do hướng nghiêng và liên từ tóm tắt viết bằng ngữ pháp; ô liên hệ theo dạng câu hỏi.
  - Mối quan tâm (nếu đã chọn) chỉ chọn ví dụ đời thường phù hợp. Không trích câu hỏi.
  - Biến thể chọn một lần lúc rút rồi đóng băng.
- **Hợp gu:**
  - Câu theo contact được ghép từ cặp hành tinh × họ góc chiếu × ngữ cảnh × giọng.
  - Câu về nhịp hai người lấy từ cân bằng nguyên tố và tính chất của hai chart.
  - Không lưu thêm dữ liệu của người kia.

### 14.6 Tiêu chí "triệt để" và cách đo

Đề xuất; owner chốt ngưỡng ở P0. Đo trên dữ liệu tổng hợp ở P1/G1, rồi đặt thành floor.

**Thiết kế phép đo:**

- **Cửa sổ quan sát:** **200 ngày** mỗi profile, dài hơn ngưỡng 90 ngày. Không dùng cửa sổ 60 ngày của
  plan nền cho chỉ số này.
  - 200 ngày **không** luôn đi qua biên lịch hai lần. Ví dụ lịch 180 ngày, offset 0 chỉ wrap một lần ở
    ngày 180.
  - Vì vậy mọi cạnh biên (L−1 → 0) được kiểm ở build trên từng lịch.
  - Fixture đo trải `offset` sao cho mỗi profile có ít nhất một lần wrap trong cửa sổ, và tổng thể phủ mọi
    vị trí wrap.
- **So câu:** so sau chuẩn hoá (NFC, chữ thường, bỏ khoảng trắng thừa và dấu câu cuối). Đo riêng từng phần
  (tiêu đề, cảnh, việc nhỏ, lời của Lá) và riêng từng giọng.
- **Chỉ số chính:** với mỗi profile và mỗi phần, lấy khoảng cách ngắn nhất (theo ngày) giữa hai lần xuất
  hiện của cùng một câu. Profile **đạt** khi khoảng cách này ≥ 90 ngày hoặc không lặp trong 200 ngày.
- **Mẫu số 95%:** tính riêng trong từng **nhóm**, không gộp:

  | Trục chia nhóm | Giá trị |
  |---|---|
  | Giờ sinh | biết / không biết |
  | Mối quan tâm | đã chọn / chưa chọn |
  | Pool tình huống | 1 / 2–3 / ≥ 4 |
  | Chương | có chương chắc / không |

  Mỗi nhóm ≥ 50 profile tổng hợp; fixture phải có pool một phần tử, tag hẹp và không có chương nào chắc.
- **Điều kiện khả thi** (build kiểm, không để tới lúc đo mới biết): với pool một phần tử, một phần có L
  câu khả dụng thì khoảng cách tối đa là L ngày.
  - Mỗi khung phải có **lịch chủ dài ≥ 90**, tức ≥ 90 tổ hợp chủ khác nhau. Câu ghép khác nhau sau
    chuẩn hoá được build kiểm khi khử trùng; ô theo bucket không được dùng để đủ số.
  - Riêng tiêu đề, G1 phải thiết kế khung đủ ô cho ≥ 90 tổ hợp mỗi tình huống, thay cho con số 30 ở §14.2.
  - Bucket nào không đạt thì đánh dấu **"mục tiêu có điều kiện"**, và báo tỷ lệ không đạt riêng. Không làm
    loãng căn cứ (evidence) để đạt đa dạng.
- **Yếu tố riêng: đếm theo nguồn tín hiệu độc lập và chắc, mỗi nguồn tối đa một lần:**

  | Nguồn | Tính khi |
  |---|---|
  | Transit cá nhân | Một transit **chắc trong orb** tới điểm natal của chính người đó. Chương và nhịp của **cùng** transit này không tính thêm |
  | Sự kiện lịch cá nhân khác | Một sự kiện thiên văn **khác** với transit trên, ví dụ sinh nhật hay chu kỳ trở về |
  | Cấu hình natal riêng | Luật cặp hoặc nhà dùng trong bài |
  | Mối quan tâm đã chọn | Thực sự được dùng để chọn nội dung trong bài |

  Salt **không** bao giờ được tính.
- **Ngưỡng yếu tố riêng theo nhóm:**
  - Đề xuất: có giờ sinh + đã chọn mối quan tâm ≥ 3; có giờ sinh, chưa chọn ≥ 2; chỉ ngày sinh + đã chọn
    ≥ 2; chỉ ngày sinh, chưa chọn ≥ 1.
  - Plan trước ghi "≥ 2 cho người chỉ có ngày sinh" ở bảng dưới và đề xuất ngang bằng "≥ 3" ở §14.6b. Owner
    chốt một ngưỡng ở P0. Nhóm ít dữ kiện chắc được phép ít yếu tố hơn và bài nói thật, **không dựng thêm
    để đủ số**.
- **Ablation:** giữ nguyên salt, đổi từng tín hiệu (giờ sinh, mối quan tâm, ngày), đo tỷ lệ nội dung đổi.
  Phép này tách phần cá nhân hoá có ý nghĩa khỏi phần khác chữ do ngẫu nhiên.

| Chỉ số | Plan nền | Bản triệt để (đề xuất) |
|---|---|---|
| Khoảng cách lặp cùng một câu, theo phần, cùng người | khoảng 6–8 ngày | ≥ 90 ngày với ≥ 95% profile **trong mỗi nhóm khả thi**; nhóm có điều kiện báo riêng |
| Hai người cùng cung, cùng ngày, note giống hệt | khác do may rủi | < 1% (trừ cặp cùng ngày sinh và cùng thiếu giờ, báo riêng) |
| Yếu tố riêng mỗi note | 1–2 | theo ngưỡng nhóm ở trên |
| Ngày trong cửa sổ chắc của một chương có nhắc mạch | 0 | đo ở G2, floor đặt sau |
| Câu runtime nằm trong allowlist đã gate | không áp dụng | 100% (độ phủ kiểm máy, không phải độ tự nhiên) |

### 14.6b Yêu cầu nâng cao đề xuất (owner hỏi 16/10, xác nhận ở P0)

| Nhóm | Yêu cầu | Ghi chú |
|---|---|---|
| **Người không rõ giờ sinh** | Cùng mục tiêu khoảng cách lặp ≥ 90 ngày như người có giờ (khả thi nhờ điều kiện lịch ở §14.6). Yếu tố riêng theo ngưỡng nhóm | Ngang bằng về **lặp** thì làm được. Ngang bằng về **số yếu tố** thì không bảo đảm trung thực khi chưa chọn mối quan tâm |
| **Lỗi nội dung** | 0 câu runtime ngoài allowlist; 0 cụm bị cấm trên toàn không gian ghép; mỗi lỗi được báo thì thêm test hồi quy **và** quét lại toàn bộ allowlist | Không chỉ sửa một câu |
| **Lặp giữa các màn** (cần AC ở P0 trước khi coi là bảo đảm) | Phạm vi đề xuất: ngày dân sự theo múi giờ của note; lời của Lá + note ngày + mọi phiên Tarot và kết quả Hợp gu tạo trong ngày đó. So theo **mã hành động** (mức nghĩa) và câu sau chuẩn hoá | Cơ chế tất định: mỗi màn lấy hành động từ một **namespace riêng** (Daily, Tarot, Hợp gu), nên không cần lịch sử và không phụ thuộc thứ tự mở màn. Đổi giọng không tính là mới. Snapshot đã đóng băng của ngày trước không xét và không bị sửa. Đây là đề xuất, chưa phải bảo đảm đã đo |
| **Lặp trong một bài** | Giữ quy tắc trùng ý của Daily; mở rộng cho Tarot (giữa các vai) và Hợp gu (giữa các mục) | Kiểm bằng gate toàn bài (§14.2) |
| **Trung thực** | Không bịa dữ liệu để đạt đa dạng: không đoán giờ sinh, không dùng Mặt Trăng hay cung mọc khi thiếu giờ, không nói pha hoặc ngày của chương khi miền bất định chưa cho phép (§14.4) | Đa dạng phải đến từ dữ liệu thật |

**Giới hạn phải ghi rõ:** hai người **cùng ngày sinh và cùng không rõ giờ** có lá số gần như giống hệt. Với
họ, khác biệt chỉ đến từ mối quan tâm đã chọn, salt và ngày mở app. Không được tuyên bố là "vì lá số
khác".

### 14.7 Đánh đổi

- Khối lượng lớn hơn rõ (composer, allowlist, khung, duyệt mẫu), nên chặng 1 dài hơn plan nền.
- Câu ghép có thể kém tự nhiên. Đối phó bằng khung ngắn, đọc 14 ngày mẫu, gate.
- Ưu tiên giữa các chương phức tạp, cần audit riêng.
- "Điều bạn đang quan tâm" là dữ liệu mới, phải rà luật trước khi bật.
- AI lúc soạn tốn chi phí một lần cho mỗi đợt và cần owner duyệt; chất lượng phụ thuộc khâu duyệt mẫu.
