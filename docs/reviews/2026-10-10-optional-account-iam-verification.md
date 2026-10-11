# Optional account / IAM — local verification

Date: 2026-10-10. Scope: the approved optional-login, returning-profile, independent-history and backend IAM delta. Preserve the pre-existing dirty worktree. No stage, commit, push, deployment, live Supabase configuration, real OTP email or paid content call in this run.

## What changed

- Anonymous profiles renew after valid private use: server clock and both cookies remain aligned, identity does not change. Public views, invalid CSRF, failed operations and workers do not extend the clock.
- First verified account link retains the same data owner. Existing accounts require explicit restore; no cross-person merge or transfer of AI consent. Devices have independent credentials and 30-day access clocks, separate from the disclosed 365-day account data clock.
- Self-only device list, single-device revoke and revoke-others are backend operations. Caller-supplied device IDs never select a foreign owner. Logout revokes only the current device; it is not account erasure.
- Managed email OTP is disabled by default. Verification is bounded, nonce/cookie-bound and database-serialized. Provider tokens, OTPs and metadata roles do not become browser credentials or operator authority.
- New private account/history tables have RLS and browser-role grants revoked. All `/v1/` responses are `no-store`.
- Automatic history has a creation-based deadline independent of login/profile renewal. Legacy histories require opt-in, with a grace period. Clear-history preserves birth/chart, current reading and Saved source data, and refuses while a provider-send fence is active.
- Basic birth-purpose consent is enforced before DOB persistence, including Tarot-only visitors; the submit notice grants this purpose only, never AI rewriting.
- Expired/erased owners cannot gain a new consent receipt after an earlier preflight; expiry is rechecked under the owner lock and reported as a domain 401.
- Client epoch/generation fences cover cookie transitions and decoded responses. Welcome does not reset a valid returning profile; network errors do not delete it. Legacy owner credentials refresh after expiry, not merely on epoch change.

Architecture and API matrix: [account IAM and retention](../architecture/account-iam-and-retention.md).

## Browser proof

Dedicated ephemeral QA at `http://localhost:5350`, API 8050; synthetic DOB 15/03/1990. Auth delivery and paid rewriting disabled. Different hostname from the user's `127.0.0.1:5310` protects that review session from cookie replacement.

Observed: invalid old QA cookie → one click on welcome → DOB → Vibe · Mộng → correct current note → Mình; cancel history deletion preserves the profile; optional login accurately reports delivery off; continuing as guest keeps the same note. Returning to welcome and pressing the ordinary start button resumes Home instead of creating a new profile. Tarot question → server-locked spread → three selected cards → reveal → summary and expandable chapters completed without login or paid provider.

Browser QA found and fixed two additional defects: an expired-cookie `/session` 401 was incorrectly fenced as a person-change before onboarding could retry, and `/me` recovery links did not match the actual `/profile` route. The 401 exception remains narrow to recognized expiry/missing-session responses with cookies cleared; generation/epoch checks remain mandatory. Cancelling optional login now returns to the allowlisted originating page instead of losing that context.

Account success/races use real application and DB flows with only the external provider HTTP boundary injected in tests. This is not proof of email delivery or two physical phones. No irreversible browser deletion performed.

Mobile-web viewport 390×844: welcome → DOB → reveal → note → Mình → optional-login unavailable → cancel returned to `/profile` and retained Vibe · Mộng. [Screenshot](account-iam-2026-10-10/profile-390.png). This is browser viewport testing, not a native phone run.

## Verification ledger

Final local results after the last code fixes:

| Gate | Result | Local log |
|---|---|---|
| Full API, no external provider | 1,163 passed; 46 environment-gated skipped | `/tmp/ll-api-iam-final-v3.log` |
| Isolated PostgreSQL 17.11 + verified TLS | 46 passed: account/history + actual revocation barrier + rewrite concurrency | `/tmp/ll-iam-pg-final-v3.log` |
| Full FE | 253 passed in 53 files | `/tmp/ll-web-test-v2.log` |
| Mypy app/tests/scripts | 324 files, clean | `/tmp/ll-iam-types-final.log` |
| Ruff lint / format | passed / 357 files formatted | `/tmp/ll-iam-lint-final.log`, `/tmp/ll-iam-format-final.log` |
| ESLint / TS / build | passed; existing >500kB bundle warning | `/tmp/ll-web-lint-v2.log`, `/tmp/ll-web-types-v2.log`, `/tmp/ll-web-build-v2.log` |
| OpenAPI / TS contract drift | current | `/tmp/ll-iam-contracts-v2.log` |
| Runtime mock / privacy / mobile config guards | passed | `/tmp/ll-iam-runtime-v2.log` |
| Tracked whitespace | `git diff --check` passed | terminal verification |

