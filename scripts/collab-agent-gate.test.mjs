import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { decide, gate, readOnlyBash, realBase, releaseAgent, repoOf, setupCommand, targets } from './collab-agent-gate.mjs';
import { claimPath, dispatch, lockFor, preflightWorkspace } from './collab-dispatch.mjs';
import { acquireLock } from './collab-lock.mjs';
import { agentGateWatch, gateHooks, installAgentGate, verifyAgentGate } from './collab-ops-wrapper.mjs';
import { runTick } from './collab-tick.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const git = (cwd, ...args) => String(execFileSync('/usr/bin/git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })).trim();
const ident = ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid'];
const origin = 'https://github.com/honghanh153-creator/la-lanh.git';

// A clone of "our" repository (by origin URL) with a worktree on an agent branch.
function setup({ branch = 'agent/claude/x', url = origin } = {}) {
  const root = realpathSync(mkdtempSync(join(tmpdir(), 'gate-')));
  const repo = join(root, 'repo');
  mkdirSync(repo);
  git(repo, 'init', '-q', '-b', 'main');
  if (url) git(repo, 'remote', 'add', 'origin', url);
  writeFileSync(join(repo, 'a.txt'), 'a\n');
  git(repo, 'add', '.');
  git(repo, ...ident, 'commit', '-q', '-m', 'init');
  const work = join(root, 'work');
  git(repo, 'worktree', 'add', '-q', '-b', branch, work);
  return { root, repo, work };
}
const pass = ({ dir }) => ({ status: 'PASS', reasons: [], dir });
// The real preflight with every machine-specific part faked (tools, hook canary).
const realPre = args => preflightWorkspace({ ...args, which: () => true, canary: () => null, shared: [] });
const noProcs = () => [];
const call = (agent, tool, extra) => ({ agent_id: agent, session_id: 's', cwd: extra.cwd, tool_name: tool, tool_input: extra.input });
const logs = [];
const opts = { preflight: realPre, log: l => logs.push(l), decideFor: args => decide({ ...args, procs: noProcs, shared: [] }) };

test('L06 gate: the main session is never gated, a sub-agent writing outside Git or in another repository passes', () => {
  const s = setup();
  assert.deepEqual(gate({ tool_name: 'Write', cwd: s.repo, tool_input: { file_path: join(s.repo, 'x') } }, opts), { allow: true, reasons: [] });
  const scratch = realpathSync(mkdtempSync(join(tmpdir(), 'gate-out-')));
  assert.equal(gate(call('a1', 'Write', { cwd: scratch, input: { file_path: join(scratch, 'n.txt') } }), opts).allow, true);
  const other = setup({ url: 'https://github.com/someone/else.git' });
  assert.equal(gate(call('a1', 'Edit', { cwd: other.work, input: { file_path: join(other.work, 'a.txt') } }), opts).allow, true);
  const none = setup({ url: null });
  assert.equal(gate(call('a1', 'Edit', { cwd: none.work, input: { file_path: join(none.work, 'a.txt') } }), opts).allow, true);
});

test('L06 gate: writes into a shared clone, onto a protected branch or a parent checkout on another branch are denied', () => {
  const s = setup();
  const shared = decide({ at: s.repo, agentId: 'a1', sessionId: 's', preflight: realPre, procs: noProcs, shared: [s.repo] });
  assert.deepEqual(shared, { allow: false, reasons: ['shared-checkout'] });
  // The parent checkout (main branch) seen from a sub-agent that never moved.
  const r = gate(call('a1', 'Bash', { cwd: s.repo, input: { command: 'touch a.txt' } }), opts);
  assert.equal(r.allow, false);
  assert.ok(r.reasons.includes('branch-not-allowed'));
  const integ = setup({ branch: 'collab/integration' });
  assert.ok(gate(call('a1', 'Write', { cwd: integ.work, input: { file_path: join(integ.work, 'b.txt') } }), opts).reasons.includes('branch-not-allowed'));
});

test('L06 gate: a symlinked file counts where it points; a new file counts from its nearest existing folder', () => {
  const s = setup();
  const scratch = realpathSync(mkdtempSync(join(tmpdir(), 'gate-link-')));
  symlinkSync(join(s.repo, 'a.txt'), join(scratch, 'innocent.txt'));
  assert.equal(realBase(join(scratch, 'innocent.txt')), s.repo);
  assert.equal(realBase(join(s.work, 'new', 'deep', 'file.txt')), s.work);
  const r = gate(call('a1', 'Write', { cwd: scratch, input: { file_path: join(scratch, 'innocent.txt') } }), opts);
  assert.equal(r.allow, false, 'the write lands in the main checkout');
});

