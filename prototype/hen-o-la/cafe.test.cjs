'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const Q = require('./cafe.js');
const H = require('./event.js');
const W = require('./world.js');

test('random names are a Lá plus a mood, never a guest name from the matchmaking evening', () => {
  let i = 0; const rand = () => (i++ % 7) / 7;
  for (let k = 0; k < 50; k++) {
    const n = Q.randomName(rand);
    assert.match(n, /^Lá \S+( \S+)? \S+ \S+$/);
    assert.ok(!H.GUESTS.some(g => g.name === n));
  }
});

test('the small hours are empty, mornings and evenings are busier', () => {
  assert.equal(Q.crowd(3), 0);
  assert.ok(Q.crowd(7) >= 4);
  assert.ok(Q.crowd(21) >= 4);
  assert.ok(Q.crowd(15) < Q.crowd(21));
  assert.equal(Q.crowd(-1), Q.crowd(23));
  assert.match(Q.crowdLabel(0), /chỉ có Cô Lá/);
  for (let h = 0; h < 24; h++) assert.ok(Q.crowd(h) <= 5, 'the café stays small');
});

test('card of the day is the same all day and changes across days', () => {
  assert.deepEqual(Q.dailyCard('2026-11-08'), Q.dailyCard('2026-11-08'));
  const seen = new Set();
  for (let d = 1; d <= 30; d++) seen.add(Q.dailyCard('2026-11-' + String(d).padStart(2, '0')).card);
  assert.ok(seen.size >= 6);
  assert.equal(Q.dateKey(new Date(2026, 10, 8)), '2026-11-08');
});

test('cards and Cô Lá only suggest small things; they never predict or judge', () => {
  const lines = [...Q.CARDS.map(c => c.todo), ...Object.values(Q.HOST).flat()];
  for (const l of lines) assert.doesNotMatch(l, /sẽ (gặp|có|đến)|định mệnh|số phận|may mắn|xui|vận|người ấy|chữa|khỏi bệnh/i, l);
  assert.equal(new Set(Q.CARDS.map(c => c.card)).size, Q.CARDS.length);
});

test('time bands cover every hour', () => {
  for (let h = 0; h < 24; h++) assert.ok(Q.HOST[Q.band(h)].length >= 2, String(h));
});

test('greetings are the only speech, short and preset', () => {
  assert.ok(Q.GREETINGS.length >= 3);
  for (const g of Q.GREETINGS) assert.ok(Array.from(g).length <= 40);
});

test('self notes are trimmed, single-line and capped', () => {
  assert.equal(Q.sanitizeNote('  hôm nay\n\nổn '), 'hôm nay ổn');
  assert.equal(Array.from(Q.sanitizeNote('ơ'.repeat(90))).length, Q.NOTE_MAX);
  assert.equal(Q.sanitizeNote(undefined), '');
});

test('every visit act is something the café can host', () => {
  for (const a of Q.VISIT_ACTS) {
    if (Q.PLACE_ACTS[a]) continue;
    assert.ok(H.ACTS[a], a);
    assert.ok(Object.values(W.SPOTS).some(s => s.act === a), a + ' has a spot');
  }
  let i = 0; const rand = () => (i++ % 5) / 5;
  const plan = Q.visitPlan(rand);
  assert.ok(plan.length >= 2 && plan.length <= 4);
});

test('the café exports nothing that keeps score', () => {
  for (const k of Object.keys(Q)) assert.doesNotMatch(k, /point|score|streak|merit|reward|xp/i);
});

test('what people bring is only a look and a quiet thing to do', () => {
  let i = 0; const rand = () => (i++ * 0.37) % 1;
  for (let k = 0; k < 40; k++) {
    const g = Q.packBag(rand);
    assert.ok(Q.THINGS[g.thing], g.thing);
    assert.ok(Q.BAGS[g.bag], g.bag);
    assert.match(g.color, /^#[0-9a-f]{6}$/);
    assert.equal(typeof g.umbrella, 'boolean');
  }
  for (const t of Object.values(Q.THINGS)) assert.ok(t.label && t.icon && t.verb);
  for (const k of [...Object.keys(Q.THINGS), ...Object.keys(Q.BAGS)]) assert.doesNotMatch(k, /vip|premium|gia|price|coin/i);
});

test('the after-hours evening stays mild: every eerie beat ends in a funny reveal', () => {
  assert.ok(Q.NIGHT.beats.length >= 4);
  for (const b of Q.NIGHT.beats) {
    assert.ok(b.scare && b.reveal, 'each beat has a reveal');
    assert.doesNotMatch(b.scare + b.reveal, /máu|chết|giết|xác|ma quỷ|nhấp nháy|hét/i);
  }
  assert.ok(Q.NIGHT.dimCap.nhe < Q.NIGHT.dimCap.vua && Q.NIGHT.dimCap.vua < 0.8, 'the room never goes fully dark');
});

test('café-only acts have a label and icon, and the dog is a café pet with a name', () => {
  for (const [k, a] of Object.entries(Q.PLACE_ACTS)) assert.ok(a.label && a.icon, k);
  assert.ok(Q.VISIT_ACTS.includes('cuaso') && Q.VISIT_ACTS.includes('nam') && Q.VISIT_ACTS.includes('vuotcho'));
  assert.equal(Q.DOG.kind, 'chó');
});
