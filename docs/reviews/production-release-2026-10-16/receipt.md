# Production release b474cafbc434 — 16/10/2026

Owner approval (chat, 16/10/2026): "nội dung rồi đó, bạn hãy push live", and "check every change and
staging/production mismatch". The content workbook (`content-approval.xlsx`, 76 lines) came back
unedited, so every line is approved as written.

## What is live

| Item | Value |
|---|---|
| URL | https://la-lanh.2-28-136-44.sslip.io |
| Release / source | `b474cafbc434` = public `main`, fast-forward push of `collab/integration` (no merge commit; tree identical to the Codex-approved `6cd7113`) |
| Scope | PRs #4, #8, #10, #11, #12 (Lá's companion line), #13 ("Tím đêm dịu" UI), each with Codex APPROVE at its merged SHA |
| Image | `la-lanh:b474cafbc434`, `sha256:10ba22405c47…`, saved at `/opt/la-lanh/releases/la-lanh-image-b474cafbc434.tar` |
| Database | Alembic `20261011_0036` (unchanged, no migration in this release) |
| Flags | generation/worker off, auth/Google off, Swiss Ephemeris `agpl` |
| Timers | guest + expired cleanup active |
| Rollback | `la-lanh:a6e11bfd149b` (same schema, same `database_url`; no secret change needed) |
| Staging | same image digest, own DB, generation off (`STAGING_GENERATION=off`) |

## Evidence

