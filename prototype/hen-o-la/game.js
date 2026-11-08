// Hẹn ở Lá: one matchmaking evening in a rainy pixel café.
// Uses game lab 14's sprite builder (Engine) with this folder's café map (World) and rules (Hen).
(function () {
  'use strict';
  const H = window.Hen, W = window.World, E = window.Engine;
  const $ = id => document.getElementById(id);
  const T = W.TILE, VW = W.W * T, VH = W.H * T;
  const FAST = new URLSearchParams(location.search).has('nhanh');
  // "Quán sau giờ đóng cửa": the same evening after hours, mildly eerie (?buoi=dem).
  const NIGHT = new URLSearchParams(location.search).get('buoi') === 'dem' ? window.Quan.NIGHT : null;
  let courage = 'nhe', lightsOn = !NIGHT, dim = 0, beatAt = 0, beatIx = 0;
  if (NIGHT) {
    const link = $('nightLink'); link.textContent = '☕ Buổi thường'; link.href = 'index.html';
    document.querySelector('.brand span').textContent = NIGHT.title + ' · bản thử chạy trên máy · khách mời hư cấu 18+';
    document.title = 'Hẹn ở Lá · ' + NIGHT.title;
  }
  const DUR = FAST ? { tudo: 45, round: 25, lycuoi: 40 } : { tudo: 150, round: 50, lycuoi: 90 }; // seconds
  const SEE_TILES = 6; // guests notice what happens within this many tiles; bubbles further away show as "…"

  const canvas = $('game'), ctx = canvas.getContext('2d');
  const overlay = $('overlay');
  let scale = 1;

  let motion = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'reduced' : 'full';
  const fx = () => motion === 'full';
  const still = () => motion === 'off';

  // ---------- evening state ----------
  let seed = Math.floor(Math.random() * 1e9);
  let ev = null, you = null;
  let phase = 'loivao', clock = 0, phaseEnd = 0;
  let round = -1, roundState = null, couples = [], myPicks = [];
  const people = new Map(); // id -> runtime body
  const particles = [], lanterns = [];
  const host = { id: 'host', host: true, name: 'Cô Lá', x: W.HOST.tx * T + 8, y: W.HOST.ty * T + 7, dir: 'down', bubble: null, sheet: E.buildSheet({ H: '#2b2230', T: '#3f6b55', C: '#7fc8a0', P: '#30303a', B: '#1d1b26', longHair: true, hat: true }) };

  // Evening-scoped timers: a callback from an evening that was restarted never runs.
  let gen = 0;
  function later(ms, fn) { const g = gen; setTimeout(() => { if (g === gen && ev) fn(); }, ms); }
  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function btn(text, cls, fn) { const b = el('button', cls, text); b.type = 'button'; b.addEventListener('click', fn); return b; }
  function pick(list) { return list[Math.floor(Math.random() * list.length)]; }
  const fmt = s => { s = Math.max(0, Math.ceil(s)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };

  // ---------- bodies ----------
  function feetOf(tx, ty) { return { x: tx * T + 8, y: ty * T + 12 }; }
  function tileOf(p) { return [Math.floor(p.x / T), Math.floor((p.y - 1) / T)]; }
  function makeBody(p, tx, ty) {
    return Object.assign({ id: p.id, name: p.name, npc: p.npc, lantern: p.lantern, item: p.item, dir: 'down', path: null, then: null, act: null, actUntil: 0,
      bubble: null, walkMs: 0, moving: false, hop: 0, blinkAt: Math.random() * 4, nextIdea: 1 + Math.random() * 3, nextLine: 3 + Math.random() * 8,
      locked: false, seat: null, sheet: E.buildSheet(p.look) }, feetOf(tx, ty));
  }
  function spawnAll() {
    people.clear();
    const free = W.freeTiles().filter(([x, y]) => y >= 3 && y <= 8 && !W.spotAt(x, y) && !W.TABLES.some(t => t.seats.some(s => s[0] === x && s[1] === y)));
    const spots = H.shuffle(free, H.rng(seed + 1));
    ev.people.forEach((p, i) => {
      const [tx, ty] = p.id === 'you' ? W.ENTRY : spots[i];
      people.set(p.id, makeBody(p, tx, ty));
    });
  }
  const me = () => people.get('you');
  function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y) / T; }

  // ---------- movement ----------
  function walkTo(b, tx, ty, then) {
    const path = W.findPath(tileOf(b), [tx, ty]);
    if (!path) return false;
    b.path = path.slice(1); b.then = then || null; b.act = null; standUp(b);
    if (!b.path.length) { b.path = null; const t = b.then; b.then = null; if (t) t(); }
    return true;
  }
  function followPath(b, dt) {
    const [tx, ty] = b.path[0], goal = feetOf(tx, ty);
    const dx = goal.x - b.x, dy = goal.y - b.y, d = Math.hypot(dx, dy), step = (b.npc ? 46 : 64) * dt;
    if (d <= step) {
      b.x = goal.x; b.y = goal.y; b.path.shift();
      if (!b.path.length) { b.path = null; const t = b.then; b.then = null; if (t) t(); }
    } else { b.x += dx / d * step; b.y += dy / d * step; }
    if (Math.abs(dx) > Math.abs(dy)) b.dir = dx > 0 ? 'right' : 'left'; else if (dy) b.dir = dy > 0 ? 'down' : 'up';
    b.moving = true;
  }
  function face(b, tx, ty) {
    const [x, y] = tileOf(b), dx = tx - x, dy = ty - y;
    b.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
  }
  function faceEachOther(a, b) {
    if (Math.abs(a.x - b.x) > Math.abs(a.y - b.y)) { a.dir = a.x < b.x ? 'right' : 'left'; b.dir = a.x < b.x ? 'left' : 'right'; }
    else { a.dir = a.y < b.y ? 'down' : 'up'; b.dir = a.y < b.y ? 'up' : 'down'; }
  }

  // ---------- acts and speech ----------
  // to: the id this line is meant for ('you' for the player). Lines meant for you are marked on the bubble,
  // light up the speaker's tag, land in the talk log and offer a reply, so nothing said to you is missed.
  function say(b, text, secs, to) {
    const t = H.sanitizeBubble(text, 160);
    if (!t) return;
    b.bubble = { text: t, until: clock + (secs || 4), born: clock, to: to || null };
    const m = me();
    if (b.id === 'you') logTalk(b, t, to);
    else if (to === 'you') {
      logTalk(b, t, 'you');
      if (m && !b.path) { if (Math.abs(b.x - m.x) > Math.abs(b.y - m.y)) b.dir = m.x > b.x ? 'right' : 'left'; else b.dir = m.y > b.y ? 'down' : 'up'; }
      cue = { id: b.id, name: b.name, text: t, until: clock + 14 };
      unread += 1; renderTalk();
    } else if (m && b.id !== 'host' && dist(b, m) <= 2.5) logTalk(b, t, to);
  }
  // ---------- talk: who you are talking to, what was said near you ----------
  let talkTarget = null, cue = null, unread = 0;
  const talkLog = [];
  function logTalk(b, text, to) {
    talkLog.push({ who: b.id, name: b.id === 'you' ? 'Bạn' : b.name, text, to: to || null, toName: to && to !== 'you' && people.get(to) ? people.get(to).name : null });
    if (talkLog.length > 40) talkLog.shift();
    renderTalkLog();
  }
  // Who hears you: the person you chose (if still close), else the nearest guest, else everyone nearby.
  function hearer() {
    const m = me();
    if (!m) return null;
    if (phase === 'xoayban' && roundState && roundState.seated && roundState.partner) return people.get(roundState.partner);
    const t = talkTarget && people.get(talkTarget);
    if (t && dist(t, m) <= 3) return t;
    return [...people.values()].filter(b => b.npc && dist(b, m) <= 2.5).sort((a, c) => dist(a, m) - dist(c, m))[0] || null;
  }
  function chooseTalk(id) {
    talkTarget = id; cue = null; unread = 0; renderTalk();
    const p = people.get(id);
    if (p && me()) faceEachOther(me(), p);
    $('sayInput').focus();
  }
  let talkKey = '';
  function renderTalk() {
    const h = ev ? hearer() : null;
    const showCue = cue && cue.until > clock;
    const key = (h ? h.id : '') + '|' + (showCue ? cue.id + cue.text : '') + '|' + unread;
    if (key === talkKey) return;
    talkKey = key;
    const row = $('talkTo'); row.replaceChildren();
    row.append(document.createTextNode('Nói với: '), el('b', '', h ? h.name : 'những ai đứng gần'));
    const near = ev && me() ? [...people.values()].filter(b => b.npc && dist(b, me()) <= 3) : [];
    if (near.length > 1 && !(phase === 'xoayban' && roundState && roundState.seated)) {
      row.append(btn('Đổi người', '', () => {
        const i = near.findIndex(b => b.id === (h && h.id));
        chooseTalk(near[(i + 1) % near.length].id);
      }));
    }
    const box = $('replyCue');
    box.hidden = !showCue;
    if (showCue) {
      $('replyText').textContent = '💬 ' + cue.name + ' vừa nói với bạn: “' + cue.text + '”';
      $('replyBtn').onclick = () => chooseTalk(cue.id);
    }
    const badge = $('talkBadge'); badge.hidden = !unread; badge.textContent = String(unread);
  }
  function renderTalkLog() {
    const ul = $('talkLog'); ul.replaceChildren();
    if (!talkLog.length) { ul.append(el('li', 'empty', 'Lời nói gần bạn và lời nói với bạn sẽ hiện ở đây.')); return; }
    for (const l of talkLog.slice(-12).reverse()) {
      const li = el('li', l.who === 'you' ? 'mine' : l.to === 'you' ? 'to-you' : '');
      li.append(el('b', '', l.name + (l.toName ? ' → ' + l.toName : '')), document.createTextNode(l.text));
      ul.append(li);
    }
  }
  function startAct(b, act) {
    const a = H.ACTS[act];
    if (!a) return false;
    if (a.place) return startPlaceAct(b, act);
    if (a.at) {
      const s = W.spotAt(...tileOf(b));
      if (!s || W.SPOTS[s].act !== act) return false;
      const spot = W.SPOTS[s]; face(b, spot.tx, spot.ty);
    }
    b.act = act; b.actUntil = clock + (act === 'ngugat' ? 6 : 4.5); b.path = null;
    if (act === 'goido') b.drink = true;
    standUp(b);
    if (act === 'ngammua') b.dir = 'up';
    if (act === 'mathe' || act === 'vaytay' || act === 'ngugat') b.dir = 'down';
    return true;
  }
  function availableActs(b) {
    const [x, y] = tileOf(b);
    const s = W.spotAt(x, y);
    const list = H.FREE_ACTS.slice();
    if (s && !b.lie) list.push(W.SPOTS[s].act);
    if (b.drink) list.push('uong');
    if (L.windowSeatAt(x, y) && !b.sit) list.push('cuaso');
    if (L.nookAt(x, y) && !b.lie) list.push('nam');
    if (dist(b, bo.dog) < 1.6) list.push('vuotcho');
    return list;
  }
  // Window bench, reading nook, Bơ the dog and a drink: things to do between people, not only at furniture.
  const L = window.Life;
  const bo = L.createDog({ clock: () => clock, rand: Math.random, still: () => still(), particles, me: () => me() }, 'Bơ');
  function startPlaceAct(b, act) {
    if (act === 'cuaso') { if (!L.sitWindow(b)) return false; b.act = 'cuaso'; b.actUntil = clock + 12; return true; }
    if (act === 'nam') { if (!L.lieDown(b)) return false; b.act = 'nam'; b.actUntil = clock + 12; return true; }
    if (act === 'uong') { if (!b.drink) return false; b.act = 'uong'; b.actUntil = clock + 3; b.drinkColor = '#a0724a'; return true; }
    if (act === 'vuotcho') {
      const d = bo.dog;
      if (dist(b, d) > 1.6) return false;
      b.sit = false; b.lie = false; b.seatKind = null;
      b.dir = Math.abs(d.x - b.x) >= Math.abs(d.y - b.y) ? (d.x > b.x ? 'right' : 'left') : (d.y > b.y ? 'down' : 'up');
      b.act = 'vuotcho'; b.actUntil = clock + 4; bo.pet(b);
      return true;
    }
    return false;
  }
  // Walking off a bench or a bean bag ends sitting or lying.
  function standUp(b) { b.sit = false; b.lie = false; b.seatKind = null; }

  // Everyone in the room watches; guests only notice what is within SEE_TILES. You see the whole room.
  let observeTimer = 0;
  function observeAll(dt) {
    observeTimer -= dt;
    if (observeTimer > 0 || !ev) return;
    observeTimer = 0.5;
    for (const actor of people.values()) {
      if (!actor.act) continue;
      for (const viewer of people.values()) {
        if (viewer === actor) continue;
        if (viewer.id !== 'you' && dist(viewer, actor) > SEE_TILES) continue;
        H.observe(ev, viewer.id, actor.id, actor.act);
      }
    }
  }

  // ---------- guest behaviour ----------
  function guestThink(b, dt) {
    const g = H.person(ev, b.id);
    b.nextLine -= dt;
    if (b.nextLine <= 0 && !b.bubble) {
      // now and then a guest standing close turns to you instead of talking to the room
      const m = me();
      if (m && phase === 'tudo' && dist(b, m) < 2.2 && Math.random() < 0.35) say(b, pick(H.OPENERS), 5, 'you');
      else say(b, pick(g.idle), 3.6);
      b.nextLine = 9 + Math.random() * 10;
    }
    if (b.locked || b.path || (b.act && b.actUntil > clock)) return;
    b.nextIdea -= dt;
    if (b.nextIdea > 0) return;
    b.nextIdea = 1.5 + Math.random() * 3;
    const act = Math.random() < 0.75 ? pick(g.does) : pick(H.FREE_ACTS);
    if (H.ACTS[act].place) { guestPlace(b, act); return; }
    if (H.ACTS[act].at) {
      const spots = Object.values(W.SPOTS).filter(s => s.act === act);
      const s = pick(spots);
      const stand = W.standTiles(s.tx, s.ty, tileOf(b))[0];
      if (stand) walkTo(b, stand[0], stand[1], () => startAct(b, act));
    } else if (Math.random() < 0.5) {
      const free = W.freeTiles().filter(([, y]) => y >= 3 && y <= 8);
      const [tx, ty] = pick(free);
      walkTo(b, tx, ty, () => startAct(b, act));
    } else startAct(b, act);
  }

  function guestPlace(b, act) {
    const all = [...people.values()];
    if (act === 'uong') { if (b.drink) startAct(b, 'uong'); else { const s = W.SPOTS.counter, st = W.standTiles(s.tx, s.ty, tileOf(b))[0]; if (st) walkTo(b, st[0], st[1], () => { startAct(b, 'goido'); b.drink = true; }); } return; }
    if (act === 'vuotcho') { const st = bo.besideTile(tileOf(b)); if (st) walkTo(b, st[0], st[1], () => startAct(b, 'vuotcho')); return; }
    const spot = pick(L.freeSpot(act === 'cuaso' ? W.WINDOW_SEATS : W.NOOK, all, b));
    if (!spot) return;
    b.goingTo = spot;
    walkTo(b, spot[0], spot[1], () => { b.goingTo = null; startAct(b, act); });
  }

  // Guests who like someone enough drop a leaf now and then; tarot mates who bump into each other compare halves.
  let socialTimer = 0;
  function guestSocial(dt) {
    socialTimer -= dt;
    if (socialTimer > 0) return;
    socialTimer = 2;
    for (const b of people.values()) {
      if (!b.npc) continue;
      for (const to of H.npcLeafTargets(ev, b.id)) {
        if (Math.random() > 0.35) continue;
        if (H.dropLeaf(ev, b.id, to) && to === 'you') {
          toast('🍃 Có người vừa thả cho bạn một chiếc lá.');
          if (!still()) particles.push({ kind: 'leaf', x: me().x + 6, y: me().y - 34, vx: -6, vy: 10, life: 2.6 });
        }
      }
      const h = ev.halves[b.id], mate = h && people.get(h.mate);
      if (mate && mate.npc && dist(b, mate) < 1.6 && !ev.tarotFound.has([b.id, mate.id].sort().join('+'))) {
        const r = H.compareHalves(ev, b.id, mate.id);
        if (r.first) { say(b, 'Ơ, nửa lá ' + r.card + '!', 3); say(mate, r.q, 5); }
      }
    }
  }

  // ---------- phases ----------
  const HOST_LINES = {
    tudo: 'Chào cả nhà! Giờ ai thích làm gì thì làm nha. Thấy ai dễ thương thì thả một chiếc lá.',
    xoayban: 'Xoay bàn nè! Mỗi lượt ngồi với một người, cùng pha một ly.',
    thu: 'Giờ viết thư không ký tên: khen một điều bạn đã thấy người ta làm.',
    thaden: 'Đèn lồng nhé. Chọn kín tối đa ba người. Ai chọn nhau thì đèn bay lên.',
    lycuoi: 'Ly cuối! Ai muốn ở lại thì cứ ngồi thêm chút nha.',
    het: 'Cảm ơn cả nhà. Về cẩn thận, trời còn mưa đó.'
  };
  function setPhase(id) {
    phase = id;
    renderTrack(); renderPhaseCard(); renderActs();
    if (id === 'tudo') { phaseEnd = clock + DUR.tudo; banner('Màn 1 · Tự do làm khùng điên', 3, true); }
    if (id === 'xoayban') { round = -1; nextRound(); }
    if (id === 'thu') { for (const b of people.values()) { b.locked = false; b.seat = null; } H.npcLetters(ev); openLetters(); }
    if (id === 'thaden') openLanterns();
    if (id === 'lycuoi') startLastDrink();
    if (id === 'het') openEnd();
    if (HOST_LINES[id]) hostSay(HOST_LINES[id]);
  }
  function nextPhase() {
    const order = H.PHASES.map(p => p.id);
    const i = order.indexOf(phase);
    if (phase === 'xoayban' && round < ev.rounds.length - 1) { endRound(); nextRound(); return; }
    if (phase === 'xoayban') endRound();
    if (i < order.length - 1) setPhase(order[i + 1]);
  }

  // Màn 2: rotation. Everyone walks to the seat the host gives them, then each table makes a drink together.
  function nextRound() {
    round++;
    const pairs = ev.rounds[round];
    const offered = H.shuffle(Object.keys(H.INGREDIENTS), H.rng(seed + 100 + round)).slice(0, 4);
    roundState = { pairs, offered, q: H.QUESTIONS[(round + (seed % H.QUESTIONS.length)) % H.QUESTIONS.length], mine: null, theirs: null, partner: null, answered: false, replied: false, seated: false, startAt: clock };
    pairs.forEach(([a, b], i) => {
      const t = W.TABLES[i];
      [a, b].forEach((id, k) => {
        const body = people.get(id);
        body.locked = true; body.act = null; body.seat = t.seats[k]; body.bubble = null;
        walkTo(body, t.seats[k][0], t.seats[k][1], () => { faceToward(body, t); });
      });
      if (a === 'you' || b === 'you') roundState.partner = a === 'you' ? b : a;
    });
    phaseEnd = clock + DUR.round + 4; // a few seconds to walk over
    const pt = roundState.partner && people.get(roundState.partner);
    banner('Màn 2 · Lượt ' + (round + 1) + '/' + ev.rounds.length + (pt ? ' · bạn ngồi với ' + pt.name : ''), 3, true);
    renderPhaseCard();
  }
  function faceToward(b, t) { b.dir = b.x < t.tx * T + 8 ? 'right' : 'left'; }
  function endRound() {
    if (!roundState) return;
    for (const [a, b] of roundState.pairs) {
      const youIn = a === 'you' || b === 'you';
      const ia = a === 'you' ? (roundState.mine || roundState.offered[0]) : H.npcIngredient(ev, a, roundState.offered);
      const ib = b === 'you' ? (roundState.mine || roundState.offered[0]) : H.npcIngredient(ev, b, roundState.offered);
      H.tableRound(ev, a, b, ia, ib, a === 'you' ? roundState.answered : true, b === 'you' ? roundState.answered : true);
      if (!youIn && fx()) particles.push({ kind: 'spark', x: (people.get(a).x + people.get(b).x) / 2, y: people.get(a).y - 18, vx: 0, vy: -8, life: 1.2 });
    }
  }
  function pickIngredient(ing) {
    if (!roundState || roundState.mine) return;
    roundState.mine = ing;
    const partner = people.get(roundState.partner);
    roundState.theirs = H.npcIngredient(ev, partner.id, roundState.offered);
    const drink = H.drinkName(ing, roundState.theirs);
    say(partner, 'Mình chọn ' + H.INGREDIENTS[roundState.theirs].toLowerCase() + '. Vậy là… ' + drink + '!', 5, 'you');
    if (fx()) particles.push({ kind: 'spark', x: me().x, y: me().y - 20, vx: 0, vy: -10, life: 1.2 });
    renderPhaseCard();
  }
  function roundTick() {
    if (!roundState) return;
    const all = [...people.values()].every(b => !b.path);
    if (all && !roundState.seated) { roundState.seated = true; roundState.seatedAt = clock; renderPhaseCard(); }
    if (!roundState.seated) return;
    const partner = roundState.partner && people.get(roundState.partner);
    if (partner && !roundState.replied && (roundState.answered || clock - roundState.seatedAt > 14)) {
      roundState.replied = true;
      say(partner, pick(H.person(ev, partner.id).answer), 7, 'you');
    }
    if (partner && !roundState.mine && clock - roundState.seatedAt > 6 && !partner.bubble && !roundState.asked) { roundState.asked = true; say(partner, 'Bạn chọn gì để pha nè?', 5, 'you'); }
    // other tables chat now and then
    for (const [a, b] of roundState.pairs) {
      if (a === 'you' || b === 'you') continue;
      const s = people.get(Math.random() < 0.5 ? a : b);
      if (!s.bubble && Math.random() < 0.004) say(s, pick(H.person(ev, s.id).answer), 4);
    }
  }

  // Màn 5
  function startLastDrink() {
    phaseEnd = clock + DUR.lycuoi;
    const mine = couples.find(c => c.a === 'you' || c.b === 'you');
    for (const b of people.values()) { b.locked = false; b.seat = null; }
    if (mine) {
      const other = people.get(mine.a === 'you' ? mine.b : mine.a);
      const t = W.TABLES[W.LOUNGE];
      for (const [b, s] of [[me(), t.seats[0]], [other, t.seats[1]]]) { b.locked = true; walkTo(b, s[0], s[1], () => faceToward(b, t)); }
      const lines = H.person(ev, other.id).last;
      lastDrink = { other: other.id, lines: lines.slice(), next: clock + 4 };
      banner('Màn 5 · Ly cuối với ' + other.name, 3, true);
    } else {
      lastDrink = null;
      banner('Màn 5 · Ly cuối', 3, true);
      later(300, () => openHostLetter());
    }
    renderPhaseCard();
  }
  let lastDrink = null;
  function lastDrinkTick() {
    if (!lastDrink) return;
    const other = people.get(lastDrink.other);
    if (lastDrink.lines.length && clock >= lastDrink.next && !other.path) {
      say(other, lastDrink.lines.shift(), 6.5, 'you');
      lastDrink.next = clock + 9;
    }
  }

  // ---------- modals ----------
  let modalOpen = false, modalClosable = true, onModalClose = null;
  function openModal(kicker, title, closable, onClose) {
    $('mKicker').textContent = kicker; $('mTitle').textContent = title;
    const body = $('mBody'); body.replaceChildren();
    modalClosable = closable !== false; onModalClose = onClose || null;
    $('mClose').hidden = !modalClosable;
    $('shade').hidden = false; modalOpen = true; keys.clear();
    setTimeout(() => { const f = $('modal').querySelector('button:not([hidden]), select, input'); if (f) f.focus(); }, 0);
    return body;
  }
  function closeModal() {
    if (!modalOpen) return;
    $('shade').hidden = true; modalOpen = false;
    const cb = onModalClose; onModalClose = null;
    if (cb) cb();
  }
  $('mClose').addEventListener('click', () => { if (modalClosable) closeModal(); });
  $('shade').addEventListener('click', e => { if (e.target === $('shade') && modalClosable) closeModal(); });
  $('modal').addEventListener('keydown', e => {
    if (e.key === 'Escape' && modalClosable) { e.preventDefault(); closeModal(); }
    if (e.key === 'Tab') {
      const f = [...$('modal').querySelectorAll('button:not([hidden]):not(:disabled), select, input')];
      if (!f.length) return;
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    }
  });

  // Lối vào: nickname, look, item and lantern colour. Nothing real is asked.
  function openSetup() {
    const choice = { name: H.NICKNAMES[0], look: 0, item: H.ITEMS[0], lantern: 'thuong' };
    const body = openModal('LỐI VÀO · THƯ MỜI', NIGHT ? 'Bạn được mời tới "' + NIGHT.title + '"' : 'Bạn được mời tới quán cà phê mưa', false);
    body.append(el('p', '', 'Tối nay có 10 người được chọn. Cô Lá dẫn buổi qua 5 màn: tự do, xoay bàn, thư giữa giờ, thả đèn và ly cuối.'),
      el('p', 'note', 'Mọi người chỉ thấy tên Lá, dáng, món đồ mang theo và màu đèn của bạn.'));
    if (NIGHT) {
      body.append(el('p', '', NIGHT.intro), el('div', 'field', 'Mức gan của bạn'));
      const row = el('div', 'choices'); body.append(row);
      const opts = [['nhe', 'Nhẹ'], ['vua', 'Vừa']];
      const bs = opts.map(([k, l]) => { const b = btn(l, '', () => { courage = k; bs.forEach(x => x.setAttribute('aria-pressed', String(x === b))); }); b.setAttribute('aria-pressed', String(k === courage)); row.append(b); return b; });
      body.append(el('p', 'note', 'Không máu me, không hù bất ngờ, không nhấp nháy, không âm thanh. Lúc nào cũng có nút "Mình sợ quá" để bật đèn cả quán.'));
    }
    const group = (label, items, render, onPick) => {
      body.append(el('div', 'field', label));
      const row = el('div', 'choices'); body.append(row);
      const buttons = items.map((it, i) => {
        const b = btn('', '', () => { buttons.forEach(x => x.setAttribute('aria-pressed', 'false')); b.setAttribute('aria-pressed', 'true'); onPick(it, i); });
        render(b, it, i); b.setAttribute('aria-pressed', i === 0 ? 'true' : 'false'); row.append(b); return b;
      });
    };
    group('Tên Lá của bạn', H.NICKNAMES, (b, n) => { b.textContent = n; }, n => { choice.name = n; });
    group('Dáng', H.LOOKS, (b, look, i) => {
      const c = document.createElement('canvas'); c.width = 14; c.height = 18; c.setAttribute('aria-hidden', 'true');
      E.drawSprite(c.getContext('2d'), E.buildSheet(look)['down:stand:0'], 0, 0);
      b.append(c); b.setAttribute('aria-label', 'Dáng ' + (i + 1));
    }, (l, i) => { choice.look = i; });
    group('Món đồ mang theo', H.ITEMS, (b, it) => { b.textContent = it; }, it => { choice.item = it; });
    group('Màu đèn lồng', Object.keys(H.LANTERNS), (b, k) => { b.textContent = H.LANTERNS[k].icon + ' ' + H.LANTERNS[k].label; }, k => { choice.lantern = k; });
    body.append(btn('Vào quán', 'primary', () => { closeModal(); beginEvening(choice); }));
  }
  function beginEvening(choice) {
    you = { name: choice.name, item: choice.item, lantern: choice.lantern, look: H.LOOKS[choice.look] };
    ev = H.createEvening(seed, you);
    couples = []; myPicks = []; round = -1; roundState = null; lastDrink = null;
    particles.length = 0; lanterns.length = 0;
    spawnAll();
    renderHalf(); renderGuests();
    if (NIGHT) { lightsOn = false; dim = 0; beatIx = 0; beatAt = clock + 12; $('scaredBtn').hidden = false; }
    const h = ev.halves.you;
    toast('Bạn giữ nửa ' + h.side + ' lá ' + h.card + '. Ai giữ nửa còn lại?');
    setPhase('tudo');
  }

  // Talking to someone in the room.
  function openPerson(id) {
    const b = people.get(id), p = H.person(ev, id);
    const body = openModal(H.LANTERNS[p.lantern].icon + ' ' + H.LANTERNS[p.lantern].label.toUpperCase(), p.name);
    body.append(el('p', 'note', 'Mang theo: ' + p.item + '.'));
    const seen = [...ev.seen.you[id]].map(a => H.ACTS[a].verb);
    body.append(el('p', 'note', seen.length ? 'Bạn đã thấy ' + p.name + ' ' + seen.join(', ') + '.' : 'Bạn chưa thấy ' + p.name + ' làm gì.'));
    if (phase === 'tudo') {
      const leafDone = ev.leafSent.you.has(id), left = H.LEAF_LIMIT - ev.leafSent.you.size;
      const leaf = btn(leafDone ? '🍃 Đã thả lá cho người này' : '🍃 Thả một chiếc lá (bí mật, còn ' + left + ')', 'primary', () => {
        if (H.dropLeaf(ev, 'you', id)) { if (!still()) particles.push({ kind: 'leaf', x: b.x + 6, y: b.y - 34, vx: -6, vy: 10, life: 2.6 }); toast('Lá đã rơi. ' + p.name + ' sẽ không biết ai thả.'); }
        closeModal(); renderGuests();
      });
      leaf.disabled = leafDone || left <= 0;
      body.append(leaf, document.createTextNode(' '));
      body.append(btn('🃏 Hỏi nửa lá tarot', 'ghost', () => {
        closeModal();
        const r = H.compareHalves(ev, 'you', id);
        faceEachOther(me(), b);
        if (r.match) { say(b, 'Nửa lá ' + r.card + '! Khớp nè.', 4, 'you'); say(me(), r.q, 6, id); toast('Hai nửa khớp. Câu hỏi chung: ' + r.q); }
        else say(b, 'Mình giữ nửa lá ' + r.card + ', không khớp rồi.', 4, 'you');
      }), document.createTextNode(' '));
    }
    body.append(btn('👋 Vẫy tay chào', 'ghost', () => {
      closeModal(); faceEachOther(me(), b); startAct(me(), 'vaytay');
      if (H.wave(ev, 'you', id)) later(500, () => say(b, pick(['Chào bạn nha!', 'Hí, chào!', 'Ơ chào!']), 4, 'you'));
    }), document.createTextNode(' '), btn('💬 Nói với ' + p.name, 'ghost', () => { closeModal(); chooseTalk(id); }));
  }

  // Màn 3
  function openLetters() {
    const body = openModal('MÀN 3 · THƯ GIỮA GIỜ', 'Gửi tối đa ' + H.LETTER_LIMIT + ' lá thư không ký tên', false);
    body.append(el('p', 'note', 'Chỉ khen một điều bạn đã thật sự thấy người ta làm. Người nhận không biết ai gửi.'));
    const count = el('p', 'note'); body.append(count);
    const update = () => { count.textContent = 'Đã gửi ' + ev.letterSent.you.size + '/' + H.LETTER_LIMIT + '.'; };
    update();
    for (const p of ev.people) {
      if (p.id === 'you') continue;
      const row = el('div', 'rowform');
      row.append(el('b', '', H.LANTERNS[p.lantern].icon + ' ' + p.name));
      const acts = [...ev.seen.you[p.id]];
      if (!acts.length) { row.append(el('span', 'none', 'Bạn chưa thấy người này làm gì.')); body.append(row); continue; }
      const sa = el('select'); sa.setAttribute('aria-label', 'Điều bạn thấy ' + p.name + ' làm');
      for (const a of acts) { const o = el('option', '', H.ACTS[a].verb); o.value = a; sa.append(o); }
      const sj = el('select'); sj.setAttribute('aria-label', 'Cảm giác của bạn');
      for (const j of H.ADJECTIVES) { const o = el('option', '', j); o.value = j; sj.append(o); }
      const send = btn('Gửi', '', () => {
        if (H.writeLetter(ev, 'you', p.id, sa.value, sj.value)) { send.textContent = 'Đã gửi'; send.disabled = sa.disabled = sj.disabled = true; update(); }
        else toast(ev.letterSent.you.size >= H.LETTER_LIMIT ? 'Bạn đã gửi đủ ' + H.LETTER_LIMIT + ' lá thư.' : 'Không gửi được.');
      });
      row.append(sa, sj, send); body.append(row);
    }
    body.append(btn('Mở hộp thư của bạn', 'primary', () => openInbox()));
  }
  function openInbox() {
    const body = openModal('MÀN 3 · HỘP THƯ', 'Thư và lá bạn nhận được', false);
    const mine = ev.letters.you;
    body.append(el('p', '', '🍃 Bạn nhận ' + ev.leaves.you + ' chiếc lá trong Màn 1.'));
    if (!mine.length) body.append(el('p', 'note', 'Chưa có lá thư nào. Không sao, nhiều người ngại viết lắm.'));
    for (const l of mine) body.append(el('div', 'letter', H.letterText(l)));
    body.append(btn('Sang Màn 4 · Thả đèn', 'primary', () => { closeModal(); nextPhase(); }));
  }

  // Màn 4
  function openLanterns() {
    myPicks = [];
    const body = openModal('MÀN 4 · THẢ ĐÈN', 'Chọn kín tối đa ba người, theo thứ tự', false);
    body.append(el('p', 'note', 'Chỉ cặp nào chọn nhau mới được công bố. Không ai biết ai đã chọn mình nếu không khớp.'));
    const list = el('div');
    const draw = () => {
      list.replaceChildren();
      for (const p of ev.people) {
        if (p.id === 'you') continue;
        const r = myPicks.indexOf(p.id);
        const b = btn('', 'pickbtn pick', () => {
          const i = myPicks.indexOf(p.id);
          if (i >= 0) myPicks.splice(i, 1); else if (myPicks.length < 3) myPicks.push(p.id);
          draw(); const again = list.querySelector('[data-id="' + p.id + '"]'); if (again) again.focus();
        });
        b.dataset.id = p.id;
        b.setAttribute('aria-pressed', r >= 0 ? 'true' : 'false');
        b.append(el('span', '', H.LANTERNS[p.lantern].icon + ' ' + p.name + ' · ' + p.item), el('span', 'rank', r >= 0 ? '#' + (r + 1) : ''));
        list.append(b);
      }
    };
    draw();
    body.append(list, btn('Thả đèn', 'primary', () => { closeModal(); releaseLanterns(); }));
  }
  function releaseLanterns() {
    const picks = { you: myPicks.slice() };
    for (const p of ev.people) if (p.npc) picks[p.id] = H.npcPicks(ev, p.id);
    couples = H.couples(ev, picks);
    for (const c of couples) {
      const a = people.get(c.a), b = people.get(c.b);
      for (const p of [a, b]) lanterns.push({ x: p.x, y: p.y - 22, vy: still() ? 0 : -14, life: 5, color: c.kind === 'hen' ? '#ef8a7a' : '#7fc8a0', sway: Math.random() * 6 });
      if (fx()) { a.hop = 300; b.hop = 300; }
    }
    const mine = couples.find(c => c.a === 'you' || c.b === 'you');
    banner(couples.length ? couples.length + ' chiếc đèn đôi bay lên' : 'Tối nay chưa có đèn đôi nào', 3, true);
    later(still() ? 300 : 2600, () => openResults(mine));
  }
  function openResults(mine) {
    const body = openModal('MÀN 4 · ĐÈN BAY', mine ? 'Đèn của bạn đã bay lên' : 'Đèn của bạn còn ở lại', false);
    if (mine) {
      const o = H.person(ev, mine.a === 'you' ? mine.b : mine.a);
      body.append(el('div', 'result mine', (mine.kind === 'hen' ? '🌸 Bạn và ' + o.name + ' chọn nhau. Một đôi hẹn.' : '🍃 Bạn và ' + o.name + ' chọn nhau. Một tình bạn mới.')));
    } else body.append(el('p', '', myPicks.length ? 'Lần này đèn của bạn chưa thành đôi. Không ai biết bạn đã chọn ai.' : 'Bạn chưa chọn ai. Vậy cũng được.'));
    body.append(el('div', 'field', 'Các đèn đôi tối nay'));
    if (!couples.length) body.append(el('p', 'note', 'Chưa có.'));
    for (const c of couples) {
      const a = H.person(ev, c.a), b = H.person(ev, c.b);
      body.append(el('div', 'result' + (c.a === 'you' || c.b === 'you' ? ' mine' : ''), (c.kind === 'hen' ? '🌸 ' : '🍃 ') + a.name + ' & ' + b.name));
    }
    body.append(btn('Sang Màn 5 · Ly cuối', 'primary', () => { closeModal(); nextPhase(); }));
  }
  function openHostLetter() {
    const body = openModal('MÀN 5 · THƯ CỦA CÔ LÁ', 'Gửi ' + you.name);
    const noticed = ev.leaves.you + ev.letters.you.length > 0;
    body.append(el('div', 'letter', 'Tối nay bạn nhận ' + ev.leaves.you + ' chiếc lá và ' + ev.letters.you.length + ' lá thư. ' +
      (noticed ? 'Có người đã để ý bạn đó.' : 'Buổi đầu ai cũng ngại, không sao cả.') + ' Ngồi lại uống thêm ly nữa nha.'),
      btn('Cảm ơn Cô Lá', 'primary', closeModal));
  }
  function openEnd() {
    const mine = couples.find(c => c.a === 'you' || c.b === 'you');
    const body = openModal('HẾT BUỔI', 'Cảm ơn bạn đã tới quán', false);
    const lines = [
      '🍃 Lá nhận được: ' + ev.leaves.you,
      '✉️ Thư nhận được: ' + ev.letters.you.length,
      '☕ Người đã ngồi cùng bàn: ' + ev.rounds.map(r => r.find(p => p.includes('you'))).filter(Boolean).map(p => H.person(ev, p[0] === 'you' ? p[1] : p[0]).name).join(', ')
    ];
    for (const l of lines) body.append(el('p', '', l));
    if (mine) {
      const o = H.person(ev, mine.a === 'you' ? mine.b : mine.a);
      body.append(el('div', 'result mine', 'Bạn và ' + o.name + ' có một chiếc đèn đôi.'));
      body.append(el('p', 'note', 'Ở bản thật, mỗi người tự quyết có cho nhau tên thật hay hẹn buổi sau. Không ai thấy lựa chọn của người kia nếu không trùng nhau. Bản thử dừng ở đây.'));
    }
    body.append(btn('Buổi khác', 'primary', () => { closeModal(); restart(); }));
  }

  // ---------- side panel ----------
  function renderTrack() {
    const nav = $('track'); nav.replaceChildren();
    const order = H.PHASES.filter(p => p.id !== 'het');
    const at = H.PHASES.findIndex(p => p.id === phase);
    order.forEach((p, i) => {
      const d = el('div', i === at ? 'now' : i < at ? 'done' : '');
      d.append(el('b', '', p.n ? 'MÀN ' + p.n : '·'), document.createTextNode(p.label));
      if (i === at) d.setAttribute('aria-current', 'step');
      nav.append(d);
    });
  }
  const PHASE_HELP = {
    loivao: 'Chọn tên Lá, dáng, món đồ và màu đèn.',
    tudo: 'Làm gì cũng được: nhảy, đọc sách, vuốt mèo, ngủ gật… Lại gần ai đó để thả lá bí mật, hỏi nửa lá tarot hoặc vẫy tay.',
    xoayban: 'Cô Lá xếp chỗ. Mỗi lượt ngồi với một người, cùng chọn nguyên liệu để pha một ly, rồi nói chuyện theo thẻ câu hỏi.',
    thu: 'Viết thư không ký tên cho tối đa ba người.',
    thaden: 'Chọn kín tối đa ba người.',
    lycuoi: 'Ngồi thêm chút, nói chuyện nhẹ nhàng trước khi về.',
    het: 'Buổi đã kết thúc.'
  };
  let lastCardKey = '';
  function renderPhaseCard() {
    const card = $('phaseCard'); card.replaceChildren();
    const p = H.PHASES.find(x => x.id === phase);
    card.append(el('small', '', p.n ? 'MÀN ' + p.n + '/5' : p.label.toUpperCase()), el('h2', '', p.label), el('p', '', PHASE_HELP[phase]));
    if (['tudo', 'xoayban', 'lycuoi'].includes(phase)) {
      card.append(el('div', 'clock', ''));
      card.append(btn(phase === 'xoayban' && round < ev.rounds.length - 1 ? 'Sang lượt tiếp' : 'Sang màn tiếp', '', () => nextPhase()));
    }
    if (phase === 'xoayban' && roundState && roundState.partner) {
      const partner = H.person(ev, roundState.partner);
      const box = el('div', 'table-ui');
      box.append(el('div', 'field', 'Bàn của bạn · ' + H.LANTERNS[partner.lantern].icon + ' ' + partner.name + ' (' + partner.item + ')'));
      if (!roundState.seated) box.append(el('p', '', 'Đang đi tới bàn…'));
      else {
        box.append(el('p', '', roundState.mine ? 'Ly của hai bạn: ' + H.drinkName(roundState.mine, roundState.theirs) : 'Cùng pha một ly: bạn chọn một nguyên liệu.'));
        const ings = el('div', 'ings');
        for (const k of roundState.offered) {
          const b = btn(H.INGREDIENTS[k], '', () => pickIngredient(k));
          b.setAttribute('aria-pressed', roundState.mine === k ? 'true' : 'false'); b.disabled = !!roundState.mine;
          ings.append(b);
        }
        box.append(ings, el('div', 'q', '🃏 ' + roundState.q), el('p', '', roundState.answered ? 'Bạn đã trả lời. ' + partner.name + ' đang nghe.' : 'Trả lời bằng ô Nói bên dưới khung game.'));
      }
      card.append(box);
    }
    if (phase === 'lycuoi') card.append(btn('Kết thúc buổi', 'primary', () => setPhase('het')));
    lastCardKey = '';
  }
  function updateClock() {
    const c = $('phaseCard').querySelector('.clock');
    if (!c) return;
    const left = phaseEnd - clock;
    const key = fmt(left);
    if (key !== lastCardKey) { c.textContent = 'còn ' + key; lastCardKey = key; }
  }
  function renderHalf() {
    const h = ev && ev.halves.you, box = $('half');
    box.replaceChildren();
    if (!h) return;
    box.append(el('b', '', '🃏 Nửa ' + h.side + ' lá ' + h.card), el('div', '', 'Ai giữ nửa còn lại thì hai bạn có chung một câu hỏi để nói. Lá bài chỉ gợi chuyện, không đoán gì về ai.'));
  }
  function renderGuests() {
    const ul = $('guestList'); ul.replaceChildren();
    if (!ev) return;
    for (const p of ev.people) {
      const li = el('li', p.id === 'you' ? 'me' : '');
      li.append(el('span', '', H.LANTERNS[p.lantern].icon + ' ' + p.name + (p.id === 'you' ? ' (bạn)' : '') + ' · ' + p.item));
      if (p.id !== 'you') li.append(btn('Đi tới', '', () => goToPerson(p.id))); else li.append(el('span'));
      if (p.id !== 'you') {
        const seen = [...ev.seen.you[p.id]].map(a => H.ACTS[a].icon).join(' ');
        const extra = ev.leafSent.you.has(p.id) ? ' · 🍃 bạn đã thả lá' : '';
        li.append(el('span', 'seen', (seen ? 'Bạn đã thấy: ' + seen : 'Chưa thấy làm gì') + extra));
      }
      ul.append(li);
    }
  }
  let guestsTimer = 0;

  function goToPerson(id) {
    const b = people.get(id), m = me();
    if (!b || m.locked) { toast('Đang ngồi ở bàn, đợi hết lượt nhé.'); return; }
    const [tx, ty] = tileOf(b);
    const stand = [[tx, ty + 1], [tx - 1, ty], [tx + 1, ty], [tx, ty - 1]].filter(([x, y]) => !W.solidTile(x, y))
      .sort((p, q) => Math.hypot(p[0] - tileOf(m)[0], p[1] - tileOf(m)[1]) - Math.hypot(q[0] - tileOf(m)[0], q[1] - tileOf(m)[1]))[0];
    if (!stand) return;
    walkTo(m, stand[0], stand[1], () => { faceEachOther(m, b); openPerson(id); });
  }

  // ---------- actions bar ----------
  let actsKey = '';
  function renderActs(force) {
    const m = me();
    const list = m ? availableActs(m) : [];
    const key = list.join(',') + phase + (m && m.locked);
    if (key === actsKey && !force) return;
    actsKey = key;
    const box = $('acts'); box.replaceChildren();
    list.forEach((a, i) => {
      const b = btn('', H.ACTS[a].at ? 'spot' : '', () => doAct(a));
      b.append(document.createTextNode(H.ACTS[a].icon + ' ' + H.ACTS[a].label), el('small', '', String(i + 1)));
      b.disabled = !ev || phase === 'loivao' || phase === 'het' || (m.locked && H.ACTS[a].at);
      box.append(b);
    });
  }
  function doAct(a) { if (ev && me() && startAct(me(), a)) { if (fx() && a === 'nhay') me().hop = 220; } }
  const QUICK = ['Chào cả nhà!', 'Mưa đẹp ghê', 'Haha 😆', 'Bạn đang làm gì đó?', 'Mình hơi ngại 🙈'];
  for (const q of QUICK) $('quick').append(btn(q, '', () => speak(q)));
  function speak(text) {
    if (!ev) return;
    const t = H.sanitizeBubble(text);
    if (!t) return;
    const h = hearer();
    say(me(), t, 4.5, h ? h.id : null);
    cue = null; unread = 0; talkKey = '';
    if (phase === 'xoayban' && roundState && roundState.seated && !roundState.answered) { roundState.answered = true; renderPhaseCard(); }
    // the person you talk to answers: a question gets an answer, anything else a short reaction
    else if (h) {
      faceEachOther(me(), h);
      const q = /\?/.test(t);
      if (q || Math.random() < 0.7) later(900, () => say(h, q ? pick(H.person(ev, h.id).answer) : pick(H.REACTIONS), 5, 'you'));
    }
    renderTalk();
  }
  $('sayForm').addEventListener('submit', e => { e.preventDefault(); speak($('sayInput').value); $('sayInput').value = ''; });

  // ---------- input ----------
  const keys = new Set();
  const MOVE_KEYS = { w: 'up', arrowup: 'up', s: 'down', arrowdown: 'down', a: 'left', arrowleft: 'left', d: 'right', arrowright: 'right' };
  window.addEventListener('keydown', e => {
    if (modalOpen) return;
    const typing = e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT');
    if (typing) { if (e.key === 'Escape') e.target.blur(); return; }
    const k = e.key.toLowerCase();
    if (MOVE_KEYS[k]) { keys.add(MOVE_KEYS[k]); if (me()) { me().path = null; me().then = null; } e.preventDefault(); return; }
    // Enter only interacts from the page or the game; a focused button or link keeps its own Enter.
    const onControl = e.target && e.target.closest && e.target.closest('button, a, [role="button"]');
    if (k === 'e' || (k === 'enter' && !onControl)) { interact(); e.preventDefault(); return; }
    if (k === 't') { $('sayInput').focus(); e.preventDefault(); return; }
    if (/^[1-9]$/.test(k) && me()) { const a = availableActs(me())[Number(k) - 1]; if (a) doAct(a); }
  });
  window.addEventListener('keyup', e => { const d = MOVE_KEYS[e.key.toLowerCase()]; if (d) keys.delete(d); });
  window.addEventListener('blur', () => keys.clear());

  canvas.addEventListener('pointerdown', e => {
    if (!ev || modalOpen || phase === 'loivao') return;
    const r = canvas.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width * VW, y = (e.clientY - r.top) / r.height * VH;
    const hit = [...people.values()].filter(b => b.id !== 'you' && Math.abs(b.x - x) < 8 && y > b.y - 20 && y < b.y + 2)[0];
    if (hit) { goToPerson(hit.id); return; }
    const m = me();
    if (m.locked) { toast('Đang ngồi ở bàn, đợi hết lượt nhé.'); return; }
    const tx = Math.floor(x / T), ty = Math.floor(y / T);
    const d = bo.dog;
    if (Math.abs(d.x - x) < 8 && y > d.y - 14 && y < d.y + 2) { const st = bo.besideTile(tileOf(m)); if (st) walkTo(m, st[0], st[1], () => startAct(m, 'vuotcho')); return; }
    if (L.windowSeatAt(tx, ty) || L.nookAt(tx, ty)) { const act = L.windowSeatAt(tx, ty) ? 'cuaso' : 'nam'; walkTo(m, tx, ty, () => startAct(m, act)); return; }
    const spotName = Object.keys(W.SPOTS).find(n => W.SPOTS[n].tx === tx && W.SPOTS[n].ty === ty);
    if (spotName) {
      const s = W.SPOTS[spotName], stand = W.standTiles(s.tx, s.ty, tileOf(m))[0];
      if (stand) walkTo(m, stand[0], stand[1], () => { if (spotName === 'counter') talkHost(); else startAct(m, s.act); });
      return;
    }
    if (!W.solidTile(tx, ty)) walkTo(m, tx, ty);
  });

  function nearestThing() {
    const m = me();
    if (!m) return null;
    const p = [...people.values()].filter(b => b.id !== 'you' && dist(b, m) < 1.4).sort((a, b) => dist(a, m) - dist(b, m))[0];
    if (p) return { kind: 'person', id: p.id, label: p.name };
    if (dist(bo.dog, m) < 1.4) return { kind: 'dog', label: 'chó Bơ' };
    const [x, y] = tileOf(m);
    if (L.windowSeatAt(x, y) && !m.sit) return { kind: 'window', label: 'ghế cạnh cửa sổ' };
    if (L.nookAt(x, y) && !m.lie) return { kind: 'nook', label: 'góc gối lười' };
    const s = W.spotAt(x, y);
    if (s) return { kind: 'spot', name: s, label: W.SPOTS[s].label };
    return null;
  }
  function interact() {
    if (!ev || modalOpen || phase === 'loivao' || phase === 'het') return;
    const n = nearestThing();
    if (!n) return;
    if (n.kind === 'person') { faceEachOther(me(), people.get(n.id)); openPerson(n.id); }
    else if (n.kind === 'dog') startAct(me(), 'vuotcho');
    else if (n.kind === 'window') startAct(me(), 'cuaso');
    else if (n.kind === 'nook') startAct(me(), 'nam');
    else if (n.name === 'counter') talkHost();
    else startAct(me(), W.SPOTS[n.name].act);
  }
  function talkHost() {
    startAct(me(), 'goido'); me().drink = true;
    hostSay(phase === 'tudo' ? 'Cứ tự nhiên nha. Thấy ai dễ thương thì thả lá, không ai biết đâu.' : 'Ly này Cô Lá mời nè.');
  }
  $('actBtn').addEventListener('click', interact);

  // ---------- toast / banner ----------
  let toastTimer = null, bannerTimer = null;
  function toast(msg) {
    const t = $('toast'); t.textContent = msg; t.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, 3200);
  }
  // Phase titles and Cô Lá's announcements share one strip at the top, one message at a time.
  const bannerQueue = [];
  // now = a phase title: drop anything still waiting and show it straight away.
  function banner(msg, secs, now) {
    if (now) { bannerQueue.length = 0; clearTimeout(bannerTimer); bannerTimer = null; }
    bannerQueue.push([msg, secs || 3]);
    if (!bannerTimer) showNextBanner();
  }
  function showNextBanner() {
    const b = $('banner'), next = bannerQueue.shift();
    if (!next) { b.hidden = true; bannerTimer = null; return; }
    b.textContent = next[0]; b.hidden = false;
    bannerTimer = setTimeout(showNextBanner, next[1] * 1000);
  }
  function hostSay(text) { banner('☕ Cô Lá: ' + text, 6); }

  // ---------- drawing (the café look is shared with the everyday café in room.js) ----------
  const R = window.Room;
  const bg = R.background();
  function px(c, x, y, w, h) { R.px(ctx, c, x, y, w, h); }
  function drawSprite(b, hop) { R.person(ctx, b, clock, still(), hop); }
  function updateParticles(dt) {
    R.actParticles(people.values(), particles, dt, still());
    R.stepParticles(particles, dt);
    for (let i = lanterns.length - 1; i >= 0; i--) {
      const l = lanterns[i];
      l.life -= dt; l.y += l.vy * dt;
      if (l.life <= 0) lanterns.splice(i, 1);
    }
  }
  function drawParticles() {
    R.drawParticles(ctx, particles);
    for (const l of lanterns) {
      const sway = still() ? 0 : Math.round(Math.sin(clock * 2 + l.sway));
      const x = Math.round(l.x + sway), y = Math.round(l.y);
      ctx.fillStyle = 'rgba(255,217,138,.18)'; ctx.fillRect(x - 5, y - 5, 10, 12);
      px('#3a2418', x - 1, y - 4, 2, 1); px(l.color, x - 3, y - 3, 6, 7); px('#ffd98a', x - 1, y - 1, 2, 3); px('#3a2418', x - 2, y + 4, 4, 1);
    }
  }

  function render() {
    ctx.drawImage(bg, 0, 0);
    R.rain(ctx, clock, still());
    R.cat(ctx, clock, still(), [...people.values()].some(b => b.act === 'vuotmeo'));
    R.lamps(ctx);
    drawSprite(host, 0);
    R.counterFront(ctx);
    R.dogBed(ctx);
    const order = [...people.values(), bo.dog].sort((a, b) => a.y - b.y);
    for (const b of order) { if (b.isDog) R.dog(ctx, b, clock, still()); else drawSprite(b, b.hop > 0 && fx() ? Math.sin((b.hop / 300) * Math.PI) * 4 : 0); }
    drawParticles();
    if (NIGHT && !lightsOn && ev) {
      // A small torch around you; the rest of the room dims slowly to a cap. Never flickers.
      const cap = NIGHT.dimCap[courage];
      dim = Math.min(cap, dim + (still() ? cap : 0.003));
      const m = me(), gr = ctx.createRadialGradient(m.x, m.y - 8, 12, m.x, m.y - 8, 64);
      gr.addColorStop(0, 'rgba(8,6,16,0)'); gr.addColorStop(1, 'rgba(8,6,16,' + dim + ')');
      ctx.fillStyle = gr; ctx.fillRect(0, 0, VW, VH);
    }
    drawOverlay();
  }

  // Names, lantern colours and speech bubbles are HTML on top of the canvas so Vietnamese text stays sharp.
  const tags = new Map();
  function tagFor(b) {
    let t = tags.get(b.id);
    if (!t) {
      t = { root: el('div', 'who'), bubble: el('div', 'bubble'), tag: el('div', 'tag' + (b.id === 'you' ? ' you' : b.id === 'host' ? ' host' : '')), last: '' };
      t.bubble.hidden = true;
      t.icon = el('span'); t.nm = el('span', 'nm'); t.doing = el('span');
      t.tag.append(t.icon, t.nm, t.doing);
      t.root.append(t.bubble, t.tag); overlay.append(t.root); tags.set(b.id, t);
    }
    return t;
  }
  function drawOverlay() {
    const all = [host, ...people.values()];
    const live = new Set(all.map(b => b.id));
    for (const [id, t] of tags) if (!live.has(id)) { t.root.remove(); tags.delete(id); }
    const m = me();
    for (const b of all) {
      const t = tagFor(b);
      const icon = b.id === 'host' ? '☕' : H.LANTERNS[b.lantern].icon;
      const name = ' ' + (b.id === 'host' ? 'Cô Lá · người dẫn' : b.name + (b.id === 'you' ? ' (bạn)' : ''));
      const doing = b.act ? ' ' + H.ACTS[b.act].icon : '';
      if (t.icon.textContent !== icon) t.icon.textContent = icon;
      if (t.nm.textContent !== name) t.nm.textContent = name;
      if (t.doing.textContent !== doing) t.doing.textContent = doing;
      const bub = b.bubble && b.bubble.until > clock ? b.bubble : null;
      // On a small screen only nearby talk shows in full, so lines meant for you stand out.
      const seeRange = overlay.classList.contains('compact') ? 3 : SEE_TILES;
      const far = bub && b.id !== 'host' && b.id !== 'you' && m && dist(b, m) > seeRange && bub.to !== 'you';
      const toYou = !!(bub && bub.to === 'you');
      const text = bub ? (far ? '…' : bub.text) : '';
      const lastKey = text + toYou;
      if (lastKey !== t.last) {
        t.last = lastKey; t.bubble.textContent = text; t.bubble.hidden = !text;
        t.bubble.className = 'bubble' + (far ? ' far' : '') + (b.id === 'host' ? ' host' : '') + (toYou ? ' to-you' : '') + (text ? ' pop' : '');
      }
      t.tag.classList.toggle('talking', toYou || (b.id !== 'you' && b.id === talkTarget));
      // Above the head by default; flip below the feet when the bubble would leave the top of the room.
      const above = (b.y - 19 + (b.sit ? 3 : 0) + (b.lie ? 6 : 0)) * scale;
      const below = above - t.root.offsetHeight < 0;
      t.root.classList.toggle('below', below);
      const half = t.root.offsetWidth / 2, room = VW * scale;
      t.root.style.left = Math.min(room - half - 2, Math.max(half + 2, b.x * scale)) + 'px';
      t.root.style.top = (below ? (b.y + 1) * scale : above) + 'px';
      t.root.style.zIndex = String(Math.round(b.y) + (bub ? 200 : 0));
    }
  }

  // ---------- sizing ----------
  function fit() {
    const stage = $('stage');
    const dpr = window.devicePixelRatio || 1;
    const w = stage.clientWidth, h = stage.clientHeight;
    const fitScale = Math.min(w / VW, h / VH);
    let k = Math.max(1, Math.floor(fitScale * dpr));
    scale = k / dpr;
    if (scale < fitScale * 0.85) { k = Math.ceil(fitScale * dpr); scale = fitScale; }
    canvas.width = VW * k; canvas.height = VH * k;
    const cw = Math.floor(VW * scale), ch = Math.floor(VH * scale);
    canvas.style.width = cw + 'px'; canvas.style.height = ch + 'px';
    ctx.setTransform(k, 0, 0, k, 0, 0);
    ctx.imageSmoothingEnabled = false;
    // Small rooms (phones) show only the lantern and what people are doing; your own name stays.
    overlay.classList.toggle('compact', scale < 1.9);
    Object.assign(overlay.style, { left: Math.round((w - cw) / 2) + 'px', top: Math.round((h - ch) / 2) + 'px', width: cw + 'px', height: ch + 'px' });
  }
  window.addEventListener('resize', fit);

  // ---------- loop ----------
  let last = 0, held = false, lastNear = '';
  function tick(dt) {
    if (ev && !modalOpen) clock += dt;
    if (ev) {
      const m = me();
      // you
      if (m.path) followPath(m, dt);
      else if (!m.locked && !modalOpen && keys.size) {
        const ix = (keys.has('right') ? 1 : 0) - (keys.has('left') ? 1 : 0), iy = (keys.has('down') ? 1 : 0) - (keys.has('up') ? 1 : 0);
        if (ix || iy) {
          const len = Math.hypot(ix, iy), sp = 64 * dt;
          const body = { x: m.x - 4, y: m.y - 4, w: 8, h: 5 };
          const moved = W.moveWithSlide(body, ix / len * sp, iy / len * sp);
          m.x = moved.x + 4; m.y = moved.y + 4; m.moving = true; m.act = null; standUp(m);
          m.dir = Math.abs(ix) >= Math.abs(iy) && ix ? (ix > 0 ? 'right' : 'left') : (iy > 0 ? 'down' : 'up');
        }
      }
      for (const b of people.values()) {
        if (b !== m) { if (b.path) followPath(b, dt); else if (phase === 'tudo' || (phase === 'lycuoi' && !b.locked)) guestThink(b, dt); }
        if (b.act && b.actUntil <= clock) b.act = null;
        if (b.bubble && b.bubble.until <= clock) b.bubble = null;
        if (b.moving) b.walkMs += dt * 1000; else b.walkMs = 0;
        if (b.hop > 0) b.hop = Math.max(0, b.hop - dt * 1000);
      }
      if (host.bubble && host.bubble.until <= clock) host.bubble = null;
      if (!modalOpen) {
        if (NIGHT && !lightsOn && phase === 'tudo' && clock >= beatAt && beatIx < NIGHT.beats.length) {
          const beat = NIGHT.beats[beatIx++];
          banner('👻 ' + beat.scare, 4);
          later(4000, () => hostSay(beat.reveal));
          beatAt = clock + (FAST ? 12 : 26);
        }
        observeAll(dt);
        bo.think(dt);
        if (phase === 'tudo') guestSocial(dt);
        if (phase === 'xoayban') roundTick();
        if (phase === 'lycuoi') lastDrinkTick();
        if (['tudo', 'xoayban', 'lycuoi'].includes(phase) && clock >= phaseEnd) {
          if (phase === 'lycuoi') setPhase('het'); else nextPhase();
        }
      }
      updateParticles(dt);
      updateClock();
      renderActs();
      guestsTimer -= dt;
      if (guestsTimer <= 0) { guestsTimer = 1; renderGuests(); renderTalk(); }
      const n = modalOpen ? null : nearestThing();
      const key = n ? n.kind + n.label + phase : '';
      if (key !== lastNear) {
        lastNear = key;
        const b = $('actBtn');
        if (n) { b.disabled = false; b.textContent = (n.kind === 'person' ? 'Gặp ' : n.kind === 'dog' ? 'Chơi với ' : n.kind === 'window' ? 'Ngồi · ' : n.kind === 'nook' ? 'Nằm đọc sách · ' : n.name === 'counter' ? 'Gọi đồ · ' : H.ACTS[W.SPOTS[n.name].act].label + ' · ') + n.label + ' (E)'; $('near').textContent = 'Gần ' + n.label + '.'; }
        else { b.disabled = true; b.textContent = 'Lại gần ai đó hoặc đồ vật'; $('near').textContent = ''; }
      }
    }
    render();
    for (const b of people.values()) b.moving = false;
  }
  function frame(now) {
    try { if (!held) { const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now; tick(dt); } }
    finally { schedule(); }
  }
  // Hidden tabs get no animation frames; fall back to a slow timer so state still advances.
  function schedule() { if (document.hidden) setTimeout(() => frame(performance.now()), 50); else requestAnimationFrame(frame); }

  // ---------- settings ----------
  const MOTION_LABEL = { full: 'Cử động: đầy đủ', reduced: 'Cử động: giảm', off: 'Cử động: tắt' };
  function applyMotion() {
    document.body.classList.toggle('reduced', motion === 'reduced');
    document.body.classList.toggle('still', motion === 'off');
    $('motionBtn').textContent = MOTION_LABEL[motion];
    if (!fx()) particles.length = 0;
  }
  $('motionBtn').addEventListener('click', () => { motion = { full: 'reduced', reduced: 'off', off: 'full' }[motion]; applyMotion(); toast(MOTION_LABEL[motion]); });
  function restart() {
    gen += 1; // drop callbacks scheduled for the evening that just ended
    talkLog.length = 0; talkTarget = null; cue = null; unread = 0; talkKey = '';
    if (NIGHT) { lightsOn = false; dim = 0; $('scaredBtn').hidden = true; }
    seed = Math.floor(Math.random() * 1e9);
    ev = null; phase = 'loivao'; clock = 0; people.clear(); couples = []; particles.length = 0; lanterns.length = 0;
    renderTrack(); renderPhaseCard(); renderHalf(); renderGuests(); renderActs(true);
    openSetup();
  }
  $('scaredBtn').addEventListener('click', () => {
    lightsOn = true; $('scaredBtn').hidden = true;
    hostSay('Đèn quán bật sáng rồi. Ai bấm cũng được, không cần giải thích.');
  });
  $('restartBtn').addEventListener('click', () => {
    if (!ev) return;
    const body = openModal('CHỈ TRONG TAB NÀY', 'Bắt đầu một buổi khác?');
    body.append(el('p', '', 'Buổi đang diễn ra sẽ mất. Khách mời được xếp lại từ đầu.'), btn('Buổi khác', 'primary', () => { closeModal(); restart(); }), document.createTextNode(' '), btn('Ở lại buổi này', 'ghost', closeModal));
  });

  // ---------- boot ----------
  applyMotion();
  fit();
  renderTrack(); renderPhaseCard(); renderActs(true);
  schedule();
  openSetup();
  window.__hen = {
    hold: v => { held = v; },
    step: ms => { for (let t = 0; t < ms; t += 16) tick(0.016); },
    ev: () => ev, phase: () => phase, people, me, clock: () => clock, round: () => round, roundState: () => roundState, couples: () => couples,
    begin: c => { closeModal(); beginEvening(Object.assign({ name: H.NICKNAMES[0], look: 0, item: H.ITEMS[0], lantern: 'thuong' }, c || {})); },
    next: nextPhase, release: () => releaseLanterns(), restart: () => restart(), act: doAct, speak, interact, goToPerson, walkTo: (tx, ty) => walkTo(me(), tx, ty), pickIngredient, closeModal, modalOpen: () => modalOpen
  };
})();
