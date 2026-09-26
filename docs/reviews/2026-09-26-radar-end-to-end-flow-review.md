# Radar Hợp Gu — end-to-end product review

**Date:** 2026-09-26  
**Verdict:** Pass for local product review. Public/native release gates remain those listed in the foundation spec.

## Flow now available

1. Home or bottom navigation → `/radar` product introduction.
2. Primary path: `/radar/start` → just-in-time own chart completion → authorized transient input → `/radar/result/:id`.
3. Owner can reopen a private result from `/radar/start#radar-history`, delete it, or begin another check.
4. Consent fallback: `/radar/invite` → private capability link → `/radar/i/:token` → request-bound consent at `/radar/continue`.
5. Recipient lands at `/radar/receipt`, can reload the result on the same device for seven days, or withdraw the result for both sides.
6. Owner reopens consented results from `/radar/invite#radar-history`; revoked, withdrawn and expired states do not expose a result.

## Actionable findings resolved

- Bound owner history and result caches to a server-confirmed guest session epoch.
- Removed personal Radar caches when the guest session changes or local personal data is cleared.
- Bound each consent action to the exact invitation opened in that browser tab.
- Added a durable, HttpOnly receipt route for recipient reload and withdrawal.
- Kept owner and recipient projections separate inside one encrypted result envelope.
- Added explicit loading, retry, expired, delete-failed and withdraw-failed states.
- Removed birthplace search results immediately after selection and on owner/session change.
- Kept raw birth inputs out of URLs, browser persistence, Radar database columns and response payloads.

## Verification evidence

- Web unit/component suite: 32 files, 105 tests passed.
- Radar API flow: 6 tests passed, including recipient receipt reopen/withdraw, stale invitation binding and result expiry.
- Web typecheck, lint and production build passed.
- Changed Radar backend passed Ruff and mypy.
- Repository privacy guard passed.
- Manual browser QA passed from `/radar` through just-in-time onboarding, exact chart completion, private check, detailed result, history and reopen. Invite creation/history also passed.
- Native release configuration guard: 4 tests passed. Syncing the packaged iOS/Android shell is intentionally fail-closed until a real versioned HTTPS API URL is supplied; no placeholder endpoint was embedded.

## Known repository health outside this Radar delivery

The complete API suite currently has five failures in the pre-existing Daily Note/Aura projection tests: a deterministic Aura candidate is rejected by its content gate and the API correctly falls back to the legacy note. Radar's six API tests and the manually exercised Radar flow are green. These Daily failures are not represented as completed work here and should be handled as a separate Daily content-gate repair before calling the whole repository release-ready.

## Security and privacy basis

- Owner mutations require trusted origin, CSRF and matching owner/guest identity.
- Invite and receipt capabilities are HttpOnly; public pages are `no-store`, `no-referrer` and `noindex`.
- Recipient consent and withdrawal reject stale request bindings.
- Derived results and nicknames are envelope-encrypted; raw third-party birth input is transient.
- The controls align with data minimization and user-control principles in Vietnam Law 91/2025/QH15 and OWASP MASVS privacy guidance. Legal review, scheduled physical purge, abuse operations and store disclosures remain public-release gates—not hidden implementation claims.
