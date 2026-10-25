# Feasibility: "Tháng này có gì mới" (monthly feature) — 2026-10-11

Read-only research. No source changed. Event dates were computed with a throwaway local script
that calls the vendored Swiss Ephemeris library (method and receipt in §2; script not committed).
Not legal advice; the legal review is in the companion market doc.

Revision 2026-10-12: addresses review of PR #9. It corrects the guest-storage and retention model,
fixes the Mercury date, separates sky dates from action deadlines, and labels timings and benchmarks
by how far they were verified.

Revision 2026-10-22: the retention model is re-checked against the current target
`collab/integration` @ `c3fab3311d65`, which includes `5f3eded` ("keep automatic Daily notes at most
24 hours", owner decision 2026-10-20). The 2026-10-12 analysis was made against `10695ce4d4c1`; its
other corrections stand. Daily notes and their moods are no longer a 29-day recap input; §3 and the
recap options below are updated. No TTL is extended and nothing monthly is built in this PR.

## Tóm tắt tiếng Việt

- **Tính được, nhưng chưa có sẵn.** Cần bộ giải sự kiện bầu trời (trăng mới/tròn, đứng nghịch/thuận,
  đổi cung) có fixture so với lịch thiên văn tham chiếu. Cần ma trận nội dung mới đã duyệt (direct +
  Roast). Cần quyết định về consent và thời hạn lưu cho recap.
- **Mô hình dữ liệu (đã đối chiếu code):**
  - Máy chủ giữ note ngày, mood, thí nghiệm hành động và tarot theo hồ sơ (`guest_id`, kể cả khách).
  - **Theo target hiện tại (`c3fab3311d65`, cập nhật 22/10):** note ngày tự động bị **ẩn sau 24 giờ**
    và **đủ điều kiện xóa vật lý từ 18 giờ**, xóa ở lần dọn đầu tiên sau đó (6 giờ/lần). Ngoại lệ: note
    hôm nay (giữ tới hết ngày theo giờ VN), note đã lưu, và note còn "con" chưa hết hạn (việc nhỏ chờ
    nhìn lại, phản hồi, link chia sẻ) được giữ ẩn tới khi con hết hạn. Mood có hạn riêng 29 ngày 18 giờ
    nhưng **mất theo cascade khi note cha bị xóa**, nên mood của note không lưu thường mất trong khoảng
    một ngày. Thí nghiệm và tarot vẫn xóa ở 29 ngày 18 giờ.
  - Các quy tắc note/mood chỉ áp dụng khi hồ sơ đã bật chính sách lịch sử; thí nghiệm và tarot luôn có hạn.
  - Thiết bị chỉ có cache bộ nhớ 36 giờ và vài marker, không có kho lịch sử.
  - Câu cũ "không xóa trước 30 ngày" là **sai**. Lời hứa là xóa **chậm nhất** 30 ngày.
- **Note đã lưu** không có hạn xóa tự động: giữ theo vòng đời hồ sơ hoặc tới khi người dùng bỏ lưu.
  Chỉ **mood của note đã lưu, thí nghiệm và tarot** thuộc nhóm 29 ngày 18 giờ (theo điều kiện policy đã
  ghi).
- **Recap:** cửa sổ 29 ngày theo giờ VN (hôm nay + 28 ngày trước) là **phạm vi tổng hợp đề xuất**,
  không phải thời hạn lưu của note đã lưu. Nó dùng được cho dữ liệu còn hợp lệ: note đã lưu (mood của
  chúng tới 29 ngày 18 giờ), thí nghiệm, tarot. Note ngày tự động và
  mood của chúng **không** còn là đầu vào 29 ngày. Phải ghi khoảng ngày thật, loại dữ liệu nào mất sớm,
  ngày thiếu và ngày bắt đầu opt-in. Không coi ngày thiếu là không hoạt động hay mood bằng 0. Không kéo
  dài thời hạn lưu. Hai hướng: endpoint tổng hợp theo hồ sơ, hoặc kho local mới có đủ kiểm soát.
- **Ngày bầu trời khác hạn chót:** Sao Thủy đứng nghịch 24/10 và **đứng thuận 13/11 lúc 22:53 giờ VN**;
  14/11 là Sao Kim. Giờ trăng mới/tròn khớp bảng của Espenak trong vòng 1 phút. Giờ đứng của hành tinh
  lệch vài phút giữa các nguồn, nên chỉ hiển thị ngày. Số đo 9 ms/29 ms là thử nghiệm một máy, không
  phải cam kết hiệu năng hay chi phí.

**Verdict:** Feasible, but not covered by the repo today. It needs:
- a sky-event solver with almanac fixtures;
- an exact-date contact solver (only if personal transit windows are wanted later);
- a new reviewed content matrix (direct + Roast);
- a privacy decision on recap inputs.

Automatic Daily notes become purge-eligible 18 h after creation (hidden at 24 h) and their moods
cascade with them. Saved notes have no purge window: they stay for the profile's lifetime or until
the user unsaves them. The moods of saved notes, experiments and tarot become purge-eligible at
29 d 18 h. So a calendar-month recap cannot be built from raw inputs, and Daily/mood history is not a
29-day input. The 29-day recap window is a proposed aggregation range, not a TTL of saved notes. The main product risk is the conflict between the old PRD's "deadline/timing" framing and
the newer no-prediction gates.

**Open AC/DoD:**
- No user story, AC or DoD exists for a monthly feature. The owner must choose the direction first.
- PRD F3.1 and the SRS `/transit-insights` endpoints are unimplemented.
- The owner must rewrite Rule 3 and the product-plan example (date contract in §1).
- A retention and consent decision is needed for any recap aggregate.
- Store and privacy-copy updates are needed if anything new is persisted or tracked.

## 1. Product contract

### What the docs already ask for
- PRD v0.3 F3.1 Transit Engine (house mapping): slow transits read "theo tháng/năm". Each transit
  insight must show start and end dates ("Quy tắc 3 — deadline"). Level 1–2 users get an
  upgrade invite instead of an insight. `docs/foundation/la-lanh-prd.md:551-604`. Data model
  `TransitEvent.transit_type` includes `house_ingress`, `retrograde_start`, `retrograde_end` and
  `aspect` (`:577`). House system for this automatic feature is Whole Sign (`:601`).
- PRD Daily: "tại sao hôm nay/tháng này tôi cảm thấy vậy" → Transit read on top of Natal, never
  on its own (`la-lanh-prd.md:55`). Fast and slow transits must not share a template (`:228`, `:559`).
- Product plan v2: Rule 3 "Gắn với thời điểm thật, có deadline cụ thể"
  (`docs/foundation/la-lanh-product-plan-v2.md:268-274`). Its example *"New Moon tháng này rơi vào
  House 10 … thời điểm tốt để nộp đơn"* (`:224`) and the month-3 focus "tại sao tháng này lại như vậy"
  (`:337`). Mercury Rx by house is named as a key engine investment (`:332`).
- SRS: `computeUserTransitImpact`, `GET /transit-insights`, `POST /transit-insights/{id}/forward
  {targetContact}`, and a daily "Transit Event Detection" job (`docs/foundation/la-lanh-srs.md:87-88,
  516-517, 594-598`). Transit insight cache per house × slow transit (`:249`). **None of this is
  implemented.** grep finds no `transit-insights` route.
- PRD v0.6 F6.1 Season Recap: a recap every 6 weeks, "Wrapped-style", with a basic version for all
  users (`la-lanh-prd.md:1192-1210`). This is the nearest documented recap concept. There is no
  monthly recap.
- Astro engine spec: transit user impact should include "ingress, station and retrograde
  multi-pass windows", "exact-hit times", and "start/peak/end based on actual orb crossings"
  (`docs/foundation/la-lanh-astro-engine-spec.md:218-225`). Event boundaries must use bracketed
  root-finding, and sampling cannot prove absence (`:256`). Station and multi-pass fixtures are
  required (`:363`).

### Constraints that override the old framing
- Content standard: no fatalism and no "dự đoán chắc chắn về sự việc"
  (`docs/foundation/la-lanh-plain-vietnamese-content-standard.md:33`). Evidence, disclaimer and
  provenance stay unchanged (`:36`).
- Daily engine: a transit keeps planet, aspect, orb and phase from the canonical claim. It must not
  be turned into "một câu dự báo chuyện đời thường"
  (`docs/foundation/daily-psychology-scene-advice-engine.md:105`). No diagnosis, fate or high-stakes
  advice (`:129`).
- Reading knowledge spec: retrograde stays in the evidence and produces no psychological conclusion
  by itself. Applying/separating is never framed as weak, bad or fate
  (`docs/foundation/la-lanh-reading-knowledge-spec.md:93`; same rule in
  `la-lanh-interpretation-corpus-methodology.md:55`). At most one prominent transit per reading
  (`:126`). Content publishes only after the evidence, anti-influence, editorial, meaning and
  privacy gates (`:156`). Provenance must be traceable (`:185`). The disclaimer is always shown (`:198`).
- Content-matrix release gate: "current transit phase … without event prediction"
  (`docs/operations/content-matrix-release-gate.md:122`). New dimensions need a versioned method,
  evidence mapping and privacy review. They must not use certain predictions
  (`:130-136`). A published action needs inspectable chart evidence
  (`docs/operations/user-experience-release-gate.md:12`).
- **Gap to record:** product-plan-v2:224 ("thời điểm tốt để nộp đơn") and Rule 3's urgency framing
  (`:268-274`, including "kéo dài đến tháng 8/2026" attached to a relationship claim) break the
  current no-prediction gates.
- **Proposed date contract.** The owner must adopt it, updating Rule 3 and the `:224` example, before
  implementation. A UI disclaimer is not a substitute.
  - An **astronomical event date** is kept. It covers the instant a lunation, station or ingress
    happens, or the computed start and end of a transit window. It is stored as a UTC instant with
    provenance (engine, version, flags), shown in ICT with the timezone stated, at a stated precision
    (§2). Example: "Sao Thủy đứng nghịch ngày 24/10 và đứng thuận ngày 13/11 (giờ Việt Nam)".
  - It is **never** turned into:
    - a good or bad time;
    - a deadline for life matters ("trước 13/11 hãy…");
    - a statement of how long a life situation lasts;
    - a forecast that emotions will rise or fall;
    - an inference about communication or relationship timing from a station or retrograde.
  - It may carry one optional, evidence-bound reflective prompt.
- Privacy baseline: Law 91/2025/QH15 and Decree 356/2025/NĐ-CP have applied since 2026-01-01
  (`docs/legal/privacy-security-flow-notes.md:5`). Derived chart and transit factors are personal
  data in the store maps (`docs/legal/store-privacy-data-map.md:45,61`). Mood and note prose are
  banned from matching and ranking (`privacy-security-flow-notes.md:76`). The `forwarded_to_contact`
  / `targetContact` field in the PRD/SRS (`la-lanh-prd.md` F3.1 model; `la-lanh-srs.md:517`) would
  collect third-party contact data. Drop it and use the existing share-link pattern.

## 2. Engine capability

Existing pieces (`apps/api/app/domains/astro/`):

| Function | What it gives | Monthly use |
|---|---|---|
| `NatalChartEngine.calculate_daily_transit(date, config)` `engine.py:279` | 12 bodies at 12:00 UTC with speed and `retrograde` flag | One snapshot per day. No event times. |
| `calculate_transit_to_natal(natal, observed_at)` `engine.py:303-370` | Contacts at one instant: body, kind, orb, phase (approaching/exact ≤0.2°/separating via +1h sample `:609-619`) | Point-in-time only. No exact-hit time, no window, no multi-pass. |
| `_transiting_bodies` `engine.py:372` | LRU cache (256) of non-personal sky positions | Reusable for a global month grid. |
| `SwissEphemerisNative.calculate` `ffi/swisseph.py:166` | `swe_calc_ut` + speed | Enough to build lunation, station and ingress solvers. |
| `sign_for_longitude`, `angular_distance`, `transit_orb_limit` `aspects.py:16` | helpers | reuse |

**Missing:**
1. A sky-event solver for lunations (Sun–Moon elongation 0°/180°), stations (speed = 0) and sign
   ingresses, including retrograde re-entries. It should use bracketed root-finding as the spec
   requires, with fixtures against a reference almanac.
2. Eclipses. The FFI binds only `swe_calc_ut`, `swe_houses_ex`, `swe_julday` and `swe_version`
   (`ffi/swisseph.py:100-139`). A locally built `libswe.dylib` exports `swe_sol_eclipse_when_glob`,
   `swe_lun_eclipse_when`, `swe_solcross_ut` and `swe_mooncross_ut` (checked with `nm`). That a
   symbol exists does **not** mean a solver is verified. Eclipses need:
   - a binding and wrapper;
   - classification and visibility rules;
   - fixtures against a published eclipse catalogue;
   - updated release evidence under `docs/legal/swiss-ephemeris-release-gate.md` (version, checksums,
     tests).
   Eclipses are out of scope for v1. None fall in Oct–Nov 2026. Dates from an earlier one-off call
   (Aug 2026, Feb 2027) were not verified and are not used here.
3. An exact-date transit-to-natal solver: hit times, enter/exit orb windows, and Mercury/Venus Rx
   multi-pass (up to 3 hits). There is also no lunation-to-natal-house mapping. That needs
   `house_for_longitude` (`engine.py:634`) and is limited to `TimePrecision.EXACT` charts, as
   Sky Chapter does (`apps/api/app/domains/daily/service.py:358`). Date-only charts get no houses
   and no substitute houses.
4. Persistence and API: no `TransitEvent`, `UserTransitInsight` or `/transit-insights` exists.

### Sky events, Oct–Nov 2026 (experiment with receipt)

| Instant (ICT, UTC+7) | Event | Display precision |
|---|---|---|
| 2026-10-03 14:16 | Venus stations retrograde, 8°29′ Scorpio | day |
| 2026-10-10 22:50 | **New Moon**, 17°22′ Libra | minute |
| 2026-10-16 09:40 | Pluto stations direct, 3°04′ Aquarius | day (sources disagree on the date; see below) |
| 2026-10-23 16:38 | Sun → Scorpio | minute* |
| 2026-10-24 14:12 | **Mercury stations retrograde**, 20°59′ Scorpio | day |
| 2026-10-25 16:09 | Venus (Rx) re-enters Libra | minute |
| 2026-10-26 11:11 | **Full Moon**, 2°46′ Taurus | minute |
| 2026-11-09 14:02 | **New Moon**, 16°53′ Scorpio | minute |
| 2026-11-13 22:53 | **Mercury stations direct**, 5°02′ Scorpio | day |
| 2026-11-14 07:27 | Venus stations direct, 22°52′ Libra | day |
| 2026-11-22 14:23 | Sun → Sagittarius | minute* |
| 2026-11-24 21:53 | **Full Moon**, 2°20′ Gemini | minute |
| 2026-11-26 06:37 | Mars → Virgo | minute |

*Sun ingresses differ by about 8 minutes from the secondary table checked (see below).

Mercury stations direct on **13/11 at 22:53 ICT**. The 14/11 date belongs to Venus. The earlier
example "thuận 14/11" was wrong and has been corrected in §1. An event near midnight can change
calendar date between timezones, so the UI must always say "giờ Việt Nam".

**Receipt (reproducible method; the script itself is a local scratch file and was not committed):**
- Library: Swiss Ephemeris `swe_version` 2.10.03, built from `vendor/swisseph` (`make -C
  vendor/swisseph`). Ephemeris files `sepl_18.se1`, `semo_18.se1` and `seas_18.se1`, with checksums
  pinned in `ffi/swisseph.py`.
- Call: `swe_calc_ut` with `SEFLG_SWIEPH | SEFLG_SPEED` (258), the engine's flags. That gives
  tropical, geocentric, apparent positions. The call fails if the result is not from the Swiss
  Ephemeris files.
- Method:
  - Scan 2026-10-01 to 2026-12-01 UT in 6-hour steps.
  - Detect sign changes of: Moon − Sun elongation (0° and 180°); longitude speed (stations of
    Mercury, Venus, Mars and Pluto); and distance to the nearest 30° boundary (ingresses of Sun,
    Mercury, Venus and Mars).
  - Refine each bracket by bisection to a 1-second tolerance.
  - Convert UT to ICT by adding 7 hours. UT1 − UTC is under 1 s and is ignored.
- Environment: Apple Silicon (arm64), macOS 26.5, system Python 3.9 with `ctypes`, 2026-10-12. Not
  the production image.
- Reference checks (done online on 2026-10-12):
  - **Lunations:** all four match F. Espenak's *Phases of the Moon 2001–2100* table (UT, to the
    minute) within 1 minute: https://astropixels.com/ephemeris/phasescat/phases2001.html.
  - **Mercury stations:**
    - The Natal Echo 2026 table (secondary, own engine) gives 07:15 UTC on 24/10 and 15:52 UTC on
      13/11. Ours are 07:12 and 15:53.
      https://natalecho.com/learn/astrology/2026-planetary-ingress-dates-ephemeris
    - A search-result excerpt of Drik Panchang gives the same dates, at 07:11 and 15:52 UTC. The page
      itself was behind a login wall from Vietnam and was not read.
  - **Other events:** the same secondary table agrees within 1–5 minutes on the Venus station and
    re-entry and the Mars ingress. It is about 8 minutes earlier on both Sun ingresses. A difference
    that size and consistency fits a different position convention, for example omitting annual
    aberration; this is an inference, not checked. It lists the Pluto station on 15/10 UTC; ours is
    16/10 02:40 UTC.
  - The official USNO API was unreachable (connection reset). **No official almanac was checked
    for stations or ingresses.**
