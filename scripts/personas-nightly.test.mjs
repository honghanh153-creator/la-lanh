// Nightly fake-user run (owner 15.11.2026): change classification, the fixed daily sample, the
// judge-output check, the start/end comparison and the cross-user leak check. Fictional ids only.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import test from 'node:test';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { acquireLock } from './collab-lock.mjs';
import { personasReceiptResult, readReceipts, receiptSummary, writeRunReceipt } from './collab-run-receipt.mjs';
import { dayCap, dayStatePath, readJson, stateDir, writeJson } from './collab-trust.mjs';
import { checkJudgeOutput, checkLabelOutput, classifyChanges, codex, compareRuns, crossLeaks, dayDir, finish, nextDay, pickCodexItems, pickIds, raiseNew, renderNightly, safetyReasons, seedOf, startRun, unionLabels, withFailureReceipt } from './personas-nightly.mjs';

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

// Codex r5/r6 on #858: a failed persona night is recorded with its real outcome.
const measured = 'b'.repeat(40);
const receiptFile = () => join(mkdtempSync(join(tmpdir(), 'persona-receipts-')), 'run-receipts.jsonl');
const boardAt = path => receiptSummary(readReceipts(path), { nowMs: Date.now() + 1000 }).personas;

test('#858: a simulation that times out or exits non-zero leaves an error receipt naming the measured commit', async () => {
  const path = receiptFile();
  const receipt = r => writeRunReceipt({ ...r, path });
  // The same throw prepare() makes at the simulation step, inside the real night lock.
  const night = () => startRun('2026-11-22', async () => { throw new Error('persona_sim end exit null: killed after the time limit'); }, { waitMs: 0, stepMs: 1 });
  // On a machine that is running another heavy job the night never starts; throw the same error then.
  const failing = async () => { const r = await night(); if (r?.status === 'busy') throw new Error('persona_sim end exit 1: x'); return r; };
  await assert.rejects(withFailureReceipt(measured, failing, receipt), /persona_sim end exit/, 'the failure still reaches the caller');
  const rows = readReceipts(path);
  assert.equal(rows.length, 1);
  assert.deepEqual({ kind: rows[0].kind, result: rows[0].result, sha: rows[0].sha }, { kind: 'personas', result: 'error', sha: measured });
  assert.deepEqual(boardAt(path), { runs: 1, errors: 1, last: { at: rows[0].at, sha: measured } }, 'the board shows the failed night, not "chưa chạy"');
  // A night that never started (busy, too late) returns its status and leaves nothing.
  assert.deepEqual(await withFailureReceipt(measured, async () => ({ status: 'busy' }), receipt), { status: 'busy' });
  assert.equal(readReceipts(path).length, 1);
  // A receipt that cannot be written does not hide the real failure.
  await assert.rejects(withFailureReceipt(measured, async () => { throw new Error('sim failed'); }, () => { throw new Error('disk full'); }), /sim failed/);
});

function seedFinish(day, extra = {}) {
  const dir = dayDir(day);
  for (const role of ['start', 'end']) {
    mkdirSync(join(dir, role), { recursive: true });
    writeFileSync(join(dir, role, 'report.md'), `# ${role}\n`);
  }
  writeFileSync(join(dir, 'end', 'transcript.jsonl'), '');
  writeFileSync(join(dir, 'codex-sample.jsonl'), '{"item_id":"a"}\n{"item_id":"b"}\n');
  rmSync(join(dir, 'codex-scores.json'), { force: true });
  writeJson(join(dir, 'state.json'), { date: day, start: 'a'.repeat(40), end: measured, seed: seedOf(day), ids: ['P1', 'P2'], appChanges: ['apps/web/src/x.ts'], unknownChanges: [], codexItems: ['x'], alerted: [], ...extra });
  process.env.LA_LANH_REPORT_DIR = mkdtempSync(join(tmpdir(), 'persona-report-'));
}
const goodScores = [{ item_id: 'a', score: 4, reason: 'rõ' }, { item_id: 'b', score: 3, reason: 'được' }];
const finishDeps = written => ({ alert: () => ({ number: 1 }), gh: () => null, receipt: r => written.push(r), report: () => ({ ...metrics(5, 0, true), understood: { items_needed: 1, items_scored: 1 }, coverage: { http_errors: 0 } }) });

test('#858: a Codex timeout followed by finish is an error receipt; a clean night is ok', () => {
  const day = '2026-11-23';
  const at = { now: () => ({ date: day, hour: 23, minute: 10 }), nowMs: () => Date.parse(`${day}T23:10:00+07:00`) };
  seedFinish(day);
  assert.equal(codex(day, { run: () => { throw new Error('spawnSync codex ETIMEDOUT'); }, ...at }).status, 'failed');
  const written = [];
  assert.equal(finish(day, finishDeps(written)).status, 'finished', 'the report is still written');
  assert.deepEqual(written, [{ kind: 'personas', result: 'error', sha: measured, counts: { personas: 2, safetyReasons: 0 } }]);

  // Codex answered with something unreadable: the attempt is on record and no scores exist.
  seedFinish(day, { codexAttempt: { startedAt: '2026-11-23T16:10:00.000Z' } });
  const unreadable = [];
  finish(day, finishDeps(unreadable));
  assert.equal(unreadable[0].result, 'error');

  // Copied scores cannot erase the durable failure, even when the rebuilt state lost the error.
  writeFileSync(join(dayDir(day), 'codex-scores.json'), JSON.stringify(goodScores));
  const scored = [];
  finish(day, finishDeps(scored));
  assert.equal(scored[0].result, 'error');
  seedFinish('2026-11-24');
  const clean = [];
  finish('2026-11-24', finishDeps(clean));
  assert.deepEqual(clean, [{ kind: 'personas', result: 'ok', sha: measured, counts: { personas: 2, safetyReasons: 0 } }]);
});

