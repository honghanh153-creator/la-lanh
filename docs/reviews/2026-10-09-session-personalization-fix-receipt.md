# Session isolation + meaningful Daily personalization: local fix receipt

Date: 2026-10-09. **Local fix/test complete; public beta unchanged.**
Pre-fix HEAD: `99a3079a383a4cb529c1331a596bc47f75b5f07f` on
`feat/luna-content-rewrite-runtime`, with substantial pre-existing dirty work.
No commit, push, deployment, key/billing change or paid provider call was made.

## DebugSummary

### Report versus confirmed facts

The owner reported a friend's beta note appearing for them, then a similar note on local staging.
The device/browser relationship is not established; this is not a confirmed cross-device incident.
Two independent defects were reproduced locally with synthetic data:

1. A valid transition from guest A to guest B left A's private memory/QueryClient/draft state alive.
   The session acceptor replaced the stored epoch without invalidating private state. Direct private
   routes did not verify identity before mounting, and fallback was not bound to its session.
2. Radar/Lá Chứng/matching owner GET helpers resumed an owner credential without comparing its
   source guest with the current guest. With owner cookie A plus guest cookie B, A's history was
   returned. Mutating routes had stronger checks, so the gap was easy to miss in existing coverage.

Separately, daily editorial selection hashed factor IDs into a small issue catalog and overwrote
richer chart synthesis with generic psychology situations. Luna preserves its source meaning;
asking it for more unique wording cannot repair missing semantics upstream.

### Root repair and defense-in-depth

- `sessionIdentity.ts` centralizes request generations, cancellation, verified-cookie change
  detection and a content-free sibling-tab notice. Server credentials remain the authority.
- API requests reject obsolete responses after fetch and JSON decoding, even when fetch ignores
  abort. Changed verified cookies prevent new personal requests before they are sent.
- `acceptSessionEpoch` clears private state before adopting a different epoch or replaying writes.
  Memory fallback binds epoch, generation and cookie marker; old projections cannot replace it.
- `SessionBoundary` verifies private routes before display. It rechecks on focus/pageshow/visibility,
  cross-tab notice and local cookie change. Offline verification hides private content. A restart
  flag prevents Back/direct navigation from silently adopting B after a session-change warning.
  Same-session focus verification hides but preserves form state; warning navigation unmounts it.
- New guest creation drops stale owner credentials. All three owner gateways share
  `resume_owner_for_guest`, requiring owner/source-guest agreement on GET as well as mutation.
  Same-guest idempotent retry stays valid. A known guest switch drops old recipient capabilities;
  first-time invite onboarding retains the capability the visitor just opened.
- Welcome restores only an explicitly pending invitation intent after new guest acceptance.
  Tarot refuses to submit a question from A's tab under a session replaced by B.

The three identical owner helpers justified one central check. Cookie detection and request fencing
supplement server authorization; neither is a substitute for it. No new migration/public schema is
required by this fix. Other dirty-tree migrations and contract deltas belong to previous work.

### Semantic content repair

Daily `daily-direct-meaning-v6` / selector `daily-semantic-eligibility-v3` ranks supported meanings
before rotating wording. Known body/domain/sign, selected role, eligible pair/aspect/strength/phase
and actor-linked exact houses can change the interpretation, observable scene and action. The
explicit user topic wins over a house-derived illustration. Unknown-time houses/angles are excluded.

Fifteen authored families have bounded daily variation. Opaque owner/chart IDs, unrelated factors,
ordering and orb formatting cannot select a personality. The supported meaning, competing need,
scene/action and limitation reach the minimized Luna brief. The compiler rejects ungated baselines
and imprecise house/angle evidence. No paid Luna output was generated in this verification.

Browser comparison after restarting the latest API:

- A, synthetic date-only: “Bạn đang đoán ý từ một tin nhắn.” Scene: an unclear “để sau nhé” message.
  Action: ask about the unclear wording.
- B, synthetic full chart: “Câu hỏi về bản nháp chưa đủ cụ thể.” Scene: a draft without a specific
  feedback question, refined to work/study by a known actor-linked house. Action: ask for feedback
  on one part. The meaning is specific-feedback, not a synonym for A's missing-context reading.

The cohort20 evaluation still contains duplicates: 14 full cards, 12 meanings, 9 behavior families.
The largest repeated family is missing-context. This finite corpus does not warrant global unique
prose or scientific personality claims. Expansion must add supported distinctions, not invented
background, runtime scans of other users' text or paid retry loops. See the separate content receipt
for all counterfactual fixtures and limits.

## Verification ledger

All tests use local/synthetic data. Bundled Node and local uv runtime were used; generation and
worker were explicitly false in the disposable QA environment on web 5310 / API 8030.

