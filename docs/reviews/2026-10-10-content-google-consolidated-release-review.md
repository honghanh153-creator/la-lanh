# Content, Google entry and consolidated release review — 10 October 2026

## Release decision

**Local review candidate; not deployed, committed or pushed.** The owner requested one bundle, not a frontend-only/CMS release. Preserve all existing WIP. Preview: http://localhost:5351/welcome.

Public Google login is **No-Go** until the provider configuration, identity-erasure workflow and real two-account/two-device acceptance below are complete. Paid rewrite activation also has an unresolved foreground-lock performance gate. A guest/local-content deployment can be considered separately only after the exact image, production-role migration, privacy, backup and smoke gates pass. This receipt is not production or legal certification.

## Product contract and delivered changes

| Area | Current candidate | Evidence / boundary |
| --- | --- | --- |
| Welcome | Exactly two entry actions: **Đồng ý & bắt đầu** and **Đăng nhập**. No demo or another-profile entry. Pause/privacy remain utility controls | Existing valid device profile resumes, including restart URL; creation only after an unavailable-session response. Offline failure keeps data |
| Google | Supabase server PKCE; encrypted short-lived verifier, random state, fixed callback, single exchange, initiating credential binding | Offline provider/API tests; actual Google is not enabled or observed |
| Account restore | Explicit confirmation; no automatic merge of birth data, history or AI consent | Existing account/device lifecycle and revocation races; provider erasure still pending |
| Retention | Guest expires after 30 inactive days; linked account 365; device credential 30; automatic history separate, creation-based maximum 30 days | History activation requires disclosure/consent; saved notes/current chart sources follow profile lifetime |
| Astro | Direct authored work/relationship examples; unsupported Jyotish uses calculated structural information rather than invented Western personality | Reading renderer v12; not a claim that every sign/planet pair has a distinct deep essay |
| Tarot | Meaning first, then context and spread role; summary above expandable chapters; one main question thread rather than stacked generic advice | Renderer v6, meaning brief v2, local gate v4; all selected card meanings kept in bounded five-card summaries |
| Luna | Rewrite is a bounded wording layer, not the source of chart/card facts | Tarot rewrite gate v4 requires evidence from every selected card and checks negation/unsafe inference; local fallback on failure |
| CMS | Independent, optional review workspace | Content functions without Studio; no public reviewer-token exposure |

The broad phrase “công sức” no longer implies that someone wants recognition: explicit “ghi nhận”/“đánh giá” is needed. Question context guides controllable examples/actions, not claims about another person's thoughts.

Example of direct Home content observed with a synthetic birth date:

> **Một tin nhắn chưa rõ làm bạn nghĩ mãi.**
> Khi tin nhắn nói để sau nhé, bạn có thể đoán lý do mà chưa hỏi rõ.
> **Thử một việc nhỏ:** Chọn một chữ chưa rõ trong tin nhắn rồi hỏi người gửi giải thích.

Tarot reference: Nhà Vua Cốc preserves emotional composure; Ba Gậy preserves foresight/next-step expansion; Sáu Tiền preserves give/receive balance. A recognised apology goal changes the question/action, not those meanings. No claim to know whether the other person will forgive or what they feel.

## Review fixes

