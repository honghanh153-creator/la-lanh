const KEY = "la-lanh-saved-note-mutations-v1";
const MAX_INTENTS = 60;
const HOUR_MS = 60 * 60 * 1000;
// Lifetimes by purpose (audit 2026-10-22 P04). A "save" can only succeed while the Daily note
// still exists (24 h). An "unsave" asks for deletion of a note that lives as long as the
// profile (30 days of inactivity for an anonymous one), so dropping it early would keep the
// note saved against the person's wish.
export const SAVED_INTENT_TTL_MS = { save: 24 * HOUR_MS, unsave: 30 * 24 * HOUR_MS } as const;

export type SavedNoteMutationIntent = {
  session_epoch: string;
  daily_note_id: string;
  revision_id: string | null;
  intent: "save" | "unsave";
  updated_at: string;
};

type EnqueueInput = {
  sessionEpoch: string;
  dailyNoteId: string;
  revisionId?: string | null;
  intent: SavedNoteMutationIntent["intent"];
};

function validIntent(value: unknown): value is SavedNoteMutationIntent {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return (
    typeof item.session_epoch === "string"
    && typeof item.daily_note_id === "string"
    && (typeof item.revision_id === "string" || item.revision_id === null)
    && (item.intent === "save" || item.intent === "unsave")
    && typeof item.updated_at === "string"
  );
}

function fresh(intent: SavedNoteMutationIntent, now: number): boolean {
  const age = now - Date.parse(intent.updated_at);
  return age >= 0 && age < SAVED_INTENT_TTL_MS[intent.intent];
}

function write(intents: SavedNoteMutationIntent[]): void {
  const serialized = JSON.stringify(intents.slice(-MAX_INTENTS));
  if (localStorage.getItem(KEY) !== serialized) localStorage.setItem(KEY, serialized);
}

export function readSavedNoteMutationQueue(): SavedNoteMutationIntent[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? "[]") as unknown;
    const now = Date.now();
    const intents = (Array.isArray(parsed) ? parsed : [])
      .filter(validIntent)
      .filter((intent) => fresh(intent, now));
    write(intents);
    return intents;
  } catch {
    localStorage.removeItem(KEY);
    return [];
  }
}

export function enqueueSavedNoteMutation(input: EnqueueInput): void {
  const revisionId = input.revisionId ?? null;
  const next: SavedNoteMutationIntent = {
    session_epoch: input.sessionEpoch,
    daily_note_id: input.dailyNoteId,
    revision_id: revisionId,
    intent: input.intent,
    updated_at: new Date().toISOString(),
  };
  const kept = readSavedNoteMutationQueue().filter((item) => !(
    item.session_epoch === next.session_epoch
    && item.daily_note_id === next.daily_note_id
    && item.revision_id === next.revision_id
  ));
  write([...kept, next]);
}

export async function flushSavedNoteMutations(
  currentSessionEpoch: string,
  apply: (intent: SavedNoteMutationIntent) => Promise<void>,
): Promise<void> {
  let queue = readSavedNoteMutationQueue().filter(
    (item) => item.session_epoch === currentSessionEpoch,
  );
  write(queue);
  for (const pending of [...queue].sort((a, b) => a.updated_at.localeCompare(b.updated_at))) {
    try {
      await apply(pending);
      queue = queue.filter((item) => !(
        item.session_epoch === pending.session_epoch
        && item.daily_note_id === pending.daily_note_id
        && item.revision_id === pending.revision_id
        && item.updated_at === pending.updated_at
      ));
      write(queue);
    } catch {
      // Keep current-session work for a later connectivity retry.
    }
  }
}

export function clearSavedNoteMutationQueue(): void {
  localStorage.removeItem(KEY);
}
