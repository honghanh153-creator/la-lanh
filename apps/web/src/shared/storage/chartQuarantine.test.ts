// Codex r58 (US-23): an unknown correction outcome keeps the old chart quarantined until it is
// resolved, not just cleared once. Synthetic data only.
import { QueryClient } from "@tanstack/react-query";
import { afterEach, expect, it, vi } from "vitest";

import { getBirthProfile, getDailyNote, SESSION_EPOCH_KEY, type BirthReveal, type DailyNote } from "../api/client";
import { CHART_QUARANTINE_KEY, isChartDerivedRead, pendingChartQuarantine } from "./chartQuarantineGate";
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

it("holds derived reads while quarantined and lets them through once resolved", async () => {
  vi.useFakeTimers();
  vi.mocked(getBirthProfile).mockResolvedValue(profile(OLD));
  const fetchMock = vi.fn(() => Promise.resolve(Response.json({ id: "synthetic-new-note", reading_projection: null })));
  vi.stubGlobal("fetch", fetchMock);
  const client = new QueryClient();
  await quarantineChartDerivedData(client, OLD, { intervalMs: 100, windowMs: 250 });
  expect(isChartDerivedRead("/daily-note?voice=roast")).toBe(true);
  expect(isChartDerivedRead("/birth-profile")).toBe(false);
  expect(isChartDerivedRead("/saved-notes")).toBe(false);

  let settled = false;
  const read = getDailyNote().then(() => { settled = true; });
  await vi.advanceTimersByTimeAsync(200);
  expect(settled).toBe(false); // the page stays in its loading state
  expect(fetchMock).not.toHaveBeenCalled();

  await vi.advanceTimersByTimeAsync(200); // same revision past the deadline: released
  await read;
  expect(fetchMock).toHaveBeenCalledTimes(1);
  vi.unstubAllGlobals();
  client.clear();
});

it("restores a pending quarantine after a reload before any derived read", async () => {
  vi.useFakeTimers();
  sessionStorage.setItem(SESSION_EPOCH_KEY, "synthetic-epoch");
  vi.mocked(getBirthProfile).mockRejectedValue(new Error("offline"));
  await quarantineChartDerivedData(new QueryClient(), OLD, { intervalMs: 100, windowMs: 60_000 });
  expect(sessionStorage.getItem(CHART_QUARANTINE_KEY)).toContain(OLD);

  // Reload: fresh module state, only sessionStorage survives.
  vi.resetModules();
  const gate = await import("./chartQuarantineGate");
  const reloaded = await import("./clearChartDerivedData");
  const cache = await import("./noteCache");
  const api = await import("../api/client");
  expect(gate.pendingChartQuarantine()?.revision).toBe(OLD);
  let released = false;
  void gate.awaitChartRelease()?.then(() => { released = true; });

  const client = new QueryClient();
  reloaded.resumeChartQuarantine(client, { intervalMs: 100 });
  cache.writeCachedDailyNote(note);
  expect(cache.readCachedDailyNote()).toBeNull();
  expect(reloaded.chartQuarantined()).toBe(true);

  vi.mocked(api.getBirthProfile).mockResolvedValue(profile(NEW)); // the change landed meanwhile
  client.setQueryData(["daily-note"], "synthetic old note");
  await vi.advanceTimersByTimeAsync(100);
  await vi.waitFor(() => expect(reloaded.chartQuarantined()).toBe(false));
  expect(client.getQueryData(["daily-note"])).toBeUndefined();
  expect(released).toBe(true);
  expect(sessionStorage.getItem(CHART_QUARANTINE_KEY)).toBeNull();
  sessionStorage.removeItem(SESSION_EPOCH_KEY);
  client.clear();
});

it("drops a stored quarantine that belongs to another session", async () => {
  sessionStorage.setItem(CHART_QUARANTINE_KEY, JSON.stringify({ revision: OLD, deadline: 0, epoch: "other" }));
  vi.resetModules();
  const gate = await import("./chartQuarantineGate");
  expect(gate.pendingChartQuarantine()).toBeNull();
  expect(pendingChartQuarantine()).toBeNull();
  expect(sessionStorage.getItem(CHART_QUARANTINE_KEY)).toBeNull();
});
