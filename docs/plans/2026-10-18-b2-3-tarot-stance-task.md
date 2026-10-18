# Task B2-3 — Tarot T2: hướng nghiêng, tóm tắt nối vai, tiêu đề động

> Nguồn đã duyệt:
> - `docs/plans/2026-10-16-personalisation-variety-plan.md` §3 và §6 bước 5 (B2-3);
> - `docs/user-stories/US-20-tarot-tra-loi-dung-cau-hoi.md` AC08–AC11 (và phần AC17 cho phiên cũ);
> - ngân hàng câu hỏi `docs/fixtures/tarot-question-bank-v1.json`: `yes_no → lean`,
>   `choice → choice_compare_or_clarify`.
>
> Stacked trên B2-2 (PR #24, APPROVE @ `19bd2d1`).

## Phạm vi

**Làm** (chỉ cho phiên có `QuestionFrame` đã lưu; phiên cũ giữ renderer cũ, giống từng byte):

1. **Nhãn `lean` (AC09)** trong `tarot/stance.py`:
   - mỗi lá có một nhãn mặc định `open` (mở), `hold` (giữ) hoặc `two_sided` (hai mặt);
   - chỉ ghi đè theo chủ đề khi khác mặc định;
   - tổng ≤ 468 nhãn: 78 mặc định cùng một số ghi đè.
2. **Hướng nghiêng (AC08, AC09):** chỉ cho câu `yes_no` và câu `choice` tách được A/B.
   - Điểm = Σ trọng số vai × giá trị nhãn, với `open = +1`, `hold = −1`, `two_sided = 0`.
   - Trọng số: vai bước tiếp 2; vai `core`/`resource`/`option` 1; vai `tension` 0,5, vì vai này mô tả rủi ro
     chứ không chỉ hướng.
   - **Ba mức**, không có mức "nghiêng về chưa nên":
     - điểm ≥ 1: "Các lá nghiêng về thử {action}";
     - điểm ≤ −1: "Các lá gợi ý cân nhắc thêm trước khi {action}";
     - còn lại: "Chưa rõ: các lá kéo về hai phía".
   - `{action}` là cụm động từ đã duyệt của nhãn hành động đóng trong frame. Không có nhãn thì dùng cụm
     chung "làm điều bạn đang cân nhắc".
   - **1–2 lý do**, mỗi lý do trỏ tới nhãn vị trí, tên lá và nội dung lá (trường của vai). Lý do được chọn
     từ các vị trí đóng góp nhiều nhất theo hướng kết quả; mức "chưa rõ" lấy một lý do mỗi phía nếu có.
   - **Câu `choice`:**
     - tách A/B ("Nên A hay B", "Giữa A và B"), mỗi phía phải ra một nhãn hành động đóng khác nhau;
     - nếu tách được và trải bài có vai `option_a`/`option_b` (map `five_choice`): so nhãn hai lá →
       "nghiêng về thử {A}", "nghiêng về thử {B}" hoặc "chưa rõ";
     - các trường hợp khác (không tách được, hoặc trải 1/3 lá không có vai hai hướng): khối **"Điều cần rõ
       trước khi chọn"**, không đưa hướng nghiêng.
   - Câu dạng khác (how/why/open/timing): không có khối hướng nghiêng.
   - Model: `TarotReading.stance` tuỳ chọn, gồm mức, nhãn hành động (enum đóng), câu kết luận và lý do (mã
     vị trí, mã lá, câu). Phiên cũ có `stance = null`.
3. **Tóm tắt nối các vai (AC10):** mỗi vai góp một câu theo thứ tự vị trí, nối bằng liên từ theo kiểu
   chuyển:
   - sang vai `tension`: "Nhưng" / "Có điều";
   - sang vai bước tiếp hoặc `resource`: "Vì vậy," / "Từ đó,";
   - sang vai `core`/`option`: "Bên cạnh đó," / "Thêm nữa,".

   Anchor của mỗi vai là trường lá của vai đó. Dòng mục tiêu và dòng "sẵn sàng" (B2-1) vẫn đứng đầu khi vừa
   ngân sách 180 chữ.
4. **Tiêu đề động (AC11):**
   - dựng từ dạng câu, kèm hướng nghiêng (yes_no/choice) hoặc hành động / chủ đề, và lá trọng tâm (lá ở vai
     bước tiếp);
   - how / why / open và "điều cần rõ" ghép thêm lá thứ hai, ưu tiên lá ở vai `tension`;
   - câu `timing` (giọng thẳng) giờ cũng là tiêu đề động: "{lá trọng tâm}: điều cần sẵn sàng trước khi
     {action}". Vẫn giữ ý sẵn sàng của AC05, và dòng giải thích của B2-1 vẫn đứng đầu tóm tắt. Test B2-1
     được cập nhật theo;
   - trần 18 chữ giữ nguyên;
   - giọng Cà khịa giữ tiêu đề Cà khịa hiện có (kể cả tiêu đề sẵn sàng của B2-1); bản Cà khịa của tiêu đề
     động thuộc B2-4 (AC19).
5. **Gate:**
   - **`stance_consistent` (AC09):** mức hướng nghiêng tính lại từ các lá phải khớp `stance`. Tiêu đề phải
     mang đúng cụm của mức đó; tóm tắt và tiêu đề không được chứa cụm của mức khác.
   - **`summary_links_cards` (AC10)** thay gate "tóm tắt nêu tên mọi lá" cho bài đọc có frame: mỗi vai có
     anchor trong tóm tắt, và có ít nhất N−1 liên từ.
6. **Contract:** `stance?` tuỳ chọn trong OpenAPI, TS và client web.
   - Web có khối "Hướng nghiêng" (thẻ "Tím đêm dịu") khi có `stance`, khối "Điều cần rõ trước khi chọn" khi
     mức là `clarify_choice`.
   - Payload Luna **không thêm** trường `stance` (B2-4); chỉ phần tóm tắt cục bộ đổi nội dung.
7. **Đo (AC11):** `pnpm tarot:audit` chạy ngân hàng câu hỏi × mọi map × 3 giọng thẳng (seed cố định), báo:
   - phân bố hướng nghiêng;
   - tỷ lệ tiêu đề trùng, mục tiêu < 10%;
   - số câu chung chung còn sót, phải bằng 0.

**Không làm:**

- 3 khung câu mỗi vai theo salt phiên, thêm cảnh ví dụ (AC15, AC16).
- Cà khịa cho tiêu đề, hướng nghiêng, liên từ (AC19).
- Renderer v7, knowledge v5, brief v3 (AC18).
- Schema payload Luna có mã nguồn gốc (AC06).

## Ánh xạ AC

| AC | Trạng thái | Bằng chứng (`tests/tarot/test_stance.py`, audit) |
|---|---|---|
| AC08 | Xong | `test_ac08_three_levels_*` (ba mức, 1–2 lý do trỏ vai + lá, không có "chưa nên"); `test_ac08_choice_*` (so ở map hai hướng, hoà thì "chưa rõ", trải 3 lá hoặc không tách được thì "điều cần rõ"); `test_ac08_other_forms_*` |
| AC09 | Xong | `test_ac09_every_card_has_a_lean_*` (78 lá + 3 ghi đè ≤ 468; trọng số vai); `test_ac09_stance_consistent_*` |
| AC10 | Xong | `test_ac10_summary_mentions_every_role_*` (mọi map); `test_ac10_gate_rejects_*` |
| AC11 | Xong: tỷ lệ tiêu đề trùng **4,45%** mỗi giọng thẳng (T2 của spec đo §4c, chuẩn hoá, riêng từng giọng; 1 776 bài mỗi giọng), 0 câu chung chung | `pnpm tarot:audit`; `test_ac11_*` |
| AC17 | Xong phần render: phiên cũ giống từng byte; bài đọc không có hướng nghiêng **bỏ hẳn khoá `stance`** khi serialize (`Field(exclude_if=…)`), nên byte lưu và byte API không đổi | golden trong `test_roles.py`; `test_ac08_other_forms_have_no_stance_and_omit_the_key` |

**Phân bố hướng nghiêng** trên ngân hàng × 6 map × 3 giọng (5 328 bài): `lean_try` 489, `consider` 210,
`unclear` 273, `clarify_choice` 864, không có hướng nghiêng (how/why/open/timing) 3 492.

**Giới hạn cần owner biết:** chỉ **11/48** câu `choice` trong ngân hàng tách được A/B thành hai nhãn hành
động đóng. Phần lớn lựa chọn không phải hành động ("lớp buổi sáng hay lớp buổi tối", "cho gia đình hay cho
bạn bè"). Đúng theo AC08, các câu này ra "Điều cần rõ trước khi chọn". Nếu owner muốn so cả những câu này,
có thể thêm nhãn đóng theo vị trí ("hướng bạn nêu trước / nêu sau") mà không chép chữ của câu hỏi. Đó là một
quyết định riêng, chưa làm ở đây.

## Nội dung mới cần owner duyệt

- **78 nhãn `lean` mặc định và 3 ghi đè** (`LEAN_DEFAULTS`, `LEAN_OVERRIDES` trong `tarot/stance.py`).
- **30 cụm hành động** cho `{action}`, cùng cụm chung "làm điều bạn đang cân nhắc".
- **4 câu kết luận** (ba mức và "điều cần rõ").
- **Khung lý do**, theo mẫu "{nhãn vị trí}: {lá} cho thấy / nhắc rằng bạn dễ / gợi ý bạn có thể …".
- **Tóm tắt:**
  - khung câu theo vai ("{lá} cho thấy …", "{lá} nhắc rằng bạn dễ …", "{lá} gợi ý bạn có thể …", "{lá}:
    hướng này được …", "Đổi lại, hướng này dễ …");
  - 6 liên từ: "Nhưng", "Có điều,", "Vì vậy,", "Từ đó,", "Bên cạnh đó,", "Thêm nữa,".
- **8 khung tiêu đề động** và 6 cụm chủ đề.
- **Web:** nhãn "Hướng nghiêng" và "Điều cần rõ trước khi chọn", nằm trong thẻ đêm của phần tóm tắt (mỗi màn
  một thẻ đêm, đúng hệ "Tím đêm dịu").
- Các nội dung B2-1 và B2-2 vẫn đang chờ duyệt.

`docs/operations/fallback-approval.json` không đổi, vì các bảng đã ghim không đổi (`tarot/stance.py` là
module mới). Khi phát hành B2, thêm `question_frame.py`, `roles.py`, `stance.py` vào phạm vi phê duyệt sau
khi owner duyệt.

## Sửa tài liệu theo review B2-2 (Codex @ `19bd2d1`)

- `ROLES` có **20** mục, không phải 21.
- API trả `small_action: null`; payload gửi provider **bỏ hẳn key null** (privacy minimiser), không gửi
  `null`.
