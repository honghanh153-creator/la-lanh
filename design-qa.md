# Design QA — lịch sử và kết quả hiện hành

Kết quả hiện hành là phần **Ultraviolet fidelity — 07/10/2026** ở cuối tài liệu. Các pass trước đó không còn là bằng chứng cho giao diện hiện tại.

## Home option 1 — lưu lịch sử

Date: 2026-10-02

## Compared artifacts

- Selected reference: `/Users/phamhanh/.codex/generated_images/019eea8d-5cee-7e90-aea9-7e655ab613c8/exec-fb4eee75-b8a1-43a6-afd0-4f8cc6590336.png`
- Final local capture: `/tmp/la-lanh-home-option1-final.png`
- Viewport under test: 390 × 844 CSS pixels
- State: date-only guest with a generated daily note

## Blocking checks

- P0: none.
- P1: none.
- P2: none.

## Match assessment

- Preserves the selected hierarchy: product promise → personalized note → one primary action → three exploration routes → Tarot as a secondary clarification path.
- Preserves Cosmic Glass Signal: navy cosmos, warm paper, restrained lime/lavender/coral, one Be Vietnam Pro family.
- Removes the detached question and daily-note headings that made the previous Home feel assembled from unrelated modules.
- Keeps feedback/share compact on the note and retains mood, context switching, full-chart unlock, and the existing backend reading.
- Uses four bottom-navigation destinations so the primary app structure is easier to scan.

## Interaction verification

- Home loaded with a real locally generated daily note.
- Primary CTA opened `/note/today` successfully.
- Evidence disclosure expanded and showed the chart basis.
- “Một người” routes to `/radar`.
- No browser console errors or warnings were observed.

## P3 follow-up

- The implementation uses the existing paper texture and rounded paper edge rather than reproducing the generated mockup's irregular torn silhouette pixel-for-pixel. This does not affect hierarchy or usability.

final result: passed

## Ultraviolet Paper — selected-reference rollout, 2026-10-06

- Current authority: `docs/design-directions/ultraviolet-paper-2026-10-06/reference.png`, the user's cream/violet/lime Home. This replaces earlier visual directions, not their functional/privacy acceptance criteria.
- Full route inventory and visual rules: `docs/design-directions/ultraviolet-paper-2026-10-06/README.md`.
- Local running review: `http://127.0.0.1:5207/welcome`; gallery of 26 real screen captures: `docs/reviews/ultraviolet-paper-2026-10-06/gallery.html`.
- One Be Vietnam Pro family, restrained type scale, cream base, one violet focal card, readable lime actions. Light is the new-user default; saved dark preferences and the Profile toggle remain intact.
- Applied to onboarding, Home/Note, birth-data supplement, Natal/chart settings/Sky, Tarot, Radar, sharing/saved, Profile and ancillary customer states. CMS and deferred stranger matching remain outside this redesign.
- Manually exercised fresh guest onboarding, full-chart cutover, mood, reading/save, three- and five-card Tarot, private Radar with unknown time, Western/Jyotish, chart settings and theme switching using synthetic QA profiles.
- Fixed cascade order, overlapping share preview, clipped note copy, pale Radar labels, partial exact-time validation and the missing Saved entry after bottom-nav simplification.
- At 390 × 844 and selected 320 × 740 checks, no page-level horizontal overflow was observed. No console errors were observed in the exercised flows.
- Lint/typecheck/build pass; 41 frontend test files / 145 tests pass. No deployment, public sharing or paid generation was performed.
- Remaining release checks: valid-token/two-device invitation/share/revoke flows, legacy result states, native share/download rendering, unfinished account login, exported birth/Radar artwork, and separate content-quality review. Sky's backend timestamp explanatory copy is inconsistent and remains tracked, not silently declared fixed.

final result: passed for the exercised visual flows; partial for token/legacy/native states and full-system copy quality. See `docs/reviews/ultraviolet-paper-2026-10-06/README.md` for evidence and limitations.

## Home daily scene/advice pass — 2026-10-02

