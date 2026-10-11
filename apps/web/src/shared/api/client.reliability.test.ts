import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  activateReadingProjection,
  claimOwner,
  createLaChungInvite,
  createShareArtifact,
  createRadarInvite,
  deleteRadarResult,
  deleteGuest,
  getDailyNote,
  getContentRewriteStatus,
  getHealth,
  getSession,
  verifyAccountCode,
  logoutAccount,
  isGuestSessionUnavailable,
  OWNER_SESSION_EPOCH_KEY,
  ownerClaimNeedsRefresh,
  saveDailyNote,
  setContentRewriteConsent,
  SESSION_EPOCH_KEY,
} from "./client";
import { readSavedNoteMutationQueue } from "../storage/savedNoteMutationQueue";
import { testLocks, testRequestUrl } from "../session/testLocks";

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function signalReason(signal: AbortSignal | null | undefined): Error {
  return signal?.reason instanceof Error
    ? signal.reason
    : new DOMException("Request aborted", "AbortError");
}

describe("API client reliability", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
    vi.stubGlobal("navigator", Object.create(navigator, { locks: { value: testLocks(), configurable: true } }));
    document.cookie = "la_lanh_csrf=; Max-Age=0; path=/";
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    document.cookie = "la_lanh_csrf=; Max-Age=0; path=/";
  });

  it("keeps the acknowledged Radar deletion independent of cookie renewal failures", async () => {
    document.cookie = "la_lanh_csrf=synthetic-csrf; path=/";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
      if (testRequestUrl(url).endsWith("/session/renew")) return Promise.resolve(new Response(null, { status: 503 }));
      return Promise.resolve(new Response(null, { status: 204 }));
    });
    await expect(deleteRadarResult("synthetic-result")).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(testRequestUrl(fetchMock.mock.calls[0][0])).toMatch(/\/radar\/results\/synthetic-result$/);
  });

  it("does not chain a hanging cookie refresh onto an acknowledged Radar creation", async () => {
    document.cookie = "la_lanh_csrf=synthetic-csrf; path=/";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((url) => {
      if (testRequestUrl(url).endsWith("/session/renew")) return new Promise(() => {});
      return Promise.resolve(jsonResponse({ id: "synthetic-invite" }));
    });
    await expect(createRadarInvite({ recipient_label: "An", context: "friend", voice: "straight_warm" }, "synthetic-retry-key-1234"))
      .resolves.toMatchObject({ id: "synthetic-invite" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const headers = fetchMock.mock.calls[0][1]?.headers as Record<string, string>;
    expect(headers["Idempotency-Key"]).toBe("synthetic-retry-key-1234");
  });

  it("classifies both missing and expired guest credentials as recoverable sessions", () => {
    expect(isGuestSessionUnavailable({ status: 401, code: "GUEST_SESSION_MISSING" })).toBe(true);
    expect(isGuestSessionUnavailable({ status: 401, code: "GUEST_EXPIRED" })).toBe(true);
    expect(isGuestSessionUnavailable({ status: 503, code: "READING_UNAVAILABLE" })).toBe(false);
  });

  it("accepts an expired-session problem without cookie writes but not a foreign session switch", async () => {
    document.cookie = "la_lanh_csrf=expired-csrf; path=/";
    vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => {
      return Promise.resolve(new Response(JSON.stringify({ code: "GUEST_EXPIRED" }), { status: 401 }));
    });
    await expect(getSession()).rejects.toMatchObject({ code: "GUEST_EXPIRED" });
    document.cookie = "la_lanh_csrf=old-person; path=/";
    vi.mocked(fetch).mockImplementationOnce(() => {
      document.cookie = "la_lanh_csrf=another-person; path=/";
      return Promise.resolve(new Response(JSON.stringify({ code: "GUEST_EXPIRED" }), { status: 401 }));
    });
    await expect(getSession()).rejects.toMatchObject({ code: "SESSION_CHANGED" });
  });

  it("rechecks a foreign session cookie installed while expiry JSON is decoding", async () => {
    document.cookie = "la_lanh_csrf=expired-csrf; path=/";
    let finish!: (value: { code: string }) => void;
    let started!: () => void;
    const decoding = new Promise<{ code: string }>((resolve) => { finish = resolve; });
    const decodingStarted = new Promise<void>((resolve) => { started = resolve; });
    const response = new Response(null, { status: 401 });
    vi.spyOn(response, "json").mockImplementation(() => { started(); return decoding; });
    vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => {
      document.cookie = "la_lanh_csrf=; Max-Age=0; path=/";
      return Promise.resolve(response);
    });
    const pending = getSession();
    const rejected = expect(pending).rejects.toMatchObject({ code: "SESSION_CHANGED" });
    await decodingStarted;
    document.cookie = "la_lanh_csrf=another-person; path=/";
    finish({ code: "GUEST_EXPIRED" });
    try { await rejected; }
    finally { document.cookie = "la_lanh_csrf=; Max-Age=0; path=/"; }
  });

  it("adopts only successful account cookie transitions and clears local data after logout ACK", async () => {
    sessionStorage.setItem(SESSION_EPOCH_KEY, "guest-a");
    document.cookie = "la_lanh_csrf=guest-a; path=/";
    vi.spyOn(globalThis, "fetch").mockImplementationOnce(() => {
      document.cookie = "la_lanh_csrf=account-device; path=/";
      return Promise.resolve(jsonResponse({ status: "signed_in", session: {
        state: "active", onboarding_status: "completed", resumed: true,
        expires_at: "2100-01-01T00:00:00Z", session_epoch: "account-b", csrf_token: "account-device",
      } }));
    });
    await verifyAccountCode("012345", "login-nonce");
    expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBe("account-b");
    vi.mocked(fetch).mockRejectedValueOnce(new TypeError("offline"));
    await expect(logoutAccount()).rejects.toThrow("offline");
    expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBe("account-b");
    vi.mocked(fetch).mockImplementationOnce(() => {
      document.cookie = "la_lanh_csrf=; Max-Age=0; path=/";
      return Promise.resolve(new Response(null, { status: 204 }));
    });
    await logoutAccount();
    expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBeNull();
  });

  it("uses a single API prefix and CSRF protection for rewrite consent", async () => {
    document.cookie = "la_lanh_csrf=synthetic-csrf; path=/";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((url, init) => {
      if (testRequestUrl(url).endsWith("/session/renew")) return Promise.resolve(jsonResponse({ state: "active" }));
      return Promise.resolve(init?.method
        ? new Response(null, { status: 204 })
        : jsonResponse({ enabled: true, consented: false, pilot_eligible: true }));
    });
    await getContentRewriteStatus();
    await setContentRewriteConsent(true);
    await setContentRewriteConsent(false);
    const consentCalls = fetchMock.mock.calls.filter(([url]) => !testRequestUrl(url).endsWith("/session/renew"));
    expect(consentCalls.map(([url]) => url)).toEqual([
      "/v1/session/content-rewrite-consent",
      "/v1/session/content-rewrite-consent",
      "/v1/session/content-rewrite-consent",
    ]);
    expect(consentCalls[1][1]).toMatchObject({
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": "synthetic-csrf" },
      body: JSON.stringify({ consent_version: "external-content-rewrite-v1", scope: "personal" }),
    });
    expect(consentCalls[2][1]).toMatchObject({
      method: "DELETE", headers: { "X-CSRF-Token": "synthetic-csrf" },
    });
    document.cookie = "la_lanh_csrf=; max-age=0; path=/";
  });

  it("sends the selected context with its explicit share revision", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResponse({ id: "share" }));
    await createShareArtifact("note", "story_9_16", "revision", "work");
    expect(fetchMock.mock.calls[0][1]?.body).toBe(JSON.stringify({
      format: "story_9_16", revision_id: "revision", background_lens: "work",
    }));
  });

  it("uses the newly activated revision for subsequent save and share payloads", async () => {
    const oldRevisionId = "00000000-0000-4000-8000-000000000010";
    const newRevisionId = "00000000-0000-4000-8000-000000000011";
    const scopeKey = "a".repeat(64);
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({
        id: "00000000-0000-4000-8000-000000000001",
        reading_projection: {
          scope_key: scopeKey,
          active: { revision_id: oldRevisionId },
          available_update: { revision_id: newRevisionId },
        },
      }))
      .mockResolvedValueOnce(jsonResponse({
        scope_key: scopeKey,
        active: { revision_id: newRevisionId },
        available_update: null,
      }))
      .mockResolvedValueOnce(jsonResponse({ daily_note_id: "note-a" }))
      .mockResolvedValueOnce(jsonResponse({ id: "share-a" }));

    await getDailyNote();
    await activateReadingProjection(scopeKey, newRevisionId);
    await saveDailyNote("note-a");
    await createShareArtifact("note-a");

    const saveBody = fetchMock.mock.calls[2]?.[1]?.body;
    const shareBody = fetchMock.mock.calls[3]?.[1]?.body;
    if (typeof saveBody !== "string" || typeof shareBody !== "string") {
      throw new Error("Expected save and share request JSON bodies");
    }
    expect(JSON.parse(saveBody)).toEqual({
      revision_id: newRevisionId,
    });
    expect(JSON.parse(shareBody)).toEqual({
      format: "story_9_16",
      revision_id: newRevisionId,
    });
  });

  it("aborts a request after 15 seconds and classifies the timeout as queueable connectivity loss", async () => {
    vi.useFakeTimers();
    sessionStorage.setItem("la-lanh-session-epoch", "epoch-a");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((_input, init) => (
      new Promise((_resolve, reject) => {
        expect(init?.signal).toBeInstanceOf(AbortSignal);
        init?.signal?.addEventListener("abort", () => reject(signalReason(init.signal)), { once: true });
      })
    ));

    const pendingSave = saveDailyNote("note-timeout", "revision-timeout");
    await Promise.resolve(); await Promise.resolve();
    expect(fetchMock.mock.calls[0]?.[1]?.signal).toBeInstanceOf(AbortSignal);
    const rejection = expect(pendingSave).rejects.toMatchObject({ name: "TimeoutError" });

    await vi.advanceTimersByTimeAsync(15_000);

    await rejection;
    expect(readSavedNoteMutationQueue()).toMatchObject([{
      session_epoch: "epoch-a",
      daily_note_id: "note-timeout",
      revision_id: "revision-timeout",
      intent: "save",
    }]);
  });

  it("shares the explicit displayed revision even when another request changed the active pointer", async () => {
    const displayedRevision = "00000000-0000-4000-8000-000000000020";
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({
        reading_projection: { scope_key: "a".repeat(64), active: { revision_id: "another-revision" } },
      }))
      .mockResolvedValueOnce(jsonResponse({ id: "share-a" }));
    await getDailyNote();
    await createShareArtifact("note-a", "square_1_1", displayedRevision);
    const body = fetchMock.mock.calls[1]?.[1]?.body;
    if (typeof body !== "string") throw new Error("Expected share request JSON");
    expect(JSON.parse(body)).toEqual({ format: "square_1_1", revision_id: displayedRevision });
  });

  it("composes caller cancellation with the request deadline", async () => {
    vi.useFakeTimers();
    const caller = new AbortController();
    vi.spyOn(globalThis, "fetch").mockImplementation((_input, init) => (
      new Promise((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(signalReason(init.signal)), { once: true });
      })
    ));

    const pendingHealth = getHealth(caller.signal);
    const rejection = expect(pendingHealth).rejects.toMatchObject({ name: "AbortError" });
    caller.abort(new DOMException("Caller cancelled", "AbortError"));

    await rejection;
    expect(vi.getTimerCount()).toBe(0);
  });

  it("allows privacy deletion to finish beyond the normal request deadline", async () => {
    vi.useFakeTimers();
    let finishRequest: ((response: Response) => void) | undefined;
    let requestSignal: AbortSignal | null | undefined;
    vi.spyOn(globalThis, "fetch").mockImplementation((_input, init) => {
      requestSignal = init?.signal;
      return new Promise((resolve) => { finishRequest = resolve; });
    });

    const deletion = deleteGuest();
    await vi.advanceTimersByTimeAsync(15_000);

    expect(requestSignal?.aborted).toBe(false);
    finishRequest?.(new Response(null, { status: 204 }));
    await deletion;
    expect(vi.getTimerCount()).toBe(0);
  });

  it("sends the owner-generated idempotency key when creating a Lá Chứng invite", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResponse({
      id: "00000000-0000-4000-8000-000000000020",
      recipient_label: "An",
      context: "bff",
      status: "pending",
      created_at: "2026-09-07T00:00:00Z",
      expires_at: "2026-09-14T00:00:00Z",
      share_url: "/la-chung/i/token",
    }));

    await createLaChungInvite({
      recipient_label: "An",
      context: "bff",
      idempotency_key: "invitekey1234567890",
    });

    const body = fetchMock.mock.calls[0]?.[1]?.body;
    if (typeof body !== "string") throw new Error("Expected invite request JSON body");
    expect(JSON.parse(body)).toEqual({
      recipient_label: "An",
      context: "bff",
      idempotency_key: "invitekey1234567890",
    });
  });

  it("refreshes the owner binding when the active guest session changes", async () => {
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-b");
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResponse({
      principal_id: "00000000-0000-4000-8000-000000000030",
      expires_at: "2026-10-26T00:00:00Z",
      resumed: false,
    }));

    expect(ownerClaimNeedsRefresh()).toBe(true);
    await claimOwner();

    expect(ownerClaimNeedsRefresh()).toBe(false);
    sessionStorage.setItem("la-lanh-owner-session-until-v1", "2020-01-01T00:00:00Z");
    expect(ownerClaimNeedsRefresh()).toBe(true);
  });

  it("does not bind an owner response to a guest session that changed in flight", async () => {
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
    let finishClaim: ((response: Response) => void) | undefined;
    let requestStarted: () => void = () => { throw new Error("Owner request not started"); };
    const started = new Promise<void>((resolve) => { requestStarted = resolve; });
    vi.spyOn(globalThis, "fetch")
      .mockImplementationOnce(() => new Promise((resolve) => { finishClaim = resolve; requestStarted(); }))
      .mockResolvedValueOnce(jsonResponse({
        principal_id: "00000000-0000-4000-8000-000000000031",
        expires_at: "2026-10-26T00:00:00Z",
        resumed: false,
      }));

    const oldSessionClaim = claimOwner();
    const rejected = expect(oldSessionClaim).rejects.toMatchObject({ name: "AbortError" });
    await started;
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-b");
    finishClaim?.(jsonResponse({
      principal_id: "00000000-0000-4000-8000-000000000030",
      expires_at: "2026-10-26T00:00:00Z",
      resumed: false,
    }));
    await rejected;

    expect(sessionStorage.getItem(OWNER_SESSION_EPOCH_KEY)).toBeNull();
    expect(ownerClaimNeedsRefresh()).toBe(true);

    await claimOwner();
    expect(sessionStorage.getItem(OWNER_SESSION_EPOCH_KEY)).toBe("epoch-b");
    expect(ownerClaimNeedsRefresh()).toBe(false);
  });
});
