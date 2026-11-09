// Liveness watchdog for the unattended Claude runs (owner 03.11.2026). A scheduled run that waits
// on a permission prompt never ends, and runs after it never start: autopilot sat 2.5 days and the
// server check a week before anyone saw it. Each run writes a start and a done beat; the tick,
// which needs no AI and no prompt, reports a task whose done beat is older than its schedule allows.
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { deliverPendingAlerts } from './collab-heal.mjs';
import { clean, readJson, stateDir, vnNow, writeJson } from './collab-trust.mjs';

// maxMinutes = schedule interval + jitter + a normal run. activeFrom: autopilot only runs 9–23,
// so the overnight gap is not a miss; from 11:00 its 09:37 and 10:37 runs should have finished.
export const watched = {
  'la-lanh-autopilot': { label: 'Autopilot (mỗi giờ)', maxMinutes: 120, activeFrom: 11 * 60 },
  'la-lanh-ops-watch': { label: 'Kiểm tra server (6 giờ/lần)', maxMinutes: 7 * 60 },
  'la-lanh-retro': { label: 'Báo cáo cuối ngày (23:35)', maxMinutes: 26 * 60 },
};

const beatsDir = () => join(stateDir, 'beats');
const beatPath = task => join(beatsDir(), `${task}.json`);
const alertPath = () => join(beatsDir(), 'alerts.json');
const hhmm = ms => { const t = vnNow(new Date(ms)); return `${t.date.slice(8)}.${t.date.slice(5, 7)} ${String(t.hour).padStart(2, '0')}:${String(t.minute).padStart(2, '0')}`; };

export function beat(task, phase, nowMs = Date.now()) {
  if (!watched[task]) throw new Error(`unknown task: ${task}`);
  if (!['start', 'done', 'stuck'].includes(phase)) throw new Error(`phase must be start, done or stuck: ${phase}`);
  const prev = readJson(beatPath(task), {});
  const next = { ...prev, task, [{ start: 'startedAt', done: 'doneAt', stuck: 'stuckAt' }[phase]]: new Date(nowMs).toISOString() };
  writeJson(beatPath(task), next);
  return next;
}

// Fix D (04.11.2026): a start beat with no done beat for more than 30 minutes is a stuck run. The
// watchdog records a stuck beat, so a run that asks "is the last one still going?" (--running) is
// not blocked by it, and alerts as for any stale task. It never kills a process.
export const stuckMinutes = 30;
const ms = value => Date.parse(value ?? 0) || 0;
export const isStuck = (b = {}, nowMs = Date.now()) => ms(b.startedAt) > Math.max(ms(b.doneAt), ms(b.stuckAt)) && nowMs - ms(b.startedAt) > stuckMinutes * 60000;
export const isRunning = (b = {}) => ms(b.startedAt) > Math.max(ms(b.doneAt), ms(b.stuckAt));
export function markStuck(beats, nowMs = Date.now()) {
  return Object.keys(beats).filter(task => watched[task] && isStuck(beats[task], nowMs)).map(task => {
    beats[task] = beat(task, 'stuck', nowMs);
    return task;
  });
}

// A task with no beat file starts its clock when the watchdog first sees it, so installing the
// watchdog does not alert on every task at once.
export function readBeats(nowMs = Date.now()) {
  return Object.fromEntries(Object.keys(watched).map(task => {
    let b = readJson(beatPath(task), null);
    // A file with only a start beat (the run began before the first tick) gets the same grace.
    if (!b?.doneAt && !b?.baselineAt) { b = { task, ...b, baselineAt: new Date(nowMs).toISOString() }; writeJson(beatPath(task), b); }
    return [task, b];
  }));
}

export function staleTasks(beats, nowMs = Date.now(), vn = vnNow(new Date(nowMs))) {
  const at = vn.hour * 60 + vn.minute;
  return Object.entries(watched).flatMap(([task, rule]) => {
    const b = beats[task] ?? {};
    const lastMs = Date.parse(b.doneAt ?? b.baselineAt ?? 0) || 0;
    const startedMs = Date.parse(b.startedAt ?? 0) || 0;
    // A run stuck for 30 minutes is reported at any hour, before its schedule limit. #229: an
    // unfinished start is judged against the done beat only; the first-sight baseline is later
    // than a start that was already running, and markStuck releases that run anyway.
    const doneMs = ms(b.doneAt);
    const stuckRun = startedMs > doneMs && nowMs - startedMs > stuckMinutes * 60000;
    if (!stuckRun && rule.activeFrom && at < rule.activeFrom) return [];
    if (!stuckRun && nowMs - lastMs <= rule.maxMinutes * 60000) return [];
    // Started after the last done and never finished: the usual shape of a permission prompt.
    const stuckSince = startedMs > doneMs ? startedMs : null;
    return [{ task, label: rule.label, lastDoneAt: b.doneAt ?? null, stuckSince: stuckSince ? new Date(stuckSince).toISOString() : null }];
  });
}

