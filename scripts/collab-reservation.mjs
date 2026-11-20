// Merge reservation for collab/integration (incident 18.11.2026; Codex critique run 23: no-go on
// reusing a PASS across base drift, go for a reservation).
//
// The incident: an author-check PASS counts only on the live integration tip (P1-A), a full CI run
// takes ~32 minutes, and fast PRs merged every 3–43 minutes. Each merge moved the tip, the front PR
// was synced again and restarted CI, and it and every PR behind it waited from 17.11 evening.
//
// The rule now: the PR the tick syncs as the front reserves integration first. While the
// reservation stands, `collab-merge` (every entry point: the tick, a direct call, a driver) refuses
// any other PR, inside one merge lock, so the reserved PR gets an unbroken window for CI, check,
// review and merge. P1-A is unchanged: its PASS is still on the live tip.
//
// The reservation ends when the reserved PR merges, leaves the queue (fix, hold, closed), its head
// changes for a reason other than the tick's own sync, or after `reservationMinutes`. An expired
// reservation cannot be taken again by the same PR at the same head, so a stuck PR never holds
// integration for long. A person or session can release it with a logged reason:
//   node scripts/collab-reservation.mjs --status
//   node scripts/collab-reservation.mjs --release --reason "<why>"
import { appendFileSync, mkdirSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { clean, isSha, readJson, stateDir } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';
import { withFileLock } from './collab-lock.mjs';

export const reservationMinutes = 90;
export const reservationPath = () => join(stateDir, 'state', 'merge-reservation.json');
export const mergeLockPath = () => join(stateDir, 'merge.lock');
const logPath = () => join(stateDir, 'logs', 'merge-reservation.log');

function write(value) {
  const path = reservationPath();
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.tmp-${process.pid}`;
  writeFileSync(tmp, `${JSON.stringify(value)}\n`);
  renameSync(tmp, path);
}

function log(line) {
  try {
    mkdirSync(dirname(logPath()), { recursive: true });
    appendFileSync(logPath(), `${new Date().toISOString()} ${line}\n`);
  } catch {}
}

const valid = r => r && Number.isInteger(r.pr) && r.pr > 0 && isSha(r.head) && Number.isFinite(r.expiresAtMs);

/** The reservation in force at `nowMs`, or null (none, unreadable, or expired). */
export function activeReservation(nowMs = Date.now()) {
  const r = readJson(reservationPath(), null)?.reservation;
  return valid(r) && nowMs < r.expiresAtMs ? r : null;
}

/**
 * Reserve integration for `pr` at `head`. Returns the reservation that stands afterwards: this
 * one, or another PR's that is still in force. An expired reservation of the same PR at the same
 * head is not renewed (`{ refused }`): it had its window.
 */
function reserveUnlocked(pr, head, { nowMs = Date.now(), minutes = reservationMinutes, tip = null } = {}) {
  if (!Number.isInteger(pr) || pr <= 0 || !isSha(head)) return { refused: 'PR hoặc head không hợp lệ' };
  const stored = readJson(reservationPath(), null) ?? {};
  const current = valid(stored.reservation) ? stored.reservation : null;
  if (current && nowMs < current.expiresAtMs) {
    if (current.pr !== pr) return { reservation: current, other: true };
    if (current.head === head) return { reservation: current };
  }
  const expired = [...(stored.expired ?? []), ...(current && nowMs >= current.expiresAtMs ? [{ pr: current.pr, head: current.head, tip: current.tip ?? null }] : [])].slice(-20);
  // Fix-forward #737: the spent window is bound to the integration tip it had. Once integration has
  // moved (another PR merged), the PR needs a sync and may reserve again; an unknown tip refuses.
  const spent = e => e.pr === pr && e.head === head && (!isSha(tip) || !isSha(e.tip) || e.tip === tip);
  if (expired.some(spent)) {
    if (current && nowMs >= current.expiresAtMs) write({ reservation: null, expired });
    return { refused: `#${pr} đã hết lượt giữ integration ở head ${head.slice(0, 7)}` };
  }
  const reservation = { pr, head, tip: isSha(tip) ? tip : null, reservedAtMs: nowMs, expiresAtMs: nowMs + minutes * 60000 };
  write({ reservation, expired });
  log(`reserve #${pr} @ ${head.slice(0, 7)} until ${new Date(reservation.expiresAtMs).toISOString()}`);
  return { reservation };
}

