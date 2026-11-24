import { useEffect, useMemo, useRef, useState } from "react";

import { useOnboardingMotion } from "../../onboardingMotion";
import { usePrefersReducedMotion } from "../useCompanionRuntime";
import type { PixelMove } from "./pixelMove";
import { GRID, PALETTE, PALETTE_OPACITY, drawPose, pixelPaths, type Pose } from "./pixelSprite";
import "./pixel-la.css";

type Props = {
  move: PixelMove;
  /** Accessible name of the button (lab copy today; user copy goes through the registry in week 5). */
  label: string;
  size?: number;
  /** Lab preview of reduced motion. */
  still?: boolean;
  /** Changing this number plays the move once (lab buttons); 0 does nothing. */
  playKey?: number;
  onPlayed?: () => void;
};

const REST: Pose = {};

function Sprite({ pose }: { pose: Pose }) {
  const parts = useMemo(() => pixelPaths(drawPose(pose)), [pose]);
  return (
    <svg viewBox={`0 0 ${GRID} ${GRID}`} shapeRendering="crispEdges" aria-hidden="true" focusable="false">
      {parts.map(({ colour, d }) => (
        <path key={colour} d={d} fill={PALETTE[colour]} fillOpacity={PALETTE_OPACITY[colour]} />
      ))}
    </svg>
  );
}

/**
 * Lá pixel (week-2 trial, behind PIXEL_LA_ON_USER_SCREENS). A button: click, Enter or Space plays
 * the move once, never in a loop. With reduced motion (device setting, the app's motion switch,
 * or `still`) Lá keeps the rest pose and a press changes nothing on screen.
 */
export function PixelLa({ move, label, size = 144, still = false, playKey = 0, onPlayed }: Props) {
  const reduced = usePrefersReducedMotion();
  const appMotion = useOnboardingMotion();
  const quiet = still || reduced || appMotion.paused;
  const [frame, setFrame] = useState<number | null>(null);
  const timer = useRef<number | null>(null);

  const stop = () => {
    if (timer.current !== null) window.clearTimeout(timer.current);
    timer.current = null;
  };

  const play = () => {
    stop();
    if (quiet) {
      setFrame(null);
      onPlayed?.();
      return;
    }
    const step = (index: number) => {
      if (index >= move.frames.length) {
        timer.current = null;
        setFrame(null);
        onPlayed?.();
        return;
      }
      setFrame(index);
      timer.current = window.setTimeout(() => step(index + 1), 1000 / move.fps);
    };
    step(0);
  };

  useEffect(() => {
    if (playKey > 0) play();
    // A new playKey is the only trigger; the move and motion are read at that moment.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playKey]);
  useEffect(() => {
    if (quiet) { stop(); setFrame(null); }
  }, [quiet]);
  useEffect(() => stop, []);

  const pose = frame === null ? REST : move.frames[frame];
  return (
    <button
      type="button"
      className="pixel-la"
      aria-label={label}
      data-move={move.id}
      data-frame={frame === null ? "rest" : String(frame)}
      data-motion={quiet ? "still" : frame === null ? "ready" : "playing"}
      style={{ width: size, height: size }}
      onClick={play}
    >
      <Sprite pose={pose} />
    </button>
  );
}
