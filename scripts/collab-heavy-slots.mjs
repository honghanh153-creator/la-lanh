// Heavy-job slots (owner 16.11.2026, 5-fix package item 3b: "2 việc nặng cùng lúc", each with its
// own ports and lock). Step D1 only gives each slot its own resources; one heavy job at a time stays
// in force until step D2 turns the two-slot semaphore on (Codex 16.11: isolate first, then activate).
// Slot 0 is today's defaults, so nothing changes for a job that sets no slot.
// What a slot moves (resource map 16.11, la-lanh-claude): the Playwright e2e preview port (4173,
// fixed before D1), verify (VERIFY_PORT), the QA server (LA_LANH_QA_API_PORT / _WEB_PORT; its sqlite
// path follows the web port), the Compose project and its Postgres port. Separate clones keep build
// outputs apart; the pnpm store, uv cache and Playwright browsers are shared read caches.
export const heavySlots = 2;
const base = { e2e: 4173, verify: 4184, qaApi: 8010, qaWeb: 5180, postgres: 5432 };
// Ports other local work uses, which no slot may take: dev API and Vite dev.
export const reservedPorts = [8000, 5173];
const step = 100;

export function slotPorts(slot) {
  if (!Number.isInteger(slot) || slot < 0 || slot >= heavySlots) throw new Error(`heavy slot ${slot} is not 0..${heavySlots - 1}`);
  return { e2e: base.e2e + step * slot, verify: base.verify + step * slot, qaApi: base.qaApi + step * slot, qaWeb: base.qaWeb + step * slot, postgres: base.postgres + slot };
}

export function slotEnv(slot) {
  const p = slotPorts(slot);
  return {
    LA_LANH_HEAVY_SLOT: String(slot),
    LA_LANH_E2E_PORT: String(p.e2e),
    VERIFY_PORT: String(p.verify),
    LA_LANH_QA_API_PORT: String(p.qaApi),
    LA_LANH_QA_WEB_PORT: String(p.qaWeb),
    POSTGRES_PORT: String(p.postgres),
    COMPOSE_PROJECT_NAME: slot === 0 ? 'la-lanh' : `la-lanh-slot${slot}`,
  };
}
