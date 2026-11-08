// Quán Lá ngày thường: drop in, sit a while, greet strangers with a bow, take home a drink, a card and a kind word.
// Shares the café map (World), look (Room) and sprites (Engine) with the matchmaking evening.
(function () {
  'use strict';
  const H = window.Hen, W = window.World, E = window.Engine, R = window.Room, Q = window.Quan;
  const $ = id => document.getElementById(id);
  const T = W.TILE, VW = W.W * T, VH = W.H * T;
  const params = new URLSearchParams(location.search);
  const hourOverride = params.has('gio') ? Number(params.get('gio')) : null;
  const nowHour = () => hourOverride != null && !Number.isNaN(hourOverride) ? hourOverride : new Date().getHours();

  const canvas = $('game'), ctx = canvas.getContext('2d'), overlay = $('overlay');
  let scale = 1;
  let motion = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'reduced' : 'full';
  const still = () => motion === 'off';

  // Acts here: a quiet subset of the evening's acts, plus a bow and sitting down.
  const ACTS = Object.assign({}, H.ACTS, {
    chaptay: { label: 'Chắp tay', verb: 'chắp tay chào', icon: '🙏' },
    ngoi: { label: 'Ngồi', verb: 'ngồi xuống', icon: '🪑' },
    lamviec: { label: 'Lấy đồ ra', verb: 'lấy đồ ra', icon: '💼' },
    cat: { label: 'Cất đồ', verb: 'cất đồ', icon: '👜' }
  }, Q.PLACE_ACTS);
  const FREE = ['chaptay', 'vaytay', 'nhay', 'ngugat'];
  const rand = Math.random;

  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function btn(text, cls, fn) { const b = el('button', cls, text); b.type = 'button'; b.addEventListener('click', fn); return b; }
  function pick(list) { return list[Math.floor(rand() * list.length)]; }

  // ---------- people ----------
  let clock = 0, seq = 0;
  const people = new Map();
  const particles = [];
  const LOOKS = H.LOOKS.concat(H.GUESTS.map(g => g.look));
  const host = { id: 'host', host: true, name: 'Cô Lá', x: W.HOST.tx * T + 8, y: W.HOST.ty * T + 7, dir: 'down', sheet: E.buildSheet({ H: '#2b2230', T: '#3f6b55', C: '#7fc8a0', P: '#30303a', B: '#1d1b26', longHair: true, hat: true }) };
  function feetOf(tx, ty) { return { x: tx * T + 8, y: ty * T + 12 }; }
  function tileOf(p) { return [Math.floor(p.x / T), Math.floor((p.y - 1) / T)]; }
  function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y) / T; }
  function body(id, name, look, npc) {
    return Object.assign({ id, name, npc, dir: 'up', path: null, then: null, act: null, actUntil: 0, sit: false, sitUntil: 0, bubble: null, walkMs: 0, moving: false,
      blinkAt: rand() * 4, sheet: E.buildSheet(look), drink: null, greeted: false, gear: Q.packBag(rand), task: false, steamT: rand() * 3, lie: false, seatKind: null }, feetOf(...W.ENTRY));
  }
  let me = null, myNotes = [], myDrink = null, myCard = null, myLine = null;
  function enter() {
    people.clear(); particles.length = 0; myNotes = []; myDrink = null; myCard = null; myLine = null;
    me = body('you', Q.randomName(rand), pick(H.LOOKS), false);
    people.set('you', me);
    // guests already sitting when you arrive
    for (let i = 0; i < Q.crowd(nowHour()); i++) spawnGuest(true);
    renderPanel(); renderNotes(); renderCard(); renderGear();
    toast('Bạn vào quán với tên ' + me.name + '.');
    hostSay(Q.hostLine(nowHour(), rand));
  }

  // ---------- movement ----------
  function walkTo(b, tx, ty, then) {
    const path = W.findPath(tileOf(b), [tx, ty]);
    if (!path) return false;
    b.sit = false; b.lie = false; b.seatKind = null; b.act = null; b.task = false;
    b.path = path.slice(1); b.then = then || null;
    if (!b.path.length) { b.path = null; const t = b.then; b.then = null; if (t) t(); }
    return true;
  }
  function followPath(b, dt) {
    const [tx, ty] = b.path[0], goal = feetOf(tx, ty);
    const dx = goal.x - b.x, dy = goal.y - b.y, d = Math.hypot(dx, dy), step = (b.npc ? 40 : 60) * dt;
    if (d <= step) {
      b.x = goal.x; b.y = goal.y; b.path.shift();
      if (!b.path.length) { b.path = null; const t = b.then; b.then = null; if (t) t(); }
    } else { b.x += dx / d * step; b.y += dy / d * step; }
    if (Math.abs(dx) > Math.abs(dy)) b.dir = dx > 0 ? 'right' : 'left'; else if (dy) b.dir = dy > 0 ? 'down' : 'up';
    b.moving = true;
  }

  // ---------- seats, acts, speech ----------
  function seatAt(tx, ty) {
    for (const t of W.TABLES) for (const s of t.seats) if (s[0] === tx && s[1] === ty) return { table: t, seat: s };
    return null;
  }
  const onList = (list, tx, ty) => list.some(([x, y]) => x === tx && y === ty);
  const windowSeatAt = (tx, ty) => onList(W.WINDOW_SEATS, tx, ty);
  const nookAt = (tx, ty) => onList(W.NOOK, tx, ty);
  function seatTaken(s, except) {
    return [...people.values()].some(b => b !== except && (b.sit || b.lie || b.goingTo) && (() => { const [x, y] = b.goingTo || tileOf(b); return x === s[0] && y === s[1]; })());
  }
  function sitDown(b) {
    const [tx, ty] = tileOf(b);
    if (windowSeatAt(tx, ty)) {
      Object.assign(b, feetOf(tx, ty));
      b.sit = true; b.seatKind = 'window'; b.lie = false; b.act = null; b.path = null; b.goingTo = null; b.task = false; b.dir = 'up';
      return true;
    }
    const here = seatAt(tx, ty);
    if (!here) return false;
    b.sit = true; b.seatKind = 'table'; b.lie = false; b.act = null; b.path = null; b.goingTo = null; b.task = false;
    b.dir = b.x < here.table.tx * T + 8 ? 'right' : 'left';
    return true;
  }
  function lieDown(b) {
    const [tx, ty] = tileOf(b);
    if (!nookAt(tx, ty)) return false;
    Object.assign(b, feetOf(tx, ty));
    b.lie = true; b.sit = false; b.seatKind = null; b.act = null; b.path = null; b.goingTo = null; b.task = false;
    return true;
  }
  function startAct(b, act) {
    if (act === 'ngoi' || act === 'cuaso') return sitDown(b);
    if (act === 'nam') return lieDown(b);
    if (act === 'uong') {
      if (!b.drink) return false;
      b.drinkColor = Q.DRINKS[b.drink].color; b.act = 'uong'; b.actUntil = clock + 3;
      return true;
    }
    if (act === 'vuotcho') {
      if (dist(b, dog) > 1.6) return false;
      b.sit = false; b.lie = false; b.seatKind = null; b.task = false;
      b.dir = Math.abs(dog.x - b.x) >= Math.abs(dog.y - b.y) ? (dog.x > b.x ? 'right' : 'left') : (dog.y > b.y ? 'down' : 'up');
      b.act = 'vuotcho'; b.actUntil = clock + 4;
      petDog(b);
      return true;
    }
    if (act === 'lamviec' || act === 'cat') { if (!b.sit) return false; b.task = act === 'lamviec'; b.act = null; return true; }
    const a = ACTS[act];
    if (!a) return false;
    if (a.at) {
      const s = W.spotAt(...tileOf(b));
      if (!s || W.SPOTS[s].act !== act) return false;
      const spot = W.SPOTS[s];
      const [x, y] = tileOf(b), dx = spot.tx - x, dy = spot.ty - y;
      b.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
    }
    if (act !== 'ngugat' && act !== 'chaptay' && act !== 'vaytay') { b.sit = false; b.seatKind = null; b.task = false; }
    if (act !== 'ngugat') b.lie = false;
    b.act = act; b.actUntil = clock + (act === 'ngugat' ? 8 : act === 'chaptay' ? 2.5 : 6);
    if (act === 'ngammua') b.dir = 'up';
    if (act === 'chaptay' && !b.sit) b.dir = 'down';
    return true;
  }
  function say(b, text, secs) { b.bubble = { text: H.sanitizeBubble(text, 40), until: clock + (secs || 3.5) }; }
  function availableActs(b) {
    const list = FREE.slice();
    if (b.drink) list.push('uong');
    const [x, y] = tileOf(b);
    const s = W.spotAt(x, y);
    if (s && W.SPOTS[s].act !== 'goido' && !b.lie) list.push(W.SPOTS[s].act);
    if (seatAt(x, y) && !b.sit) list.push('ngoi');
    if (windowSeatAt(x, y) && !b.sit) list.push('cuaso');
    if (nookAt(x, y) && !b.lie) list.push('nam');
    if (dist(b, dog) < 1.6) list.push('vuotcho');
    if (b.sit && b.seatKind === 'table') list.push(b.task ? 'cat' : 'lamviec');
    return list;
  }

  // ---------- guests come and go ----------
  function spawnGuest(alreadyIn) {
    const taken = new Set([...people.values()].map(b => b.name));
    let name = Q.randomName(rand);
    for (let i = 0; i < 10 && taken.has(name); i++) name = Q.randomName(rand);
    const g = body('g' + (++seq), name, pick(LOOKS), true);
    g.plan = Q.visitPlan(rand);
    g.leaveAt = clock + 70 + rand() * 120;
    g.idle = rand() * 2;
    if (alreadyIn) {
      const seats = W.TABLES.flatMap(t => t.seats).filter(s => !seatTaken(s));
      const s = pick(seats);
      if (s) { Object.assign(g, feetOf(...s)); people.set(g.id, g); sitDown(g); g.task = true; g.sitUntil = clock + 20 + rand() * 40; g.drink = pick(Object.keys(Q.DRINKS)); return g; }
    }
    people.set(g.id, g);
    return g;
  }
  function leave(g) {
    g.leaving = true; g.plan = [];
    if (rand() < 0.5) say(g, 'Mình về đây', 3);
    walkTo(g, W.ENTRY[0], W.ENTRY[1], () => { people.delete(g.id); });
  }
  function guestThink(g, dt) {
    if (g.path || g.leaving) return;
    if (g.act && g.actUntil > clock) return;
    if ((g.sit || g.lie) && g.sitUntil > clock) {
      if (!g.act && g.drink && rand() < dt * 0.05) startAct(g, 'uong');
      else if (!g.act && rand() < dt * (g.task ? 0.012 : g.lie ? 0.05 : 0.04)) startAct(g, 'ngugat');
      return;
    }
    g.idle -= dt;
    if (g.idle > 0) return;
    g.idle = 1 + rand() * 3;
    if (clock > g.leaveAt || !g.plan.length) { leave(g); return; }
    const next = g.plan.shift();
    if (next === 'cuaso' || next === 'nam') {
      const list = (next === 'cuaso' ? W.WINDOW_SEATS : W.NOOK).filter(s => !seatTaken(s, g));
      const s = pick(list);
      if (!s) return;
      g.goingTo = s;
      walkTo(g, s[0], s[1], () => { g.goingTo = null; if (next === 'cuaso') sitDown(g); else lieDown(g); g.sitUntil = clock + 18 + rand() * 25; });
      return;
    }
    if (next === 'vuotcho') {
      const [dx, dy] = tileOf(dog);
      const stand = W.standTiles(dx, dy, tileOf(g)).concat([[dx, dy]]).find(([x, y]) => !W.solidTile(x, y));
      if (stand) walkTo(g, stand[0], stand[1], () => startAct(g, 'vuotcho'));
      return;
    }
    if (next === 'nhay') { startAct(g, 'nhay'); g.actUntil = clock + 4; return; }
    if (next === 'ngoi') {
      const seats = W.TABLES.flatMap(t => t.seats).filter(s => !seatTaken(s, g));
      const s = pick(seats);
      if (!s) return;
      g.goingTo = s;
      walkTo(g, s[0], s[1], () => { sitDown(g); g.sitUntil = clock + 20 + rand() * 35 + (g.gear.thing === 'laptop' ? 20 : 0); setTimeout(() => { if (g.sit) g.task = true; }, 1200); });
      return;
    }
    const spots = Object.values(W.SPOTS).filter(s => s.act === next);
    const s = pick(spots);
    const stand = s && W.standTiles(s.tx, s.ty, tileOf(g))[0];
    if (stand) walkTo(g, stand[0], stand[1], () => { startAct(g, next); if (next === 'goido') g.drink = pick(Object.keys(Q.DRINKS)); });
  }
  // Guests bow to you once when they pass close; they bow back when you greet them.
  function greetings() {
    for (const g of people.values()) {
      if (!g.npc || g.greeted || g.leaving) continue;
      if (dist(g, me) < 1.6 && rand() < 0.6) { g.greeted = true; startAct(g, 'chaptay'); say(g, pick(['Chào bạn 🙏', 'Bình yên nha']), 3); }
      else if (dist(g, me) < 1.6) g.greeted = true;
    }
  }
  function greetBack() {
    const near = [...people.values()].filter(g => g.npc && !g.leaving && dist(g, me) < 2.2).sort((a, b) => dist(a, me) - dist(b, me))[0];
    if (!near) return;
    setTimeout(() => { if (people.has(near.id)) { startAct(near, 'chaptay'); say(near, pick(['Chào bạn 🙏', 'Bình yên nha', 'Mưa đẹp ghê']), 3); } }, 600);
  }
  let crowdTimer = 0;
  function keepCrowd(dt) {
    crowdTimer -= dt;
    if (crowdTimer > 0) return;
    crowdTimer = 8 + rand() * 10;
    const guests = [...people.values()].filter(b => b.npc && !b.leaving).length;
    if (guests < Q.crowd(nowHour())) spawnGuest(false);
  }

  // ---------- Bơ, the café dog ----------
  const dog = Object.assign({ id: 'dog', isDog: true, name: Q.DOG.name, dir: 'right', path: null, then: null, idle: 2, moving: false, walkMs: 0, sitting: true, petted: 0, hop: 0, bubble: null }, feetOf(...W.DOG_BED));
  function dogWalk(tx, ty, then) {
    const path = W.findPath(tileOf(dog), [tx, ty]);
    if (!path) return;
    dog.sitting = false; dog.path = path.slice(1); dog.then = then || null;
    if (!dog.path.length) { dog.path = null; if (then) then(); }
  }
  function dogFollow(dt) {
    const [tx, ty] = dog.path[0], goal = feetOf(tx, ty);
    const dx = goal.x - dog.x, dy = goal.y - dog.y, d = Math.hypot(dx, dy), step = 34 * dt;
    if (d <= step) { dog.x = goal.x; dog.y = goal.y; dog.path.shift(); if (!dog.path.length) { dog.path = null; const t = dog.then; dog.then = null; if (t) t(); } }
    else { dog.x += dx / d * step; dog.y += dy / d * step; }
    if (Math.abs(dx) > 0.5) dog.dir = dx > 0 ? 'right' : 'left';
    dog.moving = true;
  }
  function petDog(by) {
    dog.path = null; dog.then = null; dog.sitting = true; dog.petted = clock + 3.5; dog.idle = 4;
    dog.dir = by.x < dog.x ? 'left' : 'right';
    if (!still()) { dog.hop = 2; for (let i = 0; i < 3; i++) particles.push({ kind: 'heart', x: dog.x - 2 + i * 3, y: dog.y - 16, vx: 0, vy: -8, life: 1 + i * 0.2 }); }
  }
  function dogThink(dt) {
    if (dog.hop > 0) dog.hop = Math.max(0, dog.hop - dt * 8);
    if (dog.path) { dogFollow(dt); return; }
    if (dog.petted > clock) return;
    dog.idle -= dt; if (dog.idle > 0) return;
    dog.idle = 3 + rand() * 5;
    const r = rand(), free = W.freeTiles().filter(([x, y]) => y >= 3);
    if (r < 0.3 && me) {
      // trot over and sit next to you
      const st = W.standTiles(...tileOf(me), tileOf(dog)).find(([x, y]) => !W.solidTile(x, y));
      if (st) dogWalk(st[0], st[1], () => { dog.sitting = true; dog.dir = me.x < dog.x ? 'left' : 'right'; });
    } else if (r < 0.5) dogWalk(W.DOG_BED[0], W.DOG_BED[1], () => { dog.sitting = true; dog.idle = 8 + rand() * 6; });
    else { const t = pick(free); dogWalk(t[0], t[1], () => { dog.sitting = rand() < 0.5; }); }
  }

  // ---------- player actions ----------
  function doAct(a) {
    if (!startAct(me, a)) return;
    if (a === 'chaptay' || a === 'vaytay') greetBack();
  }
  function greet(text) { say(me, text, 3.5); if (/Chào|Bình yên/.test(text)) greetBack(); }
  function nearestThing() {
    const p = [...people.values()].filter(b => b.npc && dist(b, me) < 1.4).sort((a, b) => dist(a, me) - dist(b, me))[0];
    if (p) return { kind: 'person', id: p.id, label: p.name };
    if (dist(dog, me) < 1.4) return { kind: 'dog', label: Q.DOG.name };
    const [x, y] = tileOf(me);
    const s = W.spotAt(x, y);
    if (s) return { kind: 'spot', name: s, label: W.SPOTS[s].label };
    if (seatAt(x, y) && !me.sit) return { kind: 'seat', label: 'ghế' };
    if (windowSeatAt(x, y) && !me.sit) return { kind: 'window', label: 'ghế cạnh cửa sổ' };
    if (nookAt(x, y) && !me.lie) return { kind: 'nook', label: 'góc đọc sách' };
    return null;
  }
  function interact() {
    if (modalOpen) return;
    const n = nearestThing();
    if (!n) return;
    if (n.kind === 'person') { const g = people.get(n.id); me.dir = g.x < me.x ? 'left' : g.x > me.x ? 'right' : me.dir; doAct('chaptay'); }
    else if (n.kind === 'seat' || n.kind === 'window') sitDown(me);
    else if (n.kind === 'nook') lieDown(me);
    else if (n.kind === 'dog') doAct('vuotcho');
    else if (n.name === 'counter') openCounter();
    else doAct(W.SPOTS[n.name].act);
  }

  // ---------- Cô Lá at the counter ----------
  function openCounter() {
    const body = openModal('QUẦY', 'Cô Lá');
    body.append(el('p', '', myDrink ? 'Ly ' + Q.DRINKS[myDrink].label.toLowerCase() + ' của bạn còn ấm đó.' : 'Uống gì nè?'));
    const row = el('div', 'choices');
    for (const [k, d] of Object.entries(Q.DRINKS)) {
      const b = btn(d.label, '', () => { myDrink = k; me.drink = k; closeModal(); startAct(me, 'goido'); hostSay('Một ly ' + d.label.toLowerCase() + ' nè. Ngồi đâu cũng được.'); });
      b.setAttribute('aria-pressed', myDrink === k ? 'true' : 'false');
      row.append(b);
    }
    body.append(row);
    body.append(btn(myCard ? 'Xem lại lá bài hôm nay' : 'Xin lá bài hôm nay', 'primary', () => {
      myCard = Q.dailyCard(Q.dateKey(new Date()));
      closeModal(); renderCard();
      hostSay('Hôm nay là lá ' + myCard.card + '. ' + myCard.todo);
    }), document.createTextNode(' '), btn('Nói chuyện với Cô Lá', 'ghost', () => {
      myLine = Q.hostLine(nowHour(), rand); closeModal(); hostSay(myLine);
    }));
  }

  // ---------- panel ----------
  function renderPanel() {
    const h = nowHour(), d = new Date();
    $('clockLabel').textContent = 'BÂY GIỜ ' + String(hourOverride != null ? h : d.getHours()).padStart(2, '0') + ':' + String(hourOverride != null ? 0 : d.getMinutes()).padStart(2, '0');
    const guests = [...people.values()].filter(b => b.npc && !b.leaving).length;
    $('crowdLabel').textContent = Q.crowdLabel(guests);
    $('youName').textContent = 'Bạn là ' + (me ? me.name : '…') + '. Ai cũng chỉ thấy tên Lá của nhau.';
    const board = $('eventBoard'); board.replaceChildren();
    const ev = Q.NEXT_EVENT;
    board.append(el('p', '', 'Buổi hẹn sắp tới: ' + ev.title + ' · ' + ev.mode + ' · ' + ev.when + '.'),
      el('p', 'note-hint', 'Bối cảnh: ' + ev.setting + '. Mỗi buổi chọn 10–12 người.'),
      btn('Mình muốn hẹn', 'pickbtn', () => toast('Bản thử chưa nhận đăng ký. Ở bản thật, bạn nhận thư mời nếu được chọn.')), document.createTextNode(' '),
      (() => { const l = el('a', 'chip', '👻 Chơi thử buổi này'); l.href = 'index.html?buoi=dem'; return l; })());
  }
  function renderGear() {
    const box = $('gearBox'); box.replaceChildren();
    const g = me.gear;
    const row = (title, table, key) => {
      const wrap = el('div', 'choices gear');
      wrap.setAttribute('role', 'group'); wrap.setAttribute('aria-label', title);
      for (const [k, v] of Object.entries(table)) {
        const b = btn(v.icon + ' ' + v.label, '', () => { g[key] = k; if (key === 'thing') me.task = false; actsKey = ''; renderGear(); });
        b.setAttribute('aria-pressed', g[key] === k ? 'true' : 'false');
        wrap.append(b);
      }
      box.append(el('div', 'field', title), wrap);
    };
    row('Mang theo để làm', Q.THINGS, 'thing');
    row('Túi', Q.BAGS, 'bag');
    const u = btn((g.umbrella ? '☂️ Có mang ô' : '🌂 Không mang ô'), '', () => { g.umbrella = !g.umbrella; renderGear(); });
    u.setAttribute('aria-pressed', g.umbrella ? 'true' : 'false');
    const w = el('div', 'choices gear'); w.append(u); box.append(w);
  }
  function renderCard() {
    const box = $('cardBox'); box.replaceChildren();
    if (!myCard) { box.append(el('b', '', '🃏 Lá bài hôm nay'), el('div', '', 'Hỏi Cô Lá ở quầy để xin. Lá bài chỉ gợi một việc nhỏ, không phán gì về bạn.')); return; }
    box.append(el('b', '', '🃏 ' + myCard.card), el('div', '', myCard.todo));
  }
  function renderNotes() {
    $('noteCount').textContent = myNotes.length ? 'Bạn đã cất ' + myNotes.length + '/' + Q.NOTE_LIMIT + ' note. Lúc về sẽ đọc lại.' : '';
    $('noteInput').disabled = myNotes.length >= Q.NOTE_LIMIT;
  }
  $('noteForm').addEventListener('submit', e => {
    e.preventDefault();
    const t = Q.sanitizeNote($('noteInput').value);
    if (!t || myNotes.length >= Q.NOTE_LIMIT) return;
    myNotes.push(t); $('noteInput').value = ''; renderNotes(); toast('Đã cất note.');
  });

  // ---------- leaving ----------
  function openLeave() {
    if (!myCard) myCard = Q.dailyCard(Q.dateKey(new Date()));
    if (!myLine) myLine = Q.hostLine(nowHour(), rand);
    renderCard();
    const body = openModal('VỀ THÔI', 'Cảm ơn ' + me.name + ' đã ghé');
    if (myDrink) {
      const row = el('div', 'takeaway');
      const c = document.createElement('canvas'); c.width = 12; c.height = 12; c.className = 'cup'; c.setAttribute('aria-hidden', 'true');
      drawCup(c.getContext('2d'), 2, 1, myDrink);
      row.append(c, el('span', '', 'Ly của bạn: ' + Q.DRINKS[myDrink].label));
      body.append(row);
    } else body.append(el('p', 'note', 'Lần này bạn chưa gọi ly nào. Lần sau Cô Lá pha cho nhé.'));
    body.append(el('div', 'letter', '🃏 ' + myCard.card + ': ' + myCard.todo), el('div', 'letter', '☕ Cô Lá: ' + myLine));
    if (myNotes.length) { body.append(el('div', 'field', 'Note bạn để lại')); for (const n of myNotes) body.append(el('div', 'letter', n)); }
    const ev = Q.NEXT_EVENT;
    body.append(el('p', 'note', 'Buổi hẹn sắp tới: ' + ev.title + ' · ' + ev.when + '.'));
    body.append(btn('Ngồi thêm chút', 'ghost', closeModal), document.createTextNode(' '), btn('Ra về', 'primary', () => { closeModal(); leaveCafe(); }));
  }
  function leaveCafe() {
    walkTo(me, W.ENTRY[0], W.ENTRY[1], () => {
      const body = openModal('ĐÃ RA VỀ', 'Hẹn gặp lại', false);
      body.append(el('p', '', 'Quán vẫn mở. Lúc nào muốn thì ghé, không ai đếm ngày.'), btn('Ghé lại', 'primary', () => { closeModal(); enter(); }));
    });
  }
  $('leaveBtn').addEventListener('click', () => { if (!modalOpen) openLeave(); });

  // ---------- modal ----------
  let modalOpen = false, modalClosable = true;
  function openModal(kicker, title, closable) {
    $('mKicker').textContent = kicker; $('mTitle').textContent = title;
    const body = $('mBody'); body.replaceChildren();
    modalClosable = closable !== false; $('mClose').hidden = !modalClosable;
    $('shade').hidden = false; modalOpen = true; keys.clear();
    setTimeout(() => { const f = $('modal').querySelector('button:not([hidden]), input'); if (f) f.focus(); }, 0);
    return body;
  }
  function closeModal() { $('shade').hidden = true; modalOpen = false; }
  $('mClose').addEventListener('click', () => { if (modalClosable) closeModal(); });
  $('shade').addEventListener('click', e => { if (e.target === $('shade') && modalClosable) closeModal(); });
  $('modal').addEventListener('keydown', e => {
    if (e.key === 'Escape' && modalClosable) { e.preventDefault(); closeModal(); }
    if (e.key === 'Tab') {
      const f = [...$('modal').querySelectorAll('button:not([hidden]):not(:disabled), input')];
      if (!f.length) return;
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    }
  });

  // ---------- toast / banner ----------
  let toastTimer = null, bannerTimer = null;
  function toast(msg) { const t = $('toast'); t.textContent = msg; t.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, 3200); }
  function hostSay(text) { const b = $('banner'); b.textContent = '☕ Cô Lá: ' + text; b.hidden = false; clearTimeout(bannerTimer); bannerTimer = setTimeout(() => { b.hidden = true; }, 6000); }

  // ---------- action bar ----------
  let actsKey = '';
  function renderActs() {
    const list = availableActs(me);
    const key = list.join(',') + me.sit + me.gear.thing;
    if (key === actsKey) return;
    actsKey = key;
    const box = $('acts'); box.replaceChildren();
    list.forEach((a, i) => {
      const th = Q.THINGS[me.gear.thing];
      const label = a === 'lamviec' ? th.icon + ' ' + th.verb : a === 'cat' ? '👜 Cất ' + th.label.toLowerCase() : ACTS[a].icon + ' ' + ACTS[a].label;
      const b = btn('', ACTS[a].at || a === 'ngoi' || a === 'lamviec' ? 'spot' : '', () => doAct(a));
      b.append(document.createTextNode(label), el('small', '', String(i + 1)));
      box.append(b);
    });
  }
  for (const g of Q.GREETINGS) $('quick').append(btn(g, '', () => greet(g)));

  // ---------- input ----------
  const keys = new Set();
  const MOVE_KEYS = { w: 'up', arrowup: 'up', s: 'down', arrowdown: 'down', a: 'left', arrowleft: 'left', d: 'right', arrowright: 'right' };
  window.addEventListener('keydown', e => {
    if (modalOpen) return;
    if (e.target && e.target.tagName === 'INPUT') { if (e.key === 'Escape') e.target.blur(); return; }
    const k = e.key.toLowerCase();
    if (MOVE_KEYS[k]) { keys.add(MOVE_KEYS[k]); me.path = null; me.then = null; e.preventDefault(); return; }
    const onControl = e.target && e.target.closest && e.target.closest('button, a, [role="button"]');
    if (k === 'e' || (k === 'enter' && !onControl)) { interact(); e.preventDefault(); return; }
    if (/^[1-9]$/.test(k)) { const a = availableActs(me)[Number(k) - 1]; if (a) doAct(a); }
  });
  window.addEventListener('keyup', e => { const d = MOVE_KEYS[e.key.toLowerCase()]; if (d) keys.delete(d); });
  window.addEventListener('blur', () => keys.clear());
  canvas.addEventListener('pointerdown', e => {
    if (modalOpen) return;
    const r = canvas.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width * VW, y = (e.clientY - r.top) / r.height * VH;
    const tx = Math.floor(x / T), ty = Math.floor(y / T);
    const hit = [...people.values()].find(b => b.npc && Math.abs(b.x - x) < 8 && y > b.y - 20 && y < b.y + 2);
    if (hit) { const [hx, hy] = tileOf(hit); const st = W.standTiles(hx, hy, tileOf(me)).concat([[hx, hy + 1]]).find(([a, b]) => !W.solidTile(a, b)); if (st) walkTo(me, st[0], st[1], () => doAct('chaptay')); return; }
    const spotName = Object.keys(W.SPOTS).find(n => W.SPOTS[n].tx === tx && W.SPOTS[n].ty === ty);
    if (spotName) {
      const s = W.SPOTS[spotName], stand = W.standTiles(s.tx, s.ty, tileOf(me))[0];
      if (stand) walkTo(me, stand[0], stand[1], () => { if (spotName === 'counter') openCounter(); else doAct(s.act); });
      return;
    }
    if (Math.abs(dog.x - x) < 8 && y > dog.y - 14 && y < dog.y + 2) {
      const [dx, dy] = tileOf(dog), st = W.standTiles(dx, dy, tileOf(me)).find(([a, b2]) => !W.solidTile(a, b2));
      if (st) walkTo(me, st[0], st[1], () => doAct('vuotcho'));
      return;
    }
    if ((windowSeatAt(tx, ty) || nookAt(tx, ty)) && !seatTaken([tx, ty], me)) { walkTo(me, tx, ty, () => { if (windowSeatAt(tx, ty)) sitDown(me); else lieDown(me); }); return; }
    const table = W.TABLES.find(t => t.tx === tx && t.ty === ty);
    if (table) { const s = table.seats.find(s2 => !seatTaken(s2, me)); if (s) walkTo(me, s[0], s[1], () => sitDown(me)); return; }
    if (!W.solidTile(tx, ty)) walkTo(me, tx, ty);
  });
  $('actBtn').addEventListener('click', interact);

  // ---------- drawing ----------
  const night = () => nowHour() >= 18 || nowHour() < 6;
  const bg = R.background({ day: !night() });
  function drawCup(c, x, y, kind) {
    const col = Q.DRINKS[kind].color;
    c.fillStyle = '#f3ead8'; c.fillRect(x, y + 2, 7, 7);
    c.fillStyle = col; c.fillRect(x + 1, y + 3, 5, 2);
    c.fillStyle = '#f3ead8'; c.fillRect(x + 7, y + 4, 2, 3);
    c.fillStyle = 'rgba(232,228,220,.7)'; c.fillRect(x + 2, y, 1, 2); c.fillRect(x + 4, y - 1, 1, 2);
  }
  function cupSpot(b) {
    const here = seatAt(...tileOf(b));
    if (!here) return null;
    const left = b.x < here.table.tx * T + 8;
    return { table: here.table, left, x: here.table.tx * T + (left ? 2 : 10), y: here.table.ty * T + 3 };
  }
  function drawCupsOnTables() {
    for (const b of people.values()) {
      if (!b.sit) continue;
      const c = cupSpot(b);
      if (!c) continue;
      if (b.task) R.tableThing(ctx, c.table, c.left, b.gear.thing, clock + (b.blinkAt || 0), still());
      if (!b.drink) continue;
      ctx.fillStyle = '#f3ead8'; ctx.fillRect(c.x, c.y, 4, 4); ctx.fillRect(c.left ? c.x + 4 : c.x - 1, c.y + 1, 1, 2);
      ctx.fillStyle = Q.DRINKS[b.drink].color; ctx.fillRect(c.x + 1, c.y + 1, 2, 1);
    }
  }
  function steam(dt) {
    if (motion !== 'full') return;
    for (const b of people.values()) {
      if (!b.sit || !b.drink) continue;
      b.steamT -= dt; if (b.steamT > 0) continue;
      b.steamT = 1.2 + rand() * 1.5;
      const c = cupSpot(b);
      if (c) particles.push({ kind: 'steam', x: c.x + 1 + rand() * 2, y: c.y - 1, vx: rand() * 2 - 1, vy: -5, life: 1.3 });
    }
  }
  function render() {
    ctx.drawImage(bg, 0, 0);
    R.rain(ctx, clock, still());
    R.cat(ctx, clock, still(), [...people.values()].some(b => b.act === 'vuotmeo'));
    R.lamps(ctx, night() ? 0.075 : 0.035);
    R.person(ctx, host, clock, still(), 0);
    R.counterFront(ctx);
    drawCupsOnTables();
    R.dogBed(ctx);
    for (const b of [...people.values(), dog].sort((a, c) => a.y - c.y)) { if (b.isDog) R.dog(ctx, dog, clock, still()); else R.person(ctx, b, clock, still(), 0); }
    R.pendants(ctx);
    R.drawParticles(ctx, particles);
    // the small hours are dim
    if (nowHour() < 5) { ctx.fillStyle = 'rgba(10,8,20,.28)'; ctx.fillRect(0, 0, VW, VH); }
    R.glow(ctx, night());
    R.vignette(ctx, night() ? 0.4 : 0.22);
    drawOverlay();
  }

  const tags = new Map();
  function drawOverlay() {
    const all = [host, dog, ...people.values()];
    const live = new Set(all.map(b => b.id));
    for (const [id, t] of tags) if (!live.has(id)) { t.root.remove(); tags.delete(id); }
    for (const b of all) {
      let t = tags.get(b.id);
      if (!t) {
        t = { root: el('div', 'who'), bubble: el('div', 'bubble'), tag: el('div', 'tag' + (b.id === 'you' ? ' you' : b.host ? ' host' : '')), nm: el('span', 'nm'), doing: el('span'), last: '' };
        t.bubble.hidden = true; t.tag.append(t.nm, t.doing); t.root.append(t.bubble, t.tag); overlay.append(t.root); tags.set(b.id, t);
      }
      const name = b.host ? '☕ Cô Lá' : b.isDog ? Q.DOG.icon + ' ' + Q.DOG.name : b.name + (b.id === 'you' ? ' (bạn)' : '');
      const doing = b.isDog ? '' : b.act ? ' ' + ACTS[b.act].icon : b.lie ? ' 📖' : b.sit && b.task && b.gear ? ' ' + Q.THINGS[b.gear.thing].icon : b.seatKind === 'window' ? ' 🪟' : b.sit ? ' 🪑' : '';
      if (t.nm.textContent !== name) t.nm.textContent = name;
      if (t.doing.textContent !== doing) t.doing.textContent = doing;
      const bub = b.bubble && b.bubble.until > clock ? b.bubble.text : '';
      if (bub !== t.last) { t.last = bub; t.bubble.textContent = bub; t.bubble.hidden = !bub; t.bubble.className = 'bubble' + (bub ? ' pop' : ''); }
      const top = b.isDog ? b.y - 15 : b.lie ? b.y - 13 : b.y - 19 + (b.sit ? 3 : 0);
      const above = top * scale, below = above - t.root.offsetHeight < 0;
      t.root.classList.toggle('below', below);
      const half = t.root.offsetWidth / 2, room = VW * scale;
      t.root.style.left = Math.min(room - half - 2, Math.max(half + 2, b.x * scale)) + 'px';
      t.root.style.top = (below ? (b.y + 1) * scale : above) + 'px';
      t.root.style.zIndex = String(Math.round(b.y) + (bub ? 200 : 0));
    }
  }

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
    ctx.setTransform(k, 0, 0, k, 0, 0); ctx.imageSmoothingEnabled = false;
    overlay.classList.toggle('compact', scale < 1.9);
    Object.assign(overlay.style, { left: Math.round((w - cw) / 2) + 'px', top: Math.round((h - ch) / 2) + 'px', width: cw + 'px', height: ch + 'px' });
  }
  window.addEventListener('resize', fit);

  // ---------- loop ----------
  let last = 0, held = false, lastNear = '', panelTimer = 0, greetTimer = 0;
  function tick(dt) {
    if (!modalOpen) clock += dt;
    if (me.path) followPath(me, dt);
    else if (!modalOpen && keys.size) {
      const ix = (keys.has('right') ? 1 : 0) - (keys.has('left') ? 1 : 0), iy = (keys.has('down') ? 1 : 0) - (keys.has('up') ? 1 : 0);
      if (ix || iy) {
        const len = Math.hypot(ix, iy), sp = 60 * dt;
        const moved = W.moveWithSlide({ x: me.x - 4, y: me.y - 4, w: 8, h: 5 }, ix / len * sp, iy / len * sp);
        me.x = moved.x + 4; me.y = moved.y + 4; me.moving = true; me.act = null; me.sit = false; me.lie = false; me.seatKind = null; me.task = false;
        me.dir = Math.abs(ix) >= Math.abs(iy) && ix ? (ix > 0 ? 'right' : 'left') : (iy > 0 ? 'down' : 'up');
      }
    }
    if (!modalOpen) dogThink(dt);
    dog.walkMs = dog.moving ? dog.walkMs + dt * 1000 : 0;
    for (const b of [...people.values()]) {
      if (b.npc) { if (b.path) followPath(b, dt); else if (!modalOpen) guestThink(b, dt); }
      if (b.act && b.actUntil <= clock) b.act = null;
      if (b.bubble && b.bubble.until <= clock) b.bubble = null;
      if (b.moving) b.walkMs += dt * 1000; else b.walkMs = 0;
    }
    if (!modalOpen) {
      keepCrowd(dt);
      greetTimer -= dt; if (greetTimer <= 0) { greetTimer = 0.5; greetings(); }
    }
    R.actParticles(people.values(), particles, dt, still());
    if (!modalOpen) steam(dt);
    R.stepParticles(particles, dt);
    renderActs();
    panelTimer -= dt; if (panelTimer <= 0) { panelTimer = 2; renderPanel(); }
    const n = modalOpen ? null : nearestThing();
    const key = n ? n.kind + n.label : '';
    if (key !== lastNear) {
      lastNear = key;
      const b = $('actBtn');
      if (n) {
        b.disabled = false;
        b.textContent = (n.kind === 'person' ? 'Chắp tay chào ' + n.label : n.kind === 'seat' ? 'Ngồi xuống' : n.kind === 'window' ? 'Ngồi cạnh cửa sổ' : n.kind === 'nook' ? 'Nằm đọc sách' : n.kind === 'dog' ? 'Chơi với ' + n.label + ' 🐶' : n.name === 'counter' ? 'Gọi Cô Lá · ' + n.label : ACTS[W.SPOTS[n.name].act].label + ' · ' + n.label) + ' (E)';
        $('near').textContent = 'Gần ' + n.label + '.';
      } else { b.disabled = true; b.textContent = 'Lại gần quầy, cửa sổ, góc sách, mèo hay chó Bơ'; $('near').textContent = ''; }
    }
    render();
    for (const b of people.values()) b.moving = false;
    dog.moving = false;
  }
  function frame(now) {
    try { if (!held) { const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now; tick(dt); } }
    finally { schedule(); }
  }
  function schedule() { if (document.hidden) setTimeout(() => frame(performance.now()), 50); else requestAnimationFrame(frame); }

  const MOTION_LABEL = { full: 'Cử động: đầy đủ', reduced: 'Cử động: giảm', off: 'Cử động: tắt' };
  function applyMotion() {
    document.body.classList.toggle('reduced', motion === 'reduced');
    document.body.classList.toggle('still', motion === 'off');
    $('motionBtn').textContent = MOTION_LABEL[motion];
    if (motion !== 'full') particles.length = 0;
  }
  $('motionBtn').addEventListener('click', () => { motion = { full: 'reduced', reduced: 'off', off: 'full' }[motion]; applyMotion(); toast(MOTION_LABEL[motion]); });

  applyMotion();
  fit();
  enter();
  schedule();
  window.__quan = {
    hold: v => { held = v; }, step: ms => { for (let t = 0; t < ms; t += 16) tick(0.016); },
    people, me: () => me, walkTo: (tx, ty) => walkTo(me, tx, ty), act: doAct, greet, interact, openCounter, openLeave, closeModal,
    dog: () => ({ x: dog.x, y: dog.y, sitting: dog.sitting, petted: dog.petted > clock, tile: tileOf(dog) }), callDog: () => { dog.idle = 0; },
    notes: () => myNotes.slice(), drink: () => myDrink, card: () => myCard, spawn: () => spawnGuest(false), modalOpen: () => modalOpen
  };
})();
