// Thử thách đôi · L1–L2 Sĩ số +1. You and a fictional teammate share one table; each holds half of the facts
// and half of the answer. Rules live in duo.js; the café look comes from room.js.
(function () {
  'use strict';
  const D = window.Duo, W = window.World, E = window.Engine, R = window.Room, Q = window.Quan, H = window.Hen;
  const $ = id => document.getElementById(id);
  const T = W.TILE, VW = W.W * T, VH = W.H * T;
  const rand = Math.random;
  const canvas = $('game'), ctx = canvas.getContext('2d'), overlay = $('overlay');
  let scale = 1, clock = 0;
  let motion = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'reduced' : 'full';
  const still = () => motion === 'off';

  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function btn(text, cls, fn) { const b = el('button', cls, text); b.type = 'button'; b.addEventListener('click', fn); return b; }
  // Timers belong to one play-through: "Chơi lại" drops anything still pending.
  let gen = 0;
  function later(ms, fn) { const g = gen; setTimeout(() => { if (g === gen) fn(); }, still() ? Math.min(ms, 300) : ms); }
  // Round-scoped timers: a teammate's reply, lock or result for a round that already ended never runs.
  let roundGen = 0;
  function laterRound(ms, fn) { const r = roundGen; later(ms, () => { if (r === roundGen) fn(); }); }

  // ---------- the team ----------
  const TABLE = W.TABLES[1];
  function seatBody(id, name, look, seat, dir, gear) {
    return { id, name, x: seat[0] * T + 8, y: seat[1] * T + 12, dir, sit: true, task: false, sheet: E.buildSheet(look), blinkAt: rand() * 4, walkMs: 0, gear, bubble: null };
  }
  const me = seatBody('you', 'Bạn', H.LOOKS[0], TABLE.seats[0], 'right', Object.assign(Q.packBag(rand), { thing: 'sove' }));
  let mateName = Q.randomName(rand);
  const mate = seatBody('mate', mateName, H.GUESTS[2].look, TABLE.seats[1], 'left', Object.assign(Q.packBag(rand), { thing: 'sach' }));
  const SWITCH = [5, 8]; // stand here to hold the light switch by the back wall
  const host = { id: 'host', host: true, name: 'Cô Lá', x: W.HOST.tx * T + 8, y: W.HOST.ty * T + 7, dir: 'down', sheet: E.buildSheet({ H: '#2b2230', T: '#3f6b55', C: '#7fc8a0', P: '#30303a', B: '#1d1b26', longHair: true, hat: true }) };
  const people = [me, mate];
  let short = mateName.split(' ').slice(0, 2).join(' ');
  function say(b, text, secs) { b.bubble = { text: H.sanitizeBubble(text, 60), until: clock + (secs || 3.5) }; }

  // ---------- state ----------
  const S = { mode: 'hai', courage: 'nhe', mateCourage: rand() < 0.5 ? 'nhe' : 'vua', team: 'nhe', lights: false, round: 0, level: 1, stage: 'setup',
    answer: {}, locks: {}, notes: [], lamps: 0, tally: {}, struck: new Set(), dim: 0, holding: false, seenDoor: false };
  const rounds = () => D.LEVELS[S.level];
  const round = () => rounds()[S.round];
  const TOTAL_ROUNDS = D.LEVELS[1].length + D.LEVELS[2].length;

  // ---------- the teammate walks to the light switch and back ----------
  function walkTo(b, tx, ty, then) {
    const path = W.findPath([Math.floor(b.x / T), Math.floor((b.y - 1) / T)], [tx, ty]);
    if (!path) return;
    b.sit = false; b.task = false; b.path = path.slice(1); b.then = then || null;
    if (!b.path.length) { b.path = null; if (then) then(); }
  }
  function followPath(b, dt) {
    const [tx, ty] = b.path[0], gx = tx * T + 8, gy = ty * T + 12;
    const dx = gx - b.x, dy = gy - b.y, d = Math.hypot(dx, dy), step = 42 * dt;
    if (d <= step) { b.x = gx; b.y = gy; b.path.shift(); if (!b.path.length) { b.path = null; const t = b.then; b.then = null; if (t) t(); } }
    else { b.x += dx / d * step; b.y += dy / d * step; }
    if (Math.abs(dx) > Math.abs(dy)) b.dir = dx > 0 ? 'right' : 'left'; else if (dy) b.dir = dy > 0 ? 'down' : 'up';
    b.moving = true;
  }
  function holdSwitch() {
    if (S.holding || !round().needsSwitch) return;
    say(me, 'Giữ công tắc giúp mình nha', 3);
    later(600, () => walkTo(mate, SWITCH[0], SWITCH[1], () => {
      mate.dir = 'down'; S.holding = true; S.seenDoor = true; renderMine(); renderGestures();
      say(mate, 'Mình giữ rồi, bạn đọc bảng cửa sau đi', 4);
    }));
  }
  function releaseSwitch() {
    if (!S.holding) return;
    S.holding = false; renderMine(); renderGestures();
    say(me, 'Xong rồi, cảm ơn nha', 2.5);
    walkTo(mate, TABLE.seats[1][0], TABLE.seats[1][1], () => { mate.sit = true; mate.dir = 'left'; mate.task = true; });
  }

  // ---------- setup ----------
  function openSetup() {
    const body = openModal('TRƯỚC KHI VÀO', 'Hôm nay chơi màu nào?', false);
    body.append(el('p', '', 'Cùng một câu đố, chỉ đổi màu chơi. Bạn ghép đội với ' + mateName + '.'));
    const modes = el('div', 'choices'), courage = el('div', 'choices');
    const paint = () => {
      for (const b of modes.children) b.setAttribute('aria-pressed', b.dataset.k === S.mode ? 'true' : 'false');
      for (const b of courage.children) b.setAttribute('aria-pressed', b.dataset.k === S.courage ? 'true' : 'false');
      courageBox.hidden = S.mode !== 'rung';
    };
    for (const [k, m] of Object.entries(D.MODES)) { const b = btn(m.icon + ' ' + m.label, '', () => { S.mode = k; paint(); }); b.dataset.k = k; modes.append(b); }
    for (const [k, c] of Object.entries(D.COURAGE)) { const b = btn(c.label, '', () => { S.courage = k; paint(); }); b.dataset.k = k; courage.append(b); }
    const courageBox = el('div');
    courageBox.append(el('div', 'field', 'Mức gan của bạn'), courage, el('p', 'note', 'Đội luôn chơi ở mức nhẹ hơn của hai người. Lúc nào cũng có nút "Mình sợ quá" để bật đèn.'));
    body.append(el('div', 'field', 'Màu chơi'), modes, courageBox,
      el('p', 'note', 'Có gì: một sổ khách và vài tấm ảnh. Không máu me, không nhấp nháy, không âm thanh.'),
      btn('Vào bàn', 'primary', () => { closeModal(); start(); }));
    paint();
  }
  function start() {
    S.team = D.teamCourage(S.courage, S.mateCourage); bg = null; S.dim = 0;
    S.stage = 'play'; S.lights = S.mode !== 'rung';
    $('scaredBtn').hidden = S.mode !== 'rung';
    hostSay(D.MODES[S.mode].intro + (S.mode === 'rung' ? ' Đội chơi mức ' + D.COURAGE[S.team].label.toLowerCase() + '.' : ''));
    S.level = 1; startRound(0);
  }

  // ---------- rounds ----------
  function startRound(i) {
    roundGen += 1;
    S.round = i; S.answer = {}; S.conf = D.newConfirm(false); S.locks = S.conf.locks; S.tally = {}; S.struck = new Set(); S.mateRead = false; S.holding = false; S.seenDoor = false;
    for (const f of round().fields) S.tally[f] = D.FIELDS[f].labels.map(() => 0);
    const r = round();
    banner('L' + S.level + ' · Vòng ' + (i + 1) + ' · ' + r.title, 4);
    const intro = r.kind === 'route' ? 'Mình cầm sổ quét thẻ. Bạn cầm sơ đồ quán nha.' : r.ledger === 'mate' ? 'Mình cầm sổ khách. Bạn cầm ảnh nha.' : 'Lần này mình cầm ảnh, bạn cầm sổ.';
    later(900, () => say(mate, intro, 4));
    me.task = true; mate.task = true;
    renderAll();
  }

  // ---------- your half ----------
  function renderMine() {
    const box = $('mine'); box.replaceChildren();
    const r = round();
    if (S.stage !== 'play') return;
    if (r.kind === 'route') { renderMap(box, r); return; }
    if (r.photo === 'you') {
      box.append(el('h2', '', 'Phần của bạn: ảnh tối qua'), el('p', 'note-hint', 'Đếm từng loại trong ảnh, rồi dán note cho ' + short + '. Sổ khách nằm ở phía ' + short + '.'));
      for (const f of r.fields) {
        const c = document.createElement('canvas'); c.className = 'photo'; c.width = 120; c.height = 64;
        c.setAttribute('role', 'img'); c.setAttribute('aria-label', D.FIELDS[f].photo + '. Năm khách, mỗi người một ly.' + ((r.mirrored || []).includes(f) ? ' Ảnh chụp qua gương.' : ''));
        drawPhoto(c, r, f);
        box.append(el('div', 'field', D.FIELDS[f].photo));
        if ((r.mirrored || []).includes(f)) box.append(el('p', 'stamp', '📷 Dấu ở góc ảnh: "chụp qua gương tủ kính"'));
        box.append(c, legend(f));
        const row = el('div', 'tally');
        D.FIELDS[f].labels.forEach((l, k) => {
          const cell = el('div', 'cell');
          const val = el('b', '', String(S.tally[f][k]));
          cell.append(el('span', '', l), btn('−', '', () => { S.tally[f][k] = Math.max(0, S.tally[f][k] - 1); val.textContent = S.tally[f][k]; }), val,
            btn('+', '', () => { S.tally[f][k] = Math.min(9, S.tally[f][k] + 1); val.textContent = S.tally[f][k]; }));
          cell.querySelectorAll('button')[0].setAttribute('aria-label', 'Bớt ' + l); cell.querySelectorAll('button')[1].setAttribute('aria-label', 'Thêm ' + l);
          row.append(cell);
        });
        box.append(row);
      }
      box.append(btn('📝 Dán note số đếm cho ' + short, 'primary', sendCounts));
    } else {
      box.append(el('h2', '', 'Phần của bạn: sổ khách tối qua'), el('p', 'note-hint', short + ' cầm hai tấm ảnh. Bấm "Đọc giúp mình" để nghe. Chạm một dòng để gạch bớt.'));
      const tbl = el('table', 'ledger');
      const head = el('tr'); head.append(el('th', '', 'Tên'), ...r.fields.map(f => el('th', '', D.FIELDS[f].name)));
      tbl.append(head);
      D.NAMES.forEach((n, i) => {
        const tr = el('tr'); tr.tabIndex = 0; tr.setAttribute('role', 'button');
        tr.append(el('td', '', n), ...r.fields.map(f => el('td', '', D.FIELDS[f].labels[r.rows[f][i]])));
        const toggle = () => { if (S.struck.has(i)) S.struck.delete(i); else S.struck.add(i); tr.classList.toggle('struck', S.struck.has(i)); tr.setAttribute('aria-pressed', String(S.struck.has(i))); };
        tr.classList.toggle('struck', S.struck.has(i)); tr.setAttribute('aria-pressed', String(S.struck.has(i)));
        tr.addEventListener('click', toggle); tr.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
        tbl.append(tr);
      });
      box.append(tbl);
    }
  }
  // Route round: your half is the café floor plan. The back-door sign is only readable while the light is held.
  function renderMap(box, r) {
    box.append(el('h2', '', 'Phần của bạn: sơ đồ quán'), el('p', 'note-hint', short + ' cầm sổ quét thẻ. Bấm "Đọc giúp mình" để nghe từng dòng. Có thể chờ, không thể nhanh hơn đường ngắn nhất.'));
    const c = document.createElement('canvas'); c.className = 'map'; c.width = 480; c.height = 240;
    c.setAttribute('role', 'img'); c.setAttribute('aria-label', 'Sơ đồ quán: Kho, Quầy, Cửa trước, Sân sau và thời gian đi giữa chúng.');
    drawMap(c.getContext('2d'));
    box.append(c);
    const ul = el('ul', 'paths');
    for (const [a, b, w, one] of D.PATHS) {
      const door = one ? (S.holding ? ' · cửa sau chỉ mở từ ' + D.PLACES[a] + ' vào ' + D.PLACES[b] : ' · bảng cửa sau tối quá, chưa đọc được') : '';
      ul.append(el('li', one ? 'door' : '', D.PLACES[a] + ' – ' + D.PLACES[b] + ': ' + w + ' phút' + door));
    }
    box.append(ul, el('p', 'note-hint', S.holding ? 'Đèn đang sáng nhờ ' + short + ' giữ công tắc.' : 'Muốn đọc bảng cửa sau thì nhờ ' + short + ' ra giữ công tắc đèn (cử chỉ "Giữ công tắc").'));
  }
  function drawMap(g) {
    const pos = [[80, 60], [240, 60], [400, 170], [80, 170]];
    g.fillStyle = '#2a2236'; g.fillRect(0, 0, 480, 240);
    g.lineWidth = 4; g.font = '600 15px system-ui, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    for (const [a, b, w, one] of D.PATHS) {
      const [x1, y1] = pos[a], [x2, y2] = pos[b];
      g.strokeStyle = one ? (S.holding ? '#f2b45a' : '#4a3f5a') : '#8a7a9a';
      g.setLineDash(one && !S.holding ? [6, 6] : []); g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke(); g.setLineDash([]);
      const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
      g.fillStyle = '#17131f'; g.fillRect(mx - 22, my - 12, 44, 24);
      g.fillStyle = one && !S.holding ? '#8a7a9a' : '#f3ead8'; g.fillText(w + "'" + (one && !S.holding ? ' ?' : ''), mx, my);
      if (one && S.holding) { const ang = Math.atan2(y2 - y1, x2 - x1); g.fillStyle = '#f2b45a'; g.beginPath(); g.moveTo(x2 - Math.cos(ang) * 20, y2 - Math.sin(ang) * 20); g.lineTo(x2 - Math.cos(ang) * 34 - Math.sin(ang) * 9, y2 - Math.sin(ang) * 34 + Math.cos(ang) * 9); g.lineTo(x2 - Math.cos(ang) * 34 + Math.sin(ang) * 9, y2 - Math.sin(ang) * 34 - Math.cos(ang) * 9); g.fill(); }
    }
    D.PLACES.forEach((n, i) => { const [x, y] = pos[i]; g.fillStyle = '#3f6b55'; g.fillRect(x - 46, y - 18, 92, 36); g.fillStyle = '#f3ead8'; g.fillText(n, x, y); });
  }
  function legend(f) {
    const row = el('div', 'legend');
    D.FIELDS[f].labels.forEach((l, k) => {
      const c = document.createElement('canvas'); c.width = 10; c.height = 12; c.setAttribute('aria-hidden', 'true');
      drawItem(c.getContext('2d'), f, k, 1, 1);
      const s = el('span'); s.append(c, document.createTextNode(l)); row.append(s);
    });
    return row;
  }
  function drawItem(g, f, k, x, y) {
    const col = D.FIELDS[f].colors[k];
    if (f === 'cup') {
      if (k === 0) { g.fillStyle = '#c0c0c8'; g.fillRect(x + 1, y, 6, 3); g.fillStyle = '#f3ead8'; g.fillRect(x + 1, y + 3, 6, 6); g.fillStyle = col; g.fillRect(x + 2, y + 4, 4, 4); }
      if (k === 1) { g.fillStyle = 'rgba(220,235,240,.9)'; g.fillRect(x + 1, y + 1, 6, 8); g.fillStyle = col; g.fillRect(x + 2, y + 3, 4, 5); g.fillStyle = '#7fc8a0'; g.fillRect(x + 5, y, 2, 2); }
      if (k === 2) { g.fillStyle = '#ef9a8a'; g.fillRect(x + 1, y + 1, 6, 8); g.fillStyle = col; g.fillRect(x + 2, y + 1, 4, 2); g.fillStyle = '#fbf4e6'; g.fillRect(x + 3, y, 2, 2); }
    } else if (f === 'handle') { g.fillStyle = '#f3ead8'; g.fillRect(x + 2, y + 2, 5, 7); g.fillStyle = '#a0724a'; g.fillRect(x + 3, y + 3, 3, 2); g.fillStyle = '#f3ead8'; if (k === 0) g.fillRect(x, y + 4, 2, 3); else g.fillRect(x + 7, y + 4, 2, 3); }
    else { g.fillStyle = col; g.fillRect(x + 1, y + 1, 6, 3); g.fillRect(x + 3, y + 4, 2, 5); g.fillStyle = '#2a1f3d'; g.fillRect(x + 3, y + 9, 2, 1); g.fillRect(x + 3, y, 2, 1); }
  }
  // The photo shows every line except the extra one, in a shuffled but fixed order. The mood only adds decoration.
  function drawPhoto(c, r, f) {
    const g = c.getContext('2d');
    const night = S.mode === 'rung';
    g.fillStyle = night ? '#1e1a2a' : '#6b4a32'; g.fillRect(0, 0, 120, 64);
    g.fillStyle = night ? '#2a2236' : '#8a6a4a'; g.fillRect(0, 40, 120, 24);
    g.fillStyle = night ? '#3a2e44' : '#a0724a'; g.fillRect(4, 44, 112, 6);
    const items = [];
    const x = D.extraOf(r);
    D.NAMES.forEach((_, i) => { if (i !== x) items.push(r.rows[f][i]); });
    const order = [2, 0, 4, 1, 3];
    const looks = [H.GUESTS[0].look, H.GUESTS[3].look, H.GUESTS[5].look, H.GUESTS[6].look, H.GUESTS[8].look];
    order.forEach((src, pos) => {
      const px = 8 + pos * 22;
      if (f === 'cup') {
        const spr = E.buildSheet(looks[pos])['up:stand:0'];
        g.save(); g.beginPath(); g.rect(px, 22, 16, 22); g.clip(); E.drawSprite(g, spr, px, 26); g.restore();
        drawItem(g, f, items[src], px + 4, 40);
      } else if (f === 'handle') {
        const spr = E.buildSheet(looks[pos])['up:stand:0'];
        g.save(); g.beginPath(); g.rect(px, 22, 16, 22); g.clip(); E.drawSprite(g, spr, px, 26); g.restore();
        // what the camera sees: through the mirror, left and right swap
        const side = (r.mirrored || []).includes(f) ? 1 - items[src] : items[src];
        drawItem(g, f, side, px + 4, 40);
      } else {
        g.fillStyle = '#5a3a26'; g.fillRect(px + 7, 18, 2, 30);
        drawItem(g, f, items[src], px + 4, 30);
      }
    });
    if (S.mode === 'hai' && f === 'cup') { g.fillStyle = '#d9a050'; g.fillRect(52, 34, 10, 6); g.fillRect(60, 31, 4, 4); g.fillStyle = '#2a1f3d'; g.fillRect(61, 32, 1, 1); g.fillStyle = '#d9a050'; g.fillRect(50, 30, 2, 5); }
    if (S.mode === 'rung' && !S.lights) {
      const a = S.team === 'vua' ? 0.22 : 0.12;
      g.fillStyle = 'rgba(200,190,220,' + a + ')'; g.fillRect(98, 6, 10, 10); g.fillRect(96, 16, 14, 22);
      g.fillStyle = 'rgba(8,6,16,' + (S.team === 'vua' ? 0.35 : 0.2) + ')'; g.fillRect(0, 0, 120, 64);
    }
  }
  function sendCounts() {
    const r = round();
    const note = D.noteFromCounts(r, S.tally);
    addNote('you', 'Ảnh: ' + note);
    say(me, 'Mình dán note số ly rồi nha', 3);
    laterRound(1400, () => {
      const name = D.mateNameFromCounts(r, S.tally);
      const was = S.answer.name;
      if (name) { S.answer.name = name; say(mate, 'Theo note thì sổ thừa đúng một dòng. Mình điền rồi!', 4); }
      else { delete S.answer.name; say(mate, 'Theo note thì sổ chưa khớp dòng nào. Đếm lại giúp mình?', 5); }
      // Filling an empty blank keeps your lock; changing a name you may have locked on asks both to confirm again.
      if (was && was !== S.answer.name) step('answerChanged');
      mateUpdated();
    });
  }

  // ---------- gestures ----------
  function gesture(id) {
    const r = round();
    if (id === 'doc') {
      say(me, 'Đọc giúp mình với', 2.5);
      const lines = r.kind === 'route' ? D.logLines(r) : r.ledger === 'mate' ? D.ledgerLines(r) : D.photoLines(r);
      if (S.mateRead) { later(800, () => say(mate, 'Mình đọc rồi đó, xem note trên bàn nha', 3.5)); return; }
      S.mateRead = true;
      lines.forEach((l, i) => later(900 + i * 1500, () => { say(mate, l, 1.6); addNote('mate', l); }));
      return;
    }
    if (id === 'giu') { holdSwitch(); return; }
    if (id === 'tha') { releaseSwitch(); return; }
    if (id === 'doi') { say(me, 'Đợi mình chút ✋', 3); later(700, () => say(mate, 'Cứ từ từ, không vội 🙂', 3)); return; }
    if (id === 'dap') { say(me, '🙌', 2); later(500, () => say(mate, '🙌', 2)); return; }
    if (id === 'dem') {
      const n = [3, 2, 1];
      n.forEach((k, i) => later(i * 700, () => { say(me, String(k), 0.7); say(mate, String(k), 0.7); }));
      laterRound(2100, () => { lock('you'); });
    }
  }

  // ---------- answer ----------
  function renderAnswer() {
    const box = $('answer'); box.replaceChildren();
    if (S.stage !== 'play') return;
    const r = round();
    box.append(el('h2', '', 'Câu trả lời của đội'));
    const sentence = el('p', 'sentence');
    for (const b of D.blanks(r)) {
      const v = S.answer[b.key];
      sentence.append(document.createTextNode(b.label + ' '), el('span', 'blank' + (v ? ' filled' : '') + (b.owner === 'you' ? ' yours' : ''), v ? v + (b.unit ? ' ' + b.unit : '') : (b.owner === 'you' ? '…bạn điền' : '…' + short + ' điền')), document.createTextNode(' '));
    }
    box.append(sentence);
    for (const b of D.blanks(r).filter(x => x.owner === 'you')) {
      const row = el('div', 'choices'); row.setAttribute('role', 'group'); row.setAttribute('aria-label', b.label);
      for (const o of b.options) {
        const c = btn(o + (b.unit ? ' ' + b.unit : ''), '', () => pickBlank(b.key, o));
        c.setAttribute('aria-pressed', S.answer[b.key] === o ? 'true' : 'false');
        row.append(c);
      }
      box.append(el('div', 'field', 'Mảnh chữ của bạn · ' + (b.title || b.label)), row);
    }
    const st = el('p', 'note-hint', S.locks.you && !S.locks.mate ? 'Bạn đã chốt, đang đợi ' + short + '.' : S.locks.mate && !S.locks.you ? short + ' đã chốt, đang đợi bạn.' : 'Cả hai cùng bấm Chốt thì mới nộp.');
    box.append(st, btn(S.locks.you ? '✓ Đã chốt' : 'Chốt', 'primary lockbtn', () => lock('you')));
  }
  function pickBlank(key, value) {
    if (S.stage !== 'play') return;
    S.answer[key] = value; step('answerChanged');
    if (key === 'name') onNamePicked(value);
  }
  function onNamePicked(name) {
    const r = round();
    if (r.kind === 'route') {
      delete S.answer.logged; mateUpdated();
      laterRound(1300, () => { S.answer.logged = D.mateLogged(r, name); say(mate, 'Sổ ghi ' + name + ' đi mất ' + S.answer.logged + ' phút. Mình điền rồi!', 4); mateUpdated(); });
    } else if (r.ledger === 'you') mateFillsReason(name);
  }
  function mateFillsReason(name) {
    const r = round();
    for (const f of r.fields) delete S.answer[f];
    mateUpdated();
    laterRound(1300, () => {
      const out = D.mateReasonFor(r, name);
      for (const f of r.fields) S.answer[f] = out[f];
      say(mate, out.fits ? 'Dòng đó khớp cả hai ảnh. Mình điền phần ảnh rồi!' : 'Phần ảnh xong, mà dòng đó chưa khớp cả hai ảnh', 4.5);
      mateUpdated();
    });
  }
  // Confirmation goes through Duo.confirmStep: the teammate locks as soon as you have locked and
  // their half is filled, whichever comes first, and a round is judged once.
  const mateReady = () => D.blanks(round()).filter(b => b.owner === 'mate').every(b => S.answer[b.key]);
  function step(ev) {
    if (S.stage !== 'play') return;
    const hadMate = !!S.locks.mate;
    const out = D.confirmStep(S.conf, ev);
    S.conf = out.state; S.locks = S.conf.locks;
    if (!hadMate && S.locks.mate) say(mate, 'Chốt!', 2);
    renderAnswer();
    if (out.judge) judgeNow();
  }
  function mateUpdated() { step(mateReady() ? 'mateReady' : 'mateNotReady'); }
  function lock(who) {
    if (S.stage !== 'play' || who !== 'you') return;
    if (S.holding) { say(mate, 'Mình còn giữ công tắc. Xong thì bảo mình về nha', 4); return; }
    if (S.locks.you) return; // already locked: a second click is not a second submission
    step('youLock');
    if (S.stage === 'play' && !S.locks.mate) say(mate, 'Đợi mình điền xong, mình chốt luôn nha', 3.5);
  }
  function judgeNow() {
    const res = D.judge(round(), S.answer, S.locks);
    if (res.status === 'solved') { step('solved'); solved(res); }
    else { step('retry'); banner(res.text, 4); }
  }
  function solved(res) {
    // Settle the round once: bump the round token so any pending lock or reply for it is dropped.
    S.lamps += 1; S.stage = 'reveal'; me.task = false; mate.task = false;
    const token = ++roundGen;
    say(me, '🙌', 2); say(mate, '🙌', 2);
    renderAll();
    later(900, () => {
      if (token !== roundGen || S.stage !== 'reveal') return;
      const lastOfLevel = S.round === rounds().length - 1;
      const body = openModal('L' + S.level + ' · VÒNG ' + (S.round + 1) + ' XONG', 'Cả đội cùng về đích', false);
      body.append(el('p', '', res.text));
      if (lastOfLevel) body.append(el('div', 'letter', (D.MODES[S.mode].icon) + ' ' + (S.level === 1 ? D.MODES[S.mode].reveal : D.MODES[S.mode].reveal2)));
      body.append(btn(!lastOfLevel ? 'Sang vòng ' + (S.round + 2) + ' · đổi vai' : 'Ra góc nghỉ', 'primary', () => {
        closeModal();
        if (token !== roundGen || S.stage !== 'reveal') return;
        if (!lastOfLevel) { S.stage = 'play'; startRound(S.round + 1); } else breakCorner();
      }));
    });
  }

  // ---------- break corner ----------
  function breakCorner() {
    S.stage = 'break'; renderAll();
    if (S.mode === 'rung') { S.lights = true; hostSay('Đèn quán bật lại. Ngồi nghỉ chút nha.'); }
    const body = openModal('GÓC NGHỈ', 'Ngồi nghỉ, không tính giờ', false);
    body.append(el('p', '', 'Bạn có thể hỏi ' + short + ' một câu. Không hỏi cũng được.'));
    const qs = el('div', 'choices');
    for (const q of (S.level === 1 ? D.QUESTIONS : D.QUESTIONS_L2)) qs.append(btn(q, '', () => { say(me, q, 4); later(1500, () => say(mate, D.MATE_ANSWERS[q], 5)); mateAsks(q); }));
    qs.append(btn('Thôi, ngồi yên thôi', '', () => mateAsks(null)));
    body.append(qs);
  }
  function mateAsks(q) {
    const body = openModal('GÓC NGHỈ', short + ' hỏi lại bạn', false);
    const ask = S.level === 1 ? D.MATE_ASKS : D.MATE_ASKS_L2;
    if (q) body.append(el('div', 'letter', 'Bạn hỏi: ' + q + ' ' + short + ' kể: “' + D.MATE_ANSWERS[q] + '”'));
    later(q ? 2600 : 400, () => say(mate, ask, 5));
    body.append(el('p', '', short + ' hỏi: “' + ask + '” Trả lời hay bỏ qua đều được.'));
    const as = el('div', 'choices');
    for (const a of (S.level === 1 ? D.YOUR_ANSWERS : D.YOUR_ANSWERS_L2)) as.append(btn(a, '', () => { say(me, a, 4); goOn(); }));
    as.append(btn('Bỏ qua', 'ghost', () => goOn()));
    body.append(as);
  }
  function goOn() {
    const body = openModal('GÓC NGHỈ', 'Đi tiếp cùng nhau?', false);
    body.append(el('p', '', 'Chọn kín. ' + short + ' không biết bạn chọn gì, bạn cũng không biết ' + short + ' chọn gì. Chỉ khi cả hai cùng muốn thì mới đi tiếp chung đội.'));
    const pick = you => {
      const res = D.together(you, rand() < 0.75);
      const aboutLamps = el('div', 'letter', '🏮 Đèn trên mái quán: ' + S.lamps + ' ngọn do đội bạn thắp. Các đội khác cũng góp đèn, không ai đua với ai.');
      if (S.level === 1) {
        const end = openModal('HẾT L1', res.status === 'tiep' ? 'Đi tiếp cùng nhau' : 'Lượt xoay mới', false);
        end.append(el('p', '', res.text), aboutLamps,
          btn(res.status === 'tiep' ? 'Sang L2 cùng ' + short : 'Sang L2 với đồng đội mới', 'primary', () => {
            closeModal();
            if (res.status !== 'tiep') newMate();
            S.level = 2; S.stage = 'play'; S.lights = S.mode !== 'rung'; $('scaredBtn').hidden = S.mode !== 'rung'; S.dim = 0;
            hostSay(S.mode === 'rung' ? 'L2: quán tắt bớt đèn. Ai cần thì cứ bấm "Mình sợ quá".' : 'L2: khó hơn chút. Cứ từ từ nha.');
            startRound(0);
          }));
      } else {
        const end = openModal('HẾT L2', res.status === 'tiep' ? 'Đi tiếp cùng nhau' : 'Lượt xoay mới', false);
        end.append(el('p', '', res.text), el('p', 'note', 'Bản thử dừng ở L2. L3 (vụ cà phê) làm sau, khi hình chứng cứ đã duyệt.'), aboutLamps,
          btn('Chơi lại', 'primary', () => { closeModal(); restart(); }), document.createTextNode(' '),
          (() => { const a = el('a', 'chip', 'Về quán'); a.href = 'quan.html'; return a; })());
      }
      S.stage = 'end'; renderAll();
    };
    body.append(btn('Đi tiếp cùng nhau', 'primary', () => pick(true)), document.createTextNode(' '), btn('Lần này đổi đội', 'ghost', () => pick(false)));
  }

  // A new teammate after "lượt xoay mới": new name, look and courage level.
  function newMate() {
    mateName = Q.randomName(rand); short = mateName.split(' ').slice(0, 2).join(' ');
    mate.name = mateName; mate.sheet = E.buildSheet(H.GUESTS[Math.floor(rand() * H.GUESTS.length)].look); mate.gear = Object.assign(Q.packBag(rand), { thing: 'len' });
    S.mateCourage = rand() < 0.5 ? 'nhe' : 'vua'; S.team = D.teamCourage(S.courage, S.mateCourage);
    S.notes = [];
    hostSay('Bạn ghép đội mới với ' + mateName + '.' + (S.mode === 'rung' ? ' Đội chơi mức ' + D.COURAGE[S.team].label.toLowerCase() + '.' : ''));
  }
  function restart() {
    gen += 1;
    S.lamps = 0; S.notes = []; S.level = 1; S.round = 0; S.stage = 'setup'; S.holding = false;
    Object.assign(mate, { x: TABLE.seats[1][0] * T + 8, y: TABLE.seats[1][1] * T + 12, path: null, sit: true, dir: 'left' });
    openSetup(); renderAll();
  }

  // ---------- notes, lamps, round card ----------
  function addNote(who, text) {
    S.notes.push({ who, text: Array.from(String(text)).slice(0, D.NOTE_MAX + 20).join('') });
    renderNotes();
  }
  function renderNotes() {
    const ul = $('notes'); ul.replaceChildren();
    if (!S.notes.length) { ul.append(el('li', 'empty', 'Chưa có note nào.')); return; }
    for (const n of S.notes.slice(-10)) { const li = el('li', n.who === 'you' ? 'me' : ''); li.append(el('b', '', n.who === 'you' ? 'Bạn' : short), el('span', '', n.text)); ul.append(li); }
  }
  $('noteForm').addEventListener('submit', e => {
    e.preventDefault();
    const t = Q.sanitizeNote($('noteInput').value);
    if (!t) return;
    addNote('you', t); $('noteInput').value = '';
    later(900, () => say(mate, '👍', 2));
  });
  function renderLamps() {
    const box = $('lamps'); box.replaceChildren();
    box.append(el('h2', '', 'Đèn trên mái quán'));
    const row = el('div', 'lamprow');
    const others = 3;
    for (let i = 0; i < others + TOTAL_ROUNDS + 1; i++) {
      const lit = i < others || i - others < S.lamps;
      const s = el('span', 'lamp' + (lit ? ' lit' : '') + (i >= others && i - others < S.lamps ? ' ours' : ''), '🏮');
      s.setAttribute('aria-hidden', 'true'); row.append(s);
    }
    box.append(row, el('p', 'note-hint', 'Mỗi đội về đích thắp một ngọn. Đủ đèn thì cả quán cùng xem tái hiện. Không có bảng xếp hạng.'));
  }
  function renderRound() {
    const box = $('roundCard'); box.replaceChildren();
    const m = D.MODES[S.mode];
    if (S.stage === 'setup') { box.append(el('small', '', 'L1 · SĨ SỐ +1'), el('h2', '', 'Chuẩn bị'), el('p', '', 'Chọn màu chơi để vào bàn.')); return; }
    if (S.stage === 'break' || S.stage === 'end') { box.append(el('small', '', 'L' + S.level + ' · GÓC NGHỈ'), el('h2', '', 'Nghỉ chút'), el('p', '', 'Không tính giờ.')); return; }
    const r = round();
    box.append(el('small', '', 'L' + S.level + ' · VÒNG ' + (S.round + 1) + '/' + rounds().length + ' · ' + m.icon + ' ' + m.label.toUpperCase()), el('h2', '', r.title),
      el('p', '', r.kind === 'route' ? 'Bạn cầm sơ đồ quán, ' + short + ' cầm sổ quét thẻ.' : r.photo === 'you' ? 'Bạn cầm ảnh, ' + short + ' cầm sổ khách.' : 'Bạn cầm sổ khách, ' + short + ' cầm ảnh.'),
      el('p', '', r.kind === 'route' ? 'Sổ quét thẻ có 6 hành trình; một dòng không thể đi kịp. Tìm dòng thừa.' : 'Sổ khách tối qua có 6 dòng, nhưng chỉ 5 người thật sự ghé. Tìm dòng thừa.') );
    if (r.method) box.append(el('p', 'method', '🃏 Lá gợi cách kiểm: ' + r.method));
    box.append(el('p', '', 'Sổ là hồ sơ hư cấu, không phải ai trong buổi.'));
  }
  function renderTrack() {
    const box = $('track'); box.replaceChildren();
    const steps = [['L0', 'Nửa lá tarot', 'done'], ['L1·1', 'Bạn cầm ảnh'], ['L1·2', 'Đổi vai'], ['NGHỈ', 'Góc nghỉ'], ['L2·1', 'Qua gương'], ['L2·2', 'Cửa một chiều'], ['NGHỈ', 'Góc nghỉ']];
    const brk = S.stage === 'break' || S.stage === 'end';
    const now = S.stage === 'setup' ? -1 : S.level === 1 ? (brk ? 3 : S.round + 1) : (brk ? 6 : S.round + 4);
    steps.forEach(([k, l, d], i) => { const c = el('div', i === now ? 'now' : (d || i < now) ? 'done' : ''); c.append(el('b', '', k), document.createTextNode(l)); box.append(c); });
  }
  function renderGestures() {
    const box = $('gestures'); box.replaceChildren();
    const list = D.GESTURES.slice();
    if (S.stage === 'play' && round().needsSwitch) list.push(S.holding ? { id: 'tha', label: 'Xong, về bàn đi', icon: '🔆' } : { id: 'giu', label: 'Giữ công tắc giúp mình', icon: '💡' });
    for (const g of list) { const b = btn(g.icon + ' ' + g.label, g.id === 'giu' || g.id === 'tha' ? 'spot' : '', () => gesture(g.id)); b.disabled = S.stage !== 'play'; box.append(b); }
  }
  function renderAll() { renderTrack(); renderRound(); renderMine(); renderAnswer(); renderNotes(); renderLamps(); renderGestures(); }

  $('scaredBtn').addEventListener('click', () => {
    S.lights = true; $('scaredBtn').hidden = true;
    hostSay('Đèn quán bật sáng rồi. Ai bấm cũng được, không cần giải thích.');
    renderMine();
  });

  // ---------- modal, toast, banner ----------
  let modalOpen = false, modalClosable = true;
  function openModal(kicker, title, closable) {
    $('mKicker').textContent = kicker; $('mTitle').textContent = title;
    const body = $('mBody'); body.replaceChildren();
    modalClosable = closable !== false; $('mClose').hidden = !modalClosable;
    $('shade').hidden = false; modalOpen = true;
    setTimeout(() => { const f = $('modal').querySelector('button:not([hidden]), input'); if (f) f.focus(); }, 0);
    return body;
  }
  function closeModal() { $('shade').hidden = true; modalOpen = false; }
  $('mClose').addEventListener('click', () => { if (modalClosable) closeModal(); });
  $('modal').addEventListener('keydown', e => {
    if (e.key === 'Escape' && modalClosable) { e.preventDefault(); closeModal(); }
    if (e.key === 'Tab') {
      const f = [...$('modal').querySelectorAll('button:not([hidden]):not(:disabled), input, a')];
      if (!f.length) return;
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    }
  });
  let toastTimer = null, bannerTimer = null;
  function toast(msg) { const t = $('toast'); t.textContent = msg; t.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, 3200); }
  function banner(msg, secs) { const b = $('banner'); b.textContent = msg; b.hidden = false; clearTimeout(bannerTimer); bannerTimer = setTimeout(() => { b.hidden = true; }, (secs || 4) * 1000); }
  function hostSay(text) { banner('☕ Cô Lá: ' + text, 6); }

  // ---------- drawing ----------
  let bg = null;
  function render() {
    if (!bg) bg = R.background({ day: S.mode === 'hai' });
    ctx.drawImage(bg, 0, 0);
    R.rain(ctx, clock, still());
    R.cat(ctx, clock, still(), false);
    R.lamps(ctx, S.mode === 'hai' ? 0.04 : 0.08);
    R.person(ctx, host, clock, still(), 0);
    R.counterFront(ctx);
    for (const b of people) if (b.task) R.tableThing(ctx, TABLE, b === me, b.gear.thing, clock + b.blinkAt, still());
    if (S.stage === 'play' && round().needsSwitch) { const sx = SWITCH[0] * T + 6, sy = 9 * T + 2; ctx.fillStyle = '#f3ead8'; ctx.fillRect(sx, sy, 4, 6); ctx.fillStyle = S.holding ? '#f2b45a' : '#5a3a26'; ctx.fillRect(sx + 1, sy + (S.holding ? 1 : 3), 2, 2); if (S.holding) { ctx.fillStyle = 'rgba(255,214,140,.18)'; ctx.fillRect(0, 0, VW, VH); } }
    for (const b of people.slice().sort((a, c) => a.y - c.y)) R.person(ctx, b, clock, still(), 0);
    R.pendants(ctx);
    if (S.mode === 'rung' && !S.lights) {
      // Night, one torch on the table. The room dims slowly to a cap; it never flickers.
      const cap = S.team === 'vua' ? 0.82 : 0.64;
      S.dim = Math.min(cap, S.dim + (still() ? cap : 0.004));
      const cx = TABLE.tx * T + 8, cy = TABLE.ty * T + 4;
      const gr = ctx.createRadialGradient(cx, cy, 10, cx, cy, 54);
      gr.addColorStop(0, 'rgba(8,6,16,0)'); gr.addColorStop(1, 'rgba(8,6,16,' + S.dim + ')');
      ctx.fillStyle = gr; ctx.fillRect(0, 0, VW, VH);
    } else S.dim = Math.max(0, S.dim - 0.02);
    R.glow(ctx, S.mode === 'rung');
    R.vignette(ctx, S.mode === 'rung' ? 0.4 : 0.2);
    drawOverlay();
  }
  const tags = new Map();
  function drawOverlay() {
    for (const b of [host, ...people]) {
      let t = tags.get(b.id);
      if (!t) {
        t = { root: el('div', 'who'), bubble: el('div', 'bubble'), tag: el('div', 'tag' + (b.id === 'you' ? ' you' : b.host ? ' host' : '')), last: '' };
        t.bubble.hidden = true; t.tag.textContent = b.host ? '☕ Cô Lá' : b.id === 'you' ? 'Bạn' : '🤝 ' + short;
        t.root.append(t.bubble, t.tag); overlay.append(t.root); tags.set(b.id, t);
      }
      const label = b.host ? '☕ Cô Lá' : b.id === 'you' ? 'Bạn' : '🤝 ' + short;
      if (t.tag.textContent !== label) t.tag.textContent = label;
      const bub = b.bubble && b.bubble.until > clock ? b.bubble.text : '';
      if (bub !== t.last) { t.last = bub; t.bubble.textContent = bub; t.bubble.hidden = !bub; t.bubble.className = 'bubble' + (bub ? ' pop' : ''); }
      const above = (b.y - 19 + (b.sit ? 3 : 0)) * scale, below = above - t.root.offsetHeight < 0;
      t.root.classList.toggle('below', below);
      const half = t.root.offsetWidth / 2, room = VW * scale;
      t.root.style.left = Math.min(room - half - 2, Math.max(half + 2, b.x * scale)) + 'px';
      t.root.style.top = (below ? (b.y + 1) * scale : above) + 'px';
      t.root.style.zIndex = String(Math.round(b.y) + (bub ? 200 : 0));
    }
  }
  function fit() {
    const stage = $('stage'), dpr = window.devicePixelRatio || 1;
    const w = stage.clientWidth, h = stage.clientHeight, fitScale = Math.min(w / VW, h / VH);
    let k = Math.max(1, Math.floor(fitScale * dpr)); scale = k / dpr;
    if (scale < fitScale * 0.85) { k = Math.ceil(fitScale * dpr); scale = fitScale; }
    canvas.width = VW * k; canvas.height = VH * k;
    const cw = Math.floor(VW * scale), ch = Math.floor(VH * scale);
    canvas.style.width = cw + 'px'; canvas.style.height = ch + 'px';
    ctx.setTransform(k, 0, 0, k, 0, 0); ctx.imageSmoothingEnabled = false;
    overlay.classList.toggle('compact', scale < 1.9);
    Object.assign(overlay.style, { left: Math.round((w - cw) / 2) + 'px', top: Math.round((h - ch) / 2) + 'px', width: cw + 'px', height: ch + 'px' });
  }
  window.addEventListener('resize', fit);

  let last = 0, held = false;
  function tick(dt) {
    clock += dt;
    if (mate.path) followPath(mate, dt);
    mate.walkMs = mate.moving ? mate.walkMs + dt * 1000 : 0;
    render();
    mate.moving = false;
  }
  function frame(now) { try { if (!held) { const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now; tick(dt); } } finally { schedule(); } }
  function schedule() { if (document.hidden) setTimeout(() => frame(performance.now()), 50); else requestAnimationFrame(frame); }

  const MOTION_LABEL = { full: 'Cử động: đầy đủ', reduced: 'Cử động: giảm', off: 'Cử động: tắt' };
  function applyMotion() { document.body.classList.toggle('reduced', motion === 'reduced'); document.body.classList.toggle('still', motion === 'off'); $('motionBtn').textContent = MOTION_LABEL[motion]; }
  $('motionBtn').addEventListener('click', () => { motion = { full: 'reduced', reduced: 'off', off: 'full' }[motion]; applyMotion(); toast(MOTION_LABEL[motion]); });

  applyMotion(); fit(); renderAll(); schedule(); openSetup();
  window.__doi = {
    hold: v => { held = v; }, step: ms => { for (let t = 0; t < ms; t += 16) tick(0.016); },
    S, start: (mode, courage) => { S.mode = mode || 'hai'; S.courage = courage || 'nhe'; bg = null; closeModal(); start(); },
    setTally: (f, arr) => { S.tally[f] = arr.slice(); renderMine(); }, sendCounts, gesture, pickName: n => pickBlank('name', n), level: () => S.level, holding: () => S.holding, goto: (lv, i) => { S.level = lv; S.stage = 'play'; startRound(i); }, mate: () => ({ x: mate.x, y: mate.y, sit: mate.sit, path: !!mate.path }),
    pick: (k, v) => pickBlank(k, v), lock, round: () => S.round, stage: () => S.stage, answer: () => Object.assign({}, S.answer), modalOpen: () => modalOpen
  };
})();
