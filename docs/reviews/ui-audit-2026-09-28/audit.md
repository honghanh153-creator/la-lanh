# UI audit — Lá Lành mobile beta

Date: 2026-09-28  
Viewport: 390 × 844 CSS px  
Evidence: screenshots captured from `http://127.0.0.1:5202` in this audit run.

## Overall verdict

The initial audit found a recognisable Cosmic Glass Signal identity but weak hierarchy and pacing. The final implementation now gives each reviewed screen one clear primary job, limits each viewport to one lime action, and makes Tarot, Home and onboarding scan in the intended order. The representative mobile flow is ready for product review; remaining findings are non-blocking system-cleanup work.

## Steps reviewed

1. **Welcome — needs simplification.** The value is understandable, but the progress label `00/02`, large decorative art and three privacy statements make a three-step flow feel longer than it is. Evidence: `current/01-welcome.png`.
2. **Consent/privacy — structurally healthy, visually dense.** The control and deletion promises are good. The ivory note contains too many equally weighted blocks for a pre-use moment. The full detail belongs on `/privacy`; onboarding should show a short purpose/retention/control summary. Evidence: `current/02-consent.png`.
3. **Birth date — healthy core task, excessive atmosphere.** The three fields and CTA are clear, but the progress copy and art consume space without helping input. Validation is only visible after submit. Evidence: `current/03-birth.png`.
4. **First reveal — clear but generic.** It successfully rewards the user, yet the source/provenance line is too prominent and the next benefit is vague. Evidence: `current/04-reveal.png`.
5. **Home — needs hierarchy correction.** Daily Note, question router, context picker, unlock card and navigation all compete. The user first sees a long note before the explicit “Bạn đang muốn hiểu điều gì?” router, so the product's three jobs are discovered late. Evidence: `current/05-home.png`.
6. **Tarot start — major friction.** Six context choices, three suggestions, a textarea and the spread selector are presented as three form panels. It is long, technical and does not support five cards. Evidence: `current/06-tarot.png`.
7. **Radar landing — useful explanation, too long.** The value proposition is stronger than before, but the same CTA and privacy message repeat after multiple educational sections. Evidence: `current/07-radar.png`.
8. **Profile — healthy but flat.** Privacy controls are present, but every setting is the same dark card. Theme, chart layer and data controls need clearer grouping and state hierarchy. Evidence: `current/08-profile.png`.

## Highest-impact changes

- Put the Home question router before the Daily Note; keep the Note as the first personalised answer, not the first navigation decision.
- Rebuild Tarot around one question field, a compact context row and a recommended 1/3/5-card depth card.
- Replace onboarding's technical `00/02` language with `Bước 1/3`, `2/3`, `3/3`; reduce decorative art height and keep one sentence of privacy copy per screen.
- Use the ivory paper surface only for the main content object. Keep controls on dark glass so nested borders do not compete.
- Keep one lime primary action per viewport; make all other actions text or outline treatments.
- Stop using text below roughly 12 CSS px for privacy, source and helper copy.

## Accessibility risks visible from screenshots

- Several helper and provenance lines appear below comfortable mobile reading size and use low-contrast lavender on indigo.
- The app relies heavily on colour/border changes to show selected states; selected controls should also have a visible icon or text marker.
- Full-page screenshots cannot prove focus order, screen-reader names, reduced motion, keyboard behaviour or dynamic error announcements; these require interaction tests.

## Evidence limits

This pass reviewed representative primary routes, not every authenticated, error, empty, expired, result and sharing state. Radar result IDs and completed Tarot sessions were not available in a stable state for this screenshot set.

## Final implementation review

### Changes verified

1. **Tarot — passed.** The selected question-first design is implemented with a single ivory question field, compact context chips, a recommended 1/3/5-card depth control and one lime draw CTA. Five-card choice, loop, conversation and clarity maps are frozen by the API and render through the complete draw flow. Evidence: `final/01-tarot-question-first.png` and `final/tarot-comparison.jpg`.
2. **Welcome and consent — passed.** The duplicated consent stop was removed from the active onboarding path. `/welcome` now carries the short purpose, retention and control summary; `/privacy` retains the full detail. `/consent` safely aliases the canonical start. Evidence: `final/02-welcome.png` and `final/03-consent-alias.png`.
3. **Birth input — passed.** The progress language is now `Bước 2/3 · Ngày sinh`, with reduced decorative height and one clear submit action. Evidence: `final/04-birth.png`.
4. **First reveal — passed.** The screen is the third and final onboarding reward, avoids duplicated labels and names the next value directly through `Mở Note hôm nay`. Evidence: `final/05-reveal.png`.
5. **Home — passed for hierarchy.** The question router now appears before the Daily Note and exposes the four core jobs—self, another person, today's context and Tarot—without repeating a second natal acquisition card. Evidence: `final/06-home.png`.

### Deliberate differences from the selected Tarot reference

- The implementation adds broader contexts than the static concept so it can route real product questions.
- The question limit is 280 characters rather than 500 to protect mobile scanability and reading quality.
- A compact privacy line states when the question is sent, encryption retention and analytics handling.
- Selected chips use both a check icon and colour, rather than colour alone.

### Remaining non-blocking items

- **P3:** split the current web JavaScript bundle (approximately 717 kB) after beta usability work stabilises.
- **P3:** consolidate duplicated shell and bottom-navigation implementations into one app-frame component.
- **P3:** run a separate state inventory for authenticated, expired, empty and share-result routes; these were outside this representative visual pass.

### QA result

- Web lint, typecheck and component tests: **38 files / 135 tests passed**.
- API test suite: **356 tests passed**.
- Native Swiss Ephemeris, contracts, content-matrix audits and real guest → birth → Daily Note smoke flow: **passed**.
- Manual Tarot five-card flow at 390 × 844: **passed**.
- Final visual comparison: **passed**.
