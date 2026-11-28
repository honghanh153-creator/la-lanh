// Three-agent dispatch 28.11.2026, parts A and B: availability, one coordinator lease, sole agent.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { acquireLease, agentOrder, agentStatus, availableAgents, coordinatorFor, decideLease, leaseMs, markAvailable, markLimited, mayApprove, mayCall, noteProbe, parseResetAt, probeEveryMs, readAgents, recordStop, releaseLease, reviewPlan, updateAgents, waitIndependent } from './collab-agents.mjs';
import { readJson } from './collab-trust.mjs';

const T0 = Date.UTC(2026, 10, 28, 3, 0);
const subsets = [['claude'], ['codex'], ['anti'], ['claude', 'codex'], ['claude', 'anti'], ['codex', 'anti'], ['claude', 'codex', 'anti']];
const stateFor = set => Object.fromEntries(agentOrder.map(a => [a, set.includes(a) ? { status: 'available' } : { status: 'limited', untilMs: T0 + 3600000 }]));
const dir = () => mkdtempSync(join(tmpdir(), 'agents-'));

test('agents: the Codex message gives the reset time, read as Vietnam time', () => {
  const text = 'ERROR: You’ve hit your usage limit. Visit https://chatgpt.com/settings/usage to purchase more credits or try again at Dec 4th, 2026 7:35 AM.';
  assert.equal(new Date(parseResetAt(text)).toISOString(), '2026-12-04T00:35:00.000Z');
  assert.equal(new Date(parseResetAt('try again at Nov 30th, 2026 11:05 PM')).toISOString(), '2026-11-30T16:05:00.000Z');
  assert.equal(parseResetAt('rate limit, no time given'), null);
});

test('agents: all 7 combinations: coordinator order, who approves, a sole agent never approves', () => {
  for (const set of subsets) {
    const state = stateFor(set);
    const available = availableAgents(state, T0);
    assert.deepEqual(available, set, `available ${set}`);
    assert.equal(coordinatorFor(available), agentOrder.find(a => set.includes(a)), `coordinator for ${set}`);
    for (const author of ['claude', 'codex']) {
      const plan = reviewPlan({ author, available });
      const expected = set.includes('codex') && author !== 'codex';
      assert.equal(plan.status, expected ? 'review' : 'wait', `${author} PR with ${set}`);
      if (expected) assert.equal(plan.approver, 'codex');
      else assert.equal(plan.reason, waitIndependent);
      if (set.length === 1) {
        assert.equal(plan.soleAgent ?? set[0], set[0]);
        assert.ok(plan.status === 'wait' || plan.approver !== author, 'a sole agent never approves its own work');
      }
    }
    assert.equal(reviewPlan({ author: 'anti', available }).status, set.includes('codex') ? 'review' : 'wait');
  }
  assert.equal(mayApprove('codex', 'codex'), false);
  assert.equal(mayApprove('anti', 'claude'), false, 'Anti is review-only (part F)');
  assert.equal(mayApprove('claude', 'codex'), false, 'R1: Codex approves');
  assert.deepEqual(reviewPlan({ author: 'claude', available: ['claude'] }).mayWork, ['claude'], 'alone, Claude may still do, test and push');
  assert.deepEqual(reviewPlan({ author: 'claude', available: ['anti'] }).mayWork, [], 'Anti alone writes nothing');
});

test('agents: no probe before the reset; one probe after it; a new limit sets a new reset', () => {
  const until = T0 + 6 * 24 * 3600000;
  let s = markLimited({}, 'codex', { reason: 'try again at Dec 4th, 2026 7:35 AM', nowMs: T0 });
  assert.equal(s.codex.untilMs, parseResetAt('try again at Dec 4th, 2026 7:35 AM'));
  for (const t of [T0, T0 + 600000, T0 + 24 * 3600000, s.codex.untilMs - 1]) assert.equal(mayCall(s, 'codex', t), false, 'no call before the reset');
  const after = s.codex.untilMs + 1;
  assert.equal(agentStatus(s, 'codex', after), 'probe');
  s = noteProbe(s, 'codex', after);
  assert.equal(agentStatus(s, 'codex', after + 600000), 'limited', 'one probe, then wait probeEveryMs');
  assert.equal(agentStatus(s, 'codex', after + probeEveryMs), 'probe');
  s = markLimited(s, 'codex', { reason: 'usage limit', nowMs: after });
  assert.equal(s.codex.untilMs, after + probeEveryMs, 'no readable reset: wait one probe interval');
  s = markAvailable(s, 'codex', after + 2 * probeEveryMs);
  assert.equal(agentStatus(s, 'codex', after + 2 * probeEveryMs), 'available', 'an agent comes back after its limit');
  assert.equal(agentStatus({ codex: { status: 'limited', untilMs: until } }, 'codex', T0), 'limited');
  assert.equal(agentStatus({ anti: { status: 'off' } }, 'anti', T0), 'off');
});

