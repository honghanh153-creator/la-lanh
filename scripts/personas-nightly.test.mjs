// Nightly fake-user run (owner 15.11.2026): change classification, the fixed daily sample, the
// judge-output check, the start/end comparison and the cross-user leak check. Fictional ids only.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import test from 'node:test';
import { checkJudgeOutput, classifyChanges, compareRuns, crossLeaks, nextDay, pickCodexItems, pickIds, renderNightly, seedOf, unionLabels } from './personas-nightly.mjs';

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
