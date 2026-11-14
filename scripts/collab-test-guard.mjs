// Agents run tests only through this guard, so no test runs during an author check (05.11.2026).
// Usage: node scripts/collab-test-guard.mjs [--wait-min N] -- <cmd> [args...]
// Waits (default 60 min, checking every minute) until `collab-check.mjs --busy` is free, then holds
// test-guard.lock while the command runs. Refuses (exit 75) while an author check holds check.lock;
// the author check waits up to 5 minutes for this lock before it starts `pnpm check`.
import { spawnSync } from 'node:child_process';
import { machineBusy } from './collab-check.mjs';
import { takeGuardLock } from './collab-check-log.mjs';
import { isMain } from './is-main.mjs';

export const refusedCode = 75;
const pause = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

export function runGuarded(cmd, args, { busy = machineBusy, take = takeGuardLock, spawn = spawnSync, sleep = pause, waitMs = 60 * 60000, stepMs = 60000, now = Date.now, log = text => process.stderr.write(`${text}\n`) } = {}) {
  const until = now() + waitMs;
  for (;;) {
    const lock = take();
    if (lock.status === 'stale') { log(`collab-test-guard: khóa cũ của PID ${lock.pid ?? '?'}; xóa ${lock.path} nếu chắc chắn không còn test nào chạy.`); return refusedCode; }
    if (lock.status === 'check') { log('collab-test-guard: author check đang chạy, không chạy test. Thử lại sau.'); return refusedCode; }
    if (lock.status === 'ok') {
      const other = busy();
      if (!other) {
        try { return spawn(cmd, args, { stdio: 'inherit' }).status ?? 1; } finally { lock.release(); }
      }
      lock.release();
      log(`collab-test-guard: máy bận (${String(other).slice(0, 80)}), chờ.`);
    } else log(`collab-test-guard: test của agent khác đang chạy (pid ${lock.pid ?? '?'}), chờ.`);
    if (now() >= until) { log('collab-test-guard: chờ quá lâu, dừng.'); return refusedCode; }
    sleep(stepMs);
  }
}

if (isMain(import.meta.url)) {
  const argv = process.argv.slice(2);
  const dash = argv.indexOf('--');
  const wait = argv.indexOf('--wait-min');
  if (dash < 0 || dash === argv.length - 1) { process.stderr.write('Usage: node scripts/collab-test-guard.mjs [--wait-min N] -- <cmd> [args...]\n'); process.exit(2); }
  const waitMs = wait >= 0 && wait < dash ? Math.max(0, Number(argv[wait + 1]) || 0) * 60000 : undefined;
  process.exit(runGuarded(argv[dash + 1], argv.slice(dash + 2), waitMs === undefined ? {} : { waitMs }));
}