- **Precision contract that follows:**
  - Show lunations and ingresses at minute precision only after fixture tests pass against a named
    reference.
  - Show stations at **day** precision. A planet's speed is near zero around a station, so the
    instant is poorly defined and sources differ by minutes (by a day for Pluto).
  - Store the UTC instant, engine version and flags with every event as provenance.

**Cost (unverified experiments, not latency or cost guarantees):**
- Global scan:
  - The first pass took about 3,300 `swe_calc_ut` calls and about 9 ms.
  - The receipt run above took 4,966 calls and about 13 ms at a 6-hour step.
  - Both were single runs on one laptop.
- Per-user sweep:
  - `calculate_transit_to_natal` every 6 hours (120 snapshots) on a fictional chart took about 29 ms
    per user-month in one run.
  - It was not re-run for this revision. It has no recorded script, repetitions or variance.
- Native calls are serialised behind one `RLock` (`ffi/swisseph.py:50`), so batch work for many users
  is CPU-serial. Measure on the production image before making any capacity or cost claim.
- Compute global events once a month and put only that non-personal list in a shared cache, keyed by
  month and engine version. Compute the user overlay on request, the same way Sky Chapter does.
  Don't store it or shared-cache it.
- The 6-hourly sweep catches only the minimum orb. Real exact times and multi-pass hits need the
  new solver. The sweep also surfaces generational noise (for example Neptune sextile natal
  Neptune), so a salience filter is needed.

