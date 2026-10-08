# Hetzner + Supabase deployment playbook

This is the canonical, restart-safe playbook for deploying the Lá Lành closed web beta. A future
operator or Codex session should be able to use it without relying on chat history. The companion
status checklist is
`docs/plans/2026-09-26-hetzner-supabase-public-beta-deployment-plan.md`.

## Known-good recovery anchor

| Item | Value verified on 2026-09-30 |
|---|---|
| Product URL | `https://la-lanh.2-28-136-44.sslip.io/welcome` |
| VPS | `2.28.136.44` |
| Local SSH key | `~/.ssh/la_lanh_hetzner_ed25519` |
| Public source | `https://github.com/honghanh153-creator/la-lanh` |
| Deployed release | commit `3798652ed4a31f9099c2cd914868be304601abcc` / image `la-lanh:3798652ed4a3` |
| Image digest | `sha256:4da87e5c5e9ca72926f1edbae8fc3037a313450a3434abd53460174afd34e948` |
| Previous rollback image | `la-lanh:db1dab4c77f3` |
| Supabase | project `rlowapjpwsamjftpggen`, Frankfurt, session pooler `:5432` |
| Reverse proxy | Caddy `2.10.2`, Let's Encrypt certificate |

The database password and full connection URL exist only in `/opt/la-lanh/secrets/database_url` on
the VPS. Do not retrieve, print, log, or paste them into chat. A deployment should not need the
password unless that file is missing or the database password was rotated.

Release `9076c1b1e629` was verified on 2026-09-28 with the full repository gate, public smoke,
PostgreSQL TLS probe, Alembic head `20260927_0022`, private readiness and a synthetic public browser
journey. Acceptance covered the native own-birth time picker, exact time/place Natal unlock, Home
Natal CTA, full Natal reading, Radar `Không rõ giờ` with `time_precision=unknown`, precision
disclosure, Radar deletion and guest deletion. The content gate regression that previously rejected
one full-chart Daily/Natal candidate on length is covered by the full API suite. The prior healthy
release `b391e6610840` remains the immediate application rollback image.

Release `6e0e064cfb48` was verified and deployed on 2026-09-29 at 06:18 UTC. The repository gate
passed 135 web tests and 356 API tests plus Daily, Tarot, Radar and native-engine audits. Database
TLS, Alembic head `20260927_0022`, private readiness, public smoke, HTTPS/deep links and a fresh
synthetic browser journey passed. The browser journey exercised the question-first Home and the
recommended five-card Tarot flow, then permanently deleted its Tarot result and guest profile.
The app survived a controlled restart and `la-lanh:9076c1b1e629` passed the rollback dry run.
Retention timers installed by follow-up public commits `9396473` and `7d6241f` are active and their
first runs succeeded without emitting personal payloads. The running application source remains
the public historical commit `6e0e064cfb4803eb64126e8af56647e36da7ddf2`.

Release `ac96aa627aad` was deployed on 2026-09-29 at 14:03 UTC. The production image itself passed
the mandatory ten-persona reviewer (20 readings) before migration. Alembic remained at
`20260927_0022`; app/Caddy health, private readiness, public smoke and browser checks for Welcome,
Home and Tarot passed without console errors. Its corresponding source is the public commit
`ac96aa627aade967d4f1206406e276308afd2c13`; `la-lanh:6e0e064cfb48` is the immediate rollback image.

Release `db1dab4c77f3` was deployed on 2026-09-30 at 07:25 UTC. It includes the independent content
quality engine and optional Studio review surface from `b6b65893f145`, then removes the remaining
user-facing abstract `pattern` language in `db1dab4c77f3`. The release passed 396 API tests, 136 web
tests, Daily/Tarot/Radar content audits, the ten-persona reviewer, database TLS, Alembic head
`20260930_0023`, private readiness, public HTTPS smoke, and browser checks for Welcome, Home, Tarot,
and Privacy. The public Studio API remains disabled (`404`) while bundled approved content continues
to serve without CMS availability. Both retention jobs and timers passed. The previous healthy image
`la-lanh:b6b65893f145` remains the immediate rollback anchor.

