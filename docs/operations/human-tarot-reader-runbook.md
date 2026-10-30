# Runbook — Người bốc Tarot làm việc trong Google Sheet (US-24)

> Dành cho owner (người bốc) và người vận hành. Chưa áp dụng cho dữ liệu thật: cờ `human_tarot_enabled` và
> `human_tarot_sheet_sync_enabled` đang tắt, chưa có file Google hay quyền nào được cấp. Owner đã chốt (30/10): ngừng
> nhận 18:00, trả bài 22:00, retention, thay file mỗi tháng, service account trên đúng một file, tài khoản Google
> Workspace. Còn mở trước dữ liệu thật: copy (OD4) và P09/P10, thông báo quyền riêng tư, store (OD6).

## 1. Chuẩn bị một lần (owner)

1. Tạo **một** Google Sheet mới cho production (và một file khác, chỉ dữ liệu tổng hợp, cho staging). Không dùng
   lại Sheet cá nhân nào khác; không chia sẻ "Bất kỳ ai có đường liên kết".
2. Nhập bản mẫu `docs/operations/human-tarot-sheet-template.xlsx` (File → Nhập → Thay thế bảng tính). Bản mẫu có:
   - tab **Hôm nay**: hàng 1 là header cố định (17 cột A–Q), hàng 2–11 trống;
   - tab **Lá**: tên 78 lá theo catalog của app, dùng cho dropdown;
   - tab **Hướng dẫn**: tóm tắt mục 2 dưới đây.
3. Ở tab Hôm nay, chọn O2:O11 → Chèn → Hộp kiểm. Kiểm H2:L11 đang là dropdown lấy từ tab Lá.
4. Không đổi tên tab, không thêm/xoá/đổi chỗ cột, không sort hay lọc làm đổi thứ tự hàng. App kiểm header mỗi lần
   đọc; header sai thì app dừng đồng bộ (`SHEET_LAYOUT_INVALID`) cho tới khi sửa lại.
5. Chia sẻ file cho **đúng một** service account của app với quyền Người chỉnh sửa (OD3). Không chia sẻ thêm ai.
   Người vận hành đặt file khoá của service account vào thư mục secret trên VPS và cấu hình
   `LA_LANH_HUMAN_TAROT_SHEET_ID`, `LA_LANH_HUMAN_TAROT_GOOGLE_CREDENTIALS_FILE`; việc này cần lệnh riêng của owner.

## 2. Mỗi ngày (owner)

| Giờ | Việc |
|---|---|
| Từ 00:00 | App nhận tối đa 10 câu hỏi, mỗi câu vào đúng hàng app cấp (cột A–G do app ghi). Cột P ghi "Đang chờ bài". |
| Từ 00:00 tới 18:00 (giờ ngừng nhận, owner chốt 30/10) | Đọc câu hỏi, bốc đúng số lá ở cột F theo thứ tự vị trí ở cột G, chọn tên lá ở H–L. |
| Trước 22:00 | Viết "Bài đọc" (M, 40–1.500 ký tự) và "Bước nhỏ" (N, 8–240 ký tự) bằng chữ thường: không link, không công thức, không nội dung do AI viết. Tick **Sẵn sàng** (O) sau cùng. |
| Trong vòng 1 phút | App đọc hàng đã tick. Hợp lệ → cột P "Đã nhận bài". Chưa hợp lệ → P "Cần sửa", cột Q ghi mã lỗi (bảng dưới); sửa rồi để nguyên dấu tick, app đọc lại. |
| 22:00 | Người dùng mở được bài. Bài đã nhận không đổi nữa dù sửa Sheet. |
| Hết ngày | App xoá mọi hàng của ngày đó. Câu nào chưa có bài thì kết thúc, người dùng thấy "không có bài hôm nay". |

Mã lỗi ở cột Q: `NGAY_KHONG_KHOP` (cột B bị sửa), `SO_LA_SAI`, `LA_n_KHONG_CO` (tên lá không có trong tab Lá),
`LA_TRUNG`, `BAI_DOC_QUA_NGAN`/`BAI_DOC_QUA_DAI`, `BUOC_NHO_QUA_NGAN`/`BUOC_NHO_QUA_DAI`, `CO_LINK_HOAC_CONG_THUC`,
`CAU_KHANG_DINH_KHONG_AN_TOAN` (khẳng định chắc chắn, đoán ý người khác, lời khuyên y tế… như bộ lọc của app).

