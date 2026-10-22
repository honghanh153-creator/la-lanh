# P03 — retained security/privacy scan findings: current-SHA triage

Date: 2026-10-22. Audit item P03 (`la-lanh-audit-2026-10-22/privacy-content/review-v2.md`).
Judged against `origin/collab/integration` = `c3fab3311d659c240da944a84fec305eca416cc6`.

## Method and limits

- **Sources:** `retained-index.json` (86 entries); the historical `findings.json`/`report.md` of scan
  `99a3079a…_20261008T155125Z_wwcpz3ix` (75 entries, scan marked failed) and scoped scan
  `99a3079a…_20261008T135647Z_pgeahua7` (11 entries); `privacy-matrix.md`; current source and tests at
  the SHA above; PR #41 head `1fb1c83` (file list only).
- **This is a source review, not a re-scan.** No scan was restarted, no canonical scan artifact was
  modified, no code was run against live services, and no test was executed in this pass. "FIXED" means
  the current source has a control at the cited file:line *and* an existing test exercising it was found
  by grep; it is not a fresh test run. Tests marked *(opt-in PG)* skip unless
  `LA_LANH_TEST_POSTGRES_URL` is set.
- Paths are repo-relative. `api/` = `apps/api/app/`, `tests/` = `apps/api/tests/`, `web/` =
  `apps/web/src/`.
- Duplicates were grouped by the code path and missing control, not by title. 86 entries → 44 root
  causes (22 application, 22 vendored Swiss Ephemeris).
- Vendored Swiss Ephemeris (`vendor/swisseph/src`) is unchanged since 2026-08-31, so every native bug the
  scan described is **still present in vendor source**. The disposition records whether La Lành can reach
  it. The FFI binds only `swe_set_ephe_path`, `swe_set_sid_mode`, `swe_julday`, `swe_calc_ut`,
  `swe_houses_ex`, `swe_version`, `swe_close` (`api/domains/astro/ffi/swisseph.py:101-138`), with
  `SEFLG_SWIEPH|SEFLG_SPEED` only (`:14-17`); fixed body IDs 0-9, 11, 15 (`api/domains/astro/engine.py:59-72`);
  house codes P/W/E (`:74-78`); sidereal modes 1/3/5 (`:79-82`). The three shipped `.se1` files are SHA-256
  checked at construction (`swisseph.py:76-91`); the image copies only `vendor/swisseph/ephe`
  (`Dockerfile:41`), runs as UID 65532 (`Dockerfile:45`), with `read_only: true`
  (`infra/hetzner/compose.yaml:39,92`).

## Root causes

Severity is as stated by the historical report. "Vendor" = vendor/native input boundary involved.

