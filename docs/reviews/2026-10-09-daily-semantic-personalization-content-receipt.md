# Daily semantic personalization content receipt

Date: 2026-10-09. Revised daily v6 implementation; not a release approval.

## Scope and sources checked

Only these files were changed for this task:

- `apps/api/app/domains/readings/daily_psychology.py`
- `apps/api/app/domains/readings/daily_personalization.py` (new)
- `apps/api/app/domains/readings/rewrite.py`
- `apps/api/tests/readings/test_daily_psychology.py`
- `apps/api/tests/content_rewrite/test_daily_rewrite.py`
- This receipt.

Sources read: `AGENTS.md`, the daily personalization collision investigation,
`docs/foundation/daily-psychology-scene-advice-engine.md`, the direct daily meaning brief
plan, existing factor/planner/frame/renderer contracts, publication gates, rewrite compiler,
privacy allowlist and related tests. No new external research or user information was used.

Pre-existing dirty work was preserved. Frontend, reading models/application, privacy,
generation schemas, security, contracts and migrations were not edited. No commit, deployment,
provider request, billing change, database write or production inspection occurred.

## Fixed behavior and requirement mapping

The retired selector used a whole-chart ID hash to choose an issue. The new selector first
enumerates supported interpretations and ranks their eligibility. The local day only selects
among equal-ranked candidates and wording slots within their chosen issue. Orb formatting,
config/plan hashes, unrelated evidence IDs and factor ordering do not select a personality.

`daily-semantic-eligibility-v3` uses:

- Known body and domain together, sign element and twelve authored Sun-sign angles based
  on the existing sign catalog. These are general editorial angles, not private life facts.
- Selected hero and primary roles, with supported natal interactions ahead of placements.
- Seven authored body-pair rules with separate tense and cooperative readings. Unsupported
  combinations do not acquire invented pair interpretations.
- Square/opposition versus trine/sextile, compatible roles, confidence, a minimum interaction
  strength and coarse strength ranking. Strength ranks editorial relevance, not certainty
  about someone's behavior.
- Relevant natal aspect phase refs and supplied transit phase. Moon/Mars separating context
  permits a hypothetical already-sent-reply scene; applying/approaching permits an unsent
  reply scene. This is an editorial analogy, not a forecast of a message or argument.
- Known houses linked to the same actor, only with exact precision and high confidence.
  House 6/10 caretaking is specifically about time to accept work, rather than general helping.
  House context can refine an illustration; the explicit topic remains authoritative.
- A planner-selected moderate Mercury/Venus conjunction can combine wanting to understand
  with wanting to be understood, rather than falling back to two unrelated placements.
  Its known linked house context reaches the visible illustration. Selected interactions
  require strength at least 0.25; unselected interactions require at least 0.35. Weak contacts
  remain excluded. These thresholds govern editorial eligibility, not psychological certainty.

The catalog has fifteen observable situations. Five additions distinguish capacity before
agreement, a fast unsent reply, repairing a sent reply, asking for specific feedback and naming
a concrete need. Each has a matching modest action and observation question.

Each meaning now has six distinct headlines, eight authored hypothetical illustrations and
eight compatible actions: 384 combinations within that meaning. Illustrations vary the
observable task, message or decision setting without changing the interpreted response.
Actions vary bounded methods of responding to that same problem. Date-only, ambiguous and
full-chart fallback fixtures each regain 365 distinct day cards without selecting unrelated
issues. The neutral example also has the complete variant set; unknown facts are not needed
for daily novelty. This is 365 different cards, not 365 new personality claims.

Eligible relationship families additionally have eight matched actions that ask about the
other person's need, timing or understanding. Auto may check one's own capacity; explicit
relationships instead clarifies the shared need and agreed limit. Topic differences are
visible in advice, not only an introductory phrase. Every topic for the Cancer date-only
fixture has 365 distinct accepted cards in the added regression.

The brief now combines the selected interpretive tendency/competing need with the observable
behavior and action's takeaway. Limits remain in `reader_takeaway`; scenes remain
`scene_status=illustrative`. Unsupported/ambiguous inputs receive an explicitly unpersonalized
capacity-check example, not a guessed sign or private life story. Date-only users receive an
explicit general-reading limitation. Identical known Sun facts can legitimately replay the
same card.

