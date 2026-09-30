# Content Studio runbook

## Studio không phải dependency của content engine

Daily và Tarot phải tạo được nội dung đạt chuẩn từ bundled knowledge khi Studio tắt hoặc không có
database release. `ContentReviewAgent` thuộc core backend, không thuộc Studio. Studio chỉ giúp con
người biên tập và phát hành matrix thuận tiện hơn; không có Studio thì các gate và fallback vẫn chạy.

## Mục đích

Content Studio cho phép chủ sản phẩm review và sửa Daily content matrix theo bốn nhóm:
Hành tinh, Cung, Nhà và Góc. Mỗi lần publish tạo một release có hash riêng; note sinh sau
release dùng matrix mới, còn note đã lưu không bị viết lại.

Studio chỉ dành cho local/beta nội bộ. Bản beta dùng bearer token trong bộ nhớ của tab và
ứng dụng chủ động từ chối khởi động Studio ở môi trường `production`.

## Chạy local

1. Tạo token ngẫu nhiên ít nhất 32 ký tự và giữ token ngoài Git.
2. Đặt biến môi trường cho API:

   ```bash
   export LA_LANH_CONTENT_STUDIO_ENABLED=true
   export LA_LANH_CONTENT_STUDIO_API_TOKEN='<token-random>'
   ```

3. Chạy migration và khởi động API/web theo runbook phát triển hiện có.
4. Mở `/studio`, nhập token, rồi chọn một nhóm và một entry để review.

Không truyền token trong URL, ảnh chụp, log hoặc file `.env` được commit. Token chỉ tồn tại
trong React memory và mất khi khóa Studio hoặc reload tab.

## Luồng review an toàn

1. Chọn một entry và đọc theo ba vai trò: câu mở, tình huống đời thường, việc có thể thử.
2. Sửa một ý mỗi lần; không nhét disclaimer hoặc thuật ngữ chart vào nội dung chính.
3. Ghi lý do thay đổi.
4. Chọn **Lưu draft & chạy gate**. Nếu gate chặn, sửa đúng field được nêu; không bỏ gate.
   Gate này render chính catalog của draft trên 10 synthetic personas, không dùng release đang
   active và không dùng dữ liệu người dùng thật.
5. Chỉ chọn **Publish release** khi preview đọc được trong khoảng 10 giây và gate đã qua.
6. Sinh một note mới trong sản phẩm để kiểm tra. Renderer version phải có hậu tố
   `+content-<hash>`.
7. Nếu nội dung giảm chất lượng, dùng **Quay lại bản này** trong lịch sử release.

## Content gate

Publish bị chặn khi:

- thiếu bất kỳ hành tinh, 12 cung, 12 nhà hoặc góc bắt buộc nào;
- field sai schema, danh sách rỗng, nội dung quá ngắn hoặc quá dài;
- có HTML/markup;
- dùng câu trừu tượng đã loại bỏ như “pattern này”, “tín hiệu vũ trụ”,
  “điều đang chạy bên dưới” hoặc “một cách khác để thử”;
- nhét disclaimer vào nội dung chính.
- dùng câu dịch máy hoặc cụm mơ hồ như “giữ nhịp”, “mở một góc”, “cơ chế này”, “vùng mờ”;
- tình huống không có dấu hiệu quan sát được hoặc gợi ý không có hành động cụ thể;
- câu quá dài, câu lặp hoặc hai synthetic personas cho cùng một nội dung lõi.

## Privacy và security

- Studio không nhận guest ID, profile ID, ngày/giờ/nơi sinh, mood, câu hỏi Tarot hoặc dữ
  liệu Radar.
- Preview hiện tại chỉ dùng chính entry đang sửa; không đọc dữ liệu người dùng thật.
- Endpoint dùng `no-store`, `noindex`, `no-referrer` và `DENY` framing.
- API xác thực trước khi parse body và dừng đọc request chunked ngay khi vượt 256 KB.
- Public API không có route Studio khi `LA_LANH_CONTENT_STUDIO_ENABLED=false`.
- Mọi publish dùng optimistic generation và idempotency key để tránh hai người ghi đè nhau.

## Trước khi bật trên production

Không bật bản beta hiện tại. Cần hoàn tất các điều kiện sau:

- tách Studio thành app/origin riêng;
- thay bearer token bằng Supabase Auth, MFA và operator allowlist;
- session HttpOnly Secure, CSRF và exact-Origin validation;
- DB role riêng cho runtime, Studio và migration;
- append-only/immutable trigger cho release và audit events;
- preview bằng bộ synthetic personas, không dùng dữ liệu thật;
- security review, privacy review và rollback drill.

Không downgrade migration sau khi đã có release. Migration sẽ từ chối xóa bảng lịch sử; rollback
ứng dụng theo hướng forward và giữ nguyên dữ liệu audit.

## Kiểm tra sau mỗi lần thay đổi

```bash
pnpm content:review
pnpm tarot:audit
UV_CACHE_DIR=/tmp/uv-cache uv run --directory apps/api pytest tests/content tests/api/test_content_studio.py
UV_CACHE_DIR=/tmp/uv-cache uv run --directory apps/api ruff check app/domains/content app/api/v1/routes/content_studio.py
pnpm --filter @la-lanh/web lint
pnpm --filter @la-lanh/web typecheck
pnpm --filter @la-lanh/web build
```
