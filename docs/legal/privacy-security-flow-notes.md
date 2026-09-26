# Privacy and security flow notes

Sources checked again on 2026-09-14:

- Vietnam Law 91/2025/QH15 on Personal Data Protection and implementing Decree 356/2025/NĐ-CP are effective from 2026-01-01 and are the primary release baseline. Older implementation context applies only where consistent with them. Legal counsel must map the final controller/processor, data-subject rights, impact-assessment and cross-border duties to the deployed architecture.
- EDPB GDPR SME guidance: consent should be freely given, specific, informed, unambiguous, and easy to withdraw.
- FTC COPPA guidance: apps with actual knowledge they collect personal information from children under 13 need verifiable parental consent before collection unless a narrow exception applies.
- Apple App Store privacy details and Google Play Data safety guidance: collected app data, purposes, linkage, tracking, retention, security practices, and every third-party SDK must be declared for store submission.
- Android security guidance requires encrypted transport; release builds prohibit cleartext traffic. OWASP MASVS remains the mobile verification baseline for storage, auth and network controls.
- Reading knowledge is static product content. It may consume only derived, allowlisted chart factors server-side; raw birth input, coordinates and reading prose remain excluded from logs and analytics. Adding deterministic matrix synthesis under the already disclosed “calculate and interpret your chart” purpose does not authorize unrelated training, advertising or matching reuse.
- External prose generation is fail-closed twice: deployment governance must enable it and the individual request must carry a current, purpose-specific authorization. Without both, no derived chart factor is queued for a third-party provider. Withdrawal/deletion must invalidate queued work before delivery.

Official sources:

- https://vanban.chinhphu.vn/?docid=214590&pageid=27160
- https://vanban.chinhphu.vn/default.aspx?docid=216387&pageid=27160
- https://developer.apple.com/app-store/app-privacy-details/
- https://developer.apple.com/app-store/user-privacy-and-data-use/
- https://developer.apple.com/documentation/bundleresources/describing-data-use-in-privacy-manifests
- https://developer.apple.com/app-store/review/guidelines/
- https://support.google.com/googleplay/android-developer/answer/10787469
- https://developer.android.com/privacy-and-security/risks/cleartext-communications
- https://mas.owasp.org/MASVS/
- https://mas.owasp.org/MASVS/12-MASVS-PRIVACY/
- https://mas.owasp.org/MASVS/controls/MASVS-STORAGE-1/
- https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- https://capacitorjs.com/docs/apis/preferences

Product decisions for the MVP:

- The app does not require login before the birth reveal. Account creation remains deferred until matching/social actions.
- Consent is explained and recorded immediately before the birth-date form. It is a short, just-in-time data step—not an account wall—and the user can leave without submitting personal data.
- The app clearly states data category, purpose, storage, protection, retention, and deletion path before submission.
- The client blocks birth dates indicating a user under 18 before sending the date to the API. A separately reviewed age-assurance and parent/guardian flow is required before supporting minors.
- Birth date must not appear in URL, cookie, local storage, analytics payloads, or logs.
- Guest token remains HttpOnly; CSRF token is separate and checked with trusted origin on mutations.
- Raw birth input, every new chart snapshot, Daily Note, saved-reading snapshot and share projection are encrypted at rest with record-bound AES-GCM context; the API decrypts them only server-side for an authorized purpose. Transitional legacy JSON columns stay read-compatible only until a key-aware backfill or approved purge is verified.
- Lá Chứng owner mutations require trusted Origin, guest CSRF proof, owner session and matching source guest. Public capability responses are no-login and deliberately reveal the same terminal state for expired/revoked/responded links.
- Web/public link delivery adds no-referrer, no-store on capability routes, CSP, restrictive permissions policy and no-index deployment headers. The hosting platform must be verified to honor `_headers`.
- Capability routes validate token shape before storage lookup. Guest creation, chart compute and capability traffic have an in-process admission backstop; production still requires a distributed edge control and capability-path redaction.
- Withdrawing birth time or place from a full profile removes current notes, saves, shares and generated revisions before regenerating a date-only experience. The app asks for explicit confirmation and retains only birth date unless the user deletes the whole guest profile.
- Android release source disables backup and cleartext traffic. HTTPS is a hard release requirement.
- App store submission needs privacy labels/data safety answers for birth date, guest identifier, app interactions, diagnostics, and any future analytics/SDKs.
- Every reading revision records content/rules/knowledge/gate versions, while UI/cache receives only the minimum projection and bounded evidence disclosure. The always-visible short disclaimer preserves user agency without repeating a large warning card in every section.

