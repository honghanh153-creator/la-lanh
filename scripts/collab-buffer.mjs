// Work in progress (owner 12.11.2026). The loop used to keep a ready buffer of five PRs and the
// plan asked for 16–20 PRs a day; the owner found it optimised the PR count instead of what users
// get. Now WIP 1 + 1: at most one Claude task in progress and one in review. A new task opens only
// when nothing is in progress and review has room, so work gets finished before more is started.
import { join } from 'node:path';
import { label7w } from './collab-quota.mjs';
import { integration, isOwnPr, readJson, stateDir, vnNow, writeJson } from './collab-trust.mjs';

// Owner 16.11.2026 (5-fix package item 5, "tại sao ko chạy song song?"): two lanes run in parallel,
// the 7-week plan and the process work, each with its own WIP 1 + 1. Where they share the Codex review
// and merge queue the tick already orders incidents, then 7-week items, then the rest (#544).
export const wipLimit = { inProgress: 1, inReview: 1 };
export const lanes = ['plan7w', 'process'];
// Ticks run every 10 minutes; a longer gap (Mac asleep) counts at most this many minutes.
export const maxSampleMinutes = 15;

const labelled = (pr, name) => (pr.labels ?? []).some(l => (l.name ?? l) === name);
// Open agent PRs into integration. A needs-owner PR waits on the owner, not on Claude.
const agentWork = pr => isOwnPr(pr) && pr.baseRefName === integration && /^agent\//.test(pr.headRefName ?? '') && !labelled(pr, 'needs-owner');

export function readyBuffer(prs = []) {
  return prs.filter(pr => agentWork(pr) && !pr.isDraft).length;
}

const machine = new Set(['claude-check', 'codex-review', 'merge']);

// A PR is in the 7-week lane when it carries the plan label or is one of today's picked 7-week items
// (its PRs, given by the caller); everything else is process work.
// Review of 16.11 (item 5): a fix for a failing persona threshold (`persona-fix`) is plan work for users,
// so it runs in the plan lane too.
export const laneOf = (pr, plan7wPrs = []) => (labelled(pr, label7w) || labelled(pr, 'persona-fix') || plan7wPrs.includes(pr.number) ? 'plan7w' : 'process');

// In review: the machine has the next move (check, review, merge). In progress: everything else
// Claude still owns (a fix, a draft, a PR waiting on another PR's file). The totals stay as before
// (the WIP metric reads them); `lanes` splits them.
export function wipCount(prs = [], turns = [], { plan7wPrs = [] } = {}) {
  const next = new Map(turns.map(t => [t.number, t.turn]));
  const count = list => { const inReview = list.filter(pr => !pr.isDraft && machine.has(next.get(pr.number))).length; return { inProgress: list.length - inReview, inReview }; };
  const work = prs.filter(agentWork);
  return { ...count(work), lanes: Object.fromEntries(lanes.map(lane => [lane, count(work.filter(pr => laneOf(pr, plan7wPrs) === lane))])) };
}

const roomFor = ({ inProgress, inReview }) => inProgress < wipLimit.inProgress && inReview <= wipLimit.inReview;
// Each lane tops up on its own: a new task opens in a lane when nothing of that lane is in progress
// and its review has room, whatever the other lane holds. `topUpLanes` says where (7-week first).
export function queueTopUp(count) {
  const { inProgress, inReview } = count;
  if (!count.lanes) { const topUp = roomFor(count); return { topUp, topUpCount: topUp ? 1 : 0, inProgress, inReview, buffer: inProgress + inReview }; }
  const byLane = Object.fromEntries(lanes.map(lane => { const c = count.lanes[lane] ?? { inProgress: 0, inReview: 0 }; return [lane, { ...c, topUp: roomFor(c) }]; }));
  const topUpLanes = lanes.filter(lane => byLane[lane].topUp);
  return { topUp: topUpLanes.length > 0, topUpCount: topUpLanes.length, topUpLanes, inProgress, inReview, buffer: inProgress + inReview, lanes: byLane };
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
const laneName = { plan7w: 'Làn kế hoạch 7 tuần', process: 'Làn quy trình' };
export function bufferStatus(prs, turns = [], options = {}) {
  const queue = queueTopUp(wipCount(prs, turns, { plan7wPrs: options.plan7wPrs ?? [] }));
  const day = recordFlow(turns.filter(t => machine.has(t.turn)).length, options);
  const laneLines = lanes.map(lane => { const c = queue.lanes[lane]; return `${laneName[lane]}: đang làm ${c.inProgress}/${wipLimit.inProgress}, chờ review ${c.inReview}/${wipLimit.inReview}; ${c.topUp ? 'có thể mở 1 việc mới' : 'chưa mở việc mới'}.`; });
  return { queue, day, lines: [...laneLines, renderFlow(day)] };
}
