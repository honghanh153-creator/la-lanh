// Pure drawing helpers shared by the two companion prototypes. Deterministic
// from (seed, level, hour) so the same inputs always draw the same picture.
import type { MoonPhase } from "../la/moonPhase";

export const BRAND = {
  cream: "#f7f4eb",
  creamText: "#fff9e9",
  violet: "#4b278f",
  violetDeep: "#2a1660",
  lime: "#dfff4f",
  coral: "#ff6b4a",
} as const;

/** Default seed when the integrator has none yet: a fixed constant, not personal data. */
export const DEFAULT_COMPANION_SEED = 0x1a2b3c4d;

/** Stateless hash → [0, 1). Same (seed, a, b) always gives the same number. */
export function hashRandom(seed: number, a: number, b = 0): number {
  let h = (seed ^ Math.imul(a + 0x9e3779b9, 0x85ebca6b) ^ Math.imul(b + 0x7f4a7c15, 0xc2b2ae35)) >>> 0;
  h = Math.imul(h ^ (h >>> 16), 0x7feb352d);
  h = Math.imul(h ^ (h >>> 15), 0x846ca68b);
  h ^= h >>> 16;
  return (h >>> 0) / 0x100000000;
}

export function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

export function smoothstep(edge0: number, edge1: number, x: number): number {
  const t = clamp01((x - edge0) / (edge1 - edge0));
  return t * t * (3 - 2 * t);
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function hexToRgb(hex: string): [number, number, number] {
  const value = parseInt(hex.slice(1), 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

export function mixColor(a: string, b: string, t: number): string {
  const ca = hexToRgb(a);
  const cb = hexToRgb(b);
  const out = ca.map((channel, i) => Math.round(lerp(channel, cb[i], clamp01(t))));
  return `#${out.map((channel) => channel.toString(16).padStart(2, "0")).join("")}`;
}

/** Sample a 24h keyframe table (hours ascending in [0, 24]) with wrap-around. */
export function sampleByHour<T extends readonly string[]>(table: ReadonlyArray<readonly [number, T]>, hour: number): string[] {
  const h = ((hour % 24) + 24) % 24;
  for (let i = 0; i < table.length - 1; i += 1) {
    const [h0, c0] = table[i];
    const [h1, c1] = table[i + 1];
    if (h >= h0 && h <= h1) {
      const t = h1 === h0 ? 0 : smoothstep(0, 1, (h - h0) / (h1 - h0));
      return c0.map((color, j) => mixColor(color, c1[j], t));
    }
  }
  return [...table[0][1]];
}

type Sky = readonly [string, string, string];

/** Top, middle, horizon. The prettiest window is 18–21h; late night is deep and quiet. */
export const SKY_TABLE: ReadonlyArray<readonly [number, Sky]> = [
  [0, ["#090620", "#140d36", "#21184a"]],
  [4.6, ["#0d0928", "#1d1450", "#2c1d63"]],
  [5.6, ["#2b1d63", "#7a4f9e", "#f4a7a4"]],
  [6.6, ["#7c74d6", "#f5b5cc", "#ffd7a3"]],
  [8, ["#8ccaf7", "#cde9ff", "#fff1d2"]],
  [12, ["#5bb6f5", "#b9e3ff", "#f7f4eb"]],
  [15.5, ["#73aeea", "#d3e2f6", "#ffe6ad"]],
  [17.4, ["#6553c6", "#f19a82", "#ffcd6c"]],
  [18.6, ["#3a2483", "#8e4fb4", "#ff9a8c"]],
  [20, ["#24135e", "#4b278f", "#9a5fc7"]],
  [21.5, ["#120b33", "#24164f", "#3a2470"]],
  [24, ["#090620", "#140d36", "#21184a"]],
];

/** Leaf body, leaf edge, trunk, hill. */
export const PLANT_TABLE: ReadonlyArray<readonly [number, readonly [string, string, string, string]]> = [
  [0, ["#2b2f52", "#4d5a7a", "#2a1a4f", "#1a1238"]],
  [4.8, ["#2b2f52", "#4d5a7a", "#2a1a4f", "#1a1238"]],
  [6.4, ["#7fbf6a", "#ffc7b8", "#5a3a8f", "#7c6aa8"]],
  [9, ["#8fd14f", "#d9ff7a", "#4c2e8e", "#9ccf5c"]],
  [13, ["#9ade45", "#efff9a", "#4c2e8e", "#a9d65e"]],
  [16.5, ["#b6c63d", "#ffe27a", "#5b2f86", "#c7b35a"]],
  [18.6, ["#7a9a4a", "#ffb08a", "#3f2276", "#6b4a8f"]],
  [20, ["#5b3fa8", "#dfff4f", "#2f1a66", "#3a2470"]],
  [21.6, ["#33305e", "#7d8a5a", "#24154f", "#1d1440"]],
  [24, ["#2b2f52", "#4d5a7a", "#2a1a4f", "#1a1238"]],
];

/** Lit part of a moon disc (same geometry as MoonGlyph, any centre and radius). */
export function moonLitPath(cx: number, cy: number, r: number, phase: Pick<MoonPhase, "illumination" | "waxing">): string | null {
  if (phase.illumination <= 0.02) return null;
  const rx = Math.max(0.01, r * Math.abs(1 - 2 * phase.illumination));
  const crescent = phase.illumination < 0.5;
  const outer = phase.waxing ? 1 : 0;
  const inner = phase.waxing ? (crescent ? 0 : 1) : (crescent ? 1 : 0);
  return `M ${cx} ${cy - r} A ${r} ${r} 0 0 ${outer} ${cx} ${cy + r} A ${rx.toFixed(2)} ${r} 0 0 ${inner} ${cx} ${cy - r} Z`;
}

/** Position on the sky arc for a body that rises at `rise` and sets at `set` (hours, may wrap past 24). */
export function arcPosition(hour: number, rise: number, set: number, box: { x0: number; x1: number; top: number; horizon: number }): { x: number; y: number; t: number; up: boolean } {
  let h = hour;
  if (set > 24 && h < rise) h += 24;
  const t = (h - rise) / (set - rise);
  const up = t >= 0 && t <= 1;
  const tt = clamp01(t);
  return {
    x: lerp(box.x0, box.x1, tt),
    y: box.horizon - Math.sin(tt * Math.PI) * (box.horizon - box.top),
    t: tt,
    up,
  };
}

const MAX_LEVEL = 6;

export type Branch = { id: number; depth: number; x1: number; y1: number; cx: number; cy: number; x2: number; y2: number; width: number; angle: number };
export type Tip = { id: number; x: number; y: number; angle: number; depth: number };
export type Tree = { branches: Branch[]; tips: Tip[]; leaves: Array<{ id: number; x: number; y: number; angle: number; scale: number; group: number }> };

/**
 * Procedural tree. Each node's randomness comes from hashRandom(seed, nodeId),
 * not a running sequence, so raising the level only adds branches: the shape
 * a user already knows stays recognisable.
 */
export function buildTree(seed: number, level: number, base: { x: number; y: number }, size: { height: number; halfWidth: number }): Tree {
  const maxDepth = [0, 1, 2, 3, 3, 4, 4][Math.min(MAX_LEVEL, Math.max(0, level))];
  let branches: Branch[] = [];
  const tips: Tip[] = [];

  const grow = (id: number, depth: number, x: number, y: number, angle: number, length: number, width: number) => {
    const bend = (hashRandom(seed, id, 1) - 0.5) * 0.5;
    const x2 = x + Math.sin(angle) * length;
    const y2 = y - Math.cos(angle) * length;
    const mid = angle + bend;
    const cx = x + Math.sin(mid) * length * 0.55;
    const cy = y - Math.cos(mid) * length * 0.55;
    branches.push({ id, depth, x1: x, y1: y, cx, cy, x2, y2, width, angle });
    if (depth >= maxDepth) {
      tips.push({ id, x: x2, y: y2, angle, depth });
      return;
    }
    const three = level >= 4 && depth < 2 && hashRandom(seed, id, 2) > 0.5;
    const count = three ? 3 : 2;
    for (let i = 0; i < count; i += 1) {
      const side = count === 2 ? (i === 0 ? -1 : 1) : i - 1;
      const spread = 0.34 + hashRandom(seed, id, 10 + i) * 0.32;
      const childAngle = angle * 0.5 + side * spread + (hashRandom(seed, id, 20 + i) - 0.5) * 0.2;
      const childLength = length * (0.7 + hashRandom(seed, id, 30 + i) * 0.14);
      grow(id * 4 + i + 1, depth + 1, x2, y2, childAngle, childLength, Math.max(1.3, width * 0.64));
    }
  };

  grow(1, 0, 0, 0, (hashRandom(seed, 0, 3) - 0.5) * 0.12, 40, 3.2 + level * 1.15);

  // Fit to the space this level is allowed: the tree gets taller and wider
  // with level, while leaves keep a constant size.
  let minY = 0;
  let maxDx = 1;
  for (const b of branches) {
    minY = Math.min(minY, b.y2, b.cy);
    maxDx = Math.max(maxDx, Math.abs(b.x2), Math.abs(b.cx));
  }
  const k = Math.min(size.height / -minY, size.halfWidth / maxDx);
  const fit = (x: number, y: number) => [base.x + x * k, base.y + y * k] as const;
  branches = branches.map((b) => {
    const [x1, y1] = fit(b.x1, b.y1);
    const [cx, cy] = fit(b.cx, b.cy);
    const [x2, y2] = fit(b.x2, b.y2);
    return { ...b, x1, y1, cx, cy, x2, y2 };
  });
  const fittedTips = tips.map((tip) => {
    const [x, y] = fit(tip.x, tip.y);
    return { ...tip, x, y };
  });

  const leaves: Tree["leaves"] = [];
  const perTip = fittedTips.length <= 2 ? 3 : fittedTips.length <= 12 ? 2 : 1;
  fittedTips.forEach((tip, tipIndex) => {
    for (let i = 0; i < perTip; i += 1) {
      const spread = perTip === 1 ? 0 : perTip === 2 ? (i === 0 ? -0.8 : 0.8) : (i - 1) * 0.95;
      const r = hashRandom(seed, tip.id, 40 + i);
      leaves.push({
        id: tip.id * 8 + i,
        x: tip.x,
        y: tip.y,
        angle: (tip.angle + spread + (r - 0.5) * 0.5) * (180 / Math.PI),
        scale: 0.8 + r * 0.4 + (level === 0 ? 0.3 : 0),
        group: (tipIndex + i) % 3,
      });
    }
  });
  // Side leaves along outer branches make the canopy fuller as it grows.
  if (level >= 2) {
    branches.filter((b) => b.depth === Math.max(1, maxDepth - 1)).forEach((b, index) => {
      const r = hashRandom(seed, b.id, 50);
      leaves.push({
        id: b.id * 8 + 7,
        x: lerp(b.x1, b.x2, 0.55),
        y: lerp(b.y1, b.y2, 0.55),
        angle: b.angle * (180 / Math.PI) + (r > 0.5 ? 62 : -62),
        scale: 0.7 + r * 0.3,
        group: index % 3,
      });
    });
  }
  return { branches, tips: fittedTips, leaves };
}

export function branchPath(branches: Branch[]): string {
  return branches.map((b) => `M${b.x1.toFixed(1)} ${b.y1.toFixed(1)}Q${b.cx.toFixed(1)} ${b.cy.toFixed(1)} ${b.x2.toFixed(1)} ${b.y2.toFixed(1)}`).join("");
}

/** Leaf shape pointing up from its base at (0, 0), length ~14. */
export const LEAF_PATH = "M0 0C-6 -3 -7 -10 0 -15C7 -10 6 -3 0 0Z";

/** 0 awake … 1 asleep. Falls asleep 20:30–21:30, wakes 05:00–06:24; continuous across 05:00. */
export function sleepiness(hour: number): number {
  if (hour >= 20.5) return smoothstep(20.5, 21.5, hour);
  if (hour < 5) return 1;
  return 1 - smoothstep(5, 6.4, hour);
}

/** 0 day … 1 full night sky (stars, moon glow). */
export function nightness(hour: number): number {
  return hour < 12 ? 1 - smoothstep(4.8, 6.4, hour) : smoothstep(18.2, 20.4, hour);
}

/** Evening glow window, the prettiest time on purpose (18–21h), fading before late night. */
export function eveningGlow(hour: number): number {
  return smoothstep(18.3, 19.3, hour) * (1 - smoothstep(21, 22, hour));
}

export function hslToHex(h: number, s: number, l: number): string {
  const sat = s / 100;
  const light = l / 100;
  const k = (n: number) => (n + h / 30) % 12;
  const a = sat * Math.min(light, 1 - light);
  const f = (n: number) => light - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return `#${[f(0), f(8), f(4)].map((x) => Math.round(x * 255).toString(16).padStart(2, "0")).join("")}`;
}

/** Five round petals around (0, 0) as one path. */
export function petalsPath(count: number, distance: number, radius: number): string {
  let d = "";
  for (let i = 0; i < count; i += 1) {
    const a = (i / count) * Math.PI * 2 - Math.PI / 2;
    const x = Math.cos(a) * distance;
    const y = Math.sin(a) * distance;
    d += `M${(x - radius).toFixed(2)} ${y.toFixed(2)}a${radius} ${radius} 0 1 0 ${(radius * 2).toFixed(2)} 0a${radius} ${radius} 0 1 0 ${(-radius * 2).toFixed(2)} 0`;
  }
  return d;
}

/** Union of circles as one path (clouds, puffs). */
export function circlesPath(circles: ReadonlyArray<readonly [number, number, number]>): string {
  return circles.map(([x, y, r]) => `M${x - r} ${y}a${r} ${r} 0 1 0 ${r * 2} 0a${r} ${r} 0 1 0 ${-r * 2} 0`).join("");
}

/** Four-point sparkle centred at (0, 0). */
export const SPARKLE_PATH = "M0 -6L1.4 -1.4L6 0L1.4 1.4L0 6L-1.4 1.4L-6 0L-1.4 -1.4Z";
/** Small flame centred near (0, 0). */
export const FLAME_PATH = "M0 4C-3 4 -4 1.5 -3 -0.8C-2.4 -2.2 -1.2 -2.6 -1 -4.6C0.6 -3.6 1 -2.4 0.8 -1.4C1.4 -1.8 1.8 -2.4 1.9 -3C3.4 -1.4 3.6 0.6 3 2C2.4 3.3 1.3 4 0 4Z";
/** Five-point star (Trung Thu star lantern) radius ~7. */
export const STAR_LANTERN_PATH = "M0 -7L1.7 -2.3L6.7 -2.2L2.7 0.9L4.1 5.7L0 2.9L-4.1 5.7L-2.7 0.9L-6.7 -2.2L-1.7 -2.3Z";

/** Sample a numeric 24h keyframe table (hours ascending in [0, 24]). */
export function sampleNumber(table: ReadonlyArray<readonly [number, number]>, hour: number): number {
  const h = ((hour % 24) + 24) % 24;
  for (let i = 0; i < table.length - 1; i += 1) {
    const [h0, v0] = table[i];
    const [h1, v1] = table[i + 1];
    if (h >= h0 && h <= h1) return lerp(v0, v1, h1 === h0 ? 0 : smoothstep(0, 1, (h - h0) / (h1 - h0)));
  }
  return table[0][1];
}
