# Optional login review receipt

Date: 2026-10-10. Snapshot: 08:03:30 UTC.
Run: 20261010-143722-bd0530c7. Mode: agent; depth: full; report-only.

Later resolution: this is an immutable-in-time review checkpoint, not the current patch verdict. The parent reproduced C1 with an actual PostgreSQL lock barrier, then fixed scalar discovery/fresh locked rereads. The deferred-JSON race also has a failing-before/passing-after regression. The consent fixture clock was corrected. See [final local verification](2026-10-10-optional-account-iam-verification.md) for later independent bounded validation, additional history findings and final counts. The original full-review coverage degradation is not retroactively removed.

Receipt completed; independent review is **not complete**. This host exposes no native subagent launcher. All 11 selected generic reviewers remain undispatched: correctness, project-standards, testing, maintainability, security, performance, api-contract, reliability, data-migration, adversarial and julik-frontend-races. The parent performed the available review and finish work. No independent agreement or validator verdict is claimed.

## Scope and boundaries

HEAD 99a3079a383a4cb529c1331a596bc47f75b5f07f, branch feat/luna-content-rewrite-runtime, against the dirty tracked working tree: 123 files, 8634 changed lines, 4812 executable non-test changed lines. Initial and refreshed diff/hash artifacts preserve the concurrent edits. The reviewed snapshot includes the DOB-purpose guard, /profile return normalization, bulk revocation/history simplifications and final consent lifetime guard.

Untracked paths are excluded from the formal diff. New accounts/history code received a separate security-context review below; this is not full functional or new-file coverage. Two binary screenshot changes and unrelated content expansion were not exhaustively assessed. Existing WIP was preserved. No source/index/commit/push/deploy/provider/auth/billing or real-user writes; no real OTP, paid provider/review call or localhost5310 inspection. Only disposable synthetic test databases and review artifacts were written.

## Findings

### C1 - P1, excluded untracked IAM context

[accounts/postgres.py:75](</Users/phamhanh/Documents/New project/la-lanh/apps/api/app/domains/accounts/postgres.py:75>) loads a device before waiting on the owner lock, then reselects it without refreshing its ORM state. If a revoker commits while the reader waits, the stale object can still authorize the revoked credential. Both the helper and tracked guest repository accepted it in the synthetic proof.

Discover scalar IDs before locking, or use populate_existing=True on the locked device read, then check fresh revocation/expiry. Add a PostgreSQL barrier test for this exact interleaving. The proof uses SQLAlchemy 2.0.52 and isolated SQLite to emulate the PostgreSQL schedule, not actual PostgreSQL locks. [SQLAlchemy documents the identity-map refresh behavior](https://docs.sqlalchemy.org/en/20/orm/queryguide/api.html#populate-existing).

Parent-reproduced, confidence 100. Independent validation remains unavailable; this is a release gate, not automatic apply authority.

### #1 - P2, tracked expiry-response race

[client.ts:504](</Users/phamhanh/Documents/New project/la-lanh/apps/web/src/shared/api/client.ts:504>) retains the pre-JSON null-cookie exception. A foreign cookie arriving during JSON decoding is reported as GUEST_EXPIRED rather than SESSION_CHANGED. The boundary then clears caches and shows the expiry restart instead of the foreign-session warning. No cross-owner disclosure or server deletion was demonstrated.

Recheck that the current marker is still null after decoding, alongside the error allowlist and existing generation/epoch checks. Deferred-JSON reproduction passed. Confidence 100; protected concurrency finding remains unresolved because the independent validator could not launch.

## Separate security-context review

The new account models, helper, provider, service, tables and routes; history errors, service, repository, table and routes; migrations 0031/0032; and security-relevant identity/cookie/renewal integration were inspected. Exact paths, control checks and hashes are in [security-context-review.json](</tmp/compound-engineering-501/ce-code-review/20261010-143722-bd0530c7/security-context-review.json>) and security-context-sha256-receipt.txt.

Checked verified subject binding, untrusted metadata, Origin/CSRF, challenge replay and quotas, explicit restore/no merge, independent device ownership/revocation, encrypted identity, RLS/grants, creation-based history/grace and protected current/Saved sources. C1 remains the validated security defect.

The latest challenge DELETE retains owner and selected-device predicates. Manual root history DELETE uses the same owner-qualified criteria and current/Saved exemptions; the worker stays bounded. No additional defect was validated in these simplifications. Deployment-role permissions still require rehearsal.

The parent consent fix now checks owner expiry under its lock and raises a handled GuestExpired. The actual erasure-seam route now returns 401 with no resurrection. This does not prove credential-revocation linearization for older guest-ID-only consent writers; no separate release-critical exploit was validated there.

## Requirements and verification

R1/R2/R3/R4/R6/R7/R8 appear implemented locally or in excluded context. R5/R9 remain limited by #1/C1; R11 by C1. R10's broad lifecycle WIP was sampled, not exhaustively certified. U2/U4/U5/U6 remain partial for these defects, final regression and independent coverage. US01 AC23's separate DOB-purpose consent is wired and its Tarot-only API test passed. No validated unrequested behavior was found in inspected paths; scope limits remain.

Review-run results: 43 initial API tests; 81 expanded security-context tests; 22 latest simplification tests; 51 targeted FE tests; 7 updated cancel tests. Synthetic IAM/client race proofs passed. These counts overlap and are not summed.

The final consent regression pair produced one pass and one failure. test_consent_write_rechecks_owner_lifetime_after_preflight fails in fixture setup: fixed creation NOW=12:00 UTC is later than wall-clock expiry around 08:02 UTC, violating ck_guest_expiry_after_creation. Use coherent synthetic timestamps, then rerun. The separate fixed route proof returned 401.

User-reported full results: API 1155 passed/37 skipped; FE 251 passed/53 files; mypy 324 clean; ruff, ESLint, privacy/mobile/no-mock/contracts green; isolated TLS PostgreSQL 37 passed. They predate the final consent regression addition. The reviewer did not rerun the shared PostgreSQL cluster or the full suites.

## Coverage and verdict

ce-code-review full-depth selection/mechanics and parent finish path were used; public Supabase documentation/checklist informed auth checks. External review was prohibited. Validator infrastructure failed before launch: one formal protected finding remains unresolved; no shortcut, independent reviewer, confidence promotion or auto-apply queue. A helper implementation was inadvertently inspected; the documented mechanics output alone governs numbering/suppression. This is an instruction-fidelity deviation.

SMTP/provider identity deletion, live role/RLS rehearsal, native devices and production verification remain intentional release gates. Keep auth off; do not claim live optional login.

**Verdict: Not ready for release sign-off.** First resolve C1 and obtain independent security confirmation, then close #1 and rerun the clock-corrected consent regression. Formal actionable queue: empty because independent protected-finding validation was unavailable. Concrete suggested fixes and reproduction evidence remain supplied for human follow-up.

[Machine receipt](</tmp/compound-engineering-501/ce-code-review/20261010-143722-bd0530c7/review.json>) contains the complete bounded handoff.
