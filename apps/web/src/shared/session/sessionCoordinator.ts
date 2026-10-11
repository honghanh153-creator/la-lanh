const LOCK_NAME = "la-lanh-session-cookie-v1";

export class SessionCoordinationUnavailable extends Error {
  readonly name = "SessionCoordinationUnavailable";
}

export function sessionCoordinationAvailable(): boolean {
  return typeof navigator.locks?.request === "function";
}

export async function coordinateSession<T>(
  mode: LockMode,
  signal: AbortSignal | null | undefined,
  work: () => Promise<T>,
  readOnlyWithoutLocks = false,
): Promise<T> {
  signal?.throwIfAborted();
  if (!sessionCoordinationAvailable()) {
    if (readOnlyWithoutLocks) return work();
    // A per-tab mutex cannot order cookies with another tab. Do not pretend it
    // is safe, including on a native webview without a verified coordinator.
    throw new SessionCoordinationUnavailable("Browser-wide session ordering is unavailable");
  }
  return navigator.locks.request(LOCK_NAME, { mode, ...(signal ? { signal } : {}) }, async () => {
    signal?.throwIfAborted();
    // Cancellation only drops a queued lock. Once dispatched, the work must
    // drain its response before release; aborting fetch can leave late cookies.
    return work();
  });
}
