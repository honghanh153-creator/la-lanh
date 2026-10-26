import { getConfig } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ASYNC_UTIL_TIMEOUT_MS } from "./setup";

describe("test harness timing", () => {
  it("gives async waits headroom over the measured full-suite chain and stays under the test timeout", () => {
    // Owner-bound Radar pages took up to 3.5 s to render under load; the old 1,000 ms default flaked.
    expect(getConfig().asyncUtilTimeout).toBe(ASYNC_UTIL_TIMEOUT_MS);
    expect(ASYNC_UTIL_TIMEOUT_MS).toBeGreaterThanOrEqual(5_000);
    expect(ASYNC_UTIL_TIMEOUT_MS).toBeLessThan(15_000);
  });
});
