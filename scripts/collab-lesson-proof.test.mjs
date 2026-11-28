import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { nightlyProofs, proofSummary, proveAll, proveLesson, renderProofs, runNamedTest } from './collab-lesson-proof.mjs';
import { runTick } from './collab-tick.mjs';

// A throwaway repository: a bug on main, a fix branch with its regression test, merged with a merge
// commit whose first parent is the old code. Synthetic code only.
function repoWithFix() {
  const dir = mkdtempSync(join(tmpdir(), 'proof-repo-'));
  const git = (...args) => execFileSync('/usr/bin/git', ['-C', dir, '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', ...args], { encoding: 'utf8' }).trim();
  git('init', '-q', '-b', 'main');
  writeFileSync(join(dir, 'lib.mjs'), 'export const add = (a, b) => a - b;\n');
  git('add', '.'); git('commit', '-q', '-m', 'bug');
  git('checkout', '-q', '-b', 'fix');
  writeFileSync(join(dir, 'lib.mjs'), 'export const add = (a, b) => a + b;\n');
  writeFileSync(join(dir, 'helper.mjs'), 'export const two = 2;\n');
  writeFileSync(join(dir, 'lib.test.mjs'), [
    "import assert from 'node:assert/strict';",
    "import test from 'node:test';",
    "import { add } from './lib.mjs';",
    "test('L99: add adds', () => { assert.equal(add(1, 1), 2); });",
    "test('#100: unrelated', () => { assert.ok(true); });",
  ].join('\n'));
  writeFileSync(join(dir, 'new.test.mjs'), [
    "import assert from 'node:assert/strict';",
    "import test from 'node:test';",
    "import { two } from './helper.mjs';",
    "test('L98: helper exists', () => { assert.equal(two, 2); });",
  ].join('\n'));
  git('add', '.'); git('commit', '-q', '-m', 'fix');
  git('checkout', '-q', 'main');
  git('merge', '-q', '--no-ff', '-m', 'merge fix', 'fix');
  return { dir, merge: git('rev-parse', 'HEAD') };
}
const noFetch = (cmd, args, opts) => (args.includes('fetch') ? '' : execFileSync(cmd, args, opts));

test('research item 4: a lesson is proved only when its test fails on the old code and passes on the merge', () => {
  const { dir, merge } = repoWithFix();
  const gh = { json: () => ({ mergeCommit: { oid: merge }, state: 'MERGED' }) };
  const lesson = (name, file = 'lib.test.mjs') => ({ id: 'L99', status: 'done', test: { file, name }, closedBy: { pr: 9 } });
  const opts = { gh, dir, run: noFetch };
  assert.deepEqual(proveLesson(lesson('L99: add adds'), opts).result, 'proved');
  assert.equal(proveLesson(lesson('#100: unrelated'), opts).result, 'not-red', 'a test that also passes on the old code proves nothing');
  assert.equal(proveLesson(lesson('L98: helper exists', 'new.test.mjs'), opts).result, 'proved-load', 'red only because the file could not load');
  assert.equal(proveLesson(lesson('L97: not written yet'), opts).result, 'not-at-merge', 'the closing PR did not have this test');
  assert.equal(proveLesson({ id: 'L1', test: { file: 'apps/api/tests/x.py', name: 'y' }, closedBy: { pr: 1 } }, opts).result, 'unsupported', 'a Python test can never be run here: a final answer, not a retry');
  assert.equal(proveLesson(lesson('L99: add adds'), { ...opts, gh: { json: () => ({ mergeCommit: null }) } }).result, 'unknown', 'not merged');
  assert.deepEqual(execFileSync('/usr/bin/git', ['-C', dir, 'worktree', 'list'], { encoding: 'utf8' }).trim().split('\n').length, 1, 'temporary worktrees are removed');
});

