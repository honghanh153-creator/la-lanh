import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { bufferStatus, bufferTarget, flowPath, queueTopUp, readyBuffer, recordFlow, renderFlow } from './collab-buffer.mjs';

const pr = (n, extra = {}) => ({ number: n, author: { login: 'honghanh153-creator' }, isCrossRepository: false, baseRefName: 'collab/integration', headRefName: `agent/claude/t${n}`, isDraft: false, labels: [], ...extra });

test('buffer counts open agent PRs into integration, not draft or needs-owner', () => {
  const prs = [pr(1), pr(2, { isDraft: true }), pr(3, { labels: [{ name: 'needs-owner' }] }), pr(4, { baseRefName: 'main' }), pr(5, { headRefName: 'feature/x' }), pr(6, { isCrossRepository: true }), pr(7)];
  assert.equal(readyBuffer(prs), 2);
});

test('top-up asks for 5 - buffer PRs, at most 3 a run', () => {
  assert.equal(bufferTarget, 5);
  assert.deepEqual(queueTopUp(0), { topUp: true, topUpCount: 3, buffer: 0 });
  assert.deepEqual(queueTopUp(3), { topUp: true, topUpCount: 2, buffer: 3 });
  assert.deepEqual(queueTopUp(5), { topUp: false, topUpCount: 0, buffer: 5 });
});

test('flow metric adds the minutes since the last sample while no PR was actionable', () => {
  const dir = mkdtempSync(join(tmpdir(), 'flow-'));
  const t0 = Date.parse('2026-11-05T03:00:00Z');
  recordFlow(0, { dir, nowMs: t0 });
  recordFlow(2, { dir, nowMs: t0 + 10 * 60000 });
  recordFlow(0, { dir, nowMs: t0 + 20 * 60000 });
  const day = recordFlow(0, { dir, nowMs: t0 + 25 * 60000 });
  assert.equal(day.emptyMinutes, 15);
  // A gap longer than 15 minutes (Mac asleep) counts only 15.
  assert.equal(recordFlow(0, { dir, nowMs: t0 + 125 * 60000 }).emptyMinutes, 30);
  assert.equal(JSON.parse(readFileSync(flowPath('2026-11-05', dir), 'utf8')).emptyMinutes, 30);
  assert.match(renderFlow(day), /15 phút/);
});

test('bufferStatus is the one call collab-turn makes for the tick, --status and --report', () => {
  const dir = mkdtempSync(join(tmpdir(), 'flow-'));
  const out = bufferStatus([pr(1)], [{ turn: 'claude-fix' }], { dir, nowMs: Date.parse('2026-11-05T03:00:00Z') });
  assert.deepEqual(out.queue, { topUp: true, topUpCount: 3, buffer: 1 });
  assert.equal(out.day.lastActionable, 0);
  assert.match(out.lines[0], /1\/5, cần thêm 3/);
  const turn = readFileSync(new URL('./collab-turn.mjs', import.meta.url), 'utf8');
  assert.equal((turn.match(/bufferStatus\(/g) ?? []).length, 3, 'tick (#253), --status, --report');
});
