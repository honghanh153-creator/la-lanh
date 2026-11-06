import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, utimesSync, writeFileSync, writeSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-check-log-'));
const home = process.env.LA_LANH_COLLAB_HOME;
const trust = await import('./collab-trust.mjs');
const log = await import('./collab-check-log.mjs');
const { runCheck } = await import('./collab-check.mjs');
const { runGuarded, refusedCode } = await import('./collab-test-guard.mjs');

const A = 'a'.repeat(40);
const pr = () => ({ number: 248, title: 'ops: x', author: { login: 'honghanh153-creator' }, isCrossRepository: false, state: 'OPEN', baseRefName: 'collab/integration', headRefName: 'agent/claude/x', headRefOid: A, labels: [], comments: [], body: 'b' });
function fakeGh() {
  const calls = [];
  return { calls, pr, comment: (kind, number, body) => { trust.assertAgentBody(body); calls.push(body); } };
}
const git = args => (args[0] === 'rev-parse' ? A : '');
const output = [
  '> la-lanh@0.1.0 collab:test /x', 'ok 1', '',
  '> la-lanh@0.1.0 contracts:check /x', 'contracts ok', '',
  '> la-lanh@0.1.0 web:test /x', ...Array.from({ length: 50 }, (_, i) => `line ${i}`),
  'GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz0123', 'Authorization: Bearer xyz', 'owner term ZZ-PRIVATE here', 'FAIL src/a.test.ts',
].join('\n');

test('steps and the failing step come from the check chain and pnpm headers', () => {
  const steps = log.checkSteps('pnpm collab:test && pnpm contracts:check && pnpm web:test && pnpm web:e2e');
  assert.deepEqual(steps, ['collab:test', 'contracts:check', 'web:test', 'web:e2e']);
  assert.equal(log.failedStep(output, steps), 'web:test');
  assert.equal(log.failedStep('no headers', steps), null);
});

test('logs rotate: only the newest 30 check logs stay', () => {
  const dir = join(home, 'rot');
  mkdirSync(dir);
  for (let i = 0; i < 33; i++) {
    const file = join(dir, log.logName(i + 1, A));
    writeFileSync(file, 'x');
    utimesSync(file, 1000 + i, 1000 + i);
  }
  writeFileSync(join(dir, 'other.txt'), 'kept');
  assert.equal(log.rotateLogs(dir).length, 3);
  const left = readdirSync(dir);
  assert.equal(left.filter(name => name.startsWith('check-')).length, 30);
  assert.ok(!left.includes(log.logName(1, A)) && left.includes(log.logName(33, A)) && left.includes('other.txt'));
});

