# Aura Awakening + Sky Chapter — implementation review

Date: 2026-09-06  
Scope: US-03 + US-06 bridge into US-07; web companion implementation, with native app parity still required.

## Delivered vertical slice

- A successful exact time/place supplement invalidates both the server query and local note fallback before fetching the new note.
- A complete NatalChart receives a genuinely different Aura note assembled from Sun, Moon, Mercury, Venus, Mars and the dominant whole-chart element instead of reusing Sun-only copy.
- The engine calculates transit-to-natal geometry at the daily 12:00 UTC observation anchor and returns body pair, major aspect, orb and phase (`approaching`, `exact`, `separating`). The anchor keeps a Daily Note stable throughout its date.
- A versioned first-pass salience score combines normalized exactness, transiting-body duration weight and natal-target weight; the selected personal-planet contact becomes a private “Sky Chapter” bonus after Aura reveal and a compact continuing card on Home/detail.
- The API projection contains no raw birth date, time, place, coordinates, guest token or CSRF value. Share DTOs remain unchanged and do not receive awakening/chapter fields.
- Daily note fallback moved from persistent `localStorage` to memory-only storage; old plaintext cache is deleted during cache clear.

## Truthfulness gates

- Sky Chapter is only produced for `TimePrecision.EXACT`. Approximate/unknown time never receives an exact transit-to-natal chapter.
- Phase is a directional state at the note's documented daily anchor, determined by a real one-hour forward ephemeris recompute. The product does **not** claim a solved start date, exact-hit timestamp, end date or multi-pass retrograde sequence.
- Copy says “gợi ý chiêm nghiệm”, not prediction, diagnosis or professional advice.

## Engine gaps found — not hidden

| Severity | Gap | Product consequence | Required next work |
|---|---|---|---|
| Blocker for full “Sky Chapters” | No root solver for orb entry/exact/exit and no retrograde multi-pass grouping | Current UI can show one truthful phase, but not a calendar chapter with verified start/peak/end | Add ephemeris search/root finding, pass grouping and golden fixtures |
| Blocker for approximate-time Aura | Approximate birth window is collapsed to a midpoint before chart calculation | Aura and Sky Chapter are now withheld; the user remains on Vibe until stable factors can be proven | Sample the whole uncertainty interval and expose only stable factors |
| Major | Aura scoring v1 weights planet classes across element and modality, but omits chart ruler, houses, aspects and explicit numeric confidence | The compact label is no longer raw-element-only, but does not yet meet the final Aura-v2 formula | Extend the versioned factor plan and expert-review its weights before calling it Aura-v2 |
| Major | Salience v1 only combines exactness, transiting-body class and natal target | It avoids “smallest orb wins”, but still lacks angularity, repetition, verified duration windows, domain relevance and confidence | Complete the factor-plan formula and expert-review its weights |
| Major | Transit facts are computed on request, not persisted as immutable reproducible snapshots | Same-day retrieval remains correct but there is no historical chapter audit trail | Add private snapshot identity/provenance and retention policy before history/recap |
| Release gate | Native app screens and secure device storage are not implemented | Web is only the runnable companion, not the promised final app | Rebuild the same contract/screens in SwiftUI/Android and verify platform keystore/data protection |

## Security and privacy review

- The new rich interpretation stays behind the private guest session and is not copied into public share artifacts.
- Populated Aura/Sky canary values are covered by a share-projection regression test, rather than testing only null rich fields.
- Persistent browser storage is not used for the rich note/chapter. This follows OWASP MASVS guidance to minimize local sensitive-data retention and remove caches when no longer needed.
- Offline saved-note storage uses an explicit display-card allowlist. Legacy entries are rewritten on read so `awakening`, `sky_chapter` and `full_body` do not remain in plaintext localStorage.
- Removing birth time/place now clears both the private memory fallback and the active Daily Note query before profile data is refreshed.
- Guest expiry and creation of a replacement guest clear personal memory/query/device state, preventing one guest from inheriting another guest's Aura in a long-lived SPA.
- Sanitized saved-card snapshots still remain in localStorage for offline web continuity. They exclude the new rich fields but remain a shared-device residual; native release should use owner-scoped protected storage or authenticated server state.
- Consent remains purpose-specific at the deep-birth step; hour/place remain encrypted server-side and are absent from URLs, logs and analytics fields reviewed in this slice.
- Vietnam Law 91/2025/QH15 has been effective since 2026-01-01; production launch still requires qualified legal review, data-processing impact records, processor/cross-border mapping and verified subject-access/deletion operations.

## Primary references checked

- Swiss Ephemeris 2.10 programmer/reference documentation: https://www.astro.com/ftp/swisseph/doc/
- Swiss Ephemeris transit definition and coordinate conventions: https://www.astro.com/swisseph/swisseph.htm
- OWASP MASVS Storage: https://mas.owasp.org/MASVS/controls/MASVS-STORAGE-1/
- OWASP MASVS Privacy: https://mas.owasp.org/MASVS/12-MASVS-PRIVACY/
- Vietnam Law on Personal Data Protection 91/2025/QH15: https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=

## Verification evidence

- API suite: 74 passed. Coverage includes natal reference positions, transit-specific orb limits, explicit phase branches including retrograde motion, naive-datetime rejection, approximate-time Aura/chapter denial, same-day chapter stability, multi-factor Aura sensitivity, versioned policy provenance and populated-rich-field share sanitization.
- Web unit suite: 12 passed. Coverage includes non-persistent note caching, TTL expiry, saved-card allowlisting and legacy rich-entry sanitization.
- API/web lint and typecheck pass; production web build passes. The exact time/place browser flow passes on mobile and desktop.
- Residual QA: unrelated Welcome visual snapshots still target the retired design, one pre-existing desktop primary-flow assertion is intermittent, and the production bundle warning remains approximately 591 kB before gzip.

## Code-review resolution

The final correctness, API, testing, performance, maintainability, project-standard and adversarial privacy passes found no remaining P0/P1 in this feature after fixes. Applied changes include transit-specific orbs, real forward ephemeris phase comparison, daily stability, bounded config-isolated sky caching, approximate-time withholding, multi-factor Aura scoring/provenance, session-boundary clearing, saved-note allowlisting and populated share canaries. The engine and native-release gaps above remain explicit release gates rather than being represented as finished.
