import test from 'node:test';
import assert from 'node:assert/strict';
import { appendFileSync, mkdirSync, mkdtempSync, readFileSync, utimesSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  costOf, modeFor, modePath, paceLimit, paceSubject, paceWatch, projectOf, readUsage, scanFile, todayShares, usageHealth, usageLine, usagePath, usageTick,
} from './collab-usage.mjs';
import { renderBoard } from './collab-status.mjs';
import { runTick } from './collab-tick.mjs';

const home = () => mkdtempSync(join(tmpdir(), 'usage-'));
const reading = (h, percent, at) => { mkdirSync(join(h, 'state'), { recursive: true }); writeFileSync(usagePath(h), JSON.stringify({ percent, at })); };
const NOW = new Date('2026-11-22T08:00:00Z'); // 15:00 in Vietnam
const ago = minutes => new Date(NOW.getTime() - minutes * 60000).toISOString();
const line = (id, model, usage, timestamp = NOW.toISOString()) => `${JSON.stringify({ type: 'assistant', timestamp, message: { id, model, usage } })}\n`;

test('L71 owner 22.11: below 75% normal, 75–84% shift, 85–94% saving, 95% or more fallback', () => {
  assert.equal(modeFor(74.9), 'normal');
  assert.equal(modeFor(75), 'shift');
  assert.equal(modeFor(84.9), 'shift');
  assert.equal(modeFor(85), 'saving');
  assert.equal(modeFor(94.9), 'saving');
  assert.equal(modeFor(95), 'fallback');
  assert.equal(modeFor(100), 'fallback');
  assert.equal(modeFor(NaN), null);
});

test('a fresh reading sets the mode; a reading older than 3 hours keeps the last mode', () => {
  const h = home();
  assert.equal(readUsage({ home: h, now: NOW }).mode, 'normal', 'no reading yet: normal, never a guess upward');
  reading(h, 96, ago(10));
  assert.deepEqual([readUsage({ home: h, now: NOW }).mode, readUsage({ home: h, now: NOW }).fresh], ['fallback', true]);
  reading(h, 40, ago(4 * 60));
  const stale = readUsage({ home: h, now: NOW });
  assert.equal(stale.fresh, false);
  assert.equal(stale.mode, 'fallback', 'a stale low reading does not switch Claude back on');
  assert.equal(JSON.parse(readFileSync(modePath(h), 'utf8')).mode, 'fallback');
  reading(h, 101, ago(1));
  assert.equal(readUsage({ home: h, now: NOW }).fresh, false, 'an impossible percent is not a reading');
});

test('pace base: the first reading of the Vietnam day; a drop means the weekly window reset', () => {
  const h = home();
  reading(h, 60, ago(120));
  assert.deepEqual(readUsage({ home: h, now: NOW }).dayStart, { day: '2026-11-22', percent: 60 });
  reading(h, 66, ago(5));
  assert.deepEqual(readUsage({ home: h, now: NOW }).dayStart, { day: '2026-11-22', percent: 60 });
  reading(h, 3, ago(1));
  assert.deepEqual(readUsage({ home: h, now: NOW }).dayStart, { day: '2026-11-22', percent: 0 });
});

test('public API prices: input, 1.25× cache write, cache read, output', () => {
  const m = { input_tokens: 1e6 };
  assert.equal(costOf('claude-opus-5-5', m), 4);
  assert.equal(costOf('claude-opus-5-5', { cache_creation_input_tokens: 1e6 }), 5);
  assert.equal(costOf('claude-opus-5-5', { cache_read_input_tokens: 1e6 }), 0.2);
  assert.equal(costOf('claude-sonnet-5-5', { output_tokens: 1e6 }), 10);
  assert.equal(costOf('claude-fable-5-2', { output_tokens: 1e6 }), 40);
  assert.equal(costOf('claude-haiku-5-5', m), 0.1);
  assert.equal(costOf('claude-sonnet-4-6', m), 3);
  assert.equal(costOf('<synthetic>', m), 4, 'unknown models price as Opus');
});

