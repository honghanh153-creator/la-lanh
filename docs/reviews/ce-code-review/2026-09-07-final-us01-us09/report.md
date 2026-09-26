## Code Review Results

**Scope:** `dde8ff1dae6b03a943619c1e506e17836b380223` -> current working tree on `feat/guest-birth-chart-mvp` (425 tracked and untracked paths; user-owned WIP preserved)
**Intent:** Complete the UX-first Chart Synthesis plan and the app-first US01-US09 flow, then apply review findings locally without enabling external generation in production.
**Mode:** markdown local-apply

**Reviewers:** correctness, security, reliability, performance, testing, maintainability, project standards, API contract, data migration, and Swift/iOS.

- Security was selected for birth data, capability links, encryption, deletion, and the provider boundary.
- Reliability and performance were selected for offline behavior, request deadlines, compute limits, and worker leases.
- API contract and data migration were selected for generated clients and three new schema revisions.
- Swift/iOS was selected because the primary product is a Capacitor app.
- The independent adversarial reviewer timed out; a separate final validator rechecked the high-risk findings and found the additional #23 and #24 regressions, both fixed.

### Applied (explicit local apply; safe, verified)

| # | File | Fix | Reviewer |
|---|---|---|---|
| 1 | `apps/api/app/api/v1/routes/birth_profiles.py` (+tests/contracts) | Added explicit `calculation_kind` for date-only versus natal responses | api-contract |
| 2 | `apps/api/app/api/v1/routes/la_chung.py` (+contracts/web) | Added typed owner-result response and generated client type | api-contract, maintainability |
| 4 | `apps/api/app/domains/readings/models.py` (+migration/tests) | Included `config_hash` in projection identity | correctness |
| 5 | `apps/web/src/shared/api/client.ts` (+test) | Activation now updates the authoritative revision used by save/share | correctness |
| 6 | `apps/web/src/shared/storage/clearPersonalData.ts` (+test) | Personal cleanup preserves the non-personal app shell | correctness, testing |
| 7 | `apps/web/public/sw.js` (+test) | Install discovers and precaches current fingerprinted JS/CSS bundles | correctness, testing |
| 8 | `apps/api/app/domains/astro/engine.py` (+test) | Mean-node mode now uses Swiss Ephemeris body 10 for transits | correctness |
| 9 | `apps/api/migrations/versions/20260907_0012_encrypt_private_snapshots.py` (+test) | Added executable duplicate-report No-Go preflight | data-migration |
| 11 | `apps/api/app/domains/la_chung/service.py` (+migration/tests/web) | Added owner and draft-bound invite idempotency | project-standards |
| 12 | `apps/api/app/domains/la_chung/service.py` (+migration/tests) | Encrypts every new recipient label with request-bound AAD; legacy backfill remains a release gate | project-standards, security |
| 13 | `apps/api/app/middleware/admission.py` (+tests) | Added create/resend abuse limits | project-standards |
| 14 | `apps/api/app/api/v1/routes/la_chung.py` (+tests) | Added `noindex`, `no-store`, and no-referrer protection to public invite responses | project-standards |
| 15 | `apps/web/src/shared/api/client.ts` (+test) | Added a composed 15-second request deadline | reliability |
| 16 | `apps/api/app/domains/readings/worker.py` (+tests) | Worker loop recovers with capped backoff and never retries an ambiguous send | reliability |
| 17 | `apps/api/app/domains/readings/postgres.py` (+tests/docs) | Serialized guest deletion with the provider-send boundary using a guest row lock; PostgreSQL race evidence is still required | security |
| 18 | `apps/mobile/capacitor.config.ts` (+guard) | Replaced the invalid iOS scheme with `la-lanh`; signed-binary evidence is still required | swift-ios |
| 19 | `apps/api/tests/middleware/test_admission.py` | Covered birth, public, global, create, and resend admission branches | testing |
| 20 | `apps/web/src/shared/api/client.reliability.test.ts` | Covered offline save intent and revision-safe replay paths | testing |
| 21 | `apps/web/src/shared/storage/clearPersonalData.test.ts` | Covered aggregate device cleanup while retaining app-shell assets | testing |
| 22 | `apps/web/src/serviceWorker.test.ts` | Covered install, activate, navigation fallback, API bypass, and asset caching | testing |
| 23 | `apps/api/app/domains/readings/postgres.py` (+test) | Prevented deterministic fallback from being offered after generated activation | final-validator |
| 24 | `apps/web/src/shared/api/client.ts` (+test) | Gave guest deletion a 75-second privacy-operation deadline instead of the normal 15 seconds | final-validator |

