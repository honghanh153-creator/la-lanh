import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { explainGap, noteTickGap, parseKernTime } from './collab-tick-gap.mjs';
import { runTick } from './collab-tick.mjs';

const ms = iso => Date.parse(iso);
const fresh = () => join(mkdtempSync(join(tmpdir(), 'tick-gap-')), 'tick-gaps.jsonl');
const lines = path => readFileSync(path, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l));

test('the Mac clock values are read from sysctl output', () => {
  assert.equal(parseKernTime('{ sec = 1795253517, usec = 675245 } Sat Nov 21 16:31:57 2026'), 1795253517000);
  assert.equal(parseKernTime(''), null);
  assert.equal(parseKernTime('{ sec = 0, usec = 0 }'), null, 'never slept');
});

// L57 (21.11.2026): no tick line from 07:45 to 10:04 and nobody could say why.
test('L57: a tick gap is written once with its cause; only an unexplained gap alerts', () => {
  const morning = { heartbeat: () => ({ at: '2026-11-21T00:45:05Z' }), nowMs: ms('2026-11-21T03:03:48Z') };
  const slept = { sleptAt: ms('2026-11-21T00:48:30Z'), wokeAt: ms('2026-11-21T02:56:40Z'), bootedAt: ms('2026-10-12T06:27:50Z') };
  const path = fresh();
  const logged = [];
  const alerts = [];
  const entry = noteTickGap({ ...morning, power: () => slept, path, log: t => logged.push(t), alert: t => alerts.push(t) });
  assert.deepEqual([entry.cause, entry.minutes], ['sleep', 139]);
  assert.match(logged[0], /^tick ngừng 21\.11 07:45–10:03 \(139 phút\): Mac ngủ 07:48–09:56$/);
  assert.equal(alerts.length, 0, 'a sleeping Mac is not an incident');
  assert.equal(noteTickGap({ ...morning, nowMs: ms('2026-11-21T03:13:00Z'), power: () => slept, path, log: t => logged.push(t), alert: t => alerts.push(t) }), null, 'a busy tick that saw the same gap adds nothing');
  assert.equal(lines(path).length, 1);

  const awake = { sleptAt: ms('2026-11-20T15:00:00Z'), wokeAt: ms('2026-11-20T15:20:00Z'), bootedAt: ms('2026-10-12T06:27:50Z') };
  const path2 = fresh();
  const unknown = noteTickGap({ ...morning, power: () => awake, path: path2, log: () => {}, alert: t => alerts.push(t) });
  assert.equal(unknown.cause, 'unknown');
  assert.equal(alerts.length, 1);
  assert.match(alerts[0], /không rõ nguyên nhân/);

  assert.equal(explainGap({ fromMs: ms('2026-11-21T00:45:00Z'), toMs: ms('2026-11-21T03:03:00Z'), power: { sleptAt: ms('2026-11-21T02:40:00Z'), wokeAt: ms('2026-11-21T02:50:00Z') } }).cause, 'unknown',
    'a short nap late in the gap does not explain two hours without a tick');
  assert.equal(explainGap({ fromMs: ms('2026-11-21T00:45:00Z'), toMs: ms('2026-11-21T03:03:00Z'), power: { bootedAt: ms('2026-11-21T02:58:00Z') } }).cause, 'restart');
  assert.equal(noteTickGap({ heartbeat: () => ({ at: '2026-11-21T02:55:00Z' }), nowMs: ms('2026-11-21T03:03:48Z'), power: () => { throw new Error('no read below 30 minutes'); }, path: fresh() }), null, 'a normal 10-minute tick reads nothing');
  assert.equal(noteTickGap({ heartbeat: () => null, nowMs: ms('2026-11-21T03:03:48Z'), power: () => { throw new Error('x'); }, path: fresh() }), null, 'no heartbeat yet');
});

test('L57: the tick entry notes the gap before the tick runs, and a failing note never stops the tick', () => {
  const seen = [];
  const given = runTick({ raw: () => '', json: () => [] }, () => [], { run: g => g, gapNote: o => { seen.push(o); return null; } });
  assert.equal(seen.length, 1);
  assert.equal(typeof seen[0].log, 'function');
  assert.equal(typeof seen[0].alert, 'function');
  assert.equal(typeof given.review, 'function', 'the tick still gets its handlers');
  const after = runTick({ raw: () => '', json: () => [] }, () => [], { run: g => g, gapNote: () => { throw new Error('disk full'); } });
  assert.equal(typeof after.review, 'function');
});
