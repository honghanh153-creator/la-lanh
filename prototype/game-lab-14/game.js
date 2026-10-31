// Game lab 14: detectives (players or default NPCs), ghost records, co-op plates, notebook and dialogs.
(function () {
  'use strict';
  const C = window.Cases, E = window.Engine, T = E.TILE;
  const VW = E.W * T, VH = E.H * T;
  const $ = id => document.getElementById(id);
  const canvas = $('game'), ctx = canvas.getContext('2d');
  const reduceMQ = window.matchMedia ? matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  const coarse = window.matchMedia ? matchMedia('(pointer: coarse)').matches : false;

  // ---------- state ----------
  let progress = C.createProgress();
  let index = 0;
  let sessions = new Map();
  // Motion: 'full' | 'reduced' (no particles, shake, bounce, typewriter) | 'off' (no ambient motion at all).
  let motion = reduceMQ.matches ? 'reduced' : 'full';
  let modalOpen = false, returnFocus = null;
  let tab = 'sources';
  let busy = false; // transition or reveal in progress
  const keys = new Set();
  const particles = [];
  let time = 0, scale = 1;
  // Faces: detective id -> small canvas cropped from a photo the player picked. Memory only.
  const faces = new Map();

  const fx = () => motion === 'full';
  const quiet = () => !fx();
  const kase = () => C.cases[index];
  function session() {
    const c = kase();
    if (!sessions.has(c.id)) sessions.set(c.id, { earned: [], tallies: {}, struck: [], flipped: [], route: { who: '', path: [], wait: 0 }, solved: false, gone: '' });
    return sessions.get(c.id);
  }

  // Keyboard sets for same-screen play. Alone, the one player may use WASD or arrows.
  const CONTROLS = [
    { label: 'E', name: 'W A S D · E', up: 'w', down: 's', left: 'a', right: 'd', act: 'e' },
    { label: '↵', name: 'Mũi tên · Enter', up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight', act: 'Enter' },
    { label: 'O', name: 'I J K L · O', up: 'i', down: 'k', left: 'j', right: 'l', act: 'o' },
    { label: 'Y', name: 'T F G H · Y', up: 't', down: 'g', left: 'f', right: 'h', act: 'y' }
  ];
  // team: which detective each human slot plays. Unclaimed detectives run as default NPCs.
  let team = ['hanh'];
  let active = 0; // slot that touch / mouse controls

  // ---------- sprites ----------
  const sheets = {};
  function toCanvas(spr) {
    const cv = document.createElement('canvas');
    cv.width = spr.w; cv.height = spr.h;
    E.drawSprite(cv.getContext('2d'), spr, 0, 0);
    return cv;
  }
  for (const [name, look] of Object.entries(E.LOOKS)) {
    const sheet = E.buildSheet(look);
    sheets[name] = {};
    for (const [k, spr] of Object.entries(sheet)) sheets[name][k] = { cv: toCanvas(spr), spr };
  }

  // ---------- entities ----------
  const feet = (tx, ty) => ({ x: tx * T + 4, y: ty * T + 9, w: 8, h: 5 });
  const dets = C.detectives.map((d, i) => ({ kind: 'det', id: d.id, look: d.id, home: E.DETECTIVE_HOME[i], ...feet(...E.DETECTIVE_HOME[i]), vx: 0, vy: 0, dir: 'up', walkMs: 0, moving: false, path: null, then: null, task: null, nextThink: 1800 + i * 900, blinkAt: 1500 + i * 700, blinkTill: 0, dustAt: 0, hop: 0, stuckMs: 0 }));
  const ghosts = C.profiles.map((p, i) => ({ kind: 'ghost', id: p.id, look: p.id, ...feet(...E.NPC_HOME[i]), dir: 'down', walkMs: 0, moving: false, blinkAt: 2000 + i * 600, blinkTill: 0, hop: 0, glitch: 0, hidden: false, phase: i * 1.1 }));
  const slotOf = d => team.indexOf(d.id);
  const humans = () => dets.filter(d => slotOf(d) >= 0);
  const lead = () => dets.find(d => d.id === team[active]) || dets.find(d => d.id === team[0]);
  const detById = id => dets.find(d => d.id === id);
  const tileOf = b => [Math.floor((b.x + b.w / 2) / T), Math.floor((b.y + b.h / 2) / T)];
  const centerOf = b => ({ x: b.x + b.w / 2, y: b.y + b.h / 2 });
  const facing = (from, to) => { const a = centerOf(from), b = centerOf(to); const dx = b.x - a.x, dy = b.y - a.y; return Math.abs(dx) > Math.abs(dy) ? (dx < 0 ? 'left' : 'right') : (dy < 0 ? 'up' : 'down'); };
  // Detectives pass through each other and through holograms, so nobody gets stuck in couch co-op.
  const noBlock = () => false;

  // ---------- room background (drawn once) ----------
  const bg = document.createElement('canvas'); bg.width = VW; bg.height = VH;
  function drawRoom() {
    const g = bg.getContext('2d');
    const r = (c, x, y, w, h) => { g.fillStyle = c; g.fillRect(x, y, w, h); };
    // floor planks
    for (let ty = 2; ty < E.H - 1; ty++) for (let tx = 0; tx < E.W; tx++) {
      const x = tx * T, y = ty * T;
      r((tx + ty) % 2 ? '#7a5638' : '#83603f', x, y, T, T);
      r('#6a4a30', x, y + 7, T, 1); r('#6a4a30', x, y + 15, T, 1);
      r('#8d6a48', x + ((ty * 5) % 12), y + 2, 3, 1);
    }
    // walls
    r('#4b3f66', 0, 0, VW, 2 * T); r('#3b3152', 0, 2 * T - 4, VW, 4); r('#5a4d78', 0, 0, VW, 3);
    // window (left)
    r('#2a2140', 6, 6, 44, 20); r('#7fb7d9', 8, 8, 40, 16); r('#a8d4ea', 8, 8, 40, 6); r('#2a2140', 27, 8, 2, 16); r('#e8f3f8', 12, 11, 6, 2); r('#e8f3f8', 36, 10, 8, 2);
    // clock
    r('#2a2140', 58, 7, 12, 12); r('#efe3c8', 59, 8, 10, 10); r('#2a2140', 64, 9, 1, 5); r('#2a2140', 64, 13, 3, 1);
    // map poster on wall (spot 6,1)
    r('#2a2140', 6 * T - 1, 1 * T - 3, 18, 15); r('#efe3c8', 6 * T, 1 * T - 2, 16, 13);
    g.fillStyle = '#3b2b55'; [[2, 5], [6, 5], [10, 5], [14, 5]].forEach(([x, y]) => g.fillRect(6 * T + x - 1, T - 2 + y - 1, 3, 3));
    g.fillRect(6 * T + 2, T + 3, 12, 1); g.fillStyle = '#ef8a7a'; g.fillRect(6 * T + 6, T + 7, 6, 1);
    // chalkboard with tally marks: five strokes, not-equal, six strokes
    r('#2a2140', 114, 4, 54, 24); r('#2f5a46', 116, 6, 50, 20); r('#b9895a', 114, 27, 54, 2);
    g.fillStyle = '#e8efe6';
    for (let i = 0; i < 4; i++) g.fillRect(121 + i * 3, 10, 1, 10); g.fillRect(119, 15, 13, 1);
    g.fillRect(136, 13, 6, 1); g.fillRect(136, 16, 6, 1); g.fillRect(140, 11, 1, 1); g.fillRect(138, 18, 1, 1);
    for (let i = 0; i < 4; i++) g.fillRect(148 + i * 3, 10, 1, 10); g.fillRect(146, 15, 13, 1); g.fillRect(162, 10, 1, 10);
    // exit door with green sign (door spot at tile 11,1)
    r('#2a2140', 174, 6, 20, 26); r('#8a5a3a', 176, 8, 16, 24); r('#d8b25a', 188, 20, 2, 2); r('#3fb07a', 176, 2, 16, 4); r('#e8f3f8', 180, 3, 8, 2);
    // sunlight from the window and a rug, for warmth
    g.globalAlpha = 0.12; g.fillStyle = '#ffe9b0';
    for (let i = 0; i < 46; i++) g.fillRect(4 + i * 0.6, 2 * T + i, 40, 1);
    g.globalAlpha = 1;
    r('#2a2140', 5 * T + 3, 7 * T + 3, 5 * T - 6, T + 10); r('#7a3d4f', 5 * T + 4, 7 * T + 4, 5 * T - 8, T + 8); r('#a85a6a', 5 * T + 7, 7 * T + 7, 5 * T - 14, T + 2);
    // bottom wall
    r('#3b3152', 0, (E.H - 1) * T, VW, T); r('#4b3f66', 0, (E.H - 1) * T, VW, 3);
    // furniture
    for (let ty = 0; ty < E.H; ty++) for (let tx = 0; tx < E.W; tx++) {
      const t = E.tileAt(tx, ty), x = tx * T, y = ty * T;
      if (t === 'D') {
        const left = E.tileAt(tx - 1, ty) !== 'D';
        r('#2a2140', x, y + 3, T, 12); r('#b07a48', x, y + 3, T, 9); r('#c48c56', x, y + 3, T, 3); r('#7a5032', x, y + 12, T, 2);
        if (left) { r('#2a2140', x + 1, y + 14, 2, 2); r('#efe3c8', x + 4, y + 5, 6, 4); r('#3b2b55', x + 5, y + 6, 4, 1); }
        else { r('#2a2140', x + 13, y + 14, 2, 2); r('#7fc8a0', x + 3, y + 5, 3, 5); r('#f2b45a', x + 8, y + 6, 5, 2); }
      } else if (t === 'T') {
        r('#2a2140', x, y + 2, T, 13); r('#8d5f3c', x, y + 2, T, 10); r('#a46f46', x, y + 2, T, 3); r('#6a4428', x, y + 12, T, 3);
        if (tx === 3) { r('#efe3c8', x + 3, y + 4, 9, 6); r('#d9c9a8', x + 4, y + 5, 9, 6); r('#f0c94a', x + 5, y + 6, 5, 4); }
      } else if (t === 'K') {
        r('#2a2140', x, y - 6, T, 22); r('#6a4428', x + 1, y - 5, 14, 20);
        const cols = ['#ef8a7a', '#7fc8a0', '#f2b45a', '#6aa7e8', '#a995d8'];
        for (let i = 0; i < 4; i++) r(cols[(i + ty) % 5], x + 2 + i * 3, y - 3, 2, 6), r(cols[(i + ty + 2) % 5], x + 2 + i * 3, y + 5, 2, 6);
      } else if (t === 'm') {
        r('#2a2140', x + 1, y - 4, 14, 19); r('#5a5f6e', x + 2, y - 3, 12, 17); r('#16302a', x + 3, y - 1, 10, 7); r('#7fc8a0', x + 6, y + 1, 3, 3);
        r('#f2b45a', x + 4, y + 9, 2, 2); r('#ef8a7a', x + 8, y + 9, 2, 2);
      } else if (t === 's') {
        r('#2a2140', x + 3, y - 2, 10, 17); r('#3d4250', x + 4, y - 1, 8, 15); r('#6aa7e8', x + 5, y + 1, 6, 3); r('#c9cfd8', x + 6, y + 7, 4, 1);
      } else if (t === 'c') {
        r('#2a2140', x + 6, y + 6, 1, 9); r('#2a2140', x + 3, y + 13, 3, 2); r('#2a2140', x + 9, y + 13, 3, 2); r('#2a2140', x + 7, y + 7, 1, 8);
        r('#2a2140', x + 2, y, 12, 8); r('#4d4f5c', x + 3, y + 1, 10, 6); r('#1d1b26', x + 6, y + 2, 4, 4); r('#6aa7e8', x + 7, y + 3, 2, 2);
      } else if (t === 'M') {
        r('#2a2140', x + 1, y - 10, 14, 25); r('#6b6f80', x + 2, y - 9, 12, 23); r('#9fb4c7', x + 4, y - 7, 8, 12); r('#d6e4ef', x + 5, y - 6, 2, 8);
      } else if (t === 'p') {
        r('#2a2140', x + 4, y + 9, 8, 6); r('#b0603c', x + 5, y + 10, 6, 5); r('#3f8a5a', x + 3, y + 1, 10, 9); r('#5fae78', x + 5, y + 2, 4, 4);
      }
    }
    // tarot deck on desk (spot 10,4)
    r('#2a2140', 10 * T + 9, 4 * T + 3, 6, 8); r('#3a2f55', 10 * T + 10, 4 * T + 4, 4, 6); r('#f2b45a', 10 * T + 11, 4 * T + 6, 2, 2);
  }
  drawRoom();

  // ---------- canvas sizing: integer device-pixel scale ----------
  function fit() {
    const stage = $('stage');
    const dpr = window.devicePixelRatio || 1;
    const w = stage.clientWidth, h = stage.clientHeight;
    // Prefer whole device-pixel multiples (crisp, even pixels). If that leaves the room much smaller
    // than the stage (e.g. 360 px wide at 2x), stretch with image-rendering: pixelated instead.
    const fitScale = Math.min(w / VW, h / VH);
    let k = Math.max(1, Math.floor(fitScale * dpr));
    scale = k / dpr;
    if (scale < fitScale * 0.85) { k = Math.ceil(fitScale * dpr); scale = fitScale; }
    canvas.width = VW * k; canvas.height = VH * k;
    canvas.style.width = Math.floor(VW * scale) + 'px'; canvas.style.height = Math.floor(VH * scale) + 'px';
    ctx.setTransform(k, 0, 0, k, 0, 0);
    ctx.imageSmoothingEnabled = false;
  }
  window.addEventListener('resize', fit);

  // ---------- interaction targets ----------
  function plateHeld() {
    const p = kase().plate;
    return !!p && dets.some(d => { const [x, y] = tileOf(d); return x === p.at[0] && y === p.at[1]; });
  }
  function plateNeeded() {
    const c = kase(), s = session();
    return !!c.plate && !s.earned.includes(c.sources.find(k => E.SOURCE_SPOT[k] === c.plate.spot));
  }
  function targets(self) {
    const c = kase(), s = session(), list = [];
    for (const [name, sp] of Object.entries(E.SPOTS)) {
      const src = c.sources.find(k => E.SOURCE_SPOT[k] === name);
      list.push({ kind: 'spot', name, tx: sp.tx, ty: sp.ty, label: sp.label, src, earned: src ? s.earned.includes(src) : false, relevant: !!src || name === 'terminal' || name === 'tarot' });
    }
    for (const g of ghosts) if (!g.hidden) { const [tx, ty] = tileOf(g); list.push({ kind: 'ghost', ghost: g, tx, ty, label: 'Hồ sơ ' + C.nameOf(g.id), relevant: true }); }
    for (const d of dets) if (d !== self) { const [tx, ty] = tileOf(d); list.push({ kind: 'det', det: d, tx, ty, label: C.detectives.find(x => x.id === d.id).name, relevant: true }); }
    return list;
  }
  function nearest(self) {
    if (!self) return null;
    const p = centerOf(self);
    let best = null, bd = 20;
    for (const t of targets(self)) {
      const cx = t.kind === 'spot' ? t.tx * T + 8 : centerOf(t.ghost || t.det).x;
      const cy = t.kind === 'spot' ? t.ty * T + 10 : centerOf(t.ghost || t.det).y;
      const d = Math.hypot(cx - p.x, cy - p.y) + (t.kind === 'ghost' ? 4 : 0);
      if (d < bd) { bd = d; best = t; }
    }
    return best;
  }
  function nextGoal() {
    const c = kase(), s = session();
    const missing = c.sources.find(k => !s.earned.includes(k));
    if (missing) {
      const spotName = E.SOURCE_SPOT[missing];
      if (c.plate && c.plate.spot === spotName && !plateHeld()) return { tx: c.plate.at[0], ty: c.plate.at[1] + 1, plate: true };
      return E.SPOTS[spotName];
    }
    return s.solved ? null : E.SPOTS.terminal;
  }

  // ---------- update ----------
  function inputFor(d) {
    const slot = slotOf(d);
    if (slot < 0 || modalOpen || busy) return [0, 0];
    const sets = team.length === 1 ? [CONTROLS[0], CONTROLS[1]] : [CONTROLS[slot]];
    let ix = 0, iy = 0;
    for (const k of sets) {
      if (keys.has(k.left)) ix -= 1;
      if (keys.has(k.right)) ix += 1;
      if (keys.has(k.up)) iy -= 1;
      if (keys.has(k.down)) iy += 1;
    }
    return [Math.sign(ix), Math.sign(iy)];
  }

  function updateDet(d, dt) {
    let [ix, iy] = inputFor(d);
    if (ix || iy) { d.path = null; d.then = null; }
    const human = slotOf(d) >= 0;
    if (!human && !d.path && !d.task) idleThink(d);
    if (!ix && !iy && d.path && d.path.length && !modalOpen && !busy) {
      const [tx, ty] = d.path[0];
      const goal = feet(tx, ty);
      const dx = goal.x - d.x, dy = goal.y - d.y;
      if (Math.abs(dx) < 1.2 && Math.abs(dy) < 1.2) {
        d.x = goal.x; d.y = goal.y; d.path.shift();
        if (!d.path.length) { d.path = null; const then = d.then; d.then = null; if (then) then(); }
      } else { ix = Math.abs(dx) >= 1.2 ? Math.sign(dx) : 0; iy = ix ? 0 : Math.sign(dy); }
    }
    const len = Math.hypot(ix, iy) || 1;
    const speed = human || d.task ? 1 : 0.45; // idle NPCs amble
    d.vx = E.stepVelocity(d.vx, ix / len * speed, dt);
    d.vy = E.stepVelocity(d.vy, iy / len * speed, dt);
    const moved = E.moveWithSlide(d, d.vx * dt, d.vy * dt, []);
    const travelled = Math.hypot(moved.x - d.x, moved.y - d.y);
    d.x = moved.x; d.y = moved.y;
    d.moving = travelled > 0.05;
    if (ix || iy) d.dir = Math.abs(ix) > Math.abs(iy) ? (ix < 0 ? 'left' : 'right') : (iy < 0 ? 'up' : 'down');
    if (d.moving) {
      d.walkMs += dt * 1000;
      if (fx() && time > d.dustAt) { d.dustAt = time + 260; puff(d.x + d.w / 2, d.y + d.h); }
    } else d.walkMs = 0;
    if (d.path && d.path.length && travelled < 0.01) d.stuckMs += dt * 1000; else d.stuckMs = 0;
    if (d.stuckMs > 150) {
      d.stuckMs = 0;
      const here = tileOf(d), last = d.path[d.path.length - 1];
      const p = E.findPath(here, last, noBlock);
      if (p) { Object.assign(d, feet(...here)); d.path = p.slice(1); } else { d.path = null; d.then = null; }
    }
  }

  // Default NPC detectives potter around their home tile and look at whoever comes close.
  function idleThink(d) {
    if (motion === 'off' || time < d.nextThink) return;
    d.nextThink = time + 2600 + Math.random() * 3600;
    const near = humans().find(h => Math.hypot(centerOf(h).x - centerOf(d).x, centerOf(h).y - centerOf(d).y) < 40);
    if (near) { d.dir = facing(d, near); return; }
    const [hx, hy] = d.home, [cx, cy] = tileOf(d);
    if (cx !== hx || cy !== hy) { const p = E.findPath([cx, cy], [hx, hy], noBlock); if (p) d.path = p.slice(1); return; }
    if (fx() && Math.random() < 0.4) {
      const opts = [[hx + 1, hy], [hx - 1, hy], [hx, hy - 1]].filter(([x, y]) => !E.solidTile(x, y));
      if (opts.length) d.path = [opts[Math.floor(Math.random() * opts.length)]];
    } else d.dir = E.DIRS[Math.floor(Math.random() * 4)];
  }

  function blink(e) {
    if (motion === 'off') return false;
    if (time > e.blinkAt) { e.blinkTill = time + 130; e.blinkAt = time + 3000 + Math.random() * 2000; }
    return time < e.blinkTill;
  }

  // ---------- NPC tasks: fetch a source or hold the plate ----------
  function sendTo(d, tile, then) {
    const from = tileOf(d);
    const goals = E.solidTile(tile[0], tile[1]) ? E.standTiles(tile[0], tile[1], from) : [tile];
    for (const g of goals) {
      const p = E.findPath(from, g, noBlock);
      if (p) {
        d.path = p.slice(1); d.then = then;
        if (!d.path.length) { d.path = null; d.then = null; if (then) then(); }
        return true;
      }
    }
    return false;
  }
  function askFetch(d, spotName) {
    const sp = E.SPOTS[spotName], who = C.detectives.find(x => x.id === d.id);
    d.task = { type: 'fetch', spot: spotName };
    sendTo(d, [sp.tx, sp.ty], () => {
      d.dir = facing(d, { x: sp.tx * T + 4, y: sp.ty * T + 9, w: 8, h: 5 });
      const c = kase();
      if (c.plate && c.plate.spot === spotName && !plateHeld()) { d.task = null; toast(who.name + ': khoá rồi, cần một người đứng giữ công tắc.'); return; }
      d.task = null;
      const src = c.sources.find(k => E.SOURCE_SPOT[k] === spotName);
      const run = () => (spotName === 'tarot' ? tarot(who) : src ? examine(src, who) : null);
      if (modalOpen) pending.push(run); else run();
    });
    toast(who.name + ': ' + who.help);
  }
  function askHold(d) {
    const c = kase(), who = C.detectives.find(x => x.id === d.id);
    d.task = { type: 'hold' };
    sendTo(d, c.plate.at, () => { d.dir = 'down'; });
    toast(who.name + ': ' + who.hold);
  }
  const pending = [];
  function releaseHolders() { for (const d of dets) if (d.task && d.task.type === 'hold' && !plateNeeded()) { d.task = null; d.nextThink = time + 800; } }

  // ---------- particles (no flashing; all fade over >= 400 ms) ----------
  function puff(x, y) { for (let i = 0; i < 2; i++) particles.push({ x: x + (i ? 2 : -2), y, vx: (i ? 6 : -6), vy: -4, life: 420, max: 420, c: '#c9b79a', s: 1 }); }
  function sparkle(x, y) { if (quiet()) return; for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; particles.push({ x, y, vx: Math.cos(a) * 30, vy: Math.sin(a) * 30 - 10, life: 600, max: 600, c: i % 2 ? '#f2b45a' : '#fff1c7', s: 1 }); } }
  function leaves(n) {
    const spr = sheets[n.look]['down:stand:0'].spr;
    const ox = n.x + n.w / 2 - spr.w / 2, oy = n.y + n.h - spr.h;
    for (const [px, py, col] of spr.px) if ((px + py) % 2 === 0) particles.push({ x: ox + px, y: oy + py, vx: (Math.random() - 0.5) * 16, vy: -8 - Math.random() * 14, life: 900 + Math.random() * 500, max: 1400, c: Math.random() < 0.5 ? '#7fc8a0' : col, s: 1, leaf: true });
  }
  function updateParticles(dt) {
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.life -= dt * 1000; if (p.life <= 0) { particles.splice(i, 1); continue; }
      p.x += p.vx * dt; p.y += p.vy * dt;
      if (p.leaf) { p.vy += 10 * dt; p.vx += Math.sin((time + i * 50) / 180) * 4 * dt; } else p.vy += 20 * dt;
    }
  }

  // ---------- render ----------
  function spriteFor(e) {
    const frame = e.moving ? E.walkFrame(e.walkMs) : 'stand';
    const key = e.dir + ':' + frame + ':' + (blink(e) ? 1 : 0);
    const s = sheets[e.look] && sheets[e.look][key];
    if (!s && !spriteFor.warned) { spriteFor.warned = true; console.warn('sprite key missing', e.look, key, e.walkMs); }
    return s || sheets[e.look]['down:stand:0'];
  }
  function drawEntity(e) {
    const s = spriteFor(e);
    const bob = e.moving && (E.walkFrame(e.walkMs) === 'stand') ? -1 : 0;
    const hop = e.hop ? -Math.round(Math.sin((1 - e.hop / 380) * Math.PI) * 4) : 0;
    const float = e.kind === 'ghost' && fx() ? Math.round(Math.sin(time / 700 + e.phase)) : 0;
    const x = Math.round(e.x + e.w / 2 - s.spr.w / 2), y = Math.round(e.y + e.h - s.spr.h + 1 + bob + hop + float);
    const alpha = e.kind === 'ghost' ? 0.62 : 1;
    ctx.globalAlpha = (e.kind === 'ghost' ? 0.15 : 0.28); ctx.fillStyle = '#000';
    ctx.fillRect(x + 3, Math.round(e.y + e.h - 1), s.spr.w - 6, 2); ctx.fillRect(x + 4, Math.round(e.y + e.h + 1), s.spr.w - 8, 1);
    ctx.globalAlpha = alpha;
    if (e.glitch > 0) {
      for (let row = 0; row < s.spr.h; row += 3) {
        const off = ((row / 3 + Math.floor(time / 90)) % 3) - 1;
        ctx.drawImage(s.cv, 0, row, s.spr.w, 3, x + off, y + row, s.spr.w, 3);
      }
    } else ctx.drawImage(s.cv, x, y);
    ctx.globalAlpha = 1;
    if (e.kind === 'det') {
      const face = faces.get(e.id);
      if (face && e.dir !== 'up') drawFace(face, x + s.spr.w / 2, y + 4);
      const slot = slotOf(e);
      if (slot >= 0 && team.length > 1) {
        ctx.fillStyle = ['#f2b45a', '#7fc8a0', '#ef8a7a', '#6aa7e8'][slot];
        ctx.fillRect(x + s.spr.w / 2 - 1, y - 4, 3, 2); ctx.fillRect(x + s.spr.w / 2, y - 2, 1, 1);
      }
      if (e.task) {
        ctx.fillStyle = '#2a2140'; ctx.fillRect(x + s.spr.w - 3, y - 3, 7, 5);
        ctx.fillStyle = '#efe3c8'; ctx.fillRect(x + s.spr.w - 2, y - 2, 5, 3);
        ctx.fillStyle = '#2a2140'; for (let i = 0; i < 3; i++) if (e.task.type === 'hold' || Math.floor(time / 300) % 3 >= i) ctx.fillRect(x + s.spr.w - 2 + i * 2, y - 1, 1, 1);
      }
    }
  }
  // A real photo on a pixel body: drawn smooth and slightly big on purpose (bobblehead).
  function drawFace(face, cx, cy) {
    const r = 8;
    ctx.save();
    ctx.beginPath(); ctx.arc(cx, cy, r + 0.75, 0, Math.PI * 2); ctx.fillStyle = '#2a2140'; ctx.fill();
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.clip();
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(face, cx - r, cy - r, r * 2, r * 2);
    ctx.restore();
    ctx.imageSmoothingEnabled = false;
  }
  function drawPlate() {
    const p = kase().plate; if (!p) return;
    const held = plateHeld(), x = p.at[0] * T, y = p.at[1] * T;
    ctx.fillStyle = '#2a2140'; ctx.fillRect(x + 2, y + 4, 12, 9);
    ctx.fillStyle = held ? '#7fc8a0' : '#8d99a6'; ctx.fillRect(x + 3, y + 5 + (held ? 1 : 0), 10, 7 - (held ? 1 : 0));
    ctx.fillStyle = held ? '#c9f1d8' : '#c9cfd8'; ctx.fillRect(x + 4, y + 6 + (held ? 1 : 0), 8, 1);
    if (plateNeeded() && !held) {
      const a = quiet() ? 0.5 : 0.3 + 0.25 * (Math.sin(time / 450) + 1) / 2;
      ctx.globalAlpha = a; ctx.strokeStyle = '#7fc8a0'; ctx.strokeRect(x + 0.5, y + 2.5, 15, 13); ctx.globalAlpha = 1;
    }
  }
  function drawMarker(t, near, keyLabel) {
    const x = t.tx * T + 8, y = t.ty * T - (t.kind === 'spot' ? 4 : 14);
    if (t.kind === 'spot' && t.earned) { ctx.fillStyle = '#2a2140'; ctx.fillRect(x - 3, y - 4, 7, 6); ctx.fillStyle = '#7fc8a0'; ctx.fillRect(x - 2, y - 1, 1, 1); ctx.fillRect(x - 1, y, 1, 1); ctx.fillRect(x, y - 1, 1, 1); ctx.fillRect(x + 1, y - 2, 1, 1); ctx.fillRect(x + 2, y - 3, 1, 1); }
    if (!near) return;
    ctx.font = '7px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    const label = t.kind === 'spot' ? keyLabel : (keyLabel ? keyLabel + ' · ' : '') + t.label;
    const w = Math.max(9, Math.ceil(ctx.measureText(label).width) + 6);
    ctx.fillStyle = '#2a2140'; ctx.fillRect(x - w / 2 - 1, y - 13, w + 2, 10);
    ctx.fillStyle = '#efe3c8'; ctx.fillRect(x - w / 2, y - 12, w, 8);
    ctx.fillStyle = '#2a2140'; ctx.fillText(label, x, y - 7.5);
  }
  function drawGoalArrow() {
    const g = nextGoal(); if (!g) return;
    const bounce = quiet() ? 0 : Math.round(Math.sin(time / 220) * 2);
    const x = g.tx * T + 8, y = g.ty * T - 18 + bounce;
    ctx.fillStyle = '#2a2140'; ctx.fillRect(x - 4, y - 1, 9, 2); ctx.fillRect(x - 3, y + 1, 7, 2); ctx.fillRect(x - 2, y + 3, 5, 2); ctx.fillRect(x - 1, y + 5, 3, 1);
    ctx.fillStyle = g.plate ? '#7fc8a0' : '#f2b45a'; ctx.fillRect(x - 3, y, 7, 1); ctx.fillRect(x - 2, y + 1, 5, 2); ctx.fillRect(x - 1, y + 3, 3, 2);
  }
  function drawGlow(t) {
    if (t.kind !== 'spot' || !t.relevant || t.earned) return;
    const a = quiet() ? 0.35 : 0.22 + 0.18 * (Math.sin(time / 500) + 1) / 2;
    ctx.globalAlpha = a; ctx.strokeStyle = '#f2b45a'; ctx.lineWidth = 1;
    ctx.strokeRect(t.tx * T + 0.5, t.ty * T + 0.5, T - 1, T - 1);
    ctx.globalAlpha = 1;
  }
  function keyLabelFor(d) { return coarse ? '' : team.length === 1 ? 'E' : CONTROLS[slotOf(d)].label; }
  function render() {
    ctx.drawImage(bg, 0, 0);
    drawPlate();
    const ts = targets(null);
    for (const t of ts) drawGlow(t);
    const ents = ghosts.filter(n => !n.hidden).concat(dets).sort((a, b) => a.y - b.y);
    for (const e of ents) drawEntity(e);
    for (const p of particles) { ctx.globalAlpha = Math.max(0, p.life / p.max); ctx.fillStyle = p.c; ctx.fillRect(Math.round(p.x), Math.round(p.y), p.s, p.s); }
    ctx.globalAlpha = 1;
    for (const t of ts) if (t.kind === 'spot') drawMarker(t, false);
    if (!modalOpen && !busy) for (const h of humans()) { const n = nearest(h); if (n) drawMarker(n, true, keyLabelFor(h)); }
    drawGoalArrow();
  }

  // ---------- loop ----------
  let last = 0, lastNear = '';
  let held = false; // test hook: freeze the real-time loop so scripted steps are deterministic
  function frame(now) { try { if (!held) tick(now); } finally { schedule(); } }
  function tick(now) {
    const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now; time = now;
    for (const d of dets) updateDet(d, dt);
    for (const g of ghosts) if (g.hop > 0) g.hop = Math.max(0, g.hop - dt * 1000);
    for (const d of dets) if (d.hop > 0) d.hop = Math.max(0, d.hop - dt * 1000);
    updateParticles(dt);
    render();
    if (!modalOpen && pending.length) pending.shift()();
    const me = lead();
    const n = modalOpen || busy ? null : nearest(me);
    const key = n ? n.kind + n.label : '';
    if (key !== lastNear) {
      lastNear = key;
      const btnEl = $('actBtn');
      if (n) { const verb = actionVerb(me, n); btnEl.textContent = verb + ' · ' + n.label; btnEl.disabled = false; $('near').textContent = 'Gần ' + n.label + '. Nhấn ' + (team.length === 1 ? 'E' : CONTROLS[active].label) + ' để ' + verb.toLowerCase() + '.'; }
      else { btnEl.textContent = 'Lại gần đồ vật hoặc người để tương tác'; btnEl.disabled = true; $('near').textContent = ''; }
    }
  }
  // Hidden tabs get no animation frames; fall back to a slow timer so state still advances.
  function schedule() { if (document.hidden) setTimeout(() => frame(performance.now()), 50); else requestAnimationFrame(frame); }
  function actionVerb(d, t) {
    if (t.kind === 'det') return 'Nói chuyện';
    if (t.kind === 'ghost') return 'Xem hồ sơ';
    if (t.name === 'terminal') return 'Nộp lập luận';
    const owner = C.ownerOfSpot(t.name);
    return owner && owner.id !== d.id ? 'Nhờ ' + owner.name : 'Khám';
  }

  // ---------- input ----------
  const keyName = e => (e.key.length === 1 ? e.key.toLowerCase() : e.key);
  const allMoveKeys = new Set(CONTROLS.flatMap(k => [k.up, k.down, k.left, k.right]));
  document.addEventListener('keydown', e => {
    const k = keyName(e);
    if (modalOpen) {
      if (k === 'Escape') closeModal();
      if (k === 'Tab') trapFocus(e);
      return;
    }
    const typing = /INPUT|SELECT|TEXTAREA/.test(document.activeElement && document.activeElement.tagName);
    if (typing) return;
    if (allMoveKeys.has(k)) { keys.add(k); e.preventDefault(); }
    const onBody = document.activeElement === document.body || document.activeElement === canvas;
    if (onBody) {
      const slot = team.length === 1 ? ((k === 'e' || k === ' ' || k === 'Enter') ? 0 : -1) : CONTROLS.findIndex(c => c.act === k);
      if (slot >= 0 && slot < team.length) { const d = detById(team[slot]); const n = nearest(d); if (n) { e.preventDefault(); interact(d, n); } }
    }
    if (k === 'n' && team.length === 1) toggleBook();
  });
  document.addEventListener('keyup', e => keys.delete(keyName(e)));
  window.addEventListener('blur', () => keys.clear());
  $('actBtn').addEventListener('click', () => { const d = lead(); const n = nearest(d); if (n) interact(d, n); });

  canvas.addEventListener('pointerdown', e => {
    if (modalOpen || busy) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width * VW, y = (e.clientY - rect.top) / rect.height * VH;
    const tx = Math.floor(x / T), ty = Math.floor(y / T);
    const me = lead();
    const hitDet = dets.find(d => d !== me && x >= d.x - 3 && x <= d.x + d.w + 3 && y >= d.y - 14 && y <= d.y + d.h);
    const hitGhost = !hitDet && ghosts.find(g => !g.hidden && x >= g.x - 3 && x <= g.x + g.w + 3 && y >= g.y - 14 && y <= g.y + g.h);
    const spot = Object.entries(E.SPOTS).find(([, s]) => s.tx === tx && s.ty === ty);
    const all = targets(me);
    const t = hitDet ? all.find(q => q.det === hitDet) : hitGhost ? all.find(q => q.ghost === hitGhost) : spot ? all.find(q => q.name === spot[0]) : null;
    walkTo(me, t ? [t.tx, t.ty] : [tx, ty], t ? () => { const fresh = targets(me).find(q => (q.det && q.det === t.det) || (q.ghost && q.ghost === t.ghost) || (q.name && q.name === t.name)); interact(me, fresh || t); } : null);
  });

  function walkTo(d, tile, then) {
    d.task = null;
    if (!sendTo(d, tile, then)) toast('Không tới được chỗ đó.');
  }

  // ---------- UI helpers ----------
  function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined) n.textContent = text; return n; }
  function btn(text, cls, fn) { const b = el('button', cls, text); b.type = 'button'; b.addEventListener('click', fn); return b; }
  let toastT;
  function toast(text) { clearTimeout(toastT); const t = $('toast'); t.textContent = text; t.hidden = false; toastT = setTimeout(() => (t.hidden = true), 2400); }
  function openModal(kicker, title) {
    if (!modalOpen) returnFocus = document.activeElement;
    modalOpen = true; keys.clear(); for (const d of dets) if (slotOf(d) >= 0) { d.path = null; d.then = null; }
    $('mKicker').textContent = kicker; $('mTitle').textContent = title; $('mBody').replaceChildren();
    $('shade').hidden = false; setTimeout(() => $('mClose').focus(), 0);
    return $('mBody');
  }
  function closeModal() {
    if (!modalOpen) return;
    modalOpen = false; $('shade').hidden = true;
    if (returnFocus && returnFocus.isConnected && returnFocus !== document.body) returnFocus.focus(); else canvas.blur();
    renderAll();
  }
  function trapFocus(e) {
    const list = [...$('modal').querySelectorAll('button:not(:disabled),input,select')];
    if (!list.length) return;
    const first = list[0], lastEl = list[list.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); lastEl.focus(); }
    else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); first.focus(); }
  }
  $('mClose').addEventListener('click', closeModal);
  $('shade').addEventListener('pointerdown', e => { if (e.target === $('shade')) closeModal(); });

  function portrait(id, w, h) {
    const cv = el('canvas'); cv.width = 14; cv.height = 18; cv.className = 'portrait';
    if (w) { cv.style.width = w + 'px'; cv.style.height = h + 'px'; }
    cv.getContext('2d').drawImage(sheets[id]['down:stand:0'].cv, 0, 0);
    cv.setAttribute('aria-hidden', 'true');
    return cv;
  }
  function icon(key, v) {
    const f = C.fields[key];
    const s = el('span', 'icon' + (key === 'book' ? (v === 0 ? ' y' : ' b') : ''), f.icons[v]);
    s.title = f.labels[v]; s.setAttribute('aria-label', f.labels[v]);
    return s;
  }

  // ---------- interactions ----------
  function interact(d, t) {
    if (busy || modalOpen || !t) return;
    const me = C.detectives.find(x => x.id === d.id);
    if (t.kind === 'det') return talkDetective(d, t.det);
    if (t.kind === 'ghost') return recordCard(t.ghost);
    if (t.name === 'terminal') return terminal();
    const owner = C.ownerOfSpot(t.name);
    if (t.name !== 'tarot' && !t.src) { toast(t.label + ': vụ này không có nguồn mới ở đây.'); return; }
    if (owner && owner.id !== me.id) {
      const od = detById(owner.id);
      if (slotOf(od) >= 0) { toast(t.label + ' là việc của ' + C.roles[owner.role].name + ' ' + owner.name + '. Gọi ' + owner.name + ' tới nhé.'); return; }
      return askOwner(d, od, t);
    }
    const c = kase();
    if (c.plate && c.plate.spot === t.name && !plateHeld()) return lockedPlate(d, t);
    if (t.name === 'tarot') return tarot(me);
    return examine(t.src, me);
  }

  function askOwner(d, od, t) {
    const owner = C.detectives.find(x => x.id === od.id);
    const body = openModal(C.roles[owner.role].name.toUpperCase() + ' · ' + t.label.toUpperCase(), 'Việc của ' + owner.name);
    body.append(el('p', '', t.label + ' chỉ ' + C.roles[owner.role].name.toLowerCase() + ' mới mở được. ' + owner.name + ' đang ở trong phòng.'));
    body.append(btn('Nhờ ' + owner.name + ' đi khám', 'primary', () => { closeModal(); askFetch(od, t.name); }), document.createTextNode(' '), btn('Để sau', 'ghost', closeModal));
  }

  function lockedPlate(d, t) {
    const c = kase();
    const body = openModal('THỬ THÁCH HAI NGƯỜI', t.label + ' đang khoá');
    body.append(el('p', '', 'Khoá chỉ mở khi có một người đứng giữ công tắc sáng xanh ở ô ' + (c.plate.at[0] > 7 ? 'bên phải' : 'bên trái') + ' phòng. Một người không thể vừa giữ công tắc vừa khám.'));
    const helpers = dets.filter(x => x !== d && slotOf(x) < 0 && !x.task);
    for (const h of helpers) {
      const who = C.detectives.find(x => x.id === h.id);
      body.append(btn('Nhờ ' + who.name + ' giữ công tắc', 'ghost', () => { closeModal(); askHold(h); }), document.createTextNode(' '));
    }
    if (team.length > 1) body.append(el('p', 'note', 'Chơi nhiều người: một bạn đứng lên công tắc, bạn kia khám.'));
  }

  function recordCard(g) {
    const c = kase(), s = session();
    const body = openModal('HỒ SƠ MÁY XUẤT · BÓNG DỮ LIỆU', 'Hồ sơ ' + C.nameOf(g.id));
    const wrap = el('div', 'talk');
    wrap.append(portrait(g.id));
    const right = el('div');
    right.append(el('p', '', 'Một trong sáu hồ sơ máy điểm danh chiếu ra. Không ai đóng vai hồ sơ; đúng một bóng là bản máy ghép thừa.'));
    const rec = el('div', 'record');
    const row = c.rows.find(r => r.id === g.id);
    const bits = [];
    if (c.kind === 'photo') for (const k of c.sources) if (s.earned.includes(k)) { const sp = el('span'); sp.append(C.fields[k].name + ' ', icon(k, row[k])); bits.push(sp); }
    if (c.kind !== 'photo' && s.earned.includes('scan')) bits.push(el('span', '', c.kind === 'timeline'
      ? C.short[row.trip[0]] + ' 09:0' + row.trip[1] + ' → ' + C.short[row.trip[2]] + ' 09:0' + row.trip[3] + ' · huy hiệu ' + C.fields.badge.labels[row.badge]
      : C.nodes[row.trip[0]] + ' → ' + C.nodes[row.trip[1]] + ', ' + row.trip[2] + ' phút'));
    if (bits.length) bits.forEach((b, i) => { if (i) rec.append(' · '); rec.append(b); });
    else rec.append(el('span', 'note', 'Chưa có thuộc tính nào. Khám nguồn để máy mở thông tin của hồ sơ này.'));
    right.append(rec);
    wrap.append(right); body.append(wrap);
  }

  function talkDetective(d, other) {
    const p = C.detectives.find(x => x.id === other.id), c = kase(), s = session();
    if (slotOf(other) < 0) other.dir = facing(other, d);
    const body = openModal(C.roles[p.role].name.toUpperCase() + (slotOf(other) >= 0 ? ' · NGƯỜI CHƠI ĐIỀU KHIỂN' : ' · THÁM TỬ MẶC ĐỊNH'), p.name);
    const wrap = el('div', 'talk');
    wrap.append(portrait(p.id));
    const right = el('div');
    right.append(el('span', 'arch', p.sign + ' · ' + p.tarot), el('p', '', p.trait));
    const bubble = el('div', 'bubble'); bubble.setAttribute('aria-live', 'polite');
    let typing;
    const say = text => {
      clearInterval(typing);
      if (quiet()) { bubble.textContent = text; return; }
      let i = 0; bubble.textContent = '';
      typing = setInterval(() => { i += 2; bubble.textContent = text.slice(0, i); if (i >= text.length) clearInterval(typing); }, 24);
    };
    const tones = el('div', 'seg');
    [['soft', 'Hỏi nhẹ'], ['direct', 'Hỏi thẳng'], ['joke', 'Trêu nhẹ']].forEach(([k, lab], i) => {
      const b = btn(lab, '', () => { tones.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); say(p.lines[k]); });
      b.setAttribute('aria-pressed', String(i === 0)); tones.append(b);
    });
    right.append(bubble, tones);
    if (slotOf(other) < 0) {
      const asks = el('div', 'choices');
      for (const spotName of C.roles[p.role].spots) {
        const src = c.sources.find(k => E.SOURCE_SPOT[k] === spotName);
        if (spotName === 'tarot' || (src && !s.earned.includes(src))) asks.append(btn('Nhờ ' + p.name + ' khám ' + E.SPOTS[spotName].label.toLowerCase(), '', () => { closeModal(); askFetch(other, spotName); }));
      }
      if (plateNeeded() && !plateHeld()) asks.append(btn('Nhờ ' + p.name + ' giữ công tắc', '', () => { closeModal(); askHold(other); }));
      if (other.task && other.task.type === 'hold') asks.append(btn('Thôi, ' + p.name + ' nghỉ đi', '', () => { closeModal(); other.task = null; other.nextThink = time + 500; }));
      if (asks.childElementCount) right.append(el('p', 'note', 'Nhờ việc:'), asks);
    } else right.append(el('p', 'note', 'Bạn này do một người chơi điều khiển. Muốn họ khám gì thì nói với họ.'));
    right.append(el('p', 'note', 'Lời nói chỉ thể hiện tính cách, không phải chứng cứ. Cung và tarot do tác giả gán, không dùng để chấm.'));
    wrap.append(right); body.append(wrap);
    say(p.lines.soft);
  }

  function reveal(id) {
    const c = kase(), s = session();
    C.complete(progress, index, { status: 'solved' });
    s.solved = true; busy = true;
    for (const d of dets) { d.path = null; d.then = null; d.task = null; }
    const g = ghosts.find(x => x.id === id);
    const finish = () => {
      g.hidden = true; g.glitch = 0; busy = false; s.gone = id;
      const body = openModal(c.stamp + ' · ĐÃ TÌM RA BẢN GHÉP', 'Hồ sơ thừa: ' + C.nameOf(id));
      const box = el('div', 'reveal'); box.append(el('h3', '', 'Bóng hồ sơ ' + C.nameOf(id) + ' là bản máy ghép thừa'), el('p', '', explain(c, id)));
      body.append(box, el('p', 'note', 'Hồ sơ là dữ liệu hư cấu, không ai trong đội đóng vai nó. Không có điểm, coin hay streak.'));
      if (index < C.cases.length - 1) body.append(btn('Sang vụ ' + (index + 2) + ' →', 'primary', () => { closeModal(); goTo(index + 1); }));
      else body.append(el('p', '', 'Đội đã đi hết bảy vụ: đếm, cộng đường, đối chiếu, checkpoint, đọc gương, cửa một chiều và ghép giờ.'), btn('Chơi lại từ đầu', 'primary', () => { closeModal(); resetAll(); }));
      renderAll();
    };
    if (quiet()) { finish(); return; }
    g.glitch = 1;
    for (const d of dets) setTimeout(() => (d.hop = 380), 900 + Math.random() * 300);
    setTimeout(() => { leaves(g); g.hidden = true; }, 600);
    setTimeout(finish, 1500);
  }

  // ---------- team setup and faces ----------
  async function loadFace(file) {
    // Decode locally, crop a centred square, keep only a 64 x 64 canvas in memory. Nothing is uploaded or stored.
    const bmp = await createImageBitmap(file);
    const side = Math.min(bmp.width, bmp.height);
    const cv = document.createElement('canvas'); cv.width = 64; cv.height = 64;
    const g = cv.getContext('2d');
    g.imageSmoothingEnabled = true;
    g.drawImage(bmp, (bmp.width - side) / 2, (bmp.height - side) / 2.6, side, side, 0, 0, 64, 64);
    if (bmp.close) bmp.close();
    return cv;
  }
  function teamSetup(then) {
    const body = openModal('ĐỘI THÁM TỬ · CHỈ TRÊN MÁY NÀY', 'Ai chơi?');
    let count = team.length;
    const draft = team.slice();
    const render = () => {
      body.replaceChildren();
      body.append(el('p', 'note', 'Chơi một mình: bạn chọn một thám tử, ba người còn lại là thám tử mặc định, bạn nhờ họ đi khám hay giữ công tắc. Chơi nhiều người trên cùng màn hình: mỗi người một thám tử và một bộ phím.'));
      const seg = el('div', 'seg'); seg.setAttribute('role', 'group'); seg.setAttribute('aria-label', 'Số người chơi');
      [1, 2, 3, 4].forEach(n => { const b = btn(n + ' người', '', () => { count = n; while (draft.length < n) draft.push(C.detectives.find(x => !draft.includes(x.id)).id); draft.length = n; render(); }); b.setAttribute('aria-pressed', String(n === count)); seg.append(b); });
      body.append(seg);
      for (let slot = 0; slot < count; slot++) {
        const box = el('div', 'slot');
        box.append(el('b', '', 'Người chơi ' + (slot + 1)), el('span', 'note', ' · ' + (count === 1 ? 'W A S D hoặc mũi tên · E' : CONTROLS[slot].name) + (slot === 0 ? ' · chạm/bấm chuột' : '')));
        const pick = el('div', 'pick four');
        for (const d of C.detectives) {
          const taken = draft.includes(d.id) && draft[slot] !== d.id;
          const b = btn('', '', () => { draft[slot] = d.id; render(); });
          b.disabled = taken; b.setAttribute('aria-pressed', String(draft[slot] === d.id));
          b.append(portrait(d.id, 42, 54), el('span', '', d.name), el('small', '', C.roles[d.role].name));
          pick.append(b);
        }
        box.append(pick);
        const id = draft[slot];
        const faceRow = el('div', 'row');
        if (faces.has(id)) { const thumb = faces.get(id); const img = el('canvas', 'thumb'); img.width = 64; img.height = 64; img.getContext('2d').drawImage(thumb, 0, 0); faceRow.append(img, btn('Bỏ ảnh mặt', 'small', () => { faces.delete(id); render(); })); }
        const label = el('label', 'small filebtn', faces.has(id) ? 'Đổi ảnh mặt' : 'Gắn mặt của bạn (tuỳ chọn)');
        const inp = el('input'); inp.type = 'file'; inp.accept = 'image/*'; inp.setAttribute('capture', 'user'); inp.className = 'sr-only';
        inp.addEventListener('change', async () => { const f = inp.files && inp.files[0]; if (!f) return; try { faces.set(id, await loadFace(f)); } catch (err) { toast('Không đọc được ảnh này.'); } inp.value = ''; render(); });
        label.append(inp); faceRow.append(label);
        box.append(faceRow);
        body.append(box);
      }
      body.append(el('p', 'note', 'Ảnh mặt: chỉ dùng ảnh của chính người chơi thám tử đó. Ảnh được cắt và dán ngay trong trình duyệt, không gửi đi đâu, không lưu; tải lại trang hoặc bấm "Bỏ ảnh mặt" là mất.'));
      body.append(btn('Vào phòng', 'primary', () => {
        team = draft.slice(0, count); active = 0;
        for (const d of dets) { d.path = null; d.then = null; d.task = null; }
        closeModal(); renderAll(); renderSlots(); if (then) then();
      }));
    };
    render();
  }
  function renderSlots() {
    const bar = $('slots'); bar.replaceChildren();
    bar.hidden = team.length < 2;
    team.forEach((id, slot) => {
      const d = C.detectives.find(x => x.id === id);
      const b = btn('', 'slotchip', () => { active = slot; renderSlots(); });
      b.setAttribute('aria-pressed', String(slot === active));
      b.style.setProperty('--slot', ['#f2b45a', '#7fc8a0', '#ef8a7a', '#6aa7e8'][slot]);
      b.append(el('i'), d.name + ' · ' + CONTROLS[slot].label);
      b.setAttribute('aria-label', 'Chạm để điều khiển ' + d.name);
      bar.append(b);
    });
  }
  $('teamBtn').addEventListener('click', () => teamSetup());

  function examine(key, via) {
    const c = kase(), s = session();
    const spot = E.SPOTS[E.SOURCE_SPOT[key]];
    const body = openModal(c.stamp + ' · ' + (via ? C.roles[via.role].name.toUpperCase() + ' ' + via.name.toUpperCase() : 'NGUỒN HƯ CẤU'), sourceTitle(key));
    body.append(sourceView(c, key));
    if (s.earned.includes(key)) { body.append(el('p', 'msg good', '✓ Đã ghi vào sổ tay.')); return; }
    const chk = C.sourceCheck(c, key);
    const box = el('div', 'check');
    box.append(el('p', '', chk.prompt));
    let value;
    if (chk.type === 'tally') {
      value = chk.labels.map(() => 0);
      const wrap = el('div', 'steppers');
      chk.labels.forEach((lab, i) => {
        const st = el('div', 'stepper'); const out = el('output', '', '0'); out.setAttribute('aria-live', 'polite');
        st.append(el('label', '', lab),
          btn('−', '', () => { value[i] = Math.max(0, value[i] - 1); out.textContent = value[i]; }),
          out,
          btn('+', '', () => { value[i] = Math.min(6, value[i] + 1); out.textContent = value[i]; }));
        st.querySelectorAll('button')[0].setAttribute('aria-label', 'Bớt ' + lab);
        st.querySelectorAll('button')[1].setAttribute('aria-label', 'Thêm ' + lab);
        wrap.append(st);
      });
      box.append(wrap);
    } else if (chk.type === 'number') {
      const inp = el('input', 'num'); inp.type = 'number'; inp.min = chk.min; inp.max = chk.max; inp.inputMode = 'numeric'; inp.setAttribute('aria-label', chk.prompt);
      inp.addEventListener('input', () => (value = inp.value));
      inp.addEventListener('keydown', e => { if (e.key === 'Enter') confirm.click(); });
      box.append(inp);
    } else {
      const ch = el('div', 'choices');
      chk.options.forEach(([v, lab]) => { const b = btn(lab, '', () => { value = v; ch.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); }); b.setAttribute('aria-pressed', 'false'); ch.append(b); });
      box.append(ch);
    }
    const msg = el('p', 'msg'); msg.setAttribute('role', 'status');
    const confirm = btn('Ghi vào sổ tay', 'primary', () => {
      if (!C.checkSource(chk, value)) { msg.textContent = 'Chưa khớp với điều đang hiện trong nguồn. Xem lại, không mất gì.'; box.classList.remove('shake'); void box.offsetWidth; box.classList.add('shake'); return; }
      if (!s.earned.includes(key)) s.earned.push(key);
      releaseHolders();
      if (chk.type === 'tally') s.tallies[key] = value.slice();
      closeModal();
      sparkle(spot.tx * T + 8, spot.ty * T + 4);
      toast('Đã ghi ' + sourceTitle(key) + ' vào sổ tay.');
      renderAll();
    });
    box.append(confirm, msg);
    body.append(box);
  }

  function sourceTitle(key) {
    return { badge: 'Ảnh cận huy hiệu', book: 'Ảnh cận bìa sổ', ticket: 'Ảnh cận phiếu', roomphoto: 'Ảnh toàn cảnh phòng máy', map: 'Sơ đồ hành lang', scan: 'Bản ghi máy quét', checkpoint: 'Sổ phòng máy', door: 'Biển cửa thoát hiểm' }[key];
  }

  function sourceView(c, key) {
    const wrap = el('div');
    if (C.fields[key] || key === 'roomphoto') {
      const field = key === 'roomphoto' ? 'badge' : key;
      const mirrored = (c.mirrored || []).includes(key);
      const ph = el('div', 'photo' + (mirrored ? ' mirror' : ''));
      ph.append(el('span', 'stamp', c.stamp + ' · ' + (key === 'roomphoto' ? 'ẢNH TOÀN PHÒNG MÁY LÚC 09:04' : 'ẢNH CẬN ' + C.fields[field].name.toUpperCase()) + (mirrored ? ' · CHỤP QUA GƯƠNG TỦ ĐỒ' : '')));
      const strip = el('div', 'strip');
      const seen = key === 'roomphoto' ? c.proof.badge : C.seenProof(c, key);
      const items = [];
      seen.forEach((n, v) => { for (let i = 0; i < n; i++) items.push(v); });
      items.sort((a, b) => ((a * 7 + 3) % 5) - ((b * 7 + 3) % 5));
      items.forEach((v, i) => {
        const tk = el('span', 'token' + (field === 'book' ? (v === 0 ? ' y' : ' b') : ''), C.fields[field].icons[v]);
        tk.style.animationDelay = (i * 70) + 'ms'; tk.setAttribute('aria-label', C.fields[field].labels[v]); tk.setAttribute('role', 'img');
        strip.append(tk);
      });
      ph.append(strip);
      wrap.append(ph);
      wrap.append(el('p', 'note', key === 'roomphoto'
        ? 'Ảnh chụp toàn bộ phòng máy lúc 09:04. Mỗi người trong phòng đeo đúng một huy hiệu, ai không ở trong phòng thì không có trong ảnh.'
        : 'Ảnh có đủ đồ của 5 người thật, không ai bị che. Thứ tự vật trong ảnh không phải thứ tự người.'));
    } else if (key === 'map') {
      wrap.append(mapSvg(c, null), el('p', 'note', 'Số trên mỗi đoạn là thời gian đi tối thiểu. Được chờ ở bất kỳ khu nào. Không có lối tắt nào khác.' + (c.graph === 'branched' ? ' Mũi tên là đoạn chỉ đi được một chiều.' : '')));
    } else if (key === 'scan') {
      const tb = el('table', 'ledger');
      tb.innerHTML = c.kind === 'timeline'
        ? '<thead><tr><th>Hồ sơ</th><th>Quét đầu</th><th>Quét cuối</th><th>Huy hiệu</th></tr></thead>'
        : '<thead><tr><th>Hồ sơ</th><th>Từ</th><th>Đến</th><th>Cách nhau</th></tr></thead>';
      const tbody = el('tbody');
      for (const r of c.rows) {
        const tr = el('tr');
        const cells = c.kind === 'timeline'
          ? [C.nameOf(r.id), C.short[r.trip[0]] + ' · 09:0' + r.trip[1], C.short[r.trip[2]] + ' · 09:0' + r.trip[3]]
          : [C.nameOf(r.id), C.nodes[r.trip[0]], C.nodes[r.trip[1]], r.trip[2] + ' phút'];
        cells.forEach(v => tr.append(el('td', '', v)));
        if (c.kind === 'timeline') { const td = el('td'); td.append(icon('badge', r.badge)); tr.append(td); }
        tbody.append(tr);
      }
      tb.append(tbody);
      wrap.append(tb, el('p', 'note', 'Mỗi dòng là hai lượt quét thẻ của cùng một hồ sơ. Đây là bản ghi máy, không ai nói dối, nhưng máy có thể ghép nhầm một hồ sơ.'));
    } else if (key === 'checkpoint') {
      wrap.append(el('p', '', 'Sổ phòng máy ghi: cả 5 hành trình thật đều ghé Phòng máy (P) giữa hai lượt quét. Ai bắt đầu ở P thì coi như đã ghé.'));
    } else if (key === 'door') {
      wrap.append(el('p', '', 'Biển ghi: "Cửa thoát hiểm. Chỉ mở từ phía Lớp. Đi từ Lớp ra Thư viện mất 1 phút." Phía Thư viện không có tay nắm.'));
    }
    return wrap;
  }

  function mapSvg(c, route) {
    const NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('viewBox', '0 0 320 120'); svg.setAttribute('class', 'map-svg');
    svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', 'Sơ đồ: ' + C.edgesOf(c).map(([a, b, w, one]) => C.nodes[a] + (one ? ' → ' : ' – ') + C.nodes[b] + ' ' + w + ' phút').join('; '));
    const pos = [[30, 70], [120, 70], [210, 70], [295, 70]];
    const add = (tag, attrs, text) => { const n = document.createElementNS(NS, tag); for (const k in attrs) n.setAttribute(k, attrs[k]); if (text !== undefined) n.textContent = text; svg.append(n); return n; };
    const defs = add('defs', {}); const mk = document.createElementNS(NS, 'marker');
    mk.setAttribute('id', 'arr'); mk.setAttribute('markerWidth', '8'); mk.setAttribute('markerHeight', '8'); mk.setAttribute('refX', '6'); mk.setAttribute('refY', '3'); mk.setAttribute('orient', 'auto');
    const tri = document.createElementNS(NS, 'path'); tri.setAttribute('d', 'M0,0 L6,3 L0,6 z'); tri.setAttribute('fill', '#ef8a7a'); mk.append(tri); defs.append(mk);
    const used = new Set();
    if (route) for (let i = 1; i < route.length; i++) used.add(route[i - 1] + '>' + route[i]);
    for (const [a, b, w, one] of C.edgesOf(c)) {
      const [x1, y1] = pos[a], [x2, y2] = pos[b];
      const on = used.has(a + '>' + b) || (!one && used.has(b + '>' + a));
      if (Math.abs(a - b) === 1 && !one) {
        add('line', { x1, y1, x2, y2, stroke: on ? '#f2b45a' : '#7d6f96', 'stroke-width': on ? 4 : 3 });
        add('text', { x: (x1 + x2) / 2, y: y1 - 8, 'text-anchor': 'middle' }, w + ' phút');
      } else {
        const up = one ? 108 : 20;
        add('path', { d: `M${x1},${y1} Q${(x1 + x2) / 2},${up} ${x2},${y2}`, fill: 'none', stroke: on ? '#f2b45a' : one ? '#ef8a7a' : '#7d6f96', 'stroke-width': on ? 4 : 2.5, 'stroke-dasharray': one ? '5 4' : '', 'marker-end': one ? 'url(#arr)' : '' });
        add('text', { x: (x1 + x2) / 2, y: one ? 104 : 30, 'text-anchor': 'middle' }, w + ' phút' + (one ? ' · một chiều' : ''));
      }
    }
    pos.forEach(([x, y], i) => {
      const g = document.createElementNS(NS, 'g'); g.setAttribute('class', 'node'); g.dataset.node = i;
      const circ = document.createElementNS(NS, 'circle'); circ.setAttribute('cx', x); circ.setAttribute('cy', y); circ.setAttribute('r', 15);
      circ.setAttribute('fill', route && route[route.length - 1] === i ? '#f2b45a' : '#2e2540'); circ.setAttribute('stroke', '#f3ead8'); circ.setAttribute('stroke-width', 2);
      const t1 = document.createElementNS(NS, 'text'); t1.setAttribute('x', x); t1.setAttribute('y', y + 4); t1.setAttribute('text-anchor', 'middle'); t1.textContent = C.short[i];
      if (route && route[route.length - 1] === i) t1.setAttribute('style', 'fill:#2a1d08;font-weight:700');
      const t2 = document.createElementNS(NS, 'text'); t2.setAttribute('x', x); t2.setAttribute('y', y + 30); t2.setAttribute('text-anchor', 'middle'); t2.textContent = C.nodes[i];
      g.append(circ, t1, t2); svg.append(g);
    });
    return svg;
  }

  function tarot(who) {
    const c = kase(), m = C.methodFor(c);
    const body = openModal((who ? who.name.toUpperCase() + ' RÚT LÁ · ' : '') + 'GỢI CÁCH KIỂM · KHÔNG PHẢI CHỨNG CỨ', m.card);
    const w = el('div', 'tarot');
    const card = el('div', 'card'); const inner = el('div'); inner.append(el('b', '', m.glyph), el('small', '', m.card.toUpperCase())); card.append(inner);
    const txt = el('div'); txt.append(el('p', '', m.text), el('p', 'note', 'Lá này không biết ai là hồ sơ thừa và không mở nguồn bạn chưa khám.'));
    w.append(card, txt); body.append(w);
  }

  function terminal() {
    const c = kase(), s = session();
    if (s.solved) { toast('Vụ này đã giải. Mở vụ tiếp theo trên thanh vụ.'); return; }
    const body = openModal(c.stamp + ' · MÁY ĐIỂM DANH', 'Nộp lập luận');
    const missing = c.sources.filter(k => !s.earned.includes(k));
    if (missing.length) {
      body.append(el('p', '', 'Máy chỉ nhận lập luận khi bạn đã khám đủ nguồn. Còn thiếu: ' + missing.map(sourceTitle).join(', ') + '.'));
      body.append(btn('Đi tới nguồn còn thiếu', 'primary', () => { closeModal(); const sp = E.SPOTS[E.SOURCE_SPOT[missing[0]]]; const me = lead(); walkTo(me, [sp.tx, sp.ty], () => interact(me, targets(me).find(q => q.name === E.SOURCE_SPOT[missing[0]]))); }));
      return;
    }
    let who = '';
    const reason = {};
    body.append(el('p', 'note', 'Chọn hồ sơ bạn cho là bị máy ghép thừa và nêu lý do. Máy chỉ báo đúng khi cả hai đều đúng, và không nói phần nào sai.'));
    const pick = el('div', 'pick'); pick.setAttribute('role', 'group'); pick.setAttribute('aria-label', 'Hồ sơ thừa');
    for (const p of C.profiles) {
      const b = btn('', '', () => { who = p.id; pick.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); });
      b.setAttribute('aria-pressed', 'false'); b.append(portrait(p.id, 42, 54), el('span', '', p.name)); pick.append(b);
    }
    body.append(pick);
    for (const f of C.reasonFields(c)) {
      const box = el('div', 'field'); box.append(el('span', '', f.label));
      if (f.type === 'number') {
        const inp = el('input', 'num'); inp.type = 'number'; inp.min = f.min; inp.max = f.max; inp.inputMode = 'numeric'; inp.setAttribute('aria-label', f.label);
        inp.addEventListener('input', () => (reason[f.key] = inp.value)); box.append(inp, el('span', 'note', ' phút'));
      } else {
        const seg = el('div', 'seg');
        const opts = f.type === 'label' ? f.options.map((lab, i) => [i, lab]) : f.options;
        opts.forEach(([v, lab]) => { const b = btn(lab, '', () => { reason[f.key] = v; seg.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); }); b.setAttribute('aria-pressed', 'false'); seg.append(b); });
        box.append(seg);
      }
      body.append(box);
    }
    const msg = el('p', 'msg'); msg.setAttribute('role', 'status');
    const go = btn('Nộp cho máy', 'primary', () => {
      const r = C.judge(c, s.earned, who, reason);
      if (r.status === 'solved') { closeModal(); reveal(who); return; }
      msg.textContent = r.text; go.classList.remove('shake'); void go.offsetWidth; go.classList.add('shake');
    });
    body.append(go, msg);
  }

  function explain(c, id) {
    const name = C.nameOf(id);
    if (c.kind === 'photo') {
      const exp = C.expectedReason(c, id);
      return 'Bỏ hồ sơ ' + name + ' thì mọi ảnh khớp: ' + c.sources.map(k => 'ảnh ' + C.fields[k].name.toLowerCase() + ' thừa một ' + C.fields[k].labels[exp[k]]).join(', ') + '.' + ((c.mirrored || []).length ? ' Ảnh phiếu chụp qua gương nên mũi tên phải đọc ngược lại.' : '');
    }
    if (c.kind === 'route') {
      const r = c.rows.find(x => x.id === id);
      return C.nodes[r.trip[0]] + ' → ' + C.nodes[r.trip[1]] + ' cần ít nhất ' + C.expectedReason(c, id).minutes + ' phút, nhưng hồ sơ ghi ' + r.trip[2] + ' phút.';
    }
    const r = c.rows.find(x => x.id === id);
    return name + ' đi sát giờ nên bắt buộc đang ở phòng máy lúc 09:04, nhưng ảnh không có huy hiệu ' + C.fields.badge.labels[r.badge] + '.';
  }

  // ---------- notebook ----------
  // The notebook is always on screen (side panel on desktop, below the stage on phones). N jumps to it.
  function toggleBook(force) {
    if (force === false) { canvas.scrollIntoView({ block: 'nearest', behavior: fx() ? 'smooth' : 'auto' }); return; }
    $('book').scrollIntoView({ block: 'start', behavior: fx() ? 'smooth' : 'auto' });
    const tabBtn = document.querySelector('[data-tab][aria-selected="true"]'); if (tabBtn) tabBtn.focus({ preventScroll: true });
  }
  document.querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', () => { tab = b.dataset.tab; renderBook(); }));

  function renderBook() {
    document.querySelectorAll('[data-tab]').forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === tab)));
    const body = $('bookBody'); body.replaceChildren();
    const c = kase(), s = session();
    if (tab === 'sources') {
      if (!s.earned.length) body.append(el('p', 'empty', 'Chưa có nguồn nào. Đi tới chỗ có viền vàng trong phòng và khám.'));
      for (const k of s.earned) {
        const card = el('div', 'src');
        const h = el('h3', '', sourceTitle(k)); if ((c.mirrored || []).includes(k)) h.append(el('span', 'tag', 'qua gương'));
        card.append(h);
        if (s.tallies[k]) {
          const field = k === 'roomphoto' ? 'badge' : k;
          const flipped = s.flipped.includes(k);
          const vals = flipped ? s.tallies[k].slice().reverse() : s.tallies[k];
          const tl = el('div', 'tally');
          C.fields[field].labels.forEach((lab, i) => { const sp = el('span'); sp.append(icon(field, i), ' ' + lab + ' ' + vals[i]); tl.append(sp); });
          card.append(tl);
          if (field === 'ticket') card.append(btn(flipped ? '↔ Đang đọc lật (Trái ↔ Phải)' : '↔ Đọc lật trái/phải', 'small', () => { const i = s.flipped.indexOf(k); if (i >= 0) s.flipped.splice(i, 1); else s.flipped.push(k); renderBook(); }));
        } else if (k === 'map') card.append(mapSvg(c, null));
        else if (k === 'scan') card.append(el('small', '', 'Xem từng hồ sơ trong tab Tự suy luận.'));
        else if (k === 'checkpoint') card.append(el('small', '', '5 hành trình thật đều ghé P.'));
        else if (k === 'door') card.append(el('small', '', 'Cửa thoát hiểm chỉ đi Lớp → Thư viện, 1 phút.'));
        card.append(btn('Xem lại nguồn', 'small', () => examine(k)));
        body.append(card);
      }
      const left = c.sources.filter(k => !s.earned.includes(k));
      if (left.length) body.append(el('p', 'note', 'Còn ' + left.length + ' nguồn chưa khám: ' + left.map(k => E.SPOTS[E.SOURCE_SPOT[k]].label).join(', ') + '.'));
    } else if (tab === 'work') {
      if (c.kind === 'photo') workPhoto(body, c, s); else workRoute(body, c, s);
    } else {
      const list = el('div', 'places');
      for (const t of targets(lead()).filter(t => t.relevant && t.kind !== 'ghost')) {
        const b = btn('', '', () => { toggleBook(false); const me = lead(); walkTo(me, [t.tx, t.ty], () => interact(me, targets(me).find(q => (q.name && q.name === t.name) || (q.det && q.det === t.det)) || t)); });
        b.append(el('span', '', (t.kind === 'det' ? 'Nói chuyện với ' : 'Đi tới ') + t.label));
        if (t.earned) b.append(el('span', 'ok', '✓ đã khám'));
        list.append(b);
      }
      body.append(el('p', 'note', 'Bấm để nhân vật tự đi tới và mở. Dùng được bằng bàn phím và trình đọc màn hình.'), list);
    }
  }

  function workPhoto(body, c, s) {
    const boards = c.sources.filter(k => s.earned.includes(k));
    if (!boards.length) { body.append(el('p', 'empty', 'Khám ít nhất một ảnh để máy mở thuộc tính của từng hồ sơ.')); return; }
    body.append(el('p', 'note', 'Tự đếm: gạch thử một hồ sơ rồi đếm lại các hồ sơ còn lại, so với số bạn ghi từ ảnh. Sổ không tự cộng và không báo khớp.'));
    const tb = el('table', 'ledger');
    const head = el('tr'); head.append(el('th', '', 'Hồ sơ')); boards.forEach(k => head.append(el('th', '', C.fields[k].name))); head.append(el('th', '', ''));
    const thead = el('thead'); thead.append(head); tb.append(thead);
    const tbody = el('tbody');
    for (const r of c.rows) {
      const tr = el('tr'); if (s.struck.includes(r.id)) tr.className = 'struck';
      tr.append(el('td', '', C.nameOf(r.id)));
      boards.forEach(k => { const td = el('td'); td.append(icon(k, r[k])); tr.append(td); });
      const td = el('td');
      td.append(btn(s.struck.includes(r.id) ? 'Bỏ gạch' : 'Gạch', '', () => { const i = s.struck.indexOf(r.id); if (i >= 0) s.struck.splice(i, 1); else s.struck.push(r.id); renderBook(); }));
      tr.append(td); tbody.append(tr);
    }
    tb.append(tbody); body.append(tb);
    const yours = el('div', 'src'); yours.append(el('h3', '', 'Số bạn ghi từ ảnh'));
    boards.forEach(k => { const flipped = s.flipped.includes(k); const vals = flipped ? s.tallies[k].slice().reverse() : s.tallies[k]; const tl = el('div', 'tally'); C.fields[k].labels.forEach((lab, i) => { const sp = el('span'); sp.append(icon(k, i), ' ' + vals[i]); tl.append(sp); }); if (flipped) tl.append(el('span', 'tag', 'đọc lật')); yours.append(tl); });
    body.append(yours);
  }

  function workRoute(body, c, s) {
    if (!s.earned.includes('scan') || !s.earned.includes('map')) { body.append(el('p', 'empty', 'Cần cả sơ đồ hành lang và bản ghi máy quét để dựng đường.')); return; }
    const R = s.route;
    body.append(el('p', 'note', 'Dựng đường: chọn hồ sơ, rồi bấm lần lượt các khu trên sơ đồ. Sổ chỉ cộng các đoạn bạn chọn, không tìm đường ngắn nhất hộ bạn.'));
    const pills = el('div', 'pills');
    for (const r of c.rows) {
      const b = btn(C.nameOf(r.id), '', () => { R.who = r.id; R.path = [r.trip[0]]; R.wait = 0; renderBook(); });
      b.setAttribute('aria-pressed', String(R.who === r.id)); pills.append(b);
    }
    body.append(pills);
    if (!R.who) return;
    const row = c.rows.find(r => r.id === R.who);
    const end = c.kind === 'timeline' ? row.trip[2] : row.trip[1];
    const have = c.kind === 'timeline' ? row.trip[3] - row.trip[1] : row.trip[2];
    const bl = el('div', 'builder');
    bl.append(el('p', '', C.nameOf(R.who) + ': ' + C.nodes[R.path[0]] + ' → ' + C.nodes[end] + ', hồ sơ ghi ' + have + ' phút' + (c.kind === 'timeline' ? ' (09:0' + row.trip[1] + ' → 09:0' + row.trip[3] + ')' : '') + '.'));
    const svg = mapSvg(c, R.path);
    svg.querySelectorAll('.node').forEach(g => {
      g.setAttribute('tabindex', '0'); g.setAttribute('role', 'button'); g.setAttribute('aria-label', 'Đi tới ' + C.nodes[g.dataset.node]);
      const go = () => {
        const to = Number(g.dataset.node), from = R.path[R.path.length - 1];
        const e = C.edgesOf(c).find(([a, b, , one]) => (a === from && b === to) || (!one && a === to && b === from));
        if (!e) { toast('Không có đoạn đi thẳng ' + C.short[from] + ' → ' + C.short[to] + '.'); return; }
        R.path.push(to); renderBook();
      };
      g.addEventListener('click', go); g.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); go(); } });
    });
    bl.append(svg);
    let sum = 0;
    for (let i = 1; i < R.path.length; i++) { const a = R.path[i - 1], b = R.path[i]; const e = C.edgesOf(c).find(([x, y, , one]) => (x === a && y === b) || (!one && x === b && y === a)); sum += e[2]; }
    const line = el('div', 'row');
    line.append(el('span', '', 'Đường: ' + R.path.map(i => C.short[i]).join(' → ')), el('span', 'sum', (sum + R.wait) + ' phút'));
    bl.append(line);
    const ctl = el('div', 'row');
    ctl.append(btn('Lùi một bước', 'small', () => { if (R.path.length > 1) R.path.pop(); renderBook(); }),
      btn('Chờ +1 phút', 'small', () => { R.wait += 1; renderBook(); }),
      btn('Bỏ chờ', 'small', () => { R.wait = 0; renderBook(); }));
    bl.append(ctl);
    if (R.wait) bl.append(el('p', 'note', 'Đã thêm ' + R.wait + ' phút chờ.'));
    body.append(bl);
    if (c.kind === 'timeline' && s.earned.includes('roomphoto')) {
      const yours = el('div', 'src'); yours.append(el('h3', '', 'Ảnh phòng máy 09:04 (số bạn ghi)'));
      const tl = el('div', 'tally'); C.fields.badge.labels.forEach((lab, i) => { const sp = el('span'); sp.append(icon('badge', i), ' ' + lab + ' ' + s.tallies.roomphoto[i]); tl.append(sp); });
      yours.append(tl, el('p', 'note', 'Gợi ý cách nghĩ: với mỗi hồ sơ, lúc 09:04 người đó bắt buộc ở P, không thể ở P, hay có thể?'));
      body.append(yours);
    }
  }

  // ---------- HUD, track, goal ----------
  function renderTrack() {
    const tr = $('track'); tr.replaceChildren();
    C.cases.forEach((c, i) => {
      const b = btn('', progress.solved.includes(i) ? 'done' : '', () => goTo(i));
      b.disabled = i > progress.unlocked;
      if (i === index) b.setAttribute('aria-current', 'step');
      b.append(el('b', '', progress.solved.includes(i) ? '✓' : String(i + 1)), el('span', '', c.skill));
      b.setAttribute('aria-label', 'Vụ ' + (i + 1) + ': ' + c.title + (b.disabled ? ', chưa mở' : progress.solved.includes(i) ? ', đã giải' : ''));
      tr.append(b);
    });
  }
  function renderGoal() {
    const c = kase(), s = session();
    const have = c.sources.filter(k => s.earned.includes(k)).length;
    const missing = c.sources.find(k => !s.earned.includes(k));
    let hint = '';
    if (missing) {
      const owner = C.ownerOfSpot(E.SOURCE_SPOT[missing]);
      hint = ' · tiếp: ' + E.SPOTS[E.SOURCE_SPOT[missing]].label + (owner ? ' (' + owner.name + ')' : '');
      if (c.plate && c.plate.spot === E.SOURCE_SPOT[missing] && !plateHeld()) hint += ', cần người giữ công tắc';
    }
    const steps = [
      ['Khám nguồn (' + have + '/' + c.sources.length + ')' + hint, have === c.sources.length],
      ['Tự suy luận trong sổ tay', s.solved],
      ['Nộp lập luận ở máy điểm danh', s.solved]
    ];
    const ol = $('goal'); ol.replaceChildren();
    let nowSet = false;
    for (const [text, ok] of steps) { const li = el('li', ok ? 'ok' : !nowSet ? 'now' : '', text); if (!ok) nowSet = true; ol.append(li); }
    $('hudStamp').textContent = c.stamp; $('hudTitle').textContent = c.title;
  }
  function renderAll() { renderTrack(); renderGoal(); renderBook(); }

  // ---------- case flow ----------
  function placeEveryone() {
    const s = session();
    dets.forEach(d => Object.assign(d, feet(...d.home), { dir: 'up', path: null, then: null, task: null, vx: 0, vy: 0, hop: 0 }));
    ghosts.forEach(g => Object.assign(g, feet(...E.NPC_HOME[C.ids.indexOf(g.id)]), { hidden: s.gone === g.id, glitch: 0, hop: 0 }));
    pending.length = 0;
  }
  function intro() {
    const c = kase();
    const body = openModal('VỤ ' + (index + 1) + '/' + C.cases.length + ' · ' + c.stamp, c.title);
    body.append(el('span', 'intro-skill', c.skill), el('p', '', c.intro));
    if (index === 0) {
      const g = el('div', 'controls');
      g.append(el('b', '', 'Đi'), el('span', '', coarse ? 'Chạm vào sàn, thám tử tự đi tới.' : 'W A S D, phím mũi tên, hoặc bấm vào sàn.'),
        el('b', '', 'Khám'), el('span', '', coarse ? 'Chạm vào đồ vật hoặc nút ở cạnh dưới.' : 'Đứng cạnh đồ vật rồi nhấn phím hành động, hoặc bấm vào đồ vật.'),
        el('b', '', 'Vai'), el('span', '', 'Mỗi thám tử chỉ mở được loại nguồn của vai mình. Việc của người khác thì nhờ họ.'),
        el('b', '', 'Mục tiêu'), el('span', '', 'Mũi tên vàng chỉ chỗ cần tới, mũi tên xanh chỉ công tắc cần người giữ.'));
      body.append(g);
    }
    if (c.plate) body.append(el('p', 'note', 'Vụ này có một thử thách hai người: một nguồn bị khoá, cần một thám tử đứng giữ công tắc.'));
    body.append(el('p', 'note', 'Sáu bóng xanh trong phòng là sáu hồ sơ máy chiếu ra. Đúng một bóng là bản ghép thừa.'));
    body.append(btn('Vào phòng', 'primary', closeModal));
  }
  function goTo(i) {
    if (i > progress.unlocked || busy) return;
    const changing = i !== index;
    const doIt = () => { index = i; placeEveryone(); renderAll(); if (!session().solved) intro(); };
    if (!changing || quiet()) { doIt(); return; }
    busy = true; $('fade').classList.add('on');
    setTimeout(() => { doIt(); busy = false; $('fade').classList.remove('on'); }, 320);
  }
  function resetAll() {
    progress = C.createProgress(); sessions = new Map(); index = 0;
    goTo(0);
  }
  $('resetBtn').addEventListener('click', () => {
    const body = openModal('CHỈ XOÁ TRONG TAB NÀY', 'Chơi lại từ đầu?');
    body.append(el('p', '', 'Xoá nguồn đã khám và tiến độ cả bảy vụ trong tab này. Đội và ảnh mặt giữ nguyên.'), btn('Chơi lại', 'primary', () => { closeModal(); resetAll(); }), document.createTextNode(' '), btn('Giữ ván đang chơi', 'ghost', closeModal));
  });

  const MOTION_LABEL = { full: 'Cử động: đầy đủ', reduced: 'Cử động: giảm', off: 'Cử động: tắt' };
  function applyMotion() {
    document.body.classList.toggle('reduced', motion === 'reduced');
    document.body.classList.toggle('still', motion === 'off');
    $('motionBtn').textContent = MOTION_LABEL[motion];
    $('motionBtn').setAttribute('aria-label', MOTION_LABEL[motion] + '. Bấm để đổi.');
    if (!fx()) particles.length = 0;
  }
  $('motionBtn').addEventListener('click', () => { motion = { full: 'reduced', reduced: 'off', off: 'full' }[motion]; applyMotion(); toast(MOTION_LABEL[motion]); });

  // Optional on-screen d-pad for touch. It drives the active detective; tap-to-move stays the main control.
  if (coarse) $('padBtn').hidden = false;
  $('padBtn').addEventListener('click', () => {
    const on = $('dpad').hidden; $('dpad').hidden = !on; $('padBtn').setAttribute('aria-pressed', String(on));
  });
  document.querySelectorAll('#dpad [data-dir]').forEach(b => {
    const key = () => (team.length === 1 ? CONTROLS[0] : CONTROLS[active])[b.dataset.dir];
    let k = null;
    const down = e => { e.preventDefault(); k = key(); keys.add(k); const d = lead(); d.path = null; d.then = null; };
    const up = () => { if (k) keys.delete(k); k = null; };
    b.addEventListener('pointerdown', down); b.addEventListener('pointerup', up); b.addEventListener('pointerleave', up); b.addEventListener('pointercancel', up);
  });

  // ---------- boot ----------
  applyMotion();
  fit();
  placeEveryone();
  renderAll();
  renderSlots();
  schedule();
  teamSetup(intro);
  window.__lab14 = {
    hold: (v) => { held = v; }, step: (ms) => { for (let t = 0; t < ms; t += 16) tick(time + 16); },
    dets, ghosts, sessions, faces, team: () => team.slice(), setTeam: (t) => { team = t.slice(); active = 0; renderSlots(); renderAll(); },
    progress: () => progress, index: () => index, lead, walkTo, interact, targets, nearest, goTo, plateHeld, askFetch, askHold
  };
})();
