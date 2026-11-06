// Missed-run alert for the Claude desktop scheduled tasks (owner 06.11.2026). On 03.11–05.11 the
// autopilot, server check and 23:35 retro skipped runs and nobody noticed: the watchdog wrote local
// beats only. Here a scheduled slot with no done beat by slot + jitter + 30 minutes is a miss. One
// miss raises one alert per channel: a local notification and one ops-alert issue per task per
// day. An email through Mail.app when a local address file exists. launchd cannot start a Claude
// scheduled task, so the alert asks the owner to open Claude and run it again.
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { clean, readJson, stateDir, vnNow, writeJson } from './collab-trust.mjs';

export const graceMinutes = 30;
const repo = 'honghanh153-creator/la-lanh';
const hourMs = 3600000;
const vnOffsetMs = 7 * hourMs; // Asia/Ho_Chi_Minh has no daylight saving.

// Times are Vietnam time, same as the Claude scheduled-task cron. jitterMinutes covers Claude's
// start jitter (autopilot up to ~11 minutes).
export const schedules = {
  'la-lanh-autopilot': { label: 'Autopilot (mỗi giờ, :37 từ 9 đến 23 giờ)', minute: 37, hours: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23], jitterMinutes: 12 },
  'la-lanh-ops-watch': { label: 'Kiểm tra server (4:20, 10:20, 16:20, 22:20)', minute: 20, hours: [4, 10, 16, 22], jitterMinutes: 8 },
  'la-lanh-retro': { label: 'Báo cáo cuối ngày (23:35)', minute: 35, hours: [23], jitterMinutes: 2 },
};

const ms = v => Date.parse(v ?? 0) || 0;
const vnDate = t => vnNow(new Date(t)).date;
const slotMs = (date, hour, minute) => Date.parse(`${date}T${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00Z`) - vnOffsetMs;
const hhmm = t => { const v = vnNow(new Date(t)); return `${v.date.slice(8)}.${v.date.slice(5, 7)} ${String(v.hour).padStart(2, '0')}:${String(v.minute).padStart(2, '0')}`; };

// The newest slot whose deadline (slot + jitter + grace) has passed, or null.
export function lastDueSlot(rule, nowMs) {
  const wait = (rule.jitterMinutes + graceMinutes) * 60000;
  for (const back of [0, 1]) {
    const date = vnDate(nowMs - back * 24 * hourMs);
    const due = rule.hours.map(h => slotMs(date, h, rule.minute)).filter(s => s + wait <= nowMs);
    if (due.length) return Math.max(...due);
  }
  return null;
}

// A miss: the last due slot has no done beat at or after it (5 minutes early allowed for clock
// skew). Slots before the watchdog first saw a task (baselineAt) are not misses.
export function missedRuns(beats, nowMs = Date.now()) {
  return Object.entries(schedules).flatMap(([task, rule]) => {
    const slot = lastDueSlot(rule, nowMs);
    if (slot === null) return [];
    const b = beats[task] ?? {};
    if (ms(b.doneAt) >= slot - 5 * 60000) return [];
    if (!b.doneAt && ms(b.baselineAt) > slot) return [];
    return [{ task, label: rule.label, slot: new Date(slot).toISOString(), day: vnDate(slot), lastDoneAt: b.doneAt ?? null }];
  });
}

export function describeMiss(m) {
  const last = m.lastDoneAt ? `lần xong cuối ${hhmm(ms(m.lastDoneAt))}` : 'chưa có lần nào báo xong';
  return `${m.label}: lượt ${hhmm(ms(m.slot))} không chạy xong (${last}). Mở Claude để chạy bù.`;
}

export const issueTitle = m => `[ops-alert] lỡ lượt chạy ${m.task} ${m.day}`;

// gh helpers with fixed argv; `run(args, input)` returns stdout.
export function ghIssues(run) {
  return {
    find: title => JSON.parse(run(['issue', 'list', '--repo', repo, '--label', 'ops-alert', '--state', 'open', '--search', `"${title}" in:title`, '--json', 'number,title', '--limit', '20']) || '[]').find(i => i.title === title)?.number ?? null,
    create: (title, body) => {
      run(['label', 'create', 'ops-alert', '--repo', repo, '--color', 'B60205', '--force']);
      const url = run(['issue', 'create', '--repo', repo, '--title', title, '--label', 'ops-alert', '--body-file', '-'], body);
      return Number(String(url).trim().split('/').pop()) || null;
    },
    comment: (number, body) => run(['issue', 'comment', String(number), '--repo', repo, '--body-file', '-'], body),
  };
}

