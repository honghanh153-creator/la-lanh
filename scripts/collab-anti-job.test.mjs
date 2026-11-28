// One bounded Anti task run by the trusted host (Codex r1 on #955, P1). The transport is a fake;
// the repo is synthetic; nothing here talks to Antigravity or touches a real checkout.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { answerLimitMs, antiTaskBrief, checkAnswer, jobPath, openJob, stepJob, trailer } from './collab-anti-job.mjs';
import { fsIo, trustedGit } from './collab-anti-patch.mjs';

const plainGit = (cwd, args) => execFileSync('/usr/bin/git', ['-c', 'user.name=t', '-c', 'user.email=t@example.com', '-c', 'commit.gpgsign=false', ...args], { cwd, env: { PATH: '/usr/bin:/bin', HOME: cwd, GIT_CONFIG_NOSYSTEM: '1' }, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
const setup = (files = { 'docs/product/a.md': 'Dòng cũ.\n', 'apps/web/src/b.ts': 'export const b = 1;\n' }) => {
  const repoRoot = mkdtempSync(join(tmpdir(), 'anti-job-repo-'));
  plainGit(repoRoot, ['init', '-q', '-b', 'main']);
  for (const [p, text] of Object.entries(files)) { mkdirSync(join(repoRoot, p, '..'), { recursive: true }); writeFileSync(join(repoRoot, p), text); }
  plainGit(repoRoot, ['add', '-A']);
  plainGit(repoRoot, ['commit', '-q', '-m', 'base']);
  const base = plainGit(repoRoot, ['rev-parse', 'HEAD']).trim();
  const home = mkdtempSync(join(tmpdir(), 'anti-job-home-'));
  return { repoRoot, base, home };
};
const uuid = '0123abcd-0123-4567-89ab-0123456789ab';
const fake = (answer = null) => {
  const t = { briefs: [], answer, start(brief) { t.briefs.push(brief); return uuid; }, read() { return t.answer; } };
  return t;
};
const ev = (...lines) => lines.map(l => JSON.stringify(l)).join('\n');
const patchEv = (path, find, replace) => ({ type: 'patch', text: `*** Edit: ${path}\n<<<<<<< FIND\n${find}\n=======\n${replace}\n>>>>>>> REPLACE` });
const opts = (s, transport, extra = {}) => ({ issue: 950, slug: 'copy-fix', scope: ['docs/product/'], task: 'Sửa câu trong a.md cho ngắn hơn.', base: s.base, repoRoot: s.repoRoot, transport, home: s.home, nowMs: 1000, ...extra });

test('anti job: no bridge on integration means blocked, nothing created', () => {
  const s = setup();
  const r = openJob(opts(s, null));
  assert.equal(r.status, 'blocked');
  assert.equal(existsSync(join(s.home, 'anti-jobs')), false);
});

test('anti job: a protected scope, a private task or a bad base is refused before any worktree', () => {
  const s = setup();
  const t = fake();
  for (const [extra, why] of [
    [{ scope: ['scripts/collab-merge.mjs'] }, /file cổng/],
    [{ scope: ['.github/'] }, /thư mục bị cấm/],
    [{ scope: [] }, /phạm vi/],
    [{ task: 'gửi cho ai.do@gmail.com' }, /email/],
    [{ base: 'main' }, /SHA đầy đủ/],
    [{ slug: 'Bad Slug' }, /slug/],
  ]) {
    const r = openJob(opts(s, t, extra));
    assert.equal(r.status, 'refused', JSON.stringify(extra));
    assert.match(r.reasons.join(' | '), why);
  }
  assert.equal(t.briefs.length, 0, 'Anti is never asked');
  assert.equal(existsSync(join(s.home, 'anti-jobs', '950-copy-fix')), false);
});

test('anti job: started → waiting → applied on its own branch; the main checkout is untouched', () => {
  const s = setup();
  const t = fake({ done: false, text: '' });
  const r = openJob(opts(s, t));
  assert.equal(r.status, 'started', JSON.stringify(r));
  assert.deepEqual(r.files, ['docs/product/a.md']);
  assert.match(t.briefs[0], /Dòng cũ\./);
  assert.doesNotMatch(t.briefs[0], /export const b/, 'only files in scope go to Anti');
  assert.equal(openJob(opts(s, t, { slug: 'other' })).status, 'busy', 'one job at a time');
  assert.equal(stepJob({ transport: t, home: s.home, nowMs: 2000 }).status, 'waiting');
  t.answer = { done: true, text: ev({ type: 'message', text: 'Rút gọn câu.' }, patchEv('docs/product/a.md', 'Dòng cũ.', 'Dòng mới.')) };
  const done = stepJob({ transport: t, home: s.home, nowMs: 3000 });
  assert.equal(done.status, 'applied', JSON.stringify(done));
  assert.equal(done.branch, 'agent/anti/950-copy-fix');
  const dir = join(s.home, 'anti-jobs', '950-copy-fix');
  assert.equal(readFileSync(join(dir, 'docs/product/a.md'), 'utf8'), 'Dòng mới.\n');
  assert.match(trustedGit(['log', '-1', '--format=%B'], { cwd: dir }), new RegExp(trailer.replace(/[()]/g, '\\$&')));
  assert.equal(trustedGit(['rev-parse', 'HEAD~1'], { cwd: dir }).trim(), s.base);
  assert.equal(readFileSync(join(s.repoRoot, 'docs/product/a.md'), 'utf8'), 'Dòng cũ.\n', 'main checkout untouched');
  assert.equal(trustedGit(['status', '--porcelain'], { cwd: s.repoRoot }).trim(), '');
  assert.equal(stepJob({ transport: t, home: s.home, nowMs: 4000 }), null, 'a finished job is not stepped again');
});

test('anti job: tools, an unseen file, a bad answer or a timeout drop the job and its worktree', () => {
  for (const [answer, nowMs, why] of [
    [{ done: false, text: '', tools: ['run_command'] }, 2000, /công cụ/],
    [{ done: true, text: ev(patchEv('apps/web/src/b.ts', 'b = 1', 'b = 2')) }, 2000, /không được xem/],
    [{ done: true, text: ev({ type: 'tool_call', name: 'read_file', args: { path: 'docs/product/a.md' } }, patchEv('docs/product/a.md', 'Dòng cũ.', 'x')) }, 2000, /tool_call/],
    [{ done: true, text: ev({ type: 'message', text: 'không có patch' }) }, 2000, /đúng 1 patch/],
    [{ done: true, text: 'không phải JSON' }, 2000, /./],
    [{ done: false, text: '' }, 1000 + answerLimitMs + 1, /20 phút/],
  ]) {
    const s = setup();
    const t = fake(answer);
    assert.equal(openJob(opts(s, t)).status, 'started');
    const r = stepJob({ transport: t, home: s.home, nowMs });
    assert.equal(r.status, 'dropped', JSON.stringify(answer));
    assert.match(r.reasons.join(' | '), why);
    assert.equal(existsSync(join(s.home, 'anti-jobs', '950-copy-fix')), false, 'worktree removed');
    assert.equal(trustedGit(['branch', '--list', 'agent/anti/*'], { cwd: s.repoRoot }).trim(), '', 'branch removed');
    assert.equal(openJob(opts(s, t)).status, 'started', 'a dropped job does not block the next one');
  }
});

test('anti job: a write that cannot be undone marks the job invalid and keeps it out of use', () => {
  const s = setup({ 'docs/product/a.md': 'a\n', 'docs/product/b.md': 'b\n' });
  const t = fake({ done: true, text: ev({ type: 'patch', text: ['a', 'b'].map(x => `*** Edit: docs/product/${x}.md\n<<<<<<< FIND\n${x}\n=======\n${x}2\n>>>>>>> REPLACE`).join('\n') }) });
  assert.equal(openJob(opts(s, t)).status, 'started');
  let renames = 0;
  const io = { ...fsIo, renameSync(a, b) { if (renames++ === 1) throw new Error('fail'); fsIo.renameSync(a, b); }, writeFileSync(p, d, o) { if (String(p).endsWith('.back')) throw new Error('fail'); fsIo.writeFileSync(p, d, o); } };
  const r = stepJob({ transport: t, home: s.home, nowMs: 2000, io });
  assert.equal(r.status, 'invalid');
  assert.equal(JSON.parse(readFileSync(jobPath(s.home), 'utf8')).status, 'invalid');
  assert.equal(openJob(opts(s, t)).status, 'refused', 'the invalid worktree is never reused');
});

test('anti job: the brief and the answer check are text only', () => {
  const brief = antiTaskBrief({ issue: 1, task: 'x', items: [{ path: 'docs/a.md', text: 'nội dung' }] });
  assert.match(brief, /Không chạy lệnh/);
  assert.match(brief, /===== FILE docs\/a\.md =====/);
  assert.equal(checkAnswer(null, []).ok, false);
  assert.equal(checkAnswer({ done: true, text: ev(patchEv('docs/a.md', 'x', 'y')) }, ['docs/a.md']).ok, true);
});

// Codex on #955 @a1920174, P2 1: an answer shaped by Anti must not crash the trusted host.
test('anti job: an answer with inherited keys or wrong types is dropped, never thrown', () => {
  for (const answer of [
    { done: true, tools: 'x', text: '' },
    { done: true, text: ev({ type: 'constructor' }) },
    { done: true, text: ev({ type: 'tool_call', name: 'toString' }) },
    { done: true, text: 42 },
    null, 'x', [],
  ]) {
    let r;
    assert.doesNotThrow(() => { r = checkAnswer(answer, { shown: ['docs/product/a.md'] }); }, JSON.stringify(answer));
    assert.equal(r.ok, false, JSON.stringify(answer));
  }
  const s = setup();
  const t = fake({ done: false, text: '' });
  assert.equal(openJob(opts(s, t)).status, 'started');
  t.answer = { done: true, text: ev({ type: 'constructor' }, { type: 'tool_call', name: 'hasOwnProperty' }) };
  let r;
  assert.doesNotThrow(() => { r = stepJob({ transport: t, home: s.home, nowMs: 2000 }); });
  assert.equal(r.status, 'dropped', JSON.stringify(r));
  assert.equal(existsSync(join(s.home, 'anti-jobs', '950-copy-fix')), false);
});

// P2 2: every file a CI gate runs is outside what Anti may be shown, not only scripts/collab-*.
test('anti job: a scope on any gate or tool-config file is refused before any worktree', () => {
  const s = setup({ 'docs/product/a.md': 'x\n', 'scripts/research-sources.mjs': 'x\n', 'apps/api/scripts/audit.py': 'x\n', 'apps/web/vite.config.ts': 'x\n' });
  const t = fake();
  for (const scope of [['scripts/research-sources.mjs'], ['scripts/'], ['apps/api/scripts/audit.py'], ['apps/web/vite.config.ts'], ['vendor/'], ['apps/api/pyproject.toml']]) {
    const r = openJob(opts(s, t, { scope }));
    assert.equal(r.status, 'refused', JSON.stringify(scope));
  }
  assert.equal(t.briefs.length, 0, 'Anti is never shown a gate file');
});

// P2 3: the patch lands only on the exact files and head Anti was shown.
test('anti job: a branch that moved after the snapshot drops the patch', () => {
  const s = setup();
  const t = fake({ done: false, text: '' });
  assert.equal(openJob(opts(s, t)).status, 'started');
  const dir = join(s.home, 'anti-jobs', '950-copy-fix');
  writeFileSync(join(dir, 'docs/product/a.md'), 'Dòng cũ.\nThêm.\n');
  plainGit(dir, ['commit', '-q', '-am', 'moved']);
  t.answer = { done: true, text: ev(patchEv('docs/product/a.md', 'Dòng cũ.', 'Dòng mới.')) };
  const r = stepJob({ transport: t, home: s.home, nowMs: 2000 });
  assert.equal(r.status, 'dropped', JSON.stringify(r));
  assert.match(r.reasons.join(' | '), /head-moved/);
  assert.equal(existsSync(dir), false, 'the worktree is removed');
  assert.doesNotMatch(plainGit(s.repoRoot, ['log', '--all', '--format=%B']), new RegExp(trailer.replace(/[()]/g, '\\$&')), 'no Anti commit anywhere');
});

test('anti job: a file edited after the snapshot drops the patch (hash differs)', () => {
  const s = setup();
  const t = fake({ done: false, text: '' });
  assert.equal(openJob(opts(s, t)).status, 'started');
  const job = JSON.parse(readFileSync(jobPath(s.home), 'utf8'));
  assert.match(job.hashes['docs/product/a.md'], /^[0-9a-f]{64}$/, 'the job pins what Anti saw');
  writeFileSync(jobPath(s.home), JSON.stringify({ ...job, hashes: { 'docs/product/a.md': '0'.repeat(64) } }));
  t.answer = { done: true, text: ev(patchEv('docs/product/a.md', 'Dòng cũ.', 'Dòng mới.')) };
  const r = stepJob({ transport: t, home: s.home, nowMs: 2000 });
  assert.equal(r.status, 'dropped', JSON.stringify(r));
  assert.match(r.reasons.join(' | '), /khác bản Anti đã xem/);
});

// P2 4: one job lock across open and step, so a transport that re-enters cannot start a second job.
test('anti job: a re-entrant open or step while a job is opening is busy', () => {
  const s = setup();
  const inner = [];
  const t = fake({ done: false, text: '' });
  const start = t.start;
  t.start = brief => {
    inner.push(openJob(opts(s, fake(), { slug: 'other' })).status);
    inner.push(stepJob({ transport: t, home: s.home, nowMs: 1500 }).status);
    return start(brief);
  };
  const r = openJob(opts(s, t));
  assert.equal(r.status, 'started', JSON.stringify(r));
  assert.deepEqual(inner, ['busy', 'busy']);
  assert.equal(existsSync(join(s.home, 'anti-jobs', '950-other')), false);
  assert.equal(JSON.parse(readFileSync(jobPath(s.home), 'utf8')).status, 'asked', 'the first job state is intact');
});

test('anti job: a corrupt state file blocks open and step; a left-over opening is cleaned first', () => {
  const s = setup();
  mkdirSync(join(jobPath(s.home), '..'), { recursive: true });
  writeFileSync(jobPath(s.home), '{not json');
  assert.equal(openJob(opts(s, fake())).status, 'busy');
  assert.equal(stepJob({ transport: fake(), home: s.home, nowMs: 2000 }).status, 'busy');
  // A crash between "opening" and "asked" leaves a worktree; the next open removes it and starts.
  rmSync(jobPath(s.home));
  assert.equal(openJob(opts(s, fake({ done: false, text: '' }))).status, 'started');
  const left = JSON.parse(readFileSync(jobPath(s.home), 'utf8'));
  writeFileSync(jobPath(s.home), JSON.stringify({ ...left, status: 'opening' }));
  assert.equal(existsSync(left.dir), true);
  const t2 = fake({ done: false, text: '' });
  assert.equal(stepJob({ transport: t2, home: s.home, nowMs: 2000 }).status, 'dropped', 'step cleans a half-open job too');
  assert.equal(existsSync(left.dir), false, 'the left-over worktree is removed');
  writeFileSync(jobPath(s.home), JSON.stringify({ ...left, status: 'opening' }));
  plainGit(s.repoRoot, ['worktree', 'add', '-q', '-b', 'tmp-left', left.dir, s.base]);
  assert.equal(openJob(opts(s, t2, { slug: 'next' })).status, 'started', 'open recovers, then starts');
  assert.equal(existsSync(left.dir), false);
  assert.equal(t2.briefs.length, 1);
});
