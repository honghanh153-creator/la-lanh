import { Info } from "@phosphor-icons/react";

type ReadingDisclaimerProps = {
  children: string;
  compact?: boolean;
};

/** The design system's "Lưu ý" note: warm note colours, info icon, bold lead-in. */
export function ReadingDisclaimer({ children, compact = false }: ReadingDisclaimerProps) {
  return (
    <aside
      aria-label="Lưu ý về bản đọc"
      className={`reading-disclaimer${compact ? " reading-disclaimer--compact" : ""}`}
      role="note"
    >
      <Info aria-hidden="true" weight="fill" />
      <p><strong>Lưu ý.</strong> {children}</p>
    </aside>
  );
}
