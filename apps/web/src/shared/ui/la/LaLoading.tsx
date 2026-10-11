import { useEffect, useState, type ReactNode } from "react";

import { useVibe } from "../../vibe/useVibe";
import { laLoadingLines } from "./laVoice";
import { LaSpirit } from "./LaSpirit";
import "./la.css";

/**
 * Branded waiting state. A short delay avoids flashing Lá for fast checks;
 * the status text is always present for assistive technology.
 */
export function LaLoading({ text, lines: customLines, delayMs = 180, children, className = "" }: {
  text?: string;
  lines?: readonly string[];
  delayMs?: number;
  children?: ReactNode;
  className?: string;
}) {
  const { vibe } = useVibe();
  const lines = customLines ?? laLoadingLines(vibe);
  const [visible, setVisible] = useState(delayMs <= 0);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (delayMs <= 0) { setVisible(true); return; }
    const timer = window.setTimeout(() => setVisible(true), delayMs);
    return () => window.clearTimeout(timer);
  }, [delayMs]);

  useEffect(() => {
    if (text || lines.length < 2 || !visible) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const timer = window.setInterval(() => setIndex((value) => (value + 1) % lines.length), 1800);
    return () => window.clearInterval(timer);
  }, [lines.length, text, visible]);

  const line = text ?? lines[index] ?? "";
  return (
    <section className={`la-loading ${visible ? "is-visible" : ""} ${className}`.trim()} role="status" aria-live="polite">
      <LaSpirit mood="think" size={56} />
      <p className="la-loading__line">{line}</p>
      <div className="la-loading__shimmer" aria-hidden="true"><span /><span /><span /></div>
      {children}
    </section>
  );
}
