import type { TarotCard } from "../../shared/api/client";

/**
 * Pure, deterministic description of the procedural card art.
 * Same card id ⇒ same spec ⇒ same SVG. No network assets, no randomness.
 */

export type TarotArtInput = Pick<TarotCard, "id" | "arcana" | "title_vi"> &
  Partial<Pick<TarotCard, "suit" | "rank">>;

export const MAJOR_KEYS = [
  "fool",
  "magician",
  "high-priestess",
  "empress",
  "emperor",
  "hierophant",
  "lovers",
  "chariot",
  "strength",
  "hermit",
  "wheel-of-fortune",
  "justice",
  "hanged-man",
  "death",
  "temperance",
  "devil",
  "tower",
  "star",
  "moon",
  "sun",
  "judgement",
  "world",
] as const;
export type MajorKey = (typeof MAJOR_KEYS)[number];

export const SUITS = ["cups", "pentacles", "swords", "wands"] as const;
export type TarotSuit = (typeof SUITS)[number];

export const RANKS = ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "page", "knight", "queen", "king"] as const;
export type TarotRank = (typeof RANKS)[number];
export type CourtRank = Extract<TarotRank, "page" | "knight" | "queen" | "king">;

export type TarotPalette = {
  /** Gradient top. */
  top: string;
  /** Gradient bottom. */
  bottom: string;
  /** Primary line/glyph colour (cream). */
  ink: string;
  /** Metallic accent for frame, numerals and fills. */
  accent: string;
  /** Secondary luminous accent. */
  glow: string;
  /** Dark outline / title band colour. */
  band: string;
};

export const TAROT_PALETTES: Record<"major" | TarotSuit, TarotPalette> = {
  // Every card shares the brand violet so a spread reads as one deck; suits
  // differ only by the colour of their symbols (gold, cream, lime tints).
  major: { top: "#5b30a8", bottom: "#2a1159", ink: "#fff9e9", accent: "#ffd36e", glow: "#dfff4f", band: "#1b0a38" },
  wands: { top: "#55309e", bottom: "#271254", ink: "#fff9e9", accent: "#ffc98a", glow: "#ffe3b8", band: "#1b0a38" },
  cups: { top: "#55309e", bottom: "#271254", ink: "#fff9e9", accent: "#fff9e9", glow: "#dfff4f", band: "#1b0a38" },
  swords: { top: "#55309e", bottom: "#271254", ink: "#fff9e9", accent: "#e4d8ff", glow: "#fff9e9", band: "#1b0a38" },
  pentacles: { top: "#55309e", bottom: "#271254", ink: "#fff9e9", accent: "#dfff4f", glow: "#ffd36e", band: "#1b0a38" },
};

export type TarotArtSpec =
  | { kind: "major"; key: MajorKey | null; numeral: string; palette: TarotPalette; signature: string }
  | {
      kind: "minor";
      suit: TarotSuit;
      rank: TarotRank;
      numeral: string;
      pips: number | null;
      court: CourtRank | null;
      palette: TarotPalette;
      signature: string;
    };

export function toRoman(value: number): string {
  if (value <= 0) return "0";
  const table: Array<[number, string]> = [
    [10, "X"],
    [9, "IX"],
    [5, "V"],
    [4, "IV"],
    [1, "I"],
  ];
  let rest = value;
  let out = "";
  for (const [amount, glyph] of table) {
    while (rest >= amount) {
      out += glyph;
      rest -= amount;
    }
  }
  return out;
}

function isSuit(value: unknown): value is TarotSuit {
  return typeof value === "string" && (SUITS as readonly string[]).includes(value);
}

function isRank(value: unknown): value is TarotRank {
  return typeof value === "string" && (RANKS as readonly string[]).includes(value);
}

export function tarotArtSpec(card: TarotArtInput): TarotArtSpec {
  const [idSuit, idRank] = card.id.split("-", 2);
  const suit = isSuit(card.suit) ? card.suit : isSuit(idSuit) ? idSuit : null;
  const rank = isRank(card.rank) ? card.rank : isRank(idRank) ? idRank : null;
  if (card.arcana === "minor" && suit && rank) {
    const number = Number(rank);
    const pips = Number.isInteger(number) ? number : null;
    const court = rank === "page" || rank === "knight" || rank === "queen" || rank === "king" ? rank : null;
    const numeral = rank === "ace" ? "A" : pips ? toRoman(pips) : "";
    return {
      kind: "minor",
      suit,
      rank,
      numeral,
      pips,
      court,
      palette: TAROT_PALETTES[suit],
      signature: `minor:${suit}:${rank}`,
    };
  }
  const slug = card.id.startsWith("major-") ? card.id.slice("major-".length) : card.id;
  const index = (MAJOR_KEYS as readonly string[]).indexOf(slug);
  const key = index >= 0 ? MAJOR_KEYS[index] : null;
  return {
    kind: "major",
    key,
    numeral: index >= 0 ? toRoman(index) : "",
    palette: TAROT_PALETTES.major,
    signature: `major:${key ?? "unknown"}`,
  };
}

