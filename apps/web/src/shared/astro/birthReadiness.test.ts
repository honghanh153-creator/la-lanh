import { describe, expect, it } from "vitest";
import type { BirthSupplementState } from "../api/client";
import { birthCompletionPrompt } from "./birthReadiness";

const base: BirthSupplementState = { profile_id: "test", profile_level: 1, birth_time_mode: "unknown", time_precision: "unknown", place_display_name: null, timezone_id: null, approx_window: null };
describe("birth completion CTA", () => {
  it("does not guess missing data while the server is loading or unavailable", () => {
    expect(birthCompletionPrompt(undefined)).toBeNull();
  });
  it("asks for both fields on a confirmed date-only profile", () => {
    expect(birthCompletionPrompt(base)?.cta).toBe("Thêm giờ & nơi sinh");
  });
  it("does not ask for birth time again when only place is missing", () => {
    expect(birthCompletionPrompt({ ...base, profile_level: 2, birth_time_mode: "exact", time_precision: "exact" })?.cta).toBe("Thêm nơi sinh");
  });
  it("asks for time when the place is already present", () => {
    expect(birthCompletionPrompt({ ...base, place_display_name: "Hà Nội", timezone_id: "Asia/Ho_Chi_Minh" })?.cta).toBe("Thêm giờ sinh");
  });
  it("distinguishes approximate time from missing time even at level 3", () => {
    expect(birthCompletionPrompt({ ...base, profile_level: 3, birth_time_mode: "approx_window", time_precision: "approximate", place_display_name: "Hà Nội", timezone_id: "Asia/Ho_Chi_Minh" })?.cta).toBe("Làm rõ giờ sinh");
  });
  it("hides the supplement CTA for exact time and a confirmed timezone/place", () => {
    expect(birthCompletionPrompt({ ...base, profile_level: 3, birth_time_mode: "exact", time_precision: "exact", place_display_name: "Hà Nội", timezone_id: "Asia/Ho_Chi_Minh" })).toBeNull();
  });
});
