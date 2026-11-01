import type { QueryClient } from "@tanstack/react-query";

import { BIRTH_CORRECTION_TIMEOUT_MS, clearActiveDailyReading, getBirthProfile } from "../api/client";
import { currentSessionEpoch, sessionGeneration } from "../session/sessionIdentity";
import { pendingChartQuarantine, setPendingChartQuarantine } from "./chartQuarantineGate";
import { clearCachedDailyNote, suspendDailyNoteCacheWrites } from "./noteCache";
import { clearLocalSavedNotes } from "./savedNoteCache";
import { clearSavedNoteMutationQueue, dropQueuedSaves } from "./savedNoteMutationQueue";

const CHART_DERIVED_KEYS = new Set([
  "birth-profile", "birth-supplement", "birth-supplement-edit", "daily-note", "daily-note-context",
  "daily-note-mood", "daily-experiment", "insight-overview", "private-reading",
  "saved-notes", "share-artifact", "share-links", "radar-invites", "radar-result",
  "radar-receipt", "radar-received", "radar-received-result", "current-radar", "matching-readiness",
  "daily-note-resonance",
]);

const chartRevisions = new WeakMap<QueryClient, number>();

/** Pending mutation callbacks must not recreate data cleared by a precision edit. */
export function chartDataRevision(client: QueryClient): number {
  return chartRevisions.get(client) ?? 0;
}

/** Drop old precision before reloading; invalidation alone keeps erased prose visible. */
export async function clearChartDerivedData(client: QueryClient): Promise<void> {
  chartRevisions.set(client, chartDataRevision(client) + 1);
  const predicate = (query: { queryKey: readonly unknown[] }) =>
    typeof query.queryKey[0] === "string" && CHART_DERIVED_KEYS.has(query.queryKey[0]);
  await client.cancelQueries({ predicate });
  clearActiveDailyReading();
  clearCachedDailyNote();
  clearLocalSavedNotes();
  clearSavedNoteMutationQueue();
  client.removeQueries({ predicate, type: "inactive" });
  await client.resetQueries({ predicate, type: "active" });
}

/** Queries a birth-date correction keeps on the server (US-23 D2): refetch, never discard. */
const RETAINED_COPY_KEYS = new Set(["saved-notes", "share-links"]);

/**
 * Withdraw the old chart after a birth-date correction (US-23) without losing deletion intents.
 *
 * Unlike clearChartDerivedData, which a precision removal uses because it deletes every copy,
 * this keeps queued *unsaves*: the saved copies survive the correction on the server, so an
 * offline unsave must still reach it. Queued *saves* point at the deleted Daily note and go.
 */
export async function withdrawCorrectedChart(client: QueryClient): Promise<void> {
  await withdrawChart(client, true);
}

/**
 * Hide the current chart's derived content while a correction's outcome is unknown (Codex r57):
 * the change may still commit, so nothing old may stay on screen or in the offline note cache,
 * but queued saves and unsaves stay too because they are valid if the change never lands.
 *
 * Codex r58/r59: the quarantine lasts until the outcome is authoritative. Until then no Daily
 * note enters the offline cache, derived reads wait (pages keep their loading state), and the
 * profile is re-read in the background. A new revision means the change landed: the old chart is
 * withdrawn again. The same revision ends it only after the deadline, which lies well past the
 * server's own pre-commit deadline (the server rolls a late correction back), so the request can
 * no longer commit. A failed read keeps it. The pending state is session-scoped storage, so a
 * reload restores it (resumeChartQuarantine) before any derived read.
 */
export async function quarantineChartDerivedData(
  client: QueryClient,
  submittedRevision: string,
  options: { intervalMs?: number; windowMs?: number } = {},
): Promise<void> {
  endQuarantine();
  setPendingChartQuarantine({
    revision: submittedRevision,
    deadline: Date.now() + (options.windowMs ?? BIRTH_CORRECTION_TIMEOUT_MS + 30_000),
    epoch: currentSessionEpoch(),
  });
  suspendDailyNoteCacheWrites(true);
  // Codex r60: never await active refetches here; they wait on this very quarantine.
  await withdrawChart(client, false, false);
  watchQuarantine(client, options.intervalMs ?? 10_000);
}

