import { useQuery } from "@tanstack/react-query";
import { useContext, useState } from "react";

import { listSavedNotes } from "../../shared/api/client";
import { ThemeContext } from "../../shared/theme/themeContext";

const NIGHT_DISMISS_KEY = "la-lanh-night-nudge-dismissed-v1";

function localDate(at: Date): string {
  return `${at.getFullYear()}-${String(at.getMonth() + 1).padStart(2, "0")}-${String(at.getDate()).padStart(2, "0")}`;
}

export type NightNudgeState = { enable: () => void; dismiss: () => void };

/** After 21:00 on a light theme, Lá offers the dark "night" look once a night. */
export function useNightNudge(now: Date = new Date()): NightNudgeState | null {
  const theme = useContext(ThemeContext);
  const hour = now.getHours();
  const night = hour >= 21 || hour < 5;
  const key = localDate(hour < 5 ? new Date(now.getTime() - 6 * 3_600_000) : now);
  const [dismissed, setDismissed] = useState(() => {
    try { return localStorage.getItem(NIGHT_DISMISS_KEY) === key; } catch { return false; }
  });
  if (!theme || theme.theme === "dark" || !night || dismissed) return null;
  const dismiss = () => {
    setDismissed(true);
    // Stores only tonight's date so the offer does not repeat.
    try { localStorage.setItem(NIGHT_DISMISS_KEY, key); } catch { /* Storage may be unavailable. */ }
  };
  return { enable: () => { theme.setTheme("dark"); dismiss(); }, dismiss };
}

/**
 * Sunday: a short look back at notes the user chose to save this week. Built
 * only from the user's own saved notes; nothing is compared with anyone else.
 * Returns the count, or null when there is nothing to recap.
 */
export function useWeekRecap(now: Date = new Date()): number | null {
  const sunday = now.getDay() === 0;
  const saved = useQuery({
    queryKey: ["saved-notes"],
    queryFn: ({ signal }) => listSavedNotes(signal),
    enabled: sunday,
    retry: false,
  });
  if (!sunday || !saved.data) return null;
  const weekAgo = now.getTime() - 7 * 86_400_000;
  const thisWeek = saved.data.filter((item) => Date.parse(item.saved_at) >= weekAgo);
  // Nothing saved this week: stay quiet instead of adding an empty block.
  return thisWeek.length ? thisWeek.length : null;
}
