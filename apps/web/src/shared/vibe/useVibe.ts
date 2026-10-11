import { useContext, useState } from "react";

import { readCompanionStyle, readVibe } from "./vibe";
import { VibeContext, type VibeContextValue } from "./vibeContext";

/** Works without a provider (tests, isolated pages) by reading the stored choice. */
export function useVibe(): VibeContextValue {
  const shared = useContext(VibeContext);
  const [fallback] = useState(() => ({
    vibe: readVibe(),
    companion: readCompanionStyle(),
    setVibe: () => undefined,
    setCompanion: () => undefined,
  }));
  return shared ?? fallback;
}
