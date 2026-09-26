import type { DailyNote, ReadingProjection } from "../api/client";

const NOTE_CACHE_TTL_MS = 36 * 60 * 60 * 1000;

type CachedNote = {
  note: DailyNote;
  expires_at: string;
};

// Daily notes may include private transit-to-natal interpretations. Keep the
// fallback in memory only so it cannot survive a guest/session change on a
// shared device. Saved/share flows use their own sanitized projections.
let memoryCache: CachedNote | null = null;
const dismissedReadingUpdates = new Set<string>();

export type ReadingCacheIdentity = {
  scopeKey: string;
  revisionId: string;
};

export function readCachedDailyNote(identity?: ReadingCacheIdentity): CachedNote | null {
  if (!memoryCache) return null;
  if (new Date(memoryCache.expires_at).getTime() <= Date.now()) {
    memoryCache = null;
    return null;
  }
  if (identity) {
    const projection = memoryCache.note.reading_projection;
    if (
      projection?.scope_key !== identity.scopeKey
      || projection.active.revision_id !== identity.revisionId
    ) return null;
  }
  return memoryCache;
}

export function writeCachedDailyNote(note: DailyNote): void {
  memoryCache = {
    note,
    expires_at: new Date(Date.now() + NOTE_CACHE_TTL_MS).toISOString(),
  };
}

export function replaceCachedReadingProjection(projection: ReadingProjection): boolean {
  if (!memoryCache || memoryCache.note.reading_projection?.scope_key !== projection.scope_key) {
    return false;
  }
  memoryCache = {
    ...memoryCache,
    note: {
      ...memoryCache.note,
      reading_projection: { ...projection, available_update: null },
    },
  };
  return true;
}

function readingUpdateKey(scopeKey: string, revisionId: string): string {
  return `${scopeKey}:${revisionId}`;
}

export function dismissReadingUpdate(scopeKey: string, revisionId: string): void {
  dismissedReadingUpdates.add(readingUpdateKey(scopeKey, revisionId));
}

export function isReadingUpdateDismissed(scopeKey: string, revisionId: string): boolean {
  return dismissedReadingUpdates.has(readingUpdateKey(scopeKey, revisionId));
}

export function clearCachedDailyNote(): void {
  memoryCache = null;
  dismissedReadingUpdates.clear();
  // Remove legacy plaintext caches from builds before Aura Awakening.
  localStorage.removeItem("la-lanh-daily-note-cache-v1");
}
