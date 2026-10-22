# Audit v2 registry (22/10/2026)

Source: `la-lanh-audit-2026-10-22/claude-prompt-v2.md`, `privacy-content/review-v2.md`, `privacy-matrix.md`,
`content-ac-matrix.md`. Base for every PR: `collab/integration` = `c3fab3311d659c240da944a84fec305eca416cc6`.

Status values: `OPEN`, `FIXED_LOCAL` (code + red→green regression in an unmerged PR), `VERIFIED_RUNTIME` (seen working
on a real environment; **nothing in this session is**), `OWNER_DECISION`, `DEFERRED`. No PR is merged or deployed.

## A. Privacy and data lifecycle

| ID | Requirement | Status | PR / head / test | Owner | Evidence still missing |
|---|---|---|---|---|---|
| P01 | Raw Tarot question out of Web Storage | FIXED_LOCAL | #41 `1fb1c83` `TarotQuestionStorage.test.tsx` (4/6 red on base) | Codex review | runtime check on staging after merge |
| P02 | Deferred matching: no new collection | FIXED_LOCAL | #42 `0d49c62` `test_collection_gate.py` (410 default-off) | Codex | staging flag stays false |
| P03 | Triage of 75+11 retained findings | FIXED_LOCAL (triage) | #59 `a6e7e69`: 86→44 causes, 0 open P0/P1; low fixes #55 `07e29a3`, #56 `0f9ebfc`, #57 `e9ff2d6`, #58 `07ffd62` | Codex; operator for RC-23–27 | ephemeris dir listing/ownership in the deployed image; PostgreSQL race proof for #57; RC-05 before more rewrite surfaces |
| P04 | TTL for pending mood / saved retries | FIXED_LOCAL | #48 `efff6a2` `pendingMood.test.ts`, queue TTL tests | Codex; owner confirms 24 h / 30 d | device check |
| P05 | Physical TTL for revoked/expired share; experiment wording | FIXED_LOCAL | #49 `76d3460` `test_share_lifecycle.py` (cleanup case red on base) | Codex; counsel on "tối đa 30 ngày" copy | PostgreSQL run |
| P06 | Aggregate legacy-plaintext check + backfill/purge plan | FIXED_LOCAL (tooling) | #50 `109072d` `check_legacy_plaintext.py`, plan doc | operator runs; owner picks per-table option | real counts (staging, production) |
| P07 | Backup timer, alert, restore, deletion reconciliation | FIXED_LOCAL (artifacts) / OWNER_DECISION | #43 `3531bf0` units + `test_backup_timer.py`; reconciliation options A/B/C (recommend A) | operator installs; owner chooses A/B/C | install receipt, first backup, restore probe on a disposable copy |
| P08 | Log canaries; native device proof | FIXED_LOCAL (API/workers) / OPEN (native) | #51 `fd77a08` `test_log_redaction.py` | Codex; release task for native | ingress/Docker log runtime check; signed native build on device (MASVS) |
| P09 | B rights; receipt 7 d vs result 30 d | OWNER_DECISION | #52 `ab5e6a9` dossier D1–D4 | owner + counsel | decision, then process/code |
| P10 | Apple Tracking column; disclosures; counsel dossier | FIXED_LOCAL (column) / OWNER_DECISION | #52 `ab5e6a9` | counsel | legal answers; store forms at submission |
| P11 | Provider / pilot gates | OPEN / OWNER_DECISION | Luna Daily pilot on (≤20 opt-in, private budget); RC-05 limit bypass noted in #59 | owner (DPA), Claude (RC-05 fix before any new surface) | DPA acceptance by owner; RC-05 fix PR |
| P12 | Google / auth acceptance | OPEN | Google stays off | operator (secret rotation via protected channel), owner | acceptance run with a real test account on staging |

## B. Tarot

