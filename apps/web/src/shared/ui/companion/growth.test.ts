import { moonPhase } from "../la/moonPhase";
import {
  COMPANION_GROWTH_STORAGE_KEY, GROWTH_LEVEL_DAYS, GROWTH_RULE_COPY, MAX_GROWTH_DAYS, WELCOME_BACK_COPY,
  dayStage, festivalSkin, growthLevel, localDayKey, lunarAge, readGrowth, recordVisit, resolveFestival,
} from "./growth";
import { midAutumnDate, tetDate } from "./lunarCalendar";

const at = (y: number, m: number, d: number, h: number, min = 0) => new Date(y, m - 1, d, h, min);
const stored = () => JSON.parse(localStorage.getItem(COMPANION_GROWTH_STORAGE_KEY) ?? "null") as Record<string, unknown> | null;

beforeEach(() => localStorage.clear());
afterEach(() => vi.restoreAllMocks());

describe("dayStage", () => {
  it.each([
    [4, 59, "night"], [5, 0, "dawn"], [7, 59, "dawn"], [8, 0, "morning"], [10, 59, "morning"],
    [11, 0, "noon"], [13, 59, "noon"], [14, 0, "afternoon"], [17, 59, "afternoon"],
    [18, 0, "evening"], [20, 59, "evening"], [21, 0, "night"], [23, 30, "night"], [0, 0, "night"],
  ])("%i:%i is %s", (h, min, phase) => {
    expect(dayStage(at(2026, 10, 11, h, min)).phase).toBe(phase);
  });

  it("starts the day at 05:00 and progresses continuously", () => {
    expect(dayStage(at(2026, 10, 11, 5)).progress).toBe(0);
    expect(dayStage(at(2026, 10, 11, 17)).progress).toBeCloseTo(0.5);
    expect(dayStage(at(2026, 10, 12, 4, 59)).progress).toBeGreaterThan(0.99);
    let previous = -1;
    for (let minutes = 0; minutes < 24 * 60; minutes += 15) {
      const time = new Date(at(2026, 10, 11, 5).getTime() + minutes * 60_000);
      const { progress, phaseProgress } = dayStage(time);
      expect(progress).toBeGreaterThan(previous);
      expect(phaseProgress).toBeGreaterThanOrEqual(0);
      expect(phaseProgress).toBeLessThan(1);
      previous = progress;
    }
  });

  it("treats night as resting and only night", () => {
    for (let h = 0; h < 24; h += 1) {
      const stage = dayStage(at(2026, 10, 11, h));
      expect(stage.resting).toBe(stage.phase === "night");
    }
    expect(dayStage(at(2026, 10, 11, 22)).resting).toBe(true);
    expect(dayStage(at(2026, 10, 11, 3)).resting).toBe(true);
  });

  it("uses a 05:00 local day boundary", () => {
    expect(localDayKey(at(2026, 10, 11, 4, 59))).toBe("2026-10-10");
    expect(localDayKey(at(2026, 10, 11, 5, 0))).toBe("2026-10-11");
    expect(localDayKey(at(2026, 1, 1, 2))).toBe("2025-12-31");
  });
});

