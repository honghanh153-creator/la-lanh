# Audit v2 registry (revision 29, 27/10/2026: five merges, integration `010b27e`, independent CI PASS)

Sources: `la-lanh-audit-2026-10-22/claude-prompt-v2.md` and `privacy-content/`; Codex exact-head reviews in
`la-lanh-review-audit-v2-2026-10-22/` and on each PR. The audit PRs branch from
`c3fab3311d659c240da944a84fec305eca416cc6`. Since then the approved PRs were merged into `collab/integration`: first
#40, #9, #44, then #66, #17, #41–#43, #46, #47, #49–#59, #61–#63, #65, #67 (to `b5e4427`); then, on the owner's order of
25/10/2026, #70–#73, #77, #48, #78, #80, #45, #64, #69 and #60, which is now **`3d34eb4`** (see "Merged into
`collab/integration`"). On 26/10 #82, #81, #76, #74, #84, #85 and #86 followed (integration `7e6d69e`). On the owner's
release order of 26/10 #75 merged that exact commit into `main` = **`89ebdb0`**, which is **live on staging and
production** (see "Release `89ebdb0cf6b9`"); integration was fast-forwarded to it. Runtime evidence now covers that
release's staging/production smokes and the backup timers. On 26–27/10 #90, #91, #89, then #98, #92, #94 and #97
merged into integration, which is now **`95c058c`** with an independent Codex CI PASS (r39), not released (see
"26/10 evening–27/10"). On 27/10 Codex r42 approved the test follow-ups #100 and #101 at their exact heads; neither
is merged (see "27/10: test follow-ups approved (r42)"). Codex r43 then approved P07 journal batch 1 #102 and registry
revision 27 #103. On the owner's order of 27/10 #99, #103, #100, #101 and #102 merged into integration, which is now
**`010b27e`** with an independent Codex CI PASS (r45), not released (see "27/10: five merges"). Batch 2 #105 and
registry r28 #107 are approved, not merged; the PostgreSQL probe #106 had REQUEST_CHANGES and is fixed at a new head
awaiting re-review, never executed. P07/B still holds. #68 stays unreviewed by owner decision. Rows below carry the latest verdict per PR as of revision 23, each checked against a Codex comment naming the exact full SHA; heads pushed
after a verdict are marked "awaiting re-review": the REQUEST_CHANGES or APPROVE stands only for the exact SHA it
names, until Codex reviews the new head. The registry's own live-head check proves only that the heads listed match
GitHub; it says nothing about verdicts, test quality or runtime behaviour.

Status values: `OPEN`, `PARTIAL` (some of the requirement fixed locally, the rest open), `MERGED_INTEGRATION` (approved
and merged into `collab/integration`, not released to `main`/production), `FIXED_LOCAL` (code or docs
plus red→green regression in an **unmerged** PR; for a head that has not been re-reviewed yet this is the author's
claim), `RELEASED` (approved, merged and live in production release `89ebdb0cf6b9`; the row's "evidence still missing"
column still applies), `VERIFIED_RUNTIME` (seen working on a real environment: O01's four disposable Compose behaviours
and the release-receipt checks of 26/10), `OWNER_DECISION`, `DEFERRED`.
"Verdict" is Codex's latest verdict and the exact SHA it was for; a newer head needs a new verdict.

