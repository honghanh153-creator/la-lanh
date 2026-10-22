# US-22 — Hợp gu: bản đọc riêng cho từng cặp

> Nguồn: kế hoạch `docs/plans/2026-10-16-personalisation-variety-plan.md` (§5, §14.5; quyết định owner §8:
> R2, bản triệt để). Spec hiện có: `docs/foundation/la-lanh-radar-hop-gu-spec.md`.

## User story

Là người xem Hợp gu với một người cụ thể, tôi muốn bài đọc nói về đúng hai lá số này và đúng mối quan hệ
tôi chọn (crush, bạn, người yêu, …), với giọng tôi chọn. Bài không dán nhãn phán xét cho cặp và không đoán
ý người kia.

## Phạm vi

**Bao gồm:**

- Cảnh theo chủ đề × ngữ cảnh.
- Câu theo contact (cặp hành tinh × họ góc chiếu × ngữ cảnh × giọng).
- Câu về nhịp hai người, lấy từ cân bằng nguyên tố và tính chất.
- Ngữ cảnh đổi cả mục "hợp" và "ma sát".
- Giọng đổi cả câu.
- Kế hoạch biên tập nối vào các chương hiển thị, khoảng 30 khái niệm.
- Tất cả trên ngữ pháp nội dung.

**Không bao gồm:** thẻ câu hỏi và góc nhìn hai phía (chặng 2); nhắc lại sau 7 ngày (chặng 3).

## Acceptance Criteria

- **AC01:** Mỗi bản đọc có ít nhất 2 câu riêng theo contact thật giữa hai chart. Không còn một cảnh cố định
  cho mỗi chủ đề.
- **AC02:** Cùng một cặp, đổi ngữ cảnh thì ≥ 50% câu của mục "hợp" và "ma sát" đổi (không chỉ thẻ kiểm
  chứng). Đổi giọng thì ≥ 50% câu đổi (không chỉ tiền tố).
- **AC03:** Trên 50 cặp tổng hợp × 4 ngữ cảnh × 4 giọng, độ trùng câu sau chuẩn hoá giữa các cặp < 30%.
- **AC04:** Không có nhãn phán xét kiểu "Soulmate/Challenging", không điểm tổng, không đoán ý người kia.
  Gate anti-influence và meaning đạt.
- **AC05:** Biến thể chọn **một lần khi tạo kết quả**, theo seed của kết quả đã có. Mở lại, đổi giọng hay
  replay trả đúng bản đã tạo. Bản đã lưu giữ nguyên tới hết hạn (check kín: 24 giờ; lời mời đã đồng ý: 30 ngày).
- **AC06:** Không lưu thêm dữ liệu của người kia. Chart của họ vẫn tính xong rồi bỏ; nhãn và kết quả vẫn
  được mã hoá.
- **AC07:** Người kia, hoặc cả hai, không rõ giờ sinh: không dùng Mặt Trăng, cung mọc, nhà của người đó.
  Contact natal–natal chỉ dùng khi chắc trong orb trên **tích hai miền** ngày sinh, với ngưỡng và phiên bản
  của bảng **synastry**, không phải ngưỡng transit (`la-lanh-personal-sky-events-spec.md` §9).
- **AC08:** Khung, allowlist, lịch chủ và manifest theo `la-lanh-content-grammar-spec.md`.
  - Trên output cuối cùng: M8a (phủ allowlist ngữ pháp) = 100% trên output không ngoại lệ.
  - M8b (mọi output từ nguồn đã duyệt, kể cả kho nền theo `fallback-approval.json`) = 100%.
  - Ngoại lệ báo riêng theo lý do.
- **AC09:** `scripts/audit_radar_experience.py` mở rộng lên 50 cặp (có giờ và không rõ giờ) và báo các chỉ
  số AC01–AC03. `pnpm check` đạt.
  - **Trạng thái 22/10/2026 (audit R01/R06):** gate AC01–AC03 nằm ở `scripts/audit_radar_us22.py`
    (`pnpm radar:us22`). Trên `c3fab33` gate đỏ cả bốn chỉ số: AC01 528/800 bài dưới 2 câu riêng theo
    contact (câu chỉ được tính khi ít nhất 2 cặp cùng hiện và cùng chung một contact có hướng), AC02 ngữ
    cảnh 0,0 và giọng 0,0, AC03 trùng 0,9127. `tests/scripts/test_radar_us22_gate.py` giữ gate ở dạng
    strict xfail: khi nội dung R03 đạt, test này đỏ cho tới khi gỡ marker và đưa gate vào `pnpm check`.
- **AC10:** Cà khịa cho câu mới; owner duyệt qua file Excel.

## Definition of Done

- AC01–AC10 có test và audit.
- Cập nhật radar spec, content-matrix-release-gate (sửa ghi chú cũ về kế hoạch biên tập), baseline.
- Codex APPROVE @ SHA; release theo runbook.
