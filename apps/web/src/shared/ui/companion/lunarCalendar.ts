// Vietnamese lunisolar calendar, computed on the device for UTC+7.
//
// Own implementation of the standard rules used by Vietnamese calendars:
// a month starts on the local (UTC+7) day of the astronomical new moon;
// month 11 contains the winter solstice; in a 13-month year the leap month is
// the first month without a principal solar term. Astronomy uses the
// published formulas from J. Meeus, "Astronomical Algorithms" (2nd ed.),
// ch. 25 (solar longitude, low precision) and ch. 49 (new moon, main
// periodic terms). Accuracy is a few minutes for 1900–2100, enough to get the
// UTC+7 day right in years where Vietnam and China differ (e.g. Tết 1985,
// 2007, 2030). Used only for decorative, time-boxed festival skins.

const DEG = Math.PI / 180;
const TZ_DAYS = 7 / 24;
/** Mean ΔT (TT − UT) for the 2000–2040 range, in days. ~70 s. */
const DELTA_T_DAYS = 70 / 86_400;

export type CivilDate = { year: number; month: number; day: number };

function sin(degrees: number): number {
  return Math.sin(degrees * DEG);
}

/** Julian Day Number (integer, noon-based) of a Gregorian civil date. */
export function julianDayNumber({ year, month, day }: CivilDate): number {
  const a = Math.floor((14 - month) / 12);
  const y = year + 4800 - a;
  const m = month + 12 * a - 3;
  return day + Math.floor((153 * m + 2) / 5) + 365 * y + Math.floor(y / 4)
    - Math.floor(y / 100) + Math.floor(y / 400) - 32045;
}

export function civilFromJulianDayNumber(jdn: number): CivilDate {
  const a = jdn + 32044;
  const b = Math.floor((4 * a + 3) / 146097);
  const c = a - Math.floor((146097 * b) / 4);
  const d = Math.floor((4 * c + 3) / 1461);
  const e = c - Math.floor((1461 * d) / 4);
  const m = Math.floor((5 * e + 2) / 153);
  return {
    day: e - Math.floor((153 * m + 2) / 5) + 1,
    month: m + 3 - 12 * Math.floor(m / 10),
    year: 100 * b + d - 4800 + Math.floor(m / 10),
  };
}

/** Julian Date (UT) of the k-th new moon after 2000-01-06 (Meeus ch. 49). */
function newMoonJd(k: number): number {
  const t = k / 1236.85;
  const t2 = t * t;
  const t3 = t2 * t;
  const t4 = t3 * t;
  const jde = 2451550.09766 + 29.530588861 * k + 0.00015437 * t2 - 0.00000015 * t3 + 0.00000000073 * t4;
  const e = 1 - 0.002516 * t - 0.0000074 * t2;
  const m = 2.5534 + 29.1053567 * k - 0.0000014 * t2 - 0.00000011 * t3;
  const mp = 201.5643 + 385.81693528 * k + 0.0107582 * t2 + 0.00001238 * t3 - 0.000000058 * t4;
  const f = 160.7108 + 390.67050284 * k - 0.0016118 * t2 - 0.00000227 * t3 + 0.000000011 * t4;
  const om = 124.7746 - 1.56375588 * k + 0.0020672 * t2 + 0.00000215 * t3;
  const correction =
    -0.4072 * sin(mp)
    + 0.17241 * e * sin(m)
    + 0.01608 * sin(2 * mp)
    + 0.01039 * sin(2 * f)
    + 0.00739 * e * sin(mp - m)
    - 0.00514 * e * sin(mp + m)
    + 0.00208 * e * e * sin(2 * m)
    - 0.00111 * sin(mp - 2 * f)
    - 0.00057 * sin(mp + 2 * f)
    + 0.00056 * e * sin(2 * mp + m)
    - 0.00042 * sin(3 * mp)
    + 0.00042 * e * sin(m + 2 * f)
    + 0.00038 * e * sin(m - 2 * f)
    - 0.00024 * e * sin(2 * mp - m)
    - 0.00017 * sin(om)
    - 0.00007 * sin(mp + 2 * m)
    + 0.00004 * sin(2 * mp - 2 * f)
    + 0.00004 * sin(3 * m)
    + 0.00003 * sin(mp + m - 2 * f)
    + 0.00003 * sin(2 * mp + 2 * f)
    - 0.00003 * sin(mp + m + 2 * f)
    + 0.00003 * sin(mp - m + 2 * f)
    - 0.00002 * sin(mp - m - 2 * f)
    - 0.00002 * sin(3 * mp + m)
    + 0.00002 * sin(4 * mp);
  return jde + correction - DELTA_T_DAYS;
}

