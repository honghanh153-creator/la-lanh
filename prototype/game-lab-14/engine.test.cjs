'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('./engine.js');
const C = require('./cases.js');

test('map is rectangular and walled', () => {
  for (const row of E.MAP) assert.equal(row.length, E.W);
  assert.equal(E.MAP.length, E.H);
  for (let x = 0; x < E.W; x++) { assert.ok(E.solidTile(x, 0)); assert.ok(E.solidTile(x, E.H - 1)); }
});

test('every spot is solid furniture and reachable from the player start', () => {
  for (const [name, s] of Object.entries(E.SPOTS)) {
    assert.ok(E.solidTile(s.tx, s.ty), name + ' must be furniture');
    const stands = E.standTiles(s.tx, s.ty);
    assert.ok(stands.length, name + ' has no free neighbour');
    assert.ok(stands.some(t => E.findPath(E.PLAYER_START, t)), name + ' unreachable');
  }
});

test('every source of every case maps to a spot', () => {
  for (const c of C.cases) for (const s of c.sources) assert.ok(E.SPOTS[E.SOURCE_SPOT[s]], c.id + ':' + s);
});

test('record avatars stand on free tiles and do not block any spot', () => {
  const npc = new Set(E.NPC_HOME.map(([x, y]) => x + ',' + y));
  const blocked = (x, y) => npc.has(x + ',' + y);
  for (const [x, y] of E.NPC_HOME) assert.ok(!E.solidTile(x, y));
  for (const [name, s] of Object.entries(E.SPOTS)) {
    const stands = E.standTiles(s.tx, s.ty, null, blocked);
    assert.ok(stands.some(t => E.findPath(E.PLAYER_START, t, blocked)), name + ' blocked by avatars');
  }
  for (const [x, y] of E.NPC_HOME) {
    const stands = E.standTiles(x, y, null, blocked);
    assert.ok(stands.some(t => E.findPath(E.PLAYER_START, t, blocked)), 'avatar at ' + x + ',' + y + ' unreachable');
  }
});

test('sliding: blocked axis is dropped, free axis still moves', () => {
  const body = { x: 16 * 1 + 4, y: 16 * 2 + 1, w: 8, h: 5 }; // just below the wall row
  const moved = E.moveWithSlide(body, 3, -4, []);
  assert.equal(moved.x, body.x + 3);
  assert.equal(moved.y, body.y);
});

test('velocity ramps up and down within a few frames', () => {
  let v = 0;
  for (let i = 0; i < 6; i++) v = E.stepVelocity(v, 1, 1 / 60);
  assert.equal(v, E.MOVE.speed);
  for (let i = 0; i < 4; i++) v = E.stepVelocity(v, 0, 1 / 60);
  assert.equal(v, 0);
});

test('sprite templates are 12 x 16 and outlined sprites are 14 x 18 for every look', () => {
  for (const d of E.DIRS) for (const f of ['stand', 'a', 'b']) {
    const rows = E.template(d, f, {});
    assert.equal(rows.length, 16);
    for (const r of rows) assert.equal(r.length, 12, d + f);
  }
  for (const [name, look] of Object.entries(E.LOOKS)) {
    const sheet = E.buildSheet(look);
    assert.equal(Object.keys(sheet).length, 24, name);
    for (const spr of Object.values(sheet)) { assert.equal(spr.w, 14); assert.equal(spr.h, 18); }
  }
});

test('blink frames differ from open-eye frames only in the eyes', () => {
  const open = E.template('down', 'stand', {}), shut = E.template('down', 'stand', { blink: true });
  const diff = open.flatMap((r, y) => r.split('').map((c, x) => (c !== shut[y][x] ? c : null))).filter(Boolean);
  assert.deepEqual([...new Set(diff)], ['E']);
});

test('walk cycle alternates feet', () => {
  assert.deepEqual([0, 130, 260, 390, 520].map(E.walkFrame), ['a', 'stand', 'b', 'stand', 'a']);
});
