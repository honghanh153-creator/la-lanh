# US01–US06 data inventory and privacy boundaries

Last reviewed: 2026-09-14 against the resolved Signal Note plan. This is an engineering inventory, not legal advice.

| Data | Purpose | Server | Device | Share/analytics | Retention and deletion |
|---|---|---|---|---|---|
| Guest session ID and hashed credential | Guest ownership without mandatory login | Session record; credential is hashed | Credential only in secure cookie, not JS storage | Never share; analytics not implemented | Inactivity expiry ≤30 days; guest deletion removes session-owned rows |
| CSRF token | Protect cookie-authenticated mutations | Verification material | Cookie + request header only | Never | Rotates/expires with session |
| Consent version, purpose, timestamp | Prove just-in-time, purpose-specific consent for `birth_profile_basic`, `reading-resonance-v1` and `action-experiment-v1` | Server consent ledger/session record; server time is authority | Never used as a local proof flag | Never public/analytic | Birth consent follows guest lifecycle; bounded-feedback consent follows its explicit reset/revoke/delete policy |
| Birth date | Compute Sun/date-only chart | Encrypted envelope; returned only to the authenticated owner in their private profile projection | Form memory only | Never public or analytic | Deleted with guest; user can delete all data |
| Birth time and precision | Optional Moon/Rising/House computation | Encrypted envelope | Form memory only | Never | Independently removable; deleted with guest |
| Place ID, display name, coordinates, timezone | Optional house computation | Encrypted/raw projection as defined by birth repository | Search input memory only | Never | Independently removable; deleted with guest |
| Chart snapshot | Deterministic note/reveal input | AES-GCM envelope tied to owner and record context; legacy plaintext is read-only migration compatibility | Not persisted as raw chart in browser storage | Never expose in public share or analytics | Deleted with guest; higher-precision snapshots are purged when time/place precision is withdrawn |
| `persona_mode` + `persona_label` | Compact `Vibe/Aura` presentation | Versioned Daily Note snapshot | In-memory display cache only; no persistent browser cache | Public card may include bounded label; no analytics until an approved analytics contract exists | Cleared on reload/session change; saved projection follows its separate policy |
| `awakening` + `sky_chapter` | Private multi-factor explanation and current transit×natal theme | Ephemeral private Daily Note response | In-memory only; never localStorage | Not included in share/public DTOs or analytics | Current page/session only; recomputed from active chart |
| Daily Note compact/full text | Core daily value, offline continuity | Owner-scoped AES-GCM snapshot; new writes leave only an empty legacy JSON placeholder | Compact/current note ≤36h; locally saved note ≤30d | Privacy-safe snapshot only; no raw birth data | Deleted with guest/server note; all current notes are purged when full birth precision is withdrawn |
| Context lens (`auto/work/relationships/communication/energy/self-care`) | Let the user choose the everyday framing of a Daily Note | Optional only inside an owner-scoped, encrypted, versioned reading revision needed to reproduce output | Current selection in component/query memory only; no preference in localStorage, IndexedDB, service worker or Capacitor Preferences | Never public/share/analytic; sent only in a private POST body, never URL/query/path | Memory state ends on reload/session change; any server copy follows its reading revision and guest-deletion lifecycle |
| Contextual manifestation and micro-action | Render the chosen everyday framing without changing chart evidence | Encrypted private reading revision/projection; private response is `no-store` | In-memory response only; do not persist contextual prose as a preference/history | Never public/share/analytic or logged | Deleted with reading revision/guest; not retained as behavioral history |
| Resonance feedback (`hit`/`miss`) | Optional feedback on the framing for app functionality/personalization | Owner-scoped encrypted row bound idempotently to note/revision and current lens | No local feedback history or retry queue; UI state may live in memory for the active screen | Not public, shared, logged or sent to analytics/third-party training; not tracking | `expires_at` ≤30 days from creation; reset deletes rows but keeps consent; disable deletes rows and revokes consent; guest deletion cascades |
| Aura transition acknowledgement | Remember “Giữ Note hiện tại” without hiding the available Aura | Owner-scoped opaque transition ID on the private reading projection | Optional opaque transition marker only as an offline fallback; deletion clears every prefixed key | Never public/shared/analytic and contains no birth or reading prose | Replaced by a new transition identity; deleted with projection/guest |
| Held experiment + outcome | Let the user keep one reversible action and optionally reflect on attempt/usefulness | One owner-scoped open row with immutable ID/version and note/revision/lens/action-key binding; bounded payload encrypted | Query memory only; no action prose/history in localStorage, URL, service worker or Capacitor Preferences | Never public/shared/logged/analytic; not evidence that astrology is correct | `expires_at` = 29d18h and mandatory cleanup runs ≤6h, keeping physical purge ≤30d; undo/outcome closes it; snapshot/revision/precision change and guest deletion cascade |
| Mood value and pending queue | User check-in and retry | Owner-scoped mood row | Pending `{note_id,mood}` only until sync/delete | No analytics implemented | Latest value per note; queue cleared on sync/delete |
| Saved-note snapshot | User-curated memory | Owner-scoped immutable AES-GCM snapshot, including exact reading revision | Up to 30 notes, each ≤30d | Never public unless user separately creates share artifact | Unsave/delete/TTL; all current saves are purged when full birth precision is withdrawn |
| Share artifact and opaque token hash | User-initiated sharing | AES-GCM privacy-safe projection, token hash, expiry, revoke state | Public URL only when user requests it | Public read-only projection with no-store/no-referrer/no-index controls | 14-day expiry or earlier owner revocation; guest deletion or precision withdrawal cascades |
| Theme and install-prompt preference | Device-only UX | No | localStorage, non-personal | Never | User/browser controlled; not removed as personal content unless all app preferences are reset |

