# Content matrix release gate

This gate applies to every Lá Lành deployment. Its purpose is to make the product more specific and
useful over time without rewarding filler, unsafe certainty, or untraceable astrology copy.

Daily Note additionally uses `daily-psychology-scene-advice-v1`. Every release must prove that its
scene is descriptive rather than advisory, its advice is bounded and compatible with the scene, all
psychology source IDs are registered, and the 365-day deterministic suite remains collision-free.

## Current baseline

Local candidate, 2026-10-10: deterministic reading renderer v12; Tarot renderer v6, deterministic gate v4 and Luna rewrite gate v4. Tarot now preserves each card's authored meaning before applying the question's recognised goal. Reflection/action/summary are reviewed together; an imperative vocabulary must admit valid concrete actions without weakening unsafe-inference rules. Rewrite synthesis must retain meaning terms from every selected card; unsupported mind-reading/manipulation fails closed to local content. Word overlap and regex are heuristic checks, **not semantic certification**. Jyotish uses calculated positions and reviewed structural copy, not borrowed Western claims. Deep Vedic interpretations remain unavailable rather than fabricated. Five-card summaries budget optional context after all five meanings, so a multi-goal question cannot overflow the gate and leave an otherwise complete draw unreadable.

This candidate adds work-specific Moon/Venus interpretation, eight goal/action contexts and positive/negative rewrite fixtures. Existing 78-card/context banks remain; no claim that new full books were ingested. Local breadth audit: 8,424 contextual + 11,232 recognised-goal spreads. Ten synthetic personas/30 readings have no critical/high/medium findings in this sample; these are generated fixtures, **not ten human testers**. Paid Luna output and human comprehension remain independent release gates. Historical saved/shared content stays frozen.

The machine-readable floor is `docs/operations/content-matrix-baseline.json`. Run:

```sh
pnpm content:audit
```

The command fails when a launch body, aspect, theme, context, source, concept, or relationship
dimension loses coverage; when IDs drift; when a measured catalog shrinks below the accepted
baseline; or when Daily Note reintroduces a retired generic fragment, duplicate sign atom, or an
incomplete context-to-scene/action mapping. It is also part of `pnpm check`.

Current measured coverage on 2026-09-27:

- Daily Note: 14 bodies, 12 signs, 12 houses, 6 aspects, 6 interpretive lenses, 5 editorial modes,
  and a 630-day semantic editorial cycle.
- Relationship knowledge: 10 traceable sources, 23 executable concepts, 6 dimensions, and 4 explicit
  voice profiles.
- Radar: 8 interaction themes and 4 user contexts.

Counts are a regression floor, not a quality score. Adding synonyms or generic sentences does not
qualify as enrichment.

## Semantic personalization regression — 2026-10-09

Local Daily `daily-direct-meaning-v6` selects evidence-eligible meanings before rotating wording.
This update is not a deployment receipt. Each next release must check:

- [ ] Same-Sun/full-chart near neighbors: alter a relevant planet/sign, pair/aspect, phase or
      known linked house and verify the intended observable behavior/action changes, not only
      the headline. Preserve evidence refs and unknown-time exclusions.
- [ ] Negative controls: changing owner IDs, unrelated factor order/IDs, hashes or orb formatting
      must not invent a personality distinction. No identifier-based uniqueness lottery.
- [ ] Keep the 365-day stability/novelty tests and lens-specific action tests. Variants within an
      eligible meaning are finite; do not report them as independent insights.
- [ ] Review at least 20 synthetic profiles and record exact-card, core-meaning and behavior-family
      collisions separately. The local same-season baseline is 14 cards / 12 meanings / 9 behavior
      families across 20 profiles. These counts are diagnostic, not a population target or a reason
      to force unsupported alternatives. Name repeated meanings and the next justified rule gap.
- [ ] Confirm both deterministic fallback and minimized rewrite brief express the same meaning.
      Label model tests as mock/offline unless a real paid evaluation was authorized and executed.
- [ ] Read samples as an end user: what happened in the illustrative scene, what distinction is
      being explained, and what the small action actually does. Automated gates do not prove that
      Vietnamese readers understood the output.
- [ ] Historical saved/shared revisions stay frozen. Never scan other users' private prose or use
      paid regeneration loops to make someone's card look unique.

See `docs/foundation/daily-psychology-scene-advice-engine.md` and
`docs/reviews/2026-10-09-daily-semantic-personalization-content-receipt.md` for rules and samples.

## Mandatory checklist for every normal deployment

- [ ] Run `pnpm content:audit` and attach the output to release evidence.
- [ ] Run `pnpm content:review`. The core reviewer must pass without Content Studio or production
      user data; it reviews Daily and Tarot output for 10 synthetic personas.
