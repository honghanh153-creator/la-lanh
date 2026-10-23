import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearSavedNoteMutationQueue,
  enqueueSavedNoteMutation,
  flushSavedNoteMutations,
  dropQueuedSaves,
  readSavedNoteMutationQueue,
  retireSupersededIntents,
  SAVED_INTENT_TTL_MS,
} from "./savedNoteMutationQueue";
import { invalidateSessionRequests, SESSION_EPOCH_KEY } from "../session/sessionIdentity";

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

  it("drops save intents after 24 h and unsave intents after 30 days (P04)", () => {
    vi.useFakeTimers();
    try {
      vi.setSystemTime(new Date("2026-10-22T08:00:00Z"));
      enqueueSavedNoteMutation({ sessionEpoch: "epoch-a", dailyNoteId: "note-save", intent: "save" });
      enqueueSavedNoteMutation({ sessionEpoch: "epoch-a", dailyNoteId: "note-unsave", intent: "unsave" });

      vi.advanceTimersByTime(SAVED_INTENT_TTL_MS.save - 1);
      expect(readSavedNoteMutationQueue().map((item) => item.daily_note_id)).toEqual(["note-save", "note-unsave"]);
      vi.advanceTimersByTime(1);
      expect(readSavedNoteMutationQueue().map((item) => item.daily_note_id)).toEqual(["note-unsave"]);

      vi.advanceTimersByTime(SAVED_INTENT_TTL_MS.unsave - SAVED_INTENT_TTL_MS.save);
      expect(readSavedNoteMutationQueue()).toEqual([]);
      expect(localStorage.getItem("la-lanh-saved-note-mutations-v1")).toBe("[]");
    } finally {
      vi.useRealTimers();
    }
  });

  it("drops intents with an unreadable or future timestamp", () => {
    localStorage.setItem("la-lanh-saved-note-mutations-v1", JSON.stringify([
      { session_epoch: "e", daily_note_id: "n1", revision_id: null, intent: "unsave", updated_at: "not a date" },
      { session_epoch: "e", daily_note_id: "n2", revision_id: null, intent: "unsave", updated_at: "2999-01-01T00:00:00Z" },
    ]));
    expect(readSavedNoteMutationQueue()).toEqual([]);
  });

  it("does not send an intent that expires while an earlier acknowledgement is pending (P04)", async () => {
    let now = Date.parse("2026-10-22T00:00:00Z");
    vi.spyOn(Date, "now").mockImplementation(() => now);
    const stamp = new Date(now).toISOString();
    localStorage.setItem("la-lanh-saved-note-mutations-v1", JSON.stringify(["first", "second"].map((id) => (
      { session_epoch: "epoch-a", daily_note_id: id, revision_id: null, intent: "save", updated_at: stamp }
    ))));
    let done!: () => void;
    const apply = vi.fn()
      .mockImplementationOnce(() => new Promise<void>((resolve) => { done = resolve; }))
      .mockResolvedValue(undefined);
    const flushing = flushSavedNoteMutations("epoch-a", apply);
    expect(apply).toHaveBeenCalledTimes(1);
    now += SAVED_INTENT_TTL_MS.save;
    done();
    await flushing;
    expect(apply).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem("la-lanh-saved-note-mutations-v1")).toBe("[]");
  });

  it("stops sending when the session changes while an earlier send is pending (P04)", async () => {
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
    enqueueSavedNoteMutation({ sessionEpoch: "epoch-a", dailyNoteId: "first", intent: "save" });
    enqueueSavedNoteMutation({ sessionEpoch: "epoch-a", dailyNoteId: "second", intent: "unsave" });
    let done!: () => void;
    const apply = vi.fn()
      .mockImplementationOnce(() => new Promise<void>((resolve) => { done = resolve; }))
      .mockResolvedValue(undefined);
    const flushing = flushSavedNoteMutations("epoch-a", apply);
    invalidateSessionRequests();
    done();
    await flushing;
    expect(apply).toHaveBeenCalledTimes(1);
  });

  it("history deletion drops queued saves but keeps queued unsave requests", () => {
    enqueueSavedNoteMutation({ sessionEpoch: "epoch-a", dailyNoteId: "saved", intent: "save" });
    enqueueSavedNoteMutation({ sessionEpoch: "epoch-a", dailyNoteId: "removed", intent: "unsave" });
    dropQueuedSaves();
    expect(readSavedNoteMutationQueue().map((item) => [item.daily_note_id, item.intent])).toEqual([["removed", "unsave"]]);
  });

  it("a direct ACK retires older intents for that note only, keeping newer and other-owner work", () => {
    vi.useFakeTimers();
    try {
      vi.setSystemTime(new Date("2026-10-22T08:00:00Z"));
      enqueueSavedNoteMutation({ sessionEpoch: "epoch-a", dailyNoteId: "note-a", revisionId: "r1", intent: "save" });
      enqueueSavedNoteMutation({ sessionEpoch: "epoch-b", dailyNoteId: "note-a", revisionId: "r1", intent: "save" });
      enqueueSavedNoteMutation({ sessionEpoch: "epoch-a", dailyNoteId: "note-b", revisionId: "r1", intent: "save" });
      const startedAt = Date.now();
      vi.advanceTimersByTime(1000);
      enqueueSavedNoteMutation({ sessionEpoch: "epoch-a", dailyNoteId: "note-a", revisionId: "r2", intent: "save" });
      retireSupersededIntents("epoch-a", "note-a", startedAt);
      expect(readSavedNoteMutationQueue().map((item) => [item.session_epoch, item.daily_note_id, item.revision_id]))
        .toEqual([["epoch-b", "note-a", "r1"], ["epoch-a", "note-b", "r1"], ["epoch-a", "note-a", "r2"]]);
    } finally {
      vi.useRealTimers();
    }
  });
});

