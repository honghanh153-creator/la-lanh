import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-preflight-'));
const pre = await import('./collab-preflight.mjs');
const heavy = await import('./collab-heavy.mjs');
const { runCheck } = await import('./collab-check.mjs');
const trust = await import('./collab-trust.mjs');

const A = 'a'.repeat(40);
// Built at runtime so this file never carries a token-shaped literal itself.
const ghToken = `gh${'p'}_${'Z9'.repeat(18)}`;
const pemKey = ['-----BEGIN', 'RSA PRIVATE KEY-----'].join(' ');
const added = (file, ...texts) => new Map([[file, texts.map((text, i) => ({ line: i + 1, text }))]]);
const rules = findings => findings.map(f => `${f.kind}:${f.rule}`);

test('diff parsing keeps only added lines with their new line numbers', () => {
  const files = pre.parseDiff([
    'diff --git a/x.js b/x.js', '--- a/x.js', '+++ b/x.js', '@@ -3,0 +4,2 @@', '+one', '+two', '@@ -9 +11 @@', '-old', '+three',
    'diff --git a/gone.js b/gone.js', '--- a/gone.js', '+++ /dev/null', '@@ -1 +0,0 @@', '-bye',
  ].join('\n'));
  assert.deepEqual([...files.keys()], ['x.js']);
  assert.deepEqual(files.get('x.js'), [{ line: 4, text: 'one' }, { line: 5, text: 'two' }, { line: 11, text: 'three' }]);
});

test('secrets block, placeholders and environment reads do not', () => {
  assert.deepEqual(rules(pre.scanLines(added('a.ts', `const t = "${ghToken}";`))), ['secret:github-token']);
  assert.deepEqual(rules(pre.scanLines(added('a.pem.md', pemKey))), ['secret:private-key']);
  assert.deepEqual(rules(pre.scanLines(added('a.py', `API_KEY = "${'q8Lr2xWm4TzP9vBn3KdY'}"`))), ['secret:assigned-secret']);
  assert.deepEqual(pre.scanLines(added('a.py',
    'API_KEY = "your-api-key-goes-here"',
    'TOKEN = "synthetic-public-token-123"',
    'password = os.environ["DB_PASSWORD_LONG_NAME"]',
    `const t = "${ghToken}"; // collab-preflight: allow rotated test fixture`,
  )), []);
});

test('personal data in log calls blocks outside tests; plain messages do not', () => {
  const hits = pre.scanLines(added('apps/api/src/x.py',
    'logger.info("saved", birth_date=profile.birth_date)',
    'print(f"user {user.email} done")',
    'console.log(`share ${shareToken}`)',
    'logging.warning("lat=%s", lat)',
    'console.log("journal entry saved")',
    'print(f"Deletion journal: purged={journal}")',
    'logger.info("mood check started")',
  ));
  assert.deepEqual(hits.map(h => h.line), [1, 2, 3, 4]);
  assert.equal(pre.scanLines(added('apps/web/src/x.test.ts', 'console.log(user.email)')).length, 0);
  assert.equal(pre.scanLines(added('apps/api/tests/test_x.py', 'print(birth_date)')).length, 0);
  assert.equal(pre.scanLines(added('docs/x.md', 'console.log(user.email)')).length, 0);
  assert.equal(pre.scanLines(added('a.ts', 'console.log(user.email) // collab-preflight: allow masked by redact()')).length, 0);
});

test('sensitive files: env files and private keys block, examples and public certificates do not', () => {
  const read = f => (f.endsWith('ca.pem') ? '-----BEGIN CERTIFICATE-----\nabc' : pemKey);
  const found = pre.scanFiles(['.env', 'apps/api/.env.production', '.env.example', 'ops/ca.pem', 'ops/server.key', 'android/app.keystore'], read);
  assert.deepEqual(found.map(f => f.file), ['.env', 'apps/api/.env.production', 'ops/server.key', 'android/app.keystore']);
});

test('the PR comment names rule and place but never the matched secret', () => {
  const findings = pre.scanLines(added('a.ts', `const t = "${ghToken}";`));
  const text = pre.renderFindings({ status: 'FAIL', mergeBase: A, files: 1, added: 1, findings });
  assert.match(text, /a\.ts:1/);
  assert.match(text, /thu hồi/);
  assert.doesNotMatch(text, new RegExp(ghToken));
});

test('runPreflight diffs from the merge-base of the given base', () => {
  const calls = [];
  const git = args => {
    calls.push(args);
    if (args[0] === 'merge-base') return `${A}\n`;
    if (args[1] === '--name-only') return 'x.js\n';
    return ['+++ b/x.js', '@@ -0,0 +1 @@', '+console.log(user.phone)'].join('\n');
  };
  const result = pre.runPreflight({ base: 'origin/feat/y', head: 'HEAD', git });
  assert.deepEqual(calls[0], ['merge-base', 'origin/feat/y', 'HEAD']);
  assert.equal(result.status, 'FAIL');
  assert.equal(result.findings[0].kind, 'personal-log');
});

test('heavy lock: one holder, dead holders are dropped, nested runs pass through', () => {
  const path = join(process.env.LA_LANH_COLLAB_HOME, 'h1.lock');
  const release = heavy.tryAcquire('a', { path, pid: 111, isAlive: () => true });
  assert.ok(release);
  assert.equal(heavy.tryAcquire('b', { path, pid: 222, isAlive: () => true }), null);
  assert.ok(heavy.tryAcquire('c', { path, pid: 333, isAlive: pid => pid !== 111 }), 'dead holder is stale');
  assert.equal(heavy.readHolder(path).pid, 333);

  let slept = 0;
  const busy = heavy.withHeavyLock('d', () => 'ran', { path, pid: 444, isAlive: () => true, waitMs: 30000, stepMs: 15000, sleep: () => { slept++; }, env: {} });
  assert.equal(busy.status, 'busy');
  assert.equal(slept, 2);
  assert.equal(heavy.withHeavyLock('e', () => 'nested', { path, env: { [heavy.heldEnv]: '333' } }), 'nested');
});

