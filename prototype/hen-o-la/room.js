// The rainy café look shared by the matchmaking evening (game.js) and the everyday café (quan.js):
// background tiles, rain, the cat, the counter front, people with their props, and small particles.
// Browser only; uses World (map) and Engine (lab 14 sprites).
(function (root) {
  'use strict';
  const W = root.World, E = root.Engine;
  const T = W.TILE, VW = W.W * T, VH = W.H * T;

  function px(ctx, c, x, y, w, h) { ctx.fillStyle = c; ctx.fillRect(Math.round(x), Math.round(y), w || 1, h || 1); }

  function background() {
    const bg = document.createElement('canvas'); bg.width = VW; bg.height = VH;
    const g = bg.getContext('2d');
    const r = (c, x, y, w, h) => { g.fillStyle = c; g.fillRect(x, y, w, h); };
    for (let ty = 0; ty < W.H; ty++) for (let tx = 0; tx < W.W; tx++) {
      const x = tx * T, y = ty * T, c = W.tileAt(tx, ty);
      // floor everywhere first: warm planks
      r((tx + ty) % 2 ? '#6b4a32' : '#714e35', x, y, T, T);
      r('#5c3f2a', x, y + 7, T, 1); r('#5c3f2a', x + ((ty % 2) ? 5 : 11), y, 1, 7); r('#5c3f2a', x + ((ty % 2) ? 12 : 3), y + 8, 1, 8);
      if (c === 'W' || c === 'w') {
        r('#3b2f4a', x, y, T, T); r('#33283f', x, y + 12, T, 4);
        if (ty === 1) r('#4a3a2a', x, y + 13, T, 3);
      }
      if (c === 'w') { r('#8a6a4a', x + 1, y + 1, 14, 12); r('#21324a', x + 2, y + 2, 12, 10); r('#8a6a4a', x + 7, y + 2, 1, 10); }
      if (c === 'C') {
        r('#7a5236', x, y + 4, T, 12); r('#9a6a44', x, y + 2, T, 4); r('#5a3a26', x, y + 14, T, 2);
        if (tx === 0) { r('#3a3a44', x + 3, y - 4, 9, 8); r('#c0c0c8', x + 5, y - 2, 5, 3); }
        if (tx === 3) { r('#f3ead8', x + 3, y, 3, 3); r('#f3ead8', x + 9, y + 1, 3, 2); }
      }
      if (c === 'p') { r('#2a2140', x + 4, y + 10, 8, 6); r('#b0603c', x + 5, y + 10, 6, 5); r('#3f8a5a', x + 2, y + 1, 12, 9); r('#5fae78', x + 4, y + 2, 4, 4); r('#5fae78', x + 9, y + 4, 3, 3); }
      if (c === 'K') {
        r('#5a3a26', x, y - 6, T, 22); r('#3a2418', x + 1, y - 5, 14, 20);
        const spines = ['#ef8a7a', '#7fc8a0', '#f2b45a', '#a995d8', '#6aa7e8', '#e8e4dc'];
        for (let row = 0; row < 3; row++) { r('#5a3a26', x + 1, y - 5 + row * 7 + 6, 14, 1); for (let i = 0; i < 6; i++) r(spines[(i + row + tx) % 6], x + 2 + i * 2, y - 4 + row * 7, 1 + (i % 2), 6); }
      }
      if (c === 'T') { r('#2a1d14', x + 3, y + 12, 10, 3); r('#a0724a', x + 1, y + 3, 14, 9); r('#b88458', x + 2, y + 3, 12, 2); r('#5a3a26', x + 7, y + 11, 2, 3); r('#f3ead8', x + 7, y + 1, 2, 3); }
      if (c === 'm') { r('#8a3a3a', x + 1, y + 6, 14, 9); r('#c0605a', x + 2, y + 6, 12, 7); }
      if (c === 'P') { r('#1f1a28', x, y - 4, T, 18); r('#2a2230', x + 1, y - 3, 14, 10); r('#e8e4dc', x + 1, y + 7, 14, 3); for (let i = 0; i < 7; i++) r('#1f1a28', x + 2 + i * 2, y + 7, 1, 2); }
      if (c === 'd') { r('#5a3e2a', x + 1, y, 14, T); r('#7a5236', x + 2, y + 1, 12, 15); r('#f2b45a', x + 11, y + 8, 2, 2); }
    }
    // rug in the middle
    g.fillStyle = 'rgba(169,149,216,.18)'; g.fillRect(5 * T + 4, 5 * T + 4, 5 * T - 8, T + 8);
    return bg;
  }

  function rain(ctx, clock, still) {
    for (let ty = 0; ty < W.H; ty++) for (let tx = 0; tx < W.W; tx++) {
      if (W.tileAt(tx, ty) !== 'w') continue;
      const x = tx * T + 2, y = ty * T + 2;
      for (let i = 0; i < 4; i++) {
        const off = still ? i * 3 : ((clock * 22 + i * 5 + tx * 3) % 12);
        px(ctx, '#6aa7e8', x + 1 + i * 3, y + off, 1, 2);
      }
    }
  }

  function cat(ctx, clock, still, petted) {
    const s = W.SPOTS.cat, x = s.tx * T, y = s.ty * T;
    const breathe = still ? 0 : Math.round((Math.sin(clock * 2) + 1) / 2);
    px(ctx, '#d9a050', x + 3, y + 4 - breathe, 10, 5 + breathe); px(ctx, '#b07a38', x + 4, y + 5, 2, 3); px(ctx, '#b07a38', x + 9, y + 5, 2, 3);
    px(ctx, '#d9a050', x + 11, y + 2 - breathe, 4, 4); px(ctx, '#d9a050', x + 11, y + 1 - breathe, 1, 1); px(ctx, '#d9a050', x + 14, y + 1 - breathe, 1, 1);
    const tail = petted && !still ? Math.round(Math.sin(clock * 8) * 2) : 0;
    px(ctx, '#d9a050', x + 1, y + 6 + tail, 3, 1);
    if (!petted) px(ctx, '#2a1f3d', x + 12, y + 3 - breathe, 2, 1);
  }

  // Warm light pools over the tables.
  function lamps(ctx, strength) {
    ctx.fillStyle = 'rgba(255,200,120,' + (strength || 0.06) + ')';
    for (const t of W.TABLES) ctx.fillRect(t.tx * T - 10, t.ty * T - 8, 36, 30);
  }

  // Drawn after the host so the counter hides her legs.
  function counterFront(ctx) {
    for (let tx = 0; tx < 5; tx++) { px(ctx, '#7a5236', tx * T, 2 * T + 6, T, 10); px(ctx, '#9a6a44', tx * T, 2 * T + 4, T, 3); px(ctx, '#5a3a26', tx * T, 2 * T + 14, T, 2); }
    px(ctx, '#f3ead8', 3 * T + 3, 2 * T + 1, 3, 3); px(ctx, '#3a3a44', 3, 2 * T - 2, 9, 7); px(ctx, '#c0c0c8', 5, 2 * T, 5, 3);
  }

  // A person: walk frames, blinking, what they are doing, and the small prop for it.
  // b.sit draws them seated (legs hidden behind the chair).
  function person(ctx, b, clock, still, hop) {
    let frame = b.moving ? E.walkFrame(b.walkMs) : 'stand';
    const blink = b.act === 'ngugat' || ((clock + (b.blinkAt || 0)) % 3.6) < 0.12 ? 1 : 0;
    let dir = b.dir, dx = 0, dy = 0;
    if (b.act === 'nhay' && !still) { dy = -Math.abs(Math.sin(clock * 9)) * 3; dir = Math.floor(clock * 3) % 2 ? 'left' : 'right'; frame = Math.floor(clock * 6) % 2 ? 'a' : 'b'; }
    if (b.act === 'mathe' && !still) dx = Math.floor(clock * 10) % 2 ? 1 : -1;
    if (b.act === 'ngugat' || b.act === 'chaptay') dy = 1;
    const spr = b.sheet[dir + ':' + frame + ':' + blink] || b.sheet['down:stand:0'];
    const x = Math.round(b.x - 7 + dx), y = Math.round(b.y - 17 + dy - (hop || 0) + (b.sit ? 3 : 0));
    if (!b.host) { ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(Math.round(b.x - 5), Math.round(b.y - 1), 10, 2); }
    if (b.sit) {
      ctx.save(); ctx.beginPath(); ctx.rect(x - 2, y - 2, 18, 15); ctx.clip();
      E.drawSprite(ctx, spr, x, y); ctx.restore();
      px(ctx, '#5a3a26', b.x - 5, b.y - 4, 10, 3); px(ctx, '#3a2418', b.x - 4, b.y - 1, 2, 2); px(ctx, '#3a2418', b.x + 2, b.y - 1, 2, 2);
    } else E.drawSprite(ctx, spr, x, y);
    const wave = Math.floor(clock * 6) % 2;
    if (b.act === 'vaytay') px(ctx, '#f2c9a0', x + (dir === 'left' ? -1 : 13), y + 7 - (still ? 0 : wave * 2), 2, 2);
    if (b.act === 'chaptay') { px(ctx, '#f2c9a0', x + 6, y + 10, 2, 3); }
    if (b.act === 'docsach' && dir === 'down') { px(ctx, '#ef8a7a', x + 4, y + 11, 6, 4); px(ctx, '#f3ead8', x + 6, y + 11, 2, 4); }
    if (b.act === 'tuoicay') px(ctx, '#7fa8c8', x + (dir === 'left' ? -2 : 12), y + 10, 4, 3);
    if (b.act === 'goido') px(ctx, '#f3ead8', x + 11, y + 10, 3, 3);
    if (b.act === 'mathe') px(ctx, '#ef8a7a', x + 6, y + 8, 2, 1);
  }

  // Little effects tied to what people are doing.
  function actParticles(people, particles, dt, still) {
    if (still) return;
    for (const b of people) {
      if (!b.act) continue;
      b.fxT = (b.fxT || 0) - dt;
      if (b.fxT > 0) continue;
      b.fxT = 0.7;
      if (b.act === 'ngugat') particles.push({ kind: 'z', x: b.x + 4, y: b.y - 20, vx: 3, vy: -8, life: 1.4 });
      if (b.act === 'danhdan') particles.push({ kind: 'note', x: b.x + (Math.random() * 10 - 5), y: b.y - 20, vx: Math.random() * 6 - 3, vy: -10, life: 1.4 });
      if (b.act === 'vuotmeo') particles.push({ kind: 'heart', x: W.SPOTS.cat.tx * T + 10, y: W.SPOTS.cat.ty * T, vx: 0, vy: -8, life: 1.2 });
      if (b.act === 'tuoicay') particles.push({ kind: 'drop', x: b.x + (b.dir === 'left' ? -8 : 8), y: b.y - 6, vx: 0, vy: 14, life: 0.5 });
    }
  }
  function stepParticles(particles, dt) {
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.life -= dt; p.x += p.vx * dt; p.y += p.vy * dt;
      if (p.kind === 'leaf') p.vx = Math.sin(p.life * 4) * 8;
      if (p.life <= 0) particles.splice(i, 1);
    }
  }
  function drawParticles(ctx, particles) {
    for (const p of particles) {
      const x = Math.round(p.x), y = Math.round(p.y);
      if (p.kind === 'z') { px(ctx, '#e8e4dc', x, y, 3, 1); px(ctx, '#e8e4dc', x + 1, y + 1, 1, 1); px(ctx, '#e8e4dc', x, y + 2, 3, 1); }
      if (p.kind === 'note') { px(ctx, '#f2b45a', x, y, 1, 4); px(ctx, '#f2b45a', x - 1, y + 3, 2, 2); px(ctx, '#f2b45a', x + 1, y, 2, 1); }
      if (p.kind === 'heart') { px(ctx, '#ef8a7a', x, y, 1, 1); px(ctx, '#ef8a7a', x + 2, y, 1, 1); px(ctx, '#ef8a7a', x, y + 1, 3, 1); px(ctx, '#ef8a7a', x + 1, y + 2, 1, 1); }
      if (p.kind === 'drop') px(ctx, '#6aa7e8', x, y, 1, 2);
      if (p.kind === 'leaf') { px(ctx, '#7fc8a0', x, y, 3, 2); px(ctx, '#4f8a6b', x + 1, y + 2, 1, 1); }
      if (p.kind === 'spark') { px(ctx, '#ffd98a', x, y, 1, 1); px(ctx, '#ffd98a', x - 2, y + 2, 1, 1); px(ctx, '#ffd98a', x + 2, y + 1, 1, 1); }
    }
  }

  root.Room = { VW, VH, px, background, rain, cat, lamps, counterFront, person, actParticles, stepParticles, drawParticles };
})(globalThis);
