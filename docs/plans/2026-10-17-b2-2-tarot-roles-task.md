# Task B2-2 — Tarot T2: nghĩa theo vai và dọn chữ thừa

> Nguồn đã duyệt:
> - `docs/plans/2026-10-16-personalisation-variety-plan.md` §3 và §6 bước 5 (B2-2 = nghĩa theo vai, dọn chữ
>   thừa);
> - `docs/user-stories/US-20-tarot-tra-loi-dung-cau-hoi.md` AC07, AC12, AC13 (và phần AC17 cho phiên cũ).
>
> Stacked trên B2-1 (PR #23, APPROVE @ `9c28725`).

## Phạm vi

**Làm:**

1. **Vai của từng vị trí** (`tarot/roles.py`). Mỗi vị trí trong `_POSITIONS` có một vai. Vai quyết định
   trường dữ liệu của lá được đọc ở đó, khung câu bao quanh, và vị trí có việc nhỏ hay không.

   | Trường | Vị trí |
   |---|---|
   | `core` (điều đã có) | `clear`, `facts`, `need`, `trigger`, `payoff`, `feeling` |
   | `tension` (điểm vướng) | `missed`, `assumption`, `habit`, `cost`, `tradeoff` |
   | `option` (được / giá) | `option_a`, `option_b` |
   | `resource` (phần làm được) | `agency`, `boundary` |
   | **Vai bước tiếp** (có việc nhỏ) | `focus`, `next`, `alternative`, `criterion`, `opening`: việc nhỏ lấy từ hành động theo mục tiêu (nếu khớp) hoặc từ `resource` của lá |

   - Trải 3 lá: "Điều đã rõ" đọc `core`; "Điều dễ bỏ sót" đọc `tension`; "Một bước nhỏ có thể thử" đọc
     `resource`, ra việc nhỏ (AC07).
   - Không còn nhánh chung "Ý chính của lá: …".
   - **Việc nhỏ chỉ ở vai bước tiếp.** Mỗi trải bài có đúng một vai như vậy. `small_action` của các vị trí khác
     là `null`.
2. **Dọn chữ thừa (AC12):**
   - không còn "Ý chính của lá:", "Ý chính:", "Thử nhé:", "Một việc nhỏ:";
   - cảnh không mở đầu bằng "Ví dụ:" nữa, vì giao diện đã có nhãn "Ví dụ để đối chiếu";
   - web: tên lá tiếng Anh và dòng "Engine …" chuyển vào khối thu gọn "Chi tiết kỹ thuật";
   - khối "Một việc bạn có thể thử" chỉ hiện khi vị trí có việc nhỏ.
3. **Gate (AC13):**
   - **Bỏ mức tối thiểu số chữ cho Tarot** (cảnh ≥ 12, việc nhỏ ≥ 6) trong `ContentReviewAgent`. Vẫn giữ
     marker quan sát được hoặc làm được, trần độ dài và mọi bộ lọc an toàn. Daily và natal không đổi.
   - **`role_fit`**: mỗi vị trí đọc đúng trường của vai; chỉ vai bước tiếp có việc nhỏ (và bắt buộc có);
     không còn tiền tố thừa.
   - **`no_decision_or_prediction`**: không quyết thay ("bạn nên chọn", "hãy chọn hướng A"), không đoán
     ("rồi sẽ thành công", "anh ấy sẽ"). Chỉ quét phần chữ do engine viết. Trường lá và cảnh ví dụ đã duyệt
     được bỏ qua, vì một điểm vướng có thể nhắc nỗi sợ "chắc sẽ xảy ra" mà bài đọc không hề dự đoán.
   - Hai gate mới chỉ áp cho bài đọc có frame (B2-1 trở đi). `gate_version = tarot-gates-v5` cho bài đọc
     đó.
4. **Tương thích:**
   - Phiên không có frame (bắt đầu trước B2-1) đi **đúng đường render cũ**, giữ `gate_version` v4, giống
     từng byte.
   - Có test golden cho 36 bài đọc, khớp hash tính trên head đã duyệt `9c28725`.
   - Bài đọc v6 đã lưu (mọi vị trí có việc nhỏ) vẫn validate và hiển thị.
5. **Contract:** `small_action` thành `string | null` (tuỳ chọn) trong OpenAPI, contracts TS và client web.
   - Payload Luna (vẫn tắt) gửi `null` cho vị trí không có việc nhỏ.
   - Không thêm trường; canary câu hỏi vẫn không lọt vào payload.
6. **Audit:** `pnpm tarot:audit` chạy cả hai đường render (cũ và theo vai) trên 11 232 + 14 976 trải bài
   tổng hợp × 4 giọng. Cả hai đều đạt.

**Không làm (B2-3/B2-4):**

- Hướng nghiêng, tóm tắt nối vai, tiêu đề động, gate `summary_links_cards` (AC08–AC11).
- Ba khung câu mỗi vai theo salt phiên và ví dụ 2–3 cảnh (AC15, AC16).
- Cà khịa đầy đủ cho khung vai (AC19). Bài theo vai dùng lại đuôi và khung việc nhỏ Cà khịa hiện có.
- Renderer v7, knowledge v5, brief v3 (AC18).
- Schema payload Luna có mã nguồn gốc (AC06 phần còn lại).

## Ánh xạ AC

| AC | Trạng thái | Bằng chứng |
|---|---|---|
| AC07 | Xong | `test_ac07_*` (3 lá; mọi map × 4 giọng có đúng một vai bước tiếp và đọc đúng trường), audit đường theo vai |
| AC12 | Xong cho engine và web | `test_ac12_*`; web `TarotPage.test.tsx` ("Chi tiết kỹ thuật", không có khối việc nhỏ ở vai không phải bước tiếp) |
| AC13 | Xong: bỏ mức tối thiểu, gate `role_fit` và `no_decision_or_prediction` | `test_ac13_*` |
| AC17 | Phần render: phiên không frame giống từng byte; v6 đã lưu vẫn hiển thị | `test_sessions_without_a_frame_render_byte_identically`, `test_a_stored_v6_reading_still_validates` |
| AC14 | Chưa: checklist tâm lý cho cả bài cần owner đọc mẫu | — |

## Nội dung mới cần owner duyệt

1. **21 khung câu theo vai** trong `tarot/roles.py` (`ROLES`). Ví dụ:
   - "Lá này cho thấy {core}."
   - "Điều dễ trượt qua: có thể bạn đang {tension}."
   - "Điều cần tính tới khi bước tiếp: {core}."
   - "Phần nằm trong tay bạn: {resource}."
   - "Hướng này mang lại: {core}. Cái giá cần tính: dễ {tension}."
   - "Ranh giới có thể nói rõ: {resource}."
2. **Việc nhỏ** của vai bước tiếp: câu `resource` của lá, viết hoa đầu câu, **bỏ** tiền tố "Thử nhé:" /
   "Một việc nhỏ:". Nội dung lá không đổi.
3. **Cảnh** bỏ tiền tố "Ví dụ:" / "Ví dụ: Có lần" → "Có lần …". Nội dung cảnh không đổi.
4. **Web:** nhãn "Chi tiết kỹ thuật" và "Tên lá gốc: …".
5. 3 câu "sẵn sàng" từ B2-1 vẫn chờ duyệt.

`docs/operations/fallback-approval.json` **không đổi**, vì các bảng đã ghim không đổi:
- luật gate mới đặt trong `tarot/roles.py`, không trong `engine.py`;
- khi phát hành B2, sau khi owner duyệt, thêm `tarot/question_frame.py` và `tarot/roles.py` vào phạm vi phê
  duyệt rồi làm mới file.

## Bảo mật và riêng tư

- Không có endpoint, bảng hay dữ liệu cá nhân mới.
- Payload Luna chỉ bớt nội dung (`small_action` có thể `null`); không thêm trường nào.
- Frame và câu hỏi vẫn chỉ nằm trong payload AES-GCM.
- Không cần đổi data map hay khai báo store.
