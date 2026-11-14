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
  const checked = owner(renderCheck({ head, status: 'PASS', exitCode: 0, seconds: 1, date: 'x' }));
  const approved = { ...owner(`Review verdict: APPROVE @ ${head}\nReviewer: Codex`), createdAt: '2026-11-07T02:00:00Z' };
  const big = [{ path: 'scripts/b.mjs', additions: 401, deletions: 0 }];
  const pr = extra => ({ number: 11, title: 'ops(collab): x', author: { login: 'honghanh153-creator' }, isCrossRepository: false, isDraft: false, baseRefName: 'collab/integration', headRefOid: head, mergeable: 'MERGEABLE', labels: [], createdAt: '2026-11-07T00:00:00Z', body, files: big, ...extra });
  for (const comments of [[checked], [checked, approved]]) {
    const t = prTurn(pr({ comments }));
    assert.equal(t.turn, 'claude-fix');
    assert.match(t.reason, /PR quá lớn \(401 dòng mã\)/);
  }
  assert.equal(prTurn(pr({ comments: [checked], body: `${body}Size-exception: tách sẽ hỏng contract\n` })).turn, 'codex-review');
  assert.equal(prTurn(pr({ comments: [checked, approved], files: [{ path: 'scripts/b.mjs', additions: 40, deletions: 0 }] })).turn, 'merge');
});

test('mass deletion holds the PR until the owner labels it', async () => {
  const { deletionProblem } = await import('./collab-size.mjs');
  const gone = n => Array.from({ length: n }, (_, i) => ({ path: `apps/web/f${i}.ts`, additions: 0, deletions: 5, changeType: 'DELETED' }));
  assert.equal(deletionProblem({ files: gone(10) }), null);
  assert.match(deletionProblem({ files: gone(11) }), /xoá 11 file/);
  assert.equal(deletionProblem({ files: gone(11), labels: [{ name: 'owner-ok-deletion' }] }), null);
  assert.match(deletionProblem({ files: [{ path: 'a.ts', additions: 100, deletions: 600 }] }), /xoá 600 dòng/);
  assert.equal(deletionProblem({ files: [{ path: 'a.ts', additions: 400, deletions: 600 }] }), null);
  assert.equal(deletionProblem({ files: [{ path: 'pnpm-lock.yaml', additions: 0, deletions: 5000 }] }), null);
});

test('deleted files are counted by status, not by line counts (Codex #354 P2)', async () => {
  const { deletionProblem, isDeletedFile } = await import('./collab-size.mjs');
  const binaries = Array.from({ length: 11 }, (_, i) => ({ path: `apps/web/public/i${i}.png`, additions: 0, deletions: 0, changeType: 'DELETED' }));
  assert.match(deletionProblem({ files: binaries }), /xoá 11 file/);
  const trimmed = Array.from({ length: 11 }, (_, i) => ({ path: `apps/web/f${i}.ts`, additions: 0, deletions: 1, changeType: 'MODIFIED' }));
  assert.equal(deletionProblem({ files: trimmed }), null);
  assert.ok(isDeletedFile({ status: 'D' }) && isDeletedFile({ changeType: 'DELETED' }));
  assert.ok(!isDeletedFile({ changeType: 'MODIFIED' }) && !isDeletedFile({ additions: 0, deletions: 9 }));
});

test('the CI deletion guard reads file status from git (Codex #354 P2)', async () => {
  const { execFileSync, spawnSync } = await import('node:child_process');
  const { mkdtempSync, writeFileSync, rmSync } = await import('node:fs');
  const { tmpdir } = await import('node:os');
  const { join } = await import('node:path');
  const { fileURLToPath } = await import('node:url');
  const dir = mkdtempSync(join(tmpdir(), 'collab-size-del-'));
  const git = (...a) => execFileSync('git', ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid', '-c', 'commit.gpgsign=false', ...a], { cwd: dir, encoding: 'utf8' }).trim();
  try {
    git('init', '-q');
    for (let i = 0; i < 11; i++) { writeFileSync(join(dir, `bin ${i}.png`), Buffer.from([0, 1, 2, i])); writeFileSync(join(dir, `f${i}.ts`), 'a\nb\n'); }
    git('add', '-A'); git('commit', '-qm', 'base');
    const base = git('rev-parse', 'HEAD');
    for (let i = 0; i < 11; i++) writeFileSync(join(dir, `f${i}.ts`), 'a\n');
    git('commit', '-qam', 'trim');
    const trimmed = git('rev-parse', 'HEAD');
    for (let i = 0; i < 11; i++) rmSync(join(dir, `bin ${i}.png`));
    git('commit', '-qam', 'drop');
    const dropped = git('rev-parse', 'HEAD');
    const cli = (b, h) => spawnSync(process.execPath, [fileURLToPath(new URL('./collab-size.mjs', import.meta.url)), '--deletion', b, h, '[]'], { cwd: dir, encoding: 'utf8' });
    assert.equal(cli(base, trimmed).status, 0);
    const held = cli(trimmed, dropped);
    assert.equal(held.status, 1);
    assert.match(held.stdout, /xoá 11 file/);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
