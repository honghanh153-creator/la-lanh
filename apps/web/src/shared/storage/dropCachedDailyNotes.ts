import type { QueryClient } from "@tanstack/react-query";

import { fenceChartDataWriters } from "./clearChartDerivedData";
import { discardActiveQueryData } from "./discardActiveQueryData";
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
  // Pending Daily writers (a context switch, an Aura acknowledgement) started before the clear
  // check this revision and must not write their old note back.
  fenceChartDataWriters(client);
  await client.cancelQueries({ predicate: isDailyNoteQuery });
  clearCachedDailyNote();
  client.removeQueries({ predicate: isDailyNoteQuery, type: "inactive" });
  await discardActiveQueryData(client, isDailyNoteQuery);
}