Existing frame knowledge refs and hero evidence are retained; supporting refs for the selected
meaning are added, bounded by the existing twelve-ref limit. Unknown precision excludes house
and angle refs. Evidence order is canonical: heroes first, then remaining supporting refs
sorted. The two previous renderer equality failures had identical factor sets and only
editorial ordering differences; neither external assertion needed modification.
Daily v6 and its content fingerprint invalidate deterministic rendering cache
keys through the existing renderer path. Historical frozen revisions/shares are not rewritten.

The daily rewrite compiler carries the same selected meaning through existing fields. It now
requires a baseline accepted by the existing gates and rejects imprecise house/angle evidence.
No gate was disabled or relaxed. No new schema/API fields are required; `models.py`, `privacy.py`
and `schemas.py` are unchanged by this task. Luna still rewrites the selected meaning, rather
than deciding a new issue. No Luna output was generated or evaluated here.

## Verification

All commands used bundled Node on `PATH`, `UV_CACHE_DIR=/tmp/la-lanh-uv-cache` and
`UV_OFFLINE=true`.

Targeted suite:

```sh
PATH=/Users/phamhanh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH \
UV_CACHE_DIR=/tmp/la-lanh-uv-cache UV_OFFLINE=true \
uv run --directory apps/api pytest \
  tests/readings/test_daily_psychology.py \
  tests/content_rewrite/test_daily_rewrite.py \
  tests/infrastructure/generation/test_privacy.py
```

Result: **47 passed**. The two edited test files alone: **34 passed**.
Scoped Ruff check/format check and scoped mypy pass for all five Python files.
`git diff --check` passes.

Tests cover actual behavior/action differences, not just different copy:

- Same Sun, primary Mercury Virgo versus Gemini: sending a delayed draft versus completing
  one of several unfinished tasks.
- Mercury/Saturn square versus trine: delaying because of judgment versus a specific feedback
  request using an existing draft.
- Weak versus strong Sun/Saturn interaction, and incompatible role: removing the unsupported
  comparison interpretation changes the scene/action.
- Moon/Mars applying versus separating and transit approaching versus separating: read the
  whole message before answering versus clarify the reply already sent.
- Known house 6 versus 7: checking work capacity versus helping within one's limits.
- Unknown precision with an injected house: same meaning/copy as without that house, no house
  claim or supporting ref.
- Unrelated IDs, unrelated phase refs, config/plan identifiers, small orb formatting changes,
  factor ordering and an extra unrelated supporting body: unchanged selected meaning/copy.
- Ambiguous Sun: no candidate is promoted to fact; limitation is explicit.
- Stable replay, every authored combination, all topic lenses across a year, publication
  gates, safe compiler payload, privacy minimization and meaning-sensitive blueprint hash.
- 23,808 authored combinations across supported arena prefixes and matched relationship
  actions pass the unchanged direct Home gates. Each family's base catalog contains exactly
  384 distinct headline/scene/action triples. No date numbering or irrelevant ID salt is added.
- Synthetic browser A/B regression: the full selected pair plus known house has a visibly
  different scene and action from the date-only Sun input; unknown precision removes the
  house-specific illustration and reference.
- Two equally eligible factors supporting the same meaning still give 365 distinct cards
  within one core meaning. Eligibility selection and day-variation counters are independent,
  so alternating supporting factors does not repeat a card on consecutive days.

### Synthetic cohort20

Twenty actual Swiss Ephemeris full charts, all in the same March Sun season. Inputs are
synthetic: years 1980 through 1999, March days 10 through 14, varied hours, fixed test
coordinates. Day is 2026-10-09. No private profiles, cookies or production data were used.

- 20/20 pass the existing candidate gates and stable replay.
- 14 distinct full cards; three exact duplicate groups of size three.
- 12 distinct core meanings; duplicate meaning groups of sizes eight and two.
- 9 behavior families. Missing context occurs eight times; specific feedback three times;
  avoiding a small conflict three times; six other families once each.
