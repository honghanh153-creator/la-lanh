// Khách quán: sit on the mezzanine during a matchmaking evening. Watch the shared moments, cheer for the
// moment (never for someone), order a drink, keep a note, take home a cup, a card, Cô Lá's notebook and a photo.
(function () {
  'use strict';
  const X = window.Xem, W = window.World, E = window.Engine, R = window.Room, Q = window.Quan, H = window.Hen;
  const $ = id => document.getElementById(id);
  const T = W.TILE, VW = W.W * T, VH = W.H * T;
  const rand = Math.random;
  const fast = new URLSearchParams(location.search).has('nhanh');
  const canvas = $('game'), ctx = canvas.getContext('2d'), overlay = $('overlay');
  const mezz = $('mezz'), mctx = mezz.getContext('2d');
  let scale = 1, clock = 0;
  let motion = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'reduced' : 'full';
  const still = () => motion === 'off';

  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function btn(text, cls, fn) { const b = el('button', cls, text); b.type = 'button'; b.addEventListener('click', fn); return b; }
  function pick(list) { return list[Math.floor(rand() * list.length)]; }

  // ---------- the daters on the floor: no names shown, nothing to click ----------
  const daters = H.GUESTS.map((g, i) => ({ id: g.id, x: 0, y: 0, dir: 'down', act: null, actUntil: 0, path: null, then: null, idle: rand() * 2,
    sheet: E.buildSheet(g.look), blinkAt: rand() * 4, walkMs: 0, moving: false, does: g.does, gear: null, sit: false, seat: i }));
  const host = { id: 'host', host: true, x: W.HOST.tx * T + 8, y: W.HOST.ty * T + 7, dir: 'down', sheet: E.buildSheet({ H: '#2b2230', T: '#3f6b55', C: '#7fc8a0', P: '#30303a', B: '#1d1b26', longHair: true, hat: true }) };
  const feetOf = (tx, ty) => ({ x: tx * T + 8, y: ty * T + 12 });
  const tileOf = b => [Math.floor(b.x / T), Math.floor((b.y - 1) / T)];
  const free = W.freeTiles ? W.freeTiles() : [];
  daters.forEach((d, i) => { const t = free[(i * 7 + 3) % free.length] || W.ENTRY; Object.assign(d, feetOf(t[0], t[1])); });
  function walkTo(b, tx, ty, then) {
    const path = W.findPath(tileOf(b), [tx, ty]);
    if (!path) return false;
    b.act = null; b.path = path.slice(1); b.then = then || null;
    if (!b.path.length) { b.path = null; const t = b.then; b.then = null; if (t) t(); }
    return true;
  }
  function followPath(b, dt) {
    const [tx, ty] = b.path[0], goal = feetOf(tx, ty);
    const dx = goal.x - b.x, dy = goal.y - b.y, d = Math.hypot(dx, dy), step = 38 * dt;
    if (d <= step) { b.x = goal.x; b.y = goal.y; b.path.shift(); if (!b.path.length) { b.path = null; const t = b.then; b.then = null; if (t) t(); } }
    else { b.x += dx / d * step; b.y += dy / d * step; }
    if (Math.abs(dx) > Math.abs(dy)) b.dir = dx > 0 ? 'right' : 'left'; else if (dy) b.dir = dy > 0 ? 'down' : 'up';
    b.moving = true;
  }
  function daterThink(b, dt) {
    if (b.path || (b.act && b.actUntil > clock)) return;
    b.idle -= dt; if (b.idle > 0) return;
    b.idle = 1.5 + rand() * 3;
    const m = moment();
    if (m.id === 'tudo') {
      const act = pick(b.does), spots = Object.values(W.SPOTS).filter(s => s.act === act);
      const s = pick(spots);
      const stand = s && W.standTiles(s.tx, s.ty, tileOf(b))[0];
      if (stand) walkTo(b, stand[0], stand[1], () => { b.act = act; b.actUntil = clock + 4 + rand() * 4; });
      else { b.act = act; b.actUntil = clock + 3; }
    } else {
      // gather loosely around the rug for the shared moments
      const tx = 3 + (b.seat % 5) * 2, ty = b.seat < 5 ? 5 : 6;
      if (!W.solidTile(tx, ty)) walkTo(b, tx, ty, () => { b.dir = 'up'; });
    }
  }

  // ---------- the mezzanine ----------
  const neighbours = Array.from({ length: 8 }, () => ({ sheet: E.buildSheet(pick(H.LOOKS.concat(H.GUESTS.map(g => g.look)))), clapUntil: 0, blinkAt: rand() * 4, name: Q.randomName(rand), bubble: null }));
  const meName = Q.randomName(rand);
  const me = { sheet: E.buildSheet(pick(H.LOOKS)), clapUntil: 0, blinkAt: 0, name: meName, me: true, bubble: null };
  const row = neighbours.slice(0, 4).concat([me], neighbours.slice(4));
  function drawMezz() {
    const k = mezz.width / 240;
    mctx.setTransform(k, 0, 0, k, 0, 0); mctx.imageSmoothingEnabled = false;
    mctx.fillStyle = '#3d3048'; mctx.fillRect(0, 0, 240, 30);
    for (let x = 1; x < 240; x += 4) { mctx.fillStyle = '#45374f'; mctx.fillRect(x, 0, 1, 18); }
    for (let x = 0; x < 240; x += 6) { mctx.fillStyle = x % 12 ? '#ffd98a' : '#ffb070'; mctx.fillRect(x + 3, 2 + Math.round(Math.abs(Math.sin(x / 40 * Math.PI)) * 2), 1, 2); }
    row.forEach((p, i) => {
      const x = 10 + i * 25, y = 6;
      const blink = ((clock + p.blinkAt) % 3.6) < 0.12 ? 1 : 0;
      const spr = p.sheet['down:stand:' + blink];
      mctx.save(); mctx.beginPath(); mctx.rect(x, y, 16, 15); mctx.clip(); E.drawSprite(mctx, spr, x, y); mctx.restore();
      if (p.clapUntil > clock) { const up = still() ? 0 : Math.floor(clock * 8) % 2; mctx.fillStyle = '#f2c9a0'; mctx.fillRect(x + 5, y + 10 - up * 2, 2, 2); mctx.fillRect(x + 8, y + 10 - up * 2, 2, 2); }
      if (p.me) { mctx.fillStyle = '#7fc8a0'; mctx.fillRect(x + 4, y - 4, 8, 1); }
      if (p.me && myDrink) { mctx.fillStyle = '#f3ead8'; mctx.fillRect(x + 13, y + 14, 4, 4); mctx.fillStyle = Q.DRINKS[myDrink].color; mctx.fillRect(x + 14, y + 15, 2, 1); }
    });
    // the wooden rail hides everyone's legs
    mctx.fillStyle = '#5a3a26'; mctx.fillRect(0, 20, 240, 10); mctx.fillStyle = '#8a6a4a'; mctx.fillRect(0, 20, 240, 2);
    for (let x = 4; x < 240; x += 8) { mctx.fillStyle = '#4a3020'; mctx.fillRect(x, 23, 2, 7); }
  }

  // ---------- state ----------
  let seated = false, queue = null, mi = 0, momentEnd = 0, lastCheer = -9, myDrink = null, myCard = null, myNotes = [], notesShown = [], photo = null, lanterns = [], over = false;
  const moment = () => X.MOMENTS[Math.min(mi, X.MOMENTS.length - 1)];
  const secs = m => fast ? Math.ceil(m.secs / 3) : m.secs;
  const particles = [];

  function arrive() {
    queue = X.arrive(rand);
    if (queue.seated) sit();
    else {
      const body = openModal('XẾP HÀNG', 'Tầng lửng đã kín chỗ', false);
      const p = el('p', '', ''); body.append(p, el('p', 'note', 'Có người về thì người kế tiếp được vào. Bạn không cần làm gì.'));
      const tickQ = () => {
        p.textContent = 'Bạn đứng thứ ' + queue.ahead + ' trong hàng.';
        queue = X.queueStep(queue);
        if (queue.seated) setTimeout(() => { closeModal(); sit(); }, 900); else setTimeout(tickQ, fast ? 600 : 2200);
      };
      tickQ();
    }
  }
  function sit() {
    seated = true; mi = 0; momentEnd = clock + secs(moment());
    $('mezzLabel').textContent = 'Tầng lửng · ' + X.SEATS + ' chỗ · bạn là ' + meName;
    hostSay('Chào ' + meName + '. Tầng lửng nhìn xuống được cả quán. Ngồi đâu cũng được nha.');
    renderAll();
  }
  function nextMoment() {
    if (over) return;
    if (mi >= X.MOMENTS.length - 1) { finish(); return; }
    mi += 1; momentEnd = clock + secs(moment());
    const m = moment();
    banner('Khoảnh khắc chung · ' + m.title, 4);
    for (const d of daters) { d.act = null; d.path = null; d.idle = rand(); }
    if (m.id === 'thaden') startLanterns();
    if (m.id === 'taihien') retell();
    renderAll();
  }
  function startLanterns() {
    lanterns = [];
    const pairs = X.lanternPairs(rand);
    for (let i = 0; i < pairs; i++) lanterns.push({ x: 60 + i * 60 + rand() * 20, y: VH - 30, born: clock + i * 1.5 });
    hostSay(pairs + ' đôi đèn bay lên. Quán không biết ai chọn ai, chỉ biết tối nay có ' + pairs + ' đôi.');
    setTimeout(() => { try { photo = canvas.toDataURL(); } catch (e) { photo = null; } }, fast ? 2500 : 6000);
  }
  function retell() {
    hostSay('Vụ tối nay: tiếng hát lạ hoá ra là bản nhạc sinh nhật phát chậm. Cả quán cười.');
    const notes = X.hostNotes(rand, 3);
    notes.forEach((n, i) => setTimeout(() => { notesShown.push(n); renderHostNotes(); }, (i + 1) * (fast ? 1200 : 4000)));
  }

  // ---------- cheering: for the moment, never for one person ----------
  function cheer(kind) {
    if (!seated || over || clock - lastCheer < 1.2) return;
    const c = X.cheer(kind); if (!c) return;
    lastCheer = clock;
    if (kind === 'votay') {
      me.clapUntil = clock + 2;
      for (const n of neighbours) if (rand() < 0.5) n.clapUntil = clock + 1 + rand() * 2;
      if (!still()) for (let i = 0; i < 6; i++) particles.push({ kind: 'spark', x: 20 + rand() * (VW - 40), y: 8 + rand() * 10, vx: 0, vy: -4, life: 0.8 });
      toast('👏 Cả tầng lửng vỗ tay cho khoảnh khắc này.');
    } else {
      if (!still()) for (let i = 0; i < 10; i++) particles.push({ kind: 'leaf', x: rand() * VW, y: -4 - rand() * 20, vx: 0, vy: 14 + rand() * 8, life: 6 });
      toast('🍃 Lá cổ vũ rơi khắp quán, không vào tay riêng ai.');
    }
  }

  // ---------- panel ----------
  function renderMoment() {
    const box = $('momentCard'); box.replaceChildren();
    if (!seated) { box.append(el('small', '', 'TẦNG LỬNG'), el('h2', '', 'Đang vào quán'), el('p', '', 'Chờ chút nha.')); return; }
    const m = moment();
    box.append(el('small', '', 'KHOẢNH KHẮC ' + (mi + 1) + '/' + X.MOMENTS.length), el('h2', '', m.title), el('p', '', m.text),
      el('p', 'clock', String(Math.max(0, Math.ceil(momentEnd - clock)))),
      btn(mi < X.MOMENTS.length - 1 ? 'Sang khoảnh khắc sau' : 'Hết buổi', '', nextMoment));
  }
  function renderCard() {
    const box = $('cardBox'); box.replaceChildren();
    if (!myCard) { box.append(el('b', '', '🃏 Lá bài tối nay'), el('div', '', 'Hỏi Cô Lá khi gọi ly. Lá bài chỉ gợi một việc nhỏ.')); return; }
    box.append(el('b', '', '🃏 ' + myCard.card), el('div', '', myCard.todo));
  }
  function renderHostNotes() {
    const box = $('hostNotes'); box.replaceChildren();
    if (!notesShown.length) { box.append(el('p', 'note-hint', 'Cô Lá ghi lại vài khoảnh khắc dễ thương, không nói ai là ai. Tới phần tái hiện sẽ có.')); return; }
    for (const n of notesShown) box.append(el('div', 'letter', n));
  }
  function renderActs() {
    const box = $('acts'); box.replaceChildren();
    box.append(btn('👏 Vỗ tay', '', () => cheer('votay')), btn('🍃 Thả lá cổ vũ', '', () => cheer('la')), btn(myDrink ? '☕ Ly của bạn' : '☕ Gọi ly', 'spot', openOrder));
    const q = $('quick'); q.replaceChildren();
    for (const g of Q.GREETINGS.slice(0, 3)) q.append(btn(g, '', () => { toast('Bạn: ' + g); setTimeout(() => toast(pick(neighbours).name + ': ' + pick(['Chào bạn 🙏', 'Bình yên nha', 'Mưa đẹp ghê'])), 900); }));
  }
  function renderAll() { renderMoment(); renderCard(); renderHostNotes(); renderActs(); }
  function openOrder() {
    const body = openModal('CÔ LÁ MANG LÊN', 'Uống gì nè?');
    const r = el('div', 'choices');
    for (const [k, d] of Object.entries(Q.DRINKS)) { const b = btn(d.label, '', () => { myDrink = k; closeModal(); renderActs(); hostSay('Một ly ' + d.label.toLowerCase() + ' lên tầng lửng nè.'); }); b.setAttribute('aria-pressed', myDrink === k ? 'true' : 'false'); r.append(b); }
    body.append(r, btn(myCard ? 'Xem lá bài tối nay' : 'Xin lá bài tối nay', 'primary', () => { myCard = Q.dailyCard(Q.dateKey(new Date())); closeModal(); renderCard(); hostSay('Lá ' + myCard.card + '. ' + myCard.todo); }));
  }
  $('noteForm').addEventListener('submit', e => {
    e.preventDefault();
    const t = Q.sanitizeNote($('noteInput').value);
    if (!t || myNotes.length >= Q.NOTE_LIMIT) return;
    myNotes.push(t); $('noteInput').value = '';
    $('noteCount').textContent = 'Đã cất ' + myNotes.length + '/' + Q.NOTE_LIMIT + ' note. Chỉ nằm trong tab này.';
    $('noteInput').disabled = myNotes.length >= Q.NOTE_LIMIT;
    toast('Đã cất note.');
  });

  // ---------- take home ----------
  function finish() {
    over = true;
    if (!myCard) myCard = Q.dailyCard(Q.dateKey(new Date()));
    if (notesShown.length < 3) { notesShown = notesShown.concat(X.hostNotes(rand, 3).filter(n => !notesShown.includes(n))).slice(0, 3); renderHostNotes(); }
    const body = openModal('HẾT BUỔI', 'Mang về từ tầng lửng', false);
    if (photo) { const img = el('img', 'memory'); img.src = photo; img.alt = 'Ảnh kỷ niệm của quán lúc thả đèn.'; body.append(el('div', 'field', 'Ảnh kỷ niệm của quán'), img); }
    if (myDrink) body.append(el('p', '', '☕ Ly của tối nay: ' + Q.DRINKS[myDrink].label + '.'));
    body.append(el('div', 'letter', '🃏 ' + myCard.card + ': ' + myCard.todo), el('div', 'field', 'Ghi chép của Cô Lá'));
    for (const n of notesShown) body.append(el('div', 'letter', n));
    if (myNotes.length) { body.append(el('div', 'field', 'Note bạn để lại')); for (const n of myNotes) body.append(el('div', 'letter', n)); }
    body.append(btn('Lần sau mình muốn hẹn', 'primary', () => toast('Bản thử chưa nhận đăng ký. Ở bản thật, bạn nhận thư mời nếu được chọn.')), document.createTextNode(' '),
      btn('Ngồi lại buổi khác', 'ghost', () => location.reload()));
    renderAll();
  }
  $('leaveBtn').addEventListener('click', () => { if (!modalOpen && seated) finish(); });

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
  let toastTimer = null, bannerTimer = null;
  function toast(msg) { const t = $('toast'); t.textContent = msg; t.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, 3000); }
  function banner(msg, s) { const b = $('banner'); b.textContent = msg; b.hidden = false; clearTimeout(bannerTimer); bannerTimer = setTimeout(() => { b.hidden = true; }, (s || 4) * 1000); }
  function hostSay(text) { banner('☕ Cô Lá: ' + text, 6); }

  // ---------- drawing ----------
  const bg = R.background();
  function drawLanterns() {
    for (const l of lanterns) {
      const t = clock - l.born; if (t < 0) continue;
      const y = Math.max(-20, l.y - t * (still() ? 0 : 9)), sway = still() ? 0 : Math.round(Math.sin(t * 1.5) * 2);
      for (const [dx, col] of [[-5, '#ef8a7a'], [5, '#f2b45a']]) {
        const x = Math.round(l.x + dx + sway);
        ctx.fillStyle = 'rgba(255,214,140,.25)'; ctx.fillRect(x - 3, y - 3, 10, 12);
        ctx.fillStyle = col; ctx.fillRect(x, y, 5, 6); ctx.fillStyle = '#ffe8a8'; ctx.fillRect(x + 1, y + 6, 3, 1); ctx.fillStyle = '#5a3a26'; ctx.fillRect(x + 1, y - 1, 3, 1);
      }
    }
  }
  function render() {
    ctx.drawImage(bg, 0, 0);
    R.rain(ctx, clock, still());
    R.cat(ctx, clock, still(), daters.some(d => d.act === 'vuotmeo'));
    R.lamps(ctx, 0.08);
    R.person(ctx, host, clock, still(), 0);
    R.counterFront(ctx);
    for (const b of daters.slice().sort((a, c) => a.y - c.y)) R.person(ctx, b, clock, still(), 0);
    R.pendants(ctx);
    drawLanterns();
    R.drawParticles(ctx, particles);
    R.glow(ctx, true);
    R.vignette(ctx, 0.38);
    drawMezz();
  }
  function fit() {
    const stage = $('stage'), dpr = window.devicePixelRatio || 1;
    const w = stage.clientWidth, h = stage.clientHeight, fitScale = Math.min(w / VW, h / VH);
    let k = Math.max(1, Math.floor(fitScale * dpr)); scale = k / dpr;
    if (scale < fitScale * 0.85) { k = Math.ceil(fitScale * dpr); scale = fitScale; }
    canvas.width = VW * k; canvas.height = VH * k;
    canvas.style.width = Math.floor(VW * scale) + 'px'; canvas.style.height = Math.floor(VH * scale) + 'px';
    ctx.setTransform(k, 0, 0, k, 0, 0); ctx.imageSmoothingEnabled = false;
    const mk = Math.max(1, Math.round(mezz.clientWidth * dpr / 240)); mezz.width = 240 * mk; mezz.height = 30 * mk;
  }
  window.addEventListener('resize', fit);

  let last = 0, held = false, panelT = 0;
  function tick(dt) {
    if (!modalOpen || !seated) clock += dt;
    for (const d of daters) {
      if (d.path) followPath(d, dt); else if (seated && !over) daterThink(d, dt);
      if (d.act && d.actUntil <= clock) d.act = null;
      if (d.moving) d.walkMs += dt * 1000; else d.walkMs = 0;
    }
    R.actParticles(daters, particles, dt, still());
    R.stepParticles(particles, dt);
    if (seated && !over && !modalOpen && clock >= momentEnd) nextMoment();
    panelT -= dt; if (panelT <= 0) { panelT = 1; if (seated) renderMoment(); }
    render();
    for (const d of daters) d.moving = false;
  }
  function frame(now) { try { if (!held) { const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now; tick(dt); } } finally { schedule(); } }
  function schedule() { if (document.hidden) setTimeout(() => frame(performance.now()), 50); else requestAnimationFrame(frame); }

  const MOTION_LABEL = { full: 'Cử động: đầy đủ', reduced: 'Cử động: giảm', off: 'Cử động: tắt' };
  function applyMotion() { document.body.classList.toggle('reduced', motion === 'reduced'); document.body.classList.toggle('still', motion === 'off'); $('motionBtn').textContent = MOTION_LABEL[motion]; if (motion !== 'full') particles.length = 0; }
  $('motionBtn').addEventListener('click', () => { motion = { full: 'reduced', reduced: 'off', off: 'full' }[motion]; applyMotion(); toast(MOTION_LABEL[motion]); });

  applyMotion(); fit(); renderAll(); schedule(); arrive();
  window.__khach = {
    hold: v => { held = v; }, step: ms => { for (let t = 0; t < ms; t += 16) tick(0.016); },
    next: nextMoment, cheer, moment: () => moment().id, seated: () => seated, over: () => over, photo: () => !!photo,
    order: k => { myDrink = k; renderActs(); }, finish, modalOpen: () => modalOpen, closeModal
  };
})();
