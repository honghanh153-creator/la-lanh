const KEY = "la-lanh-saved-note-mutations-v1";
const MAX_INTENTS = 60;

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

function write(intents: SavedNoteMutationIntent[]): void {
  const serialized = JSON.stringify(intents.slice(-MAX_INTENTS));
  if (localStorage.getItem(KEY) !== serialized) localStorage.setItem(KEY, serialized);
}

export function readSavedNoteMutationQueue(): SavedNoteMutationIntent[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? "[]") as unknown;
    const intents = (Array.isArray(parsed) ? parsed : []).filter(validIntent);
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
