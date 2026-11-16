# Production hotfix 56523ccb7de5 — 2026-11-15

Owner order (15.11.2026, in chat, answering "Duyệt xong thì cho đưa bản sửa này lên bản chạy thật?"): "Cho đưa lên".
Operator: Claude over SSH, synthetic identities only. Forward-only; no migration.

## What shipped

- Only the fix from #546 (issue #545), cherry-picked as `56688d3` onto `main` `f6246ed` → hotfix PR #549 →
  `main` = `56523ccb7de5a18df7e5aa9510e27a48e77d2794`. No other `collab/integration` change is included.
- User effect: on Hôm nay, "Đọc bản mới" opens the offered reading for every profile type. Before, approximate-time
  profiles (and date-only profiles after a same-day content re-read) always got "Món quà chưa mở được"
  (API 409 from `activate_available`, which only accepted `full_synthesis` with a known time). The current-chart
  pin, ownership, row lock and CAS on `available_revision_id` are unchanged.
- Content release gate: availability-hotfix waiver (`content-matrix-release-gate.md`); no content change. The next
  planned release carries the deferred content work.

## Checks before deploy

| Check | Result |
|---|---|
| Codex review of the change | APPROVE on #546 at `de0b5be0` (same diff) |
| `uv run pytest tests/readings tests/daily tests/integration` on the hotfix tree | 4494 passed |
| New regression test `tests/daily/test_reading_update_activation.py` | 3 failed before the fix, 5 passed after (#546) |
| CI on #549 | CodeQL (actions, java-kotlin, js/ts, python, swift) pass; merge state CLEAN |
| Release tree vs `f6246ed2fb7a` on the host | `diff -rq`: only `readings/postgres.py` differs, plus the new test file; `infra/` identical |

## Server steps (UTC, 15.11)

| Step | Result |
|---|---|
| Source | `git archive` of `56523ccb7de5` (sha256 `b13c3ec1…0902d`, same on host) → `/opt/la-lanh/releases/56523ccb7de5/source`, 1,968 files. `app.env` (byte-identical) and `sites/staging.caddy` copied from `f6246ed2fb7a` |
| Backup | `la-lanh-backup.service` → `la-lanh-20261115T042905Z.dump` (450 KB), `sha256sum -c` OK |
| Rehearsal | Not run: no schema change (runbook rehearses schema changes); Alembic stays `20261111_0042` |
| Deploy | `deploy.sh` with `APP_HOSTNAME`, `LA_LANH_RELEASE_ID=56523ccb7de5`, `LA_LANH_SECRETS_DIR`. Content review passed (10 personas, 30 readings, no critical/high); Roast voice review passed; no migration ran; `database-privacy-isolation-ok`; app, worker, Caddy healthy. Log: `releases/56523ccb7de5/deploy.log` |
| Image | `la-lanh:56523ccb7de5` = `sha256:f42a945ee43e…` |
| Alembic | `20261111_0042 (head)` |
| `current` | `/opt/la-lanh/current` → `releases/56523ccb7de5/source` (atomic `mv -T`) |
| `smoke.sh https://la-lanh.2-28-136-44.sslip.io` | PASS |
| `/v1/ready` | production 200, staging 200 |
| Timers | 5 `la-lanh*` timers listed |
| Staging | `staging/up.sh` with `LA_LANH_RELEASE_ID=56523ccb7de5`, `STAGING_GENERATION=off`; staging infra unchanged (only its two server-only env files differ). Runs the same image |
| `qa-public-smoke.mjs` (integration checkout, `LA_LANH_SMOKE_WRITE_CONSENT=synthetic-only`) | 9/9, QA guest deleted |
| AC1 check on production (fresh cookie jar, fictional date-only profile → note → add approximate time) | update offered → `PUT …/activate` 200, active `limited/approximate` → after reload no offer; guest deleted |

## Product journey

Production `56523ccb7de5`, 15.11.2026 ~11:30 Vietnam time. `pnpm qa:journey` (`scripts/qa-product-journey.mjs`
from a `collab/integration` checkout; the released tree does not carry the script), Chromium 390 px, one synthetic
person with date, time and place, 22 steps.

- Result: `required failed: 0; guest deleted: true`. Content verdict (report mode) PASS for the Khám phá overview.
  No 5xx, no horizontal overflow; the journey recorded no control under 44 px (Codex measured four, below). One console error: the expected 401 of the first
  session check. Ready times: most screens under 1.1 s; note direct, Jyotish overview and Aura about 1.8–2.0 s.
- Claude review: all 22 screens looked at. Works end to end; no regression from the hotfix. Same known problems
  as 13.11, whose fixes are in #503 and still wait for the owner: "Vibe · Bền" labels on share cards, English and
  mechanism words ("Receipt mở khóa", "Các House", "Preview Note Aura", "Tạo safe link", "Copy link",
  "Story 9:16"), onboarding lines "Bạn xuất hiện ngày nào?" and "Khớp tín hiệu", and the "Giữ hồ sơ khi đổi máy ·
  đăng nhập tuỳ chọn" invite while sign-in is off. Calm and readable overall; score 3/5, unchanged from 13.11.
- Codex review: from the files (`journey.json`, 22 screenshots, step texts), one pass. 22/22 steps work, no
  overflow at 390 px, slowest ready 2 s. Scores 2–5 per flow; weakest is Aura (clarity 2, feel 2: heavy mechanism
  copy). No P0/P1 regression from the hotfix. All 13.11 known problems still present (Vibe, Receipt/House/Preview,
  "Tạo safe link"/"Copy link", poetic onboarding, sign-in invite while Google is off). It measured four tap targets
  under 44 px that the journey's own check did not flag: privacy link 93×16, hide-Lá line 40×40, two Radar links
  306×15, dark-mode switch 52×32. It noted the journey profile used an exact time, so the fixed approximate-time
  case is not visible in the screenshots; that case is covered by the separate AC1 production check above.
  `VERDICT: GO`.
- Owner report: sent in chat on 15.11.2026 (~11:45) with the verdict, the AC1 result and the known problems; push sent.

## Rollback

- Previous image `la-lanh:f6246ed2fb7a` (`sha256:b9e860240f01…`) runs on the same schema `0042` and is a valid
  immediate rollback anchor for this hotfix (no migration in between). Rolling back restores the bug.
- Restore into service is still forbidden (P07/B).

## Still open

- Fixes for the known copy problems above are in #503 / #505, held for owner approval of the two privacy sentences.
- The built-in browser profile used by agents holds an existing production guest session of unknown origin; it was
  not used or read. Release QA must use a fresh cookie jar (as above), never that profile.
