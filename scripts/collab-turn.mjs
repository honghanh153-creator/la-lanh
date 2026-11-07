// Whose turn is it on each open PR? `--report` replaces the registry PRs; `--tick` is the launchd safety net.
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { areaOrder, classifyArea, clean, codexDailyCap, dayStatePath, integration, isOwnPr, makeGh, readJson, repo, reviewState, sortByPriority, stateDir, vnNow, writeJson } from './collab-trust.mjs';
import { lastStartAt, makePlan, readPlanStatus } from './collab-plan.mjs';
import { bodyHash } from './collab-heal.mjs';
import { preflightFailure, readPreflight, recordPreflight } from './collab-preflight.mjs';
import { withRepeatNote } from './collab-size.mjs';
import { withFileLock } from './collab-lock.mjs';
import { bufferStatus } from './collab-buffer.mjs';

export { codexDailyCap };

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

export function fileBlocker(pr, prs = [], { dropped = [] } = {}) {
  const mine = new Set(prFiles(pr));
  if (!mine.size) return null;
  const order = sortByPriority([pr, ...prs.filter(o => o.number !== pr.number && canMove(o, dropped))]);
  return order.slice(0, order.indexOf(pr)).find(o => prFiles(o).some(f => mine.has(f)))?.number ?? null;
}

export function prTurn(pr, { dropped = [], open = [], preflight = {} } = {}) {
  const head = pr.headRefOid;
  const out = (turn, reason) => ({ number: pr.number, title: pr.title, area: classifyArea(pr), head, base: pr.baseRefName, turn, reason, files: prFiles(pr), bodyHash: bodyHash(pr.body) });
  const labels = (pr.labels ?? []).map(l => l.name ?? l);
  if (!isOwnPr(pr)) return out('hold', 'PR không phải của owner hoặc từ fork: không chạy, không review');
  if (pr.baseRefName === 'main') return out('hold', 'base là main: chỉ owner');
  if (pr.isDraft) return out('hold', 'draft');
  if (labels.includes('needs-owner')) return out('hold', 'needs-owner');
  if (dropped.includes(pr.number)) return out('hold', 'owner bỏ khỏi plan hôm nay');
  if (pr.baseRefName !== integration) return out('hold', `xếp chồng trên ${pr.baseRefName}`);
  const blocker = fileBlocker(pr, open, { dropped });
  if (blocker) return out('hold', `chờ PR #${blocker} cùng file`);
  // A conflict needs Claude at any stage: on 02.11 an approved PR in conflict kept every tick on a
  // refused merge for three hours, and checking or reviewing a head that cannot merge wastes the run (K24).
  if (pr.mergeable === 'CONFLICTING') return out('claude-fix', 'xung đột với collab/integration');
  const state = reviewState(pr);
  const check = state.check;
  const last = state.last?.verdict;
  const pre = check ? null : preflightFailure(preflight, pr);
  if (pre) return out('claude-fix', `preflight: ${clean(pre.join('; '), 200)}`);
  if (!check) return out('claude-check', 'chưa có Author check @ head');
  if (check.status === 'FAIL') return out('claude-fix', 'Author check FAIL @ head');
  if (!last || last.sha !== head) return out('codex-review', last ? `verdict cuối cho ${last.sha.slice(0, 7)}` : 'chưa có verdict');
  if (last.verdict === 'REQUEST_CHANGES') return out('claude-fix', 'REQUEST_CHANGES @ head');
  return out('merge', 'APPROVE @ head');
}

