import { Gift, X } from "@phosphor-icons/react";

import type { ReadingContent, ReadingProjection } from "../api/client";

type AvailableReadingUpdate = NonNullable<ReadingProjection["available_update"]>;

type ReadingUpdateGiftProps = {
  activeMode?: ReadingContent["mode"];
  update: AvailableReadingUpdate;
  pending: boolean;
  onActivate: () => void;
  onDismiss?: () => void;
  detail?: boolean;
};

export function ReadingUpdateGift({
  activeMode,
  update,
  pending,
  onActivate,
  onDismiss,
  detail = false,
}: ReadingUpdateGiftProps) {
  const unlocksFullChart = activeMode !== "full_synthesis"
    && update.content.mode === "full_synthesis";
  const copy = unlocksFullChart
    ? {
        eyebrow: "Bản đọc đủ lớp",
        title: "Note này có một bản đủ lớp",
        body: "Bản mới nối hành tinh, nhà và góc thành một câu chuyện cụ thể hơn; bầu trời hiện tại chỉ xuất hiện khi có căn cứ.",
        action: "Mở bản đủ lớp",
      }
    : {
        eyebrow: "Note đã được đọc lại",
        title: "Có một bản đọc mới hơn",
        body: "Lá đã đọc lại dữ liệu hiện có bằng ma trận kiến thức mới. Bạn chủ động chọn có đổi sang bản này hay không.",
        action: "Đọc bản mới",
      };

  return (
    <aside
      className={`reading-gift${detail ? " reading-gift--detail" : ""}`}
      aria-labelledby={`reading-update-title${detail ? "-detail" : ""}`}
    >
      <div className="reading-gift__icon"><Gift aria-hidden="true" weight="fill" /></div>
      <div>
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2 id={`reading-update-title${detail ? "-detail" : ""}`}>{copy.title}</h2>
        <p>{copy.body}</p>
      </div>
      {onDismiss ? (
        <button
          aria-label="Để bản mới lại sau"
          className="reading-gift__close"
          onClick={onDismiss}
          type="button"
        ><X aria-hidden="true" /></button>
      ) : null}
      <button
        className="electric-button"
        disabled={pending}
        onClick={onActivate}
        type="button"
      >
        <Gift aria-hidden="true" /> {pending ? "Đang mở…" : copy.action}
      </button>
    </aside>
  );
}
