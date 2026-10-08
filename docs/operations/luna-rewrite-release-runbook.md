# Luna rewrite release runbook

## Daily direct update, 2026-10-07

The latest Daily branch uses `daily-direct-meaning-v4`, `deterministic-vi-v10`,
`surface-rewrite-v3`, `daily-rewrite-gates/v2`, and `meaning-gate-vi-v2`.
The server-owned `SemanticBlueprint.daily_meaning` explains the core meaning and takeaway,
marks the scene as illustrative, and supplies scene/action anchors. The privacy allowlist must
reject identifiers or extra fields inside this brief as well as at the top level.

Before rollout, verify the current Daily fallback and generated rewrite against the same
direct contract. Regression cases include the exact opaque group-pressure paragraph, advice
for the wrong situation, advice inside a scene, certain predictions, long sentences, and an
action asking the reader to act before a choice the scene says was already made.

Deterministic current projections can repair to a new Daily blueprint in the same owner and plan
scope using the existing activation CAS. Do not mutate frozen shares or historical revisions.
Existing generated projections keep their available-update activation flow. If an old generated
active note still has bad copy, explicitly review/activate its replacement before rollout.

This local update makes no paid provider call and grants no new spend approval. Keep generation
and the worker disabled for local QA. Offline corpus success is not a scored Luna trial or a
human comprehension study. Review `docs/plans/2026-10-07-direct-daily-meaning-brief-plan.md`
and its QA receipt before deployment; deployment remains a separate action.

Status: implementation and offline evaluation complete. On 2026-10-04 the owner approved one
privacy-safe paid probe under a temporary ceiling of **USD 1.00 per UTC day**. This approval does
not authorize a prepaid-credit purchase, a higher limit, or a user-visible rollout.

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

The API may enqueue consented work without receiving the provider key. The separate rewrite worker
fails closed unless generation and worker execution are both enabled, governance and spend approval
are present, an API key is mounted, and both daily budgets are positive. The API container must not
mount the provider key. `store: false` is required but must not be described as Zero Data Retention.

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

Before any user payload or production worker is enabled, run exactly one synthetic probe from a
trusted machine. Enter the key into a mode-`0600` file without putting it in chat, shell arguments,
Git, or logs, then run:

```bash
cd apps/api
.venv/bin/python -m scripts.run_paid_rewrite_probe \
  --api-key-file "$HOME/.config/la-lanh/openai_api_key" \
  --confirm-max-usd 1.00
```

The probe sends no birth data, coordinates, profile identifiers, Tarot question, relationship data,
or production prose. It uses `store: false`, prints no generated prose, and reports only gate state,
aggregate tokens, pinned-price cost and explicit local/provider retention fields. The local UTC-day
receipt prevents accidental reruns on the trusted operator machine; the production worker's shared
database ledger is the cross-process USD cap. Stop if OpenAI requires a credit purchase; that
purchase needs separate owner approval.

1. **Shadow:** generate from synthetic or explicitly consented minimal payloads; users still see
   deterministic content.
2. **Editorial:** reviewers approve candidates; no live per-open generation.
3. **10% beta:** activate one surface only after corpus and privacy gates pass.
4. **50%:** proceed only when comprehension and product feedback beat baseline.
5. **100%:** retain deterministic fallback, token budget, provider spend limit, and kill switch.

## Hetzner worker activation

The production Compose stack keeps `rewrite-worker` behind the `generation` profile. `deploy.sh`
enables that profile only when `LA_LANH_GENERATION_ENABLED=true` appears exactly in `app.env`. At
that point `/opt/la-lanh/secrets/openai_api_key` must exist, be non-empty, and use the same restricted
ownership/mode as the other runtime secrets. Only `rewrite-worker` mounts it; `app` and `caddy` do
not.

For the first deployment use only:

```text
LA_LANH_GENERATION_ENABLED=true
LA_LANH_GENERATION_PROVIDER=openai
LA_LANH_GENERATION_GOVERNANCE_APPROVED=true
LA_LANH_GENERATION_SPEND_APPROVED=true
LA_LANH_GENERATION_DAILY_TOKEN_BUDGET=10000
LA_LANH_GENERATION_DAILY_BUDGET_CENTS=100
LA_LANH_GENERATION_SURFACE_ROLLOUT={"daily_home":"shadow"}
```

Compose sets `LA_LANH_GENERATION_WORKER_ENABLED=true` only inside the isolated worker; this setting
does not belong in the shared `app.env`. Shadow mode runs the local gate but cannot replace the
deterministic user-visible projection.

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
