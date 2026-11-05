// Self-healing helpers for the author check (05.11.2026). Kept apart from collab-check.mjs so the
// preflight can use the process-group runner without an import cycle.
//  - runGroup: every timed step runs detached in its own process group; the deadline kills the
//    whole tree (grandchildren included), and a step running longer than 30 minutes writes a
//    stuck beat at once and raises one ops-alert when it ends.
//  - syncWithIntegration: a PR branch behind collab/integration that merges cleanly is merged and
//    pushed (normal push), so the check runs on the new head next tick instead of going stale.
//  - bodyHash: the preflight record is keyed by head and PR body, so editing the body re-checks.
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { DeadlineError, agentMarker, boundedTimeout, clean, integration, readJson, stateDir, writeJson } from './collab-trust.mjs';

export const bodyHash = body => createHash('sha256').update(String(body ?? '')).digest('hex').slice(0, 16);

export const stepStuckMinutes = 30;
export const stepBeatPath = () => join(stateDir, 'beats', 'check-step.json');

// The supervisor stays alive until the whole group is gone: SIGTERM, then SIGKILL after
// graceMs for members that ignore it, and only then exits (124 on timeout). At stuckMs it writes
// the stuck beat itself, because the tick is blocked inside this step and cannot look.
const groupRunner = `
const { spawn } = require('node:child_process');
const { writeFileSync, mkdirSync } = require('node:fs');
const { dirname } = require('node:path');
const [ms, grace, stuckMs, beatPath, cmd, ...args] = process.argv.slice(1);
const child = spawn(cmd, args, { stdio: 'inherit', detached: true });
const group = -child.pid;
const kill = sig => { try { process.kill(group, sig); } catch {} };
const alive = () => { try { process.kill(group, 0); return true; } catch { return false; } };
const startedAt = new Date().toISOString();
const stuck = setTimeout(() => {
  try { mkdirSync(dirname(beatPath), { recursive: true }); writeFileSync(beatPath, JSON.stringify({ task: 'check-step', step: cmd + ' ' + args.join(' ').slice(0, 80), startedAt, stuckAt: new Date().toISOString(), pid: process.pid }) + '\\n'); } catch {}
}, Number(stuckMs));
let code = 1, timedOut = false, finishing = false;
const finish = () => {
  if (finishing) return;
  finishing = true;
  clearTimeout(stuck);
  kill('SIGTERM');
  const forceAt = Date.now() + Number(grace);
  const poll = setInterval(() => {
    if (!alive()) { clearInterval(poll); process.exit(timedOut ? 124 : code); }
    if (Date.now() >= forceAt) kill('SIGKILL');
  }, 100);
};
const timer = setTimeout(() => { timedOut = true; finish(); }, Number(ms));
child.on('exit', c => { code = c ?? 1; clearTimeout(timer); finish(); });
`;

// Stuck alerts are never sent inline (a gh call here could run past 23:55): they are queued in a
// local file (atomic write) and the watchdog delivers them at the start of its next tick.
export const pendingAlertsPath = () => join(stateDir, 'beats', 'pending-alerts.json');
export function queueAlert(text, nowMs = Date.now()) {
  const list = readJson(pendingAlertsPath(), []);
  writeJson(pendingAlertsPath(), [...(Array.isArray(list) ? list : []), { at: new Date(nowMs).toISOString(), text: clean(text, 1000) }]);
}
// Each delivery needs `perCallMs` (gh's fixed 60 s timeout) before the caller's deadline; what is
// not sent stays queued for the next run.
export function deliverPendingAlerts({ alert, left = () => Infinity, perCallMs = 60000 } = {}) {
  const list = readJson(pendingAlertsPath(), []);
  if (!Array.isArray(list) || !list.length) return { sent: 0, left: 0 };
  const rest = [];
  let sent = 0;
  for (const item of list) {
    if (left() < perCallMs) { rest.push(item); continue; }
    try { alert(item.text); sent += 1; } catch { rest.push(item); }
  }
  writeJson(pendingAlertsPath(), rest);
  return { sent, left: rest.length };
}

