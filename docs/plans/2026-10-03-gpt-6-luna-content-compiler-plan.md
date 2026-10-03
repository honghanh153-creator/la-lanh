# GPT-6 Luna content compiler plan

Date: 2026-10-03
Goal: improve Vietnamese comprehension without allowing a language model to invent chart meaning or block Home availability.

## Current-state findings

The repository already contains most of the safe execution shell:

- deterministic plan and renderer,
- explicit external-generation authorization,
- an asynchronous durable generation worker,
- OpenAI Responses API with `store: false`,
- structured output,
- local evidence, influence, editorial, meaning, and privacy gates,
- deterministic content that stays active when generation fails,
- revision history and activation rather than destructive overwrite.

The current integration is not ready to enable:

1. `app/config.py` pins `gpt-5.4-mini-2026-03-17`, not `gpt-6-luna`.
2. The provider schema asks for generic chart-synthesis sections up to 500–700 characters, which is incompatible with a scannable Home card.
3. The OpenAI parser constructs a `ReadingCandidate` without a `semantic_blueprint`, while the meaning gate requires one. Generated candidates therefore cannot pass the current publication contract.
4. The model receives chart factors but not the deterministic scene/action blueprint that must constrain the rewrite.
5. The present pipeline treats generation as an optional full reading update. It does not yet distinguish a short Home rewrite from a detailed reading.

## Product rule

Luna is a Vietnamese copy editor, not an astrologer and not a decision engine.

The server must decide:

- which factors are relevant,
- what claim is allowed,
- which daily situation is being described,
- which action is compatible with that situation,
- which words and claims are forbidden.

Luna may only make that closed brief shorter, clearer, and more natural.

## Personalisation input contract

Luna may receive these derived or explicitly selected fields:

- allowlisted natal/transit factor labels chosen by the planner,
- reading depth (`date_only`, `full_chart`, or `full_chart_transit`),
- the user's selected Home context,
- the user's current mood when they choose to provide it,
- prior anonymous feedback such as `hit`, `miss`, or preferred tone,
- the server-owned scene and action meanings.

Luna must not receive:

- name, email, phone number, account ID, or device ID,
- raw date of birth, exact birth time, exact birthplace, coordinates, or address,
- another person's chart or personal data without separate applicable consent,
- free-text diary, chat, or relationship history by default,
- raw feedback text when a bounded category is sufficient.

The safe payload should use transient labels such as `factor_1`, coarse context enums, and bounded preference enums. Personalisation means selecting and phrasing relevant evidence, not sending more identity data.

## Target pipeline

```text
Natal/transit engine
    -> ReadingPlanner
    -> deterministic SemanticBlueprint
    -> safe provider payload
    -> GPT-6 Luna plain-Vietnamese rewrite
    -> strict DailyCard JSON
    -> reconstruct candidate with the original blueprint keys/evidence
    -> local gates
    -> approved revision/cache
    -> Home

Any failure -> deterministic approved card
```

## Phase 1 — Define a Home-specific contract

Add a provider-neutral `DailyCardDraft` contract:

```json
{
  "title": "8–11 Vietnamese words",
  "scene": "18–36 words; one observable situation",
  "action": "10–24 words; one action possible today",
  "tone": "warm_direct",
  "confidence": "high | medium"
}
```

Do not reuse the long-form `hook/thesis/manifestation/transit/micro_action` budget for Home. Map the approved daily draft into the existing public projection only at one adapter boundary until the public API can be versioned.

Acceptance criteria:

- Home never receives more than 70 words of core content.
- No astrology terms appear in title, scene, or action.
- Scene and action are separate fields.
- The original evidence and semantic keys remain server-owned.

## Phase 2 — Make Luna a constrained rewriter

Update `apps/api/app/infrastructure/generation/openai.py`:

1. Add a daily-specific JSON schema.
2. Set the production model allowlist to `gpt-6-luna`.
3. Send only:
   - purpose and context,
   - server-selected scene and action meaning,
   - allowed/forbidden language,
   - anonymised evidence labels,
   - word budgets and examples of accepted Vietnamese.
4. Do not send name, raw birth date, exact birthplace, longitude, orb, or free-text background.
5. Require the model to preserve meaning, not add an interpretation.
6. Set a small output limit appropriate to one JSON card.

The parser must rebuild the candidate with the original `SemanticBlueprint` identifiers and evidence references. Luna may replace only the prose values. It must not generate `scene_key`, `action_key`, `mechanism_key`, or evidence IDs.

