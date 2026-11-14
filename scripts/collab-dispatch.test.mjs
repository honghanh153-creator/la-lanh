import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { dispatch, hookCanary, preflightWorkspace } from './collab-dispatch.mjs';
import { publishBatch, registryRel } from './codex-copy-review.mjs';

const git = (cwd, ...args) => String(execFileSync('/usr/bin/git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })).trim();
const ident = ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid'];

// A real repository with one commit and a worker worktree on its own branch.
function setup(branch = 'agent/claude/x') {
  const root = realpathSync(mkdtempSync(join(tmpdir(), 'dispatch-')));
  const repo = join(root, 'repo');
  mkdirSync(join(repo, 'apps/api/app/domains/content'), { recursive: true });
  git(repo, 'init', '-q', '-b', 'main');
  writeFileSync(join(repo, registryRel), '{"entries":[]}\n');
  git(repo, 'add', '.');
  git(repo, ...ident, 'commit', '-q', '-m', 'init');
  const work = join(root, 'work');
  git(repo, 'worktree', 'add', '-q', '-b', branch, work);
  return { root, repo, work, head: git(work, 'rev-parse', 'HEAD') };
}
const tools = { which: () => true };
const okHook = { canary: () => null };
const logOf = path => (existsSync(path) ? readFileSync(path, 'utf8').trim().split('\n').map(l => JSON.parse(l)) : []);
const state = dir => ({ head: git(dir, 'rev-parse', 'HEAD'), status: git(dir, 'status', '--porcelain', '--untracked-files=all') });

test('failed preflight never invokes the worker', () => {
  const cases = [
    ['wrong branch', s => ({ dir: s.work, branch: 'agent/claude/y' }), 'wrong-branch'],
    ['detached HEAD', s => { git(s.work, 'checkout', '-q', '--detach'); return { dir: s.work, branch: 'agent/claude/x' }; }, 'detached-head'],
    ['missing tool', s => ({ dir: s.work, branch: 'agent/claude/x', which: tool => tool !== 'gh' }), 'missing-tool:gh'],
    ['shared clone', s => ({ dir: s.work, branch: 'agent/claude/x', shared: [s.work] }), 'shared-checkout'],
    ['symlink alias of a worktree', s => { symlinkSync(s.work, join(s.root, 'alias')); return { dir: join(s.root, 'alias'), branch: 'agent/claude/x' }; }, 'dir-is-symlink'],
    ['subdirectory, not the worktree root', s => ({ dir: join(s.work, 'apps'), branch: 'agent/claude/x' }), 'not-worktree-root'],
    ['dirty directory', s => { writeFileSync(join(s.work, 'scratch.txt'), 'x'); return { dir: s.work, branch: 'agent/claude/x' }; }, 'dirty'],
    ['inactive hook', s => ({ dir: s.work, branch: 'agent/claude/x', canary: () => 'hook-missing' }), 'hook-missing'],
    ['hook checker absent', s => ({ dir: s.work, branch: 'agent/claude/x', canary: null }), 'hook-unchecked'],
    ['protected branch', s => ({ dir: s.work, branch: 'collab/integration' }), 'branch-not-allowed'],
    ['moved off the reviewed commit', s => ({ dir: s.work, branch: 'agent/claude/x', expectHead: 'f'.repeat(40) }), 'head-moved'],
  ];
  for (const [name, arrange, code] of cases) {
    const s = setup();
    const opts = { ...tools, ...okHook, ...arrange(s) };
    const before = state(s.work);
    const log = join(s.root, 'dispatch.jsonl');
    let calls = 0;
    const r = dispatch({ ...opts, log, worker: () => { calls += 1; } });
    assert.equal(r.status, 'FAIL', name);
    assert.ok(r.reasons.includes(code), `${name}: ${r.reasons.join(',')}`);
    assert.equal(calls, 0, `${name}: the worker never runs`);
    if (name !== 'dirty directory') assert.deepEqual(state(s.work), before, `${name}: nothing written in the worktree`);
    assert.deepEqual(logOf(log).map(l => [l.status, l.reasons.includes(code)]), [['FAIL', true]], `${name}: one log line outside the worktree`);
  }
});

test('a passing preflight runs the worker once, on the real path', () => {
  const s = setup();
  const log = join(s.root, 'dispatch.jsonl');
  const seen = [];
  const r = dispatch({ dir: s.work, branch: 'agent/claude/x', expectHead: s.head, ...tools, ...okHook, log, worker: at => { seen.push(at); return 7; } });
  assert.deepEqual(r, { status: 'PASS', result: 7 });
  assert.deepEqual(seen, [s.work]);
  assert.equal(logOf(log)[0].status, 'PASS');
});

test('two dispatches into one worktree: only one worker runs, also through a parent symlink', () => {
  const s = setup();
  const parent = join(mkdtempSync(join(tmpdir(), 'dispatch-alias-')), 'parent');
  symlinkSync(s.root, parent);
  const alias = join(parent, 'work');
  const log = join(s.root, 'dispatch.jsonl');
  const inner = [];
  dispatch({ dir: s.work, branch: 'agent/claude/x', ...tools, ...okHook, log, worker: () => {
    inner.push(dispatch({ dir: s.work, branch: 'agent/claude/x', ...tools, ...okHook, log, worker: () => { throw new Error('second worker ran'); } }));
    inner.push(dispatch({ dir: alias, branch: 'agent/claude/x', ...tools, ...okHook, log, worker: () => { throw new Error('alias worker ran'); } }));
  } });
  assert.deepEqual(inner.map(r => r.reasons), [['busy'], ['busy']]);
  assert.equal(dispatch({ dir: s.work, branch: 'agent/claude/x', ...tools, ...okHook, log, worker: () => 'free again' }).result, 'free again', 'the lock is released');
});

// The canary: the installed hook must block a synthetic term in a scratch repo.
function hookWith(script) {
  const dir = mkdtempSync(join(tmpdir(), 'hooks-'));
  writeFileSync(join(dir, 'pre-push'), `#!/bin/bash\n${script}\n`);
  chmodSync(join(dir, 'pre-push'), 0o755);
  return { verifyHook: () => [], hooksDir: () => dir };
}
const guardWith = text => { const f = join(mkdtempSync(join(tmpdir(), 'guard-')), 'private-guard.txt'); writeFileSync(f, text); return f; };
const blocking = 'cat >/dev/null; term="$(head -1 "$LA_LANH_COLLAB_HOME/private-guard.txt")"; if grep -rq "$term" --exclude-dir=.git .; then echo "private-guard: chặn, dữ liệu riêng tư ở note.txt:1"; exit 1; fi; echo "private-guard: ok"';

test('hook canary: only a hook that really blocks passes, and no term is shown', () => {
  const opsDir = mkdtempSync(join(tmpdir(), 'ops-'));
  const real = guardWith('# list\nreal-term\n');
  const run = (mod, guardFile = real, timeoutMs = 5000) => hookCanary('/unused', { hooksModule: mod, opsDir, guardFile, timeoutMs });
  assert.equal(run(hookWith(blocking)), null);
  assert.equal(run({ verifyHook: () => ['chưa cài hook trước push'], hooksDir: () => '' }), 'hook-missing');
  assert.equal(run({ verifyHook: () => ['hook trước push khác bản chuẩn, cần cài lại'], hooksDir: () => '' }), 'hook-not-standard');
  assert.equal(run(hookWith(blocking), guardWith('# only comments\n')), 'guard-list-empty', 'an empty list prints ok, so it is not a working guard');
  assert.equal(run(hookWith(blocking), join(opsDir, 'missing.txt')), 'guard-list-empty');
  assert.equal(run(hookWith('cat >/dev/null; echo "private-guard: ok"; exit 0')), 'canary-not-blocked');
  assert.equal(run(hookWith('cat >/dev/null; echo "private-guard: chặn"; exit 0')), 'canary-not-blocked', 'blocked text with exit 0 is not a block');
  assert.equal(run(hookWith('cat >/dev/null; echo "private-guard: ok"; exit 1')), 'canary-not-blocked', 'a failing hook that did not name a block');
  assert.equal(run(hookWith('cat >/dev/null; sleep 5'), real, 300), 'canary-timeout');
  assert.equal(run(hookWith('cat >/dev/null; cat "$LA_LANH_COLLAB_HOME/private-guard.txt"; echo "private-guard: chặn"; exit 1')), 'canary-leaks-term');
});

test('copy batch: a failed check writes nothing and runs no git, uv or gh', () => {
  const s = setup('agent/claude/copy-batch-20261114-1000-abc');
  writeFileSync(join(s.work, 'left-over.txt'), 'x');
  const before = readFileSync(join(s.work, registryRel), 'utf8');
  const calls = [];
  const run = (cmd, args) => { calls.push([cmd, ...args]); return ''; };
  const registry = { entries: [{ id: 'a', status: 'approved' }] };
  assert.throws(() => publishBatch(registry, 'body', '2026-11-14', 'agent/claude/copy-batch-20261114-1000-abc', s.work, s.root, run, { base: s.head, gate: tools }), /kiểm trước khi ghi trượt: dirty/);
  assert.deepEqual(calls, []);
  assert.equal(readFileSync(join(s.work, registryRel), 'utf8'), before, 'registry untouched');
  assert.equal(git(s.work, 'rev-parse', 'HEAD'), s.head);
  assert.equal(git(s.work, 'diff', '--cached', '--name-only'), '', 'index untouched');
  assert.throws(() => publishBatch(registry, 'body', '2026-11-14', 'agent/claude/x', s.repo, s.root, run, { base: s.head, gate: tools }), /branch-not-allowed|wrong-branch/);
  assert.deepEqual(calls, []);
});

test('copy batch: a clean worktree on the reviewed commit publishes once', () => {
  const branch = 'agent/claude/copy-batch-20261114-1000-def';
  const s = setup(branch);
  const calls = [];
  const run = (cmd, args) => { calls.push([cmd, ...args]); return cmd === 'gh' ? 'https://example.test/pr/9\n' : ''; };
  const url = publishBatch({ entries: [{ id: 'a', status: 'approved' }] }, 'body', '2026-11-14', branch, s.work, s.root, run, { base: s.head, gate: tools });
  assert.equal(url, 'https://example.test/pr/9');
  assert.deepEqual(calls.map(c => c[0] === 'git' ? `git ${c[1] === '-c' ? 'commit' : c[1]}` : c[0]), ['uv', 'git add', 'git commit', 'git push', 'gh']);
  assert.match(readFileSync(join(s.work, registryRel), 'utf8'), /"approved"/);
});
