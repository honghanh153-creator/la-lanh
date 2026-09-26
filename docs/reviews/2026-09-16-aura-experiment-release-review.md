---
title: "Aura Cutover + One Small Experiment — Release Review"
date: 2026-09-16
plan: docs/plans/2026-09-16-0801-feat-aura-cutover-small-experiment-plan.md
status: qa-ready
---

# Aura Cutover + One Small Experiment — Release Review

## Verdict

The scoped app/web feature is QA-ready. Aura activation and experiment choice remain separate, explicit decisions; stale chart/transition/experiment state is rejected; private payloads are encrypted and lifecycle-bound. No unresolved correctness, security or privacy finding blocks local QA.

Production release remains gated on two deployment facts: configure the six-hour retention cleanup in `docs/operations/aura-experiment-retention-runbook.md`, and provide the real versioned HTTPS API origin before Capacitor sync. Native simulator/device smoke remains required.

## Actionable Findings

| Severity | Finding | Resolution |
|---|---|---|
| P1 | “Giữ Note hiện tại” was remembered only in localStorage. | Added owner-scoped, CSRF/origin-protected acknowledgement persisted against the exact transition identity; local opaque marker is fallback only and is removed by personal-data deletion. |
| P1 | A chosen experiment could survive a changed current chart snapshot. | `current` and `reflect` now invalidate/delete stale rows; exact birth-input change is covered by API and persistence tests. |
| P1 | Aura activation could race a birth-snapshot update. | Activation now locks the birth-profile row before comparing the current snapshot. |
| P1 | Replace confirmation could stay armed after a cross-device `409`. | Confirmation resets on held experiment ID/version change; held action details remain visible across lens changes. |
| P1 | Experiment persistence guarantees lacked direct encryption/rollback/purge tests. | Added ciphertext-canary, atomic rollback, bounded purge and stale-snapshot lifecycle tests. |
| P1 | The browser gate did not cover the new vertical slice. | E2E now covers exact supplement → Aura Cutover → activate → choose → Note Detail → undo on mobile and desktop. |
| P2 | Exact supplement fetch failure could bypass Aura Cutover. | Successful exact submission now routes to Cutover even when the immediate note refresh fails; Cutover owns retry/error state. |
| P2 | Activation conflict left a stale gift actionable. | Shared activation hook invalidates/refetches the Daily Note on `409`. |
| P2 | Reflected experiments exposed an impossible undo action. | Undo is hidden after reflection; reflection remains user-opened and separate from Resonance. |
| P2 | Repeated choose/reflect could accumulate same-target rows. | Added immutable-target uniqueness and conflict-safe behavior. |
| P2 | Aura preview contrast and transition focus were weak. | Corrected the preview label token and focuses the Cutover heading on route entry. |
| P2 | A 30-day expiry without scheduler margin could exceed the promise. | Rows expire at 29d18h; production must run bounded cleanup every six hours and alert on a missed window. |

## Coverage

- Correctness review: projection/snapshot races, stale experiment lifecycle, activation/refetch and multi-device replacement.
- Security/privacy review: owner binding, CSRF/trusted Origin, encrypted payload, consent atomicity, data deletion, retention and public-surface exclusion.
- Design/accessibility review: opt-in cutover, independent CTA, held-state clarity, focus, contrast and mobile behavior.
- Testing review: persistence-layer guarantees, exact unlock receipt and full browser vertical slice.
- Cross-model pass: not run; no different-provider review CLI is installed on this host.

## Verification

- Web unit/integration: 22 files, 67 tests passed.
- Browser E2E: 8 scenarios passed in mobile and desktop Chromium, including the complete new vertical slice.
- API: full pytest suite passed; focused Aura/experiment/privacy suite passed.
- Quality: web typecheck/lint, API Ruff/format/mypy, OpenAPI/TypeScript contract check and privacy guard passed.
- Production bundle and QA server smoke passed.
- Mobile release guard: 4 tests passed; iOS privacy manifest and Android fail-closed transport config remain valid.

## Known release gates

- `pnpm mobile:sync` intentionally refuses to package until `VITE_API_BASE_URL` is a real absolute HTTPS `/v1` origin. This is a release safety gate, not a feature failure.
- The production scheduler must execute the bounded cleanup at least every six hours.
- iOS Simulator and Android emulator/device smoke were not available in this run and remain required before store release.
- The current web bundle emits a size warning above 500 kB; this is a performance follow-up, not a functional blocker for this scope.
