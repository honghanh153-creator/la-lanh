# Task B2-4b — Tarot T2: payload Luna có mã nguồn gốc, meaning brief v3, checklist tâm lý

> Nguồn đã duyệt:
> - `docs/user-stories/US-20-tarot-tra-loi-dung-cau-hoi.md` AC06, AC14, AC18 (brief v3);
> - `docs/foundation/la-lanh-plain-vietnamese-content-standard.md` "Checklist tâm lý";
> - `docs/plans/2026-10-18-b2-4-tarot-variety-roast-task.md` (phần hoãn sang B2-4b).
>
> Stacked trên B2-4a (PR #26, APPROVE @ `18ec6c8930feb8dfd6edbb7a2a8ecd38f2950aa3`). Luna vẫn tắt; mọi kiểm tra
> chỉ dựng payload tại chỗ, không gọi provider.

## Phạm vi

### 1. AC06: payload Luna có mã nguồn gốc (bài đọc có frame)

- **Schema** (`infrastructure/generation/privacy.py`, `extra="forbid"`):
  - `TarotMeaningBrief` nhận `tarot-meaning-brief-v3`, thêm `spread_map`, `summary_source {readiness}` và
    `stance {kind, level, action, options}`. Chỉ có nhãn đóng; câu kết và lý do hướng nghiêng vẫn ở local.
    Các trường này chỉ hợp lệ ở v3; v1/v2 (job cũ trong hàng đợi) không được mang.
  - `TarotPosition.source {frame, lead, gentle, reflection, action}`: mã catalog của mọi đoạn chữ ở vị trí đó.
    Brief v3 bắt buộc mọi vị trí có `source`; brief v1/v2 cấm có.
- **Reducer không ghép chuỗi từ input** (`tarot/provenance.py`):
  - `position_source` tìm mã catalog (khung vai × câu dẫn, cảnh, câu tự hỏi, việc nhỏ) tái tạo đúng chữ người
    đọc thấy. Không tìm được thì không có nguồn, compiler trả `None`, không có request.
  - Payload được dựng từ `resolve_position` / `resolve_summary` (chỉ từ mã), không chép chuỗi của bài đọc.
  - Mã nhóm mục tiêu lấy từ `question_goals` (nhãn đóng đã phân loại tại chỗ như renderer).
- **Kiểm nguồn gốc** (`untraced_paths`): duyệt mọi chuỗi lồng nhau; chuỗi nào không tra được về nhãn đóng hoặc
  mã catalog thì được báo. Compiler từ chối payload có bất kỳ chuỗi nào chưa tra được. Trường lạ cũng bị báo
  và bị schema từ chối.
- **Canary**: câu hỏi tổng hợp chứa `zqcanary7tim` và "chị Lan ở phòng 302", chạy qua engine → compiler và qua
  service (cờ generation bật, hàng đợi rewrite giả, không gửi đi). Không trường nào chứa canary hay cụm ≥ 2 từ
  liền nhau của cụm riêng tư, trừ khi cụm đó là chữ có sẵn trong catalog.
- Bài đọc **không frame** giữ brief v2 và payload như cũ (AC17). Cà khịa vẫn không bao giờ được gửi.
- Đổi chủ đích một test B2-3: payload giờ mang nhãn hướng nghiêng (AC06 cho phép), nhưng câu kết và lý do vẫn
  không ra ngoài.

### 2. AC18: meaning brief v3

Brief v3 = mục 1. `MEANING_BRIEF_VERSION` của brief v2 không đổi cho phiên cũ.

### 3. AC14: checklist tâm lý

- `tarot/checklist.py` kiểm các mục máy kiểm được; `tarot:audit` chạy trên toàn ngân hàng × 6 map × 4 giọng.
  - **Gate**: tiêu đề không khuyên (đã bỏ marker hướng nghiêng và cụm hành động đã duyệt trước khi quét);
    phần chữ do engine viết không ép buộc ("bạn phải", "nhất định", "nếu không thì", "bắt buộc"; câu phủ định
    như "không ai bắt bạn phải gồng" không tính); bài kết ở vị trí bước tiếp có việc nhỏ; tóm tắt kết ở câu
    của bước đó.
  - **Báo cho owner, không gate**: số ý điểm vướng/cái giá theo map; số ô cảnh có từ khuyên; tỷ lệ việc nhỏ có
    "khi…".
- Sửa 6 tiêu đề động còn mang lời khuyên ("nên", "khoan", "đừng vội", "xem…", "rồi hẵng tính"); test quét mọi
  khung tiêu đề với mọi cụm hành động.
- Sheet "Checklist AC14" trong file duyệt: kết quả máy cho từng bài mẫu và cột để owner chấm các mục còn lại.

## Sửa theo review Codex #27 (@ `e0842a5`)

1. **P2-1:** `PrivacyMinimiser` bỏ key null (`exclude_none`), nên payload thật trong hàng đợi và ở adapter
   provider mất `source.action` (vị trí không phải bước tiếp) và `source.lead` khi null. Resolver giờ đọc mã tuỳ
   chọn vắng mặt là null, đúng như schema. Compiler và audit kiểm **cả payload dựng ra lẫn bản đã chuẩn hoá**;
   test service đi qua `ContentRewriteService` thật (registry, authorization, minimiser) với repository giả.
2. **P2-2:** ngoại lệ checklist chỉ còn đúng ngữ cảnh đã duyệt:
   - ép buộc: chỉ miễn cụm phủ định "không ai bắt bạn phải"; "Lá/Tôi bắt bạn phải…" bị bắt;
   - tiêu đề: chỉ miễn khi tiêu đề khớp **trọn vẹn** một khung tiêu đề đã duyệt (tên lá thật, cụm hành động và
     chủ đề đã duyệt); chữ của chính khung được kiểm riêng bằng `template_gives_advice`. Tiêu đề khác quét đầy
     đủ, nên "<lá>: thử lại đi." bị bắt; "…trước khi thử lại" và marker hướng nghiêng vẫn hợp lệ.

3. **P2 (review @ `f7b0798`):** `{pair}` trong khung tiêu đề nhận **một hoặc hai** tên lá thật, khớp
   `stance.dynamic_headline` (trải 1 lá chỉ có lá trọng tâm). Regression: "Làm thế nào để mình thử lại việc này?" trên
   1 lá × 4 giọng × 3 biến thể; đối chứng nhiều lá và chặn "thử lại đi" vẫn giữ.

## Ánh xạ AC

| AC | Trạng thái | Bằng chứng |
|---|---|---|
| AC06 | Xong (schema, kiểm nguồn gốc, canary) | `tests/tarot/test_provenance.py`; `tarot:audit`: 5 340 payload giọng thẳng, mọi chuỗi đều tra được |
| AC18 (brief v3) | Xong | `test_ac06_framed_payload_is_brief_v3_with_a_source_per_position`; job v1/v2 vẫn qua schema |
| AC14 | Phần máy: xong. Phần đọc: chờ owner | `tests/tarot/test_checklist.py`; `tarot:audit`; sheet "Checklist AC14" |

## Kết quả audit cần owner quyết

- **Tối đa một ý tiêu cực mỗi bài**: map 3 lá và "rõ ràng" có 1; "hội thoại" và 1 lá có 0; **"vòng lặp" có 2**
  (phản xạ quen + cái giá) và **"lựa chọn" có 3** (giá của A, giá của B, điểm cần cân). Đây là cấu trúc map,
  không phải lỗi câu. Owner chọn: chấp nhận ngoại lệ cho hai map này, hoặc gộp/đổi vai ở B2 sau.
- **Cảnh có từ khuyên**: 3 096 trên 28 416 ô cảnh của 7 104 bài khớp "hãy/thử/nên/đừng". Phần lớn "thử" là kể
  chuyện ("muốn thử một hoạt động mới"), không phải khuyên; cần owner đọc khi duyệt cảnh. Đây là catalog cũ.
- **Việc nhỏ có "khi…"**: 876/7 104 (12%). Chuẩn nội dung muốn việc nhỏ có tình huống kích hoạt; cần một đợt
  biên tập catalog hành động.

## Phát hành (ghi nhận theo review Codex #26)

Trước khi phát hành B2: rehearsal migration `20261018_0037` / cursor / RLS trên PostgreSQL bằng **backend role
thật** (không phải SQLite hay biên dịch DDL), theo mục Tarot B2 trong
`docs/operations/chart-synthesis-release-runbook.md`. Owner duyệt copy, rồi đưa `question_frame.py`, `roles.py`,
`stance.py`, `variants.py` vào phạm vi phê duyệt và làm mới `fallback-approval.json`.

## Rủi ro còn mở

- Prompt Tarot của Luna (`infrastructure/generation/schemas.py`) chưa nói rằng `source` và `stance` là mã/nhãn
  provenance, không phải nội dung để viết lại. Không sửa prompt trong PR này (đổi prompt kéo theo phiên bản
  prompt và corpus rewrite); phải làm trước khi bật Luna.
- Kiểm nguồn gốc chứng minh mọi chuỗi tái tạo được từ catalog, không chứng minh catalog không chứa chữ trùng
  ngẫu nhiên với câu hỏi; trường hợp đó được AC06 cho phép.

## Bảo mật và riêng tư

- Không endpoint, bảng hay trường API mới. Không đổi gì lưu trong DB.
- Nếu sau này bật Luna, payload Tarot có frame gửi thêm **mã catalog** và **nhãn hướng nghiêng đóng**. Không có
  dữ liệu cá nhân mới; câu hỏi, frame, biến thể và cursor vẫn không ra ngoài. Mã câu dẫn nêu dạng câu hỏi,
  nhưng chữ câu dẫn tương ứng vốn đã nằm trong `meaning_here`. Data map đã cập nhật.
- Luna vẫn tắt; không gọi API trả phí. Khai báo store và privacy policy không đổi vì không có loại dữ liệu
  hay bên nhận mới.

## Nội dung mới cần owner duyệt

6 tiêu đề động viết lại: bản thẳng `headline.consider.1`, `headline.clarify_choice.1`; bản Cà khịa `headline.consider.1`, `headline.consider.2`, `headline.clarify_choice.0`, `headline.clarify_choice.2`. File
duyệt đã tạo lại; phần còn lại giữ như B2-4a.
