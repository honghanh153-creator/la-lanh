import { useSyncExternalStore } from "react";

import { useOnboardingMotion } from "../../shared/ui/onboardingMotion";

const QUERY = "(prefers-reduced-motion: reduce)";

function media(): MediaQueryList | undefined {
  return typeof window === "undefined" ? undefined : window.matchMedia?.(QUERY);
}

function subscribe(onChange: () => void): () => void {
  const list = media();
  list?.addEventListener?.("change", onChange);
  return () => list?.removeEventListener?.("change", onChange);
}

function prefersReducedMotion(): boolean {
  return Boolean(media()?.matches);
}

/**
 * True when Tarot animations may play: the system does not ask for reduced motion
 * and the shared in-app motion pause is off.
 */
export function useTarotMotion(): boolean {
  const { paused } = useOnboardingMotion();
  const reduced = useSyncExternalStore(subscribe, prefersReducedMotion, () => true);
  return !paused && !reduced;
}
