// Installs and checks the fixed wrapper the scheduled tasks call (lesson L10, 13.11.2026).
// The source is scripts/ops-run.sh in the ops clone (reviewed collab/integration code); a copy is
// written atomically to ~/.cache/la-lanh-collab/ops-run.sh. It refuses to install from any other
// checkout, so an unreviewed branch never replaces the wrapper the scheduled tasks run.
// Codex #487 (P2): the bytes come from the reviewed collab/integration revision (git show), never
// from the working tree; a clone that is not at that revision or has a local edit is refused.
// Usage: node scripts/collab-ops-wrapper.mjs --install | --verify
import { execFileSync } from 'node:child_process';
import { chmodSync, existsSync, readFileSync, realpathSync, renameSync, statSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { integration, stateDir } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
export const sourcePath = (root = repoRoot) => join(root, 'scripts', 'ops-run.sh');
export const installedPath = (home = stateDir) => join(home, 'ops-run.sh');
export const opsClone = (home = stateDir) => join(home, 'ops');

const real = p => { try { return realpathSync(p); } catch { return null; } };
const gitRaw = (root, args) => execFileSync('/usr/bin/git', ['-C', root, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 120000, maxBuffer: 16 * 1024 * 1024 });
const git = (root, args) => String(gitRaw(root, args)).trim();
const reviewedRef = `refs/remotes/origin/${integration}`;

// The reviewed revision and its ops-run.sh. With fetch, origin is read now (install); without, the
// last fetched tip is used (the tick fetches before every run), so the health check needs no network.
export function reviewedSource({ root = repoRoot, fetch = false } = {}) {
  if (fetch) git(root, ['fetch', '--quiet', 'origin', `+refs/heads/${integration}:${reviewedRef}`]);
  const rev = git(root, ['rev-parse', '--verify', `${reviewedRef}^{commit}`]);
  return { rev, text: gitRaw(root, ['show', `${rev}:scripts/ops-run.sh`]) };
}

export function installWrapper({ root = repoRoot, home = stateDir } = {}) {
  if (real(root) === null || real(root) !== real(opsClone(home))) {
    throw new Error(`chỉ cài từ clone ops (${opsClone(home)}), không cài từ ${root}`);
  }
  const { rev, text } = reviewedSource({ root, fetch: true });
  const head = git(root, ['rev-parse', 'HEAD']);
  if (head !== rev) throw new Error(`clone ops đang ở ${head.slice(0, 12)}, không phải bản ${integration} đã review (${rev.slice(0, 12)})`);
  if (git(root, ['status', '--porcelain'])) throw new Error('clone ops có thay đổi chưa commit, không cài từ bản đã sửa tay');
  const target = installedPath(home);
  const tmp = `${target}.tmp-${process.pid}`;
  writeFileSync(tmp, text);
  chmodSync(tmp, 0o755);
  renameSync(tmp, target);
  return target;
}

export function verifyWrapper({ root = repoRoot, home = stateDir } = {}) {
  const target = installedPath(home);
  if (!existsSync(sourcePath(root))) return ['không thấy scripts/ops-run.sh trong bản này'];
  if (!existsSync(target)) return [`chưa cài ${target}`];
  if (readFileSync(target, 'utf8') !== reviewedSource({ root }).text) return ['bản ops-run.sh đang chạy khác bản đã review, cần cài lại'];
  if (!(statSync(target).mode & 0o100)) return ['ops-run.sh không có quyền chạy'];
  return [];
}

// L19 (Codex auto-1 on #552): the two scheduled reports must read the shared slot snapshot through
// the wrapper. Their prompts live outside the repo, so the tick checks them every run and shows a
// warning when either no longer calls its snapshot step.
export const reportConsumers = [
  { task: 'la-lanh-owner-report', label: 'báo cáo owner 08/14/22', step: /ops-run\.sh snapshot 08\b/ },
  { task: 'la-lanh-retro-2026-11-02', label: 'retro 23:35', step: /ops-run\.sh snapshot retro\b/ },
];
export function verifyReportPrompts({ dir = join(homedir(), '.claude', 'scheduled-tasks') } = {}) {
  const bad = [];
  for (const c of reportConsumers) {
    let text = '';
    try { text = readFileSync(join(dir, c.task, 'SKILL.md'), 'utf8'); } catch { bad.push(`không đọc được prompt ${c.label}`); continue; }
    if (!c.step.test(text)) bad.push(`${c.label} không gọi bước bản chụp chung`);
  }
  return bad;
}

export function wrapperHealth(opts = {}) {
  try {
    const bad = [...verifyWrapper(opts), ...verifyReportPrompts(opts.prompts ? { dir: opts.prompts } : {})];
    return bad.length ? [`- ⚠️ ops-run.sh của tác vụ hẹn giờ: ${bad.join('; ')}`] : ['- ✅ ops-run.sh của tác vụ hẹn giờ: khớp bản đã review'];
  } catch (error) { return [`- ⚠️ ops-run.sh của tác vụ hẹn giờ: chưa kiểm được (${error.message})`]; }
}

if (isMain(import.meta.url)) {
  try {
    if (process.argv.includes('--install')) process.stdout.write(`installed ${installWrapper()}\n`);
    else if (process.argv.includes('--verify')) {
      const bad = verifyWrapper();
      process.stdout.write(bad.length ? `${bad.join('\n')}\n` : 'ops-run.sh ok\n');
      if (bad.length) process.exitCode = 1;
    } else { process.stderr.write('Usage: node scripts/collab-ops-wrapper.mjs --install|--verify\n'); process.exitCode = 2; }
  } catch (error) { process.stderr.write(`collab-ops-wrapper: ${error.message}\n`); process.exitCode = 1; }
}
