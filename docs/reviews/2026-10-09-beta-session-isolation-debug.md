# Beta session-isolation investigation — 2026-10-09

Status: initial diagnosis retained below; remediation authorized, implemented and tested locally on 2026-10-09. Beta deployment remains unchanged. No paid generation.

## Remediation addendum — 2026-10-09

The owner subsequently authorized fixing and testing immediately. Local implementation:

- Session changes clear private fallback/query/draft state before accepting the new epoch;
  obsolete in-flight responses are rejected even if the transport ignores cancellation.
- Private routes verify the server session before showing content. Focus, visibility, sibling-tab
  notifications and a local cookie-marker check revalidate identity. Offline verification hides
  private content. After a change, Back/direct navigation cannot silently adopt the new person's
  profile; the user must deliberately start again. A CSRF-cookie marker detects changes only;
  it is not an authentication credential or an authorization decision.
- A second confirmed server defect affected owner GETs: Radar, Lá Chứng and matching resumed an
  owner cookie without requiring its source guest to match the current guest cookie. A synthetic
  old-owner-A/new-guest-B reproduction returned A's history before the fix. All three use the
  same `resume_owner_for_guest` authorization helper now and return 401 on a mismatch.
- New guest creation clears stale owner cookies and, for a known guest switch, old Radar
  recipient capabilities. Idempotent retries preserve the same guest. First-time invite visitors
  retain their just-opened capability through onboarding; existing invitation tests protect this.

Permanent tests replace the throwaway diagnostics described below:
`apps/web/src/shared/api/sessionIsolation.test.ts`, `apps/web/src/app/SessionBoundary.test.tsx`,
and `apps/api/tests/guest/test_session_isolation.py`. Browser testing with synthetic data confirms
A's old tab is redirected to the warning rather than showing A or B's content, including direct
navigation back to `/home`. Onboarding with and without exact time, Home and Tarot draw/report
remain operable. Final counts/limits are in `2026-10-09-session-personalization-fix-receipt.md`.

These fixes do not establish that the reported incident was cross-device access. Similar authored
notes remain a separate content issue; see the semantic personalization receipt. No real user
database rows or credentials were examined. No production changes, commits or pushes were made.

## Report and scope

The owner reports seeing another person's content on reopening the beta. They confirmed
the beta environment, but have not yet clarified whether the people used independent devices
or one browser profile. That distinction remains necessary to attribute the reported incident.
No real user content, credentials, cookies, or private database rows were retrieved.

## Environment evidence

- Local HEAD: `99a3079a383a4cb529c1331a596bc47f75b5f07f` with substantial pre-existing changes.
- Read-only VPS check: `/opt/la-lanh/current` resolves to release `a7fadf7e4511`,
  application image `la-lanh:a7fadf7e4511`.
- Read-only deployed source confirms the same missing epoch-change invalidation as local code.
  The relevant `acceptSessionEpoch` block is unchanged relative to this release. Thus local WIP
  is not needed to explain this defect. No stash or reset of unrelated work was performed.
- Anonymous beta `GET /v1/session`: HTTP 401, `Cache-Control: no-store`.
- Deployed Caddy is a reverse proxy without a configured response cache.
- Service worker explicitly bypasses `/v1` API requests; its cache is app-shell assets.
- GitHub issue/PR history queries returned no existing records to link.

## Confirmed defect: frontend session boundary

1. A browser tab can hold guest A's daily note in the in-memory fallback and QueryClient.
2. A different tab/session creation can replace the browser's shared guest cookie with guest B's.
   Cookie issuance: `apps/api/app/api/v1/routes/guest_sessions.py:113`.
3. The old tab's `getSession` accepts B, but `acceptSessionEpoch` only overwrites
   `sessionStorage`; it neither compares the old epoch nor clears private state
   (`apps/web/src/shared/api/client.ts:445–459`).
4. `EntryPage` clears personal state for expiration only, not a valid identity change
   (`apps/web/src/features/entry/EntryPage.tsx:17–30`).
