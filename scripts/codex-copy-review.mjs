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

// `reviewed` maps id -> digest of the text Codex saw; an entry whose text changed since is left alone.
export function applyDecisions(registry, decisions, date, reviewed = null) {
  const approve = new Set(decisions.filter(d => d.decision === 'approve').map(d => d.id));
  const entries = registry.entries.map(e =>
    e.status === 'pending' && !ownerOnly.has(e.category) && approve.has(e.id)
      && (!reviewed || reviewed.get(e.id) === digest(e.text))
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
    '## Cổng (docs/operations/product-development-process.md §3–4)', '',
    'Mức: M — câu đã duyệt sẽ hiện cho người dùng.', '',
    'Người dùng thấy gì: một số câu đọc đã được duyệt sẽ hiện thay cho câu cũ.', '',
    '- G1 Tài liệu / US-AC: luật cờ chờ duyệt trong docs/operations/decision-checklist.md (owner 06.11.2026).',
    '- G2 UI/UX: không đổi giao diện; chỉ đổi câu đã có chỗ hiển thị.',
    '- G3 Câu chữ (owner duyệt nếu có câu mới): Codex duyệt lô theo quyết định owner 06.11; không có nhóm owner-only.',
    '- G4 BE + kiến trúc: chỉ đổi copy_registry.json và hash trong fallback-approval.json.',
    '- G5 FE: không áp dụng.',
    '- G6 QC (test đỏ→xanh, author check): scripts.fallback_approval --check chạy trong author check.',
    '- G7 Bảo mật: không đụng phiên, quyền, secret hay log; Codex chạy read-only.',
    '- G8 Data privacy: không có dữ liệu cá nhân; chỉ câu mẫu trong repo.',
    '- G9 Release: không áp dụng cho PR vào integration',
    '- G10 Chi phí / license: một lượt Codex CLI có sẵn, không thêm chi phí.', '',
    `${agentMarker} copy-batch date=${date} -->`, '',
    '🤖 Generated with [Claude Code](https://claude.com/claude-code)',
  ].join('\n'));
}

function runCodex(prompt, outPath, run) {
  run(codexBin, ['exec', '-s', 'read-only', '--ephemeral', '-m', codexModel, '-C', root,
    '--output-schema', schemaPath, '-o', outPath, '--color', 'never', '-'],
  { input: prompt, encoding: 'utf8', timeout: 20 * 60000, maxBuffer: 16 * 1024 * 1024 });
  return JSON.parse(readFileSync(outPath, 'utf8'));
}

// Writes the batch on its own branch from the reviewed integration commit and opens a PR, so a
// newer integration change to the registry is merged by git, never overwritten.
function openBatchPr(registry, body, date, base, run) {
  const branch = `agent/claude/copy-batch-${date.replaceAll('-', '')}`;
  const dir = mkdtempSync(join(tmpdir(), 'copy-batch-'));
  const git = args => run('git', args, { cwd: root, encoding: 'utf8' });
  git(['worktree', 'add', '-q', '-b', branch, join(dir, 'w'), base]);
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

export function main(argv, { run = execFileSync, out = process.stdout, registryPath = null } = {}) {
  const dryRun = argv.includes('--dry-run');
  const fakeAt = argv.indexOf('--fake-codex');
  // Review a pinned integration snapshot unless a test passes its own registry file.
  let base = null;
  let registry;
  if (registryPath) {
    registry = JSON.parse(readFileSync(registryPath, 'utf8'));
  } else {
    const git = args => String(run('git', args, { cwd: root, encoding: 'utf8' }) ?? '').trim();
    git(['fetch', '-q', 'origin', integration]);
    base = git(['rev-parse', `origin/${integration}`]);
    registry = JSON.parse(git(['show', `${base}:${registryRel}`]));
  }
  const pending = selectPending(registry);
  if (!pending.length) { out.write('no pending copy\n'); return { status: 'empty' }; }
  const date = vnNow().date;
  const result = fakeAt >= 0
    ? JSON.parse(readFileSync(argv[fakeAt + 1], 'utf8'))
    : runCodex(buildPrompt(pending), join(mkdtempSync(join(tmpdir(), 'copy-codex-')), 'out.json'), run);
  const decisions = validateDecisions(result, pending);
  const reviewed = new Map(pending.map(e => [e.id, digest(e.text)]));
  const next = applyDecisions(registry, decisions, date, reviewed);
  const changed = next.entries.some((e, i) => e !== registry.entries[i]);
  const body = renderBody(decisions, date);
  if (dryRun) { out.write(`${JSON.stringify({ registry: next, body }, null, 1)}\n`); return { status: 'dry-run', registry: next, body }; }
  if (!changed) { out.write('no copy approved in this batch\n'); return { status: 'no-approvals', registry: next, body }; }
  if (!base) throw new Error('publishing needs the integration snapshot (no --registry file)');
  const url = openBatchPr(next, body, date, base, run);
  out.write(`${url}\n`);
  return { status: 'opened', url };
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  try { main(process.argv.slice(2)); } catch (error) { process.stderr.write(`codex-copy-review failed: ${error.message}\n`); process.exitCode = 1; }
}