## A. Privacy and data lifecycle

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| P01 | Raw Tarot question out of Web Storage | RELEASED | #41 `1fb1c83c8b59a7f64d7d9fd0cf78e5d4aa6e1cc8` · APPROVE @ same · merged into integration (`17df2cf`) | — | staging check after merge |
| P02 | Deferred matching: no new collection | RELEASED | #42 `0d49c6233ad899b7b45b85da7ce441e6e0f5ac90` · APPROVE @ same · merged into integration (`b315a5c`) | — | staging flag stays false |
| P03 | Triage of 75+11 retained findings | PARTIAL | #59 `8c595f3c170ab0a1e37f1fbc5f80dca53ffedc76` · APPROVE @ same · merged into integration (`449a8a5`) (RC-05 side note corrected: an off surface never stores a job). Low fixes #55/#56/#57/#58 APPROVE; RC-05 #61 `da714a3df99eb54f09227a14d8116d5649200c71` · [APPROVE](https://github.com/honghanh153-creator/la-lanh/pull/61#issuecomment-6346172828) · merged into integration (`522d350`) | operator | RC-23–27 effective native ephemeris path evidence (NEEDS_EVIDENCE) |
| P04 | TTL/owner for pending mood and saved retries | PARTIAL | #48 `0c51d84963c6236589e838bf64a875d6cb045802` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/48#issuecomment-6378685160) (captured clear counter, epoch and generation inside the queue lock). Device and real multi-event-loop proof remain verification limits · merged into integration (`9a86179`) | operator/device | device check on a real browser/WebView with parallel tabs |
| P05 | Physical purge of revoked/expired share; experiment wording | RELEASED | #49 `76d3460cba6f5ceebb563198d271c40551156552` · APPROVE @ same · merged into integration (`c787681`) | counsel on "tối đa 30 ngày" | PostgreSQL run |
| P06 | Aggregate legacy-plaintext check + plan | PARTIAL (tooling approved) | #50 `109072dd385e5510086a741c87ef33b31b8e629a` · APPROVE @ same · merged into integration (`9c02707`) | operator: staging/prod counts via private channel | real counts; then backfill tool per owner choice |
| P07 | Backup timer, alert, restore, reconciliation | PARTIAL | **Alert channel (owner, 26/10):** a local scheduled task `la-lanh-ops-watch` on the owner's Mac (every six hours, read-only SSH checks of timers, failed units, markers, backup age/checksum, journal copy, disk, `/v1/ready`). A failure opens a public `ops-alert` issue with data-free facts and fix prompts. Its first run started 26/10 15:28 UTC and stalled, most likely on a tool approval, so **delivery is not yet proven**. It runs only while the Mac app is open. Off-site Google Drive backup is deferred by owner choice. **26/10: #43 timers and #78 journal live in `89ebdb0`; backup/check/journal timers installed, first runs pass; restore probe of the new backup passes ([receipt](production-release-2026-10-26/receipt.md)). Still open: interleaved replay probe, alert channel, Supabase PITR record, unjournaled kinds; B holds.** #43 `1de386f5e5a027161b3c9d6110f28ef5de3a7d7b` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/43#issuecomment-6346165927) · merged into integration (`abab031`), released in `89ebdb0` | operator: interleaved replay probe; owner: alert channel | interleaved replay probe, alert delivery, Supabase backup/PITR receipt, unjournaled kinds (install, first backup and restore probe done 26/10). Batch 1 of the missing kinds: #102 `e5819ccee6ad87c33a050ee90a69119959f266d6` (Tarot session delete, share revoke, saved-note unsave) · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/102#issuecomment-6443347549) (Codex r43) · merged into integration (`010b27e`), not released. Batch 2: #105 `17a65445f85ef54907105dea857d9516c94f10b7` (La Chung revoke/withdraw/hide/delete, experiment undo, pending Radar invite revoke) · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/105#issuecomment-6445069855) (Codex r44), not merged. Until a release every deferred kind stays unjournaled in production (batch 2 also in integration). Disposable PostgreSQL probe #106: REQUEST_CHANGES @ `8201ff0` (r44), fixed at `442ce98`, awaiting re-review, not executed. Journal A: #78 `c76b6954e656afe48784e9816beaaa431ce0355b` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/78#issuecomment-6378889433) (purge horizon, earlier [APPROVE @ 610c8ae](https://github.com/honghanh153-creator/la-lanh/pull/78#issuecomment-6377666271), plus the suggested horizon edge regressions, stated commit-delay assumption and export-before-purge operator step). #79 holds the same commit and has its own [APPROVE @ c76b695](https://github.com/honghanh153-creator/la-lanh/pull/79). #78 merged into integration (`99d7d90`) on 25/10 and was released in `89ebdb0` on 26/10. P07 stays PARTIAL: the interleaved operator probe has not run, B holds, and deferred erasure kinds are unjournaled (8 explicit erasure kinds; Tarot delete, share revoke, La Chung, unsave, experiment undo and pending invite revoke still unjournaled). A disposable PostgreSQL restore probe with an interleaved dump is required (operator). B = no restore into service until an interleaved restore probe has replayed the deployed journal |
| P08 | Log canaries; ingress/Docker; native | PARTIAL | #51 `1fcfa84368ebcda3592f3e2bc9e74ccf7c8dec0b` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/51#issuecomment-6346170351) · merged into integration (`8df0492`) | operator/device | ingress/Docker runtime logs; signed native build on device (MASVS) |
| P09 | B rights; receipt 7 d vs result 30 d | PARTIAL / OWNER_DECISION | dossier #52 APPROVE; D1 #62 `288b3ad281bb8eb3d5c1dc015592c7c68c7a70b2` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/62#issuecomment-6346173801) · merged into integration (`aae55b5`) (cookies already expired at 7 days are not revived). D2 API and procedure #80 `52f08bafaa3ba741dacb3f64c1b17af0a523cd5c` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/80#issuecomment-6385370273) · merged into integration (`10989fa`) | owner (copy "30 ngày", D2 screen copy), counsel D2–D4 | D2 web screens; data export decision; lawful basis/notice answers |
| P10 | Apple Tracking column; disclosures; counsel dossier | PARTIAL | #52 APPROVE · merged into integration (`0cf6334`) (column fixed; dossier is not a legal conclusion) | counsel | cross-border/DPIA, store forms at submission; DPA signature tracked separately by the owner, not a gate |
| P11 | Provider/pilot gates | PARTIAL | #61 APPROVE · merged into integration (`522d350`), released in `89ebdb0` (roster code only; not activated); Luna Daily pilot unchanged. DPA is not a deploy or Luna gate (owner 21/10 and 23/10); the owner signs it separately | operator (aggregate count of Radar/matching rewrite consents before deploying #61) | that count |
| P12 | Google/auth acceptance | OPEN | Google stays off | operator (secret rotation via protected channel), owner | acceptance run with a test account on staging |

## B. Tarot

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| T01 | One asked target for frame, stance, goal, step | PARTIAL | #45 `e2e5b4c2eae8f7180f8d571a3666a38bb95154aa` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/45#issuecomment-6398062394) (integration merge plus the one-line `question_frame#function_literals` pin for the rule token "nên"; logic byte-identical to [APPROVE @ 56c0247](https://github.com/honghanh153-creator/la-lanh/pull/45#issuecomment-6397238926)). Author's runs: full API 2,456 passed / 57 skipped / 1 xfailed. Codex: fallback check, 14 probes and an independent 18/18 census · merged into integration (`d7177f2`) | Claude for the lexical/goal follow-up | still PARTIAL: lexical action signals and keyword-goal overrides; two own questions after a reason keep the first; meaning/scene and copy remain T02/T03; machine audit is not human comprehension or copy approval |
| T02 | Scenes follow the asked action and context, observable, no hidden advice | OPEN (copy decided under delegation 26/10 and polished by Codex; not served; see the r29 correction) | workbook #67 `bdf6287907c1b00dd913ccf7ce6b33a365e87526` · [APPROVE as a draft only](https://github.com/honghanh153-creator/la-lanh/pull/67#issuecomment-6346177711) · merged into integration (`b5e4427`) as a draft (133 action×topic rows, 266 scenes); decisions recorded in #85; Codex wording pass in the workbook's "Codex wording pass (26/10/2026)" section; some current scenes break C4 (Ba Cốc, Tiết Chế) | Claude: review Codex's polished lines, then a wiring PR with versioning, frozen readings and the audit (wiring PR #110 is in review) | wiring merged and released; T05 comprehension gate; no reader has seen this copy |
| T03 | Small step with a concrete trigger | OPEN (as T02) | workbook #67 (142 action×role rows, 284 steps); decisions #85; Codex wording pass as T02 | Claude, as T02 (same wiring PR) | as T02 |
| T04 | Card names English + Vietnamese; AC12 | RELEASED | #63 `cd692bc63845f7724de1c84eb523cbe39e4707b0` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/63#issuecomment-6346174788) · merged into integration (`bc4eea1`) | owner (order/separator); device | screen reader and long-title layout on device |
| T05 | Meaning/comprehension rubric | OPEN | — | Claude + owner rubric | rubric and gate |
| T06 | Extra scenes; Tarot Luna | PARTIAL | Owner wants Tarot Luna (23/10); shared Luna budget already approved. Code on `7ca22cb`: framed brief v3 / legacy brief v2, renderer v4, gates v4. Allowlist #73 `3760dcd1ebd0557139ea2d71734be7eddd5c197b` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/73#issuecomment-6398063830) · merged into integration (`d140799`), released in `89ebdb0` (allowlist only, not enabled; #61 roster released too) | owner/operator | reader evaluation, consent/store copy, rollout, pilot, live canary receipt; extra scenes stay with T02 |