describe("recordVisit", () => {
  it("counts distinct local days only once each (10 opens = 1 day)", () => {
    for (let i = 0; i < 10; i += 1) recordVisit(at(2026, 10, 11, 9, i));
    expect(readGrowth()?.days).toBe(1);
    recordVisit(at(2026, 10, 12, 8));
    recordVisit(at(2026, 10, 12, 20));
    expect(readGrowth()?.days).toBe(2);
  });

  it("stores only the four allowed fields, no timestamps or history", () => {
    recordVisit(at(2026, 10, 11, 9, 41));
    recordVisit(at(2026, 10, 13, 18, 7));
    const value = stored();
    expect(Object.keys(value ?? {}).sort()).toEqual(["days", "last", "seed", "v"]);
    expect(value).toMatchObject({ v: 1, days: 2, last: "2026-10-13" });
    const raw = localStorage.getItem(COMPANION_GROWTH_STORAGE_KEY) ?? "";
    expect(raw).not.toMatch(/\d:\d{2}|\d{13}/);
    expect(Object.keys(localStorage)).toEqual([COMPANION_GROWTH_STORAGE_KEY]);
  });

  it("never decreases across absences of 0, 1, 30 and 365 days, or a clock moved backwards", () => {
    let day = at(2026, 1, 10, 10);
    let previous = 0;
    for (const gap of [0, 1, 30, 365, 0, 1]) {
      day = new Date(day.getFullYear(), day.getMonth(), day.getDate() + gap, 10);
      const { state } = recordVisit(day);
      expect(state.days).toBeGreaterThanOrEqual(previous);
      expect(growthLevel(state.days)).toBeGreaterThanOrEqual(growthLevel(previous));
      previous = state.days;
    }
    const before = readGrowth()?.days ?? 0;
    const back = recordVisit(at(2020, 1, 1, 10));
    expect(back.counted).toBe(false);
    expect(back.state.days).toBe(before);
    expect(readGrowth()?.last).not.toBe("2020-01-01");
  });

  it("welcomes back after a gap with a calm gift and no count of missed days", () => {
    recordVisit(at(2026, 10, 1, 10));
    expect(recordVisit(at(2026, 10, 2, 10)).welcomeBack).toBe(false);
    const back = recordVisit(at(2026, 10, 20, 10));
    expect(back).toMatchObject({ counted: true, welcomeBack: true });
    expect(back.state.days).toBe(3);
    expect(WELCOME_BACK_COPY).not.toMatch(/\d/);
  });

  it("does not grow in the quiet hours 23:00–05:00", () => {
    const late = recordVisit(at(2026, 10, 11, 23, 30));
    expect(late.counted).toBe(false);
    expect(readGrowth()?.days).toBe(0);
    expect(recordVisit(at(2026, 10, 12, 4, 59)).counted).toBe(false);
    expect(recordVisit(at(2026, 10, 12, 5, 0)).counted).toBe(true);
    expect(readGrowth()?.days).toBe(1);
  });

  it("caps the counter", () => {
    localStorage.setItem(COMPANION_GROWTH_STORAGE_KEY, JSON.stringify({ v: 1, seed: 7, days: MAX_GROWTH_DAYS, last: "2026-01-01" }));
    expect(recordVisit(at(2026, 10, 11, 10)).state.days).toBe(MAX_GROWTH_DAYS);
  });

  it("creates the seed once from the platform CSPRNG, not from inputs", () => {
    const spy = vi.spyOn(globalThis.crypto, "getRandomValues").mockImplementation(<T extends ArrayBufferView>(array: T): T => {
      (array as unknown as Uint32Array)[0] = 0xdeadbeef;
      return array;
    });
    const first = recordVisit(at(2026, 10, 11, 10)).state.seed;
    expect(first).toBe(0xdeadbeef);
    expect(spy).toHaveBeenCalledTimes(1);
    expect(recordVisit(at(2026, 10, 12, 10)).state.seed).toBe(first);
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("gives different seeds to two fresh installs at the same moment", () => {
    const moment = at(2026, 10, 11, 10);
    const a = recordVisit(moment).state.seed;
    localStorage.clear();
    const b = recordVisit(moment).state.seed;
    expect(a).not.toBe(b);
  });

  it("rejects stored values with extra or malformed fields", () => {
    localStorage.setItem(COMPANION_GROWTH_STORAGE_KEY, JSON.stringify({ v: 1, seed: 1, days: 3, last: "2026-10-01", birth: "x" }));
    expect(readGrowth()).toBeNull();
    localStorage.setItem(COMPANION_GROWTH_STORAGE_KEY, JSON.stringify({ v: 1, seed: 1, days: -2, last: "2026-10-01" }));
    expect(readGrowth()).toBeNull();
    localStorage.setItem(COMPANION_GROWTH_STORAGE_KEY, "{oops");
    expect(readGrowth()).toBeNull();
  });
});

describe("growthLevel", () => {
  it("maps day thresholds to levels 0..6 and never goes down", () => {
    expect([0, 1, 2, 3, 6, 7, 13, 14, 29, 30, 59, 60, 119, 120, 400].map(growthLevel))
      .toEqual([0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6]);
    for (let d = 1; d <= 400; d += 1) expect(growthLevel(d)).toBeGreaterThanOrEqual(growthLevel(d - 1));
    expect(GROWTH_LEVEL_DAYS).toHaveLength(7);
  });
});

describe("lunar calendar and festivals", () => {
  it.each([
    [1985, "1985-01-21"], // Vietnam (UTC+7) differs from China this year
    [2007, "2007-02-17"], // Vietnam differs from China (02-18)
    [2024, "2024-02-10"], [2025, "2025-01-29"], [2026, "2026-02-17"], [2027, "2027-02-06"],
    [2028, "2028-01-26"], [2029, "2029-02-13"], [2030, "2030-02-02"], // China: 02-03
  ])("Tết %i is %s", (year, iso) => {
    const { year: y, month, day } = tetDate(year);
    expect(`${y}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`).toBe(iso);
  });

  it.each([
    [2024, "2024-09-17"], [2025, "2025-10-06"], [2026, "2026-09-25"], [2027, "2027-09-15"],
    [2028, "2028-10-03"], [2029, "2029-09-22"], [2030, "2030-09-12"],
  ])("Trung Thu %i is %s", (year, iso) => {
    const { year: y, month, day } = midAutumnDate(year);
    expect(`${y}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`).toBe(iso);
  });

  it("opens time-boxed festival windows", () => {
    expect(festivalSkin(at(2027, 2, 6, 10))).toMatchObject({ key: "tet", offsetDays: 0 });
    expect(festivalSkin(at(2027, 2, 1, 10))).toMatchObject({ key: "tet", offsetDays: -5 });
    expect(festivalSkin(at(2027, 1, 31, 10))).toBeNull();
    expect(festivalSkin(at(2027, 2, 12, 10))).toMatchObject({ key: "tet", offsetDays: 6 });
    expect(festivalSkin(at(2027, 2, 13, 10))).toBeNull();
    expect(festivalSkin(at(2026, 9, 25, 20))).toMatchObject({ key: "trung-thu", offsetDays: 0 });
    expect(festivalSkin(at(2026, 9, 20, 20))).toMatchObject({ key: "trung-thu" });
    expect(festivalSkin(at(2026, 9, 27, 20))).toBeNull();
    expect(festivalSkin(at(2026, 10, 11, 20))).toBeNull();
  });

  it("resolves the festival prop", () => {
    expect(resolveFestival(null, at(2027, 2, 6, 10))).toBeNull();
    expect(resolveFestival("auto", at(2027, 2, 6, 10))).toBe("tet");
    expect(resolveFestival("trung-thu", at(2026, 10, 11, 10))).toBe("trung-thu");
  });

  it("reuses the on-device moon model for lunar age", () => {
    const date = at(2026, 10, 18, 12);
    expect(lunarAge(date)).toBeCloseTo(moonPhase(date).age);
  });
});

describe("copy guardrails", () => {
  it("never guilt-trips, counts streaks or creates urgency", () => {
    const banned = /nhớ bạn|buồn vì|đợi bạn|đừng bỏ|sắp héo|héo rồi|cô đơn|streak|chuỗi|liên tiếp|chỉ hôm nay|lỡ là mất|bỏ lỡ/i;
    expect(GROWTH_RULE_COPY).not.toMatch(banned);
    expect(WELCOME_BACK_COPY).not.toMatch(banned);
  });
});
