// Author check: run `pnpm check` on the exact PR head, then post the receipt line.
// Usage: node scripts/collab-check.mjs --pr N           (this checkout, must be at the PR head)
//        node scripts/collab-check.mjs --pr N --clone   (dedicated clone ~/.cache/la-lanh-collab/author)
// One check on the machine at a time: two checks share the API and e2e ports and give false receipts.
import { spawnSync, execFileSync } from 'node:child_process';
import { closeSync, existsSync, mkdirSync, openSync, readFileSync, rmSync, statSync, writeSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { agentMarker, clean, integration, isOwnPr, isSha, makeGh, repo, stateDir, vnNow } from './collab-trust.mjs';

// Any heavy test process anywhere on the machine (pnpm check starts with contracts:check).
export const heavyPattern = 'contracts:check|vitest|pytest|playwright';
export function machineBusy(run = execFileSync) {
  try { return String(run('pgrep', ['-fl', heavyPattern], { encoding: 'utf8' })).trim().split('\n')[0].slice(0, 120) || null; }
  catch { return null; }
}

// Run a command in its own process group and kill the whole group at the deadline or on exit,
// so Vite, Playwright or pytest children never outlive the check.
// The supervisor stays alive until the whole group is gone: SIGTERM, then SIGKILL after
// graceMs for members that ignore it, and only then exits (124 on timeout).
const groupRunner = `
const { spawn } = require('node:child_process');
const [ms, grace, cmd, ...args] = process.argv.slice(1);
const child = spawn(cmd, args, { stdio: 'inherit', detached: true });
const group = -child.pid;
const kill = sig => { try { process.kill(group, sig); } catch {} };
const alive = () => { try { process.kill(group, 0); return true; } catch { return false; } };
let code = 1, timedOut = false, finishing = false;
const finish = () => {
  if (finishing) return;
  finishing = true;
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
export function runGroup(cmd, args, { cwd, env, timeoutMs, graceMs = 5000, stdio = 'inherit' }, spawn = spawnSync) {
  return spawn(process.execPath, ['-e', groupRunner, String(Math.max(1000, timeoutMs)), String(graceMs), cmd, ...args], { cwd, env, stdio });
}

// Automatic checks start nothing after 23:30 and end by 23:55 (plan §3.1); direct runs get 90 minutes.
// The budget ends at the exact 23:55:00 instant minus the cleanup reserve, so SIGTERM, the grace
// period and SIGKILL all finish before the cutoff (#140).
export const cleanupReserveMs = 15000;
export function checkBudgetMs({ auto, clock = vnNow, nowMs = Date.now }) {
  if (!auto) return 90 * 60000;
  const t = clock();
  const minute = t.hour * 60 + t.minute;
  if (minute < 8 * 60 + 50 || minute >= 23 * 60 + 30) return 0;
  const byMinute = Math.min(90, 23 * 60 + 55 - minute) * 60000;
  const cutoff = Date.parse(`${t.date}T23:55:00+07:00`);
  const exact = Number.isFinite(cutoff) ? cutoff - nowMs() : byMinute;
  return Math.max(0, Math.min(byMinute, exact) - cleanupReserveMs);
}

const alive = pid => { try { process.kill(pid, 0); return true; } catch { return false; } };
export function withCheckLock(fn) {
  mkdirSync(stateDir, { recursive: true });
  const path = join(stateDir, 'check.lock');
  try {
    const pid = Number(readFileSync(path, 'utf8'));
    if (!alive(pid) || Date.now() - statSync(path).mtimeMs > 2 * 3600000) rmSync(path);
  } catch {}
  let fd;
  try { fd = openSync(path, 'wx'); } catch { return { status: 'busy', reason: 'một author check khác đang chạy' }; }
  try { writeSync(fd, String(process.pid)); return fn(); } finally { closeSync(fd); rmSync(path, { force: true }); }
}

export function renderCheck({ head, status, exitCode, seconds, date }) {
  return [
    `Author check: ${status} @ ${head}`,
    '',
    `Lệnh: \`pnpm check\` · exit ${exitCode} · ${seconds}s · ${date}. Chạy trên checkout sạch, \`HEAD == ${head.slice(0, 12)}\`.`,
    status === 'PASS' ? 'Đây là bằng chứng của tác giả, không thay review.' : 'Lượt tiếp theo là Claude sửa.',
    '',
    `${agentMarker} author-check sha=${head} -->`,
  ].join('\n');
}

export function runCheck(number, { gh = makeGh(), cwd = process.cwd(), git = args => String(execFileSync('/usr/bin/git', args, { cwd, encoding: 'utf8' })).trim(), spawn = spawnSync, now = () => Date.now(), busy = machineBusy } = {}) {
  return withCheckLock(() => checkOnce(number, { gh, cwd, git, spawn, now, busy, budget: () => 90 * 60000 }));
}

function checkOnce(number, { gh, cwd, git, spawn, now, busy, budget }) {
  const pr = gh.pr(number);
  if (!isOwnPr(pr)) return { status: 'refused', reason: 'PR không phải của owner hoặc từ fork: không chạy code của nó' };
  const head = git(['rev-parse', 'HEAD']);
  if (!isSha(pr.headRefOid) || head !== pr.headRefOid) return { status: 'refused', reason: `HEAD ${head.slice(0, 12)} không phải head của PR ${String(pr.headRefOid).slice(0, 12)}` };
  if (git(['status', '--porcelain'])) return { status: 'refused', reason: 'checkout có thay đổi chưa commit' };
  const other = busy();
  if (other) return { status: 'busy', reason: `máy đang chạy check khác: ${clean(other, 120)}` };
  const timeoutMs = budget();
  if (timeoutMs <= 0) return { status: 'refused', reason: 'ngoài giờ chạy tự động (sau 23:30)' };
  const started = now();
  // CI=1: Playwright starts its own preview server instead of reusing one left by another checkout.
  const result = runGroup('pnpm', ['check'], { cwd, timeoutMs, env: { ...process.env, CI: '1' } }, spawn);
  const exitCode = result.status ?? 1;
  // A file the check rewrote means the receipt would not describe the committed head.
  const dirty = Boolean(git(['status', '--porcelain']));
  const status = exitCode === 0 && !dirty && git(['rev-parse', 'HEAD']) === head ? 'PASS' : 'FAIL';
  gh.comment('pr', pr.number, renderCheck({ head, status, exitCode, seconds: Math.round((now() - started) / 1000), date: new Date(started).toISOString() }));
  return { status, exitCode, dirty };
}

