import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { getCurrentMood, type MoodCheckIn, type MoodValue, type ReadingContent } from "../api/client";
import { clearChartDerivedData } from "../storage/clearChartDerivedData";
import { applySavedMood, dailyActionViewKey, dailyMoodKey, dailyReadOnlyKey, newerMoodRow, readDailyMood, resetDailyActionChoice, useDailyActionView, useReadOnlyToday } from "./useDailyActionView";

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

describe("mood alternatives for Căng and Lạc trôi (#701)", () => {
  const all = {
    lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light", experiment: null },
    slow_action: { action: "Đợi năm phút rồi mới gửi câu trả lời.", weight: "slow", experiment: null },
    clear_action: { action: "Viết ra một việc duy nhất cần xong trước trưa.", weight: "clear", experiment: null },
  } as unknown as ReadingContent;

  it("shows the slow action for Căng and the clear one for Lạc trôi, each with its own switch label", () => {
    const tense = setup("Căng", all).result.current;
    expect(tense).toMatchObject({ lighterShown: true, canSwitch: true, alternativeLabel: "Xem việc chậm lại" });
    expect(tense.alternative?.action).toBe("Đợi năm phút rồi mới gửi câu trả lời.");
    const floating = setup("Lạc trôi", all).result.current;
    expect(floating).toMatchObject({ lighterShown: true, alternativeLabel: "Xem một bước rõ" });
    expect(floating.alternative?.action).toBe("Viết ra một việc duy nhất cần xong trước trưa.");
    const drained = setup("Đuối", all).result.current;
    expect(drained.alternative?.action).toBe("Uống một ly nước rồi ngồi yên hai phút.");
    expect(drained.alternativeLabel).toBe("Xem việc nhẹ hơn");
  });

  it("keeps the card's action for Rực, Chill, an unsaved mood, or a reading without that offer", () => {
    for (const mood of ["Rực", "Chill", null] as const) {
      expect(setup(mood, all).result.current).toMatchObject({ lighterShown: false, canSwitch: false, alternative: null });
    }
    const onlyLighter = { lighter_action: all.lighter_action } as unknown as ReadingContent;
    expect(setup("Căng", onlyLighter).result.current).toMatchObject({ lighterShown: false, canSwitch: false, alternative: null });
  });

  it("lets the reader switch back to the card's action and forward again", async () => {
    const { result } = setup("Căng", all);
    // The query cache notifies on the next tick, so each step waits for the hook to settle.
    act(() => result.current.switchAction());
    await waitFor(() => expect(result.current).toMatchObject({ lighterShown: false, canSwitch: true }));
    act(() => result.current.switchAction());
    await waitFor(() => expect(result.current.lighterShown).toBe(true));
  });
});

describe("the alone action (#703)", () => {
  const alone = (replaces: string[]) => ({
    lighter_action: { action: "Uống một ly nước rồi ngồi yên hai phút.", weight: "light", experiment: null },
    alone_action: { action: "Ghi ra giấy một câu bạn muốn nói, giữ cho riêng mình.", replaces, experiment: null },
  }) as unknown as ReadingContent;

  it("is offered only next to an action the server says it can replace", () => {
    // No mood: the card's own action is on screen.
    expect(setup(null, alone(["card"])).result.current.aloneAction?.action).toContain("Ghi ra giấy");
    expect(setup(null, alone(["light"])).result.current.aloneAction).toBeNull();
    // Đuối: the lighter action is on screen.
    expect(setup("Đuối", alone(["light"])).result.current.aloneAction).not.toBeNull();
    expect(setup("Đuối", alone(["card"])).result.current.aloneAction).toBeNull();
    expect(setup(null, reading).result.current).toMatchObject({ aloneAction: null, aloneShown: false });
  });

  it("switches to the alone action and back, in memory only", async () => {
    const { client, result } = setup(null, alone(["card"]));
    expect(result.current.aloneShown).toBe(false);
    act(() => result.current.switchAlone());
    await waitFor(() => expect(result.current.aloneShown).toBe(true));
    expect(client.getQueryData(dailyActionViewKey(NOTE_ID))).toEqual({ alone: true });
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain("Ghi ra giấy");
    act(() => result.current.switchAlone());
    await waitFor(() => expect(result.current.aloneShown).toBe(false));
  });

  it("does nothing when there is no alone action to show", async () => {
    const { client, result } = setup(null, alone(["light"]));
    act(() => result.current.switchAlone());
    await act(async () => { await Promise.resolve(); });
    expect(result.current.aloneShown).toBe(false);
    expect(client.getQueryData(dailyActionViewKey(NOTE_ID))).toEqual({});
  });

  it("stops showing it when the action on screen changes to one it cannot replace", async () => {
    const { result } = setup("Đuối", alone(["light"]));
    act(() => result.current.switchAlone());
    await waitFor(() => expect(result.current.aloneShown).toBe(true));
    // Back to the card's own action: the alone action is not for that one.
    act(() => result.current.switchAction());
    await waitFor(() => expect(result.current).toMatchObject({ lighterShown: false, aloneAction: null, aloneShown: false }));
    // And forward again: the mood switch started over without the alone action.
    act(() => result.current.switchAction());
    await waitFor(() => expect(result.current).toMatchObject({ lighterShown: true, aloneShown: false }));
  });

  it("starts a newly confirmed mood without it, and drops it with chart-derived data", async () => {
    const { client, result } = setup(null, alone(["card"]));
    act(() => result.current.switchAlone());
    await waitFor(() => expect(result.current.aloneShown).toBe(true));
    act(() => resetDailyActionChoice(client, NOTE_ID));
    await waitFor(() => expect(result.current.aloneShown).toBe(false));
    act(() => result.current.switchAlone());
    await waitFor(() => expect(result.current.aloneShown).toBe(true));
    await act(async () => { await clearChartDerivedData(client); });
    await waitFor(() => expect(result.current.aloneShown).toBe(false));
  });
});

