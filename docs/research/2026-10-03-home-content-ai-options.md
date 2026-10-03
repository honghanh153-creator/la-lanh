# Home + content delivery audit and AI options

Date: 2026-10-03
Scope: Lá Lành web beta, Home and daily-note delivery
Audience: Vietnamese Gen Z users, including people who do not know astrology
Time horizon: next beta iteration

## Executive decision

Do not put an unrestricted LLM rewrite call directly in the critical Home request path.

Use a hybrid content compiler instead:

1. The astrology/psychology engine emits structured evidence, never final prose.
2. A deterministic planner chooses one recognisable situation and one matching action.
3. OpenAI rewrites that small brief into plain Vietnamese using Structured Outputs.
4. Local gates reject abstract, repetitive, unsafe, or ungrounded copy.
5. Approved copy is cached and served; deterministic copy remains the fallback.

For beta, generate and review the content bank offline with Batch API. Runtime AI should be a later, controlled personalization layer rather than a dependency for opening Home.

## Product Design audit

Evidence reviewed:

- `docs/reviews/home-content-audit-2026-10-03/01-home-viewport.png`
- `docs/reviews/home-content-audit-2026-10-03/02-home-lower.png`

### 1. First viewport — unhealthy

- The brand promise occupies too much of the first screen before the user reaches today's value.
- The note combines a long headline, explanatory body, three feedback actions, and a primary CTA. It is a reading task, not a scannable daily card.
- The fixed navigation overlaps the next action in the captured viewport.
- The content still uses abstract transitions such as “hai chặng khác nhau”, “sự chú ý chuyển”, and “vị trí của mình” rather than showing one concrete moment.

### 2. Lower Home — needs work

- Context, three exploration routes, Tarot, and profile unlock are presented as similarly weighted boxes. The user cannot see the single best next step.
- Three-column supporting text is too small for comfortable mobile reading.
- The page repeats the same visual grammar, so everything is prominent and nothing is prominent.

### 3. Content handoff — unhealthy

The current card often explains a psychological idea first and only then suggests a generic action. The action is not visibly caused by the situation in the note. A user can understand every sentence and still ask “so what is this for?”

## New Home information hierarchy

1. Compact greeting and one-sentence product purpose.
2. Today's card: one concrete scene, maximum two short sentences.
3. Today's try: one action that directly responds to that scene.
4. One contextual next step.
5. Secondary exploration routes below the fold.

Remove explanatory astrology and psychology from the Home card. Put source/evidence in an optional detail view.

## Plain-language content contract

Every daily item must return this schema:

```json
{
  "scene_title": "max 11 Vietnamese words",
  "scene": "one observable moment with actor, action, and context",
  "try_today": "one concrete action with a clear stopping point",
  "why_this_fits": "internal evidence only; not shown on Home",
  "confidence": "high | medium | fallback"
}
```

Release gates:

- No astrology jargon on Home.
- No diagnosis, fate, certainty, or mind-reading.
- No metaphor needed to understand the sentence.
- No vague nouns such as “nhịp”, “tín hiệu”, “năng lượng”, “cơ chế”, or “không gian” unless a literal object is intended.
- The scene must be observable in real life.
- The action must use one verb and be possible today.
- The action must respond to the scene, not merely sound healthy.
- If any gate fails, serve the approved deterministic fallback.

## Options

### A. Generate on every Home open

Pros: highest surface-level variation.
Cons: latency, variable quality, outages, difficult QA, unnecessary handling of personal data.
Verdict: do not use as the beta default.

### B. Offline AI editorial factory + CMS review — recommended

Generate candidate cards in batches from structured evidence, run automated gates, then let an editor approve or rewrite them in Content Studio. Runtime only selects approved cards.

Pros: stable quality, low latency, reviewable, low cost, no AI dependency on Home.
Cons: personalization is cluster-level until the bank grows.
Verdict: best current choice.

### C. Deterministic content DSL only

Build cards from reviewed scene and action components with controlled grammar.

Pros: predictable, cheap, private, fast.
Cons: repetition becomes visible; high editorial work.
Verdict: keep as the fallback and baseline.

### D. Hybrid runtime rewrite

Serve approved deterministic content immediately, then optionally rewrite for context with a small model and cache the result.

Pros: personalized without blocking Home.
Cons: more moving parts; still needs the same gates and evaluation set.
Verdict: phase two, after the content bank passes beta testing.

## OpenAI implementation shape

- Use the Responses API with `store: false`.
- Use Structured Outputs with a strict JSON schema; never accept free-form prose directly into UI.
- Send derived chart factors and coarse context, not name, exact address, raw birth date, or user-written background unless strictly required and separately consented.
- Keep the stable style guide at the beginning of the prompt so prompt caching can help at scale.
- Cache by `content_version + evidence_signature + context + date`, not by raw personal data.
- Enforce a short timeout and deterministic fallback.
- Log gate outcomes and anonymous content IDs, not the user's private input.

OpenAI states that API data is not used to train models unless a customer opts in. Standard abuse-monitoring logs may contain prompts and responses and are retained for up to 30 days by default, so data minimization is still required. See: https://developers.openai.com/api/docs/guides/your-data

## Gemini comparison

The user's observation that Gemini produces more natural Vietnamese is a valid product signal, but it must be tested against Lá Lành's actual evidence bundles rather than generic writing prompts.

### Production eligibility blocker

Lá Lành has been positioned for students and school communities, which can include people under 18. The current Gemini API Additional Terms state that the service must not be used as part of an application directed towards, or likely to be accessed by, people under 18. Current Google Cloud Generative AI service terms contain the same restriction.

