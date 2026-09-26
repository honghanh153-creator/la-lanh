import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  activateReadingProjection,
  createShareArtifact,
  OWNER_SESSION_EPOCH_KEY,
  SESSION_EPOCH_KEY,
  type DailyNote,
} from "../api/client";
import { clearPersonalDataOnDevice } from "./clearPersonalData";
import {
  MATCHING_INTRO_SESSION_KEY,
  MATCHING_INTRO_STORAGE_KEY,
} from "./matchingIntroExposure";
import { readCachedDailyNote, writeCachedDailyNote } from "./noteCache";
import { enqueueSavedNoteMutation } from "./savedNoteMutationQueue";

describe("personal-data cleanup lifecycle", () => {
  const deleteCache = vi.fn<(cacheName: string) => Promise<boolean>>();

  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
    deleteCache.mockReset().mockResolvedValue(true);
    Object.defineProperty(window, "caches", {
      configurable: true,
      value: {
        keys: vi.fn().mockResolvedValue([
          "la-lanh-app-shell-v4",
          "unrelated-site-cache",
        ]),
        delete: deleteCache,
      },
    });
  });

  afterEach(() => {
    Reflect.deleteProperty(window, "caches");
  });

  it("removes aggregate guest data while preserving app-shell caches and preferences", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        scope_key: "a".repeat(64),
        active: { revision_id: "private-revision" },
        available_update: null,
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "share-a" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));
    await activateReadingProjection("a".repeat(64), "private-revision");
    writeCachedDailyNote({ id: "private-note" } as DailyNote);
    localStorage.setItem("la-lanh-daily-note-cache-v1", "private legacy note");
    localStorage.setItem("la-lanh-saved-notes-v1", "private saved notes");
    localStorage.setItem("la-lanh-pending-mood-v1", "private mood");
    localStorage.setItem("la-lanh-birth-supplement-snooze-until", "private snooze");
    localStorage.setItem("la-lanh-native-csrf-v1", "private csrf");
    localStorage.setItem("la-lanh-aura-transition-ack-v1:first", "1");
    localStorage.setItem("la-lanh-aura-transition-ack-v1:second", "1");
    localStorage.setItem("la-lanh-aura-transition-note", "keep this unrelated preference");
    localStorage.setItem("la-lanh-theme-v1", "dark");
    localStorage.setItem("la-lanh-install-dismissed", "true");
    localStorage.setItem(MATCHING_INTRO_STORAGE_KEY, JSON.stringify({ converted: false, visit: 2 }));
    sessionStorage.setItem("la-lanh-guest-create-key", "private guest key");
    sessionStorage.setItem(SESSION_EPOCH_KEY, "private epoch");
    sessionStorage.setItem(OWNER_SESSION_EPOCH_KEY, "private epoch");
    sessionStorage.setItem(MATCHING_INTRO_SESSION_KEY, "1");
    enqueueSavedNoteMutation({
      sessionEpoch: "private epoch",
      dailyNoteId: "private-note",
      revisionId: "private-revision",
      intent: "save",
    });

    await clearPersonalDataOnDevice();
    await createShareArtifact("new-note");

    expect(readCachedDailyNote()).toBeNull();
    expect(localStorage.getItem("la-lanh-daily-note-cache-v1")).toBeNull();
    expect(localStorage.getItem("la-lanh-saved-notes-v1")).toBeNull();
    expect(localStorage.getItem("la-lanh-saved-note-mutations-v1")).toBeNull();
    expect(localStorage.getItem("la-lanh-pending-mood-v1")).toBeNull();
    expect(localStorage.getItem("la-lanh-birth-supplement-snooze-until")).toBeNull();
    expect(localStorage.getItem("la-lanh-native-csrf-v1")).toBeNull();
    expect(localStorage.getItem("la-lanh-aura-transition-ack-v1:first")).toBeNull();
    expect(localStorage.getItem("la-lanh-aura-transition-ack-v1:second")).toBeNull();
    expect(localStorage.getItem(MATCHING_INTRO_STORAGE_KEY)).toBeNull();
    expect(sessionStorage.getItem("la-lanh-guest-create-key")).toBeNull();
    expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBeNull();
    expect(sessionStorage.getItem(OWNER_SESSION_EPOCH_KEY)).toBeNull();
    expect(sessionStorage.getItem(MATCHING_INTRO_SESSION_KEY)).toBeNull();

    expect(localStorage.getItem("la-lanh-theme-v1")).toBe("dark");
    expect(localStorage.getItem("la-lanh-install-dismissed")).toBe("true");
    expect(localStorage.getItem("la-lanh-aura-transition-note")).toBe(
      "keep this unrelated preference",
    );
    expect(deleteCache).not.toHaveBeenCalled();
    const shareBody = fetchMock.mock.calls[1]?.[1]?.body;
    if (typeof shareBody !== "string") throw new Error("Expected share request JSON body");
    expect(JSON.parse(shareBody)).toEqual({
      format: "story_9_16",
      revision_id: null,
    });
  });

  it("still clears the matching ladder when an earlier cleanup step fails", async () => {
    localStorage.setItem(MATCHING_INTRO_STORAGE_KEY, JSON.stringify({
      converted: false,
      visit: 2,
    }));
    sessionStorage.setItem(MATCHING_INTRO_SESSION_KEY, "1");
    const removedKeys: string[] = [];
    vi.spyOn(Storage.prototype, "removeItem").mockImplementation(function (
      key: string,
    ) {
      if (key === "la-lanh-daily-note-cache-v1") {
        throw new DOMException("blocked", "SecurityError");
      }
      removedKeys.push(key);
    });

    await expect(clearPersonalDataOnDevice()).rejects.toThrow();

    expect(removedKeys).toContain(MATCHING_INTRO_STORAGE_KEY);
    expect(removedKeys).toContain(MATCHING_INTRO_SESSION_KEY);
  });
});