const osNotify = text => execFileSync('/usr/bin/osascript', ['-e', `display notification ${JSON.stringify(clean(text, 200))} with title "Lá Lành: tác vụ hẹn giờ lỡ lượt"`], { stdio: 'ignore', timeout: 10000 });
const statePath = () => join(stateDir, 'beats', 'missed-alerts.json');

// Email (owner 06.11.2026) goes through the Mac's own Mail.app. The address lives only in a local
// file outside git (stateDir/alert-email, one line); the repo is public, so it is never in code.
// No file or an empty one disables the channel. Values reach AppleScript as argv, never as code.
export const alertEmailPath = () => join(stateDir, 'alert-email');
export function readAlertEmail(read = p => readFileSync(p, 'utf8')) {
  try { const v = String(read(alertEmailPath())).split('\n')[0].trim(); return /^[^\s@]+@[^\s@]+$/.test(v) ? v : null; } catch { return null; }
}
const mailScript = [
  'on run argv',
  'tell application "Mail"',
  'set m to make new outgoing message with properties {subject:item 2 of argv, content:item 3 of argv, visible:false}',
  'tell m to make new to recipient at end of to recipients with properties {address:item 1 of argv}',
  'send m',
  'end tell',
  'end run',
];
export const emailSubject = m => `Lá Lành: ${m.task} lỡ lượt ${hhmm(ms(m.slot))}`;
export function emailChannel({ address = readAlertEmail(), run = execFileSync } = {}) {
  if (!address) return null;
  return m => run('/usr/bin/osascript', [...mailScript.flatMap(line => ['-e', line]), address, emailSubject(m), clean(m.text, 1000)], { stdio: 'ignore', timeout: 20000 });
}

// Delivery channels are pluggable: each is `send(miss, state)` or null (disabled).
export function defaultChannels(issues, notify = osNotify, email = emailChannel()) {
  return {
    notify: m => notify(m.text),
    issue: (m, state) => {
      const dayKey = `${m.task}@${m.day}`;
      const body = `${m.text}\n\nLaunchd không tự chạy lại được tác vụ hẹn giờ của Claude: mở Claude → Scheduled → tác vụ này → Run now.\n\n<!-- la-lanh-agent ops-alert -->`;
      const number = state.issues[dayKey] ?? issues.find(issueTitle(m));
      if (number) issues.comment(number, body); else state.issues[dayKey] = issues.create(issueTitle(m), body);
      if (number) state.issues[dayKey] = number;
    },
    email,
  };
}

export const expireMs = 48 * hourMs;

// Each missed slot is stored with its payload. Every tick retries each enabled channel that has
// not delivered, for every stored slot, even after the task has run again, until delivered or 48h
// old. One miss gives one alert per channel; the first miss of a day opens the task's issue, later
// misses that day comment on it.
export function alertMissed({ beats, nowMs = Date.now(), channels, issues, notify = osNotify, load = () => readJson(statePath(), {}), save = s => writeJson(statePath(), s) }) {
  const send = channels ?? defaultChannels(issues, notify);
  const enabled = Object.keys(send).filter(name => typeof send[name] === 'function');
  const state = load();
  state.slots ??= {}; state.issues ??= {};
  for (const m of missedRuns(beats, nowMs)) {
    const key = `${m.task}@${m.slot}`;
    state.slots[key] ??= { miss: { ...m, text: describeMiss(m) }, delivered: {} };
  }
  const delivered = [];
  for (const [key, entry] of Object.entries(state.slots)) {
    if (nowMs - ms(entry.miss?.slot) > expireMs) { delete state.slots[key]; continue; }
    entry.delivered ??= {};
    for (const name of enabled) {
      if (entry.delivered[name]) continue;
      try { send[name](entry.miss, state); entry.delivered[name] = new Date(nowMs).toISOString(); delivered.push(`${key}:${name}`); } catch {}
    }
  }
  for (const k of Object.keys(state.issues)) if (k.split('@')[1] < vnDate(nowMs - expireMs)) delete state.issues[k];
  save(state);
  return delivered;
}