test('scanFile: one message counted once, a half-written line waits, appends are read from the offset', () => {
  const dir = home();
  const f = join(dir, 's.jsonl');
  const u = { output_tokens: 1e6 };
  writeFileSync(f, line('a', 'claude-opus-5-5', u) + line('a', 'claude-opus-5-5', u) + JSON.stringify({ type: 'user', message: { content: 'x' } }) + '\n' + '{"type":"assistant","usage');
  const first = scanFile(f, null, { chunk: 37 });
  assert.equal(first.days['2026-11-22'], 20, 'repeated id across content blocks counts once');
  appendFileSync(f, `"x\n${line('b', 'claude-sonnet-5-5', u)}`);
  const second = scanFile(f, first, { chunk: 4096 });
  assert.equal(second.days['2026-11-22'], 30);
  assert.equal(scanFile(f, second).days['2026-11-22'], 30, 'nothing new: nothing added');
  const yesterday = join(dir, 'y.jsonl');
  writeFileSync(yesterday, line('c', 'claude-opus-5-5', u, '2026-11-21T16:59:00Z') + line('d', 'claude-opus-5-5', u, '2026-11-21T17:00:00Z'));
  assert.deepEqual(scanFile(yesterday).days, { '2026-11-21': 20, '2026-11-22': 20 }, 'days are Vietnam days');
});

test('todayShares: la-lanh checkouts and worktrees are one project; other folders are one unnamed bucket', () => {
  const h = home();
  const root = join(h, 'projects');
  const put = (dir, name, text) => { mkdirSync(join(root, dir), { recursive: true }); writeFileSync(join(root, dir, name), text); };
  put('-Users-x-Documents-New-project-la-lanh', 'a.jsonl', line('a', 'claude-opus-5-5', { output_tokens: 1e6 }));
  put('-Users-x-Documents-New-project-la-lanh--claude-worktrees-w1/s1/subagents', 'b.jsonl', line('b', 'claude-opus-5-5', { output_tokens: 1e6 }));
  put('-Users-x-Library-scratch-somewhere', 'c.jsonl', line('c', 'claude-opus-5-5', { output_tokens: 2e6 }));
  put('-Users-x-old', 'd.jsonl', line('d', 'claude-opus-5-5', { output_tokens: 9e6 }));
  const old = new Date(NOW.getTime() - 2 * 86400000);
  utimesSync(join(root, '-Users-x-old', 'd.jsonl'), old, old);
  const t = todayShares({ home: h, root, now: NOW });
  assert.deepEqual(t.shares, [{ project: 'la-lanh', share: 0.5 }, { project: 'dự án khác', share: 0.5 }], 'la-lanh first, then the rest');
  assert.equal(projectOf('-Users-x-Documents-la-lanh-claude'), 'la-lanh');
  assert.equal(projectOf('-Users-x-la-lanhx'), 'dự án khác');
});

test('the board line and warnings show shares and percents only: no amounts, no folder names (R14)', () => {
  const h = home();
  reading(h, 88, ago(5));
  const usage = readUsage({ home: h, now: NOW });
  const text = usageLine(usage, { measured: true, shares: [{ project: 'la-lanh', share: 0.7 }, { project: 'dự án khác', share: 0.3 }] });
  assert.equal(text, 'Claude tuần: 88% · chế độ: tiết kiệm · hôm nay theo dự án: la-lanh 70%, dự án khác 30%');
  assert.doesNotMatch(text, /\$|USD|Users|scratch/);
  assert.match(usageHealth(usage).join('\n'), /⚠️ Claude đã dùng 88% tuần: Claude chỉ làm sự cố/);
  reading(h, 97, ago(5));
  assert.match(usageHealth(readUsage({ home: h, now: NOW })).join('\n'), /không dùng Claude; Codex, Antigravity và máy chạy tiếp, giữ 5%/);
  reading(h, 97, ago(5 * 60));
  assert.match(usageHealth(readUsage({ home: h, now: NOW })).join('\n'), /⚠️ Số lượt Claude cũ hơn 3 giờ: giữ chế độ chuyển sang Codex/);
});

