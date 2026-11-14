import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { ciTestFiles, confirmClosed, lessonsLine, problems, readRegister, renderLessons, summarize, verify } from './collab-lessons.mjs';
import * as trust from './collab-trust.mjs';
import { asPosted } from './collab-test-post.mjs';

const sha = 'c'.repeat(40);
const N = 7;
// Since #456 a verdict counts only with a local receipt bound to its comment, as the scripted
// review path posts it.
const sealed = (verdict, createdAt) => asPosted(trust, { authorAssociation: 'OWNER', createdAt, body: `Review verdict: ${verdict} @ ${sha}\nReviewer: Codex\n${trust.verdictSeal({ head: sha, p2: 0, base: null, receipt: trust.signReceipt({ kind: 'verdict', pr: N, head: sha, base: null, result: verdict, p2: 0 }) })}` });
const approve = sealed('APPROVE', '2026-11-14T01:00:00Z');

function fixture() {
  const base = mkdtempSync(join(tmpdir(), 'lessons-test-'));
  mkdirSync(join(base, 'scripts'), { recursive: true });
  writeFileSync(join(base, 'scripts/x.test.mjs'), "test('retries a failed batch', () => {});\n// test('only a comment')\n");
  writeFileSync(join(base, 'scripts/x.mjs'), 'export const attempts = 3;\n');
  return base;
}
const done = extra => ({ id: 'L01', title: 'Thử lại lô lỗi', who: 'claude', due: '2026-11-15', status: 'done',
  test: { file: 'scripts/x.test.mjs', name: 'retries a failed batch' }, caller: { file: 'scripts/x.mjs', contains: 'attempts' }, closedBy: { pr: 7 }, ...extra });
const ci = new Set(['scripts/x.test.mjs']);

test('the real register is valid and every done lesson has its evidence in this checkout', () => {
  const reg = readRegister();
  assert.deepEqual(problems(reg), []);
  assert.ok(reg.lessons.length >= 12, 'the 12.11 agreement is carried over');
});

test('a lesson cannot be closed by editing the register', () => {
  const base = fixture();
  assert.deepEqual(problems({ lessons: [done()] }, { base, ciFiles: ci }), []);
  const cases = [
    [done({ test: undefined }), /without a regression test/],
    [done({ test: { file: 'scripts/missing.test.mjs', name: 'x' } }), /does not exist/],
    [done({ test: { file: 'scripts/x.test.mjs', name: 'only a comment' } }), /no test named/],
    [done({ caller: { file: 'scripts/x.mjs', contains: 'nowhere' } }), /does not contain/],
    [done({ caller: undefined }), /without a caller/],
    [done({ closedBy: undefined }), /without the PR/],
    [done({ due: undefined, status: 'open' }), /due date/],
    [done({ status: 'finished' }), /status must be/],
  ];
  for (const [lesson, pattern] of cases) assert.match(problems({ lessons: [lesson] }, { base, ciFiles: ci }).join('\n'), pattern);
  assert.match(problems({ lessons: [done()] }, { base, ciFiles: new Set() }).join('\n'), /not in pnpm collab:test/, 'a test CI never runs does not count');
  assert.match(problems({ lessons: [done(), done()] }, { base, ciFiles: ci }).join('\n'), /duplicate/);
});

test('only a PR merged into integration with a trusted Codex APPROVE confirms a lesson', () => {
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [approve] }), true);
  assert.equal(confirmClosed({ number: N, state: 'OPEN', baseRefName: 'collab/integration', headRefOid: sha, comments: [approve] }), false, 'not merged');
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'main', headRefOid: sha, comments: [approve] }), false, 'other base');
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [{ ...approve, authorAssociation: 'NONE' }] }), false, 'untrusted commenter');
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [{ ...approve, body: `Review verdict: APPROVE @ ${sha}` }] }), false, 'a hand-written verdict is not the Codex review');
  const unsigned = { ...approve, body: `Review verdict: APPROVE @ ${sha}\nReviewer: Codex\n<!-- la-lanh-agent codex-auto-review sha=${sha} -->` };
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [unsigned] }), false, 'an APPROVE without a receipt does not confirm');
  // Codex 13.11: an APPROVE of an older head, or one followed by REQUEST_CHANGES, does not close.
  const other = 'd'.repeat(40);
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: other, comments: [approve] }), false, 'APPROVE of another head');
  const later = sealed('REQUEST_CHANGES', '2026-11-14T02:00:00Z');
  assert.equal(confirmClosed({ number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [approve, later] }), false, 'the last verdict counts');
});

test('overdue and unconfirmed lessons are reported, not hidden', () => {
  const dir = mkdtempSync(join(tmpdir(), 'lessons-cache-'));
  const reg = { lessons: [
    done(),
    { id: 'L02', title: 'a', who: 'claude', due: '2026-11-12', status: 'open' },
    { id: 'L03', title: 'b', who: 'claude', due: '2026-11-20', status: 'open' },
    { id: 'L04', title: 'c', who: 'owner', status: 'waiting-owner' },
  ] };
  let views = 0;
  const cachePath = join(dir, 'v.json');
  const notYet = verify(reg, { view: () => { views += 1; return { number: N, state: 'OPEN', baseRefName: 'collab/integration', headRefOid: sha, comments: [] }; }, cachePath });
  const s = summarize(reg, { today: '2026-11-14', verified: notYet });
  assert.deepEqual({ done: s.done, open: s.open, owner: s.owner, overdue: s.overdue, unconfirmed: s.unconfirmed }, { done: 0, open: 3, owner: 1, overdue: ['L02'], unconfirmed: ['L01'] });
  const line = renderLessons(s);
  assert.match(line, /0\/4 đã chạy thật/);
  assert.match(line, /\*\*1 quá hạn\*\* \(L02\)/);
  assert.match(line, /chưa có bằng chứng merge \+ Codex duyệt: L01/);
  const ok = verify(reg, { view: () => { views += 1; return { number: N, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: [approve] }; }, cachePath });
  assert.equal(summarize(reg, { today: '2026-11-14', verified: ok }).done, 1);
  verify(reg, { view: () => { views += 1; throw new Error('no network'); }, cachePath });
  assert.equal(views, 2, 'a confirmed PR is read from GitHub once');
});

test('the board line never throws and says when the register is broken', () => {
  assert.match(lessonsLine({ register: () => { throw new Error('bad json'); } }), /chưa đo được \(bad json\)/);
  assert.match(lessonsLine({ register: () => ({ lessons: [{ id: 'X' }] }), online: false }), /sổ đang sai 1 chỗ/);
  assert.match(lessonsLine({ online: false }), /^Lời hứa sửa quy trình: /);
});

test('the lessons test itself runs in CI', () => {
  assert.ok(ciTestFiles().has('scripts/collab-lessons.test.mjs'));
});
