import { QueryClient } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { chartDataRevision, clearChartDerivedData, withdrawCorrectedChart } from "./clearChartDerivedData";
import { readCachedDailyNote, writeCachedDailyNote } from "./noteCache";
import { readLocalSavedNotes, saveNoteLocally } from "./savedNoteCache";
import {
  enqueueSavedNoteMutation,
  flushSavedNoteMutations,
  readSavedNoteMutationQueue,
  type SavedNoteMutationIntent,
} from "./savedNoteMutationQueue";
import type { DailyNote } from "../api/client";

const EPOCH = "epoch-us23";
const note = { id: "old-note", reading_projection: null } as unknown as DailyNote;

function queueOfflineIntents(): void {
  // Offline before the correction: an unsave of a kept copy and a save of the old note.
  enqueueSavedNoteMutation({ sessionEpoch: EPOCH, dailyNoteId: "kept-copy", intent: "unsave" });
  enqueueSavedNoteMutation({ sessionEpoch: EPOCH, dailyNoteId: "old-note", intent: "save" });
}

describe("birth-date correction cache withdrawal (US-23)", () => {
  beforeEach(() => localStorage.clear());

  it("keeps queued unsaves, drops queued saves and the old chart, and refetches copies", async () => {
    const client = new QueryClient();
    queueOfflineIntents();
    saveNoteLocally(note);
    client.setQueryData(["birth-profile"], "old date");
    client.setQueryData(["daily-note"], "old note");
    client.setQueryData(["tarot-session", "independent"], "cards");
    client.setQueryData(["saved-notes"], ["kept copy"]);
    const before = chartDataRevision(client);
    const refetched = vi.spyOn(client, "invalidateQueries");

    await withdrawCorrectedChart(client);

    expect(chartDataRevision(client)).toBe(before + 1);
    expect(readSavedNoteMutationQueue().map((item) => [item.daily_note_id, item.intent])).toEqual([
      ["kept-copy", "unsave"],
    ]);
    expect(readLocalSavedNotes()).toEqual([]);
    expect(client.getQueryData(["birth-profile"])).toBeUndefined();
    expect(client.getQueryData(["daily-note"])).toBeUndefined();
    expect(client.getQueryData(["tarot-session", "independent"])).toBe("cards");
    // Retained copies are refreshed, not discarded.
    expect(client.getQueryData(["saved-notes"])).toEqual(["kept copy"]);
    expect(refetched).toHaveBeenCalled();
    client.clear();
  });

  it("delivers an offline unsave after the correction and a reload", async () => {
    const client = new QueryClient();
    queueOfflineIntents();
    await withdrawCorrectedChart(client);
    // Reload: the queue lives in localStorage; the next saved-list read flushes it.
    const sent: SavedNoteMutationIntent[] = [];
    await flushSavedNoteMutations(EPOCH, (intent) => { sent.push(intent); return Promise.resolve(); });
    expect(sent.map((intent) => [intent.daily_note_id, intent.intent])).toEqual([["kept-copy", "unsave"]]);
    expect(readSavedNoteMutationQueue()).toEqual([]);
    client.clear();
  });

  it("differs from the precision-removal withdrawal, which drops every intent", async () => {
    const client = new QueryClient();
    queueOfflineIntents();
    await clearChartDerivedData(client);
    expect(readSavedNoteMutationQueue()).toEqual([]);
    client.clear();
  });

  it("clears the cached Daily note of the old subject", async () => {
    writeCachedDailyNote(note);
    expect(readCachedDailyNote()).not.toBeNull();
    await withdrawCorrectedChart(new QueryClient());
    expect(readCachedDailyNote()).toBeNull();
  });
});
