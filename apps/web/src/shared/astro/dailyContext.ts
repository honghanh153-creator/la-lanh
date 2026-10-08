import { getContextualReading, getDailyNote, type SignalContext } from "../api/client";

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

export function dailyContextQueryKey(context: SignalContext): readonly string[] {
  return context === "auto" ? ["daily-note"] : ["daily-note-context", context];
}

export async function getDailyNoteForContext(context: SignalContext, signal?: AbortSignal) {
  const note = await getDailyNote(signal);
  if (context === "auto") return note;
  const projection = await getContextualReading(context, signal);
  return { ...note, reading_projection: projection };
}
