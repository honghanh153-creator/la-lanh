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
- Parity (operator): identical image digest (`docker inspect`), Alembic head, and served assets. Asset
  hashes are SHA-256 of the bytes served over HTTPS, identical on production and staging:

  | Resource | SHA-256 |
  |---|---|
  | `/assets/index-CziJ47Kd.js` | `9e70702e2d37945844d6a31ef045faea721374704fc7a8a4e72abb7812b93fcd` |
  | `/assets/index-9zq55vFH.css` | `0df4ae3af2f1629f414662efdc0d1529385e42b14ec61884cd72415bc4305f46` |
  | `/sw.js` (cache `la-lanh-app-shell-v5`) | `4be71c03d3262bf3ce776cbf7266a943d122c58f31e050f33cd5172c8248ee1c` |
  | `/offline.html` | `0f068ff9dbeb21cfedb60e36158e50d6355929b157fcd29f105ad777baff35c0` |
  | `/offline.css` | `127d329b42f3c4b50422ae09681ae1837be02c33f6fb10c6f6628887531d8b34` |
  | `/manifest.webmanifest` | `0868934c8161e2378bb6d9860a213938a526f7c7d97e0b44c9f3cd2d79c2f3bb` |

  The earlier shorthand "bundle `38ff5d77…`" was the SHA-256 of the CSS file followed by the JS file,
  concatenated in that order (sorted asset paths): `38ff5d7714984f00d7b3a26c3f7d89a2c706f20e08677e1226c6416f88e37a30`.
  It is derived from the two per-file hashes above and is not a separate artifact.
- New Radar copy is present on both; "Chạm lại để xóa hẳn kết quả" is gone. Header difference is
  only the known HSTS `includeSubDomains` (production only, from `sites/staging.caddy`).

## Incident during release (fixed)

`deploy.sh` recreated Caddy, which mounts `sites/` from the **new** release directory. That
directory had no `staging.caddy` (server-only file, not in Git), so staging returned a TLS internal
error for about 10 minutes. Production was unaffected. Fix: copied `staging.caddy` from the previous
release and restarted Caddy; production had a 2–3 s restart, then both returned 200. The runbook
now lists copying `sites/staging.caddy` with `app.env`.

## Independent verification (Codex, 16/10/2026)

Codex approved this receipt at `72f3d0d` and ran its own smoke on production and staging from a git
archive of the release: [verdict](https://github.com/honghanh153-creator/la-lanh/pull/17#issuecomment-6216088257),
[smoke report](https://github.com/honghanh153-creator/la-lanh/pull/17#issuecomment-6216142296).
Synthetic guests only, all deleted (204, then `/v1/session` 401). Every requested check passed on
**both** environments:

- `smoke.sh` and `qa-public-smoke.mjs` exit 0.
- Radar result page: the first tap on "Xóa kết quả này" opens the sheet, with 0 DELETE after the tap
  and after "Giữ lại".
- Radar history: trash opens the sheet with 0 DELETE. "Giữ lại" keeps the item. "Xoá" sends exactly
  1 DELETE (Playwright request count; production also cross-checked in Chrome DevTools Network).
- Owner change while the sheet is open, checked two ways (another tab deletes A and creates B; the
  cookie jar switches from A to B): the sheet and A's label disappear, no Radar DELETE.
- Same-owner re-verification (`/v1/session` delayed by a Playwright route, then continued to the
  server unchanged): the sheet is hidden and focus goes to `body`, then the sheet returns with focus on
  "Giữ lại". 0 DELETE.
- "Xóa vĩnh viễn" and "Xoá lịch sử": light 8.06:1, dark 10.49:1 (dark via the real switch).
- The six asset hashes above, the SW cache name and the header set match; the only header difference
  is HSTS `includeSubDomains`.

Codex's limits: the image digest, backup, Alembic head, timer state and the ~10-minute staging TLS
window are operator receipts, not independently measured. In the re-verification run Codex blocked
the service worker in that context so the route could observe the request, and checked the SW
separately via asset parity.

## Not verified by anyone in this release

- **OS-level reduced motion** on a real device. Only the browser media emulation
  (`reducedMotion: reduce`) was measured, in the 16/10 evidence run on `b474caf`.
- **A real background-tab / BFCache cycle.** Re-verification was triggered by a dispatched `focus`
  event with the session request held, not by backgrounding or restoring a page from BFCache.

## Open

- OS-level reduced motion on a real device and a real background-tab/BFCache cycle (see above).
- One synthetic guest left in production by the 16/10 evidence run (expires with 30-day cleanup),
  and one on staging. This release's runs left none.
- Luna generation and Google login remain off; their gates are unchanged.
