# Data inventory — US07–US09

Ngày rà soát: 2026-09-12. Phạm vi: Bản đồ Lá, reading knowledge, Moon Field Notes, Lá Chứng, public response và native wrapper.

| Data | Mục đích | Nơi xử lý/lưu | Chia sẻ | Retention | Quyền người dùng |
|---|---|---|---|---|---|
| Ngày/giờ/nơi sinh | Tính natal chart theo cấu hình được chọn | API; input mã hóa AES-GCM; không đưa vào URL/analytics/WebView storage | Không | Tới khi người dùng xóa profile | Xem trạng thái, sửa, xóa |
| Derived chart snapshot | Tạo reading/provenance | API; new writes dùng AES-GCM envelope, client chỉ nhận projection cần thiết; legacy nullable JSON chỉ để migration | Không | Theo profile/version | Recompute, xóa cùng profile |
| Moon reading projection | Giải nghĩa sign cùng house/aspect đủ điều kiện | Tạo deterministic từ factor refs; chỉ render trong private owner session; trạng thái accordion/bookmark chỉ ở memory | Không | Không tạo bản sao mới trong browser storage | Xem evidence theo chủ động; xóa cùng profile |
| Reading plan + knowledge provenance | Chọn tổ hợp natal/house/aspect/degree/transit và truy vết bản diễn giải | Plan được mã hóa server-side; giữ `config_hash`, factor refs, local-date editorial seed và `knowledge_version`; knowledge catalog là static code không chứa PII | Không | Theo revision/profile; xóa cùng profile | Mở evidence, kích hoạt revision mới, xóa cùng profile |
| Provider ReadingPlan allowlist | Viết lại candidate tiếng Việt khi feature flag + governance cho phép | Chỉ derived factor labels/roles/confidence/composition; không raw birth, tọa độ, ID hay free text; `store=false` nhưng provider retention vẫn là gate riêng | OpenAI chỉ sau governance | Theo hợp đồng/DPA và ZDR/MAM được chứng minh | Tắt provider vẫn dùng deterministic; khi xóa, app hủy job chưa gửi và chờ job đã gửi terminal trước khi xác nhận; dữ liệu provider đã nhận vẫn theo retention/DPA riêng |
| Chart preference | Nhớ hệ đọc US07 | Server/query memory; không ảnh hưởng Daily Note/matching | Không | Tới khi reset/xóa profile | Đổi/reset |
| Recipient label + context | Giúp owner nhận biết một lời mời | API; label mới dùng AES-GCM envelope với AAD gắn `request_id`, context là enum tối thiểu | Hiển thị tối thiểu cho người có capability hợp lệ | 7 ngày hoặc đến delete | Sửa trước issue, revoke/delete |
| Capability token | Mở đúng public request | Plaintext chỉ trong initial link/transient resend; hash + encrypted envelope server-side | Người gửi chủ động chia sẻ | Purge khi terminal/TTL | Resend, replace, revoke |
| Statement selections | Trả lời Lá Chứng | API, từng response riêng | Chỉ owner của request | Withdrawal/retention policy | Recipient withdraw; owner hide/delete |
| Alias | Optional identity | API khi opt-in; sanitize, cấm contact solicitation | Owner của request | Cùng response | Không nhập/withdraw |
| Receipt credential | Anonymous withdrawal | HttpOnly narrow-path cookie; hash + bounded ciphertext server-side | Không | Tối đa 7 ngày và không vượt quá TTL của lời mời | Withdraw, tự hết hạn |
| Safety report | Chống spam/lạm dụng Lá Chứng | API; request id + reason allowlist, không IP/device/alias | Chỉ moderation nội bộ trong tương lai | Theo abuse/legal policy đã duyệt | Không dùng cho matching/profile |
| Native CSRF token | Cho phép mutation từ Capacitor mà không lộ session credential cho JavaScript | Token anti-forgery không phải authentication được giữ trong app local storage; guest/owner credential vẫn là cookie `HttpOnly` | Không | Theo guest session; xóa khi delete/clear device data | Tự xóa cùng dữ liệu cá nhân |
| Native guest/owner session | Duy trì guest-first và ownership trong app | Cookie `HttpOnly`, `Secure` production, domain API tường minh để native HTTP cookie jar gắn đúng host | Không | Tối đa 30 ngày, rotate/revoke theo session | Delete guest/revoke; không lưu credential trong localStorage/Preferences |

## Prohibited surfaces

- Không raw birth data, capability/receipt secret, alias hoặc statement content trong product analytics, crash payload, referrer, browser storage hay push payload.
- Không gửi raw degree, factor plan, reading text hoặc editorial seed vào analytics/log. `editorial_seed` chỉ là ngày local của scope, không phải ID người dùng.
- Public capability routes không third-party tracker, dùng `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex, nofollow, noarchive` và CSP.
- Lá Chứng chỉ nhận capability đúng định dạng, chỉ nhận báo cáo khi lời mời còn pending/chưa hết hạn, và dedupe `(request_id, reason)` ở cả service lẫn unique index để chống spam/retry race.
- API có admission backstop theo peer đã băm cho guest creation, chart compute, Lá Chứng create/resend và public capability routes; production vẫn cần distributed edge limit vì bộ đếm trong process không bao phủ nhiều replica.
- Invite create lưu keyed idempotency identity gắn owner cùng keyed draft hash; retry chỉ trả lại request/link pending còn hạn và cùng draft. Key client không được lưu plaintext.
- Không lưu native session credential trong Capacitor Preferences/localStorage. Bản hiện tại dùng cookie jar `HttpOnly`; vẫn phải hoàn tất simulator/device evidence và đánh giá Keychain/Keystore trước external release.

## Release blockers

- KMS/keystore-backed envelope key và rotation chưa được cấu hình.
- Production identity/recovery, domain association, code signing và store privacy forms chưa hoàn tất.
- Complete chart rows hiện hữu cần encrypted migration rehearsal hoặc purge/recompute được phê duyệt.
- Daily/saved/share rows cũ cần key-aware backfill hoặc purge trước khi bỏ các cột plaintext tương thích; downgrade sẽ chủ động từ chối nếu còn ciphertext chưa được phục hồi.
- `la_chung_requests.recipient_label` cũ tiếp tục read-compatible sau migration `20260907_0014`. Trước production, job có quyền dùng envelope key phải mã hóa từng label với AAD `la-chung-recipient-label:{request_id}`, đọc/đối chiếu lại, ghi audit count, rồi mới xóa plaintext trong một bước riêng. Không được SQL-wipe hoặc drop cột khi chưa xác minh key version, decrypt round-trip và backup/rollback policy.
- Hosting phải chứng minh `_headers` thực sự được áp dụng; capability path phải bị redact trước CDN/WAF/app logs.
- Production API phải bật `native_app_enabled=true`, khai `cookie_domain` đúng API host và kiểm tra end-to-end create/resume/mutate/delete trên iOS + Android; source-level guard không thay thế binary evidence.

Store-facing disclosure mapping and the conditional external-generation gate are maintained in `docs/legal/store-privacy-data-map.md`.
