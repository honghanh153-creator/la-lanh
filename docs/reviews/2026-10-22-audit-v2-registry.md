# Audit v2 registry (revision 3, after Codex round 2 on 23/10/2026)

Sources: `la-lanh-audit-2026-10-22/claude-prompt-v2.md` and `privacy-content/`; Codex exact-head reviews in
`la-lanh-review-audit-v2-2026-10-22/` (21 verdicts: 14 APPROVE, 7 REQUEST_CHANGES). The audit PRs branch from
`c3fab3311d659c240da944a84fec305eca416cc6`; since then the owner merged **#40, #9 and #44** and
`collab/integration` is now `7ca22cb`. All open PRs still report MERGEABLE against it.

Status values: `OPEN`, `PARTIAL` (some of the requirement fixed locally, the rest open), `FIXED_LOCAL` (code or docs
plus red→green regression in an **unmerged** PR; for a head that has not been re-reviewed yet this is the author's
claim), `VERIFIED_RUNTIME` (seen working on a real environment: **nothing here is**), `OWNER_DECISION`, `DEFERRED`.
"Verdict" is Codex's latest verdict and the exact SHA it was for; a newer head needs a new verdict.

## A. Privacy and data lifecycle

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| P01 | Raw Tarot question out of Web Storage | FIXED_LOCAL | #41 `1fb1c83c8b59a7f64d7d9fd0cf78e5d4aa6e1cc8` · APPROVE @ same | owner merge | staging check after merge |
| P02 | Deferred matching: no new collection | FIXED_LOCAL | #42 `0d49c6233ad899b7b45b85da7ce441e6e0f5ac90` · APPROVE @ same | owner merge | staging flag stays false |
| P03 | Triage of 75+11 retained findings | PARTIAL | #59 `9bd729f21fc2ad1d497cf688d5d1c6a894c1b4b6` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/59#issuecomment-6346171536). Low fixes #55/#56/#57/#58 APPROVE; RC-05 #61 `da714a3df99eb54f09227a14d8116d5649200c71` · [APPROVE](https://github.com/honghanh153-creator/la-lanh/pull/61#issuecomment-6346172828) | operator | RC-23–27 effective native ephemeris path evidence (NEEDS_EVIDENCE) |
| P04 | TTL/owner for pending mood and saved retries | PARTIAL | #48 `2d5636b2c3e362a99369e99175c0f4a8c6e660ee` · [RC @ 4f811c3](https://github.com/honghanh153-creator/la-lanh/pull/48#issuecomment-6346167173) (late failure after remount; direct ACK vs queued intent) → fixed, awaiting re-review | Codex | device check |
| P05 | Physical purge of revoked/expired share; experiment wording | FIXED_LOCAL | #49 `76d3460cba6f5ceebb563198d271c40551156552` · APPROVE @ same | owner merge; counsel on "tối đa 30 ngày" | PostgreSQL run |
| P06 | Aggregate legacy-plaintext check + plan | PARTIAL (tooling approved) | #50 `109072dd385e5510086a741c87ef33b31b8e629a` · APPROVE @ same | operator: staging/prod counts via private channel | real counts; then backfill tool per owner choice |
| P07 | Backup timer, alert, restore, reconciliation | PARTIAL | #43 `1de386f5e5a027161b3c9d6110f28ef5de3a7d7b` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/43#issuecomment-6346165927) | operator install; Claude builds journal A | install, first backup, restore probe, alert, Supabase backup/PITR receipt; journal A not built (B = no restore into service) |
| P08 | Log canaries; ingress/Docker; native | PARTIAL | #51 `1fcfa84368ebcda3592f3e2bc9e74ccf7c8dec0b` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/51#issuecomment-6346170351) | operator/device | ingress/Docker runtime logs; signed native build on device (MASVS) |
| P09 | B rights; receipt 7 d vs result 30 d | PARTIAL / OWNER_DECISION | dossier #52 APPROVE; D1 #62 `288b3ad281bb8eb3d5c1dc015592c7c68c7a70b2` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/62#issuecomment-6346173801) (cookies already expired at 7 days are not revived) | owner (copy "30 ngày"), counsel D2–D4 | manual rights channel; lawful basis/notice answers |
| P10 | Apple Tracking column; disclosures; counsel dossier | PARTIAL | #52 APPROVE (column fixed; dossier is not a legal conclusion) | counsel | DPA, cross-border/DPIA, store forms at submission |
| P11 | Provider/pilot gates | PARTIAL | #61 APPROVE (roster code only, not activation); Luna Daily pilot unchanged | owner (DPA); operator (aggregate count of Radar/matching rewrite consents before deploying #61) | DPA acceptance; that count |
| P12 | Google/auth acceptance | OPEN | Google stays off | operator (secret rotation via protected channel), owner | acceptance run with a test account on staging |