- Main paper card now describes one concrete, observable situation; it does not contain an instruction.
- Advice is isolated in a separate dark panel labelled “Lời nhắc hôm nay”, followed by one action CTA.
- Removed “Vì sao dành cho bạn?”, birth-data source labels, evidence disclosure, and chart-status helper copy from Home. Technical evidence remains available on the detailed reading surface.
- Mobile capture at 390 × 844 confirms the first viewport scans in this order: product promise → scene → advice → action.
- Automated gates cover advice leakage, issue/advice mismatch, plain-language review, and source coverage.
- No new personal-data field or external runtime request was introduced.

final result: passed

## Ultraviolet fidelity — 07/10/2026 (current)

### Visual truth and normalized evidence

- Selected source: `docs/design-directions/ultraviolet-paper-2026-10-06/reference.png`, 853×1844, normalized to 390×844 (approximately 2.187 density).
- Running customer UI: `http://127.0.0.1:5207/home`; capture `docs/reviews/ultraviolet-fidelity-2026-10-06/after/01-home.png`, 390×844, density 1.
- Both artifacts were opened together in `docs/reviews/ultraviolet-fidelity-2026-10-06/comparison.png`. Header and illustrated exploration were also compared together in `comparison-header.png` and `comparison-explore.png`.
- State: light Home, closed sheets, actual synthetic guest reading on 07/10. Source has a different date and shorter sample copy. Main card therefore grows; this is not a same-content pixel-diff or a claim that exploration fits the first viewport for every reading.
- Other routes inherit the selected visual system; there are no selected reference images for each of their data states. Fresh screenshots were inspected individually, not falsely scored against invented source frames.

### Findings, fixes and recapture

- [P1, fixed] Old dark panels and pale text survived the theme on Radar invitations, recipient explanations, score disclosures and the Tarot bridge. Explicit customer tokens now cover these states. Evidence: frames 49, 50, 51, 52, 53 and 54.
- [P2, fixed] Earlier Home was a palette change rather than the selected composition. Removed redundant context/action/link rows; added matching paper texture, orbital header, moon context trigger, illustrated Tarot/Radar paths and filled active navigation icons. Evidence: comparison and frames 01/59.
- [P2, fixed] Demo badge/caption occupied the same line; its privacy button restarted onboarding. Caption is block-level, and the button opens `/privacy`, covered by a new regression test. Evidence: frame 11.
- [P2, fixed] Aura orb overlapped its heading and automatic heading focus produced a decorative lime box. Orb is in normal flow; screen-reader focus remains, interactive focus rings remain. Evidence: frame 31.
- [P2, fixed] Birthplace results squeezed title/helper into columns and clipped helper text in fixed-height buttons. Results are left-aligned vertical rows with auto height. Evidence: frame 36.
- [P2, fixed] At 320px, primary navigation labels wrapped. Small-screen nav keeps a single line without shrinking touch targets. Evidence: frame 55.
- [P2, fixed] Inactive context icons and score evidence were hard to see. Higher-contrast purple foreground and clear target sizing now apply. Evidence: frames 45/49.

### Verification and limits

- 42 frontend files / 146 tests pass; lint, typecheck and build pass. Runtime mock, privacy and mobile configuration guards pass. No paid generation or production deployment performed.
- 58 review frames retained in the gallery; primary routes, reading templates, onboarding inputs, Tarot 3/5-card draws/results, Radar report/invitation states, sheets, light/dark and selected 320px breakpoints inspected. No page-level overflow in measured captures. No JS console errors observed in exercised browser actions.
- Pixel-derived minimum contrast on the new violet texture: cream 6.29:1; lime 5.84:1. No lime body text on cream. This is not a full accessibility certification.
- Documentation, security/privacy deltas and the exact route/state inventory are in `docs/reviews/ultraviolet-fidelity-2026-10-06/README.md`. Consent remains explicit and unchecked; no personal-data or permission boundary was expanded.
- Not release-certified: two-device recipient receipt, valid share/revoke, legacy populated results, native sharing/export appearance, real account login and content comprehensibility across users. Old claims of exhaustive readiness must not be inferred from this visual pass.

### Follow-up polish

