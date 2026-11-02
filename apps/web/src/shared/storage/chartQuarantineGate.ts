import { currentSessionEpoch } from "../session/sessionIdentity";

/**
 * Pending birth-correction quarantine (US-23, Codex r59), kept in sessionStorage so a reload
 * restores it before any chart-derived read. Holds only the opaque profile revision, a deadline
 * and the session epoch: no date and no chart content.
 */
export const CHART_QUARANTINE_KEY = "la-lanh-chart-quarantine-v1";

export type PendingChartQuarantine = { revision: string; deadline: number; epoch: string | null };

let pending: PendingChartQuarantine | null | undefined;
let waiters: Array<() => void> = [];

function attempt<T>(action: () => T): T | undefined {
  try {
    return action();
  } catch {
    return undefined;
  }
}

/** The quarantine in force for the current session, restored from sessionStorage on first use. */
export function pendingChartQuarantine(): PendingChartQuarantine | null {
  if (pending === undefined) {
    const stored = attempt(() => JSON.parse(sessionStorage.getItem(CHART_QUARANTINE_KEY) ?? "null") as unknown) as
      PendingChartQuarantine | null | undefined;
    pending = stored && typeof stored.revision === "string" && typeof stored.deadline === "number"
      ? stored : null;
  }
  if (pending && pending.epoch !== currentSessionEpoch()) setPendingChartQuarantine(null);
  return pending;
}

export function setPendingChartQuarantine(next: PendingChartQuarantine | null): void {
  pending = next;
  attempt(() => next
    ? sessionStorage.setItem(CHART_QUARANTINE_KEY, JSON.stringify(next))
    : sessionStorage.removeItem(CHART_QUARANTINE_KEY));
  if (!next) {
    const released = waiters;
    waiters = [];
    released.forEach((release) => release());
  }
}

// Reads whose answer is the current chart's derived content (saved notes and share links survive
// a correction on the server, D2, so they stay readable).
const DERIVED_READS = ["/daily-note", "/insights/", "/birth-profile/supplement", "/radar/", "/matching/", "/public/radar/current"];
// Codex r60: the receipt is the recipient's chart-derived pair result. Codex r61: the profile itself
// carries the birth date and its calculation; only the reconciliation read passes, through the
// explicit `bypassChartQuarantine` request option (never by path).
const EXACT_DERIVED_READS = new Set(["/public/radar/receipt", "/birth-profile"]);

export function isChartDerivedRead(path: string, method = "GET"): boolean {
  if (method !== "GET") return false;
  return EXACT_DERIVED_READS.has(path.split("?")[0]) || DERIVED_READS.some((prefix) => path.startsWith(prefix));
}

/** Hold a derived read while the outcome is unknown: the page keeps its own loading state. */
export function awaitChartRelease(signal?: AbortSignal | null): Promise<void> | null {
  // No promise when nothing is pending, so ordinary reads keep their synchronous start.
  if (!pendingChartQuarantine()) return null;
  return new Promise((resolve, reject) => {
    const aborted = () => {
      waiters = waiters.filter((waiter) => waiter !== release);
      reject(signal?.reason instanceof Error ? signal.reason : new DOMException("Request cancelled", "AbortError"));
    };
    const release = () => {
      signal?.removeEventListener("abort", aborted);
      resolve();
    };
    if (signal?.aborted) return aborted();
    signal?.addEventListener("abort", aborted, { once: true });
    waiters.push(release);
  });
}
