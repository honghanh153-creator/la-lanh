// Whose turn is it on each open PR? `--report` replaces the registry PRs; `--tick` is the launchd safety net.
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { agentMarker, areaOrder, copyBatchAt, classifyArea, clean, codexDailyCap, dayCap, dayStatePath, integration, isOwnPr, makeGh, readJson, repo, reviewState, sortByPriority, stateDir, trustedComments, vnNow, writeJson, isSha } from './collab-trust.mjs';
import { autoStartAt, committedTurns, lastStartAt, makePlan, planIssue, readPlanStatus } from './collab-plan.mjs';
import { dayList, label7w, min7w, pickPlan, planCap, plannedEntry, quotaIssues, unitKey, workUnits } from './collab-quota.mjs';
import { auditReserve } from './collab-audit.mjs';
import { ownerNotes } from './collab-status.mjs';
import { bodyHash } from './collab-heal.mjs';
import { claimsByPr, mayTouch, pruneClaims } from './collab-pr-claim.mjs';
import { plannedWork, workRef } from './collab-work.mjs';
import { gateValue, preflightFailure, readPreflight, recordPreflight, userSees } from './collab-preflight.mjs';
import { syncStatusLabels } from './collab-labels.mjs';
import { deletionProblem, sizeProblem, withRepeatNote } from './collab-size.mjs';
import { withFileLock } from './collab-lock.mjs';
import { bufferStatus, dailyLaneLabel, queueTopUp, wipCount } from './collab-buffer.mjs';
import { afterDecision, disputeView, settleDisputes } from './collab-disagree.mjs';
import { isMain } from './is-main.mjs';
import { secondReviewProblem } from './codex-fallback.mjs';
import { activeReservation, followHead, releaseReservation, reserve } from './collab-reservation.mjs';
import { cleanRelease, probeView } from './collab-merge-probe.mjs';

export { codexDailyCap };
// L25: the launchd tick passes no settle, so this default is the production caller.
export const defaultSettle = settleDisputes;

export const prFiles = pr => (pr.files ?? []).map(f => f.path ?? f).filter(Boolean);

// Fix B (04.11.2026): one open PR per file. Two PRs on the same file conflicted after the first
// merge and cost a fix round each time; the later one waits for the earlier one to land.
// The repo keeps no list of generated or lock files, so every file counts.
// Fix-forward (04.11): only a blocker that can move counts. A PR on hold itself (fork/outside,
// draft, needs-owner, dropped from today's plan, stacked) would hold the other for days (#199 behind #127).
// "Earlier" means earlier in the owner's group order, then creation: a later group never holds an
// earlier one, otherwise the group gate and the file gate wait on each other forever.
const canMove = (o, dropped) => isOwnPr(o) && !o.isDraft && o.baseRefName === integration
  && !(o.labels ?? []).some(l => (l.name ?? l) === 'needs-owner') && !dropped.includes(o.number);

// Fix-forward #575 (16.11.2026): a PR whose own turn is claude-fix (conflict, failed check,
// REQUEST_CHANGES at head, preflight) or hold cannot merge soon, so it never holds another PR on a
// shared file; the one that merges later syncs. On 16.11 #505 and #503 waited behind #404 (open
// findings since 10.11) and #491 (red check) on copy_registry.json. Its turn is read without the
// file gate (open: []), so two PRs never wait on each other's turn.
const waitsOnClaude = (o, opts) => ['claude-fix', 'hold'].includes(prTurn(o, { ...opts, open: [] }).turn);
// R7 (owner 16.11, code 21.11): on a shared file the lane order decides first (incident →
// 7-week plan or persona fix → Daily → the rest), the old area order only breaks ties. The tick
// works lanes in the same order (laneWork), so the lane gate and the file gate never wait on each
// other. Was: area first, which let any content PR hold a 7-week-plan PR of a later area.
// Review of 16.11 (item 2): #505 (safety) waited 43.5 h behind an ordinary PR on a shared file. Inside
// one group an incident goes first, then 7-week plan and persona-threshold fixes (`persona-fix`), then
// the rest.
export const personaFixLabel = 'persona-fix';
const has = (p, name) => (p.labels ?? []).some(l => (l.name ?? l) === name);
// Trial 18–19.11: Daily-lane PRs rank after the 7-week plan and before the rest (owner 17.11).
export const fileRank = p => (has(p, 'incident') ? 3 : has(p, label7w) || has(p, personaFixLabel) ? 2 : has(p, dailyLaneLabel) ? 1 : 0);
const fileOrder = prs => sortByPriority(prs).sort((a, b) => fileRank(b) - fileRank(a) || areaOrder.indexOf(classifyArea(a)) - areaOrder.indexOf(classifyArea(b)));

export function fileBlocker(pr, prs = [], { dropped = [], probes, ...opts } = {}) {
  const mine = new Set(prFiles(pr));
  if (!mine.size) return null;
  const sharing = prs.filter(o => o.number !== pr.number && canMove(o, dropped) && prFiles(o).some(f => mine.has(f)));
  if (!sharing.length) return null;
  // L63: an earlier PR whose trial merge with this exact head was clean, on the copy registry only,
  // does not hold it (collab-merge-probe.mjs cleanRelease). The trial log is read only when needed.
  const view = probes ?? probeView();
  const shared = sharing.filter(o => !cleanRelease(pr, o, view));
  if (!shared.length) return null;
  // L53 (19.11.2026): a PR that is ready to merge (Author check PASS on the live tip and APPROVE at
  // its head) is never held by another PR on a shared file: it merges first and the other syncs.
  // #729 (L04, due 20.11) was approved at 16:06 and waited all evening behind #753, which had not
  // passed its check yet. Its own turn is read without the file gate (open: []).
  if (prTurn(pr, { dropped, ...opts, open: [] }).turn === 'merge') return null;
  const order = fileOrder([pr, ...shared]);
  return order.slice(0, order.indexOf(pr)).find(o => !waitsOnClaude(o, { dropped, ...opts }))?.number ?? null;
}