export function turnsFor(prs, options = {}) {
  const preflight = options.preflight ?? readPreflight();
  return sortByPriority(prs).map(pr => withRepeatNote(prTurn(pr, { ...options, open: prs, preflight }), pr));
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

export const idleTopUpRuns = 3;
export const idleAlertRuns = 6;

export function tick({ gh = makeGh(), now, clock, preflight: tools = () => [], prPreflight: preflight = () => ({ status: 'PASS' }), heavyFree = () => true, nowMs = Date.now, check = () => ({ status: 'skipped' }), review, merge, alert, board = () => {}, log = () => {}, watchdog = () => {}, health = () => [] } = {}) {
  // The clock is read again before each action, so a long review cannot push the next one past 23:30.
  const time = clock ?? (now ? () => now : () => vnNow());
  now = time();
  return withLock(() => {
    const dayPath = dayStatePath(now.date);
    const day = readJson(dayPath, { codexRuns: 0, failures: 0 });
    const heartbeat = status => writeJson(join(stateDir, 'heartbeat.json'), { at: new Date().toISOString(), vn: now, status });
    // The phone-visible board must never break a tick.
    const show = info => {
      const counts = readJson(dayPath, day);
      try { board({ now: time(), codexRuns: counts.codexRuns ?? 0, failures: counts.failures ?? 0, ...info }); } catch {}
    };
    // The scheduled-run watchdog runs before the plan gate, so it also watches at night; it never breaks a tick.
    try { watchdog(); } catch {}
    try {
      // Missing tools fail inside the handler, so the heartbeat, the counter and the alert still work.
      const missing = tools();
      if (missing.length) throw new Error(`thiếu công cụ trên PATH: ${missing.join(', ')}`);
      let plan = readPlanStatus(gh, now);
      if (plan.state === 'not-made') {
        const turns = turnsFor(gh.openPrs());
        makePlan(gh, now, turns, { codexLeft: Math.max(0, codexDailyCap - day.codexRuns), gap: tickGap(readJson(join(stateDir, 'heartbeat.json'), null)), health: (() => { try { return health(); } catch { return []; } })() });
        heartbeat('plan-made');
        show({ status: 'plan-made', turns });
        return { status: 'plan-made' };
      }
      if (plan.state !== 'open') {
        heartbeat(plan.state);
        show({ status: plan.state, turns: plan.state === 'closed' ? [] : turnsFor(gh.openPrs(), { dropped: plan.dropped }) });
        return { status: plan.state };
      }
      // Every tick works when the plan is open (retro D1, 31.10.2026): the locks keep heavy jobs
      // serial and the state on GitHub keeps work from repeating, so an hourly gate only cost time.
      const prs = gh.openPrs();
      const turns = turnsFor(prs, { dropped: plan.dropped });
      // #253: the scheduled tick samples the flow metric and owns the buffer top-up, so the
      // persisted queue and --status agree and the metric does not depend on report reads.
      const { queue: buffer } = bufferStatus(prs, turns);
      const area = activeArea(turns);
      const work = turns.filter(t => t.area === area);
      const done = [];
      const late = () => { const t = time(); return t.hour * 60 + t.minute >= lastStartAt; };
      for (const t of work.filter(t => t.turn === 'merge').slice(0, 2)) {
        if (late()) break;
        show({ status: 'running', doing: `merge #${t.number}`, expectMinutes: 5, area, turns, done });
        done.push({ pr: t.number, merge: merge(t.number) });
      }
      // Author checks need no AI: the tick runs them in the dedicated clone, one at a time, then reviews.
      // Fix A: a fast preflight first; a failure is recorded (nothing posted) and costs no check slot.
      // Fix E (04.11.2026): while the heavy-job lock is free and another PR is ready, the tick starts
      // it at once instead of waiting 10 minutes for the next run. Checks stay strictly serial here,
      // and the check lock still refuses a second heavy job from anywhere else.
      const checked = [];
      const startedMs = nowMs();
      let checks = 0;
      for (const t of work.filter(t => t.turn === 'claude-check')) {
        if (late() || checks >= checksPerTick || nowMs() - startedMs > drainMinutes * 60000) break;
        const pre = preflight(t.number);
        if (pre?.status === 'FAIL') { recordPreflight(t.number, t.head, { ...pre, bodyHash: pre.bodyHash ?? t.bodyHash }); done.push({ pr: t.number, preflight: pre }); continue; }
        if (checks > 0 && !heavyFree()) break;
        show({ status: 'running', doing: `author check #${t.number} (thường 10–35 phút)`, expectMinutes: 90, area, turns, done });
        const result = check(t.number, { auto: true, clock: time });
        checks += 1;
        done.push({ pr: t.number, check: result });
        if (result?.status === 'preflight') { recordPreflight(t.number, t.head, { status: 'FAIL', reasons: result.reasons ?? [], bodyHash: result.bodyHash ?? t.bodyHash }); checks -= 1; continue; }
        if (result?.status === 'PASS') checked.push(t);
        if (!['PASS', 'FAIL'].includes(result?.status)) break;
      }
      for (const t of [...checked, ...work.filter(t => t.turn === 'codex-review')]) {
        const fresh = readJson(dayPath, day);
        if (done.filter(d => d.review).length >= 2 || fresh.codexRuns >= codexDailyCap || late()) break;
        show({ status: 'running', doing: `Codex review #${t.number}`, expectMinutes: 30, area, turns, done });
        const result = review(t.number, { auto: true, now: time() });
        done.push({ pr: t.number, review: result });
        // Usage limit: wait for the reset; busy: a direct review holds the clone. The next run retries.
        if (['limit', 'busy'].includes(result?.status)) break;
      }
      // Retro S1 (K26/K31: 02.11 and 03.11 ran about two hours with no area): count runs in a row
      // with no area. From the third Claude is told to top up from the backlog; the sixth alerts.
      const idleRuns = area ? 0 : (readJson(dayPath, day).idleRuns ?? 0) + 1;
      writeJson(dayPath, { ...readJson(dayPath, day), idleRuns });
      writeJson(join(stateDir, 'claude-queue.json'), {
        at: new Date().toISOString(), plan: plan.state, area, items: turns.filter(t => t.turn === 'claude-fix'),
        // Plan top-up (owner 31.10.2026, buffer rule 05.11): below the ready-buffer target while the
        // day still runs, so Claude adds the next backlog task in priority order before the machine goes idle.
        topUp: (buffer.topUp || idleRuns >= idleTopUpRuns) && !late(),
        topUpCount: late() ? 0 : Math.max(buffer.topUpCount, idleRuns >= idleTopUpRuns ? 1 : 0), buffer: buffer.buffer,
        idleRuns,
      });
      if (idleRuns === idleAlertRuns && alert) alert(`collab tick chạy không ${idleRuns} lượt liền (${now.date} ${now.hour}:${String(now.minute).padStart(2, '0')}): plan không còn PR nào để làm, cần bổ sung việc từ backlog`);
      const errors = done.filter(d => d.review?.status === 'error' || d.merge?.status === 'error' || d.check?.status === 'error');
      const failures = errors.length ? (readJson(dayPath, day).failures ?? 0) + 1 : 0;
      writeJson(dayPath, { ...readJson(dayPath, day), lastRunHour: now.hour, failures });
      heartbeat(errors.length ? 'ran-with-errors' : 'ran');
      // A review waiting while the daily Codex cap is spent is a budget stop, not "no work" (#145 r2).
      const capped = !done.length && work.some(t => t.turn === 'codex-review') && (readJson(dayPath, day).codexRuns ?? 0) >= codexDailyCap;
      show({ status: errors.length ? 'ran-with-errors' : done.length ? 'ran' : capped ? 'cap' : 'idle', area, turns, done, error: errors.length ? JSON.stringify(errors) : null });
      if (failures === 2 && alert) alert(`collab tick có lỗi 2 lần liên tiếp (${now.date} ${now.hour}h): ${clean(JSON.stringify(errors), 300)}`);
      log(JSON.stringify(done));
      return { status: errors.length ? 'ran-with-errors' : 'ran', area, done };
    } catch (error) {
      const failures = (readJson(dayPath, day).failures ?? 0) + 1;
      writeJson(dayPath, { ...readJson(dayPath, day), failures });
      heartbeat(`error: ${clean(error.message, 200)}`);
      show({ status: 'error', error: error.message });
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
  return { plan, prs, turns: turnsFor(prs, { dropped: plan.dropped }) };
}

export function opsAlert(gh, text, subject = 'collab loop') {
  gh.raw(['label', 'create', 'ops-alert', '--repo', repo, '--color', 'B60205', '--force']);
  gh.raw(['issue', 'create', '--repo', repo, '--title', `[ops-alert] ${subject} ${vnNow().date}`, '--label', 'ops-alert', '--body-file', '-'],
    `${clean(text, 1000)}\n\nKiểm tra log ở ~/.cache/la-lanh-collab/logs trên máy owner.\n\n<!-- la-lanh-agent ops-alert -->`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  try {
    const gh = makeGh();
    if (args.includes('--tick')) {
      // codex-review imports this module, so the tick entry lives in collab-tick.mjs (no import cycle).
      process.stderr.write('Use: node scripts/collab-tick.mjs\n'); process.exitCode = 2;
    } else if (args.includes('--status')) {
      const { plan, prs, turns } = planTurns(gh);
      const { queue: buffer } = bufferStatus(prs, turns);
      process.stdout.write(`${JSON.stringify({ plan: plan.state, reason: plan.reason, dropped: plan.dropped, queue: { ...readJson(join(stateDir, 'claude-queue.json'), null), ...buffer } })}\n`);
    } else {
      const { prs, turns } = planTurns(gh);
      const { lines } = bufferStatus(prs, turns);
      process.stdout.write(`${args.includes('--json') ? JSON.stringify(turns, null, 2) : [renderReport(turns), ...lines].join('\n')}\n`);
    }
  } catch (error) { process.stderr.write(`collab-turn failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
}
