import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'conflict-heal-'));
const { ownerLogin } = await import('./collab-trust.mjs');
const { syncWithIntegration } = await import('./collab-heal.mjs');
const { healCandidates, healConflicts, lessonsFile, resolveRuleConflicts, unionLessons } = await import('./collab-conflict-heal.mjs');

const L = (id, extra = {}) => ({ id, title: `bài ${id}`, status: 'open', ...extra });
const doc = lessons => `${JSON.stringify({ version: 1, lessons }, null, 1)}\n`;

test('L74: the lessons rule keeps both sides\' new lessons and a one-sided edit; a two-sided clash is left to Claude', () => {
  const base = doc([L('L01')]);
  const merged = JSON.parse(unionLessons(base, doc([L('L01'), L('L03')]), doc([L('L01'), L('L02')])));
  assert.deepEqual(merged.lessons.map(l => l.id), ['L01', 'L02', 'L03'], 'integration order first, then the branch\'s new lesson');
  assert.equal(merged.version, 1);
  const closed = JSON.parse(unionLessons(base, doc([L('L01'), L('L03')]), doc([L('L01', { status: 'done' }), L('L02')])));
  assert.equal(closed.lessons[0].status, 'done', 'an edit on one side only is kept');
  assert.equal(unionLessons(base, doc([L('L01', { status: 'x' })]), doc([L('L01', { status: 'y' })])), null, 'both sides changed one lesson differently');
  assert.equal(unionLessons(base, doc([L('L02', { title: 'a' })]), doc([L('L02', { title: 'b' })])), null, 'the same new id with different text');
  assert.equal(unionLessons(base, '{not json', doc([])), null);
  assert.equal(unionLessons(base, doc([L('L01'), L('L01')]), doc([L('L01')])), null, 'a duplicate id');
  assert.deepEqual(JSON.parse(unionLessons(base, doc([L('L01'), L('L03')]), doc([]))).lessons.map(l => l.id), ['L03'], 'a lesson removed upstream and untouched here stays removed');
});

// A real repository: origin (bare) with collab/integration, a PR branch that adds a lesson, and
// integration moving on with another lesson, as it does every time a lesson PR merges.
function repoPair({ otherFile = false } = {}) {
  const root = mkdtempSync(join(tmpdir(), 'heal-repo-'));
  const g = (cwd, ...args) => execFileSync('/usr/bin/git', ['-c', 'user.name=t', '-c', 'user.email=t@example.com', '-c', 'init.defaultBranch=main', ...args], { cwd, encoding: 'utf8' }).trim();
  const origin = join(root, 'origin.git');
  mkdirSync(origin);
  g(origin, 'init', '--bare', '-q');
  const work = join(root, 'work');
  g(root, 'clone', '-q', origin, work);
  mkdirSync(join(work, 'scripts'));
  const put = (p, text) => writeFileSync(join(work, p), text);
  put(lessonsFile, doc([L('L01')]));
  put('scripts/a.mjs', 'export const a = 1;\n');
  g(work, 'add', '-A'); g(work, 'commit', '-qm', 'base'); g(work, 'push', '-q', 'origin', 'HEAD:refs/heads/collab/integration');
  g(work, 'checkout', '-qb', 'agent/claude/x');
  put(lessonsFile, doc([L('L01'), L('L03')]));
  if (otherFile) put('scripts/a.mjs', 'export const a = 3;\n');
  g(work, 'commit', '-qam', 'branch lesson'); g(work, 'push', '-q', 'origin', 'agent/claude/x');
  g(work, 'fetch', '-q', 'origin');
  g(work, 'checkout', '-qb', 'int', 'origin/collab/integration');
  put(lessonsFile, doc([L('L01'), L('L02')]));
  if (otherFile) put('scripts/a.mjs', 'export const a = 2;\n');
  g(work, 'commit', '-qam', 'integration lesson'); g(work, 'push', '-q', 'origin', 'HEAD:refs/heads/collab/integration');
  g(work, 'checkout', '-q', '--detach', 'origin/agent/claude/x');
  g(work, 'fetch', '-q', 'origin');
  const git = (args, ms = 60000) => String(execFileSync('/usr/bin/git', args, { cwd: work, encoding: 'utf8', timeout: ms })).trim();
  return { work, origin, git, g, write: (f, t) => writeFileSync(join(work, f), t) };
}
const pr = { number: 9, headRefName: 'agent/claude/x' };

