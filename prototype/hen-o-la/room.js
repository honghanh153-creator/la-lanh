// The rainy café look shared by the matchmaking evening (game.js) and the everyday café (quan.js):
// background tiles, rain, the cat, the counter front, people with their props, and small particles.
// Browser only; uses World (map) and Engine (lab 14 sprites).
(function (root) {
  'use strict';
  const W = root.World, E = root.Engine;
  const T = W.TILE, VW = W.W * T, VH = W.H * T;

  function px(ctx, c, x, y, w, h) { ctx.fillStyle = c; ctx.fillRect(Math.round(x), Math.round(y), w || 1, h || 1); }

  function shadeOf(hex, k) {
    const n = parseInt(hex.slice(1), 16), f = c => Math.max(0, Math.min(255, Math.round(c * k)));
    return 'rgb(' + f(n >> 16) + ',' + f((n >> 8) & 255) + ',' + f(n & 255) + ')';
  }
  const WINDOWS = [2, 6, 10]; // left tile of each two-tile window on row 1
  const FLOWERS = ['#ef8a7a', '#f2b45a', '#a995d8', '#f3ead8', '#ef8a7a', '#7fc8a0'];

  // opts.day: lighter sky in the windows. The evening always runs at night.
  function background(opts) {
    const day = !!(opts && opts.day);
    const bg = document.createElement('canvas'); bg.width = VW; bg.height = VH;
    const g = bg.getContext('2d');
    const r = (c, x, y, w, h) => { g.fillStyle = c; g.fillRect(x, y, w, h); };
    for (let ty = 0; ty < W.H; ty++) for (let tx = 0; tx < W.W; tx++) {
      const x = tx * T, y = ty * T, c = W.tileAt(tx, ty);
      // floor everywhere first: warm planks
      r((tx + ty) % 2 ? '#6b4a32' : '#714e35', x, y, T, T);
      r('#5c3f2a', x, y + 7, T, 1); r('#5c3f2a', x + ((ty % 2) ? 5 : 11), y, 1, 7); r('#5c3f2a', x + ((ty % 2) ? 12 : 3), y + 8, 1, 8);
      if (ty <= 1 && (c === 'W' || c === 'w')) {
        // back wall: striped wallpaper over a wood wainscot
        r('#3d3048', x, y, T, T);
        for (let i = 1; i < T; i += 4) r('#45374f', x + i, y, 1, T);
        if (ty === 1) { r('#6a4a32', x, y + 4, T, 1); r('#4a3426', x, y + 5, T, 11); r('#56402e', x + 1, y + 7, 6, 7); r('#56402e', x + 9, y + 7, 6, 7); r('#3a281c', x, y + 15, T, 1); }
      } else if (c === 'W') { r('#3b2f4a', x, y, T, T); r('#33283f', x, y + 12, T, 4); r('#4a3426', x, y, T, 3); }
      if (c === 'K') {
        r('#5a3a26', x, y - 6, T, 22); r('#3a2418', x + 1, y - 5, 14, 20);
        const spines = ['#ef8a7a', '#7fc8a0', '#f2b45a', '#a995d8', '#6aa7e8', '#e8e4dc'];
        for (let row = 0; row < 3; row++) { r('#5a3a26', x + 1, y - 5 + row * 7 + 6, 14, 1); for (let i = 0; i < 6; i++) r(spines[(i + row + tx) % 6], x + 2 + i * 2, y - 4 + row * 7, 1 + (i % 2), 6); }
      }
      if (c === 'P') {
        r('#1f1a28', x, y - 4, T, 18); r('#2a2230', x + 1, y - 3, 14, 10); r('#e8e4dc', x + 1, y + 7, 14, 3); for (let i = 0; i < 7; i++) r('#1f1a28', x + 2 + i * 2, y + 7, 1, 2);
        r('#f2b45a', x + 3, y - 7, 2, 3); r('#f3ead8', x + 2, y - 8, 4, 1); r('#7fc8a0', x + 10, y - 8, 3, 4); r('#b0603c', x + 10, y - 5, 3, 2); // lamp and a small pot on top
      }
      if (c === 'd') { r('#5a3e2a', x + 1, y, 14, T); r('#7a5236', x + 2, y + 1, 12, 15); r('#21324a', x + 4, y + 2, 8, 5); r('#8a6a4a', x + 7, y + 2, 1, 5); r('#f2b45a', x + 11, y + 8, 2, 2); }
      if (c === 'm') { r('#8a3a3a', x + 1, y + 6, 14, 9); r('#c0605a', x + 2, y + 6, 12, 7); r('#d98a7a', x + 3, y + 7, 10, 1); }
    }
    // tall windows with a sill, curtains and a little pot or candle
    for (const tx of WINDOWS) {
      const x = tx * T, w = 2 * T;
      r('#8a6a4a', x + 1, 3, w - 2, 2 * T - 5); r(day ? '#5d7f9e' : '#21324a', x + 3, 5, w - 6, 2 * T - 10);
      r(day ? '#6d8fae' : '#27394f', x + 3, 5, w - 6, 4);
      r('#8a6a4a', x + T - 1, 5, 2, 2 * T - 10); r('#8a6a4a', x + 3, 15, w - 6, 1);
      r('#b88458', x, 2 * T - 5, w, 2); r('#5a3a26', x, 2 * T - 3, w, 1);
      r('#a9616a', x - 1, 2, 3, 2 * T - 8); r('#c97a80', x - 1, 2, 1, 2 * T - 8); r('#a9616a', x + w - 2, 2, 3, 2 * T - 8); r('#c97a80', x + w, 2, 1, 2 * T - 8);
      r('#6a4a32', x - 2, 1, w + 4, 2);
      if (tx === 6) { r('#f3ead8', x + 4, 2 * T - 8, 2, 3); r('#ffd98a', x + 4, 2 * T - 9, 2, 1); }
      else { r('#b0603c', x + w - 8, 2 * T - 8, 4, 3); r('#5fae78', x + w - 9, 2 * T - 11, 6, 3); }
    }
    // chalkboard menu behind the counter
    r('#6a4a32', 2, 3, 28, 20); r('#26302a', 3, 4, 26, 18);
    for (const [lx, ly, lw] of [[5, 6, 12], [5, 9, 16], [5, 12, 10], [5, 15, 14], [5, 18, 9]]) r('#d8d4c8', lx, ly, lw, 1);
    r('#d8d4c8', 22, 13, 4, 4); r('#26302a', 23, 14, 2, 2); r('#d8d4c8', 26, 14, 1, 2); r('#d8d4c8', 23, 11, 1, 1); r('#d8d4c8', 24, 10, 1, 1);
    // floating shelves with jars and mugs
    for (const sy of [12, 22]) { r('#8a6a4a', 4 * T + 1, sy, 2 * T - 2, 2); r('#5a3a26', 4 * T + 1, sy + 2, 2 * T - 2, 1); }
    const jars = [['#f3ead8', '#ef8a7a'], ['#f3ead8', '#7fc8a0'], ['#f3ead8', '#f2b45a']];
    jars.forEach(([j, lid], i) => { r(j, 4 * T + 3 + i * 6, 7, 4, 5); r(lid, 4 * T + 3 + i * 6, 6, 4, 1); r('#a0724a', 4 * T + 4 + i * 6, 9, 2, 2); });
    for (let i = 0; i < 3; i++) { r(['#6aa7e8', '#f3ead8', '#c0605a'][i], 4 * T + 3 + i * 7, 18, 4, 4); r('#2a1f3d', 4 * T + 7 + i * 7, 19, 1, 2); }
    r('#5fae78', 4 * T + 24, 16, 5, 3); r('#3f8a5a', 4 * T + 25, 19, 3, 3);
    // a framed painting: sunset over hills
    const fx = 8 * T + 3, fy = 5;
    r('#8a6a4a', fx, fy, 26, 18); r('#f3ead8', fx + 2, fy + 2, 22, 14); r('#f2c08a', fx + 4, fy + 4, 18, 6); r('#ef9a7a', fx + 4, fy + 8, 18, 2);
    r('#ffe0a0', fx + 13, fy + 5, 4, 3); r('#5fae78', fx + 4, fy + 10, 18, 4); r('#3f8a5a', fx + 4, fy + 12, 9, 2); r('#7fc8a0', fx + 12, fy + 10, 6, 1);
    // a mint neon leaf, unlit by day
    const nx = 12 * T + 4, ny = 5, neon = day ? '#5f8a74' : '#9fe8c0';
    for (const [a, b] of [[8, 0], [6, 1], [10, 1], [5, 2], [11, 2], [4, 4], [12, 4], [4, 6], [12, 6], [5, 8], [11, 8], [6, 10], [10, 10], [8, 11], [8, 12], [8, 13], [8, 14]]) r(neon, nx + a, ny + b, 1 + (a === 8 ? 0 : 1), 1);
    r(neon, nx + 8, ny + 2, 1, 9);
    // a trailing pothos in the corner
    r('#b0603c', 14 * T + 3, 3, 8, 4); r('#8a4a2a', 14 * T + 3, 6, 8, 1); r('#3a2418', 14 * T + 7, 0, 1, 3);
    for (const [vx, len] of [[4, 14], [7, 18], [10, 11]]) for (let i = 0; i < len; i += 3) r(i % 6 ? '#5fae78' : '#3f8a5a', 14 * T + vx + (i % 6 ? 1 : 0), 7 + i, 2, 2);
    // fairy lights along the wall
    for (let x = 0; x < VW; x++) { const yy = 2 + Math.round(Math.abs(Math.sin(x / 48 * Math.PI)) * 4); r('#2a1f2a', x, yy, 1, 1); if (x % 6 === 3) r(['#ffd98a', '#ffb070', '#fff0c0'][(x / 6 | 0) % 3], x, yy + 1, 1, 2); }
    // counter base (the top and its things are drawn by counterTop, also after the host)
    for (let tx = 0; tx < 5; tx++) counterTop(g, tx * T, 2 * T);
    // plants on the floor
    for (const [tx, ty] of [[8, 2], [14, 8]]) {
      const x = tx * T, y = ty * T;
      r('#2a2140', x + 4, y + 10, 8, 6); r('#d8c8a8', x + 4, y + 9, 8, 6); r('#b8a888', x + 4, y + 13, 8, 2);
      if (tx === 8) { r('#3f8a5a', x + 1, y - 2, 14, 11); r('#5fae78', x + 3, y - 1, 4, 4); r('#5fae78', x + 9, y + 1, 4, 3); r('#7fc8a0', x + 6, y - 4, 3, 3); }
      else { for (let i = 0; i < 5; i++) r(i % 2 ? '#5fae78' : '#3f8a5a', x + 3 + i * 2, y - 3 + (i % 2) * 3, 2, 12 - (i % 2) * 3); }
    }
    // a woven rug down the aisle
    const rx = 2 * T + 8, ry = 5 * T + 3, rw = 10 * T, rh = 2 * T - 6;
    r('#7a3a34', rx, ry, rw, rh); r('#b86a4a', rx + 2, ry + 2, rw - 4, rh - 4); r('#d9b48a', rx + 4, ry + 4, rw - 8, rh - 8); r('#b86a4a', rx + 6, ry + 6, rw - 12, rh - 12);
    for (let i = 0; i < rw - 16; i += 8) { const cx = rx + 10 + i, cy = ry + rh / 2 - 1; r('#7a3a34', cx, cy - 2, 2, 1); r('#7a3a34', cx - 2, cy, 6, 2); r('#7a3a34', cx, cy + 3, 2, 1); r('#f3ead8', cx, cy, 2, 2); }
    for (let i = 0; i < rh; i += 2) { r('#d9b48a', rx - 2, ry + i, 2, 1); r('#d9b48a', rx + rw, ry + i, 2, 1); }
    // cushioned benches under the street windows
    for (const tx of [6, 10]) {
      const x = tx * T + 1, y = 2 * T, w = 2 * T - 2;
      r('#5a3a26', x, y + 9, w, 5); r('#8a6a4a', x, y + 9, w, 1); r('#a9616a', x, y + 5, w, 4); r('#c97a80', x + 1, y + 5, w - 2, 1);
      r('#f3ead8', x + 2, y + 2, 5, 4); r('#ef9a8a', x + 3, y + 3, 3, 2); // a little pillow
    }
    // reading nook: a green rug, two bean bags, a book stack and a reading lamp
    { const x = W.NOOK[0][0] * T, y = W.NOOK[0][1] * T;
      r('#4f7a64', x + 1, y + 3, 2 * T - 2, 12); r('#5f8a74', x + 2, y + 4, 2 * T - 4, 10);
      for (const [i, c, d] of [[0, '#e3b23c', '#c08a2a'], [1, '#ef8a7a', '#c0605a']]) { const bx = x + i * T; r(d, bx + 2, y + 6, 12, 7); r(c, bx + 3, y + 5, 10, 6); r(c, bx + 2, y + 7, 12, 4); }
      r('#6aa7e8', x - 6, y + 10, 5, 2); r('#f2b45a', x - 6, y + 8, 5, 2); r('#a995d8', x - 5, y + 6, 4, 2);
      r('#3a2418', x - 10, y - 4, 1, 16); r('#f2b45a', x - 12, y - 6, 5, 3); r('#ffe8a8', x - 11, y - 3, 3, 1);
    }
    // a welcome mat inside the door
    r('#6b5a3a', W.ENTRY[0] * T + 2, W.ENTRY[1] * T + 6, 12, 8); for (let i = 0; i < 12; i += 3) r('#8a7650', W.ENTRY[0] * T + 2 + i, W.ENTRY[1] * T + 6, 1, 8);
    // round tables with a bud vase, and rattan chairs on both sides
    for (const t of W.TABLES) {
      const x = t.tx * T, y = t.ty * T;
      for (const [sx, sy] of t.seats) chair(g, sx * T, sy * T, sx < t.tx, true);
      r('#2a1d14', x + 4, y + 13, 8, 2); r('#3a2418', x + 7, y + 10, 2, 4);
      r('#7a5236', x + 2, y + 10, 12, 1); r('#a0724a', x + 1, y + 4, 14, 6); r('#a0724a', x + 2, y + 3, 12, 1); r('#b88458', x + 3, y + 3, 10, 2);
      r('#9fd3bd', x + 7, y + 2, 2, 3); r('#5fae78', x + 8, y, 1, 2); r(FLOWERS[t.n % FLOWERS.length], x + 7, y - 1, 2, 2);
    }
    return bg;
  }

  // Rattan chair; back on the outer side. full=false skips the back (drawn later over a seated person).
  function chair(ctx, x, y, left, full) {
    const p = (c, a, b, w, h) => px(ctx, c, x + a, y + b, w, h);
    p('#3a2418', 4, 11, 1, 3); p('#3a2418', 11, 11, 1, 3);
    p('#9a6a3a', 3, 8, 10, 3); p('#c8965a', 4, 8, 8, 1); p('#b8864e', 4, 9, 8, 1);
    if (full) { const bx = left ? 2 : 12; p('#9a6a3a', bx, 1, 2, 10); p('#c8965a', bx, 2, 2, 1); p('#c8965a', bx, 5, 2, 1); }
  }

  // The counter top and what stands on it: coffee machine, a cake dome, cups, the bell.
  function counterTop(ctx, x, y) {
    const r = (c, a, b, w, h) => { ctx.fillStyle = c; ctx.fillRect(x + a, y + b, w, h); };
    r('#7a5236', 0, 6, T, 8); r('#9a6a44', 0, 3, T, 4); r('#b88458', 0, 3, T, 1); r('#5a3a26', 0, 14, T, 2);
    for (let i = 2; i < T; i += 5) r('#6a4630', i, 8, 1, 6);
    const tx = x / T;
    if (tx === 0) { r('#3a3a44', 3, -5, 10, 9); r('#c0c0c8', 4, -4, 8, 2); r('#2a2a30', 6, 0, 4, 2); r('#ef8a7a', 11, -3, 1, 1); }
    if (tx === 1) { r('#e8f0f0', 3, -3, 10, 6); r('#cfe0e0', 3, -3, 10, 1); r('#f2b45a', 5, 0, 3, 2); r('#ef9a8a', 9, 0, 3, 2); r('#8a6a4a', 2, 3, 12, 1); }
    if (tx === 2) { for (let i = 0; i < 3; i++) { r('#f3ead8', 3 + i * 4, 0, 3, 3); r('#d8d0c0', 3 + i * 4, 2, 3, 1); } }
    if (tx === 3) { r('#f3ead8', 3, 0, 3, 3); r('#f3ead8', 9, 1, 3, 2); r('#5fae78', 12, -2, 2, 3); }
    if (tx === 4) { r('#f2b45a', 6, 0, 4, 2); r('#c08a2a', 7, -1, 2, 1); r('#e8e4dc', 2, -1, 3, 4); }
  }

  function rain(ctx, clock, still) {
    for (const tx of WINDOWS) {
      const x = tx * T + 3;
      for (let i = 0; i < 9; i++) {
        const off = still ? (i * 7) % 20 : ((clock * 26 + i * 7 + tx * 3) % 20);
        px(ctx, 'rgba(140,190,240,.75)', x + 1 + i * 3, 6 + off, 1, 2);
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

  // The café dog (Bơ): a small corgi-ish pixel dog. d: { x, y, dir, moving, walkMs, sitting, petted }.
  function dogBed(ctx) {
    const x = W.DOG_BED[0] * T, y = W.DOG_BED[1] * T;
    px(ctx, '#3a4a6a', x + 1, y + 7, 14, 7); px(ctx, '#6a8ab0', x + 2, y + 6, 12, 7); px(ctx, '#8aa8c8', x + 4, y + 8, 8, 3);
  }
  function dog(ctx, d, clock, still) {
    const flip = d.dir === 'left';
    const bob = d.moving && !still ? Math.floor(d.walkMs / 120) % 2 : 0;
    const p = (dx, dy, w, h, c) => px(ctx, c, flip ? d.x - dx - w : d.x + dx, d.y + dy - (d.hop || 0), w, h);
    const fur = '#d9954f', dark = '#a86a30', cream = '#f3ead8';
    ctx.fillStyle = 'rgba(0,0,0,.22)'; ctx.fillRect(Math.round(d.x - 6), Math.round(d.y - 1), 13, 2);
    const wag = still ? 0 : Math.round(Math.sin(clock * (d.petted ? 18 : 6)) * (d.petted ? 2 : 1));
    if (d.sitting) {
      p(-5, -7, 8, 5, fur); p(-3, -3, 5, 2, cream); p(-4, -2, 2, 2, fur); p(1, -2, 2, 2, fur);
      p(1, -11, 6, 5, fur); p(5, -9, 2, 2, cream); p(6, -9, 1, 1, '#1d1b26'); p(3, -10, 1, 1, '#1d1b26'); p(1, -13, 2, 2, dark); p(5, -13, 2, 2, dark);
      p(-7, -6 + wag, 2, 2, dark);
      return;
    }
    p(-6, -7 - bob, 11, 4, fur); p(-4, -4 - bob, 7, 1, cream);
    p(3, -11 - bob, 5, 5, fur); p(7, -8 - bob, 2, 2, cream); p(8, -8 - bob, 1, 1, '#1d1b26'); p(5, -10 - bob, 1, 1, '#1d1b26'); p(3, -13 - bob, 2, 2, dark); p(6, -13 - bob, 2, 2, dark);
    p(-8, -9 - bob + wag, 2, 2, dark);
    const step = d.moving && !still ? Math.floor(d.walkMs / 120) % 2 : 0;
    p(-5, -3, 1, 3 - step, fur); p(-2, -3, 1, 2 + step, fur); p(1, -3, 1, 3 - step, fur); p(3, -3, 1, 2 + step, fur);
  }

  // Warm light pools over the tables, in soft steps.
  function lamps(ctx, strength) {
    const a = strength || 0.07;
    for (const t of W.TABLES) {
      const cx = t.tx * T + 8, cy = t.ty * T + 8;
      for (const [rx, ry] of [[22, 14], [16, 10], [10, 7]]) { ctx.fillStyle = 'rgba(255,200,120,' + a + ')'; ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2); ctx.fill(); }
    }
  }
  // Pendant lamps hang over each table; drawn after people.
  function pendants(ctx) {
    for (const t of W.TABLES) {
      const x = t.tx * T + 8, y = t.ty * T - 8;
      px(ctx, '#1d1b26', x, y - 14, 1, 13);
      px(ctx, '#2f4a3a', x - 2, y - 2, 5, 1); px(ctx, '#3f6b55', x - 3, y - 1, 7, 2); px(ctx, '#2a3f32', x - 3, y + 1, 7, 1);
      px(ctx, '#ffe8a8', x - 1, y + 2, 3, 1);
    }
  }
  // Glow from the fairy lights and the bulbs; stronger at night.
  function glow(ctx, night) {
    const a = night ? 0.22 : 0.08;
    ctx.fillStyle = 'rgba(255,214,140,' + a + ')';
    for (let x = 3; x < VW; x += 6) { const yy = 2 + Math.round(Math.abs(Math.sin(x / 48 * Math.PI)) * 4); ctx.fillRect(x - 1, yy, 3, 4); }
    for (const t of W.TABLES) ctx.fillRect(t.tx * T + 5, t.ty * T - 5, 7, 3);
    if (night) { ctx.fillStyle = 'rgba(159,232,192,.12)'; ctx.fillRect(12 * T + 1, 3, 23, 20); }
  }
  // Soft dark corners to pull the eye to the room.
  function vignette(ctx, strength) {
    const gr = ctx.createRadialGradient(VW / 2, VH / 2, VH * 0.35, VW / 2, VH / 2, VW * 0.65);
    gr.addColorStop(0, 'rgba(12,8,24,0)'); gr.addColorStop(1, 'rgba(12,8,24,' + (strength || 0.35) + ')');
    ctx.fillStyle = gr; ctx.fillRect(0, 0, VW, VH);
  }

  // Drawn after the host so the counter hides her legs.
  function counterFront(ctx) { for (let tx = 0; tx < 5; tx++) counterTop(ctx, tx * T, 2 * T); }

  // What someone brings: a bag and maybe a folded umbrella while standing; next to the chair while seated.
  function gearStanding(ctx, g, x, y, dir) {
    const c = g.color, d = shadeOf(c, 0.65), side = dir === 'left' || dir === 'right';
    if (g.bag === 'balo') {
      if (dir === 'up') { px(ctx, d, x + 3, y + 9, 8, 6); px(ctx, c, x + 4, y + 9, 6, 5); px(ctx, d, x + 4, y + 11, 6, 1); px(ctx, '#f3ead8', x + 7, y + 12, 1, 1); }
      else if (dir === 'down') { px(ctx, d, x + 3, y + 10, 1, 3); px(ctx, d, x + 10, y + 10, 1, 3); }
      else { const bx = dir === 'right' ? x + 1 : x + 10; px(ctx, d, bx, y + 9, 3, 6); px(ctx, c, bx + (dir === 'right' ? 0 : 1), y + 10, 2, 4); }
    } else if (g.bag === 'tuivai') {
      const bx = dir === 'down' ? x + 10 : dir === 'up' ? x + 0 : dir === 'right' ? x + 6 : x + 5;
      px(ctx, d, bx + 1, y + 9, 1, 3); px(ctx, d, bx, y + 12, 4, 5); px(ctx, c, bx + 1, y + 12, 2, 4); if (!side) px(ctx, '#f3ead8', bx + 1, y + 14, 2, 1);
    } else if (g.bag === 'tuicheo') {
      if (!side) { for (let i = 0; i < 6; i++) px(ctx, d, dir === 'down' ? x + 4 + i : x + 9 - i, y + 9 + Math.floor(i * 0.6), 1, 1); }
      const bx = dir === 'down' ? x + 9 : dir === 'up' ? x + 2 : dir === 'right' ? x + 7 : x + 4;
      px(ctx, d, bx, y + 12, 3, 3); px(ctx, c, bx, y + 12, 3, 1);
    }
    if (g.umbrella) {
      const ux = dir === 'down' || dir === 'right' ? x + 12 : x + 0;
      px(ctx, '#2a1f3d', ux, y + 9, 2, 1); px(ctx, '#2a1f3d', ux + (ux > x ? 1 : 0), y + 10, 1, 1);
      px(ctx, g.ucolor, ux, y + 11, 2, 5); px(ctx, shadeOf(g.ucolor, 0.7), ux + 1, y + 12, 1, 3); px(ctx, '#c0c0c8', ux, y + 16, 1, 1);
    }
  }
  function gearSeated(ctx, g, b, left) {
    const bx = left ? b.x - 11 : b.x + 6, by = b.y - 5, c = g.color, d = shadeOf(c, 0.65);
    if (g.bag === 'balo') { px(ctx, d, bx, by - 1, 5, 6); px(ctx, c, bx + 1, by, 3, 3); px(ctx, d, bx + 1, by + 2, 3, 1); }
    else if (g.bag === 'tuivai') { px(ctx, d, bx + 1, by - 2, 3, 1); px(ctx, d, bx, by, 5, 5); px(ctx, c, bx + 1, by + 1, 3, 3); }
    else if (g.bag === 'tuicheo') { px(ctx, d, bx + 1, by + 2, 4, 3); px(ctx, c, bx + 1, by + 2, 4, 1); }
    if (g.umbrella) { const ux = left ? b.x - 13 : b.x + 12; for (let i = 0; i < 8; i++) px(ctx, i < 6 ? g.ucolor : '#2a1f3d', ux + (left ? -Math.floor(i / 3) : Math.floor(i / 3)), by + 5 - i * 1.5, 2, 2); }
  }
  function headphones(ctx, g, x, y, dir) {
    px(ctx, '#2a2a34', x + 3, y + 1, 8, 1);
    if (dir === 'down' || dir === 'up') { px(ctx, g.color, x + 2, y + 4, 2, 3); px(ctx, g.color, x + 10, y + 4, 2, 3); }
    else px(ctx, g.color, dir === 'right' ? x + 5 : x + 7, y + 4, 2, 3);
  }

  // The thing someone took out on the table, on their half. left = they sit on the left of the table.
  function tableThing(ctx, t, left, thing, clock, still) {
    const x0 = t.tx * T + (left ? 1 : 9), y0 = t.ty * T, tick = still ? 0 : Math.floor(clock * 4) % 2;
    const p = (c, a, b, w, h) => px(ctx, c, x0 + a, y0 + b, w, h);
    if (thing === 'laptop') {
      p('#9aa0aa', 0, 8, 6, 2); p('#c0c4cc', 0, 8, 6, 1);
      const lx = left ? 5 : 0; p('#c0c4cc', lx, 3, 1, 6); p('#bfe3ff', left ? 4 : 1, 4, 1, 4);
      p('#2a2a34', 1 + tick * 2, 9, 1, 1);
    } else if (thing === 'sach') {
      p('#f3ead8', 0, 7, 3, 3); p('#e8dcc4', 3, 7, 3, 3); p('#8a6a4a', 3, 7, 0 + 1, 3); p('#b8b0a0', 1, 8, 1, 1); p('#b8b0a0', 4, 8, 1, 1); p('#c0605a', 0, 10, 6, 1);
    } else if (thing === 'sove') {
      p('#f3ead8', 0, 6, 5, 4); p('#6aa7e8', 1, 7, 2, 1); p('#ef8a7a', 2, 8, 2, 1); p('#e3b23c', 5 - tick, 7 + tick, 1, 3);
    } else if (thing === 'tainghe') {
      p('#1d1b26', 2, 7, 3, 4); p('#6aa7e8', 3, 8, 1, 2);
    } else if (thing === 'len') {
      p('#ef9a8a', 1, 7, 3, 3); p('#c0605a', 2, 8, 1, 1); p('#c0c0c8', 3 + tick, 6, 1, 4); p('#c0c0c8', 5 - tick, 6, 1, 4); p('#ef9a8a', 4, 9, 2, 1);
    } else if (thing === 'mayanh') {
      p('#2a2a34', 1, 7, 5, 3); p('#8a8a96', 3, 8, 2, 2); p('#c0c0c8', 1, 6, 1, 1); p('#a0724a', 0, 10, 6, 1);
    }
  }

  // A person: walk frames, blinking, what they are doing, and the small prop for it.
  // b.sit draws them seated (legs hidden behind the chair).
  function person(ctx, b, clock, still, hop) {
    let frame = b.moving ? E.walkFrame(b.walkMs) : 'stand';
    const blink = b.act === 'ngugat' || ((clock + (b.blinkAt || 0)) % 3.6) < 0.12 ? 1 : 0;
    let dir = b.dir, dx = 0, dy = 0;
    if (b.act === 'nhay' && !still) { dy = -Math.abs(Math.sin(clock * 9)) * 3; dir = Math.floor(clock * 3) % 2 ? 'left' : 'right'; frame = Math.floor(clock * 6) % 2 ? 'a' : 'b'; }
    if (b.act === 'mathe' && !still) dx = Math.floor(clock * 10) % 2 ? 1 : -1;
    if (b.act === 'ngugat' || b.act === 'chaptay' || b.act === 'vuotcho') dy = 1;
    if (b.lie) {
      // lying on a bean bag, head to the left, a book held up
      const lx = Math.round(b.x), ly = Math.round(b.y - 5);
      ctx.save(); ctx.translate(lx, ly); ctx.rotate(-Math.PI / 2); E.drawSprite(ctx, b.sheet['down:stand:' + blink], -7, -9); ctx.restore();
      if (!blink || b.act !== 'ngugat') { px(ctx, '#ef8a7a', lx - 6, ly - 10, 5, 3); px(ctx, '#f3ead8', lx - 4, ly - 10, 1, 3); }
      return;
    }
    const spr = b.sheet[dir + ':' + frame + ':' + blink] || b.sheet['down:stand:0'];
    const x = Math.round(b.x - 7 + dx), y = Math.round(b.y - 17 + dy - (hop || 0) + (b.sit ? 3 : 0));
    if (!b.host) { ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(Math.round(b.x - 5), Math.round(b.y - 1), 10, 2); }
    const left = dir === 'right';
    if (b.sit && b.seatKind === 'window') {
      // on the window bench, facing the rain: the bench front hides the legs
      ctx.save(); ctx.beginPath(); ctx.rect(x - 2, y - 2, 18, 13); ctx.clip(); E.drawSprite(ctx, spr, x, y); ctx.restore();
      px(ctx, '#a9616a', b.x - 8, b.y - 6, 16, 2); px(ctx, '#5a3a26', b.x - 8, b.y - 4, 16, 3);
    } else if (b.sit) {
      if (b.gear) gearSeated(ctx, b.gear, b, left);
      ctx.save(); ctx.beginPath(); ctx.rect(x - 2, y - 2, 18, 15); ctx.clip();
      E.drawSprite(ctx, spr, x, y); ctx.restore();
      chair(ctx, Math.round(b.x - 8), Math.round(b.y - 12), left, false);
      px(ctx, '#9a6a3a', left ? b.x - 6 : b.x + 4, b.y - 11, 2, 10); px(ctx, '#c8965a', left ? b.x - 6 : b.x + 4, b.y - 10, 2, 1);
      if (b.task && b.gear && b.gear.thing === 'laptop') { ctx.fillStyle = 'rgba(170,215,255,.28)'; ctx.fillRect(x + (left ? 8 : 2), y + 3, 5, 6); }
    } else {
      E.drawSprite(ctx, spr, x, y);
      if (b.gear) gearStanding(ctx, b.gear, x, y, dir);
    }
    if (b.gear && b.task && b.gear.thing === 'tainghe') headphones(ctx, b.gear, x, y, dir);
    const wave = Math.floor(clock * 6) % 2;
    if (b.act === 'vaytay') px(ctx, '#f2c9a0', x + (dir === 'left' ? -1 : 13), y + 7 - (still ? 0 : wave * 2), 2, 2);
    if (b.act === 'chaptay') { px(ctx, '#f2c9a0', x + 6, y + 10, 2, 3); }
    if (b.act === 'docsach' && dir === 'down') { px(ctx, '#ef8a7a', x + 4, y + 11, 6, 4); px(ctx, '#f3ead8', x + 6, y + 11, 2, 4); }
    if (b.act === 'tuoicay') px(ctx, '#7fa8c8', x + (dir === 'left' ? -2 : 12), y + 10, 4, 3);
    if (b.act === 'goido') px(ctx, '#f3ead8', x + 11, y + 10, 3, 3);
    if (b.act === 'mathe') px(ctx, '#ef8a7a', x + 6, y + 8, 2, 1);
    if (b.act === 'uong' && dir !== 'up') {
      const cx = dir === 'left' ? x + 1 : dir === 'right' ? x + 10 : x + 9, cy = y + 7 - (still ? 0 : Math.round(Math.abs(Math.sin(clock * 2)) * 1));
      px(ctx, '#f3ead8', cx, cy, 3, 3); px(ctx, (b.drinkColor || '#a0724a'), cx, cy, 3, 1);
      if (!still) px(ctx, 'rgba(232,228,220,.7)', cx + 1, cy - 2 - (Math.floor(clock * 3) % 2), 1, 1);
    }
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
      if (p.kind === 'steam') { ctx.fillStyle = 'rgba(232,228,220,' + Math.max(0, Math.min(0.6, p.life)) + ')'; ctx.fillRect(x, y, 1, 2); }
      if (p.kind === 'spark') { px(ctx, '#ffd98a', x, y, 1, 1); px(ctx, '#ffd98a', x - 2, y + 2, 1, 1); px(ctx, '#ffd98a', x + 2, y + 1, 1, 1); }
    }
  }

  root.Room = { VW, VH, px, background, rain, cat, dog, dogBed, lamps, pendants, glow, vignette, counterFront, tableThing, person, actParticles, stepParticles, drawParticles };
})(globalThis);
