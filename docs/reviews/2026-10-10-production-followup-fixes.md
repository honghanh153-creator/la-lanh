# Production follow-up, 10 October 2026

Status: local automated verification completed; live activation remains blocked. Not deployed. The production image remains
`la-lanh:a7fadf7e4511`, schema `20261008_0028` at the read-only inspection in this session.
No live migration, commit/push, billing operation or paid provider call has been performed.

## Review and resolution

The completed full review is [the immutable report](2026-10-10-production-bundle-code-review.json),
run `20261010-2010-production`, base `99a3079a383a4cb529c1331a596bc47f75b5f07f`.
Eleven lenses, independent merge and validation confirmed ten findings. The original Not ready
verdict is retained. This document records subsequent fixes, not an invented replacement verdict.

| Finding | Applied correction | Evidence |
| --- | --- | --- |
| #1 P1, worker Auth config | Worker explicitly overrides all Auth flags to false; never mounts admin key. | Combined Auth+generation production Settings through actual entrypoint, synthetic mounted secrets. |
| #4 P1, late profile cookies | Remove middleware cookie reflection and status cookie writes. Explicit CSRF renewal, browser-wide shared/exclusive Web Locks through response consumption and identity adoption. | ASGI delayed valid A response after confirmed B restore preserves B cookies and does not revoke A. Client cancellation/body/adoption ordering regressions. |
| #5 P1, cleanup Auth config | Shared compose selector retains app-only erasure credential even when new login is off; deployment refreshes installed retention runner. | Selector exercises Auth on/off and key present/missing; missing key fails closed; worker settings test. |
| #6 P2, account 422 contract | Declare private problem+json account errors and regenerate OpenAPI/TypeScript. | Malformed verify request produces ACCOUNT_INPUT_INVALID, correct media/schema, no-store and zero provider calls. |
| #7 P2, crashed history worker | Check unexpired durable disclosure fences, not indefinite job lease status. Bound legacy attempts by lease plus provider allowance. | Manual and scheduled history erasure succeed after fence expiry without restarting a worker; active fence still blocks. |
| #8 P2, provider privacy copy | Document DELETING, send drain, provider hard erase, local cascade and retries. | Aligned with actual adapter/repository and pending 503 regression. Live provider acceptance remains separate. |
| #9 P2, one Tarot result waits for unrelated sends | Capture only job IDs owned by this guest and this Tarot session before cascading. | Unrelated send remains while deletion completes; admitted target send must drain before ACK. |
| #10 P2, flaky PostgreSQL erasure proof | Poll bounded authoritative revocation before checking pending erasure. | Real PostgreSQL connection-kill/provider-pause test observes DELETING rather than assuming a 100ms sleep. |
| #11 P2, background/BFCache privacy | Hidden state invalidates pending checks; pageshow/visibility requires fresh same-owner verification. | Same/different owner, expiry, session change, offline Retry and unmount coverage. |
| #12 P2, abandoned Welcome adoption | Propagate cancellation into creation and async adoption; Google link disabled during pending creation. | Real client with only fetch mocked preserves next-screen draft/key and does not abort its Google transport. |

Rejected #2/#3 catalog-splitting claims remain rejected. File-size preferences alone do not prove
incorrect behavior; content was not rewritten just to satisfy those suggestions. The private
HistoryService/repository coupling is a maintenance advisory, not an authority failure; restructuring
it is deferred to avoid changing verified transaction boundaries in this release.

## Additional migration coverage

- Populated 0029/0030 upgrade on the isolated PostgreSQL cluster checks actual and reserved
  cost/tokens, NULL usage, UTC day/month boundary, queue-envelope erasure and retained spend ledgers.
- Populated pre-0032 mood table checks creation-time backfill from checked_in_at and no implicit
  legacy history consent. Both tests roll back schema changes and never connect to production.
- Guarded PostgreSQL account/rewrite suite: **60 passed** after these changes.
- Focused API history/account/erasure/infra suite: **77 passed** before final contract formatting.
- Client reliability focused suite: **14 passed** after adding actual dispatch rendezvous.
- Final current-tree verification: **303 web tests passed**, **1,228 API tests passed,
  56 environment-dependent tests skipped**. The separately guarded real PostgreSQL suite above
  covers 60 account/rewrite cases; it does not turn every skipped test into a pass.
