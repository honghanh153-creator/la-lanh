import { QueryClient, QueryObserver } from "@tanstack/react-query";
import { afterEach, describe, expect, it } from "vitest";

import { chartDataRevision } from "./clearChartDerivedData";
import { dropCachedDailyNotes } from "./dropCachedDailyNotes";

// Synthetic note text only.
const yesterday = { id: "note-yesterday", body: "Ghi chú hôm qua" };

describe("dropCachedDailyNotes (PV-21)", () => {
  const unsubscribers: Array<() => void> = [];
  afterEach(() => {
    unsubscribers.splice(0).forEach((stop) => stop());
  });

  it("does not bring back a note a screen seeded as initialData when the reload fails", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    // Home seeds the Daily query from the offline cache; Profile keeps it active.
    const observer = new QueryObserver(client, {
      queryKey: ["daily-note"],
      queryFn: () => Promise.reject(new Error("offline")),
      initialData: yesterday,
      initialDataUpdatedAt: 0,
      staleTime: Infinity,
    });
    unsubscribers.push(observer.subscribe(() => undefined));
    expect(client.getQueryData(["daily-note"])).toEqual(yesterday);

    await dropCachedDailyNotes(client);

    expect(client.getQueryData(["daily-note"])).toBeUndefined();
    expect(observer.getCurrentResult().data).toBeUndefined();
  });

  it("fences pending Daily writers started before the clear", async () => {
    const client = new QueryClient();
    const before = chartDataRevision(client);

    await dropCachedDailyNotes(client);

    // HomePage and AuraCutoverPage drop a callback whose captured revision no longer matches.
    expect(chartDataRevision(client)).not.toBe(before);
  });
});