Nếu đã tick mà muốn viết lại sau khi app báo "Đã nhận bài": không sửa âm thầm. Bài đã nhận là bài người dùng thấy;
muốn thay phải có quy trình riêng (chưa có trong bản đầu).

## 3. Quy tắc dữ liệu (bắt buộc)

- Sheet chỉ có mã yêu cầu, ngày, giờ hẹn, chủ đề, câu hỏi, số lá, vị trí và phần owner viết. Không thêm tên, liên
  hệ hay bất kỳ ghi chú nào về người hỏi; không chép câu hỏi sang nơi khác (chat, email, GitHub, ghi chú điện thoại).
- Không tải file xuống, không tạo bản sao, không xem lịch sử phiên bản để tìm lại câu hỏi đã xoá.
- Mã `LL-XXXXXX` chỉ là nhãn công việc; không dùng để liên hệ hay tìm người dùng.
- Hàng bị huỷ hoặc xoá sẽ biến mất trong vòng một phút; đừng gõ lại.

## 4. Vận hành (người vận hành)

- Job: `python -m scripts.sync_human_tarot` mỗi phút trong container app đang chạy, qua timer
  `la-lanh-human-tarot-sync.timer` (`infra/hetzner/install-human-tarot-sync-timer.sh`, chỉ cài khi owner ra lệnh).
  Một lượt: dọn cuối ngày và retention, xoá hàng đến hạn, ghi hàng chưa ghi, nhập hàng đã tick.
- Trần gọi Google của app: 30 lần/phút và 2.000 lần/ngày, gồm cả retry. Chạm trần → `GOOGLE_BUDGET_EXHAUSTED`, job
  dừng và thử lại phút sau; không tự xin thêm quota hay bật billing.
- Log chỉ có số đếm và mã lỗi (`SHEETS_UNAVAILABLE`, `SHEETS_RATE_LIMITED`, `SHEETS_ACCESS_DENIED`,
  `SHEET_LAYOUT_INVALID`, `SLOT_OCCUPIED`, `SLOT_MOVED`, `ROW_UNVERIFIED`, `GOOGLE_BUDGET_EXHAUSTED`).
- Mỗi hàng gắn với yêu cầu bằng cả **vị trí hàng do app cấp** và **mã**. App không bao giờ ghi vào hàng còn chữ mà
  thiếu mã (`SLOT_OCCUPIED`), không nhập bài khi mã đã rời hàng của nó (ví dụ chỉ sort A:G: `row_moved`), và không xoá
  khi mã nằm ở hàng khác (`SLOT_MOVED`) hay hàng đã mang mã khác (`ROW_UNVERIFIED`). Khi gặp các mã này, owner trả
  hàng về đúng chỗ hoặc xoá trống cả hàng; đừng chỉ xoá mã. Chỉ khi đọc lại cả hàng trống app mới báo đã xoá bản tạm. Không bao giờ in câu hỏi, bài, mã yêu cầu
  hay giá trị ô.
- Google lỗi hoặc mất quyền: lượt người dùng vẫn được giữ, app hiện "Chưa chuyển được tới người bốc"; sửa quyền
  rồi job tự thử lại (giãn tối đa 15 phút).
- Restore database trong một ngày đang nhận: chạy `python -m scripts.sync_human_tarot close-today` ngay sau replay
  nhật ký xoá (lệnh replay cũng tự làm việc này). Ngày đó không nhận thêm, dù Sheet còn hàng trống. Hàng trên Sheet
  có mã mà database không biết sẽ bị job xoá.
- Thay file Sheet mỗi tháng (OD2, owner duyệt 30/10; làm sau 22:00 hoặc trước 00:00 ngày mới): tạo file mới từ bản mẫu, chia sẻ cho service
  account, đổi `LA_LANH_HUMAN_TAROT_SHEET_ID`, kiểm một lượt job, rồi chuyển file cũ vào thùng rác và dọn thùng rác.
  Đây là cách giới hạn lịch sử phiên bản của Google; xoá ô không xoá lịch sử phiên bản.

## 5. Kiểm thử không có Google

`tests/human_tarot/test_sheets_sync.py` chạy toàn bộ cầu nối với `FakeSheet` (bộ nhớ, chỉ trong test). Rehearsal với Google thật
chỉ dùng file tổng hợp của staging, sau khi owner cấp quyền, và có receipt riêng; không dùng Sheet cá nhân khác.