Release `3798652ed4a3` was deployed and verified on 2026-09-30. It removes the generic Daily scene
and the fabricated fallback experiment from date-only Vibe readings, reduces Home/detail/share-card
headline scale, and keeps the disclaimer in its own accessible notice. The release passed 137 web
tests, 396 API tests, Daily/Tarot/Radar content audits, the ten-persona reviewer, PostgreSQL TLS,
Alembic head `20260930_0023`, private readiness, public HTTPS/deep-link smoke and live browser
acceptance for Home, Daily Note and share card. The app container is healthy, Caddy is serving the
release, and the correctly named `la-lanh-guest-cleanup.timer` and
`la-lanh-expired-cleanup.timer` units are active. The previous healthy image
`la-lanh:db1dab4c77f3` remains the immediate rollback anchor.

## What “successful” means

A release is successful only when all of these are true:

- the selected commit is available in the public repository before it serves users;
- the app container is healthy and `/v1/ready` confirms PostgreSQL and Swiss Ephemeris readiness;
- Caddy serves a trusted HTTPS certificate and HTTP redirects to HTTPS;
- browser deep links load rather than showing a blank SPA;
- security/privacy headers remain present and ports other than 22, 80, and 443 are not public;
- no secret or sensitive request path appears in Git, build output, `docker inspect`, or logs;
- smoke and browser acceptance pass;
- the release evidence and unresolved operations are recorded in the deployment plan.

## Non-negotiable safety rules

- Never paste a password, full database URL, cryptographic key, cookie, receipt token, or share token
  into chat, Git, shell arguments, screenshots, issues, or logs.
- Never expose port `8080`; only Caddy publishes `80/443`.
- Never enable Caddy or Uvicorn request access logs while capability tokens can appear in URLs.
- Never run an automatic Alembic downgrade in production.
- Never restore an old database directly into service. Restore in isolation and reconcile user
  deletions made after the restore point first.
- Use only synthetic identities for production acceptance. Delete the generated test data and revoke
  test capabilities afterward.
- AI generation remains disabled unless the separate Luna governance gate, current owner spend
  approval, synthetic paid probe and least-privilege worker checklist all pass.

## Server and network contract

```text
Browser -> HTTPS :443 -> Caddy -> app:8080 on private Compose network
                                   -> Supabase session pooler :5432 over TLS
```

```text
/opt/la-lanh/current/        active committed source snapshot
/opt/la-lanh/releases/       immutable release snapshots and evidence
/opt/la-lanh/secrets/        root-managed runtime secret files
```

Required baseline secret files are `database_url`, `guest_hash_key`, and `guest_encryption_key`.
When generation is enabled, `openai_api_key` is additionally required and is mounted only into the
isolated rewrite worker. The secrets directory is mode `0700`. Each file is mode `0600`, owned by
runtime UID/GID `65532:65532`, so the non-root process can read the Compose-mounted secret.

Network policy:

- Hetzner Cloud firewall: ICMP, TCP 22, TCP 80, and TCP 443 only.
- Host UFW: TCP 22 only from the current operator IP; TCP 80/443 and UDP 443 publicly reachable.
- TCP 8080 and PostgreSQL ports are never opened publicly.

## Phase 0 — resume and preflight

Run locally from `/Users/phamhanh/Documents/New project/la-lanh`:

```sh
git status --short
git fetch origin
git branch --show-current
git log -5 --oneline
git rev-parse HEAD
gh repo view honghanh153-creator/la-lanh --json visibility,url,defaultBranchRef
pnpm check
bash -n infra/hetzner/*.sh
```

Stop before deployment if the worktree has unexplained changes, checks fail, the chosen commit is not
in the public repository, or repository visibility is not `PUBLIC`. This product uses the authorized
AGPL release posture, so deployed corresponding source must remain available.

Verify SSH without weakening the firewall:

```sh
ssh -i ~/.ssh/la_lanh_hetzner_ed25519 root@2.28.136.44
```

