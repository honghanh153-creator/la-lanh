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
  /** When the direct call that queued this intent started (see beginSavedNoteMutation). */
  started_at?: number;
};

type EnqueueInput = {
  sessionEpoch: string;
  dailyNoteId: string;
  revisionId?: string | null;
  intent: SavedNoteMutationIntent["intent"];
  startedAt?: number;
};

// Browser-wide ordering of direct calls (Codex #48). Every tab shares this localStorage, so the
// ordering facts live here too, not in module memory: an acknowledged call leaves
// {session_epoch, daily_note_id, acked_start} for an hour (a direct call times out after 15 s),
// and both recording it and queueing a failed call happen under one Web Lock for all tabs.
const ACK_KEY = "la-lanh-saved-note-acks-v1";
const ACK_TTL_MS = HOUR_MS;
const QUEUE_LOCK = "la-lanh-saved-note-queue-v1";

type SavedAck = { session_epoch: string; daily_note_id: string; acked_start: number; recorded_at: number };

/** A start time comparable across tabs of one origin. */
export function beginSavedNoteMutation(): number {
  return typeof performance !== "undefined" && performance.timeOrigin
    ? performance.timeOrigin + performance.now()
    : Date.now();
}

function validAck(value: unknown): value is SavedAck {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return typeof item.session_epoch === "string"
    && typeof item.daily_note_id === "string"
    && typeof item.acked_start === "number"
    && typeof item.recorded_at === "number";
}

function readAcks(now: number): SavedAck[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(ACK_KEY) ?? "[]") as unknown;
    return (Array.isArray(parsed) ? parsed : [])
      .filter(validAck)
      .filter((ack) => now - ack.recorded_at >= 0 && now - ack.recorded_at < ACK_TTL_MS);
  } catch {
    return [];
  }
}

function writeAcks(acks: SavedAck[]): void {
  if (acks.length === 0) localStorage.removeItem(ACK_KEY);
  else localStorage.setItem(ACK_KEY, JSON.stringify(acks.slice(-MAX_INTENTS)));
}

function withQueueLock(work: () => void): Promise<void> {
  if (typeof navigator !== "undefined" && typeof navigator.locks?.request === "function") {
    return navigator.locks.request(QUEUE_LOCK, () => { work(); });
  }
  work();
  return Promise.resolve();
}

function validIntent(value: unknown): value is SavedNoteMutationIntent {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return (
    typeof item.session_epoch === "string"
    && typeof item.daily_note_id === "string"
    && (typeof item.revision_id === "string" || item.revision_id === null)
    && (item.intent === "save" || item.intent === "unsave")
    && typeof item.updated_at === "string"
    && (item.started_at === undefined || typeof item.started_at === "number")
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
    ...(input.startedAt === undefined ? {} : { started_at: input.startedAt }),
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
    // A queued intent is as old as the call that queued it, not as its enqueue time.
    && (item.started_at ?? Date.parse(item.updated_at)) <= startedAt
  )));
}

/**
 * The server accepted a direct call that started at ``startedAt``. In every tab, older queued
 * intents for that note retire, and an older call still in flight can no longer queue a retry.
 */
export function acknowledgeSavedMutation(sessionEpoch: string, dailyNoteId: string, startedAt: number): Promise<void> {
  return withQueueLock(() => {
    const now = Date.now();
    const others = readAcks(now).filter((ack) => !(ack.session_epoch === sessionEpoch && ack.daily_note_id === dailyNoteId));
    const previous = readAcks(now).find((ack) => ack.session_epoch === sessionEpoch && ack.daily_note_id === dailyNoteId);
    writeAcks([...others, {
      session_epoch: sessionEpoch,
      daily_note_id: dailyNoteId,
      acked_start: Math.max(previous?.acked_start ?? startedAt, startedAt),
      recorded_at: now,
    }]);
    retireSupersededIntents(sessionEpoch, dailyNoteId, startedAt);
  });
}

/** Queue a failed direct call for retry unless a call for the same note started later and was acknowledged. */
export function enqueueFailedSavedMutation(input: EnqueueInput & { startedAt: number }): Promise<void> {
  return withQueueLock(() => {
    const superseded = readAcks(Date.now()).some((ack) => ack.session_epoch === input.sessionEpoch
      && ack.daily_note_id === input.dailyNoteId
      && ack.acked_start >= input.startedAt);
    if (!superseded) enqueueSavedNoteMutation(input);
  });
}

export function clearSavedNoteMutationQueue(): void {
  localStorage.removeItem(ACK_KEY);
  localStorage.removeItem(KEY);
}
