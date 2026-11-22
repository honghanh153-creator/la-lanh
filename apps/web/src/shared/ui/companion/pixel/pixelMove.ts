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
