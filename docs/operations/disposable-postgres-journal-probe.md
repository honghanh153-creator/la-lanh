# Disposable PostgreSQL journal probe (P07)

**Status, 27/10/2026: prepared, not executed.** Nobody has run this procedure yet. It needs a
disposable PostgreSQL cluster. Until an operator runs it and Codex reviews the receipt,
**B stays the operating rule: no restore into service.**

This file turns the outline in
[backup-restore-and-deletion-reconciliation.md](backup-restore-and-deletion-reconciliation.md#disposable-postgresql-restore-probe-operator-before-b-can-be-lifted)
into steps. The checks themselves are in
`apps/api/tests/erasure_journal/test_postgres_restore_probe.py`. They are skipped unless
`LA_LANH_JOURNAL_PROBE_POSTGRES_URL` is set, so CI never runs them.

## What it proves, and what it does not

| Check | Proves on PostgreSQL | Does not prove |
|---|---|---|
| `test_concurrent_unsave_returns_and_journals_the_row_once` | `DELETE … RETURNING` with two connections: the second `DELETE` waits on the row lock (seen in `pg_stat_activity`), then returns nothing. There is exactly one journal entry, for the row the first connection removed. | Other `DELETE` paths. `rowcount`-based paths (experiment undo, Tarot delete) are not exercised with two connections here. |
| `test_a_dump_taken_mid_erasure_restores_and_replays` | An unsave is still uncommitted while `pg_dump` takes its snapshot (`--format=custom --schema=public`, as in `backup-database.sh`). The test also does one unsave before the dump and one after, plus a La Chung revoke after it. After `pg_restore --no-owner` into a fresh database, the snapshot holds only the earlier erasure and its journal row. Replay then gives: before the dump `reflected`; in flight and after the dump `applied`; nothing `unmatched`. Siblings are kept, and a second replay is all `reflected`. | A Supabase-managed restore or PITR. Production data volume and timing. The guest-keyed history clear (the SQLite tests cover it). |
| `test_the_purge_horizon_travels_with_the_dump` | An export taken before `purge` replays as `reflected` on a dump taken after it, because the horizon row is in the dump. | The "later history is kept" case (covered by `tests/erasure_journal/test_purge_horizon.py` on SQLite). |
| Guard tests, 6 cases (these run in CI too) | The probe refuses any driver other than asyncpg, any host other than localhost, and any database name without the `lalanh_probe_` prefix or with characters outside `a-z0-9_`. The PostgreSQL tools get the password only through `PGPASSWORD`. | — |

The send-first/delete-first verification in the release runbook is a separate item and is not covered here.

## Safety rules

- **Synthetic rows only.** The probe makes its own guests, notes, saved notes, invites and share rows, with its own throwaway keys. Never restore a real dump into the probe cluster.
- **Local and disposable.** A cluster started for this run, on `127.0.0.1`, deleted afterwards. Never staging, production, Supabase or any shared server. The test enforces localhost and the `lalanh_probe_` name, and it truncates `guest_sessions`, `erasure_journal` and `erasure_journal_horizon` (with `CASCADE`) in the probe database.
- **No password on a command line, in chat, Git, screenshots or logs.**
  - Keep the probe URL in a root-only env file (`chmod 600`) and load it with `set -a`.
  - The test passes the password to `pg_dump`, `pg_restore`, `createdb` and `dropdb` only through `PGPASSWORD`.
  - On a failure the test reports only a tool's exit code and the first line of its error output.
- No provider, flag, server or database change outside the disposable cluster.

## Steps (operator)

Record the outcome of each step for the receipt.

1. **Tools.**
   - PostgreSQL server and client tools of the same major version as production. Record both versions.
   - The repository at the exact commit under test (record the full SHA), with `uv sync` done in `apps/api`.
2. **Start a disposable cluster** in a fresh temporary directory, listening only on `127.0.0.1` and a free port, for example 55440. Use `initdb` then `pg_ctl start` with `listen_addresses=127.0.0.1`. Create a role with `CREATEDB` and a database named `lalanh_probe_journal`. Set the role's password interactively (`\password` in `psql`), never as an argument.
3. **Private env file**, mode 600, outside the repository:
   - `LA_LANH_JOURNAL_PROBE_POSTGRES_URL=postgresql+asyncpg://<role>:<password>@127.0.0.1:55440/lalanh_probe_journal`
   - `LA_LANH_DATABASE_URL` set to the same value, for Alembic.
   - `LA_LANH_ENVIRONMENT=test`

   Load it with `set -a; . <file>; set +a`.
4. **Migrate** the probe database: `cd apps/api && uv run alembic upgrade head`. The test checks that `alembic_version` equals the repository head.
5. **Run:** `cd apps/api && uv run pytest -q -p no:randomly tests/erasure_journal/test_postgres_restore_probe.py`.
   - Expected: 9 passed (3 PostgreSQL checks, 6 guard cases).
   - A failure is evidence too: keep it and do not rerun to get a green result.
6. **Receipt** (data-free): date and time, commit SHA, server and client versions, the pytest summary line, and any failure's test name and assertion. No URL, password, row id or dump.
7. **Teardown:**
   - `pg_ctl stop`;
   - delete the cluster directory and any `*.dump` left in pytest's temporary directory;
   - delete the env file and `unset` the variables.

## What the receipt can close

- With Codex's review, the registry rows for "PostgreSQL `DELETE … RETURNING`" and the "interleaved PostgreSQL replay probe" can move from open to having synthetic evidence.
- **Lifting B** (allowing a restore into service) stays an owner decision after that review. It also needs the journaled kinds deployed, because replay only re-applies kinds the running code knows. An entry of an unknown kind fails closed, so a restore must run replay with code at least as new as the code that wrote the entries.