Validation: full `pnpm check` passed; API 193 tests passed; web 37 tests passed; Ruff, mypy, ESLint, TypeScript, contracts, runtime/privacy/mobile guards, production build, fresh-schema QA smoke, PostgreSQL-dialect offline migration SQL, and Capacitor sync passed. Browser QA passed at 390 x 844 for Welcome -> Consent -> Vibe -> Home -> deep birth consent -> Aura gift -> activation -> Profile dark/light -> Western/Jyotish.

Committed: no. The checkout already contained a large user-owned WIP set, so all review fixes remain uncommitted for the user.

### P2 -- Moderate

| # | File | Issue | Reviewer | Confidence |
|---|---|---|---|---|
| 3 | `apps/api/app/api/v1/routes/daily_notes.py:183` | Some non-2xx OpenAPI entries still omit the shared problem body | api-contract | 75 |
| 10 | `apps/api/app/domains/saved/postgres.py:64` | Saved history needs cursor pagination before persistent accounts | performance | 75 |

- **#3** - Runtime errors already use a safe problem shape and the app has a fallback, but an external generated SDK would not see the complete error contract. Add one shared `ProblemResponse` and align validation/domain media types before publishing an external SDK.
- **#10** - The current guest product has a natural maximum of one saved note per day across a 30-day session. Add a stable cursor plus Load more before US19 introduces long-lived account history.

### Requirements Completeness

- [x] R1 - Canonical, versioned `ReadingPlan` exists.
- [x] R2 - Hero synthesis requires independent or higher-order evidence.
- [x] R3 - Planner selects a central negotiation, reinforcement, or tension.
- [x] R4 - Reading includes an everyday manifestation.
- [x] R5 - Natal and eligible transit content are separated.
- [x] R6 - Western and Jyotish plans remain isolated.
- [x] R7 - Precision gates remove unstable houses and angles.
- [x] R8 - Home exposes a compact hook and takeaway.
- [x] R9 - Detail orders insight, manifestation, optional transit, and micro-action.
- [x] R10 - Vietnamese tone and slang limits are executable.
- [x] R11 - High-stakes, deterministic, diagnostic, fear, and dependency claims are blocked.
- [x] R12 - Disclaimer is present but visually secondary.
- [x] R13 - Empty or repetitive bonus content is omitted.
- [x] R14 - Astrology claims map to factor references.
- [x] R15 - Out-of-plan facts fail the evidence gate.
- [x] R16 - Versioned deterministic quality gates evaluate every candidate.
- [x] R17 - Generation keys, leases, and winners are idempotent.
- [x] R18 - Immutable revisions carry content and gate provenance.
- [x] R19 - Feedback is enum-only with no free text.
- [x] R20 - Provider payload is allowlisted and excludes raw birth and identity data.
- [ ] R21 - Source behavior is implemented; disposable PostgreSQL concurrency and legacy purge evidence remain release gates.
- [x] R22 - Telemetry excludes prompts, readings, raw birth data, factors, and capability tokens by application contract.
- [ ] R23 - Provider training, retention, region, and DPA evidence remain governance gates; provider stays off.
- [x] R24 - No untrusted text can alter plans, policies, tools, or data access.
- [x] R25 - Deterministic fallback survives provider, gate, timeout, and kill-switch failure.
- [x] U1 - Versioned factor planning.
- [x] U2 - Deterministic renderer and four gates.
- [x] U3 - Provider-neutral adapter, production-off by default.
- [ ] U4 - Immutable storage and queue are implemented; real PostgreSQL race evidence remains.
- [x] U5 - Unified API projections and generated contracts.
- [x] U6 - Exact revision save/share/offline/deletion lifecycle.
- [ ] U7 - Cosmic Glass app flow is implemented and browser-tested; signed native simulator/device evidence remains.
- [ ] U8 - Runbook and controls exist; production provider, edge, store, and key-management evidence remains.

