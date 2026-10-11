import { useEffect, useMemo, useState, type ReactNode } from "react";

import {
  applyVibe, persistCompanionStyle, persistVibe, readCompanionStyle, readVibe,
  type AppVibe, type CompanionStyle,
} from "./vibe";
import { VibeContext, type VibeContextValue } from "./vibeContext";

export function VibeProvider({ children }: { children: ReactNode }) {
  const [vibe, setVibeState] = useState<AppVibe>(readVibe);
  const [companion, setCompanionState] = useState<CompanionStyle | null>(readCompanionStyle);

  useEffect(() => applyVibe(vibe), [vibe]);

  const value = useMemo<VibeContextValue>(() => ({
    vibe,
    setVibe: (next) => { persistVibe(next); setVibeState(next); },
    companion,
    setCompanion: (next) => { persistCompanionStyle(next); setCompanionState(next); },
  }), [vibe, companion]);

  return <VibeContext.Provider value={value}>{children}</VibeContext.Provider>;
}
