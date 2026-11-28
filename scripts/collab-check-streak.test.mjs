// Three-agent dispatch 28.11.2026, part E: a check failing N runs in a row becomes an incident.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { issueBody, issueTitle, record, recordCheck, streakN } from './collab-check-streak.mjs';
import { pickPlan, serious, workUnits } from './collab-quota.mjs';
import { readJson } from './collab-trust.mjs';

// 26.11.2026 10:28 Vietnam time, then one run every 10 minutes.
const T0 = Date.UTC(2026, 10, 26, 3, 28);
const at = k => T0 + k * 600000;
const fakeIssues = () => {
  const calls = [];
  const open = new Map();
  let next = 970;
  return {
    calls, open,
    failCreate: false, failClose: false,
    find(title) { calls.push(['find', title]); return [...open].find(([, t]) => t.title === title)?.[0] ?? null; },
    create(title, body) { calls.push(['create', title]); if (this.failCreate) throw new Error('gh: network'); const n = next++; open.set(n, { title, body }); return n; },
    close(n, body) { calls.push(['close', n, body]); if (this.failClose) throw new Error('gh: network'); open.delete(n); },
  };
};
const tmp = () => join(mkdtempSync(join(tmpdir(), 'streak-')), 'streaks.json');

test('streak: the 26.11 case: six blocked runs in a row open one incident at the third, a pass closes it', () => {
  const path = tmp();
  const issues = fakeIssues();
  const results = [0, 1, 2, 3, 4, 5].map(k => record('server-inside', 'blocked', { issues, path, nowMs: at(k), detail: 'ssh: connect to host 203.0.113.9 port 22: Operation timed out' }));
  assert.deepEqual(results.map(r => r.action), ['none', 'none', 'open', 'none', 'none', 'none']);
  assert.equal(streakN, 3);
  assert.equal(issues.calls.filter(c => c[0] === 'create').length, 1, 'one issue, not one per run');
  const [number, issue] = [...issues.open][0];
  assert.equal(issue.title, issueTitle('server-inside'));
  assert.match(issue.body, /không chạy được 3 lần liên tiếp, từ 26\.11 10:28 tới 26\.11 10:48/);
  assert.match(issue.body, /## Tiêu chí đạt\n- AC1/);
  assert.doesNotMatch(issue.body, /203\.0\.113|ssh|timed out/, 'no detail text reaches the public repo');
  assert.equal(readJson(path)['server-inside'].fails, 6);
  assert.match(readJson(path)['server-inside'].recent.at(-1).detail, /timed out/, 'the detail stays on this Mac');
  const ok = record('server-inside', 'ok', { issues, path, nowMs: at(6) });
  assert.equal(ok.action, 'resolve');
  assert.equal(ok.issue, number);
  assert.equal(issues.open.size, 0);
  assert.match(issues.calls.at(-1)[2], /đạt lại lúc 26\.11 11:28/);
  assert.equal(readJson(path)['server-inside'].fails, 0);
});

test('streak: a pass in between resets the count; fail and blocked both count; checks are separate', () => {
  let s = {};
  const step = (check, outcome, k) => { const r = recordCheck(s, check, outcome, { nowMs: at(k) }); s = r.state; return r.action; };
  assert.deepEqual(['fail', 'blocked', 'ok', 'fail', 'fail'].map((o, k) => step('a', o, k)), ['none', 'none', 'none', 'none', 'none']);
  assert.equal(step('b', 'fail', 5), 'none', 'another check has its own count');
  assert.equal(step('a', 'blocked', 6), 'open', 'fail, fail, blocked: three in a row');
  assert.throws(() => recordCheck({}, '../x', 'fail'), /tên kiểm tra/);
  assert.throws(() => recordCheck({}, 'a', 'maybe'), /kết quả/);
});

test('streak: a failed GitHub call is retried at the next record; a crash after create finds the open issue', () => {
  const path = tmp();
  const issues = fakeIssues();
  issues.failCreate = true;
  for (const k of [0, 1]) record('db-backup', 'fail', { issues, path, nowMs: at(k) });
  const third = record('db-backup', 'fail', { issues, path, nowMs: at(2) });
  assert.equal(third.status, 'pending');
  issues.failCreate = false;
  const fourth = record('db-backup', 'fail', { issues, path, nowMs: at(3) });
  assert.equal(fourth.status, 'recorded');
  assert.equal(issues.open.size, 1, 'opened on the retry');
  // A crash between create and the state write: the state has no issue, GitHub has one open.
  const state = readJson(path);
  const crashed = tmp();
  const again = record('db-backup', 'fail', { issues, path: crashed, nowMs: at(4), n: 1 });
  assert.equal(again.issue, [...issues.open][0][0], 'the open issue is found by title, not opened twice');
  assert.equal(issues.calls.filter(c => c[0] === 'create').length, 2, 'only the failed and the real create');
  assert.ok(state['db-backup'].issue);
  issues.failClose = true;
  assert.equal(record('db-backup', 'ok', { issues, path, nowMs: at(5) }).status, 'pending');
  issues.failClose = false;
  assert.equal(record('db-backup', 'ok', { issues, path, nowMs: at(6) }).action, 'none');
  assert.equal(issues.open.size, 0, 'the close is retried at the next pass');
});

test('streak: the incident goes first in the day list (no severity: serious, L60)', () => {
  const s = recordCheck(recordCheck(recordCheck({}, 'server-inside', 'blocked', { nowMs: at(0) }).state, 'server-inside', 'blocked', { nowMs: at(1) }).state, 'server-inside', 'blocked', { nowMs: at(2) }).state;
  const issue = { number: 970, title: issueTitle('server-inside'), labels: [{ name: 'ops-alert' }, { name: 'incident' }], body: issueBody('server-inside', s['server-inside']) };
  assert.ok(serious(issue.labels));
  const units = workUnits({ turns: [{ number: 1, title: 'pr 1', area: 'ops', turn: 'claude-check', item: null }], prs: [], issues: [issue] });
  const plan = pickPlan(units);
  assert.deepEqual(plan.incidents.map(u => u.item), [970]);
});
