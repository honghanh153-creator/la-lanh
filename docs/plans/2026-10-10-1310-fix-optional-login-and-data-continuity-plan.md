---
title: Optional login and reliable data continuity
date: 2026-10-10
type: fix
artifact_contract: ce-unified-plan/v1
product_contract_source: legacy-requirements
origin: docs/user-stories/US-19-xac-thuc-khi-can.md
execution: code
---

## Goal Capsule

Users can return to their own daily note without repeatedly entering birth details, and can choose account login to recover that profile on another device without seeing another person's data.
Implement and locally verify; preserve all existing WIP. Do not commit, deploy, change production authentication settings, send real OTPs, call paid content providers, or create charges in this run. Real email delivery is a separate release gate requiring configured Supabase Auth email delivery and operator approval.

## Product Contract

### Problem Frame

Guest data ownership is currently a single credential-bearing row used by all domain tables. The server extends its inactivity expiry, but browser cookies do not extend with it. The current owner claim is not recoverable account authentication. Account recovery cannot depend on the guest credential remaining alive, and logout must not cascade-delete charts and history.

### Requirements

- R1. Guest remains optional. Anonymous onboarding, daily note, Tarot and private Radar stay usable without account login. Soft CTA in Mình and after reveal; no forced signup.
- R2. Guest profile expires after 30 days of inactivity, not 30 days after creation. Valid private interaction renews both server lifetime and credential cookie. Server expiry stays authoritative; public previews, background workers and cleanup do not count as user activity. Invalid cookies must never be refreshed.
- R3. Email OTP login uses managed Supabase Auth. Email/code are never stored in browser storage, URL, logs or analytics; Supabase tokens never go to frontend storage. Neutral errors, strict origin checks, bounded request/verify quotas and short challenge validity. Provider off is an honest unavailable state, not simulated login.
- R4. First verified login atomically links the current guest profile to the verified account; a second device restores the same stored chart/note/history. Account-linked data is not deleted by guest inactivity cleanup. Account profile retention is explicitly disclosed as 365 days without use; extend on authenticated use, never on a worker.
- R5. Each signed-in device gets an independent revocable credential. Logout revokes that device's access and clears all client personal caches, not the profile. Login to a different account fences/aborts old requests and must never leave old content visible.
- R6. Existing account restores its own profile only after the UI explains that the on-device guest will not overwrite it. No implicit cross-person merge. The unselected guest stays on its original guest TTL; do not union private histories or migrate fresh AI consent onto an unrelated account.
- R7. Separate history clocks: Tarot, Radar, mood and automatic daily history default to at most 30 days from creation (29 days 18 hours where six-hour purge applies), not extended by reopening, login or profile retention. Explicit saved notes are kept with the profile. Birth chart/profile is not historical content. Expired history returns a clear unavailable state, not empty onboarding. Never shorten existing retained data retroactively without disclosure.
- R8. Mình clearly distinguishes đăng xuất, sửa hồ sơ, xoá lịch sử and xoá toàn bộ dữ liệu. Whole-profile erasure removes account linkage/device sessions/dependent content and does not allow later account login to resurrect deleted content. History cleanup must not delete the profile or current source pointers.
- R9. Optional email login can fail/cancel/retry without deleting the guest. Private-page 401 may clear untrusted local caches but never calls server deletion. Offer login recovery on welcome/expired-session screens. Login return path is allowlisted and never auto-submits a social action.
- R10. Fix remaining confirmed lifecycle bugs and retain their regression proofs: same-sign birth change, old reading publication, mixed metadata, obsolete rewrite spending, precision editor, Tarot depth copy, sharing fallback. No claim of live fixes until deployment is independently verified.
- R11. Backend IAM is authoritative (user addition, 2026-10-10): verified subject binds one retained profile; every private request resolves ownership server-side. No client-supplied subject/role/guest ID grants access. Ordinary account login never grants Content Studio/operator authority. Devices can be listed and revoked by their own account only, including all other devices; revoked credentials must fail on core private APIs, not just the login screen. OTP recovery is not a permission to overwrite another profile or resurrect erased data.

### Key Decisions

- Guest-first with optional recovery login (session-settled: user-approved; rejected forced initial login). Governs R1, R3, R9.
- Guest 30-day inactivity lifetime with separate history TTL (session-settled: user-approved; rejected deleting active users every 30 days). Governs R2, R7.
- No automatic overwrite when account and on-device profiles differ. Governs R6.

### User Flows

