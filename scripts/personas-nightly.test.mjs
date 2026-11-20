// Nightly fake-user run (owner 15.11.2026): change classification, the fixed daily sample, the
// judge-output check, the start/end comparison and the cross-user leak check. Fictional ids only.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import test from 'node:test';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { acquireLock } from './collab-lock.mjs';
import { dayCap, dayStatePath, readJson, stateDir, writeJson } from './collab-trust.mjs';
import { checkJudgeOutput, checkLabelOutput, classifyChanges, codex, compareRuns, crossLeaks, dayDir, nextDay, pickCodexItems, pickIds, raiseNew, renderNightly, safetyReasons, seedOf, startRun, unionLabels } from './personas-nightly.mjs';

test('only app-facing or unknown changes trigger a run', () => {
  assert.equal(classifyChanges(['docs/a.md', 'scripts/x.mjs', 'qa/personas/r.md', 'apps/api/tests/t.py']).run, false);
  for (const path of ['apps/web/src/App.tsx', 'apps/api/app/main.py', 'apps/api/migrations/0042.sql', 'pnpm-lock.yaml',
    'apps/api/uv.lock', 'package.json', 'apps/web/public/la.png', 'apps/web/vite.config.ts', 'packages/content/x.json']) {
    const c = classifyChanges(['docs/a.md', path]);
    assert.ok(c.run, path);
    assert.deepEqual(c.app, [path]);
  }
  const odd = classifyChanges(['something/new.txt']);
  assert.ok(odd.run, 'a change nobody classified still runs');
  assert.deepEqual(odd.unknown, ['something/new.txt']);
  assert.equal(classifyChanges([]).run, false);
});

test('the daily sample is fixed by date, 200 distinct ids, and differs between dates', () => {
  const ids = Array.from({ length: 1000 }, (_, i) => `P${String(i + 1).padStart(3, '0')}`);
  const a = pickIds('2026-11-16', ids);
  assert.equal(a.length, 200);
  assert.equal(new Set(a).size, 200);
  assert.deepEqual(pickIds('2026-11-16', [...ids].reverse()), a, 'input order does not matter');
  assert.notDeepEqual(pickIds('2026-11-17', ids), a);
  assert.equal(seedOf('2026-11-16'), 'personas-nightly:2026-11-16');
  assert.deepEqual(pickCodexItems('2026-11-16', ['x', 'y', 'z'], 2), pickCodexItems('2026-11-16', ['z', 'y', 'x'], 2));
  assert.equal(nextDay('2026-11-30'), '2026-12-01');
});

test('a judge output must cover every packet once with scores 1-5 and a reason', () => {
  const packets = ['{"item_id":"a"}', '{"item_id":"b"}', ''];
  assert.deepEqual(checkJudgeOutput(packets, [{ item_id: 'a', score: 3, reason: 'ok' }, { item_id: 'b', score: 5, reason: 'ok' }]), []);
  assert.match(checkJudgeOutput(packets, [{ item_id: 'a', score: 3, reason: 'ok' }]).join(), /missing 1/);
  assert.match(checkJudgeOutput(packets, [{ item_id: 'a', score: 6, reason: 'x' }, { item_id: 'b', score: 2, reason: '' }]).join(), /1-5.*reason/s);
  assert.deepEqual(checkJudgeOutput(packets, {}), ['output is not a JSON array']);
});

test('earlier nights\' scores are kept when the repo cache is merged in', () => {
  const merged = unionLabels({ rubric: 'r', scores: { a: { score: 2 } } }, { scores: { b: { score: 4 } } }, 'scores');
  assert.deepEqual(Object.keys(merged.scores).sort(), ['a', 'b']);
  assert.equal(merged.rubric, 'r');
  assert.deepEqual(unionLabels(null, null, 'labels'), { labels: {} });
});