If SSH times out after the operator's public IP changed, use the Hetzner web console to update the
host UFW rule before retrying. Do not temporarily expose password SSH.

On the VPS, inspect non-secret state:

```sh
docker version
docker compose version
systemctl is-active docker
systemctl --failed
ufw status verbose
find /opt/la-lanh/secrets -maxdepth 1 -type f -printf '%f %m %u:%g\n'
```

Do not run commands that print secret file contents.

## Phase 1 — choose and publish an immutable release

Before choosing the release commit, complete the content release gate in
`docs/operations/content-matrix-release-gate.md`:

```sh
pnpm content:audit
pnpm tarot:audit
pnpm content:review
pnpm experience:audit
```

For a normal release, record the reviewed content improvement and its regression fixture. An urgent
security or availability hotfix may use the documented waiver; do not add filler copy to force a
content delta.

`content:review` is blocking: it renders Daily and Tarot output for ten synthetic personas (twenty
readings total), including date-only/full-chart Daily and one/three/five-card Tarot. It checks
concrete scenes/actions, evidence validation, registered provenance, duplicates and disclaimer
separation, and prints only persona/surface/rule metadata. Never replace these fixtures with
production birth data, Tarot questions or reading prose. `infra/hetzner/deploy.sh` runs this reviewer
again inside the newly built app image before any migration or public container replacement.

For a release containing Lá Hỏi, also complete both spread sizes from `/tarot`, refresh the private
session route, verify an unsafe question receives a reframe, delete the result, and follow one Daily
Note and one owner-only Radar prompt into Tarot. Public/recipient Radar must not show the private
Tarot bridge. Confirm the cleanup output includes `Tarot session(s)` and that no question or reading
text appears in application/proxy logs.

The release ID is the 12-character Git commit SHA. Commit and push the intended release to public
`main` before transferring it to the server. Record the full SHA locally:

```sh
git rev-parse HEAD
git rev-parse --short=12 HEAD
git branch -r --contains HEAD
```

If `origin/main` is not listed by the last command, merge or push through the project's normal
review workflow first. Do not deploy an uncommitted worktree or a source tree that is unavailable to
users under the AGPL posture.

Create a clean archive locally, replacing `<RELEASE_ID>` with the printed 12-character SHA:

```sh
git archive --format=tar -o /private/tmp/la-lanh-<RELEASE_ID>.tar <RELEASE_ID>
shasum -a 256 /private/tmp/la-lanh-<RELEASE_ID>.tar
scp -i ~/.ssh/la_lanh_hetzner_ed25519 /private/tmp/la-lanh-<RELEASE_ID>.tar root@2.28.136.44:/opt/la-lanh/releases/
```

On the VPS, extract it without copying `.git`, local databases, `.env`, caches, or dependencies:

```sh
install -d -m 0755 /opt/la-lanh/releases/<RELEASE_ID>/source
tar -xf /opt/la-lanh/releases/la-lanh-<RELEASE_ID>.tar -C /opt/la-lanh/releases/<RELEASE_ID>/source
```

Copy only the non-secret server configuration from the last release, or initialize it from the
example on the first release:

```sh
cp /opt/la-lanh/current/infra/hetzner/app.env /opt/la-lanh/releases/<RELEASE_ID>/source/infra/hetzner/app.env
chmod 0600 /opt/la-lanh/releases/<RELEASE_ID>/source/infra/hetzner/app.env
```

Review the file without changing the established contract:

- exact origin: `https://la-lanh.2-28-136-44.sslip.io`;
- secure guest cookies enabled;
- generation disabled unless the Luna shadow checklist is the explicit purpose of this release;
- required web distribution enabled;
- Swiss Ephemeris license mode `agpl`.

`app.env` contains no secret values, but keep it server-only to avoid accidental environment drift.

## Phase 2 — secrets and database readiness

Normally, keep the existing secret files. Recreate the database URL only after a password rotation or
if the file is missing. From an interactive VPS terminal:

