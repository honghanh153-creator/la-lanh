// Disagreement log for the 3+3 day workflow experiment (docs/operations/workflow-experiment-2026-11.md).
// Arm 1 (Claude's way, 14–16.11): Claude records each disagreement with Codex itself. The nightly
// audit reads this file and checks it against the PR comments, so an unrecorded disagreement shows
// up as a gap (metric M8). Arm 2 replaces Claude's own entry with a record made by the program.
//
// L25 (owner 14.11, §0 of that document): at most two rounds; if Claude and Codex still disagree the
// disputed step is held and the owner is asked once. In the day window an unanswered question
// follows Codex's conclusion after 30 minutes ("chốt do hết giờ"); outside it the question waits for
// the morning, is asked again and only then the 30 minutes count. Owner-only items never time out.
// Rounds, questions and outcomes are kept verbatim in disputes.jsonl (a sibling file: the audit
// counts every line of disagreements.jsonl as one disagreement); each decision is also mirrored
// there as one entry, so M8 counts it once.
// Usage: node scripts/collab-disagree.mjs --add (--pr N | --task ID) --claude "…" --codex "…" --winner codex|claude|owner [--note "…"]
//        node scripts/collab-disagree.mjs --override --of <at of the entry> --winner owner|claude|codex --note "…"   (owner reverses later)
//        node scripts/collab-disagree.mjs --list [--date YYYY-MM-DD]
//        node scripts/collab-disagree.mjs --open (--pr N | --task ID [--issue N]) --round 1|2 [--id D] --claude "…"|--claude-file F
//             --codex "…"|--codex-file F [--codex-conclusion "…"] [--owner-only] [--group privacy|consent|crisis|safety|…]
//        node scripts/collab-disagree.mjs --escalate --id D      (after round 2 still disagrees: one question to the owner)
//        node scripts/collab-disagree.mjs --withdraw --id D --note "…"   (the dispute became moot, e.g. agreed on a new head)
//        node scripts/collab-disagree.mjs --settle | --status
import { execFileSync } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { agentMarker, clean, isAutoReview, isSha, isTrusted, makeGh, parseVerdict, repo, stateDir, vnNow } from './collab-trust.mjs';
import { withFileLock } from './collab-lock.mjs';
import { isMain } from './is-main.mjs';

export const logPath = join(stateDir, 'disagreements.jsonl');
export const disputePath = join(stateDir, 'disputes.jsonl');
export const winners = ['codex', 'claude', 'owner'];

// Positions are kept verbatim (Codex 14.11: a 600-character cut broke "nguyên văn"). A text this
// long is refused rather than silently cut.
export const maxText = 50000;
const verbatim = (text, what) => {
  const s = String(text ?? '');
  if (s.length > maxText) throw new Error(`${what} is longer than ${maxText} characters; nothing is cut, shorten it or point to a file`);
  return s;
};

// Codex 13.11: a disagreement can come before any PR exists (a plan), so a task id is accepted too.
function refOf({ pr, task }) {
  const n = Number(pr);
  const ref = pr !== undefined && pr !== null ? (Number.isInteger(n) && n > 0 ? { pr: n } : null) : (/^[A-Za-z][\w.-]{0,40}$/.test(task ?? '') ? { task } : null);
  if (!ref) throw new Error('--pr must be a PR number, or --task an id such as L21');
  return ref;
}

export function entry({ pr, task, claude, codex, winner, note = '', at = new Date(), date = vnNow(at).date }) {
  const ref = refOf({ pr, task });
  if (!String(claude ?? '').trim() || !String(codex ?? '').trim()) throw new Error('both positions are required');
  if (!winners.includes(winner)) throw new Error(`--winner must be one of ${winners.join(', ')}`);
  return { at: at.toISOString(), date, ...ref, claude: verbatim(claude, 'claude'), codex: verbatim(codex, 'codex'), winner, ...(note ? { note: clean(note, 300) } : {}) };
}

