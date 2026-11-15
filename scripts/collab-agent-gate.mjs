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
import { appendFileSync, lstatSync, mkdirSync, readFileSync, readdirSync, readlinkSync, realpathSync, renameSync, statSync, unlinkSync, writeFileSync } from 'node:fs';
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
// it points, even when that destination does not exist yet: Codex auto-1 on #542), a new one from
// its nearest existing ancestor. Links are followed with lstat/readlink, never existsSync.
export function realBase(target, depth = 0) {
  if (depth > 40) throw new Error('resolve-error');
  let p = target;
  for (;;) {
    let st = null;
    try { st = lstatSync(p); } catch (error) { if (!['ENOENT', 'ENOTDIR'].includes(error?.code)) throw new Error('resolve-error'); }
    if (st?.isSymbolicLink()) return realBase(resolve(dirname(p), readlinkSync(p)), depth + 1);
    if (st) {
      const at = real(p);
      return statSync(at).isDirectory() ? at : dirname(at);
    }
    const up = dirname(p);
    if (up === p) throw new Error('resolve-error');
    p = up;
  }
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

// Shell words with quotes and backslashes honoured (Codex auto-1 on #542: a quoted path with a space
// was cut at the space). Operators come back as { op }. An unbalanced quote throws (deny).
export function shellWords(command) {
  const text = String(command ?? '');
  const out = [];
  let cur = '';
  let has = false;
  let q = null;
  const push = () => { if (has) out.push(cur); cur = ''; has = false; };
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (q === "'") { if (ch === "'") q = null; else cur += ch; continue; }
    if (q === '"') {
      if (ch === '"') q = null;
      else if (ch === '\\' && i + 1 < text.length && '"\\$`'.includes(text[i + 1])) cur += text[++i];
      else cur += ch;
      continue;
    }
    if (ch === "'" || ch === '"') { q = ch; has = true; continue; }
    if (ch === '\\' && i + 1 < text.length) { cur += text[++i]; has = true; continue; }
    if (ch === '\n') { push(); out.push({ op: ';' }); continue; }
    if (/\s/.test(ch)) { push(); continue; }
    if ('|&;<>()'.includes(ch)) {
      push();
      let op = ch;
      while (i + 1 < text.length && '|&;<>'.includes(text[i + 1])) op += text[++i];
      out.push({ op });
      continue;
    }
    cur += ch;
    has = true;
  }
  if (q) throw new Error('unbalanced-quote');
  push();
  return out;
}
const segmentsOf = words => {
  const segs = [[]];
  for (const w of words) {
    if (typeof w === 'object' && ['|', '||', '&&', ';', '&'].includes(w.op)) segs.push([]);
    else segs.at(-1).push(w);
  }
  return segs.filter(s => s.length);
};

