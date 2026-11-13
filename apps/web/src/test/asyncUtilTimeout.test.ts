import { getConfig } from "@testing-library/react";
import { describe, expect, it } from "vitest";

// Deliberately does not import ./setup: the wait must arrive through vite.config.ts `setupFiles`,
// and the ceiling is the resolved Vitest `testTimeout`, not a copy of it.
describe("test harness timing", () => {
  it("gives async waits headroom over the measured full-suite chain and stays under the test timeout", ({
    task,
  }) => {
    // Owner-bound Radar pages took up to 3.5 s to render under load; the old 1,000 ms default flaked.
    const asyncUtilTimeout = getConfig().asyncUtilTimeout;
    expect(asyncUtilTimeout).toBeGreaterThanOrEqual(5_000);
    expect(asyncUtilTimeout).toBeLessThan(task.timeout);
  });
});
