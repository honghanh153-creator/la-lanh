# System full-flow audit — 2026-10-10

## Disposition

**Later checkpoint:** this document records the initial audit, not the latest implementation status. The user subsequently authorized the overlapping repairs. Source identity, stale publication, coherent Daily assembly and obsolete rewrite-spending regressions have been repaired and are included in the green suites documented in [optional-account/IAM verification](2026-10-10-optional-account-iam-verification.md). Native, provider-delivery, production and remaining editorial gates must not be inferred from these local fixes.

**Not release-ready.** This is a local audit and one bounded content fix, not a production security clearance or a completed release. Four reproduced lifecycle defects remain. Do not deploy or enable paid generation until their regressions pass.

Request: review the whole journey using `ce-debug`, reconcile approved plans with implementation, and finish approved gaps. Current scope is guest-first onboarding, Astro/Natal/Daily, Tarot, private Radar, profile/privacy and sharing. Old Vòng Lá discovery/chat/social games are superseded or deferred; do not resurrect them from old unchecked plans. Intro option 1 is already selected. Direct voice is approved; the additional affectionate-sharp A/B/C voice is still unselected.

## Workspace and authority

- Repository: `/Users/phamhanh/Documents/New project/la-lanh`.
- Branch: `feat/luna-content-rewrite-runtime`.
- Pre-fix HEAD: `99a3079a383a4cb529c1331a596bc47f75b5f07f`.
- Pre-fix tree: extensive overlapping unstaged work. Preserve it; no stash/reset/stage/commit/push/deploy.
- New permission question asks whether to patch overlapping app/tests/docs while preserving old edits. **Awaiting response at this checkpoint.** Previous permission covered birth service/repository changes, not all remaining lifecycle files.
- This-turn implementation scope was clean beforehand: `readings/knowledge.py`, `readings/renderers.py`, `tests/readings/test_knowledge.py` only. New audit and screenshot artifacts are separate.
- No live database accessed, no keys printed, no provider invoked, no paid request made.

## Real browser journey completed

Dedicated QA: `http://localhost:5311`, API 8031, disposable database, synthetic input, generation/provider/worker disabled. Hostname differs from the user's `127.0.0.1:5310` review session to avoid cookie collisions. Existing user profile and browser tabs were not reset.

| Journey | Observed result | Limits / unfinished acceptance |
|---|---|---|
| Welcome → birth | Purpose, consent CTA, optional time/place, skip path, valid DOB accepted | No real human comprehension study |
| Date-only reveal → Home | Synthetic 15/03/1990 reveals Vibe · Mộng; Home displays a readable Note first | Not proof of the user's expected label |
| Note detail → save | Save succeeds; old saved revision remains frozen after precision upgrade | Saved historic content must not be mistaken for current active content |
| Add birth precision | Shared hour/minute selector accepts 08 and 15; catalog shows all 34 provinces; Hà Nội selection works; separate precision consent | Add/edit page still starts as a fresh unlock; unknown-time/place-only flow needs convergence |
| Supplement → Aura activation | Explicit activation changes Home from “Một tin nhắn chưa rõ làm bạn nghĩ mãi” to “Bạn muốn trả lời ngay một tin nhắn khó chịu” | Receipt/preview language is still technical; did not alter user data |
| Full chart → Natal | Overview and synthesis load with real chart data | Generic conflict headline fixed in source; this browser server was already running, so this audit does not claim it rendered the new version |
| Western → Jyotish | Separate sidereal results and nakshatra load; Moon changes from Scorpio to Libra in the synthetic chart | Browser confirms raw `drishti special`, “9 nhà” and “chưa được duyệt” wording; computation working does not mean readable synthesis is complete |
| Tarot question → fan → 3 cards | Synthetic work question submitted; selected positions 1, 8, 19; server result Page of Cups, Chariot, Tower; ceremony then summary-first report | Browser coverage this run is 3 cards, not fresh browser acceptance of all 1/3/5 spreads |
| Tarot reload → chapter | Same cards and summary restore; detailed chapter opens | Content remains imperfect: summary mixes communication and delegation framing |
| Radar intro → private input → result | Synthetic second person, unknown time, catalog place and permission accepted; real result has 57/68/40 independent indicators and four report chapters | Intro wording “Không phần trăm…” needs distinction between indicators and success probability; private result has no public-share control, intentionally privacy-limited |
| Profile → dark/light | Toggle changes appearance, not birth data; restore light succeeds | No physical iOS/Android acceptance |
| Saved → Home → share preview | Saved date-only label/content frozen; active Home and card use current Aura · Sâu and current note; preview omits birth fields/evidence | PNG download, anonymous safe-link open/revoke, invitation recipient and deletion UI not completed this run |

