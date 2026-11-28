import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { promptPath, runCodex } from './codex-review.mjs';

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

test('owner 13.11: the review checks that a closed workflow lesson has a test that reproduces the old failure', () => {
  const fixed = readFileSync(promptPath, 'utf8');
  assert.match(fixed, /scripts\/collab-lessons\.json/);
  assert.match(fixed, /would fail on the code before the fix/);
  assert.match(fixed, /closed without\s+that proof is a P1 `test` finding/);
  assert.match(fixed, /Removing a lesson, moving its due date later, or changing it to `waiting-owner` is a P1 `docs` finding/);
});

// #949 r2 (N2): the reset time comes from the whole output, also when only stderr has it.
test('runCodex keeps the reset time from stderr; another failure is an error, not a limit', () => {
  const limit = runCodex({ dir: '.', prompt: 'p', outPath: '/dev/null', timeoutMs: 1000, run: () => { throw Object.assign(new Error('Command failed: codex exec'), { stdout: '', stderr: 'ERROR: You have hit your usage limit. try again at Dec 4th, 2026 7:35 AM' }); } });
  assert.equal(limit.status, 'limit');
  assert.equal(new Date(limit.untilMs).toISOString(), '2026-12-04T00:35:00.000Z');
  const net = runCodex({ dir: '.', prompt: 'p', outPath: '/dev/null', timeoutMs: 1000, run: () => { throw Object.assign(new Error('spawnSync codex ETIMEDOUT'), { stderr: '' }); } });
  assert.equal(net.status, 'error');
  assert.equal(net.untilMs, null);
});
