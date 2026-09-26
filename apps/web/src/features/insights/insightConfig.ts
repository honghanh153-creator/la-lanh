import type { Ayanamsa, HouseSystem, Tradition } from "../../shared/api/client";

type CalculationOption<Value extends string> = {
  value: Value;
  label: string;
};

export const WESTERN_HOUSE_OPTIONS: readonly CalculationOption<HouseSystem>[] = [
  { value: "placidus", label: "Placidus" },
  { value: "whole_sign", label: "Whole Sign" },
  { value: "equal", label: "Equal" },
];

export const JYOTISH_HOUSE_OPTIONS: readonly CalculationOption<HouseSystem>[] = [
  { value: "whole_sign", label: "Whole Sign" },
  { value: "equal", label: "Equal" },
];

export const AYANAMSA_OPTIONS: readonly CalculationOption<Ayanamsa>[] = [
  { value: "lahiri", label: "Lahiri · khuyên dùng" },
  { value: "raman", label: "Raman" },
  { value: "krishnamurti", label: "Krishnamurti" },
];

export function parseTradition(value: string | null): Tradition {
  return value === "jyotish" ? "jyotish" : "western";
}

export function defaultHouseSystem(tradition: Tradition): HouseSystem {
  return tradition === "jyotish" ? "whole_sign" : "placidus";
}

export function parseHouseSystem(value: string | null): HouseSystem | undefined {
  return value === "placidus" || value === "whole_sign" || value === "equal" ? value : undefined;
}

export function parseAyanamsa(value: string | null): Ayanamsa | undefined {
  return value === "lahiri" || value === "raman" || value === "krishnamurti" ? value : undefined;
}