```sh
cd /opt/la-lanh/releases/<RELEASE_ID>/source
infra/hetzner/configure-database.sh rlowapjpwsamjftpggen <SESSION_POOLER_HOST>
```

The helper asks for the password with hidden input, percent-encodes reserved characters, requires TLS,
and writes the file without putting the credential into shell history.

If application keys are missing, generate fresh base64-encoded 32-byte values directly into the
secret files. Rotating existing keys is a separate migration because it can invalidate or make
existing encrypted guest data unreadable; do not rotate them casually.

Verify permissions, never contents:

```sh
chmod 0700 /opt/la-lanh/secrets
chmod 0600 /opt/la-lanh/secrets/database_url /opt/la-lanh/secrets/guest_hash_key /opt/la-lanh/secrets/guest_encryption_key
chown 65532:65532 /opt/la-lanh/secrets/database_url /opt/la-lanh/secrets/guest_hash_key /opt/la-lanh/secrets/guest_encryption_key
```

For an approved Luna shadow release, write the OpenAI key through an interactive hidden-input step;
never paste it into chat or pass it as a shell argument. Then apply and verify permissions without
printing the value:

```sh
chmod 0600 /opt/la-lanh/secrets/openai_api_key
chown 65532:65532 /opt/la-lanh/secrets/openai_api_key
test -s /opt/la-lanh/secrets/openai_api_key
```

## Phase 3 — build, probe, migrate, and start privately

From the new release directory on the VPS, use the committed deployment script as the single source
of truth. It validates secrets and licensing, selects the `generation` profile only when explicitly
enabled, builds the image once, reruns the content review, migrates, and waits for health:

```sh
cd /opt/la-lanh/releases/<RELEASE_ID>/source
export APP_HOSTNAME=la-lanh.2-28-136-44.sslip.io
export LA_LANH_RELEASE_ID=<RELEASE_ID>
export LA_LANH_SECRETS_DIR=/opt/la-lanh/secrets
infra/hetzner/deploy.sh
docker compose -f infra/hetzner/compose.yaml run --rm --no-deps app alembic current
docker compose -f infra/hetzner/compose.yaml ps
```

When generation is enabled, `ps` must show `rewrite-worker` healthy with no public port. Confirm the
API container does not mount `/run/secrets/openai_api_key`, and the worker mounts neither the guest
hash key nor any public port; do not use `docker inspect` formats that print environment values.

The TLS probe intentionally checks the configured TLS policy plus a real query. `pg_stat_ssl` may not
give useful results through Supavisor and is not the release gate.

Since 2026-10-08, migration `20261008_0028` also isolates backend tables from Supabase Data API:
RLS enabled, `PUBLIC`/`anon`/`authenticated` table grants revoked, and current migration-owner
default table grants revoked. `deploy.sh` runs `scripts.check_database_privacy` after migration
and **before** replacing the app. Any public table missing RLS or retaining client grants is No-Go.
Keep the existing backend DB role for this release; a lower-privilege backend role is a separate
migration with retention and deployment rehearsal. Never restore browser grants during rollback.
This changes access control, not rows, credentials or keys. The guard needs rerunning if tables
are later created by a different migration owner. See [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security).

Verify readiness from inside the private app container:

```sh
docker compose -f infra/hetzner/compose.yaml exec -T app python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/v1/ready', timeout=5).status)"
```

Do not start or restart public Caddy if migration or private readiness fails. Fix the release or return
to the known-good app image first.

## Phase 4 — firewall, Caddy, and certificate

For a first deployment, open host UFW and Hetzner Cloud firewall only after private readiness passes.
For an ordinary update these rules should already exist.

In the Hetzner UI, create **separate** inbound rules for TCP 80 and TCP 443. The port field does not
accept `80,443`. Keep 8080 closed. UDP 443 is optional for HTTP/3 but is already allowed in the known-
good host configuration.

Start the full stack:

```sh
docker compose -f infra/hetzner/compose.yaml up -d --remove-orphans --wait
docker compose -f infra/hetzner/compose.yaml ps
docker compose -f infra/hetzner/compose.yaml logs --since 10m caddy
```

