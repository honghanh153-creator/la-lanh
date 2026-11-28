// Three agents in parallel with fallback (three-agent dispatch, 28.11.2026, parts A and B).
// - Availability: Claude, Codex and Anti each have a state on the host (`state/agents.json`). An agent
//   out of quota is "limited" until the reset time its own error message gives; before that time the
//   loop does not call it again (28.11: the tick called Codex every 10 minutes for six days of a known
//   limit). After the reset one probe call is allowed; a new limit sets a new reset time, and with no
//   readable reset time the next probe waits probeEveryMs.
// - One coordinator lease (`state/coordinator-lease.json`): the first available agent in the order
//   Claude → Codex → Anti coordinates. A lease passes to another agent only with proof that the old
//   job stopped: the holder released it, its process is gone, or a stop record names its job. An
//   expired lease without that proof is not taken over: the loop raises an alert instead (two
//   coordinators writing the same queue is worse than one stalled coordinator). Every acquire raises
//   the epoch; state writers check it (collab-writer.mjs), so a holder that lost the lease cannot write.
// - Hand back: when a higher agent comes back, it asks; the holder releases at its next renew.
// - A sole agent (B) may do, test and push work, never approve it. R1: Codex approves; Anti reviews
//   only (part F) and never approves. With no independent approver available the PR waits.
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { hostname } from 'node:os';
import { clean, readJson, stateDir, writeJson } from './collab-trust.mjs';
import { pidAlive, withFileLock } from './collab-lock.mjs';

export const agentOrder = ['claude', 'codex', 'anti'];
// R1: the approver. Anti is review-only (part F); Claude is the implementer.
export const approvers = ['codex'];
export const probeEveryMs = 60 * 60000;
export const leaseMs = 20 * 60000;
export const waitIndependent = 'chờ review độc lập';
export const agentsPath = () => join(stateDir, 'state', 'agents.json');
export const leasePath = () => join(stateDir, 'state', 'coordinator-lease.json');

