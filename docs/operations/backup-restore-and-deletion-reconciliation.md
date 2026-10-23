# Backup, restore and deletion reconciliation

Audit 2026-10-22: P07 (backup/restore/physical deletion evidence) and O02 (daily backup). This file
prepares the operator and owner steps. Nothing here has been installed or run on the VPS by an
agent; each step below names who does it and what evidence closes it.

## What the code now provides (FIXED_LOCAL)

| Piece | File | Behaviour |
|---|---|---|
| Daily backup | `infra/hetzner/systemd/la-lanh-backup.{service,timer}` | 20:10 UTC (03:10 Vietnam time), `Persistent=true`, runs `backup-database.sh` (custom dump of `public`, `sslmode=verify-full`, checksum, 14-day retention), then the freshness check. Sandboxed: read-only system, writes only `/opt/la-lanh/backups`, `UMask=0077`. |
| Freshness check | `infra/hetzner/check-backup-freshness.sh`, `la-lanh-backup-check.{service,timer}` | After each backup and every six hours (02/08/14/20:50 UTC): fails unless the newest dump is under 26 hours old (`LA_LANH_BACKUP_MAX_AGE_HOURS`), non-empty and matches its `.sha256`. Reads only names, ages, sizes and checksums, never the dump contents. The independent timer catches a backup timer that silently stopped. |
| Failure marker | `la-lanh-alert@.service` (`OnFailure=` of both services) | Writes an err-priority journal entry (`la-lanh-alert`) and `/var/lib/la-lanh/alerts/<unit>.failed`. **No message delivery is configured**: someone or something must watch the journal or marker files. |
| Installer | `infra/hetzner/install-backup-timer.sh` | Root only, refuses to run from a release other than `/opt/la-lanh/current`, installs the units, enables both timers, runs one backup and one check. |
| Tests | `apps/api/tests/scripts/test_backup_timer.py` | Unit contents and the real freshness script against synthetic files (fresh, stale, empty, missing checksum, tampered newest dump, bad setting). No systemd in CI: whether timers fire on the VPS is operator evidence. |

## Operator steps (not done; evidence still missing)

1. After the release that contains these files is live and `/opt/la-lanh/current` points at it:
   `sudo /opt/la-lanh/current/infra/hetzner/install-backup-timer.sh`.
2. Record: `systemctl list-timers 'la-lanh-*'`, the first backup file name and size, `sha256sum -c`
   result, and the freshness check output. Do not paste database URLs or dump contents.
3. Choose and record how failures reach a person (journal forwarding, uptime monitor on the marker
   directory, or a mail relay). Until then the marker is local only.
4. Monthly and after each schema-changing release, run the restore probe below and record the
   output summary.
5. Check the Supabase plan's own backups/PITR and their retention in the dashboard; provider
   snapshots have a lifecycle the app's 14-day retention does not control.

## Restore probe

`infra/hetzner/rehearse-migration.sh` already restores the newest dump into a disposable,
TLS-enabled PostgreSQL on an internal Docker network, as a least-privileged backend role, runs the
release image's migrations, the privacy isolation check and readiness, then destroys the container.
Use it as the restore probe with the current release ID:

```sh
cd /opt/la-lanh/current
LA_LANH_RELEASE_ID=<current release> infra/hetzner/rehearse-migration.sh
```

Evidence to record: backup file name, checksum OK, `database-privacy-isolation-ok`, readiness OK,
container removed. It proves a backup can be restored; it does not prove deletion reconciliation.

## Deletion reconciliation after a restore: option A chosen (journal not built yet)

A restore brings back every row deleted after the backup was taken: guest erasure, history clears,
Radar deletions, withdrawn consents and the 24-hour Daily/Radar purges. Today there is **no
mechanism** to replay those deletions, so a restore can resurrect data that users or retention
removed. Options:

| Option | How | Trade-off |
|---|---|---|
| A. Deletion journal | On each erasure/clear, append a keyed HMAC of the deleted root ID (guest, Radar row, history root) with its time to a small table kept only as long as the oldest backup (14 days), never with content. After a restore, replay every journal entry newer than the backup before serving. | Retains pseudonymous deletion facts for up to 14 days; needs the HMAC key to survive; must itself be in the restored copy or kept outside it. |
| B. Forward-only recovery | Never restore into service; only restore into a disposable copy to read specific rows needed for a forward fix. | No resurrection, but a full data loss incident has no restore path. |
| C. Restore plus time-based purge | After a restore, run every retention cleanup immediately, and treat explicit user erasures after the backup as lost until users repeat them. | Simple, but user-requested erasures between backup and restore are silently undone, which is a rights problem. |

Recommendation: A, scoped to explicit user actions (guest erasure, history clear, Radar delete,
consent withdrawal) because time-based retention can be re-run (C) for everything else. Until the
owner decides and the journal exists, the runbook must treat B as the rule: no restore into service.