| ID | Requirement | Status | PR / head / test | Owner | Evidence still missing |
|---|---|---|---|---|---|
| T01 | One asked target for frame, stance, goal, step | FIXED_LOCAL (frame/stance/goal/step) | #45 `a1d1994` `test_target_clause.py` 129 cases (74 red on base); bank: 1 label changes | Codex; owner confirms rule-table approval | meaning/scene still card×topic → T02 |
| T02 | C4 scenes: observable situations, no hidden advice | OPEN | — | owner (workbook approval) | workbook of new scenes per card × topic (and per asked action) |
| T03 | C5 steps: concrete trigger, one small action | OPEN | — | owner | same workbook |
| T04 | Card names English + Vietnamese; update AC12 | OPEN (decided 19/10) | — | Claude next | implementation + AC12 edit + approval of label copy |
| T05 | Meaning/comprehension gate beyond form accuracy | OPEN | — | Claude + owner rubric | rubric and gate |
| T06 | C6 extra scenes; Tarot Luna gates | DEFERRED | — | owner (cost) | — |

## C. Hợp gu / Radar

| ID | Requirement | Status | PR / head / test | Owner | Evidence still missing |
|---|---|---|---|---|---|
| R01 | Context and voice change ≥50% of fit/friction | OPEN (gate red) | #47 `15ab8e8` gate: 0.0 / 0.0 | Claude (R03 content) + owner copy | content |
| R02 | Unknown-time contacts certain on the date domain | FIXED_LOCAL | #46 `780b0f7` engine + Radar tests (16 red on base); 30/492 noon contacts dropped | Codex; confirm ±14 h reading of spec §1 | — |
| R03 | Contact-specific sentences, context scenes, full-sentence voice | OPEN | gate AC01 528/800 below 2 | owner Excel | frames by directed pair/aspect/context/voice |
| R04 | Range/calibration spec | OWNER_DECISION | — | owner | spec to write and approve before API/UI |
| R05 | Variants frozen at creation, grammar manifest on real output | OPEN | — | Claude | after R03 frames exist |
| R06 | Release audit measures US-22 AC01–AC03 | FIXED_LOCAL (measurement) | #47 strict xfail, `pnpm radar:us22` | Codex | joins `pnpm check` when R03 passes |
| R07 | Manual-entry consent / Roast copy | OPEN | attestation kept; depends on P09 D3 | owner + counsel | decision, copy approval |

## D. Operations and quality

| ID | Requirement | Status | PR / head / test | Owner | Evidence still missing |
|---|---|---|---|---|---|
| O01 | #40 kill switch, real Compose proof | FIXED_LOCAL | #40 `0444793` (11 fake-docker tests + proof script); manual stop documented | Codex (matching-head verdict), operator | real Compose proof on a disposable host; deploy |
| O02 | Daily backup | FIXED_LOCAL (artifacts) | #43 `3531bf0` | operator | install + first run receipt |
| O03 | 8 failing E2E → mandatory gate | FIXED_LOCAL | #53 `4e52dd7`: 8/8 pass; `pnpm check` ends with `web:e2e` | Codex | — |
| O04 | Pin in-function copy | FIXED_LOCAL | #54 `a069306` mutation tests; additive approval pin | Codex | — |
| O05 | Docs/Issues sync; #17; #9 | OPEN (this PR + comments) | #17 delta = hotfix receipt `836222282dfc` + Caddy restart note, merges cleanly → **re-review @ `c08262e`, not supersede**; #9 stays deferred | Codex, owner | verdict on #17 |
| O06 | G1 / 90-day diversity / date-only pool | DEFERRED | after the fixes above | owner roadmap | — |

## Pilot M1 (unchanged decisions)

Daily Luna pilot review on **04/11/2026**; at most 20 opted-in sessions; the full 670-case gate is **not met** and runs
under the owner's exception; no EvaluationRecord exists or was fabricated; budget figures stay server-side.

## Not done in this session (honest list)

T02–T05, R03–R05, R07, P11/P12 actions, O06; all runtime verification; real Compose, backup, PostgreSQL and device
evidence; no merge, deploy, server or database access, IAM/secret/budget change, or extra Luna/Google/paid API.
