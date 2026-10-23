# Legacy plaintext: aggregate check, backfill and purge plan (P06)

Status: prepared 22/10/2026 for audit P06. **Not run against any real database.** The operator runs each step
with protected credentials; the owner approves before anything that writes. Synthetic data only in this repo.

## Why

New writes encrypt chart results, Daily prose, saved and share snapshots and the La Chung recipient label with
AES-GCM bound to the row. The repositories still *read* older plaintext columns for compatibility, and tests
deliberately allow it. `check_database_privacy.py` proves grants and RLS, not that those columns are empty. So
nobody can currently say whether production still holds readable legacy rows. This plan answers that with counts,
then removes them without reading values out of the database.

## Step 1 — aggregate check (read-only)

```bash
LA_LANH_DATABASE_URL=... uv run --directory apps/api python -m scripts.check_legacy_plaintext
```

- Opens a read-only transaction, prints one JSON object of counts, nothing else (no ids, values or samples).
- Checks (`scripts/check_legacy_plaintext.py` `CHECKS`):

| Key | Legacy column read by |
|---|---|
| `chart_snapshots.result_payload` | `birth/postgres.py _result_payload` |
| `birth_profiles.place_plaintext` | `place_display_name`, `timezone_id` (new writes set NULL) |
| `daily_notes.unencrypted` / `.plaintext_beside_ciphertext` | `daily/postgres.py _content` |
| `saved_notes.unencrypted` / `.plaintext_beside_ciphertext` | `saved/postgres.py _snapshot_payload` |
| `share_artifacts.unencrypted` / `.plaintext_beside_ciphertext` | `share/postgres.py _snapshot_payload` |
| `la_chung_requests.recipient_label` | La Chung pre-encryption column |

- Record the counts and the release SHA in the release receipt. Counts are aggregate personal-data metadata:
  keep them in the private receipt, not a public issue.
- All zero: go to step 4.

## Step 2 — choose per table (owner decision)

| Table | Preferred | Why |
|---|---|---|
| `chart_snapshots` | **Purge and recompute** | Derivable from encrypted birth input; a recompute uses the current engine and is already the AC05 path. |
| `daily_notes` | **Purge** past the history window; backfill only today's or saved roots | Daily is visible ≤24 h; legacy rows past that have no product purpose. |
| `saved_notes` | **Backfill** | Saved notes follow the profile lifetime; the person chose to keep them. |
| `share_artifacts` | **Purge** inactive (P05 already does); backfill live ones | Live links are capabilities the person shared. |
| `birth_profiles` place columns | **Null** | Encrypted place already exists in `birth_place_ciphertext` for supplemented profiles. |
| `la_chung_requests.recipient_label` | **Backfill** live, purge expired | Same pattern. |

## Step 3 — key-aware backfill tool (to build after the owner chooses)

Not implemented yet, by design: it writes personal data and needs the owner's choice above. Requirements:

1. Runs inside the API image with the production envelope key provider; never exports rows or keys.
2. Per row, in owner-bound batches under the existing account lock: read through the *same* compatibility
   reader, encrypt with the *same* `_encrypt_*` helper and row context, write the ciphertext and blank or NULL the
   legacy columns in one transaction. A row that fails to decrypt or validate is left as is and counted.
3. `--dry-run` prints only the counts it would change. Real runs print only counts.
4. Before: a fresh verified backup (P07). After: rerun step 1; the counts must fall to the expected values.
5. Tests on synthetic SQLite and disposable PostgreSQL, including interrupted batches and idempotent re-runs.

## Step 4 — remove the compatibility readers

Once step 1 reports zero on production after the backfill, a separate PR removes the plaintext branches from the
four repositories and adds a migration that drops or constrains the legacy columns. Until then, the data map must
not claim every historic record is encrypted.

## What this does not prove

- Backups taken before the backfill still contain legacy rows until they expire (P07).
- Provider-side copies and logs follow their own lifecycles (P08).
- `mood_check_ins.mood`, Radar and Tarot context/voice/state columns are plaintext **by design** (closed
  operational values), not legacy; they are inventoried separately in the data map.