Therefore Gemini is not an eligible production runtime for the present audience unless Lá Lành becomes a genuinely 18+ service or Google provides written clarification that the intended use is permitted. An age checkbox should not be assumed to resolve this. This is a terms/compliance blocker, not a technical limitation.

Gemini may still be evaluated internally by adult staff to understand the desired Vietnamese writing qualities, but publishing or operationalising Gemini-generated production content for the present audience should receive legal or official Google confirmation first.

Official terms: https://ai.google.dev/gemini-api/terms

Gemini supports structured JSON output, so it can use the same `DailyCard` contract and release gates as OpenAI. This means the application should depend on a provider-neutral content interface, not model-specific prose.

Candidates for a blind bake-off:

- `gemini-3.8-flash`: primary Gemini quality candidate.
- `gemini-3.5-flash-lite`: cheaper Gemini candidate.
- `gpt-6-luna`: low-cost OpenAI baseline.
- `gpt-6.1-sol`: higher-quality OpenAI control.
- deterministic content DSL: mandatory non-AI baseline.

Do not let the models review their own writing. Run the same local gates first, then have Vietnamese readers score anonymised outputs without model names.

Google's paid Gemini service does not use prompts or responses to improve its products. Google still logs prompts and responses for abuse monitoring for a limited period; workloads that require guaranteed zero data retention should use Vertex AI or an approved ZDR configuration. Do not use Gemini's free tier with private birth-chart content because the pricing page states free-tier content may be used to improve Google's products.

Gemini sources:

- Pricing: https://ai.google.dev/gemini-api/docs/pricing
- Structured output: https://ai.google.dev/gemini-api/docs/structured-output
- Data retention: https://ai.google.dev/gemini-api/docs/zdr

## Cost estimate

Assumption per daily rewrite: 1,500 input tokens and 150 output tokens. This is intentionally conservative for a short structured card.

Current standard short-context prices used here:

- `gpt-6-luna`: $0.10 / 1M input tokens, $0.50 / 1M output tokens.
- `gpt-6.1-sol`: $2.00 / 1M input tokens, $10.00 / 1M output tokens.

| Monthly traffic | Requests | Luna, one pass | Sol, one pass |
|---|---:|---:|---:|
| 100 DAU | 3,000 | about $0.68 | about $13.50 |
| 1,000 DAU | 30,000 | about $6.75 | about $135.00 |

Allow 2–3× for retries, evaluation samples, or a second AI review pass. Batch generation costs 50% less than synchronous calls and completes within 24 hours, which is why it fits the offline editorial workflow.

Pricing source: https://developers.openai.com/api/docs/pricing
Batch source: https://developers.openai.com/api/docs/guides/batch
Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs

Using the same 1,500-input/150-output assumption, current Gemini paid-tier estimates are:

| Monthly traffic | Gemini 3.5 Flash-Lite | Gemini 3.8 Flash |
|---|---:|---:|
| 100 DAU / 3,000 requests | about $2.48 | about $5.06 |
| 1,000 DAU / 30,000 requests | about $24.75 | about $50.63 |

Gemini Batch is 50% cheaper. At beta scale, the difference between Luna and Gemini Flash is small enough that comprehension quality should decide the writer model.

## Provider-neutral bake-off

Use one versioned prompt and one schema for every candidate. Test at least 150 cases covering:

- known and unknown birth time,
- all five Home contexts,
- weak, strong, and conflicting evidence,
- repeated themes across consecutive days,
- Tarot and astrology copy separately,
- sensitive relationship and self-image scenarios.

Blind human scoring, 1–5:

1. Understood on the first read.
2. Sounds like natural contemporary Vietnamese.
3. Describes a concrete, recognisable moment.
4. The action clearly follows from the moment.
5. Specific without pretending to know the user.
6. Worth saving, sharing, or returning for.

Hard failures:

- Adds a claim not present in the evidence bundle.
- Uses astrology jargon on Home.
- Sounds diagnostic, deterministic, or manipulative.
- Repeats abstract filler or the same sentence frame.
- Fails the JSON schema or exceeds the UI word budget.

Decision rule: select the lowest-cost model that wins comprehension and natural-language scores without increasing hard failures. It is acceptable for Gemini to be the writer and for all quality gates to remain local; a second LLM reviewer should be added only if it produces a measured uplift.

Eligibility rule precedes the quality rule: a model that fails audience, privacy, or contractual requirements cannot win the production bake-off even if its prose scores higher.

## Evaluation before release

Create a fixed test set of at least:

- 30 birth-chart evidence bundles,
- 5 contexts per bundle,
- 3 user-data depths,
- difficult cases: conflicting factors, unknown birth time, weak evidence, and repeated daily themes.

Score each candidate on:

1. “I understood it on first read.”
2. “I can picture the situation.”
3. “The action clearly follows from the situation.”
4. “It feels specific without pretending to know me.”
5. “I would keep reading or share it.”

Do not ship a prompt because five examples look good. Ship a version only when it beats the deterministic baseline on the fixed evaluation set and passes all content gates.

## Recommended next build slice

1. Rebuild Home hierarchy and remove competing modules from the first viewport.
2. Introduce the structured `DailyCard` contract.
3. Build deterministic scene/action baseline and local gate suite.
4. Add offline Luna batch generation behind a feature flag.
5. Add Content Studio approval and versioning.
6. Run Vietnamese comprehension testing before enabling any runtime rewrite.
