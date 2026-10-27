# Disposable PostgreSQL journal probe (P07)

**Status, 27/10/2026: prepared, not executed** (revised after Codex r44: target guard, seed, TLS). Nobody has run this procedure yet. It needs a
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
| Offline tests, 19 cases (these run in CI too, without PostgreSQL) | The guard refuses: any driver other than asyncpg; any host other than localhost; a database name without the `lalanh_probe_` prefix or with characters outside `a-z0-9_`; **any query key other than one absolute, existing `sslrootcert`** (`database`, `host`, `port`, `user`, `password`, `server_settings`, `ssl`, `sslmode`, repeated keys). The target that the application's own engine options would connect to must equal the checked one. The tools get the password only through `PGPASSWORD` and verify the server with `PGSSLMODE=verify-full` against the same CA. The seeds respect the schema's constraints on SQLite (one principal per guest). The held-commit helper writes first and commits only after the hold. | The PostgreSQL checks themselves. |

The send-first/delete-first verification in the release runbook is a separate item and is not covered here.

## Safety rules

- **Synthetic rows only.** The probe makes its own guests, notes, saved notes, invites and share rows, with its own throwaway keys. Never restore a real dump into the probe cluster.
- **Local and disposable.** A cluster started for this run, on `127.0.0.1`, with its own throwaway CA, deleted afterwards. Never staging, production, Supabase or any shared server. The test enforces localhost and the `lalanh_probe_` name, and it truncates `guest_sessions`, `erasure_journal` and `erasure_journal_horizon` (with `CASCADE`) in the probe database.
- **No password on a command line, in chat, Git, screenshots or logs.**
  - Keep the probe URL in a root-only env file (`chmod 600`) and load it with `set -a`.
  - The test passes the password to `pg_dump`, `pg_restore`, `createdb` and `dropdb` only through `PGPASSWORD`.
  - On a failure the test reports only a tool's exit code and the first line of its error output.
- No provider, flag, server or database change outside the disposable cluster.

## Steps (operator)

Record the outcome of each step for the receipt.

1. **Tools.**
   - PostgreSQL server and client tools of the same major version as production (client tools 14 or newer, so `verify-full` accepts an IP address in the certificate). Record both versions.
   - `openssl`, and the repository at the exact commit under test (record the full SHA), with `uv sync` done in `apps/api`.
2. **Disposable CA and server certificate**, in a fresh directory `$P` (mode 700) that holds everything for this run. The application verifies the server against a pinned CA with hostname checks, and PostgreSQL ships with `ssl` off ([PostgreSQL: SSL settings](https://www.postgresql.org/docs/current/runtime-config-connection.html#RUNTIME-CONFIG-CONNECTION-SSL)), so the cluster needs TLS before anything can connect. Below, `$P` means that directory's absolute path; write the path itself inside configuration files and the URL, which do not expand variables.
   - CA: `openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -days 2 -subj "/CN=lalanh probe CA" -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign" -keyout $P/ca.key -out $P/ca.crt`
   - Server key and request: `openssl req -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -subj "/CN=127.0.0.1" -keyout $P/server.key -out $P/server.csr`
   - Server certificate for the loopback names: write `subjectAltName=IP:127.0.0.1,DNS:localhost`, `basicConstraints=CA:FALSE`, `keyUsage=critical,digitalSignature` and `extendedKeyUsage=serverAuth` (one per line) to `$P/server.ext`, then `openssl x509 -req -in $P/server.csr -CA $P/ca.crt -CAkey $P/ca.key -CAcreateserial -days 2 -extfile $P/server.ext -out $P/server.crt`.
   - `chmod 600 $P/server.key $P/ca.key`. The CA key never leaves `$P` and is deleted at teardown.
3. **Start a disposable cluster** in `$P/data`:
   - `initdb -D $P/data -U lalanh_probe_admin --auth-local=trust --auth-host=reject`.
   - In `$P/data/postgresql.conf`: `listen_addresses = '127.0.0.1'`, `port = 55440` (or another free port), `unix_socket_directories = '$P'`, `ssl = on`, `ssl_cert_file = '$P/server.crt'`, `ssl_key_file = '$P/server.key'`, `ssl_min_protocol_version = 'TLSv1.2'`.
   - In `$P/data/pg_hba.conf`, add `hostssl all all 127.0.0.1/32 scram-sha-256` (TCP only over TLS; the socket stays for local setup).
   - `pg_ctl -D $P/data -l $P/server.log start`.
   - Over the socket (`psql -h $P -p 55440 -U lalanh_probe_admin postgres`): `CREATE ROLE lalanh_probe LOGIN CREATEDB;`, then `\password lalanh_probe` (typed interactively, never as an argument), then `CREATE DATABASE lalanh_probe_journal OWNER lalanh_probe;`.
4. **Private env file** `$P/probe.env`, mode 600:
   - `LA_LANH_JOURNAL_PROBE_POSTGRES_URL=postgresql+asyncpg://lalanh_probe:<password>@127.0.0.1:55440/lalanh_probe_journal?sslrootcert=<absolute $P>/ca.crt`. No other query key: the guard refuses `host`, `database`, `port`, `user` and the rest, because asyncpg would let them override the target.
   - `LA_LANH_DATABASE_URL` set to the same value, so Alembic verifies the server the same way.
   - `LA_LANH_ENVIRONMENT=test`

   Load it with `set -a; . $P/probe.env; set +a`.
5. **TLS check** before migrating: `PGSSLMODE=verify-full PGSSLROOTCERT=$P/ca.crt psql -h 127.0.0.1 -p 55440 -U lalanh_probe -d lalanh_probe_journal -c "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()"` (password typed at the prompt) must print `t`. The probe sets the same `PGSSLMODE`/`PGSSLROOTCERT` for `pg_dump`, `pg_restore`, `createdb` and `dropdb`.
6. **Migrate** the probe database: `cd apps/api && uv run alembic upgrade head`. The test checks that `alembic_version` equals the repository head.
7. **Run:** `cd apps/api && uv run pytest -q -p no:randomly tests/erasure_journal/test_postgres_restore_probe.py`.
   - Expected: 22 passed (3 PostgreSQL checks, 19 offline cases).
   - A failure is evidence too: keep it and do not rerun to get a green result.
8. **Receipt** (data-free): date and time, commit SHA, server and client versions, the TLS check result, the pytest summary line, and any failure's test name and assertion. No URL, password, certificate, key, row id or dump.
9. **Teardown:**
   - `pg_ctl -D $P/data stop`;
   - delete `$P` entirely (cluster, CA and server keys, certificates, env file, log) and any `*.dump` left in pytest's temporary directory;
   - `unset` the variables.

## What the receipt can close

- With Codex's review, the registry rows for "PostgreSQL `DELETE … RETURNING`" and the "interleaved PostgreSQL replay probe" can move from open to having synthetic evidence.
- **Lifting B** (allowing a restore into service) stays an owner decision after that review. It also needs the journaled kinds deployed, because replay only re-applies kinds the running code knows. An entry of an unknown kind fails closed, so a restore must run replay with code at least as new as the code that wrote the entries.
