# Radar result v2 — code review

**Date:** 2026-09-21  
**Scope:** Radar projector, API contract, result UI, privacy documentation and focused tests.  
**Plan:** `docs/plans/2026-09-21-2140-feat-radar-deep-relationship-reading-plan.md`

## Actionable Findings

No unresolved actionable findings remain.

The review found and fixed three issues before this receipt:

1. Evidence provenance initially listed only synastry contacts while the public perspective claim also used house overlays. The metadata now contains every evidence ID used by the rendered sections, including Composite.
2. The first overlay was selected by engine order, which biased the perspective chapter toward the Sun for most pairs. Selection now follows the strongest pair motifs and preserves A→B/B→A direction.
3. A rare bundle with no eligible contact could raise an uncaught `ValueError`. The service now translates projection failure into the Radar domain error handled by the API rather than returning a server error.

## Coverage

- Correctness: deterministic output, contradictory evidence, context invariance and pair distinctness.
- Contract: `radar-result-v2`, backward read of v1, generated OpenAPI and TypeScript contract.
- Privacy/security: owner-bound encrypted result path remains unchanged; raw DOB/time/place/coordinates are absent from projection; no external generation provider; deletion, withdrawal and TTL behavior preserved.
- UI/accessibility: semantic headings, labeled meters, native details disclosure, 390px no-overflow check and browser console review.
- Not covered as a public-release claim: legal sufficiency of third-party permission attestation, editorial expert sign-off, or production purge/APM configuration.

## Verification

- API: 293 tests passed.
- Radar focus: 8 tests passed.
- Web: 97 tests passed.
- Python lint/format/typecheck: passed.
- Web lint/typecheck/production build: passed.
- Runtime mock guard, privacy guard and OpenAPI drift check: passed.
- Browser E2E: onboarding → exact owner chart → private Radar input → result v2; evidence accordion opened; no console warning/error; no horizontal overflow at 390px.

## Verdict

**Ready with release gates.** The local product path is complete and testable. Public/native release still requires the existing legal review for third-party birth data, scheduled physical purge evidence, device E2E/accessibility and editorial sampling defined in the Radar spec.
