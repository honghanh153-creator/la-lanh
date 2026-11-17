import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";

import type { MoodValue, ReadingContent } from "../api/client";

/**
 * Which of the day's two actions the reader sees (#627).
 *
 * The note and its own action never change (US-04 AC14). When the reader checks in as "Đuối" and
 * the reading carries a lighter action, this device shows the lighter one first and the reader can
 * switch back. The choice lives in memory only (the query cache): it is never written to storage,
 * never sent anywhere, and goes with the other chart-derived data.
 */
export const LIGHTER_MOOD: MoodValue = "Đuối";

export const dailyActionViewKey = (noteId: string | undefined) => ["daily-action-view", noteId] as const;

type DailyActionView = {
  /** The mood picked in this tab, known before (or without) the server answering. */
  mood?: MoodValue;
  /** Set only when the reader pressed the switch. */
  choice?: "original" | "lighter";
};

const EMPTY: DailyActionView = {};

/** Home calls this the moment a mood is picked; a new mood drops the earlier manual choice. */
export function noteDailyMood(client: QueryClient, noteId: string, mood: MoodValue): void {
  client.setQueryData<DailyActionView>(dailyActionViewKey(noteId), { mood });
}

export type DailyActionChoice = {
  /** True when the lighter action is the one on screen. */
  lighterShown: boolean;
  /** True when the reader can switch between the two actions. */
  canSwitch: boolean;
  switchAction: () => void;
};

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
  const canSwitch = Boolean(noteId && reading?.lighter_action) && (view.mood ?? savedMood) === LIGHTER_MOOD;
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
