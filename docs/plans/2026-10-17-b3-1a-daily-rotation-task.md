# Task B3-1a (A1) — xoay vòng riêng cho note ngày

> Nguồn đã duyệt: `docs/plans/2026-10-16-personalisation-variety-plan.md` §2.2–2.3 và §6 bước 3;
> `docs/user-stories/US-21-note-ngay-rieng-va-doi-moi-ngay.md` AC01–AC06;
> `docs/foundation/la-lanh-content-grammar-spec.md` §5; quyết định owner
> `docs/plans/2026-10-16-p0-owner-decisions.md` (A1–A12, chốt 16/10). Làm trước G0.

## Phạm vi

**Làm trong task này:**

1. **Seed theo người, không chứa ngày:** `seed = HMAC(K[1], profile_id ‖ "daily" ‖ catalog_version)`.
   - `catalog_version` = `DAILY_PSYCHOLOGY_MATRIX_VERSION`.
   - `K[1] = HMAC(guest_hash_key, "la-lanh/variety-salt/v1")`: khoá chỉ dùng để chọn biến thể, tách miền
     khỏi secret gốc, không cần secret mới trên server.
2. **Chu kỳ riêng cho từng trục** (tiêu đề 6, cảnh 8, hành động 8):
   - vị trí `day_index mod n`, với `day_index = local_date − 2026-01-01` theo `Asia/Ho_Chi_Minh`;
   - mỗi chu kỳ là một hoán vị Fisher–Yates mới, sinh từ `seed ‖ trục ‖ cycle_no` bằng chuỗi sha256
     (không dùng `random` của Python);
   - luật biên: phần tử đầu của chu kỳ mới khác phần tử cuối chu kỳ trước, nếu trùng thì đổi chỗ phần tử
     0 và 1; trục 2 giá trị thì xen kẽ; trục 1 giá trị thì đứng yên.
3. **Top-K tình huống (K = 3):**
   - giữ tình huống mạnh nhất của mỗi issue;
   - xếp theo điểm, hoà thì theo mã;
   - chọn `day_index mod K`.
4. **Guard:** không quá 2 ngày liền cùng tình huống khi pool có ít nhất 2 phần tử.
   - Đọc issue đã thực sự phục vụ ở D−1 và D−2 từ projection và revision đang lưu, qua `get_projection`
     và `get_revision` sẵn có. Không thêm bảng.
   - Đọc theo đúng scope của ngày đó (cùng lens, cùng cấu hình lá số). Ngày người dùng không mở app, hoặc
     mở với lens khác, thì dừng đọc lịch sử ở đó, nên guard không áp cho ngày hôm sau.
   - Revision do AI sinh (đang tắt) nếu thiếu `semantic_blueprint` cũng dừng ở đó.
5. **Đóng băng trước khi hash:** `DailyVariety` (`key_version`, `catalog_version`, `seed`, `day_index`,
   `recent_issue_keys`) nằm trong `ReadingPlan`, được chọn trước `plan_hash` và trước khi persist.
   - Plan cũ không có trường này giữ nguyên khoá và cách render (test golden với khoá tính trên commit
     cha `8e05e01`).
   - **Replay theo scope (sửa P2 của Codex):** trước khi chọn, đọc reading đang active của đúng scope
     hôm nay (owner, profile, ngày, cấu hình lá số, lens).
     - Nếu cùng snapshot lá số và cùng `catalog_version`, dùng lại nguyên `DailyVariety` đã lưu (seed,
       `day_index`, `recent_issue_keys`).
     - Nếu note hôm nay đã phục vụ trước khi bật xoay vòng (plan không có `DailyVariety`), giữ nguyên như
       vậy.
     - Lịch sử D−1/D−2 chỉ đọc khi ngày đó chưa có reading. Vì thế D−1 hoàn tất muộn, đổi key material
       hay restart đều không đổi note đã mở.
     - Đổi snapshot lá số hoặc `catalog_version` vẫn là cập nhật có chủ đích: chọn mới và hiện
       `available_update` như trước.
   - **First writer wins:** reading đầu tiên của ngày được kích hoạt bằng `activate_first`.
     - Hàm này chỉ kích hoạt khi projection còn trống, chạy dưới cùng khoá guest với `publish_available`,
       và không bao giờ ghi `available_update`.
     - Request thua cuộc đọc `DailyVariety` của bên thắng, dựng lại đúng plan đó (replay theo khoá) và trả
       nội dung của bên thắng.
     - Plan và revision bên thua đã lưu thì nằm lại trong kho, không được trỏ tới, xoá cùng hồ sơ.
   - Repository thêm `get_plan` vào protocol (Postgres đã có sẵn) và `activate_first`.
6. **Bật theo ngày:** `LA_LANH_DAILY_VARIETY_FROM` (mặc định không đặt, tức tắt).
   - Từ ngày đó, note ngày dùng xoay vòng mới. Ngày trước đó giữ nguyên.
7. **Đo:** `pnpm variety:a1` ghi báo cáo sau A1 vào `docs/reviews/variety-a1-2026-10-17/`.
   `baseline.json` của P1 giữ nguyên byte (chạy lại với xoay vòng tắt để chứng minh).