test('r3 P1: the FAIL receipt names the step and the log file, and never any log line', () => {
  const gh = fakeGh();
  const spawn = (cmd, args, opts) => { writeSync(opts.stdio[1], output); return { status: 1 }; };
  const result = runCheck(248, { gh, git, cwd: process.cwd(), busy: () => null, spawn, terms: () => ['ZZ-PRIVATE'], waitGuard: () => null });
  assert.equal(result.status, 'FAIL');
  const saved = join(home, 'logs', log.logName(248, A));
  assert.equal(readFileSync(saved, 'utf8'), output, 'the full log stays on the owner Mac');
  const body = gh.calls[0];
  assert.equal(trust.parseAuthorCheck(body).status, 'FAIL');
  assert.match(body, /Bước lỗi: `pnpm web:test`/);
  assert.match(body, /`logs\/check-248-aaaaaaaaaaaa\.log`/);
  for (const line of output.split('\n').filter(l => l.trim() && !l.startsWith('> '))) assert.ok(!body.includes(line), `log line published: ${line}`);
  assert.doesNotMatch(body, /\/Users\/|\/tmp\//);
});

test('r3 P1: synthetic credential formats in the log never reach the receipt', () => {
  const secrets = ['API_KEY=synthetic-k1', 'DB_PASS=synthetic-p2', 'DB_PWD=synthetic-p3', 'SESSION=synthetic-s4', 'Authorization: Basic c3ludGhldGljNQ==', JSON.stringify(JSON.stringify({ api_key: 'synthetic-k6' }))];
  const gh = fakeGh();
  runCheck(263, { gh, git, cwd: process.cwd(), busy: () => null, terms: () => [], waitGuard: () => null, spawn: (c, a, opts) => { writeSync(opts.stdio[1], `> la-lanh@0.1.0 api:test /x\n${secrets.join('\n')}\n`); return { status: 1 }; } });
  for (const value of ['synthetic-k1', 'synthetic-p2', 'synthetic-p3', 'synthetic-s4', 'c3ludGhldGljNQ', 'synthetic-k6']) assert.ok(!gh.calls[0].includes(value), value);
  assert.match(gh.calls[0], /`pnpm api:test`/);
  assert.equal(log.failedStep('> x@1 not-a-step /x', ['api:test']), null, 'only steps of the check chain are named');
});

test('PASS: no log is kept and the receipt is unchanged', () => {
  const gh = fakeGh();
  const before = existsSync(join(home, 'logs')) ? readdirSync(join(home, 'logs')).length : 0;
  const result = runCheck(249, { gh, git, busy: () => null, spawn: (c, a, opts) => { writeSync(opts.stdio[1], 'ok'); return { status: 0 }; }, terms: () => [], waitGuard: () => null });
  assert.equal(result.status, 'PASS');
  assert.equal(readdirSync(join(home, 'logs')).length, before);
  assert.doesNotMatch(gh.calls[0], /Bước lỗi/);
});

test('the check waits for guarded agent tests and stays busy if they outlast 5 minutes', () => {
  let t = 0;
  const holder = () => (t < 20000 ? 4242 : null);
  assert.equal(log.waitForGuard({ holder, now: () => t, sleep: ms => { t += ms; } }), null, 'released in time');
  t = 0;
  assert.equal(log.waitForGuard({ holder: () => 4242, now: () => t, sleep: ms => { t += ms; } }), 4242);
  assert.ok(t >= log.guardWaitMs);
  let spawned = false;
  const result = runCheck(250, { gh: fakeGh(), git, busy: () => null, spawn: () => { spawned = true; return { status: 0 }; }, terms: () => [], waitGuard: () => 4242 });
  assert.equal(result.status, 'busy');
  assert.equal(spawned, false, 'pnpm check does not start while agent tests hold the guard');
});

test('the guard refuses during a check, waits while busy, and holds its lock while the command runs', () => {
  assert.equal(runGuarded('true', [], { take: () => ({ status: 'check' }), spawn: () => { throw new Error('must not run'); }, log: () => {} }), refusedCode);
  let t = 0, busyCalls = 0, released = 0;
  const take = () => ({ status: 'ok', release: () => { released++; } });
  const code = runGuarded('node', ['-v'], { take, busy: () => (busyCalls++ < 2 ? '1 pytest' : null), spawn: () => ({ status: 3 }), sleep: ms => { t += ms; }, now: () => t, log: () => {} });
  assert.equal(code, 3, 'the command exit code is passed through');
  assert.equal(released, 3, 'the lock is released after every wait and after the run');
  assert.equal(runGuarded('x', [], { take, busy: () => 'busy', spawn: () => ({ status: 0 }), sleep: ms => { t += ms; }, now: () => t, waitMs: 120000, log: () => {} }), refusedCode, 'gives up after the wait limit');
});

test('real locks: the guard steps back from check.lock, and a held guard lock blocks a second guard', () => {
  writeFileSync(log.checkLockPath(), String(process.pid));
  assert.equal(log.takeGuardLock().status, 'check');
  writeFileSync(log.checkLockPath(), '999999999');
  const first = log.takeGuardLock();
  assert.equal(first.status, 'ok');
  assert.equal(log.lockHolder(log.guardLockPath()), process.pid);
  assert.equal(log.takeGuardLock().status, 'held');
  first.release();
  assert.equal(existsSync(log.guardLockPath()), false);
});

test('r1 P1: the guard wait is bounded by the budget and the budget is read again after it', () => {
  let left = 60000, limit = null, spawned = false;
  const result = runCheck(261, { gh: fakeGh(), git, busy: () => null, terms: () => [], budget: () => left, spawn: () => { spawned = true; return { status: 0 }; }, waitGuard: ({ limitMs }) => { limit = limitMs; left = 0; return null; } });
  assert.equal(limit, 60000, 'the wait never outlasts the time left');
  assert.equal(result.status, 'refused', 'no pnpm check once the wait used the budget');
  assert.equal(spawned, false);
  left = 10 * 60000;
  runCheck(262, { gh: fakeGh(), git, busy: () => null, terms: () => [], budget: () => left, spawn: () => ({ status: 0 }), waitGuard: ({ limitMs }) => { limit = limitMs; return null; } });
  assert.equal(limit, log.guardWaitMs);
});

test('r3 P2: a dead holder\'s lock is never reclaimed, so two guards can never both hold it', () => {
  const path = join(home, 'stale.lock');
  writeFileSync(path, '999999999');
  const b = log.takeGuardLock({ path, checkHolder: () => null });
  const c = log.takeGuardLock({ path, checkHolder: () => null });
  assert.equal(b.status, 'stale');
  assert.equal(c.status, 'stale');
  assert.equal(b.pid, 999999999);
  assert.equal(readFileSync(path, 'utf8'), '999999999', 'the stale lock is left for the owner');
  const live = join(home, 'live.lock');
  const first = log.takeGuardLock({ path: live, checkHolder: () => null });
  assert.equal(first.status, 'ok');
  assert.equal(readFileSync(live, 'utf8'), String(process.pid));
  assert.equal(log.takeGuardLock({ path: live, checkHolder: () => null }).status, 'held');
  first.release();
  let said = '';
  assert.equal(runGuarded('true', [], { take: () => ({ status: 'stale', pid: 7, path: '/x/test-guard.lock' }), spawn: () => { throw new Error('must not run'); }, log: t => { said = t; } }), refusedCode);
  assert.match(said, /khóa cũ của PID 7; xóa \/x\/test-guard\.lock nếu chắc chắn/);
});

test('r3 P2: the author check ignores a dead lock older than 30 minutes for its wait, without deleting it', () => {
  const path = join(home, 'wait.lock');
  writeFileSync(path, '999999999');
  assert.equal(log.guardHolder(path), 999999999, 'a fresh dead lock still counts');
  assert.equal(log.guardHolder(path, { now: () => Date.now() + 31 * 60000 }), null);
  assert.ok(existsSync(path));
  writeFileSync(path, String(process.pid));
  assert.equal(log.guardHolder(path, { now: () => Date.now() + 99 * 60000 }), process.pid, 'a live holder always counts');
});
