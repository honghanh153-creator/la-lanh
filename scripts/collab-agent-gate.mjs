// Gate for Claude Code sub-agents (lesson L06, part 2: "child-agent dispatch"). A sub-agent started
// with the Agent tool is not a process collab-dispatch.mjs starts, so the check runs where the write
// happens: a PreToolUse hook on Edit|Write|NotebookEdit|Bash. Inside a sub-agent the hook input
// carries agent_id (Claude Code hooks reference, checked 15.11.2026); the main session is not gated.
// Plan critiqued by Codex on 15.11 (two rounds, SỬA), points taken:
// - the write target is resolved from the real path (a symlinked file counts where it points; a new
//   file counts from its nearest existing ancestor), never from a workspace named in the prompt;
// - "outside Git" is only the answer Git gives for a directory that is not a repository; any other
//   resolve, Git or config error denies;
// - the first write of an agent into a workspace takes a claim after the full preflight (clean
//   tree, branch, tools, the real pre-push hook canary); later writes of the same agent check path,
//   branch and claim owner every time (no cached PASS), so its own edits are not "dirty";
// - the claim lives next to the dispatcher's lock (same real-path hash) and is read and written only
//   while holding that lock, so collab-dispatch.mjs and this gate exclude each other;
// - the claim ends only when the agent stopped (SubagentStop) AND no process has its working
//   directory inside the workspace; age alone never frees it (6 h only marks it as suspect);
// - every failure denies (exit 2 inside, `onFailure: "block"` in the installed settings).
// Limits (same machine rights as L24): Claude can remove the hook or start without it; the verify
// in collab-ops-wrapper.mjs and the tick alert only detect that. Bash is checked by its working
// directory and the absolute paths it names; a relative path after `cd` in the same command is not
// seen. The main session is not gated.
// Usage (from the hook): node scripts/collab-agent-gate.mjs            (PreToolUse, JSON on stdin)
//                         node scripts/collab-agent-gate.mjs --release  (SubagentStop, JSON on stdin)
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { appendFileSync, existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, realpathSync, renameSync, statSync, unlinkSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, isAbsolute, join, resolve, sep } from 'node:path';
import { acquireLock } from './collab-lock.mjs';
import { stateDir } from './collab-trust.mjs';
import { claimFree, claimPath, dispatchLog, lockFor, preflightWorkspace, procsIn, protectedBranches, profiles, realCanary, sharedCheckouts } from './collab-dispatch.mjs';
import { isMain } from './is-main.mjs';

export const repoRe = /github\.com[:/]honghanh153-creator\/la-lanh(?:\.git)?\/?$/;
export const suspectMs = 6 * 3600 * 1000;
const writeTools = new Set(['Edit', 'Write', 'NotebookEdit', 'MultiEdit']);

const real = p => realpathSync(p);
const inside = (path, root) => path === root || path.startsWith(root.endsWith(sep) ? root : `${root}${sep}`);
const git = (dir, args) => spawnSync('/usr/bin/git', ['-C', dir, ...args], { encoding: 'utf8', timeout: 20000 });

// The real directory a write lands in: an existing target by its real path (a symlink counts where
// it points), a new one from its nearest existing ancestor.
export function realBase(target) {
  let p = target;
  while (!existsSync(p)) {
    const up = dirname(p);
    if (up === p) throw new Error('resolve-error');
    p = up;
  }
  const at = real(p);
  return statSync(at).isDirectory() ? at : dirname(at);
}

// { kind: 'outside' } when Git says the directory is not a repository; { kind: 'repo', top, ours }
// otherwise. Any other failure throws, so the caller denies.
export function repoOf(dir, run = git) {
  const top = run(dir, ['rev-parse', '--show-toplevel']);
  if (top.status !== 0) {
    if (/not a git repository/i.test(top.stderr ?? '')) return { kind: 'outside' };
    throw new Error('git-error');
  }
  const at = real(top.stdout.trim());
  const url = run(at, ['config', '--get', 'remote.origin.url']);
  if (url.status === 1 && !url.stdout.trim()) return { kind: 'repo', top: at, ours: false };
  if (url.status !== 0) throw new Error('git-error');
  return { kind: 'repo', top: at, ours: repoRe.test(url.stdout.trim()) };
}

