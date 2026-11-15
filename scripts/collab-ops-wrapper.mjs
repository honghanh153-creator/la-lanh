// Installs and checks the fixed wrapper the scheduled tasks call (lesson L10, 13.11.2026).
// The source is scripts/ops-run.sh in the ops clone (reviewed collab/integration code); a copy is
// written atomically to ~/.cache/la-lanh-collab/ops-run.sh. It refuses to install from any other
// checkout, so an unreviewed branch never replaces the wrapper the scheduled tasks run.
// Codex #487 (P2): the bytes come from the reviewed collab/integration revision (git show), never
// from the working tree; a clone that is not at that revision or has a local edit is refused.
// L06 part 2: it also installs and checks the Claude Code hooks of the sub-agent gate
// (collab-agent-gate.mjs) in ~/.claude/settings.json; other hooks there are kept.
// Usage: node scripts/collab-ops-wrapper.mjs --install | --verify | --install-agent-gate
import { execFileSync } from 'node:child_process';
import { chmodSync, copyFileSync, existsSync, readFileSync, realpathSync, renameSync, statSync, writeFileSync } from 'node:fs';
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

// The sub-agent gate runs from the ops clone (reviewed integration code), with the bundled node.
export const gateScript = (home = stateDir) => join(opsClone(home), 'scripts', 'collab-agent-gate.mjs');
export const settingsPath = (user = homedir()) => join(user, '.claude', 'settings.json');
const nodePath = '$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin';
export const gateHooks = (home = stateDir) => ({
  PreToolUse: { matcher: 'Edit|Write|NotebookEdit|MultiEdit|Bash', hooks: [{ type: 'command', command: `PATH="${nodePath}:/usr/bin:/bin:/usr/sbin" node "${gateScript(home)}"`, timeout: 60, onFailure: 'block' }] },
  SubagentStop: { hooks: [{ type: 'command', command: `PATH="${nodePath}:/usr/bin:/bin:/usr/sbin" node "${gateScript(home)}" --release`, timeout: 60 }] },
});
const isGate = (entry, home) => (entry?.hooks ?? []).some(h => String(h?.command ?? '').includes(gateScript(home)));

// Adds (or replaces) the gate entries; every other hook and setting is kept. A backup is written first.
export function installAgentGate({ home = stateDir, settings = settingsPath(), now = () => new Date() } = {}) {
  let data = {};
  if (existsSync(settings)) {
    data = JSON.parse(readFileSync(settings, 'utf8'));
    copyFileSync(settings, `${settings}.bak-${now().toISOString().replace(/[:.]/g, '-')}`);
  }
  const hooks = { ...(data.hooks ?? {}) };
  for (const [event, entry] of Object.entries(gateHooks(home))) hooks[event] = [...(hooks[event] ?? []).filter(e => !isGate(e, home)), entry];
  const next = { ...data, hooks };
  const tmp = `${settings}.tmp-${process.pid}`;
  writeFileSync(tmp, `${JSON.stringify(next, null, 2)}\n`);
  renameSync(tmp, settings);
  return settings;
}

// Problems with the installed gate: entries missing or changed, fail-open, hooks turned off in a
// settings file this machine reads. It detects removal; it cannot prevent it (same rights as L24).
export function verifyAgentGate({ home = stateDir, settings = settingsPath(), extra = [] } = {}) {
  let data;
  try { data = JSON.parse(readFileSync(settings, 'utf8')); } catch { return [`không đọc được ${settings}`]; }
  const bad = [];
  for (const [event, want] of Object.entries(gateHooks(home))) {
    const got = (data.hooks?.[event] ?? []).filter(e => isGate(e, home));
    if (got.length !== 1 || JSON.stringify(got[0]) !== JSON.stringify(want)) bad.push(`hook ${event} của cổng dev con thiếu hoặc khác bản chuẩn`);
  }
  if (!existsSync(gateScript(home))) bad.push('không thấy collab-agent-gate.mjs trong clone ops');
  for (const file of [settings, settings.replace(/settings\.json$/, 'settings.local.json'), ...extra]) {
    try { if (JSON.parse(readFileSync(file, 'utf8')).disableAllHooks === true) bad.push(`disableAllHooks đang bật trong ${file}`); } catch {}
  }
  return bad;
}

// Tick hook (Codex r2 on the L06 plan: health lines alone open no alert): a broken gate opens one
// ops-alert a day; the marker is written only after the alert was delivered. When the gate is
// healthy again the open alert is closed once.
export const gateAlertSubject = 'cổng dev con';
export function agentGateWatch({ verify = () => verifyAgentGate(), alert, resolve, marker = join(stateDir, 'agent-gate-alert.json'), today }) {
  let state = {};
  try { state = JSON.parse(readFileSync(marker, 'utf8')); } catch { state = {}; }
  const save = next => { const tmp = `${marker}.tmp-${process.pid}`; writeFileSync(tmp, `${JSON.stringify(next)}\n`); renameSync(tmp, marker); };
  let bad;
  try { bad = verify(); } catch (error) { bad = [`chưa kiểm được (${String(error?.message ?? error).slice(0, 120)})`]; }
  if (bad.length) {
    if (state.alertedOn === today) return { status: 'already-alerted' };
    alert(`Cổng kiểm dev con (L06) không ở trạng thái chuẩn: ${bad.join('; ')}. Cài lại bằng: node ~/.cache/la-lanh-collab/ops/scripts/collab-ops-wrapper.mjs --install-agent-gate`);
    save({ alertedOn: today, open: true });
    return { status: 'alerted' };
  }
  if (state.open) { resolve('cổng dev con đã khớp bản chuẩn'); save({ ...state, open: false }); return { status: 'resolved' }; }
  return { status: 'ok' };
}

export function wrapperHealth(opts) {
  try {
    const bad = verifyWrapper(opts);
    return bad.length ? [`- ⚠️ ops-run.sh của tác vụ hẹn giờ: ${bad.join('; ')}`] : ['- ✅ ops-run.sh của tác vụ hẹn giờ: khớp bản đã review'];
  } catch (error) { return [`- ⚠️ ops-run.sh của tác vụ hẹn giờ: chưa kiểm được (${error.message})`]; }
}

if (isMain(import.meta.url)) {
  try {
    if (process.argv.includes('--install-agent-gate')) process.stdout.write(`installed agent gate in ${installAgentGate()}\n`);
    else if (process.argv.includes('--install')) process.stdout.write(`installed ${installWrapper()}\n`);
    else if (process.argv.includes('--verify')) {
      const bad = [...verifyWrapper(), ...verifyAgentGate()];
      process.stdout.write(bad.length ? `${bad.join('\n')}\n` : 'ops-run.sh ok\nagent gate ok\n');
      if (bad.length) process.exitCode = 1;
    } else { process.stderr.write('Usage: node scripts/collab-ops-wrapper.mjs --install|--verify|--install-agent-gate\n'); process.exitCode = 2; }
  } catch (error) { process.stderr.write(`collab-ops-wrapper: ${error.message}\n`); process.exitCode = 1; }
}
