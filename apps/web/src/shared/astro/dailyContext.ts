import { getContextualReading, getDailyNote, type SignalContext } from "../api/client";
import type { AppVibe } from "../vibe/vibe";

export function parseDailyContext(value: string | null): SignalContext {
  switch (value) {
    case "work":
    case "relationships":
    case "communication":
    case "energy":
    case "self_care":
      return value;
    default:
      return "auto";
  }
}

export function dailyContextPath(path: "/note/today" | "/card", context: SignalContext): string {
  return context === "auto" ? path : `${path}?context=${context}`;
}

export function dailyContextQueryKey(context: SignalContext, vibe: AppVibe = "direct"): readonly string[] {
  // Roast wording lives under its own keys so the direct note, its local cache
  // and activation updates keep their existing exact ["daily-note"] key.
  if (vibe === "roast") return ["daily-note", "roast", context];
  return context === "auto" ? ["daily-note"] : ["daily-note-context", context];
}

export async function getDailyNoteForContext(context: SignalContext, signal?: AbortSignal, vibe: AppVibe = "direct") {
  const note = vibe === "roast" ? await getDailyNote(signal, vibe) : await getDailyNote(signal);
  if (context === "auto") return note;
  const projection = vibe === "roast"
    ? await getContextualReading(context, signal, vibe)
    : await getContextualReading(context, signal);
  return { ...note, reading_projection: projection };
}