// L25: the dispute state is read by default, so the review command (codex-review.mjs) routes the
// same way as the tick and the merge gate (Codex 15.11: a caller without it refused after a decision).
export function prTurn(pr, { dropped = [], open = [], preflight = {}, baseFiles, disputes = disputeView(), probes } = {}) {
  const head = pr.headRefOid;
  const out = (turn, reason, extra = {}) => ({ number: pr.number, title: pr.title, area: classifyArea(pr), head, base: pr.baseRefName, tip: isSha(pr.baseTipOid) ? pr.baseTipOid : null, turn, reason, files: prFiles(pr), bodyHash: bodyHash(pr.body),
    source: gateValue(pr.body, 'G1') || null, userSees: userSees(pr.body), item: workRef(pr.body), ...extra });
  const labels = (pr.labels ?? []).map(l => l.name ?? l);
  if (!isOwnPr(pr)) return out('hold', 'PR không phải của owner hoặc từ fork: không chạy, không review');
  if (pr.baseRefName === 'main') return out('hold', 'base là main: chỉ owner');
  if (pr.isDraft) return out('hold', 'draft');
  if (labels.includes('needs-owner')) return out('hold', 'needs-owner');
  // L68: held during Codex fallback; the tick removes the label when Claude is back.
  if (labels.includes('cho-claude')) return out('hold', 'chờ Claude quay lại (chế độ chuyển sang Codex)');
  const deletion = deletionProblem(pr);
  if (deletion) return out('hold', deletion);
  // L25: an open dispute holds the PR; after a decision only a newer check and review count.
  if (disputes[pr.number]?.hold) return out('hold', disputes[pr.number].hold);
  if (dropped.includes(pr.number)) return out('hold', 'owner bỏ khỏi plan hôm nay');
  if (pr.baseRefName !== integration) return out('hold', `xếp chồng trên ${pr.baseRefName}`);
  const blocker = fileBlocker(pr, open, { dropped, preflight, baseFiles, disputes, probes });
  if (blocker) return out('hold', `chờ PR #${blocker} cùng file`);
  // A conflict needs Claude at any stage: on 02.11 an approved PR in conflict kept every tick on a
  // refused merge for three hours, and checking or reviewing a head that cannot merge wastes the run (K24).
  if (pr.mergeable === 'CONFLICTING') return out('claude-fix', 'xung đột với collab/integration');
  // P1-A: the check must be for the live base; a base move sends the PR back to claude-check.
  // L25: after a dispute decision only a newer check and review count.
  const state = reviewState(afterDecision(pr, disputes[pr.number]), { baseFiles });
  const check = state.check;
  const last = state.last?.verdict;
  const pre = check ? null : preflightFailure(preflight, pr);
  if (pre) return out('claude-fix', `preflight: ${clean(pre.join('; '), 200)}`);
  if (!check) return out('claude-check', 'chưa có Author check có biên nhận @ head trên base hiện tại');
  // #254: preflight runs only before a check, so a PR checked before the size cap would reach
  // review or merge without it. The cap is applied here too, before review and merge routing.
  const size = sizeProblem(pr);
  if (size) return out('claude-fix', `preflight: ${clean(size, 200)}`);
  // #508: `cause` routes the CI recheck; the reason text may gain a repeat note (collab-size).
  if (check.status === 'FAIL') return out('claude-fix', 'Author check FAIL @ head', { cause: 'author-fail' });
  if (!last || last.sha !== head) return out('codex-review', last ? `verdict cuối cho ${last.sha.slice(0, 7)}` : 'chưa có verdict');
  if (last.verdict === 'REQUEST_CHANGES') return out('claude-fix', 'REQUEST_CHANGES @ head');
  if (state.stale) return out('codex-review', `review lại: ${clean(state.stale, 200)}`);
  // L69: a PR Codex fixed needs a second critic that is not Codex before it merges.
  const second = secondReviewProblem(pr);
  if (second) return out(second.turn, second.reason);
  return out('merge', 'APPROVE @ head');
}

// The day's list (collab-quota.mjs). A failed label read leaves the quota unknown and says so; the
// machine then picks as before, never as if there were no 7-week items.
export function planList({ gh, turns, prs, comments, date, issues = () => quotaIssues(gh) }) {
  try {
    return dayList({ units: workUnits({ turns, prs, issues: issues() }), comments, date });
  } catch (error) {
    const units = workUnits({ turns, prs, issues: [] });
    return { source: 'machine', unknown: true, note: `Chưa xác định được chỗ cho kế hoạch 7 tuần (${clean(error.message, 120)}); máy chọn theo thứ tự cũ.`, ...pickPlan(units, { need: 0 }) };
  }
}
// Selections are recorded by stable key (item:N or pr:N), so execution follows an item to whatever
// PR does it later, and a re-pick keeps entries that already finished (Codex r1 on #544).
export function recordList(list, carried = []) {
  const all = [...(list.incidents ?? []), ...list.items];
  const entries = [...carried.map(c => c.entry), ...all.map(plannedEntry)];
  const keys7w = [...carried.filter(c => c.entry.plan7w).map(c => c.key), ...list.items.filter(u => u.plan7w).map(u => u.key)];
  return {
    planned: all.flatMap(u => u.prs), plannedItems: entries, plannedKeys: [...carried.map(c => c.key), ...list.items.map(u => u.key)],
    planned7wKeys: keys7w, incidentKeys: (list.incidents ?? []).map(u => u.key), planSource: list.source, planNote: list.note,
    quota7w: list.unknown ? null : { want: list.want, picked: keys7w.length, available: list.available7w },
  };
}
const entryKey = e => (e.item ? `item:${e.item}` : `pr:${e.pr}`);
// The day's dropped work, as keys: `Bỏ #N` names a PR or an item; a PR dropped by number also
// drops the item it works on.
// The day's drops, kept in the day state, so an item stays dropped after its PR closes; held
// turns for dropped work never reach the active area, a queue or a re-pick (Codex r3 on #544).
// Codex r4 on #544: drops become PR numbers before turnsFor, so prTurn holds them and fileBlocker
// lets work behind them move, at every call (tick, re-pick, queue refresh, --status).
export function dropSet(plan, prs, dayPath = null, day = {}) {
  const d = dayPath ? readJson(dayPath, day) : day;
  const dropped = plan?.dropped ?? [];
  const keys = new Set([...(d.droppedKeys ?? []), ...dropped.flatMap(n => [`pr:${n}`, `item:${n}`])]);
  for (const p of prs ?? []) if (dropped.includes(p.number)) { const item = workRef(p.body); keys.add(item ? `item:${item}` : `pr:${p.number}`); }
  if (dayPath && keys.size !== (d.droppedKeys ?? []).length) writeJson(dayPath, { ...d, droppedKeys: [...keys].sort() });
  const numbers = (prs ?? []).filter(p => keys.has(`pr:${p.number}`) || (workRef(p.body) && keys.has(`item:${workRef(p.body)}`))).map(p => p.number);
  return { keys, prs: [...new Set([...dropped, ...numbers])] };
}
export function dayDrops(plan, turns, dayPath, day) {
  const d = readJson(dayPath, day);
  const keys = new Set([...(d.droppedKeys ?? []), ...droppedKeysOf(plan, turns)]);
  if (keys.size !== (d.droppedKeys ?? []).length) writeJson(dayPath, { ...d, droppedKeys: [...keys].sort() });
  return keys;
}
export const applyDrops = (turns, keys) => turns.map(t => (t.turn !== 'hold' && keys.has(unitKey(t)) ? { ...t, turn: 'hold', reason: 'owner bỏ việc này khỏi plan hôm nay' } : t));
export function droppedKeysOf(plan, turns) {
  const dropped = plan?.dropped ?? [];
  const keys = new Set(dropped.flatMap(n => [`pr:${n}`, `item:${n}`]));
  for (const t of turns) if (dropped.includes(t.number)) keys.add(unitKey(t));
  return keys;
}

