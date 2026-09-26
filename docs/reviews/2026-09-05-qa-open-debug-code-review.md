# QA open failure - debug and code review

Date: 2026-09-05

## Scope and intent

- Reviewed the staged product tree against `247b84e`.
- Reproduced the blank/unreachable product from both `file://apps/web/index.html` and stopped localhost services.
- Verified the app-first guest path with a synthetic date from Welcome -> consent -> birth -> Swiss Ephemeris reveal -> Home -> mood -> saved note.
- Checked the current PRD/SRS/user stories, OWASP MASVS, Vietnam Personal Data Protection Law 91/2025/QH15, Apple privacy guidance, and official Vite serving guidance.

## Applied fixes

1. Added a same-origin QA web server with SPA deep-link fallback, API proxy, readiness endpoint, localhost-only binding, security headers, safe path resolution, and bounded upstream timeout.
2. Added `Open Lá Lành QA.command` and documented `pnpm qa` as the supported way to open the product.
3. Build and verify Swiss Ephemeris assets before launch.
4. Use a fresh temporary QA database for each launch. Development data is not read, overwritten, or deleted.
5. Added unit and real subprocess smoke tests for the QA server, API startup, proxy, fresh schema, and deep links. Added these checks to `pnpm check`.
6. Enabled SQLite foreign-key enforcement and fixed snapshot insertion order so QA uses the same referential-integrity behavior expected from PostgreSQL.

## Validation

- Contracts current.
- Runtime mock guard passed.
- Privacy guard passed.
- Web lint and typecheck passed.
- Web tests: 7 passed.
- API lint and strict typecheck passed.
- API tests: 68 passed.
- QA server unit test passed.
- Production web build and Swiss Ephemeris checksum verification passed.
- Full-stack QA CLI smoke passed.
- Browser console: no warning or error on the verified path.
- Five independent reviewer lenses completed: correctness, project standards, testing, maintainability, and performance. Security/privacy checks were also applied directly against the project gate and current official sources. The separate cross-model route did not run because no independent provider CLI was available on this machine.

## Remaining release blockers from code review

These do not block the local web QA link, but they block a claim that the native app or all US1-US9 are production-complete:

1. Native shells still need an allowlisted HTTPS production API origin and Keychain/Keystore-backed session transport.
2. Approximate birth time still uses a midpoint for some facts; uncertain Moon/planet factors must be sampled across the full interval and withheld or shown as alternatives.
3. Guest claim/delete/expiry must atomically re-parent data, revoke the old credential, and avoid the current `RESTRICT` cleanup conflict.
4. Lá Chứng invitation capability must be exchanged for a narrow HttpOnly cookie and removed from URL/history.
5. Lá Chứng request creation needs owner-scoped idempotency.
6. Daily Note and US07 need true transit-to-natal synthesis; current content is not yet the complete PRD interpretation engine.
7. PostgreSQL migration and concurrency tests, real native build tests, and an unmocked full-stack Playwright suite remain release gates.
8. The plaintext chart migration needs a production-safe encrypted backfill or purge strategy before release.

## Verdict

- Local QA web product: ready for hands-on QA.
- Native app and complete US1-US9 production release: not ready until the blockers above are closed.
- Fixes are left staged and uncommitted because the branch already contained the larger US1-US9 work in progress.