8. Sửa P3 của Codex trong README baseline P1 (nhãn và mẫu số pool).

**Không làm trong task này:**

- Ngữ pháp nội dung, lịch chủ, `L`, manifest, `variety_exception` (G0/G1). Vì vậy cam kết (b) "không lặp
  câu trong L ngày" và AC06 (ngoại lệ) chưa áp dụng.
- Pool cho người chỉ có ngày sinh, cân lại transit, 5 tình huống mới (A2/G1).
- Các vòng quay theo ngày khác vẫn giữ nguyên: xoay tổng hợp natal trong planner, `_daily_focus_domain`,
  khung câu trong `knowledge.py`.
- Tarot và Hợp gu.
- Bump `K[v+1]`: cấu trúc `key_version` đã có, chưa có lịch đổi khoá.

## Ánh xạ AC

| AC (US-21) | Trạng thái trong task | Bằng chứng |
|---|---|---|
| AC01 seed không chứa ngày | Xong cho 3 trục và top-K. "Vị trí p dùng chung mọi khung" thuộc G0 | `test_seed_has_no_date_and_separates_owner_catalog_and_key_version` |
| AC02 mọi ô đổi giữa hai ngày liền | Xong cho 3 trục hiện có, kể cả biên chu kỳ | `test_every_axis_changes_every_day_including_cycle_boundaries`, test render ngày-only và có giờ, báo cáo sau A1 |
| AC03 không lặp câu trong L ngày | Chưa: cần lịch chủ (G0/G1) | — |
| AC04 replay | Xong: restart, cache miss, mở lại trong ngày, D−1 hoàn tất muộn, đổi key material, hai request tạo đồng thời đều trả đúng revision đầu tiên; plan cũ không đổi; FROM đặt sau khi note hôm nay đã mở (kể cả bằng hôm nay) không đổi hôm nay; đổi catalog/lá số vẫn là update có chủ đích | `test_rotation_replays_the_same_revision_after_restart`, `test_late_previous_day_never_changes_an_opened_note`, `test_new_key_material_after_restart_only_applies_to_new_days`, `test_concurrent_first_readings_keep_the_first_writer`, `test_start_date_set_after_today_was_opened_keeps_today`, `test_catalog_or_chart_change_is_still_an_intentional_update`, `test_activate_first_only_fills_an_empty_projection`, `test_legacy_plans_keep_their_identity` |
| AC05 top-K và guard | Xong | `test_top_k_*`, `test_guard_reads_served_days_and_stops_at_the_first_unserved_day`, `test_exact_note_with_transits_changes_every_axis_and_respects_the_guard` |
| AC06 ngoại lệ | Chưa: cần manifest (G0) | — |
| AC14 đo trên output được phục vụ | Một phần: harness đo output render cuối cùng, gồm fallback natal khi gate từ chối | `docs/reviews/variety-a1-2026-10-17/` |

## Phát hành (owner quyết, không làm trong PR)

- Deploy với `LA_LANH_DAILY_VARIETY_FROM` **chưa đặt** thì hành vi y như hiện tại.
- Muốn bật: đặt `LA_LANH_DAILY_VARIETY_FROM` trong `infra/hetzner/app.env`, rồi restart API.
  - Khuyến nghị đặt **ngày sau ngày deploy** cho dễ đối chiếu.
  - Đặt bằng chính ngày deploy cũng không đổi note đã mở hôm đó, vì note được replay như cũ. Chỉ người
    mở lần đầu sau khi restart mới nhận xoay vòng.
- Tắt lại: bỏ biến. Ngày mới quay về vòng quay theo ngày. Ngày đã mở trong lúc bật có thể hiện
  `available_update` nếu được mở lại cùng ngày.
- Đổi `guest_hash_key` sẽ đổi `K[1]`. Plan đã lưu không đổi; chỉ ngày mới đổi biến thể.

## Bảo mật và riêng tư

- **Không có endpoint, cột hay bảng mới.**
  - `seed` là HMAC 128 bit của `profile_id`. Không suy ngược được nếu không có khoá. Không chứa ngày sinh,
    giờ sinh hay toạ độ.
  - `seed` nằm trong plan, và plan đã được mã hoá (`plan_ciphertext`), xoá cùng hồ sơ.
- `recent_issue_keys` là mã danh mục đóng (ví dụ `capacity-before-agreement`), không phải chữ người dùng.
- Không log seed hay issue. Không có trong response API, vì projection chỉ trả prose.
- Không gửi provider: payload provider là allowlist (`_safe_payload`, brief rewrite).
  - Có test chặn `seed` và `daily_variety` khỏi payload.
- Khoá: `K[1]` dẫn xuất bằng HMAC có nhãn phiên bản, chỉ dùng để chọn biến thể, không mã hoá hay xác thực
  dữ liệu.
- Không cần cập nhật khai báo Apple/Google hay privacy copy: không có loại dữ liệu mới, mục đích mới hay
  bên nhận mới. Data map ghi thêm một dòng về dữ liệu suy ra.
