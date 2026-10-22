import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { invalidateSessionRequests, SESSION_EPOCH_KEY } from "../session/sessionIdentity";
import {
  acknowledgePendingMood,
  captureMoodIntent,
  keepPendingMood,
  PENDING_MOOD_KEY,
  PENDING_MOOD_TTL_MS,
  prunePendingMood,
  takePendingMood,
} from "./pendingMood";

const isMood = (value: unknown): value is "calm" | "tired" => value === "calm" || value === "tired";
const stored = () => JSON.parse(localStorage.getItem(PENDING_MOOD_KEY) ?? "null") as Record<string, unknown> | null;

describe("pending mood retry (P04)", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-22T08:00:00Z"));
  });
  afterEach(() => vi.useRealTimers());

  it("replays the mood once for the same session and note within the first-capture deadline", () => {
    keepPendingMood("note-a", "calm", captureMoodIntent());
    expect(Object.keys(stored() ?? {}).sort()).toEqual(["mood", "note_id", "saved_at", "session_epoch"]);
    vi.advanceTimersByTime(PENDING_MOOD_TTL_MS - 1);
    expect(takePendingMood("note-a", isMood)?.mood).toBe("calm");
    expect(stored()).toBeNull();
    expect(takePendingMood("note-a", isMood)).toBeNull();
  });

  it("a failed retry keeps the original deadline and is dropped at it", () => {
    const first = captureMoodIntent();
    keepPendingMood("note-a", "calm", first);
    vi.advanceTimersByTime(23 * 60 * 60 * 1000);
    const retry = takePendingMood("note-a", isMood);
    expect(retry?.intent.savedAt).toBe(first.savedAt);
    keepPendingMood("note-a", "calm", retry!.intent); // the retry failed
    expect(stored()?.saved_at).toBe(first.savedAt);
    vi.advanceTimersByTime(60 * 60 * 1000);
    keepPendingMood("note-a", "calm", retry!.intent); // failing again past the deadline keeps nothing
    prunePendingMood();
    expect(stored()).toBeNull();
  });

  it("stores nothing for a callback that outlived its session or a device clear", () => {
    const intent = captureMoodIntent();
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-b");
    keepPendingMood("note-a", "calm", intent);
    expect(stored()).toBeNull();
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
    const before = captureMoodIntent();
    invalidateSessionRequests();
    keepPendingMood("note-a", "calm", before);
    expect(stored()).toBeNull();
  });

  it("an acknowledged choice clears an older waiting one but never a newer one", () => {
    const older = captureMoodIntent();
    keepPendingMood("note-a", "calm", older);
    vi.advanceTimersByTime(1000);
    acknowledgePendingMood("note-a", captureMoodIntent());
    expect(stored()).toBeNull();

    const ackedEarlier = captureMoodIntent();
    vi.advanceTimersByTime(1000);
    keepPendingMood("note-a", "tired", captureMoodIntent()); // newer choice failed
    acknowledgePendingMood("note-a", ackedEarlier); // an earlier request finishes late
    expect(stored()?.mood).toBe("tired");
  });

  it("an older failure arriving late does not overwrite a newer waiting choice", () => {
    const older = captureMoodIntent();
    vi.advanceTimersByTime(1000);
    keepPendingMood("note-a", "tired", captureMoodIntent());
    keepPendingMood("note-a", "calm", older);
    expect(stored()?.mood).toBe("tired");
  });

  it("prune removes expired, other-session and old-format entries without a network", () => {
    for (const entry of [
      { session_epoch: "epoch-a", note_id: "n", mood: "calm", saved_at: Date.now() - PENDING_MOOD_TTL_MS },
      { session_epoch: "epoch-b", note_id: "n", mood: "calm", saved_at: Date.now() },
      { note_id: "n", mood: "calm" },
    ]) {
      localStorage.setItem(PENDING_MOOD_KEY, JSON.stringify(entry));
      prunePendingMood();
      expect(stored()).toBeNull();
    }
    localStorage.setItem(PENDING_MOOD_KEY, "{not json");
    prunePendingMood();
    expect(localStorage.getItem(PENDING_MOOD_KEY)).toBeNull();
    keepPendingMood("n", "calm", captureMoodIntent());
    prunePendingMood();
    expect(stored()?.mood).toBe("calm"); // a live entry stays
  });

  it("does not keep a mood without a session", () => {
    sessionStorage.clear();
    keepPendingMood("note-a", "calm", captureMoodIntent());
    expect(stored()).toBeNull();
  });
});