### Actionable Findings

| # | File | Issue | Route | Notes |
|---|---|---|---|---|
| 3 | `apps/api/app/api/v1/routes/daily_notes.py:183` | Complete the external error contract | `manual -> downstream-resolver` | Accepted and recorded; required before an external SDK |
| 10 | `apps/api/app/domains/saved/postgres.py:64` | Add saved-note cursor pagination | `gated_auto -> downstream-resolver` | Accepted and recorded; required before US19 persistent history |

### Deployment Notes

- Pre-deploy: run migrations up and down on disposable PostgreSQL, including duplicate preflight, config recovery, and label backfill counts.
- Verify concurrency: with two connections, delete-first prevents a send marker and send-first makes deletion wait for a terminal attempt.
- Verify privacy: no legacy plaintext snapshots or labels remain; capability tokens are redacted before every access-log layer.
- Verify native: signed iOS and Android builds complete guest -> birth -> Daily -> Aura -> save/share -> delete against the production-like HTTPS API.
- Healthy signals: deterministic projection success above 99.9 percent, one winner per generation key, zero generated Jyotish attempts, and no private content in logs.
- Rollback trigger: unsupported claim, cross-user access, late provider send after completed deletion, or private-data canary at the provider boundary.
- Rollback: disable generation, stop workers, preserve deterministic active and immutable saved/shared revisions, then invoke incident handling if data crossed the boundary.
- Validation window and owner: one week or 1,000 internal attempts, whichever is later; product engineering and privacy/security jointly own sign-off.

### Coverage

- Applied findings: 22.
- Accepted residual findings: 2, durably recorded in `docs/reviews/2026-09-07-chart-synthesis-release-review.md`.
- Suppressed findings: 0.
- Failed reviewer: independent adversarial pass timed out; all other selected reviewers completed, and a final validator rechecked high-risk behavior.
- Residual risk: legacy encrypted-data migration, real PostgreSQL locking, distributed rate limits, native binaries, store disclosures, and provider governance cannot be proven in this local checkout.
- Testing gap: no Xcode/Simulator, Android JDK, Docker/PostgreSQL, or provider production credentials were available.
- Bundle advisory: the main JavaScript chunk is about 606 kB minified; route-level code splitting is a performance follow-up.

---

> **Verdict:** Not ready
>
> **Reasoning:** The local deterministic app and US01-US09 flow are ready for product review, with all discovered P1 code regressions fixed. Production release remains No-Go until PostgreSQL, legacy-data, signed-native, edge/privacy, and provider-governance evidence exists.
>
> **Fix order:** PostgreSQL and legacy-data proof -> signed native QA -> edge and store privacy evidence -> provider shadow gate -> external API pagination and problem-contract hardening.

### Actionable Findings - Closing Recap

| # | Severity | File | Action | Response type |
|---|---|---|---|---|
| 3 | P2 | `apps/api/app/api/v1/routes/daily_notes.py:183` | Add the shared documented problem schema before external SDK release | manual; suggested fix present; confidence 75 |
| 10 | P2 | `apps/api/app/domains/saved/postgres.py:64` | Add cursor pagination before US19 persistent history | gated auto; suggested fix present; confidence 75 |
