import type { ShareFormat, ZodiacSign } from "../../shared/api/client";

/**
 * Pure SVG builder for every Lá Lành share image (note card, Lá Khai Sinh, public preview).
 *
 * Privacy contract: the builder only receives display strings that are already safe to share
 * (headline, one supporting line, sticker labels). It never accepts birth date/time/place,
 * question text, email, ids or tokens, so the output cannot contain them.
 */

export type ShareElement = "fire" | "earth" | "air" | "water";

export type ShareArtSpec = {
  /** Small eyebrow above the hook, e.g. "Note hôm nay". */
  kicker: string;
  /** The one bold line. Never truncated; the type shrinks until every word fits. */
  hook: string;
  /** At most one short supporting line. */
  support?: string | null;
  /** Main lime sticker, e.g. "Mặt Trời Song Tử · Khí". */
  badge: string;
  /** Optional second sticker, e.g. "Vibe · Lanh". */
  tag?: string | null;
  element: ShareElement | null;
  /** When set, the hero disc shows the zodiac glyph; otherwise the element emblem. */
  sign?: ZodiacSign | null;
  footer: string;
};

export const SHARE_PRIVACY_FOOTER = "Không kèm ngày / giờ / nơi sinh";

export const elementNames: Record<ShareElement, string> = {
  fire: "Lửa",
  earth: "Đất",
  air: "Khí",
  water: "Nước",
};

export const elementBySign: Record<ZodiacSign, ShareElement> = {
  aries: "fire", leo: "fire", sagittarius: "fire",
  taurus: "earth", virgo: "earth", capricorn: "earth",
  gemini: "air", libra: "air", aquarius: "air",
  cancer: "water", scorpio: "water", pisces: "water",
};

/**
 * Presentation-only colour lookup. Persona labels are produced server-side and each one belongs
 * to exactly one element in both Vibe (sun sign) and Aura (dominant element + modality) mapping.
 */
const elementByPersonaLabel: Record<string, ShareElement> = {
  "Nóng": "fire", "Rực": "fire", "Phiêu": "fire",
  "Bền": "earth", "Gọn": "earth", "Chắc": "earth",
  "Lanh": "air", "Duyên": "air", "Khác": "air",
  "Mềm": "water", "Sâu": "water", "Mộng": "water",
};

export function elementForPersonaLabel(label: string | null | undefined): ShareElement | null {
  return label ? elementByPersonaLabel[label] ?? null : null;
}

/** Persona label as the product names it: "Vibe · X" (owner decision 2026-10-11). */
export function personaTag(label: string | null | undefined): string | null {
  const clean = sanitize(label ?? "");
  return clean ? `Vibe · ${clean}` : null;
}

export const shareCanvasSize: Record<ShareFormat, { width: number; height: number }> = {
  story_9_16: { width: 1080, height: 1920 },
  square_1_1: { width: 1080, height: 1080 },
};

const INK = "#1b0b33";
const VIOLET = "#4b278f";
const CREAM = "#fff9e9";
const LIME = "#dfff4f";
const LAVENDER_TEXT = "#e6dcff";
const BG_TOP = "#2a1457";
const BG_BOTTOM = "#1f0e40";

/** Every text colour / background pair used in the image (checked for ≥ 4.5:1 in tests). */
export const shareTextPairs = [
  { use: "hook, brand on violet", fg: CREAM, bg: VIOLET },
  { use: "hook on top gradient", fg: CREAM, bg: BG_TOP },
  { use: "kicker on violet", fg: LIME, bg: VIOLET },
  { use: "badge sticker", fg: INK, bg: LIME },
  { use: "tag sticker", fg: VIOLET, bg: CREAM },
  { use: "supporting line", fg: INK, bg: CREAM },
  { use: "privacy footer", fg: LAVENDER_TEXT, bg: BG_BOTTOM },
  { use: "privacy footer (mid)", fg: LAVENDER_TEXT, bg: VIOLET },
] as const;

type Theme = { foil: string[]; glow: string; accent: string };

export const shareThemes: Record<ShareElement | "none", Theme> = {
  fire: { foil: ["#ffc2a8", "#ff8a65", "#ffc46b", LIME, CREAM], glow: "#ff7a59", accent: "#ffb38a" },
  earth: { foil: ["#efe39a", "#cbb85a", LIME, "#bcd98a", CREAM], glow: "#c9b458", accent: "#e8dc8a" },
  air: { foil: ["#e0d4ff", "#bfa9ff", "#aee0ff", LIME, CREAM], glow: "#9fd8ff", accent: "#c9b6ff" },
  water: { foil: ["#a8f2e8", "#46d3cb", "#8fbfff", "#cdbcff", CREAM], glow: "#3fd0c9", accent: "#8fe6de" },
  none: { foil: ["#d4c4ff", LIME, CREAM, "#ffc2a8", "#c9b6ff"], glow: LIME, accent: "#d4c4ff" },
};

