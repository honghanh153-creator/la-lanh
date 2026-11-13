import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { bufferStatus, flowPath, queueTopUp, readyBuffer, recordFlow, renderFlow, wipCount, wipLimit } from './collab-buffer.mjs';

const pr = (n, extra = {}) => ({ number: n, author: { login: 'honghanh153-creator' }, isCrossRepository: false, baseRefName: 'collab/integration', headRefName: `agent/claude/t${n}`, isDraft: false, labels: [], ...extra });

test('buffer counts open agent PRs into integration, not draft or needs-owner', () => {
  const prs = [pr(1), pr(2, { isDraft: true }), pr(3, { labels: [{ name: 'needs-owner' }] }), pr(4, { baseRefName: 'main' }), pr(5, { headRefName: 'feature/x' }), pr(6, { isCrossRepository: true }), pr(7)];
  assert.equal(readyBuffer(prs), 2);
});

// Owner 12.11.2026: no PR quota. WIP 1 + 1: a new Claude task opens only when nothing is in
// progress and at most one PR waits in review, so finished work beats a count of open PRs.
test('WIP 1 + 1: a new task only when nothing is in progress and at most one is in review', () => {
  assert.deepEqual(wipLimit, { inProgress: 1, inReview: 1 });
  assert.deepEqual(queueTopUp({ inProgress: 0, inReview: 0 }), { topUp: true, topUpCount: 1, inProgress: 0, inReview: 0, buffer: 0 });
  assert.equal(queueTopUp({ inProgress: 0, inReview: 1 }).topUp, true, 'one in review: Claude may start the second slot');
  assert.equal(queueTopUp({ inProgress: 1, inReview: 1 }).topUp, false, '1 in progress and 1 in review: wait');
  assert.equal(queueTopUp({ inProgress: 1, inReview: 0 }).topUp, false, 'one task in progress already fills the slot');
  assert.equal(queueTopUp({ inProgress: 0, inReview: 2 }).topUp, false, 'review is full: finish before starting');
  assert.equal(queueTopUp({ inProgress: 0, inReview: 0 }).topUpCount, 1, 'never more than one new task at a time');
});

test('WIP counts open agent PRs: machine turns are in review, the rest are in progress', () => {
  const prs = [pr(1), pr(2), pr(3, { isDraft: true }), pr(4, { labels: [{ name: 'needs-owner' }] }), pr(5, { headRefName: 'feature/x' }), pr(6)];
  const turns = [{ number: 1, turn: 'codex-review' }, { number: 2, turn: 'claude-fix' }, { number: 3, turn: 'hold' }, { number: 4, turn: 'hold' }, { number: 5, turn: 'merge' }, { number: 6, turn: 'merge' }];
  assert.deepEqual(wipCount(prs, turns), { inProgress: 2, inReview: 2 }, 'needs-owner waits on the owner and an owner branch is not agent work');
  assert.equal(readyBuffer(prs), 3, 'the old readiness count still skips draft and needs-owner');
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
  const out = bufferStatus([pr(1)], [{ number: 1, turn: 'claude-fix' }], { dir, nowMs: Date.parse('2026-11-05T03:00:00Z') });
  assert.deepEqual(out.queue, { topUp: false, topUpCount: 0, inProgress: 1, inReview: 0, buffer: 1 });
  assert.equal(out.day.lastActionable, 0);
  assert.match(out.lines[0], /Việc đang làm: 1\/1, đang chờ review: 0\/1; chưa mở việc mới\./);
  const turn = readFileSync(new URL('./collab-turn.mjs', import.meta.url), 'utf8');
  assert.equal((turn.match(/bufferStatus\(/g) ?? []).length, 3, 'tick (#253), --status, --report');
});
