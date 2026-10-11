import type { BirthReveal } from "../api/client";
import { identityFromCalculation, SIGN_ELEMENT } from "./identity";

type Calculation = BirthReveal["calculation"];

describe("identityFromCalculation", () => {
  it("keeps moon and rising locked for a date-only profile", () => {
    const slots = identityFromCalculation({ status: "certain", sign: "gemini", candidates: ["gemini"] } as unknown as Calculation);
    expect(slots.map((slot) => [slot.key, slot.sign])).toEqual([["sun", "gemini"], ["moon", null], ["rising", null]]);
  });

  it("does not guess moon or rising without an exact time", () => {
    const chart = {
      time_precision: "approximate",
      bodies: [{ body: "sun", sign: "leo" }, { body: "moon", sign: "pisces" }],
      houses: [{ number: 1, sign: "virgo", longitude: 160 }],
    } as unknown as Calculation;
    expect(identityFromCalculation(chart).map((slot) => slot.sign)).toEqual(["leo", null, null]);
  });

  it("reads moon and the first house sign with an exact time", () => {
    const chart = {
      time_precision: "exact",
      bodies: [{ body: "sun", sign: "leo" }, { body: "moon", sign: "pisces" }],
      houses: [{ number: 2, sign: "libra", longitude: 190 }, { number: 1, sign: "virgo", longitude: 160 }],
    } as unknown as Calculation;
    expect(identityFromCalculation(chart).map((slot) => slot.sign)).toEqual(["leo", "pisces", "virgo"]);
  });

  it("maps every sign to one element", () => {
    expect(Object.keys(SIGN_ELEMENT)).toHaveLength(12);
  });
});
