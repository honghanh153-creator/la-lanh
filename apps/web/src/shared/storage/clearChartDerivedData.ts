import type { QueryClient } from "@tanstack/react-query";

import { clearActiveDailyReading } from "../api/client";
import { clearCachedDailyNote } from "./noteCache";
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
  clearLocalSavedNotes();
  dropQueuedSaves();
  client.removeQueries({ predicate: derived, type: "inactive" });
  await client.resetQueries({ predicate: derived, type: "active" });
  // listSavedNotes flushes the kept unsaves before it reads the list.
  await client.invalidateQueries({ predicate: retained });
}
