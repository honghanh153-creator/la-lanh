import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { codeLines, repeatFixReason, sizeProblem, withRepeatNote } from './collab-size.mjs';
import { runPreflight } from './collab-preflight.mjs';

const files = [
  { path: 'scripts/a.mjs', additions: 300, deletions: 50 },
  { path: 'scripts/a.test.mjs', additions: 900, deletions: 0 },
  { path: 'apps/api/tests/test_x.py', additions: 500, deletions: 0 },
  { path: 'docs/x.md', additions: 700, deletions: 0 },
  { path: 'pnpm-lock.yaml', additions: 2000, deletions: 100 },
  { path: 'apps/api/uv.lock', additions: 2000, deletions: 100 },
];

test('code lines skip tests, docs and lockfiles', () => {
  assert.equal(codeLines(files), 350);
  assert.equal(codeLines([...files, { path: 'apps/web/b.ts', additions: 60, deletions: 0 }]), 410);
});

test('more than 400 code lines fails unless the body has Size-exception', () => {
  const big = [...files, { path: 'apps/web/b.ts', additions: 60, deletions: 0 }];
  assert.equal(sizeProblem({ files }), null);
  assert.equal(sizeProblem({ files: big }), 'PR quá lớn (410 dòng mã) — tách nhỏ hoặc ghi `Size-exception: <lý do>` trong body');
  assert.equal(sizeProblem({ files: big, body: 'x\nSize-exception: một migration không tách được\n' }), null);
  assert.notEqual(sizeProblem({ files: big, body: 'Size-exception:\n' }), null);
});

const body = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10'].map(g => `- ${g}: ${g === 'G7' ? 'không đụng phiên, dữ liệu, log' : 'ok'}`).join('\n') + '\nMức: S\nNgười dùng thấy gì: không trực tiếp (vận hành)\n';
test('preflight reports the size cap', () => {
  const big = [{ path: 'scripts/b.mjs', additions: 401, deletions: 0 }];
  assert.deepEqual(runPreflight({ body, files: big }).reasons, ['PR quá lớn (401 dòng mã) — tách nhỏ hoặc ghi `Size-exception: <lý do>` trong body']);
  assert.equal(runPreflight({ body: `${body}Size-exception: tách sẽ hỏng contract\n`, files: big }).status, 'PASS');
});

const sha = 'a'.repeat(40);
const rc = { authorAssociation: 'OWNER', body: `Review verdict: REQUEST_CHANGES @ ${sha}\nReviewer: Codex` };
test('after two REQUEST_CHANGES the next fix turn asks for a repo-wide sweep', () => {
  assert.equal(repeatFixReason({ comments: [rc] }), null);
  assert.equal(repeatFixReason({ comments: [rc, { ...rc, authorAssociation: 'NONE' }] }), null);
  assert.match(repeatFixReason({ comments: [rc, rc] }), /rà cùng loại lỗi toàn repo trước khi push/);
  const pr = { number: 9, comments: [rc, rc] };
  assert.match(withRepeatNote({ turn: 'claude-fix', reason: 'REQUEST_CHANGES @ head' }, pr).reason, /^REQUEST_CHANGES @ head; .*rà cùng loại lỗi toàn repo trước khi push/);
  assert.equal(withRepeatNote({ turn: 'codex-review', reason: 'x' }, pr).reason, 'x');
  assert.match(readFileSync(new URL('./collab-turn.mjs', import.meta.url), 'utf8'), /withRepeatNote\(prTurn\(/);
});

test('#254: a blank Size-exception does not borrow the next line as its reason', () => {
  const big = [{ path: 'scripts/b.mjs', additions: 401, deletions: 0 }];
  assert.notEqual(sizeProblem({ files: big, body: 'Size-exception:\n- G1: existing gate evidence\n' }), null);
  assert.notEqual(sizeProblem({ files: big, body: 'Size-exception:   \nMức: S\n' }), null);
  assert.notEqual(sizeProblem({ files: big, body: '-\nSize-exception: \n' }), null);
  assert.equal(sizeProblem({ files: big, body: '- Size-exception:\tmột migration\n' }), null);
});

test('#254: an oversized PR with an existing author check goes back to Claude, not review or merge', async () => {
  const { renderCheck } = await import('./collab-check.mjs');
  const { prTurn } = await import('./collab-turn.mjs');
  const head = 'c'.repeat(40);
  const owner = b => ({ authorAssociation: 'OWNER', createdAt: '2026-11-07T01:00:00Z', body: b });
  const trust = await import('./collab-trust.mjs');
  // Signed for PR 11 on the live base, as the scripted check and review paths post them (P1-A/P1-B).
  const base = 'e'.repeat(40);
  const checked = owner(renderCheck({ head, base, receipt: trust.signReceipt({ kind: 'check', pr: 11, head, base, result: 'PASS' }), status: 'PASS', exitCode: 0, seconds: 1, date: 'x' }));
  const approved = { ...owner(`Review verdict: APPROVE @ ${head}\nReviewer: Codex\n${trust.verdictSeal({ head, p2: 0, base, receipt: trust.signReceipt({ kind: 'verdict', pr: 11, head, base, result: 'APPROVE' }) })}`), createdAt: '2026-11-07T02:00:00Z' };
  const big = [{ path: 'scripts/b.mjs', additions: 401, deletions: 0 }];
  const pr = extra => ({ number: 11, title: 'ops(collab): x', author: { login: 'honghanh153-creator' }, isCrossRepository: false, isDraft: false, baseRefName: 'collab/integration', headRefOid: head, baseTipOid: base, mergeable: 'MERGEABLE', labels: [], createdAt: '2026-11-07T00:00:00Z', body, files: big, ...extra });
  for (const comments of [[checked], [checked, approved]]) {
    const t = prTurn(pr({ comments }));
    assert.equal(t.turn, 'claude-fix');
    assert.match(t.reason, /PR quá lớn \(401 dòng mã\)/);
  }
  assert.equal(prTurn(pr({ comments: [checked], body: `${body}Size-exception: tách sẽ hỏng contract\n` })).turn, 'codex-review');
  assert.equal(prTurn(pr({ comments: [checked, approved], files: [{ path: 'scripts/b.mjs', additions: 40, deletions: 0 }] })).turn, 'merge');
});