- OpenAPI/TypeScript contracts, runtime/privacy/mobile configuration guards, web lint/typecheck,
  API lint/format/typecheck all passed. Daily audit: 630 variants; Tarot audit: 19,656 synthetic
  spreads; reviewer: 10 synthetic personas, 30 readings, zero critical/high/medium findings;
  Radar: four contexts and four voices; rewrite manifest: 670 cases over 13 surfaces.
- `pnpm check` reached QA after the preceding checks passed, then failed on sandbox-denied
  loopback listen (`EPERM`). The unchanged `pnpm qa:test` rerun with loopback permission passed:
  three server tests, production web build, pinned ephemeris checksums and real
  guest -> birth -> daily-note CLI smoke. Do not describe the first command as exit 0.
- Vite reports a large application chunk and mixed static/dynamic import of clearPersonalData.
  These are nonblocking build advisories, not evidence of a measured performance improvement.

## Browser and content evidence

Observed on the separate synthetic local QA origin `http://localhost:5351`: Welcome has exactly
the guest and login entry actions; guest birth 15 March 1990 reveals Mộng; Home shows the daily note;
Tarot question -> five-card fan -> selected-card reveal -> summary first -> expandable card meanings.
The deterministic content uses ordinary direct Vietnamese and never enables external AI itself.
The browser's native screenshot operation failed with zero viewport width during this session;
current visual/mobile fidelity is not certified by an accessibility tree. Existing screenshots
in the earlier receipt are earlier evidence, not newly captured proof.

Cookie-capable transports drain after cancellation rather than releasing a late-cookie race.
An indefinitely stalled cookie transport holds the fence. Ordinary cookie-free requests retain
the existing bounded timeout. Web Locks unavailable means cookie issuance refuses safely;
physical native Web Locks/Google callback acceptance is still unverified. Do not call offline
provider fixtures a real Google sign-in or ten synthetic personas a human comprehension study.

## Actual blockers for the requested full production activation

1. Inspected VPS has no `supabase_admin_key`; linked account erasure and production Auth cannot
   activate without it. Google provider Client ID/Secret, exact callback allowlist and real
   two-account/device acceptance have not been observed. Client Secret belongs in Supabase only.
2. Inspected VPS has no existing `openai_api_key`. No new key, recharge or budget increase is allowed
   as a workaround. Install the user's existing key through protected input; retain USD 1/month.
3. Production backup/restore, new-schema role/grants, exact committed AGPL source/image, rollback
   and public E2E still must run once activation is unblocked. No live backup or schema change was
   made during the read-only check.

The application budget does not protect a key stolen and used outside the app. Never put either
secret in chat, app.env, browser JavaScript, Git, logs or this receipt.

## Guided setup continuation

On the signed-in Supabase dashboard, the Google provider was observed disabled with empty
Client ID/Client Secret fields. No settings were saved. The observed provider callback is
`https://rlowapjpwsamjftpggen.supabase.co/auth/v1/callback`.
The project list subsequently loaded. The selected existing Google project is **La Lanh Beta**,
ID `la-lanh-beta`. Do not ask the owner to find that ID again. Google Auth Platform then reported
Failed to load. The visible APIs & Services Credentials page also reported Failed to load OAuth
clients. Its empty table is not evidence that no client exists. No credential was created or
changed during the failed in-app browser checks. The owner subsequently approved continuing in
Chrome. Its Credentials page loaded without errors and showed no OAuth clients. Google Auth
Platform Overview explicitly reported not configured yet.

The owner approved `honghanh153@gmail.com` as the support email and explicitly accepted the
Google API Services User Data Policy. Google consent configuration was saved successfully:
app Lá Lành, that support/contact email, External audience in Testing. Homepage, privacy and
terms URLs still need configuration before public activation. The Web OAuth client form is
prepared as La Lanh Beta Web, with production origin and only the Supabase callback above.
Create has not been submitted: the owner must perform credential generation and keep the
Client Secret out of chat. No test users added, Supabase provider enabled, billing changed or
production login activated. Preserve the Chrome handoff instead of restarting setup.

