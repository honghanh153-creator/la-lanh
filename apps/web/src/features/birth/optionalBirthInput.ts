import type { ApproxWindow, BirthTimeMode, PlaceResult } from "../../shared/api/client";

export type OptionalBirthInput = {
  mode: BirthTimeMode;
  time: string;
  window: ApproxWindow;
  placeText: string;
  place: PlaceResult | null;
  consented: boolean;
};

export const emptyBirthDetails: OptionalBirthInput = {
  mode: "unknown", time: "", window: "morning", placeText: "", place: null, consented: false,
};

export function hasBirthDetails(value: OptionalBirthInput) {
  return value.mode !== "unknown" || Boolean(value.place);
}

export function birthDetailsError(value: OptionalBirthInput): string | null {
  if (value.mode === "exact" && !/^([01]\d|2[0-3]):[0-5]\d$/.test(value.time)) {
    return "Chọn đủ giờ và phút, hoặc chọn Chưa biết giờ nhé.";
  }
  if (value.placeText.trim() && !value.place) return "Chọn một nơi trong danh sách, hoặc xóa ô nơi sinh để thêm sau.";
  if (hasBirthDetails(value) && !value.consented) return "Đồng ý dùng giờ/nơi sinh để tính lá số, hoặc bỏ qua phần này nhé.";
  return null;
}
