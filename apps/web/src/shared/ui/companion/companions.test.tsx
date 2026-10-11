import { act, fireEvent, render, screen } from "@testing-library/react";

import { AuraSproutCompanion } from "./AuraSproutCompanion";
import { SkyWindowCompanion } from "./SkyWindowCompanion";
import { NIGHT_SETTLE_MS } from "./useCompanionRuntime";

const at = (h: number, min = 0) => new Date(2026, 9, 11, h, min);
const companions = [
  ["SkyWindowCompanion", SkyWindowCompanion, /Chạm vào cây trong cửa sổ trời/],
  ["AuraSproutCompanion", AuraSproutCompanion, /Chạm vào Mầm Aura/],
] as const;
const banned = /nhớ bạn|buồn vì|đợi bạn|đừng bỏ|sắp héo|cô đơn|streak|chuỗi|liên tiếp|chỉ hôm nay|lỡ là mất|bỏ lỡ|sẽ gặp|sắp có/i;

function setReducedMotion(matches: boolean) {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: (query: string) => ({
      matches: matches && query.includes("reduce"),
      media: query,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
    }),
  });
}

function root(container: HTMLElement) {
  return container.querySelector(".lc-companion") as HTMLElement;
}

afterEach(() => {
  Reflect.deleteProperty(window, "matchMedia");
  vi.useRealTimers();
});

describe.each(companions)("%s", (_name, Companion, buttonName) => {
  it("describes the current stage in Vietnamese and changes with the hour", () => {
    const labels = [7, 12, 17, 20, 23].map((hour) => {
      const { unmount } = render(<Companion now={at(hour)} growthDays={7} seed={42} />);
      const label = screen.getByRole("img").getAttribute("aria-label") ?? "";
      unmount();
      return label;
    });
    expect(new Set(labels).size).toBe(5);
    expect(labels[0]).toContain("bình minh");
    expect(labels[1]).toMatch(/buổi trưa, .*nở hoa/);
    expect(labels[3]).toContain("chạng vạng");
    expect(labels[4]).toMatch(/ban đêm.*đi ngủ thôi/);
    for (const label of labels) expect(label).not.toMatch(banned);
  });

  it("offers a named tap button that calls onTap", () => {
    const onTap = vi.fn();
    render(<Companion now={at(12)} onTap={onTap} />);
    fireEvent.click(screen.getByRole("button", { name: buttonName }));
    expect(onTap).toHaveBeenCalledTimes(1);
  });

  it("uses the label prop as the button name", () => {
    render(<Companion now={at(12)} label="Chạm để chào Lá" />);
    expect(screen.getByRole("button", { name: "Chạm để chào Lá" })).toBeInTheDocument();
  });

  it("sparkles on a daytime tap but stays quiet at night", () => {
    const day = render(<Companion now={at(12)} />);
    fireEvent.click(screen.getByRole("button"));
    expect(day.container.querySelector(".lc-burst")).not.toBeNull();
    day.unmount();
    const night = render(<Companion now={at(23)} />);
    fireEvent.click(screen.getByRole("button"));
    expect(night.container.querySelector(".lc-burst")).toBeNull();
  });

  it("renders a still pose for reduced motion and for the still preview", () => {
    setReducedMotion(true);
    const reduced = render(<Companion now={at(12)} />);
    expect(root(reduced.container)).toHaveAttribute("data-cmotion", "still");
    expect(reduced.container.querySelector("svg path")).not.toBeNull();
    fireEvent.click(screen.getByRole("button"));
    // Motionless feedback only: CSS removes every animation in the still pose.
    expect(reduced.container.querySelector(".lc-burst")).not.toBeNull();
    reduced.unmount();
    setReducedMotion(false);
    const preview = render(<Companion now={at(12)} still />);
    expect(root(preview.container)).toHaveAttribute("data-cmotion", "still");
  });

  it("pauses while the page is hidden", () => {
    const { container } = render(<Companion now={at(12)} />);
    expect(root(container)).toHaveAttribute("data-cmotion", "running");
    Object.defineProperty(document, "hidden", { configurable: true, value: true });
    act(() => { document.dispatchEvent(new Event("visibilitychange")); });
    expect(root(container)).toHaveAttribute("data-cmotion", "paused");
    Object.defineProperty(document, "hidden", { configurable: true, value: false });
    act(() => { document.dispatchEvent(new Event("visibilitychange")); });
    expect(root(container)).toHaveAttribute("data-cmotion", "running");
  });

  it("settles into stillness within 10 seconds at night", () => {
    vi.useFakeTimers();
    const { container } = render(<Companion now={at(23)} />);
    expect(root(container)).toHaveAttribute("data-phase", "night");
    expect(root(container)).toHaveAttribute("data-cmotion", "running");
    act(() => { vi.advanceTimersByTime(NIGHT_SETTLE_MS); });
    expect(root(container)).toHaveAttribute("data-cmotion", "paused");
  });

  it("switches accents for the roast vibe", () => {
    const { container } = render(<Companion now={at(12)} vibe="roast" />);
    expect(root(container)).toHaveAttribute("data-vibe", "roast");
    expect(container.querySelector(".lc-roast-sparks")).not.toBeNull();
  });

  it("is deterministic for a seed and unaffected by vibe or time for its permanent shape", () => {
    const a = render(<Companion now={at(12)} growthDays={30} seed={1234} />);
    const first = a.container.innerHTML;
    a.unmount();
    const b = render(<Companion now={at(12)} growthDays={30} seed={1234} />);
    expect(b.container.innerHTML.replace(/_r_\w+_|r\d+/g, "")).toBe(first.replace(/_r_\w+_|r\d+/g, ""));
  });

  it("shows festival skins only when active", () => {
    const tet = render(<Companion now={at(12)} festival="tet" />);
    expect(root(tet.container)).toHaveAttribute("data-festival", "tet");
    expect(screen.getByRole("img").getAttribute("aria-label")).toMatch(/Tết/);
    tet.unmount();
    const none = render(<Companion now={new Date(2027, 1, 6, 12)} festival={null} />);
    expect(root(none.container)).not.toHaveAttribute("data-festival");
    none.unmount();
    const auto = render(<Companion now={new Date(2027, 1, 6, 12)} />);
    expect(root(auto.container)).toHaveAttribute("data-festival", "tet");
  });

  it("stays within the SVG node budget at full growth", () => {
    const { container } = render(<Companion now={at(20)} growthDays={400} seed={99} festival="trung-thu" vibe="roast" />);
    expect(container.querySelectorAll("svg *").length).toBeLessThanOrEqual(200);
  });
});

