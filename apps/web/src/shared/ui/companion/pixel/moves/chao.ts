import type { PixelMove } from "../pixelMove";

/** Chào (Vui): crouch, hop, wave twice, land. 18 frames at 12 fps = 1.5 s. */
export const chao: PixelMove = {
  id: "chao",
  name: "Chào",
  group: "vui",
  fps: 12,
  frames: [
    { sq: 1 },
    { sq: 2, eyes: "happy" },
    { dy: -2, sq: -1, eyes: "happy", leaf: 1 },
    { dy: -4, sq: -2, eyes: "happy", arm: "up", leaf: 1, mouth: "open" },
    { dy: -5, sq: -1, eyes: "happy", arm: "up2", leaf: -1, mouth: "open", sparkle: true },
    { dy: -5, eyes: "happy", arm: "up", leaf: 1, mouth: "open", sparkle: true },
    { dy: -4, eyes: "happy", arm: "up2", leaf: -1, mouth: "open", sparkle: true },
    { dy: -2, sq: -1, eyes: "happy", arm: "up", leaf: 1 },
    { sq: 2, eyes: "happy", arm: "up2", leaf: 0 },
    { sq: 1, eyes: "happy", arm: "up", leaf: -1 },
    { eyes: "happy", arm: "up2", leaf: 1, mouth: "open" },
    { eyes: "happy", arm: "up", leaf: -1, mouth: "open" },
    { eyes: "happy", arm: "up2", leaf: 1, mouth: "open" },
    { eyes: "happy", arm: "up", leaf: 0 },
    { eyes: "open", arm: "up", lean: 1 },
    { eyes: "open", lean: 1 },
    { eyes: "closed" },
    {},
  ],
};
