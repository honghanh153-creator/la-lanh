// Installs and checks the fixed wrapper the scheduled tasks call (lesson L10, 13.11.2026).
// The source is scripts/ops-run.sh in the ops clone (reviewed collab/integration code); a copy is
// written atomically to ~/.cache/la-lanh-collab/ops-run.sh. It refuses to install from any other
// checkout, so an unreviewed branch never replaces the wrapper the scheduled tasks run.
// Usage: node scripts/collab-ops-wrapper.mjs --install | --verify
import { chmodSync, existsSync, readFileSync, realpathSync, renameSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { stateDir } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
export const sourcePath = (root = repoRoot) => join(root, 'scripts', 'ops-run.sh');
export const installedPath = (home = stateDir) => join(home, 'ops-run.sh');
export const opsClone = (home = stateDir) => join(home, 'ops');

const real = p => { try { return realpathSync(p); } catch { return null; } };

export function installWrapper({ root = repoRoot, home = stateDir } = {}) {
  if (real(root) === null || real(root) !== real(opsClone(home))) {
    throw new Error(`chỉ cài từ clone ops (${opsClone(home)}), không cài từ ${root}`);
  }
  const target = installedPath(home);
  const tmp = `${target}.tmp-${process.pid}`;
  writeFileSync(tmp, readFileSync(sourcePath(root)));
  chmodSync(tmp, 0o755);
  renameSync(tmp, target);
  return target;
}

export function verifyWrapper({ root = repoRoot, home = stateDir } = {}) {
  const target = installedPath(home);
  if (!existsSync(sourcePath(root))) return ['không thấy scripts/ops-run.sh trong bản này'];
  if (!existsSync(target)) return [`chưa cài ${target}`];
  if (readFileSync(target, 'utf8') !== readFileSync(sourcePath(root), 'utf8')) return ['bản ops-run.sh đang chạy khác bản đã review, cần cài lại'];
  if (!(statSync(target).mode & 0o100)) return ['ops-run.sh không có quyền chạy'];
  return [];
}

export function wrapperHealth(opts) {
  try {
    const bad = verifyWrapper(opts);
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
