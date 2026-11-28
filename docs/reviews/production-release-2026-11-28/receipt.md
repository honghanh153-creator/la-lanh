# Production release 5518cca34786 — 2026-11-28 (weekly 27.11)

Authority: the owner answered "BK phát hành" on the Friday release item (R12 weekly schedule). The repetition gate in
the release evidence said "giữ"; the owner chose to release anyway. One-time approval for this release.
Operator: Claude over SSH, synthetic identities only. Forward-only; no migration.

## What shipped

- Candidate `collab/integration` `a3a1222215f9` merged with `main` `42b678c13a93` as `b5ad571d` (tree identical to
  `a3a12222`: the #808 hotfix was already in integration), released through PR #953. `main` is now
  `5518cca3478649ed2b8cedf1e7c6f37ec8cd24ce`.
- Owner switch AE1 (19.11.2026, #740): `LA_LANH_KEEP_ACTION_ALL_PROFILES=true` on production. Date-only and
  approximate-time profiles can now keep the Daily note's action. No other switch changed: the topic schedule and pixel
  Lá stay off.
- All lighter, slow, clear, alone and issue-light sentences (`lighter.*`, 87 entries) are still pending in the copy
  registry, so this build offers none of them and no such kept row can exist yet.

## Server steps (UTC, 28.11)

| Step | Result |
|---|---|
| Source | `git archive` of `5518cca34786` (sha256 `ab0abc889e95…c81a79ea`, same on host, 2,449 files) → `/opt/la-lanh/releases/5518cca34786/source`. `sites/staging.caddy` copied from `42b678c13a93` (identical); `app.env` copied from `42b678c13a93` plus the AE1 line, the only difference |
| Backup | `la-lanh-backup.service` → `la-lanh-20261128T072435Z.dump` (487 KB), `sha256sum -c` OK |
| Rehearsal | Not run: no schema change |
| Deploy | `deploy.sh` with `APP_HOSTNAME`, `LA_LANH_RELEASE_ID=5518cca34786`, `LA_LANH_SECRETS_DIR`; exit 0. Content review and Roast voice review passed. No migration ran. `database-privacy-isolation-ok`. App, rewrite worker and Caddy healthy; no error lines in the app log |
| Image | `la-lanh:5518cca34786` = `sha256:7517a74c5638…` |
| Alembic | `20261111_0042 (head)` |
| `current` | `/opt/la-lanh/current` → `releases/5518cca34786/source` (set by `deploy.sh`) |
| AE1 | `printenv LA_LANH_KEEP_ACTION_ALL_PROFILES` in the app container: `true` |
| `smoke.sh https://la-lanh.2-28-136-44.sslip.io` | PASS |
| `/v1/ready` | production 200, staging 200 |
| Timers | 6 `la-lanh*` timers listed |
| Staging | `infra` refreshed from the release (previous copy kept as `infra.42b678c13a93`; its own `app.env`, `staging/app.env` and `staging/generation.env` kept). `staging/up.sh` with `LA_LANH_RELEASE_ID=5518cca34786`, `STAGING_HOSTNAME=staging.la-lanh.2-28-136-44.sslip.io`, `STAGING_GENERATION=off`: same image digest, healthy, network alias `staging-app` (not `app`). AE1 is not set on staging (off by default) |
| `qa-public-smoke.mjs` (released checkout, `LA_LANH_SMOKE_WRITE_CONSENT=synthetic-only`) | 9/9, QA guest deleted |

## AE1 check on production

A fresh cookie jar and a fictional date-only guest (birth date only):
- `POST /v1/birth-profile` → `calculation_kind: date_only_sun`; the Daily note's precision is `unknown`.
- `GET /v1/daily-note` offers `reading_projection.active.experiment` (the keep button).
- `PUT /v1/daily-note/{id}/experiment` → 200, the kept action matches the offered one; `GET /v1/daily-note/experiment`
  shows it; `DELETE /v1/daily-note/experiment` → 204.
- The guest was deleted (`DELETE /v1/guest-session` 204). The script prints no cookies, tokens or ids.

## Screens at 360 and 390 px

Headless Chromium from the released checkout (not the browser-pane profile), a fictional date-only person at 360 and
390 px: welcome, the birth-date screen filled in with "Tiếp tục" enabled, home, and the Daily note scrolled to
"Giữ để thử hôm nay". The keep button is visible at both widths, no horizontal overflow on any screen, and both
guests were deleted through Profile → "Xóa Lá và dữ liệu". The screenshots stay on the owner's machine (report folder of
28.11).

## Product journey

Production `5518cca34786`, 28.11.2026, about 14:30 Vietnam time. `scripts/qa-product-journey.mjs` ran from the released
checkout: Chromium at 390 px, one synthetic person with date, time and place, 22 steps.

- **Result:** `required failed: 0; guest deleted: true`. All 22 steps passed, the optional mood step included.
  Content verdict (report mode) PASS for the Khám phá overview. No horizontal overflow at 390 px. 4xx from `/v1`:
  2 expected; the one console 401 is the first-visit session check.
- Claude review: a Claude subagent looked at `journey.json`, the 22 screenshots, the step texts and the 360/390 shots.
  `VERDICT: GO-WITH-FOLLOWUPS`. No P0/P1; no regression in the date-only flow; the keep button renders cleanly at
  both widths; no tokens or ids on screen.
  - P2 copy: technical words on Khám phá and the aura/note pages ("Chart", "lớp/nhà", "TỔNG HÒA LÁ SỐ"); two awkward
    Daily action sentences.
  - P3: "Mình & người ấy" wraps to three lines at 360; three tap targets under 44 px; the Tarot card label is in
    English; "căn cứ riêng" on the share page is unclear.
- Codex review: run on 28.11.2026 in the evening, after the owner approved it ("BR1"). `codex exec -s read-only`
  on copies of `journey/` and the 360/390 shots only (synthetic data, no owner files). `VERDICT: GO-WITH-FOLLOWUPS`.
  No P0/P1: 22/22 steps, no 5xx, no horizontal overflow, guest deleted; the date-only keep button renders at both
  widths (what happens after the tap is not shown in these shots).
  - P2: say what "Giữ để thử hôm nay" does next to "Lưu note", and confirm after the tap; Aura page copy describes
    processing ("MỘT LỚP ĐỌC MỚI ĐÃ ĐƯỢC TÍNH"); onboarding explanations are long; small tap targets (privacy link,
    dismiss button, dark-mode switch); the bottom bar may cover the end of the Home message; the sky timestamp is
    unclear; Profile says "Nhóm test có tối đa 20 phiên đã đồng ý".
  - P3: poetic lines on Khám phá, Aura, birth card and saved notes; mechanism words (deck locking, encryption,
    "Chi tiết kỹ thuật"); English words ("Note", "Chart", "natal", "PNG", "OpenAI", Tarot card name); the Mood answer
    is announced three times; direct note ready at 2.0 s.
  - Follow-ups are tracked in #964.
- Owner report: sent to the coordinator session right after the checks, for the owner's next report.

## Rollback

- The previous image `la-lanh:42b678c13a93` (`sha256:807bdcbcff52…`) runs on the same schema `0042` and is a valid
  immediate rollback anchor; change only the app, never the data.
- To undo AE1 alone, set `LA_LANH_KEEP_ACTION_ALL_PROFILES=false` and recreate the app. New keeps for date-only and
  approximate-time profiles stop at once; actions already kept stay until closed or expired (≤30 days).
- If people without an exact time kept an action before a rollback, re-check `GET /v1/daily-note/experiment` and
  closing it on the old image after rolling back (not tested here).
- The #627 rollback limit does not apply yet: no lighter sentence is approved in this build.
- Restore into service is still forbidden (P07/B).
