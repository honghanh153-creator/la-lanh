# Chart synthesis — release, monitoring and rollback runbook

Last reviewed: 2026-09-07. Owner: product engineering. Product posture: deterministic is the full product; external generation is optional and off by default.

## Flag matrix

| Stage | `generation_enabled` | Provider | Governance | User-visible behavior |
|---|---:|---|---:|---|
| Local/default | false | disabled | false | Deterministic revision only |
| Internal shadow | true | openai | true | Candidate may be generated and gated; deterministic remains active; no automatic swap |
| Reviewed exposure | true | openai | true | Accepted Western candidate becomes `available`; user explicitly activates it |
| Kill switch | false | disabled | false | All new reads remain deterministic; saved/shared exact revisions stay unchanged |

Generated Jyotish remains disabled regardless of the matrix until a separate expert corpus and sign-off exist.

## Pre-release Go/No-Go

Release is **No-Go** until every applicable row has evidence:

- `pnpm check`, contracts, runtime/privacy guards and browser QA pass.
- PostgreSQL migration up/down and two-worker lease/CAS concurrency pass on a disposable database.
- Western Vietnamese benchmark has zero unsupported astrology facts and records the evaluator version.
- Knowledge coverage proves 12 signs, 12 houses, all launch bodies, six Western aspects, degree/orb bands and three transit phases; every sample passes the evidence/editorial/privacy/anti-influence gates.
- Daily freshness proves same-day deterministic replay and adjacent-day changes to hook plus micro-action or hero focus. “Tín hiệu vũ trụ” and equivalent generic cosmic-message copy are rejected by the editorial gate.
- Moderated user test demonstrates: at least 80% can repeat one takeaway, at least 70% rate it chart-specific, “chung chung” is below 15%, and Home takeaway is understood within 3–5 seconds. Minimum sample: 20 target users; owner: product research.
- Provider DPA, subprocessors, inference region, cross-border route, retention and ZDR/MAM status are documented. `store=false` alone is insufficient.
- Apple archive privacy report, App Privacy answers and Google Data Safety answers match the signed binary and enabled SDKs.
- iOS and Android release builds pass create guest → birth → Daily → Aura → save/share → delete on simulator/device with the production-like HTTPS API.
- Production uses managed encryption/hash keys, `guest_cookie_secure=true`, `native_app_enabled=true`, and `cookie_domain` exactly matching the API host.
- Legacy chart/daily/saved/share rows and Lá Chứng recipient labels are either purged or migrated through a key-aware, audited backfill. SQL-only migrations must not manufacture encryption envelopes.
- Migration `20260907_0012` executes a duplicate Lá Chứng preflight before any DDL and blocks if the same `(request_id, reason)` appears more than once. Resolve duplicates under the retention policy; the migration never deletes them.
- Migration `20260907_0013` is **No-Go** if any projection config cannot be recovered from a linked legacy plaintext chart, or if active/available pointers do not prove the same config. Run a key-aware backfill that decrypts `ReadingPlan.config_hash`, splits mixed-config projections, and recomputes canonical scope keys; never substitute a default hash.
- Distributed edge admission limits are active for guest creation, birth compute, Lá Chứng create/resend and public capability routes; capability tokens are redacted before CDN/WAF/proxy/application access logs.

## Safe rollout

1. Deploy expand migrations while generation remains off.
2. Deploy `20260907_0012`; its duplicate-report preflight blocks the unique index without modifying duplicate rows. Then execute the approved key-aware legacy backfill or purge and verify no personalized plaintext remains before removing compatibility columns in a later migration.
3. Deploy `20260907_0013`. If its safe plaintext backfill cannot prove every projection config and pointer, stop and run the documented key-aware projection backfill/split before retrying.
4. Deploy `20260907_0014` before code that writes encrypted Lá Chứng labels. Backfill legacy labels one row at a time with AAD `la-chung-recipient-label:{request_id}`; decrypt and byte-compare each envelope before recording it complete. Keep the plaintext compatibility column until counts, key-version coverage, backup restore and rollback rehearsal pass. Plaintext clearing/removal is a separate, explicitly approved migration.
5. Verify deterministic projections, exact save/share, precision withdrawal and full guest deletion on the new schema.
6. Enable internal shadow only after provider governance passes. Do not expose candidate text or send reading text to telemetry.
7. Observe one week or 1,000 attempts, whichever is later. Review only enum/count metrics and a separately approved, access-controlled sample workflow.
8. Enable user-visible `available` updates for a small internal cohort. Never hot-swap an open note.
9. Expand only if factuality, safety, privacy, latency and user outcome gates remain green.

## Monitoring and validation

Allowed dimensions: provider/model/prompt/gate versions, purpose, tradition, precision bucket, result enum, count and latency bucket. Do not log prompt, reading text, raw birth data, coordinates, factor refs, chart/profile/session IDs or capability tokens.

Healthy signals:

- deterministic projection success remains above 99.9%;
- generation failures never increase Daily/Insight request errors;
- one accepted winner per generation key;
- no generated Jyotish attempt;
- deletion leaves no first-party plan/revision/attempt/share rows for the guest;
- deletion first marks the guest `deleting`, cancels every generation attempt that has not crossed the durable send marker, and returns success only after any already-sending attempt becomes terminal;
- the worker and deletion transaction both lock the guest row before crossing their irreversible boundary; a PostgreSQL two-connection test must prove delete-first blocks a provider send and send-first makes deletion wait;
- `gate_rejected`, refusal and incomplete rates are visible as counts, not content.

Rollback triggers:

- any unsupported factual claim reaches `available`;
- any personal-data canary appears in provider payload/log/trace;
- a provider request begins after the corresponding guest deletion has returned success;
- cross-user revision, save, share or capability access;
- ambiguous retries create duplicate provider work or competing winners;
- deterministic request availability degrades because of the optional worker;
- provider contract, retention or subprocessor status changes without review.

## Rollback

1. Set `generation_enabled=false` and provider to `disabled`.
2. Stop generation workers; do not delete or rewrite saved/shared revisions.
3. Keep deterministic active projections serving immediately.
4. Quarantine affected generated revisions from activation and preserve only the minimum audit data allowed by policy.
5. If personal data crossed the boundary, invoke incident response, provider deletion where contractually available, user/regulator notification assessment and store disclosure review.
6. Re-enable only after root cause, regression tests, corpus rerun and governance approval.

## App-first validation

Build with `VITE_API_BASE_URL=https://<api-host>/v1 pnpm mobile:sync`. The API deployment must use the same host in `LA_LANH_COOKIE_DOMAIN` and enable secure cookies. Verify the native marker, guest cookie persistence, CSRF mutation, app restart, session expiry and delete on both platforms. A successful web build or `cap sync` is not release evidence.

For PWA fallback, install from a clean profile while online, wait for the service worker to activate, clear only the ordinary HTTP cache, disable network and reopen a deep link. The install event must have cached the fingerprinted JS/CSS discovered from the current `index.html`; no API or personalized response may appear in Cache Storage.

## Current local blockers

- This machine does not currently provide Xcode/Simulator, Android Studio/JDK or Docker/PostgreSQL. Native binary smoke and PostgreSQL concurrency therefore remain No-Go items, not silently passed gates.
- Provider remains production-off pending privacy/governance evidence and benchmark/user-research thresholds.
- The application limiter is a fail-fast backstop only. Multi-replica production still needs a shared/edge policy and verified token redaction in every access-log layer.
