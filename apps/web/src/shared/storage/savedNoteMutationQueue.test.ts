import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearSavedNoteMutationQueue,
  enqueueSavedNoteMutation,
  flushSavedNoteMutations,
  readSavedNoteMutationQueue,
} from "./savedNoteMutationQueue";

describe("saved note mutation queue", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("keeps only the last intent for one session, note and revision", () => {
    enqueueSavedNoteMutation({
      sessionEpoch: "epoch-a",
      dailyNoteId: "note-a",
      revisionId: "revision-a",
      intent: "save",
    });
    enqueueSavedNoteMutation({
      sessionEpoch: "epoch-a",
      dailyNoteId: "note-a",
      revisionId: "revision-a",
      intent: "unsave",
    });

    expect(readSavedNoteMutationQueue()).toMatchObject([
      {
        session_epoch: "epoch-a",
        daily_note_id: "note-a",
        revision_id: "revision-a",
        intent: "unsave",
      },
    ]);
    const persisted = localStorage.getItem("la-lanh-saved-note-mutations-v1") ?? "";
    expect(persisted).not.toContain("title");
    expect(persisted).not.toContain("body");
    expect(persisted).not.toContain("reading");
  });

  it("never replays an intent from an old guest session epoch", async () => {
    enqueueSavedNoteMutation({
      sessionEpoch: "old-epoch",
      dailyNoteId: "note-a",
      revisionId: "revision-a",
      intent: "save",
    });
    const apply = vi.fn().mockResolvedValue(undefined);

    await flushSavedNoteMutations("new-epoch", apply);

    expect(apply).not.toHaveBeenCalled();
    expect(readSavedNoteMutationQueue()).toEqual([]);
  });

  it("replays current-session intents once and removes only successful work", async () => {
    enqueueSavedNoteMutation({
      sessionEpoch: "epoch-a",
      dailyNoteId: "note-a",
      revisionId: "revision-a",
      intent: "save",
    });
    enqueueSavedNoteMutation({
      sessionEpoch: "epoch-a",
      dailyNoteId: "note-b",
      revisionId: null,
      intent: "unsave",
    });
    const apply = vi.fn()
      .mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce(new Error("still offline"));

    await flushSavedNoteMutations("epoch-a", apply);

    expect(apply).toHaveBeenCalledTimes(2);
    expect(readSavedNoteMutationQueue()).toHaveLength(1);
    expect(readSavedNoteMutationQueue()[0]?.daily_note_id).toBe("note-b");
  });

  it("clears every pending intent during personal-data deletion", () => {
    enqueueSavedNoteMutation({
      sessionEpoch: "epoch-a",
      dailyNoteId: "note-a",
      revisionId: "revision-a",
      intent: "save",
    });

    clearSavedNoteMutationQueue();

    expect(readSavedNoteMutationQueue()).toEqual([]);
  });
});
