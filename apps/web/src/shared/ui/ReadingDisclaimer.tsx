import { Info } from "@phosphor-icons/react";

type ReadingDisclaimerProps = {
  children: string;
  compact?: boolean;
};

export function ReadingDisclaimer({ children, compact = false }: ReadingDisclaimerProps) {
  return (
    <aside
      aria-label="Lưu ý về bản đọc"
      className={`reading-disclaimer${compact ? " reading-disclaimer--compact" : ""}`}
      role="note"
    >
      <Info aria-hidden="true" weight="fill" />
      <div>
        <strong>Lưu ý</strong>
        <p>{children}</p>
      </div>
    </aside>
  );
}
