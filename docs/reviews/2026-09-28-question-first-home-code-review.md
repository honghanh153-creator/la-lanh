# Code review receipt — Question-first Home

Date: 2026-09-28  
Plan: `plans/2026-09-28-2042-feat-question-first-home-plan.md`  
Verdict: **PASS** — no unresolved P0, P1 or P2 finding.

## Actionable findings and resolution

| Priority | Finding | Resolution |
|---|---|---|
| P1 | Resend/replacement retirement guards had no tests | Added explicit `410 Gone` assertions for create, resend, replacement, public preview and submit. |
| P1 | Receipt-withdrawal UI had no behavior coverage | Added explicit-action, success, missing-receipt and connectivity-failure tests. |
| P1 | Empty history fixture could not prove retained management actions | Added pending/completed fixtures; verified revoke remains, result remains, and create/resend/replace do not return. |
| P2 | Cached Daily Note fallback was not covered | Added cache seed + failed refresh test; question router and cached reading remain visible together. |
| P2 | Current Sky back action lost Home context | Home passes route state and Current Sky returns to Home when entered there. |
| P2 | Current Sky could show loading forever on failure | Added retryable error state and a failure-to-success test. |
| P2 | Public retirement CTA could send a recipient without a session to Home | CTA now goes through `/`, where the entry resolver chooses Home or Welcome safely. |
| P2 | Withdrawal UI described every failure as an invalid receipt | Missing receipt and connectivity/server failures now have distinct copy. |
| P2 security | A valid receipt could stop working when the invitation expired first | Withdrawal now follows receipt TTL and completed status, not invitation-preview expiry; regression test expires the invitation before a successful withdrawal. |

## Review coverage

- Correctness: Home state ordering, destination routing, Current Sky failure/back behavior, retired public flow.
- Security/privacy: token non-reflection, `410` server enforcement, CSRF/auth preservation, safe public headers, revoke/hide/delete/withdraw rights.
- Testing: cached/offline behavior, legacy data management, receipt withdrawal, mobile/desktop E2E.
- Simplification: removed duplicate Lá Chứng acquisition entry, duplicate Home bento, repeated media queries and unrelated stylesheet coupling.

## Verification evidence

- Web: 38 files / 127 tests passed; lint and TypeScript passed.
- API: 5 focused Lá Chứng tests passed; Ruff passed.
- Contracts: OpenAPI and generated TypeScript contract current.
- Browser: 8 Playwright scenarios passed across mobile and desktop, including Home → Tarot navigation.
- Production build passed. Existing Vite bundle-size warning remains non-blocking and predates this slice.
