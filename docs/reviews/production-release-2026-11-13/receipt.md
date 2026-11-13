# Production release R1 f22a755f7128 + R2 f6246ed2fb7a — 2026-11-13

Owner order (13.11.2026, in chat): "đẩy hết lên production". Migration `20261029_0039` refuses to run in the same
upgrade that applies the `0038a` marker, so the release went in two steps per `hetzner-supabase-release-runbook.md`.
Operator: Claude over SSH, with synthetic identities only. Forward-only: no `alembic downgrade`, no restore into
service.

## Step R1: compatibility release (Alembic `20261029_0038a`)

- Source: #464 (`10b1f13` US-23 U1 + `main` with hotfixes #427, #430) → `main` = `f22a755`.
- Backup `la-lanh-20261113T050336Z.dump` before deploy.
- `deploy.sh`: content review passed; `0038 → 0038a`; `database-privacy-isolation-ok`; app, worker, Caddy healthy.
- `smoke.sh` PASS. `qa-public-smoke.mjs`: 9/9. It ran from a temporary copy, because the script still expected
  4 Radar sections; fixed in #467.
- Retention and backup timers present and running.
- Rollback anchor at the time: `la-lanh:1d3de55e041d` (schema 0038a = 0038).

## Step R2: full integration (Alembic `20261111_0042`)

### Source

- #463 brought the main hotfixes into `collab/integration`, after a G8 inventory fix requested by Codex; an
  inventory row was added to `docs/reference/data-inventory-us01-us06.md`.
- #472: `collab/integration` `cac542e` (186 PRs since main) merged with `main`. Two conflicts in
  `scripts/codex-review.mjs` and `scripts/collab-plan.mjs`: integration code kept, R1's CodeQL backslash escape
  re-applied.
- Two later test-only commits for CodeQL (`316ebc3`, `bfcbf7d`) compare the cited hostname by equality.
- Code-scanning alerts #2, #3 and #11 (`py/cookie-injection`) dismissed as false positives. The value only reaches
  Set-Cookie through `token_cookie_value()`, which raises unless it fullmatches `[A-Za-z0-9_-]{43}`.
- `main` = `f6246ed2fb7a5033247ad6b41af33f35022cab12`.

### Checks before deploy

| Check | Result |
|---|---|
| `pnpm check` on the release tree `e98ea89` (Mac, 13.11) | EXIT=0. Web 645/645 (95 files); API 10,679 passed, 72 skipped, 1 xfailed; e2e 13 passed, 1 skipped; content, Tarot, Radar, clarity and rewrite audits pass; QA CLI smoke pass |
| `pnpm collab:test` on the merged tree | 187/187 |
| CI on #472 at `bfcbf7d` | CodeQL (actions, js/ts, python, java-kotlin, swift) and screens pass; merge state CLEAN |
| New flags | `LA_LANH_HUMAN_TAROT_*` and `LA_LANH_MOOD_ENCRYPTED_WRITES` absent from production `app.env` (default off) |

### Server steps (UTC)

| Step | Result |
|---|---|
| Source | codeload tarball of `f6246ed` unpacked on the host into `/opt/la-lanh/releases/f6246ed2fb7a/source` (1,967 files). `app.env` and `sites/staging.caddy` copied from the R1 release |
| Backup | `la-lanh-backup.service` → `la-lanh-20261113T111412Z.dump` (439 KB), `sha256sum -c` OK |
| Rehearsal | `rehearse-migration.sh` (absolute path) with image `la-lanh:f6246ed2fb7a` on a disposable restore of that dump, as the least-privileged role. Head `0038a → 0039 → 0040 → 0041 → 0042`; `guest_sessions` 12 before and after; `database-privacy-isolation-ok`; `tarot-cursor-rehearsal-ok`; readiness ready. 7 `pg_restore` warnings are the expected Supabase-only roles |
| Deploy | `deploy.sh` with `APP_HOSTNAME`, `LA_LANH_RELEASE_ID=f6246ed2fb7a`, `LA_LANH_SECRETS_DIR`. Content review passed (10 personas, 30 readings, no critical or high findings). Same four upgrades as the rehearsal; `database-privacy-isolation-ok`; app, worker, Caddy healthy. Log: `releases/f6246ed2fb7a/deploy.log` |
| Image | `la-lanh:f6246ed2fb7a` = `sha256:b9e860240f01…`; staging runs the same image ID |
| `smoke.sh https://la-lanh.2-28-136-44.sslip.io` | PASS |
| `qa-public-smoke.mjs` (repo script at `bfcbf7d`, `LA_LANH_SMOKE_WRITE_CONSENT=synthetic-only`) | 9/9: daily note; share → revoke; exact chart → Aura → Western/Jyotish/Natal/Sky; Tarot 1/3/5; Radar exact/unknown (radar-result-v2 contract); QA guest deleted |
| `current` | `/opt/la-lanh/current` → `releases/f6246ed2fb7a/source`. It pointed one level too high for a few seconds and was corrected before any timer ran. The backup unit runs `current/infra/hetzner/backup-database.sh` |
| Timers | backup, backup-check, erasure-journal, guest-cleanup, expired-cleanup listed |
| `/v1/ready` | production 200, staging 200 |

### Staging

- Staging had been unhealthy for about 44 hours: its own database TLS certificate (30-day, from
  `make-db-tls.sh`) expired on 2026-11-10 11:26 UTC.
- The expired pair was kept as `secrets/tls.expired-20261110`. A new pair was created by the same script (valid
  to 2026-12-13) and the staging DB restarted.
- The staging database was still on `20261023_0038`, so the 0039 guard refused R2 as designed. Staging was
  brought up on R1 `f22a755f7128` (`0038 → 0038a`, privacy OK), then on R2 (`→ 0042`, privacy OK), with the same
  server-only env files and `STAGING_GENERATION=off`. Infra archived first as `infra-before-f6246ed2fb7a.tgz`.
- Production is not affected; it verifies Supabase's CA.

### G2 evidence for #463 (natal overview page)

- Staging, synthetic guest (2001-03-07 08:15 Hà Nội), `/insights/overview?tradition=jyotish`.
- At both 360 and 390 px: no horizontal scroll, one `h1`, six `h2`, no link or button under 44 px.
- Screenshots: [360 px](overview-jyotish-360.jpg), [390 px](overview-jyotish-390.jpg).
- The synthetic guest was deleted afterwards (204).
- Observation: the page shows only the background for about 4–6 s while the overview loads.

## Rollback

- Image `la-lanh:f22a755f7128` (`sha256:a0e57af3ad11…`, R1) is the immediate anchor. It runs on 0038a but not
  on 0039+, because 0039 drops the cascades R1 still relies on.
- After R2 a rollback is a forward fix. Do not run `alembic downgrade` on production without a separate decision.
- Restore into service is still forbidden (P07/B).

## Still open

- Staging DB TLS certificates last 30 days with no expiry alert. Add a watchdog or renewal so staging cannot
  silently go red again.
- Overview page loading state (the observation above).
- From the release review:
  - Dependabot alerts on Mako, glob and uuid;
  - `0041` downgrade is a no-op;
  - the store privacy data map still says US-23 is not released;
  - no kill switch for date correction or data export.
