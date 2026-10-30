# Spec đo đa dạng và cá nhân hoá, kèm fixture (P0)

Phiên bản: `variety-measurement/v1` (16/10/2026). Nguồn: plan §0, §14.6, §14.6b (Codex APPROVE @ 8574d72).
Mọi dữ liệu là tổng hợp, không lấy từ người dùng thật. Mọi chỉ số tính trên **output cuối cùng được phục
vụ** (sau khi chọn, sau ngoại lệ và kho nền), không tính trên lịch build.

## 1. Fixture

| Fixture | Nội dung | Nơi lưu (P1 tạo) |
|---|---|---|
| **Profile Daily** | Đủ để mỗi nhóm ở §3 có ≥ 50 profile, sinh tất định từ seed (ngày sinh 1970–2008, có hoặc không giờ/nơi, mối quan tâm có hoặc không). Gồm fixture pool một phần tử, tag hẹp, và không có chương chắc | `apps/api/tests/fixtures/variety/profiles-v1.json` |
| **Cặp trùng ngày sinh** | ≥ 20 cặp cùng ngày sinh, cùng không rõ giờ | cùng file, nhóm riêng |
| **Ngân hàng câu hỏi Tarot** | `docs/fixtures/tarot-question-bank-v1.json`: 288 câu chấp nhận (6 chủ đề × 6 dạng × 8), 32 câu phải từ chối hoặc hỏi lại, 8 ca dễ nhầm | đã có trong P0 |
| **Cặp Hợp gu** | 50 cặp (có giờ và không rõ giờ) × 4 ngữ cảnh × 4 giọng | `apps/api/tests/fixtures/variety/radar-pairs-v1.json` |
| **Offset** | Trải `offset` sao cho mỗi profile có ít nhất một lần qua biên lịch trong cửa sổ, và tổng thể phủ mọi vị trí biên | sinh trong script đo |

**Kiểm fixture Tarot với engine hiện tại** (16/10, `TarotReadingEngine.assess_question` tại main
836222282dfc; `apps/api` của PR này giống hệt). Mục có `context: null` dùng `general`. Lệnh tái hiện:
`cd apps/api && PYTHONPATH=. uv run python ../../docs/fixtures/validate_tarot_question_bank.py`.

| Nhóm | Mẫu số | Kết quả với engine hiện tại |
|---|---|---|
| Câu thường, không phải "khi nào" | 240 | 240 chấp nhận |
| Ca dễ nhầm, không phải "khi nào" (`edge.1–5,7,8`) | 7 | 7 chấp nhận |
| "Khi nào" trong nhóm thường | 48 | 48 bị từ chối |
| "Khi nào" kể cả `edge.6` | 49 | 49 bị từ chối (US-20 AC05 đổi hành vi này) |
| Từ chối: đoán ý người khác, đòi chắc chắn, rủi ro cao | 24 | 24 bị từ chối |
| Câu mơ hồ (`too_vague`) | 8 | 6 chấp nhận, 2 bị từ chối (lỗ hổng, US-20 AC04) |
| Toàn fixture | 328 | 253 chấp nhận, 75 bị từ chối |

Đây là hành vi **hiện tại**. Giá trị `expected` trong fixture là mục tiêu T2, nên không được sửa expected
để baseline hiện tại trông như đạt. *Đính chính:* bản nháp trước ghi "273/273 câu không phải 'khi nào'
được chấp nhận". Thật ra 273 là tổng số mục khớp kỳ vọng hiện tại (240 + 7 chấp nhận, 24 + 2 từ chối).

## 2. Cửa sổ và chuẩn hoá

- **Daily:** 200 ngày lịch liên tiếp mỗi profile (MVP_TIMEZONE), bắt đầu từ cùng một ngày cho cả tập.
- Mọi cạnh biên L−1 → 0 cũng được kiểm ở build trên từng lịch, không chỉ dựa vào cửa sổ đo.
- **Chuẩn hoá câu:** NFC, chữ thường, gộp khoảng trắng, bỏ dấu câu cuối. So riêng từng phần (tiêu đề, cảnh,
  việc nhỏ, lời của Lá, "Vì sao hôm nay?") và riêng từng giọng.

## 3. Nhóm (mẫu số tính riêng, không gộp)

Giờ sinh (biết / không biết) × mối quan tâm (đã chọn / chưa) × pool tình huống (1 / 2–3 / ≥ 4) × chương
(có cửa sổ chắc / không). Mỗi nhóm ≥ 50 profile. Nhóm không đủ profile thì báo "thiếu mẫu", không suy ra.