On a first certificate issuance, a brief TLS alert can occur before Caddy finishes the ACME flow.
Wait and confirm `certificate obtained successfully` in Caddy logs instead of weakening TLS or
reconfiguring the proxy.

After the public stack is healthy, update the active pointer:

```sh
ln -sfn /opt/la-lanh/releases/<RELEASE_ID>/source /opt/la-lanh/current.next
mv -Tf /opt/la-lanh/current.next /opt/la-lanh/current
```

If `/opt/la-lanh/current` is still a real directory from the first deployment rather than a symlink,
preserve it as a legacy release before performing this one-time conversion. Never delete the active
tree while containers or rollback evidence depend on it.

## Phase 5 — public smoke and browser acceptance

After read-only HTTPS smoke, run the committed core-flow acceptance script with an explicit
synthetic-only write acknowledgement. It creates a new cookie jar (never reads a user's session),
tests date-only/Aura/charts, context-bound share/revoke, Tarot 1/3/5 and Radar exact/unknown,
then deletes only its own guest and records. It does not call a paid model when generation is off.
Failure is No-Go; fix the cause, rerun and record the evidence, not just the landing-page status.

```sh
LA_LANH_SMOKE_WRITE_CONSENT=synthetic-only node scripts/qa-public-smoke.mjs https://la-lanh.2-28-136-44.sslip.io
```

Do not print cookies, CSRF tokens, DB URL, private result IDs or share capabilities during QA.

Run from either the VPS release directory or a trusted local checkout:

```sh
infra/hetzner/smoke.sh https://la-lanh.2-28-136-44.sslip.io
```

The smoke script deliberately sends `Accept: text/html` for SPA routes. A default curl request with
`Accept: */*` may receive `404` on a deep link by design and does not prove the browser route is broken.

Browser acceptance, in a fresh/private session:

- `/welcome` renders, has the expected title, and has no console errors;
- direct navigation to `/home`, `/radar`, and `/privacy` renders without a blank page;
- `/privacy` names the current processors and links to public source and `LICENSE`;
- mobile-width layout has no clipped critical text or controls;
- network responses include HSTS, `no-referrer`, `noindex`, `no-store`, CSP, COOP,
  Permissions-Policy, and `X-Frame-Options`;
- cookies created by the flow are `Secure` and host-only;
- a mutation without a CSRF token is rejected.

Then complete a synthetic data-writing test:

1. welcome -> consent -> synthetic birth date -> reveal -> home -> daily note;
2. add synthetic time/place and verify the richer profile survives refresh;
3. complete Radar private input, reload the result, and verify share controls;
4. delete the synthetic result/profile and verify revoked capability URLs are no longer readable.

Do not use real birth or relationship data for this operator test.

## Phase 6 — operations gates

Run both retention jobs once, record aggregate counts only, and then schedule them at least every six
hours:

```sh
docker compose -f infra/hetzner/compose.yaml run --rm --no-deps app python -m scripts.cleanup_guests --batch-size 500
docker compose -f infra/hetzner/compose.yaml run --rm --no-deps app python -m scripts.cleanup_expired --batch-size 500
```

Install or refresh the committed systemd timers after the active release pointer has been updated:

```sh
cd /opt/la-lanh/current
infra/hetzner/install-retention-timers.sh
systemctl list-timers --all 'la-lanh-*-cleanup.timer'
```

The installer immediately runs both services once, then schedules guest cleanup at `00/06/12/18:25`
and bounded-data cleanup at `00/06/12/18:40`, with a small randomized delay. Each service resolves
the immutable image tag from the healthy production container, starts a short-lived non-root app
container through the standard secret-file entrypoint, and never prints personal payloads.

Before inviting external testers, record the actual backup/restore capability of the active Supabase
plan. Do not claim point-in-time recovery or automated backups unless the dashboard and plan confirm
them. A restore rehearsal must happen in an isolated project/database and must account for deletions
made after the restore point.

The current production closed beta passed availability checks, a full synthetic data-writing E2E,
the controlled restart and rollback dry run on 2026-09-29. Cleanup timers are active and verified.
The Supabase backup capability record and isolated restore rehearsal remain open until the companion
checklist says otherwise.

## Phase 7 — release evidence and handoff

Append or update the “Known-good deployed release” table in the deployment plan with:

- UTC deployment date/time;
- full commit and 12-character image tag;
- image digest from `docker image inspect`;
- public URL and certificate issuer/status;
- migration head;
- smoke/browser results;
- current and previous image tags;
- unresolved checklist items and exact next action.

Use this handoff template for the next session:

```text
Public URL:
Current release commit/image:
Previous release commit/image:
Image digest:
Migration head:
Smoke result and timestamp:
Browser E2E result and timestamp:
Retention timer status:
Backup capability/restore drill status:
Unresolved blockers:
Secrets: remain only on VPS; not copied or displayed.
```

## Rollback

Rollback changes the application image/source only. It does not downgrade the live database.

1. Record failing and previous release IDs.
2. Confirm the previous app is compatible with the current, already-migrated schema.
3. From the previous release source directory, export the previous immutable
   `LA_LANH_RELEASE_ID`, the same `APP_HOSTNAME`, and the secrets directory.
4. Run Compose without `build` and wait for health.
5. Restore `/opt/la-lanh/current` to the previous source pointer only after health passes.
6. Run public smoke and browser deep-link checks again.
7. Preserve the failed image and logs until the incident is understood; never include secret values
   or capability URLs in the incident record.

If the previous image was pruned, rebuild it only from the matching public Git commit. If schema
compatibility is uncertain, stop traffic and diagnose rather than guessing or downgrading.

## Incident triage

```sh
docker compose -f /opt/la-lanh/current/infra/hetzner/compose.yaml ps
docker compose -f /opt/la-lanh/current/infra/hetzner/compose.yaml logs --since 15m app rewrite-worker caddy
curl --fail https://la-lanh.2-28-136-44.sslip.io/v1/ready
systemctl --failed
ufw status verbose
```

Redact or avoid any URL containing a share/capability token before saving diagnostic output.

## Known pitfalls and their proven fixes

1. **Reserved characters in the Supabase password:** always use `configure-database.sh`; manual URLs
   can break parsing. Alembic also needs encoded percent signs escaped for its configuration layer.
2. **Secret permission failures:** parent directory is `0700`; files are `0600` and owned by
   `65532:65532`.
3. **Wrong Supabase mode:** use the IPv4 Supavisor **session** pooler on `5432` with `ssl=require`,
   not transaction mode or a browser-side key.
4. **Misleading TLS introspection:** Supavisor may hide `pg_stat_ssl`; use the shipped TLS probe and
   successful query.
5. **Buildx warning:** a non-fatal output/import warning is not a deployment failure if the tagged
   image exists and Compose starts it.
6. **Early TLS alert:** normal while Caddy is obtaining the first certificate; inspect Caddy logs and
   wait for issuance.
7. **SPA curl 404:** send `Accept: text/html`; the smoke script already does this.
8. **Hetzner port syntax:** add TCP 80 and TCP 443 as separate firewall rules.
9. **Privacy leaks in logs:** keep both proxy and app access logs disabled because tokens can occur in
   paths.
10. **Secret exposure during debugging:** inspect file metadata and health status, never `cat` secret
    files or run `docker inspect` output through a public transcript without redaction.

## Official references

- Docker on Ubuntu: https://docs.docker.com/engine/install/ubuntu/
- Docker Compose plugin: https://docs.docker.com/compose/install/linux/
- Caddy automatic HTTPS: https://caddyserver.com/docs/automatic-https
- Supabase database connections: https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase product security: https://supabase.com/docs/guides/security/product-security
- Hetzner firewalls: https://docs.hetzner.com/cloud/firewalls/
- Hetzner backups: https://docs.hetzner.com/cloud/servers/backups-snapshots/overview
