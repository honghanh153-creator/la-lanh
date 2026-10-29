# Edit birth data after it is saved: plan (29/10/2026)

**Status: plan only, no code.** Owner request, 29/10/2026: "lên kế hoạch để làm thêm phần đổi thông tin, cập
nhật thông tin ngày sinh sau khi đã có". Facts below are read from integration `e0d62fa`. Delivery follows the usual
exact-SHA review; nothing here authorizes a merge, release or provider change.

## Goal

From **Mình**, a person can correct a wrong birth date, or add, change or remove their birth time and place, without
starting over. They see what will change before they confirm, and afterwards nothing silently mixes the old and the new
birth data. This fits the north star: calm, no surprises, and "this app understands me" depends on correct inputs.

## What exists today

| Part | Today | Source |
|---|---|---|
| Time and place | Editable. Mình → "Sửa lớp dữ liệu sinh" opens `/birth-time`, which loads `GET /v1/birth-profile/supplement/edit` and re-asks for deep consent. "Xóa giờ sinh" and "Xóa nơi sinh" exist. | `ProfilePage.tsx:210-226`, `BirthSupplementPage.tsx`, US-06 S29 / AC14 |
| Birth date | **No edit entry.** After a save the date fields are disabled only by a local React flag; the server does not enforce it. | `BirthDatePage.tsx:164`, `:185` |
| `POST /v1/birth-profile` with a different date | Accepted. It detaches live reading pointers, clears time/place and the deep consent version, sets level 1 and activates a new date-only snapshot. Old snapshots are kept as "immutable history". | `domains/birth/postgres.py:35-143` |
| Requirement | No profile story owns a date edit. US-06 puts it out of scope ("DOB edit (profile story)"); US-02 covers a change only before the reveal. | US-06 `:205`, `:360`; US-02 `:245-247` |

## Gaps this plan closes

1. **No date edit in Mình**, and no story, AC or SRS endpoint for it. SRS sketches `POST /users/me/birth-data`, which
   does not exist.
2. **The date "lock" is only in the client.** Any retry or crafted request with another date replaces the subject.
3. **Replacing the date leaves old data behind**:
   - earlier chart snapshots, including any full chart computed with the old time and place;
   - Radar results built from the old chart;
   - queued Luna rewrite jobs.
   Removing time or place already deletes these (`_erase_precision`, `postgres.py:340-402`); a date change should do no
   less.
4. **No erasure-journal kind** records a date change, so a restore from backup could bring the old subject back.
5. **Matching age** is computed live from the date (`matching/service.py:43-62`), and nothing re-checks the 18+
   condition after a change.

## Decisions (Claude, under the owner's 29/10 delegation; the owner can override any of them)

| # | Decision | Why |
|---|---|---|
| D1 | A date change is a **replacement**, not history. Old snapshots, plans, revisions, projections, Radar results with this person as a participant, pending Radar invites from them, and rewrite jobs are deleted in the same transaction. Today's daily note is rebuilt. | A wrong date has no remaining purpose; this matches data minimization and what removing time/place already does. |
| D2 | **Saved notes and existing share links are kept**. The confirm sheet says so and points to Đã lưu, where each can be deleted. | They are copies the person chose to keep; US-06 `:261` says not to rewrite shared history. |
| D3 | Time and place are **cleared** when the date changes (as today), and deep consent must be given again to add them back. | They belong to the old date; asking again keeps consent explicit and current. |
| D4 | `POST /v1/birth-profile` **refuses** a different date once a profile exists (`409 birth_date_change_requires_edit`). A new explicit endpoint does the change. | Closes gap 2: a retry can never replace the subject by accident. |
| D5 | The date can be changed at most **3 times in 24 hours** per person, with a calm message after that. | It stops "chart shopping" and the age-gaming risk named in US-02 `:247`, and the limit is easy to change. |
| D6 | After a change the **same age rules as onboarding** apply. If matching is on and the new date makes the person under 18, matching consent is withdrawn and the profile is hidden, using the existing withdrawal path. | Matching requires 18+ (`routes/matching.py:37`). |

## Scope

**In scope:**
- a "Ngày sinh" row in Mình showing the saved date, with a **Sửa** action;
- a confirm sheet, an edit page that reuses `BirthDatePage` in edit mode, and the server cascade, journal kind, rate
  limit and age re-check;
- a summary of the current time and place on the existing "Sửa lớp dữ liệu sinh" entry.

**Out of scope:**
- a second profile (US-01 `:344` forbids it);
- editing someone else's data in Radar or Hợp gu;
- changing saved or shared copies.

## User flow (copy is a draft for the copy pass)

1. **Mình → "Chiếc Lá của bạn"** shows "Ngày sinh: 12/03/2001 · Sửa", with "Giờ và nơi sinh: 07:30, Huế · Sửa" below
   (or "Chưa thêm · Thêm").
2. **Sửa ngày sinh** opens a sheet:
   - "Đổi ngày sinh sẽ tạo lại Lá của bạn."
   - What changes: Lá khai sinh, note hôm nay and gợi ý are recomputed; giờ và nơi sinh are cleared and you can add
     them again; kết quả Hợp gu built from the old date are deleted.
   - What stays: ghi chú đã lưu and đường link đã chia sẻ (you can delete them in Đã lưu).
   - Actions: "Đổi ngày sinh" / "Giữ như cũ".
3. **The edit page** is `BirthDatePage` in edit mode: the current date is prefilled, and a save asks for the date once
   more as a typo check.