## 3. User data available for a month recap (one data model, verified in code)

### Server-side, per owner
Everything in the table is stored on the server and keyed by `guest_id`. Guests have a
`guest_sessions` row too. Signed-in accounts keep the same owner. The server is not only where
charts are computed.

| Data | Table | Useful fields | Retention |
|---|---|---|---|
| Daily notes | `daily_notes` (`apps/api/app/domains/daily/tables.py:12-36`) | `note_date`, `context_label`, `persona_mode` | **Target `c3fab3311d65`:** automatic past-day notes are hidden 24 h after `created_at` and eligible for physical purge from 18 h, deleted at the first 6-hourly cleanup after that (`DAILY_HISTORY_WINDOW`, `DAILY_PURGE_WINDOW`, `apps/api/app/domains/history/postgres.py:38-45`). Exempt: today's note until the local ICT day ends (`note_date < today`, `:121-124`), saved notes (`saved_daily_source`), and notes with a live child — unexpired experiment, resonance feedback or unrevoked share — kept hidden until the child expires (`live_daily_children`, `:83-106`, applied at `:279-281`). An owner's rewrite send fence can defer a run. Daily projections and plans follow the same windows. Applies only under the `history-retention-v1` policy (row created after activation, or activation ≥ 30 d ago). Physical deletion is not a proven 24 h bound. |
| Saved notes | `saved_notes` (`saved/tables.py:13-49`) | snapshots, `saved_at` | No automatic purge: kept for the profile's lifetime (cascade on profile deletion) or until the user unsaves (`routes/saved_notes.py:173-178`). Not in the cleanup list (`history/postgres.py:290-296` on target); protects its source Daily note through `saved_daily_source` (`:109-118`). |
| Mood | `mood_check_ins` (`mood/tables.py:12-22`), one per note | 5 moods (`mood/models.py:7-12`), `checked_in_at` | Own window unchanged: 29 d 18 h physical purge under the policy (`history/postgres.py:282-283`). But `daily_note_id` is `ON DELETE CASCADE` (`mood/tables.py:22`), so a mood **goes with its Daily note**: for an unsaved note that is usually within about a day. Saving the note keeps the note, and its mood until the mood's own 29 d 18 h point. |
| Experiments | `daily_experiments` (`experiments/tables.py:22-70`) | `state` chosen/reflected; outcome `not_tried`/`helpful`/`no_difference`/`not_for_now` (`experiments/models.py:14-18`), encrypted payload | `expires_at` = creation + 29 d 18 h for every owner (`experiments/service.py:15,49`) |
| Tarot sessions | `tarot_sessions` (`tarot/tables.py:12-33`) | `context`, `spread`, `voice`, encrypted payload | `expires_at` = creation + 29 d 18 h for every owner (`tarot/service.py:50,156`) |
| Daily-note views | not recorded | — | — |

