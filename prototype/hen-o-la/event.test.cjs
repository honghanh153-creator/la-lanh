'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const H = require('./event.js');

const YOU = { name: 'Lá Mít', item: 'sổ tay', lantern: 'thuong', look: H.LOOKS[0] };
const evening = (seed = 7) => H.createEvening(seed, YOU);

test('ten guests with unique ids and nicknames, all fictional Lá names', () => {
  const ev = evening();
  assert.equal(ev.people.length, 10);
  assert.equal(new Set(ev.ids).size, 10);
  assert.equal(new Set(ev.people.map(p => p.name)).size, 10);
  for (const p of ev.people) assert.match(p.name, /^Lá /);
  for (const n of H.NICKNAMES) assert.ok(!H.GUESTS.some(g => g.name === n), n + ' clashes with a guest');
});

test('rotation: four rounds, everyone seated once per round, nobody meets twice', () => {
  const ev = evening();
  assert.equal(ev.rounds.length, 4);
  const met = new Set();
  for (const round of ev.rounds) {
    const inRound = round.flat();
    assert.equal(inRound.length, 10);
    assert.equal(new Set(inRound).size, 10);
    for (const [a, b] of round) { const k = [a, b].sort().join('+'); assert.ok(!met.has(k), k); met.add(k); }
  }
  // odd counts give one person a break instead of a repeat
  const odd = H.rotation(['a', 'b', 'c'], 2);
  for (const r of odd) assert.equal(r.length, 1);
});

test('tarot halves: every card is held by exactly two people who point at each other', () => {
  const ev = evening(3);
  const byCard = {};
  for (const [id, h] of Object.entries(ev.halves)) (byCard[h.card] = byCard[h.card] || []).push(id);
  for (const ids of Object.values(byCard)) {
    assert.equal(ids.length, 2);
    assert.equal(ev.halves[ids[0]].mate, ids[1]);
    assert.equal(ev.halves[ids[1]].mate, ids[0]);
  }
  const mate = ev.halves.you.mate;
  assert.equal(H.compareHalves(ev, 'you', mate).match, true);
  const other = ev.ids.find(id => id !== 'you' && id !== mate);
  assert.equal(H.compareHalves(ev, 'you', other).match, false);
});

test('tarot topics never predict anything about the person', () => {
  for (const t of H.TAROT) assert.doesNotMatch(t.q, /định mệnh|hợp nhau|số phận|sẽ yêu/i);
});

test('seeing a loved act counts once, more than an ordinary act', () => {
  const ev = evening();
  const npc = ev.people.find(p => p.npc);
  const loved = npc.loves[0], plain = H.FREE_ACTS.find(a => !npc.loves.includes(a));
  assert.ok(H.observe(ev, npc.id, 'you', loved));
  assert.ok(!H.observe(ev, npc.id, 'you', loved), 'second sighting of the same act does not count');
  assert.equal(ev.aff[npc.id].you, 2);
  H.observe(ev, npc.id, 'you', plain);
  assert.equal(ev.aff[npc.id].you, 2.5);
  assert.ok(!H.observe(ev, 'you', 'you', 'nhay'));
});

test('leaves are anonymous: they never raise anyone’s feeling toward the sender, and are capped', () => {
  const ev = evening();
  const before = JSON.stringify(ev.aff);
  const npcs = ev.ids.filter(id => id !== 'you');
  let sent = 0;
  for (const id of npcs) if (H.dropLeaf(ev, 'you', id)) sent++;
  assert.equal(sent, H.LEAF_LIMIT);
  assert.equal(JSON.stringify(ev.aff), before);
  assert.equal(H.dropLeaf(ev, 'you', 'you'), false);
  assert.equal(H.dropLeaf(ev, 'you', npcs[0]), false, 'one leaf per person');
});

test('letters must name something the writer actually saw, carry no sender, and are capped', () => {
  const ev = evening();
  const [a, b, c, d, e] = ev.ids.filter(id => id !== 'you');
  assert.equal(H.writeLetter(ev, 'you', a, 'nhay', 'vui lây'), false, 'not seen yet');
  for (const t of [a, b, c, d, e]) H.observe(ev, 'you', t, 'nhay');
  assert.ok(H.writeLetter(ev, 'you', a, 'nhay', 'vui lây'));
  assert.equal(H.writeLetter(ev, 'you', a, 'nhay', 'vui lây'), false, 'one letter per person');
  assert.ok(H.writeLetter(ev, 'you', b, 'nhay', 'vui lây'));
  assert.ok(H.writeLetter(ev, 'you', c, 'nhay', 'vui lây'));
  assert.equal(H.writeLetter(ev, 'you', d, 'nhay', 'vui lây'), false, 'three letters max');
  for (const l of ev.letters[a]) assert.deepEqual(Object.keys(l).sort(), ['act', 'adj']);
  assert.match(H.letterText(ev.letters[a][0]), /^Có người thấy bạn nhảy/);
});