const git = (args, cwd, run) => String(run('/usr/bin/git', args, { cwd, encoding: 'utf8', timeout: 600000, maxBuffer: 64 * 1024 * 1024 })).trim();

// A clone only for author checks, so no agent checkout is switched under anyone.
// Ignored build outputs (node_modules, .venv, ephemeris build) are kept between runs.
export class DeadlineError extends Error {}

// Every preparation step is bounded by the time left before the absolute deadline;
// install and make run as process groups so nothing they start survives the cutoff.
export function prepareAuthorClone(number, head, run = execFileSync, { deadlineMs = Infinity, nowMs = Date.now, group = runGroup } = {}) {
  const left = cap => {
    const ms = Math.min(cap, deadlineMs - nowMs());
    if (ms <= 0) throw new DeadlineError('hết giờ khi đang chuẩn bị clone');
    return ms;
  };
  const step = (args, cwd, cap) => String(run('/usr/bin/git', args, { cwd, encoding: 'utf8', timeout: left(cap), maxBuffer: 64 * 1024 * 1024 })).trim();
  const build = (cmd, args, cap) => {
    const ok = group(cmd, args, { cwd: dir, timeoutMs: left(cap), stdio: 'ignore' }).status === 0;
    if (!ok && nowMs() >= deadlineMs) throw new DeadlineError('hết giờ khi đang chuẩn bị clone');
    return ok;
  };
  const dir = join(stateDir, 'author');
  if (!existsSync(join(dir, '.git'))) {
    mkdirSync(stateDir, { recursive: true });
    step(['clone', '--quiet', '--no-checkout', `https://github.com/${repo}.git`, dir], stateDir, 600000);
  }
  step(['fetch', '--quiet', '--force', 'origin', `+refs/heads/${integration}:refs/remotes/origin/${integration}`, `+refs/pull/${Number(number)}/head:refs/remotes/pr/${Number(number)}`], dir, 300000);
  step(['checkout', '--quiet', '--force', '--detach', head], dir, 120000);
  step(['clean', '-fdq'], dir, 120000);
  const actual = step(['rev-parse', 'HEAD'], dir, 60000);
  if (actual !== head) throw new Error(`Author clone is at ${actual}, not ${head}.`);
  if (!build('pnpm', ['install', '--frozen-lockfile', '--offline'], 900000)) {
    if (!build('pnpm', ['install', '--frozen-lockfile'], 900000)) throw new Error('pnpm install failed in the author clone');
  }
  if (!build('make', ['-C', 'vendor/swisseph'], 600000)) throw new Error('ephemeris build failed in the author clone');
  left(1);
  return dir;
}

export function runCheckInClone(number, { gh = makeGh(), run = execFileSync, auto = false, clock = vnNow, ...rest } = {}) {
  const pr = gh.pr(number);
  if (!isSha(pr.headRefOid)) throw new Error('PR head SHA unavailable.');
  // Never fetch, build or run a PR that is not the owner's own branch (fork or outside author).
  if (!isOwnPr(pr)) return { status: 'refused', reason: 'PR không phải của owner hoặc từ fork: không chạy code của nó' };
  if (checkBudgetMs({ auto, clock }) <= 0) return { status: 'refused', reason: 'ngoài giờ chạy tự động (sau 23:30)' };
  // Refuse before touching the clone when another check owns the machine.
  const other = (rest.busy ?? machineBusy)();
  if (other) return { status: 'busy', reason: `máy đang chạy check khác: ${clean(other, 120)}` };
  const nowMs = rest.nowMs ?? Date.now;
  const deadlineMs = nowMs() + checkBudgetMs({ auto, clock, nowMs });
  return withCheckLock(() => {
    let cwd;
    try { cwd = prepareAuthorClone(number, pr.headRefOid, run, { deadlineMs, nowMs, group: rest.group ?? runGroup }); }
    catch (error) { if (error instanceof DeadlineError) return { status: 'refused', reason: error.message }; throw error; }
    // The clock is read again after the clone and install, which can take minutes.
    const budget = () => Math.min(checkBudgetMs({ auto, clock, nowMs }), deadlineMs - nowMs());
    return checkOnce(number, { gh, cwd, git: args => git(args, cwd, run), spawn: rest.spawn ?? spawnSync, now: rest.now ?? (() => Date.now()), busy: rest.busy ?? machineBusy, budget });
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const number = Number(args[args.indexOf('--pr') + 1]);
  if (!args.includes('--pr') || !Number.isInteger(number) || number <= 0) {
    process.stderr.write('Usage: node scripts/collab-check.mjs --pr N\n'); process.exit(2);
  }
  try {
    const result = args.includes('--clone') ? runCheckInClone(number) : runCheck(number);
    process.stdout.write(`${JSON.stringify(result)}\n`);
    if (result.status !== 'PASS') process.exitCode = 3;
  } catch (error) { process.stderr.write(`collab-check failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
}
