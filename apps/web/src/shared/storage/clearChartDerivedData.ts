import type { QueryClient } from "@tanstack/react-query";

import { BIRTH_CORRECTION_TIMEOUT_MS, clearActiveDailyReading, getBirthProfile } from "../api/client";
import { currentSessionEpoch, sessionGeneration } from "../session/sessionIdentity";
import { discardActiveQueryData } from "./discardActiveQueryData";
import { pendingChartQuarantine, setPendingChartQuarantine, type PendingChartQuarantine } from "./chartQuarantineGate";
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

/** Any deletion of derived data: pending writers started before it see a new revision and stop. */
export function fenceChartDataWriters(client: QueryClient): void {
  chartRevisions.set(client, chartDataRevision(client) + 1);
}

/** Drop old precision before reloading; invalidation alone keeps erased prose visible. */
export async function clearChartDerivedData(client: QueryClient): Promise<void> {
  fenceChartDataWriters(client);
  const predicate = (query: { queryKey: readonly unknown[] }) =>
    typeof query.queryKey[0] === "string" && CHART_DERIVED_KEYS.has(query.queryKey[0]);
  await client.cancelQueries({ predicate });
  clearActiveDailyReading();
  clearCachedDailyNote();
  clearLocalSavedNotes();
  clearSavedNoteMutationQueue();
  client.removeQueries({ predicate, type: "inactive" });
  await discardActiveQueryData(client, predicate);
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
  // The outcome is known now: drop the old cache, then release the gate (a pending correction
  // record or quarantine holds the very refetches awaited below, Codex r61).
  const { refetch } = await withdrawChart(client, true);
  endQuarantine();
  await refetch;
}

/**
 * Codex r61: record the correction before its PUT leaves. A reload while the request is pending
 * loses this page's continuation, but the server may still commit; the stored record (same shape
 * as the quarantine: opaque revision, deadline, session epoch) makes the next app start hold the
 * derived reads and reconcile (resumeChartQuarantine). Reads in this tab wait meanwhile too.
 */
export function beginPendingCorrection(submittedRevision: string): PendingChartQuarantine {
  const record = {
    revision: submittedRevision,
    deadline: Date.now() + BIRTH_CORRECTION_TIMEOUT_MS + 30_000,
    epoch: currentSessionEpoch(),
  };
  // An earlier unresolved correction keeps its watched quarantine, which already holds the reads
  // (and the editor cannot load a date while it lasts).
  if (!activeQuarantine) setPendingChartQuarantine(record);
  return record;
}

/** A definitive answer: this request can no longer commit, so its record goes. */
export function settlePendingCorrection(record: PendingChartQuarantine): void {
  const current = pendingChartQuarantine();
  if (activeQuarantine || !current) return;
  if (current.revision === record.revision && current.deadline === record.deadline) endQuarantine();
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
  // Replace any earlier record without releasing the gate in between (Codex r61): a release here
  // would let held reads fetch the old chart before the new record is in place.
  stopWatcher();
  setPendingChartQuarantine({
    revision: submittedRevision,
    deadline: Date.now() + (options.windowMs ?? BIRTH_CORRECTION_TIMEOUT_MS + 30_000),
    epoch: currentSessionEpoch(),
  });
  suspendDailyNoteCacheWrites(true);
  // Codex r60: never await active refetches here; they wait on this very quarantine. The withdrawal
  // includes the birth profile itself (date and calculation), Codex r61.
  const { refetch } = await withdrawChart(client, false);
  void refetch.catch(() => undefined);
  watchQuarantine(client, options.intervalMs ?? 10_000);
}

/**
 * App start: continue a quarantine (or a correction still pending when the page reloaded) before
 * anything derived is shown. The first reconciliation read runs at once.
 */
export function resumeChartQuarantine(client: QueryClient, options: { intervalMs?: number } = {}): void {
  if (activeQuarantine || !pendingChartQuarantine()) return;
  suspendDailyNoteCacheWrites(true);
  clearCachedDailyNote();
  watchQuarantine(client, options.intervalMs ?? 10_000, 0);
}

function watchQuarantine(client: QueryClient, intervalMs: number, firstDelayMs = intervalMs): void {
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
      // The only profile read allowed past the gate (Codex r61).
      revision = (await getBirthProfile(undefined, { bypassChartQuarantine: true })).profile_revision ?? undefined;
    } catch {
      revision = undefined;
    }
    if (activeQuarantine?.token !== token) return;
    if (revision !== undefined && revision !== pending.revision) {
      // Codex r60: withdraw the cache without awaiting refetches (this gate holds them), then
      // release the gate so the active queries refetch the corrected chart.
      const { refetch } = await withdrawChart(client, true);
      void refetch.catch(() => undefined);
      if (activeQuarantine?.token === token) endQuarantine();
      return;
    }
    if (revision === pending.revision && Date.now() >= pending.deadline) return endQuarantine();
    activeQuarantine.timer = setTimeout(() => void check(), intervalMs);
  };
  activeQuarantine.timer = setTimeout(() => void check(), firstDelayMs);
}

function stopWatcher(): void {
  if (activeQuarantine?.timer) clearTimeout(activeQuarantine.timer);
  activeQuarantine = null;
}

let activeQuarantine: { token: object; timer: ReturnType<typeof setTimeout> | null } | null = null;

/** True while a correction's outcome is still unknown. */
export function chartQuarantined(): boolean {
  return activeQuarantine !== null || pendingChartQuarantine() !== null;
}

/** Stop a pending quarantine (resolved, or replaced by a definitive withdrawal). */
export function endQuarantine(): void {
  stopWatcher();
  setPendingChartQuarantine(null);
  suspendDailyNoteCacheWrites(false);
}

/**
 * Drops the old derived cache and starts the refetches without awaiting them: they may wait at the
 * quarantine gate, which the caller releases (wrapped so the async return does not await it).
 */
async function withdrawChart(client: QueryClient, sourceDeleted: boolean): Promise<{ refetch: Promise<unknown> }> {
  fenceChartDataWriters(client);
  const derived =(query: { queryKey: readonly unknown[] }) =>
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
  // The old data goes synchronously (not back to an initialData snapshot); the refetch may wait
  // behind the quarantine gate.
  const refetch = Promise.all([
    discardActiveQueryData(client, derived),
    // listSavedNotes flushes the kept unsaves before it reads the list.
    client.invalidateQueries({ predicate: retained }),
  ]);
  return { refetch };
}