// Codex r7 on #858: an answer that does not score every sampled item is not a good night.
test('#858: codex then finish records ok only when every sampled item has a valid score', () => {
  const answers = [
    ['2026-12-01', [], 'incomplete', 'error'],
    ['2026-12-02', [goodScores[0]], 'incomplete', 'error'],
    ['2026-12-03', [goodScores[0], { item_id: 'b', score: 6, reason: 'x' }], 'incomplete', 'error'],
    ['2026-12-04', goodScores, 'scored', 'ok'],
  ];
  for (const [day, answer, status, result] of answers) {
    const at = { now: () => ({ date: day, hour: 23, minute: 10 }), nowMs: () => Date.parse(`${day}T23:10:00+07:00`) };
    seedFinish(day);
    const run = (_bin, args) => { writeFileSync(args[args.indexOf('-o') + 1], JSON.stringify(answer)); };
    assert.equal(codex(day, { run, ...at }).status, status, day);
    const written = [];
    const done = finish(day, finishDeps(written));
    assert.equal(written[0].result, result, day);
    const text = readFileSync(done.report, 'utf8');
    assert.equal(/Codex trả lời thiếu hoặc sai/.test(text), result === 'error', `${day}: the report says the scores were not used`);
  }
  // Invalid stored scores are an error even without an attempt marker.
  seedFinish('2026-12-05');
  writeFileSync(join(dayDir('2026-12-05'), 'codex-scores.json'), '[]');
  const rewritten = [];
  finish('2026-12-05', finishDeps(rewritten));
  assert.equal(rewritten[0].result, 'error');
});

test('L858: durable Codex outcomes survive the production reset and finish reports the same result', async t => {
  const cases = [
    { day: '2026-12-10', outcome: 'failed', reset: true, expected: 'error' },
    { day: '2026-12-11', outcome: 'scored', reset: true, expected: 'error' },
    { day: '2026-12-12', outcome: 'incomplete', reset: true, expected: 'error' },
    { day: '2026-12-13', outcome: 'scored', reset: false, expected: 'ok' },
    { day: '2026-12-14', outcome: null, reset: true, expected: 'ok' },
    { day: '2026-12-15', outcome: 'failed', reset: true, noNewItems: true, expected: 'error' },
  ];
  for (const entry of cases) {
    await t.test(`${entry.day}: ${entry.outcome ?? 'not called'}, reset=${entry.reset}`, async () => {
      const { day, outcome, reset, expected } = entry;
      const at = { now: () => ({ date: day, hour: 23, minute: 10 }), nowMs: () => Date.parse(`${day}T23:10:00+07:00`) };
      seedFinish(day);
      if (outcome) {
        const run = (_bin, args) => {
          if (outcome === 'failed') throw new Error('synthetic Codex timeout');
          writeFileSync(args[args.indexOf('-o') + 1], JSON.stringify(outcome === 'scored' ? goodScores : []));
        };
        assert.equal(codex(day, { run, ...at }).status, outcome);
      }
      if (reset) {
        const resetResult = await startRun(day, async dir => {
          assert.equal(existsSync(join(dir, 'state.json')), false, 'the production reset removes the old state');
          assert.equal(existsSync(join(dir, 'codex-scores.json')), false, 'the production reset removes scores');
          seedFinish(day, entry.noNewItems || !outcome ? { codexItems: [] } : {});
          return { status: 'prepared' };
        }, { waitMs: 0, stepMs: 1 });
        assert.equal(resetResult.status, 'prepared', 'exercise the real reset, never skip a busy result');
        assert.equal(readJson(join(dayDir(day), 'state.json'), {}).codexAttempt, undefined);
        assert.equal(codex(day, { run: () => assert.fail('a prepare retry must not call Codex again'), ...at }).status, 'skipped');
      }
      const written = [];
      const done = finish(day, finishDeps(written));
      assert.deepEqual(written, [{ kind: 'personas', result: expected, sha: measured, counts: { personas: 2, safetyReasons: 0 } }]);
      const reportText = readFileSync(done.report, 'utf8');
      assert.equal(reportText.includes('Codex đã được gọi nhưng không có kết quả hợp lệ.'), expected === 'error');
      assert.equal(reportText.includes('- Không chạy ('), outcome === null);
      assert.equal(readJson(dayStatePath(day), {}).codexRuns ?? 0, outcome ? 1 : 0);
    });
  }
});

test('#858: a finish that stops part-way leaves an error receipt and still throws', () => {
  const day = '2026-11-25';
  seedFinish(day);
  const written = [];
  assert.throws(() => finish(day, { ...finishDeps(written), report: () => { throw new Error('persona_report exit 1'); } }), /persona_report exit 1/);
  assert.deepEqual(written, [{ kind: 'personas', result: 'error', sha: measured, counts: { personas: 2 } }]);
  assert.deepEqual([{ failed: true }, { codexAttempt: { error: 'x' }, codexScored: true }, { codexAttempt: {}, codexScored: false }, { codexAttempt: {}, codexScored: true }, {}, { codexInvalid: true }, { codexAttempt: {}, codexScored: true, codexInvalid: true }].map(personasReceiptResult), ['error', 'error', 'error', 'ok', 'ok', 'error', 'error']);
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
