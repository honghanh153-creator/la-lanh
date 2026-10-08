import {
  BatteryCharging,
  Briefcase,
  ChatCircleDots,
  Heart,
  Leaf,
  Sparkle,
} from "@phosphor-icons/react";

import type { SignalContext } from "../api/client";
import { AppSheet } from "./AppSheet";

const contexts = [
  { value: "auto", label: "Để Lá chọn", compactLabel: "Lá chọn", detail: "Giữ góc nổi bật nhất từ chart hôm nay.", Icon: Sparkle },
  { value: "work", label: "Việc cần chốt", compactLabel: "Công việc", detail: "Nhìn rõ việc nên ưu tiên, hoãn hoặc nói lại.", Icon: Briefcase },
  { value: "relationships", label: "Một mối quan hệ", compactLabel: "Quan hệ", detail: "Đọc ranh giới, kỳ vọng và nhịp giữa hai người.", Icon: Heart },
  { value: "communication", label: "Điều cần nói", compactLabel: "Giao tiếp", detail: "Chuẩn bị cách mở lời mà không đoán hộ người khác.", Icon: ChatCircleDots },
  { value: "energy", label: "Nhịp cơ thể", compactLabel: "Năng lượng", detail: "Nhận ra lúc nên tăng tốc, giảm tải hoặc nghỉ.", Icon: BatteryCharging },
  { value: "self_care", label: "Điều mình cần", compactLabel: "Chăm mình", detail: "Đổi lời nhắc thành một cách chăm mình cụ thể hơn.", Icon: Leaf },
] as const;

type SignalContextPickerProps = {
  appearance?: "row" | "moon";
  error?: string | null;
  onOpenChange: (open: boolean) => void;
  onSelect: (context: SignalContext) => void;
  open: boolean;
  pending: SignalContext | null;
  selected: SignalContext;
};

export function SignalContextPicker({
  appearance = "row",
  error,
  onOpenChange,
  onSelect,
  open,
  pending,
  selected,
}: SignalContextPickerProps) {
  const active = contexts.find((item) => item.value === selected) ?? contexts[0];
  const ActiveIcon = active.Icon;

  return <>
    <section aria-label="Góc đang đọc" className={appearance === "moon" ? "home-note-context" : "signal-context-control"}>
      <button aria-label={`Góc đang đọc ${active.compactLabel}`} aria-haspopup="dialog" className={appearance === "moon" ? "home-note-moon" : "signal-context-trigger"} onClick={() => onOpenChange(true)} title="Đổi góc đọc Note" type="button">
        {appearance === "moon" ? <><img alt="" src="/assets/ultraviolet/moon.webp" /><span className="sr-only">Đổi góc đọc</span></> : <><span><ActiveIcon aria-hidden="true" weight="fill" /></span>
          <span><small>Góc đang đọc</small><strong>{active.compactLabel}</strong></span>
          <span aria-hidden="true">Đổi góc →</span></>}
      </button>
    </section>

    <AppSheet
      closeDisabled={pending !== null}
      eyebrow="Context Dial · riêng cho Note này"
      onClose={() => onOpenChange(false)}
      open={open}
      title="Bạn muốn Note giúp nhìn rõ điều gì?"
    >
      <p className="signal-context-sheet__intro">
        Chọn một tác dụng, không phải khai thêm về bạn. Lựa chọn này không được lưu thành sở thích.
      </p>
      <div aria-label="Chọn góc đọc" className="signal-context-sheet__options" role="group">
        {contexts.map(({ value, label, detail, Icon }) => {
          const selectedNow = selected === value;
          const loading = pending === value;
          return <button
            aria-label={label}
            aria-pressed={selectedNow}
            className={selectedNow ? "signal-context-sheet__option is-selected" : "signal-context-sheet__option"}
            disabled={pending !== null}
            key={value}
            onClick={() => selectedNow ? onOpenChange(false) : onSelect(value)}
            type="button"
          >
            <span><Icon aria-hidden="true" weight={selectedNow ? "fill" : "regular"} /></span>
            <span><strong>{label}</strong><small>{loading ? "Đang đổi góc…" : detail}</small></span>
          </button>;
        })}
      </div>
      {error ? <p className="signal-context-sheet__error" role="alert">{error}</p> : null}
    </AppSheet>
  </>;
}
