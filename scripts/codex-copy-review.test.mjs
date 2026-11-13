import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { applyDecisions, batchFor, batchSize, buildPrompt, digest, main, pendingCount, readRejected, recordRejected, renderBody, runCopyBatch, selectPending, validateDecisions } from './codex-copy-review.mjs';
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
  assert.deepEqual(out, { status: 'opened', url: 'https://example.invalid/pr/1' });
  assert.equal(released, 1);
  assert.equal(runCopyBatch({ lock: () => () => { released += 1; }, run: () => { throw new Error('push refused'); } }).status, 'error');
  assert.equal(released, 2, 'the lock is released after an error');
});
