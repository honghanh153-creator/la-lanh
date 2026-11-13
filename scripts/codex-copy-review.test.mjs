import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { applyDecisions, batchBranch, commitArgs, batchFor, batchSize, codexBin, readSaved, buildPrompt, digest, main, pendingCount, readRejected, recordRejected, renderBody, runCopyBatch, selectPending, validateDecisions } from './codex-copy-review.mjs';
import { bodyProblems } from './collab-preflight.mjs';

// Synthetic sentences only.
const registry = {
  version: 'copy-registry/v1',
  entries: [
    { id: 'tarot.a', category: 'reading', text: 'Câu thử A.', status: 'pending' },
    { id: 'tarot.b', category: 'reading', text: 'Câu thử B.', status: 'pending' },
    { id: 'privacy.c', category: 'privacy', text: 'Câu thử C.', status: 'pending' },
  ],
};
const decisions = { decisions: [
  { id: 'tarot.a', decision: 'approve', reason: 'rõ' },
  { id: 'tarot.b', decision: 'reject', reason: 'khó hiểu' },
] };

test('owner-only categories are never sent to Codex', () => {
  assert.deepEqual(selectPending(registry).map(e => e.id), ['tarot.a', 'tarot.b']);
  assert.ok(!buildPrompt(selectPending(registry)).includes('Câu thử C.'));
});

test('approve sets codex approver and digest; reject stays pending', () => {
  const next = applyDecisions(registry, validateDecisions(decisions, selectPending(registry)), '2026-11-06');
  const [a, b, c] = next.entries;
  assert.deepEqual(a, { ...registry.entries[0], status: 'approved', approver: 'codex', date: '2026-11-06', digest: digest('Câu thử A.') });
  assert.equal(b.status, 'pending');
  assert.equal(c.status, 'pending');
});

test('a decision for an owner-only or unknown entry is refused', () => {
  const pending = selectPending(registry);
  assert.throws(() => validateDecisions({ decisions: [{ id: 'privacy.c', decision: 'approve', reason: 'x' }] }, pending));
  assert.throws(() => validateDecisions({ decisions: [{ id: 'nope', decision: 'approve', reason: 'x' }] }, pending));
});

test('PR body never uses the owner reply words and carries the agent marker', () => {
  const body = renderBody([{ id: 'tarot.a', decision: 'approve', reason: 'Duyệt\nGiữ' }], '2026-11-06');
  assert.ok(!/^(Duyệt|Giữ|Bỏ)/m.test(body));
  assert.match(body, /<!-- la-lanh-agent copy-batch/);
});

test('the batch PR body passes the loop preflight, including "Người dùng thấy gì:" (owner 12.11)', () => {
  assert.deepEqual(bodyProblems(renderBody([{ id: 'tarot.a', decision: 'approve', reason: 'rõ' }], '2026-11-12')), []);
});

test('dry run with a fake Codex touches no git and returns the batch', () => {
  const dir = mkdtempSync(join(tmpdir(), 'copy-review-test-'));
  writeFileSync(join(dir, 'reg.json'), JSON.stringify(registry));
  writeFileSync(join(dir, 'fake.json'), JSON.stringify(decisions));
  const calls = [];
  const sink = { text: '', write(s) { this.text += s; } };
  const result = main(['--dry-run', '--fake-codex', join(dir, 'fake.json')],
    { run: (...args) => { calls.push(args); }, out: sink, registryPath: join(dir, 'reg.json') });
  assert.equal(result.status, 'dry-run');
  assert.deepEqual(calls, []);
  assert.equal(result.registry.entries[0].status, 'approved');
});

test('python and node digests agree', () => {
  assert.equal(digest('Câu thử A.'), digest('Câu thử A.'.normalize('NFD')));
});

test('generated batch PR body passes the preflight gate check at level M', async () => {
  const { bodyProblems } = await import('./collab-preflight.mjs');
  const body = renderBody([{ id: 'tarot.a', decision: 'approve', reason: 'rõ' }], '2026-11-06');
  assert.deepEqual(bodyProblems(body), []);
  assert.match(body, /^Mức: M/m);
});

test('an entry changed after review is not approved', () => {
  const pending = selectPending(registry);
  const reviewed = new Map(pending.map(e => [e.id, digest(e.text)]));
  const edited = { ...registry, entries: registry.entries.map(e => e.id === 'tarot.a' ? { ...e, text: 'Câu đã đổi.' } : e) };
  const next = applyDecisions(edited, decisions.decisions, '2026-11-06', reviewed);
  assert.equal(next.entries[0].status, 'pending');
});

test('a batch with no approvals publishes nothing', () => {
  const dir = mkdtempSync(join(tmpdir(), 'copy-review-test-'));
  writeFileSync(join(dir, 'reg.json'), JSON.stringify(registry));
  writeFileSync(join(dir, 'fake.json'), JSON.stringify({ decisions: [{ id: 'tarot.a', decision: 'reject', reason: 'x' }] }));
  const calls = [];
  const result = main(['--fake-codex', join(dir, 'fake.json')],
    { run: (...args) => { calls.push(args); }, out: { write() {} }, registryPath: join(dir, 'reg.json') });
  assert.equal(result.status, 'no-approvals');
  assert.deepEqual(calls, []);
});

