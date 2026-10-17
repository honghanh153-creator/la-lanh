# Task B2-1 — Tarot T2: hiểu câu hỏi (`QuestionFrame`)

> Nguồn đã duyệt:
> - `docs/plans/2026-10-16-personalisation-variety-plan.md` §3 và §6 bước 5 (bảng: B2-1 = hiểu câu hỏi);
> - `docs/user-stories/US-20-tarot-tra-loi-dung-cau-hoi.md` AC01–AC06;
> - quyết định owner T2 (khi nào → sẵn sàng trước), A6 (30 nhãn hành động), A7 (câu mơ hồ),
>   `docs/plans/2026-10-16-p0-owner-decisions.md`;
> - ngân hàng câu hỏi tổng hợp `docs/fixtures/tarot-question-bank-v1.json`.
>
> Stacked trên G0 (PR #22, APPROVE @ `23d1d53`).

## Phạm vi

**Làm:**

1. **`QuestionFrame`** (`tarot/models.py`, logic ở `tarot/question_frame.py`). Model `extra="forbid"`,
   chỉ chứa nhãn đóng:
   - `form ∈ {yes_no, choice, how, why, timing, open}` (AC01);
   - `topic`: chấm điểm nhiều tín hiệu theo từng chủ đề, cộng ưu tiên 1,5 cho chủ đề người dùng chọn; hoà
     thì giữ chủ đề đã chọn. "hỏi" không phải tín hiệu của chủ đề giao tiếp (AC02);
   - `action`: một trong 30 nhãn đóng của US-20/A6.
     - Tín hiệu bị phủ định **trong chính mệnh đề của nó** bị loại trước khi xếp hạng, gồm phủ định trực
       tiếp ("không xin lỗi") và có trợ động từ chen giữa ("không cần phải xin lỗi").
     - Sau đó tín hiệu dài nhất thắng, rồi tới thứ tự bảng.
     - Không còn hành động được khẳng định nào thì `None`, không đoán.
2. **Bộ lọc nhận câu hỏi**, giữ thứ tự AC03: quá ngắn hoặc mơ hồ → rủi ro cao → đoán ý người khác → đòi
   chắc chắn.
   - **Mơ hồ (A7, AC04):** dưới 3 từ, hoặc không có từ để hỏi lẫn động từ nào. "Tình yêu và công việc" bị
     hỏi lại; "Vì sao mình hay im lặng trong các cuộc họp?" được nhận. Câu `edge.7` vẫn được nhận.
   - **Khi nào (T2, AC05):** bỏ "khi nào/bao giờ" khỏi bộ lọc chắc chắn.
     - Câu hỏi thời điểm về **việc của chính mình** được nhận và trả lời theo hướng điều cần sẵn sàng
       trước. Chủ thể được xác định **trong chính mệnh đề được hỏi giờ**, không tìm "nên" hay "để mình" ở
       bất kỳ đâu trong câu:
       - cụm thời gian mở đầu câu: lấy chủ thể ngay sau nó (bỏ qua "thì / là lúc phù hợp để");
       - cụm thời gian ở giữa hoặc cuối câu: lấy chủ thể ở đầu câu;
       - chủ thể phải là ngôi thứ nhất (hoặc người đọc ngầm định trước "nên"), và vị ngữ phải là một hành
         động, không phải kết quả ("có", "sẽ", "được", "bị", …).
     - Câu hỏi thời điểm về sự kiện hoặc người khác ("Khi nào mình có người yêu?", "Bao giờ người ấy nhắn
       lại?") vẫn bị từ chối như đòi chắc chắn.
     - "chắc chắn", "có quay lại", "sẽ xảy ra" vẫn bị từ chối.
3. **Bài đọc cho câu `timing`:**
   - tiêu đề "điều cần sẵn sàng trước", có bản direct và bản Cà khịa;
   - mở đầu phần tóm tắt bằng một dòng giải thích vì sao không đoán thời điểm.

   Các câu dạng khác hiển thị y như trước. Nghĩa theo vai, hướng nghiêng và tiêu đề động thuộc B2-2/B2-3.
4. **Đóng băng và replay:**
   - frame tính **một lần** lúc bắt đầu phiên, lưu trong payload AES-GCM (`question_frame`,
     `question_rules_version = tarot-question-rules-v2`);
   - lúc render dùng frame đã lưu, không tính lại;
   - kiểm câu mơ hồ chỉ chạy lúc nhận câu hỏi; render chỉ chạy lại ranh giới an toàn, nên phiên nhận theo
     luật cũ vẫn render được;
   - phiên bắt đầu trước B2-1 (không có frame) render theo **ranh giới v1** (`_CERTAINTY_V1` giữ nguyên
     văn), `question_rules_version` v1. Câu v1 đã nhận nhưng v2 từ chối, như "Lúc nào mình có người
     yêu?", vẫn ra bài đọc cho lượt rút đang dở (AC17, phần của B2-1).
5. **Riêng tư (AC06):**
   - frame không vào API (view không có trường này), không log, không gửi provider;
   - payload Luna **không đổi**, B2-1 không thêm trường nào;
   - có test canary đi qua toàn đường: phiên → render → meaning brief → payload rewrite → log. Kết quả:
     không có token canary, cũng không có cụm 2 từ liền nào của cụm riêng tư tổng hợp.
6. **Đo:** `pnpm tarot:audit` chạy toàn ngân hàng câu hỏi:
   - độ đúng của dạng câu, sàn 95%;
   - chấp nhận và từ chối đúng kỳ vọng;
   - ca biên đúng chủ đề;
   - mọi câu `timing` có dòng sẵn sàng;
   - độ phủ nhãn hành động.

**Không làm (B2-2…4):**

- Nghĩa theo vai, dọn chữ thừa: AC07, AC12, AC13.
- Hướng nghiêng, nhãn `lean`, tóm tắt nối vai, tiêu đề động, khung câu đa dạng theo ngữ pháp: AC08–AC11,
  AC14–AC16.
- Cà khịa đầy đủ, phiên bản renderer v7 / gates v5 / knowledge v5 / brief v3, Luna: AC18–AC19.
- Tách A/B thành nhãn đóng cho `choice`: AC08, thuộc B2-3.
- **Schema payload Luna có mã nguồn gốc cho từng chuỗi** (phần "kiểm nguồn gốc" của AC06): B2-4. B2-1 chỉ
  chứng minh câu hỏi không lọt vào payload hiện tại, qua canary.
- `TarotQuestionIntent` giữ nguyên, kể cả việc "hỏi" kéo intent sang giao tiếp, để B2-1 không đổi nội dung
  hiển thị ngoài câu `timing`. Intent sẽ thay bằng vai ở B2-2.

## Kết quả đo (dữ liệu tổng hợp)

| Chỉ số | Kết quả |
|---|---|
| Dạng câu đúng trên 289 mục có nhãn (AC01) | **100%** (sàn 95%), cộng 8 câu giữ ngoài ngân hàng |
| Ca biên đúng chủ đề (AC02) | **8/8** |
| Mục từ chối (AC03) | **32/32** bị từ chối, có gợi ý hỏi lại. `reject.certainty.8` ("Họ có quay lại …") bị bộ lọc đoán người khác bắt trước, đúng thứ tự, như trước B2-1 |
| `too_vague` (AC04) | **8/8** được hỏi thêm tình huống (trước: 2/8); 296 câu hợp lệ không bị bắt nhầm |
| `timing` (AC05) | **49/49** được nhận và có dòng sẵn sàng; câu dự đoán vẫn bị từ chối |
| Nhãn hành động | 164/296 câu khớp một nhãn, 29/30 nhãn được dùng |

## Ánh xạ AC

| AC | Trạng thái | Bằng chứng |
|---|---|---|
| AC01 | Xong | `test_ac01_*`, `pnpm tarot:audit` |
| AC02 | Xong | `test_ac02_*` |
| AC03 | Xong | `test_ac03_*` |
| AC04 | Xong | `test_ac04_*` |
| AC05 | Xong cho phần hiểu câu hỏi và một dòng giải thích; khung câu "sẵn sàng" phong phú hơn thuộc B2-3 | `test_ac05_*` |
| AC06 | Một phần: frame chỉ ở payload mã hoá, không API, không log, không provider; canary qua toàn đường. Schema có nguồn gốc từng chuỗi thuộc B2-4 | `test_ac06_*` |
| AC17 | Một phần: phiên cũ không có frame render như trước | `test_sessions_started_before_b2_1_render_as_before` |

## Duyệt và phát hành

- **Copy mới cần owner duyệt trước khi phát hành:**
  - 2 tiêu đề sẵn sàng (direct, Cà khịa);
  - 1 dòng giải thích.

  Cả ba nằm ở `tarot/question_frame.py`.
- `docs/operations/fallback-approval.json` **chưa** làm mới: các bảng đã ghim không đổi, nên
  `pnpm grammar:check` vẫn đạt. Khi phát hành B2, owner duyệt rồi thêm `tarot/question_frame.py` vào phạm vi
  phê duyệt và làm mới file. Không tự làm mới khi chưa có duyệt.
- Không đổi renderer version (v6), vì đó là trường đã ghim. Bump v7 khi phát hành B2 (AC18).

## Sửa theo review Codex @ `8ecf5c4` (3 P2)

| P2 | Sửa | Regression (fail trên `8ecf5c4`, pass bây giờ) |
|---|---|---|
| 1. Phiên v1 bị luật timing mới từ chối lúc render, nên lượt rút xong mà không có bài đọc | Render chọn ranh giới theo phiên bản: không có frame thì dùng ranh giới v1 nguyên văn | `test_p2_1_sessions_started_before_b2_1_keep_the_v1_boundary` qua service với payload v1 ("Lúc nào mình có người yêu?", "Bao lâu nữa dự án này xong?"); `test_p2_1_the_v1_boundary_is_the_released_rule` |
| 2. Ngoại lệ timing chỉ tìm "nên"/"để mình" | Xác định chủ thể và vị ngữ trong mệnh đề được hỏi giờ | `test_ac05_predictions_stay_rejected` (người khác dù có "nên", sự kiện có mệnh đề mục đích ngôi thứ nhất, kết quả); `test_p2_2_own_actions_are_reframed_with_or_without_nen`; `test_p2_service_*` |
| 3. Hành động bị phủ định vẫn được đóng băng | Phủ định theo mệnh đề, có trợ động từ, loại trước khi xếp hạng | `test_p2_3_a_negated_action_is_never_frozen` (frame đầy đủ); `test_p2_3_negation_stays_in_its_clause`; `test_p2_service_freezes_owner_timing_and_affirmed_actions` (frame đã lưu) |

Trên ngân hàng câu hỏi chỉ một nhãn đổi: "Điều gì mình **chưa nói ra** …" từ `noi_ra` thành `None`. Câu này
hỏi về điều chưa nói, không phải một hành động được khẳng định.

## Bảo mật và riêng tư

- Không có endpoint, bảng hay cột mới. Frame là dữ liệu suy ra từ câu hỏi:
  - nằm trong cùng payload AES-GCM của phiên;
  - hết hạn và bị xoá cùng phiên (≤ 29 ngày 18 giờ);
  - không log, không vào API, không gửi provider.
- Data map có thêm một dòng.
- Regex chỉ dùng mẫu phẳng trên câu tối đa 280 ký tự (giới hạn hiện có), không có regex lồng nhau.
