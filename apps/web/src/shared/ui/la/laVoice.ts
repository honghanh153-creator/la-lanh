import type { MoodValue } from "../../api/client";
import type { AppVibe } from "../../vibe/vibe";
import {
  LA_GREETINGS,
  LA_LOADING,
  LA_MOOD_NUDGE as CATALOG_MOOD_NUDGE,
  LA_MOOD_REACTIONS as CATALOG_MOOD_REACTIONS,
  LA_NOTE_FALLBACK,
} from "./laCatalog.generated";
import { moonPhase, type MoonPhase } from "./moonPhase";

// Lá's framing microcopy. It greets, waits and reacts; it never changes the
// meaning of a reading, predicts events, or speaks for another person.
// Voices: "direct" (plain, warm Vietnamese) and "roast" (owner-approved
// 2026-10-11: teasing the situation, never the person, always with a way out).
// The words live in the API content matrix (apps/api/app/domains/readings/companion.py)
// and reach this file through laCatalog.generated.ts; change them there.

export type DayPart = "morning" | "noon" | "afternoon" | "evening" | "late";

export function dayPart(at: Date = new Date()): DayPart {
  const hour = at.getHours();
  if (hour >= 5 && hour < 11) return "morning";
  if (hour >= 11 && hour < 14) return "noon";
  if (hour >= 14 && hour < 18) return "afternoon";
  if (hour >= 18 && hour < 22) return "evening";
  return "late";
}

export type LaGreeting = { line: string; moon: MoonPhase; part: DayPart };

export function laGreeting(at: Date = new Date(), vibe: AppVibe = "direct"): LaGreeting {
  const part = dayPart(at);
  return { line: LA_GREETINGS[vibe][part], moon: moonPhase(at), part };
}

export const LA_LOADING_LINES: readonly string[] = LA_LOADING.direct;
export const LA_ROAST_LOADING_LINES: readonly string[] = LA_LOADING.roast;

export function laLoadingLines(vibe: AppVibe): readonly string[] {
  return vibe === "roast" ? LA_ROAST_LOADING_LINES : LA_LOADING_LINES;
}

export const LA_MOOD_REACTIONS: Record<MoodValue, string> = CATALOG_MOOD_REACTIONS.direct;
export const LA_ROAST_MOOD_REACTIONS: Record<MoodValue, string> = CATALOG_MOOD_REACTIONS.roast;

export function laMoodReaction(mood: MoodValue, vibe: AppVibe): string {
  return (vibe === "roast" ? LA_ROAST_MOOD_REACTIONS : LA_MOOD_REACTIONS)[mood];
}

export const LA_MOOD_NUDGE: string = CATALOG_MOOD_NUDGE;

/**
 * What Lá says next to today's card. The API already voices and (for Luna cards) writes
 * `sections.companion`; the catalog fallback only covers legacy notes without it.
 */
export function laNoteLine(companion: string | null | undefined, vibe: AppVibe): string {
  return companion?.trim() ? companion : LA_NOTE_FALLBACK[vibe];
}
