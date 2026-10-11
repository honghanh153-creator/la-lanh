# Tài khoản, IAM và thời hạn dữ liệu

Ngày: 2026-10-10. Trạng thái: triển khai và kiểm thử local; **chưa deploy, chưa bật Google/OTP thật**.
Plan: [optional login và data continuity](../plans/2026-10-10-1310-fix-optional-login-and-data-continuity-plan.md).

## Người dùng phải thấy gì?

Không cần đăng nhập để đọc note, Tarot hoặc dùng chart. Welcome có đúng hai CTA vào app: **Đồng ý & bắt đầu** và **Đăng nhập**. Nút đầu tiếp tục hồ sơ hợp lệ trên máy; chỉ tạo khách nếu không có phiên hợp lệ. `restart=1` không đổi owner. Không có bản mẫu hay nút làm hồ sơ khác. Nút đăng nhập dùng Google; đây là lựa chọn giữ hồ sơ khi đổi máy, không phải điều kiện sử dụng core feature. Lỗi mạng không xoá hồ sơ.

| Đối tượng | Thời hạn | Điều làm gia hạn |
|---|---|---|
| Hồ sơ khách | 30 ngày không hoạt động | Dùng tính năng riêng tư với phiên hợp lệ |
| Hồ sơ tài khoản | 365 ngày không hoạt động, cần đồng ý riêng | Dùng phiên tài khoản hợp lệ |
| Phiên từng thiết bị | 30 ngày không hoạt động | Chính thiết bị đó dùng tính năng riêng tư |
| Lịch sử tự động | Tối đa 30 ngày từ lúc tạo | Không gia hạn khi mở lại hoặc đăng nhập |
| Chart, bản đọc hiện tại, note đã lưu | Theo thời hạn hồ sơ | Không bị thao tác xoá lịch sử lấy đi |

Hồ sơ cũ không tự bị bật chính sách lịch sử mới. Sau khi người dùng đồng ý, có đủ 30 ngày trước lần dọn đầu tiên. Dọn vật lý có khoảng dự phòng 6 giờ; phải chạy cleanup ít nhất mỗi 6 giờ. Không dùng việc xem link public hoặc worker để gia hạn hồ sơ.

## Nguồn quyền hạn nằm ở backend

`Cookie HttpOnly → digest của credential → thiết bị/account → data owner`.

Supabase xác minh Google SSO bằng PKCE. Backend chỉ dùng subject UUID đã xác minh, email đã xác nhận và identity Google; không tin `user_metadata.role`, email do client tự khai, `guest_id`, hay principal ID trong payload để cấp quyền. Không đưa access/refresh/provider token xuống browser. Không giữ mật khẩu hoặc khoá service-role ở frontend. API email OTP cũ còn để tương thích nhưng UI hiện tại chỉ có Google; bật Google không tự bật OTP.

Giữ guest ID làm data owner khi liên kết lần đầu; không chuyển các foreign key hoặc chép chart sang hồ sơ mới. Credential khách cũ bị vô hiệu hoá một lần. Mỗi lần đăng nhập thêm tạo credential thiết bị độc lập; không làm các máy khác mất phiên.

Nếu tài khoản đã có hồ sơ, phải xác nhận **mở hồ sơ tài khoản đó**. Không tự merge hồ sơ khách đang mở, DOB hoặc consent AI. Xoá hồ sơ là trạng thái cuối: đăng nhập lại không phục hồi chart đã xoá.

## Các tác vụ IAM

