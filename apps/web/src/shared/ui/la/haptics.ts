/**
 * A tiny tap of vibration where the device supports it (Android browsers).
 * Skipped when the user prefers reduced motion. Never required for feedback:
 * every action also changes visibly on screen.
 */
export function tapFeedback(durationMs = 12): void {
  try {
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    navigator.vibrate?.(durationMs);
  } catch {
    /* Vibration is optional. */
  }
}
