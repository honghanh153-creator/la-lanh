import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PixelLa } from "./PixelLa";
import { PIXEL_MOVES } from "./moves";
import { moveDurationMs } from "./pixelMove";
import { GRID, PALETTE, drawPose } from "./pixelSprite";

const chao = PIXEL_MOVES.find((move) => move.id === "chao")!;

function setReducedMotion(reduced: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: reduced && query.includes("prefers-reduced-motion"),
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
  }));
}

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("Lá pixel drawing (#714 AC1)", () => {
  it("is drawn from code only: paths in the Mầm xanh palette, no image files", () => {
    setReducedMotion(false);
    const { container } = render(<PixelLa move={chao} label="Lá pixel" />);
    const svg = container.querySelector("svg")!;
    expect(svg.getAttribute("viewBox")).toBe(`0 0 ${GRID} ${GRID}`);
    expect(container.querySelectorAll("image, img, use, foreignObject")).toHaveLength(0);
    const fills = [...svg.querySelectorAll("path")].map((path) => path.getAttribute("fill"));
    expect(fills.length).toBeGreaterThan(4);
    for (const fill of fills) expect(PALETTE).toContain(fill);
  });

  it("every frame of every move stays inside the grid and keeps Lá's face and sprout", () => {
    for (const move of PIXEL_MOVES) {
      for (const pose of move.frames) {
        const grid = drawPose(pose);
        expect(grid).toHaveLength(GRID * GRID);
        expect(grid.includes(1)).toBe(true); // ink outline and face
        expect(grid.includes(8)).toBe(true); // sprout leaf
      }
    }
  });
});

describe("Lá pixel playing (#714 AC2, AC3)", () => {
  it("has a name for screen readers and plays once from the keyboard, then rests", async () => {
    setReducedMotion(false);
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<PixelLa move={chao} label="Lá pixel, bấm để chạy động tác Chào" />);
    const button = screen.getByRole("button", { name: "Lá pixel, bấm để chạy động tác Chào" });
    expect(button).toHaveAttribute("data-frame", "rest");
    button.focus();
    await user.keyboard("{Enter}");
    expect(button).toHaveAttribute("data-motion", "playing");
    act(() => { vi.advanceTimersByTime(moveDurationMs(chao) + 200); });
    expect(button).toHaveAttribute("data-frame", "rest");
    await user.keyboard(" ");
    expect(button).toHaveAttribute("data-motion", "playing");
  });

  it("keeps the rest pose under reduced motion, also when pressed", () => {
    setReducedMotion(true);
    vi.useFakeTimers();
    render(<PixelLa move={chao} label="Lá pixel" />);
    const button = screen.getByRole("button", { name: "Lá pixel" });
    expect(button).toHaveAttribute("data-motion", "still");
    const before = button.innerHTML;
    fireEvent.click(button);
    act(() => { vi.advanceTimersByTime(300); });
    expect(button).toHaveAttribute("data-frame", "rest");
    expect(button.innerHTML).toBe(before);
  });

  it("the lab's still preview stops a move that is playing", () => {
    setReducedMotion(false);
    vi.useFakeTimers();
    const { rerender } = render(<PixelLa move={chao} label="Lá pixel" />);
    fireEvent.click(screen.getByRole("button", { name: "Lá pixel" }));
    act(() => { vi.advanceTimersByTime(200); });
    expect(screen.getByRole("button")).toHaveAttribute("data-motion", "playing");
    rerender(<PixelLa move={chao} label="Lá pixel" still />);
    expect(screen.getByRole("button")).toHaveAttribute("data-frame", "rest");
    expect(screen.getByRole("button")).toHaveAttribute("data-motion", "still");
  });
});
