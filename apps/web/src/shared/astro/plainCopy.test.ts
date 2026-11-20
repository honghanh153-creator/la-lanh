import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { signDetails } from "./signs";

// New-user persona run and production journey review, 20.11.2026 (#773): first-week screens mixed
// English and mechanism words and opened with image-heavy lines. Owner style R15: plain, short,
// concrete Vietnamese.
const RETIRED_LABELS = [
  "Tạo safe link",
  "Copy link",
  "Story 9:16",
  "Square 1:1",
  "Các House",
  "Bản đọc Natal",
  "Bạn xuất hiện ngày nào?",
  "Chia sẻ card",
  "Trạm bắt sóng bên trong bạn",
  "giữ nguyên trên máy chủ",
];
const IMAGE_WORDS = ["nhịp", "cánh cửa", "căn phòng", "đỡ lấy", "hướng đi", "gọi tên"];

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return sources(path);
    return /\.tsx?$/.test(name) && !/\.test\.tsx?$/.test(name) ? [path] : [];
  });
}

describe("plain first-week copy", () => {
  it("keeps retired English and mechanism labels out of the app screens", () => {
    const root = resolve(__dirname, "../../features");
    const found = sources(root).flatMap((path) => {
      const text = readFileSync(path, "utf8");
      return RETIRED_LABELS.filter((label) => text.includes(label)).map((label) => `${path}: ${label}`);
    });
    expect(found).toEqual([]);
  });

  it("opens the reveal with one short, plain line per sign", () => {
    for (const [sign, detail] of Object.entries(signDetails)) {
      const words = detail.note.split(/\s+/).length;
      expect(words, sign).toBeLessThanOrEqual(16);
      expect(detail.note.startsWith("Bạn "), sign).toBe(true);
      for (const word of IMAGE_WORDS) expect(detail.note.toLowerCase(), `${sign}: ${word}`).not.toContain(word);
    }
  });
});
