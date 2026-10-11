# Paid rewrite pilot preparation

Production unchanged; paid worker disabled. This is local preparation, not a release receipt.

## Verified

- Reused existing key metadata access and one synthetic Luna generation. 710 input/63 output tokens,
  USD 0.00010250 at pinned Standard prices. Gate passed; no user data or local prose retained.
- Platform USD 5 credit balance, auto-reload off. Later project view confirms enforced USD 1/month.
  No operator credit purchase, new key, saved payment method or retry of the rejected cap save.
- 525 API tests passed, API lint/typecheck and contracts checked. The first full run had a transient
  in-memory SQLite "no such table: chart_snapshots" failure in the existing birth-change experiment
  test; isolated rerun and subsequent full suite passed. Root cause is not established; do not claim
  the intermittent test issue was fixed.
- 197 web tests passed after the API-client prefix/CSRF fix; all web lint/typecheck/build checks pass.
  The live local opt-in path, not just mocked components, saved and revoked consent.
- QA CLI smoke initially could not listen under the sandbox. With localhost permission, all three
  QA harness tests, native ephemeris integrity, production web build and real guest/birth/daily smoke
  passed. Native config guards 4/4 passed. Bundle-size warning remains, not a payment blocker.
- 670-case manifest/content/privacy/experience audits passed offline. The scored generated-output
  release command fails closed without `--results`. No reviewer scores were invented.

## Browser QA

Ephemeral database, separate `localhost:5211` origin, synthetic date only. The API was enqueue-only;
worker disabled and no key mounted. This check made no paid provider calls.

1. Welcome, date, reveal and Home worked; normal note appeared with no AI consent.
2. Real UI exposed a duplicated `/v1` prefix and missing CSRF/JSON headers in the new client methods.
   Both are fixed with a client-level regression, not just mocked component tests.
3. Profile showed opt-in; disclosure opened with focus on Close. Consent saved, survived reload,
   and withdrawal changed the control back to opt-in. Normal content stayed available.
4. Consent snapshot saved in `consent-local.png`. This is synthetic local UI, not live activation.
5. Temporary tab/server closed. Existing localhost product session/port and production untouched.

## Review gates

Documentation: API contracts and runbooks updated for monthly cap, active-session cohort and explicit
personal consent. Percentage rollout is artifact-based, not a people or spend limit.

Security: aggregate ledger locks reservations; RLS/browser-role grants denied; no owner identifiers,
no deletion reset; worker must have positive daily/monthly/cohort limits; no API/frontend key mount;
CSRF mutations and no-store status read; expired sessions and revoked consent block provider use.
The worker requires an explicit project ID and passes it to the OpenAI SDK. Read-only model access
with the capped project header returned 200; no second paid generation was performed.

Privacy: only derived semantic briefs are allowed, never raw birth/location/identity values or
free-form Tarot questions. Personal consent does not authorize Radar/Matching. `store:false` does
not mean Zero Data Retention. Anonymous spend history remains after personal data deletion.

Sources and pending requirements are in
`docs/plans/2026-10-08-paid-rewrite-pilot-activation.md`. OpenAI data controls, model pricing/spend
limits, Supabase RLS and Vietnam Law 91/2025/QH15 were checked; this is not legal certification.

## Still incomplete

Confirmed VPS key destination, PostgreSQL migration/concurrency rehearsal, scored generated-output
review and provider/DPA/cross-border evidence, source commit/deploy, live paid worker and fallback
E2E. Current code is not deployed and user-visible AI is not enabled.
