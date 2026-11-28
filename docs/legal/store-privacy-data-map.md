# Lá Lành — store privacy data map

Last reviewed: 2026-10-29 (data export delta; earlier local engineering delta 2026-10-09). This is an engineering disclosure map, not legal advice. Final answers must be reconciled against the signed release binary, production data flow, every SDK and the store console wording at submission time.

Design-only addition: 2026-11-25, money context (#709), inventoried below. This addition does not re-certify the runtime, earlier deltas or current legal/store sources.

## Runtime posture

- Product target: Capacitor iOS/Android app; web is a companion and QA reference.
- Account: guest-first; a pseudonymous guest ID owns the profile before login.
- Tracking/advertising: none implemented.
- Analytics: none implemented for reading text, chart factors or personal fields.
- External content provider: production off by default. If enabled after governance, it receives only an allowlisted derived ReadingPlan; never raw birth values, coordinates, identity/session/chart IDs or free text.
- Current web beta processors: Hetzner VPS in Germany and Supabase in Frankfurt, Germany, as named in the beta privacy notice and deployment register. Google Cloud is not the deployed route. External rewrite activation adds OpenAI as a separate processor; review the applicable Law 91/2025/QH15 and Decree 356/2025/NĐ-CP obligations, DPA, processing destinations and retention before sending derived user content.
- Transport: production native build requires an absolute HTTPS API URL. Android cleartext and mixed content are disabled.
- Native session: authentication credential stays in a production `Secure` + `HttpOnly` API-domain cookie; only the separate CSRF token is persisted in app-local storage. Native requests carry a marker for origin handling, but still require the CSRF token and cookie.
- Deletion: in-app guest deletion removes first-party server records, exact saved/share revisions and device personal caches; generated attempts are tied to the same deletion epoch/cascade.

### Session-isolation engineering delta — local, 2026-10-09

- Private in-memory fallback is tagged with the current guest epoch, local request generation and
  CSRF-cookie change marker. These tags verify cache freshness, not authentication. The server
  still verifies HttpOnly credentials and requires owner/source-guest agreement on owner routes.
- A browser-local random cross-tab notice contains no epoch, birth field, reading, token or user ID.
  It is a trigger to recheck the server, not an accepted identity. It remains local; no telemetry or
  new third-party processor is added. Native cookie/storage behavior needs separate device testing.
- On a known session change, private caches, queues and in-progress drafts are cleared and pending
  responses cancelled/fenced. This does not delete the previous person's server profile or revoke
  their independent sessions. Rechecking offline hides private content rather than displaying it
  without verified ownership. The UI warns before a deliberate new guest start.
- Daily meaning selection reuses existing derived chart factors. No new birth, mood, free text,
  background, location or relationship fields are collected. Static synthetic collision evaluation
  is offline; other users' private readings are not scanned to enforce unique prose.
- The Daily mood check-in can be stored application-encrypted at rest (migration `20261111_0042`).
  The first release ships only the reader and keeps writing plain values; new and changed entries
  are encrypted once `LA_LANH_MOOD_ENCRYPTED_WRITES` is turned on in a later release. Entries
  written before that keep a plain value until changed or expired with their Daily note; collection,
  purpose, retention, export and deletion are unchanged.
- These local fixes are not a production deployment, native release approval or complete legal
  compliance assessment. The signed release/runtime remains the disclosure authority.

## Apple Privacy Manifest / App Privacy mapping

The app target includes `PrivacyInfo.xcprivacy` with `NSPrivacyTracking=false`. The manifest deliberately uses conservative categories because the API collects structured birth inputs and derived content even though no contact identity is required.

| Apple category | Lá Lành data | Linked | Tracking | Purposes |
|---|---|---:|---:|---|
| User ID | pseudonymous guest/owner identifier | Yes | No | App Functionality |
| Precise Location | user-selected birthplace coordinates used for chart houses; not device GPS/current location | Yes | No | App Functionality, Product Personalization |
| Other User Content | birth date/time, selected context, mood and user-initiated response fields | Yes | No | App Functionality, Product Personalization |
| Product Interaction | mood/save/share/activation state required to provide the feature | Yes | No | App Functionality |
| Other Data Types | derived natal/transit factors, reading plan/revision and astrology profile | Yes | No | App Functionality, Product Personalization |
| Other User Content | Radar nickname/context, permission attestation and minimized relationship result (audience: private mode owner only; invite mode the invited pair) | Yes | No | App Functionality, Product Personalization |

Before App Store submission:

1. Generate Xcode’s privacy report from the archive and compare it with the app manifest and every SDK manifest.
2. Confirm whether Apple’s current questionnaire expects historical birthplace under Location or Other Data for this exact flow; keep the more protective declaration until counsel/store review approves a narrower one.
3. Do not declare analytics, diagnostics or tracking unless the release binary actually includes them; if added, update consent, inventory, manifest, App Privacy answers and deletion behavior together.
4. Verify required-reason API warnings from the archive. The app’s own Swift code currently declares no required-reason API; bundled Capacitor frameworks carry their own manifests.

## Google Play Data Safety mapping

Use the following as the draft answer source, then map to the current Play Console fields:

| Google category | Lá Lành data | Collected | Shared | Required/optional | Purpose |
|---|---|---:|---:|---|---|
| Personal info — User IDs / Other info | guest ID, birth inputs, derived astrology profile | Yes | No by default | birth date required for core reveal; time/place optional | App functionality, Personalization, Security |
| Location — precise | user-selected birthplace coordinates, not current device location | Yes | No by default | Optional | App functionality, Personalization |
| App activity — App interactions | mood/save/share/activation state | Yes | No | Optional by action | App functionality |
| User-generated content / Other | Lá Chứng response/context where enabled | Yes | Only with an explicit capability link and bounded projection | Optional | App functionality |
| Personal info / User-generated content | Radar nickname/context, permission attestation or pair consent, and minimized relationship result | Yes | Private mode: owner only; invite mode: invited pair; raw birth inputs are never exchanged | Optional | App functionality, Personalization, Security |

## Radar hợp gu release delta

- Intended public scope is a private, known-person 1:1 Radar. Pool/discovery, 5 hidden cards, mutual, chat and recap (US-14–18) are deferred. Legacy matching routes are still mounted for existing data. Audit P02 (2026-10-22) found that they still accepted new profiles (gender identity, dating intent, preference, age range, region) without matching consent or DOB; the fix gates profile, consent and pool-join writes behind `matching_accepting_new_activity` (default off, HTTP 410 after the owner/CSRF check), keeping consent withdrawal and leaving the pool. Until a release with that fix is live, do not claim matching collection is impossible; existing rows still need the deletion paths and an aggregate count before any purge decision.
- Primary `private_check` lets A enter B's birth data only after attesting that B allowed this use. Raw B DOB/time/place is processed in request memory and must not be persisted as raw inputs, logged, cached or turned into a profile. Retained fields include encrypted nickname/result, attestation timestamp/version, coarse context/voice and keyed retry metadata, for 24 hours of result access (owner decision 2026-10-19; results created earlier keep their original expiry of at most 30 days). Expired rows are hidden at once. The six-hour `cleanup_expired` job deletes them with their rewrite jobs (cascade), nominally within about 30 hours of creation; each run that meets an active rewrite send fence or started generation attempt for that owner defers deletion by one six-hour run, with no hard upper bound (see the Radar spec §6). Backup expiry is a separate lifecycle check. A consented invite result keeps 30 days from acceptance.
- Secondary `radar-pair-v1` invite is purpose-specific and separate from birth-profile consent. B supplies B's own profile and may view or withdraw the pair result for its 30-day life: with the receipt, from B's own guest session without the receipt, or, withdraw only, by proving possession of the invite link (P09 D2). None of these paths collects new data or asks for B's birth data again.
- No current location, GPS, coarse discovery region, contacts import or numeric distance is collected for Radar.
- The API application-encrypts nickname and minimized relationship result. Coarse relationship context and voice are plaintext operational fields within the protected database. Nullable keyed HMAC retry/input digests are derived personal metadata, retained only with the Radar row, not anonymous data. Raw third-party DOB/time/place is not stored as a profile. `radar-result-v2` includes Pair Signature (since `radar-readable-v2`, 29/10/2026: a named tier without a number, three context areas with a level and coarse signal bands; earlier results: three interaction indicators), scenario copy, technical evidence receipts and provenance versions. These remain derived personal data; the change adds no collected field, recipient or purpose, so store declarations are unchanged. Capability and receipt tokens are hashed for lookup and protected by no-store/no-referrer/no-index public delivery. B's receipt (view/withdraw) lasts as long as the consented result, 30 days (owner decision P09 D1, 22/10/2026; was 7 days, which left days 8–30 without self-service).
- Both store disclosures must still include birth date/time and user-selected birthplace because server-side natal calculation receives them, including transient third-party input in private mode, even though Radar never shares those raw values.
- Pair results are derived personal data and should be disclosed as linked product-personalization/app-functionality data, not tracking.

## Deferred Vòng Lá matching release delta

- Matching is 18+ and must use the Play Console Restrict Minor Access control plus an in-app age gate appropriate to the final risk review. The existing birth-date validation alone is not represented as robust age assurance.
- `matching-v1` is purpose-specific and independently withdrawable. Withdrawal removes the user from active discovery immediately; account/guest deletion cascades profile, consent and verification rows.
- Matching stores only a coarse region code for discovery; it does not request current device location, GPS or numeric distance.
- Display name is application-encrypted at rest. Intent, self-declared gender/preference, age range, region bucket and verification state remain operational eligibility data and require restricted database roles, encrypted backups, retention and audit controls in deployment.
- Pre-mutual matching uses a minimized relationship-evidence projection. Raw birth date/time/place, chart payloads, mood, note prose and chat are prohibited from the ranker contract.
- Photo upload is not enabled until private object storage, moderation/verification processing, retry/appeal, deletion and store disclosures are implemented. Runtime must remain fail-closed; no development fixture may become a production auto-pass.
- Chat cannot launch without terms/community rules, filtering, in-app report, block, published support contact and an operational response queue.

Google’s “shared” definition and service-provider exceptions must be checked again before enabling any provider. Even when a processor transfer is not classified as store “sharing”, the privacy notice must still name the category, purpose, retention and destination accurately.

## External generation disclosure gate

The 2026-10-08 local pilot implementation adds explicit `external-content-rewrite-v1` personal
opt-in under `Mình`, default off. The disclosure names OpenAI, derived semantic summaries, no raw
birth/location/identity values or free-form Tarot questions, `store:false`, possible abuse-monitoring
retention (normally up to 30 days; longer when required by law or reasonably necessary to protect
the service or a third party from harm), and the limits of withdrawal. This does not authorize
Radar/Matching or another person's information. A UI choice is not evidence that the provider's
DPA/cross-border requirements have been completed. Production generation is still disabled.

2026-10-13 copy correction (Issue #7, local only): the opt-in and onboarding text now also name
the anonymous astrology labels that are sent (planet, sign, house, aspect), say that Tarot sends a
pre-classified topic instead of the question text, name OpenAI as a US company processing outside
Vietnam, and say that withdrawal cancels queued requests while already shown AI versions stay like
other readings. Still missing before activation: an App Privacy / Data Safety row for OpenAI as a
processor, DPA acceptance and a cross-border transfer impact assessment (Law 91/2025/QH15 Art. 20,
Decree 356/2025/NĐ-CP), and a decision whether to bump `external-content-rewrite-v1` if anyone
consented under the previous wording.

2026-10-13 retention wording (PR #11 review): both surfaces now state the full OpenAI exception
set for abuse-monitoring logs, checked against OpenAI "Your data" (Data retention controls for
abuse monitoring) on 2026-10-13: retained up to 30 days unless longer retention is required by law
or reasonably necessary to protect OpenAI services or any third party from harm. `store:false` does
not remove this retention; only an approved Zero Data Retention arrangement would. A shared constant
and test keep the two surfaces identical.

2026-10-13 companion field (local only): the `daily_home` payload also carries
`companion_meaning`, a fixed editorial brief from the content matrix chosen by the Daily issue key.
It is the same for every reader with that issue. It holds no personal data and nothing typed by
the user, and it does not change the consent scope above. Luna's returned `companion` line is
stored with the generated revision and deleted with it.

The new monthly reservation record has UTC month and conservative nanodollar debit only. It has no
owner identifiers or foreign keys. Preserve this anonymous aggregate after personal deletion to
prevent budget reset. This is not analytics, tracking, or retention of the deleted reading.

Provider generation may only move from `off` to `shadow` or user-visible exposure when all of these are evidenced:

- provider/DPA, subprocessors, inference region and cross-border route reviewed;
- retention wording states that `store=false` does not remove default abuse-monitoring retention; ZDR/MAM status is evidenced, not assumed;
- input allowlist canary proves no raw birth, coordinates, identity, session/chart IDs or free text leaves the API;
- output remains an unavailable candidate until local evidence, anti-influence, editorial and privacy gates pass;
- kill switch returns every surface to deterministic without invalidating saved/shared snapshots;
- Apple/Google disclosures and in-app privacy copy match the enabled environment.

Native release additionally requires the API host to be configured as the cookie domain. `__Host-` cookie names must not be combined with a `Domain` attribute; if the app later moves session credentials to Keychain/Keystore, this map and both store disclosures must be regenerated from the signed binary.

2026-10-20 M1 Daily payload without direct chart facts: the `daily_home` provider payload no
longer carries natal or transit evidence or the chart-selected first sentence of the meaning brief.
It carries Lá's shared catalog wording for the chosen situation and closed labels. The situation is
still chosen from the chart, so the payload reflects it coarsely; on a date-only reading it reveals
the Sun sign (one-to-one `SUN_ISSUES`), and nothing finer (no date, degree, other placement or
identifier). Our assessment, not legal advice, is that this cannot identify or help identify a
specific reader (Law 91/2025/QH15 Art. 2). `Settings` refuses rollout of every other surface,
because they still send chart-derived evidence. The opt-in copy in `Mình` and on `/privacy` says
what is sent (shared constant `OPENAI_REWRITE_SCOPE_NOTICE`) and that Tarot does not use AI yet;
the owner approved this copy on 2026-10-20.

Consent version: it stays `external-content-rewrite-v1` because the new wording **narrows** what
is sent. Whether production already holds v1 consents is not known from code: the consent endpoint
stores v1 even while generation is off, so "generation off" is no evidence that nobody opted in.
The owner either confirms the production state (a read-only count, only on the owner's instruction)
or decides on a version bump; no bump is required merely because the payload narrowed.

Store declarations: on the assessment above, OpenAI receives no personal data from Luna under M1,
so no new App Privacy / Data Safety category is added for it; re-check before any surface that
sends personal data is enabled. The app's own hosting abroad is unchanged by M1.

## Tarot meaning brief delta — local work, 2026-10-09

Tarot rewriting adds an allowlisted, locally authored meaning brief: selected topic,
intent, recognised goal codes, contextual summary and explicitly supported card links.
This is **derived personal content**, not anonymous data merely because names are absent.
It requires the separate external-rewrite opt-in. Raw questions, names, birth values,
coordinates and account/session identifiers remain excluded from provider input.

The provider boundary rejects a missing brief before transport. A failed local reading
gate keeps the selected cards but does not enqueue generation. A rejected rewrite keeps
the local reading; it does not trigger another paid attempt. Existing saved revisions
are not silently rewritten. `store:false` is not Zero Data Retention.

These are source-level controls, not proof of live deployment, legal compliance or
completed processor/cross-border arrangements. Text gates are heuristic, not a guarantee
that every generated sentence preserves meaning. Paid sample review remains a release gate.

## Reading voice delta — local work, 2026-10-11

The app vibe (`direct` or `roast`) is a device-local presentation preference. Daily sends it per
request as `GET /v1/daily-note?voice=roast` or the `voice` body field of
`POST /v1/daily-note/context`; the API applies it at read time and does not store, log or share it.
Stored revisions, share artifacts and saved snapshots stay direct. Tarot stores the effective voice
in the existing coarse `voice` column of the encrypted session row; sensitive questions store the
default voice. Roast Tarot readings are never enqueued for provider rewrite, so no new field or prose
reaches a third party. No new personal-data category is collected.

## Money context design delta — 2026-11-25, not implemented

Source of the design: [decision #709](../decisions/2026-11-25-goc-tien-bac-kien-truc.md). This section describes the selected future flow, not data already collected by the current release. #709 is documentation only, including the decision, this map, US-03/US-05 contract deltas and the review handoff. The API enum, flags, storage, consent and UI are not implemented here. Runtime work must default off; enabling new collection needs owner approval under R2. Existing birth-profile or external-AI consent does not authorize money context. All new user copy stays `status: pending` until approved; #709 writes no privacy/consent/crisis/safety sentences for the app.

### Inventory, purpose and recipients

The closed input is `background_lens = money` plus exactly one `money_situation`: `tuition_or_rent_shortfall`, `month_end_shortfall`, `family_remittance`, or `costly_social_invitation`. No amount, free text, debt, income, assets, family profile, new birth/location field or additional age document is requested or inferred. Sending money home or declining an expensive outing does not establish a shortfall. The choice changes framing and small actions only, with the same chart facts, evidence, precision and confidence. Scope is `DAILY_NOTE`; other reading purposes reject money at the shared application boundary. Money accepts absent/direct voice with deterministic rendering only; absent always becomes direct on the server, without inheriting a prior roast preference/setting. Roast is rejected with 422 before planning/enqueue. Legacy lenses retain their voice behavior. Public lens inputs are ContextProjectionRequest, ResonanceRequest, ExperimentChooseRequest and ShareArtifactRequest, all currently extra=forbid. Only context POST may accept a money situation; the other three must reject money and validate revision provenance, including a forged baseline lens. SavedNoteRequest separately accepts only a revision ID, forbids extra fields and allows money after owner/source/provenance, generation consent and flag checks; it is not subject to the three downstream DTOs' ban. Recheck the generated public contract in #711.

| Data | Purpose | Selected processing/storage and access | Retention / erasure |
|---|---|---|---|
| Lens and one money situation | Personalize this requested Daily reading | Private POST body and session/request memory; then only in existing owner-bound encrypted plan/revision envelopes. No URL, preference store or analytics. Neither the literal money lens nor situation/prose/financial labels may appear in any plaintext column of plan/revision/projection/saved-note tables; only encrypted envelopes and keyed identities | Choice is not reused by default on a later request. Encrypted revisions create a history of money circumstances while retained; lifecycle below |
| Derived money prose, normal and lighter actions | Display/replay exactly the accepted reading | Deterministic builder on the `apps/api` server, no LLM/AI. Private encrypted revision, owned response and memory only | With source revision; no extra retention from viewing or changing lens |
| Saved money reading | Explicit private save | Exact revision in the existing encrypted saved-note mechanism. Saved-list rows show only date and the identical approved neutral label used for baseline notes; no lens, money flag, financial label, prose snippet or money filter in this release. Detail requires current authorization. No plaintext money column or offline queue of money save IDs | Explicit save retains the revision and hidden root beyond the Daily 18–24-hour window, until unsave/withdrawal/profile or account deletion. Unsave removes the child/snapshot and prunes the root when no eligible child/current note remains |
| `lens_variant`, `scope_key`, `plan_key`, `revision_key`, with owner/profile/source/date linkage | Replay, deduplication, isolation and identity validation | HMAC-SHA-256 in existing identity columns with a dedicated versioned key ring, independent of guest_hash_key; provisioning requires owner authorization. Separate canonical formulas are in decision §4: lens binds owner/profile/consent generation only, scope also binds chart/date/purpose but excludes situation/content version; plan/revision bind the situation and their canonical content. Replay checks every retained key before inserting under a rotation-independent owner/profile transaction fence. Scheme/key_id stay encrypted; public versions reveal neither money nor a situation. No new situation index/dedupe table | With the corresponding plan/revision/projection. Derived, linkable personal metadata, not anonymous; repetition remains observable. DB plus key compromise permits guessing. No log, export, analytics or AI |
| Money consent receipt: owner, purpose `money_context`, immutable generation `E` (UUID id), approved version, `accepted_at`, `revoked_at` | Prove authorization for each generation and stop processing on withdrawal | One row per `(owner,purpose,E)` in `consents`, never overwritten by reaccept/upgrade. Version/accepted_at immutable; revoked_at set once. Current unique `(guest_id,purpose)` requires reviewed migration/repository changes in #935/#711. New writes use the current approved generation; reads/saves/export authenticate the exact E in the encrypted record against its unrevoked receipt and version rights, including older compatible versions. Upgrade never silently rekeys old saves. No situation, amount or revision in receipt | Active proof follows the authorized profile lifetime. Define finite justified L and maximum restorable-copy B before enabling. Purge only the revoked E by purge_at = revoked_at + L, without touching active E2. Every backup containing that receipt must expire and identifying markers be purged by D = revoked_at + L + B + six hours, after erasure/replay verification. Restore at/after purge_at must hard-delete the restored E1 receipt, even if snapshot says unrevoked; before that deadline reapply original revoked_at/purge schedule. Never restart L/B/D after restore/reaccept. Reconcile with Decree 356 Article 6 and owner-approved disclosure. Unknown bounds block enablement |
| Money withdrawal erasure marker: owner, purpose, E, original revoked_at, purge_at, D, HMAC scheme/key_ids | Re-apply generation-specific deletion after backup restore | Authenticated encrypted journal envelope under a dedicated journal encryption key, independent of DB snapshots, reading HMAC and guest_hash_key. No situation/prose or ambiguous root digest. key_ids cover every HMAC key that wrote E; keep independently recoverable key ring/old encoding and journal keys through all relevant backups and D. On restore enumerate all P from O's restored records/roots/saves, derive H(k,reading-lens/v1,[O,P,E,money]) for marker keys, match owner/lens, authenticate E and erase all dependent records/hidden roots. No plaintext money column or surviving receipt required; E2 never matches E1. Missing key/journal or incomplete coverage keeps traffic/jobs closed. Restricted access; new services/keys/access need owner authorization | Withdrawal fences and durably records a marker per revoked E before success; purpose withdrawal covers every unrevoked generation then present, not later reaccept E2. Replay exact-E receipt erasure at/after purge_at, including (purge_at,D], before traffic/jobs. Repeated restore retains original deadlines and cannot delete E2. The default 15 days is not proof; cover all restorable copies and purge identifying markers by D after verification |
| Export attachment containing the owner's still-exportable choice/prose/saved readings and minimal consent data | The person's access/provision right | Fresh private export, no retained server copy. Export/list/history/saved/read/write all share the withdrawal permission fence, checked again before response/file handoff. If withdrawal wins, cancel export and erase buffers/temp files; after withdrawal export contains no money data or pending money receipt. Exclude internal plans, identifiers, HMACs, tokens and others' data. Fixed filename; native app-private temporary cache, cleared after system sheet including cancel/failure | Temporary app copy follows export cleanup; a user-chosen file outside the app cannot be erased by withdrawal. Cleanup failure is not deletion success |

Application encryption does not remove personal-data status or store collection. The chosen design retains both the choice and prose; it must not be described as "money circumstances are never stored". It adds no separate preference history, financial analytics or adaptation. The no-storage and prose-only alternatives and their costs are in the decision. If implementation needs a situation or derived identifier outside existing lens storage, it must stop that part under AC2/condition 5 and record the owner gap. The minimal consent receipt is a separately inventoried new flow, not a place to store the situation.

The current map names Hetzner Germany and Supabase Frankfurt as infrastructure processors. The money design reuses the approved hosting flow, subject to confirming the release configuration and processor arrangements. Hosting outside Vietnam still requires cross-border review. No money input, prose, HMAC, queued job or derived context goes to AI/provider/third-party SDK, even with general AI consent on. No new processor or dependency is selected. The dedicated HMAC key ring and independent journal may require secret/access changes; those are unresolved owner actions, with collection off. No secret/IAM/service is provisioned by these documents.

### Downstream boundaries and device copies

| Path | Selected rule before enablement |
|---|---|
| Private POST, GET detail/history, GET saved list and detail, export and associated errors | Owner/source authorization with the shared withdrawal fence before every response/commit, and unconditional `Cache-Control: no-store`; identical policy for accounts with/without money, empty/baseline-only lists and flag off. Never query money presence to select a cache header. CSRF/trusted Origin for mutations/export, abuse limits, redacted validation errors. Remove unauthorized entries before pagination/count, no placeholders. Client cache disabled, no ETag/304 reuse |
| Client, WebView, web/PWA and native storage | Session/request-scoped memory only; clear/fence on session change, withdrawal or leaving flow. No Web Storage, IndexedDB, service worker, Capacitor Preferences or HTTP cache for money data, including derived pending-save IDs. Native cache/backup/temp files require separate MASVS/MASTG verification |
| Share link/image | Never share a money revision or its hook/manifestation/action. Rebuild the baseline from allowed source facts and preview it for explicit confirmation. Share row must not reference money; server checks actual revision provenance, including a forged non-money lens. Keep capability revoke/no-index/no-referrer/no-cache controls |
| Held experiment | Display money actions, but never persist their text/action key/money revision in held experiments. To hold a baseline action the user must open and confirm that baseline; never silently substitute |
| Resonance feedback | No feedback row for money, even with only a revision ID/digest; no feedback buttons on money, no reattribution to baseline. Baseline consent/TTL/reset/revoke remain as before |
| Logging, traces, errors and analytics | No situation, private prose, body, HMAC or exception containing them. No financial telemetry, tracking or advertising |

The proposed formal deltas in [US-03 §25](../user-stories/US-03-doc-note-hom-nay.md#25-delta-góc-tiền-bạc-2026-11-25) and [US-05 §21](../user-stories/US-05-luu-va-chia-se-note.md#21-delta-góc-tiền-bạc-2026-11-25) define the baseline preview, disabled money feedback/hold paths and server-only saved-note exception. Independent contract review and implementation tests remain required before enabling them; these documents do not silently waive existing AC or authorize collection. Privacy guards must check content leakage as well as DTO fields; removing `money_situation` alone is insufficient.

### Consent, withdrawal, retention and age

The consent work item [#935](https://github.com/honghanh153-creator/la-lanh/issues/935) exists, verified on 2026-11-25; no implementer has confirmed acceptance. Coordination must confirm an implementer and independent reviewer. It covers owner-approved copy/version, API accept/status/withdraw, UI disclosure before the first situation POST, multi-generation schema/rights, independent server checks, race protection, erasure/restore and tests. Receipt writes remain off until authorized. Refusal/cancel records zero rows and leaves the baseline usable. A receipt must prove which immutable approved version the person accepted; silence/client flags/birth-profile or AI consent are not enough. Reaccept/upgrade inserts a new E; compatible older unrevoked generations can retain read rights under the approved policy, without granting new purposes. Undefined version compatibility blocks the affected flow pending #935/owner disclosure.

Money withdrawal stops new processing and denies reads immediately, fences pending reads/writes/list/history/saved/export, and removes money plans/revisions, projections, saved money notes and dependent app copies. It leaves baseline/chart/account data intact. Retry cleanup failures without claiming completion; journal/replay requirements and exact-E receipt deadlines are inventoried above and specified in decision §6. Test export paused during file creation and before handoff; withdrawal must cancel it and clear temporary files. A response already completely delivered before withdrawal cannot be recalled. Reacceptance never revives deleted revisions. This erasure choice is a product policy requiring approved disclosure, not a claim that every legal withdrawal mandates immediate physical deletion. Technical flag-off blocks new consent/generation/regeneration/save, cancels uncommitted new writes, and clears unsent choices. It retains authorized read/reload/list/export/unsave/withdraw/delete without extending retention; it never silently switches an open reading to baseline. Existing saved records may replay their saved state, but no new save or recreation after unsave. Test pressing Save or resaving an unsaved note on an open money reading just as the flag turns off: no write, reading retained, state/message follows R15 with new copy pending in #710/#712 and never served before approval.

Keep backend and UI rollback floors for reading/history/saved. For old/unknown-capability clients, derive the full lens HMAC candidate set across retained key versions, all owner profiles and all record-bearing authorized generations (including compatible old versions). Exclude candidates and unauthorized/orphan rows in SQL before ordering/cursor/pagination/count; saved/projection queries join their revision/root identity. No hidden count or money placeholder. Missing keys/incomplete coverage denies the response; do not filter after pagination. #711/#712 must test multiple P/E/key versions, fewer/empty lists and cursor stability. Upgrade/web guidance depends only on client capability, identically for users with/without money; any new copy stays pending. A compatible web path for export/purpose withdrawal/unsave must work without requiring an app install/update before enablement. Old-client full export/account deletion must cover money server-side, independent of its filtered list; these rights paths still require implementation evidence.

Automatic Daily history remains visible at most 24 hours, eligible for cleanup from 18 hours once it is no longer today's note, on a six-hour job. Current notes and saved notes have existing profile-lifetime exceptions; this is not a proven 24-hour physical deletion bound. Money creates no share/experiment/feedback child, but it does create a saved_note child on explicit save. This child can keep a hidden root until unsave/withdrawal/profile or account deletion; it is an explicit long-lived exception, not a 24-hour bound. Withdrawal erases both saved snapshots and money hidden roots. Saved-list and detail endpoints must be no-store, neutral in list display, never queued offline and fenced on withdrawal. Legacy profiles without a clear effective retention policy cannot write money; do not accept history consent on the person's behalf. Viewing/changing angle does not extend retention. Backup/provider lifetimes and restoration are separate; incomplete evidence blocks enablement, even though no AI is called.

Keep the current product-wide 18+ restriction and server birth-date check at onboarding/correction. Tuition does not imply age. Test direct requests, legacy profiles and birth-date edits without adding age/guardian documents. Any expansion to minors requires separate owner-approved work. The distinction between children under 16 in Vietnamese law and the product's under-18 restriction was verified against Article 1 of official consolidated text 108/VBHN-VPQH on 2026-11-25.

### Proposed Apple App Privacy and Google Data Safety answers

These are explicit engineering classifications for the selected design when enabled, subject to current official wording and the signed binary. They do not modify the current release's store submission. Financial categories are a conservative project judgment about the four situations; neither store is asserted to name these codes specifically.

| Data | Apple category | Google category |
|---|---|---|
| Selected money situation | Financial Info → Other Financial Info | Financial info → Other financial info |
| Stored derived prose/reading and saved money content | Other User Content / Other Data Types, plus financial classification where the prose reveals circumstances | App activity → Other user-generated content, plus financial classification where it reveals circumstances |
| Linked metadata, private save state, minimal consent receipt/withdrawal marker | User ID; Product Interaction according to actual fields, with financial context where linkable | Personal info → User IDs; App activity → App interactions according to actual fields, with financial context where linkable |

| Property | Answer for the proposed enabled flow |
|---|---|
| Collected | Yes, after flag/consent/owner gates; off means no new money collection |
| Linked to You | Yes, including pseudonymous guest ownership; HMAC/encryption do not make it anonymous |
| Purpose | App Functionality and Product Personalization; receipt/erasure metadata supports consent and rights, not financial profiling |
| Tracking / advertising | No |
| Google Shared | No proposed store sharing; verify infrastructure recipients satisfy the service-provider exception. Hosting transfers still appear in privacy/cross-border records |
| Required / optional | Optional; baseline reading does not need money data |
| Ephemeral processing | No; the selected design keeps encrypted plans/revisions beyond the request |
| Encryption in transit | Required HTTPS/TLS; confirm the release environment before answering Yes in the console |
| Deletion | Existing profile/account paths plus money-specific withdrawal deletion; require implementation, concurrency and restore evidence before answering operationally complete |

### Privacy copy and official-source gate

`/privacy` needs an addition before enablement covering data types, purposes, processors/destinations, encrypted history, metadata, retention, withdrawal/erasure/export and downstream limits. This is an editorial requirement, not new privacy text. Owner approval and a verifiable separate consent flow are required. Store answers, manifests, disclosure and actual behavior must be reconciled before release.

Official sources were opened and checked on **2026-11-25**. The [decision §8](../decisions/2026-11-25-goc-tien-bac-kien-truc.md#8-nghiên-cứu-g1-và-nguồn-ac5) records the read sections and conclusions, including the alternate official Gazette text used for the scanned decree:

- [Law 91/2025/QH15](https://congbao.cdnchinhphu.vn/CongBaoCP/VanBan/2025/6/45578/57730-1-2025971-97291-2025-qh15.pdf), Articles 9–12, 20–22, 24 and 38. The design retains separate authorization and treats encryption as protection, not anonymization.
- [Decree 356/2025/NĐ-CP official metadata](https://vanban.chinhphu.vn/?docid=216387&pageid=27160), [signed scan](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/356-nd.signed.pdf), [readable official Gazette](https://congbaocdn.chinhphu.vn/180507251028987904/2026/1/17/cong-bao-so-18-ngay-18-01-46924signed-1768637757042330005940.pdf), Articles 4, 6, 17–20 and 41–42. Classification/proof/impact-record duties remain deployment prerequisites; do not assume a small-business exemption.
- [Consolidated Law on Children](https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/9/108-vbhn-vpqh.pdf), Article 1. Product 18+ remains stricter than the under-16 definition.
- [Apple App Privacy](https://developer.apple.com/app-store/app-privacy-details/) and [App Review privacy rules](https://developer.apple.com/app-store/review/guidelines/#privacy), data collection/types/use/linkage and 5.1.1–5.1.2. The retained flow is collected and linked; financial mapping is a project inference.
- [Google Data Safety](https://support.google.com/googleplay/android-developer/answer/10787469) and [User Data policy](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en), collection/sharing/types and disclosure/consent/deletion. Stored revisions are not ephemeral; the service-provider exception requires evidence of processor terms.

Source verification supplies AC4/AC5 research evidence, not operational compliance. Still required: official consent issue and accepted assignment; independent US-delta/final-commit review; owner-approved sensitive text, key/access provisioning and new collection; processing/cross-border records, actual backup/restore/receipt purge/native evidence and release/store reconciliation. Collection stays off.

## Official sources

### Rewrite erasure implementation, 2026-10-08

Migration 0030 links encrypted rewrite jobs to the authorizing guest and supported Reading, Tarot or Radar parent. Deleting either a guest or the parent removes the queued payload through database foreign-key cascades. Radar jobs for both perspectives share the same parent linkage. External-rewrite consent withdrawal invalidates the matching queued jobs in the consent transaction. Removing birth precision cancels pending Reading rewrites and erases affected Radar reports for both participants; unrelated birthless Tarot work remains available. A new Radar report requires recalculation with the remaining information.

The scheduled guest cleanup also removes unlocked rewrite envelopes older than 24 hours in bounded batches, including abandoned expired leases, while skipping active leased work. Anonymous conservative daily/monthly debit totals persist independently of personal-data erasure. They do not retain guest IDs, questions, chart facts or generated text. Admitted provider work can delay withdrawal acknowledgement until it finishes or times out. Already transmitted data remains subject to the provider's retention policy; do not promise immediate provider-side erasure.

These are source-level changes, not evidence of deployed configuration, completed store declarations or legal compliance. Check the live migration, retention schedule and provider arrangements before enabling paid rewriting. Vietnam's [Law 91/2025/QH15](https://congbao.chinhphu.vn/van-ban/luat-so-91-2025-qh15-45578.htm) is effective from 2026-01-01; this review checked official publication metadata, not a full legal assessment.

- Apple, App Privacy Details: https://developer.apple.com/app-store/app-privacy-details/
- Apple, Privacy manifest files: https://developer.apple.com/documentation/bundleresources/privacy-manifest-files
- Apple, Describing data use: https://developer.apple.com/documentation/bundleresources/describing-data-use-in-privacy-manifests
- Google Play, Data Safety: https://support.google.com/googleplay/android-developer/answer/10787469
- Google Play, User Data policy: https://support.google.com/googleplay/android-developer/answer/10144311
- Google Play, User-generated content: https://support.google.com/googleplay/android-developer/answer/9876937
- Google Play, incidental dating or matchmaking: https://support.google.com/googleplay/android-developer/answer/16838200
- Capacitor v8 configuration/cookies/http/security: https://capacitorjs.com/docs/config, https://capacitorjs.com/docs/apis/cookies, https://capacitorjs.com/docs/apis/http, https://capacitorjs.com/docs/guides/security
- OpenAI API data controls: https://developers.openai.com/api/docs/guides/your-data

## Account/history delta — 2026-10-10, not a store submission

**Google SSO update:** UI uses Google via Supabase PKCE, not phone/email entry. Supabase/Google process the login identity, including basic profile name/photo under the default profile scope. The app stores a verified subject UUID and masked email, not a profile photo. The encrypted short-lived PKCE verifier is consumed before code exchange. Code/state exist only transiently in callback memory after URL scrubbing; Supabase access/refresh and Google provider tokens never reach browser storage or become app authorization. No Gmail, contacts or birthday access is needed. Configure only openid/email/profile and verify the actual live consent screen before activation; source code alone does not prove provider settings. Login does not enable external AI consent. Flags stay off until provider identity erasure and live acceptance are complete. See [Google IAM](../architecture/account-iam-and-retention.md).

The local implementation adds optional managed email identity (Supabase subject UUID + masked email), independent hashed device credentials, encrypted short-lived email challenges and keyed quota digests. Provider access/refresh tokens, OTP, raw device secrets and device fingerprinting are not persisted as application content. New private account/history tables enable RLS and revoke public/browser-role grants; the server uses explicit ownership predicates.

Clocks and opt-ins: anonymous profile 30 days inactivity; linked account profile 365 days inactivity with `account-storage-v1`; device access 30 days inactivity; automatic history with `history-retention-v1`: Daily notes (with that day's mood, attached by FK cascade, and their Daily plans and rewrite revisions) are visible at most 24 hours after creation and become eligible for physical deletion from 18 hours once they are no longer today's note, so cleanup can remove them before 24 hours (owner decision 2026-10-20); a Daily note still referenced by an unexpired experiment, resonance feedback or unrevoked share link is kept hidden until those children expire, so they are not cascaded early. Physical deletion is scheduled, not a proven 24-hour bound (current-day exemption, six-hour timer, send fences). Other automatic history at most 30 days. The consent version stays v1: both windows stay within the "at most 30 days" it disclosed, and the copy now names the 24-hour Daily window and the child exemption. Today's note and explicitly saved notes are exempt. The first-link screen discloses account storage and history together and records both acceptances. Do not describe this as two independent switches in that flow. Legacy history remains opt-in with a full 30-day grace. Current chart/readings and explicitly saved notes follow profile lifetime. Access expiry/logout is not erasure. Restore never copies unrelated guest consent. Physical cleanup, backup expiry and provider-side copies have different lifecycles; no immediate erasure of every copy is certified.

On-device retries (audit P04, 2026-10-22): an offline mood check-in is kept in localStorage as `{session_epoch, note_id, mood, saved_at}`, labelled with the session that made the choice (a callback arriving after a session change or device clear stores nothing). It is replayed only for the same session and note before 24 hours from the **first** capture; a failed retry keeps that deadline instead of renewing it, and a later accepted choice clears an older waiting one and leaves a small `{session_epoch, note_id, acked_at}` marker (same 24-hour lifetime) so an older request failing later, even after Home was closed and reopened, stores nothing. Expired, other-session and old-format entries are removed whenever Home opens, online or offline. Offline saved-note intents hold only ids and a timestamp: `save` for 24 hours (the Daily note's lifetime), `unsave` for 30 days (a deletion request for a note that lives as long as the profile); each intent is rechecked (deadline and session) right before it is sent, and a direct save or unsave the server accepts retires older queued intents for the same note in either direction (judged by when each call started), and an older call for that note that fails afterwards queues nothing, in any tab: the accepted call leaves `{session_epoch, daily_note_id, acked_start, recorded_at}` in localStorage for one hour (no content or credential), and recording it and queueing a failed call are serialized across tabs with a Web Lock. Each such write first re-checks, inside the lock, that the same session and session generation still own the call and that the device was not cleared since it started; clear-device increments a counter (`la-lanh-saved-note-clears-v1`, a count only: no id, content or time) that each call captures when it starts, so a callback in any tab whose count changed cannot write note ids back afterwards, whatever the wall clock does. History deletion removes the pending mood and queued `save` intents but keeps queued `unsave` intents so the deletion still reaches the server; clear-device and guest erase remove everything, including those ordering markers (clear-device keeps only that counter). These are device copies, not server retention.

Share links and held experiments (audit P05, 2026-10-22): a share link gives 14 days of access; once it is revoked or expired it previews exactly like an unknown token, and the six-hourly cleanup (and history clear) physically deletes its encrypted snapshot row, including links made from a saved note. Live links are kept. Held experiments expire 29 days 18 hours after creation, so cleanup normally deletes them within 30 days. None of these is a hard physical bound: cleanup skips an owner while a rewrite send fence is open, and backups and provider copies follow their own lifecycles. In-app copy saying other history is kept "tối đa 30 ngày" describes expiry; whether it must also state the possible physical delay is an owner/counsel question (P10).

Lighter Daily action (#627, API and web, not released, no approved sentence yet): the Daily reading can carry a second, lighter action taken from approved catalog copy (`lighter.action.*`), picked from the revision id alone. The server does not read mood to build it and collects nothing new. When a person keeps the lighter action, the held experiment's encrypted payload also stores that catalog sentence (at most 120 characters), so the row shows that the lighter choice was kept; the row is the same held experiment as above, with the same undo, expiry and deletion. The data export lists experiments without their action text, as before. A saved note never stores the lighter action: the saved copy keeps the shape it had before this change, so an earlier release can still read it. Each card maps to one fixed catalog sentence (id and text digest pinned in code), so approving or adding other sentences never changes what an opened card offers. Web (#627 PR B): on a day whose saved mood is "Đuối", Home and the note page show the lighter action first, with a button back to the card's own action. A mood that is still being saved, or that failed to save, does not change the action. This is the first place the mood changes what the person sees; it stays inside the declared mood purpose (App Functionality, Product Personalization) and is not a health inference. The device decides which action to show from the saved mood it already reads; no extra copy of the mood is made. The person's press on the button (which of the two actions to show) is held in memory only (never in localStorage or sessionStorage), is not sent to the server or to analytics, and is dropped on history clear, with the other chart-derived data, and at every session change. No new request carries the mood; the note page reads the saved mood (the existing `GET /v1/daily-note/{id}/mood`) only when the reading has a lighter action to offer. Before release: decide whether the in-app privacy page needs a sentence about the mood changing the suggested action (privacy copy is the owner's).

Approximate-time Daily transits (US-21 Daily step 2, not released): a profile with an approximate birth time (a window, not a typed time) can now get a transit in its Daily plan, like an exact-time profile already does. Nothing new is collected or asked. The contact is derived on the server from the chart already stored and the day's sky. It counts only when it holds for every birth time in the window. To place that window, the server reads the time zone of the stored birthplace (the zone id only: no place name, coordinates or time), through the birth service, for the signed-in owner and the same profile, once per request and only for a Western chart with an approximate time. The zone is held in memory for that request; it is not stored again, logged or sent anywhere. When the lookup fails or there is no zone, the wide night window applies (fewer contacts qualify), never a guessed zone. The day's transit is chosen once from the chart, the day and the owner's rotation seed, without the lens and without the per-lens rotation guard, so the planner gives every lens the same factors and evidence (US-03 AC22); a lens changes only the scene and the action. This is tested through the reading service with the rotation on. The first lens opened for a day and chart decides the day's transit (or none). Every later lens repeats that decision from the owner's own stored plan of the same profile, day and chart, and does not calculate again; so a transit calculation or zone lookup that fails for one request and works for the next never gives two lenses different evidence. When a gate rejects one lens's reason sentence, that lens keeps the transit as evidence and loses only the sentence. These failure-and-recovery cases are tested through the reading service. One case is not covered: two lenses of the same day opened for the first time at the same moment, while one of the two requests fails; each then keeps what it was served. When the kept transit does not explain a lens's scene, it is listed as evidence without a reason sentence and the plan carries the marker `transit_reason_withheld` (a boolean, no personal data). The derived factor (transit body, aspect, natal body, worst-case orb, phase), the plan's `transit_policy` and that marker are stored inside the already-encrypted reading plan, with the same lifetime, history deletion, birth-data deletion, profile erasure and export exclusion as every other Daily plan ("internal reading/rewrite state" is never in the export). The rewrite provider payload never carries the orb (the slot is filtered as before, PV-28). The evidence shown in the app names the contact and phase without an orb number, because the stored orb is an upper bound. Exception logs on failure carry only the purpose, as before. The store data types do not change ("derived natal/transit factors").

Birth date correction (US-23, not released): a person can correct their birth date from Mình (`PUT /v1/birth-profile/date`). The same data types are collected, so the store forms do not change. The old date and everything derived from it (chart snapshots, plans, revisions, projections, Daily notes with their mood and feedback, experiments, Radar results and pending invites for both participants, queued rewrite jobs) are deleted in one transaction; time, place and deep consent are cleared and asked again. Saved notes and live share links the person chose to keep stay as frozen copies until they unsave or revoke them; Đã lưu now lists the person's own share links (id, format, status and dates only; never the token or content). A refused under-18/over-120 date is not stored or logged. A keyed counter (guest id and time only, 24 hours) limits corrections to 3 per day. The erasure journal records a data-free `birth_date_replaced` entry so a restore cannot bring the old subject back. Removing birth time or place still deletes every saved note and share link, as its confirmation states.

Deletion journal (audit P07, option A, owner decision 2026-10-22; deployed 2026-10-26 in release `89ebdb0cf6b9`): each explicit erasure or withdrawal (guest erasure, history clear (also the id of each Tarot session, human Tarot request and Radar result it actually removes), birth time/place removal or switch to an unknown time, Radar delete or withdraw, consent withdrawal including resonance and Vòng Lá matching; and, once batches 1 and 2 are released, Tarot session delete, share-link revoke, saved-note unsave, Lá Chứng invite revoke, response withdrawal, result hide and result delete, daily experiment undo and pending Radar invite revoke, each keyed by the row's own random id; and account device sign-out or revoke, keyed by the device row id, #206) appends `erasure_journal` {kind, keyed HMAC-SHA256 of the root id, closed scope such as the consent purpose, time}. No id, content, birth data or label is stored; the HMAC key is the existing server hash key. Purpose: after a restore, re-apply erasures made after the backup so restored copies cannot bring them back. Retention: 15 days by default (`LA_LANH_ERASURE_JOURNAL_RETENTION_DAYS`, at least the oldest restorable backup). Dumps carry the journal rows and a one-row purge horizon (a time only), which together mark which erasures each snapshot reflects, under the dumps' own 14-day retention; an hourly root-only host copy (`/opt/la-lanh/backups/erasure-journal/`, 0600, newest kept plus about two days of older copies) holds the same digests. These are pseudonymous personal data about the fact of a deletion, kept for the person's own erasure right; they are not shared, exported to any third party or used for analytics.

Linked-account erasure first commits a DELETING state that denies all device access, then drains already admitted external sends, hard-deletes the verified identity in Supabase Auth, and finally cascades local app data. A missing admin credential or provider failure returns a private pending error, not a success acknowledgement. Scheduled cleanup retries the same DELETING identity. Disabling new sign-in must not remove the erasure credential. Live provider deletion, database role/cleanup/backup verification and native store disclosures remain release gates; optional Auth delivery is off. This is not a production deletion or legal/store certification. See [Account IAM contract](../architecture/account-iam-and-retention.md).

## Daily rotation delta — B3-1a, 2026-10-17

Daily plans may carry `daily_variety`: a 128-bit HMAC of the profile ID under a selection-only key derived
from the server hash key, the note's calendar-day index, the catalog version, and the closed issue keys
served on the two previous days. It is derived data stored only inside the already-encrypted reading plan,
deleted with the profile, never logged, never returned by the API and never sent to a provider (allowlisted
payloads; covered by a test). No new data type, purpose, recipient or store declaration. The feature is off
until `LA_LANH_DAILY_VARIETY_FROM` is set.

## Tarot question frame delta — B2-1, 2026-10-17

Accepted Tarot questions get a `QuestionFrame`: closed labels for the question form, a scored topic
and an optional action label from a fixed 30-label table. It is derived from the question, stored only
inside the session's existing AES-GCM payload, and expires or is deleted with the session (at most 29 days
18 hours). It is never logged, never returned by the API and never sent to a provider; the Luna payload is
unchanged. There is no new data type, recipient or store declaration.

## Tarot variants delta — B2-4a, 2026-10-18

Each new Tarot session stores a `variants` record inside its existing AES-GCM payload: small integers that
pick the role frames, the lead offset and the headline frame. They are chosen once when the session starts
from an HMAC of the guest ID under the selection-only key derived from the server hash key (the same key
family as `daily_variety`) and the guest's session position. The seed itself is not stored. The record carries
no text, says nothing about the person, expires or is deleted with the session (at most 29 days 18 hours), is
never logged, never returned by the API and never sent to a provider.

The position comes from `tarot_variant_cursors`: one integer per guest (how many Tarot sessions the guest has
started), allocated in the transaction that creates a session so it never repeats after a reading is deleted
or expires. It holds no reading data, has row-level security enabled with no client grants, is never returned
or logged, and is deleted with the guest (foreign-key cascade; guest expiry and erasure remove it). No new
data type, purpose, recipient or store declaration.

## Tarot provider payload delta — B2-4b, 2026-10-18

Luna (the optional AI rewrite) stays off. If it is enabled later, the payload for a framed Tarot reading uses
meaning brief v3: besides the texts it already carried, it sends catalog codes for every text (role frame, lead,
scene, reflection, action) and the closed lean labels (kind, level, action label, option labels). Every string is
rebuilt from those codes and checked before a request is built; a string that traces to no closed label or
catalog code blocks the request. The question, the QuestionFrame, the variant record and the variant cursor are
never sent; lean conclusions and reasons stay local. No new data type, recipient or store declaration.

## Data export and B rights delta — 2026-10-29, not a store submission

- **Right of access / provision:** `POST /v1/session/data-export` (Mình > "Tải dữ liệu của tôi") returns the requester's own data as a JSON attachment: profile dates, linked account (masked email, device dates), consents, history retention, decrypted birth date, time mode/local time or window, place display name and timezone, chart result, visible Daily notes with mood, saved notes, share-link dates/status, unexpired Tarot questions and readings, the person's own unexpired, non-cancelled human Tarot requests (US-24: status, day, topic, spread, question while the app still keeps it, consent version/time, release time and the human reading once released; never the request code, Sheet row or state, or day tally), note feedback, experiments, A's own Radar and Lá Chứng side (nickname A typed, context, status, dates, A's attestation time), B's received Radar consent and dates, and Vòng Lá matching profile/consents/verification status.
- Never in the file: ids, hashes, digests, capability/receipt tokens, CSRF or session secrets, Radar result prose, Lá Chứng responder content, other people's birth data, birthplace centroid coordinates, rows the app already hides (expired Daily history, Tarot, Radar), internal reading/rewrite state.
- Delivery: built on request from a fresh read, not stored or cached server-side (`no-store`, `Pragma: no-cache`, `nosniff`, `no-referrer`, fixed filename `la-lanh-du-lieu-cua-toi.json`), CSRF + trusted origin, 5/min per peer. The web client hands the Blob to the device and keeps no copy; the Capacitor shell writes the JSON to the app's own cache directory with the official `@capacitor/filesystem` plugin, opens it with `@capacitor/share` (system share sheet), and deletes the temp file as soon as the sheet closes (saved, cancelled or failed); if that delete fails, the file stays only in the app-private cache until the OS or app clears it. Neither plugin sends data off the device. Real iOS/Android device testing is still required before release. No third party or SDK receives it, so Apple App Privacy and Google Play Data Safety answers do not change (no new collection or sharing). Play's "users can request data deletion" answer is unchanged; the export is an additional in-app right.
- **P09 D2:** B's self-service screens (session list/view/withdraw, used-invite withdraw, receipt) are in integration since #83; Mình and the privacy page now link B to them and explain what is held. B is never asked for birth data again. Inventory and open questions: [plan](../plans/2026-10-29-privacy-export-and-b-rights.md).
