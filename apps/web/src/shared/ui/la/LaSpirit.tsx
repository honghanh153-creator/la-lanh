import { useId } from "react";

import { useVibe } from "../../vibe/useVibe";
import type { MoonPhase } from "./moonPhase";
import "./la.css";

export type LaMood = "idle" | "think" | "happy" | "whisper";

/**
 * Lá, the app's companion: a small leaf spirit. Purely decorative; whatever
 * Lá "says" must also be rendered as real text next to it.
 */
export function LaSpirit({ mood = "idle", size = 56, className = "" }: {
  mood?: LaMood;
  size?: number;
  className?: string;
}) {
  const id = useId().replace(/:/g, "");
  const { vibe } = useVibe();
  const roast = vibe === "roast";
  return (
    <span aria-hidden="true" className={`la-spirit ${className}`.trim()} data-mood={mood} data-vibe={vibe} style={{ width: size, height: size }}>
      <svg viewBox="0 0 64 64" width={size} height={size} focusable="false">
        <defs>
          <linearGradient id={`${id}-body`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#8d5cf0" />
            <stop offset="55%" stopColor="#5a2ea8" />
            <stop offset="100%" stopColor="#3a1c78" />
          </linearGradient>
          <linearGradient id={`${id}-sheen`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#fff9e9" stopOpacity="0" />
            <stop offset="50%" stopColor="#fff9e9" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#fff9e9" stopOpacity="0" />
          </linearGradient>
        </defs>
        <g className="la-spirit__body">
          <path d="M32 6 C48 14 54 30 46 46 C41 55 23 55 18 46 C10 30 16 14 32 6 Z" fill={`url(#${id}-body)`} />
          <path className="la-spirit__sheen" d="M22 18 C26 12 30 10 32 9 C30 16 27 22 22 26 Z" fill={`url(#${id}-sheen)`} />
          <path d="M32 9 C31.6 14 31.8 18 32 21 M32 44 C32 47 32 50 32 53" stroke="#dfff4f" strokeWidth="1.6" strokeLinecap="round" fill="none" opacity="0.85" />
          <path d="M32 16 L27 12 M32 48 L37 44" stroke="#dfff4f" strokeWidth="1.2" strokeLinecap="round" opacity="0.6" />
          <g className="la-spirit__eyes">
            {mood === "happy"
              ? <>
                <path d="M23 33 Q26 29.5 29 33" stroke="#fff9e9" strokeWidth="2.2" strokeLinecap="round" fill="none" />
                <path d="M35 33 Q38 29.5 41 33" stroke="#fff9e9" strokeWidth="2.2" strokeLinecap="round" fill="none" />
              </>
              : <>
                <ellipse className="la-spirit__eye" cx="25.5" cy={mood === "think" ? 31 : 33} rx="3.4" ry="4.2" fill="#fff9e9" />
                <ellipse className="la-spirit__eye" cx="38.5" cy={mood === "think" ? 31 : 33} rx="3.4" ry="4.2" fill="#fff9e9" />
              </>}
            {mood === "whisper" && !roast ? <path d="M29 40 Q32 42 35 40" stroke="#fff9e9" strokeWidth="1.6" strokeLinecap="round" fill="none" /> : null}
            {roast ? <>
              <path className="la-spirit__brow" d="M22.5 26.5 L29.5 24.5" stroke="#fff9e9" strokeWidth="1.8" strokeLinecap="round" />
              <path d="M34.5 27.5 L41 28.5" stroke="#fff9e9" strokeWidth="1.8" strokeLinecap="round" />
              <path d="M28 40.5 Q33 43 37 39" stroke="#fff9e9" strokeWidth="1.7" strokeLinecap="round" fill="none" />
            </> : null}
          </g>
        </g>
        <g className="la-spirit__spark">
          {roast
            ? <path d="M52 8 C55 12 57 14 55.5 18 C54.5 20.5 50 21 48.8 18.2 C48 16 49.5 14.6 50.4 13.8 C50.6 15.2 51.6 15.8 52.4 15.2 C53.4 13.6 52.6 10.8 52 8 Z" fill="#ff6b4a" />
            : <path d="M52 10 L53.4 14 L57.5 15.4 L53.4 16.8 L52 21 L50.6 16.8 L46.5 15.4 L50.6 14 Z" fill="#dfff4f" />}
        </g>
        {mood === "think" ? <circle className="la-spirit__orbit" cx="32" cy="4" r="2" fill="#dfff4f" /> : null}
      </svg>
    </span>
  );
}

/** Lá with a speech bubble. The text is real, readable content. */
export function LaSays({ children, mood = "idle", live = false, className = "" }: {
  children: React.ReactNode;
  mood?: LaMood;
  live?: boolean;
  className?: string;
}) {
  return (
    <div className={`la-says ${className}`.trim()}>
      <LaSpirit mood={mood} size={48} />
      <p className="la-says__bubble" aria-live={live ? "polite" : undefined}>{children}</p>
    </div>
  );
}

/** Small moon disc drawn from the computed phase. */
export function MoonGlyph({ phase, size = 20 }: { phase: MoonPhase; size?: number }) {
  const r = 9;
  const c = 10;
  const rx = Math.max(0.01, r * Math.abs(1 - 2 * phase.illumination));
  const crescent = phase.illumination < 0.5;
  const outerSweep = phase.waxing ? 1 : 0;
  const innerSweep = phase.waxing ? (crescent ? 0 : 1) : (crescent ? 1 : 0);
  const lit = `M ${c} ${c - r} A ${r} ${r} 0 0 ${outerSweep} ${c} ${c + r} A ${rx} ${r} 0 0 ${innerSweep} ${c} ${c - r} Z`;
  return (
    <svg aria-hidden="true" className="moon-glyph" focusable="false" height={size} viewBox="0 0 20 20" width={size}>
      <circle cx={c} cy={c} fill="#3a2a5c" r={r} />
      {phase.illumination > 0.02 ? <path d={lit} fill="#fff4cf" /> : null}
      <circle cx={c} cy={c} fill="none" r={r} stroke="#dfff4f" strokeOpacity="0.5" strokeWidth="0.8" />
    </svg>
  );
}
