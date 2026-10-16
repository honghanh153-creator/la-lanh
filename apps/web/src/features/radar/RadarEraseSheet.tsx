import { AppSheet } from "../../shared/ui/AppSheet";
import type { useRadarEraseTarget } from "./useRadarEraseTarget";

export function RadarEraseSheet({
  body,
  confirmLabel = "Xoá",
  erase,
  onConfirm,
  pending,
  title,
}: {
  body: string;
  confirmLabel?: string;
  erase: ReturnType<typeof useRadarEraseTarget>;
  onConfirm: (id: string) => void;
  pending: boolean;
  title: (label: string) => string;
}) {
  const { open, target } = erase;
  return (
    <AppSheet closeDisabled={pending} onClose={erase.cancel} open={open} title={title(target?.label ?? "người này")}>
      <p className="uv-confirm__body">{body}</p>
      <div className="uv-confirm__actions">
        <button className="outline-button" disabled={pending} onClick={erase.cancel} type="button">Giữ lại</button>
        <button
          className="uv-danger-button"
          disabled={pending}
          onClick={() => {
            if (target) onConfirm(target.id);
            erase.cancel();
          }}
          type="button"
        >{confirmLabel}</button>
      </div>
    </AppSheet>
  );
}
