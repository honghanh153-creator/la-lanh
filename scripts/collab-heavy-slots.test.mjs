// D1 of the two-heavy-jobs change (owner 16.11.2026): each slot has its own ports and Compose project.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { heavySlots, reservedPorts, slotEnv, slotPorts } from './collab-heavy-slots.mjs';

test('heavy slots: slot 0 is today\'s defaults; no port or Compose project is shared between slots or with dev', () => {
  assert.deepEqual(slotPorts(0), { e2e: 4173, verify: 4184, qaApi: 8010, qaWeb: 5180, postgres: 5432 });
  assert.equal(slotEnv(0).COMPOSE_PROJECT_NAME, 'la-lanh', 'slot 0 keeps the compose.yaml project');
  const all = Array.from({ length: heavySlots }, (_, s) => Object.values(slotPorts(s))).flat();
  assert.equal(new Set(all).size, all.length, 'every port belongs to one slot');
  assert.ok(!all.some(p => reservedPorts.includes(p)), 'no slot takes the dev ports');
  const projects = Array.from({ length: heavySlots }, (_, s) => slotEnv(s).COMPOSE_PROJECT_NAME);
  assert.equal(new Set(projects).size, heavySlots);
  assert.throws(() => slotPorts(heavySlots), /heavy slot/);
  assert.throws(() => slotEnv(-1), /heavy slot/);
});

test('heavy slots: the e2e run takes its port from the slot and never reuses another job\'s server', () => {
  const config = readFileSync(new URL('../apps/web/playwright.config.ts', import.meta.url), 'utf8');
  assert.match(config, /process\.env\.LA_LANH_E2E_PORT/, 'the port comes from the slot');
  assert.doesNotMatch(config, /127\.0\.0\.1:4173/, 'no fixed e2e origin is left');
  assert.match(config, /--port \$\{port\}/, 'the preview server starts on the slot port');
  assert.match(config, /reuseExistingServer: !process\.env\.CI && !process\.env\.LA_LANH_HEAVY_SLOT/, 'a slot never reuses a server it did not start');
  // The other moved resources are read from the env names the slot sets.
  const reads = {
    VERIFY_PORT: 'apps/web/tests/verify/verify.config.ts', LA_LANH_QA_API_PORT: 'scripts/qa-server.mjs', LA_LANH_QA_WEB_PORT: 'scripts/qa-server.mjs', POSTGRES_PORT: 'infra/compose/compose.yaml',
  };
  for (const [name, file] of Object.entries(reads)) assert.match(readFileSync(new URL(`../${file}`, import.meta.url), 'utf8'), new RegExp(name), `${file} reads ${name}`);
  for (const name of Object.keys(reads)) assert.ok(name in slotEnv(1), `slot env sets ${name}`);
});
