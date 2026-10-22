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

## Deletion reconciliation after a restore: owner decision needed

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