// Bash that only reads. Anything not on this list, and any option that writes a file or runs a
// program (sort -o, sed w/e, git --output, rg --pre, git -c), is treated as a write (fail closed).
const readers = new Set(['cat', 'ls', 'head', 'tail', 'wc', 'grep', 'rg', 'jq', 'sort', 'cut', 'tr', 'echo', 'printf', 'pwd', 'stat', 'diff', 'which', 'date', 'cd', 'true', 'basename', 'dirname', 'realpath', 'test', '[']);
const gitReaders = new Set(['log', 'show', 'diff', 'status', 'grep', 'rev-parse', 'ls-files', 'ls-tree', 'blame', 'cat-file', 'merge-base', 'describe', 'shortlog', 'rev-list']);
const writingOption = {
  sort: w => /^(-[a-zA-Z]*o|--output|--compress-program)/.test(w),
  rg: w => /^--pre/.test(w),
  date: w => /^(-[a-zA-Z]*s|--set)/.test(w),
};
export function readOnlyBash(command) {
  const raw = String(command ?? '');
  if (/`|\$\(|<\(|>\(/.test(raw)) return false;
  let words;
  try { words = shellWords(raw.replace(/(^|\s)\d?>&\d(?=\s|$)/g, '$1').replace(/(^|\s)\d?>\s*\/dev\/null(?=\s|$)/g, '$1')); } catch { return false; }
  if (words.some(w => typeof w === 'object' && /[<>]/.test(w.op))) return false;
  return segmentsOf(words).every(segment => {
    if (segment.some(w => typeof w === 'object')) return false;
    // An environment prefix (GIT_EXTERNAL_DIFF=…, PAGER=…) can run a program: never read-only.
    if (/^[A-Za-z_][A-Za-z0-9_]*=/.test(segment[0] ?? '')) return false;
    const [cmd, ...rest] = segment;
    if (!cmd) return true;
    if (readers.has(cmd)) return !rest.some(w => writingOption[cmd]?.(w));
    if (cmd === 'sed') {
      // Only print-by-line-number scripts: no w/W/e/r commands, no in-place.
      const flags = rest.filter(w => w.startsWith('-'));
      const args = rest.filter(w => !w.startsWith('-'));
      return flags.length > 0 && flags.every(f => f === '-n') && args.length >= 1 && /^(\d+|\$)(,(\d+|\$))?p$/.test(args[0]);
    }
    if (cmd === 'find') return !rest.some(w => /^-(delete|exec|execdir|ok|okdir|fprint|fprint0|fprintf|fls)$/.test(w));
    if (cmd === 'git') return readOnlyGit(rest);
    return false;
  });
}

// Git by argument position (Codex auto-2 on #542): before the subcommand only `-C <dir>` is
// allowed (no -c/--exec-path/-p or any other global option); after it, options that write or run a
// program refuse the exemption, and `branch` takes only listing flags (`branch -C` force-copies).
export function readOnlyGit(args) {
  let i = 0;
  while (i < args.length && args[i].startsWith('-')) {
    if (args[i] !== '-C' || i + 1 >= args.length) return false;
    i += 2;
  }
  const sub = args[i];
  const opts = args.slice(i + 1);
  if (!sub) return false;
  if (opts.some(w => /^--(output|ext-diff|open-files-in-pager|exec|upload-pack|receive-pack)/.test(w) || /^-O/.test(w))) return false;
  if (sub === 'config') return opts.length === 2 && opts[0] === '--get' || (opts.length === 1 && opts[0] === '--list');
  if (sub === 'branch') return opts.every(w => ['--show-current', '-a', '-r', '--list', '-v', '-vv'].includes(w));
  return gitReaders.has(sub);
}

// Workspace setup a sub-agent may run against a shared clone: it writes only Git metadata there and
// the new worktree is checked on its first write. Parsed with shell words, so quoted paths work.
export function setupCommand(command) {
  let words;
  try { words = shellWords(command); } catch { return false; }
  if (words.some(w => typeof w === 'object' && !['&&', ';'].includes(w.op))) return false;
  const segs = segmentsOf(words);
  const ref = /^[\w./-]+$/;
  return segs.length > 0 && segs.every(w =>
    (w.length === 2 && w[0] === 'cd')
    // fetch: only `git -C <clone> fetch [-q] origin <branch>`; no refspec with ':' (it can move a
    // checked-out branch), no other option such as --update-head-ok (Codex auto-2 on #542).
    || (w[0] === 'git' && w[1] === '-C' && w[3] === 'fetch' && (w.length === 6 || (w.length === 7 && ['-q', '--quiet'].includes(w[4]))) && w.at(-2) === 'origin' && /^[\w./-]+$/.test(w.at(-1)) && !w.at(-1).startsWith('-'))
    || (w[0] === 'git' && w[1] === '-C' && w[3] === 'worktree' && w[4] === 'add' && w[6] === '-b' && /^agent\/claude\/[\w./-]+$/.test(w[7] ?? '') && (w.length === 8 || (w.length === 9 && ref.test(w[8])))));
}

// Absolute paths a command names, from shell words (quoted spaces kept; `--x=/path` too).
const absPaths = command => {
  let words;
  try { words = shellWords(command); } catch { throw new Error('unbalanced-quote'); }
  const out = [];
  for (const w of words) {
    if (typeof w !== 'string') continue;
    for (const part of [w, ...(w.includes('=') ? [w.slice(w.indexOf('=') + 1)] : [])]) {
      if (part.startsWith('/')) out.push(part);
      else if (part.startsWith('~/')) out.push(join(homedir(), part.slice(2)));
    }
  }
  const unique = [...new Set(out)];
  // Every path is checked; a command naming more than 100 is denied, never cut (Codex auto-2 on #542).
  if (unique.length > 100) throw new Error('too-many-paths');
  return unique;
};

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