- Generated grain, moon/orbit and illustration details match the direction but not individual pixels. Remaining visual variance is P3.
- Runtime title/body/advice length changes card height; the current longer reading needs scrolling to the illustrated choices. Copy quality and mobile information density need a separate content pass, not text clipping or fake QA copy.
- Existing large JS bundle needs a separate code-splitting pass.

final result: passed

## Optional birth details + subtle planet material — 07/10/2026

Current delta, not a replacement for the full route QA above. Adds optional inline time/place in Birth, separate consent/skip, accurate missing-field CTAs and full-chart Reveal source/overview path. Purple focus cards now use the generated planet-surface WebP blended softly over the selected violet.

- Normalized source/runtime comparison opened: `docs/reviews/optional-birth-planet-2026-10-07/comparison.png`; actual copy/date differ. Also inspected 320px expanded Birth and dark form captures.
- Full synthetic optional save → Radar continuation without duplicate birth questions; full Reveal → Natal successfully exercised. No JS errors observed. Date-only route, consent validation/reset, skip and retry stages covered by automated tests.
- 44 frontend files / 165 tests pass; lint/typecheck/build and runtime guards pass. No deployment or paid rewrite calls.
- Critical contrast dependency: raw texture fails; `soft-light` over `#4b278f` produces minimum cream 8.39:1/lime 7.79:1. Keep blend, do not reuse raw asset underneath text.
- No P0/P1/P2 visual defect observed in captures scoped to this delta. Longer real copy still extends Home card; P3 density/copy work remains, not hidden by truncation.
- Limits: fresh no-pending-Radar browser E2E, deletion/revoke, complete token/share states, full backend/native/production gates not rerun. Existing approximate-night label ambiguity is recorded. No expanded personal-data access or new provider.

Detailed evidence, privacy/source checks and limitations: `docs/reviews/optional-birth-planet-2026-10-07/README.md`.

final result: passed for evidenced local visual/optional-onboarding scope; partial for full release readiness.

## Violet hue correction + replay entry — 07/10/2026, latest

- [P2 fixed] Previous soft-light planet material drifted from selected violet: reference background sample median #4c2e8e vs runtime #311288. Replaced with #4c2e8e base and a separate 9% luminance-only terrain overlay. New sample #482e8a.
- Opened `docs/reviews/optional-birth-planet-2026-10-07/comparison-color-corrected.png` at normalized 390×844. Same light Home layout but different real copy/date. Fonts, spacing/layout and illustrations unchanged; long-copy height remains the documented P3, not clipped.
- Home, Tarot and Radar recaptured. Background DOM and no horizontal overflow verified at 390. No console errors in exercised actions. Body contrast conservative bound ≥7.50:1 cream/6.97:1 lime; prior soft-light contrast numbers are historical, not current.
- Explicit `/welcome?restart=1` keeps Welcome open for user replay. Visiting alone does not reset data or consent; affirmative start clears stale local Radar intents through existing reset flow. Ordinary Radar onboarding still resumes. Covered by regression test.
- Lint/typecheck/build/runtime guards pass, 44 files/166 tests pass. Security/privacy boundaries unchanged; no deployment/payment. Sources and limitations in the linked QA receipt. Fresh browser E2E normal onboarding, native, production and token/revoke gates not claimed complete.

final result: passed for the current color fix and replay-entry scope.

## Shared time selector + concrete aspect copy + visible terrain — 07/10/2026, latest