/** Zodiac glyphs drawn as strokes on a 100×100 grid so they render identically on every device. */
const zodiacPaths: Record<ZodiacSign, string> = {
  aries: "M50 88V42M50 42C50 16 22 10 18 30C15 45 30 52 36 42M50 42C50 16 78 10 82 30C85 45 70 52 64 42",
  taurus: "M18 16C26 40 74 40 82 16M50 40A22 22 0 1 0 50.01 40",
  gemini: "M22 16C40 25 60 25 78 16M22 84C40 75 60 75 78 84M38 22V78M62 22V78",
  cancer: "M84 36C70 16 34 14 18 34M16 64C30 84 66 86 82 66M38 36A10 10 0 1 1 38 35.9M62 64A10 10 0 1 1 62 63.9",
  leo: "M34 70A12 12 0 1 1 34.01 70M44 64C30 42 36 16 58 16C78 16 82 36 72 52C62 68 62 80 74 86C80 89 86 86 87 80",
  virgo: "M14 28C20 20 28 22 28 32V80M28 34C28 20 46 20 46 32V80M46 34C46 20 64 20 64 32V68C64 80 74 86 84 78M64 56C74 48 88 54 82 68C78 76 70 84 60 88",
  libra: "M14 80H86M14 64H34C24 56 26 30 50 28C74 30 76 56 66 64H86",
  scorpio: "M12 28C18 20 26 22 26 32V80M26 34C26 20 44 20 44 32V80M44 34C44 20 62 20 62 32V72C62 82 70 84 84 80M74 72L85 80L76 89",
  sagittarius: "M18 84L82 20M52 20H82V50M30 54L48 72",
  capricorn: "M12 30C18 22 26 26 28 34V72M28 40C32 20 52 22 52 40V64C52 84 76 88 82 72C86 60 72 52 62 62C56 70 50 82 38 88",
  aquarius: "M12 44L26 32L40 44L54 32L68 44L84 32M12 70L26 58L40 70L54 58L68 70L84 58",
  pisces: "M24 14C46 34 46 66 24 86M76 14C54 34 54 66 76 86M22 50H78",
};

/** Alchemical element triangles on the same 100×100 grid. */
const elementPaths: Record<ShareElement | "none", string> = {
  fire: "M50 14L88 82H12Z",
  water: "M50 86L88 18H12Z",
  air: "M50 14L88 82H12ZM26 58H74",
  earth: "M50 86L88 18H12ZM26 42H74",
  none: "M50 12L58 42L88 50L58 58L50 88L42 58L12 50L42 42Z",
};

function isUnsafeChar(code: number): boolean {
  return code <= 0x1f
    || (code >= 0x7f && code <= 0x9f)
    || (code >= 0x200b && code <= 0x200f)
    || (code >= 0x2028 && code <= 0x202e)
    || (code >= 0x2066 && code <= 0x2069);
}

/** Drops control, zero-width and bidi-override characters and collapses whitespace. */
export function sanitize(value: string): string {
  let out = "";
  for (const char of value) out += isUnsafeChar(char.codePointAt(0) ?? 0) ? " " : char;
  return out.replace(/\s+/g, " ").trim();
}

export function escapeXml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

const NARROW = new Set([..."iljI.,:;'!|()[]{}`’‘ı"]);
const SEMI = new Set([..."ftr-/\"“”"]);
const WIDE = new Set([..."mwMW—@%"]);

/** Conservative width estimate (in px) for Be Vietnam Pro / system sans fallbacks. */
export function estimateWidth(text: string, size: number, weight: number): number {
  const base = text.normalize("NFD").replace(/\p{M}/gu, "");
  let units = 0;
  for (const char of base) {
    if (char === " ") units += 0.28;
    else if (NARROW.has(char)) units += 0.3;
    else if (SEMI.has(char)) units += 0.42;
    else if (WIDE.has(char)) units += 0.9;
    else if (/[0-9]/.test(char)) units += 0.62;
    else if (char !== char.toLowerCase()) units += 0.74;
    else units += 0.6;
  }
  return units * size * (weight >= 700 ? 1.04 : 1.0);
}