## C. Hợp gu / Radar

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| R01 | Context/voice change ≥ 50% of fit/friction | OPEN (gate red) | — | content R03 | — |
| R02 | Unknown-time contacts certain on the date domain | RELEASED | #46 `780b0f7bdf8f6fbd9a4dd193257516804b7fc4d8` · APPROVE @ same · merged into integration (`465c4b6`) | — | ±14 h is the reviewed known-place path only; it does not replace the place-free §1 date-only domain |
| R03 | Contact-specific sentences, context scenes, full-sentence voice | OPEN (copy and the fourth voice `deep_dive` decided under delegation 26/10, polished by Codex; not wired) | workbook #65 `aa8bf9f44808711fc54faed5c5292afcc3bd5b68` · [APPROVE as a draft only](https://github.com/honghanh153-creator/la-lanh/pull/65#issuecomment-6346176631) · merged into integration (`4303dec`) as a draft (560 sentences, 35 contacts × 4 contexts × 4 voices; projected AC01 43/50); decisions recorded in #86; Codex wording pass in the workbook (37 replacements, 29 `deep_dive` lines) | Claude: review Codex's authored edits, then a wiring PR with versioning, frozen results and the audit | AC03 needs pair-specific facts or seeded variants at wiring; AC02 needs replacing, not appending; comprehension gate |
| R04 | Range/calibration | OWNER_DECISION | spec #64 `df80d621987aaf0e3f8702b2709f133afeb58621` · APPROVE @ same · merged into integration (`f5eae3b`) (spec coherent: one outward-rounding policy). Not an approved implementation or owner policy | owner | decisions in spec §8 |
| R05 | Variants frozen at creation; grammar manifest on real output | OPEN | — | Claude after R03 | — |
| R06 | Release audit measures US-22 AC01–AC03 | PARTIAL | #47 `de6f666934b34f440057173134b4b5d513cb8959` · APPROVE @ same · merged into integration (`ef043da`) (closed-catalog oracle). The gate stays a strict xfail until R03 wiring; not complete | Claude after R03 | real AC01–AC03 pass on wired output |
| R07 | Manual-entry consent / Roast copy | OPEN | depends on P09 D3 | owner + counsel | decision, copy approval |

## D. Operations and quality

| ID | Requirement | Status | PR · head · verdict | Owner of next step | Evidence still missing |
|---|---|---|---|---|---|
| O01 | Kill switch; real Compose proof | PARTIAL | #40 `b5a4a74554710ffd84ac738176383290a3d18ff1` · APPROVE @ same · merged into integration (`b954ac9`). It left `pnpm check` red (grammar test pinned the old `approved_release`) → fix #66 `7ed0094e0540e54513127b75910465b73b324dec` · [APPROVE](https://github.com/honghanh153-creator/la-lanh/pull/66#issuecomment-6345745985) · merged into integration (`88a4f06`). Disposable Compose proof **PASS**: [run 39954403234](https://github.com/honghanh153-creator/la-lanh/actions/runs/39954403234) on a GitHub-hosted runner, source `7ca22cb` (script byte-identical in `b5e4427`), six PASS, cleanup 0. VERIFIED_RUNTIME for those four Compose behaviours only. Workflow/receipt #74 `7f29ffdc565aeb4af41e56a85fa436c16c512009` · APPROVE (Claude) @ same, merged into integration (`d00f053`) and released in `89ebdb0`; the release's `deploy.sh` ran with the #40 preflight (generation resolved `true`, worker kept) | operator | a real generation-off deploy that removes the worker (not exercised; flags unchanged by order) |
| O02 | Daily backup | VERIFIED_RUNTIME | #43 (see P07) · installed 26/10 from `89ebdb0`: `la-lanh-backup.timer` 20:10 UTC, check every six hours; first backup `la-lanh-20261026T102155Z.dump` checksum OK, freshness OK ([receipt](production-release-2026-10-26/receipt.md)) | owner: alert channel | failure alert delivery (marker is local only) |
| O07 | Release to main | VERIFIED_RUNTIME | #75 at `7e6d69e` (Codex independent CI PASS r32) merged → `main` `89ebdb0` (tree identical); staging then production deploy, migration 0038, smokes green ([receipt](production-release-2026-10-26/receipt.md), [#75 staging evidence](https://github.com/honghanh153-creator/la-lanh/pull/75#issuecomment-6413542960)); `approved_release` refreshed in this revision | — | none for this release; later releases need their own receipt |
| O03 | E2E as mandatory gate | RELEASED | #53 `4e52dd7a53ec33a062e3f0452b57b2b8e6f4fbb0` · APPROVE @ same · merged into integration (`83e4c66`) | — | — |
| O04 | Pin in-function copy | RELEASED | #54 `aab05a1169e3c6fbc5c76965e8cfcd11ddeb02ea` (conflict resolution only) · APPROVE @ same · merged into integration (`72ec31f`) | — | pins the literal inventory only, not mapping/placeholder/control-flow invariance |
| O05 | Docs/Issues sync; #17; #9 | PARTIAL | #17 `c08262eeb24fceee5a49a8d9fe3e2f8740bd6fcc` re-APPROVE · merged into integration (`7055492`); #9 was merged by the owner (`a8e80d6`, no longer deferred); Issues #5/#6/#7/#14 commented | owner | — |
| O06 | G1 / 90-day diversity / date-only pool | DEFERRED | — | owner roadmap | — |

