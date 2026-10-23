import { currentSessionEpoch, sessionGeneration } from "../session/sessionIdentity";

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

function sameIntent(a: SavedNoteMutationIntent): (b: SavedNoteMutationIntent) => boolean {
  return (b) => b.session_epoch === a.session_epoch
    && b.daily_note_id === a.daily_note_id
    && b.revision_id === a.revision_id
    && b.updated_at === a.updated_at;
}

export async function flushSavedNoteMutations(
  epoch: string,
  apply: (intent: SavedNoteMutationIntent) => Promise<void>,
): Promise<void> {
  const generation = sessionGeneration();
  write(readSavedNoteMutationQueue().filter((item) => item.session_epoch === epoch));
  const order = readSavedNoteMutationQueue().sort((a, b) => a.updated_at.localeCompare(b.updated_at));
  for (const pending of order) {
    // Recheck right before each send (audit P04): while an earlier call was waiting, the
    // session may have changed or been cleared, and this intent may have expired or been
    // replaced. Reading the stored queue again also drops anything past its deadline.
    const liveEpoch = currentSessionEpoch();
    if (sessionGeneration() !== generation || (liveEpoch !== null && liveEpoch !== epoch)) return;
    if (!readSavedNoteMutationQueue().some(sameIntent(pending))) continue;
    try {
      await apply(pending);
      write(readSavedNoteMutationQueue().filter((item) => !sameIntent(pending)(item)));
    } catch {
      // Keep current-session work for a later connectivity retry.
    }
  }
}

/**
 * History deletion removes the unsaved Daily notes a queued "save" would target, so those
 * intents go; queued "unsave" intents are deletion requests and stay until they reach the server.
 */
export function dropQueuedSaves(): void {
  write(readSavedNoteMutationQueue().filter((item) => item.intent === "unsave"));
}

/**
 * A direct save or unsave the server just accepted supersedes every queued intent for the same
 * note that was recorded before that call started, in either direction (Codex #48): an older
 * queued save must not re-save a note the person has since unsaved, and vice versa. Newer
 * intents and other sessions' intents stay.
 */
export function retireSupersededIntents(sessionEpoch: string, dailyNoteId: string, startedAt: number): void {
  write(readSavedNoteMutationQueue().filter((item) => !(
    item.session_epoch === sessionEpoch
    && item.daily_note_id === dailyNoteId
    && Date.parse(item.updated_at) <= startedAt
  )));
}

export function clearSavedNoteMutationQueue(): void {
  localStorage.removeItem(KEY);
}
