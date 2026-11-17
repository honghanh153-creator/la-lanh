import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";

import type { MoodValue, ReadingContent } from "../api/client";

/**
 * Which of the day's two actions the reader sees (#627).
 *
 * The note and its own action never change (US-04 AC14). When the saved mood of the day is "Đuối"
 * and the reading carries a lighter action, this device shows the lighter one first and the reader
 * can switch back.
 *
 * The lighter action follows the saved mood only: what the server returned, or a check-in the
 * server has confirmed. A mood that is still being saved, or that failed to save, never changes the
 * action, so there is no order of requests to keep track of. The only thing kept here is the
 * reader's press on the switch, in memory (the query cache): never in storage, never sent anywhere.
 */
export const LIGHTER_MOOD: MoodValue = "Đuối";

/** Removed with the mood on every erase path (history clear, chart-derived wipe). */
export const DAILY_ACTION_VIEW_KEY = "daily-action-view";

export const dailyActionViewKey = (noteId: string | undefined) => [DAILY_ACTION_VIEW_KEY, noteId] as const;

/** The saved mood of a note, as the server last confirmed it. Home and the note page share it. */
export const dailyMoodKey = (noteId: string | undefined) => ["daily-note-mood", noteId] as const;

type DailyActionView = {
  /** Set only when the reader pressed the switch. */
  choice?: "original" | "lighter";
};

const EMPTY: DailyActionView = {};

/** A newly confirmed mood starts from its default action again. */
export function resetDailyActionChoice(client: QueryClient, noteId: string): void {
  if (client.getQueryData<DailyActionView>(dailyActionViewKey(noteId))?.choice) {
    client.setQueryData<DailyActionView>(dailyActionViewKey(noteId), EMPTY);
  }
}

export type DailyActionChoice = {
  /** True when the lighter action is the one on screen. */
  lighterShown: boolean;
  /** True when the reader can switch between the two actions. */
  canSwitch: boolean;
  switchAction: () => void;
};

/** `confirmedMood` is the saved mood of this note; pass null while a check-in is unsaved. */
export function useDailyActionView(
  noteId: string | undefined,
  reading: ReadingContent | null | undefined,
  confirmedMood: MoodValue | null | undefined,
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
  const canSwitch = Boolean(noteId && reading?.lighter_action) && confirmedMood === LIGHTER_MOOD;
  const lighterShown = canSwitch && view.choice !== "original";
  return {
    lighterShown,
    canSwitch,
    switchAction: () => {
      if (!canSwitch) return;
      client.setQueryData<DailyActionView>(key, { choice: lighterShown ? "original" : "lighter" });
    },
  };
}