function splitLongWord(word: string, size: number, weight: number, maxWidth: number): string[] {
  const parts: string[] = [];
  let current = "";
  for (const char of word) {
    if (current && estimateWidth(current + char, size, weight) > maxWidth) {
      parts.push(current);
      current = char;
    } else current += char;
  }
  if (current) parts.push(current);
  return parts;
}

export function wrapText(text: string, size: number, weight: number, maxWidth: number): string[] {
  const rows: string[] = [];
  for (const rawWord of text.split(" ").filter(Boolean)) {
    const pieces = estimateWidth(rawWord, size, weight) > maxWidth ? splitLongWord(rawWord, size, weight, maxWidth) : [rawWord];
    for (const word of pieces) {
      const last = rows.at(-1);
      if (last !== undefined && estimateWidth(`${last} ${word}`, size, weight) <= maxWidth) rows[rows.length - 1] = `${last} ${word}`;
      else rows.push(word);
    }
  }
  return rows;
}

/** Greedy wrap, then narrow the measure while the line count stays the same (avoids one-word orphans). */
function balance(text: string, size: number, weight: number, width: number): string[] {
  const greedy = wrapText(text, size, weight, width);
  if (greedy.length < 2) return greedy;
  let low = width * 0.55;
  let high = width;
  let best = greedy;
  for (let step = 0; step < 10; step += 1) {
    const middle = (low + high) / 2;
    const candidate = wrapText(text, size, weight, middle);
    if (candidate.length === greedy.length) {
      best = candidate;
      high = middle;
    } else low = middle;
  }
  return best;
}

export type FitResult = { size: number; lines: string[]; lineHeight: number; height: number };

/**
 * Picks the largest size that fits the box (preferring ≤ maxLines), then keeps shrinking below
 * `min` if needed. Text is never cut.
 */
export function fitText(text: string, box: { width: number; height: number; max: number; min: number; maxLines: number; leading: number; weight: number; balanced?: boolean }): FitResult {
  const make = (size: number): FitResult => {
    const lines = box.balanced ? balance(text, size, box.weight, box.width) : wrapText(text, size, box.weight, box.width);
    const lineHeight = size * box.leading;
    return { size, lines, lineHeight, height: lines.length * lineHeight };
  };
  for (let size = box.max; size >= box.min; size -= 2) {
    const result = make(size);
    if (result.lines.length <= box.maxLines && result.height <= box.height) return result;
  }
  for (let size = box.max; size > 8; size -= 1) {
    const result = make(size);
    if (result.height <= box.height) return result;
  }
  return make(8);
}