// Bash that only reads. Anything not on this list is treated as a write (fail closed).
const readers = new Set(['cat', 'ls', 'head', 'tail', 'wc', 'grep', 'rg', 'jq', 'sort', 'uniq', 'cut', 'tr', 'echo', 'printf', 'pwd', 'stat', 'file', 'diff', 'which', 'date', 'cd', 'true', 'basename', 'dirname', 'realpath', 'test', '[']);
const gitReaders = new Set(['log', 'show', 'diff', 'status', 'grep', 'rev-parse', 'ls-files', 'ls-tree', 'blame', 'cat-file', 'merge-base', 'describe', 'shortlog', 'rev-list']);
export function readOnlyBash(command) {
  const text = String(command ?? '').replace(/\d?>&\d/g, '').replace(/\d?>\s*\/dev\/null/g, '');
  if (/[>`]|\$\(|<\(|\btee\b/.test(text)) return false;
  return text.split(/&&|\|\||;|\||\n/).map(s => s.trim()).filter(Boolean).every(segment => {
    const words = segment.split(/\s+/).filter(w => !/^[A-Z_][A-Z0-9_]*=/.test(w));
    const [cmd, ...rest] = words;
    if (!cmd) return true;
    if (readers.has(cmd)) return true;
    if (cmd === 'sed') return rest.includes('-n') && !rest.some(w => /^-[a-zA-Z]*i/.test(w) || w === '--in-place');
    if (cmd === 'find') return !rest.some(w => /^-(delete|exec|execdir|ok|okdir|fprint|fprintf|fls)$/.test(w));
    if (cmd === 'git') {
      const sub = rest.filter((w, i) => !(w.startsWith('-') || rest[i - 1] === '-C' || rest[i - 1] === '-c'))[0];
      if (sub === 'config') return rest.includes('--get') || rest.includes('--list');
      if (sub === 'branch') return rest.every(w => ['branch', '--show-current', '-a', '-r', '--list', '-v', '-vv'].includes(w) || rest[rest.indexOf(w) - 1] === '-C' || w === '-C');
      return gitReaders.has(sub);
    }
    return false;
  });
}

// Workspace setup a sub-agent may run against a shared clone: it writes only Git metadata there and
// the new worktree is checked on its first write.
export function setupCommand(command) {
  const segs = String(command ?? '').split(/&&|;|\n/).map(s => s.trim()).filter(Boolean);
  return segs.length > 0 && segs.every(s => /^cd\s+\S+$/.test(s) || /^git\s+-C\s+\S+\s+(fetch(\s+-q|\s+--quiet)?\s+origin(\s+[\w./:+-]+)*|worktree\s+add\s+\S+\s+-b\s+agent\/claude\/[\w./-]+(\s+[\w./-]+)?)$/.test(s));
}

const absPaths = command => [...String(command ?? '').matchAll(/(?:^|[\s'"=:])(~\/[^\s'";|&<>()]*|\/[^\s'";|&<>()]+)/g)]
  .map(m => (m[1].startsWith('~/') ? join(homedir(), m[1].slice(2)) : m[1])).slice(0, 25);

// The directories a tool call writes in, or [] for a read-only Bash call.
export function targets(input) {
  const tool = input.tool_name;
  const cwd = input.cwd ?? process.cwd();
  if (writeTools.has(tool)) {
    const file = input.tool_input?.file_path ?? input.tool_input?.notebook_path;
    if (!file) throw new Error('no-target');
    return [realBase(isAbsolute(file) ? file : resolve(cwd, file))];
  }
  if (tool === 'Bash') {
    const command = input.tool_input?.command ?? '';
    if (readOnlyBash(command)) return [];
    return [realBase(cwd), ...absPaths(command).map(realBase)];
  }
  return [];
}

const readClaim = at => { try { return JSON.parse(readFileSync(claimPath(at), 'utf8')); } catch (error) { if (error?.code === 'ENOENT') return null; throw new Error('claim-unreadable'); } };
const writeClaim = (at, claim) => { const p = claimPath(at); const tmp = `${p}.tmp-${process.pid}`; writeFileSync(tmp, `${JSON.stringify(claim)}\n`, { mode: 0o600 }); renameSync(tmp, p); };
const dropClaim = at => { try { unlinkSync(claimPath(at)); } catch {} };

const branchOf = (at, run = git) => { const r = run(at, ['symbolic-ref', '-q', '--short', 'HEAD']); return r.status === 0 ? r.stdout.trim() : ''; };
const allowedBranch = b => Boolean(b) && !protectedBranches.has(b) && profiles.subagent.branch.test(b);

// Decision for one workspace of our repository. Runs under the dispatcher's lock for that path.
export function decide({ at, agentId, sessionId, now = () => new Date(), lock = p => acquireLock(lockFor(p), { staleMs: Infinity, waitMs: 3000 }), preflight, procs = procsIn, shared = sharedCheckouts(), run = git }) {
  if (shared.map(p => { try { return real(p); } catch { return null; } }).filter(Boolean).some(s => s === at)) return { allow: false, reasons: ['shared-checkout'] };
  mkdirSync(dirname(lockFor(at)), { recursive: true });
  const release = lock(at);
  if (!release) return { allow: false, reasons: ['workspace-busy'] };
  try {
    let claim = readClaim(at);
    if (claim && claim.agentId !== agentId) {
      let free = false;
      try { free = claimFree(claim, at, procs); } catch { free = false; }
      if (!free) {
        const suspect = now() - new Date(claim.lastAt ?? claim.at) > suspectMs;
        return { allow: false, reasons: suspect ? ['workspace-busy', 'claim-suspect'] : ['workspace-busy'] };
      }
      dropClaim(at);
      claim = null;
    }
    if (claim) {
      const branch = branchOf(at, run);
      if (!allowedBranch(branch)) return { allow: false, reasons: ['branch-not-allowed'] };
      writeClaim(at, { ...claim, branch, lastAt: now().toISOString(), stoppedAt: null });
      return { allow: true, reasons: [] };
    }
    const branch = branchOf(at, run);
    const pre = preflight({ dir: at, branch, profile: 'subagent' });
    if (pre.status !== 'PASS') return { allow: false, reasons: pre.reasons };
    if (pre.dir !== at) return { allow: false, reasons: ['dir-moved'] };
    writeClaim(at, { agentId, sessionId, workspace: at, branch, at: now().toISOString(), lastAt: now().toISOString(), stoppedAt: null });
    return { allow: true, reasons: [], claimed: true };
  } finally { release(); }
}

const record = (line, log = dispatchLog()) => { try { mkdirSync(dirname(log), { recursive: true }); appendFileSync(log, `${JSON.stringify(line)}\n`); } catch {} };

// The PreToolUse decision. Returns { allow, reasons }. Throws only on a bug; the caller denies then.
export function gate(input, { repo = repoOf, decideFor = decide, preflight, log = record, now = () => new Date() } = {}) {
  if (!input?.agent_id) return { allow: true, reasons: [] };
  const dirs = targets(input);
  const reasons = [];
  const seen = new Set();
  for (const dir of dirs) {
    const r = repo(dir);
    if (r.kind === 'outside' || !r.ours || seen.has(r.top)) continue;
    seen.add(r.top);
    // Workspace setup against a shared clone (fetch, worktree add on an agent/claude branch).
    if (input.tool_name === 'Bash' && setupCommand(input.tool_input?.command) && sharedCheckouts().some(s => { try { return real(s) === r.top; } catch { return false; } })) continue;
    const d = decideFor({ at: r.top, agentId: String(input.agent_id), sessionId: String(input.session_id ?? ''), preflight, now });
    if (!d.allow) reasons.push(...d.reasons);
    if (d.claimed || !d.allow) log({ at: now().toISOString(), source: 'agent-tool', tool: input.tool_name, agentType: String(input.agent_type ?? '').slice(0, 60), status: d.allow ? 'CLAIM' : 'FAIL', reasons: d.reasons });
  }
  const unique = [...new Set(reasons)];
  return { allow: unique.length === 0, reasons: unique };
}

// SubagentStop: marks this agent's claims stopped, and drops those with nothing left running in the
// workspace. Other agents' claims are never touched.
export function releaseAgent(agentId, { dir = join(stateDir, 'dispatch'), procs = procsIn, lock = p => acquireLock(lockFor(p), { staleMs: Infinity, waitMs: 3000 }), now = () => new Date() } = {}) {
  let names = [];
  try { names = readdirSync(dir).filter(n => n.endsWith('.claim.json')); } catch { return { released: 0, kept: 0 }; }
  let released = 0;
  let kept = 0;
  for (const name of names) {
    let claim;
    try { claim = JSON.parse(readFileSync(join(dir, name), 'utf8')); } catch { continue; }
    if (claim?.agentId !== agentId || !claim.workspace) continue;
    const release = lock(claim.workspace);
    if (!release) { kept += 1; continue; }
    try {
      const fresh = readClaim(claim.workspace);
      if (fresh?.agentId !== agentId) continue;
      let busy = true;
      try { busy = procs(claim.workspace).length > 0; } catch { busy = true; }
      if (busy) { writeClaim(claim.workspace, { ...fresh, stoppedAt: now().toISOString() }); kept += 1; }
      else { dropClaim(claim.workspace); released += 1; }
    } finally { release(); }
  }
  return { released, kept };
}

const deny = reasons => {
  process.stderr.write(`collab-agent-gate: chặn ghi của dev con (${reasons.join(', ')}). Dev con chỉ ghi trong worktree riêng của nhánh agent/claude/*, sạch lúc nhận, có hook pre-push; xem scripts/collab-agent-gate.mjs.\n`);
  process.exit(2);
};

if (isMain(import.meta.url)) {
  try {
    const input = JSON.parse(readFileSync(0, 'utf8'));
    if (process.argv.includes('--release')) {
      if (input?.agent_id) releaseAgent(String(input.agent_id));
      process.exit(0);
    }
    const canary = await realCanary();
    const preflight = args => preflightWorkspace({ ...args, canary });
    const r = gate(input, { preflight });
    if (!r.allow) deny(r.reasons);
    process.exit(0);
  } catch (error) {
    deny([/^[a-z-]+$/.test(String(error?.message)) ? error.message : 'gate-error']);
  }
}
