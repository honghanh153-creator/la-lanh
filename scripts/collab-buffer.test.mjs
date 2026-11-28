import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { admittedQueue, bufferStatus, flowPath, liveJobs, queueTopUp, readyBuffer, recordFlow, renderFlow, wipCount, wipLimit } from './collab-buffer.mjs';

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
  const count = wipCount(prs, turns);
  assert.deepEqual([count.inProgress, count.inReview], [2, 2], 'needs-owner waits on the owner and an owner branch is not agent work');
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
  // Owner 16.11: one process task in progress fills the process lane only; the 7-week lane may start.
  assert.deepEqual([out.queue.topUp, out.queue.topUpCount, out.queue.topUpLanes, out.queue.inProgress, out.queue.buffer], [true, 2, ['plan7w', 'daily'], 1, 1]);
  assert.equal(out.day.lastActionable, 0);
  assert.match(out.lines[0], /^Làn kế hoạch 7 tuần: đang làm 0\/1, chờ review 0\/1; có thể mở 1 việc mới\.$/);
  assert.match(out.lines[1], /^Làn Daily \(thử 18–19\.11\): đang làm 0\/1, chờ review 0\/1; có thể mở 1 việc mới\.$/);
  assert.match(out.lines[2], /^Làn quy trình: đang làm 1\/1, chờ review 0\/1; chưa mở việc mới\.$/);
  const turn = readFileSync(new URL('./collab-turn.mjs', import.meta.url), 'utf8');
  assert.equal((turn.match(/bufferStatus\(/g) ?? []).length, 3, 'tick (#253), --status, --report');
});

// Owner 16.11.2026 (5-fix package item 5): the 7-week lane and the process lane run in parallel,
// each with its own WIP 1 + 1.
test('two lanes: each lane has its own WIP 1 + 1 and tops up on its own; 7-week first', () => {
  const plan = [{ name: 'ke-hoach-7-tuan' }];
  const prs = [pr(11, { labels: plan }), pr(12), pr(13), pr(14)];
  const turns = [{ number: 11, turn: 'claude-fix' }, { number: 12, turn: 'claude-fix' }, { number: 13, turn: 'codex-review' }, { number: 14, turn: 'claude-check' }];
  // #14 is a picked 7-week item without the label yet: it counts in the 7-week lane.
  const count = wipCount(prs, turns, { plan7wPrs: [14] });
  assert.deepEqual(count.lanes, { plan7w: { inProgress: 1, inReview: 1 }, daily: { inProgress: 0, inReview: 0 }, process: { inProgress: 1, inReview: 1 } });
  assert.deepEqual([count.inProgress, count.inReview], [2, 2], 'the totals the WIP metric reads are unchanged');
  const full = queueTopUp(count);
  assert.deepEqual([full.topUp, full.topUpLanes], [true, ['daily']], 'the 7-week and process lanes are full; the empty Daily lane may start');
  // The process lane finishes its task; only that lane may start a new one.
  const one = queueTopUp(wipCount([pr(11, { labels: plan }), pr(13), pr(14)], turns, { plan7wPrs: [14] }));
  assert.deepEqual([one.topUp, one.topUpCount, one.topUpLanes], [true, 2, ['daily', 'process']]);
  // Both empty: both lanes may start, the 7-week lane first.
  const both = queueTopUp(wipCount([], [], {}));
  assert.deepEqual([both.topUpCount, both.topUpLanes], [3, ['plan7w', 'daily', 'process']]);
  // A busy process lane never blocks the 7-week lane.
  const busy = queueTopUp(wipCount([pr(12), pr(13)], turns));
  assert.deepEqual(busy.topUpLanes, ['plan7w', 'daily']);
});

test('review 16.11: a persona-fix PR is plan-lane work', () => {
  const count = wipCount([pr(31, { labels: [{ name: 'persona-fix' }] })], [{ number: 31, turn: 'claude-fix' }]);
  assert.deepEqual(count.lanes, { plan7w: { inProgress: 1, inReview: 0 }, daily: { inProgress: 0, inReview: 0 }, process: { inProgress: 0, inReview: 0 } });
});

