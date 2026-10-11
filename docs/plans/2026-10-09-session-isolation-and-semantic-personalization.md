# Session isolation and meaningful Daily personalization

Status: local implementation and verification complete; public beta not updated.
Owner authorization: fix and test immediately. Preserve existing dirty work; no broad commit/push,
paid calls or deployment in this execution. Pre-fix HEAD: `99a3079a383a4cb529c1331a596bc47f75b5f07f`.

## Outcome and acceptance

Two independent problems require separate evidence. Ownership must be correct even if two users
receive similar authored text. Personalization must change meaning when relevant known factors
change; different words alone do not prove personalization.

- [x] Reproduce A cache surviving B session acceptance; retain same-A control.
- [x] Invalidate old caches, pending private drafts/queues and late responses on a session change.
- [x] Verify identity before showing private routes and after tab resume/sibling-session changes.
      Hide content on verification failure; Back must not silently adopt B after warning.
- [x] Bind owner GETs to the current guest, not just a valid old owner cookie. Clear stale owner
      cookies on new guest creation; preserve same-guest retry and first-time invitation onboarding.
- [x] Add separate-cookie-jar foreign read/write denial tests and synthetic real-browser A/B proof.
- [x] Rank supported meanings before deterministic wording; preserve direct Vietnamese and known
      house/phase distinctions, unknown-time limits, evidence and existing publication gates.
- [x] Carry the selected interpretation into Luna's minimized brief. Test compiler without paid calls.
- [x] Preserve daily novelty/replay and frozen historical shared/saved revisions.
- [x] Record 20-profile collision results honestly; do not create unsupported uniqueness.
- [x] Run full local API/web tests, lint/types/contracts/runtime guards and offline content review.
- [x] Align foundation, investigation addenda and future deployment checklist.
- [ ] Run environment-dependent PostgreSQL concurrency/TLS tests in the isolated configured test DB.
- [ ] Human readability testing with users; machine reviewer is not a human comprehension study.
- [ ] Native iOS/Android verification; web results cannot stand in for it.
- [ ] Isolate and approve the release patch from unrelated WIP, then deploy and run live acceptance.
      Generation/billing activation stays under its separate consent and budget gate.

## Execution order and rollback

1. Diagnose and capture red/green repros; no real private user rows.
2. Repair shared client identity/route boundary and server owner authorization.
3. Repair semantic source selection and brief, not just rewrite wording.
4. Run integration and browser checks with disposable local data and generation disabled.
5. Review only this fix scope, update receipts and hand off undeployed changes explicitly.

No new database migration or public schema is introduced by this patch. Other dirty-tree changes
contain migrations/API changes from previous work and are not implicitly part of this plan.
Rollback requires the reviewed release source/image, not an automatic database downgrade. Before
shipping, verify the chosen rollback retains any necessary session/privacy protections; an old
image with this confirmed ownership defect is not an acceptable long-term rollback target.

## Evidence

- `docs/reviews/2026-10-09-beta-session-isolation-debug.md`
- `docs/reviews/2026-10-09-daily-personalization-collision-debug.md`
- `docs/reviews/2026-10-09-daily-semantic-personalization-content-receipt.md`
- `docs/reviews/2026-10-09-session-personalization-fix-receipt.md`
