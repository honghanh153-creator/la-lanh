# US-23 delivery notes: birth-data correction (29/10/2026)

Branch `feat/birth-date-correction`, built on the plan branch `docs/birth-data-edit-plan` (`e372e29`, plan after
Codex r52) plus the Codex r54 corrections relayed by the coordinator (snapshot ordering, share-creation fence,
invite copy). The plan doc itself is maintained on its own branch and is not edited here. Not merged, not released;
the correction must not be enabled before migrations `20261029_0039` and `20261029_0040` are deployed.

## What shipped on the branch

| Slice | Content |
|---|---|
| 1 Docs | `docs/user-stories/US-23-sua-thong-tin-sinh.md`; SRS endpoints replacing the `/users/me/birth-data` sketch; data inventory, store data map, restore/erasure doc; US-06 points at US-23. |
| 2 Artifact lifecycle | Migration `20261029_0039` drops the saved/share foreign keys to `daily_notes` and `reading_revisions` (names read from the catalog; ids kept; `guest_id` cascades kept; downgrade refuses while detached rows exist). Explicit copy deletes where the cascade carried a contract: birth time/place removal, the time downgrade and its replay (every copy of the guest, detached included), manual history clear (live links on the unsaved notes and plans it removes). Share creation fenced under the owner lock with a live-source recheck (Codex r54 P2). |
| 3 Share-link management | `GET /v1/share-artifacts` (owner only, keyset cursor, 1–50, metadata columns only, `no-store`, `share-list` admission bucket) and "Link đã chia sẻ" in Đã lưu with revoke. |
| 4 Correction API | `PUT /v1/birth-profile/date` with compute / locked replace / drain phases, D4 refusal on POST, D5 counter (`birth_date_changes`), D6 before compute, journal kind `birth_date_replaced` with fail-closed replay, `profile_revision` on the reveal response. |
| 5 Web | Mình rows and confirm sheet, `/birth?edit=1` edit mode, `/birth` redirect, correction-specific cache withdrawal, reveal follow-up, privacy-notice detail. |

## Inventory of source-deleting paths (plan "explicit deletes")

| Path | Deletes sources | Copies now |
|---|---|---|
| Birth time/place removal, switch to unknown time, `replay_time_downgrade` (`_erase_precision`) | Daily notes, plans/revisions, non-date-only snapshots | **Deleted explicitly**, all of the guest's (unchanged contract, confirmation text). |
| Manual history clear (`clear_in_session`, `replay_clear`) | Unsaved past Daily notes, unprotected daily plans | **Deleted explicitly** where they reference the removed roots/revisions (live links on unsaved notes went by cascade before; saved roots/plans were and are excluded). |
| Automatic retention (`purge_expired`) | Expired unsaved roots without live children | Unchanged: revoked/expired links are deleted directly (detached ones too); live links keep their root. |
| Guest deletion / cleanup | Guest row | Unchanged: `guest_id` cascade removes every copy. |
| Birth-date correction (`replace_date`), its replay (`replay_date_replacement`) | All snapshots, plans, projections, Daily notes, experiments, Radar rows (both sides), Reading/Radar jobs | **Kept** (D2), deliberate change. |

No other path deletes `daily_notes`, `reading_revisions`, `reading_plans`, `chart_snapshots` or `birth_profiles`
(searched `app/` and `scripts/`).

## Privacy review (AGENTS.md gate 3)

| Data | Collected / stored | Retention and deletion |
|---|---|---|
| New birth date | Same field as US-02, AES-GCM envelope bound to the guest | Replaces the old value in one transaction; the old snapshot and all derived rows are deleted (D1). |
| Refused date (under 18 / over 120) | Not stored, not logged, not echoed in the error body | — (checked before any read, compute or write). |
| `confirm_birth_date` | Request body only; compared and discarded | Never stored. |
| `expected_revision` | Echo of the profile's update time | Never stored separately. |
| Time, place, deep consent version | Cleared on correction | Re-collected only with fresh deep consent (US-06). |
| Saved notes, share links | Unchanged ciphertext | Kept through a correction, still unsavable/revocable; removed by unsave/revoke, expiry cleanup, time/place removal and guest deletion. |
| Share list response | id, format, status, created/expiry/revocation times | No token (only its hash exists), no public path, no source note id, no content. |
| `birth_date_changes` | guest id + time, no value | Pruned after 24 h by the next correction and the six-hourly cleanup; guest deletion cascades; RLS on, browser roles revoked. |
| Journal `birth_date_replaced` | kind, keyed HMAC of the guest id, empty scope, time | 15-day journal retention like the other kinds. |
| Logs | `profile date edit rejected code=<CODE>` / `accepted` | No date, guest id or chart value (tested with `caplog`; repository privacy guard passes). |

Purpose limitation and minimization: the correction re-uses the existing `birth_profile_basic` purpose (not asked
again); everything derived from a wrong date is deleted. The in-app privacy notice (`ConsentPage`, "Sửa ngày sinh"),
the data inventory and the store data map describe the same runtime behavior. Store forms: no new data type, so the
Apple App Privacy and Play Data Safety answers are not expected to change; re-check at release.