const months = { jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11 };
// "try again at Dec 4th, 2026 7:35 AM" (Codex CLI). The owner's machine runs on Vietnam time (+07:00).
export function parseResetAt(text, { offsetMinutes = 7 * 60 } = {}) {
  const m = /try again at\s+([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\s+(\d{1,2}):(\d{2})\s*([AP]M)?/i.exec(String(text ?? ''));
  if (!m) return null;
  const month = months[m[1].toLowerCase()];
  if (month === undefined) return null;
  let hour = Number(m[4]) % (m[6] ? 12 : 24);
  if (m[6]?.toUpperCase() === 'PM') hour += 12;
  const ms = Date.UTC(Number(m[3]), month, Number(m[2]), hour, Number(m[5])) - offsetMinutes * 60000;
  return Number.isFinite(ms) ? ms : null;
}

// 'available' | 'probe' (reset passed: one call allowed) | 'limited' | 'off' (not set up on this host).
export function agentStatus(state, agent, nowMs = Date.now()) {
  const s = state?.[agent];
  if (!agentOrder.includes(agent)) return 'off';
  if (!s || s.status === 'available') return 'available';
  if (s.status === 'off') return 'off';
  if (s.status !== 'limited') return 'available';
  const until = Number(s.untilMs) || 0;
  if (nowMs < until) return 'limited';
  if (s.probedAtMs && nowMs - s.probedAtMs < probeEveryMs) return 'limited';
  return 'probe';
}
export const mayCall = (state, agent, nowMs = Date.now()) => ['available', 'probe'].includes(agentStatus(state, agent, nowMs));
export const availableAgents = (state, nowMs = Date.now()) => agentOrder.filter(a => mayCall(state, a, nowMs));

// #949 r2 (A2): a fresh limit starts a new generation. The previous probe's time is dropped, so a
// short reset (5 minutes) is not held for the rest of the old probe's hour.
export function markLimited(state, agent, { reason = '', nowMs = Date.now(), untilMs = parseResetAt(reason) } = {}) {
  const until = Number.isFinite(untilMs) && untilMs > nowMs ? untilMs : nowMs + probeEveryMs;
  return { ...state, [agent]: { status: 'limited', untilMs: until, until: new Date(until).toISOString(), reason: clean(reason, 300), atMs: nowMs, probedAtMs: null } };
}
export const markAvailable = (state, agent, nowMs = Date.now()) => ({ ...state, [agent]: { status: 'available', atMs: nowMs } });
export const noteProbe = (state, agent, nowMs = Date.now()) => (state?.[agent]?.status === 'limited' ? { ...state, [agent]: { ...state[agent], probedAtMs: nowMs } } : state);

// The host keeps one agents file; every change is a read-modify-write under its lock.
export function updateAgents(change, { path = agentsPath() } = {}) {
  return withFileLock(`${path}.lock`, { staleMs: 60000, waitMs: 5000, busy: null }, () => {
    const next = change(readJson(path, {}));
    writeJson(path, next);
    return next;
  });
}
export const readAgents = ({ path = agentsPath() } = {}) => readJson(path, {});

export const coordinatorFor = available => agentOrder.find(a => available.includes(a)) ?? null;
const rank = agent => agentOrder.indexOf(agent);

// Proof that the holder's job stopped. `alive` checks a PID on this host only; a lease from another
// host needs a release or a stop record.
export function stopProof(lease, { alive = pidAlive, host = hostname() } = {}) {
  if (!lease) return 'no-lease';
  if (lease.released) return 'released';
  if ((lease.stops ?? []).includes(lease.jobId)) return 'stop-record';
  if (lease.host === host && Number.isInteger(lease.pid) && !alive(lease.pid)) return 'pid-gone';
  return null;
}

// Pure decision. Returns { action, lease, reason, alert? }; action is one of acquire, renew,
// takeover, release, wait. The caller writes `lease` when it is not null.
export function decideLease({ lease, me, jobId, pid = process.pid, host = hostname(), available, nowMs = Date.now(), alive = pidAlive }) {
  const top = coordinatorFor(available);
  const fresh = epoch => ({ holder: me, epoch, jobId, pid, host, acquiredAtMs: nowMs, renewedAtMs: nowMs, expiresAtMs: nowMs + leaseMs, released: false, stops: [] });
  if (!available.includes(me)) return { action: 'wait', lease: null, reason: `${me} không sẵn sàng` };
  if (lease && lease.holder === me && lease.jobId === jobId && !lease.released) {
    // Hand back: a higher agent asked and is available again.
    if (lease.handback && rank(lease.handback) < rank(me) && available.includes(lease.handback)) {
      return { action: 'release', lease: { ...lease, released: true, releasedAtMs: nowMs, releaseReason: `trả lại cho ${lease.handback}` }, reason: `trả lại cho ${lease.handback}` };
    }
    // A renew records the current process: a stable job (the tick) runs in a new process each round.
    return { action: 'renew', lease: { ...lease, pid, host, renewedAtMs: nowMs, expiresAtMs: nowMs + leaseMs }, reason: 'gia hạn' };
  }
  if (top !== me) return { action: 'wait', lease: null, reason: `${top} đứng trước ${me}` };
  const epoch = (lease?.epoch ?? 0) + 1;
  const proof = stopProof(lease, { alive, host });
  if (proof) return { action: lease ? 'takeover' : 'acquire', lease: fresh(epoch), reason: proof };
  // The holder is still running. Nobody takes over without stop proof; an expired lease raises the
  // alert on every branch (#949 r2 A3), including while a lower holder is asked to hand back.
  const expired = nowMs > (lease.expiresAtMs ?? 0);
  const alert = expired ? `Lease điều phối của ${lease.holder} (job ${lease.jobId}) đã hết hạn nhưng chưa có bằng chứng việc cũ đã dừng; không ai nhận thay.` : undefined;
  if (rank(lease.holder) > rank(me)) {
    const asked = lease.handback === me ? null : { ...lease, handback: me };
    return { action: 'wait', lease: asked, reason: expired ? `đã xin ${lease.holder} trả lại; lease hết hạn nhưng chưa có bằng chứng việc cũ đã dừng` : `đã xin ${lease.holder} trả lại`, alert };
  }
  return { action: 'wait', lease: null, reason: expired ? 'hết hạn nhưng chưa có bằng chứng việc cũ đã dừng' : `${lease.holder} đang giữ`, alert };
}

export function acquireLease({ me, jobId, available, path = leasePath(), nowMs = Date.now(), alive = pidAlive, host = hostname(), pid = process.pid }) {
  // A fresh host has no state folder yet; the tick asks for the lease before anything else writes there.
  mkdirSync(dirname(path), { recursive: true });
  return withFileLock(`${path}.lock`, { staleMs: 60000, waitMs: 5000, busy: { action: 'wait', reason: 'lease đang được ghi' } }, () => {
    const decision = decideLease({ lease: readJson(path, null), me, jobId, pid, host, available, nowMs, alive });
    if (decision.lease) writeJson(path, decision.lease);
    return decision;
  });
}

// #948 (b): the tick asks for the lease on every round. Its job id is stable per host, so the next
// round renews the lease instead of waiting on its own previous round; the coordinator is the first
// available agent in agentOrder.
export const tickJobId = (host = hostname()) => `collab-tick@${host}`;
export function tickLease({ available, nowMs = Date.now(), path = leasePath(), alive = pidAlive, host = hostname(), pid = process.pid } = {}) {
  const me = coordinatorFor(available);
  if (!me) return { action: 'wait', lease: null, reason: 'không agent nào sẵn sàng' };
  return acquireLease({ me, jobId: tickJobId(host), available, path, nowMs, alive, host, pid });
}

// The holder's clean exit, and a stop record written by whoever confirmed the job ended.
export function releaseLease({ me, jobId, path = leasePath(), nowMs = Date.now() }) {
  return withFileLock(`${path}.lock`, { staleMs: 60000, waitMs: 5000, busy: false }, () => {
    const lease = readJson(path, null);
    if (!lease || lease.holder !== me || lease.jobId !== jobId) return false;
    writeJson(path, { ...lease, released: true, releasedAtMs: nowMs });
    return true;
  });
}
export function recordStop({ jobId, path = leasePath() }) {
  return withFileLock(`${path}.lock`, { staleMs: 60000, waitMs: 5000, busy: false }, () => {
    const lease = readJson(path, null);
    if (!lease) return false;
    writeJson(path, { ...lease, stops: [...new Set([...(lease.stops ?? []), jobId])] });
    return true;
  });
}

// B: who may approve a PR. The approver must be available and not the author.
export const mayApprove = (agent, author) => approvers.includes(agent) && agent !== author;
export function reviewPlan({ author, available }) {
  const approver = approvers.find(a => available.includes(a) && mayApprove(a, author));
  if (approver) return { status: 'review', approver };
  const soleAgent = available.length === 1 ? available[0] : null;
  return { status: 'wait', reason: waitIndependent, soleAgent, mayWork: available.filter(a => a !== 'anti') };
}

// #949 r1 (C4): every model call reserves its slot first. The check and the probe note are one
// critical section, so two callers cannot both spend the one probe after a reset. Returns
// { ok: true } or { ok: false, status: 'limited' | 'busy', reason, until }.
export function reserveCall(agent, { path = agentsPath(), nowMs = Date.now() } = {}) {
  mkdirSync(dirname(path), { recursive: true });
  return withFileLock(`${path}.lock`, { staleMs: 60000, waitMs: 5000, busy: { ok: false, status: 'busy', reason: 'trạng thái agent đang được ghi' } }, () => {
    const state = readJson(path, {});
    if (!mayCall(state, agent, nowMs)) {
      const until = state?.[agent]?.until ?? null;
      return { ok: false, status: 'limited', reason: `${agent} chưa dùng được${until ? ` tới ${until}` : ''}`, until };
    }
    writeJson(path, noteProbe(state, agent, nowMs));
    return { ok: true };
  });
}
// The call's outcome (#949 r2 A1, N2). A limit keeps its reset time: the caller parses it from the
// whole captured output (`untilMs`) before the stored reason is cut short. Only a usable answer
// (`ok`) says the agent is back, and never for an agent switched off on this host. Any other failure
// (network, auth, timeout) leaves the state as it is, so a failed probe keeps its hour of backoff.
export function nextAgentState(state, agent, { ok = false, limited = false, reason = '', untilMs, nowMs = Date.now() } = {}) {
  if (limited) return markLimited(state, agent, { reason, nowMs, untilMs: Number.isFinite(untilMs) ? untilMs : parseResetAt(reason) });
  if (!ok) return state;
  const now = state?.[agent]?.status;
  return now && now !== 'available' && now !== 'off' ? markAvailable(state, agent, nowMs) : state;
}
export function noteCallResult(agent, { ok = false, limited = false, reason = '', untilMs, path = agentsPath(), nowMs = Date.now() } = {}) {
  try {
    return updateAgents(state => nextAgentState(state, agent, { ok, limited, reason, untilMs, nowMs }), { path });
  } catch { return null; }
}
// What a failed subprocess call said, for the limit check and the reset time (stdout, stderr, message).
export const callOutput = error => [error?.stdout, error?.stderr, error?.message].map(x => String(x ?? '')).join('\n');
export const limitOf = (error, isLimit) => { const full = callOutput(error); return { limited: Boolean(isLimit(full)), untilMs: parseResetAt(full), reason: clean(String(error?.message ?? ''), 200) }; };

// #949 r1 (C3): who implemented a PR. The PR template line "Agent thực hiện:" and the branch
// prefix must agree; a PR that names nobody, or two different agents, has no known author and
// no one may approve it.
const agentNames = { claude: 'claude', codex: 'codex', anti: 'anti', antigravity: 'anti' };
export function implementerOf(pr) {
  const line = /^\s*Agent thực hiện:\s*([A-Za-z]+)/mi.exec(String(pr?.body ?? ''))?.[1]?.toLowerCase();
  const fromBody = line ? agentNames[line] ?? null : null;
  const fromBranch = /^agent\/(claude|codex|anti)\//.exec(String(pr?.headRefName ?? ''))?.[1] ?? null;
  if (line && !fromBody) return null;
  if (fromBody && fromBranch && fromBody !== fromBranch) return null;
  return fromBody ?? fromBranch;
}
