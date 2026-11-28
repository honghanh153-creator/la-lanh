// One host writer for shared loop state (three-agent dispatch, 28.11.2026, part C).
// - Every change to a shared state file (day file codexRuns and plan lists, queue, claims) goes
//   through applyOnce: one host lock, a check that the writer still holds the coordinator lease
//   epoch (fencing), and an idempotency key kept inside the same file. The change and its key land
//   in one atomic rename, so a restart or a retry of the same step never counts it twice.
// - Backpressure: at most 3 tasks in progress, 2 waiting for review, 2 heavy jobs (R10) on the host.
//   A full queue opens nothing new; work already started continues.
import { join } from 'node:path';
import { readJson, stateDir, writeJson } from './collab-trust.mjs';
import { withFileLock } from './collab-lock.mjs';
import { leasePath } from './collab-agents.mjs';
import { heavySlots } from './collab-heavy-slots.mjs';

export const writerLockPath = () => join(stateDir, 'state', 'writer.lock');
export const opsKeep = 500;
export const hostLimits = { inProgress: 3, inReview: 2, heavy: heavySlots };

// Returns { status: 'applied' | 'duplicate' | 'fenced' | 'busy', value }.
// `epoch`: when given, the write happens only while the coordinator lease still has that epoch.
export function applyOnce(path, key, mutate, { epoch = null, lease = leasePath(), lock = writerLockPath(), nowMs = Date.now(), waitMs = 10000 } = {}) {
  if (!key) throw new Error('applyOnce needs an idempotency key');
  return withFileLock(lock, { staleMs: 60000, waitMs, busy: { status: 'busy' } }, () => {
    if (epoch !== null) {
      const current = readJson(lease, null);
      if (!current || current.epoch !== epoch || current.released) return { status: 'fenced', value: null };
    }
    const before = readJson(path, {});
    const ops = before._ops ?? {};
    if (ops[key]) return { status: 'duplicate', value: before };
    const next = mutate(before);
    const kept = Object.entries({ ...ops, [key]: nowMs }).sort((a, b) => a[1] - b[1]).slice(-opsKeep);
    const value = { ...next, _ops: Object.fromEntries(kept) };
    writeJson(path, value);
    return { status: 'applied', value };
  });
}

// How many new tasks the host may open now. `counts`: { inProgress, inReview, heavy }.
export function admit(counts = {}, limits = hostLimits) {
  const inProgress = counts.inProgress ?? 0;
  const inReview = counts.inReview ?? 0;
  const heavy = counts.heavy ?? 0;
  const reasons = [];
  if (inProgress >= limits.inProgress) reasons.push(`đang làm ${inProgress}/${limits.inProgress}`);
  if (inReview >= limits.inReview) reasons.push(`chờ review ${inReview}/${limits.inReview}`);
  const room = reasons.length ? 0 : limits.inProgress - inProgress;
  return { room, heavyRoom: Math.max(0, limits.heavy - heavy), reasons };
}
