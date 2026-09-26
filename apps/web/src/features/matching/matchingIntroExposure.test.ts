import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  markMatchingIntroConverted,
  MATCHING_INTRO_SESSION_KEY,
  MATCHING_INTRO_STORAGE_KEY,
  registerMatchingIntroVisit,
} from "../../shared/storage/matchingIntroExposure";

describe("matching intro exposure", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("advances once per app session and stops at visit three", () => {
    expect(registerMatchingIntroVisit()).toBe(1);
    expect(registerMatchingIntroVisit()).toBe(1);

    sessionStorage.clear();
    expect(registerMatchingIntroVisit()).toBe(2);

    sessionStorage.clear();
    expect(registerMatchingIntroVisit()).toBe(3);

    sessionStorage.clear();
    expect(registerMatchingIntroVisit()).toBe(3);
  });

  it.each([
    "not-json",
    JSON.stringify({ converted: false, visit: 0 }),
    JSON.stringify({ converted: false, visit: 4 }),
    JSON.stringify({ converted: false, visit: 1.5 }),
    JSON.stringify({ converted: "no", visit: 2 }),
  ])("falls back safely when the stored payload is invalid: %s", (payload) => {
    localStorage.setItem(MATCHING_INTRO_STORAGE_KEY, payload);

    expect(registerMatchingIntroVisit()).toBe(1);
    expect(JSON.parse(localStorage.getItem(MATCHING_INTRO_STORAGE_KEY) ?? "{}")).toEqual({
      converted: false,
      visit: 1,
    });
  });

  it("freezes the ladder after a matching profile is saved", () => {
    localStorage.setItem(MATCHING_INTRO_STORAGE_KEY, JSON.stringify({ converted: false, visit: 1 }));
    expect(registerMatchingIntroVisit()).toBe(2);
    markMatchingIntroConverted();

    sessionStorage.clear();
    expect(registerMatchingIntroVisit()).toBe(2);
    expect(JSON.parse(localStorage.getItem(MATCHING_INTRO_STORAGE_KEY) ?? "{}")).toEqual({
      converted: true,
      visit: 2,
    });
  });

  it("keeps the same visible visit when only the persistent write fails", () => {
    let writes = 0;
    const setItem = vi.fn(() => {
      writes += 1;
      if (writes === 1) throw new DOMException("blocked", "SecurityError");
    });
    const failingLocal = {
      getItem: vi.fn(() => JSON.stringify({ converted: false, visit: 2 })),
      setItem,
      removeItem: vi.fn(),
    } as unknown as Storage;

    expect(registerMatchingIntroVisit(failingLocal, sessionStorage)).toBe(2);
    expect(registerMatchingIntroVisit(failingLocal, sessionStorage)).toBe(2);
    expect(setItem).toHaveBeenCalledOnce();
  });

  it("keeps the page usable when browser storage is unavailable", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new DOMException("blocked", "SecurityError");
    });

    expect(registerMatchingIntroVisit()).toBe(1);
    expect(() => markMatchingIntroConverted()).not.toThrow();
  });

  it("uses no cross-session identifier or timestamp", () => {
    registerMatchingIntroVisit();

    expect(sessionStorage.getItem(MATCHING_INTRO_SESSION_KEY)).toBe("1");
    expect(localStorage.getItem(MATCHING_INTRO_STORAGE_KEY)).toBe(
      JSON.stringify({ converted: false, visit: 1 }),
    );
  });
});
