# Production release b474cafbc434 — 16/10/2026

Owner approval (chat, 16/10/2026): "nội dung rồi đó, bạn hãy push live", and "check every change and
staging/production mismatch". The content workbook (`content-approval.xlsx`, 76 lines) came back
unedited, so every line is approved as written.

## What is live

| Item | Value |
|---|---|
| URL | https://la-lanh.2-28-136-44.sslip.io |
| Release / source | `b474cafbc434` = public `main` (fast-forward of `collab/integration`, PR #3) |
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
- Browser acceptance, production, 375 px, synthetic guest: Welcome → birth → reveal → Home with night card, "Thử một việc nhỏ", "Đọc đầy đủ", mood pill and 3D Lá. `/v1/daily-note` returns `sections.companion` = the authored missing-context line. A mutation without CSRF is rejected (422). Only `la_lanh_csrf` is script-visible. The guest was deleted via Mình → Xoá (session 401, no cookies).

## Staging ↔ production parity

| Check | Result |
|---|---|
| Image digest | identical (`10ba22405c47…`). A first staging start used an earlier build of the same source; staging was recreated on the deployed image |
| Web bundle, `sw.js` (`la-lanh-app-shell-v5`), `offline.html/.css`, manifest | byte-identical |
| Effective settings (41 non-secret fields read inside each container) | only `cors_origins` differs (own origin) |
| `app.env` file | staging omits `GENERATION_PROVIDER`/`GOVERNANCE_APPROVED` lines (stripped by `up.sh`); effective values equal (`disabled`/`false`) |
| Alembic | both `20261011_0036 (head)` |
| Security headers | identical except HSTS `includeSubDomains` on production only. This is pre-existing in `sites/staging.caddy` (unchanged since a6e11bf); production's header already covers the staging subdomain |
| Release strings in bundle | all new strings present, all replaced strings absent, on both |
| Caddy alias `app` | resolves to production only (guard from the 11/10 incident holds) |

## Found during release

1. **Low-contrast destructive button (fixed in follow-up PR, not yet deployed):** the new
   `ultraviolet.css` set `.danger-button` text to `--uv-danger` (#8b332b) while the legacy red
   background (#b7294d) stayed, about 1.6:1. Affects "Xóa vĩnh viễn" and "Xoá lịch sử" in Profile.
   The buttons still work. The fix makes it a filled danger pill with white text (≈7.6:1) and a
   dark-theme equivalent, with a contrast regression test.
2. `rehearse-migration.sh` must be invoked by absolute path: a relative path makes Docker treat
   `infra/hetzner/entrypoint.sh` as a volume name.
3. One synthetic guest remains in the staging database (a click missed during cleanup). Staging data
   only; it expires with 30-day inactivity cleanup.

## Not covered

Real devices/iOS/Android, real-user comprehension, Luna generation (still off; human scoring and
governance gates open), Google login (off).
