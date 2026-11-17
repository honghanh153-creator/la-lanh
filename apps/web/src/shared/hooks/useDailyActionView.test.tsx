import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import type { MoodValue, ReadingContent } from "../api/client";
import { clearChartDerivedData } from "../storage/clearChartDerivedData";
import { dailyActionViewKey, resetDailyActionChoice, useDailyActionView } from "./useDailyActionView";

const NOTE_ID = "00000000-0000-4000-8000-000000000001";
const reading = {
  lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light", experiment: null },
} as unknown as ReadingContent;

function setup(confirmedMood: MoodValue | null, content: ReadingContent | null = reading) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  const hook = renderHook(({ mood }: { mood: MoodValue | null }) => useDailyActionView(NOTE_ID, content, mood), { wrapper, initialProps: { mood: confirmedMood } });
  return { client, ...hook };
}

describe("useDailyActionView (#627)", () => {
  it("shows the lighter action first only for a saved Đuối mood with a lighter action", () => {
    expect(setup("Đuối").result.current).toMatchObject({ lighterShown: true, canSwitch: true });
    expect(setup("Chill").result.current).toMatchObject({ lighterShown: false, canSwitch: false });
    expect(setup(null).result.current).toMatchObject({ lighterShown: false, canSwitch: false });
    expect(setup("Đuối", {} as ReadingContent).result.current).toMatchObject({ lighterShown: false, canSwitch: false });
  });

  it("follows the saved mood in every order, with nothing remembered from an earlier mood", () => {
    // The hook keeps no mood of its own, so any sequence of saved moods gives the same answer as
    // the last one alone: two tabs, a slow read, a failed save all reduce to this.
    const { result, rerender } = setup("Chill");
    for (const mood of ["Đuối", "Chill", "Đuối", null, "Rực", "Đuối"] as const) {
      rerender({ mood });
      expect(result.current, String(mood)).toMatchObject({ lighterShown: mood === "Đuối", canSwitch: mood === "Đuối" });
    }
  });

  it("lets the reader switch back and forth, and offers no switch for another mood", async () => {
    const { result, rerender } = setup("Đuối");
    // The query cache notifies on the next tick, so each step waits for the hook to settle.
    act(() => result.current.switchAction());
    await waitFor(() => expect(result.current).toMatchObject({ lighterShown: false, canSwitch: true }));
    act(() => result.current.switchAction());
    await waitFor(() => expect(result.current).toMatchObject({ lighterShown: true, canSwitch: true }));
    rerender({ mood: "Chill" });
    act(() => result.current.switchAction());
    expect(result.current).toMatchObject({ lighterShown: false, canSwitch: false });
  });

  it("starts a newly confirmed mood from the lighter action again", async () => {
    const { client, result } = setup("Đuối");
    act(() => result.current.switchAction());
    await waitFor(() => expect(result.current.lighterShown).toBe(false));
    act(() => resetDailyActionChoice(client, NOTE_ID));
    await waitFor(() => expect(result.current.lighterShown).toBe(true));
  });

  it("keeps only the switch press in memory, and drops it when chart-derived data is cleared", async () => {
    const { client, result } = setup("Đuối");
    act(() => result.current.switchAction());
    await waitFor(() => expect(result.current.lighterShown).toBe(false));
    // No mood is copied into this cache or into device storage.
    expect(client.getQueryData(dailyActionViewKey(NOTE_ID))).toEqual({ choice: "original" });
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain("Đuối");
    await act(async () => { await clearChartDerivedData(client); });
    await waitFor(() => expect(result.current.lighterShown).toBe(true));
  });
});
