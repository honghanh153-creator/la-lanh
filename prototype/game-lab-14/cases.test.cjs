'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const C = require('./cases.js');

const expected = { p1: 'ha', r1: 'chi', p2: 'binh', r2: 'duy', p4: 'an', r4: 'linh', x1: 'ha' };

test('every case has exactly one candidate from its sources', () => {
  for (const c of C.cases) assert.deepEqual(C.candidates(c), [expected[c.id]], c.id);
});

test('answers rotate: no two consecutive cases share an answer', () => {
  const seq = C.cases.map(c => C.candidates(c)[0]);
  for (let i = 1; i < seq.length; i++) assert.notEqual(seq[i], seq[i - 1]);
  assert.ok(new Set(seq).size >= 6);
});

test('photo cases need every listed board', () => {
  for (const c of C.cases.filter(c => c.kind === 'photo' && c.sources.length > 1)) {
    for (const drop of c.sources) {
      const partial = { ...c, sources: c.sources.filter(s => s !== drop) };
      assert.ok(C.candidates(partial).length > 1, c.id + ' without ' + drop);
    }
  }
});

test('P4 mirror trap: reading the mirror literally gives no answer', () => {
  const c = C.cases.find(x => x.id === 'p4');
  const literal = { ...c, proof: { ...c.proof, ticket: C.seenProof(c, 'ticket') } };
  assert.deepEqual(C.candidates(literal), []);
});

test('R4 trap: ignoring the one-way door gives three candidates, two-way door gives none', () => {
  const c = C.cases.find(x => x.id === 'r4');
  const noDoor = { ...c, graph: 'linearPlusCorridor' };
  C.graphs.linearPlusCorridor = C.graphs.branched.filter(e => !e[3]);
  assert.deepEqual(C.candidates(noDoor).sort(), ['an', 'binh', 'linh']);
  C.graphs.twoWay = C.graphs.branched.map(e => e.slice(0, 3));
  assert.deepEqual(C.candidates({ ...c, graph: 'twoWay' }), []);
});

test('R2 needs the checkpoint; X1 needs the photo', () => {
  const r2 = C.cases.find(x => x.id === 'r2');
  assert.deepEqual(C.candidates({ ...r2, checkpoint: undefined }), []);
  const x1 = C.cases.find(x => x.id === 'x1');
  const timeOnly = x1.rows.filter(r => C.earliest(x1, r.trip[0], r.trip[2]) > r.trip[3] - r.trip[1]);
  assert.deepEqual(timeOnly, []);
});

test('judge needs sources, right record and right reason; wrong answers get no hint', () => {
  for (const [i, c] of C.cases.entries()) {
    const ans = expected[c.id];
    const reason = C.expectedReason(c, ans);
    assert.equal(C.judge(c, c.sources.slice(1), ans, reason).status, 'insufficient');
    assert.equal(C.judge(c, c.sources, ans, reason).status, 'solved', c.id);
    const retries = new Set();
    for (const id of C.ids.filter(x => x !== ans)) {
      const r = C.judge(c, c.sources, id, reason);
      assert.equal(r.status, 'retry');
      retries.add(r.text);
    }
    const wrongReason = Object.fromEntries(Object.entries(reason).map(([k, v]) => [k, typeof v === 'number' ? v + 1 : 'x']));
    const wr = C.judge(c, c.sources, ans, wrongReason);
    assert.equal(wr.status, 'retry');
    retries.add(wr.text);
    assert.equal(retries.size, 1, 'same text for wrong record and wrong reason in ' + c.id);
    void i;
  }
});

test('expected reasons are the human explanation', () => {
  const byId = Object.fromEntries(C.cases.map(c => [c.id, c]));
  assert.deepEqual(C.expectedReason(byId.p1, 'ha'), { badge: 2 });
  assert.deepEqual(C.expectedReason(byId.r1, 'chi'), { minutes: 4 });
  assert.deepEqual(C.expectedReason(byId.r2, 'duy'), { minutes: 5 });
  assert.deepEqual(C.expectedReason(byId.r4, 'linh'), { minutes: 4 });
  assert.deepEqual(C.expectedReason(byId.x1, 'ha'), { presence: 'must', badge: 0 });
});

test('source checks never ask about the answer row and accept only the seen values', () => {
  for (const c of C.cases) {
    const ans = expected[c.id];
    for (const s of c.sources) {
      const chk = C.sourceCheck(c, s);
      assert.ok(chk, c.id + ':' + s);
      assert.ok(!chk.prompt.includes(C.nameOf(ans)), c.id + ':' + s + ' names the answer');
      assert.ok(C.checkSource(chk, chk.answer));
    }
  }
  const p4 = C.cases.find(x => x.id === 'p4');
  const chk = C.sourceCheck(p4, 'ticket');
  assert.deepEqual(chk.answer, [3, 2], 'player records what the mirror shows');
});

test('progress unlocks one case at a time and only on solved', () => {
  const p = C.createProgress();
  assert.equal(C.complete(p, 1, { status: 'solved' }), false);
  assert.equal(C.complete(p, 0, { status: 'retry' }), false);
  assert.equal(C.complete(p, 0, { status: 'solved' }), true);
  assert.equal(p.unlocked, 1);
});

test('method cards never name a record or a detective', () => {
  for (const c of C.cases) {
    const m = C.methodFor(c);
    for (const pr of C.profiles.concat(C.detectives)) assert.ok(!m.text.includes(pr.name + ' '), c.id);
  }
});

test('detective lines contain no case facts and no record names', () => {
  for (const d of C.detectives) for (const line of Object.values(d.lines).concat([d.help, d.hold])) {
    assert.ok(!/\d/.test(line), d.id);
    for (const n of C.nodes) assert.ok(!line.includes(n), d.id + ' mentions ' + n);
    for (const r of C.profiles) assert.ok(!new RegExp('(^|[^\\p{L}])' + r.name + '($|[^\\p{L}])', 'u').test(line), d.id + ' names record ' + r.name);
  }
});

test('records and detectives never share a name; every spot that gives a source has exactly one role owner', () => {
  const names = new Set(C.profiles.map(p => p.name));
  for (const d of C.detectives) assert.ok(!names.has(d.name));
  const roleIds = C.detectives.map(d => d.role);
  assert.equal(new Set(roleIds).size, roleIds.length);
  for (const spot of ['camera', 'mirror', 'poster', 'door', 'scanner', 'shelf', 'teacher', 'tarot']) assert.ok(C.ownerOfSpot(spot), spot);
  assert.equal(C.ownerOfSpot('terminal'), null);
});

test('co-op plates sit on free floor away from the spot they unlock', () => {
  const E = require('./engine.js');
  for (const c of C.cases.filter(x => x.plate)) {
    const [px, py] = c.plate.at, sp = E.SPOTS[c.plate.spot];
    assert.ok(!E.solidTile(px, py), c.id);
    for (const [sx, sy] of E.standTiles(sp.tx, sp.ty)) assert.ok(Math.abs(sx - px) + Math.abs(sy - py) >= 4, c.id + ' plate too close to its spot');
  }
});
