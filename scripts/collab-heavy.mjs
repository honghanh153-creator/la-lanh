// One heavy job at a time on the owner's fanless Mac, and wait while it is hot (collab-auto-loop-plan.md 4.4).
// Usage: node scripts/collab-heavy.mjs [--job NAME] [--wait-min N] [--cool-min N] -- <command> [args...]
import { execFileSync, spawnSync } from 'node:child_process';
import { closeSync, mkdirSync, openSync, readFileSync, rmSync, statSync, writeSync } from 'node:fs';
import { availableParallelism, loadavg } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { clean, stateDir } from './collab-trust.mjs';

export const heavyLockPath = () => join(stateDir, 'heavy.lock');
export const staleLockMinutes = 120;
// Children of a lock holder (a wrapped collab-check, say) must not wait on their own parent.
export const heldEnv = 'LA_LANH_HEAVY_LOCK_HELD';

export const sleepMs = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

const alive = pid => {
  try { process.kill(pid, 0); return true; } catch (error) { return error.code === 'EPERM'; }
};

export function readHolder(path = heavyLockPath()) {
  try { return JSON.parse(readFileSync(path, 'utf8')); } catch { return null; }
}

// A lock left by a dead process or older than two hours belongs to a crashed run.
function dropStale(path, { now = Date.now, isAlive = alive } = {}) {
  let mtime;
  try { mtime = statSync(path).mtimeMs; } catch { return; }
  const holder = readHolder(path);
  if (now() - mtime > staleLockMinutes * 60000 || (holder?.pid && !isAlive(holder.pid))) rmSync(path, { force: true });
}

export function tryAcquire(job, { path = heavyLockPath(), now = Date.now, isAlive = alive, pid = process.pid } = {}) {
  mkdirSync(stateDir, { recursive: true });
  dropStale(path, { now, isAlive });
  let fd;
  try { fd = openSync(path, 'wx'); } catch { return null; }
  try { writeSync(fd, JSON.stringify({ pid, job: clean(job, 80), at: new Date(now()).toISOString() })); } finally { closeSync(fd); }
  return () => { if (readHolder(path)?.pid === pid) rmSync(path, { force: true }); };
}

// Runs fn while holding the lock. Waits up to waitMs; returns { status: 'busy', holder } if it never frees.
export function withHeavyLock(job, fn, { waitMs = 90 * 60000, stepMs = 15000, sleep = sleepMs, env = process.env, ...lock } = {}) {
  if (env[heldEnv] && readHolder(lock.path ?? heavyLockPath())?.pid === Number(env[heldEnv])) return fn({ waitedMs: 0, nested: true });
  let waitedMs = 0;
  let release = tryAcquire(job, lock);
  while (!release && waitedMs < waitMs) {
    sleep(stepMs);
    waitedMs += stepMs;
    release = tryAcquire(job, lock);
  }
  if (!release) return { status: 'busy', holder: readHolder(lock.path ?? heavyLockPath()), waitedMs };
  try { return fn({ waitedMs, nested: false }); } finally { release(); }
}

// Reads `pmset -g therm` and the 1-minute load. Unknown output counts as cool.
export function parseTherm(text) {
  const speed = /CPU_Speed_Limit\s*=\s*(\d+)/i.exec(text);
  if (speed && Number(speed[1]) < 100) return `CPU giới hạn ${speed[1]}%`;
  const level = /(thermal|performance) warning level[^0-9\n]*(\d+)/i.exec(text);
  if (level && Number(level[2]) > 0) return `cảnh báo ${level[1].toLowerCase()} mức ${level[2]}`;
  return null;
}

export function machineHeat({ therm = () => String(execFileSync('/usr/bin/pmset', ['-g', 'therm'], { encoding: 'utf8', timeout: 10000 })), load = () => loadavg()[0], cores = availableParallelism() } = {}) {
  let hot = null;
  try { hot = parseTherm(therm()); } catch {}
  if (hot) return { hot: true, reason: hot };
  const l = load();
  if (l > cores) return { hot: true, reason: `tải ${l.toFixed(1)} > ${cores} nhân` };
  return { hot: false, reason: null };
}

// Heat only slows a run, it never changes the result, so after waitMs the job runs anyway.
export function waitForCool({ waitMs = 15 * 60000, stepMs = 60000, sleep = sleepMs, heat = machineHeat } = {}) {
  let waitedMs = 0;
  let state = heat();
  const first = state.reason;
  while (state.hot && waitedMs < waitMs) {
    sleep(stepMs);
    waitedMs += stepMs;
    state = heat();
  }
  return { waitedMs, cooled: !state.hot, reason: first };
}

export function runHeavy(job, command, args, { spawn = spawnSync, waitMs, coolMs, heat, ...options } = {}) {
  return withHeavyLock(job, ({ nested }) => {
    const cool = nested ? { waitedMs: 0, cooled: true, reason: null } : waitForCool({ waitMs: coolMs, heat, sleep: options.sleep });
    const holder = nested ? process.env[heldEnv] : String(process.pid);
    const result = spawn(command, args, { stdio: 'inherit', env: { ...process.env, [heldEnv]: holder } });
    return { status: 'ran', exitCode: result.status ?? 1, cool };
  }, { waitMs, ...options });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const split = args.indexOf('--');
  const own = split < 0 ? [] : args.slice(0, split);
  const command = split < 0 ? [] : args.slice(split + 1);
  const opt = name => (own.includes(name) ? own[own.indexOf(name) + 1] : undefined);
  const waitMin = Number(opt('--wait-min') ?? 90);
  const coolMin = Number(opt('--cool-min') ?? 15);
  if (!command.length || ![waitMin, coolMin].every(n => Number.isFinite(n) && n >= 0)) {
    process.stderr.write('Usage: node scripts/collab-heavy.mjs [--job NAME] [--wait-min N] [--cool-min N] -- <command> [args...]\n'); process.exit(2);
  }
  const result = runHeavy(opt('--job') ?? command.join(' '), command[0], command.slice(1), { waitMs: waitMin * 60000, coolMs: coolMin * 60000 });
  if (result.status === 'busy') {
    process.stderr.write(`collab-heavy: máy đang chạy việc nặng khác (${clean(JSON.stringify(result.holder), 200)}); thử lại sau.\n`);
    process.exitCode = 75;
  } else {
    if (result.cool.waitedMs) process.stderr.write(`collab-heavy: đã chờ máy hết nóng ${Math.round(result.cool.waitedMs / 60000)} phút (${result.cool.reason}).\n`);
    process.exitCode = result.exitCode;
  }
}
