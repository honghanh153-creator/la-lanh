# Code review — content trust and Home priority

Date: 2026-09-29

## Actionable Findings

All release-blocking findings found during the review were fixed:

1. **Historical Western v4 plans could stop loading after the v5 bump.** New plans still emit v5;
   the model now accepts the persisted v4 format and rejects unknown older versions. Regression
   tests cover both paths.
2. **The review script could pass with fewer than 20 readings.** It now requires exactly ten
   persona IDs and both Daily and Tarot for every persona.
3. **Evidence was only checked for a non-empty label.** Daily samples now must pass the existing
   five publish gates and use actual evidence factor references; Tarot source IDs must belong to the
   registered catalog.
4. **Coverage was narrower than the product contract.** The fixture now alternates date-only and
   full-chart Daily inputs and rotates one-, three- and five-card Tarot spreads.
5. **Several reviewer branches were untested.** Tests now isolate weak disclaimers, unobservable
   scenes, non-testable actions, missing provenance, unvalidated evidence and incomplete persona
   coverage.
6. **Disclaimer separation was only asserted on the shared reading component.** Home's empty branch
   order and the Tarot, Radar and Reveal notice semantics now have page-level assertions.
7. **The deploy command could bypass the local review checklist.** Hetzner deployment now runs the
   content reviewer inside the newly built image before migration and before replacing the public
   app container.

Low-priority maintainability feedback was also addressed by making the audit reuse the review
agent's canonical banned-fragment list and removing obsolete shared disclaimer selectors. The old
Radar-specific selectors remain harmless dead CSS and can be removed when that stylesheet is next
split; they do not affect the new shared notice.

## Coverage

- Correctness: reading version compatibility, evidence binding, exact fixture cardinality,
  Home hierarchy and runtime provenance.
- Security/privacy: synthetic inputs only, no production records, no new external call, no secret or
  prose logging, existing privacy/runtime/mobile guards passed.
- Tests: 135 web and 368 API tests; all content/Tarot/Radar audits passed.
- Release: production build and end-to-end guest → birth → Daily Note smoke passed.

## Verdict

**PASS — ready for product review.** No unresolved high- or critical-severity finding remains.
Human moderated validation is still required before claiming that ten real users find the content
personally useful. The existing JavaScript chunk-size warning is non-blocking and unrelated to this
change.