- [ ] Run `pnpm experience:audit`, then complete the human mobile review in
      `docs/operations/user-experience-release-gate.md`.
- [ ] Run the complete reading, relationship, and Radar test suites.
- [ ] Compare representative Daily Note and Radar outputs with the currently deployed release.
- [ ] Add at least one reviewed, evidence-bound content improvement: a new useful atom, a missing
      interaction case, a new tested dimension, or a clearer real-life manifestation.
- [ ] Add or update a regression/golden fixture proving the new content is chart-specific and does not
      merely change wording.
- [ ] Bump the affected knowledge/content/renderer version when visible output or selection logic
      changes.
- [ ] Update `content-matrix-baseline.json` only after tests and human review pass; never lower a metric
      to make CI green.
- [ ] Confirm evidence, anti-influence, editorial, meaning, and privacy gates still pass. Meaning
      Gate must reject prose that no longer matches its semantic blueprint, chosen context, evidence
      refs, observable scene, or action contract.
- [ ] Record what became more specific, which user scenario benefits, and which dimension remains
      missing.

An emergency security or availability hotfix may ship without content expansion. The release record
must name the waiver and the next planned release must include the deferred content improvement. Do
not add low-quality prose merely to satisfy a deployment counter.

## Review findings on 2026-09-27

### Fixed now

- Radar mixed Vietnamese copy with English planet names in evidence. All launch body labels are now
  consistently Vietnamese and protected by an automated regression test.
- There was no single deploy-time command that checked content coverage. `pnpm content:audit` now
  provides that gate and is included in the full project check.
- Daily Note no longer chooses a generic hook, scene and action independently. Every newly rendered
  note carries one server-side semantic blueprint and must pass Meaning Gate before publication.
- The reported Pisces fragments and the internal “chưa có thử nghiệm hành vi” message are retired
  and protected by content and component tests.

### Remaining product gap

The 23-concept relationship corpus and four voice profiles are valid and tested, but Radar's current
public dossier is still rendered mainly from its own hard-coded theme/scene catalog. The editorial
plan is not yet connected to visible Radar chapters, and the user cannot yet select a voice profile.
Metadata must not imply that an unused voice or concept changed the output.

This is the highest-value next content task: connect `RelationshipEditorialPlan` to one evidence-bound
chapter or observation at a time, keep its evidence IDs aligned with Radar receipts, expose only an
explicit voice choice, and add golden tests before enabling it publicly.

## Dimension expansion roadmap

Prioritize dimensions that change what the user can understand, not how many paragraphs appear:

1. **Interaction direction:** distinguish what A activates in B from what B activates in A.
2. **Life scene:** messaging, first meetings, conflict, planning, affection, boundaries, and repair.
3. **Time and development:** current transit phase and repeated pattern, without event prediction.
4. **Relationship context:** crush, friend, partner, or someone—context changes examples, never facts.
5. **Data confidence:** exact time for both, one exact chart, date-only, and low-signal degradation.
6. **Technique:** natal, synastry, two-way house overlays, Composite, then consented timing layers.
7. **User-selected voice:** straight/warm, gentle/specific, playful/grounded, or deep dive.
8. **Observed feedback:** “trúng/chưa trúng” may rerank approved atoms only after explicit consent;
   it must not create hidden personality labels or train on private free text.

Each new dimension needs a versioned method, input eligibility rule, evidence mapping, privacy review,
failure/degradation behavior, and near-neighbor benchmark. Jyotish interpretation, diagnostic labels,
compatibility verdicts, and inferred consent remain disabled until their separate expert and safety
gates are met.

Psychology dimensions are editorial lenses only. They cannot introduce diagnoses, therapy claims,
sensitive-trait inference, certain predictions, or new personal-data collection. Copyrighted source
text is never stored in the matrix; all user-facing Vietnamese copy must be original.

## Verification basis

- Astrodienst's official introduction treats planets, signs, houses, and aspects as distinct inputs
  that must be synthesized; adding more isolated labels is therefore not accepted as deeper content:
  https://www.astro.com/astrology/in_intro_e.htm
- OWASP MASVS-PRIVACY-1 requires data minimization and informed consent. New content dimensions must
  reuse the minimum chart projection needed and must not silently expand personal-data collection:
  https://mas.owasp.org/MASVS/controls/MASVS-PRIVACY-1/
- Vietnam's Personal Data Protection Law 91/2025/QH15 remains the current statutory baseline,
  effective 2026-01-01:
  https://vanban.chinhphu.vn/?docid=214590&pageid=27160
