import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-watchdog-'));
const { beat, describeStale, healthLines, readBeats, staleTasks, watch } = await import('./collab-watchdog.mjs');
const { tick } = await import('./collab-turn.mjs');

const ms = iso => Date.parse(iso);
const vn = (hour, minute = 0) => ({ date: '2026-11-03', hour, minute });
const H = 3600000;

test('a run that started and never finished is reported as waiting on a prompt', () => {
  const beats = { 'la-lanh-autopilot': { doneAt: '2026-10-31T11:00:00Z', startedAt: '2026-10-31T12:48:00Z' }, 'la-lanh-ops-watch': { doneAt: '2026-11-03T01:00:00Z' }, 'la-lanh-retro': { doneAt: '2026-11-02T16:40:00Z' } };
  const stale = staleTasks(beats, ms('2026-11-03T05:00:00Z'), vn(12));
  assert.deepEqual(stale.map(s => s.task), ['la-lanh-autopilot']);
  assert.equal(stale[0].stuckSince, '2026-10-31T12:48:00.000Z');
  assert.match(describeStale(stale[0]), /31\.10 19:48 chưa xong: thường là đang chờ bấm "cho phép"/);
});

test('autopilot is not stale overnight or before 11:00, other tasks are watched all day', () => {
  const beats = { 'la-lanh-autopilot': { doneAt: '2026-11-02T16:40:00Z' }, 'la-lanh-ops-watch': { doneAt: '2026-11-02T14:00:00Z' }, 'la-lanh-retro': { doneAt: '2026-11-02T16:40:00Z' } };
  assert.deepEqual(staleTasks(beats, ms('2026-11-02T22:00:00Z'), vn(5)).map(s => s.task), ['la-lanh-ops-watch']);
  assert.deepEqual(staleTasks(beats, ms('2026-11-03T03:30:00Z'), vn(10, 30)).map(s => s.task), ['la-lanh-ops-watch']);
  assert.deepEqual(staleTasks(beats, ms('2026-11-03T04:10:00Z'), vn(11, 10)).map(s => s.task), ['la-lanh-autopilot', 'la-lanh-ops-watch']);
});

test('the retro is stale only after a missed 23:35 run (26 hours)', () => {
  const beats = { 'la-lanh-autopilot': { doneAt: '2026-11-03T03:00:00Z' }, 'la-lanh-ops-watch': { doneAt: '2026-11-03T03:00:00Z' }, 'la-lanh-retro': { doneAt: '2026-11-01T16:40:00Z' } };
  assert.deepEqual(staleTasks(beats, ms('2026-11-02T18:00:00Z'), vn(1)).map(s => s.task), []);
  assert.deepEqual(staleTasks(beats, ms('2026-11-02T19:00:00Z'), vn(2)).map(s => s.task), ['la-lanh-retro']);
});

test('installing the watchdog starts each clock at first sight instead of alerting at once', () => {
  const now = ms('2026-11-03T03:00:00Z');
  const alerts = [];
  assert.deepEqual(watch({ nowMs: now, alert: t => alerts.push(t), notify: () => {} }).stale, []);
  assert.equal(alerts.length, 0);
  assert.ok(readBeats(now)['la-lanh-ops-watch'].baselineAt);
});

test('one alert and one notification per stall; a done beat ends it and the next stall alerts again', () => {
  const t0 = ms('2026-11-03T03:00:00Z');
  for (const task of ['la-lanh-autopilot', 'la-lanh-ops-watch', 'la-lanh-retro']) beat(task, 'done', t0);
  beat('la-lanh-ops-watch', 'start', t0 + H);
  const alerts = []; const notes = [];
  // Autopilot keeps finishing every hour, so only the server check can go late here.
  const run = at => { beat('la-lanh-autopilot', 'done', at); return watch({ nowMs: at, alert: t => alerts.push(t), notify: t => notes.push(t) }); };
  assert.deepEqual(run(t0 + 6 * H).alerted, []);
  assert.deepEqual(run(t0 + 8 * H).alerted, ['la-lanh-ops-watch']);
  assert.deepEqual(run(t0 + 8 * H + 600000).alerted, []);
  assert.equal(alerts.length, 1); assert.equal(notes.length, 1);
  assert.match(alerts[0], /Kiểm tra server.*chưa xong: thường là đang chờ bấm "cho phép"[\s\S]*Scheduled/);
  beat('la-lanh-ops-watch', 'done', t0 + 9 * H);
  assert.deepEqual(run(t0 + 9 * H + 600000).stale, []);
  assert.deepEqual(run(t0 + 17 * H).alerted, ['la-lanh-ops-watch']);
  assert.match(alerts[1], /Không có lần chạy nào bắt đầu/);
});

test('a failing notifier or alert never stops the watchdog, and beats reject unknown names', () => {
  assert.doesNotThrow(() => watch({ nowMs: ms('2026-11-05T05:00:00Z'), alert: () => { throw new Error('gh down'); }, notify: () => { throw new Error('no osascript'); } }));
  assert.throws(() => beat('rm -rf', 'done'), /unknown task/);
  assert.throws(() => beat('la-lanh-retro', 'later'), /phase/);
});

test('health lines mark late tasks for the morning plan', () => {
  const beats = { 'la-lanh-autopilot': { doneAt: '2026-11-02T16:40:00Z' }, 'la-lanh-ops-watch': { doneAt: '2026-10-26T15:30:00Z' }, 'la-lanh-retro': {} };
  const lines = healthLines(beats, ms('2026-11-03T01:50:00Z'), vn(8, 50));
  assert.equal(lines[0], '- ✅ Autopilot (mỗi giờ): xong lần cuối 02.11 23:40');
  assert.equal(lines[1], '- ⚠️ Kiểm tra server (6 giờ/lần): xong lần cuối 26.10 22:30');
  assert.match(lines[2], /⚠️ Báo cáo cuối ngày.*chưa báo xong lần nào/);
});

test('the tick runs the watchdog even when the plan is closed, and a watchdog error does not break it', () => {
  let ran = 0;
  const gh = { json: () => [{ number: 1, title: 'Kế hoạch chạy tự động hằng ngày' }], raw: () => '', comment: () => '', openPrs: () => [] };
  const night = { date: '2026-11-03', hour: 4, minute: 20 };
  assert.equal(tick({ gh, now: night, watchdog: () => { ran++; } }).status, 'closed');
  assert.equal(tick({ gh, now: night, watchdog: () => { ran++; throw new Error('boom'); } }).status, 'closed');
  assert.equal(ran, 2);
});
