# Task G0 — composer và allowlist dựng lúc build (hạ tầng ngữ pháp chung)

> Nguồn đã duyệt:
> - `docs/plans/2026-10-16-personalisation-variety-plan.md` §6 bước 4 và §14.2;
> - `docs/foundation/la-lanh-content-grammar-spec.md` §2–§7;
> - `docs/foundation/la-lanh-variety-measurement-spec.md` §4b;
> - quyết định owner A2, A4, A5 (`docs/plans/2026-10-16-p0-owner-decisions.md`).
>
> Làm sau B3-1a (PR #21, APPROVE @ `f118f60`). Stacked trên branch đó.

## Phạm vi

**Làm:**

1. **Định dạng catalog** (`app/domains/grammar/models.py`), chốt ở G0:
   - JSON, không YAML, để không thêm dependency.
   - Mỗi surface có `app/domains/<domain>/grammar/catalog.json` cùng `frames/*.json`. Daily nằm ở
     `app/domains/readings/grammar/`.
   - Giá trị ô có `id` ổn định. Constraint (`if`/`forbid`/`require`), mã tổ hợp và ánh xạ Cà khịa đều theo
     id, nên sửa chữ không làm vỡ chúng.
   - Ba loại ô:
     - `must_change`;
     - `bucket` (`by` + `buckets`, bắt buộc có `_default`);
     - `repeatable`. Ở G0 chỉ nhận **một** giá trị; nhiều giá trị thì build từ chối và yêu cầu tách khung hoặc
       chuyển sang `bucket`.
   - Template chỉ chứa placeholder `{slot}` thuần, theo đúng thứ tự ô.
2. **Composer** (`composer.py`), theo spec §3 bước 1–5:
   - liệt kê mọi tổ hợp của từng khung × bucket và áp constraint;
   - ghép, rồi chuẩn hoá: NFC, khoảng trắng, dấu câu, viết hoa đầu câu;
   - gate từng câu;
   - khử trùng theo **đúng chuẩn hoá của spec đo §2** (`scripts/variety_baseline.normalize`): NFC,
     casefold, gộp khoảng trắng, bỏ dấu câu cuối. Hai câu chỉ khác `.`/`!` là một câu:
     - một câu chỉ thuộc một tổ hợp chủ, nên cam kết (b) giữ cả khi đổi bucket;
     - một câu chỉ xuất hiện một lần trong mỗi bucket;
     - một câu chỉ thuộc một khung trong cùng surface và giọng.
3. **Gate từng câu** (`gate.py`). Dùng lại luật mức văn bản của gate live, đã tách ra từ `readings/gates.py`
   mà không đổi hành vi:
   - anti-influence, editorial, privacy, `BANNED_CORE_FRAGMENTS`;
   - tiêu đề và cảnh không được chứa lời khuyên;
   - việc nhỏ phải có hành động quan sát được và anchor nghĩa của tình huống;
   - lời của Lá phải qua nudge checker.

   `evaluate_candidate` vẫn là lưới an toàn lúc chạy, theo spec §5.
4. **Lịch chủ** (`schedule.py`), theo spec §3 bước 6:
   - DFS tất định có giới hạn bước. Ứng viên quét lười theo thứ tự hash của biến thể; **không dựng graph láng
     giềng**. Một bước là một phép kiểm kề nhau hoặc một tổ hợp được đặt vào lịch, nên công việc trước khi bỏ
     cuộc luôn ≤ budget A4 (2 000 000), kể cả với miền lớn (161 051 tổ hợp chủ trong test);
   - kề nhau và độ phủ chứng minh trên id, còn build bảo đảm id khác nhau thì **chữ hiển thị cũng khác nhau**
     sau chuẩn hoá (xem mục 5);
   - chu trình khép kín dài L, hai phần tử kề nhau (kể cả cuối → đầu) khác nhau ở mọi ô bắt buộc đổi;
   - mỗi tổ hợp chủ dùng một lần, mỗi giá trị ô bắt buộc đổi có mặt ít nhất một lần;
   - tổ hợp chủ chỉ vào lịch khi có trong allowlist của **mọi** bucket;
   - dựng **đúng M** biến thể khác nhau (không tính bản chỉ xoay vòng). Manifest ghi M, và runtime chọn
     `variant = seed mod M`, nên dựng thiếu thì build từ chối.
5. **Build và luật từ chối** (`build.py`). CI đỏ khi:
   - L nhỏ hơn mức tối thiểu (90, owner A2) hoặc M nhỏ hơn mức tối thiểu (4, owner A4);
   - không dựng được lịch, hoặc dựng được ít hơn M biến thể;
   - hai giá trị của một ô bắt buộc đổi có chữ trùng nhau sau chuẩn hoá, ở giọng direct hoặc Cà khịa;
   - vượt giới hạn A4 (200 000 tổ hợp mỗi khung × bucket, 48 bucket, 2 000 000 bước);
   - thiếu khung Cà khịa, Cà khịa không khớp ô/id, hoặc có tổ hợp direct không có bản Cà khịa trong allowlist;
   - vi phạm tách từ vựng: khung headline/scene chứa giá trị hoặc từ vựng `action` của cùng bài;
   - có hơn một khung `negative_role` trong một bài, hoặc giá trị `negative` nằm ngoài khung đó;
   - còn câu bị gate trong allowlist.
6. **Manifest:**
   - `spec_version`, `catalog_version`, `catalog_sha256`, `composer_version`, `gate_version`;
   - L, M, giới hạn, bài;
   - số liệu từng khung;
   - hash của từng allowlist và từng biến thể lịch;
   - ngoại lệ đã review;
   - hash các file build.

   Build ghi vào `grammar/build/` và được commit. `pnpm grammar:check` từ chối khi có lệch.
7. **Runtime đọc-only** (`runtime.py`), **chưa nối vào bài nào**:
   - `load_grammar` trả `ok`, `manifest_missing` hoặc `manifest_corrupt`. Trước khi trả `ok`, nó kiểm:
     - phiên bản và hash;
     - **schema và kích thước** của manifest: L, M (số nguyên, khớp catalog), độ phủ khung;
     - với mỗi khung direct, đúng M lịch, mỗi lịch dài L, không trùng, mã đúng ô;
     - mỗi tổ hợp chủ có trong mọi bucket.

     Không ghép câu nào trong lúc kiểm. Lệch bất kỳ điểm nào đều là `manifest_corrupt`;
   - `select` chọn câu ở vị trí `(biến thể, p, bucket)`;
   - `roast` tra cùng mã tổ hợp, không chạy lại lịch;
   - `schedule_position` tính `p = (day_index + offset) mod L` từ seed.
8. **Kho nền đã duyệt:** `docs/operations/fallback-approval.json` cùng `scripts/fallback_approval.py`
   (measurement spec §4b).
   - File ghim hash của từng bảng nội dung: tâm lý Daily, lời của Lá và giọng Cà khịa, tri thức Tarot, copy
     Hợp gu. Kèm phiên bản renderer, phiên bản gate và bằng chứng duyệt.
   - Hash **trùng khớp với release `836222282dfc`**: đã tính lại trên worktree của commit đó.
   - CI đỏ khi code lệch file này.
9. **Một khung mẫu:** `daily.missing-context.advice`, gồm bản direct và Cà khịa.
   - Ô: trigger 6, động từ 5, đối tượng 4 (đều bắt buộc đổi), đuôi theo lens (`_default`, `work`,
     `relationships`).
   - 5 constraint, có ví dụ "hỏi thẳng" của spec, cùng các cặp lặp từ.
   - Kết quả: 99 tổ hợp chủ đủ điều kiện, 486 câu mỗi giọng, 4 biến thể L = 90 (169–195 bước), build khoảng
     0,2 giây.
   - `serving: false`: không phục vụ, không đổi nội dung hiển thị.

**Không làm:**

- Nối grammar vào renderer, `variety_exception`, counter và đường kho nền lúc chạy (G1). Có test chứng minh
  API không import package grammar.
- Kiểm fail-closed của kho nền lúc khởi động: G0 chỉ kiểm ở build/CI, vì runtime chưa phục vụ grammar.
- Lịch ghép chung cho quy tắc giữa khung không đưa được vào cấu trúc: chưa có khung nào cần.
- Ô `repeatable` nhiều giá trị; khung Cà khịa ít ô hơn khung direct. Cả hai để G1 nếu cần.
- Nội dung thật cho 20 tình huống, owner duyệt giá trị ô và mẫu ghép qua Excel (A5), owner đọc 14 ngày mẫu: G1.
- Báo cáo M8a/M8b trên output được phục vụ: G1.

## Ánh xạ AC (spec §7)

| AC | Trạng thái ở G0 | Bằng chứng (`tests/grammar/test_grammar.py`) |
|---|---|---|
| G-AC1 ép gate từ chối ngày D | G1 (cần runtime phục vụ) | — |
| G-AC2 đổi bucket ở mọi `p` | Xong trên khung mẫu: 4 biến thể × 3 kiểu đổi bucket × 180 ngày, cả hai giọng | `test_bucket_changes_keep_a_and_b_for_both_voices` |
| G-AC3 biên L−1 → 0 | Xong | `test_every_variant_is_a_valid_closed_cycle_with_full_coverage` |
| G-AC4 CI đỏ | Xong: tách từ vựng, phân vai, giá trị tiêu cực sai chỗ, thiếu hoặc lệch Cà khịa, vượt giới hạn, L dưới mức, lịch không khả thi, repeatable nhiều giá trị, template không an toàn | `test_*_is_refused`, `test_combination_and_bucket_limits_are_enforced` |
| G-AC5 manifest thiếu/hỏng | Một phần: loader trả đúng trạng thái và không bao giờ ghép; phục vụ kho nền và counter thuộc G1 | `test_missing_or_corrupt_manifest_never_composes` |
| G-AC5c kho nền sai hash | Xong ở build/CI; lúc khởi động thuộc G1 | `test_fallback_approval_matches_the_live_tables`, `pnpm grammar:check` |
| G-AC6 đổi giọng, replay, chia sẻ | Một phần: Cà khịa tra theo mã tổ hợp; replay khi nối vào plan thuộc G1 | `test_bucket_changes_keep_a_and_b_for_both_voices` |
| G-AC7 báo cáo | G1 | — |
| G-AC8 direct và Roast | Xong cho (a)/(b)/(c) trên khung mẫu | như G-AC2 |
| G-AC9 phản ví dụ allowlist | Xong | `test_codex_counterexample_allowlist_is_refused` |

## Sửa theo review Codex @ `ab34eae` (5 P2)

| P2 | Sửa | Regression (fail trên `ab34eae`, pass bây giờ) |
|---|---|---|
| 1. Id khác nhưng chữ trùng làm ô bắt buộc đổi không đổi trên output | Build từ chối giá trị trùng chữ **như sẽ hiển thị**: chuẩn hoá ghép câu của composer trước (ví dụ bỏ khoảng trắng trước dấu phẩy), rồi đến chuẩn đo (`value_identity`). Áp cho cả hai giọng; chuẩn đo câu giữ nguyên | `test_p2_1_must_change_ids_with_the_same_text_are_refused`: khung chéo L = 90, M = 4, direct và Cà khịa. `test_p2_1_values_that_render_the_same_are_refused`: "tin nhắn," / "tin nhắn ," với 108 tổ hợp chủ, direct và Cà khịa, kèm đối chứng sạch dựng được (sửa thêm theo review @ `602e727`) |
| 2. Khử trùng giữ dấu câu cuối | Khoá khử trùng = chuẩn hoá của spec đo; `COMPOSER_VERSION` lên `grammar-composer-v2` | `test_p2_2_sentence_identity_follows_the_measurement_normalisation`: 45 cặp `.`/`!`, direct và Cà khịa; `test_p2_2_a_sentence_never_moves_to_another_master_across_buckets` |
| 3. Graph láng giềng bậc hai dựng trước budget | Quét lười, mọi phép kiểm kề nhau đều tính vào budget | `test_p2_3_schedule_search_does_no_unbudgeted_quadratic_work`: 10×10×5 với `max_steps=1` gọi ≤ 2 phép kiểm; 11⁵ = 161 051 tổ hợp chủ vẫn dựng được trong 10 000 bước |
| 4. M dựng được khác M trong manifest | Từ chối nếu số biến thể ≠ M; `select` từ chối biến thể ngoài khoảng | `test_p2_4_published_variant_count_matches_the_manifest` (gồm chọn mọi biến thể đã công bố) |
| 5. Manifest có L/M hỏng vẫn `ok` | Kiểm schema, kích thước và độ phủ trước khi trả `ok` | `test_p2_5_inconsistent_manifest_dimensions_are_corrupt` (5 ca; fail khi tắt bước kiểm kích thước) |

## Bảo mật và riêng tư

- **Không có endpoint, bảng, cột hay dữ liệu cá nhân mới.**
  - Catalog và allowlist là nội dung tĩnh trong repo.
  - Gate privacy chặn câu có email, số điện thoại, ngày tháng hay ID.
- **Runtime chỉ đọc file trong repo:**
  - parse bằng JSON và pydantic, không có eval;
  - template chỉ nhận placeholder thuần, nên không truy cập được thuộc tính qua `str.format`;
  - manifest sai hash thì không bao giờ ghép.
- Không gọi provider hay API trả phí. Provenance `ai_authoring` bắt buộc có `model` và `prompt_version`.
- Không cần cập nhật khai báo store hay privacy copy.

## Rủi ro

- **Kích thước allowlist:** khoảng 240 KB cho một khung × 2 giọng. Ở quy mô G1 (20 tình huống × nhiều khung)
  cần nén mã tổ hợp hoặc lưu theo khung trước khi commit hàng loạt.
- **Tự nhiên của câu:** "100% trong allowlist" chỉ chứng minh độ phủ của kiểm tra máy. Khung mẫu chưa qua
  owner duyệt.
- **Gate động từ hành động** dùng so khớp chuỗi con của gate live, nên có thể nhận nhầm. Không đổi ở G0, vì
  đổi sẽ ảnh hưởng nội dung đang live.