test('guest letters only mention acts that guest saw', () => {
  const ev = evening(11);
  const npc = ev.people.find(p => p.npc);
  H.observe(ev, npc.id, 'you', 'vaytay');
  H.npcLetters(ev);
  for (const l of ev.letters.you) assert.ok([...ev.ids].some(id => id !== 'you' && ev.seen[id].you.has(l.act)));
  assert.ok(ev.letters.you.length >= 1);
});

test('final pairs are mutual, one per person, and only both-🌸 pairs are called a date', () => {
  const ev = evening();
  const [a, b, c, d] = ev.ids.filter(id => id !== 'you');
  const picks = { you: [a, b], [a]: ['you', c], [b]: ['you'], [c]: [a], [d]: ['you'] };
  const res = H.couples(ev, picks);
  const flat = res.flatMap(p => [p.a, p.b]);
  assert.equal(new Set(flat).size, flat.length);
  for (const p of res) {
    assert.ok(picks[p.a].includes(p.b) && picks[p.b].includes(p.a));
    const both = H.person(ev, p.a).lantern === 'thuong' && H.person(ev, p.b).lantern === 'thuong';
    assert.equal(p.kind, both ? 'hen' : 'ban');
  }
  assert.ok(res.some(p => [p.a, p.b].includes('you') && [p.a, p.b].includes(a)), 'first choice on both sides wins');
  assert.ok(!flat.includes(d), 'one-sided pick never pairs');
});

test('guests pick nobody they barely know; ghé-chơi guests need a stronger pull', () => {
  const ev = evening();
  for (const id of ev.ids) if (id !== 'you') assert.deepEqual(H.npcPicks(ev, id), []);
  const choi = ev.people.find(p => p.lantern === 'choi');
  ev.aff[choi.id].you = 4;
  assert.deepEqual(H.npcPicks(ev, choi.id), []);
  ev.aff[choi.id].you = 5;
  assert.deepEqual(H.npcPicks(ev, choi.id), ['you']);
});

test('table round rewards shared taste and answering, and names the drink', () => {
  const ev = evening();
  const npc = ev.people.find(p => p.npc);
  const name = H.tableRound(ev, 'you', npc.id, npc.taste[0], npc.taste[0], true, true);
  assert.equal(ev.aff[npc.id].you, 4);
  assert.equal(name, H.INGREDIENTS[npc.taste[0]] + ' gấp đôi');
  assert.equal(H.npcIngredient(ev, npc.id, ['muoi', npc.taste[1]]), npc.taste.includes('muoi') ? 'muoi' : npc.taste[1]);
});

test('speech bubbles are trimmed, single-line, plain text and capped at 40 characters', () => {
  assert.equal(H.sanitizeBubble('  xin\n\nchào\t '), 'xin chào');
  assert.equal(Array.from(H.sanitizeBubble('ả'.repeat(60))).length, 40);
  assert.equal(H.sanitizeBubble(null), '');
});

test('guest lines carry no numbers, places of residence or contact hints', () => {
  for (const g of H.GUESTS) for (const line of [...g.idle, ...g.answer, ...g.last]) {
    assert.doesNotMatch(line, /\d|@|zalo|facebook|số điện thoại|nhà mình ở/i, g.id + ': ' + line);
  }
});

test('same seed, same evening', () => {
  const a = evening(42), b = evening(42);
  assert.deepEqual(a.ids, b.ids);
  assert.deepEqual(a.rounds, b.rounds);
  assert.deepEqual(a.halves, b.halves);
});

test('openers and reactions are short, ask nothing private, and every guest act exists', () => {
  for (const line of [...H.OPENERS, ...H.REACTIONS]) {
    assert.ok(Array.from(line).length <= 40, line);
    assert.doesNotMatch(line, /\d|@|zalo|facebook|số điện thoại|nhà ở đâu|ở đâu|bao nhiêu tuổi/i, line);
  }
  for (const g of H.GUESTS) for (const a of [...g.does, ...g.loves]) assert.ok(H.ACTS[a], g.id + ' ' + a);
  for (const a of H.PLACE_ACTS) assert.ok(!H.FREE_ACTS.includes(a) && !H.ACTS[a].at, a);
});

