# Paid rewrite pilot — 10–20 testers

Date: 2026-10-08. Status: local preparation implemented; live activation remains blocked.
Production remains deterministic. Do not infer runtime activation from funding or a successful probe.

## Approved intent

The owner requested paid rewriting for a small test group and explicitly chose the existing key,
not creation of a new key. Preserve the latest requested ceiling of USD 1/month. A prepaid credit
purchase is separate from usage approval and requires an explicit decision if it exceeds this ceiling.
Do not enable automatic recharge, purchase credits, or increase the budget on the owner's behalf.

## Verification history

- Found the existing key in the operator's private mode-restricted configuration file. No plaintext
  credential was printed, copied into Git, or sent to the browser/frontend.
- One authenticated `GET /v1/models/gpt-6-luna` returned 200. This verifies model metadata access,
  not sufficient billing balance, content quality, or successful paid generation.
- The signed-in Platform account showed Personal Organization, Default project,
  `proj_eiNVxorNxWcueLgvBnYOU16T`, Free trial, and credit remaining USD 0.00.
- The visible project Limits screen exposed model/rate controls but no spend-limit editor on this
  unfunded account. No provider monthly cap was set or claimed as verified.
- Production has no mounted OpenAI credential yet. Destination confirmation was requested for
  `/opt/la-lanh/secrets/openai_api_key`; do not transfer until confirmed.
- No generation worker enabled, no paid generation call, no billing mutation.

The bullets above describe the initial unfunded check. After the owner completed payment:

- Platform billing showed USD 5.00 in prepaid credit and **auto-reload off**. The operator did not
  purchase credits or save a payment method.
- One synthetic GPT-6 Luna probe completed, local content gates passed, input 710 tokens, output
  63 tokens, pinned-price cost USD 0.00010250. The generated text was neither printed nor retained
  locally. No user data was sent. The trusted-machine daily receipt prevents an accidental rerun.
- The first project hard-limit save was rejected by action review because historical USD 1/day and
  later USD 1/month approvals conflicted. The operator did not retry or use a workaround. After the
  owner said "done", a later read-only observation showed **$0.00 / $1.00** and **"Requests will start
  to fail when limit is reached"**. The enforced project limit is now verified on
  `proj_eiNVxorNxWcueLgvBnYOU16T`; screenshot `/tmp/la-lanh-openai-monthly-cap-verified-2026-10-08.png`.
  Do not confuse the additional 100% alert with the observed enforced spend limit.
- The existing key has **not** been transferred to the VPS. The persistent destination still needs
  explicit confirmation. No new key was created and no production flags were changed.

## Local implementation

- Migration `20261008_0029` adds a server-only aggregate monthly reservation table. It has no guest,
  chart, job or consent identifiers. UTC month and conservative nanodollar debit are the only fields.
  RLS and denied browser-role grants protect it. Rollback never deletes its history.
- The shared worker reserves an upper-bound cost before the provider boundary. The monthly debit
  is non-refundable, including failures, owner purge and consent withdrawal. This can stop earlier
  than actual invoiced usage, intentionally. A second reservation for the same lease is rejected.
- Worker startup rejects a missing/zero monthly limit or pilot limit. Settings reject more than
  100 cents/month or more than 20 active opted-in sessions. Cohort membership is checked again
  before provider use. A session is not proof of a unique human; do not claim identity enforcement.
- `Mình` has a separate personal opt-in disclosure, close/cancel without consent, and withdrawal.
  Opt-in stays hidden when generation is disabled or only shadow/editorial modes are configured.
  The API status endpoint authenticates the caller and reveals only their own boolean state.
- OpenAI requests explicitly use `service_tier:default` and `store:false`. Personal consent never
  covers Radar/Matching data; those require separate scope consent and remain off for this rollout.

Safe tests cover cross-day accounting, owner deletion, concurrent reservations on SQLite,
duplicate debit prevention, 21st-session rejection, expiry/revocation, API CSRF and UI opt-in/cancel.
They do not replace a PostgreSQL concurrency/migration rehearsal or scored editorial review.

## Required before activation

1. Owner completes payment details and explicitly approves the required initial credit purchase.
   Official minimum purchase is USD 5, separate from the USD 1/month consumption target. Turn
   **Use auto-reload off** before purchase; verify the resulting balance and recharge setting.
2. Confirm the reused key's billing project and set/verify a USD 1 monthly enforced project limit.
   A spend alert alone is not a cap. Provider enforcement can be delayed; retain app-side protection.
3. Implement and verify a durable app-side monthly reservation/cost cap before sending live jobs.
   Current runtime only caps the UTC day. Job-row accounting is not sufficient evidence of a strict
   monthly cap, especially across midnight, retries, deletion and cleanup. Do not activate at
   USD 1/day or label it USD 1/month. Keep a conservative daily/token bound as a second layer.
