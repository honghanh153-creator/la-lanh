import { QueryClient, QueryObserver } from "@tanstack/react-query";
import { waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { clearChartDerivedData } from "./clearChartDerivedData";

describe("chart precision cache withdrawal", () => {
  it("cancels an old response so it cannot restore an erased private reading", async () => {
    const client = new QueryClient();
    let complete!: (value: string) => void;
    const oldResponse = new Promise<string>((resolve) => { complete = resolve; });
    const key = ["private-reading", "natal"];
    const request = client.fetchQuery({ queryKey: key, queryFn: () => oldResponse });
    const settled = request.catch(() => undefined);
    await clearChartDerivedData(client);
    complete("erased precise reading");
    await settled;
    expect(client.getQueryData(key)).toBeUndefined();
    client.clear();
  });

  it("removes active old text before refreshing and leaves unrelated Tarot intact", async () => {
    const client = new QueryClient();
    const key = ["insight-overview", "western"];
    client.setQueryData(key, "old precise houses");
    client.setQueryData(["tarot-session", "independent"], "selected cards");
    let complete!: (value: string) => void;
    const newResponse = new Promise<string>((resolve) => { complete = resolve; });
    const observer = new QueryObserver(client, {
      queryKey: key, queryFn: () => newResponse, staleTime: Infinity,
    });
    const unsubscribe = observer.subscribe(() => undefined);
    const clearing = clearChartDerivedData(client);
    await waitFor(() => expect(observer.getCurrentResult().data).toBeUndefined());
    complete("date-only overview");
    await clearing;
    expect(observer.getCurrentResult().data).toBe("date-only overview");
    expect(client.getQueryData(["tarot-session", "independent"])).toBe("selected cards");
    unsubscribe();
    client.clear();
  });
});