**Policy coverage:**
- New web guests are created with `history_consent_version: "history-retention-v1"`
  (`apps/web/src/shared/api/client.ts:668`), so the policy starts at creation.
- Older profiles can opt in from Mình. Their pre-existing rows get 30 days from activation.
- Owners without the policy keep daily notes and moods until the profile itself expires. Experiments
  and tarot expire regardless.

**Profile lifetime:**
- Guest: 30 days of inactivity, extended by valid private use (`apps/api/app/config.py:39`,
  `guest/service.py:132`).
- Account owner: 365 days; each device session: 30 days (`accounts/models.py:8-9`).
- Expired profiles are deleted by the guest-cleanup job.

**Purge timing:**
- `scripts/cleanup_expired` drains eligible rows in owner-locked batches.
- It runs every 6 hours:
  - Hetzner: `infra/hetzner/systemd/la-lanh-expired-cleanup.timer`, at 00/06/12/18:40 with up to
    5 minutes of random delay;
  - GCP: `infra/gcp/deploy.sh:182-183`, `40 */6 * * *`.
- The runbook alerts if no cleanup has succeeded for 6 hours
  (`docs/operations/aura-experiment-retention-runbook.md`).
- So with a healthy scheduler, a saved-note mood, experiment or tarot row is deleted between 29 d 18 h
  and about 30 d after creation; an automatic Daily note (and its mood) between 18 h and roughly a day
  after creation, unless an exemption above applies. The user-facing copy on the target says automatic
  Daily notes show for at most 24 h with that day's mood and may be deleted earlier; other history is
  kept at most 30 days (`apps/web/src/features/consent/ConsentPage.tsx:74`).

