# Lá Lành — store privacy data map

Last reviewed: 2026-10-09 (local engineering delta). This is an engineering disclosure map, not legal advice. Final answers must be reconciled against the signed release binary, production data flow, every SDK and the store console wording at submission time.

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
| Other User Content | Radar nickname/context, permission attestation and minimized relationship result | Yes | Private mode: owner only; invite mode: invited pair | App Functionality, Personalization |

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

- Intended public scope is a private, known-person 1:1 Radar. Pool/discovery, 5 hidden cards, mutual, chat and recap (US-14–18) are deferred. Legacy matching routes are still mounted; do not claim their collection is impossible until they are disabled or separately assessed at deployment.
- Primary `private_check` lets A enter B's birth data only after attesting that B allowed this use. Raw B DOB/time/place is processed in request memory and must not be persisted as raw inputs, logged, cached or turned into a profile. Retained fields include encrypted nickname/result, attestation timestamp/version, coarse context/voice and keyed retry metadata, for up to 30 days of result access. Scheduled physical deletion and backup expiry are separate lifecycle checks.
- Secondary `radar-pair-v1` invite is purpose-specific and separate from birth-profile consent. B supplies B's own profile and may withdraw the pair result.
- No current location, GPS, coarse discovery region, contacts import or numeric distance is collected for Radar.
- The API application-encrypts nickname and minimized relationship result. Coarse relationship context and voice are plaintext operational fields within the protected database. Nullable keyed HMAC retry/input digests are derived personal metadata, retained only with the Radar row, not anonymous data. Raw third-party DOB/time/place is not stored as a profile. `radar-result-v2` includes Pair Signature, three independent interaction indicators, scenario copy, technical evidence receipts and provenance versions. These remain derived personal data. Capability and receipt tokens are hashed for lookup and protected by no-store/no-referrer/no-index public delivery.
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

2026-10-20 M1 chart-free Daily payload: the `daily_home` provider payload no longer carries
natal or transit evidence or the chart-selected first sentence of the meaning brief. It carries
only Lá's shared catalog wording for the chosen situation and closed labels, which cannot identify
or help identify a reader (Law 91/2025/QH15 Art. 2; our reading, not legal advice). `Settings`
refuses rollout of every other surface, because they still send chart-derived evidence. The
opt-in copy in `Mình` and on `/privacy` now says exactly this (shared constant
`OPENAI_REWRITE_SCOPE_NOTICE`) and states that Tarot does not use AI yet. The consent version stays
`external-content-rewrite-v1`: the new wording narrows what is sent, and production had no opt-ins
because generation was off. Store declarations: OpenAI receives no personal data from Luna under M1,
so no new App Privacy / Data Safety category is added for it; re-check before any surface that sends
personal data is enabled. The app's own hosting abroad is unchanged by M1.

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

Clocks and opt-ins: anonymous profile 30 days inactivity; linked account profile 365 days inactivity with `account-storage-v1`; device access 30 days inactivity; automatic history max 30 days from creation with `history-retention-v1`. The first-link screen discloses account storage and history together and records both acceptances. Do not describe this as two independent switches in that flow. Legacy history remains opt-in with a full 30-day grace. Current chart/readings and explicitly saved notes follow profile lifetime. Access expiry/logout is not erasure. Restore never copies unrelated guest consent. Physical cleanup, backup expiry and provider-side copies have different lifecycles; no immediate erasure of every copy is certified.

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
