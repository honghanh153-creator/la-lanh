import assert from 'node:assert/strict';
import test from 'node:test';
import { alertMissed, defaultChannels, emailChannel, missedRuns, readAlertEmail } from './collab-missed-run.mjs';

const vn = s => Date.parse(`${s}+07:00`);
const fakeIssues = () => {
  const log = [];
  return { log, find: () => null, create: (title, body) => { log.push({ op: 'create', title, body }); return 301; }, comment: (n, body) => log.push({ op: 'comment', n, body }) };
};
const mem = () => { let s = {}; return { load: () => JSON.parse(JSON.stringify(s)), save: v => { s = v; } }; };
const fresh = { 'la-lanh-ops-watch': { doneAt: new Date(vn('2026-11-05T10:25:00')).toISOString() }, 'la-lanh-retro': { doneAt: new Date(vn('2026-11-04T23:40:00')).toISOString() } };

test('autopilot slot without done beat is a miss only after jitter + 30 min grace', () => {
  const beats = { ...fresh, 'la-lanh-autopilot': { doneAt: new Date(vn('2026-11-05T09:45:00')).toISOString() } };
  assert.deepEqual(missedRuns(beats, vn('2026-11-05T11:10:00')).map(m => m.task), []);
  assert.deepEqual(missedRuns(beats, vn('2026-11-05T11:20:00')).map(m => m.task), ['la-lanh-autopilot']);
});

test('overnight gap is not an autopilot miss; retro missed at 23:35 is', () => {
  const beats = { ...fresh, 'la-lanh-autopilot': { doneAt: new Date(vn('2026-11-04T23:45:00')).toISOString() }, 'la-lanh-retro': { doneAt: new Date(vn('2026-11-03T23:40:00')).toISOString() } };
  const misses = missedRuns(beats, vn('2026-11-05T09:00:00'));
  assert.deepEqual(misses.map(m => m.task), ['la-lanh-retro']);
  assert.equal(misses[0].day, '2026-11-04');
});

test('slots before the watchdog first saw a task are not misses', () => {
  const beats = { ...fresh, 'la-lanh-autopilot': { baselineAt: new Date(vn('2026-11-05T10:50:00')).toISOString() } };
  assert.deepEqual(missedRuns(beats, vn('2026-11-05T11:00:00')), []);
});

test('one miss gives one alert; second miss same day comments on the same issue', () => {
  const issues = fakeIssues(); const store = mem(); const notes = [];
  const beats = { ...fresh, 'la-lanh-autopilot': { doneAt: new Date(vn('2026-11-05T09:45:00')).toISOString() } };
  const run = t => alertMissed({ beats, nowMs: vn(t), issues, notify: x => notes.push(x), ...store });
  run('2026-11-05T11:20:00'); run('2026-11-05T11:30:00');
  assert.equal(issues.log.length, 1); assert.equal(notes.length, 1);
  assert.equal(issues.log[0].op, 'create');
  assert.doesNotMatch(issues.log[0].body, /@honghanh/);
  assert.match(issues.log[0].body, /Mở Claude để chạy bù/);
  run('2026-11-05T12:20:00');
  assert.deepEqual(issues.log.map(l => l.op), ['create', 'comment']);
  assert.equal(issues.log[1].n, 301);
  assert.equal(notes.length, 2);
});

test('a failed issue call retries next tick without a second notification', () => {
  const store = mem(); const notes = []; let fail = true; const log = [];
  const issues = { find: () => null, create: () => { if (fail) throw new Error('offline'); log.push('create'); return 9; }, comment: () => {} };
  const beats = { ...fresh, 'la-lanh-autopilot': { doneAt: new Date(vn('2026-11-05T09:45:00')).toISOString() } };
  alertMissed({ beats, nowMs: vn('2026-11-05T11:20:00'), issues, notify: x => notes.push(x), ...store });
  fail = false;
  alertMissed({ beats, nowMs: vn('2026-11-05T11:30:00'), issues, notify: x => notes.push(x), ...store });
  assert.deepEqual(log, ['create']); assert.equal(notes.length, 1);
});