**Correction (2026-10-12, still valid for the 29 d 18 h data).** The earlier line "nothing is deleted before 30 days" was wrong. Rows become
deletable at 29 d 18 h and are normally gone before day 30. The 6-hour margin exists to keep the
"no later than 30 days" promise. It is not a guarantee that 30 × 24 h are kept. Between 29 d 18 h
and 30 d, whether a row still exists depends on cleanup timing.

### On the device (web and the Capacitor app, which runs the same web code)
| Item | Storage | Content and lifetime |
|---|---|---|
| Daily-note cache | memory only (`apps/web/src/shared/storage/noteCache.ts:4-19`) | Current note, 36 h. Dropped on session, epoch or cookie change. |
| Saved-note sync markers | `localStorage` `la-lanh-saved-notes-v1` (`savedNoteCache.ts:3-18`) | Note id, revision id, `saved_at`; ≤ 30 items, ≤ 30 days; no prose |
| Pending mood | `localStorage` `la-lanh-pending-mood-v1` (`features/home/HomePage.tsx:210-235`) | One unsynced (note id, mood) pair until the next successful sync |
| Companion growth | `localStorage` (`shared/ui/companion/growth.ts:1-8,127-141`) | Random seed, capped count of distinct visit days, last day; no per-day history |
| Tarot and ritual keys | `sessionStorage` / `localStorage` flags | Idempotency and dismissal markers only |