/** App start: continue a quarantine a reload interrupted, before anything derived is shown. */
export function resumeChartQuarantine(client: QueryClient, options: { intervalMs?: number } = {}): void {
  if (activeQuarantine || !pendingChartQuarantine()) return;
  suspendDailyNoteCacheWrites(true);
  clearCachedDailyNote();
  watchQuarantine(client, options.intervalMs ?? 10_000);
}

function watchQuarantine(client: QueryClient, intervalMs: number): void {
  const pending = pendingChartQuarantine();
  if (!pending) return;
  const generation = sessionGeneration();
  const token = {};
  activeQuarantine = { token, timer: null };
  const check = async () => {
    if (activeQuarantine?.token !== token) return;
    // The session boundary clears the old owner's data itself.
    if (pending.epoch !== currentSessionEpoch() || generation !== sessionGeneration()) return endQuarantine();
    let revision: string | undefined;
    try {
      revision = (await getBirthProfile()).profile_revision ?? undefined;
    } catch {
      revision = undefined;
    }
    if (activeQuarantine?.token !== token) return;
    if (revision !== undefined && revision !== pending.revision) {
      // Codex r60: withdraw the cache without awaiting refetches (this gate holds them), then
      // release the gate so the active queries refetch the corrected chart.
      await withdrawChart(client, true, false);
      if (activeQuarantine?.token === token) endQuarantine();
      return;
    }
    if (revision === pending.revision && Date.now() >= pending.deadline) return endQuarantine();
    activeQuarantine.timer = setTimeout(() => void check(), intervalMs);
  };
  activeQuarantine.timer = setTimeout(() => void check(), intervalMs);
}

let activeQuarantine: { token: object; timer: ReturnType<typeof setTimeout> | null } | null = null;

/** True while a correction's outcome is still unknown. */
export function chartQuarantined(): boolean {
  return activeQuarantine !== null || pendingChartQuarantine() !== null;
}

/** Stop a pending quarantine (resolved, or replaced by a definitive withdrawal). */
export function endQuarantine(): void {
  if (activeQuarantine?.timer) clearTimeout(activeQuarantine.timer);
  activeQuarantine = null;
  setPendingChartQuarantine(null);
  suspendDailyNoteCacheWrites(false);
}

async function withdrawChart(client: QueryClient, sourceDeleted: boolean, awaitRefetch = true): Promise<void> {
  chartRevisions.set(client, chartDataRevision(client) + 1);
  const derived = (query: { queryKey: readonly unknown[] }) =>
    typeof query.queryKey[0] === "string"
    && CHART_DERIVED_KEYS.has(query.queryKey[0])
    && !RETAINED_COPY_KEYS.has(query.queryKey[0]);
  const retained = (query: { queryKey: readonly unknown[] }) =>
    typeof query.queryKey[0] === "string" && RETAINED_COPY_KEYS.has(query.queryKey[0]);
  await client.cancelQueries({ predicate: derived });
  clearActiveDailyReading();
  clearCachedDailyNote();
  // Pending-sync markers of saves that can no longer reach their deleted source.
  if (sourceDeleted) {
    clearLocalSavedNotes();
    dropQueuedSaves();
  }
  client.removeQueries({ predicate: derived, type: "inactive" });
  // resetQueries drops the old data synchronously; its refetch may wait behind the quarantine gate.
  const refetch = Promise.all([
    client.resetQueries({ predicate: derived, type: "active" }),
    // listSavedNotes flushes the kept unsaves before it reads the list.
    client.invalidateQueries({ predicate: retained }),
  ]);
  if (awaitRefetch) await refetch;
  else void refetch.catch(() => undefined);
}
