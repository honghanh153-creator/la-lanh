import type { RadarInvite } from "../../shared/api/client";

export const RADAR_CONTEXT_OPTIONS: Array<[RadarInvite["context"], string]> = [
  ["crush", "Crush"],
  ["friend", "Bạn thân"],
  ["partner", "Người yêu"],
  ["someone", "Một người"],
];

export const RADAR_PENDING_REQUEST_KEY = "la-lanh-radar-pending-request-id";
