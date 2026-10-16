# Production release 836222282dfc — 16/10/2026 (hotfix)

Owner order (chat, 16/10/2026): "merge và deploy #15, #16". The order also approves the new Radar
sheet copy ("Xoá kết quả với {tên}?" / "Bản đọc này sẽ không còn mở được, kể cả từ lịch sử. Việc
này không hoàn tác được.").

| Item | Value |
|---|---|
| Source | `main` = `collab/integration` = `836222282dfc`. #15 merged at its approved head `5ff226c`, then #16 at `7c61fb5`. Tree identical to `7c61fb5` |
| Image | `la-lanh:836222282dfc`, `sha256:aabf64a081d0…`, saved at `/opt/la-lanh/releases/la-lanh-image-836222282dfc.tar`. Staging runs the same digest |
| Database | Alembic `20261011_0036` (no migration). Backup `la-lanh-20261016T121230Z.dump` (732K, checksum OK) |
| Flags | generation/worker off, auth/Google off, `agpl` |
| Rollback | `la-lanh:b474cafbc434` (same schema/secrets) |

## Evidence

- Local rehearsal of the same merge: `pnpm check` exit 0. Results: 448 web tests, 1624 API tests pass / 56 skip, content review direct + roast, QA smoke.
- Rehearsal on the backup copy: 27 guest sessions, head 0036 → 0036, privacy isolation OK, ready.
- `deploy.sh`: DB TLS OK. Content review in image: direct + roast, 10 personas × 30 readings each, 0 findings. Privacy check passed.
- `smoke.sh` and `qa-public-smoke.mjs` passed on staging (before and after) and on production.
- Deployed-build browser evidence, headless Chromium, 375 px, synthetic guest deleted at the end (session 401), **production and staging both**:
  - Radar private history: trash → sheet "Xoá kết quả với QA tổng hợp?" with 0 DELETE. "Giữ lại" → item kept, 0 DELETE. "Xoá" → exactly 1 DELETE, item gone.
  - Same-owner re-verification (`/v1/session` held, `focus` dispatched): sheet hidden, focus `body`. Released: sheet visible, focus back on "Giữ lại", 0 DELETE.
  - Owner result page: first tap → sheet, 0 DELETE. "Xoá" → 1 DELETE, lands on `/radar/start#radar-history`.
  - "Xóa vĩnh viễn": `rgb(255,255,255)` on `rgb(139,51,43)` = **8.06:1**. Dark theme via the real switch: `rgb(42,15,18)` on `rgb(255,180,166)` = **10.49:1**.
- Parity: identical image digest, bundle (`38ff5d77…`), `sw.js` v5, offline page/CSS, manifest, Alembic head. New Radar copy is present on both; "Chạm lại để xóa hẳn kết quả" is gone. Header difference is only the known HSTS `includeSubDomains`.

## Incident during release (fixed)

`deploy.sh` recreated Caddy, which mounts `sites/` from the **new** release directory. That
directory had no `staging.caddy` (server-only file, not in Git), so staging returned a TLS internal
error for about 10 minutes. Production was unaffected. Fix: copied `staging.caddy` from the previous
release and restarted Caddy; production had a 2–3 s restart, then both returned 200. The runbook
now lists copying `sites/staging.caddy` with `app.env`.

## Open

- OS-level reduced motion on a real device; a true background-tab/BFCache cycle.
- One synthetic guest left in production by the 16/10 evidence run (expires with 30-day cleanup),
  and one on staging. This release's runs left none.
- Luna generation and Google login remain off; their gates are unchanged.
