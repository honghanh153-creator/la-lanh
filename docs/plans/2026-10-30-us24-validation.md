# US-24 validation notes: human Tarot reader via Google Sheet (30/10/2026)

Stack (each PR reviewed at its own SHA): spec `docs(us-24)` → U4 admission/APIs → U5 Sheet bridge → U6 web →
U7 this note and the data map. Base: `collab/integration` (`e0d62fa`). Migrations `20261030_0041` and
`20261030_0042` revise `20261023_0038`; whichever of this stack and the birth-correction stack (0039/0040) merges
second rebases its `down_revision` onto the other (plan KTD8). **Nothing is enabled**: both flags default to
false, staging/production refuse them without `human_tarot_launch_approved`, no Google credential, file id or
call exists, and no real question was used anywhere (synthetic data only).

## AC matrix (US-24 §10)

| AC | Evidence | Status |
|---|---|---|
| AC01 20 concurrent → 10 | `test_admission.py::test_ac01…` (SQLite file DB, BEGIN IMMEDIATE); `test_postgres_admission_probe.py` | SQLite pass; PostgreSQL written, not run |
| AC02 same key once | `test_ac02…`; PG probe | SQLite pass; PG not run |
| AC03 one per guest/day, also after cancel | `test_ac03…`, HTTP `test_create_read_and_cancel…` | Pass |
| AC04 cut-off, replay after it, lock waiter | `test_ac04…` ×2, `test_owner_cut_off_earlier_than_ten` | Pass |
| AC05 never refunded | `test_ac05…` | Pass |
| AC06 Vietnam midnight | `test_ac06…` | Pass |
| AC07 consent / filter / key take no slot | `test_ac07…`, HTTP `test_rejected_question…` | Pass |
| AC08 22:00 by server clock | `test_ac08…`, `test_ready_row…opens_at_22` | Pass (device clock: release decided only server-side; web refetch is presentation) |
| AC09 owner only | `test_ac09…`, HTTP `test_reads_need_a_session…` | Pass |
| AC10 late / unfulfilled, no machine reading | `test_ac10…`, `test_day_end_clears_yesterday…` | Pass |
| AC11 label + provenance | `test_ac11…`, web "Bài do người bốc viết" | Pass |
| AC12 RAW | `test_google_client.py::test_write_is_raw…`, `test_export_writes…as_text` | Pass (mock transport; no real Google call) |
| AC13 ambiguous timeout | `test_ambiguous_timeout…`; a write that lands after its clear is cleared again (`test_a_row_that_lands_after_its_clear…`, 15-minute watch) | Pass |
| AC14 429/403/5xx keep request, no content in logs | `test_google_failures…` ×3 | Pass |
| AC15 validation codes | `test_invalid_ready_rows…` ×9 | Pass |
| AC16 freeze once | `test_ready_row…` (Sheet edit after import) | Pass |
| AC17 header / sort / duplicate | `test_a_wrong_header…`, `test_duplicate_codes…`, `test_a_row_holding_another_code…` | Pass |
| AC18 budget 30/min, 2,000/day | `test_the_google_budget_fails_closed` | Pass |
| AC19 cancel blocks + readback | `test_ac19…`, `test_cancel_clears_the_row…` | Pass |
| AC20 cancel during export in flight | `test_a_cancel_during_an_export_in_flight…`; removing the state fence makes it fail (mutation control, not committed) | Pass |
| AC21 guest deletion, history clear, expiry, replay | `test_ac21…` ×3, `test_guest_deletion_and_unknown_codes…`, `test_question_is_purged…`; a request admitted during the grid read is not mistaken for an orphan (`test_a_request_admitted_during_the_grid_read…`) | Pass |
| AC22 restore closes the day | `test_intake_closed_after_restore…`, `test_bridge_wiring.py::test_operator_commands` (journal replay prints the closure) | Pass |
| AC23 Sheet/log minimization | `test_export_writes…` (no guest/request id), log assertions in AC14 | Pass |
| AC24 self-draw unchanged | TarotPage suite with the reader off; full API suite | Pass |

Still owed: PostgreSQL runs (needs a separate owner approval), a rehearsal against a synthetic Google file with a
granted service account (OD3/OD7), e2e on the QA stack, a native device check, and owner copy approval.

Self-review findings fixed before handoff (each with a test that fails on the earlier head): the orphan sweep read
the known codes before the grid and could clear a fresh request's row; a row that Google applied after its clear
had no clear job left. Both on U5.

## Privacy review (AGENTS.md gate 3)

New personal-data flow: the free-text question leaves the app's database for the first time to a third party
(Google, as Sheet host) and is read by a person (the owner). Inventory and retention: data map section "Human
Tarot reader delta". Controls in code:

- **Explicit, timely, separate consent** stored per request (`human-tarot-v1`), unticked by default, not merged
  with Tarot or Luna consent; the self-draw needs none of it.
- **Minimization**: the Sheet gets the code, date, release time, context label, question, number of cards and
  position labels; never a guest/session/request id, account, birth data, cookie, token or link
  (`test_export_writes…`). The intake filter of US-20 still rejects mind reading and high-stakes questions; users
  are told not to name other people. A free-text question can still contain sensitive data: no claim of anonymity.
