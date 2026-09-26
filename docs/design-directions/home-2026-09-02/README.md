# Home redesign — five minimal directions

Date: 2026-09-02

## Source of truth

- Approved reference: `prototype/public/design-reference.png`
- Product behavior: `docs/user-stories/US-03-doc-note-hom-nay.md`, `US-04-mood-check-in.md`, `US-05-luu-va-chia-se-note.md`, and `US-06-bo-sung-gio-noi-sinh.md`
- Quality gates: `docs/reference/quality-gates-doc-security-privacy.md`

## Why the current frontend drifts

1. The reference has one dominant object: the physical daily note. The implementation presents greeting, note, mood, actions, unlock teaser, and navigation at nearly equal visual weight.
2. The reference relies on a precise collage composition and real paper depth. The frontend replaces these with generic CSS circles, radial backgrounds, panels, and outlines.
3. The current font tokens are platform fallbacks (`Avenir Next`, `Marker Felt`, `Segoe Print`, and others), so typography and spacing change between devices.
4. The decorative language is repeated across many components instead of being concentrated in one memorable hero moment.
5. The saved Home QA screenshot currently contains an Internal Server Error, so it cannot be accepted as visual evidence.

## Directions

| # | Direction | Main idea | Best quality | Trade-off |
|---|---|---|---|---|
| 01 | Editorial Note | One large tactile note and one eclipse | Closest to approved DNA | Still visually rich |
| 02 | Cosmic Card Deck | Collectible stack of daily cards | Strong product mechanic and Gen Z energy | Taller hero, less content above fold |
| 03 | Warm Electric Bento | Light paper canvas with one dark hero | Fastest to scan and most accessible | Less mysterious than dark modes |
| 04 | Midnight Whisper | A secret note revealed in darkness | Warmest mystery and strongest focus | Must be tested carefully for dark-mode contrast |
| 05 | Young Leaf Orbit | Fresh leaf green with organic orbit | Most alive and distinctive | Furthest from the electric-purple reference |

## Implementation guardrails

- Use exactly two bundled font families: one UI/display family with Vietnamese glyph coverage and one handwriting family used only for the note headline or kicker.
- Keep one dominant hero, one primary action, one secondary action, and one decorative celestial/organic cluster per screen.
- Keep body text contrast at least 4.5:1; design primary touch targets around the iOS 44 pt default and never below WCAG 2.2 minimum target/spacing requirements.
- Use labels in addition to color for mood state. Support larger text without hiding core content or actions.
- Home and share-safe surfaces must not reveal date of birth, exact birth time, birth place, coordinates, guest/session identifiers, or account identifiers.
- The unlock teaser describes the benefit but does not display unconfirmed Moon/House data or silently collect additional birth data.

## Recommendation

Use **02 Cosmic Card Deck** as the strongest product direction. It converts the note from decoration into a collectible daily object while keeping the flow simple. Borrow the typography restraint and spacing from **04 Midnight Whisper**. Keep **03 Warm Electric Bento** as the accessibility/light-mode reference.