| Finding | Repair | Discriminating proof |
| --- | --- | --- |
| P1 valid resume loops back to Welcome after sibling-owner warning | Remove restart sentinel only after successful session verification and both consents | Integrated Entry/Welcome resume and failed-consent regressions |
| P1 auth-off environment templates fail startup on blank optional values | Comment optional provider settings instead of empty validated URL/key strings | Both complete environment templates instantiate with auth disabled |
| P1 interrupted committed deletion stays DELETING forever | Bounded scheduled cleanup selects DELETING independent of expiry, preserving ordered owner locks and provider-started deferral | Five SQLite regressions and four real-PG send-fence/interruption scenarios |
| P1 experiment rollback restores the previous owner's cache | Capture chart revision, session generation and owner epoch before awaits; fence optimistic writes and every completion/rollback | Pending undo/reflection/choice with session changes cannot recreate old data |
| P1 new mood timestamp breaks previous writer during rollout/rollback | Database CURRENT_TIMESTAMP default retained alongside immutable updates | Compiled migration DDL and actual PG previous-image-shaped INSERT without created_at, then UPDATE |
| P2 delayed welcome completion overrides Google navigation | Abort session verification on departure and fence subsequent mutations/navigation | Delayed completion/unavailable responses after leaving Welcome |
| P2 accepted multi-goal five-card draw loses its reading at summary gate | Mandatory card meanings first, whole optional sentences budgeted; summary focuses one main goal | Exact cards/question reproduced at engine and full selection/resume API boundaries |
| P2 month-end test fails outside 31-day months | Actual calendar month-end | February/leap-February/April/October cases and real transaction crossing budget period |
| Post-review contract mismatch: current Tarot meaning brief v2 rejected by the provider privacy parser | Explicitly permit v1 for older queued jobs and v2 for current output, without adding raw context fields | 28 focused rewrite tests pass; unknown versions and raw_question remain rejected |
| Testing gap: cookie changes without tab notification | Add direct polling/hide/mismatch-cache-clear and timer-unmount tests | SessionBoundary eight-test suite |
| Testing gap: same-owner budget race hides ledger race | Four separate owners, absent daily/monthly ledger rows, fake-provider admission | Real PostgreSQL USD 1 monthly-limit regression |

Review covers the full tracked/untracked inventory, not just files changed in this turn. Eleven native review lenses completed; detailed path inspection was sampled. No paid cross-model reviewer was launched. The immutable [code-review report](2026-10-10-content-google-code-review.json) and [metadata](2026-10-10-content-google-code-review-metadata.json) retain the review-time verdict: **Not ready**, one confirmed P2 provider-lock defect and eight findings fixed after the original review (not original false positives). Post-review test receipts below supplement that report; they do not change its validated defect or certify live acceptance.

## Verification ledger

Final local `pnpm check` completed with **exit 0** on 10 October 2026 (terminal session 83863). Earlier failing setup/lint/sandbox runs are not passing evidence. The first QA listener attempt was denied by sandbox EPERM; the final permitted loopback QA gate passed. No production network or paid provider was used.

- Web: **290 tests passed in 53 files**, ESLint and TypeScript passed.
- API: **1,206 passed, 53 skipped**; skipped PostgreSQL scenarios are covered by the separate guarded database run below. Ruff and format check passed (360 files); mypy passed (326 source files).
- Contract/runtime/privacy/mobile guards, content matrix, Tarot knowledge, synthetic editorial review, Radar experience and 670-case rewrite manifest all passed.
- QA: **three server tests passed**, production web/native-engine build passed, checksums passed, and actual guest → birth → daily-note CLI smoke passed.

- Real isolated PostgreSQL suites: **57 passed** (53 database cases plus four calendar cases), port 55434 only. Includes credential revocation/restore, send/erasure fences, mood compatibility and independent-owner budget races. Test fixtures clear only their guarded synthetic database.
- Focused Tarot engine/API after the final summary/context change: **33 passed**.
- Focused Tarot rewrite/privacy after the meaning-brief version repair: **28 passed**. The legacy/current-version allowlist remains closed to unknown versions and additional raw context.
- Local browser observed: Welcome → guest consent → birth date → **Vibe · Mộng** → top-of-Home note; three-card and five-card selection → reveal animation → summary → expandable chapter. Latest code must be used for the final handoff preview.
- Build succeeded. Existing warnings remain: main JS approximately 783 kB / 221 kB gzip, mixed static/dynamic clearPersonalData imports. They are not proof of measured slow-user incidence.
- Synthetic content audits are not human comprehension tests. Ten synthetic personas/30 readings, 19,656 Tarot spreads, 630 daily variants and a 670-case/13-surface rewrite manifest do not establish that ten real users understood the output.
- Paid Luna output, native Google callbacks, BFCache on physical devices and live provider erase are **not verified**.