// The owner reversing a decision later is its own record, so the original line is never edited.
export function override({ of, winner, note, at = new Date() }) {
  if (!/^\d{4}-\d{2}-\d{2}T/.test(of ?? '')) throw new Error('--of must be the at of the original entry');
  if (!winners.includes(winner)) throw new Error(`--winner must be one of ${winners.join(', ')}`);
  if (!String(note ?? '').trim()) throw new Error('--note is required for an override');
  return { at: at.toISOString(), date: vnNow(at).date, type: 'override', of, winner, note: clean(note, 300) };
}

export function append(e, path = logPath) {
  mkdirSync(dirname(path), { recursive: true });
  appendFileSync(path, `${JSON.stringify(e)}\n`);
  return e;
}

export function read(path = logPath) {
  if (!existsSync(path)) return [];
  return readFileSync(path, 'utf8').split('\n').filter(Boolean).map(line => { try { return JSON.parse(line); } catch { return null; } }).filter(Boolean);
}

// ---- L25: disputes that reach the owner ----

// "Ban ngày" is the owner's word; 08:00–22:00 Vietnam time is our reading of it, an implementation
// choice and not the owner's words (the loop starts PRs at 08:00, PR #514).
export const dayStartMinute = 8 * 60;
export const dayEndMinute = 22 * 60;
export const replyMinutes = 30;
const vnOffsetMs = 7 * 3600000; // Asia/Ho_Chi_Minh has no daylight saving time
const dayMs = 86400000;
const sinceMidnight = ms => (((ms + vnOffsetMs) % dayMs) + dayMs) % dayMs;
// The 30 minutes fit only when they start and end inside the day window.
export const clockFits = ms => { const m = Math.floor(sinceMidnight(ms) / 60000); return m >= dayStartMinute && m + replyMinutes <= dayEndMinute; };
export function nextMorning(ms) {
  const morning = ms - sinceMidnight(ms) + dayStartMinute * 60000;
  return morning > ms ? morning : morning + dayMs;
}

// Owner-only items never time out (§0: "việc chỉ owner quyết vẫn chờ owner"), e.g. L05 and copy in
// these groups.
export const ownerOnlyTasks = ['L05'];
export const ownerOnlyGroups = ['privacy', 'consent', 'crisis', 'safety'];

const iso = ms => new Date(ms).toISOString();
const timeOf = value => Date.parse(value ?? '');
const record = (path, nowMs, e) => append({ at: iso(nowMs), ...e }, path);
const targetOf = d => (d.pr ? { kind: 'pr', number: d.pr } : d.issue ? { kind: 'issue', number: d.issue } : null);
const targetKey = t => (t ? `${t.kind}:${t.number}` : null);

// Replays the event log into one state per dispute, plus the needs-owner label events per target.
export function disputeStates(events = []) {
  const map = new Map();
  const labels = new Map();
  for (const e of events) {
    if (!e?.id) continue;
    if (e.type === 'round') {
      const d = map.get(e.id) ?? { id: e.id, ...(e.pr ? { pr: e.pr } : { task: e.task }), issue: null, ownerOnly: false, rounds: [], questions: [], requested: null, stale: null, decided: null, withdrawn: null, closed: false };
      if (e.issue) d.issue = e.issue;
      d.ownerOnly ||= Boolean(e.ownerOnly);
      d.rounds.push(e);
      map.set(e.id, d);
      continue;
    }
    if (e.type === 'label-added' || e.type === 'label-removed') labels.set(e.target, e);
    const d = map.get(e.id);
    if (!d) continue;
    if (e.type === 'escalate') d.requested = e;
    // rounds: how many rounds existed when the question was posted; the question is about that one.
    else if (e.type === 'sent') { d.questions.push({ ...e, rounds: e.rounds ?? d.rounds.length, notifiedAt: null, clockFrom: null, morningAt: null }); d.requested = null; d.stale = null; }
    else if (e.type === 'notified') { const q = d.questions.find(x => x.q === e.q); if (q) Object.assign(q, { notifiedAt: e.at, clockFrom: e.clockFrom ?? null, morningAt: e.morningAt ?? null }); }
    else if (e.type === 'stale') d.stale = e;
    else if (e.type === 'decided') d.decided = e;
    else if (e.type === 'withdrawn') d.withdrawn = e;
    else if (e.type === 'closed') d.closed = true;
  }
  return { map, labels };
}
export const disputes = (events = read(disputePath)) => disputeStates(events).map;

