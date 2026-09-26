# Hetzner + Supabase release runbook

Use this runbook for the closed Lá Lành web beta. The canonical implementation plan and reusable
checklist are in `docs/plans/2026-09-26-hetzner-supabase-public-beta-deployment-plan.md`.

## Required owner decisions

- Select a Supabase project and region. For this long-running IPv4 VPS, copy the **session pooler**
  connection string on port 5432 from Supabase's Connect dialog.
- Approve and retain evidence for either a Swiss Ephemeris professional license or an
  AGPL-compliant public-source release.
- Review the closed-beta processor/cross-border disclosure for Hetzner Germany and the selected
  Supabase region. Update the privacy notice before inviting testers.
- Keep AI generation disabled unless the separate governance gate is approved.

Never paste the database password, full database URL, cryptographic keys, or API secrets into chat,
Git, issue trackers, or shell command arguments. Create the secret files from an interactive server
terminal. Keep the parent directory root-owned with mode `0700`; files use mode `0600` and runtime
UID/GID `65532:65532` so the non-root application process can read its mounted secrets.

## Server layout

```text
/opt/la-lanh/current/        committed source snapshot
/opt/la-lanh/secrets/        root-owned secret files
/opt/la-lanh/releases/       release metadata and prior snapshots
```

Required secret files are `database_url`, `guest_hash_key`, and `guest_encryption_key`. The database
URL must start with `postgresql+asyncpg://`, use the exact Supabase session-pooler host/username,
include port 5432, and require TLS. Percent-encode reserved password characters.

Use `infra/hetzner/configure-database.sh PROJECT_REF POOLER_HOST` from an interactive VPS terminal.
It prompts with hidden input, percent-encodes the password, and writes the connection string with
mode `0600`, keeping the credential out of chat and shell history.

Generate the two application keys on the server with a cryptographically secure generator. Each
file must contain one base64-encoded 32-byte value and a trailing newline is acceptable.

## First deployment order

1. Verify SSH, UFW, unattended upgrades and the Hetzner firewall remain healthy.
2. Install Docker Engine and the Compose plugin from a supported repository.
3. Transfer a committed repository snapshot to `/opt/la-lanh/current` without `.git`, local
   databases, `.env` files, caches or dependencies.
4. Copy `infra/hetzner/app.env.example` to `infra/hetzner/app.env`, set the exact HTTPS origin, and
   replace the development license mode only after its gate is approved.
5. Write the three secret files directly on the server; keep the directory `0700`, and set files to
   runtime UID/GID `65532:65532` with mode `0600`.
6. Export `APP_HOSTNAME` and an immutable `LA_LANH_RELEASE_ID` in the operator shell.
7. Run `infra/hetzner/deploy.sh`. It validates configuration, builds the image, applies migrations,
   waits for readiness, and then starts Caddy.
8. Open host and Hetzner firewall ports 80/tcp, 443/tcp and 443/udp. Keep 8080 closed.
9. Run `infra/hetzner/smoke.sh https://HOSTNAME` and complete browser acceptance from the plan.

## Database safety

- The browser does not use Supabase APIs or keys. FastAPI is the only application database client.
- Before migration, run `python -m scripts.check_database_tls` through the app service. It verifies
  encrypted transport while deliberately suppressing connection details on failure.
- Prefer a non-exposed database schema. If tables stay in an exposed schema, enable RLS and revoke
  `anon`/`authenticated` access unless the product explicitly needs it.
- Run Alembic migrations before replacing the app. Do not automatically downgrade a live schema.
- Verify Supabase backups and retention for the selected plan. A restore must reconcile user
  deletions made after the restore point before traffic resumes.

## Retention jobs

Run these from the current source directory with the same Compose environment, record aggregate
counts only, and schedule both at least every six hours:

```sh
docker compose -f infra/hetzner/compose.yaml run --rm --no-deps app \
  python -m scripts.cleanup_guests --batch-size 500
docker compose -f infra/hetzner/compose.yaml run --rm --no-deps app \
  python -m scripts.cleanup_expired --batch-size 500
```

## Rollback

Record the current and previous image tags before every release. For an application rollback, set
`LA_LANH_RELEASE_ID` to the prior built tag and run Compose without rebuilding. Confirm that the
prior app version is compatible with the already-applied schema, then run public smoke checks.

Do not put an old database backup directly into service. Restore into isolation, reconcile
post-backup deletions, validate ownership boundaries, and only then cut over.

## Incident checks

- `docker compose -f infra/hetzner/compose.yaml ps`
- `docker compose -f infra/hetzner/compose.yaml logs --since 15m app caddy`
- `curl --fail https://HOSTNAME/v1/ready`
- `systemctl --failed`
- `ufw status verbose`

Logs must never include request bodies, birth data, coordinates, relationship content, cookies,
database URLs, receipt tokens, or share tokens. Caddy access logs and Uvicorn access logs remain
disabled because capability tokens currently occur in URLs.

## Official references

- Docker on Ubuntu: https://docs.docker.com/engine/install/ubuntu/
- Docker Compose plugin: https://docs.docker.com/compose/install/linux/
- Caddy automatic HTTPS: https://caddyserver.com/docs/automatic-https
- Supabase database connections: https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase product security: https://supabase.com/docs/guides/security/product-security
- Hetzner firewalls: https://docs.hetzner.com/cloud/firewalls/
- Hetzner backups: https://docs.hetzner.com/cloud/servers/backups-snapshots/overview
