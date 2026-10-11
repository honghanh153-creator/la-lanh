import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { TarotSession } from "../../shared/api/client";
import { OnboardingMotionContext } from "../../shared/ui/onboardingMotion";
import { TarotRevealCeremony } from "./TarotRevealCeremony";

const cards: TarotSession["selected_cards"] = Array.from({ length: 5 }, (_, index) => ({
  fan_index: index,
  position_key: `position-${index}`,
  position_label: `Lá ${index + 1}`,
  card: {
    id: `fixture-${index}`, title_vi: `Lá thử ${index + 1}`, title_en: `Fixture ${index + 1}`,
    arcana: "major", core: "Nội dung thử", tension: "Điểm cần chú ý", resource: "Điều có thể thử",
    source_concept_ids: [],
  },
}));

describe("TarotRevealCeremony", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

  it.each([1, 3, 5])("reveals exactly %i chosen cards in order then finishes once", async (count) => {
    const done = vi.fn();
    render(<TarotRevealCeremony cards={cards.slice(0, count)} onComplete={done} />);
    expect(screen.getByRole("heading", { name: "Bài của bạn đang mở" })).toHaveFocus();
    const titles = screen.getAllByText(/Lá thử/).map((element) => element.textContent);
    expect(titles).toEqual(cards.slice(0, count).map((item) => item.card.title_vi));
    await act(() => vi.advanceTimersByTime(2799));
    expect(done).not.toHaveBeenCalled();
    await act(() => vi.advanceTimersByTime(1));
    expect(done).toHaveBeenCalledTimes(1);
  });

  it("cleans up the timer when skipped/unmounted", async () => {
    const done = vi.fn();
    const page = render(<TarotRevealCeremony cards={cards} onComplete={done} />);
    screen.getByRole("button", { name: "Xem bài ngay →" }).click();
    expect(done).toHaveBeenCalledTimes(1);
    page.unmount();
    await act(() => vi.advanceTimersByTime(4000));
    expect(done).toHaveBeenCalledTimes(1);
  });

  it("bypasses the scene for shared paused motion", async () => {
    const done = vi.fn();
    render(<OnboardingMotionContext.Provider value={{ paused: true, toggle: vi.fn() }}>
      <TarotRevealCeremony cards={cards} onComplete={done} />
    </OnboardingMotionContext.Provider>);
    expect(done).toHaveBeenCalledTimes(1);
    await act(() => vi.advanceTimersByTime(4000));
    expect(done).toHaveBeenCalledTimes(1);
  });

  it("bypasses the scene for system reduced motion", async () => {
    vi.stubGlobal("matchMedia", vi.fn(() => ({ matches: true })));
    const done = vi.fn();
    render(<TarotRevealCeremony cards={cards} onComplete={done} />);
    expect(done).toHaveBeenCalledTimes(1);
    await act(() => vi.advanceTimersByTime(4000));
    expect(done).toHaveBeenCalledTimes(1);
  });

  it("ends a running scene when reduced motion changes and removes the listener", async () => {
    const media = new EventTarget();
    vi.stubGlobal("matchMedia", vi.fn(() => Object.assign(media, { matches: false })));
    const remove = vi.spyOn(media, "removeEventListener");
    const done = vi.fn();
    const page = render(<TarotRevealCeremony cards={cards} onComplete={done} />);
    await act(() => media.dispatchEvent(Object.assign(new Event("change"), { matches: true })));
    expect(done).toHaveBeenCalledTimes(1);
    page.unmount();
    expect(remove).toHaveBeenCalledWith("change", expect.any(Function));
    await act(() => vi.advanceTimersByTime(4000));
    expect(done).toHaveBeenCalledTimes(1);
  });
});
