# Security & privacy review — Lá Lành US01–US09

Ngày chốt: 2026-09-07  
Scan ID: `62990c73-fb6f-44e5-8cb5-fb107fa19055`  
Phạm vi: API, React/Capacitor client, migrations, QA server, public capability links và chart-synthesis provider boundary.

## Kết luận

Không còn finding bảo mật có thể báo cáo trong snapshot đã scan sau vòng hardening. Kết quả này **không đồng nghĩa production release-ready**: coverage là partial vì chưa có hạ tầng production, PostgreSQL runtime và signed native binaries để kiểm chứng.

Scan cũng ghi nhận working tree tiếp tục thay đổi trong quá trình review. Vì vậy full regression và code review cuối của current tree vẫn là gate bắt buộc, không được dùng riêng security receipt này để phát hành.

## Controls đã đóng

- Session guest/owner, CSRF và ownership được kiểm tra ở mutation boundary.
- Birth compute được dedupe theo input hash, giới hạn compute slot và có admission backstop.
- Daily, saved và share personalized snapshots được bọc AES-GCM với AAD theo record; write mới không để prose trong cột plaintext cũ.
- Xóa giờ/nơi sinh sẽ hạ precision và purge note/save/share/plan/revision/projection/attempt phụ thuộc; snapshot date-only được giữ để người dùng không phải bắt đầu lại.
- Provider generation mặc định tắt, chỉ nhận allowlisted derived plan, `store=false`, không raw birth/coordinates/identity/free text và không tự activate output.
- Xóa guest dùng protocol hai pha: worker và delete cùng serialize trên guest row, khóa session sang `deleting`, hủy job chưa gửi, chặn send marker mới và chỉ trả thành công sau khi job đang gửi đã terminal; lỗi bất ngờ sau send marker bị đóng `ambiguous`, không retry.
- Public share/Lá Chứng có token shape validation, expiry, revoke, dedupe, receipt TTL và response headers `no-store`, `no-referrer`, `noindex`.
- QA/dev bind loopback, database tách biệt và access log tắt; custom QA port tự cập nhật CORS origin.
- Native config fail closed nếu thiếu HTTPS API `/v1`, chặn cleartext/mixed content và external WebView navigation.

## Ba release gate còn mở

1. Chạy migration up/down, duplicate preflight và lease/CAS concurrency trên PostgreSQL disposable; kiểm chứng KMS rotation và legacy encrypted-snapshot backfill.
2. Build signed iOS/Android, test create guest → birth → Daily → Aura → save/share → delete trên simulator/device; kiểm chứng secure storage, restart, expiry, deep link và platform accessibility.
3. Xác minh edge/WAF distributed admission, redaction capability token ở mọi lớp access log, production cookie/domain/TLS và provider DPA/region/subprocessor/retention/ZDR-MAM trước khi bật generation.

## Release posture

- Local web QA: được phép dùng để nghiệm thu hành vi và visual reference.
- Deterministic engine: là đường sản phẩm hoàn chỉnh, không phụ thuộc provider.
- Provider generation: production off.
- Generated Jyotish: off chờ expert corpus/sign-off.
- Native production: No-Go cho tới khi ba gate trên có evidence thật.

## Canonical scan artifact

Report sealed nằm tại:

`/private/var/folders/dh/my7pp465325dcfxnznhylvkr0000gn/T/codex-security-scans-vWEetR/la-lanh/dde8ff1dae6b03a943619c1e506e17836b380223_20260907T090105Z_oyf5o73k/report.md`
