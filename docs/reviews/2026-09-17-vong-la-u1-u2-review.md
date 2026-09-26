# Review: Vòng Lá foundation và readiness

Ngày: 2026-09-17  
Plan: `docs/plans/2026-09-17-vong-la-product-completion-plan.md`  
Phạm vi code review: matching domain/API/migration, `/vong-la`, API contract và navigation.

## Intent

Đặt nền cho Vòng Lá bằng dữ liệu và quyền thật: chỉ tạo owner identity khi người dùng chủ động vào social matching; profile và matching consent tách riêng; pool membership fail-closed khi thiếu birth profile, age eligibility hoặc verification; app hiển thị mọi chốt thay vì giả candidate hay giả trạng thái đã duyệt.

## Fixes applied during review

1. Bổ sung `gender_identity` tự khai và lựa chọn phi nhị nguyên để reciprocal preference có thể được tính đúng; không suy giới từ tên, ảnh hoặc chart.
2. Mã hóa `display_name` ở application layer trước khi ghi database và thêm test chứng minh plaintext không được lưu.
3. Serialize profile/consent mutations bằng principal row lock để tránh duplicate profile hoặc hai active consent khi request đồng thời.
4. Giữ consent history bất biến: mỗi lần đồng ý lại tạo record mới; partial unique index chỉ cho một consent active, thay vì xóa dấu vết revoke cũ.
5. Chạy các read độc lập của readiness song song để giảm số round-trip nối tiếp mà không bỏ safety check.
6. Đổi copy “tài khoản” thành “xác nhận thiết bị” vì owner claim hiện tại chưa phải phone/email OTP và không được phép khiến người dùng hiểu sai.

## Actionable Findings

| # | Severity | Location | Finding | Required response |
|---|---|---|---|---|
| 1 | P1 | `docs/user-stories/US-19-xac-thuc-khi-can.md:16` | Hard auth cho matching vẫn chưa có phone/email OTP, merge guest/account và account recovery. Device-bound owner claim chỉ đủ cho internal QA. | Chọn OTP provider, lưu identifier dạng normalized + protected hash/encryption, thêm anti-enumeration/rate limit và merge flow trước public beta. |
| 2 | P1 | `docs/user-stories/US-14-chuan-bi-profile-matching-ready.md:25` | Photo verification/moderation provider chưa được nối. Runtime hiện fail-closed và không có auto-pass; vì vậy user thật chưa thể active pool. | Chọn private object storage + verification/moderation process/provider, retry/appeal và SLA 24h. |
| 3 | P1 | `docs/plans/2026-09-17-vong-la-product-completion-plan.md:146` | U3-U6 chưa triển khai: weekly slate persistence/UI, request/mutual, Lá Nối/chat và recap. Relationship selector chỉ là nền computation. | Thực hiện tuần tự U3 -> U6 sau khi auth/verification seams được khóa. |
| 4 | P2 | `scripts/sync-mobile.mjs:5` | Mobile sync cố ý chặn API URL không phải HTTPS; workspace chưa có URL API staging/production thật nên build mới chưa được copy vào iOS/Android shell. | Cấp `VITE_API_BASE_URL=https://.../v1`, sau đó chạy `pnpm mobile:sync` và simulator smoke. |
| 5 | P1 | Release operations | Chat/UGC chưa được phép launch nếu thiếu community rules, report queue, block và contact hỗ trợ. | Hoàn thành U5 và moderation runbook trước khi bật matching ngoài internal QA. |

## Requirements Completeness

- [x] Profile matching, weekly intent, coarse region và consent riêng có persistence thật.
- [x] Owner authorization, CSRF, no-store và fail-closed pool membership.
- [x] Verification state model không có production auto-pass.
- [x] Cosmic Glass app screen, 5-item navigation, light/dark compatible, mobile viewport QA.
- [ ] US-19 OTP account và guest merge.
- [ ] Verification upload/provider/moderation.
- [ ] U3 weekly slate/card persistence và card UI.
- [ ] U4 request/mutual/Lá Nối.
- [ ] U5 safe chat/report/block/unmatch.
- [ ] U6 recap/share/return loop.
- [ ] U7 native sync/simulator/store readiness.

## Security, privacy và store coverage

- Apple UGC policy yêu cầu filter, report, block và contact; account creation phải có in-app deletion. Guest deletion hiện cascade sang principal/matching rows, nhưng chat/report chưa tồn tại nên release gate vẫn mở.
- Google Play UGC yêu cầu terms, ongoing moderation, report và block; matchmaking phải có robust age gate và không target trẻ em.
- Matching endpoints không trả principal id, raw chart, birth date/time/place, GPS hoặc compatibility scalar.
- Coarse region/intent/gender vẫn là personal data cần database access control, backup encryption, retention và audit ở deployment layer.

## Coverage

- 279 API tests passed; matching includes auth timing, CSRF, explicit consent, fail-closed pool, encrypted display name và consent history.
- 69 web tests passed; matching includes just-in-time identity gate và explicit consent behavior.
- Ruff, mypy (185 source files), ESLint, TypeScript, OpenAPI contract, runtime mock/privacy/mobile guards passed.
- QA CLI, fresh schema, API proxy, SPA deep-link và production web build passed.
- Manual browser QA at 390x844 passed with no console warning/error; navigation has five readable items.
- iOS/Android sync not run because a real HTTPS API base URL is intentionally required.

## Verdict

**Not ready for public matching.** U1-U2 are suitable as an internal, fail-closed foundation and review surface. The next blocking order is: real US-19 authentication -> verification/moderation -> U3 weekly slate -> U4 mutual -> U5 safety/chat -> U6 recap -> native/store release gate.

Actionable findings: #1, #2 and #5 are launch blockers; #3 is the planned product completion path; #4 needs deployment input rather than a code workaround.