describe("useReadOnlyToday (#700)", () => {
  const NEXT_NOTE_ID = "00000000-0000-4000-8000-000000000002";

  function setupReadOnly(noteId: string | null = NOTE_ID) {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
    const hook = renderHook(({ id }: { id: string | undefined }) => useReadOnlyToday(id), { wrapper, initialProps: { id: noteId ?? undefined } });
    return { client, ...hook };
  }

  it("starts open, folds on a press and opens on the next", async () => {
    const { result } = setupReadOnly();
    expect(result.current.readOnly).toBe(false);
    act(() => result.current.toggle());
    await waitFor(() => expect(result.current.readOnly).toBe(true));
    act(() => result.current.toggle());
    await waitFor(() => expect(result.current.readOnly).toBe(false));
  });

  it("is shared by every screen of the same note, and does nothing without a note", async () => {
    const { client, result } = setupReadOnly();
    const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
    const otherScreen = renderHook(() => useReadOnlyToday(NOTE_ID), { wrapper });
    act(() => result.current.toggle());
    await waitFor(() => expect(otherScreen.result.current.readOnly).toBe(true));

    const noNote = setupReadOnly(null);
    act(() => noNote.result.current.toggle());
    await act(async () => { await Promise.resolve(); });
    expect(noNote.result.current.readOnly).toBe(false);
    expect(noNote.client.getQueryCache().getAll().every((query) => query.state.data !== true)).toBe(true);
  });

  it("belongs to one note: the next day's note starts open again (US-04 AC12)", async () => {
    const { result, rerender } = setupReadOnly();
    act(() => result.current.toggle());
    await waitFor(() => expect(result.current.readOnly).toBe(true));
    rerender({ id: NEXT_NOTE_ID });
    expect(result.current.readOnly).toBe(false);
    // Yesterday's fold is not moved or copied to the new note.
    rerender({ id: NOTE_ID });
    expect(result.current.readOnly).toBe(true);
  });

  it("lives in memory only: no storage, no request, and it goes when chart-derived data is cleared", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const stored = () => JSON.stringify({ ...localStorage, ...sessionStorage });
    const before = stored();
    const { client, result } = setupReadOnly();
    act(() => result.current.toggle());
    await waitFor(() => expect(result.current.readOnly).toBe(true));

    expect(client.getQueryData(dailyReadOnlyKey(NOTE_ID))).toBe(true);
    expect(stored()).toBe(before);
    expect(fetchSpy).not.toHaveBeenCalled();
    // It does not touch the lighter-action choice kept next to it.
    expect(client.getQueryData(dailyActionViewKey(NOTE_ID))).toBeUndefined();
    // A blanket refetch (Home does one when the day's note changes) does not open the box.
    await act(async () => { await client.invalidateQueries(); });
    expect(result.current.readOnly).toBe(true);

    await act(async () => { await clearChartDerivedData(client); });
    await waitFor(() => expect(result.current.readOnly).toBe(false));
    fetchSpy.mockRestore();
  });
});

describe("memory-only choices outlive a visit to another screen (#833 review)", () => {
  // React Query drops an unused query after five minutes by default. These two choices have
  // nothing to refetch, so they must stay for the app session: fold or switch, leave Home and the
  // note page for a while, come back the same day, and the choice is still there.
  const SIX_MINUTES = 6 * 60 * 1000;

  it("keeps the folded box after unmount, six minutes away and a remount", () => {
    vi.useFakeTimers();
    try {
      const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
      const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
      const first = renderHook(() => useReadOnlyToday(NOTE_ID), { wrapper });
      act(() => first.result.current.toggle());
      act(() => { vi.advanceTimersByTime(1); }); // React Query hands updates over on a timer.
      expect(first.result.current.readOnly).toBe(true);
      first.unmount();
      act(() => { vi.advanceTimersByTime(SIX_MINUTES); });
      expect(client.getQueryData(dailyReadOnlyKey(NOTE_ID))).toBe(true);
      const again = renderHook(() => useReadOnlyToday(NOTE_ID), { wrapper });
      expect(again.result.current.readOnly).toBe(true);
    } finally {
      vi.useRealTimers();
    }
  });

  it("keeps the switch press after unmount, six minutes away and a remount", () => {
    vi.useFakeTimers();
    try {
      const { client, result, unmount } = setup("Đuối");
      expect(result.current.lighterShown).toBe(true);
      act(() => result.current.switchAction());
      act(() => { vi.advanceTimersByTime(1); });
      expect(result.current.lighterShown).toBe(false);
      unmount();
      act(() => { vi.advanceTimersByTime(SIX_MINUTES); });
      expect(client.getQueryData(dailyActionViewKey(NOTE_ID))).toEqual({ choice: "original" });
      const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
      const again = renderHook(() => useDailyActionView(NOTE_ID, reading, "Đuối"), { wrapper });
      expect(again.result.current.lighterShown).toBe(false);
    } finally {
      vi.useRealTimers();
    }
  });
});
