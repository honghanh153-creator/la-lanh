---
title: Hetzner + Supabase public beta deployment
date: 2026-09-26
status: deployed-with-operations-follow-ups
deepened: 2026-09-26
deployed: 2026-09-26
---

# Hetzner + Supabase public beta deployment

## Goal capsule

Publish the current Lá Lành web product at a stable public HTTPS URL while keeping the existing one-origin session/CSRF model, birth and relationship data protections, chart-engine readiness checks, and deletion/retention behavior intact.

Success is not merely a reachable page. A fresh user must be able to complete the core web flow against the deployed PostgreSQL database, refresh deep links without a blank page, and receive secure cookies over HTTPS. The release must also have a documented rollback and an operator checklist that can be reused.

## Scope

### In scope

- One Hetzner VPS at `2.28.136.44` running the existing containerized Vite + FastAPI + Swiss Ephemeris application.
- Supabase PostgreSQL as the managed database; the FastAPI backend is the only database client.
- Caddy as the public TLS terminator and reverse proxy.
- Docker Compose deployment, environment templates, migration/cleanup commands, smoke checks, and rollback instructions.
- A temporary DNS-derived beta hostname when no owned domain is available, replaceable later without changing the app architecture.
- A repeatable manual first deployment from the trusted local checkout. CI/CD is deferred until the first deployment is proven.

### Out of scope

- Native iOS/Android publication.
- Supabase Auth, Data API, Realtime, Storage, or browser-side Supabase keys.
- AI-generated readings; generation remains disabled.
- Open/public marketing launch, search indexing, distributed edge rate limiting, or production-scale observability.
- Rewriting the existing product features or database model.

## Current baseline

- The VPS has key-only SSH, password login disabled, UFW, unattended security updates, AppArmor, and a Hetzner cloud firewall.
- The application already serves its built SPA and API from one origin through `apps/api/app/cloud_run.py` and disables Uvicorn access logs.
- Runtime settings reject staging/production unless PostgreSQL, secure cookies, managed cryptographic keys, HTTPS origins, and a non-development Swiss Ephemeris license posture are configured.
- The database schema is managed by Alembic through `apps/api/migrations/`.

## Known-good deployed release

This is the recovery anchor for a future session. It contains no credentials.

| Item | Verified value |
|---|---|
| Public URL | `https://la-lanh.2-28-136-44.sslip.io/welcome` |
| Source repository | `https://github.com/honghanh153-creator/la-lanh` (public) |
| Deployed application commit/tag | `9076c1b1e629` / `la-lanh:9076c1b1e629` |
| Deployed image digest | `sha256:2ebe3cf17a9f8b74b44ea6bc7ae77e911e39111b42ae8d56ee97e74e22292fdd` |
| Previous rollback image | `la-lanh:b391e6610840` |
| Supabase project | `rlowapjpwsamjftpggen`, Frankfurt |
| Reverse proxy | Caddy `2.10.2` with a valid Let's Encrypt certificate |
| Database | Supavisor session pooler on port `5432`, TLS required |

Verified again on 2026-09-27 at 08:00 UTC for release `0b3fecb65297`: public health/readiness, SPA
deep links, HTTPS redirect and certificate, security/privacy headers, `/welcome`, and `/privacy`.
The public smoke script passed and the in-app browser loaded `/welcome` without console errors. A synthetic
production journey passed guest consent, birth chart, daily note, mood, save/share, place search,
time/place supplementation, full profile, owner claim, matching readiness, private Radar creation and
reload, deletion, capability revocation, unsave, and guest deletion. All synthetic records were
deleted. Scheduled retention/backup operations and the controlled rollback drill remain explicit
follow-ups below and must not be reported as complete.

Release `7f4940d7c59f` was deployed and verified on 2026-09-27 at 10:03 UTC. The release adds the
versioned 34-unit Vietnam birthplace catalog, all 29 former province-name lookups, complete matching
region options and an allow-list validation gate. Live acceptance proved the empty catalog returns
34 current units, `Đà Nẵng` resolves canonically and `Bình Dương` resolves with its current mapping
shown. The first release candidate exposed an API/service validation mismatch (`422` on empty browse);
the corrected release includes an API-level regression test so the defect cannot pass the release
suite again. The content delta for this release is the explicit, plain-language administrative-name
mapping; no unrelated astrology prose was added merely to satisfy the content gate.

Release `9076c1b1e629` was deployed and verified on 2026-09-28 at 11:28 UTC. It replaces typed own
birth time with the native time picker, adds an explicit `Không rõ giờ` path to private Radar, removes
Moon/Rising/House and other time-dependent evidence from that reduced-precision reading, and opens a
clear Natal value path only after exact time and place are available. Full repository checks passed:
114 web tests, 353 API tests, OpenAPI/contracts, privacy/runtime guards, content/Tarot/Radar audits,
production build and QA deep-link proxy smoke. Public synthetic acceptance then completed the exact
birth/Natal path and unknown-time Radar path and deleted both the result and guest data. Migration
head remained `20260927_0022`; public smoke passed at the URL above.

## Architecture

