# G36 — Đại Án: tìm Kẻ Chủ Mưu, trao danh hiệu, tiêu huỷ hồ sơ

> Phiên Tòa Tủ Lạnh. [PRD](../../foundation/game-line/phien-toa-tu-lanh-prd.md) §4.1, §4.3 ·
> [SRS](../../foundation/game-line/phien-toa-tu-lanh-srs.md) §3.6. Phiếu: **G05**. Khảo sát cuối buổi: **G08**. Tiêu huỷ hồ sơ:
> **G07**. Trạng thái: nháp.

## 1. User story

Là người chơi sau ba vụ, tôi muốn cùng đội ghép ba chữ bị đổi để đoán ai là Kẻ Chủ Mưu, xem cả phòng bỏ phiếu, nghe danh hiệu vui
cho từng đội và từng vai, rồi xem tòa tiêu huỷ hồ sơ ngay trên màn hình.

## 2. Mục tiêu và ranh giới

### Mục tiêu

- Đại Án 4–5 phút, là cao trào của buổi.
- Mọi danh hiệu đều tích cực.
- Kết bằng tiêu huỷ hồ sơ thật (G07).

### Trong phạm vi

Ba chữ và gợi ý; đề cử theo đội; bỏ phiếu cả phòng; lộ diện hoặc thoát; tiết lộ Kẻ Chủ Mưu và Thư Ký; bản án + Miễn án cho Kẻ Chủ
Mưu lộ diện; danh hiệu; câu khảo sát; chuyển sang tiêu huỷ.

### Ngoài phạm vi

Kẻ Chủ Mưu xuyên mùa (sau MVP, cần thiết kế riêng tư mới); cơ chế tiêu huỷ (G07).

## 3. Actor, điều kiện và output

- **Actor:** đội, mọi người chơi, Kẻ Chủ Mưu, Thẩm Phán Lá.
- **Điều kiện:** vụ 3 đã xong (hoặc host bỏ qua tới Đại Án).
- **Output:** phiếu `pt_grand_nominate`, `pt_grand_verdict`, `pt_pardon`; danh hiệu; số đếm khảo sát; phòng `ended`.

## 4. Luồng

```mermaid
flowchart TD
  A["Sau vụ 3"] --> B{"Kẻ Chủ Mưu đã đổi ít nhất 1 chữ?"}
  B -->|Không (đã rời từ đầu)| X["'Kẻ Chủ Mưu đã rời phòng, đại án khép lại'"] --> H
  B -->|Có| C["Màn chiếu: các chữ bị đổi + TPL-27, TPL-28 — ghép chữ 60 s"]
  C --> D["Đội đề cử (pt_grand_nominate) — 45 s"]
  D --> E["Cả phòng bỏ phiếu (pt_grand_verdict) — 20 s"]
  E --> F{"Đứng đầu và ≥ 1/4 phiếu là Kẻ Chủ Mưu?"}
  F -->|Có| G["TPL-29 + bản án + Miễn án"]
  F -->|Không| G2["TPL-30"]
  G --> H["Danh hiệu (TPL-31) — 45 s"]
  G2 --> H
  H --> I["Khảo sát 1 câu — 30 s (G08)"]
  I --> J["Tiêu huỷ hồ sơ (G07) → TPL-32 → TPL-33"]
```

## 5. Giao diện và trạng thái

- Màn chiếu ghép chữ: ba ô chữ lớn theo thứ tự vụ, mỗi ô ghi "Vụ 1 / Vụ 2 / Vụ 3"; gợi ý "Ba chữ này là chữ cái đầu trong ba câu trả
  lời của Kẻ Chủ Mưu (bữa sáng, loại nhạc, chỗ ngồi, màu áo hoặc món trong túi)."
- Điện thoại: bảng tra chữ cái đầu → phương án của 5 câu (để đội tự ghép, ví dụ X → Xanh dương/Xanh lá/Xôi); phiếu đề cử.
- Danh hiệu: từng thẻ lật, tên danh hiệu + biệt danh (người có đồng ý) hoặc tên đội.
- Trạng thái: `không có Kẻ Chủ Mưu` (đã rời), `chỉ có 1–2 chữ` (Kẻ Chủ Mưu rời giữa chừng).

## 6. Quy tắc

Theo SRS PT-FR-70 đến PT-FR-76 và bảng rời phòng §3.7. Không công bố đội nào đề cử ai ngoài danh sách đề cử chung.

## 7. Tiêu chí chấp nhận

- **G36-AC01:** Ba chữ hiện đúng thứ tự vụ, mỗi chữ là chữ cái đầu (bỏ dấu, viết hoa) của một câu trả lời khác `skip` của Kẻ Chủ Mưu.
- **G36-AC02:** Bảng tra trên điện thoại chỉ chứa phương án của 5 câu, không chứa câu trả lời của bất kỳ ai.
- **G36-AC03:** Đề cử và bỏ phiếu theo luật PT-FR-71, PT-FR-72; người bị bầu nhầm không nhận bản án.
- **G36-AC04:** Kẻ Chủ Mưu lộ diện nhận bản án tượng trưng + nút Miễn án như G35-AC01.
- **G36-AC05:** Tuyên án cuối hiện ai đóng Kẻ Chủ Mưu và Thư Ký (chỉ người có `consent_display`).
- **G36-AC06:** Mọi danh hiệu thuộc danh sách tích cực của PRD §4.3; người đã rời hiện "Người đã rời"; không có bảng điểm cá nhân.
- **G36-AC07:** Kẻ Chủ Mưu rời từ trước vụ 1: Đại Án bị bỏ với câu giải thích, buổi chơi vẫn tới danh hiệu và tiêu huỷ.
- **G36-AC08:** Câu khảo sát "Có lúc nào bạn thấy bị nhắm vào không?" chỉ lưu số đếm (G08-AC08).
- **G36-AC09:** Sau danh hiệu và khảo sát, phòng chuyển `ended` và G07 chạy; số đếm trên màn tiêu huỷ khớp số hàng đã xoá.
- **G36-AC10:** Điểm đội và danh hiệu không còn tồn tại sau tiêu huỷ (không mang sang buổi sau).

## 8. Trường hợp biên

| Trường hợp | Cách xử lý |
|---|---|
| Nhiều người có cùng bộ ba chữ cái | Bình thường; Đại Án là đoán, có thể sai |
| Host bỏ qua thẳng tới Đại Án sau vụ 1 | Đại Án dùng chữ của các vụ đã chơi |
| Không đội nào đề cử | Bỏ phiếu bị bỏ qua; TPL-30 |

## 9. Definition of Done

- G36-AC01–AC10 pass.
- Danh hiệu và câu Đại Án được owner duyệt văn phong.
- Không còn lỗi P0/P1.

## 10. Bàn giao

- **Nguồn:** báo cáo ("Ai đứng sau cả ba vụ?", danh hiệu cả buổi, tòa tiêu huỷ hồ sơ); PRD §4.3.
- **Đã xử lý:** chữ của Chủ Mưu suy ra từ câu trả lời của chính người đó (không thêm dữ liệu); danh hiệu chỉ tích cực.
- **Rủi ro mở:** Đại Án có thể quá khó hoặc quá dễ — chơi thử đo.
- **AC/DoD chưa xong:** toàn bộ.