| RC | Root cause | Entries (scan#) | Sev | Disposition | Evidence (current SHA) | Missing evidence / note |
|---|---|---|---|---|---|---|
| RC-01 | Precision downgrade via supplement edit lowered `profile_level` so later erasure skipped precise snapshots, plans, notes and shares | F1, F2, F3, F8, F29 | med (F29 low) | FIXED | Downgrade without new snapshot now erases: `api/domains/birth/postgres.py:191-193`; removal always erases, no level guard: `:294-295`; erase body `:302-362`; shares cascade from `daily_notes`/`reading_revisions` (`api/domains/share/tables.py:30-39,53-54`). Tests: `tests/birth/test_postgres_encryption.py:257` `test_precision_downgrade_cannot_keep_full_chart_before_or_after_erasure`, `:344` `test_inflight_supplement_cannot_restore_erased_precision` | Share-row deletion is FK cascade; no test asserts a live share token 404s after downgrade+erase |
| RC-02 | Insight routes paired a pre-erasure precise chart with the post-erasure date-only snapshot | F4, F10, F63, F70 | med/low | FIXED | Snapshot+revision read before and after chart, mismatch → `BirthProfileChanged`: `api/api/v1/routes/insights.py:175-182, 249-256`; persist re-checks `source_revision` under guest lock: `api/domains/readings/postgres.py:67-82`. Test: `tests/readings/test_api.py:260` `test_insight_cannot_bind_pre_erasure_chart_to_post_erasure_snapshot` | — |
| RC-03 | Radar accept/private-check read charts outside the erasure fence; pending invite had no recipient ID | F7, F9, F22, F23, F42, F69 | med/low | FIXED | Source revision captured before chart read and re-verified under ordered guest locks: `api/domains/radar/service.py:528-538, 771-797`; create/private paths `:158-159, 277-278`. Tests: `tests/radar/test_flow.py:212` `test_inflight_invite_accept_cannot_save_after_precision_erasure`, `:263` `test_inflight_private_radar_cannot_recreate_result_after_birth_erasure` | — |
| RC-04 | Radar external rewrite authorized by the perspective guest only, though payload derives from both people | F5, F6, F33, F52, F67 | med/low | FIXED | Both subjects resolved and their consents locked at enqueue/send/publish: `api/domains/content_rewrite/authorization.py:96-128, 137-183, 238-256`. Tests: `tests/content_rewrite/test_radar_subject_consent.py:32` `test_radar_requires_both_subjects_before_enqueue_and_execution`; `tests/content_rewrite/test_postgres_concurrency.py:717` *(opt-in PG)* | Radar rewriting cannot currently be enabled (see RC-05) |
| RC-05 | Pilot roster counts only PERSONAL consents; Radar-only guests pass while roster < limit | F19, F55, F56, F64 | low | NOT_APPLICABLE (feature off; defect latent) | Defect still in `api/domains/content_rewrite/authorization.py:192-212` and reused by `is_authorized` `:256`. Unreachable: settings reject any non-off rollout outside `CHART_FREE_REWRITE_SURFACES={"daily_home"}` (`api/config.py:18, 174-182`); worker marks non-rolled-out surfaces DISABLED before authorization (`api/domains/content_rewrite/worker.py:103-111, 415`). Test: `tests/infrastructure/generation/test_openai.py:404` `test_m1_rollout_rejects_surfaces_that_still_send_chart_facts` | Must be fixed before any Radar/Matching/Tarot rewrite rollout. Side note: Radar enqueue is gated only on global `generation_enabled` (`api/domains/radar/service.py:716`), so pair jobs can be stored then marked DISABLED — a minimisation question, not one of the 86 |
| RC-06 | Precision-erasure UI cleanup removed only `daily-note`; private readings, context notes, saved, Radar receipt, card export stayed cached | F12, F35, F37, F66, F75 | low | FIXED (web source) | Central key set incl. `private-reading`, `daily-note-context`, `saved-notes`, `radar-receipt`, `share-artifact`; cancel + remove + reset + revision bump: `web/shared/storage/clearChartDerivedData.ts:8-13, 23-34`; wired at `web/features/profile/ProfilePage.tsx:117-118`. Tests: `web/shared/storage/clearChartDerivedData.test.ts:8` "cancels an old response so it cannot restore an erased private reading", `:22` | Native packaged bundles are gitignored build output (`apps/mobile/ios/.gitignore:4`, `apps/mobile/android/.gitignore:96`); need signed-build provenance that they were rebuilt from ≥ this SHA |
| RC-07 | Legacy Lá Chứng owner result kept in query cache after hide/permanent delete | F17, F47 (+ La Chứng part of F12) | low | **OPEN** | `web/features/la-chung/ResultPage.tsx:21-24` invalidates only `la-chung-invites`; `["la-chung-result", id]` is retained and rendered whenever `query.data` exists (`:40`), incl. after refetch error. Route still mounted (`web/app/router.tsx:93`); owner GET still served (`api/api/v1/routes/la_chung.py:230`) | Reachable only for owners of historical La Chứng rows, same tab, within default gcTime |
| RC-08 | Failed Tarot start stores raw question in `sessionStorage['la-lanh-tarot-start']`; whole-guest deletion did not clear it | F18, F24, F31, F51, F74 | low | FIXED_LOCAL_PR #41 | Deletion path now removes both keys (`web/shared/storage/clearPersonalData.ts:71-72`) but **no test** covers it. Raw question still written on start and kept on failure (`web/features/tarot/TarotPage.tsx:140-151, 233`). PR #41 head `1fb1c83` changes `TarotPage.tsx` and adds `TarotQuestionStorage.test.tsx` | Unmerged; PR content not reviewed in this pass |
| RC-09 | Guest deletion cleared only the current tab's QueryClient | F46 | low | FIXED (web) | Sibling tabs re-verify on `la_lanh_csrf` cookie-marker change (500 ms poll) and storage notice, then clear/redirect: `web/app/SessionBoundary.tsx:94-111`. Tests: `web/app/SessionBoundary.test.tsx:45` "polls a changed cookie without focus or storage events and hides until verified", `:97`, `:109` | `deleteGuest` (`web/shared/api/client.ts:1028-1041`) does not call `announceSessionChange`; relies on server clearing the CSRF cookie. Native WebView cookie behaviour needs device evidence |
| RC-10 | QA proxy re-resolves scheme-relative request target, replacing API origin and forwarding all headers/cookies | F14, F25 | low | **OPEN** | `scripts/qa-server.mjs:154` classifies by pathname of `//host/v1/…`, then `:79-84` `new URL(request.url, apiOrigin)` takes the attacker authority and forwards `request.headers` | Dev/QA tool only, bound to 127.0.0.1 (`:250`); not in production image |
| RC-11 | GCP bootstrap passes DB password on `gcloud` argv | F30 | low | **OPEN** | `infra/gcp/bootstrap.sh:119-123` (`--password` on set-password/create) | Exposure limited to local process observers while the operator runs bootstrap; GCP path is the older beta stack |
| RC-12 | Release privacy preflight opened PostgreSQL without the shared verified-TLS options | F38, F71 | low | FIXED | `apps/api/scripts/check_database_privacy.py:14-16` uses `verified_engine_options`; helper `api/db/session.py:14-31`. Test: `tests/db/test_session.py:8` `test_postgres_cannot_downgrade_server_identity_verification` | Test covers the helper, not that the script calls it |
| RC-13 | Radar creation and owner history unbounded per owner | F34 | low | FIXED | `MAX_RETAINED_REQUESTS=100`, page ≤ 50: `api/domains/radar/service.py:52-54, 297-305, 428-439`. Tests: `tests/radar/test_limits.py:146` `test_combined_capacity_serializes_concurrent_creates_and_delete_frees_space`, `:280` `test_history_pages_are_bounded_and_old_share_does_not_enumerate` | — |
| RC-14 | Resonance clear/withdraw does not take the guest lock used by record; a concurrent write can survive a successful withdrawal | F60 | low | **OPEN** | `api/domains/resonance/postgres.py:128-148` deletes then revokes without `GuestSessionRow ... FOR UPDATE`; `status` reports `last_choice` regardless of consent (`:92-126`). Route mounted without flag (`api/api/v1/routes/daily_notes.py:636-694`) | Self-only race (same guest's concurrent requests); feedback kept ≤ 30 days |
| RC-15 | Guest deletion could finish before a new rewrite send started; jobs had no guest FK | S1 | med | FIXED | DELETING state + captured send fences drained before delete: `api/domains/guest/postgres.py:161-174`; authority requires ACTIVE guest: `api/domains/content_rewrite/authorization.py:172-176`; job FK cascade `api/domains/content_rewrite/tables.py:81-82`. Tests: `tests/content_rewrite/test_postgres_concurrency.py:476` `test_erasure_waits_for_execution_then_fences_stale_worker` *(opt-in PG)*; `tests/content_rewrite/test_execution_fences.py:520` `test_withdrawal_wins_no_provider_or_projection` | — |
| RC-16 | PostgreSQL `ssl=require` without server identity verification | S2 | med | FIXED | `SSLContext` with CERT_REQUIRED + hostname: `api/db/session.py:14-31`; ops URL `verify-full` (`infra/hetzner/configure-database.sh:31`). Tests: `tests/db/test_session.py:8`; `tests/content_rewrite/test_postgres_concurrency.py:505` `test_verified_tls_accepts_test_ca_and_rejects_untrusted_server` *(opt-in PG)* | Live DB URL/CA not inspected |
| RC-17 | Public JSON bodies read and parsed without a size bound | S3 | med | FIXED (app) | `api/middleware/body_limit.py:5-44` (Content-Length + streamed bytes, 1 MiB), installed `api/main.py:357`. Test: `tests/middleware/test_body_limit.py:18` `test_actual_body_bounded_before_parser` | Edge has no `request_body` limit (`infra/hetzner/Caddyfile:17`); defence in depth only |
| RC-18 | Rewrite projectors (Daily, long-form, Radar, Tarot) wrote results after consent withdrawal | S4, S6, S7, S9 | med | FIXED | Projection runs inside a fresh `execution_guard` that re-locks both-subject consent, lease and parent and lends its transaction: `api/domains/content_rewrite/worker.py:187-193`, `api/domains/content_rewrite/postgres.py:69-104`; projectors use the borrowed session (`api/domains/readings/postgres.py:290`, `api/domains/radar/rewrite.py:452`, `api/domains/tarot/rewrite.py:417`); withdrawal drains captured sends (`api/domains/guest/postgres.py:396-431`). Tests: `tests/content_rewrite/test_execution_fences.py:520`, `:547` `test_projection_write_rolled_back_when_finalization_fails`, `:581` `test_reading_projectors_share_atomic_revision_and_publication` | — |
| RC-19 | Precision withdrawal left queued chart-derived rewrite jobs sendable | S5 | med | FIXED | Readings/Radar jobs deleted on removal and in erase: `api/domains/birth/postgres.py:258-275, 337-342`; parent existence locked in guard (`api/domains/content_rewrite/postgres.py:108-130`). Tests: `tests/content_rewrite/test_execution_fences.py:184` `test_precision_withdrawal_erases_both_radar_jobs_and_rejects_late_enqueue`, `:379` `test_obsolete_birth_reading_cannot_send_or_reserve_budget` | — |
| RC-20 | Arbitrary HTTP method tokens created unbounded Prometheus label sets | S8 | med | FIXED | `api/observability/metrics.py:20-26, 55` (allowlist → `OTHER`). Test: `tests/middleware/test_metrics_bounds.py:4` `test_unrecognized_methods_have_one_bounded_label` | — |
| RC-21 | Guest erasure/expiry left decryptable rewrite request envelopes | S10 | low | FIXED | Guest/parent FK cascades `api/domains/content_rewrite/tables.py:81-91`; stale non-leased payload purge after 24 h `api/domains/guest/postgres.py:266-281`. Test: `tests/content_rewrite/test_execution_fences.py:127` `test_expired_leased_payload_erased_without_resend` | Purge timer execution in production is operational evidence |
| RC-22 | Deleting rewrite jobs reset daily spend accounting | S11 | low | FIXED | Owner-independent day/month ledgers: `api/domains/content_rewrite/postgres.py:806-862`, tables `api/domains/content_rewrite/tables.py:12, 34`. Tests: `tests/history/test_retention.py:145` `test_terminal_rewrite_allows_clear_and_keeps_conservative_spend`; `tests/db/test_rewrite_fence_migration.py:5` | — |
| RC-23 | Vendor: blank filename header → backward trim before buffer (`sweph.c:4549-4578`) | F13 | low | NEEDS_EVIDENCE | Reached by bound `swe_calc_ut` → `read_const`, but only with an attacker-crafted `.se1` in the ephemeris dir; shipped files are checksum-verified (see Method) | Vendor. Need: deployed image manifest showing `/app/vendor/swisseph/ephe` holds only the 3 checksummed files, root-owned and read-only; `LA_LANH_SWISSEPH_EPHEMERIS_PATH` not overridden in `app.env` |
| RC-24 | Vendor: CRC staging length allows 1-byte stack overflow (`sweph.c:4757-4779`) | F16 | low | NEEDS_EVIDENCE | Same `read_const` path as RC-23 | Vendor. Same evidence as RC-23 |
| RC-25 | Vendor: ephemeris header object IDs index outside `swed.pldat` (`sweph.c:4798-4855`) | F49 | low | NEEDS_EVIDENCE | Same `read_const` path as RC-23 | Vendor. Same evidence as RC-23 |
| RC-26 | Vendor: file coefficient count `ncoe` unchecked vs `MAXORD+1` (`sweph.c:4814-4827`) | F61, F68 | low | NEEDS_EVIDENCE | Same `read_const` path as RC-23 | Vendor. Same evidence as RC-23 |
| RC-27 | Vendor: optional `swe_deltat.txt` year < 1620 writes before table (`swephlib.c:3097-3120`) | F15, F54, F72 | low | NEEDS_EVIDENCE | Reached via `swe_calc_ut` → delta-T init if that file exists in the ephemeris path; repo ships none (`vendor/swisseph/ephe` = 3 `.se1`) and it is not in the checksum list | Vendor. Same evidence as RC-23, plus confirmation no `swe_deltat.txt` exists in the image |
| RC-28 | Vendor: JPL record/interpolation dimensions exceed fixed buffers (`swejpl.c:322-327`) | F11, F62 | low | NOT_APPLICABLE | JPL path needs `SEFLG_JPLEPH`/`swe_set_jpl_file`; app uses `SEFLG_SWIEPH` only (`swisseph.py:14-17`) | Vendor; latent if flags change |
| RC-29 | Vendor: EOP loader writes past 36525-entry arrays (`sweph.c:1389-1420`) | F26, F32 | low | NOT_APPLICABLE | Only via `swe_set_jpl_file` (not bound, `swisseph.py:101-138`) | Vendor; latent |
| RC-30 | Vendor: EOP rows with < 10 fields dereference NULL (`sweph.c:1403-1418`) | F27 | low | NOT_APPLICABLE | Same as RC-29 | Vendor; latent |
| RC-31 | Vendor: leap-second table terminator written past end (`swedate.c:275-353`) | F48 | low | NOT_APPLICABLE | `swe_utc_*` not bound; app uses `swe_julday` | Vendor; latent |
| RC-32 | Vendor: fixed-star record trimmed before field-count check (`sweph.c:6211-6225`) | F36 | low | NOT_APPLICABLE | `swe_fixstar*` not bound | Vendor; latent |
| RC-33 | Vendor: `swe_vis_limit_mag` strcpy of unbounded name into 256-byte stack (`swehel.c:305-313`) | F20, F39, F65 | low | NOT_APPLICABLE | Heliacal/visibility API not bound | Vendor; latent |
| RC-34 | Vendor: heliacal arc-visibility passes `xaz[2]` to 3-output `swe_azalt` (`swehel.c:2211-2217`) | F40, F45, F73 | low | NOT_APPLICABLE | Heliacal API not bound | Vendor; latent |
| RC-35 | Vendor: heliacal conjunction table indexed before bounds check (`swehel.c:2566-2589`) | F41 | low | NOT_APPLICABLE | Heliacal API not bound | Vendor; latent |
| RC-36 | Vendor: Moon heliacal search ignores failure in unbounded loop (`swehel.c:2143-2167`) | F53 | low | NOT_APPLICABLE | Heliacal API not bound | Vendor; latent |
| RC-37 | Vendor: negative sidereal-mode ID in `swe_get_ayanamsa_name` (`sweph.c:7127-7134`) | F21 | low | NOT_APPLICABLE | Function not bound; `swe_set_sid_mode` receives only 1/3/5 (`engine.py:79-82`) | Vendor; latent |
| RC-38 | Vendor: phenomena/rise use negative `SE_ECL_NUT` as table index (`swecl.c:3875-3898`) | F28 | low | NOT_APPLICABLE | `swe_pheno*`/`swe_rise_trans` not bound | Vendor; latent |
| RC-39 | Vendor: occultation error sprintf overflows 256-byte buffer (`swecl.c:1614-1620`) | F57 | low | NOT_APPLICABLE | Occultation API not bound | Vendor; latent |
| RC-40 | Vendor: Sunshine house validation writes through NULL `serr` (`swehouse.c:648-660`) | F59 | low | NOT_APPLICABLE | `swe_houses_ex` is bound but app passes only P/W/E (`engine.py:74-78`), never Sunshine `I` | Vendor; latent |
| RC-41 | Vendor: empty orbital-elements file formats uninitialised stack text (`swemplan.c:703-756`) | F50 | low | NOT_APPLICABLE | Fictitious bodies (≥ 40) never requested; body IDs fixed (`engine.py:59-72`) | Vendor; latent |
| RC-42 | Vendor: orbital-element parser loops on unsupported character (`swemplan.c:933-965`) | F58 | low | NOT_APPLICABLE | Same as RC-41 | Vendor; latent |
| RC-43 | Vendor: numbered-asteroid header prefix overflows `sastnam` (`sweph.c:4594-4607`) | F43 | low | NOT_APPLICABLE | No numbered asteroid bodies requested (Chiron 15 is in `seas_18.se1`, `engine.py:71`) | Vendor; latent |
| RC-44 | Vendor: Moshier error formats oversized finite JD with `%f` into 256 bytes (`swemplan.c:299-306`) | F44 | low | NOT_APPLICABLE | Needs a huge JD; app JD comes from `swe_julday` of a Python `date` (year ≤ 9999) and Moshier is never selected explicitly | Vendor; latent |

## Entry → root cause (all 86)

"failed" = scan `…_20261008T155125Z_wwcpz3ix` (index numbers 1-75, F*n* above); "scoped" =
`…_20261008T135647Z_pgeahua7` (index numbers 1-11, S*n* above).

| Scan | # | Historical title | Sev | RC | Disposition |
|---|---|---|---|---|---|
| failed | 1 | A partial birth-profile update makes later precision erasure skip stored charts and shares | medium | RC-01 | FIXED |
| failed | 2 | Deleting birth precision after a downgrade leaves precise charts and share links accessible | medium | RC-01 | FIXED |
| failed | 3 | Editing to lower precision makes later erasure retain precise-derived artifacts | medium | RC-01 | FIXED |
| failed | 4 | Reading requests can bind withdrawn precise chart data to the surviving date-only snapshot | medium | RC-02 | FIXED |
| failed | 5 | Radar sends both participants' derived data with only one external consent | medium | RC-04 | FIXED |
| failed | 6 | Radar rewriting sends another participant's derived data without their external-processing consent | medium | RC-04 | FIXED |
| failed | 7 | Concurrent Radar creation can persist erased birth precision | medium | RC-03 | FIXED |
| failed | 8 | Removing precision after an unknown-time update leaves the full birth chart and its artifacts | medium | RC-01 | FIXED |
| failed | 9 | Radar acceptance and private creation can restore withdrawn precision | medium | RC-03 | FIXED |
| failed | 10 | Insights can persist a stale precise chart under the surviving date-only snapshot | low | RC-02 | FIXED |
| failed | 11 | JPL metadata can select a record larger than the native coefficient buffer | low | RC-28 | NOT_APPLICABLE |
| failed | 12 | Deletion leaves private readings and results in the browser query cache | low | RC-06 (La Chứng part → RC-07) | FIXED |
| failed | 13 | Blank filename headers make trimming write before the buffer | low | RC-23 | NEEDS_EVIDENCE |
| failed | 14 | QA proxy lets a request URL replace the configured API origin | low | RC-10 | OPEN |
| failed | 15 | Auxiliary delta-T years permit writes before the table | low | RC-27 | NEEDS_EVIDENCE |
| failed | 16 | CRC staging length permits a one-byte stack overflow | low | RC-24 | NEEDS_EVIDENCE |
| failed | 17 | Deleted La Chứng results remain renderable from the client cache | low | RC-07 | OPEN |
| failed | 18 | Failed Tarot starts retain private questions after whole-guest deletion | low | RC-08 | FIXED_LOCAL_PR #41 |
| failed | 19 | Radar-only consent sessions bypass the paid pilot participant limit | low | RC-05 | NOT_APPLICABLE |
| failed | 20 | Public visibility calculation copies an unbounded object name onto the stack | low | RC-33 | NOT_APPLICABLE |
| failed | 21 | A negative native sidereal-mode ID indexes before the name pointer table | low | RC-37 | NOT_APPLICABLE |
| failed | 22 | Radar can publish precision-derived reports after precision deletion | low | RC-03 | FIXED |
| failed | 23 | Radar can restore precise chart reports after birth-data erasure | low | RC-03 | FIXED |
| failed | 24 | Pending Tarot questions survive personal-data deletion | low | RC-08 | FIXED_LOCAL_PR #41 |
| failed | 25 | A crafted local QA URL can forward the guest cookie to an external host | low | RC-10 | OPEN |
| failed | 26 | Optional EOP parser writes daily records beyond its fixed allocations | low | RC-29 | NOT_APPLICABLE |
| failed | 27 | Incomplete EOP rows dereference absent fields | low | RC-30 | NOT_APPLICABLE |
| failed | 28 | Phenomena and rise APIs accept the negative nutation sentinel as a table index | low | RC-38 | NOT_APPLICABLE |
| failed | 29 | Birth-profile downgrade bypasses deletion of precise derived artifacts | low | RC-01 | FIXED |
| failed | 30 | GCP bootstrap exposes the backend database password in child-process arguments | low | RC-11 | OPEN |
| failed | 31 | Failed Tarot questions survive whole-guest device erasure | low | RC-08 | FIXED_LOCAL_PR #41 |
| failed | 32 | EOP records overflow fixed heap arrays | low | RC-29 | NOT_APPLICABLE |
| failed | 33 | Radar can send another participant's chart evidence without their external consent | low | RC-04 | FIXED |
| failed | 34 | Radar creation and full-history reads have no per-owner resource bound | low | RC-13 | FIXED |
| failed | 35 | Removed birth precision remains in cached readings and can be exported again | low | RC-06 | FIXED |
| failed | 36 | Malformed star records crash before field validation | low | RC-32 | NOT_APPLICABLE |
| failed | 37 | Precision deletion leaves private readings and Radar receipts in client memory | low | RC-06 | FIXED |
| failed | 38 | Database privacy release check bypasses enforced TLS identity verification | low | RC-12 | FIXED |
| failed | 39 | The exported visibility API copies an oversized object name into a fixed stack buffer | low | RC-33 | NOT_APPLICABLE |
| failed | 40 | Heliacal visibility passes a two-double buffer to a three-double writer | low | RC-34 | NOT_APPLICABLE |
| failed | 41 | Heliacal conjunction lookup exceeds its fixed table | low | RC-35 | NOT_APPLICABLE |
| failed | 42 | Radar can persist precise relationship data after precision erasure | low | RC-03 | FIXED |
| failed | 43 | Asteroid header prefix controls an unchecked stack copy | low | RC-43 | NOT_APPLICABLE |
| failed | 44 | Oversized finite Julian dates overflow the Moshier error buffer | low | RC-44 | NOT_APPLICABLE |
| failed | 45 | Arcus-visionis event calculations pass two output doubles to a three-output function | low | RC-34 | NOT_APPLICABLE |
| failed | 46 | Guest deletion does not clear private data already displayed in another tab | low | RC-09 | FIXED |
| failed | 47 | Hidden or permanently deleted Lá Chứng responses remain readable from the client cache | low | RC-07 | OPEN |
| failed | 48 | Leap-second parser writes its terminator past a full native table | low | RC-31 | NOT_APPLICABLE |
| failed | 49 | Ephemeris object IDs index outside native planet state | low | RC-25 | NEEDS_EVIDENCE |
| failed | 50 | Empty orbital-elements files copy uninitialized stack text | low | RC-41 | NOT_APPLICABLE |
| failed | 51 | A failed Tarot question remains on the device after full guest deletion | low | RC-08 | FIXED_LOCAL_PR #41 |
| failed | 52 | External Radar rewriting checks consent for only one participant | low | RC-04 | FIXED |
| failed | 53 | Moon heliacal search ignores failure in an unbounded loop | low | RC-36 | NOT_APPLICABLE |
| failed | 54 | Auxiliary Delta T parser writes before its table for earlier years | low | RC-27 | NEEDS_EVIDENCE |
| failed | 55 | Radar-only opt-ins can consume the paid pilot budget without occupying a pilot slot | low | RC-05 | NOT_APPLICABLE |
| failed | 56 | Radar-only consents bypass the configured pilot participant count | low | RC-05 | NOT_APPLICABLE |
| failed | 57 | Occultation error formatting overflows conventional error buffer | low | RC-39 | NOT_APPLICABLE |
| failed | 58 | Unsupported orbital-element characters leave the parser in a non-progress loop | low | RC-42 | NOT_APPLICABLE |
| failed | 59 | Sunshine house validation writes through omitted error buffer | low | RC-40 | NOT_APPLICABLE |
| failed | 60 | Concurrent resonance feedback can survive successful consent withdrawal | low | RC-14 | OPEN |
| failed | 61 | Swiss ephemeris coefficient counts can overrun the rotation stack array | low | RC-26 | NEEDS_EVIDENCE |
| failed | 62 | Vendored JPL parser trusts dimensions beyond fixed heap buffers | low | RC-28 | NOT_APPLICABLE |
| failed | 63 | Insight requests can recreate erased precision under a date-only snapshot | low | RC-02 | FIXED |
| failed | 64 | Radar-only opt-ins bypass the configured pilot participant limit | low | RC-05 | NOT_APPLICABLE |
| failed | 65 | Visibility API copies unbounded names into its stack buffer | low | RC-33 | NOT_APPLICABLE |
| failed | 66 | Precision erasure leaves deleted private readings and saved snapshots in the browser query cache | low | RC-06 | FIXED |
| failed | 67 | A participant's Radar rewrite can send the other participant's derived facts after their consent withdrawal | low | RC-04 | FIXED |
| failed | 68 | Unchecked coefficient count overflows downstream stack buffers | low | RC-26 | NEEDS_EVIDENCE |
| failed | 69 | An in-flight Radar acceptance can publish a report after birth precision is erased | low | RC-03 | FIXED |
| failed | 70 | An in-flight Insight request can recreate erased precision under a date-only snapshot | low | RC-02 | FIXED |
| failed | 71 | Privacy preflight opens PostgreSQL without the shared identity-verifying TLS policy | low | RC-12 | FIXED |
| failed | 72 | Optional Delta-T file records can write before the native table | low | RC-27 | NEEDS_EVIDENCE |
| failed | 73 | Heliacal calculation undersizes its altitude output buffer | low | RC-34 | NOT_APPLICABLE |
| failed | 74 | Failed Tarot submission leaves the original question on the device after guest deletion | low | RC-08 | FIXED_LOCAL_PR #41 |
| failed | 75 | Precision deletion leaves previously fetched private readings and saved data in the UI cache | low | RC-06 | FIXED |
| scoped | 1 | Guest deletion can complete before a new rewrite provider send starts | medium | RC-15 | FIXED |
| scoped | 2 | Kết nối PostgreSQL yêu cầu TLS nhưng không xác minh danh tính máy chủ | medium | RC-16 | FIXED |
| scoped | 3 | API JSON công khai không giới hạn kích thước body trước khi đọc và parse | medium | RC-17 | FIXED |
| scoped | 4 | Daily rewrite revisions survive cancellation and are published after withdrawal | medium | RC-18 | FIXED |
| scoped | 5 | Precision withdrawal leaves queued chart-derived content eligible for a new provider send | medium | RC-19 | FIXED |
| scoped | 6 | Long-form reading rewrites persist and become available after consent withdrawal | medium | RC-18 | FIXED |
| scoped | 7 | Radar scoped-consent withdrawal does not fence delayed projection writes | medium | RC-18 | FIXED |
| scoped | 8 | HTTP method tùy ý tạo vô hạn nhãn Prometheus trong bộ nhớ | medium | RC-20 | FIXED |
| scoped | 9 | Delayed Tarot rewrites are stored and served after consent withdrawal | medium | RC-18 | FIXED |
| scoped | 10 | Guest erasure and expiry leave reconstructable rewrite requests behind | low | RC-21 | FIXED |
| scoped | 11 | Deleting rewrite jobs resets daily spend accounting | low | RC-22 | FIXED |

## Counts by disposition

| Disposition | Root causes | Retained entries |
|---|---|---|
| FIXED | 16 (RC-01, 02, 03, 04, 06, 09, 12, 13, 15–22) | 40 |
| FIXED_LOCAL_PR | 1 (RC-08 → #41) | 5 |
| OPEN | 4 (RC-07, 10, 11, 14) | 6 |
| NOT_APPLICABLE | 18 (RC-05 latent behind rollout guard; RC-28–44 vendor APIs not bound) | 27 |
| NEEDS_EVIDENCE | 5 (RC-23–27 vendor ephemeris-file parsers) | 8 |
| **Total** | **44** | **86** |

No root cause still OPEN was rated above **low** by the historical report, and none is P0/P1 on current
source review. Every medium-severity entry (failed F1–F9, scoped S1–S9) maps to a FIXED root cause.

## Unresolved and follow-up (for the handoff)

- OPEN, low: RC-07 (La Chứng result cache), RC-10 (QA proxy authority), RC-11 (GCP bootstrap argv
  password), RC-14 (resonance withdraw race / status ignores consent).
- RC-08 depends on merging PR #41; current source has no test for the deletion-path key removal.
- RC-05 must be fixed before enabling any non-`daily_home` rewrite surface.
- NEEDS_EVIDENCE (RC-23–27): deployed image manifest for the ephemeris directory, ownership/read-only
  mount, and `app.env` without an ephemeris-path override. Vendored native bugs remain in source; any new
  FFI binding (heliacal, fixed stars, JPL, UTC helpers, pheno/rise) reopens the matching NOT_APPLICABLE RC.
- Partial-evidence notes: native bundle rebuild provenance (RC-06), native WebView cookie behaviour
  (RC-09), edge body limit (RC-17), live DB TLS URL (RC-16), retention timer execution (RC-21).
- AC/DoD for P03 still incomplete: findings were not re-run as tests in this pass; opt-in PostgreSQL
  tests were not executed; no runtime/native/device evidence was collected.
