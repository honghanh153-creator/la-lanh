# Production release a6e11bfd149b — 11/10/2026

Owner approval (chat, 11/10/2026): deploy staging + production in four steps (backup → migration rehearsal → staging → production), **Google login off**.

## What is live

| Item | Value |
|---|---|
| URL | https://la-lanh.2-28-136-44.sslip.io |
| Release / source | `a6e11bfd149b` (public `main`, PR #1 fast-forwarded; later ops-only commits on `main`) |
| Image | `la-lanh:a6e11bfd149b`, app + Caddy healthy |
| Database | Supabase `rlowapjpwsamjftpggen`, Alembic `20261008_0028` → **`20261011_0036`** |
| DB TLS | Verified identity: pinned Supabase Root 2021 CA (`infra/hetzner/certs/`), hostname check, TLS ≥ 1.2 |
| Flags | `auth_enabled=false` (`/v1/account` → `login_enabled:false`), generation/worker off |
| Timers | `la-lanh-guest-cleanup.timer`, `la-lanh-expired-cleanup.timer` active |
| Rollback image | `la-lanh:a7fadf7e4511`; restore `/opt/la-lanh/secrets/database_url.pre-ca` first (old image rejects `sslrootcert`). Schema stays at 0036 (additive). |
| Staging | https://staging.la-lanh.2-28-136-44.sslip.io — own empty PostgreSQL + keys, `/opt/la-lanh/staging/source`, auth/generation off |

## Evidence

- Local `pnpm check` exit 0: 425 web + 1290 API tests, content/Tarot (4 voices incl. roast)/Radar audits, ten-persona reviews (direct + roast), contracts, build, QA smoke.
- Backups (root-only, 14-day retention, `pg_dump` with `sslmode=verify-full`): 10:52, 11:08, 11:14 and **11:17 UTC (pre-migration)**, 612 KB each, checksummed.
- Rehearsal on the final image: restore newest backup into disposable TLS PostgreSQL → 20 guests, `0028 → 0036`, `database-privacy-isolation-ok`, rows preserved, app `/v1/ready` OK; container and data destroyed.
- `deploy.sh`: DB TLS probe OK, content review (direct + roast) in image, migration, privacy check, healthy app/Caddy.
- Public smoke passed (production + staging); HSTS, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex` present.
- Live browser acceptance (production, synthetic guest, 390×844): Welcome → birth date → reveal → Home → Tarot 3 cards (fan, pick, ceremony, result) → Mình → birth/note share cards; 0 page errors; QA guest deleted via Mình → Xóa Lá.

## Problems found and fixed during the release

1. **Runtime crash prevented:** `httpx` was dev-only but imported by the app → image would not boot. Caught by the rehearsal; moved to runtime dependencies.
2. **DB TLS:** the release verifies PostgreSQL identity; Supabase's pooler chains to a private root missing from public stores, and Python 3.13's strict X.509 profile rejects that root (no keyUsage). Pinned the CA (fingerprint matched dashboard download and live chain) and cleared only `VERIFY_X509_STRICT`. Deploy stopped safely before any migration until fixed.
3. **Incident — traffic split to staging (~11:05–11:33 UTC):** the staging service was named `app` and joined the production network, so Caddy load-balanced production requests across both stacks. Effect: intermittent 401/CSRF errors for anyone using production in that window; no cross-user data exposure (staging held only synthetic data), no production data loss. Every guest created in either database during the window matches a QA run by minute. Fixed by disconnecting staging, renaming the service `staging-app`, adding a DNS guard to `staging/up.sh`, and recreating staging with a fresh database.

## Open items

- Four synthetic QA guests (created 11:18–11:23 UTC, no account) remain in production because their test sessions broke during the incident; they expire under the 30-day inactivity cleanup. They were not hard-deleted by SQL to avoid touching any non-test row.
- Google login stays off until: Supabase server secret for identity erasure is installed via protected input, Supabase Site URL changed to the public origin, exposed Web client secret replaced, then two-account live acceptance.
- Runtime database role is `postgres` (non-superuser, broad privileges); a least-privileged app role is still a separate change.
- Not covered: real devices, iOS/Android, provider erasure, real-user comprehension.
