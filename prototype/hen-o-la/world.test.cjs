'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const W = require('./world.js');
const H = require('./event.js');
const E = require('../game-lab-14/engine.js');

test('café map is rectangular and walled top and bottom', () => {
  for (const row of W.MAP) assert.equal(row.length, W.W);
  assert.equal(W.MAP.length, W.H);
  for (let x = 0; x < W.W; x++) { assert.ok(W.solidTile(x, 0)); assert.ok(W.solidTile(x, W.H - 1)); }
});

test('every spot is furniture, unlocks a real act and is reachable from the door', () => {
  for (const [name, s] of Object.entries(W.SPOTS)) {
    assert.ok(W.solidTile(s.tx, s.ty), name);
    assert.ok(H.ACTS[s.act] && H.ACTS[s.act].at, name + ' act');
    assert.ok(W.standTiles(s.tx, s.ty).some(t => W.findPath(W.ENTRY, t)), name + ' unreachable');
  }
  for (const act of Object.keys(H.ACTS).filter(k => H.ACTS[k].at)) assert.ok(Object.values(W.SPOTS).some(s => s.act === act), act + ' has no spot');
});

test('enough reachable two-seat tables for every pair of a ten-guest evening', () => {
  assert.ok(W.TABLES.length >= 5);
  const seats = new Set();
  for (const t of W.TABLES) {
    assert.equal(W.tileAt(t.tx, t.ty), 'T');
    for (const s of t.seats) { assert.ok(!W.solidTile(...s)); assert.ok(W.findPath(W.ENTRY, s)); seats.add(s.join(',')); }
  }
  assert.equal(seats.size, W.TABLES.length * 2, 'no seat is shared by two tables');
});

test('spotAt finds the spot whose stand tile you are on', () => {
  assert.equal(W.spotAt(1, 8), 'piano');
  assert.equal(W.spotAt(13, 6), 'cat');
  assert.equal(W.spotAt(7, 5), null);
});

test('sliding drops only the blocked axis', () => {
  const body = { x: 16 * 6 + 4, y: 16 * 2 + 1, w: 8, h: 5 }; // just under the window wall
  const moved = W.moveWithSlide(body, 3, -4);
  assert.equal(moved.x, body.x + 3);
  assert.equal(moved.y, body.y);
});

test('every guest and every player look renders with the lab 14 sprite builder', () => {
  for (const look of [...H.GUESTS.map(g => g.look), ...H.LOOKS]) {
    const sheet = E.buildSheet(look);
    assert.equal(Object.keys(sheet).length, 24);
  }
});

test('window benches, the reading nook and the dog bed are free, reachable and not shared with table seats', () => {
  const tableSeats = new Set(W.TABLES.flatMap(t => t.seats).map(s => s.join(',')));
  for (const s of [...W.WINDOW_SEATS, ...W.NOOK, W.DOG_BED]) {
    assert.ok(!W.solidTile(...s), s.join(','));
    assert.ok(W.findPath(W.ENTRY, s), s.join(',') + ' unreachable');
    assert.ok(!tableSeats.has(s.join(',')), s.join(',') + ' is a table seat');
  }
  for (const [x, y] of W.WINDOW_SEATS) assert.equal(W.tileAt(x, y - 1), 'w', 'a window bench sits under a window');
});