test('every carried item has something to put on the table', () => {
  const kinds = new Set(['sove', 'mayanh', 'len', 'sach', 'tainghe', 'banh', 'xuongrong', 'ukulele', 'dieu']);
  for (const item of [...H.ITEMS, ...H.GUESTS.map(g => g.item)]) assert.ok(kinds.has(H.itemThing(item)), item);
  assert.equal(H.itemThing('máy ảnh film'), 'mayanh');
  assert.equal(H.itemThing('diều giấy'), 'dieu');
});

test('the shared seat rule: every free gesture keeps you seated, place acts get you up (fix-forward #320)', () => {
  // Every free gesture is one you can make from a chair (README: they do not make you stand up).
  assert.deepEqual([...H.SEATED_GESTURES].sort(), [...H.FREE_ACTS].sort());
  for (const act of H.FREE_ACTS) assert.equal(H.keepsSeat(act), true, act);
  for (const act of ['docsach', 'tuoicay', 'goido', 'vuotcho', 'nam']) assert.equal(H.keepsSeat(act), false, act + ' gets you up');
});

// Runs a page controller (game.js / quan.js) in node with an inert DOM, so tests drive its real
// action path through the window.__hen / window.__quan hooks instead of copying its logic.
function loadController(file) {
  const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
  const handler = {
    get(t, k) {
      if (k === Symbol.toPrimitive) return hint => (hint === 'number' ? 0 : '');
      if (k === Symbol.iterator) return function* () {};
      if (k === 'length') return 0;
      if (k === 'then') return undefined;
      if (!Object.prototype.hasOwnProperty.call(t, k)) t[k] = node();
      return t[k];
    },
    apply: () => node(),
    construct: () => node()
  };
  function node() { return new Proxy(function () {}, handler); }
  const document = node();
  document.hidden = false;
  const math = Object.create(Math);
  math.random = H.rng(7);
  const g = {
    console, Math: math, URLSearchParams, document, location: { search: '' },
    performance: { now: () => 0 }, setTimeout: () => 0, clearTimeout() {}, requestAnimationFrame: () => 0,
    matchMedia: () => ({ matches: false, addEventListener() {} }), addEventListener() {}, devicePixelRatio: 1
  };
  g.window = g;
  vm.createContext(g);
  for (const f of ['../game-lab-14/engine.js', 'world.js', 'room.js', 'life.js', 'event.js', 'cafe.js', file]) {
    const full = path.join(__dirname, f);
    vm.runInContext(fs.readFileSync(full, 'utf8'), g, { filename: full });
  }
  return g;
}
const seatState = b => ({ sit: b.sit, seatKind: b.seatKind, task: b.task, locked: b.locked });

test('dancing at a locked rotation seat keeps you seated (game.js, fix-forward #320/#324)', () => {
  const hen = loadController('game.js').__hen;
  hen.begin();
  hen.next(); // Màn 2: the host locks everyone to a rotation seat
  assert.equal(hen.phase(), 'xoayban');
  for (let i = 0; i < 40 && !hen.me().sit; i++) hen.step(250);
  hen.act('layra');
  const before = seatState(hen.me());
  assert.deepEqual(before, { sit: true, seatKind: 'table', task: true, locked: true });
  hen.act('nhay');
  assert.equal(hen.me().act, 'nhay', 'the dance actually ran');
  assert.deepEqual(seatState(hen.me()), before);
});

test('dancing at a table seat keeps you seated with your things out (quan.js, fix-forward #320/#324)', () => {
  const quan = loadController('quan.js').__quan;
  const W = require('./world.js');
  const [tx, ty] = W.TABLES[0].seats[0];
  for (const b of quan.people.values()) if (b.npc) quan.people.delete(b.id); // keep the seat free
  assert.ok(quan.walkTo(tx, ty) !== false);
  for (let i = 0; i < 40 && quan.me().path; i++) quan.step(250);
  quan.act('ngoi');
  quan.act('lamviec');
  quan.me().locked = true; // the café has no rotation lock; dancing must still leave the flag alone
  const before = seatState(quan.me());
  assert.deepEqual(before, { sit: true, seatKind: 'table', task: true, locked: true });
  quan.act('nhay');
  assert.equal(quan.me().act, 'nhay', 'the dance actually ran');
  assert.deepEqual(seatState(quan.me()), before);
});
