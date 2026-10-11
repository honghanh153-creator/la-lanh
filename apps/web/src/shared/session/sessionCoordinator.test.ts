import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { createGuest, getHealth, requestGoogleLogin, restoreAccount, SESSION_EPOCH_KEY, type GuestSession } from "../api/client";
import { testLocks } from "./testLocks";

function deferred<T>() {
  let resolve: (value: T) => void = () => { throw new Error("not initialized"); };
  const promise = new Promise<T>((finish) => { resolve = finish; });
  return { promise, resolve };
}
const session = { state: "active", onboarding_status: "completed", expires_at: "2026-11-09T00:00:00Z", session_epoch: "epoch-b", resumed: true } satisfies GuestSession;
const signed = () => new Response(JSON.stringify({ status: "signed_in", session }));

beforeEach(() => {
  sessionStorage.clear(); localStorage.clear();
  document.cookie = "la_lanh_csrf=; Max-Age=0; path=/";
  vi.stubGlobal("navigator", Object.create(navigator, { locks: { value: testLocks(), configurable: true } }));
});
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it("holds identity/challenge ordering through body consumption and epoch adoption", async () => {
  const body = deferred<string>();
  const started = deferred<void>();
  const response = new Response();
  vi.spyOn(response, "json").mockImplementation(async () => { started.resolve(); return JSON.parse(await body.promise) as unknown; });
  const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response)
    .mockImplementationOnce(() => {
      expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBe("epoch-b");
      return Promise.resolve(new Response(JSON.stringify({ authorize_url: "https://synthetic.invalid", expires_at: session.expires_at })));
    });
  const restore = restoreAccount("synthetic-proof");
  await started.promise;
  const challenge = requestGoogleLogin();
  const staleChallenge = expect(challenge).rejects.toMatchObject({ code: "SESSION_CHANGED" });
  await Promise.resolve();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  body.resolve(JSON.stringify({ status: "signed_in", session }));
  await restore;
  await staleChallenge;
  expect(fetchMock).toHaveBeenCalledTimes(1);
  await requestGoogleLogin();
  expect(fetchMock).toHaveBeenCalledTimes(2);
});

it("cancelled cookie creation drains before restore and never adopts the abandoned owner", async () => {
  const response = deferred<Response>();
  const started = deferred<void>();
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => { started.resolve(); return response.promise; })
    .mockResolvedValueOnce(signed());
  const caller = new AbortController();
  const creation = createGuest("synthetic-creation-key-123456", caller.signal);
  const rejected = expect(creation).rejects.toMatchObject({ name: "AbortError" });
  await started.promise;
  caller.abort();
  const restore = restoreAccount("synthetic-proof");
  await Promise.resolve();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock.mock.calls[0]?.[1]?.signal?.aborted).toBe(false);
  response.resolve(new Response(JSON.stringify({ ...session, session_epoch: "abandoned-a" })));
  await rejected;
  await restore;
  expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBe("epoch-b");
});

it("ordinary timeout releases a shared read even if the transport ignores abort", async () => {
  vi.useFakeTimers();
  const started = deferred<void>();
  const hung = deferred<Response>();
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => { started.resolve(); return hung.promise; })
    .mockResolvedValueOnce(signed());
  const health = getHealth();
  const rejected = expect(health).rejects.toMatchObject({ name: "TimeoutError" });
  await started.promise;
  await vi.advanceTimersByTimeAsync(15_000);
  await rejected;
  expect(fetchMock.mock.calls[0]?.[1]?.signal?.aborted).toBe(true);
  await restoreAccount("synthetic-proof");
  hung.resolve(new Response("{}"));
});

it("cookie timeout holds the fence until drain, rejects adoption, then permits restore", async () => {
  vi.useFakeTimers();
  const started = deferred<void>();
  const response = deferred<Response>();
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => { started.resolve(); return response.promise; })
    .mockResolvedValueOnce(signed());
  const creation = createGuest("synthetic-creation-key-123456");
  const rejected = expect(creation).rejects.toMatchObject({ name: "TimeoutError" });
  await started.promise;
  await vi.advanceTimersByTimeAsync(15_000);
  const restore = restoreAccount("synthetic-proof");
  await Promise.resolve();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBeNull();
  expect(fetchMock.mock.calls[0]?.[1]?.signal?.aborted).toBe(false);
  response.resolve(new Response(JSON.stringify({ ...session, session_epoch: "abandoned-a" })));
  await rejected;
  await restore;
});

it("without Web Locks refuses identity issuance before any transport", async () => {
  vi.stubGlobal("navigator", Object.create(navigator, { locks: { value: undefined } }));
  const fetchMock = vi.spyOn(globalThis, "fetch");
  await expect(createGuest("synthetic-creation-key-123456")).rejects.toMatchObject({ name: "SessionCoordinationUnavailable" });
  expect(fetchMock).not.toHaveBeenCalled();
});
