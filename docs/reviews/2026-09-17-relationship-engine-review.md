# Relationship engine implementation review — 2026-09-17

## Scope reviewed

- Western Synastry v2, house overlays, Composite aspects, uncorrected Davison.
- Factual Jyotish D9/Navāṁśa gate.
- Ten-book relationship knowledge registry and editorial boundaries.
- Matching-related PRD/SRS and US-14–18 contracts, plus the pure five-energy slate selector.

## Documentation findings

- Fixed: runtime now follows the existing multidimensional requirement instead of offering a new total score.
- Fixed: Synastry has a separate versioned orb policy; it no longer silently inherits natal orbs.
- Fixed: method limitations are explicit for Composite houses and uncorrected Davison.
- Deferred: corrected Davison, progressions, Ashtakoota and generated Jyotish relationship prose require reference fixtures/domain-expert approval.

## Security findings

- No new endpoint, database table, external model call or log field was added.
- Pair calculations reject mixed calculation configs; facts cannot silently combine tropical/sidereal systems.
- Fixed during review: pre-mutual selector input was narrowed from the full relationship bundle to dimensions + evidence ids + method version; Composite/Davison never enter candidate selection.
- Later API integration must verify authorization to both profiles and rerun block/report/safety filters before mutual creation.
- No P0/P1 issue found in this pure calculation/static registry slice.

## Privacy findings

- Birth time/place, coordinates, intent and pair-derived facts remain classified as sensitive.
- The new code calculates in memory and does not persist or transmit these fields.
- Psychology concepts are prohibited from hidden inference/ranking. Consent to astrology does not authorize diagnosis or behavioral profiling.
- Later product integration still needs separate matching consent, retention/deletion propagation, redacted analytics and access-control tests.

## Sources checked

- Official publisher/author pages for the ten registered books.
- Astrodienst relationship chart/partner FAQ and Davison/Composite method references.
- Existing project PRD/SRS, astro spec, US-14, US-15, US-16 and privacy/security gates.

## Verification evidence

- Focused astro + relationship tests: passed.
- Full API suite: 276 tests passed.
- mypy: 178 source files passed.
- Ruff lint/format and generated OpenAPI/TypeScript contract checks passed.
