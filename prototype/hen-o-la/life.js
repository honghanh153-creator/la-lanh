// Shared café life for the evening (game.js) and the everyday café (quan.js): the window benches, the
// reading nook and Bơ the café dog. Browser only; uses World for the map and paths.
(function (root) {
  'use strict';
  const W = root.World, T = W.TILE;
  const feetOf = (tx, ty) => ({ x: tx * T + 8, y: ty * T + 12 });
  const tileOf = p => [Math.floor(p.x / T), Math.floor((p.y - 1) / T)];
  const onList = (list, tx, ty) => list.some(([x, y]) => x === tx && y === ty);
  const windowSeatAt = (tx, ty) => onList(W.WINDOW_SEATS, tx, ty);
  const nookAt = (tx, ty) => onList(W.NOOK, tx, ty);

  // Sit on a window bench (facing the rain) or lie on a bean bag. b must already stand on that tile.
  function sitWindow(b) {
    const [tx, ty] = tileOf(b);
    if (!windowSeatAt(tx, ty)) return false;
    Object.assign(b, feetOf(tx, ty), { sit: true, seatKind: 'window', lie: false, act: null, path: null, goingTo: null, dir: 'up' });
    return true;
  }
  function lieDown(b) {
    const [tx, ty] = tileOf(b);
    if (!nookAt(tx, ty)) return false;
    Object.assign(b, feetOf(tx, ty), { lie: true, sit: false, seatKind: null, act: null, path: null, goingTo: null });
    return true;
  }
  // First bench or bean bag nobody uses or is walking to.
  function freeSpot(list, people, except) {
    const taken = new Set();
    for (const b of people) if (b !== except && (b.sit || b.lie || b.goingTo)) { const [x, y] = b.goingTo || tileOf(b); taken.add(x + ',' + y); }
    return list.filter(([x, y]) => !taken.has(x + ',' + y));
  }

  // Bơ wanders, naps in the bed, trots over to sit beside you and wags when petted.
  // env: { clock(), rand(), still(), particles, me() }
  function createDog(env, name) {
    const dog = Object.assign({ id: 'dog', isDog: true, name, dir: 'right', path: null, then: null, idle: 2, moving: false, walkMs: 0, sitting: true, petted: 0, hop: 0, bubble: null }, feetOf(...W.DOG_BED));
    const pick = list => list[Math.floor(env.rand() * list.length)];
    function walk(tx, ty, then) {
      const path = W.findPath(tileOf(dog), [tx, ty]);
      if (!path) return;
      dog.sitting = false; dog.path = path.slice(1); dog.then = then || null;
      if (!dog.path.length) { dog.path = null; if (then) then(); }
    }
    function follow(dt) {
      const [tx, ty] = dog.path[0], goal = feetOf(tx, ty);
      const dx = goal.x - dog.x, dy = goal.y - dog.y, d = Math.hypot(dx, dy), step = 34 * dt;
      if (d <= step) { dog.x = goal.x; dog.y = goal.y; dog.path.shift(); if (!dog.path.length) { dog.path = null; const t = dog.then; dog.then = null; if (t) t(); } }
      else { dog.x += dx / d * step; dog.y += dy / d * step; }
      if (Math.abs(dx) > 0.5) dog.dir = dx > 0 ? 'right' : 'left';
      dog.moving = true;
    }
    function pet(by) {
      dog.path = null; dog.then = null; dog.sitting = true; dog.petted = env.clock() + 3.5; dog.idle = 4;
      dog.dir = by.x < dog.x ? 'left' : 'right';
      if (!env.still()) { dog.hop = 2; for (let i = 0; i < 3; i++) env.particles.push({ kind: 'heart', x: dog.x - 2 + i * 3, y: dog.y - 16, vx: 0, vy: -8, life: 1 + i * 0.2 }); }
    }
    function think(dt) {
      if (dog.hop > 0) dog.hop = Math.max(0, dog.hop - dt * 8);
      dog.walkMs = dog.moving ? dog.walkMs + dt * 1000 : 0;
      dog.moving = false;
      if (dog.path) { follow(dt); return; }
      if (dog.petted > env.clock()) return;
      dog.idle -= dt; if (dog.idle > 0) return;
      dog.idle = 3 + env.rand() * 5;
      const r = env.rand(), me = env.me();
      if (r < 0.3 && me) {
        const st = W.standTiles(...tileOf(me), tileOf(dog)).find(([x, y]) => !W.solidTile(x, y));
        if (st) walk(st[0], st[1], () => { dog.sitting = true; dog.dir = me.x < dog.x ? 'left' : 'right'; });
      } else if (r < 0.5) walk(W.DOG_BED[0], W.DOG_BED[1], () => { dog.sitting = true; dog.idle = 8 + env.rand() * 6; });
      else { const t = pick(W.freeTiles().filter(([, y]) => y >= 3)); walk(t[0], t[1], () => { dog.sitting = env.rand() < 0.5; }); }
    }
    // A free tile next to the dog, nearest to `from`.
    function besideTile(from) { return W.standTiles(...tileOf(dog), from).find(([x, y]) => !W.solidTile(x, y)); }
    return { dog, think, pet, besideTile };
  }

  root.Life = { feetOf, tileOf, windowSeatAt, nookAt, sitWindow, lieDown, freeSpot, createDog };
})(globalThis);
