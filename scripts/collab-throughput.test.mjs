import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'throughput-'));
const { agentMarker } = await import('./collab-trust.mjs');
const { ctxOf, scanFile, splitShares, triggerOf } = await import('./collab-usage.mjs');
const { antigravityFirstPass, claudeBudget, codexFirstPass, goVuongPath, readGoVuong, throughputLines, throughputTick } = await import('./collab-throughput.mjs');

const NOW = new Date('2026-11-22T08:00:00Z'); // 15:00 in Vietnam
const A = 'a'.repeat(40);
const B = 'b'.repeat(40);
const verdict = (v, sha) => ({ authorAssociation: 'OWNER', body: `Review verdict: ${v} @ ${sha}\nReviewer: Codex`, createdAt: '2026-11-22T07:00:00Z', url: 'u' });

test('L72: the daily budget is what is left above the 5% reserve, spread over the days to the reset', () => {
  const usage = { percent: 80, dayStart: { day: '2026-11-22', percent: 74 } };
  const b = claudeBudget(usage, { resetsAt: '2026-11-25T08:00:00Z', now: NOW });
  assert.equal(b.today, 6);
  assert.equal(b.daily, 5, '(100 − 5 − 80) ÷ 3 days');
  assert.equal(claudeBudget(usage, { now: NOW }).daily, null, 'no reset time: unknown, never a guess');
  assert.equal(claudeBudget(usage, { resetsAt: '2026-11-22T12:00:00Z', now: NOW }).daily, 15, 'less than a day left counts as one day');
  assert.equal(claudeBudget({ percent: 80, dayStart: { day: '2026-11-21', percent: 70 } }, { now: NOW }).today, null, 'yesterday\'s start is not today');
});

test('L72: first pass: a Codex fix passes with no later fix and no change request on its head; Antigravity passes when counted', () => {
  const runs = [{ pr: 1, head: A }, { pr: 1, head: B }, { pr: 2, head: A }, { pr: 3, head: A }, { pr: 4, head: A }];
  const open = [
    { number: 1, headRefOid: B, comments: [verdict('APPROVE', B)] },
    { number: 3, headRefOid: A, comments: [verdict('REQUEST_CHANGES', A)] },
    { number: 4, headRefOid: A, comments: [] },
  ];
  // #1 first run needed a second fix (fail), second run approved (pass); #2 closed (pass); #3 asked changes (fail); #4 waits.
  assert.deepEqual(codexFirstPass(runs, open), { pass: 2, fail: 2 });
  const second = { authorAssociation: 'OWNER', body: `Phản biện: REQUEST_CHANGES @ ${A}\nReviewer: Antigravity\n\n> P1 x`, createdAt: '2026-11-22T07:00:00Z', url: 'v' };
  assert.deepEqual(codexFirstPass([{ pr: 5, head: A }], [{ number: 5, headRefOid: A, comments: [verdict('APPROVE', A), second] }]), { pass: 0, fail: 1 }, 'the second critic counts too');
  assert.deepEqual(antigravityFirstPass([{ status: 'posted' }, { status: 'dropped' }, { status: 'posted' }]), { pass: 2, fail: 1 });
});

