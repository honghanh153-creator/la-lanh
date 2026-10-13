# Luna rewrite release runbook

## Lá's companion line, 2026-10-13 — local only

`daily_home` now has a fourth field, `companion`: the line Lá (the sprout companion) says next to
the card. Chain: `surface-rewrite-v5` → schema `daily-rewrite/v2` → `daily-rewrite-gates/v4`
(report `daily-home-rewrite-gates/v4`); every bump changes the cache key, so nothing generated
under v4 is reused.

- Luna receives only `companion_meaning`, the editorial brief from the content matrix
  (`apps/api/app/domains/readings/companion.py`), never the authored sentence.
- The gate checks 4–14 words, no astrology terms or filler, no claim to know the reader, no fate
  wording, no statement of what another person thinks or wants, no certainty, and no repeat of the
  title or action. The Meaning Gate runs the same rules on the authored line of every
  deterministic card. The full-year test confirms every authored line passes.
- Deterministic cards do not store a line. The read model adds the authored direct or roast line
  from the catalog. Roast readers of a Luna card get the voiced deterministic baseline with its
  roast line, never a mix. Lá's line alone never swaps a Luna card for the baseline.
- Budget: the 40-case pilot's worst-case reservation is **USD 0.029799**, under the 3-cent staging
  day, with about 0.7% margin. A longer prompt or brief must be re-checked with
  `pnpm rewrite:pilot generate --dry-run` before it ships.
- Human scoring of the pilot sample now also covers "Lời của Lá"; the review page shows it.

No paid call was made for this update.

## Daily v7 contract update, 2026-10-13 — local only

Daily now uses the v7 card (two-sentence thesis, scene opened by a context clause). The rewrite
chain is `surface-rewrite-v4` → `daily-rewrite-gates/v3` (report `daily-home-rewrite-gates/v3`).
Both bumps change the rewrite cache key, so nothing generated under v3/v2 is reused. Luna still
rewrites only title/scene/action; the projector keeps the deterministic thesis. The rewrite gate
additionally rejects a dropped context clause, a reintroduced "Ví dụ …" fragment and a verbatim
repeat of the takeaway. Roast ("Cà khịa") readers never see a half-roasted Luna card: the roast is
served from the deterministic baseline of the same plan, or the Luna text stays fully direct.
No paid call was made for this update.

## Local security/content update, 2026-10-09 — not deployed

- Current Tarot chain: `tarot-renderer-v4` → `tarot-meaning-brief-v1` → `gpt-6-luna-tarot-v3` → `tarot-rewrite-gates/v3`. Only new readings use the new local renderer; no bulk legacy rewrite or additional paid evaluation is authorised here.
- Rebuild both API and worker from the same immutable image. The worker now also mounts the managed `guest_hash_key`, because its production Settings contract requires it. Keep all secret files read-only and never mount `openai_api_key` into the API or frontend. This expands the worker's trusted secret set; do not bypass the API's production validator to avoid the mount.
- Before launch, test Settings with fake files matching Compose mounts. Confirm actual worker startup/health on the target with generation disabled first. Local compose text checks alone are not a live-container proof.
- Reservation uses UTC. If lock acquisition or the send marker crosses into the next day, fail the job without sending and retain its debit. The ledger is conservative, not a provider invoice or protection against an unrelated caller using the same key.
- Isolated PostgreSQL tests now cover actual connection termination and a killed subprocess at the send boundary. They do not undo data already transmitted before consent withdrawal. Verify this limitation is reflected in privacy copy.
- Reject legacy Tarot jobs without a meaning brief before transport; don't replay or migrate them into new paid jobs automatically. Rejected AI keeps its valid local baseline. Rejected first local rendering locks the drawn cards but exposes no draft and creates no rewrite job.
- Keep generation/worker disabled for local browser QA. Run all six topic banks through `tarot:audit`, read a separate synthetic sample corpus, and obtain real reader acceptance. Passing schemas, keyword checks or a ten-persona simulation is not evidence that ten real users understood the product.
- Remaining release gates: completed review receipt, approved content sample acceptance, live deployment verification, native-specific verification if publishing the app, and disposition of retained security findings. The failed deep scan is not a certificate of system-wide security.

## Pilot daily_home config (proposed, not applied)

