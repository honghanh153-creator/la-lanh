# Reading Knowledge Engine — code review receipt

Date: 2026-09-12  
Scope: Daily Note knowledge/planner/renderer/gates, update activation UI, privacy boundaries  
Verdict: **Go for local product QA; no-go for public release until the listed release gates close.**

## Review lenses

- Correctness: factor selection, daily freshness, ambiguity, projection activation.
- Security/privacy: high-stakes influence, external generation authorization, data minimization.
- Maintainability: canonical factor grammar, Western/Jyotish isolation, duplicated activation flow.
- Testing: behavioral matrix coverage and timezone boundary.

## Findings resolved

1. Ambiguous date-only Sun no longer picks one candidate as fact.
2. Full Daily reading rotates among a bounded high-salience factor pool by local date, so the user-visible synthesis changes after Asia/Ho_Chi_Minh midnight.
3. Jyotish plans reject Western aspect/transit semantics; gochara interpretation remains off pending a dedicated reviewed corpus.
4. Canonical factor ids now fail closed at model validation instead of crashing during positional decoding.
5. Evidence gate rejects recombined body/sign labels that do not belong to the same canonical claim.
6. Anti-influence coverage now rejects all-savings/crypto pressure and covert phone surveillance/relationship-control prompts.
7. External generation requires both deployment enablement and an explicit purpose authorization; no product route currently supplies that authorization.
8. Home and Note Detail share one activation hook that cancels stale Daily Note requests before installing the authoritative revision.
9. Update gift copy no longer invents whether the birth data did or did not change.
10. Behavioral tests cover signs at a fixed date, planets, houses, aspects, degree/orb bands, transit phases, local midnight, ambiguous Sun and Jyotish isolation.

## Deliberately deferred, fail-closed

- Replace canonical colon-delimited factor ids with discriminated typed payloads in a storage migration. Current grammar validation is a mitigation, not the final model.
- External generated prose needs a closed semantic response contract (`template_id` + `factor_ref`) before it can be enabled in the product. Configuration and per-request authorization remain off by default.
- Pending-update API still includes the full encrypted/decrypted candidate projection before activation; reduce it to metadata-only in the next contract migration.
- Public release still needs production KMS, distributed edge controls, deployed HTTPS API, native device QA, legal/privacy assessment and a Swiss Ephemeris licensing decision.

## Verification evidence

- Backend: 216 tests passed; Ruff passed; mypy passed for 100 source files.
- Frontend: 16 files / 42 tests passed; ESLint and TypeScript passed.
- Production web build passed; Swiss Ephemeris asset checks passed.
- Privacy guard passed; mobile privacy/config guard 4/4 passed.
- Browser QA completed on onboarding, date-only reveal, Daily Note, and the full-data consent flow.