**There is no device-side history store.** "On-device-first" recap is not an existing capability.
It would mean building a new store.

### Read endpoints
- `GET /v1/saved-notes` is the only list endpoint (`routes/saved_notes.py:108`).
- Notes, mood, experiments and tarot can be read only for today, the current item, or a known id.

### Recap options (choose one; both need the owner's decision and new AC)
1. **Owner-scoped aggregate endpoint** over rows still allowed to be kept, computed at request time:
   - authenticated owner only;
   - CSRF rules as for other owner reads;
   - `Cache-Control: no-store`;
   - no new persisted artifact;
   - not sent to any rewrite provider.
   The safe window is **today plus the previous 28 ICT dates (29 dates)** for data still kept that
   long: saved notes (and their moods up to 29 d 18 h), experiments and tarot. Its oldest possible row
   is at most 29 days old, inside the 29 d 18 h point. Automatic Daily notes and their moods are **not**
   available across that window on the current target; a recap may only say which kinds were kept and
   must not infer activity or mood from their absence. Mood is biased towards saved notes. Persisting an aggregate beyond that is a
   separate, new derived dataset. It would need separate consent, its own retention, deletion on
   withdrawal or profile deletion, export, and store-declaration updates.
2. **New local store** for recap inputs or results. It needs:
   - a retention limit;
   - a user delete control;
   - clearing on logout and on profile or guest change;
   - partitioning by profile on shared devices;
   - exclusion from OS backups in the Capacitor app;
   - privacy copy and store declarations, if anything is sent or synced.

