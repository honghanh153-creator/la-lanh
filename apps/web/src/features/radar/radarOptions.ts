import type { RadarInvite, RadarVoice } from "../../shared/api/client";

export const RADAR_CONTEXT_OPTIONS: Array<[RadarInvite["context"], string]> = [
  ["crush", "Crush"],
  ["friend", "Bạn thân"],
  ["partner", "Người yêu"],
  ["someone", "Một người"],
];

export const RADAR_PENDING_REQUEST_KEY = "la-lanh-radar-pending-request-id";

export const RADAR_VOICE_OPTIONS: Array<[RadarVoice, string, string]> = [
  ["straight_warm", "Nói thẳng, không lạnh", "Nói rõ ý, không phán."],
  ["gentle_specific", "Mềm & cụ thể", "Dịu hơn nhưng không mơ hồ."],
  ["playful_grounded", "Hơi cợt, vẫn có căn", "Vui vừa đủ, vẫn có căn cứ."],
  ["deep_dive", "Đọc kỹ", "Nhiều lớp và nói rõ giới hạn."],
];

export function radarVoiceLabel(voice: RadarVoice): string {
  return RADAR_VOICE_OPTIONS.find(([value]) => value === voice)?.[1] ?? "Nói thẳng, không lạnh";
}
