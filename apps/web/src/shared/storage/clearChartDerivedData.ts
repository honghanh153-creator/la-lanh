import type { QueryClient } from "@tanstack/react-query";

import { clearActiveDailyReading } from "../api/client";
import { clearCachedDailyNote } from "./noteCache";
import { clearLocalSavedNotes } from "./savedNoteCache";
import { clearSavedNoteMutationQueue } from "./savedNoteMutationQueue";

const CHART_DERIVED_KEYS = new Set([
  "birth-profile", "birth-supplement", "birth-supplement-edit", "daily-note", "daily-note-context",
  "daily-note-mood", "daily-experiment", "insight-overview", "private-reading",
  "saved-notes", "share-artifact", "radar-invites", "radar-result",
  "radar-receipt", "current-radar", "matching-readiness", "daily-note-resonance",
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