The 46 skipped base-suite cases were exercised separately against the disposable PG cluster. Counts across targeted/independent/full runs overlap; do not sum them as distinct tests. The guarded fixture refuses any host/database except the created loopback test cluster at port 55434. No production database was used.

No real-user study, physical iOS/Android run, real SMTP delivery, paid Luna content generation, production-role test or public URL verification in this revision.

## Simplification review

Three read-only reviewers examined reuse, quality and efficiency. Applied: one owner-qualified set-based challenge delete for revocation; direct criterion-based root deletion for unbounded manual history clearing. Owner locks, CSRF, revocation timestamps, table order, saved/current-source exclusion and bounded worker limits remain unchanged.

Deferred, not hidden as completed: cross-domain private-helper reuse (would create coupling), history transaction API encapsulation (needs a separate interface refactor), nested login render extraction and redundant expired-timer rerenders (not access-control defects), aggregate cleanup backlog counting (current per-owner count is correct but needs scale optimization). Track the latter before scaling beyond beta; no benchmark proves large-dataset performance.

## Review findings and resolution

The delegated full `ce-code-review` receipt covered the tracked dirty snapshot and excluded untracked files from its formal diff. Its launcher could not start the selected eleven reviewer personas, so [that checkpoint remains degraded](2026-10-10-optional-login-agent-full-review-20261010-143722-bd0530c7.md). Separate context review caught C1; do not relabel the checkpoint as a full independent clearance.

A later independent native read-only reviewer explicitly included the new accounts/history files and validated the narrowed fixes. Initial independent runs: 97 focused API and 20 FE tests; final history validation: 31 tests, including all seven new regressions. No remaining actionable finding in that precise reviewed delta. This does not certify unrelated existing WIP/content or the entire system.

| Finding | Failing-before proof | Fix and passing-after proof |
|---|---|---|
| P1 revoked device accepted after owner-lock wait | Actual PostgreSQL core `GuestSessionService.resume` reader waits on owner lock, revoker commits, reader erroneously accepts; `/tmp/ll-iam-revocation-red.log` | Scalar-only discovery; locked owner/device `populate_existing` rereads plus owner/digest checks. Actual PG barrier passes; independent lock-seam validation also rejects |
| P2 foreign cookie arrives during expiry JSON decoding | Deferred JSON returns `GUEST_EXPIRED` instead of `SESSION_CHANGED`; `/tmp/ll-iam-cookie-red.log` | Recheck current cookie is still null after decoding; regression passes and independent FE validation passes |
| P2 consent owner erased/expired after preflight | Unhandled missing-owner error and absent under-lock expiry check | Handled `GuestExpired` domain 401 under lock; coherent expired/erased fixture passes on SQLite and PG. No resurrection |
| P2 unsent history attempts silently prevent erasure | Six pending/retry/unsent-leased × manual/purge cases and one hidden-busy-backlog case fail; `/tmp/ll-iam-history-red.log` | Remove attempt-status retention exemption; owner-locked plan deletion cascades unsent attempts and delayed send recheck fails. Actual-send busy fence remains; blocked backlog counted. Seven regressions pass on SQLite and PG and independent history rerun |

Some initial commands failed due to a mistyped test path, wrong migration environment-variable name, test timestamps violating expiry-after-creation and import ordering. These were corrected before the green results; the failed setup was not treated as a passing regression or repaired by weakening safety constraints. No pre-existing/live DB reset was used.

## Release gates still closed

1. Public login stays off until approved real Supabase SMTP/OTP settings and delivery checks exist. Supabase default SMTP restricts recipients and is not production delivery.
2. Local erasure removes account linkage, devices and local dependent data, but does not yet erase the email identity at Supabase Auth. Complete provider identity-erasure handling before enabling public account storage; disclosure is not a substitute for that work.
3. Rehearse migrations 0031/0032 and least-privileged application grants on the deployment environment, schedule bounded cleanup at least every six hours, and verify backlog, backup retention and rollback fences.
4. Complete native two-device continuity and real-email recovery before claiming app-ready authentication. Current preview is local only; existing beta has not changed.

Research refreshed 2026-10-10: [Supabase email OTP](https://supabase.com/docs/guides/auth/auth-email-passwordless), [SMTP restrictions](https://supabase.com/docs/guides/auth/auth-smtp), [OWASP sessions](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html). These inform engineering controls; they do not certify legal compliance or absence of vulnerabilities.