#57 additionally has Codex's independent PostgreSQL 17.6 two-transaction red/green proof (synthetic local cluster;
not Supabase, migration or live certification).

## E. Luna sprint (plan #69)

| Step | PR · head · verdict | Status | Still missing |
|---|---|---|---|
| S1 enqueue only when the surface is on | #70 `4c08e3c853a43e1e199a273edd06319272f1f3a8` · APPROVE @ same · merged into integration (`cdb88a4`), released in `89ebdb0` | RELEASED | — |
| S2 Hợp gu payload without chart labels | #71 `58192dea24cff5a6a43e878f01488e234e5a2107` · APPROVE @ same · merged into integration (`764b8f0`), released in `89ebdb0` | RELEASED | — |
| S3 Hợp gu merge gates | #72 `ebd99a761c9bcc8b9180b691fb55ca32bc456fb9` · APPROVE @ same (tripwire). Its own branch shows the inherited `approved_release` failure (2166 passed / 57 skipped / 1 failed), fixed by #66 on integration · merged into integration (`3d78ccd`) | PARTIAL | machine voice-preservation gate |
| S4 Tarot allowlist | #73 `3760dcd1ebd0557139ea2d71734be7eddd5c197b` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/73#issuecomment-6398063830) (merges #71's approved head; both runbook bullets kept, Radar S2 before Tarot S4). Branch evidence: related suites 284 passed / 28 skipped; full API 2,192 passed / 57 skipped / **1 failed**, the inherited `approved_release` pin at `tests/grammar/test_grammar.py:367` (same failure on 46059af, fixed by #66 on integration), so the branch alone is not full-API green; on integration after merge `CI=1 pnpm check` exit 0 · merged into integration (`d140799`), released in `89ebdb0` | RELEASED (allowlist code only; Tarot not enabled) | reader evaluation, rollout, pilot, live canary (activation and evaluation stay open) |
| Plan | #69 `aba9988ea6199adaa74da121c05601503234f6c2` · APPROVE @ same · merged into integration (`fdfe5e1`) (plan delta; not privacy or Luna completion) | RELEASED | — |
| Tarot canary controls | #77 `2573e5b50d98a338900d1b8dd593ff3b7e24ccaa` (test-only: legacy and Roast canary) · APPROVE @ same · merged into integration (`5859a4d`), released in `89ebdb0`; not an allowlist or rollout change | RELEASED | — |

## Owner decisions recorded 22/10/2026 (delegated: "tự quyết định theo cách bạn đề xuất")

| Item | Decision | Where it lands |
|---|---|---|
| P07 reconciliation | **A** (keyed deletion journal for explicit user actions) + C's retention re-run; **B** (no restore into service) until the journal ships | #43 doc; journal is a future PR |
| P09 D1 | Receipt lives as long as the consented result (30 days) | #62 |
| P09 D2 | Manual rights channel; verify by possession of the invite link/receipt or A deletes on request; never re-collect B's birth data | API + procedure #80 `52f08bafaa3ba741dacb3f64c1b17af0a523cd5c` · [APPROVE @ same](https://github.com/honghanh153-creator/la-lanh/pull/80#issuecomment-6385370273) (scoped API/procedure only, not D2 completion or release; earlier RC @ bf8bb8f and @ fb83a52 addressed). · merged into integration (`10989fa`), released in `89ebdb0` (staging and production two-guest smoke green). Web screens #83 `df3fde6` · Codex APPROVE @ same · merged into integration (`288a535`), not released. Still open: release of the screens, counsel, data export |
| P09 D3 | Keep A's attestation with the 24 h private result until counsel answers | unchanged |
| P09 D4 | No automatic contact of B until counsel answers | unchanged |
| P06 | Per-table "Preferred" column of `legacy-plaintext-backfill-plan.md` | after operator counts |
| P04 TTL | Keep 24 h mood/save, 30 days unsave | #48 |

## Merged into `collab/integration` (owner order, 25/10/2026)

