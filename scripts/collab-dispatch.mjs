// Check a workspace before a worker writes in it (lesson L06; agreement of 12.11, item D: "tách
// checkout, kiểm trước giao agent"). A failed check means the worker is never called.
// Plan critiqued by Codex on 14.11 (SỬA), points taken:
// - one exclusive lock per real path, held while the worker runs (two workers, one worktree, or an
//   alias through a symlink, cannot both run);
// - shared checkouts are found by real path against the fixed clones and `git worktree list`;
// - the hook canary proves the installed pre-push hook BLOCKS a synthetic term in a scratch repo
//   (an empty guard list prints "ok", so "ok" proves nothing); it never runs lint and never prints
//   a real guard term;
// - reasons are fixed codes, never stderr text that could carry private data;
// - only the log line outside the worktree is written on FAIL.
// Not covered (Codex 14.11, P1): Claude subagents started with the Agent tool are not processes
// this program starts, so for them this is a check the autopilot runs, not a gate. Publishing
// rights stay with GitHub credentials until the broker (L24) holds them.
// Usage: node scripts/collab-dispatch.mjs --check --dir D --branch B [--profile agent|batch]
//        node scripts/collab-dispatch.mjs --dir D --branch B [--profile …] -- <command> [args]   (runs only on PASS)
import { execFileSync, spawnSync } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import { appendFileSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { acquireLock } from './collab-lock.mjs';
import { integration, stateDir } from './collab-trust.mjs';

export const dispatchLog = () => join(stateDir, 'dispatch.jsonl');
const projectDir = join(homedir(), 'Documents', 'New project');
// Checkouts a worker must never write in directly: each agent's own clone, the ops clone that
// runs the loop, and the old checkout the owner keeps.
export const sharedCheckouts = () => [join(projectDir, 'la-lanh-claude'), join(projectDir, 'la-lanh-codex'), join(projectDir, 'la-lanh'), join(stateDir, 'ops')];
export const protectedBranches = new Set(['main', integration]);
export const profiles = {
  agent: { tools: ['node', 'git', 'gh', 'pnpm', 'uv'], hook: true, branch: /^agent\/claude\/[\w./-]+$/ },
  batch: { tools: ['git', 'uv', 'gh'], hook: false, branch: /^agent\/claude\/copy-batch-[\w-]+$/ },
};

const real = path => { try { return realpathSync(path); } catch { return null; } };
const gitIn = dir => args => String(execFileSync('/usr/bin/git', args, { cwd: dir, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })).trim();
const defaultWhich = (tool, path) => { try { execFileSync('/bin/sh', ['-c', `command -v ${tool}`], { env: { PATH: path }, stdio: 'ignore' }); return true; } catch { return false; } };

// The pre-push hook of the clone this worktree belongs to must be the standard one and must block.
// `hook` is injected in tests; the real one verifies the file and runs the canary.
export function hookCanary(dir, { hooksModule, opsDir = join(stateDir, 'ops'), guardFile = join(stateDir, 'private-guard.txt'), timeoutMs = 30000 } = {}) {
  const bad = hooksModule.verifyHook(dir);
  if (bad.length) return /chưa cài/.test(bad[0]) ? 'hook-missing' : 'hook-not-standard';
  let terms = 0;
  try { terms = readFileSync(guardFile, 'utf8').split('\n').filter(l => l.trim() && !l.trim().startsWith('#')).length; } catch { terms = 0; }
  if (!terms) return 'guard-list-empty';
  // Scratch repo + scratch collab home: the hook reads ops/ and private-guard.txt from it. The
  // synthetic term exists only there and is removed afterwards.
  const scratch = mkdtempSync(join(tmpdir(), 'dispatch-canary-'));
  try {
    const term = `lalanh-canary-${randomBytes(6).toString('hex')}`;
    const home = join(scratch, 'home');
    mkdirSync(home);
    symlinkSync(opsDir, join(home, 'ops'));
    writeFileSync(join(home, 'private-guard.txt'), `${term}\n`);
    const repo = join(scratch, 'repo');
    mkdirSync(repo);
    const git = gitIn(repo);
    git(['init', '-q']);
    writeFileSync(join(repo, 'note.txt'), `${term}\n`);
    git(['add', 'note.txt']);
    git(['-c', 'user.name=canary', '-c', 'user.email=canary@example.invalid', 'commit', '-q', '-m', 'canary']);
    const sha = git(['rev-parse', 'HEAD']);
    const hook = join(hooksModule.hooksDir(dir), 'pre-push');
    const r = spawnSync(hook, ['origin', 'https://example.invalid/x.git'], { cwd: repo, input: `refs/heads/x ${sha} refs/heads/x ${'0'.repeat(40)}\n`,
      env: { ...process.env, LA_LANH_COLLAB_HOME: home }, encoding: 'utf8', timeout: timeoutMs });
    if (r.error?.code === 'ETIMEDOUT' || r.signal) return 'canary-timeout';
    const out = `${r.stdout ?? ''}${r.stderr ?? ''}`;
    if (out.includes(term)) return 'canary-leaks-term';
    if (r.status === 0 || !out.includes('private-guard: chặn')) return 'canary-not-blocked';
    return null;
  } catch { return 'canary-error'; }
  finally { rmSync(scratch, { recursive: true, force: true }); }
}

// Returns { status: 'PASS' | 'FAIL', reasons: [code], dir } and writes nothing.
export function preflightWorkspace({ dir, branch, profile = 'agent', path = process.env.PATH, which = defaultWhich, git = null, shared = sharedCheckouts(), canary = null, expectHead = null } = {}) {
  const p = profiles[profile];
  if (!p) return { status: 'FAIL', reasons: ['unknown-profile'] };
  const reasons = [];
  const at = real(dir);
  if (!at) return { status: 'FAIL', reasons: ['no-dir'] };
  try { if (lstatSync(dir).isSymbolicLink()) reasons.push('dir-is-symlink'); } catch { reasons.push('no-dir'); }
  const run = git ?? gitIn(at);
  let top = null;
  try { top = real(run(['rev-parse', '--show-toplevel'])); } catch { top = null; }
  if (top !== at) reasons.push('not-worktree-root');
  else {
    let current = '';
    try { current = run(['symbolic-ref', '-q', '--short', 'HEAD']); } catch { current = ''; }
    if (!current) reasons.push('detached-head');
    else if (current !== branch) reasons.push('wrong-branch');
    // A worker given a reviewed commit writes on exactly that commit (copy batch: the integration
    // snapshot Codex reviewed).
    if (expectHead) { try { if (run(['rev-parse', 'HEAD']) !== expectHead) reasons.push('head-moved'); } catch { reasons.push('head-moved'); } }
    if (protectedBranches.has(branch) || !p.branch.test(branch ?? '')) reasons.push('branch-not-allowed');
    if (shared.map(real).filter(Boolean).includes(at)) reasons.push('shared-checkout');
    try {
      const listed = run(['worktree', 'list', '--porcelain']).split('\n').filter(l => l.startsWith('worktree ')).map(l => real(l.slice(9)));
      if (listed.filter(x => x === at).length !== 1) reasons.push('shared-checkout');
    } catch { reasons.push('worktree-list-unreadable'); }
    try { if (run(['status', '--porcelain', '--untracked-files=all'])) reasons.push('dirty'); } catch { reasons.push('status-unreadable'); }
  }
  for (const tool of p.tools) if (!which(tool, path)) reasons.push(`missing-tool:${tool}`);
  if (p.hook) {
    const code = canary ? canary(at) : 'hook-unchecked';
    if (code) reasons.push(code);
  }
  const unique = [...new Set(reasons)];
  return { status: unique.length ? 'FAIL' : 'PASS', reasons: unique, dir: at };
}

const lockFor = at => join(stateDir, 'dispatch', `${createHash('sha256').update(at).digest('hex').slice(0, 16)}.lock`);
const defaultLock = at => { mkdirSync(join(stateDir, 'dispatch'), { recursive: true }); return acquireLock(lockFor(at), { staleMs: 3 * 3600000 }); };
const record = (line, path) => { try { mkdirSync(dirname(path), { recursive: true }); appendFileSync(path, `${JSON.stringify(line)}\n`); } catch {} };

// Preflight, then the worker under an exclusive lock on the real path. FAIL: the worker is never
// called and the only write is one log line outside the worktree.
export function dispatch({ dir, branch, profile = 'agent', worker, lock = defaultLock, log = dispatchLog(), now = () => new Date(), preflight = preflightWorkspace, ...checks }) {
  const pre = preflight({ dir, branch, profile, ...checks });
  const base = { at: now().toISOString(), profile, branch: String(branch ?? '').slice(0, 120) };
  if (pre.status !== 'PASS') { record({ ...base, status: 'FAIL', reasons: pre.reasons }, log); return { status: 'FAIL', reasons: pre.reasons }; }
  const release = lock(pre.dir);
  if (!release) { record({ ...base, status: 'FAIL', reasons: ['busy'] }, log); return { status: 'FAIL', reasons: ['busy'] }; }
  try {
    record({ ...base, status: 'PASS' }, log);
    return { status: 'PASS', result: worker(pre.dir) };
  } finally { release(); }
}

// The real hook check for the agent profile, from the hooks installer once it is in this checkout.
export async function realCanary() {
  try {
    const hooksModule = await import('./collab-hooks.mjs');
    return dir => hookCanary(dir, { hooksModule });
  } catch { return () => 'hook-checker-missing'; }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const all = process.argv.slice(2);
  const cut = all.indexOf('--');
  const args = cut >= 0 ? all.slice(0, cut) : all;
  const command = cut >= 0 ? all.slice(cut + 1) : [];
  const flag = name => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
  const dir = flag('--dir');
  const branch = flag('--branch');
  const profile = flag('--profile') ?? 'agent';
  if (!dir || !branch || (!args.includes('--check') && !command.length)) {
    process.stderr.write('Usage: collab-dispatch.mjs --check --dir D --branch B [--profile agent|batch] | --dir D --branch B -- <command> [args]\n');
    process.exit(2);
  }
  const canary = await realCanary();
  if (args.includes('--check')) {
    const r = preflightWorkspace({ dir, branch, profile, canary });
    process.stdout.write(`${JSON.stringify({ status: r.status, reasons: r.reasons })}\n`);
    process.exitCode = r.status === 'PASS' ? 0 : 3;
  } else {
    const r = dispatch({ dir, branch, profile, canary, worker: at => spawnSync(command[0], command.slice(1), { cwd: at, stdio: 'inherit' }).status });
    if (r.status !== 'PASS') { process.stdout.write(`${JSON.stringify(r)}\n`); process.exitCode = 3; }
    else process.exitCode = r.result ?? 1;
  }
}
