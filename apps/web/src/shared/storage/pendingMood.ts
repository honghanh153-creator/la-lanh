import { currentSessionEpoch, sessionGeneration } from "../session/sessionIdentity";

export const PENDING_MOOD_KEY = "la-lanh-pending-mood-v1";
/**
 * Latest acknowledged choice per session and note: survives Home unmounting, so a request that
 * fails after a newer choice was accepted cannot store or replay the older mood (Codex #48).
 */
export const PENDING_MOOD_ACK_KEY = "la-lanh-pending-mood-ack-v1";
// A mood belongs to one daily note, which leaves Home after 24 h (Daily auto-hide), so an
// offline check-in is only worth retrying for that long (audit 2026-10-22 P04).
export const PENDING_MOOD_TTL_MS = 24 * 60 * 60 * 1000;

type PendingMood<Mood extends string> = {
  session_epoch: string;
  note_id: string;
  mood: Mood;
  /** First capture of this choice; a retry never renews it. */
  saved_at: number;
};

/** Who made a mood choice and when, captured when the choice is made, before any request. */
export type MoodIntent = { sessionEpoch: string | null; generation: number; savedAt: number };

export function captureMoodIntent(savedAt = Date.now()): MoodIntent {
  return { sessionEpoch: currentSessionEpoch(), generation: sessionGeneration(), savedAt };
}

type MoodAck = { session_epoch: string; note_id: string; acked_at: number };

function remove(): void {
  try { localStorage.removeItem(PENDING_MOOD_KEY); } catch { /* Storage may be unavailable. */ }
}

function readAck(): Partial<MoodAck> | null {
  try {
    const parsed = JSON.parse(localStorage.getItem(PENDING_MOOD_ACK_KEY) ?? "null") as unknown;
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

/** Was a choice made at or after ``savedAt`` already accepted for this session and note? */
function superseded(sessionEpoch: string | null | undefined, noteId: string | undefined, savedAt: number): boolean {
  const ack = readAck();
  return Boolean(ack && ack.session_epoch === sessionEpoch && ack.note_id === noteId && Number(ack.acked_at) >= savedAt);
}

function read(): Partial<PendingMood<string>> | null | undefined {
  let raw: string | null;
  try { raw = localStorage.getItem(PENDING_MOOD_KEY); } catch { return undefined; }
  if (raw === null) return null;
  try {
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function live(pending: Partial<PendingMood<string>>, now: number): boolean {
  const age = now - Number(pending.saved_at);
  return typeof pending.note_id === "string"
    && typeof pending.mood === "string"
    && pending.session_epoch === currentSessionEpoch()
    && age >= 0 && age < PENDING_MOOD_TTL_MS;
}

/**
 * Keep a failed check-in for a later retry, labelled with the owner that made it. Nothing is kept
 * when the session changed while the request was in flight, or once the first-capture deadline
 * has passed: a retry keeps the original clock instead of starting a new one.
 */
export function keepPendingMood<Mood extends string>(noteId: string, mood: Mood, intent: MoodIntent): void {
  if (!intent.sessionEpoch) return;
  if (intent.sessionEpoch !== currentSessionEpoch() || intent.generation !== sessionGeneration()) return;
  const age = Date.now() - intent.savedAt;
  if (age < 0 || age >= PENDING_MOOD_TTL_MS) return;
  if (superseded(intent.sessionEpoch, noteId, intent.savedAt)) return;
  const current = read();
  // A newer choice that is already waiting wins over an older one failing late.
  if (current && current.session_epoch === intent.sessionEpoch && current.note_id === noteId
    && Number(current.saved_at) > intent.savedAt) return;
  const pending: PendingMood<Mood> = { session_epoch: intent.sessionEpoch, note_id: noteId, mood, saved_at: intent.savedAt };
  try { localStorage.setItem(PENDING_MOOD_KEY, JSON.stringify(pending)); } catch { /* Storage may be unavailable. */ }
}

/** Drop anything that can no longer be replayed (expired, another session, old format), online or not. */
export function prunePendingMood(): void {
  const pending = read();
  if (pending && (!live(pending, Date.now())
    || superseded(pending.session_epoch, pending.note_id, Number(pending.saved_at)))) remove();
  const ack = readAck();
  const ackAge = Date.now() - Number(ack?.acked_at);
  if (ack && (ack.session_epoch !== currentSessionEpoch() || !(ackAge >= 0 && ackAge < PENDING_MOOD_TTL_MS))) {
    try { localStorage.removeItem(PENDING_MOOD_ACK_KEY); } catch { /* Storage may be unavailable. */ }
  }
}

/**
 * The mood to retry for this note, removing the stored entry either way: it is replayed only
 * for the same session and note within the original deadline.
 */
export function takePendingMood<Mood extends string>(
  noteId: string,
  valid: (value: unknown) => value is Mood,
): { mood: Mood; intent: MoodIntent } | null {
  const pending = read();
  if (!pending) return null;
  remove();
  if (!live(pending, Date.now()) || pending.note_id !== noteId || !valid(pending.mood)
    || superseded(pending.session_epoch, noteId, Number(pending.saved_at))) return null;
  return { mood: pending.mood, intent: captureMoodIntent(Number(pending.saved_at)) };
}

/** The server accepted the choice made at ``intent``: an equal or older waiting choice is done. */
export function acknowledgePendingMood(noteId: string, intent: MoodIntent): void {
  if (!intent.sessionEpoch || intent.sessionEpoch !== currentSessionEpoch()) return;
  const pending = read();
  if (pending && pending.note_id === noteId && pending.session_epoch === intent.sessionEpoch
    && Number(pending.saved_at) <= intent.savedAt) remove();
  if (!superseded(intent.sessionEpoch, noteId, intent.savedAt)) {
    const ack: MoodAck = { session_epoch: intent.sessionEpoch, note_id: noteId, acked_at: intent.savedAt };
    try { localStorage.setItem(PENDING_MOOD_ACK_KEY, JSON.stringify(ack)); } catch { /* Storage may be unavailable. */ }
  }
}

export function clearPendingMood(): void {
  remove();
  try { localStorage.removeItem(PENDING_MOOD_ACK_KEY); } catch { /* Storage may be unavailable. */ }
}
