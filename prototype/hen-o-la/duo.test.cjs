'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const D = require('./duo.js');
const H = require('./event.js');

test('every round has exactly one extra line, and one photo alone is not enough in round 2', () => {
  for (const r of D.ROUNDS) assert.equal(D.candidates(r, D.photoCounts(r)).length, 1, r.id);
  const r2 = D.ROUNDS[1];
  for (const f of r2.fields) {
    const only = { ...r2, fields: [f] };
    assert.ok(D.candidates(only, D.photoCounts(r2)).length > 1, f + ' alone must stay ambiguous');
  }
});

test('the photos show every line except the extra one', () => {
  for (const r of D.ROUNDS) {
    const x = D.extraOf(r);
    for (const f of r.fields) assert.deepEqual(D.tally(r, f, x), D.photoCounts(r)[f].slice(0, D.FIELDS[f].labels.length));
  }
});

test('the extra line is a fictional record, never a guest or player name', () => {
  for (const n of D.NAMES) assert.ok(!H.GUESTS.some(g => g.name.includes(n)), n);
});

test('roles swap between rounds and each blank belongs to one teammate', () => {
  assert.notEqual(D.ROUNDS[0].photo, D.ROUNDS[1].photo);
  for (const r of D.ROUNDS) {
    const owners = new Set(D.blanks(r).map(b => b.owner));
    assert.deepEqual([...owners].sort(), ['mate', 'you'], r.id + ': nobody can answer alone');
  }
});

test('judge needs both locks and gives one shared sentence when wrong', () => {
  const r = D.ROUNDS[0];
  const right = { name: D.NAMES[D.extraOf(r)], cup: D.FIELDS.cup.labels[r.rows.cup[D.extraOf(r)]] };
  assert.equal(D.judge(r, right, { you: true }).status, 'waiting');
  assert.equal(D.judge(r, right, { you: true, mate: true }).status, 'solved');
  const wrongName = D.judge(r, { ...right, name: 'An' }, { you: true, mate: true });
  const wrongCup = D.judge(r, { ...right, cup: 'Trà' }, { you: true, mate: true });
  assert.equal(wrongName.status, 'retry');
  assert.equal(wrongName.text, wrongCup.text, 'the sentence never says which blank or who');
  assert.equal(D.judge(r, { name: 'An' }, { you: true, mate: true }).status, 'incomplete');
});

test('the teammate only concludes from what your note says', () => {
  const r = D.ROUNDS[0];
  assert.equal(D.mateNameFromCounts(r, D.photoCounts(r)), D.NAMES[D.extraOf(r)]);
  assert.equal(D.mateNameFromCounts(r, { cup: [2, 2, 1] }), null, 'a miscount gives no name rather than a wrong one');
  const r2 = D.ROUNDS[1];
  const x = D.NAMES[D.extraOf(r2)];
  assert.equal(D.mateReasonFor(r2, x).fits, true);
  assert.equal(D.mateReasonFor(r2, D.NAMES.find(n => n !== x)).fits, false);
});

test('the team plays at the gentler courage level', () => {
  assert.equal(D.teamCourage('vua', 'nhe'), 'nhe');
  assert.equal(D.teamCourage('nhe', 'vua'), 'nhe');
  assert.equal(D.teamCourage('vua', 'vua'), 'vua');
});

test('going on together needs two yeses and never says who said no', () => {
  assert.equal(D.together(true, true).status, 'tiep');
  assert.equal(D.together(true, false).text, D.together(false, true).text);
  assert.equal(D.together(false, false).text, D.together(true, false).text);
});

test('break questions are optional, gentle and have answers; nothing keeps score', () => {
  for (const q of D.QUESTIONS) assert.ok(D.MATE_ANSWERS[q], q);
  for (const k of Object.keys(D)) assert.doesNotMatch(k, /score|point|rank(?!s)|streak|xp/i);
  for (const m of Object.values(D.MODES)) assert.doesNotMatch(m.intro + m.reveal, /máu|chết|giết|xác/i);
});

