import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { promptPath } from './codex-review.mjs';

test('retro S2: the review prompt asks for every place of the same class in one round', () => {
  const fixed = readFileSync(promptPath, 'utf8');
  assert.match(fixed, /search the whole repository for every other place with the same pattern/);
  assert.match(fixed, /`file:line` entries/);
  assert.match(fixed, /same class again in a place an earlier round could have named is itself a P2 `docs` finding/);
});

test('#208: the prompt gets a trusted creation time and the gate rule for each side of the cutoff', async () => {
  const { fillPrompt, gateRule } = await import('./codex-review.mjs');
  const fixed = readFileSync(promptPath, 'utf8');
  assert.match(fixed, /\{\{GATE_RULE\}\}/);
  assert.match(gateRule('2026-10-31T16:59:59Z'), /exempt from the S\/M\/L/);
  assert.match(gateRule('2026-10-31T17:00:00Z'), /gate-evidence check applies/);
  assert.match(gateRule('2026-11-03T02:00:00Z'), /2026-11-03T02:00:00\.000Z.*check applies/);
  assert.match(gateRule(undefined), /unknown: apply/);
  assert.match(fillPrompt(fixed, { GATE_RULE: gateRule('2026-10-20T00:00:00Z') }), /2026-10-20T00:00:00\.000Z.*exempt/);
});

test('#208: the process doc no longer rejects every missing gate', () => {
  const doc = readFileSync(new URL('../docs/operations/product-development-process.md', import.meta.url), 'utf8');
  assert.doesNotMatch(doc, /thiếu cổng bắt buộc là\s+REQUEST_CHANGES \(P1 nếu là G7\/G8, P2 nếu khác\)/);
  assert.match(doc, /P2 `docs` không chặn: verdict APPROVE kèm issue fix-forward/);
});