| API | Quyền và kết quả |
|---|---|
| `GET /v1/account` | Trạng thái của credential hiện tại, email che bớt; không tra email người khác |
| `POST /v1/account/login/google` | Origin + CSRF + consent lưu tài khoản; PKCE verifier mã hoá, state/cookie gắn credential khởi tạo; trả authorize URL cố định |
| `POST /v1/account/login/google/verify` | Code + state nonce; consume verifier trong DB trước exchange; một lần duy nhất, không tự merge account cũ |
| `POST /v1/account/login/code` | Trusted Origin + CSRF nếu đang có phiên, consent lưu tài khoản riêng; hạn mức bền vững trong DB |
| `POST /v1/account/login/verify` | Mã 6 chữ số, nonce/challenge ngắn hạn gắn với credential khởi tạo; một verifier thắng |
| `POST /v1/account/login/restore` | Proof một lần + xác nhận rõ; không cấp cookie trước xác nhận |
| `POST /v1/account/login/cancel` | Huỷ challenge; giữ hồ sơ/phiên khách |
| `POST /v1/account/logout` | Thu hồi thiết bị hiện tại, xoá cookie sau commit; không xoá account/chart/máy khác |
| `GET /v1/account/devices` | Chỉ phiên tài khoản hợp lệ; chỉ liệt kê thiết bị của chính account |
| `POST /v1/account/devices/{id}/revoke` | Trusted Origin + CSRF; ID account khác trả 404; thu hồi máy hiện tại thì xoá cookie |
| `POST /v1/account/devices/revoke-others` | Thu hồi tất cả máy khác, giữ credential hiện tại và hồ sơ |
| `POST /v1/session/birth-profile-consent` | Đồng ý purpose sinh cơ bản trên đúng phiên đang mở; không cấp consent AI hay quyền operator |
| `POST /v1/session/history-retention` | Đồng ý thời hạn lịch sử riêng; idempotent, không reset ngày kích hoạt |
| `DELETE /v1/session/history` | Xoá lịch sử được xác định, không xoá chart/current/Saved; từ chối tạm thời nếu đang có provider-send cần giữ fence |

Danh sách thiết bị chỉ trả ID thu hồi, cờ máy hiện tại và các mốc thời gian. Không trả digest, credential, subject, tên/email đầy đủ, IP, user-agent hay dấu vân tay máy. UI quản lý nhiều thiết bị chưa nằm trong đợt này; API IAM đã có để bổ sung UI sau.

Khách chỉ consent Tarot không được persist DOB cho đến khi đồng ý purpose sinh. Bấm submit DOB có thông báo mục đích và ghi receipt riêng trước khi tính chart. Xác minh thêm tài khoản không tự chấp thuận các mục đích còn lại.

## Chống lỗi và lạm dụng

Google callback chỉ nhận tại trusted origin `/auth/callback` (HTTPS trên staging/production). State nằm trong redirect của Supabase; verifier không ra browser. Challenge hết hạn sau 10 phút, còn code của Supabase có hạn 5 phút và dùng một lần. Callback scrubs code/state/error khỏi URL; proof chỉ còn trong memory, không localStorage/history/log. StrictMode dùng cùng promise exchange; lỗi/refresh yêu cầu bắt đầu lại. Callback ở máy/cookie khác, cancel, replay hoặc provider thất bại không thay owner. Bắt đầu login mới sẽ vô hiệu challenge đang hiển thị trên browser đó; không hỗ trợ hai login song song.

- Digest domain-separated; email challenge được mã hoá ngắn hạn, scrub khi kết thúc.
- 5 lần thử/challenge, 10 phút; resend tối thiểu 60 giây. Quota send theo email/peer/toàn hệ thống là 5/10/100 mỗi giờ; verify là 30/120/1000 mỗi giờ.
- Provider call ngoài transaction; DB ghi verifier claim trước khi gửi. Finalize lock subject, owner theo thứ tự, rồi challenge; recheck sau lock. Không dùng mutex trong một process làm nguồn quyền hạn.
- Thu hồi thiết bị lock owner rồi device; logout/revoke/restore/erase dùng cùng thứ tự. Credential đã thu hồi không authorize yêu cầu tiếp theo, kể cả replay cookie cũ.
- Discovery trước lock chỉ đọc ID scalar. Reread owner/device sau lock phải refresh ORM state; không authorize bằng object đã cache trước khi chờ revoker commit. Regression PostgreSQL giữ owner lock, cho private reader chờ, commit revoke rồi bắt buộc reader trả unavailable.
- Account thường không được truy cập Content Studio. Operator vẫn dùng cơ chế độc lập; không thêm role admin cho account.
- Tất cả API `/v1/` trả `no-store`; cookie renewal không đổi giá trị CSRF. Client gia hạn cookie khi kiểm tra `/session` tại SessionBoundary hoặc lúc vào tính năng. Không nối thêm renewal sau mỗi mutation riêng tư, để lỗi mạng ở renewal không biến một lần xoá/tạo đã được xác nhận thành lỗi. Yêu cầu ghi cookie vẫn phải drain dưới fence chung giữa các tab; không thả fence khi timeout để tránh cookie đến muộn ghi đè phiên mới.
- Client chặn response của owner cũ khi đổi phiên, kể cả response đã đến nhưng chưa decode JSON. Chỉ allowlist các chuyển cookie sau login/logout thành công và `/session` 401 hết hạn đã xoá cookie; vẫn kiểm tra generation/epoch.
- Legacy owner binding phải claim lại khi thời hạn hết, không chỉ khi session epoch đổi. Hết owner credential không đồng nghĩa mất dữ liệu account.
- Xoá lịch sử không miễn trừ tác vụ `pending`, `retry_wait` hoặc lease chưa gửi. Xoá plan dưới owner lock cascade các attempt chưa gửi; worker giữ lease cũ phải thất bại ở send-boundary recheck. Provider-send đã bắt đầu vẫn làm clear tạm từ chối; backlog vẫn phải đếm lịch sử đang bị fence, không báo sạch khi còn dữ liệu.

