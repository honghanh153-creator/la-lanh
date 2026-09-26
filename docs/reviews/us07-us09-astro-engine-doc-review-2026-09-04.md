# Document review — US-07, US-08, US-09 và Astro Engine v2

> Review date: 2026-09-04 · Mode: non-interactive · Result: applied high-confidence fixes; manual release gates retained.

## Coverage

Personas: coherence, feasibility, product, design, security, scope guardian và adversarial. Review đối chiếu repository hiện tại, PRD/SRS/story map và primary official sources trong Astro Engine Spec.

## Findings đã sửa

| Nhóm | Vấn đề | Cách sửa |
|---|---|---|
| Source of truth | Engine v2 tự nhận authoritative nhưng README/foundation list không có | Thêm engine spec thành tầng “tính thế nào”; PRD/SRS link và migration priority |
| Data model | SRS vừa cấm mọi coordinate vừa cần birth-place coordinate | Tách live GPS (không thu) khỏi encrypted city-centroid phục vụ chart |
| Architecture | “One deployable process” mâu thuẫn worker scale độc lập | Chốt modular-monolith codebase với API + worker processes dùng internal package |
| Native feasibility | App-first DoD nhưng repo chỉ có web/PWA | Ghi hard predecessor: chốt platform/architecture và tạo native target |
| Identity | US-08/09 cần account owner nhưng runtime guest-only | US-19 thành hard prerequisite, yêu cầu atomic guest→account ownership claim |
| Notification | Chưa có outbox/push | Outbox + idempotent in-app inbox là prerequisite; push best-effort, polling fallback |
| Key management | Spec đòi rotation nhưng runtime static single key | KMS/version-aware key provider thành production blocker |
| US-07 switch | Pending/error có thể hiện Western dưới nhãn Jyotish | Thêm atomic async state machine, focus/live announcement và 200% text behavior |
| US-08 share | Share cancel flow mâu thuẫn; có read tracking chưa chốt | Luôn quay lại S39; `Xong` explicit; launch bỏ open/read receipt |
| Capability resend | Hash-only token không thể resend sau restart | Giữ hash + envelope ciphertext, owner-auth decrypt, KMS audit, terminal purge |
| US-09 withdrawal | Secret trong URL; receipt flow thiếu; lost response làm mất quyền rút | Secret body/header + no-store; HttpOnly receipt flow; encrypted recoverable secret cho idempotent retry |
| US-09 scope | Cross-request aggregation làm story phình | Defer aggregation sang social-proof story; US-09 chỉ individual result |
| Engine launch scope | D9/dasha/synastry block core Western+Jyotish | Core two-system launch bắt buộc; D9/Vimshottari/US-12–13 có activation gates riêng |
| Date-only | Không place vẫn nói “full local day UTC” | Dùng timezone đã biết hoặc conservative UTC+14→UTC−12 envelope; không dùng device/server zone |
| Uncertainty | Adaptive samples bị dùng như proof 100% stable | Boundary root-solving; sampled-only luôn `limited`; solver fail thì withhold |
| Reproducibility | Version strings không đủ tái tạo chart | Thêm immutable artifact/build/data/tzdb/rules/serializer manifest + retention |
| Accuracy oracle | `swetest` và production cùng Swiss library nhưng gọi independent | Đổi thành adapter parity; JPL independent body check; expert/second-implementation fixtures cho derived conventions |
| Product outcome | US-07 chỉ đo tap/switch | Thêm comprehension/trust usability target; analytics chỉ là proxy |

## Manual decisions / release gates

1. Chọn iOS, Android hoặc cả hai; native thuần hay native shell. Không có native target ở repository hiện tại.
2. Chọn Swiss Ephemeris AGPL-compatible release hay Professional License trước public deployment.
3. Chọn/provision production KMS và HA topology; 99.9% chưa phải active SLO của local MVP.
4. Domain-expert sign-off cho core Jyotish; D9/Vimshottari có gate riêng khi bật.
5. Legal/privacy review tại Việt Nam, privacy impact/cross-border obligations và Apple/Google declarations theo SDK cuối.
6. Quyết định advanced ayanāṁśa visibility và phạm vi ảnh hưởng của custom Placidus.

## Final document status

- US-07: implementation-ready requirements; blocked for release by engine/native/content gates.
- US-08: implementation-ready requirements; blocked by US-19/native/KMS.
- US-09: implementation-ready requirements; blocked by US-08/US-19/outbox/public-route security evidence.
- Astro Engine v2: implementation contract ready for planning; not production-ready until licensing, golden validation, KMS, native and legal gates clear.

“Ready for planning” does not mean implemented. Current runtime remains the US-01–US-06 web/PWA reference and partial Western engine.
