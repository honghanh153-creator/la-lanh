// Work in progress (owner 12.11.2026). The loop used to keep a ready buffer of five PRs and the
// plan asked for 16–20 PRs a day; the owner found it optimised the PR count instead of what users
// get. Now WIP 1 + 1: at most one Claude task in progress and one in review. A new task opens only
// when nothing is in progress and review has room, so work gets finished before more is started.
import { join } from 'node:path';
import { integration, isOwnPr, readJson, stateDir, vnNow, writeJson } from './collab-trust.mjs';

export const wipLimit = { inProgress: 1, inReview: 1 };
// Ticks run every 10 minutes; a longer gap (Mac asleep) counts at most this many minutes.
export const maxSampleMinutes = 15;

const labelled = (pr, name) => (pr.labels ?? []).some(l => (l.name ?? l) === name);
// Open agent PRs into integration. A needs-owner PR waits on the owner, not on Claude.
const agentWork = pr => isOwnPr(pr) && pr.baseRefName === integration && /^agent\//.test(pr.headRefName ?? '') && !labelled(pr, 'needs-owner');

export function readyBuffer(prs = []) {
  return prs.filter(pr => agentWork(pr) && !pr.isDraft).length;
}

const machine = new Set(['claude-check', 'codex-review', 'merge']);

// In review: the machine has the next move (check, review, merge). In progress: everything else
// Claude still owns (a fix, a draft, a PR waiting on another PR's file).
export function wipCount(prs = [], turns = []) {
  const next = new Map(turns.map(t => [t.number, t.turn]));
  const work = prs.filter(agentWork);
  const inReview = work.filter(pr => !pr.isDraft && machine.has(next.get(pr.number))).length;
  return { inProgress: work.length - inReview, inReview };
}

export function queueTopUp({ inProgress, inReview }) {
  const topUp = inProgress < wipLimit.inProgress && inReview <= wipLimit.inReview;
  return { topUp, topUpCount: topUp ? 1 : 0, inProgress, inReview, buffer: inProgress + inReview };
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

// The one call collab-turn makes for the tick (#253), --status and --report: WIP, top-up and today's flow metric.
// `actionable` counts PRs the machine can work on now (check, review, merge).
export function bufferStatus(prs, turns = [], options = {}) {
  const queue = queueTopUp(wipCount(prs, turns));
  const day = recordFlow(turns.filter(t => machine.has(t.turn)).length, options);
  return { queue, day, lines: [`Việc đang làm: ${queue.inProgress}/${wipLimit.inProgress}, đang chờ review: ${queue.inReview}/${wipLimit.inReview}; ${queue.topUp ? 'có thể mở 1 việc mới' : 'chưa mở việc mới'}.`, renderFlow(day)] };
}
