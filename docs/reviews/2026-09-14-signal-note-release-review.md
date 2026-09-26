# Signal Note Experience — implementation review

Ngày: 2026-09-14  
Scope: canonical onboarding `Trạm Bắt Sóng`, Personal Signal Daily Note, Context Dial, resonance controls, docs/privacy/security contracts và app packaging gates.

## Outcome

**Ready for product/design review on the local QA build. Not ready for native store release.**

Shared UI, API behavior, documentation and automated tests are implemented. The remaining release blocker is external and intentional: no real versioned HTTPS API origin has been supplied for the Capacitor bundle. The build guard correctly rejects a missing, local-cleartext or placeholder origin.

## Implemented product flow

1. `/welcome` — `00/02`, concise purpose/retention/control disclosure, one consent CTA, demo without personal profile.
2. `/birth` — `01/02`, strict DD/MM/YYYY validation, 18+ gate, no DOB in URL/storage/logging.
3. `/reveal` — `02/02`, Vibe reveal from the create response cache, no duplicate fetch or fake wait.
4. `/home` — dark Cosmic Glass first, Context Dial, compact cream Note, evidence disclosure, reversible action, resonance, Mood, save/share, Aura unlock and feature navigation.
5. `/note/today` — long-form reading for the user who asks to go deeper.
6. `/profile` — light/dark toggle plus feedback status, reset and revoke controls.

## Context and content behavior

- The first scan exposes `auto/work/relationships/communication`; `energy/self_care` are available through `Thêm 2 góc`.
- Context is sent by private CSRF-protected POST body and is not copied to URL, analytics, public/share payload or preference storage.
- Context changes only manifestation and micro-action. Chart snapshot, factors, evidence, precision and confidence remain invariant.
- `Đổi góc` records nothing; it focuses the Context Dial and waits for an explicit selection.
- `Trúng/Chưa trúng` require just-in-time consent. Stored fields are bounded enums/IDs/timestamps, owner-scoped, encrypted, idempotent and purged within 30 days; free text is not accepted.

## Verification evidence

- Web lint: pass.
- Web typecheck: pass.
- Web unit/component tests: **51 passed** across 19 files.
- Browser E2E: **8 passed** across mobile and desktop Chromium.
- Focused API/readings/resonance suite: **184 passed**.
- OpenAPI and generated TypeScript contracts: current.
- Runtime no-mock guard: pass.
- Privacy guard: pass.
- Mobile release guard: pass; guard tests **4 passed**.
- Working-tree whitespace/error scan: pass.
- Real local flow: guest consent → DOB → Swiss Ephemeris reveal → Home completed; Context Dial changed copy while URL remained `/home`; browser console error log was empty.
- PostgreSQL migration offline upgrade/downgrade: pass through head `20260914_0016`.

Two unrelated full-suite `la_chung` fixtures use invitations fixed to 2026-09-07 and now fail as expired on 2026-09-14. No `la_chung` implementation was changed for this scope; the focused affected-domain suite is green. This fixture debt must still be corrected before calling the repository-wide suite fully green.

## Product review files

- Plan: `docs/plans/2026-09-14-2047-feat-signal-note-experience-plan.md`
- Resolved plan review: `docs/reviews/2026-09-14-signal-note-plan-review.md`
- Design contract and captures: `docs/design-directions/signal-note-2026-09-14/`
- Design QA: `design-qa.md`
- Updated stories: `docs/user-stories/US-01-bat-dau-che-do-khach.md`, `US-02-khai-ngay-sinh-reveal-la-khai-sinh.md`, `US-03-doc-note-hom-nay.md`
- Privacy/security: `docs/legal/privacy-security-flow-notes.md`, `docs/reference/data-inventory-us01-us06.md`

## Native release No-Go

`pnpm mobile:sync` deliberately refuses to run without `VITE_API_BASE_URL=https://<real-host>/v1`. To turn this review build into an installable release candidate:

1. Supply the real versioned HTTPS API origin and matching secure-cookie/CORS configuration.
2. Sync the final web assets into both native shells.
3. Build/run iOS and Android, then test onboarding, context POST, feedback consent/reset, restart/resume, offline state, safe areas and accessibility.
4. Reconcile runtime collection with Apple Privacy Manifest/App Privacy and Android Data Safety before store submission.

Qualified Vietnamese legal review remains required for production impact-assessment and cross-border-processing obligations.