The synthetic date-only Mộng → full Aura Sâu transition is a calculation-mode change, not by itself evidence of another user's data. The separate lifecycle reproductions below demonstrate genuine stale-source defects. Do not conflate either case or hardcode a persona label.

Screenshot: `system-flow-2026-10-10/share-preview.jpg` (synthetic data only).

## Confirmed lifecycle defects — next patch sequence

All four were independently reproduced with synthetic local/TestClient checks, with no provider call. They are related to stale state within an owner; this alone does not establish cross-account data exposure on production.

1. **P2 — stale publication after date change.** A request begins with snapshot A. Date A→B clears projection pointers in `birth/postgres.py:94`. The paused A request reaches `readings/postgres.py:220`, which validates ownership/configuration but not current source; it reactivates A into the empty pointer. Current snapshot stays B while active reading is A. Routine refetch does not repair a different-plan source. Serialize source validation/publication with birth updates and reject stale source. Regression: pause before publication, switch date, resume; persisted and returned current content must never be A.
2. **P2 — same-sign dates collide.** The date-only factor at `readings/planner.py:200` uses sign/status. `canonical_reading_plan_key` at `readings/models.py:759` hashes factual content without source-specific persisted identity; immutable replay at `readings/postgres.py:1076` rejects a different snapshot. 15/03/1990→16/03/1990 triggers immutable conflict; Daily quietly falls back without a rich projection. Separate factual reuse from source-specific storage identity. Regression: two dates in the same sign on one day must each have a coherent current projection and immutable retained history.
3. **P2 — mixed metadata/prose response.** `api/v1/routes/daily_notes.py:280` loads the legacy note, then line 288 independently reads current snapshot. A→B between them yields A's persona metadata with B's projection. Bind or validate a common source/revision for the complete response; retry/reject a changed source, never return a mixed response. Regression: switch DOB between those calls and assert coherent identity in the response.
4. **P2 — obsolete rewrite can spend.** Date changes retain historic plans/jobs. `content_rewrite/postgres.py:115` checks plan existence but not current source; worker reserves budget before send. Synthetic enqueue A→switch B→lease A still permits execution. Fence current profile/snapshot before reservation and inside the send guard, using the same lock order as birth changes. Regression: stale queued A must never reserve/send after B becomes current; a budget reservation already consumed by a real send must not be falsely refunded.

Tests belong in existing birth/reading/rewrite integration and execution-fence homes. These files overlap existing changes, so the next implementation step requires the pending dirty-file confirmation. Do not replace concurrency proof with only mocks, delete historical plans, or suppress errors to manufacture green tests.

## Other approved gaps

| Gap | Required next work |
|---|---|
| Legacy erasure test setup | `tests/readings/test_api.py:124` still uses a DOB change to simulate a legacy date-only pointer with retained precision. The corrected date-change behavior removes precision, producing 409 before the intended erasure assertions. Build the legacy state explicitly inside the test; preserve deletion assertions. Strengthen sibling race tests to assert their hook actually ran. |
| Jyotish readability | Plain-language reviewed coverage for drishti/nakshatra; preserve structural-only fallback where genuine coverage is absent. Do not map Western meanings onto Jyotish just to remove warnings. |
| Natal labeling | Natal report currently says “Vì sao hôm nay?” even for static natal data. Use a purpose-aware evidence title. |
| Precision editing | Make add/edit state-aware using safe metadata; reset consent when inputs change. Do not leak raw encrypted time through prefill/local storage. |
| Content quality | Current offline gate has 18 medium findings. Complete semantic/clarity review, including Tarot intent and negation, not only wording rewrites. CMS remains optional. |
| Additional voice | Obtain A/B/C selection before final prompt/selector. Preserve Direct default and Direct fallback for vulnerable/sensitive topics. |
| Runtime and release | Latest patch needs isolated real PostgreSQL concurrency/TLS verification, scoped review and public-release acceptance. Prior 23-case PostgreSQL proof is historical, not a fresh run of this patch. |
| Deep scan | Prior external deep scan terminated on quota; do not describe it as a successful exhaustive clearance. |
| Native and readers | Native-device and real-reader tests remain unverified. Ten synthetic personas are not ten real users. |