- Gate on `6cd7113` (tree identical to `b474caf`): `pnpm check` exit 0. Results: 442 web tests, 1624 API tests pass / 56 skip, content audits, QA smoke.
- Backup `la-lanh-20261016T072144Z.dump` (724K, checksum OK).
- Rehearsal: newest backup restored into disposable TLS PostgreSQL, 26 guest sessions, head 0036 → 0036, `database-privacy-isolation-ok`, rows preserved, `/v1/ready` OK, container destroyed.
- `deploy.sh`: DB TLS OK. Content review in image: direct and roast voices, each 10 personas × 30 readings, no critical/high and 0 medium. Privacy check passed, app/Caddy healthy.
- Smoke, both environments: `smoke.sh` passed; `qa-public-smoke.mjs` passed for date-only note, share/revoke, Aura and charts, Tarot 1/3/5 and Radar exact/unknown, and deleted its own guest.
- Browser acceptance, production, 375 px, synthetic guest: Welcome → birth → reveal → Home with night card, "Thử một việc nhỏ", "Đọc đầy đủ", mood pill and 3D Lá. `/v1/daily-note` returns `sections.companion` = the authored missing-context line. Only `la_lanh_csrf` is script-visible. (Correction: my "mutation without CSRF → 422" probe sent an empty body to `onboarding-status`, so 422 may be schema validation, not the CSRF guard. It is not CSRF evidence. Codex's independent probe, POST `birth-profile` without the CSRF header → **403** and the same request with it succeeds, is the evidence.) The guest was deleted via Mình → Xoá (session 401, no cookies).

## Staging ↔ production parity

| Check | Result |
|---|---|
| Image digest | identical (`10ba22405c47…`). A first staging start used an earlier build of the same source; staging was recreated on the deployed image |
| Web bundle, `sw.js` (`la-lanh-app-shell-v5`), `offline.html/.css`, manifest | byte-identical |
| Effective settings (41 non-secret fields read inside each container) | only `cors_origins` differs (own origin) |
| `app.env` file | staging omits `GENERATION_PROVIDER`/`GOVERNANCE_APPROVED` lines (stripped by `up.sh`); effective values equal (`disabled`/`false`) |
| Alembic | both `20261011_0036 (head)` |
| Security headers | identical except HSTS `includeSubDomains` on production only. This is pre-existing in `sites/staging.caddy` (unchanged since a6e11bf); production's header already covers the staging subdomain |
| Release strings in bundle | every replaced string is absent on both. Every new UI string from the workbook is present except **U08 "Lá nhắc"**: that is the internal name of the single reminder slot, used only in code comments, and no UI label renders it. Each reminder shows its own title ("Còn lá ẩn chờ bạn mở", "Chủ nhật · nhìn lại tuần", …). U13 is a template (`Xoá lần Radar với [tên]?`), checked with a QA name. The workbook keeps the owner-approved text as received; this row records the correction. |
| Caddy alias `app` | resolves to production only (guard from the 11/10 incident holds) |

## Found during release

1. **Low-contrast destructive button (fixed in follow-up PR, not yet deployed):** the new
   `ultraviolet.css` set `.danger-button` text to `--uv-danger` (#8b332b) while the legacy red
   background (#b7294d) stayed: **1.32:1** (measured live on both environments). Affects "Xóa vĩnh viễn" and "Xoá lịch sử" in Profile.
   The buttons still work. The fix makes it a filled danger pill: white on #8b332b = **8.06:1**, dark theme #2a0f12 on #ffb4a6 =
   **10.49:1**, with a contrast regression test.
2. `rehearse-migration.sh` must be invoked by absolute path: a relative path makes Docker treat
   `infra/hetzner/entrypoint.sh` as a volume name.
3. One synthetic guest remains in the staging database (a click missed during cleanup). Staging data
   only; it expires with 30-day inactivity cleanup.

## Not covered

Real devices/iOS/Android, real-user comprehension, Luna generation (still off; human scoring and
governance gates open), Google login (off).

## Addendum — independent smoke by Codex (16/10/2026)

Codex's smoke report on PR #15 (comment 6212742235) confirmed both environments for smoke, synthetic
write flows, Home UI, overflow at 320/360/390 px, pause, birth-time reminder priority and snooze,
companion direct→roast, Tarot 3, Radar invite revoke + sheet delete, privacy/consent copy, offline
CSP, headers/cookies, CSRF (403), and byte-identical assets. It found:

- **F1 (P2):** Radar private history deleted on a single tap (`RadarPrivateStartPage.tsx:213`),
  and the owner result page used tap-twice inline. Fixed in #16 with the shared owner-epoch
  `RadarEraseSheet`. **Deployed in `836222282dfc`** (see `receipt-836222282dfc.md`).
- **F2 (P2):** the 1.32:1 destructive button above. Fixed in #15. **Deployed in `836222282dfc`**.
- **F3 (P3):** the string claim and contrast figures above, corrected here.

### Runtime evidence added afterwards (live b474caf, headless Chromium via Playwright, synthetic guests)

| Gap Codex named | Result on the live site |
|---|---|
| Real reduced motion | `/welcome` with OS preference off: 14 running animations; with `reducedMotion: reduce`: `matchMedia` true, **0** running animations. Home under reduce: **0** |
| Sunday / night reminder priority | Clock set to Sunday 18/10 21:30 ICT, one note saved. Bubble order: birth-time unlock → "Chủ nhật · nhìn lại tuần" (1 note) → "Khuya rồi. Bật nền tối…" → companion line. Each step is dismissed with its own X |
| Companion = this session's `/v1/daily-note` | DOM "Hỏi lại một câu thôi, đỡ hơn đoán cả buổi." equals `reading_projection.active.sections.companion` captured from the **same page's** responses (3 seen). The card's action is "hỏi người gửi giải thích" |
| Sheet hides on re-verification, focus returns | Profile "Xoá lịch sử đã xem?" sheet, focus on "Giữ lịch sử". `/v1/session` held, window `focus` dispatched: sheet **not visible**, focus on `body`. Released: sheet visible, focus back on "Giữ lịch sử". Escape closes it, focus returns to the opener |

Still open: real devices/OS-level reduced motion (the result above is browser emulation of the
media feature, not an OS toggle); a true background-tab/BFCache cycle (re-verification was triggered by a
dispatched `focus` event with the session request held).

**Cleanup:** the reverify guest was deleted (session 401). The first evidence run stopped before its
cleanup step, so **one synthetic guest remains in production**: date-only 14/03/1995, one saved
note, no account, created 16/10. Its cookies were discarded with the browser context, so it cannot
be deleted through the app. It expires under the 30-day inactivity cleanup. No SQL deletion was
attempted, to avoid touching non-test rows.
