# Design QA — Cosmic Glass Signal refresh

Date: 2026-09-28

Viewport: 390 × 844 CSS px

Selected reference: `/var/folders/dh/my7pp465325dcfxnznhylvkr0000gn/T/codex-clipboard-18708661-83c2-4af2-aa19-d37efebb454b.png`

## Scope

- Tarot question-first entry and 1/3/5-card selection
- Welcome, consent alias, birth input and first reveal
- Home information hierarchy and route discovery
- Shared type, colour, surface and primary-action consistency

## Iterations completed

1. Audited the existing mobile flow and captured the initial representative routes.
2. Rebuilt Tarot around the selected visual direction and implemented the missing five-card product contract.
3. Removed the duplicate consent step and compressed onboarding into three understandable moments.
4. Moved the Home question router above the Daily Note and removed competing acquisition content.
5. Captured the final routes at the target viewport and compared the Tarot implementation directly against the selected reference.

## Findings and resolution

| Priority | Finding | Resolution | Status |
| --- | --- | --- | --- |
| P0 | None | — | Passed |
| P1 | Tarot was long, form-like and lacked five-card support | One question field, compact contexts, recommended 1/3/5 depth and full five-card API/UI flow | Fixed |
| P1 | Home hid the product's core jobs below a long Daily Note | Question router moved to the top; Tarot and three answer routes are visible before the note | Fixed |
| P1 | Onboarding repeated consent and felt longer than the actual flow | Canonical three-step flow; `/consent` aliases `/welcome`; detailed terms remain on `/privacy` | Fixed |
| P2 | Several selected states relied mainly on colour | Added visible check/text state to compact controls | Fixed |
| P2 | Multiple lime actions competed in one viewport | Retained one primary lime action per reviewed screen | Fixed |
| P2 | Privacy helper copy was scattered | Consolidated into one compact line near the committing Tarot action | Fixed |
| P3 | Large web bundle and duplicated shells | Logged for post-beta structural cleanup | Open, non-blocking |

## Evidence

- Final Tarot: `docs/reviews/ui-audit-2026-09-28/final/01-tarot-question-first.png`
- Reference comparison: `docs/reviews/ui-audit-2026-09-28/final/tarot-comparison.jpg`
- Welcome: `docs/reviews/ui-audit-2026-09-28/final/02-welcome.png`
- Consent alias: `docs/reviews/ui-audit-2026-09-28/final/03-consent-alias.png`
- Birth: `docs/reviews/ui-audit-2026-09-28/final/04-birth.png`
- Reveal: `docs/reviews/ui-audit-2026-09-28/final/05-reveal.png`
- Home: `docs/reviews/ui-audit-2026-09-28/final/06-home.png`

## Final result

**Passed.** No P0 or P1 visual blocker remains in the reviewed representative flow. The remaining P3 items do not block product review.