Acceptance criteria:

- An AI candidate can pass the meaning gate only when its server-owned keys match the plan.
- Changing prose cannot change evidence attribution.
- Refusal, timeout, invalid JSON, or gate failure never removes the deterministic card.

## Phase 3 — Strengthen the gates

Keep existing gates and add Home-specific checks:

- title <= 11 words,
- scene has a concrete actor/context/action marker,
- action starts with one observable verb,
- action refers to at least one concrete noun from the scene,
- no opaque vocabulary or translated-sounding filler,
- no second-person certainty or mind-reading,
- no diagnosis, fate, urgency, dependency, or professional advice,
- no duplicate sentence frame in the recent content window,
- no unsupported chart claim,
- no personal data in output.

Add an explicit failure code for scene/action semantic disconnection rather than relying only on keyword presence.

## Phase 4 — Build the evaluation corpus before runtime

Create at least 150 fixed cases:

- 30 chart/evidence bundles,
- five Home contexts,
- exact and unknown birth time,
- natal-only and natal+transit,
- weak and conflicting evidence,
- repeated themes on adjacent dates.

For each case, retain:

- deterministic baseline,
- Luna output,
- gate result and failure codes,
- editor score,
- final approved version.

Human scoring, 1–5:

1. Understandable on the first read.
2. Natural contemporary Vietnamese.
3. A recognisable situation rather than an explanation.
4. An action clearly caused by that situation.
5. Specific without pretending to know the user.
6. Worth returning to, saving, or sharing.

Release thresholds:

- >= 90% understandability score of 4 or 5,
- >= 85% scene/action relevance score of 4 or 5,
- zero privacy, unsupported-claim, diagnosis, fate, or urgency failures,
- < 5% duplicate framing across a seven-day sample,
- measurable improvement over the deterministic baseline.

## Phase 5 — Use Content Studio as an editorial factory

Extend Content Studio with:

- source blueprint and evidence preview,
- deterministic/Luna side-by-side comparison,
- gate results by field,
- approve, edit, reject, and regenerate actions,
- prompt/model/content version,
- reviewer and reason,
- rollback to a prior release,
- filters for abstract language, repeated framing, and weak scene/action linkage.

Initially, generate content in batches and publish only editor-approved versions. Do not enable live per-user rewriting yet.

## Phase 6 — Safe runtime rollout

1. **Shadow:** Luna generates candidates, but users see deterministic content.
2. **Editorial:** approved Luna content enters the shared content bank.
3. **10% beta:** runtime-generated content is shown only after all gates pass.
4. **50%:** proceed only when comprehension and feedback beat baseline.
5. **100%:** retain the kill switch, budget cap, deterministic fallback, and rollback.

Runtime behavior:

- Home returns deterministic content immediately.
- The worker generates asynchronously.
- An approved candidate becomes an available revision; it must not silently rewrite a note already saved or shared.
- Cache/replay by plan, date, context, model, prompt version, and content version.
- A provider outage must be invisible to the user.

## Phase 7 — Observability and cost controls

Track without storing raw private input:

- request and accepted-candidate counts,
- gate rejection rate by failure code,
- latency and timeout rate,
- input/output tokens and cost,
- activation rate,
- “trúng/chưa trúng” feedback,
- save/share/open-detail rate,
- content fingerprint diversity.

Set:

- a project-level API spend limit,
- a per-day generation budget,
- one safe attempt plus one retry only when delivery is known not to have occurred,
- an automatic kill switch when rejection, timeout, or cost thresholds are exceeded.

At 100 DAU and one 1,500-input/150-output Luna call per daily note, the model cost estimate is about $0.68/month before retries and evaluation overhead. Budget $3/month for beta rather than optimizing prematurely.

## Definition of done

- `gpt-6-luna` is allowlisted and configured through secrets, never committed.
- Daily output uses the short structured contract.
- Server-owned semantic blueprint and evidence survive generation unchanged.
- All existing security/privacy/evidence gates pass.
- New comprehension and scene/action gates pass.
- 150-case corpus meets the release thresholds.
- Deterministic content remains the immediate fallback.
- Content Studio supports review, approval, versioning, and rollback.
- Shadow-mode telemetry shows no private fields sent to the provider.
- Browser QA confirms Home hierarchy, text size, wrapping, loading, offline, and failure states.
