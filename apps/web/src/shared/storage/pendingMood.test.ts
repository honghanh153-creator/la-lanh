import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SESSION_EPOCH_KEY } from "../session/sessionIdentity";
import { keepPendingMood, PENDING_MOOD_KEY, PENDING_MOOD_TTL_MS, takePendingMood } from "./pendingMood";

const isMood = (value: unknown): value is "calm" | "tired" => value === "calm" || value === "tired";

describe("pending mood retry (P04)", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-22T08:00:00Z"));
  });
  afterEach(() => vi.useRealTimers());

  it("replays the mood once for the same session and note within the TTL", () => {
    keepPendingMood("note-a", "calm");
    const stored = JSON.parse(localStorage.getItem(PENDING_MOOD_KEY) ?? "{}") as Record<string, unknown>;
    expect(Object.keys(stored).sort()).toEqual(["mood", "note_id", "saved_at", "session_epoch"]);
    vi.advanceTimersByTime(PENDING_MOOD_TTL_MS - 1);
    expect(takePendingMood("note-a", isMood)).toBe("calm");
    expect(localStorage.getItem(PENDING_MOOD_KEY)).toBeNull();
    expect(takePendingMood("note-a", isMood)).toBeNull();
  });

  it("discards an expired mood instead of keeping it", () => {
    keepPendingMood("note-a", "calm");
    vi.advanceTimersByTime(PENDING_MOOD_TTL_MS);
    expect(takePendingMood("note-a", isMood)).toBeNull();
    expect(localStorage.getItem(PENDING_MOOD_KEY)).toBeNull();
  });

  it("discards a mood for another note or another session", () => {
    keepPendingMood("note-a", "calm");
    expect(takePendingMood("note-b", isMood)).toBeNull();
    expect(localStorage.getItem(PENDING_MOOD_KEY)).toBeNull();

    keepPendingMood("note-a", "tired");
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-b");
    expect(takePendingMood("note-a", isMood)).toBeNull();
    expect(localStorage.getItem(PENDING_MOOD_KEY)).toBeNull();
  });

  it("discards the old untimed format and malformed entries", () => {
    localStorage.setItem(PENDING_MOOD_KEY, JSON.stringify({ note_id: "note-a", mood: "calm" }));
    expect(takePendingMood("note-a", isMood)).toBeNull();
    expect(localStorage.getItem(PENDING_MOOD_KEY)).toBeNull();
    localStorage.setItem(PENDING_MOOD_KEY, "{not json");
    expect(takePendingMood("note-a", isMood)).toBeNull();
    expect(localStorage.getItem(PENDING_MOOD_KEY)).toBeNull();
  });

  it("does not keep a mood without a session", () => {
    sessionStorage.clear();
    keepPendingMood("note-a", "calm");
    expect(localStorage.getItem(PENDING_MOOD_KEY)).toBeNull();
  });
});
