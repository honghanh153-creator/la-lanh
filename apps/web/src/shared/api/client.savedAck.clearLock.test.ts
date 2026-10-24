// Codex #48 @ 3e120f5: an ACK or failure callback that is waiting for the shared queue lock must
// not write the note id back after the device was cleared while it waited.
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { testLocks } from "../session/testLocks";

const QUEUE_LOCK = "la-lanh-saved-note-queue-v1";
const ACKS = "la-lanh-saved-note-acks-v1";
const QUEUE = "la-lanh-saved-note-mutations-v1";
const EPOCH = "la-lanh-session-epoch";

beforeEach(() => {
  vi.resetModules();
  localStorage.clear();
  sessionStorage.clear();
  sessionStorage.setItem(EPOCH, "epoch-synthetic");
  document.cookie = "la_lanh_csrf=synthetic; path=/";
  Object.defineProperty(navigator, "locks", { value: testLocks(), configurable: true });
  vi.spyOn(navigator, "onLine", "get").mockReturnValue(true);
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  document.cookie = "la_lanh_csrf=; Max-Age=0; path=/";
});

async function holdQueueLock() {
  let release!: () => void;
  let held!: () => void;
  const isHeld = new Promise<void>((resolve) => { held = resolve; });
  const blocker = navigator.locks.request(QUEUE_LOCK, async () => {
    held();
    await new Promise<void>((resolve) => { release = resolve; });
  });
  await isHeld;
  let waiting!: () => void;
  const callbackWaits = new Promise<void>((resolve) => { waiting = resolve; });
  const real = navigator.locks.request.bind(navigator.locks);
  vi.spyOn(navigator.locks, "request").mockImplementation(((...args: unknown[]) => {
    if (args[0] === QUEUE_LOCK) waiting();
    return Reflect.apply(real, navigator.locks, args) as unknown;
  }) as typeof navigator.locks.request);
  return { callbackWaits, release: async () => { release(); await blocker; } };
}

function wire(mode: "ack" | "failure") {
  vi.spyOn(globalThis, "fetch").mockImplementation(() => mode === "failure"
    ? Promise.reject(new TypeError("synthetic offline"))
    : Promise.resolve(new Response(JSON.stringify({ daily_note_id: "note-x" }), {
      status: 200, headers: { "Content-Type": "application/json" },
    })));
}

it.each(["ack", "failure"] as const)("a waiting %s cannot recreate storage after this tab cleared the device", async (mode) => {
  const client = await import("./client");
  const { clearPersonalDataOnDevice } = await import("../storage/clearPersonalData");
  const lock = await holdQueueLock();
  wire(mode);
  const call = client.saveDailyNote("note-x", "rev-x").catch((e: unknown) => e);
  await lock.callbackWaits; // owner already checked before the lock wait
  await clearPersonalDataOnDevice();
  expect(localStorage.getItem(ACKS)).toBeNull();
  expect(localStorage.getItem(QUEUE)).toBeNull();
  await lock.release();
  await call;
  expect(sessionStorage.getItem(EPOCH)).toBeNull();
  expect(localStorage.getItem(ACKS)).toBeNull();
  expect(localStorage.getItem(QUEUE)).toBeNull();
});

it.each(["ack", "failure"] as const)("a waiting %s stays fenced even when the same epoch comes back", async (mode) => {
  const client = await import("./client");
  const { clearPersonalDataOnDevice } = await import("../storage/clearPersonalData");
  const lock = await holdQueueLock();
  wire(mode);
  const call = client.saveDailyNote("note-x", "rev-x").catch((e: unknown) => e);
  await lock.callbackWaits;
  await clearPersonalDataOnDevice();
  sessionStorage.setItem(EPOCH, "epoch-synthetic"); // a clear that leaves the epoch unchanged
  await lock.release();
  await call;
  expect(localStorage.getItem(ACKS)).toBeNull();
  expect(localStorage.getItem(QUEUE)).toBeNull();
});

it.each(["ack", "failure"] as const)("a waiting %s stays fenced when another tab cleared the device", async (mode) => {
  const tabA = await import("./client");
  const lock = await holdQueueLock();
  wire(mode);
  const call = tabA.saveDailyNote("note-x", "rev-x").catch((e: unknown) => e);
  await lock.callbackWaits;
  vi.resetModules(); // tab B: its own module memory and session generation
  const tabB = await import("../storage/clearPersonalData");
  await tabB.clearPersonalDataOnDevice();
  sessionStorage.setItem(EPOCH, "epoch-synthetic"); // tab A keeps its own session storage
  await lock.release();
  await call;
  expect(localStorage.getItem(ACKS)).toBeNull();
  expect(localStorage.getItem(QUEUE)).toBeNull();
});
