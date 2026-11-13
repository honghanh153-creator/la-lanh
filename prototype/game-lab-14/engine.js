// Game lab 14: tile room, collision, pathfinding and code-drawn pixel sprites.
// Pure helpers are exported for node tests; drawing helpers only run in a browser.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Engine = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const TILE = 16;
  // 15 x 10 tiles = 240 x 160 internal pixels. W wall, K shelf, T teacher desk, D desk, m terminal,
  // s scanner, c camera, M mirror locker, p plant, . floor.
  const MAP = [
    'WWWWWWWWWWWWWWW',
    'WWWWWWWWWWWWWWW',
    'K.TTT....m...sp',
    'K..............',
    '..DD..DD..DD...',
    '...............',
    '..DD..DD..DD...',
    '..............c',
    'M..............',
    'WWWWWWWWWWWWWWW'
  ];
  const W = MAP[0].length, H = MAP.length;
  const SOLID = new Set(['W', 'K', 'T', 'D', 'm', 's', 'c', 'M', 'p']);

  // Interactable spots. tx,ty is the object tile; the player stands on a free neighbour to use it.
  const SPOTS = {
    camera: { tx: 14, ty: 7, label: 'Máy ảnh', glyph: '◉' },
    teacher: { tx: 3, ty: 2, label: 'Bàn giáo viên', glyph: '▤' },
    mirror: { tx: 0, ty: 8, label: 'Tủ đồ có gương', glyph: '▯' },
    poster: { tx: 6, ty: 1, label: 'Sơ đồ hành lang', glyph: '⌗' },
    scanner: { tx: 13, ty: 2, label: 'Máy quét thẻ', glyph: '▣' },
    shelf: { tx: 0, ty: 3, label: 'Sổ phòng máy', glyph: '▥' },
    door: { tx: 11, ty: 1, label: 'Biển cửa thoát hiểm', glyph: '⇥' },
    tarot: { tx: 10, ty: 4, label: 'Bộ tarot', glyph: '✦' },
    terminal: { tx: 9, ty: 2, label: 'Máy điểm danh', glyph: '⌨' }
  };
  // Which spot gives which source key.
  const SOURCE_SPOT = { badge: 'camera', roomphoto: 'camera', book: 'teacher', ticket: 'mirror', map: 'poster', scan: 'scanner', checkpoint: 'shelf', door: 'door' };

  // Where the six record avatars stand (tile coords). They never stand on solid tiles.
  const NPC_HOME = [[2, 3], [5, 5], [8, 3], [10, 7], [13, 5], [6, 7]];
  const PLAYER_START = [7, 8];
  // Detectives start along the front row (index matches Cases.detectives).
  const DETECTIVE_HOME = [[5, 8], [7, 8], [9, 8], [11, 8]];

  function tileAt(tx, ty) { return tx < 0 || ty < 0 || tx >= W || ty >= H ? 'W' : MAP[ty][tx]; }
  function solidTile(tx, ty) { return SOLID.has(tileAt(tx, ty)); }

  function boxHitsSolid(x, y, w, h, blockers) {
    const x0 = Math.floor(x / TILE), x1 = Math.floor((x + w - 0.01) / TILE);
    const y0 = Math.floor(y / TILE), y1 = Math.floor((y + h - 0.01) / TILE);
    for (let ty = y0; ty <= y1; ty++) for (let tx = x0; tx <= x1; tx++) if (solidTile(tx, ty)) return true;
    for (const b of blockers || []) if (x < b.x + b.w && x + w > b.x && y < b.y + b.h && y + h > b.y) return true;
    return false;
  }

  // Axis-separated move so the body slides along walls instead of sticking.
  function moveWithSlide(body, dx, dy, blockers) {
    let { x, y } = body;
    if (dx && !boxHitsSolid(x + dx, y, body.w, body.h, blockers)) x += dx;
    if (dy && !boxHitsSolid(x, y + dy, body.w, body.h, blockers)) y += dy;
    return { x, y };
  }

  // 4-direction A* on tiles. blocked(tx,ty) can add dynamic blockers (other characters).
  function findPath(from, to, blocked) {
    const key = (x, y) => x + ',' + y;
    const free = (x, y) => !solidTile(x, y) && !(blocked && blocked(x, y));
    if (!free(to[0], to[1])) return null;
    const open = [[from[0], from[1], 0, Math.abs(to[0] - from[0]) + Math.abs(to[1] - from[1])]];
    const came = new Map([[key(from[0], from[1]), null]]);
    const cost = new Map([[key(from[0], from[1]), 0]]);
    while (open.length) {
      open.sort((a, b) => a[3] - b[3]);
      const [x, y, g] = open.shift();
      if (x === to[0] && y === to[1]) {
        const path = [];
        let k = key(x, y);
        while (k) { const [px, py] = k.split(',').map(Number); path.unshift([px, py]); k = came.get(k); }
        return path;
      }
      for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
        if (!free(nx, ny)) continue;
        const k = key(nx, ny), ng = g + 1;
        if (cost.has(k) && cost.get(k) <= ng) continue;
        cost.set(k, ng); came.set(k, key(x, y));
        open.push([nx, ny, ng, ng + Math.abs(to[0] - nx) + Math.abs(to[1] - ny)]);
      }
    }
    return null;
  }

  // Free tiles next to an object, nearest first.
  function standTiles(tx, ty, near, blocked) {
    const out = [[tx, ty + 1], [tx - 1, ty], [tx + 1, ty], [tx, ty - 1]]
      .filter(([x, y]) => !solidTile(x, y) && !(blocked && blocked(x, y)));
    if (near) out.sort((a, b) => Math.hypot(a[0] - near[0], a[1] - near[1]) - Math.hypot(b[0] - near[0], b[1] - near[1]));
    return out;
  }

  // Movement tuning (internal pixels per second). Reach top speed in ~0.08 s, stop in ~0.06 s.
  const MOVE = { speed: 72, accel: 900, decel: 1200 };
  function stepVelocity(v, input, dt) {
    const target = input * MOVE.speed;
    const rate = input ? MOVE.accel : MOVE.decel;
    if (v < target) return Math.min(target, v + rate * dt);
    if (v > target) return Math.max(target, v - rate * dt);
    return v;
  }

  // ---------- pixel sprites (12 x 16 templates, outlined at draw time) ----------
  const HEAD_DOWN = ['....HHHH....', '...HHHHHH...', '..HHHHHHHH..', '..HSSSSSSH..', '..SSESSESS..', '..SSSSSSSS..', '...SSmSSS...', '....SSSS....'];
  const HEAD_UP = ['....HHHH....', '...HHHHHH...', '..HHHHHHHH..', '..HHHHHHHH..', '..HHHHHHHH..', '..HHHHHHHH..', '...HHHHHH...', '....SSSS....'];
  const HEAD_SIDE = ['....HHHH....', '...HHHHHH...', '..HHHHHHHH..', '..HHHSSSSS..', '..HHSSSSES..', '..HHSSSSSS..', '...HSSSmS...', '.....SSS....'];
  const BODY_FRONT = ['..CCCCCCCC..', '.CCCCCCCCCC.', '.SCCCCCCCCS.', '.S.CCCCCC.S.'];
  const BODY_SIDE = ['....CCCCC...', '...CCCCCCC..', '...CCCSCCC..', '....CCSCC...'];
  const LEGS = {
    front: { stand: ['..PPPPPPPP..', '..PPP..PPP..', '..PPP..PPP..', '..BBB..BBB..'],
      a: ['..PPPPPPPP..', '..PPP..PPP..', '..BBB..PPP..', '.......BBB..'],
      b: ['..PPPPPPPP..', '..PPP..PPP..', '..PPP..BBB..', '..BBB.......'] },
    side: { stand: ['....PPPPP...', '....PP.PP...', '....PP.PP...', '....BB.BB...'],
      a: ['....PPPPP...', '...PP...PP..', '..PP.....PP.', '..BB.....BB.'],
      b: ['....PPPP....', '.....PP.....', '.....PP.....', '.....BB.....'] }
  };

  function template(dir, frame, opts) {
    const head = (dir === 'up' ? HEAD_UP : dir === 'down' ? HEAD_DOWN : HEAD_SIDE).map(r => r.split(''));
    if (opts.glasses && dir === 'down') head[4] = '..SGEGGEGS..'.split('');
    if (opts.glasses && dir === 'side') head[4] = '..HHSSGEGS..'.split('');
    if (opts.blink) for (const row of head) for (let i = 0; i < row.length; i++) if (row[i] === 'E') row[i] = 'S';
    if (opts.longHair) {
      for (let r = 3; r <= 8 && r < head.length; r++) {
        if (dir !== 'side' || r > 2) { if (head[r][2] !== 'E') head[r][2] = 'H'; }
        if (dir !== 'side') { if (head[r][9] !== 'E') head[r][9] = 'H'; } else { head[r][1] = r < 7 ? 'H' : head[r][1]; }
      }
    }
    if (opts.hat) {
      head[0] = '...TTTTTT...'.split('');
      head[1] = '..TTTTTTTT..'.split('');
      head[2] = '.TTTTTTTTTT.'.split('');
    }
    const body = dir === 'left' || dir === 'right' ? BODY_SIDE : BODY_FRONT;
    const legs = LEGS[dir === 'left' || dir === 'right' ? 'side' : 'front'][frame];
    let rows = head.map(r => r.join('')).concat(body, legs);
    if (dir === 'left') rows = rows.map(r => r.split('').reverse().join(''));
    return rows;
  }

  const OUTLINE = '#2a1f3d';
  function renderSprite(rows, palette) {
    const h = rows.length, w = rows[0].length;
    const px = [];
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const ch = rows[y][x];
      if (ch !== '.' && palette[ch]) px.push([x + 1, y + 1, palette[ch]]);
    }
    const filled = new Set(px.map(([x, y]) => x + ',' + y));
    const outline = [];
    for (const [x, y] of px) for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
      const k = nx + ',' + ny;
      if (!filled.has(k)) { filled.add(k); outline.push([nx, ny, OUTLINE]); }
    }
    return { w: w + 2, h: h + 2, px: outline.concat(px) };
  }

  const SKIN = '#f2c9a0';
  const LOOKS = {
    player: { H: '#3a2a22', T: '#3f6b55', C: '#4f8a6b', P: '#2f3b4a', B: '#1d1b26', hat: true },
    hanh: { H: '#3b2420', T: '#c0605a', C: '#ef9a8a', P: '#3a3550', B: '#1d1b26', longHair: true },
    quan: { H: '#1f1c1c', T: '#c08a2a', C: '#e3b23c', P: '#2e3a5c', B: '#1d1b26', glasses: true },
    minh: { H: '#26201c', T: '#3f6b55', C: '#7fc8a0', P: '#30303a', B: '#1d1b26', hat: true },
    thao: { H: '#2b2230', T: '#6a4fa0', C: '#a995d8', P: '#2f2f38', B: '#1d1b26', longHair: true },
    an: { ghost: true, H: '#2b2230', C: '#efe3c8', P: '#2e3a5c', B: '#3a3540', glasses: true },
    binh: { ghost: true, H: '#26201c', C: '#9fd3bd', P: '#30303a', B: '#e8e4dc' },
    chi: { ghost: true, H: '#3b2420', C: '#ef7b6a', P: '#26252b', B: '#e8e4dc', longHair: true },
    duy: { ghost: true, H: '#1f1c1c', C: '#e3b23c', P: '#2e3a5c', B: '#e8e4dc', glasses: true },
    ha: { ghost: true, H: '#4a3028', C: '#3d9a96', P: '#2f2f38', B: '#3a3540', longHair: true },
    linh: { ghost: true, H: '#211d24', C: '#a995d8', P: '#30303a', B: '#e8e4dc' }
  };

  // Records are machine holograms: same body shapes, one cool palette, drawn translucent.
  const GHOST = { H: '#3d7f9a', C: '#7fd0e0', P: '#4f9ab0', B: '#3d7f9a', skin: '#c9f1f6' };

  const DIRS = ['down', 'up', 'left', 'right'];
  const FRAMES = ['stand', 'a', 'b'];
  function buildSheet(look) {
    const g = look.ghost ? GHOST : null;
    const palette = g ? { H: g.H, S: g.skin, E: '#1d4a5a', m: '#8fc8d4', G: '#1d4a5a', C: g.C, P: g.P, B: g.B, T: g.H }
      : { H: look.H, S: SKIN, E: '#1d1b26', m: '#c98a78', G: '#1d1b26', C: look.C, P: look.P, B: look.B, T: look.T || look.H };
    const sheet = {};
    for (const d of DIRS) for (const f of FRAMES) for (const blink of [false, true]) {
      sheet[d + ':' + f + ':' + (blink ? 1 : 0)] = renderSprite(template(d, f, { ...look, blink }), palette);
    }
    return sheet;
  }

  // Walk cycle: a, stand, b, stand. ~130 ms per frame at full speed.
  const WALK_MS = 130;
  function walkFrame(ms) { return ['a', 'stand', 'b', 'stand'][Math.floor(ms / WALK_MS) % 4]; }

  function drawSprite(ctx, spr, x, y) {
    for (const [px, py, c] of spr.px) { ctx.fillStyle = c; ctx.fillRect(x + px, y + py, 1, 1); }
  }

  return { TILE, MAP, W, H, SPOTS, SOURCE_SPOT, NPC_HOME, PLAYER_START, tileAt, solidTile, boxHitsSolid, moveWithSlide,
    findPath, standTiles, DETECTIVE_HOME, MOVE, stepVelocity, template, renderSprite, LOOKS, buildSheet, walkFrame, WALK_MS, drawSprite, DIRS };
});
