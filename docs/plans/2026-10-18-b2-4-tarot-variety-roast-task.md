# Task B2-4a — Tarot T2: biến thể theo phiên, câu riêng cho từng câu hỏi, Cà khịa, phiên bản

> Nguồn đã duyệt:
> - `docs/plans/2026-10-16-personalisation-variety-plan.md` §3 (đa dạng, giọng, phiên bản) và §6 bước 5;
> - `docs/user-stories/US-20-tarot-tra-loi-dung-cau-hoi.md` AC15, AC16, AC17, AC18, AC19, AC20;
> - `docs/foundation/la-lanh-variety-measurement-spec.md` §4c (T2, T3, T4).
>
> Stacked trên B2-3 (PR #25, APPROVE @ `b420e464be1e70da2e8f489186b7fefbaaec677d`).

## AC còn thiếu sau B2-3

| AC | Còn thiếu | Làm ở |
|---|---|---|
| AC06 | Schema payload Luna có mã nguồn gốc cho mọi chuỗi; test duyệt mọi trường lồng nhau; canary "chị Lan ở phòng 302" theo từng cụm ≥ 2 từ | **B2-4b** |
| AC14 | Checklist tâm lý cho cả bài và từng phần; owner đọc mẫu | **B2-4b** (cần owner) |
| AC15 | Biến thể chọn một lần lúc rút theo seed `HMAC(K[v], owner_scope ‖ "tarot" ‖ catalog_version)` và vị trí theo phiên, ghi vào payload | **B2-4a** (khung vai, tiêu đề, câu dẫn). Trục ví dụ đời thường đã có chỗ trong bản ghi nhưng mới có 1 cảnh mỗi lá × chủ đề |
| AC16 | Hai câu hỏi khác nhau, cùng lá, cùng vai ra câu khác nhau ≥ 80% cặp (T4, đo ở audit). P1 đo được 0% | **B2-4a** |
| AC17 | Phần còn lại: phiên có frame nhưng chưa có biến thể; bản v7 đọc lại được | **B2-4a** |
| AC18 | Renderer v7, gates v5 thành hằng số, knowledge v5, meaning brief v3; sửa default cũ và tài liệu cũ | **B2-4a** (renderer, gates, knowledge, default). Brief v3 đi cùng AC06 ở **B2-4b** |
| AC19 | Cà khịa cho tiêu đề, hướng nghiêng, liên từ, khung vai; ánh xạ theo mã tổ hợp; câu nhạy cảm vẫn ép khỏi Cà khịa; owner duyệt qua Excel | **B2-4a** |
| AC20 | Audit toàn ngân hàng × mọi map × **4 giọng** (B2-3 mới chạy 3 giọng thẳng) | **B2-4a** |

B2-4b (PR sau) gồm AC06, brief v3 và AC14. Luna vẫn tắt ở cả hai PR. Ví dụ đời thường 2–3 cảnh mỗi lá × chủ đề
(khoảng 470–940 cảnh mới) là việc nội dung, làm theo đợt biên tập riêng hoặc chặng E khi owner duyệt chi phí.
B2-4a chỉ dựng trục chọn cảnh, nên khi có cảnh mới chỉ cần thêm dữ liệu.

## Phạm vi B2-4a

### 1. Biến thể theo phiên (AC15)

- Module mới `tarot/variants.py`. Khi **bắt đầu phiên** (cùng lúc xáo bộ bài), service chọn:
  - `lead`: vị trí bắt đầu trong 5 câu dẫn của dạng câu hỏi;
  - `headline`: 1 trong 3 khung tiêu đề;
  - `frames[position_key]`: 1 trong 3 khung câu cho từng vai của map đã chọn;
  - `scenes[position_key]`: chỉ số cảnh (hiện luôn là 0 vì mỗi lá × chủ đề mới có 1 cảnh).
- Seed: `HMAC(K[1], guest_id ‖ "tarot" ‖ TAROT_VARIANT_CATALOG_VERSION)`. `K[v]` là khoá chọn biến thể đã có
  từ B3-1a (`derive_variety_key`, dẫn xuất từ `guest_hash_key`, chỉ dùng để chọn, không mã hoá gì).
- Vị trí: cursor tăng bền vững theo guest (bảng `tarot_variant_cursors`, sửa theo review Codex P2-1). Cursor
  được cấp bằng một upsert nguyên tử trong **cùng transaction tạo phiên**: xoá bài đọc hay cleanup không làm lùi
  cursor; replay idempotency không cấp vị trí; nếu tạo phiên thất bại thì cấp phát rollback theo. Cursor bị xoá
  cùng guest (FK cascade). Giá trị trục lấy bằng `axis_slot` của B3-1a, nên **hai phiên liên tiếp luôn khác
  nhau** ở mọi trục có ≥ 2 giá trị.
- Ghi vào payload AES-GCM của phiên: `{"version", "key_version", "lead", "headline", "frames", "scenes"}`.
  Chỉ lưu chỉ số đã chọn, không lưu seed. Render chỉ đọc bản ghi này, không tính lại, nên đổi khoá, đổi
  catalog hay restart đều không làm đổi bản đã rút.
- Bản đọc vẫn render một lần ở lá cuối và được lưu. Tarot không có đường đổi giọng sau khi bắt đầu (giọng chốt
  lúc tạo phiên), nên "đổi giọng" trong AC15 không có đường chạy; ghi nhận ở đây.
- Chỉ khi **thiếu hẳn key** `variants` (phiên có frame bắt đầu trước B2-4, chỉ có ở dev) mới dùng chỉ số 0. Bản
  ghi hiện diện phải giải mã chặt (sửa theo review Codex P2-2): đủ sáu trường, đúng version, số nguyên strict
  (không bool, chuỗi số hay float), không trường lạ; `null`, `{}` hay thiếu trường đều báo lỗi thay vì tự bịa
  chỉ số. Bản ghi DEFAULT đầy đủ (frames/scenes rỗng) vẫn replay được.
- Service không có khoá (test cũ, môi trường không cấu hình): mọi chỉ số = 0 (vẫn ghi bản ghi đầy đủ).
- Hai lần tạo phiên đồng thời được upsert xếp hàng trên cùng dòng cursor, nên mỗi phiên có vị trí riêng.

### 2. Câu riêng cho từng câu hỏi (AC16)

- **Câu dẫn theo dạng câu hỏi** (`roles.LEADS`): 5 câu dẫn ngắn (≤ 4 chữ) cho mỗi dạng `yes_no`, `choice`,
  `how`, `why`, `timing`, `open`. Vị trí thứ i dùng câu dẫn `(lead + i) mod 5`, nên trong một bài không câu dẫn
  nào lặp. Câu dẫn lấy từ nhãn đóng `form`, không chứa chữ nào từ câu hỏi.
- **3 khung câu cho mỗi vai** (`roles.FRAMES`): khung 0 là câu B2-2 đã có; thêm 2 khung mới cho mỗi vai.
- **Vai bước tiếp gắn với hành động**: khi câu hỏi có nhãn hành động (`yes_no`, `timing`, `how`), vai bước
  tiếp đọc "trước khi {action}" bằng cụm từ đã duyệt `ACTION_PHRASES`.
- Ước lượng trên ngân hàng: cặp câu hỏi cùng chủ đề trùng dạng 15%, trùng cả dạng và hành động 4,2%. Riêng
  phần do câu hỏi quyết định đã cho khoảng 85%; cộng biến thể theo phiên thì cao hơn.
- `tarot:audit` đo T4 theo đúng spec §4c (mọi cặp câu hỏi khác nhau trong cùng chủ đề × mọi map × vai × 78
  lá), báo ba con số:
  - **T4 theo phiên** (mỗi câu hỏi là một phiên của một guest tổng hợp khác nhau): gate ≥ 80%;
  - **T4 chỉ theo câu hỏi** (mọi chỉ số biến thể = 0): gate ≥ 80%, để chứng minh câu đổi vì câu hỏi chứ
    không chỉ vì salt;
  - **T4 cùng guest, phiên liên tiếp** (thông tin thêm).
- Câu được dựng bằng đúng hàm engine dùng; test đối chiếu với render đầy đủ.

### 3. Cà khịa (AC19)

Bản Cà khịa ánh xạ **theo mã tổ hợp**: mỗi khung thẳng có mã (`clear.0`, `headline.lean_try.1`,
`conjunction.tension.0`, …) và bản Cà khịa mang đúng mã đó.

- Khung vai: 20 vai × 3 khung.
- Tiêu đề động: 8 khoá × 3 khung. Tiêu đề Cà khịa vẫn chứa marker của mức nghiêng, nên gate
  `stance_consistent` **bỏ miễn trừ cho Cà khịa**.
- Câu kết hướng nghiêng: 4 mức.
- Liên từ tóm tắt: 5 nhóm × 2. Gate `summary_links_cards` đếm cả liên từ Cà khịa.
- Câu dẫn theo dạng câu hỏi dùng chung cho mọi giọng (trung tính).
- Ngữ cảnh năng lượng và chăm mình: giữ quy tắc hiện có của `voice.py` (Cà khịa ở đây là giọng nhẹ). Khung vai,
  tiêu đề, câu kết và liên từ dùng bản thẳng; vẫn có câu mở đầu và đuôi giọng nhẹ như trước.
- Câu hỏi nhạy cảm vẫn bị `effective_voice` ép về giọng mặc định, có test qua service.

### 4. Phiên bản (AC18)

- Bài đọc có frame: `renderer = tarot-renderer-v7`, `gates = tarot-gates-v5`, `knowledge = tarot-knowledge-v5`
  (thêm nhãn lean theo lá × chủ đề và khung vai).
- Bài đọc không frame giữ `v6 / v4 / v4` như cũ. Các giá trị này thành hằng số `LEGACY_*`.
- `rewrite.py` coi bản gốc là mới nếu renderer khớp đúng loại bài (v7 cho bài có frame, v6 cho bài cũ).
- `TarotReadingProvenance`: bỏ default cũ (`knowledge-v2`, `renderer-v1`, `gates-v1`, `question-rules-v1`) cho
  4 trường engine luôn ghi. Mọi bản đọc đã lưu từ khi có Tarot (`b391e66`, 27/09) đều ghi đủ 4 trường qua
  `model_dump`, nên không bản đã lưu nào cần default.
- Meaning brief v3 để sang B2-4b cùng AC06.

### 5. Audit (AC20)

`audit_stance_and_headlines` chạy toàn ngân hàng × 6 map × **4 giọng**, có biến thể theo phiên. Báo phân bố
mức nghiêng, tỷ lệ trùng tiêu đề theo từng giọng (< 10%) và số câu chung chung (= 0). Thêm T4 (mục 2) và kiểm
độ dài xấu nhất cho mọi tổ hợp khung × câu dẫn × lá × chủ đề (câu ≤ 28 chữ, đúng trường của vai).

### 6. Tương thích (AC17)

- Phiên không frame: giống từng byte (golden `412f37f9…`).
- Bản B2-3 (v6 có frame, không biến thể) đã lưu vẫn validate và hiển thị.
- Trường mới đều nằm trong payload mã hoá; API và contract không thêm trường bắt buộc.

## Không làm trong B2-4a

- AC06 (payload Luna có mã nguồn gốc), meaning brief v3, AC14: B2-4b.
- Cảnh ví dụ mới (2–3 mỗi lá × chủ đề), câu hỏi tự soi theo vai × dạng: đợt nội dung riêng.
- Không bật Luna, không gọi API trả phí, không đổi `fallback-approval.json`.

## Ánh xạ AC

| AC | Trạng thái | Bằng chứng |
|---|---|---|
| AC15 | Xong cho khung vai, câu dẫn, tiêu đề. Trục cảnh đã có, mới 1 cảnh | `test_ac15_*` (chọn tất định theo guest/khoá/catalog; phiên liên tiếp khác nhau ở mọi trục; bản ghi chỉ có chỉ số, hỏng thì báo lỗi; qua service: xoay khoá và restart giữa lúc rút vẫn ra đúng bản đã rút, mở lại không cần khoá) |
| AC16 | Xong | `tarot:audit` T4: theo phiên **98,99%**, chỉ theo câu hỏi **84,98%**, cùng guest liên tiếp 99,28% trên 13 399 776 cặp (P1: 0%); `test_ac16_*` |
| AC17 | Xong phần render | golden phiên cũ `412f37f9…` không đổi; `test_ac17_a_stored_b2_3_framed_reading_still_validates`; phiên có frame chưa có biến thể dùng chỉ số 0 |
| AC18 | Xong renderer v7, knowledge v5, gates v5, default cũ. Brief v3 ở B2-4b | `test_ac18_*`; `test_tarot_rewrite_projects_through_encrypted_session_without_changing_cards` (bản gốc v7 không bị coi là cũ) |
| AC19 | Xong, chờ owner duyệt câu | `test_ac19_*` (ánh xạ 1-1 theo mã và cùng ô; tiêu đề và câu kết Cà khịa giữ đúng marker; gate từ chối tiêu đề Cà khịa thiếu marker và câu kết sai giọng; ngữ cảnh nhẹ giữ khung thẳng; câu nhạy cảm qua service ra giọng mặc định) |
| AC20 | Xong | `tarot:audit`: 7 104 bài (ngân hàng × 6 map × 4 giọng), tiêu đề trùng ≤ 2,52% mỗi giọng, chung chung 0; 864 lượt độ dài xấu nhất |
| AC06, AC14 | Chưa: B2-4b | — |

## Kết quả và các quyết định trong lúc làm

- Tự soát bài mẫu thấy Cà khịa vừa có khung riêng vừa gắn đuôi ở mọi vị trí, có đuôi lệch nghĩa (vd. "Phần này
  nằm trong tay bạn" ở vị trí điểm vướng). Vì vậy **bài có khung Cà khịa không gắn đuôi nữa**; ngữ cảnh năng
  lượng và chăm mình vẫn giữ đuôi giọng nhẹ. Câu mở đầu tóm tắt và khung việc nhỏ Cà khịa giữ như cũ. Owner
  có thể đảo quyết định này.
- Tiêu đề Cà khịa đầu tiên vượt 18 chữ với tên lá dài + cụm hành động 6 chữ (audit bắt được 3 bài). Đã rút
  gọn 5 khung và thêm test kiểm mọi khung tiêu đề ở độ dài xấu nhất.
- Ngân sách tóm tắt: với liên từ Cà khịa, khung gọn tối đa 160 chữ + dòng sẵn sàng 20 chữ = 180, vừa đúng trần;
  audit độ dài xấu nhất chạy cả Cà khịa.
- Khung vai B2-2 (khung 0) được rút ngắn cho vừa câu dẫn (mật độ ≤ 28 chữ/câu): vd. "Điều cần tính tới khi bước
  tiếp: {core}" → "Điều cần tính tới: {core}". Test kiểm mọi khung × câu dẫn dài nhất × 78 lá × 6 chủ đề.
- `fallback-approval.json` không đổi: copy mới nằm ở `roles.py`, `stance.py`, `variants.py`; engine chỉ import
  module (tên viết hoa import vào `engine.py` sẽ lọt vào bảng đã ghim). Hằng số phiên bản mới kết thúc bằng
  `VERSION` nên không vào bảng.

## Nội dung mới cần owner duyệt

File `docs/reviews/2026-10-18-b2-tarot-copy-review.xlsx` gom toàn bộ copy B2-1 → B2-4a, mỗi sheet có cột
"Duyệt" và "Góp ý":

1. Khung vai: 20 vai × 3 khung × (thẳng, Cà khịa) = 120 câu, theo mã tổ hợp.
2. Câu dẫn theo dạng câu hỏi: 6 dạng × 5 = 30 câu (dùng chung mọi giọng).
3. Tiêu đề động: 8 khoá × 3 × 2 = 48 khung.
4. Câu kết hướng nghiêng: 4 thẳng (B2-3) + 4 Cà khịa.
5. Liên từ tóm tắt: 10 thẳng (B2-3) + 10 Cà khịa.
6. Cụm từ B2-1/B2-3 còn chờ: câu sẵn sàng, 30 cụm hành động, 6 cụm chủ đề, nhãn lean 78 + 3 ghi đè.
7. 12 bài mẫu (6 câu hỏi tổng hợp × giọng mặc định và Cà khịa) để owner đọc theo checklist tâm lý (AC14).
8. Quyết định bỏ đuôi Cà khịa khi đã có khung Cà khịa.

Khi phát hành (sau duyệt): đưa `question_frame.py`, `roles.py`, `stance.py`, `variants.py` vào phạm vi phê duyệt
rồi làm mới `fallback-approval.json`.

## Bảo mật và riêng tư

- Không endpoint hay trường API mới. Contract chỉ bỏ default cũ của 4 trường provenance (kiểu TS vốn đã
  bắt buộc).
- Bản ghi `variants` chỉ là số nguyên trong payload AES-GCM, không chứa chữ, không chứa seed, không log, không
  trả qua API, không gửi provider; hết hạn/xoá cùng phiên. Seed dùng khoá chọn biến thể đã có (B3-1a), dẫn xuất
  tách miền từ `guest_hash_key`, không mã hoá hay xác thực gì.
- Bảng mới `tarot_variant_cursors` (migration `20261018_0037`): một số nguyên mỗi guest, bật RLS, thu hồi quyền
  client, không trả API, không log, xoá cùng guest. Data map đã cập nhật.
- Payload Luna không đổi (Luna vẫn tắt; Cà khịa không được gửi rewrite). Data map đã thêm mục delta B2-4a.
- Không có dữ liệu cá nhân mới, nên không cần rà lại luật; kế thừa kết luận của B3-1a cho khoá chọn biến thể.