test('L72: Gỡ Vướng status file: streams shown, old marked, missing said; names cleaned', () => {
  const home = mkdtempSync(join(tmpdir(), 'gv-'));
  assert.equal(readGoVuong(home, NOW), null);
  mkdirSync(join(home, 'state'), { recursive: true });
  writeFileSync(goVuongPath(home), JSON.stringify({ at: '2026-11-22T07:30:00Z', streams: [{ name: 'Luồng A <script>', passedToday: 3, backlog: 5, missedSchedules: 1 }] }));
  const gv = readGoVuong(home, NOW);
  assert.deepEqual(gv, { old: false, streams: [{ name: 'Luồng A script', passedToday: 3, backlog: 5, missedSchedules: 1 }] });
  assert.equal(readGoVuong(home, new Date('2026-11-22T12:00:00Z')).old, true);
  const split = splitShares({ 'task|>500k': [0.2, 2], 'session|200-500k': [0.1, 3], 'owner|<100k': [0.7, 9] });
  const lines = throughputLines({ budget: { today: 6, daily: 5 }, merged: 3, goVuong: gv, codex: { pass: 2, fail: 2 }, antigravity: { pass: 0, fail: 0 }, split, projectShares: [{ project: 'la-lanh', share: 0.5 }, { project: 'dự án khác', share: 0.5 }] });
  assert.deepEqual(lines, [
    'Claude hôm nay: 6 điểm tuần / ngân sách ngày 5 điểm ⚠️ vượt',
    'Lá Lành: 3 PR merge hôm nay · 1 điểm Claude mỗi PR',
    'Gỡ Vướng: Luồng A script qua 3 lô, tồn 5, lỡ lịch 1 ⚠️ · 1 điểm Claude mỗi lô đạt',
    'Đạt ngay lần đầu (7 ngày): Codex sửa 50% (2/4) · Antigravity phản biện chưa có lượt',
    'Claude hôm nay theo nguồn: việc nền xong 20% · tin phiên khác 10% · owner 70%',
    'Theo độ dài phiên: dưới 100k 70% · 200–500k 10% · trên 500k 20% ⚠️ trên 500k cần dưới 10%',
    'Tốn nhất: owner × dưới 100k 70% · việc nền xong × trên 500k 20% · tin phiên khác × 200–500k 10%',
  ]);
  assert.doesNotMatch(lines.join('\n'), /\$|USD|đồng/, 'R14: points and shares only');
  const none = throughputLines({});
  assert.match(none.join('\n'), /chưa có số.*chưa biết \(thiếu giờ đặt lại\)/);
  assert.match(none.join('\n'), /Gỡ Vướng: chưa có file trạng thái/);
});

test('L72: spend is tagged by what started the turn; a tool result or an app reminder does not change it', () => {
  assert.equal(triggerOf({ type: 'user', origin: { kind: 'task-notification' } }), 'task');
  assert.equal(triggerOf({ type: 'user', origin: { kind: 'peer' } }), 'session');
  assert.equal(triggerOf({ type: 'user', origin: { kind: 'human' }, message: { content: 'làm đi' } }), 'owner');
  assert.equal(triggerOf({ type: 'user', message: { content: '<cross-session-message from="x">hi' } }), 'session');
  assert.equal(triggerOf({ type: 'user', message: { content: [{ type: 'tool_result', content: 'ok' }] } }), null);
  assert.equal(triggerOf({ type: 'user', message: { content: '<system-reminder>\nx' } }), null);
  const dir = mkdtempSync(join(tmpdir(), 'tr-'));
  const f = join(dir, 's.jsonl');
  const at = '2026-11-22T07:00:00.000Z';
  const reply = id => JSON.stringify({ type: 'assistant', timestamp: at, message: { id, model: 'claude-opus-5-5', usage: { input_tokens: 1000000, output_tokens: 0 } } });
  writeFileSync(f, [
    JSON.stringify({ type: 'user', origin: { kind: 'human' }, message: { content: 'làm đi' } }), reply('m1'),
    JSON.stringify({ type: 'user', origin: { kind: 'task-notification' }, message: { content: '<task-notification>' } }), reply('m2'),
    JSON.stringify({ type: 'user', message: { content: [{ type: 'tool_result', content: 'ok' }] } }), reply('m3'),
    JSON.stringify({ type: 'user', message: { content: '<system-reminder>x' } }), reply('m4'),
    JSON.stringify({ type: 'user', origin: { kind: 'peer' }, message: { content: '<cross-session-message>' } }), reply('m5'), '',
  ].join('\n'));
  const rec = scanFile(f);
  const day = rec.days['2026-11-22'];
  const sh = splitShares(rec.byCell['2026-11-22']);
  assert.equal(sh.triggerShares.task, 0.6, 'the notification turn: its reply, the reply after a tool result and after a reminder');
  assert.equal(sh.triggerShares.session, 0.2);
  assert.equal(sh.triggerShares.owner, 0.2);
  assert.equal(rec.trigger, 'session');
});

