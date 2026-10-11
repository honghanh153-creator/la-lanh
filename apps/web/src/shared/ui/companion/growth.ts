// Living-companion rhythm. Everything here is computed on the device.
//
// Privacy (Nghị định 356/2025 treats service-usage tracking as sensitive):
// the only stored state is a random seed, a capped count of distinct local
// visit days and the last counted local day. No timestamps, no per-day
// history, nothing derived from birth data, mood or location, and nothing is
// sent over the network. Growth only ever adds: there is no streak, no
// wilting and no penalty for a gap (guardrails G1–G7, P1–P3 in
// reports/Bạn đồng hành cây lớn dần.md).
import { moonPhase } from "../la/moonPhase";
import { midAutumnDate, tetDate, julianDayNumber, type CivilDate } from "./lunarCalendar";

/** A new local "day" starts at 05:00, so a late night belongs to the day before (G4). */
export const DAY_BOUNDARY_HOUR = 5;
/** 23:00–05:00: visits never add growth (G6). */
export const QUIET_GROWTH_START_HOUR = 23;
export const COMPANION_GROWTH_STORAGE_KEY = "la-lanh-companion-growth-v1";
export const MAX_GROWTH_DAYS = 400;
/** Distinct visit days needed for each growth level 0..6. */
export const GROWTH_LEVEL_DAYS = [1, 3, 7, 14, 30, 60, 120] as const;
export const MAX_GROWTH_LEVEL = GROWTH_LEVEL_DAYS.length - 1;

/** One-sentence rule the UI can show next to the companion (G4). */
export const GROWTH_RULE_COPY =
  "Mỗi ngày bạn ghé, cây lớn thêm một chút. Vắng vài hôm cây chỉ nghỉ, không bao giờ héo.";
/** Calm return copy after a gap (G3). Never mentions how long the user was away. */
export const WELCOME_BACK_COPY = "Chào bạn quay lại. Cây giữ cho bạn một chiếc lá mới.";

export type DayPhase = "dawn" | "morning" | "noon" | "afternoon" | "evening" | "night";

export type DayStage = {
  phase: DayPhase;
  /** Continuous 0–1 progress through the local day, 0 at 05:00. */
  progress: number;
  /** 0–1 progress inside the current phase. */
  phaseProgress: number;
  /** Local fractional hour, 0 ≤ hour < 24. */
  hour: number;
  /** Night: calm, dim, no rewards, gently suggests rest. */
  resting: boolean;
  label: string;
};

const PHASES: ReadonlyArray<{ phase: DayPhase; start: number; end: number; label: string }> = [
  { phase: "dawn", start: 5, end: 8, label: "bình minh" },
  { phase: "morning", start: 8, end: 11, label: "buổi sáng" },
  { phase: "noon", start: 11, end: 14, label: "buổi trưa" },
  { phase: "afternoon", start: 14, end: 18, label: "buổi chiều" },
  { phase: "evening", start: 18, end: 21, label: "chạng vạng" },
  { phase: "night", start: 21, end: 29, label: "ban đêm" },
];

export const DAY_PHASE_LABEL: Record<DayPhase, string> = Object.fromEntries(
  PHASES.map(({ phase, label }) => [phase, label]),
) as Record<DayPhase, string>;

export function localHour(at: Date): number {
  return at.getHours() + at.getMinutes() / 60 + at.getSeconds() / 3600;
}

