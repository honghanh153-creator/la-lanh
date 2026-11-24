import type { PixelMove } from "../pixelMove";

/** Kính rơi (Lá tự hỏng việc): puts on sunglasses to look cool, they slide off and fall, Lá is shy. 20 frames at 10 fps = 2 s. */
export const kinhRoi: PixelMove = {
  id: "kinh-roi",
  name: "Kính rơi",
  group: "tu-hong-viec",
  fps: 10,
  frames: [
    { arm: "up2", glasses: -6 },
    { arm: "up2", glasses: -4 },
    { arm: "up2", glasses: -2 },
    { arm: "up", glasses: 0, mouth: "flat" },
    { glasses: 0, mouth: "flat", lean: 1, sparkle: true },
    { glasses: 0, mouth: "flat", lean: 1, sparkle: true },
    { glasses: 0, mouth: "flat", lean: 1 },
    { glasses: 1, mouth: "flat", lean: 1 },
    { glasses: 2, mouth: "o" },
    { glasses: 3, mouth: "o", eyes: "wide" },
    { glasses: 5, mouth: "o", eyes: "wide", sq: -1 },
    { glasses: 8, mouth: "o", eyes: "wide", sq: -1 },
    { mouth: "o", eyes: "wide", sq: 1 },
    { mouth: "flat", eyes: "wide" },
    { mouth: "flat", eyes: "closed", sweat: true },
    { mouth: "flat", eyes: "closed", sweat: true, lean: -1 },
    { mouth: "smile", eyes: "closed", sweat: true, lean: -1 },
    { mouth: "smile", eyes: "happy", sweat: true },
    { mouth: "smile", eyes: "happy" },
    {},
  ],
};
