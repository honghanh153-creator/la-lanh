import type { AppVibe } from "../../vibe/vibe";
import type { FestivalKey } from "./growth";

export type CompanionReaction = "happy" | "think" | null;

export type CompanionProps = {
  /** Time to draw. Defaults to the device clock (refreshed on return to the page). */
  now?: Date;
  /** Distinct visit days from `readGrowth()`; drives the permanent growth level. */
  growthDays?: number;
  /** Random seed from `readGrowth()`. Never derive it from personal data. */
  seed?: number;
  vibe?: AppVibe;
  /** Rendered width in CSS px. */
  size?: number;
  reacting?: CompanionReaction;
  onTap?: () => void;
  /** Accessible name of the tap button. */
  label?: string;
  /** Force the still pose (QA preview of reduced motion). */
  still?: boolean;
  /** "auto" (default) follows the calendar; null hides festival skins; a key previews one. */
  festival?: FestivalKey | null | "auto";
  /** Show the calm welcome-back gift (a new leaf) after `recordVisit` reported a gap. */
  welcomeBack?: boolean;
  className?: string;
};