## Debug Summary — bounded Natal fix

**Problem:** harmonious natal aspects receive a headline that frames both needs as a conflict.

**Root cause:** `full_frame` already builds aspect-aware explanatory text, but `_lens_copy` discarded the relationship type and always used “Điểm khó…” for the default lens; work manifestation also asserted a tug-of-war regardless of aspect.

**Recommended tests:** existing `tests/readings/test_knowledge.py` now covers trine/sextile supportive headlines without conflict markers, and square/opposition preserving tension without claiming easy support.

**Fix:** pass a supportive-aspect predicate from the same hero evidence into copy assembly, use an explicit supportive headline, make work manifestation neutral, bump renderer to `deterministic-vi-v11` so retained immutable revisions are not overwritten.

**Prevention:** test headline and explanation contract together, not only whether two aspect bodies differ. Six new cases: supportive/tense aspects, cross-lens context and sextile initiative. The supportive cases failed for the exact generic-headline defect; independent review then caught context loss and missing initiative, both reproduced red before refining the patch. All six pass afterwards.

**Confidence:** high for the bounded logic defect; not a claim that all Natal writing is editorially complete.

## Post-Fix Quality and verification

- Scope: three clean-before fix-owned files; unrelated branch work excluded.
- Simplification: three bounded read-only reuse/quality/efficiency reviews under `ce-simplify-code`, no scope widening or file-wide rewrite of dirty work. Reuse/efficiency: 0 applied; quality: 1 applied, consolidating identical supportive selection with explicit lens-specific prefixes. Version bump is mechanical.
- Content re-verification caught one newly overlong Natal sentence; split it into two readable sentences without changing the meaning. The final content gate again has no critical/high findings, with 18 existing Tarot medium follow-ups.
- Independent scoped review: initial lens-context finding accepted and fixed with regression tests; final review reports no actionable findings. Eight trine/sextile × lens projections passed candidate gates offline.
- Dedicated branch-wide review not used because unrelated work would enter its scope.
- Targeted knowledge/renderer/gates: **124 passed**.
- Web unit tests: **233 passed**, 51 files.
- Web TypeScript: passed.
- Ruff lint and format on the three fix-owned files: passed.
- Mypy on two implementation files: passed.
- Full API after final fix: **1,054 passed, 1 failed, 23 skipped**. Failure is the legacy setup above; skipped real PostgreSQL cases were not run this session. **Overall test gate remains red.**
- Content gate: **10 synthetic personas / 30 generated deterministic samples**, no critical/high rule findings, **18 medium follow-ups**. “Generated” here does not mean paid Luna.

Reference checks: [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [OWASP Web Cache Security](https://cheatsheetseries.owasp.org/cheatsheets/Web_Cache_Security_Cheat_Sheet.html), [PostgreSQL row locks](https://www.postgresql.org/docs/17/explicit-locking.html). These support current-state authorization, stale-cache exclusion and serialization; they do not certify this system's compliance.

## Resume checklist

- [ ] Receive pending confirmation to edit overlapping WIP without staging/committing/deploying.
- [ ] Patch source-specific identity with a failing same-sign-date test first.
- [ ] Patch serialized publication with a paused A→B request test first.
- [ ] Patch coherent Daily response with a between-read date-change test first.
- [ ] Patch stale rewrite eligibility before reservation/send; test no provider/no budget spend.
- [ ] Repair legacy-test setup without weakening erasure or race assertions.
- [ ] Run full API green and isolated PostgreSQL concurrency/TLS gates.
- [ ] Complete precision add/edit, purpose labels and reviewed Jyotish coverage.
- [ ] Close medium content findings and remaining share/invite/delete/1-and-5-card browser acceptance.
- [ ] Obtain optional second-voice choice; no premature paid generation.
- [ ] Release only after a cleanly isolated approved patch and explicit deployment authority; verify the public URL afterwards.
