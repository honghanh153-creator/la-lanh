import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  activateReadingProjection,
  claimOwner,
  createLaChungInvite,
  createShareArtifact,
  deleteGuest,
  getDailyNote,
  getHealth,
  isGuestSessionUnavailable,
  OWNER_SESSION_EPOCH_KEY,
  ownerClaimNeedsRefresh,
  saveDailyNote,
  SESSION_EPOCH_KEY,
} from "./client";
import { readSavedNoteMutationQueue } from "../storage/savedNoteMutationQueue";

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
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("classifies both missing and expired guest credentials as recoverable sessions", () => {
    expect(isGuestSessionUnavailable({ status: 401, code: "GUEST_SESSION_MISSING" })).toBe(true);
    expect(isGuestSessionUnavailable({ status: 401, code: "GUEST_EXPIRED" })).toBe(true);
    expect(isGuestSessionUnavailable({ status: 503, code: "READING_UNAVAILABLE" })).toBe(false);
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
  });

  it("does not bind an owner response to a guest session that changed in flight", async () => {
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
    let finishClaim: ((response: Response) => void) | undefined;
    vi.spyOn(globalThis, "fetch")
      .mockImplementationOnce(() => new Promise((resolve) => { finishClaim = resolve; }))
      .mockResolvedValueOnce(jsonResponse({
        principal_id: "00000000-0000-4000-8000-000000000031",
        expires_at: "2026-10-26T00:00:00Z",
        resumed: false,
      }));

    const oldSessionClaim = claimOwner();
    sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-b");
    finishClaim?.(jsonResponse({
      principal_id: "00000000-0000-4000-8000-000000000030",
      expires_at: "2026-10-26T00:00:00Z",
      resumed: false,
    }));
    await oldSessionClaim;

    expect(sessionStorage.getItem(OWNER_SESSION_EPOCH_KEY)).toBeNull();
    expect(ownerClaimNeedsRefresh()).toBe(true);

    await claimOwner();
    expect(sessionStorage.getItem(OWNER_SESSION_EPOCH_KEY)).toBe("epoch-b");
    expect(ownerClaimNeedsRefresh()).toBe(false);
  });
});
