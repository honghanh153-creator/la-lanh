# Lá Lành — release review US01–US09

Ngày review: 2026-09-07; vòng xác nhận cuối: 2026-09-08  
Phạm vi: app-first React/Capacitor, web/PWA QA companion, API, Astro Engine, Chart Synthesis, privacy và Lá Chứng.

## Kết luận sản phẩm

US01–US09 đã có đường đi end-to-end trên bản QA. Người mới có thể nhận giá trị trước đăng nhập; Vibe chuyển thành Aura sau khi chủ động thêm giờ/nơi sinh; Home, note sâu, lưu/chia sẻ và Bản đồ Lá dùng immutable reading revision; Lá Chứng chỉ yêu cầu owner checkpoint tại thời điểm tạo capability link.

Deterministic reading là sản phẩm hoạt động đầy đủ. Provider sinh prose vẫn là lớp tùy chọn, mặc định tắt và chưa được phép bật production.

## Coverage theo user story

| User story | Trạng thái | Evidence hành vi chính |
|---|---|---|
| US01 — Bắt đầu ở chế độ khách | Đạt | Welcome hai nhịp, consent tách mục đích, chưa cần login, guest session có CSRF và expiry. |
| US02 — Ngày sinh và reveal | Đạt | Field DD/MM/YYYY, validation, Swiss Ephemeris thật, reveal Vibe và provenance date-only. |
| US03 — Note hôm nay | Đạt | Daily Note server-owned, trạng thái loading/error/offline, detail đọc cùng active revision. |
| US04 — Mood check-in | Đạt | Năm mood, selected state, retry và draft pending cục bộ theo session. |
| US05 — Lưu/chia sẻ | Đạt | Save/unsave, queue offline last-intent, safe card/link khóa exact revision, revoke và no-store/noindex. |
| US06 — Bổ sung giờ/nơi sinh | Đạt | Exact/approx/unknown, place suggestion, deep consent, Aura gift, withdrawal xóa dữ liệu và nội dung suy ra. |
| US07 — Insight sâu và chart switch | Đạt | Western/Jyotish, house/ayanamsa settings, full synthesis và từng chapter; config hash tách đúng projection. |
| US08 — Tạo Lá Chứng | Đạt | Owner checkpoint đúng lúc, preview, invite idempotent, label mã hóa, capability hết hạn/thu hồi. |
| US09 — Phản hồi Lá Chứng | Đạt | Public response không login, ẩn danh mặc định, 3–5 statement, receipt/withdraw, result riêng và không đi vào matching. |

## QA đã chạy

- Browser QA thật ở viewport 390 × 844: Welcome → Consent → Birth → Reveal Vibe → Home → giờ/nơi sinh Hà Nội → quà Aura → activate → save/share → Bản đồ Lá Western/Jyotish → calculation settings → Lá Chứng owner checkpoint → Profile dark/light.
- Aura sau unlock đổi rõ source label, headline và nội dung; Home không hot-swap mà yêu cầu người dùng tự mở quà.
- Western/Jyotish cho vị trí và chapter khác nhau; engine tests xác nhận node mode và config-aware projection.
- Home dark/light dùng một font Be Vietnam Pro, không horizontal overflow ở 390px và không có console warning/error.
- Automated: API 193 tests; web 37 tests; contracts, lint, typecheck, runtime/privacy/mobile guards, production build và QA fresh-schema smoke đều pass.

## Lỗi được phát hiện và sửa trong vòng cuối

- Scope projection trước đây có thể trùng giữa hai cấu hình chart; đã thêm `config_hash` vào identity, persistence và migration.
- Mean-node transit từng dùng true node; đã dùng đúng Swiss Ephemeris body 10 theo lựa chọn.
- Activate Aura từng để save/share bám revision cũ; client giờ cập nhật active revision ngay.
- Timeout request, offline asset fallback và việc consent vô tình xóa app-shell cache đã được sửa và có test.
- iOS WebView scheme có dấu/khoảng trắng đã đổi thành ASCII-safe `la-lanh`.
- Lá Chứng đã có create-idempotency, rate limit create/resend, encrypted recipient label, typed owner result và public noindex.
- Xóa guest giờ chặn provider send mới, hủy attempt chưa gửi và chờ attempt đang gửi terminal trước khi báo thành công.
- Profile Aura không còn mô tả sai là chỉ lấy nguồn từ Mặt Trời.
- `GET /birth-profile` có `calculation_kind` tường minh để app phân biệt date-only và natal thay vì đoán theo shape.
- Service worker lấy đúng fingerprinted JS/CSS ngay trong install, nên app-shell của lần cài đầu không phụ thuộc việc bundle đã từng được request qua worker hay chưa.
- Refetch deterministic không còn quảng cáo một bản fallback yếu hơn sau khi người dùng đã chủ động activate generated revision.
- Xóa guest và provider-send cùng khóa guest row trước điểm không thể đảo ngược; thứ tự giao dịch quyết định rõ send hay delete thắng.

## Quyết định với finding không chặn local product

- Danh sách đã lưu chưa thêm cursor trong US01–US09: phiên guest hiện chỉ truy cập tối đa 30 ngày và mỗi ngày một note, nên tải đầu tiên vẫn có chặn tự nhiên. Cursor pagination trở thành requirement trước khi US19 mở lưu trữ tài khoản dài hạn.
- Error body đã thống nhất ở runtime theo `application/problem+json`, nhưng OpenAPI của một số non-2xx route chưa mô tả đủ body. App có fallback an toàn; đây là contract-hardening phải đóng trước khi phát hành SDK/client ngoài, không phải blocker của app local.
- Union date-only/natal được giữ có chủ đích vì app cần current active snapshot; `calculation_kind` là discriminator tương thích ngược cho client.

## Release gate còn mở

1. Chạy migration up/down và multi-worker concurrency trên PostgreSQL disposable; hoàn tất key-aware backfill/purge cho dữ liệu plaintext legacy.
2. Build signed iOS/Android và test đầy đủ trên simulator/device với HTTPS API production-like, safe area, Dynamic Type, VoiceOver/TalkBack và app restart.
3. Chứng minh WAF/distributed limits, capability-token log redaction, key management và store privacy disclosures.
4. Giữ provider production off tới khi DPA/region/subprocessor/retention/ZDR-MAM và benchmark tiếng Việt đạt gate; generated Jyotish tiếp tục off chờ expert sign-off.

## Release posture

- Local QA / product review: **Go**.
- Deterministic product path: **Go sau PostgreSQL + native binary evidence**.
- External generated prose: **No-Go production**.
- Store release: **No-Go cho tới khi ba nhóm evidence hạ tầng/native/privacy hoàn tất**.
