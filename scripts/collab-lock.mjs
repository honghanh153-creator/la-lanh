// Self-recovering file locks for the unattended loop (check.lock, review.lock, tick.lock).
// Codex on PR #258: a check-then-delete reclaim lets A see a dead PID, B replace the lock, and A
// delete B's lock, so two runs hold it. Here every create, reclaim and release of a lock happens
// under a separate reclaim mutex (`<lock>.reclaim`, taken with O_EXCL), so between "read owner →
// verify stale → unlink → create" no other process can create or release the same lock.
// A lock holds only the owner PID (other readers parse it with Number()); release removes the
// lock only while it still holds this process's PID, under the same mutex.
// A lock is stale when its PID is dead, or when it is older than `staleMs` (a hung or legacy run).
// A mutex older than 60 s whose owner is dead belongs to a crashed acquirer and is removed once.
import { randomBytes } from 'node:crypto';
import { closeSync, openSync, readFileSync, rmSync, statSync, writeSync } from 'node:fs';

export const mutexStaleMs = 60000;
export const pidAlive = pid => { try { process.kill(pid, 0); return true; } catch (error) { return error?.code === 'EPERM'; } };
const ownerPid = text => { const pid = Number(String(text).trim().split(/\s+/)[0]); return Number.isInteger(pid) && pid > 0 ? pid : null; };
const sleep = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
const read = path => { try { return { text: readFileSync(path, 'utf8'), mtimeMs: statSync(path).mtimeMs }; } catch { return null; } };

function createExclusive(path, text) {
  let fd;
  try { fd = openSync(path, 'wx'); } catch (error) { if (error?.code === 'EEXIST') return false; throw error; }
  try { writeSync(fd, text); } finally { closeSync(fd); }
  return true;
}

// Takes the reclaim mutex, retrying briefly; returns its token or null.
function takeMutex(path, { alive, nowMs, pause, waitMs }) {
  const mutex = `${path}.reclaim`;
  const token = `${process.pid} ${randomBytes(8).toString('hex')}`;
  const until = nowMs() + waitMs;
  let removedStale = false;
  for (;;) {
    if (createExclusive(mutex, token)) return token;
    const held = read(mutex);
    if (!removedStale && held && nowMs() - held.mtimeMs > mutexStaleMs && ownerPid(held.text) !== null && !alive(ownerPid(held.text))) {
      pause('mutex-stale');
      const again = read(mutex);
      if (again && again.text === held.text) rmSync(mutex, { force: true });
      removedStale = true;
      continue;
    }
    if (nowMs() >= until) return null;
    sleep(10);
  }
}
function dropMutex(path, token) {
  const mutex = `${path}.reclaim`;
  const held = read(mutex);
  if (held && held.text === token) rmSync(mutex, { force: true });
}

// Returns a release function when the lock was taken, or null when another live run holds it.
// `pause(step)` is a test hook called between the steps of a reclaim.
export function acquireLock(path, { staleMs, alive = pidAlive, nowMs = Date.now, pause = () => {}, waitMs = 2000 } = {}) {
  const mutex = takeMutex(path, { alive, nowMs, pause, waitMs });
  if (!mutex) return null;
  const token = String(process.pid);
  let taken = false;
  try {
    pause('mutex-held');
    if (!createExclusive(path, token)) {
      const held = read(path);
      const pid = held && ownerPid(held.text);
      const stale = held && ((pid !== null && !alive(pid)) || nowMs() - held.mtimeMs > staleMs);
      pause('verified');
      if (held && !stale) return null;
      rmSync(path, { force: true });
      pause('unlinked');
      if (!createExclusive(path, token)) return null;
    }
    taken = true;
  } finally { dropMutex(path, mutex); }
  return () => {
    if (!taken) return;
    taken = false;
    const m = takeMutex(path, { alive, nowMs, pause: () => {}, waitMs });
    try { const held = read(path); if (held && held.text === token) rmSync(path, { force: true }); }
    finally { if (m) dropMutex(path, m); }
  };
}

// Runs fn while holding the lock; returns `busy` (without calling fn) when the lock is held.
export function withFileLock(path, { busy, ...options }, fn) {
  const release = acquireLock(path, options);
  if (!release) return busy;
  try { return fn(); } finally { release(); }
}
