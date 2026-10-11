# Security and content execution receipt

Updated 2026-10-09, Asia/Ho_Chi_Minh. Supersedes the earlier documentation-only handoff.

Canonical plan: [Security, content and onboarding](../plans/2026-10-09-0820-fix-security-content-onboarding-plan.md). The active-run scope is U2/U3/new Tarot U4; broader roadmap requirements remain open. This receipt is local evidence, not permission or evidence of release.

Subsequent owner-requested local full-flow/animation review: [2026-10-09 receipt](2026-10-09-full-flow-tarot-reveal-review.md). Frontend now 220 passing checks, plus real optional-birth and private Radar unknown-time browser proof. This does not close the broader audit/release or paid-provider gates below.

## Actual progress

| Unit | Implemented and verified locally | Still required |
|---|---|---|
| U1–U2 privacy | Precision removal cleans retained derived data; profile revision checks reject stale writes; external Radar rewriting requires both subjects' consent. Frontend cancels old responses, clears chart-derived caches and rejects stale experiment/context callbacks. | Full retained-scan triage, cross-process and remaining mutation surfaces. Not a completed security audit. |
| U3 cost/database | Persistent daily/month limits, verified TLS, erasure/execution locks and atomic publication. 23 isolated PostgreSQL checks include actual process kill and terminated DB connection, plus UTC day/month rollover with no send against an old reservation. Worker production Settings secret mounts are tested with fake fixture files. | Key permissions/mounts, live migration/roles, provider controls and rotation on deployment target. Backfill cannot reconstruct spend from already-deleted historical rows. |
| U4 Tarot | Six contextual banks cover all 78 cards, including 312 new work/communication/energy/self-care entries. Closed meaning brief, eight purpose codes with 24 action variants, three ordered cross-card links, summary-first UI and fact/plain-language/polarity gates. | Full combinations and purpose coverage are not implemented. Keyword classification and heuristic gates cannot prove meaning preservation. Older readings are not silently migrated. Paid rewrite quality and real-reader comprehension not exercised. |
| U4 Astro | Existing direct daily meaning briefs and gates preserved. Ten synthetic personas cover daily/natal/Tarot. | Audit each active runtime surface, not just 13 enum values; medium findings and missing meaning-brief adapters remain. |
| U5 intro | Owner selected option 1 with richer motion. Revised keyframe shown, selected reference saved in repo, replacement welcome implemented with three real raster assets and independent loops. Local welcome → birth → reveal → Home, demo/privacy, pause persistence, small/desktop and dark/light verified. | Native platform performance and OS-level reduced-motion manual check; final release review. Local implementation, not production. |
| U6 second voice | Three stronger affectionate-sharp voice samples saved; direct is the approved default. Specific selection requested, not the approved scope again. | Owner selection before prompt/selector; vulnerable subjects stay direct. |
| U7 delivery | Backend/frontend checks and isolated browser QA; no paid app API request. | Mandatory review runner failed before leaf dispatch (`Operation not permitted`); no successful formal review receipt. Remaining roadmap requirements and release authority are still needed. No commit, push or production deploy. |

## Latest evidence

- Backend default suite: **1,026 passed / 23 opt-in cases skipped**. Skips are not counted as passing.
- PostgreSQL suite: **23 passed** against localhost:55432 only. Includes parallel reservations, erasure locks, stale execution, rollback, actual DB connection termination and worker process kill, UTC rollover, pair consent, TLS, RLS isolation and legacy backfill. Not proof of live Supabase configuration. Sandbox networking denied the first rerun; the permitted isolated-local rerun passed, not an ignored product failure.
- Frontend: **209 passed / 48 files**; lint/typecheck/build and runtime/privacy/mobile source guards passed. Approximately 754 kB bundle warning remains.
- Ruff/formatting and mypy on **294 app/test/script sources** passed.
- Tarot audit: **8,424 contextual + 11,232 recognised-goal rotating synthetic spreads**, plus deck checks. Not all possible combinations or a human study.
- Content review: earlier **10 synthetic personas / 30 readings**, with **13 medium follow-ups**, remains distinct from the new [ten-question Tarot corpus](security-content-2026-10-09/tarot-purpose-corpus.md). Neither is ten real testers or paid Luna output.
- Browser: isolated 5310/8030, actual Tarot question → select three cards → summary → details. Mobile 390 × 844 and desktop 1280 × 900, no horizontal overflow. [Tarot mobile proof](security-content-2026-10-09/tarot-mobile.jpg), [Tarot desktop proof](security-content-2026-10-09/tarot-desktop.jpg). New welcome → date-only birth → reveal → Home also passed using synthetic data, plus demo/privacy, pause persistence and light/dark. [Welcome mobile proof](security-content-2026-10-09/welcome-mobile.jpg). Full optional-birth/Radar/native flows still required.