export function disputeStatus(d) {
  if (d.withdrawn) return 'withdrawn';
  if (d.decided) return 'decided';
  if (!d.rounds.some(r => r.round === 2)) return 'debating';
  if (d.requested) return 'sending';
  if (d.stale) return 'stale';
  if (isSuperseded(d)) return 'superseded';
  return d.questions.length ? 'asked' : 'ready';
}
const isOpenQuestion = d => ['sending', 'asked', 'stale', 'superseded'].includes(disputeStatus(d)) && d.questions.length > 0;
// A new head or a new recorded argument is a substantive change; anything else is the same question.
const questionKey = (head, rounds) => `${head ?? '-'}|${rounds}`;
const lastRound = d => d.rounds.at(-1);
// Codex 15.11: the owner answers the arguments that were sent. A round recorded after the newest
// question supersedes it: no reply and no timeout applies to it until a fresh --escalate, and a
// decision always uses the round that was sent, never a newer one.
const askedRound = (d, q) => d.rounds[q.rounds - 1];
function isSuperseded(d) {
  const q = d.questions.at(-1);
  return Boolean(q) && !(q.rounds === d.rounds.length && askedRound(d, q));
}

export function openRound({ id, pr, task, issue, round, claude, codex, codexConclusion, head, ownerOnly = false, group, nowMs = Date.now(), path = disputePath } = {}) {
  const r = Number(round);
  if (![1, 2].includes(r)) throw new Error('--round must be 1 or 2 (at most two rounds)');
  if (!String(claude ?? '').trim() || !String(codex ?? '').trim()) throw new Error('both positions are required');
  if (id !== undefined && !/^[A-Za-z][\w.-]{0,60}$/.test(id)) throw new Error('--id must look like pr515-1');
  const all = disputes(read(path));
  const d = id ? all.get(id) : null;
  if (r === 2 && !d) throw new Error(id ? `no dispute ${id}; record round 1 first` : 'round 2 needs --id of the dispute');
  if (d && (d.decided || d.withdrawn)) throw new Error(`dispute ${id} is already closed`);
  if (r === 1 && d) throw new Error(`dispute ${id} already has round 1`);
  const ref = d ? (d.pr ? { pr: d.pr } : { task: d.task }) : refOf({ pr, task });
  if (d && pr !== undefined && Number(pr) !== d.pr) throw new Error(`dispute ${id} belongs to ${d.pr ? `PR #${d.pr}` : d.task}`);
  if (ref.pr && !isSha(head)) throw new Error('a PR dispute records the head SHA of each round');
  const n = Number(issue);
  if (issue !== undefined && !(Number.isInteger(n) && n > 0)) throw new Error('--issue must be an issue number');
  const newId = id ?? `${ref.pr ? `pr${ref.pr}` : ref.task}-${[...all.values()].filter(x => (ref.pr ? x.pr === ref.pr : x.task === ref.task)).length + 1}`;
  const only = Boolean(ownerOnly) || ownerOnlyTasks.includes(ref.task) || ownerOnlyGroups.includes(String(group ?? '').toLowerCase());
  return record(path, nowMs, { type: 'round', id: newId, ...ref, ...(ref.pr ? { head } : {}), ...(issue !== undefined ? { issue: n } : {}), round: r,
    claude: verbatim(claude, 'claude'), codex: verbatim(codex, 'codex'), ...(codexConclusion ? { codexConclusion: verbatim(codexConclusion, 'codex conclusion') } : {}),
    ...(only ? { ownerOnly: true } : {}), ...(group ? { group: clean(group, 40) } : {}) });
}

// ---- GitHub side ----

const fold = text => String(text ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/gi, 'd').toLowerCase();
const firstLine = body => String(body ?? '').split(/\r?\n/).map(l => l.trim()).find(Boolean) ?? '';
// "Theo Claude" / "Theo Codex", optionally followed by the dispute id when a PR has two questions open.
export function parseDisputeReply(body) {
  const m = /^theo\s+(claude|codex)\b\s*([a-z][\w.]*-\d+)?/.exec(fold(firstLine(body)));
  return m ? { chosen: m[1], id: m[2] ?? null } : null;
}

const markerRe = /<!-- la-lanh-agent disagree id=(\S+) q=(\d+)(?: r=(\d+))?( label=added)? -->/;
// r is the number of rounds the question shows, so a crash recovery knows which arguments were sent.
export const questionMarker = (id, q, label, rounds) => `${agentMarker} disagree id=${id} q=${q}${rounds ? ` r=${rounds}` : ''}${label ? ' label=added' : ''} -->`;
export const decidedMarker = id => `${agentMarker} disagree-decided id=${id} -->`;
const findQuestion = (comments, id, q) => comments.filter(isTrusted).find(c => { const m = markerRe.exec(c.body ?? ''); return m && m[1] === id && Number(m[2]) === q; });

function readTarget(gh, t) {
  const raw = t.kind === 'pr' ? gh.pr(t.number) : gh.json(['issue', 'view', String(t.number), '--repo', repo, '--json', 'number,state,labels,comments']);
  return { head: raw.headRefOid ?? null, state: raw.state ?? 'OPEN', comments: raw.comments ?? [], labels: (raw.labels ?? []).map(l => l.name ?? l) };
}

const quote = text => clean(text, 500).replace(/<!--/g, '&lt;!--').split('\n').map(l => `> ${l}`).join('\n');
function questionBody(d, q, label, rounds) {
  const last = lastRound(d);
  const where = d.pr ? `PR #${d.pr}` : `việc ${d.task}`;
  return [
    `Claude và Codex chưa thống nhất sau hai vòng ở ${where} (mã ${d.id}${q > 1 ? `, hỏi lần ${q}` : ''}). Bước đang tranh chấp tạm dừng tới khi chốt.`,
    '', '**Ý Claude:**', quote(last.claude), '', '**Ý Codex:**', quote(last.codexConclusion ?? last.codex), '',
    `Bản đầy đủ của hai bên nằm trong sổ bất đồng trên máy owner (~/.cache/la-lanh-collab/disputes.jsonl, mã ${d.id}).`, '',
    'Owner trả lời một dòng: `Theo Claude` hoặc `Theo Codex`.',
    `Nếu chỗ này đang có hơn một câu hỏi, thêm mã ở cuối, ví dụ \`Theo Codex ${d.id}\`.`,
    d.ownerOnly
      ? 'Việc này chỉ owner quyết, nên vòng tự động chờ owner và không tự chốt.'
      : 'Ban ngày (08:00–22:00), sau 30 phút chưa có trả lời thì làm theo Codex và ghi "chốt do hết giờ". Ngoài giờ đó thì chờ tới sáng, hỏi lại rồi mới tính 30 phút.',
    '', questionMarker(d.id, q, label, rounds),
  ].join('\n');
}

function decidedBody(d, decided) {
  const where = d.pr ? `PR #${d.pr}` : `việc ${d.task}`;
  if (!decided) return [`Câu hỏi bất đồng ${d.id} ở ${where} không còn cần owner trả lời: ${clean(d.withdrawn?.note, 300)}`, '', decidedMarker(d.id)].join('\n');
  const who = decided.decidedBy === 'owner' ? `owner chọn theo ${decided.chosen === 'codex' ? 'Codex' : 'Claude'}` : 'làm theo Codex, chốt do hết giờ (owner chưa trả lời sau 30 phút ban ngày)';
  return [`Chốt bất đồng ${d.id} ở ${where}: ${who}.`, '', 'Hướng đã chọn:', quote(decided.conclusion), '',
    ...(d.pr ? ['PR vẫn cần Author check và review mới trên head hiện tại trước khi merge.', ''] : []), decidedMarker(d.id)].join('\n');
}

const osNotify = text => execFileSync('/usr/bin/osascript', ['-e', `display notification ${JSON.stringify(clean(text, 200))} with title "Lá Lành: cần owner chọn"`], { stdio: 'ignore', timeout: 10000 });
const notifyText = d => `Claude và Codex cần owner chọn ở ${d.pr ? `PR #${d.pr}` : `việc ${d.task}`} (mã ${d.id}). Trả lời trên GitHub: Theo Claude hoặc Theo Codex.`;

function addLabel(gh, t) {
  gh.raw(['label', 'create', 'needs-owner', '--repo', repo, '--color', 'D93F0B', '--description', 'Vòng tự động dừng, chờ owner', '--force']);
  gh.raw([t.kind, 'edit', String(t.number), '--repo', repo, '--add-label', 'needs-owner']);
}

// The clock starts only once the owner has been told: the comment is posted (both agents share the
// owner's account, so GitHub does not notify) and the desktop notification went out.
function notifyOwner(d, q, { notify, nowMs, path }) {
  try { notify(notifyText(d)); } catch (error) {
    record(path, nowMs, { type: 'notify-failed', id: d.id, q, error: clean(error.message, 200) });
    return { status: 'sent-unnotified', q };
  }
  const timed = !d.ownerOnly && clockFits(nowMs);
  record(path, nowMs, { type: 'notified', id: d.id, q, clockFrom: timed ? iso(nowMs) : null, morningAt: d.ownerOnly || timed ? null : iso(nextMorning(nowMs)) });
  return { status: 'sent', q, clock: timed ? 'started' : d.ownerOnly ? 'owner-only' : 'held-until-morning' };
}

// One question: label, marker comment, then the notification. A crash after the comment never
// posts a second one: the marker for this question number is looked up first.
function send(d, { gh, notify, nowMs, path, labels }) {
  const t = targetOf(d);
  const q = d.questions.length + 1;
  const tg = readTarget(gh, t);
  const key = targetKey(t);
  const found = findQuestion(tg.comments, d.id, q);
  let askedAt = found?.createdAt ?? null;
  // The body shows the latest round of this snapshot; a recovered comment says which round it showed.
  const rounds = found ? Number(markerRe.exec(found.body ?? '')?.[3]) || d.rounds.length : d.rounds.length;
  if (!found) {
    try {
      if (!tg.labels.includes('needs-owner')) {
        addLabel(gh, t);
        record(path, nowMs, { type: 'label-added', id: d.id, target: key });
        labels.set(key, { type: 'label-added', at: iso(nowMs) });
      }
      askedAt = iso(nowMs);
      gh.comment(t.kind, t.number, questionBody(d, q, labels.get(key)?.type === 'label-added', rounds));
    } catch (error) {
      record(path, nowMs, { type: 'send-failed', id: d.id, q, error: clean(error.message, 200) });
      throw error;
    }
  }
  record(path, nowMs, { type: 'sent', id: d.id, q, askedAt, head: tg.head, rounds, key: questionKey(tg.head, rounds), ...(found ? { recovered: true } : {}) });
  return notifyOwner(d, q, { notify, nowMs, path });
}

const lockPath = () => join(stateDir, 'disputes.lock');
const locked = fn => withFileLock(lockPath(), { staleMs: 15 * 60000, busy: { status: 'busy' } }, fn);

export function escalate({ id, gh = makeGh(), notify = osNotify, nowMs = Date.now(), path = disputePath } = {}) {
  return locked(() => {
    const { map, labels } = disputeStates(read(path));
    const d = map.get(id);
    if (!d) throw new Error(`no dispute ${id}`);
    if (d.decided || d.withdrawn) throw new Error(`dispute ${id} is already closed`);
    if (!d.rounds.some(r => r.round === 2)) throw new Error('ask the owner only after round 2 still disagrees');
    const t = targetOf(d);
    if (!t) throw new Error('a task dispute needs --issue N on a round, so the owner has somewhere to answer');
    if (!d.requested) {
      const head = t.kind === 'pr' ? readTarget(gh, t).head : null;
      if (d.questions.some(q => q.key === questionKey(head, d.rounds.length))) {
        return { status: 'already-asked', reason: 'owner đã được hỏi; chưa có head mới hay lý lẽ mới' };
      }
      record(path, nowMs, { type: 'escalate', id });
    }
    return send(d, { gh, notify, nowMs, path, labels });
  });
}

export function withdraw({ id, note, nowMs = Date.now(), path = disputePath } = {}) {
  if (!String(note ?? '').trim()) throw new Error('--note is required to withdraw a dispute');
  const d = disputes(read(path)).get(id);
  if (!d) throw new Error(`no dispute ${id}`);
  if (d.decided || d.withdrawn) throw new Error(`dispute ${id} is already closed`);
  return record(path, nowMs, { type: 'withdrawn', id, note: clean(note, 300) });
}

// The turn table and the merge gate: a PR with an open dispute after round 2 is held; after a
// decision only an author check and a review newer than the decision count (Codex 14.11).
export function disputeView(events = read(disputePath)) {
  const view = {};
  for (const d of disputes(events).values()) {
    if (!d.pr) continue;
    const v = view[d.pr] ??= { hold: null, since: null };
    if (d.decided && (!v.since || timeOf(d.decided.at) > timeOf(v.since))) v.since = d.decided.at;
    const s = disputeStatus(d);
    if (!v.hold && ['ready', 'sending', 'asked', 'stale', 'superseded'].includes(s)) {
      v.hold = s === 'stale' ? `bất đồng ${d.id}: head đổi sau câu hỏi, cần hỏi lại hoặc rút`
        : s === 'superseded' ? `bất đồng ${d.id}: lý lẽ đổi sau câu hỏi, cần hỏi lại hoặc rút`
        : s === 'ready' ? `bất đồng ${d.id}: chưa hỏi owner` : `bất đồng ${d.id}: chờ owner`;
    }
  }
  return view;
}
export const afterDecision = (pr, view) => (view?.since
  ? { ...pr, comments: (pr.comments ?? []).filter(c => timeOf(c.createdAt) > timeOf(view.since)) } : pr);

// Another reason still waiting on the owner keeps needs-owner: an open question of another dispute
// on the same PR or issue, or an automatic REQUEST_CHANGES after our label (codex-review adds the
// label itself after the second one, and adding an existing label changes nothing).
function otherOwnerReason(d, tg, all, labelEvent) {
  const key = targetKey(targetOf(d));
  if ([...all.values()].some(o => o.id !== d.id && targetKey(targetOf(o)) === key && isOpenQuestion(o))) return true;
  return tg.comments.some(c => isTrusted(c) && isAutoReview(c.body) && parseVerdict(c.body)?.verdict === 'REQUEST_CHANGES' && timeOf(c.createdAt) > timeOf(labelEvent?.at));
}

function finish(d, { gh, nowMs, path, logFile, all, labels }) {
  const t = targetOf(d);
  const decided = d.decided;
  if (decided && !read(logFile).some(e => e.dispute === d.id)) {
    const last = d.rounds[(decided.rounds ?? d.rounds.length) - 1];
    append({ ...entry({ ...(d.pr ? { pr: d.pr } : { task: d.task }), claude: last.claude, codex: last.codex, winner: decided.chosen, note: decided.note ?? '', at: new Date(timeOf(decided.at)) }),
      dispute: d.id, decidedBy: decided.decidedBy, chosen: decided.chosen }, logFile);
  }
  if (t && (decided || d.questions.length)) {
    const tg = readTarget(gh, t);
    if (!tg.comments.some(c => isTrusted(c) && String(c.body ?? '').includes(decidedMarker(d.id)))) gh.comment(t.kind, t.number, decidedBody(d, decided));
    const key = targetKey(t);
    const ours = labels.get(key);
    if (tg.labels.includes('needs-owner') && ours?.type === 'label-added' && !otherOwnerReason(d, tg, all, ours)) {
      gh.raw([t.kind, 'edit', String(t.number), '--repo', repo, '--remove-label', 'needs-owner']);
      record(path, nowMs, { type: 'label-removed', id: d.id, target: key });
      labels.set(key, { type: 'label-removed', at: iso(nowMs) });
    }
  }
  record(path, nowMs, { type: 'closed', id: d.id });
  return decided ? { status: 'decided', decidedBy: decided.decidedBy, chosen: decided.chosen } : { status: 'withdrawn' };
}

function decide(d, { decidedBy, chosen, q, head, nowMs, path }) {
  const last = askedRound(d, q);
  d.decided = record(path, nowMs, { type: 'decided', id: d.id, q: q.q, rounds: q.rounds, decidedBy, chosen, head,
    conclusion: chosen === 'codex' ? last.codexConclusion ?? last.codex : last.claude, ...(decidedBy === 'timeout' ? { note: 'chốt do hết giờ' } : {}) });
}

function settleOne(d, ctx) {
  const { gh, nowMs, path, all } = ctx;
  if (d.closed) return null;
  if (d.decided || d.withdrawn) return finish(d, ctx);
  const status = disputeStatus(d);
  if (status === 'debating' || status === 'ready') return null;
  const t = targetOf(d);
  const q = d.questions.at(-1);
  // A failed send (or a crash before it was recorded) is retried; its clock has not started.
  if (!q) return send(d, ctx);
  // A newer round superseded the question: nothing the owner said to it and no clock applies.
  const superseded = isSuperseded(d);
  if (superseded && status !== 'sending') return { status: 'superseded' };
  const tg = readTarget(gh, t);
  if (tg.state !== 'OPEN') return { status: 'target-closed' };
  // Replies are read before anything else, also in the morning before a second question.
  // A reply without an id counts only when this was the one open question on that PR or issue at
  // the time of the reply; with two open it names the id ("Theo Codex pr515-2").
  const alone = at => ![...all.values()].some(o => o.id !== d.id && targetKey(targetOf(o)) === targetKey(t)
    && o.questions.some(x => timeOf(x.askedAt) < at) && !(timeOf(o.decided?.at ?? o.withdrawn?.at) < at));
  const reply = tg.comments
    .filter(c => isTrusted(c) && !String(c.body ?? '').includes(agentMarker) && timeOf(c.createdAt) > timeOf(q.askedAt))
    .sort((a, b) => timeOf(a.createdAt) - timeOf(b.createdAt))
    .map(c => ({ ...parseDisputeReply(c.body), at: timeOf(c.createdAt) })).filter(r => r.chosen && (r.id ? r.id === d.id.toLowerCase() : alone(r.at))).at(-1);
  if (reply && !superseded) { decide(d, { decidedBy: 'owner', chosen: reply.chosen, q, head: tg.head, nowMs, path }); return finish(d, ctx); }
  if (status === 'sending') return send(d, ctx);
  if (!q.notifiedAt) return notifyOwner(d, q.q, ctx);
  if (status === 'stale') return { status: 'stale' };
  // The head moved since the question: the owner was asked about something else, so no auto decision.
  if (t.kind === 'pr' && tg.head !== q.head) {
    record(path, nowMs, { type: 'stale', id: d.id, q: q.q, head: q.head, newHead: tg.head });
    return { status: 'stale' };
  }
  // Owner-only items never time out and are not asked again; they wait for the owner.
  if (d.ownerOnly) return { status: 'waiting-owner' };
  if (q.clockFrom) {
    if (nowMs < timeOf(q.clockFrom) + replyMinutes * 60000) return { status: 'waiting', until: iso(timeOf(q.clockFrom) + replyMinutes * 60000) };
    // A timeout only picks Codex's direction; it grants nothing the owner alone may decide and
    // the PR still needs a new check and review on its head (see disputeView).
    decide(d, { decidedBy: 'timeout', chosen: 'codex', q, head: tg.head, nowMs, path });
    return finish(d, ctx);
  }
  if (q.morningAt && nowMs >= timeOf(q.morningAt) && clockFits(nowMs)) {
    record(path, nowMs, { type: 'escalate', id: d.id, reason: 'morning' });
    return send(d, ctx);
  }
  return { status: 'held-until-morning' };
}

// Called by the tick each run. Disputes still in debate cost no GitHub call.
export function settleDisputes({ gh = makeGh(), nowMs = Date.now(), notify = osNotify, log = () => {}, path = disputePath, logFile = logPath } = {}) {
  return locked(() => {
    const { map: all, labels } = disputeStates(read(path));
    const done = [];
    for (const d of all.values()) {
      try {
        const result = settleOne(d, { gh, nowMs, notify, path, logFile, all, labels });
        if (result) done.push({ id: d.id, ...result });
      } catch (error) {
        log(`dispute ${d.id}: ${clean(error.message, 200)}`);
        done.push({ id: d.id, status: 'error', reason: clean(error.message, 200) });
      }
    }
    return { status: 'ok', done };
  });
}

const flag = (args, name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : undefined; };
const text = (args, name) => flag(args, name) ?? (flag(args, `${name}-file`) ? readFileSync(flag(args, `${name}-file`), 'utf8') : undefined);

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  const out = value => process.stdout.write(`${JSON.stringify(value)}\n`);
  try {
    if (args.includes('--add')) {
      out(append(entry({ pr: flag(args, '--pr'), task: flag(args, '--task'), claude: text(args, '--claude'), codex: text(args, '--codex'), winner: flag(args, '--winner'), note: flag(args, '--note') })));
    } else if (args.includes('--override')) {
      out(append(override({ of: flag(args, '--of'), winner: flag(args, '--winner'), note: flag(args, '--note') })));
    } else if (args.includes('--list')) {
      const date = flag(args, '--date');
      for (const e of read().filter(e => !date || e.date === date)) out(e);
    } else if (args.includes('--open')) {
      const pr = flag(args, '--pr');
      const id = flag(args, '--id');
      const known = id ? disputes().get(id) : null;
      const number = pr ?? known?.pr;
      const head = flag(args, '--head') ?? (number ? makeGh().pr(number).headRefOid : undefined);
      out(openRound({ id, pr, task: flag(args, '--task'), issue: flag(args, '--issue'), round: flag(args, '--round'), claude: text(args, '--claude'), codex: text(args, '--codex'),
        codexConclusion: flag(args, '--codex-conclusion'), head, ownerOnly: args.includes('--owner-only'), group: flag(args, '--group') }));
    } else if (args.includes('--escalate')) {
      out(escalate({ id: flag(args, '--id') }));
    } else if (args.includes('--withdraw')) {
      out(withdraw({ id: flag(args, '--id'), note: flag(args, '--note') }));
    } else if (args.includes('--settle')) {
      out(settleDisputes());
    } else if (args.includes('--status')) {
      for (const d of disputes().values()) out({ id: d.id, ...(d.pr ? { pr: d.pr } : { task: d.task }), status: disputeStatus(d), rounds: d.rounds.length, questions: d.questions.length, ownerOnly: d.ownerOnly, decided: d.decided ? { decidedBy: d.decided.decidedBy, chosen: d.decided.chosen } : null });
    } else { process.stderr.write('Usage: collab-disagree.mjs --add … | --override … | --list | --open … | --escalate --id D | --withdraw --id D --note … | --settle | --status\n'); process.exitCode = 2; }
  } catch (error) { process.stderr.write(`collab-disagree: ${error.message}\n`); process.exitCode = 1; }
}