describe("SkyWindowCompanion growth", () => {
  it("only adds leaves as days accumulate", () => {
    const counts = [0, 3, 7, 14, 30, 60, 120].map((days) => {
      const { container, unmount } = render(<SkyWindowCompanion now={at(10)} growthDays={days} seed={5} />);
      const count = container.querySelectorAll(".lc-leaves path").length;
      unmount();
      return count;
    });
    for (let i = 1; i < counts.length; i += 1) expect(counts[i]).toBeGreaterThanOrEqual(counts[i - 1]);
    expect(counts[6]).toBeGreaterThan(counts[0]);
  });

  it("shows the welcome-back gift by day only", () => {
    render(<SkyWindowCompanion now={at(10)} welcomeBack />);
    expect(screen.getByRole("img").getAttribute("aria-label")).toContain("một chiếc lá mới");
  });
});

describe("AuraSproutCompanion growth", () => {
  it("keeps earned accessories and describes them", () => {
    const early = render(<AuraSproutCompanion now={at(12)} growthDays={0} seed={5} />);
    const earlyLabel = screen.getByRole("img").getAttribute("aria-label") ?? "";
    early.unmount();
    render(<AuraSproutCompanion now={at(12)} growthDays={120} seed={5} />);
    const lateLabel = screen.getByRole("img").getAttribute("aria-label") ?? "";
    expect(earlyLabel).toContain("mầm mới");
    expect(lateLabel).toContain("cây lớn");
    expect(lateLabel).toContain("viền vàng");
  });

  it("looks sleepy at night with closed eyes and no tap reactions", () => {
    const { container } = render(<AuraSproutCompanion now={at(23)} reacting="happy" />);
    expect(root(container)).toHaveAttribute("data-asleep", "true");
    expect(container.querySelector(".lc-eyes")).toBeNull();
    expect(container.querySelector(".lc-zz")).not.toBeNull();
  });
});