export function dayStage(at: Date = new Date()): DayStage {
  const hour = localHour(at);
  const shifted = hour < DAY_BOUNDARY_HOUR ? hour + 24 : hour;
  const entry = PHASES.find(({ start, end }) => shifted >= start && shifted < end) ?? PHASES[PHASES.length - 1];
  return {
    phase: entry.phase,
    progress: (shifted - DAY_BOUNDARY_HOUR) / 24,
    phaseProgress: (shifted - entry.start) / (entry.end - entry.start),
    hour,
    resting: entry.phase === "night",
    label: entry.label,
  };
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

/** Local day key ("YYYY-MM-DD") with the 05:00 boundary. */
export function localDayKey(at: Date): string {
  const shifted = new Date(at.getFullYear(), at.getMonth(), at.getDate(), at.getHours() - DAY_BOUNDARY_HOUR, at.getMinutes());
  return `${shifted.getFullYear()}-${pad(shifted.getMonth() + 1)}-${pad(shifted.getDate())}`;
}

function dayKeyNumber(key: string): number {
  const [year, month, day] = key.split("-").map(Number);
  return julianDayNumber({ year, month, day });
}

export type GrowthState = {
  v: 1;
  /** Random 32-bit seed created once; never derived from personal data (P3). */
  seed: number;
  /** Distinct local visit days, capped. Never decreases. */
  days: number;
  /** Last counted local day key, or "" before the first counted day. */
  last: string;
};

const DAY_KEY = /^\d{4}-\d{2}-\d{2}$/;

function isGrowthState(value: unknown): value is GrowthState {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  const keys = Object.keys(record).sort().join(",");
  return keys === "days,last,seed,v"
    && record.v === 1
    && Number.isInteger(record.seed) && (record.seed as number) >= 0 && (record.seed as number) <= 0xffffffff
    && Number.isInteger(record.days) && (record.days as number) >= 0 && (record.days as number) <= MAX_GROWTH_DAYS
    && typeof record.last === "string"
    && (DAY_KEY.test(record.last) || (record.last === "" && record.days === 0));
}

/** Random 32-bit unsigned seed from the platform CSPRNG. */
export function createSeed(): number {
  try {
    const out = new Uint32Array(1);
    globalThis.crypto.getRandomValues(out);
    return out[0];
  } catch {
    return Math.floor(Math.random() * 0x100000000) >>> 0;
  }
}

export function readGrowth(): GrowthState | null {
  try {
    const raw = localStorage.getItem(COMPANION_GROWTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    return isGrowthState(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function writeGrowth(state: GrowthState): void {
  try {
    // Exactly the four allowed fields, in a fixed order.
    const minimal: GrowthState = { v: 1, seed: state.seed, days: state.days, last: state.last };
    localStorage.setItem(COMPANION_GROWTH_STORAGE_KEY, JSON.stringify(minimal));
  } catch {
    /* Storage blocked: the companion still renders for this visit. */
  }
}

export type VisitResult = {
  state: GrowthState;
  /** True when this visit added a new day. */
  counted: boolean;
  /** True after a gap of at least one whole local day; show the calm gift, never a count of missed days. */
  welcomeBack: boolean;
};

/**
 * Count today's visit at most once per local day (05:00 boundary). Visits in
 * the quiet hours (23:00–05:00) never add growth. Never decreases `days`,
 * including when the device clock moves backwards.
 */
export function recordVisit(now: Date = new Date()): VisitResult {
  const existing = readGrowth();
  const base: GrowthState = existing ?? { v: 1, seed: createSeed(), days: 0, last: "" };
  const hour = localHour(now);
  const quiet = hour >= QUIET_GROWTH_START_HOUR || hour < DAY_BOUNDARY_HOUR;
  const today = localDayKey(now);
  const isNewDay = base.last === "" || dayKeyNumber(today) > dayKeyNumber(base.last);
  if (quiet || !isNewDay) {
    if (!existing) writeGrowth(base);
    return { state: base, counted: false, welcomeBack: false };
  }
  const gap = base.last === "" ? 0 : dayKeyNumber(today) - dayKeyNumber(base.last);
  const next: GrowthState = {
    v: 1,
    seed: base.seed,
    days: Math.min(MAX_GROWTH_DAYS, base.days + 1),
    last: today,
  };
  writeGrowth(next);
  return { state: next, counted: true, welcomeBack: gap >= 2 };
}

/** 0..6. Level n needs GROWTH_LEVEL_DAYS[n] distinct days; 0 and 1 day are both level 0. */
export function growthLevel(days: number): number {
  const safe = Number.isFinite(days) ? Math.max(0, days) : 0;
  let level = 0;
  for (let i = 0; i < GROWTH_LEVEL_DAYS.length; i += 1) {
    if (safe >= GROWTH_LEVEL_DAYS[i]) level = i;
  }
  return level;
}

export const GROWTH_LEVEL_LABEL = [
  "mầm mới",
  "mầm non",
  "cây con",
  "cây nhỏ",
  "cây xanh",
  "cây sum suê",
  "cây lớn",
] as const;

/** Days since the last new moon (0 ≤ age < 29.53), from the on-device moon model. */
export function lunarAge(at: Date = new Date()): number {
  return moonPhase(at).age;
}

export type FestivalKey = "tet" | "trung-thu";

export type FestivalSkin = {
  key: FestivalKey;
  label: string;
  /** 0 on the festival day itself; negative before, positive after. */
  offsetDays: number;
};

/**
 * Time-boxed decorative skins. Tết: 5 days before mùng 1 through mùng 7.
 * Trung Thu: lunar 10/8 through 16/8. Dates come from the UTC+7 lunisolar
 * calendar (`lunarCalendar.ts`). Skins are cosmetic only; nothing is stored or
 * collected, and copy never uses "chỉ hôm nay" / "lỡ là mất" (C3).
 */
export function festivalSkin(at: Date = new Date()): FestivalSkin | null {
  const civil: CivilDate = { year: at.getFullYear(), month: at.getMonth() + 1, day: at.getDate() };
  const today = julianDayNumber(civil);
  const windows: Array<{ key: FestivalKey; label: string; day: CivilDate; before: number; after: number }> = [];
  for (const year of [civil.year, civil.year + 1]) {
    try {
      windows.push({ key: "tet", label: "Tết", day: tetDate(year), before: 5, after: 6 });
    } catch { /* outside supported range */ }
  }
  try {
    windows.push({ key: "trung-thu", label: "Trung Thu", day: midAutumnDate(civil.year), before: 5, after: 1 });
  } catch { /* outside supported range */ }
  for (const window of windows) {
    const offset = today - julianDayNumber(window.day);
    if (offset >= -window.before && offset <= window.after) {
      return { key: window.key, label: window.label, offsetDays: offset };
    }
  }
  return null;
}

/** Resolve a component's `festival` prop: "auto"/undefined follows the calendar, null hides skins. */
export function resolveFestival(prop: FestivalKey | null | "auto" | undefined, at: Date): FestivalKey | null {
  if (prop === null) return null;
  if (prop === "tet" || prop === "trung-thu") return prop;
  return festivalSkin(at)?.key ?? null;
}
