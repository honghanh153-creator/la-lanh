# Daily personalization: repeated meaning is not proof of shared ownership

Date: 2026-10-09. Initial investigation retained below; local implementation and testing completed subsequently. No beta deployment or paid provider call.

## Implementation addendum

The owner authorized fixing and testing. Runtime `daily-direct-meaning-v6` now selects supported
meanings before wording, through `daily-semantic-eligibility-v3`. Selected pair/aspect/phase,
actor-linked eligible house context and explicit topic reach the semantic brief and direct
fallback; opaque IDs no longer rotate arbitrary problems. The same brief reaches Luna's existing
privacy-minimized rewrite payload. Unsupported details and imprecise houses are excluded.

Fifteen authored behavior families and bounded variants preserve the existing daily novelty gates
without inventing 365 new personality claims. Counterfactual tests distinguish delayed drafts
from unfinished tasks, asking for feedback from self-judgment, an unsent reply from a reply to repair,
and work capacity from a relationship request. Unrelated IDs/ordering/format changes do not change
the meaning. Known low-data inputs can still legitimately share a reading.

Cohort20 has 14 cards, 12 meanings and 9 behavior families; duplicates are recorded rather than
hidden with synonyms or paid retries. See `2026-10-09-daily-semantic-personalization-content-receipt.md`
for detailed evidence and `2026-10-09-session-personalization-fix-receipt.md` for integrated QA.

## Owner's report

The owner saw a friend's beta note, then apparently the same note on local staging after
entering their own details. They want materially more personal content while retaining direct
Vietnamese. No friend's profile/content was retrieved to investigate this report.

Two hypotheses remain separate:

1. Incorrect owner/session state. See `2026-10-09-beta-session-isolation-debug.md`.
2. Correctly isolated owners receive identical or semantically shallow authored content.

The second is now reproducible without sharing cookies, network responses, or a database.
Reusing the same text is not sufficient evidence of a privacy breach. Conversely, rewriting
that text must never be used to conceal an ownership bug.

## Confirmed content behavior

Synthetic date-only charts for 1998-03-15 and 2000-03-10, rendered on 2026-10-09:

- Same Sun sign; identical ReadingPlan hash.
- Identical hook, scene, and action:
  - “Càng xem nhiều lựa chọn, bạn càng khó chọn.”
  - “Khi đã mệt mà vẫn phải chọn giữa nhiều phương án, bạn có thể xem đi xem lại nhưng chưa chốt được.”
  - “Giảm còn hai lựa chọn phù hợp nhất rồi so một điểm quan trọng.”
- No user content or provider API involved; pure chart engine → planner → renderer.

Ten synthetic full charts at the same date:

- 10 distinct plan hashes;
- 10 distinct text triples;
- only 7 distinct issue keys; three profiles share `avoid-small-conflict`, two share
  `automatic-caretaking`.

This small fixture is a diagnostic sample, not a measured collision rate for all users or
proof of comprehensibility. The script used real Swiss Ephemeris calculations, no model calls.

## Causal chain and test gap

- `ReadingApplicationService.projection` supplies the same local-day editorial seed to all
  profiles (`domains/readings/application.py:129`).
- Date-only plan factors identify Sun sign/status, not distinct individuals. Different birth
  dates in the same sign can legitimately contain the same available astrology facts.
- `apply_daily_psychology` selects from **10 authored issues** and rotates variant slots by
  Sun sign or a hash of factor IDs (`daily_psychology.py:503–533`). A hash shifts copy selection;
  it does not explain why a situation is relevant to that chart.
- The function overwrites the richer source frame's hook, thesis, scene and action with that
  issue's copy (`daily_psychology.py:537–556`). Detailed chart evidence can remain present while
  the daily prose becomes a generic psychology situation.
- `compile_daily_rewrite_request` passes the already-selected title/scene/action and meaning
  brief (`rewrite.py:198–209`). The model's contract is to preserve these meanings, not to
  invent a new personal interpretation.
- Therefore adding synonyms or asking Luna to “make it unique” does not repair the source
  semantics. A single limited input cannot justify person-specific life facts.
- Existing tests prove stable replay, 365 different text triples for one chart and publication
  gates. They do not prove that chart differences cause meaningful reading differences.

Read-only beta deployment observation: release `a7fadf7e4511`;
`LA_LANH_GENERATION_ENABLED=false`, `LA_LANH_GENERATION_WORKER_ENABLED=false` in the running
application container. These observations do not enable generation or identify the origin
of every historic revision. Local QA also intentionally disables generation.

## Proposed implementation contract

### Priority 1 — correct owner before better prose

Verify the active guest/profile before rendering. Bind caches and delayed responses to their
owner/session generation. Local QA must use a disposable database and synthetic personas, not
the production database or borrowed production cookies. Compare profile, snapshot, revision
and session identities locally; never print credentials or another user's personal content.