export function runGroup(cmd, args, { cwd, env, timeoutMs, graceMs = 5000, stdio = 'inherit', encoding, input, maxBuffer, stuckMs = stepStuckMinutes * 60000, alert = queueAlert } = {}, spawn = spawnSync) {
  const beatPath = stepBeatPath();
  const result = spawn(process.execPath, ['-e', groupRunner, String(Math.max(1000, timeoutMs)), String(graceMs), String(stuckMs), beatPath, cmd, ...args], { cwd, env, stdio, encoding, input, maxBuffer });
  // Real supervisor only: a fake spawn in tests writes nothing.
  const b = readJson(beatPath, null);
  if (b?.stuckAt && !b.doneAt && b.pid === result?.pid) {
    writeJson(beatPath, { ...b, doneAt: new Date().toISOString(), status: result.status });
    try { alert(`Bước "${b.step}" của author check chạy quá ${stepStuckMinutes} phút (bắt đầu ${b.startedAt}, kết thúc với mã ${result.status}). Cả cây tiến trình đã được dừng khi hết giờ.`); } catch {}
  }
  return result;
}

export const syncableBranch = name => /^agent\/(claude|codex)\/[\w./-]+$/.test(String(name ?? '')) && !String(name).includes('..');

// Called in the author clone at the PR head after the fetch of origin/collab/integration.
// Returns null when there is nothing to do (up to date, or not an agent branch). Every git and gh
// step is bounded by left() (time to the absolute deadline minus the cleanup reserve); nothing
// starts once it is spent. A merge cut off by the deadline is aborted and nothing is pushed.
export function syncWithIntegration(pr, { git, gh, left = () => 600000 }) {
  if (!syncableBranch(pr.headRefName)) return null;
  const expired = { status: 'refused', reason: 'hết giờ trước khi đồng bộ với integration' };
  const ms = cap => boundedTimeout(cap, left);
  const base = `origin/${integration}`;
  try {
    try { git(['merge-base', '--is-ancestor', base, 'HEAD'], ms(60000)); return null; } catch (error) { if (error instanceof DeadlineError) throw error; }
    try {
      git(['-c', 'user.name=la-lanh-agent', '-c', 'user.email=la-lanh-agent@users.noreply.github.com', 'merge', '--no-edit', '--no-ff', '-m', `Merge ${integration} into ${pr.headRefName} (auto-sync before author check)`, base], ms(120000));
    } catch (error) {
      try { git(['merge', '--abort'], 10000); } catch {} // cleanup fits inside the reserve
      if (error instanceof DeadlineError || left() <= 0) return expired;
      return { status: 'conflict', turn: 'claude-fix', reason: 'xung đột với collab/integration' };
    }
    const head = git(['rev-parse', 'HEAD'], ms(60000));
    git(['push', 'origin', `HEAD:refs/heads/${pr.headRefName}`], ms(120000));
    // gh has a fixed 60 s timeout: post only when that fits; the push alone already heals the PR.
    if (left() >= 60000) (gh.withDeadline?.(left) ?? gh).comment('pr', pr.number, `Tự đồng bộ: nhánh đi sau ${integration} và merge sạch, nên đã merge ${integration} vào nhánh và push thường (không force). Head mới ${head.slice(0, 12)} cần author check riêng ở tick sau.\n\n${agentMarker} handoff -->`);
    return { status: 'synced', head, reason: 'đã đồng bộ với integration, check lại ở tick sau' };
  } catch (error) {
    if (error instanceof DeadlineError) return expired;
    throw error;
  }
}


// execFileSync-shaped wrapper over runGroup (returns stdout, throws with stdout/stderr on failure),
// for callers such as the Codex review that used execFileSync with a timeout.
export function groupExec(cmd, args, { timeout = 30 * 60000, ...opts } = {}) {
  const result = runGroup(cmd, args, { ...opts, stdio: 'pipe', timeoutMs: timeout });
  if (result.status !== 0) {
    const error = new Error(result.status === 124 ? `${cmd} hết giờ sau ${Math.round(timeout / 1000)} s` : `${cmd} exit ${result.status}`);
    Object.assign(error, { status: result.status, stdout: result.stdout, stderr: result.stderr });
    throw error;
  }
  return result.stdout;
}