test('publishing reviews and branches from the same pinned integration commit', () => {
  const sha = 'a'.repeat(40);
  const calls = [];
  const run = (cmd, args) => {
    calls.push([cmd, ...args]);
    if (args[0] === 'rev-parse') return `${sha}\n`;
    if (args[0] === 'show') return JSON.stringify(registry);
    if (args[0] === 'worktree') mkdirSync(join(args[5], 'apps/api/app/domains/content'), { recursive: true });
    if (cmd === 'gh') return 'https://example.test/pr/1\n';
    return '';
  };
  const dir = mkdtempSync(join(tmpdir(), 'copy-review-test-'));
  writeFileSync(join(dir, 'fake.json'), JSON.stringify(decisions));
  const result = main(['--fake-codex', join(dir, 'fake.json')], { run, out: { write() {} } });
  assert.equal(result.status, 'opened');
  assert.ok(calls.some(c => c[1] === 'show' && c[2] === `${sha}:apps/api/app/domains/content/copy_registry.json`));
  const add = calls.find(c => c[1] === 'worktree');
  assert.equal(add.at(-1), sha);
  assert.ok(!calls.some(c => c[0] === 'git' && c[1] === 'fetch' && calls.indexOf(c) > calls.indexOf(add)));
  // The ops clone has no global git identity: the commit names the agent itself.
  const commit = calls.find(c => c[0] === 'git' && c.includes('commit'));
  assert.deepEqual(commit.slice(1, 5), ['-c', 'user.name=la-lanh-agent', '-c', 'user.email=la-lanh-agent@users.noreply.github.com']);
});

test('owner-only copy stays pending even if a decision for it slips past validation', () => {
  const forced = applyDecisions(registry, [{ id: 'privacy.c', decision: 'approve', reason: 'x' }], '2026-11-12');
  assert.equal(forced.entries[2].status, 'pending');
  for (const category of ['privacy', 'consent', 'crisis', 'safety']) {
    const reg = { entries: [{ id: `${category}.x`, category, text: 'Câu thử.', status: 'pending' }] };
    assert.equal(pendingCount(reg), 0, `${category} is never counted as Codex work`);
    assert.equal(applyDecisions(reg, [{ id: `${category}.x`, decision: 'approve' }], '2026-11-12').entries[0].status, 'pending');
  }
});

test('rejected copy does not fill every later batch; edited text is reviewed again (Codex #451 P1)', () => {
  const dir = mkdtempSync(join(tmpdir(), 'copy-review-test-'));
  const file = join(dir, 'rejected.json');
  const big = { entries: Array.from({ length: batchSize + 1 }, (_, i) => ({ id: `q.${i}`, category: 'reading', text: `Câu thử ${i}.`, status: 'pending' })) };
  const first = batchFor(big, readRejected(file));
  recordRejected(first.map(e => ({ id: e.id, decision: 'reject', reason: 'x' })), new Map(first.map(e => [e.id, digest(e.text)])), file);
  const next = batchFor(big, readRejected(file));
  assert.deepEqual(next.map(e => e.id), [`q.${batchSize}`], 'the day after, the unread entry is reviewed');
  assert.equal(pendingCount(big, readRejected(file)), 1);
  const edited = { entries: big.entries.map(e => e.id === 'q.0' ? { ...e, text: 'Câu đã sửa.' } : e) };
  assert.ok(batchFor(edited, readRejected(file)).some(e => e.id === 'q.0'), 'an edited sentence comes back for review');
});

test('one daily batch holds at most batchSize entries, so the PR body stays readable', () => {
  const big = { entries: Array.from({ length: batchSize + 30 }, (_, i) => ({ id: `r.${i}`, category: 'reading', text: `Câu thử ${i}.`, status: 'pending' })) };
  assert.equal(batchFor(big).length, batchSize);
  assert.equal(pendingCount(big), batchSize + 30);
  assert.ok(renderBody(batchFor(big).map(e => ({ id: e.id, decision: 'reject', reason: 'chưa rõ chủ thể trong câu' })), '2026-11-12').length < 60000, 'under the GitHub body limit');
  assert.match(renderBody([], '2026-11-12'), /^Size-exception: /m, 'a generated registry batch is not split by the size cap');
});

test('the tick runner takes the review lock and reports busy without starting Codex', () => {
  let started = 0;
  assert.deepEqual(runCopyBatch({ lock: () => null, run: () => { started += 1; } }), { status: 'busy' });
  assert.equal(started, 0);
  let released = 0;
  const out = runCopyBatch({ lock: () => () => { released += 1; }, run: () => ({ status: 'opened', url: 'https://example.invalid/pr/1' }) });
  assert.deepEqual(out, { status: 'opened', codex: false, url: 'https://example.invalid/pr/1' });
  assert.equal(released, 1);
  assert.equal(runCopyBatch({ lock: () => () => { released += 1; }, run: () => { throw new Error('push refused'); } }).status, 'error');
  assert.equal(released, 2, 'the lock is released after an error');
});

