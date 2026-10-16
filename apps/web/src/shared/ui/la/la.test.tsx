import { act, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { dayPart, laGreeting } from "./laVoice";
import { LaLoading } from "./LaLoading";
import { LaSays, MoonGlyph } from "./LaSpirit";
import { moonPhase } from "./moonPhase";

describe("moonPhase", () => {
  it.each([
    ["2026-10-10T16:00:00Z", "new"],
    ["2026-10-26T04:00:00Z", "full"],
    ["2024-04-08T18:00:00Z", "new"],
    ["2024-12-15T09:00:00Z", "full"],
  ])("matches published lunations around %s", (iso, key) => {
    expect(moonPhase(new Date(iso)).key).toBe(key);
  });

  it("reports illumination between 0 and 1 and a readable label", () => {
    const phase = moonPhase(new Date("2026-10-18T12:00:00Z"));
    expect(phase.illumination).toBeGreaterThan(0.3);
    expect(phase.illumination).toBeLessThan(0.7);
    expect(phase.waxing).toBe(true);
    expect(phase.label).toMatch(/^Trăng/);
  });
});

describe("Lá voice", () => {
  it("greets by local time of day", () => {
    expect(dayPart(new Date(2026, 9, 11, 7))).toBe("morning");
    expect(dayPart(new Date(2026, 9, 11, 12))).toBe("noon");
    expect(dayPart(new Date(2026, 9, 11, 16))).toBe("afternoon");
    expect(dayPart(new Date(2026, 9, 11, 20))).toBe("evening");
    expect(dayPart(new Date(2026, 9, 11, 2))).toBe("late");
    expect(laGreeting(new Date(2026, 9, 11, 7)).line).toContain("buổi sáng");
  });

  it("never states an event as certain", () => {
    for (const hour of [7, 12, 16, 20, 2]) {
      expect(laGreeting(new Date(2026, 9, 11, hour)).line).not.toMatch(/sẽ (gặp|xảy ra|có)/);
    }
  });
});

describe("Lá components", () => {
  it("keeps Lá decorative and the words readable", () => {
    const { container } = render(<LaSays>Chào bạn</LaSays>);
    expect(screen.getByText("Chào bạn")).toBeInTheDocument();
    expect(container.querySelector(".la-spirit")).toHaveAttribute("aria-hidden", "true");
  });

  it("exposes the waiting text as a status", () => {
    render(<LaLoading delayMs={0} text="Lá đang mở bản đọc…" />);
    expect(screen.getByRole("status")).toHaveTextContent("Lá đang mở bản đọc…");
  });

  it("draws no lit area at new moon", () => {
    const { container } = render(<MoonGlyph phase={moonPhase(new Date("2026-10-10T16:00:00Z"))} />);
    expect(container.querySelector("path")).toBeNull();
  });
});

describe("LaLoading reassurance", () => {
  it("adds one calm line after eight seconds without replacing the status text", () => {
    vi.useFakeTimers();
    try {
      render(<LaLoading delayMs={0} text="Lá đang mở bản đọc…" variant="reading" />);
      expect(screen.queryByText("Vẫn đang mở, bạn chờ thêm chút nhé.")).not.toBeInTheDocument();
      act(() => { vi.advanceTimersByTime(8000); });
      expect(screen.getByRole("status")).toHaveTextContent("Lá đang mở bản đọc…");
      expect(screen.getByText("Vẫn đang mở, bạn chờ thêm chút nhé.")).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });
});
