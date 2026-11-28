// Tick gaps (L57, 21.11.2026). The tick log had no line from 07:45 to 10:04 and nobody knew why: the
// heartbeat keeps only the latest tick and the gap was reported only in the morning plan. Each tick
// now compares the previous heartbeat with the clock. A gap of 30 minutes or more is written once to
// tick-gaps.jsonl with its cause, read from the Mac itself:
// - sleep: the last sleep and wake (kern.sleeptime / kern.waketime) cover the gap, leaving under
//   30 minutes awake on each side;
// - restart: the Mac booted inside the gap (kern.boottime);
// - unknown: anything else. Only this opens an ops alert, because the loop stopped while the Mac ran.
// macOS keeps only the latest sleep, so the cause is read on the first tick after the gap.
import { execFileSync } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { readJson, stateDir, vnNow } from './collab-trust.mjs';

export const gapMinutes = 30;
export const gapLogPath = () => join(stateDir, 'tick-gaps.jsonl');
export const heartbeatPath = () => join(stateDir, 'heartbeat.json');
export const tickGapSubject = 'tick ngừng không rõ lý do';
const minute = 60000;

// `sysctl -n kern.sleeptime` prints `{ sec = 1795253517, usec = 675245 } Sat Nov 21 16:31:57 2026`.
export const parseKernTime = text => { const m = /\bsec\s*=\s*(\d+)/.exec(String(text ?? '')); return m && Number(m[1]) > 0 ? Number(m[1]) * 1000 : null; };
export function readPower(run = execFileSync) {
  const one = name => { try { return parseKernTime(run('/usr/sbin/sysctl', ['-n', name], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })); } catch { return null; } };
  return { sleptAt: one('kern.sleeptime'), wokeAt: one('kern.waketime'), bootedAt: one('kern.boottime') };
}

export function explainGap({ fromMs, toMs, power = {} }) {
  const inside = ms => Number.isFinite(ms) && ms >= fromMs && ms <= toMs;
  if (inside(power.bootedAt)) return { cause: 'restart', bootedAt: power.bootedAt };
  const { sleptAt, wokeAt } = power;
  if (inside(sleptAt) && inside(wokeAt) && wokeAt >= sleptAt && sleptAt - fromMs < gapMinutes * minute && toMs - wokeAt < gapMinutes * minute) {
    return { cause: 'sleep', sleptAt, wokeAt };
  }
  return { cause: 'unknown' };
}

const hhmm = ms => { const t = vnNow(new Date(ms)); return `${String(t.hour).padStart(2, '0')}:${String(t.minute).padStart(2, '0')}`; };
const day = ms => { const t = vnNow(new Date(ms)); return `${t.date.slice(8)}.${t.date.slice(5, 7)}`; };
const known = path => (existsSync(path) ? readFileSync(path, 'utf8').split('\n').filter(Boolean).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean) : []);

// Called by the tick before it writes its own heartbeat. Returns the entry it wrote, or null.
export function noteTickGap({ nowMs = Date.now(), heartbeat = () => readJson(heartbeatPath(), null), power = () => readPower(), path = gapLogPath(),
  log = () => {}, alert = () => {} } = {}) {
  const fromMs = Date.parse(heartbeat()?.at ?? '');
  if (!Number.isFinite(fromMs) || nowMs - fromMs < gapMinutes * minute) return null;
  const from = new Date(fromMs).toISOString();
  // A tick that stops before its heartbeat (busy lock) would see the same gap again: one line per gap.
  if (known(path).some(e => e.from === from)) return null;
  const why = explainGap({ fromMs, toMs: nowMs, power: power() ?? {} });
  const entry = { from, to: new Date(nowMs).toISOString(), minutes: Math.round((nowMs - fromMs) / minute), ...why,
    ...(why.sleptAt ? { sleptAt: new Date(why.sleptAt).toISOString(), wokeAt: new Date(why.wokeAt).toISOString() } : {}),
    ...(why.bootedAt ? { bootedAt: new Date(why.bootedAt).toISOString() } : {}) };
  mkdirSync(dirname(path), { recursive: true });
  appendFileSync(path, `${JSON.stringify(entry)}\n`);
  const span = `${day(fromMs)} ${hhmm(fromMs)}–${hhmm(nowMs)} (${entry.minutes} phút)`;
  const text = why.cause === 'sleep' ? `tick ngừng ${span}: Mac ngủ ${hhmm(why.sleptAt)}–${hhmm(why.wokeAt)}`
    : why.cause === 'restart' ? `tick ngừng ${span}: Mac khởi động lại lúc ${hhmm(why.bootedAt)}`
      : `tick ngừng ${span}: không rõ nguyên nhân (Mac không ngủ, không khởi động lại trong khoảng này)`;
  log(text);
  if (why.cause === 'unknown') alert(`${text}. Xem logs/launchd.err và tick log quanh giờ đó.`);
  return entry;
}
