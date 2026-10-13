import { laGreeting, laNoteLine } from "../../shared/ui/la/laVoice";
import type { AppVibe } from "../../shared/vibe/vibe";

export type HomeCompanionState = "idle" | "loading" | "error";

/** Home loading copy, unchanged from the earlier Home waiting state. */
export const HOME_LOADING_LINE = "Lá đang mở note hôm nay…";
/** Shown beside a note that has not arrived (HomeError artboard). */
export const HOME_ERROR_LINE = "Trong lúc chờ, bạn vẫn rút Tarot được.";

/**
 * The one short line Lá says in the Home bubble when no ritual notice needs
 * the slot. With today's card it is the card's own line (`sections.companion`,
 * already voiced by the API and written by Luna for generated cards; content
 * matrix in readings/companion.py). Without a card (legacy note) Lá greets by
 * time of day.
 */
export function homeCompanionLine({
  state = "idle",
  vibe = "direct",
  now = new Date(),
  companion,
}: {
  state?: HomeCompanionState;
  vibe?: AppVibe;
  now?: Date;
  companion?: string | null;
} = {}): { text: string } {
  if (state === "loading") return { text: HOME_LOADING_LINE };
  if (state === "error") return { text: HOME_ERROR_LINE };
  if (companion?.trim()) return { text: laNoteLine(companion, vibe) };
  return { text: laGreeting(now, vibe).line };
}