test('L2 mirror: the photo read as-is matches nobody; read through the mirror it matches one line', () => {
  const g1 = D.L2[0];
  assert.equal(D.candidates(g1, D.photoCounts(g1)).length, 1);
  assert.equal(D.candidates(g1, D.seenCounts(g1)).length, 0, 'forgetting the mirror gives no line');
  assert.notDeepEqual(D.seenCounts(g1).handle, D.photoCounts(g1).handle);
  assert.ok(D.candidates({ ...g1, fields: ['cup'] }, D.photoCounts(g1)).length > 1, 'cups alone are not enough');
  assert.equal(D.mateNameFromCounts(g1, D.seenCounts(g1)), null);
  assert.equal(D.mateNameFromCounts(g1, D.photoCounts(g1)), D.NAMES[D.extraOf(g1)]);
});

test('L2 route: the one-way back door is what makes exactly one line impossible', () => {
  const g2 = D.L2[1];
  assert.equal(D.candidates(g2).length, 1);
  assert.equal(D.candidates(g2, { ignoreOneWay: true }).length, 0, 'treating the door as two-way finds nothing');
  const exp = D.answerOf(g2);
  assert.ok(Number(exp.shortest) > Number(exp.logged));
  assert.equal(D.mateLogged(g2, exp.name), exp.logged);
  assert.equal(D.logLines(g2).length, 6);
  const owners = new Set(D.blanks(g2).map(b => b.owner));
  assert.deepEqual([...owners].sort(), ['mate', 'you']);
  const right = { ...exp };
  assert.equal(D.judge(g2, right, { you: true, mate: true }).status, 'solved');
  assert.equal(D.judge(g2, { ...right, shortest: '1' }, { you: true, mate: true }).status, 'retry');
});

test('levels chain and later questions stay optional with answers', () => {
  assert.equal(D.LEVELS[1], D.ROUNDS);
  assert.equal(D.LEVELS[2], D.L2);
  for (const q of D.QUESTIONS_L2) assert.ok(D.MATE_ANSWERS[q], q);
  for (const r of D.L2) assert.ok(r.method && !/An|Bình|Chi|Duy|Hà|Linh/.test(r.method), 'method cards never name a line');
});

// Controller timing (review of #319 @ bbe0886): the confirmation flow must neither stall nor settle twice.
function run(events, mateReadyAtStart) {
  let st = D.newConfirm(mateReadyAtStart), judged = 0;
  for (const ev of events) {
    const out = D.confirmStep(st, ev);
    st = out.state;
    if (out.judge) { judged++; st = D.confirmStep(st, 'solved').state; }
  }
  return { st, judged };
}

test('an early Chốt before the teammate has filled their half does not stall', () => {
  const r = run(['youLock', 'mateReady']);
  assert.equal(r.judged, 1, 'the teammate locks when their half arrives and the round is judged once');
});

test('Chốt after the teammate is ready settles at once; repeated Chốt never settles twice', () => {
  assert.equal(run(['mateReady', 'youLock']).judged, 1);
  assert.equal(run(['mateReady', 'youLock', 'youLock', 'youLock', 'mateReady']).judged, 1);
  assert.equal(run(['youLock', 'youLock', 'mateReady', 'youLock']).judged, 1);
});

test('editing the sentence or a wrong answer releases both locks; nothing moves after settling', () => {
  let st = D.newConfirm(true);
  st = D.confirmStep(st, 'answerChanged').state;
  assert.deepEqual(st.locks, {});
  st = D.confirmStep(D.newConfirm(false), 'youLock').state;
  st = D.confirmStep(st, 'mateNotReady').state;
  assert.equal(!!st.locks.mate, false);
  const retry = D.confirmStep({ locks: { you: true, mate: true }, mateReady: true, settled: false }, 'retry');
  assert.deepEqual(retry.state.locks, {});
  const after = D.confirmStep({ locks: { you: true, mate: true }, mateReady: true, settled: true }, 'youLock');
  assert.equal(after.judge, false);
  // after a wrong answer, locking again with the teammate still ready is judged again exactly once
  assert.equal(D.confirmStep(retry.state, 'youLock').judge, true);
});