test('L06 gate: resolve or Git errors deny; only "not a git repository" means outside', () => {
  const s = setup();
  assert.deepEqual(repoOf(s.work, () => ({ status: 128, stdout: '', stderr: 'fatal: not a git repository (or any parent)' })), { kind: 'outside' });
  assert.throws(() => repoOf(s.work, () => ({ status: 128, stdout: '', stderr: 'fatal: detected dubious ownership' })), /git-error/);
  const failing = { ...opts, repo: () => { throw new Error('git-error'); } };
  assert.throws(() => gate(call('a1', 'Write', { cwd: s.work, input: { file_path: join(s.work, 'z') } }), failing), /git-error/);
});

test('L06 gate: first write claims after the full preflight; the same agent keeps writing on a dirty tree; a second agent is busy', () => {
  const s = setup();
  const w = call('a1', 'Write', { cwd: s.work, input: { file_path: join(s.work, 'b.txt') } });
  assert.deepEqual(gate(w, opts), { allow: true, reasons: [] });
  assert.equal(JSON.parse(readFileSync(claimPath(s.work), 'utf8')).agentId, 'a1');
  writeFileSync(join(s.work, 'b.txt'), 'dirty\n');
  assert.equal(gate(w, opts).allow, true, 'its own edits are not "dirty"');
  git(s.work, 'add', '.');
  git(s.work, ...ident, 'commit', '-q', '-m', 'c');
  assert.equal(gate(w, opts).allow, true, 'a commit by the owner does not lose the claim');
  const other = gate(call('a2', 'Edit', { cwd: s.work, input: { file_path: join(s.work, 'a.txt') } }), opts);
  assert.deepEqual(other, { allow: false, reasons: ['workspace-busy'] });
  // Switching the claimed worktree to integration at the same commit is caught on the next write.
  git(s.work, 'checkout', '-q', '-B', 'collab/integration');
  assert.deepEqual(gate(w, opts), { allow: false, reasons: ['branch-not-allowed'] });
});

test('L06 gate: a dirty workspace cannot be claimed', () => {
  const s = setup();
  writeFileSync(join(s.work, 'left.txt'), 'x\n');
  const r = gate(call('a1', 'Write', { cwd: s.work, input: { file_path: join(s.work, 'b.txt') } }), opts);
  assert.equal(r.allow, false);
  assert.ok(r.reasons.includes('dirty'));
});

test('L06 gate: SubagentStop frees the claim only when nothing runs in the workspace; age alone never frees it', () => {
  const s = setup();
  const w = agent => call(agent, 'Write', { cwd: s.work, input: { file_path: join(s.work, 'b.txt') } });
  assert.equal(gate(w('s1'), opts).allow, true);
  // a1 stopped but a background process still has its working directory in the worktree.
  assert.deepEqual(releaseAgent('s1', { procs: () => [4242] }), { released: 0, kept: 1 });
    const busyStill = decide({ at: s.work, agentId: 's2', sessionId: 's', preflight: realPre, procs: () => [4242], shared: [] });
  assert.deepEqual(busyStill, { allow: false, reasons: ['workspace-busy'] });
  // Six hours later with the process still there: suspect, still busy.
  const late = decide({ at: s.work, agentId: 's2', sessionId: 's', preflight: realPre, procs: () => [4242], shared: [], now: () => new Date(Date.now() + 7 * 3600e3) });
  assert.deepEqual(late, { allow: false, reasons: ['workspace-busy', 'claim-suspect'] });
  // The process is gone: a2 takes over (after its own full preflight).
  assert.equal(gate(w('s2'), opts).allow, true);
  assert.equal(JSON.parse(readFileSync(claimPath(s.work), 'utf8')).agentId, 's2');
  // A clean stop drops the claim; a lsof failure keeps it.
  assert.deepEqual(releaseAgent('s2', { procs: () => { throw new Error('lsof-error'); } }), { released: 0, kept: 1 });
  assert.deepEqual(releaseAgent('s2', { procs: noProcs }), { released: 1, kept: 0 });
  assert.equal(existsSync(claimPath(s.work)), false);
  assert.deepEqual(releaseAgent('nobody', { procs: noProcs }), { released: 0, kept: 0 });
});