The owner ordered the merge (Issue #2). Before each command the live head, base and OPEN state were checked and the merge
was pinned with `--match-head-commit`; `CI=1 pnpm check` ran on the new integration head after each group. These checks
were run by Claude on the real integration heads, not by Codex.

| Group | PR · approved head → merge commit | Integration after | `CI=1 pnpm check` |
|---|---|---|---|
| 1 | #70 `4c08e3c` → `cdb88a4`; #71 `58192de` → `764b8f0`; #72 `ebd99a7` → `3d78ccd`; #77 `2573e5b` → `5859a4d` | `5859a4d` | exit 0: web 470, API 2,303 passed / 57 skipped / 1 xfailed, e2e 8/8 |
| 2 | #48 `0c51d84` → `9a86179` | `9a86179` | exit 0: web 511, API 2,303 / 57 / 1, e2e 8/8 |
| 3 | #78 `c76b695` → `99d7d90`; #80 `52f08ba` → `10989fa` | `10989fa` | exit 0: web 511, API 2,335 / 57 / 1, e2e 8/8 |
| 4 | #45 `e2e5b4c` → `d7177f2`; #73 `3760dcd` → `d140799` | `d140799` | exit 0: web 511, API 2,559 / 57 / 1, e2e 8/8 |
| 5 | #64 `df80d62` → `f5eae3b`; #69 `aba9988` → `fdfe5e1`; #60 `7c17d88` → `3d34eb4` | `3d34eb4` | exit 0: web 511, API 2,559 / 57 / 1, e2e 8/8 |

**Codex receipt, 26/10/2026 (r28), recorded separately; the table above is unchanged and remains Claude's 25/10 history.**
Codex's independent `CI=1 pnpm check` at `3d34eb4` is **red**: web 509 passed / 2 failed in `client.reliability.test.ts`
(lines 331 and 365). Codex ran the steps after the stop separately: API lint/mypy pass, API 2,559 passed / 57 skipped /
1 xfailed, QA smoke passes, E2E 8/8. Those separate passes do not make the full check green. Cause: two owner-session
fixtures expire at `2026-10-26T00:00:00Z` without a pinned clock, so they started failing once that date passed; Claude's
runs were on 25/10, before that instant. Product logic is correct. Test-only fix #82 (`5971415`) pins the clock and adds
a 60-second-buffer regression; with it `CI=1 pnpm check` exits 0 (Claude's run), awaiting Codex review. Until #82
merges, integration's full check is red. (#82 merged on 26/10; see the next section.)

(25/10, superseded by the release below.) Merging is not release: `main`/production stays `c3fab33`. The release PR #75 now points at `3d34eb4` and stays No-Go
until the owner decides #74 and #76, the operator takes a fresh backup and restores the timers, and staging →
production smoke runs. Nothing here enables a provider or rollout; Tarot is allowlisted, not on.

## Merged on 26/10 and release `89ebdb0cf6b9`

| PR · approved head → merge commit | Verdict |
|---|---|
| #82 `5971415` → `da492c9` | Codex APPROVE @ `5971415d394adef688cf58945ffac66537a95547` (Codex ran its own full check before approving) |
| #81 `834889b` → `84ad7d1` | Codex APPROVE @ `834889b108afba40044546a2a43fbda0accd1c38` |
| #76 `74bdff2` → `3775caf`; #74 `7f29ffd` → `d00f053` | Claude APPROVE (Codex-authored polish / workflow) |
| #84 `b2c6863` → `e20805a`; #85 `64dce01` → `daa0ad2`; #86 `d715c51` → `7e6d69e` | Claude APPROVE on Codex's polish (docs/workbooks only); Codex had approved earlier heads, e.g. #84 @ `774bf469e22ac68a57212fb493aefde994f00c64` |

**Codex independent `CI=1 pnpm check` at `7e6d69e1bb39f300d06ac0ee5c14471887bf60d4`: PASS** (r32, 09:50–09:57 UTC,
exit 0): web 513 / 78 files, API 2,559 passed / 57 skipped / 1 strict xfailed, QA PASS, E2E 8/8, all guards, audits,
lint and typechecks ([receipt](https://github.com/honghanh153-creator/la-lanh/pull/75#issuecomment-6413239465)). This
closes the red r28 receipt at `3d34eb4` above, which stays recorded as history. PostgreSQL skips remain unproved.

On the owner's release order the operator (Claude) took a protected backup with a restore probe, rehearsed 0038 on a
disposable copy, deployed staging, smoked it, merged #75 → `89ebdb0`, deployed production, smoked it and installed the
backup/check/journal timers. Full evidence: [production-release-2026-10-26](production-release-2026-10-26/receipt.md).
Flags are unchanged. #83, #87 and #88 (Codex APPROVE) and #89 (REQUEST_CHANGES) are not in the release.

**After the release (integration only, not released):** #87 `4db3a60` → `2cb2041`, #88 `8052eab` → `b899d11` and #83
`df3fde6` → `288a535`, each pinned to its Codex APPROVE SHA. Codex independent `CI=1 pnpm check` at
`288a5357122257f4ac583e8c294a9768e5529d80`: **PASS** (r33, 12:14–12:21 UTC): web 527 / 81 files, API 2,563 passed / 57
skipped / 1 strict xfailed, QA PASS, E2E 8/8. #91 (P3 follow-ups) has Codex APPROVE @
`53264393292dca4782950480d04b12ce339a99fe`, not merged. #89 is under re-review.

## 26/10 evening–27/10: integration `9b945e6` → `95c058c`

**Merged (owner order, 26/10):** #90 `88b1e57` → `eaca728`, #91 `5326439` → `8b73f64`, #89 `77d6875` → `9b945e6`, each
pinned with `--match-head-commit` to its Codex APPROVE SHA. Integration is **`9b945e660462963af6866dcc38a4cad47bdde628`**;
`main` stays `89ebdb0`.

**CI receipts at `9b945e6` (all kept):**
- **Claude, run 1: FAIL, exit 1.** Web 526 / 3 failed (`findBy` timeouts in RadarPrivateStartPage, BirthDatePage and
  TarotPage, under high host load).
- **Claude, run 2 (unchanged source): PASS, exit 0.** Web 529, API 2,580 / 57 / 1, e2e 8/8.
- **Codex r36, independent: FAIL, exit 1.** API 2,579 passed / 1 failed (`test_deletion_waits_for_an_already_started_provider_send`,
  SQLite `database is locked`); QA/E2E not reached.
- The integration gate is **not green**. A green rerun does not prove determinism.

**Approved, then merged on 27/10 (see below):**

| PR | Verdict | Notes |
|---|---|---|
| #92 Lá Chứng cache fence | Codex APPROVE @ `8329279326c1c5821f53dbbebad0c5c2adea9c69` | Codex full check at that SHA **FAIL, exit 1** (web 533 / 1 failed, `RadarStartPage.test.tsx:54`), kept. Later separate steps passed, which does not make that invocation a PASS. |
| #97 SQLite send-boundary lock | Codex APPROVE @ `3fe4a428c21168d66a34d0a1d4d1813c73b77f31` | Cause: a deferred read-then-write transaction cannot upgrade while deletion holds `BEGIN IMMEDIATE`. `mark_generation_request_started` and `finalize_generation_success` now take the SQLite write lock first; PostgreSQL is unchanged. Codex: the new regressions fail 3/3 on old code; the original test passed 10 fresh runs; API 2,583 / 57 / 1. Claude full check exit 0 at that SHA (its first run at `51a530f` stopped at mypy on test typing). |
| #94 owner-chain wait headroom | Codex APPROVE @ `80e8d86d78d87ab665c24d9407f8cbf6a7206a33` | `asyncUtilTimeout` 5,000 ms and `testTimeout` 15,000 ms. Codex: old config fails and head passes with a 1,100 ms history delay; a never-resolving history still rejects at ~5,010 ms; web 530 / 82 files. Claude full check exit 0 at that SHA. |

**Non-blocking test caveats (Codex r37), open as follow-ups** (27/10: both addressed by #100, Codex r42 APPROVE, not
merged; see "27/10: test follow-ups approved (r42)"):
1. **#97 barrier scope.** Order B and the send-fence test release deletion after a 100 ms sleep without observing the
   worker's entry into its blocked DB operation (`test_worker.py:758`, `:794`). Order A tolerates a bounded 500 ms
   acquisition wait (`:721–724`). The old-code failures prove the exercised schedule, not scheduling-independent
   determinism. Follow-up: operation-entry/pending-operation handshakes. The PR body was corrected.
2. **#94 guard test.** `asyncUtilTimeout.test.ts:11` compares to the literal 15,000 rather than the resolved Vitest
   `testTimeout`, and imports `setup.ts` directly. Follow-up: pin the real config and wiring.

**Still open (unchanged by the 27/10 PASS):**
- The release runbook's PostgreSQL two-connection delete-first/send-first verification has not been executed; local
  file-backed SQLite is the only database tested.
- The 57 skipped tests and 1 strict xfail remain coverage limits.
- The focus assertion race ("gives focus back to the open sheet…") is outside #94. (27/10: addressed by #101, Codex
  r42 APPROVE, not merged.)
- #94's before-fix concurrent measurements were taken under leftover stress-loop load, as disclosed in its body.

**Merged (owner order, 27/10):** #98 `9aedc8e` → `406bcbb`, #92 `8329279` → `9a96b02`, #94 `80e8d86` → `eda90c5`, #97
`3fe4a42` → `95c058c`, each pinned with `--match-head-commit` to its Codex APPROVE SHA (#98: [APPROVE](https://github.com/honghanh153-creator/la-lanh/pull/98#issuecomment-6432404118)).
Integration is **`95c058c84114c34e286b01b533d8c628bce97bdb`**; `main` stays `89ebdb0`.

**CI receipts at `95c058c`:**
- **Claude (author evidence): PASS, exit 0**, first run. Web 537 / 82 files, API 2,583 / 57 / 1, e2e 8/8.
- **Codex r39, independent: PASS, exit 0** ([handoff](https://github.com/honghanh153-creator/la-lanh/issues/2#issuecomment-6434669012)),
  05:30–05:37 UTC, separate exact-tree archive, one continuous invocation. Web 537 / 82 files, API 2,583 / 57 / 1
  (mypy 411 files), QA/native/web build PASS, Playwright 8/8. Codex also verified each merge's second parent equals the
  approved head, a contiguous first-parent chain from `9b945e6` (#98 → #92 → #94 → #97) with no conflict-resolution
  hunks, and all 1,612 tracked blobs unchanged after the run.
- Codex's earlier invocation in r39 exited 1 at the first contracts import (local Python env missing `httpx`) before
  any test ran; it is kept as a setup failure (`integration-full-ci-setup-failed-01.*`), not a product failure. No
  failing product test was retried.
- The PASS applies to `95c058c` only. It does not rewrite the red receipts above (r36 at `9b945e6`, #92 at `8329279`,
  Claude's run 1 at `9b945e6`). One pass does not prove determinism of the timeout, focus or SQLite-lock failures.
- **The exact-head check for `95c058c` is complete; no further same-SHA check is requested.** A new head needs its own
  check.

**CI PASS is not release Go.** A release of `95c058c` needs an explicit owner order and the runbook gates (backup,
restore probe, staging, smokes, production receipt). Nothing was deployed and no flag or provider changed.

## 27/10: test follow-ups approved (r42), not merged

Codex r42 ([handoff](https://github.com/honghanh153-creator/la-lanh/issues/2#issuecomment-6440414485)). Test files only;
no product code. Neither PR is merged; integration stays `95c058c`, `main` stays `89ebdb0`.

| PR | Verdict | Scope and evidence |
|---|---|---|
| #100 r37 caveats (#97 handshake, #94 guard) | r41 [REQUEST_CHANGES](https://github.com/honghanh153-creator/la-lanh/issues/2#issuecomment-6439466546) @ `451ab065ed6d694717f584f27363096c766faf53` (P2: the probe signalled before aiosqlite created the cursor) → [APPROVE @ `11281ec80f448cab778028956ac916705feb6b69`](https://github.com/honghanh153-creator/la-lanh/pull/100#issuecomment-6440400139) | The write-lock probe sits at aiosqlite's queue boundary, after cursor creation; a zero-timeout `BEGIN IMMEDIATE` on the SQLite thread decides contention, with a committed late-cursor negative control. Codex: worker file 18 passed; 20/20 fresh five-test runs; old `readings/postgres.py` from `9b945e6` fails 3/3; under r41's cursor-delay schedule the old probe `451ab06` **passes 3/3 (wrong)** and the new probe fails 3/3. The #94 guard compares `asyncUtilTimeout` with the resolved `task.timeout`, without importing `setup.ts` (found addressed in r41). The PR body was refreshed after r42 to describe the approved head; code unchanged. |
| #101 SessionBoundary focus race | [APPROVE @ `1f46985168993ee71ac0ef70cc63cceb63688c87`](https://github.com/honghanh153-creator/la-lanh/pull/101#issuecomment-6440401109) | The test waits for the sheet's mount-effect focus before moving focus, then awaits the restore effect. Codex: 17/17; under a scheduler-only clock skew the old test fails 3/3 at line 283 and the new one passes 17/17 three times; removing only the restore hook's focus call makes the new test fail. No product change. |

Limits (r42): the zero-timeout attempt proves real contention when the request arrives, not time blocked inside the
original statement; the instrumentation relies on private aiosqlite internals, confined to tests; this is not
exhaustive real-device focus verification. Claude's full `CI=1 pnpm check` at both heads (exit 0; API 2,584 / 57 / 1 at
`11281ec`, 2,583 / 57 / 1 at `1f46985`; web 537 / 82 files; e2e 8/8) is author evidence; Codex ran no full check and
did not rerun `95c058c`. A merge of either PR into integration would make a new head that needs its own check.

**Awaiting review:** #102 `e5819ccee6ad87c33a050ee90a69119959f266d6`, P07 journal batch 1 (see P07). #99 (this
registry's revision 26) keeps its r40 APPROVE @ `1b47308400a6f25c336a9fed56dfb9ca9348d67c` and awaits an owner merge
order; this revision is stacked on it and does not change that head.

Approvals are not a merge, release or provider order.

## 27/10: r43, P07 batch 1 and registry r27 approved; batch 2 and the PostgreSQL probe awaiting

Codex r43 ([handoff](https://github.com/honghanh153-creator/la-lanh/issues/2#issuecomment-6443369524)). Nothing merged;
integration stays `95c058c`, `main` stays `89ebdb0`. The "Awaiting review" line in the r42 section above is that
section's snapshot.

| PR | Verdict | Scope and evidence |
|---|---|---|
| #102 P07 journal batch 1 | [APPROVE @ `e5819ccee6ad87c33a050ee90a69119959f266d6`](https://github.com/honghanh153-creator/la-lanh/pull/102#issuecomment-6443347549) | Tarot session delete, share revoke, saved-note unsave, each keyed by the row's own id, recorded in the erasure's transaction and replayed after restore. Codex: full API 2,587 passed / 57 skipped / 1 xfailed (not a full `pnpm check`); 11 reviewer controls (record and flush failure roll back, same UUID in another kind untouched, later re-save survives, only the intended rewrite job deleted). A base revert of the recording sites failed on constructor incompatibility, not behaviour; Codex's record-only mutation gave three assertion failures. Codex's first external-control run failed at collection and a registry-check literal first failed on whitespace; both receipts are kept in its packet. |
| #103 registry revision 27 | [APPROVE @ `ad26433583844b8030a0f60dd6e244ef42317078`](https://github.com/honghanh153-creator/la-lanh/pull/103#issuecomment-6443348649) | Docs only, stacked on #99 (unchanged). |

**Awaiting review:**
- #105 `17a65445f85ef54907105dea857d9516c94f10b7`, P07 batch 2, stacked on #102: La Chung invite revoke, response
  withdraw, result hide and result delete; experiment undo; pending Radar invite revoke. Six tests (own-id digest,
  authZ/no-op records nothing, journal failure rolls back each erasure, restore + replay applied once then reflected,
  interrupted replay re-applies without change, earlier hide kept, same-UUID Radar row untouched) and five scratch
  mutations each caught. Author full check exit 0 (API 2,593 / 57 / 1).
- #106 `8201ff096540ad1943b2b1aee51406032f300b7d`, stacked on #105: gated PostgreSQL probe (`DELETE … RETURNING` with two connections,
  `pg_dump` taken while an unsave is uncommitted then `pg_restore` and replay, purge horizon through a dump) and the
  operator procedure `docs/operations/disposable-postgres-journal-probe.md`. **Prepared, not executed**: no PostgreSQL
  run exists. Its guard tests (localhost, `lalanh_probe_` name, password only in `PGPASSWORD`) run in CI; the three
  PostgreSQL checks are skipped there.

P07 stays **PARTIAL** and **B holds** until the probe has run on a disposable cluster, Codex has reviewed the receipt
and the owner decides; the journaled kinds must also be deployed. Every red receipt above stays.

## 27/10: five merges on the owner's order; integration `010b27e`, independent CI PASS (r45)

**Merged (owner order in chat, 27/10):** before each merge the live head, base and OPEN state were checked, and the merge
was pinned with `--match-head-commit` to its Codex APPROVE SHA. #103 was retargeted from #99's branch to
`collab/integration` after #99 merged; its head did not change. Branches were kept.

| PR · approved head → merge commit | Verdict |
|---|---|
| #99 `1b47308` → `799039a` | r40 APPROVE @ `1b47308400a6f25c336a9fed56dfb9ca9348d67c` |
| #103 `ad26433` → `123525e` | r43 APPROVE @ `ad26433583844b8030a0f60dd6e244ef42317078` |
| #100 `11281ec` → `6382f6f` | r42 APPROVE @ `11281ec80f448cab778028956ac916705feb6b69` |
| #101 `1f46985` → `49c8886` | r42 APPROVE @ `1f46985168993ee71ac0ef70cc63cceb63688c87` |
| #102 `e5819cc` → `010b27e` | r43 APPROVE @ `e5819ccee6ad87c33a050ee90a69119959f266d6` |

Integration is **`010b27e92136119a79223ffca3b29fbe6df8ceef`**; `main` stays `89ebdb0`.

**CI receipts at `010b27e`:**
- **Claude (author evidence): PASS, exit 0**, first run ([record](https://github.com/honghanh153-creator/la-lanh/issues/2#issuecomment-6445043714)).
  Web 537 / 82 files, API 2,588 / 57 / 1 (2,583 + #100's negative control + #102's four tests), e2e 8/8.
- **Codex r45, independent: PASS, exit 0** ([handoff](https://github.com/honghanh153-creator/la-lanh/issues/2#issuecomment-6445633904)),
  15:01–15:08 UTC, one continuous invocation in a fresh exact-head archive. Web 537 / 82 files, API 2,588 / 57 / 1
  (mypy 412 files), QA/native/web build and CLI smoke PASS, Playwright 8/8. Codex verified five consecutive
  first-parent merges from `95c058c`, each with two parents and the second equal to the approved head, and all 1,613
  tracked blobs unchanged after the run.
- Codex's first offline `pnpm install` in r45 failed before any CI or test step (a tarball missing from its package
  store); a frozen-lockfile install into a task-owned store then succeeded. It is kept as a setup failure, not a product
  failure. The full command was not retried.
- The PASS applies to `010b27e` only. It does not rewrite earlier red receipts (r36 and Claude run 1 at `9b945e6`, #92
  at `8329279`, the r39 environment failure, the r43/r44 control, setup and checker receipts), and one pass does not
  prove flakes impossible. A later merged head needs its own check.

**Codex r44 verdicts (unchanged by retargeting, re-confirmed in r45):**

| PR | Verdict | Notes |
|---|---|---|
| #105 P07 batch 2 | [APPROVE @ `17a65445f85ef54907105dea857d9516c94f10b7`](https://github.com/honghanh153-creator/la-lanh/pull/105#issuecomment-6445069855) | Base now `collab/integration`; not merged. |
| #106 PostgreSQL probe | [REQUEST_CHANGES @ `8201ff096540ad1943b2b1aee51406032f300b7d`](https://github.com/honghanh153-creator/la-lanh/pull/106#issuecomment-6445070952) | P1: query keys such as `?database=` or `?host=` override asyncpg's target past the guard (the fixture truncates). P2: the sibling invite seed broke `principals.source_guest_id` uniqueness. P2: the procedure's fresh cluster had no TLS, but every connection verifies the server. Fixed at `442ce989b601b3fd2221995cf4c7a86451702b31` with 13 new offline cases. [r46 (28/10): REQUEST_CHANGES @ `442ce98`](https://github.com/honghanh153-creator/la-lanh/pull/106#issuecomment-6446632256) (guard tests without a valid CA; `pg_hba` order), fixed at `c46a62840a530b82469618c378b164ba80fe8390`; **awaiting re-review, never executed**. |
| #107 registry revision 28 | [APPROVE @ `7382ee2d387f61e2a7953d4a03fc33e4eaadc7b7`](https://github.com/honghanh153-creator/la-lanh/pull/107#issuecomment-6445072132) | Base now `collab/integration`; not merged; this revision is stacked on it. |

**Correction, T02/T03/R03:** the current rows (T02, T03 and R03 above) said "owner approves copy". The owner delegated these copy decisions on
26/10; the decisions are recorded row by row in the workbooks (#85 T02/T03, #86 R03, merged 26/10 and part of
`89ebdb0` as documents). T02: 129 approved, 1 rewrite, 3 dropped; T03: 139 approved, 3 rewrites; R03: fourth voice
`deep_dive`, rewrites per voice. Codex's wording pass is already recorded in both workbooks (their "Codex wording pass
(26/10/2026)" sections) and asks Claude to review the authored edits. Next, per feature: Claude's review of those edits;
a separate wiring PR with versioning, frozen readings and the audit (T02/T03: #110, in review; R03: not started); then
the comprehension gates (T05 for Tarot, R03's own). Nothing is served. One careful reading is not a reader
comprehension test.

**CI PASS and merges are not release Go.** A release needs an explicit owner order and the runbook gates.

## Combined-branch checks (local, not pushed)

### Author's local merge-order check (revision 21)

One-off local merge on `b5e4427` in the order above, with #45 `e2e5b4c` and #73 `3760dcd`: all 12 merges clean (local
tree `59e0db8`, never pushed). `CI=1 pnpm check` exit 0: contracts, runtime/privacy/mobile guards, grammar and fallback approval, content/Tarot/Radar/rewrite audits, web lint/typecheck/511 tests, API lint/mypy and 2,559 passed / 57 skipped / 1 xfailed (R06 strict xfail), QA, web e2e 8/8. A first run with #45 at `56c0247` stopped at `fallback_approval --check`
(`question_frame#function_literals`), which `e2e5b4c` fixes. This is the author's run, not Codex or runtime proof.

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

## Not done (honest list, as of 27/10/2026; production is still `89ebdb0cf6b9`)

Released and live: everything merged into integration up to `7e6d69e`, including journal A (migration 0038), #61's
roster and #76's copy. Staging and production smokes are green, and the backup/check/journal timers run with
first-run receipts ([receipt](production-release-2026-10-26/receipt.md)).

Still open:
- **Content:** T02/T03/R03 copy is decided under the owner's 26/10 delegation and polished by Codex, but not served.
  T02/T03 wiring is in review (#110). R03 waits on Claude's review of the Codex edits and on its wiring. The
  comprehension gates (T05, R03) are open, as are R05, R07 and P12; the R06 strict xfail remains.
- **Pilots:** the Tarot pilot is not enabled; the Daily pilot continues to its 04/11 review.
- **Rights and devices:** the rights channel and native/device evidence are open.
- **P07:** the interleaved replay probe, failure-alert delivery, the Supabase backup/PITR record and the erasure
  kinds not yet journaled in production (#102 batch 1 in integration, #105 batch 2 approved and not merged); the
  disposable PostgreSQL probe (#106) is being fixed after r44 and r46 and has never run. **B holds.**
- **Operations:** a generation-off deploy (the worker-removal path) has not been exercised in a real deploy. The
  disclosure re-check for the release is open.
- **Rollback:** `c3fab33` is not a verified rollback anchor on schema 0038.
- **Integration after the release:** #83/#87/#88, #90/#91/#89, #98/#92/#94/#97 and #99/#103/#100/#101/#102 merged into
  integration (`010b27e`), not released. Independent check at `010b27e`: **PASS** (Codex r45; `95c058c` had r39); the
  red receipts at `9b945e6` and `8329279` stay. Release awaits an owner order. Details: "27/10: five merges" above.
- **Test follow-ups:** #97 operation-entry handshakes and #94 guard test (#100) and the focus assertion race (#101) are
  merged into integration; the PostgreSQL two-connection verification is not run (#106 prepares the journal part of
  it, not the send-first/delete-first fence).

As of 25/10 (before the release), the list also had: draft #75 No-Go; #76 pending the owner's wording; no fresh
backup, timers or restore probe; #61 merged but not deployed. All of those are closed by the release above.

This session's server and database access was operator work under the owner's release order of 26/10/2026.
There was no IAM/secret/budget change and no extra Luna/Google/paid API.
