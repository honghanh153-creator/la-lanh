// Lá pixel: Mầm xanh drawn on a 48×48 grid from formulas, no image files (owner 14.11.2026:
// "Lá pixel là Mầm xanh, làm bằng code"). A pose is a handful of numbers; drawPose turns it into
// palette indices and pixelPaths merges equal colours into one <path> each.

export const GRID = 48;

/** Palette taken from the Mầm xanh companion (AuraSproutCompanion) so both read as one character. */
export const PALETTE = [
  "", // 0 transparent
  "#24123f", // 1 ink
  "#3ff23a", // 2 body
  "#13c24a", // 3 body shade
  "#b6ff2a", // 4 body light
  "#f4ffd2", // 5 gloss
  "#f2ffc4", // 6 belly
  "#2fd94a", // 7 stem
  "#1fc94a", // 8 leaf
  "#7dff3a", // 9 leaf light
  "#ffffff", // 10 white
  "#ff9cc6", // 11 cheek
  "#ff5a4a", // 12 red
  "#4b278f", // 13 glass
  "#fff9e9", // 14 cup
  "#e9fbff", // 15 steam
  "#2a1660", // 16 shadow
  "#dfff4f", // 17 sparkle
  "#9fe3ff", // 18 sweat
] as const;

/** Shadow is drawn see-through, like the round companion's ground shadow. */
export const PALETTE_OPACITY: Partial<Record<number, number>> = { 16: 0.22, 15: 0.85 };

export type Eyes = "open" | "wide" | "closed" | "happy" | "soft";
export type Mouth = "smile" | "flat" | "o" | "open" | "tongue";
export type Arm = "down" | "up" | "up2" | "hold";

/** One picture of Lá. Every field is optional; {} is the rest pose. */
export type Pose = {
  /** Body offset up (-) or down (+), in pixels. */
  dy?: number;
  /** Squash (+, wider and shorter) or stretch (-), in pixels, -2..2. */
  sq?: number;
  /** Lean of the top of the body, in pixels, -2..2. */
  lean?: number;
  eyes?: Eyes;
  mouth?: Mouth;
  arm?: Arm;
  /** Tilt of the sprout leaves, -1..1. */
  leaf?: number;
  /** A small heart this many pixels above its start; absent = no heart. */
  heart?: number;
  /** Sunglasses this many pixels below the eyes; absent = no glasses. */
  glasses?: number;
  /** A cup held in front; the value lifts it (pixels up). */
  cup?: number;
  /** Steam above the cup, phase 0..2. */
  steam?: number;
  sweat?: boolean;
  sparkle?: boolean;
};

const STAMPS: Record<string, readonly string[]> = {
  leaves: [".98...89.", "8889.9888", ".888.888.", "....7...."],
  eye_open: ["1a", "11", "11"],
  eye_wide: ["111", "1a1", "111"],
  eye_closed: ["...", "1.1", ".1."],
  eye_happy: [".1.", "1.1", "..."],
  eye_soft: ["...", "111", "..."],
  mouth_smile: ["1.1", ".1."],
  mouth_flat: ["111"],
  mouth_o: [".1.", "1.1", ".1."],
  mouth_open: ["111", "1c1", ".1."],
  mouth_tongue: ["111", ".c."],
  heart: ["cc.cc", "ccccc", ".ccc.", "..c.."],
  glasses: ["11111111111111", "1ddddd11ddddd1", "1ddad1..1ddad1", ".1111....1111."],
  cup: ["11111..", "1eee111", "1eee1.1", "1eee111", ".111..."],
  steam0: [".f.", "f..", ".f."],
  steam1: ["..f", ".f.", "f.."],
  steam2: ["f..", ".f.", "..f"],
  sweat: [".i", "ii", "ii"],
  sparkle: [".h.", "hhh", ".h."],
};

/** Stamp characters: digits are palette indices, letters a–i are 10–18. */
function colourOf(ch: string): number {
  if (ch >= "0" && ch <= "9") return Number(ch);
  const code = ch.charCodeAt(0) - 97;
  return code >= 0 && code <= 8 ? 10 + code : 0;
}

function stamp(grid: Uint8Array, name: string, x0: number, y0: number, shear = 0): void {
  const rows = STAMPS[name];
  rows.forEach((row, ry) => {
    const shift = Math.round((shear * (rows.length - 1 - ry)) / 2);
    for (let rx = 0; rx < row.length; rx += 1) {
      const colour = colourOf(row[rx]);
      const x = x0 + rx + shift;
      const y = y0 + ry;
      if (colour && x >= 0 && x < GRID && y >= 0 && y < GRID) grid[y * GRID + x] = colour;
    }
  });
}

/** Mark the pixels just outside the figure with ink, so the silhouette reads at any size. */
function outline(grid: Uint8Array): void {
  const solid = grid.map((colour) => (colour ? 1 : 0));
  for (let y = 0; y < GRID; y += 1) {
    for (let x = 0; x < GRID; x += 1) {
      if (solid[y * GRID + x]) continue;
      const near = (x > 0 && solid[y * GRID + x - 1]) || (x < GRID - 1 && solid[y * GRID + x + 1])
        || (y > 0 && solid[(y - 1) * GRID + x]) || (y < GRID - 1 && solid[(y + 1) * GRID + x]);
      if (near) grid[y * GRID + x] = 1;
    }
  }
}

