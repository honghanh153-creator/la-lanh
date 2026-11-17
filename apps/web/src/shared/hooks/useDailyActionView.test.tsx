import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import type { MoodValue, ReadingContent } from "../api/client";
import { clearChartDerivedData } from "../storage/clearChartDerivedData";
import { noteDailyMood, useDailyActionView } from "./useDailyActionView";

const NOTE_ID = "00000000-0000-4000-8000-000000000001";
const reading = {
  lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light", experiment: null },
} as unknown as ReadingContent;

function setup(savedMood: MoodValue | null, content: ReadingContent | null = reading) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  return { client, ...renderHook(() => useDailyActionView(NOTE_ID, content, savedMood), { wrapper }) };
}

describe("useDailyActionView (#627)", () => {
  it("shows the lighter action first only for a saved Đuối mood with a lighter action", () => {
    expect(setup("Đuối").result.current).toMatchObject({ lighterShown: true, canSwitch: true });
    expect(setup("Chill").result.current).toMatchObject({ lighterShown: false, canSwitch: false });
    expect(setup(null).result.current).toMatchObject({ lighterShown: false, canSwitch: false });
    expect(setup("Đuối", {} as ReadingContent).result.current).toMatchObject({ lighterShown: false, canSwitch: false });
  });

  it("lets the mood just picked win over the saved one and resets a manual choice", async () => {
    const { client, result } = setup("Chill");
    // The query cache notifies on the next tick, so each step waits for the hook to settle.
    act(() => noteDailyMood(client, NOTE_ID, "Đuối"));
    await waitFor(() => expect(result.current.lighterShown).toBe(true));
    act(() => result.current.switchAction());
    await waitFor(() => expect(result.current).toMatchObject({ lighterShown: false, canSwitch: true }));
    act(() => noteDailyMood(client, NOTE_ID, "Đuối"));
    await waitFor(() => expect(result.current.lighterShown).toBe(true));
    act(() => noteDailyMood(client, NOTE_ID, "Rực"));
    await waitFor(() => expect(result.current).toMatchObject({ lighterShown: false, canSwitch: false }));
  });

  it("forgets the picked mood and the choice when chart-derived data is cleared", async () => {
    const { client, result } = setup(null);
    act(() => noteDailyMood(client, NOTE_ID, "Đuối"));
    await waitFor(() => expect(result.current.lighterShown).toBe(true));
    await act(async () => { await clearChartDerivedData(client); });
    await waitFor(() => expect(result.current).toMatchObject({ lighterShown: false, canSwitch: false }));
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain("Đuối");
  });
});