Browser evidence: [final Welcome](content-google-2026-10-10/welcome-final.jpg), [mobile Welcome](content-google-2026-10-10/welcome-mobile.jpg), [Google activation gate](content-google-2026-10-10/google-gated.jpg), [Home](content-google-2026-10-10/home-mobile.jpg), [five-card summary first](content-google-2026-10-10/tarot-summary-mobile.jpg). All content fixtures are synthetic. After the final gate, the agent-owned ephemeral QA environment was restarted with the exact current backend and built frontend, without any synthetic profile retained; `/__qa/ready` returned ready and the browser showed exactly the two entry actions. The owner's existing preview and production database were not reset. Google/generation/worker flags remain off in this handoff preview.

## Remaining release gates — ordered checklist

1. [ ] Freeze an exact release manifest/commit including tracked AND new files, assets, generated contract and migrations; retain matching AGPL source. No keys, session payloads or raw logs in Git.
2. [ ] Record actual public image, schema head, generation/auth flags and approved backup retention. This review has not connected to production.
3. [ ] Rehearse migrations 0031 → 0032 → 0033 with populated legacy data and the actual least-privileged backend role. Check new private-table RLS/browser grants, the mood default and old-image write compatibility. Local test-column alignment is not a production migration rehearsal.
4. [ ] Schedule bounded cleanup at least every six hours; verify DELETING/backlog recovery, expired devices, history expiry and monitoring without personal-data logs.
5. [ ] Build and smoke the exact candidate image privately: readiness, HTTPS/proxy/headers, onboarding, current full chart/aura, daily note, Tarot 1/3/5, Radar ownership, logout/restore and erasure. Do not expose Google merely because its button exists.
6. [ ] Google: configure the correct Supabase/Google OAuth client and fixed redirect allowlist. Client Secret belongs only in the provider's protected settings; do not send it in chat or a frontend environment. Obtain provider identity-erasure integration and verify retries/idempotence without resurrecting local data. Then test two actual accounts, two browsers/devices, cancellation/replay/wrong-cookie/expiry and explicit restore. Only then approve auth flags.
7. [ ] Paid rewrite: current execution guard holds the owner-row lock across provider I/O; a slow fake/real provider can delay session reads. Rework with a durable in-flight/drain protocol and reproduce responsive foreground checks while preserving revocation/erasure/atomic-publication fences **before enabling the new paid path**. Do not weaken the lock to make the benchmark green.
8. [ ] Run approved real-provider/editorial acceptance within the existing USD 1/month cap, with separate subject consent and no raw birth details/free-text questions sent. Review actual wording with 10–20 testers; keep local fallback and a stop switch. No recharge or budget increase is authorized by this receipt.
9. [ ] Only after the applicable gates: deploy, run public fresh/returning-browser smoke and compare actual image/schema/source. Watch errors, latency, cleanup and spend. Report exact URL/version.
10. [ ] Rollback: stop admissions/workers and disable feature exposure first; use a verified compatible old image. Keep additive schema and erasure/revocation records. Do not downgrade/drop 0031–0033 or restore deleted personal data/credentials.

The application cap only controls this application's admitted calls. It does not stop a stolen API key used outside the application. Existing provider-key handling and account usage alerts still require operational review; this turn did not rotate keys or change billing.

## Sources and limits

Checked current primary documentation on 10 October 2026: [Supabase Google Auth](https://supabase.com/docs/guides/auth/social-login/auth-google), [PKCE](https://supabase.com/docs/guides/auth/sessions/pkce-flow), [server-side auth guidance](https://supabase.com/docs/guides/auth/server-side/advanced-guide), and official [Vietnam personal-data law 91/2025/QH15 metadata](https://vanban.chinhphu.vn/?docid=214590&pageid=27160). No assertion that every implementing decree or transfer obligation has been legally cleared.

Tarot meaning cross-check used first-party [King of Cups](https://biddytarot.com/tarot-card-meanings/minor-arcana/suit-of-cups/king-of-cups/) and [Three of Wands](https://biddytarot.com/tarot-card-meanings/minor-arcana/suit-of-wands/three-of-wands/) references. Authored examples are not copied book passages; no claim that complete books were ingested.
