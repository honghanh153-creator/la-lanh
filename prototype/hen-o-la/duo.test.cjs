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
