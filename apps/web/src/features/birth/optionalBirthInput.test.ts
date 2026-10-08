import { describe, expect, it } from "vitest";
import { birthDetailsError, emptyBirthDetails, hasBirthDetails } from "./optionalBirthInput";

describe("optional birth input", () => {
  it("needs neither assumed time nor extra consent for a blank unknown input", () => {
    expect(hasBirthDetails(emptyBirthDetails)).toBe(false);
    expect(birthDetailsError(emptyBirthDetails)).toBeNull();
  });
  it("accepts midnight but does not infer missing minutes", () => {
    expect(birthDetailsError({ ...emptyBirthDetails, mode: "exact", time: "00:00", consented: true })).toBeNull();
    expect(birthDetailsError({ ...emptyBirthDetails, mode: "exact", time: "07:" })).toMatch(/giờ và phút/);
  });
  it("accepts an approximate window without making up an exact time", () => {
    expect(birthDetailsError({ ...emptyBirthDetails, mode: "approx_window", window: "evening", consented: true })).toBeNull();
  });
  it("does not treat typed place text as a chosen reference", () => {
    expect(birthDetailsError({ ...emptyBirthDetails, placeText: "Hà Nội", consented: true })).toMatch(/Chọn một nơi/);
  });
  it("requires separate consent for place-only input even when birth time is unknown", () => {
    const place = { place_id: "hanoi", display_name: "Hà Nội", country_code: "VN", timezone_id: "Asia/Ho_Chi_Minh", confidence: "province-centroid" };
    expect(hasBirthDetails({ ...emptyBirthDetails, place })).toBe(true);
    expect(birthDetailsError({ ...emptyBirthDetails, place })).toMatch(/Đồng ý/);
    expect(birthDetailsError({ ...emptyBirthDetails, place, consented: true })).toBeNull();
  });
});