## Gate trước khi bật đăng nhập thật

1. Cấu hình Google OAuth trong Supabase, Google authorized redirect trỏ callback của Supabase, và Supabase redirect allowlist trỏ đúng callback web. Không dùng wildcard rộng. `auth_google_callback_url` phải khớp CORS origin. Google client secret chỉ ở Supabase, không ở FE/repo. Chưa kiểm thử thật thì giữ `auth_enabled=false`, `auth_google_enabled=false`. SMTP không là điều kiện của Google; nếu bật API email cũ thì vẫn cần gate SMTP/OTP riêng và `auth_delivery_approved=true`.
2. Đã có adapter xoá cứng danh tính Supabase cho tài khoản đã liên kết; cần secret key riêng trên server và kiểm thử provider thật trước khi bật. Hồ sơ chuyển DELETING trước cuộc gọi; lỗi provider giữ liên kết để cleanup thử lại và trả pending, không báo đã xoá. Chỉ sau 200/204 hoặc 404 idempotent mới cascade hồ sơ/thiết bị local. Không xoá tài khoản Google. Hủy login không tự xoá danh tính chưa liên kết hoặc danh tính đang dùng ở máy khác.
3. Rehearsal migrations `0031 → 0032 → 0033 → 0034 → 0035`, grants/RLS và application DB role trên môi trường triển khai; không suy ra từ test superuser local rằng role live đúng. 0033 bổ sung provider/verifier; 0034 thêm durable send/drain; 0035 pin trigger search_path. Rollback giữ schema/data và tắt flag thay vì drop cột.
4. Kiểm tra trusted proxy peer, cron cleanup/drain/backlog, backup có thời hạn và rollback không phục hồi credential đã thu hồi.
5. Kiểm thử hai tài khoản Google/hai máy thật, consent/restore/cancel/logout/revoke/erase. Callback trong Capacitor/iOS/Android cần acceptance riêng; web flow không chứng minh native SSO. Không gọi HTTP mock là proof Google đã hoạt động live.
6. Không bật paid rewrite để test auth. Không thay khoá hoặc ngân sách hiện tại; không phát sinh phí mới trong đợt local này.

Nguồn tham chiếu: [Supabase OTP](https://supabase.com/docs/guides/auth/auth-email-passwordless), [SMTP](https://supabase.com/docs/guides/auth/auth-smtp), [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html). Đây là thiết kế kỹ thuật, không phải chứng nhận pháp lý hay cam kết không thể có lỗ hổng.

Google references: [Google provider](https://supabase.com/docs/guides/auth/social-login/auth-google), [PKCE](https://supabase.com/docs/guides/auth/sessions/pkce-flow), [server-side auth](https://supabase.com/docs/guides/auth/server-side/advanced-guide). Xem [release review hợp nhất](../reviews/2026-10-10-content-google-consolidated-release-review.md) để phân biệt kiểm thử local và gate live chưa hoàn tất.
