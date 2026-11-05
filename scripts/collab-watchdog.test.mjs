import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
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
  assert.deepEqual(run(t0 + H + 20 * 60000).alerted, []);
  // Fix D: a start with no done for over 30 minutes alerts before the 7-hour schedule limit.
  assert.deepEqual(run(t0 + 6 * H).alerted, ['la-lanh-ops-watch']);
  assert.deepEqual(run(t0 + 8 * H).alerted, []);
  assert.equal(alerts.length, 1); assert.equal(notes.length, 1);
  assert.match(alerts[0], /Kiểm tra server.*chưa xong: thường là đang chờ bấm "cho phép"[\s\S]*Scheduled/);
  beat('la-lanh-ops-watch', 'done', t0 + 9 * H);
  assert.deepEqual(run(t0 + 9 * H + 600000).stale, []);
  assert.deepEqual(run(t0 + 17 * H).alerted, ['la-lanh-ops-watch']);
  assert.match(alerts[1], /Không có lần chạy nào bắt đầu/);
});

test('a failed channel is retried on the next tick until it is delivered, then not again', () => {
  const t0 = ms('2026-11-05T03:00:00Z');
  for (const task of ['la-lanh-autopilot', 'la-lanh-ops-watch', 'la-lanh-retro']) beat(task, 'done', t0);
  let ghUp = false; let issues = 0; let notes = 0;
  const run = at => { beat('la-lanh-autopilot', 'done', at); return watch({ nowMs: at, alert: () => { if (!ghUp) throw new Error('gh down'); issues++; }, notify: () => { notes++; } }); };
  assert.doesNotThrow(() => run(t0 + 8 * H));
  assert.equal(issues, 0); assert.equal(notes, 1);
  run(t0 + 8 * H + 600000);
  assert.equal(issues, 0); assert.equal(notes, 1);
  ghUp = true;
  assert.deepEqual(run(t0 + 8 * H + 1200000).alerted, ['la-lanh-ops-watch']);
  assert.equal(issues, 1); assert.equal(notes, 1);
  assert.deepEqual(run(t0 + 8 * H + 1800000).alerted, []);
  assert.equal(issues, 1);
});

test('an autopilot stall alerted yesterday does not alert again after the overnight pause', () => {
  const t0 = ms('2026-11-06T03:00:00Z'); // 10:00 VN
  for (const task of ['la-lanh-autopilot', 'la-lanh-ops-watch', 'la-lanh-retro']) beat(task, 'done', t0);
  let count = 0;
  const run = at => { beat('la-lanh-ops-watch', 'done', at); beat('la-lanh-retro', 'done', at); return watch({ nowMs: at, alert: () => {}, notify: () => { count++; } }); };
  assert.deepEqual(run(t0 + 3 * H).alerted, ['la-lanh-autopilot']); // 13:00 VN
  assert.deepEqual(run(t0 + 20 * H).stale, []); // 06:00 VN next day: not watched
  assert.deepEqual(run(t0 + 25 * H + 600000).alerted, []); // 11:10 VN: same stall, no new alert
  assert.equal(count, 1);
  beat('la-lanh-autopilot', 'done', t0 + 26 * H);
  assert.deepEqual(run(t0 + 29 * H).alerted, ['la-lanh-autopilot']); // a new stall alerts again
});

