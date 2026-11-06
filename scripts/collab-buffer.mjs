// Ready buffer (owner 05.11.2026, fix A). Queuing practice: a column that keeps running empty
// signals an upstream deficit (kanbantool), so the loop keeps a few PRs ready instead of topping
// up only when the machine is already idle. The target 5 is a local starting value, to be measured:
// a Little's-law sizing was tried and refuted, so the number is tuned from the flow metric below.
import { join } from 'node:path';
import { integration, isOwnPr, readJson, stateDir, vnNow, writeJson } from './collab-trust.mjs';

export const bufferTarget = 5;
export const maxTopUpPerRun = 3;
// Ticks run every 10 minutes; a longer gap (Mac asleep) counts at most this many minutes.
export const maxSampleMinutes = 15;

const labelled = (pr, name) => (pr.labels ?? []).some(l => (l.name ?? l) === name);

export function readyBuffer(prs = []) {
  return prs.filter(pr => isOwnPr(pr) && pr.baseRefName === integration && /^agent\//.test(pr.headRefName ?? '')
    && !pr.isDraft && !labelled(pr, 'needs-owner')).length;
}

export function queueTopUp(buffer) {
  const topUpCount = Math.min(maxTopUpPerRun, Math.max(0, bufferTarget - buffer));
  return { topUp: topUpCount > 0, topUpCount, buffer };
}

export const flowPath = (date, dir = join(stateDir, 'beats')) => join(dir, `flow-${date}.json`);

// Minutes a day with zero actionable PRs: the time since the previous sample counts as empty
// when that sample saw none (it held until now).
export function recordFlow(actionable, { dir, nowMs = Date.now() } = {}) {
  const date = vnNow(new Date(nowMs)).date;
  const path = flowPath(date, dir);
  const day = readJson(path, { date, emptyMinutes: 0, samples: 0 });
  if (day.lastAt && day.lastActionable === 0) {
    day.emptyMinutes += Math.max(0, Math.min(maxSampleMinutes, Math.round((nowMs - day.lastAt) / 60000)));
  }
  const next = { ...day, samples: day.samples + 1, lastAt: nowMs, lastActionable: actionable };
  writeJson(path, next);
  return next;
}

export const renderFlow = day => `Hàng chờ trống hôm nay: ${day?.emptyMinutes ?? 0} phút (không có PR nào để máy làm).`;

// The one call collab-turn makes for --status and --report: buffer, top-up and today's flow metric.
// `actionable` counts PRs the machine can work on now (check, review, merge).
const machine = new Set(['claude-check', 'codex-review', 'merge']);
export function bufferStatus(prs, turns = [], options = {}) {
  const queue = queueTopUp(readyBuffer(prs));
  const day = recordFlow(turns.filter(t => machine.has(t.turn)).length, options);
  return { queue, day, lines: [`PR sẵn sàng: ${queue.buffer}/${bufferTarget}${queue.topUp ? `, cần thêm ${queue.topUpCount}` : ''}.`, renderFlow(day)] };
}