test('L74: a branch that only clashes on the lessons file is merged by the machine and pushed, not sent to Claude', () => {
  const { work, origin, git, write } = repoPair();
  const posted = [];
  const gh = { comment: (...a) => posted.push(a) };
  assert.deepEqual(syncWithIntegration(pr, { git, gh }), { status: 'conflict', turn: 'claude-fix', reason: 'xung đột với collab/integration' }, 'without the rule: a Claude fix (the old wake-up)');
  const out = syncWithIntegration(pr, { git, gh, resolve: () => resolveRuleConflicts({ git, write }) });
  assert.equal(out.status, 'synced');
  assert.deepEqual(out.resolved, [lessonsFile]);
  const pushed = execFileSync('/usr/bin/git', ['show', `agent/claude/x:${lessonsFile}`], { cwd: origin, encoding: 'utf8' });
  assert.deepEqual(JSON.parse(pushed).lessons.map(l => l.id), ['L01', 'L02', 'L03'], 'both lessons kept on the pushed branch');
  assert.equal(execFileSync('/usr/bin/git', ['rev-parse', 'agent/claude/x'], { cwd: origin, encoding: 'utf8' }).trim(), out.head);
  assert.match(posted[0][2], /chỉ xung đột ở scripts\/collab-lessons\.json/);
  assert.equal(readFileSync(join(work, lessonsFile), 'utf8').includes('<<<<'), false);
});

test('L74: a conflict in any other file is aborted and left to Claude as before', () => {
  const { git, write } = repoPair({ otherFile: true });
  const out = syncWithIntegration(pr, { git, gh: { comment: () => assert.fail('nothing is posted') }, resolve: () => resolveRuleConflicts({ git, write }) });
  assert.equal(out.status, 'conflict');
  assert.equal(git(['status', '--porcelain']), '', 'the merge was aborted');
});

test('L74: the tick heals only own, unclaimed agent PRs that GitHub marks conflicting and that touch a rule file', () => {
  const own = (n, extra = {}) => ({ number: n, headRefName: `agent/claude/p${n}`, headRefOid: 'a'.repeat(40), mergeable: 'CONFLICTING', author: { login: ownerLogin }, isCrossRepository: false, files: [{ path: lessonsFile }], ...extra });
  const prs = [own(1), own(2, { mergeable: 'MERGEABLE' }), own(3, { files: [{ path: 'scripts/a.mjs' }] }), own(4, { isCrossRepository: true }), own(5, { headRefName: 'feat/x' }), own(6), own(7), own(8)];
  assert.deepEqual(healCandidates(prs).map(p => p.number), [1, 6, 7, 8]);
  const seen = [];
  const out = healConflicts({
    gh: {}, prs, prepare: n => { seen.push(n); throw new Error('clone failed'); },
    mayTouch: n => ({ ok: n !== 6 }), lock: fn => fn(), prLock: (n, fn) => fn(),
  });
  assert.deepEqual(seen, [1, 7, 8], 'claimed #6 is left to its session; at most three per tick');
  assert.deepEqual(out.map(o => o.status), ['failed', 'failed', 'failed'], 'a failure is logged, never thrown into the tick');
  assert.deepEqual(healConflicts({ gh: {}, prs, prepare: () => assert.fail('no clone while busy'), mayTouch: () => ({ ok: true }), lock: () => ({ status: 'busy' }), prLock: () => {} }).length, 1, 'another author check holds the clone: stop for this tick');
});
