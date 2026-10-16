# Spec ngữ pháp nội dung và lịch chủ (P0, bản triệt để)

Phiên bản spec: `content-grammar-spec/v1` (16/10/2026). Nguồn: kế hoạch
`docs/plans/2026-10-16-personalisation-variety-plan.md` §2 và §14.2 (Codex APPROVE @ 8574d72). File này cụ
thể hoá phần đó để G0 triển khai. Chỗ nào spec và plan lệch nhau thì plan đã duyệt là chuẩn, và spec phải
sửa theo.

## 1. Khái niệm

| Khái niệm | Định nghĩa |
|---|---|
| **Khung** (frame) | Một phần của bài (tiêu đề, cảnh, việc nhỏ, lời của Lá, vai Tarot, câu contact Hợp gu, …). Gồm một mẫu câu và danh sách ô theo thứ tự |
| **Ô** (slot) | Vị trí trong mẫu, có danh sách **giá trị** đã duyệt |
| **Ô bắt buộc đổi** | Ô phải khác nhau giữa hai ngày lịch liên tiếp. Không phụ thuộc bucket |
| **Ô được lặp** | Ô có thể giữ nguyên (ví dụ danh từ của tình huống) |
| **Ô theo bucket** | Ô mà giá trị phụ thuộc bucket (ví dụ cụm danh từ hợp mối quan tâm). Không tính vào cam kết (a) |
| **Bucket** | Một tổ hợp tag đủ điều kiện: lens × mối quan tâm × nhịp chương (Daily); ngữ cảnh (Hợp gu); chủ đề (Tarot) |
| **Tổ hợp chủ** | Bộ giá trị của các ô bắt buộc đổi |
| **Lịch chủ** | Chu trình khép kín dài L trên các tổ hợp chủ của một khung |
| **Biến thể lịch** | Một trong M lịch chủ khác nhau đã được chứng minh của cùng khung |

## 2. Định dạng catalog

Mỗi khung là một mục YAML hoặc JSON trong `apps/api/app/domains/<surface>/grammar/`. Vị trí chính xác chốt
ở G0.

```yaml
frame_id: daily.missing-context.advice
surface: daily            # daily | tarot | radar | companion
part: advice              # headline | scene | advice | companion | role:<vai> | contact
voice: direct             # direct | roast (khung roast riêng, ánh xạ theo mã tổ hợp)
template: "{trigger} {verb} {object}."
slots:
  trigger: {kind: must_change, values: [t1, t2, ...]}
  verb:    {kind: must_change, values: [...]}
  object:  {kind: bucket, by: focus, values: {hoc_tap: [...], cong_viec: [...], _default: [...]}}
constraints:              # loại trừ/bắt buộc đi cùng, kiểm ở build
  - {if: {verb: "hỏi thẳng"}, forbid: {trigger: ["Lúc đọc lại đoạn chat,"]}}
meaning_key: missing-context
negative_role: false      # chỉ một khung mỗi bài được true (phân vai ý tiêu cực)
vocab_class: action       # tách từ vựng giữa khung: headline/scene không dùng vocab_class action
provenance: {source: authored|ai_authoring, model: null, prompt_version: null, reviewed_by: null, date: null}
```

Mỗi giá trị có metadata: `meaning_key`, `voice`, `tags`, `length`, `grammar` (loại từ, trợ từ cuối câu).
Giá trị do AI lúc soạn tạo ra phải có `provenance` đầy đủ (plan §14.3).

## 3. Build (CI)

1. **Liệt kê** mọi tổ hợp của từng khung × bucket, áp `constraints`.
2. **Ghép và chuẩn hoá:** NFC, khoảng trắng, dấu câu, viết hoa đầu câu.
3. **Gate từng câu:** meaning, anti-influence, editorial, nudge checker (với lời của Lá), các mục kiểm máy
   được của checklist tâm lý, cụm bị cấm (`BANNED_CORE_FRAGMENTS`).
4. **Khử trùng** câu sau chuẩn hoá, trong từng khung và giữa các khung cùng surface.
5. **Allowlist** = các tổ hợp qua bước 3–4.
6. **Lịch chủ:**
   - Tìm chu trình khép kín dài L trên tổ hợp chủ có trong allowlist của **mọi** bucket. Một tổ hợp chủ chỉ
     vào lịch khi với mọi bucket đủ điều kiện, ghép với ít nhất một giá trị ô theo bucket đều qua gate.
   - Hai phần tử kề nhau, kể cả cặp cuối → đầu, khác nhau ở mọi ô bắt buộc đổi. Mỗi giá trị của ô bắt buộc
     đổi có mặt ít nhất một lần.
   - Tìm kiếm tất định, có giới hạn bước. Dựng tối đa M biến thể.
7. **Ghép toàn bài:**
   - Kiểm **tách từ vựng**: khung `headline`/`scene` không chứa giá trị thuộc `vocab_class: action`.
   - Kiểm **phân vai**: mỗi tập khung của một bài có đúng ≤ 1 khung `negative_role: true`.
   - Quy tắc nào không đưa được vào cấu trúc thì dựng lịch ghép chung và kiểm đủ L vị trí.
8. **Cà khịa:** mọi mã tổ hợp direct có ánh xạ tới một tổ hợp roast cũng nằm trong allowlist.
9. **Manifest:** `catalog_version`, `composer_version`, `gate_version`, `spec_version`; hash của từng
   allowlist và từng biến thể lịch; L, M, số bucket, số tổ hợp.

