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

Chưa triển khai khi tạo receipt. Chỉ đổi sang PASS sau khi image/schema/public smoke và browser live được kiểm chứng.

Lượt đầu `328c48e8906f`: image healthy, schema `20261008_0028`, HTTPS/header smoke pass. Public synthetic E2E phát hiện tạo safe link từ góc Work trả 404: POST chỉ gửi revision, backend project lại góc auto. Đã sửa input context enum trong POST và project cùng lens; mặc định auto giữ backward compatibility. Public snapshot vẫn không có field lens hoặc dữ liệu sinh. Gate privacy nay rà đúng response schemas thay vì nhầm private request/function argument là response. Test hồi quy kiểm đúng bản đọc, lens không khớp bị 404, enum sai bị 422, revoke làm link cũ 404. Full check sau sửa: 192 web + 520 backend pass.
