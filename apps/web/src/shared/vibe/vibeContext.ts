import { createContext } from "react";

import type { AppVibe, CompanionStyle } from "./vibe";

export type VibeContextValue = {
  vibe: AppVibe;
  setVibe: (vibe: AppVibe) => void;
  companion: CompanionStyle | null;
  setCompanion: (style: CompanionStyle) => void;
};

export const VibeContext = createContext<VibeContextValue | null>(null);
