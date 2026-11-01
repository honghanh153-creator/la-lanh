// Codex r58 (US-23): an unknown correction outcome keeps the old chart quarantined until it is
// resolved, not just cleared once. Synthetic data only.
import { QueryClient } from "@tanstack/react-query";
import { afterEach, expect, it, vi } from "vitest";

import { getBirthProfile, type BirthReveal, type DailyNote } from "../api/client";
import { chartQuarantined, endQuarantine, quarantineChartDerivedData } from "./clearChartDerivedData";
import { readCachedDailyNote, writeCachedDailyNote } from "./noteCache";

vi.mock("../api/client", async (original) => ({
  ...await original<typeof import("../api/client")>(),
  getBirthProfile: vi.fn(),
}));

const OLD = "2026-10-29T08:00:00Z";
const NEW = "2026-10-29T09:00:00Z";
const profile = (revision: string) => ({ profile_revision: revision }) as unknown as BirthReveal;
const note = { id: "synthetic-old-note", reading_projection: null } as unknown as DailyNote;

afterEach(() => {
  endQuarantine();
  vi.useRealTimers();
  vi.clearAllMocks();
});

it("withdraws old content fetched while the correction was still computing once it commits", async () => {
  vi.useFakeTimers();
  vi.mocked(getBirthProfile)
    .mockResolvedValueOnce(profile(OLD)) // still computing
    .mockRejectedValueOnce(new Error("offline")) // outcome still unknown
    .mockResolvedValue(profile(NEW)); // committed late
  const client = new QueryClient();
  await quarantineChartDerivedData(client, OLD, { intervalMs: 100, windowMs: 60_000 });
  // Home reopens before the commit and fetches the still-current old note.
  writeCachedDailyNote(note);
  client.setQueryData(["daily-note"], "synthetic old note");
  expect(readCachedDailyNote()).toBeNull(); // never enters the offline fallback

  await vi.advanceTimersByTimeAsync(100);
  await vi.advanceTimersByTimeAsync(100);
  expect(chartQuarantined()).toBe(true);
  expect(client.getQueryData(["daily-note"])).toBe("synthetic old note");

  await vi.advanceTimersByTimeAsync(100);
  await vi.waitFor(() => expect(chartQuarantined()).toBe(false));
  expect(client.getQueryData(["daily-note"])).toBeUndefined();
  expect(readCachedDailyNote()).toBeNull();
  client.clear();
});

it("keeps the quarantine while reads fail, even after the request deadline", async () => {
  vi.useFakeTimers();
  vi.mocked(getBirthProfile).mockRejectedValue(new Error("offline"));
  const client = new QueryClient();
  await quarantineChartDerivedData(client, OLD, { intervalMs: 100, windowMs: 0 });
  await vi.advanceTimersByTimeAsync(500);
  expect(chartQuarantined()).toBe(true);
  writeCachedDailyNote(note);
  expect(readCachedDailyNote()).toBeNull();
  client.clear();
});

it("ends after the deadline when the server still has the old revision", async () => {
  vi.useFakeTimers();
  vi.mocked(getBirthProfile).mockResolvedValue(profile(OLD));
  const client = new QueryClient();
  await quarantineChartDerivedData(client, OLD, { intervalMs: 100, windowMs: 250 });
  await vi.advanceTimersByTimeAsync(200);
  expect(chartQuarantined()).toBe(true);
  await vi.advanceTimersByTimeAsync(200);
  expect(chartQuarantined()).toBe(false);
  writeCachedDailyNote(note);
  expect(readCachedDailyNote()).not.toBeNull();
  client.clear();
});
