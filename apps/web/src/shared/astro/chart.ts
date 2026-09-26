import type { BirthReveal, ZodiacSign } from "../api/client";

type Calculation = BirthReveal["calculation"];

export function sunSignsFromCalculation(calculation: Calculation): ZodiacSign[] {
  if ("status" in calculation) {
    if (calculation.status === "certain" && calculation.sign) return [calculation.sign];
    return [...calculation.candidates];
  }
  const sun = calculation.bodies.find((body) => body.body === "sun");
  return sun ? [sun.sign] : [];
}

export function primarySunSign(calculation: Calculation): ZodiacSign | null {
  return sunSignsFromCalculation(calculation)[0] ?? null;
}

export function isDateOnlyCalculation(calculation: Calculation): boolean {
  return "status" in calculation;
}
