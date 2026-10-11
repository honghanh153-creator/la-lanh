# Web Google OAuth — local end-to-end receipt, 11 October 2026

Scope: the **web** Google login of the PR head `1bb7db9` run against the real Supabase project `rlowapjpwsamjftpggen` and the real Google `La Lanh Beta Web` client. iOS and Android were paused by the owner. This is live-provider evidence for the web flow on a local API, not a production deployment, not native acceptance and not a release approval.

## Setup

| Item | Value |
| --- | --- |
| API | `uvicorn app.main:app` on `127.0.0.1:8000`, `environment=development`, PR head source |
| Web | Vite dev server on `http://localhost:5173`, `/v1` proxied to the API |
| Database | Throwaway SQLite file outside the repository; no production database was touched |
| Auth flags | `auth_enabled=true`, `auth_google_enabled=true`, `auth_delivery_approved=false` (email OTP stayed off) |
| Callback | `http://localhost:5173/auth/callback`, the only trusted CORS origin |
| Provider credential | Supabase **publishable** key only, in a gitignored local env file (mode 0600). No secret/service-role key was configured, so linked-identity erasure was not exercised |
| Browser | Claude built-in browser; the owner chose the Google account and completed Google's step personally |

No Supabase URL configuration, Google client, audience, test-user, VPS or production setting was changed. Supabase still has Site URL `http://localhost:3000` and no redirect URLs.

## Results

| Check | How | Result |
| --- | --- | --- |
| Guest first | Welcome → **Đồng ý & bắt đầu** → test DOB → reveal | Guest created with birth profile and chart snapshot |
| Start login | Account-storage consent → **Tiếp tục với Google** | Backend returned Supabase `/auth/v1/authorize` with S256 PKCE and `redirect_to=http://localhost:5173/auth/callback?state=<43 chars>`; Google account chooser showed `rlowapjpwsamjftpggen.supabase.co` with the Web client ID |
| Callback and exchange | Owner selected the test account | Supabase returned to `/auth/callback` with `code` and the backend `state`; `POST /login/google/verify` 200; landed on `/home` |
| First link keeps guest owner | Local DB | `accounts.guest_id` equals the original guest ID; that guest still owns its birth profile and chart snapshot; masked email `h***@gmail.com` only |
| Logout | Owner-driven | `POST /logout` 204; device row revoked |
| Re-login and explicit restore | Owner-driven: login again from a fresh guest | `restore_required` → `POST /login/restore` 200 → signed in to the **original** guest. The new temporary guest kept its own row with no birth profile; nothing was merged |
| Cancel during restore | Owner-driven | `POST /login/cancel` 204 |
| Challenge hygiene | Local DB | Every Google challenge `consumed` after 1 attempt; encrypted PKCE verifier scrubbed (`NULL`) |
| No provider tokens in the browser | JS scan of `document.cookie`, local/session storage, URL and history state | No JWT-shaped value, no `sb-*-auth-token`, `access_token`, `refresh_token` or `provider_token`. Only JS-readable cookie is `la_lanh_csrf`; the device credential is HttpOnly. URL scrubbed of `code`/`state` |
| Untrusted Origin | `POST /login/google` with `Origin: https://evil.example` | 403 |
| Missing consent | `POST /login/google` without consent | 422 |
| Wrong device | `verify` with valid `state` but no challenge cookie | 403 `LOGIN_CHALLENGE_REJECTED` |
| Wrong state | `verify` with challenge cookie but different `state` | 403 `LOGIN_CHALLENGE_REJECTED` |
| Forged code | `verify` with a made-up code (real Supabase exchange) | 400 `LOGIN_VERIFICATION_FAILED` |
| Replay | Same challenge again | 400 `LOGIN_CHALLENGE_USED` |
| Provider cancel/deny | `/auth/callback?error=access_denied` | Error shown, URL scrubbed, existing session unchanged |
| Caching | Account responses | `Cache-Control: no-store, max-age=0`, `Referrer-Policy: no-referrer` |

## Finding: redirect acceptance depends on the Site URL host

The redirect back to `localhost:5173` succeeded with an **empty** Supabase redirect allowlist. The observed behaviour matches Supabase Auth accepting a `redirect_to` whose hostname equals the Site URL hostname (`localhost`). Two consequences for the public origin:

1. Setting Site URL to `https://la-lanh.2-28-136-44.sslip.io` is what makes the public callback acceptable; it is not cosmetic.
2. The backend appends `?state=…` to the callback. An exact allowlist entry `https://…/auth/callback` might not match a URL with a query string; if Supabase falls back to the Site URL, the `state` is lost and the callback page rejects the login (fails closed, no account change). Verify this on the real origin after the approved URL change instead of widening the allowlist with wildcards.

## Side effects

- One Supabase Auth user now exists for the approved test Google account in project `rlowapjpwsamjftpggen`. The local app data lives only in the throwaway SQLite file. Delete the Supabase user from the dashboard if a clean provider state is wanted; local account deletion cannot do it here without the server secret.
- Google login for the Web client was exercised with the Web secret that is already recorded as exposed. Replacing it before production activation remains open.

## Still open for web

- Two different Google accounts in isolated browser contexts. This needs a second approved Google test user (Google Auth Platform → Audience), which was not added.
- Account deletion with real provider erasure (needs the protected `sb_secret_…` server credential).
- The same flow on the deployed public origin, after the release-runbook gates (backup/restore, migrations 0029–0036, least-privileged role) and the approved Supabase Site URL change.
- Minor UX: the post-login redirect falls back to `/home` from `/reveal` because `/reveal` is not in the login page's safe-return list; the provider-denied message says "Hồ sơ khách vẫn được giữ" even when an account session is active.