F1. Guest creates profile → views note each day → activity extends guest lifetime → history expires independently → current birth profile remains.
F2. Guest chooses Giữ hồ sơ → email + explicit account storage notice → OTP → verified account new → link + rotate credentials → home.
F3. Returning account on another device → OTP → existing profile confirmation → new device credential → same chart/history → home.
F4. Logout → revoke current device only → clear caches → welcome with Đăng nhập lại; other signed-in device unaffected.
F5. Delete all data → confirm scope → fence jobs/dependent erase → account link removed → later login starts an empty profile, never restores deleted data.

## Planning Contract

### Key Technical Decisions

KTD1. Preserve existing guest IDs as data-owner IDs; add account linkage and per-device credential rows rather than moving dozens of foreign keys. Persist only domain-separated credential/CSRF digests; never raw device secrets. Split data retention from access-token expiry. Avoid rotating the one shared GuestSessionRow token for every account login, which would log other devices out.
KTD2. Server-side Supabase REST email OTP adapter, fixed configured HTTPS project origin + publishable key only. No service-role key needed, no custom password database, no JWT authorization from user_metadata. A verified provider subject is the account key. Store only subject ID and masked/encrypted identity as necessary, never OTP/provider bearer tokens. Disabled by default pending delivery configuration.
KTD3. Explicit restore of an existing account; do not implement broad historic merge in this revision. US-19's richer union/phone/social-pool requirements remain deferred. API response tells UI when account restore needs consent; do not emit account-owned guest credentials until confirmed.
KTD4. Migration is additive with backfill-safe defaults, RLS/revoked anon grants for all new private tables on PostgreSQL. Account purge integrated into cleanup with owner/source lock ordering; current profile remains independent of reading history.
KTD5. Central cookie renewal after successful guest verification, reuse existing secure/domain/path/SameSite settings; never alter CSRF value just to extend its expiry. Session identity boundaries still fence same-origin tabs and in-flight data.

### High-Level Technical Design

Directional relationships (not implementation code):

```text
Login screen → API OTP challenge → managed identity provider
             → verified subject → account → owned profile
Device cookie → credential record ─────────→ owned profile → chart / note / history
Anonymous cookie ─────────────────────────→ owned profile
```

Protocol: request code → verify short-lived challenge → review existing profile if needed → issue independent device credential → clear old client epoch → load authoritative profile.
Lifecycle: anonymous active → linked account → device logged out / credential expired → verified account recovery. Data lifetime and device login lifetime are independent. Erasure is a terminal deletion, not logout.

| Clock | Reset by | Not reset by |
|---|---|---|
| Guest profile 30d | Valid private user use | Workers/public links |
| Account profile 365d | Verified-account private use | Guest credential cleanup |
| Device credential 30d | Valid authenticated use | Another device logging in |
| History <=30d | Creation only | Opening/login/rewrite |

### Risks and Release Dependencies

Supabase's default SMTP only delivers to team-member addresses, is rate-limited and is not production delivery. Need operator-configured SMTP, email OTP template, provider expiry/cooldown and anti-abuse settings before public login is enabled. This work must not purchase them. Existing beta users cannot recover already-deleted profiles or cleared guest cookies without a previously linked account. Account expiry/purge must be documented and scheduled before enabling long-term storage. PostgreSQL concurrency proof remains mandatory before release; prior local test-role credential block is not waived by SQLite tests.

### Sources

- Supabase email OTP: https://supabase.com/docs/guides/auth/auth-email-passwordless
- Supabase delivery restrictions: https://supabase.com/docs/guides/auth/auth-smtp
- Supabase sessions: https://supabase.com/docs/guides/auth/sessions
- OWASP session management: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- Vietnam privacy framework baseline: https://vanban.chinhphu.vn/?pageid=27160&docid=214590
- Existing US-01, US-19; guest service/repository/routes; SessionBoundary and clearPersonalData; lifecycle audit dated 2026-10-10.

## Implementation Units

### U1. Sliding guest lifetime and safe renewal

Requirements: R2, R9. Files: guest service/repository/routes, middleware and guest tests. Reproduce day-29/day-31 returning cookie mismatch before patch; renew only after successful owner verification. Verify expired credentials cannot be revived, failed network never deletes server state, unchanged CSRF marker does not trigger false session changes.

### U2. Account ownership, device credentials and optional managed login

Requirements: R1, R3-R6, R8-R9; KTD1-KTD4. Files: new account domain/provider/routes/migration, guest repository, main/router/config, identity bridge, focused account tests. Native sequential execution because dirty shared WIP and shared ownership APIs prevent a safe parallel write wave. Proof first for new account link, restore, duplicate/concurrent verification, wrong/expired code, off-provider, independent devices, logout, cleanup, account deletion/recovery. Fake external transport only in tests; no runtime mock auth.

