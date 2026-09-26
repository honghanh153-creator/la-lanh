import type { ReactNode } from "react";

import { BrandMark } from "./BrandMark";
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
  0: "TRẠM BẮT SÓNG",
  1: "TRẠM BẮT SÓNG",
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
  return (
    <main
      aria-busy={loading || undefined}
      aria-labelledby={titleId}
      className={`signal-station signal-station--act-${act} ${className}`.trim()}
    >
      <header className="signal-station__header">
        <BrandMark />
      </header>

      <div className="signal-progress" aria-label={`${actLabels[act]}, bước ${act} trên 2`}>
        <span className="signal-progress__track" aria-hidden="true">
          <span className="signal-progress__fill" />
        </span>
        <p>{actLabels[act]} · 0{act}/02</p>
      </div>

      <div className="signal-station__art" aria-hidden="true" />
      <div className="signal-station__content">{children}</div>
      {actions ? <footer className="signal-station__actions">{actions}</footer> : null}
    </main>
  );
}