test('L06 gate: the dispatcher and the gate exclude each other on the same real path', () => {
  const s = setup();
  // The dispatcher holds the path lock while its worker runs: the gate is busy.
  const held = acquireLock((mkdirSync(dirname(lockFor(s.work)), { recursive: true }), lockFor(s.work)), { staleMs: Infinity });
  const r = gate(call('d1', 'Write', { cwd: s.work, input: { file_path: join(s.work, 'b.txt') } }), { ...opts, decideFor: args => decide({ ...args, procs: noProcs, shared: [], lock: p => acquireLock(lockFor(p), { staleMs: Infinity }) }) });
  assert.deepEqual(r, { allow: false, reasons: ['workspace-busy'] });
  held();
  // The gate's claim (its hook process long gone) blocks the dispatcher.
  assert.equal(gate(call('d1', 'Write', { cwd: s.work, input: { file_path: join(s.work, 'b.txt') } }), opts).allow, true);
  let ran = false;
  const d = dispatch({ dir: s.work, branch: 'agent/claude/x', worker: () => { ran = true; }, preflight: pass, log: join(s.root, 'd.jsonl') });
  assert.deepEqual(d, { status: 'FAIL', reasons: ['claimed-by-agent'] });
  assert.equal(ran, false);
  // Through a symlinked alias the same real path is refused too.
  symlinkSync(s.work, join(s.root, 'alias'));
  assert.deepEqual(dispatch({ dir: join(s.root, 'alias'), branch: 'agent/claude/x', worker: () => { ran = true; }, preflight: pass, log: join(s.root, 'd.jsonl') }).reasons, ['claimed-by-agent']);
  releaseAgent('d1', { procs: noProcs });
  assert.equal(dispatch({ dir: s.work, branch: 'agent/claude/x', worker: () => 'ran', preflight: pass, log: join(s.root, 'd.jsonl') }).status, 'PASS');
});

test('L06 gate: read-only Bash passes anywhere; writes, redirects and unknown commands are checked', () => {
  for (const c of ['git log --oneline -3', 'git -C /x status --porcelain', 'cat a | grep b | wc -l', "sed -n '1,5p' f", 'ls -la 2>/dev/null', 'git config --get remote.origin.url', 'cd /tmp && git diff', 'find . -name x'])
    assert.equal(readOnlyBash(c), true, c);
  for (const c of ['touch a', 'echo x > a', 'sed -i s/a/b/ f', 'git commit -m x', 'find . -delete', 'cat a | tee b', 'echo $(rm -rf x)', 'node build.mjs', 'git branch -D x', 'npm test', 'git config user.name x'])
    assert.equal(readOnlyBash(c), false, c);
  assert.deepEqual(targets({ tool_name: 'Bash', cwd: '/', tool_input: { command: 'git status' } }), []);
  assert.equal(setupCommand('git -C /a/la-lanh-claude fetch -q origin collab/integration && git -C /a/la-lanh-claude worktree add /tmp/w -b agent/claude/x FETCH_HEAD'), true);
  assert.equal(setupCommand('git -C /a/la-lanh-claude worktree add /tmp/w -b main'), false);
  assert.equal(setupCommand('git -C /a/la-lanh-claude reset --hard'), false);
});

test('L06 gate: Bash naming an absolute path inside a checkout is checked even from outside Git', () => {
  const s = setup();
  const scratch = realpathSync(mkdtempSync(join(tmpdir(), 'gate-abs-')));
  const r = gate(call('a1', 'Bash', { cwd: scratch, input: { command: `cp x.txt ${s.repo}/a.txt` } }), opts);
  assert.equal(r.allow, false, 'the main checkout is on main');
});

// The real hook file, spawned as Claude Code runs it: exit 2 + reason on stderr blocks the call.
const hook = (stdin, args = [], env = {}) => spawnSync(process.execPath, [join(here, 'collab-agent-gate.mjs'), ...args], { input: stdin, encoding: 'utf8', env: { ...process.env, ...env }, timeout: 60000 });
test('L06 gate: the hook process fails closed (bad JSON, unknown target) and lets the main session through', () => {
  const bad = hook('{not json');
  assert.equal(bad.status, 2);
  assert.match(bad.stderr, /chặn ghi của dev con \(gate-error\)/);
  const noTarget = hook(JSON.stringify({ agent_id: 'a', tool_name: 'Write', cwd: '/', tool_input: {} }));
  assert.equal(noTarget.status, 2);
  assert.match(noTarget.stderr, /no-target/);
  assert.equal(hook(JSON.stringify({ tool_name: 'Write', cwd: '/', tool_input: { file_path: '/tmp/x' } })).status, 0);
  const s = setup();
  const denied = hook(JSON.stringify({ agent_id: 'a', session_id: 's', tool_name: 'Edit', cwd: s.repo, tool_input: { file_path: join(s.repo, 'a.txt') } }));
  assert.equal(denied.status, 2, 'main branch of a clone of our repo');
  assert.match(denied.stderr, /branch-not-allowed/);
  assert.equal(hook(JSON.stringify({ agent_id: 'a' }), ['--release']).status, 0);
});

