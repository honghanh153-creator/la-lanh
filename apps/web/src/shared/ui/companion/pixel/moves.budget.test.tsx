import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PixelLa } from "./PixelLa";
import { MOVE_MAX_BYTES, moveDurationMs, moveProblems, type PixelMove } from "./pixelMove";
import { PIXEL_MOVES } from "./moves";

// The CI check for #715 AC2. Runs in `pnpm check` (web:test). For every move: file ≤ 8 KB,
// one run ≤ 5 s, still under reduced motion, playable from the keyboard. Red when any move breaks one.

const sources = import.meta.glob<string>("./moves/*.ts", { query: "?raw", import: "default", eager: true });
const moveFiles = Object.entries(sources).filter(([path]) => !path.endsWith("/index.ts"));
const bytesOf = (source: string) => new TextEncoder().encode(source).length;

function fileOf(move: PixelMove): string {
  const found = moveFiles.find(([, source]) => source.includes(`id: "${move.id}"`));
  if (!found) throw new Error(`${move.id} has no file in ./moves`);
  return found[1];
}

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

const cases = PIXEL_MOVES.map((move) => [move.id, move] as const);

describe("Lá pixel: all moves meet the week-2 budget (#715 AC2)", () => {
  it("has the four trial moves, each in its own file", () => {
    expect(PIXEL_MOVES.map((move) => move.id)).toEqual(["chao", "ngoi-cung", "kinh-roi", "uong-tra"]);
    expect(moveFiles).toHaveLength(PIXEL_MOVES.length);
    for (const move of PIXEL_MOVES) expect(fileOf(move)).toBeTruthy();
  });

  it.each(cases)("%s: file ≤ 8 KB, one run ≤ 5 s, 12–24 pictures", (_id, move) => {
    expect(moveProblems(move, bytesOf(fileOf(move)))).toEqual([]);
  });

  it.each(cases)("%s: stays still under reduced motion, also when pressed", (_id, move) => {
    setReducedMotion(true);
    vi.useFakeTimers();
    render(<PixelLa move={move} label={`Lá ${move.name}`} />);
    const button = screen.getByRole("button", { name: `Lá ${move.name}` });
    const rest = button.innerHTML;
    fireEvent.click(button);
    act(() => { vi.advanceTimersByTime(moveDurationMs(move)); });
    expect(button).toHaveAttribute("data-motion", "still");
    expect(button.innerHTML).toBe(rest);
  });

  it.each(cases)("%s: plays from the keyboard and is back at rest within its time", async (_id, move) => {
    setReducedMotion(false);
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<PixelLa move={move} label={`Lá ${move.name}`} />);
    const button = screen.getByRole("button", { name: `Lá ${move.name}` });
    button.focus();
    await user.keyboard("{Enter}");
    expect(button).toHaveAttribute("data-motion", "playing");
    const seen = new Set<string>();
    for (let t = 0; t < moveDurationMs(move); t += 1000 / move.fps) {
      seen.add(button.innerHTML);
      act(() => { vi.advanceTimersByTime(1000 / move.fps); });
    }
    act(() => { vi.advanceTimersByTime(50); });
    expect(button).toHaveAttribute("data-frame", "rest");
    // A move that never changes the picture would pass the other checks; require real motion.
    expect(seen.size).toBeGreaterThan(3);
  });
});

describe("the budget check goes red when a move breaks it (negative controls)", () => {
  const base: PixelMove = { id: "thu", name: "Thử", group: "vui", fps: 12, frames: Array.from({ length: 12 }, () => ({})) };

  it("a file over 8 KB", () => {
    expect(moveProblems(base, MOVE_MAX_BYTES + 1)).toEqual([`thu: ${MOVE_MAX_BYTES + 1} byte > ${MOVE_MAX_BYTES}`]);
  });

  it("a run over 5 seconds", () => {
    expect(moveProblems({ ...base, fps: 2 }, 100)).toEqual(["thu: 6000 ms > 5000"]);
  });

  it("too few or too many pictures, and the play-only group", () => {
    expect(moveProblems({ ...base, frames: base.frames.slice(0, 4) }, 100)).toEqual(["thu: 4 hình, cần 12–24"]);
    expect(moveProblems({ ...base, frames: [...base.frames, ...base.frames, {}] }, 100)).toEqual(["thu: 25 hình, cần 12–24"]);
    expect(moveProblems({ ...base, group: "nhay" }, 100)).toHaveLength(1);
  });

  it("the real move files are measured, not a constant", () => {
    const sizes = PIXEL_MOVES.map((move) => bytesOf(fileOf(move)));
    expect(new Set(sizes).size).toBe(sizes.length);
    expect(Math.min(...sizes)).toBeGreaterThan(200);
  });
});