```text
Browser
  -> HTTPS :443
  -> Caddy on Hetzner (automatic TLS, no request access log)
  -> app container :8080 on a private Compose network
  -> Supabase PostgreSQL over TLS using the IPv4 session pooler :5432
```

The frontend never receives a Supabase database password, service-role key, or direct database access. All application tables remain server-side and should be removed from the Supabase Data API exposed schemas where possible; RLS is retained as defense in depth if an exposed schema must be used.

## Key technical decisions

1. **Keep one origin.** This preserves the current host-only cookies and same-origin CSRF contract.
2. **Use Supavisor session mode on port 5432.** Hetzner is a long-running IPv4 backend and the application uses persistent asyncpg connections; transaction mode is unnecessary and has prepared-statement limitations.
3. **Do not store GitHub credentials on the VPS.** The first release is transferred from the committed local checkout and built on-server. A read-only deploy key or CI pipeline can be added later.
4. **Do not expose port 8080.** Only Caddy publishes 80/443; the app is private to the Compose network.
5. **Do not log request URLs.** Radar/share capability tokens may appear in paths. Caddy access logging stays off and Uvicorn already runs with `--no-access-log`.
6. **Run migrations as an explicit one-shot command before app replacement.** Schema changes are forward-only for this beta; rollback restores the prior image without reversing migrations.
7. **Use a generated beta hostname only as a temporary review URL.** An owned domain remains preferable before inviting a broad cohort.

## Requirements and acceptance criteria

| ID | Requirement | Acceptance evidence |
|---|---|---|
| R1 | Public HTTPS URL | Browser and `curl` receive a trusted certificate and HTTP redirects to HTTPS. |
| R2 | Core app available | `/welcome`, `/home`, `/radar`, and a direct SPA route return the app without a blank screen. |
| R3 | Backend ready | `/v1/health` and `/v1/ready` return 200; readiness includes PostgreSQL and Swiss Ephemeris. |
| R4 | Secure state | Cookies are `Secure`; mutation requests still enforce CSRF and exact trusted origin. |
| R5 | Private data path | Database connection uses TLS; no database secret appears in Git, client bundles, container metadata output, or logs. |
| R6 | Capability privacy | HTML/API responses are `no-store`, globally `noindex`, `no-referrer`, and neither Caddy nor Uvicorn records request paths. |
| R7 | Recoverable release | Previous image reference and environment backup are retained; rollback procedure is tested or dry-run validated. |
| R8 | Retention operations | Guest and bounded-feedback cleanup commands can be run and are scheduled at least every six hours. |
| R9 | Legal/license gate | External tester invitation does not proceed until Swiss Ephemeris posture and cross-border/privacy processor notice are approved. |

## Implementation units

### U1 — Hosting adapter and durable operator artifacts

**Goal:** add a Hetzner-specific Compose stack, Caddy policy, environment template, deploy/smoke scripts, and reusable runbook.

**Files:**

- `infra/hetzner/compose.yaml`
- `infra/hetzner/Caddyfile`
- `infra/hetzner/app.env.example`
- `infra/hetzner/deploy.sh`
- `infra/hetzner/smoke.sh`
- `docs/operations/hetzner-supabase-release-runbook.md`
- `docs/operations/web-beta-release-runbook.md`

**Verification:** Compose config renders with placeholder secrets supplied out-of-band; shell scripts pass `bash -n`; the container has no published 8080 port, uses `no-new-privileges`, and has bounded logs and a healthcheck.

### U2 — VPS container runtime and release directories

**Goal:** install supported Docker Engine/Compose components, create `/opt/la-lanh`, and preserve the hardened network baseline.

**External state:** Hetzner VPS.

**Verification:** Docker service active; `docker compose version` works; SSH remains key-only; UFW remains active; ports 80/443 remain closed until TLS deployment is ready.

### U3 — Supabase database contract

**Goal:** connect the VPS app to a user-created Supabase project using a TLS session-pooler URL and apply the committed Alembic migrations.

**External state:** Supabase project and database password supplied by the owner directly to the server, never through chat or Git.

**Verification:** TLS database connection succeeds; `alembic upgrade head` exits zero; `alembic current` equals head; `/v1/ready` reports ready.

### U4 — Secrets and release configuration

**Goal:** create a root-readable server environment file containing the database URL, fresh 32-byte hash/encryption keys, exact HTTPS origin, secure-cookie settings, disabled generation, and approved license mode.

**External state:** product-owner license decision and privacy/cross-border approval.

**Verification:** configuration validates in staging; file mode is `0600`; secrets do not appear in `git status`, `docker inspect`, shell history, or app logs.

### U5 — First application deployment

**Goal:** transfer the committed source snapshot, build a versioned image, migrate, start the app and Caddy, then open only ports 80/443 in host and Hetzner firewalls.

**Verification:** R1–R7 smoke evidence; container restart policy survives a controlled restart; no failed systemd units.

### U6 — Retention, backup, and operations

**Goal:** schedule cleanup jobs, enable/confirm Supabase backups appropriate to the selected plan, and document incident/restore/rollback procedures.

