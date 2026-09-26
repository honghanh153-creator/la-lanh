import type { DailyNote } from "../api/client";

const KEY = "la-lanh-saved-notes-v1";
const MAX_LOCAL_SAVED_NOTES = 30;
const LOCAL_SAVED_NOTE_TTL_MS = 30 * 24 * 60 * 60 * 1000;

function write(notes: LocalSavedNote[]): void {
  const serialized = JSON.stringify(notes.slice(0, MAX_LOCAL_SAVED_NOTES));
  if (localStorage.getItem(KEY) !== serialized) localStorage.setItem(KEY, serialized);
}

// This device cache is only a pending-sync marker. Reading prose stays in
// memory/server storage and cannot survive a guest change on a shared device.
export type LocalSavedNote = {
  daily_note_id: string;
  revision_id?: string;
  saved_at: string;
};

function sanitize(value: unknown): LocalSavedNote | null {
  if (!value || typeof value !== "object") return null;
  const item = value as Record<string, unknown>;
  if (typeof item.daily_note_id !== "string" || typeof item.saved_at !== "string") return null;
  const legacyNote = item.note as Record<string, unknown> | undefined;
  const revisionId = typeof item.revision_id === "string"
    ? item.revision_id
    : typeof legacyNote?.revision_id === "string"
      ? legacyNote.revision_id
      : undefined;
  return {
    daily_note_id: item.daily_note_id,
    saved_at: item.saved_at,
    ...(revisionId ? { revision_id: revisionId } : {}),
  };
}

export function readLocalSavedNotes(): LocalSavedNote[] {
  try {
    const cutoff = Date.now() - LOCAL_SAVED_NOTE_TTL_MS;
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? "[]") as unknown;
    const notes = (Array.isArray(parsed) ? parsed : [])
      .map(sanitize)
      .filter((item): item is LocalSavedNote => (
        item !== null && new Date(item.saved_at).getTime() > cutoff
      ));
    write(notes);
    return notes;
  } catch {
    localStorage.removeItem(KEY);
    return [];
  }
}

export function saveNoteLocally(note: DailyNote): void {
  const notes = readLocalSavedNotes().filter((item) => item.daily_note_id !== note.id);
  const revisionId = note.reading_projection?.active.revision_id;
  notes.unshift({
    daily_note_id: note.id,
    saved_at: new Date().toISOString(),
    ...(revisionId ? { revision_id: revisionId } : {}),
  });
  write(notes);
}

export function unsaveNoteLocally(noteId: string): void {
  write(readLocalSavedNotes().filter((item) => item.daily_note_id !== noteId));
}

export function clearLocalSavedNotes(): void {
  localStorage.removeItem(KEY);
}