**Từ chối build (CI đỏ) khi:**

- không dựng được lịch với L ≥ 90 (hoặc ngưỡng owner chốt);
- vi phạm tách từ vựng hoặc phân vai;
- thiếu ánh xạ Cà khịa;
- vượt giới hạn ở §4;
- còn cụm bị cấm trong allowlist.

Ngoại lệ duy nhất là ngoại lệ đã review, khai báo trong manifest (ví dụ hạ một ô xuống "được lặp").

## 4. Giới hạn (đề xuất, owner và Codex chốt ở P0)

| Giới hạn | Giá trị đề xuất |
|---|---|
| Tổ hợp tối đa mỗi khung × bucket (trước gate) | 200 000; vượt thì tách khung |
| Bucket tối đa mỗi khung | 48 |
| Bước tìm kiếm tối đa mỗi biến thể lịch | 2 000 000 |
| Biến thể lịch M mỗi khung | 4–8 |
| L tối thiểu | 90 |
| Thời gian CI cho toàn bộ build ngữ pháp | ≤ 10 phút trên runner hiện có; vượt thì cache theo hash của khung |

## 5. Runtime

- `seed = HMAC(K[v], owner_scope ‖ surface ‖ catalog_version)`. Seed chọn biến thể lịch và `offset`.
- **Daily:** `p = (day_index + offset) mod L`. Ngày lịch và `day_index` theo US-21 (MVP_TIMEZONE).
- **Tarot:** vị trí theo phiên (mã phiên và thứ tự vai), chọn một lần lúc rút.
- **Hợp gu:** vị trí theo mã kết quả, chọn một lần khi tạo kết quả.
- Mọi khung của một bài dùng cùng `p` và cùng L. Ô theo bucket lấy theo bucket của ngày đó.
- **Không chọn lại lúc chạy.** `evaluate_candidate` chỉ là lưới an toàn.
- Lựa chọn hoàn tất **trước** `plan_hash` và persist. Provenance ghi `catalog_version`, biến thể lịch, `p`,
  bucket, `variant_key_version`.
- **Ngoại lệ:** khi gate an toàn từ chối hoặc manifest hỏng/thiếu:
  - phục vụ kho nền, ghi `variety_exception = {reason, catalog_version}` (không có dữ liệu cá nhân);
  - tăng counter tổng hợp theo khung và phiên bản;
  - ngày sau dùng `p` danh nghĩa.

## 6. Cam kết (trên output thật được phục vụ)

- **(a)** Hai ngày lịch liên tiếp của cùng khung, cùng `catalog_version` và biến thể lịch, đều không ngoại
  lệ, thì khác nhau ở mọi ô bắt buộc đổi, kể cả khi đổi bucket và ở biên lịch.
- **(b)** Cùng một câu (sau chuẩn hoá) không được phục vụ lại cho cùng người trong L ngày lịch, không tính
  ngày ngoại lệ.
- **(c)** Mỗi giá trị ô bắt buộc đổi có trong mỗi lịch chủ.
- **Không cam kết:**
  - khoảng cách giữa hai lần dùng cùng một giá trị ô;
  - ô theo bucket không lặp;
  - câu tự nhiên hay đúng nghĩa ("100% trong allowlist" chỉ chứng minh độ phủ của kiểm tra máy; owner vẫn
    đọc mẫu).
- **Replay:** cùng `(owner_scope, surface, ngày hoặc phiên, catalog_version, manifest)` thì trả đúng bản đã
  tạo. Mở lại nhiều lần trong cùng ngày không phải "hai ngày liên tiếp".

## 7. AC kiểm ở G0/G1 (gồm AC 1–7 của plan §14.2)

| # | Tình huống | Kỳ vọng |
|---|---|---|
| G-AC1 | Ép gate từ chối ngày D (phản ví dụ của Codex) | D là ngoại lệ, có cờ; D+1 ở `p` danh nghĩa; không câu nào phục vụ hai lần trong L ngày (không tính cặp ngoại lệ) |
| G-AC2 | Đổi bucket giữa D và D+1, ở mọi `p` và mọi cặp bucket có thể kề nhau trong fixture | (a) và (b) giữ |
| G-AC3 | D ở `p = L−1`, D+1 ở `p = 0` | (a) giữ |
| G-AC4 | Cấu hình vi phạm tách từ vựng, phân vai, thiếu Cà khịa, vượt giới hạn, hoặc lịch không khả thi | CI đỏ |
| G-AC5 | Manifest hỏng hoặc thiếu | Kho nền, có cờ và counter; không ghép tự do |
| G-AC6 | Đổi giọng; replay sau cache miss hoặc restart; chia sẻ | Cùng mã tổ hợp, không chạy lại lịch |
| G-AC7 | Báo cáo | Chỉ số tính trên output cuối; có số lượt và tỷ lệ ngoại lệ, tỷ lệ vi phạm (a)/(b), theo nhóm |
| G-AC8 | Direct và Roast | (a)/(b)/(c) đúng cho cả hai giọng |
| G-AC9 | Phản ví dụ allowlist `{(0,0,0),(0,1,1),(1,0,1)}` | Build từ chối |

## 8. Duyệt của owner

- Owner duyệt **giá trị ô** và **mẫu ghép** (khoảng 30 tổ hợp mỗi khung, chọn tất định, gồm tổ hợp biên)
  qua Excel, cả hai giọng.
- Tách từ vựng không thay cho kiểm trùng ý và meaning, cũng không thay cho owner đọc mẫu.