## Latest red-to-green checks

- Experiment choose restored an erased result; undo/reflection rollback briefly restored it before a refetch. Three new tests observe all cache writes, not just the final screen. A per-client lifecycle revision now rejects these stale callbacks.
- Both a previously opened and a delayed contextual Home reading survived precision withdrawal. Two new tests fail on the old implementation and pass with the lifecycle revision attached to contextual state and publication.
- Browser QA exposed a relationship question receiving workplace wording for Ace of Pentacles. A failing context test now passes with the relationship meaning bank, without modifying the selected card facts. Renderer version advanced to tarot-renderer-v3.
- Real PostgreSQL backfill uses synthetic paid and reserved costs across a UTC month boundary. Upgrade yields September 700 and October 1100 nanos, then rolls the test transaction back; it never changes live data.
- Welcome test was first updated to the selected direct copy and new pauseable raster hero. Two assertions failed against the old welcome, then passed after implementation. Three new behavior tests cover pause, failed consent retry with the same key, and shared pause across the real AppShell navigation. Existing Radar/restart tests stay green.

## Review disposition

The actual ce-code-review orchestration returned **failed**, run `20261009-200134-74208729`, artifact path `/tmp/compound-engineering-501/ce-code-review/20261009-200134-74208729`. Required CLI reviewer/finish dispatch was denied by the environment; there is no report-leaf return, independent merged review or cross-model receipt. Paid peer review was prohibited. Shipping remains stopped; local implementation and tests continue without relabelling the review successful.

Three locally supported content findings were reproduced and fixed inline:

1. An apology question received “tiếp tục tìm hiểu” advice. A failing test now passes with purpose-constrained actions and distinct reflections; the card core/pitfall remains contextual.
2. A Tower warning was summarised as “Kết luận cả mối quan hệ…”. The overview now explicitly frames pitfalls as cautions and separates next-step advice from card meaning.
3. The rewrite function accepted “không cần lắng nghe” despite reciprocal-listening source meaning. Four failing cases (position/headline/overview/closing) now reject that inversion. This is a regression tripwire, not complete semantic verification.

Additional UX checks remove duplicate advice from action-position explanations, the ungrammatical “nói về muốn” assembly and the abstract “Mục tiêu là đưa câu cần nói ra trước lớp…” boilerplate. Advice has its own UI block; the explanation retains the card core and pitfall. A narrow regression excludes an explicitly declined apology goal (“không muốn xin lỗi”); indirect wording and broader negation remain limitations of keyword recognition.

Latest live-local browser proof covers both a three-card apology and a five-card work handoff: question → committed fan → chosen cards → overview first → expandable chapters. Selected card order and purpose remain intact. [Latest mobile overview](security-content-2026-10-09/tarot-purpose-mobile.png). Existing session revisions were not rewritten; start a new draw to review new copy. This is not live production or paid Luna proof.

The three simplify reviewers were closed. Applied: hoist question classification, fold stop words once, remove unused context-lens fields. Skipped: private cross-domain text-fold reuse, regex cache, repeated brief computation and extra frame abstractions; no measured benefit justified the coupling/abstraction. No changes were staged or committed.

Deep scan `9bdffbe3-169e-449a-bad2-3dde3de736e6` is terminal failed due quota. Partial results preserved; full coverage and final consolidation unavailable. Do not restart or relabel that scan.

Two independent scoped security reviewers actually ran. Their findings were checked against regression tests and fixes. This does not substitute for complete ce-doc-review, final ce-code-review or scan-wide coverage.

Detailed security evidence stays in the managed artifact store, not public product documents. Supplemental receipt: `hardening/2026-10-09-postgres-content-verification.md`.

## Next execution

1. Preserve dirty checkout and failed scan state. Never stage all existing edits or reset user changes.
2. Use only synthetic local PostgreSQL. Fixture refuses hosts other than 127.0.0.1, ports other than 55432 and databases other than la_lanh_security_test. Never substitute live Supabase.
3. Finish remaining security validation and runtime content review. CMS remains optional.
4. Intro option 1 is selected and implemented. Obtain only the remaining specific voice choice without re-asking the approved overall scope or intro selection.
5. Implement the selected voice, finish remaining flows/reduced-motion checks, complete shipping review.
6. Deploy only after gates and new release authority; local green tests are not live deployment.

## Spend and environment

Latest application ceiling **USD1/month**, not USD1/day. App limits cannot stop a stolen provider key being used elsewhere. No paid API calls, purchases, key transfer/rotation or billing changes in this continuation. Live flags and key permissions not newly verified.

PostgreSQL built from the [official 17.11 distribution](https://www.postgresql.org/ftp/source/v17.11/) with checksum verification and a synthetic local TLS certificate. Files remain only under /private/tmp/la-lanh-pg-verify; no system install, paid database or production records.