// 13.11.2026: the first live batch failed at the commit after Codex had decided; the decisions
// were lost and the day was skipped. A retry must publish the saved decisions without Codex.
test('a batch that fails after Codex decided is published on retry without a second Codex run', () => {
  const sha = 'b'.repeat(40);
  const dir = mkdtempSync(join(tmpdir(), 'copy-review-test-'));
  const savedFile = join(dir, 'saved.json');
  let failCommit = true;
  const calls = [];
  const run = (cmd, args) => {
    calls.push([cmd, ...args]);
    if (cmd === codexBin) { writeFileSync(args[args.indexOf('-o') + 1], JSON.stringify(decisions)); return ''; }
    if (args[0] === 'rev-parse') return `${sha}\n`;
    if (args[0] === 'show') return JSON.stringify(registry);
    if (args[0] === 'worktree' && args[1] === 'add') mkdirSync(join(args[5], 'apps/api/app/domains/content'), { recursive: true });
    if (args.includes('commit') && failCommit) throw new Error('Author identity unknown');
    if (cmd === 'gh') return 'https://example.test/pr/2\n';
    return '';
  };
  const opts = { run, out: { write() {} }, rejectedFile: join(dir, 'rejected.json'), savedFile };
  const first = {};
  assert.throws(() => main([], { ...opts, progress: first, at: { date: '2026-11-13', hour: 10, minute: 48 } }), /Author identity/);
  assert.equal(first.codexRan, true);
  assert.ok(readSaved(savedFile, '2026-11-13'), 'Codex decisions survive the failed publish');
  const codexCalls = () => calls.filter(c => c[0] === codexBin).length;
  assert.equal(codexCalls(), 1);
  assert.ok(calls.some(c => c[1] === 'branch' && c[2] === '-D'), 'the failed attempt drops its local branch');

  failCommit = false;
  const second = {};
  const result = main([], { ...opts, progress: second, at: { date: '2026-11-13', hour: 11, minute: 5 } });
  assert.equal(result.status, 'opened');
  assert.equal(codexCalls(), 1, 'the retry does not call Codex again');
  assert.equal(second.reused, true);
  assert.ok(!existsSync(savedFile), 'saved decisions are dropped once published');
  const branches = calls.filter(c => c[1] === 'worktree' && c[2] === 'add').map(c => c[5]);
  assert.deepEqual(branches, [batchBranch('2026-11-13', { hour: 10, minute: 48 }), batchBranch('2026-11-13', { hour: 11, minute: 5 })]);
  assert.notEqual(branches[0], branches[1], 'a retry never reuses the failed attempt\'s branch');
  assert.match(branches[0], /^agent\/claude\/copy-batch-/, 'the tick still sees the batch PR as open');
});

test('saved decisions expire and an edited sentence is still left pending', () => {
  const dir = mkdtempSync(join(tmpdir(), 'copy-review-test-'));
  const file = join(dir, 'saved.json');
  writeFileSync(file, JSON.stringify({ date: '2026-11-01', decisions: [], reviewed: [] }));
  assert.equal(readSaved(file, '2026-11-13'), null, 'older than the limit: Codex reviews afresh');
  writeFileSync(file, '{ not json');
  assert.equal(readSaved(file, '2026-11-13'), null);
});

test('runCopyBatch says whether Codex was called, also when the run fails', () => {
  const lock = () => () => {};
  assert.deepEqual(runCopyBatch({ lock, run: p => { p.codexRan = true; throw new Error('push rejected'); } }),
    { status: 'error', codex: true, reason: 'push rejected' });
  assert.deepEqual(runCopyBatch({ lock, run: p => { p.reused = true; return { status: 'opened', url: 'https://example.invalid/pr/3' }; } }),
    { status: 'opened', codex: false, url: 'https://example.invalid/pr/3' });
});

// Codex 13.11 on #462: the identity fix was only tested against a fake git. This commits with the
// exact arguments in a real repository whose git has no user name or email at all.
test('the batch commit works in a real git with no configured identity', () => {
  const dir = mkdtempSync(join(tmpdir(), 'copy-git-'));
  const home = mkdtempSync(join(tmpdir(), 'copy-home-'));
  // useConfigOnly: git may not guess a name from the machine, as on the ops clone where it failed.
  writeFileSync(join(home, 'gitconfig'), '[user]\n\tuseConfigOnly = true\n');
  const env = { PATH: process.env.PATH, HOME: home, GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: join(home, 'gitconfig') };
  const git = args => execFileSync('/usr/bin/git', args, { cwd: dir, env, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  git(['init', '-q']);
  writeFileSync(join(dir, 'f.txt'), 'x\n');
  git(['add', 'f.txt']);
  assert.throws(() => git(['commit', '-q', '-m', 'plain']), /identity|empty ident|user\.email|Please tell me who you are/i, 'this git really has no identity');
  git(commitArgs('2026-11-13'));
  assert.equal(git(['log', '-1', '--format=%an <%ae>']).trim(), 'la-lanh-agent <la-lanh-agent@users.noreply.github.com>');
});