4. **After success:** a short reveal of the new Lá, then an offer to add time and place again ("Thêm giờ và nơi sinh để
   Lá rõ hơn"). The web clears derived caches (`clearChartDerivedData`).
5. **Errors:**
   - same date: "Ngày này đã được lưu", and nothing changes;
   - limit reached: "Bạn đã đổi ngày sinh vài lần hôm nay. Thử lại sau nhé.";
   - compute failure: the old chart stays (US-02 `:246`).
6. **Routing:** `/birth` redirects a person who already has a profile to Mình.

## API and data

- **`PUT /v1/birth-profile/date`.** Body: `{birth_date, confirm_birth_date, expected_revision}`.
  - Requires a trusted origin and CSRF. Returns `no-store`.
  - `expected_revision` is the profile `updated_at` revision fence, so two tabs cannot race; a stale value returns
    `409 profile_revision_changed`.
  - It uses the `birth-compute` admission bucket plus the D5 per-person limit, kept as a keyed counter (no raw date).
- **One transaction**, under the guest row lock that `save_or_replay` already takes:
  1. verify the fence;
  2. compute the new date-only snapshot (outside the lock, as now) and check again;
  3. delete the D1 dependents and clear time/place/deep consent;
  4. activate the new snapshot;
  5. write the journal entry;
  6. run the D6 age re-check.
- **Erasure journal:** a new kind `birth_date_replaced`.
  - The root is the guest's keyed id, and the entry is data-free (no date).
  - On replay after a restore, it deletes snapshots and dependents created before the entry and clears time/place, so
    the old subject cannot return.
  - Add it to the recording list in `backup-restore-and-deletion-reconciliation.md`. It needs a PostgreSQL replay test
    like the other kinds.
- **No migration is expected** (kinds are strings; the counter can live in the existing admission or keyed-metadata
  store). If one is needed, it is additive and reversible.
- **Logs and analytics:** no date, time, place or chart value is logged. Only the event name and result code are
  logged, and existing redaction is kept.

## Privacy review (AGENTS.md gate 3)

| Data | Change |
|---|---|
| Birth date | Replaced. The old value and everything derived from it are deleted (D1), except copies the person saved or shared (D2). |
| Time and place | Cleared on a date change; added back only with fresh deep consent. |
| Radar results | Deleted for both participants when built from the old chart, as removing precision already does. The other person sees the result as gone, with no reason given. |
| Journal | One data-free entry, kept 15 days like the other kinds. |
| Rate counter | Keyed id and timestamps only, kept 24 hours. |
| Consent | The basic consent purpose is unchanged, so it is not asked again. Deep consent is asked again for time and place. |

The same data types are collected as before, so the store forms are not expected to change. The in-app privacy notice
and the data map gain one line saying a date correction deletes the old derived data. A recorded check confirms this
during delivery. This supports correcting one's own data; how the duties apply stays part of the owner/engineering
P09 assessment and is not claimed here.

## Security review (AGENTS.md gate 2)

- **Request protection:** CSRF and a trusted origin on the new endpoint, and the revision fence against races. The
  old `POST` refuses a date change (D4).
- **Abuse:** the per-person limit (D5) plus the existing per-peer and global buckets.
- **No exposure:** no date in a URL, log or error, and `no-store` responses.
- **Deletion path:** the same cascade helpers as `_erase_precision`, with failure and rollback tested; the journal
  covers restore.
- **Native app:** the same API. Native storage keeps no date (the web caches are cleared); a device check is listed
  under DoD.

## Delivery slices (each is its own PR with exact-SHA review)

1. **Docs.**
   - A new story **US-23 "Sửa thông tin sinh"** with AC, validation rules, edge cases and DoD.
   - The SRS endpoint, replacing the `/users/me/birth-data` sketch.
   - Data map, erasure doc and privacy notice lines.
   - US-06 `:205/:360` pointed at US-23.
2. **API.**
   - `PUT /date` with the cascade, journal kind, D4 refusal, D5 limit and D6 re-check.
   - SQLite and PostgreSQL tests, including races, retries, failure rollback, journal replay and the age crossing.
3. **Web.**
   - The Mình rows, confirm sheet, edit mode, `/birth` redirect and cache clearing.
   - Unit tests, an e2e test of the edit flow, and an accessibility check of the sheet.
4. **Copy and sync.** The copy pass for the new strings, the experience/content audits, and the registry.

## Acceptance criteria (draft for US-23)

- **AC1:** Given a saved profile, Mình shows the saved date with Sửa. Given no time or place, it shows "Chưa thêm".
- **AC2:** Given a confirmed new date, the new chart is active. Earlier snapshots, plans, revisions, projections, Radar
  results built from them and rewrite jobs are gone. Time, place and deep consent are cleared. Saved notes and share
  links remain.
- **AC3:** Given the same date, nothing changes and the person is told so.
- **AC4:** Given a stale revision from another tab, the server returns `409`, nothing changes, and the page reloads the
  current date.
- **AC5:** Given a fourth change within 24 hours, the server refuses and the old chart stays.
- **AC6:** Given a compute failure, the old chart and its data stay unchanged.
- **AC7:** Given a profile, `POST /v1/birth-profile` with another date returns `409 birth_date_change_requires_edit`.
- **AC8:** Given a backup taken before the change and restored after it, journal replay leaves only the new subject.
- **AC9:** Given matching on and a new date under 18, matching is withdrawn and the profile is hidden.
- **AC10:** No date, time or place appears in logs, URLs or error bodies.

## DoD

All AC are covered by tests (PostgreSQL for AC2, AC4 and AC8). Codex APPROVE at each exact SHA. Docs, privacy copy and
the data map match runtime behavior. Experience and content audits pass. There is a device check on the native build.
A release still needs the owner's order.
