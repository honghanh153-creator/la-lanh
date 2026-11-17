import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";

import { getCurrentMood, type MoodCheckIn, type MoodValue, type ReadingContent } from "../api/client";

/**
 * Which of the day's two actions the reader sees (#627).
 *
 * The note and its own action never change (US-04 AC14). When the saved mood of the day is "Đuối"
 * and the reading carries a lighter action, this device shows the lighter one first and the reader
 * can switch back.
 *
 * The lighter action follows the saved mood only: the newest row the server has given this device
 * (see `newerMoodRow`). A mood that is still being saved, or that failed to save, never changes
 * the action. The only other thing kept here is the reader's press on the switch, in memory (the
 * query cache): never in storage, never sent anywhere.
 */
export const LIGHTER_MOOD: MoodValue = "Đuối";

/** Removed with the mood on every erase path (history clear, chart-derived wipe). */
export const DAILY_ACTION_VIEW_KEY = "daily-action-view";

export const dailyActionViewKey = (noteId: string | undefined) => [DAILY_ACTION_VIEW_KEY, noteId] as const;

/** The saved mood of a note, as the server last confirmed it. Home and the note page share it. */
export const dailyMoodKey = (noteId: string | undefined) => ["daily-note-mood", noteId] as const;

/**
 * The one ordering rule for every answer about a note's mood: the first read, a refetch, and the
 * answer to a save. An answer is applied only if it is not older than the row already applied for
 * that note. "Older" is decided by the server's own `checked_in_at`, never by the order answers
 * happen to arrive in or by this device's clock. The server makes that time follow the order in
 * which saves are written to a row: each written save is at least a millisecond newer than the one
 * before it (`apps/api/app/domains/mood/postgres.py`), whatever order the requests arrived in.
 *
 * The marker is the applied row itself, in the shared mood query: it outlives any screen, so an
 * answer that arrives after its screen was closed is held to the same rule, and it is erased with
 * the mood on every erase path.
 *
 * "No mood" (null) carries no time and is always applied: the server saying there is nothing must
 * win, or an erased mood could stay on screen. A read that could carry a stale null (started
 * before a save) is cancelled when a mood is picked and again before a save's answer is applied.
 */
export function newerMoodRow(applied: MoodCheckIn | null | undefined, incoming: MoodCheckIn | null): MoodCheckIn | null {
  if (!incoming || !applied || applied.daily_note_id !== incoming.daily_note_id) return incoming;
  return Date.parse(applied.checked_in_at) > Date.parse(incoming.checked_in_at) ? applied : incoming;
}

/** Reads the saved mood from the server; the result goes through the ordering rule. */
export async function readDailyMood(client: QueryClient, noteId: string, signal?: AbortSignal): Promise<MoodCheckIn | null> {
  const incoming = await getCurrentMood(noteId, signal);
  return newerMoodRow(client.getQueryData<MoodCheckIn | null>(dailyMoodKey(noteId)), incoming);
}

/**
 * Applies the answer to a save; it goes through the same ordering rule as a read. Returns whether
 * the answer was accepted: false means a newer row was already applied and nothing changed.
 */
export function applySavedMood(client: QueryClient, row: MoodCheckIn): boolean {
  const key = dailyMoodKey(row.daily_note_id);
  const accepted = newerMoodRow(client.getQueryData<MoodCheckIn | null>(key), row) === row;
  if (accepted) client.setQueryData<MoodCheckIn | null>(key, row);
  return accepted;
}

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
