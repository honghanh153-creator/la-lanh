# Relationship knowledge + chart engine plan

**Status:** approved for implementation  
**Scope:** backend facts, editorial knowledge and the privacy-minimized deterministic slate selector; no matching persistence/API/app UI rollout in this slice.

## Goal

Give Vòng Lá a defensible relationship foundation before product ranking is built: richer chart facts, a versioned 10-book concept registry, multidimensional evidence, and explicit safety/privacy gates. The engine must help people find useful conversation angles without diagnosing, predicting fate, or turning astrology into a compatibility verdict.

## Requirements mapped

- US-14: inferred relationship data remains purpose-bound and opt-in; no hidden psychographic profile.
- US-15 AC03/04: labels come from inspectable facts; never expose a compatibility percentage.
- US-16: no relationship reading affects request visibility, rejection disclosure, or safety filters.
- Astro engine spec §9: compatible chart configs, bidirectional house overlays, multidimensional output, no single truth score.
- Project gates: source traceability, no raw birth data in logs, no new persistence or public endpoint in this slice.

## Decisions

1. Keep astronomy facts separate from relationship-language knowledge.
2. Add strict/versioned synastry orbs rather than reusing natal orbs.
3. Emit dimensions (`communication`, `emotional`, `relating`, `drive`, `growth`, `friction`) and evidence, not a scalar match score.
4. Add A→B/B→A house overlays only when houses are actually available.
5. Enrich midpoint Composite with internal aspects; do not invent Composite houses.
6. Add an uncorrected Davison chart from exact midpoint time/place and label the method precisely; no claim of Astro.com corrected-method parity.
7. Add factual Jyotish D9/Navāṁśa points behind exact-time/tradition gates. Generated Jyotish interpretation remains ineligible pending expert review.
8. Keep Ashtakoota, corrected Davison, progressed synastry and relationship timing as declared gated capabilities, not pretend implementations.
9. The ten books contribute concepts and prompts only. No excerpts, diagnoses, attachment labels, or automatic behavioral inference.
10. Preserve the legacy compatibility API for callers, but mark it non-display/deprecated; new product work consumes multidimensional evidence.

## Implementation units

### 1. Chart contracts and calculations

- Extend astro models for relationship dimensions, contact strength/tone, house overlays, Composite aspects, Davison and D9.
- Add strict synastry aspect policy and deterministic house placement helper.
- Validate compatible traditions/config hashes before pair calculations.
- Add `calculate_relationship_bundle`, `calculate_davison_relationship`, and `calculate_navamsa`.
- Golden tests: orb rejection, bidirectional overlay, 0° midpoint, Davison midpoint, D9 boundaries, cross-config rejection, no scalar score in the new bundle.

### 2. Knowledge registry

- Add `domains/relationships` with a frozen source registry of ten books.
- Store bibliographic metadata, concept tags, allowed/prohibited uses and evidence class.
- Add safe editorial lenses/prompts that can explain evidence without diagnosing either person.
- Tests ensure ten unique sources, URLs, no excerpt payload, and mandatory prohibited-use rules.

### 3. Product, security and privacy contract

- Add a relationship-engine spec covering chart capability status, source methodology and matching constraints.
- Update the astro spec where runtime capability changed.
- Record data minimization: calculation is pure/in-memory in this slice; persistence, API exposure and consent enforcement remain later integration work.

### 4. Matching requirement cutover + selector

- Replace PRD/SRS top-five scalar ranking with five-energy slate diversity.
- Add optional expiring weekly intent, hard-filter-before-astrology contract and low-pool truthfulness.
- Implement a deterministic pure selector using only the six-dimension evidence projection, prior exposure count and stable weekly rotation.
- Exclude raw birth data, profile copy, mood, chat, popularity, Composite, Davison and D9 from the pre-mutual selector input.

## Verification

- Focused relationship/astro tests.
- Full API tests, Ruff and mypy.
- Review changed files against docs, security and privacy gates.

## Definition of done

- New relationship bundle returns inspectable multidimensional facts with method/version provenance.
- Synastry no longer silently uses natal orbs; overlays are withheld without houses.
- Composite and Davison limitations are explicit.
- D9 factual output is gated and cannot produce user copy.
- Ten-source knowledge registry is versioned, paraphrased and safety-bounded.
- Vòng Lá requirement docs and US-14–18 no longer depend on a scalar compatibility leaderboard.
- Pure slate selector yields unique candidates/energy slots, fails closed on safety eligibility and returns low-pool instead of inventing evidence.
- No new public endpoint, storage table, ranking score or UI claim is introduced.