Owner decision 2026-10-13 (Issue #7, "Kế hoạch release beta"): Luna only for the Home Daily note
(`daily_home`), at most 20 sessions that opted in themselves, provider project cap USD 1/month,
app-side reservation cap 90 cents/month in total. Staging first, then production. Nothing below
is applied; no secret appears here. `tests/scripts/test_pilot_config_doc.py` loads both blocks
into the real `Settings` validators with fake secret files, so a value that the code would reject
fails CI.

How the code reads these values:

- `LA_LANH_GENERATION_SURFACE_ROLLOUT` must name `daily_home` only. The personal opt-in in `Mình`
  is offered only when a personal surface is in a user-visible mode (`beta_10`, `beta_50` or
  `full`; `guest_sessions.py`). `shadow`/`editorial` hide the opt-in, so with no consenting
  session nothing is ever enqueued: shadow is not a useful pilot step for personal content.
  `beta_10` publishes only ~10% of artifacts, so 20 testers would rarely see Luna. Use `full`.
  Even then a Luna note is only an *available update*; the tester activates it explicitly.
- Unlisted surfaces stay `off`, so `reveal`/`natal`/`transit_insight`/`tarot` are not enqueued
  even though the same personal consent receipt covers them. Do not add them without a new
  owner decision and copy review.
- One Daily job reserves ~5.3k–6.2k tokens and 0.061–0.070 cents before the provider call
  (conservative UTF-8 byte count of the brief + prompt + schema + 512, output cap 220; measured on
  synthetic v7 cards 2026-10-13). Observed real cost is ~0.01 cent per job.
  `DAILY_BUDGET_CENTS=3` therefore admits ~42 jobs/UTC day; `DAILY_TOKEN_BUDGET=300000` (~48 jobs)
  keeps the cent cap binding. The older `100000` example would stop at ~16 jobs/day, fewer than
  20 testers. Each context lens is its own job, so heavy lens switching drains the day sooner.
- Each database keeps its own monthly ledger. Staging and production use the same key and
  provider project, so their monthly caps must add up to at most 90: staging 10 + production 80.
  Use production 90 only if staging generation stays off for that whole UTC month.
- `PILOT_USER_LIMIT=20` counts active opted-in sessions, not people.
- Worker-only settings (`LA_LANH_GENERATION_WORKER_ENABLED`, the key file path) are set by
  Compose inside the worker and never belong in `app.env`/`generation.env`.

Staging (`infra/hetzner/staging/generation.env`, git-ignored, used only with
`STAGING_GENERATION=on ./up.sh`; key at `/opt/la-lanh/staging/secrets/openai_api_key`, owner
65532, mode 0600, mounted only into `staging-rewrite-worker`):

```text pilot-staging
LA_LANH_GENERATION_ENABLED=true
LA_LANH_GENERATION_PROVIDER=openai
LA_LANH_GENERATION_GOVERNANCE_APPROVED=true
LA_LANH_GENERATION_SPEND_APPROVED=true
LA_LANH_GENERATION_SURFACE_ROLLOUT={"daily_home":"full"}
LA_LANH_GENERATION_MONTHLY_BUDGET_CENTS=10
LA_LANH_GENERATION_DAILY_BUDGET_CENTS=3
LA_LANH_GENERATION_DAILY_TOKEN_BUDGET=300000
LA_LANH_GENERATION_PILOT_USER_LIMIT=3
LA_LANH_GENERATION_OPENAI_PROJECT_ID=proj_eiNVxorNxWcueLgvBnYOU16T
```

Production (`infra/hetzner/app.env` on the VPS; `deploy.sh` then starts `rewrite-worker` through
the `generation` profile and requires `/opt/la-lanh/secrets/openai_api_key`):

```text pilot-production
LA_LANH_GENERATION_ENABLED=true
LA_LANH_GENERATION_PROVIDER=openai
LA_LANH_GENERATION_GOVERNANCE_APPROVED=true
LA_LANH_GENERATION_SPEND_APPROVED=true
LA_LANH_GENERATION_SURFACE_ROLLOUT={"daily_home":"full"}
LA_LANH_GENERATION_MONTHLY_BUDGET_CENTS=80
LA_LANH_GENERATION_DAILY_BUDGET_CENTS=3
LA_LANH_GENERATION_DAILY_TOKEN_BUDGET=300000
LA_LANH_GENERATION_PILOT_USER_LIMIT=20
LA_LANH_GENERATION_OPENAI_PROJECT_ID=proj_eiNVxorNxWcueLgvBnYOU16T
```

`SPEND_APPROVED=true` and `GOVERNANCE_APPROVED=true` may only be written by the operator after the
owner's explicit approval of this spend and of the privacy items below; leaving either `false`
keeps the worker from starting (`Settings` validation). Kill switch: set
`LA_LANH_GENERATION_ENABLED=false` (production: redeploy; staging: rerun `up.sh` with
`STAGING_GENERATION=off`, which also removes the staging worker). Deterministic notes stay as the
fallback.

Still blocking activation (not done here): owner approval of spend and governance, DPA
acceptance and cross-border transfer impact assessment (Law 91/2025/QH15, Decree 356/2025/NĐ-CP),
privacy copy update, human scoring of the ~40-case `daily_home` sample, secret copy to the VPS,
live worker health check and one supervised end-to-end run on staging.

## daily_home pilot evaluation (~40 human-scored cases)

`scripts/daily_rewrite_pilot_eval.py` (`pnpm rewrite:pilot -- <command>`). Everything is
synthetic: the versioned catalog `apps/api/scripts/fixtures/daily_home_pilot_cases.json`
(`daily-home-cases-v1`) maps the corpus's 75 `daily_home-NNNN` ids to generated charts/dates
(63 exact with transits, 12 date-only); no real person is described.

1. `select --out selection.json` picks 40 cases (`daily-home-pilot-sample-v1`) covering all 15
   Daily issues (≥2 each), all six lenses, every scene context, both chart kinds, and roast
   cards for relationships/communication/work plus the gentle energy/self-care frame. Offline.
2. `generate --selection selection.json --out cases.jsonl --dry-run` renders each baseline,
   compiles the exact `daily_home` request (`surface-rewrite-v4`, `daily-rewrite-gates/v3`),
   runs the provider privacy allowlist and prints the worst-case ledger reservation
   (≈ USD 0.028 for the 40 cases). Zero network calls (tested with sockets disabled).
3. Paid step, later and only after the owner approves it: inside the staging worker container,
   which already holds the validated worker Settings and the mounted key, e.g.
   `docker compose -f compose.staging.yaml --profile generation run --rm --no-deps -v /opt/la-lanh/staging/eval:/eval staging-rewrite-worker python -m scripts.daily_rewrite_pilot_eval generate --selection /eval/selection.json --out /eval/cases.jsonl --paid --confirm-max-usd 0.03`.
   It refuses unless worker Settings validate, generation/governance/spend approval are true,
   `daily_home` is in the rollout, the database is PostgreSQL, and `--confirm-max-usd` (≤ 0.90)
   covers the worst case. Before every send it debits the same anonymous day/month ledger as the
   worker (`reserve_standalone_budget`); a refused reservation stops the run and marks the rest
   `budget_blocked`. The proposed staging day cap of 3 cents covers one 40-case run only on a
   day without other staging jobs. Output is gated by the production `DailyRewriteProjector`
   (`publish=False`); nothing is published. The key is never read or printed by the script.
   `cases.jsonl` is written mode 0600 and holds only synthetic prose; delete it after review.
4. `html --cases cases.jsonl --out review.html` writes a self-contained page (no network, CSP,
   noindex). A/B order is blinded per case. The reviewer scores six 1–5 dimensions for both
   versions and marks Đạt/Không đạt, then exports `rewrite-results.json` (strict
   `EvaluationRecord` array; a human "Không đạt" becomes `gate_passed=false` with
   `human_rejected`) plus review notes.
5. `pnpm rewrite:release -- --results rewrite-results.json --selection selection.json` applies
   the unchanged release thresholds (comprehension ≥ 90%, relevance ≥ 85%, duplicate frames
   < 5%, zero gate failures, candidate mean > baseline mean) to the declared sample. This is a
   **pilot sample gate**, reported as such; it does not replace the full 670-case release gate.

## Paid pilot update, 2026-10-08

This section supersedes the older **USD 1/day** examples below for the current pilot. The requested
ceiling is **USD 1/month**. The first save was rejected; the operator did not retry it. After the owner
completed their step, a read-only observation verified the project page's `$0.00 / $1.00` enforced
limit and "Requests will start to fail" message. Funding is verified at USD 5 and auto-reload off. One synthetic probe
passed at USD 0.00010250. Do not rerun it or treat funding as permission to increase consumption.

Before starting the new worker, apply migration `20261008_0029` with generation off and verify RLS
and denied Supabase browser-role grants. Test concurrent monthly reservations on a disposable
PostgreSQL database. The anonymous monthly table survives owner deletion and code rollback.
Never downgrade/delete this table to refill a budget. When rolling back to a pre-monthly-cap image,
disable generation first; the old worker cannot enforce the new policy.

Required new settings, in addition to governance/spend approval and daily token bounds:

```text
LA_LANH_GENERATION_MONTHLY_BUDGET_CENTS=90
LA_LANH_GENERATION_DAILY_BUDGET_CENTS=3
LA_LANH_GENERATION_DAILY_TOKEN_BUDGET=100000
LA_LANH_GENERATION_PILOT_USER_LIMIT=20
LA_LANH_GENERATION_OPENAI_PROJECT_ID=proj_eiNVxorNxWcueLgvBnYOU16T
```

These are proposed, **not applied**. The 90-cent reservation cap leaves room for probes/evaluation
outside the production ledger. It is a conservative debit, not a real-time invoice. Uncertain
requests and deleted jobs cannot refund it. Reserve any standalone paid evaluation separately
within the same USD 1/month total. Provider-side enforced limits can lag; do not promise that this
protects unrelated callers or other keys/projects.

Keep the existing key, and only copy it to `/opt/la-lanh/secrets/openai_api_key` after destination
confirmation. Mount it only into `rewrite-worker`, never `app` or the frontend. Use standard service
tier, no tools, no regional/fast premium, and `store:false`.

`Mình` offers personal external-rewrite consent only when a personal user-visible pilot is
configured. It stays hidden for shadow/editorial-only runs. Each tester must opt in independently;
initial birth consent is not external-provider consent. Withdrawals stop subsequent requests.
The cap is 20 **active opted-in sessions**, not verified people or lifetime registrations. Radar and
Matching remain off unless their separate subject consent and content review gates pass.

The 670-case manifest is not scored output. Missing human review, processor/cross-border evidence,
secret-destination confirmation, or paid E2E proof blocks user-visible activation. See
`docs/plans/2026-10-08-paid-rewrite-pilot-activation.md` for current status and sources.

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

Historical status: implementation and offline evaluation complete. On 2026-10-04 the owner approved one
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

Example for an explicitly approved pilot, not permission to enable billing or generation:

```text
LA_LANH_GENERATION_ENABLED=true
LA_LANH_GENERATION_PROVIDER=openai
LA_LANH_GENERATION_GOVERNANCE_APPROVED=true
LA_LANH_GENERATION_SPEND_APPROVED=true
LA_LANH_GENERATION_DAILY_TOKEN_BUDGET=10000
LA_LANH_GENERATION_DAILY_BUDGET_CENTS=3
LA_LANH_GENERATION_MONTHLY_BUDGET_CENTS=90
LA_LANH_GENERATION_PILOT_USER_LIMIT=20
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

## Security patch rollout, 2026-10-08

Source implementation is not a live deployment. Keep paid generation disabled until these checks pass.

### Repeatable isolated PostgreSQL checks

Use a disposable local PostgreSQL with TLS and synthetic records. Create `la_lanh_security_test`
on `127.0.0.1:55432`; trust the local test CA using the `sslrootcert` URL parameter. Apply
migrations through `20261008_0030` with the API/worker's verified connection configuration.
Never disable TLS verification to make a test pass.

Set `LA_LANH_TEST_POSTGRES_URL` privately to that synthetic database URL, then run:

```sh
uv run --directory apps/api pytest tests/content_rewrite/test_postgres_concurrency.py
```

The fixture truncates synthetic tables and refuses any other host/port/database. Never use live
Supabase or a shared environment. Without the variable these tests skip, which does not satisfy
the PostgreSQL release gate. The 2026-10-09 receipt records 18 passing cases. Populated legacy
backfills and deployment-target controls still need separate proof.

Keep generation and its worker disabled during these checks. Stop the temporary server after
verification. Never install the synthetic superuser/certificate on production. Security details
stay in the managed artifact store; product progress is recorded in
`docs/reviews/2026-10-09-security-content-work-handoff.md`.

### Live release sequence

1. Stop the rewrite worker and wait for its current request to finish before schema upgrade. Disable new enqueue during the upgrade.
2. Back up the database using the existing restricted backup process. Run Alembic through `20261008_0030`. Migration 0029 preserves anonymous month debits. Migration 0030 preserves visible day debits, removes legacy encrypted queue jobs, and adds cascading owner/parent foreign keys. It does not delete user readings or reset spend history. Only unfinished jobs need re-enqueue; AI-updated readings retain their existing version.
3. Verify PostgreSQL hostname and certificate chain using `python -m scripts.check_database_tls`. API, worker and migrations use the same verified SSL context. The pooler hostname must match its certificate. If a custom CA is required, install the provider's trusted CA through the approved server configuration, never disable verification to unblock a deploy.
4. Run fake-provider tests for consent, guest deletion, parent deletion, rollback, expired lease and budget persistence. Run concurrent two-connection race tests against PostgreSQL as well. SQLite ignores row locks and cannot close that release gate.
5. Keep the existing guest-retention job scheduled even when generation is off. It purges bounded batches of unlocked rewrite envelopes older than 24 hours, including abandoned expired leases. It skips currently active leased work. The worker never selects pending jobs older than the retention limit. Owner/parent deletion cascades immediately. Anonymous daily/monthly counters remain and contain no guest, chart, question or output identifiers.
6. Verify request bodies above 1 MiB return 413 before JSON parsing, including chunked bodies. The existing smaller authenticated Studio limit remains. Verify unsupported HTTP methods produce only the `OTHER` metrics label.
7. Check provider project controls, restricted key permissions and secret mounts without displaying the key. Reconcile the application's conservative admission ledger with provider usage. A stolen key used outside this app bypasses its ledger. The app's $1/month ceiling is not a guarantee against unauthorized provider-side key use.
8. Run owner-only smoke flows on the release candidate. Verify guest onboarding, date-only note, optional birth supplement, Tarot, Radar, consent withdrawal and deletion. Restart the paid worker only after explicit approval and all security gates pass.

The current pilot implementation serializes each owner's provider request with lifecycle changes using a database transaction. Projector writes and lease success borrow the same session and commit together. A withdrawal or deletion may wait for the admitted call to finish, normally within the configured provider timeout and at most the worker's bounded timeout. It cannot retract a request already received by a provider. This conservative design is limited to the small pilot; before scaling, replace it with a durable in-flight cancellation/drain protocol and test process crashes and connection loss.

Budget reservation commits before the provider boundary. Day and month debits are anonymous and non-refundable even after a gate failure, cancellation, retry or deletion. Exact observed usage is separate from admission limits. Reservation dates use UTC; a call admitted just before midnight may finish the next day. No provider call or billing change is part of offline verification.

An expired reserved lease is terminalized as ambiguous even if its send marker rolled back. Never automatically resend such work: the original call may already have been billed. Only an explicit provider response declaring retry safety can authorize the existing bounded retry path. Parent locks precede job locks, and lease deadlines are checked after lock acquisition, before sending, and during atomic publication. Paid workers require PostgreSQL; SQLite tests verify rollback but cannot prove concurrent row-lock behavior. Production workers must use managed guest hash and encryption keys, not development defaults.

Removing birth time or place erases affected Radar parents and both perspectives, including queued AI jobs. A delayed enqueue for the old report is rejected. Users must generate a new report from the remaining information; unrelated birthless Tarot remains intact. Concurrent creation of a new Radar report from a stale snapshot remains a PostgreSQL race-test gate, not a verified live guarantee.

Rollback retains migrations 0029/0030 and both debit tables. Keep generation disabled when rolling application code back. Do not downgrade to a worker that can create jobs without owner/parent erasure links.

Primary references checked: [PostgreSQL TLS verification](https://www.postgresql.org/docs/current/libpq-ssl.html), [Supabase database connections](https://supabase.com/docs/guides/database/connecting-to-postgres), and [OWASP API resource limits](https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption/).