**Rules for both options:**
- The recap states its actual covered range, the days with no data and the opt-in start date. A
  recap that started on 20/10 covers 20/10 onward, not "30 ngày qua".
- Missing data is never shown as zero activity or neutral or low mood.
- No retention window is extended quietly to make a calendar month fit.

## 4. UI entry points and weekly recap

**How `WeekRecap` works today** (`apps/web/src/features/home/HomeRituals.tsx:44-67`, rendered at
`features/home/HomePage.tsx:339`)
- It is client-only and shows only on Sundays (`now.getDay() === 0`).
- It fetches `GET /saved-notes` and filters `saved_at` to a rolling 7×24 h window.
- It shows "Tuần này bạn giữ lại {n} note." with a CTA to `/saved`.
- It renders nothing when the count is 0.
- It uses saved notes only: no mood, experiments or tarot.

**US-18** "recap chủ nhật" is unrelated: it covers the Vòng Lá pool recap and has been
**DEFERRED** since 2026-09-20 (`docs/user-stories/US-18-xem-chia-se-recap-chu-nhat.md:3`). Its
tone and privacy principles are a reference only; its AC are not AC for a monthly feature.

**Candidate entry points**
1. **Home**, next to `<WeekRecap />` (`HomePage.tsx:339`), as a "Tháng này" ritual card shown in the
   first days of the month or at a lunation. Another option is a third tile in
   `HomeExploreRoutes` (`HomePage.tsx:502-517`, currently Tarot and Radar).
2. **Khám phá** (`/insights`). It already has `/insights/current-sky`, backed by
   `GET current-sky` → `calculate_daily_transit` (`apps/api/app/api/v1/routes/insights.py:290-320`).
   This is the most natural home for the global "sky this month" calendar.
3. **Mình** (`apps/web/src/features/profile/ProfilePage.tsx`): the shortcuts nav (:165-166) and the
   "Lịch sử, không phải hồ sơ" history section (:198-204). These fit a personal recap and its
   retention controls.

Tabs are `/home`, `/insights`, `/radar` and `/profile` (`apps/web/src/shared/ui/AppNav.tsx:4-9`).

## 5. Risks

- **No-prediction gate.** A lunation-or-Rx "what's coming" list drifts into forecasting quickly.
  Mitigation:
  - Adopt the date contract (§1) before implementation.
  - Show sky facts with dates plus at most one evidence-bound reflective prompt per event.
  - Never write "nên/không nên ký, nộp đơn, tỏ tình". Never infer communication or relationship
    timing from a station or retrograde.
  - Keep the disclaimer next to the content. It does not license predictive copy.
  - The retrograde copy must not imply a bad period (reading-knowledge-spec:93).
  - The Meaning Gate must reject event certainty.
- **Privacy** (legal text and inferences are in the market doc §4):
  - A per-user month view combines derived transit-to-natal contacts, natal houses and, for a recap,
    mood, notes and experiment outcomes. That is new derived personal data. Usage aggregates are
    likely behaviour/service-use tracking data under Decree 356 Art. 4(1)(l). Aggregates linked to
    an owner are not de-identified (Law 91 Art. 2(11)).
  - The recap needs its own purpose-specific consent, separate from share consent. It needs
    withdrawal that stops aggregation and deletes any stored recap. It needs owner-scoped access
    controls (Decree 356 Art. 4(2)).
  - Compute on the fly and don't persist (option 1 in §3). Never send mood, notes or intention text
    to the external rewrite provider (store-privacy-data-map:11).
  - Update Apple App Privacy, Google Play Data Safety, in-app privacy copy and the privacy policy if
    a new stored artifact or tracked event appears.
  - A shareable monthly card is off by default, previewed and editable, and excludes mood, notes and
    intention text. It follows the share-link rules in AGENTS.md: no-store, noindex, no-referrer,
    tokens out of logs, revocable. Copy states that screenshots cannot be revoked.