export function describeStale(s) {
  const last = s.lastDoneAt ? `lần xong cuối ${hhmm(Date.parse(s.lastDoneAt))}` : 'chưa có lần nào báo xong';
  const stuck = s.stuckSince
    ? ` Lần chạy bắt đầu lúc ${hhmm(Date.parse(s.stuckSince))} chưa xong: thường là đang chờ bấm "cho phép".`
    : ' Không có lần chạy nào bắt đầu: tác vụ có thể bị tắt, hoặc lần chạy trước còn treo.';
  return `${s.label}: quá hạn, ${last}.${stuck}`;
}

// Plan line: the owner sees the health of every unattended run each morning, alert or not.
export function healthLines(beats, nowMs = Date.now(), vn = vnNow(new Date(nowMs))) {
  const stale = new Set(staleTasks(beats, nowMs, vn).map(s => s.task));
  return Object.entries(watched).map(([task, rule]) => {
    const done = beats[task]?.doneAt;
    return `- ${stale.has(task) ? '⚠️' : '✅'} ${rule.label}: ${done ? `xong lần cuối ${hhmm(Date.parse(done))}` : 'chưa báo xong lần nào'}`;
  });
}

const osNotify = text => execFileSync('/usr/bin/osascript', ['-e', `display notification ${JSON.stringify(clean(text, 200))} with title "Lá Lành: tác vụ hẹn giờ bị treo"`], { stdio: 'ignore', timeout: 10000 });

// One alert per stale episode and channel. A channel that failed is retried on the next tick; a
// new done beat ends the episode, so the next stall alerts again. Hours when a task is not watched
// (autopilot before 11:00) keep the marker, so one stall does not alert again every morning.
export function watch({ nowMs = Date.now(), alert = () => {}, notify = osNotify } = {}) {
  const beats = readBeats(nowMs);
  const stale = staleTasks(beats, nowMs);
  const stuck = markStuck(beats, nowMs);
  const sent = readJson(alertPath(), {});
  const episode = task => beats[task]?.doneAt ?? 'none';
  for (const task of Object.keys(sent)) if (sent[task]?.episode !== episode(task)) delete sent[task];
  const alerted = [];
  for (const s of stale) {
    const mark = sent[s.task] ?? { episode: episode(s.task), notify: false, alert: false };
    if (mark.notify && mark.alert) continue;
    const text = describeStale(s);
    const channels = {
      notify: () => notify(text),
      alert: () => alert(`${text}\n\nCách xử lý: mở Claude → Scheduled → mở tác vụ này, dừng hoặc duyệt lần chạy đang treo. Watchdog: scripts/collab-watchdog.mjs (tick 10 phút, không dùng AI).`),
    };
    for (const [name, send] of Object.entries(channels)) {
      if (mark[name]) continue;
      try { send(); mark[name] = true; } catch {}
    }
    sent[s.task] = mark;
    alerted.push(s.task);
  }
  writeJson(alertPath(), sent);
  // Stuck-step alerts queued by runGroup during a check (never sent inline).
  const queued = deliverPendingAlerts({ alert });
  return { stale: stale.map(s => s.task), alerted, stuck, queued };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  try {
    if (args[0] === '--beat') process.stdout.write(`${JSON.stringify(beat(args[1], args[2]))}\n`);
    // Exit 0 while a run is in progress; a stuck run (stuck beat recorded) does not count.
    else if (args[0] === '--running') { if (!watched[args[1]]) throw new Error(`unknown task: ${args[1]}`); const on = isRunning(readJson(beatPath(args[1]), {})); process.stdout.write(`${on ? 'running' : 'free'}\n`); process.exitCode = on ? 0 : 1; }
    else if (args[0] === '--report') process.stdout.write(`${healthLines(readBeats()).join('\n')}\n`);
    else { process.stderr.write('Use: node scripts/collab-watchdog.mjs --beat <task> start|done|stuck | --running <task> | --report\n'); process.exitCode = 2; }
  } catch (error) { process.stderr.write(`collab-watchdog failed: ${clean(error.message, 300)}\n`); process.exitCode = 1; }
}