function hashSeed(value: string): number {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function prng(seed: number) {
  let state = seed || 1;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const r1 = (value: number) => Math.round(value * 10) / 10;

function sparkle(x: number, y: number, s: number, fill: string, opacity: number) {
  return `<path d="M${r1(x)} ${r1(y - s)}Q${r1(x)} ${r1(y)} ${r1(x + s)} ${r1(y)}Q${r1(x)} ${r1(y)} ${r1(x)} ${r1(y + s)}Q${r1(x)} ${r1(y)} ${r1(x - s)} ${r1(y)}Q${r1(x)} ${r1(y)} ${r1(x)} ${r1(y - s)}Z" fill="${fill}" opacity="${opacity}"/>`;
}

type Rect = { x: number; y: number; w: number; h: number };

function starField(seed: string, width: number, height: number, avoid: Rect[], count: number) {
  const random = prng(hashSeed(seed));
  const out: string[] = [];
  let attempts = 0;
  while (out.length < count && attempts < count * 12) {
    attempts += 1;
    const x = 40 + random() * (width - 80);
    const y = 40 + random() * (height - 80);
    const size = 5 + random() * 13;
    if (avoid.some((r) => x > r.x - size && x < r.x + r.w + size && y > r.y - size && y < r.y + r.h + size)) continue;
    const fill = random() > 0.7 ? LIME : CREAM;
    const opacity = r1(0.35 + random() * 0.5);
    out.push(random() > 0.45 ? sparkle(x, y, size, fill, opacity) : `<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(size / 4)}" fill="${fill}" opacity="${opacity}"/>`);
  }
  return out.join("");
}

function textRows(rows: string[], x: number, firstBaseline: number, lineHeight: number, className: string, anchor: "start" | "middle" = "start") {
  return `<text class="${className}" x="${x}" y="${r1(firstBaseline)}" text-anchor="${anchor}">${rows
    .map((row, index) => `<tspan x="${x}" dy="${index ? r1(lineHeight) : 0}">${escapeXml(row)}</tspan>`)
    .join("")}</text>`;
}

function sticker(opts: { cx: number; cy: number; text: string; size: number; maxWidth: number; rotate: number; fill: string; color: string; className: string; icon?: string | null; anchor?: "center" | "left" }) {
  let size = opts.size;
  const iconSpace = (s: number) => (opts.icon ? s * 1.15 : 0);
  const padding = (s: number) => s * 0.85;
  const widthFor = (s: number) => estimateWidth(opts.text, s, 800) + padding(s) * 2 + iconSpace(s);
  while (size > 14 && widthFor(size) > opts.maxWidth) size -= 1;
  const width = widthFor(size);
  const height = size * 2.2;
  const left = opts.anchor === "left" ? opts.cx : opts.cx - width / 2;
  const top = opts.cy - height / 2;
  const textX = left + padding(size) + iconSpace(size);
  const icon = opts.icon
    ? `<g transform="translate(${r1(left + padding(size) * 0.9)} ${r1(opts.cy - size * 0.42)}) scale(${r1(size * 0.0085 * 100) / 100})"><path d="${opts.icon}" fill="none" stroke="${opts.color}" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/></g>`
    : "";
  const pivotX = r1(left + width / 2);
  return `<g transform="rotate(${opts.rotate} ${pivotX} ${r1(opts.cy)})">
    <rect x="${r1(left + 6)}" y="${r1(top + 9)}" width="${r1(width)}" height="${r1(height)}" rx="${r1(height / 2)}" fill="${INK}" opacity="0.45"/>
    <rect x="${r1(left)}" y="${r1(top)}" width="${r1(width)}" height="${r1(height)}" rx="${r1(height / 2)}" fill="${opts.fill}" stroke="${CREAM}" stroke-width="5"/>
    ${icon}
    <text class="${opts.className}" x="${r1(textX)}" y="${r1(opts.cy + size * 0.36)}" font-size="${size}" fill="${opts.color}">${escapeXml(opts.text)}</text>
  </g>`;
}

function heroDisc(cx: number, cy: number, r: number, spec: ShareArtSpec) {
  const glyphPath = spec.sign ? zodiacPaths[spec.sign] : elementPaths[spec.element ?? "none"];
  const glyphScale = (r * 1.12) / 100;
  const stroke = spec.sign ? 7.5 : 6.5;
  return `
    <circle cx="${cx}" cy="${cy}" r="${r1(r * 1.12)}" fill="none" stroke="${LIME}" stroke-width="5"/>
    <circle cx="${cx}" cy="${cy}" r="${r}" fill="${CREAM}"/>
    <g transform="translate(${r1(cx - 50 * glyphScale)} ${r1(cy - 50 * glyphScale)}) scale(${r1(glyphScale * 1000) / 1000})">
      <path d="${glyphPath}" fill="none" stroke="${INK}" stroke-width="${stroke}" stroke-linecap="round" stroke-linejoin="round"/>
    </g>
`;
}

type Layout = {
  width: number;
  height: number;
  header: number;
  brandSize: number;
  disc: { cx: number; cy: number; r: number };
  badge: { cx: number; cy: number; size: number; maxWidth: number; anchor: "center" | "left"; rotate: number };
  tag: { cx: number; cy: number; size: number; maxWidth: number; anchor: "center" | "left"; rotate: number };
  stack: { top: number; bottom: number; left: number; width: number };
  kickerSize: number;
  hook: { max: number; min: number };
  support: { max: number; min: number; padding: number };
  footer: { y: number; size: number };
  frameInset: number;
};

function layoutFor(format: ShareFormat): Layout {
  if (format === "square_1_1") {
    return {
      width: 1080, height: 1080, header: 100, brandSize: 40,
      disc: { cx: 250, cy: 318, r: 128 },
      badge: { cx: 452, cy: 272, size: 34, maxWidth: 570, anchor: "left", rotate: -3 },
      tag: { cx: 476, cy: 372, size: 28, maxWidth: 480, anchor: "left", rotate: 4 },
      stack: { top: 500, bottom: 978, left: 90, width: 900 },
      kickerSize: 24,
      hook: { max: 88, min: 40 },
      support: { max: 32, min: 22, padding: 30 },
      footer: { y: 1036, size: 22 },
      frameInset: 26,
    };
  }
  return {
    width: 1080, height: 1920, header: 236, brandSize: 46,
    disc: { cx: 540, cy: 600, r: 222 },
    badge: { cx: 540, cy: 900, size: 42, maxWidth: 900, anchor: "center", rotate: -4 },
    tag: { cx: 770, cy: 370, size: 32, maxWidth: 380, anchor: "center", rotate: 8 },
    stack: { top: 990, bottom: 1610, left: 90, width: 900 },
    kickerSize: 30,
    hook: { max: 128, min: 56 },
    support: { max: 40, min: 28, padding: 40 },
    footer: { y: 1700, size: 26 },
    frameInset: 30,
  };
}

const FONT_STACK = "'LL Share','Be Vietnam Pro',system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif";

/** Build the share image. `fontCss` is optional embedded @font-face CSS (see shareFonts.ts). */
export function buildShareArtSvg(input: ShareArtSpec, format: ShareFormat, fontCss = ""): string {
  const spec: ShareArtSpec = {
    ...input,
    kicker: sanitize(input.kicker),
    hook: sanitize(input.hook) || "Lá Lành",
    support: input.support ? sanitize(input.support) || null : null,
    badge: sanitize(input.badge),
    tag: input.tag ? sanitize(input.tag) || null : null,
    footer: sanitize(input.footer),
  };
  const L = layoutFor(format);
  const theme = shareThemes[spec.element ?? "none"];
  const { width, height } = L;

  const kickerBlock = spec.kicker ? L.kickerSize * 1.9 : 0;
  const supportWidth = L.stack.width - L.support.padding * 2;
  const support = spec.support
    ? fitText(spec.support, { width: supportWidth, height: L.support.max * 1.4 * 3, max: L.support.max, min: L.support.min, maxLines: 3, leading: 1.4, weight: 600 })
    : null;
  const supportBox = support ? support.height + L.support.padding * 1.6 : 0;
  const supportGap = support ? L.kickerSize * 1.4 : 0;
  const stackHeight = L.stack.bottom - L.stack.top;
  const hook = fitText(spec.hook, {
    width: L.stack.width,
    height: stackHeight - kickerBlock - supportBox - supportGap,
    max: L.hook.max,
    min: L.hook.min,
    maxLines: 3,
    leading: 1.14,
    weight: 800,
    balanced: true,
  });
  const used = kickerBlock + hook.height + supportGap + supportBox;
  let y = L.stack.top + Math.max(0, (stackHeight - used) / 2);

  const parts: string[] = [];
  if (spec.kicker) {
    parts.push(sparkle(L.stack.left + L.kickerSize * 0.45, y + L.kickerSize * 0.62, L.kickerSize * 0.45, LIME, 1));
    parts.push(`<text class="kick" x="${L.stack.left + L.kickerSize * 1.25}" y="${r1(y + L.kickerSize)}" font-size="${L.kickerSize}">${escapeXml(spec.kicker.toLocaleUpperCase("vi"))}</text>`);
    y += kickerBlock;
  }
  const hookTop = y;
  parts.push(`<g font-size="${hook.size}">${textRows(hook.lines, L.stack.left, y + hook.size * 0.92, hook.lineHeight, "hook")}</g>`);
  y += hook.height;
  let supportRect: Rect | null = null;
  if (support) {
    y += supportGap;
    supportRect = { x: L.stack.left, y, w: L.stack.width, h: supportBox };
    parts.push(`<rect x="${L.stack.left}" y="${r1(y)}" width="${L.stack.width}" height="${r1(supportBox)}" rx="${format === "square_1_1" ? 26 : 34}" fill="${CREAM}"/>`);
    parts.push(`<rect x="${L.stack.left + 14}" y="${r1(y + 18)}" width="9" height="${r1(supportBox - 36)}" rx="4.5" fill="url(#ll-foil)"/>`);
    parts.push(`<g font-size="${support.size}">${textRows(support.lines, L.stack.left + L.support.padding, y + L.support.padding * 0.8 + support.size * 1.02, support.lineHeight, "sup")}</g>`);
    y += supportBox;
  }

  const avoid: Rect[] = [
    { x: L.stack.left - 10, y: hookTop - kickerBlock - 10, w: L.stack.width + 20, h: y - hookTop + kickerBlock + 20 },
    { x: L.disc.cx - L.disc.r * 1.3, y: L.disc.cy - L.disc.r * 1.3, w: L.disc.r * 2.6, h: L.disc.r * 2.6 },
    { x: 60, y: L.header - 60, w: 420, h: 90 },
    { x: width - 330, y: L.header - 50, w: 300, h: 80 },
    { x: 0, y: L.footer.y - 50, w: width, h: 80 },
  ];
  if (format === "square_1_1") avoid.push({ x: L.badge.cx - 20, y: L.badge.cy - 60, w: 600, h: 180 });
  else avoid.push({ x: 60, y: L.badge.cy - 70, w: width - 120, h: 140 }, { x: L.tag.cx - 200, y: L.tag.cy - 60, w: 400, h: 120 });
  if (supportRect) avoid.push(supportRect);

  const glowR = format === "square_1_1" ? 330 : 470;
  const seed = `${spec.hook}|${spec.badge}|${format}`;
  const stars = starField(seed, width, height, avoid, 6);
  const foilStops = theme.foil.map((color, index) => `<stop offset="${r1((index / (theme.foil.length - 1)) * 100)}%" stop-color="${color}"/>`).join("");

  const badge = spec.badge
    ? sticker({ ...L.badge, rotate: 0, text: spec.badge, fill: LIME, color: INK, className: "stk", icon: elementPaths[spec.element ?? "none"] })
    : "";
  // One sticker only; the persona tag stays in the alt text and page copy.
  const tag = "";

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <style><![CDATA[${fontCss}
    text{font-family:${FONT_STACK}}
    .brand{font-weight:800;fill:${CREAM};letter-spacing:-0.01em}
    .kick{font-weight:800;fill:${LIME};letter-spacing:0.12em}
    .hook{font-weight:800;fill:${CREAM};letter-spacing:-0.015em}
    .sup{font-weight:600;fill:${INK}}
    .stk{font-weight:800}
    .foot{font-weight:600;fill:${LAVENDER_TEXT};letter-spacing:0.02em}
  ]]></style>
  <defs>
    <linearGradient id="ll-bg" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0%" stop-color="${BG_TOP}"/><stop offset="48%" stop-color="${VIOLET}"/><stop offset="100%" stop-color="${BG_BOTTOM}"/>
    </linearGradient>
    <radialGradient id="ll-glow" cx="${L.disc.cx}" cy="${L.disc.cy}" r="${glowR}" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="${theme.glow}" stop-opacity="0.55"/><stop offset="55%" stop-color="${theme.glow}" stop-opacity="0.14"/><stop offset="100%" stop-color="${theme.glow}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="ll-foil" x1="0" y1="0" x2="1" y2="1">${foilStops}</linearGradient>
    <linearGradient id="ll-sheen" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/><stop offset="38%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="46%" stop-color="#ffffff" stop-opacity="0.6"/><stop offset="52%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="62%" stop-color="#ffffff" stop-opacity="0.28"/><stop offset="66%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="${width}" height="${height}" fill="url(#ll-bg)"/>
  <rect width="${width}" height="${height}" fill="url(#ll-glow)"/>
  <rect x="${L.frameInset}" y="${L.frameInset}" width="${width - L.frameInset * 2}" height="${height - L.frameInset * 2}" rx="44" fill="none" stroke="${CREAM}" stroke-width="2" opacity="0.25"/>
  ${stars}
  <text class="brand" x="90" y="${L.header}" font-size="${L.brandSize}">Lá Lành<tspan fill="${LIME}">*</tspan></text>
  ${heroDisc(L.disc.cx, L.disc.cy, L.disc.r, spec)}
  ${tag}
  ${badge}
  ${parts.join("\n  ")}
  ${sparkle(width / 2 - estimateWidth(spec.footer, L.footer.size, 600) / 2 - 26, L.footer.y - L.footer.size * 0.34, 9, LIME, 1)}
  <text class="foot" x="${width / 2}" y="${L.footer.y}" font-size="${L.footer.size}" text-anchor="middle">${escapeXml(spec.footer)}</text>
</svg>`;
}

/** Human description of the image for alt text / aria-label. */
export function shareArtAlt(spec: ShareArtSpec, format: ShareFormat): string {
  const label = format === "square_1_1" ? "vuông 1:1" : "Story 9:16";
  const stickers = [spec.badge, spec.tag].map((value) => sanitize(value ?? "")).filter(Boolean).join(", ");
  const support = spec.support ? ` ${sanitize(spec.support)}` : "";
  const hook = sanitize(spec.hook);
  const end = /[.!?…]$/.test(hook) ? "" : ".";
  return `Thẻ ${sanitize(spec.kicker)} khổ ${label}: “${hook}${end}”${support} Nhãn: ${stickers}. ${sanitize(spec.footer)}.`;
}
