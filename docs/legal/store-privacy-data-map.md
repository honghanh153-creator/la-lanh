# Lá Lành — store privacy data map

Last reviewed: 2026-09-26. This is an engineering disclosure map, not legal advice. Final answers must be reconciled against the signed release binary, production data flow, every SDK and the store console wording at submission time.

## Runtime posture

- Product target: Capacitor iOS/Android app; web is a companion and QA reference.
- Account: guest-first; a pseudonymous guest ID owns the profile before login.
- Tracking/advertising: none implemented.
- Analytics: none implemented for reading text, chart factors or personal fields.
- External content provider: production off by default. If enabled after governance, it receives only an allowlisted derived ReadingPlan; never raw birth values, coordinates, identity/session/chart IDs or free text.
- Planned web beta processor: Google Cloud using Cloud Run, Cloud SQL, Secret Manager, Artifact Registry, Cloud Scheduler and Cloud Logging. The default `asia-southeast1` region is Singapore, so Vietnamese-user data follows a cross-border route. Do not invite external testers until the applicable Law 91/2025/QH15 and Decree 356/2025/NĐ-CP review is evidenced and the user-facing privacy notice names the processor, destination, purposes and retention.
- Transport: production native build requires an absolute HTTPS API URL. Android cleartext and mixed content are disabled.
- Native session: authentication credential stays in a production `Secure` + `HttpOnly` API-domain cookie; only the separate CSRF token is persisted in app-local storage. Native requests carry a marker for origin handling, but still require the CSRF token and cookie.
- Deletion: in-app guest deletion removes first-party server records, exact saved/share revisions and device personal caches; generated attempts are tied to the same deletion epoch/cascade.

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

- Active scope is a private, known-person 1:1 Radar. Pool/discovery, 5 hidden cards, matching profile, mutual, chat and recap (US-14–18) are deferred and must not be declared as active runtime collection.
- Primary `private_check` lets A enter B's birth data only after attesting that B allowed this use. Raw B DOB/time/place is processed in request memory and must not be persisted, logged, cached, analyzed or turned into a profile. Only encrypted nickname/result and attestation timestamp/version remain for up to 30 days.
- Secondary `radar-pair-v1` invite is purpose-specific and separate from birth-profile consent. B supplies B's own profile and may withdraw the pair result.
- No current location, GPS, coarse discovery region, contacts import or numeric distance is collected for Radar.
- The API stores an encrypted nickname/context and encrypted minimized relationship result. `radar-result-v2` includes Pair Signature, three independent interaction indicators, scenario copy, technical evidence receipts and provenance versions; these are derived personal data even though raw birth inputs are absent. Capability and receipt tokens are hashed for lookup and protected by no-store/no-referrer/no-index public delivery.
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

Provider generation may only move from `off` to `shadow` or user-visible exposure when all of these are evidenced:

- provider/DPA, subprocessors, inference region and cross-border route reviewed;
- retention wording states that `store=false` does not remove default abuse-monitoring retention; ZDR/MAM status is evidenced, not assumed;
- input allowlist canary proves no raw birth, coordinates, identity, session/chart IDs or free text leaves the API;
- output remains an unavailable candidate until local evidence, anti-influence, editorial and privacy gates pass;
- kill switch returns every surface to deterministic without invalidating saved/shared snapshots;
- Apple/Google disclosures and in-app privacy copy match the enabled environment.

Native release additionally requires the API host to be configured as the cookie domain. `__Host-` cookie names must not be combined with a `Domain` attribute; if the app later moves session credentials to Keychain/Keystore, this map and both store disclosures must be regenerated from the signed binary.

## Official sources

- Apple, App Privacy Details: https://developer.apple.com/app-store/app-privacy-details/
- Apple, Privacy manifest files: https://developer.apple.com/documentation/bundleresources/privacy-manifest-files
- Apple, Describing data use: https://developer.apple.com/documentation/bundleresources/describing-data-use-in-privacy-manifests
- Google Play, Data Safety: https://support.google.com/googleplay/android-developer/answer/10787469
- Google Play, User Data policy: https://support.google.com/googleplay/android-developer/answer/10144311
- Google Play, User-generated content: https://support.google.com/googleplay/android-developer/answer/9876937
- Google Play, incidental dating or matchmaking: https://support.google.com/googleplay/android-developer/answer/16838200
- Capacitor v8 configuration/cookies/http/security: https://capacitorjs.com/docs/config, https://capacitorjs.com/docs/apis/cookies, https://capacitorjs.com/docs/apis/http, https://capacitorjs.com/docs/guides/security
- OpenAI API data controls: https://developers.openai.com/api/docs/guides/your-data
