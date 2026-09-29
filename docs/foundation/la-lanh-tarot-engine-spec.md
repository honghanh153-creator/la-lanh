# Lá Hỏi — Tarot engine specification

Status: question-first 1/3/5-card slice implemented on 2026-09-28. CMS and live-reader mode are out of scope.

## Product promise

Lá Hỏi is a private self-draw reflection flow. The user brings one real question, chooses one,
three, or five face-down cards from a 78-card fan, and receives a concrete reading anchored to an everyday
scene, a reflection question, and one reversible action. It does not predict certainty or claim to
read another person's mind.

Entry points are `/tarot`, Daily Note, and the owner-only Radar result. Daily/Radar entry links carry
only allowlisted `origin`, `context`, and `prompt` identifiers. They never put reading prose, names,
birth data, or report evidence in the URL.

## Reading contract

- Context is one closed value: general, relationships, work, communication, energy, or self-care.
- The user can edit the suggested question before starting.
- The question gate reframes third-party mind reading, deterministic prediction, and medical,
  legal, or financial decision questions.
- Question intent is classified into clarity, boundary, next step, communication, or self-check.
  This typed intent changes the rendered interpretation; it is not decorative metadata.
- One-card spread: `Điều đáng nhìn lúc này`.
- Three-card spread: `Điều đã rõ` → `Điều dễ bỏ sót` → `Một bước nhỏ có thể thử`.
- Five-card mode chooses and freezes one map when the session starts:
  - clarity: facts → assumption → need → agency → next check;
  - loop: trigger → habitual response → immediate payoff → later cost → alternative;
  - choice: non-negotiable need → option A gain/cost → option B gain/cost → real trade-off → criterion;
  - conversation: facts → feeling → need → boundary → opening line.
- The client recommends depth locally from the question shape. The question is not transmitted for
  recommendation; the server validates the final question and freezes the spread map only after the
  user presses `Xòe bài`.
- Every position contains: card theme, contextual meaning, everyday scene, reflection question,
  and a small action with explicit permission to stop when it does not fit reality.
- The launch voice is fixed to `playful_grounded`: current, direct, lightly playful, and never
  mystical filler. Voice selection is deliberately not another onboarding step.

## Deck and synthesis

The launch deck contains 22 Major Arcana and 56 Minor Arcana, upright only. Major Arcana have
original, card-specific Vietnamese semantic atoms. Minor Arcana use a compositional matrix:

`suit domain × rank motion × tension × resource × context lens × spread map × position × question intent`

This lets the engine vary by question and position without pretending random prose is
personalization. Reversals, named historical spreads, deck imagery, AI prose generation, and live
reader interpretation are deferred.

Every output records schema, knowledge, renderer, gate, deck, spread, question-rule, methodology,
and actual concept-source versions. Provenance includes only sources whose concept categories were
used in that reading.

## Knowledge sources

Eight books inform methodology at concept level only:

1. Rachel Pollack, *Seventy-Eight Degrees of Wisdom* — archetypal depth and symbolic tension.
2. Mary K. Greer, *Tarot for Your Self* — self-reflection and reader agency.
3. Evelin Bürger and Johannes Fiebig, *The Complete Book of Tarot Spreads* — position discipline
   and spread intent.
4. Deborah Lipp, *Tarot Interactions* — interaction, contrast, and progression across cards.
5. Benebell Wen, *Holistic Tarot* — non-deterministic ethics and personal-development framing.
6. Joan Bunning, *Learning the Tarot* — story coherence and everyday meaning.
7. Melissa Cynova, *Kitchen Table Tarot* — plain-spoken readings grounded in practical context.
8. Lisa Freinkel Tishman, *Mindful Tarot* — present-focused reflection and distance from prediction.

No book text, proprietary card entry, named spread, exercise, layout, table, case study, metaphor,
or illustration is copied into runtime knowledge. All Vietnamese card atoms and output templates
are original product content. Detailed rights notes are in `docs/legal/tarot-source-rights-notes.md`.

## State, privacy, and security

- Direct use creates a Tarot-only guest after the user presses `Xòe bài`; it does not fake or reuse
  birth-profile consent.
- Before that action, UI states that question and draw are encrypted, kept for at most 30 days, and
  deletable at any time.
- The server securely shuffles and encrypts the full deck order before the fan is shown. The UI must
  say the order was locked, not claim a publicly verifiable cryptographic commitment.
- Question, prompt ID, deck order, selections, and frozen result live only inside an AES-GCM payload
  bound to the session ID. The row contains operational state and no plaintext question or reading.
- Owner access requires the current guest; mutations also require trusted Origin and CSRF proof.
- Session creation is idempotent. Selection uses row locking plus expected version; a duplicate tap
  on the same card returns current state, while a competing stale selection fails closed.
- Private routes are `no-store`. Questions and reading prose are prohibited from logs and analytics.
- Sessions expire at 29 days 18 hours, leaving cleanup margin inside the stated 30-day limit.
- Start and select routes have in-process admission limits; production still requires edge limits.

## Quality gates

`pnpm tarot:audit` renders all 78 cards in all six contexts plus multi-card samples. It fails on
missing deck/source coverage, forbidden mystical filler, empty or thin semantic blocks, missing
provenance, and repeated three-card meanings/actions. It runs inside `pnpm check`.

Required release checks also include API contract generation, backend unit/API tests, frontend
type/lint/tests, mobile viewport visual inspection, keyboard selection, refresh/resume, delete,
question reframe, CSRF rejection, owner isolation, and expiry cleanup.

## Deliberate launch limits

- No CMS, live reader, payment, sharing, reversals, AI-generated prose, offline draw, or session list.
- Same-browser resume is via the private route; cross-device recovery requires a later account flow.
- The current server-persisted shuffle is tamper-resistant against client redraws but is not a
  user-verifiable fairness proof. Add a commitment/reveal protocol only if product research shows
  that proof materially increases trust.