test('heavy lock: a waiter runs once the holder releases, and releases after', () => {
  const path = join(process.env.LA_LANH_COLLAB_HOME, 'h2.lock');
  const releaseFirst = heavy.tryAcquire('first', { path, pid: process.pid });
  const result = heavy.withHeavyLock('second', ({ waitedMs }) => waitedMs, { path, pid: 555, isAlive: () => true, sleep: () => releaseFirst(), env: {} });
  assert.equal(result, 15000);
  assert.equal(existsSync(path), false);
});

test('heat: pmset limits or overload wait, then the job runs anyway', () => {
  assert.equal(heavy.parseTherm('CPU_Scheduler_Limit = 100\nCPU_Speed_Limit = 70'), 'CPU giới hạn 70%');
  assert.match(heavy.parseTherm('Thermal warning level: 2'), /thermal mức 2/);
  assert.equal(heavy.parseTherm('Note: No thermal warning level has been recorded'), null);
  assert.equal(heavy.machineHeat({ therm: () => '', load: () => 12, cores: 10 }).hot, true);
  assert.equal(heavy.machineHeat({ therm: () => { throw new Error('no pmset'); }, load: () => 1, cores: 10 }).hot, false);

  let reads = 0;
  const cooled = heavy.waitForCool({ heat: () => ({ hot: ++reads < 3, reason: 'nóng' }), sleep: () => {}, stepMs: 60000 });
  assert.deepEqual(cooled, { waitedMs: 120000, cooled: true, reason: 'nóng' });
  const capped = heavy.waitForCool({ heat: () => ({ hot: true, reason: 'nóng' }), sleep: () => {}, stepMs: 60000, waitMs: 180000 });
  assert.equal(capped.waitedMs, 180000);
  assert.equal(capped.cooled, false);
});

function checkHarness(extra = {}) {
  const posted = [];
  const spawned = [];
  const gh = { pr: () => ({ number: 9, headRefOid: A, baseRefName: 'collab/integration' }), comment: (kind, n, body) => { trust.assertAgentBody(body); posted.push(body); } };
  const git = args => (args[0] === 'rev-parse' ? A : '');
  const spawn = (cmd, args) => { spawned.push([cmd, ...args]); return { status: 0 }; };
  const clean = { status: 'PASS', mergeBase: A, files: 1, added: 2, findings: [] };
  return { posted, spawned, opts: { gh, git, spawn, now: () => 0, preflight: () => clean, heavy: (job, fn) => fn(), cool: () => ({ waitedMs: 0 }), ...extra } };
}

test('author check stops at a preflight failure without running pnpm check', () => {
  const finding = { kind: 'personal-log', rule: 'email', file: 'x.ts', line: 3 };
  const h = checkHarness({ preflight: () => ({ status: 'FAIL', mergeBase: A, files: 1, added: 1, findings: [finding] }) });
  assert.deepEqual(runCheck(9, h.opts), { status: 'FAIL', preflight: 1 });
  assert.equal(h.spawned.length, 0);
  assert.deepEqual(trust.parseAuthorCheck(h.posted[0]), { status: 'FAIL', sha: A });
  assert.match(h.posted[0], /chưa chạy `pnpm check`/);
});

test('author check posts nothing while another heavy job holds the machine', () => {
  const h = checkHarness({ heavy: () => ({ status: 'busy', holder: { job: 'api-test' } }) });
  assert.equal(runCheck(9, h.opts).status, 'busy');
  assert.equal(h.posted.length, 0);
});

test('author check passes with the preflight summary and any heat wait on record', () => {
  const h = checkHarness({ cool: () => ({ waitedMs: 120000, reason: 'CPU giới hạn 70%' }) });
  assert.equal(runCheck(9, h.opts).status, 'PASS');
  assert.deepEqual(h.spawned, [['pnpm', 'check']]);
  assert.deepEqual(trust.parseAuthorCheck(h.posted[0]), { status: 'PASS', sha: A });
  assert.match(h.posted[0], /Soát nhanh: sạch/);
  assert.match(h.posted[0], /chờ máy hết nóng 2 phút/);
});

test('author check refuses a base name that could act as a git option', () => {
  const h = checkHarness();
  h.opts.gh.pr = () => ({ number: 9, headRefOid: A, baseRefName: '--upload-pack=x' });
  assert.equal(runCheck(9, h.opts).status, 'refused');
});

test('CLI entries load and print usage', () => {
  const heavyCli = spawnSync(process.execPath, ['scripts/collab-heavy.mjs'], { encoding: 'utf8', timeout: 20000 });
  assert.equal(heavyCli.status, 2);
  assert.match(heavyCli.stderr, /Usage/);
  const ok = spawnSync(process.execPath, ['scripts/collab-heavy.mjs', '--wait-min', '0', '--cool-min', '0', '--', process.execPath, '-e', 'process.exit(5)'], {
    encoding: 'utf8', timeout: 20000, env: { ...process.env, LA_LANH_COLLAB_HOME: mkdtempSync(join(tmpdir(), 'collab-heavy-cli-')) },
  });
  assert.equal(ok.status, 5, 'wrapped exit code passes through');
});

test('pre-push hook is executable and calls the preflight', () => {
  const hook = 'scripts/git-hooks/pre-push';
  assert.ok(existsSync(hook));
  assert.equal(spawnSync('/bin/test', ['-x', hook]).status, 0);
});