/** Draw one pose as GRID×GRID palette indices (row-major). */
export function drawPose(pose: Pose = {}): Uint8Array {
  const grid = new Uint8Array(GRID * GRID);
  const sq = Math.max(-2, Math.min(2, pose.sq ?? 0));
  const rx = 13 + sq;
  const ry = 11 - sq;
  const bottom = 42 + (pose.dy ?? 0);
  const cy = bottom - ry;
  const cx = 24;
  const lean = pose.lean ?? 0;
  const shiftAt = (y: number) => Math.round((lean * (bottom - y)) / (2 * ry));

  // Ground shadow stays on the floor while Lá hops, and shrinks as Lá goes up.
  const lift = Math.max(0, -(pose.dy ?? 0));
  const shadowRx = Math.max(6, 12 - lift);
  for (let x = cx - shadowRx; x <= cx + shadowRx; x += 1) {
    grid[44 * GRID + x] = 16;
    if (Math.abs(x - cx) < shadowRx - 2) grid[45 * GRID + x] = 16;
  }
  const shadow = grid.slice();

  const figure = new Uint8Array(GRID * GRID);
  for (let y = 0; y < GRID; y += 1) {
    for (let x = 0; x < GRID; x += 1) {
      const sx = x - shiftAt(y);
      const nx = (sx + 0.5 - cx) / rx;
      const ny = (y + 0.5 - cy) / ry;
      if (nx * nx + ny * ny > 1) continue;
      let colour = 2;
      if (nx * 0.6 + ny * 0.8 > 0.62) colour = 3;
      else if (nx * 0.6 + ny * 0.8 < -0.72) colour = 4;
      const bx = (sx + 0.5 - cx) / 6;
      const by = (y + 0.5 - (cy + 6)) / 3.2;
      if (bx * bx + by * by <= 1) colour = 6;
      const gx = (sx + 0.5 - (cx - 7)) / 2.2;
      const gy = (y + 0.5 - (cy - 6)) / 1.4;
      if (gx * gx + gy * gy <= 1) colour = 5;
      figure[y * GRID + x] = colour;
    }
  }

  const top = cy - ry;
  const stemX = cx + shiftAt(top);
  for (let y = top - 3; y < top + 1; y += 1) figure[y * GRID + stemX] = 7;
  stamp(figure, "leaves", stemX - 4, top - 7, pose.leaf ?? 0);

  const arm = pose.arm ?? "down";
  const armY = cy + 3;
  const leftX = cx - rx - 1 + shiftAt(armY);
  const rightX = cx + rx + shiftAt(armY);
  const put = (x: number, y: number) => { figure[y * GRID + x] = 2; };
  if (arm === "hold") {
    put(leftX + 3, armY + 2); put(leftX + 4, armY + 2);
    put(rightX - 3, armY + 2); put(rightX - 4, armY + 2);
  } else {
    put(leftX, armY); put(leftX, armY + 1);
    if (arm === "up") { put(rightX + 1, armY - 2); put(rightX + 2, armY - 3); put(rightX + 2, armY - 4); }
    else if (arm === "up2") { put(rightX + 1, armY - 2); put(rightX + 1, armY - 3); put(rightX + 1, armY - 4); }
    else { put(rightX, armY); put(rightX, armY + 1); }
  }

  outline(figure);
  for (let i = 0; i < grid.length; i += 1) grid[i] = figure[i] || shadow[i];

  const faceShift = shiftAt(cy);
  const eyeY = cy - 3;
  const eyes = pose.eyes ?? "open";
  const eyeName = `eye_${eyes}`;
  const eyeWidth = STAMPS[eyeName][0].length;
  stamp(grid, eyeName, cx - 6 + faceShift + (eyeWidth === 2 ? 1 : 0), eyeY);
  stamp(grid, eyeName, cx + 3 + faceShift, eyeY);
  grid[(cy + 1) * GRID + cx - 9 + faceShift] = 11;
  grid[(cy + 1) * GRID + cx - 8 + faceShift] = 11;
  grid[(cy + 1) * GRID + cx + 8 + faceShift] = 11;
  grid[(cy + 1) * GRID + cx + 9 + faceShift] = 11;
  stamp(grid, `mouth_${pose.mouth ?? "smile"}`, cx - 1 + faceShift, cy + 1);

  if (pose.glasses !== undefined) stamp(grid, "glasses", cx - 7 + faceShift, eyeY - 1 + pose.glasses);
  if (pose.heart !== undefined) stamp(grid, "heart", cx + 10, top - 2 - pose.heart);
  if (pose.cup !== undefined) {
    const cupY = cy + 4 - pose.cup;
    stamp(grid, "cup", cx - 3 + faceShift, cupY);
    if (pose.steam !== undefined) stamp(grid, `steam${Math.abs(Math.round(pose.steam)) % 3}`, cx - 2 + faceShift, cupY - 4);
  }
  if (pose.sweat) stamp(grid, "sweat", cx + rx - 1 + faceShift, top + 2);
  if (pose.sparkle) {
    stamp(grid, "sparkle", cx - rx - 4, top - 2);
    stamp(grid, "sparkle", cx + rx + 2, top + 4);
  }
  return grid;
}

/** One SVG path per colour: each horizontal run becomes a 1-pixel-tall rectangle. */
export function pixelPaths(grid: Uint8Array): Array<{ colour: number; d: string }> {
  const parts = new Map<number, string[]>();
  for (let y = 0; y < GRID; y += 1) {
    let x = 0;
    while (x < GRID) {
      const colour = grid[y * GRID + x];
      let end = x + 1;
      while (end < GRID && grid[y * GRID + end] === colour) end += 1;
      if (colour) {
        const list = parts.get(colour) ?? [];
        list.push(`M${x} ${y}h${end - x}v1h${x - end}z`);
        parts.set(colour, list);
      }
      x = end;
    }
  }
  return [...parts.entries()].sort((a, b) => a[0] - b[0]).map(([colour, list]) => ({ colour, d: list.join("") }));
}
