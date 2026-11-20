import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

// Owner-approved consent/privacy copy (item AN1, 20.11.2026). These strings are owner-only:
// change them only with a new owner approval, never by rewording in a PR.
const read = (path: string) => readFileSync(join(process.cwd(), "src/features", path), "utf8");

describe("owner-approved copy AN1", () => {
  it("keeps the birth-date consent sentence and button verbatim", () => {
    const birth = read("birth/BirthDatePage.tsx");

    expect(birth).toContain("Bấm Tiếp tục là đồng ý dùng ngày sinh để tính lá số và note. Lá không tự bật AI viết lại.");
    expect(birth).toContain(': "Tiếp tục"}');
    expect(birth).not.toContain("Khớp tín hiệu");
  });

  it("keeps the Tarot privacy lines verbatim", () => {
    const tarot = read("tarot/TarotPage.tsx");

    expect(tarot).toContain("Không cần đăng nhập · chỉ gửi khi bạn bấm Xòe bài · mã hóa tối đa 30 ngày · không dùng để thống kê.");
    expect(tarot).toContain("Chỉ trình duyệt này mở lại được phiên.</p>");
    expect(tarot).not.toContain("analytics");
    expect(tarot).not.toContain("Không có chế độ bốc offline.");
  });
});
