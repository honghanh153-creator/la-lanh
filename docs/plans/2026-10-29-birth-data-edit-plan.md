# Edit birth data after it is saved: plan (29/10/2026)

**Status: plan only, no code.** Owner request, 29/10/2026: "lên kế hoạch để làm thêm phần đổi thông tin, cập
nhật thông tin ngày sinh sau khi đã có". Facts below are read from integration `e0d62fa`. Revised after Codex r52 and r54
([REQUEST_CHANGES @ `db50cd7`](https://github.com/honghanh153-creator/la-lanh/pull/113#issuecomment-6497712508)): an
artifact-lifecycle prerequisite, a fail-closed restore state, an explicit 18+ policy, the compute/commit/drain phases,
a cache withdrawal that keeps queued unsaves, share-link management, and the invite-link disclosure. Delivery follows
the usual exact-SHA review; nothing here authorizes a merge, release or provider change.

## Goal

From **Mình**, a person can correct a wrong birth date, or add, change or remove their birth time and place, without
starting over. They see what will change before they confirm, and afterwards nothing silently mixes the old and the new
birth data. This fits the north star: calm, no surprises, and "this app understands me" depends on correct inputs.

## What exists today

| Part | Today | Source |
|---|---|---|
| Time and place | Editable. Mình → "Sửa lớp dữ liệu sinh" opens `/birth-time`, which loads `GET /v1/birth-profile/supplement/edit` and re-asks for deep consent. "Xóa giờ sinh" and "Xóa nơi sinh" exist. | `ProfilePage.tsx:210-226`, `BirthSupplementPage.tsx`, US-06 S29 / AC14 |
| Removing time or place | Deletes daily notes, plans and the precise snapshots, which **also deletes saved notes and share links by foreign-key cascade**. The confirm text says so: "Xóa giờ sinh và mọi note, bản lưu, link chia sẻ hiện có?". It captures admitted provider sends inside the transaction and drains them after commit. | `birth/postgres.py:258-322`, `:340-402`; `ProfilePage.tsx:219-222` |
| Birth date | **No edit entry.** After a save the date fields are disabled only by a local React flag; the server does not enforce it. | `BirthDatePage.tsx:164`, `:185` |
| `POST /v1/birth-profile` with a different date | Accepted for an adult date. It detaches live reading pointers, clears time/place and the deep consent version, sets level 1 and activates a new date-only snapshot. Old snapshots are kept as "immutable history". | `domains/birth/postgres.py:35-143` |
| Age | The whole product is 18+. The service refuses a date under 18 (or over 120 years) before computing (`BirthDateOutOfRange`), and the page refuses it before submitting ("Lá Lành hiện dành cho người từ 18 tuổi."). | `birth/service.py:59-63`, `BirthDatePage.tsx:78-82`, US-02 |
| Saved notes and share links | Both point at their daily note and reading revision with `ON DELETE CASCADE`. History clear and retention skip a source that a saved copy or a live share still uses. There is no endpoint that lists a person's own share links; a link can be revoked only from the card page that just created it. | `saved/tables.py:15-28,37-39`, `share/tables.py:30-43,53-55`, `history/postgres.py:101-119`, `share_artifacts.py:138-207`, `CardPage.tsx` |
| Web cache after a precision edit | `clearChartDerivedData` clears the whole saved-note mutation queue, queued unsaves included. `dropQueuedSaves` keeps unsaves. | `clearChartDerivedData.ts:31-32`, `savedNoteMutationQueue.ts:189,254-256` |
| Requirement | No profile story owns a date edit. US-06 puts it out of scope ("DOB edit (profile story)"); US-02 covers a change only before the reveal. | US-06 `:205`, `:360`; US-02 `:245-247` |

## Gaps this plan closes

1. **No date edit in Mình**, and no story, AC or SRS endpoint for it. SRS sketches `POST /users/me/birth-data`, which
   does not exist.
2. **The date "lock" is only in the client.** Any retry or crafted request with another adult date replaces the
   subject.
3. **Replacing the date leaves old data behind**: earlier chart snapshots (including any full chart computed with the
   old time and place), Radar results built from the old chart, and queued Luna rewrite jobs.
4. **No erasure-journal kind** records a date change, so a restore from backup could bring the old subject back.
5. **Saved copies and share links cannot outlive their source today.** Keeping them through a correction (D2) needs a
   schema and lifecycle change first.
6. **A person cannot find or revoke their own older share links** after leaving the card page.

## Decisions (Claude, under the owner's 29/10 delegation; the owner can override any of them)

| # | Decision | Why |
|---|---|---|
| D1 | A date change is a **replacement**, not history. Old snapshots, plans, revisions, projections, daily notes, experiments, Radar results with this person as a participant, pending Radar invites from them, and rewrite jobs are deleted. Today's daily note is rebuilt. | A wrong date has no remaining purpose; this matches data minimization and what removing time/place already does. |
| D2 | **Saved notes and existing share links are kept** as frozen copies. They stay manageable: Đã lưu lists saved notes (unsave) and, newly, the person's share links (revoke). The confirm sheet says so. | They are copies the person chose to keep; US-06 `:261` says not to rewrite shared history. Removing time or place keeps its current, disclosed behavior of deleting them. |
| D3 | Time and place are **cleared** when the date changes (as today), and deep consent must be given again to add them back. | They belong to the old date; asking again keeps consent explicit and current. |
| D4 | `POST /v1/birth-profile` **refuses** a different date while an active birth subject exists (`409 birth_date_change_requires_edit`). A new explicit endpoint does the change. | Closes gap 2: a retry can never replace the subject by accident. |
| D5 | The date can be changed at most **3 times in 24 hours** per person, with a calm message after that. | It stops "chart shopping" and the age-gaming risk named in US-02 `:247`, and the limit is easy to change. |
| D6 | **The 18+ rule applies to a correction exactly as at onboarding.** A new date under 18 (or over 120 years) is refused by the client before submitting and by the service before computing, with the onboarding message. Nothing changes: the old date, chart, Matching state and data stay. The refusal also points to the existing "Xóa Lá và dữ liệu" path, so a person who is in fact under 18 can remove everything. The server does not flag, retain or infer anything from the refused value. A valid adult correction recomputes Matching's live age, so other people's age filters apply to the new age. | US-02 makes the whole product 18+, and the correction must not relax that gate. Refusing without deleting avoids wiping someone's data on a typo; offering deletion keeps the person in control. How data-subject duties apply stays in the owner/engineering P09 assessment. |

## Scope

**In scope:**
- a "Ngày sinh" row in Mình showing the saved date, with a **Sửa** action;
- a confirm sheet, an edit page that reuses `BirthDatePage` in edit mode, and the server phases, journal kind, rate
  limit and age rule;
- the saved/share lifecycle change and share-link management that D2 depends on;
- a summary of the current time and place on the existing "Sửa lớp dữ liệu sinh" entry.

**Out of scope:**
- a second profile (US-01 `:344` forbids it);
- editing someone else's data in Radar or Hợp gu;
- changing the content of saved or shared copies;
- changing what removing time or place deletes.

## User flow (copy is a draft for the copy pass)

1. **Mình → "Chiếc Lá của bạn"** shows "Ngày sinh: 12/03/2001 · Sửa", with "Giờ và nơi sinh: 07:30, Huế · Sửa" below
   (or "Chưa thêm · Thêm").
2. **Sửa ngày sinh** opens a sheet:
   - "Đổi ngày sinh sẽ tạo lại Lá của bạn."
   - What changes:
     - Lá khai sinh, note hôm nay and gợi ý are recomputed;
     - giờ và nơi sinh are cleared, and you can add them again;
     - kết quả Hợp gu built from the old date are deleted;
     - **lời mời Hợp gu bạn đã gửi mà chưa được chấp nhận sẽ ngừng hoạt động** (kể cả lời mời đã được mở nhưng
       chưa chấp nhận).
   - What stays: ghi chú đã lưu and đường link đã chia sẻ. You can unsave a note or revoke a link in Đã lưu.
   - Actions: "Đổi ngày sinh" / "Giữ như cũ".
3. **The edit page** is `BirthDatePage` in edit mode: the current date is prefilled, and a save asks for the date once
   more as a typo check. The 18+ check runs before submitting (D6).
4. **After success:** a short reveal of the new Lá, then an offer to add time and place again ("Thêm giờ và nơi sinh để
   Lá rõ hơn"). The web withdraws the old chart from its caches (see "Web cache").
5. **Errors:**
   - same date: "Ngày này đã được lưu", and nothing changes;
   - under 18 or over 120 years: "Lá Lành hiện dành cho người từ 18 tuổi.", nothing changes, plus a link to "Xóa Lá
     và dữ liệu";
   - limit reached: "Bạn đã đổi ngày sinh vài lần hôm nay. Thử lại sau nhé.";
   - compute failure: the old chart stays (US-02 `:246`).
6. **Routing:** `/birth` redirects a person who has an active birth subject to Mình.
7. **Đã lưu** gains a "Link đã chia sẻ" section: each live link shows when it was made and when it expires, with "Thu
   hồi link". Unsave is never labelled as revoking a link.

## API and data

### Prerequisite: saved and shared copies outlive their source

- **Schema.** Remove the `ON DELETE CASCADE` foreign keys from `saved_notes` and `share_artifacts` to `daily_notes` and
  `reading_revisions`.
  - Keep `daily_note_id`, `revision_id` and `profile_id` as plain identifier columns, so the existing unsave key
    (`daily_note_id`, `revision_id`), queued unsaves and the share revoke by id keep working after the source is gone.
  - Keep, unchanged: `guest_id` with its cascade (guest deletion still removes every copy), the ciphertext columns,
    `expires_at`, `revoked_at`, the unique `(guest_id, daily_note_id)` index and the token hash.
  - Adjust the bundle checks only as far as a detached row needs.
- **Explicit deletes.** List every path that deletes `daily_notes`, `reading_revisions`, `reading_plans` or
  `chart_snapshots` and today removes copies by cascade. Each one either deletes the copies explicitly, keeping its
  current behavior, or is named as a deliberate change.
  - Removing time or place keeps deleting saved notes and share links, as its confirm text promises.
  - History clear and retention already skip sources that a copy uses. That exclusion stays unless a test shows it can
    be simplified safely.
- **Share-creation fence.** Today `ShareArtifactService.create` reads the owned source (`share/service.py:43`)
  and `PostgresShareArtifactRepository.create` inserts in another transaction (`share/postgres.py:28-46`). The
  source FKs are what reject a late insert after removal deleted the source. Once those FKs are dropped:
  - the insert transaction takes the same guest row lock as correction and time/place removal;
  - inside that lock it rechecks that the live daily note (and the revision, when one is referenced) still exists
    and is owned by the caller, and refuses otherwise;
  - **creation first, then date correction:** the copy committed first is a frozen copy like any other and is
    **kept** (D2), still unsavable and revocable;
  - **creation first, then time/place removal:** the removal **explicitly deletes** the new copy with the guest's
    other copies, as its confirm text promises (not by cascade: the source FKs are gone);
  - **removal or correction first:** the late creation rechecks its source under the lock, finds it missing and is
    refused, so no copy of deleted chart text is published;
  - saving a note gets the same fence.
- **Reads.** Saving still requires a live source. Listing saved notes, unsave, the public share read, revoke, purge
  and erasure-journal replay of unsave and share revoke must work for a detached row. The public share read already
  serves only the stored safe snapshot.
- **Migration.** One Alembic migration replaces the constraints. Existing rows keep their identifiers.
  - The downgrade refuses to run while any detached row exists, because the old cascade cannot hold them. There is no
    automatic downgrade in production.
  - The correction endpoint is not enabled until this migration is deployed.
- **Compatibility release (Codex r56 P1).** `deploy.sh` migrates before it replaces the app, so the app still running
  during the cascade drop must already delete copies itself. The explicit deletes and the share-create fence ship
  first, with the cascades kept and a no-op marker migration. The cascade drop ships in the next release, revises
  that marker and refuses to run in the same upgrade that applies it on a database with people. Once it has run,
  roll back only to an image of the compatibility release or later.
- **Tests:** SQLite and PostgreSQL.
  - A copy survives deletion of its source.
  - A share creation paused between its source read and its insert, with the source deleted meanwhile, is refused
    (SQLite control now; a PostgreSQL race test before this slice ships on its own).
  - Removing time or place still deletes copies.
  - Unsave, revoke, public read, purge and replay work on a detached row.
  - The migration upgrades rows, and the downgrade refuses while detached rows exist.

### Share-link management

- `GET /v1/share-artifacts`, for the session owner only.
  - Returns, per link: id, format, `created_at`, `expires_at` and `revoked_at`.
  - Never returns a token, which cannot be shown again because only its hash is stored. Never returns the snapshot
    content.
  - `no-store`, rate-limited, bounded page size.
- The existing `DELETE /v1/share-artifacts/{id}` revokes. Revoking a detached link works, and the public read then
  answers as for any revoked link.
- **Tests:** a link made before a date correction can still be listed and revoked after the correction and a reload;
  another person's link is never listed; unsave does not revoke a link.

### `PUT /v1/birth-profile/date`

- Body: `{birth_date, confirm_birth_date, expected_revision}`.
  - Requires a trusted origin and CSRF. Returns `no-store`.
  - `expected_revision` is the profile `updated_at` revision fence, so two tabs cannot race; a stale value returns
    `409 profile_revision_changed`.
  - It uses the `birth-compute` admission bucket plus the D5 per-person limit, kept as a keyed counter (no raw date).
- **Phase 1, no write lock.**
  1. Validate: same date, age (D6), range.
  2. Read the fence.
  3. Compute and encrypt the new date-only snapshot.

  Nothing is written. A failure here leaves everything as it was.
- **Phase 2, one transaction** under the guest row lock that `save_or_replay` and `clear_supplement` already take:
  1. Recheck `expected_revision` and the D5 limit.
  2. Capture the admitted provider sends for this guest (`pending_sends`), as `clear_supplement` does.
  3. Insert the prepared new snapshot (not yet active).
  4. **Detach the active pointer and flush:** point `current_snapshot_id` at the new snapshot and flush before any
     old snapshot is deleted. `BirthProfileRow.current_snapshot_id` is an immediate FK with no `ON DELETE`
     (`birth/tables.py:19-26`); `_erase_precision` uses the same order (flush at `birth/postgres.py:373-374`,
     delete at `:396`).
  5. Delete the D1 dependents explicitly: Radar requests of both perspectives first, then rewrite jobs, experiments,
     daily notes, plans and the old snapshots. Saved copies and share links stay, per the prerequisite.
  6. Clear time, place and deep consent.
  7. Write the journal entry.
  8. Commit. Any failure rolls back the whole transaction: the old subject stays active and nothing is deleted.
- **Phase 3, after commit and before the response:** `drain_sends` waits for every captured send to finish. This
  matters because `content_rewrite/worker.py:143-157` releases its guard before provider I/O. Publication is fenced
  by the job lease and deletion epoch (`worker.py:213`); a test proves that a late result for a deleted job is
  discarded. Success is returned only after the drain.
- **Tests:**
  - a send admitted before the correction finishes before success and never publishes old-subject text;
  - a late publication after commit is discarded;
  - a failure in phase 1 or 2 changes nothing;
  - an active subject is corrected without an FK error (detach and flush come first);
  - two tabs race on the fence.

### Erasure journal and restore

- A new kind, `birth_date_replaced`. The root is the guest's keyed id, and the entry is data-free: no date, and no
  value is added to the journal.
- **Replay follows the journal's checkpoint rule.** A dump's own journal rows mark what it already holds.
  - **The dump was taken after the correction:** the entry is in the dump, replay reports it as reflected and leaves
    the new subject untouched.
  - **The dump was taken before the correction:** the dump holds only the old subject, and no replacement value exists
    to restore. Replay fails closed:
    - in one owner-locked transaction, it first sets `current_snapshot_id` to null and flushes, then deletes the old
      subject's snapshots, plans, revisions, projections, daily notes, Radar rows and rewrite jobs;
    - it clears the profile's date-bearing state, time, place and deep consent, leaving **no active birth subject**;
    - saved copies and share links follow the prerequisite and stay;
    - on the next visit, the app asks the person to enter their birth date again, and `POST` accepts it because no
      active subject exists (D4);
    - while no subject exists, Matching readiness is false.
- Add the kind to the recording list in `backup-restore-and-deletion-reconciliation.md`. It needs PostgreSQL replay
  tests for both dump sides, like the other kinds.

### Logs and analytics

No date, time, place or chart value is logged, including a refused date. Only the event name and result code are logged,
and existing redaction is kept.

## Web cache

`clearChartDerivedData` is not used unchanged, because it drops queued unsaves (`clearChartDerivedData.ts:31-32`). A
correction-specific withdrawal instead:
- bumps the chart revision fence, so stale callbacks cannot recreate old chart data;
- cancels and resets the chart-derived queries;
- clears the active daily reading and the cached daily note;
- drops queued **saves**, which point at the old daily note (`dropQueuedSaves`);
- **keeps queued unsaves** and replays them against the retained copies' identifiers;
- refetches the saved list and share links instead of discarding retained copies.

Tests cover an offline unsave followed by a correction and a reload: the unsave reaches the server, and the copy is
gone.

## Privacy review (AGENTS.md gate 3)

| Data | Change |
|---|---|
| Birth date | Replaced. The old value and everything derived from it are deleted (D1), except copies the person saved or shared (D2), which stay frozen and manageable. A refused under-18 date is neither stored nor logged (D6). |
| Time and place | Cleared on a date change; added back only with fresh deep consent. |
| Saved notes and share links | Kept through a correction, still deletable (unsave) and revocable (new share list). They are removed by guest deletion, expiry and purge as today, and by removing time or place as disclosed today. |
| Radar results and invites | Deleted for both participants when built from the old chart, as removing precision already does. The other person sees the result as gone, with no reason given. Pending invite links stop working, and the confirm sheet says so. |
| Journal | One data-free entry, kept 15 days like the other kinds. A restore from before the correction leaves no active subject and asks for re-entry. |
| Rate counter | Keyed id and timestamps only, kept 24 hours. |
| Consent | The basic consent purpose is unchanged, so it is not asked again. Deep consent is asked again for time and place. |

The same data types are collected as before, so the store forms are not expected to change. The in-app privacy notice
and the data map gain lines saying:
- a date correction deletes the old derived data;
- saved copies and links stay until the person removes them;
- the share list shows link dates only.

A recorded check confirms this during delivery. This supports correcting one's own data; how the duties apply stays
part of the owner/engineering P09 assessment and is not claimed here.

## Security review (AGENTS.md gate 2)

- **Request protection:** CSRF and a trusted origin on the new endpoint, and the revision fence against races. The
  old `POST` refuses a date change (D4).
- **Abuse:** the per-person limit (D5) plus the existing per-peer and global buckets. The share list is rate-limited
  and paged.
- **No exposure:**
  - no date in a URL, log or error, and `no-store` responses;
  - the share list returns no token and no content, and only the owner's links.
- **Deletion path:**
  - explicit deletes in phase 2, with admitted sends captured inside the lock and drained after commit;
  - failure and rollback are tested;
  - the journal fails closed on restore.
- **Schema change:** removing cascades must not orphan copies past guest deletion. The guest cascade stays, and a test
  proves it.
- **Native app:** the same API. Native storage keeps no date (the web caches are withdrawn); a device check is listed
  under DoD.

## Delivery slices (each is its own PR with exact-SHA review)

1. **Docs.**
   - A new story **US-23 "Sửa thông tin sinh"** with AC, validation rules, edge cases and DoD.
   - The SRS endpoints (`PUT /v1/birth-profile/date`, `GET /v1/share-artifacts`), replacing the
     `/users/me/birth-data` sketch.
   - Data map, erasure doc and privacy notice lines.
   - US-06 `:205/:360` pointed at US-23.
2. **Artifact lifecycle**, in two releases. First the explicit deletes, the share-create fence and the marker, with
   the cascades kept (compatibility release). Then the schema change and migration, deployed only after every app
   process runs the compatibility release. SQLite and PostgreSQL tests for both. No product behavior changes yet.
3. **Share-link management.** The `GET` list, the Đã lưu section and its tests.
4. **Date correction API.**
   - `PUT /date` with the three phases, journal kind and replay, D4 refusal, D5 limit and D6 rule.
   - SQLite and PostgreSQL tests: races, retries, rollback, admitted sends, both dump sides, and age refusal.
   - It ships only after slices 2 and 3 are deployed.
5. **Web.**
   - The Mình rows, confirm sheet, edit mode, `/birth` redirect and correction cache withdrawal.
   - Unit tests, an e2e test of the edit flow including the offline unsave, and an accessibility check of the sheet.
6. **Copy and sync.** The copy pass for the new strings (including the invite-link line), the experience/content
   audits, and the registry.

## Acceptance criteria (draft for US-23)

- **AC1:** Given a saved profile, Mình shows the saved date with Sửa. Given no time or place, it shows "Chưa thêm".
- **AC2:** Given a confirmed new date:
  - the new chart is active;
  - earlier snapshots, plans, revisions, projections, daily notes, Radar results and pending invites built from them,
    and rewrite jobs are gone;
  - time, place and deep consent are cleared;
  - saved notes and share links remain, and can still be unsaved or revoked.
- **AC3:** Given the same date, nothing changes and the person is told so.
- **AC4:** Given a stale revision from another tab, the server returns `409`, nothing changes, and the page reloads the
  current date.
- **AC5:** Given a fourth change within 24 hours, the server refuses and the old chart stays.
- **AC6:** Given a compute failure, the old chart and its data stay unchanged.
- **AC7:** Given an active birth subject, `POST /v1/birth-profile` with another date returns
  `409 birth_date_change_requires_edit`.
- **AC8:** Restore and replay.
  - Given a dump taken before the correction, restored after it, replay deletes the old subject and its dependents
    and leaves no active birth subject. The app asks for the birth date again. No birth value is in the journal.
  - Given a dump taken after the correction, replay leaves the new subject as it is.
- **AC9:** Given a new date under 18 (or over 120 years):
  - the page refuses before submitting and the service refuses before computing, with the onboarding message;
  - nothing changes: date, chart, Matching state and data;
  - the page offers "Xóa Lá và dữ liệu";
  - the refused date is not stored or logged.
- **AC10:** No date, time or place appears in logs, URLs or error bodies.
- **AC11:** Given a send admitted before the correction, success is returned only after it ends, and no old-subject
  text is published afterwards.
- **AC12:** Given a share link made before the correction, after the correction and a reload it is listed in Đã lưu and
  can be revoked; the public link then answers as revoked.
- **AC13:** Given an unsave queued offline before the correction, after the correction and a reload the unsave reaches
  the server.
- **AC14:** Given a pending Radar invite, including one opened but not accepted, the confirm sheet says it will stop
  working before the person confirms.
- **AC15:** Given a share or save that read its source before a correction or time/place removal committed, the late
  insert is refused, and no copy of the deleted chart text becomes readable. Given a share or save that committed
  first, a later date correction keeps it as a frozen copy (D2), and a later time/place removal deletes it (Codex r55).

## DoD

- All AC are covered by tests, with PostgreSQL for AC2, AC4, AC8, AC11, AC15 and the lifecycle migration.
- Codex APPROVE at each exact SHA.
- Docs, privacy copy and the data map match runtime behavior.
- Experience and content audits pass.
- There is a device check on the native build.
- A release still needs the owner's order.
