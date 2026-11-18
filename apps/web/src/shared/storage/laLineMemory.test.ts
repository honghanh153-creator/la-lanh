import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearPersonalDataOnDevice } from "./clearPersonalData";
import {
  AUTHORED_PAIR,
  beginLaLineMemoryWrite,
  clearLaLineMemory,
  LA_LINE_MEMORY_KEY,
  lastLaLine,
  MAX_LA_LINE_ISSUES,
  rememberLaLine,
  type LaLineEntry,
} from "./laLineMemory";
import { SESSION_EPOCH_KEY } from "../session/sessionIdentity";
import { testLocks } from "../session/testLocks";

const A = "00000000-0000-4000-8000-0000000000a1";
const B = "00000000-0000-4000-8000-0000000000b2";
const entry = (pair: string, day: string, appearance = A): LaLineEntry => ({ pair, day, appearance });

describe("which line Lá said last, kept on the device (W1 phase 3, #626)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
    vi.stubGlobal("navigator", Object.create(navigator, { locks: { value: testLocks(), configurable: true } }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("remembers the pair id, server day and appearance per issue and reads them back", async () => {
    const owner = beginLaLineMemoryWrite();
    expect(lastLaLine("changed-plan")).toBeNull();
    await expect(rememberLaLine(owner, "changed-plan", entry("la.issue.changed-plan.02", "2026-11-18"))).resolves.toBe(true);
    await expect(rememberLaLine(owner, "missing-context", entry(AUTHORED_PAIR, "2026-11-18", B))).resolves.toBe(true);
    expect(lastLaLine("changed-plan")).toEqual(entry("la.issue.changed-plan.02", "2026-11-18"));
    expect(lastLaLine("missing-context")).toEqual(entry(AUTHORED_PAIR, "2026-11-18", B));
    expect(lastLaLine("comparison-loop")).toBeNull();
  });

  it("stores only the scope and, per issue, a catalog pair id, a date and a revision id", async () => {
    await rememberLaLine(beginLaLineMemoryWrite(), "changed-plan", entry("la.issue.changed-plan.02", "2026-11-18"));
    expect(JSON.parse(localStorage.getItem(LA_LINE_MEMORY_KEY) ?? "null")).toEqual({
      v: 2,
      scope: "epoch-a",
      issues: { "changed-plan": { pair: "la.issue.changed-plan.02", day: "2026-11-18", appearance: A } },
    });
  });

  it("refuses malformed keys, a pair of another issue, a slot number, a bad day or appearance", async () => {
    const owner = beginLaLineMemoryWrite();
    const bad: Array<[string, LaLineEntry]> = [
      ["Changed-Plan", entry("la.issue.changed-plan.02", "2026-11-18")],
      ["__proto__", entry(AUTHORED_PAIR, "2026-11-18")],
      ["changed-plan", entry("la.issue.missing-context.02", "2026-11-18")],
      ["changed-plan", entry("2", "2026-11-18")],
      ["changed-plan", entry("la.issue.changed-plan.2", "2026-11-18")],
      ["changed-plan", entry("la.issue.changed-plan.02.direct", "2026-11-18")],
      ["changed-plan", entry(AUTHORED_PAIR, "18/11/2026")],
      ["changed-plan", entry(AUTHORED_PAIR, "2026-13-45")],
      ["changed-plan", entry(AUTHORED_PAIR, "2026-11-18", "not-a-revision")],
      ["changed-plan", { ...entry(AUTHORED_PAIR, "2026-11-18"), text: "a sentence" } as LaLineEntry],
    ];
    for (const [issue, value] of bad) await expect(rememberLaLine(owner, issue, value)).resolves.toBe(false);
    expect(localStorage.getItem(LA_LINE_MEMORY_KEY)).toBeNull();
    await expect(rememberLaLine(null, "changed-plan", entry(AUTHORED_PAIR, "2026-11-18"))).resolves.toBe(false);
  });

  it("never moves backwards: an older server day does not replace a newer one", async () => {
    const owner = beginLaLineMemoryWrite();
    await rememberLaLine(owner, "changed-plan", entry("la.issue.changed-plan.03", "2026-11-18"));
    await expect(rememberLaLine(owner, "changed-plan", entry("la.issue.changed-plan.01", "2026-11-17"))).resolves.toBe(false);
    expect(lastLaLine("changed-plan")?.pair).toBe("la.issue.changed-plan.03");
    await expect(rememberLaLine(owner, "changed-plan", entry("la.issue.changed-plan.04", "2026-11-18", B))).resolves.toBe(true);
    expect(lastLaLine("changed-plan")).toEqual(entry("la.issue.changed-plan.04", "2026-11-18", B));
  });

  it("merges with what another tab wrote meanwhile instead of overwriting it", async () => {
    const tab1 = beginLaLineMemoryWrite();
    const tab2 = beginLaLineMemoryWrite();
    await Promise.all([
      rememberLaLine(tab1, "changed-plan", entry("la.issue.changed-plan.02", "2026-11-18")),
      rememberLaLine(tab2, "missing-context", entry(AUTHORED_PAIR, "2026-11-18", B)),
    ]);
    expect(lastLaLine("changed-plan")?.pair).toBe("la.issue.changed-plan.02");
    expect(lastLaLine("missing-context")?.pair).toBe(AUTHORED_PAIR);
  });

  it("drops a late write after the memory was cleared or the session changed", async () => {
    const before = beginLaLineMemoryWrite();
    expect(clearLaLineMemory()).toBe(true);
    await expect(rememberLaLine(before, "changed-plan", entry(AUTHORED_PAIR, "2026-11-18"))).resolves.toBe(false);
    expect(localStorage.getItem(LA_LINE_MEMORY_KEY)).toBeNull();

    const owner = beginLaLineMemoryWrite();
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-b");
    await expect(rememberLaLine(owner, "changed-plan", entry(AUTHORED_PAIR, "2026-11-18"))).resolves.toBe(false);
    expect(localStorage.getItem(LA_LINE_MEMORY_KEY)).toBeNull();
  });

  it("ignores another session's record", async () => {
    await rememberLaLine(beginLaLineMemoryWrite(), "changed-plan", entry(AUTHORED_PAIR, "2026-11-18"));
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-b");
    expect(lastLaLine("changed-plan")).toBeNull();
  });

  it("keeps at most the newest issues and drops the one seen longest ago", async () => {
    const owner = beginLaLineMemoryWrite();
    for (let index = 0; index <= MAX_LA_LINE_ISSUES; index += 1) {
      await rememberLaLine(owner, `issue-${index}`, entry(AUTHORED_PAIR, "2026-11-18"));
    }
    expect(lastLaLine("issue-0")).toBeNull();
    expect(lastLaLine(`issue-${MAX_LA_LINE_ISSUES}`)).not.toBeNull();
    const stored = JSON.parse(localStorage.getItem(LA_LINE_MEMORY_KEY) ?? "{}") as { issues: object };
    expect(Object.keys(stored.issues)).toHaveLength(MAX_LA_LINE_ISSUES);
  });

  it("reads a tampered or old-format record as nothing", () => {
    for (const raw of ["{", "null", "[]", JSON.stringify({ v: 1, lines: { "changed-plan": 2 } }),
      JSON.stringify({ v: 2, scope: "epoch-a", issues: { "changed-plan": { pair: "7", day: "2026-11-18", appearance: A } } })]) {
      localStorage.setItem(LA_LINE_MEMORY_KEY, raw);
      expect(lastLaLine("changed-plan")).toBeNull();
    }
  });

  it("blocked storage never breaks the screen", async () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    expect(lastLaLine("changed-plan")).toBeNull();
    await expect(rememberLaLine({ sessionEpoch: "epoch-a", generation: 0, clears: 0 }, "changed-plan", entry(AUTHORED_PAIR, "2026-11-18"))).resolves.toBe(false);
    expect(clearLaLineMemory()).toBe(false);
  });

  it("goes with delete profile, sign-out and session change (clearPersonalDataOnDevice)", async () => {
    await rememberLaLine(beginLaLineMemoryWrite(), "changed-plan", entry(AUTHORED_PAIR, "2026-11-18"));
    expect(localStorage.getItem(LA_LINE_MEMORY_KEY)).not.toBeNull();
    await clearPersonalDataOnDevice();
    expect(localStorage.getItem(LA_LINE_MEMORY_KEY)).toBeNull();
  });
});
