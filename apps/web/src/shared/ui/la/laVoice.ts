import type { MoodValue } from "../../api/client";
import type { AppVibe } from "../../vibe/vibe";
import { moonPhase, type MoonPhase } from "./moonPhase";

// Lá's framing microcopy. It greets, waits and reacts; it never changes the
// meaning of a reading, predicts events, or speaks for another person.
// Voices: "direct" (plain, warm Vietnamese) and "roast" (owner-approved
// 2026-10-11: teasing the situation, never the person, always with a way out).

export type DayPart = "morning" | "noon" | "afternoon" | "evening" | "late";

export function dayPart(at: Date = new Date()): DayPart {
  const hour = at.getHours();
  if (hour >= 5 && hour < 11) return "morning";
  if (hour >= 11 && hour < 14) return "noon";
  if (hour >= 14 && hour < 18) return "afternoon";
  if (hour >= 18 && hour < 22) return "evening";
  return "late";
}

const ROAST_GREETINGS: Record<DayPart, string> = {
  morning: "Dậy rồi đó hả? Note hôm nay Lá để sẵn, đọc trước khi lướt TikTok nha.",
  noon: "Giữa trưa rồi, ăn chưa mà đã mở app xem số phận? Đùa thôi, xem note đi.",
  afternoon: "Chiều rồi mà vẫn chưa xong việc buổi sáng hả? Lá biết hết á.",
  evening: "Tối rồi. Ngồi xuống, kể Lá nghe hôm nay ai làm bạn cạn pin.",
  late: "Khuya vậy còn thức? Đọc nhanh rồi cất điện thoại, mai còn làm người.",
};

const GREETINGS: Record<DayPart, string> = {
  morning: "Chào buổi sáng. Lá để sẵn note hôm nay cho bạn rồi.",
  noon: "Giữa ngày rồi. Ghé Lá một chút nhé.",
  afternoon: "Chiều rồi. Xem nhanh điều đáng để ý hôm nay?",
  evening: "Tối rồi. Ngồi xuống với Lá một nhịp.",
  late: "Khuya rồi đó. Đọc nhẹ thôi rồi đi ngủ nhé.",
};

export type LaGreeting = { line: string; moon: MoonPhase; part: DayPart };

export function laGreeting(at: Date = new Date(), vibe: AppVibe = "direct"): LaGreeting {
  const part = dayPart(at);
  return { line: (vibe === "roast" ? ROAST_GREETINGS : GREETINGS)[part], moon: moonPhase(at), part };
}

export const LA_LOADING_LINES = [
  "Lá đang dò sóng…",
  "Lá đang lật trang lá số…",
  "Lá đang gom ánh sao…",
] as const;

export const LA_ROAST_LOADING_LINES = [
  "Đợi xíu, Lá đang soi bạn…",
  "Vũ trụ đang gõ… đừng giục.",
  "Lá đang lục lại hồ sơ drama của bạn…",
] as const;

export function laLoadingLines(vibe: AppVibe): readonly string[] {
  return vibe === "roast" ? LA_ROAST_LOADING_LINES : LA_LOADING_LINES;
}

export const LA_MOOD_REACTIONS: Record<MoodValue, string> = {
  "Rực": "Bạn đang nhiều năng lượng. Nhớ để dành một chút cho mình.",
  Chill: "Nhịp này đẹp đấy. Không cần đẩy mọi thứ đi nhanh hơn.",
  "Đuối": "Hôm nay bớt một việc cũng là chăm mình.",
  "Căng": "Thở chậm một nhịp trước khi trả lời điều quan trọng.",
  "Lạc trôi": "Chưa cần hiểu hết. Chỉ cần tìm một điểm để quay về.",
};

export const LA_ROAST_MOOD_REACTIONS: Record<MoodValue, string> = {
  "Rực": "Năng lượng max ghê. Nhớ chừa pin cho tối nay, đừng đốt hết lúc 10 giờ sáng.",
  Chill: "Chill quá ha. Giữ nhịp này, đừng để group chat kéo bạn vào drama.",
  "Đuối": "Pin 3% mà còn gồng. Bớt một việc đi, thế giới không sập đâu.",
  "Căng": "Vai đang gồng tới tai rồi kìa. Thở ra một hơi rồi hẵng rep tin nhắn.",
  "Lạc trôi": "Đang trôi giữa vũ trụ hả? Neo lại một việc nhỏ trước đã.",
};

export function laMoodReaction(mood: MoodValue, vibe: AppVibe): string {
  return (vibe === "roast" ? LA_ROAST_MOOD_REACTIONS : LA_MOOD_REACTIONS)[mood];
}

export const LA_MOOD_NUDGE = "Hôm nay bạn đang ở mood nào? Chạm để kể Lá nghe.";