const metrics = (caught, figurative, okSafety) => ({
  crisis: { crisis_caught: caught, figurative_flagged: figurative, ordinary_flagged: 0 },
  verdicts: [
    { group: 'Lặp lại', threshold: 'T1', result: '1', ok: false },
    { group: 'An toàn', threshold: 'Báo nhầm', result: `${figurative}`, ok: okSafety },
  ],
});
test('a safety threshold that passed in the morning and fails at night is a regression', () => {
  assert.deepEqual(compareRuns(metrics(5, 0, true), metrics(5, 0, true)).safety, []);
  const worse = compareRuns(metrics(5, 0, true), metrics(3, 4, false));
  assert.equal(worse.safety.length, 3);
  assert.match(worse.safety.join('|'), /đạt ở đầu ngày, trượt ở cuối ngày/);
  assert.match(worse.safety.join('|'), /giảm từ 5 xuống 3/);
  assert.equal(compareRuns(metrics(0, 0, false), metrics(0, 0, false)).safety.length, 0, 'a fail that was already failing is not a new alert');
});

test('one persona\'s typed text on another persona\'s screen is a leak', () => {
  const rows = [
    { persona: 'P1', day: 0, tarot: [{ text: 'Câu hỏi riêng của người một về chỗ làm' }], headline: 'Hôm nay ổn' },
    { persona: 'P2', day: 3, tarot: [], headline: 'Lá nhắc: Câu hỏi riêng của người một về chỗ làm' },
    { persona: 'P1', day: 4, tarot: [{ text: 'ngắn', headline: 'x' }], thesis: 'Câu hỏi riêng của người một về chỗ làm' },
  ];
  assert.deepEqual(crossLeaks(rows), [{ persona: 'P2', day: 3, from: 'P1' }]);
  assert.deepEqual(crossLeaks(rows.slice(0, 1)), []);
});

test('the report names both commits, the seed and puts safety first', () => {
  const state = { date: '2026-11-16', start: 'a'.repeat(40), end: 'b'.repeat(40), ids: ['P1'], seed: 'personas-nightly:2026-11-16', appChanges: ['apps/web/src/x.ts'], unknownChanges: [], runs: { end: { seconds: 90, loadMax: 6.2, loadMean: 4.1 } } };
  const text = renderNightly({ state, cmp: compareRuns(metrics(5, 0, true), metrics(3, 0, true)), leaks: [], codexCmp: null, judged: { needed: 10, scored: 8 }, endMetrics: { coverage: { http_errors: 0 } } });
  assert.match(text, /aaaaaaaaaaaa/);
  assert.match(text, /bbbbbbbbbbbb/);
  assert.match(text, /personas-nightly:2026-11-16/);
  assert.ok(text.indexOf('Cảnh báo an toàn') < text.indexOf('So với đầu ngày'));
  assert.match(text, /8\/10 mục/);
  assert.match(text, /không thay QA trình duyệt/);
});

test('action-label outputs are checked against the label schema, not the score schema', () => {
  const packets = ['{"action":"đi bộ 5 phút"}', '{"action":"gọi cho mẹ"}'];
  assert.deepEqual(checkLabelOutput(packets, [{ action: 'đi bộ 5 phút', label: 'light' }, { action: 'gọi cho mẹ', label: 'not_light' }]), []);
  assert.match(checkLabelOutput(packets, [{ action: 'đi bộ 5 phút', label: 'nhẹ' }]).join('|'), /missing 1.*light or not_light/s);
});

test('a safety reason is raised once, as soon as it is known, and only new reasons later', () => {
  const calls = [];
  const alert = (_gh, text) => { calls.push(text); return { number: 7 }; };
  const state = { start: 'a'.repeat(40), end: 'b'.repeat(40), alerted: [] };
  const first = safetyReasons(metrics(5, 0, true), metrics(3, 0, true), [
    { persona: 'P1', day: 0, tarot: [{ text: 'Câu hỏi riêng của người một về chỗ làm' }] },
    { persona: 'P2', day: 1, headline: 'Câu hỏi riêng của người một về chỗ làm' },
  ]);
  assert.equal(first.reasons.length, 2);
  assert.equal(raiseNew('2026-11-16', state, first.reasons, { alert, gh: () => null }).raised.length, 2);
  assert.equal(calls.length, 1);
  assert.equal(raiseNew('2026-11-16', state, first.reasons, { alert, gh: () => null }).raised.length, 0, 'finish does not repeat it');
  assert.equal(calls.length, 1);
  assert.deepEqual(raiseNew('2026-11-16', state, [...first.reasons, 'mới'], { alert, gh: () => null }).raised, ['mới']);
});