test('trial 18–19.11 (owner 17.11): a daily-lane PR runs in its own lane, after the 7-week plan', () => {
  const daily = [{ name: 'daily-lane' }];
  const count = wipCount([pr(41, { labels: daily }), pr(42, { labels: [{ name: 'ke-hoach-7-tuan' }, { name: 'daily-lane' }] })], [{ number: 41, turn: 'claude-fix' }, { number: 42, turn: 'codex-review' }]);
  assert.deepEqual(count.lanes, { plan7w: { inProgress: 0, inReview: 1 }, daily: { inProgress: 1, inReview: 0 }, process: { inProgress: 0, inReview: 0 } }, 'the 7-week label wins over daily');
  assert.deepEqual(queueTopUp(count).topUpLanes, ['plan7w', 'process'], 'the Daily lane is busy; the others may start');
});

// #949 r1 (C5): --status and --report show the admitted view the tick uses: lanes never say
// "có thể mở" past the host limits, and the reason is one plain line.
test('bufferStatus shows the admitted lanes and why the host opens nothing', () => {
  const dir = mkdtempSync(join(tmpdir(), 'flow-'));
  const nowMs = Date.parse('2026-11-05T03:00:00Z');
  const late = bufferStatus([pr(1)], [{ number: 1, turn: 'claude-fix' }], { dir, nowMs, late: true });
  assert.deepEqual([late.queue.topUp, late.queue.topUpCount, late.queue.topUpLanes], [false, 0, []]);
  assert.ok(late.lines.slice(0, 3).every(l => /chưa mở việc mới\.$/.test(l)), 'no lane opens after lastStartAt');
  assert.ok(late.lines.some(l => /^Máy đang đầy, chưa mở việc mới: .*đã qua giờ mở việc mới/.test(l)));
  const full = bufferStatus([pr(1), pr(2)], [{ number: 1, turn: 'codex-review' }, { number: 2, turn: 'codex-review' }], { dir, nowMs });
  assert.equal(full.queue.topUp, false);
  assert.ok(full.lines.some(l => /^Máy đang đầy, chưa mở việc mới: .*chờ review 2\/2/.test(l)));
});

// #949 r2 (C6): host backpressure counts live jobs (a claimed PR not in machine review), not every
// open PR. A large unclaimed backlog with idle workers must still let the empty plan lane open.
test('C6: a big unclaimed backlog does not fill the host gate; claimed PRs do', () => {
  const daily = Array.from({ length: 6 }, (_, i) => pr(100 + i, { labels: [{ name: 'daily-lane' }] }));
  const proc = Array.from({ length: 14 }, (_, i) => pr(200 + i));
  const prs = [...daily, ...proc];
  const turns = prs.map(p => ({ number: p.number, turn: 'claude-fix' }));
  assert.deepEqual(liveJobs(prs, turns, []), { inProgress: 0, inReview: 0 });
  const idle = admittedQueue(prs, turns, { claimed: [] });
  assert.equal(idle.lanes.plan7w.topUp, true, 'plan lane is empty: it may open one');
  assert.deepEqual(idle.backpressure, [], 'no live job: no host backpressure');
  assert.equal(idle.liveJobs, 0);
  const busy = admittedQueue(prs, turns, { claimed: ['100', '200', '201'] });
  assert.equal(busy.liveJobs, 3, 'claimed PRs count as live jobs');
  assert.equal(busy.topUp, false, '3 live jobs fill the host gate');
  assert.ok(busy.backpressure.length > 0);
  const reviewing = liveJobs(prs, prs.map(p => ({ number: p.number, turn: p.number === 100 ? 'codex-review' : 'claude-fix' })), ['100']);
  assert.deepEqual(reviewing, { inProgress: 0, inReview: 1 }, 'a claimed PR in machine review counts once, as review');
});
