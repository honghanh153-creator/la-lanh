# Home note + Bản đồ debug and code review — 2026-09-28

## Scope

- Home ordering and daily-note states.
- Natal overview and current-sky error states.
- Local QA server session persistence.
- Regression coverage for mobile and desktop product flow.

Baseline reviewed: `513d7930cf7e26f8b33661aaf079cbf4eeaa2665` on `codex/hetzner-supabase-deploy` with pre-existing working-tree changes preserved.

## Reproduction

Opening `/home` after restarting the local QA server produced:

- `GET /v1/daily-note` → `401 GUEST_EXPIRED` for a cookie created against the previous database.
- A clean real API sequence (`guest-sessions` → `birth-profile` → `daily-note`) still returned a complete note with `200`, proving that note generation itself was healthy.

The browser still held the previous cookie while `scripts/qa-server.mjs` had deleted its temporary SQLite database during shutdown. The UI recognized only `GUEST_SESSION_MISSING`, not `GUEST_EXPIRED`, and therefore presented the authorization failure as a generic connection/data error.

## Resolution

1. `Tín hiệu hôm nay` and its note now render before the Tarot/self/person/world exploration router.
2. A missing or expired guest session now has a dedicated recovery state and CTA back to `Trạm Bắt Sóng` on Home, Natal and current-sky.
3. A cached note remains readable offline. If the private session is missing, Home also explains that live Note/Bản đồ features need to be reconnected.
4. QA now uses a persistent local SQLite database keyed by project and web port. The containing directory is forced to mode `0700`.
5. `LA_LANH_QA_RESET=1` creates a clean review state; `LA_LANH_QA_EPHEMERAL=1` restores delete-on-stop behavior; `LA_LANH_QA_DATABASE_URL` remains the only explicit database override.
6. The QA CLI smoke now exercises the real guest → birth profile → daily-note path through the same web proxy used by the product; a healthy `/v1/health` endpoint alone is no longer enough to pass.

## Code-review result

No actionable correctness, security/privacy, reliability or test-coverage finding remains in the reviewed fix.

- The session check is structural (`status` + `code`), so it works for deserialized API problems as well as local `ApiProblem` instances.
- Persistent QA data is not shared across repositories with the same port and is never stored in the git worktree.
- Production database configuration is unchanged.
- Resetting QA intentionally invalidates old browser cookies; the new recovery state makes that transition explicit.

## Verification

- Web lint: pass.
- Web typecheck: pass.
- Web unit/component tests: 38 files, 133 tests pass.
- Focused Home/Natal/current-sky tests: 18 pass.
- QA server tests: 3 pass, including persistence, project isolation, ephemeral cleanup, SPA deep links and API proxy.
- Playwright product flow: 6 scenarios pass across mobile and desktop, including Home → current sky → Home → Bản đồ.
- Production web build: pass.

Known non-blocking build note: the main web bundle remains above Vite's 500 kB advisory threshold; this change does not increase the runtime surface materially and code-splitting remains separate performance work.
