# Feasibility: "Tháng này có gì mới" (monthly feature) — 2026-10-11

Read-only research. No source changed. Event dates were computed with throwaway local scripts using the existing engine primitives (not committed).

**Verdict:** Feasible. The sky events are cheap to compute, but the work in the repo today doesn't cover the
feature. It needs a new event solver, an exact-date contact solver, a new reviewed content matrix
(direct + Roast), and a privacy decision on how long recap inputs are kept. Raw inputs are purged
at 29 d 18 h, so a calendar-month recap can't be built from them. The main product risk is the
conflict between the old PRD's "deadline/timing" framing and the newer no-prediction gates.

**Open AC/DoD:**
- No user story, AC or DoD exists for a monthly feature.
- PRD F3.1 and the SRS `/transit-insights` endpoints are unimplemented.
- A no-prediction rewrite of Rule 3 is needed.
- A retention and consent decision is needed for any recap aggregate.
- Store and privacy-copy updates are needed if anything new is persisted.

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
  break the current no-prediction gates. A monthly feature must reframe dates as *sky facts with
  exact dates* (for example "Sao Thủy đứng nghịch 24/10 → thuận 14/11"). It can add an optional
  reflective prompt. It must never say "good time to X".
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
   ingresses, including retrograde re-entries. It should use bracketed root-finding as the spec requires.
2. Eclipses. The FFI binds only `swe_calc_ut`, `swe_houses_ex`, `swe_julday` and `swe_version`
   (`ffi/swisseph.py:100-139`). The bundled `libswe.dylib` exports `swe_sol_eclipse_when_glob`,
   `swe_lun_eclipse_when`, `swe_solcross_ut` and `swe_mooncross_ut`. Adding them is a small
   binding change, but it would need new checksum, test and release-gate entries.
3. An exact-date transit-to-natal solver: hit times, enter/exit orb windows, and Mercury/Venus Rx
   multi-pass (up to 3 hits). There is also no lunation-to-natal-house mapping. That needs
   `house_for_longitude` (`engine.py:634`) and is limited to `TimePrecision.EXACT` charts, as
   Sky Chapter does (`apps/api/app/domains/daily/service.py:358`).
4. Persistence and API: no `TransitEvent`, `UserTransitInsight` or `/transit-insights` exists.

**Computed with existing primitives** (Western tropical, times in ICT; spot-checked against
published almanac dates):

| Date (ICT) | Event |
|---|---|
| 2026-10-03 14:16 | Venus stations retrograde, 8°29′ Scorpio |
| 2026-10-10 22:50 | **New Moon**, 17°22′ Libra |
| 2026-10-16 09:40 | Pluto stations direct, 3°04′ Aquarius |
| 2026-10-23 16:38 | Sun → Scorpio |
| 2026-10-24 14:12 | **Mercury stations retrograde**, 20°59′ Scorpio |
| 2026-10-25 16:09 | Venus (Rx) re-enters Libra |
| 2026-10-26 11:11 | **Full Moon**, 2°46′ Taurus |
| 2026-11-09 14:02 | **New Moon**, 16°53′ Scorpio |
| 2026-11-13 22:53 | **Mercury stations direct**, 5°02′ Scorpio |
| 2026-11-14 07:27 | Venus stations direct, 22°52′ Libra |
| 2026-11-22 14:23 | Sun → Sagittarius |
| 2026-11-24 21:53 | **Full Moon**, 2°20′ Gemini |
| 2026-11-26 06:36 | Mars → Virgo |

There are no eclipses in Oct–Nov 2026. A scratch call to the library found solar eclipses on
2026-08-13 00:45 ICT and 2027-02-06, and lunar eclipses on 2026-08-28 and 2027-02-21.

**Cost:**
- The global 2-month event scan took about 3,300 `swe_calc_ut` calls and **about 9 ms** of wall time.
- The per-user monthly sweep used `calculate_transit_to_natal` every 6 hours (120 snapshots) on a
  fictional chart: **about 29 ms per user-month (0.24 ms per snapshot)**.
- Native calls are serialised behind one `RLock` (`ffi/swisseph.py:50`). Batch-computing every
  user would therefore be CPU-serial, but it is still trivial at beta scale.
- Compute global events once a month and cache them (they are non-personal). Compute the user
  overlay on request, the same way Sky Chapter does, and don't store it.
- The 6-hourly sweep catches only the minimum orb. Real exact times and multi-pass hits need the
  new solver. The sweep also surfaces generational noise (for example Neptune sextile natal
  Neptune), so a salience filter is needed.

## 3. User data available for a month recap

Everything below is stored on the server and keyed by `guest_id`. That includes guests, who have a
`guest_sessions` row. The device keeps only caches and sync markers.