- Each selected family has an eligible rule whose supporting refs appear in its blueprint.

These counts separate text duplicates from semantic duplicates. Grouping by behavior family
also detects similar responses even when their interpretive explanations differ. Duplicates
are documented for editorial review, not resolved by paid retries, runtime user-prose scans or
unsupported facts. This is a small same-season regression cohort, not a population collision
rate, an ownership test or scientific personality validation.

### Revised broader regression result

Command: `pytest tests/readings tests/daily tests/content_rewrite/test_daily_rewrite.py
tests/content_rewrite/test_reading_rewrite.py tests/infrastructure/generation/test_privacy.py
--tb=short` with the same environment.

Result: **293 passed, zero failures**. The initial v5 attempt regressed daily novelty and was
not sufficient. All eight previously reported failures are now resolved through implementation,
without editing external tests, dropping test cases or weakening their assertions:

- The three existing 365-day date-only/ambiguous/full tests pass with their original quotas.
- The existing twelve-sign specificity test passes through sign-supported meanings.
- Auto-versus-relationships advice tests pass through shared-need actions.
- Both renderer evidence-equality cases pass through canonical ordering of the same facts.

No parent evidence assertion adjustment is needed for these fixtures. A future test involving
genuinely different supporting factor sets would need its own evidence-backed contract review.
Parent will run the full backend suite after coordination; this receipt records the scoped
broader suite, not an unperformed full-backend result.

## Direct samples

Actual synthetic cohort card, index 2:

> Câu hỏi về bản nháp chưa đủ cụ thể.
>
> Khi gửi bản nháp lần đầu, bạn có thể quên ghi câu hỏi về phần còn chưa rõ.
>
> Hỏi người đọc góp ý một phần trước, chưa yêu cầu xem hết bản nháp.

Synthetic browser pair on 2026-10-09:

- A, 1998-03-15 date-only, stays an unclear-message reading with an explicit Sun-only limit.
- B, 2000-10-06 14:30 Hanoi, has a selected Mercury/Venus conjunction of strength about 0.31
  and a known linked Venus house 9. The visible scene starts "Ví dụ trong công việc hoặc
  chuyện học" and illustrates a draft whose feedback question is unclear. Its action asks
  for feedback on one part, not the intent of a short message.

The previous B implementation omitted that moderate selected conjunction, then rotated
between two missing-context placement interpretations, sometimes losing the known house
context from Home. This was a genuine semantic coverage gap, now covered by a regression.
Other full charts can still legitimately share A's missing-context meaning. This example
does not establish global uniqueness or resolve all coverage gaps.

Counterfactual phase examples from the authored catalog, both gate-tested:

> Bạn định trả lời khi chưa đọc hết.
>
> Khi một tin nhắn làm bạn khó chịu, bạn có thể gõ câu trả lời ngay dù chưa đọc hết.
>
> Đọc hết tin nhắn rồi viết câu trả lời về đúng điều người kia hỏi.

> Bạn gửi rồi mới thấy câu mình hơi gắt.
>
> Khi đọc lại tin nhắn vừa gửi, bạn có thể thấy cách mình trả lời gắt hơn điều muốn nói.
>
> Nhắn lại ý bạn muốn nói bằng một câu rõ, không trách người kia.

These are offline fallback examples, not reports of actual events or Luna output.

## Security, privacy and remaining DoD

No new collection, free-text input, mood, raw birth details, coordinates, ownership keys or
provider-visible factor IDs were added. The compiler privacy regression confirms existing
anonymous labels and brief survive minimization, without birth input or owner identifiers.
Owner scope, consent, budgets, share authorization and deletion paths were not changed.

Remaining work belongs to the parent/release workflow: run the full backend suite,
reconcile foundation version/selection documentation, review repeated cohort meanings and rule coverage,
conduct human Vietnamese readability review and verify actual same-origin ownership/late
response/session flows. Automated wording gates do not establish comprehension. This content
fix does not diagnose or certify session isolation, and is not a deploy/paid-evaluation approval.
