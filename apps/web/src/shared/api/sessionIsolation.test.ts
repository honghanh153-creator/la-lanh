import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { getDailyNote, getSession, SESSION_EPOCH_KEY, type DailyNote } from "./client";
import { clearCachedDailyNote, readCachedDailyNote, writeCachedDailyNote } from "../storage/noteCache";
import { testLocks } from "../session/testLocks";

const note = {
  id: "00000000-0000-4000-8000-000000000001", note_date: "2026-10-09",
  title: "Synthetic guest A only", body: "Synthetic fixture.", full_body: "Synthetic fixture.",
  context_label: "Test", content_version: "test", persona_mode: "aura", persona_label: "Chắc",
  persona_version: "test", source_level: "natal_chart", astrology_source_version: "test",
  fallback_used: false, fallback_reason: null, created_at: "2026-10-09T00:00:00Z",
  awakening: null, sky_chapter: null,
} satisfies DailyNote;

function session(epoch: string) {
  return new Response(JSON.stringify({ state: "active", onboarding_status: "completed",
    expires_at: "2026-11-09T00:00:00Z", session_epoch: epoch }), { status: 200 });
}

beforeEach(() => {
  vi.stubGlobal("navigator", Object.create(navigator, { locks: { value: testLocks(), configurable: true } }));
  localStorage.clear(); sessionStorage.clear(); clearCachedDailyNote();
});
afterEach(() => {
  vi.restoreAllMocks(); clearCachedDailyNote();
  vi.unstubAllGlobals();
  document.cookie = "la_lanh_csrf=; max-age=0; path=/";
});

it("discards A's fallback, owner claim marker and pending draft when the server resumes B", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  sessionStorage.setItem("la-lanh-owner-session-epoch", "epoch-a");
  sessionStorage.setItem("la-lanh-radar-pending", "private draft A");
  writeCachedDailyNote(note);
  vi.spyOn(globalThis, "fetch").mockResolvedValue(session("epoch-b"));
  await getSession();
  expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBe("epoch-b");
  expect(readCachedDailyNote()).toBeNull();
  expect(sessionStorage.getItem("la-lanh-owner-session-epoch")).toBeNull();
  expect(sessionStorage.getItem("la-lanh-radar-pending")).toBeNull();
});

it("retains same-session offline fallback", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  writeCachedDailyNote(note);
  vi.spyOn(globalThis, "fetch").mockResolvedValue(session("epoch-a"));
  await getSession();
  expect(readCachedDailyNote()?.note.id).toBe(note.id);
});

it("rejects A's delayed response even if fetch ignores abort after B is accepted", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  let finish: (response: Response) => void = () => { throw new Error("Request did not start"); };
  vi.spyOn(globalThis, "fetch")
    .mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }))
    .mockResolvedValueOnce(session("epoch-b"));
  const pending = getDailyNote();
  const rejected = expect(pending).rejects.toMatchObject({ name: "AbortError" });
  await getSession();
  finish(new Response(JSON.stringify(note), { status: 200 }));
  await rejected;
  expect(readCachedDailyNote()).toBeNull();
});

it("refuses cached A data when session storage changes without going through getSession", () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  writeCachedDailyNote(note);
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-b");
  expect(readCachedDailyNote()).toBeNull();
});

it("rejects a response if another tab changed the cookie during the request", async () => {
  document.cookie = "la_lanh_csrf=synthetic-a; path=/";
  vi.spyOn(globalThis, "fetch").mockImplementation(() => {
    document.cookie = "la_lanh_csrf=synthetic-b; path=/";
    return Promise.resolve(new Response(JSON.stringify(note), { status: 200 }));
  });
  await expect(getDailyNote()).rejects.toMatchObject({ code: "SESSION_CHANGED" });
  document.cookie = "la_lanh_csrf=; max-age=0; path=/";
});

it("does not send a personal request after the verified cookie has changed", async () => {
  document.cookie = "la_lanh_csrf=synthetic-a; path=/";
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => Promise.resolve(session("epoch-a")));
  await getSession();
  writeCachedDailyNote(note);
  document.cookie = "la_lanh_csrf=synthetic-b; path=/";
  expect(readCachedDailyNote()).toBeNull();
  await expect(getDailyNote()).rejects.toMatchObject({ code: "SESSION_CHANGED" });
  expect(fetchMock).toHaveBeenCalledTimes(2); // status + explicit renewal, no personal request
});
