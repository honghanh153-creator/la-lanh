# Optional managed login backend (U2)

Runtime login is disabled by default. No runtime fake auth exists. The REST adapter
uses only a fixed `https://<20-character-project-ref>.supabase.co` origin and a
`SecretStr` publishable key in the `apikey` header. Redirects and environment proxy
settings are disabled. Provider response bodies, codes, and tokens are not logged.
Provider access/refresh tokens are discarded; browser credentials are local device
secrets. Browser responses never contain provider subjects or unmasked email.

## API contract

All paths below have `/v1` prefix. All account responses, including validation and
provider errors, are `no-store`. Validation errors never echo request input.

| Method/path | Request | Response |
| --- | --- | --- |
| GET `/account` | Current device cookie, if present | `login_enabled`, `signed_in`, `masked_email`, `profile_expires_at`, `guest_inactivity_days`, `history_days`, `daily_note_hours`, `account_inactivity_days` |
| POST `/account/login/code` | `{email, account_storage_consent?: "account-storage-v1"}`; current guest CSRF if active | `{status: "code_sent", login_csrf_token, expires_at, resend_after_seconds: 60}` |
| POST `/account/login/verify` | `{code: "123456"}`; `X-CSRF-Token: login_csrf_token` | `signed_in`, `restore_required`, `onboarding_required`, or `consent_required` |
| POST `/account/login/restore` | `{confirm: true}`; same login CSRF | `signed_in` after one-time HttpOnly restore proof validation |
| POST `/account/login/cancel` | Same login CSRF and bound challenge cookie | 204; removes challenge/proof cookies and durable challenge, preserves guest |
| POST `/account/logout` | Current device cookie and device `X-CSRF-Token` | 204; revokes current device only, clears profile/legacy-owner/capability cookies |

`signed_in` returns `session: {state, onboarding_status, expires_at, csrf_token,
session_epoch, resumed: true}`, plus `masked_email` and `profile_expires_at`.
`session.expires_at` is the device clock, not the account data clock.
`restore_required` returns only status/masked email/profile expiry, never a device
credential. Its proof is in an HttpOnly cookie; confirmation is mandatory.
Onboarding/consent outcomes issue no credentials and preserve the current guest.
The client must deliberately adopt the successful session and re-claim the retained
guest via `ensureOwnerIdentity` when necessary. Login does not claim an owner session.

Web POSTs require trusted Origin. Explicitly enabled native transport accepts the
existing Capacitor marker with absent/known native Origin, never an evil web Origin.
The marker does not authenticate: guest CSRF, the initiating credential binding,
and the login nonce still apply. Native storage behavior needs device QA.

## Ownership, clocks, and locks

The account retains the existing guest ID, chart encryption context, consent,
principal, and dependent foreign keys. First link requires a live anonymous guest
and explicit account-storage opt-in. It invalidates the original guest credential
once, scrubs every guest creation replay envelope, and revokes pre-link legacy owner
sessions. Later devices never rotate the shared guest token. An existing subject
always restores its own profile after confirmation; unrelated guests are not merged.
No guest creates an `onboarding_required` outcome, never a fake birth profile.

Account data expires after 365 days without authenticated use, independently of
each device's sliding 30-day credential lifetime. Monotonic renewal cannot shorten
either clock. Guest expiry remains the authoritative account purge clock. Cleanup
batches expired/revoked devices, expired challenges, and expired quota rows.
History clocks are unchanged by U2; U3 owns history retention implementation.

Provider calls occur outside DB transactions. A durable single-verifier claim and
attempt increment precede verification; a crash fails closed until expiry.
Finalization discovers the challenge without locking, locks the provider subject
via PostgreSQL advisory lock, locks initiating/target owners in UUID order, then
locks/rechecks the challenge. Anonymous/device resolution rechecks after locking.
SQLite mutations reserve `BEGIN IMMEDIATE`; no process-local mutex is authoritative.
There are five verify attempts, a ten-minute challenge, at most five additional
minutes for restore within that challenge, and a durable 60-second email cooldown.
Hourly send limits are global 100, email 5, peer 10; verify limits are 1000/30/120.
Quota keys are keyed domain-separated hashes only; active challenges temporarily
hold an encrypted email, scrubbed on success/failure/cancellation or bounded expiry.

## Erasure and release gates

Local whole-profile erasure uses the existing owner/provider-send fence and cascades
account linkage, devices, and relevant challenges. Expired/revoked credentials
cannot erase. Later verification of the same provider subject cannot recover deleted
local chart/history; a newly consented guest has a different ID. Logout is not erasure.

Linked account deletion and expiry now hard-delete the verified Supabase Auth subject before
local erasure is acknowledged. The server-only eraser uses a separately mounted secret key,
does not log provider bodies, and treats provider 404 as an idempotent acknowledgement.
DELETING owners reject access, restore and new sends; a failed provider call keeps the linkage
for bounded cleanup retry rather than pretending the identity was erased. Provider cancellation
alone does not erase an existing identity; no Google account is deleted. Public auth activation
requires these credentials and actual provider-erasure acceptance. See the deployment playbook.

Keep `auth_enabled=false` until operator-approved email delivery, OTP templates,
provider expiry/cooldown/anti-abuse configuration, PostgreSQL migration/RLS/role
rehearsal and concurrency proof, trusted proxy peer handling, scheduled bounded
cleanup, native physical-device QA, privacy review, and client contract integration
are verified. Downgrade preserves private data and revocations; rolling application
code back must not expose tables or revive anonymous credentials. No live Auth,
SMTP, PostgreSQL, mobile, or production verification was performed in this unit.

Primary sources checked: [Supabase email OTP](https://supabase.com/docs/guides/auth/auth-email-passwordless),
[SMTP restrictions](https://supabase.com/docs/guides/auth/auth-smtp),
[API keys](https://supabase.com/docs/guides/getting-started/api-keys), and
[Vietnam Law 91/2025/QH15 official entry](https://vanban.chinhphu.vn/?docid=214590&pageid=27160).
The official law entry is not legal certification; release privacy review remains required.
