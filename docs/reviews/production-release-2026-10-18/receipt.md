# Production release 4111f03cee3c — 18/10/2026

Owner approval (chat, 18/10/2026): "okie golive nhé", then, after choosing "rehearsal first, then
go-live", "okie chạy d3 và go live đi". Content approval for Tarot B2:
`docs/reviews/2026-10-18-b2-tarot-owner-approval.md`.

## What is live

| Item | Value |
|---|---|
| URL | https://la-lanh.2-28-136-44.sslip.io |
| Release / source | `4111f03cee3c` = public `main`, fast-forward of `collab/integration` after merging PRs #20 → #31, each with Codex APPROVE matching its head (merged with `--match-head-commit`). Tree identical to the last approved head `59dfd805e66e` |
| Scope | P1 variety baseline (#20, audit only), B3-1a Daily rotation (#21, **off**: `LA_LANH_DAILY_VARIETY_FROM` unset), G0 grammar composer (#22, not served), Tarot B2-1 → B2-4b (#23 → #27), owner approval + fallback pin (#28, #29, #30), least-privileged rehearsal (#31) |
| Image | `la-lanh:4111f03cee3c`, digest `sha256:3194d73b9762…`, saved at `/opt/la-lanh/releases/la-lanh-image-4111f03cee3c.tar` |
| Database | Alembic `20261011_0036` → `20261018_0037` (adds `tarot_variant_cursors`) |
| Flags | generation/worker off, auth/Google off, Swiss Ephemeris `agpl`, Daily rotation off |
| Rollback | **No verified rollback anchor for B2 data yet** (see "Rollback limit" below). `la-lanh:836222282dfc` is present and starts against schema 0037, but it cannot reopen framed Tarot readings stored since go-live |
| Staging | same image digest, own DB migrated to 0037, generation off |

## Evidence

- Gate on `59dfd805e66e` (tree identical to `4111f03cee3c`): `pnpm check` exit 0 — 452 web tests, 2109 API
  passed / 56 skipped, contracts, runtime/privacy guards, grammar and fallback approval current, content
  audits, `tarot:audit` (T4 per session 98.99% / question only 84.98%, 5,340 provider payloads traced,
  psychology checklist on 7,104 readings), QA CLI smoke. Legacy Tarot golden unchanged.
- Backup `la-lanh-20261018T155045Z.dump` (732K, checksum OK), read-only `pg_dump` of `public`.
- **D3 rehearsal** (runbook "Tarot B2 (US-20)") with the release image, newest backup restored into a
  disposable TLS PostgreSQL on an internal Docker network, app connected as the NOSUPERUSER/NOBYPASSRLS
  backend role that owns the restored tables:
  - `Head before: 20261011_0036` → `Head after: 20261018_0037`; `guest_sessions` 27 → 27;
  - `database-privacy-isolation-ok`, `tarot-cursor-rehearsal-ok`, `Rehearsal readiness OK`, exit 0;
  - container and network removed;
  - `pg_restore` ignored 7 errors, all expected: `CREATE SCHEMA public` (already present, owned by the
    backend role) and six `ALTER DEFAULT PRIVILEGES` for the Supabase-only `postgres` / `supabase_admin`
    roles. No table or data errors (dump: 38 tables, 38 table-data entries). Run twice with the same result.
- `deploy.sh`: database TLS OK; content review in the image passed (direct and Roast, 10 personas × 30
  readings, no critical/high/medium); migration 0036 → 0037; `database-privacy-isolation-ok`; app and
  Caddy healthy; `alembic current` = `20261018_0037 (head)`.
- Smoke: `infra/hetzner/smoke.sh` passed on production and staging. `qa-public-smoke.mjs` (synthetic only,
  from `main` = `4111f03cee3c`) passed: date-only note, share/revoke, Aura and charts, Tarot 1/3/5, Radar
  exact/unknown, and deleted its own guest.
- Browser acceptance, production, synthetic question ("Mình có nên nhận thêm việc ở chỗ làm không?",
  work, 3 cards): framed reading with the dynamic headline, the "Hướng nghiêng" block with reasons, a
  linked summary and a question-form lead in the role sentence; a refresh shows the same reading; "Xóa bài
  này" → "Xóa hẳn" deletes it and the old link shows "Không mở lại được lần bốc này"; a third-party question
  ("Anh ấy có quay lại với mình không?") gets the reframe and creates no session. The Tarot-only guest
  cookie of this check holds no session and expires with the 30-day inactivity cleanup.

## Rollback limit

Schema compatibility is not data compatibility. Migration 0037 only adds `tarot_variant_cursors` and its
downgrade is a no-op, so `la-lanh:836222282dfc` starts against the new schema. But framed (B2) readings store
`small_action: null` on positions that are not the step role, while `TarotReadingPosition.small_action` is a
required `str` in the 836222282dfc model. Its `TarotSessionService._view` validates the stored reading, so
reopening a B2 reading created after go-live raises a validation error (server error) under that image.
Reproduced with synthetic data by Codex on PR #32 and locally: a framed THREE_UNBLOCK reading is rejected
at `positions.0.small_action` and `positions.1.small_action` (`string_type`), while a legacy (frameless)
reading of the same cards validates.

Therefore:

- `la-lanh:836222282dfc` is **not** a safe rollback image for this release. Using it in an emergency means
  accepting that B2 readings created since go-live fail to reopen until production rolls forward again; the
  stored data is not changed by the old image.
- Stored guest readings are not deleted or rewritten to make an old image work.
- An image counts as a safe rollback anchor only after (a) its reader accepts the B2 reading shape (at least
  an optional `small_action`; the extra `stance` key is ignored by the older model) and (b) a probe on a
  disposable copy reopens a reading created by `4111f03cee3c`. Preparing such an image or any runtime change
  is a separate, owner-authorised task. Until then, the recovery path is a forward fix.

## Found during release

1. **Staging lost its Caddy site after the production deploy.** `infra/hetzner/sites/staging.caddy` is a
   server-local file (not in git). The new release directory did not have it, so the recreated production
   Caddy no longer served `staging.la-lanh…` (TLS internal error); production was unaffected. Fixed by
   copying the file from the previous release directory and restarting the Caddy container (a few seconds
   of production restart, same image and config); both smokes pass afterwards. The runbook now says to copy
   it before `deploy.sh`; automating it is a follow-up. The same step had already been written down in PR #17 (hotfix receipt
   `836222282dfc`, approved but not yet merged at the time), which is why the release checklist missed it.
