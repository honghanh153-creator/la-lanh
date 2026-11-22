import type { PixelMove } from "../pixelMove";
import { chao } from "./chao";
import { ngoiCung } from "./ngoiCung";

/** Every Lá pixel move, one file each in this folder (the budget test checks both agree). */
export const PIXEL_MOVES: readonly PixelMove[] = [chao, ngoiCung];
