// Codex approves the daily batch of pending copy (owner decision 06.11.2026).
// Usage: node scripts/codex-copy-review.mjs [--dry-run] [--fake-codex decisions.json]
// Codex runs read-only, the same way scripts/codex-review.mjs calls it. Privacy, consent, crisis
// and safety copy is never sent: it stays owner-only. The result goes into a PR on
// agent/claude/copy-batch-YYYYMMDD; the script never writes main or collab/integration and
// never posts owner reply words.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { agentMarker, assertAgentBody, integration, repo, vnNow } from './collab-trust.mjs';

const here = dirname(fileURLToPath(import.meta.url));
export const root = join(here, '..');
export const registryRel = 'apps/api/app/domains/content/copy_registry.json';
export const schemaPath = join(here, 'codex-copy-review-schema.json');
export const codexBin = process.env.CODEX_BIN || '/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex';
export const codexModel = 'gpt-6.1-sol';
export const ownerOnly = new Set(['privacy', 'consent', 'crisis', 'safety']);
export const ruleDocs = [
  'docs/foundation/la-lanh-plain-vietnamese-content-standard.md',
  'docs/operations/decision-checklist.md',
];

// Same digest as app/domains/content/copy_approval.py (sha256 of the NFC text).
export const digest = text => createHash('sha256').update(String(text).normalize('NFC')).digest('hex');

export function selectPending(registry) {
  return (registry.entries ?? []).filter(e => e.status === 'pending' && !ownerOnly.has(e.category));
}

export function buildPrompt(pending) {
  const rows = pending.map(e => JSON.stringify({ id: e.id, category: e.category, text: e.text })).join('\n');
  return [
    'Bạn duyệt câu chữ mới của Lá Lành cho người dùng. Chỉ đọc, không sửa file.',
    `Đọc luật trong: ${ruleDocs.join(', ')}.`,
    'Duyệt (approve) chỉ khi câu: êm, rõ, dễ hiểu ngay lần đầu; tiếng Việt đời thường; có chủ thể;',
    'không dự đoán sự kiện đời sống; không giải thích cơ chế kỹ thuật; không đụng quyền riêng tư,',
    'đồng ý, khủng hoảng hay an toàn. Nghi ngờ thì reject và nêu lý do ngắn.',
    'Trả về đúng schema: một quyết định cho mỗi id dưới đây.',
    rows,
  ].join('\n');
}

export function validateDecisions(out, pending) {
  const ids = new Set(pending.map(e => e.id));
  const seen = new Set();
  for (const d of out?.decisions ?? []) {
    if (!ids.has(d.id) || seen.has(d.id)) throw new Error(`unexpected decision id: ${d.id}`);
    if (d.decision !== 'approve' && d.decision !== 'reject') throw new Error(`bad decision for ${d.id}`);
    seen.add(d.id);
  }
  return (out?.decisions ?? []);
}

export function applyDecisions(registry, decisions, date) {
  const approve = new Set(decisions.filter(d => d.decision === 'approve').map(d => d.id));
  const entries = registry.entries.map(e =>
    e.status === 'pending' && !ownerOnly.has(e.category) && approve.has(e.id)
      ? { ...e, status: 'approved', approver: 'codex', date, digest: digest(e.text) }
      : e);
  return { ...registry, entries };
}

export function renderBody(decisions, date) {
  const rows = decisions.map(d => `| \`${d.id}\` | ${d.decision} | ${String(d.reason).replace(/[|\n]/g, ' ')} |`);
  return assertAgentBody([
    `Lô copy chờ duyệt ngày ${date}, do Codex (read-only) chấm theo chuẩn tiếng Việt dễ hiểu.`,
    'Câu bị reject vẫn ở trạng thái pending; app vẫn dùng câu đã duyệt hiện tại.',
    'Copy về quyền riêng tư, đồng ý, khủng hoảng, an toàn không có trong lô này (chỉ owner duyệt).',
    '', '| Mục | Kết quả | Lý do |', '| --- | --- | --- |', ...rows, '',
    'Mức: S', '', `${agentMarker} copy-batch date=${date} -->`, '',
    '🤖 Generated with [Claude Code](https://claude.com/claude-code)',
  ].join('\n'));
}

function runCodex(prompt, outPath, run) {
  run(codexBin, ['exec', '-s', 'read-only', '--ephemeral', '-m', codexModel, '-C', root,
    '--output-schema', schemaPath, '-o', outPath, '--color', 'never', '-'],
  { input: prompt, encoding: 'utf8', timeout: 20 * 60000, maxBuffer: 16 * 1024 * 1024 });
  return JSON.parse(readFileSync(outPath, 'utf8'));
}

// Writes the batch on its own branch from origin/collab/integration and opens a PR.
function openBatchPr(registry, body, date, run) {
  const branch = `agent/claude/copy-batch-${date.replaceAll('-', '')}`;
  const dir = mkdtempSync(join(tmpdir(), 'copy-batch-'));
  const git = args => run('git', args, { cwd: root, encoding: 'utf8' });
  git(['fetch', '-q', 'origin', integration]);
  git(['worktree', 'add', '-q', '-b', branch, join(dir, 'w'), `origin/${integration}`]);
  const work = join(dir, 'w');
  writeFileSync(join(work, registryRel), `${JSON.stringify(registry, null, 1)}\n`);
  run('uv', ['run', 'python', '-m', 'scripts.fallback_approval'], { cwd: join(work, 'apps/api'), encoding: 'utf8' });
  const at = args => run('git', args, { cwd: work, encoding: 'utf8' });
  at(['add', registryRel, 'docs/operations/fallback-approval.json']);
  at(['commit', '-q', '-m', `content(copy): Codex copy batch ${date}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`]);
  at(['push', '-q', 'origin', `HEAD:${branch}`]);
  const bodyPath = join(dir, 'body.md');
  writeFileSync(bodyPath, body);
  return run('gh', ['pr', 'create', '--repo', repo, '--base', integration, '--head', branch,
    '--title', `content(copy): Codex copy batch ${date}`, '--label', 'area:content', '--body-file', bodyPath],
  { cwd: work, encoding: 'utf8' }).trim();
}

export function main(argv, { run = execFileSync, out = process.stdout, registryPath = join(root, registryRel) } = {}) {
  const dryRun = argv.includes('--dry-run');
  const fakeAt = argv.indexOf('--fake-codex');
  const registry = JSON.parse(readFileSync(registryPath, 'utf8'));
  const pending = selectPending(registry);
  if (!pending.length) { out.write('no pending copy\n'); return { status: 'empty' }; }
  const date = vnNow().date;
  const result = fakeAt >= 0
    ? JSON.parse(readFileSync(argv[fakeAt + 1], 'utf8'))
    : runCodex(buildPrompt(pending), join(mkdtempSync(join(tmpdir(), 'copy-codex-')), 'out.json'), run);
  const decisions = validateDecisions(result, pending);
  const next = applyDecisions(registry, decisions, date);
  const body = renderBody(decisions, date);
  if (dryRun) { out.write(`${JSON.stringify({ registry: next, body }, null, 1)}\n`); return { status: 'dry-run', registry: next, body }; }
  const url = openBatchPr(next, body, date, run);
  out.write(`${url}\n`);
  return { status: 'opened', url };
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  try { main(process.argv.slice(2)); } catch (error) { process.stderr.write(`codex-copy-review failed: ${error.message}\n`); process.exitCode = 1; }
}
