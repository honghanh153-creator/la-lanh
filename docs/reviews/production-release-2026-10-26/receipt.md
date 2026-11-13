# Production release 89ebdb0cf6b9 — 2026-10-26

Owner order (26/10/2026, Issue #2): release #75 per `hetzner-supabase-release-runbook.md`. (1) Take a new
protected backup, verify a restore and re-enable the backup/check timers per #43. (2) Deploy the integration head
that Codex checked green to staging, run migration `20261023_0038_erasure_journal`, smoke staging. (3) If staging
passes, merge #75, deploy production, smoke, record this receipt and refresh `approved_release`. Keep flags, locks
and private caps unchanged. No Luna rollout change or new provider. Forward-only (P07/B). Stop on any red step.
Operator: Claude over SSH, with synthetic identities only. No step was red.

## Source

- Candidate `collab/integration` = `7e6d69e1bb39f300d06ac0ee5c14471887bf60d4`, tree
  `0768400274b6111946282eb05fe6748ade9649b3`. Independent Codex `CI=1 pnpm check` **PASS** at that commit (r32,
  09:50–09:57 UTC): web 513 / 78 files, API 2,559 passed / 57 skipped / 1 strict xfailed, QA PASS, E2E 8/8,
  contracts, privacy, grammar/fallback, audits, lint and typechecks
  ([receipt](https://github.com/honghanh153-creator/la-lanh/pull/75#issuecomment-6413239465),
  [confirmation](https://github.com/honghanh153-creator/la-lanh/issues/2#issuecomment-6413444928)).
- #75 merged with `gh pr merge 75 --merge --match-head-commit 7e6d69e…` → `main` =
  `89ebdb0cf6b974994b7f67807873ac320b5ed228` (parents `c3fab33`, `7e6d69e`). Its tree equals the candidate tree, and
  a `diff -rq` of the unpacked sources on the host showed no differences except server-only files. `collab/integration`
  was then fast-forwarded to the same commit.
- The four PRs open at release time are **not** included: #83, #87 and #88 (Codex APPROVE, outside the release by
  order) and #89 (Codex REQUEST_CHANGES).
- Content gates on the candidate: `content:audit`, `tarot:audit`, `content:review`, `experience:audit` exit 0;
  `bash -n infra/hetzner/*.sh` OK; repository PUBLIC.

## Step 1: backup, restore probe, rehearsal (before any service change)

| Check | Result (UTC) |
|---|---|
| Pre-state | `current` → `c3fab3311d65`; app, worker and Caddy healthy; only the guest and expired cleanup timers installed; newest backup 2026-10-21 |
| Backup | `backup-database.sh` (verify-full TLS) → `la-lanh-20261026T095223Z.dump` (704K), `sha256sum -c` OK, both files 0600 root. 14-day retention removed the 2026-10-11 dumps |
| Restore probe | `rehearse-migration.sh` with image `c3fab3311d65`: 28 guest sessions restored, head stays `20261018_0037`, `database-privacy-isolation-ok`, `tarot-cursor-rehearsal-ok`, readiness ready, disposable container and network removed |
| Migration 0038 rehearsal | the same script with candidate image `7e6d69e1bb39` on a disposable restore of that dump: `0037 → 0038`, 28 rows kept, privacy isolation OK, cursor OK, readiness ready, removed |

The 7 `pg_restore` warnings in both runs are the Supabase-only roles and default privileges the script expects.
Neither run is the interleaved restore/journal replay probe (see "Still open").

## Step 2: staging (`staging.la-lanh.2-28-136-44.sslip.io`)

- Image `la-lanh:7e6d69e1bb39` (`sha256:cf4880910d6f…`) built on the host before any deploy. The previous staging
  infra was archived (`infra-before-7e6d69e1bb39.tgz`, `infra.c3fab3311d65`). Then `up.sh` ran with the release
  infra and the server-only `generation.env` kept. The effective staging `app.env` is byte-identical to before, so
  flags are unchanged and auth is off.
- `alembic current` = `20261023_0038 (head)`; `check_database_privacy` passed; production `app` alias guard passed.
- `smoke.sh` PASS. Security headers present: HSTS, `no-referrer`, `noindex, nofollow, noarchive`, `no-store`, CSP,
  COOP, Permissions-Policy, `X-Frame-Options: DENY`. SPA routes return 200 for `text/html`.
- `qa-public-smoke.mjs` at the candidate: daily note, share → revoke, exact chart/Aura/charts, Tarot 1/3/5,
  Radar private exact/unknown, all cleaned up, guest deleted.
- Radar receipt and D2 API (#80), two synthetic guests: invite; B preview with `no-referrer` and `no-store` and no
  A birth data; accept; receipt readable; `GET /v1/radar/received` lists the result and B opens it; A gets 404 on
  B's route; withdraw without CSRF is rejected, with CSRF returns 204; afterwards B gets 404, the list no longer
  holds it, the receipt is 404 and A's owner result is 404; both guests deleted. A mutation without a
  session/CSRF returns 401.
- Browser: Home Note ngày renders; Lá Hỏi with 3 cards on a self-care question shows a consistent lean and step;
  delete confirm → session 404.
- Logs (staging app/worker, Caddy, last 30 min): no question text, synthetic birth data/labels or invite tokens;
  no errors.
- The D2 **web screen** ships with #83 and is not in this release.
- Evidence comment: [#75 issuecomment-6413542960](https://github.com/honghanh153-creator/la-lanh/pull/75#issuecomment-6413542960).

## Step 3: production (`la-lanh.2-28-136-44.sslip.io`)

- Release directory `/opt/la-lanh/releases/89ebdb0cf6b9/source` from `git archive` (archive SHA-256 matched on the
  host). `app.env` and `sites/staging.caddy` were copied from the verified live release `c3fab3311d65`; `app.env`
  is byte-identical, and the release adds no new keys.
- `deploy.sh`: database TLS, content review, `alembic upgrade 20261018_0037 → 20261023_0038`,
  `database-privacy-isolation-ok`, app, worker and Caddy recreated and healthy. Image `la-lanh:89ebdb0cf6b9` =
  `sha256:8fcab2f44e273ac430baa4c1f02d4e44be0215008509b6da416277b4383ec4ed`.
- `alembic current` = `20261023_0038 (head)`. Port 8080 has no host listener. The API container does not mount the
  provider key. The `app` alias resolves to one container.
- `current` → `/opt/la-lanh/releases/89ebdb0cf6b9/source` (atomic `mv -Tf`).
- Staging was recreated on `la-lanh:89ebdb0cf6b9`, so production and staging run the same digest. Staging stayed
  reachable after the Caddy recreate.
- `smoke.sh` PASS; `/v1/ready` 200 on both hosts. `qa-public-smoke.mjs` (synthetic-only) PASS for every flow above.
  The two-guest Radar receipt and D2 API smoke passed on production with the same checks as staging. All
  synthetic guests were deleted.

## Operations after release

- `install-backup-timer.sh` from `current`: `la-lanh-backup.timer` (20:10 UTC), `la-lanh-backup-check.timer`
  (every six hours) and `la-lanh-erasure-journal.timer` (hourly) are enabled. First runs succeeded:
  - backup `la-lanh-20261026T102155Z.dump`, `sha256sum -c` OK;
  - freshness check "Backup OK … under 26h, checksum verified";
  - journal export of 6 digest-only entries (the synthetic smoke erasures) to
    `/opt/la-lanh/backups/erasure-journal/` (0600), and the purge removed 0 entries.
- No alert markers.
- `install-retention-timers.sh` refreshed; guest and expired cleanup timers active, last results `success`.

## Flags and limits (unchanged)

Production and staging generation settings are exactly as before: Luna on for `daily_home` only, private caps and
pilot limit unchanged, and the values are not recorded here. Tarot is allowlisted, not on. No provider was added or
enabled. Auth stays off on staging.

## Rollback

Forward-only. Migration 0038 only adds tables, but no probe has shown that `c3fab3311d65` starts and serves on schema
0038, so it is **not** a verified rollback anchor. Even if it is, rolling back would stop erasure journaling while
the journal timer keeps running. Prefer a forward fix. Never run an automatic Alembic downgrade or restore into service: **P07/B holds**.

## Still open

- **P07:**
  - the interleaved PostgreSQL restore/journal replay probe (operator, disposable database);
  - the alert channel (the failure marker and journal entry are local only; no message delivery);
  - the Supabase plan backup/PITR record;
  - the unjournaled erasure kinds listed in `backup-restore-and-deletion-reconciliation.md`.

  B stays the rule.
- **Hygiene (P3, already present before this release):** some `delete_cookie` calls in `guest_sessions.py` clear
  cookies without `Secure`. This is harmless on HTTPS but inconsistent.
- **Next integration work:** merge the approved #83/#87/#88 and fix #89 (two P2s). Each needs its own check before
  any later release.
