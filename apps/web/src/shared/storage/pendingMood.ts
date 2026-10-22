import { currentSessionEpoch } from "../session/sessionIdentity";

export const PENDING_MOOD_KEY = "la-lanh-pending-mood-v1";
// A mood belongs to one daily note, which leaves Home after 24 h (Daily auto-hide), so an
// offline check-in is only worth retrying for that long (audit 2026-10-22 P04).
export const PENDING_MOOD_TTL_MS = 24 * 60 * 60 * 1000;

type PendingMood<Mood extends string> = {
  session_epoch: string;
  note_id: string;
  mood: Mood;
  saved_at: number;
};

function remove(): void {
  try { localStorage.removeItem(PENDING_MOOD_KEY); } catch { /* Storage may be unavailable. */ }
}

export function keepPendingMood<Mood extends string>(noteId: string, mood: Mood): void {
  const sessionEpoch = currentSessionEpoch();
  if (!sessionEpoch) return;
  const pending: PendingMood<Mood> = { session_epoch: sessionEpoch, note_id: noteId, mood, saved_at: Date.now() };
  try { localStorage.setItem(PENDING_MOOD_KEY, JSON.stringify(pending)); } catch { /* Storage may be unavailable. */ }
}

/**
 * The mood to retry for this note, removing the stored entry either way: it is replayed only
 * for the same session and note within the TTL, and any other entry (older format, another
 * session or note, expired) is discarded rather than kept on the device.
 */
export function takePendingMood<Mood extends string>(noteId: string, valid: (value: unknown) => value is Mood): Mood | null {
  let raw: string | null;
  try { raw = localStorage.getItem(PENDING_MOOD_KEY); } catch { return null; }
  if (raw === null) return null;
  remove();
  try {
    const pending = JSON.parse(raw) as Partial<PendingMood<Mood>>;
    const age = Date.now() - Number(pending.saved_at);
    return pending.session_epoch === currentSessionEpoch()
      && pending.note_id === noteId
      && age >= 0 && age < PENDING_MOOD_TTL_MS
      && valid(pending.mood)
      ? pending.mood
      : null;
  } catch {
    return null;
  }
}

export function clearPendingMood(): void {
  remove();
}