test('agents: the host file keeps the limit across processes', () => {
  const path = join(dir(), 'agents.json');
  updateAgents(s => markLimited(s, 'codex', { reason: 'try again at Dec 4th, 2026 7:35 AM', nowMs: T0 }), { path });
  assert.equal(mayCall(readAgents({ path }), 'codex', T0 + 3600000), false);
});

test('lease: first available agent takes it; others wait; renew keeps the epoch', () => {
  const all = ['claude', 'codex', 'anti'];
  const a = decideLease({ lease: null, me: 'claude', jobId: 'j1', pid: 11, host: 'h', available: all, nowMs: T0, alive: () => true });
  assert.equal(a.action, 'acquire');
  assert.equal(a.lease.epoch, 1);
  assert.equal(decideLease({ lease: a.lease, me: 'codex', jobId: 'j2', pid: 12, host: 'h', available: all, nowMs: T0, alive: () => true }).action, 'wait');
  const r = decideLease({ lease: a.lease, me: 'claude', jobId: 'j1', pid: 11, host: 'h', available: all, nowMs: T0 + 60000, alive: () => true });
  assert.equal(r.action, 'renew');
  assert.equal(r.lease.epoch, 1);
  assert.equal(r.lease.expiresAtMs, T0 + 60000 + leaseMs);
});

test('lease: handover only with proof the old job stopped; expired without proof raises an alert', () => {
  const lease = decideLease({ lease: null, me: 'claude', jobId: 'j1', pid: 11, host: 'h', available: ['claude', 'codex'], nowMs: T0, alive: () => true }).lease;
  const later = T0 + 2 * leaseMs;
  const noProof = decideLease({ lease, me: 'codex', jobId: 'j2', pid: 12, host: 'h', available: ['codex'], nowMs: later, alive: () => true });
  assert.equal(noProof.action, 'wait');
  assert.match(noProof.alert, /chưa có bằng chứng/);
  assert.equal(noProof.lease, null, 'nothing is written');
  for (const [proof, old] of [['pid-gone', lease], ['released', { ...lease, released: true }], ['stop-record', { ...lease, stops: ['j1'] }]]) {
    const t = decideLease({ lease: old, me: 'codex', jobId: 'j2', pid: 12, host: 'h', available: ['codex'], nowMs: later, alive: () => proof !== 'pid-gone' });
    assert.equal(t.action, 'takeover', proof);
    assert.equal(t.reason, proof);
    assert.equal(t.lease.epoch, 2, 'every acquire raises the epoch');
  }
  const otherHost = decideLease({ lease, me: 'codex', jobId: 'j2', pid: 12, host: 'other', available: ['codex'], nowMs: later, alive: () => false });
  assert.equal(otherHost.action, 'wait', 'a PID on another host proves nothing');
});

test('lease: a higher agent back after its limit asks; the holder hands back at its next renew', () => {
  const held = decideLease({ lease: null, me: 'codex', jobId: 'c1', pid: 21, host: 'h', available: ['codex', 'anti'], nowMs: T0, alive: () => true }).lease;
  const ask = decideLease({ lease: held, me: 'claude', jobId: 'k1', pid: 22, host: 'h', available: agentOrder, nowMs: T0 + 1000, alive: () => true });
  assert.equal(ask.action, 'wait');
  assert.equal(ask.lease.handback, 'claude');
  const back = decideLease({ lease: ask.lease, me: 'codex', jobId: 'c1', pid: 21, host: 'h', available: agentOrder, nowMs: T0 + 2000, alive: () => true });
  assert.equal(back.action, 'release');
  const take = decideLease({ lease: back.lease, me: 'claude', jobId: 'k1', pid: 22, host: 'h', available: agentOrder, nowMs: T0 + 3000, alive: () => true });
  assert.equal(take.action, 'takeover');
  assert.equal(take.lease.epoch, 2);
});

test('lease: the file round trip (acquire, release, stop record) on the host', () => {
  const path = join(dir(), 'lease.json');
  assert.equal(acquireLease({ me: 'claude', jobId: 'j1', available: ['claude'], path, nowMs: T0 }).action, 'acquire');
  assert.equal(acquireLease({ me: 'claude', jobId: 'j1', available: ['claude'], path, nowMs: T0 + 1 }).action, 'renew');
  assert.equal(releaseLease({ me: 'codex', jobId: 'j1', path }), false, 'only the holder releases');
  assert.equal(acquireLease({ me: 'codex', jobId: 'j2', available: ['codex'], path, nowMs: T0 + 2 * leaseMs }).action, 'wait', 'this process is alive: no proof');
  assert.ok(recordStop({ jobId: 'j1', path }));
  const t = acquireLease({ me: 'codex', jobId: 'j2', available: ['codex'], path, nowMs: T0 + 2 * leaseMs });
  assert.equal(t.action, 'takeover');
  assert.equal(readJson(path).holder, 'codex');
  assert.ok(releaseLease({ me: 'codex', jobId: 'j2', path }));
  assert.equal(readJson(path).released, true);
});