- **Intention text** (concept C): profile-scoped. It has a stated retention (expires after the
  look-back), delete and withdraw controls, and clearing on logout or profile change on shared
  devices. It is never sent to providers, never used in analytics or matching, and does not invite
  naming third parties.
- **Retention vs recap window.**
  - Saved-note moods, experiments and tarot become deletable at 29 d 18 h; automatic Daily notes and
    their moods from 18 h (§3).
  - A recap label must show the real covered range and which data kinds it covers. The safe rolling
    window is 29 ICT dates for the kinds still kept that long. A
    "30 ngày qua" label without stated dates would overstate what is kept.
  - Persisting a minimised aggregate beyond the window is new derived data. It needs separate
    affirmative consent, its own retention, deletion and export, and store-declaration updates.
  - Recommendation: read-time aggregate within the window. Do not extend the windows quietly.
- **Content volume** (Vietnamese, reviewed, direct + Roast):
  - Global events: about 12 lunations per year × 12 signs, roughly 24 lunation meanings plus
    sign framing.
  - Station copy: Mercury, Venus and Mars Rx/direct, about 6 base meanings × 12 signs.
  - Ingress copy: Sun, Mercury, Venus and Mars, sign framing only.
  - Personal house layer (EXACT only): lunation × 12 houses (24 to 36 atoms) and Rx × 12 houses.
  - Minimum viable set: **about 60 to 100 new reviewed atoms**, each needing a scene, a bounded
    action and evidence refs. Then double that for Roast.
- **Roast voice mapping:**
  - The Daily Roast layer matches only exact approved direct text. Anything not authored there
    stays direct (`apps/api/app/domains/readings/voice.py:1-16`; content standard:52-54).
  - New monthly lines need their own Roast frames and owner re-approval ("Câu mới hoặc sửa nghĩa
    phải duyệt lại", content standard:62-63).
  - The voice must self-soften for body/rest themes. Saved and shared snapshots stay direct.
  - The work must pass `pnpm content:review` with its Roast pass.
- **Precision tiers:**
  - v1 starts from shared sky events that need no birth data.
  - The house overlay needs an EXACT birth time. Without it there are no houses and no substitute
    houses, such as whole-sign-from-Sun.
  - Date-only users get the global sky and sign-level framing only (PRD F3.1 Level 1–2 rule).
  - Avoid Sun-sign-only "horoscope" text, because it fails Rule 2's >30% specificity test
    (product-plan-v2:262-266).
- **Engine correctness.**
  - Station and ingress solvers need fixture tests against a named reference almanac (engine
    spec:363), with the tolerances and display precision from §2.
  - Eclipse support needs a verified solver and updated Swiss Ephemeris release evidence
    (`docs/legal/swiss-ephemeris-release-gate.md`). It is not a binding-only change.
- **Measurement.** First measure usefulness and understanding: an optional one-tap check, and that
  users do not read the card as a prediction. Only then look at return rate. Analytics events carry
  no content and are themselves usage-tracking data.

## Sources checked, findings fixed, unresolved (handoff)

- **Code checked:**
  - `apps/api/app/domains/{history,experiments,tarot,mood,guest,accounts}`;
  - `apps/api/scripts/cleanup_expired.py`;
  - `infra/hetzner/systemd/*cleanup.timer` and `infra/gcp/deploy.sh`;
  - `apps/web/src/shared/storage/*`, `features/home/HomePage.tsx`, `shared/ui/companion/growth.ts`,
    `features/consent/ConsentPage.tsx`;
  - `apps/mobile` (Capacitor shell; no separate native store found at the top level).
- **Primary sources checked:**
  - Law 91/2025 pp. 2, 6–7 and Decree 356/2025 pp. 2–3 (signed scans, read visually);
  - VBHN 88/VBHN-VPQH p. 6;
  - Decree 87/2026/NĐ-CP full text on vbpl.vn;
  - Dai, Milkman & Riis 2014 full text;
  - TechCrunch on Wrapped 2025;
  - Espenak lunation table.
- **Fixed:**
  - guest storage model and purge timing;
  - the "not deleted before 30 days" error;
  - the Mercury direct date (13/11, not 14/11);
  - timings and benchmarks labelled by verification level;
  - eclipse scope;
  - the date contract.
- **Unresolved:**
  - no official almanac checked for stations and ingresses;
  - the 29 ms per-user figure was not re-run;
  - Sun-ingress difference against the secondary table not explained by test;
  - legal items marked [counsel] in the market doc;
  - no US/AC/DoD for any monthly feature.
