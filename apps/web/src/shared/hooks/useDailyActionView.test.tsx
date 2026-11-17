import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";

import type { MoodValue, ReadingContent } from "../api/client";
import { clearChartDerivedData } from "../storage/clearChartDerivedData";
import { dailyMoodKey, noteDailyMood, useDailyActionView } from "./useDailyActionView";

const NOTE_ID = "00000000-0000-4000-8000-000000000001";
const reading = {
  lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light", experiment: null },
} as unknown as ReadingContent;

const savedRow = (mood: MoodValue) => ({ id: "synthetic-mood", daily_note_id: NOTE_ID, mood, checked_in_at: "2026-09-07T00:00:00Z" });

/** The saved mood lives in the shared mood query, as on Home and the note page. */
function setup(savedMood: MoodValue | null, content: ReadingContent | null = reading) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  client.setQueryData(dailyMoodKey(NOTE_ID), savedMood ? savedRow(savedMood) : null);
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  const hook = renderHook(({ saved }: { saved: MoodValue | null }) => useDailyActionView(NOTE_ID, content, saved), { wrapper, initialProps: { saved: savedMood } });
  /** A newer saved mood arrives: this check-in confirmed, or a change fetched from another tab. */
  const saveMood = (mood: MoodValue) => {
    client.setQueryData(dailyMoodKey(NOTE_ID), savedRow(mood));
    hook.rerender({ saved: mood });
  };
  return { client, saveMood, ...hook };
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

  it("drops an older pick once a newer saved mood arrives: Đuối here, then Chill from another tab", async () => {
    const { client, result, saveMood } = setup(null);
    act(() => noteDailyMood(client, NOTE_ID, "Đuối"));
    await waitFor(() => expect(result.current.lighterShown).toBe(true));
    // The check-in succeeds: the saved mood is now Đuối and the lighter action stays.
    act(() => saveMood("Đuối"));
    expect(result.current).toMatchObject({ lighterShown: true, canSwitch: true });
    // Another tab changes today's mood; this tab fetches it.
    act(() => saveMood("Chill"));
    expect(result.current).toMatchObject({ lighterShown: false, canSwitch: false });
  });

  it("drops an older pick once a newer saved mood arrives: Chill here, then Đuối from another tab", async () => {
    const { client, result, saveMood } = setup(null);
    act(() => noteDailyMood(client, NOTE_ID, "Chill"));
    act(() => saveMood("Chill"));
    expect(result.current).toMatchObject({ lighterShown: false, canSwitch: false });
    act(() => saveMood("Đuối"));
    await waitFor(() => expect(result.current).toMatchObject({ lighterShown: true, canSwitch: true }));
  });

  it("keeps an unconfirmed pick while the saved mood has not changed (offline check-in)", async () => {
    const { client, result } = setup("Chill");
    act(() => noteDailyMood(client, NOTE_ID, "Đuối"));
    await waitFor(() => expect(result.current.lighterShown).toBe(true));
    // A refetch that returns the same saved mood does not undo the pick still waiting to sync.
    act(() => { client.setQueryData(dailyMoodKey(NOTE_ID), savedRow("Chill")); });
    expect(result.current.lighterShown).toBe(true);
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