**Decision (22/10/2026):** the owner delegated this choice to the recommendation above: **A**, scoped to
explicit user actions, with C's immediate re-run of retention cleanups for everything else.

## Option A implementation (FIXED_LOCAL, not deployed)

| Piece | Where | Behaviour |
|---|---|---|
| Journal table | `erasure_journal` (migration `20261023_0038`), `domains/erasure_journal/` | `{kind, HMAC-SHA256(server hash key, "erasure-journal:<kind>" + root id), scope, occurred_at}`. No id or content. RLS on; no `anon`/`authenticated` access. |
| Recording | same transaction as the erasure | guest erasure (with the DELETING marker), history clear (through `clear_in_session`, which the HTTP service and `repository.clear` both use), birth supplement removal (`time`/`place`), switch to an unknown birth time, Radar delete, Radar withdraw, consent withdrawal (purpose as scope), resonance clear (`consent` when withdrawn), Vòng Lá matching consent withdrawal. |
| Not yet journaled | follow-up PR | Tarot session delete, share-link revoke, La Chung withdraw/delete/revoke/hide, saved-note unsave, experiment undo, pending Radar invite revoke. Until then a restore can bring these back; C covers only their time-based expiry. |
| Snapshot checkpoint | `backup-database.sh` dumps `public` with the journal rows | Each journal row commits with its erasure, and `pg_dump` reads one consistent snapshot, so the rows in a dump are exactly the erasures that snapshot reflects. No wall-clock cutoff is used. |
| Purge horizon | `erasure_journal_horizon` (one row: `purged_before`, a time only), written in each purge's own transaction | Retention removes old rows, but an export taken before the purge can still carry them. Every entry older than the horizon committed long before that purge, so a snapshot holding the horizon reflects it: replay counts such an entry as `reflected` and never applies it again, which keeps history created after an old clear. Entries newer than the horizon still go by row presence. |
| Host copy | `export-erasure-journal.sh`, `la-lanh-erasure-journal.{service,timer}` (hourly at :05, installed by `install-backup-timer.sh`) | `scripts.erasure_journal export` to `/opt/la-lanh/backups/erasure-journal/journal-<UTC>.jsonl` (0600), then `purge` of entries older than `LA_LANH_ERASURE_JOURNAL_RETENTION_DAYS` (default 15, minimum 15). Older export files are kept about two days. The six-hourly expired cleanup applies the same retention, so it holds before this timer is installed. |
| Replay | `scripts.erasure_journal replay FILE...` | For each exported entry: if the restored copy already holds it, or the entry is older than the copy's purge horizon, its erasure is in the snapshot and it is skipped (data created afterwards stays). Otherwise it matches the digest against ids in the restored copy, re-applies the erasure through the same repository code (built without a journal), and then records the entry. Idempotent: a second run finds every entry held. |

Losses the design accepts, so the runbook must not hide them:
- Erasures in the last hour before a total loss of both the database and its live journal are only in the
  database. An export from the live database before any restore closes this gap whenever it is readable.
- A provider point-in-time recovery rewinds the journal with the data (the checkpoint stays consistent), so the
  entries after that point must come from an export taken before the recovery or from the hourly copy.
- Rotating the server hash key makes older digests unmatchable. Replay any pending restore before rotating.
- Linked accounts: the Supabase Auth identity was already deleted at erasure time; replay finishes the local
  deletion through the guest cleanup job, which retries the identity call.

### Restore procedure (only after this PR is reviewed and deployed)

1. If the damaged database is still readable: `scripts.erasure_journal export > pre-restore.jsonl` (root-only).
2. Restore the chosen dump (`pg_restore --no-owner --role=<backend>`); its journal rows come with it.
3. `scripts.erasure_journal replay pre-restore.jsonl /opt/la-lanh/backups/erasure-journal/journal-*.jsonl`
   and record the per-kind counts (`reflected`/`applied`/`unmatched`, no ids).
4. Run the guest and expired cleanup jobs (option C) until they report nothing remaining.
5. Privacy isolation check and readiness, then serve.

### Disposable PostgreSQL restore probe (operator, before B can be lifted)

SQLite tests model the snapshot as a file copy. The real interleaving must be shown once on a disposable
PostgreSQL with synthetic data, not on staging or production:
1. Seed synthetic guests with history. Open an erasure (for example a history clear) whose transaction has
   taken `now` and holds the owner lock but has not committed.
2. Start `pg_dump` while that transaction is open, then commit it, then run one more erasure after the dump.
3. Export the journal, restore the dump into a fresh disposable database, run step 3 above and both cleanups.
4. Record: the in-flight erasure is `applied` (its row was not in the snapshot), an erasure committed before the
   dump is `reflected` with later data kept, the post-dump erasure is `applied`, and no erased row remains.

Until the journal is deployed, the hourly copy has run and this probe has passed, **B stays the operating
rule: no restore into service.**
