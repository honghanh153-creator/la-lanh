// Liveness watchdog for the unattended Claude runs (owner 03.11.2026). A scheduled run that waits
// on a permission prompt never ends, and runs after it never start: autopilot sat 2.5 days and the
// server check a week before anyone saw it. Each run writes a start and a done beat; the tick,
// which needs no AI and no prompt, reports a task whose done beat is older than its schedule allows.
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
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
  if (!['start', 'done'].includes(phase)) throw new Error(`phase must be start or done: ${phase}`);
  const prev = readJson(beatPath(task), {});
  const next = { ...prev, task, [phase === 'start' ? 'startedAt' : 'doneAt']: new Date(nowMs).toISOString() };
  writeJson(beatPath(task), next);
  return next;
}

// A task with no beat file starts its clock when the watchdog first sees it, so installing the
// watchdog does not alert on every task at once.
export function readBeats(nowMs = Date.now()) {
  return Object.fromEntries(Object.keys(watched).map(task => {
    let b = readJson(beatPath(task), null);
    if (!b) { b = { task, baselineAt: new Date(nowMs).toISOString() }; writeJson(beatPath(task), b); }
    return [task, b];
  }));
}

export function staleTasks(beats, nowMs = Date.now(), vn = vnNow(new Date(nowMs))) {
  const at = vn.hour * 60 + vn.minute;
  return Object.entries(watched).flatMap(([task, rule]) => {
    if (rule.activeFrom && at < rule.activeFrom) return [];
    const b = beats[task] ?? {};
    const lastMs = Date.parse(b.doneAt ?? b.baselineAt ?? 0) || 0;
    if (nowMs - lastMs <= rule.maxMinutes * 60000) return [];
    const startedMs = Date.parse(b.startedAt ?? 0) || 0;
    // Started after the last done and never finished: the usual shape of a permission prompt.
    const stuckSince = startedMs > lastMs ? startedMs : null;
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

// One alert per stale episode: a new done beat ends the episode, so the next stall alerts again.
export function watch({ nowMs = Date.now(), alert = () => {}, notify = osNotify } = {}) {
  const beats = readBeats(nowMs);
  const stale = staleTasks(beats, nowMs);
  const sent = readJson(alertPath(), {});
  const fresh = stale.filter(s => sent[s.task] !== (s.lastDoneAt ?? 'none'));
  for (const s of fresh) {
    const text = describeStale(s);
    try { notify(text); } catch {}
    try { alert(`${text}\n\nCách xử lý: mở Claude → Scheduled → mở tác vụ này, dừng hoặc duyệt lần chạy đang treo. Watchdog: scripts/collab-watchdog.mjs (tick 10 phút, không dùng AI).`); } catch {}
    sent[s.task] = s.lastDoneAt ?? 'none';
  }
  for (const task of Object.keys(sent)) if (!stale.some(s => s.task === task)) delete sent[task];
  writeJson(alertPath(), sent);
  return { stale: stale.map(s => s.task), alerted: fresh.map(s => s.task) };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  try {
    if (args[0] === '--beat') process.stdout.write(`${JSON.stringify(beat(args[1], args[2]))}\n`);
    else if (args[0] === '--report') process.stdout.write(`${healthLines(readBeats()).join('\n')}\n`);
    else { process.stderr.write('Use: node scripts/collab-watchdog.mjs --beat <task> start|done | --report\n'); process.exitCode = 2; }
  } catch (error) { process.stderr.write(`collab-watchdog failed: ${clean(error.message, 300)}\n`); process.exitCode = 1; }
}
