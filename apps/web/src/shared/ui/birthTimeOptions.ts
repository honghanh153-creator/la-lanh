import type { ApproxWindow } from "../api/client";

export const birthTimeWindows: { value: ApproxWindow; label: string; hint: string }[] = [
  { value: "dawn", label: "Rạng sáng", hint: "00–06h" },
  { value: "morning", label: "Sáng", hint: "06–10h" },
  { value: "noon", label: "Trưa", hint: "10–14h" },
  { value: "afternoon", label: "Chiều", hint: "14–18h" },
  { value: "evening", label: "Tối", hint: "18–22h" },
  { value: "night", label: "Đêm", hint: "22–24h" },
];