## B. Tarot

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| T01 | One asked target for frame, stance, goal, step | PARTIAL | #45 `4e02c46ba166e73435accd84cc3d515459856d8f` · [RC @ 875a3ae](https://github.com/honghanh153-creator/la-lanh/pull/45#issuecomment-6346168190) ("nhưng" contrast inside background) → fixed, awaiting re-review | Codex; Claude (residuals) | meaning/scene remains T02; longest-signal and keyword-goal overrides are a separate open item |
| T02 | Scenes follow the asked action and context, observable, no hidden advice | OPEN (draft) | workbook #67 `bdf6287907c1b00dd913ccf7ce6b33a365e87526` · [APPROVE as a draft only](https://github.com/honghanh153-creator/la-lanh/pull/67#issuecomment-6346177711) (133 action×topic rows, 266 scenes); some current scenes break C4 (Ba Cốc, Tiết Chế) | owner approves copy | approval, then wiring with frozen readings kept |
| T03 | Small step with a concrete trigger | OPEN (draft) | workbook #67 (142 action×role rows, 284 steps) | owner | same |
| T04 | Card names English + Vietnamese; AC12 | FIXED_LOCAL | #63 `cd692bc63845f7724de1c84eb523cbe39e4707b0` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/63#issuecomment-6346174788) | owner (order/separator); device | screen reader and long-title layout on device |
| T05 | Meaning/comprehension rubric | OPEN | — | Claude + owner rubric | rubric and gate |
| T06 | Extra scenes; Tarot Luna | DEFERRED | — | owner (cost) | — |

## C. Hợp gu / Radar

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| R01 | Context/voice change ≥ 50% of fit/friction | OPEN (gate red) | — | content R03 | — |
| R02 | Unknown-time contacts certain on the date domain | FIXED_LOCAL | #46 `780b0f7bdf8f6fbd9a4dd193257516804b7fc4d8` · APPROVE @ same | owner merge | ±14 h is the reviewed known-place path only; it does not replace the place-free §1 date-only domain |
| R03 | Contact-specific sentences, context scenes, full-sentence voice | OPEN (draft) | workbook #65 `aa8bf9f44808711fc54faed5c5292afcc3bd5b68` · [APPROVE as a draft only](https://github.com/honghanh153-creator/la-lanh/pull/65#issuecomment-6346176631) (560 sentences, 35 contacts × 4 contexts × 4 voices; projected AC01 43/50) | owner: approval and the voice choice (runtime has `deep_dive`, no `roast`) | AC03 needs pair-specific facts or seeded variants at wiring; AC02 needs replacing, not appending |
| R04 | Range/calibration | OWNER_DECISION | spec #64 `84e36775fe09016d283cf2372b1edabfd6f52f4e` · [RC @ bf8f281](https://github.com/honghanh153-creator/la-lanh/pull/64#issuecomment-6346175704) (rounding vs AC3) → fixed, awaiting re-review | owner after re-review | decisions in spec §8 |
| R05 | Variants frozen at creation; grammar manifest on real output | OPEN | — | Claude after R03 | — |
| R06 | Release audit measures US-22 AC01–AC03 | PARTIAL | #47 `de6f666934b34f440057173134b4b5d513cb8959` · [RC @ d4a1623](https://github.com/honghanh153-creator/la-lanh/pull/47#issuecomment-6346169353) (renderer self-certification) → closed-catalog oracle, awaiting re-review; strict xfail until R03 | Codex | — |
| R07 | Manual-entry consent / Roast copy | OPEN | depends on P09 D3 | owner + counsel | decision, copy approval |

