import type { ReadingContent } from "../api/client";

export function readingModeLabel(content: ReadingContent): string {
  return content.mode === "full_synthesis"
    ? "Aura · Tổng hòa lá số"
    : content.mode === "vibe_fallback"
      ? "Vibe · Một lớp từ ngày sinh"
      : "Bản đọc giới hạn";
}