| Executed check | Result |
|---|---|
| Full web Vitest | 233 passed, 51 files |
| Full API pytest | 1,045 passed, 23 skipped |
| New web session suites | 12 passed; included in full web total |
| Focused guest isolation + daily + rewrite | 38 passed; included in API total |
| Web typecheck / ESLint / build | Passed; build retains bundle-size and static/dynamic-import warnings |
| API Ruff + format | Passed, 327 files |
| API mypy | Passed, 297 files |
| OpenAPI / generated TS contract checks | Current |
| Runtime / privacy / mobile config guards | Passed; not native device acceptance |
| Content matrix audit | Passed; legacy reported 630 editorial variants is not v6 independent insight count |
| Offline ContentReviewAgent | 10 synthetic personas, 30 readings; no critical/high, 18 medium follow-ups |
| Tarot knowledge audit | 8,424 contextual + 11,232 recognized-goal spreads passed |
| Radar experience audit | 4 contexts × 4 voices passed |
| Rewrite corpus manifest | 670 synthetic cases / 13 surfaces passed; no provider calls |
| QA server unit/smoke | 3 passed; first sandbox run denied localhost binding (EPERM), rerun with permission passed |
| Diff whitespace check | Passed |

The 23 skipped tests require `LA_LANH_TEST_POSTGRES_URL` for an isolated localhost PostgreSQL
environment. This run did not execute their real concurrency, worker-termination, TLS, RLS and
consent-fencing cases. Do not use local SQLite results to certify production PostgreSQL behavior.

### Browser evidence

Two agent-created tabs in the same browser profile, real same-origin local HTTP server:

1. A welcome → date-only birth → reveal → Home: passed.
2. B creates another guest: A immediately hides old content and goes to Welcome with a warning.
3. A direct `/home` after warning: remains at Welcome; does not show either person's private card.
4. B exact-time picker + Hà Nội selection + separate consent → full Reveal/Aura → Home: passed.
5. B Tarot question → committed 78-card fan → choose 3 cards → reveal ceremony → summary/chapter
   report: passed. The ceremony completed automatically; a later click on its departed shortcut
   found no button, and state inspection confirmed the report rather than a failed draw.
6. API restarted with v6, fresh A/B journey repeated: ownership warning still works; B's visible
   meaning/scene/action differ from A as listed above. No SQLite lock or API error appeared in this
   new QA process during these journeys. Earlier obsolete QA had lock logs and was replaced.

Screenshots: `/tmp/la-lanh-session-switch-qa.jpg` (ownership warning),
`/tmp/la-lanh-personalized-note-qa.jpg` (synthetic full-chart card).
They contain no real user input, credentials or private production rows.

## PostFixQuality

- Read and followed ce-debug's investigate/fix/defense-in-depth/post-fix handoff references.
- Three ce-simplify-code persona reviews covered the fix scope read-only. Applied only small,
  behavior-preserving reductions in new files: redundant request counter, duplicate generation
  marker and unchanged-state setter. Kept defensive query clearing. Overlapping older WIP was
  excluded from simplification. Final tests were rerun after changes.
- Manual integration review checked request fences, public invite/share route exceptions, common
  owner helper, cleanup order, explicit restart, same-guest retry and precision-bound evidence.
- Updated execution plan, diagnosis addenda, foundation, privacy data map and deployment gates.
- No automatic commit/PR workflow: the fix overlaps earlier API client/Welcome/Tarot content WIP.
  A blanket stage would include unrelated work. No issue of record was found in the prior search.

## Documentation, security and privacy gates

Documentation: guest-first onboarding, optional birth precision, direct daily meaning, owner-only
history and frozen shared revisions remain aligned. This local patch has no new API fields.
The foundation now distinguishes finite wording combinations from semantic depth.

Security: confirmed stale private-cache and owner/guest mismatch paths fixed and covered by red/green
tests. CSRF/origin checks and HttpOnly server credentials remain. Public capabilities retain their
existing scope, no-store/no-referrer behavior; no new public access, credential or processor was added.
This is a targeted fix, not completion/certification of the earlier exhaustive security scan.

Privacy: no new birth/background/mood/free-text collection. Cross-tab notice contains only a random
local marker, not identity or content. Owner-bound derived evidence stays in its existing backend
flow; static collision evaluation never reads real user prose. Cleared browser state is not deletion
of another guest's server records. Native storage/cookies need separate device verification.

Primary sources checked on 2026-10-09:

- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
  informed the identity lifecycle and multiple-cookie review.
- [OWASP Web Cache Security](https://cheatsheetseries.owasp.org/cheatsheets/Web_Cache_Security_Cheat_Sheet.html)
  informed separating public asset caching from owner-bound private response state.
- [OWASP MASVS-PRIVACY-1](https://mas.owasp.org/MASVS/controls/MASVS-PRIVACY-1/)
  informed the no-new-collection/minimization review; native compliance is not claimed.
- [Vietnam Law 91/2025/QH15 official page](https://vanban.chinhphu.vn/?docid=214590&pageid=27160)
  verified the named privacy-law reference. No new processor/transfer was introduced; this is not
  a legal compliance opinion or evidence that all deployment obligations have been discharged.

## Remaining acceptance and release work

- Beta still serves the previously observed `a7fadf7e4511`; local success does not fix live users.
  Before deployment, isolate reviewed source from unrelated WIP, publish the approved source, run
  required database checks, deploy and repeat live synthetic acceptance with rollback evidence.
- Real independent-device reproduction of the owner's original report is still unconfirmed.
  Do not mask it with different wording or claim a live Supabase isolation audit occurred.
- Obtain user comprehension feedback. Medium reviewer findings and repeated cohort families remain
  editorial follow-ups, not solved by a green technical test suite.
- Paid rewrite quality/rollout, native device checks and the environment-dependent PostgreSQL tests
  remain separate gates. No spending permission or budget setting changed here.
