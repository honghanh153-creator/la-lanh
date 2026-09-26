import type { MatchingReadiness } from "../../shared/api/client";

export const readinessOrder = [
  "age_18_plus",
  "birth_profile_level_3",
  "matching_profile",
  "matching_consent",
  "photo_verification",
] as const;

export type ReadinessKey = typeof readinessOrder[number];
export type MatchingNextAction = "age" | "birth" | "profile" | "consent" | "verification" | "join" | "leave" | "hold";

export const checkCopy: Record<ReadinessKey, { title: string; detail: string }> = {
  age_18_plus: { title: "Đủ 18 tuổi", detail: "Vòng Lá chỉ mở cho người từ 18 tuổi." },
  birth_profile_level_3: { title: "Lá đủ lớp", detail: "Ngày, giờ và nơi sinh đã đủ để đọc quan hệ." },
  matching_profile: { title: "Ranh giới ghép", detail: "Intent, khoảng tuổi và thành phố do bạn tự chọn." },
  matching_consent: { title: "Quyền ghép riêng", detail: "Dữ liệu Lá chỉ được dùng sau khi bạn đồng ý riêng." },
  photo_verification: { title: "Xác minh ảnh", detail: "Pool chỉ mở sau khi lớp an toàn thật duyệt." },
};

export type MatchingDeck = {
  action: MatchingNextAction;
  blocker: ReadinessKey | null;
  completed: number;
  ctaLabel: string;
  detail: string;
  orderedChecks: Array<{ key: ReadinessKey; complete: boolean; blocking: boolean }>;
  title: string;
};

export function deriveMatchingDeck(readiness: MatchingReadiness): MatchingDeck {
  const byKey = new Map(readiness.checks.map((check) => [check.key, check]));
  const orderedChecks = readinessOrder.map((key) => ({
    key,
    complete: byKey.get(key)?.complete ?? false,
    blocking: byKey.get(key)?.blocking ?? true,
  }));
  const completed = orderedChecks.filter((check) => check.complete).length;
  const blocker = orderedChecks.find((check) => check.blocking && !check.complete)?.key ?? null;

  if (blocker === "age_18_plus") return deck("age", blocker, completed, orderedChecks, "Vòng Lá dành cho người từ 18 tuổi", "Ngày sinh hiện tại chưa đạt điều kiện an toàn này.", "Chưa thể tham gia");
  if (blocker === "birth_profile_level_3") return deck("birth", blocker, completed, orderedChecks, "Còn thiếu giờ và nơi sinh", "Bổ sung hai dữ kiện để Lá không ghép bằng vài câu chung chung.", "Hoàn thiện Lá");
  if (blocker === "matching_profile") return deck("profile", blocker, completed, orderedChecks, "Đặt ranh giới trước khi gặp ai", "Chọn intent, khoảng tuổi và thành phố. Không dùng GPS.", "Tạo hồ sơ ghép");
  if (blocker === "matching_consent") return deck("consent", blocker, completed, orderedChecks, "Bạn quyết định dữ liệu nào được dùng", "Đọc phạm vi sử dụng rồi cấp quyền riêng cho Vòng Lá.", "Xem và đồng ý");
  if (blocker === "photo_verification") {
    if (readiness.verification_status === "pending") return deck("verification", blocker, completed, orderedChecks, "Ảnh đang được kiểm tra", "Chốt này vẫn đóng cho tới khi hệ thống an toàn trả kết quả.", "Xem trạng thái");
    if (readiness.verification_status === "fail") return deck("verification", blocker, completed, orderedChecks, "Cần xác minh lại", "Không có đường tắt qua chốt an toàn. Xem lý do và cách thử lại.", "Xem bước xác minh");
    return deck("verification", blocker, completed, orderedChecks, "Còn một chốt an toàn", "Xem cách xác minh ảnh trước khi hồ sơ được vào pool.", "Xem bước xác minh");
  }

  if (readiness.ready && readiness.profile?.active) return deck("leave", null, completed, orderedChecks, "Bạn đang ở trong vòng", "Bộ năm lá sẽ cố định trong phiên; rời vòng không báo cho ai.", "Rời Vòng Lá");
  if (readiness.ready) return deck("join", null, completed, orderedChecks, "Bạn đã bắt đúng sóng", "Sẵn sàng nhận năm kiểu kết nối trong vòng gần nhất.", "Tham gia Vòng Lá");
  return deck("hold", null, completed, orderedChecks, "Đang đồng bộ chốt an toàn", "Trạng thái từ server chưa thống nhất. Không có bước nào được tự mở.", "Chờ đồng bộ");
}

function deck(
  action: MatchingNextAction,
  blocker: ReadinessKey | null,
  completed: number,
  orderedChecks: MatchingDeck["orderedChecks"],
  title: string,
  detail: string,
  ctaLabel: string,
): MatchingDeck {
  return { action, blocker, completed, ctaLabel, detail, orderedChecks, title };
}