test('a start beat written before the first tick still gets the full grace period', () => {
  const at = ms('2026-11-08T03:00:00Z');
  for (const task of ['la-lanh-autopilot', 'la-lanh-retro']) beat(task, 'done', at);
  rmSync(join(process.env.LA_LANH_COLLAB_HOME, 'beats', 'la-lanh-ops-watch.json'));
  beat('la-lanh-ops-watch', 'start', at);
  const alerts = [];
  assert.deepEqual(watch({ nowMs: at + 60000, alert: t => alerts.push(t), notify: () => {} }).stale, []);
  assert.equal(alerts.length, 0);
  assert.deepEqual(watch({ nowMs: at + 8 * H, alert: t => alerts.push(t), notify: () => {} }).alerted.includes('la-lanh-ops-watch'), true);
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

test('fix D: a start with no done for over 30 minutes is stuck, recorded and alerted, never killed', async () => {
  const { isRunning, isStuck, stuckMinutes } = await import('./collab-watchdog.mjs');
  const t0 = ms('2026-11-10T03:00:00Z'); // 10:00 VN, before autopilot's 11:00 watch window
  for (const task of ['la-lanh-autopilot', 'la-lanh-ops-watch', 'la-lanh-retro']) beat(task, 'done', t0);
  beat('la-lanh-autopilot', 'start', t0 + 60000);
  const alerts = [];
  const run = at => watch({ nowMs: at, alert: t => alerts.push(t), notify: () => {} });
  assert.deepEqual(run(t0 + 20 * 60000).stuck, [], '20 minutes is a normal run');
  assert.equal(isRunning(readBeats(t0)['la-lanh-autopilot']), true);
  const result = run(t0 + (stuckMinutes + 2) * 60000);
  assert.deepEqual(result.stuck, ['la-lanh-autopilot']);
  assert.deepEqual(result.alerted, ['la-lanh-autopilot'], 'stuck alerts even before the 120-minute limit and the 11:00 window');
  assert.match(alerts[0], /chưa xong: thường là đang chờ bấm "cho phép"/);
  const b = readBeats(t0)['la-lanh-autopilot'];
  assert.ok(b.stuckAt, 'a stuck beat is recorded');
  assert.equal(isRunning(b), false, 'the next run is not blocked by the stuck one');
  assert.equal(isStuck(b, t0 + 3 * H), false, 'recorded once');
  assert.deepEqual(run(t0 + 40 * 60000).alerted, [], 'one alert per episode, as today');
  beat('la-lanh-autopilot', 'start', t0 + 50 * 60000);
  assert.equal(isRunning(readBeats(t0)['la-lanh-autopilot']), true, 'a new start counts as running again');
  assert.throws(() => beat('la-lanh-retro', 'later'), /start, done or stuck/);
  const src = (await import('node:fs')).readFileSync(new URL('./collab-watchdog.mjs', import.meta.url), 'utf8');
  assert.doesNotMatch(src, /process\.kill|\bkill\b|chmod|launchctl/, 'the watchdog never kills processes or edits permissions');
});

// Self-heal fixes (05.11.2026): stale preflight record, auto-sync before the check, process-tree kill.
const heal = await import('./collab-heal.mjs');
const preflightMod = await import('./collab-preflight.mjs');
const { spawnSync: spawnPlain } = await import('node:child_process');
const await_fs = await import('node:fs');
const { readFileSync: readText } = await_fs;
const SHA = 'a'.repeat(40);

test('self-heal 1: editing the PR body (same head) clears a body preflight failure', () => {
  const pr = { number: 501, headRefOid: SHA, body: 'old body' };
  const fail = preflightMod.runPreflight(pr);
  assert.equal(fail.status, 'FAIL');
  preflightMod.recordPreflight(501, SHA, fail);
  assert.ok(preflightMod.preflightFailure(preflightMod.readPreflight(), pr), 'same head and body: still failing');
  assert.equal(preflightMod.preflightFailure(preflightMod.readPreflight(), { ...pr, body: 'fixed body' }), null, 'edited body is re-checked');
  preflightMod.recordPreflight(502, SHA, { status: 'FAIL', reasons: ['ruff lỗi: x'] });
  assert.ok(preflightMod.preflightFailure(preflightMod.readPreflight(), { number: 502, headRefOid: SHA, body: 'any' }), 'lint record stays keyed by head');
});

const fakeGit = ({ behind, conflict }) => {
  const calls = [];
  const git = args => {
    calls.push(args.filter(a => !a.startsWith('user.') && a !== '-c').join(' '));
    if (args[0] === 'merge-base' && behind) throw new Error('not ancestor');
    if (args.includes('merge') && !args.includes('--abort') && conflict) throw new Error('CONFLICT');
    return args[0] === 'rev-parse' ? 'b'.repeat(40) : '';
  };
  return { git, calls };
};

test('self-heal 2: a branch behind integration that merges cleanly is merged, pushed and rechecked', () => {
  const posted = [];
  const gh = { comment: (...a) => posted.push(a) };
  const { git, calls } = fakeGit({ behind: true });
  const result = heal.syncWithIntegration({ number: 9, headRefName: 'agent/claude/x' }, { git, gh });
  assert.equal(result.status, 'synced');
  assert.ok(calls.includes('push origin HEAD:refs/heads/agent/claude/x'));
  assert.ok(!calls.some(c => /--force|-f\b/.test(c)), 'never a force push');
  assert.match(posted[0][2], /<!-- la-lanh-agent handoff -->$/);
  const up = fakeGit({ behind: false });
  assert.equal(heal.syncWithIntegration({ number: 9, headRefName: 'agent/claude/x' }, { git: up.git, gh }), null, 'up to date: nothing');
  assert.equal(heal.syncWithIntegration({ number: 9, headRefName: 'feat/x' }, { git: fakeGit({ behind: true }).git, gh }), null, 'only agent branches');
  const bad = fakeGit({ behind: true, conflict: true });
  assert.deepEqual(heal.syncWithIntegration({ number: 9, headRefName: 'agent/codex/y' }, { git: bad.git, gh }), { status: 'conflict', turn: 'claude-fix', reason: 'xung đột với collab/integration' });
  assert.ok(bad.calls.includes('merge --abort') && !bad.calls.some(c => c.startsWith('push')), 'conflict: abort, push nothing');
  assert.equal(posted.length, 1);
});

test('self-heal 3: a timed step kills a grandchild and a step past the stuck limit writes a beat and alerts', () => {
  const marker = `${50 + (process.pid % 7)}.${Date.now() % 100000}`;
  const alerts = [];
  // The child spawns a sleeping grandchild in the background, then sleeps itself.
  const started = Date.now();
  const result = heal.runGroup('/bin/sh', ['-c', `(sleep ${marker} &) ; sleep ${marker}`], { timeoutMs: 1500, graceMs: 500, stdio: 'ignore', stuckMs: 300, alert: t => alerts.push(t) });
  assert.equal(result.status, 124);
  assert.ok(Date.now() - started < 10000);
  assert.equal(spawnPlain('pgrep', ['-f', `^sleep ${marker}`], { encoding: 'utf8' }).stdout.trim(), '', 'no grandchild survives');
  const b = JSON.parse(readText(heal.stepBeatPath(), 'utf8'));
  assert.ok(b.stuckAt && b.doneAt, 'stuck beat written and closed');
  assert.equal(alerts.length, 1);
  assert.match(alerts[0], /quá 30 phút/);
  const quick = heal.runGroup('/bin/sh', ['-c', 'exit 0'], { timeoutMs: 5000, stdio: 'ignore', alert: t => alerts.push(t) });
  assert.equal(quick.status, 0);
  assert.equal(alerts.length, 1, 'a quick step does not alert');
  assert.throws(() => heal.groupExec('/bin/sh', ['-c', 'sleep 5'], { timeout: 1000 }), /hết giờ/);
});

test('self-heal 2 r2 (P1): auto-sync is bounded by the deadline with a fake clock that advances', () => {
  let clock = 0;
  const steps = [];
  // Each git step uses its whole budget.
  const git = (args, ms) => { steps.push({ args: args.join(' '), ms, left: 200000 - clock }); clock += ms; if (args[0] === 'merge-base') throw new Error('behind'); return args[0] === 'rev-parse' ? 'b'.repeat(40) : ''; };
  const posted = [];
  const result = heal.syncWithIntegration({ number: 9, headRefName: 'agent/claude/x' }, { git, gh: { comment: (...a) => posted.push(a) }, left: () => 200000 - clock });
  assert.equal(result.status, 'refused');
  assert.ok(steps.filter(s => !s.args.includes('--abort')).every(s => s.ms <= s.left && s.ms > 0), 'no step runs past the deadline');
  assert.ok(!steps.some(s => s.args.startsWith('push')) || steps.find(s => s.args.startsWith('push')).ms <= steps.find(s => s.args.startsWith('push')).left);
  assert.deepEqual(posted, [], 'no comment once the deadline is spent');
  const none = [];
  assert.equal(heal.syncWithIntegration({ number: 9, headRefName: 'agent/claude/x' }, { git: a => { none.push(a); return ''; }, gh: {}, left: () => 0 }).status, 'refused');
  assert.deepEqual(none, [], 'nothing starts after the deadline');
});

test('self-heal 1 r2 (P2): a legacy body record is re-evaluated; the clone path keeps the body hash', async () => {
  const pr = { number: 503, headRefOid: SHA, body: 'x' };
  preflightMod.recordPreflight(503, SHA, { status: 'FAIL', reasons: ['PR body thiếu mức rủi ro S/M/L'] });
  assert.equal(preflightMod.preflightFailure(preflightMod.readPreflight(), pr), null, 'legacy body record without hash is stale');
  const { runCheckInClone } = await import('./collab-check.mjs');
  const fakePr = { number: 504, author: { login: 'honghanh153-creator' }, isCrossRepository: false, headRefName: 'feat/x', headRefOid: SHA, body: 'b', comments: [] };
  const result = runCheckInClone(504, { gh: { pr: () => fakePr, comment: () => {} }, run: (c, a) => a[0] === 'rev-parse' ? SHA : '', group: () => ({ status: 0 }), busy: () => null, terms: () => [],
    preflight: p => preflightMod.runPreflight(p), spawn: () => { throw new Error('no pnpm'); } });
  assert.equal(result.status, 'preflight');
  assert.equal(result.bodyHash, heal.bodyHash('b'), 'body hash carried through the clone check');
});

test('self-heal 3 r3 (P1): a stuck step queues its alert; delivery obeys an advancing deadline', () => {
  for (const { path } of heal.pendingAlerts()) rmSync(path);
  // Default alert: nothing sent inline, the alert is queued and the stuck beat is still written.
  const r = heal.runGroup('/bin/sh', ['-c', 'sleep 1'], { timeoutMs: 5000, stuckMs: 200, stdio: 'ignore' });
  assert.equal(r.status, 0);
  assert.ok(JSON.parse(readText(heal.stepBeatPath(), 'utf8')).stuckAt, 'stuck beat written at once');
  heal.queueAlert('second');
  assert.equal(heal.pendingAlerts().length, 2);
  // Fake clock: each gh call takes its full 60 s; the deadline allows only one.
  let clock = 0;
  const sent = [];
  const out = heal.deliverPendingAlerts({ alert: t => { sent.push(t); clock += 60000; }, left: () => 100000 - clock });
  assert.deepEqual(out, { sent: 1, left: 1 });
  assert.match(sent[0], /quá 30 phút/);
  // The watchdog's next run delivers the rest.
  const later = [];
  const w = watch({ nowMs: Date.now(), alert: t => later.push(t), notify: () => {} });
  assert.equal(w.queued.sent, 1);
  assert.ok(later.includes('second'));
  assert.deepEqual(heal.pendingAlerts(), []);
});

test('#241: an alert queued while a delivery runs survives it', () => {
  for (const { path } of heal.pendingAlerts()) rmSync(path);
  heal.queueAlert('A');
  const sent = [];
  const out = heal.deliverPendingAlerts({ alert: t => { sent.push(t); heal.queueAlert('B'); } });
  assert.deepEqual(out, { sent: 1, left: 0 });
  assert.deepEqual(sent, ['A']);
  assert.deepEqual(heal.pendingAlerts().map(e => e.item.text), ['B'], 'B queued during delivery is kept');
  heal.deliverPendingAlerts({ alert: () => {} });
  assert.deepEqual(heal.pendingAlerts(), []);
});

// Deadline on every call (05.11.2026): gh, post-clone git and review git follow the time left.
const trustMod = await import('./collab-trust.mjs');
const codexMod = await import('./codex-review.mjs');

test('deadline: gh calls are bounded by the time left and stop once it is spent', () => {
  let clock = 0;
  const timeouts = [];
  const gh = trustMod.makeGh((cmd, args, opts) => { timeouts.push(opts.timeout); clock += 50000; return '{}'; }, { left: () => 100000 - clock });
  gh.raw(['a']); gh.raw(['b']);
  assert.deepEqual(timeouts, [60000, 50000]);
  assert.throws(() => gh.raw(['c']), trustMod.DeadlineError);
  assert.equal(timeouts.length, 2, 'nothing starts after the deadline');
  const later = gh.withDeadline(() => 30000);
  later.raw(['d']);
  assert.equal(timeouts.at(-1), 30000);
});

test('deadline: git after the author clone follows the same deadline', async () => {
  const { runCheckInClone, cleanupReserveMs } = await import('./collab-check.mjs');
  let clock = 0;
  const seen = [];
  const deadline = 26 * 60000;
  // Each git call takes 2 minutes of the fake clock.
  const run = (cmd, args, opts) => { seen.push({ args: args.join(' '), timeout: opts.timeout, left: deadline - cleanupReserveMs - clock }); clock += 2 * 60000; return args[0] === "rev-parse" ? SHA : ''; };
  const fakePr = { number: 505, author: { login: 'honghanh153-creator' }, isCrossRepository: false, headRefName: 'feat/x', headRefOid: SHA, body: 'b', comments: [], files: [] };
  runCheckInClone(505, { gh: { pr: () => fakePr, comment: () => {} }, run, auto: true, clock: () => ({ date: 'd', hour: 23, minute: 29 }), nowMs: () => clock, group: () => ({ status: 0 }), busy: () => null, terms: () => [], preflight: () => ({ status: 'PASS' }), spawn: () => ({ status: 0 }) });
  const after = seen.slice(seen.findIndex(s => s.args === 'rev-parse HEAD') + 1);
  assert.ok(after.length >= 1, 'git ran after the clone');
  assert.ok(after.every(s => s.timeout <= s.left), `post-clone git past the deadline: ${JSON.stringify(after)}`);
});

test('deadline: the review clone git calls follow the time left', () => {
  let clock = 0;
  const seen = [];
  const run = (cmd, args, opts) => { seen.push({ timeout: opts.timeout, left: 400000 - clock }); clock += 200000; return args[0] === 'rev-parse' ? SHA : ''; };
  assert.throws(() => codexMod.prepareClone(506, SHA, run, () => 400000 - clock), trustMod.DeadlineError);
  assert.ok(seen.every(s => s.timeout <= s.left), JSON.stringify(seen));
  assert.deepEqual(seen.map(s => s.timeout).slice(0, 2), [300000, 200000]);
});
