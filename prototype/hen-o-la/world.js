// Hẹn ở Lá: the rainy café room. Same tile grid, sliding collision and A* as game lab 14,
// but on its own map. Sprites come from ../game-lab-14/engine.js (Engine.buildSheet).
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.World = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const TILE = 16;
  // 15 x 10 tiles = 240 x 160 internal pixels.
  // W wall, w rainy window, C counter, p plant, K bookshelf, T table, m cat cushion, P old piano, d door, . floor.
  const MAP = [
    'WWWWWWWWWWWWWWW',
    'WWwwWWwwWWwwWWW',
    'CCCCC...p....KK',
    '...............',
    '...T...T...T...',
    '...............',
    '..............m',
    '...T...T...T...',
    'P.............p',
    'WWWWWWWdWWWWWWW'
  ];
  const W = MAP[0].length, H = MAP.length;
  const SOLID = new Set(['W', 'w', 'C', 'p', 'K', 'T', 'm', 'P', 'd']);

  // Places you can do something at. act is the key in Hen.ACTS that standing here unlocks.
  const SPOTS = {
    counter: { tx: 4, ty: 2, label: 'Quầy · Cô Lá', act: 'goido' },
    window1: { tx: 6, ty: 1, label: 'Cửa sổ mưa', act: 'ngammua' },
    window2: { tx: 10, ty: 1, label: 'Cửa sổ mưa', act: 'ngammua' },
    plant1: { tx: 8, ty: 2, label: 'Chậu trầu bà', act: 'tuoicay' },
    plant2: { tx: 14, ty: 8, label: 'Chậu lưỡi hổ', act: 'tuoicay' },
    shelf: { tx: 13, ty: 2, label: 'Kệ sách', act: 'docsach' },
    cat: { tx: 14, ty: 6, label: 'Mèo Mướp', act: 'vuotmeo' },
    piano: { tx: 0, ty: 8, label: 'Đàn piano cũ', act: 'danhdan' }
  };

  // Six two-seat tables for the rotation. Seats are the free tiles left and right of each table.
  const TABLES = [[3, 4], [7, 4], [11, 4], [3, 7], [7, 7], [11, 7]].map(([x, y], i) => ({ n: i + 1, tx: x, ty: y, seats: [[x - 1, y], [x + 1, y]] }));
  const ENTRY = [7, 8];
  const HOST = { tx: 2, ty: 2 }; // drawn standing behind the counter
  const LOUNGE = 2; // index of the window-side table used for "Ly cuối"

  function tileAt(tx, ty) { return tx < 0 || ty < 0 || tx >= W || ty >= H ? 'W' : MAP[ty][tx]; }
  function solidTile(tx, ty) { return SOLID.has(tileAt(tx, ty)); }

  function boxHitsSolid(x, y, w, h) {
    const x0 = Math.floor(x / TILE), x1 = Math.floor((x + w - 0.01) / TILE);
    const y0 = Math.floor(y / TILE), y1 = Math.floor((y + h - 0.01) / TILE);
    for (let ty = y0; ty <= y1; ty++) for (let tx = x0; tx <= x1; tx++) if (solidTile(tx, ty)) return true;
    return false;
  }

  // Axis-separated move so the body slides along furniture instead of sticking.
  function moveWithSlide(body, dx, dy) {
    let { x, y } = body;
    if (dx && !boxHitsSolid(x + dx, y, body.w, body.h)) x += dx;
    if (dy && !boxHitsSolid(x, y + dy, body.w, body.h)) y += dy;
    return { x, y };
  }

  // 4-direction A* on tiles. People never block each other, so only furniture matters.
  function findPath(from, to) {
    const key = (x, y) => x + ',' + y;
    if (solidTile(to[0], to[1])) return null;
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
        if (solidTile(nx, ny)) continue;
        const k = key(nx, ny), ng = g + 1;
        if (cost.has(k) && cost.get(k) <= ng) continue;
        cost.set(k, ng); came.set(k, key(x, y));
        open.push([nx, ny, ng, ng + Math.abs(to[0] - nx) + Math.abs(to[1] - ny)]);
      }
    }
    return null;
  }

  // Free tiles next to an object, nearest first.
  function standTiles(tx, ty, near) {
    const out = [[tx, ty + 1], [tx - 1, ty], [tx + 1, ty], [tx, ty - 1]].filter(([x, y]) => !solidTile(x, y));
    if (near) out.sort((a, b) => Math.hypot(a[0] - near[0], a[1] - near[1]) - Math.hypot(b[0] - near[0], b[1] - near[1]));
    return out;
  }

  // Spot whose stand tile the given tile is, if any.
  function spotAt(tx, ty) {
    for (const [name, s] of Object.entries(SPOTS)) if (standTiles(s.tx, s.ty).some(([x, y]) => x === tx && y === ty)) return name;
    return null;
  }

  function freeTiles() {
    const out = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (!solidTile(x, y)) out.push([x, y]);
    return out;
  }

  return { TILE, MAP, W, H, SPOTS, TABLES, ENTRY, HOST, LOUNGE, tileAt, solidTile, boxHitsSolid, moveWithSlide, findPath, standTiles, spotAt, freeTiles };
});