/** FNV-1a → mulberry32: tiny seeded PRNG so background sparkles are stable per card. */
export function seededRandom(seed: string): () => number {
  let hash = 0x811c9dc5;
  for (let index = 0; index < seed.length; index += 1) {
    hash ^= seed.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  let state = hash >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let next = state;
    next = Math.imul(next ^ (next >>> 15), next | 1);
    next ^= next + Math.imul(next ^ (next >>> 7), next | 61);
    return ((next ^ (next >>> 14)) >>> 0) / 4294967296;
  };
}

/** Split a Vietnamese title into at most two balanced lines for the bottom band. */
export function titleLines(title: string): string[] {
  const clean = title.trim();
  if (clean.length <= 15) return [clean];
  const words = clean.split(/\s+/);
  if (words.length < 2) return [clean];
  let best = 1;
  let bestDiff = Number.POSITIVE_INFINITY;
  for (let cut = 1; cut < words.length; cut += 1) {
    const diff = Math.abs(words.slice(0, cut).join(" ").length - words.slice(cut).join(" ").length);
    if (diff <= bestDiff) {
      best = cut;
      bestDiff = diff;
    }
  }
  return [words.slice(0, best).join(" "), words.slice(best).join(" ")];
}

/** SVG geometry helpers (rounded so markup stays compact and deterministic). */
const r1 = (value: number) => Math.round(value * 10) / 10;

export function starPoints(cx: number, cy: number, outer: number, inner: number, points: number, rotation = -90): string {
  const out: string[] = [];
  for (let index = 0; index < points * 2; index += 1) {
    const radius = index % 2 === 0 ? outer : inner;
    const angle = ((rotation + (index * 180) / points) * Math.PI) / 180;
    out.push(`${r1(cx + radius * Math.cos(angle))},${r1(cy + radius * Math.sin(angle))}`);
  }
  return out.join(" ");
}

export function raysPath(cx: number, cy: number, inner: number, outer: number, count: number, offsetDeg = 0, arc: [number, number] = [0, 360]): string {
  const [from, to] = arc;
  const full = to - from >= 360;
  const step = (to - from) / (full ? count : Math.max(count - 1, 1));
  let d = "";
  for (let index = 0; index < count; index += 1) {
    const angle = ((from + offsetDeg + index * step) * Math.PI) / 180;
    d += `M${r1(cx + inner * Math.cos(angle))} ${r1(cy + inner * Math.sin(angle))}L${r1(cx + outer * Math.cos(angle))} ${r1(cy + outer * Math.sin(angle))}`;
  }
  return d;
}

export function crescentPath(cx: number, cy: number, radius: number, thickness = 0.62): string {
  return `M${cx} ${cy - radius}A${radius} ${radius} 0 1 0 ${cx} ${cy + radius}A${r1(radius * thickness)} ${radius} 0 1 1 ${cx} ${cy - radius}Z`;
}

export function wavePath(x: number, y: number, width: number, amplitude = 3, period = 12): string {
  let d = `M${x} ${y}`;
  const steps = Math.max(1, Math.round(width / period));
  const half = width / steps / 2;
  for (let index = 0; index < steps; index += 1) {
    d += `q${r1(half / 2)} ${-amplitude} ${r1(half)} 0t${r1(half)} 0`;
  }
  return d;
}

/** Pip coordinates inside the 120×200 card for 2–10. */
export const PIP_LAYOUTS: Record<number, Array<[number, number]>> = {
  2: [[60, 62], [60, 124]],
  3: [[60, 54], [60, 93], [60, 132]],
  4: [[40, 62], [80, 62], [40, 124], [80, 124]],
  5: [[40, 58], [80, 58], [60, 93], [40, 128], [80, 128]],
  6: [[40, 56], [80, 56], [40, 93], [80, 93], [40, 130], [80, 130]],
  7: [[40, 54], [80, 54], [60, 73], [40, 93], [80, 93], [40, 132], [80, 132]],
  8: [[40, 52], [80, 52], [60, 72], [40, 93], [80, 93], [60, 114], [40, 134], [80, 134]],
  9: [[40, 50], [80, 50], [40, 79], [80, 79], [60, 93], [40, 107], [80, 107], [40, 136], [80, 136]],
  10: [[40, 50], [80, 50], [60, 64], [40, 79], [80, 79], [40, 107], [80, 107], [60, 122], [40, 136], [80, 136]],
};