test('research item 4: proofs are kept per evidence, at most one a tick and six a night, and counted on the board', () => {
  const path = join(mkdtempSync(join(tmpdir(), 'proofs-')), 'lesson-proofs.json');
  const reg = { lessons: [
    { id: 'L1', status: 'done', test: { file: 'a.test.mjs', name: 'L1: a' }, closedBy: { pr: 1 } },
    { id: 'L2', status: 'done', test: { file: 'b.test.mjs', name: 'L2: b' }, closedBy: { pr: 2 } },
    { id: 'L3', status: 'open', test: { file: 'c.test.mjs', name: 'L3: c' } },
  ] };
  const results = { L1: 'proved', L2: 'not-red' };
  const prove = l => ({ result: results[l.id] });
  assert.deepEqual(proveAll({ register: () => reg, prove, path, max: 1 }).map(p => p.id), ['L1']);
  assert.deepEqual(proveAll({ register: () => reg, prove, path, max: 5 }).map(p => p.id), ['L2'], 'a proved lesson is not run again');
  const proofs = JSON.parse(execFileSync('cat', [path], { encoding: 'utf8' }));
  const line = renderProofs(proofSummary(reg, proofs));
  assert.equal(line, 'Bài học có bằng chứng đỏ → xanh: 1/2; chưa kiểm 0; test không đỏ trên code cũ: L2.');
  const statePath = join(mkdtempSync(join(tmpdir(), 'proof-night-')), 'run.json');
  let calls = 0;
  const nightly = status => nightlyProofs({ status, statePath, nowMs: Date.parse('2026-11-21T18:00:00Z'), prove: () => { calls += 1; return []; } });
  assert.equal(nightly('ran'), null, 'never while the loop works');
  for (let i = 0; i < 8; i += 1) nightly('closed');
  assert.equal(calls, 6, 'six lessons a night at most');
});

test('#860 r1: a lesson that cannot be proved never holds up the lessons after it', () => {
  const path = join(mkdtempSync(join(tmpdir(), 'proofs-')), 'lesson-proofs.json');
  const reg = { lessons: [
    { id: 'L46', status: 'done', test: { file: 'apps/api/tests/x.py', name: 'test_x' }, closedBy: { pr: 46 } },
    { id: 'L47', status: 'done', test: { file: 'a.test.mjs', name: 'L47: a' }, closedBy: { pr: 47 } },
    { id: 'L48', status: 'done', test: { file: 'b.test.mjs', name: 'L48: b' }, closedBy: { pr: 48 } },
    { id: 'L49', status: 'done', test: { file: 'c.test.mjs', name: 'L49: c' }, closedBy: { pr: 49 } },
  ] };
  // L46 goes through the real proveLesson (Python: unsupported); L47 cannot be read tonight (unknown).
  const prove = l => (l.id === 'L46' ? proveLesson(l, { gh: { json: () => { throw new Error('unused'); } } }) : l.id === 'L47' ? { result: 'unknown', why: 'không đọc được PR' } : { result: 'proved' });
  const at = hours => new Date(Date.parse('2026-11-27T17:00:00Z') + hours * 3600000);
  const tick = hours => proveAll({ register: () => reg, prove, path, max: 1, at: at(hours) }).map(p => `${p.id}:${p.result}`);
  assert.deepEqual([tick(0), tick(0.1), tick(0.2), tick(0.3), tick(0.4)], [['L46:unsupported'], ['L47:unknown'], ['L48:proved'], ['L49:proved'], []],
    'each tick moves on to a lesson not tried yet');
  assert.deepEqual(tick(25), ['L47:unknown'], 'an unknown result is tried again a day later; an unsupported one never is');
  const reg2 = { lessons: [...reg.lessons, { id: 'L50', status: 'done', test: { file: 'd.test.mjs', name: 'L50: d' }, closedBy: { pr: 50 } }] };
  assert.deepEqual(proveAll({ register: () => reg2, prove, path, max: 1, at: at(50) }).map(p => p.id), ['L50'], 'a lesson not tried yet goes before a retry');
  const line = renderProofs(proofSummary(reg, JSON.parse(execFileSync('cat', [path], { encoding: 'utf8' }))));
  assert.equal(line, 'Bài học có bằng chứng đỏ → xanh: 2/4; chưa kiểm 1; không kiểm được 1.');
});