## 4. Chỉ số

| # | Chỉ số | Cách tính | Ngưỡng đề xuất (owner chốt) |
|---|---|---|---|
| M1 | Khoảng cách lặp câu | Với mỗi profile × phần, khoảng ngày ngắn nhất giữa hai lần cùng câu, bỏ ngày ngoại lệ. Profile đạt khi ≥ 90 hoặc không lặp | ≥ 95% profile đạt **trong mỗi nhóm khả thi** |
| M2 | Vi phạm (a) | Số cặp ngày liên tiếp không ngoại lệ có ô bắt buộc đổi trùng nhau | 0 |
| M3 | Tỷ lệ ngoại lệ | Ngày có `variety_exception` / tổng ngày, theo lý do | 0 với lý do gate; báo riêng lý do manifest |
| M4 | Note giống hệt | Cặp profile khác nhau, cùng cung, cùng ngày, note giống hệt sau chuẩn hoá | < 1%; cặp trùng ngày sinh báo riêng |
| M5 | Yếu tố riêng | Đếm theo §5, trung bình và phân vị 10 | Theo nhóm (owner chốt) |
| M6 | Chương | Tỷ lệ ngày nằm trong cửa sổ chắc của một chương; tỷ lệ ngày nói "Ngày N" ngoài cửa sổ chắc | Tỷ lệ thứ hai = 0 |
| M7 | Ablation | Giữ salt, đổi từng tín hiệu (giờ sinh, mối quan tâm, ngày); tỷ lệ phần nội dung đổi | Báo cáo; không có ngưỡng ở P0 |
| M8a | Phủ allowlist ngữ pháp | Mẫu số: output ngữ pháp **không** ngoại lệ. Tử số: output có mã tổ hợp thuộc allowlist của manifest hợp lệ đang dùng | 100% |
| M8b | Mọi output đến từ nguồn đã duyệt | Mẫu số: **mọi** output được phục vụ, gồm cả ngoại lệ và kho nền. Tử số: output thuộc allowlist ngữ pháp hợp lệ, **hoặc** do kho nền ở đúng phiên bản đã duyệt tạo ra (§4b) | 100%. Báo riêng số output kho nền theo lý do |
| T1–T4 | Tarot | Đúng dạng câu (≥ 95%), tiêu đề trùng < 10%, câu chung chung = 0, cùng lá × vai khác câu với ≥ 80% cặp câu hỏi | theo US-20 |
| R1–R3 | Hợp gu | ≥ 2 câu contact mỗi bài, đổi ngữ cảnh hoặc giọng thì ≥ 50% câu đổi, trùng câu giữa cặp < 30% | theo US-22 |

### 4b. Kho nền và nguồn phê duyệt độc lập

- **Kho nền** là renderer tất định hiện hành (plan nền §2): các bảng của `daily_psychology`, catalog lời của
  Lá, tri thức Tarot và Hợp gu, ở phiên bản đang live.
- **Nguồn phê duyệt độc lập:** file `docs/operations/fallback-approval.json`, tạo ở G0, độc lập với manifest
  ngữ pháp. File gồm:
  - `renderer_version` của từng mảng;
  - hash nội dung của từng bảng nguồn;
  - phiên bản gate;
  - bằng chứng duyệt: content audit, `review_content_release` (direct và roast), receipt owner duyệt, ví dụ
    workbook 16/10 và release `836222282dfc`.
- CI kiểm hash hiện tại khớp file này. Không khớp thì build đỏ.
- **Runtime:** output kho nền ghi provenance `renderer_version` và hash bảng nguồn. M8b chỉ tính output kho
  nền khi provenance khớp `fallback-approval.json`.
- Cờ `variety_exception` **không** phải bằng chứng nội dung an toàn. Nếu kho nền cũng không hợp lệ thì
  không phục vụ được (fail closed ở build hoặc khởi động), giống cổng content review hiện có của
  `deploy.sh`.
- **Kỳ vọng M8 trong các AC:**

  | Tình huống | M8a | M8b | Ghi nhận |
  |---|---|---|---|
  | Ép gate từ chối ngày D (G-AC1) | D không vào mẫu số | D vào mẫu số, đạt nhờ kho nền đã duyệt | `variety_exception.reason = gate_rejected`, counter +1 |
  | Manifest **thiếu** (G-AC5a) | không có output ngữ pháp, mẫu số = 0 (báo "không áp dụng") | 100% từ kho nền đã duyệt | reason = `manifest_missing` cho mọi ngày bị ảnh hưởng |
  | Manifest **hỏng hoặc sai hash** (G-AC5b) | như trên | như trên | reason = `manifest_corrupt` |
  | Kho nền sai hash so với `fallback-approval.json` | không áp dụng | build hoặc khởi động thất bại, không phục vụ | không có output |