/** Local (UTC+7) day number on which the k-th new moon falls. */
function newMoonDay(k: number): number {
  return Math.floor(newMoonJd(k) + 0.5 + TZ_DAYS);
}

/** Apparent solar longitude in degrees [0, 360) at Julian Date `jd` (Meeus ch. 25). */
function sunLongitude(jd: number): number {
  const t = (jd - 2451545) / 36525;
  const l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t;
  const m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t;
  const c = (1.914602 - 0.004817 * t - 0.000014 * t * t) * sin(m)
    + (0.019993 - 0.000101 * t) * sin(2 * m)
    + 0.000289 * sin(3 * m);
  const omega = 125.04 - 1934.136 * t;
  const apparent = l0 + c - 0.00569 - 0.00478 * sin(omega);
  return ((apparent % 360) + 360) % 360;
}

/** Solar-term sector (0–11, 30° each) at the local midnight starting `day`. */
function sectorAtDayStart(day: number): number {
  return Math.floor(sunLongitude(day - 0.5 - TZ_DAYS) / 30);
}

function kNear(day: number): number {
  return Math.floor((day - 0.5 - 2451550.09766) / 29.530588861);
}

/** Local day number on which lunar month 11 of Gregorian `year` begins. */
function month11Start(year: number): number {
  const dec31 = julianDayNumber({ year, month: 12, day: 31 });
  let k = kNear(dec31) + 1;
  while (newMoonDay(k) > dec31) k -= 1;
  // The solstice (270°) must fall inside the month: if the month starting
  // here already begins at or past 270°, the solstice month is the previous one.
  while (sectorAtDayStart(newMoonDay(k)) >= 9) k -= 1;
  return newMoonDay(k);
}

type LunarMonth = { start: number; month: number; leap: boolean };

const yearCache = new Map<number, LunarMonth[]>();

/** Months from month 11 of `year - 1` up to (not including) month 11 of `year`. */
function lunarMonthsEnding(year: number): LunarMonth[] {
  const cached = yearCache.get(year);
  if (cached) return cached;
  const a11 = month11Start(year - 1);
  const b11 = month11Start(year);
  const starts: number[] = [];
  let k = kNear(a11) - 1;
  while (newMoonDay(k) < a11) k += 1;
  while (newMoonDay(k) < b11) {
    starts.push(newMoonDay(k));
    k += 1;
  }
  let leapIndex = -1;
  if (starts.length === 13) {
    for (let i = 1; i < starts.length; i += 1) {
      const next = i + 1 < starts.length ? starts[i + 1] : b11;
      if (sectorAtDayStart(starts[i]) === sectorAtDayStart(next)) {
        leapIndex = i;
        break;
      }
    }
  }
  const months = starts.map((start, i) => {
    const offset = leapIndex >= 0 && i >= leapIndex ? i - 1 : i;
    return { start, month: ((10 + offset) % 12) + 1, leap: i === leapIndex };
  });
  yearCache.set(year, months);
  return months;
}

/** Gregorian date of lunar `day`/`month` (non-leap) in the lunar year that starts in Gregorian `year`. */
export function lunarToSolar(year: number, month: number, day: number): CivilDate {
  // Months 1–10 of lunar year `year` lie between month 11 of (year-1) and
  // month 11 of `year`; months 11–12 begin at month 11 of `year`.
  const source = month >= 11 ? lunarMonthsEnding(year + 1) : lunarMonthsEnding(year);
  const found = source.find((entry) => entry.month === month && !entry.leap);
  if (!found) throw new Error(`No lunar month ${month} in ${year}`);
  return civilFromJulianDayNumber(found.start + day - 1);
}

/** Mùng 1 Tết (lunar 1/1) for the lunar year beginning in Gregorian `year`. */
export function tetDate(year: number): CivilDate {
  return lunarToSolar(year, 1, 1);
}

/** Tết Trung Thu (Rằm tháng Tám, lunar 15/8) in Gregorian `year`. */
export function midAutumnDate(year: number): CivilDate {
  return lunarToSolar(year, 8, 15);
}
