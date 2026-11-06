// Failure logs and the agent test guard for the author check (05.11.2026: a FAIL on #248 kept no
// log, and an agent's tests probably ran during the check).
// - The full `pnpm check` output goes to logs/check-<pr>-<sha12>.log (last 30 kept); a FAIL
//   receipt names only the failing `pnpm <step>` and the log file name; no log line is published.
// - scripts/collab-test-guard.mjs holds test-guard.lock while an agent's tests run; the author
//   check waits up to 5 minutes for it, and the guard refuses while check.lock is held. A lock left
//   by a dead process is never removed automatically (#258 r3).
import { closeSync, linkSync, mkdirSync, openSync, readFileSync, readdirSync, renameSync, rmSync, statSync, writeSync } from 'node:fs';
import { join } from 'node:path';
import { stateDir } from './collab-trust.mjs';

export const logDir = () => join(stateDir, 'logs');
export const keepLogs = 30;
export const staleGuardMs = 30 * 60000;
export const checkLockPath = () => join(stateDir, 'check.lock');
export const guardLockPath = () => join(stateDir, 'test-guard.lock');
export const guardWaitMs = 5 * 60000;

const alive = pid => { if (!Number.isInteger(pid) || pid <= 0) return false; try { process.kill(pid, 0); return true; } catch { return false; } };
export function lockHolder(path) {
  try { const pid = Number(readFileSync(path, 'utf8')); return alive(pid) ? pid : null; } catch { return null; }
}

// The steps of the `check` script, in order: `pnpm a && pnpm b` -> ['a', 'b'].
export function checkSteps(script = '') {
  return String(script).split('&&').map(part => /^\s*pnpm\s+(?:run\s+)?(\S+)/.exec(part)?.[1]).filter(Boolean);
}
// pnpm prints `> pkg@version step /path` before each script; the last header seen is the step that
// was running when the chain stopped. Without headers the step is unknown.
export function failedStep(output = '', steps = []) {
  let last = null;
  for (const line of String(output).split('\n')) {
    const match = /^> \S+ (\S+)(\s|$)/.exec(line.trim());
    if (match && steps.includes(match[1])) last = match[1];
  }
  return last;
}

// The public receipt carries no log content at all (#258 r3): only the step and the log file name.
// The full log stays on the owner's Mac (0600).
export function failDetails({ output = '', steps = [], logPath = null }) {
  const step = failedStep(output, steps);
  const name = logPath ? String(logPath).split('/').pop() : null;
  return [`Bước lỗi: ${step ? `\`pnpm ${step}\`` : 'không xác định'}.${name ? ` Log đầy đủ chỉ trên máy owner: \`logs/${name}\`.` : ''}`];
}

export const logName = (pr, sha) => `check-${Number(pr)}-${String(sha).slice(0, 12)}.log`;
// Keep the newest `keep` check logs; older ones are removed.
export function rotateLogs(dir = logDir(), keep = keepLogs) {
  let files = [];
  try { files = readdirSync(dir).filter(name => /^check-\d+-[0-9a-f]{12}\.log$/.test(name)); } catch { return []; }
  const sorted = files.map(name => ({ name, at: statSync(join(dir, name)).mtimeMs })).sort((a, b) => b.at - a.at || b.name.localeCompare(a.name));
  const removed = sorted.slice(keep).map(({ name }) => name);
  for (const name of removed) rmSync(join(dir, name), { force: true });
  return removed;
}
// A temp file that receives the check's stdout and stderr; keep() moves it to its final name.
export function openCheckLog(pr, sha, dir = logDir()) {
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  const temp = join(dir, `.running-${process.pid}.log`);
  const fd = openSync(temp, 'w', 0o600);
  const final = join(dir, logName(pr, sha));
  return {
    fd, path: final,
    read() { try { return readFileSync(temp, 'utf8'); } catch { return ''; } },
    close() { try { closeSync(fd); } catch {} },
    keep() { this.close(); renameSync(temp, final); rotateLogs(dir); return final; },
    drop() { this.close(); rmSync(temp, { force: true }); },
  };
}

// What the author check waits for: a live holder, or a dead holder's lock younger than 30 minutes.
// An older dead lock is ignored for this wait only; it is not deleted.
export function guardHolder(path = guardLockPath(), { now = Date.now, staleMs = staleGuardMs } = {}) {
  let pid, at;
  try { pid = Number(readFileSync(path, 'utf8')); at = statSync(path).mtimeMs; } catch { return null; }
  if (alive(pid)) return pid;
  return now() - at > staleMs ? null : (pid || -1);
}

// The author check waits for an agent's guarded tests to finish, at most `limitMs`.
export function waitForGuard({ limitMs = guardWaitMs, holder = () => guardHolder(), sleep = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms), now = Date.now, stepMs = 5000 } = {}) {
  const until = now() + limitMs;
  for (;;) {
    const pid = holder();
    if (!pid) return null;
    if (now() >= until) return pid;
    sleep(Math.min(stepMs, Math.max(1, until - now())));
  }
}

// Guard side: take test-guard.lock only while no author check holds check.lock. The lock is never
// reclaimed automatically (#258 r3): a dead holder's lock makes the guard refuse with its path.
// Returns { status: 'ok', release } | { status: 'check' } | { status: 'held', pid } | { status: 'stale', pid, path }.
export function takeGuardLock({ checkHolder = () => lockHolder(checkLockPath()), path = guardLockPath() } = {}) {
  mkdirSync(stateDir, { recursive: true });
  if (checkHolder()) return { status: 'check' };
  // The PID is written to a private temp file first and linked into place, so the lock never exists
  // empty; link never replaces an existing lock.
  const temp = `${path}.${process.pid}.tmp`;
  const fd = openSync(temp, 'w', 0o600);
  writeSync(fd, String(process.pid)); closeSync(fd);
  try { linkSync(temp, path); } catch {
    const pid = lockHolder(path);
    if (pid) return { status: 'held', pid };
    let old = null; try { old = Number(readFileSync(path, 'utf8')) || null; } catch {}
    return { status: 'stale', pid: old, path };
  } finally { rmSync(temp, { force: true }); }
  // A check that started in the gap between the two looks wins; the guard steps back.
  if (checkHolder()) { rmSync(path, { force: true }); return { status: 'check' }; }
  return { status: 'ok', release: () => { if (lockHolder(path) === process.pid) rmSync(path, { force: true }); } };
}
