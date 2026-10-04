# Luna rewrite release runbook

Status: implementation and offline evaluation only. The owner has approved a temporary test ceiling
of **USD 1.00 per UTC day**, but no API key, paid request, or paid deployment is approved yet.

## Non-negotiable release gates

The deterministic product remains the source of truth and fallback. A rewrite may change wording,
never chart facts, Tarot card meaning, relationship scores, consent state, access state, or legal
copy.

Do not enable an external model until all of these are true:

1. The product owner explicitly approves the expected spend for this rollout.
2. `LA_LANH_GENERATION_SPEND_APPROVED=true` is set by an operator after that approval.
3. `LA_LANH_GENERATION_DAILY_TOKEN_BUDGET` is set to a positive bounded value.
4. `LA_LANH_GENERATION_DAILY_BUDGET_CENTS=100` (or lower) is set; values above 100 are rejected.
5. The OpenAI project also has a provider-side project budget/alert as defense in depth.
6. `LA_LANH_GENERATION_SURFACE_ROLLOUT` explicitly names only the approved surfaces and modes.
7. Governance, privacy, consent, and provider-retention copy have been reviewed.
8. The 670-case synthetic corpus is complete and passes the release thresholds.
9. The target surface has its own kill switch and deterministic fallback verified.

The API fails closed if generation is enabled without governance approval, spend approval, an API
key, a daily token budget, or a daily USD budget. `store: false` is required but must not be
described as Zero Data Retention.

Before any provider request is marked as sent, the worker atomically reserves a conservative token
allowance in the database for both tokens and estimated USD cost. Concurrent workers count completed
usage and in-flight reservations; retry, failure, success, cancellation, and expired leases reconcile
both reservations. If either daily limit cannot be reserved, the job stops before the provider
boundary.

When delivery may have happened but exact provider usage is unavailable, the full reservation is
counted as spent for both tokens and USD. Only failures proven to occur before provider work release
the allowance without charging it. The retired Reading worker is network-disabled; it cannot bypass
this shared budget.

Cost accounting is pinned to `gpt-6-luna-standard-2026-10-04`: Standard short-context pricing of
$0.10/1M input tokens and $0.50/1M output tokens, represented as integer nanodollars. Reverify the
[official model pricing](https://developers.openai.com/api/docs/models/gpt-6-luna) before any paid
activation and create a new pricing version if it changes. The app intentionally does not assume
Batch, Flex, Fast, cached-input, or regional pricing.

Example JSON for a non-user-visible first step: `{"daily_home":"shadow"}`. Unlisted surfaces stay
off. `shadow` and `editorial` run local gates but cannot publish to a user projection.

## Offline workflow (no provider cost)

```bash
pnpm rewrite:corpus
pnpm api:lint
pnpm api:typecheck
pnpm api:test
pnpm web:lint
pnpm web:typecheck
pnpm web:test
```

`rewrite:corpus` validates that the versioned manifest contains exactly 670 synthetic cases and
covers every registered rewrite surface. It does not call OpenAI or any other provider.

Human review results use the strict `EvaluationRecord` schema. Run the release gate only after a
complete scored results file exists:

```bash
pnpm rewrite:release -- --results /absolute/path/to/rewrite-results.json
```

Release is blocked when coverage is incomplete, any local content gate fails, first-read
comprehension is below 90%, scene/action relevance is below 85%, duplicate framing exceeds the
surface limit, or the candidate does not beat its deterministic baseline.

## Paid rollout workflow

Each step requires a fresh product-owner approval of the expected spend before changing runtime
configuration.

1. **Shadow:** generate from synthetic or explicitly consented minimal payloads; users still see
   deterministic content.
2. **Editorial:** reviewers approve candidates; no live per-open generation.
3. **10% beta:** activate one surface only after corpus and privacy gates pass.
4. **50%:** proceed only when comprehension and product feedback beat baseline.
5. **100%:** retain deterministic fallback, token budget, provider spend limit, and kill switch.

Never use Batch with live user payloads. Batch evaluation is limited to synthetic/redacted fixtures
and its files/results must be deleted after review.

## What may be observed

Allowed operational metadata:

- surface, model, prompt/schema/gate versions;
- state and redacted failure code;
- aggregate input/output token counts;
- aggregate estimated USD cost and pinned pricing version;
- attempt count and timestamps;
- non-reconstructable output fingerprint and gate receipt ID.

Never expose or log owner IDs, birth date/time/place, coordinates, Tarot question text, third-party
profile data, safe brief values, provider output text, or encrypted payloads. Content Studio is
read-only for the runtime queue and has no button that can spend money.

## Immediate stop conditions

Disable generation and keep deterministic output when any of these occurs:

- a raw personal field crosses the provider boundary;
- an unsupported chart/card/relationship claim is published;
- daily token or USD budget is reached;
- gate rejection, timeout, or refusal rises above the approved surface threshold;
- content becomes harder to understand than baseline;
- consent cannot be verified at send time;
- saved or shared content changes without a new explicit revision.

After stopping, preserve only non-sensitive operational metadata, purge pending owner-linked jobs,
document the incident, fix and rerun the complete offline gate before requesting approval again.
