import type { Pose } from "./pixelSprite";

/** The six groups from the 15.11 design note; "nhay" is only for when the person taps Lá to play. */
export type MoveGroup = "vui" | "tu-hong-viec" | "nhay" | "ngoi-cung" | "viec-nho" | "hoc";

/** One short move: plays once at `fps`, then Lá returns to the rest pose. */
export type PixelMove = {
  id: string;
  /** Internal name for the lab page; not user copy. */
  name: string;
  group: MoveGroup;
  fps: number;
  frames: readonly Pose[];
};

/** Budget from the 7-week plan (week 2): every move at most 8 KB and 5 seconds per run. */
export const MOVE_MAX_BYTES = 8 * 1024;
export const MOVE_MAX_MS = 5000;

export function moveDurationMs(move: PixelMove): number {
  return Math.round((move.frames.length * 1000) / move.fps);
}

/** Shortest and longest move, from the 15.11 design note (12–24 pictures per move). */
export const MOVE_MIN_FRAMES = 12;
export const MOVE_MAX_FRAMES = 24;

/** Why a move breaks the week-2 budget; empty when it fits. `sourceBytes` is its file size. */
export function moveProblems(move: PixelMove, sourceBytes: number): string[] {
  const problems: string[] = [];
  if (sourceBytes > MOVE_MAX_BYTES) problems.push(`${move.id}: ${sourceBytes} byte > ${MOVE_MAX_BYTES}`);
  if (moveDurationMs(move) > MOVE_MAX_MS) problems.push(`${move.id}: ${moveDurationMs(move)} ms > ${MOVE_MAX_MS}`);
  if (move.frames.length < MOVE_MIN_FRAMES || move.frames.length > MOVE_MAX_FRAMES) {
    problems.push(`${move.id}: ${move.frames.length} hình, cần ${MOVE_MIN_FRAMES}–${MOVE_MAX_FRAMES}`);
  }
  if (move.group === "nhay") problems.push(`${move.id}: nhóm "nhay" chỉ dùng khi người dùng tự chạm Lá để chơi`);
  return problems;
}
