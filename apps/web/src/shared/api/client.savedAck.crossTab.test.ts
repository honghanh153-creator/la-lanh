// Codex #48 @ b417b76: two client module instances on one origin (like two tabs) share the queue
// in localStorage and the Web Locks manager, but not module memory. A late failure in tab A must
// not undo the choice tab B already had acknowledged.
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { testLocks } from "../session/testLocks";

beforeEach(() => {
  vi.resetModules();
  localStorage.clear();
  sessionStorage.clear();
  sessionStorage.setItem("la-lanh-session-epoch", "epoch-synthetic");
  document.cookie = "la_lanh_csrf=synthetic; path=/";
  Object.defineProperty(navigator, "locks", { value: testLocks(), configurable: true });
  vi.spyOn(navigator, "onLine", "get").mockReturnValue(true);
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  document.cookie = "la_lanh_csrf=; Max-Age=0; path=/";
});

function transport(methods: string[]) {
  let failFirst!: (error: Error) => void;
  let firstSent!: () => void;
  const sent = new Promise<void>((resolve) => { firstSent = resolve; });
  vi.spyOn(globalThis, "fetch").mockImplementation((_url, init) => {
    const method = init?.method ?? "GET";
    methods.push(method);
    if (methods.length === 1) {
      firstSent();
      return new Promise<Response>((_resolve, reject) => { failFirst = reject; });
    }
    return Promise.resolve(method === "DELETE"
      ? new Response(null, { status: 204 })
      : new Response(JSON.stringify(method === "PUT" ? { daily_note_id: "note-x" } : []), {
        status: 200, headers: { "Content-Type": "application/json" },
      }));
  });
  return { sent, fail: (error: Error) => failFirst(error) };
}

it.each([
  ["save", "unsave", "PUT", "DELETE"],
  ["unsave", "save", "DELETE", "PUT"],
] as const)("a late %s in tab A cannot undo the %s tab B had acknowledged", async (older, newer, first, second) => {
  const methods: string[] = [];
  const wire = transport(methods);
  const tabA = await import("./client");
  const pending = (older === "save" ? tabA.saveDailyNote : tabA.unsaveDailyNote)("note-x", "rev-x").catch((e: unknown) => e);
  await wire.sent;
  vi.resetModules(); // fresh module memory, same storage, cookie and lock manager
  const tabB = await import("./client");
  await (newer === "save" ? tabB.saveDailyNote : tabB.unsaveDailyNote)("note-x", "rev-x");
  wire.fail(new TypeError("synthetic transport failure"));
  await pending;
  await tabB.listSavedNotes();
  expect(methods).toEqual([first, second, "GET"]);
});

it("a lone failure in one tab is still retried by another tab", async () => {
  const methods: string[] = [];
  const wire = transport(methods);
  const tabA = await import("./client");
  const pending = tabA.saveDailyNote("note-x", "rev-x").catch((e: unknown) => e);
  await wire.sent;
  wire.fail(new TypeError("synthetic transport failure"));
  await pending;
  vi.resetModules();
  const tabB = await import("./client");
  await tabB.listSavedNotes();
  expect(methods).toEqual(["PUT", "PUT", "GET"]);
});
