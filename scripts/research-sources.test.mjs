import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { changedResearch, researchProblems } from './research-sources.mjs';

// Synthetic research text only.
const good = [
  '# Nghiên cứu thử',
  '',
  '## Kết luận',
  '',
  '- Người chơi mới bỏ cuộc khi luật dài hơn một màn hình [S1].',
  '- Gợi ý ngắn giúp người chơi quay lại [S1][S2].',
  '',
  '| Điều | Nguồn |',
  '|---|---|',
  '| Thẻ luật nên có ví dụ [S2] | S2 |',
  '',
  '## Nguồn đã đọc',
  '',
  '- S1: https://example.org/study — đọc: mục 3, bảng 2',
  '- S2: docs/operations/product-development-process.md — đọc: §1c Research note',
  '',
  '## Bị bác / chưa có nguồn',
  '',
  '- Màu đỏ làm người chơi vội hơn (không tìm được nguồn).',
].join('\n');
const root = new URL('..', import.meta.url).pathname;

test('a conclusion without a read source is rejected even with many URLs', () => {
  assert.deepEqual(researchProblems(good, { path: 'r.md', root }), []);
  const urls = good.replace('- Gợi ý ngắn giúp người chơi quay lại [S1][S2].', '- Gợi ý ngắn giúp người chơi quay lại https://a.example https://b.example https://c.example');
  assert.deepEqual(researchProblems(urls, { path: 'r.md', root }), ['r.md:6: kết luận không trỏ tới nguồn [S…] (nhiều URL không thay được nguồn đã đọc)']);
  const paragraph = good.replace('## Kết luận\n\n', '## Kết luận\n\nĐoạn văn này cũng là một kết luận mà không có nguồn.\n\n');
  assert.match(researchProblems(paragraph, { path: 'r.md', root })[0], /^r\.md:5: kết luận không trỏ tới nguồn/, 'a paragraph is a conclusion too');
  const row = good.replace('| Thẻ luật nên có ví dụ [S2] | S2 |', '| Thẻ luật nên có ví dụ | — |');
  assert.match(researchProblems(row, { path: 'r.md', root })[0], /^r\.md:10: kết luận không trỏ tới nguồn/, 'a table row is a conclusion; its header is not');
});

test('every key is a real, specific source', () => {
  assert.deepEqual(researchProblems(good.replace('[S1].', '[S9].'), { path: 'r.md', root }), ['r.md:5: S9 không có trong "Nguồn đã đọc"']);
  assert.deepEqual(researchProblems(good.replace('https://example.org/study', 'một bài báo'), { path: 'r.md', root }), ['r.md:14: S1 phải là URL https hoặc đường dẫn có thật trong repo']);
  assert.deepEqual(researchProblems(good.replace('docs/operations/product-development-process.md', 'docs/khong-co-file.md'), { path: 'r.md', root }), ['r.md:15: S2 phải là URL https hoặc đường dẫn có thật trong repo']);
  assert.deepEqual(researchProblems(good.replace(' — đọc: mục 3, bảng 2', ''), { path: 'r.md', root }), ['r.md:14: S1 thiếu "— đọc: <phần đã đọc>" cụ thể']);
  assert.deepEqual(researchProblems('# Ghi chú\n\nVài ý.\n', { path: 'n.md', root }), ['n.md: thiếu mục "## Kết luận"', 'n.md: thiếu mục "## Nguồn đã đọc"']);
});

test('no date in a file exempts it: new files in full, edited old files by their added lines', () => {
  const repo = mkdtempSync(join(tmpdir(), 'research-'));
  const git = (...args) => String(execFileSync('/usr/bin/git', ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid', ...args], { cwd: repo, encoding: 'utf8' })).trim();
  git('init', '-q', '-b', 'main');
  mkdirSync(join(repo, 'docs/research'), { recursive: true });
  writeFileSync(join(repo, 'docs/research/2026-10-01-cu.md'), '# Cũ\n\nMột ý cũ không có nguồn.\n');
  git('add', '.');
  git('commit', '-q', '-m', 'base');
  const base = git('rev-parse', 'HEAD');
  writeFileSync(join(repo, 'docs/research/2026-10-01-cu.md'), '# Cũ\n\nMột ý cũ không có nguồn.\nMột ý mới thêm vào file cũ.\n');
  // A back-dated new file is still a new file.
  writeFileSync(join(repo, 'docs/research/2020-01-01-moi.md'), '# Mới\n\n- Kết luận không nguồn.\n');
  git('add', '.');
  git('commit', '-q', '-m', 'change');
  const files = changedResearch({ base, root: repo });
  const problems = files.flatMap(f => researchProblems(f.text, { path: f.path, added: f.added, root: repo }));
  assert.deepEqual(problems, [
    'docs/research/2020-01-01-moi.md: thiếu mục "## Kết luận"',
    'docs/research/2020-01-01-moi.md: thiếu mục "## Nguồn đã đọc"',
    'docs/research/2026-10-01-cu.md:4: dòng mới ở file nghiên cứu cũ phải nằm trong "## Kết luận" (có [S…]), "## Nguồn đã đọc" hoặc "## Bị bác / chưa có nguồn"',
  ], 'the untouched old line is not checked; the added one is');
});