| Data | Table | Useful fields | Retention |
|---|---|---|---|
| Daily notes | `daily_notes` (`apps/api/app/domains/daily/tables.py:12-36`) | `note_date`, `context_label`, `persona_mode` | History: hidden after 30 d, **physically purged at 29 d 18 h** for unsaved past days, once the user opts in to `history-retention-v1` (`apps/api/app/domains/history/postgres.py:34-35, 81-86, 224-240`) |
| Saved notes | `saved_notes` (`saved/tables.py:13-49`) | snapshots, `saved_at` | Kept for the profile's lifetime; protects its source note (`history/postgres.py:70-78`) |
| Experiments | `daily_experiments` (`experiments/tables.py:22-70`) | `state` chosen/reflected; outcome `not_tried`/`helpful`/`no_difference`/`not_for_now` (`experiments/models.py:14-18`), encrypted payload | `RETENTION_WINDOW = 29 d 18 h` (`experiments/service.py:15`) |
| Mood | `mood_check_ins` (`mood/tables.py:12-22`) | 5 moods (`mood/models.py:7-12`), `checked_in_at` | History purge at 29 d 18 h; cascades with its note |
| Tarot sessions | `tarot_sessions` (`tarot/tables.py:12-33`) | `context`, `spread`, `voice`, encrypted payload | `RETENTION_WINDOW = 29 d 18 h` (`tarot/service.py:50`) |
| Daily-note views | not recorded | — | The companion keeps only a count of distinct days (`apps/web/src/shared/ui/companion/growth.ts:1-17`) |

**Lifetimes and cleanup**
- Guest profile: 30 days of inactivity (`apps/api/app/config.py:39`).
- Account: 365 days; each device: 30 days (`accounts/models.py:8-9`).
- Cleanup runs every 6 h (`docs/operations/aura-experiment-retention-runbook.md`).
- 7- and 14-day windows exist only for share links, Radar and Lá Chứng, not for this data.

**Answer: nothing is deleted before 30 days.** But the purge at 29 d 18 h means a full
*calendar* month (31 days) can never be recapped from raw rows. By the last day of a 31-day month,
day 1 is already gone.

**Read endpoints**
- `GET /v1/saved-notes` is the only list endpoint (`routes/saved_notes.py:108`).
- Notes, mood, experiments and tarot can be read only for today, the current item, or a known id.
  A recap needs a new owner-scoped aggregate endpoint.

**Device storage**
- Note cache: memory only, 36 h (`apps/web/src/shared/storage/noteCache.ts:4`).
- Saved-note sync markers: at most 30 items and 30 days (`savedNoteCache.ts:3-18`).
- Pending mood under `la-lanh-pending-mood-v1` (`features/home/HomePage.tsx:211`).

## 4. UI entry points and weekly recap

**How `WeekRecap` works today** (`apps/web/src/features/home/HomeRituals.tsx:44-67`, rendered at
`features/home/HomePage.tsx:339`)
- It is client-only and shows only on Sundays (`now.getDay() === 0`).
- It fetches `GET /saved-notes` and filters `saved_at` to a rolling 7×24 h window.
- It shows "Tuần này bạn giữ lại {n} note." with a CTA to `/saved`.
- It renders nothing when the count is 0.
- It uses saved notes only: no mood, experiments or tarot.

**US-18** "recap chủ nhật" is unrelated: it covers the Vòng Lá pool recap and has been
**DEFERRED** since 2026-09-20 (`docs/user-stories/US-18-xem-chia-se-recap-chu-nhat.md:3`).

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
  - Show sky facts with dates plus at most one evidence-bound reflective prompt per event.
  - Never write "nên/không nên ký, nộp đơn, tỏ tình".
  - Keep the disclaimer next to the content.
  - The retrograde copy must not imply a bad period (reading-knowledge-spec:93).
  - The Meaning Gate must reject event certainty.
- **Privacy:**
  - A per-user month view combines derived transit-to-natal contacts, natal houses and (for a
    recap) mood, notes and experiment outcomes. The result is a new derived profile and needs a
    purpose and retention review under Law 91/2025 and Decree 356/2025.
  - Compute it on the fly and don't persist it. Never send mood or notes to the external rewrite
    provider (store-privacy-data-map:11).
  - Update the store declarations if a new stored artifact appears.
  - A shareable monthly card must follow the share-link rules in AGENTS.md: no-store, noindex,
    no-referrer, revocable. It must also exclude mood and notes.
- **Retention vs calendar month.**
  - Raw recap inputs are purged at 29 d 18 h.
  - Options:
    - (a) A rolling "30 ngày qua" recap. This needs no new retention.
    - (b) Persist a minimized monthly aggregate before the purge. That is new derived data about
      mood and behaviour, so it needs separate affirmative consent, its own retention, deletion
      and export, and store-declaration updates.
  - Recommend (a). Do not extend the windows quietly.
- **Content volume** (Vietnamese, reviewed, direct + Roast):
  - Global events: about 12 lunations per year × 12 signs, roughly 24 lunation meanings plus
    sign framing.
  - Station copy: Mercury, Venus and Mars Rx/direct, about 6 base meanings × 12 signs.
  - Ingress copy: Sun, Mercury, Venus and Mars, sign framing only.
  - Personal house layer: lunation × 12 houses (24 to 36 atoms) and Rx × 12 houses.
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
  - The house overlay needs an EXACT birth time.
  - Date-only users get only the global sky and sign-level framing (PRD F3.1 Level 1–2 rule).
  - Avoid Sun-sign-only "horoscope" text, because it fails Rule 2's >30% specificity test
    (product-plan-v2:262-266).
- **Engine correctness.** Station and ingress solvers need fixture tests against reference
  almanac dates (engine spec:363). Eclipse bindings would extend the Swiss Ephemeris release gate
  (`docs/legal/swiss-ephemeris-release-gate.md`).
