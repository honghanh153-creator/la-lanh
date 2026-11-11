import type { QueryClient } from "@tanstack/react-query";

import { clearCachedDailyNote } from "./noteCache";

// Every query that holds Daily-note text: the auto note, its roast voice and each background lens.
const DAILY_NOTE_KEYS = new Set(["daily-note", "daily-note-context"]);

const isDailyNoteQuery = (query: { queryKey: readonly unknown[] }) =>
  typeof query.queryKey[0] === "string" && DAILY_NOTE_KEYS.has(query.queryKey[0]);

/**
 * PV-21: after a history clear, no earlier Daily note may stay in memory. Query keys carry no
 * date, so a tab left open past midnight still holds yesterday's text under the same key; drop
 * every Daily-note entry and the offline fallback, then let open screens reload today's note.
 */
export async function dropCachedDailyNotes(client: QueryClient): Promise<void> {
  await client.cancelQueries({ predicate: isDailyNoteQuery });
  clearCachedDailyNote();
  client.removeQueries({ predicate: isDailyNoteQuery, type: "inactive" });
  // resetQueries clears the old data at once; a failed reload leaves the screen empty, not stale.
  await client.resetQueries({ predicate: isDailyNoteQuery, type: "active" });
}
