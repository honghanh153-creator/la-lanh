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

test('the receipt tail is 40 lines with secrets and private terms hidden', () => {
  const tail = log.lastLines(output, ['ZZ-PRIVATE']);
  assert.equal(tail.length, 40);
  const text = tail.join('\n');
  assert.doesNotMatch(text, /ghp_|Bearer|ZZ-PRIVATE/);
  assert.match(text, /\[ẩn\]/);
  assert.match(text, /FAIL src\/a\.test\.ts/);
  for (const secret of ['export DATABASE_URL=postgres://u:p@h/db', 'see postgresql://u:pw@host/x', 'key sk-abcdefghijklmnop1234']) assert.match(log.scrubLines(secret)[0], /dòng ẩn/);
  assert.equal(log.scrubLines('plain ```fence')[0], "plain '''fence", 'a fence in the log cannot close the code block');
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

test('FAIL: the full output is kept and the receipt names the step and quotes the tail', () => {
  const gh = fakeGh();
  const spawn = (cmd, args, opts) => { writeSync(opts.stdio[1], output); return { status: 1 }; };
  const result = runCheck(248, { gh, git, busy: () => null, spawn, terms: () => ['ZZ-PRIVATE'], waitGuard: () => null });
  assert.equal(result.status, 'FAIL');
  const saved = join(home, 'logs', log.logName(248, A));
  assert.equal(readFileSync(saved, 'utf8'), output, 'the log file has the full unscrubbed output (owner Mac only, 0600)');
  const body = gh.calls[0];
  assert.equal(trust.parseAuthorCheck(body).status, 'FAIL');
  assert.match(body, /Bước lỗi: `pnpm web:test`/);
  assert.match(body, /FAIL src\/a\.test\.ts/);
  assert.match(body, /logs\/check-248-aaaaaaaaaaaa\.log/);
  assert.doesNotMatch(body, /ghp_|ZZ-PRIVATE|\/Users\//);
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
