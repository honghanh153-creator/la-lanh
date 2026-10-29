# Privacy: "Tải dữ liệu của tôi" and B's rights screens (29/10/2026)

Branch `feat/privacy-export-and-b-rights`, from `collab/integration` at `e0d62fa`. Owner order
"làm hết 1 lượt đi"; registry P09 "data export decision" = build it. Engineering record, not legal
advice.

## Scope

1. **Data export (right of access / provision of data).** `POST /v1/session/data-export` returns the
   caller's own data as one JSON file. Mình > Dữ liệu & quyền riêng tư > "Tải dữ liệu của tôi".
2. **P09 D2 web screens for B.** Already built in #83 (`/radar/received`, `/radar/received/:id`,
   withdraw on `/radar/i/:token` after use, receipt page) and merged into integration at `288a535`.
   A's delete path already exists on the owner result page and both Radar histories. This branch adds
   only the missing entry points and disclosure: a link from Mình, a "Lá đang giữ gì về bạn ở đây?"
   block on `/radar/received`, and two privacy-page entries. No API change was needed for D2.

## API contract

| | |
|---|---|
| Method / path | `POST /v1/session/data-export` (tag `privacy`) |
| Auth | guest session cookie + `X-CSRF-Token`, trusted `Origin` (or the native `X-La-Lanh-Client` marker, which still needs the CSRF token) |
| Success | `200`, body `DataExport` (strict, `extra="forbid"` at every level) |
| Headers | `Cache-Control: no-store, max-age=0`, `Pragma: no-cache`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Content-Disposition: attachment; filename="la-lanh-du-lieu-cua-toi.json"` |
| Errors | `401` no/expired session, `403` bad CSRF or origin, `429` admission limit (`Retry-After`) - all problem+json, no data |
| Rate limit | admission policy `data-export`: 5 per minute per peer, 60 per minute global (rejected attempts count) |
| Size | each list holds the newest 500 items; a cut list is named in `truncated` |

Why POST: the file is a bulk disclosure. A GET with a `SameSite=Lax` cookie can be triggered by a
cross-site top-level navigation, a link prefetcher or a crawler; POST with the CSRF token and a
trusted origin cannot. The browser never caches it, and the web client does not keep it in React
Query or Web Storage.

## Data inventory

Every table with personal data was read (`apps/api/app/domains/*/tables.py`).

### Included

| Section | Fields | Source |
|---|---|---|
| `profile` | state, onboarding status, created, last active, expiry | `guest_sessions` |
| `account` | masked email, linked at; devices: created, last active, expiry, revoked | `accounts`, `account_devices` |
| `consents` | purpose, version, accepted, revoked (birth basic/deep, Tarot, resonance, AI rewrite, history, account storage...) | `consents` |
| `history_retention` | consent version, activated at | `history_retention_policies` |
| `birth_profile` | **birth date, time mode, exact local time or window, place display name, timezone** (decrypted), profile level, precision, supplement consent version, natal chart or date-only Sun result | `birth_profiles`, `chart_snapshots` |
| `daily_notes` | date, title, body, full body, context label, persona, created, that day's mood and time | `daily_notes`, `mood_check_ins` |
| `saved_notes` | saved at, note text snapshot, saved reading sections, evidence and disclaimer | `saved_notes` |
| `share_links` | format, status, created, expiry, revoked | `share_artifacts` |
| `tarot_sessions` | state, topic, spread, voice, question, cards by position, reading (headline, summary, positions, stance conclusion, closing prompt, disclaimer) | `tarot_sessions` |
| `note_feedback` | hit/miss, background lens, created, expiry | `resonance_feedback` |
| `daily_experiments` | state, lens, outcome, created, expiry, reflected | `daily_experiments` |
| `radar_sent` | A's side: nickname A typed, context, voice, mode, status, A's permission attestation time, created, expiry | `radar_requests` (A as owner) |
| `radar_received` | B's side: context, B's consent version, accepted, expiry | `radar_requests` (B as recipient) |
| `la_chung_invites` | nickname A typed, context, status, whether a visible answer exists, created, expiry | `la_chung_requests` |
| `matching` | Vòng Lá profile (display name, gender identity, intent, preference, age range, region, weekly intent, active, dates), matching consents, verification status | `matching_*` |
| `not_included`, `notice` | plain Vietnamese explanation of the exclusions below and a privacy notice | constant |

### Excluded, and why

| Data | Reason |
|---|---|
| Every database id, `token_hash`, `csrf_hash`, digest, receipt, capability token, idempotency/request hash, credential envelope, owner session | Access keys, not content. A file that leaks must not open the profile, a share link or a receipt. |
| Radar result prose (both modes) | Derived from B's chart. Copying it out would let it outlive the 24 h / 30 day window B agreed to (or A attested to for B). A still sees it in the app while it lasts. |
| La Chung responder's selections and alias | Written by another person who keeps a withdraw right. |
| B's birth date/time/place | Never stored as a profile (private check) or lives in B's own profile (invite). |
| Birthplace centroid coordinates | Catalog data derived from the chosen place; the place name and timezone are exported. |
| Daily notes hidden by the history window, expired Tarot, expired/withdrawn/revoked Radar requests | Hidden in the app and pending cleanup; the file must not bring back what the person was told is gone. Saved notes and today's note are always included. |
| Reading plans, revisions, projections, generation attempts, content-rewrite jobs (encrypted request/output) | Internal processing state. What the person saw is in Daily notes, Tarot and saved notes. |
| Experiment `action_key` | Opaque digest of catalog copy. |
| Matching verification provider reference | External identifier. |
| Erasure journal, login challenges/quotas, Tarot variant cursor | Keyed digests or counters about the system, not readable content about the person. |

## Security review (gate 2)

- **Ownership:** guest resolved by `verify_csrf` from the cookie (device credentials of a linked
  account resolve to the same guest). Every query filters on that guest id, or on the principal whose
  `source_guest_id` is that guest. Radar received uses the same eligibility filter as
  `GET /v1/radar/received`. Tests: another guest's file never contains this guest's data; A's file
  never contains B's birth data; B's file never contains A's nickname for B or A's birth data.
- **CSRF / origin:** mutation proofs required; GET returns 405. Native shell uses the marker header and
  still needs the CSRF token.
- **Abuse:** admission limit (in-memory backstop, as for other expensive routes); edge limits remain the
  production layer (unchanged gap). Lists bounded at 500.
- **Caching / transport:** no-store at the route and in the private-response middleware; nosniff,
  no-referrer; fixed filename with no personal data. HTTPS as for every API call.
- **Logs:** the route and service log nothing; error bodies carry only the problem code.
  `scripts/verify-privacy.mjs` passes.
- **Schema drift:** strict Pydantic models, `response_model`, and a test that rejects keys ending in
  `_id`/`_hash`/`_ciphertext` (except `timezone_id` and the chart engine's `config_hash` label).
- **Failure paths:** a decryption failure is a 500 with no body content; nothing partial is written
  anywhere. The export is read-only, so no rollback is needed.
- **Mobile (MASVS-STORAGE/PLATFORM):** the web client never writes the file to localStorage,
  IndexedDB or the query cache; the Blob URL is revoked at once. In the Capacitor shell the system
  share sheet saves the file when it accepts files; the file then lives where the person puts it.
  No new permission or plugin.

## Privacy review (gate 3)

- **Fields:** see inventory. Sensitive: birth date/time/place, derived chart, mood, relationship
  context and nicknames, matching preferences. All are the requester's own data.
- **Purpose:** honour the data subject's rights to view and request provision of their personal data
  (Law 91/2025/QH15 Art. 4(1), in force 01/01/2026; procedure detail in Decree 356/2025/NĐ-CP).
  The excerpts checked list viewing and requesting provision; they do not name a file format or
  portability, so JSON is a product choice.
- **Minimisation:** no credentials, no other people's data, no internal processing state.
- **Retention:** none on the server; the file is built on request and not stored. The SRS rule "no API
  returns raw birth data after the chart is computed" now has a second owner-only exception beside the
  private edit form (SRS §7 updated).
- **Third parties:** none. No provider, SDK or analytics receives the file or its content.
- **Consent:** not needed for the person's own access request; the sheet explains the contents first.
- **Store disclosures:** no new collection or sharing; data map updated with an export delta.

## Tests

- API `apps/api/tests/privacy/test_data_export.py` (8): owner file content and headers; no ids, tokens,
  hashes or cookies; no B birth data; B's own file; CSRF/origin/anonymous/other-guest rejection and
  405 on GET; fresh read after removing time/place; per-peer 429; list bound and `truncated`; history
  visibility; empty guest.
- Web: `downloadMyData.test.ts` (Blob download name, content, URL revoked; native share and cancel),
  `ProfilePage.test.tsx` (sheet copy, cancel, download, 429 and offline errors, B link),
  `RadarReceivedFlow.test.tsx` (held-data disclosure, no birth-data field).

## Open questions for the owner

1. **Radar result prose in the file:** excluded for B's sake. Should A get it while it is still
   openable? (Engineering recommendation: keep it out.)
2. **Hidden-but-not-yet-deleted Daily notes:** excluded to match the app. Include them instead,
   labelled "đang chờ xoá"?
3. **La Chung answers:** A sees the selected statements in the app; the file only says an answer exists.
4. **Copy approval:** the sheet, privacy-page entries and received-page disclosure are new copy.
5. **Native save:** confirm on a device build that the share sheet offers "Lưu vào Tệp" (iOS) and a
   file target (Android); WebView anchor downloads are not relied on.
6. **Response deadline** for manual requests under Decree 356/2025 is still not stated in-app.
