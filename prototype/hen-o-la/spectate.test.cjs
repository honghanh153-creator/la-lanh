'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const X = require('./spectate.js');
const H = require('./event.js');

test('the mezzanine is small: a short queue moves one by one, then you sit', () => {
  for (let k = 0; k < 10; k++) {
    const r = k / 10;
    let s = X.arrive(() => r);
    assert.ok(s.seated ? s.free > 0 : s.ahead >= 1);
    let steps = 0;
    while (!s.seated) { s = X.queueStep(s); steps++; }
    assert.ok(steps <= 4, 'queue stays short');
  }
  assert.ok(X.SEATS >= 30 && X.SEATS <= 50);
});

test('guests only watch shared moments, never private ones', () => {
  const ids = X.MOMENTS.map(m => m.id);
  for (const p of X.PRIVATE) assert.ok(!ids.includes(p), p);
  for (const id of ids) assert.ok(id === 'taihien' || H.PHASES.some(p => p.id === id), id);
});

test('cheering has no target', () => {
  assert.equal(X.cheer.length, 1, 'cheer(kind) takes no person');
  assert.deepEqual(X.cheer('votay'), { kind: 'votay', forMoment: true });
  assert.equal(X.cheer('someone'), null);
});

test("Cô Lá's notes never say who", () => {
  const names = H.GUESTS.map(g => g.name).concat(H.GUESTS.map(g => g.name.replace(/^Lá /, '')));
  for (const n of X.HOST_NOTES) {
    assert.match(n, /^Có (người|hai người)/, n);
    assert.doesNotMatch(n, /\d/, n);
    for (const g of names) assert.ok(!n.includes(g), g + ' in ' + n);
  }
  let i = 0; const rand = () => (i++ * 0.31) % 1;
  const three = X.hostNotes(rand, 3);
  assert.equal(new Set(three).size, 3);
});

test('lanterns are only a count', () => {
  for (const r of [0, 0.5, 0.99]) { const n = X.lanternPairs(() => r); assert.ok(Number.isInteger(n) && n >= 1 && n <= 3); }
  for (const k of Object.keys(X)) assert.doesNotMatch(k, /who|watcher|viewer|score|point|streak/i);
});
