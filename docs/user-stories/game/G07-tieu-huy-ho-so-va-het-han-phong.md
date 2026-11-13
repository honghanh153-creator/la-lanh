# G07 — Tiêu huỷ hồ sơ và hết hạn phòng

> Hạ tầng phòng dùng chung. Đặc tả: [`shared-room-platform-srs.md`](../../foundation/game-line/shared-room-platform-srs.md)
> §4.7, §6, §11, RP-PRV-04. Mỗi trò đặt lời thoại riêng cho màn này (Phiên Tòa: "Tòa tiêu huỷ hồ sơ"; Sĩ Số +1: "Xoá sổ
> điểm danh"). Trạng thái: nháp.

## 1. User story

Là người chơi, tôi muốn thấy tận mắt hồ sơ của buổi chơi bị xoá ở cuối buổi, và biết chắc nếu ai quên kết thúc thì phòng
cũng tự xoá sau tối đa 2 giờ, để tôi yên tâm câu trả lời của mình không nằm lại đâu cả.

## 2. Mục tiêu và ranh giới

### Mục tiêu

- Màn tiêu huỷ nói thật: chỉ chạy sau khi máy chủ đã xoá xong.
- Không dữ liệu theo người chơi nào sống quá mốc 2 giờ sau khi bắt đầu.
- Cảnh kết đủ đẹp để là cảnh người ta muốn quay lại (báo cáo, phần kết luận).

### Trong phạm vi

Xoá trong một giao dịch; màn tiêu huỷ có số đếm thật; tự kết thúc lúc 1h55; việc định kỳ mỗi phút; từ chối truy cập phòng
quá hạn; giữ số đếm tổng hợp; màn kết thúc trên điện thoại.

### Ngoài phạm vi

Nội dung lật mặt trước khi tiêu huỷ (SRS của trò); xoá backup (không có backup theo RP-PRV-04 — RP-D3).

## 3. Actor, điều kiện và output

- **Actor:** máy chủ; host (kết thúc); người chơi (xem).
- **Kích hoạt:** host kết thúc; trò tới cảnh kết; 1h55 sau bắt đầu; host vắng > 10 phút; sảnh 30 phút chưa bắt đầu; việc
  định kỳ thấy phòng quá `hard_expires_at`.
- **Output:** phòng `purged`; số đếm tổng hợp; mọi link, mã, token, cookie của phòng vô hiệu.

## 4. Luồng

```mermaid
sequenceDiagram
  participant T as Kích hoạt (host/trò/đồng hồ)
  participant S as Máy chủ
  participant K as Kho trạng thái
  participant M as Số đếm tổng hợp
  participant D as Màn chiếu + điện thoại
  T->>S: kết thúc phòng
  S->>D: room.ending ("Đang tiêu huỷ hồ sơ…")
  S->>K: Xoá biệt danh, câu trả lời, đồng ý, vai, phiếu, lượt riêng của trò, báo cáo, hash mã/token/phiên (một giao dịch)
  K-->>S: số hàng đã xoá theo loại
  S->>M: ghi số đếm gộp theo ngày (không room_id sau 24 giờ)
  S->>D: room.purged (số đã xoá)
  D->>D: Hiệu ứng đóng dấu "ĐÃ TIÊU HUỶ"
  Note over S,K: Lỗi giữa chừng → giao dịch huỷ, việc định kỳ mỗi phút làm lại; phòng đã bị khoá truy cập
```

## 5. Giao diện và trạng thái

**Màn chiếu** (chữ của trò, khung chung):

1. "Đang tiêu huỷ hồ sơ…" (tối đa vài giây, chờ máy chủ xác nhận).
2. Danh mục đã xoá: "Đã xoá: 27 biệt danh · 121 câu trả lời · vai và phiếu của buổi này."
3. Dấu đóng "ĐÃ TIÊU HUỶ" (có bản tĩnh khi bật giảm chuyển động).
4. Dòng cuối: "Không còn gì của buổi này được giữ lại, trừ con số tổng như số người chơi."

**Điện thoại:** "Buổi chơi đã kết thúc. Dữ liệu của bạn đã được xoá." + nút `Chơi lại` (về trang chủ Lá Úp) và
`Tôi muốn tự làm host` (đều chỉ đếm số lần bấm) + câu khảo sát của trò nếu có (G08).

**Bảng host:** cảnh báo ở phút 105 "Phòng sẽ tự kết thúc sau 10 phút"; phút 115 tự kết thúc.

Trạng thái lỗi: "Buổi chơi bị gián đoạn. Dữ liệu của bạn không được giữ lại." (máy chủ khởi động lại — SRS §9.4).

## 6. Quy tắc

1. Xoá trước, hiện sau (RP-FR-60). Số trên màn là số máy chủ trả về sau khi xoá.
2. Danh mục xoá theo SRS §6.1 cột "Xoá khi".
3. Phòng tự kết thúc ở 1h55; việc định kỳ mỗi phút là lưới an toàn cho mốc 2 giờ (RP-FR-63, RP-FR-64).
4. Phòng quá hạn bị từ chối mọi truy cập ngay, kể cả trước khi việc xoá chạy.
5. Chỉ giữ số đếm ở SRS §6.3; `room_id` không gắn với số đếm quá 24 giờ.
6. Lời trên màn không hứa điều không kiểm được: không viết "xoá vĩnh viễn khỏi mọi nơi" (ảnh chụp, video người trong
   phòng quay nằm ngoài tầm kiểm soát — dossier, mục "What is not claimed").

## 7. Tiêu chí chấp nhận

- **G07-AC01:** Sau `room.purged`, truy vấn trực tiếp kho trạng thái không còn hàng nào của phòng (biệt danh, câu trả lời,
  đồng ý, vai, phiếu, lượt riêng của trò, báo cáo, hash mã/token/phiên) (RP-TH-06).
- **G07-AC02:** Số trên màn tiêu huỷ bằng số hàng máy chủ đã xoá; nếu xoá lỗi, màn không chạy hiệu ứng đóng dấu.
- **G07-AC03:** Với đồng hồ giả, phòng bắt đầu lúc T tự kết thúc lúc T + 1h55 và có cảnh báo lúc T + 1h45.
- **G07-AC04:** Tắt luồng kết thúc thường (giả lập lỗi), việc định kỳ xoá phòng trong ≤ 60 giây sau `hard_expires_at`; mọi
  truy cập sau `hard_expires_at` bị từ chối.
- **G07-AC05:** Sau tiêu huỷ: mã phòng, token vào phòng, token màn chiếu, `host_session`, `player_session` đều trả thông báo
  lỗi chung; cookie bị xoá phía trình duyệt (`Max-Age=0`).
- **G07-AC06:** Số đếm tổng hợp không chứa biệt danh, slot, câu trả lời hay lựa chọn phiếu; sau 24 giờ không còn `room_id`.
- **G07-AC07:** Kho trạng thái phòng không nằm trong bất kỳ lịch backup hay PITR nào (biên bản của operator) — điều kiện
  phát hành, phụ thuộc RP-D3.
- **G07-AC08:** Hiệu ứng đóng dấu qua kiểm nhấp nháy; có bản tĩnh khi bật giảm chuyển động.
- **G07-AC09:** Câu chữ trên màn tiêu huỷ không có cụm "vĩnh viễn khỏi mọi nơi" hay hứa hẹn về ảnh chụp của người khác.

## 8. Trường hợp biên

| Trường hợp | Cách xử lý |
|---|---|
| Mất điện màn chiếu đúng lúc tiêu huỷ | Máy chủ vẫn xoá; điện thoại vẫn nhận màn kết thúc |
| Máy chủ khởi động lại giữa buổi | Kho tạm thời mất; phòng coi như đã tiêu huỷ; điện thoại báo gián đoạn |
| Người chơi muốn giữ lại kết quả | Không có bản lưu ở MVP; trò không tạo thẻ chia sẻ chứa câu trả lời |
| Tiêu huỷ chạy khi một người đang gửi phiếu | Lệnh trả `closed`; không tạo hàng mới sau khi phòng `ended` |

## 9. Definition of Done

- G07-AC01–AC09 pass trên môi trường giống production.
- Biên bản operator xác nhận kho trạng thái không có backup/PITR (RP-D3 đã chốt).
- DPIA, nháp chính sách quyền riêng tư và nhãn cửa hàng ghi đúng thời hạn: "xoá khi buổi chơi kết thúc, chậm nhất 2 giờ sau
  khi bắt đầu".
- Không còn lỗi P0/P1.

## 10. Bàn giao

- **Nguồn:** SRS §4.7; báo cáo ("tòa tiêu huỷ hồ sơ", phần kết luận); brief chung (hết hạn cứng 2 giờ); dossier P07 (backup).
- **Đã xử lý:** xoá trước rồi mới hiện; tự kết thúc 1h55; không hứa xoá được ảnh người khác chụp.
- **Rủi ro mở:** RP-D3.
- **AC/DoD chưa xong:** toàn bộ.
