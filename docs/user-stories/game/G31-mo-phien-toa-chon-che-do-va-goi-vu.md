# G31 — Mở Phiên Tòa: chọn chế độ, gói vụ và đổi vụ an toàn

> Phiên Tòa Tủ Lạnh. [PRD](../../foundation/game-line/phien-toa-tu-lanh-prd.md) §4.4, §6.1 · [SRS](../../foundation/game-line/phien-toa-tu-lanh-srs.md)
> §3.1. Tạo phòng, màn chiếu, sảnh chờ, nút host chung: **G01, G06** (không nhắc lại ở đây). Trạng thái: nháp.

## 1. User story

Là host tất niên văn phòng, tôi muốn chọn chế độ hợp với phòng mình, chọn hoặc bốc ngẫu nhiên ba vụ, tránh các vụ "lấy đồ" nếu
công ty vừa mất đồ thật, và đổi sang vụ con vịt cao su ngay khi thấy không khí không hợp.

## 2. Mục tiêu và ranh giới

### Mục tiêu

- Chọn xong cấu hình trong ≤ 30 giây (mặc định dùng được ngay).
- Không lựa chọn nào bật yếu tố ma.
- Host luôn có một lối an toàn (vụ con vịt) trước khi cáo trạng kết thúc.

### Trong phạm vi

Chế độ Văn phòng / Lớp học / Tất niên; chọn 3 vụ hoặc ngẫu nhiên; công tắc "Tránh chủ đề lấy đồ"; nút "Đổi sang vụ con vịt cao
su"; xem trước tên vụ trên bảng host (không hiện lên màn chiếu cho tới khi vụ bắt đầu).

### Ngoài phạm vi

Host tự viết vụ; thẻ tự thú; mùa nhiều buổi; G01/G06.

## 3. Actor, điều kiện và output

- **Actor:** host.
- **Điều kiện:** đang tạo phòng (G01) với trò Phiên Tòa; hoặc vụ đang ở pha cáo trạng (đổi vụ).
- **Output:** cấu hình buổi: chế độ, danh sách 3 mã vụ, cờ tránh lấy đồ.

## 4. Luồng

```mermaid
flowchart TD
  A["G01: chọn trò Phiên Tòa"] --> B["Chọn chế độ: Văn phòng / Lớp học / Tất niên"]
  B --> C{"Tránh chủ đề lấy đồ?"}
  C -->|Bật| D["Lọc bỏ vụ 'lấy đồ' và 'nhạy cảm vừa'"]
  C -->|Tắt| E["Danh sách theo nhãn chế độ"]
  D --> F{"Chọn vụ"}
  E --> F
  F -->|Ngẫu nhiên (mặc định)| G["Bốc 3 vụ không lặp"]
  F -->|Tự chọn| H["Chọn đúng 3 vụ"]
  G --> I["Sảnh chờ (G01)"]
  H --> I
  I --> J["Vụ bắt đầu → pha cáo trạng"]
  J -->|Host bấm 'Đổi sang vụ con vịt cao su'| K["Thay vụ, giữ vai, đọc lại cáo trạng"]
```

## 5. Giao diện và trạng thái

- Bước chế độ: ba thẻ, mỗi thẻ một câu: "Văn phòng — chuyện pantry, phòng họp, máy lạnh." · "Lớp học — ký túc xá, căn tin, nhóm bài
  tập." · "Tất niên — sự cố hài của cả năm." Dưới cùng dòng "Không chế độ nào có ma."
- Bước vụ: danh sách tên vụ kèm nhãn nhỏ "lấy đồ" / "an toàn"; nút `Ngẫu nhiên`.
- Bảng host trong lúc chơi: tên vụ kế tiếp (chỉ host thấy); nút `Đổi sang vụ con vịt cao su` hiện trong pha cáo trạng, tắt sau đó.
- Trạng thái: `chưa đủ vụ` (khi tự chọn < 3), `vụ con vịt đã dùng` (nút đổi sang vụ an toàn còn lại).

## 6. Quy tắc

Theo SRS PT-FR-01 đến PT-FR-06. Chế độ không đổi được sau khi bắt đầu. Danh sách vụ đọc từ kho nội dung có phiên bản đã được owner
duyệt.

## 7. Tiêu chí chấp nhận

- **G31-AC01:** Không có lựa chọn, công tắc hay vụ nào trong cả ba chế độ chứa yếu tố ma (rà kho nội dung theo từ khoá: ma, hồn, nhập,
  người thứ 31…).
- **G31-AC02:** Chế độ Văn phòng chỉ bốc vụ có nhãn VP; Lớp học chỉ LH; Tất niên mọi vụ có nhãn TN, kèm câu dẫn "Trong năm qua…".
- **G31-AC03:** Bật "Tránh chủ đề lấy đồ": vụ 1, 3, 5 (lấy đồ) và vụ 2 (nhạy cảm vừa) không xuất hiện trong danh sách và trong 1.000
  lần bốc ngẫu nhiên.
- **G31-AC04:** Ngẫu nhiên không lặp vụ trong một buổi.
- **G31-AC05:** Trong pha cáo trạng, bấm "Đổi sang vụ con vịt cao su": màn chiếu đọc cáo trạng vụ 4 trong ≤ 1 giây; vai đã chia không
  đổi; nếu vụ 4 đã dùng, thay bằng một vụ "không lấy đồ" chưa dùng.
- **G31-AC06:** Sau pha cáo trạng, nút đổi vụ bị tắt; host vẫn dùng được "Bỏ qua vụ" (G06).
- **G31-AC07:** Tên vụ kế tiếp không có trong gói `display`/`audience` trước khi vụ bắt đầu.
- **G31-AC08:** Chỗ trống của vụ bốc khi vụ bắt đầu và giữ nguyên tới hết vụ.

## 8. Trường hợp biên

| Trường hợp | Cách xử lý |
|---|---|
| Bật tránh lấy đồ ở chế độ Văn phòng chỉ còn 2 vụ (4, 6) | Bổ sung vụ an toàn từ nhãn TN; nếu vẫn thiếu, hiện "Gói an toàn có 2 vụ" và cho chơi 2 vụ + Đại Án |
| Host đổi vụ hai lần trong một buổi | Lần hai thay bằng vụ an toàn còn lại; hết vụ an toàn thì nút tắt |
| Host muốn đổi chế độ giữa chừng | Không được; phải kết thúc và mở phòng mới |

## 9. Definition of Done

- G31-AC01–AC08 pass.
- Kho bảy vụ được owner duyệt văn phong; biên bản rà nhóm chủ đề cấm (PT-TH-05).
- Không còn lỗi P0/P1.

## 10. Bàn giao

- **Nguồn:** báo cáo (ba chế độ, nút đổi sang vụ con vịt, lằn ranh "trộm"); PRD §4.4, §6.1.
- **Đã xử lý:** thêm công tắc "Tránh chủ đề lấy đồ"; gắn "nhạy cảm vừa" cho vụ seen không rep.
- **Rủi ro mở:** gói an toàn cho Văn phòng hơi mỏng (2 vụ) — cần viết thêm vụ "không lấy đồ".
- **AC/DoD chưa xong:** toàn bộ.
