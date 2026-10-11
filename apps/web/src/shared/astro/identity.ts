import type { BirthReveal, ZodiacSign } from "../api/client";
import { primarySunSign } from "./chart";

type Calculation = BirthReveal["calculation"];

export type Element = "fire" | "earth" | "air" | "water";

export const SIGN_ELEMENT: Record<ZodiacSign, Element> = {
  aries: "fire", leo: "fire", sagittarius: "fire",
  taurus: "earth", virgo: "earth", capricorn: "earth",
  gemini: "air", libra: "air", aquarius: "air",
  cancer: "water", scorpio: "water", pisces: "water",
};

export const ELEMENT_LABEL: Record<Element, string> = {
  fire: "Lửa", earth: "Đất", air: "Khí", water: "Nước",
};

export type IdentitySlot = {
  key: "sun" | "moon" | "rising";
  label: string;
  sign: ZodiacSign | null;
  /** Why the slot is still locked, in plain words. */
  lockedHint: string;
};

/**
 * The "big three" that the stored calculation can honestly support. Moon and
 * rising need an exact birth time; anything less stays locked rather than
 * guessed.
 */
export function identityFromCalculation(calculation: Calculation | null | undefined): IdentitySlot[] {
  const sun = calculation ? primarySunSign(calculation) : null;
  let moon: ZodiacSign | null = null;
  let rising: ZodiacSign | null = null;
  if (calculation && !("status" in calculation) && calculation.time_precision === "exact") {
    moon = calculation.bodies.find((body) => body.body === "moon")?.sign ?? null;
    rising = calculation.houses?.find((house) => house.number === 1)?.sign ?? null;
  }
  return [
    { key: "sun", label: "Mặt Trời", sign: sun, lockedHint: "Mở khi có ngày sinh" },
    { key: "moon", label: "Mặt Trăng", sign: moon, lockedHint: "Mở khi thêm giờ sinh chính xác" },
    { key: "rising", label: "Cung Mọc", sign: rising, lockedHint: "Mở khi thêm giờ và nơi sinh" },
  ];
}
