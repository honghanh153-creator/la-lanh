// Real sky context, computed on the device from the date alone. It is ambient
// framing for Lá's greeting, never a claim that the Moon caused a reading.
const SYNODIC_DAYS = 29.530588853;
// Reference new moon: 2000-01-06 18:14 UTC.
const REFERENCE_NEW_MOON_MS = Date.UTC(2000, 0, 6, 18, 14);
const DAY_MS = 86_400_000;

export type MoonPhaseKey =
  | "new" | "waxing_crescent" | "first_quarter" | "waxing_gibbous"
  | "full" | "waning_gibbous" | "last_quarter" | "waning_crescent";

export type MoonPhase = {
  key: MoonPhaseKey;
  label: string;
  /** Days since the last new moon, 0 ≤ age < 29.53. */
  age: number;
  /** Lit fraction of the disc, 0 (new) to 1 (full). */
  illumination: number;
  waxing: boolean;
};

const LABELS: Record<MoonPhaseKey, string> = {
  new: "Trăng mới",
  waxing_crescent: "Trăng lưỡi liềm đầu tháng",
  first_quarter: "Trăng thượng huyền",
  waxing_gibbous: "Trăng sắp tròn",
  full: "Trăng tròn",
  waning_gibbous: "Trăng vừa qua rằm",
  last_quarter: "Trăng hạ huyền",
  waning_crescent: "Trăng lưỡi liềm cuối tháng",
};

export function moonPhase(at: Date = new Date()): MoonPhase {
  const elapsed = (at.getTime() - REFERENCE_NEW_MOON_MS) / DAY_MS;
  const age = ((elapsed % SYNODIC_DAYS) + SYNODIC_DAYS) % SYNODIC_DAYS;
  const illumination = (1 - Math.cos((2 * Math.PI * age) / SYNODIC_DAYS)) / 2;
  const key: MoonPhaseKey =
    age < 1.2 || age >= 28.3 ? "new"
      : age < 6.4 ? "waxing_crescent"
        : age < 8.4 ? "first_quarter"
          : age < 13.8 ? "waxing_gibbous"
            : age < 15.8 ? "full"
              : age < 21.1 ? "waning_gibbous"
                : age < 23.1 ? "last_quarter"
                  : "waning_crescent";
  return { key, label: LABELS[key], age, illumination, waxing: age < SYNODIC_DAYS / 2 };
}