/** Move the reservation of `pr` to its new head (the tick's own sync gave it a new head). */
function followHeadUnlocked(pr, head, { nowMs = Date.now(), tip = null } = {}) {
  const current = activeReservation(nowMs);
  if (!current || current.pr !== pr || !isSha(head) || (current.head === head && (!isSha(tip) || current.tip === tip))) return current;
  const stored = readJson(reservationPath(), null) ?? {};
  // #739: the sync merged the live tip into the head; the window is bound to that tip.
  const moved = { ...current, head, ...(isSha(tip) ? { tip } : {}) };
  write({ ...stored, reservation: moved });
  return moved;
}

/** End the reservation (of `pr`, or any when `pr` is null). Returns whether one was ended. */
function releaseUnlocked(pr, why, { nowMs = Date.now() } = {}) {
  const stored = readJson(reservationPath(), null) ?? {};
  const current = valid(stored.reservation) ? stored.reservation : null;
  if (!current || (pr !== null && current.pr !== pr)) return false;
  write({ reservation: null, expired: stored.expired ?? [] });
  log(`release #${current.pr}: ${clean(String(why ?? ''), 200)}${nowMs >= current.expiresAtMs ? ' (expired)' : ''}`);
  return true;
}

/** May `pr` merge now? Only the reserved PR while a reservation is in force. */
export function mergeAllowed(pr, nowMs = Date.now()) {
  const current = activeReservation(nowMs);
  if (!current || current.pr === pr) return { ok: true, reservation: current };
  const until = new Date(current.expiresAtMs).toISOString().slice(11, 16);
  return { ok: false, reason: `integration đang giữ cho #${current.pr} (CI, check, review, merge) tới ${until} UTC; PR khác chờ` };
}

// Codex P2 on #736: every reservation change takes the same lock as merge admission, so a merge
// admitted before a reservation finishes before the holder is synced, and none starts inside it.
const busyReserve = { refused: 'một merge khác đang chạy; thử lại ở tick sau' };
export const reserve = (pr, head, { lockWaitMs = 30000, ...options } = {}) =>
  withMergeLock(() => reserveUnlocked(pr, head, options), { busy: busyReserve, waitMs: lockWaitMs });
export const followHead = (pr, head, options = {}) => withMergeLock(() => followHeadUnlocked(pr, head, options), { busy: null });
/** `locked: true` only from inside `withMergeLock` (runMerge), which already holds the lock. */
export function releaseReservation(pr, why, { locked = false, ...options } = {}) {
  return locked ? releaseUnlocked(pr, why, options) : withMergeLock(() => releaseUnlocked(pr, why, options), { busy: false });
}

/** Runs `fn` under the merge lock shared by every merge entry point; `busy` when it is held. */
export function withMergeLock(fn, { busy = { status: 'busy', reason: 'một merge khác đang chạy' }, waitMs = 30000 } = {}) {
  return withFileLock(mergeLockPath(), { busy, staleMs: 10 * 60000, waitMs }, fn);
}

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.includes('--status')) {
    process.stdout.write(`${JSON.stringify(activeReservation())}\n`);
  } else if (args.includes('--release')) {
    const reason = args[args.indexOf('--reason') + 1];
    if (!args.includes('--reason') || !reason || reason.startsWith('--')) {
      process.stderr.write('Usage: node scripts/collab-reservation.mjs --release --reason "<why>"\n'); process.exit(2);
    }
    process.stdout.write(`${JSON.stringify({ released: releaseReservation(null, `manual: ${reason}`) })}\n`);
  } else {
    process.stderr.write('Usage: node scripts/collab-reservation.mjs --status | --release --reason "<why>"\n'); process.exitCode = 2;
  }
}
// Exposed for tests only.
export const _resetReservation = () => { try { rmSync(reservationPath(), { force: true }); } catch {} };
