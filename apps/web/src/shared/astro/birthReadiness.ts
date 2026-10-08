import type { BirthSupplementState } from "../api/client";

/** Only confirmed server state may trigger a request for more personal data. */
export function birthCompletionPrompt(state: BirthSupplementState | undefined) {
  if (!state) return null;
  const hasTime = state.birth_time_mode === "exact" && state.time_precision === "exact";
  const hasPlace = Boolean(state.place_display_name && state.timezone_id);
  if (hasTime && hasPlace) return null;
  if (hasTime) return { cta: "Thêm nơi sinh", body: "Bạn đã có giờ sinh. Thêm nơi sinh để mở bản đọc tổng quan." };
  if (state.birth_time_mode === "approx_window") return { cta: "Làm rõ giờ sinh", body: "Giờ gần đúng đã được lưu. Có giờ chính xác và nơi sinh, bản đọc tổng quan sẽ rõ hơn." };
  if (hasPlace) return { cta: "Thêm giờ sinh", body: "Bạn đã có nơi sinh. Thêm giờ sinh để mở bản đọc tổng quan." };
  return { cta: "Thêm giờ & nơi sinh", body: "Thêm khi bạn muốn đọc sâu hơn về cảm xúc, cách kết nối và những điều hay lặp lại." };
}