2. A typo in the full SHA while uploading the source produced an empty archive on the first try; the
   upload was redone from the `collab/integration` ref. No effect on the release.

## Not covered

Real devices/iOS/Android, real-user comprehension, Luna generation (off; prompt update for the brief v3
provenance labels is required before any activation), Google login (off), the B3-1a Daily rotation start
date (owner decision).

## Addendum — 19/10/2026: B3-1a Daily rotation enabled

Owner instruction (chat, 19/10/2026): "lên hết production đi, để tôi cho người dùng dùng thử".

- PR #32 (this receipt, APPROVE @ `069a5eefda13`) merged into `collab/integration`; `main` fast-forwarded to
  `4f595a35dd68`. The only change under `apps/` is one grammar test assertion, so production keeps running
  image `la-lanh:4111f03cee3c` (no rebuild needed for the merge itself).
- `LA_LANH_DAILY_VARIETY_FROM=2026-10-19` added to the production and staging `app.env` (previous files kept
  as `app.env.pre-daily-variety`). 19/10 is after the B3-1a deploy day (18/10), as the runbook requires; notes
  already opened on 19/10 replay unchanged, new days use the per-person rotation.
- Applied with the standard `deploy.sh` (same image; content review, privacy check and health passed) and
  staging `up.sh`. Inside the image `Settings().daily_variety_from` = `2026-10-19`.
- After the change: `smoke.sh` passed on production and staging; `qa-public-smoke.mjs` (synthetic only)
  passed, including the date-only Daily note, Tarot 1/3/5 and Radar, and deleted its guest.
- Not enabled: Luna (prompt update for brief v3, budget, key and DPA approval pending), Google login.
- Turning it off: remove the line (or restore `app.env.pre-daily-variety`) and rerun `deploy.sh`; stored notes
  keep their frozen plans, and a note reopened that day may show `available_update` (runbook "Daily rotation").
