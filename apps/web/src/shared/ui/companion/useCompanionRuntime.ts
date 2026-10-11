import { useCallback, useEffect, useRef, useState, type MouseEvent, type RefObject } from "react";

import { useOnboardingMotion } from "../onboardingMotion";

/**
 * running: loops play.
 * paused: loops freeze where they are (page hidden, off-screen, app motion
 *   toggle, or night settled after 10 s). No jump, resumes smoothly.
 * still: reduced motion or explicit still preview; the designed rest pose.
 */
export type CompanionMotion = "running" | "paused" | "still";

/** Night: everything settles into a still pose within this many ms (G6). */
export const NIGHT_SETTLE_MS = 10_000;
/** Re-read the clock this often while visible; colours crossfade, never jump. */
const CLOCK_REFRESH_MS = 5 * 60_000;

function reducedMotionQuery(): MediaQueryList | null {
  try {
    return window.matchMedia?.("(prefers-reduced-motion: reduce)") ?? null;
  } catch {
    return null;
  }
}

export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => reducedMotionQuery()?.matches ?? false);
  useEffect(() => {
    const query = reducedMotionQuery();
    if (!query) return undefined;
    const onChange = () => setReduced(query.matches);
    query.addEventListener?.("change", onChange);
    return () => query.removeEventListener?.("change", onChange);
  }, []);
  return reduced;
}

export function usePageVisible(): boolean {
  const [visible, setVisible] = useState(() => typeof document === "undefined" || !document.hidden);
  useEffect(() => {
    const onChange = () => setVisible(!document.hidden);
    document.addEventListener("visibilitychange", onChange);
    return () => document.removeEventListener("visibilitychange", onChange);
  }, []);
  return visible;
}

function useOnScreen(ref: RefObject<Element | null>): boolean {
  const [onScreen, setOnScreen] = useState(true);
  useEffect(() => {
    const node = ref.current;
    if (!node || typeof IntersectionObserver === "undefined") return undefined;
    const observer = new IntersectionObserver((entries) => {
      setOnScreen(entries.some((entry) => entry.isIntersecting));
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, [ref]);
  return onScreen;
}

/** The given time, or the device clock refreshed on return to the page and every few minutes. */
export function useCompanionClock(now: Date | undefined, visible: boolean): Date {
  const [clock, setClock] = useState(() => new Date());
  useEffect(() => {
    if (now || !visible) return undefined;
    setClock(new Date());
    const timer = window.setInterval(() => setClock(new Date()), CLOCK_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [now, visible]);
  return now ?? clock;
}

export function useCompanionMotion({ rootRef, still, resting, visible }: {
  rootRef: RefObject<HTMLElement | null>;
  still: boolean;
  resting: boolean;
  visible: boolean;
}): { motion: CompanionMotion; canAnimate: () => boolean } {
  const reduced = usePrefersReducedMotion();
  const appMotion = useOnboardingMotion();
  const onScreen = useOnScreen(rootRef);
  const [settled, setSettled] = useState(false);

  useEffect(() => {
    setSettled(false);
    if (!resting || still || reduced) return undefined;
    const timer = window.setTimeout(() => setSettled(true), NIGHT_SETTLE_MS);
    return () => window.clearTimeout(timer);
  }, [resting, still, reduced]);

  const motion: CompanionMotion = still || reduced
    ? "still"
    : !visible || !onScreen || appMotion.paused || (resting && settled)
      ? "paused"
      : "running";

  const motionRef = useRef(motion);
  useEffect(() => {
    motionRef.current = motion;
  }, [motion]);
  const canAnimate = useCallback(() => {
    if (motionRef.current !== "running") return false;
    const node = rootRef.current;
    return !node?.closest('[data-motion="paused"], [data-home-motion="paused"]');
  }, [rootRef]);

  return { motion, canAnimate };
}

/** Web Animations helper; a no-op where the API is missing (jsdom, old WebViews). */
export function playAnimation(node: Element | null, keyframes: Keyframe[], options: KeyframeAnimationOptions): void {
  if (!node || typeof (node as Element & { animate?: unknown }).animate !== "function") return;
  node.animate(keyframes, options);
}

/** Map a click to viewBox coordinates; keyboard activation (detail 0) uses the centre. */
export function tapPoint(event: MouseEvent<HTMLElement>, viewBox: { width: number; height: number }, fallback: { x: number; y: number }): { x: number; y: number } {
  if (event.detail === 0) return fallback;
  const rect = event.currentTarget.getBoundingClientRect();
  if (!rect.width || !rect.height) return fallback;
  return {
    x: ((event.clientX - rect.left) / rect.width) * viewBox.width,
    y: ((event.clientY - rect.top) / rect.height) * viewBox.height,
  };
}

export type Burst = { id: number; x: number; y: number };

/** Short-lived tap bursts, at most three on screen. */
export function useBursts(lifetimeMs = 950): { bursts: Burst[]; addBurst: (x: number, y: number) => void } {
  const [bursts, setBursts] = useState<Burst[]>([]);
  const nextId = useRef(1);
  const timers = useRef<number[]>([]);
  useEffect(() => () => timers.current.forEach((timer) => window.clearTimeout(timer)), []);
  const addBurst = useCallback((x: number, y: number) => {
    const id = nextId.current;
    nextId.current += 1;
    setBursts((current) => [...current.slice(-2), { id, x, y }]);
    timers.current.push(window.setTimeout(() => {
      setBursts((current) => current.filter((burst) => burst.id !== id));
    }, lifetimeMs));
  }, [lifetimeMs]);
  return { bursts, addBurst };
}
