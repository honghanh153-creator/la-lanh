import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";

import { ApiProblem } from "../shared/api/client";
import { shouldRetryQuery } from "./queryRetry";

function client() {
  return new QueryClient({ defaultOptions: { queries: { retry: shouldRetryQuery, retryDelay: 0 } } });
}

describe("default query retry policy", () => {
  it("does not repeat a request the server rejected as unusable content (422)", async () => {
    const queryFn = vi.fn().mockRejectedValue(new ApiProblem(422, "READING_CONTENT_REJECTED", "rejected"));

    await expect(client().fetchQuery({ queryKey: ["synthetic-note"], queryFn })).rejects.toBeInstanceOf(ApiProblem);
    expect(queryFn).toHaveBeenCalledTimes(1);
  });

  it("still retries a transient failure once", async () => {
    const queryFn = vi.fn().mockRejectedValue(new ApiProblem(503, "UPSTREAM_UNAVAILABLE", "busy"));

    await expect(client().fetchQuery({ queryKey: ["synthetic-note"], queryFn })).rejects.toBeInstanceOf(ApiProblem);
    expect(queryFn).toHaveBeenCalledTimes(2);
  });

  it("keeps retrying other 422 codes as before", () => {
    expect(shouldRetryQuery(0, new ApiProblem(422, "OTHER_CODE", "x"))).toBe(true);
    expect(shouldRetryQuery(1, new Error("network"))).toBe(false);
  });
});
