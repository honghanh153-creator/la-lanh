# Tarot reveal and full local review

Scope: owner request on 2026-10-09. Local web review of the app journey; no deployment, purchases or paid generation. Builds on the existing security/content work without declaring its unresolved audit/release gates complete.

## Product contract

Welcome → consent CTA → birth date (optional time/place) → reveal → Home. From Home: today's note, natal/insights, Tarot, private Radar and profile/settings. Tarot: question/context → 1/3/5-card depth → locked fan → select cards → short reveal → summary → expandable details → another question or delete.

After a successful final selection, show the server-selected cards turning over inside a violet, illuminated scene. A slow halo and small orbit accents create a moment of anticipation; do not suggest a new calculation or fabricate progress. Copy: “Bài của bạn đang mở”. Default ceremony lasts 2.8 seconds, with “Xem bài ngay”. No new request, reroll, sound, vibration or third-party asset.

## Acceptance criteria

- Only a new successful completion with a reading triggers the ceremony. Intermediate picks, errors, missing readings and restored complete sessions do not.
- Actual server-selected order, titles and 1/3/5-card counts are preserved. Five cards fit a small viewport.
- Skip opens the summary immediately. System reduced-motion or the existing shared pause preference bypasses the ceremony; changing reduced-motion while it runs ends it.
- Timer/subscription cleanup on unmount, completion and route changes. No flashing or infinite loop; keyboard focus moves to the ceremony then report heading.
- Summary remains above card details. Existing no-reading, retry, ownership and delete paths stay intact.
- Test the main local journey using synthetic data, record actual passes/gaps and leave a fresh welcome URL for owner review. Do not silently erase the owner's live data.

## Gates

Docs: map changed behavior here and record QA evidence. Accessibility reference: [W3C Animation from Interactions](https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions), [C39 reduced-motion](https://www.w3.org/WAI/WCAG22/Techniques/css/C39.html), checked 2026-10-09.

Security/privacy: presentation only; no new endpoint, permissions, external transmission, analytics, storage, share capability or provider request. Existing session ownership/consent remain unchanged. Titles are React-rendered text, not HTML. Paid generation stays disabled for review. This change does not certify the outstanding system-wide security scan or production controls.

## Execution

- [x] Implement ceremony and transition regression tests.
- [x] Run frontend suite, lint, typecheck and production build.
- [x] Check the live local journey on mobile, including completion and restored results.
- [x] Save review evidence and hand off at the welcome screen.

Receipt: [full local review](../reviews/2026-10-09-full-flow-tarot-reveal-review.md). Checked items refer only to this scoped change, not to all roadmap or security/content release requirements.