const codexDay = '2026-11-16';
const now = () => ({ date: codexDay, hour: 23, minute: 10 });
const nowMs = () => Date.parse(`${codexDay}T23:10:00+07:00`);
function seedState(extra = {}) {
  mkdirSync(dayDir(codexDay), { recursive: true });
  writeJson(join(dayDir(codexDay), 'state.json'), { date: codexDay, start: 'a'.repeat(40), end: 'b'.repeat(40), codexItems: ['x'], ...extra });
}
test('the nightly Codex call is counted before it runs, even when it fails, and runs once a night', () => {
  writeJson(dayStatePath(codexDay), { codexRuns: 3, failures: 0 });
  seedState();
  const failed = codex(codexDay, { run: () => { throw new Error('timeout'); }, now, nowMs });
  assert.equal(failed.status, 'failed');
  assert.equal(readJson(dayStatePath(codexDay), {}).codexRuns, 4);
  assert.equal(codex(codexDay, { run: () => { throw new Error('should not run'); }, now, nowMs }).status, 'skipped');
  seedState(); // a re-run of prepare rewrites the date directory without the marker
  assert.equal(codex(codexDay, { run: () => { throw new Error('should not run'); }, now, nowMs }).reason, 'đêm nay đã gọi Codex một lần');
  assert.equal(readJson(dayStatePath(codexDay), {}).codexRuns, 4);
});

test('a prepared night cannot start its Codex call after that night\'s 23:59', () => {
  const day = '2026-11-20';
  mkdirSync(dayDir(day), { recursive: true });
  writeJson(join(dayDir(day), 'state.json'), { date: day, start: 'a'.repeat(40), end: 'b'.repeat(40), codexItems: ['x'] });
  const after = codex(day, { run: () => { throw new Error('no'); }, now: () => ({ date: '2026-11-21', hour: 0, minute: 5 }), nowMs: () => Date.parse('2026-11-21T00:05:00+07:00') });
  assert.equal(after.status, 'refused');
});

test('the nightly Codex call waits for the shared review lock and respects the cap and the cutoff', () => {
  const day = '2026-11-18';
  const at = hhmm => ({ now: () => ({ date: day, hour: 23, minute: 10 }), nowMs: () => Date.parse(`${day}T${hhmm}:00+07:00`) });
  mkdirSync(dayDir(day), { recursive: true });
  writeJson(join(dayDir(day), 'state.json'), { date: day, start: 'a'.repeat(40), end: 'b'.repeat(40), codexItems: ['x'] });
  const release = acquireLock(join(stateDir, 'review.lock'), { staleMs: 60000 });
  try { assert.equal(codex(day, { run: () => { throw new Error('no'); }, ...at('23:10') }).status, 'busy'); }
  finally { release(); }
  writeJson(dayStatePath(day), { codexRuns: dayCap({}) - 1, failures: 0 });
  assert.equal(codex(day, { run: () => { throw new Error('no'); }, ...at('23:10') }).reason, 'hết lượt Codex trong ngày');
  assert.equal(readJson(dayStatePath(day), {}).codexRuns, dayCap({}) - 1);
  assert.equal(codex(day, { run: () => { throw new Error('no'); }, ...at('23:59') }).status, 'refused');
});

test('a second prepare for the same date waits for the lock and leaves a running night\'s files alone (#565)', async () => {
  const day = '2026-11-19';
  mkdirSync(dayDir(day), { recursive: true });
  writeFileSync(join(dayDir(day), 'personas-200.json'), '{}');
  const release = acquireLock(join(stateDir, 'check.lock'), { staleMs: 60000 });
  let ran = false;
  try {
    const second = await startRun(day, async () => { ran = true; }, { waitMs: 0, stepMs: 1 });
    assert.equal(second.status, 'busy');
    assert.equal(ran, false);
    assert.ok(existsSync(join(dayDir(day), 'personas-200.json')), 'the running night keeps its files');
  } finally { release(); }
  let seen = null;
  const fresh = await startRun(day, async dir => { seen = existsSync(join(dir, 'personas-200.json')); return { status: 'ok' }; }, { waitMs: 0, stepMs: 1 });
  if (fresh.status === 'ok') assert.equal(seen, false, 'the lock holder starts from an empty folder');
});