### Priority 2 — meaning-aware selector, not hashed arbitrary situations

Use selected natal/transit factors, eligible house context, aspect type/strength/phase and the
user-selected topic to build a bounded personalization brief. The knowledge rules must name:

- what tendency is being interpreted;
- what competing tendency changes it;
- what context makes it visible;
- what observable response distinguishes it from a nearby case;
- what modest action addresses that specific interpretation;
- which supplied evidence supports each interpretation and what remains unknown.

Rank eligible situations by these meanings first. Use deterministic variation only among
equally eligible situations, not as a substitute for relevance. Same chart/topic/day remains
stable on refresh. Preserve the existing no-forecast, unknown-time and precision constraints.
Unsupported houses/angles/transits must not be fabricated for date-only users.

### Priority 3 — direct rewrite from that brief

Luna may change phrasing and select an allowed illustration from the semantic brief. It may not
change the selected meaning, manufacture private background, infer someone's motives, or promise
events. Keep short everyday subject–verb sentences. No astrology jargon in the Home card.

Both the deterministic fallback and generated version must express the same distinction. Paid
rewrite remains separately controlled by consent, caps and deployment approval. A low monthly
budget makes fallback quality essential; do not run extra paid regenerations merely to obtain
unique wording.

### Priority 4 — personalization gate and truthful sharing

Test with at least 20 synthetic profiles, including pairs with the same Sun but different full
charts. Keep four separate scores: ownership correctness, factual support, semantic difference,
and readability. Use counterfactual tests: changing a relevant factor should change the affected
meaning; changing an unrelated identifier should not invent a different personality.

Detect duplicated full cards and near-identical meaning within the offline evaluation corpus.
Do not scan other users' private prose at runtime to make a card unique. A detected duplicate
must result in review or an eligible alternative, not random rewriting, new private facts, or
automatic paid retries.

When only Sun/date is known, be honest about the limited reading. Two similar inputs can
legitimately produce related interpretations. Distinct prose for every person worldwide is
neither a useful nor supportable guarantee. An optional topic choice can improve relevance
without pretending the app knows the user's day. Do not add collection of life history without
separate product/privacy review.

Share the exact owner-authorized displayed revision. Do not add birth details, private context,
or another user's content to a share image to make it seem more personal. Existing frozen
shares must remain unchanged when matrix/prompt versions update.

## Direct samples for editorial review

These are illustrative tone/meaning examples, not readings of the owner or their friend.

### A — agreeing before asking the group

**Bạn gật đầu theo nhóm, dù vẫn chưa hiểu.**

Cả nhóm chốt rất nhanh. Có thể bạn cũng nói “ok”, nhưng vẫn còn một chỗ muốn hỏi.

**Thử:** Hỏi đúng chỗ đó: “Phần này mình chưa hiểu, giải thích thêm nhé?”

### B — agreeing despite limited time

**Bạn nói “được”, nhưng lịch đã kín.**

Một người nhờ thêm việc. Có thể bạn nhận lời cho khỏi ngại, rồi mới nghĩ không biết làm lúc nào.

**Thử:** Nói lại phần bạn làm được và thời gian bạn cần.

### C — delaying because of anticipated judgment

**Bản nháp đủ ý. Bạn vẫn ngại gửi.**

Có thể bạn sửa thêm vài chữ vì sợ người nhận chê, chứ không phải vì bài còn thiếu.

**Thử:** Gửi bản nháp và ghi rõ phần nào bạn muốn được góp ý.

Difference must be A's unanswered question vs B's lack of capacity vs C's anticipation of
judgment—not simply three ways of saying “slow down”. The rule must only select a distinction
that its source brief supports. It must not claim these events actually happened.

## Verification and delivery boundaries

Before implementation: authorize editing overlapping dirty files (API client, privacy/schema,
reading models/application if needed). Preserve pre-existing work. No blanket staging/commit.

Before beta: session-isolation regressions pass; semantic/counterfactual fixtures pass; fallback
sample review; actual same-origin flow checks; migration/version compatibility where relevant;
separately authorized paid evaluation if needed. Do not label offline copy as Luna output.

Sources checked:

- Existing daily psychology foundation, direct meaning brief plan and rewrite architecture.
- [OpenAI prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering):
  relevant context and explicit examples, not uniqueness through wording alone.
- [OpenAI model optimization](https://developers.openai.com/api/docs/guides/model-optimization):
  task-specific evaluation before model/prompt changes are called successful.
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html):
  cached private state can outlive its session; this is distinct from generic shared copy.

No product implementation, beta deployment, credential handling, new personal-data collection,
or paid provider call occurred during this investigation.