## Privacy-focused Standard scan, completed 10 October 2026 UTC

Scan `3facdd52-44ff-4356-9c87-d40dc90a3dde` reviewed the dirty source snapshot before this receipt
update. Its generated report is stored under the Codex Security scan directory, revision
`99a3079a383a4cb529c1331a596bc47f75b5f07f`, suffix `20261010T164046Z_1uw78al4/report.md`.
Coverage is partial: independent baseline reviewed 89 complete source files; architecture
mapping and excerpts are not exhaustive security coverage. No source patch was made in this scan.

- One parent-validated medium finding: Radar creation has no transactional owner quota and
  `list_owned` eagerly loads/decrypts the entire collection; sharing also enumerates it. An
  authorized guest can amplify shared resource usage. Fix quota, idempotency, rate limits,
  bounded pagination and direct owner/ID share lookup; no live load attack was performed.
- Reviewed owner/session paths showed no source-supported cross-account bypass. This does not
  resolve the previously reported beta symptom or certify older production behavior.
- Private Radar mode is denied external AI rewrite; invited pair rewrites require both subjects'
  distinct active consent. An owner's general policy acceptance is not third-party consent.
- Fresh live Supabase metadata showed schema 0028, RLS enabled and no anon/authenticated table
  grants. Two immutable-history trigger search_path warnings remain; local 0035 addresses them
  but has not been deployed. Backend least privilege remains a release gate.
- Data-map corrections needed: coarse Radar context is plaintext, not encrypted; first-link
  history consent is combined with disclosed account-storage consent, not always a separate UI
  action; deferred matching still has mounted collection endpoints.
- Publish accurate controller/contact and Google/Supabase identity-processing disclosures,
  verify actual minimal scopes and redirect allowlists. Provider profile processing can include
  name/photo even when the app keeps only subject UUID and masked email. App requests no Gmail
  or contacts, but real Google consent has not yet been observed.
- Logical expiry and installed cleanup timers do not establish exact physical deletion in
  backups or provider systems. Backup expiry/restore rehearsal, provider deletion, real
  two-account/device acceptance and processor arrangements remain unverified.

The completed scan is implementation evidence, not a legal compliance certificate. No user rows,
secrets, paid provider calls, live migration or deployment were used for this privacy review.

A completed read-only deployment sidecar verified the live image and protected-file inventory.
It found no executable backup/restore procedure, no PostgreSQL client tools or cached PostgreSQL
image, and no restore proof. Provider credentials do not block an isolated backup/migration
rehearsal. Before that rehearsal, supply protected database client configuration, an isolated
destination and documented backup expiry/deletion handling. Do not run deploy.sh first: it
changes the live schema and replaces containers without a backup gate. The sidecar made no
database connections, writes or provider calls and has been closed.

Sequence: select accessible Google project -> configure minimal OAuth and Supabase redirects ->
protected VPS credential input -> backup/restore and exact-image migration rehearsal -> committed
public source and deployment -> live owner-isolation/Google/Tarot/Radar acceptance. Live Google
selection requires the owner's sign-in; secrets must not be pasted into the chat.

## Sources checked

- [Supabase Google](https://supabase.com/docs/guides/auth/social-login/auth-google) and
  [PKCE](https://supabase.com/docs/guides/auth/sessions/pkce-flow).
- [Supabase key handling](https://supabase.com/docs/guides/getting-started/api-keys) and
  [provider hard deletion](https://supabase.com/docs/reference/python/auth-admin-deleteuser).
- [Web Locks](https://www.w3.org/TR/web-locks/) and
  [page lifecycle](https://developer.mozilla.org/en-US/docs/Web/API/Window/pagehide_event).
- [Vietnam personal-data law official record](https://vanban.chinhphu.vn/?docid=214590&pageid=27160).

These checks are implementation evidence, not a legal, native-store or external penetration-test certificate.