### 4c. Công thức tất định cho chỉ số Tarot và Hợp gu

Mọi phép đo dùng seed cố định trong fixture, nên hai bên chạy lại cho cùng mẫu số.

- **T1, đúng dạng câu:** số mục có `form` khác null mà dạng phân loại đúng, chia cho số mục đó. Mẫu số hiện
  là 289 (288 câu thường + `edge.6`). Mục từ chối và các ca dễ nhầm khác có `form` null, không tính.
- **T2, phần mở đầu trùng:** chạy mọi mục chấp nhận × mọi map hợp lệ × 4 giọng với seed phiên cố định.
  `1 − (số phần mở đầu khác nhau sau chuẩn hoá / số bài)`, tính riêng theo giọng. Phần mở đầu là tiêu đề cộng
  tóm tắt. Từ 29/10/2026 tiêu đề không nêu tên lá theo góp ý của owner, nên tỷ lệ trùng của riêng tiêu đề chỉ
  để báo cáo.
- **T3, câu chung chung:** đếm câu khớp danh sách mẫu chung (nhánh `else` cũ, các tiền tố đã bỏ) trên toàn bộ bài
  của T2. Phải bằng 0.
- **T4, cùng lá × vai khác câu:** với mỗi (lá, vai, chủ đề), ghép từng cặp câu hỏi khác nhau trong cùng chủ
  đề từ fixture, ép cùng lá ở cùng vai. Tỷ lệ cặp có câu khác nhau sau chuẩn hoá.
- **R1:** số câu contact mỗi bài, trên 50 cặp × 4 ngữ cảnh × 4 giọng. Cặp không đủ contact chắc được báo
  riêng, không dựng thêm câu.
- **R2:** cùng cặp, đổi ngữ cảnh hoặc giọng. Tỷ lệ câu của mục "hợp" và "ma sát" khác nhau sau chuẩn hoá.
- **R3, trùng giữa cặp:** với mỗi (ngữ cảnh, giọng), tỷ lệ câu của một cặp cũng xuất hiện ở ít nhất một cặp
  khác, lấy trung bình trên các cặp.

**Bucket không khả thi** (lịch chủ < 90) là "mục tiêu có điều kiện": báo tỷ lệ không đạt riêng và không
tính vào ngưỡng M1. Không làm loãng căn cứ để đạt đa dạng.

## 5. Yếu tố riêng: nguồn độc lập, mỗi nguồn tối đa một lần

1. **Transit cá nhân chắc:** `orb_max ≤ θ` tới điểm natal của chính người đó. Chương và nhịp của cùng
   transit này không tính thêm.
2. **Sự kiện lịch khác:** một sự kiện thiên văn khác với nguồn 1.
3. **Cấu hình natal riêng:** luật cặp hoặc nhà dùng trong bài.
4. **Mối quan tâm đã chọn:** thực sự được dùng để chọn nội dung.

Salt không tính. Nhóm có ít dữ kiện chắc được phép ít yếu tố hơn, và bài không dựng thêm để đủ số.

## 6. Lặp giữa các màn (đề xuất AC, chưa phải bảo đảm)

- **Phạm vi:** ngày lịch (MVP_TIMEZONE); lời của Lá + note ngày + mọi phiên Tarot và kết quả Hợp gu tạo
  trong ngày đó.
- **So sánh:** theo mã hành động (mức nghĩa) và câu sau chuẩn hoá.
- **Cơ chế:** namespace hành động tách theo màn. Kiểm tách ở **mức nghĩa và câu thật**, không chỉ khác
  tiền tố ID. Không phụ thuộc thứ tự mở màn.
- Đổi giọng không tính là mới. Snapshot của ngày trước không xét và không bị sửa.
- **Báo cáo:** số cặp trùng trên mô phỏng 30 ngày × fixture.

## 7. Báo cáo

Script P1 xuất JSON và Markdown gồm:

- mọi chỉ số theo nhóm;
- mẫu số;
- số ngoại lệ theo lý do;
- danh sách bucket có điều kiện;
- phiên bản catalog, manifest, spec.

Floor đưa vào `content-matrix-baseline.json` sau khi owner chốt ngưỡng.
