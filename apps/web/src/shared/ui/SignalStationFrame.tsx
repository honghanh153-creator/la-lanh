import type { ReactNode } from "react";
import { Pause, Play, StarFour } from "@phosphor-icons/react";

import { BrandMark } from "./BrandMark";
import { useOnboardingMotion } from "./onboardingMotion";
import "../styles/signal-onboarding.css";

type SignalStationFrameProps = {
  act: 0 | 1 | 2;
  children: ReactNode;
  titleId: string;
  actions?: ReactNode;
  className?: string;
  loading?: boolean;
};

const actLabels = {
  0: "BẮT ĐẦU",
  1: "NGÀY SINH",
  2: "LÁ ĐẦU TIÊN",
} as const;

export function SignalStationFrame({
  act,
  children,
  titleId,
  actions,
  className = "",
  loading = false,
}: SignalStationFrameProps) {
  const motion = useOnboardingMotion();
  const motionLabel = motion.paused ? "Tiếp tục chuyển động" : "Tạm dừng chuyển động";
  return (
    <main
      aria-busy={loading || undefined}
      aria-labelledby={titleId}
      data-motion-paused={motion.paused}
      className={`signal-station signal-station--act-${act} ${className}`.trim()}
    >
      <header className="signal-station__header">
        <BrandMark />
        <button
          type="button"
          className="signal-motion-toggle"
          aria-label={motionLabel}
          title={motionLabel}
          onClick={motion.toggle}
        >
          {motion.paused ? <Play size={20} aria-hidden="true" /> : <Pause size={20} aria-hidden="true" />}
        </button>
      </header>

      <div className="signal-progress" aria-label={`${actLabels[act]}, bước ${act + 1} trên 3`}>
        <span className="signal-progress__track" aria-hidden="true">
          <span className="signal-progress__fill" key={act} />
        </span>
        <p>BƯỚC {act + 1}/3 · {actLabels[act]}</p>
      </div>

      <div className="signal-station__art" aria-hidden="true">
        <span className="signal-station__planet" />
        <span className="signal-station__orbit signal-station__orbit--near">
          <StarFour weight="fill" />
        </span>
        <span className="signal-station__orbit signal-station__orbit--far">
          <StarFour weight="fill" />
        </span>
      </div>
      <div className="signal-station__content">{children}</div>
      {actions ? <footer className="signal-station__actions">{actions}</footer> : null}
    </main>
  );
}
