// Self-recovering file locks for the unattended loop (check.lock, review.lock, tick.lock).
// Codex on #258/#279: a check-then-delete reclaim lets A see a stale owner, B replace the lock, and
// A delete B's lock, so two runs hold it. The protocol here:
// - Every lock or guard file is published complete: written to a temp file, then linkSync'd into
//   place (atomic, fails when the name exists). A crash never leaves an empty owner file.
// - Each file holds "<pid> <random token>"; the token names one incarnation of the file.
// - Only the holder of `<file>.<token>.gone` (itself such a lock) may unlink incarnation <token>.
//   It re-reads the file under that guard and unlinks only if the token is unchanged; no one else
//   can remove that incarnation meanwhile, so nothing can replace it between the read and unlink.
// - Release uses the same guard; when the guard cannot be taken, release deletes nothing.
// - A guard left by a crashed holder (dead or unknown PID, older than 60 s) is recovered the same
//   way, one level deeper, so a crash at any step does not block the lock forever.
import { randomBytes } from 'node:crypto';
import { linkSync, readFileSync, statSync, unlinkSync, writeFileSync } from 'node:fs';

export const mutexStaleMs = 60000;
export const pidAlive = pid => { try { process.kill(pid, 0); return true; } catch (error) { return error?.code === 'EPERM'; } };
const sleep = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
const newToken = () => `${process.pid} ${randomBytes(8).toString('hex')}`;
const unlink = path => { try { unlinkSync(path); } catch {} };

// Reads "<pid> <token>"; pid is null for a legacy or unknown owner.
export function readOwner(path) {
  let text, mtimeMs;
  try { text = readFileSync(path, 'utf8'); mtimeMs = statSync(path).mtimeMs; } catch { return null; }
  const [first, token] = text.trim().split(/\s+/);
  const pid = Number(first);
  return { text, mtimeMs, pid: Number.isInteger(pid) && pid > 0 ? pid : null, token: token || `legacy-${mtimeMs}` };
}

// Atomic create with full content; false when the name is taken.
export function publish(path, text) {
  const temp = `${path}.tmp-${process.pid}-${randomBytes(4).toString('hex')}`;
  writeFileSync(temp, text);
  try { linkSync(temp, path); return true; }
  catch (error) { if (error?.code === 'EEXIST') return false; throw error; }
  finally { unlink(temp); }
}

const guardStale = ({ alive, nowMs }) => o => (o.pid === null || !alive(o.pid)) && nowMs() - o.mtimeMs > mutexStaleMs;

// Unlinks incarnation `token` of `path` while holding its guard; returns false when the guard is
// held by a live run (then nothing is deleted).
function removeIncarnation(path, token, ctx, depth = 0) {
  const guard = `${path}.${token.replace(/[^\w-]/g, '_')}.gone`;
  const mine = claim(guard, { ...ctx, stale: guardStale(ctx) }, depth + 1);
  if (!mine) return false;
  try {
    ctx.pause('guarded');
    if (readOwner(path)?.token === token) unlink(path);
    return true;
  } finally { unlink(guard); }
}

function claim(path, ctx, depth = 0) {
  if (depth > 8) return null;
  const until = ctx.nowMs() + ctx.waitMs;
  for (;;) {
    const text = newToken();
    if (publish(path, text)) return text;
    const held = readOwner(path);
    if (held) {
      ctx.pause(depth ? 'guard-read' : 'read');
      if (ctx.stale(held)) { removeIncarnation(path, held.token, ctx, depth); if (publish(path, text)) return text; }
    }
    if (ctx.nowMs() >= until) return null;
    sleep(10);
  }
}

// Returns a release function when the lock was taken, or null while a live run holds it.
// Stale: the owner PID is dead, or the lock is older than `staleMs`. `pause(step)` is a test hook.
export function acquireLock(path, { staleMs, alive = pidAlive, nowMs = Date.now, pause = () => {}, waitMs = 0 } = {}) {
  const ctx = { alive, nowMs, pause, waitMs };
  const stale = o => (o.pid !== null && !alive(o.pid)) || nowMs() - o.mtimeMs > staleMs;
  const text = claim(path, { ...ctx, stale });
  if (!text) return null;
  const token = text.split(' ')[1];
  let held = true;
  return () => { if (held) { held = false; removeIncarnation(path, token, { ...ctx, waitMs: 2000 }); } };
}

// Runs fn while holding the lock; returns `busy` (without calling fn) when the lock is held.
export function withFileLock(path, { busy, ...options }, fn) {
  const release = acquireLock(path, options);
  if (!release) return busy;
  try { return fn(); } finally { release(); }
}