test('#860 r1: green needs the test process to end well, not only a passing line', () => {
  const tap = 'TAP version 13\n# Subtest: L99: add adds\nok 1 - L99: add adds\n  ---\n  duration_ms: 1\n  ...\n1..1\n';
  const named = r => runNamedTest('/nonexistent', 'lib.test.mjs', 'L99: add adds', { spawn: () => r });
  assert.equal(named({ stdout: tap, status: 0, signal: null }), 'pass');
  assert.equal(named({ stdout: tap, status: 1, signal: null }), 'broken', 'a hook failed after the passing line');
  assert.equal(named({ stdout: tap, status: null, signal: 'SIGTERM' }), 'broken');
  assert.equal(named({ stdout: tap, status: 0, signal: null, error: new Error('ETIMEDOUT') }), 'broken');
  assert.equal(named({ stdout: '', status: null, signal: 'SIGTERM', error: new Error('ETIMEDOUT') }), 'error', 'a run that was cut short says nothing about the old code');
  assert.equal(named({ stdout: 'TAP version 13\nok 1 - L99: add adds # SKIP test name does not match pattern\n1..1\n', status: 0, signal: null }), 'missing', 'a skipped test did not run');
  const { dir, merge } = repoWithFix();
  const lesson = { id: 'L99', status: 'done', test: { file: 'lib.test.mjs', name: 'L99: add adds' }, closedBy: { pr: 9 } };
  const opts = { gh: { json: () => ({ mergeCommit: { oid: merge } }) }, dir, run: noFetch };
  const runs = results => { const left = [...results]; return () => left.shift(); };
  assert.equal(proveLesson(lesson, { ...opts, test: runs(['fail', 'broken']) }).result, 'not-green');
  assert.equal(proveLesson(lesson, { ...opts, test: runs(['broken', 'pass']) }).result, 'not-red', 'the named test passed on the old code');
  assert.equal(proveLesson(lesson, { ...opts, test: runs(['error', 'pass']) }).result, 'unknown', 'tried again later');
});

test('#860 r1: a shortened test name is resolved to the one full name it belongs to', () => {
  const { dir, merge } = repoWithFix();
  const opts = { gh: { json: () => ({ mergeCommit: { oid: merge } }) }, dir, run: noFetch };
  const lesson = name => ({ id: 'L99', status: 'done', test: { file: 'lib.test.mjs', name }, closedBy: { pr: 9 } });
  assert.equal(proveLesson(lesson('add adds'), opts).result, 'proved', 'a fragment of one test name');
  assert.equal(proveLesson(lesson('L99:'), opts).result, 'proved');
  assert.equal(proveLesson(lesson('a'), opts).result, 'ambiguous', 'a fragment of two test names proves nothing');
  const reg = { lessons: [lesson('a')] };
  assert.equal(renderProofs(proofSummary(reg, { 'L99:lib.test.mjs:a:9': { result: 'ambiguous' } })),
    'Bài học có bằng chứng đỏ → xanh: 0/1; chưa kiểm 0; tên test khớp nhiều test: L99.');
});

test('research item 4: the tick runs the proofs and shows the proof line; a failing proof never fails the tick', () => {
  const seen = [];
  const given = runTick({ raw: () => '', json: () => [] }, () => [], { run: g => ({ ...g, status: 'closed' }), gapNote: () => null, areaNote: () => null, probe: () => [], receipt: () => {},
    receipts: () => 'r', proofs: o => { seen.push(o.status); return []; }, proofLine: () => 'Bài học có bằng chứng đỏ → xanh: 3/57.' });
  assert.deepEqual(seen, ['closed']);
  assert.ok(given.health().includes('Bài học có bằng chứng đỏ → xanh: 3/57.'));
  const after = runTick({ raw: () => '', json: () => [] }, () => [], { run: () => ({ status: 'closed' }), gapNote: () => null, areaNote: () => null, probe: () => [], receipt: () => {}, proofs: () => { throw new Error('git'); } });
  assert.equal(after.status, 'closed');
});
