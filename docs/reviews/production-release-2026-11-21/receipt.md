# Production hotfix 42b678c13a93 — 2026-11-21

Authority: the owner's standing hotfix permission (R12 in `docs/operations/luat-dang-hieu-luc.md`, valid until 29.11.2026). On 20.11 the owner was told that this fix would ship under R12 once reviewed. All six conditions are proven below.
Operator: Claude over SSH, synthetic identities only. Forward-only; no migration.

## What shipped

- Only the crisis-guard fix from #808 (issue #809). Merge `a145367e21fd` on `collab/integration` was cherry-picked with `-m 1` as `c800226d` onto `main` `577a5d0b`, released through hotfix PR #824. `main` is now `42b678c13a9333c68840e5ac65b2ae06dff4be81`. No other `collab/integration` change is included.
- What users see: typed text such as "Tối nay mình sẽ đi xa mãi mãi rồi", "… để không ai phải lo nữa", "… khỏi cuộc đời này" or "Em sẽ đi xa mãi mãi thôi" now gets the crisis notice instead of a reading. The guard is shared by Tarot and every other input that uses it.
- The new lookahead is a superset of the old one, so every text the 20.11 release flagged is still flagged. Telling grief for a relative apart from a farewell letter is not in this hotfix (#819).

## R12 conditions

| # | Condition | Evidence |
|---|---|---|
| 1 | Reproduced on production | `detect_crisis` at `main` `577a5d0b`, the code of the 20.11 release, returned False for the five missed lines and True for the base line "Tối nay mình sẽ đi xa mãi mãi". |
| 2 | Regression test red, then green | New phrase-table cases on the production rule: `tests/safety` 1 failed, 59 passed. With the fix, all pass. Full `uv run pytest tests` on the release tree: 11171 passed, 72 skipped, 1 xfailed. |
| 3 | Codex APPROVE on the exact release SHA | Manual read-only Codex review (`scripts/codex-review.mjs` only reviews PRs into `collab/integration`), counted in the day's Codex runs. `VERDICT: APPROVE c800226d72fe8eb00383f5e70ccd3ddc14cea2dc`. An earlier review approved `0719b7a4`, whose cherry-pick trailer named a wrong source SHA. The trailer was fixed (tree identical) and re-reviewed. Codex compared 8,841 cases: zero cases flag less than before, and no catastrophic backtracking was found. Verdict posted on #824. |
| 4 | No migration, data, copy, privacy, auth/IAM, secret, dependency or cost change | Two files: `apps/api/app/domains/safety/crisis.py` (+11/−1) and `apps/api/tests/safety/crisis_phrases.py`. On the host, `diff -rq` against the 20.11 release shows only these two files; `app.env` is byte-identical and `infra/` is unchanged. |
| 5 | Single cherry-pick | One commit on top of `577a5d0b`. CodeQL (actions, java-kotlin, js/ts, python, swift) passed on #824; merge state CLEAN at the reviewed head. |
| 6 | Rollback anchor; smoke, AC and journey after deploy | See the sections below. |

## Server steps (UTC, 21.11)

| Step | Result |
|---|---|
| Source | `git archive` of `42b678c13a93` (sha256 `15a0ac87f065…3f9e43`, same on host) → `/opt/la-lanh/releases/42b678c13a93/source`. `app.env` (byte-identical) and `sites/staging.caddy` copied from `577a5d0b7a98` |
| Backup | `la-lanh-backup.service` → `la-lanh-20261121T055327Z.dump` (477 KB), `sha256sum -c` OK |
| Rehearsal | Not run: no schema change |
| Deploy | `deploy.sh` with `APP_HOSTNAME`, `LA_LANH_RELEASE_ID=42b678c13a93`, `LA_LANH_SECRETS_DIR`. Content review passed (10 personas, 30 readings, no critical/high). Roast voice review passed. No migration ran. `database-privacy-isolation-ok`. App, rewrite worker and Caddy healthy. Log: `releases/42b678c13a93/deploy.log` |
| Image | `la-lanh:42b678c13a93` = `sha256:807bdcbcff52…` |
| Alembic | `20261111_0042 (head)` |
| `current` | `/opt/la-lanh/current` → `releases/42b678c13a93/source` (set by `deploy.sh`) |
| `smoke.sh https://la-lanh.2-28-136-44.sslip.io` | PASS |
| `/v1/ready` | production 200, staging 200 |
| Timers | 6 `la-lanh*` timers listed |
| Staging | `staging/up.sh` with `LA_LANH_RELEASE_ID=42b678c13a93`, `STAGING_HOSTNAME=staging.la-lanh.2-28-136-44.sslip.io`, `STAGING_GENERATION=off`. It runs the same image; the staging infra differs only in its two server-only env files |
| `qa-public-smoke.mjs` (integration checkout, `LA_LANH_SMOKE_WRITE_CONSENT=synthetic-only`) | 9/9, QA guest deleted |

## AC check on production

A fresh cookie jar and a fictional guest sent six Tarot questions to `POST /v1/tarot/sessions`:
- the five lines that production missed before, one of them typed without accents;
- the base line, as a control.

All six answered `422 CRISIS_NOTICE` with `Cache-Control: no-store`, and no Tarot session was created. The guest was deleted (`DELETE /v1/guest-session` 204). The script prints no cookies, tokens or ids.

## Product journey

Production `42b678c13a93`, 21.11.2026, about 13:00 Vietnam time. `scripts/qa-product-journey.mjs` ran from a `collab/integration` checkout: Chromium at 390 px, one synthetic person with date, time and place, 22 steps.

- **Result:** `required failed: 0; guest deleted: true`. Content verdict (report mode) PASS for the Khám phá overview. No horizontal overflow at 390 px.
- **Optional step 10 (mood) failed** with a click timeout. The script still looks for the old mood button label, while the screen shows "Chọn". This is a known script issue from 20.11, not a regression.
- Claude review: Home and Tarot screens look as they did in the 20.11 release. The hotfix changes no screen.
- Codex review: one pass over `journey.json`, the 22 screenshots and the step texts. `VERDICT: GO-WITH-FOLLOWUPS`. No P0/P1, no hotfix regression.
  - Scores: onboarding 4, Hôm nay 4, note 4, Khám phá/Aura 3, Tarot 4, Hợp gu 3, profile/delete 4.
  - Follow-ups:
    - update the mood selector;
    - trace the one console 401 (expected first session check, as on 15.11);
    - low contrast on the profile share button, small tap targets, dense technical words in Khám phá;
    - the Tarot line about hiding or avoiding something reads as accusatory.
  - The crisis behaviour is not in the journey; it is covered by the AC check above.
- Owner report: push notification sent right after the deploy; this use of R12 is listed in the owner's approvals file.

## Rollback

- The previous image `la-lanh:577a5d0b7a98` runs on the same schema `0042` and is a valid immediate rollback anchor (no migration in between). Rolling back brings back the missed farewell lines.
- Restore into service is still forbidden (P07/B).