5. Home uses the unscoped memory fallback as initial data and the shared `["daily-note"]`
   query key (`apps/web/src/features/home/HomePage.tsx:57–66`). The old note can therefore
   remain visible after the active session changes, including when a fresh request fails.
6. Window-focus revalidation is disabled (`apps/web/src/app/AppProviders.tsx:17`).
   Direct `/home` and other private routes have no shared session-verification boundary.

This proves a browser/session-boundary defect, **not cross-device data exfiltration**.
The missing device/browser detail prevents equating it with the owner's exact incident.

## Repeatable checks

`apps/web/diagnostics/session-isolation.spec.ts` contains only synthetic fixtures.
Run from `apps/web`:

```sh
pnpm exec vitest run diagnostics/session-isolation.spec.ts --config session-isolation-diagnostic.config.ts
```

- FAIL: `must discard A's private fallback when a resumed session belongs to B`.
  Epoch changes to B but A's note remains readable.
- PASS control: `may retain A's private fallback when the resumed session is still A`.
- A broad run with this diagnostic also passed all 220 pre-existing frontend tests.
  Existing tests clear state in their setup and cover explicit deletion, projection identity,
  and revision updates, but do not exercise a valid guest-to-guest epoch transition.

An in-memory SQL-backed FastAPI probe used two separate synthetic cookie jars, real repositories,
and generation explicitly disabled:

- Different guest epochs, birth snapshots, and daily-note IDs: PASS.
- Own birth snapshot remains isolated in both directions: PASS.
- Foreign daily-note mood read and write: both 404 in both directions.
- Foreign Tarot session read: 404 in both directions.
- Giving the first test client the second client's cookie jar reproduces the shared-browser
  behavior: it resumes the second guest's profile. The application identifies a guest cookie,
  not the human currently holding the device.

These backend results are local synthetic evidence, not a live Supabase isolation audit.
An initial network probe against localhost was denied by the execution sandbox before creation;
the in-process probe above was used instead. No public test profiles were created.

## Original proposal, before authorization

The current request asks for checking/debugging, not an explicit implementation or deployment.

1. Centralize session-transition invalidation in the API/session layer. On changed or missing
   identity, cancel old personal requests and clear private caches before accepting the new
   identity or replaying queued writes. Reject responses from an obsolete session generation.
2. Add a private-route verification boundary and tab synchronization/resume checks. Hide old
   private content until identity is verified; do not treat an offline verification failure as
   permission to display data belonging to a possibly different guest.
3. Bind private fallback/query state to the verified guest epoch. Remount personal UI on identity
   changes so local component state cannot survive cache clearing.
4. Clarify shared-device UX: starting another person's guest session in the same browser replaces
   the original guest identity. A recoverable account/profile-switch design is separate from
   cache invalidation and must not be silently invented during a security fix.

Candidate files: `shared/api/client.ts`, `shared/storage/noteCache.ts`,
`shared/storage/clearPersonalData.ts`, `app/AppProviders.tsx`, `app/router.tsx`,
`features/entry/EntryPage.tsx`, plus a focused session boundary/helper if needed.
`client.ts` already has unrelated uncommitted work; preserve it and obtain approval before editing.
No unrelated security/content changes should be bundled into a beta hotfix.

Recommended regression homes: strengthen `client.reliability.test.ts`, `noteCache.test.ts`,
`clearPersonalData.test.ts`, and route/provider integration coverage. Promote the synthetic
diagnostic into existing coverage once a fix is authorized. Include two tabs, delayed A responses
after B takes over, direct private-route navigation, missing/expired sessions, offline resume,
and both directions of backend ownership checks (including Radar results).

## Sources and limits

- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html):
  session lifecycle and client storage boundaries.
- [MDN sessionStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage):
  storage is tab-scoped, unlike a shared browser cookie jar.
- Repository instructions, deployed non-secret source, and the synthetic checks above.

Confidence: high in the confirmed frontend defect and the local backend checks; attribution to
the owner's specific beta incident remains incomplete. No remediation, deployment, production
database inspection, key rotation, or payment action occurred in this investigation.
