# Production release c3fab3311d65 — 2026-10-21

Owner order (2026-10-21): after Codex APPROVE of PR #39, merge PR #33–#39, deploy staging then
production, and turn Luna on for the Daily note. Spend: owner-approved cap for all Luna writing
(private, server-only; not recorded in git). DPA: owner signs later.

## Source

- `main` = `collab/integration` = `c3fab3311d659c240da944a84fec305eca416cc6` (public repository).
- Merged with `gh pr merge --merge --match-head-commit`, each at its Codex APPROVE SHA:
  #33 `13c25f9`, #34 `e6debac`, #35 `8436bc5`, #36 `be668f8`, #37 `6fae045`, #38 `e2ffb2d`,
  #39 `2d025e9` (base retargeted from the #38 branch to `collab/integration` before merging).
- Owner copy approvals: #35 (Radar private check 24 hours, 2026-10-21), #37 (Luna opt-in, 2026-10-20),
  #38 (Daily history retention, 2026-10-21). US-21 AC05 decision recorded in #39.
- `pnpm check` on `c3fab33` before release: exit 0 — 459 web tests, 2133 API passed / 56 skipped,
  contracts, grammar/fallback approval, content/Tarot/experience audits, rewrite corpus manifest, QA
  smoke. `bash -n` on every Hetzner script passed. No Alembic migration in #33–#39.

## Runtime

- Backup before any change: `la-lanh-20261021T144155Z.dump` (733K, `sha256sum -c` OK).
- Release directory `/opt/la-lanh/releases/c3fab3311d65/source` from `git archive` (local and server
  SHA-256 prefixes matched). `app.env` and `sites/staging.caddy` copied from the **4111f03cee3c**
  release directory, not from `/opt/la-lanh/current` (see "Corrected" below).
- Image `la-lanh:c3fab3311d65`, digest `sha256:ff8247ab158b5449a9be0050a3daff1d3a568a308b9197221a69318e5664a9ae`.
  Production app and worker and staging app and worker all run this digest (staging recreated after
  `deploy.sh`).
- Staging first: image built ahead of production, staging infra refreshed (server-local
  `generation.env` kept), `STAGING_GENERATION=off ./up.sh`, `/v1/ready` 200, `smoke.sh` passed.
- Production `deploy.sh`: database TLS, content review (direct and Roast: 10 personas × 30 readings,
  no critical/high), `alembic upgrade head` (no change), `database-privacy-isolation-ok`, healthy.
  `/v1/health` and `/v1/ready` 200, `smoke.sh` passed, HTTP → HTTPS 308. Staging stayed reachable
  after the Caddy recreate. Firewall unchanged (22 restricted, 80/443).
- Browser (production `/privacy`): the new Daily-retention copy (#38) and the M1 Luna copy (#37) are
  served; the old "nhãn chiêm tinh liên quan" wording is gone; no horizontal overflow at 390 px.

## Luna (Daily note, M1)

- Production `app.env`: generation on, rollout `{"daily_home":"full"}` only (the M1 rollout guard
  refuses any other surface), pilot user limit 20, budgets set to the owner-approved private caps
  (production plus staging stay within the owner's total). Previous file kept as `app.env.pre-luna`.
  OpenAI key installed at `/opt/la-lanh/secrets/openai_api_key` (65532:65532, 0600), never printed.
- Staging with Luna on (same release): synthetic profiles through the real API. One candidate was
  rejected by the gate (`gate_rejected`; the deterministic note stayed), one passed and was offered as
  an update in about 10 s. Queued payload schema `daily-rewrite/v3` (no chart evidence).
- Production with Luna on: two synthetic profiles, both produced a gate-passed update in about 10 s.
  All production test guests were deleted (`DELETE /v1/guest-session` 204).
- **Pilot:** `daily_home` only, 14 days from 2026-10-21, at most 20 active opted-in sessions; review on
  2026-11-04 (end, extend, or require the full 670-case gate). The full gate stays not met (owner
  exception, PR #37 runbook); no `EvaluationRecord` exists.

## Corrected during this release

- **Kill switch:** setting generation off and redeploying left the profiled `rewrite-worker` running
  with `LA_LANH_GENERATION_ENABLED=true` (compose does not treat a profiled service as an orphan). It was
  removed by hand with `docker compose … --profile generation rm -sf rewrite-worker`, then Luna was
  turned back on (new worker, app and worker `true`). `deploy.sh` is fixed in this PR.
- **Stale `current` pointer:** `/opt/la-lanh/current` still pointed at `836222282dfc` after the
  2026-10-18 release (that release skipped the runbook switch), so the retention job read an old
  source tree. It now points at `c3fab3311d65`; both cleanup timers are active.

## Effects and limits to watch

- **Daily history (#38):** the first expired-cleanup run after deploy (18:43 UTC, 2026-10-21) applies
  the new window. Unsaved automatic Daily notes past it are deleted with their mood, except today's
  note and notes kept by a live experiment, feedback or share link. This deletion is irreversible;
  the backup above predates it.
- **Radar private check (#35):** new checks keep 24 hours; checks created before this release keep
  their original expiry.
- **AC05 (#39):** guaranteed within one calendar variant with stable inputs. Production has rotated
  notes since 2026-10-19 under the earlier guard, so a third identical situation can occur once at
  that transition. Opened notes are never rewritten.
- One synthetic staging guest from an interrupted script remains on staging only; it expires with
  the staging guest TTL.
- Rollback: image `la-lanh:4111f03cee3c` is schema-compatible (no new migration), but Daily notes
  deleted under #38 cannot be restored without the backup and a reconciliation.

## Still open

- DPA (owner, later; recommended under M1). Lawyer question on the app's hosting abroad. Daily backup
  timer not installed. Luna stays off for Tarot and Radar (rollout guard).