4. Define pilot eligibility for 10–20 testers and approved surfaces. Existing percentage rollout is
   artifact-based, not an enrollment limit. Do not describe it as a fixed-user cohort.
5. Preserve explicit external-rewrite consent per subject/surface, revocation checks, minimal
   semantic briefs, no raw birth/contact data or third-party private data, `store:false`, and no
   payload/key logging. Check current privacy disclosure against actual provider retention.
6. After confirmed secret destination, copy the existing key via encrypted transport into the private
   worker's secret file only. API and Caddy must not mount it; no new key or rotated credential.
7. Run one bounded synthetic probe, review its gate output and actual cost. Complete the scored
   content release gate before user-visible publication; offline corpus coverage alone is not proof
   of generated quality. If rejected, retain fallback instead of weakening gates.
8. Enable only approved pilot modes/surfaces; verify healthy isolated worker, genuine generated
   revision, consent/fallback behavior, cache, cost reporting and rollback. Document exact coverage.

The probe in step 7 is now complete. Do not repeat it. The 670-case manifest passes offline, but a
complete **human-scored generated-output** results file has not been produced. This is still a
release blocker, not permission to invent scores, lower thresholds, or enable publication anyway.

### Proposed conservative configuration, not applied

Provider project enforced limit: USD 1/month, now verified. Proposed app reservation cap: **90 cents/month**, to leave room
for the probe, out-of-ledger evaluation and delayed provider billing. Separate synthetic paid
evaluation must use an operator-wide reservation ledger and fit the same total; the production
table does not account for standalone scripts or other clients using this key.

```text
LA_LANH_GENERATION_MONTHLY_BUDGET_CENTS=90
LA_LANH_GENERATION_DAILY_BUDGET_CENTS=3
LA_LANH_GENERATION_DAILY_TOKEN_BUDGET=100000
LA_LANH_GENERATION_PILOT_USER_LIMIT=20
LA_LANH_GENERATION_OPENAI_PROJECT_ID=proj_eiNVxorNxWcueLgvBnYOU16T
```

Keep generation disabled until approval and gates pass. Start with one reviewed personal content
type, not all 13 registry entries. The standalone worker currently implements `daily_home`, `reveal`,
`natal`, `transit_insight`, `radar` and `tarot`; the last two-person content type cannot use personal
consent. Unlisted content types stay off. `beta_10`/`beta_50` sample artifacts, not people; they do not
limit provider cost and cannot substitute for the active-session cap.

## Sources checked

- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna): Standard short-context
  USD 0.10/1M input, USD 0.50/1M output; same as current pinned cost accounting. Do not use Fast,
  regional pricing, hosted tools or cache writes without reviewing their extra charges.
- [Spend limits](https://developers.openai.com/api/docs/guides/spend-limits): alerts do not stop
  requests; enforced limits can slightly overshoot because enforcement is not instantaneous.
- [Prepaid billing](https://help.openai.com/en/articles/8264644-setting-up-and-managing-prepaid-api-billing):
  USD 5 minimum purchase; auto-reload on by default at setup; credit balance is not an instantaneous cap.
- [Provider data controls](https://developers.openai.com/api/docs/guides/your-data): `store:false`
  is not a Zero Data Retention guarantee; abuse-monitoring retention may still apply.
- [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security): private
  accounting tables need browser-role grant isolation as well as row-level security.
- [Vietnam personal data protection law](https://congbao.chinhphu.vn/van-ban/luat-so-91-2025-qh15-45578.htm):
  engineering consent and deletion controls are not a certificate of legal compliance. Provider/DPA,
  cross-border assessment and retention review still require evidence before user-data activation.

AC/DoD incomplete: persistent key-destination confirmation,
PostgreSQL rehearsal, scored generated-content review, provider/governance evidence,
secret transfer, deployment and live paid end-to-end verification. Do not report AI as enabled.

Final local QA: 197 web tests passed after the API prefix/CSRF regression fix; 525 API tests passed.
Real browser opt-in saved, survived reload and withdrew correctly on a temporary synthetic session,
with worker disabled. QA CLI smoke/build passed with localhost permission. See
`docs/reviews/paid-rewrite-pilot-2026-10-08/receipt.md` for exact limits and unresolved gates.

An additional **zero-cost model metadata read** with `OpenAI-Project` explicitly set to the capped
project returned 200. The response did not include an effective-project header, so this is an access
check, not invoice attribution proof. The new worker now requires the explicit project setting and
passes it to the SDK, instead of relying on an implicit account default.