test('L06 gate: install keeps other hooks, verify catches removal, changes and disableAllHooks', () => {
  const dir = realpathSync(mkdtempSync(join(tmpdir(), 'gate-settings-')));
  const settings = join(dir, 'settings.json');
  const home = join(dir, 'collab');
  mkdirSync(join(home, 'ops', 'scripts'), { recursive: true });
  writeFileSync(join(home, 'ops', 'scripts', 'collab-agent-gate.mjs'), '// stub\n');
  const other = { matcher: 'Bash', hooks: [{ type: 'command', command: 'node guard.mjs' }] };
  writeFileSync(settings, JSON.stringify({ model: 'x', hooks: { PreToolUse: [other] } }));
  installAgentGate({ home, settings });
  installAgentGate({ home, settings });
  const data = JSON.parse(readFileSync(settings, 'utf8'));
  assert.equal(data.model, 'x');
  assert.deepEqual(data.hooks.PreToolUse, [other, gateHooks(home).PreToolUse], 'installed once, other hook kept');
  assert.equal(data.hooks.PreToolUse[1].hooks[0].onFailure, 'block');
  assert.deepEqual(verifyAgentGate({ home, settings }), []);
  writeFileSync(settings, JSON.stringify({ ...data, hooks: { ...data.hooks, PreToolUse: [other] } }));
  assert.match(verifyAgentGate({ home, settings }).join(), /PreToolUse/);
  const failOpen = structuredClone(data);
  delete failOpen.hooks.PreToolUse[1].hooks[0].onFailure;
  writeFileSync(settings, JSON.stringify(failOpen));
  assert.match(verifyAgentGate({ home, settings }).join(), /PreToolUse/);
  writeFileSync(settings, JSON.stringify({ ...data, disableAllHooks: true }));
  assert.match(verifyAgentGate({ home, settings }).join(), /disableAllHooks/);
  writeFileSync(settings, JSON.stringify(data));
  writeFileSync(join(dir, 'settings.local.json'), JSON.stringify({ disableAllHooks: true }));
  assert.match(verifyAgentGate({ home, settings }).join(), /settings\.local\.json/);
});

test('L06 gate: a broken gate opens one alert a day from the real tick, and closes it once fixed', () => {
  const dir = realpathSync(mkdtempSync(join(tmpdir(), 'gate-alert-')));
  const marker = join(dir, 'm.json');
  const sent = [];
  const closed = [];
  const watch = (bad, today) => agentGateWatch({ verify: () => bad, alert: t => sent.push(t), resolve: t => closed.push(t), marker, today });
  assert.equal(watch(['x'], '2026-11-15').status, 'alerted');
  assert.equal(watch(['x'], '2026-11-15').status, 'already-alerted');
  assert.equal(watch(['x'], '2026-11-16').status, 'alerted');
  assert.equal(sent.length, 2);
  assert.equal(watch([], '2026-11-16').status, 'resolved');
  assert.equal(watch([], '2026-11-16').status, 'ok');
  assert.equal(closed.length, 1);
  // A failed delivery writes no marker, so the next tick tries again.
  const m2 = join(dir, 'm2.json');
  assert.throws(() => agentGateWatch({ verify: () => ['x'], alert: () => { throw new Error('gh down'); }, resolve: () => {}, marker: m2, today: 'd' }));
  assert.equal(existsSync(m2), false);
  // Wiring: the production tick's watchdog calls the gate watch with the ops-alert subject.
  let seen = null;
  const given = runTick({ raw: () => '', json: () => [] }, () => [], { run: g => g, gateWatch: args => { seen = args; return { status: 'ok' }; } });
  given.watchdog();
  assert.ok(seen && typeof seen.alert === 'function' && typeof seen.resolve === 'function' && /^\d{4}-\d{2}-\d{2}$/.test(seen.today));
});