- **Purpose and retention**: OD2, approved by the owner on 30/10, in `policy.py`; question removed from the app 24 h after release (or at
  day end / cancel), Sheet row cleared at cancel and day end, reading kept 30 days. Owner approval pending.
- **Deletion**: cancel/delete, guest deletion (cascade, then the slot loses its link and the Sheet row is cleared),
  history clear, expiry, journal replay (`human_tarot_request_cancelled`), restore (day closed, unknown Sheet rows
  cleared). The copy never says "deleted everywhere" until the Sheet readback confirms; Google revision history
  is outside the API (OD2 file rotation).
- **Encryption and access**: AES-GCM payload bound to the request id; three backend-only tables + two counters with
  RLS on and browser roles revoked; owner-only API, `no-store`, problem codes without content; logs carry counts
  and closed codes only.
- **Not yet consistent for real data**: the privacy policy, the in-app privacy notice (`ConsentPage`), P09/P10
  (new recipient Google, likely cross-border storage) and the store forms say nothing about this flow. That is
  correct while it is off and must change before it is on (OD6).

## Security review (AGENTS.md gate 2)

- **AuthN/AuthZ**: owner from the guest cookie; POST/DELETE need trusted Origin + CSRF; GET request needs a
  session; availability is public counts only. A foreign id answers 404 for read and delete.
- **Abuse**: durable cap in the DB (CHECK 0–10, one slot per guest per day, never refunded); admission buckets
  for create (10/peer) and availability (120/peer). Many guest sessions can still take all 10 slots (A2: an upper
  bound, not proof of 10 people).
- **Input**: `extra="forbid"`, 8–280 characters, closed enums, idempotency key pattern. Owner input from the Sheet is
  validated (catalog cards, lengths, no link/formula/HTML/control characters, unsafe-claim patterns) and rendered
  as React text (an `<img>` stays text, web test).
- **Third-party transport**: HTTPS only, `trust_env=False`, no redirects, 8 s timeout, RS256 JWT bearer for one
  scope, token cached in memory only, errors without bodies. The key file path comes from settings; the key never
  enters the repo, env or logs. Writes are RAW.
- **Integrity and races**: per-row leases, state-fenced completion (a committed cancel wins), freeze under the
  request row lock with a day check, one sync pass at a time, header check before any write, rows matched by code
  never by position. Unknown app codes are cleared rather than trusted.
- **Failure/rollback**: Google down → request kept, `delivery=error`, exponential back-off (max 15 min); budget
  exhausted → fail closed. Migrations are additive; downgrade keeps the tables so no Sheet row loses its clear job.
- **Threat model gaps**: the Sheet itself is protected only by Google sharing (one service account + the owner);
  anyone the owner shares it with can read questions. A compromised owner Google account exposes at most today's
  ≤10 questions plus revision history (OD2/OD7). No P0/P1 found in this review; Codex review pending.

## Sources checked (30/10/2026)

Internal: `AGENTS.md`, the Codex plan `docs/plans/2026-10-29-2222-feat-birth-human-tarot-plan.md`, US-20, US-23,
`tarot/service.py`, `content_rewrite/postgres.py`, erasure journal, history, guest deletion, data map.

Official:
- [Google Sheets API usage limits](https://developers.google.com/workspace/sheets/api/limits): 300 read and 300
  write requests per minute per project, 60 per user per project; standard use free, and the page says quota
  overage is planned to incur Google Cloud charges later in 2026. The app cap (30/min, 2,000/day) stays far below,
  and nothing raises quota or enables billing.
- [Google Cloud Data Processing Addendum](https://cloud.google.com/terms/data-processing-addendum/) (formerly the
  Workspace Data Processing Amendment): "Google is a processor and Customer is a controller or processor" under a
  customer agreement. Consumer Google accounts are not covered by it → OD7.
- [ValueInputOption RAW](https://developers.google.com/workspace/sheets/api/reference/rest/v4/ValueInputOption),
  [Sheets scopes](https://developers.google.com/workspace/sheets/api/scopes), and
  [Drive revisions.delete](https://developers.google.com/workspace/drive/api/reference/rest/v3/revisions/delete) as
  cited by the plan (29/10/2026).
- Law 91/2025/QH15 and Decree 356/2025/NĐ-CP: as assessed in the P09/P10 draft (#116, sources read 29/10/2026).
  This flow adds a recipient and likely a transfer abroad; no compliance claim is made.

## Owner decisions open

Settled by the owner on 30/10/2026: OD1 intake until 18:00 and release at 22:00, OD2 retention and monthly Sheet
rotation, OD3 service account on one file, OD7 Google Workspace account; OD5 delegated (remaining count shown).
Still open: OD4 copy (owner: Claude decides, Luna rewrites; calling Luna is a paid API, not allowed in this batch)
and OD6 P09/P10, privacy notice and store forms before enabling.
Plus: release order of the two stacks, any PostgreSQL run, the Google rehearsal and enabling anything.