Law check (primary/official sources, 29/10/2026): Law 91/2025/QH15 on personal data protection is in force since
01/01/2026 ([Hà Tĩnh provincial portal](https://hatinh.gov.vn/vi/bai-viet/luat-bao-ve-du-lieu-ca-nhan-chinh-thuc-co-hieu-luc-thi-hanh-tu-ngay-112026),
[SBV implementation notice](https://sbv.gov.vn/en/w/tri%E1%BB%83n-khai-thi-h%C3%A0nh-lu%E1%BA%ADt-b%E1%BA%A3o-v%E1%BB%87-d%E1%BB%AF-li%E1%BB%87u-c%C3%A1-nh%C3%A2n-1));
Article 4(1) lists the data subject's right to view and correct their own data. This feature supports that right;
how the duties apply stays in the owner/engineering P09 assessment and no compliance claim is made.

## Security review (AGENTS.md gate 2)

- **Authentication / ownership:** owner derived from the guest cookie only; the PUT needs trusted Origin + CSRF and
  basic consent; GET share list needs a valid session (401 otherwise) and only reads `guest_id = owner`.
- **Races:** revision fence checked in phase 1 and again under the guest row lock; two tabs → one 409
  `BIRTH_PROFILE_CHANGED`. Share creation and saved-note saving recheck the live source under the same lock, so a
  late create cannot attach to a deleted subject (both orders tested on SQLite; PostgreSQL gated).
- **Foreign keys:** `birth_profiles.current_snapshot_id` is detached and flushed before old snapshots are deleted, in
  the correction and in its replay (Codex r54 #1), then the prepared snapshot is activated.
- **Abuse:** `birth-compute` admission bucket on the PUT, D5 counter (3 / 24 h), `share-list` bucket (60 per peer,
  600 global per window) and a 50-row page cap on the list.
- **Input validation:** `extra="forbid"` bodies, ISO dates, cursor length ≤ 120 and strict decode (422
  `SHARE_CURSOR_INVALID`).
- **Error disclosure:** problem+json codes only; `no-store` on the PUT, its errors and the share list.
- **Failure / rollback:** phase 1 writes nothing; phase 2 is one transaction (a failed journal write rolls back the
  deletes, the counter and the switch — tested); phase 3 waits for captured provider sends, and a job leased before
  the correction cannot pass `execution_guard` or `succeed` afterwards (tested).
- **Restore:** a pre-correction dump replays fail-closed (no active subject, guest `birth_pending`, copies kept); a
  post-correction dump reports `reflected`. The journal carries no birth value.
- **Native:** same API; web caches withdrawn without keeping chart text. A device check is still owed (DoD).

## Tests

- API (SQLite, real app): full suite `2688 passed, 69 skipped, 1 xfailed` after slice 4; new files
  `tests/saved/test_detached_copies.py`, `tests/db/test_detached_copy_migration.py`,
  `tests/share/test_share_list.py`, `tests/share/test_share_create_fence.py`, `tests/birth/test_date_correction.py`,
  plus a late-publication test in `tests/content_rewrite/test_execution_fences.py`. Five existing tests that replaced
  the subject through `POST` now use the correction (behavior change D4).
- Web: `vitest` 551 tests pass; `src/app/router.test.tsx` fails to load in this worktree only because Vite denies
  font files outside the worktree root (node_modules are symlinked); it failed identically before any web change.
- Lint/types: ruff, ruff format, mypy, eslint, tsc clean; `contracts:check` equivalent (export_openapi `--check` and
  the generator `--check`) current; privacy, runtime-mock and mobile guards pass; fallback approval current; Radar
  experience audit and content review pass.

## Did not run

- **PostgreSQL:** `tests/saved/test_postgres_detached_copies_probe.py` and
  `tests/birth/test_postgres_date_correction_probe.py` (catalog after 0039, downgrade refusal, share-create race on two
  connections, FK ordering, fence race, send drain, pg_dump/pg_restore on both sides of a correction) are gated on
  `LA_LANH_JOURNAL_PROBE_POSTGRES_URL` and skipped; their seeds were exercised on SQLite. The migrations were not run
  against PostgreSQL.
- **E2E / device:** Playwright was not run (needs the QA stack); the existing e2e mocks keep `birth_pending`, so the new
  redirect should not affect them. No native device check. No accessibility audit of the sheet beyond role/label tests.

## Deviations from the plan

1. Error codes follow the API's uppercase convention: `BIRTH_DATE_CHANGE_REQUIRES_EDIT`, and the stale revision reuses
   the existing `409 BIRTH_PROFILE_CHANGED` (plan: `profile_revision_changed`). Added `BIRTH_DATE_UNCHANGED` (409),
   `BIRTH_DATE_CHANGE_LIMITED` (429), `BIRTH_DATE_CONFIRMATION_MISMATCH` (422).
2. The D5 counter is keyed by the guest id with an FK cascade (`birth_date_changes`) rather than an HMAC, so guest
   deletion removes it; it holds no value.
3. The Mình time/place summary shows precision and city, not "07:30": the general supplement state never contains the
   raw time by design.
4. The share-create fence landed as its own commit after slice 3 (the coordinator asked for it in the lifecycle slice);
   nothing on the branch ships independently.
5. A publish that finds its revision erased by a birth edit now answers `409 BIRTH_PROFILE_CHANGED` instead of an
   ownership error (a cross-owner revision still raises the ownership error).
6. The replay also resets the guest to `birth_pending` so every client path asks for the date again.

## Open owner decisions

- D1–D6 stay delegated choices; in particular the 3-per-24h limit and keeping saved/shared copies through a correction.
- Copy pass for the new strings (sheet, edit page, share list, privacy detail).
- Release order: deploy 0039 (+ share fence) and the share list first, then 0040 and the correction, as the plan says.

## AC / DoD still incomplete

- AC2, AC4, AC8, AC11 and the 0039 migration have PostgreSQL tests written but not run.
- AC13 is covered by unit tests of the queue and withdrawal, not by an e2e test with a reload.
- DoD: Codex APPROVE per SHA, e2e, native device check, experience/content audit of the new copy, store-form re-check at
  release, owner release order.