Signal Note decisions for the 2026-09-14 release:

- Entry is a three-act app flow `00/02 consent → 01/02 DOB → 02/02 reveal`. Birth-profile consent is recorded before any DOB field/request. Decline creates no guest/profile and opens a fixed, labelled non-personalized demo.
- DOB remains volatile until private submit and is prohibited from URL/history, browser persistence, logs, crash reports, analytics and public/share artifacts. Successful create is idempotent; reveal reuses its cached snapshot instead of requesting it again.
- Context uses the closed enum `auto/work/relationships/communication/energy/self-care` in a private POST body. It is a user-directed framing choice, not an inferred trait: only manifestation and micro-action may change; chart facts, selected factors, evidence, precision and confidence are invariant.
- Client context is memory-only by default and must not become a localStorage/IndexedDB/service-worker/Capacitor Preferences preference. A server copy is permitted only in an owner-scoped, encrypted, versioned reading revision needed for reproducibility. Private responses are `no-store`; context and contextual prose stay out of public/share DTOs and analytics.
- `Trúng`/`Chưa trúng` are a separate purpose from birth data and Mood. First use requires disclosure plus affirmative consent version `reading-resonance-v1`; cancel/decline writes nothing and does not reduce access to the Note.
- Resonance stores only `hit|miss`, current lens, note/revision identity and server protocol metadata. No free text, raw chart/birth input, note prose, inferred personality or analytics identifier is permitted. Writes are owner-bound, CSRF/trusted-Origin protected, enum/extra-field validated, idempotent and encrypted at rest.
- Resonance expires within 30 days. `Reset feedback` deletes rows and keeps current consent; `Tắt phản hồi` deletes rows and revokes consent; whole-guest deletion cascades feedback, consent and reading revisions. `Đổi góc` stores nothing and only focuses Context Dial.
- Resonance is not evidence that astrology is true and is not used for adaptive ranking, diagnosis, personality inference, advertising, tracking or third-party model training in this release. A new use requires a separate purpose, inventory, legal review and consent decision.
- Store declarations should classify the bounded resonance event as data linked to the user/guest and used for Product Interaction/App Functionality and personalization, not tracking, subject to final Apple/Google form wording and legal review.
- Native app release requires iOS Privacy Manifest/App Privacy and Android Data Safety alignment with actual runtime, Keychain/Keystore credential handling, no sensitive device backup/log/cache leakage, synced Capacitor assets and real iOS/Android lifecycle smoke. A web-only pass or missing native toolchain is a release No-Go.

Aura experiment decisions for the 2026-09-16 release:

- Aura readiness and active Note are separate. Exact time/place may make the profile Aura-ready, but only an explicit activation changes today’s Note; keeping the current Note is durably acknowledged without hiding the available update forever.
- The experiment API accepts no user/client-authored prose. Action text, observation cue and stop permission are server-owned output bound to an accepted reading revision; writes carry only closed identity/version/lens/outcome fields.
- The first `Giữ để thử hôm nay` is an affirmative just-in-time action for `action-experiment-v1`; cancel writes neither consent nor row. Undo removes the row but does not pretend consent was revoked; whole-guest deletion removes both.
- All experiment mutations require owner session, trusted Origin, matching CSRF and stale-write protection. One unresolved experiment exists per guest; replace/outcome/undo use immutable ID/version and never last-write-wins silently.
- Experiment data is private, encrypted, no-store and excluded from URL, logs, analytics, crash breadcrumbs and public/share artifacts. Rows expire at 29 days 18 hours and the mandatory six-hour cleanup schedule in `docs/operations/aura-experiment-retention-runbook.md` keeps physical retention within 30 days; chart-snapshot change or birth-precision withdrawal removes dependent experiments.
- Outcome measures attempt/usefulness/fit only. It is not Resonance, proof of astrology, personality inference, adaptive ranking, diagnosis, advertising, tracking or training data.

Vòng Lá decisions for the 2026-09-17 foundation:

> **Deferred on 2026-09-20:** pool/discovery, 5-card cohort, mutual, chat and recap are no longer active MVP routes. The controls below remain requirements if US-14–18 resume; they do not describe the current Radar runtime.

