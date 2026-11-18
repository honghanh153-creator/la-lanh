# Lớp chặn câu tự hại đứng trước endpoint (15/11/2026)

Mức: **L**. Lớp này đổi hành vi API ở 7 endpoint, có endpoint công khai, và chạm an toàn người dùng. PR #505.

## Quyết định

Một bộ nhận diện dùng chung `apps/api/app/domains/safety/crisis.py` đọc chữ người dùng gõ (câu hỏi Tarot, các ô tên). Nó chạy như một dependency của route (`crisis_guard()`), **trước** kiểm CSRF, phiên và kiểm dữ liệu vào:

- Câu khớp: route trả `422` `application/problem+json`, mã `CRISIS_NOTICE`, kèm `Cache-Control: no-store` và câu hỗ trợ owner duyệt ngày 14/11. Endpoint không chạy, nên không ghi gì vào cơ sở dữ liệu.
- Câu không khớp: request đi tiếp như cũ.

Cách nhận diện:

- Danh sách cách nói viết tay, có dấu và không dấu, gồm câu nói kín, phủ định và tiếng lóng.
- Mỗi luật tiếng Việt ghi cách viết có dấu đúng của từ khóa. Gõ có dấu mà khác dấu là câu khác ("tủ sắt" không phải "tự sát"), nên không bị chặn. Gõ không dấu vẫn bị chặn. Thêm 16/11 sau review Codex vòng 2.
- Mỗi request chỉ quét tối đa 2048 ký tự, và không có backtracking lồng.
- Không gọi dịch vụ ngoài hay mô hình AI.

Web chỉ hiện câu server gửi về. Lời công bố trên `/privacy` do owner duyệt ngày 15/11 ("D duyệt").

## Các cách đã cân nhắc

1. **Kiểm trong từng endpoint, sau kiểm dữ liệu vào.** Bị loại. Câu ngắn hơn 8 ký tự (như "tự tử") bị trả lỗi độ dài trước khi tới lớp kiểm. Mỗi endpoint lại phải nhớ gọi lớp này.
2. **Kiểm ở web trước khi gửi.** Bị loại. Bỏ qua web là lách được, và danh sách cách nói sẽ lộ ra trong bundle công khai.
3. **Gửi chữ cho một mô hình phân loại bên ngoài.** Bị loại. Như vậy là gửi chữ nhạy cảm cho bên thứ ba, trái lời công bố, và thêm chi phí và độ trễ.
4. **Dependency dùng chung chạy trước route (đã chọn).** Có một chỗ duy nhất để sửa luật. Lớp chạy trước kiểm độ dài và không đọc phiên, nên không lộ phiên có tồn tại hay không.

## Hệ quả

- Danh sách viết tay có thể bỏ sót hoặc nhận nhầm. Lời công bố nói đúng như vậy. Số đo tuần 1 nằm trong PR #505:
  - bắt 135/135 câu mẫu, báo nhầm 0/205 câu nghĩa bóng;
  - trên bộ câu viết sau khi chỉnh luật: bắt 30/30, báo nhầm 0/40.
- Câu hỗ trợ dùng chung cho các form không phải Tarot. Câu hỏi về câu riêng cho các form đó vẫn mở, chờ owner.
- Chữ bị chặn không được lưu, không ghi nhật ký và không gửi đi:
  - access log đã tắt;
  - middleware chỉ ghi route và status;
  - response không lặp lại chữ;
  - web không giữ chữ trong storage hay trong history state (bản nháp tên Lá Chứng chỉ nằm trong bộ nhớ của trang).

## Rút lại (rollback)

- Revert PR #505 sẽ gỡ cả lớp chặn lẫn lời công bố trên `/privacy`, vì cả hai nằm trong cùng PR. Không được giữ lời công bố khi đã gỡ lớp chặn: câu đó sẽ hứa một việc app không còn làm.
- Nếu chỉ tắt lớp chặn, phải gỡ `privacy.crisis-check-disclosure` khỏi `/privacy` trong cùng thay đổi, rồi ghim lại `fallback-approval.json`.
- Không có migration, nên rollback không phải xử lý dữ liệu.
