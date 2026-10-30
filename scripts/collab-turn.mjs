// Whose turn is it on each open PR? `--report` replaces the registry PRs; `--tick` is the launchd safety net.
import { closeSync, mkdirSync, openSync, rmSync, statSync, writeSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { areaOrder, classifyArea, clean, dayStatePath, integration, makeGh, readJson, repo, reviewState, sortByPriority, stateDir, vnNow, writeJson } from './collab-trust.mjs';
import { lastStartAt, makePlan, readPlanStatus } from './collab-plan.mjs';

export const codexDailyCap = 12;

export function prTurn(pr, { dropped = [] } = {}) {
  const head = pr.headRefOid;
  const out = (turn, reason) => ({ number: pr.number, title: pr.title, area: classifyArea(pr), head, base: pr.baseRefName, turn, reason });
  const labels = (pr.labels ?? []).map(l => l.name ?? l);
  if (pr.baseRefName === 'main') return out('hold', 'base là main: chỉ owner');
  if (pr.isDraft) return out('hold', 'draft');
  if (labels.includes('needs-owner')) return out('hold', 'needs-owner');
  if (dropped.includes(pr.number)) return out('hold', 'owner bỏ khỏi plan hôm nay');
  if (pr.baseRefName !== integration) return out('hold', `xếp chồng trên ${pr.baseRefName}`);
  const state = reviewState(pr);
  const check = state.check;
  const last = state.last?.verdict;
  if (!check) return out('claude-check', 'chưa có Author check @ head');
  if (check.status === 'FAIL') return out('claude-fix', 'Author check FAIL @ head');
  if (!last || last.sha !== head) return out('codex-review', last ? `verdict cuối cho ${last.sha.slice(0, 7)}` : 'chưa có verdict');
  if (last.verdict === 'REQUEST_CHANGES') return out('claude-fix', 'REQUEST_CHANGES @ head');
  return out('merge', 'APPROVE @ head');
}

export function turnsFor(prs, options) {
  return sortByPriority(prs).map(pr => prTurn(pr, options));
}

// Owner order: finish every content PR before privacy, and privacy before features.
// Held PRs do not block a later group; anything else in an earlier group does.
export function activeArea(turns) {
  return areaOrder.find(area => turns.some(t => t.area === area && t.turn !== 'hold')) ?? null;
}

export function renderReport(turns) {
  const rows = turns.map(t => `#${t.number}\t${t.area}\t${t.turn}\t${t.head?.slice(0, 7)}\t${clean(t.reason, 80)}\t${clean(t.title, 80)}`);
  return ['PR\tnhóm\tlượt\thead\tlý do\ttiêu đề', ...rows].join('\n');
}

// One tick at a time; a lock older than 90 minutes belongs to a crashed run.
function withLock(fn) {
  mkdirSync(stateDir, { recursive: true });
  const path = join(stateDir, 'tick.lock');
  try { if (Date.now() - statSync(path).mtimeMs > 90 * 60000) rmSync(path); } catch {}
  let fd;
  try { fd = openSync(path, 'wx'); } catch { return { status: 'locked' }; }
  try { writeSync(fd, String(process.pid)); return fn(); } finally { closeSync(fd); rmSync(path, { force: true }); }
}

export function tick({ gh = makeGh(), now, clock, review, merge, alert, log = () => {} } = {}) {
  // The clock is read again before each action, so a long review cannot push the next one past 23:30.
  const time = clock ?? (now ? () => now : () => vnNow());
  now = time();
  return withLock(() => {
    const dayPath = dayStatePath(now.date);
    const day = readJson(dayPath, { codexRuns: 0, failures: 0 });
    const heartbeat = status => writeJson(join(stateDir, 'heartbeat.json'), { at: new Date().toISOString(), vn: now, status });
    try {
      let plan = readPlanStatus(gh, now);
      if (plan.state === 'not-made') {
        const turns = turnsFor(gh.openPrs());
        makePlan(gh, now, turns, { codexLeft: Math.max(0, codexDailyCap - day.codexRuns) });
        heartbeat('plan-made');
        return { status: 'plan-made' };
      }
      if (plan.state !== 'open') { heartbeat(plan.state); return { status: plan.state }; }
      if (day.lastRunHour === now.hour) { heartbeat('already-ran-this-hour'); return { status: 'already-ran-this-hour' }; }
      const turns = turnsFor(gh.openPrs(), { dropped: plan.dropped });
      const area = activeArea(turns);
      const work = turns.filter(t => t.area === area);
      const done = [];
      const late = () => { const t = time(); return t.hour * 60 + t.minute >= lastStartAt; };
      for (const t of work.filter(t => t.turn === 'merge').slice(0, 2)) {
        if (late()) break;
        done.push({ pr: t.number, merge: merge(t.number) });
      }
      for (const t of work.filter(t => t.turn === 'codex-review')) {
        const fresh = readJson(dayPath, day);
        if (done.filter(d => d.review).length >= 2 || fresh.codexRuns >= codexDailyCap || late()) break;
        const result = review(t.number, { auto: true, now: time() });
        done.push({ pr: t.number, review: result });
        // Usage limit: wait for the reset; busy: a direct review holds the clone. The next run retries.
        if (['limit', 'busy'].includes(result?.status)) break;
      }
      writeJson(join(stateDir, 'claude-queue.json'), {
        at: new Date().toISOString(), plan: plan.state, area, items: work.filter(t => t.turn.startsWith('claude-')),
      });
      const errors = done.filter(d => d.review?.status === 'error' || d.merge?.status === 'error');
      const failures = errors.length ? (readJson(dayPath, day).failures ?? 0) + 1 : 0;
      writeJson(dayPath, { ...readJson(dayPath, day), lastRunHour: now.hour, failures });
      heartbeat(errors.length ? 'ran-with-errors' : 'ran');
      if (failures === 2 && alert) alert(`collab tick có lỗi 2 lần liên tiếp (${now.date} ${now.hour}h): ${clean(JSON.stringify(errors), 300)}`);
      log(JSON.stringify(done));
      return { status: errors.length ? 'ran-with-errors' : 'ran', area, done };
    } catch (error) {
      const failures = (readJson(dayPath, day).failures ?? 0) + 1;
      writeJson(dayPath, { ...readJson(dayPath, day), failures });
      heartbeat(`error: ${clean(error.message, 200)}`);
      if (failures === 2 && alert) alert(`collab tick lỗi 2 lần liên tiếp (${now.date} ${now.hour}:${String(now.minute).padStart(2, '0')}): ${clean(error.message, 300)}`);
      return { status: 'error', error: clean(error.message, 300) };
    }
  });
}

export function opsAlert(gh, text) {
  gh.raw(['label', 'create', 'ops-alert', '--repo', repo, '--color', 'B60205', '--force']);
  gh.raw(['issue', 'create', '--repo', repo, '--title', `[ops-alert] collab loop ${vnNow().date}`, '--label', 'ops-alert', '--body-file', '-'],
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
      const plan = readPlanStatus(gh);
      process.stdout.write(`${JSON.stringify({ plan: plan.state, reason: plan.reason, dropped: plan.dropped, queue: readJson(join(stateDir, 'claude-queue.json'), null) })}\n`);
    } else {
      const turns = turnsFor(gh.openPrs());
      process.stdout.write(`${args.includes('--json') ? JSON.stringify(turns, null, 2) : renderReport(turns)}\n`);
    }
  } catch (error) { process.stderr.write(`collab-turn failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
}