## Boundary rules

- Server authorization always derives ownership from the verified guest cookie. A client-supplied resource ID never grants access.
- Every cookie-authenticated mutation requires trusted Origin and matching CSRF token.
- URL, referrer, application/proxy logs, crash breadcrumbs, metrics, PNG metadata and public share JSON must contain no birth date, time, place, coordinates, chart snapshot, guest credential or CSRF token.
- `Vibe/Aura` is derived personal data. It is not “anonymous” merely because it is a bounded enum. No analytics property is allowed until purpose, legal basis/consent, retention, deletion linkage and destinations are approved.
- Context is user-selected framing, not a chart fact or inferred profile trait. Changing it may alter only manifestation and micro-action; chart snapshot, selected/hero factors, evidence references, precision and confidence must remain unchanged.
- Resonance consent is distinct from birth-profile consent and Mood. The first `hit`/`miss` requires affirmative `reading-resonance-v1`; cancel writes nothing. `Đổi góc` is a no-write focus action and requires no consent.
- Resonance payloads are enum-only and owner/CSRF/trusted-Origin protected. They must not contain free text, note prose, raw chart/birth data or analytics identifiers, and they are not used for adaptive ranking, diagnosis or personality inference in this release.
- Experiment mutations accept only server-issued action identity plus note/revision/lens and CAS metadata. Client/user-authored prose is rejected; outcome is a closed enum and remains semantically separate from Resonance.
- Only one unresolved experiment may exist per guest. Replace/outcome/undo address immutable experiment ID/version; stale or cross-owner operations fail without exposing current owner state.
- Public share tokens require at least 128 bits of entropy, are stored only as hashes, expire, can be revoked by the owner and produce non-enumerating failures.
- Public/compute endpoints have an in-process admission backstop. Production must additionally provide distributed edge limits and redact capability paths before access logging; the application deliberately does not trust forwarded peer headers.
- Removing either birth time or birth place from a previously full-precision profile deletes every current Daily Note, saved snapshot, public share, generated reading revision and dependent held experiment before producing a new date-only result. The confirmation UI states this broad consequence before mutation.
- Web/PWA caches are a development/reference implementation. Native iOS/Android must use Keychain/Keystore for credentials and complete MASVS storage/network/privacy verification before release.

## Local deletion sequence

1. Server deletes the guest and all owned rows transactionally/cascade-safe, including consent ledger entries, encrypted reading revisions and resonance rows.
2. Client clears React Query/component state, context selection, resonance display state, daily/saved note caches, mood retry and supplement snooze state.
3. Client clears Lá Lành service-worker caches; they are app-shell-only and must never cache `/v1` responses.
4. Cookie expiry is confirmed by the server response; failure remains visible and local personal content is not falsely reported deleted.

## Signal Note release boundary

- Baseline `GET /daily-notes/today` remains context-free. Contextualization uses a private POST with a closed lens enum; unknown values and extra fields fail closed.
- Private Daily Note/context/feedback responses are `no-store`. Cache keys that exist in memory include context and revision so a stale cross-context response cannot be presented as freshly generated.
- Store disclosures must describe resonance as linked Product Interaction used for app functionality/personalization and not tracking, subject to final platform/legal review. Any SDK, training use, advertising use or adaptive ranking requires a new inventory and consent decision.
- Capacitor iOS/Android are the release products. App release requires Keychain/Keystore credential handling, privacy-manifest/data-safety reconciliation, log/cache inspection and actual native lifecycle smoke; web is QA evidence only.
