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
- B2-1 (`tarot-question-rules-v2`, `docs/plans/2026-10-17-b2-1-tarot-question-frame-task.md`):
  - Intake order: too short or vague (under 3 words, or no question word and no verb) → high stakes →
    another person's mind → certainty.
  - "Khi nào / bao giờ" about one's own action is accepted and answered as what to have ready first,
    with one line saying no date is predicted. Timing about an event or another person is still
    refused as certainty.
  - Each accepted question gets a `QuestionFrame` of closed labels: form, scored topic, and an optional
    action from the 30-label table. It is computed once at intake and stored in the encrypted session
    payload, then replayed at render. It is never logged, returned by the API or sent to a provider.
  - Sessions started before B2-1 have no frame and render as before.
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
- B2-2 (`docs/plans/2026-10-17-b2-2-tarot-roles-task.md`), for sessions with a stored
  `QuestionFrame`:
  - Each position reads by its role: core, tension, option or resource.
  - Only the step role (focus, next, alternative, criterion, opening) carries the small action;
    other positions return `small_action: null`.
  - Readings drop the "Ý chính của lá" / "Thử nhé:" / "Ví dụ:" prefixes.
  - The Tarot review has no minimum word count.
  - The `role_fit` and `no_decision_or_prediction` gates apply (`tarot-gates-v5`).
  - Earlier sessions render with the legacy renderer.
- B2-3 (`docs/plans/2026-10-18-b2-3-tarot-stance-task.md`), framed sessions only:
  - Yes/no questions, and choices whose A/B map to two closed action labels, get a `stance`. It
    is computed from per-card lean labels and role weights: lean to try / consider more first /
    unclear (both ways), with 1–2 reasons citing a position and its card.
  - Unsplittable choices, or choices without option roles, get "what to clarify before choosing".
  - The summary links every role with conjunctions; the headline is built from form, lean (or
    action/topic) and the focal card.
  - Gates: `stance_consistent` and `summary_links_cards`.
  - Readings without a stance omit the key.
- B2-4a (`docs/plans/2026-10-18-b2-4-tarot-variety-roast-task.md`), framed sessions only:
  - Each role has three frames per voice register; the headline has three frames per key. A
    session picks its frames, its lead offset and its headline frame once, when it starts, from
    `HMAC(K[1], guest ‖ "tarot" ‖ tarot-variant-catalog-v1)` and the guest's session position,
    taken from a monotonic per-guest cursor (`tarot_variant_cursors`) in the transaction that
    creates the session; deleting or expiring readings never rewinds it. Only the indices are
    stored, in the encrypted payload; rendering replays them. Only an absent record falls back to
    index 0; a present record must decode strictly (all six fields, supported version, strict
    integers) or the render fails.
  - Every position starts with a lead chosen by the question form (5 per form, none repeated in a
    reading), so two questions over the same card and role read differently (T4).
  - Roast has its own role frames, headlines, stance conclusions and summary conjunctions, mapped
    one to one by combination code. Energy and self-care Roast keeps the direct frames with the
    gentle opener and tails. Sensitive questions still render the default voice.
  - Framed readings record `tarot-renderer-v7`, `tarot-knowledge-v5`, `tarot-gates-v5`; sessions
    without a frame keep v6 / v4 / v4 byte for byte. Provenance version fields have no defaults.
- B2-4b (`docs/plans/2026-10-18-b2-4b-tarot-provenance-task.md`), framed sessions only:
  - The Luna payload uses meaning brief v3: closed labels (topic, intent, spread map, goal codes, stance
    kind/level/action/options) and, on every position, the catalog codes its texts resolve from. The
    reducer builds the texts from those codes and refuses any payload with a string it cannot trace.
    Stance conclusions and reasons stay local. Sessions without a frame keep brief v2.
  - `tarot/checklist.py` holds the machine items of the psychology checklist (headline without advice,
    no coercion, the reading and its summary end on the step); `tarot:audit` gates them.
- The launch voice is fixed to `playful_grounded`: current, direct, lightly playful, and never
  mystical filler. Voice selection is deliberately not another onboarding step.
- 2026-10-11 owner decision: `POST /v1/tarot/sessions` accepts optional `voice: "default" | "roast"`
  (default `"default"` → `playful_grounded`). `roast` frames the headline, summary, meaning and
  small action without changing cards, positions, scenes, reflections or action steps (B2-4: for
  framed sessions Roast also has its own role frames, headlines, stance conclusions and links;
  the headline states the stance in every voice). Energy and
  self-care readings get gentle frames; sensitive questions (health, safety, crisis, grief, legal or
  money trouble) store and render `playful_grounded`. Roast readings are not queued for AI rewrite.
  See `docs/foundation/la-lanh-plain-vietnamese-content-standard.md`.

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

Since B2-4 it also runs the whole question bank × every map × all four voices with per-session
variants (stance distribution, headline duplicates per voice < 10%, generic copy = 0), the T4
measure (same card × role × topic across question pairs: ≥ 80% per session and ≥ 80% from the
question alone), and worst-length draws for every frame, lead and headline index. Since B2-4b it also
traces every direct-voice provider payload to closed labels and catalog codes (AC06) and gates the machine
items of the psychology checklist, reporting the rest for the owner (AC14).

Required release checks also include API contract generation, backend unit/API tests, frontend
type/lint/tests, mobile viewport visual inspection, keyboard selection, refresh/resume, delete,
question reframe, CSRF rejection, owner isolation, and expiry cleanup.

## Deliberate launch limits

- No CMS, live reader, payment, sharing, reversals, AI-generated prose, offline draw, or session list.
- Same-browser resume is via the private route; cross-device recovery requires a later account flow.
- The current server-persisted shuffle is tamper-resistant against client redraws but is not a
  user-verifiable fairness proof. Add a commitment/reveal protocol only if product research shows
  that proof materially increases trust.