### U3. Distinct history retention and cleanup

Requirements: R7-R8. Files: cleanup scripts/domain history repositories and tests, profile retention response. Test old history removed while chart/saved notes/account remain; no sliding history on access; expired result UX; new account data not cascaded by guest cleanup.

### U4. Account UI and recovery-safe client boundary

Requirements: R1, R5-R6, R8-R9. Files: account page/API helpers/router, profile/welcome/reveal and tests. Clear code/email on unmount, password-manager OTP autofill, resend cooldown, cancellation, retry, unavailable, existing-profile confirmation, safe return. Logout clears personal caches only after server acknowledgement; network failures never claim success. History-clear confirmation names Tarot/Radar/mood/automatic daily history, preserves profile, current source pointers and saved notes; cancel, pending, retryable error and acknowledged success are distinct. Match cream/ultraviolet design with existing form controls.

### U5. Documentation and full-flow verification

Requirements: R1-R10. Files: US-01/19 update, data map/privacy UI, deployment gates, review receipt. Implement any remaining confirmed lifecycle defect in its owning domain before rerunning its regression proof; do not limit R10 to reporting. Backend/FE full tests/types/lint/build/contracts and browser synthetic flows. Explicitly record provider delivery, real PostgreSQL, physical mobile and production verification as unproven if not run. No broad dirty-branch commit or deployment.

### U6. Backend IAM and device revocation (user-added)

Requirements: R3-R6, R8-R9, R11. Server-owned resource authorization remains based on verified device → account → retained data owner, never email/metadata/IDs supplied by a caller. Extend the account API with self-only device listing, one-device revocation and all-other-device revocation. Do not add password storage, general admin RBAC, device fingerprinting or unverified email changes. Inspect the private session and legacy owner bridge; fix current-session refresh and test cross-account IDs, wrong CSRF, expired/revoked credentials, operator privilege escalation, logout/revoke/erase races and actual PostgreSQL behavior. Keep real Auth delivery off pending release gates. This is backend-first; advanced device-management UI is not part of this addition.

## Verification Contract

Use offline uv and pnpm runtime. Run targeted guest/account/history tests first, then full API pytest without default addopts, mypy/ruff, web vitest/build/lint, contracts generation + drift check, privacy/no-mock guard. Browser synthetic guest → returning user → login unavailable, login forms/error handling, Tarot/Radar history and private-note isolation. Managed delivery cannot be claimed from mocked tests. Two devices/accounts and logout tested through real API/database with injected provider response only.
Every bug patched gets a regression test; current-source lifecycle and no-provider-spending regressions from the prior run must stay green. Review changed delta only, not unrelated WIP. Record no real-user study/no real paid rewrite if those checks remain unavailable.

## Definition of Done

Local runtime and generated contracts agree, no test regressions, no accidental guest reset on normal return, no account restore leaking another subject, no logout deleting profile, bounded history cleanup preserves current chart. UI states and privacy notices reflect actual retention. Independent security/data-integrity review has no unresolved release-critical flaw in the implemented delta. Public login remains off until real provider/SMTP setup and PostgreSQL/migration rehearsal are proven; do not label disabled-provider local tests as a completed production login.

## Execution checkpoint — 2026-10-10

- U1/U2/U3/U4/U6: implemented and locally verified, including server-owned account/device IAM, purpose-specific DOB consent and owner/device/history lifetime separation. Auth delivery remains off by design, not a simulated success.
- U5: docs, regression suites, actual TLS PostgreSQL and browser/mobile-web journeys completed for this delta. Later bounded independent validation resolved revoked-cookie, deferred-JSON and unsent-history findings. The larger tracked-WIP full-review launcher was degraded; do not claim exhaustive independent clearance of all existing changes.
- Final proof: 1,163 API passed, 253 FE passed, 46 isolated PostgreSQL passed; lint/types/build/contracts/guards green. [Verification and limits](../reviews/2026-10-10-optional-account-iam-verification.md).
- Still closed before real release: SMTP/provider delivery authorization and setup; provider identity erasure; live least-privileged migration/RLS rehearsal and cleanup/backup operations; physical native/two-device recovery; deployment/public URL proof. Do not mark production login or all of US-19 complete.
- No commit, push, deployment, live provider configuration, real email or paid rewrite in this execution. Existing WIP and budget preserved.
