import type { PixelMove } from "../pixelMove";
import { chao } from "./chao";
import { kinhRoi } from "./kinhRoi";
import { ngoiCung } from "./ngoiCung";
import { uongTra } from "./uongTra";

/** Every Lá pixel move, one file each in this folder (the budget test checks both agree). */
export const PIXEL_MOVES: readonly PixelMove[] = [chao, ngoiCung, kinhRoi, uongTra];
