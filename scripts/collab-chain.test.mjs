import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'chain-'));
const { briefPath, chainPath, classify, maxAttempts, runChain } = await import('./collab-chain.mjs');
const { readProgress } = await import('./collab-progress.mjs');

const day = Date.parse('2026-11-22T03:00:00Z'); // 10:00 in Vietnam
function rig(script) {
  const home = mkdtempSync(join(tmpdir(), 'chain-home-'));
  let clock = day;
  const calls = [], slept = [];
  const step = name => n => { calls.push(name); const next = script[name].shift(); return typeof next === 'function' ? next() : next; };
  const go = () => runChain(904, { home, nowMs: () => clock, sleep: ms => { slept.push(ms); clock += ms; }, steps: { check: step('check'), review: step('review'), merge: step('merge') } });
  return { home, calls, slept, go, tick: ms => { clock += ms; } };
}

test('L76: one command runs check → review → merge, waiting through busy steps without waking Claude', () => {
  const r = rig({ check: [{ status: 'busy' }, { status: 'synced' }, { status: 'PASS' }], review: [{ status: 'stale' }, { status: 'posted', verdict: 'APPROVE' }], merge: [{ status: 'blocked', reasons: ['CI chưa xong'] }, { status: 'merged' }] });
  assert.deepEqual(r.go(), { pr: 904, status: 'done' });
  assert.deepEqual(r.calls, ['check', 'check', 'check', 'review', 'review', 'merge', 'merge']);
  assert.deepEqual(r.slept, [60000, 120000, 60000, 60000], 'backoff per step, reset after each step passes');
  assert.equal(JSON.parse(readFileSync(chainPath(904, r.home), 'utf8')).status, 'done');
  assert.equal(readProgress({ home: r.home, now: new Date(day + 3600000) })[0].status, 'done', 'the shared board says done; nobody was messaged');
});

test('L76: a REQUEST_CHANGES stops with a brief for a small fresh session; the rerun resumes at the check; a third fix round escalates', () => {
  const rc = { status: 'posted', verdict: 'REQUEST_CHANGES', blocking: 1 };
  const r = rig({ check: [{ status: 'PASS' }, { status: 'PASS' }, { status: 'FAIL', reason: 'test hỏng' }], review: [rc, rc], merge: [] });
  const first = r.go();
  assert.equal(first.status, 'fix');
  const brief = readFileSync(briefPath(904, r.home), 'utf8');
  for (const part of ['Mục tiêu:', 'Đầu vào:', 'Quyết định đã có:', 'Bằng chứng:', 'Xong khi:']) assert.ok(brief.includes(part), part);
  assert.match(brief, /vòng sửa 1\/2/);
  assert.equal(readProgress({ home: r.home, now: new Date(day) })[0].status, 'blocked');
  assert.equal(r.go().status, 'fix', 'second round');
  const third = r.go();
  assert.equal(third.status, 'escalated');
  assert.match(third.reason, /quá 2 vòng sửa: test hỏng/);
  assert.equal(readProgress({ home: r.home, now: new Date(day) })[0].status, 'decision');
  assert.deepEqual(r.calls, ['check', 'review', 'check', 'review', 'check']);
});

test('L76: a step that keeps waiting, an overdue chain, owner work, a spent Codex cap and 23:35 all stop instead of looping', () => {
  const busy = rig({ check: Array.from({ length: maxAttempts + 1 }, () => ({ status: 'busy', reason: 'khóa' })), review: [], merge: [] });
  const out = busy.go();
  assert.equal(out.status, 'escalated');
  assert.match(out.reason, new RegExp(`chờ quá ${maxAttempts} lần: khóa`));
  const slow = rig({ check: [() => { slow.tick(4 * 3600000); return { status: 'busy' }; }], review: [], merge: [] });
  assert.equal(slow.go().status, 'overdue');
  assert.equal(classify('review', { status: 'posted', verdict: 'APPROVE', needsOwner: ['release'] }).go, 'stop');
  assert.equal(classify('review', { status: 'limit' }).go, 'stop');
  assert.equal(classify('check', { status: 'FAIL' }).go, 'fix');
  const late = rig({ check: [], review: [], merge: [] });
  late.tick(13 * 3600000 + 40 * 60000); // 23:40 in Vietnam
  assert.equal(late.go().status, 'stopped');
  assert.deepEqual(late.calls, [], 'no step starts after 23:35 (R9)');
});