**Verification:** both cleanup commands run once successfully with aggregate-only output; timer definitions are active; backup capability and retention are recorded accurately.

### U7 — End-to-end beta acceptance

**Goal:** test the real user path in a fresh browser and record remaining launch blockers.

**Verification scenarios:**

- First visit -> consent -> birth date -> reveal -> home -> daily note.
- Birth time/place completion changes the profile layer and survives refresh.
- Radar private-input flow completes, result reloads, sharing controls obey the current product contract, and deletion works.
- Direct navigation to SPA routes works.
- Missing CSRF token is rejected.
- Revoked capability is no longer readable.
- Mobile-width page is usable and no critical text/control clips.

## Execution checklist

### Already complete

- [x] VPS deletion/rebuild protection enabled.
- [x] SSH key installed and password authentication disabled.
- [x] Host UFW and Hetzner firewall attached.
- [x] Automatic security upgrades and AppArmor active.
- [x] Rebooted into the patched kernel and verified zero failed services.

### Repository and server

- [x] Add and verify U1 artifacts.
- [x] Install Docker/Compose on VPS.
- [x] Create release directories and transfer a committed source snapshot.
- [x] Build the application image successfully on the 4 GB VPS.

### Owner unblockers

- [x] Create/select Supabase project `rlowapjpwsamjftpggen` in Frankfurt.
- [x] Put the Supabase **session pooler** connection string into the server secret file without pasting it into chat.
- [x] Product owner authorized an AGPL-compliant public-source release on 2026-09-26.
- [x] The in-app privacy detail names Hetzner Germany and Supabase Frankfurt as the beta processors/destinations.
- [x] Approve and deploy temporary hostname `la-lanh.2-28-136-44.sslip.io`.
- [ ] Replace the temporary hostname with an owned domain before a broad/public launch.

### Release

- [ ] For the next release, pass `pnpm content:audit`, record a meaningful content improvement and
      its regression fixture, or document an emergency security/availability waiver.
- [x] Generate production cryptographic keys on the VPS.
- [x] Run Alembic migrations to head.
- [x] Start app privately and pass local readiness checks.
- [x] Configure DNS/TLS and open inbound 80/443 while keeping 8080 closed.
- [x] Pass public smoke tests and browser acceptance for availability, deep links, privacy copy, and console health.
- [x] Run both cleanup jobs once for release `0b3fecb65297` (0 expired guest sessions; 0 expired
      experiments/resonance rows).
- [ ] Enable and verify recurring cleanup timers.
- [ ] Confirm and record the Supabase backup/restore capability for the active plan.
- [x] Run the full synthetic data-writing E2E journey in U7, including deletion/revocation checks.
- [ ] Perform a controlled restart and rollback dry run against the current schema.
- [x] Record image/version, URL, date, and unresolved launch risks.

## Rollback

- Keep the previous image tag and previous non-secret deployment manifest.
- If the new app fails before migration, restore the prior Compose image and restart.
- If it fails after a forward-compatible migration, restore the prior image only after confirming it can run against the new schema.
- Never restore an old database backup directly into service: first reconcile deletions made after the restore point, then validate privacy and ownership boundaries in an isolated database.

## Security and privacy review

- Birth date/time/place, coordinates, mood, inferred profiles, relationship inputs, and capability tokens remain sensitive personal data.
- Hetzner and Supabase are processors/subprocessors whose regions, purposes, retention, and deletion behavior must match the user-facing privacy notice.
- The temporary beta URL remains `noindex`; the cohort should be small and named.
- Host firewall SSH restriction is tied to the current operator IP. Network changes require updating UFW through the Hetzner console before SSH will work.
- The in-process admission limiter is not a distributed abuse-control layer; this is acceptable only for a small closed beta.

## Definition of done

- R1–R6 pass and evidence is captured in the runbook.
- R7 passes after a controlled restart and rollback dry run.
- R8 passes after both cleanup jobs run once, timers are active, and backup capability is recorded.
- U7 passes with synthetic test data and post-test deletion/revocation verified.
- No P0/P1 security or privacy defect is known.
- R9 is explicitly approved before external testers are invited.
- The deployment and rollback can be repeated from the runbook without relying on this conversation.

Until the remaining boxes are checked, describe this as a technically deployed closed beta, not a
fully operations-complete production release.

## Sources checked

- Docker Engine/Compose installation: https://docs.docker.com/engine/install/ubuntu/ and https://docs.docker.com/compose/install/linux/
- Caddy automatic HTTPS and reverse proxy: https://caddyserver.com/docs/automatic-https and https://caddyserver.com/docs/quick-starts/reverse-proxy
- Supabase PostgreSQL connection modes: https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase security guidance: https://supabase.com/docs/guides/security/product-security
- Hetzner Cloud firewalls/backups: https://docs.hetzner.com/cloud/firewalls/ and https://docs.hetzner.com/cloud/servers/backups-snapshots/overview
- Vietnam Personal Data Protection Law 91/2025/QH15: https://vanban.chinhphu.vn/?docid=214590&pageid=27160&typegroupid=3