test('a done beat after the slot clears the miss', () => {
  const beats = { ...fresh, 'la-lanh-autopilot': { doneAt: new Date(vn('2026-11-05T10:45:00')).toISOString() } };
  assert.deepEqual(missedRuns(beats, vn('2026-11-05T11:20:00')), []);
});

test('undelivered issue retries after the task ran again (fails 11:20, done 11:25, GitHub back 11:30)', () => {
  const store = mem(); const notes = []; let fail = true; const log = [];
  const issues = { find: () => null, create: () => { if (fail) throw new Error('offline'); log.push('create'); return 9; }, comment: () => {} };
  const beats = { ...fresh, 'la-lanh-autopilot': { doneAt: new Date(vn('2026-11-05T09:45:00')).toISOString() } };
  alertMissed({ beats, nowMs: vn('2026-11-05T11:20:00'), issues, notify: x => notes.push(x), ...store });
  beats['la-lanh-autopilot'] = { doneAt: new Date(vn('2026-11-05T11:25:00')).toISOString() };
  fail = false;
  alertMissed({ beats, nowMs: vn('2026-11-05T11:30:00'), issues, notify: x => notes.push(x), ...store });
  assert.deepEqual(log, ['create']); assert.equal(notes.length, 1);
});

test('stored misses expire after 48h undelivered', () => {
  const store = mem();
  const issues = { find: () => null, create: () => { throw new Error('offline'); }, comment: () => {} };
  const beats = { ...fresh, 'la-lanh-autopilot': { doneAt: new Date(vn('2026-11-05T09:45:00')).toISOString() } };
  alertMissed({ beats, nowMs: vn('2026-11-05T11:20:00'), issues, notify: () => {}, ...store });
  const later = { ...fresh, 'la-lanh-autopilot': { doneAt: new Date(vn('2026-11-07T12:45:00')).toISOString() }, 'la-lanh-ops-watch': { doneAt: new Date(vn('2026-11-07T10:30:00')).toISOString() }, 'la-lanh-retro': { doneAt: new Date(vn('2026-11-06T23:40:00')).toISOString() } };
  alertMissed({ beats: later, nowMs: vn('2026-11-07T13:00:00'), issues, notify: () => {}, ...store });
  assert.deepEqual(Object.keys(store.load().slots), []);
});

test('email channel is off without a local address file and sends once per miss through osascript argv', () => {
  assert.equal(readAlertEmail(() => { throw new Error('ENOENT'); }), null);
  assert.equal(readAlertEmail(() => '\n'), null);
  assert.equal(emailChannel({ address: null }), null);
  assert.equal(defaultChannels({}, () => {}, null).email, null);
  const calls = []; const store = mem();
  const email = emailChannel({ address: 'owner@example.test', run: (cmd, args, opts) => calls.push({ cmd, args, opts }) });
  const beats = { ...fresh, 'la-lanh-autopilot': { doneAt: new Date(vn('2026-11-05T09:45:00')).toISOString() } };
  const channels = { email, off: null };
  alertMissed({ beats, nowMs: vn('2026-11-05T11:20:00'), channels, ...store });
  alertMissed({ beats, nowMs: vn('2026-11-05T11:30:00'), channels, ...store });
  assert.equal(calls.length, 1);
  const { cmd, args, opts } = calls[0];
  assert.equal(cmd, '/usr/bin/osascript');
  assert.ok(opts.timeout <= 20000);
  const tail = args.slice(-3);
  assert.equal(tail[0], 'owner@example.test');
  assert.equal(tail[1], 'Lá Lành: la-lanh-autopilot lỡ lượt 05.11 10:37');
  assert.match(tail[2], /Mở Claude để chạy bù/);
  assert.ok(!args.slice(0, -3).join(' ').includes('owner@example.test'));
});