test('L72: the tick adds the throughput lines to the board numbers, and a failure never hides the other numbers', () => {
  const home = mkdtempSync(join(tmpdir(), 'tt-'));
  const gh = { raw: () => JSON.stringify([{ number: 1, mergedAt: '2026-11-22T03:00:00Z' }, { number: 2, mergedAt: '2026-11-21T10:00:00Z' }]) };
  const lines = throughputTick({ gh, prs: [], usageNote: { usage: { percent: 80, dayStart: { day: '2026-11-22', percent: 78 } }, today: { measured: true, shares: [{ project: 'la-lanh', share: 1 }], ...splitShares({ 'task|<100k': [1, 1] }) } }, home, now: NOW });
  assert.match(lines[1], /^Lá Lành: 1 PR merge hôm nay · 2 điểm Claude mỗi PR$/, 'only merges on the Vietnam day count');
  assert.match(lines[4], /theo nguồn: việc nền xong 100%/);
  assert.deepEqual(throughputTick({ gh: null, prs: null, home, now: NOW, log: () => {} }).length, 5, 'a broken gh says unknown, the rest still shows');
  const tick = readFileSync(new URL('./collab-tick.mjs', import.meta.url), 'utf8');
  assert.match(tick, /\.\.\.throughputTick\(\{ gh, prs, usageNote: usageNow\(\), log \}\)/);
  assert.ok(agentMarker);
});

test('L73: spend is split by what started the turn × the context each call carried', () => {
  const u = (kind, text, extra = {}) => ({ type: 'user', ...(kind ? { origin: { kind } } : {}), message: { content: [{ type: 'text', text }] }, ...extra });
  assert.equal(triggerOf(u('task-notification', '<scheduled-task name="la-lanh-autopilot">')), 'schedule', 'a scheduled task is not a background-task wake-up');
  assert.equal(triggerOf(u('task-notification', '<task-notification>')), 'task');
  assert.equal(triggerOf(u(null, '<ci-monitor-event>conflict')), 'autofix');
  assert.equal(triggerOf(u('coordinator', 'The coordinator says')), 'session');
  assert.equal(triggerOf({ type: 'user', origin: { kind: 'human' }, message: { content: [{ type: 'text', text: '<system-reminder>Linked sessions</system-reminder>' }, { type: 'text', text: 'làm tiếp' }] } }), 'owner');
  assert.equal(triggerOf(u('human', '<system-reminder>The session "Workflow" finished</system-reminder>')), 'session', 'the app\'s note that a linked session finished');
  assert.equal(triggerOf(u(null, 'Hourly workflow pass: …')), 'schedule', 'a cron or loop prompt');
  assert.equal(triggerOf(u(null, 'Làm việc bằng tiếng Việt', { isSidechain: true })), 'subagent');
  for (const t of ['This session is being continued from a previous conversation', '[Image: original 2000x1000]', 'Base directory for this skill: x', '[Request interrupted by user]']) assert.equal(triggerOf(u(null, t)), null, t);
  assert.deepEqual([{ input_tokens: 5 }, { cache_read_input_tokens: 150000 }, { cache_read_input_tokens: 400000, input_tokens: 1 }, { cache_read_input_tokens: 600000 }].map(ctxOf), ['<100k', '100-200k', '200-500k', '>500k']);
  const dir = mkdtempSync(join(tmpdir(), 'cell-'));
  const f = join(dir, 's.jsonl');
  const reply = (id, ctx) => JSON.stringify({ type: 'assistant', timestamp: '2026-11-22T07:00:00.000Z', message: { id, model: 'claude-opus-5-5', usage: { cache_read_input_tokens: ctx, output_tokens: 0 } } });
  writeFileSync(f, [JSON.stringify(u('task-notification', '<scheduled-task name="x">')), reply('m1', 600000), JSON.stringify(u(null, '<ci-monitor-event>')), reply('m2', 50000), reply('m3', 50000), ''].join('\n'));
  const rec = scanFile(f);
  assert.deepEqual(Object.keys(rec.byCell['2026-11-22']).sort(), ['autofix|<100k', 'schedule|>500k']);
  assert.equal(rec.byCell['2026-11-22']['autofix|<100k'][1], 2, 'calls are counted');
  const sh = splitShares(rec.byCell['2026-11-22']);
  assert.ok(Math.abs(sh.ctxShares['>500k'] - 600 / 700) < 1e-9);
  assert.deepEqual(sh.ctxCalls, { '<100k': 2, '100-200k': 0, '200-500k': 0, '>500k': 1 });
  const old = { ...rec, v: 1, byCell: {} };
  assert.ok(scanFile(f, old).byCell['2026-11-22'], 'a cache from the old format is read again from the start');
  const tick = readFileSync(new URL('./collab-throughput.mjs', import.meta.url), 'utf8');
  assert.match(tick, /split: usageNote\?\.today\?\.measured \? usageNote\.today : null/);
});