// Replacement after `Bỏ #N` (a PR or an item number): dropped selections leave; the rest stay,
// finished ones included; pickPlan fills the freed seats (7-week first while short). The note is
// saved before posting and retried until it is delivered.
export function replan({ gh, plan, dayPath, day, date, issues = () => quotaIssues(gh) }) {
  let d = readJson(dayPath, day);
  if (d.replanNote) {
    gh.comment('issue', planIssue(gh), d.replanNote);
    writeJson(dayPath, { ...readJson(dayPath, d), replanNote: null });
    return { delivered: true };
  }
  if (!Array.isArray(d.plannedKeys)) return null;
  const prs = gh.openPrs();
  // Codex r2–r4 on #544: every drop of the day (by PR or item number) stays dropped, for selection
  // and execution alike, also after the dropped PR closes.
  const drops = dropSet(plan, prs, dayPath, d);
  d = readJson(dayPath, d);
  const all = drops.keys;
  const turns = applyDrops(turnsFor(prs, { dropped: drops.prs, baseFiles: gh.compareFiles }), all);
  const droppedKeys = d.plannedKeys.filter(k => all.has(k));
  const dropKey = droppedKeys.sort().join(',');
  if (!dropKey || d.replannedFor === dropKey) return null;
  const units = workUnits({ turns, prs, issues: issues() }).filter(u => !all.has(u.key));
  const keep = d.plannedKeys.filter(k => !all.has(k));
  // Every kept selection keeps its original entry and class; only replacements are classified
  // now (Codex r2/r3 on #544).
  const original = k => (d.plannedItems ?? []).find(e => entryKey(e) === k) ?? { [k.split(':')[0]]: Number(k.split(':')[1]), plan7w: (d.planned7wKeys ?? []).includes(k) };
  const carried = keep.map(k => ({ key: k, entry: original(k) }));
  const carried7w = carried.filter(c => c.entry.plan7w).length;
  const list = { source: 'replan', note: `Chọn bù sau khi bỏ ${droppedKeys.map(k => `#${k.split(':')[1]}`).join(', ')}.`,
    // Only the dropped seats are refilled: the day keeps its original size (Codex r2 on #544).
    ...pickPlan(units.filter(u => !keep.includes(u.key)), { cap: Math.min(planCap, d.plannedKeys.length) - carried.length, need: Math.max(0, min7w - carried7w) }) };
  const added = list.items.filter(u => !d.plannedKeys.includes(u.key));
  const lines = added.map(u => `- ${u.prs.length ? u.prs.map(n => `#${n}`).join(', ') : `việc #${u.item} (chưa có PR)`} ${clean(u.title, 80)}${u.plan7w ? ' [Kế hoạch 7 tuần]' : ''}`);
  const base = recordList(list, carried);
  const record = { ...base, planned: turns.filter(t => base.plannedKeys.includes(unitKey(t)) || (base.incidentKeys ?? []).includes(unitKey(t))).map(t => t.number) };
  const note = [`Cập nhật plan ${date}: ${list.note}`, ...(lines.length ? ['Việc thêm vào:', ...lines] : ['Không còn việc sẵn sàng để chọn bù.']),
    `Kế hoạch 7 tuần: ${record.planned7wKeys.length} việc (mục tiêu ${min7w}).`, '', `${agentMarker} replan date=${date} drop=${dropKey} -->`].join('\n');
  writeJson(dayPath, { ...d, ...record, replannedFor: dropKey, planVersion: (d.planVersion ?? 1) + 1, replanNote: note });
  gh.comment('issue', planIssue(gh), note);
  writeJson(dayPath, { ...readJson(dayPath, d), replanNote: null });
  return { added: added.map(u => u.key) };
}

export function turnsFor(prs, options = {}) {
  const preflight = options.preflight ?? readPreflight();
  const disputes = options.disputes ?? disputeView();
  const probes = options.probes ?? probeView();
  return sortByPriority(prs).map(pr => withRepeatNote(prTurn(pr, { ...options, open: prs, preflight, disputes, probes }), pr));
}

// Owner order: finish every content PR before privacy, and privacy before features.
// Held PRs do not block a later group; anything else in an earlier group does.
// The machine works on the earliest group that has machine work (check, review, merge). A PR that
// waits for Claude's fix no longer blocks the machine: on 31.10 one ops PR in claude-fix stalled
// every group for two hours. Claude still fixes in priority order (claude-queue.json).
// Fix E: how many checks one tick may run back to back; the tick lock is treated as crashed after
// 90 minutes, so the drain also stops starting new checks after 60.
export const checksPerTick = 3;
export const drainMinutes = 60;
export const machineTurns = new Set(['claude-check', 'codex-review', 'merge']);
export function activeArea(turns) {
  return areaOrder.find(area => turns.some(t => t.area === area && machineTurns.has(t.turn))) ?? null;
}

// R7 (owner 16.11.2026; #604 counted the lanes but the tick still worked one area at a time
// 21.11.2026): the lanes share the machine in the order incident/safety → 7-week plan → Daily →
// process. Every PR that is not an incident, a 7-week item or Daily is in the process lane, whatever
// its area; the old area order (ops → content → privacy → feature) only sorts inside that lane. On
// 21.11 eight process PRs had waited up to three days without one check, because the single active
// area was always ops or content.
// Each lane gets its 1 + 1: a lane that had machine work and got nothing for laneStarveTicks ticks
// in a row goes first after incidents on the next tick. It then holds the front (sync and
// reservation), so its PR runs check → review → merge. Incidents always go first.
export const laneStarveTicks = 2;
export const laneOrder = ['incident', 'plan7w', 'daily', 'process'];
export function laneWork({ live, prs = [], incidentKeys = new Set(), kept = new Set(), starved = {} }) {
  const byNumber = new Map(prs.map(p => [p.number, p]));
  const labelled = (t, name) => (byNumber.get(t.number)?.labels ?? []).some(l => (l.name ?? l) === name);
  const laneOf = new Map();
  for (const t of live) {
    const key = unitKey(t);
    laneOf.set(t, incidentKeys.has(key) ? 'incident' : kept.has(key) || labelled(t, label7w) || labelled(t, personaFixLabel) ? 'plan7w'
      : labelled(t, dailyLaneLabel) ? 'daily' : 'process');
  }
  const rank = t => areaOrder.indexOf(t.area);
  const lanes = Object.fromEntries(laneOrder.map(l => [l, live.filter(t => laneOf.get(t) === l)]));
  lanes.process = [...lanes.process].sort((a, b) => rank(a) - rank(b));
  const busy = l => lanes[l].some(t => machineTurns.has(t.turn));
  const hungry = laneOrder.slice(1).filter(l => (starved[l] ?? 0) >= laneStarveTicks && busy(l));
  const order = ['incident', ...hungry, ...laneOrder.slice(1).filter(l => !hungry.includes(l))];
  const work = order.flatMap(l => lanes[l]);
  return { work, lane: t => laneOf.get(t) ?? null, lanes, hungry, busy };
}

// After a tick: a lane with machine work counts one more starved tick unless one of its PRs made
// progress: a merge that merged, a review that was posted, a check with a result (PASS or FAIL), or
// the front synced to integration. Codex auto-1 on #843: a stale PR behind the front reads
// `ci-pending` every tick from CI (`waiting` in local mode), and a busy, refused, limited or failed
// call changes nothing; counting those reset the counter each tick, so the lane never went first.
export const progressed = d => d.merge?.status === 'merged' || d.review?.status === 'posted' || ['PASS', 'FAIL', 'synced'].includes(d.check?.status);
export function nextStarved({ starved = {}, lanes, busy, done }) {
  const served = l => done.some(d => lanes[l].some(t => t.number === d.pr) && progressed(d));
  return Object.fromEntries(laneOrder.slice(1).map(l => [l, busy(l) && !served(l) ? (starved[l] ?? 0) + 1 : 0]));
}

// Two reviews a tick at most; when the process lane has one waiting, one of the two is its. Codex
// auto-1 on #843 (P2): the reserved slot never displaces an incident review; it takes the place of
// the last non-incident review in the first slots, and none when both slots are incidents.
export function reviewSlots(list, lane, slots = 2) {
  const i = list.findIndex(t => lane(t) === 'process');
  if (i < slots || list.slice(0, slots).some(t => lane(t) === 'process')) return list;
  const j = list.slice(0, slots).findLastIndex(t => lane(t) !== 'incident');
  if (j < 0) return list;
  return [...list.slice(0, j), list[i], ...list.filter((_, k) => k >= j && k !== i)];
}

// #508 (Codex 14.11): a FAIL read from CI stayed in claude-fix after the job was re-run and
// turned green at the same head, and nothing checked it again. Such a PR gets one new author
// check per (PR, head, run, attempt). A local FAIL, a guard hit or an older green run stays.
export function ciFailAtHead(pr) {
  const last = trustedComments(pr.comments).filter(c => c.check?.sha === pr.headRefOid).at(-1);
  if (last?.check.status !== 'FAIL') return null;
  const rows = String(last.body ?? '').normalize('NFC').split(/\r?\n/).map(l => l.trim());
  if (!rows.some(l => l.startsWith('Nguồn: CI')) || rows.some(l => l.includes('Chặn: dữ liệu riêng tư'))) return null;
  return last;
}
export const recheckKey = (number, head, ci) => `${number}@${head}#${ci.runId}.${ci.attempt}`;
// A preflight FAIL spends the key only for that PR body, so a body-only fix is checked again.
const bodyKey = (key, hash) => `${key}|body:${hash}`;
const prevDate = date => new Date(Date.parse(`${date}T00:00:00Z`) - 86400000).toISOString().slice(0, 10);
// Keys live in the day state; yesterday's file is read too, so midnight does not reset them.
export const recheckedKeys = date => new Set([prevDate(date), date].flatMap(d => readJson(dayStatePath(d), {}).rechecked ?? []));

export function ciRechecks(turns, prs, { ci, seen = new Set(), log = () => {} } = {}) {
  if (!ci) return turns;
  return turns.map(t => {
    const pr = t.turn === 'claude-fix' && t.cause === 'author-fail' ? prs.find(p => p.number === t.number) : null;
    const fail = pr ? ciFailAtHead(pr) : null;
    if (!fail) return t;
    let run;
    try { run = ci(t.head); } catch (error) { log(`ci recheck #${t.number}: ${clean(error.message, 200)}`); return t; }
    const green = run?.state === 'PASS' && run.conclusion === 'success' && Date.parse(run.completedAt) > Date.parse(fail.createdAt);
    const key = green ? recheckKey(t.number, t.head, run) : null;
    if (!key || seen.has(key) || seen.has(bodyKey(key, t.bodyHash))) return t;
    return { ...t, turn: 'claude-check', reason: 'CI chạy lại xanh ở cùng head: check lại (#508)', recheck: key };
  });
}

export function renderReport(turns) {
  const rows = turns.map(t => `#${t.number}\t${t.area}\t${t.turn}\t${t.head?.slice(0, 7)}\t${clean(t.reason, 80)}\t${clean(t.title, 80)}`);
  return ['PR\tnhóm\tlượt\thead\tlý do\ttiêu đề', ...rows].join('\n');
}

// One tick at a time; a lock whose PID is dead or older than 90 minutes belongs to a crashed run.
// The reclaim runs under the reclaim mutex (collab-lock.mjs, Codex #258).
function withLock(fn) {
  mkdirSync(stateDir, { recursive: true });
  return withFileLock(join(stateDir, 'tick.lock'), { staleMs: 90 * 60000, busy: { status: 'locked' } }, fn);
}

export const idleAlertRuns = 6;

// A failed daily copy batch is retried on later ticks, at most this many attempts a day.
export const copyBatchAttempts = 3;
export const stuckAlertRuns = 3;

export const autopilotSession = 'autopilot';

// Owner 16.11 (two lanes): today's picked 7-week items' PRs belong to the 7-week lane even before
// their PR carries the plan label.
export const plan7wPrNumbers = (turns, date) => { const keys = new Set(readJson(dayStatePath(date), {}).planned7wKeys ?? []); return turns.filter(t => keys.has(unitKey(t))).map(t => t.number); };

const defaultReservations = {
  active: nowMs => activeReservation(nowMs),
  reserve: (pr, head, options) => reserve(pr, head, options),
  follow: (pr, head, options) => followHead(pr, head, options),
  release: (pr, why) => releaseReservation(pr, why),
};

export function tick({ gh = makeGh(), now, clock, preflight: tools = () => [], prPreflight: preflight = () => ({ status: 'PASS' }), heavyFree = () => true, nowMs = Date.now, check = () => ({ status: 'skipped' }), review, merge, alert, board = () => {}, log = () => {}, watchdog = () => {}, health = () => [], copyPending = () => 0, copyBatch = null, copySaved = () => false, notify = () => {}, metrics = () => null, audit = null, incidents = null, ciStatus = null, settle = defaultSettle, mergeAudit = null, reservations = defaultReservations, fallback = null, critic = null } = {}) {
  // The clock is read again before each action, so a long review cannot push the next one past lastStartAt.
  const time = clock ?? (now ? () => now : () => vnNow());
  now = time();
  return withLock(() => {
    const dayPath = dayStatePath(now.date);
    const day = readJson(dayPath, { codexRuns: 0, failures: 0 });
    // Fix-forward #622: every tick takes the next number, whatever path it leaves by, so the quiet red
    // streak counts only back-to-back ticks. Kept apart from the day state, which must stay absent
    // until the plan writes it.
    const seqPath = join(stateDir, 'tick-seq.json');
    const seqNow = readJson(seqPath, {});
    const seq = (seqNow.date === now.date ? seqNow.seq ?? 0 : 0) + 1;
    writeJson(seqPath, { date: now.date, seq });
    const heartbeat = status => writeJson(join(stateDir, 'heartbeat.json'), { at: new Date().toISOString(), vn: now, status });
    // The phone-visible board must never break a tick.
    // Outcome numbers (collab-metrics.mjs) are read once per tick, never at night.
    let metricLines = null;
    const measure = (prs, turns) => { try { metricLines = metrics({ prs, turns }); } catch (error) { log(`metrics failed: ${clean(error.message, 200)}`); } };
    // Health (watchdog, pre-push hook) is read once per tick and shown on every board update, not
    // only in the morning plan: a hook removed at noon shows on the next tick (Codex r1 on #482).
    let healthNow;
    const readHealth = () => { if (healthNow === undefined) { try { healthNow = health(); } catch { healthNow = []; } } return healthNow; };
    // L19: open incidents are read from GitHub once per tick and shown on every board update.
    let openIncidents;
    const readIncidents = () => { if (openIncidents === undefined) { try { openIncidents = incidents ? incidents() : []; } catch { openIncidents = null; } } return openIncidents; };
    const show = info => {
      const counts = readJson(dayPath, day);
      try { board({ now: time(), codexRuns: counts.codexRuns ?? 0, cap: dayCap(counts), failures: counts.failures ?? 0, metrics: metricLines, health: readHealth(), incidents: readIncidents(), ...info }); } catch {}
    };
    // Owner notes (collab-status.mjs): a new comment only for merges, a 2-tick failure streak and a
    // new needs-owner (no slot digest since 16.11.2026: one report per slot). Never breaks a tick.
    const tell = ({ turns = [], comments = [] } = {}) => {
      try {
        const d = readJson(dayPath, day);
        const notes = ownerNotes({ now: time(), merged: d.mergedToday ?? [], failures: d.failures ?? 0, streakAt: d.streakAt ?? null, turns });
        if (notes.length) notify(notes, comments);
      } catch (error) { log(`owner note failed, retry next run: ${clean(error.message, 200)}`); }
    };
    const streak = (failures, prev) => (failures === 0 ? null : failures === 1 ? `${String(now.hour).padStart(2, '0')}:${String(now.minute).padStart(2, '0')}` : prev ?? null);
    // The scheduled-run watchdog runs before the plan gate, so it also watches at night; it never breaks a tick.
    try { watchdog(); } catch {}
    // Night audit (L21b): 23:00–23:29 provisional, before 10:00 final for yesterday. It runs before
    // the plan gate so a held or closed plan does not skip it, and it never breaks a tick.
    if (audit) {
      try { const result = audit(); if (result && !['idle', 'done'].includes(result.status)) log(`night audit: ${JSON.stringify(result)}`); }
      catch (error) { log(`night audit failed: ${clean(error.message, 200)}`); }
    }
    // L25: owner replies, the 30-minute clock and the morning resend for disputes; never breaks a tick.
    try { settle({ gh, log }); } catch (error) { log(`disputes failed: ${clean(error.message, 200)}`); }
    try {
      // Missing tools fail inside the handler, so the heartbeat, the counter and the alert still work.
      const missing = tools();
      if (missing.length) throw new Error(`thiếu công cụ trên PATH: ${missing.join(', ')}`);
      // L26 (cách 2-nhẹ): the post-merge audit (collab-merge-audit.mjs, at most once an hour) runs
      // before the plan gate, so it also runs while the plan is closed or not made. It checks
      // consistency only, not that Codex reviewed independently. It never breaks a tick.
      if (mergeAudit) {
        try {
          const audit = mergeAudit({ gh, now: new Date(nowMs()) });
          if (audit?.status === 'error') log(`merge audit stopped, retry next run: ${clean(audit.error, 200)}`);
        } catch (error) { log(`merge audit failed, retry next run: ${clean(error.message, 200)}`); }
      }
      let plan = readPlanStatus(gh, now);
      if (plan.state === 'not-made') {
        const prs = gh.openPrs();
        const turns = turnsFor(prs, { baseFiles: gh.compareFiles });
        measure(prs, turns);
        // Progress is items done / items picked (owner 12.11.2026): remember what was picked.
        // L11: the items picked are recorded now, so a PR body edited later cannot change the count.
        // Owner 15.11: one list a day, with at least 2 seats kept for the 7-week plan (collab-quota.mjs).
        const list = planList({ gh, turns, prs, comments: plan.comments, date: now.date });
        writeJson(dayPath, { ...readJson(dayPath, day), ...recordList(list) });
        makePlan(gh, now, turns, { codexLeft: Math.max(0, dayCap(day) - day.codexRuns), cap: dayCap(day), gap: tickGap(readJson(join(stateDir, 'heartbeat.json'), null)), health: readHealth(), list });
        heartbeat('plan-made');
        show({ status: 'plan-made', turns });
        return { status: 'plan-made' };
      }
      // Owner `Bỏ #N` on a picked item: pick a replacement with the same rules, once per drop set.
      if (plan.state !== 'closed') { try { replan({ gh, plan, dayPath, day, date: now.date }); } catch (error) { log(`replan failed, retry next run: ${clean(error.message, 200)}`); } }
      if (plan.state !== 'open') {
        heartbeat(plan.state);
        if (plan.state === 'closed') { show({ status: plan.state, turns: [] }); return { status: plan.state }; }
        const prs = gh.openPrs();
        const drops = dropSet(plan, prs, dayPath, day);
        const turns = applyDrops(turnsFor(prs, { dropped: drops.prs, baseFiles: gh.compareFiles }), drops.keys);
        measure(prs, turns);
        show({ status: plan.state, turns });
        tell({ turns, comments: plan.comments });
        return { status: plan.state };
      }
      // Every tick works when the plan is open (retro D1, 31.10.2026): the locks keep heavy jobs
      // serial and the state on GitHub keeps work from repeating, so an hourly gate only cost time.
      const prs = gh.openPrs();
      // One session per PR (owner 16.11): a claim goes only once GitHub confirms its PR is closed or
      // merged (Codex r1 on #597: absence from this list is not proof).
      try { const gone = pruneClaims(prs.map(p => p.number), { closed: n => ['CLOSED', 'MERGED'].includes(gh.pr(n)?.state) }); if (gone.length) log(`claims dropped for closed PRs: ${gone.join(', ')}`); }
      catch (error) { log(`claim prune failed: ${clean(error.message, 200)}`); }
      const drops = dropSet(plan, prs, dayPath, day);
      const gone = drops.keys;
      const turns = applyDrops(ciRechecks(turnsFor(prs, { dropped: drops.prs, baseFiles: gh.compareFiles }), prs, { ci: ciStatus, seen: recheckedKeys(now.date), log }), gone);
      // Labels follow the final turns, after a green CI re-run may have moved a PR to claude-check.
      try { if (gh.raw) syncStatusLabels(gh, prs, turns); } catch (error) { log(`status labels: ${String(error.message ?? error).slice(0, 200)}`); }
      // #253: the scheduled tick samples the flow metric and owns the buffer top-up, so the
      // persisted queue and --status agree and the metric does not depend on report reads.
      const { queue: startBuffer } = bufferStatus(prs, turns, { plan7wPrs: plan7wPrNumbers(turns, now.date) });
      measure(prs, turns);
      let area = activeArea(turns);
      // Owner 15.11: the kept 7-week items are worked first, or the seats are empty words. Since 21.11 (R7) the
      // rest follows by lane (laneWork), not by one active area.
      // Codex r1 on #544: by stable key, so a PR opened later for a picked item counts; serious
      // incidents first, then the kept 7-week items, then the active area.
      const dayNow = readJson(dayPath, day);
      // Codex r5 on #544: a serious incident opened after the plan also goes first; the day's
      // selections and drops stay as they are. A failed read keeps the planned incidents only.
      let liveIncidents = [];
      try { liveIncidents = workUnits({ turns, prs, issues: quotaIssues(gh) }).filter(u => u.ready && u.incident).map(u => u.key); }
      catch (error) { log(`incident refresh failed, planned incidents only: ${clean(error.message, 200)}`); }
      const incidentKeys = new Set([...(dayNow.incidentKeys ?? []), ...liveIncidents]);
      const kept = new Set(dayNow.planned7wKeys ?? []);
      // A dropped item is not worked, even through another PR that names it (Codex r2 on #544).
      const live = turns.filter(t => !gone.has(unitKey(t)));
      // R7 lanes (21.11): incidents, kept 7-week items, Daily, then every other PR in the process lane.
      const lanePlan = laneWork({ live, prs, incidentKeys, kept, starved: dayNow.laneStarved ?? {} });
      if (lanePlan.hungry.length) log(`lane first after ${laneStarveTicks} ticks without work: ${lanePlan.hungry.join(', ')}`);
      let work = lanePlan.work;
      area = work.find(t => machineTurns.has(t.turn))?.area ?? area;
      const done = [];
      const late = () => { const t = time(); return t.hour * 60 + t.minute >= lastStartAt; };
      // Codex r1 on #899 (P1): the second critic's step runs before merges are chosen. Its answer for a
      // PR is read and posted while that PR is still open, and a PR whose critique is under way is held
      // by the merge gate (criticPending), so a ready PR is never merged past its critic.
      if (critic && !late()) {
        try { const r = critic({ turns: live, prs }); if (r) log(`critic: ${JSON.stringify(r)}`); }
        catch (error) { log(`critic failed: ${clean(error.message, 200)}`); }
      }
      // 17.11.2026 (#633): a PR ready to merge is merged whatever its area. Merging costs no Codex run
      // or heavy job, while waiting lets another area's merge move integration and void its check and
      // review (#633 waited 45 minutes behind content work, then needed a new check and review).
      // Checks and reviews keep the area order; the merge gate still checks every PR.
      // Incident 18.11.2026 (Codex run 23, P1 on #736): the front reserves integration before it is
      // synced, and collab-merge refuses every other PR while the reservation stands, so a full CI run
      // is not voided by fast merges. The holder is validated before the merges are chosen: while it
      // stands, only the holder may be merged, from any area; a holder that left the queue or was
      // pushed to by someone else is released first.
      const waitingTurns = ['claude-check', 'codex-review', 'merge'];
      let held = reservations.active(nowMs());
      if (held) {
        const t = live.find(x => x.number === held.pr);
        const why = !t ? 'không còn trong hàng' : !waitingTurns.includes(t.turn) ? `rời hàng (${t.turn})`
          : t.head && t.head !== held.head ? 'head đổi ngoài tick' : null;
        if (why) { reservations.release(held.pr, why); log(`reservation #${held.pr} released: ${why}`); held = null; }
        else work = [t, ...work.filter(x => x !== t)];
      }
      const merges = [...work, ...live.filter(t => !work.includes(t))].filter(t => t.turn === 'merge' && (!held || t.number === held.pr)).slice(0, 2);
      for (const t of merges) {
        if (late()) break;
        show({ status: 'running', doing: `merge #${t.number}`, expectMinutes: 5, area, turns, done });
        const result = merge(t.number);
        done.push({ pr: t.number, merge: result });
        if (result?.status === 'merged') {
          const d = readJson(dayPath, day);
          writeJson(dayPath, { ...d, mergedToday: [...(d.mergedToday ?? []).filter(m => m.number !== t.number), { number: t.number, title: t.title }] });
        }
      }
      // Author checks need no AI: the tick runs them in the dedicated clone, one at a time, then reviews.
      // Fix A: a fast preflight first; a failure is recorded (nothing posted) and costs no check slot.
      // Fix E (04.11.2026): while the heavy-job lock is free and another PR is ready, the tick starts
      // it at once instead of waiting 10 minutes for the next run. Checks stay strictly serial here,
      // and the check lock still refuses a second heavy job from anywhere else.
      const checked = [];
      // L14 (retro 12.11 S25): only the PR at the front of the area queue is merged with
      // integration before its check. Every waiting PR used to be re-synced whenever integration
      // moved (22 re-syncs on 12.11, #441 five times, 7 PRs never checked). The front is read after
      // this tick's merges (Codex 14.11), so a PR merged a moment ago never holds the place. A PR
      // that cannot merge cleanly goes to claude-fix: conflicts are Claude's to resolve.
      const mergedNow = new Set(done.filter(d => d.merge?.status === 'merged').map(d => d.pr));
      // Fix-forward #739: the tip in the turns was read before this tick's merges; a reservation (and the
      // head the holder gets from its sync) records the live tip, so its expiry is bound to the base it
      // really had. Unknown when the read fails (then a spent window is refused, as before).
      const liveTip = n => { try { const tip = gh.pr(n)?.baseTipOid; return isSha(tip) ? tip : null; } catch { return null; } };
      // #524 (Codex r1 on #495): the front is the first PR the machine can act on; a held or
      // claude-fix PR ahead of it (needs-owner, conflict) no longer keeps it from syncing.
      // One session per PR (owner 16.11): a PR a session holds is never synced by the machine; its
      // session merges integration in. It may still get an author check of the head it pushed.
      // The holder merged in this tick (runMerge released it): integration is free for a new front.
      if (held && mergedNow.has(held.pr)) { reservations.release(held.pr, 'đã merge'); held = null; }
      let front = held && live.find(x => x.number === held.pr && ['claude-check', 'codex-review'].includes(x.turn) && mayTouch(x.number).ok)?.number || null;
      // No new reservation from lastStartAt (23:35): nothing new starts, so nothing should wait.
      if (!held && now.hour * 60 + now.minute < lastStartAt) {
        for (const t of work.filter(x => ['claude-check', 'codex-review'].includes(x.turn) && !mergedNow.has(x.number) && mayTouch(x.number).ok)) {
          const r = reservations.reserve(t.number, t.head, { nowMs: nowMs(), tip: mergedNow.size ? liveTip(t.number) : t.tip });
          if (r.refused) { log(`reservation #${t.number} refused: ${r.refused}`); continue; }
          if (r.reservation?.pr === t.number) { front = t.number; log(`reservation #${t.number} until ${new Date(r.reservation.expiresAtMs).toISOString()}`); }
          break;
        }
      }
      const startedMs = nowMs();
      let checks = 0;
      // #508: a recheck is spent only by a receipt or a preflight result on an unchanged head (a
      // preflight result only for that body); busy, pending, refused or a throw leaves the key unset.
      const markRechecked = (t, status) => {
        if (!t.recheck || !['PASS', 'FAIL', 'preflight'].includes(status)) return;
        let head = null;
        try { head = gh.pr(t.number).headRefOid; } catch (error) { log(`recheck head #${t.number}: ${clean(error.message, 200)}`); }
        if (head !== t.head) return;
        const key = status === 'preflight' ? bodyKey(t.recheck, t.bodyHash) : t.recheck;
        const d = readJson(dayPath, day);
        writeJson(dayPath, { ...d, rechecked: [...new Set([...(d.rechecked ?? []), key])] });
      };
      for (const t of work.filter(t => t.turn === 'claude-check')) {
        if (late() || checks >= checksPerTick || nowMs() - startedMs > drainMinutes * 60000) break;
        const pre = preflight(t.number);
        if (pre?.status === 'FAIL') { recordPreflight(t.number, t.head, { ...pre, bodyHash: pre.bodyHash ?? t.bodyHash }); done.push({ pr: t.number, preflight: pre }); markRechecked(t, 'preflight'); continue; }
        if (checks > 0 && !heavyFree()) break;
        show({ status: 'running', doing: `author check #${t.number} (thường 10–35 phút)`, expectMinutes: 90, area, turns, done });
        const result = check(t.number, { auto: true, clock: time, sync: t.number === front });
        if (t.number === front && result?.status === 'synced' && result.head) reservations.follow(t.number, result.head, { nowMs: nowMs(), tip: liveTip(t.number) });
        checks += 1;
        done.push({ pr: t.number, check: result });
        markRechecked(t, result?.status);
        if (result?.status === 'preflight') { recordPreflight(t.number, t.head, { status: 'FAIL', reasons: result.reasons ?? [], bodyHash: result.bodyHash ?? t.bodyHash }); checks -= 1; continue; }
        if (result?.status === 'PASS') checked.push(t);
        // ci-pending: this head's CI is still running; the next PR may already have its result.
        // synced: the front got a new head (CI runs on it); the PRs behind it still read their CI.
        // waiting: a PR behind the front is behind integration too; it is synced on its own turn.
        if (!['PASS', 'FAIL', 'ci-pending', 'synced', 'waiting'].includes(result?.status)) break;
      }
      for (const t of reviewSlots([...checked, ...work.filter(t => t.turn === 'codex-review')], lanePlan.lane)) {
        const fresh = readJson(dayPath, day);
        if (done.filter(d => d.review).length >= 2 || fresh.codexRuns >= dayCap(fresh) - auditReserve || late()) break;
        show({ status: 'running', doing: `Codex review #${t.number}`, expectMinutes: 30, area, turns, done });
        const result = review(t.number, { auto: true, now: time() });
        done.push({ pr: t.number, review: result });
        // Usage limit: wait for the reset; busy: a direct review holds the clone. The next run retries.
        if (['limit', 'busy'].includes(result?.status)) break;
      }
      // R7: each lane's starved ticks, kept in the day state for the next tick.
      { const d = readJson(dayPath, day); writeJson(dayPath, { ...d, laneStarved: nextStarved({ starved: d.laneStarved ?? {}, lanes: lanePlan.lanes, busy: lanePlan.busy, done }) }); }
      // Owner 06.11.2026: Codex approves one batch of non-sensitive copy a day. The tick runs it at
      // most once a day, from copyBatchAt (08:00), only while copy outside the owner-only groups is
      // pending, inside the daily Codex cap, and never next to an open batch PR on the same file.
      // A busy review lock starts nothing and is retried on the next run.
      if (copyBatch && !late() && (t => t.hour * 60 + t.minute)(time()) >= copyBatchAt) {
        const today = readJson(dayPath, day);
        // Only our own batch PR into integration counts: a fork branch with the same name must not
        // stop the daily copy review.
        const batchOpen = prs.some(p => isOwnPr(p) && p.baseRefName === integration && /^agent\/claude\/copy-batch-/.test(p.headRefName ?? ''));
        let pending = 0;
        // 13.11: a failed batch used to count as the day's batch, so nothing retried and nobody was
        // told. An error now retries on later ticks, up to copyBatchAttempts a day.
        const retry = today.copyBatch?.status === 'error' && (today.copyBatch.attempts ?? 1) < copyBatchAttempts;
        // Publishing saved decisions calls no Codex, so it may run after the cap is spent (Codex 13.11).
        const budgetOk = (today.codexRuns ?? 0) < dayCap(today) - auditReserve || copySaved();
        if ((!today.copyBatch || retry) && budgetOk && !batchOpen) {
          try { pending = copyPending(); } catch (error) { log(`copy batch: registry unreadable: ${clean(error.message, 200)}`); }
        }
        if (pending > 0) {
          show({ status: 'running', doing: 'Codex duyệt lô câu chữ hằng ngày', expectMinutes: 25, area, turns, done });
          const result = copyBatch();
          done.push({ copy: result });
          if (result?.status !== 'busy') {
            const fresh = readJson(dayPath, day);
            // Only a run that called Codex spends the cap; a retry publishes saved decisions.
            const spent = result?.codex === false || result?.status === 'empty' ? 0 : 1;
            const attempts = (fresh.copyBatch?.status === 'error' ? fresh.copyBatch.attempts ?? 1 : 0) + 1;
            const reason = clean(result?.reason ?? 'không rõ', 300);
            // Each failed attempt queues its own alert; a later success never erases one that
            // has not been delivered yet (Codex 13.11 on #480).
            const copyAlerts = [...(fresh.copyAlerts ?? []), ...(result?.status === 'error'
              ? [`Lô duyệt câu chữ hằng ngày lỗi (lần ${attempts}/${copyBatchAttempts}, ${now.date}): ${reason}. `
                + (attempts >= copyBatchAttempts ? 'Đã hết lượt thử hôm nay, Claude cần sửa nguyên nhân.' : 'Lượt sau thử lại; quyết định Codex đã lưu nên không tốn thêm lượt Codex.')]
              : [])];
            writeJson(dayPath, { ...fresh, codexRuns: (fresh.codexRuns ?? 0) + spent, copyAlerts, copyBatch: {
              status: result?.status ?? 'unknown', at: new Date().toISOString(), attempts,
              ...(result?.reason ? { reason } : {}) } });
          }
        }
      }
      // Every failed attempt reaches the owner's alert thread at once, and a failed delivery is
      // retried on the next tick until it goes through (Codex 13.11).
      for (const text of readJson(dayPath, day).copyAlerts ?? []) {
        if (!alert) break;
        try {
          alert(text);
          const latest = readJson(dayPath, day);
          writeJson(dayPath, { ...latest, copyAlerts: (latest.copyAlerts ?? []).filter(t => t !== text) });
        } catch (error) { log(`copy batch alert failed, retry next run: ${clean(error.message, 200)}`); break; }
      }
      // Retro S1 (K26/K31: 02.11 and 03.11 ran about two hours with no area): count runs in a row
      // with no area; the sixth alerts. A top-up still waits for room under WIP 1 + 1 (owner 12.11).
      const idleRuns = area ? 0 : (readJson(dayPath, day).idleRuns ?? 0) + 1;
      // #237: remember whether the idle alert was delivered, so a failed delivery retries next run.
      const idleAlerted = idleRuns ? Boolean(readJson(dayPath, day).idleAlerted) : false;
      writeJson(dayPath, { ...readJson(dayPath, day), idleRuns, idleAlerted });
      // #158/#159: after merges, checks or reviews the queue and buffer are read again, so the
      // top-up describes what is left now, not the list fetched before this run's work.
      const left = done.length ? gh.openPrs() : prs;
      const leftTurns = done.length ? applyDrops(turnsFor(left, { dropped: dropSet(plan, left, null, readJson(dayPath, day)).prs, baseFiles: gh.compareFiles }), gone) : turns;
      const buffer = done.length ? queueTopUp(wipCount(left, leftTurns, { plan7wPrs: plan7wPrNumbers(leftTurns, now.date) })) : startBuffer;
      writeJson(join(stateDir, 'claude-queue.json'), {
        // One session per PR (owner 16.11): the hourly autopilot (session id `autopilot`) gets only
        // fix items no other session holds; the held ones are listed apart.
        at: new Date().toISOString(), plan: plan.state, area, items: leftTurns.filter(t => t.turn === 'claude-fix' && mayTouch(t.number, autopilotSession).ok),
        claimed: Object.entries(claimsByPr()).map(([n, c]) => ({ pr: Number(n), session: c?.session ?? null, since: c?.at ?? null })),
        // Plan top-up (owner 31.10.2026), WIP 1 + 1 since 12.11: Claude opens the next backlog task
        // only when nothing is in progress and review has room, and never from lastStartAt on.
        topUp: buffer.topUp && !late(),
        topUpCount: late() ? 0 : buffer.topUpCount, buffer: buffer.buffer, inProgress: buffer.inProgress, inReview: buffer.inReview,
        // Two lanes (owner 16.11): where a new task may open, 7-week first, and each lane's counts.
        topUpLanes: late() ? [] : buffer.topUpLanes ?? [], lanes: buffer.lanes ?? null,
        idleRuns,
      });
      // L68: in Codex fallback one claude-fix turn goes to Codex; outside it the hold labels come off.
      if (fallback && !late()) {
        try { const r = fallback({ turns: leftTurns, prs: left, late }); if (r) log(`fallback: ${JSON.stringify(r)}`); }
        catch (error) { log(`fallback failed: ${clean(error.message, 200)}`); }
      }
      if (idleRuns >= idleAlertRuns && !idleAlerted && alert) {
        try {
          alert(`collab tick chạy không ${idleRuns} lượt liền (${now.date} ${now.hour}:${String(now.minute).padStart(2, '0')}): plan không còn PR nào để làm, cần bổ sung việc từ backlog`);
          writeJson(dayPath, { ...readJson(dayPath, day), idleAlerted: true });
        } catch (error) { log(`idle alert failed, retry next run: ${clean(error.message, 200)}`); }
      }
      const errors = done.filter(d => d.review?.status === 'error' || d.merge?.status === 'error' || d.check?.status === 'error' || d.copy?.status === 'error');
      const failures = errors.length ? (readJson(dayPath, day).failures ?? 0) + 1 : 0;
      writeJson(dayPath, { ...readJson(dayPath, day), lastRunHour: now.hour, failures, streakAt: streak(failures, readJson(dayPath, day).streakAt) });
      // An unresolved copy batch error keeps the run red until a batch succeeds; a quiet tick after
      // the last retry must not look healthy (Codex 13.11). It is not counted as a new failure.
      const stuckBatch = readJson(dayPath, day).copyBatch;
      const stuck = stuckBatch?.status === 'error' ? `Lô duyệt câu chữ còn lỗi chưa xử lý (lần ${stuckBatch.attempts ?? 1}/${copyBatchAttempts}): ${clean(stuckBatch.reason ?? 'không rõ', 200)}` : null;
      const red = errors.length || stuck;
      heartbeat(red ? 'ran-with-errors' : 'ran');
      // A review waiting while the daily Codex cap is spent is a budget stop, not "no work" (#145 r2).
      const capped = !done.length && work.some(t => t.turn === 'codex-review') && (readJson(dayPath, day).codexRuns ?? 0) >= dayCap(readJson(dayPath, day)) - auditReserve;
      show({ status: red ? 'ran-with-errors' : done.length ? 'ran' : capped ? 'cap' : 'idle', area, turns, done, error: red ? [errors.length ? JSON.stringify(errors) : null, stuck].filter(Boolean).join(' · ') : null });
      if (failures === 2 && alert) alert(`collab tick có lỗi 2 lần liên tiếp (${now.date} ${now.hour}h): ${clean(JSON.stringify(errors), 300)}`);
      // Review of 16.11: 34 red ticks from 15:43 to 21:41 raised no alert, because a tick red only from the
      // unresolved copy batch is not a new failure. Three such ticks in a row open one ops-alert a day,
      // with the reason; the count resets on a green tick.
      const prevStuck = readJson(dayPath, day);
      const stuckRuns = stuck && !errors.length ? (prevStuck.stuckSeq === seq - 1 ? (prevStuck.stuckRuns ?? 0) + 1 : 1) : 0;
      writeJson(dayPath, { ...readJson(dayPath, day), stuckRuns, stuckSeq: stuckRuns ? seq : null });
      if (stuckRuns >= stuckAlertRuns && !readJson(dayPath, day).stuckAlerted && alert) {
        try {
          alert(`collab tick đỏ ${stuckRuns} lượt liền mà không có lỗi mới (${now.date} ${now.hour}:${String(now.minute).padStart(2, '0')}): ${stuck}`);
          writeJson(dayPath, { ...readJson(dayPath, day), stuckAlerted: true });
        } catch (error) { log(`stuck alert failed, retry next run: ${clean(error.message, 200)}`); }
      }
      tell({ turns: leftTurns, comments: plan.comments });
      log(JSON.stringify(done));
      // 16.11.2026: the tick log printed only "ran-with-errors" for a whole day; the reason a quiet tick is
      // still red (the unresolved copy batch) now rides in the logged result too.
      return { status: red ? 'ran-with-errors' : 'ran', area, done, ...(stuck ? { stuck } : {}) };
    } catch (error) {
      const failures = (readJson(dayPath, day).failures ?? 0) + 1;
      writeJson(dayPath, { ...readJson(dayPath, day), failures, streakAt: streak(failures, readJson(dayPath, day).streakAt) });
      heartbeat(`error: ${clean(error.message, 200)}`);
      show({ status: 'error', error: error.message });
      tell();
      if (failures === 2 && alert) alert(`collab tick lỗi 2 lần liên tiếp (${now.date} ${now.hour}:${String(now.minute).padStart(2, '0')}): ${clean(error.message, 300)}`);
      return { status: 'error', error: clean(error.message, 300) };
    }
  });
}

// Ticks run every 10 minutes; a heartbeat older than 30 minutes means the Mac slept or was off.
export function tickGap(last, nowMs = Date.now()) {
  const at = Date.parse(last?.at ?? '');
  if (!Number.isFinite(at) || nowMs - at < 30 * 60000) return null;
  const hhmm = ms => new Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(ms);
  return { from: hhmm(at), to: hhmm(nowMs) };
}

// #253: --status and --report count the same plan-aware turns as the tick, so a PR dropped from
// today's plan is never sampled as actionable.
export function planTurns(gh, now) {
  const plan = readPlanStatus(gh, now);
  const prs = gh.openPrs();
  const drops = dropSet(plan, prs, null, readJson(dayStatePath((now ?? vnNow()).date), {}));
  return { plan, prs, turns: applyDrops(turnsFor(prs, { dropped: drops.prs, baseFiles: gh.compareFiles }), drops.keys) };
}

// S8 (retro 08.11, K35): one open ops-alert per subject. A repeat becomes a comment on the open
// issue (an older dated title counts too), so the owner closes one thread once it is fixed
// instead of sweeping a new issue per alert. After the owner closes it, the next alert opens a
// fresh one. If the lookup itself fails, the alert is still raised as a new issue.
export const opsAlertTitle = subject => `[ops-alert] ${subject}`;

export function openOpsAlert(issues, subject) {
  const base = opsAlertTitle(subject);
  const same = title => title === base || (title.startsWith(`${base} `) && /^\d{4}-\d{2}-\d{2}$/.test(title.slice(base.length + 1)));
  return (issues ?? []).filter(i => typeof i?.title === 'string' && same(i.title))
    .reduce((newest, i) => (newest === null || i.number > newest ? i.number : newest), null);
}

export function opsAlert(gh, text, subject = 'collab loop', now = vnNow()) {
  const body = `${clean(text, 1000)}\n\nKiểm tra log ở ~/.cache/la-lanh-collab/logs trên máy owner.\n\n<!-- la-lanh-agent ops-alert -->`;
  let open = null;
  try {
    open = openOpsAlert(gh.json(['issue', 'list', '--repo', repo, '--label', 'ops-alert', '--state', 'open',
      '--search', `"${opsAlertTitle(subject)}" in:title`, '--json', 'number,title', '--limit', '50']), subject);
  } catch { open = null; }
  if (open !== null) {
    const at = `${now.date} ${String(now.hour).padStart(2, '0')}:${String(now.minute).padStart(2, '0')}`;
    gh.raw(['issue', 'comment', String(open), '--repo', repo, '--body-file', '-'], `Lặp lại lúc ${at}: ${body}`);
    return { number: open, created: false };
  }
  gh.raw(['label', 'create', 'ops-alert', '--repo', repo, '--color', 'B60205', '--force']);
  gh.raw(['issue', 'create', '--repo', repo, '--title', opsAlertTitle(subject), '--label', 'ops-alert', '--body-file', '-'], body);
  return { number: null, created: true };
}

// S8 part 2: the alert's own cause is gone, so the open issue for that subject is closed with a
// short note. A failed lookup throws, so the caller keeps its marker and retries on the next tick.
export function resolveOpsAlert(gh, text, subject) {
  const open = openOpsAlert(gh.json(['issue', 'list', '--repo', repo, '--label', 'ops-alert', '--state', 'open',
    '--search', `"${opsAlertTitle(subject)}" in:title`, '--json', 'number,title', '--limit', '50']), subject);
  if (open === null) return { number: null, closed: false };
  gh.raw(['issue', 'close', String(open), '--repo', repo, '--comment', `Tự đóng: ${clean(text, 500)}\n\n<!-- la-lanh-agent ops-alert -->`]);
  return { number: open, closed: true };
}

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  try {
    const gh = makeGh();
    if (args.includes('--tick')) {
      // codex-review imports this module, so the tick entry lives in collab-tick.mjs (no import cycle).
      process.stderr.write('Use: node scripts/collab-tick.mjs\n'); process.exitCode = 2;
    } else if (args.includes('--status')) {
      const { plan, prs, turns } = planTurns(gh);
      const { queue: buffer } = bufferStatus(prs, turns, { plan7wPrs: plan7wPrNumbers(turns, vnNow().date) });
      process.stdout.write(`${JSON.stringify({ plan: plan.state, reason: plan.reason, dropped: plan.dropped, queue: { ...readJson(join(stateDir, 'claude-queue.json'), null), ...buffer } })}\n`);
    } else {
      const { prs, turns } = planTurns(gh);
      const { lines } = bufferStatus(prs, turns, { plan7wPrs: plan7wPrNumbers(turns, vnNow().date) });
      process.stdout.write(`${args.includes('--json') ? JSON.stringify(turns, null, 2) : [renderReport(turns), ...lines].join('\n')}\n`);
    }
  } catch (error) { process.stderr.write(`collab-turn failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
}