## D. Operations and quality

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| O01 | Kill switch; real Compose proof | PARTIAL | #40 `b5a4a74554710ffd84ac738176383290a3d18ff1` · APPROVE @ same · **merged** (`b954ac9`). It left `pnpm check` red (grammar test pinned the old `approved_release`) → fix #66 `7ed0094e0540e54513127b75910465b73b324dec` · [APPROVE](https://github.com/honghanh153-creator/la-lanh/pull/66#issuecomment-6345745985) | Codex (#66); operator (disposable host only) | real Compose proof; deploy of the kill-switch fix |
| O02 | Daily backup | PARTIAL | #43 (see P07) | operator | install and first-run receipt |
| O03 | E2E as mandatory gate | FIXED_LOCAL | #53 `4e52dd7a53ec33a062e3f0452b57b2b8e6f4fbb0` · APPROVE @ same | owner merge | — |
| O04 | Pin in-function copy | FIXED_LOCAL | #54 `a069306701cb9486111c0a19b448410a1a9e0523` · APPROVE @ same | owner merge | pins the literal inventory only, not mapping/placeholder/control-flow invariance |
| O05 | Docs/Issues sync; #17; #9 | PARTIAL | #17 `c08262eeb24fceee5a49a8d9fe3e2f8740bd6fcc` re-APPROVE (not superseded); #9 was merged by the owner (`a8e80d6`, no longer deferred); Issues #5/#6/#7/#14 commented | owner | — |
| O06 | G1 / 90-day diversity / date-only pool | DEFERRED | — | owner roadmap | — |

#57 additionally has Codex's independent PostgreSQL 17.6 two-transaction red/green proof (synthetic local cluster;
not Supabase, migration or live certification).

## Owner decisions recorded 22/10/2026 (delegated: "tự quyết định theo cách bạn đề xuất")

| Item | Decision | Where it lands |
|---|---|---|
| P07 reconciliation | **A** (keyed deletion journal for explicit user actions) + C's retention re-run; **B** (no restore into service) until the journal ships | #43 doc; journal is a future PR |
| P09 D1 | Receipt lives as long as the consented result (30 days) | #62 |
| P09 D2 | Manual rights channel; verify by possession of the invite link/receipt or A deletes on request; never re-collect B's birth data | process to build after counsel |
| P09 D3 | Keep A's attestation with the 24 h private result until counsel answers | unchanged |
| P09 D4 | No automatic contact of B until counsel answers | unchanged |
| P06 | Per-table "Preferred" column of `legacy-plaintext-backfill-plan.md` | after operator counts |
| P04 TTL | Keep 24 h mood/save, 30 days unsave | #48 |

## Combined-branch check (local only, not pushed)

All PR heads above plus #17 merged onto `c3fab33` in a local worktree. Two textual conflicts, both additive:
`store-privacy-data-map.md` (#48 and #49 insert paragraphs at the same place: keep both) and
`fallback-approval.json` (#45's `_REFLECTIVE_FORMS` leaf and #54's 15 leaves: keep #40's release fields, add both;
regenerated, 0 keys removed or changed, literal pins identical to #54). Whoever merges second rebases with the same
resolution.

`CI=1 pnpm check` on the combined tree (local head `e32b7a389b8b`): every audit, contracts, privacy guard, grammar and
fallback approval, web 74 files, QA smoke and E2E 8/8 pass; the API suite has **one failure that exists on #40 alone**:
`tests/grammar/test_grammar.py:367` still expects `approved_release` `4111f03cee3c` while #40 sets `c3fab3311d65`
(reported on #40; not pushed by this session because another session owns that branch). With that one line changed
locally the API suite is 2388 passed / 57 skipped / 1 xfailed.

## Pilot M1 (unchanged)

Daily Luna pilot review on **04/11/2026**; at most 20 opted-in sessions; the full 670-case gate is **not met** and runs
under the owner's exception; no EvaluationRecord exists or was fabricated; budget figures stay server-side.

## Not done (honest list)

T02/T03/R03 are drafts awaiting approval; T05, R05, R07, P12, journal A, rights channel, native/device and all runtime
evidence remain open. No merge, deploy, server or database access, IAM/secret/budget change, or extra
Luna/Google/paid API in this session.
