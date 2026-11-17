import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import type { MoodCheckIn, MoodValue, ReadingContent } from "../api/client";

/**
 * Which of the day's two actions the reader sees (#627).
 *
 * The note and its own action never change (US-04 AC14). When the reader checks in as "Đuối" and
 * the reading carries a lighter action, this device shows the lighter one first and the reader can
 * switch back. The choice lives in memory only (the query cache): it is never written to storage,
 * never sent anywhere, and goes with the other chart-derived data.
 */
export const LIGHTER_MOOD: MoodValue = "Đuối";

/** Every path that erases the mood must also remove this key (history clear, chart-derived wipe). */
export const DAILY_ACTION_VIEW_KEY = "daily-action-view";

export const dailyActionViewKey = (noteId: string | undefined) => [DAILY_ACTION_VIEW_KEY, noteId] as const;

/** The saved mood of a note, as the server last confirmed it. Home and the note page share it. */
export const dailyMoodKey = (noteId: string | undefined) => ["daily-note-mood", noteId] as const;

type DailyActionView = {
  /**
   * A mood picked in this tab that the server has not confirmed yet. `over` is the saved mood it
   * was picked over. The intent is removed for good when its check-in succeeds
   * (`retireDailyMoodIntent`) or when any other saved mood arrives (a change made in another
   * tab); a saved mood that later returns to `over` never brings it back.
   */
  pending?: { mood: MoodValue; over: MoodValue | null };
  /** Set only when the reader pressed the switch. */
  choice?: "original" | "lighter";
};

const EMPTY: DailyActionView = {};

/** Home calls this the moment a mood is picked; a new mood drops the earlier manual choice. */
export function noteDailyMood(client: QueryClient, noteId: string, mood: MoodValue): void {
  const over = client.getQueryData<MoodCheckIn | null>(dailyMoodKey(noteId))?.mood ?? null;
  client.setQueryData<DailyActionView>(dailyActionViewKey(noteId), { pending: { mood, over } });
}

/** Removes the unconfirmed pick and keeps the reader's manual choice. Home calls it when the check-in succeeds. */
export function retireDailyMoodIntent(client: QueryClient, noteId: string): void {
  const view = client.getQueryData<DailyActionView>(dailyActionViewKey(noteId));
  if (!view?.pending) return;
  client.setQueryData<DailyActionView>(dailyActionViewKey(noteId), view.choice ? { choice: view.choice } : EMPTY);
}

/** The mood the screen should act on: a still-unconfirmed pick, otherwise the saved mood. */
export function effectiveDailyMood(
  pending: DailyActionView["pending"],
  savedMood: MoodValue | null | undefined,
): MoodValue | null {
  const saved = savedMood ?? null;
  return pending && pending.over === saved ? pending.mood : saved;
}

export type DailyActionChoice = {
  /** True when the lighter action is the one on screen. */
  lighterShown: boolean;
  /** True when the reader can switch between the two actions. */
  canSwitch: boolean;
  switchAction: () => void;
};

/** `savedMood` must be the value of the `dailyMoodKey(noteId)` query, the same one `noteDailyMood` reads. */
export function useDailyActionView(
  noteId: string | undefined,
  reading: ReadingContent | null | undefined,
  savedMood: MoodValue | null | undefined,
): DailyActionChoice {
  const client = useQueryClient();
  const key = dailyActionViewKey(noteId);
  const { data } = useQuery({
    queryKey: key,
    // Nothing to fetch: after a data wipe the view simply starts empty again.
    queryFn: () => EMPTY,
    initialData: EMPTY,
    staleTime: Infinity,
    enabled: Boolean(noteId),
  });
  const view = data ?? EMPTY;
  // A saved mood other than the one the pick was made over is newer than the pick: the pick is
  // already ignored in this render (effectiveDailyMood) and is removed here so it cannot return.
  const outdated = Boolean(noteId && view.pending && view.pending.over !== (savedMood ?? null));
  useEffect(() => {
    if (outdated && noteId) retireDailyMoodIntent(client, noteId);
  }, [client, noteId, outdated]);
  const canSwitch = Boolean(noteId && reading?.lighter_action)
    && effectiveDailyMood(view.pending, savedMood) === LIGHTER_MOOD;
  const lighterShown = canSwitch && view.choice !== "original";
  return {
    lighterShown,
    canSwitch,
    switchAction: () => {
      if (!canSwitch) return;
      client.setQueryData<DailyActionView>(key, { ...view, choice: lighterShown ? "original" : "lighter" });
    },
  };
}
