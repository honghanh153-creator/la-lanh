import { describe, expect, it } from "vitest";
import { dailyContextPath, dailyContextQueryKey, parseDailyContext } from "./dailyContext";

describe("Daily context navigation", () => {
  it.each(["work", "relationships", "communication", "energy", "self_care"])("accepts the known %s context", (value) => {
    expect(parseDailyContext(value)).toBe(value);
  });

  it.each([null, "", "auto", "WORK", "unknown", "work&unexpected=value"])("does not forward an invalid context %s", (value) => {
    expect(parseDailyContext(value)).toBe("auto");
  });

  it("keeps the auto route compatible and gives contextual reads a distinct cache key", () => {
    expect(dailyContextPath("/note/today", "auto")).toBe("/note/today");
    expect(dailyContextPath("/card", "work")).toBe("/card?context=work");
    expect(dailyContextQueryKey("auto")).toEqual(["daily-note"]);
    expect(dailyContextQueryKey("work")).toEqual(["daily-note-context", "work"]);
  });
});