test('pace alert: once a day when today gained more than 70% of an even weekly pace', () => {
  assert.equal(Math.round(paceLimit * 10) / 10, 10);
  const h = home();
  const sent = [];
  reading(h, 50, ago(150));
  readUsage({ home: h, now: NOW });
  reading(h, 59, ago(1));
  assert.equal(paceWatch({ usage: readUsage({ home: h, now: NOW }), alert: t => sent.push(t), home: h }), null, '9 points: below the line');
  reading(h, 61, ago(1));
  assert.ok(paceWatch({ usage: readUsage({ home: h, now: NOW }), alert: t => sent.push(t), home: h }));
  reading(h, 70, ago(1));
  paceWatch({ usage: readUsage({ home: h, now: NOW }), alert: t => sent.push(t), home: h });
  assert.equal(sent.length, 1, 'one alert per day');
  assert.match(sent[0], /^Hôm nay Claude đã dùng thêm 11% giới hạn tuần/);
  assert.doesNotMatch(sent[0], /\$|USD/);
});

test('L67: the board shows the usage line, the tick feeds it and the warnings, and the pace alert has its own subject', () => {
  const board = renderBoard({ now: { date: '2026-11-22', hour: 15, minute: 0 }, status: 'idle', usage: 'Claude tuần: 88% · chế độ: tiết kiệm · hôm nay theo dự án: la-lanh 70%' });
  assert.match(board, /\nClaude tuần: 88% · chế độ: tiết kiệm/);
  assert.doesNotMatch(renderBoard({ now: { date: '2026-11-22', hour: 15, minute: 0 }, status: 'idle' }), /Claude tuần/);
  const posted = [];
  const gh = { raw: () => '', json: () => [] };
  let calls = 0;
  const given = runTick(gh, () => [], { run: g => g, gapNote: () => null, areaNote: () => null, usageNote: ({ alert }) => { calls += 1; posted.push(alert); return { line: 'Claude tuần: 96%', health: ['⚠️ Claude đã dùng 96% tuần'] }; } });
  assert.equal(calls, 0, 'nothing is scanned until the tick asks');
  assert.ok(given.health().includes('⚠️ Claude đã dùng 96% tuần'));
  given.health();
  assert.equal(calls, 1, 'one scan per tick');
  assert.equal(paceSubject, 'Claude dùng nhanh hơn nhịp tuần');
  const broken = runTick(gh, () => [], { run: g => g, gapNote: () => null, areaNote: () => null, log: () => {}, usageNote: () => { throw new Error('EACCES'); } });
  assert.ok(Array.isArray(broken.health()), 'a failed usage read never breaks the tick');
  assert.equal(typeof usageTick, 'function');
});

test('Codex #893: a null, empty or false percent is no reading; a drop across midnight is a weekly reset; the scan cache keeps no paths or ids', () => {
  const h = home();
  reading(h, 97, ago(10));
  assert.equal(readUsage({ home: h, now: NOW }).mode, 'fallback');
  for (const bad of [null, '', false, ' ']) {
    reading(h, bad, ago(5));
    const u = readUsage({ home: h, now: NOW });
    assert.deepEqual([u.fresh, u.mode], [false, 'fallback'], `${JSON.stringify(bad)} keeps the saved mode`);
  }
  const r = home();
  mkdirSync(join(r, 'state'), { recursive: true });
  writeFileSync(modePath(r), JSON.stringify({ mode: 'fallback', percent: 96, at: '2026-11-21T15:00:00Z', dayStart: { day: '2026-11-21', percent: 80 } }));
  reading(r, 11, ago(5));
  assert.deepEqual(readUsage({ home: r, now: NOW }).dayStart, { day: '2026-11-22', percent: 0 }, '96% yesterday, 11% today: 11 points gained, not 0');
  const root = join(h, 'projects', '-Users-x-Documents-la-lanh');
  mkdirSync(root, { recursive: true });
  writeFileSync(join(root, 's.jsonl'), line('msg_secretid', 'claude-opus-5-5', { output_tokens: 1e6 }));
  todayShares({ home: h, root: join(h, 'projects'), now: NOW });
  const cache = readFileSync(join(h, 'state', 'claude-usage-scan.json'), 'utf8');
  assert.doesNotMatch(cache, /msg_secretid|Users|la-lanh|s\.jsonl/);
  assert.match(cache, /[0-9a-f]{16}/);
});