- [P2 fixed] Hour-entry presentation diverged across inline onboarding, later supplement and Radar. All now consume `BirthTimeInput` + `BirthTimePicker`; only precision modes supported by each API are exposed. Radar other-person mode supports exact/unknown, not an unsupported approximate button.
- [P2 fixed] Mars–Moon natal copy used vague “needs competing” prose. Six aspect-specific scenes now describe observable conversations; retired fragments are blocked, renderer v9 creates a new revision, and browser reload confirmed the user's current `/note/today` is repaired without deleting its older snapshot.
- [P2 fixed] 9% luminance-only terrain was barely visible. Increased to 50%, preserving #4c2e8e hue and using the existing generated raster. Same-source terrain pixel model: cream ≥5.42:1, lime ≥5.03:1. Not a whole-app accessibility certification.
- Opened normalized source/runtime [time-control comparison](docs/reviews/optional-birth-planet-2026-10-07/time-content-terrain/time-component-comparison.png), matching 06:15 + minute focus; and [Home comparison](docs/reviews/optional-birth-planet-2026-10-07/time-content-terrain/home-reference-comparison.png), matching 390×844 light viewport with intentionally different real date/copy.
- Browser controls exercised: exact 06:15/00:00, approximate afternoon, unknown; unknown Radar hides/clears time. 320px onboarding has no horizontal overflow; mode buttons are 44px tall. No JS errors in inspected actions. No other-person birth form submitted.
- Lint/typecheck/build and runtime guards pass, **169 frontend tests / 506 backend tests** pass. Content release review: 10 synthetic personas / 30 readings, no critical/high, 36 medium follow-ups. No paid generation or deployment.
- Remaining P3: small source/runtime type-spacing differences, real Home copy grows the card beyond source height. Unresolved content work includes cross-section coherence and broader pair-scene authoring; this pass does not declare every interpretation or CMS editing surface complete.
- [Current receipt, sources, security/privacy delta and limits](docs/reviews/optional-birth-planet-2026-10-07/time-content-terrain/README.md). Native/production, all dark states, share/revoke and comprehension by real users are not release-certified here.

final result: passed for the evidenced time-control, targeted copy-repair and planet-material scope.

## Onboarding motion — 07/10/2026, latest

- 1/3 moon float + short brand-star wink; 2/3 small moon arrival without animating input fields; 3/3 gentle card reveal. All decoration ends within 4.4s. Existing raster/icon assets, palette/layout/content unchanged.
- Step indicator now corresponds to 33/67/100%, animates from the previous step using transform. Not a fake computation meter; no new delay, timeout, request or navigation logic.
- [P2 prevented] General reduce-motion CSS was weaker than new specific selectors. Its animation/transition override now has priority; regression guard added. Real OS reduced-motion browser state not emulated, see receipt limits.
- Actual 390px screenshots and captured-frame GIF inspected; CSS transforms changed then returned to rest, Birth fields have animation none, Birth/Reveal actions available without waiting, no horizontal overflow or JS errors in checked states. Content/CTA present immediately in all steps under unit tests.
- Lint/typecheck/build and runtime guards pass, 46 files / 172 frontend tests pass. No backend change, paid generation, deployment or data-access expansion.
- [Motion receipt, AC, official W3C sources and limits](docs/reviews/optional-birth-planet-2026-10-07/onboarding-motion/README.md). Native/production and a new guest E2E not rerun; current profile and DB retained.

final result: passed for evidenced onboarding-motion scope.

## Onboarding motion v2 — 07/10/2026, supersedes finite bob

- [P2 fixed] Finite vertical bob felt like a one-time entrance. Current moon drifts/tilts/scales continuously with two counter-orbiting stars and staggered brand-star motion. No palette/content/field changes or artificial wait.
- [P2 prevented] Looping nonessential motion needs a stop mechanism. Header Pause/Play controls all decorative loops, is 44×44px and keyboard-operable; state survives SPA route changes in AppShell memory, without new storage/telemetry. Reduced-motion CSS disables animation and hides the unneeded control.
- Captured >11 seconds: planet transform keeps changing, heading rect stays identical. Paused transforms remain equal. Fresh isolated guest E2E: Welcome → Birth → real Reveal → Home, pause survives transition, date fields work while paused, keyboard resume and completion pass. No overwrite/reset of the 5207 session or paid generation.
- 320px Welcome/Birth/Reveal have no horizontal overflow. 46 files / 174 frontend tests, lint/typecheck/build and runtime guards pass. Backend unchanged; full backend suite not rerun.
- [Current AC, proof clip, screenshots, official W3C sources, doc/security/privacy review and limits](docs/reviews/optional-birth-planet-2026-10-07/onboarding-motion-v2/README.md). Native hardware, OS reduce-motion emulation, FPS/battery and production release remain unverified. Existing bundle-size warning remains.

final result: passed for evidenced motion v2 and date-only guest E2E scope.
