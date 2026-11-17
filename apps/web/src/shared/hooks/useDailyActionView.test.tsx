import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { getCurrentMood, type MoodCheckIn, type MoodValue, type ReadingContent } from "../api/client";
import { clearChartDerivedData } from "../storage/clearChartDerivedData";
import { applySavedMood, dailyActionViewKey, dailyMoodKey, newerMoodRow, readDailyMood, resetDailyActionChoice, useDailyActionView } from "./useDailyActionView";

vi.mock("../api/client", async (original) => ({
  ...(await original<typeof import("../api/client")>()),
  getCurrentMood: vi.fn(),
}));

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

describe("the ordering rule for mood answers (#627)", () => {
  const at = (mood: MoodValue, time: string, noteId = NOTE_ID): MoodCheckIn => ({ id: `row-${time}`, daily_note_id: noteId, mood, checked_in_at: time });
  const older = at("Đuối", "2026-09-07T10:00:00Z");
  const newer = at("Chill", "2026-09-07T10:00:05Z");

  it("applies an answer only if it is not older than the row already applied", () => {
    expect(newerMoodRow(undefined, older)).toBe(older);
    expect(newerMoodRow(null, older)).toBe(older);
    expect(newerMoodRow(older, newer)).toBe(newer);
    expect(newerMoodRow(newer, older)).toBe(newer);
    // The same time is not older: the incoming row is taken (the same save read back).
    const sameTime = { ...older, id: "row-again" };
    expect(newerMoodRow(older, sameTime)).toBe(sameTime);
    // Times are compared as instants, not as text.
    expect(newerMoodRow(at("Đuối", "2026-09-07T17:00:05+07:00"), at("Chill", "2026-09-07T10:00:04Z"))?.mood).toBe("Đuối");
  });

  it("always applies 'no mood', and never compares rows of different notes", () => {
    expect(newerMoodRow(newer, null)).toBeNull();
    const otherNote = at("Đuối", "2026-09-06T10:00:00Z", "00000000-0000-4000-8000-000000000002");
    expect(newerMoodRow(newer, otherNote)).toBe(otherNote);
  });

  it("holds the answer to a save to the rule, whichever order answers arrive in", () => {
    const client = new QueryClient();
    // It says whether the answer was accepted, so the caller can leave everything else alone
    // when an older answer is rejected.
    expect(applySavedMood(client, newer)).toBe(true);
    expect(applySavedMood(client, older)).toBe(false);
    expect(client.getQueryData(dailyMoodKey(NOTE_ID))).toEqual(newer);
    const client2 = new QueryClient();
    expect(applySavedMood(client2, older)).toBe(true);
    expect(applySavedMood(client2, newer)).toBe(true);
    expect(client2.getQueryData(dailyMoodKey(NOTE_ID))).toEqual(newer);
  });

  it("holds a read to the same rule: an older row read from the server does not replace a newer applied one", async () => {
    const client = new QueryClient();
    applySavedMood(client, newer);
    vi.mocked(getCurrentMood).mockResolvedValueOnce(older);
    expect(await readDailyMood(client, NOTE_ID)).toEqual(newer);
    const newest = at("Đuối", "2026-09-07T10:00:09Z");
    vi.mocked(getCurrentMood).mockResolvedValueOnce(newest);
    expect(await readDailyMood(client, NOTE_ID)).toBe(newest);
    vi.mocked(getCurrentMood).mockResolvedValueOnce(null);
    expect(await readDailyMood(client, NOTE_ID)).toBeNull();
  });
});

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
