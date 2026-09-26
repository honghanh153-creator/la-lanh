# Kế hoạch hoàn thiện social + relationship release

Ngày: 2026-09-18  
Trạng thái: active, tiếp nối `2026-09-17-vong-la-product-completion-plan.md`

## Thứ tự critical path

### R0 — US-19 account/auth thật

- Phone/email OTP provider interface, challenge hash, expiry, resend/attempt/rate limit và anti-enumeration.
- Account/principal link, guest claim atomically, conflict review, recovery và in-app deletion.
- Draft resume contract cho Lá Chứng, Pitch Card, Lá Ghép và Vòng Lá.
- Production fail-closed nếu delivery provider chưa cấu hình; test adapter chỉ tồn tại trong test environment.

### R1 — US-10/11 Pitch Card acquisition

- ThemeBank + StatementBank versioned, đúng năm câu, rate-limit pitcher-target.
- Public capability link không chứa statement/birth data; preview trước install.
- B guest consent + Basic reveal; accept chỉ mở US-14, không auto-enroll.
- Revoke/expiry/decline và deletion propagation.

### R2 — US-12/13 Lá Ghép

- Pair draft A; input B mã hóa và chưa canonical.
- Synastry degraded preview; B xác nhận dữ liệu và consent purpose riêng.
- Immutable full result snapshot dùng Synastry; Composite bonus; Davison only exact+consented.
- Simultaneous reveal, private invite/public share tách token, revoke/expiry/delete.

### R3 — US-14 verification operationalization

- Private object storage, signed upload, malware/image validation, provider/manual review seam.
- Pending/pass/fail/retry/appeal, reason code an toàn và SLA.
- Community rules + support contact + deletion/retention.

### R4 — US-15/16 weekly slate + mutual

- Pool/slate/card/request/mutual/Lá Nối tables và idempotent weekly jobs.
- Five energy slots, hard filters first, max three opens, low-pool honest state.
- Reciprocal request transaction, block race, private pending and immutable Lá Nối.

### R5 — US-17 chat safety

- Authorized thread/message store, ordering/idempotency/reconnect.
- Three editable icebreakers from evidence-bound relationship editorial plan.
- Block/report/unmatch on same screen; moderation queue, abuse limit and retention.

### R6 — US-18 recap + app loop

- Sunday immutable recap snapshot, no-match-positive copy and safe anonymous shares.
- Push/deep-link fallback to API state; CTA Daily Note/countdown.

### R7 — Native release

- Secure token storage, Universal/App Links, push, photo permissions at point of need.
- iOS/Android simulator, MASVS checks, store 18+, account deletion, privacy labels/data safety.

## Release rule

R0 must finish before R1–R5 are called account-backed. R4 cannot public without R3 and R5. R6 cannot expose non-mutual identity. R7 is a launch gate, not a post-launch polish task.

## Verification receipt required per unit

- Unit tests + API authorization/CSRF/race tests.
- Contract generation current.
- Mobile viewport screenshot and a11y smoke.
- Data map, consent purpose, retention and deletion path updated.
- No mock runtime or production-only bypass.