- Vòng Lá is a hard social trigger. Guest Daily Note remains usable without login; device-bound owner claim is only an internal ownership bridge and is not represented as complete phone/email authentication or account recovery.
- Matching profile, matching consent and verification are separate records. Consent `matching-v1` is explicit, versioned and withdrawable; withdrawal atomically disables active pool membership while preserving an immutable grant/revoke audit trail.
- Eligibility is fail-closed: 18+, profile Level 3, matching profile, active consent and verification pass are all required. Production has no endpoint or environment flag that auto-passes photo verification.
- Display name is encrypted with record-bound application context. Coarse region, intent, self-declared gender/preference, age range and verification state are operational matching fields; they remain personal data and require least-privilege database access, encrypted storage/backups and a documented retention schedule.
- No device GPS, numeric distance, mood, note prose, chat, popularity or scalar compatibility score may enter candidate selection. The selector receives only authorized, minimized relationship dimensions/evidence after reciprocal hard filters and block/safety checks.
- Before mutual, only Synastry evidence may explain a card. Composite is a post-mutual bonus; Davison requires exact time/place for both users and incremental consent. Missing precision always downgrades rather than guesses.
- Apple and Google UGC rules make filtering, report, block, moderation response and published support contact release blockers for chat. Google’s matchmaking controls also require a robust minor-access safeguard and 18+ store configuration.
- Account deletion must remove/irreversibly anonymize matching profile, verification assets, requests, mutual/chat content and shared recap projections unless a documented legal retention duty applies. Provider-side deletion must be evidenced, not assumed.

Radar hợp gu decisions for the 2026-09-20 active MVP:

- Radar compares one known pair and is not discovery. Primary mode allows A to enter B's birth information only after an explicit permission attestation; the raw fields are calculated transiently, never stored as B's profile, and never expose B to a pool.
- A requires an exact chart in their encrypted profile. B's exact time/place in private mode exists only in request memory. The local Vietnam index avoids a third-party geocoder and asks for no GPS permission.
- `radar-result-v2` stores only a minimized Pair Signature, three independent evidence-derived indicators, scenario sections, evidence receipts and version metadata. It stores no raw date/time/place/coordinates and makes no external prose-generation call.
- `Bắt sóng`, `Dễ phối hợp`, `Lực cấn` are UI indices within one pair, not a total compatibility score, success probability or candidate-ranking feature. They must never feed discovery, safety, consent or intent decisions.
- “Kín” means no app invitation or notification, not permission to process data secretly. The attestation is an accountability gate, not conclusive legal proof; public release requires counsel review under Law 91/2025/QH15 and Decree 356/2025/NĐ-CP.
- When A lacks permission, the fallback link previews purpose and rights. B must grant separate `radar-pair-v1` consent; birth-profile consent alone is insufficient.
- The capability token is sensitive-by-capability: 256-bit random, shape-validated, hash-indexed, seven-day TTL, revocable, no-store/no-referrer/no-index and prohibited from analytics/logging/localStorage.
- Accept requires active guest, trusted Origin and CSRF. The server computes synastry/composite from encrypted inputs and stores only an encrypted minimized multi-dimensional result; raw birth inputs and chart payloads are never returned to the other person.
- No scalar compatibility percentage, candidate rank, soulmate/red-flag verdict or inference about intent, consent, abuse or safety may be generated.
- B receives a short-lived HttpOnly receipt to withdraw. Withdrawal deletes result ciphertext and makes A's result unavailable.
- Before public launch, add distributed idempotency, automated TTL purge, capability-path log redaction evidence, abuse report/block operations and native Universal/App Link QA.

Open gates before public release:

- Legal review for Vietnam personal data impact assessment and any cross-border data transfer duties under Law 91/2025/QH15 and Decree 356/2025/NĐ-CP.
- Age-assurance and verifiable parent/guardian consent design if the product later supports users under 18.
- Apple Privacy Nutrition Label and Google Play Data Safety form based on the final SDK inventory.
- Swiss Ephemeris licensing decision remains blocked by `docs/legal/swiss-ephemeris-release-gate.md`.
- Production hosting must prove CSP/security headers on HTML (not only JSON), redact capability URLs before edge/application logs and apply shared rate limits to public preview/submit/report routes and expensive chart computation.
- Existing development chart/daily/saved/share rows must be migrated by a key-aware job or deleted before plaintext compatibility columns are removed; migration rollback is intentionally blocked while ciphertext would otherwise be discarded.
- Data inventory, privacy policy, consent copy, iOS App Privacy/Privacy Manifest and Android Data Safety must all match final context/resonance runtime behavior and third-party SDK inventory.
- Production must configure and verify the six-hour bounded experiment/resonance cleanup schedule; missing or stale cleanup is a release No-Go.
