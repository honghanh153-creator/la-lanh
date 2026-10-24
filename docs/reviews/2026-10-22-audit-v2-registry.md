# Audit v2 registry (revision 12, after the Codex r11 verdicts of 24/10/2026)

Sources: `la-lanh-audit-2026-10-22/claude-prompt-v2.md` and `privacy-content/`; Codex exact-head reviews in
`la-lanh-review-audit-v2-2026-10-22/` and on each PR. The audit PRs branch from
`c3fab3311d659c240da944a84fec305eca416cc6`. Since then the approved PRs were merged into `collab/integration`, which is
now `b5e4427` (#40, #9, #44, then #66, #17, #41–#43, #46, #47, #49–#59, #61–#63, #65, #67). **`main`/production is
still `c3fab33`**: nothing merged here is released. The only runtime evidence is O01's disposable Compose proof on a
GitHub-hosted runner; nothing is verified on staging or production. Open: #45, #48, #60 (this PR), #64, #69, #70–#78
(#68 stays unreviewed by owner decision). Rows below carry the latest verdict per PR as of revision 12, each checked against a Codex comment naming the exact full SHA; heads pushed
after a verdict are marked "awaiting re-review": the REQUEST_CHANGES or APPROVE stands only for the exact SHA it
names, until Codex reviews the new head. The registry's own live-head check proves only that the heads listed match
GitHub; it says nothing about verdicts, test quality or runtime behaviour.

Status values: `OPEN`, `PARTIAL` (some of the requirement fixed locally, the rest open), `MERGED_INTEGRATION` (approved
and merged into `collab/integration`, not released to `main`/production), `FIXED_LOCAL` (code or docs
plus red→green regression in an **unmerged** PR; for a head that has not been re-reviewed yet this is the author's
claim), `VERIFIED_RUNTIME` (seen working on a real environment: only O01's four disposable Compose behaviours on a
GitHub-hosted runner; **nothing on staging or production**), `OWNER_DECISION`, `DEFERRED`.
"Verdict" is Codex's latest verdict and the exact SHA it was for; a newer head needs a new verdict.

## A. Privacy and data lifecycle

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| P01 | Raw Tarot question out of Web Storage | MERGED_INTEGRATION | #41 `1fb1c83c8b59a7f64d7d9fd0cf78e5d4aa6e1cc8` · APPROVE @ same · merged into integration (`17df2cf`) | release to main (owner order) | staging check after merge |
| P02 | Deferred matching: no new collection | MERGED_INTEGRATION | #42 `0d49c6233ad899b7b45b85da7ce441e6e0f5ac90` · APPROVE @ same · merged into integration (`b315a5c`) | release to main (owner order) | staging flag stays false |
| P03 | Triage of 75+11 retained findings | PARTIAL | #59 `8c595f3c170ab0a1e37f1fbc5f80dca53ffedc76` · APPROVE @ same · merged into integration (`449a8a5`) (RC-05 side note corrected: an off surface never stores a job). Low fixes #55/#56/#57/#58 APPROVE; RC-05 #61 `da714a3df99eb54f09227a14d8116d5649200c71` · [APPROVE](https://github.com/honghanh153-creator/la-lanh/pull/61#issuecomment-6346172828) · merged into integration (`522d350`) | operator | RC-23–27 effective native ephemeris path evidence (NEEDS_EVIDENCE) |
| P04 | TTL/owner for pending mood and saved retries | PARTIAL | #48 `0c51d84963c6236589e838bf64a875d6cb045802` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/48#issuecomment-6378685160) (captured clear counter, epoch and generation inside the queue lock). Device and real multi-event-loop proof remain verification limits | release to main (owner order); operator/device | device check on a real browser/WebView with parallel tabs |
| P05 | Physical purge of revoked/expired share; experiment wording | MERGED_INTEGRATION | #49 `76d3460cba6f5ceebb563198d271c40551156552` · APPROVE @ same · merged into integration (`c787681`) | release to main (owner order); counsel on "tối đa 30 ngày" | PostgreSQL run |
| P06 | Aggregate legacy-plaintext check + plan | PARTIAL (tooling approved) | #50 `109072dd385e5510086a741c87ef33b31b8e629a` · APPROVE @ same · merged into integration (`9c02707`) | operator: staging/prod counts via private channel | real counts; then backfill tool per owner choice |
| P07 | Backup timer, alert, restore, reconciliation | PARTIAL | #43 `1de386f5e5a027161b3c9d6110f28ef5de3a7d7b` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/43#issuecomment-6346165927) · merged into integration (`abab031`) | operator install; Codex reviews journal A | install, first backup, restore probe, alert, Supabase backup/PITR receipt. Journal A: #78 `c76b6954e656afe48784e9816beaaa431ce0355b` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/78#issuecomment-6378889433) (purge horizon, earlier [APPROVE @ 610c8ae](https://github.com/honghanh153-creator/la-lanh/pull/78#issuecomment-6377666271), plus the suggested horizon edge regressions, stated commit-delay assumption and export-before-purge operator step). #79 holds the same commit and has its own [APPROVE @ c76b695](https://github.com/honghanh153-creator/la-lanh/pull/79); GitHub shows it MERGED only into its base, #78's branch, after #78 fast-forwarded to that commit. Nothing reached integration (still `b5e4427`) or main. P07 stays PARTIAL: not deployed, the operator probe has not run, B holds, and deferred erasure kinds are unjournaled (8 explicit erasure kinds; Tarot delete, share revoke, La Chung, unsave, experiment undo and pending invite revoke still unjournaled). A disposable PostgreSQL restore probe with an interleaved dump is required (operator). B = no restore into service until it is deployed and a restore probe has replayed it |
| P08 | Log canaries; ingress/Docker; native | PARTIAL | #51 `1fcfa84368ebcda3592f3e2bc9e74ccf7c8dec0b` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/51#issuecomment-6346170351) · merged into integration (`8df0492`) | operator/device | ingress/Docker runtime logs; signed native build on device (MASVS) |
| P09 | B rights; receipt 7 d vs result 30 d | PARTIAL / OWNER_DECISION | dossier #52 APPROVE; D1 #62 `288b3ad281bb8eb3d5c1dc015592c7c68c7a70b2` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/62#issuecomment-6346173801) · merged into integration (`aae55b5`) (cookies already expired at 7 days are not revived) | owner (copy "30 ngày"), counsel D2–D4 | manual rights channel; lawful basis/notice answers |
| P10 | Apple Tracking column; disclosures; counsel dossier | PARTIAL | #52 APPROVE · merged into integration (`0cf6334`) (column fixed; dossier is not a legal conclusion) | counsel | cross-border/DPIA, store forms at submission; DPA signature tracked separately by the owner, not a gate |
| P11 | Provider/pilot gates | PARTIAL | #61 APPROVE · merged into integration (`522d350`) (roster code only, not activation or deploy); Luna Daily pilot unchanged. DPA is not a deploy or Luna gate (owner 21/10 and 23/10); the owner signs it separately | operator (aggregate count of Radar/matching rewrite consents before deploying #61) | that count |
| P12 | Google/auth acceptance | OPEN | Google stays off | operator (secret rotation via protected channel), owner | acceptance run with a test account on staging |

## B. Tarot

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| T01 | One asked target for frame, stance, goal, step | PARTIAL | #45 `58cbd2640f2f4fbcb4951fa2b97db8ebd9caed7b` · [RC @ 00a87df](https://github.com/honghanh153-creator/la-lanh/pull/45#issuecomment-6379315351) (requiring a conjunction dropped xin_loi in comma-only lists) → Claude fixed at this head (clause structure: a last segment reaches back unless it has an opener or its own predicate frame), awaiting Codex re-review | Codex re-review; Claude (residuals: bare "… không?" own clause after a reported question) | meaning/scene remains T02; longest-signal and keyword-goal overrides are a separate open item |
| T02 | Scenes follow the asked action and context, observable, no hidden advice | OPEN (draft) | workbook #67 `bdf6287907c1b00dd913ccf7ce6b33a365e87526` · [APPROVE as a draft only](https://github.com/honghanh153-creator/la-lanh/pull/67#issuecomment-6346177711) · merged into integration (`b5e4427`) as a draft, which is not copy approval (133 action×topic rows, 266 scenes); some current scenes break C4 (Ba Cốc, Tiết Chế) | owner approves copy | approval, then wiring with frozen readings kept |
| T03 | Small step with a concrete trigger | OPEN (draft) | workbook #67 (142 action×role rows, 284 steps) | owner | same |
| T04 | Card names English + Vietnamese; AC12 | MERGED_INTEGRATION | #63 `cd692bc63845f7724de1c84eb523cbe39e4707b0` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/63#issuecomment-6346174788) · merged into integration (`bc4eea1`) | owner (order/separator); device | screen reader and long-title layout on device |
| T05 | Meaning/comprehension rubric | OPEN | — | Claude + owner rubric | rubric and gate |
| T06 | Extra scenes; Tarot Luna | PARTIAL | Owner wants Tarot Luna (23/10); shared Luna budget already approved. Code on `7ca22cb`: framed brief v3 / legacy brief v2, renderer v4, gates v4. Allowlist #73 `46059af4628021eded928d5d0eefd6bbfcebe92b` · APPROVE @ same (allowlist only, not enabled) | merge after #45 (#61 and #66 are merged into integration; #61 is not deployed); then owner/operator | reader evaluation, consent/store copy, rollout, pilot, live canary receipt; extra scenes stay with T02 |

## C. Hợp gu / Radar

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| R01 | Context/voice change ≥ 50% of fit/friction | OPEN (gate red) | — | content R03 | — |
| R02 | Unknown-time contacts certain on the date domain | MERGED_INTEGRATION | #46 `780b0f7bdf8f6fbd9a4dd193257516804b7fc4d8` · APPROVE @ same · merged into integration (`465c4b6`) | release to main (owner order) | ±14 h is the reviewed known-place path only; it does not replace the place-free §1 date-only domain |
| R03 | Contact-specific sentences, context scenes, full-sentence voice | OPEN (draft) | workbook #65 `aa8bf9f44808711fc54faed5c5292afcc3bd5b68` · [APPROVE as a draft only](https://github.com/honghanh153-creator/la-lanh/pull/65#issuecomment-6346176631) · merged into integration (`4303dec`) as a draft, which is not copy approval (560 sentences, 35 contacts × 4 contexts × 4 voices; projected AC01 43/50) | owner: approval and the voice choice (runtime has `deep_dive`, no `roast`) | AC03 needs pair-specific facts or seeded variants at wiring; AC02 needs replacing, not appending |
| R04 | Range/calibration | OWNER_DECISION | spec #64 `df80d621987aaf0e3f8702b2709f133afeb58621` · APPROVE @ same (spec coherent: one outward-rounding policy). Not an approved implementation or owner policy | owner | decisions in spec §8 |
| R05 | Variants frozen at creation; grammar manifest on real output | OPEN | — | Claude after R03 | — |
| R06 | Release audit measures US-22 AC01–AC03 | PARTIAL | #47 `de6f666934b34f440057173134b4b5d513cb8959` · APPROVE @ same · merged into integration (`ef043da`) (closed-catalog oracle). The gate stays a strict xfail until R03 wiring; not complete | release to main (owner order); Claude after R03 | real AC01–AC03 pass on wired output |
| R07 | Manual-entry consent / Roast copy | OPEN | depends on P09 D3 | owner + counsel | decision, copy approval |

## D. Operations and quality

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| O01 | Kill switch; real Compose proof | PARTIAL | #40 `b5a4a74554710ffd84ac738176383290a3d18ff1` · APPROVE @ same · merged into integration (`b954ac9`). It left `pnpm check` red (grammar test pinned the old `approved_release`) → fix #66 `7ed0094e0540e54513127b75910465b73b324dec` · [APPROVE](https://github.com/honghanh153-creator/la-lanh/pull/66#issuecomment-6345745985) · merged into integration (`88a4f06`). Disposable Compose proof **PASS**: [run 39954403234](https://github.com/honghanh153-creator/la-lanh/actions/runs/39954403234) on a GitHub-hosted runner, source `7ca22cb` (script byte-identical in `b5e4427`), six PASS, cleanup 0. VERIFIED_RUNTIME for those four Compose behaviours only. Workflow/receipt #74 `7f29ffdc565aeb4af41e56a85fa436c16c512009` · APPROVE (Claude) @ same, not merged | owner (adopt #74; promote release #75); operator | kill-switch path exercised by a real staging/production deploy; release receipt |
| O02 | Daily backup | PARTIAL | #43 (see P07) | operator | install and first-run receipt; operator read-out 23/10: last backup over 45 h old, backup/check timers inactive |
| O07 | Release to main | OPEN | draft #75 at `b5e4427` (23-PR manifest verified: each merge's second parent equals its reviewed head; tree `d52cdc15`; no migration) · Claude release review: No-Go as drafted. Old #62 recipient strings still ship; successor #76 `1f7b02ad06c97edd5588267aae8a10b9a748649e` · REQUEST_CHANGES (Claude) @ same (second sentence names a regulation as the cause of browser-data loss and drops withdrawal/deletion) | owner: #76 wording and promotion decision; operator: fresh backup, timers, staging → production | approved copy, fresh backup, staging/prod receipts, disclosure re-check, post-release `approved_release` refresh |
| O03 | E2E as mandatory gate | MERGED_INTEGRATION | #53 `4e52dd7a53ec33a062e3f0452b57b2b8e6f4fbb0` · APPROVE @ same · merged into integration (`83e4c66`) | release to main (owner order) | — |
| O04 | Pin in-function copy | MERGED_INTEGRATION | #54 `aab05a1169e3c6fbc5c76965e8cfcd11ddeb02ea` (conflict resolution only) · APPROVE @ same · merged into integration (`72ec31f`) | release to main (owner order) | pins the literal inventory only, not mapping/placeholder/control-flow invariance |
| O05 | Docs/Issues sync; #17; #9 | PARTIAL | #17 `c08262eeb24fceee5a49a8d9fe3e2f8740bd6fcc` re-APPROVE · merged into integration (`7055492`); #9 was merged by the owner (`a8e80d6`, no longer deferred); Issues #5/#6/#7/#14 commented | owner | — |
| O06 | G1 / 90-day diversity / date-only pool | DEFERRED | — | owner roadmap | — |

#57 additionally has Codex's independent PostgreSQL 17.6 two-transaction red/green proof (synthetic local cluster;
not Supabase, migration or live certification).

## E. Luna sprint (plan #69)

| Step | PR · head · verdict | Status | Still missing |
|---|---|---|---|
| S1 enqueue only when the surface is on | #70 `4c08e3c853a43e1e199a273edd06319272f1f3a8` · APPROVE @ same | FIXED_LOCAL | merge |
| S2 Hợp gu payload without chart labels | #71 `58192dea24cff5a6a43e878f01488e234e5a2107` · APPROVE @ same | FIXED_LOCAL | merge (runbook conflict with #73: keep both bullets) |
| S3 Hợp gu merge gates | #72 `ebd99a761c9bcc8b9180b691fb55ca32bc456fb9` · APPROVE @ same (tripwire). Its own branch shows the inherited `approved_release` failure (2166 passed / 57 skipped / 1 failed), fixed by #66 on integration | PARTIAL | machine voice-preservation gate |
| S4 Tarot allowlist | #73 `46059af4628021eded928d5d0eefd6bbfcebe92b` · APPROVE @ same | FIXED_LOCAL (allowlist only) | merge after #45 (#61, #66 merged into integration; #61 not deployed); rollout, pilot, live canary |
| Plan | #69 `aba9988ea6199adaa74da121c05601503234f6c2` · APPROVE @ same (plan delta; not privacy or Luna completion) | — | — |
| Tarot canary controls | #77 `2573e5b50d98a338900d1b8dd593ff3b7e24ccaa` (test-only: legacy and Roast canary) · APPROVE @ same; not an allowlist or rollout change | FIXED_LOCAL | merge |

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

## Proposed merge order into `collab/integration` (plan only; nothing merged)

Not all audit PRs are approved yet: #45 `58cbd26` and this registry's new head await Codex review. Each step needs the
owner's merge order and a Codex APPROVE on the exact head being merged; re-run `CI=1 pnpm check` on integration after
each group.
1. #70 `4c08e3c` (S1), #71 `58192de` (S2), #72 `ebd99a7` (S3; its own branch shows the inherited pin failure that
   #66 already fixed on integration), #77 `2573e5b` (test-only).
2. #48 `0c51d84` (P04; already merged integration once, data map keeps P04 and P05).
3. #78 `c76b695` (P07 journal with follow-ups, approved head).
4. #45, only after APPROVE on its current head, then #73 `46059af` (S4 allowlist depends on #45). #71 and #73 add a
   bullet at the same place in the Luna runbook: keep both.
5. Docs: #64 `df80d62`, #69 `aba9988`, then this registry last, re-reviewed at its final head so it records the merges.

Draft commands for the owner/Codex, to run only after the owner orders the merge and #45 plus this registry have an
APPROVE on the exact head shown (each refuses to merge if the head moved):

```
gh pr merge 70 --merge --match-head-commit 4c08e3c853a43e1e199a273edd06319272f1f3a8
gh pr merge 71 --merge --match-head-commit 58192dea24cff5a6a43e878f01488e234e5a2107
gh pr merge 72 --merge --match-head-commit ebd99a761c9bcc8b9180b691fb55ca32bc456fb9
gh pr merge 77 --merge --match-head-commit 2573e5b50d98a338900d1b8dd593ff3b7e24ccaa
gh pr merge 48 --merge --match-head-commit 0c51d84963c6236589e838bf64a875d6cb045802
gh pr merge 78 --merge --match-head-commit c76b6954e656afe48784e9816beaaa431ce0355b
gh pr merge 45 --merge --match-head-commit <APPROVED #45 head, now 58cbd2640f2f4fbcb4951fa2b97db8ebd9caed7b pending>
gh pr merge 73 --merge --match-head-commit 46059af4628021eded928d5d0eefd6bbfcebe92b   # runbook: keep both bullets
gh pr merge 64 --merge --match-head-commit df80d621987aaf0e3f8702b2709f133afeb58621
gh pr merge 69 --merge --match-head-commit aba9988ea6199adaa74da121c05601503234f6c2
gh pr merge 60 --merge --match-head-commit <APPROVED registry head>
```

The #73 step will report the runbook conflict with #71: resolve it on the #73 branch keeping both bullets, then it needs
a fresh APPROVE before merging. Run `CI=1 pnpm check` on integration after each group.

Merging is not release: `main`/production stays `c3fab33`, #75 stays No-Go, #74 and #76 keep their owner gates, and
nothing here enables a provider or rollout.

## Combined-branch checks (local, not pushed)

### Author's local code-cohort check (revision 8, stale)

Since this run #45 moved from `87ca55f` to `00a87df` and #78 from `610c8ae` to `c76b695`; the other heads are unchanged. Test green and the live-head check do not show that no content defects remain.


Local head `06d870354c4e3fa3d2e0315c7eda394a6be5166d` (not pushed) = `collab/integration` `b5e4427` + #45 `87ca55f`,
#48 `0c51d84`, #70 `4c08e3c`, #71 `58192de`, #72 `ebd99a7`, #73 `46059af`, #77 `2573e5b`, #78 `610c8ae`, merged in
that order. One textual conflict, the Luna runbook (keep both bullets). Docs-only #60, #64 and #69 are not in it.
`CI=1 pnpm check`, first run, exit 0: audits, contracts, privacy guard, grammar, fallback approval, web 78 files /
511 tests, API 2506 passed / 57 skipped / 1 xfailed (the R06 strict xfail, not a pass), QA smoke, E2E 8/8. Author's
local synthetic run only: not re-run by Codex, not a Compose, staging or production proof, and any later head change
makes it stale.

### Author's local code-cohort check (revision 6, stale)

Since this run #45, #48 and #78 have moved; it covers none of their current heads.


Local head `65cfeab4493656100fbde114a0f5bfe28358234e` (not pushed) = `collab/integration` `b5e4427` + #45 `c9cc3d9`,
#48 `d3c9b3f`, #70 `4c08e3c`, #71 `58192de`, #72 `ebd99a7`, #73 `46059af`, #77 `2573e5b`, #78 `5579600`, merged in
that order. One textual conflict, the Luna runbook (#71 and #73 add a bullet at the same place: keep both). Docs-only
#60, #64 and #69 are not in it. `CI=1 pnpm check`, first run, exit 0: audits, contracts, privacy guard, grammar,
fallback approval, web 77 files / 504 tests, API 2501 passed / 57 skipped / 1 xfailed (the R06 strict xfail, not a
pass), QA smoke, E2E 8/8. Author's local synthetic run only: not re-run by Codex, not a Compose, staging or production
proof, and any later head change makes it stale.

### Author's local code-cohort check (revision 5, stale)

Since this run #45, #48 and #78 have moved, so it no longer covers their current heads.

Local head `b4cb913fa8acd33e69a1ef6f6ad26715796bf522` (not pushed) = `collab/integration` `b5e4427` + #45 `c912caf`,
#48 `3e120f5`, #70 `4c08e3c`, #71 `58192de`, #72 `ebd99a7`, #73 `46059af`, #77 `2573e5b`, #78 `8173a20`, merged in
that order. One textual conflict, the Luna runbook (#71 and #73 add a bullet at the same place: keep both). Docs-only
#60, #64 and #69 are not in it. `CI=1 pnpm check`, first run, exit 0: audits, contracts, privacy guard, grammar,
fallback approval, web 76 files / 498 tests, API 2490 passed / 57 skipped / 1 xfailed (the R06 strict xfail, not a
pass), QA smoke, E2E 8/8. Author's local synthetic run only: not re-run by Codex, not a Compose, staging or production
proof, and any later head change makes it stale.

### Author's local code-cohort check (revision 4)

Local head `c65145ac077fa1ef94ab9770b047f9ade4aee72d` (not pushed) = `collab/integration` `b5e4427` + #45 `7328572`,
#48 `b417b76`, #70 `4c08e3c`, #71 `58192de`, #72 `ebd99a7`, #73 `46059af`, merged in that order. One textual conflict:
the Luna runbook (#71 and #73 add a bullet at the same place: keep both). Docs-only #60, #64 and #69 are not in it.
`CI=1 pnpm check`: the first run failed one web test (`SessionBoundary.test.tsx` "gives focus back to the open sheet…",
a focus-timing assertion; the file passed 5/5 when rerun alone and none of these PRs touches it). The second run on the
same tree passed, exit 0: audits, contracts, privacy guard, grammar, fallback approval, web 75 files / 494 tests, API
2448 passed / 57 skipped / 1 xfailed (the R06 strict xfail, not a pass), QA smoke, E2E 8/8. With #66 merged the
inherited `approved_release` failure is gone. This is the author's local synthetic check, not a release or runtime proof, and Codex has not
re-run it independently. It excludes the docs PRs (#60, #64, #69) and predates #77, #78, #45 `c912caf` and #48
`3e120f5`, so it does not cover the current heads either.

### Prior round (22/10)

This is a **prior-round result** only. It did not exercise later heads: since then #45, #47, #48, #54, #59 and #64
moved, and #65, #66, #67 and #70–#78 were not in it. The separate-PR test runs cited on each PR are not a combined
proof either.

Manifest of local head `e32b7a389b8b73c11ea46b9b5480cbaddb3d2880` (built 22/10 22:31 +07 on `7ca22cb`, merged in
this order): #17 `c08262e`, #41 `1fb1c83`, #42 `0d49c62`, #43 `1de386f`, #45 `875a3ae`, #46 `780b0f7`, #47 `d4a1623`,
#48 `4f811c3`, #50 `109072d`, #51 `1fcfa84`, #52 `ab5e6a9`, #53 `4e52dd7`, #55 `07e29a3`, #56 `0f9ebfc`,
#57 `e9ff2d6`, #58 `07ffd62`, #59 `9bd729f`, #61 `da714a3`, #62 `288b3ad`, #63 `cd692bc`, #64 `bf8f281`,
#49 `76d3460`, #54 `a069306`. Two textual conflicts, both additive: `store-privacy-data-map.md` (#48 and #49 insert
paragraphs at the same place: keep both) and `fallback-approval.json` (#45's `_REFLECTIVE_FORMS` leaf and #54's 15
leaves: keep #40's release fields, add both; regenerated, 0 keys removed or changed, literal pins identical to #54).

`CI=1 pnpm check` on that tree: every audit, contracts, privacy guard, grammar and fallback approval, web 74 files,
QA smoke and E2E 8/8 pass; the API suite had **one failure inherited from #40**: `tests/grammar/test_grammar.py:367`
still expects `approved_release` `4111f03cee3c` while #40 sets `c3fab3311d65`. #66 fixes it (not in this manifest).
With that one line changed locally the API suite was 2388 passed / 57 skipped / 1 xfailed. #66 has since been merged
into integration.

## Pilot M1 (unchanged)

Daily Luna pilot review on **04/11/2026**; at most 20 opted-in sessions; the full 670-case gate is **not met** and runs
under the owner's exception; no EvaluationRecord exists or was fabricated; budget figures stay server-side.

## Not done (honest list)

T02/T03/R03 are drafts awaiting approval; T05, R05, R07, P12, journal A, rights channel, native/device and all runtime
evidence remain open. Not complete either: the R06 strict xfail, the Tarot and Daily pilots, and any release to `main`
(draft #75 is No-Go; copy PR #76 is REQUEST_CHANGES pending the owner's wording). Operator evidence: the disposable
Compose proof (O01) passed and the pre-#61 consent count was taken privately; still missing are the kill-switch path in a
real staging/production deploy, a fresh backup with #43's timers installed and their first-run receipts, a restore
probe, the Supabase backup/PITR record and the disclosure re-check for the release. #45 is still a merge prerequisite for the Tarot
allowlist; #61 (merged, not deployed) and #66 (merged) remain dependencies of any Tarot rollout. No merge, deploy, server or database access, IAM/secret/budget change, or extra
Luna/Google/paid API in this session.
