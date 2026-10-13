import { useEffect, useState, type ReactNode } from "react";

import { useVibe } from "../../vibe/useVibe";
import { laLoadingLines } from "./laVoice";
import "./la.css";

const SLOW_AFTER_MS = 8000;
const LA_LOADING_SLOW_LINE = "Vẫn đang mở, bạn chờ thêm chút nhé.";

/**
 * Branded waiting state. A short delay avoids flashing Lá for fast checks;
 * the status text is always present for assistive technology.
 */
export function LaLoading({ text, lines: customLines, delayMs = 180, children, className = "", variant = "page" }: {
  text?: string;
  lines?: readonly string[];
  delayMs?: number;
  children?: ReactNode;
  className?: string;
  /** page: Lá + status line; reading: status line + reading-shaped skeleton; list: status line + card skeletons. */
  variant?: "page" | "reading" | "list";
}) {
  const { vibe } = useVibe();
  const lines = customLines ?? laLoadingLines(vibe);
  const [visible, setVisible] = useState(delayMs <= 0);
  const [index, setIndex] = useState(0);
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    // DS-States: after 8 seconds, add one reassuring line.
    const timer = window.setTimeout(() => setSlow(true), SLOW_AFTER_MS);
    return () => window.clearTimeout(timer);
  }, []);

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
    <section className={`la-loading la-loading--${variant} ${visible ? "is-visible" : ""} ${className}`.trim()} role="status" aria-live="polite">
      {variant === "page" ? <img alt="" className="la-loading__sprout" src="/assets/ultraviolet/sprout-3d.png" /> : null}
      <p className="la-loading__line"><span aria-hidden="true" className="uv-spinner" />{line}</p>
      {slow ? <p className="la-loading__slow">{LA_LOADING_SLOW_LINE}</p> : null}
      {variant === "reading" ? (
        <div className="la-loading__skeleton" aria-hidden="true">
          <div className="la-loading__night"><span /><span /><span /><span /><span /></div>
          <span className="la-loading__heading" />
          <div className="la-loading__card"><span /><span /><span /></div>
          <span className="la-loading__heading" />
          <div className="la-loading__card"><span /><span /></div>
        </div>
      ) : variant === "list" ? (
        <div className="la-loading__skeleton" aria-hidden="true">
          <div className="la-loading__row"><i /><span /><span /></div>
          <div className="la-loading__row"><i /><span /><span /></div>
          <div className="la-loading__row"><i /><span /><span /></div>
        </div>
      ) : null}
      {children}
    </section>
  );
}
