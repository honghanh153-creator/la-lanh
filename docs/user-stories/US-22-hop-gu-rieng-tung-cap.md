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
  replay trả đúng bản đã tạo. Bản đã lưu giữ nguyên tới hết hạn 30 ngày.
- **AC06:** Không lưu thêm dữ liệu của người kia. Chart của họ vẫn tính xong rồi bỏ; nhãn và kết quả vẫn
  được mã hoá.
- **AC07:** Người kia không rõ giờ sinh: không dùng Mặt Trăng, cung mọc, nhà của họ. Contact chỉ dùng khi
  orb chắc trên miền ngày sinh (`la-lanh-personal-sky-events-spec.md`).
- **AC08:** Khung, allowlist, lịch chủ và manifest theo `la-lanh-content-grammar-spec.md`. Trên output cuối
  cùng: 0 câu ngoài allowlist; ngoại lệ báo riêng.
- **AC09:** `scripts/audit_radar_experience.py` mở rộng lên 50 cặp (có giờ và không rõ giờ) và báo các chỉ
  số AC01–AC03. `pnpm check` đạt.
- **AC10:** Cà khịa cho câu mới; owner duyệt qua file Excel.

## Definition of Done

- AC01–AC10 có test và audit.
- Cập nhật radar spec, content-matrix-release-gate (sửa ghi chú cũ về kế hoạch biên tập), baseline.
- Codex APPROVE @ SHA; release theo runbook.
