# Production release 577a5d0b7a98 — 2026-11-20 (weekly release)

Owner order (20.11.2026, in chat, answering item AH in the approvals file): "Ah1". This means: release today,
accepting that 10 "people who saw a repeat" counts in the Daily-repetition gate rose by 1–4 out of 1000.
Operator: Claude over SSH, synthetic identities only. Forward-only; no migration.

## What shipped

- `collab/integration` `059d3c35` (the Friday release candidate), merged with `main` `56523ccb7de5` in #769 →
  `main` = `577a5d0b7a9875d0e66c9a780e6f4db5cb77b68c`. The tree is identical to `059d3c35`. The one add/add conflict
  (`tests/daily/test_reading_update_activation.py`) kept integration's newer expectation from #626.
- 141 PRs since the 13.11 release. What users see:
  - the self-harm guard on free text (#505);
  - "Vibe" removed, and no sign-in invite while sign-in is off (#503);
  - mood under the Note (#449);
  - less Daily repetition for approximate-time and date-only profiles (#660, #666, #684);
  - Jyotish with an approximate time (#388);
  - plain-language Daily copy (#491, #635, #685);
  - three owner-approved privacy sentences.
- Not in this release: #740 (keep action for every profile; `LA_LANH_KEEP_ACTION_ALL_PROFILES` stays unset) and #734
  (Lá line device memory).
- The approved-but-switched-off pieces stay off. No lighter-action sentence is approved, and the Lá line selector is
  off.

## Checks before deploy

| Check | Result |
|---|---|
| `pnpm check` on `059d3c35` (fresh worktree, test guard, 20.11 04:40–05:13 ICT) | PASS: web 719, API 11171 (72 skipped), e2e 37; content, Tarot, 10-persona, Roast and clarity gates pass |
| Nightly personas, 200 of 1000 (end of day = `059d3c35`) | safety 30/30, false alarms 0, HTTP errors 0; no row worse than start of day |
| Daily-repetition gate, 1000 personas × 29 days, `56523ccb7de5` vs `059d3c35` | every repeat-day count lower (headline 7-day 9144 → 6451; lighter action 29-day 14725 → 3371); 10 person-count metrics +1 to +4 of 1000 (largest +1.02%); crisis 135/135 on C, no cross-user leak. Strict rule: HOLD; the owner accepted it (AH1) |
| Blockers | no `owner-release-check` PR in C, no new data collection switched on, no migration, no open ops-alert or P0/P1 |
| CI on #769 | CodeQL (actions, java-kotlin, js/ts, python, swift) and screens pass; merge state CLEAN |

## Server steps (UTC, 20.11)

| Step | Result |
|---|---|
| Source | `git archive` of `577a5d0b7a98` (sha256 `2abfd57e…5b006`, same on host) → `/opt/la-lanh/releases/577a5d0b7a98/source`, 2,325 files. `app.env` (byte-identical) and `sites/staging.caddy` copied from `56523ccb7de5` |
| Backup | `la-lanh-backup.service` → `la-lanh-20261120T022715Z.dump` (403 KB), `sha256sum -c` OK |
| Rehearsal | Not run: no schema change; Alembic stays `20261111_0042` |
| Deploy | `deploy.sh` with `APP_HOSTNAME`, `LA_LANH_RELEASE_ID=577a5d0b7a98`, `LA_LANH_SECRETS_DIR`. Content review passed (10 personas, 30 readings, no critical/high, 0 medium); Roast voice review passed; no migration ran; `database-privacy-isolation-ok`; app (started 02:28:38), worker and Caddy healthy. `deploy.sh` set the active link itself (new in this release). Log: `releases/577a5d0b7a98/deploy.log` |
| Image | `la-lanh:577a5d0b7a98` = `sha256:a9eb4b1fcb73…` |
| Alembic | `20261111_0042 (head)` |
| `current` | `/opt/la-lanh/current` → `releases/577a5d0b7a98/source` |
| `/v1/ready` | private 200; public production 200, staging 200 |
| `smoke.sh https://la-lanh.2-28-136-44.sslip.io` | PASS |
| Timers | 5 production `la-lanh*` timers listed |
| Staging | `infra` refreshed from the release (previous copy kept as `infra.56523ccb7de5`; only the two server-only env files differ); `up.sh` with `LA_LANH_RELEASE_ID=577a5d0b7a98`, `STAGING_GENERATION=off`; same image, healthy. `install-db-tls-timer.sh` run once: `la-lanh-staging-db-tls.timer` active, first run OK (certificate valid until 13.12, renews under 10 days) |
| `qa-public-smoke.mjs` (released checkout, `LA_LANH_SMOKE_WRITE_CONSENT=synthetic-only`) | 9/9, QA guest deleted |

## Product journey

Production `577a5d0b7a98`, 20.11.2026 ~09:34 Vietnam time. `pnpm qa:journey` from the released checkout, Chromium
390 px, one synthetic person with date, time and place, 22 steps.

- First run: the required steps passed; the optional mood step failed. The script still clicked "Chọn mood", but #449
  renamed the trigger to "Chọn cảm giác hôm nay". This PR fixes the selector. Second run with the fixed selector:
  22/22, `required failed: 0; guest deleted: true`. Content verdict (report mode) PASS for the Khám phá overview.
  No 5xx, no horizontal overflow, no control under 44 px flagged by the journey. One console error: the expected 401
  of the first session check. Ready times: most screens under 0.8 s; note direct, Jyotish overview and Aura about
  1.85 s.
- Claude review: all 22 screenshots and texts read. GO with follow-ups, no P0/P1, average 4.1/5 (weakest Radar 3.6,
  Share/Khám phá/Aura 3.8).
  - Fixed since 15.11: "Vibe ·", "Receipt mở khóa", "Preview Note Aura", the sign-in invite while sign-in is off, and
    the #730 close-button overlap.
  - Still present (P2): "Bền" chip; "Các House"; "Tạo safe link", "Copy link", "Story 9:16", "Square 1:1";
    "Bạn xuất hiện ngày nào?" and "Khớp tín hiệu"; Aura and Radar mechanism or English copy; repeated planet lines in
    Khám phá; the four small tap targets. Plus P3 poetic lines.
- Codex review: from the files, one pass, `VERDICT: GO-WITH-FOLLOWUPS`. All steps work. Scores 2–5; weakest is Aura
  (clarity 2). Its known-problem checklist matches Claude's. It also flagged the white-on-lime profile button contrast
  and asked to recheck a truncated headline on the direct note.
- Owner report: sent in chat on 20.11.2026 (~09:50) with the verdict, the checks and the known problems; push sent.

## Rollback

- Previous image `la-lanh:56523ccb7de5` (`sha256:f42a945ee43e…`) runs on the same schema `0042` and is a valid
  immediate rollback anchor.
- The #627 lighter-action limit does not apply yet, because no approved lighter sentence is served.
- Restore into service is still forbidden (P07/B).

## Still open

- The copy follow-ups above (P2/P3) and the four small tap targets.
- The production crisis measurement in the repetition harness: it reads 0/135 on `56523ccb7de5` with statuses
  201/422. This is likely a harness/response-shape mismatch and is not verified.
- The 7h screenshot tool may still look for the old mood button; to be checked with the journey selector fix.
- Dependabot reports 8 moderate alerts on the default branch. These are not new in this release and are handled by
  the loop.
