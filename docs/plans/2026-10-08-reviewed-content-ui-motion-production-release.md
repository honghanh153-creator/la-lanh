# Phát hành content direct, Ultraviolet Paper và motion

Ngày: 2026-10-08. Người dùng yêu cầu rà content/UI/animation, plan rồi đưa lên production.

## Kết quả cần đạt

URL public đang có phải phục vụ bản mới đã kiểm chứng, không chỉ screenshot hoặc QA local. Home có Note đầu màn, nội dung direct có một cảnh và một việc nhỏ phù hợp; màn đọc thêm/chia sẻ giữ cùng context. UI cream/purple planetary surface đồng nhất. Onboarding có giờ/nơi sinh tùy chọn, không khóa đường bỏ qua. Animation lặp có pause và Reduced Motion.

## Phạm vi nguồn

Đóng gói các thay đổi sản phẩm đã chốt trong working tree: backend content/rewrite gates, frontend/routes/theme/birth input, asset Ultraviolet, các test/doc tương ứng và cấu hình triển khai rewrite worker mặc định tắt. Không đưa bản ideation chưa chốt vào runtime. Không triển khai CMS public, marketplace/matching mới, app store, model rollout hoặc tăng ngân sách.

Contract nền: US-01/02/03/06; `docs/plans/2026-10-07-direct-daily-meaning-brief-plan.md`; `docs/plans/2026-10-07-optional-birth-details-planet-surface.md`; `docs/reviews/home-motion-2026-10-08/qa-receipt.md`; release runbook, content và UX gates.

## Plan theo thứ tự

1. Inventory git và production không đọc secret. Chốt rollback image/source, đủ disk/RAM, timers. Xác nhận SSH, public source và generation đang tắt.
2. Rà diff content/context/revision, giờ sinh/consent, theme và animation. Kiểm tra 10 persona tổng hợp qua reviewer, không gọi là thử với 10 người thật. Sửa lỗi blocking nếu có; không nới gate cho qua.
3. Chạy complete repository gates, TypeScript/Python, unit/API, native asset/license, shell syntax. QA browser 360/390px cho first-run → Home → Note, birth optional, Radar/Tarot và pause. Lưu bằng chứng, limitation.
4. Commit đúng file sản phẩm, public nguồn AGPL trước khi deploy. Archive từ immutable commit, không copy worktree/env/db/cache. Chuyển lên VPS và kiểm checksum.
5. Copy cấu hình server không bí mật; giữ generation/worker/public Studio tắt. Không rotate keys hoặc nâng cấp dịch vụ. Build image, TLS DB probe, reviewer trong image, migration/readiness rồi mới chuyển container.
6. Public smoke HTTPS/SPA/headers; browser first-run tổng hợp và Home mới, pause/context/detail/Tarot/Radar. Không dùng dữ liệu thật. Chỉ xóa dữ liệu QA do chính lần kiểm tra này tạo; không đụng người dùng khác.
7. Chốt current pointer, timers, immutable image/source và rollback. Lưu receipt/checklist future-session; báo URL và những giới hạn chưa kiểm chứng.

## Điều kiện Go / No-go

Không phát hành nếu tests/content reviewer fail; secret hoặc dữ liệu cá nhân đi vào source/URL/log; thiếu consent/owner scope; paid worker tự bật; image readiness lỗi; source không public; UI mất CTA/blank/tràn ngang nghiêm trọng. Không downgrade database. Nếu smoke lỗi, rollback app image tương thích, không phục hồi dữ liệu tùy tiện.

## An ninh và privacy

Giữ owner session/CSRF, TLS, secret files, no-access-log, capability no-store/no-referrer, native credential guard. Thu giờ/nơi sinh tùy chọn với consent riêng; không GPS/address mới. Brief AI là copy biên tập, không thêm dữ liệu cá nhân, không bật gửi provider. Preflight phát hiện bảng backend có quyền Data API: đã bật RLS, thu hồi quyền `PUBLIC`/`anon`/`authenticated`, khóa default grants; migration 28 và gate kiểm chứng giữ trạng thái này cho các lần deploy sau. Backend giữ quyền hiện có, không đổi dữ liệu/secret/firewall. Không chi phí mới ngoài hạ tầng đã mua.

## AC / DoD

- Full check và reviewer 10 persona pass; không còn known P0/P1 trong phạm vi đã rà.
- Public Welcome → Birth → Reveal → Home → Note hoạt động; tùy chọn/skip không chặn.
- Home direct + đúng context ở detail/share; layout và animation đúng bản đã chốt, có pause toàn bộ decoration.
- Tarot và Radar vẫn đi được từ Home; form giờ sinh hỗ trợ unknown.
- Healthy image/readiness, source public, HTTPS/headers/migration/timers có bằng chứng và rollback anchor.
- Không gọi paid model; chưa test thiết bị thật, human study hoặc AI scoring phải ghi rõ, không suy thành đã hoàn thành.

## Nguồn chính thức đã rà

[WCAG Pause, Stop, Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html), [OWASP MASVS privacy minimization](https://mas.owasp.org/MASVS/controls/MASVS-PRIVACY-1/), [Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://vanban.chinhphu.vn/?docid=214590&pageid=27160). Đây là checklist kỹ thuật, không phải chứng nhận tuân thủ pháp luật.

## Theo dõi thực hiện

- [x] Đã xác nhận production image cũ `la-lanh:3798652ed4a3`, source tương ứng, timers active, disk còn 27GB; SSH key hoạt động.
- [x] Gates và review: 191 web + 519 API tests, full `pnpm check`, native guard; 10 synthetic persona/30 bản đọc, không critical/high; 36 Tarot medium follow-up còn mở. Browser Home 360/390px không tràn ngang, context Work ở detail/share khớp, 4 decoration pause được. Supabase guard đã áp dụng lên 29 bảng hiện có, kiểm chứng isolation pass.
- [ ] Source public và archive.
- [ ] Image/build/readiness + deploy.
- [ ] Public browser/smoke + release receipt.
