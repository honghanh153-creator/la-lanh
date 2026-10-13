import { laGreeting } from "../../shared/ui/la/laVoice";
import type { AppVibe } from "../../shared/vibe/vibe";

export type HomeCompanionState = "idle" | "loading" | "error";

/** Home loading copy, unchanged from the earlier Home waiting state. */
export const HOME_LOADING_LINE = "Lá đang mở note hôm nay…";
/** Shown beside a note that has not arrived (HomeError artboard). */
export const HOME_ERROR_LINE = "Trong lúc chờ, bạn vẫn rút Tarot được.";

/**
 * The one short line Lá says in the Home bubble when no ritual notice needs
 * the slot. Idle reuses Lá's existing direct/roast day-part greeting from
 * laVoice; copy there is owned separately and not changed here.
 */
export function homeCompanionLine({
  state = "idle",
  vibe = "direct",
  now = new Date(),
}: {
  state?: HomeCompanionState;
  vibe?: AppVibe;
  now?: Date;
} = {}): { text: string } {
  if (state === "loading") return { text: HOME_LOADING_LINE };
  if (state === "error") return { text: HOME_ERROR_LINE };
  return { text: laGreeting(now, vibe).line };
}
