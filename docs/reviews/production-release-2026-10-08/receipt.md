# Production release — 2026-10-08

## Trước phát hành

Rollback anchor: `la-lanh:3798652ed4a3`; source `/opt/la-lanh/releases/3798652ed4a3/source`.
Public URL: <https://la-lanh.2-28-136-44.sslip.io/welcome>.

- Full `pnpm check`: 191 web tests, 519 backend tests, lint/typecheck/contracts/runtime/privacy/native assets, QA CLI E2E pass. Native guard 4 tests pass separately.
- Offline content reviewer: 10 synthetic personas, 30 readings, zero critical/high; 36 medium findings are Tarot repeated sentences across sections. These are not ten human usability interviews.
- Content matrix audit: 630 daily variants, 23 relationship concepts, 8 Radar themes; Tarot audit: 78 cards × 6 contexts; rewrite manifest: 670 cases/13 surfaces. No paid provider request.
- Browser local 390px: Work Note → detail → share has same headline and context. Four looping decorative animations pause. 360px Home has no horizontal overflow; heading 28px. Tarot five-card option changes CTA; Radar shared hour/minute selects and unknown-time option visible.
- Supabase preflight found 29 backend tables with browser-role grants and no RLS. Applied transaction-safe idempotent guard immediately: RLS plus client/PUBLIC grant revocation, future current-owner default grants revoked. Verification passed. Migration 28 records it and protects the new rewrite queue. No rows/credentials/keys changed. Backend role remains existing `postgres` with bypassrls; narrowing it needs a separate rehearsed migration.
- Source checked: [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security), [Supabase connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres), [WCAG Pause Stop Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html), [OWASP privacy minimization](https://mas.owasp.org/MASVS/controls/MASVS-PRIVACY-1/).

## Giới hạn còn mở

Tarot repetition follow-ups; ~748kB JS bundle warning; chưa có kiểm chứng đọc hiểu với người thật hoặc FPS trên điện thoại thật; Reduced Motion được kiểm bằng CSS/tests, chưa thay OS preference trực tiếp. Luna/provider worker vẫn tắt: không suy rằng nội dung đang được LLM viết live. Backup/restore rehearsal riêng vẫn là follow-up vận hành. Không phải chứng nhận security/privacy toàn hệ thống.

## Deploy / public verification

PASS — final runtime commit `a7fadf7e45113e9a2be5cc9e2e7f7785bde56049`, published on main before serving.

| Evidence | Verified result |
|---|---|
| Container image / digest | `la-lanh:a7fadf7e4511` / `sha256:b2842068c3982ad8b7024b97a2f6ecc9a01fa796a59d8fde854580ce50398c1d` |
| Archive checksum, local/VPS | `c58763255ea75d94badb19d17aa825d43684ea5a25e8ec00c2bf062c1e1bf0ce` |
| Schema | `20261008_0028` |
| Active source | `/opt/la-lanh/releases/a7fadf7e4511/source` |
| Health | app and Caddy healthy; public health/readiness + deep links pass |
| Privacy | DB isolation gate pass; `anon` and `authenticated` denied SQL zero-row queries (`42501`); no data retrieved |
| Headers | HTTPS trusted certificate; HSTS, no-referrer, noindex, no-store verified |
| Operations | guest-cleanup + expired-cleanup timers active; old images preserved; no DB downgrade |
| Spending | `generation_enabled=False`, `worker_enabled=False`; no paid provider calls or billing changes |
| Rollback | immediate `la-lanh:328c48e8906f`; pre-release `la-lanh:3798652ed4a3` |

Public E2E, fresh synthetic session: date-only birth → Note; Work projection → safe share with matching title → public preview without DOB → revoke/404; time/place supplement → profile level 3/Aura → activate full-synthesis; Western/Jyotish overview, Natal/Aura reading and current sky; Tarot 1/3/5 completion and anonymous denial; Radar exact and unknown time, four-section report, anonymous 404 and deletion. All QA-owned guest data deleted in `finally`; cascade covers principal/Radar records. No real user's profile was edited or deleted.

Browser live: Home and Note contain direct copy; Welcome 1/3 with looping motion, pause freezes all decoration; optional Birth 2/3 supports unknown/known hour-minute controls with separate unchecked consent. Width 390px: no page overflow. Home final JS is `index-DBLYtUBv.js`; four Home animations pause/resume. Save `live-home-final-390.png`, `live-welcome-390.png`, `live-note-390.png`, `live-birth-optional-390.png`; local 360px evidence also retained. Browser first-run form was not submitted against the user's existing profile; synthetic submission was tested through public API instead.

The QA harness was corrected after release for Radar's intended empty 404 denial, not 401/JSON. The final harness exited 0 after all nine checks. These script/receipt corrections are source follow-up only; running application code remains the immutable commit above. Future operators must use latest main for the local acceptance harness.

The previously open Supabase permissions were confirmed and closed; this pass does not establish whether any historical unauthorized access occurred. Do not claim an incident review or a full security certification.

Lượt đầu `328c48e8906f`: image healthy, schema `20261008_0028`, HTTPS/header smoke pass. Public synthetic E2E phát hiện tạo safe link từ góc Work trả 404: POST chỉ gửi revision, backend project lại góc auto. Đã sửa input context enum trong POST và project cùng lens; mặc định auto giữ backward compatibility. Public snapshot vẫn không có field lens hoặc dữ liệu sinh. Gate privacy nay rà đúng response schemas thay vì nhầm private request/function argument là response. Test hồi quy kiểm đúng bản đọc, lens không khớp bị 404, enum sai bị 422, revoke làm link cũ 404. Full check sau sửa: 192 web + 520 backend pass.
