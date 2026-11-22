import { MOVE_MAX_BYTES, MOVE_MAX_MS, moveDurationMs } from "./pixelMove";
import { PIXEL_MOVES } from "./moves";

// Raw source of each move file, so the size checked is the size shipped before minifying.
const sources = import.meta.glob<string>("./moves/*.ts", { query: "?raw", import: "default", eager: true });
const moveFiles = Object.entries(sources).filter(([path]) => !path.endsWith("/index.ts"));

describe("Lá pixel move budget (7-week plan, week 2)", () => {
  it("every move file is in the registry and every registered move has its own file", () => {
    expect(moveFiles.length).toBe(PIXEL_MOVES.length);
    for (const move of PIXEL_MOVES) {
      expect(moveFiles.some(([, source]) => source.includes(`id: "${move.id}"`))).toBe(true);
    }
  });

  it.each(moveFiles)("%s is at most 8 KB", (_path, source) => {
    expect(new TextEncoder().encode(source).length).toBeLessThanOrEqual(MOVE_MAX_BYTES);
  });

  it.each(PIXEL_MOVES.map((move) => [move.id, move] as const))("%s runs at most 5 seconds with 12–24 frames", (_id, move) => {
    expect(moveDurationMs(move)).toBeLessThanOrEqual(MOVE_MAX_MS);
    expect(move.frames.length).toBeGreaterThanOrEqual(12);
    expect(move.frames.length).toBeLessThanOrEqual(24);
  });

  it("no move uses the 'nhay' group, which is only for when the person taps Lá to play", () => {
    expect(PIXEL_MOVES.filter((move) => move.group === "nhay")).toEqual([]);
  });
});
